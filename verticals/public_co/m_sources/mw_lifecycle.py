"""Material-weakness lifecycle tracker.

Parses Item 9A (Controls and Procedures) across multiple 10-Ks to classify
the issuer's material-weakness state:

  NO_MW: never disclosed an MW in lookback window
  MW_PRESENT_CURRENT: latest 10-K asserts MW exists; ICFR "not effective"
  MW_REMEDIATED_MGMT_ASSERTION: previously disclosed MW, latest 10-K asserts
    "remediated" / "no longer exists" but auditor opinion change not
    verifiable from text parse alone
  MW_REMEDIATED_AUDITOR_VALIDATED: previously disclosed MW, latest 10-K's
    auditor attestation is now UNQUALIFIED (clean ICFR opinion) — highest-
    quality cure signal
  MW_REMEDIATED_THEN_REEMERGED: had MW, asserted remediated, then re-
    disclosed MW in subsequent 10-K — operational chaos signal

OUTPUT FIELDS
  mw_history: per-year {fiscal_year, has_mw, icfr_opinion, remediation_text}
  current_state: classification above
  cure_quality: HIGH | MEDIUM | LOW | N/A
  signal: NO_MW | MW_CURRENT | MW_HIGH_QUALITY_CURE | MW_LOW_QUALITY_CURE |
          MW_OPERATIONAL_CHAOS

LIMITATIONS
- Text parsing of Item 9A is heuristic; companies sometimes describe
  cured MWs that recur with new descriptions.
- ICFR audit opinion type (unqualified/adverse/disclaimer) is inferred
  from auditor-report excerpt language ("expressed an unqualified opinion"
  vs "expressed an adverse opinion"); some 10-Ks bury this in PCAOB-style
  language requiring auditor name to parse.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "Material-weakness lifecycle tracking across 10-Ks (present / remediated-asserted / verified).",
}

import re
from typing import Any, Optional

from .. import edgar


# Phrases that indicate MW PRESENT (current period)
_MW_PRESENT_RE = re.compile(
    r"(material\s+weakness(?:es)?\s+(?:identified|exists?|disclosed)|"
    r"(?:management|we|the\s+company)\s+(?:concluded|determined|identified|disclosed)\s+(?:that\s+)?(?:our|the)\s+(?:internal\s+control[^.]{0,80}(?:was|were|is|are)\s+)?not\s+effective|"
    r"(?:internal\s+control\s+over\s+financial\s+reporting|ICFR)\s+(?:was|were|is|are)\s+not\s+effective|"
    r"material\s+weakness(?:es)?\s+in\s+(?:our|the\s+company'?s?|the)\s+internal\s+controls)",
    re.IGNORECASE
)

# Phrases that indicate REMEDIATION
_REMEDIATION_RE = re.compile(
    r"(remediat(?:ed|ion\s+(?:plan|effort|complete))|"
    r"no\s+longer\s+(?:exists?|present)|"
    r"material\s+weakness(?:es)?\s+(?:has|have)\s+been\s+(?:cured|remediated|resolved)|"
    r"the\s+previously[\s-]reported\s+material\s+weakness|"
    r"successfully\s+remediated|"
    r"completed\s+(?:our\s+)?remediation)",
    re.IGNORECASE
)

# ICFR audit opinion type
_AUDIT_UNQUALIFIED_RE = re.compile(
    r"(unqualified\s+(?:audit\s+)?opinion|"
    r"effective\s+internal\s+control\s+over\s+financial\s+reporting|"
    r"in\s+all\s+material\s+respects)",
    re.IGNORECASE
)
_AUDIT_ADVERSE_RE = re.compile(
    r"(adverse\s+(?:audit\s+)?opinion|"
    r"adverse\s+opinion\s+on\s+(?:the\s+effectiveness\s+of\s+)?(?:internal\s+control|ICFR)|"
    r"did\s+not\s+maintain\s+effective\s+internal\s+control|"
    r"internal\s+control[^.]{0,40}was\s+not\s+effective)",
    re.IGNORECASE
)


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&#160;", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def _extract_item_9a(text: str, max_chars: int = 200_000) -> str:
    """Best-effort extract of Item 9A controls section. The 10-K's Item 9A
    can be deep in a HTML-laden filing; we strip HTML first and search the
    clean text, then return a generous window.

    Falls back to scanning the whole document for our MW regexes when
    section anchors fail (the regexes themselves are specific enough that
    this isn't catastrophically lossy)."""
    # Try several anchor patterns. Find the LAST occurrence (the body, not
    # the table-of-contents reference at the top).
    patterns = [
        r"Item\s+9A[.]?\s+Controls\s+and\s+Procedures",
        r"Item\s+9A\(?T\)?\s+",
        r"ITEM\s+9A[.]?\s+CONTROLS\s+AND\s+PROCEDURES",
    ]
    end_patterns = [
        r"Item\s+9B",
        r"ITEM\s+9B",
        r"Item\s+10[.]?\s+Directors",
        r"PART\s+III",
    ]
    best_start = -1
    for sp in patterns:
        matches = list(re.finditer(sp, text, re.IGNORECASE))
        if matches:
            # use the LAST occurrence (skip TOC reference at top)
            last = matches[-1]
            if last.start() > best_start:
                best_start = last.start()
    if best_start >= 0:
        end = len(text)
        for ep in end_patterns:
            em = re.search(ep, text[best_start + 50:], re.IGNORECASE)
            if em:
                end = best_start + 50 + em.start()
                break
        return text[best_start:min(end, best_start + max_chars)]
    # Fallback: scan a generous prefix of the cleaned text. MW phrases are
    # specific enough to detect even outside a clean section anchor.
    return text[:max_chars]


def _classify_one_10k(text: str) -> dict:
    """Return {has_mw, icfr_opinion, mentions_remediation, raw_phrases}.

    Strip HTML first (the section anchors and our MW regexes work on plain
    text; raw HTML inflates positions and bloats the doc with style noise)."""
    clean = _strip_html(text)
    section = _extract_item_9a(clean)

    mw_matches = _MW_PRESENT_RE.findall(section)
    rem_matches = _REMEDIATION_RE.findall(section)
    adv_matches = _AUDIT_ADVERSE_RE.findall(section)
    unq_matches = _AUDIT_UNQUALIFIED_RE.findall(section)

    has_mw = bool(mw_matches) or bool(adv_matches)
    mentions_remediation = bool(rem_matches)

    # ICFR opinion classification (heuristic):
    # adverse > 0 → ADVERSE
    # unqualified > 0 and adverse == 0 → UNQUALIFIED
    # else → UNKNOWN
    if adv_matches:
        icfr_opinion = "ADVERSE"
    elif unq_matches and not has_mw:
        icfr_opinion = "UNQUALIFIED"
    elif unq_matches and mentions_remediation and not adv_matches:
        # remediated and clean opinion → unqualified post-cure
        icfr_opinion = "UNQUALIFIED"
    else:
        icfr_opinion = "UNKNOWN"

    return {
        "has_mw": has_mw,
        "icfr_opinion": icfr_opinion,
        "mentions_remediation": mentions_remediation,
        "n_mw_matches": len(mw_matches),
        "n_remediation_matches": len(rem_matches),
        "n_adverse_matches": len(adv_matches),
        "section_len": len(section),
    }


def query_mw_lifecycle(
    cik: str,
    cutoff_date: str,
    lookback_years: int = 4,
) -> dict[str, Any]:
    """Pull recent 10-Ks pre-cutoff, parse Item 9A in each, classify the
    issuer's material-weakness lifecycle."""
    try:
        _, filings = edgar.list_filings(cik)
    except Exception as e:
        return {"signal": "ERROR", "_note": f"list_filings failed: {e}"}

    cands = [
        f for f in filings
        if f.get("form") in ("10-K", "10-K/A")
        and (f.get("filing_date") or "") <= cutoff_date
    ]
    cands.sort(key=lambda f: f.get("filing_date", ""), reverse=True)
    cands = cands[:lookback_years]

    history = []
    for f in cands:
        try:
            text = edgar.fetch_filing_clean(cik, f["accession"], f["primary_document"])
            if not text:
                continue
            cls = _classify_one_10k(text)
            history.append({
                "filing_date": f["filing_date"],
                "accession": f["accession"],
                "form": f["form"],
                **cls,
            })
        except Exception as e:
            history.append({
                "filing_date": f["filing_date"],
                "accession": f["accession"],
                "form": f["form"],
                "_note": f"fetch/parse failed: {e}",
                "has_mw": None,
            })

    # Order earliest → latest for lifecycle inference
    history_chrono = sorted(history, key=lambda h: h["filing_date"])
    mw_states = [h.get("has_mw") for h in history_chrono if h.get("has_mw") is not None]
    latest = history_chrono[-1] if history_chrono else None

    # Lifecycle classification
    if not history_chrono:
        current_state = "UNKNOWN"
        cure_quality = "N/A"
    elif latest and latest["has_mw"]:
        # Current period has MW
        current_state = "MW_PRESENT_CURRENT"
        cure_quality = "N/A"
    elif any(mw_states[:-1]) and latest and not latest["has_mw"]:
        # Earlier MW but latest is clean
        if latest["icfr_opinion"] == "UNQUALIFIED":
            current_state = "MW_REMEDIATED_AUDITOR_VALIDATED"
            cure_quality = "HIGH"
        elif latest["mentions_remediation"]:
            current_state = "MW_REMEDIATED_MGMT_ASSERTION"
            cure_quality = "MEDIUM"
        else:
            current_state = "MW_REMEDIATED_MGMT_ASSERTION"
            cure_quality = "MEDIUM"
        # Reemergence check: pattern MW → clean → MW would be in mw_states
        # transitions; we check if there's any "True → False → True" subseq
        for i in range(len(mw_states) - 2):
            if mw_states[i] and not mw_states[i + 1] and mw_states[i + 2]:
                current_state = "MW_REMEDIATED_THEN_REEMERGED"
                cure_quality = "LOW"
                break
    else:
        current_state = "NO_MW"
        cure_quality = "N/A"

    # Signal mapping
    if current_state == "NO_MW":
        signal = "NO_MW"
    elif current_state == "MW_PRESENT_CURRENT":
        signal = "MW_CURRENT"
    elif current_state == "MW_REMEDIATED_AUDITOR_VALIDATED":
        signal = "MW_HIGH_QUALITY_CURE"
    elif current_state == "MW_REMEDIATED_MGMT_ASSERTION":
        signal = "MW_LOW_QUALITY_CURE"
    elif current_state == "MW_REMEDIATED_THEN_REEMERGED":
        signal = "MW_OPERATIONAL_CHAOS"
    else:
        signal = "UNKNOWN"

    return {
        "cik": cik,
        "cutoff_date": cutoff_date,
        "n_10ks_analyzed": len(history_chrono),
        "mw_history": history_chrono,
        "current_state": current_state,
        "cure_quality": cure_quality,
        "signal": signal,
    }


if __name__ == "__main__":
    import json
    # IPAR — known to have MW in FY2024
    print("IPAR (Interparfums — known MW FY2024):")
    r = query_mw_lifecycle("0000822663", "2025-05-15", lookback_years=4)
    print(json.dumps({k: v for k, v in r.items() if k != "mw_history"}, indent=2))
    print("\nmw_history:")
    for h in r.get("mw_history", []):
        print(f"  {h.get('filing_date')} {h.get('form'):6}  has_mw={h.get('has_mw')}  icfr={h.get('icfr_opinion')}  rem={h.get('mentions_remediation')}")
