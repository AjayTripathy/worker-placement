"""Unit contract for core/control_suite.py primitives.

The public_co golden-master already pins these end-to-end, but this pins the
shared primitives directly so a future consumer (muni blind-OOS) can rely on a
stable contract without depending on public_co's data.

Run: python3 tests/test_control_suite.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.control_suite import basket_overlap, basket_stats, placebo_basket_test


def test_placebo_is_deterministic_for_a_seed():
    rets = [(-1) ** i * (i % 7) / 10 for i in range(40)]
    a = placebo_basket_test(rets, 5, 0.2, n_trials=2000, seed=123)
    b = placebo_basket_test(rets, 5, 0.2, n_trials=2000, seed=123)
    assert a == b, "same seed must give identical result"
    c = placebo_basket_test(rets, 5, 0.2, n_trials=2000, seed=124)
    assert c != a, "different seed should generally differ"


def test_placebo_reports_target_position():
    rets = [0.0] * 20 + [1.0] * 20
    # A target above every achievable basket mean sits at the top.
    res = placebo_basket_test(rets, 4, 2.0, n_trials=1000, seed=1)
    assert res.percentile_of_target == 100.0
    assert res.one_sided_p_value == 0.0
    # A target below every basket mean sits at the bottom.
    res2 = placebo_basket_test(rets, 4, -1.0, n_trials=1000, seed=1)
    assert res2.percentile_of_target == 0.0
    assert res2.one_sided_p_value == 1.0


def test_basket_overlap_partitions():
    ov = basket_overlap({"A", "B", "C"}, {"B", "C", "D"})
    assert ov["both"] == {"B", "C"}
    assert ov["only_a"] == {"A"}
    assert ov["only_b"] == {"D"}


def test_basket_stats_empty_is_none():
    assert basket_stats([]) is None
    s = basket_stats([0.1, 0.3])
    assert s == {"n": 2, "mean": 0.2, "median": 0.2}


def main() -> None:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")


if __name__ == "__main__":
    main()
