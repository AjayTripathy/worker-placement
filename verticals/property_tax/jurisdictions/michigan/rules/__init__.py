"""
Michigan SignalRule registry.

Compiled rules have implementation= set to their apply() function path.
LLM-fallback rules have implementation=None — TieredRuleInterpreter calls the LLM
with rule.source_text at query time.
"""
from core.models import SignalRule

RULES: list[SignalRule] = [
    SignalRule(
        rule_id="PILOT",
        vertical="property_tax",
        jurisdiction="michigan",
        rule_type="gap_explainer",
        detectable=True,
        statutory_ref="MCL 125.1415A",
        description="PILOT/LIHTC full tax exemption — detected via tax_status field",
        implementation="verticals.property_tax.jurisdictions.michigan.rules.pilot.apply",
        priority=1,
    ),
    SignalRule(
        rule_id="PRE",
        vertical="property_tax",
        jurisdiction="michigan",
        rule_type="gap_modifier",
        detectable=True,
        statutory_ref="MCL 211.7cc",
        description="Principal Residence Exemption — reduces millage 67→40 mills",
        implementation="verticals.property_tax.jurisdictions.michigan.rules.pre.apply",
        priority=10,
    ),
    SignalRule(
        rule_id="PRE_ENTITY_VIOLATION",
        vertical="property_tax",
        jurisdiction="michigan",
        rule_type="gap_modifier",
        detectable=True,
        statutory_ref="MCL 211.7cc",
        description=(
            "Entity owner (LLC/Inc/Corp/Ltd/LP) claims PRE — violates "
            "natural-person-occupancy requirement. Adds millage-differential "
            "gap to annual impact independent of any TV-uncap fraud."
        ),
        implementation="verticals.property_tax.jurisdictions.michigan.rules.pre_entity_violation.apply",
        priority=15,
    ),
    SignalRule(
        rule_id="NEZ",
        vertical="property_tax",
        jurisdiction="michigan",
        rule_type="gap_modifier",
        detectable=True,
        statutory_ref="Detroit City Ordinance — NEZ Homestead",
        description="NEZ Homestead — reduces millage to ~6 mills for individually-owned residential in NEZ district",
        implementation="verticals.property_tax.jurisdictions.michigan.rules.nez.apply",
        priority=20,
    ),
    SignalRule(
        rule_id="PA210",
        vertical="property_tax",
        jurisdiction="michigan",
        rule_type="gap_modifier",
        detectable=False,
        statutory_ref="MCL 207.771 et seq. (PA 210 of 2005)",
        description="Commercial Rehabilitation Act — freezes TV at pre-renovation level. Not detectable from assessor roll.",
        implementation=None,
        confidence_if_llm=0.3,
        priority=30,
        source_text=(
            "PA 210 of 2005 (MCL 207.771-207.787): A qualified local governmental unit may "
            "establish a commercial rehabilitation district and grant exemption certificates. "
            "The taxable value of a qualified facility is frozen at the pre-rehabilitation level "
            "for the duration of the exemption (up to 10 years). No flag appears on the standard "
            "assessor roll."
        ),
    ),
    SignalRule(
        rule_id="OPRA",
        vertical="property_tax",
        jurisdiction="michigan",
        rule_type="gap_modifier",
        detectable=False,
        statutory_ref="MCL 207.841 et seq. (PA 146 of 2000)",
        description="Obsolete Property Rehabilitation Act — TV freeze for obsolete commercial/industrial. Not detectable from assessor roll.",
        implementation=None,
        confidence_if_llm=0.3,
        priority=31,
        source_text=(
            "PA 146 of 2000 (MCL 207.841-207.856): Provides a tax exemption for the rehabilitation "
            "of obsolete property. The taxable value is frozen during the exemption period. "
            "No indicator appears on the standard assessor roll."
        ),
    ),
]
