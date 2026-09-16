from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["nyc_rent_stabilized_units"],
    "asset_classes": ["nyc_multifamily_re"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "rsl_overcharge",
}

from decimal import Decimal

from core.models import GapResult, Record, RuleMatch, SignalRule


def apply(rule: SignalRule, gap: GapResult, records: list[Record]) -> RuleMatch:
    """
    NYC RSL §26-516 overcharge rule.

    Fires when the gap function detected a positive overcharge (listed_rent >
    estimated max legal stabilized rent). Confirms the signal and adds the
    statutory reference. gap_adjustment is zero — the raw gap from the gap
    function already represents the monthly overcharge.
    """
    listed     = gap.metadata.get("listed_rent", 0)
    max_legal  = gap.metadata.get("max_legal_rent", 0)
    confidence = gap.metadata.get("stabilization_confidence", 0.5)

    matched = gap.raw_gap > 0 and listed > 0 and max_legal > 0

    if not matched:
        return RuleMatch(
            rule=rule,
            matched=False,
            confidence=float(confidence),
            gap_adjustment=Decimal(0),
            explanation="No overcharge detected",
            interpreter="compiled",
        )

    monthly_gap = float(gap.raw_gap)
    return RuleMatch(
        rule=rule,
        matched=True,
        confidence=float(confidence),
        gap_adjustment=Decimal(0),
        explanation=(
            f"Listed rent ${listed:,.0f}/mo exceeds estimated max legal stabilized "
            f"rent ${max_legal:,.0f}/mo by ${monthly_gap:,.0f}/mo "
            f"(${monthly_gap * 12:,.0f}/yr). "
            f"Stabilization confidence: {confidence:.0%}. "
            "Tenants may be entitled to recover overcharges for up to 6 years "
            "plus treble damages if willful (Admin. Code §26-516)."
        ),
        interpreter="compiled",
    )
