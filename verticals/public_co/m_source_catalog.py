"""Structured catalog of available M-sources.

Used by the LLM-driven pipeline so Claude knows what queries are available,
what each one returns, and what parameters to pass.
"""
from __future__ import annotations

from .m_sources import (
    bls_qcew,
    claim_evolution,
    clinical_trials,
    dol_h1b_lca,
    edgar_fts,
    epa_emissions,
    epa_frs,
    fdic_call_reports,
    finra_brokercheck,
    google_patents,
    iborrow,
    megacap_namecheck,
    nasa_ntrs,
    nhtsa,
    nrel_fuel,
    openfda,
    osha_establishments,
    sam_entity,
    sec_filings,
    acq_coherence,
    auditor_change_tracker,
    cybercom_budget,
    doe_budget,
    earmark_detector,
    going_concern_detector,
    ic_contracting_proxy,
    insider_vs_calendar,
    pentagon_jbook,
    revenue_concentration,
    ucc_financing_statement,
    ucc_proxy,
    usaspending,
    uspto_odp,
)


# Each entry describes one source as a tool the LLM can pick.
CATALOG = {
    "nhtsa.query_manufacturer": {
        "fn": nhtsa.query_manufacturer,
        "description": (
            "NHTSA vPIC manufacturer registry. Returns manufacturers matching the "
            "name, with vehicle types (Truck / Passenger Car / Multipurpose "
            "Passenger Vehicle / Bus / Trailer / Incomplete Vehicle / etc.) and "
            "address. 'Incomplete Vehicle' means chassis-only / glider — NOT a "
            "complete OEM. Use to verify production-vehicle claims. IMPORTANT: "
            "use the BASE BRAND name only, not the full corporate name. E.g. "
            "use 'Rivian' not 'Rivian Automotive Inc'; 'Lordstown' not 'Lordstown "
            "Motors Corp'; 'Lucid' not 'Lucid Group'. NHTSA registers under "
            "short brand names."
        ),
        "params": {"name": "string — base brand name only (e.g. 'Rivian', 'Lordstown')"},
        "good_for": ["production vehicle claims", "OEM existence", "vehicle-type registration"],
    },
    "epa_frs.query_facilities": {
        "fn": epa_frs.query_facilities,
        "description": (
            "EPA Facility Registry Service. Lists every EPA-regulated US "
            "industrial facility matching the name (substring) in the given "
            "state. Returns facility_name, address, county. Real factories that "
            "process emissions register here. Authoritative test for "
            "factory-existence claims; complements but supersedes NHTSA address."
        ),
        "params": {
            "facility_name": "string — substring of facility name",
            "state_abbr": "string — 2-letter US state code (e.g. 'IL', 'AZ')",
            "city_filter": "(optional) string — case-insensitive city filter",
        },
        "good_for": ["factory existence", "manufacturing-plant claims", "industrial site verification"],
    },
    "nrel_fuel.query_alt_fuel_stations": {
        "fn": nrel_fuel.query_alt_fuel_stations,
        "description": (
            "DOE/NREL Alternative Fueling Stations Locator. Counts stations of a "
            "given fuel type (HY=hydrogen, ELEC=EV charging) that were open or "
            "last-confirmed before the cutoff date. Use name_filter to count "
            "stations operated by a specific company."
        ),
        "params": {
            "fuel_type": "string — 'HY' for hydrogen, 'ELEC' for EV charging",
            "cutoff_date": "string — YYYY-MM-DD",
            "name_filter": "(optional) string — case-insensitive operator name",
        },
        "good_for": ["fueling/charging network claims", "infrastructure existence"],
    },
    "edgar_fts.query_fulltext": {
        "fn": edgar_fts.query_fulltext,
        "description": (
            "SEC EDGAR fulltext search. Counts filings mentioning a search term, "
            "optionally restricted to a specific CIK and form type. Use to verify "
            "counterparty disclosures: e.g. 'does Amazon's 10-K mention this "
            "company as a customer?' (cik=AMZN's CIK). Or to count external "
            "validation across all filers (no cik). IMPORTANT: search_term is "
            "treated as an EXACT PHRASE. Multi-word queries (3+ words) almost "
            "always return 0. Prefer SINGLE WORDS or 2-word phrases that are "
            "distinctive (a company name, product name, or unique number). "
            "Examples that work: 'Rivian', 'Trikafta', 'Endurance pickup'. "
            "Examples that fail: 'Lordstown Motors pre-orders Endurance' "
            "(too long). To verify counterparty corroboration, use the "
            "company's brand name + cik=<counterparty CIK>."
        ),
        "params": {
            "search_term": "string — single word or 2-word distinctive phrase",
            "cutoff_date": "string — YYYY-MM-DD",
            "cik": "(optional) string — restrict to one CIK (zero-padded 10 digits)",
            "start_date": "(optional) string — YYYY-MM-DD, default 2018-01-01",
            "forms": "(optional) string — comma-separated form types, default '10-K,10-Q,8-K,DEF 14A,20-F,40-F'",
        },
        "good_for": ["counterparty disclosure", "partner/customer corroboration", "external validation"],
    },
    "clinical_trials.query_by_lead_sponsor": {
        "fn": clinical_trials.query_by_lead_sponsor,
        "description": (
            "ClinicalTrials.gov v2 API. Lists trials where the entity is lead "
            "sponsor. Returns count, phase distribution, status, and "
            "collaborators. Use for biotech / pharma / medical-device claims "
            "about clinical programs."
        ),
        "params": {
            "sponsor_name": "string — entity name (e.g. 'Cassava Sciences', 'Vertex Pharmaceuticals')",
            "cutoff_date": "string — YYYY-MM-DD; trials starting after this are excluded",
        },
        "good_for": ["clinical program claims", "biotech pipeline", "trial collaborators"],
    },
    "openfda.query_approved_drugs": {
        "fn": openfda.query_approved_drugs,
        "description": (
            "openFDA Drugs@FDA API. Returns FDA-approved drug applications by "
            "manufacturer name. Clinical-stage companies have 0; commercial "
            "companies have multiple. Use to verify commercial-revenue / "
            "approved-product claims."
        ),
        "params": {"manufacturer_name": "string — case-insensitive substring"},
        "good_for": ["FDA approval claims", "commercial-stage pharma verification"],
    },
    "google_patents.query_assignee": {
        "fn": google_patents.query_assignee,
        "description": (
            "Google Patents JSON XHR. Returns granted patents assigned to a name "
            "with priority date before cutoff. Optionally categorize titles by "
            "keyword buckets to test claims about specific tech areas. NOTE: "
            "rate-limits aggressively in practice — usually returns 503. "
            "Prefer `uspto_odp.query_assignee` instead; this stays as a fallback."
        ),
        "params": {
            "assignee_name": "string — exact assignee name",
            "cutoff_date": "string — YYYY-MM-DD",
            "categorize": "(optional) dict — {bucket: [keyword,...]} for title categorization",
        },
        "good_for": ["IP/patent claims", "technology-area depth"],
    },
    "uspto_odp.query_assignee": {
        "fn": uspto_odp.query_assignee,
        "description": (
            "USPTO Open Data Portal patent applications search (preferred patent "
            "source — keyless Google Patents alternative is rate-limited). Returns "
            "all patent applications by an assignee filed before cutoff, plus the "
            "subset that have been granted ('Patented Case' status), with optional "
            "title-keyword categorization. Requires API key at ~/.uspto_api_key. "
            "Match is on the firstApplicantName field via a single-token query, so "
            "use the SHORT brand name (e.g. 'Velo3D' not 'Velo3D, Inc.'). The "
            "endpoint indexes APPLICATIONS, so n_total_applications is total "
            "filings and n_granted is the issued-patent subset. For the framework's "
            "patent-existence check, n_granted is the most directly comparable "
            "number to legacy 'patent count' claims."
        ),
        "params": {
            "assignee_name": "string — short brand name (no comma/Inc suffix)",
            "cutoff_date": "string — YYYY-MM-DD",
            "categorize": "(optional) dict — {bucket: [keyword,...]} for title categorization (case-insensitive)",
        },
        "good_for": ["IP/patent claims", "technology-area depth", "granted-patent counts"],
    },
    "usaspending.query_federal_presence": {
        "fn": usaspending.query_federal_presence,
        "description": (
            "PREFERRED federal-presence verifier. UEI-anchored, one-shot "
            "query: resolves name variants → recipient UEIs → aggregates "
            "contracts and grants per UEI. Returns (n_ueis_resolved, ueis, "
            "n_contracts, contracts_amount_M, n_grants, grants_amount_M, "
            "agencies, top_awards, signal). Signal tiers: "
            "INFLATION_SUSPECT (0 UEIs and 0 awards — strong absence; "
            "no federal recipient profile exists at all), "
            "SUB_MATERIAL_FEDERAL (real awards but <$5M lifetime), "
            "RECURRING_FEDERAL (>$5M lifetime federal presence). "
            "PREFERRED over query_recipient_contracts when verifying ANY "
            "federal/agency counterparty claim (DoD, NASA, DOE, VA, etc.) "
            "because UEI anchoring removes the substring-noise + name-"
            "variant gaps that destroy the bare-name search. Pass multiple "
            "name variants (parent + subsidiaries from 10-K Exhibit 21) "
            "to catch all UEIs. ABSENCE (signal=INFLATION_SUSPECT) when "
            "a federal/agency claim is made is a HARD CONTRADICTION."
        ),
        "params": {
            "name_variants": "list[str] — name variants to resolve (parent + subsidiaries; "
                              "e.g. ['Perma-Fix Environmental', 'Perma-Fix', 'Perma-Fix Northwest'])",
            "start_date":   "(optional) YYYY-MM-DD, default 2018-01-01",
            "end_date":     "(optional) YYYY-MM-DD, default 2026-12-31",
            "include_grants":"(optional) bool, default True — also query grants/cooperative agreements",
        },
        "good_for": ["federal/agency counterparty claims", "DoD program claims",
                     "NASA/DOE/VA contract verification", "subsidiary-aware federal presence",
                     "inflation-vs-real federal-relationship adjudication"],
    },
    "sam_entity.query_entity_by_uei": {
        "fn": sam_entity.query_entity_by_uei,
        "description": (
            "SAM.gov Entity Information v3 lookup by UEI. Returns the "
            "federally-registered entity's declared primary NAICS, physical "
            "address, registration status, CAGE code, business types, and "
            "exclusion flag. PAIRS WITH usaspending: usaspending tells us "
            "the entity's award history; SAM tells us how the entity "
            "describes itself to the federal government. Best for: NAICS-"
            "vs-claim adjudication (filing claims 'drone manufacturer' but "
            "SAM primary NAICS is 541990 'Other Professional Services' = "
            "scope contradiction); address-vs-facility consistency; "
            "registration-active check; exclusion-debarment check. NOTE: "
            "the v3 public tier does NOT return employee_count or "
            "annual_revenue — those require paid extracts. Free-tier rate "
            "limit ~10 req/min; key required at ~/.sam_api_key."
        ),
        "params": {
            "uei":     "string — 12-char UEI (resolve from usaspending first if needed)",
            "api_key": "(optional) override path-based key",
        },
        "good_for": ["NAICS-vs-claim scope adjudication",
                     "registered-vs-claimed address match",
                     "federal-eligibility / debarment check"],
    },
    "earmark_detector.query_earmark_status": {
        "fn": earmark_detector.query_earmark_status,
        "description": (
            "Earmark / political-add detector. Distinguishes Pentagon-"
            "requested funding (merit-based, durable) from congressional "
            "adds (politically-secured, fragile when sponsors lose power). "
            "The IONQ short thesis hinged on this: $51M FY22-24 AFRL "
            "Quantum Networking was never requested by Pentagon — entirely "
            "a congressional add by Maryland senators / Senate Approps "
            "Defense Subcommittee chair (Tester, MT). After Nov 2024 "
            "election: sponsors lost majority / Tester lost seat. FY25/FY26: "
            "earmark zeroed. Signal EARMARK_SUNSET. Pairs with "
            "pentagon_jbook (J-Book tells you a program is unfunded; "
            "earmark_detector tells you WHY it's unfunded and whether the "
            "de-funding is structural vs CR timing). Query by program_name, "
            "pe_number, or program_id (links to pentagon_jbook). CAVEATS: "
            "v1 corpus is hand-curated for IONQ-relevant earmarks; "
            "automated parsing of committee reports via "
            "scripts/ingest_committee_report.py is best-effort. Signals: "
            "EARMARK_SUNSET (SEVERE — program gone AND sponsors gone), "
            "EARMARK_AT_RISK (SEVERE — active but sponsors out), "
            "ROUTINE_EARMARK (MODERATE — active and sponsors still in "
            "power), NOT_EARMARK (PASS), AMBIGUOUS (UNVERIFIABLE)."
        ),
        "params": {
            "program_name": "(optional) string — program name or partial match",
            "pe_number":    "(optional) string — Program Element number",
            "program_id":   "(optional) string — exact program_id (links to pentagon_jbook)",
            "cutoff_date":  "(optional) string — ISO YYYY-MM-DD; consider history through this FY",
        },
        "good_for": ["congressional-add vs merit-based funding discrimination",
                     "earmark sponsor-power tracking",
                     "EARMARK_SUNSET detection (canonical IONQ catch)",
                     "forward-fragility assessment of federal-customer revenue"],
    },
    "acq_coherence.score_acquisition_coherence": {
        "fn": acq_coherence.score_acquisition_coherence,
        "description": (
            "LLM-based technology-coherence scorer for a parent company's "
            "recent acquisitions. The canonical IONQ short-thesis tell is "
            "a 'quantum computing' parent rolling up SAR satellites, atomic "
            "clocks, QKD, and a semiconductor foundry — each individually "
            "has rationale; the cluster is incoherent with the parent's "
            "stated technology thesis. Per-acquisition coherence 0-1 + "
            "aggregate signal (COHERENT_ROLLUP / MIXED / INCOHERENT_ROLLUP). "
            "Pairs with usaspending + pentagon_jbook: when a parent loses "
            "its core revenue stream AND starts rolling up incoherent "
            "businesses, that's the highest-precision fraud-pattern signal. "
            "Caveats: needs Haiku LLM access; LLM_UNAVAILABLE → UNVERIFIABLE."
        ),
        "params": {
            "parent_thesis": "string — 1-2 sentence description of parent's core thesis from 10-K Item 1 or S-1",
            "acquisitions":  "list of dicts — each {acquired_name, target_business, deal_value_usd (optional), announcement_date (optional)}",
            "cutoff_date":   "(optional) string — ISO YYYY-MM-DD; filter to acquisitions on/before this date",
        },
        "good_for": ["rollup-distraction detection",
                     "post-revenue-shock acquisition coherence",
                     "technology-vertical-divergence flag"],
    },
    "insider_vs_calendar.query_insider_sales_near_budget_events": {
        "fn": insider_vs_calendar.query_insider_sales_near_budget_events,
        "description": (
            "Form 4 insider-sale × federal-budget-calendar overlay. The "
            "canonical YSS/IONQ tell: insiders dump shares on or within "
            "days of a budget action that quietly de-funds the company's "
            "primary customer program. IONQ ex-CEO Chapman sold $37.5M the "
            "day the House passed FY25 appropriations confirming the AFRL "
            "earmark was gone. Pulls Form 4 filings from EDGAR (free, no "
            "key) and overlays against a hand-curated budget-calendar "
            "(data/_budget_calendar/events.json). Returns proximate-sale "
            "count, discretionary vs 10b5-1 distinction, unique-owner "
            "concentration. PASS contractor_name TO ENABLE VALIDATORS — the "
            "raw signal can false-positive on temporal coincidence (e.g. "
            "TDG insider sales coincident with bipartisan_budget_signed but "
            "TDG has no direct budget-line exposure; sales were actually "
            "pre-earnings). Validator 1 requires issuer to have named-"
            "program exposure in by_entity index; Validator 2 requires "
            "matched event content to reference the issuer's contractor "
            "name or program names. Both must pass for CLUSTERED_DISCRETIONARY "
            "to fire (SEVERE). Otherwise the signal downgrades to "
            "CLUSTERED_DISCRETIONARY_UNCONFIRMED (MODERATE) — likely "
            "temporal coincidence, not MNPI. Backwards-compatible: omitting "
            "contractor_name keeps the legacy non-validated signal."
        ),
        "params": {
            "cik":              "string — 10-digit padded CIK of focal company",
            "window_days":      "(optional) int — ± days around each budget event; default 14",
            "lookback_days":    "(optional) int — Form 4 scan window in days; default 365",
            "cutoff_date":      "(optional) string — ISO YYYY-MM-DD upper bound (for backtests)",
            "contractor_name":  "(optional) string — enables validators 1+2. "
                                "Pass the issuer's contractor name to gate "
                                "CLUSTERED_DISCRETIONARY against IONQ-template "
                                "false positives (e.g. TDG, CACI). Omit for "
                                "legacy behavior.",
            "entity_index_path": "(optional) string — override path to by_entity.json",
        },
        "good_for": ["insider-sale clustering around budget actions",
                     "MNPI-style timing signal — only when validators 1+2 pass",
                     "10b5-1 vs discretionary disambiguation",
                     "temporal-coincidence false-positive rejection (validators 1+2)"],
    },
    "doe_budget.query_program_funding": {
        "fn": doe_budget.query_program_funding,
        "description": (
            "DOE Office of Science Congressional Budget Justification lookup — "
            "the DOE-side counterpart to pentagon_jbook. Returns FY-by-FY "
            "funding trajectory + status for DOE programs (ASCR, BES, BER, "
            "FES, HEP, NP and their subprograms). Forward-looking signal "
            "for quantum / scientific-computing / fusion / isotope companies "
            "whose revenue comes from DOE Office of Science programs and "
            "the National Quantum Initiative Centers — NOT from DoD J-Book "
            "PEs. CAVEATS: v1 corpus is LLM-extracted from the FY 2026 DOE "
            "Office of Science budget request (78 programs, 18 QIS-relevant); "
            "NNSA / ARPA-E / EERE volumes not yet ingested. Same status "
            "enum as pentagon_jbook (FUNDED_GROWING/STEADY/SHRINKING, "
            "UNFUNDED_*, TERMINATED, NOT_FOUND)."
        ),
        "params": {
            "program_name":     "(optional) string — program name or any subprogram",
            "doe_program_code": "(optional) string — formal DOE program code if assigned",
            "parent_office":    "(optional) string — ASCR / BES / BER / FES / HEP / NP",
            "contractor_name":  "(optional) string — company name; finds programs where they appear",
            "qis_only":         "(optional) bool — restrict to QIS-relevant programs only",
            "cutoff_date":      "(optional) string — ISO YYYY-MM-DD; only consider FYs through this year",
        },
        "good_for": ["DOE forward-funding check (quantum, ASCR, BES, fusion)",
                     "National Quantum Initiative funding trajectory",
                     "Office of Science FY26 cuts vs FY25 enacted",
                     "Companion to pentagon_jbook for non-DoD federal revenue"],
    },
    "pentagon_jbook.query_program_funding": {
        "fn": pentagon_jbook.query_program_funding,
        "description": (
            "Pentagon J-Book program-funding lookup. usaspending shows "
            "REAR-VIEW awarded contracts; this is the FORWARD view — "
            "what Congress and the Pentagon have actually budgeted for "
            "specific Program Elements (PEs) in the current and future "
            "FYs. The canonical YSS / IONQ short-thesis pattern is: "
            "small-cap derives 80-96% of revenue from a named Pentagon "
            "program; that program is zeroed out for 2+ consecutive FYs "
            "in the latest J-Book; the company hasn't disclosed it. "
            "Query by program_name (e.g., 'Tranche 3 Transport Layer', "
            "'AFRL Quantum Networking'), pe_number (e.g., '1206410SF' "
            "or 'PE 1203636SF'), OR contractor_name to find programs a "
            "given company is a primary contractor on. CAVEATS: v1 "
            "corpus is hand-extracted JSON in data/_jbook_data/; only "
            "covers programs seeded for known cases — UNVERIFIABLE for "
            "anything else. Extend programs.json to add coverage; see "
            "_jbook_data/README.md. Signals: UNFUNDED_TWO_PLUS_YEARS "
            "(SEVERE — canonical YSS/IONQ catch), UNFUNDED_THIS_YEAR "
            "(MODERATE), TERMINATED (RED_FLAG), FUNDED_SHRINKING "
            "(MODERATE), FUNDED_STEADY/GROWING (PASS), NOT_FOUND "
            "(UNVERIFIABLE)."
        ),
        "params": {
            "program_name":    "(optional) string — program name or any synonym",
            "pe_number":       "(optional) string — Program Element number, with or without 'PE ' prefix",
            "contractor_name": "(optional) string — company name; returns all programs they're a primary contractor on",
            "cutoff_date":     "(optional) string — ISO YYYY-MM-DD; only consider funding through this FY (for historical backtests)",
        },
        "good_for": ["federal-program forward-funding check",
                     "customer-concentration disappearance signal",
                     "earmark-program risk (loss of political sponsor → de-funding)",
                     "Pentagon program element status tracking"],
    },
    "auditor_change_tracker.query_auditor_changes": {
        "fn": auditor_change_tracker.query_auditor_changes,
        "description": (
            "Auditor-change detector via SEC 8-K Item 4.01 parsing. "
            "Required disclosure when public co changes its certifying "
            "accountant. Auditor changes are a high-signal small-cap "
            "quality flag — Big 4 firms walk away from clients only "
            "when something is materially wrong. Detects (a) Big 4 → "
            "non-Big 4 downgrades, (b) auditor resignations / declines, "
            "(c) affirmative disclosed disagreements (not template "
            "negation language), (d) frequent turnover (>1 in lookback). "
            "Signal: CLEAN_AUDITOR_TENURE (no changes), UPGRADE_OR_LATERAL "
            "(routine change), DOWNGRADE_TO_SMALLER_FIRM (MODERATE), "
            "RESIGNATION_OR_DECLINE (SEVERE), DISAGREEMENT_DISCLOSED "
            "(RED), FREQUENT_TURNOVER (SEVERE), NOT_FOUND. The "
            "DISAGREEMENT_DISCLOSED signal uses affirmative-only "
            "regex; 'no disagreements' template language does NOT "
            "trigger."
        ),
        "params": {
            "cik":           "string — 10-digit padded CIK",
            "lookback_days": "(optional) int — scan window in days; default 1825 (5 years)",
            "cutoff_date":   "(optional) string — ISO YYYY-MM-DD upper bound",
        },
        "good_for": ["auditor-change red flag detection",
                     "small-cap audit-relationship breakdown signal",
                     "Big 4 resignation as quality flag",
                     "disagreement classification (template-noise rejected)"],
    },
    "going_concern_detector.query_going_concern": {
        "fn": going_concern_detector.query_going_concern,
        "description": (
            "Going-concern language detector via SEC 10-K/10-Q parsing. "
            "'Substantial doubt about the ability to continue as a going "
            "concern' is the SEC-required ASC 205-40 disclosure when "
            "management or auditors identify conditions that raise "
            "substantial doubt about 12-month operability. For small-cap "
            "claim verification this is the highest-value universal "
            "quality signal — if the issuer has going-concern language, "
            "the rest of the framework's claim verification is moot. "
            "Parses the most recent 10-K/10-Q for canonical phrases "
            "('substantial doubt', 'going concern', 'ability to continue "
            "as a going concern') and classifies as EXPLICIT (current-"
            "period language → SEVERE), MITIGATED (cure language nearby "
            "→ MODERATE), HISTORICAL (references prior conditions → "
            "PASS), or NO_GOING_CONCERN (clean → PASS). CAVEATS: many "
            "small-caps explicitly manage cash to AVOID going-concern "
            "language; a clean result is necessary but not sufficient "
            "for survival. Pair with cash-runway analysis."
        ),
        "params": {
            "cik":         "string — 10-digit padded CIK",
            "cutoff_date": "(optional) string — ISO YYYY-MM-DD; consider filings up to this date",
            "max_text_scan_chars": "(optional) int — cap raw text scan; default 1.5M",
        },
        "good_for": ["going-concern disclosure detection",
                     "small-cap universal quality screen",
                     "auditor-raised substantial-doubt flag",
                     "cure-language classification"],
    },
    "revenue_concentration.query_revenue_concentration": {
        "fn": revenue_concentration.query_revenue_concentration,
        "description": (
            "Revenue-concentration analyzer for federal services primes. "
            "Adjudicates 10-K concentration disclosures (top vehicle %, "
            "top task order %, IDIQ vehicle count) against industry-norm "
            "thresholds AND hand-curated peer benchmarks (BAH, SAIC, CACI, "
            "LDOS, KBR, VVX, PSN) from public 10-Ks. The canonical false-"
            "MODERATE catch: BAH '18% top vehicle / 4% top TO / 2,596 "
            "IDIQs' is operationally diversified — the LLM scorer landed "
            "it MODERATE only because it lacked an industry benchmark. "
            "Industry medians (FY24-25): top vehicle 16%, top TO 4%. With "
            "2,596 active TOs and <5% single-TO ceiling, single-vehicle % "
            "is a portfolio metric not an operational risk. CRITICAL "
            "DESIGN: customer concentration (DoD = 60-95% typical) is NOT "
            "a primary axis — DoD is a stable counterparty with statutory "
            "funding, conflating it with vehicle/TO concentration is a "
            "category error. The 10% SEC customer-disclosure rule already "
            "handles non-government customer concentration. Signals: "
            "DIVERSIFIED/TYPICAL → PASS (industry norm), CONCENTRATED → "
            "MODERATE (single vehicle ≥30% or single TO ≥10%), "
            "SEVERELY_CONCENTRATED → SEVERE (vehicle ≥50% or TO ≥20%), "
            "UNVERIFIABLE (missing inputs). Operational-diversification "
            "override: ≥1000 IDIQ TOs AND <5% top-TO downgrades CONCENTRATED "
            "→ TYPICAL because loss-of-recompete on any single TO is "
            "bounded. Extend peer set: data/_peer_benchmarks/"
            "services_prime_concentration.json."
        ),
        "params": {
            "recipient_name":     "string — company name (for echo/labeling)",
            "top_vehicle_pct":    "(optional) float — largest single IDIQ vehicle as % of revenue",
            "top_task_order_pct": "(optional) float — largest single task order as % of revenue",
            "n_idiq_vehicles":    "(optional) int — count of active IDIQ vehicles",
            "top_customer_pct":   "(optional) float — informational; not used in adjudication",
            "fiscal_year":        "(optional) int — fiscal year of the disclosure",
        },
        "good_for": ["IDIQ vehicle / task-order concentration adjudication",
                     "industry-norm benchmark + peer percentile",
                     "operational-diversification (TO count) detection",
                     "false-MODERATE catch on disclosed concentration metrics"],
    },
    "ic_contracting_proxy.query_ic_revenue_consistency": {
        "fn": ic_contracting_proxy.query_ic_revenue_consistency,
        "description": (
            "Intelligence Community revenue-disclosure consistency check. "
            "Pentagon J-Book and usaspending both have limited IC "
            "visibility (NIP/MIP are largely classified). Services primes "
            "(BAH ~16% IC, CACI ~70%, SAIC, LDOS) disclose IC revenue % in "
            "their 10-Ks, but these claims land NOT_FOUND in pentagon_jbook. "
            "This connector triangulates three signals: (1) cleared-FTE "
            "BENCHMARK — expected_IC_revenue = cleared_FTE × utilization × "
            "rev/cleared-FTE (industry default: 0.75 × $145k); (2) "
            "USAspending floor from IC-coded agencies (DIA, NGA, DCSA, "
            "DISA — NSA/NRO/CIA don't appear); (3) the disclosed claim. "
            "Verdict: CONSISTENT (claim ∈ [0.7×, 1.3×] benchmark AND "
            "visible floor ≥ 0.3× claim → PASS); SUSPICIOUSLY_HIGH "
            "(claim > 1.4× benchmark → MODERATE, possibly inflated); "
            "SUSPICIOUSLY_LOW (claim < 0.6× benchmark → PASS, likely "
            "under-disclosed not inflated); COVERAGE_INSUFFICIENT "
            "(visible floor too small to ground-truth → UNVERIFIABLE); "
            "UNVERIFIABLE (cleared_FTE not disclosed). CAVEATS: benchmark "
            "is industry-standard not company-specific; back-office-heavy "
            "or delivery-heavy mix shifts revenue-per-cleared-FTE; v2 "
            "should pull peer norms from SAIC/CACI/LDOS 10-Ks."
        ),
        "params": {
            "recipient_name":          "string — company name for usaspending lookup",
            "disclosed_ic_revenue_M":  "float — IC revenue claimed in 10-K ($M)",
            "cleared_employees":       "int — headcount with active security clearance (from 10-K)",
            "fiscal_year":             "(optional) int — FY of the disclosure",
            "utilization":             "(optional) float — billable utilization rate (default 0.75)",
            "revenue_per_cleared_FTE_K": "(optional) float — $K of annual revenue per cleared FTE (default 145)",
        },
        "good_for": ["IC-revenue disclosure plausibility check",
                     "cleared-FTE × benchmark consistency",
                     "USAspending IC-agency floor (DIA, NGA, DCSA, DISA)",
                     "claim-inflation detection on intel customer mix"],
    },
    "cybercom_budget.query_cybercom_envelope": {
        "fn": cybercom_budget.query_cybercom_envelope,
        "description": (
            "USCYBERCOM + service-cyber-SAG budget aggregator. CMF/CYBERCOM "
            "funding does not live in a single PE — it's distributed across "
            "Army Cyberspace Operations / Cybersecurity SAGs, Navy Cyberspace "
            "Activities, USMC Cyberspace Activities, SOCOM Cyberspace SAG, "
            "plus USCYBERCOM's unified appropriation (Combatant Command "
            "Acquisition Executive, post-FY24). pentagon_jbook queries by "
            "program_name or PE miss this because no single record carries "
            "'CYBERCOM' as the program. This aggregator sums the service "
            "cyber SAGs (and the USCYBERCOM line when ingested) and returns "
            "the FY-by-FY envelope + trajectory + signal. CRITICAL: OP-5 "
            "SAGs do not carry contractor attribution — to verify a "
            "specific contractor's CYBERCOM exposure, you must cross-join "
            "with usaspending awards under CYBERCOM agency codes or named "
            "cyber IDIQs (DEFENDER, JCC2, EITAAS-Cyber). This aggregator "
            "returns the budget envelope only; pass contractor_name to "
            "get the cross-reference instructions in the response. v1 "
            "covers Army (Active/NG/Reserve), Navy (Active/Reserve), USMC, "
            "SOCOM. GAPS: USCYBERCOM unified line not yet ingested; AF/SF "
            "cyber SAGs blocked by saffm.hq.af.mil DNS outage. Signals: "
            "FUNDED_GROWING/STEADY/SHRINKING (aggregate trajectory), "
            "COVERAGE_PARTIAL (< 3 services covered), NOT_FOUND."
        ),
        "params": {
            "cutoff_date":     "(optional) string — ISO YYYY-MM-DD; only consider funding through this FY",
            "contractor_name": "(optional) string — adds usaspending cross-reference note for the named contractor",
        },
        "good_for": ["CMF / CYBERCOM funding envelope",
                     "cross-service cyber budget aggregation",
                     "cyber contractor exposure verification (paired with usaspending)",
                     "Pentagon cyber budget trajectory"],
    },
    "ucc_financing_statement.query_ucc_filings": {
        "fn": ucc_financing_statement.query_ucc_filings,
        "description": (
            "State UCC-1/UCC-3 financing-statement lookup keyed on the DEBTOR "
            "(a pledging insider/affiliate), NOT the issuer CIK. Complements — "
            "does not duplicate — ucc_proxy: ucc_proxy rides SEC 8-K/10-K "
            "disclosure and sees only the ISSUER's secured debt, so it is BLIND "
            "to an insider's PERSONAL margin loan secured by a pledge of company "
            "stock (no 8-K fires on a founder's personal debt). That pledge is "
            "perfected by a UCC-1 filed at the STATE level against the debtor "
            "(the LLC or the individual). Use when a DEF 14A beneficial-ownership "
            "footnote or 10-K discloses an insider share pledge (canonical case: "
            "Caris/CAI — Halbert Family Capital, LLC pledged 25M shares). The "
            "UCC-1 DATES the perfected interest (→ bounds the original LTV via "
            "the share price that day) and names the SECURED PARTY (the lender); "
            "UCC-3 amendments adding collateral are the TOP-UP signal. The record "
            "does NOT state loan principal, so the 'pledge is underwater' claim "
            "stays CONDITIONAL — this source returns that caveat, never a "
            "manufactured severity. ACCESS: UCC is public record (no legal "
            "barrier) but state-by-state — DE has no public online index "
            "(paid UCC-11 order ~$20-75); TX SOSDirect needs a free account "
            "+ ~$1/search; CA/FL/NY/NV are free online (often bot-walled). No "
            "free national API. V1 is Tier-0 graceful degradation: it resolves "
            "the correct §9-307 filing jurisdiction and emits a structured "
            "manual-pull instruction (office, URL, cost, search terms) + the "
            "UNVERIFIABLE conditional. A commercial aggregator key at "
            "~/.ucc_api_key upgrades it to an automated multi-state pull."
        ),
        "params": {
            "debtor_name":        "string — pledging entity/person EXACTLY as on the financing statement (e.g. 'Halbert Family Capital, LLC')",
            "debtor_type":        "(optional) 'registered_org' (LLC/corp/LP) or 'individual' — drives the §9-307 jurisdiction rule",
            "state_of_formation": "(optional) 2-letter state — REQUIRED for a registered org (UCC filed in state of formation)",
            "state_of_residence": "(optional) 2-letter state — REQUIRED for an individual (UCC filed at principal residence)",
            "secured_party":      "(optional) lender name to confirm/filter",
            "as_of_date":         "(optional) ISO YYYY-MM-DD — backtest upper bound",
        },
        "good_for": ["insider/affiliate share-pledge perfection check",
                     "founder margin-loan forced-sale-channel verification",
                     "pledge top-up detection via UCC-3 amendments",
                     "lender (secured-party) identification on a stock pledge",
                     "off-balance-sheet lien that ucc_proxy/8-K disclosure misses"],
    },
    "ucc_proxy.query_ucc_exposure": {
        "fn": ucc_proxy.query_ucc_exposure,
        "description": (
            "UCC-proxy via SEC filings for lien / secured-debt exposure "
            "detection. State-by-state UCC scraping is broadly blocked "
            "(Cloudflare/Incapsula on CA/FL/NY/NC/TX/MA state UCC "
            "portals; OpenCorporates needs paid key; bulk data requires "
            "formal registration). This proxy exploits SEC disclosure "
            "mandates that mirror UCC filings: Form 8-K Item 2.03 "
            "(Creation of Direct Financial Obligation) is mandatory "
            "for any material new secured-debt by a SEC reporter, and "
            "10-K Notes are required to disclose secured debt + "
            "covenants. Approximates UCC-1 filing pace + concentration "
            "at ~80% signal coverage. CAVEATS: misses sub-material "
            "filings, private-vendor UCCs against subsidiaries, and "
            "old grandfathered filings. Signals: HIGH_LIEN_EXPOSURE "
            "(distress-credit cluster), ELEVATED, MODERATE, "
            "LOW_LIEN_EXPOSURE (no secured-debt activity detected). "
            "Best for: small-cap distress-cluster detection, "
            "receivables-financing flag, secured-debt-pace tracking."
        ),
        "params": {
            "cik":           "string — 10-digit padded CIK",
            "cutoff_date":   "string — YYYY-MM-DD upper bound",
            "window_months": "(optional) int — lookback months, default 36",
        },
        "good_for": ["lien-exposure detection via SEC proxy",
                     "secured-debt pace + concentration",
                     "distress-credit cluster detection",
                     "receivables-financing / factoring agreement flag"],
    },
    "bls_qcew.query_county_naics": {
        "fn": bls_qcew.query_county_naics,
        "description": (
            "BLS Quarterly Census of Employment and Wages (QCEW) — "
            "county+NAICS employment denominators for plausibility "
            "checks on facility-scope claims. A company claiming "
            "'500-person Aircraft Mfg facility in Maricopa County AZ' "
            "implies ~3% of county-wide NAICS-3364 employment "
            "(17,330 emp across 114 estabs in 2024). The framework's "
            "use: compute the implied % share of county-NAICS "
            "employment from the company's claim and flag if "
            "implausibly large for a small-cap (>20% share with <50 "
            "employees would be a red flag). Provide fips5 (5-digit "
            "state+county) or use bls_qcew.lookup_fips(state, county) "
            "for common counties. Free, public, no key."
        ),
        "params": {
            "fips5":        "5-digit FIPS (state+county), e.g. '04013' for Maricopa AZ",
            "year":         "int — year (most recent ~6mo behind)",
            "qtr":          "int — quarter 1-4",
            "naics_prefix": "(optional) string — NAICS prefix to filter (e.g. '3364' for aerospace)",
            "ownership":    "(optional) string — '5' (private, default), '0' (total), '1'-'3' for gov",
            "naics_digits": "(optional) int 2-6 — NAICS aggregation level (4 = '3364', 6 = '336411')",
        },
        "good_for": ["facility-scope plausibility check",
                     "county-NAICS employment denominator",
                     "claimed-headcount-vs-county-total sanity check"],
    },
    "nasa_ntrs.query_ntrs": {
        "fn": nasa_ntrs.query_ntrs,
        "description": (
            "NASA Technical Reports Server search. Returns any "
            "NASA-published citations referencing the queried entity "
            "(by title/abstract word-boundary match — same fix we "
            "applied to USAspending/OSHA/DOL). Corroborates NASA "
            "collaboration / contract claims: presence is strong "
            "(NASA published technical output mentioning the entity); "
            "absence is moderate (ITAR/EAR-restricted work may not "
            "be published). Pairs with usaspending (which shows "
            "NASA funding) and NASA TechPort (proposed; would show "
            "active funded projects)."
        ),
        "params": {
            "query":      "string — entity name (word-boundary post-filter applied)",
            "size":       "(optional) int, default 25",
            "after_year": "(optional) int — earliest published year",
            "match_mode": "(optional) 'word_boundary' (default), 'substring', or 'exact'",
        },
        "good_for": ["NASA collaboration corroboration",
                     "claimed-NASA-program verification",
                     "research-output existence check"],
    },
    "dol_h1b_lca.query_lca_filings": {
        "fn": dol_h1b_lca.query_lca_filings,
        "description": (
            "DOL Office of Foreign Labor Certification H-1B LCA "
            "disclosure data. Every H-1B Labor Condition Application "
            "is published quarterly with employer + worksite address + "
            "number of workers requested + SOC code + wage. Fills the "
            "sub-20-employee gap that OSHA Form 300A leaves: tech, "
            "biotech, semi, SaaS small-caps file H-1B LCAs at worksites "
            "even before they file 300A. Search by employer_name + "
            "optional worksite city/state/address. CALIBRATION CAVEAT: "
            "defense primes (LMT/NOC/RTX) and traditional industrial "
            "operators (refrigerant, hazwaste) have near-zero H-1B "
            "sponsorship because their work is US-citizen-only — "
            "absence is NOT informative in those domains. Strongest "
            "signal for software/saas/biotech/semi/drone workforce "
            "claims. Default match_mode='word_boundary'."
        ),
        "params": {
            "employer_name":  "(optional) string — employer-name match (word_boundary by default)",
            "fein":           "(optional) string — exact Federal EIN match",
            "naics_prefix":   "(optional) string — leading digits of NAICS",
            "city":           "(optional) string — worksite city (case-insensitive exact)",
            "state":          "(optional) string — 2-letter worksite state",
            "address_substr": "(optional) string — substring on worksite_address1",
            "soc_prefix":     "(optional) string — SOC title prefix (e.g. 'Software')",
            "only_certified": "(optional) bool, default True — exclude denied/withdrawn",
            "match_mode":     "(optional) 'word_boundary' (default), 'substring', or 'exact'",
            "max_results":    "(optional) int, default 50",
        },
        "good_for": ["workforce-at-worksite verification",
                     "claimed-headcount adjudication for tech/biotech/semi",
                     "subsidiary-name worksite discovery",
                     "operational-scope check below OSHA 300A threshold"],
    },
    "osha_establishments.query_establishments": {
        "fn": osha_establishments.query_establishments,
        "description": (
            "OSHA Form 300A Establishment Summary lookup. Returns every "
            "US establishment (with 20+ employees in covered industries) "
            "matching the filters, with annual_average_employees, NAICS, "
            "address. The non-EPA operational-scope check — catches "
            "facility-scale claims that EPA can't (drone assembly, "
            "biotech labs, electronics integration). Default match_mode "
            "is 'word_boundary' so 'AIRO' matches 'AIRO Group' but NOT "
            "'Cairo' or 'Kairos'. COVERAGE GAP: establishments with <20 "
            "employees and low-injury-rate industries are exempt from "
            "filing, so absence is NOT informative for small-cap drone/"
            "biotech/electronics companies (KLIC, KULR, ALMU all have "
            "real US ops but file no 300A). Calibrated as a corroboration "
            "source: presence at scale = strong PASS; absence is mostly "
            "UNVERIFIABLE except when the claim explicitly asserts "
            "'thousand-person facility' or 'Fortune 500 employer'."
        ),
        "params": {
            "company_name":   "(optional) string — substring/word-boundary match on establishment_name + company_name",
            "address_substr": "(optional) string — substring match on street_address",
            "city":           "(optional) string — exact city match (case-insensitive)",
            "state":          "(optional) string — 2-letter state code",
            "naics_prefix":   "(optional) string — NAICS code prefix (e.g. '3364' for aerospace)",
            "match_mode":     "(optional) 'word_boundary' (default), 'substring', or 'exact'",
            "max_results":    "(optional) int, default 50",
        },
        "good_for": ["industrial facility headcount verification",
                     "claimed-address operational-scope check",
                     "Form 300A-registered employer corroboration"],
    },
    "megacap_namecheck.query_megacap_mentions": {
        "fn": megacap_namecheck.query_megacap_mentions,
        "description": (
            "Megacap-side filing name-check for inflation detection on "
            "COMMERCIAL counterparty claims (e.g. 'we partnered with "
            "Microsoft', 'AWS deployment', 'Walmart pilot'). Searches the "
            "MEGACAP's own SEC filings (10-K/10-Q/8-K) over a 10-year "
            "window for any mention of the small-cap's name. Returns "
            "per-megacap hit counts and a 3-band signal: "
            "INFLATION_SUSPECT (0 hits across megacaps — no megacap has "
            "ever mentioned this name; strong fabrication/inflation "
            "signal), SUB_MATERIAL_RELATIONSHIP (1-2 hits — real but "
            "below ecosystem-partner cadence; AMBIGUOUS — could be a "
            "small real relationship or an alleged inflation), "
            "RECURRING_RELATIONSHIP (3+ hits — real ecosystem partner). "
            "Asymmetric from H7 (which scores small-cap-side disclosure): "
            "this scores megacap-side EARNINGS-CALL-CADENCE mentions, "
            "which catch real partnerships at materiality thresholds far "
            "below the 10-K customer-concentration table. PREFERRED over "
            "edgar_fts with cik=<megacap CIK> for COMMERCIAL counterparty "
            "verification because it queries multiple megacaps in one "
            "call and applies calibrated signal thresholds."
        ),
        "params": {
            "small_cap_name": "string — full name of the small-cap (e.g. 'Plug Power', 'Akazoo')",
            "cutoff_date":    "string — YYYY-MM-DD",
            "megacap_subset": "(optional) list[str] — subset of megacaps to query (e.g. ['Amazon','Microsoft']); "
                               "default queries ~19 common megacap counterparties",
            "window_days":    "(optional) int, default 3650 (10 years)",
            "forms":          "(optional) string, default '10-K,10-Q,8-K'",
        },
        "good_for": ["commercial megacap partnership claims",
                     "AWS / Microsoft / Walmart / Tesla / Nvidia counterparty verification",
                     "inflation-vs-real commercial-partnership adjudication"],
    },
    "usaspending.query_recipient_contracts": {
        "fn": usaspending.query_recipient_contracts,
        "description": (
            "[LEGACY — prefer usaspending.query_federal_presence for new "
            "queries.] USAspending.gov federal contract search via bare "
            "name substring. Returns (n_awards, total_amount, top_awards, "
            "agencies). The bare-name match has severe substring noise "
            "(e.g. 'Hudson Technologies' matches 67k unrelated entities; "
            "'AIRO' matches 119) and variant gaps. Kept for back-compat "
            "and for cases where the LLM has a single canonical recipient "
            "name and wants to short-circuit UEI resolution."
        ),
        "params": {
            "recipient_name":  "string — recipient brand substring (e.g. 'Kratos', 'Red Cat')",
            "start_date":      "(optional) YYYY-MM-DD, default 2020-01-01",
            "end_date":        "(optional) YYYY-MM-DD, default 2026-12-31",
            "awarding_agency": "(optional) full agency name e.g. 'Department of Defense'",
            "page_size":       "(optional) int, default 25",
        },
        "good_for": ["DoD contract verification", "federal contract claims",
                     "named program awards", "agency relationship verification"],
    },
    "usaspending.query_dod_contracts": {
        "fn": usaspending.query_dod_contracts,
        "description": (
            "Convenience wrapper: USAspending federal CONTRACT search "
            "restricted to Department of Defense as the awarding agency. "
            "Same return shape as query_recipient_contracts."
        ),
        "params": {
            "recipient_name":  "string — recipient brand substring",
            "start_date":      "(optional) YYYY-MM-DD, default 2020-01-01",
            "end_date":        "(optional) YYYY-MM-DD, default 2026-12-31",
            "page_size":       "(optional) int, default 25",
        },
        "good_for": ["DoD-only contract verification", "tactical/military program claims"],
    },
    "usaspending.query_recipient_grants": {
        "fn": usaspending.query_recipient_grants,
        "description": (
            "USAspending federal financial-assistance (GRANTS / cooperative "
            "agreements) search. Use for DARPA / OTA / SBIR / STTR claims "
            "that may not appear as contracts. Same return shape."
        ),
        "params": {
            "recipient_name": "string — recipient brand substring",
            "start_date":     "(optional) YYYY-MM-DD",
            "end_date":       "(optional) YYYY-MM-DD",
            "page_size":      "(optional) int, default 10",
        },
        "good_for": ["DARPA grants", "SBIR / STTR awards", "OTA cooperative agreements"],
    },
    "fdic_call_reports.query_bank_credit_history": {
        "fn": fdic_call_reports.query_bank_credit_history,
        "description": (
            "FDIC Call Reports — quarterly bank-level credit-portfolio data. "
            "Adjudicates non-bank lender claims (UPST, AFRM, etc.) that "
            "originate loans on bank-partner balance sheets — the bank's "
            "Call Report shows the actual portfolio size, charge-off rate, "
            "nonaccrual rate, and YoY growth. Returns last N quarters of "
            "LNCONOTH (other consumer loans), NTLNLS (net charge-offs), "
            "NCLNLS (nonaccrual loans), ASSET, NETINC, ROAQ/ROEQ, plus "
            "computed summary (charge_off_rate_pct, nonaccrual_rate_pct, "
            "LNCONOTH_yoy_pct). Use bank_name to look up by substring; "
            "use cert for direct FDIC certificate lookup. Most useful for "
            "claim-vs-cohort-credit-quality adjudication in fintech."
        ),
        "params": {
            "bank_name": "(optional) string — substring of bank name, e.g. 'Cross River Bank'",
            "cert":      "(optional) int — FDIC certificate number; specify either bank_name or cert",
            "quarters":  "(optional) int — number of recent quarters (default 8, max 40)",
            "fields":    "(optional) list[str] — override the default field set",
        },
        "good_for": [
            "fintech bank-partner credit-quality adjudication",
            "lender-cohort charge-off and nonaccrual trajectory",
            "bank-partner balance-sheet sizing",
        ],
    },
    "fdic_bankfind.query_institution": {
        "fn": fdic_call_reports.lookup_institution,
        "description": (
            "FDIC BankFind Suite institution registry. Resolves a bank name to "
            "its FDIC CERT, RSSDID, state, city, and active/inactive status. "
            "Tries exact-phrase match first, then multi-token AND, then "
            "first-token prefix. Use to verify that a named bank partner is "
            "real and active before pulling Call Report data."
        ),
        "params": {
            "name": "string — bank name or substring, e.g. 'SoFi Bank, N.A.'",
        },
        "good_for": [
            "bank-partner existence / charter verification",
            "resolving a marketing-tier bank name to its FDIC CERT",
        ],
    },
    "fdic_call_reports.consumer_loan_originations": {
        "fn": fdic_call_reports.query_multi_bank_originations,
        "description": (
            "Aggregate consumer-loan portfolio data across a list of bank "
            "partners. Adjudicates 'origination concentration' claims (e.g. "
            "UPST '83% of loans through top three lending partners' — sum of "
            "consumer-loan portfolios across the named partners is the "
            "registry-side denominator). Returns per-bank summaries plus "
            "weighted-average charge-off and nonaccrual rates across the set."
        ),
        "params": {
            "bank_names": "list[str] — bank names to look up and aggregate, e.g. ['Cross River Bank', 'FinWise Bank', 'Customers Bank']",
            "quarters":   "(optional) int — recent quarters per bank (default 4)",
        },
        "good_for": [
            "lending-partner concentration adjudication",
            "cohort-level credit-quality across multiple bank partners",
        ],
    },
    "finra_brokercheck.query_firm": {
        "fn": finra_brokercheck.query_firm,
        "description": (
            "FINRA BrokerCheck firm registration lookup. Authoritative public "
            "registry of all U.S.-registered broker-dealers and investment "
            "advisers. Adjudicates 'registered broker-dealer regulated by SEC "
            "and FINRA' claims. Returns firm CRD, SEC#, registration status "
            "(active BD / IA), and other firm names (for renamed entities)."
        ),
        "params": {
            "firm_name": "string — broker-dealer firm name, e.g. 'Capital One Securities'",
            "limit":     "(optional) int — max matches to return (default 5, max 25)",
        },
        "good_for": [
            "broker-dealer registration verification",
            "FINRA member firm CRD/SEC# resolution",
            "investment-adviser registration check",
        ],
    },
    "epa_emissions.query_facility_emissions": {
        "fn": epa_emissions.query_facility_emissions,
        "description": (
            "EPA operational-capacity test (FRS + TRI + GHGRP, with optional "
            "location audit). Probes three EPA registries: FRS (master index "
            "of every EPA-permitted facility, any program), TRI (chemicals "
            ">10-25k lb/yr), GHGRP (>25kt CO2e/yr). When the caller supplies "
            "claimed_locations=[{city,state},...], the connector also reverse-"
            "looks-up each claimed plant location and reports whether the "
            "company has an FRS-registered facility there. The strongest "
            "divergence signal — CLAIMED_LOCATION_GAP — fires when EPA "
            "knows the company elsewhere but no permitted facility exists at "
            "the marketed plant address. Use for claims about commercial "
            "scale (production volume, named manufacturing facilities, "
            "shipping at scale, gigafactory openings)."
        ),
        "params": {
            "company_name":      "string — focal company name (e.g. 'Plug Power', 'Bloom Energy')",
            "state":             "(optional) 2-letter state code to filter facilities by",
            "claimed_locations": "(optional) list of {'city': str, 'state': str} "
                                 "dicts naming plant locations the focal company "
                                 "has marketed; the connector audits each and "
                                 "reports whether the company is FRS-registered there.",
        },
        "good_for": [
            "operational-capacity testing on industrial-scale revenue claims",
            "peer comparison (in-registry vs not at similar revenue scale)",
            "reverse-lookup at named plant address ('what entity is permitted at this site')",
            "MVST/SES/PLUG/BE/FCEL-style scale-of-operations adjudication",
        ],
    },
    "claim_evolution.query_claim_evolution": {
        "fn": claim_evolution.query_claim_evolution,
        "description": (
            "Self-disclosure evolution tracking. Searches the focal company's "
            "OWN subsequent filings (10-K / 10-Q / 8-K / DEF 14A) AFTER the "
            "original claim's filing date and BEFORE the test cutoff. Use this "
            "as the materiality-correct test for claims that name mega-cap "
            "counterparties (Amazon, Microsoft, Walmart, GM, etc.) where "
            "counterparty-side disclosure is asymmetrically rare. Tests "
            "whether the focal company keeps re-disclosing the claim in "
            "subsequent filings (REAFFIRMED) or has gone silent on it "
            "(SILENT_POST_CLAIM — concerning if the claim was material)."
        ),
        "params": {
            "cik":                "10-digit padded CIK of the FOCAL company (NOT the counterparty)",
            "search_term":        "the entity, dollar amount, or term to track (e.g. 'Walmart')",
            "base_filing_date":   "ISO date of the original claim's filing — window starts day+1",
            "cutoff_date":        "ISO date upper bound on the search window",
            "forms":              "(optional) comma-separated SEC form types; default '10-K,10-Q,8-K,DEF 14A'",
        },
        "good_for": [
            "claims naming mega-cap counterparties (where Heuristic 7 is unsafe)",
            "customer-concentration evolution tracking",
            "going-concern + restatement cadence over time",
            "forward-looking marketing claims that may quietly disappear from later filings",
        ],
    },
    "iborrow.get_borrow_rate": {
        "fn": iborrow.get_borrow_rate,
        "description": (
            "Indicative IBKR daily securities-lending data via iborrowdesk.com. "
            "Returns latest annualized borrow fee, shares available, 30-day "
            "moving average, 30-day max, and a stable/rising/falling trend "
            "tag. Used for short-leg execution feasibility on paired trades. "
            "IBKR is the canonical retail-prime venue; other brokers track "
            "loosely but can differ materially."
        ),
        "params": {
            "ticker": "string — equity ticker symbol, e.g. 'IREN'",
        },
        "good_for": [
            "short-leg borrow-cost estimation",
            "short-leg inventory check (squeeze-risk proxy)",
            "borrow-fee trend monitoring (rising fees often front-run thesis)",
        ],
    },
    "sec_filings.list_filings_by_form": {
        "fn": sec_filings.list_filings_by_form,
        "description": (
            "SEC EDGAR submissions API — list all filings of a given form type "
            "for a specific CIK within a date window. Complements edgar_fts "
            "(which is fulltext-search-based) with a CIK-anchored 'show me all "
            "ABS-15G filings by this issuer' query. Use this for "
            "regulatory-cadence claims (filing N reports of form X since "
            "date Y) and securitization-issuance claims."
        ),
        "params": {
            "cik":         "string — 10-digit padded CIK or shorter form",
            "forms":       "string | list[str] — form name(s) to filter, e.g. ['ABS-15G','ABS-EE','10-D']",
            "cutoff_date": "(optional) string — ISO date upper bound 'YYYY-MM-DD'",
            "start_date":  "(optional) string — ISO date lower bound (default 2018-01-01)",
            "limit":       "(optional) int — max filings returned (default 50)",
        },
        "good_for": [
            "ABS-15G / ABS-EE securitization filing cadence",
            "10-D pool report frequency",
            "424B prospectus supplement counts",
            "filing-discipline adjudication for any CIK + form combination",
        ],
    },
}


