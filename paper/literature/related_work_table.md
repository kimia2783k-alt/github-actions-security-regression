# Related Work Comparison Table

| Paper / Resource | Year | Data / Scope | Focus | Gap vs this study |
|------------------|------|--------------|-------|-------------------|
| Ghaleb et al., *When AI Agents Touch CI/CD Configurations* (MSR 2026) | 2026 | 8,031 agentic PRs / AIDev | Frequency of CI/CD YAML edits; merge & build success | No security regression taxonomy or detector evaluation |
| *Reliability of AI Bots Footprints in GitHub Actions* (MSR) | 2026 | 61,837 workflow runs | Reliability of runs triggered by agent PRs; failure taxonomy | Runtime reliability ≠ config security weakening |
| *Evaluating CI/CD Security Best Practices in the GitHub Actions Documentation* | 2026 | Docs corpus | Coverage of security guidance in official docs | Not about agent-authored diffs |
| zizmor static analyzer | 2024–2026 | Single workflow snapshot | Template injection, permissions, pinning, etc. | After-only scanning; not regression-aware before→after on agent PRs |
| Actionlint / OpenSSF Scorecard | ongoing | Repo/workflow lint | Correctness & some security signals | Not agent-vs-human empirical study |
| OWASP Top 10 CI/CD Security Risks | 2022+ | Risk framework | Risk categories (PPE, PBAC, secrets, …) | Framework, not empirical agent study |
| OWASP GitHub Actions Security Cheat Sheet | 2025–2026 | Guidance | Hardening advice incl. AI assistants *in* CI | Advises defenders; does not measure agent *edits* to workflows |
| Microsoft Security Blog: Claude Code GitHub Action case | 2026-06 | Incident analysis | Secrets exposure when agents process untrusted content *inside* Actions | Different threat: agent-as-runner vs agent-as-author of YAML |
| CSA note: Prompt Injection in AI-Powered GitHub Actions | 2026-05 | Industry research note | Prompt injection against agents embedded in workflows | Complements our threat model but different artifact (runtime agent vs YAML diff) |
| OWASP Agent Security Regression Harness | 2026 | Scenario harness | Regression tests for agent *behavior* (tools/prompts) | Not GitHub Actions YAML security diffs |
| SecureVibeBench (ACL-related) | 2025–2026 | Code security bench | Vulnerabilities in AI-generated application code | Application code, not CI/CD configs |
| Li et al., AIDev dataset | 2025–2026 | Millions of agent PRs | Enables mining of agent contributions | Dataset paper; no security regression analysis of Actions |
| Tamtaji et al., AI for cyber attack prediction (JAIAI) | 2024/2025 | Simulation / ISMS | Attack prediction with ML | Iranian venue-relevant but unrelated to Actions agents |
| JAIAI deep learning anomaly detection review | 2024 | Survey | Network/security anomaly DL | No CI/CD agent angle |
| Iranian LLM coding evaluation critique (prior scoping) | — | Programming benchmarks | Limits of functional tests for LLM coding | Not CI/CD security regressions |

## Gap statement (for Introduction)

Prior work shows that AI coding agents occasionally modify CI/CD YAML and that their workflow *runs* can fail for diverse reasons. Static tools can flag insecure workflow states. Industry reports warn about agents *executing inside* CI with secrets. **However, we lack a systematic measurement of whether agent pull requests introduce security regressions in GitHub Actions configurations relative to matched human changes, and whether a policy-based before/after validator can catch those regressions better than after-only static scanning.**
