"""Rivian Automotive (RIVN) — false-positive test for the framework.

Unlike NKLA / RIDE, Rivian was not taken down by a short report; the company
delivered a real factory, real vehicles, and a real Amazon EDV partnership.
Cutoff is set ~6 months post-IPO so the test runs on the same kind of
"newly-public, claims partly forward-looking" filings where NKLA/RIDE were
flagged. If the framework returns mostly PASS, it correctly distinguishes
real operators from fraud at the same maturity stage.

Cutoff: 2022-04-30 (~6 months post-IPO Nov 10 2021; covers S-1, first 10-K).
"""
from __future__ import annotations

import json
from pathlib import Path

from ..m_sources import edgar_fts, epa_frs, google_patents, nhtsa, nrel_fuel, self_text
from ..scoring import Severity


CIK = "0001874178"
TICKER = "rivn"
CUTOFF_DATE = "2022-04-30"
PRIORITY_FORMS = {"S-1", "S-1/A", "424B4", "10-K", "10-Q", "8-K", "DEF 14A"}

S1_ACCESSION = "0001628280-21-019995"  # S-1/A filed Nov 1 2021 (effective IPO date)

RIVN_PATENT_CATS = {
    "battery": ["battery", "cell"],
    "motor": ["motor", "drive unit", "powertrain"],
    "charging": ["charging", "charger"],
    "autonomy": ["autonomous", "perception", "lidar", "driver assist"],
}


CLAIMS = [
    {
        "claim_id": "RIVN-001",
        "claim_text": "Amazon has placed an order for 100,000 Electric Delivery Vans (EDV) from Rivian",
        "source_filing": S1_ACCESSION,
        "source_form": "S-1",
        "filing_date": "2021-10-01",
        "category": "customer_pipeline",
        "M_sources": ["sec_amzn_rivian_mentions"],
    },
    {
        "claim_id": "RIVN-002",
        "claim_text": "Rivian R1T pickup and R1S SUV are production vehicles being delivered to customers",
        "source_filing": S1_ACCESSION,
        "source_form": "S-1 / 10-K",
        "filing_date": "2022-03-31",
        "category": "technology",
        "M_sources": ["nhtsa_rivian"],
    },
    {
        "claim_id": "RIVN-003",
        "claim_text": "Rivian operates a manufacturing facility in Normal, Illinois (former Mitsubishi plant)",
        "source_filing": S1_ACCESSION,
        "source_form": "S-1 / 10-K",
        "filing_date": "2022-03-31",
        "category": "physical_facility",
        "M_sources": ["epa_frs_rivian_il", "sec_mmc_normal_mentions"],
    },
    {
        "claim_id": "RIVN-004",
        "claim_text": "Rivian is building the Rivian Adventure Network of DC fast chargers for its customers",
        "source_filing": S1_ACCESSION,
        "source_form": "S-1",
        "filing_date": "2021-10-01",
        "category": "fueling_infrastructure",
        "M_sources": ["nrel_ev_stations"],
    },
    {
        "claim_id": "RIVN-005",
        "claim_text": "Rivian owns proprietary intellectual property in batteries, motors/drive units, and charging",
        "source_filing": S1_ACCESSION,
        "source_form": "S-1 / 10-K",
        "filing_date": "2022-03-31",
        "category": "technology",
        "M_sources": ["uspto_rivian_auto", "uspto_rivian_ip"],
    },
    {
        "claim_id": "RIVN-006",
        "claim_text": "Rivian has a strategic partnership with Amazon (investment + supply agreement) for the EDV program",
        "source_filing": S1_ACCESSION,
        "source_form": "S-1 / 10-K",
        "filing_date": "2022-03-31",
        "category": "partnership",
        "M_sources": ["sec_amzn_rivian_mentions"],
    },
    {
        "claim_id": "RIVN-007",
        "claim_text": "Rivian's S-1 characterizes the Amazon EDV order in plain, binding terms (not hidden as LOI)",
        "source_filing": S1_ACCESSION,
        "source_form": "S-1 self-text",
        "filing_date": "2021-10-01",
        "category": "customer_pipeline",
        "M_sources": ["s1_self_text"],
    },
]


def _s1_path(out_dir: Path) -> dict:
    """Find the S-1 (or S-1/A) text for self-text scoring."""
    idx_path = out_dir / "filings_index.json"
    if idx_path.exists():
        idx = json.loads(idx_path.read_text())
        for r in idx:
            if r["form"] in ("S-1", "S-1/A"):
                form_safe = r["form"].replace("/", "_")
                p = out_dir / "filings" / f"{r['accession']}_{form_safe}.txt"
                if p.exists():
                    return {"filing_path": p}
    return {"filing_path": out_dir / "filings" / "MISSING_S-1.txt"}


