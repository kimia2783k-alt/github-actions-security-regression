# An Empirical Study of Security Regressions in AI-Agent-Modified GitHub Actions Workflows and Evaluation of a Policy-Based Validation Mechanism

**Authors:** [To be filled], [Supervisor name — To be filled]  
**Affiliation:** [University / Department — To be filled], Iran  
**Corresponding author:** [email — To be filled]  
**Manuscript type:** Full-Text Paper  
**Target venue:** Journal of Artificial Intelligence, Applications and Innovations (JAIAI)  
**Status:** Delivery manuscript v0.5 — pin-semantics freeze (comment-only SHA ≠ pin); controlled + field N=330 + single-annotator human n=63  
**Date:** 5 November 2026

---

## Abstract

AI coding agents increasingly edit continuous integration and continuous delivery (CI/CD) files, including GitHub Actions workflows. Build success does not guarantee that security controls remain intact. This paper studies *security regressions*: before-to-after workflow changes that weaken security posture. We propose a taxonomy of fifteen automatically checkable regression classes (R01–R15) mapped to the OWASP Top 10 CI/CD Security Risks, and a policy-based validator that diffs security signals extracted from YAML pairs. On a controlled fifteen-pair suite, the validator achieved precision, recall, and F1 of 1.00 (implementation check; not population generalization). An after-only zizmor baseline reached F1 0.80 with false-positive rate (FPR) 1.00 on the same regression labels. A merged AIDev/GitHub field pilot (N=330) yields a 13.9% audited regression rate (46/330) under policy-v3 predicates; the validator reaches precision ≈0.88, recall ≈0.93, and FPR ≈0.02, while a zizmor before/after finding-set diff lowers FPR from ≈0.91 to ≈0.18. Under a single-annotator evaluation, one annotator labeled 63 of 80 prepared pairs (36 positives); against that human gold the validator reaches precision ≈0.87, recall ≈0.94, and F1 ≈0.91. Results support diff-aware policy checks in merge gates for agent-touched workflows, alongside—not instead of—after-only static scanning.

**Keywords:** AI coding agents; GitHub Actions; CI/CD security; security regression; policy-based validation; DevSecOps; OWASP CI/CD; empirical software engineering

---

## 1. Introduction

Coding agents such as GitHub Copilot, OpenAI Codex, Cursor, Devin, Claude Code, and Google Jules now open pull requests (PRs) and modify project configuration. Datasets such as AIDev document agent-authored PRs at scale [1]. GitHub Actions workflows under `.github/workflows/` govern secrets, third-party actions, privileged triggers, and security gates. A change that keeps CI green can still escalate permissions, introduce `pull_request_target`, unpin actions from commit SHAs, expose secrets, or remove CodeQL. We call such worsenings *security regressions*.

Prior work measures how often agents touch CI/CD YAML and whether builds succeed [2], or studies reliability of workflow *runs* for agent PRs [3]. Static tools such as zizmor inspect a single revision [4]. Industry reports document prompt-injection risks when agents *execute inside* Actions [5], [6]. Less studied is whether *edits to workflow files* introduce security regressions relative to the prior revision, and whether a *diff-aware* policy detector outperforms after-only scanning for that task.

**Research questions.**

- **RQ1:** What types of security regressions appear in agent-related workflow diffs, and how are they distributed?
- **RQ2:** Do regression rates differ between agent-labeled and human-labeled changes under a matched setting?
- **RQ3:** Can a policy-based before/after validator detect regressions competitively versus an after-oriented static baseline?

**Contributions.** (1) An OWASP-mapped regression taxonomy (R01–R15). (2) An open policy-based before/after validator. (3) Controlled evaluation on fifteen labeled pairs. (4) A field pilot on N=330 AIDev/GitHub pairs plus a single-annotator human subset (n=63).

---

## 2. Background

