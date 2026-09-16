"""Auditor change detector.

FIRES when current-year auditor differs from prior-year auditor AND change
is to a lower-tier firm OR is unexplained.

Why predictive: Auditor changes often precede operational disclosures (a
Big 4 firm resigns when uncomfortable with a client's accounting; a hospital
downgrades from Big 4 to regional when it can't afford or is dropped). Lead
time vs rating action: typically 6-18 months.

Data shape:
  {
    "audit_firm_current": "PricewaterhouseCoopers LLP",
    "audit_firm_prior": "PricewaterhouseCoopers LLP",
    "audit_firm_current_fiscal_year": "FY2024",
    "explanation_disclosed": false  # was the change explained in 8-K/proxy/note?
  }

Tier rankings (lower-tier = more concerning):
  Tier 1 (Big 4): PwC, Deloitte, EY, KPMG
  Tier 2 (national mid-tier): RSM, BDO, Grant Thornton, Crowe, Baker Tilly
  Tier 3 (regional): everything else
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["all_muni"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "Auditor change detector.",
}

import re

BIG_4 = {"pricewaterhousecoopers", "pwc", "deloitte", "ernst & young", "ernst and young", "ey",
         "kpmg"}
TIER_2 = {"rsm", "bdo", "grant thornton", "crowe", "baker tilly", "moss adams", "plante moran",
          "mazars", "marcum", "withum"}


def normalize_firm(firm: str) -> str:
    if not firm:
        return ""
    return re.sub(r"[^a-z\s&]", "", firm.lower()).strip()


def firm_tier(firm: str) -> int:
    """Returns 1 (Big 4), 2 (national mid-tier), or 3 (regional)."""
    norm = normalize_firm(firm)
    for f in BIG_4:
        if f in norm:
            return 1
    for f in TIER_2:
        if f in norm:
            return 2
    return 3


def evaluate(obligor_name: str, data: dict) -> dict:
    current = data.get("audit_firm_current")
    prior = data.get("audit_firm_prior")
    if not current or not prior:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    current_norm = normalize_firm(current)
    prior_norm = normalize_firm(prior)
    if current_norm == prior_norm:
        return {"fires": False, "reason": "NO_CHANGE", "evidence": {"firm": current}}

    cur_tier = firm_tier(current)
    pri_tier = firm_tier(prior)
    explained = data.get("explanation_disclosed", False)

    # Fires if downgrade in tier OR unexplained change
    fires = (cur_tier > pri_tier) or not explained
    severity = (
        "HIGH" if cur_tier > pri_tier and not explained
        else "MEDIUM" if (cur_tier > pri_tier or not explained)
        else "LOW"
    )

    return {
        "fires": fires,
        "reason": "TIER_DOWNGRADE" if cur_tier > pri_tier else "UNEXPLAINED_CHANGE" if not explained else "EXPLAINED_LATERAL",
        "severity": severity,
        "evidence": {
            "from": prior,
            "from_tier": pri_tier,
            "to": current,
            "to_tier": cur_tier,
            "explanation_disclosed": explained,
        },
    }
