# Field false-negative analysis (policy v3)

Source of truth: `eval_summary.json` after v3 gold + detector.

| Item | Value |
|------|------:|
| N | 330 |
| Gold positives | 46 |
| Validator FN | 2 |
| Validator FP | 5 |
| Recall | 0.9565 |
| FPR | 0.0176 |

## Historical note (superseded)

Earlier drafts reported FN≈24 and Recall≈0.38 under interim gold (~39 positives) before formalization.
A mid-stage v2 gold (33/330) briefly showed FN=0 after trusted-owner realignment but before R12–R15.
Those figures are **not** current results.

## Gold definition changes on the same N=330

See `gold_v_delta.md`: interim (reconstructed) ≈40 → v2 ≈33 → **v3 = 46**.
