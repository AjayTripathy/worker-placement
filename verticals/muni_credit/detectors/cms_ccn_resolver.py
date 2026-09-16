"""Obligor -> CMS CCN resolver (the "go-fetch-and-resolve" half of the brain).

The dispatch-index coverage validator surfaces that the nh_* CMS detectors
APPLY_TO every snf/ccrc obligor but have no data fed in. This module closes that
gap WITHOUT fabrication: it resolves an obligor name to a row in the local CMS
Nursing Home Provider Info file (CCN-keyed) and emits the exact input dicts the
three nh_* detectors consume.

Resolution hazard
-----------------
Obligor records carry only a name (with location/legal hints in parentheses),
not an address or CCN. Naive substring matching produces cross-facility false
matches:
  * "Paradise Valley Estates" (Fairfield, NorCal CCRC) vs "Paradise Valley
    Health Care" (National City, San Diego) — same first two tokens, different
    facility.
  * Aldersly's 20-bed SNF is uncertified — the correct answer is NO MATCH, not
    the wrong CCN a 3rd-party aggregator once reported.

So the resolver is deliberately conservative. It scores token overlap against
both Provider Name and Legal Business Name, uses a CA-city gazetteer (built from
the CMS file itself) to penalize city conflicts, and only accepts a match that
clears an absolute score floor AND beats the runner-up by a margin. Anything
below that returns None with a reason — an honest UNVERIFIABLE, never a
fabricated star rating. CCNs already claimed by another obligor are excluded so
two obligors can never share a provider row.
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["hospital_obligor", "nursing_home_obligor", "ccrc_obligor"],
    "asset_classes": ["ca_hospital_muni", "healthcare_muni", "ca_chffa_hospital_conduit", "ca_nh_muni", "ca_ccrc_muni", "ccrc_muni"],
    "applies_universally": False,
    "kind": "helper",
    "summary": "Obligor -> CMS CCN resolver (the \"go-fetch-and-resolve\" half of the brain).",
}

import csv
import re
from functools import lru_cache
from pathlib import Path

_CSV = Path(__file__).resolve().parent.parent / "data" / "cms_nh" / "NH_ProviderInfo_May2026.csv"

# Generic words that carry no disambiguating signal for senior-living / SNF names.
_STOP = frozenset({
    "the", "of", "a", "an", "and", "for", "at", "in", "to",
    "inc", "llc", "lp", "corp", "corporation", "company", "co", "incorporated",
    "non", "profit", "nonprofit",
    "services", "service", "community", "communities", "retirement",
    "senior", "seniors", "home", "homes", "house", "housing", "nursing",
    "facility", "facilities", "care", "center", "centre", "health", "healthcare",
    "living", "association", "obligated", "group", "california", "ca",
    "convalescent", "rehabilitation", "rehab", "skilled", "snf", "ccrc",
    # generic age descriptors — rare enough to look distinctive but carry no
    # identity (e.g. 'California Home for the Aged' must not anchor on 'aged').
    "aged", "elderly",
})

_ACCEPT_FLOOR = 0.34   # minimum IDF-weighted score to accept a match
_MARGIN = 0.12         # best must beat runner-up by this much (no ambiguous ties)
_DISTINCT_DF = 8       # a token in <= this many CA providers is "distinctive"
_NAME_COMMON_DF = 15   # a city token seen in >= this many provider names is not a city hint


def _norm_tokens(s: str) -> set[str]:
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return {t for t in s.split() if t and t not in _STOP and not t.isdigit()}


def _parentheticals(name: str) -> list[str]:
    return re.findall(r"\(([^)]*)\)", name or "")


@lru_cache(maxsize=1)
def _ca_rows() -> tuple[dict, ...]:
    if not _CSV.exists():
        return tuple()
    with open(_CSV, encoding="latin-1") as f:
        return tuple(r for r in csv.DictReader(f) if r.get("State") == "CA")


@lru_cache(maxsize=1)
def _name_df() -> dict[str, int]:
    """Document frequency of each token across CA provider + legal-business names.
    A proper noun like 'aldersly' appears once; a generic like 'garden' appears
    in dozens. Drives both distinctiveness and city-hint filtering."""
    df: dict[str, int] = {}
    for r in _ca_rows():
        toks = _norm_tokens(r.get("Provider Name", "")) | _norm_tokens(r.get("Legal Business Name", ""))
        for t in toks:
            df[t] = df.get(t, 0) + 1
    return df


def _idf(token: str) -> float:
    import math
    n = max(1, len(_ca_rows()))
    return math.log((n + 1) / (_name_df().get(token, 0) + 1)) + 1.0


@lru_cache(maxsize=1)
def _city_gazetteer() -> frozenset[str]:
    """CA city tokens from the CMS file, EXCLUDING tokens that are also common
    facility-name words (e.g. 'garden', 'valley', 'village'). Without this filter
    a name like 'Aldersly Garden' would treat 'garden' as a Garden Grove city hint
    and false-match a facility in that city."""
    df = _name_df()
    out: set[str] = set()
    for r in _ca_rows():
        for tok in (r.get("City/Town") or "").lower().replace("/", " ").split():
            if len(tok) >= 4 and df.get(tok, 0) < _NAME_COMMON_DF:
                out.add(tok)
    return frozenset(out)


def _city_hints(name: str) -> set[str]:
    gaz = _city_gazetteer()
    hints: set[str] = set()
    # parenthetical locations + whole-name token scan against the gazetteer
    blob = name.lower().replace("/", " ")
    for tok in re.sub(r"[^a-z0-9\s]", " ", blob).split():
        if tok in gaz:
            hints.add(tok)
    return hints


def _int(v):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def _money(v):
    try:
        return float(str(v).replace("$", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def resolve(obligor_name: str, exclude_ccns: frozenset[str] = frozenset()) -> dict | None:
    """Resolve an obligor name to a CMS provider row.

    Returns the matched row dict augmented with _score / _method / _confidence,
    or None when no candidate clears the floor + margin gates (honest no-match).
    """
    rows = _ca_rows()
    if not rows:
        return None

    # Obligor token set: main name + all parenthetical alt-names contribute.
    a_tokens = _norm_tokens(obligor_name)
    for p in _parentheticals(obligor_name):
        a_tokens |= _norm_tokens(p)
    if not a_tokens:
        return None
    hints = _city_hints(obligor_name)

    df = _name_df()
    scored: list[tuple[float, dict]] = []
    for r in rows:
        ccn = r.get("CMS Certification Number (CCN)")
        if ccn in exclude_ccns:
            continue
        b_tokens = _norm_tokens(r.get("Provider Name", "")) | _norm_tokens(r.get("Legal Business Name", ""))
        if not b_tokens:
            continue
        inter = a_tokens & b_tokens
        if not inter:
            continue
        # Require at least one DISTINCTIVE shared token (a proper noun, not a
        # generic word like 'home'/'garden'/'valley'). This is what kills the
        # 'California Home for the Aged' / 'Garden Park' style false matches that
        # share only a common word.
        if not any(df.get(t, 0) <= _DISTINCT_DF for t in inter):
            continue
        # IDF-weighted Jaccard: distinctive shared tokens dominate the score.
        inter_w = sum(_idf(t) for t in inter)
        union_w = sum(_idf(t) for t in (a_tokens | b_tokens))
        score = inter_w / union_w if union_w else 0.0

        cand_city = (r.get("City/Town") or "").lower()
        cand_city_tokens = set(cand_city.replace("/", " ").split())
        if hints:
            if hints & cand_city_tokens:
                score += 0.25           # city corroborates -> boost
            else:
                score *= 0.30           # city conflict -> heavy penalty
        if (r.get("Continuing Care Retirement Community") or "").upper() == "Y":
            score += 0.05               # obligor universe is CCRC/senior-living
        scored.append((score, r))

    if not scored:
        return None
    scored.sort(key=lambda x: -x[0])
    best_score, best = scored[0]
    second = scored[1][0] if len(scored) > 1 else 0.0

    if best_score < _ACCEPT_FLOOR or (best_score - second) < _MARGIN:
        return None

    out = dict(best)
    out["_score"] = round(best_score, 3)
    out["_runner_up_score"] = round(second, 3)
    out["_method"] = "NAME_CITY_FUZZY"
    out["_confidence"] = "HIGH" if best_score >= 0.55 else "MEDIUM"
    return out


def to_detector_inputs(row: dict) -> dict:
    """Map a CMS provider row to the input dicts the three nh_* detectors read."""
    ccn = row.get("CMS Certification Number (CCN)")
    src = f"CMS NH Provider Info May 2026 (CCN {ccn})"

    sff_raw = (row.get("Special Focus Status") or "").strip().upper()
    sff_status = {"SFF": "SFF", "SFF CANDIDATE": "SFF_CANDIDATE"}.get(sff_raw, "NONE")

    fines_total = _money(row.get("Total Amount of Fines in Dollars"))
    n_fines = _int(row.get("Number of Fines"))

    return {
        "nh_cms_star_rating": {
            "overall_star_rating": _int(row.get("Overall Rating")),
            "health_inspection_rating": _int(row.get("Health Inspection Rating")),
            "staffing_rating": _int(row.get("Staffing Rating")),
            "qm_rating": _int(row.get("QM Rating")),
            "rating_date": "2026-05",
            "source": src,
            "_resolution": {
                "ccn": ccn,
                "matched_provider": row.get("Provider Name"),
                "matched_city": row.get("City/Town"),
                "score": row.get("_score"),
                "method": row.get("_method"),
                "confidence": row.get("_confidence"),
            },
        },
        "nh_special_focus_facility": {
            "sff_status": sff_status,
            "list_date": "2026-05" if sff_status != "NONE" else None,
            "source": src,
        },
        "nh_civil_monetary_penalty": {
            # CMS publishes cumulative fines over the ~3yr survey window, not a
            # rolling 24mo CMP. Mapped here but window-labeled so the detector's
            # $500K threshold reads it without overstating recency.
            "cumulative_cmp_24mo_usd": fines_total,
            "n_cmps_24mo": n_fines,
            "active_dpna": None,  # denial-of-payment not in this CMS export
            "as_of_date": "2026-05",
            "_window_note": "CMS Total Amount of Fines = cumulative over ~3yr survey window, not strict 24mo",
            "source": src,
        },
    }


_NH_KEYS = ("nh_cms_star_rating", "nh_special_focus_facility", "nh_civil_monetary_penalty")


def fill_cms_gaps(detector_data: dict, seed_ccns: frozenset[str] = frozenset()) -> list[dict]:
    """Fill the nh_* CMS detector inputs for any obligor missing them.

    This is the wiring that turns the coverage validator's gap list into an
    actual fetch: for each obligor with no nh_* data, resolve its name to a CMS
    provider row and inject the three detector input dicts. Existing (curated)
    nh_* data is left untouched. CCNs are never double-assigned across obligors.

    Mutates detector_data in place; returns a per-obligor resolution report.
    """
    used = set(seed_ccns)
    report: list[dict] = []
    for obligor in sorted(detector_data):
        data = detector_data[obligor]
        if any(isinstance(data.get(k), dict) and data.get(k) for k in _NH_KEYS):
            continue  # already has CMS data (curated or previously filled)
        inputs, meta = resolve_to_detector_inputs(obligor, frozenset(used))
        if meta["resolved"]:
            used.add(meta["ccn"])
            for k, v in inputs.items():
                data[k] = v
        report.append(meta)
    return report


def print_resolution_report(report: list[dict], title: str = "CMS CCN RESOLUTION") -> None:
    resolved = [m for m in report if m.get("resolved")]
    print(f"\n=== {title} (gap -> fetch) ===")
    print(f"  Resolved {len(resolved)}/{len(report)} previously-unfed obligors to a CMS CCN:")
    for m in resolved:
        print(f"    {m['obligor'][:44]:44} -> CCN {m['ccn']} {(m['matched_provider'] or '')[:30]:30} "
              f"{(m['matched_city'] or '')[:14]:14} score={m['score']} ({m['confidence']})")
    unresolved = [m for m in report if not m.get("resolved")]
    if unresolved:
        print(f"  Still UNVERIFIABLE (no confident CMS match — honest no-fetch, not clean):")
        for m in unresolved:
            print(f"    {m['obligor'][:44]:44} -> {m['reason']}")


def resolve_to_detector_inputs(
    obligor_name: str, exclude_ccns: frozenset[str] = frozenset()
) -> tuple[dict, dict]:
    """Convenience: resolve + map. Returns (detector_inputs, meta).

    detector_inputs is {} when unresolved; meta always reports the outcome so a
    caller (and the coverage validator) can log resolved vs UNVERIFIABLE.
    """
    row = resolve(obligor_name, exclude_ccns)
    if row is None:
        return {}, {"obligor": obligor_name, "resolved": False, "reason": "NO_CONFIDENT_CMS_MATCH"}
    inputs = to_detector_inputs(row)
    meta = {
        "obligor": obligor_name,
        "resolved": True,
        "ccn": row.get("CMS Certification Number (CCN)"),
        "matched_provider": row.get("Provider Name"),
        "matched_city": row.get("City/Town"),
        "score": row.get("_score"),
        "runner_up_score": row.get("_runner_up_score"),
        "confidence": row.get("_confidence"),
    }
    return inputs, meta
