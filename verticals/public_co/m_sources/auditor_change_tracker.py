"""
Auditor change detector via SEC 8-K Item 4.01 parsing.

WHY THIS EXISTS
SEC Form 8-K Item 4.01 ("Changes in Registrant's Certifying
Accountant") is REQUIRED disclosure when a public company changes its
auditor. Item 4.01 has two sub-items:
  4.01(a) Previous Independent Accountant — disclosed when prior
          auditor resigned, was dismissed, or declined to stand for
          re-appointment
  4.01(b) New Independent Accountant — disclosed when a new auditor
          is engaged

Auditor changes are a high-signal small-cap quality flag because:
  1. A "Big 4" auditor (Deloitte, PwC, EY, KPMG) resigning is
     RARE and concerning — Big 4 firms walk away from clients only
     when something is materially wrong
  2. Downgrading from a Big 4 to a smaller firm typically signals
     fee pressure OR audit-relationship breakdown
  3. The 8-K's "reason for change" disclosure is informative — when
     the issuer states only "to reduce costs" without naming a
     specific issue, it's often masking a real concern
  4. Frequent auditor turnover (>1 change per 5 years) is a pattern
     correlated with restatement risk and management opacity

SIGNAL ENUM
  CLEAN_AUDITOR_TENURE        — no auditor change in lookback period
  DOWNGRADE_TO_SMALLER_FIRM   — change from Big 4 to non-Big 4
  UPGRADE_OR_LATERAL          — Big 4 to Big 4 or smaller to Big 4
  RESIGNATION_OR_DECLINE      — auditor resigned or declined re-appointment
  DISAGREEMENT_DISCLOSED      — 8-K discloses material disagreement
                                between issuer and former auditor (rare
                                and severe)
  FREQUENT_TURNOVER           — multiple auditor changes in lookback
  NOT_FOUND                   — no 8-K Item 4.01 found in lookback

CAVEATS
- 8-K Item 4.01 parsing is text-heavy; classification of "reason"
  uses pattern matching on canonical phrases
- Some changes are benign (M&A integration, audit firm reorganization)
- Detector errs toward flagging — analyst should review the 8-K text
  for context before acting on a signal
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "Parses 8-K Item 4.01 auditor changes; resignations/dismissals are a high-signal small-cap quality flag.",
}

import re
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional

from .. import edgar


BIG_4 = (
    "Deloitte", "PricewaterhouseCoopers", "PwC", "Ernst & Young", "EY",
    "KPMG", "Deloitte & Touche", "Deloitte LLP", "PricewaterhouseCoopers LLP",
    "Ernst & Young LLP", "KPMG LLP",
)

# Phrases used in 8-K Item 4.01 disclosure
_RESIGN_RE = re.compile(
    r"(resigned|declined\s+to\s+stand|declined\s+re-?appointment|"
    r"declined\s+to\s+be\s+re-?appointed|was\s+dismissed)",
    re.IGNORECASE
)
# Real disagreement requires AFFIRMATIVE language. The Item 4.01 template
# routinely contains negated forms ("no reportable events", "no disagreements")
# — those must NOT trigger the flag.
_DISAGREEMENT_AFFIRMATIVE_RE = re.compile(
    r"(there\s+(?:were|was|have\s+been|has\s+been)\s+"
    r"(?:the\s+following\s+)?"
    r"(?!no\s)(reportable\s+events?|material\s+weaknesses?|"
    r"disagreements?|adverse\s+opinions?|qualified\s+opinions?|"
    r"disclaimed\s+opinions?|significant\s+deficienc(?:y|ies)))",
    re.IGNORECASE
)
# Negated form sanity-check: count negated phrases for transparency
_DISAGREEMENT_NEGATED_RE = re.compile(
    r"(no\s+(?:reportable\s+events?|material\s+weaknesses?|"
    r"disagreements?|adverse\s+opinions?|qualified\s+opinions?))",
    re.IGNORECASE
)
_FORMER_AUDITOR_RE = re.compile(
    r"(former|previous)\s+(independent\s+registered\s+public\s+accounting\s+firm|"
    r"independent\s+registered\s+public\s+accountant|auditor|"
    r"registered\s+public\s+accounting\s+firm)\s+(?:was|is|has\s+been|of\s+the\s+Company\s+was)?\s*(.{5,80})",
    re.IGNORECASE
)
_NEW_AUDITOR_RE = re.compile(
    r"(new|engaged|appointed|approved)\s+(?:as\s+)?(?:the\s+)?(?:Company'?s\s+)?"
    r"(?:independent\s+)?(?:registered\s+)?(?:public\s+)?(?:accounting\s+firm|"
    r"accountant|auditor)\s*[,:]?\s*(.{5,80})",
    re.IGNORECASE
)


def _is_big4(name: str) -> bool:
    if not name:
        return False
    nl = name.lower()
    return any(b.lower() in nl for b in BIG_4)


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&#160;", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def query_auditor_changes(
    cik: str,
    lookback_days: int = 1825,  # 5 years
    cutoff_date: Optional[str] = None,
) -> dict[str, Any]:
    """Detect auditor changes via SEC 8-K Item 4.01 in lookback window.

    Args:
      cik: 10-digit padded CIK
      lookback_days: how far back to scan for Item 4.01 8-Ks (default 5 years)
      cutoff_date: ISO YYYY-MM-DD upper bound

    Returns:
      {
        "n_8k_item_401":          int (count of Item 4.01 disclosures),
        "changes":                list of detected changes (date, former, new, big4_flags),
        "n_big4_resignations":    int,
        "n_disagreements":        int,
        "signal":                 see enum above,
        "lookback_start":         ISO date,
        "cutoff_date":            ISO date,
      }
    """
    cutoff = date.fromisoformat(str(cutoff_date)[:10]) if cutoff_date else date.today()
    lookback_start = cutoff - timedelta(days=lookback_days)

    try:
        _, all_filings = edgar.list_filings(cik)
    except Exception:
        return {"signal": "NOT_FOUND", "_note": f"Could not list filings for CIK {cik}",
                "n_8k_item_401": 0, "changes": []}

    # Filter to 8-K filings in lookback window
    eight_ks = []
    for f in all_filings:
        if f.get("form") not in ("8-K", "8-K/A"):
            continue
        try:
            d = date.fromisoformat(f.get("filing_date", "")[:10])
            if lookback_start <= d <= cutoff:
                eight_ks.append((d, f))
        except (ValueError, TypeError):
            continue

    changes: list[dict] = []
    n_big4_resign = 0
    n_disagreements = 0

    # Cap scan to avoid hammering EDGAR — typical company has <30 8-Ks in 5yr
    for d, f in eight_ks[:80]:
        try:
            text = edgar.fetch_filing_clean(cik, f["accession"], f["primary_document"])
        except Exception:
            continue
        if not text:
            continue
        clean = _strip_html(text[:200_000])
        if "Item 4.01" not in clean:
            continue
        # Extract details
        former = None
        new = None
        m_former = _FORMER_AUDITOR_RE.search(clean)
        if m_former:
            former = re.sub(r"\s+", " ", m_former.group(3))[:80].strip(".,;: ")
        m_new = _NEW_AUDITOR_RE.search(clean)
        if m_new:
            new = re.sub(r"\s+", " ", m_new.group(2))[:80].strip(".,;: ")
        # Resignation language?
        resigned = bool(_RESIGN_RE.search(clean))
        # Disagreement language? Affirmative only (not "no disagreement").
        disagreement = bool(_DISAGREEMENT_AFFIRMATIVE_RE.search(clean))
        n_negated = len(_DISAGREEMENT_NEGATED_RE.findall(clean))
        former_b4 = _is_big4(former or "")
        new_b4 = _is_big4(new or "")
        change = {
            "date": d.isoformat(),
            "accession": f["accession"],
            "form": f.get("form"),
            "former_auditor": former,
            "new_auditor": new,
            "former_is_big4": former_b4,
            "new_is_big4": new_b4,
            "resigned": resigned,
            "disagreement": disagreement,
            "n_negated_template_phrases": n_negated,
        }
        if former_b4 and resigned:
            n_big4_resign += 1
        if disagreement:
            n_disagreements += 1
        changes.append(change)

    # Signal logic
    n = len(changes)
    if n == 0:
        signal = "CLEAN_AUDITOR_TENURE"
    elif n_disagreements > 0:
        signal = "DISAGREEMENT_DISCLOSED"
    elif n_big4_resign > 0:
        signal = "RESIGNATION_OR_DECLINE"
    elif n >= 2:
        signal = "FREQUENT_TURNOVER"
    elif n == 1:
        c = changes[0]
        if c["former_is_big4"] and not c["new_is_big4"]:
            signal = "DOWNGRADE_TO_SMALLER_FIRM"
        elif c["resigned"]:
            signal = "RESIGNATION_OR_DECLINE"
        else:
            signal = "UPGRADE_OR_LATERAL"
    else:
        signal = "CLEAN_AUDITOR_TENURE"

    return {
        "n_8k_item_401":      n,
        "changes":            changes,
        "n_big4_resignations": n_big4_resign,
        "n_disagreements":    n_disagreements,
        "signal":             signal,
        "lookback_start":     lookback_start.isoformat(),
        "cutoff_date":        cutoff.isoformat(),
    }
