"""Bond covenant breach disclosure detector.

FIRES on disclosure language in audited financial statements / official
statements / EMMA continuing disclosure documents indicating that the
obligor has BREACHED a financial covenant in its bond indenture, master
trust indenture, loan agreement, or continuing disclosure agreement.

Why predictive: every muni bond indenture has financial covenants (DSCR,
days cash, liquidity tests, additional bonds test, rate covenant). Audited
financials include a compliance section. A breach is one of three things:

  (a) CURED — silently disclosed; auditor notes the metric fell below the
      covenant intra-year but was cured by FYE. Mild signal.
  (b) WAIVED — auditor explicitly states "non-compliance ... waiver
      obtained." Strong signal: lender / trustee was uncomfortable enough
      to require formal action; rating agencies typically begin review.
  (c) ACTIVE — auditor states obligor remains out of compliance; in
      severe cases the trustee may have accelerated maturity. Rare.
      RED-tier signal.

PROTOTYPE CATCH: Alliance College-Ready Public Schools FY25 audit
disclosed non-compliance with financial covenants, waiver obtained. The
covenant breach moved Alliance from the v1 BUY list (BBB anchor at 91
bps) to the v2 EXCLUDE list per CA_CHARTER_INVESTMENT_THESIS_V2.md. The
detector formalizes that catch into a re-runnable rule.

This detector is COMPLEMENTARY to `covenant_tripwire.py`:
  - covenant_tripwire computes headroom from CURRENT metrics vs
    KNOWN covenant minimums — fires at GREEN/YELLOW/ORANGE/RED/TRIPWIRED.
    Requires per-obligor covenant_terms.json + cafr_overrides.json.
  - covenant_breach reads DISCLOSURE LANGUAGE from audits/EMMA filings —
    fires only on explicit breach text. Higher precision; covers obligors
    where we don't have parameterized covenant terms.

Data shape:
  {
    "obligor_name": "Alliance College-Ready Public Schools",
    "audit_fy": "2024-2025",
    "audit_url": "https://...",
    "audit_page": 47,                            # optional, for citation
    "audit_text": "...long excerpt or full...",  # detector scans this
    "emma_continuing_disclosure_text": "...",    # optional alternate source
    "emma_url": "https://emma.msrb.org/...",     # optional
    "explicit_breach_status": "WAIVER_OBTAINED"  # optional manual override:
                                                 # one of WAIVER_OBTAINED,
                                                 # ACTIVE, ACCELERATION,
                                                 # CURED, NONE
    "as_of_date": "2026-05-28",
  }

Returns:
  {
    "fires": bool,
    "reason": str,        # e.g. "NON_COMPLIANCE_WAIVER_OBTAINED"
    "severity": str,      # RED / HIGH / MEDIUM / LOW
    "evidence": {
      "breach_disclosure_found": bool,
      "breach_language_excerpt": str,
      "breach_status": str,   # WAIVER_OBTAINED / ACTIVE / ACCELERATION / CURED
      "audit_url": str,
      "audit_page": int|None,
      "audit_fy": str,
      "confidence": str,    # HIGH / MEDIUM / LOW / UNVERIFIABLE
    }
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
    "summary": "Bond covenant breach disclosure detector.",
}

import re


# ---- pattern library ------------------------------------------------------

# Affirmative-finding patterns for explicit breach disclosure.
# Each tuple is (regex, status_label, severity).
# Severity ordering: ACCELERATION > ACTIVE > WAIVER_OBTAINED > CURED
BREACH_PATTERNS: list[tuple[str, str, str]] = [
    # ACCELERATION — bondholders/trustee accelerated maturity (RED)
    (r"(?:trustee|bondholders?)\s+(?:has\s+)?(?:accelerated|declared\s+all\s+(?:bonds?|amounts?)\s+(?:to\s+be\s+)?(?:due|immediately\s+due))",
     "ACCELERATION", "RED"),
    (r"event\s+of\s+default\s+(?:has\s+)?(?:occurred|been\s+declared)(?:[^.]{0,200}accelerat)",
     "ACCELERATION", "RED"),

    # ACTIVE non-compliance, no waiver mentioned (RED)
    (r"(?:remains?\s+|is\s+currently\s+|continues?\s+(?:to\s+be\s+)?in\s+)(?:non[-\s]?compliance|default)\s+(?:with|under)",
     "ACTIVE", "RED"),
    (r"(?:has\s+)?not\s+(?:cured|remedied)\s+(?:the|this|such)\s+(?:non[-\s]?compliance|default|violation|breach)",
     "ACTIVE", "RED"),

    # WAIVER OBTAINED — explicit waiver language (HIGH)
    (r"non[-\s]?compliance\s+with\s+(?:certain\s+|the\s+|its\s+)?(?:financial\s+)?(?:covenants?|debt\s+covenants?|loan\s+covenants?|bond\s+covenants?)[^.]{0,400}(?:waiver|forbearance)",
     "WAIVER_OBTAINED", "HIGH"),
    (r"(?:waiver|forbearance)[^.]{0,300}(?:non[-\s]?compliance|covenant\s+violation|covenant\s+breach|default)",
     "WAIVER_OBTAINED", "HIGH"),
    (r"(?:received|obtained|granted)\s+(?:a\s+)?(?:waiver|forbearance)[^.]{0,200}(?:covenant|indenture|loan\s+agreement)",
     "WAIVER_OBTAINED", "HIGH"),
    (r"covenant\s+(?:violation|breach)[^.]{0,200}(?:waiver|forbearance)",
     "WAIVER_OBTAINED", "HIGH"),

    # Rate covenant failure — utility / hospital specific (HIGH)
    (r"(?:did\s+not\s+meet|failed\s+to\s+(?:meet|satisfy|achieve))\s+(?:the\s+)?rate\s+covenant",
     "ACTIVE", "HIGH"),
    (r"rate\s+covenant\s+(?:was\s+not|has\s+not\s+been)\s+(?:met|satisfied|achieved)",
     "ACTIVE", "HIGH"),

    # Indenture / additional bonds test failure (HIGH)
    (r"violation\s+of\s+(?:the\s+)?indenture",
     "ACTIVE", "HIGH"),
    (r"additional\s+bonds?\s+test\s+(?:was\s+not|has\s+not\s+been|failed|cannot\s+be)\s+(?:met|satisfied|achieved|passed)",
     "ACTIVE", "HIGH"),
    (r"(?:failed|unable)\s+to\s+(?:meet|satisfy|achieve|pass)\s+the\s+additional\s+bonds?\s+test",
     "ACTIVE", "HIGH"),

    # Continuing disclosure default (MEDIUM-HIGH)
    (r"default\s+under\s+(?:the\s+)?continuing\s+disclosure",
     "ACTIVE", "MEDIUM"),
    (r"(?:material\s+)?failure\s+to\s+(?:file|provide|submit)\s+(?:the\s+)?(?:annual\s+)?continuing\s+disclosure",
     "ACTIVE", "MEDIUM"),

    # Generic non-compliance disclosure, no explicit waiver yet (HIGH)
    (r"non[-\s]?compliance\s+with\s+(?:certain\s+|the\s+|its\s+)?(?:financial\s+)?(?:covenants?|debt\s+covenants?)",
     "ACTIVE", "HIGH"),
    (r"(?:was\s+|were\s+|has\s+been\s+|have\s+been\s+)(?:not\s+in\s+compliance|out\s+of\s+compliance)\s+with\s+(?:certain\s+|the\s+|its\s+)?(?:financial\s+)?covenants?",
     "ACTIVE", "HIGH"),
    (r"(?:covenant|indenture)\s+(?:was\s+|were\s+|has\s+been\s+)?(?:violated|breached)",
     "ACTIVE", "HIGH"),

    # CURED — breach occurred intra-year but was remedied by FYE (MEDIUM)
    (r"(?:was\s+|were\s+|has\s+been\s+|have\s+been\s+)(?:subsequently\s+|since\s+)?(?:cured|remedied|brought\s+(?:back\s+)?into\s+compliance)",
     "CURED", "MEDIUM"),
    (r"(?:intra[-\s]?year|temporary|temporarily)\s+(?:non[-\s]?compliance|violation|breach)",
     "CURED", "MEDIUM"),
]

# Boilerplate exclusions — covenant terms RECITED in note disclosure that
# describe what the covenants ARE, not whether they were breached.
BOILERPLATE_CONTEXT_PATTERNS = [
    r"\bthe\s+(?:bond\s+)?indenture\s+(?:requires|provides|specifies|contains)",
    r"\bthe\s+(?:loan|trust)\s+agreement\s+(?:requires|provides|specifies|contains)",
    r"\bcovenants?\s+include\b",
    r"\bcovenants?\s+(?:require|provide|specify)",
    r"\bin\s+compliance\s+with\s+all\b",  # "the entity is in compliance with all covenants"
    r"\bwas\s+in\s+compliance\s+with\b",
    r"\bwere\s+in\s+compliance\s+with\b",
    r"\bis\s+in\s+compliance\s+with\b",
    r"\bare\s+in\s+compliance\s+with\b",
    r"\bremained\s+in\s+compliance\b",
    r"\bremains?\s+in\s+compliance\b",
    # Description of penalty structure, not actual breach
    r"\bif\s+the\s+(?:District|Authority|Corporation|Hospital|Entity|Borrower)\s+(?:fails|does\s+not|were\s+to)",
    r"\bwould\s+(?:constitute|result\s+in|trigger)\b",
]


def _is_boilerplate_context(text_lower: str, match_start: int, match_end: int,
                             window: int = 200) -> bool:
    """Return True if the regex match looks like covenant-terms recital,
    not an actual breach disclosure."""
    ctx_start = max(0, match_start - window)
    ctx_end = min(len(text_lower), match_end + window)
    context = text_lower[ctx_start:ctx_end]
    for bp in BOILERPLATE_CONTEXT_PATTERNS:
        if re.search(bp, context):
            return True
    return False


def find_breach_disclosure(text: str) -> tuple[bool, str | None, str | None, str | None]:
    """Scan free-text for breach disclosure.

    Returns (fires, breach_status, severity, excerpt).
    If multiple matches, returns the most severe.
    """
    if not text:
        return False, None, None, None

    severity_rank = {"RED": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    best: tuple[bool, str | None, str | None, str | None] = (False, None, None, None)
    best_sev = -1

    text_lower = text.lower()
    for pattern, status, severity in BREACH_PATTERNS:
        for m in re.finditer(pattern, text_lower, re.IGNORECASE | re.DOTALL):
            if _is_boilerplate_context(text_lower, m.start(), m.end()):
                continue
            sev = severity_rank.get(severity, 0)
            if sev > best_sev:
                start = max(0, m.start() - 120)
                end = min(len(text), m.end() + 120)
                excerpt = re.sub(r"\s+", " ", text[start:end]).strip()
                best = (True, status, severity, excerpt)
                best_sev = sev
    return best


def evaluate(obligor_name: str, data: dict) -> dict:
    """Evaluate covenant-breach disclosure for an obligor.

    Strategy:
      1. If explicit_breach_status is provided as a manual override, use it
         (caller has reviewed the audit and made the call).
      2. Otherwise scan audit_text + emma_continuing_disclosure_text for
         breach-pattern matches.
      3. If neither audit nor EMMA text is provided AND no override,
         return UNVERIFIABLE (we cannot confirm "no breach" from silence).
    """
    as_of = data.get("as_of_date")
    audit_url = data.get("audit_url")
    audit_fy = data.get("audit_fy")
    audit_page = data.get("audit_page")
    audit_text = data.get("audit_text") or ""
    emma_text = data.get("emma_continuing_disclosure_text") or ""
    emma_url = data.get("emma_url")
    explicit = (data.get("explicit_breach_status") or "").upper().strip() or None

    # ---- explicit override path -------------------------------------------
    if explicit:
        status_to_severity = {
            "ACCELERATION": "RED",
            "ACTIVE": "RED",
            "WAIVER_OBTAINED": "HIGH",
            "CURED": "MEDIUM",
            "NONE": None,
        }
        if explicit not in status_to_severity:
            return {
                "fires": False,
                "reason": "INVALID_OVERRIDE",
                "evidence": {"explicit_breach_status": explicit,
                             "confidence": "UNVERIFIABLE"},
            }
        if explicit == "NONE":
            return {
                "fires": False,
                "reason": "NO_BREACH_PER_AUDIT",
                "evidence": {
                    "breach_disclosure_found": False,
                    "breach_status": "NONE",
                    "audit_url": audit_url,
                    "audit_fy": audit_fy,
                    "audit_page": audit_page,
                    "as_of_date": as_of,
                    "confidence": data.get("confidence", "HIGH"),
                },
            }
        return {
            "fires": True,
            "reason": f"BREACH_{explicit}",
            "severity": status_to_severity[explicit],
            "evidence": {
                "breach_disclosure_found": True,
                "breach_language_excerpt": data.get("breach_language_excerpt", ""),
                "breach_status": explicit,
                "audit_url": audit_url,
                "audit_fy": audit_fy,
                "audit_page": audit_page,
                "emma_url": emma_url,
                "as_of_date": as_of,
                "confidence": data.get("confidence", "HIGH"),
            },
        }

    # ---- pattern-scan path -------------------------------------------------
    if not audit_text and not emma_text:
        # Hostile validator: silence is NOT "no breach"
        return {
            "fires": False,
            "reason": "UNVERIFIABLE_NO_AUDIT_TEXT",
            "evidence": {
                "breach_disclosure_found": None,
                "breach_status": "UNKNOWN",
                "audit_url": audit_url,
                "audit_fy": audit_fy,
                "as_of_date": as_of,
                "confidence": "UNVERIFIABLE",
            },
        }

    # Audit gets first crack (primary source), EMMA second
    audit_fires, audit_status, audit_severity, audit_excerpt = find_breach_disclosure(audit_text)
    emma_fires, emma_status, emma_severity, emma_excerpt = find_breach_disclosure(emma_text)

    severity_rank = {"RED": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    if audit_fires and emma_fires:
        if severity_rank.get(audit_severity, 0) >= severity_rank.get(emma_severity, 0):
            fires, status, severity, excerpt = audit_fires, audit_status, audit_severity, audit_excerpt
            primary_source = "AUDIT"
        else:
            fires, status, severity, excerpt = emma_fires, emma_status, emma_severity, emma_excerpt
            primary_source = "EMMA"
    elif audit_fires:
        fires, status, severity, excerpt = audit_fires, audit_status, audit_severity, audit_excerpt
        primary_source = "AUDIT"
    elif emma_fires:
        fires, status, severity, excerpt = emma_fires, emma_status, emma_severity, emma_excerpt
        primary_source = "EMMA"
    else:
        fires, status, severity, excerpt, primary_source = False, "NONE", None, None, "AUDIT"

    if not fires:
        return {
            "fires": False,
            "reason": "NO_BREACH_LANGUAGE_FOUND",
            "evidence": {
                "breach_disclosure_found": False,
                "breach_status": "NONE",
                "audit_url": audit_url,
                "audit_fy": audit_fy,
                "audit_page": audit_page,
                "emma_url": emma_url,
                "as_of_date": as_of,
                "confidence": "HIGH" if audit_text else "MEDIUM",
            },
        }

    return {
        "fires": True,
        "reason": f"BREACH_{status}",
        "severity": severity,
        "evidence": {
            "breach_disclosure_found": True,
            "breach_language_excerpt": excerpt,
            "breach_status": status,
            "primary_source": primary_source,
            "audit_url": audit_url,
            "audit_fy": audit_fy,
            "audit_page": audit_page,
            "emma_url": emma_url,
            "as_of_date": as_of,
            "confidence": "HIGH" if primary_source == "AUDIT" else "MEDIUM",
        },
    }


# ---- self-test ------------------------------------------------------------

if __name__ == "__main__":
    # Prototype catch — Alliance Charter
    prototype = {
        "audit_fy": "2024-2025",
        "audit_url": "https://emma.msrb.org/...alliance...",
        "audit_text": (
            "During fiscal year 2025, the Organization was in non-compliance "
            "with certain financial covenants under the Master Indenture. "
            "Subsequent to year-end, the Organization obtained a waiver from "
            "the trustee with respect to such non-compliance. Management is "
            "implementing corrective measures."
        ),
        "as_of_date": "2026-05-28",
    }
    r = evaluate("Alliance College-Ready Public Schools", prototype)
    print("[prototype]", r["fires"], r.get("reason"), r.get("severity"))
    assert r["fires"]
    assert r["reason"] == "BREACH_WAIVER_OBTAINED"

    # Negative — clean covenant compliance language
    clean = {
        "audit_fy": "2024",
        "audit_url": "https://...",
        "audit_text": (
            "The District is required by the Indenture to maintain a debt "
            "service coverage ratio of not less than 1.20x. As of June 30, "
            "2024, the District was in compliance with all financial "
            "covenants under the Indenture."
        ),
        "as_of_date": "2026-05-28",
    }
    r = evaluate("Sample District", clean)
    print("[clean]", r["fires"], r.get("reason"))
    assert not r["fires"]

    # Negative — covenant TERMS recital (boilerplate)
    boilerplate = {
        "audit_fy": "2024",
        "audit_url": "https://...",
        "audit_text": (
            "The Indenture requires the District to maintain certain "
            "financial covenants, including a minimum debt service coverage "
            "ratio of 1.10x. If the District fails to meet these covenants, "
            "the trustee may declare an event of default. The covenants "
            "include rate covenants and additional bonds tests."
        ),
        "as_of_date": "2026-05-28",
    }
    r = evaluate("Sample District", boilerplate)
    print("[boilerplate]", r["fires"], r.get("reason"))
    assert not r["fires"]

    # UNVERIFIABLE — no audit text
    unverifiable = {"audit_fy": "2024", "as_of_date": "2026-05-28"}
    r = evaluate("Sample District", unverifiable)
    print("[unverifiable]", r["fires"], r.get("reason"))
    assert not r["fires"]
    assert r["reason"] == "UNVERIFIABLE_NO_AUDIT_TEXT"

    # RED — accelerated maturity
    accelerated = {
        "audit_fy": "2024",
        "audit_url": "https://...",
        "audit_text": (
            "An event of default has occurred under the Loan Agreement. "
            "The trustee has accelerated all amounts due under the bonds "
            "and demanded payment from the obligated group."
        ),
        "as_of_date": "2026-05-28",
    }
    r = evaluate("Sample Distressed Obligor", accelerated)
    print("[accelerated]", r["fires"], r.get("reason"), r.get("severity"))
    assert r["fires"]
    assert r["evidence"]["breach_status"] == "ACCELERATION"

    # Explicit override
    override = {
        "audit_fy": "2024-2025",
        "audit_url": "https://...",
        "explicit_breach_status": "WAIVER_OBTAINED",
        "breach_language_excerpt": "manually transcribed",
        "as_of_date": "2026-05-28",
    }
    r = evaluate("Manual Override Example", override)
    print("[override]", r["fires"], r.get("reason"))
    assert r["fires"]
    assert r["reason"] == "BREACH_WAIVER_OBTAINED"

    print("\nAll self-tests passed.")
