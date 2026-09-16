"""sgma_overlay — groundwater / SGMA water-supply AV-erosion screen for CA muni tax bases.

WHY. This is a SECOND macro assessed-value (AV) erosion channel, a sibling to the AI-bubble
cap-gains channel (capgains_beta.py) — but for AGRICULTURE rather than tech. California's
Sustainable Groundwater Management Act (SGMA, 2014) requires "critically overdrafted"
groundwater basins to reach sustainable pumping by 2040. In the San Joaquin Valley the gap
between historical pumping and the sustainable yield is large enough that hundreds of thousands
of acres of irrigated farmland are projected to be fallowed over the next ~15 years (PPIC: on
the order of 500k-900k acres of SJV cropland may come out of production). Fallowed/dryland
farmland is reassessed DOWN; permanent crops lose value; and the agricultural assessed-value
base that an unlimited ad-valorem GO levy rides on erodes slowly through ~2040.

THE TRANSMISSION CHANNEL (slow, not a default trigger):
  pumping cut (SGMA allocation / probation) -> irrigated acres fallowed -> ag land + improvement
  AV reassessed down (Williamson Act / Prop 8) -> levy base shrinks -> tax rate must rise to
  hold debt service constant -> the rate-ceiling / affordability stress shows up over a DECADE.
This is a TAIL on AV growth, NOT a near-term default flag. A GO bond over a critically-
overdrafted ag basin is still money-good in the near term; the screen flags the slow erosion
risk on the levy base, which matters for long-duration GO and for new-money capacity.

WHAT THIS IS NOT. It is not a claim that any specific district defaults. It is an exposure
flag: tax base is ag + ag sits over a basin under a binding pumping-cut mandate.

DATA SOURCE (authoritative, published, stable).
  California DWR, Bulletin 118 — "California's Critically Overdrafted Groundwater Basins."
  21 basins. Basin boundaries published 02/11/2019; the critically-overdrafted map published
  01/2020 (DWR COD-Basins.pdf). The SGMA basin-priority designation (High/Medium/Low/Very Low)
  comes from DWR's 2019 SGMA Basin Prioritization. These designations are stable and rarely
  change; we encode the published 21-basin critically-overdrafted list verbatim plus the
  county membership for each, and a county->ag-dependence proxy. We DO NOT hit a live service
  on every call; the static table carries its citation + as-of date and is cached to
  data/sgma_basins.json.

MAPPING. district -> basin is done by COUNTY first (cheap, reliable, and sufficient because the
critically-overdrafted basins are county-aligned in the SJV). LIMITATION: a county can contain
both a critically-overdrafted basin and non-overdrafted areas; county-level mapping therefore
flags the COUNTY's exposure, not a parcel-precise basin assignment. A lat/lon refinement hook is
provided (point-in-basin against DWR's B118 GIS) but county-level is the default and is stated as
such in the note. If county is unknown and cannot be inferred, we return UNVERIFIABLE (not clean).

THRESHOLDS (stated explicitly).
  - District in a Critically-Overdrafted basin AND ag-dependent (high/med)  -> sgma_flag="hard"
      => REVIEW for slow AV-erosion tail (NOT a default flag — framed as a long-dated levy-base
         drag through 2040).
  - District in a High-priority (non-critical) basin AND ag-dependent       -> sgma_flag="soft"
      => soft note only (prioritized basin, pumping mgmt likely but no acute overdraft mandate).
  - Critically-Overdrafted basin but county is NOT ag-dependent (urban)     -> sgma_flag="soft"
      => the AV base is not farmland, so the erosion channel is muted; note only.
  - No SGMA-critical / non-ag / urban coastal-LA-Bay                        -> sgma_flag=None.
  - County/basin cannot be determined                                       -> "UNVERIFIABLE".

OUTPUT FIELDS (sgma_exposure -> dict):
  sgma_basin       basin/subbasin name or None
  sgma_priority    "Critically Overdrafted" | "High" | "Medium" | "Low" | "Very Low" | None | "UNVERIFIABLE"
  sgma_critical    bool (in the published 21-basin critically-overdrafted list)
  ag_dependence    "high" | "medium" | "low" | "unknown"  (county/region ag-economy proxy)
  sgma_flag        "hard" | "soft" | None | "UNVERIFIABLE"
  sgma_note        plain-language explanation incl. mapping limitation + AV-erosion-tail framing

This module does NOT write into any shared integration file (issuer_credit_latest.json etc.).
Integration is done separately by the desk.
"""
from __future__ import annotations
import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CACHE = os.path.join(DATA_DIR, "sgma_basins.json")

