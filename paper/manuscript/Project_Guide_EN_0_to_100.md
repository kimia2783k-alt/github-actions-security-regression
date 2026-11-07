# Complete Project Guide (0 to 100)
## Security Regressions in AI-Agent-Modified GitHub Actions Workflows

**Document type:** Full English project explanation (not the short journal manuscript)  
**Audience:** Student, supervisor, secretariat reviewers, and future maintainers  
**Purpose:** Explain the whole research project from first principles to final results, files, commands, and how to talk about the work  
**Companion short papers:** `main.md` (English manuscript), `main_fa.md` (Persian print article)

---

# Part I — What This Project Is About

## Chapter 1. The story in plain English

Imagine a software team that hosts its code on GitHub. Every time someone proposes a change, automated jobs build the project, run tests, and sometimes publish releases. That automation is called continuous integration and continuous delivery (CI/CD).

On GitHub, the instructions for those jobs live in workflow files. They usually sit under:

`.github/workflows/`

Those files are written in YAML. They specify:

- when a job should run (for example, on pull request or push);
- what machine it runs on;
- what permissions the temporary GitHub token receives;
- which reusable Actions are downloaded;
- whether security scanners such as CodeQL still run.

In recent years, AI coding agents (Copilot, Codex, Claude Code, Cursor, Devin, Jules, and similar systems) do more than autocomplete. They open pull requests and edit project files—including workflow YAML.

Here is the security problem this project studies:

A workflow change can keep tests green while making the pipeline less safe. Examples include granting `write-all` permissions, introducing a privileged trigger such as `pull_request_target`, unpinning a third-party Action from a commit SHA to a floating tag, echoing secrets into logs, or deleting a security job.

We call a before-to-after worsening of security posture a **security regression**.

**One sentence for your supervisor:**  
We study whether AI coding agents (and comparable workflow edits) introduce security regressions in GitHub Actions, and whether a policy-based before/after validator can detect those regressions better than after-only static scanning for that specific task.

This guide explains the entire project from zero knowledge to full operational understanding: concepts, threat model, taxonomy, validator design, controlled benchmark, field pilot, human labeling, results, repository layout, reproduction commands, and how to present the work.

---

## Chapter 2. Glossary (learn these once)

### 2.1 GitHub
A platform for hosting repositories and collaborating through commits and pull requests (PRs).

### 2.2 GitHub Actions
GitHub’s automation system for CI/CD workflows: build, test, release, and security scanning jobs.

### 2.3 Workflow file
A YAML file under `.github/workflows/` that defines triggers, permissions, jobs, and steps.

### 2.4 AI coding agent
An LLM-based system that can write or edit code and open PRs. In field data we use agent labels from the AIDev mining setting.

### 2.5 Security regression
A change that makes the after workflow less safe than the before workflow on monitored dimensions. Pre-existing insecurity that does not worsen is not counted as a regression of this change.

### 2.6 Policy-based validator
Our detector: it extracts security signals from before and after YAML, diffs them, and fires versioned rules (R01–R15).

### 2.7 zizmor
An existing static analyzer for CI/CD configurations. We use it as a baseline under two operationalizations: after-only, and before/after finding-set difference.

### 2.8 AIDev
A large research dataset of AI-agent pull requests on public GitHub. We use it for the field pilot.

### 2.9 Evaluation metrics (plain language)

- **Precision:** Of the alarms the detector raised, what fraction were real regressions?
- **Recall:** Of all real regressions, what fraction did the detector find?
- **F1:** Harmonic mean of precision and recall.
- **FPR (false-positive rate):** Of non-regressions, what fraction were wrongly flagged?
- **FNR (false-negative rate):** Of real regressions, what fraction were missed?

**Supervisor-friendly line:** We want to catch worsenings without raising noisy alarms on harmless or hardening edits.

### 2.10 Gold label
The reference answer used for scoring detectors. In the controlled suite, gold follows curated fixtures. In the field pilot, gold is a reproducible predicate audit under policy v3. A human subset provides an independent reading of 63 pairs.

### 2.11 OWASP CI/CD Top 10
A community catalog of major CI/CD security risk categories. Our rules are mapped to those categories for interpretability.

---

## Chapter 3. Why the topic matters

### 3.1 Functional success is not security
A pipeline can pass unit tests, keep CI green, and still:

- widen token permissions;
- remove a security gate;
- introduce an unpinned third-party Action;
- create a poisoned-pipeline pattern.

“It works” and “it is safe” are different claims.

### 3.2 Do not mix two threat models
Security literature often discusses two nearby but different problems:

1. **Agent runs inside CI** and reads untrusted issue/PR content, risking secret leakage via prompt injection. Industry reports from Microsoft and CSA emphasize this runtime setting.
2. **Agent authors workflow files** in a PR. Even if no agent executes inside Actions, the merged YAML can still become less safe.

**This project focuses on model (2):** the agent (or any author) as a workflow editor.

### 3.3 Why after-only scanners are not enough for our question
Tools such as zizmor are valuable for: “Does the landing file still contain risky patterns?”

Our question is different: “Did this PR make security worse than before?”

Those questions diverge:

- The after file may still have old findings, yet be no worse than before → after-only scanning still alarms, but the change is not necessarily a regression.
- The after file may look cleaner because a CodeQL job was deleted → after-only scanning may miss the removal, while a before/after policy catches it as a regression.

### 3.4 Practical motivation for merge gates
As agents touch `.github/workflows/` more often, organizations need lightweight checks that block clear worsenings at merge time. Our validator is designed for that role: tens of milliseconds per pair on the field set, declarative policies, and rule-linked findings.

---

## Chapter 4. Research questions

**RQ1:** What types of security regressions appear in agent-related GitHub Actions workflow diffs, and how are they distributed?

**RQ2:** Do regression rates differ between agent-labeled and human-labeled changes under a matched evaluation setting?

**RQ3:** Can a policy-based before/after validator detect regressions with competitive precision/recall and controlled false positives relative to after-oriented static baselines?

**How to say this simply:** First map the failure modes; second compare agent vs human strata; third measure whether our diff-aware detector is useful.

---

## Chapter 5. High-level method (the production line)

Think of the method as five linked stages:

**A. Define rules.** We built a taxonomy of automated regression classes (R01–R15, with R99 reserved for manual residuals) mapped to OWASP CI/CD categories. Rules live in a versioned declarative policy file.

**B. Build the validator.** The program reads before/after YAML, extracts signals, diffs them, and emits findings.

**C. Controlled evaluation.** Fifteen synthetic pairs cover major regressions and safe negatives. This is an implementation check.

**D. Field evaluation.** We materialized AIDev/GitHub workflow pairs (N=330), assigned policy-v3 gold labels, and scored detectors.

**E. Baseline comparison.** The same pairs were evaluated with zizmor after-only and zizmor before/after finding-set diff.

Additionally, a stratified human annotation pack was prepared; annotator A labeled 63 pairs for an independent check.

---

# Part II — Concepts Inside a Workflow File

## Chapter 6. Anatomy of a GitHub Actions workflow

A conceptual workflow contains:

- `on:` events that start the run (`push`, `pull_request`, `pull_request_target`, `workflow_run`, `issue_comment`, …);
- `permissions:` what the `GITHUB_TOKEN` may do;
- `jobs:` named jobs;
- inside each job: `runs-on` (runner) and `steps`;
- in steps: either `uses:` (reuse an Action) or `run:` (shell script).

An Action reference looks like:

`uses: owner/name@ref`

The `ref` may be:

- a floating tag such as `v4` or `main` (can move);
- a 40-character commit SHA (pinned to one immutable revision).

Pinning to SHA is usually safer for supply-chain trust because a tag can be force-moved to malicious content.

Security-relevant signals we extract include:

- permission maps and dangerous write scopes;
- trigger sets;
- Action identities and pin strength;
- suspicious script patterns (secret echo, injection, curl|bash, GITHUB_ENV writes);
- presence/absence of security jobs (for example CodeQL);
- self-hosted runners.

---

## Chapter 7. Formal definition of regression

Let \(W_b\) and \(W_a\) be before and after workflow documents for the same path.  
Let \(S(\cdot)\) be the extracted signal set.

The pair is a security regression if and only if there exists a rule \(i\) in R01–R15 such that \(\mathrm{Worse}_i(S(W_b), S(W_a))\) holds.

Important consequences:

- Unchanged pre-existing insecurity is **not** a regression.
- Hardening (adding CodeQL, pinning SHA) should not fire as regression.
- The construct is change-relative, not snapshot-absolute.

Policy version used in the current freeze: **3.0.0** in `policies/owasp_cicd_rules.yaml`, with formal notes in `policies/rule_formal_spec.md`.

---

# Part III — The Rule Taxonomy (R01–R15)

## Chapter 8. Why a taxonomy instead of one “bad change” bit?

A taxonomy is an organized catalog. We do not only say “this change is bad.” We say **which kind of badness** occurred. That helps:

- interpret field distributions;
- debug false positives/negatives;
- map findings to OWASP categories;
- tune organizational policy packs.

Each automated class has an identifier R01…R15. R99 is reserved for human residuals not yet automated.

---

## Chapter 9. Rule-by-rule explanation with examples

### 9.1 R01 — Escalation to write-all
**Intent:** Detect broad write-token escalation.  
**Typical pattern:** before has `contents: read`; after has `permissions: write-all`.  
**Why it matters:** A compromised step can do far more damage with a powerful token.  
**Fixture:** `data/sample/r01_permissions_write_all`

### 9.2 R02 — Permissions restriction removed
**Intent:** Detect removal of explicit least-privilege maps.  
**Typical pattern:** before has an explicit permissions block; after drops it.  
**Fixture:** `data/sample/r02_permissions_removed`

### 9.3 R03 — pull_request_target introduced
**Intent:** New PPE-capable trigger.  
**Why it matters:** `pull_request_target` can run with higher trust than ordinary `pull_request`.  
**Fixture:** `data/sample/r03_pr_target`

### 9.4 R04 — Privileged checkout of untrusted PR head
**Intent:** Combined with privileged context, checking out attacker-controlled code is dangerous.  
**Typical pattern:** checkout with `ref: ${{ github.event.pull_request.head.sha }}` after introducing privileged triggers.  
**Often co-fires with R03.**

### 9.5 R05 — Effective SHA pin lost
**Intent:** Same Action key loses effective pin (40-hex `@ref` or trailing `# <sha>` comment).  
**Typical pattern:** `actions/checkout@<sha>` becomes `actions/checkout@v4`.  
**Fixture:** `data/sample/r05_comment_pin_lost` (and related)