GitHub Actions YAML defines triggers (`on`), permissions, jobs, steps, and `uses:` action references. Security-relevant signals include token scopes, privileged events, pin strength (tag vs commit SHA), secret usage in `run:` scripts, and presence of security jobs. OWASP’s CI/CD Top 10 and GitHub hardening guides motivate concrete checks [7], [8], [9], [10]. A *regression* is defined relative to a before/after pair: the after file is less safe along monitored dimensions, even if residual issues already existed before.

---

## 3. Related Work

MSR challenge papers study agent interaction with CI/CD configurations and success rates [2], [17]. Complementary MSR work examines AI bot footprints in workflow runs [3]. Static linters and scanners (actionlint, zizmor, OpenSSF Scorecard) target residual risk in a file or repository [4], [14], [18]. Reports on agent-in-CI prompt injection address runtime abuse [5], [6]. Adjacent JAIAI work discusses AI-assisted cyber-defense and anomaly detection themes [11], [12]. Practitioner hardening notes and token guidance complement the OWASP mapping [13], [20]. Supply-chain Action compromises motivate pinning-oriented rules [19]. Dataset deposits and related harnesses are listed for completeness [15], [16], [22]. Our focus is *authoring-time* before/after security regressions in workflow diffs and a policy gate specialized to that construct, not a replacement for snapshot scanning. Venue submission guidance is summarized separately for authors [21].

---

## 4. Methodology

### 4.1 Regression taxonomy (R01–R15)

We monitor fifteen automated classes. Rules are versioned in `policies/owasp_cicd_rules.yaml` (v3.0.0) with formal predicates; the OWASP Top 10 CI/CD mapping below is copied from `policies/rule_owasp_map.md` [7].

**Table A. R01–R15 → OWASP CI/CD mapping (policy v3.0.0).**

| Rule | Name | OWASP IDs |
|------|------|-----------|
| R01 | permissions_escalated_to_write_all | CICD-SEC-2, CICD-SEC-5 |
| R02 | permissions_restriction_removed | CICD-SEC-5 |
| R03 | pull_request_target_introduced | CICD-SEC-4 |
| R04 | privileged_pr_checkout | CICD-SEC-4 |
| R05 | action_unpinned_from_sha | CICD-SEC-3 |
| R06 | new_unpinned_third_party_action | CICD-SEC-8 |
| R07 | secret_exposure_pattern | CICD-SEC-6 |
| R08 | security_job_or_step_removed | CICD-SEC-1 |
| R09 | workflow_run_introduced | CICD-SEC-4, CICD-SEC-7 |
| R10 | script_injection_risk_added | CICD-SEC-4 |
| R11 | self_hosted_runner_added | CICD-SEC-7 |
| R12 | dangerous_permission_scope_escalated | CICD-SEC-2, CICD-SEC-5 |
| R13 | remote_shell_pipe_added | CICD-SEC-3, CICD-SEC-8 |
| R14 | dangerous_interactive_trigger_introduced | CICD-SEC-4 |
| R15 | github_env_injection_risk_added | CICD-SEC-4 |

R99 is reserved for manual residuals. For R05/R06, an effective pin requires a 40-hex `@ref` commit SHA; a YAML `# <sha>` comment does not change the GitHub-resolved Action reference and is not treated as a pin.

### 4.2 Policy validator

The validator parses before and after YAML, extracts security signals, diffs them, and emits rule-linked findings. A pair is predicted positive if any non-parse finding fires. Mean latency on the field set is on the order of tens of milliseconds per pair.

### 4.3 Field gold predicates

Field gold for N=330 is a reproducible *predicate audit* aligned with policy v3, independent of live validator predictions but still specification-tied. Expanding interim predicates with R12–R15 raised positives on the same paths from ≈39–40 to **46** (13.9%).

### 4.4 Baselines

We evaluate zizmor v1.31.1 under two regression operationalizations: (i) after-only (any finding on the after file ⇒ positive); (ii) before/after finding-set difference (new findings after relative to before ⇒ positive).

### 4.5 Human annotation subset (single annotator)