# ---------------------------------------------------------------------------
# AUTHORITATIVE STATIC TABLE
# Source: California DWR, Bulletin 118 — "California's Critically Overdrafted
#   Groundwater Basins." Basin boundaries published 02/11/2019; COD map
#   published 01/2020. (DWR COD-Basins.pdf, water.ca.gov Bulletin 118 ->
#   Critically Overdrafted Basins.) 21 basins, verbatim with basin numbers.
# County membership per basin: DWR Bulletin 118 basin descriptions + DWR SGMA
#   basin pages (groundwaterexchange.org basin profiles).
# ---------------------------------------------------------------------------
SOURCE = ("California DWR, Bulletin 118 — California's Critically Overdrafted Groundwater "
          "Basins (COD-Basins map). Basin boundaries published 02/11/2019; COD map "
          "published 01/2020. SGMA priority designations from DWR 2019 SGMA Basin "
          "Prioritization.")
AS_OF = "2020-01 (COD map); basin boundaries 2019-02-11; SGMA prioritization 2019"

# The published 21 critically-overdrafted basins: number, name, member counties.
CRITICALLY_OVERDRAFTED = [
    ("3-001",    "Santa Cruz Mid-County",                       ["Santa Cruz"]),
    ("3-002.01", "Corralitos - Pajaro Valley",                  ["Santa Cruz", "Monterey", "San Benito"]),
    ("3-004.01", "Salinas Valley - 180/400 Foot Aquifer",       ["Monterey"]),
    ("3-004.06", "Salinas Valley - Paso Robles Area",           ["San Luis Obispo"]),
    ("3-008.01", "Los Osos Valley - Los Osos Area",             ["San Luis Obispo"]),
    ("3-013",    "Cuyama Valley",                                ["Santa Barbara", "San Luis Obispo", "Ventura", "Kern"]),
    ("4-004.02", "Santa Clara River Valley - Oxnard",           ["Ventura"]),
    ("4-006",    "Pleasant Valley",                              ["Ventura"]),
    ("5-022.01", "San Joaquin Valley - Eastern San Joaquin",    ["San Joaquin"]),
    ("5-022.04", "San Joaquin Valley - Merced",                 ["Merced"]),
    ("5-022.05", "San Joaquin Valley - Chowchilla",             ["Madera", "Merced"]),
    ("5-022.06", "San Joaquin Valley - Madera",                 ["Madera", "Fresno", "Merced"]),
    # Stanislaus REMOVED 2026-06-20: Delta-Mendota covers only the far-SW county edge (Patterson); the
    # populated districts (Modesto/Turlock/Ceres) sit in the EASTERN Modesto/Turlock subbasins, which are
    # HIGH-priority, NOT critically-overdrafted (DD-confirmed). County-level mapping over-flagged them.
    ("5-022.07", "San Joaquin Valley - Delta-Mendota",          ["Fresno", "Merced", "San Joaquin", "Madera", "San Benito"]),
    ("5-022.08", "San Joaquin Valley - Kings",                  ["Fresno", "Kings", "Tulare"]),
    ("5-022.09", "San Joaquin Valley - Westside",               ["Fresno", "Kings"]),
    ("5-022.11", "San Joaquin Valley - Kaweah",                 ["Tulare", "Kings"]),
    ("5-022.12", "San Joaquin Valley - Tulare Lake",            ["Kings"]),
    ("5-022.13", "San Joaquin Valley - Tule",                   ["Tulare"]),
    ("5-022.14", "San Joaquin Valley - Kern County",           ["Kern"]),
    ("6-054",    "Indian Wells Valley",                          ["Kern", "San Bernardino", "Inyo"]),
    ("7-024.01", "Borrego Valley - Borrego Springs",            ["San Diego"]),
]

