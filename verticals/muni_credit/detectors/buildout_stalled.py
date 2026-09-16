"""Land-secured (CFD) build-out-stalled detector.

FIRES when CFD's build-out percentage (% of planned parcels developed) is
below 70% with bonds outstanding 5+ years, OR build-out has been unchanged
across the last 2 CDA filings.

Why predictive: pre-buildout CFDs depend on the master developer paying
special tax on undeveloped parcels (priced to support full debt service
assuming buildout completes). If buildout stalls, the developer can't
amortize their carrying cost; default risk rises non-linearly. The
2008-2012 wave of CFD distress was almost entirely stalled-buildout cases.

Public data: Continuing Disclosure Annual Report (CDA) filed on EMMA; OS at
issuance. NOT in YFSR. Per-CFD CDA pull is meaningful manual work — this is
a MEDIUM-confidence detector limited by data availability.

Data shape:
  {
    "buildout_pct": 32,
    "buildout_pct_t1": 30,
    "buildout_pct_t2": 28,
    "years_since_first_bond": 8,
    "cfd_type": "housing_development",  # filter: only fires on housing CFDs
    "as_of_date": "2024-06-30",
    "source": "CDA filed 2024-10-15 on EMMA",
    "confidence": "MEDIUM"
  }
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["land_secured_district"],
    "asset_classes": ["ca_mello_roos_cfd", "ca_cfd_muni", "ca_1915_act_assessment_bonds"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Land-secured (CFD) build-out-stalled detector.",
}

BUILDOUT_LOW_THRESHOLD = 70.0
MIN_YEARS_OUTSTANDING = 5


def evaluate(obligor_name: str, data: dict) -> dict:
    buildout = data.get("buildout_pct")
    t1 = data.get("buildout_pct_t1")
    t2 = data.get("buildout_pct_t2")
    years_outstanding = data.get("years_since_first_bond")
    cfd_type = (data.get("cfd_type") or "").lower()

    # Only fire on housing-development CFDs; municipal-services / school CFDs
    # don't have a buildout concept in the same way.
    if cfd_type and cfd_type not in ("housing_development", "mixed_use", "residential"):
        return {
            "fires": False,
            "reason": "NOT_HOUSING_CFD",
            "evidence": {"cfd_type": cfd_type},
        }

    if not isinstance(buildout, (int, float)):
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if not isinstance(years_outstanding, (int, float)) or years_outstanding < MIN_YEARS_OUTSTANDING:
        # New issuance — low buildout is expected, not a signal
        return {
            "fires": False,
            "reason": "BONDS_TOO_NEW",
            "evidence": {"buildout_pct": buildout, "years_outstanding": years_outstanding},
        }

    stalled_2yr = (
        isinstance(t1, (int, float))
        and isinstance(t2, (int, float))
        and buildout - t2 < 5.0  # less than 5pp gain over 2 years
        and buildout < BUILDOUT_LOW_THRESHOLD
    )

    if buildout < BUILDOUT_LOW_THRESHOLD:
        severity = "HIGH" if buildout < 50 else "MEDIUM"
        reason = "BUILDOUT_STALLED_2YR" if stalled_2yr else "BUILDOUT_LOW"
        return {
            "fires": True,
            "reason": reason,
            "severity": severity,
            "evidence": {
                "buildout_pct": buildout,
                "buildout_pct_t1": t1,
                "buildout_pct_t2": t2,
                "years_since_first_bond": years_outstanding,
                "stalled_2yr": stalled_2yr,
            },
        }
    return {
        "fires": False,
        "reason": "BUILDOUT_HEALTHY",
        "evidence": {"buildout_pct": buildout},
    }
