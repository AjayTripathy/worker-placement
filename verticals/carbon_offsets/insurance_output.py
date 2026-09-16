"""
Insurance-grade output format.

Converts the league table into actuarial JSON suitable for ingestion by carbon
insurance underwriters (Kita, Oka, CarbonPool, etc.).

Per-project output:
  - P(invalidation) over multiple horizons with confidence intervals
  - Methodology citation
  - Evidence trail
  - Severity tier (for human-readable sorting)

Portfolio aggregation:
  - Given a set of project_ids + retired tonnage, compute:
    - Expected invalidated tonnage
    - VaR at 95% / 99%
    - Correlation matrix across projects (geographic + temporal + methodology)
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict, Counter
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).parent / "data"


def load_data():
    """Load all needed inputs: scan results, calibrated probabilities, project metadata."""
    sc_results = {}
    sc_path = DATA_DIR / "forest_scan_results_v2.json"
    if sc_path.exists():
        with open(sc_path) as f:
            for r in json.load(f):
                sc_results[str(r["id"])] = r

    methane_results = {}
    m_path = DATA_DIR / "methane_scan_results.json"
    if m_path.exists():
        with open(m_path) as f:
            for r in json.load(f):
                methane_results[str(r["id"])] = r

    # Mangrove-specific scan results (GMW-based methodology — see score_mangrove.py)
    mangrove_results = {}
    mg_path = DATA_DIR / "mangrove_scan_results.json"
    if mg_path.exists():
        with open(mg_path) as f:
            for r in json.load(f):
                mangrove_results[str(r["id"])] = r

    calib = {}
    c_path = DATA_DIR / "calibrated_probabilities.json"
    if c_path.exists():
        with open(c_path) as f:
            for r in json.load(f):
                calib[str(r["id"])] = r

    with open(DATA_DIR / "verra_projects.json") as f:
        all_projects = json.load(f)
    seen = {}
    for p in all_projects:
        seen[p["resourceIdentifier"]] = p
    projects_by_id = seen

    return sc_results, methane_results, mangrove_results, calib, projects_by_id


def build_per_project_record(pid, sc_results, methane_results, mangrove_results, calib, projects_by_id):
    """Build the actuarial-grade output for a single project."""
    project = projects_by_id.get(pid, {})
    sc = sc_results.get(pid)
    methane = methane_results.get(pid)
    mangrove = mangrove_results.get(pid)
    cal = calib.get(pid)

    record = {
        "project_id": pid,
        "verra_url": f"https://registry.verra.org/app/projectDetail/VCS/{pid}",
        "name": project.get("resourceName"),
        "country": project.get("country"),
        "current_status": project.get("resourceStatus"),
        "protocol": project.get("protocols"),
        "subcategory": project.get("protocolSubCategories"),
        "claim_tco2_yr": project.get("estAnnualEmissionReductions"),
        "crediting_period": {
            "start": project.get("creditingPeriodStartDate"),
            "end": project.get("creditingPeriodEndDate"),
        },
        "evidence": {},
        "probability_of_invalidation": None,
        "severity_tier": None,
        "methodology": [],
    }

    # Add forest synthetic-control evidence
    if sc and sc.get("status") == "ok":
        record["evidence"]["synthetic_control"] = {
            "method": "buffer_ring_5_to_30km",
            "project_aoi_ha": sc.get("project_total_aoi_ha"),
            "buffer_aoi_ha": sc.get("buffer_total_aoi_ha"),
            "project_forest_2000_ha": sc.get("project_forest_2000_ha"),
            "buffer_forest_2000_ha": sc.get("buffer_forest_2000_ha"),
            "project_annual_loss_rate": sc.get("project_annual_loss_rate"),
            "buffer_annual_loss_rate": sc.get("buffer_annual_loss_rate"),
            "counterfactual_loss_ha_yr": sc.get("counterfactual_loss_ha_yr"),
            "observed_avoided_ha_yr": sc.get("observed_avoided_ha_yr"),
            "implied_avoided_ha_yr": sc.get("implied_avoided_ha_yr"),
            "ratio_observed_to_claimed": sc.get("ratio_observed_to_claimed"),
            "data_source": "Hansen Global Forest Change v1.11",
            "split_year": sc.get("split_year"),
            "tiles_processed": sc.get("tiles"),
        }
        record["severity_tier"] = sc.get("severity")
        record["methodology"].append("West et al. 2020 (PNAS) synthetic-control matched-neighbor approach")

    # Add methane evidence
    if methane and methane.get("status") == "ok":
        record["evidence"]["methane_observation"] = {
            "method": "carbon_mapper_l4a_plume_aggregation",
            "n_observations": methane.get("n_observations"),
            "mean_obs_kghr": methane.get("mean_obs_kghr"),
            "median_obs_kghr": methane.get("median_obs_kghr"),
            "max_obs_kghr": methane.get("max_obs_kghr"),
            "claim_capture_kghr": methane.get("claim_capture_kghr"),
            "implied_capture_rate": methane.get("implied_capture_rate"),
            "leakage_to_capture_ratio": methane.get("leakage_to_capture_ratio"),
            "plume_dates_observed": methane.get("plume_dates"),
            "sample_plumes": methane.get("sample_plumes"),
            "data_source": "Carbon Mapper STAC L4A point-source CH4 plume detections",
        }
        if record["severity_tier"] is None:
            record["severity_tier"] = methane.get("severity")
        record["methodology"].append("Carbon Mapper L4A plume detection sector-filtered (IPCC 6A/1B/3)")

    # Add mangrove evidence (GMW v3 + coastline buffer methodology)
    if mangrove and mangrove.get("status") == "ok":
        record["evidence"]["mangrove_synthetic_control"] = {
            "method": "gmw_v3_coastline_buffer",
            "aoi_mangrove_2010_ha": mangrove.get("aoi_mangrove_2010_ha"),
            "aoi_mangrove_2020_ha": mangrove.get("aoi_mangrove_2020_ha"),
            "aoi_net_change_ha": mangrove.get("aoi_net_change_ha_2010_2020"),
            "buffer_mangrove_2010_ha": mangrove.get("buffer_mangrove_2010_ha"),
            "buffer_mangrove_2020_ha": mangrove.get("buffer_mangrove_2020_ha"),
            "buffer_net_change_ha": mangrove.get("buffer_net_change_ha_2010_2020"),
            "aoi_change_rate_per_decade": mangrove.get("aoi_change_rate_per_ha_decade"),
            "buffer_change_rate_per_decade": mangrove.get("buffer_change_rate_per_ha_decade"),
            "counterfactual_change_ha_yr": mangrove.get("counterfactual_change_ha_yr"),
            "observed_aoi_change_ha_yr": mangrove.get("observed_aoi_change_ha_yr"),
            "project_benefit_ha_yr": mangrove.get("project_benefit_ha_yr"),
            "implied_benefit_ha_yr": mangrove.get("implied_benefit_ha_yr"),
            "ratio_observed_to_claimed": mangrove.get("ratio_observed_to_claimed"),
            "carbon_stock_tco2_ha": mangrove.get("carbon_stock_tco2_ha"),
            "data_source": "Global Mangrove Watch v3 (Bunting et al. 2018/2022); 25m resolution; 2010 + 2020 layers",
        }
        if record["severity_tier"] is None or record["severity_tier"] == "no_evidence":
            record["severity_tier"] = mangrove.get("severity")
        record["methodology"].append("Global Mangrove Watch v3 + coastline-following buffer ring; mangrove-specific carbon stock 350 tCO2/ha (Donato et al. 2011)")

    # Add calibrated probabilities
    if cal:
        record["probability_of_invalidation"] = cal.get("predictions", {}).get("horizons", {})
        record["methodology"].append("Logistic regression calibrated on Verra Withdrawn/Rejected vs Registered outcomes; bootstrap CI. Per validation, the model is dominated by demographic features (country, subcat, age, claim size) rather than satellite divergence; treat as a regulator-pattern predictor that corroborates direct evidence rather than a standalone source.")

    # Evidence-type classification — what kind of signal supports this record?
    has_satellite_direct = bool(
        (sc and sc.get("status") == "ok" and sc.get("divergence_normalized") is not None)
        or (methane and methane.get("status") == "ok" and methane.get("implied_capture_rate") is not None)
        or (mangrove and mangrove.get("status") == "ok" and mangrove.get("ratio_observed_to_claimed") is not None)
    )
    has_calibration_only = bool(cal and not has_satellite_direct)

    if has_satellite_direct:
        record["evidence_type"] = "satellite_direct"
        record["evidence_strength"] = "high"
        record["evidence_summary"] = (
            f"Direct satellite observation: {record['severity_tier']}. "
            f"{'Calibrated regulator-pattern P(5yr) corroborates: ' + format(cal['predictions']['horizons']['p_5yr']['estimate'], '.0%') if cal else 'No calibration available.'}"
        )
    elif has_calibration_only:
        record["evidence_type"] = "regulator_pattern_only"
        record["evidence_strength"] = "moderate"
        p5 = cal['predictions']['horizons']['p_5yr']['estimate']
        record["evidence_summary"] = (
            f"No direct satellite signal (project KML missing or scan failed). "
            f"Demographic-pattern P(5yr) = {p5:.0%} based on country, sub-category, age, and claim size. "
            f"This is pattern recognition; not direct evidence."
        )
    else:
        record["evidence_type"] = "no_evidence"
        record["evidence_strength"] = "none"
        record["severity_tier"] = "no_evidence"
        record["evidence_summary"] = "No usable satellite scan or calibration prediction."

    return record


def _p_5yr_for_record(rec):
    """Get P(invalidation_5yr) for a project, falling back to severity-tier
    heuristic if no calibration probability exists.

    Severity → P(5yr) mapping is a buyer-side heuristic for satellite-direct evidence:
      RED_FLAG_NEGATIVE: 0.85 (project lost more forest than matched neighbor — strong invalidation signal)
      SEVERE_UNDERDELIVERY: 0.65 (<25% of claimed avoidance)
      MODERATE_UNDERDELIVERY: 0.30 (25–75% of claim)
      PASS: 0.10 (≥75% of claim)
      LOW_CAPTURE variants for methane mirror the forest tiers.
    These are first-order calibrations; underwriters would refine against their own loss data.
    """
    SEV_P5YR = {
        "RED_FLAG_NEGATIVE": 0.85, "RED_FLAG_LOW_CAPTURE": 0.85,
        "SEVERE_UNDERDELIVERY": 0.65, "SEVERE_LOW_CAPTURE": 0.65,
        "MODERATE_UNDERDELIVERY": 0.30, "MODERATE_LOW_CAPTURE": 0.30,
        "PASS": 0.10,
    }
    p = (rec.get("probability_of_invalidation") or {}).get("p_5yr", {}).get("estimate") if rec.get("probability_of_invalidation") else None
    if p is not None:
        return p, "calibration"
    sev = rec.get("severity_tier")
    if sev in SEV_P5YR:
        return SEV_P5YR[sev], f"severity_{sev}"
    return None, None


def build_portfolio_view(retired_credits, per_project_records):
    """
    Given retired credits = [{project_id, tonnes_retired, vintage_year, retirement_date}, ...]
    and per_project_records, compute portfolio-level risk metrics.
    """
    total_tonnes = sum(r["tonnes_retired"] for r in retired_credits)

    # Per-credit expected invalidated tonnes
    expected_invalidated = 0
    var_95 = 0
    project_tonnes = defaultdict(float)
    p_source_counts = defaultdict(int)
    for r in retired_credits:
        pid = r["project_id"]
        rec = per_project_records.get(pid)
        if not rec:
            continue
        p_5yr, source = _p_5yr_for_record(rec)
        if p_5yr is None:
            continue
        p_source_counts[source] += 1
        expected_invalidated += r["tonnes_retired"] * p_5yr
        project_tonnes[pid] += r["tonnes_retired"]

    # Concentration: HHI on project-level exposure
    if total_tonnes > 0:
        shares = [t / total_tonnes for t in project_tonnes.values()]
        hhi = sum(s ** 2 for s in shares)
    else:
        hhi = 0

    # Geographic concentration
    country_tonnes = defaultdict(float)
    subcat_tonnes = defaultdict(float)
    for r in retired_credits:
        pid = r["project_id"]
        rec = per_project_records.get(pid)
        if not rec:
            continue
        country_tonnes[rec.get("country", "unknown")] += r["tonnes_retired"]
        subcat_tonnes[rec.get("subcategory", "unknown")] += r["tonnes_retired"]

    # Bootstrap-based VaR estimate (rough; assumes independent project failures)
    # For each project, sample Bernoulli with p=p_5yr, sum invalidated tonnes
    # Repeat 1000 times, take 95th and 99th percentile
    np.random.seed(42)
    n_sims = 1000
    sim_invalidated = np.zeros(n_sims)
    for r in retired_credits:
        pid = r["project_id"]
        rec = per_project_records.get(pid)
        if not rec:
            continue
        p_5yr, _ = _p_5yr_for_record(rec)
        if p_5yr is None:
            continue
        # Independent invalidation per project (correlation matrix is future work)
        outcomes = (np.random.random(n_sims) < p_5yr).astype(float)
        sim_invalidated += outcomes * r["tonnes_retired"]

    var_95 = float(np.percentile(sim_invalidated, 95))
    var_99 = float(np.percentile(sim_invalidated, 99))
    expected_loss = float(sim_invalidated.mean())
    median_loss = float(np.median(sim_invalidated))

    # Evidence-type breakdown: what fraction of portfolio has direct vs pattern-only support
    evidence_tonnes = defaultdict(float)
    for r in retired_credits:
        rec = per_project_records.get(r["project_id"])
        if not rec:
            continue
        evidence_tonnes[rec.get("evidence_type", "no_evidence")] += r["tonnes_retired"]

    return {
        "total_retired_tonnes": total_tonnes,
        "n_projects": len(project_tonnes),
        "n_credits": len(retired_credits),
        "expected_invalidated_tonnes_5yr": expected_loss,
        "median_invalidated_tonnes_5yr": median_loss,
        "var_95_5yr": var_95,
        "var_99_5yr": var_99,
        "expected_invalidation_rate_5yr": expected_loss / total_tonnes if total_tonnes else 0,
        "evidence_breakdown": {
            "satellite_direct_tonnes": evidence_tonnes.get("satellite_direct", 0),
            "regulator_pattern_only_tonnes": evidence_tonnes.get("regulator_pattern_only", 0),
            "no_evidence_tonnes": evidence_tonnes.get("no_evidence", 0),
            "satellite_direct_share": evidence_tonnes.get("satellite_direct", 0) / total_tonnes if total_tonnes else 0,
        },
        "p_estimate_sources": dict(p_source_counts),
        "concentration": {
            "hhi_project_level": hhi,
            "top_3_country_share": sum(sorted(country_tonnes.values(), reverse=True)[:3]) / total_tonnes if total_tonnes else 0,
            "country_distribution": dict(sorted(country_tonnes.items(), key=lambda x: -x[1])[:10]),
            "subcat_distribution": dict(sorted(subcat_tonnes.items(), key=lambda x: -x[1])),
        },
        "methodology_notes": [
            "Per-project invalidation probabilities from logistic regression calibrated on Verra status outcomes",
            "Forest projects: synthetic-control divergence (Hansen GFC vs buffer-ring counterfactual)",
            "Methane projects: Carbon Mapper plume-derived implied capture rate",
            "VaR computed via 1000-iteration Monte Carlo with independent per-project invalidation events (correlation matrix not yet implemented)",
            "5-year horizon based on training data (Verra projects registered before 2020 observed through 2024)",
            "Confidence: bootstrap 200 resamples; HHI ranges 0 (perfectly diversified) to 1 (single project)",
        ],
    }


def main():
    sc_results, methane_results, mangrove_results, calib, projects_by_id = load_data()

    # Build per-project records for all scored projects
    all_pids = set(sc_results.keys()) | set(methane_results.keys()) | set(mangrove_results.keys()) | set(calib.keys())
    print(f"Building actuarial records for {len(all_pids)} projects", file=sys.stderr)

    per_project = {}
    for pid in all_pids:
        per_project[pid] = build_per_project_record(pid, sc_results, methane_results, mangrove_results, calib, projects_by_id)

    # Save per-project records
    out_path = DATA_DIR / "actuarial_records.json"
    with open(out_path, "w") as f:
        json.dump(per_project, f, indent=2, default=str)
    print(f"Saved {len(per_project)} actuarial records to {out_path}", file=sys.stderr)

    # Build TWO sample portfolios for buyer demo:
    #   (a) "worst by calibration" — uses regulator-pattern model (existing)
    #   (b) "worst by satellite-direct evidence" — the saleable case (new)
    sample_views = {}

    if calib:
        sample_portfolio_calib = []
        sorted_calib = sorted(calib.values(),
                              key=lambda r: -(r.get("predictions", {}).get("horizons", {}).get("p_5yr", {}).get("estimate", 0)))
        for r in sorted_calib[:30]:
            sample_portfolio_calib.append({
                "project_id": r["id"],
                "tonnes_retired": 10000,
                "vintage_year": 2022,
                "retirement_date": "2024-01-01",
            })
        sample_views["worst_by_calibration"] = {
            "portfolio_metadata": {
                "name": "Worst-30 by calibrated P(5yr) — pattern-recognition driven, mostly regulator-pattern_only",
                "total_credits": 300_000,
                "buyer_archetype": "demo_buyer_pattern_signal",
            },
            "portfolio_view": build_portfolio_view(sample_portfolio_calib, per_project),
            "per_credit_records": sample_portfolio_calib,
        }

    # Worst-30 by satellite-direct severity (RED_FLAG > SEVERE > MODERATE > PASS)
    SEV_RANK = {"RED_FLAG_NEGATIVE": 0, "RED_FLAG_LOW_CAPTURE": 0,
                "SEVERE_UNDERDELIVERY": 1, "SEVERE_LOW_CAPTURE": 1,
                "MODERATE_UNDERDELIVERY": 2, "MODERATE_LOW_CAPTURE": 2,
                "PASS": 3}
    sat_direct = [r for r in per_project.values() if r.get("evidence_type") == "satellite_direct"]
    sat_direct.sort(key=lambda r: (SEV_RANK.get(r.get("severity_tier"), 9),
                                   -(r.get("claim_tco2_yr") or 0)))
    sample_portfolio_sat = []
    for r in sat_direct[:30]:
        sample_portfolio_sat.append({
            "project_id": r["project_id"],
            "tonnes_retired": 10000,
            "vintage_year": 2022,
            "retirement_date": "2024-01-01",
        })
    if sample_portfolio_sat:
        sample_views["worst_by_satellite_direct"] = {
            "portfolio_metadata": {
                "name": f"Worst-{len(sample_portfolio_sat)} by satellite-direct severity — direct remote-sensing evidence",
                "total_credits": len(sample_portfolio_sat) * 10_000,
                "buyer_archetype": "demo_buyer_satellite_signal",
            },
            "portfolio_view": build_portfolio_view(sample_portfolio_sat, per_project),
            "per_credit_records": sample_portfolio_sat,
        }

    sample_path = DATA_DIR / "sample_portfolio_view.json"
    with open(sample_path, "w") as f:
        json.dump(sample_views, f, indent=2, default=str)

        for view_name, view in sample_views.items():
            pv = view["portfolio_view"]
            print(f"\nPortfolio: {view['portfolio_metadata']['name']}", file=sys.stderr)
            print(f"  Total: {pv['total_retired_tonnes']:,.0f} tonnes across {pv['n_projects']} projects", file=sys.stderr)
            print(f"  Expected invalidated 5yr: {pv['expected_invalidated_tonnes_5yr']:>10,.0f} t  ({pv['expected_invalidation_rate_5yr']:.1%})", file=sys.stderr)
            print(f"  VaR 95% / 99% (5yr):     {pv['var_95_5yr']:>10,.0f}  /  {pv['var_99_5yr']:,.0f} t", file=sys.stderr)
            eb = pv['evidence_breakdown']
            print(f"  Evidence: satellite_direct={eb['satellite_direct_share']:.0%}, "
                  f"regulator_pattern={eb['regulator_pattern_only_tonnes']/pv['total_retired_tonnes']:.0%}, "
                  f"none={eb['no_evidence_tonnes']/pv['total_retired_tonnes']:.0%}", file=sys.stderr)

    # Print evidence-type summary across entire registry
    type_counts = Counter(r.get("evidence_type", "no_evidence") for r in per_project.values())
    print(f"\n=== Evidence-type breakdown across {len(per_project)} actuarial records ===", file=sys.stderr)
    for t, n in type_counts.most_common():
        print(f"  {t}: {n}", file=sys.stderr)


if __name__ == "__main__":
    main()