### 9.6 R06 — New untrusted unpinned third-party Action
**Intent:** A brand-new Action identity appears without SHA pin.  
**Trusted-owner exception:** owners such as `actions/`, `github/`, `docker/` (configurable) are exempt for R06 noise control; pin loss on those owners still matters under R05.  
**Identity key:** `(owner, name, ref)` for “new”; pin-loss uses `(owner, name)`.

### 9.7 R07 — Secret exposure patterns
**Intent:** New script patterns that echo secrets or dump environments into logs.  
**Signal:** `secret_echo_hits` counters on `run:` scripts.

### 9.8 R08 — Security gate removed
**Intent:** Deletion of security jobs/steps (for example CodeQL) while ordinary CI may remain.  
**Why diff-awareness matters:** after-only scanners may not treat “missing job” as a new finding.

### 9.9 R09 — workflow_run introduced
**Intent:** New high-trust trigger patterns via `workflow_run`.  
**Fixture:** `data/sample/r09_workflow_run`

### 9.10 R10 — Script injection patterns
**Intent:** Untrusted `github.event` fragments interpolated into `run:` scripts.  
**Signal:** `injection_hits`.

### 9.11 R11 — Self-hosted runner introduced
**Intent:** Moving execution onto organization-owned runners changes blast radius and operational trust.

### 9.12 R12 — Dangerous write scopes raised
**Intent:** Even without `write-all`, adding scopes such as `contents: write` or `id-token: write` can be a serious escalation.  
**Fixture:** `data/sample/r12_contents_write`

### 9.13 R13 — Remote pipe-to-shell
**Intent:** New `curl … | bash` / `wget … | sh` style patterns.  
**Fixture:** `data/sample/r13_curl_bash`

### 9.14 R14 — Dangerous interactive triggers
**Intent:** New triggers such as `issue_comment` that can enable interaction-driven PPE paths.  
**Fixture:** `data/sample/r14_issue_comment`

### 9.15 R15 — Untrusted writes into GITHUB_ENV / GITHUB_PATH
**Intent:** Untrusted values written into runner environment files can poison later steps.  
**Fixture:** `data/sample/r15_github_env`

### 9.16 R99 — Manual residual
Reserved for annotator-defined issues not covered by automation yet.

### 9.17 Why these rules were chosen
They are:

1. observable on YAML text;
2. aligned with public hardening guidance and OWASP CI/CD themes;
3. meaningful as before/after worsenings, not merely “file looks ugly.”

---

# Part IV — System Design and Code

## Chapter 10. End-to-end architecture

```text
[Synthetic fixtures / AIDev PRs]
        | filter .github/workflows
        v
[Before YAML] ----\
                   >--> Signal extraction --> Diff --> Policy rules --> Findings
[After YAML] -----/
        |
        +--> Gold labels
        |
        +--> Metrics vs baselines --> Tables/Figures --> Manuscript / Guide
```

Core modules under `src/`:

- `workflow_parse/signals.py` — parse YAML and extract `SignalSet`
- `policy_validator/validator.py` — apply policy rules and emit findings
- `baselines/zizmor_baseline.py` — after-only and before/after-diff baselines
- `evaluate/run_eval.py` — score detectors against label CSVs
- `evaluate/metrics.py` — precision/recall/F1/FPR helpers
- `labeling/prelabel.py` — assistance for labeling pipelines
- `github_fetch/fetch_pairs.py` — fetch before/after workflow contents

Policies:

- `policies/owasp_cicd_rules.yaml` (v3.0.0)
- `policies/rule_formal_spec.md`
- `policies/rule_owasp_map.md`

---

## Chapter 11. What the validator does step by step

1. Receive two paths: before YAML and after YAML for the same workflow.
2. Parse both documents (invalid YAML yields parse findings).
3. Extract signals: triggers, permissions, actions, scripts, security jobs, runners.
4. Compare signals under each rule’s `Worse` predicate.
5. Emit findings with rule id, severity, and short message.
6. For binary evaluation, any non-parse finding ⇒ predicted positive.

Mean latency on the field set is on the order of tens of milliseconds per pair, which is compatible with CI merge gates on workflow paths.

---

## Chapter 12. Baselines in detail

### 12.1 After-only zizmor
Run zizmor on the after file. If any finding exists, predict regression = 1.

This answers residual risk in the landing revision. As a regression label it is often too noisy because old issues still fire.

### 12.2 Before/after finding-set diff
Run zizmor on before and after; treat newly appearing findings as positives.

This is fairer for the regression task than after-only, but still not identical to our policy predicates. In the field pilot it reduced FPR from about 0.91 to about 0.18, remaining above the policy validator’s FPR.

### 12.3 Framing versus zizmor
High after-only FPR on regression labels does **not** prove zizmor is a weak security scanner for its intended use. It proves snapshot findings are not interchangeable with “this PR made security worse.” Organizations should run both classes of checks.

---

# Part V — Experiments and Data

## Chapter 13. Controlled benchmark (N=15)

### 13.1 Purpose
Verify that rules and the validator implementation behave as designed on known fixtures.

### 13.2 Composition
Fifteen before/after pairs under `data/sample/`:

- ten positive regressions spanning major rules;
- five negatives (harmless echo, CodeQL addition, trusted security Action addition, SHA pinning hardening, non-regression where `write-all` already existed).

Labels: `annotations/labels_sample.csv`.

### 13.3 Key result
Policy validator: Precision 1.00, Recall 1.00, F1 1.00, FPR 0.00.  
zizmor after-only: Precision 0.67, Recall 1.00, F1 0.80, FPR 1.00.

**Interpretation:** Perfect controlled scores are an implementation correctness check on a co-designed suite, not proof of universal robustness on all GitHub projects.

### 13.4 Illustrative RQ2 on fixtures
Agent-tagged positives were all regressions (9/9) versus 1/6 among human-tagged pairs. Agent tags on fixtures are synthetic for coverage and must **not** be read as epidemiology of production agents.

---

## Chapter 14. Field pilot (N=330)

### 14.1 Sampling idea
Start from AIDev / GitHub evidence of PRs touching workflow paths, materialize before/after YAML, and include repo-matched human controls where possible.

### 14.2 Stratum sizes
- OpenAI_Codex: 200
- Claude_Code: 20
- Copilot: 20
- Cursor: 6
- Devin: 4
- human controls: 80
- Jules: no workflow hits in the probed subsample

Total: **N = 330**

### 14.3 Field gold
Field gold is a reproducible predicate audit aligned with policy v3 (`scripts/field_gold_audit.py`), stored in `annotations/labels_aidev.csv`. It is independent of live validator predictions but still specification-tied.

Under current v3 audit: **46 / 330 = 13.9%** gold regressions.

Earlier drafts cited ≈39–40 positives under narrower interim predicates. Replaying historical definitions on the same 330 paths shows the increase is a **relabel under an expanded formal definition** (notably R12–R15), not a silent resample. See `paper/manuscript/tables/field/gold_v_delta.md`.

### 14.4 Detector results (field)

| Method | Precision | Recall | F1 | FPR | FNR |
|--------|----------:|-------:|---:|----:|----:|
| Policy Validator | 0.88 | 0.93 | 0.91 | 0.02 | 0.07 |
| zizmor after-only | 0.15 | 0.96 | 0.25 | 0.91 | 0.04 |
| zizmor before/after-diff | 0.40 | 0.74 | 0.52 | 0.18 | 0.26 |

### 14.5 Rates by stratum (v3 gold)

| Stratum | N | Rate |
|---------|--:|-----:|
| OpenAI_Codex | 200 | 0.180 |
| Claude_Code | 20 | 0.050 |
| Copilot | 20 | 0.000 |
| Cursor | 6 | 0.500 |
| Devin | 4 | 0.000 |
| All AI pooled | 250 | 0.160 |
| Human | 80 | 0.075 |

Pooled agent vs human: 0.160 vs 0.075, chi-square p ≈ 0.085 (not significant at α=0.05). Directionally higher agent rates appear, but this pilot does not establish a conclusive population difference. Small cells (Cursor/Devin) require caution.

### 14.6 Frequent automated hits
Field rule hits commonly include unpinning / untrusted Action patterns (for example R06) and dangerous scopes (R12), among others listed in `eval_summary.json`.

---

## Chapter 15. Human annotation subset

### 15.1 Pack design
A stratified pack of 80 pairs (all 46 v3 positives + 34 stratified negatives) lives under `annotations/human_round/`.

Annotators see only before/after YAML paths—not validator predictions and not `predicate_gold_key.csv`.

### 15.2 What was completed
Annotator A labeled **63** pairs (36 positive, 27 negative).  
**17** pairs lacked available YAML locally and were left unlabeled.  
Human labels follow a **single-annotator evaluation**; Cohen’s κ is not estimated.

### 15.3 Detector vs human gold (n=63)

| Method | Precision | Recall | F1 | FPR | FNR | N |
|--------|----------:|-------:|---:|----:|----:|--:|
| Policy Validator | 0.87 | 0.94 | 0.91 | 0.19 | 0.06 | 63 |

This shows strong recall and solid precision against an independent human reading, with higher FPR than on predicate-aligned field gold—consistent with humans sometimes applying broader judgment than formal predicates.

---

## Chapter 16. Qualitative cases (to explain by hand)

**Case A — Permissions escalation.**  
Before: `contents: read`. After: `write-all`. Validator fires R01/R02. Tests may still pass.

**Case B — Poisoned pipeline setup.**  
Before: `pull_request`. After: `pull_request_target` plus checkout of PR head. Critical findings (R03/R04).

**Case C — Security gate removal.**  
Before includes CodeQL job. After deletes it but keeps tests. R08 fires. After-only scanners may not isolate the removal event.

**Case D — Benign hardening.**  
Adding CodeQL or pinning `actions/checkout` to a SHA should not fire as regression.

---

# Part VI — Repository Map and Reproduction

## Chapter 17. Directory tour

```text
مقاله روش پژوهش/
  src/                      # validator, parsing, evaluation, baselines
  policies/                 # OWASP-mapped rule pack v3 + formal spec
  data/sample/              # controlled before/after fixtures
  data/processed/           # materialized field pairs (when present)
  annotations/              # labels_sample, labels_aidev, human_round
  scripts/                  # sampling, gold audit, IAA, docx builders
  tests/                    # unit tests for rules and baselines
  paper/manuscript/         # main.md, main_fa.md, tables, figures, guides
  paper/literature/         # search notes, reference audit, adequacy
  replication/              # REPRODUCE.md, DATA_CARD.md
```

Important manuscript artifacts:

