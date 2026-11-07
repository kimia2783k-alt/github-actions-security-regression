from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import chi2_contingency, fisher_exact


@dataclass
class BinaryMetrics:
    tp: int
    fp: int
    tn: int
    fn: int

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    @property
    def fpr(self) -> float:
        return self.fp / (self.fp + self.tn) if (self.fp + self.tn) else 0.0

    @property
    def fnr(self) -> float:
        return self.fn / (self.fn + self.tp) if (self.fn + self.tp) else 0.0

    def as_dict(self) -> dict[str, float | int]:
        return {
            "tp": self.tp,
            "fp": self.fp,
            "tn": self.tn,
            "fn": self.fn,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "fpr": round(self.fpr, 4),
            "fnr": round(self.fnr, 4),
        }


def binary_metrics(y_true: list[int], y_pred: list[int]) -> BinaryMetrics:
    tp = fp = tn = fn = 0
    for t, p in zip(y_true, y_pred):
        if t == 1 and p == 1:
            tp += 1
        elif t == 0 and p == 1:
            fp += 1
        elif t == 0 and p == 0:
            tn += 1
        elif t == 1 and p == 0:
            fn += 1
    return BinaryMetrics(tp, fp, tn, fn)


def ai_vs_human_test(ai_pos: int, ai_n: int, human_pos: int, human_n: int) -> dict:
    table = np.array(
        [
            [ai_pos, ai_n - ai_pos],
            [human_pos, human_n - human_pos],
        ]
    )
    result: dict = {
        "ai_rate": ai_pos / ai_n if ai_n else None,
        "human_rate": human_pos / human_n if human_n else None,
        "table": table.tolist(),
    }
    if table.min() < 5:
        oddsratio, p = fisher_exact(table)
        result.update({"test": "fisher", "odds_ratio": float(oddsratio), "p_value": float(p)})
    else:
        chi2, p, dof, _ = chi2_contingency(table)
        result.update(
            {
                "test": "chi2",
                "chi2": float(chi2),
                "dof": int(dof),
                "p_value": float(p),
            }
        )
    return result