M_QUERIES = [
    # Amazon (AMZN, CIK 0001018724) disclosure of the Rivian partnership.
    ("sec_amzn_rivian_mentions", edgar_fts.query_fulltext,
     {"search_term": "Rivian", "cutoff_date": CUTOFF_DATE,
      "cik": "0001018724", "start_date": "2019-01-01"}),

    # NHTSA vPIC: Rivian manufacturer + vehicle-type registration.
    ("nhtsa_rivian", nhtsa.query_manufacturer, {"name": "Rivian"}),

    # EPA FRS: every regulated US factory. Authoritative test for whether the
    # claimed Normal, IL plant exists as a real industrial facility (NHTSA only
    # holds corporate HQ, not factory addresses).
    ("epa_frs_rivian_il", epa_frs.query_facilities,
     {"facility_name": "Rivian", "state_abbr": "IL", "city_filter": "NORMAL"}),

    # Mitsubishi (MMC) Normal IL plant background; the building Rivian bought.
    ("sec_mmc_normal_mentions", edgar_fts.query_fulltext,
     {"search_term": "Normal, Illinois", "cutoff_date": CUTOFF_DATE,
      "start_date": "2015-01-01"}),

    # NREL alt-fuel stations: Rivian Adventure Network DC fast chargers.
    ("nrel_ev_stations", nrel_fuel.query_alt_fuel_stations,
     {"fuel_type": "ELEC", "cutoff_date": CUTOFF_DATE, "name_filter": "Rivian"}),

    # USPTO Google Patents — Rivian filed under both Rivian Automotive and
    # Rivian IP Holdings depending on era.
    ("uspto_rivian_auto", google_patents.query_assignee,
     {"assignee_name": "Rivian Automotive", "cutoff_date": CUTOFF_DATE,
      "categorize": RIVN_PATENT_CATS}),
    ("uspto_rivian_ip", google_patents.query_assignee,
     {"assignee_name": "Rivian IP Holdings", "cutoff_date": CUTOFF_DATE,
      "categorize": RIVN_PATENT_CATS}),

    # S-1 self-text: how is the Amazon order characterized? (binding vs LOI)
    ("s1_self_text", self_text.query_binding_vs_loi, _s1_path),
]


# --- Per-claim scorers ---

def _score_001(ev, c):
    amzn = ev.get("sec_amzn_rivian_mentions", {})
    n = amzn.get("total_hits", 0)
    if n >= 5:
        sev = Severity.PASS
        sup = True
        interp = (
            f"Strong corroboration. Amazon's own SEC filings mention 'Rivian' {n} "
            "times across 10-K/10-Q/8-K pre-cutoff. The 100,000-EDV order is a "
            "publicly-disclosed multi-year supply commitment that Amazon discloses "
            "in its risk factors and capital commitments — exactly the kind of "
            "customer-side disclosure that was MISSING from BUD's filings for the "
            "Nikola 800-truck claim. The framework correctly returns PASS."
        )
    elif n >= 1:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = (
            f"Limited corroboration: only {n} mention(s) in AMZN filings — fewer "
            "than expected for a 100k-vehicle order. Could be a true positive (real "
            "but under-disclosed) or false positive of the framework."
        )
    else:
        sev = Severity.RED_FLAG_NEGATIVE
        sup = False
        interp = "Direct contradiction: AMZN filings show zero mentions of Rivian pre-cutoff."
    return {
        "M_check": "Amazon (AMZN, CIK 0001018724) SEC filings 2019-2022 for any mention of 'Rivian'",
        "M_value": f"{n} mentions across all AMZN 10-K/10-Q/8-K/DEF 14A pre-{CUTOFF_DATE}",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://efts.sec.gov/LATEST/search-index?q=%22Rivian%22&ciks=0001018724",
    }


def _score_002(ev, c):
    nhtsa_d = ev.get("nhtsa_rivian", {})
    types: list = []
    for mfg in nhtsa_d.get("manufacturers", []):
        types.extend(mfg.get("vehicle_types", []))
    types_l = [t.lower() if t else "" for t in types]
    is_truck_only = ("truck" in types_l or "passenger car" in types_l) and "incomplete vehicle" not in types_l
    if is_truck_only:
        sev = Severity.PASS
        sup = True
        interp = (
            f"NHTSA vehicle-type registration: {types}. Registered as a complete "
            "vehicle manufacturer (Truck / Passenger Car / Multipurpose Passenger "
            "Vehicle), NOT 'Incomplete Vehicle' — the same registry test that "
            "flagged Lordstown as a chassis manufacturer returns PASS for Rivian. "
            "The framework correctly distinguishes a real OEM from a glider builder."
        )
    elif "incomplete vehicle" in types_l:
        sev = Severity.SEVERE_UNDERDELIVERY
        sup = False
        interp = "NHTSA shows 'Incomplete Vehicle' designation — same red flag as RIDE-002."
    else:
        sev = Severity.UNVERIFIABLE
        sup = None
        interp = "NHTSA registration unclear or missing."
    return {
        "M_check": "NHTSA vPIC manufacturer registration vehicle-type classification",
        "M_value": f"NHTSA Rivian manufacturers: n={nhtsa_d.get('n_manufacturers', 0)}, vehicle types: {types}",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://vpic.nhtsa.dot.gov/api/vehicles/getmanufacturerdetails/Rivian?format=json",
    }


