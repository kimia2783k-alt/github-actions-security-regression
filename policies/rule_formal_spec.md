# Formal Rule Specification (R01–R15)

Policy version: **3.0.0** (`policies/owasp_cicd_rules.yaml`)

## Shared contract

Let \(W_b\) and \(W_a\) be before/after workflow documents for the same path.
Let \(S(\cdot)\) be the `SignalSet` extracted by `workflow_parse.signals`.

A pair is a **security regression** iff \(\exists i \in \{01..15\}\) such that
\(\mathrm{Worse}_i(S(W_b), S(W_a))\) holds.

Unchanged pre-existing insecurity is **not** a regression.

### Action identity and pinning

- Action key: \(K = (\mathrm{owner}, \mathrm{name})\) (case-normalized lower).
- Action identity (for “new action”): \(I = (\mathrm{owner}, \mathrm{name}, \mathrm{ref})\).
- **Effectively pinned** iff the `@ref` itself is a 40-hex commit SHA.
  A trailing `# <40-hex>` comment next to a floating tag/branch (e.g.
  `uses: actions/checkout@v4 # <sha>`) is **not** an effective pin: the
  workflow still resolves `@v4`. Comment SHAs may be recorded for diagnostics
  (`comment_sha`) but do not satisfy `effectively_pinned`.
- R05 uses key \(K\) (same action lost pin).
- R06 uses identity \(I\) (entirely new unpinned third-party). Changing only
  ref SHA→tag on the same \(K\) is R05, not R06.

### Trusted owners (R06 exception)

See `trusted_action_owners` in the YAML policy. Local `./` actions are exempt.

### Dangerous write scopes (R12)

Default set \(D\): `contents`, `id-token`, `actions`, `packages`, `security-events`,
`deployments`, `environments`, `attestations` (overridable via `dangerous_write_scopes`).

\(S.write\_scopes\) = union of workflow- and job-level scopes with value `write`,
or all of \(D\) when permissions string is `write-all`.

### Dangerous interactive triggers (R14)

Default: `issue_comment`, `discussion_comment`, `pull_request_review_comment`
(overridable via `dangerous_triggers`).

### Script hit counters

Precomputed on `run_scripts`: `secret_echo_hits`, `injection_hits`,
`pipe_shell_hits`, `github_env_injection_hits`.

---

## R01 — permissions_escalated_to_write_all

1. **Intent:** Detect escalation to broad write tokens.
2. **Inputs:** `permissions_raw`, `permissions_score` (workflow- and job-level max).
3. **Predicates:**
   - \(P_b\): not `write-all(before)` (or score may be moderate).
   - \(P_a\): `write-all(after)` or high score.
   - \(\mathrm{Worse}\): `(write-all(after) ∧ ¬write-all(before)) ∨ (score_a ≥ score_b + 30 ∧ score_a ≥ 80)`.
4. **Exceptions:** none.
5. **Minimal example:** `data/sample/r01_permissions_write_all`
6. **Non-regression:** `write-all` already present (`data/sample/no_regression_already_write_all`).
7. **Field blind spots:** job-only escalations without top-level key (covered via score); exotic permission maps.

## R02 — permissions_restriction_removed

1. **Intent:** Detect removal of explicit least-privilege maps.
2. **Inputs:** `permissions_raw`.
3. **Predicates:**
   - Restriction = non-empty permissions dict **or** string `read-all`.
   - \(\mathrm{Worse}\): restriction(before) ∧ ¬restriction(after).
4. **Exceptions:** none.
5. **Example:** `data/sample/r02_permissions_removed`
6. **Non-regression:** never had an explicit restriction.
7. **Blind spots:** replacement of a tight map with a looser non-empty map (not currently scored as R02; may surface under R01 score jump).

## R03 — pull_request_target_introduced

1. **Intent:** New PPE-capable trigger.
2. **Inputs:** `triggers`.
3. **Worse:** `pull_request_target ∈ after` ∧ `∉ before`.
4. **Exceptions:** none.
5. **Example:** `data/sample/r03_pr_target`
6. **Non-regression:** trigger already present.
7. **Blind spots:** nested `on:` forms already normalized by `_normalize_triggers`.

## R04 — privileged_pr_checkout

1. **Intent:** Classic pwn-request: checkout PR head under privileged trigger.
2. **Inputs:** `privileged_checkout`, `triggers`.
3. **Worse:** `privileged_checkout(after)` ∧ ¬`privileged_checkout(before)`.
4. **Exceptions:** none.
5. **Example:** often co-fires with R03 in `data/sample/r03_pr_target`.
6. **Non-regression:** privileged checkout already present.
7. **Blind spots:** indirect checkout actions not named `*checkout*`.

## R05 — action_unpinned_from_sha

1. **Intent:** Loss of commit pin on an existing action.
2. **Inputs:** `actions` (with `effectively_pinned`).
3. **Worse:** ∃ key \(K\): effectively_pinned(before[\(K\)]) ∧ ¬effectively_pinned(after[\(K\)]).
4. **Exceptions:** none (trusted owners still monitored for pin loss).
5. **Examples:** `data/sample/r05_unpinned_action`, `data/sample/r05_comment_pin_lost`.
6. **Non-regression:** new floating action with no prior pin → R06 candidate, not R05.
7. **Blind spots (historical):** comment-only SHA stripped by YAML loaders; multi-job same action with mixed pins (last/first occurrence). Implementation keeps the **most pinned** before instance and flags if after has any unpinned instance for that key.

