"""Tier 1 / Test B — random-LONG placebo.

Draws 10k random 13-name baskets from the 64 scored names with valid
forward returns. Locates the framework's LOOSE_LONG basket mean
(+64.6%) on the empirical distribution.

If +64.6% lies in the top 1-2% of the placebo distribution, the basket
return is unlikely under random selection from the same universe. If
it lies near the median, the framework added no selection skill within
this universe — the alpha came from elsewhere (mostly the act of
running a basket at all on a distressed universe that has fat upside
tails, not from picking).

Usage:
    python3 verticals/public_co/data/_backtest/survivorship_2025_05/tier1_test_B_placebo.py
"""
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from core.control_suite import placebo_basket_test

SYNTH = HERE / "synthesis.json"
SEED = 20260525
N_TRIALS = 10_000


def main():
    rows = json.loads(SYNTH.read_text())
    # Universe of scored names with valid forward return
    scored = [r for r in rows if r.get("forward_return") is not None]
    # Framework LOOSE_LONG basket size + mean
    framework_long = [r for r in scored if r["tier"] in ("STRICT_LONG", "LOOSE_LONG")]
    n_basket = len(framework_long)
    framework_mean = statistics.mean(r["forward_return"] for r in framework_long)
    framework_tickers = sorted(r["ticker"] for r in framework_long)

    print("=" * 80)
    print("TIER 1 / TEST B — Random-LONG placebo")
    print("=" * 80)
    print(f"Scored universe: n={len(scored)}")
    print(f"Framework LOOSE_LONG basket: n={n_basket}, mean={framework_mean*100:+.1f}%")
    print(f"Framework picks: {framework_tickers}")
    print()

    rets = [r["forward_return"] for r in scored]
    res = placebo_basket_test(rets, n_basket, framework_mean, n_trials=N_TRIALS, seed=SEED)
    pct = res.percentiles
    mu = res.placebo_mean
    sd = res.placebo_stdev
    pct_rank = res.percentile_of_target
    one_sided_p = res.one_sided_p_value
    z = res.z_score

    print(f"Placebo distribution ({N_TRIALS:,} draws of {n_basket}-name baskets):")
    print(f"  mean         = {mu*100:+.1f}%")
    print(f"  stdev        = {sd*100:.1f} pp")
    print(f"  p05          = {pct['p05']*100:+.1f}%")
    print(f"  p25          = {pct['p25']*100:+.1f}%")
    print(f"  p50 (median) = {pct['p50']*100:+.1f}%")
    print(f"  p75          = {pct['p75']*100:+.1f}%")
    print(f"  p95          = {pct['p95']*100:+.1f}%")
    print(f"  p99          = {pct['p99']*100:+.1f}%")
    print(f"  max          = {pct['max']*100:+.1f}%")
    print()
    print(f"Framework basket return ({framework_mean*100:+.1f}%):")
    print(f"  percentile   = {pct_rank:.2f}%  (fraction of draws strictly below)")
    print(f"  one-sided p  = {one_sided_p:.4f}  (draws >= framework)")
    print(f"  z-score      = {z:+.2f}")
    print()
    if one_sided_p < 0.01:
        verdict = "STRONG: framework picks significantly better than random within universe."
    elif one_sided_p < 0.05:
        verdict = "MODERATE: framework picks beat random at 5% level."
    elif one_sided_p < 0.15:
        verdict = "WEAK: framework picks above median but not statistically robust."
    else:
        verdict = "NULL: framework picks indistinguishable from random within universe — alpha came from universe, not picking."
    print(f"Verdict: {verdict}")

    out = HERE / "tier1_test_B_results.json"
    out.write_text(json.dumps({
        "n_basket": n_basket,
        "framework_mean": framework_mean,
        "framework_tickers": framework_tickers,
        "n_trials": N_TRIALS,
        "placebo_mean": mu,
        "placebo_stdev": sd,
        "placebo_p05": pct["p05"],
        "placebo_p50": pct["p50"],
        "placebo_p95": pct["p95"],
        "placebo_p99": pct["p99"],
        "placebo_max": pct["max"],
        "percentile_of_framework": pct_rank,
        "one_sided_p_value": one_sided_p,
        "z_score": z,
        "verdict": verdict,
    }, indent=2))
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
