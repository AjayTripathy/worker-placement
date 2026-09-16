from core.models import SignalRule

RULES: list[SignalRule] = [
    SignalRule(
        rule_id="RSL_OVERCHARGE",
        vertical="rent_stabilization",
        jurisdiction="*",
        rule_type="gap_modifier",
        detectable=True,
        statutory_ref="NYC Admin. Code §26-516",
        description=(
            "Rent overcharge — landlord charging above the legal regulated rent ceiling. "
            "Tenants may recover overcharges for up to 6 years plus treble damages if willful."
        ),
        implementation=(
            "verticals.rent_stabilization.rules.rsl_overcharge.apply"
        ),
        priority=10,
    ),
    SignalRule(
        rule_id="J51_OBLIGATION",
        vertical="rent_stabilization",
        jurisdiction="*",
        rule_type="gap_modifier",
        detectable=True,
        statutory_ref="NYC Admin. Code §11-243; Roberts v. Tishman Speyer (2009)",
        description=(
            "J-51 stabilization obligation — buildings receiving J-51 tax benefits must "
            "keep all units rent-stabilized for the benefit period + 35 years. Deregulation "
            "during this window is void under Roberts v. Tishman Speyer."
        ),
        implementation=(
            "verticals.rent_stabilization.rules.j51_obligation.apply"
        ),
        confidence_if_llm=0.7,
        priority=5,
        source_text=(
            "NYC Admin. Code §11-243 requires rent stabilization as a condition of J-51 "
            "tax abatement. The Court of Appeals in Roberts v. Tishman Speyer Properties "
            "(2009) held that apartments in J-51 buildings cannot be deregulated even if "
            "rent exceeds the high-rent threshold during the benefit period."
        ),
    ),
    SignalRule(
        rule_id="HSTPA_LOCK",
        vertical="rent_stabilization",
        jurisdiction="*",
        rule_type="gap_modifier",
        detectable=False,
        statutory_ref="NY ETPA §26-511 as amended by L. 2019 ch. 36",
        description=(
            "HSTPA permanent lock — since June 14 2019 no apartment may be permanently "
            "deregulated regardless of rent level or tenant income. Any deregulation after "
            "that date is void ab initio."
        ),
        implementation=None,
        confidence_if_llm=0.6,
        priority=1,
        source_text=(
            "The Housing Stability and Tenant Protection Act of 2019 (HSTPA) eliminated "
            "high-rent vacancy deregulation and high-income deregulation. All apartments "
            "that were stabilized on June 14, 2019 remain stabilized permanently. "
            "Apartments deregistered after that date without a lawful basis (e.g., "
            "conversion to co-op/condo, owner occupancy with proper notice) remain subject "
            "to RSL and any rents charged above the legal regulated rent are recoverable."
        ),
    ),
]
