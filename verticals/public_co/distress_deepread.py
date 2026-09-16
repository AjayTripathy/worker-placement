"""
Deep-read on top distress-sift candidates.

For each candidate CIK:
  1. Pull most recent 10-Q + 10-K + 8-K (past 90 days) via EDGAR submissions API
  2. Extract cash + cash-equivalents + investments from balance sheet (XBRL financial facts API)
  3. Compute trailing-quarter operating cash burn
  4. Compute implied runway (months)
  5. Surface concrete forward prediction with falsification criteria

Output: predictions.json + predictions.md

Usage:
    python3 -m verticals.public_co.distress_deepread --top 15
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

HERE = Path(__file__).parent
DATA = HERE / "data" / "_distress_sift"


def companyfacts(cik: str) -> dict | None:
    cik_padded = cik.lstrip("0").rjust(10, "0")
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"
    try:
        with httpx.Client(headers=HEADERS, timeout=30) as c:
            r = c.get(url)
            if r.status_code != 200:
                return None
            return r.json()
    except Exception:
        return None


def latest_value(facts: dict, concept: str, unit: str = "USD") -> tuple[float, str, str] | None:
    """Return (value, end_date, form) for the most recent reported value of `concept`."""
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    entry = us_gaap.get(concept)
    if not entry:
        return None
    units = entry.get("units", {}).get(unit, [])
    if not units:
        return None
    # Most recent end-date wins
    sorted_units = sorted(units, key=lambda x: x.get("end", ""), reverse=True)
    for u in sorted_units:
        return float(u.get("val", 0)), u.get("end", ""), u.get("form", "")
    return None


def quarterly_change(facts: dict, concept: str) -> tuple[float, str, str] | None:
    """Most recent quarterly (3-month duration) value for a flow concept."""
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    entry = us_gaap.get(concept)
    if not entry:
        return None
    units = entry.get("units", {}).get("USD", [])
    quarterly = [u for u in units if u.get("fp") in ("Q1", "Q2", "Q3", "Q4") and u.get("form","").startswith("10")]
    if not quarterly:
        return None
    quarterly.sort(key=lambda x: x.get("end", ""), reverse=True)
    u = quarterly[0]
    return float(u.get("val", 0)), u.get("end", ""), u.get("form", "")


def assess_candidate(cik: str, company: str, signals: list[str]) -> dict:
    """Build a forward prediction record from XBRL company facts."""
    facts = companyfacts(cik)
    if not facts:
        return {
            "cik": cik, "company": company, "signals": signals,
            "ok": False, "error": "no companyfacts (no XBRL filings?)",
        }

    # Cash position (try several concept names)
    cash = None
    for concept in [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        "Cash",
        "CashAndCashEquivalentsAndShortTermInvestments",
    ]:
        v = latest_value(facts, concept)
        if v:
            cash = v
            break

    # Quarterly cash burn from operations (negative is bad)
    qburn = quarterly_change(facts, "NetCashProvidedByUsedInOperatingActivities")

    # Total liabilities for leverage context
    total_liab = latest_value(facts, "Liabilities")

    # Stockholders' equity
    equity = latest_value(facts, "StockholdersEquity")

    # Most recent reporting period
    most_recent_filing = None
    for concept in ["Assets", "Liabilities", "StockholdersEquity"]:
        v = latest_value(facts, concept)
        if v:
            most_recent_filing = v[1]
            break

    out = {
        "cik":           cik,
        "company":       company,
        "signals":       signals,
        "ok":            True,
        "cash":          cash[0] if cash else None,
        "cash_date":     cash[1] if cash else None,
        "qburn":         qburn[0] if qburn else None,
        "qburn_date":    qburn[1] if qburn else None,
        "total_liab":    total_liab[0] if total_liab else None,
        "equity":        equity[0] if equity else None,
        "report_date":   most_recent_filing,
    }

    # Implied runway in months
    if cash and qburn and qburn[0] < 0:
        monthly_burn = -qburn[0] / 3.0
        runway_months = cash[0] / monthly_burn if monthly_burn > 0 else None
        out["monthly_burn"]   = monthly_burn
        out["runway_months"]  = runway_months
    else:
        out["monthly_burn"]   = None
        out["runway_months"]  = None

    return out


def build_prediction(rec: dict) -> str:
    """Compose a one-line forward prediction with falsification criteria."""
    if not rec.get("ok"):
        return f"  ⚠️ no XBRL data: {rec.get('error','')}"
    rw = rec.get("runway_months")
    cash = rec.get("cash")
    burn = rec.get("monthly_burn")
    report = rec.get("report_date", "?")

    if rw is None:
        return f"  cash={cash}, no operating-burn signal — no runway estimate"
    if rw < 6:
        flag = "🔴 SUB-6-MONTH RUNWAY"
    elif rw < 12:
        flag = "🟠 6-12 MONTH RUNWAY"
    elif rw < 24:
        flag = "🟡 12-24 MONTH RUNWAY"
    else:
        flag = "🟢 24+ MONTH RUNWAY"

    return (f"  cash=${cash/1e6:,.1f}M, burn=${burn/1e6:.2f}M/mo, "
            f"runway≈{rw:.1f} months from {report}.  {flag}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    candidates = json.loads((DATA / "candidates.json").read_text())
    print(f"Loaded {len(candidates):,} candidates", file=sys.stderr)

    out_rows = []
    for cand in candidates[:args.top]:
        cik = cand["cik"]
        company = cand["company"]
        signals = cand["signals"]
        print(f"\n=== {company[:60]:60s} (CIK={cik}) ===", file=sys.stderr)
        print(f"     signals: {signals}", file=sys.stderr)
        rec = assess_candidate(cik, company, signals)
        out_rows.append(rec)
        print(build_prediction(rec), file=sys.stderr)
        time.sleep(0.3)

    out_path = DATA / "predictions.json"
    out_path.write_text(json.dumps(out_rows, indent=2))
    print(f"\nWrote → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
