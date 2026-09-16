from __future__ import annotations

from decimal import Decimal

from core.models import GapResult, Record, RuleMatch, SignalRule

# California R&T Code §218: owner-occupied residential gets a $7,000 AV reduction.
# Tax impact at 1.2%: $7,000 × 12 mills / 1,000 = $84/yr — small but structurally correct.
HOE_AV_REDUCTION = Decimal("7000")


def apply(rule: SignalRule, gap: GapResult, records: list[Record]) -> RuleMatch:
    """
    California Homeowner Exemption (R&T Code §218).

    Reduces net assessed value by $7,000 for owner-occupied residential property.
    Detected via the homeowner_exemption flag on the assessor roll.
    """
    claimed = gap.metadata.get("homeowner_exemption", False)

    if not claimed:
        return RuleMatch(
            rule=rule,
            matched=False,
            confidence=1.0,
            gap_adjustment=Decimal(0),
            explanation="No Homeowner Exemption claimed on assessor roll",
            interpreter="compiled",
        )

    return RuleMatch(
        rule=rule,
        matched=True,
        confidence=1.0,
        gap_adjustment=-HOE_AV_REDUCTION,
        explanation="Homeowner Exemption claimed — AV reduced by $7,000 (R&T Code §218)",
        interpreter="compiled",
    )
