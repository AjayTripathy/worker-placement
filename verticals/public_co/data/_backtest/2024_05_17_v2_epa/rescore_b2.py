"""B2 rescore — apply epa_emissions v2 to the B1 industrial cohort.

For each industrial-cohort ticker in B1:
  1. Load the existing plan + queries.
  2. Run epa_emissions.query_facility_emissions(company, claimed_locations=...)
     where claimed_locations are extracted from each plan's physical_facility /
     production_volume claims (US-only).
  3. Attach the EPA result to the first physical_facility (or production_volume)
     claim's results list with label='epa_emissions.query_facility_emissions'.
  4. Write the augmented plan + queries to _backtest/2024_05_17_v2_epa/.
  5. Re-run the deterministic_scorer against the new directory.

Caveats:
  - FRS data is read TODAY (2026-05-17), not as-of 2024-05-17. Some PLUG
    facilities (e.g. Woodbine GA, Charleston TN) were permitted in 2024
    and would have been in FRS by the cutoff. Others (Graham TX
    "Limestone") came later. This is a "what would today's framework
    say about these names" run, not a pure point-in-time replay.
  - Several names (BLDP, SES, ENVX) have primarily non-US operations
    that EPA can't probe. Those will land on NO_EPA_FOOTPRINT and
    should be interpreted accordingly.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from verticals.public_co.m_sources.epa_emissions import query_facility_emissions
from verticals.public_co.deterministic_scorer import score_ticker

B1_DIR = Path("verticals/public_co/data/_backtest/2024_05_17")
B2_DIR = Path("verticals/public_co/data/_backtest/2024_05_17_v2_epa")
B2_DIR.mkdir(parents=True, exist_ok=True)


# Claimed plant locations extracted from each plan's physical_facility /
# production_volume claims. Hand-extracted because the planner LLM doesn't
# yet produce a structured location field; v3 of the planner could.
CLAIMED_LOCATIONS = {
    "PLUG": [
        {"city": "KINGSLAND",  "state": "GA"},     # FY23 10-K claim text
        {"city": "WOODBINE",   "state": "GA"},     # Camden County alias
        {"city": "CHARLESTON", "state": "TN"},     # FY23 10-K claim text
    ],
    "FCEL": [
        {"city": "TORRINGTON", "state": "CT"},     # 167k sq ft mfg facility
        {"city": "LONG BEACH", "state": "CA"},     # Toyota tri-gen
    ],
    "HYZN": [
        {"city": "BOLINGBROOK", "state": "IL"},    # 110k sq ft mfg facility
    ],
    "BE": [
        {"city": "FREMONT",    "state": "CA"},     # multi-gigawatt factory
        {"city": "NEWARK",     "state": "DE"},     # Energy Server + electrolyzer
    ],
    "BLDP": [],  # primarily Canadian; EPA US-only
    "LIN": [],   # global; 350 Americas facilities — probe by name, no audit
    "APD": [],   # global; 450 Americas facilities — same
    "ENVX": [
        # Penang Malaysia is international. Their US ops are in Fremont CA.
        {"city": "FREMONT",    "state": "CA"},
    ],
    "MVST": [
        {"city": "CLARKSVILLE", "state": "TN"},    # 577k sq ft mfg
        {"city": "WINDSOR",     "state": "CO"},    # 100k sq ft ESS assembly
    ],
    "QS": [
        {"city": "SAN JOSE",   "state": "CA"},     # QS-0 pilot line
    ],
    "SES": [],   # Shanghai + Chungju, no US
    "SLDP": [
        {"city": "THORNTON",   "state": "CO"},     # SP2 electrolyte facility
    ],
    "ALB": [
        {"city": "MAGNOLIA",    "state": "AR"},    # Bromine
        {"city": "SILVER PEAK", "state": "NV"},    # Lithium
    ],
    "LAC": [],   # Argentina/Chile; Thacker Pass not in B1 claim text
}


COMPANY_NAME = {
    "PLUG": "Plug Power",
    "FCEL": "FuelCell Energy",
    "HYZN": "Hyzon",
    "BE":   "Bloom Energy",
    "BLDP": "Ballard",
    "LIN":  "Linde",
    "APD":  "Air Products",
    "ENVX": "Enovix",
    "MVST": "Microvast",
    "QS":   "QuantumScape",
    "SES":  "SES AI",
    "SLDP": "Solid Power",
    "ALB":  "Albemarle",
    "LAC":  "Lithium Americas",
}


def find_target_claim(plan: dict) -> str | None:
    """Pick the claim_id to attach EPA results to. Prefer physical_facility,
    fall back to production_volume."""
    claims = plan.get("claims", [])
    for cat in ("physical_facility", "production_volume", "manufacturing_capacity"):
        for c in claims:
            if c.get("category") == cat:
                return c["claim_id"]
    return None


def rescore_ticker(ticker: str) -> dict:
    plan_path = B1_DIR / f"{ticker}.plan.json"
    qry_path  = B1_DIR / f"{ticker}.queries.json"
    if not plan_path.exists() or not qry_path.exists():
        return {"ticker": ticker, "error": "missing B1 inputs"}

    plan = json.loads(plan_path.read_text())
    qry  = json.loads(qry_path.read_text())

    target_cid = find_target_claim(plan)
    if not target_cid:
        return {"ticker": ticker, "error": "no industrial claim to attach EPA to"}

    company = COMPANY_NAME.get(ticker, ticker)
    locs = CLAIMED_LOCATIONS.get(ticker) or None

    epa_res = query_facility_emissions(
        company_name=company,
        claimed_locations=locs,
    )

    new_result = {
        "label":      "epa_emissions.query_facility_emissions",
        "result":     epa_res,
        "kwargs":     {"company_name": company, "claimed_locations": locs},
        "_b2_added":  True,
    }

    # The deterministic scorer only inspects results[0]; insert at the front so
    # the EPA v2 audit becomes the primary adjudication for this physical-
    # facility claim. The original B1 M-source (often epa_frs.query_facilities,
    # which is subsumed by epa_emissions v2's broader FRS layer) is preserved
    # at index 1+ for traceability but ignored by the scorer.
    results_by_cid = qry.setdefault("results", {})
    results_by_cid.setdefault(target_cid, [])
    results_by_cid[target_cid].insert(0, new_result)

    # Write augmented files to B2_DIR
    (B2_DIR / f"{ticker}.plan.json").write_text(plan_path.read_text())
    (B2_DIR / f"{ticker}.queries.json").write_text(json.dumps(qry, indent=2, default=str))

    return {
        "ticker":       ticker,
        "target_cid":   target_cid,
        "signal":       epa_res.get("operational_scale_signal"),
        "frs":          epa_res.get("frs", {}).get("facilities_found"),
        "tri":          epa_res.get("tri", {}).get("facilities_found"),
        "ghgrp":        epa_res.get("ghgrp", {}).get("facilities_found"),
        "claimed_loc_audit": [
            {"city": a["city"], "state": a["state"], "present": a["company_present_at_loc"]}
            for a in (epa_res.get("claimed_location_audit") or [])
        ],
    }


def main():
    tickers = list(COMPANY_NAME.keys())
    rescore_results = []
    print(f"=== B2 rescore: epa_emissions v2 on {len(tickers)} industrial-cohort tickers ===")
    print(f"  B1 source: {B1_DIR}")
    print(f"  B2 output: {B2_DIR}")
    print()

    for tk in tickers:
        r = rescore_ticker(tk)
        rescore_results.append(r)
        if "error" in r:
            print(f"  {tk:6s}: ERROR  {r['error']}")
            continue
        print(f"  {tk:6s}: signal={r['signal']:42s}  FRS={r['frs']:3} TRI={r['tri']:2} GHGRP={r['ghgrp']:2}")
        if r["claimed_loc_audit"]:
            for a in r["claimed_loc_audit"]:
                pres = "✓" if a["present"] else "✗"
                print(f"           {pres} {a['city']}, {a['state']}")

    # Now also copy over the non-industrial (fintech / control) tickers
    # untouched so the scorer can be run uniformly on B2_DIR.
    print()
    print("Copying non-industrial tickers unchanged...")
    for src in B1_DIR.glob("*.plan.json"):
        tk = src.name.replace(".plan.json", "")
        if tk in COMPANY_NAME:
            continue
        for ext in ("plan", "queries"):
            sf = B1_DIR / f"{tk}.{ext}.json"
            df = B2_DIR / f"{tk}.{ext}.json"
            if sf.exists() and not df.exists():
                shutil.copy(sf, df)

    # Re-run the scorer over B2_DIR
    print()
    print("=== rescore via deterministic_scorer ===")
    all_tickers = sorted({p.name.replace(".plan.json", "") for p in B2_DIR.glob("*.plan.json")})
    for tk in all_tickers:
        r = score_ticker(tk, data_dir=B2_DIR)
        if "error" in r:
            print(f"  {tk:6s}: {r['error']}")
            continue
        ord_ = ["PASS", "MODERATE_UNDERDELIVERY", "SEVERE_UNDERDELIVERY", "RED_FLAG_NEGATIVE", "UNVERIFIABLE"]
        parts = [f"{k[:4]}={r['counts'].get(k,0)}" for k in ord_]
        print(f"  {tk:6s}: {r['n_claims']:2d} claims  " + " ".join(parts))

    (B2_DIR / "_rescore_summary.json").write_text(
        json.dumps(rescore_results, indent=2, default=str)
    )


if __name__ == "__main__":
    main()
