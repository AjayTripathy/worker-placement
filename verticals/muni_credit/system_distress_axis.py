"""System-level debt distress axis — safety override for the composite score.

WHY THIS EXISTS

The 4-axis HCRIS + CAFR + MEN composite caught 24/25 STRONG_SELL signals
in the forward backtest, but had 3 architectural misses on the BUY side:

  Tower Health    (CCC- explicit, our STRONG_BUY +6.4 notches → MULTI_DOWNGRADE)
  Steward Health  (D explicit, our STRONG_BUY +17.2 notches → DEFAULT)
  Prospect Medical (D explicit, our STRONG_BUY +16.8 notches → DEFAULT)

All three share the same architecture flaw: HCRIS captures facility-level
operating performance, which can be perfectly healthy while the parent's
system-level debt structure is collapsing. Steward's hospitals were running
positive margins right up until the Chapter 11 filing.

This module is a SAFETY OVERRIDE that prevents the composite from ever
generating a BUY signal on a distressed obligor, regardless of HCRIS data.

SIGNAL TIERS (output)

  CLEAN              — no distress indicators; composite score applies normally
  WATCH              — early warning; composite SELL signals amplified, BUY signals
                       reduced to CONSENSUS
  DISTRESSED         — explicit rating in BB tier OR moderate MEN history;
                       all BUY signals forbidden, model defaults to AVOID
  SEVERE_DISTRESSED  — explicit rating in B tier OR severe MEN history;
                       all signals override to SHORT
  DEFAULTED          — explicit rating CCC+ or worse OR bankruptcy MEN;
                       all signals override to MAX_SHORT / EXCLUDE

INPUTS

  obligor_name        — for MEN lookup
  explicit_rating     — consensus letter rating from agencies (e.g., "AA-")
  snapshot_date       — ISO YYYY-MM-DD for MEN window
  current_spread_bps  — optional: bond spread to MMD AAA (if > 200bps wide of
                        expected, market is pricing distress)

USAGE

  result = system_distress(obligor_name, explicit_letter, snapshot_date)
  if result["tier"] in ("DISTRESSED", "SEVERE_DISTRESSED", "DEFAULTED"):
      # Override composite BUY signals
      override_action = result["override_action"]
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import date, timedelta
from typing import Optional

HERE = Path(__file__).parent
MEN_FILE = HERE / "data" / "emma_material_events.json"

# Explicit-rating-based prior distress tiers
RATING_TIER_OVERRIDES = {
    # Letter → tier override
    # AAA / AA / A → CLEAN (no override)
    "BBB+": "CLEAN", "BBB": "CLEAN", "BBB-": "CLEAN",
    "BB+": "WATCH", "BB": "DISTRESSED", "BB-": "DISTRESSED",
    "B+": "SEVERE_DISTRESSED", "B": "SEVERE_DISTRESSED", "B-": "SEVERE_DISTRESSED",
    "CCC+": "DEFAULTED", "CCC": "DEFAULTED", "CCC-": "DEFAULTED",
    "CC": "DEFAULTED", "C": "DEFAULTED", "D": "DEFAULTED",
}

# MEN event codes → severity weight for distress
MEN_DISTRESS_CODES = {
    "1.01": "DISTRESSED",       # payment delinquency
    "1.02": "SEVERE_DISTRESSED", # non-payment-related default
    "1.03": "DEFAULTED",        # bankruptcy
    "2.04": "DISTRESSED",       # covenant violation / modification to bondholder rights
    "3.02": "DISTRESSED",       # taxability determination
}

# Action map per tier
OVERRIDE_ACTION = {
    "CLEAN":              "USE_COMPOSITE_NORMALLY",
    "WATCH":              "REDUCE_BUY_TO_CONSENSUS",
    "DISTRESSED":         "FORBID_BUY",         # composite SELL signals amplified; no BUY
    "SEVERE_DISTRESSED":  "OVERRIDE_TO_SHORT",   # regardless of composite, this is a SHORT
    "DEFAULTED":          "EXCLUDE_OR_DEEP_SHORT", # exclude from book entirely OR deep distressed-debt trade only
}


def _tier_rank(tier: str) -> int:
    return {"CLEAN": 0, "WATCH": 1, "DISTRESSED": 2,
            "SEVERE_DISTRESSED": 3, "DEFAULTED": 4}.get(tier, 0)


def _max_tier(a: str, b: str) -> str:
    return a if _tier_rank(a) >= _tier_rank(b) else b


def _load_mens() -> list[dict]:
    if not MEN_FILE.exists():
        return []
    return json.loads(MEN_FILE.read_text()).get("events", [])


def system_distress(
    obligor_name: str,
    explicit_letter: Optional[str],
    snapshot_date: str,
    *,
    current_spread_bps: Optional[float] = None,
    expected_spread_bps: Optional[float] = None,
    lookback_days: int = 730,
) -> dict:
    """Compute system-level debt distress tier.

    Returns:
      {
        "tier":              CLEAN / WATCH / DISTRESSED / SEVERE_DISTRESSED / DEFAULTED,
        "override_action":   action string (see OVERRIDE_ACTION map),
        "reasons":           list of contributing signals,
        "drivers": {
            "rating_tier":   tier from explicit rating,
            "men_tier":      tier from MEN history,
            "spread_tier":   tier from bond pricing (if provided),
        }
      }
    """
    reasons = []
    drivers = {}

    # Layer 1: Rating-based prior
    rating_tier = "CLEAN"
    if explicit_letter and explicit_letter in RATING_TIER_OVERRIDES:
        rating_tier = RATING_TIER_OVERRIDES[explicit_letter]
        if rating_tier != "CLEAN":
            reasons.append(f"explicit rating {explicit_letter} → {rating_tier}")
    drivers["rating_tier"] = rating_tier

    # Layer 2: MEN-based signal
    men_tier = "CLEAN"
    snap = date.fromisoformat(snapshot_date[:10])
    floor = snap - timedelta(days=lookback_days)
    mens = _load_mens()
    obligor_l = obligor_name.lower()
    matched = []
    for e in mens:
        e_obligor = (e.get("obligor") or "").lower()
        if obligor_l not in e_obligor and e_obligor not in obligor_l:
            continue
        try:
            ed = date.fromisoformat(e.get("filing_date","")[:10])
        except Exception:
            continue
        if floor <= ed <= snap:
            matched.append(e)

    matched_codes = []
    for e in matched:
        code = e.get("event_code", "")
        matched_codes.append(code)
        event_tier = MEN_DISTRESS_CODES.get(code)
        if event_tier:
            men_tier = _max_tier(men_tier, event_tier)
    if matched and men_tier != "CLEAN":
        reasons.append(f"MEN: {len(matched)} events incl codes {sorted(set(matched_codes))} → {men_tier}")
    drivers["men_tier"] = men_tier
    drivers["men_events_count"] = len(matched)

    # Layer 3: Bond pricing signal (optional)
    spread_tier = "CLEAN"
    if current_spread_bps is not None and expected_spread_bps is not None:
        excess_bps = current_spread_bps - expected_spread_bps
        if excess_bps >= 500:
            spread_tier = "DEFAULTED"
            reasons.append(f"bond spread +{excess_bps:.0f} bps wide of expected → DEFAULTED")
        elif excess_bps >= 250:
            spread_tier = "SEVERE_DISTRESSED"
            reasons.append(f"bond spread +{excess_bps:.0f} bps wide of expected → SEVERE_DISTRESSED")
        elif excess_bps >= 150:
            spread_tier = "DISTRESSED"
            reasons.append(f"bond spread +{excess_bps:.0f} bps wide of expected → DISTRESSED")
        elif excess_bps >= 75:
            spread_tier = "WATCH"
            reasons.append(f"bond spread +{excess_bps:.0f} bps wide of expected → WATCH")
    drivers["spread_tier"] = spread_tier

    # Combine: take MAX tier across the 3 layers
    final_tier = _max_tier(_max_tier(rating_tier, men_tier), spread_tier)

    return {
        "tier":             final_tier,
        "override_action":  OVERRIDE_ACTION[final_tier],
        "reasons":          reasons or ["no distress indicators"],
        "drivers":          drivers,
    }


def apply_override(composite_signal: str, distress_tier: str) -> str:
    """Apply system-distress override to a composite signal.

    Rules:
      DEFAULTED          → always "EXCLUDE_OR_DEEP_SHORT"
      SEVERE_DISTRESSED  → all signals become "OVERRIDE_TO_SHORT"
      DISTRESSED         → BUY signals become "CONSENSUS"; SELL signals amplified
      WATCH              → BUY signals reduced to CONSENSUS; SELL unchanged
      CLEAN              → no override
    """
    if distress_tier == "DEFAULTED":
        return "EXCLUDE_OR_DEEP_SHORT"
    if distress_tier == "SEVERE_DISTRESSED":
        return "OVERRIDE_TO_SHORT"
    if distress_tier == "DISTRESSED":
        if "BUY" in composite_signal:
            return "CONSENSUS_OVERRIDE"  # BUY signals forbidden
        return composite_signal  # SELL signals pass through
    if distress_tier == "WATCH":
        if composite_signal == "STRONG_BUY":
            return "WEAK_BUY"
        if composite_signal == "WEAK_BUY":
            return "CONSENSUS"
        return composite_signal
    return composite_signal


if __name__ == "__main__":
    import sys
    obligor = sys.argv[1] if len(sys.argv) > 1 else "Tower Health"
    rating = sys.argv[2] if len(sys.argv) > 2 else "CCC-"
    snapshot = sys.argv[3] if len(sys.argv) > 3 else "2022-12-31"
    res = system_distress(obligor, rating, snapshot)
    print(json.dumps(res, indent=2))
