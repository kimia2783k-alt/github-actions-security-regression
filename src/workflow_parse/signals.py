from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


SHA_RE = re.compile(r"^[0-9a-f]{40}$", re.I)
# uses: owner/name@ref  optionally followed by # <40hex>
USES_LINE_RE = re.compile(
    r"(?m)^\s*-?\s*uses:\s*[\"']?([^\"'\s#]+)[\"']?\s*(?:#\s*([0-9a-fA-F]{40}))?"
)
SECRET_ECHO_RE = re.compile(
    r"("
    r"(?:echo|print|printf|console\.log|printenv)\b.{0,120}(?:secrets\.|toJSON\s*\(\s*secrets|SECRET|PASSWORD|TOKEN|API_KEY)"
    r"|toJSON\s*\(\s*secrets"
    r"|env\s*\|\s*(?:grep|sort)"
    r")",
    re.I,
)
INJECTION_RE = re.compile(
    r"\$\{\{\s*github\.(event\.(issue|comment|pull_request|head_commit|review|discussion|inputs)|head_ref|ref_name).*?\}\}",
    re.I,
)
# curl|bash / wget|sh / fetch|iex style remote shell pipes
PIPE_SHELL_RE = re.compile(
    r"("
    r"curl\b[^\n|]{0,120}\|\s*(?:ba)?sh\b"
    r"|wget\b[^\n|]{0,120}\|\s*(?:ba)?sh\b"
    r"|invoke-expression\b|iex\s*\("
    r")",
    re.I,
)
# Writing untrusted context into GITHUB_ENV / GITHUB_PATH
GITHUB_ENV_INJECTION_RE = re.compile(
    r"("
    r"(?:echo|printf).{0,120}\$\{?\{\s*github\.(event|head_ref|ref_name)"
    r".{0,80}(?:GITHUB_ENV|GITHUB_PATH)"
    r"|>>\s*\$?\{?GITHUB_(?:ENV|PATH)\}?"
    r".{0,80}\$\{\{\s*github\.(event|head_ref)"
    r")",
    re.I | re.S,
)

# High-impact GITHUB_TOKEN write scopes (OWASP IAM / PBAC)
DANGEROUS_WRITE_SCOPES = frozenset(
    {
        "contents",
        "id-token",
        "actions",
        "packages",
        "security-events",
        "deployments",
        "environments",
        "attestations",
    }
)
DANGEROUS_TRIGGERS = frozenset(
    {
        "issue_comment",
        "discussion_comment",
        "pull_request_review_comment",
    }
)


@dataclass
class ActionRef:
    uses: str
    owner: str
    name: str
    ref: str
    pinned_sha: bool
    job: str
    step_index: int
    comment_sha: str | None = None
    effectively_pinned: bool = False

    @property
    def key(self) -> tuple[str, str]:
        return (self.owner.lower(), self.name.lower())

    @property
    def identity(self) -> tuple[str, str, str]:
        return (self.owner.lower(), self.name.lower(), self.ref)


@dataclass
class SignalSet:
    triggers: set[str] = field(default_factory=set)
    permissions_raw: Any = None
    permissions_score: int = 0  # higher = broader
    # scopes explicitly granted write (workflow ∪ jobs), lowercased names
    write_scopes: set[str] = field(default_factory=set)
    actions: list[ActionRef] = field(default_factory=list)
    job_names: set[str] = field(default_factory=set)
    security_step_keys: set[str] = field(default_factory=set)
    run_scripts: list[str] = field(default_factory=list)
    has_self_hosted: bool = False
    privileged_checkout: bool = False
    pipe_shell_hits: int = 0
    github_env_injection_hits: int = 0
    secret_echo_hits: int = 0
    injection_hits: int = 0
    parse_error: str | None = None
    source_text: str | None = None


def _coerce_workflow_root(data: Any) -> Any:
    """Empty files load as None; treat as empty mapping. Multi-doc: first mapping."""
    if data is None:
        return {}
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                return item
        return {"__parse_error__": "workflow root is a list without a mapping document"}
    return data


def load_workflow(path: str | Path) -> Any:
    yaml = YAML(typ="safe")
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        if not text.strip():
            return {}
        try:
            data = yaml.load(text)
        except Exception:
            # multi-doc or recover first document
            data = None
            for doc in yaml.load_all(text):
                if isinstance(doc, dict):
                    data = doc
                    break
            if data is None:
                raise
        return _coerce_workflow_root(data)
    except Exception as exc:  # noqa: BLE001 — quarantine invalid field YAML
        return {"__parse_error__": str(exc)}


def load_workflow_text(path: str | Path) -> tuple[Any, str]:
    """Load YAML mapping plus raw source (for comment-SHA recovery)."""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        return {"__parse_error__": str(exc)}, ""
    if not text.strip():
        return {}, text
    yaml = YAML(typ="safe")
    try:
        data = yaml.load(text)
        return _coerce_workflow_root(data), text
    except Exception as exc:  # noqa: BLE001
        # Try first mapping document in multi-doc streams
        try:
            for doc in YAML(typ="safe").load_all(text):
                if isinstance(doc, dict):
                    return doc, text
        except Exception:  # noqa: BLE001
            pass
        return {"__parse_error__": str(exc)}, text


