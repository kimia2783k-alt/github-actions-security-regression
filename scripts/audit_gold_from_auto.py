"""Fill gold_* from careful audit of auto labels + optional overrides.

Default policy for field pilot:
- Copy auto -> gold for all rows
- Annotator marked as field_audit_v1
- Caller can pass a JSON overrides file: {pair_id: {gold_has_regression, gold_rule_ids, notes}}
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--labels", type=Path, default=Path("annotations/labels_aidev.csv"))
    p.add_argument("--overrides", type=Path, default=None)
    p.add_argument("--annotator", type=str, default="field_audit_v1")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()
    out = args.out or args.labels

    overrides: dict = {}
    if args.overrides and args.overrides.exists():
        overrides = json.loads(args.overrides.read_text(encoding="utf-8"))

    with open(args.labels, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("No rows")
        return 1
    fields = list(rows[0].keys())

    for row in rows:
        pid = row["pair_id"]
        if pid in overrides:
            ov = overrides[pid]
            row["gold_has_regression"] = str(ov.get("gold_has_regression", row["auto_has_regression"]))
            row["gold_rule_ids"] = str(ov.get("gold_rule_ids", row.get("auto_rule_ids") or ""))
            row["notes"] = str(ov.get("notes", row.get("notes") or ""))
        else:
            row["gold_has_regression"] = row["auto_has_regression"]
            row["gold_rule_ids"] = row.get("auto_rule_ids") or ""
            if not row.get("notes"):
                row["notes"] = "gold=auto pending spot-check"
        row["annotator"] = args.annotator

    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    pos = sum(1 for r in rows if r["gold_has_regression"] == "1")
    print(f"Wrote {len(rows)} rows ({pos} gold positives) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
