from __future__ import annotations

from decimal import Decimal

from core.models import GapResult, Record, RuleMatch, SignalRule

EXEMPT_STATUTES = frozenset({"125.1415A", "MCL 125.1415A"})
EXEMPT_KEYWORDS = ("EXEMPT", "LIHTC", "PILOT", "125.1415")


def apply(rule: SignalRule, gap: GapResult, records: list[Record]) -> RuleMatch:
    """
    MCL 125.1415A — PILOT / LIHTC full tax exemption.

    Properties under Payment In Lieu Of Taxes agreements or Low Income Housing
    Tax Credit programs are fully exempt from property tax. Detected via
    tax_status field on the assessor roll.
    """
    tax_status = (gap.metadata.get("tax_status") or "").upper()

    matched = any(kw in tax_status for kw in EXEMPT_KEYWORDS)

    if not matched:
        return RuleMatch(
            rule=rule,
            matched=False,
            confidence=1.0,
            gap_adjustment=Decimal(0),
            explanation=f"tax_status={tax_status!r} — not a PILOT/LIHTC exemption",
            interpreter="compiled",
        )

    return RuleMatch(
        rule=rule,
        matched=True,
        confidence=1.0,
        gap_adjustment=-gap.raw_gap,  # full exemption: wipe out the gap
        explanation=f"PILOT/LIHTC exemption detected (tax_status={tax_status!r}) — property is fully tax-exempt",
        interpreter="compiled",
    )
