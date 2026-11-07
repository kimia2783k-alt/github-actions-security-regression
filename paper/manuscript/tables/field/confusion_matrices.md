# Confusion matrices (frozen post pin-semantics fix)

Source: `eval_summary.json`, `eval_human_gold.json`.  
Effective pin = `@ref` is 40-hex only; comment-only SHA is not a pin.

## Field gold (N=330, policy-v3)

### Policy Validator

|  | Pred + | Pred − |
|--|-------:|-------:|
| Gold + | TP 43 | FN 3 |
| Gold − | FP 6 | TN 278 |

P=0.8776 · R=0.9348 · F1=0.9053 · FPR=0.0211 · FNR=0.0652

### Zizmor after-only

|  | Pred + | Pred − |
|--|-------:|-------:|
| Gold + | TP 44 | FN 2 |
| Gold − | FP 258 | TN 26 |

P=0.1457 · R=0.9565 · F1=0.2529 · FPR=0.9085 · FNR=0.0435

### Zizmor before/after finding-set diff

|  | Pred + | Pred − |
|--|-------:|-------:|
| Gold + | TP 34 | FN 12 |
| Gold − | FP 50 | TN 234 |

P=0.4048 · R=0.7391 · F1=0.5231 · FPR=0.1761 · FNR=0.2609

## Human gold (n=63, annotator A)

### Policy Validator

|  | Pred + | Pred − |
|--|-------:|-------:|
| Human + | TP 34 | FN 2 |
| Human − | FP 5 | TN 22 |

P=0.8718 · R=0.9444 · F1=0.9067 · FPR=0.1852 · FNR=0.0556
