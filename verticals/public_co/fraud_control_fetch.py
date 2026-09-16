"""
Fetch the best pre-cutoff substantive filing for each fraud_control_cohort
member. Unlike backtest_fetch_filings (which only picks 10-K/20-F), this
falls back through 10-K → 10-K/A → S-1 → 10-Q → 10-Q/A based on what's
available before each member's pre-revelation cutoff.

Writes to data/<ticker>/filings_<cutoff>/ to match the planner-prompt
filings_<cutoff_slug>/ convention.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

from . import edgar
from .fraud_control_cohort import COHORT

HERE = Path(__file__).parent
DATA = HERE / "data"
HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

FORM_PRIORITY = ["10-K", "10-K/A", "20-F", "S-1", "S-1/A", "10-Q", "10-Q/A"]

# Per-ticker accession overrides. Use when auto-pick lands on a pre-merger
# SPAC shell filing instead of the post-merger operating business filing.
OVERRIDES: dict[str, dict] = {
    # NKLA inherited VectoIQ's CIK; 2020-03-06 "10-K" is the VectoIQ SPAC
    # shell annual report (no Nikola content). Use post-merger S-1 instead.
    "NKLA": {
        "form":        "S-1",
        "filing_date": "2020-07-17",
        "accession":   "0001047469-20-004147",
        "primary_doc": "a2241967zs-1.htm",
    },
    # RIDE inherited DiamondPeak's CIK; 2020-03-25 "10-K" is the DiamondPeak
    # SPAC shell. Use post-merger Lordstown S-1.
    "RIDE": {
        "form":        "S-1",
        "filing_date": "2020-11-12",
        "accession":   "0001104659-20-124501",
        "primary_doc": "tm2035569-1_s1.htm",
    },
}


def list_filings(cik: str) -> list[dict]:
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
        out.append({
            "form":         f,
            "filing_date":  dates[i] if i < len(dates) else "",
            "accession":    accs[i]  if i < len(accs)  else "",
            "primary_doc":  pris[i]  if i < len(pris)  else "",
        })
    return out


def pick_substantive_pre_cutoff(filings: list[dict], cutoff: str) -> dict | None:
    """Pick the highest-priority form filed at or before cutoff. Within a
    form priority, take the most recent."""
    pre = [f for f in filings if f["filing_date"] <= cutoff]
    for form in FORM_PRIORITY:
        candidates = [f for f in pre if f["form"] == form]
        if candidates:
            candidates.sort(key=lambda x: x["filing_date"], reverse=True)
            return candidates[0]
    return None


def fetch_filing_text(cik: str, accession: str, primary_doc: str) -> str | None:
    cik_int = int(str(cik).lstrip("0") or "0")
    acc_no_dashes = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_no_dashes}/{primary_doc}"
    try:
        r = httpx.get(url, headers=HEADERS, timeout=120, follow_redirects=True)
        if r.status_code != 200:
            return None
        return r.text
    except Exception as e:
        print(f"  fetch error: {e}")
        return None


def fetch_member(m) -> dict:
    cutoff_slug = m.cutoff.replace("-", "_")
    out_dir = DATA / m.ticker.lower() / f"filings_{cutoff_slug}"
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "index.json"

    if index_path.exists():
        return {"ticker": m.ticker, "status": "cached",
                "index": json.loads(index_path.read_text())}

    if m.ticker in OVERRIDES:
        pick = OVERRIDES[m.ticker]
    else:
        filings = list_filings(m.cik)
        if not filings:
            return {"ticker": m.ticker, "status": "no_filings_found"}
        pick = pick_substantive_pre_cutoff(filings, m.cutoff)
        if not pick:
            return {"ticker": m.ticker, "status": "no_pre_cutoff_filing"}

    text = edgar.fetch_filing_clean(m.cik, pick["accession"], pick["primary_doc"])
    if not text:
        return {"ticker": m.ticker, "status": "fetch_failed", "pick": pick}

    fname = f"{pick['accession']}_{pick['form'].replace('-','').replace('/','')}.txt"
    fpath = out_dir / fname
    fpath.write_text(text)
    index = {
        "ticker":   m.ticker,
        "cik":      m.cik,
        "cutoff":   m.cutoff,
        "klass":    m.klass,
        "filing":   pick,
        "saved_to": str(fname),
        "n_chars":  len(text),
    }
    index_path.write_text(json.dumps(index, indent=2))
    return {"ticker": m.ticker, "status": "fetched",
            "form": pick["form"], "filing_date": pick["filing_date"],
            "n_chars": len(text)}


def main():
    print(f"Fetching pre-revelation filings for {len(COHORT)} members...")
    results = []
    for m in COHORT:
        r = fetch_member(m)
        results.append(r)
        if r["status"] == "fetched":
            print(f"  {m.ticker} [{m.klass}] cutoff={m.cutoff}: "
                  f"{r['form']} dated {r['filing_date']} ({r['n_chars']:,} chars)")
        elif r["status"] == "cached":
            idx = r["index"]
            print(f"  {m.ticker} [{m.klass}]: cached "
                  f"{idx['filing']['form']} dated {idx['filing']['filing_date']}")
        else:
            print(f"  {m.ticker} [{m.klass}]: {r['status']}  {r}")
        time.sleep(0.3)

    fetched = sum(1 for r in results if r["status"] in ("fetched", "cached"))
    print(f"\nSummary: {fetched}/{len(results)} successful")


if __name__ == "__main__":
    main()