def render_for_llm() -> str:
    """Render the catalog as a markdown spec for the LLM prompt."""
    lines = ["# Available M-source queries\n"]
    for name, spec in CATALOG.items():
        lines.append(f"## `{name}`")
        lines.append(spec["description"])
        lines.append("\n**Parameters:**")
        for p, desc in spec["params"].items():
            lines.append(f"- `{p}`: {desc}")
        lines.append(f"\n**Good for:** {', '.join(spec['good_for'])}\n")
    return "\n".join(lines)


# Param-name aliases the LLM planner often gets wrong. Map alias → canonical.
# Each function's signature is consulted at dispatch time; only aliases that
# would land on a real parameter are applied. Unknown kwargs are dropped
# rather than crashing.
_PARAM_ALIASES: dict[str, str] = {
    # edgar_fts
    "form_type":       "forms",
    "form_types":      "forms",
    "form":            "forms",
    "date_from":       "start_date",
    "start_dt":        "start_date",
    "startdt":         "start_date",
    "enddt":           "cutoff_date",
    "end_date":        "cutoff_date",
    "ciks":            "cik",
    # fdic_call_reports — only string-name aliases; RSSDID ≠ CERT so don't alias.
    "bank_names":      "bank_name",
    "institution_name":"bank_name",
    "institution":     "bank_name",
    "n_quarters":      "quarters",
}


