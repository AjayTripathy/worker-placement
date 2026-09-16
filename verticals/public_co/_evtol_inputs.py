"""eVTOL cohort LocalProvider input.json generator."""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path("/Users/ajay/exalted/signalos/verticals/public_co/data/_local")
OUT.mkdir(exist_ok=True, parents=True)

UAL = "0000100517"
AAL = "0000006201"
DAL = "0000027904"
JBLU = "0001158463"
TM   = "0001094517"
ERJ  = "0001355856"   # Embraer
STLA = "0001605484"   # Stellantis
CUTOFF = "2024-06-30"


def write(ticker, claims):
    (OUT / f"{ticker}.input.json").write_text(json.dumps(
        {"ticker": ticker, "cutoff_date": CUTOFF, "claims": claims}, indent=2))


# JOBY — Toyota partnership, named airline customer, Marina CA factory
write("joby", [
    {"claim_id": "C-001", "claim_text": "Joby has a strategic partnership with Toyota (manufacturing know-how + investment)",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Joby", "cutoff_date": CUTOFF, "cik": TM, "start_date": "2020-01-01"},
                  "rationale": "Toyota's ADR filings should disclose Joby investment + supplier relationship"}]},
    {"claim_id": "C-002", "claim_text": "Joby has named airline / military customer commitments (Delta + DoD)",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Joby", "cutoff_date": CUTOFF, "cik": DAL, "start_date": "2022-01-01"},
                  "rationale": "Delta is named partner; should appear in Delta 10-K"}]},
    {"claim_id": "C-003", "claim_text": "Joby operates a manufacturing/test facility in California (Marina, San Carlos)",
     "queries": [{"source": "epa_frs.query_facilities", "kwargs": {"facility_name": "Joby", "state_abbr": "CA"}, "rationale": ""}]},
    {"claim_id": "C-004", "claim_text": "Joby has IP portfolio in eVTOL propulsion / battery / aerodynamics",
     "queries": [{"source": "google_patents.query_assignee",
                  "kwargs": {"assignee_name": "Joby Aero", "cutoff_date": CUTOFF,
                             "categorize": {"propulsion": ["propulsion", "rotor", "motor", "tilt"],
                                            "battery": ["battery", "cell"],
                                            "aircraft": ["aircraft", "vertical takeoff", "VTOL"]}},
                  "rationale": ""}]},
    {"claim_id": "C-005", "claim_text": "Joby has external US public-co counterparty footprint",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Joby Aviation", "cutoff_date": CUTOFF, "start_date": "2021-01-01",
                             "forms": "10-K,10-Q,8-K,DEF 14A,20-F"}, "rationale": ""}]},
])


# ACHR — United Airlines $1B order, Stellantis manufacturing, Georgia plant
write("achr", [
    {"claim_id": "C-001", "claim_text": "United Airlines placed an order for up to 200 Archer Midnight aircraft (~$1B)",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Archer Aviation", "cutoff_date": CUTOFF, "cik": UAL, "start_date": "2021-01-01"},
                  "rationale": "United is named largest customer; should appear in UAL filings"}]},
    {"claim_id": "C-002", "claim_text": "Archer has Stellantis as manufacturing partner",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Archer Aviation", "cutoff_date": CUTOFF, "cik": STLA, "start_date": "2022-01-01"},
                  "rationale": "Stellantis is named manufacturing partner"}]},
    {"claim_id": "C-003", "claim_text": "Archer is constructing a manufacturing facility in Covington, Georgia",
     "queries": [{"source": "epa_frs.query_facilities", "kwargs": {"facility_name": "Archer", "state_abbr": "GA"}, "rationale": ""}]},
    {"claim_id": "C-004", "claim_text": "Archer has IP portfolio in eVTOL design / propulsion",
     "queries": [{"source": "google_patents.query_assignee",
                  "kwargs": {"assignee_name": "Archer Aviation", "cutoff_date": CUTOFF,
                             "categorize": {"propulsion": ["propulsion", "rotor", "motor", "tilt"],
                                            "aircraft": ["aircraft", "VTOL", "vertical"],
                                            "battery": ["battery", "cell"]}}, "rationale": ""}]},
    {"claim_id": "C-005", "claim_text": "Archer has external US public-co counterparty footprint",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Archer Aviation", "cutoff_date": CUTOFF, "start_date": "2021-01-01",
                             "forms": "10-K,10-Q,8-K,DEF 14A"}, "rationale": ""}]},
])


