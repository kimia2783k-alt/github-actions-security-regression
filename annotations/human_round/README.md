# Human annotation pack (single-annotator evaluation)

This delivery uses **one** human annotator only. Inter-rater agreement (Cohen’s κ) is not estimated.

1. Read `ANNOTATION_GUIDE_FA.md`.
2. Fill `annotator_A.csv` (`has_regression` = 0 or 1) from before/after YAML only.
3. Build gold from filled A rows → `gold_human_adjudicated.csv` (tag `single_annotator_A`).
4. Run `python scripts/eval_human_gold.py`.

Do **not** open `predicate_gold_key.csv` while labeling.

`annotator_B.csv` is unused historical scaffolding and is not part of the reported study design.
