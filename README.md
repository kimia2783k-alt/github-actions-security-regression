# Security Regressions in AI-Agent-Modified GitHub Actions

Policy-based before/after validator and empirical pilot for detecting **security regressions** in GitHub Actions workflow diffs (including AI-agent-related edits).

**Result freeze:** `pin-semantics-v0.5`  
**Policy:** `policies/owasp_cicd_rules.yaml` v3.0.0  
**Effective Action pin:** `@ref` must be a 40-hex commit SHA (YAML `# <sha>` comments are **not** pins).

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = "src"

# Unit tests (no network)
python -m pytest tests -q

# Controlled evaluation (N=15)
python -m evaluate.run_eval --labels annotations/labels_sample.csv --out paper/manuscript/tables/controlled

# Field evaluation (N=330; needs materialized pairs under data/processed if regenerating)
python -m evaluate.run_eval --labels annotations/labels_aidev.csv --out paper/manuscript/tables/field
```

Optional baseline scanner: install `zizmor` into the same venv (`pip install zizmor`).

Secrets for optional GitHub/HF sampling: copy `.env.example` → `.env` (never commit `.env`).

## Layout

| Path | Purpose |
|------|---------|
| `src/` | Parser, policy validator, evaluation |
| `policies/` | OWASP-mapped rule pack + formal map |
| `tests/` | Pin semantics and rule tests |
| `data/sample/` | Controlled before/after fixtures |
| `annotations/` | Field labels, 330-pair manifest, human labels |
| `paper/manuscript/tables/` | Frozen metrics / confusion matrices |
| `replication/` | Reproduce, sampling protocol, publish guide, env freeze |

## Field freeze headline (N=330)

- Gold regressions: **46/330 (13.9%)**
- Policy validator: **P≈0.88 · R≈0.93 · F1≈0.91 · FPR≈0.02**
- Source of truth: `paper/manuscript/tables/field/eval_summary.json`

## Publish to GitHub

Follow **`replication/PUBLISH.md`** (exact steps). Do not upload `.env`.

## Ethics

Public GitHub / AIDev artifacts only. Do not commit tokens or real secrets.

## License

See `LICENSE`.
