"""Pilot 5 pair-trade P&L computation, using the mini free price feed.

For each of the 3 verified-SELL obligors (Ascension, UPMC, Trinity) plus the 2
EXCLUDE obligors (Steward, Tower), compute estimated pair-trade P&L vs MUB
(broad muni benchmark) for the Dec 2022 → Mar 2025 holding period.

OUTPUT
  /verticals/muni_credit/outputs/pilot_5_pair_trade_results.json
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from feed import etf_total_return, bval_aaa_yield, pair_trade_pnl

HERE = Path(__file__).parent
CACHE_DIR = HERE.parent / "data" / "_price_cache"
OUTPUT = HERE.parent / "outputs" / "pilot_5_pair_trade_results.json"

START = "2022-12-30"
END = "2025-03-31"


# Per-obligor inputs derived from VERIFIED outcomes (per_obligor/*.json)
# Literature-anchored spread widening estimates per outcome class:
#   AFFIRM_NEGATIVE_OUTLOOK (1-3 agencies):  +5 to +15 bps
#   DOWNGRADE (1 notch):                     +20 to +50 bps
#   MULTI_DOWNGRADE:                         +50 to +150 bps
#   DEFAULT / distressed exchange:           +500 to +2000 bps (HIGH NOISE)
#   AFFIRM_STABLE:                           -10 to +10 bps
PILOT_OBLIGORS = [
    {
        "name": "Ascension Health",
        "model_signal": "STRONG_SELL",
        "model_notches": -5.2,
        "verified_outcome_class": "AFFIRM_NEGATIVE_OUTLOOK",
        "verified_outcome_detail": "Moody's outlook → negative Sept 2024",
        "duration": 8.0,  # representative for 10-15y hospital muni
        "estimated_spread_widening_bps": 10,  # mid of 5-15 range, ONE agency outlook neg
        "use_in_basket": True,
        "side": "SHORT",
    },
    {
        "name": "UPMC",
        "model_signal": "STRONG_SELL",
        "model_notches": -3.5,
        "verified_outcome_class": "AFFIRM_NEGATIVE_OUTLOOK",
        "verified_outcome_detail": "Fitch outlook → negative March 2025 (1 of 3 agencies)",
        "duration": 8.0,
        "estimated_spread_widening_bps": 5,  # lower than Ascension since only 1 agency moved
        "use_in_basket": True,
        "side": "SHORT",
    },
    {
        "name": "Trinity Health (Michigan)",
        "model_signal": "STRONG_SELL",
        "model_notches": -2.6,
        "verified_outcome_class": "AFFIRM_STABLE",
        "verified_outcome_detail": "All 3 agencies affirmed stable",
        "duration": 8.0,
        "estimated_spread_widening_bps": 0,  # actually stable; model was wrong here
        "use_in_basket": True,
        "side": "SHORT",
    },
    {
        "name": "Steward Health Care",
        "model_signal": "STRONG_BUY",
        "model_notches": +17.2,
        "verified_outcome_class": "DEFAULT (Ch 11 2024-05-06)",
        "verified_outcome_detail": "No public muni bonds — Cerberus-owned LBO. Excluded by universe rule.",
        "duration": None,
        "estimated_spread_widening_bps": None,
        "use_in_basket": False,
        "excluded_reason": "NO_PUBLIC_BONDS",
        "side": "EXCLUDE",
    },
    {
        "name": "Tower Health",
        "model_signal": "STRONG_BUY",
        "model_notches": +6.4,
        "verified_outcome_class": "DEFAULT (S&P D + distressed exchange Sept 2024)",
        "verified_outcome_detail": "S&P took 7 actions BB- → D over 21 months. Bond CUSIP 08451PAG6 went from ~70 to ~84 area during exchange. Distressed exchange WAS orderly.",
        "duration": 4.0,  # shorter for the 2027 maturity
        "estimated_spread_widening_bps": -1500,  # NEGATIVE: bond actually rallied during exchange (price 70→84 ≈ +20% / 4 dur ≈ -500 bps tightening). The override saved you from a SHORT here.
        "use_in_basket": False,
        "excluded_reason": "SYSTEM_DISTRESS_OVERRIDE (correctly excluded; bonds existed but were highly distressed)",
        "side": "EXCLUDE",
    },
]


def main():
    print(f"PILOT 5 PAIR TRADE — {START} → {END}")
    print("=" * 80)

    # Get baseline ETF & AAA yields
    print("\n=== BASELINE FEEDS ===")
    bench = etf_total_return("MUB", START, END, cache_dir=CACHE_DIR)
    print(f"MUB (broad muni AA-tier benchmark): {bench['start_date_actual']} ${bench['start_price_adj']:.2f} → "
          f"{bench['end_date_actual']} ${bench['end_price_adj']:.2f} = "
          f"{bench['total_return']*100:+.2f}% TR")

    hyd = etf_total_return("HYD", START, END, cache_dir=CACHE_DIR)
    print(f"HYD (high-yield muni — for distressed proxy):                            "
          f"{hyd['total_return']*100:+.2f}% TR")

    aaa_start = bval_aaa_yield(START, tenor_years=10)
    aaa_end = bval_aaa_yield(END, tenor_years=10)
    aaa_change_bps = (aaa_end['yield_pct'] - aaa_start['yield_pct']) * 100
    print(f"BVAL AAA 10Y: {aaa_start['yield_pct']:.3f}% → {aaa_end['yield_pct']:.3f}% = "
          f"{aaa_change_bps:+.1f} bps")

    # Compute basket trade
    print("\n=== EVEN-WEIGHTED SHORT BASKET (excluded names follow override rule) ===")
    short_basket = [o for o in PILOT_OBLIGORS if o["use_in_basket"]]
    print(f"In basket ({len(short_basket)} names): {[o['name'] for o in short_basket]}")
    print(f"Excluded ({len([o for o in PILOT_OBLIGORS if not o['use_in_basket']])} names): "
          f"{[(o['name'], o['excluded_reason']) for o in PILOT_OBLIGORS if not o['use_in_basket']]}")

    result = pair_trade_pnl(
        short_obligors=[{
            "name": o["name"],
            "duration": o["duration"],
            "estimated_spread_widening_bps": o["estimated_spread_widening_bps"]
        } for o in short_basket],
        long_benchmark="MUB",
        start_date=START,
        end_date=END,
        transaction_cost_bps=20,
        cache_dir=CACHE_DIR,
    )

    print(f"\n=== RESULT ===")
    print(f"Benchmark (LONG MUB): {result['benchmark_total_return']*100:+.2f}% over {result['years']:.2f} years")
    print(f"\nPer-name short P&L (gross):")
    for p in result["per_name"]:
        print(f"  {p['obligor']:<30} duration={p['duration']}, spread_widening={p['estimated_spread_widening_bps']} bps")
        print(f"    benchmark TR: {p['benchmark_total_return']*100:+.2f}%, est own TR: {p['own_total_return_est']*100:+.2f}%, pair P&L: {p['pair_pnl_gross']*100:+.2f}%")
    print(f"\nAVERAGE PAIR TRADE P&L (gross): {result['avg_pair_pnl_gross_pct']:+.2f}%")
    print(f"AVERAGE PAIR TRADE P&L (net of {result['transaction_cost_bps']} bps t-costs): {result['avg_pair_pnl_net_pct']:+.2f}%")
    print(f"ANNUALIZED GROSS:  {result['annualized_gross_pct']:+.2f}%")
    print(f"ANNUALIZED NET:    {result['annualized_net_pct']:+.2f}%")

    # Now also compute: what if we IGNORED the override and went SHORT Tower?
    print(f"\n=== COUNTERFACTUAL: What if override didn't exist and we shorted Tower Health? ===")
    tower = [o for o in PILOT_OBLIGORS if o["name"] == "Tower Health"][0]
    print(f"  Tower bond (CUSIP 08451PAG6) went from ~70 → ~84 (+20% price ≈ -500 bps yield over 4-dur)")
    print(f"  If we'd SHORTED Tower at par-equivalent, we'd have LOST ~20% over the period")
    print(f"  This validates the system_distress_axis override: excluding Tower SAVED ~20% on that position")
    print(f"  Even though Tower technically 'defaulted' (S&P D), the distressed exchange was ORDERLY")
    print(f"  and bondholders received recovery > pre-exchange market price.")

    # Save
    OUTPUT.parent.mkdir(exist_ok=True)
    full_result = {
        "snapshot_date": START,
        "endpoint_date": END,
        "computed_at": datetime.utcnow().isoformat() + "Z",
        "obligor_inputs": PILOT_OBLIGORS,
        "etf_data": {
            "MUB": bench,
            "HYD": hyd,
        },
        "bval_aaa_10y": {
            "start": aaa_start,
            "end": aaa_end,
            "change_bps": aaa_change_bps,
        },
        "pair_trade_result": result,
        "_data_quality_notes": [
            "ETF data: HIGH confidence (Yahoo Finance public REST)",
            "BVAL AAA: HIGH confidence (MSRB-published PDFs)",
            "Per-obligor spread widening: MEDIUM-LOW confidence (literature estimates only)",
            "Bond-level CUSIP prices: NOT MEASURED (EMMA blocks programmatic access)",
            "N=3 in-basket — pilot only, not a backtest",
        ],
    }
    OUTPUT.write_text(json.dumps(full_result, indent=2))
    print(f"\nSaved: {OUTPUT}")


if __name__ == "__main__":
    main()
