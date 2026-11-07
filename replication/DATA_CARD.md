# Data Card

## Synthetic benchmark (`data/sample/`)

- **Description:** Hand-crafted GitHub Actions YAML before/after pairs for unit tests and controlled evaluation (R01–R15 fixtures + negatives).
- **PII:** None.
- **Secrets:** Only fictional `secrets.*` references inside YAML expressions; no real credentials.
- **License:** Same as repository (MIT recommended).
- **Intended use:** Reproducible detector evaluation; teaching examples.

## AIDev-derived field data (`data/processed/` when generated)

- **Upstream:** Li et al., AIDev (Hugging Face / Zenodo). Cite AIDev in any publication.
- **Contents:** Indexes of PRs touching `.github/workflows/*` and fetched public YAML pairs (pilot N=330).
- **Filtering:** Public repositories only.
- **Redaction policy:** If a real secret-looking string appears in a workflow, replace with `***REDACTED***` before sharing.
- **Limitations:** Agent labels follow AIDev mining heuristics; may include false agent attributions.
- **Redistribution:** Bulk raw AIDev dumps are not redistributed; share redacted indexes/pairs per upstream license.

## Labels (`annotations/`)

- `labels_sample.csv` — controlled gold (fixture-aligned).
- `labels_aidev.csv` — field gold from policy-v3 predicate audit (`scripts/field_gold_audit.py`); independent of live validator predictions but same predicate family.
- `human_round/` — stratified human annotation pack; **this delivery uses a single annotator** (annotator B out of scope; no Cohen’s κ). Annotators must not see validator predictions.

## Generated tables

- `paper/manuscript/tables/controlled/eval_summary.json`
- `paper/manuscript/tables/field/eval_summary.json`
- `paper/manuscript/tables/field/gold_v_delta.md`
