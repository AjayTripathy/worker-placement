"""CA CCRC muni union exclusion screen."""
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

CA_TEY_MULTIPLIER = 1 / (1 - 0.37 - 0.133)
HONEST_BPS_PER_PP = 4


def normalize_outcome(oc):
    if oc is None: return None
    mapping = {
        "DOWNGRADE_EQUIVALENT": "DOWNGRADE",
        "DISTRESS_GOING_CONCERN": "MULTI_DOWNGRADE",
        "OUTLOOK_NEGATIVE": "AFFIRM_NEGATIVE_OUTLOOK",
        "TERMINATED_BY_MERGER": "AFFIRM_STABLE",
    }
    return mapping.get(oc, oc)


def load_ccrc_data():
    detector_data = {}
    ma_fires = {}
    outcomes = {}
    ccrc_dir = DATA / "ccrc_per_obligor"
    for f in sorted(ccrc_dir.glob("*.json")):
        d = json.loads(f.read_text())
        name = d.get("obligor_name")
        if not name or name.startswith("_"):
            continue
        detector_data[name] = {}
        # nh_* CMS keys are included because a CCRC's skilled-nursing wing carries
        # a CMS provider number and is star/SFF/CMP-rated like a standalone SNF.
        # They are NOT stored in the ccrc_per_obligor file; the CMS-resolved data
        # lives in the parallel nh_per_obligor/<same_filename> record, so merge
        # from there below.
        for k in ("auditor_change", "pension_funded_ratio", "late_filing", "payor_concentration",
                  "doj_fca", "going_concern", "ccrc_occupancy", "ccrc_days_cash",
                  "nh_cms_star_rating", "nh_special_focus_facility", "nh_civil_monetary_penalty"):
            if k in d and isinstance(d[k], dict):
                detector_data[name][k] = d[k]
        nh_counterpart = DATA / "nh_per_obligor" / f.name
        if nh_counterpart.exists():
            nh_d = json.loads(nh_counterpart.read_text())
            for k in ("nh_cms_star_rating", "nh_special_focus_facility", "nh_civil_monetary_penalty"):
                if k not in detector_data[name] and isinstance(nh_d.get(k), dict):
                    detector_data[name][k] = nh_d[k]
        ma_events = d.get("ma_events_2023_2025") or d.get("ma_events_in_window") or []
        ma_fires[name] = any(e.get("leverage_impact") == "high" for e in ma_events)
        vo = d.get("verified_outcome") or {}
        oc = vo.get("computed_outcome_class") if isinstance(vo, dict) else None
        outcomes[name] = normalize_outcome(oc or d.get("computed_outcome_class"))
    return detector_data, ma_fires, outcomes


def main():
    print("=" * 80)
    print("CA CCRC MUNI — UNION EXCLUSION SCREEN")
    print("=" * 80)
    detector_data, ma_fires, outcomes = load_ccrc_data()
    print(f"Detector data: {len(detector_data)} obligors")

    # Brain pre-flight: every CCRC obligor is sector=ccrc (which implies snf, so
    # the CMS star/SFF/CMP detectors are expected). Surface any detector that
    # APPLIES_TO this sector but has no data fed in.
    cov = coverage_report(detector_data, "ccrc")
    print_coverage_report(cov, title="CCRC DISPATCH COVERAGE (before resolve)")

    # Gap -> fetch: resolve obligor names to CMS CCNs to fill the nh_* detectors
    # the validator just flagged as applicable-but-unfed.
    res = fill_cms_gaps(detector_data)
    print_resolution_report(res, title="CCRC CMS CCN RESOLUTION")
    cov = coverage_report(detector_data, "ccrc")
    print_coverage_report(cov, title="CCRC DISPATCH COVERAGE (after resolve)")

    outcome_dist = Counter(outcomes.values())
    print(f"\nOutcome distribution:")
    for cls, n in outcome_dist.most_common():
        print(f"  {cls}: {n}")

    result = run(detector_data, ma_leverage_fires=ma_fires)
    print(f"\n=== UNION RESULT ===")
    print(f"Universe: {result['n_universe']}, excluded: {result['n_excluded']}, clean: {result['n_clean']}")
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
        print(f"\n{thresh.upper()}: full {alpha['full_evaluable']}/{alpha['full_n_deteriorated']}, "
              f"clean {alpha['clean_evaluable']}/{alpha['clean_n_deteriorated']}, "
              f"excluded {alpha['excluded_evaluable']}/{alpha['excluded_n_deteriorated']}")
        if alpha['exclusion_alpha_pp'] is not None:
            pp = alpha['exclusion_alpha_pp']
            est_bps = pp * HONEST_BPS_PER_PP
            est_tey = est_bps * CA_TEY_MULTIPLIER
            print(f"  EXCLUSION ALPHA: {pp:+.1f} pp = ~{est_bps:.0f} bps muni / ~{est_tey:.0f} bps CA TEY")

    out_path = OUTPUTS / "ca_ccrc_union_results.json"
    out_path.write_text(json.dumps({
        "universe_result": result,
        "alpha_loose": measure_exclusion_alpha(result, outcomes, threshold="loose"),
        "alpha_strict": measure_exclusion_alpha(result, outcomes, threshold="strict"),
    }, indent=2, default=str))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
