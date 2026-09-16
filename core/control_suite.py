"""Deterministic control-suite primitives, vertical-agnostic.

These are the apparatus a vertical uses to ask "is this basket selection better
than chance, or did the alpha come from the universe rather than the picking?"
They are pure and deterministic: given the same inputs (and seed) they return
byte-identical results, which is what lets the public_co golden-master pin them.

Scope discipline (see rigor/ ledger + the 2026-05-29 audit): only genuinely
shared, single-formula routines live here. The severity-weighted *composite*
deliberately does NOT — public_co has two divergent composite formulas
(synthesize.py's simple count/len(tuples) vs m_sources/composite_recompute.py's
distress+recovery with candidate exclusion), and unifying them would change
numbers. That is a behavior-change task, not an extraction, so it stays out.

Current consumer: public_co survivorship backtest (tier1_test_A/B).
Expected next consumers: the other public_co sample_universe placebo scripts;
muni_credit blind-OOS.
"""
from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlaceboResult:
    """Outcome of a random-basket placebo test."""
    n_trials: int
    placebo_mean: float
    placebo_stdev: float
    percentiles: dict[str, float] = field(default_factory=dict)  # "p05".."p99", "max"
    percentile_of_target: float = 0.0   # % of draws strictly below the target
    one_sided_p_value: float = 0.0       # fraction of draws >= the target
    z_score: float = 0.0


def placebo_basket_test(
    returns: list[float],
    basket_size: int,
    target_mean: float,
    n_trials: int = 10_000,
    seed: int = 0,
) -> PlaceboResult:
    """Locate `target_mean` on the distribution of random `basket_size`-baskets.

    Draws `n_trials` random baskets (without replacement) from `returns`, takes
    each basket's equal-weight mean, and reports where `target_mean` falls. A
    target in the top 1-2% means the selection is unlikely under random picking
    from the same universe; a target near the median means the basket's return
    came from the universe, not the picking.

    Determinism: uses `random.Random(seed)` and `rng.sample` in trial order, and
    computes each basket mean as `sum(draw) / basket_size`, matching the original
    tier1_test_B implementation exactly so existing outputs stay byte-identical.
    """
    rng = random.Random(seed)
    means: list[float] = []
    for _ in range(n_trials):
        draw = rng.sample(returns, basket_size)
        means.append(sum(draw) / basket_size)
    means.sort()

    def at(frac: float) -> float:
        return means[int(n_trials * frac)]

    percentiles = {
        "p05": at(0.05),
        "p25": at(0.25),
        "p50": means[n_trials // 2],
        "p75": at(0.75),
        "p95": at(0.95),
        "p99": at(0.99),
        "max": means[-1],
    }
    n_ge = sum(1 for m in means if m >= target_mean)
    pct_rank = (sum(1 for m in means if m < target_mean) / n_trials) * 100
    mu = statistics.mean(means)
    sd = statistics.stdev(means)
    return PlaceboResult(
        n_trials=n_trials,
        placebo_mean=mu,
        placebo_stdev=sd,
        percentiles=percentiles,
        percentile_of_target=pct_rank,
        one_sided_p_value=n_ge / n_trials,
        z_score=(target_mean - mu) / sd,
    )


def basket_overlap(set_a: set, set_b: set) -> dict[str, set]:
    """Partition two membership sets into both / only_a / only_b."""
    return {
        "both": set_a & set_b,
        "only_a": set_a - set_b,
        "only_b": set_b - set_a,
    }


def basket_stats(returns: list[float]) -> dict | None:
    """Equal-weight basket summary, or None for an empty basket.

    Uses statistics.mean/median so callers that previously called those directly
    stay numerically identical.
    """
    if not returns:
        return None
    return {
        "n": len(returns),
        "mean": statistics.mean(returns),
        "median": statistics.median(returns),
    }