- English short paper: `paper/manuscript/main.md` (+ DOCX)
- Persian print article: `paper/manuscript/main_fa.md` (+ DOCX)
- This full guide: `paper/manuscript/Project_Guide_EN_0_to_100.md` (+ DOCX)
- Field metrics: `paper/manuscript/tables/field/eval_summary.json`
- Controlled metrics: `paper/manuscript/tables/controlled/eval_summary.json`

---

## Chapter 18. Environment setup

```powershell
cd "d:\مقاله روش پژوهش"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = "src"
```

Optional: install `zizmor` on PATH for baseline regeneration.

---

## Chapter 19. Reproduce the numbers

### 19.1 Unit tests
```powershell
python -m pytest tests -q
```

### 19.2 Controlled evaluation
```powershell
python -m evaluate.run_eval --labels annotations/labels_sample.csv --out paper/manuscript/tables/controlled
```

### 19.3 Field evaluation
```powershell
python -m evaluate.run_eval --labels annotations/labels_aidev.csv --out paper/manuscript/tables/field
```

### 19.4 Gold definition delta
```powershell
python scripts/gold_version_delta.py
```

### 19.5 Human-gold evaluation
```powershell
python scripts/eval_human_gold.py
```

### 19.6 Regenerate documents
```powershell
python scripts/md_to_docx.py
python scripts/main_fa_to_docx.py
python scripts/build_project_guide_en.py
```

---

## Chapter 20. Data card summary

**Synthetic benchmark:** hand-crafted YAML pairs; no real secrets; intended for reproducible detector checks and teaching.

**AIDev-derived field data:** cite AIDev; public repos only; do not redistribute bulk upstream dumps; redact secret-looking strings before sharing.

**Labels:**

- `labels_sample.csv` — controlled gold
- `labels_aidev.csv` — field predicate-v3 gold
- `human_round/` — annotation pack and provisional single-annotator gold

---

# Part VII — How to Present and Defend the Work

## Chapter 21. A 3-minute oral summary

1. Agents edit GitHub Actions workflows, not only application code.
2. Green CI does not mean security posture stayed the same.
3. We define security regressions as before-to-after worsenings and encode fifteen automated rules.
4. We built a policy validator that diffs security signals.
5. On 15 controlled pairs it recovers curated regressions with FPR 0.00 (implementation check).
6. On 330 field pairs, audited regression rate is 13.9%; validator reaches about P0.88 / R0.93 / FPR0.02.
7. After-only zizmor is too noisy as a regression predictor; before/after finding diff helps but remains weaker than our policy gate.
8. A human-labeled subset (n=63) also shows strong agreement (F1≈0.91).
9. Practical takeaway: add diff-aware policy checks to merge gates for workflow paths, alongside snapshot scanners.

---

## Chapter 22. Likely supervisor questions and answers

**Q: Is F1=1.00 on the controlled set overfitting?**  
A: The suite is co-designed with the rules. Treat it as an implementation check. The field pilot and human subset are the more informative external signals.

**Q: Are field detector scores circular?**  
A: Field gold and the detector share the same predicate family by design for a specified gate. That is useful for policy enforcement measurement, but it is not identical to fully independent dual human adjudication.

**Q: Did you prove agents are worse than humans?**  
A: No conclusive population claim. Field pooled rates are 16.0% vs 7.5% with p≈0.085. Directional only.

**Q: Why not only use zizmor?**  
A: zizmor answers residual risk in a file. We answer whether a change worsened security. Both are needed.

**Q: What is ready for secretariat print?**  
A: The Persian article DOCX is the short print manuscript. This English guide is the complete project explanation document.

---

## Chapter 23. Contributions checklist

1. OWASP-mapped regression taxonomy (R01–R15).
2. Open policy-based before/after validator with versioned predicates.
3. Controlled empirical evaluation (N=15).
4. Field pilot (N=330) with documented gold-definition revision.
5. Human single-annotator subset evaluation (n=63).
6. Reproducible scripts, tests, tables, and manuscripts.

---

## Chapter 24. Limitations (for technical understanding; optional in short print papers)

- Controlled suite co-design risk.
- Field gold is predicate-aligned.
- Some agent cells are small.
- Human evidence is single-annotator on 63 pairs; 17 pack rows missing YAML; no independent second rater / κ.
- After-only baseline is a strict operationalization of residual findings as regression labels.

These points matter for scientific honesty when discussing the work in depth. Short secretariat print versions may omit a dedicated limitations section by local preference.

---

## Chapter 25. Future work

1. Enlarge sparse agent cells and strengthen human matching.
2. Package the validator as a GitHub Action for merge protection on workflow paths.
3. Support organization-tunable policy packs beyond default trusted owners.
4. (Optional, not in this delivery) a second human annotator if a later journal revision requires κ.

---

# Part VIII — Deep Reference Material

## Chapter 26. Signal extraction notes

The signal layer normalizes Action owners/names, computes permission scores, unions dangerous write scopes, detects effective pins (SHA ref or trailing comment SHA), and precomputes script hit counters:

- `secret_echo_hits`
- `injection_hits`
- `pipe_shell_hits`
- `github_env_injection_hits`

These counters keep rule logic readable and testable.

---

## Chapter 27. Trusted owners and policy tuning

R06 uses a trusted-owner allowlist to reduce noise on common maintainers (`actions`, `github`, `docker`, and selected security vendors as configured). Organizations can tighten or loosen this list. Pin-loss (R05) remains important even for trusted owners because tags move.

Dangerous scopes for R12 and interactive triggers for R14 are also configurable in the YAML policy.

---

## Chapter 28. Worked example walkthrough (permissions)

Before:

```yaml
permissions:
  contents: read
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test
```

After:

```yaml
permissions: write-all
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm test
```

Functional tests can still pass. Security posture is worse. Expected findings: R01 (and typically R02-related restriction removal behavior depending on representation). This is the canonical teaching example for non-specialists.

---

## Chapter 29. Worked example walkthrough (security job removal)

Before includes a `codeql` job using `github/codeql-action/*`.  
After deletes that job and retains only tests.

Expected finding: R08.  
Why after-only scanning may miss the story: the after file is shorter and may look “cleaner,” yet assurance decreased.

---

## Chapter 30. Interpreting tables without overclaiming

When you show Table-style results:

- Say “on the controlled suite” for F1=1.00.
- Say “under policy-v3 gold on N=330” for field metrics.
- Say “provisional single-annotator human gold, n=63” for human metrics.
- Never convert Fisher/chi-square p-values into definitive causality claims about all AI agents.

---

## Chapter 31. File-level checklist before a meeting

- [ ] Can explain security regression in one minute
- [ ] Can contrast after-only scanning vs before/after policy
- [ ] Know N=15 / N=330 / n=63 numbers
- [ ] Know where policy YAML lives
- [ ] Can open one fixture pair and narrate findings
- [ ] Can reproduce controlled eval command
- [ ] Know Persian print DOCX path for secretariat
- [ ] Know this English guide path for full explanation

---

## Chapter 32. Extended FAQ

**Is YAML parsing perfect?**  
No parser is perfect on every exotic Actions expression. Parse failures are surfaced; tests cover core patterns.

**Do we claim to detect all possible CI/CD risks?**  
No. We detect a curated, automatable regression catalog. R99 exists for residuals.

**Can policies be organization-specific?**  
Yes; that is an intended future packaging direction.

**Where are figures?**  
`paper/manuscript/figures/` (method F1, rule counts, agent rates) generated from evaluation outputs.

**What English short manuscript status is this guide aligned with?**  
Delivery manuscript v0.4 numbers: controlled + field N=330 + human n=63.

---

## Chapter 33. Mapping rules to everyday language

| Rule | Everyday meaning |
|------|------------------|
| R01 | Token became extremely powerful (`write-all`) |
| R02 | Least-privilege map disappeared |
| R03/R04 | Privileged PR trigger / untrusted checkout path |
| R05 | Locked Action version became floating |
| R06 | New less-trusted Action without lock |
| R07 | Secrets more likely to leak into logs |
| R08 | Security scanner/job removed |
| R09 | New workflow_run trust path |
| R10 | Untrusted text can break into shell commands |
| R11 | Jobs now run on self-hosted machines |
| R12 | Dangerous write scopes increased |
| R13 | Download-and-run remote script pattern added |
| R14 | Dangerous comment/interactive triggers added |
| R15 | Untrusted values written into runner env files |

---

## Chapter 34. End-to-end narrative for a written report

If you must write one coherent paragraph for a progress report:

AI coding agents increasingly modify GitHub Actions workflows. Because successful builds do not guarantee preserved security controls, this project defines security regressions as before-to-after worsenings of workflow security posture, implements an OWASP-mapped policy validator over fifteen automated rule classes, and evaluates the approach on a controlled fifteen-pair suite, a 330-pair AIDev/GitHub field pilot (13.9% audited regressions under policy v3), and a 63-pair human-labeled subset. The validator achieves perfect scores on the co-designed controlled suite as an implementation check, strong predicate-aligned field metrics (about precision 0.88, recall 0.93, FPR 0.02), and F1 about 0.91 against human labels. Compared with after-only static scanning, diff-aware policy checking is a more appropriate construct for merge-gate decisions about whether a pull request made CI security worse.

---

## Chapter 35. Closing of the core narrative

The chapters above already cover the problem, definitions, rules, architecture, datasets, experiments, results, repository layout, reproduction commands, and presentation tips. The remaining parts expand the same project into a full reference handbook so that a reader can understand every major artifact without opening the code first.

**Primary deliverables reminder**

- Full English guide (this document): `Project_Guide_EN_0_to_100.docx`
- Short English manuscript: `Security_Regressions_GHA_AI_Agents_Manuscript.docx`
- Persian secretariat article: `Security_Regressions_GHA_AI_Agents_Manuscript_FA.docx`

---

# Part IX — Expanded Teaching Handbook

## Chapter 36. From “I know nothing” to “I can teach this”

If you are completely new, follow this reading order:

1. Chapters 1–4 (problem and questions)
2. Chapters 6–7 (workflow anatomy and regression definition)
3. Chapter 9 (rules with examples)
4. Chapters 13–15 (results)
5. Chapter 21 (3-minute talk)
6. Then come back to architecture and reproduction when you need to run code

Do not start with the raw YAML policy file. Start with the story, then the construct, then the evidence.

---

## Chapter 37. A classroom analogy for security regression

Think of a building safety inspection.

An after-only scanner is like inspecting the building after renovation and listing every remaining hazard. That is useful.

A regression detector is like comparing yesterday’s inspection to today’s inspection and asking: “Did today’s renovation make the building less safe?”

If yesterday already had a cracked window and today still has it, that is residual risk, not a new regression caused by today’s renovation. If today removed the fire extinguishers, that is a regression even if the rooms look cleaner.

This analogy is the conceptual heart of the project.

