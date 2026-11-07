"""Pilot descriptive statistics (run as script or convert to notebook)."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
index_path = ROOT / "data" / "interim" / "pilot_index.json"
labels_path = ROOT / "annotations" / "labels_sample.csv"
out_md = ROOT / "paper" / "manuscript" / "tables" / "corpus_descriptive.md"


def main() -> None:
    index = json.loads(index_path.read_text(encoding="utf-8"))
    rows = index.get("rows", [])
    agents = Counter(r.get("agent", "?") for r in rows)
    reg = Counter(bool(r.get("expected_regression")) for r in rows)
    labels = pd.read_csv(labels_path)

    lines = [
        "# Corpus descriptive statistics",
        "",
        f"- Pairs in pilot index: **{len(rows)}**",
        f"- Expected regressions: **{reg[True]}**; non-regressions: **{reg[False]}**",
        "",
        "## By agent label",
        "",
        "| Agent | Count |",
        "|---|---:|",
    ]
    for a, c in sorted(agents.items()):
        lines.append(f"| {a} | {c} |")
    lines += [
        "",
        "## Label file summary",
        "",
        f"- Rows: {len(labels)}",
        f"- Auto positives: {int(labels['auto_has_regression'].sum())}",
        f"- Gold positives: {int(pd.to_numeric(labels['gold_has_regression']).sum())}",
        "",
    ]
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(out_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
