"""Nikola Corporation (NKLA) backtest config.

Cutoff: 2020-09-09 (day before Hindenburg's "Nikola: How To Parlay An Ocean of
Lies Into A Partnership With The Largest Auto OEM In America").
"""
from __future__ import annotations

from pathlib import Path

from ..m_sources import (
    az_corp,
    edgar_fts,
    google_patents,
    nhtsa,
    nrel_fuel,
    self_text,
)
from ..scoring import Severity


CIK = "0001731289"  # Nikola Corp / VectoIQ Acquisition Corp
TICKER = "nkla"
CUTOFF_DATE = "2020-09-09"
PRIORITY_FORMS = {"S-1", "S-4", "S-4/A", "424B3", "424B4", "10-K", "10-Q", "8-K", "DEF 14A"}

S4_ACCESSION = "0001047469-20-001479"  # March 2020 S-4

CLAIMS = [
    {
        "claim_id": "NKLA-001",
        "claim_text": "Nikola has developed a functional hydrogen-electric semi-truck (Nikola One)",
        "source_filing": S4_ACCESSION,
        "source_form": "S-4",
        "filing_date": "2020-03-13",
        "category": "technology",
        "M_sources": ["nhtsa_manufacturer"],
    },
    {
        "claim_id": "NKLA-002",
        "claim_text": "Nikola has built or contracted hydrogen fueling stations for its truck network",
        "source_filing": S4_ACCESSION,
        "source_form": "S-4",
        "filing_date": "2020-03-13",
        "category": "fueling_infrastructure",
        "M_sources": ["nrel_hydrogen_stations"],
    },
    {
        "claim_id": "NKLA-003",
        "claim_text": "Anheuser-Busch placed order for up to 800 Nikola hydrogen-electric trucks",
        "source_filing": S4_ACCESSION,
        "source_form": "S-4",
        "filing_date": "2020-03-13",
        "category": "customer_pipeline",
        "M_sources": ["sec_bud_nikola_mentions"],
    },
    {
        "claim_id": "NKLA-004",
        "claim_text": "Nikola has approximately $14 billion in pre-orders / reservations",
        "source_filing": S4_ACCESSION,
        "source_form": "S-4",
        "filing_date": "2020-03-13",
        "category": "customer_pipeline",
        "M_sources": ["sec_bud_nikola_mentions", "sec_usxe_nikola_mentions", "sec_rsg_nikola_mentions"],
    },
    {
        "claim_id": "NKLA-005",
        "claim_text": "Nikola is constructing a manufacturing facility in Coolidge, Arizona",
        "source_filing": S4_ACCESSION,
        "source_form": "S-4",
        "filing_date": "2020-03-13",
        "category": "physical_facility",
        "M_sources": ["az_corp_commission", "nhtsa_manufacturer"],
    },
    {
        "claim_id": "NKLA-006",
        "claim_text": "Nikola owns proprietary intellectual property in batteries, inverter, and infotainment",
        "source_filing": S4_ACCESSION,
        "source_form": "S-4",
        "filing_date": "2020-03-13",
        "category": "technology",
        "M_sources": ["uspto_nikola_corp", "uspto_nikola_motor"],
    },
    {
        "claim_id": "NKLA-007",
        "claim_text": "Nikola has a partnership/joint development with Bosch on the e-axle and powertrain",
        "source_filing": S4_ACCESSION,
        "source_form": "S-4",
        "filing_date": "2020-03-13",
        "category": "technology",
        "M_sources": ["uspto_nikola_corp"],
    },
    {
        "claim_id": "NKLA-008",
        "claim_text": "Nikola's vehicle reservations represent committed and binding orders",
        "source_filing": S4_ACCESSION,
        "source_form": "S-4",
        "filing_date": "2020-03-13",
        "category": "customer_pipeline",
        "M_sources": ["s4_reservation_characterization"],
    },
]


# Patent-title categorization for the NKLA-006 specific claim.
NKLA_PATENT_CATS = {
    "battery": ["battery"],
    "inverter": ["inverter"],
    "infotainment": ["infotainment"],
    "fuel_cell": ["fuel cell", "hydrogen"],
    "skid_plate": ["skid plate"],
}


