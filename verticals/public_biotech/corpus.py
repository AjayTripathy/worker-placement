"""Blinded R-corpus fetcher: pre-cutoff marketing from SEC EDGAR.

The R of a biotech catalyst lives in promotional disclosure — press releases and
investor presentations — which companies file as 8-K EXHIBITS (EX-99.x), not in
the 8-K cover body. This module pulls those exhibits for a CatalystCase, strictly
filtered to filings dated on or before the case cutoff, so the blind is enforced
by EDGAR's own date stamps rather than by analyst discipline.

Scope of what we ingest (the marketing surface most prone to catalyst spin):
  - 8-K item 2.02  Results of Operations / trial data press releases
  - 8-K item 7.01  Reg FD Disclosure (investor decks, conference PRs)
  - 8-K item 8.01  Other Events (program updates, regulatory correspondence)
Each EX-99.* .htm exhibit is de-tagged to text and written with a provenance
header. PDF/graphic exhibits (investor decks filed as images) are logged but not
OCR'd here — a figure pass is a separate step.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import httpx

from .catalyst_spec import CatalystCase, DATA_DIR

HEADERS = {"User-Agent": "Signal OS Research 4tripathy@gmail.com"}
MARKETING_8K_ITEMS = {"2.02", "7.01", "8.01"}
# Exhibit filenames vary wildly across filers and eras:
#   Madrigal:  d409333dex991.htm
#   Cassava:   ex_727922.htm  /  sava-20221118xex99_1.htm  /  exh_991.htm
# Match an 'ex'/'exh'/'exhibit' token (possibly embedded, e.g. 'xex99' or the
# full-word 'exhibit9912026.htm') followed by a digit, or a 'press' marker. The
# (?:hibit)? alt is required: many filers name press releases 'exhibit991.htm',
# where the letters between 'ex' and the digits defeat a bare 'exh?[-_]?\d'.
# The doc-TYPE filter below then keeps only EX-99.
# Exclude the 8-K cover, XBRL R-renditions, and index/summary scaffolding.
_EX_RE = re.compile(r"ex(?:hibit|h)?[-_\s]?\d|press", re.I)
_EX_EXCLUDE_RE = re.compile(r"(8[-_]?k|^r\d+\.htm|index|filingsummary|metalinks|_htm\.xml)", re.I)


def _submissions(cik: str) -> dict:
    cik_padded = cik.lstrip("0").rjust(10, "0")
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    with httpx.Client(timeout=30, headers=HEADERS) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.json()


def _accession_files(cik: str, accession: str) -> list[dict]:
    cik_int = cik.lstrip("0")
    acc = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc}/index.json"
    with httpx.Client(timeout=30, headers=HEADERS) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.json().get("directory", {}).get("item", [])


def _fetch_text(cik: str, accession: str, name: str) -> str:
    cik_int = cik.lstrip("0")
    acc = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc}/{name}"
    with httpx.Client(timeout=60, headers=HEADERS) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.text


def _detag(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?</\1>", " ", html)
    txt = re.sub(r"<[^>]+>", " ", html)
    txt = re.sub(r"&#160;|&nbsp;", " ", txt)
    txt = re.sub(r"&amp;", "&", txt)
    txt = re.sub(r"&#?\w+;", " ", txt)
    return re.sub(r"\s+", " ", txt).strip()


def _select_8ks(submissions: dict, case: CatalystCase) -> list[dict]:
    recent = submissions.get("filings", {}).get("recent", {})
    n = len(recent.get("accessionNumber", []))
    out = []
    for i in range(n):
        form = recent["form"][i]
        fdate = recent["filingDate"][i]
        if form != "8-K":
            continue
        if not (case.marketing_window_start <= fdate <= case.cutoff):
            continue
        items = set((recent.get("items", [""] * n)[i] or "").split(","))
        items = {x.strip() for x in items if x.strip()}
        if items and not (items & MARKETING_8K_ITEMS):
            continue  # an 8-K with only non-marketing items (e.g. 5.02 only)
        out.append({
            "accession": recent["accessionNumber"][i],
            "filing_date": fdate,
            "items": sorted(items),
        })
    return out


def fetch_corpus(case: CatalystCase, *, limit: int | None = None,
                 verbose: bool = True) -> dict:
    """Pull pre-cutoff 8-K EX-99 marketing exhibits for `case`.

    Writes text exhibits + a corpus_index.json under data/<ticker>/corpus/ and
    returns the index dict. Idempotent: existing non-empty exhibit files are
    skipped.
    """
    out_dir = DATA_DIR / case.case_id / "corpus"
    out_dir.mkdir(parents=True, exist_ok=True)

    subs = _submissions(case.cik)
    eight_ks = _select_8ks(subs, case)
    eight_ks.sort(key=lambda r: r["filing_date"], reverse=True)
    if limit:
        eight_ks = eight_ks[:limit]
    if verbose:
        print(f"[{case.ticker}] {len(eight_ks)} marketing 8-Ks in "
              f"[{case.marketing_window_start} .. {case.cutoff}]", file=sys.stderr)

    index: list[dict] = []
    for r in eight_ks:
        try:
            files = _accession_files(case.cik, r["accession"])
        except Exception as e:
            print(f"  index FAIL {r['accession']}: {e}", file=sys.stderr)
            continue
        ex_htms = [f for f in files
                   if f["name"].lower().endswith((".htm", ".html"))
                   and _EX_RE.search(f["name"])
                   and not _EX_EXCLUDE_RE.search(f["name"])]
        for f in ex_htms:
            stem = f"{r['filing_date']}_{r['accession']}_{f['name']}".replace("/", "_")
            stem = re.sub(r"\.html?$", ".txt", stem)
            dest = out_dir / stem
            if dest.exists() and dest.stat().st_size > 500:
                index.append(_index_row(case, r, f, dest))
                continue
            try:
                raw = _fetch_text(case.cik, r["accession"], f["name"])
            except Exception as e:
                print(f"  exhibit FAIL {f['name']}: {e}", file=sys.stderr)
                continue
            text = _detag(raw)
            if len(text) < 200:
                continue
            # Keep only EX-99 exhibits (press releases / investor decks). Other
            # exhibit classes (EX-10 agreements, EX-3 charter, EX-5 opinion)
            # match the loose filename regex but aren't marketing. The doc type
            # is the leading token of the de-tagged text, rendered either as
            # "EX-99.1 ..." or "Exhibit 99.1 ..." — handle both forms.
            type_m = re.match(r"\s*ex(?:hibit)?[-\s]?(\d+)", text, re.I)
            if type_m and type_m.group(1) != "99":
                continue
            header = (f"SOURCE: SEC EDGAR 8-K exhibit\n"
                      f"COMPANY: {case.company} ({case.ticker})\n"
                      f"FILING_DATE: {r['filing_date']}\n"
                      f"ACCESSION: {r['accession']}\n"
                      f"ITEMS: {','.join(r['items'])}\n"
                      f"EXHIBIT: {f['name']}\n"
                      f"{'='*70}\n")
            dest.write_text(header + text)
            index.append(_index_row(case, r, f, dest))
            if verbose:
                print(f"  + {r['filing_date']} {f['name']} ({len(text)//1024} KB)",
                      file=sys.stderr)
            time.sleep(0.15)

    (out_dir / "corpus_index.json").write_text(json.dumps({
        "case_id": case.case_id, "cutoff": case.cutoff,
        "marketing_window_start": case.marketing_window_start,
        "n_exhibits": len(index), "exhibits": index,
    }, indent=2))
    if verbose:
        print(f"[{case.ticker}] corpus: {len(index)} exhibits -> {out_dir}", file=sys.stderr)
    return {"out_dir": str(out_dir), "n_exhibits": len(index), "exhibits": index}


def _index_row(case: CatalystCase, r: dict, f: dict, dest: Path) -> dict:
    return {
        "filing_date": r["filing_date"],
        "accession": r["accession"],
        "items": r["items"],
        "exhibit": f["name"],
        "path": str(dest.relative_to(DATA_DIR)),
        "url": (f"https://www.sec.gov/Archives/edgar/data/"
                f"{case.cik.lstrip('0')}/{r['accession'].replace('-','')}/{f['name']}"),
    }


if __name__ == "__main__":
    from .catalyst_spec import CASES
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("case_id", nargs="?", help="case id, or 'all'")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    targets = CASES.values() if (args.case_id in (None, "all")) else [CASES[args.case_id]]
    for case in targets:
        fetch_corpus(case, limit=args.limit)
