"""
Going-concern detector via SEC 10-K/10-Q parsing.

WHY THIS EXISTS
"Substantial doubt about the ability to continue as a going concern" is
the SEC's required disclosure language (ASC 205-40) when management OR
auditors identify conditions that raise substantial doubt about the
issuer's ability to continue operating for at least 12 months from the
filing date.

For small-cap claim verification, this is the highest-value universal
quality signal:
  - If the issuer has going-concern language → the rest of the
    framework's claim verification is moot. SHORT or AVOID.
  - If the issuer DOES NOT have going-concern language → continue with
    standard claim verification.

The detector parses the most recent 10-K/10-Q and applies pattern
matching on the canonical language. Three tiers of severity:

  EXPLICIT_GOING_CONCERN — auditor or management explicitly uses the
                            "substantial doubt" phrase
  MITIGATED_GOING_CONCERN — earlier filings had going concern but
                            management discloses cure plans (raised
                            capital, refinanced); current filing has
                            cleared the language
  CURE_LANGUAGE          — borderline: "have addressed" / "subject to"
                            cure conditions that may revive going concern
  NO_GOING_CONCERN       — clean
  NOT_FOUND_FILING       — no recent 10-K/10-Q available

PARSING APPROACH
SEC requires the phrase "substantial doubt" to appear when going-concern
applies. The connector greps for:
  - "substantial doubt"
  - "going concern"
  - "ability to continue as a going concern"

Then categorizes the language context (present-tense vs cured vs
historical reference).

LIMITATIONS
- Historical references to prior going-concern conditions can produce
  false positives; the connector filters to current-period language
- Some filings discuss going concern in footnotes about subsidiaries
  not the parent; this connector reports raw matches and lets the
  caller / scorer interpret
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "ASC 205-40 going-concern language detection in 10-K/10-Q for any issuer.",
}

import re
import json
from datetime import date
from pathlib import Path
from typing import Any, Optional

from .. import edgar


# Canonical going-concern phrases
_GOING_CONCERN_RE = re.compile(
    r"(substantial\s+doubt|going\s+concern|ability\s+to\s+continue\s+as\s+a\s+going\s+concern)",
    re.IGNORECASE
)

# Phrases that indicate a CURED / MITIGATED state (auditor previously
# raised going concern, management has since addressed)
_CURE_RE = re.compile(
    r"(no\s+longer\s+exists|previously\s+identified|substantial\s+doubt\s+has\s+been\s+alleviated|"
    r"management\s+plans?\s+to\s+(?:raise|refinance|restructure)|"
    r"successfully\s+completed|"
    r"completed\s+a\s+capital\s+raise|"
    r"the\s+substantial\s+doubt\s+about\s+our\s+ability\s+to\s+continue.{0,100}has\s+been)",
    re.IGNORECASE
)

# Historical / immaterial-reference filters (e.g., discussing a former subsidiary)
_HISTORICAL_RE = re.compile(
    r"(formerly\s+had|previously\s+had|prior\s+to\s+\d{4}|in\s+\d{4}\s+we\s+had|"
    r"acquired\s+entity|legacy\s+entity)",
    re.IGNORECASE
)


def _normalize_ws(text: str) -> str:
    """Whitespace normalization for already-cleaned filing text."""
    return re.sub(r"\s+", " ", text)


def query_going_concern(
    cik: str,
    cutoff_date: Optional[str] = None,
    max_text_scan_chars: int = 1_500_000,
) -> dict[str, Any]:
    """Detect going-concern language in the most recent 10-K/10-Q.

    Args:
      cik: 10-digit padded CIK
      cutoff_date: ISO YYYY-MM-DD; only consider filings up to this date
      max_text_scan_chars: cap raw text scan to keep runtime bounded

    Returns:
      {
        "filing": {accession, form, filed_at, primary_document},
        "n_matches": int (total going-concern phrase matches in filing),
        "n_cure_matches": int (matches with cure language nearby),
        "n_current_period_matches": int (matches that look current-period),
        "sample_contexts": list of up to 5 short context strings around matches,
        "signal": EXPLICIT_GOING_CONCERN | MITIGATED_GOING_CONCERN |
                   CURE_LANGUAGE | NO_GOING_CONCERN | NOT_FOUND_FILING,
        "cutoff_date": echo,
      }
    """
    cutoff_iso = str(cutoff_date)[:10] if cutoff_date else None

    # Most-recent-of-either-form as of cutoff (point-in-time). This replaces the
    # old "prefer 10-K, else 10-Q" loop, which could surface a stale filing, and
    # folds the cutoff into selection so a just-after-cutoff filing no longer
    # masks an earlier pre-cutoff one.
    filing = edgar.latest_filing(
        cik, cutoff_iso, forms=("10-K", "10-K/A", "10-Q", "10-Q/A")
    )
    if not filing:
        return {
            "filing": None,
            "n_matches": 0,
            "signal": "NOT_FOUND_FILING",
            "cutoff_date": cutoff_date,
            "_note": f"No 10-K/10-Q found for CIK {cik}"
                     + (f" as of cutoff ({cutoff_iso})." if cutoff_iso else "."),
        }

    text = edgar.fetch_filing_clean(cik, filing["accession"], filing["primary_document"])
    if not text:
        return {
            "filing": filing,
            "n_matches": 0,
            "signal": "NOT_FOUND_FILING",
            "cutoff_date": cutoff_date,
            "_note": "Filing text could not be fetched.",
        }

    clean = _normalize_ws(text[:max_text_scan_chars])
    matches = list(_GOING_CONCERN_RE.finditer(clean))

    if not matches:
        return {
            "filing": filing,
            "n_matches": 0,
            "signal": "NO_GOING_CONCERN",
            "cutoff_date": cutoff_date,
        }

    # Examine context around each match
    n_cure = 0
    n_historical = 0
    n_current_period = 0
    sample_contexts = []
    for m in matches[:20]:  # cap to first 20 matches
        s = max(0, m.start() - 250)
        e = min(len(clean), m.end() + 250)
        ctx = clean[s:e]
        if _CURE_RE.search(ctx):
            n_cure += 1
            continue
        if _HISTORICAL_RE.search(ctx):
            n_historical += 1
            continue
        n_current_period += 1
        if len(sample_contexts) < 5:
            sample_contexts.append(ctx[:400])

    # Signal logic
    n_total = len(matches)
    if n_current_period >= 1:
        signal = "EXPLICIT_GOING_CONCERN"
    elif n_cure > 0 and n_current_period == 0:
        signal = "MITIGATED_GOING_CONCERN"
    elif n_historical > 0 and n_current_period == 0 and n_cure == 0:
        # All historical references — treat as clean
        signal = "NO_GOING_CONCERN"
    else:
        # Going-concern phrase found but no clear classification
        signal = "CURE_LANGUAGE"

    return {
        "filing": {
            "accession":  filing.get("accession"),
            "form":       filing.get("form"),
            "filed_at":   filing.get("filed_at") or filing.get("filing_date"),
            "primary_document": filing.get("primary_document"),
        },
        "n_matches":                n_total,
        "n_cure_matches":           n_cure,
        "n_historical_matches":     n_historical,
        "n_current_period_matches": n_current_period,
        "sample_contexts":          sample_contexts,
        "signal":                   signal,
        "cutoff_date":              cutoff_date,
    }