# County -> ag-dependence proxy. This is a QUALITATIVE economy proxy for "is the muni tax
# base meaningfully agricultural," used to gate whether the overdraft channel actually touches
# AV. SJV core counties (top US ag-production counties) = high. Mixed counties = medium.
# Heavily urban counties = low (overdraft basin present but AV base is not farmland).
# Proxy basis: USDA/CDFA county ag-production rank + share of county economy in ag; encoded
# qualitatively, not as a hard number, to avoid over-precision.
AG_DEPENDENCE = {
    # Core San Joaquin Valley ag economies (nation-leading ag-production counties)
    "Kern": "high", "Tulare": "high", "Fresno": "high", "Kings": "high",
    "Madera": "high", "Merced": "high",
    # SJV-edge / mixed ag + city
    "Stanislaus": "high", "San Joaquin": "medium",
    # Central Coast ag (Salinas/Pajaro/Paso/Cuyama farmland)
    "Monterey": "high", "San Benito": "high", "San Luis Obispo": "medium",
    "Santa Barbara": "medium", "Ventura": "medium", "Santa Cruz": "medium",
    # Desert / mixed
    "Imperial": "high", "Inyo": "low", "San Bernardino": "low",
    # Urban / low ag-dependence (overdraft basin may exist but tax base is not farmland)
    "Los Angeles": "low", "Orange": "low", "San Diego": "low", "San Francisco": "low",
    "San Mateo": "low", "Santa Clara": "low", "Alameda": "low", "Contra Costa": "low",
    "Sacramento": "low", "Riverside": "low", "Placer": "low", "Sonoma": "medium",
    "Marin": "low", "Solano": "medium", "Yolo": "high", "Napa": "medium",
    "Tehama": "high", "Shasta": "low", "Butte": "high", "Glenn": "high", "Colusa": "high",
    "Sutter": "high", "Plumas": "low",
}