def extract_signals_raw_fallback(source_text: str, security_keywords: list[str] | None = None) -> SignalSet:
    """Best-effort signals when YAML parse fails (still recover uses:/on:/runs-on)."""
    signals = SignalSet(source_text=source_text)
    keywords = [k.lower() for k in (security_keywords or [])]
    text = source_text or ""
    # triggers (rough)
    if re.search(r"(?m)^\s*pull_request_target\s*:", text) or re.search(
        r"\bpull_request_target\b", text
    ):
        signals.triggers.add("pull_request_target")
    if re.search(r"(?m)^\s*workflow_run\s*:", text) or re.search(r"\bworkflow_run\b", text):
        signals.triggers.add("workflow_run")
    for t in DANGEROUS_TRIGGERS:
        if re.search(rf"(?m)^\s*{re.escape(t)}\s*:", text) or re.search(rf"\b{re.escape(t)}\b", text):
            signals.triggers.add(t)
    if re.search(r"permissions:\s*write-all", text):
        signals.permissions_raw = "write-all"
        signals.permissions_score = 100
        signals.write_scopes |= set(DANGEROUS_WRITE_SCOPES)
    for scope in DANGEROUS_WRITE_SCOPES:
        if re.search(rf"(?m)^\s*{re.escape(scope)}\s*:\s*write\b", text):
            signals.write_scopes.add(scope)
    if re.search(r"self-hosted", text):
        signals.has_self_hosted = True
    # collect run: blocks roughly for script pattern counts
    for m in re.finditer(r"(?ms)^\s*run:\s*[|>]?(.*?)(?=^\s*(?:-\s)?(?:name:|uses:|run:|with:|env:|id:)|^\S|\Z)", text):
        signals.run_scripts.append(m.group(1))
    if not signals.run_scripts:
        signals.run_scripts.append(text)
    _accumulate_script_hits(signals)
    for m in USES_LINE_RE.finditer(text):
        uses = m.group(1).strip()
        comment = m.group(2)
        owner, name, ref, pinned = _parse_uses(uses)
        csha = comment.lower() if comment and SHA_RE.match(comment) else None
        # Effective pin = @ref is a 40-hex commit SHA only.
        # A trailing "# <sha>" comment does NOT pin a floating tag/branch ref.
        signals.actions.append(
            ActionRef(
                uses=uses,
                owner=owner,
                name=name,
                ref=ref,
                pinned_sha=pinned,
                job="raw",
                step_index=len(signals.actions),
                comment_sha=csha,
                effectively_pinned=pinned,
            )
        )
        key = f"{owner}/{name}"
        if any(k in f"{key} {uses}".lower() for k in keywords):
            signals.security_step_keys.add(key)
    return signals


def _normalize_triggers(on_value: Any) -> set[str]:
    triggers: set[str] = set()
    if on_value is None:
        return triggers
    if isinstance(on_value, str):
        triggers.add(on_value)
    elif isinstance(on_value, list):
        for item in on_value:
            if isinstance(item, str):
                triggers.add(item)
    elif isinstance(on_value, dict):
        triggers.update(str(k) for k in on_value.keys())
    return triggers


def _permissions_score(permissions: Any) -> int:
    if permissions is None:
        return 50  # default token often write on many repos historically
    if isinstance(permissions, str):
        p = permissions.strip().lower()
        if p == "write-all":
            return 100
        if p == "read-all":
            return 40
        return 60
    if isinstance(permissions, dict):
        score = 10
        for _, v in permissions.items():
            if str(v).lower() == "write":
                score += 15
            elif str(v).lower() == "read":
                score += 2
        return min(score, 99)
    return 50


def _write_scopes(permissions: Any) -> set[str]:
    """Return permission scope names that are explicitly write (or write-all → all dangerous)."""
    out: set[str] = set()
    if permissions is None:
        return out
    if isinstance(permissions, str):
        if permissions.strip().lower() == "write-all":
            return set(DANGEROUS_WRITE_SCOPES)
        return out
    if isinstance(permissions, dict):
        for k, v in permissions.items():
            if str(v).lower() == "write":
                out.add(str(k).strip().lower())
    return out


def _accumulate_script_hits(signals: SignalSet) -> None:
    signals.secret_echo_hits = sum(1 for s in signals.run_scripts if SECRET_ECHO_RE.search(s))
    signals.injection_hits = sum(1 for s in signals.run_scripts if INJECTION_RE.search(s))
    signals.pipe_shell_hits = sum(1 for s in signals.run_scripts if PIPE_SHELL_RE.search(s))
    signals.github_env_injection_hits = sum(
        1 for s in signals.run_scripts if GITHUB_ENV_INJECTION_RE.search(s)
    )


