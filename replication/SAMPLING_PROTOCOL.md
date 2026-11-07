# Field sampling protocol (N=330)

## Goal

Assemble a reproducible pilot of before/after GitHub Actions workflow pairs for policy-v3 regression measurement, with agent-related edits and a human-control stratum.

## Calendar / retrieval window

- Pilot assembly and materialization: **October 2026** (repository literature stamps: search log from 2026-10-21; field status consistency pass 2026-10-24).
- Exact per-script wall-clock start/end times: record in the author checklist if the journal requires hour-level provenance; the frozen pair set is the 330-row manifest below (content-addressed).

## Inclusion

- Public pull request (or equivalent public commit pair) touching `.github/workflows/*.{yml,yaml}`
- Both before and after YAML materializable and parseable (raw fallback allowed)
- Agent stratum: AIDev-linked / GitHub-sampled agent footprints
- Human stratum: same-repo human workflow edits used as controls

## Exclusion

- Whitespace-only or non-workflow path changes
- Private repositories
- Unmaterializable YAML after recovery attempts

## Retrieval process

1. **Codex / AIDev stream** (`scripts/stream_aidev_workflows.py`): stream AIDev `pr_commit_details`, keep workflow paths, enrich with PR/repo tables (avoids full ~12GB download).
2. **Other agents** (`scripts/sample_agents_via_github.py`): probe AIDev PR rows via GitHub Files API; keep PRs that touch workflow YAML.
3. **Human controls** (`scripts/sample_human_controls.py`): from the same repos as agent hits, sample non-bot commits under `.github/workflows`.
4. **Merge / gold** (`scripts/merge_field_eval.py`, `scripts/field_gold_audit.py`): assemble labels; audit gold under policy v3.

## Repository matching

Human controls are **repo-matched** to the agent index: repositories are harvested from the agent field index (`--from-index`), then human workflow commits are taken from those repos (bot logins excluded).

## Deduplication

- Stream path: unique key `(pr_id, workflow_filename)`.
- Human controls: unique key `(repo, filepath)` via `seen_files`.
- Merge: unique `pair_id` (skip duplicates when concatenating strata).

## Executed strata (frozen)

| Stratum | N | Source tag |
|---------|--:|------------|
| OpenAI_Codex | 200 | `aidev_stream` |
| Claude_Code | 20 | `aidev_github_sample` |
| Copilot | 20 | `aidev_github_sample` |
| Cursor | 6 | `aidev_github_sample` |
| Devin | 4 | `aidev_github_sample` |
| human | 80 | `human_repo_control` |
| **Total** | **330** | — |

## Full pair manifest

- CSV: `annotations/field_pairs_manifest_330.csv`
- Meta + SHA-256: `annotations/field_pairs_manifest_330.meta.json`  
  (`sha256=d1c7339c5877ddf90ef6184f82cb4c68ec5cf936dadff7aafdcda8dfd1640f11`)
- Authoritative gold: `annotations/labels_aidev.csv` (policy-v3 audit; **46/330** positives)

## Human check (this delivery)

- Pack: `annotations/human_round/` (80 prepared; 63 labeled by annotator A)
- Annotator B / dual-rater κ: **out of scope**
- Independent human evaluation = single-annotator judgment vs validator