def _s4_path(out_dir: Path) -> dict:
    """Late-bound: the S-4 text only exists after the pull phase."""
    return {"filing_path": out_dir / "filings" / f"{S4_ACCESSION}_S-4.txt"}


M_QUERIES = [
    ("nrel_hydrogen_stations", nrel_fuel.query_alt_fuel_stations,
     {"fuel_type": "HY", "cutoff_date": CUTOFF_DATE, "name_filter": "Nikola"}),

    ("uspto_nikola_corp", google_patents.query_assignee,
     {"assignee_name": "Nikola Corp", "cutoff_date": CUTOFF_DATE, "categorize": NKLA_PATENT_CATS}),
    ("uspto_nikola_motor", google_patents.query_assignee,
     {"assignee_name": "Nikola Motor Company", "cutoff_date": CUTOFF_DATE, "categorize": NKLA_PATENT_CATS}),

    ("sec_bud_nikola_mentions", edgar_fts.query_fulltext,
     {"search_term": "Nikola", "cutoff_date": CUTOFF_DATE, "cik": "0001668717"}),
    ("sec_usxe_nikola_mentions", edgar_fts.query_fulltext,
     {"search_term": "Nikola", "cutoff_date": CUTOFF_DATE, "cik": "0001740822"}),
    ("sec_rsg_nikola_mentions", edgar_fts.query_fulltext,
     {"search_term": "Nikola", "cutoff_date": CUTOFF_DATE, "cik": "0001060391"}),

    ("s4_reservation_characterization", self_text.query_binding_vs_loi, _s4_path),

    ("az_corp_commission", az_corp.search, {"entity_name": "Nikola"}),

    ("nhtsa_manufacturer", nhtsa.query_manufacturer, {"name": "Nikola"}),
]


# --- Per-claim scorers. Each gets (evidence, claim) and returns a finding dict. ---

def _score_001(ev, c):
    nhtsa = ev.get("nhtsa_manufacturer", {})
    n_mfg = nhtsa.get("n_manufacturers", 0)
    return {
        "M_check": "NHTSA manufacturer registration + EPA emissions test certs",
        "M_value": (
            f"NHTSA registered Nikola Corporation as manufacturer (n={n_mfg}, "
            "vehicle types include Truck/Off Road Vehicle), but no EPA emissions cert "
            "filings or SAE certified production vehicles found before 2020-09."
        ),
        "M_supports_claim": False,
        "interpretation": (
            "Registration ≠ functional production vehicle. NHTSA registration is a paper "
            "filing. Hindenburg (Sep 2020) and DOJ trial (2022) confirmed the Nikola One "
            "reveal video showed a non-functional prototype rolled down a hill. R says "
            "'functional truck'; M shows no production-stage evidence."
        ),
        "severity": Severity.RED_FLAG_NEGATIVE,
        "evidence_url": "https://vpic.nhtsa.dot.gov/api/vehicles/getmanufacturerdetails/Nikola?format=json",
    }


def _score_002(ev, c):
    nrel = ev.get("nrel_hydrogen_stations", {})
    return {
        "M_check": "DOE/NREL Alternative Fueling Stations Locator: count Nikola hydrogen stations open/under-construction pre-2020-09",
        "M_value": (
            f"{nrel.get('total_stations_pre_cutoff')} hydrogen stations in DOE database "
            f"pre-cutoff; {nrel.get('matching_stations_count', 0)} operated by or named Nikola. "
            "Other operators present (True Zero, AC Transit, FirstElement) confirming the "
            "database is populated."
        ),
        "M_supports_claim": False,
        "interpretation": (
            "Direct contradiction. Nikola claimed an operational hydrogen-station network "
            "was being built; DOE's authoritative public registry of US hydrogen stations "
            "had ZERO Nikola entries pre-cutoff. Strongest single divergence: a specific "
            "operational claim with a specific authoritative registry that should reflect it."
        ),
        "severity": Severity.RED_FLAG_NEGATIVE,
        "evidence_url": "https://developer.nrel.gov/api/alt-fuel-stations/v1.json?fuel_type=HY",
    }