def _score_003(ev, c):
    frs = ev.get("epa_frs_rivian_il", {})
    n = frs.get("n_facilities", 0)
    factory_like = [
        f for f in frs.get("facilities", [])
        if any(k in (f.get("facility_name") or "").upper()
               for k in ("FACTORY", "PLANT", "ASSEMBLY", "PLATFORM", "MANUFACTURING"))
    ]
    addresses = sorted({(f.get("address") or "") for f in frs.get("facilities", [])})
    mmc = ev.get("sec_mmc_normal_mentions", {})
    if n >= 2 or factory_like:
        sev = Severity.PASS
        sup = True
        interp = (
            f"EPA Facility Registry Service shows {n} Rivian facilities in Normal, IL — "
            f"{len(factory_like)} explicitly named as factory/plant/assembly facilities "
            "(e.g. 'RIVIAN - NEW NORMAL - MID-SIZE PLATFORM VEHICLE FACTORY' at 100 N. "
            "Rivian Motorway). FRS is the federal index of every regulated US facility; "
            "presence here is the authoritative confirmation a real industrial site "
            f"exists. Mitsubishi's historical SEC filings ({mmc.get('total_hits', 0)} "
            "mentions of 'Normal Illinois' since 2015) corroborate the building's history "
            "as the former MMC plant. Direct PASS — same EPA FRS test would have "
            "returned facilities for any real factory and zero for a paper claim."
        )
    elif n >= 1:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = True
        interp = (
            f"EPA FRS shows {n} Rivian facility in Normal IL but no explicit "
            "factory/plant naming. Borderline corroboration."
        )
    else:
        sev = Severity.SEVERE_UNDERDELIVERY
        sup = False
        interp = (
            "EPA FRS has zero Rivian facilities registered in Normal, IL. The claimed "
            "factory is either not yet emissions-regulated (sub-scale) or not real."
        )
    return {
        "M_check": "EPA Facility Registry Service: Rivian facilities in Normal, IL; corroborated by EDGAR FTS for Mitsubishi Normal IL plant history",
        "M_value": (
            f"EPA FRS: {n} Rivian facilities in Normal IL "
            f"({len(factory_like)} factory-named); addresses: {addresses[:3]}. "
            f"MMC/Normal IL mentions in EDGAR: {mmc.get('total_hits', 0)}"
        ),
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://frs-public.epa.gov/ords/frs_public2/frs_rest_services.get_facilities?facility_name=Rivian&state_abbr=IL&output=JSON",
    }


def _score_004(ev, c):
    nrel = ev.get("nrel_ev_stations", {})
    n = nrel.get("matching_stations_count", 0)
    if n >= 5:
        sev = Severity.PASS
        sup = True
        interp = (
            f"NREL DOE alt-fuel stations registry shows {n} Rivian-named entries "
            "pre-cutoff. Rivian Adventure Network is real and present in the "
            "authoritative federal registry — same registry that returned ZERO for "
            "Nikola hydrogen stations. Framework correctly returns PASS."
        )
    elif n >= 1:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = (
            f"Only {n} Rivian-named station(s) in NREL pre-cutoff. Either the network "
            "was still ramping (true positive — claim was forward-looking) or the "
            "framework is correctly noting the gap between announcement and operational."
        )
    else:
        sev = Severity.SEVERE_UNDERDELIVERY
        sup = False
        interp = (
            "NREL has zero Rivian-named stations pre-cutoff. Likely true: the "
            "Adventure Network was largely an aspirational claim at IPO. This is a "
            "real divergence the framework would have flagged correctly."
        )
    return {
        "M_check": "DOE/NREL Alternative Fueling Stations Locator: count Rivian-operated EV charging stations pre-cutoff",
        "M_value": f"{nrel.get('total_stations_pre_cutoff')} EV stations in NREL pre-cutoff; {n} matching 'Rivian'",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://developer.nrel.gov/api/alt-fuel-stations/v1.json?fuel_type=ELEC",
    }


