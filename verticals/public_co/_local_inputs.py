"""Generator for the remaining 10 cohort companies' LocalProvider input JSONs.

I picked claims using recipe shapes (factory + production check + named
counterparty + IP + external validation), customized per company based on
what each filing actually claims. Same 5-recipe-slot template as the first 5.
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path("/Users/ajay/exalted/signalos/verticals/public_co/data/_local")
OUT.mkdir(exist_ok=True, parents=True)


# CIK hints
GM     = "0001467858"
AMZN   = "0001018724"
UPS    = "0001090727"
MAGNA  = "0001072627"
TOTAL  = "0000879764"
DAIMLER_TRUCK = "0001868275"


def write(ticker: str, cutoff: str, claims: list[dict]) -> None:
    inp = {"ticker": ticker, "cutoff_date": cutoff, "claims": claims}
    (OUT / f"{ticker}.input.json").write_text(json.dumps(inp, indent=2))


# ---- RIDE (Lordstown) ----
write("ride", "2021-03-11", [
    {"claim_id": "C-001", "claim_text": "Lordstown's pre-orders include named fleet operators and the GM strategic investment is publicly disclosed",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Lordstown", "cutoff_date": "2021-03-11", "cik": GM, "start_date": "2019-01-01"},
                  "rationale": "GM is a named strategic investor + plant seller — should appear in GM's filings"}]},
    {"claim_id": "C-002", "claim_text": "Lordstown operates the former GM Lordstown OH assembly plant",
     "queries": [{"source": "epa_frs.query_facilities",
                  "kwargs": {"facility_name": "Lordstown", "state_abbr": "OH"}, "rationale": ""}]},
    {"claim_id": "C-003", "claim_text": "Lordstown is producing the Endurance pickup, a complete vehicle",
     "queries": [{"source": "nhtsa.query_manufacturer", "kwargs": {"name": "Lordstown"}, "rationale": ""}]},
    {"claim_id": "C-004", "claim_text": "Lordstown has IP portfolio in EV powertrain / hub motors",
     "queries": [{"source": "google_patents.query_assignee",
                  "kwargs": {"assignee_name": "Lordstown Motors", "cutoff_date": "2021-03-11",
                             "categorize": {"hub_motor": ["hub motor", "in-wheel"], "battery": ["battery"], "drivetrain": ["drivetrain", "motor", "powertrain"]}},
                  "rationale": ""}]},
    {"claim_id": "C-005", "claim_text": "Lordstown has external US public-co counterparty footprint",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Lordstown Motors", "cutoff_date": "2021-03-11", "start_date": "2019-01-01", "forms": "10-K,10-Q,8-K"},
                  "rationale": ""}]},
])


# ---- HYZN (Hyzon) ----
write("hyzn", "2022-01-15", [
    {"claim_id": "C-001", "claim_text": "Hyzon hydrogen-truck commitments from named US-listed customers (TotalEnergies)",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Hyzon", "cutoff_date": "2022-01-15", "cik": TOTAL, "start_date": "2020-01-01"},
                  "rationale": "TotalEnergies is named as customer/partner in Hyzon disclosures"}]},
    {"claim_id": "C-002", "claim_text": "Hyzon operates manufacturing in Rochester, NY",
     "queries": [{"source": "epa_frs.query_facilities", "kwargs": {"facility_name": "Hyzon", "state_abbr": "NY"}, "rationale": ""}]},
    {"claim_id": "C-003", "claim_text": "Hyzon is a complete-vehicle manufacturer (hydrogen trucks delivered to customers)",
     "queries": [{"source": "nhtsa.query_manufacturer", "kwargs": {"name": "Hyzon"}, "rationale": ""}]},
    {"claim_id": "C-004", "claim_text": "Hyzon has IP portfolio in fuel cell + hydrogen mobility",
     "queries": [{"source": "google_patents.query_assignee",
                  "kwargs": {"assignee_name": "Hyzon Motors", "cutoff_date": "2022-01-15",
                             "categorize": {"fuel_cell": ["fuel cell", "hydrogen"], "drivetrain": ["drivetrain", "motor", "powertrain"]}},
                  "rationale": ""}]},
    {"claim_id": "C-005", "claim_text": "Hyzon has external US public-co counterparty footprint",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Hyzon Motors", "cutoff_date": "2022-01-15", "start_date": "2020-01-01", "forms": "10-K,10-Q,8-K,20-F"},
                  "rationale": ""}]},
])


# ---- FSR (Fisker) ----
write("fsr", "2021-04-30", [
    {"claim_id": "C-001", "claim_text": "Fisker has manufacturing partnership with Magna International for the Ocean",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Fisker", "cutoff_date": "2021-04-30", "cik": MAGNA, "start_date": "2019-01-01"},
                  "rationale": "Magna is named manufacturing partner — should appear in Magna's filings"}]},
    {"claim_id": "C-002", "claim_text": "Fisker operates in California (HQ + design)",
     "queries": [{"source": "epa_frs.query_facilities", "kwargs": {"facility_name": "Fisker", "state_abbr": "CA"}, "rationale": ""}]},
    {"claim_id": "C-003", "claim_text": "Fisker Ocean SUV is in production / scheduled for 2022 delivery",
     "queries": [{"source": "nhtsa.query_manufacturer", "kwargs": {"name": "Fisker"}, "rationale": ""}]},
    {"claim_id": "C-004", "claim_text": "Fisker has IP portfolio in EV vehicle systems",
     "queries": [{"source": "google_patents.query_assignee",
                  "kwargs": {"assignee_name": "Fisker", "cutoff_date": "2021-04-30",
                             "categorize": {"battery": ["battery", "cell"], "drivetrain": ["drivetrain", "motor", "powertrain"]}},
                  "rationale": ""}]},
    {"claim_id": "C-005", "claim_text": "Fisker has external US public-co counterparty footprint",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Fisker Inc", "cutoff_date": "2021-04-30", "start_date": "2019-01-01", "forms": "10-K,10-Q,8-K"},
                  "rationale": ""}]},
])


# ---- ARVL (Arrival) ----
write("arvl", "2021-09-30", [
    {"claim_id": "C-001", "claim_text": "UPS placed an order for up to 10,000 Arrival electric delivery vans",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Arrival", "cutoff_date": "2021-09-30", "cik": UPS, "start_date": "2020-01-01"},
                  "rationale": "UPS is named as 10,000-vehicle customer — should appear in UPS filings"}]},
    {"claim_id": "C-002", "claim_text": "Arrival operates a microfactory in Charlotte, NC",
     "queries": [{"source": "epa_frs.query_facilities", "kwargs": {"facility_name": "Arrival", "state_abbr": "NC"}, "rationale": ""}]},
    {"claim_id": "C-003", "claim_text": "Arrival is a complete-vehicle manufacturer (EV vans)",
     "queries": [{"source": "nhtsa.query_manufacturer", "kwargs": {"name": "Arrival"}, "rationale": ""}]},
    {"claim_id": "C-004", "claim_text": "Arrival has IP portfolio in microfactory robotics + EV systems",
     "queries": [{"source": "google_patents.query_assignee",
                  "kwargs": {"assignee_name": "Arrival", "cutoff_date": "2021-09-30",
                             "categorize": {"battery": ["battery", "cell"], "robotics": ["robotic", "automated assembly"], "drivetrain": ["drivetrain", "motor"]}},
                  "rationale": ""}]},
    {"claim_id": "C-005", "claim_text": "Arrival has external US public-co counterparty footprint",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Arrival Group", "cutoff_date": "2021-09-30", "start_date": "2020-01-01", "forms": "10-K,10-Q,8-K"},
                  "rationale": "Arrival is a common word — using 'Arrival Group' to reduce noise"}]},
])


# ---- LEV (Lion Electric) ----
write("lev", "2021-11-30", [
    {"claim_id": "C-001", "claim_text": "Amazon committed to purchase 2,500 Lion electric trucks",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Lion Electric", "cutoff_date": "2021-11-30", "cik": AMZN, "start_date": "2020-01-01"},
                  "rationale": "Amazon is named as 2,500-truck customer"}]},
    {"claim_id": "C-002", "claim_text": "Lion Electric is constructing a battery factory in Joliet, IL",
     "queries": [{"source": "epa_frs.query_facilities", "kwargs": {"facility_name": "Lion Electric", "state_abbr": "IL"}, "rationale": ""}]},
    {"claim_id": "C-003", "claim_text": "Lion Electric manufactures complete electric trucks and school buses",
     "queries": [{"source": "nhtsa.query_manufacturer", "kwargs": {"name": "Lion Electric"}, "rationale": ""}]},
    {"claim_id": "C-004", "claim_text": "Lion has IP portfolio in EV truck/bus drivetrains",
     "queries": [{"source": "google_patents.query_assignee",
                  "kwargs": {"assignee_name": "Lion Electric", "cutoff_date": "2021-11-30",
                             "categorize": {"battery": ["battery", "cell"], "drivetrain": ["drivetrain", "motor", "powertrain"]}},
                  "rationale": ""}]},
    {"claim_id": "C-005", "claim_text": "Lion Electric has external US public-co counterparty footprint",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Lion Electric", "cutoff_date": "2021-11-30", "start_date": "2020-01-01", "forms": "10-K,10-Q,8-K,20-F,6-K"},
                  "rationale": ""}]},
])


# ---- PTRA (Proterra) ----
write("ptra", "2021-12-31", [
    {"claim_id": "C-001", "claim_text": "Proterra has battery + powertrain supply contracts with Daimler Truck",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Proterra", "cutoff_date": "2021-12-31", "start_date": "2019-01-01", "forms": "20-F,6-K,10-K"},
                  "rationale": "Daimler Truck is named partner; foreign-issuer search"}]},
    {"claim_id": "C-002", "claim_text": "Proterra operates manufacturing in South Carolina (Greenville)",
     "queries": [{"source": "epa_frs.query_facilities", "kwargs": {"facility_name": "Proterra", "state_abbr": "SC"}, "rationale": ""}]},
    {"claim_id": "C-003", "claim_text": "Proterra produces complete electric transit buses",
     "queries": [{"source": "nhtsa.query_manufacturer", "kwargs": {"name": "Proterra"}, "rationale": ""}]},
    {"claim_id": "C-004", "claim_text": "Proterra has IP portfolio in battery systems + electric drivetrains",
     "queries": [{"source": "google_patents.query_assignee",
                  "kwargs": {"assignee_name": "Proterra", "cutoff_date": "2021-12-31",
                             "categorize": {"battery": ["battery", "cell", "pack"], "drivetrain": ["drivetrain", "motor", "powertrain"]}},
                  "rationale": ""}]},
    {"claim_id": "C-005", "claim_text": "Proterra also operates in California (Burlingame)",
     "queries": [{"source": "epa_frs.query_facilities", "kwargs": {"facility_name": "Proterra", "state_abbr": "CA"}, "rationale": ""}]},
])


# ---- FFIE (Faraday Future) ----
write("ffie", "2022-01-30", [
    {"claim_id": "C-001", "claim_text": "Faraday Future operates the FF 91 manufacturing facility in Hanford, CA",
     "queries": [{"source": "epa_frs.query_facilities", "kwargs": {"facility_name": "Faraday Future", "state_abbr": "CA"}, "rationale": ""}]},
    {"claim_id": "C-002", "claim_text": "Faraday Future is a complete-vehicle manufacturer (FF 91 luxury EV)",
     "queries": [{"source": "nhtsa.query_manufacturer", "kwargs": {"name": "Faraday Future"}, "rationale": ""}]},
    {"claim_id": "C-003", "claim_text": "Faraday Future has IP portfolio in EV powertrain + autonomy",
     "queries": [{"source": "google_patents.query_assignee",
                  "kwargs": {"assignee_name": "Faraday Future", "cutoff_date": "2022-01-30",
                             "categorize": {"battery": ["battery", "cell"], "drivetrain": ["drivetrain", "motor", "powertrain"], "autonomy": ["autonomous", "driver assist"]}},
                  "rationale": ""}]},
    {"claim_id": "C-004", "claim_text": "Faraday Future has external US public-co counterparty footprint",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Faraday Future", "cutoff_date": "2022-01-30", "start_date": "2019-01-01", "forms": "10-K,10-Q,8-K"},
                  "rationale": ""}]},
    {"claim_id": "C-005", "claim_text": "Faraday Future has named US-listed strategic counterparty (Geely / other OEM)",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Faraday Future FF 91", "cutoff_date": "2022-01-30", "start_date": "2019-01-01"},
                  "rationale": "Distinctive product name, broad search"}]},
])


# ---- LCID (Lucid) ----
write("lcid", "2022-03-15", [
    {"claim_id": "C-001", "claim_text": "Lucid operates the AMP-1 manufacturing facility in Casa Grande, AZ",
     "queries": [{"source": "epa_frs.query_facilities",
                  "kwargs": {"facility_name": "Lucid", "state_abbr": "AZ", "city_filter": "CASA GRANDE"}, "rationale": ""}]},
    {"claim_id": "C-002", "claim_text": "Lucid Air is a production-stage luxury EV (delivered to customers)",
     "queries": [{"source": "nhtsa.query_manufacturer", "kwargs": {"name": "Lucid"}, "rationale": ""}]},
    {"claim_id": "C-003", "claim_text": "Lucid has IP portfolio in batteries + EV powertrain (Peter Rawlinson / ex-Tesla team)",
     "queries": [{"source": "google_patents.query_assignee",
                  "kwargs": {"assignee_name": "Atieva", "cutoff_date": "2022-03-15",
                             "categorize": {"battery": ["battery", "cell"], "drivetrain": ["drivetrain", "motor", "inverter", "powertrain"]}},
                  "rationale": "Atieva is the legal name Lucid files patents under"}]},
    {"claim_id": "C-004", "claim_text": "Lucid has external US public-co counterparty footprint",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Lucid Group", "cutoff_date": "2022-03-15", "start_date": "2020-01-01", "forms": "10-K,10-Q,8-K"},
                  "rationale": ""}]},
    {"claim_id": "C-005", "claim_text": "Lucid Air is EPA-certified as production vehicle (Air Dream models)",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "Lucid Air", "cutoff_date": "2022-03-15", "start_date": "2021-01-01"},
                  "rationale": "Distinctive product name"}]},
])


# ---- CHPT (ChargePoint) — NOT a vehicle OEM ----
write("chpt", "2021-08-30", [
    {"claim_id": "C-001", "claim_text": "ChargePoint operates a network of 100,000+ EV charging ports",
     "queries": [{"source": "nrel_fuel.query_alt_fuel_stations",
                  "kwargs": {"fuel_type": "ELEC", "cutoff_date": "2021-08-30", "name_filter": "ChargePoint"}, "rationale": ""}]},
    {"claim_id": "C-002", "claim_text": "ChargePoint has external US public-co counterparty footprint",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "ChargePoint", "cutoff_date": "2021-08-30", "start_date": "2019-01-01", "forms": "10-K,10-Q,8-K"},
                  "rationale": ""}]},
    {"claim_id": "C-003", "claim_text": "ChargePoint operates from California",
     "queries": [{"source": "epa_frs.query_facilities", "kwargs": {"facility_name": "ChargePoint", "state_abbr": "CA"}, "rationale": ""}]},
    {"claim_id": "C-004", "claim_text": "ChargePoint is NOT a vehicle manufacturer (sanity check — they make charging equipment)",
     "queries": [{"source": "nhtsa.query_manufacturer", "kwargs": {"name": "ChargePoint"}, "rationale": ""}]},
    {"claim_id": "C-005", "claim_text": "ChargePoint has IP portfolio in EV charging hardware",
     "queries": [{"source": "google_patents.query_assignee",
                  "kwargs": {"assignee_name": "ChargePoint", "cutoff_date": "2021-08-30",
                             "categorize": {"charging": ["charging", "charger"], "power": ["power electronics", "inverter"]}},
                  "rationale": ""}]},
])


# ---- EVGO (EVgo) — NOT a vehicle OEM ----
write("evgo", "2022-01-31", [
    {"claim_id": "C-001", "claim_text": "EVgo operates 800+ DC fast-charging stations",
     "queries": [{"source": "nrel_fuel.query_alt_fuel_stations",
                  "kwargs": {"fuel_type": "ELEC", "cutoff_date": "2022-01-31", "name_filter": "EVgo"}, "rationale": ""}]},
    {"claim_id": "C-002", "claim_text": "EVgo has strategic partnership with GM",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "EVgo", "cutoff_date": "2022-01-31", "cik": GM, "start_date": "2020-01-01"},
                  "rationale": "GM is named partner — should appear in GM filings"}]},
    {"claim_id": "C-003", "claim_text": "EVgo has external US public-co counterparty footprint",
     "queries": [{"source": "edgar_fts.query_fulltext",
                  "kwargs": {"search_term": "EVgo", "cutoff_date": "2022-01-31", "start_date": "2019-01-01", "forms": "10-K,10-Q,8-K"},
                  "rationale": ""}]},
    {"claim_id": "C-004", "claim_text": "EVgo operates from California",
     "queries": [{"source": "epa_frs.query_facilities", "kwargs": {"facility_name": "EVgo", "state_abbr": "CA"}, "rationale": ""}]},
    {"claim_id": "C-005", "claim_text": "EVgo is NOT a vehicle manufacturer (sanity check)",
     "queries": [{"source": "nhtsa.query_manufacturer", "kwargs": {"name": "EVgo"}, "rationale": ""}]},
])


print(f"wrote {len(list(OUT.glob('*.input.json')))} input.json files in {OUT}")
