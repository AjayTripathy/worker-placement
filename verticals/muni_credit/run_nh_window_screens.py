"""Run NH framework on multiple windows and compare.

Reuses run_nh_union_screen.py logic but parameterizes by data directory.
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

from detectors.union_runner import run, measure_exclusion_alpha

HERE = Path(__file__).parent
DATA = HERE / "data"
OUTPUTS = HERE / "outputs"

CA_TEY_MULTIPLIER = 1 / (1 - 0.37 - 0.133)
HONEST_BPS_PER_PP = 4


def normalize_outcome(oc):
    if oc is None: return None
    mapping = {
        # Default class
        "DOWNGRADE_EQUIVALENT": "DOWNGRADE",
        "GOING_CONCERN_NEGATIVE_EQUITY": "MULTI_DOWNGRADE",
        "POST_DEFAULT_REORGANIZATION": "DEFAULT",
        "DISTRESS_GOING_CONCERN": "MULTI_DOWNGRADE",
        "OUTLOOK_NEGATIVE": "AFFIRM_NEGATIVE_OUTLOOK",
        "AFFIRM_NEGATIVE": "AFFIRM_NEGATIVE_OUTLOOK",
        "MERGER_DOWNGRADE": "MULTI_DOWNGRADE",
        "MULTI_NOTCH_DOWNGRADE": "MULTI_DOWNGRADE",
        "COVENANT_BREACH": "DOWNGRADE",
        "COVENANT_BREACH_NO_BOND_DEFAULT": "DOWNGRADE",
        "RESTRUCTURING": "MULTI_DOWNGRADE",
        "TERMINATED_BY_MERGER": "AFFIRM_STABLE",
        # Agent-introduced classes (multi-window NH test)
        "NO_DEFAULT_AFFIRM": "AFFIRM_STABLE",
        "NO_DEFAULT_AFFIRM_AT_END": "AFFIRM_STABLE",
        "NO_DEFAULT_BUT_OPERATIONAL_STRESS": "AFFIRM_NEGATIVE_OUTLOOK",
        "AFFIRM_STABLE_WITH_MA_EVENT": "AFFIRM_STABLE",
        "DEFAULT_BANKRUPTCY": "DEFAULT",
        # Precursor in Window A means the actual default was in Window B — so for Window A,
        # this obligor was already in default at snapshot. Treat as UNVERIFIABLE (already-distressed,
        # not a NEW in-window event we're predicting).
        "DEFAULT_BANKRUPTCY_PRECURSOR": "UNVERIFIABLE",
        # Survived our window but had distress AFTER — for our window, no deterioration to predict
        "SURVIVED_WINDOW_BUT_CLOSED_LATER": "AFFIRM_STABLE",
        "SURVIVED_WINDOW_DEFAULTED_POST_WINDOW": "AFFIRM_STABLE",
        "SURVIVED_WINDOW_DISTRESS_POST_WINDOW": "AFFIRM_STABLE",
        "SURVIVED_WINDOW": "AFFIRM_STABLE",
        "UNVERIFIABLE_LOW_RATED_BUT_INSURED": "UNVERIFIABLE",
        "UNVERIFIABLE_UNRATED_NO_KNOWN_DISTRESS": "AFFIRM_STABLE",
    }
    return mapping.get(oc, oc)


def load_window_data(data_dir: Path):
    detector_data = {}
    ma_fires = {}
    outcomes = {}
    for f in sorted(data_dir.glob("*.json")):
        if f.name.startswith("_"):
            continue
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
        ma_events = d.get("ma_events") or d.get("ma_events_in_window") or []
        ma_fires[name] = any(e.get("leverage_impact") == "high" for e in ma_events)
        vo = d.get("verified_outcome") or {}
        oc = vo.get("computed_outcome_class") if isinstance(vo, dict) else None
        outcomes[name] = normalize_outcome(oc or d.get("computed_outcome_class"))
    return detector_data, ma_fires, outcomes


def run_window(label: str, data_dir: Path):
    print(f"\n{'=' * 80}\n{label}\n{'=' * 80}")
    if not data_dir.exists():
        print(f"  Data dir missing: {data_dir}")
        return None
    detector_data, ma_fires, outcomes = load_window_data(data_dir)
    print(f"Detector data: {len(detector_data)} obligors")
    outcome_dist = Counter(outcomes.values())
    print(f"Outcome distribution: {dict(outcome_dist)}")

    result = run(detector_data, ma_leverage_fires=ma_fires)
    print(f"Universe: {result['n_universe']}, excluded: {result['n_excluded']}, clean: {result['n_clean']}")
    print(f"Fire rates: {dict((k, f'{v*100:.0f}%') for k, v in result['detector_fire_rates'].items())}")
    print(f"Excluded obligors:")
    for r in result['per_obligor']:
        if r['excluded']:
            print(f"  {r['obligor']:<48} fired_by: {r['fired_by']}  outcome: {outcomes.get(r['obligor'], '?')}")

    print(f"\nExclusion alpha:")
    results = {}
    for thresh in ("loose", "strict"):
        alpha = measure_exclusion_alpha(result, outcomes, threshold=thresh)
        pp = alpha.get('exclusion_alpha_pp')
        results[thresh] = alpha
        if pp is not None:
            est_bps = pp * HONEST_BPS_PER_PP
            est_tey = est_bps * CA_TEY_MULTIPLIER
            print(f"  {thresh.upper()}: full {alpha['full_evaluable']} ({alpha['full_n_deteriorated']} det), "
                  f"clean {alpha['clean_evaluable']} ({alpha['clean_n_deteriorated']} det), "
                  f"excluded {alpha['excluded_evaluable']} ({alpha['excluded_n_deteriorated']} det)")
            print(f"  EXCLUSION ALPHA: {pp:+.1f} pp = ~{est_bps:.0f} bps muni / ~{est_tey:.0f} bps CA TEY")
    return results


def main():
    windows = [
        ("WINDOW A — COVID STRESS (snapshot 2019-12-31, outcomes 2020-2022)",
         DATA / "nh_stressed_2019_2022" / "per_obligor"),
        ("WINDOW B — PRE-COVID BLIND (snapshot 2017-12-31, outcomes 2018-2019)",
         DATA / "nh_blind_2017_2019" / "per_obligor"),
    ]
    all_results = {}
    for label, dirpath in windows:
        all_results[label] = run_window(label, dirpath)

    print(f"\n{'=' * 80}\nMULTI-WINDOW COMPARISON\n{'=' * 80}")
    print(f"{'Window':<60} {'LOOSE':<10} {'STRICT':<10}")
    print(f"{'CA NH In-sample (2022-12-31 → 2025-Q1)':<60} {'+14.3':<10} {'+14.3':<10}")
    for label, r in all_results.items():
        if r:
            loose = r['loose'].get('exclusion_alpha_pp')
            strict = r['strict'].get('exclusion_alpha_pp')
            label_short = label.split('—')[0].strip()
            print(f"{label_short:<60} {loose:+.1f}    {strict:+.1f}" if loose is not None else f"{label_short}: no data")


if __name__ == "__main__":
    main()
