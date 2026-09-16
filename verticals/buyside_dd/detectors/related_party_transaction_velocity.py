"""Related-party transaction velocity detector for corporate IPO DD.

FIRES when aggregate related-party transactions (director-affiliated, controlling-
shareholder, founder-related) exceed thresholds relative to company size.

Severity:
- RED: aggregate RPT > 10% of revenue OR > $1B absolute AND no audit-committee
       approval policy adopted PRE-IPO
- HIGH: aggregate RPT 5-10% of revenue OR $100M-$1B absolute
- MEDIUM: aggregate RPT 1-5% of revenue OR $10-100M absolute
- LOW: routine and minor

Live catch (2026-05-28): SpaceX's $20.2B in equipment leases to Director Antonio
Gracias's Valor — $885M paid 2025 + $857M Jan-Feb 2026. Audit-committee policy
adopted only AFTER IPO. Fires RED.

## Data shape

{
  "company_name": "Space Exploration Technologies Corp",
  "aggregate_rpt_ltm_usd": 20200000000,
  "ltm_revenue_usd": 15000000000,  # approximate, fill from S-1
  "rpt_breakdown": [
    {"counterparty": "Valor (Director Gracias)", "type": "equipment leases",
     "amount_ltm_usd": 1742000000, "described_as_arms_length": true},
    ...
  ],

  # Mitigating factors (DETERMINISTIC SEVERITY DOWNGRADES). Default to most-
  # conservative (no mitigation) when unknown — preserves SpaceX-class fires.
  "audit_committee_rpt_approval_policy_pre_ipo": false,
  "arms_length_pricing_benchmarks_provided": false,    # independent benchmarks vs narrative-only
  "rpt_disclosed_in_aggregate_dollar_terms": false,    # tabular $ aggregates vs prose only
  "rpt_majority_described_as_market_terms": false,     # explicit on-market-terms language
  "as_of_date": "2026-05-28",
  "source_url": "S-1 Certain Relationships and Related Person Transactions"
}
"""
from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["corporate_ipo_dd"],
    "applies_universally": True,
    "summary": "RPT >10% of revenue OR >$1B absolute.",
}

RED_PCT_OF_REVENUE = 10.0
HIGH_PCT_OF_REVENUE = 5.0
MED_PCT_OF_REVENUE = 1.0

RED_ABS_USD = 1_000_000_000
HIGH_ABS_USD = 100_000_000
MED_ABS_USD = 10_000_000


def evaluate(obligor_name: str, data: dict) -> dict:
    rpt = data.get("aggregate_rpt_ltm_usd")
    rev = data.get("ltm_revenue_usd")
    # Default: conservative (no mitigators present)
    policy        = bool(data.get("audit_committee_rpt_approval_policy_pre_ipo", False))
    benchmarks    = bool(data.get("arms_length_pricing_benchmarks_provided", False))
    aggregated    = bool(data.get("rpt_disclosed_in_aggregate_dollar_terms", False))
    market_terms  = bool(data.get("rpt_majority_described_as_market_terms", False))

    if not isinstance(rpt, (int, float)):
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    pct = None
    if isinstance(rev, (int, float)) and rev > 0:
        pct = (rpt / rev) * 100

    # Severity by absolute + relative — base tier
    severity = None
    reason = None
    if rpt >= RED_ABS_USD or (pct is not None and pct >= RED_PCT_OF_REVENUE):
        severity = "RED"
        reason = "EXTREME_RPT_VELOCITY"
    elif rpt >= HIGH_ABS_USD or (pct is not None and pct >= HIGH_PCT_OF_REVENUE):
        severity = "HIGH"
        reason = "MATERIAL_RPT_VELOCITY"
    elif rpt >= MED_ABS_USD or (pct is not None and pct >= MED_PCT_OF_REVENUE):
        severity = "MEDIUM"
        reason = "ELEVATED_RPT_VELOCITY"

    # Deterministic mitigating-factor downgrades.
    # Rule: count active mitigators (max 4). With 3+ mitigators, drop one tier;
    # with 4 mitigators, drop two tiers (RED -> MEDIUM). With 0 mitigators at RED tier,
    # escalation tag added (preserves SpaceX RED).
    n_mit = sum([policy, benchmarks, aggregated, market_terms])
    annotation = []
    if severity:
        # Conservative escalation when no policy AND RED-tier
        if severity == "RED" and not policy:
            reason += "_NO_AUDIT_POLICY_PRE_IPO"
        if n_mit >= 4:
            severity = {"RED": "MEDIUM", "HIGH": "LOW", "MEDIUM": "LOW"}.get(severity, severity)
            annotation.append("4_OF_4_MITIGATORS_PRESENT_DOWNGRADED_TWO_TIERS")
        elif n_mit >= 3:
            severity = {"RED": "HIGH", "HIGH": "MEDIUM", "MEDIUM": "LOW"}.get(severity, severity)
            annotation.append("3_OF_4_MITIGATORS_PRESENT_DOWNGRADED_ONE_TIER")
        elif n_mit == 0 and severity == "HIGH":
            # Zero mitigators at HIGH tier escalates to RED (was original behavior when policy=False)
            severity = "RED"
            annotation.append("ZERO_MITIGATORS_AT_HIGH_TIER_ESCALATED_TO_RED")
        if annotation:
            reason += "__" + "__".join(annotation)

    if severity is None:
        return {
            "fires": False,
            "reason": "RPT_VELOCITY_IMMATERIAL",
            "evidence": {"rpt_usd": rpt, "pct_of_revenue": pct},
        }

    return {
        "fires": True,
        "reason": reason,
        "severity": severity,
        "evidence": {
            "aggregate_rpt_ltm_usd": rpt,
            "ltm_revenue_usd": rev,
            "rpt_as_pct_of_revenue": pct,
            "n_mitigators_present": n_mit,
            "mitigators": {
                "audit_committee_policy_pre_ipo": policy,
                "arms_length_pricing_benchmarks_provided": benchmarks,
                "rpt_disclosed_in_aggregate_dollar_terms": aggregated,
                "rpt_majority_described_as_market_terms": market_terms,
            },
            "rpt_breakdown_count": len(data.get("rpt_breakdown") or []),
        },
    }
