"""Synthesize Tier 3 walk-forward results.

Same pattern as Tier 1/2 synthesize. Reads pilot_<TICKER>.json files,
runs deterministic composite recompute, joins with forward returns from
_unblinded/tier3_test_set.json, computes basket P&L + catastrophe-recall.

Key comparison: Tier 3 catastrophe recall vs Tier 1 (93%). If close,
in-cohort detection is durable. If much lower, Tier 1 was window-specific.

Run:
    python3 verticals/public_co/data/_backtest/walk_forward_2024_05/synthesize.py
"""
import json
import statistics
from pathlib import Path

HERE = Path(__file__).parent
SCORES = HERE / "scores"
TEST_SET = HERE / "_unblinded" / "tier3_test_set.json"

SEV_W = {
    "PASS": 0,
    "UNVERIFIABLE": 0,
    "MODERATE_UNDERDELIVERY": 1,
    "SEVERE_UNDERDELIVERY": 2,
    "RED_FLAG_NEGATIVE": 3,
}

# IJR same-window (2024-05-15 → 2025-05-15)
# IJR ~107.06 at 2024-05-15, ~105.26 at 2025-05-15 = -1.68%
# Will compute from yfinance if needed
IJR_RETURN = 0.0029  # IJR 106.71 → 107.02 (2024-05-15 → 2025-05-15)


def tier(composite: float) -> str:
    if composite <= 0.20:
        return "STRICT_LONG"
    if composite <= 0.30:
        return "LOOSE_LONG"
    if composite < 0.50:
        return "NEUTRAL"
    return "SHORT"