---

## Chapter 38. Why GitHub Actions is a high-value attack surface

GitHub Actions often has:

- access to repository contents;
- access to secrets and deployment credentials;
- ability to publish packages or release assets;
- ability to approve or comment via tokens;
- trust boundaries between forks, issues, and privileged workflows.

A small YAML edit can therefore change the blast radius of many later executions. That is why workflow paths deserve special merge protection.

---

## Chapter 39. Common misconceptions

**Misconception 1:** “If CI is green, security is fine.”  
False. CI greenness usually measures functional tests, not permission posture.

**Misconception 2:** “Any zizmor finding means this PR caused a regression.”  
False. Findings may be pre-existing.

**Misconception 3:** “If the after file has fewer findings, security improved.”  
Not necessarily. Removing a scanner can reduce findings while reducing assurance.

**Misconception 4:** “Perfect controlled F1 means the detector is universally solved.”  
False. Controlled fixtures verify implementation. Field and human evidence are needed for broader claims.

**Misconception 5:** “This project claims all AI agents are insecure.”  
False. We report pilot rates and detector utility. Population epidemiology remains cautious.

---

## Chapter 40. Detailed controlled-suite tour

The controlled suite is intentionally pedagogical. Each positive fixture isolates one main story:

- permissions opened too widely;
- privileged PR patterns introduced;
- pins lost;
- secrets/injection patterns added;
- security jobs removed;
- self-hosted runners added;
- dangerous scopes / interactive triggers / env injection (later rules).

Negatives intentionally include:

- trivial script text changes;
- adding CodeQL;
- pinning to SHA;
- already-bad-before non-worsening edits.

When explaining to a supervisor, open one positive and one negative side by side. That contrast teaches the construct faster than any metric table.

---

## Chapter 41. How field pairs are conceptually created

At a high level:

1. Identify PRs that touch workflow paths in AIDev/GitHub evidence.
2. Recover the before revision and after revision of the same workflow path.
3. Store them as a pair with metadata (agent label, repo, path).
4. Audit gold under policy predicates.
5. Run detectors and aggregate metrics by stratum.

Exact download commands depend on local caches and upstream availability. The evaluation entry point once labels exist is `python -m evaluate.run_eval`.

---

## Chapter 42. Understanding gold revision (interim → v3)

Scientific transparency requires explaining why positive counts changed on a fixed N=330 set.

- Interim heuristic drafts reported about 39–40 positives.
- Formalization and expansion (trusted-owner/pin alignment plus R12–R15) produced 46 positives.
- The pair set stayed the same; the definition expanded.
- Therefore the jump is a definition revision, not hidden resampling.

This is important if a reviewer asks: “Why did your number change?”

---

## Chapter 43. Reading eval_summary.json like a human

Open `paper/manuscript/tables/field/eval_summary.json`. You will see:

- `n` — number of pairs
- `regression_rate` — gold positive rate
- `policy_validator` — confusion-derived metrics
- `baseline_after_only` / `baseline_before_after_diff` — zizmor operationalizations
- `rule_counts` — which rules fired how often
- `per_agent_regression_rate` — stratum rates
- `ai_vs_human` — pooled comparison and p-value

You do not need to memorize every field. For meetings, remember validator P/R/FPR, zizmor-diff FPR, overall rate 13.9%, and pooled AI vs human rates.

---

## Chapter 44. Annotation protocol in practice

For this delivery, human labeling stops at one annotator:

1. Give the annotator only YAML paths and the guide.
2. Forbid opening validator outputs and gold keys.
3. Label `has_regression` as 0/1.
4. Optionally record confidence and notes.
5. Build gold from filled A rows and run `eval_human_gold.py`.

Human evaluation is reported as single-annotator only; no inter-rater κ is claimed.

---

## Chapter 45. Script catalog (what each script is for)

- `sample_human_annotation_set.py` — build the 80-pair pack
- `compute_iaa.py` — inter-annotator agreement
- `eval_human_gold.py` — detector vs adjudicated/human gold
- `field_gold_audit.py` — predicate audit for field gold
- `gold_version_delta.py` — compare gold definitions on fixed pairs
- `analyze_field_fn.py` — false-negative analysis helpers
- `merge_field_eval.py` — merge evaluation pieces when needed
- `md_to_docx.py` — English short manuscript Word export
- `main_fa_to_docx.py` — Persian print Word export
- `build_project_guide_en.py` — this full English guide
- `guide_fa_to_docx.py` — older Persian educational guide export
- AIDev sampling helpers: `stream_aidev_workflows.py`, `sample_agents_via_github.py`, `sample_human_controls.py`, `try_aidev_download.py`

You rarely need all scripts in one sitting. For defense meetings, reproduction of tables matters most.

---

## Chapter 46. Test suite purpose

Unit tests under `tests/` protect rule semantics and baseline wiring. They reduce the risk that a later refactor silently changes R05/R06 identity logic or zizmor-diff behavior. Before claiming regenerated numbers, run `pytest`.

---

## Chapter 47. Severity and finding messages

Findings are not only binary positives. They carry rule identifiers and severity so a reviewer can triage:

- critical patterns (for example privileged PR + untrusted checkout);
- high/medium supply-chain pin issues;
- script-injection and secret-exposure patterns;
- control-removal events.

In merge gates, organizations may block on selected severities or selected rule families only.

---

## Chapter 48. Ablation intuition

Even without listing every ablation number, the idea is simple:

- permissions-only rules catch only a subset;
- pinning-only rules catch another subset;
- full policy is needed for broad recall.

The controlled ablation tables in the manuscript show that no single family replaces the full pack.

---

## Chapter 49. Related work positioning paragraph

Prior MSR challenge work measures how often agents touch CI/CD and whether builds succeed. Other work studies reliability of workflow runs. Static tools inspect residual risk in a revision. Industry reports document prompt-injection against agents executing inside Actions. Our contribution sits in the remaining gap: authoring-time before/after security regressions in workflow diffs, plus a policy gate specialized to that construct.

---

## Chapter 50. OWASP mapping philosophy

We do not claim a one-to-one exclusive mapping from each rule to exactly one OWASP item with no overlap. Real failures touch multiple categories. Mapping is a communication aid: it connects our engineering predicates to a vocabulary security practitioners already know.

---

## Chapter 51. Supply-chain angle (pins and third parties)

Modern CI is a software supply chain. Floating tags on third-party Actions are convenient and risky. Compromised Action tags have appeared in public incidents. R05 and R06 encode the regression view of that risk: not merely “is this pinned now?” but “did this change remove a pin or introduce a new unpinned third party?”

---

## Chapter 52. Secrets and logging angle

Secrets in Actions are easy to mishandle. Printing them, dumping environments, or writing untrusted values into `GITHUB_ENV` can escalate quickly. Rules R07 and R15 target change-introduced patterns of this family. They are pattern-based and therefore incomplete, but they catch high-value mistakes that often survive functional tests.

---

## Chapter 53. Trigger-trust angle

Not all events are equal. `pull_request` from forks, `pull_request_target`, `workflow_run`, and comment triggers have different trust assumptions. Several rules exist specifically because “we only changed the trigger” can be a major security event even when the build script looks identical.

---

## Chapter 54. How to demo the validator live

Suggested live demo script:

1. Open a positive fixture pair in an editor.
2. Ask the audience whether CI could still be green.
3. Run the validator on that pair.
4. Show the rule id and message.
5. Open a hardening negative.
6. Show that no regression finding fires.
7. Optionally show an after-only baseline alarm on a non-regression to illustrate construct mismatch.

This demo is more persuasive than slides alone.

---

## Chapter 55. Recommended slide outline (10 slides)

1. Title and one-sentence problem
2. Green CI ≠ preserved security
3. Two threat models; we study authoring-time edits
4. Definition of security regression
5. Taxonomy overview (grouped, not all 15 bullets)
6. Validator architecture diagram
7. Controlled results
8. Field results (rate + detector table)
9. Human subset + practical implication
10. Conclusion and next steps

---

## Chapter 56. Writing style guidance for your own Persian/English summaries

- Prefer short sentences.
- Define a term once, then reuse the Persian/English stable form.
- Put numbers in separate short sentences when possible.
- Avoid stacking many Latin tokens between one Persian verb.
- Keep claims scoped: controlled / field / human.

---

## Chapter 57. Ethical and redistribution notes

Use public data sources as licensed. Do not publish raw secret-looking strings. Prefer redacted indexes for sharing. Cite AIDev and tooling authors. Disclose AI writing assistance if the target venue requires it.

---

## Chapter 58. What “policy v3” changed conceptually

Policy v3 is not a cosmetic rename. It formalizes pin identity, trusted-owner exceptions, and additional high-value classes (dangerous scopes, pipe-to-shell, interactive triggers, env-file injection). That is why field positives increased on the same pairs: the gate became stricter and clearer, not randomly retargeted.

---

## Chapter 59. False positives and false negatives in plain language

**False positive:** detector says regression, human/gold says no. Cost: noisy merge blocking or alert fatigue.  
**False negative:** real regression missed. Cost: silent security worsening.

On predicate-aligned field gold, FPR is low (~0.02). On human gold, FPR is higher (~0.19), which is expected when humans use broader judgment than formal predicates. Both views are informative.

---

## Chapter 60. Why latency matters

A detector that needs minutes per file is hard to place on every workflow-path PR. Our validator’s millisecond-scale latency supports a practical merge-gate story: block clear worsenings quickly, leave deep residual scanning to heavier tools asynchronously if needed.

---

## Chapter 61. Organization rollout sketch

1. Start in audit mode: warn on R01/R03/R08/R12.
2. Measure noise for two weeks.
3. Turn blocking on for the noisiest high-severity rules with least disagreement.
4. Tune trusted owners and scope lists.
5. Keep zizmor/CodeQL for residual risk.

This project provides the measurement and the detector core for that rollout path.

---

## Chapter 62. Relationship to DevSecOps

DevSecOps argues security checks should be continuous and automated. Most pipelines already run tests continuously. Fewer pipelines continuously decide whether a configuration change reduced security assurance. Diff-aware workflow policy is a concrete DevSecOps control for the configuration layer.

---

## Chapter 63. Student maintenance guide

If you pause the project and return months later:

1. Read Chapter 1 and Chapter 21 again.
2. Run pytest.
3. Regenerate controlled and field tables.
4. Confirm `eval_summary.json` numbers still match the manuscript.
5. Only then change policy rules.

Never edit gold labels and policy predicates casually without recording a definition version note.

---

## Chapter 64. Manuscript vs guide vs Persian print

- **English manuscript (`main.md`)**: short scholarly paper style for venue-like reading.
- **Persian print (`main_fa.md`)**: secretariat/print-oriented short article.
- **This guide**: complete pedagogical and operational handbook.

