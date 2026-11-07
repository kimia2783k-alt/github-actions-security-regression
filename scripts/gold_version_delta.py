"""Reconstruct gold-label transitions across policy versions on the same N=330 set.

interim ≈ early heuristic (no R12–R15; docker NOT trusted for R06)
v2     ≈ formal trusted owners + pin/comment; still no R12–R15
v3     ≈ current field_gold_audit / labels_aidev.csv gold columns
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USES_RE = re.compile(
    r"(?m)^\s*-?\s*uses:\s*[\"']?([^\"'\s#]+)[\"']?\s*(?:#\s*([0-9a-fA-F]{40}))?"
)
SHA = re.compile(r"^[0-9a-f]{40}$", re.I)
TRUSTED_V2 = {
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
TRUSTED_INTERIM = TRUSTED_V2 - {"docker"}
DANG = (
    "contents",
    "id-token",
    "actions",
    "packages",
    "security-events",
    "deployments",
    "environments",
    "attestations",
)
PIPE = re.compile(
    r"curl\b[^\n|]{0,120}\|\s*(?:ba)?sh\b|wget\b[^\n|]{0,120}\|\s*(?:ba)?sh\b",
    re.I,
)
ENV_INJ = re.compile(
    r"(?:echo|printf).{0,120}github\.(event|head_ref).{0,80}GITHUB_(?:ENV|PATH)"
    r"|GITHUB_(?:ENV|PATH).{0,80}github\.(event|head_ref)",
    re.I | re.S,
)


def parse_actions(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    out: list[dict] = []
    for m in USES_RE.finditer(text):
        uses = m.group(1).strip()
        comment = m.group(2)
        if uses.startswith("./") or uses.startswith(".\\"):
            owner, name, ref, eff = "local", uses, "local", True
        elif "@" not in uses:
            owner, name, ref, eff = "unknown", uses.lower(), "", False
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


def audit(bp: Path, ap: Path, trusted: set[str], with_r12_r15: bool) -> tuple[int, list[str]]:
    b_acts, a_acts = parse_actions(bp), parse_actions(ap)
    gold = 0
    rules: list[str] = []
    b_best: dict = {}
    for a in b_acts:
        prev = b_best.get(a["key"])
        if prev is None or (a["effectively_pinned"] and not prev["effectively_pinned"]):
            b_best[a["key"]] = a
    a_by_key: dict = {}
    for a in a_acts:
        a_by_key.setdefault(a["key"], []).append(a)
    for key, b in b_best.items():
        if not b["effectively_pinned"]:
            continue
        if any(not a["effectively_pinned"] for a in a_by_key.get(key, [])):
            gold = 1
            rules.append("R05")
            break
    b_ids = {a["identity"] for a in b_acts}
    for a in a_acts:
        if a["identity"] in b_ids:
            continue
        if a["owner"] in trusted or a["owner"] == "local":
            continue
        if not a["effectively_pinned"]:
            gold = 1
            rules.append("R06")
    bt = bp.read_text(encoding="utf-8", errors="replace")
    at = ap.read_text(encoding="utf-8", errors="replace")
    if re.search(r"permissions:\s*write-all", at) and not re.search(
        r"permissions:\s*write-all", bt
    ):
        gold = 1
        rules.append("R01")
    if "pull_request_target" in at and "pull_request_target" not in bt:
        gold = 1
        rules.append("R03")
    if re.search(r"(?m)^\s*workflow_run\s*:", at) and not re.search(
        r"(?m)^\s*workflow_run\s*:", bt
    ):
        gold = 1
        rules.append("R09")
    if re.search(r"self-hosted", at) and not re.search(r"self-hosted", bt):
        gold = 1
        rules.append("R11")
    if with_r12_r15:
        write_all_new = bool(
            re.search(r"permissions:\s*write-all", at)
            and not re.search(r"permissions:\s*write-all", bt)
        )
        if not write_all_new:
            for scope in DANG:
                pat = rf"(?m)^\s*{re.escape(scope)}\s*:\s*write\b"
                if re.search(pat, at) and not re.search(pat, bt):
                    gold = 1
                    rules.append("R12")
                    break
        if PIPE.search(at) and not PIPE.search(bt):
            gold = 1
            rules.append("R13")
        for t in ("issue_comment", "discussion_comment", "pull_request_review_comment"):
            if re.search(rf"(?m)^\s*{t}\s*:", at) and not re.search(rf"(?m)^\s*{t}\s*:", bt):
                gold = 1
                rules.append("R14")
                break
        if ENV_INJ.search(at) and not ENV_INJ.search(bt):
            gold = 1
            rules.append("R15")
    return gold, sorted(set(rules))


def main() -> int:
    rows = list(csv.DictReader((ROOT / "annotations" / "labels_aidev.csv").open(encoding="utf-8")))
    interim_pos = v2_pos = v3_pos = 0
    newly_pos: list[dict] = []
    flipped_neg: list[dict] = []
    rule_gain = Counter()
    for r in rows:
        bp, ap = Path(r["before_path"]), Path(r["after_path"])
        g_i, rules_i = audit(bp, ap, TRUSTED_INTERIM, False)
        g_2, _rules_2 = audit(bp, ap, TRUSTED_V2, False)
        g_3 = int(float(r.get("gold_has_regression") or 0))
        rules_3 = [x for x in (r.get("gold_rule_ids") or "").split("|") if x]
        interim_pos += g_i
        v2_pos += g_2
        v3_pos += g_3
        if g_i == 0 and g_3 == 1:
            added = [x for x in rules_3 if x not in rules_i]
            for a in added or rules_3 or ["OTHER"]:
                rule_gain[a] += 1
            newly_pos.append(
                {
                    "pair_id": r["pair_id"],
                    "agent": r.get("agent"),
                    "new_rules": "|".join(rules_3),
                }
            )
        if g_i == 1 and g_3 == 0:
            flipped_neg.append(
                {
                    "pair_id": r["pair_id"],
                    "agent": r.get("agent"),
                    "old_rules": "|".join(rules_i),
                }
            )

    out_dir = ROOT / "paper" / "manuscript" / "tables" / "field"
    out_dir.mkdir(parents=True, exist_ok=True)
    md = [
        "# Gold-label version delta (same N=330 set)\n",
        "Reconstruction note: interim/v2 columns are **reconstructed** by replaying",
        "historical audit predicates on the same paths; v3 is the current CSV gold.\n",
        "| Version | Predicate family | Gold positives | Rate |",
        "|---|---|---:|---:|",
        f"| Interim (reconstructed) | R01/R03/R05/R06*/R09/R11; docker not trusted | {interim_pos} | {interim_pos/330:.3f} |",
        f"| v2 (reconstructed) | + trusted docker/formal pin; still no R12–R15 | {v2_pos} | {v2_pos/330:.3f} |",
        f"| **v3 (current)** | + R12–R15 + formal signals | **{v3_pos}** | **{v3_pos/330:.3f}** |",
        "\n\\*Interim R06 treated `docker/*` as third-party.\n",
        f"\nNewly positive vs interim: **{len(newly_pos)}**; flipped interim→neg under v3: **{len(flipped_neg)}**.\n",
        "## Rule tags among newly-positive pairs (count of rule appearances)\n",
        "| Rule | Count |",
        "|---|---:|",
    ]
    for k, v in rule_gain.most_common():
        md.append(f"| {k} | {v} |")
    md += [
        "\n## Sample newly-positive pair_ids (up to 15)\n",
        "| pair_id | agent | gold_rule_ids |",
        "|---|---|---|",
    ]
    for row in newly_pos[:15]:
        md.append(f"| `{row['pair_id'][:72]}` | {row['agent']} | {row['new_rules']} |")
    if flipped_neg:
        md += [
            "\n## Sample flipped to negative (trusted-owner realignment)\n",
            "| pair_id | agent | old_rules |",
            "|---|---|---|",
        ]
        for row in flipped_neg[:10]:
            md.append(f"| `{row['pair_id'][:72]}` | {row['agent']} | {row['old_rules']} |")
    (out_dir / "gold_v_delta.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    summary = {
        "n": 330,
        "interim_pos": interim_pos,
        "v2_pos": v2_pos,
        "v3_pos": v3_pos,
        "newly_positive_vs_interim": len(newly_pos),
        "flipped_to_negative": len(flipped_neg),
        "rule_gain": dict(rule_gain),
    }
    (out_dir / "gold_v_delta.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
