from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


def plot_rule_counts(summary: dict, out: Path) -> None:
    counts = summary.get("rule_counts") or {}
    if not counts:
        return
    labels = list(counts.keys())
    values = [counts[k] for k in labels]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(labels, values, color="#2f5d8c")
    ax.set_xlabel("Rule ID")
    ax.set_ylabel("Count")
    ax.set_title("Security regression rule hits")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_agent_rates(summary: dict, out: Path) -> None:
    rates = summary.get("per_agent_regression_rate") or {}
    if not rates:
        return
    labels = list(rates.keys())
    values = [rates[k] or 0 for k in labels]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(labels, values, color="#6b8f71")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Regression rate")
    ax.set_title("Regression rate by agent label")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_method_f1(summary: dict, out: Path) -> None:
    pol = summary.get("policy_validator") or {}
    after = summary.get("baseline_after_only") or summary.get("baseline") or {}
    diff = summary.get("baseline_before_after_diff") or {}
    fig, ax = plt.subplots(figsize=(7.5, 4))
    methods = ["Policy Validator", "zizmor after-only", "zizmor before/after-diff"]
    f1s = [pol.get("f1", 0), after.get("f1", 0), diff.get("f1", 0)]
    ax.bar(methods, f1s, color=["#2f5d8c", "#a65d3f", "#7a6f9b"])
    ax.set_ylim(0, 1)
    ax.set_ylabel("F1")
    ax.set_title("Detector F1 comparison (field freeze)")
    ax.tick_params(axis="x", rotation=15)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--summary",
        type=Path,
        default=Path("paper/manuscript/tables/eval_summary.json"),
    )
    p.add_argument("--out-dir", type=Path, default=Path("paper/manuscript/figures"))
    args = p.parse_args(argv)
    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    plot_rule_counts(summary, args.out_dir / "rule_counts.png")
    plot_agent_rates(summary, args.out_dir / "agent_rates.png")
    plot_method_f1(summary, args.out_dir / "method_f1.png")
    print(f"Figures written to {args.out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