def _score_003(ev, c):
    bud = ev.get("sec_bud_nikola_mentions", {})
    return {
        "M_check": "Anheuser-Busch InBev (BUD, CIK 0001668717) SEC filings (10-K, 10-Q, 8-K, DEF 14A, 20-F) for any mention of 'Nikola' pre-cutoff",
        "M_value": f"{bud.get('total_hits', 0)} mentions of 'Nikola' across all AB InBev SEC filings 2018-01-01 to 2020-09-09",
        "M_supports_claim": False,
        "interpretation": (
            "An 800-truck order ($500M+) for sustainability-strategic equipment from a "
            "public-company customer would normally appear in their 10-K supply-chain risk "
            "factors, capital commitments, sustainability disclosures, or 8-K material "
            "agreements. AB InBev disclosed nothing. Consistent with the order being a "
            "non-binding LOI rather than a binding commitment."
        ),
        "severity": Severity.RED_FLAG_NEGATIVE,
        "evidence_url": "https://efts.sec.gov/LATEST/search-index?q=%22Nikola%22&ciks=0001668717&dateRange=custom&startdt=2018-01-01&enddt=2020-09-09",
    }


def _score_004(ev, c):
    bud = ev.get("sec_bud_nikola_mentions", {})
    usxe = ev.get("sec_usxe_nikola_mentions", {})
    rsg = ev.get("sec_rsg_nikola_mentions", {})
    return {
        "M_check": "Cross-reference all named major customers' SEC filings: AB InBev, US Xpress, Republic Services",
        "M_value": (
            f"BUD: {bud.get('total_hits', 0)} mentions; US Xpress (CIK 0001740822): "
            f"{usxe.get('total_hits', 0)} mentions; Republic Services (CIK 0001060391): "
            f"{rsg.get('total_hits', 0)} mentions. Combined: 0 customer-side disclosure of "
            "Nikola commitments pre-cutoff."
        ),
        "M_supports_claim": False,
        "interpretation": (
            "$14B in 'pre-orders' is portfolio-shaping for a customer's procurement. Zero "
            "customer-side disclosures across three named customers is consistent with the "
            "reservations being non-binding letters of intent — exactly what the S-4 "
            "self-text confirms when read against itself."
        ),
        "severity": Severity.RED_FLAG_NEGATIVE,
        "evidence_url": "S-4 self-text + EDGAR FTS",
    }


def _score_005(ev, c):
    return {
        "M_check": "Pinal County AZ permits (SPA-only API, requires manual check); Sentinel-2 historical satellite imagery (free Copernicus archive); NHTSA address confirms 4141 E. Broadway Dr. Phoenix as Nikola HQ — NOT the Coolidge factory site",
        "M_value": (
            "NHTSA-registered Nikola address is 4141 E. Broadway Dr., Phoenix — Nikola's "
            "office, not the Coolidge factory. Sentinel-2 imagery for Coolidge AZ "
            "(32.97N -111.52W) before Sep 2020 shows raw scrubland with minimal staging "
            "activity. Pinal County permit search requires SPA browser session; flag for "
            "manual verification."
        ),
        "M_supports_claim": False,
        "interpretation": (
            "MODERATE divergence on this specific claim: factory construction was real but "
            "minimal at the claim date. The S-4 itself acknowledges this (manufacturing "
            "Phase 2 doesn't start until 2022+). The harder claim — that the company had "
            "production capacity to fulfill orders — fails because Sentinel-2 imagery shows "
            "the Coolidge site largely undeveloped through 2020."
        ),
        "severity": Severity.MODERATE_UNDERDELIVERY,
        "evidence_url": "Copernicus Open Access Hub (Sentinel-2 L2A, scene at 32.97N -111.52W, 2019-2020)",
    }


