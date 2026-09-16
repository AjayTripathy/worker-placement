"""utility_supply — coarse SUPPLY-SOURCE bucketing for the utility-revenue sleeve diversification cap.

A utility-revenue sleeve only diversifies the property-tax-regime tail if it is itself SUPPLY-diversified.
Buying five Colorado-River-dependent water systems just swaps one correlated CA tail (Prop 13) for another
(a Colorado River allocation cut). This assigns each candidate a coarse water-supply region (or ELECTRIC),
so the sourcing pass can cap names per source. Heuristic — issuer name + county + the OS supply note from
water_revenue_underwrite.assess_supply_risk. Returns a bucket label; UNKNOWN when it can't tell (the cap
treats UNKNOWN conservatively — counts against a shared bucket so it can't hide concentration)."""
import re

# region -> matching tokens in the issuer name (uppercased)
_NAME = {
    "COLORADO_RIVER":   ("IMPERIAL", "COACHELLA", "PALO VERDE", "BLYTHE", "NEEDLES"),
    "STATE_WATER_PROJ": ("KERN", "ANTELOPE", "CASTAIC", "PALMDALE", "MOJAVE", "TEHACHAPI",
                         "SAN GABRIEL", "THREE VALLEYS", "FOOTHILL", "INLAND EMPIRE"),
    "NORCAL_DELTA":     ("EAST BAY", "EBMUD", "SAN FRANCISCO", "SFPUC", "CONTRA COSTA", "SACRAMENTO",
                         "SANTA CLARA", "SOLANO", "YOLO", "ZONE 7", "ALAMEDA CTY WTR", "DUBLIN SAN RAMON"),
    "SIERRA_LOCAL":     ("TURLOCK", "MODESTO", "MERCED IRR", "NEVADA IRR", "OAKDALE", "SOUTH SAN JOAQUIN",
                         "YUBA", "PLACER", "EL DORADO", "CALAVERAS", "TUOLUMNE", "FRESNO IRR"),
    "COASTAL_LOCAL":    ("MONTEREY", "MARIN", "SANTA BARBARA", "CAMBRIA", "SAN LUIS", "SANTA CRUZ",
                         "CAMROSA", "VENTURA", "GOLETA", "CARPINTERIA", "SOQUEL"),
}
# county -> region (fallback when the name is uninformative)
_COUNTY = {
    "Imperial": "COLORADO_RIVER", "Riverside": "STATE_WATER_PROJ", "Kern": "STATE_WATER_PROJ",
    "Los Angeles": "STATE_WATER_PROJ", "San Bernardino": "STATE_WATER_PROJ",
    "Alameda": "NORCAL_DELTA", "Contra Costa": "NORCAL_DELTA", "Sacramento": "NORCAL_DELTA",
    "San Francisco": "NORCAL_DELTA", "Santa Clara": "NORCAL_DELTA", "San Mateo": "NORCAL_DELTA",
    "Solano": "NORCAL_DELTA", "Yolo": "NORCAL_DELTA",
    "Stanislaus": "SIERRA_LOCAL", "Merced": "SIERRA_LOCAL", "Tuolumne": "SIERRA_LOCAL",
    "Nevada": "SIERRA_LOCAL", "Placer": "SIERRA_LOCAL", "El Dorado": "SIERRA_LOCAL",
    "Monterey": "COASTAL_LOCAL", "Santa Cruz": "COASTAL_LOCAL", "Santa Barbara": "COASTAL_LOCAL",
    "San Luis Obispo": "COASTAL_LOCAL", "Marin": "COASTAL_LOCAL", "Ventura": "COASTAL_LOCAL",
    "Fresno": "GROUNDWATER", "Tulare": "GROUNDWATER", "Kings": "GROUNDWATER", "Madera": "GROUNDWATER",
}


def supply_bucket(sectype=None, issuer=None, county=None, system_type=None, supply_note=None):
    """Coarse supply source. ELECTRIC for power systems; otherwise a CA water region. Groundwater-only
    systems (SGMA-exposed) are their own bucket. Returns one of: ELECTRIC, COLORADO_RIVER,
    STATE_WATER_PROJ, NORCAL_DELTA, SIERRA_LOCAL, COASTAL_LOCAL, GROUNDWATER, UNKNOWN."""
    if (sectype or "").upper() == "ELEC-REV":
        return "ELECTRIC"
    name = (issuer or "").upper()
    note = (supply_note or "").lower()
    st = (system_type or "").lower()
    # explicit groundwater-only systems (the SGMA-exposed tail)
    if "groundwater" in st or "groundwater" in note or "sgma" in note or "overdraft" in note:
        # but if the name says a surface/imported source, prefer that region below
        if not any(t in name for grp in _NAME.values() for t in grp):
            return "GROUNDWATER"
    if "colorado river" in note:
        return "COLORADO_RIVER"
    if "state water project" in note or "swp" in note:
        return "STATE_WATER_PROJ"
    for region, toks in _NAME.items():
        if any(t in name for t in toks):
            return region
    if county and county in _COUNTY:
        return _COUNTY[county]
    return "UNKNOWN"