def main():
    test_set = {r["ticker"]: r for r in json.loads(TEST_SET.read_text())}
    rows = []
    unscoreable = []
    for f in sorted(SCORES.glob("pilot_*.json")):
        d = json.loads(f.read_text())
        tk = d.get("ticker") or f.stem.replace("pilot_", "")
        tuples = d.get("rfm_tuples") or []
        ts = test_set.get(tk, {})
        fwd = ts.get("forward_return")
        if not tuples:
            unscoreable.append({"ticker": tk, "reason": d.get("exclusion_reason", "no_tuples"), "forward_return": fwd})
            continue
        counts = {k: 0 for k in SEV_W}
        for t in tuples:
            s = t.get("severity")
            if s in counts:
                counts[s] += 1
        composite = sum(SEV_W[k] * v for k, v in counts.items()) / len(tuples)
        rows.append({
            "ticker": tk,
            "company": ts.get("company") or d.get("company"),
            "sector": ts.get("sector") or d.get("sector"),
            "composite_recomputed": composite,
            "composite_agent_reported": d.get("composite"),
            "tier": tier(composite),
            "n_claims": len(tuples),
            "sev_counts": counts,
            "forward_return": fwd,
            "drawdown_2024_05_15": ts.get("drawdown_2024_05_15"),
            "delisted_before_measurement": ts.get("delisted_before_measurement", False),
            "summary": d.get("summary", "")[:500],
        })
    rows.sort(key=lambda x: -x["composite_recomputed"])

    print("=" * 100)
    print(f"TIER 3 / WALK-FORWARD 2024-05-15 → 2025-05-15 — {len(rows)} pilots (target 60)")
    print(f"  Drawdown floor: -25%, IJR same window: {IJR_RETURN*100:+.1f}%")
    print("=" * 100)
    print()
    print(f"{'TK':6} {'comp':>5}  {'tier':12}  {'fwd':>8}  {'dd':>7}  {'sector':18}  {'sev':18}")
    print("-" * 100)
    for r in rows:
        fwd = r["forward_return"]
        fwd_s = f"{fwd*100:+.1f}%" if fwd is not None else "  null"
        dd = r.get("drawdown_2024_05_15")
        dd_s = f"{dd*100:+.1f}%" if dd is not None else "  null"
        sc = r["sev_counts"]
        sev = f"P{sc['PASS']}/M{sc['MODERATE_UNDERDELIVERY']}/S{sc['SEVERE_UNDERDELIVERY']}/R{sc['RED_FLAG_NEGATIVE']}/U{sc['UNVERIFIABLE']}"
        del_tag = " [DEL]" if r.get("delisted_before_measurement") else ""
        print(f"{r['ticker']:6} {r['composite_recomputed']:>5.3f}  {r['tier']:12}  {fwd_s:>8}  {dd_s:>7}  {(r['sector'] or '')[:18]:18}  {sev:18}{del_tag}")

    print()
    print("=" * 100)
    print("CATASTROPHE-RECALL TEST (the critical Tier 3 metric)")
    print("=" * 100)
    catastrophes = [r for r in rows if (r["forward_return"] or 0) <= -0.40]
    short_flagged = [r for r in rows if r["tier"] == "SHORT"]
    cats_flagged = [r for r in catastrophes if r["tier"] == "SHORT"]
    print(f"  Catastrophes (return <= -40%): {len(catastrophes)}")
    print(f"  SHORT-flagged: {len(short_flagged)}")
    print(f"  True positives (SHORT-flagged catastrophes): {len(cats_flagged)}")
    if catastrophes:
        recall = len(cats_flagged)/len(catastrophes)*100
        print(f"  Catastrophe SHORT-flag RECALL: {recall:.0f}%")
        print(f"  (Tier 1 was 93%; collapse to ~30-50% would suggest Tier 1 was window-specific)")
    if short_flagged:
        prec = len(cats_flagged)/len(short_flagged)*100
        print(f"  SHORT precision (TP / all SHORT-flagged): {prec:.0f}%")

    print()
    print("FALSE POSITIVES (SHORT but positive return):")
    fps = [r for r in rows if r["tier"] == "SHORT" and (r["forward_return"] or 0) > 0.10]
    for r in fps:
        print(f"  {r['ticker']:6} comp={r['composite_recomputed']:.3f}  fwd={r['forward_return']*100:+.1f}%")

    print()
    print("FALSE NEGATIVES (catastrophes missed by framework):")
    fns = [r for r in catastrophes if r["tier"] != "SHORT"]
    for r in fns:
        print(f"  {r['ticker']:6} comp={r['composite_recomputed']:.3f}  fwd={r['forward_return']*100:+.1f}%  tier={r['tier']}")

    print()
    print("=" * 100)
    print("BASKET P&L")
    print("=" * 100)
    short_rets = [r["forward_return"] for r in rows if r["tier"] == "SHORT" and r["forward_return"] is not None]
    long_rets = [r["forward_return"] for r in rows if r["tier"] in ("STRICT_LONG", "LOOSE_LONG") and r["forward_return"] is not None]
    strict_rets = [r["forward_return"] for r in rows if r["tier"] == "STRICT_LONG" and r["forward_return"] is not None]
    notshort_rets = [r["forward_return"] for r in rows if r["tier"] != "SHORT" and r["forward_return"] is not None]
    universe_rets = [r["forward_return"] for r in test_set.values() if r.get("forward_return") is not None]
    scored_rets = [r["forward_return"] for r in rows if r["forward_return"] is not None]

    def line(label, rets):
        if not rets: return
        print(f"  {label:36} n={len(rets):3}  mean={statistics.mean(rets)*100:+7.1f}%  median={statistics.median(rets)*100:+7.1f}%")

    print("  Framework baskets:")
    line("STRICT_LONG basket",       strict_rets)
    line("LOOSE_LONG (incl strict)", long_rets)
    line("NOT-SHORT basket",         notshort_rets)
    line("SHORT basket (avoided)",   short_rets)
    print()
    print("  Baselines:")
    line("SCORED-ONLY basket",       scored_rets)
    line("FULL UNIVERSE (60 names)", universe_rets)
    print(f"  IJR same window:                          {IJR_RETURN*100:+.1f}%")

    if long_rets and universe_rets:
        alpha = statistics.mean(long_rets) - statistics.mean(universe_rets)
        alpha_ijr = statistics.mean(long_rets) - IJR_RETURN
        print()
        print(f"  ALPHA: LOOSE_LONG vs universe (60 distressed) = {alpha*100:+.1f} pp")
        print(f"  ALPHA: LOOSE_LONG vs IJR                       = {alpha_ijr*100:+.1f} pp")
    if short_rets and universe_rets:
        savg = statistics.mean(universe_rets) - statistics.mean(short_rets)
        print(f"  AVOIDANCE-ALPHA: skip SHORT vs universe       = {savg*100:+.1f} pp")

    # Comparison stat
    print()
    print("CONTRAST WITH TIER 1 (66-name distressed, 2025-05-15 → 2026-05-15)")
    print("  Tier 1 catastrophe recall: 93%")
    print("  Tier 1 LOOSE_LONG +64.6% / universe +7.0% / alpha +57.6 pp")
    print()
    print("INTERPRETATION GUIDE:")
    print("  - If Tier 3 catastrophe-recall >= 80% AND LOOSE_LONG alpha >= +20 pp:")
    print("    → in-cohort detection is durable; Tier 1 effect generalizes")
    print("    → within-distressed-cohort framework is real")
    print("  - If Tier 3 catastrophe-recall <= 50% OR LOOSE_LONG alpha ~ 0:")
    print("    → Tier 1 was window-specific (single-window artifact)")
    print("  - In between: nuanced — framework picks up signal but Tier 1 was inflated")

    out = HERE / "synthesis.json"
    out.write_text(json.dumps(rows, indent=2))
    print(f"\nSaved synthesis to {out}")


if __name__ == "__main__":
    main()
