"""Going-concern language detector.

FIRES when the audit opinion or MD&A contains "substantial doubt" / "going
concern" language about the obligor's ability to continue operations.

Why predictive: Going-concern language is a binary, narrow, high-precision
signal. Even when not a formal qualified opinion (which would trigger
mandatory disclosure under PCAOB AS 2415), the presence of "substantial
doubt" language in management discussion indicates auditors / management
have explicit concerns. Lead time vs rating action: typically 3-12 months.

Data shape:
  {
    "audit_opinion_has_going_concern_language": true,
    "mda_has_going_concern_language": false,
    "going_concern_excerpt": "...",  # actual text
    "fiscal_year": "FY2024",
    "source_url": "..."
  }
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["all_muni"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "Going-concern language detector.",
}

import re

# Affirmative-finding patterns. These must AVOID the standard auditor
# responsibility boilerplate, which reads:
#   "evaluate WHETHER there are conditions ... that raise substantial doubt"
#   "considered in the aggregate, raise substantial doubt about [Entity]'s
#    ability to continue as a going concern"
# That boilerplate appears in every PCAOB-compliant audit opinion under AS 2415
# and must be excluded — it represents the auditor's risk assessment, not a finding.
#
# Affirmative-finding language reads more like:
#   "We have determined that substantial doubt exists..."
#   "Conditions exist that raise substantial doubt..."
#   "The auditor's report includes an explanatory paragraph"
#   "Going Concern" as a section header in MD&A
GOING_CONCERN_FINDING_PATTERNS = [
    r"\b(?:has|have)\s+(?:determined|concluded)\s+that\s+(?:substantial\s+doubt|there\s+is\s+substantial\s+doubt)",
    r"substantial\s+doubt\s+(?:exists|has\s+been\s+raised|currently\s+exists)",
    r"(?:auditor|auditors)['’]\s*report\s+includes\s+an\s+(?:explanatory|emphasis-of-matter)\s+paragraph",
    r"emphasis[-\s]of[-\s]matter\s+paragraph",
    r"\bunable\s+to\s+continue\s+as\s+a\s+going\s+concern",
    r"\bdoubt\s+about\s+the\s+(?:Company|System|Hospital|Entity|Foundation)['’]s\s+ability\s+to\s+(?:meet|fund|satisfy)",
    # Section header style — line starts with "Going Concern" and is short (header-like)
    r"^\s*going\s+concern\s*$",
]

# Negative patterns — if "substantial doubt" appears within ~50 chars of these,
# it's boilerplate, not a finding.
BOILERPLATE_CONTEXT = [
    r"\bwhether\b",       # "evaluate whether ... substantial doubt"
    r"\bevaluate\b",
    r"\bevaluating\b",
    r"\bassess\b",
    r"\bassessing\b",
    r"\bconsider(?:ed|ing)\s+in\s+the\s+aggregate",
]


def has_going_concern_language(text: str) -> tuple[bool, str | None]:
    """Returns (found, matched_excerpt) for affirmative going-concern findings.

    Excludes the standard PCAOB auditor-responsibility boilerplate.
    """
    if not text:
        return False, None
    text_lower = text.lower()
    for pat in GOING_CONCERN_FINDING_PATTERNS:
        for m in re.finditer(pat, text_lower, re.MULTILINE):
            # Check if this match is within boilerplate context (±100 chars)
            ctx_start = max(0, m.start() - 100)
            ctx_end = min(len(text_lower), m.end() + 100)
            context = text_lower[ctx_start:ctx_end]
            if any(re.search(bp, context) for bp in BOILERPLATE_CONTEXT):
                continue  # boilerplate; skip
            # Real finding — return excerpt
            start = max(0, m.start() - 80)
            end = min(len(text), m.end() + 80)
            excerpt = re.sub(r"\s+", " ", text[start:end]).strip()
            return True, excerpt
    return False, None


def evaluate(obligor_name: str, data: dict) -> dict:
    audit_text = data.get("audit_opinion_text") or ""
    mda_text = data.get("mda_text") or ""

    audit_flag, audit_excerpt = has_going_concern_language(audit_text)
    mda_flag, mda_excerpt = has_going_concern_language(mda_text)

    # Allow callers to pass pre-computed flags too
    explicit_audit = data.get("audit_opinion_has_going_concern_language")
    explicit_mda = data.get("mda_has_going_concern_language")
    if explicit_audit is not None:
        audit_flag = explicit_audit
    if explicit_mda is not None:
        mda_flag = explicit_mda

    if not audit_text and not mda_text and explicit_audit is None and explicit_mda is None:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if audit_flag:
        return {
            "fires": True,
            "reason": "GOING_CONCERN_IN_AUDIT_OPINION",
            "severity": "HIGH",
            "evidence": {"audit_excerpt": audit_excerpt or data.get("going_concern_excerpt")},
        }
    if mda_flag:
        return {
            "fires": True,
            "reason": "GOING_CONCERN_IN_MDA",
            "severity": "MEDIUM",
            "evidence": {"mda_excerpt": mda_excerpt or data.get("going_concern_excerpt")},
        }
    return {
        "fires": False,
        "reason": "NO_GOING_CONCERN_LANGUAGE",
        "evidence": {},
    }
