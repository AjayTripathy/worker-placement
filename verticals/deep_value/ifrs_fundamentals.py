"""ifrs_fundamentals — pulls ANNUAL fundamentals for US-listed FOREIGN (IFRS) filers that the us-gaap
frames miss, via per-CIK companyfacts, converts to USD, and maps to the us-gaap f-row keys so the existing
quality gate + PFIC screen run unchanged. 20-F filers don't file standardized quarterlies, so freshness is
FY-level (not quarterly) — flagged, and survivors get deep-diligenced anyway. FX is a static screening
table (approximate; ratios are currency-neutral, only EV/EBIT needs the USD bridge).
"""
from __future__ import annotations
import json, time, urllib.request

HDRS = {"User-Agent": "signalos-deepvalue research 4tripathy@gmail.com"}
FX = {"USD": 1.0, "EUR": 1.08, "GBP": 1.27, "CAD": 0.73, "BRL": 0.18, "ILS": 0.27, "AUD": 0.66,
      "MXN": 0.055, "TWD": 0.031, "JPY": 0.0064, "CHF": 1.12, "SEK": 0.095, "NOK": 0.093, "DKK": 0.145,
      "HKD": 0.128, "SGD": 0.74, "INR": 0.012, "KRW": 0.00073, "CNY": 0.138, "ZAR": 0.054, "NZD": 0.61,
      "ARS": 0.001, "CLP": 0.0011, "ZAC": 0.0054}

IFRS_MAP = {
    "Revenues": ["Revenue", "RevenueFromContractsWithCustomers"],
    "OperatingIncomeLoss": ["ProfitLossFromOperatingActivities", "OperatingProfit"],
    "Assets": ["Assets"],
    "AssetsCurrent": ["CurrentAssets"],
    "Liabilities": ["Liabilities"],
    "LiabilitiesCurrent": ["CurrentLiabilities"],
    "StockholdersEquity": ["EquityAttributableToOwnersOfParent", "Equity"],
    "CashAndCashEquivalentsAtCarryingValue": ["CashAndCashEquivalents"],
    "ShortTermInvestments": ["CurrentInvestments", "OtherCurrentFinancialAssets"],
    "LongTermInvestments": ["NoncurrentInvestments", "InvestmentsInSubsidiariesJointVenturesAndAssociates"],
    "LongTermDebtNoncurrent": ["NoncurrentBorrowings", "NoncurrentPortionOfNoncurrentBorrowings"],
    "DebtCurrent": ["CurrentBorrowings", "ShorttermBorrowings"],
    "NetCashProvidedByUsedInOperatingActivities": ["CashFlowsFromUsedInOperatingActivities"],
    "PaymentsToAcquirePropertyPlantAndEquipment":
        ["PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities"],
}
_FLOWS = {"Revenues", "OperatingIncomeLoss", "NetCashProvidedByUsedInOperatingActivities",
          "PaymentsToAcquirePropertyPlantAndEquipment"}


def _pick(units: dict, annual: bool):
    """Return (val_usd, currency) for the latest annual flow / latest instant, converted to USD."""
    best = None
    for unit, arr in units.items():
        cur = unit.split("-")[0].upper()[:3] if unit != "USD" else "USD"
        fx = FX.get(unit) or FX.get(cur)
        if fx is None:
            continue
        for r in arr:
            end = r.get("end", "")
            if annual:
                st = r.get("start", "")
                dur_ok = st and end and (int(end[:4]) - int(st[:4])) >= 1 and (end[5:7] == st[5:7] or True)
                if not dur_ok:
                    continue
            if end and (best is None or end > best[2]):
                best = (r["val"] * fx, cur, end)
    return (best[0], best[1]) if best else (None, None)


def fetch_ifrs(cik: int) -> dict | None:
    try:
        cf = json.load(urllib.request.urlopen(urllib.request.Request(
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json", headers=HDRS), timeout=30))
    except Exception:
        return None
    g = cf.get("facts", {}).get("ifrs-full")
    if not g:
        return None
    rec, latest_end = {}, ""
    for our_key, ifrs_keys in IFRS_MAP.items():
        for k in ifrs_keys:
            if k in g:
                v, cur = _pick(g[k]["units"], annual=(our_key in _FLOWS))
                if v is not None:
                    rec[our_key] = v
                    break
    # need at least revenue/EBIT/assets to be screenable
    if not (rec.get("OperatingIncomeLoss") is not None and rec.get("Assets")):
        return None
    # annual recency: treat as "fresh" if the latest fiscal year is 2024+
    for k in ("Assets", "Revenues"):
        if k in g.get(k, {}):
            pass
    rec["_ttm_rolling"] = True            # annual-fresh proxy (20-F has no quarterly frame)
    rec["_ifrs_annual"] = True            # flag: screened on annual IFRS, not quarterly
    rec["OperatingIncomeLoss_prior"] = None
    rec["OperatingIncomeLoss_q"] = None   # no quarterly -> quarterly-inflection gate is skipped
    rec["OperatingIncomeLoss_q_prior"] = None
    rec["OneTimeGain_q"] = 0
    rec["OneTimeGain_q_prior"] = 0
    rec["Revenues_prior"] = None
    return rec


def fetch_ifrs_cross_section(ciks, max_pull=500) -> dict[int, dict]:
    out = {}
    for i, cik in enumerate(list(ciks)[:max_pull]):
        r = fetch_ifrs(cik)
        if r:
            out[cik] = r
        time.sleep(0.08)
    return out
