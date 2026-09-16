"""Dual-class voting concentration detector for corporate IPO DD.

FIRES when post-IPO voting structure concentrates control in a single
person / sponsor / founder group beyond a threshold.

Severity:
- RED: >75% voting control to single insider/sponsor + no sunset clause
- HIGH: 50-75% voting control OR >75% with sunset clause (>10yr)
- MEDIUM: 25-50% voting control OR multi-class with super-vote ratio >=10x
- LOW: minor super-voting structure, control diffuse

Fires on 4 of 5 IPOs scored 2026-05-28: Firefly (AE Industrial 37% but >50% via
SciTec proxies), Quantinuum (Honeywell 49.1%), Entrata (Silver Lake control via
Class B 10x), SpaceX (Musk 85.1% no independent chair).

## Data shape

{
  "company_name": "SpaceX",
  "voting_class_structure": {
    "class_a_votes_per_share": 1,
    "class_b_votes_per_share": 10,
    "class_c_votes_per_share": 0,
    "super_vote_ratio": 10
  },
  "top_holder_post_ipo_voting_pct": 85.1,
  "top_holder_name": "Elon Musk",
  "second_holder_post_ipo_voting_pct": null,
  "independent_chair": false,
  "is_controlled_company_under_listing_rule": true,

  # Mitigating factors (DETERMINISTIC SEVERITY DOWNGRADES — no LLM sentiment).
  # Default to most-conservative (no mitigation) when unknown.
  "sunset_clause_years": null,              # int years until sunset; null = perpetual (worst)
  "sunset_trigger": null,                   # "founder_death" | "below_threshold" | "fixed_date" | null
  "coordinated_voting_agreement_exists": false,  # multi-holder coordination ESCALATES
  "as_of_date": "2026-05-28",
  "source_url": "S-1 Cover + Principal Stockholders section"
}
"""
from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["corporate_ipo_dd"],
    "applies_universally": True,
    "summary": "Voting structure that concentrates control >25% in insiders post-IPO.",
}

CONTROL_RED_PCT = 75.0
CONTROL_HIGH_PCT = 50.0
CONTROL_MEDIUM_PCT = 25.0
SUPER_VOTE_RATIO_FIRE = 10.0


def evaluate(obligor_name: str, data: dict) -> dict:
    top_pct = data.get("top_holder_post_ipo_voting_pct")
    sunset = data.get("sunset_clause_years")
    has_sunset = sunset is not None and sunset <= 10
    sunset_trigger = data.get("sunset_trigger")
    coordinated = bool(data.get("coordinated_voting_agreement_exists"))
    structure = data.get("voting_class_structure") or {}
    super_ratio = structure.get("super_vote_ratio")
    is_controlled = data.get("is_controlled_company_under_listing_rule")
    indep_chair = data.get("independent_chair", True)

    if top_pct is None and super_ratio is None and not is_controlled:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if not isinstance(top_pct, (int, float)):
        top_pct = 0

    severity = None
    reason = None
    if top_pct >= CONTROL_RED_PCT and not has_sunset:
        severity = "RED"
        reason = "EXTREME_VOTING_CONCENTRATION_NO_SUNSET"
    elif top_pct >= CONTROL_RED_PCT:
        severity = "HIGH"
        reason = "EXTREME_VOTING_CONCENTRATION_WITH_SUNSET"
    elif top_pct >= CONTROL_HIGH_PCT:
        severity = "HIGH"
        reason = "MAJORITY_VOTING_CONCENTRATION"
    elif top_pct >= CONTROL_MEDIUM_PCT:
        severity = "MEDIUM"
        reason = "SIGNIFICANT_VOTING_CONCENTRATION"
    elif super_ratio and super_ratio >= SUPER_VOTE_RATIO_FIRE:
        severity = "MEDIUM"
        reason = "SUPER_VOTE_RATIO_HIGH"
    elif is_controlled:
        severity = "MEDIUM"
        reason = "CONTROLLED_COMPANY_LISTING_RULE"

    # Mitigating: a "below_threshold" sunset trigger is weaker than "fixed_date"
    # because the holder can sometimes keep voting above threshold indefinitely.
    # No downgrade; just annotate.
    sunset_weak = (sunset_trigger == "below_threshold")

    # Escalating modifiers
    if severity == "HIGH" and not indep_chair:
        severity = "RED"
        reason += "_NO_INDEPENDENT_CHAIR"
    if severity in ("HIGH", "MEDIUM") and coordinated:
        # Coordinated voting agreements aggregate effective control — escalate one tier
        prior = severity
        severity = {"MEDIUM": "HIGH", "HIGH": "RED"}.get(severity, severity)
        if severity != prior:
            reason += "_COORDINATED_VOTING_AGREEMENT"

    if severity is None:
        return {
            "fires": False,
            "reason": "VOTING_STRUCTURE_DIFFUSE",
            "evidence": {"top_holder_pct": top_pct, "super_vote_ratio": super_ratio},
        }

    return {
        "fires": True,
        "reason": reason,
        "severity": severity,
        "evidence": {
            "top_holder_pct": top_pct,
            "top_holder_name": data.get("top_holder_name"),
            "super_vote_ratio": super_ratio,
            "sunset_years": sunset,
            "sunset_trigger": sunset_trigger,
            "sunset_trigger_is_weak": sunset_weak,
            "coordinated_voting_agreement": coordinated,
            "is_controlled_company": is_controlled,
            "independent_chair": indep_chair,
        },
    }
