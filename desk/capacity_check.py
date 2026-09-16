"""capacity_check — the BENCH-TIME detector, generalized (built after the IBEX 94%-offshore-utilization
read, 2026-07-03). 'Bench' wears different words per industry: workstations/seats (BPO), utilization %
(IT services), occupancy (hotels/REITs/CCRCs), load factor (airlines), capacity utilization (manufacturing),
beds (hospitals). The SIGNAL is the same everywhere: HIGH utilization + capacity BUILD = management's capex
is its own revealed demand forecast; utilization FALLING = demand rolling over before revenue shows it.

Pulls the latest 10-K text from EDGAR and extracts every utilization/capacity disclosure with its numbers.
An extraction assist for DDs — findings quote the filing verbatim; NOT_DISCLOSED is a finding too.

  python3 -m desk.capacity_check IBEX
READ-ONLY.
"""
from __future__ import annotations
import json, re, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}
KEYWORDS = ["utilization", "workstation", "capacity", "occupancy", "load factor", "seats in use",
            "billable", "bench", "beds in service", "available seat"]


def _cik(ticker: str) -> str | None:
    from desk.seasonality import _cik as f
    return f(ticker)


def latest_10k_text(ticker: str) -> str | None:
    cik = _cik(ticker)
    if not cik:
        return None
    try:
        req = urllib.request.Request(f"https://data.sec.gov/submissions/CIK{cik}.json", headers=HDRS)
        subs = json.load(urllib.request.urlopen(req, timeout=30))
        recent = subs["filings"]["recent"]
        for i, form in enumerate(recent["form"]):
            if form == "10-K":
                acc = recent["accessionNumber"][i].replace("-", "")
                doc = recent["primaryDocument"][i]
                url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{doc}"
                req2 = urllib.request.Request(url, headers=HDRS)
                raw = urllib.request.urlopen(req2, timeout=60).read().decode("utf-8", "ignore")
                txt = re.sub(r"<[^>]+>", " ", raw)
                return re.sub(r"\s+", " ", txt)
    except Exception:
        return None
    return None


def check(ticker: str) -> dict:
    txt = latest_10k_text(ticker)
    if not txt:
        return {"ticker": ticker, "status": "NO_10K_TEXT"}
    findings = []
    for kw in KEYWORDS:
        for m in re.finditer(re.escape(kw), txt, re.I):
            a, b = max(0, m.start() - 300), m.start() + 400
            seg = txt[a:b]
            # keep only segments with actual numbers (percentages or counts)
            if re.search(r"\d{1,3}(\.\d)?\s?%", seg) or re.search(r"\b\d{1,3},\d{3}\b", seg):
                findings.append({"keyword": kw, "excerpt": seg.strip()[:420]})
            if len([f for f in findings if f["keyword"] == kw]) >= 2:
                break
    # dedupe near-identical excerpts
    seen, uniq = set(), []
    for f in findings:
        key = f["excerpt"][:120]
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    return {"ticker": ticker, "status": "OK" if uniq else "NOT_DISCLOSED",
            "n_findings": len(uniq), "findings": uniq[:10],
            "doctrine": "HIGH util + capacity build = revealed demand forecast; util falling = demand rolling; NOT_DISCLOSED = a finding (ask why the DD's utilization question can't be answered)"}


def main():
    t = sys.argv[1] if len(sys.argv) > 1 else "IBEX"
    r = check(t)
    print(f"=== CAPACITY/BENCH CHECK  {t}  ({r['status']}, {r.get('n_findings', 0)} numeric disclosures) ===")
    for f in r.get("findings", []):
        print(f"  [{f['keyword']}] ...{f['excerpt'][:300]}...")


if __name__ == "__main__":
    main()
