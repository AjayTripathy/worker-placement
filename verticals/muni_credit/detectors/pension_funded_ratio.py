"""Pension funded ratio detector.

FIRES when defined-benefit pension funded ratio < 60% (assets / projected
benefit obligation).

Why predictive: Underfunded pensions are footnote-buried in audited FS and
often missed by surface-level credit analysis. They represent senior-claim
liability that competes with bondholders for cash. Funded ratio < 60% means
the obligor will need to make material cash contributions over the next
3-5 years, eroding liquidity even with positive operating performance.

Lead time vs rating action: typically 12-36 months — pension underfunding
shows up in agency models slowly as service-cost increases.

Data shape:
  {
    "plan_assets_usd": 450000000,
    "projected_benefit_obligation_usd": 780000000,
    "fiscal_year": "FY2024",
    "source_url": "..."
  }

Funded ratio = plan_assets / PBO
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["pension_dependent_gf"],
    "asset_classes": ["all_muni"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "Pension funded ratio detector.",
}

CRITICAL_THRESHOLD = 0.60  # below 60% funded fires the detector
WATCH_THRESHOLD = 0.75    # below 75% is YELLOW (observe but don't exclude)


def evaluate(obligor_name: str, data: dict) -> dict:
    assets = data.get("plan_assets_usd")
    pbo = data.get("projected_benefit_obligation_usd")
    if assets is None or pbo is None or pbo == 0:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    funded_ratio = assets / pbo
    if funded_ratio < CRITICAL_THRESHOLD:
        return {
            "fires": True,
            "reason": "PENSION_UNDERFUNDED_CRITICAL",
            "severity": "HIGH",
            "evidence": {
                "funded_ratio": funded_ratio,
                "assets_usd": assets,
                "pbo_usd": pbo,
                "underfunding_usd": pbo - assets,
            },
        }
    elif funded_ratio < WATCH_THRESHOLD:
        return {
            "fires": False,  # YELLOW — don't exclude but worth watching
            "reason": "PENSION_UNDERFUNDED_WATCH",
            "severity": "MEDIUM",
            "evidence": {
                "funded_ratio": funded_ratio,
                "assets_usd": assets,
                "pbo_usd": pbo,
            },
        }
    return {
        "fires": False,
        "reason": "PENSION_ADEQUATE",
        "evidence": {"funded_ratio": funded_ratio},
    }
