"""Sync Project_Guide_EN_0_to_100.md metrics to pin-semantics freeze."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "paper" / "manuscript" / "Project_Guide_EN_0_to_100.md"
text = path.read_text(encoding="utf-8")
replacements = [
    (
        "| Policy Validator | 0.90 | 0.96 | 0.93 | 0.02 | 0.04 |",
        "| Policy Validator | 0.88 | 0.93 | 0.91 | 0.02 | 0.07 |",
    ),
    (
        "| Policy Validator | 0.85 | 0.94 | 0.89 | 0.22 | 0.06 | 63 |",
        "| Policy Validator | 0.87 | 0.94 | 0.91 | 0.19 | 0.06 | 63 |",
    ),
    (
        "validator reaches about P0.90 / R0.96 / FPR0.02.",
        "validator reaches about P0.88 / R0.93 / FPR0.02.",
    ),
    (
        "strong agreement (F1≈0.89).",
        "strong agreement (F1≈0.91).",
    ),
    (
        "strong predicate-aligned field metrics (about precision 0.90, recall 0.96, FPR 0.02), and F1 about 0.89 against human labels.",
        "strong predicate-aligned field metrics (about precision 0.88, recall 0.93, FPR 0.02), and F1 about 0.91 against human labels.",
    ),
    (
        "On human gold, FPR is higher (~0.22)",
        "On human gold, FPR is higher (~0.19)",
    ),
    (
        "- Validator ≈ P0.90 R0.96 F1 0.93 FPR 0.02",
        "- Validator ≈ P0.88 R0.93 F1 0.91 FPR 0.02",
    ),
    (
        "- Validator ≈ P0.85 R0.94 F1 0.89 FPR 0.22",
        "- Validator ≈ P0.87 R0.94 F1 0.91 FPR 0.19",
    ),
    (
        "Field: N=330, 13.9% regressions, validator ~P0.90 R0.96 FPR0.02.",
        "Field: N=330, 13.9% regressions, validator ~P0.88 R0.93 FPR0.02.",
    ),
    (
        "Human: n=63, validator F1~0.89.",
        "Human: n=63, validator F1~0.91.",
    ),
    (
        "the validator reaches approximately precision 0.90, recall 0.96, and FPR 0.02.",
        "the validator reaches approximately precision 0.88, recall 0.93, and FPR 0.02.",
    ),
    (
        "A human-labeled subset of 63 pairs yields validator F1 around 0.89.",
        "A human-labeled subset of 63 pairs yields validator F1 around 0.91.",
    ),
    (
        "- Precision 0.85\n",
        "- Precision 0.87\n",
    ),
    (
        "- F1 0.89\n",
        "- F1 0.91\n",
    ),
    (
        "- FPR 0.22\n",
        "- FPR 0.19\n",
    ),
]
changed = 0
for old, new in replacements:
    if old in text:
        text = text.replace(old, new)
        changed += 1
    else:
        print("MISS:", old[:60].replace("\n", "\\n"))
path.write_text(text, encoding="utf-8")
print("applied", changed, "/", len(replacements))
