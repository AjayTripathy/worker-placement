from __future__ import annotations

from decimal import Decimal

from core.models import GapResult, Record, RuleMatch, SignalRule

from ..config import MILLAGE_HOMESTEAD, MILLAGE_NON_HOMESTEAD

MILLAGE_DELTA = MILLAGE_NON_HOMESTEAD - MILLAGE_HOMESTEAD  # 27 mills


def apply(rule: SignalRule, gap: GapResult, records: list[Record]) -> RuleMatch:
    """
    MCL 211.7cc — Principal Residence Exemption.

    Reduces applicable millage from 67 to 40 mills for owner-occupied residential.
    Detected via homestead_pct field on the assessor roll.
    """
    homestead_pct = gap.metadata.get("homestead_pct") or 0.0

    if not homestead_pct or homestead_pct <= 0:
        return RuleMatch(
            rule=rule,
            matched=False,
            confidence=1.0,
            gap_adjustment=Decimal(0),
            explanation="No PRE claimed (homestead_pct=0)",
            interpreter="compiled",
        )

    pct = homestead_pct / 100.0
    tv_delta = gap.raw_gap
    adjustment = -(tv_delta / 1000 * Decimal(str(MILLAGE_DELTA)) * Decimal(str(pct)))

    return RuleMatch(
        rule=rule,
        matched=True,
        confidence=1.0,
        gap_adjustment=adjustment,
        explanation=(
            f"PRE {homestead_pct:.0f}% claimed — millage reduced from "
            f"{MILLAGE_NON_HOMESTEAD:.0f} to {MILLAGE_HOMESTEAD:.0f} mills on "
            f"{homestead_pct:.0f}% of property"
        ),
        interpreter="compiled",
    )
