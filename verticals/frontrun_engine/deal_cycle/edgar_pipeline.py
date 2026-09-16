"""edgar_pipeline — the deal-cycle's DIRECT leading indicator: counts of the SEC filings that
lead IPO/M&A activity, by month, from the EDGAR quarterly master index (pipe-delimited, robust).

The forms, ordered by how EARLY they fire in the deal lifecycle:
  DRS / DRS/A   — confidential draft IPO registration (JOBS Act). The EARLIEST public IPO tell:
                  a company starts the SEC process weeks-to-months before the public S-1.
  S-1 / S-1/A   — public IPO registration (DFIN drafts these — its forward revenue).
  424B4         — IPO PRICING (the deal completes; lagging, the print itself).
  S-4           — M&A / exchange-offer registration.
  DEFM14A/PREM14A — merger proxy (deal announced/voted).
  D             — Reg-D private placement (the late-stage pre-IPO financing funnel; earliest of all).

NO LOOK-AHEAD: counts are keyed to the filing's Date-Filed (the public-observable date), never the
deal's eventual close — the censoring discipline the MAUDE/govcon pilots taught (timestamp by when the
datum was VISIBLE, not when the event happened).

Source of authority: SEC EDGAR full-index master.idx (CIK|Company|Form|Date|Filename).
"""
from __future__ import annotations
import os, time, urllib.request, collections
from pathlib import Path

HDRS = {"User-Agent": "signalos-dealcycle research 4tripathy@gmail.com"}
CACHE = Path(__file__).resolve().parent / "data" / "_idx_cache"
CACHE.mkdir(parents=True, exist_ok=True)

# forms of interest -> lifecycle bucket
FORMS = {
    "DRS": "ipo_confidential", "DRS/A": "ipo_confidential",
    "S-1": "ipo_public", "S-1/A": "ipo_public",
    "424B4": "ipo_pricing",
    "S-4": "ma_register", "S-4/A": "ma_register",
    "DEFM14A": "ma_proxy", "PREM14A": "ma_proxy",
    "D": "private_regd", "D/A": "private_regd",
}


def _quarter_idx(year: int, qtr: int) -> str:
    """Download+cache one quarter's master.idx; return its text."""
    fn = CACHE / f"master_{year}_QTR{qtr}.idx"
    if fn.exists() and fn.stat().st_size > 1000:
        return fn.read_text(errors="replace")
    url = f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{qtr}/master.idx"
    req = urllib.request.Request(url, headers=HDRS)
    txt = urllib.request.urlopen(req, timeout=60).read().decode(errors="replace")
    fn.write_text(txt)
    time.sleep(0.2)
    return txt


def monthly_counts(start_ym: str, end_ym: str) -> dict[str, dict[str, int]]:
    """{ 'YYYY-MM': {form_or_bucket: count} } over [start_ym, end_ym] inclusive (YYYY-MM strings)."""
    (sy, sm), (ey, em) = (int(x) for x in start_ym.split("-")), (int(x) for x in end_ym.split("-"))
    quarters = set()
    y, m = sy, sm
    while (y, m) <= (ey, em):
        quarters.add((y, (m - 1) // 3 + 1))
        m += 1
        if m > 12:
            y, m = y + 1, 1
    out: dict[str, dict[str, int]] = collections.defaultdict(lambda: collections.defaultdict(int))
    for (yy, qq) in sorted(quarters):
        try:
            txt = _quarter_idx(yy, qq)
        except Exception:
            continue
        for line in txt.splitlines():
            parts = line.split("|")
            if len(parts) != 5:
                continue
            form, date_filed = parts[2].strip(), parts[3].strip()
            if form not in FORMS or len(date_filed) < 7:
                continue
            ym = date_filed[:7]
            if not (start_ym <= ym <= end_ym):
                continue
            out[ym][form] += 1
            out[ym][FORMS[form]] += 1
    # collapse defaultdicts
    return {k: dict(v) for k, v in sorted(out.items())}


def pipeline_series(start_ym: str, end_ym: str) -> dict[str, dict]:
    """Aggregate buckets per month: the leading composites the monitor/lead-lag consume."""
    mc = monthly_counts(start_ym, end_ym)
    series = {}
    for ym, d in mc.items():
        ipo_lead = d.get("ipo_confidential", 0) + d.get("ipo_public", 0)      # DRS+S-1 = forward IPO supply
        ma_lead = d.get("ma_register", 0) + d.get("ma_proxy", 0)              # S-4+merger proxies
        series[ym] = {
            "ipo_confidential": d.get("ipo_confidential", 0),
            "ipo_public": d.get("ipo_public", 0),
            "ipo_pricing": d.get("ipo_pricing", 0),
            "ipo_lead": ipo_lead,
            "ma_lead": ma_lead,
            "private_regd": d.get("private_regd", 0),
        }
    return series


if __name__ == "__main__":
    import sys, json
    a = sys.argv[1] if len(sys.argv) > 1 else "2026-03"
    b = sys.argv[2] if len(sys.argv) > 2 else "2026-06"
    s = pipeline_series(a, b)
    print(json.dumps(s, indent=1))
