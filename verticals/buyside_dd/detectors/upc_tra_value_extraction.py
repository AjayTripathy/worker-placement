"""Up-C + TRA (Tax Receivable Agreement) value extraction detector.

FIRES when a corporate IPO uses an Up-C / TRA structure that transfers post-IPO
tax shield value to pre-IPO holders rather than the public float.

Standard Up-C/TRA: post-IPO entity acquires basis step-up via exchanges of LLC
units for shares; resulting tax savings are paid to pre-IPO holders via a TRA
typically capturing 85% of savings over 15-25 years.

Severity:
- RED: TRA captures >=85% of tax savings AND >=$1B PV of payments AND change-of-
       control termination payment >= 10% of pro-forma equity value
- HIGH: TRA 80-85% of tax savings AND material PV
- MEDIUM: TRA <80% of tax savings OR sunset/clawback present

Live catch (2026-05-28 Quantinuum): TRA directs 85% of post-IPO tax savings to
Honeywell + Cambridge Quantum (estimated $2.6B PV over 25yr); change-of-control
termination $1.67B immediately due (depresses exit premium).

## Data shape

{
  "company_name": "Quantinuum",
  "uses_up_c_structure": true,
  "tra_recipient_pct_of_tax_savings": 85,
  "tra_recipients": ["Honeywell", "Cambridge Quantum"],
  "tra_pv_estimate_usd": 2600000000,
  "change_of_control_termination_payment_usd": 1670000000,
  "pro_forma_equity_value_usd": 12000000000,
  "tra_sunset_clause_years": null,  # null = perpetual
  "as_of_date": "2026-05-28",
  "source_url": "Quantinuum S-1 Notes to Pro Forma Financial Statements"
}
"""
from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["upc_tra_structure"],
    "asset_classes": ["corporate_ipo_dd"],
    "applies_universally": True,
    "summary": "Up-C / TRA structure capturing >=85% of tax savings to pre-IPO holders.",
}


def evaluate(obligor_name: str, data: dict) -> dict:
    uses = data.get("uses_up_c_structure")
    pct = data.get("tra_recipient_pct_of_tax_savings")
    pv = data.get("tra_pv_estimate_usd")
    cot = data.get("change_of_control_termination_payment_usd")
    pf_equity = data.get("pro_forma_equity_value_usd")

    if not uses:
        return {"fires": False, "reason": "NO_UP_C_STRUCTURE", "evidence": {}}

    if not isinstance(pct, (int, float)):
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    cot_pct = None
    if isinstance(cot, (int, float)) and isinstance(pf_equity, (int, float)) and pf_equity > 0:
        cot_pct = (cot / pf_equity) * 100

    severity = None
    reason = None
    if pct >= 85 and isinstance(pv, (int, float)) and pv >= 1_000_000_000 and (cot_pct or 0) >= 10:
        severity = "RED"
        reason = "EXTREME_TRA_VALUE_EXTRACTION_WITH_COC_OVERHANG"
    elif pct >= 85 and isinstance(pv, (int, float)) and pv >= 1_000_000_000:
        severity = "RED"
        reason = "EXTREME_TRA_VALUE_EXTRACTION"
    elif pct >= 80:
        severity = "HIGH"
        reason = "MATERIAL_TRA_VALUE_EXTRACTION"
    elif pct >= 50:
        severity = "MEDIUM"
        reason = "MODERATE_TRA_VALUE_EXTRACTION"

    if severity is None:
        return {
            "fires": False,
            "reason": "TRA_PRESENT_BUT_IMMATERIAL",
            "evidence": {"tra_pct": pct, "tra_pv_usd": pv},
        }

    return {
        "fires": True,
        "reason": reason,
        "severity": severity,
        "evidence": {
            "tra_recipient_pct": pct,
            "tra_pv_usd": pv,
            "change_of_control_termination_usd": cot,
            "coc_pct_of_pro_forma_equity": cot_pct,
            "tra_recipients": data.get("tra_recipients"),
        },
    }
