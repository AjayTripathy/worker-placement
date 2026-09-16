"""
R-F-M taxonomy v0 — per-(domain, claim_type) registry mapping.

Each cell answers: given a focal company in DOMAIN making a CLAIM_TYPE
claim, what's the canonical f(M) registry? What's the secondary
corroboration source? What does absence mean?

The taxonomy is a STRONG DEFAULT, not a constraint. Planner subagents
emit `mapped_queries` from the canonical/secondary sources and
ADDITIONALLY emit `creative_extensions` for any non-taxonomy source
they propose. Creative extensions are logged for promotion.

Status legend:
  CANONICAL    — established f(M), planner should call this first
  PROVISIONAL  — best-guess primary; subagent encouraged to propose alternatives
  GAP          — no good source yet in catalog; creative extension explicitly invited

Source naming:
  "name.method"  — exists in m_source_catalog.CATALOG (callable)
  "name.method*" — proposed connector (not yet in catalog)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Cell:
    """One (domain, claim_type) cell of the taxonomy."""
    status: str  # CANONICAL | PROVISIONAL | GAP
    primary: list[str] = field(default_factory=list)
    secondary: list[str] = field(default_factory=list)
    proposed: list[str] = field(default_factory=list)
    expected_naics_prefix: Optional[str] = None
    absence_severity: str = "UNVERIFIABLE"  # severity when absent
    notes: str = ""


@dataclass
class Domain:
    name: str
    description: str
    naics_prefixes: list[str]
    example_tickers: list[str]
    claim_types: dict[str, Cell]


# ===== AVIATION / DRONES / EVTOL ============================================
aviation_drones = Domain(
    name="aviation_drones",
    description="Manufacturers of aircraft, drones, eVTOLs, avionics. "
                "FAA-regulated. NAICS 3364xx.",
    naics_prefixes=["3364"],
    example_tickers=["AIRO", "ACHR", "JOBY", "RCAT", "ONDS", "AVAV", "EH"],
    claim_types={
        "existence": Cell(
            status="PROVISIONAL",
            primary=["sam_entity.query_entity_by_uei"],
            secondary=["osha_establishments.query_establishments",
                       "edgar_fts.query_fulltext"],
            proposed=["faa_aircraft_registry*"],
            expected_naics_prefix="3364",
            absence_severity="MODERATE",
            notes="FAA Aircraft Registry would be CANONICAL; SAM+OSHA "
                  "are corroboration. Absence in SAM with federal claim "
                  "is real signal; OSHA absence is weak (sub-20 common).",
        ),
        "production_count": Cell(
            status="GAP",
            primary=[],
            secondary=["usaspending.query_federal_presence"],
            proposed=["faa_aircraft_registry*", "customs_bol*"],
            absence_severity="MODERATE",
            notes="Need FAA N-number registry for delivered-aircraft counts. "
                  "Customs bills of lading for export shipments. Currently "
                  "GAP — creative extensions explicitly invited.",
        ),
        "federal_customer": Cell(
            status="CANONICAL",
            primary=["usaspending.query_federal_presence"],
            secondary=["sam_entity.query_entity_by_uei",
                       "nasa_ntrs.query_ntrs"],
            absence_severity="SEVERE",
            notes="UEI-anchored federal presence. Absence + federal claim "
                  "= hard contradiction. SAM corroborates entity-level "
                  "federal eligibility. NASA NTRS adds research-output "
                  "corroboration for NASA-claimed work.",
        ),
        "commercial_customer": Cell(
            status="CANONICAL",
            primary=["megacap_namecheck.query_megacap_mentions"],
            secondary=["claim_evolution.query_claim_evolution",
                       "edgar_fts.query_fulltext"],
            absence_severity="MODERATE",
            notes="Asymmetric: presence is strong (3+ hits = recurring "
                  "partnership); absence is moderate (megacap won't "
                  "disclose sub-material).",
        ),
        "facility_scope": Cell(
            status="PROVISIONAL",
            primary=["sam_entity.query_entity_by_uei",
                     "osha_establishments.query_establishments"],
            secondary=["epa_emissions.query_facility_emissions",
                       "dol_h1b_lca.query_lca_filings",
                       "bls_qcew.query_county_naics"],
            proposed=["county_assessor*", "state_air_permits*",
                      "satellite_imagery*"],
            notes="SAM declares NAICS + address. OSHA fires only at 20+ "
                  "emp. EPA is non-informative for drone assembly (no "
                  "chemistry). Real gap below 20-emp threshold.",
        ),
        "workforce": Cell(
            status="CANONICAL",
            primary=["dol_h1b_lca.query_lca_filings"],
            secondary=["osha_establishments.query_establishments"],
            proposed=["linkedin_headcount*"],
            absence_severity="UNVERIFIABLE",
            notes="H-1B LCA covers sub-20-emp ops that OSHA Form 300A "
                  "misses. Defense primes are an exception (US-citizen-"
                  "only cleared work means LMT/NOC/RTX have ~0 LCAs).",
        ),
        "certification_milestone": Cell(
            status="GAP",
            primary=[],
            proposed=["faa_part21_holders*", "faa_part107_operators*",
                      "dod_blue_uas_list*"],
            notes="FAA Part 21 (production cert) + Part 107 (operator) + "
                  "DoD Blue UAS authorized list are all canonical for "
                  "drone certification claims. None built yet.",
        ),
        "supply_chain": Cell(
            status="GAP",
            primary=[],
            secondary=["uspto_odp.query_assignee"],
            proposed=["customs_bol*", "import_yeti*"],
            notes="Component imports = customs bills of lading. Joint "
                  "patents corroborate co-development. Customs is the "
                  "key gap.",
        ),
        "patents_ip": Cell(
            status="CANONICAL",
            primary=["uspto_odp.query_assignee"],
            secondary=["google_patents.query_assignee"],
            absence_severity="UNVERIFIABLE",
            notes="USPTO is canonical. Absence is asymmetric — patents "
                  "may be filed under subsidiary/inventor names.",
        ),
        "financial_distress": Cell(
            status="CANONICAL",
            primary=["claim_evolution.query_claim_evolution",
                     "sec_filings.list_filings_by_form"],
            secondary=["edgar_fts.query_fulltext",
                       "ucc_proxy.query_ucc_exposure"],
            proposed=["real_state_ucc*"],
            notes="Going-concern, ICFR, stock-for-services — temporal "
                  "via claim_evolution + SEC filing cadence. ucc_proxy "
                  "catches DISCLOSED secured-debt activity via SEC FTS; "
                  "for OMITTED UCC filings (a documented fraud pattern — "
                  "toxic-convertible financiers like Yorkville/GHS/"
                  "Geneva Roth file UCC-1s that microcap issuers fail "
                  "to disclose), real state UCC is needed. Real state "
                  "UCC blocked on aggregator paywall or browser-"
                  "automation infrastructure.",
        ),
    },
)


# ===== BIOTECH / PHARMA =====================================================
biotech_pharma = Domain(
    name="biotech_pharma",
    description="Drug developers, biopharma, gene/cell therapy. "
                "FDA-regulated. NAICS 32541x, 5417xx.",
    naics_prefixes=["32541", "5417"],
    example_tickers=["CDNA", "EDIT", "SAVA", "CASS", "ARDX", "IMMX"],
    claim_types={
        "existence": Cell(
            status="CANONICAL",
            primary=["sam_entity.query_entity_by_uei",
                     "openfda.query_approved_drugs"],
            secondary=["edgar_fts.query_fulltext"],
            expected_naics_prefix="3254",
            notes="openFDA returns approved-drug applications by mfr. "
                  "Clinical-stage cos have 0 approvals (expected).",
        ),
        "drug_approval": Cell(
            status="CANONICAL",
            primary=["openfda.query_approved_drugs"],
            secondary=["clinical_trials.query_by_lead_sponsor"],
            absence_severity="MODERATE",
            notes="openFDA Drugs@FDA is canonical. Claim of approved "
                  "product with 0 openFDA hits = contradiction.",
        ),
        "clinical_pipeline": Cell(
            status="CANONICAL",
            primary=["clinical_trials.query_by_lead_sponsor"],
            secondary=["edgar_fts.query_fulltext"],
            absence_severity="MODERATE",
            notes="CT.gov v2 returns trials by lead sponsor. Pipeline "
                  "claims should map 1:1 with NCT IDs.",
        ),
        "federal_customer": Cell(
            status="CANONICAL",
            primary=["usaspending.query_federal_presence"],
            secondary=["sam_entity.query_entity_by_uei"],
            proposed=["nih_reporter*"],
            notes="USAspending covers NIH/BARDA/DOD biotech awards. "
                  "NIH RePORTER would add R01/SBIR detail.",
        ),
        "facility_scope": Cell(
            status="PROVISIONAL",
            primary=["sam_entity.query_entity_by_uei"],
            secondary=["osha_establishments.query_establishments",
                       "dol_h1b_lca.query_lca_filings"],
            proposed=["fda_drug_establishment*", "fda_device_establishment*"],
            notes="FDA Drug Establishment Registration is the canonical "
                  "missing piece — every drug mfg facility registers "
                  "annually. Not yet built. H-1B LCA helps with R&D-"
                  "worksite verification.",
        ),
        "patents_ip": Cell(
            status="CANONICAL",
            primary=["uspto_odp.query_assignee"],
            secondary=["google_patents.query_assignee"],
        ),
        "workforce": Cell(
            status="CANONICAL",
            primary=["dol_h1b_lca.query_lca_filings"],
            secondary=["osha_establishments.query_establishments"],
            notes="Biotech is H-1B-dense (PhDs, postdocs). LCA filings "
                  "are high-signal for workforce-at-site claims.",
        ),
        "supply_chain": Cell(
            status="GAP",
            primary=[],
            proposed=["customs_bol*", "fda_drug_establishment*"],
            notes="API/excipient imports + foreign supplier names = "
                  "customs. FDA establishment list catches GMP-certified "
                  "foreign suppliers.",
        ),
        "future_milestone": Cell(
            status="PROVISIONAL",
            primary=["claim_evolution.query_claim_evolution",
                     "clinical_trials.query_by_lead_sponsor"],
            notes="'PDUFA expected Q2 2026' — CT.gov trial primary "
                  "completion dates + 10-K self-disclosure cadence.",
        ),
        "financial_distress": Cell(
            status="CANONICAL",
            primary=["claim_evolution.query_claim_evolution",
                     "sec_filings.list_filings_by_form"],
            secondary=["edgar_fts.query_fulltext",
                       "ucc_proxy.query_ucc_exposure"],
            proposed=["real_state_ucc*"],
        ),
    },
)


# ===== HAZWASTE / NUCLEAR / ENVIRONMENTAL ===================================
hazwaste_nuclear = Domain(
    name="hazwaste_nuclear",
    description="Hazardous waste treatment, nuclear waste, decommissioning, "
                "environmental services. NAICS 5622xx, 5629xx.",
    naics_prefixes=["5622", "5629", "5419"],
    example_tickers=["PESI", "CWST", "WCN", "ECOL", "BWXT"],
    claim_types={
        "existence": Cell(
            status="CANONICAL",
            primary=["epa_emissions.query_facility_emissions",
                     "sam_entity.query_entity_by_uei"],
            secondary=["osha_establishments.query_establishments"],
            expected_naics_prefix="5622",
            absence_severity="SEVERE",
            notes="Hazwaste IS EPA-regulated; absence in FRS is a real "
                  "contradiction. Watch subsidiary-name asymmetry.",
        ),
        "federal_customer": Cell(
            status="CANONICAL",
            primary=["usaspending.query_federal_presence"],
            secondary=["sam_entity.query_entity_by_uei"],
            proposed=["doe_osti*", "nrc_inspection_reports*"],
            absence_severity="SEVERE",
            notes="DOE West Valley / Hanford / SRS / ORNL contracts all "
                  "appear in usaspending. NRC + DOE-OSTI would add "
                  "license + research-program detail.",
        ),
        "facility_scope": Cell(
            status="CANONICAL",
            primary=["epa_emissions.query_facility_emissions",
                     "sam_entity.query_entity_by_uei"],
            secondary=["osha_establishments.query_establishments"],
            absence_severity="SEVERE",
            notes="EPA FRS + TRI + GHGRP all expected to fire for any "
                  "real hazwaste operator. Triple-absence = strong.",
        ),
        "certification_milestone": Cell(
            status="GAP",
            primary=[],
            proposed=["nrc_licenses*", "epa_permits_by_state*"],
            notes="NRC reactor licenses, EPA RCRA Part B operating "
                  "permits — domain-specific. Not in catalog yet.",
        ),
        "production_count": Cell(
            status="GAP",
            primary=[],
            secondary=["epa_emissions.query_facility_emissions"],
            proposed=["epa_rcra_manifests*", "nrc_operations*"],
            notes="Waste-volume claims need RCRA biennial reporting. "
                  "Nuclear MWh from NRC operations.",
        ),
        "patents_ip": Cell(
            status="CANONICAL",
            primary=["uspto_odp.query_assignee"],
        ),
        "financial_distress": Cell(
            status="CANONICAL",
            primary=["claim_evolution.query_claim_evolution",
                     "sec_filings.list_filings_by_form"],
            secondary=["edgar_fts.query_fulltext",
                       "ucc_proxy.query_ucc_exposure"],
            proposed=["real_state_ucc*"],
        ),
    },
)


# ===== SEMICONDUCTORS =======================================================
semiconductors = Domain(
    name="semiconductors",
    description="Chip mfg, semiconductor capital equipment, packaging, "
                "compound semis. NAICS 33441x.",
    naics_prefixes=["33441"],
    example_tickers=["KLIC", "ALMU", "ASYS", "AEHR", "MX", "INTC", "TSMC"],
    claim_types={
        "existence": Cell(
            status="CANONICAL",
            primary=["sam_entity.query_entity_by_uei",
                     "osha_establishments.query_establishments"],
            expected_naics_prefix="33441",
        ),
        "production_count": Cell(
            status="GAP",
            primary=[],
            proposed=["customs_bol*", "semi_book_to_bill*", "wafer_starts_data*"],
            notes="Wafer-starts and shipment data is private (SEMI Org). "
                  "Customs bills of lading for export volumes.",
        ),
        "federal_customer": Cell(
            status="CANONICAL",
            primary=["usaspending.query_federal_presence"],
            proposed=["chips_act_awards*"],
            notes="CHIPS Act awards have their own tracker — propose "
                  "dedicated connector for CHIPS Funding Office data.",
        ),
        "patents_ip": Cell(
            status="CANONICAL",
            primary=["uspto_odp.query_assignee"],
            notes="Semis are patent-dense; USPTO categorize=True for "
                  "tech-area depth (e.g., 'compound semi' vs 'silicon').",
        ),
        "commercial_customer": Cell(
            status="CANONICAL",
            primary=["megacap_namecheck.query_megacap_mentions"],
            secondary=["claim_evolution.query_claim_evolution"],
            notes="Semi customers are heavily megacap (Apple, NVDA, "
                  "Samsung). Megacap-namecheck is well-calibrated here.",
        ),
        "facility_scope": Cell(
            status="PROVISIONAL",
            primary=["sam_entity.query_entity_by_uei",
                     "osha_establishments.query_establishments",
                     "epa_emissions.query_facility_emissions"],
            proposed=["state_air_permits*"],
            notes="Fab operations DO trigger EPA permits (HF, photoresist, "
                  "solvents). Real semi fabs appear in FRS+TRI.",
        ),
        "workforce": Cell(
            status="CANONICAL",
            primary=["dol_h1b_lca.query_lca_filings"],
            secondary=["osha_establishments.query_establishments"],
            notes="Semi is H-1B-dense — LCA is high-signal.",
        ),
        "supply_chain": Cell(
            status="GAP",
            primary=[],
            proposed=["customs_bol*", "bis_export_licenses*"],
            notes="BIS export licenses for advanced chips (China). "
                  "Customs for component imports.",
        ),
    },
)


# ===== AUTOS / VEHICLES =====================================================
autos_vehicles = Domain(
    name="autos_vehicles",
    description="Auto/truck/EV makers + suppliers. NAICS 3361xx, 3363xx.",
    naics_prefixes=["3361", "3363"],
    example_tickers=["LCID", "RIVN", "MULN", "WKHS", "LEV", "GP"],
    claim_types={
        "existence": Cell(
            status="CANONICAL",
            primary=["nhtsa.query_manufacturer",
                     "sam_entity.query_entity_by_uei"],
            absence_severity="SEVERE",
            notes="NHTSA vPIC registers every US vehicle mfr — required "
                  "for any production claim. 'Incomplete Vehicle' = "
                  "chassis/glider only, NOT a true OEM.",
        ),
        "production_count": Cell(
            status="PROVISIONAL",
            primary=["nhtsa.query_manufacturer"],
            secondary=["edgar_fts.query_fulltext"],
            proposed=["nhtsa_vin_decoder*", "customs_bol*"],
            notes="NHTSA-registered VINs by year would be canonical. "
                  "Currently coarse — registration ≠ production.",
        ),
        "federal_customer": Cell(
            status="CANONICAL",
            primary=["usaspending.query_federal_presence"],
            proposed=["gsa_vehicle_sales*"],
            notes="GSA fleet sales is the cleanest channel for fed-fleet "
                  "claims (Workhorse-style USPS contracts).",
        ),
        "facility_scope": Cell(
            status="PROVISIONAL",
            primary=["osha_establishments.query_establishments",
                     "epa_emissions.query_facility_emissions"],
            secondary=["sam_entity.query_entity_by_uei"],
        ),
        "patents_ip": Cell(
            status="CANONICAL",
            primary=["uspto_odp.query_assignee"],
        ),
        "supply_chain": Cell(
            status="GAP",
            proposed=["customs_bol*"],
        ),
        "certification_milestone": Cell(
            status="GAP",
            proposed=["epa_vehicle_certifications*", "nhtsa_recalls*"],
            notes="EPA Vehicle Certification + NHTSA recalls are the "
                  "two canonical OEM compliance trackers.",
        ),
        "financial_distress": Cell(
            status="CANONICAL",
            primary=["claim_evolution.query_claim_evolution",
                     "sec_filings.list_filings_by_form"],
            secondary=["edgar_fts.query_fulltext",
                       "ucc_proxy.query_ucc_exposure"],
            proposed=["real_state_ucc*"],
        ),
    },
)


# ===== FINANCE / BANKING ====================================================
finance_banking = Domain(
    name="finance_banking",
    description="Banks, broker-dealers, IAs, lenders, insurers. "
                "NAICS 5221xx, 5231xx.",
    naics_prefixes=["5221", "5231", "5239", "5241"],
    example_tickers=["UPST", "AFRM", "SOFI", "LMND"],
    claim_types={
        "existence": Cell(
            status="CANONICAL",
            primary=["fdic_bankfind.query_institution",
                     "finra_brokercheck.query_firm"],
            absence_severity="SEVERE",
        ),
        "bank_partner_balance_sheet": Cell(
            status="CANONICAL",
            primary=["fdic_call_reports.query_bank_credit_history"],
            secondary=["fdic_call_reports.consumer_loan_originations"],
            notes="Resolves UPST/AFRM-style 'partner bank' claims to "
                  "actual Call Report numbers.",
        ),
        "registration": Cell(
            status="CANONICAL",
            primary=["finra_brokercheck.query_firm"],
            proposed=["sec_iapd*"],
            notes="FINRA covers BDs. SEC IAPD would add IA-only firms.",
        ),
        "federal_customer": Cell(
            status="CANONICAL",
            primary=["usaspending.query_federal_presence"],
        ),
        "patents_ip": Cell(
            status="CANONICAL",
            primary=["uspto_odp.query_assignee"],
            notes="Fintech patents (UPST credit-model claims, etc.).",
        ),
    },
)


# ===== DEFENSE / AEROSPACE PRIMES & SUBS ====================================
defense_aerospace = Domain(
    name="defense_aerospace",
    description="DoD primes, subcontractors, defense electronics, "
                "missile/munitions. NAICS 3364xx, 3345xx, 3328xx.",
    naics_prefixes=["3364", "3345", "3328", "3329"],
    example_tickers=["KTOS", "AIRO", "RCAT", "ONDS", "MRCY", "MRGN"],
    claim_types={
        "existence": Cell(
            status="CANONICAL",
            primary=["sam_entity.query_entity_by_uei"],
            secondary=["osha_establishments.query_establishments"],
            expected_naics_prefix="3364",
        ),
        "federal_customer": Cell(
            status="CANONICAL",
            primary=["usaspending.query_federal_presence"],
            secondary=["sam_entity.query_entity_by_uei"],
            absence_severity="SEVERE",
            notes="UEI-anchored over parent + subs. The strongest "
                  "registry the framework has. Pairs with "
                  "pentagon_jbook for forward-funding view.",
        ),
        "federal_program_funding_status": Cell(
            status="CANONICAL",
            primary=["pentagon_jbook.query_program_funding"],
            secondary=["usaspending.query_federal_presence",
                       "earmark_detector.query_earmark_status"],
            absence_severity="SEVERE",
            notes="Forward-view check for any claim naming a specific "
                  "Pentagon program (e.g., 'Tranche 3 Transport Layer', "
                  "AFRL/SDA programs, PE numbers like '1206410SF'). "
                  "usaspending shows REAR-VIEW awarded contracts; "
                  "pentagon_jbook shows FORWARD budget allocations; "
                  "earmark_detector tells you whether the funding is "
                  "merit-based or a politically-fragile congressional "
                  "add. Canonical YSS/IONQ catch: program zeroed in 2+ "
                  "consecutive J-Books while issuer's 10-K still "
                  "claims it as a revenue driver = SEVERE.",
        ),
        "federal_program_political_status": Cell(
            status="CANONICAL",
            primary=["earmark_detector.query_earmark_status"],
            secondary=["pentagon_jbook.query_program_funding"],
            absence_severity="MODERATE",
            notes="Distinguishes Pentagon-requested funding (durable) "
                  "from congressional adds (politically fragile when "
                  "sponsors lose power). Canonical IONQ catch: AFRL "
                  "Quantum Networking was 100% congressional add; "
                  "sponsors lost majority after Nov 2024; signal "
                  "EARMARK_SUNSET. Use whenever a federal-revenue claim "
                  "involves an agency known for earmark-secured "
                  "line items (AFRL especially).",
        ),
        "production_count": Cell(
            status="GAP",
            proposed=["dod_fpds_detail*", "customs_bol*"],
            notes="FPDS detail per-contract delivery quantities is in "
                  "usaspending but not exposed by query_federal_presence.",
        ),
        "patents_ip": Cell(
            status="CANONICAL",
            primary=["uspto_odp.query_assignee"],
        ),
        "supply_chain": Cell(
            status="GAP",
            proposed=["customs_bol*", "bis_export_licenses*",
                      "itar_registrants*"],
            notes="ITAR registration is the canonical 'defense mfr' "
                  "registry but is not public for many entries.",
        ),
        "subcontracting": Cell(
            status="PROVISIONAL",
            primary=["usaspending.query_federal_presence"],
            proposed=["fpds_subawards*"],
            notes="Subaward data is in usaspending sub-awards endpoint "
                  "but is reporting-threshold-gated and sparse.",
        ),
    },
)


# ===== MEDICAL DEVICES ======================================================
medical_devices = Domain(
    name="medical_devices",
    description="Medical device makers (Class I/II/III). NAICS 3391xx.",
    naics_prefixes=["3391"],
    example_tickers=["CDNA", "NVRO", "PEN"],
    claim_types={
        "existence": Cell(
            status="PROVISIONAL",
            primary=["sam_entity.query_entity_by_uei"],
            proposed=["fda_device_establishment*", "fda_510k*"],
            notes="FDA Device Establishment Registration is canonical; "
                  "every device mfr files annually.",
        ),
        "approval_clearance": Cell(
            status="GAP",
            primary=[],
            proposed=["fda_510k*", "fda_pma*"],
            notes="510(k)/PMA clearance is the device equivalent of "
                  "drug approval. Both are publicly searchable.",
        ),
        "facility_scope": Cell(
            status="PROVISIONAL",
            primary=["sam_entity.query_entity_by_uei",
                     "osha_establishments.query_establishments"],
            proposed=["fda_device_establishment*"],
        ),
        "federal_customer": Cell(
            status="CANONICAL",
            primary=["usaspending.query_federal_presence"],
            notes="VA hospitals are the dominant federal customer.",
        ),
        "patents_ip": Cell(
            status="CANONICAL",
            primary=["uspto_odp.query_assignee"],
        ),
    },
)


# ===== ENERGY / UTILITIES / OIL & GAS =======================================
energy_utilities = Domain(
    name="energy_utilities",
    description="Power generation, renewables, oil & gas, hydrogen, "
                "fuel cells. NAICS 2211xx, 2111xx, 4862xx.",
    naics_prefixes=["2211", "2111", "4862"],
    example_tickers=["PLUG", "BLDP", "FCEL", "CIFR", "IREN"],
    claim_types={
        "existence": Cell(
            status="CANONICAL",
            primary=["epa_emissions.query_facility_emissions",
                     "sam_entity.query_entity_by_uei"],
            secondary=["nrel_fuel.query_alt_fuel_stations"],
            expected_naics_prefix="2211",
        ),
        "production_count_generation": Cell(
            status="GAP",
            proposed=["eia_form_923*", "eia_form_860*"],
            notes="EIA Form 923 has monthly generation by plant. EIA-860 "
                  "has every generator on the grid. Canonical for any "
                  "MWh / capacity claim.",
        ),
        "fueling_network": Cell(
            status="CANONICAL",
            primary=["nrel_fuel.query_alt_fuel_stations"],
            absence_severity="MODERATE",
            notes="DOE/NREL station locator covers hydrogen + EV.",
        ),
        "facility_scope": Cell(
            status="CANONICAL",
            primary=["epa_emissions.query_facility_emissions",
                     "sam_entity.query_entity_by_uei"],
        ),
        "patents_ip": Cell(
            status="CANONICAL",
            primary=["uspto_odp.query_assignee"],
        ),
        "federal_customer": Cell(
            status="CANONICAL",
            primary=["usaspending.query_federal_presence"],
        ),
    },
)


# ===== SOFTWARE / SAAS ======================================================
software_saas = Domain(
    name="software_saas",
    description="SaaS, IT services, software dev. NAICS 5112xx, 5415xx, 5182xx.",
    naics_prefixes=["5112", "5415", "5182"],
    example_tickers=["VERI", "BBAI", "PLTR", "AI"],
    claim_types={
        "existence": Cell(
            status="PROVISIONAL",
            primary=["sam_entity.query_entity_by_uei"],
            secondary=["edgar_fts.query_fulltext"],
            notes="Software has no operational-registry equivalent. SAM "
                  "is mainly useful for federal-eligible SaaS firms.",
        ),
        "federal_customer": Cell(
            status="CANONICAL",
            primary=["usaspending.query_federal_presence"],
            proposed=["gsa_advantage*", "gwac_holders*"],
            notes="GSA Advantage IT schedules + GWAC holder lists "
                  "would refine.",
        ),
        "commercial_customer": Cell(
            status="CANONICAL",
            primary=["megacap_namecheck.query_megacap_mentions"],
            secondary=["claim_evolution.query_claim_evolution"],
        ),
        "production_count": Cell(
            status="GAP",
            proposed=["github_traffic*", "npm_pypi_downloads*",
                      "internet_archive*", "similarweb*"],
            notes="SaaS production = users / ARR / downloads. Mostly "
                  "private. GitHub commit cadence + package-manager "
                  "downloads are the best free proxies.",
        ),
        "patents_ip": Cell(
            status="CANONICAL",
            primary=["uspto_odp.query_assignee"],
        ),
        "workforce": Cell(
            status="CANONICAL",
            primary=["dol_h1b_lca.query_lca_filings"],
            secondary=["osha_establishments.query_establishments"],
            proposed=["linkedin_headcount*"],
            notes="Software is H-1B-dense; LCA is the gold source. "
                  "OSHA exempt for many software industries.",
        ),
    },
)


# ===== CONSUMER PRODUCTS ====================================================
consumer_products = Domain(
    name="consumer_products",
    description="Consumer goods, electronics, apparel, household. "
                "NAICS 334xx, 339xx, 315xx.",
    naics_prefixes=["3341", "3344", "3399", "315"],
    example_tickers=["KULR", "GPRO", "VRA"],
    claim_types={
        "existence": Cell(
            status="PROVISIONAL",
            primary=["sam_entity.query_entity_by_uei"],
            secondary=["osha_establishments.query_establishments"],
        ),
        "production_count": Cell(
            status="GAP",
            proposed=["customs_bol*", "cpsc_recalls*"],
        ),
        "facility_scope": Cell(
            status="PROVISIONAL",
            primary=["sam_entity.query_entity_by_uei",
                     "osha_establishments.query_establishments"],
        ),
        "safety_compliance": Cell(
            status="GAP",
            proposed=["cpsc_recalls*", "cpsc_certifications*"],
        ),
        "supply_chain": Cell(
            status="GAP",
            proposed=["customs_bol*"],
            notes="Consumer products are import-heavy; customs is high-"
                  "leverage for sourcing-claim verification.",
        ),
        "patents_ip": Cell(
            status="CANONICAL",
            primary=["uspto_odp.query_assignee"],
        ),
    },
)


# ===== INDUSTRIAL CHEMISTRY (NON-NUCLEAR) ===================================
industrial_chemistry = Domain(
    name="industrial_chemistry",
    description="Specialty + commodity chemicals, refrigerants, gases, "
                "battery materials. NAICS 3251xx, 3252xx.",
    naics_prefixes=["3251", "3252"],
    example_tickers=["HDSN", "NGVT", "TROX", "SCL", "IOSP", "KOP", "OEC"],
    claim_types={
        "existence": Cell(
            status="CANONICAL",
            primary=["epa_emissions.query_facility_emissions",
                     "sam_entity.query_entity_by_uei"],
            absence_severity="SEVERE",
            expected_naics_prefix="3251",
            notes="Chemistry IS EPA-regulated; absence in FRS is real "
                  "signal. Watch subsidiary-name asymmetry + tenant "
                  "co-location (PLUG@Wacker, SLI@Lanxess patterns).",
        ),
        "facility_scope": Cell(
            status="CANONICAL",
            primary=["epa_emissions.query_facility_emissions",
                     "osha_establishments.query_establishments",
                     "sam_entity.query_entity_by_uei"],
        ),
        "production_count": Cell(
            status="PROVISIONAL",
            primary=["epa_emissions.query_facility_emissions"],
            proposed=["tri_chemical_release*", "ghgrp_co2e*",
                      "customs_bol*"],
            notes="TRI release pounds + GHGRP CO2e correlate with output. "
                  "Per-chemical breakouts from TRI are useful.",
        ),
        "federal_customer": Cell(
            status="CANONICAL",
            primary=["usaspending.query_federal_presence"],
        ),
        "patents_ip": Cell(
            status="CANONICAL",
            primary=["uspto_odp.query_assignee"],
        ),
    },
)


# ===== FOOD / AGRICULTURE ===================================================
food_agriculture = Domain(
    name="food_agriculture",
    description="Food processing, agriculture, meat/poultry. NAICS 311xxx, 112xxx.",
    naics_prefixes=["311", "112"],
    example_tickers=["TSN", "PPC"],
    claim_types={
        "existence": Cell(
            status="GAP",
            primary=[],
            proposed=["usda_fsis_establishments*", "fda_food_facility*"],
            notes="USDA-FSIS for meat/poultry; FDA Food Facility "
                  "Registration for everything else. Both canonical, "
                  "neither in catalog.",
        ),
        "federal_customer": Cell(
            status="CANONICAL",
            primary=["usaspending.query_federal_presence"],
        ),
        "facility_scope": Cell(
            status="PROVISIONAL",
            primary=["sam_entity.query_entity_by_uei",
                     "osha_establishments.query_establishments"],
            proposed=["usda_fsis_establishments*"],
        ),
    },
)


# ===== REAL ESTATE / CONSTRUCTION ==========================================
real_estate_construction = Domain(
    name="real_estate_construction",
    description="REITs, construction, real estate brokerage. NAICS 236xxx, 531xxx.",
    naics_prefixes=["236", "237", "238", "531"],
    example_tickers=["LRHC", "FOR"],
    claim_types={
        "existence": Cell(
            status="PROVISIONAL",
            primary=["sam_entity.query_entity_by_uei"],
            proposed=["county_assessor*"],
        ),
        "property_holdings": Cell(
            status="GAP",
            proposed=["county_assessor*", "costar*", "loopnet*"],
            notes="Property-holdings claims need county assessor parcel "
                  "data — fragmented across thousands of jurisdictions.",
        ),
        "construction_pipeline": Cell(
            status="GAP",
            proposed=["city_building_permits*"],
        ),
        "patents_ip": Cell(
            status="CANONICAL",
            primary=["uspto_odp.query_assignee"],
            notes="Mostly UNVERIFIABLE for this domain — non-IP-intensive.",
        ),
    },
)


# ===== TRANSPORTATION / LOGISTICS ==========================================
transportation_logistics = Domain(
    name="transportation_logistics",
    description="Trucking, shipping, rail, last-mile. NAICS 484xxx, 488xxx.",
    naics_prefixes=["484", "488", "493"],
    example_tickers=["XPO", "ARCB", "USAK"],
    claim_types={
        "existence": Cell(
            status="CANONICAL",
            primary=["sam_entity.query_entity_by_uei"],
            proposed=["fmcsa_safer*"],
            notes="FMCSA SAFER has every interstate trucking company "
                  "with fleet size + safety record. Connector exists "
                  "in m_sources/fmcsa.py — verify catalog wiring.",
        ),
        "fleet_count": Cell(
            status="PROVISIONAL",
            primary=[],
            proposed=["fmcsa_safer*"],
            notes="FMCSA tracks power-unit + driver counts per carrier.",
        ),
        "federal_customer": Cell(
            status="CANONICAL",
            primary=["usaspending.query_federal_presence"],
        ),
    },
)


# ===== ALL DOMAINS REGISTRY =================================================
ALL_DOMAINS: dict[str, Domain] = {
    d.name: d for d in [
        aviation_drones,
        biotech_pharma,
        hazwaste_nuclear,
        semiconductors,
        autos_vehicles,
        finance_banking,
        defense_aerospace,
        medical_devices,
        energy_utilities,
        software_saas,
        consumer_products,
        industrial_chemistry,
        food_agriculture,
        real_estate_construction,
        transportation_logistics,
    ]
}


# ===== LOOKUP HELPERS =======================================================
def lookup(domain_name: str, claim_type: str) -> Optional[Cell]:
    """Return the Cell for (domain, claim_type) or None."""
    d = ALL_DOMAINS.get(domain_name)
    if not d:
        return None
    return d.claim_types.get(claim_type)


def domain_for_naics(naics: str) -> Optional[Domain]:
    """Resolve a NAICS code to the best-matching domain."""
    if not naics:
        return None
    best, best_len = None, 0
    for d in ALL_DOMAINS.values():
        for p in d.naics_prefixes:
            if naics.startswith(p) and len(p) > best_len:
                best, best_len = d, len(p)
    return best


def render_for_llm() -> str:
    """Render the taxonomy as a markdown spec for the LLM prompt."""
    lines = ["# R-F-M Taxonomy (v0)\n",
             "For each focal-company claim, look up the (domain, claim_type) "
             "cell below. Use the **primary** sources first; **secondary** "
             "sources corroborate. **Proposed** sources are not yet in the "
             "catalog — if a proposed source is relevant, emit a "
             "`creative_extension` entry in your plan with the rationale.\n",
             "Status: CANONICAL = use the primary first. PROVISIONAL = best "
             "guess but propose alternatives if you can. GAP = no good "
             "catalog source yet — creative extensions explicitly invited.\n"]
    for d in ALL_DOMAINS.values():
        lines.append(f"\n## `{d.name}` — {d.description}")
        lines.append(f"NAICS prefixes: {', '.join(d.naics_prefixes)}; "
                     f"example tickers: {', '.join(d.example_tickers[:5])}")
        for ct_name, cell in d.claim_types.items():
            tag = f"[{cell.status}]"
            lines.append(f"\n### {ct_name} {tag}")
            if cell.primary:
                lines.append(f"- **Primary:** {', '.join(cell.primary)}")
            if cell.secondary:
                lines.append(f"- Secondary: {', '.join(cell.secondary)}")
            if cell.proposed:
                lines.append(f"- Proposed (not in catalog): "
                             f"{', '.join(cell.proposed)}")
            if cell.absence_severity != "UNVERIFIABLE":
                lines.append(f"- Absence severity: **{cell.absence_severity}**")
            if cell.notes:
                lines.append(f"- Notes: {cell.notes}")
    lines.append("\n---\n")
    lines.append("**You are not constrained to taxonomy sources.** Emit "
                 "`creative_extensions` for ANY non-taxonomy registry, "
                 "database, or public artifact that would test the claim. "
                 "Each creative extension must include: (a) the source / "
                 "URL, (b) what observable it returns, (c) the expected "
                 "signal direction, (d) the severity if the result "
                 "contradicts the claim.")
    return "\n".join(lines)


def gap_report() -> list[tuple[str, str, str]]:
    """Return [(domain, claim_type, status)] for non-CANONICAL cells."""
    rows = []
    for d in ALL_DOMAINS.values():
        for ct_name, cell in d.claim_types.items():
            if cell.status != "CANONICAL":
                rows.append((d.name, ct_name, cell.status))
    return rows
