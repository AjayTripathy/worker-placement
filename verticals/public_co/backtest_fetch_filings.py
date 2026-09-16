"""
Fetch the most-recent-pre-cutoff 10-K for each ticker in a backtest run.

Uses SEC EDGAR submissions API to list all 10-K filings for a CIK, picks
the most recent one filed BEFORE the cutoff date, downloads the primary
document text into data/<ticker>/filings_<cutoff>/.

Usage:
    python3 -m verticals.public_co.backtest_fetch_filings \
        --cutoff 2024-05-17 --tickers UPST AFRM OPEN SOFI COF
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import httpx

HERE = Path(__file__).parent
DATA = HERE / "data"

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}


def list_10k_filings(cik: str) -> list[dict]:
    """Return list of {form, filing_date, accession, primary_doc} for a CIK,
    sorted by filing_date DESC."""
    cik_padded = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    r = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
    if r.status_code != 200:
        return []
    j = r.json()
    recent = j.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accs  = recent.get("accessionNumber", [])
    pris  = recent.get("primaryDocument", [])
    out = []
    for i, f in enumerate(forms):
        if f not in ("10-K", "20-F", "40-F"):
            continue
        out.append({
            "form":         f,
            "filing_date":  dates[i] if i < len(dates) else "",
            "accession":    accs[i]  if i < len(accs)  else "",
            "primary_doc":  pris[i]  if i < len(pris)  else "",
        })
    return sorted(out, key=lambda x: x["filing_date"], reverse=True)


def pick_pre_cutoff(filings: list[dict], cutoff: str) -> dict | None:
    for f in filings:
        if f["filing_date"] <= cutoff:
            return f
    return None


def fetch_filing(cik: str, accession: str, primary_doc: str) -> str | None:
    """Fetch the primary filing document; return text content."""
    cik_padded = str(cik).zfill(10).lstrip("0") or "0"
    acc_no_dashes = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik_padded)}/{acc_no_dashes}/{primary_doc}"
    try:
        r = httpx.get(url, headers=HEADERS, timeout=60, follow_redirects=True)
        if r.status_code != 200:
            return None
        return r.text
    except Exception:
        return None


def fetch_ticker(ticker: str, cik: str, cutoff: str) -> dict:
    """Fetch the most recent pre-cutoff 10-K for a ticker. Save to
    data/<ticker>/filings_<cutoff>/."""
    out_dir = DATA / ticker.lower() / f"filings_{cutoff.replace('-','_')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "index.json"

    if index_path.exists():
        return {"ticker": ticker, "status": "cached", "index": json.loads(index_path.read_text())}

    filings = list_10k_filings(cik)
    if not filings:
        return {"ticker": ticker, "status": "no_filings_found", "cik": cik}

    pick = pick_pre_cutoff(filings, cutoff)
    if not pick:
        return {"ticker": ticker, "status": "no_pre_cutoff_filing", "all_filings": filings[:5]}

    text = fetch_filing(cik, pick["accession"], pick["primary_doc"])
    if not text:
        return {"ticker": ticker, "status": "fetch_failed", "pick": pick}

    fname = f"{pick['accession']}_{pick['form'].replace('-','')}.txt"
    fpath = out_dir / fname
    fpath.write_text(text)
    index_path.write_text(json.dumps({
        "ticker":      ticker,
        "cik":         cik,
        "cutoff":      cutoff,
        "filing":      pick,
        "saved_to":    str(fname),
        "n_chars":     len(text),
    }, indent=2))
    return {"ticker": ticker, "status": "fetched", "filing": pick, "n_chars": len(text)}


COHORT_MODULES = [
    "verticals.public_co.defense_cohort",
    "verticals.public_co.lidar_cohort",
    "verticals.public_co.nuclear_cohort",
    "verticals.public_co.quantum_cohort",
    "verticals.public_co.hydrogen_cohort",
    "verticals.public_co.dcpivot_cohort",
    "verticals.public_co.ssbattery_cohort",
    "verticals.public_co.robotics_cohort",
    "verticals.public_co.cellgene_cohort",
    "verticals.public_co.space_cohort",
    "verticals.public_co.fintech_cohort",
    "verticals.public_co.retail_cohort",
]


def collect_cohort_tickers(modules: list[str]) -> list[tuple[str, str]]:
    import importlib
    pairs: list[tuple[str, str]] = []
    seen = set()
    for modname in modules:
        try:
            m = importlib.import_module(modname)
        except Exception:
            continue
        for member in getattr(m, "COHORT", []):
            tk = member.ticker.upper()
            if tk in seen:
                continue
            seen.add(tk)
            pairs.append((tk, member.cik))
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff", required=True, help="ISO date, e.g. 2024-05-17")
    ap.add_argument("--tickers", nargs="*", help="explicit tickers, or omit to use all cohorts")
    ap.add_argument("--cohorts", nargs="*", help="restrict to specific cohort module names")
    args = ap.parse_args()

    if args.tickers:
        import importlib
        # Need CIKs from cohort modules
        all_tickers = collect_cohort_tickers(args.cohorts or COHORT_MODULES)
        cik_map = {t: c for t, c in all_tickers}
        work = [(t.upper(), cik_map.get(t.upper(), "")) for t in args.tickers]
    else:
        work = collect_cohort_tickers(args.cohorts or COHORT_MODULES)

    print(f"Fetching pre-{args.cutoff} 10-K for {len(work)} tickers...")
    results = []
    for tk, cik in work:
        if not cik:
            results.append({"ticker": tk, "status": "no_cik"})
            print(f"  {tk}: no CIK in cohort modules")
            continue
        r = fetch_ticker(tk, cik, args.cutoff)
        results.append(r)
        status = r.get("status")
        if status == "fetched":
            d = r.get("filing", {})
            print(f"  {tk}: {status} {d.get('form')} dated {d.get('filing_date')} ({r['n_chars']} chars)")
        elif status == "cached":
            print(f"  {tk}: cached")
        else:
            print(f"  {tk}: {status}  {r}")
        time.sleep(0.2)  # be nice to EDGAR

    fetched = sum(1 for r in results if r["status"] in ("fetched", "cached"))
    print(f"\nSummary: {fetched}/{len(results)} successful")


if __name__ == "__main__":
    main()
