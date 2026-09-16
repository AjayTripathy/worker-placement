"""Land-secured (CFD) top-taxpayer-concentration detector.

FIRES when a single property owner accounts for >25% of CFD special-tax
liability AND there is corroborating distress (delinquency >2%, OR buildout
stalled, OR developer financially weak). Severity HIGH at >50% concentration.

Why predictive: builder concentration risk. Pre-buildout CFDs structurally
have high developer concentration (master developer owns all undeveloped
parcels). Concentration alone is not the signal — concentration paired with
ANY distress trigger is.

Calibration note: standalone concentration >50% fires on ~15-20% of housing
CFDs (mostly innocuous master-developer structures). Pairing with corroborating
distress drops fire rate to <5% with much higher precision.

Public data: Continuing Disclosure Annual Report (CDA) Section listing top
10 taxpayers; OS at issuance.

Data shape:
  {
    "top_taxpayer_pct": 67,
    "top_taxpayer_name": "FivePoint Holdings",
    "corroborating_distress": {
      "delinquency_pct": 4.5,
      "buildout_stalled": false,
      "developer_distress": false
    },
    "as_of_date": "2024-06-30",
    "source": "CDA filed 2024-10-15",
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
    "summary": "Land-secured (CFD) top-taxpayer-concentration detector.",
}

CONCENTRATION_THRESHOLD = 25.0
HIGH_CONCENTRATION = 50.0
DELINQ_CORROBORATING_THRESHOLD = 2.0


def evaluate(obligor_name: str, data: dict) -> dict:
    concentration = data.get("top_taxpayer_pct")
    corroborating = data.get("corroborating_distress") or {}
    delinq = corroborating.get("delinquency_pct")
    buildout_stalled = corroborating.get("buildout_stalled")
    dev_distress = corroborating.get("developer_distress")

    if not isinstance(concentration, (int, float)):
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if concentration < CONCENTRATION_THRESHOLD:
        return {
            "fires": False,
            "reason": "CONCENTRATION_BELOW_THRESHOLD",
            "evidence": {"top_taxpayer_pct": concentration},
        }

    # Concentration alone is not enough — need corroborating distress
    has_corroborating = (
        (isinstance(delinq, (int, float)) and delinq > DELINQ_CORROBORATING_THRESHOLD)
        or buildout_stalled
        or dev_distress
    )

    if not has_corroborating:
        return {
            "fires": False,
            "reason": "CONCENTRATION_WITHOUT_CORROBORATING_DISTRESS",
            "evidence": {
                "top_taxpayer_pct": concentration,
                "top_taxpayer_name": data.get("top_taxpayer_name"),
            },
        }

    severity = "HIGH" if concentration > HIGH_CONCENTRATION else "MEDIUM"
    return {
        "fires": True,
        "reason": "CONCENTRATION_WITH_DISTRESS",
        "severity": severity,
        "evidence": {
            "top_taxpayer_pct": concentration,
            "top_taxpayer_name": data.get("top_taxpayer_name"),
            "delinquency_pct": delinq,
            "buildout_stalled": buildout_stalled,
            "developer_distress": dev_distress,
        },
    }
