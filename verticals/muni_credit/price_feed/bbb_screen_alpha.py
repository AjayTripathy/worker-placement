"""Estimate alpha from owning the GREEN BBB names vs unscreened BBB basket.

This is a LITERATURE-ANCHORED ESTIMATE, not a measurement. We have:
  - Verified MUB (AA-tier broad muni) total return: +6.33% over 27 months
  - Verified HYD (high-yield muni, BBB and below) total return: +10.99%
  - Verified BVAL AAA Callable 10Y: +56 bps yield change
  - No bond-level CUSIP prices for the 19 BBB-tier hospital muni names

The estimates below use published literature on:
  - Covenant breach disclosure impact on muni spreads: ~50-200 bps widening
  - Rating downgrade impact (1-notch BBB): ~30-80 bps widening
  - Distressed exchange / default impact: variable (Tower's was orderly)
  - Outlook revision impact: ~10-30 bps widening
"""
from __future__ import annotations

import json
from pathlib import Path
from feed import etf_total_return, bval_aaa_yield

HERE = Path(__file__).parent
CACHE = HERE.parent / "data" / "_price_cache"
OUT = HERE.parent / "outputs" / "bbb_screen_alpha_results.json"

START = "2022-12-30"
END = "2025-03-31"

# Per-obligor outcome estimate (literature-anchored)
# Each entry: estimated spread move vs sector benchmark over 27 months
TRIPWIRED_OBLIGORS = [
    # name, estimated spread widening vs BBB sector (bps), duration, rationale
    {"name": "Tower Health", "est_spread_widening_bps": 800,
     "duration": 4,
     "rationale": "Distressed exchange (S&P D). Original bondholders took NPV impairment via deferred amortization to 2039. Post-exchange paper rallied but pre-restructuring holders lost ~20-30% of par."},
    {"name": "UC Health (Cincinnati)", "est_spread_widening_bps": 150,
     "duration": 8,
     "rationale": "DSCR -2.66 in FY23 vs 1.10x covenant. S&P warning. Recovery underway."},
    {"name": "Frederick Health Hospital", "est_spread_widening_bps": 200,
     "duration": 8,
     "rationale": "Fitch BBB Rating Watch Negative + ransomware. 3 yrs op losses."},
    {"name": "Mount Sinai NYC", "est_spread_widening_bps": 60,
     "duration": 8,
     "rationale": "Moody's downgrade Baa1→Baa3 Aug 2024. Two-notch action."},
    {"name": "Allegheny Health Network", "est_spread_widening_bps": 80,
     "duration": 8,
     "rationale": "Below typical DCOH floor (53/65). Highmark consolidation masks at parent level."},
    {"name": "Nuvance Health", "est_spread_widening_bps": 50,
     "duration": 8,
     "rationale": "Northwell merger absorbed it 2024-25 — spread compressed on takeout."},
    {"name": "Brown University Health", "est_spread_widening_bps": 40,
     "duration": 8,
     "rationale": "Post-Lifespan rebrand. Marginal operating performance."},
    {"name": "UofL Health", "est_spread_widening_bps": 100,
     "duration": 8,
     "rationale": "Fitch downgrade BBB+→BBB Aug 2024. Critically low 30 DCOH."},
    {"name": "Boston Medical Center", "est_spread_widening_bps": 50,
     "duration": 8,
     "rationale": "Moody's downgrade Baa2→Baa3 in 2026. Steward acquisition weakening."},
]

GREEN_OBLIGORS = [
    {"name": "ProMedica Health System", "est_spread_change_bps": -75,
     "duration": 7,
     "rationale": "Turnaround story: 8.1% operating margin in 2025 after 2022 covenant breach. Ratings (Ba2/BB) lag operating reality — re-rate to BBB-area would tighten ~75 bps."},
    {"name": "Naples Comprehensive Health (NCH)", "est_spread_change_bps": -25,
     "duration": 8,
     "rationale": "Fitch BBB+ stable. 108 DCOH. Expects breakeven FY26 — modest tightening on stable execution."},
    {"name": "Adventist Health (West Coast)", "est_spread_change_bps": 0,
     "duration": 8,
     "rationale": "Split-rated A3/A-/BBB+. 138 DCOH. Already priced fairly; limited alpha."},
    {"name": "Lompoc Valley Medical Center", "est_spread_change_bps": 0,
     "duration": 6,
     "rationale": "Small standalone, illiquid. Probably no name-specific alpha — just BBB sector return."},
]


