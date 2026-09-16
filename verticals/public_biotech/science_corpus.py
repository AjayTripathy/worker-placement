"""Science-corpus M-source: the actual scientific record behind the marketing.

Marketing claims (R) are derived from conference posters / peer-reviewed trial
publications. CT.gov registration gives the trial DESIGN but, pre-readout, no
DATA. The peer-reviewed + preprint literature is where the actual reported
effect sizes, control structure, populations, and p-values live — so it is the
M that tests whether marketing RUNS AHEAD OF THE SCIENCE.

Minimal version: Europe PMC (clean, dated REST API; covers PubMed/MED, PMC OA,
preprints incl. medRxiv). Leakage-guarded to firstPublicationDate <= cutoff — a
paper published AFTER the catalyst would leak the outcome and is dropped
mechanically, exactly like the CT.gov version guard in m_asof. Open-access full
text is pulled when available; otherwise the abstract is the M.

GET-only, public host (Ring-2 discipline).
"""
from __future__ import annotations

import json
import re
import sys

import httpx

from .catalyst_spec import CatalystCase, DATA_DIR

_BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

# Per-program literature queries + a title relevance gate. The broad query nets
# the field; the title gate keeps only PRIMARY reports of THIS program's drug or
# trial (the drug/trial named in the title), dropping generic reviews, pipeline
# surveys, and conference abstract-index dumps that merely mention the drug.
# Kept here (not in catalyst_spec) to keep the blind spec free of M-sourcing detail.
SCIENCE_QUERIES: dict[str, dict] = {
    "cassava_simufilam_p3": {
        "queries": [
            '(simufilam) AND (Alzheimer)',
            '(PTI-125) AND (Alzheimer OR filamin)',
            '(simufilam OR "PTI-125") AND (phase 2 OR cognition OR biomarker)',
        ],
        "title_must": r"simufilam|PTI-?125",
    },
    "madrigal_resmetirom_p3": {
        "queries": [
            '(resmetirom) AND (NASH OR steatohepatitis OR fibrosis)',
            '("MGL-3196") AND (NASH OR liver OR thyroid)',
            '(resmetirom) AND (MAESTRO OR "phase 2" OR biopsy)',
        ],
        "title_must": r"resmetirom|MGL-?3196|MAESTRO",
    },
    "cortexyme_atuzaginstat_gain": {
        "queries": [
            '(atuzaginstat OR "COR388") AND (Alzheimer OR gingipain OR gingivalis)',
            '("Porphyromonas gingivalis") AND (Alzheimer AND brain)',
            '(atuzaginstat OR "COR388" OR gingipain) AND (cognition OR "phase 1" OR safety)',
        ],
        "title_must": r"atuzaginstat|COR-?388|gingipain",
    },
    "karuna_karxt_emergent2": {
        "queries": [
            '(KarXT OR xanomeline) AND (schizophrenia OR psychosis OR PANSS)',
            '(xanomeline AND trospium) AND (schizophrenia OR muscarinic)',
            '(KarXT OR xanomeline) AND (EMERGENT OR "phase 2" OR antipsychotic)',
        ],
        "title_must": r"KarXT|xanomeline",
    },
    "cytokinetics_aficamten_sequoia": {
        "queries": [
            '(aficamten OR "CK-274" OR "CK-3773274") AND (cardiomyopathy OR HCM OR myosin)',
            '(aficamten) AND (hypertrophic OR obstructive OR REDWOOD OR FOREST)',
            '(aficamten OR "CK-274") AND ("phase 2" OR echocardiograph OR gradient)',
        ],
        "title_must": r"aficamten|CK-?274|CK-?3773274",
    },
    "atea_at527_moonsong": {
        "queries": [
            '("AT-527" OR bemnifosbuvir OR RO7496998) AND (COVID OR SARS-CoV-2 OR antiviral)',
            '("AT-527" OR bemnifosbuvir) AND (nucleotide OR polymerase OR hepatitis)',
            '("AT-527") AND ("phase 2" OR viral load OR efficacy)',
        ],
        "title_must": r"AT-?527|bemnifosbuvir|RO7496998",
    },
}