They share the same scientific numbers but different depth and tone.

---

## Chapter 65. Full metric sheet (memorize or print)

Controlled (N=15):

- Validator P/R/F1/FPR = 1.00 / 1.00 / 1.00 / 0.00
- zizmor after-only F1 = 0.80, FPR = 1.00

Field (N=330, v3 gold):

- Rate = 13.9% (46/330)
- Validator ≈ P0.88 R0.93 F1 0.91 FPR 0.02
- zizmor after-only FPR ≈ 0.91
- zizmor diff FPR ≈ 0.18
- AI vs human rates 0.160 vs 0.075 (p≈0.085)

Human subset (n=63):

- Validator ≈ P0.87 R0.94 F1 0.91 FPR 0.19

---

## Chapter 66. Glossary expansion (symbols and shorthand)

- PPE: poisoned pipeline execution
- SHA: commit hash used as immutable pin
- FPR/FNR: false positive/negative rates
- PR: pull request
- GHA: GitHub Actions
- Policy pack: versioned YAML rule set
- Stratum: subgroup such as Codex or human controls
- Adjudication: resolving annotator disagreements into final gold

---

## Chapter 67. Minimal YAML literacy sheet

You should be able to recognize:

- a trigger block under `on:`
- a permissions map
- a job with `runs-on`
- a `uses:` Action line
- a `run:` script multiline block
- an expression like `${{ secrets.X }}` or `${{ github.event... }}`

If you can point to those with a mouse, you can explain most rules.

---

## Chapter 68. Security regression decision tree (manual)

When looking at a pair by eye:

1. Did permissions become broader?
2. Did a more privileged trigger appear?
3. Did a pin disappear or a new unpinned third party appear?
4. Did secret/injection/pipe/env-risk patterns appear?
5. Was a security job removed?
6. Did self-hosted runners appear?
7. If none of the above, lean toward non-regression even if the after file is not perfect.

This is essentially what annotators are asked to do.

---

## Chapter 69. Example annotation notes style

Good notes are short and causal:

- “Added contents:write at workflow level.”
- “Replaced pull_request with pull_request_target and checkout of PR head.”
- “Removed CodeQL job; tests remain.”
- “Only bumped Node version; no security worsening.”

Avoid vague notes like “looks bad” without saying why.

---

## Chapter 70. How this project can become a GitHub Action

Packaging direction:

1. Trigger on changes under `.github/workflows/**`
2. Fetch base and head versions of changed workflow files
3. Run the policy validator
4. Fail the check on selected severities
5. Print rule ids and remediation hints in the log

The research codebase already contains the core comparison engine for that productization path.

---

## Chapter 71. Remediation hints corresponding to rules

- R01/R02/R12: restore least privilege; avoid write-all
- R03/R04/R09/R14: avoid privileged triggers unless carefully hardened; never combine with untrusted checkout casually
- R05/R06: pin third-party Actions to SHA
- R07/R10/R13/R15: remove dangerous script patterns; pass data via env with proper escaping
- R08: do not delete security jobs without replacement control
- R11: justify self-hosted use and harden runners

---

## Chapter 72. What success looks like for the thesis narrative

A coherent thesis narrative is:

problem → construct → method → evidence → implication.

If each chapter of a thesis maps cleanly onto that chain, examiners can follow it. This project already has those pieces implemented and measured.

---

## Chapter 73. Risks if someone misuses the results

Misuses to avoid:

- claiming universal agent insecurity from N=330 pilot;
- replacing all security scanners with only this validator;
- treating controlled F1=1.00 as field-proof;
- hiding the gold-definition revision that changed 39→46.

Responsible communication strengthens credibility.

---

## Chapter 74. Backup and handoff checklist

Before handing the project to another student or archiving:

- [ ] Virtualenv instructions work on a clean machine
- [ ] pytest passes
- [ ] controlled and field JSON regenerate
- [ ] manuscripts open in Word
- [ ] data card and reproduce docs are current
- [ ] secrets are absent from shared archives

---

## Chapter 75. Final synthesis

This project starts from a simple observation: AI-assisted and human workflow edits can weaken CI/CD security without breaking builds. It responds with a precise construct (security regression), a concrete mechanism (policy-based before/after validation), and layered evidence (controlled, field, human). The engineering artifacts are reproducible; the scientific claims are scoped; and the practical implication is clear: merge gates for workflow paths should become diff-aware.

If you can explain that paragraph and then open one fixture pair to illustrate it, you understand the project from 0 to 100.

---

# Part X — Extended Appendices for Complete Mastery

## Chapter 76. Appendix A: week-by-week learning plan

**Week 1 — Concepts only.**  
Read Chapters 1–7. Write, in your own words, definitions of workflow, regression, and after-only versus before/after detection. Do not touch code yet.

**Week 2 — Rules.**  
Study Chapter 9 and open at least five fixtures under `data/sample/`. For each, write one sentence naming the worsened behavior.

**Week 3 — Validator mental model.**  
Read Chapters 10–12. Draw the architecture on paper from memory. Explain where zizmor enters as a baseline.

**Week 4 — Controlled evidence.**  
Run the controlled evaluation. Match your output to Table-style metrics in Chapter 13. Explain why FPR=1.00 for after-only is conceptually expected on that suite.

**Week 5 — Field evidence.**  
Read Chapters 14–15. Interpret stratum rates carefully. Practice answering the “are agents worse?” question without overclaiming.

**Week 6 — Communication.**  
Prepare the 3-minute talk and 10-slide outline. Deliver it once to a friend and once to yourself recorded.

This plan turns the repository from a pile of files into a mastered project.

---

## Chapter 77. Appendix B: command cookbook with expected intent

**Create environment**  
Intent: isolate dependencies.  
Command family: `python -m venv .venv` then activate and `pip install -r requirements.txt`.

**Set import path**  
Intent: make `src` modules importable as `evaluate`, `policy_validator`, and friends.  
Command: set `PYTHONPATH=src`.

**Run unit tests**  
Intent: verify rule predicates and baseline helpers still behave.  
Command: `python -m pytest tests -q`.

**Controlled eval**  
Intent: regenerate N=15 detector tables.  
Command: `python -m evaluate.run_eval --labels annotations/labels_sample.csv --out paper/manuscript/tables/controlled`.

**Field eval**  
Intent: regenerate N=330 detector tables.  
Command: `python -m evaluate.run_eval --labels annotations/labels_aidev.csv --out paper/manuscript/tables/field`.

**Human eval**  
Intent: score validator against filled human gold.  
Command: `python scripts/eval_human_gold.py`.

**Rebuild docs**  
Intent: refresh Word outputs after text edits.  
Commands: `md_to_docx.py`, `main_fa_to_docx.py`, `build_project_guide_en.py`.

Keep a personal log of the last date you regenerated each artifact.

---

## Chapter 78. Appendix C: explaining one fixture in a full page

Take permissions escalation as a one-page teaching sheet you can reuse:

**Title:** Permissions escalation as a security regression  

**Before state:** The workflow token is limited to reading repository contents.  

**After state:** The workflow token is `write-all`.  

**Functional view:** `npm test` or equivalent may still pass. Continuous integration looks healthy.  

**Security view:** Any code execution inside the workflow now inherits a much more powerful token. The blast radius expanded.  

**Detector view:** Policy rules compare permission signals and fire R01 (and related restriction-removal behavior).  

**Baseline view:** An after-only scanner might warn about broad permissions, but it would also warn if broad permissions already existed before. The regression detector specifically cares that the change introduced or increased the danger.  

**Takeaway sentence:** Green builds can hide authorization expansions.

If you can rewrite this page for CodeQL removal and for pin loss, you have internalized the project’s core pedagogy.

---

## Chapter 79. Appendix D: comparing three detector philosophies

**Philosophy 1 — Snapshot residual risk.**  
Question: What risks exist in the landing file?  
Typical tool: zizmor after-only, linters, scorecards.  
Strength: broad residual visibility.  
Weakness for our task: does not isolate worsenings.

**Philosophy 2 — Finding-set novelty.**  
Question: What new scanner findings appeared after the change?  
Typical tool: zizmor before/after diff.  
Strength: better aligned with change.  
Weakness: still depends on scanner vocabulary, not an explicit regression taxonomy.

**Philosophy 3 — Policy-diff regression gate.**  
Question: Did monitored security signals worsen according to explicit rules?  
Typical tool: this project’s validator.  
Strength: construct match for merge decisions; explainable rule ids.  
Weakness: coverage limited to encoded predicates; needs policy maintenance.

The project’s scientific claim is not that Philosophy 3 replaces 1 and 2. It is that Philosophy 3 is necessary in addition to them when the decision is “merge or block this workflow change.”

---

## Chapter 80. Appendix E: stratum interpretation workshop

When you see Cursor rate 0.500 with N=6, practice saying:

“The point estimate is high, but the cell is tiny. I will not generalize from six pairs. I will treat it as a flag for more sampling, not as a verdict.”

When you see Copilot rate 0.000 with N=20, practice saying:

“In this pilot subsample we observed no v3 gold regressions for Copilot. That is interesting but still a pilot cell, not a certification of safety.”

When you see Codex rate 0.180 with N=200, practice saying:

“This is the largest agent cell and contributes most of the pooled agent rate. It is the most stable agent-stratum estimate we currently have.”

This rhetorical discipline prevents the most common overclaiming failure mode in empirical security talks.

---

## Chapter 81. Appendix F: human labeling quality tips

High-quality labels come from process, not heroics:

- Rest after every twenty pairs.
- When uncertain, mark low confidence and write why.
- Do not negotiate with yourself toward the validator.
- Do not open predictor outputs “just to check.”
- Prefer missing labels over guessed labels when YAML is unavailable.

The 17 unlabeled pairs in the current pack are an example of preferring honesty over forced completeness.

---

## Chapter 82. Appendix G: mapping project artifacts to thesis chapters

A possible thesis chapter map:

1. Introduction and motivation ← Guide Chapters 1–4  
2. Background on Actions and CI/CD security ← Chapters 6–8, 50–53  
3. Related work ← Chapter 49 and literature notes  
4. Taxonomy and formal predicates ← Chapters 9, 26–27, formal spec  
5. System design ← Chapters 10–12  
6. Experimental design ← Chapters 13–15 setup parts  
7. Results ← Chapters 13–16, 65  
8. Discussion and implications ← Chapters 61–62, 73  
9. Conclusion and future work ← Chapters 25, 70  

You can literally outline a thesis from this handbook.

---

## Chapter 83. Appendix H: troubleshooting regeneration failures

