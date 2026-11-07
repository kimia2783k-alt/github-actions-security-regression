# Qualitative Case Studies (Discussion seeds)

These examples illustrate regression classes. Field PRs from AIDev should replace synthetic IDs before camera-ready when available.

## Case A — Permissions escalation (R01/R02)

**Pair:** `sample-r01_permissions_write_all`  
**Change:** `permissions: contents: read` → `permissions: write-all`  
**Why it matters:** Broad write tokens amplify impact of any code execution in the workflow (supply-chain or PPE).  
**Validator:** Flags R01 and R02.  
**Baseline proxy:** Also flags broad permissions.

## Case B — Poisoned pipeline setup (R03/R04)

**Pair:** `sample-r03_pr_target`  
**Change:** `pull_request` → `pull_request_target` plus checkout of PR head SHA.  
**Why it matters:** Classic “pwn request” pattern; privileged context with untrusted code.  
**Validator:** Critical findings R03+R04.  
**Baseline proxy:** Detects trigger introduction.

## Case C — Security gate removed (R08)

**Pair:** `sample-r08_removed_security_job`  
**Change:** Entire `codeql` job deleted while tests remain.  
**Why it matters:** Functional CI may still pass; security signal disappears.  
**Validator:** R08.  
**Baseline proxy:** Often misses *removal* regressions if after-file alone looks “simple/clean.”

## Case D — Benign hardening (negative)

**Pair:** `sample-safe_add_codeql` / `sample-human_safe_pin`  
**Change:** Add CodeQL job or pin checkout to SHA.  
**Expected:** No regression.  
**Validator:** PASS.

## Industry motivation (non-AIDev)

Microsoft (2026) and CSA (2026) document risks when AI agents *run inside* Actions with secrets. Our cases target the complementary risk: agents *editing* workflow YAML and silently weakening controls even when builds stay green.
