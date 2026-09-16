"""Blind CA hospital muni union exclusion screen — Dec 2016 → Dec 2019 window.

Same engine as run_ca_union_screen.py, pointed at blind data:
  - Universe from data/blind_ca_2016_universe.json (27 obligors)
  - Per-obligor data from data/blind_ca_oos_2017_2019/per_obligor/*.json
  - HCAI uses current data (SPC ratings change slowly; 2030 deadline is consistent)

Compares blind alpha vs in-sample CA (+3.8 pp LOOSE / +5.8 pp STRICT).
"""
from __future__ import annotations

import json
import glob
import re
from pathlib import Path

from detectors.union_runner import run, measure_exclusion_alpha
from detectors import hcai_seismic

HERE = Path(__file__).parent
DATA = HERE / "data"
OUTPUTS = HERE / "outputs"

CA_TEY_MULTIPLIER = 1 / (1 - 0.37 - 0.133)


CANONICAL_NAMES = {
    "Adventist Health System/West": "Adventist Health (West Coast)",
    "Children's Hospital Los Angeles": "Children's Hospital Los Angeles",
    "Verity Health System of California": "Verity Health System",
    "Marin General Hospital (MarinHealth Medical Center)": "MarinHealth Medical Center",
    "MarinHealth Medical Center (Marin General Hospital)": "MarinHealth Medical Center",
    "St. Joseph Health System (pre-Providence merger)": "St. Joseph Health (CA)",
    "Cedars-Sinai Medical Center": "Cedars-Sinai Health System",
    "Dignity Health": "Dignity Health (pre-CommonSpirit)",
    "El Camino Hospital District": "El Camino Health",
    "Rady Children's Hospital — San Diego": "Rady Children's Hospital",
    "Children's Hospital of Orange County": "Children's Hospital of Orange County (CHOC)",
    "Lucile Salter Packard Children's Hospital at Stanford": "Lucile Salter Packard Children's Hospital at Stanford",
    "Community Hospital of the Monterey Peninsula": "CHOMP",
    "Tahoe Forest Hospital District": "Tahoe Forest Hospital District",
    "Eisenhower Medical Center": "Eisenhower Medical Center",
    "Kaweah Delta Health Care District": "Kaweah Health",
}


def canonicalize(name: str) -> str:
    return CANONICAL_NAMES.get(name, name)


def normalize_outcome(oc: str) -> str:
    if oc is None:
        return None
    mapping = {
        "DISTRESS_GOING_CONCERN": "MULTI_DOWNGRADE",
        "DISTRESS_NO_PUBLIC_RATING": "MULTI_DOWNGRADE",
        "POST_DEFAULT_REORGANIZATION": "DEFAULT",
        "ACQUIRED_UPGRADE": "AFFIRM_POSITIVE_OUTLOOK",
        "ACQUIRED": "AFFIRM_STABLE",
        "ACQUIRED_DISTRESSED": "MULTI_DOWNGRADE",
        "DOWNGRADE_TO_NON_IG": "MULTI_DOWNGRADE",
        "OUTLOOK_NEGATIVE": "AFFIRM_NEGATIVE_OUTLOOK",
        "AFFIRM_NEGATIVE": "AFFIRM_NEGATIVE_OUTLOOK",
        "OUTLOOK_REVISION_NEGATIVE": "AFFIRM_NEGATIVE_OUTLOOK",
        "TERMINATED_BY_MERGER": "AFFIRM_STABLE",
        "MERGER_PENDING": "AFFIRM_STABLE",
        "MERGER_DOWNGRADE": "MULTI_DOWNGRADE",
        "MERGER_DOWNGRADE_BLEND": "MULTI_DOWNGRADE",
        "MULTI_NOTCH_DOWNGRADE": "MULTI_DOWNGRADE",
        "UPGRADE_MULTI_AGENCY": "UPGRADE",
        "MIXED_UPGRADE_PATH_WITH_COVENANT_WARNING": "AFFIRM_STABLE",
        "MIXED": "AFFIRM_STABLE",
        "PROBABLE_AFFIRM_STABLE_LOW_CONFIDENCE": "AFFIRM_STABLE",
    }
    return mapping.get(oc, oc)


def load_blind_ca_data() -> tuple[dict, dict, dict]:
    detector_data = {}
    ma_fires = {}
    outcomes = {}

    blind_dir = DATA / "blind_ca_oos_2017_2019" / "per_obligor"
    for f in sorted(blind_dir.glob("*.json")):
        d = json.loads(f.read_text())
        name = canonicalize(d.get("obligor_name"))
        if not name:
            continue
        if name not in detector_data:
            detector_data[name] = {}

        # Map detector fields
        for k in ("auditor_change", "pension_funded_ratio", "late_filing", "payor_concentration",
                  "doj_fca"):
            if k in d and isinstance(d[k], dict):
                detector_data[name][k] = d[k]

        # Operating metrics (FY2016)
        if "operating_metrics_fy2016" in d:
            detector_data[name]["_operating_metrics"] = d["operating_metrics_fy2016"]

        # M&A: collect events, compute fire flag
        ma_events = d.get("ma_events_2017_2018") or []
        rev = (d.get("operating_metrics_fy2016") or {}).get("total_operating_revenue_usd")
        ma_fire = False
        for e in ma_events:
            impact = e.get("leverage_impact")
            dv = e.get("deal_value_usd")
            if impact == "high":
                ma_fire = True
                break
            if dv and rev and (dv / rev) >= 0.15:
                ma_fire = True
                break
        ma_fires[name] = ma_fire

        # Outcome
        vo = d.get("verified_outcome") or {}
        oc = vo.get("computed_outcome_class") if isinstance(vo, dict) else None
        if not oc:
            oc = d.get("computed_outcome_class")
        outcomes[name] = normalize_outcome(oc)

    # Add HCAI as overlay (NOT in active detector registry — used for overlay reporting)
    hcai_path = DATA / "detector_data_ca_hcai_seismic.json"
    if hcai_path.exists():
        hcai = json.loads(hcai_path.read_text())
        for raw_name, entry in hcai.get("obligors", {}).items():
            name = canonicalize(raw_name)
            if name in detector_data and "hcai_seismic" in entry:
                detector_data[name]["hcai_seismic"] = entry["hcai_seismic"]

    return detector_data, ma_fires, outcomes


