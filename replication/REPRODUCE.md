# Reproduce evaluation tables

Working directory: repository root (`مقاله روش پژوهش`).

## 0. Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = "src"
```

Optional (field zizmor baselines): install `zizmor` on PATH or in the venv Scripts folder.

## 1. Unit tests

```powershell
python -m pytest tests -q
```

Expect 23 collected/passing tests at pin-semantics freeze (includes `test_pin_semantics.py`).

## 2. Controlled benchmark (N=15)

```powershell
python -m evaluate.run_eval --labels annotations/labels_sample.csv --out paper/manuscript/tables/controlled
```

Source of truth: `paper/manuscript/tables/controlled/eval_summary.json`.

## 3. Field pilot (N=330)

```powershell
python -m evaluate.run_eval --labels annotations/labels_aidev.csv --out paper/manuscript/tables/field
```

Source of truth: `paper/manuscript/tables/field/eval_summary.json`  
(policy v3 gold; Validator ≈ P0.88 R0.93 F1 0.91 FPR0.02; zizmor-diff FPR≈0.18).  
Confusion matrices: `paper/manuscript/tables/field/confusion_matrices.md`.

## 4. Gold definition delta (same N=330)

```powershell
python scripts/gold_version_delta.py
```

Outputs: `paper/manuscript/tables/field/gold_v_delta.md` and `.json`.

## 5. Human annotation pack (this delivery: single annotator)

```powershell
python scripts/sample_human_annotation_set.py
# Fill annotations/human_round/annotator_A.csv only (annotator B is out of scope for this delivery)
python scripts/eval_human_gold.py
```

See `annotations/human_round/README.md` and `ANNOTATION_GUIDE_FA.md`. Cohen’s κ is not part of this delivery.

## 6. Regenerate Word manuscripts

```powershell
python scripts/md_to_docx.py
python scripts/guide_fa_to_docx.py
```

## Artifact checklist

| Artifact | Path |
|----------|------|
| Policy v3 | `policies/owasp_cicd_rules.yaml` |
| Formal rules | `policies/rule_formal_spec.md` |
| Field labels | `annotations/labels_aidev.csv` |
| Full 330 manifest | `annotations/field_pairs_manifest_330.csv` (+ `.meta.json`) |
| Sampling protocol | `replication/SAMPLING_PROTOCOL.md` |
| HW/SW freeze | `replication/ENV_FREEZE.md` / `ENV_FREEZE.json` |
| Pin audit | `docs/pin_semantics_audit.md` |
| OWASP map check | `policies/owasp_mapping_check.md` |
| Field metrics | `paper/manuscript/tables/field/eval_summary.json` |
| Gold delta | `paper/manuscript/tables/field/gold_v_delta.md` |
| English MS | `paper/manuscript/main.md` |
| Publish to GitHub | `replication/PUBLISH.md` + `replication/GITHUB_STEPS_FA.md` |
| Public URL | https://github.com/kimia2783k-alt/github-actions-security-regression (tag `pin-semantics-v0.5`) |