def _adapt_kwargs(fn, kwargs: dict) -> tuple[dict, list[str], list[str]]:
    """Return (clean_kwargs, dropped_keys, applied_aliases) ready to call fn.

    Behavior:
      - Apply alias renames where the alias maps to a real parameter.
      - If a kwarg is a list/tuple and the target param is a scalar, take [0].
      - Drop kwargs whose (possibly aliased) name isn't in fn's signature
        AND fn doesn't accept **kwargs.
    """
    import inspect
    sig = inspect.signature(fn)
    params = sig.parameters
    accepts_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    valid_names = {n for n, p in params.items()
                   if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                 inspect.Parameter.KEYWORD_ONLY)}

    clean: dict = {}
    dropped: list[str] = []
    applied: list[str] = []

    for k, v in kwargs.items():
        target = k
        if k not in valid_names and k in _PARAM_ALIASES:
            cand = _PARAM_ALIASES[k]
            if cand in valid_names:
                target = cand
                applied.append(f"{k}->{cand}")
        if target not in valid_names and not accepts_var_kw:
            dropped.append(k)
            continue
        # List → scalar collapse when the parameter annotation isn't a list.
        if isinstance(v, (list, tuple)) and target in params:
            ann = params[target].annotation
            ann_str = str(ann)
            if "list" not in ann_str.lower() and "tuple" not in ann_str.lower():
                if v:
                    v = v[0]
                else:
                    dropped.append(k)
                    continue
        clean[target] = v

    return clean, dropped, applied


