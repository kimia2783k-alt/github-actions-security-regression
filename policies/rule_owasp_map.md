# Rule → OWASP CI/CD Top 10 Mapping

Policy version: **3.0.0**

| Rule | Name | OWASP IDs | Worse condition (summary) | Notes |
|------|------|-----------|---------------------------|-------|
| R01 | permissions_escalated_to_write_all | CICD-SEC-2, CICD-SEC-5 | `write-all` newly set, or permissions score jumps ≥30 toward ≥80 | IAM / PBAC weakening |
| R02 | permissions_restriction_removed | CICD-SEC-5 | Explicit least-privilege map / `read-all` removed | Loss of least privilege |
| R03 | pull_request_target_introduced | CICD-SEC-4 | Trigger newly added | Poisoned Pipeline Execution |
| R04 | privileged_pr_checkout | CICD-SEC-4 | Privileged checkout of PR head newly true | Classic pwn-request pattern |
| R05 | action_unpinned_from_sha | CICD-SEC-3 | Existing action key lost effective SHA pin (`@ref` is 40-hex only; comment SHA is not a pin) | Dependency chain abuse |
| R06 | new_unpinned_third_party_action | CICD-SEC-8 | New `(owner,name,ref)` unpinned, non-trusted | Ungoverned 3rd party |
| R07 | secret_exposure_pattern | CICD-SEC-6 | Secret-echo / toJSON(secrets) / env\|grep match count increases | Credential hygiene |
| R08 | security_job_or_step_removed | CICD-SEC-1 | Security control keys disappear | Flow control / gates removed |
| R09 | workflow_run_introduced | CICD-SEC-4, CICD-SEC-7 | `workflow_run` newly added | Privileged follow-on workflows |
| R10 | script_injection_risk_added | CICD-SEC-4 | Injection-pattern match count increases (event/head_ref/inputs) | Expression injection |
| R11 | self_hosted_runner_added | CICD-SEC-7 | `self-hosted` newly introduced | Insecure system configuration |
| R12 | dangerous_permission_scope_escalated | CICD-SEC-2, CICD-SEC-5 | New dangerous write scopes (contents, id-token, …); defers to R01 on new write-all | Fine-grained token abuse |
| R13 | remote_shell_pipe_added | CICD-SEC-3, CICD-SEC-8 | curl\|bash / wget\|sh / IEX newly added | Remote code execution in CI |
| R14 | dangerous_interactive_trigger_introduced | CICD-SEC-4 | `issue_comment` / `discussion_comment` / review-comment newly added | Interactive PPE vectors |
| R15 | github_env_injection_risk_added | CICD-SEC-4 | Untrusted context → GITHUB_ENV/PATH newly added | Environment file injection |
| R99 | other (manual) | — | Annotator-defined residual | Not automated |

Full predicates: [`rule_formal_spec.md`](rule_formal_spec.md). Policy: [`owasp_cicd_rules.yaml`](owasp_cicd_rules.yaml) v3.0.0.

Reference: [OWASP Top 10 CI/CD Security Risks](https://owasp.org/www-project-top-10-ci-cd-security-risks/)
