"""TIER-1 CONTROL 1 — placebo tests on the survivorship_2025_05 honesty backtest.

Nulls (all on the 64 scored names, window 2025-05-15 -> 2026-05-15, EW):
  A. random-SELECTION: 10k random 13-name baskets           (vs LOOSE_LONG +64.6%)
  B. random-EXCLUSION: 10k random keep-14 baskets           (vs NOT-SHORT +66.0%)
  C. score-SHUFFLE:    10k permutations of the composite vector across names,
                       re-tier, take the LOOSE_LONG basket  (equivalent to A up to
                       tie-structure; run anyway as specified)
  D. concentration check: leave-one-out on the framework basket.

Alpha framing: subtracting IJR (+26.11% TR, verified via yfinance) is a
constant shift, so percentile/z are identical for return and alpha.

Writes: data/_backtest/tier1_controls/control1_placebo.json
"""
from __future__ import annotations

import json
import random
import statistics
from pathlib import Path

from tier1_step0_reproduce import load_rows  # type: ignore

HERE = Path(__file__).parent
OUT = HERE / "data" / "_backtest" / "tier1_controls"
IJR = 0.2611
SEED = 20260706
N_TRIALS = 10_000


def pct_stats(dist, target):
    d = sorted(dist)
    below = sum(1 for x in d if x < target)
    ge = sum(1 for x in d if x >= target)
    mu = statistics.mean(d)
    sd = statistics.stdev(d)
    return {
        "mean": mu, "stdev": sd,
        "p05": d[int(0.05 * len(d))], "p50": d[len(d) // 2],
        "p95": d[int(0.95 * len(d))], "p99": d[int(0.99 * len(d))],
        "max": d[-1],
        "target": target,
        "percentile_of_target": 100 * below / len(d),
        "one_sided_p": ge / len(d),
        "z": (target - mu) / sd,
    }


def main():
    rows, _, _ = load_rows()
    rows = [r for r in rows if r["forward_return"] is not None]
    rets = [r["forward_return"] for r in rows]
    comps = [r["composite"] for r in rows]
    rng = random.Random(SEED)

    fw_long = [r for r in rows if r["tier"] in ("STRICT_LONG", "LOOSE_LONG")]
    fw_keep = [r for r in rows if r["tier"] != "SHORT"]
    fw_long_mean = statistics.mean(r["forward_return"] for r in fw_long)
    fw_keep_mean = statistics.mean(r["forward_return"] for r in fw_keep)

    # A. random selection of len(fw_long)
    k = len(fw_long)
    distA = [statistics.mean(rng.sample(rets, k)) for _ in range(N_TRIALS)]
    A = pct_stats(distA, fw_long_mean)

    # B. random exclusion -> keep len(fw_keep)
    kk = len(fw_keep)
    distB = [statistics.mean(rng.sample(rets, kk)) for _ in range(N_TRIALS)]
    B = pct_stats(distB, fw_keep_mean)

    # C. score shuffle: permute composite vector, re-tier, LOOSE_LONG basket
    def tier(c):
        return "L" if c <= 0.30 else ("N" if c < 0.50 else "S")
    distC = []
    idx = list(range(len(rows)))
    for _ in range(N_TRIALS):
        rng.shuffle(idx)
        basket = [rets[i] for n, i in enumerate(idx) if comps[n] <= 0.30]
        # comps[n] assigned to name idx[n]; basket = names receiving a LONG score
        distC.append(statistics.mean(basket))
    C = pct_stats(distC, fw_long_mean)

    # D. concentration: leave-one-out on framework basket
    loo = []
    for r in fw_long:
        rest = [x["forward_return"] for x in fw_long if x is not r]
        loo.append({"drop": r["ticker"], "ret": r["forward_return"],
                    "basket_mean_without": statistics.mean(rest)})
    loo.sort(key=lambda d: d["basket_mean_without"])

    out = {
        "seed": SEED, "n_trials": N_TRIALS, "ijr_tr": IJR,
        "framework_long": {"n": k, "mean": fw_long_mean, "alpha_vs_ijr": fw_long_mean - IJR,
                           "tickers": sorted(r["ticker"] for r in fw_long)},
        "framework_keep_notshort": {"n": kk, "mean": fw_keep_mean, "alpha_vs_ijr": fw_keep_mean - IJR},
        "null_A_random_selection": A,
        "null_B_random_exclusion": B,
        "null_C_score_shuffle": C,
        "leave_one_out": loo,
    }
    (OUT / "control1_placebo.json").write_text(json.dumps(out, indent=2))

    for name, res, tgt in [("A random-selection (13)", A, fw_long_mean),
                           ("B random-exclusion (keep 14)", B, fw_keep_mean),
                           ("C score-shuffle LOOSE_LONG", C, fw_long_mean)]:
        print(f"NULL {name}: target {tgt*100:+.1f}%  null mean {res['mean']*100:+.1f}%  "
              f"p95 {res['p95']*100:+.1f}%  p99 {res['p99']*100:+.1f}%  max {res['max']*100:+.1f}%")
        print(f"   percentile {res['percentile_of_target']:.2f}  one-sided p {res['one_sided_p']:.4f}  z {res['z']:+.2f}")
    print("\nLeave-one-out (worst → best basket without that name):")
    for d in loo[:3] + loo[-3:]:
        print(f"   drop {d['drop']:6} (ret {d['ret']*100:+7.1f}%) -> basket {d['basket_mean_without']*100:+.1f}%")


if __name__ == "__main__":
    main()
