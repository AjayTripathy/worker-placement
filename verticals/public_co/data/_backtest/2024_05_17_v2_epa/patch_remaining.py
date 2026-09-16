"""Patch the 3 problem tickers from the main rescore:
  - ALB, LAC: never completed (ALB stuck on slow Envirofacts response)
  - BLDP: substring noise from too-generic "Ballard" name → re-do with "Ballard Power"

Also copies the non-industrial tickers from B1 unchanged, then runs the
deterministic scorer over the full B2 directory.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from verticals.public_co.m_sources.epa_emissions import query_facility_emissions
from verticals.public_co.deterministic_scorer import score_ticker

B1 = Path("verticals/public_co/data/_backtest/2024_05_17")
B2 = Path("verticals/public_co/data/_backtest/2024_05_17_v2_epa")


PATCHES = [
    # ticker, company_name (tighter), claimed_locations, target_cid
    ("BLDP", "Ballard Power", [],                                    "BLDP-6"),
    ("ALB",  "Albemarle",     [{"city": "MAGNOLIA",    "state": "AR"},
                                {"city": "SILVER PEAK", "state": "NV"}], "ALB-4"),
    ("LAC",  "Lithium Americas", [],                                  "LAC-7"),
]


def find_target_claim(plan: dict, prefer: str | None = None) -> str | None:
    claims = plan.get("claims", [])
    if prefer:
        for c in claims:
            if c["claim_id"] == prefer:
                return prefer
    for cat in ("physical_facility", "production_volume", "manufacturing_capacity"):
        for c in claims:
            if c.get("category") == cat:
                return c["claim_id"]
    return None


def patch_ticker(ticker: str, company: str, locs: list[dict], prefer_cid: str | None) -> dict:
    plan_path = B1 / f"{ticker}.plan.json"
    qry_path  = B1 / f"{ticker}.queries.json"
    plan = json.loads(plan_path.read_text())
    qry  = json.loads(qry_path.read_text())

    target_cid = find_target_claim(plan, prefer=prefer_cid)
    if not target_cid:
        return {"ticker": ticker, "error": "no target claim"}

    epa = query_facility_emissions(
        company_name=company,
        claimed_locations=locs or None,
    )

    new_result = {
        "label":  "epa_emissions.query_facility_emissions",
        "result": epa,
        "kwargs": {"company_name": company, "claimed_locations": locs},
        "_b2_added": True,
    }

    qry.setdefault("results", {}).setdefault(target_cid, []).insert(0, new_result)

    (B2 / f"{ticker}.plan.json").write_text(plan_path.read_text())
    (B2 / f"{ticker}.queries.json").write_text(json.dumps(qry, indent=2, default=str))

    return {
        "ticker":  ticker,
        "signal":  epa.get("operational_scale_signal"),
        "frs":     epa.get("frs", {}).get("facilities_found"),
        "tri":     epa.get("tri", {}).get("facilities_found"),
        "ghgrp":   epa.get("ghgrp", {}).get("facilities_found"),
    }


def main():
    print("=== patch_remaining: re-do BLDP/ALB/LAC ===")
    for tk, name, locs, cid in PATCHES:
        r = patch_ticker(tk, name, locs, cid)
        if "error" in r:
            print(f"  {tk:6s}: ERROR {r['error']}")
            continue
        print(f"  {tk:6s} ({name!r}): signal={r['signal']:42s}  FRS={r['frs']:4} TRI={r['tri']:3} GHGRP={r['ghgrp']:3}")

    # Copy non-industrial tickers untouched (so scorer can sweep the whole dir).
    print()
    print("Copying non-industrial tickers unchanged...")
    industrial = {"PLUG", "FCEL", "HYZN", "BE", "BLDP", "LIN", "APD",
                  "ENVX", "MVST", "QS", "SES", "SLDP", "ALB", "LAC"}
    for src in B1.glob("*.plan.json"):
        tk = src.name.replace(".plan.json", "")
        if tk in industrial:
            continue
        for ext in ("plan", "queries"):
            sf = B1 / f"{tk}.{ext}.json"
            df = B2 / f"{tk}.{ext}.json"
            if sf.exists() and not df.exists():
                shutil.copy(sf, df)
                print(f"  copy {tk}.{ext}.json")

    print()
    print("=== rescore via deterministic_scorer ===")
    all_tickers = sorted({p.name.replace(".plan.json", "") for p in B2.glob("*.plan.json")})
    for tk in all_tickers:
        r = score_ticker(tk, data_dir=B2)
        if "error" in r:
            print(f"  {tk:6s}: {r['error']}")
            continue
        ord_ = ["PASS", "MODERATE_UNDERDELIVERY", "SEVERE_UNDERDELIVERY", "RED_FLAG_NEGATIVE", "UNVERIFIABLE"]
        parts = [f"{k[:4]}={r['counts'].get(k,0)}" for k in ord_]
        print(f"  {tk:6s}: {r['n_claims']:2d} claims  " + " ".join(parts))


if __name__ == "__main__":
    main()
