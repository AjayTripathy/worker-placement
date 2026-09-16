"""Cash-runway calculator for development-stage issuers.

WHY THIS EXISTS

Dev-stage pharma, biotech, and pre-revenue tech issuers have a single
catastrophe vector that dwarfs the rest: cash runs out before the next
milestone. Going-concern paragraphs lag the runway exhaustion — by the
time the auditor writes a going-concern qualification, the equity has
typically already been diluted to oblivion via emergency ATM raises.

The deterministic forward signal: cash + short-term investments / (TTM
operating cash burn / 12). Below 12 months → SEVERE. Below 6 months →
RED. Above 24 months → CLEAN (insulated).

INPUTS (via xbrl_panel)

  Cash:
    us-gaap:CashAndCashEquivalentsAtCarryingValue |
    us-gaap:Cash
  ST investments:
    us-gaap:ShortTermInvestments | us-gaap:MarketableSecuritiesCurrent
  Operating cash flow:
    us-gaap:NetCashProvidedByUsedInOperatingActivities

OUTPUT

  signal: INSULATED | CLEAN | TIGHT | SEVERE | RED | UNVERIFIABLE

THRESHOLDS

  runway_months >= 24  → INSULATED
  12 <= runway < 24    → CLEAN
  6 <= runway < 12     → TIGHT
  3 <= runway < 6      → SEVERE
  runway < 3           → RED

If TTM operating cash flow is POSITIVE (issuer is cash-generative),
signal = NOT_APPLICABLE — runway is infinite. Skip and let other
m-sources speak to going concern.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["283", "384", "737"],
    "issuer_features": ["development_stage_prerevenue"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Deterministic cash-runway calculation for dev-stage issuers; runway exhaustion leads the going-concern flag.",
}

from typing import Any, Optional

from . import xbrl_panel


_SEVERITY_MAP = {
    "INSULATED":      "PASS",
    "CLEAN":          "PASS",
    "TIGHT":          "MODERATE_UNDERDELIVERY",
    "SEVERE":         "SEVERE_UNDERDELIVERY",
    "RED":            "RED_FLAG_NEGATIVE",
    "NOT_APPLICABLE": "PASS",
    "UNVERIFIABLE":   "UNVERIFIABLE",
}

CASH_TAGS = ("us-gaap:CashAndCashEquivalentsAtCarryingValue", "us-gaap:Cash")
STI_TAGS  = ("us-gaap:ShortTermInvestments", "us-gaap:MarketableSecuritiesCurrent")
OCF_TAGS  = ("us-gaap:NetCashProvidedByUsedInOperatingActivities",)


def _latest(series: list[dict]) -> Optional[float]:
    return series[-1].get("val") if series else None


def _ttm(quarterly: list[dict]) -> Optional[float]:
    if len(quarterly) < 4:
        return None
    vals = [o.get("val") for o in quarterly[-4:]]
    if any(v is None for v in vals):
        return None
    return sum(vals)


def query_runway(cik: str, cutoff_date: str) -> dict[str, Any]:
    p = xbrl_panel.panel(
        cik,
        tags=[CASH_TAGS, STI_TAGS, OCF_TAGS],
        cutoff_date=cutoff_date,
    )
    if "error" in p:
        return {"signal": "UNVERIFIABLE", "severity": "UNVERIFIABLE",
                "direction": "neutral", "_note": p["error"]}

    tags = p.get("tags") or {}
    cash_q = xbrl_panel.quarterly_series(tags.get(CASH_TAGS[0], []))
    sti_q  = xbrl_panel.quarterly_series(tags.get(STI_TAGS[0], []))
    ocf_q  = xbrl_panel.quarterly_series(tags.get(OCF_TAGS[0], []))

    cash_latest = _latest(cash_q)
    sti_latest  = _latest(sti_q)
    ocf_ttm     = _ttm(ocf_q)

    if cash_latest is None or ocf_ttm is None:
        return {
            "cik": p.get("cik"),
            "signal": "UNVERIFIABLE",
            "severity": "UNVERIFIABLE",
            "direction": "neutral",
            "_note": "Missing cash or OCF facts.",
            "missing_tags": p.get("missing_tags"),
        }

    liquid_assets = cash_latest + (sti_latest or 0)

    if ocf_ttm >= 0:
        # Cash-generative; runway is N/A
        return {
            "cik": p.get("cik"),
            "entity_name": p.get("entity_name"),
            "cutoff_date": cutoff_date,
            "signal": "NOT_APPLICABLE",
            "severity": _SEVERITY_MAP["NOT_APPLICABLE"],
            "direction": "positive",
            "metrics": {
                "cash_and_sti_usd": liquid_assets,
                "ttm_operating_cash_flow_usd": ocf_ttm,
                "runway_months": None,
            },
            "_note": f"TTM OCF = ${ocf_ttm:,.0f} (positive); runway infinite.",
        }

    burn_per_month = -ocf_ttm / 12.0
    runway_months = liquid_assets / burn_per_month if burn_per_month > 0 else None

    if runway_months is None:
        signal = "UNVERIFIABLE"
    elif runway_months >= 24:
        signal = "INSULATED"
    elif runway_months >= 12:
        signal = "CLEAN"
    elif runway_months >= 6:
        signal = "TIGHT"
    elif runway_months >= 3:
        signal = "SEVERE"
    else:
        signal = "RED"

    direction = (
        "positive" if signal in ("INSULATED", "CLEAN")
        else "negative" if signal in ("TIGHT", "SEVERE", "RED")
        else "neutral"
    )

    return {
        "cik": p.get("cik"),
        "entity_name": p.get("entity_name"),
        "cutoff_date": cutoff_date,
        "signal": signal,
        "severity": _SEVERITY_MAP[signal],
        "direction": direction,
        "metrics": {
            "cash_and_sti_usd":           liquid_assets,
            "ttm_operating_cash_flow_usd": ocf_ttm,
            "monthly_burn_usd":            round(burn_per_month, 0),
            "runway_months":               round(runway_months, 1) if runway_months else None,
        },
        "_note": (
            f"Cash+STI ${liquid_assets/1e6:.1f}M; monthly burn ${burn_per_month/1e6:.1f}M; "
            f"runway {runway_months:.1f} months."
            if runway_months else "Cannot compute runway."
        ),
    }


if __name__ == "__main__":
    import json
    import sys
    cik = sys.argv[1] if len(sys.argv) > 1 else "0001711279"  # KRYS
    cutoff = sys.argv[2] if len(sys.argv) > 2 else "2024-05-15"
    print(json.dumps(query_runway(cik, cutoff), indent=2, default=str))
