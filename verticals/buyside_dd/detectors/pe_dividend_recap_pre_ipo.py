"""PE / private equity sponsor dividend recap pre-IPO detector.

FIRES when a PE sponsor took a special cash dividend within 24 months pre-IPO,
financed by new debt, AND the IPO proceeds are used (in part) to retire that
same debt.

This pattern transfers value from public-IPO subscribers to the PE sponsor:
sponsor pulls out cash via debt-financed dividend pre-IPO, then uses IPO
proceeds to pay down the debt the sponsor caused the company to incur.

Severity:
- RED: dividend > 25% of post-IPO equity value AND IPO proceeds materially used
       to retire the dividend-financing debt
- HIGH: dividend 10-25% of post-IPO equity value OR IPO proceeds partly used to
        retire dividend-financing debt
- MEDIUM: smaller dividend without debt-financing OR longer-tail timing

Live catch (2026-05-28 Entrata): Silver Lake took $356M special dividend
Nov 2025 financed by new $400M term loan @ 6.4%; IPO proceeds slated partly to
pay down that same debt.

## Data shape

{
  "company_name": "Entrata",
  "pe_sponsor": "Silver Lake",
  "special_dividend_usd": 356000000,
  "dividend_date": "2025-11-15",
  "months_pre_ipo_filing": 6,
  "debt_financing_for_dividend_usd": 400000000,
  "debt_interest_rate_pct": 6.4,
  "ipo_proceeds_used_for_debt_retirement_usd": 200000000,  # estimate from use-of-proceeds
  "post_ipo_implied_equity_value_usd": 4500000000,
  "as_of_date": "2026-05-28",
  "source_url": "Entrata S-1 Use of Proceeds + Subsequent Events"
}
"""
from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["pe_sponsor_control"],
    "asset_classes": ["corporate_ipo_dd"],
    "applies_universally": True,
    "summary": "PE special dividend within 24mo pre-IPO, debt-financed, IPO retires the debt.",
}

DIVIDEND_RED_PCT_OF_EQUITY = 25.0
DIVIDEND_HIGH_PCT_OF_EQUITY = 10.0
LOOKBACK_MONTHS = 24


def evaluate(obligor_name: str, data: dict) -> dict:
    div = data.get("special_dividend_usd")
    months_back = data.get("months_pre_ipo_filing")
    debt = data.get("debt_financing_for_dividend_usd")
    proceeds_to_debt = data.get("ipo_proceeds_used_for_debt_retirement_usd", 0)
    equity = data.get("post_ipo_implied_equity_value_usd")

    if not isinstance(div, (int, float)):
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if isinstance(months_back, (int, float)) and months_back > LOOKBACK_MONTHS:
        return {
            "fires": False,
            "reason": "DIVIDEND_OUTSIDE_LOOKBACK_WINDOW",
            "evidence": {"months_pre_ipo": months_back},
        }

    pct = None
    if isinstance(equity, (int, float)) and equity > 0:
        pct = (div / equity) * 100

    debt_financed = isinstance(debt, (int, float)) and debt >= div * 0.8
    ipo_pays_down_debt = isinstance(proceeds_to_debt, (int, float)) and proceeds_to_debt > 0

    severity = None
    reason = None
    if pct and pct >= DIVIDEND_RED_PCT_OF_EQUITY and debt_financed and ipo_pays_down_debt:
        severity, reason = "RED", "EXTREME_DIVIDEND_RECAP_WITH_IPO_PAYDOWN"
    elif (pct and pct >= DIVIDEND_HIGH_PCT_OF_EQUITY) or (debt_financed and ipo_pays_down_debt):
        severity, reason = "HIGH", "MATERIAL_DIVIDEND_RECAP"
    elif div >= 100_000_000:
        severity, reason = "MEDIUM", "ELEVATED_DIVIDEND_PRE_IPO"

    if severity is None:
        return {
            "fires": False,
            "reason": "DIVIDEND_IMMATERIAL",
            "evidence": {"dividend_usd": div, "pct_of_equity": pct},
        }

    return {
        "fires": True,
        "reason": reason,
        "severity": severity,
        "evidence": {
            "special_dividend_usd": div,
            "dividend_pct_of_equity": pct,
            "debt_financed": debt_financed,
            "ipo_proceeds_for_debt_retirement_usd": proceeds_to_debt,
            "pe_sponsor": data.get("pe_sponsor"),
            "months_pre_ipo": months_back,
        },
    }
