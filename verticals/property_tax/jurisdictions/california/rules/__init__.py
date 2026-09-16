from core.models import SignalRule

RULES: list[SignalRule] = [
    SignalRule(
        rule_id="WELFARE_EXEMPTION",
        vertical="property_tax",
        jurisdiction="*",
        rule_type="gap_modifier",
        detectable=False,
        statutory_ref="Cal. R&T Code §214",
        description="Welfare exemption — nonprofits, churches, and charitable organizations",
        implementation=None,
        confidence_if_llm=0.5,
        priority=1,
        source_text=(
            "R&T Code §214: Property owned and used exclusively for religious, hospital, "
            "scientific, or charitable purposes by a qualifying organization is exempt from "
            "property tax. Requires annual filing of BOE-267 with the county assessor."
        ),
    ),
    SignalRule(
        rule_id="HOE",
        vertical="property_tax",
        jurisdiction="*",
        rule_type="gap_modifier",
        detectable=True,
        statutory_ref="Cal. R&T Code §218",
        description="Homeowner Exemption — $7,000 AV reduction for owner-occupied residential",
        implementation=(
            "verticals.property_tax.jurisdictions.california.rules.homeowner_exemption.apply"
        ),
        priority=10,
    ),
    SignalRule(
        rule_id="PROP19_EXCLUSION",
        vertical="property_tax",
        jurisdiction="*",
        rule_type="gap_modifier",
        detectable=True,
        statutory_ref="Cal. Const. Art. XIII A §2.1 (Prop 19, 2020)",
        description=(
            "Parent-child transfer exclusion — primary residence transferred parent-to-child "
            "may be excluded from full reassessment up to $1M AV above the parent's factored "
            "base year value"
        ),
        implementation=None,
        confidence_if_llm=0.4,
        priority=20,
        source_text=(
            "Prop 19 (effective Feb 16, 2021): Transfers of a primary residence between "
            "parent and child are excluded from reassessment only if the child uses the "
            "property as their primary residence within one year of transfer. The exclusion "
            "is limited to $1,000,000 above the parent's factored base year value. "
            "Transfers of investment or rental properties are now fully reassessed."
        ),
    ),
]