def main():
    print("=" * 80)
    print("BLIND CA HOSPITAL MUNI — UNION EXCLUSION SCREEN (2016 universe, 2017-2019 outcomes)")
    print("=" * 80)
    detector_data, ma_fires, outcomes = load_blind_ca_data()
    print(f"Detector data: {len(detector_data)} obligors")
    print(f"M&A fires: {sum(1 for v in ma_fires.values() if v)} of {len(ma_fires)}")
    print(f"Outcomes loaded: {len(outcomes)}")

    from collections import Counter
    outcome_dist = Counter(outcomes.values())
    print(f"\nOutcome distribution:")
    for cls, n in outcome_dist.most_common():
        print(f"  {cls}: {n}")

    result = run(detector_data, ma_leverage_fires=ma_fires)
    print(f"\n=== BLIND UNION RESULT ===")
    print(f"Universe: {result['n_universe']}, excluded: {result['n_excluded']}, clean: {result['n_clean']}")
    print(f"Exclusion rate: {result['exclusion_rate']*100:.0f}%")
    print(f"\nPer-detector fire rates:")
    for det, rate in sorted(result['detector_fire_rates'].items(), key=lambda kv: -kv[1]):
        n_fire = result['detector_fire_counts'][det]
        n_eval = result['detector_eval_counts'].get(det, 0)
        print(f"  {det}: {n_fire}/{n_eval} = {rate*100:.0f}%")

    print(f"\nExcluded obligors:")
    for r in result['per_obligor']:
        if r['excluded']:
            outcome = outcomes.get(r['obligor'], '?')
            print(f"  {r['obligor']:<55} fired_by: {r['fired_by']} outcome: {outcome}")

    print(f"\n=== BLIND CA EXCLUSION ALPHA ===")
    for thresh in ("loose", "strict"):
        alpha = measure_exclusion_alpha(result, outcomes, threshold=thresh)
        print(f"\n{thresh.upper()} threshold:")
        print(f"  Full universe: {alpha['full_evaluable']} evaluable, "
              f"{alpha['full_n_deteriorated']} deteriorated = "
              f"{(alpha['full_deterioration_rate'] or 0)*100:.0f}% rate")
        print(f"  Clean basket:  {alpha['clean_evaluable']} evaluable, "
              f"{alpha['clean_n_deteriorated']} deteriorated = "
              f"{(alpha['clean_deterioration_rate'] or 0)*100:.0f}% rate")
        print(f"  Excluded:      {alpha['excluded_evaluable']} evaluable, "
              f"{alpha['excluded_n_deteriorated']} deteriorated = "
              f"{(alpha['excluded_deterioration_rate'] or 0)*100:.0f}% rate")
        if alpha['exclusion_alpha_pp'] is not None:
            print(f"  *** BLIND CA EXCLUSION ALPHA: {alpha['exclusion_alpha_pp']:+.1f} pp ***")
            est_muni_alpha_bps = alpha['exclusion_alpha_pp'] * 30
            est_tey_alpha_bps = est_muni_alpha_bps * CA_TEY_MULTIPLIER
            print(f"  Approx muni alpha: {est_muni_alpha_bps:.0f} bps")
            print(f"  Approx CA TEY alpha: {est_tey_alpha_bps:.0f} bps")

    print(f"\n=== COMPARISON: IN-SAMPLE CA vs BLIND CA ===")
    is_alpha_loose = 3.8
    is_alpha_strict = 5.8
    blind_loose = measure_exclusion_alpha(result, outcomes, threshold='loose').get('exclusion_alpha_pp')
    blind_strict = measure_exclusion_alpha(result, outcomes, threshold='strict').get('exclusion_alpha_pp')
    print(f"In-sample CA (2022-2025, n=34): +{is_alpha_loose} pp LOOSE / +{is_alpha_strict} pp STRICT")
    print(f"Blind CA   (2017-2019, n=27): {blind_loose:+.1f} pp LOOSE / {blind_strict:+.1f} pp STRICT" if blind_loose is not None else "")

    out_path = OUTPUTS / "blind_ca_union_exclusion_results.json"
    out_path.write_text(json.dumps({
        "blind_universe_result": result,
        "blind_alpha_loose": measure_exclusion_alpha(result, outcomes, threshold="loose"),
        "blind_alpha_strict": measure_exclusion_alpha(result, outcomes, threshold="strict"),
        "in_sample_comparison": {"loose": is_alpha_loose, "strict": is_alpha_strict},
    }, indent=2, default=str))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
