from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from baselines.zizmor_baseline import (
    run_zizmor_after_only,
    run_zizmor_before_after_diff,
    run_zizmor_proxy,
)
from evaluate.metrics import ai_vs_human_test, binary_metrics
from policy_validator.validator import validate_paths


def _read_labels(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _truth(row: dict) -> int | None:
    g = row.get("gold_has_regression", "")
    if g == "" or g is None:
        a = row.get("auto_has_regression", "")
        return int(a) if a != "" else None
    return int(float(g))


def run(labels_path: Path, out_dir: Path) -> dict:
    rows = _read_labels(labels_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    y_true: list[int] = []
    y_policy: list[int] = []
    y_base_after: list[int] = []
    y_base_diff: list[int] = []
    times: list[float] = []
    rule_counter: Counter[str] = Counter()
    agent_reg: dict[str, list[int]] = defaultdict(list)
    detail_rows = []
    zizmor_cli_ok = False

    for row in rows:
        truth = _truth(row)
        if truth is None:
            continue
        before = Path(row["before_path"])
        after = Path(row["after_path"])
        t0 = time.perf_counter()
        findings = validate_paths(before, after)
        elapsed = time.perf_counter() - t0
        times.append(elapsed)
        pred = int(any(f.rule_id != "PARSE" for f in findings))
        for f in findings:
            if f.rule_id != "PARSE":
                rule_counter[f.rule_id] += 1

        # Prefer dual CLI baselines; fall back to proxy wrapper
        after_only = run_zizmor_after_only(after)
        diff = run_zizmor_before_after_diff(before, after)
        if after_only.get("available"):
            zizmor_cli_ok = True
            pred_after = int(bool(after_only.get("predicted_regression")))
            pred_diff = int(bool(diff.get("predicted_regression")))
            method_after = "zizmor_after_only"
            method_diff = "zizmor_before_after_diff"
        else:
            proxy = run_zizmor_proxy(before, after)
            pred_after = int(bool(proxy["predicted_regression"]))
            pred_diff = int(bool(proxy.get("diff", {}).get("predicted_regression")))
            method_after = proxy["method"]
            method_diff = proxy.get("diff", {}).get("method", "zizmor_proxy")

        y_true.append(truth)
        y_policy.append(pred)
        y_base_after.append(pred_after)
        y_base_diff.append(pred_diff)
        agent = row.get("agent") or "unknown"
        agent_reg[agent].append(truth)

        detail_rows.append(
            {
                "pair_id": row.get("pair_id"),
                "agent": agent,
                "gold": truth,
                "policy_pred": pred,
                "baseline_after_pred": pred_after,
                "baseline_diff_pred": pred_diff,
                "baseline_after_method": method_after,
                "baseline_diff_method": method_diff,
                "rules": "|".join(f.rule_id for f in findings if f.rule_id != "PARSE"),
                "seconds": round(elapsed, 6),
            }
        )

    policy_m = binary_metrics(y_true, y_policy).as_dict()
    base_after_m = binary_metrics(y_true, y_base_after).as_dict()
    base_diff_m = binary_metrics(y_true, y_base_diff).as_dict()

    ai_agents = {
        "copilot",
        "codex",
        "cursor",
        "devin",
        "claude_code",
        "jules",
        "openai_codex",
        "github_copilot",
        "claude",
        "devin_ai",
    }

    def _is_ai(name: str) -> bool:
        n = (name or "").strip().lower().replace("-", "_").replace(" ", "_")
        if n in ai_agents or n == "human":
            return n != "human"
        return any(k in n for k in ("codex", "copilot", "cursor", "devin", "claude", "jules", "gpt"))

    ai_vals = [v for a, vals in agent_reg.items() if _is_ai(a) for v in vals]
    human_vals = [v for a, vals in agent_reg.items() if (a or "").strip().lower() == "human" for v in vals]
    stats = None
    if ai_vals and human_vals:
        stats = ai_vs_human_test(sum(ai_vals), len(ai_vals), sum(human_vals), len(human_vals))

    summary = {
        "n": len(y_true),
        "regression_rate": (sum(y_true) / len(y_true)) if y_true else None,
        "policy_validator": policy_m,
        "baseline": base_after_m,  # backward-compatible alias (= after-only)
        "baseline_after_only": base_after_m,
        "baseline_before_after_diff": base_diff_m,
        "zizmor_cli_available": zizmor_cli_ok,
        "mean_seconds": (sum(times) / len(times)) if times else None,
        "rule_counts": dict(rule_counter),
        "per_agent_regression_rate": {
            a: (sum(v) / len(v) if v else None) for a, v in sorted(agent_reg.items())
        },
        "ai_vs_human": stats,
    }

    with open(out_dir / "eval_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with open(out_dir / "eval_details.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(detail_rows[0].keys()) if detail_rows else ["pair_id"])
        w.writeheader()
        for r in detail_rows:
            w.writerow(r)

    md = []
    md.append("# Evaluation Tables (auto-generated)\n")
    md.append("## Detector performance\n")
    md.append("| Method | Precision | Recall | F1 | FPR | N |\n|---|---:|---:|---:|---:|---:|")
    md.append(
        f"| Policy Validator | {policy_m['precision']} | {policy_m['recall']} | "
        f"{policy_m['f1']} | {policy_m['fpr']} | {summary['n']} |"
    )
    md.append(
        f"| Zizmor after-only | {base_after_m['precision']} | {base_after_m['recall']} | "
        f"{base_after_m['f1']} | {base_after_m['fpr']} | {summary['n']} |"
    )
    md.append(
        f"| Zizmor before/after-diff | {base_diff_m['precision']} | {base_diff_m['recall']} | "
        f"{base_diff_m['f1']} | {base_diff_m['fpr']} | {summary['n']} |"
    )
    md.append("\n## Rule hit counts\n")
    md.append("| Rule | Count |\n|---|---:|")
    for k, v in sorted(rule_counter.items()):
        md.append(f"| {k} | {v} |")
    if stats:
        md.append("\n## AI vs Human\n")
        md.append(f"- AI regression rate: {stats['ai_rate']}")
        md.append(f"- Human regression rate: {stats['human_rate']}")
        md.append(f"- Test: {stats['test']} p={stats['p_value']}")
    (out_dir / "tables_eval.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run evaluation for policy validator")
    p.add_argument("--labels", type=Path, default=Path("annotations/labels_sample.csv"))
    p.add_argument("--out", type=Path, default=Path("paper/manuscript/tables"))
    args = p.parse_args(argv)
    summary = run(args.labels, args.out)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
