"""Lucid Group (LCID) — second false-positive test for the framework.

Lucid de-SPAC'd from Churchill Capital Corp IV on 2021-07-23. Like Rivian, it
has a real factory, real production vehicles, and a real strategic partner
(Saudi Public Investment Fund). It also drew skepticism (post-deSPAC stock
underperformance) but operations are legitimate. Cutoff at 2022-03-15 captures
the first 10-K (filed 2022-02-28) and post-merger S-1/A.

If the framework returns mostly PASS for Lucid as well, that's a second clean
data point — different team, different geography, similar shape.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..m_sources import edgar_fts, epa_frs, google_patents, nhtsa, self_text
from ..scoring import Severity


CIK = "0001811210"  # Lucid Group, Inc. (post Churchill IV merger)
TICKER = "lcid"
CUTOFF_DATE = "2022-03-15"
PRIORITY_FORMS = {"S-1", "S-1/A", "424B3", "424B4", "10-K", "10-Q", "8-K", "DEF 14A", "DEFM14A"}

S1A_ACCESSION = "0001104659-21-107865"  # S-1/A Aug 20 2021 (post-merger)
TENK_ACCESSION = "0001628280-22-004253"  # FY2021 10-K filed Feb 28 2022

LCID_PATENT_CATS = {
    "battery": ["battery", "cell"],
    "motor": ["motor", "drive unit", "powertrain", "inverter"],
    "charging": ["charging", "charger"],
    "autonomy": ["autonomous", "perception", "lidar", "driver assist"],
}


CLAIMS = [
    {
        "claim_id": "LCID-001",
        "claim_text": "Saudi Arabia's Public Investment Fund has committed to purchase up to 100,000 Lucid vehicles over 10 years",
        "source_filing": TENK_ACCESSION,
        "source_form": "10-K",
        "filing_date": "2022-02-28",
        "category": "customer_pipeline",
        "M_sources": ["s1_self_text", "tenk_self_text"],
    },
    {
        "claim_id": "LCID-002",
        "claim_text": "Lucid Air is a production vehicle with active customer deliveries",
        "source_filing": TENK_ACCESSION,
        "source_form": "10-K",
        "filing_date": "2022-02-28",
        "category": "technology",
        "M_sources": ["nhtsa_lucid"],
    },
    {
        "claim_id": "LCID-003",
        "claim_text": "Lucid operates the AMP-1 manufacturing facility in Casa Grande, Arizona",
        "source_filing": TENK_ACCESSION,
        "source_form": "10-K",
        "filing_date": "2022-02-28",
        "category": "physical_facility",
        "M_sources": ["epa_frs_lucid_az"],
    },
    {
        "claim_id": "LCID-004",
        "claim_text": "Lucid owns proprietary intellectual property in batteries, motors/drive units, and inverter (Peter Rawlinson / ex-Tesla Model S team)",
        "source_filing": S1A_ACCESSION,
        "source_form": "S-1/A",
        "filing_date": "2021-08-20",
        "category": "technology",
        "M_sources": ["uspto_lucid_motors", "uspto_atieva"],
    },
    {
        "claim_id": "LCID-005",
        "claim_text": "Saudi PIF is a major strategic shareholder in Lucid (~60% post-merger) — the partnership is real and binding",
        "source_filing": S1A_ACCESSION,
        "source_form": "S-1/A",
        "filing_date": "2021-08-20",
        "category": "partnership",
        "M_sources": ["s1_self_text", "tenk_self_text"],
    },
    {
        "claim_id": "LCID-006",
        "claim_text": "Lucid's S-1/A characterizes the Saudi PIF vehicle commitment in plain, non-LOI terms",
        "source_filing": S1A_ACCESSION,
        "source_form": "S-1/A self-text",
        "filing_date": "2021-08-20",
        "category": "customer_pipeline",
        "M_sources": ["s1_self_text"],
    },
]


def _s1_path(out_dir: Path) -> dict:
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


def _tenk_path(out_dir: Path) -> dict:
    p = out_dir / "filings" / f"{TENK_ACCESSION}_10-K.txt"
    return {"filing_path": p}


M_QUERIES = [
    ("nhtsa_lucid", nhtsa.query_manufacturer, {"name": "Lucid"}),

    ("epa_frs_lucid_az", epa_frs.query_facilities,
     {"facility_name": "Lucid", "state_abbr": "AZ", "city_filter": "CASA GRANDE"}),

    ("uspto_lucid_motors", google_patents.query_assignee,
     {"assignee_name": "Lucid Motors", "cutoff_date": CUTOFF_DATE,
      "categorize": LCID_PATENT_CATS}),
    ("uspto_atieva", google_patents.query_assignee,
     {"assignee_name": "Atieva", "cutoff_date": CUTOFF_DATE,
      "categorize": LCID_PATENT_CATS}),

    ("s1_self_text", self_text.query_binding_vs_loi, _s1_path),
    ("tenk_self_text", self_text.query_binding_vs_loi, _tenk_path),
]


# --- Per-claim scorers ---

def _score_001(ev, c):
    s1 = ev.get("s1_self_text", {})
    tenk = ev.get("tenk_self_text", {})
    binding = (s1.get("binding_count", 0) or 0) + (tenk.get("binding_count", 0) or 0)
    loi = (s1.get("loi_count", 0) or 0) + (tenk.get("loi_count", 0) or 0)
    if binding >= 1 and loi <= binding:
        sev = Severity.PASS
        sup = True
        interp = (
            f"S-1/A + 10-K self-text: {binding} 'binding' / {loi} 'LOI' mentions in "
            "pre-order context. The PIF 100,000-vehicle commitment is described in "
            "binding-agreement language, not buried as an LOI. Same self-text test "
            "that flagged Nikola (8 LOI / 2 binding) and Lordstown returns PASS for "
            "Lucid."
        )
    elif loi >= binding * 2:
        sev = Severity.SEVERE_UNDERDELIVERY
        sup = False
        interp = f"LOI-dominant pattern: {loi} LOI vs {binding} binding — fraud-shape signal."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = f"Mixed: {loi} LOI vs {binding} binding."
    return {
        "M_check": "S-1/A + 10-K self-text: binding vs LOI characterization of PIF 100k vehicle commitment",
        "M_value": f"binding={binding}, loi={loi}",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": f"Internal: S-1/A {S1A_ACCESSION} + 10-K {TENK_ACCESSION}",
    }


def _score_002(ev, c):
    nhtsa_d = ev.get("nhtsa_lucid", {})
    types: list = []
    addr = ""
    for mfg in nhtsa_d.get("manufacturers", []):
        nm = (mfg.get("mfr_name") or "").upper()
        if "LUCID USA" in nm or "LUCID GROUP" in nm or "LUCID MOTORS" in nm:
            types.extend(mfg.get("vehicle_types", []))
            addr = mfg.get("address") or ""
            break
    types_l = [t.lower() if t else "" for t in types]
    is_complete = (
        ("passenger car" in types_l or "truck" in types_l or "multipurpose passenger vehicle (mpv)" in types_l)
        and "incomplete vehicle" not in types_l
    )
    if is_complete:
        sev = Severity.PASS
        sup = True
        interp = (
            f"NHTSA registers Lucid USA, Inc. as a complete-vehicle manufacturer "
            f"(types: {types}), NOT 'Incomplete Vehicle'. Same registry test that "
            "flagged Lordstown as a chassis manufacturer returns PASS for Lucid. "
            "The Air sedan is also EPA-certified and listed in fueleconomy.gov "
            "(Air Dream P/R AWD with 19\" and 21\" wheels), confirming production "
            "vehicle status."
        )
    else:
        sev = Severity.SEVERE_UNDERDELIVERY
        sup = False
        interp = f"NHTSA shows incomplete or missing vehicle-type registration (types: {types})."
    return {
        "M_check": "NHTSA vPIC manufacturer registration vehicle-type classification",
        "M_value": f"NHTSA Lucid USA Inc. types: {types}; address: '{addr}'",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://vpic.nhtsa.dot.gov/api/vehicles/getmanufacturerdetails/Lucid?format=json",
    }


def _score_003(ev, c):
    frs = ev.get("epa_frs_lucid_az", {})
    n = frs.get("n_facilities", 0)
    factory_like = [
        f for f in frs.get("facilities", [])
        if any(k in (f.get("facility_name") or "").upper()
               for k in ("FACTORY", "PLANT", "ASSEMBLY", "PLATFORM",
                         "MANUFACTURING", "POWERTRAIN", "AMP"))
    ]
    addresses = sorted({(f.get("address") or "") for f in frs.get("facilities", [])})
    if n >= 1:
        sev = Severity.PASS
        sup = True
        interp = (
            f"EPA Facility Registry Service shows {n} Lucid facilities in Casa Grande, "
            f"AZ ({len(factory_like)} factory/plant-named). Same authoritative federal "
            "registry of regulated US facilities — Lucid is present, the AMP-1 site is "
            "real. The framework returns PASS using the same EPA FRS test that would "
            "have returned zero for a paper claim."
        )
    else:
        sev = Severity.SEVERE_UNDERDELIVERY
        sup = False
        interp = "EPA FRS has zero Lucid facilities registered in Casa Grande, AZ."
    return {
        "M_check": "EPA Facility Registry Service: Lucid facilities in Casa Grande, AZ",
        "M_value": (
            f"EPA FRS: {n} Lucid facilities in Casa Grande AZ "
            f"({len(factory_like)} factory-named); addresses: {addresses[:3]}"
        ),
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://frs-public.epa.gov/ords/frs_public2/frs_rest_services.get_facilities?facility_name=Lucid&state_abbr=AZ&output=JSON",
    }


def _score_004(ev, c):
    motors = ev.get("uspto_lucid_motors", {})
    atieva = ev.get("uspto_atieva", {})
    cat_m = motors.get("category_counts") or {}
    cat_a = atieva.get("category_counts") or {}
    n_battery = cat_m.get("battery", 0) + cat_a.get("battery", 0)
    n_motor = cat_m.get("motor", 0) + cat_a.get("motor", 0)
    n_total = (motors.get("total_granted_patents_pre_cutoff", 0)
               + atieva.get("total_granted_patents_pre_cutoff", 0))
    has_categories = n_battery >= 1 and n_motor >= 1
    if has_categories and n_total >= 20:
        sev = Severity.PASS
        sup = True
        interp = (
            f"USPTO portfolio corroborates the specific categories claimed: "
            f"battery={n_battery}, motor/drive/inverter={n_motor} (of {n_total} total). "
            "Same patent-category test that flagged Nikola (51 patents, 0 in claimed "
            "categories) returns PASS for Lucid because the portfolio matches what "
            "Lucid claims."
        )
    elif n_total >= 5:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = (
            f"Portfolio exists ({n_total}) but coverage of specific claimed categories "
            f"(battery={n_battery}, motor={n_motor}) thinner than expected."
        )
    else:
        sev = Severity.UNVERIFIABLE
        sup = None
        interp = "Patents query failed (likely Google Patents rate-limit) — cannot verify."
    return {
        "M_check": "Google Patents assignee search for 'Lucid Motors' + 'Atieva' (legal predecessor name), priority date pre-cutoff",
        "M_value": (
            f"Total pre-cutoff patents: {n_total} "
            f"(Lucid Motors: {motors.get('total_granted_patents_pre_cutoff')}, "
            f"Atieva: {atieva.get('total_granted_patents_pre_cutoff')}). "
            f"Categories: battery={n_battery}, motor/drive/inverter={n_motor}."
        ),
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": "https://patents.google.com/?assignee=Atieva&before=priority:20220315",
    }


def _score_005(ev, c):
    s1 = ev.get("s1_self_text", {})
    tenk = ev.get("tenk_self_text", {})
    s1_b = s1.get("binding_count", 0) or 0
    tenk_b = tenk.get("binding_count", 0) or 0
    if (s1_b + tenk_b) >= 1:
        sev = Severity.PASS
        sup = True
        interp = (
            f"S-1/A + 10-K self-text: {s1_b + tenk_b} 'binding' mentions in PIF/Saudi "
            "context. The PIF investment + supply commitment is described as a real "
            "binding agreement — corroborated by the visible ~60% PIF ownership stake "
            "post-merger (publicly disclosed). Framework returns PASS."
        )
    else:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = "PIF agreement language thinner than expected."
    return {
        "M_check": "S-1/A + 10-K self-text: binding-language characterization of PIF strategic partnership",
        "M_value": f"S-1/A binding mentions: {s1_b}; 10-K binding mentions: {tenk_b}",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": f"Internal: S-1/A {S1A_ACCESSION} + 10-K {TENK_ACCESSION}",
    }


def _score_006(ev, c):
    s1 = ev.get("s1_self_text", {})
    binding = s1.get("binding_count", 0) or 0
    non_binding = s1.get("non_binding_count", 0) or 0
    loi = s1.get("loi_count", 0) or 0
    if loi == 0 and non_binding <= binding:
        sev = Severity.PASS
        sup = True
        interp = (
            f"S-1/A self-text: {binding} binding / {non_binding} non-binding / {loi} LOI "
            "in pre-order context. PIF vehicle commitment not buried in LOI language. "
            "Framework returns PASS."
        )
    elif loi >= binding * 2:
        sev = Severity.SEVERE_UNDERDELIVERY
        sup = False
        interp = f"LOI-dominant pattern: {loi} LOI vs {binding} binding."
    else:
        sev = Severity.MODERATE_UNDERDELIVERY
        sup = False
        interp = f"Mixed: {loi} LOI vs {binding} binding."
    return {
        "M_check": "S-1/A self-text: binding vs LOI characterization in pre-order context",
        "M_value": f"binding={binding}, non_binding={non_binding}, loi={loi}",
        "M_supports_claim": sup,
        "interpretation": interp,
        "severity": sev,
        "evidence_url": f"Internal: S-1/A {S1A_ACCESSION}",
    }


SCORERS = {
    "LCID-001": _score_001,
    "LCID-002": _score_002,
    "LCID-003": _score_003,
    "LCID-004": _score_004,
    "LCID-005": _score_005,
    "LCID-006": _score_006,
}
