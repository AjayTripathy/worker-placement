"""Synthesize Tier 2 / boring-middle backtest results.

Same pattern as the Tier 1 synthesize.py: reads each scores/pilot_<TICKER>.json,
runs deterministic composite recompute, joins with forward returns from
_unblinded/tier2_test_set.json, and computes basket P&L.

Run:
    python3 verticals/public_co/data/_backtest/boring_middle_2025_05/synthesize.py
"""
import json
import statistics
from pathlib import Path

HERE = Path(__file__).parent
SCORES = HERE / "scores"
TEST_SET = HERE / "_unblinded" / "tier2_test_set.json"

SEV_W = {
    "PASS": 0,
    "UNVERIFIABLE": 0,
    "MODERATE_UNDERDELIVERY": 1,
    "SEVERE_UNDERDELIVERY": 2,
    "RED_FLAG_NEGATIVE": 3,
}

# IJR same-window (2025-05-15 → 2026-05-15)
IJR_RETURN = (134.94 / 105.256) - 1  # ≈ +28.2%


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
            "drawdown_2025_05_15": ts.get("drawdown_2025_05_15"),
            "summary": d.get("summary", "")[:500],
        })
    rows.sort(key=lambda x: -x["composite_recomputed"])

    print("=" * 96)
    print(f"TIER 2 / BORING-MIDDLE BACKTEST — {len(rows)} pilots (target 50)")
    print(f"  Cutoff: 2025-05-15  |  Measurement: 2026-05-15  |  IJR: {IJR_RETURN*100:+.1f}%")
    print("=" * 96)
    print()
    print(f"{'TK':6} {'comp':>5}  {'tier':12}  {'fwd':>8}  {'sector':20}  {'sev':18}")
    print("-" * 96)
    for r in rows:
        fwd = r["forward_return"]
        fwd_s = f"{fwd*100:+.1f}%" if fwd is not None else "  null"
        sc = r["sev_counts"]
        sev = f"P{sc['PASS']}/M{sc['MODERATE_UNDERDELIVERY']}/S{sc['SEVERE_UNDERDELIVERY']}/R{sc['RED_FLAG_NEGATIVE']}/U{sc['UNVERIFIABLE']}"
        print(f"{r['ticker']:6} {r['composite_recomputed']:>5.3f}  {r['tier']:12}  {fwd_s:>8}  {(r['sector'] or '')[:20]:20}  {sev:18}")

    print()
    print("=" * 96)
    print("BASKET P&L vs IJR / universe")
    print("=" * 96)
    short_rets = [r["forward_return"] for r in rows if r["tier"] == "SHORT" and r["forward_return"] is not None]
    long_rets = [r["forward_return"] for r in rows if r["tier"] in ("STRICT_LONG", "LOOSE_LONG") and r["forward_return"] is not None]
    strict_rets = [r["forward_return"] for r in rows if r["tier"] == "STRICT_LONG" and r["forward_return"] is not None]
    notshort_rets = [r["forward_return"] for r in rows if r["tier"] != "SHORT" and r["forward_return"] is not None]
    universe_rets = [r["forward_return"] for r in test_set.values() if r.get("forward_return") is not None]
    scored_rets = [r["forward_return"] for r in rows if r["forward_return"] is not None]

    def line(label, rets):
        if not rets:
            return
        print(f"  {label:36} n={len(rets):3}  mean={statistics.mean(rets)*100:+7.1f}%  median={statistics.median(rets)*100:+7.1f}%")

    print("  Framework baskets (scored only):")
    line("STRICT_LONG basket",       strict_rets)
    line("LOOSE_LONG (incl strict)", long_rets)
    line("NOT-SHORT basket",         notshort_rets)
    line("SHORT basket (avoided)",   short_rets)
    print()
    print("  Baselines:")
    line("SCORED-ONLY basket",       scored_rets)
    line("FULL UNIVERSE (50 names)", universe_rets)
    print(f"  IJR same window:                          {IJR_RETURN*100:+.1f}%")

    if long_rets and universe_rets:
        alpha_universe = statistics.mean(long_rets) - statistics.mean(universe_rets)
        alpha_ijr = statistics.mean(long_rets) - IJR_RETURN
        print()
        print(f"  ALPHA: LOOSE_LONG vs universe (50 boring middle) = {alpha_universe*100:+.1f} pp")
        print(f"  ALPHA: LOOSE_LONG vs IJR                          = {alpha_ijr*100:+.1f} pp")
    if short_rets and universe_rets:
        short_alpha = statistics.mean(universe_rets) - statistics.mean(short_rets)
        print(f"  AVOIDANCE-ALPHA: skip SHORT vs universe          = {short_alpha*100:+.1f} pp")

    # Comparison to Tier 1
    print()
    print("CONTRAST WITH TIER 1 (distressed cohort)")
    print("  Tier 1 LOOSE_LONG (66 names, distressed):  n=13, mean=+64.6%, alpha vs universe +57.6 pp")
    print(f"  Tier 2 LOOSE_LONG ({len(rows)} names, boring middle): see above")
    print("  Key question: does the +57 pp Tier 1 alpha survive on a non-distressed cohort?")

    out = HERE / "synthesis.json"
    out.write_text(json.dumps(rows, indent=2))
    print(f"\nSaved synthesis to {out}")


if __name__ == "__main__":
    main()
