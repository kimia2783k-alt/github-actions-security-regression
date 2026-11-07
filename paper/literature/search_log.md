# Systematic Search Log

**Date started:** 2026-10-21  
**Reviewer:** research agent (Cursor)  
**Scope:** Security regressions in GitHub Actions / CI/CD configs modified by AI coding agents; policy-based validation; related Iranian journal literature.

## Databases / sources

| Source | Used | Notes |
|--------|------|-------|
| Google Scholar / Web search | Yes | Primary discovery |
| arXiv | Yes | MSR 2026 related |
| ACM DL | Yes (via public pages) | Reliability of AI Bots Footprints |
| ACL Anthology | Partial | SecureVibeBench mentioned in prior scoping |
| OWASP / GitHub docs | Yes | Standards & tooling |
| JAIAI journal site | Yes | Iranian target venue |
| SID / Civilica / Magiran | Limited public web | No exact match found in open results |

## Queries (English)

1. `"GitHub Actions" (security OR vulnerability) (agent OR Copilot OR "coding agent")`
2. `"CI/CD" "security regression" (LLM OR "AI agent")`
3. `"poisoned pipeline" OR pull_request_target (LLM OR agent)`
4. `"policy-based" OR "policy as code" "GitHub Actions" security`
5. `AIDev "GitHub Actions" OR "CI/CD"`
6. `zizmor OR actionlint security evaluation`
7. `When AI Agents Touch CI/CD Configurations`
8. `Prompt Injection in AI-Powered GitHub Actions`

## Queries (Persian / Iranian venues)

1. هوش مصنوعی عامل کدنویس امنیت CI/CD
2. گیت‌هاب اکشن امنیت مدل زبانی
3. site:journalaiai.com cybersecurity OR agent
4. بازاندیشی معیارهای ارزیابی مدل‌های زبانی برنامه‌نویسی (prior scoping)

## Screening summary (2026-10-21)

- Records screened (title/abstract level): 28
- Included for related work table: 18
- Excluded: general LLM hallucination without CI; Android malware JAIAI papers; agent prompt-regression harnesses that do not analyze Actions YAML diffs

## Gap decision

**No peer-reviewed study found that jointly (a) measures security regressions in AI-agent diffs to GitHub Actions YAML, (b) compares to matched human changes, and (c) evaluates a before/after policy validator against a static Actions scanner.**

Closest neighbors focus on CI change frequency/build success (MSR 2026), workflow run reliability, static scanners (zizmor), or AI agents *running inside* Actions (prompt injection / secret exposure)—not agent *edits to* workflow files.

**Title retained** as proposed; novelty claim kept as “likely gap / complementary study,” not “first in the world.”
