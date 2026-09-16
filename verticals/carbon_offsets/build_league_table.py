"""Merge forest + methane scan results into a single sortable league table CSV."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# Severity ordering (worst → best)
SEVERITY_RANK = {
    "RED_FLAG_NEGATIVE": 0,
    "RED_FLAG_LOW_CAPTURE": 1,
    "SEVERE_UNDERDELIVERY": 2,
    "SEVERE_LOW_CAPTURE": 2,
    "MODERATE_UNDERDELIVERY": 3,
    "MODERATE_LOW_CAPTURE": 3,
    "PASS": 4,
    "no_observations": 5,
    "no_score": 6,
    "no_kml": 7,
    "outside_cm_coverage": 8,
}


def normalize_forest(r: dict) -> dict:
    sev = r.get("severity", r.get("status", "?"))
    return {
        "id": r.get("id"),
        "name": r.get("name", ""),
        "country": r.get("country", ""),
        "type": "forest",
        "subtype": r.get("subcat", ""),
        "claim_tco2_yr": r.get("claim_tco2_yr"),
        "aoi_or_loc": r.get("aoi_area_ha"),
        "metric_pre": r.get("pre_loss_ha_yr"),
        "metric_post": r.get("post_loss_ha_yr"),
        "metric_change_pct": r.get("change_pct"),
        "implied_claimed": r.get("implied_avoided_ha_yr"),
        "implied_observed": r.get("observed_reduction_ha_yr"),
        "ratio_obs_to_claim": r.get("ratio_observed_to_claimed"),
        "n_observations": None,
        "implied_capture_rate": None,
        "severity": sev,
        "scan_status": r.get("status"),
    }


def normalize_methane(r: dict) -> dict:
    sev = r.get("severity", r.get("status", "?"))
    return {
        "id": r.get("id"),
        "name": r.get("name", ""),
        "country": r.get("country", ""),
        "type": "methane",
        "subtype": (r.get("category") or "")[:30],
        "claim_tco2_yr": r.get("claim_tco2_yr"),
        "aoi_or_loc": f"{r.get('lat'):.3f},{r.get('lon'):.3f}" if r.get("lat") else None,
        "metric_pre": None,
        "metric_post": r.get("mean_obs_kghr"),
        "metric_change_pct": None,
        "implied_claimed": r.get("claim_capture_kghr"),
        "implied_observed": r.get("mean_obs_kghr"),
        "ratio_obs_to_claim": (r.get("leakage_to_capture_ratio")),
        "n_observations": r.get("n_observations"),
        "implied_capture_rate": r.get("implied_capture_rate"),
        "severity": sev,
        "scan_status": r.get("status"),
    }


def main():
    rows = []

    forest_path = DATA_DIR / "forest_scan_results.json"
    if forest_path.exists():
        with open(forest_path) as f:
            for r in json.load(f):
                rows.append(normalize_forest(r))
    print(f"Forest rows: {sum(1 for r in rows if r['type']=='forest')}", file=sys.stderr)

    methane_path = DATA_DIR / "methane_scan_results.json"
    if methane_path.exists():
        with open(methane_path) as f:
            for r in json.load(f):
                rows.append(normalize_methane(r))
    print(f"Methane rows: {sum(1 for r in rows if r['type']=='methane')}", file=sys.stderr)

    # Sort: severity rank ascending (worst first), then claim_tco2_yr descending (biggest claim first)
    def sort_key(r):
        sev = r.get("severity") or "?"
        rank = SEVERITY_RANK.get(sev, 99)
        claim = -(r.get("claim_tco2_yr") or 0)
        return (rank, claim)

    rows.sort(key=sort_key)

    # CSV output
    out_csv = DATA_DIR / "league_table.csv"
    fields = ["id", "name", "country", "type", "subtype", "claim_tco2_yr",
              "aoi_or_loc", "metric_pre", "metric_post", "metric_change_pct",
              "implied_claimed", "implied_observed", "ratio_obs_to_claim",
              "n_observations", "implied_capture_rate", "severity", "scan_status"]
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Wrote {len(rows)} rows to {out_csv}", file=sys.stderr)

    # Severity distribution
    from collections import Counter
    sev_counts = Counter(r["severity"] for r in rows)
    print("\nSeverity distribution:")
    for sev in sorted(sev_counts, key=lambda s: SEVERITY_RANK.get(s, 99)):
        print(f"  {sev:<28} {sev_counts[sev]:>4}")

    # Sum of claimed reductions by severity
    print("\nClaimed tCO2/yr by severity (sum):")
    sev_claim = {}
    for r in rows:
        sev = r["severity"]
        sev_claim[sev] = sev_claim.get(sev, 0) + (r.get("claim_tco2_yr") or 0)
    for sev in sorted(sev_claim, key=lambda s: SEVERITY_RANK.get(s, 99)):
        print(f"  {sev:<28} {sev_claim[sev]:>14,.0f}")

    # Top 25 worst offenders
    print("\n=== TOP 25 WORST OFFENDERS (by severity rank, then claim size) ===")
    worst = [r for r in rows if r["severity"] in
             ("RED_FLAG_NEGATIVE", "RED_FLAG_LOW_CAPTURE", "SEVERE_UNDERDELIVERY",
              "SEVERE_LOW_CAPTURE", "MODERATE_UNDERDELIVERY", "MODERATE_LOW_CAPTURE")]
    print(f"\n{'ID':<6} {'Type':<8} {'Country':<22} {'Claim(tCO2/yr)':>14} {'Severity':<22} Name")
    print("-" * 130)
    for r in worst[:25]:
        c = r.get("claim_tco2_yr") or 0
        print(f"{r['id']:<6} {r['type']:<8} {r['country'][:22]:<22} {c:>14,.0f} {r['severity']:<22} {r['name'][:50]}")


if __name__ == "__main__":
    main()
