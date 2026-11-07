from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from policy_validator.validator import validate_paths


def prelabel_pairs(index_path: Path, out_csv: Path) -> int:
    data = json.loads(index_path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        rows = data.get("rows", [])
    else:
        rows = []
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "pair_id",
        "agent",
        "source",
        "before_path",
        "after_path",
        "auto_has_regression",
        "auto_rule_ids",
        "auto_severity_max",
        "gold_has_regression",
        "gold_rule_ids",
        "annotator",
        "notes",
    ]
    n = 0
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            before = row.get("before_path")
            after = row.get("after_path")
            if not before or not after:
                continue
            findings = validate_paths(before, after)
            rule_ids = [x.rule_id for x in findings if x.rule_id != "PARSE"]
            sev_order = {"critical": 3, "high": 2, "medium": 1, "low": 0, "info": -1}
            sev = max((sev_order.get(x.severity, 0) for x in findings), default=-1)
            sev_name = {v: k for k, v in sev_order.items()}.get(sev, "")
            gold = row.get("expected_regression")
            w.writerow(
                {
                    "pair_id": row.get("pair_id", ""),
                    "agent": row.get("agent", ""),
                    "source": row.get("source", ""),
                    "before_path": before,
                    "after_path": after,
                    "auto_has_regression": int(bool(rule_ids)),
                    "auto_rule_ids": "|".join(rule_ids),
                    "auto_severity_max": sev_name,
                    "gold_has_regression": "" if gold is None else int(bool(gold)),
                    "gold_rule_ids": "",
                    "annotator": "auto",
                    "notes": "",
                }
            )
            n += 1
    return n


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--index", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("annotations/labels_auto.csv"))
    args = p.parse_args(argv)
    n = prelabel_pairs(args.index, args.out)
    print(f"Prelabeled {n} pairs -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