def _parse_uses(uses: str) -> tuple[str, str, str, bool]:
    """Return owner, name, ref, pinned_sha. Owner/name lowercased."""
    uses = uses.strip().strip("\"'")
    if uses.startswith("./") or uses.startswith(".\\"):
        return ("local", uses, "local", True)
    if "@" not in uses:
        return ("unknown", uses.lower(), "", False)
    left, ref = uses.rsplit("@", 1)
    # drop accidental inline comment residue if caller passed it
    ref = ref.split("#", 1)[0].strip().strip("\"'")
    parts = left.split("/")
    owner = (parts[0] if parts else "unknown").lower()
    name = "/".join(parts[1:]).lower() if len(parts) > 1 else left.lower()
    pinned = bool(SHA_RE.match(ref))
    return owner, name, ref, pinned


def _comment_pin_map(source_text: str | None) -> dict[tuple[str, str, str], str]:
    """Map (owner, name, ref) -> comment SHA from raw uses lines."""
    out: dict[tuple[str, str, str], str] = {}
    if not source_text:
        return out
    for m in USES_LINE_RE.finditer(source_text):
        uses = m.group(1).strip()
        comment = m.group(2)
        if not comment or not SHA_RE.match(comment):
            continue
        owner, name, ref, _ = _parse_uses(uses)
        out[(owner, name, ref)] = comment.lower()
    return out


def extract_signals(
    data: Any,
    security_keywords: list[str] | None = None,
    source_text: str | None = None,
) -> SignalSet:
    signals = SignalSet()
    signals.source_text = source_text
    if isinstance(data, dict) and "__parse_error__" in data:
        # Recover what we can from raw text instead of aborting the pair.
        if source_text and source_text.strip():
            fb = extract_signals_raw_fallback(source_text, security_keywords)
            fb.parse_error = str(data["__parse_error__"])  # informational only
            return fb
        signals.parse_error = str(data["__parse_error__"])
        return signals
    if not isinstance(data, dict):
        if source_text and source_text.strip():
            fb = extract_signals_raw_fallback(source_text, security_keywords)
            fb.parse_error = "workflow root is not a mapping"
            return fb
        signals.parse_error = "workflow root is not a mapping"
        return signals

    keywords = [k.lower() for k in (security_keywords or [])]
    comment_pins = _comment_pin_map(source_text)
    signals.triggers = _normalize_triggers(data.get("on") or data.get(True))
    signals.permissions_raw = data.get("permissions")
    signals.permissions_score = _permissions_score(signals.permissions_raw)
    signals.write_scopes |= _write_scopes(signals.permissions_raw)

    jobs = data.get("jobs") or {}
    if not isinstance(jobs, dict):
        _accumulate_script_hits(signals)
        return signals

    privileged = (
        "pull_request_target" in signals.triggers
        or "workflow_run" in signals.triggers
        or bool(signals.triggers & DANGEROUS_TRIGGERS)
    )

    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        signals.job_names.add(str(job_name))
        runs_on = job.get("runs-on")
        if isinstance(runs_on, str) and "self-hosted" in runs_on:
            signals.has_self_hosted = True
        elif isinstance(runs_on, list) and any("self-hosted" in str(x) for x in runs_on):
            signals.has_self_hosted = True

        if "permissions" in job:
            job_perms = job.get("permissions")
            job_score = _permissions_score(job_perms)
            signals.permissions_score = max(signals.permissions_score, job_score)
            signals.write_scopes |= _write_scopes(job_perms)

        steps = job.get("steps") or []
        if not isinstance(steps, list):
            continue
        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            uses = step.get("uses")
            if isinstance(uses, str):
                owner, name, ref, pinned = _parse_uses(uses)
                csha = comment_pins.get((owner, name, ref))
                # Effective pin = @ref is a 40-hex commit SHA only.
                # Comment-only SHA beside @v4/@main is documentation, not a pin.
                signals.actions.append(
                    ActionRef(
                        uses=uses.strip().strip("\"'"),
                        owner=owner,
                        name=name,
                        ref=ref,
                        pinned_sha=pinned,
                        job=str(job_name),
                        step_index=idx,
                        comment_sha=csha,
                        effectively_pinned=pinned,
                    )
                )
                key = f"{owner}/{name}"
                blob = f"{key} {uses}".lower()
                if any(k in blob for k in keywords):
                    signals.security_step_keys.add(key)
                if privileged and "checkout" in name:
                    with_block = step.get("with") or {}
                    if isinstance(with_block, dict):
                        ref_val = str(with_block.get("ref", ""))
                        if "pull_request" in ref_val or "head" in ref_val:
                            signals.privileged_checkout = True

            run = step.get("run")
            if isinstance(run, str):
                signals.run_scripts.append(run)
                step_name = str(step.get("name", "")).lower()
                if any(k in step_name for k in keywords) or any(
                    k in run.lower() for k in keywords
                ):
                    signals.security_step_keys.add(f"run:{job_name}:{idx}")

    for jn in signals.job_names:
        jl = jn.lower()
        if any(k in jl for k in keywords) or jl in {"codeql", "security", "sast", "sca"}:
            signals.security_step_keys.add(f"job:{jl}")

    _accumulate_script_hits(signals)
    return signals


def extract_signals_from_path(
    path: str | Path,
    security_keywords: list[str] | None = None,
) -> SignalSet:
    data, text = load_workflow_text(path)
    return extract_signals(data, security_keywords, source_text=text)