def call(source_name: str, kwargs: dict) -> dict:
    """Mechanically dispatch a query the LLM has selected. Retries once on
    transient errors (5xx, status_500) before giving up. Filters and aliases
    LLM-supplied kwargs so planner sloppiness doesn't crash execution."""
    import time as _t
    if source_name not in CATALOG:
        return {"error": f"unknown_source: {source_name}"}
    fn = CATALOG[source_name]["fn"]
    clean, dropped, applied = _adapt_kwargs(fn, kwargs or {})
    last = None
    for attempt in range(2):
        try:
            r = fn(**clean)
            if isinstance(r, dict):
                if dropped:
                    r.setdefault("_dropped_kwargs", dropped)
                if applied:
                    r.setdefault("_aliased_kwargs", applied)
            err = r.get("error", "") if isinstance(r, dict) else ""
            transient = isinstance(err, str) and ("status_5" in err or "incomplete chunk" in err)
            if not transient:
                return r
            last = r
            _t.sleep(2)
        except TypeError as e:
            return {"error": f"bad_kwargs: {e}", "_dropped_kwargs": dropped, "_aliased_kwargs": applied, "_cleaned": clean}
        except Exception as e:
            last = {"error": f"runtime: {e}"}
            _t.sleep(2)
    return last or {"error": "no result"}