**Import errors for evaluate modules.**  
Set `PYTHONPATH=src` or install the package in editable mode if you later add packaging.

**zizmor not found.**  
Field baseline fields may be empty or stale. Install zizmor or keep the committed JSON summaries for reporting.

**Unicode path issues on Windows.**  
Run commands from the repository root and prefer the project venv absolute path.

**DOCX open failure because file is locked.**  
Close Word windows viewing the same output path, then regenerate.

**Numbers changed after policy edit.**  
That is expected. Record a new policy version and update manuscript text; do not silently overwrite historical claims.

---

## Chapter 84. Appendix I: what to send where

**To secretariat for print (Persian short article):**  
`Security_Regressions_GHA_AI_Agents_Manuscript_FA.docx`

**To supervisor who wants full understanding in English:**  
`Project_Guide_EN_0_to_100.docx` (this document)

**To venue-style English paper readers:**  
`Security_Regressions_GHA_AI_Agents_Manuscript.docx`

**To engineers reproducing metrics:**  
`replication/REPRODUCE.md` plus this guide’s Part VI

Sending the wrong artifact to the wrong audience creates avoidable confusion.

---

## Chapter 85. Appendix J: one-page cheat sheet

Problem: workflow edits can weaken security while CI stays green.  
Construct: security regression = before-to-after worsening.  
Method: R01–R15 policy validator over extracted signals.  
Controlled: N=15, validator F1=1.00 (implementation check).  
Field: N=330, 13.9% regressions, validator ~P0.88 R0.93 FPR0.02.  
Baseline: after-only zizmor too noisy for regression labels; diff helps.  
Human: n=63, validator F1~0.91.  
Implication: add diff-aware merge checks for workflow paths.  
Not claimed: definitive proof that all agents are worse than humans.

Print this chapter alone as a pocket card before meetings.

---

## Chapter 86. Appendix K: extended discussion on RQ1

RQ1 asks what types of regressions appear. In practice, answer in two layers:

**Layer A — taxonomy coverage.** We can observe permissions escalations, privileged triggers, pin loss, untrusted Actions, secret/injection patterns, gate removal, self-hosted introduction, and the later R12–R15 classes.

**Layer B — empirical frequency.** In the field pilot, some classes dominate hit counts. Frequency does not equal severity. A rare R03/R04 pattern may still be more operationally dangerous than a common mild pin issue.

A strong oral answer mentions both existence of classes and the need to separate frequency from severity.

---

## Chapter 87. Appendix L: extended discussion on RQ2

RQ2 is socially and scientifically sensitive because audiences hear “AI vs human.” Guardrails:

- controlled fixture tags are synthetic;
- field labels follow mining heuristics;
- cells are unbalanced;
- statistical significance was not reached for the pooled gap in this pilot.

The honest contribution on RQ2 is that the harness can compare strata and that early field evidence is directionally elevated for agents without being conclusive. That is still a real contribution because many talks skip the non-significance.

---

## Chapter 88. Appendix M: extended discussion on RQ3

RQ3 is where the engineering contribution is strongest. The validator matches the regression construct, performs well on controlled fixtures, shows strong predicate-aligned field metrics, and remains competitive on human labels. The baseline contrast teaches why construct validity matters as much as raw recall.

If a committee allows only one RQ to be “fully answered” by the current milestone, RQ3 is the safest candidate, with RQ1 partially answered and RQ2 cautiously framed.

---

## Chapter 89. Appendix N: concrete before/after narratives for three more fixtures

**Pin loss narrative.**  
A third-party Action was locked to a commit SHA. After the edit, the same Action uses a floating tag. Convenience improved; supply-chain assurance declined. Rule R05 speaks.

**Gate removal narrative.**  
A CodeQL job disappears while unit tests remain. The repository still “has CI,” but security assurance shrank. Rule R08 speaks.

**Env injection narrative.**  
Untrusted head ref material is written into `GITHUB_ENV`. Later steps inherit poisoned environment state. Rule R15 speaks.

Use these narratives when an audience’s eyes glaze over at metric tables.

---

## Chapter 90. Appendix O: project vocabulary in one bilingual mini-list

- security regression / پسرفت امنیتی  
- workflow / گردش‌کار  
- policy validator / اعتبارسنج سیاست‌محور  
- after-only scanning / پویش فقط‌بعد  
- false-positive rate / نرخ مثبت کاذب  
- field pilot / پایلوت میدانی  
- controlled benchmark / بنچمارک کنترل‌شده  
- merge gate / دروازهٔ ادغام  

This list helps when switching between the Persian print article and this English handbook.

---

## Chapter 91. Appendix P: integrity rules for future edits

1. Never change gold labels silently.  
2. Never change policy predicates without bumping version notes.  
3. Never report κ without real dual annotators.  
4. Never drop conflicting baseline numbers just because they look worse.  
5. Never mix controlled and field metrics in one sentence without naming the set.

These integrity rules protect you in review.

---

## Chapter 92. Appendix Q: long closing briefing you can paste into email

Subject: Project status briefing — security regressions in GitHub Actions  

Body:  
This project studies security regressions in GitHub Actions workflows after AI-agent-related and comparable edits. A security regression means the after version is less safe than the before version on monitored dimensions, even if builds still pass. We implemented a policy-based before/after validator over fifteen automated rules aligned with OWASP CI/CD themes. On a controlled fifteen-pair suite the validator recovers curated regressions with FPR 0.00 as an implementation check. On a 330-pair field pilot the audited regression rate under policy v3 is 13.9%, and the validator reaches approximately precision 0.88, recall 0.93, and FPR 0.02. An after-only static baseline is poorly aligned with the regression task; a before/after finding-set diff reduces false positives but remains weaker than the policy gate. A human-labeled subset of 63 pairs yields validator F1 around 0.91. The practical implication is to place diff-aware policy checks on workflow-path merge gates alongside residual static scanning. Full details are in the English 0-to-100 project guide and the short manuscripts.

---

## Chapter 93. Appendix R: final mastery self-test

Answer without notes:

1. Define security regression in one sentence.  
2. Give two examples where after-only scanning disagrees with regression labeling.  
3. Name five rule families and what they catch.  
4. State controlled, field, and human headline numbers.  
5. Explain why 39→46 positives happened.  
6. State what is not claimed about AI versus humans.  
7. Name the three main document deliverables and their audiences.  
8. Write the exact controlled and field evaluation commands.  
9. Explain trusted-owner exceptions for R06.  
10. Give one organization rollout plan using the validator.

If you can answer all ten, you have completed the journey from 0 to 100.

---

## Chapter 94. Bridge to the complete engineering dump

The chapters above already teach the science and the story. The remaining parts dump **everything else** that was previously thinner: module-by-module code, pipelines, protocol history, ablation numbers, literature audit, human-pack details, CLI usage, and figure generation. After this section, the guide is intended to be complete for handoff.

---

# Part XI — Module-by-Module Source Code Guide

## Chapter 95. `src/workflow_parse/signals.py`

**Role:** Turn a workflow YAML file into a structured `SignalSet`.

**Important pieces:**

- `ActionRef` dataclass: owner, name, ref, pin flags, optional comment SHA, `effectively_pinned`
- Regexes for secret-echo, injection, curl|bash pipes, and `GITHUB_ENV` injection
- Constants `DANGEROUS_WRITE_SCOPES` and `DANGEROUS_TRIGGERS`
- YAML loading via `ruamel.yaml` for better real-world parsing tolerance
- `extract_signals` / `extract_signals_from_path` entry points

**Why it matters:** Every rule compares signals, not raw text blindly. If signal extraction is wrong, every downstream metric is wrong.

**What “effectively pinned” means here:** either `@ref` is a 40-hex SHA, or a trailing `# <40hex>` comment SHA is present on the `uses:` line.

---

## Chapter 96. `src/policy_validator/validator.py`

**Role:** Load policy YAML, compare before/after `SignalSet`s, emit `Finding` objects.

**Key types:**

- `Finding(rule_id, severity, message, evidence, owasp)`
- `load_rules()` finds `policies/owasp_cicd_rules.yaml`
- `compare_signals(before, after, rules_doc)` implements R01–R15 predicates
- `validate_paths(before, after, rules=None)` is the main API used by evaluation

**Binary prediction rule used in metrics:** any finding whose `rule_id != "PARSE"` ⇒ predicted regression = 1.

**CLI wrapper:** `src/policy_validator/cli.py` and `python -m policy_validator`.

Example:

```text
python -m policy_validator data/sample/r01_permissions_write_all/before/ci.yml data/sample/r01_permissions_write_all/after/ci.yml
```

Optional `--json` emits machine-readable findings.

---

## Chapter 97. `src/baselines/zizmor_baseline.py`

**Role:** Wrap zizmor for two regression operationalizations.

1. **After-only:** findings on after file ⇒ positive
2. **Before/after finding-set diff:** new findings after relative to before ⇒ positive

If the zizmor CLI is unavailable, a proxy path may be used so evaluation still runs; `eval_summary.json` records whether the real CLI was available.

---

## Chapter 98. `src/evaluate/metrics.py` and `run_eval.py`

**`metrics.py`:** binary confusion metrics (precision, recall, F1, FPR, FNR) and AI-vs-human tests (Fisher / chi-square helpers).

**`run_eval.py`:** reads a labels CSV, runs policy validator + baselines on each pair, writes:

- `eval_summary.json`
- markdown tables
- per-row detail artifacts under the chosen `--out` directory

Truth column preference: `gold_has_regression` if present, else `auto_has_regression`.

---

## Chapter 99. `src/evaluate/ablation.py`

**Role:** Re-score the controlled suite with rule-family subsets.

Committed result in `paper/manuscript/tables/ablation.json` (N=15):

| Family | Precision | Recall | F1 | FPR |
|--------|----------:|-------:|---:|----:|
| full | 1.00 | 1.00 | 1.00 | 0.00 |
| permissions_only | 1.00 | 0.30 | 0.46 | 0.00 |
| pinning_only | 1.00 | 0.20 | 0.33 | 0.00 |
| ppe_only | 1.00 | 0.20 | 0.33 | 0.00 |
| controls_only | 1.00 | 0.10 | 0.18 | 0.00 |

**Interpretation:** each family alone is precise but incomplete; the full pack is required for high recall.

Command:

```powershell
python -m evaluate.ablation --labels annotations/labels_sample.csv --out paper/manuscript/tables/ablation.json
```

---

## Chapter 100. `src/figures/plot_results.py`

**Role:** Generate manuscript figures from evaluation outputs (F1 comparison, rule counts, agent rates).

Outputs typically land under `paper/manuscript/figures/`:

- `method_f1.png`
- `rule_counts.png`
- `agent_rates.png`