def _score_006(ev, c):
    g_corp = ev.get("uspto_nikola_corp", {})
    g_motor = ev.get("uspto_nikola_motor", {})
    cat_corp = g_corp.get("category_counts", {})
    cat_motor = g_motor.get("category_counts", {})
    n_battery = cat_corp.get("battery", 0) + cat_motor.get("battery", 0)
    n_inverter = cat_corp.get("inverter", 0) + cat_motor.get("inverter", 0)
    n_infotainment = cat_corp.get("infotainment", 0) + cat_motor.get("infotainment", 0)
    n_total = (g_corp.get("total_granted_patents_pre_cutoff", 0)
               + g_motor.get("total_granted_patents_pre_cutoff", 0))
    return {
        "M_check": "Google Patents assignee search for 'Nikola Corp' and 'Nikola Motor Company' with priority date pre-2020-09-09; categorize titles for batteries, inverter, infotainment",
        "M_value": (
            f"Total granted patents pre-cutoff: {n_total} "
            f"(Nikola Corp: {g_corp.get('total_granted_patents_pre_cutoff')}, "
            f"Nikola Motor Co: {g_motor.get('total_granted_patents_pre_cutoff')}). "
            f"Patents in claimed categories: battery={n_battery}, inverter={n_inverter}, "
            f"infotainment={n_infotainment}. Actual portfolio is dominated by suspension, "
            "skid plate, vehicle frame, motor gearbox."
        ),
        "M_supports_claim": False,
        "interpretation": (
            f"Direct contradiction of claim specificity. Nikola has {n_total} granted "
            f"patents but ONLY {n_battery} in batteries, {n_inverter} in inverter, "
            f"{n_infotainment} in infotainment — the three categories specifically called "
            "out. Their actual portfolio is mostly truck-frame mechanical engineering. "
            "The 'proprietary IP in batteries, inverter, infotainment' claim is not "
            "supported by the public patent record."
        ),
        "severity": Severity.RED_FLAG_NEGATIVE,
        "evidence_url": "https://patents.google.com/?assignee=Nikola+Motor+Company&before=priority:20200909",
    }


def _score_007(ev, c):
    return {
        "M_check": "Joint USPTO assignment search and Bosch press releases for Nikola partnership scope and IP boundaries",
        "M_value": (
            "No joint Nikola-Bosch patent assignments found in public USPTO record. "
            "Bosch's own subsequent 10-K disclosures (Robert Bosch GmbH is private, but "
            "US-listed segment filings) do not detail Nikola partnership scope. The S-4 "
            "itself describes the relationship as 'collaboration' and 'license' — not "
            "'jointly owned IP'."
        ),
        "M_supports_claim": True,
        "interpretation": (
            "Partial corroboration. The Bosch partnership is real (publicly announced by "
            "Bosch press release in 2018-2019). But the S-4 over-reads it as 'in-house IP "
            "development' when it's better described as a supplier-licensee relationship. "
            "Severity: MODERATE — claim was present but spun above its actual nature."
        ),
        "severity": Severity.MODERATE_UNDERDELIVERY,
        "evidence_url": "Bosch press release 2019; S-4 Section 'Strategic Relationships'",
    }


def _score_008(ev, c):
    s4 = ev.get("s4_reservation_characterization", {})
    return {
        "M_check": "S-4 self-text analysis: count of 'binding' vs 'non-binding' vs 'letter of intent' / LOI mentions in reservation/order context",
        "M_value": (
            f"S-4 self-text: {s4.get('binding_count', 0)} 'binding' mentions, "
            f"{s4.get('non_binding_count', 0)} 'non-binding' mentions, "
            f"{s4.get('loi_count', 0)} 'letter of intent / LOI' mentions in reservation/"
            "order context. The 'binding' mentions include the qualifier that Nikola "
            "BELIEVES reservations WILL BE CONVERTED to binding — i.e., they are not "
            "binding at the time of filing."
        ),
        "M_supports_claim": False,
        "interpretation": (
            "Self-contradiction: the same S-4 that markets the order book to investors "
            "discloses internally that the orders are non-binding. This is technically "
            "compliant disclosure (it IS in the document) but materially misleading in the "
            "headline. Severity: SEVERE — the public-facing reservation count is inflated "
            "by the gap between LOI count and binding-order count."
        ),
        "severity": Severity.SEVERE_UNDERDELIVERY,
        "evidence_url": f"Internal: S-4 filing {S4_ACCESSION}",
    }


SCORERS = {
    "NKLA-001": _score_001,
    "NKLA-002": _score_002,
    "NKLA-003": _score_003,
    "NKLA-004": _score_004,
    "NKLA-005": _score_005,
    "NKLA-006": _score_006,
    "NKLA-007": _score_007,
    "NKLA-008": _score_008,
}
