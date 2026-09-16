"""Comparable public-company valuation anchor detector for corporate IPO DD.

NOT a fire-or-not detector — produces an analysis output that anchors a fair-
value estimate against the closest public comparable. Fires when comp-implied
valuation is materially below the IPO's implied valuation (suggesting overpriced
issue).

Severity (vs implied IPO valuation):
- RED: comp-implied valuation < 50% of IPO ask
- HIGH: comp-implied valuation 50-75% of IPO ask
- MEDIUM: comp-implied valuation 75-90% of IPO ask
- LOW / NO_FIRE: comp-implied valuation > 90% of IPO ask

Live anchor pairs from 2026-05-28 pass:
- Quantinuum → IonQ: same architecture (trapped-ion), IonQ ~$130M rev / +202% YoY
  vs Quantinuum $30.9M / +34%. IonQ ~5-8x sales = at Quantinuum scale ~$155M
  fair value vs $12B IPO ask = comp-implied valuation 1.3% of IPO ask = RED.
- Firefly → RKLB: small launcher comp; RKLB ~$400M rev, 100% Electron success vs
  Firefly $100M / 33% Alpha success. Firefly trades at ~$10B; RKLB at ~$8B with
  4x revenue → fair value ~$2-3B = comp-implied 20-30% of mkt cap.
- Entrata → AppFolio: APPF $1.1B FY guide / 17.5% growth / 27% op margin trades
  ~5x sales = $5.5B. ENT $536M / 24% / 28% margin → fair value ~$4.3-4.8B at
  4-4.5x sales after governance + antitrust discount.

## Data shape

{
  "company_name": "Quantinuum",
  "implied_ipo_valuation_usd": 12000000000,
  "company_ltm_revenue_usd": 30900000,
  "company_ltm_growth_pct": 34,
  "company_op_margin_pct": -100,  # negative for cash-burning co's
  "comp_anchor": {
    "ticker": "IONQ",
    "name": "IonQ",
    "ltm_revenue_usd": 130000000,
    "ltm_growth_pct": 202,
    "op_margin_pct": -50,
    "mkt_cap_usd": 1500000000,
    "ev_revenue_multiple": 11.5,
    "source_url": "IonQ 10-K + most recent earnings"
  },
  "comp_implied_company_valuation_usd": 355000000,  # ev_rev_multiple * company_rev
  "comp_implied_vs_ipo_ask_pct": 3.0,
  "as_of_date": "2026-05-28"
}
"""
from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["corporate_ipo_dd"],
    "applies_universally": True,
    "summary": "Comp-implied valuation <90% of IPO ask (often <50%).",
}


def evaluate(obligor_name: str, data: dict) -> dict:
    ipo_val = data.get("implied_ipo_valuation_usd")
    comp_implied = data.get("comp_implied_company_valuation_usd")

    if not isinstance(ipo_val, (int, float)) or not isinstance(comp_implied, (int, float)):
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if ipo_val <= 0:
        return {"fires": False, "reason": "INVALID_IPO_VALUATION", "evidence": {}}

    pct = (comp_implied / ipo_val) * 100

    if pct < 50:
        severity, reason = "RED", "COMP_IMPLIED_VALUATION_LESS_THAN_HALF_OF_IPO_ASK"
    elif pct < 75:
        severity, reason = "HIGH", "COMP_IMPLIED_VALUATION_MATERIALLY_BELOW_IPO_ASK"
    elif pct < 90:
        severity, reason = "MEDIUM", "COMP_IMPLIED_VALUATION_MODESTLY_BELOW_IPO_ASK"
    else:
        return {
            "fires": False,
            "reason": "COMP_SUPPORTS_OR_EXCEEDS_IPO_ASK",
            "evidence": {
                "ipo_valuation_usd": ipo_val,
                "comp_implied_valuation_usd": comp_implied,
                "comp_pct_of_ipo": round(pct, 1),
                "comp_anchor": data.get("comp_anchor", {}).get("ticker"),
            },
        }

    return {
        "fires": True,
        "reason": reason,
        "severity": severity,
        "evidence": {
            "ipo_valuation_usd": ipo_val,
            "comp_implied_valuation_usd": comp_implied,
            "comp_pct_of_ipo": round(pct, 1),
            "comp_anchor_ticker": data.get("comp_anchor", {}).get("ticker"),
            "comp_anchor_name": data.get("comp_anchor", {}).get("name"),
            "comp_ev_revenue_multiple": data.get("comp_anchor", {}).get("ev_revenue_multiple"),
        },
    }
