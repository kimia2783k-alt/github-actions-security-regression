# Data Adequacy Report (Pilot)

**Date:** 2026-10-24

## Decision: Conditional Go (pilot executed)

| Corpus | Status | N pairs | Use in paper |
|--------|--------|---------|--------------|
| Controlled synthetic benchmark (`data/sample`) | Ready | 15+ before/after pairs covering R01–R15 + negatives | Primary controlled evaluation |
| AIDev field pilot | **Executed** via streaming + GitHub API (no full 12GB download) | **330** (Codex 200 + other agents 50 + human 80) | Section 6.6 pilot results (policy v3 gold = 46/330) |
| Future scale-up | Not done | Target ≥200 well-matched human + larger sparse agent cells | Camera-ready epidemiology |

## Synthetic corpus composition (current)

- Positive regressions: permissions escalation/removal, `pull_request_target`+privileged checkout, unpinning, secret echo, security job removal, script injection, self-hosted, new unpinned third-party
- Negatives / non-regressions: harmless echo change, add CodeQL, add pinned security action, pre-existing `write-all` unchanged, human safe pin-down

## AIDev scale-up procedure (for author)

```powershell
# Ensure HF_TOKEN / network available
python -m aidev_extract.pilot --limit 200 --scan-rows 500000 --out data/interim/aidev_actions_index.json
# After enriching index with base_sha/head_sha/repo:
python -m github_fetch.fetch_pairs --index data/interim/aidev_actions_index.json --out data/processed/workflow_pairs
```

Alternative: reuse filtered CI/CD PR lists from the MSR 2026 replication package ([Taher-Ghaleb/AIAgentsCI_CD-MSR2026](https://github.com/Taher-Ghaleb/AIAgentsCI_CD-MSR2026)) then fetch YAML pairs.

## Adequacy criteria

- **Method validation:** satisfied by synthetic suite + unit tests (5/5 pytest)
- **External validity for prevalence claims:** requires AIDev/GitHub field sample ≥200/arm — mark RQ1/RQ2 field estimates as *pending scale-up* in Discussion until completed
- **Detector metrics:** report synthetic results as controlled benchmark; recompute on labeled field subsample before final submission

## Recommendation

Proceed with full manuscript draft now, clearly separating **controlled benchmark results** from **field-study protocol**. Complete AIDev extraction before JAIAI final upload if the editor/advisor requires large-N empirical prevalence.