Human labels use a **single-annotator evaluation**. An 80-pair stratified pack (all 46 v3 positives plus 34 negatives) was prepared under `annotations/human_round/`. One annotator labeled **63** pairs from before/after YAML only (36 positive, 27 negative); **17** pairs lacked available YAML and were excluded. Inter-rater agreement (e.g., Cohen’s κ) is not estimated because only one annotator produced labels. Human gold is tagged `single_annotator_A`.

---

## 5. Experimental Setup

**Controlled benchmark.** Fifteen synthetic before/after pairs under `data/sample/` (ten positives spanning major rules; five negatives including hardening and non-worsening edits). Labels in `annotations/labels_sample.csv`.

**Field pilot.** Merged AIDev/GitHub pairs with workflow materialization in October 2026: N=330 (OpenAI_Codex 200, Claude_Code 20, Copilot 20, Cursor 6, Devin 4, human 80). Codex rows from an AIDev stream with `(pr_id, filename)` deduplication; other agents via GitHub Files API; human controls repo-matched to the agent index with bot exclusion and `(repo, path)` deduplication. Full index: `annotations/field_pairs_manifest_330.csv` (SHA-256 in companion `.meta.json`). Protocol: `replication/SAMPLING_PROTOCOL.md`. Evaluation via `python -m evaluate.run_eval`.

**Metrics.** Precision, recall, F1, FPR, FNR; stratum rates. Pooled agent vs human rates use Pearson’s χ² on the 2×2 contingency table via `scipy.stats.chi2_contingency` with the library default **Yates continuity correction** (`correction=True`); if any cell were &lt;5 the code path switches to Fisher’s exact test (`fisher_exact`).

**Reproducibility environment (freeze pin-semantics-v0.5).** Windows 11 (10.0.26200); Python 3.14.7; `ruamel.yaml` 0.19.1; `scipy` 1.18.1; `pytest` 9.1.1; zizmor 1.31.1; AMD64 host, 24 logical CPUs. Details: `replication/ENV_FREEZE.md`.

---

## 6. Results

### 6.1 Controlled detector performance (RQ3)

**Table 1. Controlled benchmark (N=15).**

| Method | Precision | Recall | F1 | FPR |
|--------|----------:|-------:|---:|----:|
| Policy Validator | 1.00 | 1.00 | 1.00 | 0.00 |
| zizmor after-only | 0.67 | 1.00 | 0.80 | 1.00 |

Perfect validator scores demonstrate implementation correctness on a co-designed suite, not universal robustness. After-only zizmor flags all pairs (FPR=1.00) when used as a regression predictor.

### 6.2 Controlled RQ2 (illustrative only)

On the synthetic suite, agent-tagged positives were all regressions (9/9) versus 1/6 among human-tagged pairs (Fisher p≈0.002). Agent tags on fixtures are synthetic for coverage; this table is **not** evidence about production agents.

### 6.3 Field pilot (RQ1–RQ3)

**Table 2. Field detector performance (N=330; policy-v3 gold).**

| Method | Precision | Recall | F1 | FPR | FNR |
|--------|----------:|-------:|---:|----:|----:|
| Policy Validator | 0.88 | 0.93 | 0.91 | 0.02 | 0.07 |
| zizmor after-only | 0.15 | 0.96 | 0.25 | 0.91 | 0.04 |
| zizmor before/after-diff | 0.40 | 0.74 | 0.52 | 0.18 | 0.26 |

**Table 3. Field regression rates by stratum (v3 gold).**

| Stratum | N | Rate |
|---------|--:|-----:|
| OpenAI_Codex | 200 | 0.180 |
| Claude_Code | 20 | 0.050 |
| Copilot | 20 | 0.000 |
| Cursor | 6 | 0.500 |
| Devin | 4 | 0.000 |
| All AI (pooled) | 250 | 0.160 |
| Human controls | 80 | 0.075 |

