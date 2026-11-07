"""Analyze field false negatives: gold=1 but policy validator predicts 0."""
from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from policy_validator.validator import validate_paths  # noqa: E402
from workflow_parse.signals import extract_signals, load_workflow  # noqa: E402

USES_RE = re.compile(r"(?m)^\s*-?\s*uses:\s*([^\s#'\"]+|['\"][^'\"]+['\"])\s*(#\s*([0-9a-fA-F]{40}))?")
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


def _parse_uses_line(raw: str) -> tuple[str, str, str, bool]:
    u = raw.strip().strip("'\"")
    if u.startswith("./") or u.startswith(".\\"):
        return "local", u, "local", True
    if "@" not in u:
        return "unknown", u, "", False
    left, ref = u.rsplit("@", 1)
    parts = left.split("/")
    owner = (parts[0] if parts else "unknown").lower()
    name = "/".join(parts[1:]).lower() if len(parts) > 1 else left.lower()
    pinned = bool(SHA.match(ref.strip()))
    return owner, name, ref.strip(), pinned


def raw_action_scan(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for m in USES_RE.finditer(text):
        uses = m.group(1).strip().strip("'\"")
        comment_sha = m.group(3)
        owner, name, ref, pinned = _parse_uses_line(uses)
        eff = pinned or bool(comment_sha and SHA.match(comment_sha))
        out.append(
            {
                "uses": uses,
                "owner": owner,
                "name": name,
                "ref": ref,
                "pinned": pinned,
                "comment_sha": comment_sha,
                "effectively_pinned": eff,
                "key": (owner, name),
                "identity": (owner, name, ref),
            }
        )
    return out


def classify_pair(before: Path, after: Path) -> list[str]:
    tags: list[str] = []
    bt = before.read_text(encoding="utf-8", errors="replace")
    at = after.read_text(encoding="utf-8", errors="replace")
    b_acts = raw_action_scan(before)
    a_acts = raw_action_scan(after)
    b_keys = {a["key"]: a for a in b_acts}
    for a in a_acts:
        prev = b_keys.get(a["key"])
        if prev and prev["effectively_pinned"] and not a["effectively_pinned"]:
            tags.append("R05_expected")
            break
    b_ids = {a["identity"] for a in b_acts}
    for a in a_acts:
        if a["identity"] in b_ids:
            continue
        if a["owner"] in TRUSTED or a["owner"] == "local":
            continue
        if not a["effectively_pinned"]:
            tags.append("R06_expected")
            break
    if re.search(r"permissions:\s*write-all", at) and not re.search(
        r"permissions:\s*write-all", bt
    ):
        tags.append("R01_expected")
    if "pull_request_target" in at and "pull_request_target" not in bt:
        tags.append("R03_expected")
    if re.search(r"self-hosted", at) and not re.search(r"self-hosted", bt):
        tags.append("R11_expected")
    if "workflow_run" in at and "workflow_run" not in bt:
        tags.append("R09_expected")
    # signal-level check for other gaps
    try:
        sb = extract_signals(load_workflow(before))
        sa = extract_signals(load_workflow(after))
        if sa.parse_error or sb.parse_error:
            tags.append("PARSE")
        if sb.security_step_keys - sa.security_step_keys:
            tags.append("R08_expected")
    except Exception:  # noqa: BLE001
        tags.append("PARSE")
    if not tags:
        tags.append("UNKNOWN_GOLD_OR_OTHER")
    return tags


def main() -> int:
    labels = ROOT / "annotations" / "labels_aidev.csv"
    details = ROOT / "paper" / "manuscript" / "tables" / "field" / "eval_details.csv"
    rows = list(csv.DictReader(labels.open(encoding="utf-8")))
    pred_map: dict[str, dict] = {}
    if details.exists():
        for d in csv.DictReader(details.open(encoding="utf-8")):
            pred_map[d["pair_id"]] = d

    fn_rows = []
    cat = Counter()
    for r in rows:
        gold = r.get("gold_has_regression", "")
        if gold == "" or int(float(gold)) != 1:
            continue
        pid = r["pair_id"]
        before, after = Path(r["before_path"]), Path(r["after_path"])
        # live policy pred
        findings = validate_paths(before, after) if before.exists() and after.exists() else []
        pred = int(any(f.rule_id != "PARSE" for f in findings))
        if pred == 1:
            continue
        tags = classify_pair(before, after) if before.exists() and after.exists() else ["MISSING_FILE"]
        for t in tags:
            cat[t] += 1
        fn_rows.append(
            {
                "pair_id": pid,
                "agent": r.get("agent"),
                "tags": "|".join(tags),
                "old_detail_pred": pred_map.get(pid, {}).get("policy_pred", ""),
                "old_rules": pred_map.get(pid, {}).get("rules", ""),
            }
        )

    out_dir = ROOT / "paper" / "manuscript" / "tables" / "field"
    out_dir.mkdir(parents=True, exist_ok=True)
    md = ["# Field false-negative analysis\n", f"FN count (live validator): **{len(fn_rows)}**\n"]
    md.append("## Category counts\n")
    md.append("| Tag | Count |\n|---|---:|")
    for k, v in cat.most_common():
        md.append(f"| {k} | {v} |")
    md.append("\n## FN pairs\n")
    md.append("| pair_id | agent | tags |\n|---|---|---|")
    for row in fn_rows:
        md.append(f"| {row['pair_id']} | {row['agent']} | {row['tags']} |")
    (out_dir / "fn_analysis.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    with (out_dir / "fn_analysis.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pair_id", "agent", "tags", "old_detail_pred", "old_rules"])
        w.writeheader()
        w.writerows(fn_rows)
    print(f"FN={len(fn_rows)} categories={dict(cat)} -> {out_dir / 'fn_analysis.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