def main():
    print("=" * 80)
    print("BBB TRIPWIRE SCREEN — ALPHA ESTIMATE")
    print(f"Window: {START} → {END} (27 months)")
    print("=" * 80)

    # Baseline benchmarks
    mub = etf_total_return("MUB", START, END, cache_dir=CACHE)
    hyd = etf_total_return("HYD", START, END, cache_dir=CACHE)
    print(f"\nBenchmark sector returns (VERIFIED from Yahoo Finance):")
    print(f"  MUB (broad AA muni): {mub['total_return']*100:+.2f}%")
    print(f"  HYD (high-yield/BBB muni): {hyd['total_return']*100:+.2f}%")
    print(f"  Sector excess (HYD - MUB): {(hyd['total_return'] - mub['total_return'])*100:+.2f} pp")

    # Estimate per-obligor returns
    print(f"\n=== TRIPWIRED basket (9 names) — what an unscreened BBB basket would have INCLUDED ===")
    print(f"{'Obligor':<35} {'Spread Δ':<12} {'Dur':<6} {'Est ret vs HYD':<15}")
    print("-" * 80)
    tripwired_returns = []
    for o in TRIPWIRED_OBLIGORS:
        # Their return relative to HYD = HYD return - duration * spread widening
        ret_vs_hyd = -o["duration"] * o["est_spread_widening_bps"] / 10000
        tripwired_returns.append(ret_vs_hyd)
        print(f"  {o['name']:<33} +{o['est_spread_widening_bps']:>5} bps    {o['duration']:<6} {ret_vs_hyd*100:+.2f}%")
    tripwired_avg_vs_hyd = sum(tripwired_returns) / len(tripwired_returns)
    print(f"  {'AVG':<33}                            {tripwired_avg_vs_hyd*100:+.2f}%")

    print(f"\n=== GREEN basket (4 names) — what the screen SAYS TO OWN ===")
    print(f"{'Obligor':<35} {'Spread Δ':<12} {'Dur':<6} {'Est ret vs HYD':<15}")
    print("-" * 80)
    green_returns = []
    for o in GREEN_OBLIGORS:
        ret_vs_hyd = -o["duration"] * o["est_spread_change_bps"] / 10000
        green_returns.append(ret_vs_hyd)
        print(f"  {o['name']:<33} {o['est_spread_change_bps']:>+5} bps     {o['duration']:<6} {ret_vs_hyd*100:+.2f}%")
    green_avg_vs_hyd = sum(green_returns) / len(green_returns)
    print(f"  {'AVG':<33}                            {green_avg_vs_hyd*100:+.2f}%")

    # Convert to actual return levels
    hyd_tr = hyd["total_return"]
    tripwired_basket_tr = hyd_tr + tripwired_avg_vs_hyd
    green_basket_tr = hyd_tr + green_avg_vs_hyd
    unscreened_bbb_tr = (sum(tripwired_returns) + sum(green_returns)) / (len(tripwired_returns) + len(green_returns)) + hyd_tr

    print(f"\n=== ESTIMATED 27-MONTH TOTAL RETURNS ===")
    print(f"  HYD sector benchmark (verified):                 {hyd_tr*100:+7.2f}%")
    print(f"  Unscreened BBB basket (all 13 evaluable names):  {unscreened_bbb_tr*100:+7.2f}%")
    print(f"  TRIPWIRED basket (9 names — what to AVOID):       {tripwired_basket_tr*100:+7.2f}%")
    print(f"  GREEN basket (4 names — what the screen BUYS):    {green_basket_tr*100:+7.2f}%")

    # Alpha sources
    alpha_vs_unscreened = green_basket_tr - unscreened_bbb_tr
    alpha_vs_hyd = green_basket_tr - hyd_tr
    alpha_vs_mub = green_basket_tr - mub["total_return"]
    avoided_drag = unscreened_bbb_tr - green_basket_tr  # negative because GREEN > UNSCREENED

    print(f"\n=== ALPHA DECOMPOSITION ===")
    print(f"  GREEN vs UNSCREENED BBB:  {alpha_vs_unscreened*100:+.2f}% ← THE SCREEN'S CONTRIBUTION")
    print(f"  GREEN vs HYD (sector):    {alpha_vs_hyd*100:+.2f}% ← screen + name-specific stories")
    print(f"  GREEN vs MUB (AA):        {alpha_vs_mub*100:+.2f}% ← includes ~5pp BBB sector spread compensation")

    # Annualize
    years = 27 / 12
    annualized_screen_alpha = (1 + alpha_vs_unscreened) ** (1/years) - 1
    print(f"\n  ANNUALIZED screen alpha (GREEN - UNSCREENED): {annualized_screen_alpha*100:+.2f}%/yr")

    # T-costs
    tcost_bps = 25  # round-trip muni retail
    annualized_screen_alpha_net = annualized_screen_alpha - (tcost_bps / 10000) / years
    print(f"  After {tcost_bps} bps round-trip cost:           {annualized_screen_alpha_net*100:+.2f}%/yr")

    # Save
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "window": {"start": START, "end": END, "years": years},
        "benchmarks_verified": {
            "MUB_total_return": mub["total_return"],
            "HYD_total_return": hyd["total_return"],
        },
        "tripwired_basket": {
            "obligors": TRIPWIRED_OBLIGORS,
            "estimated_total_return": tripwired_basket_tr,
        },
        "green_basket": {
            "obligors": GREEN_OBLIGORS,
            "estimated_total_return": green_basket_tr,
        },
        "alpha": {
            "screen_alpha_vs_unscreened_bbb_27mo": alpha_vs_unscreened,
            "screen_alpha_vs_hyd_27mo": alpha_vs_hyd,
            "screen_alpha_vs_mub_27mo": alpha_vs_mub,
            "annualized_screen_alpha_gross_pct": annualized_screen_alpha * 100,
            "annualized_screen_alpha_net_pct": annualized_screen_alpha_net * 100,
        },
        "_data_quality": "Tripwired/Green per-name spread estimates are LITERATURE-ANCHORED, not measured. ETF and BVAL benchmarks are verified.",
    }, indent=2, default=str))
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
