"""Universe + market cap + price + sector/country, from the Nasdaq screener API.

One bulk call returns every US-listed stock with marketCap/lastsale/sector/industry/
country. We filter to micro/small-cap, ex-financials/real-estate, drop warrants/units/
prefs, and map ticker->CIK via SEC company_tickers.
"""
from __future__ import annotations
import json, urllib.request

NASDAQ_URL = ("https://api.nasdaq.com/api/screener/stocks"
              "?tableonly=true&limit=10000&offset=0&download=true")
NASDAQ_HDRS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9", "Referer": "https://www.nasdaq.com/",
}
SEC_HDRS = {"User-Agent": "signalos-deepvalue research 4tripathy@gmail.com"}
FINANCIAL_SECTORS = {"Finance", "Real Estate"}


def _get(url, hdrs, timeout=60):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=hdrs), timeout=timeout))


def _num(s):
    s = str(s or "").replace("$", "").replace(",", "").replace("%", "")
    try:
        return float(s)
    except ValueError:
        return None


def ticker_to_cik() -> dict[str, int]:
    data = _get("https://www.sec.gov/files/company_tickers.json", SEC_HDRS)
    return {v["ticker"].upper(): int(v["cik_str"]) for v in data.values()}


def fetch_universe(min_mcap=5e7, max_mcap=2e9, ex_financials=True) -> list[dict]:
    """Micro/small-cap common stocks, ex-financials/RE, mapped to CIK."""
    rows = _get(NASDAQ_URL, NASDAQ_HDRS)["data"]["rows"]
    t2c = ticker_to_cik()
    out = []
    for x in rows:
        sym = (x.get("symbol") or "").upper()
        m = _num(x.get("marketCap"))
        sec = x.get("sector") or ""
        if not sym or m is None or not (min_mcap < m < max_mcap):
            continue
        if "^" in sym or "/" in sym or len(sym) > 5:           # warrants/units/prefs
            continue
        if ex_financials and sec in FINANCIAL_SECTORS:
            continue
        cik = t2c.get(sym)
        if not cik:
            continue
        out.append({"sym": sym, "cik": cik, "mktcap": m, "px": _num(x.get("lastsale")),
                    "sec": sec, "ind": x.get("industry", ""), "country": x.get("country", ""),
                    "name": x.get("name", "")})
    return out
