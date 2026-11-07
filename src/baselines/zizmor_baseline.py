from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from workflow_parse.signals import extract_signals, load_workflow


def _zizmor_bin() -> str | None:
    found = shutil.which("zizmor")
    if found:
        return found
    import sys

    scripts = Path(sys.executable).resolve().parent
    for name in ("zizmor.exe", "zizmor"):
        cand = scripts / name
        if cand.exists():
            return str(cand)
    return None


def zizmor_available() -> bool:
    return _zizmor_bin() is not None


def run_zizmor_cli(path: Path) -> dict[str, Any]:
    """Run zizmor if installed; return structured result."""
    bin_path = _zizmor_bin()
    if not bin_path:
        return {"available": False, "findings": [], "error": "zizmor not on PATH"}
    try:
        proc = subprocess.run(
            [bin_path, "--format", "json", str(path)],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        findings: list[Any] = []
        if proc.stdout.strip():
            try:
                findings = json.loads(proc.stdout)
            except json.JSONDecodeError:
                findings = [{"raw": proc.stdout[:2000]}]
        return {
            "available": True,
            "returncode": proc.returncode,
            "findings": findings if isinstance(findings, list) else [findings],
            "stderr": proc.stderr[:1000],
        }
    except Exception as exc:  # noqa: BLE001
        return {"available": True, "findings": [], "error": str(exc)}


def _finding_key(finding: Any) -> str:
    """Stable key for set-diff of zizmor findings."""
    if not isinstance(finding, dict):
        return json.dumps(finding, sort_keys=True, default=str)
    for k in ("ident", "id", "fingerprint"):
        if finding.get(k):
            return str(finding[k])
    # Common zizmor SARIF-like / custom fields
    parts = []
    for k in ("determination", "kind", "name", "rule_id", "rule", "message"):
        if k in finding and finding[k] is not None:
            v = finding[k]
            if isinstance(v, dict):
                v = v.get("text") or v.get("markdown") or json.dumps(v, sort_keys=True)
            parts.append(f"{k}={v}")
    loc = finding.get("location") or finding.get("locations") or finding.get("span")
    if loc is not None:
        parts.append(f"loc={json.dumps(loc, sort_keys=True, default=str)}")
    if parts:
        return "|".join(parts)
    # Fallback: subset of stable-ish keys
    subset = {
        k: finding[k]
        for k in sorted(finding.keys())
        if k not in {"url", "link", "persona", "ignored"}
    }
    return json.dumps(subset, sort_keys=True, default=str)


def _finding_keys(findings: list[Any]) -> set[str]:
    return {_finding_key(f) for f in findings}


def run_zizmor_after_only(after_path: Path) -> dict[str, Any]:
    cli = run_zizmor_cli(after_path)
    if not cli.get("available") or cli.get("error"):
        return {
            "method": "zizmor_after_only",
            "predicted_regression": False,
            "available": False,
            "n_findings": 0,
            "error": cli.get("error"),
        }
    findings = cli.get("findings") or []
    return {
        "method": "zizmor_after_only",
        "predicted_regression": bool(findings),
        "available": True,
        "n_findings": len(findings),
        "returncode": cli.get("returncode"),
    }


def run_zizmor_before_after_diff(before_path: Path, after_path: Path) -> dict[str, Any]:
    """Positive only if after findings are a strict worsening vs before."""
    before_cli = run_zizmor_cli(before_path)
    after_cli = run_zizmor_cli(after_path)
    if not before_cli.get("available") or before_cli.get("error"):
        return {
            "method": "zizmor_before_after_diff",
            "predicted_regression": False,
            "available": False,
            "error": before_cli.get("error") or after_cli.get("error"),
            "n_before": 0,
            "n_after": 0,
            "n_new": 0,
        }
    if after_cli.get("error"):
        return {
            "method": "zizmor_before_after_diff",
            "predicted_regression": False,
            "available": False,
            "error": after_cli.get("error"),
            "n_before": len(before_cli.get("findings") or []),
            "n_after": 0,
            "n_new": 0,
        }
    b_findings = before_cli.get("findings") or []
    a_findings = after_cli.get("findings") or []
    b_keys = _finding_keys(b_findings)
    a_keys = _finding_keys(a_findings)
    new_keys = a_keys - b_keys
    # Strict set growth OR count increase when keys collide poorly
    predicted = bool(new_keys) or (len(a_findings) > len(b_findings))
    return {
        "method": "zizmor_before_after_diff",
        "predicted_regression": predicted,
        "available": True,
        "n_before": len(b_findings),
        "n_after": len(a_findings),
        "n_new": len(new_keys),
    }


def _proxy_flags(before_path: Path, after_path: Path) -> list[str]:
    before = extract_signals(load_workflow(before_path))
    after = extract_signals(load_workflow(after_path))
    flags: list[str] = []
    if "pull_request_target" in after.triggers and "pull_request_target" not in before.triggers:
        flags.append("pull_request_target")
    if after.permissions_score >= 90 and before.permissions_score < 90:
        flags.append("broad_permissions")
    if after.privileged_checkout and not before.privileged_checkout:
        flags.append("privileged_checkout")
    return flags


def run_zizmor_proxy(before_path: Path, after_path: Path) -> dict[str, Any]:
    """
    Backward-compatible entry used by older eval code.

    Prefer real CLI after-only semantics when available (historical baseline).
    Also attaches before/after-diff result under `diff` when CLI works.
    """
    after_only = run_zizmor_after_only(after_path)
    diff = run_zizmor_before_after_diff(before_path, after_path)
    proxy_flags = _proxy_flags(before_path, after_path)

    if after_only.get("available"):
        predicted = bool(after_only.get("predicted_regression"))
        method = "zizmor_after_only"
    else:
        predicted = bool(proxy_flags)
        method = "zizmor_proxy"

    return {
        "method": method,
        "predicted_regression": predicted,
        "proxy_flags": proxy_flags,
        "after_only": after_only,
        "diff": diff,
        "cli": {
            "available": after_only.get("available", False),
            "n_findings": after_only.get("n_findings", 0),
        },
    }