# EVEX (Eve Holding) — Embraer-backed, named airline customers
write("evex", [
    {"claim_id": "C-001", "claim_text": "American Airlines has named EVE as eVTOL partner (commitment for hundreds of aircraft)",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Eve Holding", "cutoff_date": CUTOFF, "cik": AAL, "start_date": "2022-01-01"},
                  "rationale": ""}]},
    {"claim_id": "C-002", "claim_text": "EVE is backed by Embraer (parent ADR) for design + manufacturing",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Eve Holding", "cutoff_date": CUTOFF, "cik": ERJ, "start_date": "2022-01-01"},
                  "rationale": "Embraer's ADR filings should disclose EVE backing"}]},
    {"claim_id": "C-003", "claim_text": "EVE operates from Florida (Melbourne FL Embraer facility)",
     "queries": [{"source": "epa_frs.query_facilities", "kwargs": {"facility_name": "Eve", "state_abbr": "FL"}, "rationale": ""}]},
    {"claim_id": "C-004", "claim_text": "EVE has IP / leverage Embraer IP for eVTOL design",
     "queries": [{"source": "google_patents.query_assignee",
                  "kwargs": {"assignee_name": "Eve Holding", "cutoff_date": CUTOFF,
                             "categorize": {"propulsion": ["propulsion", "rotor", "motor"],
                                            "aircraft": ["aircraft", "vertical", "eVTOL"]}}, "rationale": ""}]},
    {"claim_id": "C-005", "claim_text": "EVE has external US public-co counterparty footprint",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Eve Holding", "cutoff_date": CUTOFF, "start_date": "2022-01-01",
                             "forms": "10-K,10-Q,8-K,20-F,6-K"}, "rationale": ""}]},
])


# LILM (Lilium) — German eVTOL, named airline + corporate fleet customers
write("lilm", [
    {"claim_id": "C-001", "claim_text": "Lilium has named US-listed airline / fleet partners with order commitments",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Lilium", "cutoff_date": CUTOFF, "cik": JBLU, "start_date": "2021-01-01"},
                  "rationale": "JetBlue/Azul partnership rumored; check JBLU filings"}]},
    {"claim_id": "C-002", "claim_text": "Lilium operates from Munich, Germany (R&D + assembly)",
     "queries": [{"source": "epa_frs.query_facilities", "kwargs": {"facility_name": "Lilium", "state_abbr": "CA"}, "rationale": "EPA FRS US-only — Lilium primarily German; expecting 0 hits is honest"}]},
    {"claim_id": "C-003", "claim_text": "Lilium has IP portfolio in jet-eVTOL aircraft design",
     "queries": [{"source": "google_patents.query_assignee",
                  "kwargs": {"assignee_name": "Lilium", "cutoff_date": CUTOFF,
                             "categorize": {"propulsion": ["jet", "ducted fan", "propulsion"],
                                            "aircraft": ["aircraft", "vertical", "eVTOL"]}}, "rationale": ""}]},
    {"claim_id": "C-004", "claim_text": "Lilium has external US public-co counterparty footprint",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Lilium", "cutoff_date": CUTOFF, "start_date": "2021-01-01",
                             "forms": "10-K,10-Q,8-K,20-F,6-K"}, "rationale": ""}]},
    {"claim_id": "C-005", "claim_text": "Lilium product (Lilium Jet) has external mention as a distinctive product",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Lilium Jet", "cutoff_date": CUTOFF, "start_date": "2021-01-01"},
                  "rationale": "Distinctive product name search"}]},
])


