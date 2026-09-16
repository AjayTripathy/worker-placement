from __future__ import annotations

from decimal import Decimal

from core.models import GapResult, Record, RuleMatch, SignalRule

from ..config import MILLAGE_HOMESTEAD, MILLAGE_NON_HOMESTEAD

MILLAGE_DELTA = Decimal(str(MILLAGE_NON_HOMESTEAD - MILLAGE_HOMESTEAD))  # 27 mills

# Owner-name patterns that indicate a legitimate carve-out from PRE-entity
# violation: housing cooperatives, LDHAs, etc. can have legal pathways for
# PRE through individual member occupancy. Validated on Detroit roll
# (2026-05-18 scan): only 23 of 23,211 candidate parcels matched these
# patterns, so the false-positive cost from over-exclusion is negligible.
_LEGIT_CARVE_OUTS = (
    "CO-OP", "COOPERATIVE",
    "LDHA", "LIMITED DIVIDEND",
    "SENIOR HOUSING", "LIHTC",
)


def _is_legit_carve_out(owner: str) -> bool:
    upper = (owner or "").upper()
    return any(kw in upper for kw in _LEGIT_CARVE_OUTS)


def apply(rule: SignalRule, gap: GapResult, records: list[Record]) -> RuleMatch:
    """
    PRE-on-Entity violation — MCL 211.7cc requires the Principal Residence
    Exemption to apply only to natural-person owner-occupancy. An LLC, Inc,
    Corp, Ltd, or LP cannot legitimately claim PRE: these entities cannot
    "occupy" a principal residence in the statutory sense.

    Validated 2026-05-18 against Detroit Open Data: 23,211 parcels match
    strict-entity (LLC/INC/CORP/LTD/LP) + 100% PRE, exposing ~$10.72M/yr
    in suppressed taxes via the 67-vs-40 mill differential.

    Detected from assessor roll alone — owner_is_entity classification
    + homestead_pct field. No external data required.

    Carve-outs (housing co-ops, LDHAs, LIHTC) are excluded by owner-name
    keyword match; these have legitimate PRE pathways through individual
    member occupancy.

    Annual impact = TV × (millage_standard - millage_homestead) × pct / 1000

    For a $20K-TV LLC-owned parcel at 100% PRE: $20,000 × 27 / 1000 = $540/yr
    suppressed. Across 23K parcels: ~$10.7M/yr suppressed citywide.
    """
    owner = gap.metadata.get("owner") or ""
    owner_is_entity = bool(gap.metadata.get("owner_is_entity"))
    homestead_pct = gap.metadata.get("homestead_pct") or 0.0

    if not owner_is_entity:
        return RuleMatch(
            rule=rule, matched=False, confidence=1.0,
            gap_adjustment=Decimal(0),
            explanation=f"Owner {owner!r} is not classified as an entity",
            interpreter="compiled",
        )

    if homestead_pct <= 0:
        return RuleMatch(
            rule=rule, matched=False, confidence=1.0,
            gap_adjustment=Decimal(0),
            explanation=f"Entity owner has homestead_pct={homestead_pct} — no PRE claimed",
            interpreter="compiled",
        )

    if _is_legit_carve_out(owner):
        return RuleMatch(
            rule=rule, matched=False, confidence=1.0,
            gap_adjustment=Decimal(0),
            explanation=(
                f"Owner {owner!r} matches co-op/LDHA carve-out pattern — "
                f"member-occupancy PRE pathway may apply"
            ),
            interpreter="compiled",
        )

    # Annual dollar gap from the millage differential. The current TV is
    # taken as the taxable base — this is the suppressed tax at TODAY's
    # capped TV. Any TV-uncap component is a SEPARATE fraud handled by
    # the standard PropertyTaxGapFunction + scorer chain.
    tv = gap.metadata.get("taxable_value") or gap.regulated_value or Decimal(0)
    pct = Decimal(str(homestead_pct)) / Decimal(100)
    annual_impact = (Decimal(str(tv)) / Decimal(1000)) * MILLAGE_DELTA * pct

    return RuleMatch(
        rule=rule, matched=True, confidence=1.0,
        gap_adjustment=annual_impact,
        explanation=(
            f"Entity owner {owner!r} claims {homestead_pct:.0f}% PRE — "
            f"violates MCL 211.7cc natural-person-occupancy requirement. "
            f"Millage should be {MILLAGE_NON_HOMESTEAD:.0f} not {MILLAGE_HOMESTEAD:.0f}; "
            f"annual gap on current TV ${float(tv):,.0f} = ${float(annual_impact):,.0f}/yr"
        ),
        interpreter="compiled",
    )
