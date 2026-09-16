"""book_universe — the canonical book names + per-name FEATURES that drive detector dispatch. A detector
only scans the subset of names whose features match its APPLIES_TO contract (the dispatch-index discipline:
query the graph at dispatch time, don't blindly run every detector over every name).

features:
  legal_name        the entity legal name (for litigation / usaspending recipient search)
  gov_revenue       material US federal contract revenue -> usaspending
  undisclosed_cust  thesis leans on an unnamed concentrated customer -> customer_id (customs BOL)
  import_driven     {'hs4': [...], 'origin': [(code,name)...], 'readability': 0..1, 'note': ...}
                    revenue dominated by a readable HS4 x origin import flow -> import_nowcast
                    (Census monthly imports LEAD the quarterly print). CTY codes: 5520=VIETNAM,
                    5700=CHINA, 5600=INDONESIA — resolve via CTY_CODE=* before trusting a cell.
  capacity_ramp     (keywords, location) a plant/ops ramp to underwrite -> hiring_velocity
  physical_asset    {'kind': methane|oil|buildout, 'aoi': ...} -> satellite (needs AOI to execute)
  litigation        screen the entity in federal dockets (applies to ~all public names)
"""
from __future__ import annotations

BOOK = {
    # ---- held positions ----
    "BAH":  {"legal_name": "Booz Allen Hamilton", "gov_revenue": True, "litigation": True},
    "J":    {"legal_name": "Jacobs Technology", "gov_revenue": True, "litigation": True},
    "CAI":  {"legal_name": "CAI International", "litigation": True},
    "SLS":  {"legal_name": "SELLAS Life Sciences Group", "litigation": True},
    # ---- value sleeve ----
    "GCT":  {"legal_name": "GigaCloud Technology", "litigation": True,
             "capacity_ramp": ("warehouse fulfillment", "California")},
    "DFIN": {"legal_name": "Donnelley Financial Solutions", "litigation": True},
    "EVER": {"legal_name": "EverQuote", "litigation": True},
    "EPAM": {"legal_name": "EPAM Systems", "litigation": True},
    "SBH":  {"legal_name": "Sally Beauty Holdings", "litigation": True},
    "BKE":  {"legal_name": "Buckle Inc", "litigation": True},
    "CRCT": {"legal_name": "Cricut Inc", "litigation": True},
    "REPX": {"legal_name": "Riley Exploration Permian", "litigation": True,
             "physical_asset": {"kind": "methane_oil", "aoi": "Permian/Yeso (NM Eddy Co)"}},
    # ---- beauty / wellness ----
    "ESTA": {"legal_name": "Establishment Labs Holdings", "litigation": True},
    "ELF":  {"legal_name": "e.l.f. Beauty", "undisclosed_cust": True, "litigation": True},
    "ODD":  {"legal_name": "Oddity Tech", "litigation": True},
    "HIMS": {"legal_name": "Hims & Hers Health", "litigation": True},
    "INSP": {"legal_name": "Inspire Medical Systems", "litigation": True},
    "WST":  {"legal_name": "West Pharmaceutical Services", "undisclosed_cust": True, "litigation": True},
    "PGNY": {"legal_name": "Progyny Inc", "litigation": True},
    "PRCT": {"legal_name": "Procept BioRobotics", "litigation": True},
    "BRBR": {"legal_name": "BellRing Brands", "litigation": True},
    "VERU": {"legal_name": "Veru Inc", "litigation": True},
    # ---- K-beauty (ODM concentration + plant ramps) ----
    "COSMECCA": {"legal_name": "Cosmecca Korea", "undisclosed_cust": True, "litigation": False,
                 "capacity_ramp": ("cosmetics manufacturing", "New Jersey"),
                 "physical_asset": {"kind": "buildout", "aoi": "Englewood NJ / Totowa plant"}},
    "COSMAX": {"legal_name": "Cosmax Inc", "undisclosed_cust": True,
               "physical_asset": {"kind": "buildout", "aoi": "Korea/US ODM plants"}},
    "SILICON2": {"legal_name": "Silicon2 Co", "litigation": False},
    # ---- TRADE-DATA WIDE SWEEP 2026-07-11 — new tracked names (watch candidates, NOT positions) ----
    # (1) IMPORT-NOWCAST: public importers whose revenue maps to ONE readable HS4 x origin container flow.
    "CROX": {"legal_name": "Crocs Inc", "litigation": True,
             "import_driven": {"hs4": ["6402"], "origin": [("5520", "VIETNAM"), ("5700", "CHINA"), ("5600", "INDONESIA")],
                               "readability": 0.85, "next_print": "~late Oct 2026 (Q3)",
                               "note": "cleanest signature in the sweep: 1 product/1 material/1 HS4, VN-led. SCOPE TO "
                                       "CROCS-BRAND — exclude HEYDUDE (China textile 6404, separable noisier series)."}},
    "HOFT": {"legal_name": "Hooker Furnishings", "litigation": True,
             "import_driven": {"hs4": ["9403", "9401"], "origin": [("5520", "VIETNAM"), ("5700", "CHINA")],
                               "readability": 0.72, "next_print": "~early Sep 2026 (FQ2 Aug-end)",
                               "note": "~71% imported net sales, VN 76%/CN 13% — tighter origin read than GCT. Direct GCT "
                                       "analog on 9403. Re-baseline post-Home Meridian divestiture (Dec-2025)."}},
    "FLXS": {"legal_name": "Flexsteel Industries", "litigation": True,
             "import_driven": {"hs4": ["9401"], "origin": [("5520", "VIETNAM"), ("5700", "CHINA")],
                               "readability": 0.70, "next_print": "~late Aug 2026 (FQ4 Jun-end)",
                               "note": "import leg 'primarily Vietnam' upholstered seating. CAVEAT: captive Mexico plants "
                                       "ship US by TRUCK/rail, OUTSIDE the ocean-import series."}},
    "WEYS": {"legal_name": "Weyco Group", "litigation": True,
             "import_driven": {"hs4": ["6403"], "origin": [("5700", "CHINA"), ("5330", "INDIA")],
                               "readability": 0.75, "next_print": "~early Nov 2026 (Q3)",
                               "note": "~100% importer, ONE category (leather dress shoes); disclosed 2 China suppliers "
                                       "each >10% + India (CTY 5330, verified 2026-07-11). Small-cap sleeper, thin coverage = the edge."}},
    # (2) CUSTOMS-WHALE (undisclosed_cust): STVN = the template (already resolved ->Lilly). WST added above.
    #     RH / LZB = supplier-side inversion (resolve the hidden ASIAN VENDOR, demand-nowcast not customer re-rate).
    "STVN": {"legal_name": "Stevanato Group", "undisclosed_cust": True, "litigation": True},
    "RH":   {"legal_name": "RH (Restoration Hardware)", "undisclosed_cust": True, "litigation": True},
    "LZB":  {"legal_name": "La-Z-Boy Inc", "undisclosed_cust": True, "litigation": True},
    # (3) FEDERAL AWARD-FLOW (gov_revenue) — CIVILIAN-heavy (~0d tradeable lag). The CUT is more tradeable
    #     than the acceleration (obligation->revenue decouples in the current de-scope regime; trust down-prints).
    "ICFI": {"legal_name": "ICF International", "gov_revenue": True, "litigation": True},   # ~94% civilian, task-order
    "KBR":  {"legal_name": "KBR Inc", "gov_revenue": True, "litigation": True},              # NASA/DOE/State civilian slice
    "TTEK": {"legal_name": "Tetra Tech", "gov_revenue": True, "litigation": True},           # EPA/USACE-civil/DOE/water; USAID shock
    "PSN":  {"legal_name": "Parsons Corporation", "gov_revenue": True, "litigation": True},  # read CI segment (civ), not consolidated
}


def names_with(feature: str) -> list[str]:
    """Book tickers whose features include `feature` (truthy)."""
    return [t for t, f in BOOK.items() if f.get(feature)]


def legal(t: str) -> str:
    return BOOK.get(t, {}).get("legal_name", t)


def import_driven_names() -> dict:
    """Tickers with an import_driven config -> the config (drives import_nowcast dispatch)."""
    return {t: f["import_driven"] for t, f in BOOK.items() if f.get("import_driven")}
