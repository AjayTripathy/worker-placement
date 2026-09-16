"""v3 narrow-screen operational-capacity probe.

Universe: 12 chemistry-intensive small-to-mid-caps ($300M-$3B mcap)
where federal-registry permits SHOULD exist at the claimed revenue
scale. Two added "non-chemistry" names (FOR, MTW) included as
expected-low-permit controls.

Per-ticker subsidiary variants curated from 10-K Exhibit 21 / known
operating subsidiaries.
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
HERE = Path(__file__).parent


TARGETS = {
    # === lithium / battery materials (narrow-screen TARGETS) ===
    "SLI": {
        "company": "Standard Lithium",
        "mcap_b": 0.88, "rev_b": 0.0,
        "variants": ["Standard Lithium", "Smackover Lithium", "TETRA Smackover"],
        "claimed_locations": [("EL DORADO","AR")],
        "industry": "lithium",
    },
    "AMPX": {
        "company": "Amprius Technologies",
        "mcap_b": 2.21, "rev_b": 0.09,
        "variants": ["Amprius Technologies", "Amprius"],
        "claimed_locations": [("FREMONT","CA"), ("BRIGHTON","CO")],
        "industry": "battery_materials",
    },
    "EOSE": {
        "company": "Eos Energy",
        "mcap_b": 2.57, "rev_b": 0.16,
        "variants": ["Eos Energy", "Eos Energy Enterprises", "Eos Energy Storage"],
        "claimed_locations": [("TURTLE CREEK","PA"), ("EDISON","NJ")],
        "industry": "battery_chemistry",
    },

    # === specialty chemicals — established operators (POSITIVE CONTROLS) ===
    "SCL": {
        "company": "Stepan Company",
        "mcap_b": 1.13, "rev_b": 2.34,
        "variants": ["Stepan Company", "Stepan"],
        "claimed_locations": [("MILLSDALE","IL"), ("FIELDSBORO","NJ"),
                              ("ELWOOD","IL"), ("LATEXO","TX"),
                              ("ANAHEIM","CA"), ("STALYBRIDGE","GB")],
        "industry": "specialty_chem_control",
    },
    "IOSP": {
        "company": "Innospec",
        "mcap_b": 1.95, "rev_b": 1.79,
        "variants": ["Innospec", "Octel Performance", "Aroma Performance"],
        "claimed_locations": [("HIGH POINT","NC"), ("SALISBURY","NC"),
                              ("ARLINGTON HEIGHTS","IL"), ("LEUNA","DE")],
        "industry": "specialty_chem_control",
    },
    "KOP": {
        "company": "Koppers",
        "mcap_b": 0.79, "rev_b": 1.88,
        "variants": ["Koppers"],
        "claimed_locations": [("PITTSBURGH","PA"), ("STICKNEY","IL"),
                              ("CARBONDALE","IL"), ("FOLLANSBEE","WV"),
                              ("ROANOKE","VA")],
        "industry": "specialty_chem_control",
    },
    "OEC": {
        "company": "Orion Engineered Carbons",
        "mcap_b": 0.39, "rev_b": 1.79,
        "variants": ["Orion Engineered Carbons", "Orion Carbons"],
        "claimed_locations": [("BORGER","TX"), ("BELPRE","OH"),
                              ("ORANGE","TX"), ("LAKE CHARLES","LA")],
        "industry": "specialty_chem_control",
    },
    "NGVT": {
        "company": "Ingevity",
        "mcap_b": 2.35, "rev_b": 1.18,
        "variants": ["Ingevity"],
        "claimed_locations": [("CHARLESTON","SC"), ("CRESCENT CITY","FL"),
                              ("COVINGTON","VA"), ("WICKLIFFE","KY")],
        "industry": "specialty_chem_control",
    },

    # === industrial chemistry (TARGETS — should have permits if claims real) ===
    "LXU": {
        "company": "LSB Industries",
        "mcap_b": 1.01, "rev_b": 0.64,
        "variants": ["LSB Industries", "El Dorado Chemical", "Pryor Chemical",
                     "Cherokee Nitrogen", "EDC Ag Products"],
        "claimed_locations": [("EL DORADO","AR"), ("PRYOR","OK"),
                              ("CHEROKEE","AL")],
        "industry": "nitrogen_chemistry",
    },
    "ASIX": {
        "company": "AdvanSix",
        "mcap_b": 0.58, "rev_b": 1.55,
        "variants": ["AdvanSix", "AdvanSix Resins", "AdvanSix Inc"],
        "claimed_locations": [("HOPEWELL","VA"), ("FRANKFORD","PA"),
                              ("CHESTERFIELD","VA")],
        "industry": "caprolactam_chemistry",
    },
    "TROX": {
        "company": "Tronox",
        "mcap_b": 1.26, "rev_b": 2.92,
        "variants": ["Tronox", "Tronox Pigments", "Tronox Mineral",
                     "Tronox Holdings"],
        "claimed_locations": [("HAMILTON","MS"), ("BOTLEK","NL"),
                              ("STALLINGBOROUGH","GB"), ("KWINANA","AU")],
        "industry": "titanium_dioxide_chemistry",
    },
    "AMSC": {
        "company": "American Superconductor",
        "mcap_b": 2.37, "rev_b": 0.28,
        "variants": ["American Superconductor", "AMSC"],
        "claimed_locations": [("AYER","MA"), ("DEVENS","MA"),
                              ("BOLOGNA","IT"), ("AUSTRIA","AT")],
        "industry": "superconductor_chemistry",
    },

    # === non-chemistry controls (expected LOW permits) ===
    "FOR": {
        "company": "Forestar Group",
        "mcap_b": 1.30, "rev_b": 1.71,
        "variants": ["Forestar Group", "Forestar"],
        "claimed_locations": [("ARLINGTON","TX")],
        "industry": "real_estate_nonchem_control",
    },
    "MTW": {
        "company": "Manitowoc",
        "mcap_b": 0.43, "rev_b": 2.26,
        "variants": ["Manitowoc", "Manitowoc Cranes", "Grove Worldwide"],
        "claimed_locations": [("MANITOWOC","WI"), ("SHADY GROVE","PA"),
                              ("WILHELMSHAVEN","DE")],
        "industry": "industrial_machinery_control",
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


def _tri_by_name(variant: str) -> list[dict]:
    enc = urllib.parse.quote(variant.upper())
    return _get(f"tri_facility/facility_name/CONTAINING/{enc}/JSON")


def _ghgrp_by_name(variant: str) -> list[dict]:
    enc = urllib.parse.quote(variant.upper())
    return _get(f"PUB_DIM_FACILITY/facility_name/CONTAINING/{enc}/JSON")


def _frs_by_loc(city: str, state: str) -> list[dict]:
    return _get(f"FRS_FACILITY_SITE/state_code/{state.upper()}/city_name/{city.upper()}/JSON")


# Substring-noise prefixes / patterns observed in v2 probe + speculative new ones.
_NOISE_PATTERNS = [
    re.compile(r"\bFORESTAR(\s|$)"),     # FOR — many "Forestar" road / property names
    re.compile(r"^MANITOWOC\s+(CO|COUNTY|MARITIME)"),  # Manitowoc as a Wisconsin town
    re.compile(r"\bGROVE\b(?!\s+WORLDWIDE)"),  # avoid Manitowoc->Grove false positives
    re.compile(r"^STEPAN\s+[A-Z]\."),    # personal-name patterns (Stepan J., Stepan F.)
    re.compile(r"^KOPPEL\s"),             # close to Koppers, different company
]


def _is_relevant(name: str, variants: list[str]) -> bool:
    """Word-boundary-strict match against any variant, with noise filtering."""
    upper = (name or "").upper()
    if not any(re.search(r"\b" + re.escape(v.upper()) + r"\b", upper) for v in variants):
        return False
    for pat in _NOISE_PATTERNS:
        if pat.search(upper):
            return False
    return True


def probe(tk: str, meta: dict) -> dict:
    variants = meta["variants"]
    print(f"\n=== {tk} ({meta['company']}) — {len(variants)} variants ===")
    frs_hits, tri_hits, ghg_hits = [], [], []
    s_frs, s_tri, s_ghg = set(), set(), set()
    for v in variants:
        for r in _frs_by_name(v):
            rid = r.get("registry_id")
            if rid in s_frs or not _is_relevant(r.get("primary_name"), variants):
                continue
            s_frs.add(rid); frs_hits.append(r)
        for r in _tri_by_name(v):
            rid = r.get("tri_facility_id")
            if rid in s_tri or not _is_relevant(r.get("facility_name"), variants):
                continue
            s_tri.add(rid); tri_hits.append(r)
        for r in _ghgrp_by_name(v):
            rid = r.get("facility_id")
            if rid in s_ghg or not _is_relevant(r.get("facility_name"), variants):
                continue
            s_ghg.add(rid); ghg_hits.append(r)
        time.sleep(0.1)

    location_audit = []
    if not frs_hits and meta.get("claimed_locations"):
        print(f"  ⚠ no name-variant hits — running location audit")
        for city, state in meta["claimed_locations"]:
            facs = _frs_by_loc(city, state)
            relevant = [f for f in facs if _is_relevant(f.get("primary_name"), variants)]
            location_audit.append({
                "city": city, "state": state, "n_at_loc": len(facs),
                "n_company": len(relevant),
                "company_facilities": [{"name": f.get("primary_name"),
                                        "address": f.get("location_address")} for f in relevant[:3]],
            })
            time.sleep(0.1)

    rev = (meta.get("rev_b") or 0) * 1e9
    mcap = (meta.get("mcap_b") or 0) * 1e9
    rev_per_frs = (rev / len(frs_hits)) if frs_hits else None

    result = {
        "ticker": tk,
        "company": meta["company"],
        "industry": meta["industry"],
        "mcap": mcap,
        "revenue": rev,
        "variants_probed": variants,
        "n_FRS": len(frs_hits),
        "n_TRI": len(tri_hits),
        "n_GHGRP": len(ghg_hits),
        "rev_per_FRS": rev_per_frs,
        "location_audit": location_audit,
        "frs_sample": [{"name": f.get("primary_name"), "city": f.get("city_name"),
                        "state": f.get("state_code"), "address": f.get("location_address")}
                       for f in frs_hits[:8]],
    }
    print(f"  FRS={len(frs_hits)}  TRI={len(tri_hits)}  GHGRP={len(ghg_hits)}  "
          f"mcap=${mcap/1e9:.2f}B  rev=${rev/1e9:.2f}B  "
          f"rev/FRS={'n/a' if rev_per_frs is None else '$%.1fM' % (rev_per_frs/1e6)}")
    for f in result["frs_sample"][:5]:
        nm = (f.get("name") or "?")[:50]
        c = f.get("city") or "?"; s = f.get("state") or "?"
        print(f"     {nm:50s} | {c} {s}")
    return result


def main():
    results = []
    for tk, meta in TARGETS.items():
        try:
            r = probe(tk, meta)
        except Exception as e:
            r = {"ticker": tk, "error": str(e)}
        results.append(r)
        (HERE / f"probe_{tk}.json").write_text(json.dumps(r, indent=2, default=str))
        time.sleep(0.2)
    (HERE / "probe_all.json").write_text(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