Audited regression rate: **46/330 (13.9%)**. Qualitatively, automated hits are dominated by unpinning/untrusted-action patterns and dangerous permission scopes; we do **not** invent a full R01–R15 frequency table in prose—per-rule detector hit counts must be read from `paper/manuscript/tables/field/eval_summary.json` (`rule_counts`). Field zizmor baselines in that same freeze report `zizmor_cli_available: true` (real CLI, not proxy); re-check this flag after any regeneration before submission. Pooled agent vs human rates: 0.160 vs 0.075 (Pearson χ² with Yates continuity correction: χ²≈2.976, df=1, p≈0.0845; not significant at α=0.05). Without continuity correction the same table yields p≈0.056; we report the default corrected test used by the evaluation code. Field validator scores are informative for a specified gate but partly expected because gold and detector share the v3 predicate family.

### 6.4 Single-annotator human subset

**Table 4. Policy validator vs single-annotator human gold (n=63).**

| Method | Precision | Recall | F1 | FPR | FNR | N |
|--------|----------:|-------:|---:|----:|----:|--:|
| Policy Validator | 0.87 | 0.94 | 0.91 | 0.19 | 0.06 | 63 |

Agreement with the human reader is strong on recall and solid on precision, with higher FPR than on predicate-aligned field gold—consistent with a human applying broader judgment than formal predicates.

### 6.5 Qualitative cases (brief)

Permissions escalation to `write-all`, `pull_request_target` with untrusted checkout, and deletion of a CodeQL job are flagged as regressions; adding CodeQL or SHA-pinning trusted actions are treated as non-regressions.

---

## 7. Discussion

Security regression is a property of a *change*. After-only scanners answer residual risk in the landing file; regression policies answer whether the PR made security worse. Organizations should run both. Latency of the policy check is compatible with CI merge gates on workflow paths. The field agent–human gap is directionally elevated but not statistically conclusive. The human subset supports that the validator tracks human-perceived worsenings, while FPR ≈0.19 shows remaining disagreements between formal predicates and human judgment. Effective Action pinning is defined strictly as a 40-hex `@ref` commit SHA; a trailing `# <sha>` comment beside a floating tag is not treated as a pin.

---

## 8. Threats to Validity

**Construct.** Organization policies may diverge from default rules; declarative packs make disagreements tunable. **Internal.** Controlled F1=1.00 risks overfitting; field scores are predicate-aligned. **External.** N=330 and small Cursor/Devin cells limit generality. **Label.** Human evidence is a single-annotator subset (n=63) without an independent second rater or Cohen’s κ; 17 pack rows lacked YAML. **Baseline.** After-only zizmor as a regression label is a strict operationalization; finding-set diff is fairer but still noisier than the policy gate.

---

## 9. Conclusion

We presented an OWASP-mapped taxonomy (R01–R15), a policy-based before/after validator, controlled and field evidence (N=330; 13.9% v3 regressions), and a single-annotator human check (n=63; validator F1≈0.91). Diff-aware policy gates are a practical complement to after-only scanning for agent-modified GitHub Actions. Future work: enlarge sparse agent cells and human matching, and package the validator as a GitHub Action.

---

## Acknowledgments

The authors thank the maintainers of the AIDev dataset and the open-source CI security tooling community.

**Ethics:** The study uses only publicly available GitHub and AIDev artifacts. No interaction with private systems or human subjects beyond voluntary expert annotation of public YAML was conducted; secrets in workflows are not redistributed.

**Funding:** [To be filled — none if applicable].

**Conflict of interest:** The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

**Author contributions (CRediT):** [To be filled — e.g., Conceptualization; Methodology; Software; Validation; Formal analysis; Investigation; Data curation; Writing — original draft; Writing — review & editing; Supervision].

**AI writing disclosure (JAIAI):** In order to correct and improve the academic writing of our paper, we have used the language model Cursor Agent (Composer).

