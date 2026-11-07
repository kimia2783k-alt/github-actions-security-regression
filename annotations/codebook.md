# Annotation Codebook — Security Regressions in GitHub Actions Diffs

## Unit of annotation

One **before/after pair** of the same workflow file in a pull request.

## Primary label

| Field | Values | Definition |
|-------|--------|------------|
| `has_regression` | 0/1 | 1 if after state is **security-worse** than before on ≥1 taxonomy rule |
| `rule_ids` | `R01\|R02\|...` | All applicable regression classes |
| `severity` | low/medium/high/critical | Max severity among applicable rules |
| `notes` | free text | Borderline rationale |
| `annotator` | id | Who labeled |

## Decision rule

Label a regression **only if the change worsens security**. Pre-existing issues that remain unchanged are **not** regressions for this study (they may still be static findings for zizmor).

## Class definitions (summary)

See `policies/rule_owasp_map.md` for OWASP mapping.

- **R01** Permissions escalated to `write-all` or large broaden
- **R02** Explicit least-privilege `permissions:` removed
- **R03** `pull_request_target` newly added
- **R04** Checkout of PR head under privileged trigger
- **R05** SHA pin replaced by floating tag
- **R06** New untrusted unpinned third-party action
- **R07** Secret echoed/printed in scripts
- **R08** Security job/step removed
- **R09** `workflow_run` newly added
- **R10** Untrusted `github.event.*` interpolated into `run:`
- **R11** `self-hosted` runner newly introduced
- **R12** Other (explain in notes)

## Examples

Bundled under `data/sample/`:

| Sample | Expected |
|--------|----------|
| `r01_permissions_write_all` | R01 |
| `r03_pr_target` | R03, R04 |
| `r05_unpinned_action` | R05 |
| `r08_removed_security_job` | R08 |
| `safe_change` | none |
