"""Build independent gold labels for field pairs via before/after action diffs.

Aligned with policies/rule_formal_spec.md v2:
- R05: same (owner, name) lost effective pin (ref SHA or # comment SHA)
- R06: new (owner, name, ref) unpinned third-party
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

USES_RE = re.compile(
    r"(?m)^\s*-?\s*uses:\s*[\"']?([^\"'\s#]+)[\"']?\s*(?:#\s*([0-9a-fA-F]{40}))?"
)
SHA = re.compile(r"^[0-9a-f]{40}$", re.I)
TRUSTED = {
    "actions",
    "github",
    "aquasecurity",
    "ossf",
    "step-security",
    "docker",
    "aws-actions",
    "azure",
    "google-github-actions",
}


def parse_actions(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    out: list[dict] = []
    for m in USES_RE.finditer(text):
        uses = m.group(1).strip()
        comment = m.group(2)
        if uses.startswith("./") or uses.startswith(".\\"):
            owner, name, ref = "local", uses, "local"
            eff = True
        elif "@" not in uses:
            owner, name, ref = "unknown", uses.lower(), ""
            eff = False
        else:
            left, ref = uses.rsplit("@", 1)
            ref = ref.strip()
            parts = left.split("/")
            owner = (parts[0] if parts else "unknown").lower()
            name = "/".join(parts[1:]).lower() if len(parts) > 1 else left.lower()
            eff = bool(SHA.fullmatch(ref)) or bool(comment and SHA.fullmatch(comment))
        out.append(
            {
                "uses": uses,
                "owner": owner,
                "name": name,
                "ref": ref,
                "key": (owner, name),
                "identity": (owner, name, ref),
                "effectively_pinned": eff,
            }
        )
    return out


def main() -> int:
    labels = Path("annotations/labels_aidev.csv")
    rows = list(csv.DictReader(labels.open(encoding="utf-8")))
    overrides: dict = {}
    for r in rows:
        bp, ap = Path(r["before_path"]), Path(r["after_path"])
        b_acts, a_acts = parse_actions(bp), parse_actions(ap)
        gold = 0
        rules: list[str] = []
        notes: list[str] = []

        b_best: dict[tuple[str, str], dict] = {}
        for a in b_acts:
            prev = b_best.get(a["key"])
            if prev is None or (a["effectively_pinned"] and not prev["effectively_pinned"]):
                b_best[a["key"]] = a
        a_by_key: dict[tuple[str, str], list] = {}
        for a in a_acts:
            a_by_key.setdefault(a["key"], []).append(a)
        unpin = []
        for key, b in b_best.items():
            if not b["effectively_pinned"]:
                continue
            for a in a_by_key.get(key, []):
                if not a["effectively_pinned"]:
                    unpin.append(f"{key[0]}/{key[1]}@{b['ref']}->{a['ref']}")
                    break
        if unpin:
            gold = 1
            rules.append("R05")
            notes.append("unpin")

        b_ids = {a["identity"] for a in b_acts}
        for a in a_acts:
            if a["identity"] in b_ids:
                continue
            if a["owner"] in TRUSTED or a["owner"] == "local":
                continue
            if not a["effectively_pinned"]:
                gold = 1
                rules.append("R06")
                notes.append(f"new:{a['uses']}")

        bt = bp.read_text(encoding="utf-8", errors="replace")
        at = ap.read_text(encoding="utf-8", errors="replace")
        if re.search(r"permissions:\s*write-all", at) and not re.search(
            r"permissions:\s*write-all", bt
        ):
            gold = 1
            rules.append("R01")
            notes.append("write_all")
        if "pull_request_target" in at and "pull_request_target" not in bt:
            gold = 1
            rules.append("R03")
            notes.append("pr_target")
        if "workflow_run" in at and "workflow_run" not in bt:
            # only count as gold if it's a trigger-like occurrence; crude but aligned
            if re.search(r"(?m)^\s*workflow_run\s*:", at) or "workflow_run" in re.findall(
                r"on:\s*\[([^\]]+)\]", at
            ):
                gold = 1
                rules.append("R09")
                notes.append("workflow_run")
        if re.search(r"self-hosted", at) and not re.search(r"self-hosted", bt):
            gold = 1
            rules.append("R11")
            notes.append("self_hosted")
        # R12: dangerous write scopes newly present (without new write-all → R01)
        dang = (
            "contents",
            "id-token",
            "actions",
            "packages",
            "security-events",
            "deployments",
            "environments",
            "attestations",
        )
        write_all_new = bool(
            re.search(r"permissions:\s*write-all", at)
            and not re.search(r"permissions:\s*write-all", bt)
        )
        if not write_all_new:
            for scope in dang:
                pat = rf"(?m)^\s*{re.escape(scope)}\s*:\s*write\b"
                if re.search(pat, at) and not re.search(pat, bt):
                    gold = 1
                    rules.append("R12")
                    notes.append(f"scope:{scope}")
                    break
        # R13 remote shell pipe
        pipe = re.compile(
            r"curl\b[^\n|]{0,120}\|\s*(?:ba)?sh\b|wget\b[^\n|]{0,120}\|\s*(?:ba)?sh\b",
            re.I,
        )
        if pipe.search(at) and not pipe.search(bt):
            gold = 1
            rules.append("R13")
            notes.append("curl_bash")
        # R14 interactive triggers
        for t in ("issue_comment", "discussion_comment", "pull_request_review_comment"):
            if re.search(rf"(?m)^\s*{t}\s*:", at) and not re.search(rf"(?m)^\s*{t}\s*:", bt):
                gold = 1
                rules.append("R14")
                notes.append(t)
                break
        # R15 GITHUB_ENV with github context
        env_inj = re.compile(
            r"(?:echo|printf).{0,120}github\.(event|head_ref).{0,80}GITHUB_(?:ENV|PATH)"
            r"|GITHUB_(?:ENV|PATH).{0,80}github\.(event|head_ref)",
            re.I | re.S,
        )
        if env_inj.search(at) and not env_inj.search(bt):
            gold = 1
            rules.append("R15")
            notes.append("github_env")
        rules = sorted(set(rules))
        overrides[r["pair_id"]] = {
            "gold_has_regression": gold,
            "gold_rule_ids": "|".join(rules),
            "notes": ";".join(notes) or ("neg" if gold == 0 else "pos"),
        }

    out = Path("annotations/gold_overrides.json")
    out.write_text(json.dumps(overrides, indent=2), encoding="utf-8")
    pos = sum(1 for v in overrides.values() if v["gold_has_regression"] == 1)
    print(f"gold_pos={pos}/{len(overrides)} -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
