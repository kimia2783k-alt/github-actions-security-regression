# Study Protocol (Pre-registered Analysis Plan)

**Title:** An Empirical Study of Security Regressions in AI-Agent-Modified GitHub Actions Workflows and Evaluation of a Policy-Based Validation Mechanism

**Version:** 0.3.0  
**Date:** 2026-10-24

## 1. Objectives

Answer RQ1–RQ3 as defined in the project README and proposal.

## 2. Primary analyses (confirmatory)

1. **Regression prevalence (RQ1):** Proportion of pairs with ≥1 security regression label; distribution over taxonomy classes R01–R15 (R99 manual residual).
2. **AI vs Human (RQ2):** Chi-square or Fisher exact test on `has_regression` for agent vs matched human samples; odds ratio with 95% CI (bootstrap if sparse).
3. **Detector performance (RQ3):** Precision, Recall, F1, FPR of Policy Validator vs gold; same metrics for zizmor after-only and zizmor before/after-diff baselines.

## 3. Secondary / exploratory analyses

- Per-agent breakdown (Copilot, Codex, Cursor, Devin, Claude Code, Jules)
- Per-rule performance and ablation (permissions-only, pinning-only, full)
- Runtime cost per file
- Qualitative case studies (3–5 public PRs)
- Sensitivity to strict vs lenient regression definitions / gold-version deltas

## 4. Inclusion criteria

- Public PR modifying `.github/workflows/*.{yml,yaml}`
- Parseable YAML before and after (invalid YAML recovered via raw fallback when possible)
- Agent label available from AIDev, or human control from matched set

## 5. Exclusion criteria

- Whitespace-only diffs (when detectable)
- Binary or non-workflow YAML under other paths
- Private repositories

## 6. Sample size

### 6.1 Executed pilot (reported in manuscript §6.6)

- **N = 330** pairs: OpenAI_Codex 200, Claude_Code 20, Copilot 20, Cursor 6, Devin 4, human 80
- Gold under policy v3: **46/330 (13.9%)**
- This pilot is **done** and is the basis of reported field rates
- Full index: `annotations/field_pairs_manifest_330.csv`
- Detailed protocol: `replication/SAMPLING_PROTOCOL.md`
- Host environment freeze: `replication/ENV_FREEZE.md`

### 6.2 Future scale-up target (not claimed as done)

- ≥200 well-matched human pairs (prefer PR-level matching)
- Enlarge sparse agent cells (Cursor/Jules/Devin)
- Optional full-corpus extraction when storage permits
- If corpus remains smaller than targets, report full eligible set and mark RQ2 as exploratory

## 7. Labeling

- **Controlled:** fixture-curated gold
- **Field (pilot):** independent predicate audit (`scripts/field_gold_audit.py`) aligned with `rule_formal_spec.md` v3; does not copy live validator predictions
- Fields: `has_regression`, `rule_ids`, `severity`, `notes`, `annotator`
- Human check for this delivery: **single annotator** (second annotator out of scope; no Cohen’s κ)

## 8. Multiple testing

Confirmatory tests limited to section 2. All other tests labeled exploratory; no alpha adjustment claimed for exploratory family.

## 9. Ethics

Public data only; redact secrets; no interaction with production systems of third parties beyond reading public GitHub content.
