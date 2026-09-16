"""JOBS Act emerging-growth-company disclosure exemption audit detector.

JOBS Act EGC (annual revenue <$1.2B) status lets an issuer hold back:
- Top-10 customer percentage of revenue
- Full executive compensation (CD&A, pay-vs-performance, etc.)
- Auditor attestation on internal controls (SOX 404(b))
- Selected financial data table
- Reduced new-accounting-standards adoption timeline (extended transition)

FIRES when a material number of EGC exemptions are taken on a filing where the
withheld data would be load-bearing for DD.

Severity:
- HIGH: 3+ material exemptions invoked, including customer-concentration AND
        full-exec-comp
- MEDIUM: 2 material exemptions
- LOW: 1 exemption invoked (routine)

Live catch (2026-05-28): 4 of 5 IPOs scored used JOBS Act exemptions to hold
back material data. Entrata withheld top-10 customer % (load-bearing given REIT
customer concentration risk). Quantinuum withheld Azure passthrough split.

## Data shape

{
  "company_name": "Entrata",
  "is_emerging_growth_company": true,
  "exemptions_invoked": [
    {"name": "top_10_customer_concentration", "withheld_data": "top-10 customer % of revenue",
     "material_for_dd": true, "rationale_in_s1": "EGC accommodation"},
    {"name": "executive_comp_cda", "withheld_data": "full Compensation Discussion & Analysis",
     "material_for_dd": true},
    {"name": "sox_404b", "withheld_data": "auditor attestation on internal controls",
     "material_for_dd": true},
    {"name": "selected_financial_data_table", "withheld_data": "5-year selected financial data",
     "material_for_dd": false},
  ],
  "as_of_date": "2026-05-28",
  "source_url": "S-1 Cover + Risk Factors"
}
"""
from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["egc_status"],
    "asset_classes": ["corporate_ipo_dd"],
    "applies_universally": True,
    "summary": "3+ EGC exemptions, especially customer concentration + exec comp combined.",
}


def evaluate(obligor_name: str, data: dict) -> dict:
    is_egc = data.get("is_emerging_growth_company")
    exemptions = data.get("exemptions_invoked") or []

    if not is_egc:
        return {"fires": False, "reason": "NOT_EGC", "evidence": {}}

    material = [e for e in exemptions if e.get("material_for_dd")]
    n_material = len(material)

    customer_concentration_withheld = any(
        "customer" in (e.get("name") or "").lower() or
        "concentration" in (e.get("withheld_data") or "").lower()
        for e in material
    )
    exec_comp_withheld = any(
        "comp" in (e.get("name") or "").lower() or "cda" in (e.get("name") or "").lower()
        for e in material
    )

    if n_material >= 3 and customer_concentration_withheld and exec_comp_withheld:
        severity, reason = "HIGH", "MULTIPLE_MATERIAL_EXEMPTIONS_INCLUDING_CUSTOMER_AND_COMP"
    elif n_material >= 3:
        severity, reason = "HIGH", "MULTIPLE_MATERIAL_EXEMPTIONS_INVOKED"
    elif n_material >= 2:
        severity, reason = "MEDIUM", "TWO_MATERIAL_EXEMPTIONS_INVOKED"
    elif n_material >= 1:
        severity, reason = "LOW", "ONE_MATERIAL_EXEMPTION_INVOKED"
    else:
        return {
            "fires": False,
            "reason": "EGC_BUT_NO_MATERIAL_EXEMPTIONS",
            "evidence": {"total_exemptions": len(exemptions)},
        }

    return {
        "fires": True,
        "reason": reason,
        "severity": severity,
        "evidence": {
            "n_material_exemptions": n_material,
            "n_total_exemptions": len(exemptions),
            "customer_concentration_withheld": customer_concentration_withheld,
            "exec_comp_withheld": exec_comp_withheld,
            "withheld_data_items": [e.get("withheld_data") for e in material],
        },
    }
