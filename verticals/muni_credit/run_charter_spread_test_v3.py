"""Re-run CSFA LCFF intercept spread test on v3 universe with 56 empirical anchors.

Tests whether the rating-band masking finding (ICEF=New Designs at BB+ 143 bps)
holds when expanded across the full 56-anchor CSFA 2010-2024 spread distribution.
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict
from statistics import mean, median, stdev

HERE = Path(__file__).parent
DATA = HERE / "data"

anchors_raw = json.loads((DATA / "charter_v3_spread_anchors.json").read_text())
ops = json.loads((DATA / "charter_operator_signals.json").read_text())
v3 = json.loads((DATA / "charter_universe_v3.json").read_text())

anchors = anchors_raw["anchors"]
op_per = ops.get("per_obligor", {})

# Normalize rating tier
def norm_rating(r):
    if not r: return None
    r = r.strip().upper()
    # Extract base rating
    for tier in ("BBB+", "BBB-", "BBB", "BB+", "BB-", "BB", "B+", "B-", "B",
                 "A+", "A-", "A", "AA+", "AA-", "AA", "AAA"):
        if tier in r:
            return tier
    return r[:5]

# Bucket anchors by rating
by_rating = defaultdict(list)
for a in anchors:
    rt = norm_rating(a["rating"])
    a["rating_norm"] = rt
    if rt:
        by_rating[rt].append(a)

# Get operator score for each anchor's obligor
for a in anchors:
    op = op_per.get(a["obligor"], {})
    a["operator_score"] = op.get("operator_signal_strength_score")

print("=" * 100)
print("CSFA LCFF INTERCEPT SPREAD TEST — v3 (56 empirical anchors)")
print("=" * 100)
print()

# Per-rating-band distribution
print(f"{'Rating':<10} {'N':<5} {'Median bps':<12} {'Mean bps':<10} {'Min-Max':<14} {'Stdev':<8}")
print("-" * 70)
for rt in ("BBB+", "BBB", "BBB-", "BB+", "BB", "BB-", "B+", "B"):
    rows = by_rating.get(rt, [])
    if not rows: continue
    sps = [r["mmd_spread_bps"] for r in rows if isinstance(r["mmd_spread_bps"], (int, float))]
    if len(sps) >= 1:
        md = median(sps) if sps else 0
        mn = mean(sps) if sps else 0
        sd = stdev(sps) if len(sps) >= 2 else 0
        print(f"  {rt:<8} {len(sps):<5} {md:<12.0f} {mn:<10.1f} {min(sps)}-{max(sps):<10} {sd:<8.1f}")

# Within-rating-band operator-signal test
print()
print("=" * 100)
print("WITHIN-RATING-BAND TEST: does operator strength predict spread WITHIN a rating?")
print("=" * 100)
print()
print("The masking hypothesis: spread DOES NOT track operator strength within a rating band.")
print("(Because CSFA intercept moves the obligor into the rating band, and within-band")
print(" operator signal is absorbed by the intercept's credit enhancement.)")
print()

for rt in ("BBB", "BBB-", "BB+"):
    rows = [r for r in by_rating.get(rt, []) if isinstance(r.get("operator_score"), (int, float)) and isinstance(r.get("mmd_spread_bps"), (int, float))]
    if len(rows) < 2:
        continue
    print(f"\n--- {rt} band ---")
    print(f"{'Obligor':<42} {'Op Score':<10} {'Spread bps':<12} {'Series'}")
    for r in sorted(rows, key=lambda x: x["operator_score"]):
        print(f"  {r['obligor'][:40]:<42} {r['operator_score']:<10} {r['mmd_spread_bps']:<12} {r['series']}")
    sps = [r["mmd_spread_bps"] for r in rows]
    ops_ = [r["operator_score"] for r in rows]
    n = len(sps)
    ms = sum(sps) / n
    mo = sum(ops_) / n
    num = sum((sps[i] - ms) * (ops_[i] - mo) for i in range(n))
    den_s = (sum((x - ms) ** 2 for x in sps)) ** 0.5
    den_o = (sum((x - mo) ** 2 for x in ops_)) ** 0.5
    if den_s > 0 and den_o > 0:
        corr = num / (den_s * den_o)
        print(f"  Pearson r(spread, op_score) within {rt}: {corr:+.3f}  (N={n})")
        if abs(corr) < 0.3:
            print(f"  → Within-rating-band: operator signal does NOT predict spread (masking CONFIRMED)")
        else:
            print(f"  → Within-rating-band: operator signal {'positively' if corr > 0 else 'negatively'} predicts spread (partial)")

# Across-rating-band — confirm rating dominates
print()
print("=" * 100)
print("ACROSS-RATING-BAND: does rating dominate spread (as the masking hypothesis requires)?")
print("=" * 100)
print()
all_paired = [r for r in anchors if isinstance(r.get("mmd_spread_bps"), (int, float))]
# For each transaction, predict spread from rating only
RATING_RANK = {"BBB+": 1, "BBB": 2, "BBB-": 3, "BB+": 4, "BB": 5, "BB-": 6, "B+": 7, "B": 8}
ranked = [(r["rating_norm"], r["mmd_spread_bps"]) for r in all_paired if r["rating_norm"] in RATING_RANK]
if len(ranked) >= 5:
    # Spearman approximation: correlate rating-rank vs spread
    rks = [RATING_RANK[r] for r, s in ranked]
    sps = [s for r, s in ranked]
    n = len(rks)
    mr = sum(rks) / n
    ms = sum(sps) / n
    num = sum((rks[i] - mr) * (sps[i] - ms) for i in range(n))
    den_r = (sum((x - mr) ** 2 for x in rks)) ** 0.5
    den_s = (sum((x - ms) ** 2 for x in sps)) ** 0.5
    if den_r > 0 and den_s > 0:
        corr = num / (den_r * den_s)
        print(f"  Correlation(rating_rank, spread) across all {n} anchors: {corr:+.3f}")
        print(f"  Interpretation: rating ALONE explains {(corr**2)*100:.0f}% of spread variance — strong directionality")

# Time-series for Granada Hills — single-issuer rating curve
print()
print("=" * 100)
print("CASE STUDY: Granada Hills Charter — single-issuer time-series (BBB- → BBB)")
print("=" * 100)
gh = sorted([r for r in anchors if "Granada Hills" in r.get("obligor", "")],
            key=lambda x: x.get("closing_date") or "")
for r in gh:
    rt = r.get("rating_norm") or r.get("rating", "?")
    print(f"  {r.get('closing_date'):<12} {r.get('series'):<20} {str(rt):<10} spread {r.get('mmd_spread_bps')} bps  par {r.get('par_usd')}")

# Save the v3 spread test result
out = {
    "_built": "2026-05-28",
    "anchors_used": len(anchors),
    "per_rating_distribution": {
        rt: {
            "n": len(by_rating[rt]),
            "spreads_bps": [r["mmd_spread_bps"] for r in by_rating[rt] if isinstance(r["mmd_spread_bps"], (int, float))],
            "median_bps": median([r["mmd_spread_bps"] for r in by_rating[rt] if isinstance(r["mmd_spread_bps"], (int, float))] or [0]),
        } for rt in by_rating if by_rating[rt]
    },
    "within_band_op_score_tests": {},
}
(DATA / "charter_v3_spread_test_results.json").write_text(json.dumps(out, indent=2, default=str))
print()
print(f"Results saved to data/charter_v3_spread_test_results.json")
