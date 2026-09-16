"""CA standalone nursing home muni union exclusion screen.

Universe: 14 CA SNF muni obligors.
Detectors: full library + nh_cms_star_rating + nh_special_focus_facility +
            nh_civil_monetary_penalty.
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

from detectors.union_runner import run, measure_exclusion_alpha
from detectors.dispatch_index import coverage_report, print_coverage_report
from detectors.cms_ccn_resolver import fill_cms_gaps, print_resolution_report

HERE = Path(__file__).parent
DATA = HERE / "data"
OUTPUTS = HERE / "outputs"
OUTPUTS.mkdir(exist_ok=True)

CA_TEY_MULTIPLIER = 1 / (1 - 0.37 - 0.133)
HONEST_BPS_PER_PP = 4  # ~ pp_alpha × bps_per_pp = annualized return alpha


def normalize_outcome(oc: str) -> str:
    if oc is None:
        return None
    mapping = {
        "DOWNGRADE_EQUIVALENT": "DOWNGRADE",
        "GOING_CONCERN_NEGATIVE_EQUITY": "MULTI_DOWNGRADE",
        "DISTRESS_GOING_CONCERN": "MULTI_DOWNGRADE",
        "DISTRESS_NO_PUBLIC_RATING": "MULTI_DOWNGRADE",
        "POST_DEFAULT_REORGANIZATION": "DEFAULT",
        "OUTLOOK_NEGATIVE": "AFFIRM_NEGATIVE_OUTLOOK",
        "AFFIRM_NEGATIVE": "AFFIRM_NEGATIVE_OUTLOOK",
        "TERMINATED_BY_MERGER": "AFFIRM_STABLE",
    }
    return mapping.get(oc, oc)


def load_nh_data() -> tuple[dict, dict, dict]:
    detector_data = {}
    ma_fires = {}
    outcomes = {}

    nh_dir = DATA / "nh_per_obligor"
    for f in sorted(nh_dir.glob("*.json")):
        d = json.loads(f.read_text())
        name = d.get("obligor_name")
        if not name:
            continue
        detector_data[name] = {}
        for k in ("auditor_change", "pension_funded_ratio", "late_filing", "payor_concentration",
                  "doj_fca", "going_concern", "nh_cms_star_rating", "nh_special_focus_facility",
                  "nh_civil_monetary_penalty"):
            if k in d and isinstance(d[k], dict):
                detector_data[name][k] = d[k]

        # M&A
        ma_events = d.get("ma_events_2023_2025") or d.get("ma_events_in_window") or []
        ma_fire = any(
            e.get("leverage_impact") == "high" for e in ma_events
        )
        ma_fires[name] = ma_fire

        # Outcome
        vo = d.get("verified_outcome") or {}
        oc = vo.get("computed_outcome_class") if isinstance(vo, dict) else None
        if not oc:
            oc = d.get("computed_outcome_class")
        outcomes[name] = normalize_outcome(oc)

    return detector_data, ma_fires, outcomes


def main():
    print("=" * 80)
    print("CA NURSING HOME MUNI — UNION EXCLUSION SCREEN")
    print("=" * 80)
    detector_data, ma_fires, outcomes = load_nh_data()
    print(f"Detector data: {len(detector_data)} obligors")
    print(f"M&A fires: {sum(1 for v in ma_fires.values() if v)} of {len(ma_fires)}")

    # Brain pre-flight: every obligor here is sector=snf. Surface any detector
    # that APPLIES_TO snf but had no data fed in (silent-skip guard).
    cov = coverage_report(detector_data, "snf")
    print_coverage_report(cov, title="NH DISPATCH COVERAGE (before resolve)")

    # Gap -> fetch: resolve obligor names to CMS CCNs to fill any nh_* gaps.
    res = fill_cms_gaps(detector_data)
    print_resolution_report(res, title="NH CMS CCN RESOLUTION")
    cov = coverage_report(detector_data, "snf")
    print_coverage_report(cov, title="NH DISPATCH COVERAGE (after resolve)")

    outcome_dist = Counter(outcomes.values())
    print(f"\nOutcome distribution:")
    for cls, n in outcome_dist.most_common():
        print(f"  {cls}: {n}")

    result = run(detector_data, ma_leverage_fires=ma_fires)
    print(f"\n=== UNION RESULT ===")
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
            print(f"  {r['obligor']:<48} fired_by: {r['fired_by']}  outcome: {outcome}")

    print(f"\n=== EXCLUSION ALPHA ===")
    for thresh in ("loose", "strict"):
        alpha = measure_exclusion_alpha(result, outcomes, threshold=thresh)
        print(f"\n{thresh.upper()}:")
        print(f"  Full universe: {alpha['full_evaluable']} eval, {alpha['full_n_deteriorated']} det = {(alpha['full_deterioration_rate'] or 0)*100:.0f}%")
        print(f"  Clean basket:  {alpha['clean_evaluable']} eval, {alpha['clean_n_deteriorated']} det = {(alpha['clean_deterioration_rate'] or 0)*100:.0f}%")
        print(f"  Excluded:      {alpha['excluded_evaluable']} eval, {alpha['excluded_n_deteriorated']} det = {(alpha['excluded_deterioration_rate'] or 0)*100:.0f}%")
        if alpha['exclusion_alpha_pp'] is not None:
            pp = alpha['exclusion_alpha_pp']
            est_bps = pp * HONEST_BPS_PER_PP
            est_tey = est_bps * CA_TEY_MULTIPLIER
            print(f"  EXCLUSION ALPHA: {pp:+.1f} pp")
            print(f"  Honest annualized: ~{est_bps:.0f} bps muni / ~{est_tey:.0f} bps CA TEY")

    out_path = OUTPUTS / "ca_nh_union_results.json"
    out_path.write_text(json.dumps({
        "universe_result": result,
        "alpha_loose": measure_exclusion_alpha(result, outcomes, threshold="loose"),
        "alpha_strict": measure_exclusion_alpha(result, outcomes, threshold="strict"),
    }, indent=2, default=str))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
