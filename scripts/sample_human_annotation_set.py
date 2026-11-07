"""Build stratified dual-annotation pack (N≈80) without validator predictions."""
from __future__ import annotations

import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "annotations" / "labels_aidev.csv"
OUT_DIR = ROOT / "annotations" / "human_round"
SEED = 42
TARGET_N = 80


def _stratum(agent: str) -> str:
    a = (agent or "").strip().lower()
    if a == "human":
        return "human"
    if "codex" in a:
        return "codex"
    return "other_agent"


def main() -> int:
    rows = list(csv.DictReader(LABELS.open(encoding="utf-8")))
    for r in rows:
        r["_gold"] = int(float(r.get("gold_has_regression") or 0))
        r["_stratum"] = _stratum(r.get("agent") or "")

    positives = [r for r in rows if r["_gold"] == 1]
    negatives = [r for r in rows if r["_gold"] == 0]
    rng = random.Random(SEED)

    selected = list(positives)  # all v3 positives (46)
    need = max(0, TARGET_N - len(selected))
    # stratify negatives: prefer mix of human / codex / other
    neg_by = {"human": [], "codex": [], "other_agent": []}
    for r in negatives:
        neg_by[r["_stratum"]].append(r)
    for k in neg_by:
        rng.shuffle(neg_by[k])
    picks: list[dict] = []
    # round-robin strata until need filled
    keys = ["codex", "human", "other_agent"]
    i = 0
    while len(picks) < need and any(neg_by[k] for k in keys):
        k = keys[i % len(keys)]
        if neg_by[k]:
            picks.append(neg_by[k].pop())
        i += 1
    selected.extend(picks)
    rng.shuffle(selected)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_fields = [
        "pair_id",
        "agent",
        "stratum",
        "before_path",
        "after_path",
        "predicate_gold_v3",  # for analysts only — strip from annotator sheets
    ]
    with (OUT_DIR / "pairs_manifest.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=manifest_fields)
        w.writeheader()
        for r in selected:
            w.writerow(
                {
                    "pair_id": r["pair_id"],
                    "agent": r.get("agent"),
                    "stratum": r["_stratum"],
                    "before_path": r["before_path"],
                    "after_path": r["after_path"],
                    "predicate_gold_v3": r["_gold"],
                }
            )

    ann_fields = ["pair_id", "before_path", "after_path", "has_regression", "rule_ids_optional", "confidence", "notes"]
    for name in ("annotator_A.csv", "annotator_B.csv"):
        with (OUT_DIR / name).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=ann_fields)
            w.writeheader()
            for r in selected:
                w.writerow(
                    {
                        "pair_id": r["pair_id"],
                        "before_path": r["before_path"],
                        "after_path": r["after_path"],
                        "has_regression": "",  # 0 or 1
                        "rule_ids_optional": "",
                        "confidence": "",  # low|med|high
                        "notes": "",
                    }
                )

    # Analyst-only key (not for annotators)
    with (OUT_DIR / "predicate_gold_key.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["pair_id", "predicate_gold_v3", "stratum"])
        w.writeheader()
        for r in selected:
            w.writerow(
                {
                    "pair_id": r["pair_id"],
                    "predicate_gold_v3": r["_gold"],
                    "stratum": r["_stratum"],
                }
            )

    n_pos = sum(1 for r in selected if r["_gold"] == 1)
    print(
        f"wrote {len(selected)} pairs to {OUT_DIR} "
        f"(positives={n_pos}, negatives={len(selected)-n_pos}, seed={SEED})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
