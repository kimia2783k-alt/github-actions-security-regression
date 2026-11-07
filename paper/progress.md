# Progress log

## 2026-10-24 — Advisor + journal-path pack (v0.3-advisor)

- [x] Version unified to **v0.3-advisor** (header + footer)
- [x] Strengthened RQ2 synthetic-tag caveat + zizmor framing (not “zizmor is bad”)
- [x] `replication/REPRODUCE.md` + availability with `[URL_TO_BE_FILLED]`
- [x] Pin semantics: comment-only SHA not effective pin; tests + re-eval freeze
- [x] 330-pair manifest + sampling protocol + ENV_FREEZE + OWASP map check
- [x] Confusion matrices + manuscript/DOCX synced to freeze metrics
- [x] `paper/literature/reference_audit.md` + incomplete bib notes
- [x] Dual-annotation infra: `annotations/human_round/` (80 pairs), `compute_iaa.py`, guide
- [x] Human labels: single annotator A (n=63); annotator B **out of scope** for this delivery (no κ)
- [x] Delivery manuscripts v0.4 with single-annotator human subset

## 2026-10-24 — Consistency pass (v0.3 manuscript)

- [x] Explained gold change on fixed N=330: interim ≈39–40 → v2 ≈33 → **v3 = 46** (`tables/field/gold_v_delta.md`)
- [x] Split §5.4 into executed pilot vs future scale-up; removed “rates remain unset”
- [x] Softened detector claims (controlled co-design; field predicate-aligned)
- [x] Unified zizmor-diff FPR to **0.18** everywhere (not 0.21)
- [x] Abstract / taxonomy / guide FAQ / literature / protocol synced to policy v3
- [x] Regenerated Word manuscripts

### Current field source of truth (`tables/field/eval_summary.json`)

| Metric | Value |
|--------|------:|
| N | 330 |
| Gold positives | 46 (13.9%) |
| Policy P/R/F1/FPR | 0.90 / 0.96 / 0.93 / 0.02 |
| Zizmor after-only FPR | 0.91 |
| Zizmor before/after-diff FPR | 0.18 |
| AI vs human | 16.0% vs 7.5% (χ² p≈0.085) |

### Historical (superseded — do not cite as current)

- Interim gold ≈39/330 (11.8%); Policy ≈0.79/0.38; Fisher p≈0.009
- Mid v2 gold ≈33/330 (10.0%)

## 2026-10-21 — Milestone manuscript v0.2-full (continued)

### Phase A (complete)

- [x] Full English journal-style manuscript in `paper/manuscript/main.md`
- [x] Tables 1–7 embedded; figures regenerated
- [x] Persian abstract + supervisor milestone note
- [x] `references.bib` aligned with in-text citations
- [x] Proposal points to English manuscript

### Phase B (complete for pilot; scale-up optional)

- [x] zizmor CLI baseline + before/after-diff
- [x] Field pilot merged **N=330**
- [x] Policy v3 formalization (R01–R15)
- [ ] Optional: enlarge Cursor/Devin/Jules; PR-level human matching
- [ ] Paste into official JAIAI DOC + submit

### Frozen controlled-benchmark metrics

| Method | P | R | F1 | FPR | N |
|--------|--:|--:|---:|----:|--:|
| Policy Validator | 1.00 | 1.00 | 1.00 | 0.00 | 15 |
| zizmor v1.31.1 after-only | 0.67 | 1.00 | 0.80 | 1.00 | 15 |

### Primary deliverable for advisor

Explain (FA Word): `paper/manuscript/Guide_Explain_Full_FA.docx`  
English manuscript Word: `paper/manuscript/Security_Regressions_GHA_AI_Agents_Manuscript.docx`  
Pointer note: `paper/manuscript/milestone_note_fa.md`
