"""Build a survivorship-free IPO cohort for the 2024-H1 -> 2025-H1 backtest.

Primary source = EDGAR quarterly full-index `form.idx`. It is a static,
complete list of every filing by form type, so the ENTRY side carries no
survivorship bias (delisted names keep their original 424B4 filing forever).

Pipeline:
  1. Cache 6 quarters of form.idx locally (_raw_idx/), download once.
  2. Parse 424B4 / 424B1 (final IPO prospectus, filed at pricing).
  3. Dedupe by CIK -> EARLIEST such filing = the IPO pricing event.
  4. Drop SPAC / fund / shell via the ipo_pipeline predicates.
  5. Enrich via the submissions endpoint, with a POINT-IN-TIME primary-IPO
     check: count public filings (10-K/10-Q/8-K/20-F/40-F/6-K) dated BEFORE
     the 424B4. Zero => primary IPO; >0 => follow-on (excluded).
  6. Write cohort.json.

Run:
  python3 verticals/buyside_dd/data/_ipo_backtest_2024_2025/cohort_builder.py build
  python3 .../cohort_builder.py enrich      # network: submissions per CIK
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
RAW_IDX = HERE / "_raw_idx"
CANDIDATES = HERE / "candidates.json"
COHORT = HERE / "cohort.json"

_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from verticals.buyside_dd.ipo_pipeline import is_fund, is_shell, is_spac

UA = {"User-Agent": "SignalOS research 4tripathy@gmail.com"}

# 2024-H1 -> 2025-H1 = six quarters (IPO pricing window).
QUARTERS = [(2024, 1), (2024, 2), (2024, 3), (2024, 4), (2025, 1), (2025, 2)]

# 424B4 / 424B1 = final prospectus filed at pricing. 424B3 is resale/shelf -> excluded.
IPO_PRICING_FORMS = {"424B4", "424B1"}

PUBLIC_FORMS = {"10-K", "10-Q", "10-K/A", "10-Q/A", "8-K", "20-F", "40-F", "6-K", "10-KT"}

# Non-operating issuers that pass the name filter but aren't real operating IPOs.
SIC_EXCLUDE = {
    "6770": "Blank Checks (SPAC)",
    "6189": "Asset-Backed Securities (securitization trust)",
}

LINE_RE = re.compile(r"^(.{12})(.+?)\s+(\d{1,10})\s+(\d{4}-\d{2}-\d{2})\s+(edgar/\S+?)\s*$")


def _get(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def cache_indices() -> None:
    RAW_IDX.mkdir(parents=True, exist_ok=True)
    for yr, qtr in QUARTERS:
        dest = RAW_IDX / f"form_{yr}_QTR{qtr}.idx"
        if dest.exists() and dest.stat().st_size > 0:
            continue
        url = f"https://www.sec.gov/Archives/edgar/full-index/{yr}/QTR{qtr}/form.idx"
        print(f"  downloading {url}", file=sys.stderr)
        dest.write_bytes(_get(url))
        time.sleep(0.3)


def parse_pricing_filings() -> list[dict]:
    rows: list[dict] = []
    for yr, qtr in QUARTERS:
        path = RAW_IDX / f"form_{yr}_QTR{qtr}.idx"
        text = path.read_text(encoding="latin-1")
        for line in text.splitlines():
            form = line[:12].strip()
            if form not in IPO_PRICING_FORMS:
                continue
            m = LINE_RE.match(line)
            if not m:
                continue
            _f, company, cik, fdate, fpath = m.groups()
            rows.append({
                "form": form,
                "company_name": company.strip(),
                "cik": str(int(cik)),
                "file_date": fdate,
                "filing_path": fpath,
            })
    return rows


def dedupe_and_filter(rows: list[dict]) -> tuple[list[dict], dict]:
    """Keep EARLIEST pricing filing per CIK; drop SPAC/fund/shell."""
    by_cik: dict[str, dict] = {}
    for r in rows:
        cik = r["cik"]
        ex = by_cik.get(cik)
        if ex is None or r["file_date"] < ex["file_date"]:
            by_cik[cik] = r
    kept, skipped = [], {"spac": 0, "fund": 0, "shell": 0}
    for r in by_cik.values():
        name = r["company_name"]
        if is_spac(name):
            skipped["spac"] += 1
        elif is_fund(name):
            skipped["fund"] += 1
        elif is_shell(name):
            skipped["shell"] += 1
        else:
            kept.append(r)
    kept.sort(key=lambda x: x["file_date"])
    return kept, skipped


def build() -> None:
    cache_indices()
    rows = parse_pricing_filings()
    print(f"Raw 424B4/424B1 filings (6 quarters): {len(rows)}", file=sys.stderr)
    kept, skipped = dedupe_and_filter(rows)
    print(f"After dedupe-by-CIK + SPAC/fund/shell drop: {len(kept)} "
          f"(skipped {skipped})", file=sys.stderr)
    CANDIDATES.write_text(json.dumps(
        {"window": "2024-H1..2025-H1", "n_candidates": len(kept),
         "skipped": skipped, "candidates": kept}, indent=2))
    print(f"Wrote {CANDIDATES.name}", file=sys.stderr)


def _point_in_time_prior_public(recent: dict, ipo_date: str) -> int:
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    n = 0
    for i, f in enumerate(forms):
        d = dates[i] if i < len(dates) else ""
        if f in PUBLIC_FORMS and d and d < ipo_date:
            n += 1
    return n


def enrich() -> None:
    data = json.loads(CANDIDATES.read_text())
    cands = data["candidates"]
    enriched, follow_on, errors, sic_excluded = [], 0, 0, 0
    for i, c in enumerate(cands):
        cik = int(c["cik"])
        url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
        try:
            d = json.loads(_get(url, timeout=30))
        except Exception as e:
            print(f"  [{i+1}/{len(cands)}] ERR {c['company_name'][:40]}: {e}", file=sys.stderr)
            errors += 1
            time.sleep(0.2)
            continue
        recent = d.get("filings", {}).get("recent", {})
        prior = _point_in_time_prior_public(recent, c["file_date"])
        sic = d.get("sic")
        if sic in SIC_EXCLUDE:
            sic_excluded += 1
        elif prior > 0:
            follow_on += 1
        else:
            enriched.append({
                **c,
                "name_official": d.get("name"),
                "sic": d.get("sic"),
                "sic_description": d.get("sicDescription"),
                "tickers": d.get("tickers", []),
                "exchanges": d.get("exchanges", []),
                "ipo_date": c["file_date"],
                "prior_public_filings_pit": prior,
            })
        if i % 10 == 9:
            print(f"  enriched {i+1}/{len(cands)} (kept {len(enriched)}, follow-on {follow_on}, err {errors})", file=sys.stderr)
        time.sleep(0.15)
    COHORT.write_text(json.dumps(
        {"window": "2024-H1..2025-H1", "n_primary_ipo": len(enriched),
         "n_follow_on_excluded": follow_on, "n_sic_excluded": sic_excluded,
         "n_errors": errors, "cohort": enriched}, indent=2))
    print(f"\nPrimary IPOs: {len(enriched)} | follow-on: {follow_on} | "
          f"sic-excluded: {sic_excluded} | errors: {errors}", file=sys.stderr)
    print(f"Wrote {COHORT.name}", file=sys.stderr)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "build":
        build()
    elif cmd == "enrich":
        enrich()
    else:
        print("usage: cohort_builder.py [build|enrich]", file=sys.stderr)
        sys.exit(2)