Command (as used in full local pipeline):

```powershell
python -m figures.plot_results
```

---

## Chapter 101. `src/labeling/prelabel.py`

**Role:** Help create initial label CSVs from indexes / pairs. Useful for bootstrapping, not a substitute for gold definition discipline.

---

## Chapter 102. `src/github_fetch/fetch_pairs.py`

**Role:** Fetch before/after workflow file contents for PR/path pairs from GitHub when materializing field data.

This is where network credentials, rate limits, and public-only constraints matter. Failures here are operational, not conceptual.

---

## Chapter 103. `src/aidev_extract/`

**Role:** Pilot extraction helpers over AIDev-derived indexes.

`python -m aidev_extract.pilot --limit 200 --out data/interim/pilot_index.json` is the historical local pilot entry used in `run_full_pipeline.ps1`.

The merged reported field set in the manuscript freeze is the **N=330** labeled corpus in `annotations/labels_aidev.csv`, which may be broader than an early `--limit 200` pilot index.

---

# Part XII — Full Pipelines, Scripts, and Shell Entry Points

## Chapter 104. `scripts/run_full_pipeline.ps1` / `.sh`

Local full pipeline sketch:

1. `pytest -q`
2. `python -m aidev_extract.pilot ...`
3. `python -m labeling.prelabel ...`
4. `python -m evaluate.run_eval ...`
5. `python -m figures.plot_results`
6. `python -m evaluate.ablation ...`

This is the “press one script” path for a local smoke/full cycle. For manuscript-faithful field numbers, prefer regenerating from `annotations/labels_aidev.csv` as in `replication/REPRODUCE.md`.

---

## Chapter 105. `scripts/run_pilot.ps1` / `.sh`

Narrower pilot runner for quicker iteration than the full pipeline.

---

## Chapter 106. Field construction scripts (detailed)

**`stream_aidev_workflows.py`**  
Stream / filter AIDev rows touching workflow paths; useful when full dumps are too large.

**`sample_agents_via_github.py`**  
Supplement sparse agent cells via GitHub sampling strategies.

**`sample_human_controls.py`**  
Build repo-matched human control pairs.

**`try_aidev_download.py`**  
Probe / download AIDev materials with defensive checks.

**`merge_field_eval.py`**  
Merge partial evaluation outputs when field collection happened in batches.

**`field_gold_audit.py`**  
Recompute predicate-aligned gold from before/after paths under policy v3 formal rules. This is the authoritative field-gold builder for the freeze.

**`gold_version_delta.py`**  
Replay interim/v2/v3 definitions on the same N=330 paths and write `gold_v_delta.md/.json`.

**`audit_gold_from_auto.py`**  
Helper audits comparing automatic labels / overrides.

**`analyze_field_fn.py`**  
Inspect false negatives for qualitative diagnosis.

---

## Chapter 107. Human-round scripts (detailed)

**`sample_human_annotation_set.py`**  
Creates the stratified 80-pair pack under `annotations/human_round/`.

**`compute_iaa.py`**  
Computes agreement / κ when both A and B are filled.

**`eval_human_gold.py`**  
Evaluates validator against `gold_human_adjudicated.csv`.

Current freeze reality:

- A filled for 63 pairs
- B not completed
- κ not reported
- human-gold metrics exist for n=63

---

## Chapter 108. Document build scripts

- `md_to_docx.py` → English short manuscript DOCX
- `main_fa_to_docx.py` → Persian print DOCX (RTL-aware)
- `guide_fa_to_docx.py` → older Persian educational guide
- `briefing_fa_to_docx.py` → supervisor briefing export
- `build_project_guide_en.py` → this complete English handbook
- `qa_secretariat_fa.py` → QA checks for Persian print readiness

---

# Part XIII — Study Protocol and Progress History

## Chapter 109. Study protocol summary (`paper/study_protocol.md`)

**Confirmatory analyses:**

1. Regression prevalence and class distribution (RQ1)
2. AI vs human association test (RQ2)
3. Detector metrics vs gold for policy and zizmor baselines (RQ3)

**Secondary/exploratory:** per-agent breakdown, ablations, runtime, qualitative cases, gold-definition sensitivity.

**Inclusion:** public PRs modifying workflow YAML; parseable before/after; agent or matched human label.

**Exclusion:** whitespace-only diffs, non-workflow paths, private repos.

**Executed pilot sample:** N=330 as reported.

**Future scale-up (not claimed done):** ≥200 well-matched humans; enlarge Cursor/Jules/Devin; optional full-corpus extract.

**Ethics:** public data only; redact secrets; no invasive interaction with third-party production systems beyond public reads.

**Multiple testing:** confirmatory family limited; other tests exploratory.

---

## Chapter 110. Progress log highlights (`paper/progress.md`)

Major milestones recorded in-repo:

- Controlled suite + validator + zizmor baselines working
- Field pilot materialized and evaluated
- Policy formalization to v3 and gold delta documentation (≈39–40 → 46)
- Softened novelty / overclaim language
- Reproduction docs and data card
- Human annotation pack infrastructure
- Delivery manuscripts (English short + Persian print)
- This complete English handbook

Delivery design: single-annotator human evidence (n=63). Do not fabricate κ.

---

# Part XIV — Literature and Reference Audit

## Chapter 111. Source-by-source audit (`paper/literature/reference_audit.md`)

| Cite | Topic | Completeness | Notes |
|------|-------|--------------|-------|
| [1] AIDev | dataset / agents on GitHub | Good | cite paper + dataset URL |
| [2] Agents touch CI/CD | MSR challenge | Medium | verify final author list |
| [3] AI bot workflow reliability | MSR proceedings | Medium | author names incomplete in bib |
| [4] zizmor docs | web | Good | |
| [5] Microsoft agent-in-CI case | web | Good | runtime threat model (complementary) |
| [6] CSA prompt injection | web | Medium | URL/permalink may need confirmation |
| [7] OWASP CI/CD Top 10 | web | Good | taxonomy mapping basis |
| [8] GitHub hardening | web | Good | |
| [9] OWASP GHA cheat sheet | web | Good | |
| [10] pull_request_target guidance | web | Good | |
| [11] JAIAI cyber prediction paper | journal | Good | venue fit, topical adjacency |
| [12] JAIAI anomaly survey | journal | Weak | missing authors in bib |

**Novelty stance used in manuscripts:** likely/well-motivated gap — not a “world-first” claim without a documented systematic review protocol.

Remaining bibliographic chores: fill missing authors for [3]/[12], confirm CSA URL, replace `[URL_TO_BE_FILLED]` when public repo exists.

---

## Chapter 112. Related literature folders

Also browse:

- `paper/literature/search_log.md`
- `paper/literature/related_work_table.md`
- `paper/literature/data_adequacy.md`
- `paper/literature/field_study_status.md`

These are working notes supporting the manuscript, not alternate ground-truth metric stores.

---

# Part XV — Human Pack Complete Dump

## Chapter 113. Files inside `annotations/human_round/`

- `ANNOTATION_GUIDE_FA.md` — labeling instructions
- `README.md` — process steps
- `annotator_A.csv` — filled for 63 pairs in current freeze
- `annotator_B.csv` — template / incomplete
- `pairs_manifest.csv` — pack membership
- `predicate_gold_key.csv` — analysis-only key (**annotators must not open**)
- `gold_human_adjudicated.csv` — provisional gold from filled A rows (`source=single_annotator_A`)

---

## Chapter 114. Exact human-pack process

1. Read the annotation guide.
2. Independently fill A and B with `has_regression ∈ {0,1}`.
3. Run `compute_iaa.py`.
4. Adjudicate disagreements into final gold.
5. Run `eval_human_gold.py`.
6. Update manuscript numbers.

**Current delivery scope:** single annotator on 63 pairs; 17 missing YAML excluded; no κ.

Human-gold metrics:

- Precision 0.87
- Recall 0.94
- F1 0.91
- FPR 0.19
- N 63

---

# Part XVI — Controlled Suite Inventory and CLI Recipes

## Chapter 115. How to run the validator on any fixture

```powershell
$env:PYTHONPATH = "src"
python -m policy_validator `
  data/sample/<fixture>/before/ci.yml `
  data/sample/<fixture>/after/ci.yml
```

Useful fixtures include permissions escalation, PR-target, pin loss, CodeQL removal, contents:write, curl|bash, issue_comment, and github_env examples under `data/sample/`.

---

## Chapter 116. Controlled confusion numbers (exact)

From `tables/controlled/eval_summary.json`:

- Policy: TP10 FP0 TN5 FN0
- zizmor after-only: TP10 FP5 TN0 FN0
- zizmor before/after-diff: TP5 FP2 TN3 FN5
- Mean validator seconds ≈ 0.012 on this suite
- Rule hits observed on suite include R01–R08, R10, R11 (fixture coverage dependent)

---

## Chapter 117. Field confusion numbers (exact)

From `tables/field/eval_summary.json`:

- Policy: TP43 FP6 TN278 FN3
- After-only: TP44 FP258 TN26 FN2
- Diff: TP34 FP50 TN234 FN12
- Mean seconds ≈ 0.056
- Rule_counts include notable R06 and R12 mass, among others
- AI vs human chi-square p ≈ 0.0845

---

# Part XVII — Policies, Overrides, and Config Knobs

## Chapter 118. Policy files

- `policies/owasp_cicd_rules.yaml` — executable rule pack v3.0.0
- `policies/rule_formal_spec.md` — formal predicates and exceptions
- `policies/rule_owasp_map.md` — mapping notes

Tunable concepts:

- trusted Action owners for R06
- dangerous write scopes for R12
- dangerous interactive triggers for R14
- enable/disable individual rules

---

## Chapter 119. `annotations/gold_overrides.json`

Optional override mechanism for exceptional gold decisions. Any override should be documented; silent overrides destroy auditability.

---

# Part XVIII — Deliverable Map (nothing left ambiguous)

## Chapter 120. Every major output and where it lives

**Science short form (EN):** `paper/manuscript/main.md` + `Security_Regressions_GHA_AI_Agents_Manuscript.docx`  
**Print short form (FA):** `paper/manuscript/main_fa.md` + `Security_Regressions_GHA_AI_Agents_Manuscript_FA.docx`  
**Complete handbook (EN):** this file + `Project_Guide_EN_0_to_100.docx`  
**Metrics:** `tables/controlled/*`, `tables/field/*`, `tables/ablation.json`  
**Labels:** `annotations/labels_sample.csv`, `annotations/labels_aidev.csv`, `annotations/human_round/*`  
**Reproduce:** `replication/REPRODUCE.md`, `replication/DATA_CARD.md`  
**Protocol/progress:** `paper/study_protocol.md`, `paper/progress.md`  
**Literature notes:** `paper/literature/*`

