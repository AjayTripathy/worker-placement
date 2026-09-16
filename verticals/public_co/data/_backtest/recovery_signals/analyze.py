"""Analyze recovery_backtest.json:

  - Spearman correlation: recovery_signal_score vs fwd_12m, vs fwd_24m
  - Quintile basket math: top vs bottom quintile by score, at 12m and 24m
  - Comparison to original Tier 3 framework tier (from synthesis.json)
  - Leaderboard

Run:
  python3 verticals/public_co/data/_backtest/recovery_signals/analyze.py
"""
import json
import statistics
from pathlib import Path

HERE = Path(__file__).parent
TIER3 = HERE.parents[1] / "_backtest" / "walk_forward_2024_05"


def rank(arr):
    ix = sorted(range(len(arr)), key=lambda i: arr[i])
    r = [0.0]*len(arr)
    for k, i in enumerate(ix): r[i] = k + 1
    return r


def pearson(xs, ys):
    n = len(xs); mx = sum(xs)/n; my = sum(ys)/n
    num = sum((x-mx)*(y-my) for x,y in zip(xs, ys))
    dx = (sum((x-mx)**2 for x in xs))**0.5
    dy = (sum((y-my)**2 for y in ys))**0.5
    return num/(dx*dy) if dx and dy else 0


def main():
    data = json.load(open(HERE / "recovery_backtest.json"))
    # Original framework tier (from synthesis.json)
    synth = json.load(open(TIER3 / "synthesis.json"))
    orig_tier = {r["ticker"]: r["tier"] for r in synth}

    valid = [r for r in data if r.get("fwd_12m") is not None and r.get("fwd_24m") is not None]
    print(f"Recovery backtest: {len(data)} runs, {len(valid)} with both 12m + 24m returns")
    print()

    scores = [r["recovery_signal_score"] for r in valid]
    ret12  = [r["fwd_12m"] for r in valid]
    ret24  = [r["fwd_24m"] for r in valid]

    print("CORRELATIONS (recovery_signal_score vs forward returns):")
    print(f"  vs 12m forward return:  Pearson r = {pearson(scores, ret12):+.3f},  Spearman ρ = {pearson(rank(scores), rank(ret12)):+.3f}")
    print(f"  vs 24m forward return:  Pearson r = {pearson(scores, ret24):+.3f},  Spearman ρ = {pearson(rank(scores), rank(ret24)):+.3f}")
    print()

    # Quintile basket math
    sorted_by_score = sorted(valid, key=lambda r: -r["recovery_signal_score"])
    n = len(sorted_by_score)
    q = n // 5
    top = sorted_by_score[:q]
    bottom = sorted_by_score[-q:]
    middle = sorted_by_score[q:-q]

    def stats(group, label):
        if not group: return
        r12 = [r["fwd_12m"] for r in group]
        r24 = [r["fwd_24m"] for r in group]
        print(f"  {label:30}  n={len(group):3}  12m mean={statistics.mean(r12)*100:+7.1f}%  24m mean={statistics.mean(r24)*100:+7.1f}%")

    print("QUINTILE BASKET MATH:")
    stats(top, "TOP quintile by score")
    stats(middle, "MIDDLE 60%")
    stats(bottom, "BOTTOM quintile by score")
    print()
    print(f"  Top - Bottom 12m spread: {(statistics.mean(r['fwd_12m'] for r in top) - statistics.mean(r['fwd_12m'] for r in bottom))*100:+.1f} pp")
    print(f"  Top - Bottom 24m spread: {(statistics.mean(r['fwd_24m'] for r in top) - statistics.mean(r['fwd_24m'] for r in bottom))*100:+.1f} pp")
    print()

    # Comparison to original framework's tier
    print("COMPARISON TO ORIGINAL TIER 3 FRAMEWORK TIER:")
    orig_long = [r for r in valid if orig_tier.get(r["ticker"]) in ("STRICT_LONG", "LOOSE_LONG")]
    orig_short = [r for r in valid if orig_tier.get(r["ticker"]) == "SHORT"]
    print(f"  Original LONG basket: n={len(orig_long)} 12m={statistics.mean(r['fwd_12m'] for r in orig_long)*100:+.1f}% 24m={statistics.mean(r['fwd_24m'] for r in orig_long)*100:+.1f}%")
    print(f"  Original SHORT basket: n={len(orig_short)} 12m={statistics.mean(r['fwd_12m'] for r in orig_short)*100:+.1f}% 24m={statistics.mean(r['fwd_24m'] for r in orig_short)*100:+.1f}%")
    print()
    print("  NEW: top-quintile recovery names + original LONG, overlap:")
    top_tk = {r["ticker"] for r in top}
    long_tk = {r["ticker"] for r in orig_long}
    print(f"    top-recovery ∩ original-LONG: {sorted(top_tk & long_tk)}")
    print(f"    top-recovery, ORIGINALLY SHORT: {sorted(top_tk & {r['ticker'] for r in orig_short})}")
    print()

    # Leaderboard
    print("LEADERBOARD — top 15 by recovery_signal_score:")
    print(f"  {'tk':6}  {'score':>5}  {'orig_tier':>12}  {'12m':>8}  {'24m':>8}  signals")
    for r in sorted_by_score[:15]:
        sig_summary = []
        for k in ("filing_timeliness", "insider_buy_timing", "mw_lifecycle", "lender_concession"):
            x = r.get(k, {})
            sig_summary.append(f"{k[:4]}={x.get('signal','?')[:10]}({x.get('score',0):+d})")
        print(f"  {r['ticker']:6}  {r['recovery_signal_score']:+5d}  {orig_tier.get(r['ticker'],'?'):>12}  {r['fwd_12m']*100:>+7.1f}%  {r['fwd_24m']*100:>+7.1f}%  {' | '.join(sig_summary[:2])}")

    print()
    print("BOTTOM 10 by recovery_signal_score:")
    for r in sorted_by_score[-10:]:
        sig_summary = []
        for k in ("filing_timeliness", "insider_buy_timing", "mw_lifecycle", "lender_concession"):
            x = r.get(k, {})
            sig_summary.append(f"{k[:4]}={x.get('signal','?')[:10]}({x.get('score',0):+d})")
        print(f"  {r['ticker']:6}  {r['recovery_signal_score']:+5d}  {orig_tier.get(r['ticker'],'?'):>12}  {r['fwd_12m']*100:>+7.1f}%  {r['fwd_24m']*100:>+7.1f}%  {' | '.join(sig_summary[:2])}")


if __name__ == "__main__":
    main()
