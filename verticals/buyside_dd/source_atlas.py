"""
Source atlas — the M space for buyside real-estate DD.

Organized by REFERENT TYPE → ATTRIBUTE → SOURCE. Read this top docstring as the
catalog; the MSource entries below are the machine-readable form the dispatcher uses.

╔══════════════════════════════════════════════════════════════════════════════╗
║ M-SPACE TAXONOMY FOR REAL-ESTATE BUYSIDE DD                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║ ┌─ PARCEL (a specific tax-roll lot)                                          ║
║ │   ├ deed_records         → county recorder, ACRIS, WPRDC                   ║
║ │   ├ mortgage_records     → county recorder (lender, balance, lien order)   ║
║ │   ├ assessment_records   → county assessor (TV, SEV, ETCV, exemptions)     ║
║ │   ├ tax_payment_status   → county treasurer (delinquent? years owed?)      ║
║ │   ├ tax_lien_records     → county recorder + state DOR                     ║
║ │   ├ ucc_security_interest→ state SoS UCC database                          ║
║ │   ├ zoning_designation   → city/county zoning portal                       ║
║ │   ├ flood_zone           → FEMA NFHL                                       ║
║ │   ├ environmental_status → EPA Envirofacts, state DEQ                      ║
║ │   ├ sale_history         → MLS aggregators (Zillow, Redfin), recorder      ║
║ │   └ ownership_chain      → recorder grantee chain over time                ║
║ │                                                                            ║
║ ├─ BUILDING (improvements on parcel)                                         ║
║ │   ├ unit_count           → assessor + DOB                                  ║
║ │   ├ year_built / sqft    → assessor                                        ║
║ │   ├ rent_stabilization   → NYC J-51/DHCR; LA RSO; SF rent board (per-juris)║
║ │   ├ building_permits     → city building department                        ║
║ │   ├ code_violations      → city code enforcement                           ║
║ │   ├ eviction_filings     → housing/landlord-tenant court records           ║
║ │   ├ rent_roll            → no public source; PHA records for HCV; FOIA     ║
║ │   ├ section8_status      → HUD multifamily contracts (PBV); PHA FOIA (HCV) ║
║ │   ├ insurance_history    → CLUE report (paid, owner consent required)      ║
║ │   └ utility_history      → utility provider (FOIA, owner consent)          ║
║ │                                                                            ║
║ ├─ GEOGRAPHIC_AREA (zip, tract, county, MSA)                                 ║
║ │   ├ market_median_rent   → Census ACS B25031, RentCast, Zillow ZORI        ║
║ │   ├ hud_fair_market_rent → HUD FMR (annual, by metro + small-area)         ║
║ │   ├ hud_income_limits    → HUD IL (annual)                                 ║
║ │   ├ market_cap_rate      → CoStar, CBRE/JLL surveys, Real Capital Analytics║
║ │   ├ vacancy_rate         → Census ACS, CoStar                              ║
║ │   ├ employment_trends    → BLS LAUS / QCEW                                 ║
║ │   ├ population_trends    → Census ACS                                      ║
║ │   ├ school_quality       → state DOE testing data                          ║
║ │   ├ crime_stats          → FBI UCR / NIBRS, city open data                 ║
║ │   ├ eviction_rate        → Princeton Eviction Lab                          ║
║ │   └ flood_risk_modeled   → First Street Foundation                         ║
║ │                                                                            ║
║ ├─ ENTITY (sponsor, LLC, fund, manager)                                      ║
║ │   ├ corporate_registration → state SoS (50 states); OpenCorporates         ║
║ │   ├ registered_agent     → state SoS                                       ║
║ │   ├ officer_member_list  → state annual reports (varies by state)          ║
║ │   ├ federal_litigation   → PACER                                           ║
║ │   ├ federal_state_litig  → CourtListener                                   ║
║ │   ├ bankruptcy_history   → PACER bankruptcy courts                         ║
║ │   ├ sec_filings          → SEC EDGAR (Form D, 10-K, 13-F, etc.)            ║
║ │   ├ ria_registration     → SEC IAPD (Form ADV)                             ║
║ │   ├ broker_dealer_status → FINRA BrokerCheck                               ║
║ │   ├ state_securities_actions → NASAA aggregator                            ║
║ │   ├ tax_lien_judgment    → state court + county recorder                   ║
║ │   ├ ucc_filings          → state UCC databases                             ║
║ │   ├ real_estate_license  → state DRE (per state)                           ║
║ │   ├ related_entities     → registered agent overlap; shared address        ║
║ │   ├ tax_exempt_990       → IRS 990 (for 501c3-affiliated sponsors)         ║
║ │   ├ appointment_availability → own public booking scheduler (slot panel)   ║
║ │   └ ofac_sanctions       → Treasury OFAC SDN                               ║
║ │                                                                            ║
║ └─ PERSON (principal, manager, guarantor)                                    ║
║     ├ professional_license → state license boards (CRE, CPA, attorney, etc.) ║
║     ├ news / reputation    → web search, news APIs                           ║
║     ├ ofac_sanctions       → OFAC SDN                                        ║
║     ├ pacer_personal       → PACER party search                              ║
║     ├ state_court_personal → state court portals                             ║
║     ├ professional_history → LinkedIn (paid for full data)                   ║
║     └ political_donations  → FEC                                             ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ ACCESS PATTERN LEGEND                                                        ║
║   api                 — JSON/REST/GraphQL endpoint, programmatic             ║
║   file_download       — periodic bulk file (CSV/Excel/Shapefile)             ║
║   scrape              — HTML scrape of a public web form                     ║
║   scrape_per_state    — per-jurisdiction scraping (50-state coverage needed) ║
║   foia                — formal records request, weeks-to-months              ║
║   paid_subscription   — commercial data product                              ║
║   manual              — phone/visit/in-person                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Coverage gaps to be aware of when running DD:
  - Section 8 HCV (tenant-based) landlord registry: only via per-PHA FOIA. No
    national database. Estimated 30-day async lag.
  - Beneficial ownership: CTA BOI registry was struck down for domestic
    reporting companies (Texas Top Cop Shop, 2024-2025); not reliably accessible.
  - Private fund returns: no audited public source; triangulate via individual
    deal outcomes (recorder + foreclosure + eviction).
  - Off-market transactions: many properties sold without MLS listing — only
    appear in deed records.
"""
from __future__ import annotations

from .schemas import MSource, ReferentType


