"""Stage 0.5 (biotech): DETERMINISTIC forward-leak check on the fetched corpus —
run AFTER fetch_corpus, BEFORE extract_claims, no model, no credits.

Why this exists
---------------
A LIVE case is only a blind forward test if the catalyst has NOT yet read out as
of the cutoff. The binding gate (verify_binding) confirms we point at the RIGHT
trial, but it cannot tell that the trial's TOPLINE PRESS RELEASE is already sitting
in the pre-cutoff marketing corpus. That is a different failure: right trial, but
the outcome leaked.

Canonical miss (CYTK / ACACIA-HCM): aficamten's non-obstructive-HCM pivotal
reported positive topline on 2026-05-05, four weeks before the 2026-06-01 cutoff.
The readout 8-K was pulled into the corpus. The binding check passed (right NCT,
right disease/phase/sponsor); its timing axis only compares registry
primary_completion_date (2026-06) to cutoff, so it could not see that a results PR
already existed. The honesty screen would then "predict" an outcome it can read.

What this does
--------------
Scans each already-fetched corpus exhibit for co-occurrence, in a short window, of
  (a) a CATALYST-TRIAL name token (the study acronym, taken from case.notes — the
      curated notes always lead with it: ACACIA-HCM, LUCIDITY, HARMONi-3, ...), and
  (b) a PAST-TENSE readout announcement tight to that name (announced/reported
      positive|negative results, met / did not meet the primary, ...).
Keying on the CATALYST trial acronym (not the drug) is what avoids false positives
from a multi-trial deck: a CYTK deck quotes SEQUOIA-HCM p<0.0001 all over, but
those are a DIFFERENT trial than the ACACIA-HCM catalyst, so they do not fire.

Output is a WARN/LEAK verdict with the offending exhibit + quote for human review,
NOT a silent mutation. assert_no_leak() raises so a live run aborts before extract
spends credits; the sealed backtest may deliberately keep leaked controls, so the
caller decides whether to honor it.

BLIND: reads only the on-disk corpus the case already produced; no network, no
_sealed_outcomes.json.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .catalyst_spec import CASES, CatalystCase, DATA_DIR

# TIER-A: PAST-TENSE result announcements. Deliberately excludes bare "topline" —
# forward guidance constantly says "expect to REPORT topline results in 2H26",
# which is NOT a leak. We only fire on language that asserts a result was obtained.
_READOUT_A = re.compile(
    r"\b(?:met\s+(?:its|the|both|all)?\s*(?:co-?)?primary"
    r"|(?:did\s+not|didn't|failed\s+to)\s+meet\s+(?:its|the)?\s*(?:co-?)?primary"
    r"|missed\s+the\s+primary"
    r"|achieved\s+(?:statistical\s+)?significance"
    # Canonical topline-PR verbs only. "showed/demonstrated statistically
    # significant" is deliberately excluded: it also describes a re-analysis of
    # EARLIER-phase data using the catalyst trial's endpoint model (AMLX showed
    # Phase 2b data "using the Phase 3 LUCIDITY primary endpoint model"), which is
    # not the Phase 3 reading out.
    r"|(?:reported|announced|delivered|posted)\s+(?:positive|negative|mixed|topline|statistically\s+significant)"
    r"|results?\s+met\b)\b",
    re.I)
# NOTE on what we deliberately do NOT use: bare p-values / "statistically
# significant" near the acronym. A topline PR quotes a program's EARLIER-phase data
# (avexitide Phase 2b) or a SIBLING trial (ONWARD psoriasis for a lupus catalyst;
# ARCHER-I for an ARCHER-II catalyst) right alongside the upcoming catalyst trial's
# NAME. Acronym-proximity then binds the historical p-value to the wrong (future)
# trial and fabricates a leak. Only a PAST-TENSE announcement verb sitting TIGHT to
# the catalyst acronym reliably says "this specific trial read out."

# Tokens that look acronym-ish in notes but are NOT trial names.
_NOTE_STOP = {
    "ph1", "ph2", "ph3", "ph1b", "ph2b", "phase", "high", "med", "low", "eoy",
    "nct", "ole", "pdufa", "bla", "nda", "snda", "maa", "fda", "ema", "chmp",
    "us", "eu", "uk", "fr", "ads", "note", "med-high", "q1", "q2", "q3", "q4",
}
# Tight window: the acronym must sit close to the announcement verb so it is the
# SUBJECT/OBJECT of the announcement ("announced positive ... from ACACIA-HCM"),
# not merely co-mentioned in the same paragraph as a different trial's result.
_WINDOW = 60


def _acronym_candidates(case: CatalystCase) -> list[str]:
    """Pull study-acronym tokens from the curated notes' leading clause."""
    lead = re.split(r"[;(]", case.notes or "", 1)[0]
    indic = (case.indication or "").lower()
    out: list[str] = []
    for tok in re.findall(r"[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)*", lead):
        low = tok.lower()
        n_upper = sum(c.isupper() for c in tok)
        looks_acronym = n_upper >= 2 or bool(re.search(r"[A-Za-z]-?\d", tok))
        if (len(tok) >= 4 and looks_acronym and low not in _NOTE_STOP
                and low not in indic):           # drop indication tokens (nHCM, etc.)
            out.append(tok)
    # De-dupe, preserve order.
    seen: set[str] = set()
    return [t for t in out if not (t.lower() in seen or seen.add(t.lower()))]


