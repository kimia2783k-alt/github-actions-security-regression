# Field-study / Phase B status

**Updated:** 2026-10-24 (policy v3; consistency pass)

## Merged field corpus

| Arm | N | How obtained |
|-----|--:|--------------|
| OpenAI_Codex | 200 | HF stream + GitHub fetch |
| Claude_Code | 20 | AIDev PR probe via GitHub Files API |
| Copilot | 20 | same |
| Cursor | 6 | same |
| Devin | 4 | same |
| Google_Jules | 0 | no workflow hits in probe |
| Human controls | 80 | non-bot commits on `.github/workflows` in Codex repos |
| **Total** | **330** | `annotations/labels_aidev.csv` |

## Headline metrics (`tables/field/eval_summary.json`, policy v3 gold)

| Metric | Value |
|--------|------:|
| Gold regression rate | 0.139 (46/330) |
| Policy P / R / F1 / FPR | 0.88 / 0.93 / 0.91 / 0.02 |
| zizmor after-only P / R / F1 / FPR | 0.15 / 0.96 / 0.25 / 0.91 |
| zizmor before/after-diff P / R / F1 / FPR | 0.40 / 0.74 / 0.52 / 0.18 |
| AI vs human rates | 0.160 vs 0.075 |
| χ² p | ≈0.085 |

### Superseded interim headline (do not cite as current)

Gold ≈0.118 (≈39/330); Policy ≈0.79/0.38/0.52/0.014; Fisher p≈0.009 — replaced by v3 table above.

## Scripts

- `scripts/stream_aidev_workflows.py`
- `scripts/sample_agents_via_github.py`
- `scripts/sample_human_controls.py`
- `scripts/merge_field_eval.py`
- `scripts/field_gold_audit.py`
- `scripts/gold_version_delta.py`

## Still open (future scale-up — not claimed done)

- Larger Cursor/Devin/Jules cells
- PR-level (not only repo-level) human matching toward ≥200 human pairs
- Second human annotator + κ — **out of scope for this delivery** (single-annotator human subset used instead)
