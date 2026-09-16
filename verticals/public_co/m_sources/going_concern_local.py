"""Local-file going-concern + auditor-change check for backtests.

The production `going_concern_detector.query_going_concern()` has a
cutoff bug: it always fetches the LATEST 10-K/10-Q from EDGAR, then
returns NOT_FOUND_FILING if that filing is post-cutoff. For backtest
work where we've already fetched the latest-pre-cutoff 10-K to a local
path (e.g. via `backtest_fetch_filings.py`), this helper applies the
same pattern matching directly to the local file — bypassing the
EDGAR fetch and the cutoff bug entirely.

Use this for survivorship-bias backtests where the local 10-K is the
authoritative point-in-time filing.

Usage:
    from verticals.public_co.m_sources.going_concern_local import (
        going_concern_from_text, auditor_change_from_text
    )
    txt = open(filing_path).read()
    gc = going_concern_from_text(txt)
    ac = auditor_change_from_text(txt)
"""


from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "helper",
    "summary": "Local-file going-concern variant for backtests (cutoff-safe); infra, never dispatched.",
}

import re
from typing import Any

# Patterns copied from going_concern_detector.py
_GOING_CONCERN_RE = re.compile(
    r"(substantial\s+doubt|going\s+concern|ability\s+to\s+continue\s+as\s+a\s+going\s+concern)",
    re.IGNORECASE,
)
_CURE_RE = re.compile(
    r"(no\s+longer\s+exists|previously\s+identified|substantial\s+doubt\s+has\s+been\s+alleviated|"
    r"management\s+plans?\s+to\s+(?:raise|refinance|restructure)|"
    r"successfully\s+completed|"
    r"completed\s+a\s+capital\s+raise|"
    r"the\s+substantial\s+doubt\s+about\s+our\s+ability\s+to\s+continue.{0,100}has\s+been)",
    re.IGNORECASE,
)
_HISTORICAL_RE = re.compile(
    r"(formerly\s+had|previously\s+had|prior\s+to\s+\d{4}|in\s+\d{4}\s+we\s+had|"
    r"acquired\s+entity|legacy\s+entity)",
    re.IGNORECASE,
)


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&nbsp;", " ").replace("&#160;", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def going_concern_from_text(text: str, max_chars: int = 1_500_000) -> dict[str, Any]:
    """Apply the same pattern logic as query_going_concern, but on raw filing text."""
    clean = _strip_html(text[:max_chars])
    matches = list(_GOING_CONCERN_RE.finditer(clean))

    if not matches:
        return {"signal": "NO_GOING_CONCERN", "n_matches": 0,
                "n_current_period": 0, "n_cure": 0, "n_historical": 0,
                "sample_contexts": []}

    n_cure = n_historical = n_current_period = 0
    sample_contexts: list[str] = []
    for m in matches[:20]:
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

    if n_current_period >= 1:
        signal = "EXPLICIT_GOING_CONCERN"
    elif n_cure > 0 and n_current_period == 0:
        signal = "MITIGATED_GOING_CONCERN"
    elif n_historical > 0:
        signal = "NO_GOING_CONCERN"
    else:
        signal = "CURE_LANGUAGE"

    return {
        "signal": signal,
        "n_matches": len(matches),
        "n_current_period": n_current_period,
        "n_cure": n_cure,
        "n_historical": n_historical,
        "sample_contexts": sample_contexts,
    }


# ---------------- Auditor change ----------------

# Item 4.01 = changes in registrant's certifying accountant
# 8-K filings disclose these; in a 10-K, look for auditor name and tenure
_BIG4 = ("Ernst & Young", "EY", "Deloitte", "PricewaterhouseCoopers",
         "PwC", "KPMG")
_TIER_BIG6 = _BIG4 + ("BDO", "Grant Thornton", "RSM", "Crowe")


def _detect_auditor_name(text: str) -> list[str]:
    """Find auditor mentions in a 10-K. Multiple hits = multiple firms in
    history (frequent turnover) or firm change."""
    hits = []
    for firm in _BIG4 + ("BDO USA", "BDO", "Grant Thornton", "RSM US",
                         "Marcum", "Withum", "Crowe"):
        if re.search(rf"\b{re.escape(firm)}\b", text):
            hits.append(firm)
    # Dedupe order-preserving
    seen = set(); deduped = []
    for h in hits:
        if h not in seen:
            seen.add(h); deduped.append(h)
    return deduped


_RESIGNATION_RE = re.compile(
    r"(auditor\s+(?:resigned|declined\s+to\s+stand|was\s+dismissed)|"
    r"(?:has\s+)?dismissed\s+our\s+(?:independent\s+registered\s+public\s+accounting\s+firm|auditor)|"
    r"appointed.{0,80}as\s+our\s+(?:new\s+)?(?:independent\s+)?(?:registered\s+public\s+accounting\s+firm|auditor))",
    re.IGNORECASE,
)
_DISAGREEMENT_RE = re.compile(
    r"(disagreement\s+with\s+(?:the\s+)?(?:former\s+)?auditor|"
    r"reportable\s+event|material\s+weakness.{0,80}identified\s+by\s+(?:our\s+)?auditor)",
    re.IGNORECASE,
)


def auditor_change_from_text(text: str, max_chars: int = 1_500_000) -> dict[str, Any]:
    clean = _strip_html(text[:max_chars])
    firms = _detect_auditor_name(clean)
    n_resignation_lang = len(list(_RESIGNATION_RE.finditer(clean)))
    n_disagreement_lang = len(list(_DISAGREEMENT_RE.finditer(clean)))

    is_big4 = any(f in _BIG4 or f == "PwC" or f == "EY" for f in firms)
    n_firms = len(firms)

    if n_disagreement_lang > 0:
        signal = "DISAGREEMENT_DISCLOSED"
    elif n_resignation_lang > 0:
        signal = "RESIGNATION_OR_DECLINE"
    elif n_firms >= 3:
        signal = "FREQUENT_TURNOVER"
    elif n_firms == 2:
        signal = "UPGRADE_OR_LATERAL"  # could be either way
    elif n_firms == 1 and is_big4:
        signal = "CLEAN_BIG4_TENURE"
    elif n_firms == 1:
        signal = "CLEAN_TIER_2_TENURE"
    else:
        signal = "AUDITOR_UNCLEAR"

    return {
        "signal": signal,
        "firms_mentioned": firms,
        "n_firms": n_firms,
        "n_resignation_lang": n_resignation_lang,
        "n_disagreement_lang": n_disagreement_lang,
        "is_big4": is_big4,
    }