## R06 — new_unpinned_third_party_action

1. **Intent:** Introduce a new third-party dependency without SHA pin.
2. **Inputs:** `actions`, `trusted_action_owners`.
3. **Worse:** ∃ after action \(A\) with identity \(I\) absent from before, owner not trusted/local, ¬effectively_pinned(\(A\)).
4. **Exceptions:** `trusted_action_owners`; `./` local.
5. **Example:** `data/sample/r06_new_unpinned_third_party`
6. **Non-regression:** new trusted action; new third-party with SHA pin (`data/sample/safe_new_pinned_action`).
7. **Blind spots:** owner typosquatting of trusted names; docker:// refs (treated as unknown owner).

## R07 — secret_exposure_pattern

1. **Intent:** New echo/print of secrets in `run` scripts.
2. **Inputs:** `run_scripts`, `SECRET_ECHO_RE`.
3. **Worse:** match_count(after) > match_count(before).
4. **Exceptions:** none.
5. **Example:** `data/sample/r07_secret_echo`
6. **Non-regression:** pattern already present unchanged.
7. **Blind spots:** obfuscated dumps; env: blocks without echo.

## R08 — security_job_or_step_removed

1. **Intent:** Removal of security gates (CodeQL, scanners, …).
2. **Inputs:** `security_step_keys` vs `security_action_keywords`.
3. **Worse:** \(K_b \setminus K_a \neq \emptyset\).
4. **Exceptions:** none.
5. **Example:** `data/sample/r08_removed_security_job`
6. **Non-regression:** adding scanners (`data/sample/safe_add_codeql`).
7. **Blind spots:** renamed jobs that still run the same scanner; custom scripts without keywords.

## R09 — workflow_run_introduced

1. **Intent:** New privileged follow-on trigger.
2. **Inputs:** `triggers`.
3. **Worse:** `workflow_run ∈ after` ∧ `∉ before`.
4. **Exceptions:** none.
5. **Example:** `data/sample/r09_workflow_run`
6. **Non-regression:** already present.
7. **Blind spots:** none major.

## R10 — script_injection_risk_added

1. **Intent:** New untrusted `github.event.*` interpolation into `run`.
2. **Inputs:** `run_scripts`, `INJECTION_RE`.
3. **Worse:** match_count(after) > match_count(before).
4. **Exceptions:** none.
5. **Example:** `data/sample/r10_script_injection`
6. **Non-regression:** pattern already present.
7. **Blind spots:** `env:` indirection then shell expansion; contexts outside the regex.

## R11 — self_hosted_runner_added

1. **Intent:** Introduce self-hosted runners.
2. **Inputs:** `has_self_hosted`.
3. **Worse:** after ∧ ¬before.
4. **Exceptions:** none.
5. **Example:** `data/sample/r11_self_hosted`
6. **Non-regression:** already self-hosted.
7. **Blind spots:** matrix/`runs-on` expressions that resolve at runtime.

## R12 — dangerous_permission_scope_escalated

1. **Intent:** Detect fine-grained high-impact token write grants (not only `write-all`).
2. **Inputs:** `write_scopes`, `dangerous_write_scopes`.
3. **Worse:** \((S_a \cap D) \setminus (S_b \cap D) \neq \emptyset\), unless the change is a newly introduced blanket `write-all` (then R01 only).
4. **Exceptions:** defer to R01 when `write-all` is newly introduced.
5. **Example:** `data/sample/r12_contents_write`
6. **Non-regression:** scopes already write; read→unchanged.
7. **Blind spots:** reusable-workflow inherited permissions not in local YAML.

## R13 — remote_shell_pipe_added

1. **Intent:** Detect new `curl|bash` / `wget|sh` / PowerShell IEX remote execution.
2. **Inputs:** `pipe_shell_hits`.
3. **Worse:** hits(after) > hits(before).
4. **Exceptions:** none.
5. **Example:** `data/sample/r13_curl_bash`
6. **Non-regression:** pattern already present.
7. **Blind spots:** multi-line pipes split across steps; encoded payloads.

## R14 — dangerous_interactive_trigger_introduced

1. **Intent:** New interactive/PPE-adjacent triggers beyond `pull_request_target`.
2. **Inputs:** `triggers`, `dangerous_triggers`.
3. **Worse:** new intersection with dangerous trigger set.
4. **Exceptions:** none.
5. **Example:** `data/sample/r14_issue_comment`
6. **Non-regression:** trigger already present.
7. **Blind spots:** `workflow_call` indirection.

## R15 — github_env_injection_risk_added

1. **Intent:** Untrusted context written into `GITHUB_ENV` / `GITHUB_PATH`.
2. **Inputs:** `github_env_injection_hits`.
3. **Worse:** hits(after) > hits(before).
4. **Exceptions:** none.
5. **Example:** `data/sample/r15_github_env`
6. **Non-regression:** only trusted literals written to env files.
7. **Blind spots:** intermediate env vars then appended.

## R99 — other (manual)

Not automated. Reserved for annotator residuals (formerly called R12 in early drafts).