**Data and code availability:** Artifacts include `src/`, `policies/owasp_cicd_rules.yaml` (v3), OWASP map (`policies/rule_owasp_map.md`), `data/sample/`, field gold `annotations/labels_aidev.csv`, full pair index `annotations/field_pairs_manifest_330.csv`, sampling protocol `replication/SAMPLING_PROTOCOL.md`, host HW/SW freeze `replication/ENV_FREEZE.md`, human pack `annotations/human_round/` (single-annotator labels), evaluation tables under `paper/manuscript/tables/` (including `confusion_matrices.md`), `replication/REPRODUCE.md`, and publish steps in `replication/PUBLISH.md`. Result version: **pin-semantics-v0.5**. Public repository URL: https://github.com/kimia2783k-alt/github-actions-security-regression. Release/commit: `06d70c809d08203b4a0b8478844219d39c0a5306`.

---

## Appendix A. Author Completion Checklist (Remove Before Submission)

This checklist is an editorial aid and is not part of the scientific article. Complete each item, then remove this appendix before submitting the manuscript.

- [ ] Complete author names, institutional affiliations, corresponding-author details, and ORCID identifiers.
- [x] Insert the exact public URL and release/commit hash of the research implementation (https://github.com/kimia2783k-alt/github-actions-security-regression / `06d70c809d08203b4a0b8478844219d39c0a5306`).
- [x] Confirm the field-sampling dates, retrieval process, repository matching, deduplication, and workflow-pair manifest (`replication/SAMPLING_PROTOCOL.md`; `annotations/field_pairs_manifest_330.csv`).
- [x] Copy the exact R01–R15 OWASP mapping from `policies/rule_owasp_map.md` (Table A in §4.1).
- [x] Audit whether comment-only SHA values are treated as actual pins; a YAML comment does not change the GitHub-resolved Action reference (`docs/pin_semantics_audit.md`; `effectively_pinned` = `@ref` 40-hex only).
- [x] If pinning logic is corrected, rerun relevant tests, policy-v3 gold generation, and affected R05/R06 metrics; clearly version the new results (**pin-semantics-v0.5**; field validator ≈P0.88/R0.93/F1 0.91; human F1≈0.91).
- [x] Confirm the exact statistical test and continuity-correction setting behind the reported p-value (Pearson χ² via `scipy.stats.chi2_contingency`, **Yates correction on**; p≈0.0845).
- [x] Add hardware, operating system, Python, parser, and zizmor versions for reproducibility (`replication/ENV_FREEZE.md`).
- [ ] Complete ethics, funding, conflict-of-interest, acknowledgments, and author-contribution statements. *(Ethics/COI/acks drafted; funding + CRediT still author-filled.)*
- [ ] Check the venue’s reference style, word limit, figure requirements, and data/software availability policies (`paper/jaiai/checklist.md`; JAIAI submissions page).
- [ ] Verify all references and in-text citations against the final publication records (`paper/literature/reference_audit.md`).
- [x] Regenerate all tables from committed evaluation outputs and confirm that the manuscript numbers match (`tables/field/eval_summary.json`, `eval_human_gold.json`, `confusion_matrices.md`).

---

## References

[1] H. Li, H. Zhang, and A. E. Hassan, “AIDev: Studying AI Coding Agents on GitHub,” arXiv:2507.15003, 2025. Dataset: https://huggingface.co/datasets/hao-li/AIDev

[2] T. A. Ghaleb, “When AI Agents Touch CI/CD Configurations: Frequency and Success,” in *Proc. 23rd Int. Conf. on Mining Software Repositories (MSR ’26)*, Rio de Janeiro, Brazil, Apr. 13–14, 2026. arXiv:2601.17413. https://arxiv.org/abs/2601.17413

[3] S. M. A. Shah, S. Habib, M. A. Hussain, M. A. Ghafoor, and A. A. Bangash, “Reliability of AI Bots Footprints in GitHub Actions CI/CD Workflows,” in *Proc. 23rd Int. Conf. on Mining Software Repositories (MSR ’26)*, Rio de Janeiro, Brazil, Apr. 13–14, 2026, doi: 10.1145/3793302.3793569. Also: arXiv:2604.18334. https://doi.org/10.1145/3793302.3793569

[4] zizmor project, “zizmor documentation,” https://docs.zizmor.sh/ (accessed Oct. 21, 2026).

[5] Microsoft Threat Intelligence, “Securing CI/CD in an agentic world: Claude Code GitHub Action case,” Microsoft Security Blog, Jun. 5, 2026. https://www.microsoft.com/en-us/security/blog/2026/06/05/securing-ci-cd-in-an-agentic-world-claude-code-github-action-case/

[6] Cloud Security Alliance AI Safety Initiative, “Prompt Injection in AI-Powered GitHub Actions,” CSA Research Note, May 3, 2026. https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-github-actions-security-20260503-csa-st/

[7] OWASP Foundation, “Top 10 CI/CD Security Risks,” https://owasp.org/www-project-top-10-ci-cd-security-risks/ (accessed 2026).

[8] GitHub, “Security hardening for GitHub Actions,” GitHub Docs, https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions (accessed 2026).

[9] OWASP, “GitHub Actions Security Cheat Sheet,” https://cheatsheetseries.owasp.org/cheatsheets/GitHub_Actions_Security_Cheat_Sheet.html (accessed 2026).

[10] GitHub, “Securely using pull_request_target,” GitHub Docs, https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target (accessed 2026).

[11] M. Tamtaji, A. Ekrami Kivaj, and S. G. H. Tabatabaei, “The Role of Artificial Intelligence in Predicting Cyber Attack Patterns and Offering Solutions to Mitigate Attacks in ISMS Compliant Environments,” *Journal of Artificial Intelligence, Applications and Innovations*, vol. 1, no. 4, pp. 14–29, 2024.

[12] M. Samadzadeh, E. Farahani, and S. J. Seyyedzadeh, “Reviewing the Landscape of Security Anomaly Detection through Deep Learning Techniques,” *Journal of Artificial Intelligence, Applications and Innovations*, vol. 1, no. 3, 2024, doi: 10.61838/jaiai.1.3.5. https://www.journalaiai.com/index.php/aiai/article/view/34

[13] GitHub Security Lab, “Keeping your GitHub Actions and workflows secure” (series), https://securitylab.github.com/ (accessed 2026).

[14] OpenSSF, “Scorecard,” https://github.com/ossf/scorecard (accessed 2026).

[15] OWASP, “Agent Security Regression Harness,” https://github.com/OWASP/Agent-Security-Regression-Harness (accessed 2026).

[16] H. Li, H. Zhang, and A. E. Hassan, AIDev dataset on Hugging Face (AIDev / AIDev-7.6M), 2025–2026. https://huggingface.co/datasets/hao-li/AIDev

[17] T. A. Ghaleb, “AIAgentsCI_CD-MSR2026 replication package,” https://github.com/Taher-Ghaleb/AIAgentsCI_CD-MSR2026 (accessed 2026).

[18] rhysd (R. Yamashita), “actionlint,” https://github.com/rhysd/actionlint (accessed 2026).

[19] CISA / industry reporting on compromised GitHub Actions supply-chain incidents, including `tj-actions/changed-files` (CVE-2025-30066) and related Action compromises; discussed in [6], 2025–2026.

[20] GitHub, “Automatic token authentication / Using the GITHUB_TOKEN in a workflow,” GitHub Docs, https://docs.github.com/en/actions/security-guides/automatic-token-authentication (accessed 2026).

[21] Journal of Artificial Intelligence, Applications and Innovations (JAIAI), Author Guidelines / Submissions, https://www.journalaiai.com/index.php/aiai/about/submissions (accessed 2026).

[22] H. Li, H. Zhang, and A. E. Hassan, AIDev dataset deposit on Zenodo, https://zenodo.org/records/16919051, 2025.

---

*End of delivery manuscript v0.5 (pin-semantics freeze).*
