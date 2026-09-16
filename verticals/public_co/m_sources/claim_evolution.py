"""
Claim-evolution tracking — test whether a focal company's subsequent
filings AFFIRM, AMEND, TERMINATE, or are UNRELATED to a previously-
disclosed claim. v3: LLM-based semantic classification.

WHY V3 REPLACED V2:
V2 used keyword-proximity matching: it looked for the search_term within
N chars of an "adverse" keyword list (terminate / cancel / material
adverse / etc.). This generated massive false positives:

  - M&A contracts ALWAYS contain termination boilerplate. Filing an
    Amended-and-Restated Merger Agreement triggered ADVERSE_EVENT
    detection even though the merger was being STRENGTHENED.
  - License-agreement amendments triggered the detector because every
    license has "termination conditions" sections.
  - "going concern" mentioned near "going concern" was matched as
    adverse despite being a self-reference (claim re-asserted, not
    resolved).

In the fraud-vs-control test (2026-05-18), all 3 of CEI's SEVERE flags
and 1 of WKHS's 2 SEVERE flags turned out to be v2 false positives.

WHAT V3 DOES:
1. edgar_fts.query_fulltext to find subsequent filings mentioning the
   search_term (unchanged from v2 — this is cheap).
2. For each mentioning filing (cap at 6), fetch the body and extract a
   wide snippet (~2000 chars) around the first occurrence of the term.
3. Send each snippet to Haiku for classification: AFFIRMED | AMENDED |
   TERMINATED | UNRELATED.
4. Aggregate: any TERMINATED → ADVERSE_EVENT_DETECTED; any substantive
   AMENDED → AMENDMENT_DETECTED; otherwise REAFFIRMED or SILENT.

Outputs preserve the v2 shape for backward compat with deterministic_scorer.
The `adverse_findings` list now carries LLM `classification` and `reasoning`
fields per finding; `adverse_hits` and `amendment_hits` retain the keyword-
list shape for any consumer that reads them but are now populated from
the LLM's own terminology, not regex hits.

If the anthropic SDK or API key is unavailable, query returns
evolution_status="UNKNOWN_LLM_UNAVAILABLE" with an explanation, rather
than falling back to the noisy keyword path (per LLM-only design choice
2026-05-18).
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "Tracks whether later filings AFFIRM/AMEND/TERMINATE a previously disclosed claim (LLM semantic classification).",
}

import json
import re
import sys
from datetime import datetime, timedelta

import httpx

from . import edgar_fts
from . import disclosure_classifier  # shared LLM helper (2026-05-29 refactor)

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

# Backward-compat re-exports for callers that imported _MODEL / _SDK_CLIENT
_MODEL = disclosure_classifier.model_name()
_SDK_CLIENT = disclosure_classifier._SDK_CLIENT  # type: ignore[attr-defined]
_SDK_ERROR = disclosure_classifier.unavailable_reason()


def _llm_classify(search_term: str, snippet: str, form: str,
                  filing_date: str) -> dict:
    """Thin wrapper preserving the (form, filing_date) call signature.
    Delegates to disclosure_classifier.classify()."""
    return disclosure_classifier.classify(
        search_term=search_term,
        snippet=snippet,
        venue=form,
        disclosure_date=filing_date,
    )


def _fetch_filing_body(cik: str, accession_with_doc: str) -> str | None:
    """accession_with_doc format from edgar_fts: 'NNNNNNNNNN-NN-NNNNNN:filename.htm'."""
    if ":" not in accession_with_doc:
        return None
    acc, doc = accession_with_doc.split(":", 1)
    acc_no_dashes = acc.replace("-", "")
    cik_int = str(int(str(cik).lstrip("0") or "0"))
    url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_no_dashes}/{doc}"
    try:
        r = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
        if r.status_code != 200:
            return None
        return r.text
    except Exception:
        return None


def _extract_snippet(text: str, search_term: str,
                      window_chars: int = 1200) -> str | None:
    """Extract a wide snippet around the first occurrence of search_term.
    HTML-stripped and whitespace-collapsed."""
    if not text:
        return None
    plain = re.sub(r"<[^>]+>", " ", text)
    plain = re.sub(r"\s+", " ", plain)
    term_low = search_term.lower()
    plain_low = plain.lower()
    idx = plain_low.find(term_low)
    if idx < 0:
        return None
    start = max(0, idx - window_chars)
    end = min(len(plain), idx + window_chars)
    return plain[start:end]


def query_claim_evolution(
    cik: str,
    search_term: str,
    base_filing_date: str,
    cutoff_date: str,
    forms: str = "10-K,10-Q,8-K,DEF 14A",
    max_classify: int = 6,
) -> dict:
    """Search the focal CIK's filings after base_filing_date and before
    cutoff_date for mentions of search_term, then LLM-classify each
    mentioning filing as AFFIRMED / AMENDED / TERMINATED / UNRELATED.

    Args:
      cik: 10-digit padded CIK of the focal company.
      search_term: the entity, dollar amount, or term to search for.
      base_filing_date: ISO date of the original claim's filing (window starts day+1).
      cutoff_date: ISO date upper bound on the search window.
      forms: comma-separated SEC form types to include.
      max_classify: max filings to fetch + LLM-classify (cost control).
    """
    try:
        base = datetime.fromisoformat(base_filing_date)
    except ValueError:
        return {"error": f"bad base_filing_date: {base_filing_date}"}
    start = (base + timedelta(days=1)).strftime("%Y-%m-%d")

    r = edgar_fts.query_fulltext(
        search_term=search_term,
        cutoff_date=cutoff_date,
        cik=cik,
        start_date=start,
        forms=forms,
    )
    if "error" in r:
        return {**r, "evolution_status": "UNKNOWN",
                "window_start": start, "window_end": cutoff_date}

    hits = r.get("total_hits", 0)
    top = r.get("top_filings", [])
    forms_seen = sorted({f.get("form") for f in top if f.get("form")})
    structured = {"10-K", "10-Q", "DEF 14A", "20-F", "40-F"}

    # LLM-classify each top filing. Prioritize 8-Ks (where amendments/
    # terminations surface) but include structured forms too if they're
    # the only mentions.
    candidates = list(top)
    candidates.sort(key=lambda f: 0 if f.get("form", "").startswith("8-K") else 1)
    candidates = candidates[:max_classify]

    findings: list[dict] = []
    n_classified = 0
    n_terminated = 0
    n_amended = 0
    n_affirmed = 0
    n_unrelated = 0

    for f in candidates:
        body = _fetch_filing_body(cik, f.get("accession", ""))
        if not body:
            continue
        snippet = _extract_snippet(body, search_term)
        if not snippet:
            continue
        cls = _llm_classify(search_term=search_term, snippet=snippet,
                             form=f.get("form", ""),
                             filing_date=f.get("filing_date", ""))
        if "error" in cls:
            findings.append({
                "form":            f.get("form"),
                "filing_date":     f.get("filing_date"),
                "accession":       f.get("accession"),
                "snippet":         snippet[:500],
                "classification":  "ERROR",
                "reasoning":       cls.get("error", ""),
                "adverse_hits":    [],
                "amendment_hits":  [],
            })
            continue
        n_classified += 1
        c = cls["classification"]
        if c == "TERMINATED":
            n_terminated += 1
        elif c == "AMENDED":
            n_amended += 1
        elif c == "AFFIRMED":
            n_affirmed += 1
        else:
            n_unrelated += 1
        # For backward compat, populate adverse_hits/amendment_hits from
        # the LLM verdict so existing scorer text rendering works.
        adverse_hits = ["llm_terminated"] if c == "TERMINATED" else []
        amendment_hits = ["llm_amended"] if c == "AMENDED" else []
        findings.append({
            "form":            f.get("form"),
            "filing_date":     f.get("filing_date"),
            "accession":       f.get("accession"),
            "snippet":         snippet[:500],
            "classification":  c,
            "reasoning":       cls.get("reasoning", ""),
            "adverse_hits":    adverse_hits,
            "amendment_hits":  amendment_hits,
        })

    # Aggregate
    if _SDK_CLIENT is None:
        status = "UNKNOWN_LLM_UNAVAILABLE"
    elif hits == 0:
        status = "SILENT_POST_CLAIM"
    elif n_terminated > 0:
        status = "ADVERSE_EVENT_DETECTED"
    elif n_amended > 0:
        status = "AMENDMENT_DETECTED"
    elif n_affirmed > 0 and any(f in structured for f in forms_seen):
        status = "REAFFIRMED_IN_STRUCTURED_DISCLOSURE"
    elif n_affirmed > 0:
        status = "REAFFIRMED_IN_8K_ONLY"
    else:
        # mentions exist but LLM classified all as UNRELATED (or no classified)
        status = "MENTIONED_INCIDENTALLY"

    # For backward-compat with old scorer code, only the TERMINATED /
    # AMENDED findings get put in adverse_findings (since that field
    # historically meant "things that triggered the adverse path").
    adverse_findings = [f for f in findings
                         if f.get("classification") in ("TERMINATED", "AMENDED")]

    return {
        "cik":                   cik,
        "search_term":           search_term,
        "window_start":          start,
        "window_end":            cutoff_date,
        "n_subsequent_mentions": hits,
        "forms_mentioning":      forms_seen,
        "evolution_status":      status,
        "adverse_findings":      adverse_findings,
        "all_classifications":   findings,
        "classification_counts": {
            "AFFIRMED":   n_affirmed,
            "AMENDED":    n_amended,
            "TERMINATED": n_terminated,
            "UNRELATED":  n_unrelated,
        },
        "top_filings":           top,
        "llm_model":             _MODEL if _SDK_CLIENT else None,
    }


if __name__ == "__main__":
    cik = sys.argv[1] if len(sys.argv) > 1 else "0001309082"   # CEI
    term = sys.argv[2] if len(sys.argv) > 2 else "Viking"
    base = sys.argv[3] if len(sys.argv) > 3 else "2020-06-29"
    cutoff = sys.argv[4] if len(sys.argv) > 4 else "2021-09-01"
    print(json.dumps(query_claim_evolution(cik, term, base, cutoff), indent=2,
                     default=str))
