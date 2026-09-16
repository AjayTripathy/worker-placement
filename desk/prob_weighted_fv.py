"""prob_weighted_fv — connect catalyst predictions to PRICING, with the anti-optimism discipline.

The lesson from the 3-of-4 edge collapses (TBC/AST/BAH): "we're bullish" is NOT edge unless our probability
DIVERGES from what the price already pays for. This makes that check systematic for catalyst names.

3-SCENARIO model (bull/base/bear) — a BINARY (bull-vs-bear) model over-states edge because it forces every
non-bull outcome to the bear anchor and ignores the most likely 'base / muddle-through' case. We condition on
a shared base probability (p_base) and let the disagreement live in the bull-vs-bear tail split:

  market_implied_p_bull = clip( (price − p_base·base − (1−p_base)·bear) / (bull − bear), 0 .. 1−p_base )
        # given the agreed p_base, what bull-probability is the PRICE paying for
  prob_weighted_fv      = p_bull·bull + p_base·base + (1−p_bull−p_base)·bear        # OUR expected fair value
  edge_pp               = (our p_bull − market_implied_p_bull)·100                  # ONLY this gap is edge
  upside_to_pwfv        = prob_weighted_fv/price − 1
A catalyst we LIKE only moves the entry above the pure-base band when edge_pp is materially positive.
NOTE: catalyst_predictions 'p_favorable' is NOT p_bull (it conflates bull + lean) — set the explicit
{p_bull, p_base} split per name in catalyst_scenarios.json; until then we show market-implied for reference.
"""
from __future__ import annotations

DEFAULT_P_BASE = 0.5     # reference muddle-through weight used when we have no curated split (for market-implied only)


def market_implied_p_bull(px, bear, base, bull, p_base) -> float | None:
    if None in (px, bear, base, bull, p_base) or bull == bear:
        return None
    raw = (px - p_base * base - (1 - p_base) * bear) / (bull - bear)
    return max(0.0, min(1.0 - p_base, raw))


def prob_weighted_fv(p_bull, p_base, bear, base, bull) -> float:
    p_bull = max(0.0, min(p_bull, 1.0 - p_base))
    return p_bull * bull + p_base * base + (1 - p_bull - p_base) * bear


def verdict(edge_pp) -> str:
    if edge_pp is None:
        return "NO_VIEW"          # scenario FVs only — market-implied shown for reference; set our {p_bull,p_base} to grade
    if edge_pp >= 8:
        return "UNDERPRICED"      # our P(bull) >> market's → the catalyst is cheap; conviction CAN move the entry up
    if edge_pp <= -8:
        return "OVERPRICED"       # market pays for more than we believe → fade / wait
    return "FAIR"                 # our view ≈ priced → NO catalyst edge; hold the pure-base entry discipline


def compute_one(px, bear, base, bull, p_bull=None, p_base=None) -> dict:
    pb = p_base if p_base is not None else DEFAULT_P_BASE
    mip = market_implied_p_bull(px, bear, base, bull, pb)
    pwfv = prob_weighted_fv(p_bull, pb, bear, base, bull) if p_bull is not None else None
    edge = (round((p_bull - mip) * 100, 1) if (p_bull is not None and mip is not None) else None)
    return {"px": px, "bear": bear, "base": base, "bull": bull,
            "our_p_bull": p_bull, "p_base": (p_base if p_base is not None else None),
            "market_implied_p_bull": (round(mip, 3) if mip is not None else None),
            "prob_weighted_fv": (round(pwfv, 2) if pwfv is not None else None),
            "upside_to_pwfv_pct": (round((pwfv / px - 1) * 100, 1) if (pwfv and px) else None),
            "upside_to_base_pct": (round((base / px - 1) * 100, 1) if (base and px) else None),
            "edge_pp": edge, "verdict": verdict(edge)}


if __name__ == "__main__":
    import json
    # COSMECCA: bear 40k / base 67k / bull 110k, live 69,200. Our DD split: p_bull 0.25, p_base 0.55 (p_bear 0.20).
    print("our split (p_bull 0.25, p_base 0.55):")
    print(json.dumps(compute_one(69200, 40000, 67000, 110000, 0.25, 0.55), indent=1))
