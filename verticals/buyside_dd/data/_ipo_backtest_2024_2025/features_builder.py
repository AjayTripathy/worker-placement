"""Deterministic, frozen detector-input features from EDGAR structural fields.

No LLM, no prospectus parsing — every field is a structured EDGAR attribute,
so the feature set is fully reproducible. These are the cheaply-extractable
inputs to the chinese_smallcap_ramp_dump_archetype detector (domicile / filer
type / venue). The underwriter-watchlist feature needs prospectus parsing and
is deliberately NOT included here.

Captured per name:
  - incorp_code / incorp_desc        stateOfIncorporation (E9=Cayman, D8=BVI, DE=Delaware...)
  - biz_country_code                 business-address stateOrCountry (F4=China, K3=HK...)
  - foreign_private_issuer           files F-1 / 20-F / 6-K
  - exchange

Run: python3 verticals/buyside_dd/data/_ipo_backtest_2024_2025/features_builder.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
COHORT = HERE / "cohort.json"
OUT = HERE / "features.json"
UA = {"User-Agent": "SignalOS research 4tripathy@gmail.com"}

FPI_FORMS = {"F-1", "F-1/A", "20-F", "6-K", "40-F"}


def _subs(cik: int) -> dict:
    url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main() -> None:
    cohort = json.loads(COHORT.read_text())["cohort"]
    out, errors = [], 0
    for i, rec in enumerate(cohort):
        cik = int(rec["cik"])
        try:
            d = _subs(cik)
        except Exception as e:
            print(f"  [{i+1}] ERR {rec['company_name'][:36]}: {e}", file=sys.stderr)
            errors += 1
            time.sleep(0.2)
            continue
        biz = d.get("addresses", {}).get("business", {}) or {}
        forms = set(d.get("filings", {}).get("recent", {}).get("form", []))
        out.append({
            "cik": rec["cik"],
            "ticker": (rec["tickers"] or [None])[0],
            "company_name": rec["company_name"],
            "incorp_code": d.get("stateOfIncorporation"),
            "incorp_desc": d.get("stateOfIncorporationDescription"),
            "biz_country_code": biz.get("stateOrCountry"),
            "biz_city": biz.get("city"),
            "foreign_private_issuer": bool(forms & FPI_FORMS),
            "exchange": (rec["exchanges"] or [None])[0],
            "sic": rec.get("sic"),
        })
        if i % 25 == 24:
            print(f"  {i+1}/{len(cohort)} | err {errors}", file=sys.stderr)
        time.sleep(0.15)
    OUT.write_text(json.dumps({"n": len(out), "n_errors": errors, "features": out}, indent=2))
    print(f"\nWrote {OUT.name} ({len(out)} rows, {errors} errors)", file=sys.stderr)


if __name__ == "__main__":
    main()