def _strip_xml(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _search(query: str, cutoff: str, *, page_size: int = 25) -> list[dict]:
    """Europe PMC search, hard-filtered to firstPublicationDate <= cutoff.

    The date range is also pushed into the query, but we ALWAYS re-filter
    client-side — the query date clause is a convenience, the client filter is
    the leakage guard.
    """
    cutoff_year = cutoff[:4]
    q = f'({query}) AND (FIRST_PDATE:[1990-01-01 TO {cutoff}])'
    params = {"query": q, "format": "json", "pageSize": page_size,
              "resultType": "core", "sort": "P_PDATE_D asc"}
    try:
        with httpx.Client(timeout=40, headers=HEADERS) as c:
            r = c.get(f"{_BASE}/search", params=params)
            if r.status_code != 200:
                return []
            results = r.json().get("resultList", {}).get("result", [])
    except Exception as e:
        print(f"EuropePMC search error '{query}': {e}", file=sys.stderr)
        return []
    out = []
    for a in results:
        date = a.get("firstPublicationDate") or a.get("pubYear") or ""
        if not date:
            continue
        # Leakage guard: a bare year (e.g. cutoff year) is admitted only if the
        # full date is present and <= cutoff; year-only records in the cutoff
        # year are excluded as un-datable past the catalyst.
        if len(date) == 4:
            if date < cutoff_year:
                date = f"{date}-01-01"
            else:
                continue
        if date > cutoff:
            continue
        out.append(a)
    return out


def _fulltext_excerpt(source: str, ident: str, *, max_chars: int = 6000) -> str | None:
    """Open-access full text (results-biased excerpt) if available, else None."""
    pmcid = None
    if source == "PMC" or str(ident).startswith("PMC"):
        pmcid = ident if str(ident).startswith("PMC") else f"PMC{ident}"
    if not pmcid:
        return None
    try:
        with httpx.Client(timeout=40, headers=HEADERS) as c:
            r = c.get(f"{_BASE}/{pmcid}/fullTextXML")
            if r.status_code != 200:
                return None
            xml = r.text
    except Exception:
        return None
    # Prefer the results/efficacy sections — that's where marketing-vs-data lives.
    m = re.search(r"<sec[^>]*>.*?(result|efficacy|outcome).*?</sec>", xml,
                  re.I | re.S)
    chunk = m.group(0) if m else xml
    return _strip_xml(chunk)[:max_chars]


def build_science_corpus(case: CatalystCase, *, verbose: bool = True) -> dict:
    spec = SCIENCE_QUERIES.get(case.case_id, {})
    queries = spec.get("queries", [])
    title_must = re.compile(spec["title_must"], re.I) if spec.get("title_must") else None
    seen: set[str] = set()
    records: list[dict] = []
    for q in queries:
        for a in _search(q, case.cutoff):
            key = f"{a.get('source')}:{a.get('id')}"
            if key in seen:
                continue
            if title_must and not title_must.search(a.get("title") or ""):
                continue
            seen.add(key)
            date = a.get("firstPublicationDate") or f"{a.get('pubYear')}-01-01"
            rec = {
                "id": key,
                "source": a.get("source"),
                "pmid": a.get("pmid"),
                "doi": a.get("doi"),
                "date": date,
                "journal": (a.get("journalInfo") or {}).get("journal", {}).get("title"),
                "title": a.get("title"),
                "is_open_access": a.get("isOpenAccess") == "Y",
                "abstract": _strip_xml(a.get("abstractText") or ""),
                "fulltext_excerpt": None,
                "url": f"https://europepmc.org/article/{a.get('source')}/{a.get('id')}",
            }
            if rec["is_open_access"] and a.get("pmcid"):
                rec["fulltext_excerpt"] = _fulltext_excerpt("PMC", a.get("pmcid"))
            records.append(rec)
    records.sort(key=lambda r: r["date"])
    out = {"case_id": case.case_id, "ticker": case.ticker, "cutoff": case.cutoff,
           "n_records": len(records), "records": records}
    out_dir = DATA_DIR / case.ticker / "science"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "corpus.json").write_text(json.dumps(out, indent=2, default=str))
    if verbose:
        print(f"[{case.ticker}] science corpus: {len(records)} records "
              f"(<= {case.cutoff})", file=sys.stderr)
        for r in records:
            ft = "FT" if r["fulltext_excerpt"] else "abs"
            print(f"    {r['date']} [{ft}] {r['journal'] or r['source']}: "
                  f"{(r['title'] or '')[:72]}", file=sys.stderr)
    return out


def load_science_corpus(case: CatalystCase) -> list[dict]:
    p = DATA_DIR / case.ticker / "science" / "corpus.json"
    if not p.exists():
        return []
    return json.loads(p.read_text()).get("records", [])


if __name__ == "__main__":
    from .catalyst_spec import CASES
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("case_id", nargs="?", default="all")
    args = ap.parse_args()
    targets = list(CASES.values()) if args.case_id == "all" else [CASES[args.case_id]]
    for case in targets:
        build_science_corpus(case)
