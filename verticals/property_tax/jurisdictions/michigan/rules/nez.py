from __future__ import annotations

from decimal import Decimal

from core.models import GapResult, Record, RuleMatch, SignalRule

from ..config import MILLAGE_NEZ, MILLAGE_NON_HOMESTEAD

MILLAGE_DELTA = MILLAGE_NON_HOMESTEAD - MILLAGE_NEZ  # 61 mills


def apply(rule: SignalRule, gap: GapResult, records: list[Record]) -> RuleMatch:
    """
    NEZ Homestead — Neighborhood Enterprise Zone.

    Reduces millage to ~6 mills for individually-owned, owner-occupied residential
    in a designated NEZ district. Entity owners (LLCs, corporations) cannot claim.
    Requires annual NEZ Homestead application with Detroit HRD.
    """
    nez_district = gap.metadata.get("nez_district")
    owner_is_entity = gap.metadata.get("owner_is_entity", False)

    if not nez_district:
        return RuleMatch(
            rule=rule,
            matched=False,
            confidence=1.0,
            gap_adjustment=Decimal(0),
            explanation="Not in a NEZ district",
            interpreter="compiled",
        )

    if owner_is_entity:
        return RuleMatch(
            rule=rule,
            matched=False,
            confidence=1.0,
            gap_adjustment=Decimal(0),
            explanation=f"In NEZ district {nez_district} but entity-owned — NEZ Homestead rate unavailable",
            interpreter="compiled",
        )

    tv_delta = gap.raw_gap
    adjustment = -(tv_delta / 1000 * Decimal(str(MILLAGE_DELTA)))

    return RuleMatch(
        rule=rule,
        matched=True,
        confidence=1.0,
        gap_adjustment=adjustment,
        explanation=(
            f"NEZ district {nez_district} — individually owned, potentially eligible for "
            f"{MILLAGE_NEZ:.0f}-mill rate (vs {MILLAGE_NON_HOMESTEAD:.0f} mills standard). "
            f"Requires active NEZ Homestead application."
        ),
        interpreter="compiled",
    )