---

## Chapter 121. Completeness declaration

This handbook now includes:

1. conceptual 0–100 explanation  
2. full rule taxonomy with examples  
3. architecture and baselines  
4. controlled / field / human results with exact key numbers  
5. repository map and reproduction commands  
6. presentation and defense material  
7. module-by-module source guide  
8. pipeline and script catalog  
9. study protocol and progress history  
10. literature/reference audit  
11. human-pack file dump and current status  
12. ablation numbers and figure generation entry points  
13. CLI recipes and confusion matrices  
14. policy/config knobs and deliverable map  

If a future file is added to the repo, append a short note here rather than letting the handbook drift silently.

## Chapter 122. Response to external review notes (do not skip)

Another review of this handbook asked for a **detailed** expansion that does **not** merely lengthen paragraphs, but restores material that is almost absent from the short manuscript. This part answers that request directly and also keeps two ambiguities honest and explicit.

Restored / expanded below:

1. separate discussion of all fifteen rules (pointer + field hit table);
2. why before/after comparison is the right construct;
3. signal extraction and exact metric formulas;
4. ablation over rule families with numbers;
5. gold-label evolution into policy v3;
6. explicit handling of rule-count provenance;
7. explicit handling of real zizmor CLI versus proxy path.

---

# Part XIX — Restored Technical Depth (Short-Paper Gaps Closed)

## Chapter 123. Why before/after comparison (restored rationale)

The short manuscript compresses this argument. The long guide must state it fully.

**Security regression is a property of a change.**  
A snapshot scanner answers: “What residual risks exist in the landing file?”  
A before/after policy answers: “Did this pull request make monitored security posture worse?”

These diverge in both directions:

- **Old risk, unchanged:** after-only tools may still alarm; regression label should stay 0.
- **Control removed:** after file may look simpler and attract fewer snapshot findings; regression label should be 1 (for example R08).
- **Pin lost / scope widened / privileged trigger added:** both may alarm, but only the diff construct names the worsening event as the unit of analysis.

Therefore the project does **not** claim after-only scanners are useless. It claims they are the wrong sole oracle for merge-gate decisions about worsenings. Diff-aware policy is complementary.

---

## Chapter 124. All fifteen rules — keep them separate (not one blurred list)

The short paper lists the taxonomy briefly. The detailed handbook must keep each rule distinct. Chapter 9 already defines R01–R15 one-by-one. Use that chapter as the canonical prose. This chapter adds the **operational reminder**:

| ID | One-line worsening |
|----|--------------------|
| R01 | Escalation to `write-all` |
| R02 | Explicit least-privilege restriction removed |
| R03 | `pull_request_target` newly introduced |
| R04 | Privileged checkout of untrusted PR head |
| R05 | Effective SHA pin lost on an existing Action key |
| R06 | New untrusted unpinned third-party Action identity |
| R07 | New secret-exposure script patterns |
| R08 | Security gate/job removed |
| R09 | `workflow_run` newly introduced |
| R10 | New script-injection patterns from untrusted contexts |
| R11 | Self-hosted runner newly introduced |
| R12 | Dangerous write scopes newly raised |
| R13 | Remote pipe-to-shell pattern newly added |
| R14 | Dangerous interactive triggers newly added |
| R15 | Untrusted writes into `GITHUB_ENV` / `GITHUB_PATH` |

R99 remains manual residual only.

Do not collapse these into “permissions and other stuff” when explaining the detailed version.

---

## Chapter 125. Signal extraction details (restored)

`workflow_parse.signals` builds a `SignalSet` used by every rule. Detailed extraction includes:

**Triggers.** Normalized event names from `on:`.

**Permissions.** Raw maps/strings, score heuristics, write-all detection, and `write_scopes` union across workflow/job levels for dangerous scopes.

**Actions.** Parsed `uses:` lines into `(owner, name, ref)` with pin detection:
- `@ref` is 40-hex SHA, or
- trailing `# <40hex>` comment SHA on the same line  
⇒ `effectively_pinned = true`.

**Scripts.** Concatenate `run:` bodies and precompute counters:
- `secret_echo_hits`
- `injection_hits`
- `pipe_shell_hits`
- `github_env_injection_hits`

**Security controls.** Presence of known security Actions/jobs (for removal detection).

**Runners.** Self-hosted markers.

Rules never invent worsenings from thin air; they compare these extracted signals before versus after under formal predicates in policy v3.

---

## Chapter 126. How metrics are calculated (exact formulas)

Let a labeled set have gold binary labels \(y_i \in \{0,1\}\) and detector predictions \(\hat y_i \in \{0,1\}\).

Confusion counts:

- TP = \(\sum 1[y=1 \land \hat y=1]\)
- FP = \(\sum 1[y=0 \land \hat y=1]\)
- TN = \(\sum 1[y=0 \land \hat y=0]\)
- FN = \(\sum 1[y=1 \land \hat y=0]\)

Then:

- Precision = TP / (TP + FP) (undefined/handled if denominator 0)
- Recall = TP / (TP + FN)
- F1 = 2 · Precision · Recall / (Precision + Recall)
- FPR = FP / (FP + TN)
- FNR = FN / (FN + TP)

**Policy prediction rule in this repo:** \(\hat y = 1\) iff there exists a finding with `rule_id != "PARSE"`.

**zizmor after-only prediction:** any finding on the after file ⇒ 1.  
**zizmor diff prediction:** any finding present after but not before (finding-set difference) ⇒ 1.

AI-vs-human tests use stratum rates and Fisher/chi-square helpers in `evaluate.metrics`.

All manuscript tables should regenerate from these definitions via `python -m evaluate.run_eval`, not from hand-edited markdown.

---

## Chapter 127. Ablation over rule families (restored numbers)

Short papers often omit ablation. Detailed handbook must keep it.

Controlled suite (N=15), from `paper/manuscript/tables/ablation.json`:

| Family | P | R | F1 | FPR |
|--------|--:|--:|---:|----:|
| full | 1.00 | 1.00 | 1.00 | 0.00 |
| permissions_only (R01–R02 family setting) | 1.00 | 0.30 | 0.46 | 0.00 |
| pinning_only | 1.00 | 0.20 | 0.33 | 0.00 |
| ppe_only | 1.00 | 0.20 | 0.33 | 0.00 |
| controls_only | 1.00 | 0.10 | 0.18 | 0.00 |

**Meaning:** every subset stays precise on this suite, but recall collapses. The full pack is necessary for coverage. Ablation supports the claim that the taxonomy is not redundant window dressing.

Regenerate with:

```powershell
python -m evaluate.ablation --labels annotations/labels_sample.csv --out paper/manuscript/tables/ablation.json
```

---

## Chapter 128. Gold-label evolution into policy v3 (restored trend)

Short text mentions “46 not 39.” Detailed text must explain the trend on the **same N=330 paths**.

From `paper/manuscript/tables/field/gold_v_delta.md` (reconstructed interim/v2; current v3 CSV):

| Version | Gold positives | Rate | Notes |
|---------|---------------:|-----:|-------|
| Interim (reconstructed) | 40 | 0.121 | drafts often cited ≈39 (11.8%) |
| v2 (reconstructed) | 33 | 0.100 | trusted docker + formal pins; still no R12–R15 |
| **v3 (current)** | **46** | **0.139** | +R12–R15 + formal signals |

Net story versus interim:

- newly positive: **12** (chiefly R12, plus R13/R15)
- flipped to negative: **6** (mostly former R06 on `docker/*` after trusted-owner realignment)

This is a **definition revision**, not silent resampling. Always say that sentence when numbers are challenged.

---

## Chapter 129. Ambiguity A — per-rule occurrence counts (kept explicit)

Review note: “exact per-rule occurrence counts were not in the guide.”

**Clarification now included:**

1. The **source of truth** for detector rule-hit counts on the field freeze is:

`paper/manuscript/tables/field/eval_summary.json` → key `rule_counts`

2. Those counts are **validator finding tallies over the evaluated pairs**, not a separate hand census of gold-only rule tags, and not a claim that every gold positive is exclusively one rule.

3. Frozen field `rule_counts` at the time this handbook section was written:

| Rule | Count in field eval_summary |
|------|----------------------------:|
| R06 | 37 |
| R12 | 17 |
| R07 | 5 |
| R05 | 3 |
| R10 | 2 |
| R15 | 2 |
| R09 | 2 |
| R13 | 2 |
| R14 | 2 |
| R02 | 1 |
| R03 | 1 |

Rules absent from this dict in that JSON snapshot simply had zero counted hits in that evaluation pass (they may still exist in fixtures/policy).

4. If you regenerate evaluation, **re-read the JSON**. Do not treat the table above as eternally frozen if local outputs changed.

5. Gold-delta “newly positive” rule tags (a different table) live in `gold_v_delta.md` and must not be confused with `rule_counts`.

---

## Chapter 130. Ambiguity B — real zizmor CLI vs proxy path (kept explicit)

Review note: whether the run used real zizmor or a proxy must be confirmed from evaluation output.

**How to confirm:**

Open `paper/manuscript/tables/field/eval_summary.json` (and the controlled twin) and read:

`zizmor_cli_available`

**Frozen field value in the current project tree:** `true`

That means the field metrics above were produced with the real zizmor CLI path available for after-only and before/after-diff baselines.

**If the flag is false after a future run:** baseline numbers may come from the proxy fallback in `baselines/zizmor_baseline.py`. In that case, say so explicitly in any report; do not silently present proxy numbers as CLI numbers.

**Always re-check the flag after regeneration.** This handbook records the freeze value, but the JSON is authoritative.

Controlled summary also carries the same key; inspect both when defending baselines.

---

## Chapter 131. Short manuscript vs detailed handbook — what was restored

| Topic | Short paper tendency | Detailed handbook |
|-------|----------------------|-------------------|
| 15 rules | compressed list | separate definitions + one-line table + Chapter 9 |
| before/after why | brief framing | full construct argument (Ch. 123) |
| signals/metrics | mostly implicit | extraction + formulas (Ch. 125–126) |
| ablation | often omitted | full table (Ch. 127) |
| gold 39→46 | short clause | version trend table (Ch. 128) |
| rule hit counts | usually absent | JSON-backed table + provenance warning (Ch. 129) |
| zizmor CLI/proxy | easy to blur | explicit flag + verification (Ch. 130) |

---

## Chapter 132. End matter

This handbook is now the detailed English 0-to-100 project document: conceptual, operational, and engineering-complete, with the short-paper gaps restored and the two review ambiguities stated explicitly rather than hidden.

*End of complete English project guide.*
