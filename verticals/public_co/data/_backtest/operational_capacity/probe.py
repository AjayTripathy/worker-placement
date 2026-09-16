"""Thorough EPA operational-capacity probe.

For each target company:
  1. Build name variants:
     - Parent ticker name (e.g. "Plug Power")
     - Parent + common suffixes (Power, Materials, Manufacturing, Fuel Cell,
       Electrolyzers, Mining, LLC, Inc, Corp)
     - Known/discovered subsidiary names (manually curated below; for v2
       this should auto-pull from 10-K Exhibit 21)
  2. Probe FRS (broadest), TRI (chemical-threshold), GHGRP (>25kt CO2e)
     for EACH variant
  3. Deduplicate hits by EPA registry ID across variants
  4. Filter: relevant hits = primary_name contains any of the variants
     AND not obvious-noise (Ballard road, Linde grove, etc.)
  5. Report per-target:
     - n_FRS_total, n_TRI_total, n_GHGRP_total
     - Top facility names + addresses
     - Revenue from yfinance.info
     - Revenue per facility

Skepticism rule: if a target shows 0 hits across all variants, do a
location-based reverse lookup (FRS by city+state) for any claimed plant
address before accepting NO_EPA_FOOTPRINT as a real signal.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}
BASE = "https://data.epa.gov/efservice"


# Known subsidiary names + claimed plant locations per target.
# Curated by reading each company's 10-K narrative + Exhibit 21 where
# possible. Where uncertain, lean conservative (more variants).
TARGETS = {
    # ====== Hydrogen / fuel-cell cohort ======
    "PLUG": {
        "company":   "Plug Power",
        "variants":  ["Plug Power", "Plug Power Electrolyzers", "Plug Power Limestone", "Plug Power East"],
        "claimed_locations": [
            ("LATHAM","NY"), ("ROCHESTER","NY"), ("CONCORD","MA"),
            ("WOODBINE","GA"), ("KINGSLAND","GA"), ("CHARLESTON","TN"),
            ("GRAHAM","TX"), ("CAMDEN","GA"),
        ],
        "industry": "hydrogen",
        "revenue_estimate": 891e6,  # FY23 reported
    },
    "FCEL": {
        "company":   "FuelCell Energy",
        "variants":  ["FuelCell Energy", "Fuelcell Energy", "FCE"],
        "claimed_locations": [("TORRINGTON","CT"), ("DANBURY","CT"), ("LONG BEACH","CA")],
        "industry":  "hydrogen",
        "revenue_estimate": 123e6,
    },
    "HYZN": {
        "company":   "Hyzon Motors",
        "variants":  ["Hyzon Motors", "Hyzon"],
        "claimed_locations": [("BOLINGBROOK","IL")],
        "industry":  "hydrogen",
        "revenue_estimate": 0.3e6,
    },
    "BE": {
        "company":   "Bloom Energy",
        "variants":  ["Bloom Energy"],
        "claimed_locations": [("SUNNYVALE","CA"), ("FREMONT","CA"), ("NEWARK","DE"), ("SAN JOSE","CA")],
        "industry":  "hydrogen",
        "revenue_estimate": 1.4e9,
    },
    "BLDP": {
        "company":   "Ballard Power",
        # Critical: Ballard files under SUBSIDIARY names, not parent
        "variants":  ["Ballard Power", "Ballard Fuel Cell", "Ballard Material",
                      "Ballard Mat", "Protonex"],
        "claimed_locations": [("BEND","OR"), ("LOWELL","MA"), ("BURNABY","BC")],
        "industry":  "hydrogen",
        "revenue_estimate": 102e6,
    },

    # ====== Solid-state / lithium battery ======
    "MVST": {
        "company":   "Microvast",
        "variants":  ["Microvast"],
        "claimed_locations": [("CLARKSVILLE","TN"), ("WINDSOR","CO"), ("ORLANDO","FL")],
        "industry":  "battery",
        "revenue_estimate": 306e6,
    },
    "ENVX": {
        "company":   "Enovix",
        "variants":  ["Enovix"],
        "claimed_locations": [("FREMONT","CA")],
        "industry":  "battery",
        "revenue_estimate": 7e6,
    },
    "SLDP": {
        "company":   "Solid Power",
        "variants":  ["Solid Power", "Solidpower"],
        "claimed_locations": [("THORNTON","CO"), ("LOUISVILLE","CO")],
        "industry":  "battery",
        "revenue_estimate": 17e6,
    },
    "QS": {
        "company":   "QuantumScape",
        "variants":  ["QuantumScape", "Quantumscape", "QSV"],
        "claimed_locations": [("SAN JOSE","CA")],
        "industry":  "battery",
        "revenue_estimate": 0.0,  # pre-revenue
    },
    "SES": {
        "company":   "SES AI",
        "variants":  ["SES AI", "Solidenergy Systems"],
        "claimed_locations": [("WOBURN","MA"), ("SHANGHAI","CN")],
        "industry":  "battery",
        "revenue_estimate": 3e6,
    },
    "LAC": {
        "company":   "Lithium Americas",
        "variants":  ["Lithium Americas", "Thacker Pass"],
        "claimed_locations": [("WINNEMUCCA","NV"), ("ORONOZ","NV")],
        "industry":  "lithium",
        "revenue_estimate": 0.0,
    },

    # ====== Defense / drone manufacturing ======
    "AIRO": {
        "company":   "AIRO Group",
        "variants":  ["AIRO", "AIRO Drone", "Sky-Watch", "Coastal Defense",
                      "Aspen Avionics", "Jaunt"],
        "claimed_locations": [("PHOENIX","AZ"), ("ALBUQUERQUE","NM")],
        "industry":  "defense",
        "revenue_estimate": 84e6,
    },

    # ====== EV / commercial vehicles ======
    "WKHS": {
        "company":   "Workhorse Group",
        "variants":  ["Workhorse Group", "Workhorse"],
        "claimed_locations": [("UNION CITY","IN"), ("LOVELAND","OH"), ("MORENO VALLEY","CA")],
        "industry":  "ev",
        "revenue_estimate": 13e6,
    },
    "BLNK": {
        "company":   "Blink Charging",
        "variants":  ["Blink Charging", "Blink Mobility"],
        "claimed_locations": [("BOWIE","MD"), ("LOS ANGELES","CA")],
        "industry":  "ev",
        "revenue_estimate": 140e6,
    },

    # ====== Quantum / specialty hardware ======
    "QBTS": {
        "company":   "D-Wave",
        "variants":  ["D-Wave", "D-Wave Systems"],
        "claimed_locations": [("PALO ALTO","CA"), ("BURNABY","BC")],
        "industry":  "quantum",
        "revenue_estimate": 9e6,
    },
    "IONQ": {
        "company":   "IonQ",
        "variants":  ["IonQ"],
        "claimed_locations": [("COLLEGE PARK","MD"), ("BOTHELL","WA")],
        "industry":  "quantum",
        "revenue_estimate": 41e6,
    },
    "RGTI": {
        "company":   "Rigetti",
        "variants":  ["Rigetti", "Rigetti Computing"],
        "claimed_locations": [("BERKELEY","CA"), ("FREMONT","CA")],
        "industry":  "quantum",
        "revenue_estimate": 11e6,
    },

    # ====== INDUSTRIAL CONTROLS — known operating scale ======
    "LIN": {
        "company":   "Linde",
        "variants":  ["Linde", "Linde Gas", "Linde Engineering", "Linde plc",
                      "Praxair"],
        "claimed_locations": [],   # global — too many to enumerate
        "industry":  "control_industrial_gas",
        "revenue_estimate": 33e9,
    },
    "APD": {
        "company":   "Air Products",
        "variants":  ["Air Products", "Air Products and Chemicals"],
        "claimed_locations": [],
        "industry":  "control_industrial_gas",
        "revenue_estimate": 12e9,
    },
    "ALB": {
        "company":   "Albemarle",
        "variants":  ["Albemarle"],
        "claimed_locations": [("MAGNOLIA","AR"), ("SILVER PEAK","NV"), ("KINGS MOUNTAIN","NC")],
        "industry":  "control_lithium",
        "revenue_estimate": 9.6e9,
    },
    "HDSN": {
        "company":   "Hudson Technologies",
        "variants":  ["Hudson Technologies"],
        "claimed_locations": [("PEARL RIVER","NY"), ("CHAMPAIGN","IL")],
        "industry":  "control_refrigerant",
        "revenue_estimate": 290e6,
    },
}


def _get(path: str) -> list:
    try:
        r = httpx.get(f"{BASE}/{path}", headers=HEADERS, timeout=30, follow_redirects=True)
        if r.status_code != 200:
            return []
        return r.json() or []
    except Exception:
        return []


def _frs_by_name(variant: str) -> list[dict]:
    enc = urllib.parse.quote(variant.upper())
    return _get(f"FRS_FACILITY_SITE/primary_name/CONTAINING/{enc}/JSON")


def _frs_by_loc(city: str, state: str) -> list[dict]:
    return _get(f"FRS_FACILITY_SITE/state_code/{state.upper()}/city_name/{city.upper()}/JSON")


def _tri_by_name(variant: str) -> list[dict]:
    enc = urllib.parse.quote(variant.upper())
    return _get(f"tri_facility/facility_name/CONTAINING/{enc}/JSON")


def _ghgrp_by_name(variant: str) -> list[dict]:
    enc = urllib.parse.quote(variant.upper())
    return _get(f"PUB_DIM_FACILITY/facility_name/CONTAINING/{enc}/JSON")


# Words that, when they're the WHOLE match context, indicate substring noise
# rather than the focal company. E.g. "Ballard" the road/neighborhood,
# "Linde" as part of "Linden", etc.
_KNOWN_NOISE_PREFIXES = {
    # Ballard: known to match Seattle neighborhood + surname
    "BIRD-JOHNSON", "SKILLS INC", "BALLARD COUNTY", "BALLARD ESTATES",
    "BALLARD PROPERTIES", "BALLARD SUBDIVISION", "BALLARD, RICHARD",
    "BALLARD, J ", "RAWLPLUG",
    # Linde / Linden / etc.
    "LINDEN", "LINDEMAN", "LINDEMANN",
    # "Plug" — known to match transmission-line "plug and abandonment"
    "PLUG IN ", "WECO LONG LINES PLUG", "ZOAR STORAGE WELLS PLUG",
    "PLUG ABANDONMENT", "PLUG & ABANDONMENT",
    # IONQ — none expected
}


def _is_relevant(name: str, variants: list[str]) -> bool:
    """Check if a facility primary_name matches one of the variants and isn't
    obvious noise."""
    upper = (name or "").upper()
    if not any(v.upper() in upper for v in variants):
        return False
    # Filter out known noise prefixes
    for noise in _KNOWN_NOISE_PREFIXES:
        if noise in upper:
            return False
    return True


def probe_target(ticker: str, meta: dict) -> dict:
    """Run the full probe for one target."""
    variants = meta["variants"]
    company  = meta["company"]
    print(f"\n=== {ticker} ({company}) — {len(variants)} variants ===")

    # Probe FRS by each variant
    frs_hits = []
    tri_hits = []
    ghg_hits = []
    seen_frs_ids = set()
    seen_tri_ids = set()
    seen_ghg_ids = set()

    for v in variants:
        for row in _frs_by_name(v):
            rid = row.get("registry_id")
            if rid in seen_frs_ids:
                continue
            if not _is_relevant(row.get("primary_name"), variants):
                continue
            seen_frs_ids.add(rid)
            frs_hits.append(row)
        for row in _tri_by_name(v):
            rid = row.get("tri_facility_id")
            if rid in seen_tri_ids:
                continue
            if not _is_relevant(row.get("facility_name"), variants):
                continue
            seen_tri_ids.add(rid)
            tri_hits.append(row)
        for row in _ghgrp_by_name(v):
            rid = row.get("facility_id")
            if rid in seen_ghg_ids:
                continue
            if not _is_relevant(row.get("facility_name"), variants):
                continue
            seen_ghg_ids.add(rid)
            ghg_hits.append(row)
        time.sleep(0.1)

    # Skepticism step: if 0 hits anywhere, probe each claimed location for
    # FRS facilities at that city+state and report who's there.
    location_audit = []
    if not frs_hits and meta.get("claimed_locations"):
        print(f"  ⚠ no name-variant hits — running location audit on {len(meta['claimed_locations'])} claimed locations")
        for city, state in meta["claimed_locations"]:
            facs = _frs_by_loc(city, state)
            relevant_here = [f for f in facs if _is_relevant(f.get("primary_name"), variants)]
            location_audit.append({
                "city":      city,
                "state":     state,
                "n_at_loc":  len(facs),
                "n_company": len(relevant_here),
                "company_facilities_at_loc": [
                    {"name": f.get("primary_name"), "address": f.get("location_address")}
                    for f in relevant_here[:3]
                ],
            })
            time.sleep(0.1)

    n_frs   = len(frs_hits)
    n_tri   = len(tri_hits)
    n_ghgrp = len(ghg_hits)
    rev     = meta.get("revenue_estimate") or 0
    rev_per_frs = (rev / n_frs) if n_frs else None

    result = {
        "ticker":               ticker,
        "company":              company,
        "industry":             meta.get("industry"),
        "variants_probed":      variants,
        "revenue_estimate":     rev,
        "n_FRS":                n_frs,
        "n_TRI":                n_tri,
        "n_GHGRP":              n_ghgrp,
        "rev_per_FRS_facility": rev_per_frs,
        "location_audit":       location_audit,
        "frs_sample":           [
            {"name": f.get("primary_name"), "city": f.get("city_name"),
             "state": f.get("state_code"), "address": f.get("location_address")}
            for f in frs_hits[:8]
        ],
        "tri_sample":           [
            {"name": f.get("facility_name"), "city": f.get("city_name"),
             "state": f.get("state_abbr")}
            for f in tri_hits[:5]
        ],
        "ghgrp_sample":         [
            {"name": f.get("facility_name"), "city": f.get("city"),
             "state": f.get("state")}
            for f in ghg_hits[:5]
        ],
    }
    print(f"  FRS={n_frs}  TRI={n_tri}  GHGRP={n_ghgrp}  rev=${rev/1e6:.0f}M  "
          f"rev/FRS=${rev_per_frs/1e6:.1f}M" if rev_per_frs else f"  FRS={n_frs}  TRI={n_tri}  GHGRP={n_ghgrp}  rev=${rev/1e6:.0f}M")
    for f in result["frs_sample"][:5]:
        print(f"     FRS: {f['name']:50s} | {f['city']} {f['state']}")
    return result


def main():
    out_dir = Path(__file__).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for tk, meta in TARGETS.items():
        try:
            r = probe_target(tk, meta)
        except Exception as e:
            r = {"ticker": tk, "error": str(e)}
        results.append(r)
        (out_dir / f"probe_{tk}.json").write_text(json.dumps(r, indent=2, default=str))
        time.sleep(0.2)

    (out_dir / "probe_all.json").write_text(json.dumps(results, indent=2, default=str))
    print(f"\nSaved {len(results)} probe results to {out_dir}")


if __name__ == "__main__":
    main()
