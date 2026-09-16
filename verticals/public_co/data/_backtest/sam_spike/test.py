"""SAM.gov entity-lookup spike on a panel of UEIs from prior spikes.

For each UEI:
  1. Fetch the SAM entity record
  2. Extract primary NAICS + description, address, registration status
  3. Compare NAICS to the filing's stated business activity

This validates SAM as a scope-verification source. Public v3 API does
NOT return employee count or revenue (those require paid extracts or
FOUO access), so the actionable signal is NAICS-mismatch + address-
consistency + registration status.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from verticals.public_co.m_sources.sam_entity import query_entity_by_uei

HERE = Path(__file__).parent

# (label, uei, parent_ticker, expected_naics_family_or_None)
PANEL = [
    # PESI subsidiaries (DOE nuclear waste) — expect 5622 family
    ("PESI/Northwest Richland", "C9CABLLMBP63", "PESI", "5622"),
    ("PESI/Florida",            "HLG5NHJJJ4Q8", "PESI", "5622"),

    # HDSN (refrigerant supplier) — expect 325120 industrial gas
    ("HDSN Hudson Tech",        "H1K6JDP3K2K8", "HDSN", "3251"),
    ("HDSN alt UEI",            "PTZTPC76BCZ6", "HDSN", "3251"),

    # KULR (battery safety) — expect electronics-related
    ("KULR Corp",               "YM83B3CN2K61", "KULR", None),

    # AIRO subsidiaries
    ("AIRO/Coastal Defense",    "N7GAJ4WGU8M8", "AIRO", None),    # training services?
    ("AIRO/Aspen Avionics",     "MXQSNB4QEKN4", "AIRO", "3345"),  # avionics electronics
    ("AIRO/Jaunt Air Mobility", "D2XPQEHMLYX1", "AIRO", "3364"),  # aircraft

    # Lockheed parent UEI (known: 12 PNJ4LL3M2H47 or similar)
    # Skip for now — we have plenty
]


def main():
    rows = []
    print(f"{'label':28s} {'NAICS':>7s} {'desc':35s} {'city':18s} {'state':>4s} {'status':10s} naics_match")
    print("=" * 130)
    for label, uei, ticker, exp_naics_prefix in PANEL:
        r = query_entity_by_uei(uei)
        time.sleep(15)  # SAM free tier: ~10 req/min; conservative spacing
        if r.get("error"):
            print(f"  {label:26s} ERROR: {r.get('error')}")
            rows.append({"label": label, "uei": uei, "error": r.get("error")})
            continue
        primary = r.get("primary_naics") or ""
        naics_desc = ""
        for nc, nd in (r.get("all_naics") or []):
            if nc == primary:
                naics_desc = (nd or "")[:33]
                break
        addr = r.get("physical_address") or {}
        city = (addr.get("city") or "")[:16]
        state = addr.get("state") or "??"
        status = r.get("registration_status") or "?"
        naics_match = "?"
        if exp_naics_prefix:
            naics_match = "MATCH" if primary.startswith(exp_naics_prefix) else "MISMATCH"
        print(f"  {label:26s} {primary:>7s} {naics_desc:35s} {city:18s} {state:>4s} "
              f"{status:10s} {naics_match}")
        rows.append({
            "label":        label,
            "uei":          uei,
            "parent":       ticker,
            "legal_name":   r.get("legal_business_name"),
            "primary_naics": primary,
            "naics_desc":   naics_desc,
            "all_naics":    r.get("all_naics"),
            "city":         addr.get("city"),
            "state":        state,
            "status":       status,
            "cage_code":    r.get("cage_code"),
            "exp_naics_prefix": exp_naics_prefix,
            "naics_match":  naics_match,
        })

    (HERE / "spike_results.json").write_text(json.dumps(rows, indent=2, default=str))
    print(f"\nWrote {HERE / 'spike_results.json'}")


if __name__ == "__main__":
    main()
