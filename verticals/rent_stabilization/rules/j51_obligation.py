from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["nyc_rent_stabilized_units", "j51_tax_benefit_history"],
    "asset_classes": ["nyc_multifamily_re"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "j51_obligation",
}

from decimal import Decimal

from core.models import GapResult, Record, RuleMatch, SignalRule


def apply(rule: SignalRule, gap: GapResult, records: list[Record]) -> RuleMatch:
    """
    NYC Admin. Code §11-243 + Roberts v. Tishman Speyer (2009).

    Fires when:
      - The building has a confirmed J-51 stabilization obligation
        (PLUTO+J-51 cross-join produced status="j51_confirmed"), AND
      - A positive gap was detected (listed > max_legal_rent).

    Distinct from RSL_OVERCHARGE in that the legal basis is statutory + case-law
    specific (not vintage-inferred) and the confidence is 1.0. The Court of
    Appeals held that a J-51 building cannot deregulate any unit during the
    benefit period or its 35-year tail — listing above the legal stabilized
    max is a per-se violation of the J-51 covenant, irrespective of whether
    the unit was ever individually deregulated.
    """
    listed     = gap.metadata.get("listed_rent", 0)
    max_legal  = gap.metadata.get("max_legal_rent", 0)
    status     = gap.metadata.get("stabilization_status", "")
    confidence = gap.metadata.get("stabilization_confidence", 0.0)

    matched = (
        status == "j51_confirmed"
        and gap.raw_gap > 0
        and listed > 0
        and max_legal > 0
    )

    if not matched:
        return RuleMatch(
            rule=rule,
            matched=False,
            confidence=float(confidence) if status == "j51_confirmed" else 0.0,
            gap_adjustment=Decimal(0),
            explanation=(
                "No J-51 obligation violation"
                if status != "j51_confirmed"
                else "J-51 building present but no overcharge gap"
            ),
            interpreter="compiled",
        )

    monthly_gap = float(gap.raw_gap)
    return RuleMatch(
        rule=rule,
        matched=True,
        confidence=1.0,
        gap_adjustment=Decimal(0),
        explanation=(
            f"J-51 obligation violation. Building is in PLUTO + active J-51 dataset "
            f"(NYC Admin. Code §11-243). Under Roberts v. Tishman Speyer Properties, "
            f"L.P., 13 N.Y.3d 270 (2009), every unit in this building must remain "
            f"rent-stabilized for the J-51 benefit period plus 35 years; deregulation "
            f"during this window is void ab initio. "
            f"Listed rent ${listed:,.0f}/mo exceeds the estimated maximum legal "
            f"stabilized rent ${max_legal:,.0f}/mo by ${monthly_gap:,.0f}/mo "
            f"(${monthly_gap * 12:,.0f}/yr). "
            f"Tenants have a private right of action for overcharge recovery (6-year "
            f"lookback) and the Attorney General has parens patriae standing under "
            f"Executive Law §63(12) for systemic Roberts violations."
        ),
        interpreter="compiled",
    )