def _build_cache() -> dict:
    """Build the static basin table (county->critical-basin index) and cache it."""
    county_to_critical: dict[str, list[dict]] = {}
    for num, name, counties in CRITICALLY_OVERDRAFTED:
        for c in counties:
            county_to_critical.setdefault(c, []).append({"basin_number": num, "basin_name": name})
    table = {
        "_source": SOURCE,
        "_as_of": AS_OF,
        "_note": ("County-level mapping. A county that appears here contains a critically-"
                  "overdrafted basin; it does NOT mean every parcel in the county overlies "
                  "that basin. Parcel-precise assignment needs lat/lon point-in-basin (hook "
                  "provided but not required)."),
        "critically_overdrafted_basins": [
            {"basin_number": n, "basin_name": nm, "counties": cs}
            for n, nm, cs in CRITICALLY_OVERDRAFTED
        ],
        "county_to_critical": county_to_critical,
        "ag_dependence": AG_DEPENDENCE,
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(CACHE, "w") as f:
        json.dump(table, f, indent=1)
    return table


def _load_cache() -> dict:
    if os.path.exists(CACHE):
        try:
            return json.load(open(CACHE))
        except Exception:
            pass
    return _build_cache()


# District-name -> county inference, for the case where only a district name is supplied.
# Keys are normalized substrings; conservative — only well-known SJV / control names so we
# never FABRICATE a county. Unknown -> UNVERIFIABLE (not clean).
_NAME_COUNTY_HINTS = {
    "turlock": "Stanislaus", "modesto": "Stanislaus", "ceres": "Stanislaus",
    "bakersfield": "Kern", "mcfarland": "Kern", "delano": "Kern", "wasco": "Kern",
    "arvin": "Kern", "shafter": "Kern", "taft": "Kern", "southern kern": "Kern",
    "lakeside union": "Kern", "lamont": "Kern",
    "tulare": "Tulare", "visalia": "Tulare", "porterville": "Tulare", "lindsay": "Tulare",
    "dinuba": "Tulare", "exeter": "Tulare", "woodlake": "Tulare",
    "fresno": "Fresno", "clovis": "Fresno", "sanger": "Fresno", "selma": "Fresno",
    "kerman": "Fresno", "reedley": "Fresno", "parlier": "Fresno", "washington unified": "Fresno",
    "hanford": "Kings", "lemoore": "Kings", "corcoran": "Kings",
    "madera": "Madera", "chowchilla": "Madera",
    "merced": "Merced", "los banos": "Merced", "atwater": "Merced", "livingston": "Merced",
    "stockton": "San Joaquin", "manteca": "San Joaquin", "lodi": "San Joaquin",
    "tracy": "San Joaquin", "ripon": "San Joaquin",
    "salinas": "Monterey", "monterey peninsula": "Monterey", "soledad": "Monterey",
    "hollister": "San Benito",
    "paso robles": "San Luis Obispo",
    "oxnard": "Ventura", "hueneme": "Ventura",
    "borrego": "San Diego",
    # control / urban
    "los angeles": "Los Angeles", "long beach": "Los Angeles", "culver city": "Los Angeles",
    "baldwin park": "Los Angeles", "lynwood": "Los Angeles", "monrovia": "Los Angeles",
    "oakland": "Alameda", "hayward": "Alameda", "berkeley": "Alameda",
    "san francisco": "San Francisco", "milpitas": "Santa Clara", "gilroy": "Santa Clara",
}


def _infer_county_from_name(district_name: str) -> str | None:
    if not district_name:
        return None
    q = district_name.lower()
    for hint, county in _NAME_COUNTY_HINTS.items():
        if hint in q:
            return county
    return None


def _refine_basin_by_point(lat: float, lon: float):
    """OPTIONAL lat/lon -> basin refinement against DWR B118 GIS.

    Default build does NOT call a live service (county-level is the contract). This hook is a
    placeholder for a point-in-basin query against DWR's published B118 basin polygons; if a
    local polygon file is dropped in, wire it here. Returns None when no GIS is available, so
    callers transparently fall back to county-level mapping (and the note says so).
    """
    return None


def sgma_exposure(district_name: str | None = None, county: str | None = None,
                  lat: float | None = None, lon: float | None = None) -> dict:
    """SGMA groundwater AV-erosion exposure for a CA muni tax base.

    Resolution order: explicit county -> infer county from district_name -> (optional) lat/lon
    point-in-basin refinement. County-level is the authoritative default. If no county can be
    determined, returns UNVERIFIABLE (NOT clean).
    """
    table = _load_cache()
    county_to_critical = table["county_to_critical"]
    ag_dep_map = table["ag_dependence"]

    # 1. Resolve county.
    resolved = None
    if county:
        resolved = county.replace(" County", "").strip()
        # normalize case to table keys
        for k in county_to_critical.keys() | ag_dep_map.keys():
            if k.lower() == resolved.lower():
                resolved = k
                break
    if not resolved:
        resolved = _infer_county_from_name(district_name or "")

    # 1b. Optional lat/lon basin refinement (only sets basin, county still drives ag-gate).
    point_basin = _refine_basin_by_point(lat, lon) if (lat is not None and lon is not None) else None

    if not resolved and not point_basin:
        return {
            "sgma_basin": None,
            "sgma_priority": "UNVERIFIABLE",
            "sgma_critical": False,
            "ag_dependence": "unknown",
            "sgma_flag": "UNVERIFIABLE",
            "sgma_note": ("County could not be determined from the inputs and no basin polygon "
                          "match was available, so SGMA exposure is UNVERIFIABLE (not clean). "
                          "Supply a county or a known district name to resolve."),
        }

    ag = ag_dep_map.get(resolved, "unknown") if resolved else "unknown"

    # 2. Critically-overdrafted basin membership (county-level).
    crit_basins = county_to_critical.get(resolved, []) if resolved else []
    # Pick the representative basin: prefer the one whose name contains the county (the
    # county's own SJV subbasin) over an edge-shared basin (e.g. Kern -> "Kern County", not
    # the small slice of "Cuyama Valley"). Otherwise take the first listed.
    rep = None
    if crit_basins and resolved:
        rep = next((b for b in crit_basins if resolved.lower() in b["basin_name"].lower()), None)
        if rep is None:
            rep = crit_basins[0]
    basin_name = point_basin or (rep["basin_name"] if rep else None)
    all_basins = [b["basin_name"] for b in crit_basins]
    is_critical = bool(crit_basins) or bool(point_basin)

    if is_critical:
        priority = "Critically Overdrafted"
        # gate the channel on ag-dependence of the tax base
        if ag in ("high", "medium"):
            flag = "hard"
            note = (
                f"{resolved} County overlies a Critically-Overdrafted SGMA basin "
                f"({basin_name}; DWR Bulletin 118) and is an agriculture-dependent tax base "
                f"(ag_dependence={ag}). REVIEW for a SLOW assessed-value-erosion TAIL: SGMA "
                f"pumping cuts to 2040 are projected to fallow irrigated farmland, which "
                f"reassesses ag land/improvements DOWN and erodes the ad-valorem levy base over "
                f"a decade. This is an AV-growth tail on long-duration GO, NOT a near-term "
                f"default flag. County-level mapping: the county contains this basin but not "
                f"every parcel overlies it; parcel-precise assignment needs lat/lon."
            )
        else:
            flag = "soft"
            note = (
                f"{resolved} County overlies a Critically-Overdrafted SGMA basin "
                f"({basin_name}; DWR Bulletin 118) but the tax base is not ag-dependent "
                f"(ag_dependence={ag}), so the farmland AV-erosion channel is muted. Note only. "
                f"County-level mapping limitation applies."
            )
        if len(all_basins) > 1:
            note += f" County spans {len(all_basins)} COD basins: {', '.join(all_basins)}."
        return {
            "sgma_basin": basin_name,
            "sgma_basins_in_county": all_basins,
            "sgma_priority": priority,
            "sgma_critical": True,
            "ag_dependence": ag,
            "sgma_flag": flag,
            "sgma_note": note,
        }

    # 3. Not critically-overdrafted. We do not encode the full Bulletin-118 High/Med/Low
    #    priority polygon set here (that needs the live SGMA prioritization service); we
    #    represent it conservatively: ag-heavy SJV/Central-Valley counties not in the COD list
    #    are still in High-priority basins under SGMA -> soft note; everything else -> None.
    #    We do NOT assert a specific non-critical priority we cannot cite -> "High (inferred)"
    #    only for clearly ag Central Valley counties, else None.
    if ag == "high":
        return {
            "sgma_basin": None,
            "sgma_priority": "High",
            "sgma_critical": False,
            "ag_dependence": ag,
            "sgma_flag": "soft",
            "sgma_note": (
                f"{resolved} County is agriculture-dependent and sits in the Central Valley / "
                f"SGMA High-priority basin footprint but is NOT on the published 21-basin "
                f"Critically-Overdrafted list (DWR Bulletin 118). Soft note: pumping management "
                f"is likely but there is no acute overdraft mandate, so AV-erosion pressure is "
                f"lower than in COD basins. County-level mapping; basin-priority not parcel-"
                f"verified here."
            ),
        }

    return {
        "sgma_basin": None,
        "sgma_priority": None,
        "sgma_critical": False,
        "ag_dependence": ag,
        "sgma_flag": None,
        "sgma_note": (
            f"{resolved or 'Unknown'} County is not on the DWR Bulletin 118 Critically-"
            f"Overdrafted list and is not an ag-dependent Central Valley tax base "
            f"(ag_dependence={ag}); no material SGMA AV-erosion exposure on this channel."
        ),
    }


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------
def _validate():
    _build_cache()  # refresh cache from the static authoritative table
    print(f"SGMA source: {SOURCE}")
    print(f"As-of: {AS_OF}")
    print(f"Cache: {CACHE}")
    print(f"Critically-overdrafted basins encoded: {len(CRITICALLY_OVERDRAFTED)} (expect 21)\n")

    # Book / control districts: SJV names should fire critical-hard; coastal/urban should not.
    cases = [
        # (district_name, county)  -- county None tests name-inference
        ("Turlock Unified", "Stanislaus"),
        ("Bakersfield City", "Kern"),
        ("Southern Kern Unified", "Kern"),
        ("McFarland Unified", "Kern"),
        ("Tulare City", "Tulare"),
        ("Lindsay Unified", "Tulare"),
        ("Sanger Unified", "Fresno"),
        ("Fresno Unified", "Fresno"),
        ("Washington Unified", "Fresno"),
        ("Manteca Unified", "San Joaquin"),
        ("Stockton Unified", "San Joaquin"),
        ("Monterey Peninsula Unified", "Monterey"),
        ("Hollister", "San Benito"),
        ("Hueneme Elementary", "Ventura"),
        # name-only (county omitted) to test inference
        ("Madera Unified", None),
        ("Chowchilla Elementary", None),
        ("Paso Robles Joint Unified", None),
        # negative controls: urban / coastal LA-Bay
        ("Baldwin Park Unified", "Los Angeles"),
        ("Culver City Unified", "Los Angeles"),
        ("Long Beach CCD", "Los Angeles"),
        ("Hayward Unified", "Alameda"),
        ("Milpitas Unified", "Santa Clara"),
        ("Natomas Unified", "Sacramento"),
        # urban-over-COD-basin control: San Diego (Borrego COD basin) but low ag
        ("San Diego City", "San Diego"),
        # UNVERIFIABLE control: unknown county/name
        ("Some Unknown District", None),
    ]

    hdr = f"{'district':30} {'county':14} {'flag':12} {'priority':22} {'ag':7} basin"
    print(hdr)
    print("-" * len(hdr))
    for name, cty in cases:
        r = sgma_exposure(district_name=name, county=cty)
        flag = str(r["sgma_flag"])
        print(f"{name[:30]:30} {str(cty or '(infer)')[:14]:14} {flag:12} "
              f"{str(r['sgma_priority'])[:22]:22} {str(r['ag_dependence'])[:7]:7} "
              f"{r['sgma_basin'] or '-'}")

    # Assertions: SJV ag names fire critical-hard; LA/Bay/Sac controls do not.
    assert sgma_exposure(county="Stanislaus")["sgma_flag"] == "hard"
    assert sgma_exposure(county="Kern")["sgma_critical"] is True
    assert sgma_exposure(county="Tulare")["sgma_flag"] == "hard"
    assert sgma_exposure(county="Fresno")["sgma_flag"] == "hard"
    assert sgma_exposure(district_name="Madera Unified")["sgma_critical"] is True
    assert sgma_exposure(district_name="Paso Robles Joint Unified")["sgma_critical"] is True
    # urban controls: not critical (LA/Alameda/Santa Clara/Sacramento have no COD basin)
    assert sgma_exposure(county="Los Angeles")["sgma_flag"] is None
    assert sgma_exposure(county="Alameda")["sgma_flag"] is None
    assert sgma_exposure(county="Sacramento")["sgma_flag"] is None
    # San Diego: COD basin (Borrego) present but low ag -> critical True but soft (muted channel)
    sd = sgma_exposure(county="San Diego")
    assert sd["sgma_critical"] is True and sd["sgma_flag"] == "soft"
    # UNVERIFIABLE when nothing resolves
    assert sgma_exposure(district_name="Some Unknown District")["sgma_flag"] == "UNVERIFIABLE"
    print("\nAll assertions passed.")


if __name__ == "__main__":
    _validate()
