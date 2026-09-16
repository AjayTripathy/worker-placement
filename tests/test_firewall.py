"""Unit contract for core/firewall.py confusion_matrix.

The muni golden-master pins the muni consumer end-to-end. public_co's
confusion_matrix_print takes network-derived rows, so it cannot be replayed
deterministically — this pins the shared primitive directly and exercises
public_co's exact derivation on a synthetic cohort.

Run: python3 tests/test_firewall.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.firewall import confusion_matrix


def test_basic_counts():
    cm = confusion_matrix([(True, True), (True, False), (False, True), (False, False)])
    assert cm["confusion"] == {"TP": 1, "FP": 1, "TN": 1, "FN": 1}
    assert cm["n_evaluable"] == 4 and cm["n_unknown"] == 0
    assert cm["precision"] == 0.5 and cm["recall"] == 0.5 and cm["specificity"] == 0.5
    assert cm["accuracy"] == 0.5


def test_none_is_unknown():
    cm = confusion_matrix([(True, None), (None, True), (True, True)])
    assert cm["n_unknown"] == 2
    assert cm["n_evaluable"] == 1
    assert cm["confusion"]["TP"] == 1


def test_degenerate_denominators_are_zero():
    # No positives predicted -> precision/recall well-defined as 0.0, no ZeroDivision.
    cm = confusion_matrix([(False, False), (False, False)])
    assert cm["precision"] == 0.0 and cm["recall"] == 0.0
    assert cm["f1"] == 0.0
    assert cm["accuracy"] == 1.0
    # All-negative actuals -> majority baseline is 1.0, lift cannot be positive.
    assert cm["baseline_majority_accuracy"] == 1.0
    assert cm["lift_over_baseline_acc"] == 0.0


def test_matches_public_co_derivation():
    # Mirror confusion_matrix_print: predicted = score>=thr, actual = outcome in pos.
    rows = [
        {"score_per_claim": 2.0, "outcome": "FRAUD"},
        {"score_per_claim": 1.6, "outcome": "BANKRUPT"},
        {"score_per_claim": 0.2, "outcome": "ALIVE"},
        {"score_per_claim": 0.8, "outcome": "ALIVE"},
    ]
    thr, pos = 1.0, {"FRAUD", "BANKRUPT"}
    cm = confusion_matrix((r["score_per_claim"] >= thr, r["outcome"] in pos) for r in rows)
    # FRAUD@2.0 -> TP, BANKRUPT@1.6 -> TP, ALIVE@0.2 -> TN, ALIVE@0.8 -> TN
    assert cm["confusion"] == {"TP": 2, "FP": 0, "TN": 2, "FN": 0}
    assert cm["precision"] == 1.0 and cm["recall"] == 1.0 and cm["specificity"] == 1.0


def main() -> None:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")


if __name__ == "__main__":
    main()