def _exhibit_date(text: str, fallback: str) -> str:
    m = re.search(r"^FILING_DATE:\s*(\d{4}-\d{2}-\d{2})", text, re.M)
    return m.group(1) if m else fallback


def _scan_exhibit(text: str, acronyms: list[str]) -> list[dict]:
    """Return hits where a catalyst acronym sits within _WINDOW chars of a readout
    marker. TIER-A OR TIER-B both count once bound to the acronym."""
    hits: list[dict] = []
    low = text.lower()
    for acr in acronyms:
        for am in re.finditer(re.escape(acr.lower()), low):
            s = max(0, am.start() - _WINDOW)
            e = min(len(text), am.end() + _WINDOW)
            span = text[s:e]
            mk = _READOUT_A.search(span)
            if mk:
                hits.append({
                    "acronym": acr, "marker": mk.group(0),
                    "quote": re.sub(r"\s+", " ", span).strip()[:200],
                })
                break  # one hit per acronym per exhibit is enough
    return hits


def check_leak(case: CatalystCase) -> dict:
    idx_path = DATA_DIR / case.case_id / "corpus" / "corpus_index.json"
    if not idx_path.exists():
        return {"case_id": case.case_id, "ticker": case.ticker,
                "status": "NO_CORPUS", "exhibits": []}
    idx = json.loads(idx_path.read_text())
    acronyms = _acronym_candidates(case)
    if not acronyms:
        return {"case_id": case.case_id, "ticker": case.ticker,
                "status": "NO_ACRONYM", "acronyms": [], "exhibits": []}

    flagged: list[dict] = []
    for ex in idx.get("exhibits", []):
        p = DATA_DIR / ex["path"]
        if not p.exists():
            continue
        text = p.read_text()
        hits = _scan_exhibit(text, acronyms)
        if hits:
            flagged.append({
                "filing_date": _exhibit_date(text, ex.get("filing_date", "")),
                "exhibit": ex.get("exhibit"), "url": ex.get("url"),
                "hits": hits,
            })
    flagged.sort(key=lambda f: f["filing_date"], reverse=True)
    status = "LEAK" if flagged else "CLEAR"
    return {"case_id": case.case_id, "ticker": case.ticker, "status": status,
            "acronyms": acronyms, "exhibits": flagged}


class LeakError(RuntimeError):
    """Raised by assert_no_leak when a catalyst readout leaked into the corpus."""


def assert_no_leak(case: CatalystCase) -> dict:
    """Pre-flight gate: raise before extract spends credits if the catalyst's
    topline appears to already sit in the pre-cutoff corpus."""
    r = check_leak(case)
    if r["status"] == "LEAK":
        ev = r["exhibits"][0]
        h = ev["hits"][0]
        raise LeakError(
            f"[{case.ticker}] catalyst readout LEAKED into corpus — "
            f"{ev['filing_date']} {ev['exhibit']}: '{h['acronym']}' near "
            f"'{h['marker']}'. Quote: {h['quote'][:160]}")
    return r


def _print_case(r: dict) -> None:
    icon = {"CLEAR": "ok  ", "LEAK": "LEAK", "NO_CORPUS": "----",
            "NO_ACRONYM": "??  "}.get(r["status"], "?   ")
    print(f"[{icon}] {r['ticker']:<6} {r['case_id']:<34} {r['status']} "
          f"(acronyms={r.get('acronyms')})", file=sys.stderr)
    for ev in r.get("exhibits", []):
        for h in ev["hits"]:
            print(f"         {ev['filing_date']} {ev['exhibit']} — "
                  f"'{h['acronym']}' ~ '{h['marker']}'\n"
                  f"            \"{h['quote'][:200]}\"", file=sys.stderr)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Deterministic corpus forward-leak check")
    ap.add_argument("case_ids", nargs="*", help="case ids (default: all sealed CASES)")
    ap.add_argument("--live", action="store_true", help="include the live cohort")
    args = ap.parse_args()

    cases = dict(CASES)
    if args.live:
        from .live_catalysts import LIVE_CASES
        cases.update(LIVE_CASES)
    ids = args.case_ids or list(cases)

    results = []
    for cid in ids:
        try:
            r = check_leak(cases[cid])
        except Exception as ex:
            r = {"case_id": cid, "ticker": cases[cid].ticker, "status": "ERROR",
                 "acronyms": [], "exhibits": [], "error": str(ex)}
        results.append(r)
        _print_case(r)

    from collections import Counter
    tally = Counter(r["status"] for r in results)
    print(f"\n==== LEAK AUDIT: {dict(tally)} over {len(results)} cases ====",
          file=sys.stderr)
    leaks = [r["ticker"] for r in results if r["status"] == "LEAK"]
    if leaks:
        print(f"LEAK (readout in corpus): {leaks}", file=sys.stderr)
