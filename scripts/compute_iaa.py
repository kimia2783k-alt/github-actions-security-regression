"""Compute Cohen's kappa and disagreement list from dual annotator CSVs."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _cohen_kappa(y1: list[int], y2: list[int]) -> float:
    n = len(y1)
    if n == 0:
        return float("nan")
    agree = sum(a == b for a, b in zip(y1, y2)) / n
    c1 = Counter(y1)
    c2 = Counter(y2)
    pe = sum((c1[k] / n) * (c2[k] / n) for k in set(c1) | set(c2))
    if pe >= 1.0:
        return 1.0
    return (agree - pe) / (1.0 - pe)


def _read_ann(path: Path) -> dict[str, dict]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    out: dict[str, dict] = {}
    for r in rows:
        pid = r["pair_id"]
        raw = (r.get("has_regression") or "").strip()
        if raw == "":
            continue
        out[pid] = {
            "has_regression": int(float(raw)),
            "rule_ids_optional": r.get("rule_ids_optional", ""),
            "confidence": r.get("confidence", ""),
            "notes": r.get("notes", ""),
            "before_path": r.get("before_path", ""),
            "after_path": r.get("after_path", ""),
        }
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--a", type=Path, default=ROOT / "annotations" / "human_round" / "annotator_A.csv")
    p.add_argument("--b", type=Path, default=ROOT / "annotations" / "human_round" / "annotator_B.csv")
    p.add_argument(
        "--adjudicated",
        type=Path,
        default=ROOT / "annotations" / "human_round" / "gold_human_adjudicated.csv",
    )
    p.add_argument("--out", type=Path, default=ROOT / "paper" / "manuscript" / "tables" / "field")
    args = p.parse_args(argv)

    a = _read_ann(args.a)
    b = _read_ann(args.b)
    common = sorted(set(a) & set(b))
    if not common:
        print(
            "No overlapping filled labels yet. "
            f"Fill {args.a.name} and {args.b.name} (has_regression=0|1) then re-run."
        )
        args.out.mkdir(parents=True, exist_ok=True)
        stub = {
            "status": "pending_annotator_labels",
            "n_filled_a": len(a),
            "n_filled_b": len(b),
            "n_common": 0,
            "cohen_kappa": None,
        }
        (args.out / "iaa_summary.json").write_text(json.dumps(stub, indent=2), encoding="utf-8")
        (args.out / "iaa_summary.md").write_text(
            "# IAA summary\n\n**Status:** pending — annotator CSVs not yet filled.\n",
            encoding="utf-8",
        )
        return 0

    y1 = [a[pid]["has_regression"] for pid in common]
    y2 = [b[pid]["has_regression"] for pid in common]
    kappa = _cohen_kappa(y1, y2)
    agree_n = sum(i == j for i, j in zip(y1, y2))
    disagreements = [
        {
            "pair_id": pid,
            "A": a[pid]["has_regression"],
            "B": b[pid]["has_regression"],
            "before_path": a[pid]["before_path"],
            "after_path": a[pid]["after_path"],
        }
        for pid, i, j in zip(common, y1, y2)
        if i != j
    ]

    summary = {
        "status": "ok",
        "n_common": len(common),
        "n_agree": agree_n,
        "agreement_rate": agree_n / len(common),
        "cohen_kappa": round(kappa, 4),
        "n_disagreements": len(disagreements),
        "disagreements": disagreements,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "iaa_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    md = [
        "# IAA summary (dual human annotation)\n",
        f"- N labeled by both: **{len(common)}**",
        f"- Agreement rate: **{agree_n / len(common):.3f}**",
        f"- Cohen's κ: **{kappa:.4f}**",
        f"- Disagreements: **{len(disagreements)}**",
        "\n## Disagreements\n",
        "| pair_id | A | B |\n|---|---:|---:|",
    ]
    for d in disagreements:
        md.append(f"| `{d['pair_id'][:64]}` | {d['A']} | {d['B']} |")
    (args.out / "iaa_summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # If adjudicated file exists, report counts
    if args.adjudicated.exists():
        adj = list(csv.DictReader(args.adjudicated.open(encoding="utf-8")))
        filled = [r for r in adj if (r.get("has_regression") or "").strip() != ""]
        summary["n_adjudicated"] = len(filled)
        (args.out / "iaa_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps({k: summary[k] for k in summary if k != "disagreements"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
