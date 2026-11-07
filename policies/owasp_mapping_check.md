# R01–R15 ↔ OWASP CI/CD mapping check

Cross-check of `owasp_cicd_rules.yaml` v3.0.0 against `rule_owasp_map.md`.

| Rule | YAML `owasp` | Map table | Match |
|------|--------------|-----------|-------|
| R01 | CICD-SEC-2, CICD-SEC-5 | CICD-SEC-2, CICD-SEC-5 | yes |
| R02 | CICD-SEC-5 | CICD-SEC-5 | yes |
| R03 | CICD-SEC-4 | CICD-SEC-4 | yes |
| R04 | CICD-SEC-4 | CICD-SEC-4 | yes |
| R05 | CICD-SEC-3 | CICD-SEC-3 | yes |
| R06 | CICD-SEC-8 | CICD-SEC-8 | yes |
| R07 | CICD-SEC-6 | CICD-SEC-6 | yes |
| R08 | CICD-SEC-1 | CICD-SEC-1 | yes |
| R09 | CICD-SEC-4, CICD-SEC-7 | CICD-SEC-4, CICD-SEC-7 | yes |
| R10 | CICD-SEC-4 | CICD-SEC-4 | yes |
| R11 | CICD-SEC-7 | CICD-SEC-7 | yes |
| R12 | CICD-SEC-2, CICD-SEC-5 | CICD-SEC-2, CICD-SEC-5 | yes |
| R13 | CICD-SEC-3, CICD-SEC-8 | CICD-SEC-3, CICD-SEC-8 | yes |
| R14 | CICD-SEC-4 | CICD-SEC-4 | yes |
| R15 | CICD-SEC-4 | CICD-SEC-4 | yes |

Policy is the source of truth; the map table is the human-readable twin. Re-run this checklist after any YAML OWASP list edit.
