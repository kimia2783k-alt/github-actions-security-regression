# GitHub Actions Security Regression

Before/after policy checks for security regressions in GitHub Actions workflows (OWASP-mapped rules R01–R15).

**Public release:** [`pin-semantics-v0.5`](https://github.com/kimia2783k-alt/github-actions-security-regression/releases/tag/pin-semantics-v0.5)  
**Repo:** https://github.com/kimia2783k-alt/github-actions-security-regression

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = "src"
```

## Reproduce

```powershell
python -m pytest tests -q
python -m evaluate.run_eval --labels annotations/labels_sample.csv --out paper/manuscript/tables/controlled
python -m evaluate.run_eval --labels annotations/labels_aidev.csv --out paper/manuscript/tables/field
```

Details: [`replication/REPRODUCE.md`](replication/REPRODUCE.md)

## What’s in this repo

| Path | Content |
|------|---------|
| `src/` | Validator and evaluation code |
| `policies/` | Rule pack + OWASP map |
| `tests/` | Unit tests (incl. pin semantics) |
| `data/sample/` | Controlled YAML fixtures |
| `annotations/` | Field labels + 330-pair manifest |
| `paper/manuscript/tables/` | Frozen metrics |
| `replication/` | Reproduce / sampling / env freeze |

Manuscript Word files and long draft notes are **not** published here.