REAL_ESTATE_SOURCES: list[MSource] = [

    # ══════════════════════════════════════════════════════════════════════════
    # PARCEL — deed records
    # ══════════════════════════════════════════════════════════════════════════
    MSource(
        source_id="wprdc_allegheny_sales",
        referent_type=ReferentType.PARCEL,
        attribute="deed_records",
        jurisdiction="Allegheny_County_PA",
        granularity="per_instrument",
        access_pattern="api",
        endpoint="https://data.wprdc.org/api/3/action/datastore_search",
        authority_tier=1,
        connector_module="connectors.wprdc_allegheny",
        notes="CKAN datastore_search; resource_id=5bbe6c55-bce6-4edb-9d04-68edeb6bf7b1; covers Pittsburgh + ~130 muni; validated against FCRE2",
    ),
    MSource(
        source_id="acris_nyc",
        referent_type=ReferentType.PARCEL,
        attribute="deed_records",
        jurisdiction="NYC",
        granularity="per_instrument",
        access_pattern="api",
        endpoint="https://data.cityofnewyork.us/resource/8h5j-fqxa.json",
        authority_tier=1,
        connector_module="connectors.acris_nyc",
    ),
    MSource(
        source_id="wayne_county_deeds",
        referent_type=ReferentType.PARCEL,
        attribute="deed_records",
        jurisdiction="Wayne_County_MI",
        granularity="per_instrument",
        access_pattern="scrape",
        endpoint="https://www.waynecounty.com/elected/treasurer/online-property-search.aspx",
        connector_module="connectors.wayne_county_deeds",
    ),
    MSource(
        source_id="stlouis_city_recorder",
        referent_type=ReferentType.PARCEL,
        attribute="deed_records",
        jurisdiction="StLouis_City_MO",
        granularity="per_instrument",
        access_pattern="scrape",
        endpoint="https://www.stlouis-mo.gov/government/departments/recorder-of-deeds/",
        connector_module="connectors.stlouis_recorder",
    ),
    MSource(
        source_id="zillow_redfin_sale_snippet",
        referent_type=ReferentType.PARCEL,
        attribute="deed_records",
        jurisdiction="US",
        granularity="per_instrument",
        access_pattern="scrape_via_intermediary",
        endpoint="search engine snippets pointed at zillow/redfin/homes.com",
        authority_tier=5,
        connector_module="connectors.search_snippet_extractor",
        completeness=0.6,
        notes="Fallback when county recorder is gated. Snippet-only.",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # PARCEL — mortgage records (capital stack)
    # ══════════════════════════════════════════════════════════════════════════
    MSource(
        source_id="wprdc_allegheny_mortgages",
        referent_type=ReferentType.PARCEL,
        attribute="mortgage_records",
        jurisdiction="Allegheny_County_PA",
        granularity="per_instrument",
        access_pattern="api",
        endpoint="https://data.wprdc.org/api/3/action/datastore_search",
        connector_module="connectors.wprdc_allegheny",
        notes="Same connector as sales; mortgage instrument table; reveals senior lender + amount",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # PARCEL — assessment records
    # ══════════════════════════════════════════════════════════════════════════
    MSource(
        source_id="detroit_assessor",
        referent_type=ReferentType.PARCEL,
        attribute="assessment_records",
        jurisdiction="Detroit_MI",
        granularity="per_parcel_per_year",
        access_pattern="api",
        endpoint="https://data.detroitmi.gov/datasets/parcels-2/",
        connector_module="connectors.detroit_assessor",
    ),
    MSource(
        source_id="nyc_pluto",
        referent_type=ReferentType.PARCEL,
        attribute="building_characteristics",
        jurisdiction="NYC",
        granularity="annual",
        access_pattern="file_download",
        endpoint="https://www1.nyc.gov/site/planning/data-maps/open-data.page",
        connector_module="connectors.nyc_pluto",
    ),
    MSource(
        source_id="wprdc_allegheny_assessment",
        referent_type=ReferentType.PARCEL,
        attribute="assessment_records",
        jurisdiction="Allegheny_County_PA",
        granularity="per_parcel",
        access_pattern="api",
        endpoint="https://data.wprdc.org/api/3/action/datastore_search",
        connector_module="connectors.wprdc_allegheny",
    ),
    MSource(
        source_id="laserfiche_weblink",
        referent_type=ReferentType.PARCEL,
        attribute="entitlement_record",
        jurisdiction="US",
        granularity="per_planning_project",
        access_pattern="browser_automation",
        endpoint="Laserfiche WebLink (per-tenant; e.g. weblink.bozeman.net) — see connector TENANTS",
        authority_tier=1,
        connector_module="connectors.laserfiche_weblink",
        completeness=0.9,
        notes="ESCALATION/HEAVYWEIGHT: drives a REAL browser (Playwright + Chrome) to defeat the "
              "Cloudflare JS-challenge + cookie gate on Laserfiche WebLink municipal planning "
              "archives — where HTTP/curl/fingerprint all 403. Returns the PRIMARY entitlement "
              "record (site-plan application: applicant of record, property owner, unit count, "
              "product type, zoning, lot area, approval status). Verifies any real-estate/"
              "development offering's 'we are developing this / X units / approved / for-sale' "
              "claims. Validated 2026-06-16 on Bozeman (AHC Sun Valley = City file 24635: applicant/"
              "owner were the MASTER DEVELOPER not the sponsor; 30 apartments not 33 rowhouses). "
              "Many cities run Laserfiche WebLink — add tenants to connectors.TENANTS as validated. "
              "See memory reference_browser_automation_gated_portals.",
    ),

    MSource(
        source_id="litigation_screen",
        referent_type=ReferentType.PERSON,
        attribute="litigation_history",
        jurisdiction="US",
        granularity="per_person",
        access_pattern="api",
        endpoint="CourtListener/RECAP v4 search API (free federal-docket proxy for PACER)",
        authority_tier=1,
        connector_module="connectors.litigation_screen",
        completeness=0.7,
        notes="AUTO-DISPATCH on any named principal/operator/sponsor/GP (recall-floor). Pulls federal "
              "dockets + opinions and CLASSIFIES by materiality: MATERIAL = securities/fraud/RICO/"
              "investor-fiduciary/franchise-termination/debtor-bankruptcy (fires principal_litigation_flag); "
              "BASELINE = employment/ADA/wage-hour (routine for any large operator — does NOT fire). "
              "Distinguishes subject-as-defendant/debtor (bad) from plaintiff/creditor (neutral); flags "
              "common-name false positives as disambiguation_needed. COVERAGE: federal/RECAP only — state "
              "courts + full PACER + UCC are a paid/manual escalation. Built+validated 2026-06-17 on PCM "
              "Hospitality (Barry Dubin/B Wild/7 Star/Sublime Huts/KBP = clean of material categories; "
              "only routine employment/ADA at the 1,000-unit KBP franchisee).",
    ),
    MSource(
        source_id="litigation_screen",
        referent_type=ReferentType.ENTITY,
        attribute="litigation_history",
        jurisdiction="US",
        granularity="per_entity",
        access_pattern="api",
        endpoint="CourtListener/RECAP v4 search API",
        authority_tier=1,
        connector_module="connectors.litigation_screen",
        completeness=0.7,
        notes="Entity (LLC/fund/operating-company) federal-litigation screen; see the PERSON entry. "
              "Same connector handles person_name, entity_name, and extra.aliases in one call.",
    ),
    MSource(
        source_id="customer_id",
        referent_type=ReferentType.ENTITY,
        attribute="customer_concentration",
        jurisdiction="US",
        granularity="per_company",
        access_pattern="api",
        endpoint="customs bill-of-lading aggregators (importinfo/importgenius/importyeti) + Bayesian aggregation",
        authority_tier=3,
        connector_module="connectors.customer_id",
        completeness=0.5,
        notes="AUTO-DISPATCH when a diligence finds MATERIAL customer concentration (top customer N% "
              "of revenue / 'capacity sold out to a customer') but the customer is UNNAMED — resolves "
              "WHO the whale most likely is, the swing factor for any single-customer-dependent thesis. "
              "Method: resolve the customs-BOL SHIPPER alias (companies ship under a subsidiary, NOT the "
              "brand — Stevanato ships as 'Nuova Ompi', querying the brand returns nothing) -> pull "
              "shipper->consignee from free BOL data -> triangulate co-location/product-format/geography/"
              "demand-trend -> Bayesian posterior over candidate customers with leave-one-out robustness. "
              "BLIND SPOT: foreign fill-finish bypasses US customs (Novo fills in Denmark) -> 'customer "
              "absent' is weakly informative, never zero (down-weight, don't zero). Built+validated "
              "2026-06-25 on STVN: constrained GLP-1 book Lilly-anchored 93% (robust >=67% even dropping "
              "the customs channel); Novo bear-tail 4-21% -> de-risked the Novo-destock thesis crack.",
    ),
    MSource(
        source_id="hiring_velocity",
        referent_type=ReferentType.ENTITY,
        attribute="capacity_ramp",
        jurisdiction="US",
        granularity="per_site",
        access_pattern="api",
        endpoint="LinkedIn guest jobs endpoint (no auth) + Adzuna/Indeed (free key, for the operator wave)",
        authority_tier=3,
        connector_module="connectors.hiring_velocity",
        completeness=0.5,
        notes="AUTO-DISPATCH when a thesis depends on a NEW PLANT/CAPACITY RAMPING to utilization "
              "('coming online', 'operating leverage as the new plant fills', 'sold out into 20XX', "
              "'commercial production 20XX') — a free LEADING proxy for the ramp, ahead of the margin "
              "print. A plant ramping to full 24/7 production hires in a WAVE (operators/technicians/QC/"
              "shift crews) then TAPERS at full staff; track open-req COUNT + production-role MIX + "
              "posting VELOCITY over snapshots. CAVEATS: (1) LinkedIn skews white-collar -> the "
              "production-OPERATOR wave is Indeed-only (add a free Adzuna key to capture it; Latina "
              "showed operators on LinkedIn, Fishers didn't); (2) a single ~300-person plant is a small, "
              "lumpy signal -> read the TREND across snapshots, not one pull. Built 2026-06-25 after the "
              "satellite-thermal furnace sensor was CONTROL-REFUTED (a known-operating glass furnace "
              "showed no daytime-LST signal vs a Costco) and free phone/foot-traffic came up empty — "
              "hiring was the first free signal that produced a usable read (STVN Fishers/Latina ramp).",
    ),
    MSource(
        source_id="scheduler_exhaust",
        referent_type=ReferentType.ENTITY,
        attribute="appointment_availability",
        jurisdiction=None,
        granularity="per_location_panel",
        access_pattern="scrape",
        endpoint="per-instance PanelSpec.scheduler_url — framework desk/scheduler_exhaust.py "
                 "(Playwright real-Chrome fingerprint, land-first-for-cookies, in-page fetch; "
                 "--manual CSV fallback)",
        authority_tier=2,
        connector_module="connectors.scheduler_exhaust",
        completeness=0.1,
        latency_days=0,
        notes="PAPER / PROVISIONAL Ring-0 — direct observation of the issuer's OWN public "
              "booking surface (slot scarcity: days-to-next-available, %-same-day, "
              "booking-horizon depth over a FIXED location panel) = leading read on reported "
              "volume, 0-1 quarter latency. AUTO-DISPATCH when a thesis or marketing claim "
              "rests on appointment/reservation-based volume ('record patient volumes', "
              "'booked out for months', 'same-day availability', traffic/utilization claims "
              "at schedulable service businesses). CONFOUNDER: slot scarcity conflates demand "
              "with CAPACITY (staffing up shortens waits while volume rises) — cross-check "
              "hiring_velocity before reading a scarcity move as a volume move; also "
              "spot-vs-average sampling (fix the weekday/hour, read trends not pulls). "
              "blocked = MISSING never zero. Applicability census over the book: "
              "desk/data/scheduler_exhaust/candidates.json (UNSCREENED != CLEAR). Validation: "
              "PAPER — seed = DGX/LH lab panel Q2-2026 frozen calls, grades at the Q3-2026 "
              "prints (October); no sizing use before graduation.",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # ENTITY — venture / private-company verification (added for AHC deal)
    # ══════════════════════════════════════════════════════════════════════════
    MSource(
        source_id="company_signal",
        referent_type=ReferentType.ENTITY,
        attribute="funding_round_history",
        jurisdiction="US",
        granularity="per_company",
        access_pattern="scrape_via_intermediary",
        endpoint="DDG lite snippets aggregating Crunchbase / PitchBook / Preqin / news",
        authority_tier=5,
        connector_module="connectors.company_signal",
        completeness=0.5,
        notes="Surfaces Crunchbase URLs, mentioned dollar amounts, possible investor names from snippets. Triangulation only.",
    ),
    MSource(
        source_id="uspto_patents",
        referent_type=ReferentType.PERSON,
        attribute="patent_filings",
        jurisdiction="US",
        granularity="per_inventor",
        access_pattern="api",
        endpoint="https://search.patentsview.org/api/v1/patent",
        authority_tier=1,
        connector_module="connectors.uspto_patents",
        notes="PatentsView API (free, may need PATENTSVIEW_API_KEY env var for volume). Fallback to Google Patents scrape — currently flaky, needs iteration.",
    ),
    MSource(
        source_id="osha_establishment",
        referent_type=ReferentType.ENTITY,
        attribute="industrial_facility_presence",
        jurisdiction="US",
        granularity="per_establishment",
        access_pattern="scrape",
        endpoint="https://www.osha.gov/pls/imis/establishment.search",
        authority_tier=1,
        connector_module="connectors.osha_establishment",
        notes="OSHA establishment search. Hit = positive confirmation factory exists; no-hit = inconclusive (small/new facilities not yet inspected).",
    ),
    MSource(
        source_id="restaurant_ratings",
        referent_type=ReferentType.BUILDING,
        attribute="operating_location_status",
        jurisdiction="US",
        granularity="per_location",
        access_pattern="api",
        endpoint="Google Places API (New) places:searchText (business_status/rating/userRatingCount); OSM Nominatim no-key existence fallback",
        authority_tier=2,
        connector_module="connectors.restaurant_ratings",
        completeness=0.8,
        notes="AUTO-DISPATCH per address on any deal asserting brick-and-mortar OPERATING UNITS "
              "(restaurant/retail/clinic/franchise roster). Verifies each storefront EXISTS and is "
              "OPERATIONAL (vs CLOSED_PERMANENTLY/TEMPORARILY/NOT_FOUND) plus public rating + review "
              "count — a closed/relocated/declining unit in a marketed 'N operating units' roster "
              "silently inflates the count and the consolidated revenue struck on it. Ratings + "
              "operating-status need GOOGLE_PLACES_API_KEY (env) or ~/.google_places_key; the no-key "
              "path verifies address existence via OSM Nominatim only. Built 2026-06-25 after the "
              "Cheba/Evergreen 24-unit roster sat unverified until asked by hand (24/24 operating; "
              "the by-hand pass also caught 2 sister units excluded from the deal).",
    ),
    MSource(
        source_id="tx_comptroller_corp",
        referent_type=ReferentType.ENTITY,
        attribute="corporate_registration",
        jurisdiction="TX",
        granularity="per_entity",
        access_pattern="scrape",
        endpoint="https://mycpa.cpa.state.tx.us/coa/",
        authority_tier=1,
        connector_module="connectors.tx_comptroller_corp",
        notes="TX Comptroller franchise tax search. Currently flaky — needs proper form-action URL discovery; iterate later.",
    ),

    MSource(
        source_id="usaspending",
        referent_type=ReferentType.ENTITY,
        attribute="government_contracts",
        jurisdiction="US",
        granularity="per_recipient",
        access_pattern="api",
        endpoint="https://api.usaspending.gov/api/v2/search/spending_by_award/",
        authority_tier=1,
        connector_module="connectors.usaspending",
        notes="Federal prime-contract obligations to a recipient — primary auditable source for a "
              "'X% government revenue' claim; splits defense vs civil. LIMITS: prime-only (subs "
              "invisible), multi-year obligation totals (not annual revenue), classified IC (NRO/NGA "
              "National Intelligence Program) + FOREIGN sovereign contracts NOT included -> understates. "
              "A low total means the US-federal-prime portion is modest, NOT that gov revenue is small. "
              "Pair with the J-book (DoD program elements) + the 10-K geography table.",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # PARCEL — building permits (per-city expansion for venture/manufacturing DD)
    # ══════════════════════════════════════════════════════════════════════════
    MSource(
        source_id="austin_permits",
        referent_type=ReferentType.BUILDING,
        attribute="building_permits",
        jurisdiction="Austin_TX",
        granularity="per_permit",
        access_pattern="api",
        endpoint="https://data.austintexas.gov/resource/3syk-w9eu.json",
        authority_tier=1,
        connector_module="connectors.austin_permits",
        notes="Socrata open data; field names use compact form (applieddate, issue_date). Substring entity match risk — narrow queries needed.",
    ),
    MSource(
        source_id="bozeman_permits",
        referent_type=ReferentType.BUILDING,
        attribute="building_permits",
        jurisdiction="Bozeman_MT",
        granularity="per_permit",
        access_pattern="scrape",
        endpoint="https://bozeman.opengov.com/PORTAL/PROJECT/permitting",
        authority_tier=1,
        connector_module="connectors.bozeman_permits",
        completeness=0.3,
        notes="OpenGov SaaS portal — JS-heavy SPA. Connector currently fails gracefully; needs OpenGov API key OR portal-specific reverse engineering. Manual lookup viable.",
    ),
    MSource(
        source_id="albuquerque_permits",
        referent_type=ReferentType.BUILDING,
        attribute="building_permits",
        jurisdiction="Albuquerque_NM",
        granularity="per_permit",
        access_pattern="api",
        endpoint="https://services.arcgis.com/Q5pZAALdIzXDH0CV/ArcGIS/rest/services/Building_Permits/FeatureServer/0/query",
        authority_tier=1,
        connector_module="connectors.albuquerque_permits",
        completeness=0.3,
        notes="Tries ABQ ArcGIS Hub FeatureServer — URL is best-guess and may need updating per current portal state. Falls back to manual.",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # PARCEL — environmental
    # ══════════════════════════════════════════════════════════════════════════
    MSource(
        source_id="epa_envirofacts",
        referent_type=ReferentType.PARCEL,
        attribute="environmental_status",
        jurisdiction="US",
        granularity="per_facility",
        access_pattern="api",
        endpoint="https://data.epa.gov/efservice/",
        connector_module="connectors.epa_envirofacts",
        notes="Brownfield, Superfund, RCRA, TRI lookup by lat/lon or address",
    ),
    MSource(
        source_id="carbon_mapper",
        referent_type=ReferentType.PARCEL,
        attribute="environmental_status",
        jurisdiction="US",
        granularity="per_location",
        access_pattern="api",
        endpoint="https://api.carbonmapper.org/api/v1/catalog/plumes/annotated",
        authority_tier=1,
        connector_module="connectors.carbon_mapper",
        notes="Satellite/airborne methane+CO2 super-emitter plumes (Planet Tanager-1 'tan', "
              "NASA EMIT 'emi', GAO/AVIRIS aircraft). Public, no auth. Keyed by lat/lon or "
              "geocoded address. Instrument-measured PHYSICAL ground-truth: a quantified plume "
              "confirms the asset is operating/emitting (corroborates EPA Envirofacts) — and "
              "refutes a marketed 'clean'/'within-limits' claim. Free for non-commercial use; "
              "commercial productization needs a Carbon Mapper / Planet license (see TECH_DEBT).",
    ),
    MSource(
        source_id="sentinel2_buildout",
        referent_type=ReferentType.PARCEL,
        attribute="construction_activity",
        jurisdiction="US",
        granularity="per_location_per_period",
        access_pattern="api",
        endpoint="https://earth-search.aws.element84.com/v1/search",
        authority_tier=2,
        connector_module="connectors.sentinel2_buildout",
        notes="FREE Sentinel-2 L2A (10-20m) optical buildout signal: NDBI(built-up) + NDVI change "
              "baseline vs recent over a parcel. No auth (Element84 STAC + open sentinel-cogs bucket). "
              "Physical ground-truth for CFD/land-secured 'buildout on schedule' + buyside 'facility "
              "under construction/operating'. Tier-2 (coarse). Escalate to planet_imagery (3m/50cm, paid).",
    ),
    MSource(
        source_id="fema_nri_hazard",
        referent_type=ReferentType.PARCEL,
        attribute="natural_hazard_exposure",
        jurisdiction="US",
        granularity="per_census_tract",
        access_pattern="api",
        endpoint="https://services.arcgis.com/XG15cJAlne2vxtgt/arcgis/rest/services/"
                 "National_Risk_Index_Census_Tracts/FeatureServer/0/query",
        authority_tier=2,
        connector_module="connectors.fema_nri_hazard",
        notes="FEMA National Risk Index: 18 natural hazards (wildfire, earthquake, flood, drought, "
              "...) scored per census tract with building-value exposure. Free, no auth (official "
              "FEMA ArcGIS service; OpenFEMA does NOT carry it, old static download path is dead). "
              "Checks any hazard-shaped claim with a physical referent ('low natural-disaster "
              "risk', 'insurance costs stable', 'collateral in safe areas') and feeds the "
              "insurance-withdrawal value-drag channel: insurer exits track these designations and "
              "degrade marketability/assessed value years before any loss event. Lesson "
              "2026-06-10: check hazards JOINTLY — seismic diversification silently concentrated "
              "wildfire (Mendocino USD 91% of building value in high-fire tracts).",
    ),
    MSource(
        source_id="planet_imagery",
        referent_type=ReferentType.PARCEL,
        attribute="construction_activity",
        jurisdiction="US",
        granularity="per_location_per_period",
        access_pattern="paid_subscription",
        endpoint="https://api.planet.com/ (PlanetScope/SkySat; commercial license)",
        auth_required=True,
        authority_tier=1,
        connector_module="connectors.planet_imagery",
        notes="PAID escalation tier: PlanetScope ~3m daily / SkySat ~50cm tasked. Same buildout output "
              "contract as sentinel2_buildout at higher res. ~$2-5k/diligence event (SkySat tasking, "
              "€4,500 min) or ~$10-50k/yr (PlanetScope subscription). Needs PL_API_KEY; stub until a deal "
              "justifies it. See TECH_DEBT TD-1.",
    ),
    MSource(
        source_id="crop_yield_ndvi",
        referent_type=ReferentType.GEOGRAPHIC_AREA,
        attribute="crop_condition",
        jurisdiction="US",
        granularity="per_aoi_per_season",
        access_pattern="api",
        endpoint="https://earth-search.aws.element84.com/v1/search",
        authority_tier=2,
        connector_module="connectors.crop_yield_ndvi",
        notes="FREE Sentinel-2 peak-season NDVI, year-over-year, over a cropland AOI -> crop "
              "condition/yield proxy. Cross-checks ag/commodity/fertilizer/crop-insurance revenue "
              "claims ('record yields' vs NDVI down YoY = divergence). No phone substitute; runs on "
              "Planet's cheap daily tier too. Escalate to planet_imagery 3m for small-plot/field-edge.",
    ),
    MSource(
        source_id="forest_integrity",
        referent_type=ReferentType.GEOGRAPHIC_AREA,
        attribute="forest_harvest_rate",
        jurisdiction="INTL",
        granularity="per_aoi_per_year",
        access_pattern="api",
        endpoint="https://earth-search.aws.element84.com/v1/search",
        authority_tier=2,
        connector_module="connectors.forest_integrity",
        notes="FREE Sentinel-2 summer-NDVI forest health + clear-cut/final-fell proxy over managed-forest "
              "AOIs -> verifies the QUANTITY half of a forest/timberland ASSET MARK (health + harvest-rate-"
              "vs-stated-plan). Built for Stora Enso (STERV) EUR10.80/sh forest mark; run_forest_panel.py "
              "runs the 8-AOI panel (6 estate SAMPLE + protected-NP method-validation control + non-estate "
              "managed peer) and grades observed clear-cut % vs the ~0.9%/yr Swedish norm + the company's "
              "own stated harvest intensity. Guards: uniform-collapse + cloud-differential haze rejection "
              "(no fake fells). PAPER-gated (grades the mark's plausibility, not stock timing); estate is a "
              "REGION sample, not the deed map. companyfacts/transaction verifies the PRICE half separately.",
    ),
    MSource(
        source_id="oil_storage",
        referent_type=ReferentType.PARCEL,
        attribute="petroleum_storage_inventory",
        jurisdiction="US",
        granularity="per_tankfarm_per_period",
        access_pattern="api",
        endpoint="https://earth-search.aws.element84.com/v1/search",
        authority_tier=3,
        connector_module="connectors.oil_storage",
        notes="FREE Sentinel-2 AGGREGATE tank-farm floating-roof shadow proxy. Tier-3 (LOW): sun-angle "
              "confound is normalized, but at 10m tanks are 5-10px so per-tank roof-shadow is sub-pixel "
              "and the residual sits within noise — validated at Cushing 2023-25, NOT a usable barrel "
              "count on the free tier. This is the case that genuinely NEEDS planet_imagery 3m (paid). "
              "Pipeline + escalation socket are ready; cross-checks midstream/E&P/refiner storage claims "
              "+ complements EIA weekly stocks once on Planet res.",
    ),
    MSource(
        source_id="fema_nfhl",
        referent_type=ReferentType.PARCEL,
        attribute="flood_zone",
        jurisdiction="US",
        granularity="per_address",
        access_pattern="api",
        endpoint="https://hazards.fema.gov/gis/nfhl/services/public/NFHL/MapServer",
        connector_module="connectors.fema_nfhl",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # BUILDING — code violations & permits
    # ══════════════════════════════════════════════════════════════════════════
    MSource(
        source_id="hpd_violations_nyc",
        referent_type=ReferentType.BUILDING,
        attribute="code_violations",
        jurisdiction="NYC",
        granularity="per_violation",
        access_pattern="api",
        endpoint="https://data.cityofnewyork.us/resource/wvxf-dwi5.json",
        connector_module="connectors.hpd_violations",
    ),
    MSource(
        source_id="detroit_blight_violations",
        referent_type=ReferentType.PARCEL,
        attribute="code_violations",
        jurisdiction="Detroit_MI",
        granularity="per_violation",
        access_pattern="api",
        endpoint="https://data.detroitmi.gov/datasets/blight-violations/",
        connector_module="connectors.detroit_blight",
    ),
    MSource(
        source_id="pittsburgh_pli_violations",
        referent_type=ReferentType.BUILDING,
        attribute="code_violations",
        jurisdiction="Pittsburgh_PA",
        granularity="per_violation",
        access_pattern="api",
        endpoint="https://data.wprdc.org/dataset/pittsburgh-pli-violations-report",
        connector_module="connectors.wprdc_allegheny",
        notes="Pittsburgh PLI (Permits Licenses Inspections) via WPRDC",
    ),
    MSource(
        source_id="nyc_dob_permits",
        referent_type=ReferentType.BUILDING,
        attribute="building_permits",
        jurisdiction="NYC",
        granularity="per_permit",
        access_pattern="api",
        endpoint="https://data.cityofnewyork.us/resource/ipu4-2q9a.json",
        connector_module="connectors.nyc_dob",
    ),
    MSource(
        source_id="detroit_permits",
        referent_type=ReferentType.PARCEL,
        attribute="building_permits",
        jurisdiction="Detroit_MI",
        granularity="per_permit",
        access_pattern="api",
        endpoint="https://data.detroitmi.gov/datasets/building-permits/",
        connector_module="connectors.detroit_permits",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # BUILDING — eviction / housing court
    # ══════════════════════════════════════════════════════════════════════════
    MSource(
        source_id="nyc_housing_court_filings",
        referent_type=ReferentType.BUILDING,
        attribute="eviction_filings",
        jurisdiction="NYC",
        granularity="per_filing",
        access_pattern="scrape",
        endpoint="https://iapps.courts.state.ny.us/webcivil/ecourtsMain",
        connector_module="connectors.nyc_housing_court",
    ),
    MSource(
        source_id="pa_magistrate_court",
        referent_type=ReferentType.BUILDING,
        attribute="eviction_filings",
        jurisdiction="PA",
        granularity="per_filing",
        access_pattern="scrape_per_county",
        endpoint="https://ujsportal.pacourts.us/CaseSearch",
        connector_module="connectors.pa_ujs",
        notes="PA Unified Judicial System — landlord-tenant cases at magisterial district level",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # BUILDING — Section 8 / HUD subsidy
    # ══════════════════════════════════════════════════════════════════════════
    MSource(
        source_id="hud_multifamily_contracts",
        referent_type=ReferentType.BUILDING,
        attribute="section8_project_based_status",
        jurisdiction="US",
        granularity="per_contract",
        access_pattern="file_download",
        endpoint="https://www.hud.gov/program_offices/housing/mfh/exp/mfhdiscl",
        connector_module="connectors.hud_multifamily",
        notes="Project-based Section 8 contracts only; SFR portfolios won't appear here (those use HCV)",
    ),
    MSource(
        source_id="hud_picture_subsidized_households",
        referent_type=ReferentType.GEOGRAPHIC_AREA,
        attribute="voucher_density",
        jurisdiction="US",
        granularity="census_tract_annual",
        access_pattern="file_download",
        endpoint="https://www.huduser.gov/portal/datasets/picture/yearlydata.html",
        connector_module="connectors.hud_posh",
    ),
    MSource(
        source_id="pha_foia_template",
        referent_type=ReferentType.BUILDING,
        attribute="section8_hcv_landlord_status",
        jurisdiction="US",
        granularity="per_landlord_per_PHA",
        access_pattern="foia",
        endpoint="N/A (per-PHA mailing template)",
        connector_module="connectors.pha_foia",
        latency_days=30,
        notes="Only path to HCV landlord registry. Generates a templated FOIA letter per PHA.",
    ),
    MSource(
        source_id="nyc_j51_socrata",
        referent_type=ReferentType.PARCEL,
        attribute="j51_obligation_status",
        jurisdiction="NYC",
        granularity="per_BBL",
        access_pattern="api",
        endpoint="https://data.cityofnewyork.us/resource/y7az-s7wc.json",
        connector_module="connectors.nyc_j51",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # GEOGRAPHIC_AREA — rent / market data
    # ══════════════════════════════════════════════════════════════════════════
    MSource(
        source_id="hud_fmr",
        referent_type=ReferentType.GEOGRAPHIC_AREA,
        attribute="hud_fair_market_rent",
        jurisdiction="US",
        granularity="county_or_msa_or_zip_annual",
        access_pattern="api",
        endpoint="https://www.huduser.gov/hudapi/public/fmr",
        auth_required=True,
        authority_tier=2,
        connector_module="connectors.hud_fmr",
        notes="Free API, register for token at huduser.gov/portal/dataset/fmr-api.html",
    ),
    MSource(
        source_id="hud_il",
        referent_type=ReferentType.GEOGRAPHIC_AREA,
        attribute="hud_income_limits",
        jurisdiction="US",
        granularity="county_or_msa_annual",
        access_pattern="api",
        endpoint="https://www.huduser.gov/hudapi/public/il",
        auth_required=True,
        connector_module="connectors.hud_il",
    ),
    MSource(
        source_id="census_acs_b25031",
        referent_type=ReferentType.GEOGRAPHIC_AREA,
        attribute="median_gross_rent_by_bedroom",
        jurisdiction="US",
        granularity="zip_or_tract_5yr",
        access_pattern="api",
        endpoint="https://api.census.gov/data/2022/acs/acs5",
        auth_required=True,
        authority_tier=2,
        connector_module="connectors.census_acs",
        notes="Free API key from api.census.gov; 5-year estimate; B25031 series for rent by bedroom",
    ),
    MSource(
        source_id="rentcast_api",
        referent_type=ReferentType.PARCEL,
        attribute="estimated_rent_value",
        jurisdiction="US",
        granularity="per_address",
        access_pattern="api",
        endpoint="https://api.rentcast.io/v1/avm/rent/long-term",
        auth_required=True,
        cost_per_query=0.10,
        connector_module="connectors.rentcast",
    ),
    MSource(
        source_id="streeteasy_via_search_snippet",
        referent_type=ReferentType.BUILDING,
        attribute="listed_rent",
        jurisdiction="NYC",
        granularity="per_listing",
        access_pattern="scrape_via_intermediary",
        endpoint="ddg_lite + brave_search snippets",
        connector_module="connectors.search_snippet_extractor",
        completeness=0.5,
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # GEOGRAPHIC_AREA — market metrics
    # ══════════════════════════════════════════════════════════════════════════
    MSource(
        source_id="costar_market_reports",
        referent_type=ReferentType.GEOGRAPHIC_AREA,
        attribute="market_cap_rate_and_rent_growth",
        jurisdiction="US",
        granularity="quarterly_metro",
        access_pattern="paid_subscription",
        endpoint="https://www.costar.com/",
        auth_required=True,
        completeness=0.9,
        connector_module="connectors.costar",
    ),
    MSource(
        source_id="bls_qcew",
        referent_type=ReferentType.GEOGRAPHIC_AREA,
        attribute="employment_trends",
        jurisdiction="US",
        granularity="county_quarterly",
        access_pattern="api",
        endpoint="https://data.bls.gov/cew/data/api/",
        connector_module="connectors.bls_qcew",
    ),
    MSource(
        source_id="princeton_eviction_lab",
        referent_type=ReferentType.GEOGRAPHIC_AREA,
        attribute="eviction_filing_rate",
        jurisdiction="US",
        granularity="census_tract_annual",
        access_pattern="file_download",
        endpoint="https://evictionlab.org/eviction-tracking/get-the-data/",
        connector_module="connectors.eviction_lab",
        completeness=0.7,
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # ENTITY — corporate & sponsor verification
    # ══════════════════════════════════════════════════════════════════════════
    MSource(
        source_id="state_corp_pa",
        referent_type=ReferentType.ENTITY,
        attribute="corporate_registration",
        jurisdiction="PA",
        granularity="per_entity",
        access_pattern="scrape",
        endpoint="https://file.dos.pa.gov/search/business",
        connector_module="connectors.state_corp_pa",
    ),
    MSource(
        source_id="state_corp_fl",
        referent_type=ReferentType.ENTITY,
        attribute="corporate_registration",
        jurisdiction="FL",
        granularity="per_entity",
        access_pattern="scrape",
        endpoint="https://search.sunbiz.org/Inquiry/CorporationSearch/ByName",
        connector_module="connectors.state_corp_fl",
    ),
    MSource(
        source_id="state_corp_mo",
        referent_type=ReferentType.ENTITY,
        attribute="corporate_registration",
        jurisdiction="MO",
        granularity="per_entity",
        access_pattern="scrape",
        endpoint="https://bsd.sos.mo.gov/BusinessEntity/BESearch.aspx",
        connector_module="connectors.state_corp_mo",
    ),
    MSource(
        source_id="state_corp_generic",
        referent_type=ReferentType.ENTITY,
        attribute="corporate_registration",
        jurisdiction="US_state",
        granularity="per_entity",
        access_pattern="scrape_per_state",
        endpoint="varies; see connectors/state_corp_registry.py",
        connector_module="connectors.state_corp_registry",
        notes="Multi-state aggregator; routes to state-specific scrapers",
    ),
    MSource(
        source_id="opencorporates",
        referent_type=ReferentType.ENTITY,
        attribute="corporate_registration",
        jurisdiction="global",
        granularity="per_entity",
        access_pattern="api",
        endpoint="https://api.opencorporates.com/v0.4/companies",
        auth_required=True,
        connector_module="connectors.opencorporates",
    ),
    MSource(
        source_id="sec_edgar",
        referent_type=ReferentType.ENTITY,
        attribute="public_filings",
        jurisdiction="US",
        granularity="per_filing",
        access_pattern="api",
        endpoint="https://efts.sec.gov/LATEST/search-index",
        authority_tier=1,
        connector_module="connectors.sec_edgar",
        notes="No auth; full-text search. For specific filer lookup use sec_edgar_company (same module, mode=company).",
    ),
    MSource(
        source_id="sec_edgar_company",
        referent_type=ReferentType.ENTITY,
        attribute="entity_filings",
        jurisdiction="US",
        granularity="per_filer",
        access_pattern="api",
        endpoint="https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany",
        authority_tier=1,
        connector_module="connectors.sec_edgar",
        notes="HTML table of filers matching a name pattern. Returns CIK, name. Pass extra={'edgar_mode':'company'}.",
    ),
    MSource(
        source_id="sec_edgar_form_d",
        referent_type=ReferentType.ENTITY,
        attribute="form_d_detail",
        jurisdiction="US",
        granularity="per_filing",
        access_pattern="api",
        endpoint="https://www.sec.gov/Archives/edgar/data/{CIK}/{ACC}/primary_doc.xml",
        authority_tier=1,
        connector_module="connectors.sec_edgar",
        notes="Parses Form D primary_doc.xml for offering amount, sold amount, investors, related persons. Needs extra={'cik':...} (from sec_edgar_company lookup or scope).",
    ),
    MSource(
        source_id="sec_iapd",
        referent_type=ReferentType.ENTITY,
        attribute="form_adv_filings",
        jurisdiction="US",
        granularity="per_filing",
        access_pattern="api",
        endpoint="https://adviserinfo.sec.gov/api/Search/AdvSearch",
        connector_module="connectors.sec_iapd",
    ),
    MSource(
        source_id="finra_brokercheck",
        referent_type=ReferentType.ENTITY,
        attribute="broker_dealer_status",
        jurisdiction="US",
        granularity="per_individual_or_firm",
        access_pattern="api",
        endpoint="https://api.brokercheck.finra.org/search/firm",
        connector_module="connectors.finra_brokercheck",
    ),
    MSource(
        source_id="ofac_sdn",
        referent_type=ReferentType.ENTITY,
        attribute="sanctions_status",
        jurisdiction="US",
        granularity="per_entity_or_person",
        access_pattern="file_download",
        endpoint="https://www.treasury.gov/ofac/downloads/sdn.csv",
        authority_tier=1,
        connector_module="connectors.ofac_sdn",
    ),
    MSource(
        source_id="irs_990",
        referent_type=ReferentType.ENTITY,
        attribute="nonprofit_filings",
        jurisdiction="US",
        granularity="per_filing_per_year",
        access_pattern="api",
        endpoint="https://projects.propublica.org/nonprofits/api/v2/",
        connector_module="connectors.propublica_nonprofit",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # ENTITY — litigation
    # ══════════════════════════════════════════════════════════════════════════
    MSource(
        source_id="pacer",
        referent_type=ReferentType.ENTITY,
        attribute="federal_litigation",
        jurisdiction="US",
        granularity="per_case",
        access_pattern="api",
        endpoint="https://pcl.uscourts.gov/pcl/index.jsf",
        auth_required=True,
        cost_per_query=0.10,
        authority_tier=1,
        connector_module="connectors.pacer",
    ),
    MSource(
        source_id="courtlistener",
        referent_type=ReferentType.ENTITY,
        attribute="federal_and_state_litigation",
        jurisdiction="US",
        granularity="per_case",
        access_pattern="api",
        endpoint="https://www.courtlistener.com/api/rest/v3/",
        auth_required=False,
        connector_module="connectors.courtlistener",
        notes="Free Law Project; broader than PACER for state cases; covers RECAP backfill",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # ENTITY — UCC / liens
    # ══════════════════════════════════════════════════════════════════════════
    MSource(
        source_id="ucc_state_filings",
        referent_type=ReferentType.ENTITY,
        attribute="ucc_security_interests",
        jurisdiction="US_state",
        granularity="per_filing",
        access_pattern="scrape_per_state",
        endpoint="varies by state SoS UCC portal",
        connector_module="connectors.ucc_state",
    ),

    # ══════════════════════════════════════════════════════════════════════════
    # CONDITIONING LAYER — discovery / crowding (NO-EDGE control, not alpha)
    # ──────────────────────────────────────────────────────────────────────────
    # These six measure how DISCOVERED/CROWDED a TICKER already is so a divergence
    # can be filtered to UN-discovered names + signal-to-price latency mapped. The
    # referent is the public-company ENTITY; entity_name carries the TICKER (FTD /
    # FINRA / StockTwits keys) or the COMPANY NAME (Wikipedia / GDELT, name-indexed).
    # Aggregated by connectors.discovery_state into attention/positioning scores +
    # a UNDISCOVERED/DISCOVERING/DISCOVERED_CROWDED regime. See CONDITIONING_LAYER_SPEC.md.
    # ══════════════════════════════════════════════════════════════════════════
    MSource(
        source_id="stocktwits",
        referent_type=ReferentType.ENTITY,
        attribute="retail_attention",
        jurisdiction="US",
        granularity="per_ticker_live",
        access_pattern="api",
        endpoint="https://api.stocktwits.com/api/2/streams/symbol/{SYM}.json",
        authority_tier=4,
        latency_days=0,
        connector_module="connectors.stocktwits",
        notes="CONDITIONING/attention. Free, no auth (needs a browser UA). Last-30-message public "
              "window: msg volume + bull/bear sentiment over the labeled subset. Lag ~live. A "
              "high-traffic name SATURATES the 30-window (msgs/day is a ceiling). 404 symbol = no "
              "retail stream = un-discovered (returned as success/0, not error).",
    ),
    MSource(
        source_id="wikipedia_pageviews",
        referent_type=ReferentType.ENTITY,
        attribute="public_attention",
        jurisdiction="global",
        granularity="per_company_daily",
        access_pattern="api",
        endpoint="https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/...",
        authority_tier=2,
        latency_days=1,
        connector_module="connectors.wikipedia_pageviews",
        notes="CONDITIONING/attention. Cleanest free source, no auth. Daily article pageviews vs the "
              "name's own ~90d baseline. Title resolved via en.wikipedia opensearch. Many micro-caps "
              "have NO article = strong un-discovered signal (success, has_article=False). Lag ~1 day. "
              "Indexed by COMPANY NAME, not ticker.",
    ),
    MSource(
        source_id="gdelt_news",
        referent_type=ReferentType.ENTITY,
        attribute="news_attention",
        jurisdiction="global",
        granularity="per_company_15min",
        access_pattern="api",
        endpoint="https://api.gdeltproject.org/api/v2/doc/doc (mode=timelinevol)",
        authority_tier=3,
        latency_days=0,
        connector_module="connectors.gdelt_news",
        notes="CONDITIONING/attention. Free, no auth. News-article VOLUME/velocity (NOT sentiment) vs "
              "own history. RATE LIMIT: GDELT throttles ~1 req/5s and 429s hard; connector backs off "
              "and returns RATE_LIMIT if still blocked (aggregator degrades to UNAVAILABLE, never "
              "fabricates). Lag ~15 min. Indexed by COMPANY NAME.",
    ),
    MSource(
        source_id="google_trends",
        referent_type=ReferentType.ENTITY,
        attribute="search_attention",
        jurisdiction="US",
        granularity="per_term_daily",
        access_pattern="api",
        endpoint="https://trends.google.com/trends/api/explore (+ widgetdata/multiline)",
        authority_tier=4,
        latency_days=1,
        connector_module="connectors.google_trends",
        notes="CONDITIONING/attention. UNOFFICIAL endpoint — Google HARD-429s datacenter/cloud IPs "
              "(and pytrends hits the same wall). Connector implements the real explore->token-> "
              "multiline flow with backoff but USUALLY returns RATE_LIMIT on a research IP -> "
              "aggregator marks the component UNAVAILABLE (never fabricates). Works opportunistically "
              "from a residential IP / proxy. Conceptually the strongest retail-attention source, "
              "operationally the weakest.",
    ),
    MSource(
        source_id="sec_ftd",
        referent_type=ReferentType.ENTITY,
        attribute="settlement_fails",
        jurisdiction="US",
        granularity="per_ticker_settlement_date",
        access_pattern="file_download",
        endpoint="https://www.sec.gov/files/data/fails-deliver-data/cnsfails{YYYYMM}{a|b}.zip",
        authority_tier=1,
        latency_days=27,
        connector_module="connectors.sec_ftd",
        notes="CONDITIONING/positioning. Free, no auth (UA header required). Reg SHO bi-monthly "
              "fails-to-deliver by symbol (pipe-delimited). An FTD spike = short-pressure/crowding "
              "tell. LAG ~2-4 WEEKS (published late); connector fetches latest file <= asof and "
              "surfaces asof_lag_days — NEVER backfilled. Keyed by TICKER.",
    ),
    MSource(
        source_id="finra_short_interest",
        referent_type=ReferentType.ENTITY,
        attribute="short_interest",
        jurisdiction="US",
        granularity="per_ticker_bimonthly",
        access_pattern="api",
        endpoint="https://api.finra.org/data/group/otcMarket/name/consolidatedShortInterest",
        authority_tier=1,
        latency_days=14,
        connector_module="connectors.finra_short_interest",
        notes="CONDITIONING/positioning. Free, no auth (POST query API). Bi-monthly consolidated "
              "short position qty + avg-daily-volume + DAYS-TO-COVER + change. The most direct "
              "'how crowded is the short already' gauge. GAP: feed has NO float/shares-outstanding, "
              "so short-interest %-of-float needs a caller-supplied float (Phase 2 joins SEC shares); "
              "days_to_cover is the native crowding proxy. Lag ~1-2wk, surfaced not backfilled. TICKER-keyed.",
    ),
    # ── Phase 2: INSTITUTIONAL crowding channel ──────────────────────────────
    MSource(
        source_id="options_positioning",
        referent_type=ReferentType.ENTITY,
        attribute="options_positioning",
        jurisdiction="US",
        granularity="per_ticker_live",
        access_pattern="api",
        endpoint="IBKR/TWS reqSecDefOptParams+reqMktData(modelGreeks,OI) [127.0.0.1:7496]",
        authority_tier=1,
        latency_days=0,
        connector_module="connectors.options_positioning",
        notes="CONDITIONING/INSTITUTIONAL. The most direct read on whether the STREET has priced a "
              "risk: 25-delta risk-reversal (put IV - call IV = the crowding/fear signature) + ATM IV "
              "+ total put/call OI. Elevated put skew + deep OI = institutionally priced. Per-strike "
              "needs the live TWS API socket; degrades to IBKR-MCP UNDERLYING-level (annual IV, "
              "IV-pctile-of-52wk, option volume) when TWS down — flagged underlying_level, skew "
              "UNAVAILABLE, never fabricated. TICKER-keyed.",
    ),
    MSource(
        source_id="analyst_coverage",
        referent_type=ReferentType.ENTITY,
        attribute="analyst_coverage",
        jurisdiction="US",
        granularity="per_ticker_daily",
        access_pattern="api",
        endpoint="yfinance / Yahoo Finance analyst aggregates",
        authority_tier=2,
        latency_days=1,
        connector_module="connectors.analyst_coverage",
        notes="CONDITIONING/INSTITUTIONAL. Sell-side coverage density = cheapest 'is this name "
              "institutionally WATCHED' proxy. n_analysts + recommendation mean/trend + consensus PT "
              "upside + QoQ revision direction + market_cap (also the cap-tier source). Free (Yahoo). "
              "Falls back to a cap-tier+listing-age PROXY when no Yahoo analyst record, flagged proxy=True. "
              "TICKER-keyed.",
    ),
    MSource(
        source_id="thirteenf_diff",
        referent_type=ReferentType.ENTITY,
        attribute="institutional_ownership_change",
        jurisdiction="US",
        granularity="per_cusip_quarterly",
        access_pattern="api",
        endpoint="https://efts.sec.gov/LATEST/search-index (13F-HR full-text search)",
        authority_tier=1,
        latency_days=90,
        connector_module="connectors.thirteenf_diff",
        notes="CONDITIONING/INSTITUTIONAL. QoQ change in 13F holder BREADTH (count of distinct 13F-HR "
              "filers reporting the CUSIP) = smart-money positioning direction (adding vs trimming). "
              "TIER-1 VERIFIED: exact filer count via EDGAR FTS, free. TIER-2 UNVERIFIABLE: aggregate "
              "SHARE count needs parsing every info table (10k+ for a widely-held name) — only a flagged "
              "SAMPLE is computed, never extrapolated. Needs extra.cusip (FTS keys on CUSIP). Lag "
              "45-135d (13F filed up to 45d after quarter-end). CUSIP-keyed.",
    ),
]


def index_sources(sources: list[MSource]) -> dict[tuple[ReferentType, str], list[MSource]]:
    idx: dict[tuple[ReferentType, str], list[MSource]] = {}
    for s in sources:
        key = (s.referent_type, s.attribute)
        idx.setdefault(key, []).append(s)
    return idx


REAL_ESTATE_SOURCES_INDEX = index_sources(REAL_ESTATE_SOURCES)


# ─────────────────────────────────────────────────────────────────────────────
# Ring 1 — attribute-alias reconciliation
# ─────────────────────────────────────────────────────────────────────────────
# The R/f/M LLM proposes referent_attributes in free text. Dispatch is an EXACT
# lookup against the atlas keys, so the agent's correct intent ("osha_inspections")
# silently evaporates when its label doesn't equal the atlas key
# ("industrial_facility_presence"). This map reconciles agent vocabulary to
# canonical atlas attributes so a synonym can no longer produce a silent skip.
# Add an entry here whenever a DD run shows the agent emitting a sensible label
# the atlas didn't recognize.
ATTRIBUTE_ALIASES: dict[str, str] = {
    # OSHA / industrial-facility existence
    "osha_inspections": "industrial_facility_presence",
    "osha_establishment": "industrial_facility_presence",
    "osha": "industrial_facility_presence",
    "factory_presence": "industrial_facility_presence",
    "manufacturing_facility": "industrial_facility_presence",
    "industrial_facility": "industrial_facility_presence",
    "plant_presence": "industrial_facility_presence",
    # operating-location / storefront roster (auto-dispatch restaurant_ratings)
    "operating_locations": "operating_location_status",
    "operating_units": "operating_location_status",
    "open_units": "operating_location_status",
    "open_locations": "operating_location_status",
    "store_locations": "operating_location_status",
    "restaurant_locations": "operating_location_status",
    "unit_roster": "operating_location_status",
    "store_roster": "operating_location_status",
    "storefront_status": "operating_location_status",
    # undisclosed customer concentration / counterparty identity (auto-dispatch customer_id)
    "top_customer": "customer_concentration",
    "largest_customer": "customer_concentration",
    "customer_mix": "customer_concentration",
    "counterparty_identity": "customer_concentration",
    "anchor_customer": "customer_concentration",
    "whale_identity": "customer_concentration",
    "customer_dependence": "customer_concentration",
    # capacity/plant ramp -> utilization (auto-dispatch hiring_velocity as the leading proxy)
    "workforce_ramp": "capacity_ramp",
    "hiring_velocity": "capacity_ramp",
    "plant_ramp": "capacity_ramp",
    "facility_utilization": "capacity_ramp",
    "new_capacity": "capacity_ramp",
    "capacity_buildout": "capacity_ramp",
    "ramp_to_utilization": "capacity_ramp",
    # booking/appointment slot scarcity -> utilization nowcast (auto-dispatch scheduler_exhaust)
    "booking_availability": "appointment_availability",
    "slot_availability": "appointment_availability",
    "appointment_backlog": "appointment_availability",
    "booking_horizon": "appointment_availability",
    "reservation_availability": "appointment_availability",
    "appointment_wait_time": "appointment_availability",
    "wait_times": "appointment_availability",
    "booking_lead_time": "appointment_availability",
    "same_day_availability": "appointment_availability",
    "scheduler_exhaust": "appointment_availability",
    # litigation / principal background (auto-dispatch litigation_screen)
    "litigation": "litigation_history",
    "lawsuits": "litigation_history",
    "legal_history": "litigation_history",
    "court_records": "litigation_history",
    "background_check": "background",
    "principal_history": "principal_background",
    "operator_history": "operator_record",
    "management_history": "management_team",
    # corporate registry
    "corporate_registry": "corporate_registration",
    "company_registration": "corporate_registration",
    "secretary_of_state": "corporate_registration",
    # SEC
    "sec_form_d": "form_d_detail",
    "form_d": "form_d_detail",
    "sec_filings": "public_filings",
    # government / defense revenue (-> government_contracts; primary = usaspending)
    "government_revenue": "government_contracts",
    "gov_revenue": "government_contracts",
    "federal_contracts": "government_contracts",
    "federal_procurement": "government_contracts",
    "defense_contracts": "government_contracts",
    "defense_revenue": "government_contracts",
    "government_customer": "government_contracts",
    "defense_and_intelligence_revenue": "government_contracts",
    # patents
    "patents": "patent_filings",
    "patent": "patent_filings",
    # satellite emissions ground-truth (-> environmental_status, co-dispatches w/ EPA)
    "methane_emissions": "environmental_status",
    "methane_plume": "environmental_status",
    "satellite_emissions": "environmental_status",
    "emissions_verification": "environmental_status",
    "ghg_emissions": "environmental_status",
    "super_emitter": "environmental_status",
    "carbon_mapper": "environmental_status",
    "environmental_violations": "environmental_status",
    # satellite optical buildout / construction progress (-> construction_activity)
    "buildout": "construction_activity",
    "buildout_progress": "construction_activity",
    "construction_progress": "construction_activity",
    "site_development": "construction_activity",
    "development_progress": "construction_activity",
    "absorption_progress": "construction_activity",
    "facility_construction": "construction_activity",
    "satellite_imagery": "construction_activity",
    # crop condition / yield (-> crop_condition)
    "crop_yield": "crop_condition",
    "crop_health": "crop_condition",
    "ndvi": "crop_condition",
    "harvest": "crop_condition",
    "agricultural_output": "crop_condition",
    "growing_conditions": "crop_condition",
    # forest / timberland asset mark verification (-> forest_harvest_rate)
    "forest_mark": "forest_harvest_rate",
    "forest_valuation": "forest_harvest_rate",
    "forest_assets": "forest_harvest_rate",
    "timberland": "forest_harvest_rate",
    "timber_assets": "forest_harvest_rate",
    "biological_assets": "forest_harvest_rate",
    "forest_health": "forest_harvest_rate",
    "harvest_rate": "forest_harvest_rate",
    "harvest_intensity": "forest_harvest_rate",
    "forest_harvest": "forest_harvest_rate",
    "clearcut": "forest_harvest_rate",
    "clear_cut": "forest_harvest_rate",
    "final_fell": "forest_harvest_rate",
    "deforestation": "forest_harvest_rate",
    # petroleum storage inventory (-> petroleum_storage_inventory)
    "oil_storage": "petroleum_storage_inventory",
    "crude_inventory": "petroleum_storage_inventory",
    "tank_farm": "petroleum_storage_inventory",
    "storage_utilization": "petroleum_storage_inventory",
    "tank_inventory": "petroleum_storage_inventory",
    "petroleum_storage": "petroleum_storage_inventory",
    # permits / deeds (common pluralization drift)
    "building_permit": "building_permits",
    "permits": "building_permits",
    "deed": "deed_records",
    "deeds": "deed_records",
    # entitlement / development-approval claims (-> entitlement_record, Laserfiche WebLink)
    "entitlement_status": "entitlement_record",
    "entitlement": "entitlement_record",
    "site_plan_approval": "entitlement_record",
    "city_approved": "entitlement_record",
    "approved_massing": "entitlement_record",
    "approved_units": "entitlement_record",
    "unit_count": "entitlement_record",
    "applicant_of_record": "entitlement_record",
    "developer_of_record": "entitlement_record",
    "zoning_approval": "entitlement_record",
    "planning_application": "entitlement_record",
    "development_approval": "entitlement_record",
    # natural-hazard / insurability claims (-> natural_hazard_exposure, FEMA NRI)
    "wildfire_risk": "natural_hazard_exposure",
    "fire_risk": "natural_hazard_exposure",
    "fire_hazard": "natural_hazard_exposure",
    "flood_risk": "natural_hazard_exposure",
    "flood_zone": "natural_hazard_exposure",
    "earthquake_risk": "natural_hazard_exposure",
    "seismic_risk": "natural_hazard_exposure",
    "natural_disaster_risk": "natural_hazard_exposure",
    "disaster_risk": "natural_hazard_exposure",
    "hazard_exposure": "natural_hazard_exposure",
    "climate_risk": "natural_hazard_exposure",
    "insurance_cost": "natural_hazard_exposure",
    "insurance_availability": "natural_hazard_exposure",
    "insurability": "natural_hazard_exposure",
    "property_insurance": "natural_hazard_exposure",
}


def canonical_attribute(attribute: str) -> str:
    """Map a free-text agent attribute label to its canonical atlas key."""
    if not attribute:
        return attribute
    key = attribute.strip().lower()
    return ATTRIBUTE_ALIASES.get(key, attribute)


# ─────────────────────────────────────────────────────────────────────────────
# Ring 1 — recall-floor contract (the "brain" / APPLIES_TO validator)
# ─────────────────────────────────────────────────────────────────────────────
# Aliasing reconciles vocabulary the agent DID emit. The recall floor catches the
# opposite failure: a mandatory source the agent OMITTED. Each rule declares a
# referent feature (detected from the claim) and the source_ids that MUST be in
# the dispatch set for any referent with that feature. A pre-flight diff surfaces
# the gap loudly instead of letting it pass as "no source applies".
# A claim earns the OSHA recall floor ONLY when it is genuinely about a physical
# facility's EXISTENCE / LOCATION / permitting — not merely because the word
# "factory" appears in its subject or quote. Keying on the verification ATTRIBUTE
# (and an existence/location PREDICATE) keeps precision high: it fires on
# "operates_factory_at" / "located_at_address" claims, NOT on a factory's
# bedroom-count, margin, or a founder's bio. (Earlier token-matching bolted OSHA
# onto 46 claims incl. people; this scopes it to the 2-3 that are real.)
_FACILITY_EXISTENCE_ATTRS = frozenset({
    "industrial_facility_presence", "building_permits", "located_at_address",
    "facility_address", "code_violations", "environmental_status",
})
_FACILITY_PREDICATE_TOKENS = (
    "operates_factory", "operates_at_address", "located_at_address",
    "factory_address", "facility_address", "owns_property_at",
    "manufactures_at", "has_facility_at", "operates_plant",
)
_NON_PHYSICAL_REFERENTS = frozenset({"person", "amount", "time_period",
                                     "quantity", "intangible"})


def _looks_industrial(typed_claim) -> bool:
    """Does this claim assert a physical facility's existence/location (so OSHA
    establishment data should be consulted)? Accepts a TypedClaim (Stage 5) or
    the raw claim dict (Stage 4)."""
    tc = typed_claim
    if isinstance(tc, dict):
        rt = str(tc.get("referent_type", "")).lower()
        predicate = str(tc.get("predicate", ""))
        attrs = tc.get("referent_attributes") or []
    else:
        rt = str(getattr(getattr(tc, "referent_type", ""), "value",
                         getattr(tc, "referent_type", ""))).lower()
        claim = getattr(tc, "claim", None)
        predicate = str(getattr(claim, "predicate", "")) if claim is not None else ""
        attrs = getattr(tc, "referent_attributes", None) or []
    # Never a person / pure-number / intangible referent.
    if rt in _NON_PHYSICAL_REFERENTS:
        return False
    canon = {canonical_attribute(str(a)) for a in attrs}
    if canon & _FACILITY_EXISTENCE_ATTRS:
        return True
    pred = predicate.lower()
    return any(tok in pred for tok in _FACILITY_PREDICATE_TOKENS)


def _looks_government_revenue(typed_claim) -> bool:
    """Does this claim assert government/defense revenue or a government-customer relationship?
    If so, USASpending federal procurement MUST be consulted (primary auditable record). Keys off
    the verification ATTRIBUTE or a gov/defense-revenue predicate/object — not the word
    'government' anywhere — to keep precision high."""
    tc = typed_claim
    if isinstance(tc, dict):
        predicate = str(tc.get("predicate", "")); attrs = tc.get("referent_attributes") or []
        obj = str(tc.get("object_value", ""))
    else:
        claim = getattr(tc, "claim", None)
        predicate = str(getattr(claim, "predicate", "")) if claim is not None else ""
        attrs = getattr(tc, "referent_attributes", None) or []
        obj = str(getattr(claim, "object_value", "")) if claim is not None else ""
    if "government_contracts" in {canonical_attribute(str(a)) for a in attrs}:
        return True
    blob = (predicate + " " + obj).lower()
    return any(t in blob for t in ("government_revenue", "defense_revenue", "government_customer",
                                   "derives_revenue_from_government", "defense_and_intelligence",
                                   "percent_government", "pct_government"))


# feature_name -> (predicate detecting it, source_ids that must be dispatched)
RECALL_FLOOR_RULES: list[dict] = [
    {
        "feature": "industrial_facility",
        "applies": _looks_industrial,
        "expect_source_ids": ["osha_establishment"],
        "why": "A physical manufacturing facility should be checked against OSHA "
               "establishment records (hit = facility existence confirmed).",
    },
    {
        "feature": "government_revenue",
        "applies": _looks_government_revenue,
        "expect_source_ids": ["usaspending"],
        "why": "A government/defense-revenue claim MUST be checked against USASpending federal "
               "procurement (primary auditable record). The classified-IC (NRO/NGA) + foreign-"
               "sovereign portion is separately unverifiable and must be flagged, not assumed. "
               "(This is the PL '82% government' miss the recall floor now prevents.)",
    },
    {
        "feature": "natural_hazard_claim",
        "applies": lambda tc: _looks_hazard_shaped(tc),
        "expect_source_ids": ["fema_nri_hazard"],
        "why": "A hazard/insurability claim with a physical referent ('low disaster risk', "
               "'insurance costs stable', 'safe location') must be checked against FEMA NRI "
               "tract-level hazard scores — and hazards checked JOINTLY: optimizing away one "
               "peril silently concentrates another (CA sleeve seismic-vs-wildfire, 2026-06-10).",
    },
    {
        "feature": "entitlement_control_claim",
        "applies": lambda tc: _looks_entitlement_claim(tc),
        "expect_source_ids": ["laserfiche_weblink"],
        "why": "A development offering that claims the sponsor is DEVELOPING/OWNS a project, or "
               "that it is 'city-approved' for N units, must be checked against the primary "
               "entitlement record — the marketed sponsor/units/product routinely diverge from the "
               "city site-plan applicant/owner/count (AHC Sun Valley: applicant/owner were the "
               "master developer, not the sponsor; 30 apartments not 33 rowhouses, 2026-06-17).",
    },
    {
        "feature": "named_principal_or_operator",
        "applies": lambda tc: _looks_principal_claim(tc),
        "expect_source_ids": ["litigation_screen"],
        "why": "Any named principal / operator / sponsor / GP / founder backing a deal MUST be run "
               "through a federal-litigation background screen automatically. Material litigation "
               "(securities/fraud, RICO, investor/breach-of-fiduciary, franchisor termination, "
               "debtor-bankruptcy) is the category an operator-credential pitch hides; routine "
               "employment/ADA/wage-hour does not fire. The pull was a 'recommended next step' on "
               "PCM Hospitality and Pearlmark — it should be a DEFAULT, not an add-on (2026-06-17).",
    },
    {
        "feature": "capacity_buildout_ramp",
        "applies": lambda tc: _looks_capacity_ramp_claim(tc),
        "expect_source_ids": ["hiring_velocity"],
        "why": "A thesis that hinges on a NEW PLANT / CAPACITY RAMPING to utilization ('coming "
               "online', 'operating leverage as the new plant fills', 'commercial production 20XX', "
               "'sold out into 20XX') should be checked against a LEADING physical proxy for the "
               "ramp, ahead of the margin print. Hiring velocity (operator-wave -> taper) is the "
               "free working proxy; sentinel2_buildout covers earlier construction stage. (STVN "
               "Fishers/Latina, 2026-06-25 — after satellite-thermal was control-refuted.)",
    },
    {
        "feature": "booking_slot_utilization",
        "applies": lambda tc: _looks_booking_utilization_claim(tc),
        "expect_source_ids": ["scheduler_exhaust"],
        "why": "A claim that rests on appointment/reservation-based volume at a business with "
               "PUBLIC online booking ('record patient volumes', 'booked out for months', "
               "'same-day availability') should be checked against the issuer's own scheduler "
               "exhaust — slot scarcity over a fixed location panel is a free leading read on "
               "the volume actually showing up. CONFOUNDER: capacity-vs-demand — co-dispatch "
               "hiring_velocity as the capacity cross-check. PAPER status (DGX/LH Q2-2026 "
               "seed); treat as corroboration, not a standalone verdict, until graduated.",
    },
    {
        "feature": "undisclosed_customer_concentration",
        "applies": lambda tc: _looks_customer_concentration_claim(tc),
        "expect_source_ids": ["customer_id"],
        "why": "A thesis that DEPENDS on a concentrated customer ('top customer N% of revenue', "
               "'capacity sold out to an anchor customer') but does NOT name the customer MUST trigger "
               "a customer-identification pass — WHO the whale is (a growing customer vs a decelerating "
               "one) is the swing factor for the whole thesis. Resolve via customs-BOL shipper-alias "
               "triangulation + Bayesian ID (STVN: the constrained GLP-1 book is Lilly-anchored 93%, "
               "which de-risked the Novo-destock bear case the HOLD had hinged on, 2026-06-25).",
    },
    {
        "feature": "operating_location_roster",
        "applies": lambda tc: _looks_operating_location_roster(tc),
        "expect_source_ids": ["restaurant_ratings"],
        "why": "A deal that markets a roster of OPERATING brick-and-mortar units (restaurant / "
               "retail / clinic / franchise locations) MUST have each address verified as existing "
               "AND OPERATIONAL — a closed, relocated, or declining unit silently inflates a marketed "
               "'N operating units' count and the consolidated revenue/EBITDA struck on it. The Cheba/"
               "Evergreen 24-unit roster sat unverified until asked by hand (the by-hand pass found "
               "24/24 operating but ALSO 2 sister units excluded from the deal); this makes the "
               "per-address storefront check a DEFAULT, not an add-on (2026-06-25).",
    },
]


# Canonical attribute only. NB: raw 'unit_count'/'store_count' are already aliased to
# 'entitlement_record' (the AHC 'units approved' rule) — so this rule keys off the canonical
# 'operating_location_status' (the open-units roster vocabulary) plus the OPEN/OPERATING tokens
# below. That is the precision boundary between "units APPROVED" (entitlement) and "units OPEN"
# (operating roster) — a bare count alone does not fire restaurant_ratings.
_CAPACITY_RAMP_TOKENS = (
    "coming online", "ramping up", "ramp to full", "ramp to utilization", "new plant", "new facility",
    "capacity expansion", "capacity coming online", "utilization ramp", "operating leverage from",
    "commercial production", "plant fills", "sold out into 20", "capacity sold out", "new capacity",
    "fishers", "latina", "greenfield", "plant ramp", "scaling production", "production ramp",
)


def _looks_capacity_ramp_claim(typed_claim) -> bool:
    """Thesis hinges on a NEW PLANT / CAPACITY ramping to utilization (the margin-inflection driver).
    Keys off canonical 'capacity_ramp' attribute first, then ramp-specific tokens. Excludes
    person/time/intangible referents. Fires the hiring_velocity (+ buildout) ramp proxy."""
    tc = typed_claim
    if isinstance(tc, dict):
        rt = str(tc.get("referent_type", "")).lower()
        predicate = str(tc.get("predicate", "")); attrs = tc.get("referent_attributes") or []
        obj = str(tc.get("object_value", ""))
    else:
        rt = str(getattr(getattr(tc, "referent_type", ""), "value",
                         getattr(tc, "referent_type", ""))).lower()
        claim = getattr(tc, "claim", None)
        predicate = str(getattr(claim, "predicate", "")) if claim is not None else ""
        attrs = getattr(tc, "referent_attributes", None) or []
        obj = str(getattr(claim, "object_value", "")) if claim is not None else ""
    if "capacity_ramp" in {canonical_attribute(str(a)) for a in attrs}:
        return True
    if rt in {"person", "time_period", "intangible"}:
        return False
    blob = (predicate + " " + obj).lower()
    return any(tok in blob for tok in _CAPACITY_RAMP_TOKENS)


_BOOKING_UTILIZATION_TOKENS = (
    "days to next appointment", "appointment availability", "appointments available",
    "booking horizon", "booked out", "fully booked", "same-day appointment",
    "same-day availability", "wait time for an appointment", "reservation availability",
    "next available appointment",
)


def _looks_booking_utilization_claim(typed_claim) -> bool:
    """Claim rests on appointment/reservation-based volume or availability at a schedulable
    service business. Keys off the canonical 'appointment_availability' attribute FIRST
    (recall-floor matcher discipline: attribute+referent_type, never token spray), then a
    NARROW booking-phrase check. Entity referents only. Fires scheduler_exhaust."""
    tc = typed_claim
    if isinstance(tc, dict):
        rt = str(tc.get("referent_type", "")).lower()
        predicate = str(tc.get("predicate", "")); attrs = tc.get("referent_attributes") or []
        obj = str(tc.get("object_value", ""))
    else:
        rt = str(getattr(getattr(tc, "referent_type", ""), "value",
                         getattr(tc, "referent_type", ""))).lower()
        claim = getattr(tc, "claim", None)
        predicate = str(getattr(claim, "predicate", "")) if claim is not None else ""
        attrs = getattr(tc, "referent_attributes", None) or []
        obj = str(getattr(claim, "object_value", "")) if claim is not None else ""
    if "appointment_availability" in {canonical_attribute(str(a)) for a in attrs}:
        return True
    if rt not in {"entity", ""}:
        return False
    blob = (predicate + " " + obj).lower()
    return any(tok in blob for tok in _BOOKING_UTILIZATION_TOKENS)


_CUSTOMER_CONCENTRATION_TOKENS = (
    "top customer", "largest customer", "customer concentration", "concentrated customer",
    "anchor customer", "single customer", "two customers", "key customer", "major customer",
    "customer accounts for", "customer represents", "% of revenue from", "sold out to a customer",
    "capacity committed to", "customer-dependent", "reliance on a customer", "whale",
)


def _looks_customer_concentration_claim(typed_claim) -> bool:
    """Material customer-concentration claim where the customer is UNNAMED (top customer N% of
    revenue / anchor customer / capacity committed to a customer). Keys off the canonical
    'customer_concentration' attribute first, then concentration-specific tokens (NOT a bare
    '% of revenue', which would over-fire). Excludes person/time/intangible referents. Fires the
    customer_id whale-resolution pass."""
    tc = typed_claim
    if isinstance(tc, dict):
        rt = str(tc.get("referent_type", "")).lower()
        predicate = str(tc.get("predicate", "")); attrs = tc.get("referent_attributes") or []
        obj = str(tc.get("object_value", ""))
    else:
        rt = str(getattr(getattr(tc, "referent_type", ""), "value",
                         getattr(tc, "referent_type", ""))).lower()
        claim = getattr(tc, "claim", None)
        predicate = str(getattr(claim, "predicate", "")) if claim is not None else ""
        attrs = getattr(tc, "referent_attributes", None) or []
        obj = str(getattr(claim, "object_value", "")) if claim is not None else ""
    if "customer_concentration" in {canonical_attribute(str(a)) for a in attrs}:
        return True
    if rt in {"person", "time_period", "intangible"}:
        return False
    blob = (predicate + " " + obj).lower()
    return any(tok in blob for tok in _CUSTOMER_CONCENTRATION_TOKENS)


_OPERATING_LOCATION_ATTRS = frozenset({"operating_location_status"})
_OPERATING_LOCATION_TOKENS = (
    "operating_units", "open_locations", "units_open", "open_units", "stores_open",
    "operating_locations", "restaurants_operating", "operates_units", "locations_open",
    "open_restaurants", "open_stores", "unit_count", "store_count", "units_at",
    "operates_n_units", "locations_operating",
)


def _looks_operating_location_roster(typed_claim) -> bool:
    """Does this claim assert a roster of physical OPERATING units/storefronts (restaurant, retail,
    clinic, franchise locations) — so each address should be verified as existing and OPERATIONAL?
    Keys off the verification ATTRIBUTE first (decisive regardless of how the count is typed), then a
    narrow open-units predicate/object. The attribute path fires even on AMOUNT/QUANTITY-typed unit
    counts; the looser token path still excludes person/time/intangible referents. (Cheba 24-unit
    roster, 2026-06-25.)"""
    tc = typed_claim
    if isinstance(tc, dict):
        rt = str(tc.get("referent_type", "")).lower()
        predicate = str(tc.get("predicate", "")); attrs = tc.get("referent_attributes") or []
        obj = str(tc.get("object_value", ""))
    else:
        rt = str(getattr(getattr(tc, "referent_type", ""), "value",
                         getattr(tc, "referent_type", ""))).lower()
        claim = getattr(tc, "claim", None)
        predicate = str(getattr(claim, "predicate", "")) if claim is not None else ""
        attrs = getattr(tc, "referent_attributes", None) or []
        obj = str(getattr(claim, "object_value", "")) if claim is not None else ""
    canon = {canonical_attribute(str(a)) for a in attrs}
    if canon & _OPERATING_LOCATION_ATTRS:
        return True  # attribute is decisive — a unit-count/roster claim, however typed
    if rt in {"person", "time_period", "intangible"}:
        return False
    blob = (predicate + " " + obj).lower()
    return any(tok in blob for tok in _OPERATING_LOCATION_TOKENS)


def _looks_principal_claim(typed_claim) -> bool:
    """Is this claim about a deal PRINCIPAL/operator/sponsor/GP/founder, or their record/background?
    Keys off the verification ATTRIBUTE first, then a role predicate/object — kept narrow so it fires
    on operator-credential claims, not every incidental person/company mention."""
    tc = typed_claim
    if isinstance(tc, dict):
        predicate = str(tc.get("predicate", "")); attrs = tc.get("referent_attributes") or []
        obj = str(tc.get("object_value", "")); rtype = str(tc.get("referent_type", ""))
    else:
        claim = getattr(tc, "claim", None)
        predicate = str(getattr(claim, "predicate", "")) if claim is not None else ""
        attrs = getattr(tc, "referent_attributes", None) or []
        obj = str(getattr(claim, "object_value", "")) if claim is not None else ""
        rtype = str(getattr(tc, "referent_type", ""))
    canon = {canonical_attribute(str(a)) for a in attrs}
    if canon & {"litigation_history", "background", "track_record", "principal_background",
                "operator_record", "management_team", "disciplinary_history"}:
        return True
    blob = (predicate + " " + obj).lower()
    role = ("founder", "co-founder", "cofounder", "operator", "operating partner", "sponsor",
            "managing partner", "general partner", "managing principal", " gp ", "principal",
            "led the", "built the", "skin in the game", "track record", "ceo", "managing member")
    # fire only when a PERSON/ENTITY referent is cast in a principal/operator role
    return rtype in ("person", "entity") and any(t in blob for t in role)


def _looks_entitlement_claim(tc) -> bool:
    """Development-control / entitlement-shaped claim: keyed off the canonical attribute first
    (recall-floor matcher discipline), then a narrow predicate/object phrase check."""
    if isinstance(tc, dict):
        predicate = str(tc.get("predicate", "")); attrs = tc.get("referent_attributes") or []
        obj = str(tc.get("object_value", ""))
    else:
        claim = getattr(tc, "claim", None)
        predicate = str(getattr(claim, "predicate", "")) if claim is not None else ""
        attrs = getattr(tc, "referent_attributes", None) or []
        obj = str(getattr(claim, "object_value", "")) if claim is not None else ""
    if "entitlement_record" in {canonical_attribute(str(a)) for a in attrs}:
        return True
    blob = (predicate + " " + obj).lower()
    return any(t in blob for t in ("is_developing", "developing", "we are developing",
                                   "city approved", "city-approved", "approved massing",
                                   "entitled", "entitlement", "site plan approv", "approved for",
                                   "units approved", "approved units"))


def _looks_hazard_shaped(tc) -> bool:
    """Hazard/insurability-shaped claim: keyed off the canonical verification attribute first
    (per the recall-floor matcher discipline), then a narrow predicate/object phrase check."""
    if isinstance(tc, dict):
        predicate = str(tc.get("predicate", "")); attrs = tc.get("referent_attributes") or []
        obj = str(tc.get("object_value", ""))
    else:
        claim = getattr(tc, "claim", None)
        predicate = str(getattr(claim, "predicate", "")) if claim is not None else ""
        attrs = getattr(tc, "referent_attributes", None) or []
        obj = str(getattr(claim, "object_value", "")) if claim is not None else ""
    if "natural_hazard_exposure" in {canonical_attribute(str(a)) for a in attrs}:
        return True
    blob = (predicate + " " + obj).lower()
    return any(t in blob for t in ("wildfire", "fire hazard", "flood zone", "flood risk",
                                   "natural disaster", "disaster risk", "seismic risk",
                                   "earthquake risk", "insurance cost", "insurance availability",
                                   "uninsurable", "insurability"))


def recall_floor_gaps(typed_claim, selected_source_ids: list[str]) -> list[dict]:
    """Return the recall-floor rules that APPLY to this claim but whose expected
    source_ids are absent from the selected dispatch set. Empty == no gap."""
    selected = set(selected_source_ids or [])
    gaps = []
    for rule in RECALL_FLOOR_RULES:
        try:
            applies = rule["applies"](typed_claim)
        except Exception:
            applies = False
        if not applies:
            continue
        missing = [sid for sid in rule["expect_source_ids"] if sid not in selected]
        if missing:
            gaps.append({
                "feature": rule["feature"],
                "missing_source_ids": missing,
                "why": rule["why"],
            })
    return gaps


def find_sources(
    referent_type: ReferentType,
    attribute: str,
    jurisdiction: str | None = None,
) -> list[MSource]:
    """Find applicable M sources for a (referent_type, attribute) pair.

    Jurisdiction matching: a source whose jurisdiction is None (US-wide) always
    matches; a state-scoped source matches when its jurisdiction string is a
    suffix of the requested jurisdiction (e.g. "PA" matches "Allegheny_County_PA").
    """
    attribute = canonical_attribute(attribute)
    candidates = REAL_ESTATE_SOURCES_INDEX.get((referent_type, attribute), [])
    if jurisdiction is None:
        return candidates
    out = []
    for s in candidates:
        if s.jurisdiction is None:
            out.append(s)
        elif s.jurisdiction in ("US", "global"):
            out.append(s)
        elif s.jurisdiction == jurisdiction:
            out.append(s)
        elif jurisdiction.endswith(s.jurisdiction):
            out.append(s)
        elif s.jurisdiction.endswith(jurisdiction):
            out.append(s)
    return out


_SOURCE_BY_ID = {s.source_id: s for s in REAL_ESTATE_SOURCES}


def source_by_id(source_id: str) -> MSource | None:
    return _SOURCE_BY_ID.get(source_id)


def implemented_sources() -> list[MSource]:
    """Subset of the atlas where the connector module is actually wired up."""
    import importlib
    out = []
    for s in REAL_ESTATE_SOURCES:
        if s.connector_module is None:
            continue
        try:
            mod_path = f"verticals.buyside_dd.{s.connector_module}"
            importlib.import_module(mod_path)
            out.append(s)
        except (ImportError, ModuleNotFoundError):
            continue
    return out
