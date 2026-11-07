from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from workflow_parse.signals import (
    DANGEROUS_TRIGGERS,
    DANGEROUS_WRITE_SCOPES,
    SignalSet,
    extract_signals,
    extract_signals_from_path,
)


@dataclass
class Finding:
    rule_id: str
    severity: str
    message: str
    evidence: str
    owasp: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_rules(rules_path: str | Path | None = None) -> dict[str, Any]:
    if rules_path is None:
        candidates = [
            Path("policies/owasp_cicd_rules.yaml"),
            Path(__file__).resolve().parents[2] / "policies" / "owasp_cicd_rules.yaml",
        ]
        for c in candidates:
            if c.exists():
                rules_path = c
                break
        if rules_path is None:
            raise FileNotFoundError("policies/owasp_cicd_rules.yaml not found")
    with open(rules_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _rule_meta(rules_doc: dict[str, Any], rule_id: str) -> dict[str, Any]:
    for r in rules_doc.get("rules", []):
        if r.get("id") == rule_id:
            return r
    return {"id": rule_id, "severity": "medium", "owasp": [], "enabled": True}


def _enabled(rules_doc: dict[str, Any], rule_id: str) -> bool:
    meta = _rule_meta(rules_doc, rule_id)
    return bool(meta.get("enabled", True))


def _finding(rules_doc: dict[str, Any], rule_id: str, message: str, evidence: str) -> Finding:
    meta = _rule_meta(rules_doc, rule_id)
    return Finding(
        rule_id=rule_id,
        severity=str(meta.get("severity", "medium")),
        message=message,
        evidence=evidence,
        owasp=list(meta.get("owasp") or []),
    )


def _is_write_all(permissions: Any) -> bool:
    if isinstance(permissions, str) and permissions.strip().lower() == "write-all":
        return True
    return False


def _has_explicit_restriction(permissions: Any) -> bool:
    if isinstance(permissions, dict) and permissions:
        return True
    if isinstance(permissions, str) and permissions.strip().lower() == "read-all":
        return True
    return False


def _best_pin_by_key(actions) -> dict[tuple[str, str], Any]:
    """For each (owner, name), keep the most-pinned occurrence."""
    best: dict[tuple[str, str], Any] = {}
    for a in actions:
        key = a.key
        prev = best.get(key)
        if prev is None:
            best[key] = a
            continue
        # prefer effectively_pinned
        if a.effectively_pinned and not prev.effectively_pinned:
            best[key] = a
    return best


def compare_signals(before: SignalSet, after: SignalSet, rules_doc: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    trusted = {str(x).lower() for x in (rules_doc.get("trusted_action_owners") or [])}

    # R01 write-all escalation
    if _enabled(rules_doc, "R01"):
        if _is_write_all(after.permissions_raw) and not _is_write_all(before.permissions_raw):
            findings.append(
                _finding(
                    rules_doc,
                    "R01",
                    "Permissions escalated to write-all",
                    f"before={before.permissions_raw!r} after={after.permissions_raw!r}",
                )
            )
        elif after.permissions_score >= before.permissions_score + 30 and after.permissions_score >= 80:
            findings.append(
                _finding(
                    rules_doc,
                    "R01",
                    "Permissions score escalated substantially toward broad write",
                    f"score {before.permissions_score} -> {after.permissions_score}",
                )
            )

    # R02 restriction removed
    if _enabled(rules_doc, "R02"):
        if _has_explicit_restriction(before.permissions_raw) and not _has_explicit_restriction(
            after.permissions_raw
        ):
            findings.append(
                _finding(
                    rules_doc,
                    "R02",
                    "Explicit permissions restriction removed",
                    f"before={before.permissions_raw!r} after={after.permissions_raw!r}",
                )
            )

    # R03 pull_request_target
    if _enabled(rules_doc, "R03"):
        if "pull_request_target" in after.triggers and "pull_request_target" not in before.triggers:
            findings.append(
                _finding(
                    rules_doc,
                    "R03",
                    "pull_request_target trigger newly introduced",
                    f"triggers={sorted(after.triggers)}",
                )
            )

    # R04 privileged checkout
    if _enabled(rules_doc, "R04"):
        if after.privileged_checkout and not before.privileged_checkout:
            findings.append(
                _finding(
                    rules_doc,
                    "R04",
                    "Checkout of PR head under privileged trigger",
                    "privileged_checkout=true",
                )
            )

    # R05 unpinned from SHA (effective pin: @ref is 40-hex commit only)
    if _enabled(rules_doc, "R05"):
        before_best = _best_pin_by_key(before.actions)
        after_by_key: dict[tuple[str, str], list] = {}
        for a in after.actions:
            after_by_key.setdefault(a.key, []).append(a)
        for key, b_act in before_best.items():
            if not b_act.effectively_pinned:
                continue
            after_acts = after_by_key.get(key) or []
            if not after_acts:
                continue
            # regression if any after instance for this key lost effective pin
            if any(not a.effectively_pinned for a in after_acts):
                a_ex = next(a for a in after_acts if not a.effectively_pinned)
                findings.append(
                    _finding(
                        rules_doc,
                        "R05",
                        f"Action {key[0]}/{key[1]} lost SHA pin",
                        f"{b_act.uses} (pinned={b_act.effectively_pinned}, "
                        f"comment={b_act.comment_sha}) -> {a_ex.uses}",
                    )
                )

    # R06 new unpinned third-party — identity (owner, name, ref)
    if _enabled(rules_doc, "R06"):
        before_ids = {a.identity for a in before.actions}
        for a in after.actions:
            if a.identity in before_ids:
                continue
            if a.owner in trusted or a.owner == "local":
                continue
            if not a.effectively_pinned:
                findings.append(
                    _finding(
                        rules_doc,
                        "R06",
                        f"New unpinned third-party action {a.uses}",
                        f"identity={a.identity}",
                    )
                )

    # R07 secret exposure (expanded patterns via SignalSet.secret_echo_hits)
    if _enabled(rules_doc, "R07"):
        if after.secret_echo_hits > before.secret_echo_hits:
            findings.append(
                _finding(
                    rules_doc,
                    "R07",
                    "Secret exposure pattern added in run scripts",
                    f"matches {before.secret_echo_hits} -> {after.secret_echo_hits}",
                )
            )

    # R08 security controls removed
    if _enabled(rules_doc, "R08"):
        removed = before.security_step_keys - after.security_step_keys
        if removed:
            findings.append(
                _finding(
                    rules_doc,
                    "R08",
                    "Security job/step removed",
                    f"removed={sorted(removed)}",
                )
            )

    # R09 workflow_run
    if _enabled(rules_doc, "R09"):
        if "workflow_run" in after.triggers and "workflow_run" not in before.triggers:
            findings.append(
                _finding(
                    rules_doc,
                    "R09",
                    "workflow_run trigger newly introduced",
                    f"triggers={sorted(after.triggers)}",
                )
            )

    # R10 script injection (expanded contexts)
    if _enabled(rules_doc, "R10"):
        if after.injection_hits > before.injection_hits:
            findings.append(
                _finding(
                    rules_doc,
                    "R10",
                    "Untrusted context interpolation added to run scripts",
                    f"matches {before.injection_hits} -> {after.injection_hits}",
                )
            )

    # R11 self-hosted
    if _enabled(rules_doc, "R11"):
        if after.has_self_hosted and not before.has_self_hosted:
            findings.append(
                _finding(
                    rules_doc,
                    "R11",
                    "self-hosted runner newly introduced",
                    "has_self_hosted=true",
                )
            )

    # R12 dangerous fine-grained write scopes newly granted
    if _enabled(rules_doc, "R12"):
        policy_scopes = rules_doc.get("dangerous_write_scopes") or list(DANGEROUS_WRITE_SCOPES)
        watched = {str(s).lower() for s in policy_scopes}
        new_scopes = (after.write_scopes & watched) - before.write_scopes
        # Avoid double-counting pure write-all already reported as R01 when before had none
        if new_scopes and not (
            _is_write_all(after.permissions_raw) and not _is_write_all(before.permissions_raw)
        ):
            findings.append(
                _finding(
                    rules_doc,
                    "R12",
                    "Dangerous permission write scope(s) newly granted",
                    f"new_scopes={sorted(new_scopes)}",
                )
            )
        elif new_scopes and _is_write_all(after.permissions_raw) and not _is_write_all(
            before.permissions_raw
        ):
            # write-all already covered by R01; still emit R12 only for explicit map escalations
            pass

    # R13 remote shell pipe (curl|bash etc.)
    if _enabled(rules_doc, "R13"):
        if after.pipe_shell_hits > before.pipe_shell_hits:
            findings.append(
                _finding(
                    rules_doc,
                    "R13",
                    "Remote shell pipe pattern added in run scripts",
                    f"matches {before.pipe_shell_hits} -> {after.pipe_shell_hits}",
                )
            )

    # R14 dangerous comment/review triggers (PPE-adjacent)
    if _enabled(rules_doc, "R14"):
        policy_triggers = rules_doc.get("dangerous_triggers") or list(DANGEROUS_TRIGGERS)
        watched_t = {str(t) for t in policy_triggers}
        new_t = (after.triggers & watched_t) - before.triggers
        if new_t:
            findings.append(
                _finding(
                    rules_doc,
                    "R14",
                    "Dangerous interactive trigger newly introduced",
                    f"new_triggers={sorted(new_t)}",
                )
            )

    # R15 GITHUB_ENV / GITHUB_PATH injection risk
    if _enabled(rules_doc, "R15"):
        if after.github_env_injection_hits > before.github_env_injection_hits:
            findings.append(
                _finding(
                    rules_doc,
                    "R15",
                    "Untrusted context written toward GITHUB_ENV/GITHUB_PATH",
                    f"matches {before.github_env_injection_hits} -> {after.github_env_injection_hits}",
                )
            )

    return findings


def _signals_unusable(s: SignalSet) -> bool:
    """True only when parse failed and raw fallback recovered nothing."""
    if not s.parse_error:
        return False
    return (
        not s.actions
        and not s.triggers
        and s.permissions_raw is None
        and not s.has_self_hosted
        and not s.security_step_keys
        and not s.run_scripts
    )


def validate_pair(
    before_data: Any,
    after_data: Any,
    rules_doc: dict[str, Any] | None = None,
    before_text: str | None = None,
    after_text: str | None = None,
) -> list[Finding]:
    rules_doc = rules_doc or load_rules()
    keywords = list(rules_doc.get("security_action_keywords") or [])
    before = extract_signals(before_data, keywords, source_text=before_text)
    after = extract_signals(after_data, keywords, source_text=after_text)
    if _signals_unusable(before) and _signals_unusable(after):
        return [
            Finding(
                rule_id="PARSE",
                severity="info",
                message="Parse error",
                evidence=f"before={before.parse_error} after={after.parse_error}",
                owasp=[],
            )
        ]
    return compare_signals(before, after, rules_doc)


def validate_paths(
    before_path: str | Path,
    after_path: str | Path,
    rules_path: str | Path | None = None,
) -> list[Finding]:
    rules_doc = load_rules(rules_path)
    keywords = list(rules_doc.get("security_action_keywords") or [])
    before = extract_signals_from_path(before_path, keywords)
    after = extract_signals_from_path(after_path, keywords)
    if _signals_unusable(before) and _signals_unusable(after):
        return [
            Finding(
                rule_id="PARSE",
                severity="info",
                message="Parse error",
                evidence=f"before={before.parse_error} after={after.parse_error}",
                owasp=[],
            )
        ]
    return compare_signals(before, after, rules_doc)


def findings_to_json(findings: list[Finding]) -> str:
    return json.dumps([f.to_dict() for f in findings], indent=2, ensure_ascii=False)
