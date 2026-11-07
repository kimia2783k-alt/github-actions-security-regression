"""Evaluate policy validator against adjudicated human gold (when filled)."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from evaluate.metrics import binary_metrics  # noqa: E402
from policy_validator.validator import validate_paths  # noqa: E402


def main() -> int:
    adj = ROOT / "annotations" / "human_round" / "gold_human_adjudicated.csv"
    if not adj.exists():
        print("missing adjudicated file")
        return 1
    rows = [r for r in csv.DictReader(adj.open(encoding="utf-8")) if (r.get("has_regression") or "").strip() != ""]
    if len(rows) < 5:
        print(f"only {len(rows)} adjudicated rows; need filled gold_human_adjudicated.csv")
        out = {
            "status": "pending_adjudication",
            "n": len(rows),
        }
        outp = ROOT / "paper" / "manuscript" / "tables" / "field" / "eval_human_gold.json"
        outp.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(json.dumps(out, indent=2))
        return 0

    y_true: list[int] = []
    y_pred: list[int] = []
    for r in rows:
        before = Path(r["before_path"])
        after = Path(r["after_path"])
        findings = validate_paths(before, after)
        pred = int(any(f.rule_id != "PARSE" for f in findings))
        y_true.append(int(float(r["has_regression"])))
        y_pred.append(pred)
    m = binary_metrics(y_true, y_pred).as_dict()
    summary = {"status": "ok", "n": len(y_true), "policy_validator": m}
    outp = ROOT / "paper" / "manuscript" / "tables" / "field" / "eval_human_gold.json"
    outp.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
