"""Analyst-curated M-recipe library.

Each recipe maps a CLAIM SHAPE to a concrete M-source query template. The LLM's
job in Stage 2 is reduced to: (1) match each claim to the right recipe(s),
(2) fill in the variables (brand name, state, counterparty CIK, etc.).

This is the 'cheating' part — an analyst encodes the institutional knowledge
of which public registry verifies which kind of claim. The LLM provides the
reading comprehension to extract claims and pattern-match them.

Each recipe is a dict with:
  - id: short identifier
  - applies_when: plain-English description of when this recipe fits
  - queries: list of (source, kwargs_template) tuples; kwargs may have
    placeholders like "<BRAND>", "<STATE>", "<COUNTERPARTY_CIK>", "<CUTOFF>",
    "<FUEL_TYPE>", "<PATENT_AREAS>" that the LLM fills in.
  - scoring_hints: brief notes on what evidence patterns mean what severity
"""
from __future__ import annotations


RECIPES = [
    {
        "id": "production_vehicle_check",
        "applies_when": (
            "Claim asserts the company produces or will produce a complete vehicle "
            "(car, truck, SUV, bus, etc.) — not chassis, drivetrain, or charging "
            "equipment alone."
        ),
        "queries": [
            {
                "source": "nhtsa.query_manufacturer",
                "kwargs_template": {"name": "<BRAND>"},
            },
        ],
        "scoring_hints": (
            "PASS if vehicle_types contains Truck/Passenger Car/MPV/Bus and NOT "
            "'Incomplete Vehicle'. SEVERE if registered as 'Incomplete Vehicle' only "
            "(chassis/glider, not complete OEM). MODERATE if not registered at all "
            "for a company claiming production. UNVERIFIABLE only if NHTSA query errors."
        ),
    },
    {
        "id": "factory_at_state",
        "applies_when": (
            "Claim asserts the company operates a manufacturing/assembly/processing "
            "facility in a specific US state. (For non-US factories, this recipe "
            "does not apply — note as UNVERIFIABLE since EPA FRS is US-only.)"
        ),
        "queries": [
            {
                "source": "epa_frs.query_facilities",
                "kwargs_template": {
                    "facility_name": "<BRAND>",
                    "state_abbr": "<STATE>",
                    "city_filter": "<CITY_OR_OMIT>",
                },
            },
        ],
        "scoring_hints": (
            "PASS if n_facilities >= 1 (preferred: facility name contains 'PLANT', "
            "'FACTORY', 'ASSEMBLY', 'MANUFACTURING'). SEVERE if zero facilities for a "
            "company claiming production-stage operations. MODERATE if facilities exist "
            "but none factory-named (e.g. only office sites)."
        ),
    },
    {
        "id": "fueling_network_count",
        "applies_when": (
            "Claim asserts the company operates a network of fueling/charging stations "
            "(hydrogen stations, EV chargers, CNG stations, etc.)."
        ),
        "queries": [
            {
                "source": "nrel_fuel.query_alt_fuel_stations",
                "kwargs_template": {
                    "fuel_type": "<HY_OR_ELEC>",
                    "cutoff_date": "<CUTOFF>",
                    "name_filter": "<BRAND>",
                },
            },
        ],
        "scoring_hints": (
            "PASS if matching_stations_count is substantial relative to claim (e.g. "
            ">10 if claim is 'extensive network'). SEVERE if claim is a meaningful "
            "network and matching_stations_count is 0 (DOE's authoritative US registry "
            "with NO entries is a strong contradiction)."
        ),
    },
    {
        "id": "named_counterparty_order",
        "applies_when": (
            "Claim asserts a NAMED US-listed counterparty (Amazon, GM, UPS, Anheuser-"
            "Busch, etc.) has placed an order, made an investment, or entered a "
            "supply commitment with the company. Counterparty MUST be a US-listed "
            "filer (has a CIK)."
        ),
        "queries": [
            {
                "source": "edgar_fts.query_fulltext",
                "kwargs_template": {
                    "search_term": "<BRAND>",
                    "cutoff_date": "<CUTOFF>",
                    "cik": "<COUNTERPARTY_CIK>",
                    "start_date": "<COUNTERPARTY_START_OR_2018>",
                },
            },
        ],
        "scoring_hints": (
            "PASS if total_hits >= 1 (counterparty's own filings disclose the brand). "
            "RED_FLAG_NEGATIVE if total_hits is 0 — a real material commitment from a "
            "named US-listed buyer would normally appear in their 10-K supply-chain or "
            "capital commitments. (Caveat: some commitments are immaterial relative to "
            "the counterparty's size.)"
        ),
    },
    {
        "id": "external_brand_validation",
        "applies_when": (
            "No specific named counterparty, but you want to gauge if the company is "
            "discussed in any US-listed filers' disclosures (suppliers, partners, "
            "competitors). Use the company's distinctive brand or product name."
        ),
        "queries": [
            {
                "source": "edgar_fts.query_fulltext",
                "kwargs_template": {
                    "search_term": "<DISTINCTIVE_BRAND_OR_PRODUCT>",
                    "cutoff_date": "<CUTOFF>",
                    "start_date": "2018-01-01",
                    "forms": "10-K,10-Q,8-K,DEF 14A",
                },
            },
        ],
        "scoring_hints": (
            "PASS if total_hits >= 10 (real footprint in US public-co filings). "
            "MODERATE if 1-9 hits. SEVERE if 0 hits — distinctive products of real "
            "companies leave traces in counterparty / competitor filings."
        ),
    },
    {
        "id": "patent_portfolio_in_area",
        "applies_when": (
            "Claim asserts proprietary IP in specific technology areas (batteries, "
            "motors, drivetrains, autonomy, fuel cells, etc.). The claim should name "
            "the technology categories."
        ),
        "queries": [
            {
                "source": "uspto_odp.query_assignee",
                "kwargs_template": {
                    "assignee_name": "<COMPANY_BRAND>",
                    "cutoff_date": "<CUTOFF>",
                    "categorize": "<DICT_OF_BUCKETS_TO_KEYWORDS>",
                },
            },
        ],
        "scoring_hints": (
            "Use n_granted (granted patents pre-cutoff) as the primary count. "
            "PASS if n_granted >= 5 AND category_counts shows >= 1 in each claimed "
            "category. MODERATE if n_granted >= 5 but applicants seem to focus on "
            "different areas than claimed (most titles in 'other'). SEVERE if "
            "n_granted is substantial (>=20) but category_counts shows ZERO in claimed "
            "categories — Nikola pattern (51 patents but 0 in batteries/inverter as "
            "claimed). UNVERIFIABLE only if uspto_odp returns an error. NOTE: "
            "n_total_applications includes pending; use n_granted for the comparable-"
            "to-claim figure."
        ),
    },
    {
        "id": "clinical_trial_program",
        "applies_when": (
            "Claim asserts the company has active clinical trials, sponsors trials, "
            "or has a clinical pipeline (biotech / pharma / med device)."
        ),
        "queries": [
            {
                "source": "clinical_trials.query_by_lead_sponsor",
                "kwargs_template": {
                    "sponsor_name": "<SPONSOR_NAME>",
                    "cutoff_date": "<CUTOFF>",
                },
            },
        ],
        "scoring_hints": (
            "PASS if n_studies_pre_cutoff >= claimed phase distribution (e.g. claim "
            "of 'Phase 2/3 program' should show PHASE2/PHASE3 entries in phase_counts). "
            "MODERATE if studies exist but phases below claim. SEVERE if zero studies "
            "for a claimed active sponsor."
        ),
    },
    {
        "id": "fda_approved_products",
        "applies_when": (
            "Claim asserts the company has FDA-approved drugs or commercial pharma/"
            "device products. NOT for clinical-stage companies (pre-NDA)."
        ),
        "queries": [
            {
                "source": "openfda.query_approved_drugs",
                "kwargs_template": {"manufacturer_name": "<MANUFACTURER>"},
            },
        ],
        "scoring_hints": (
            "PASS if n_approved_applications >= 1. RED_FLAG_NEGATIVE only if claim "
            "explicitly says 'we have approved products' and n=0. For clinical-stage "
            "companies that DON'T claim approval, this recipe does not apply."
        ),
    },
]


def render_for_llm() -> str:
    """Render the recipe library as markdown for the LLM prompt."""
    out = ["# M-source recipes (analyst-curated)\n",
           "Match each extracted claim to one or more recipes. For each match, fill",
           "in the placeholder variables (in <ANGLE_BRACKETS>) using values from the",
           "claim and the cutoff date. If no recipe fits a claim, mark it as",
           "untestable rather than inventing a query.\n"]
    for r in RECIPES:
        out.append(f"## `{r['id']}`")
        out.append(f"**Applies when:** {r['applies_when']}")
        out.append("**Queries to run:**")
        for q in r["queries"]:
            out.append(f"- source: `{q['source']}`")
            out.append(f"  kwargs template: `{q['kwargs_template']}`")
        out.append(f"**Scoring hints:** {r['scoring_hints']}\n")
    return "\n".join(out)


# Recipe lookup by id (for runtime dispatch)
BY_ID = {r["id"]: r for r in RECIPES}
