"""bond_dominance — relative-value FLOOR test for same-country EM-equity political-risk premiums.

You can harvest a country's political/sovereign risk two ways: the SENIOR hard-currency sovereign bond
(its spread over UST) or the JUNIOR equity (its political-component premium). Equity is subordinated and
bears MORE in a stress (dilution + the operational hit + a deeper drawdown), so to be worth the junior seat
it must pay the bond spread PLUS a subordination cushion. If the equity's political premium is below that
floor, the BOND DOMINATES — buy the senior claim, pass the equity *as a premium-harvest*. (You may still own
the equity as a COMPOUNDER on its own merits — the bond can't give you the ROE/book-value growth — but that
is a separate, fair-value thesis, not a premium-harvest edge.)

TWO things this is NOT, and one trap to avoid:
- It is NOT the alpha/edge test. Edge = is the priced premium OVERBLOWN vs warranted (a separate check).
  A name can CLEAR the bond floor (pays more than the bond) yet have NO edge (premium ≈ warranted) — e.g. TBC.
- Compare the equity's POLITICAL-COMPONENT premium (after debiting the NON-political warranted discounts —
  ROE gap vs a clean peer, execution/Uzbekistan, multiple), NOT the whole implied-CoE premium.
- TRAP (made once): do NOT compare the residual alpha GAP to the bond spread — that's mixing a mispricing
  (bps of edge) with a risk premium (bps of compensation). Compare LEVEL-to-LEVEL.

  python3 -m desk.bond_dominance        # worked example (TBC)
"""
from __future__ import annotations


def bond_dominance(equity_political_premium_bps: float, sovereign_spread_bps: float,
                   cushion_mult: float = 2.0, cushion_add_bps: float = 200.0) -> dict:
    """The equity must pay the sovereign spread × cushion_mult (or +cushion_add, whichever is larger) to be
    worth the junior seat. cushion ~2x reflects that equity bears roughly 2x the loss-given-political-event."""
    floor = max(cushion_mult * sovereign_spread_bps, sovereign_spread_bps + cushion_add_bps)
    if equity_political_premium_bps < sovereign_spread_bps:
        verdict = "BOND_DOMINATES"      # equity pays LESS than the senior bond for the same risk -> pass equity, buy bond
        note = "equity pays less than the senior bond — strictly buy the bond, pass the equity as a premium-harvest"
    elif equity_political_premium_bps < floor:
        verdict = "MARGINAL"            # clears the bond but not the juniority cushion -> prefer the bond
        note = "clears the bond spread but not the subordination cushion — prefer the bond unless you want the compounding"
    else:
        verdict = "EQUITY_CLEARS"       # adequately over-compensates juniority -> ownable as a premium harvest
        note = "clears the bond + cushion — the equity adequately pays for its junior seat (still judge EDGE separately)"
    excess = equity_political_premium_bps - sovereign_spread_bps
    return {"equity_political_premium_bps": equity_political_premium_bps, "sovereign_spread_bps": sovereign_spread_bps,
            "subordination_floor_bps": round(floor), "excess_over_bond_bps": round(excess),
            "clears_floor": equity_political_premium_bps >= floor, "verdict": verdict, "note": note,
            "reminder": "bond-dominance != edge. EDGE = priced political premium OVERBLOWN vs warranted (run separately)."}


if __name__ == "__main__":
    import json
    # TBC: equity political-component premium ~470-590bps (mid 530); Georgia sovereign USD spread ~152bps.
    print(json.dumps(bond_dominance(530, 152), indent=1))
    print("\n# counter-example — if the equity political premium were only 120bps (< the 152bps bond):")
    print(json.dumps(bond_dominance(120, 152), indent=1))
