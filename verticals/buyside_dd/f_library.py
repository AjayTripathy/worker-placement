"""
f-library: encoded expected relationships between claims and observable reality.

Each rule answers: "If this claim is true, what should we observe in M?"

Initial seed focused on real-estate syndications (the user's working DD vertical).
Expand as new domains arise.
"""
from __future__ import annotations

from .schemas import FRule, ReferentType


REAL_ESTATE_RULES: list[FRule] = [

    # ── PROPERTY VALUATION CLAIMS ─────────────────────────────────────────────
    FRule(
        rule_id="re.acquisition_price_matches_deed",
        predicate="acquired_at_price",
        referent_type=ReferentType.PARCEL,
        description="Sponsor's claimed acquisition price should match recorded deed consideration",
        formula="abs(sponsor_claim - deed_consideration) / sponsor_claim < 0.05",
        formula_inputs=["deed_consideration", "deed_date", "deed_grantor", "deed_grantee"],
        noise_tolerance=0.05,
        severity_thresholds={"PASS": 0.05, "MINOR": 0.10, "MODERATE": 0.25, "SEVERE": 0.50, "CRITICAL": 1.0},
        source_authority="County recorder of deeds; transfer tax records",
    ),

    FRule(
        rule_id="re.acquisition_price_matches_mls",
        predicate="acquired_at_price",
        referent_type=ReferentType.PARCEL,
        description="If MLS shows a recent sale, sponsor's claimed acquisition price should match",
        formula="abs(sponsor_claim - mls_sale_price) / mls_sale_price < 0.05",
        formula_inputs=["mls_sale_price", "mls_sale_date"],
        noise_tolerance=0.05,
        severity_thresholds={"PASS": 0.05, "MINOR": 0.15, "MODERATE": 0.30, "SEVERE": 0.50},
        source_authority="MLS / Redfin / Zillow sale history",
    ),

    FRule(
        rule_id="re.zero_consideration_deed_with_market_sale",
        predicate="acquired_at_price",
        referent_type=ReferentType.PARCEL,
        description="$0 or $1 quit-claim deed on the same date as a market MLS sale is a fraud signal (Detroit La Salle pattern)",
        formula="deed_consideration <= 1 AND mls_sale_price > 1000 AND deed_date == mls_sale_date",
        formula_inputs=["deed_consideration", "deed_type", "mls_sale_price", "mls_sale_date"],
        severity_thresholds={"PASS": 0.0, "CRITICAL": 1.0},  # binary; flagged or not
        source_authority="MCL 211.27a (Michigan); analogous statutes elsewhere",
    ),

    # ── ASSESSED VALUE CONSISTENCY ────────────────────────────────────────────
    FRule(
        rule_id="re.assessor_value_consistent_with_claim",
        predicate="property_market_value",
        referent_type=ReferentType.PARCEL,
        description="Sponsor's claimed market value shouldn't be wildly above the assessor's estimate",
        formula="abs(sponsor_claim - assessor_market_value) / assessor_market_value",
        formula_inputs=["assessor_market_value", "assessor_etcv"],
        noise_tolerance=0.30,  # assessor often lags market by 20-30%
        severity_thresholds={"PASS": 0.30, "MINOR": 0.50, "MODERATE": 1.00, "SEVERE": 2.00},
        source_authority="County assessor office",
    ),

    # ── RENT ROLL VERIFICATION ────────────────────────────────────────────────
    FRule(
        rule_id="re.unit_rent_within_market_range",
        predicate="charges_rent",
        referent_type=ReferentType.BUILDING,
        description="Sponsor's claimed in-place rent should fall within market comparable range for the area+type",
        formula="abs(sponsor_rent - market_median) / market_median < 0.30",
        formula_inputs=["market_median_rent", "market_p25_rent", "market_p75_rent", "unit_bedrooms"],
        noise_tolerance=0.30,
        severity_thresholds={"PASS": 0.30, "MINOR": 0.50, "MODERATE": 1.00, "SEVERE": 2.00},
        source_authority="Census ACS B25031; RentCast; Zillow Rent Index; StreetEasy/Zumper scrape",
    ),

    FRule(
        rule_id="re.rent_below_legal_max_if_stabilized",
        predicate="charges_rent",
        referent_type=ReferentType.BUILDING,
        jurisdiction="NYC",
        description="If building is rent-stabilized (J-51, 421a, or pre-1974 6+ units), claimed rent must be ≤ legal max",
        formula="sponsor_rent <= legal_max_rent_for_unit",
        formula_inputs=["j51_status", "registration_year", "borough", "rgb_cumulative_factor"],
        severity_thresholds={"PASS": 0.05, "MODERATE": 0.50, "SEVERE": 1.00, "CRITICAL": 2.00},
        source_authority="NYC RSL § 26-510; J-51 Socrata y7az-s7wc",
    ),

    # ── REHAB BUDGET VERIFICATION ─────────────────────────────────────────────
    FRule(
        rule_id="re.rehab_budget_proportional_to_permits",
        predicate="rehab_spend_planned",
        referent_type=ReferentType.PARCEL,
        description="Stated rehab budget should be roughly proportional to building permit cost estimates",
        formula="abs(sponsor_budget - permit_cost_estimate) / permit_cost_estimate",
        formula_inputs=["permit_cost_estimate", "permit_count", "permit_dates"],
        noise_tolerance=0.50,  # permits often understate true cost
        severity_thresholds={"PASS": 0.50, "MODERATE": 1.50, "SEVERE": 3.00},
        source_authority="City building department permit records",
    ),

    # ── SPONSOR TRACK RECORD ─────────────────────────────────────────────────
    FRule(
        rule_id="re.sponsor_owns_claimed_priors",
        predicate="previously_acquired",
        referent_type=ReferentType.ENTITY,
        description="Sponsor's claimed prior acquisitions should be findable in deed records under the LLC's name or known affiliates",
        formula="prior_property_in_deed_records_for_(sponsor_or_affiliate)",
        formula_inputs=["sponsor_legal_name", "affiliate_llcs", "deed_records_by_grantee"],
        severity_thresholds={"PASS": 0.0, "MODERATE": 0.5, "SEVERE": 1.0},
        source_authority="State LLC registry + county deed records",
    ),

    FRule(
        rule_id="re.sponsor_claimed_returns_match_filings",
        predicate="prior_fund_returned_irr",
        referent_type=ReferentType.ENTITY,
        description="Sponsor's claimed prior-fund returns should match Form ADV / SEC filings if registered",
        formula="abs(sponsor_claim - sec_filing_value) / abs(sec_filing_value)",
        formula_inputs=["sec_form_adv", "sec_form_d", "private_fund_filings"],
        noise_tolerance=0.10,
        severity_thresholds={"PASS": 0.10, "MODERATE": 0.30, "SEVERE": 0.50},
        source_authority="SEC IAPD database; Form ADV filings",
    ),

    FRule(
        rule_id="re.sponsor_no_undisclosed_litigation",
        predicate="legal_status_is_clean",
        referent_type=ReferentType.ENTITY,
        description="Sponsor (and affiliates) should have no undisclosed litigation in PACER or state courts",
        formula="pacer_cases_against_sponsor == disclosed_cases",
        formula_inputs=["sponsor_legal_name", "affiliate_names", "pacer_search", "state_court_search"],
        severity_thresholds={"PASS": 0.0, "MODERATE": 0.3, "SEVERE": 0.7, "CRITICAL": 1.0},
        source_authority="PACER; state court online dockets",
    ),

    # ── LIENS, ENCUMBRANCES, TAX STATUS ──────────────────────────────────────
    FRule(
        rule_id="re.no_undisclosed_liens",
        predicate="lien_status_is_clean",
        referent_type=ReferentType.PARCEL,
        description="No mechanic's liens, tax liens, or UCC filings against the property beyond disclosed",
        formula="recorded_liens == disclosed_liens",
        formula_inputs=["county_lien_records", "ucc_filings", "tax_lien_records"],
        severity_thresholds={"PASS": 0.0, "MODERATE": 0.3, "SEVERE": 0.7, "CRITICAL": 1.0},
        source_authority="County recorder; state UCC database; state/county tax assessor",
    ),

    FRule(
        rule_id="re.property_tax_paid_current",
        predicate="property_tax_status_is_current",
        referent_type=ReferentType.PARCEL,
        description="Property taxes should be paid current; delinquency is a deal flag",
        formula="years_delinquent == 0",
        formula_inputs=["assessor_payment_history", "tax_delinquency_status"],
        severity_thresholds={"PASS": 0.0, "MODERATE": 0.3, "SEVERE": 0.7, "CRITICAL": 1.0},
        source_authority="County tax assessor / treasurer",
    ),

    FRule(
        rule_id="re.no_pending_taxable_uncap",
        predicate="property_tax_baseline_is_stable",
        referent_type=ReferentType.PARCEL,
        jurisdiction="Michigan",
        description="If recent transfer occurred, Taxable Value will reset on next assessment (MCL 211.27a). Sponsor's projected taxes must account for this.",
        formula="if recent_arms_length_transfer: projected_TV >= SEV",
        formula_inputs=["last_transfer_date", "current_TV", "current_SEV", "deed_consideration"],
        severity_thresholds={"PASS": 0.0, "MODERATE": 0.3, "SEVERE": 0.7},
        source_authority="MCL 211.27a; Detroit/Wayne County assessor",
    ),

    # ── CODE VIOLATIONS / DEFERRED MAINTENANCE ───────────────────────────────
    FRule(
        rule_id="re.no_undisclosed_code_violations",
        predicate="building_condition_is_disclosed",
        referent_type=ReferentType.BUILDING,
        description="Open code violations should be disclosed; surprises here add capex liability",
        formula="open_violations_in_city_records == disclosed_violations",
        formula_inputs=["city_code_enforcement_records", "open_violation_count", "open_violation_severity"],
        severity_thresholds={"PASS": 0.0, "MODERATE": 0.3, "SEVERE": 0.7, "CRITICAL": 1.0},
        source_authority="City code enforcement / building department",
    ),

    # ── EVICTION / TENANT TURNOVER ───────────────────────────────────────────
    FRule(
        rule_id="re.eviction_history_consistent_with_occupancy",
        predicate="occupancy_is_stable",
        referent_type=ReferentType.BUILDING,
        description="High eviction filings inconsistent with claimed stable occupancy",
        formula="eviction_filings_per_unit_per_year < 0.20",
        formula_inputs=["eviction_court_filings", "unit_count", "filing_period"],
        noise_tolerance=0.10,
        severity_thresholds={"PASS": 0.10, "MODERATE": 0.30, "SEVERE": 0.50},
        source_authority="State landlord-tenant court records; Princeton Eviction Lab",
    ),

    # ── RELATED-PARTY TRANSACTIONS ───────────────────────────────────────────
    FRule(
        rule_id="re.no_related_party_acquisition_uplift",
        predicate="acquired_at_arms_length",
        referent_type=ReferentType.PARCEL,
        description="If sponsor or affiliate sold to themselves at uplift, it's a related-party fee extraction",
        formula="grantor_unrelated_to_grantee_in_state_corp_filings",
        formula_inputs=["deed_grantor", "deed_grantee", "state_corp_filings", "shared_officers", "shared_addresses"],
        severity_thresholds={"PASS": 0.0, "MODERATE": 0.5, "SEVERE": 1.0, "CRITICAL": 2.0},
        source_authority="State corporate registries; deed grantor/grantee chains",
    ),

    # ── PROJECTED FINANCIALS SANITY ──────────────────────────────────────────
    FRule(
        rule_id="re.projected_noi_consistent_with_market",
        predicate="projects_noi",
        referent_type=ReferentType.BUILDING,
        description="Projected NOI per unit should fall within reasonable range for asset class+market",
        formula="projected_noi_per_unit / market_median_noi_per_unit",
        formula_inputs=["market_noi_per_unit", "asset_class", "metro_area"],
        noise_tolerance=0.30,
        severity_thresholds={"PASS": 0.30, "MODERATE": 0.50, "SEVERE": 1.00},
        source_authority="CoStar / NCREIF / RealPage market reports; assessor income approach data",
    ),

    FRule(
        rule_id="re.projected_cap_rate_within_market",
        predicate="projects_exit_cap_rate",
        referent_type=ReferentType.BUILDING,
        description="Projected exit cap rate should be within +/- 1% of market spot for asset+market",
        formula="abs(projected_cap_rate - market_cap_rate) <= 0.01",
        formula_inputs=["market_cap_rate", "asset_class", "metro_area", "exit_year"],
        noise_tolerance=0.01,
        severity_thresholds={"PASS": 0.01, "MODERATE": 0.02, "SEVERE": 0.04},
        source_authority="CBRE / JLL cap rate surveys; CoStar transaction comps",
    ),

    FRule(
        rule_id="re.distribution_assumptions_reasonable",
        predicate="projects_cash_distribution",
        referent_type=ReferentType.ENTITY,
        description="Projected LP distributions shouldn't depend on exit price >2x acquisition or rent growth >market+3%",
        formula="projected_exit_multiple <= 2.0 AND projected_rent_growth - market_rent_growth <= 0.03",
        formula_inputs=["projected_exit_multiple", "market_rent_growth_5yr", "projected_rent_growth"],
        severity_thresholds={"PASS": 0.0, "MODERATE": 0.3, "SEVERE": 0.7},
        source_authority="Underwriting standards (industry practice)",
    ),

    # ── VENTURE FUND-RAISE RECONCILIATION ─────────────────────────────────
    FRule(
        rule_id="re.raise_amount_matches_form_d",
        predicate="raise_amount",
        referent_type=ReferentType.ENTITY,
        description="Sponsor's claimed raise amount should match the SEC Form D primary doc within 5%.",
        formula="abs(claim - form_d.totalAmountSold) / form_d.totalAmountSold < 0.05",
        formula_inputs=["form_d[0].totalAmountSold", "form_d[0].totalOfferingAmount"],
        noise_tolerance=0.05,
        severity_thresholds={"PASS": 0.05, "MINOR": 0.15, "MODERATE": 0.30, "SEVERE": 0.50, "CRITICAL": 1.0},
        source_authority="SEC EDGAR Form D primary_doc.xml",
    ),

    # ── VENTURE / GROWTH-STAGE EXISTENCE RULES ────────────────────────────
    # Claimed building/factory/project should appear in city permits if it exists.
    FRule(
        rule_id="re.claimed_building_in_city_permits",
        predicate="operates_industrial_facility",
        referent_type=ReferentType.BUILDING,
        description="If sponsor claims a building/project in city X, the city's permit DB should have at least one matching permit. Zero hits across multiple name variants is a SEVERE absence-of-record signal.",
        formula="permit_count > 0",
        formula_inputs=["austin_permit_count", "bozeman_permit_count", "abq_permit_count"],
        severity_thresholds={"PASS": 0.0, "SEVERE": 1.0},
        source_authority="City open data permit portals",
    ),
    # Sponsor entity should appear in state corporate registry.
    FRule(
        rule_id="re.sponsor_in_corp_registry",
        predicate="registered_as_entity",
        referent_type=ReferentType.ENTITY,
        description="Claimed sponsor entity should appear in state corporate registry. Zero hits = SEVERE.",
        formula="corp_match_count > 0",
        formula_inputs=["tx_corp_match_count", "edgar_company_match_count"],
        severity_thresholds={"PASS": 0.0, "SEVERE": 1.0},
        source_authority="State Secretary of State + SEC EDGAR",
    ),
    # Industrial facility should appear in OSHA establishment search.
    FRule(
        rule_id="re.factory_in_osha",
        predicate="operates_industrial_facility",
        referent_type=ReferentType.ENTITY,
        description="Claimed manufacturing facility should appear in OSHA establishment search if it's been operating long enough to be inspected. New/small factories may legitimately have no record (mitigates severity).",
        formula="osha_establishment_count > 0",
        formula_inputs=["osha_establishment_count"],
        severity_thresholds={"PASS": 0.0, "MODERATE": 1.0},
        source_authority="OSHA Establishment Search",
    ),

    # ── ADDRESS-RESOLVED FACTORY VERIFICATION ─────────────────────────────
    # When a deal claims a specific property address, the city's permit
    # database should show ANY permits at that address (ignoring whose name
    # is on them — tenants don't appear on permits, GCs and landlords do).
    # This rule fires the address-resolved check that closes the false-negative
    # we hit on AHC where searching "AHC" returned 0 permits but the address
    # search returns 12.
    FRule(
        rule_id="re.address_corroborated_by_permits",
        predicate="located_at_address",
        referent_type=ReferentType.BUILDING,
        description="If issuer claims a specific factory/office address, the city's permit DB should have at least one permit at that address. Recent permits with industrial scope (electrical service upgrade, mechanical, fire-suppression) corroborate active build-out. Zero permits = SEVERE absence of record.",
        formula="permit_count_at_address > 0; recent_industrial_permit_present → PASS; old_only_permits → MODERATE",
        formula_inputs=["austin_permit_count", "austin_permit[*].applied", "austin_permit[*].description"],
        severity_thresholds={"PASS": 0.0, "MODERATE": 0.5, "SEVERE": 1.0},
        source_authority="City open data permit portals (address-keyed search)",
    ),

    # ── PARENT-ENTITY FORM D EXISTENCE ────────────────────────────────────
    # When direct securities sales are claimed (SAFE checks paid directly to
    # parent entity, not via SPV), Reg D 506(b)/(c) requires Form D within 15
    # days of first sale. Absence of any parent-entity Form D when direct sales
    # are evidenced is a Reg D compliance question OR signals the lead investor
    # never closed.
    FRule(
        rule_id="re.parent_form_d_exists_for_direct_securities",
        predicate="filed_form_d_for_direct_safes",
        referent_type=ReferentType.ENTITY,
        description="Reg D 506(b)/(c) requires Form D within 15 days of first sale. If the issuer took direct SAFE checks (not via SPV), a parent-entity Form D should exist on EDGAR.",
        formula="edgar_company_match_count > 0 OR full_text_match > 0",
        formula_inputs=["edgar_company_match_count", "edgar_filing_count"],
        severity_thresholds={"PASS": 0.0, "SEVERE": 1.0},
        source_authority="SEC EDGAR; Reg D 506(b)/(c) Form D filing requirement",
    ),

    # ── LEAD INVESTOR VISIBILITY ──────────────────────────────────────────
    # Named "lead" investors should appear somewhere in the public record:
    # either as a related person on the issuer's Form D, in their own SAFE
    # documents, or as a publicly-disclosed portfolio company on the lead's
    # website. Total invisibility despite being named as lead is a SEVERE
    # signal that the round structure isn't what the deck represents.
    FRule(
        rule_id="re.lead_investor_visible_in_public_record",
        predicate="led_investment_round",
        referent_type=ReferentType.ENTITY,
        description="Named lead investor should appear in: issuer's Form D relatedPersons, publicly-listed portfolio of the lead, or own SAFE document. Total absence is SEVERE — the round may not have closed at the structure represented.",
        formula="edgar_match_count(lead) > 0 OR form_d_related_persons.contains(lead) OR portfolio_page_lists(lead, issuer)",
        formula_inputs=["edgar_company_match_count", "edgar_filing_count", "form_d[0].relatedPersons"],
        severity_thresholds={"PASS": 0.0, "MODERATE": 0.5, "SEVERE": 1.0},
        source_authority="SEC EDGAR; Form D relatedPersons; lead investor's public portfolio page",
    ),

    # ── VALUATION CAP (SAFE-derived) ──────────────────────────────────────
    # Claim's stated cap should match the cap recorded on the executed SAFE.
    # Requires the safe_pdf_parser connector (TODO) to emit `safe.cap` and
    # `safe.purchase_amount` observations. Until then, this rule will fire
    # but produce UNVERIFIABLE — the rule shell is ready for when the
    # connector lands.
    FRule(
        rule_id="re.valuation_cap_matches_safe_document",
        predicate="valuation_cap",
        referent_type=ReferentType.ENTITY,
        description="Claimed valuation cap must match the cap actually written on the executed SAFE. CAUTION: SAFE caps are not market-validated priced valuations — they are forward-looking ceilings.",
        formula="abs(claim - safe.cap) / claim < 0.05",
        formula_inputs=["safe.cap", "safe.purchase_amount", "safe.investor", "safe.date"],
        noise_tolerance=0.05,
        severity_thresholds={"PASS": 0.05, "MINOR": 0.10, "MODERATE": 0.25, "SEVERE": 0.50},
        source_authority="Executed SAFE PDF (parsed via safe_pdf_parser connector)",
    ),

    # ── TOTAL PAID BY INVESTOR (SAFE-derived) ─────────────────────────────
    # Investor's claimed total cost basis should match the sum of their
    # executed SAFE purchase amounts. Used to reconcile user-stated cost
    # basis against the documentary evidence.
    FRule(
        rule_id="re.total_paid_matches_safe_purchase_amounts",
        predicate="total_paid_to_AHC",
        referent_type=ReferentType.ENTITY,
        description="Investor's stated total paid should match the sum of their executed SAFE purchase amounts.",
        formula="abs(claim - sum(safe[*].purchase_amount where safe.investor == claim.subject)) / claim < 0.05",
        formula_inputs=["safe[*].purchase_amount", "safe[*].investor"],
        noise_tolerance=0.05,
        severity_thresholds={"PASS": 0.05, "MINOR": 0.10, "MODERATE": 0.25, "SEVERE": 0.50},
        source_authority="Executed SAFE PDFs aggregated by investor name",
    ),
]


# Index by (predicate, referent_type) for fast lookup
def index_rules(rules: list[FRule]) -> dict[tuple[str, ReferentType], list[FRule]]:
    idx: dict[tuple[str, ReferentType], list[FRule]] = {}
    for rule in rules:
        key = (rule.predicate, rule.referent_type)
        idx.setdefault(key, []).append(rule)
    return idx


REAL_ESTATE_RULES_INDEX = index_rules(REAL_ESTATE_RULES)


def find_rules(predicate: str, referent_type: ReferentType, jurisdiction: str = None) -> list[FRule]:
    """Look up applicable f-rules for a (predicate, referent_type) pair."""
    candidates = REAL_ESTATE_RULES_INDEX.get((predicate, referent_type), [])
    if jurisdiction:
        # Filter to rules that match jurisdiction OR are jurisdiction-agnostic
        return [r for r in candidates if r.jurisdiction is None or r.jurisdiction == jurisdiction]
    return candidates