# EVTL (Vertical Aerospace) — UK eVTOL, named airline customers
write("evtl", [
    {"claim_id": "C-001", "claim_text": "Vertical Aerospace has named US airline customers (American + Japan Airlines + Virgin)",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Vertical Aerospace", "cutoff_date": CUTOFF, "cik": AAL, "start_date": "2022-01-01"},
                  "rationale": "American Airlines is named buyer for VX4"}]},
    {"claim_id": "C-002", "claim_text": "Vertical Aerospace is operating in Texas (US base) + UK headquarters",
     "queries": [{"source": "epa_frs.query_facilities", "kwargs": {"facility_name": "Vertical Aerospace", "state_abbr": "TX"}, "rationale": ""}]},
    {"claim_id": "C-003", "claim_text": "Vertical Aerospace has IP portfolio in eVTOL aircraft design",
     "queries": [{"source": "google_patents.query_assignee",
                  "kwargs": {"assignee_name": "Vertical Aerospace", "cutoff_date": CUTOFF,
                             "categorize": {"aircraft": ["aircraft", "vertical", "eVTOL"],
                                            "propulsion": ["propulsion", "rotor"]}}, "rationale": ""}]},
    {"claim_id": "C-004", "claim_text": "Vertical Aerospace VX4 product has external mention as distinctive product",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Vertical Aerospace VX4", "cutoff_date": CUTOFF, "start_date": "2022-01-01"},
                  "rationale": ""}]},
    {"claim_id": "C-005", "claim_text": "Vertical Aerospace has external US public-co counterparty footprint",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Vertical Aerospace", "cutoff_date": CUTOFF, "start_date": "2022-01-01",
                             "forms": "10-K,10-Q,8-K,20-F,6-K"}, "rationale": ""}]},
])


# SRFM (Surf Air Mobility) — direct listing 2023, fixed-wing + future eVTOL
write("srfm", [
    {"claim_id": "C-001", "claim_text": "Surf Air operates regional flight services (real revenue, not pre-revenue)",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Surf Air Mobility", "cutoff_date": CUTOFF, "start_date": "2023-01-01",
                             "forms": "10-K,10-Q,8-K"}, "rationale": "Surf is operating; check for breadth of disclosure"}]},
    {"claim_id": "C-002", "claim_text": "Surf Air operates from California (HQ + base of operations)",
     "queries": [{"source": "epa_frs.query_facilities", "kwargs": {"facility_name": "Surf Air", "state_abbr": "CA"}, "rationale": ""}]},
    {"claim_id": "C-003", "claim_text": "Surf Air is registered as an aircraft manufacturer or operator",
     "queries": [{"source": "nhtsa.query_manufacturer", "kwargs": {"name": "Surf Air"}, "rationale": "NHTSA isn't aviation but used as sanity check; expect 0"}]},
    {"claim_id": "C-004", "claim_text": "Surf Air has IP in electrification of regional aircraft / hybrid powertrain",
     "queries": [{"source": "google_patents.query_assignee",
                  "kwargs": {"assignee_name": "Surf Air Mobility", "cutoff_date": CUTOFF,
                             "categorize": {"aircraft": ["aircraft", "VTOL", "hybrid"],
                                            "propulsion": ["propulsion", "motor", "battery"]}}, "rationale": ""}]},
    {"claim_id": "C-005", "claim_text": "Surf Air has named US-listed strategic counterparty (Textron/Cessna or similar)",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Surf Air", "cutoff_date": CUTOFF,
                             "cik": "0000217346", "start_date": "2022-01-01"},
                  "rationale": "Textron CIK as the major aircraft OEM Surf operates (Cessna Caravans)"}]},
])


print(f"wrote eVTOL inputs: {sorted(p.stem.replace('.input','') for p in OUT.glob('*.input.json') if p.stem.replace('.input','') in ('joby','achr','evex','lilm','evtl','srfm'))}")
