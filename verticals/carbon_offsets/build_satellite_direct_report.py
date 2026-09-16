"""Satellite-direct findings report — the saleable subset.

Filters actuarial records to projects where we have *direct* satellite evidence
(successful V2 scan or methane plume observation), and produces a clean per-project
report card suitable for pitching to insurance underwriters or rating-agency buyers.

This is what differentiates Signal OS carbon from a regulator-pattern model: we
can point to a Hansen-derived loss rate, a Carbon Mapper plume detection, or a
buffer-ring counterfactual computation per project.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


SEVERITY_ORDER = {
    "RED_FLAG_NEGATIVE": 0,    # observed loss > buffer counterfactual
    "SEVERE_UNDERDELIVERY": 1, # observed/claimed < 0.25
    "MODERATE_UNDERDELIVERY": 2,
    "PASS": 3,
    None: 9,
    "no_evidence": 9,
}


def main():
    with open(DATA_DIR / "actuarial_records.json") as f:
        records = json.load(f)

    direct = {pid: r for pid, r in records.items() if r.get("evidence_type") == "satellite_direct"}
    print(f"Satellite-direct records: {len(direct)} of {len(records)} total", file=sys.stderr)

    # Group by severity
    by_severity = defaultdict(list)
    for r in direct.values():
        by_severity[r.get("severity_tier") or "unknown"].append(r)

    severity_counts = {k: len(v) for k, v in by_severity.items()}
    print(f"\nSeverity distribution:", file=sys.stderr)
    for sev in ("RED_FLAG_NEGATIVE", "SEVERE_UNDERDELIVERY", "MODERATE_UNDERDELIVERY", "PASS"):
        if sev in severity_counts:
            print(f"  {sev}: {severity_counts[sev]}", file=sys.stderr)

    # Build the report
    report = {
        "report_type": "satellite_direct_findings",
        "generated_at": __import__("datetime").datetime.utcnow().isoformat(),
        "n_projects": len(direct),
        "severity_distribution": severity_counts,
        "methodology_summary": {
            "forest": "Synthetic-control buffer-ring (5–30km donut) per West et al. 2020 PNAS approach. Hansen Global Forest Change v1.11 30m annual loss data. Project AOI vs. matched-neighbor buffer. Severity from ratio observed_avoided / claimed_avoided.",
            "methane": "Carbon Mapper L4A point-source plume detections within facility AOI. Sector-filtered (IPCC 6A/1B/3). Implied capture rate from claim_capture / (claim + leakage).",
        },
        "what_this_tells_underwriters": (
            "For each project below, we have direct satellite-derived evidence of "
            "delivery vs. claim. RED_FLAG_NEGATIVE means the project area lost more "
            "forest than the matched-neighbor counterfactual — phantom credit pattern. "
            "SEVERE_UNDERDELIVERY means observed avoided loss is <25% of claimed. "
            "These are not pattern-match predictions; they are reconciliations of "
            "primary remote-sensing data against project claims."
        ),
        "projects": [],
    }

    # Sort by severity then by claim size (biggest first within tier)
    sorted_projects = sorted(
        direct.values(),
        key=lambda r: (
            SEVERITY_ORDER.get(r.get("severity_tier"), 9),
            -(r.get("claim_tco2_yr") or 0),
        ),
    )

    for r in sorted_projects:
        sc_ev = r.get("evidence", {}).get("synthetic_control")
        m_ev = r.get("evidence", {}).get("methane_observation")
        mg_ev = r.get("evidence", {}).get("mangrove_synthetic_control")
        cal_p5 = None
        if r.get("probability_of_invalidation"):
            cal_p5 = r["probability_of_invalidation"].get("p_5yr", {}).get("estimate")

        entry = {
            "project_id": r["project_id"],
            "verra_url": r["verra_url"],
            "name": r.get("name"),
            "country": r.get("country"),
            "current_status": r.get("current_status"),
            "subcategory": r.get("subcategory"),
            "claim_tco2_yr": r.get("claim_tco2_yr"),
            "severity_tier": r.get("severity_tier"),
            "calibrated_p_invalidation_5yr_corroboration": cal_p5,
        }
        if sc_ev:
            ratio = sc_ev.get("ratio_observed_to_claimed")
            entry["satellite_signal"] = {
                "kind": "forest_synthetic_control",
                "project_loss_rate_per_yr": sc_ev.get("project_annual_loss_rate"),
                "buffer_loss_rate_per_yr": sc_ev.get("buffer_annual_loss_rate"),
                "observed_avoided_ha_yr": sc_ev.get("observed_avoided_ha_yr"),
                "claimed_implied_avoided_ha_yr": sc_ev.get("implied_avoided_ha_yr"),
                "ratio_observed_to_claimed": ratio,
                "interpretation": (
                    "project lost more than counterfactual" if ratio is not None and ratio < 0
                    else f"observed delivers {ratio*100:.0f}% of claim" if ratio is not None
                    else "ratio uncomputable"
                ),
                "data_source": sc_ev.get("data_source"),
            }
        if m_ev:
            entry["satellite_signal"] = {
                "kind": "methane_plume_observation",
                "n_plume_observations": m_ev.get("n_observations"),
                "mean_observed_kghr": m_ev.get("mean_obs_kghr"),
                "claim_capture_kghr": m_ev.get("claim_capture_kghr"),
                "implied_capture_rate": m_ev.get("implied_capture_rate"),
                "data_source": m_ev.get("data_source"),
            }
        if mg_ev:
            ratio = mg_ev.get("ratio_observed_to_claimed")
            entry["satellite_signal"] = {
                "kind": "mangrove_extent_change",
                "aoi_mangrove_2010_ha": mg_ev.get("aoi_mangrove_2010_ha"),
                "aoi_mangrove_2020_ha": mg_ev.get("aoi_mangrove_2020_ha"),
                "aoi_change_rate_per_decade": mg_ev.get("aoi_change_rate_per_decade"),
                "buffer_change_rate_per_decade": mg_ev.get("buffer_change_rate_per_decade"),
                "project_benefit_ha_yr": mg_ev.get("project_benefit_ha_yr"),
                "implied_benefit_ha_yr": mg_ev.get("implied_benefit_ha_yr"),
                "ratio_observed_to_claimed": ratio,
                "interpretation": (
                    "project lost mangrove faster than counterfactual" if ratio is not None and ratio < 0
                    else f"observed delivers {ratio*100:.0f}% of claim" if ratio is not None
                    else "ratio uncomputable"
                ),
                "data_source": mg_ev.get("data_source"),
            }
        report["projects"].append(entry)

    out_path = DATA_DIR / "satellite_direct_report.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"\nSaved {len(report['projects'])} satellite-direct project records to {out_path}", file=sys.stderr)

    # Also print a markdown summary of the worst tier
    worst = [p for p in sorted_projects if p.get("severity_tier") in ("RED_FLAG_NEGATIVE", "SEVERE_UNDERDELIVERY")]
    if worst:
        print(f"\n=== {len(worst)} satellite-direct RED_FLAG / SEVERE projects ===", file=sys.stderr)
        print(f"{'ID':<6} {'Severity':<22} {'Country':<20} {'Claim tCO2/yr':>15} {'Ratio':>8}  {'Method':<12}  Name", file=sys.stderr)
        print("-" * 145, file=sys.stderr)
        for r in worst[:35]:
            # Pull ratio from whichever evidence type is present
            sc = r.get("evidence", {}).get("synthetic_control") or {}
            mg = r.get("evidence", {}).get("mangrove_synthetic_control") or {}
            ratio = sc.get("ratio_observed_to_claimed") or mg.get("ratio_observed_to_claimed")
            ratio_str = f"{ratio*100:+.0f}%" if ratio is not None else "—"
            method = "forest" if sc else ("mangrove" if mg else "methane" if r.get("evidence", {}).get("methane_observation") else "?")
            print(
                f"{r['project_id']:<6} {(r.get('severity_tier') or '')[:22]:<22} {(r.get('country') or '')[:20]:<20} "
                f"{(r.get('claim_tco2_yr') or 0):>15,.0f} {ratio_str:>8}  {method:<12}  {(r.get('name') or '')[:50]}",
                file=sys.stderr,
            )


if __name__ == "__main__":
    main()
