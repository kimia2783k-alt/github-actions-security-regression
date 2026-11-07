from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from evaluate.metrics import binary_metrics
from policy_validator.validator import compare_signals, load_rules
from workflow_parse.signals import extract_signals, load_workflow


def _with_rules_enabled(rules_doc: dict, enabled_ids: set[str]) -> dict:
    doc = json.loads(json.dumps(rules_doc))  # deep copy via json
    for r in doc.get("rules", []):
        r["enabled"] = r.get("id") in enabled_ids
    return doc


def run_ablation(labels_path: Path, out_path: Path) -> dict:
    rows = list(csv.DictReader(labels_path.open(encoding="utf-8")))
    base_rules = load_rules()
    configs = {
        "full": {r["id"] for r in base_rules["rules"]},
        "permissions_only": {"R01", "R02"},
        "pinning_only": {"R05", "R06"},
        "ppe_only": {"R03", "R04", "R09", "R10"},
        "controls_only": {"R08"},
    }
    results = {}
    for name, enabled in configs.items():
        rules = _with_rules_enabled(base_rules, enabled)
        y_true, y_pred = [], []
        for row in rows:
            g = row.get("gold_has_regression", "")
            if g == "":
                g = row.get("auto_has_regression", "")
            if g == "":
                continue
            truth = int(float(g))
            before = load_workflow(row["before_path"])
            after = load_workflow(row["after_path"])
            keywords = list(rules.get("security_action_keywords") or [])
            findings = compare_signals(
                extract_signals(before, keywords),
                extract_signals(after, keywords),
                rules,
            )
            pred = int(bool(findings))
            y_true.append(truth)
            y_pred.append(pred)
        # Note: gold is full-taxonomy; ablation metrics are indicative
        results[name] = binary_metrics(y_true, y_pred).as_dict() | {"n": len(y_true)}

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--labels", type=Path, default=Path("annotations/labels_sample.csv"))
    p.add_argument("--out", type=Path, default=Path("paper/manuscript/tables/ablation.json"))
    args = p.parse_args(argv)
    res = run_ablation(args.labels, args.out)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