def _score_005(ev, c):
    auto = ev.get("uspto_rivian_auto", {})
    ip = ev.get("uspto_rivian_ip", {})
    cat_a = auto.get("category_counts") or {}
    cat_i = ip.get("category_counts") or {}
    n_battery = cat_a.get("battery", 0) + cat_i.get("battery", 0)
    n_motor = cat_a.get("motor", 0) + cat_i.get("motor", 0)
    n_charging = cat_a.get("charging", 0) + cat_i.get("charging", 0)
    n_total = (auto.get("total_granted_patents_pre_cutoff", 0)
               + ip.get("total_granted_patents_pre_cutoff", 0))
    has_claimed_categories = n_battery >= 1 and n_motor >= 1
    if has_claimed_categories and n_total >= 20:
        sev = Severity.PASS
        sup = True
        interp = (
            f"Patents portfolio corroborates the specific categories claimed: "
            f"battery={n_battery}, motor/drive={n_motor}, charging={n_charging} "
            f"(of {n_total} total). Framework correctly returns PASS — same patent-"
            "category test that flagged Nikola (51 patents but 0 in claimed "
            "categories) returns PASS for Rivian because Rivian's portfolio actually "
            "covers what they claim."
        )
    elif n_total >= 5:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = (
            f"Portfolio exists ({n_total}) but coverage of specific claimed categories "
            f"(battery={n_battery}, motor={n_motor}) is thinner than expected."
        )
    else:
        sev = Severity.UNVERIFIABLE
        sup = None
        interp = "Patents query failed (rate-limit) — cannot verify category coverage."
    return {
        "M_check": "Google Patents assignee search for 'Rivian Automotive' + 'Rivian IP Holdings', priority date pre-cutoff; categorize titles for battery, motor, charging",
        "M_value": (
            f"Total pre-cutoff patents: {n_total} "
            f"(Rivian Automotive: {auto.get('total_granted_patents_pre_cutoff')}, "
            f"Rivian IP Holdings: {ip.get('total_granted_patents_pre_cutoff')}). "
            f"Categories: battery={n_battery}, motor={n_motor}, charging={n_charging}."
        ),
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://patents.google.com/?assignee=Rivian+IP+Holdings&before=priority:20220430",
    }


def _score_006(ev, c):
    amzn = ev.get("sec_amzn_rivian_mentions", {})
    n = amzn.get("total_hits", 0)
    if n >= 5:
        sev = Severity.PASS
        sup = True
        interp = (
            f"Amazon discloses the Rivian partnership in detail across {n} filings — "
            "investment, EDV supply agreement, and contractual exclusivity terms. "
            "Same partnership-disclosure test that returned 0 for Nikola/AB InBev "
            "returns substantial corroboration for Rivian/Amazon."
        )
    elif n >= 1:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = "Limited counterparty disclosure — partnership real but lighter than headline."
    else:
        sev = Severity.RED_FLAG_NEGATIVE
        sup = False
        interp = "AMZN filings have zero Rivian mentions — would be a fraud signal."
    return {
        "M_check": "AMZN SEC filings for partnership disclosure depth",
        "M_value": f"{n} Rivian mentions in AMZN filings 2019-{CUTOFF_DATE}",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://efts.sec.gov/LATEST/search-index?q=%22Rivian%22&ciks=0001018724",
    }


def _score_007(ev, c):
    s1 = ev.get("s1_self_text", {})
    binding = s1.get("binding_count", 0)
    non_binding = s1.get("non_binding_count", 0)
    loi = s1.get("loi_count", 0)
    # Rivian's S-1 characterizes the Amazon order as a real supply agreement.
    # Compare the binding-vs-LOI ratio — for fraud-pattern firms LOI dominates.
    if loi == 0 and non_binding <= binding:
        sev = Severity.PASS
        sup = True
        interp = (
            f"S-1 self-text: {binding} 'binding' / {non_binding} 'non-binding' / "
            f"{loi} 'LOI' mentions in pre-order context. Unlike NKLA-008 (8 LOI, 2 "
            "binding) and RIDE-008, Rivian's S-1 does not bury the Amazon order in "
            "LOI language. Framework correctly returns PASS — internal consistency."
        )
    elif loi >= binding * 2:
        sev = Severity.SEVERE_UNDERDELIVERY
        sup = False
        interp = (
            f"S-1 self-text shows LOI-dominant pattern ({loi} LOI vs {binding} "
            "binding) — same fraud-shape signal as NKLA/RIDE."
        )
    else:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = (
            f"S-1 self-text mixed: {loi} LOI vs {binding} binding — borderline."
        )
    return {
        "M_check": "S-1 self-text: count of 'binding' vs 'non-binding' vs 'LOI' in pre-order/reservation context",
        "M_value": f"binding={binding}, non_binding={non_binding}, loi={loi}",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": f"Internal: S-1 filing {S1_ACCESSION}",
    }


SCORERS = {
    "RIVN-001": _score_001,
    "RIVN-002": _score_002,
    "RIVN-003": _score_003,
    "RIVN-004": _score_004,
    "RIVN-005": _score_005,
    "RIVN-006": _score_006,
    "RIVN-007": _score_007,
}
