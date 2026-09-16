"""Run the union exclusion screen on the BLIND 2016 universe.

Same engine as run_union_screen.py, pointed at blind data.
Outcomes come from data/blind_oos_2017_2019/per_obligor/*.json.
M&A leverage signals derived from ma_events_2017_2018 inside those files.
"""
from __future__ import annotations

import json
import glob
import re
from pathlib import Path

from detectors.union_runner import run, measure_exclusion_alpha

HERE = Path(__file__).parent
DATA = HERE / "data"
OUTPUTS = HERE / "outputs"


def load_blind_detector_data() -> dict:
    auditor_pension = json.loads((DATA / "blind_detector_data_auditor_pension.json").read_text())
    filing_payor = json.loads((DATA / "blind_detector_data_filing_payor.json").read_text())
    merged = {}
    for obligor in set(auditor_pension.get("obligors", {})) | set(filing_payor.get("obligors", {})):
        merged[obligor] = {
            **auditor_pension.get("obligors", {}).get(obligor, {}),
            **filing_payor.get("obligors", {}).get(obligor, {}),
        }
    return merged


def load_blind_ma_leverage_fires() -> dict:
    """Pull M&A events from blind per-obligor files and apply the same rule."""
    fires = {}
    blind_dir = DATA / "blind_oos_2017_2019" / "per_obligor"
    for f in sorted(blind_dir.glob("*.json")):
        d = json.loads(f.read_text())
        name = d.get("obligor_name")
        if not name:
            continue
        # Strip state suffix to match the auditor/pension keys
        bare = re.sub(r"\s*\([^)]+\)\s*", "", name).strip()
        rev = (d.get("operating_metrics_fy2016") or {}).get("total_operating_revenue_usd")
        events = d.get("ma_events_2017_2018") or []
        fired = False
        for e in events:
            dv = e.get("deal_value_usd")
            impact = e.get("leverage_impact")
            if impact == "high":
                fired = True
                break
            if dv and rev and (dv / rev) >= 0.15:
                fired = True
                break
        fires[name] = fired
        fires[bare] = fired
    return fires


def load_blind_outcomes() -> dict:
    outcomes = {}
    blind_dir = DATA / "blind_oos_2017_2019" / "per_obligor"

    def normalize_outcome(oc):
        mapping = {
            "ACQUIRED_UPGRADE": "AFFIRM_POSITIVE_OUTLOOK",
            "ACQUIRED": "AFFIRM_STABLE",
            "ACQUIRED_DISTRESSED": "MULTI_DOWNGRADE",
            "DOWNGRADE_TO_NON_IG": "MULTI_DOWNGRADE",
            "OUTLOOK_NEGATIVE": "AFFIRM_NEGATIVE_OUTLOOK",
            "AFFIRM_NEGATIVE": "AFFIRM_NEGATIVE_OUTLOOK",
            "TERMINATED_BY_MERGER": "AFFIRM_STABLE",
            "MERGER_PENDING": "AFFIRM_STABLE",
        }
        return mapping.get(oc, oc)

    for f in sorted(blind_dir.glob("*.json")):
        d = json.loads(f.read_text())
        name = d.get("obligor_name")
        oc = normalize_outcome(d.get("computed_outcome_class"))
        if name and oc:
            outcomes[name] = oc
            bare = re.sub(r"\s*\([^)]+\)\s*", "", name).strip()
            if bare not in outcomes:
                outcomes[bare] = oc
    return outcomes


def main():
    detector_data = load_blind_detector_data()
    print(f"Blind detector data: {len(detector_data)} obligors")

    ma_fires = load_blind_ma_leverage_fires()
    n_ma_fire = sum(1 for v in ma_fires.values() if v) // 2  # divided by 2 because we index by both name + bare
    print(f"Blind M&A fires: ~{n_ma_fire}")

    outcomes = load_blind_outcomes()
    print(f"Blind outcomes loaded: {len(outcomes)} keys")

    result = run(detector_data, ma_leverage_fires=ma_fires)
    print(f"\n=== BLIND UNION RESULT ===")
    print(f"Universe: {result['n_universe']}, excluded: {result['n_excluded']}, clean: {result['n_clean']}")
    print(f"Exclusion rate: {result['exclusion_rate']*100:.0f}%")
    print(f"\nPer-detector fire rates:")
    for det, rate in sorted(result['detector_fire_rates'].items(), key=lambda kv: -kv[1]):
        n_fire = result['detector_fire_counts'][det]
        n_eval = result['detector_eval_counts'].get(det, 0)
        print(f"  {det}: {n_fire}/{n_eval} = {rate*100:.0f}%")

    print(f"\nFired obligors:")
    for r in result['per_obligor']:
        if r['excluded']:
            print(f"  {r['obligor']}: fired by {r['fired_by']}")

    print(f"\n=== BLIND EXCLUSION ALPHA ===")
    for thresh in ("loose", "strict"):
        alpha = measure_exclusion_alpha(result, outcomes, threshold=thresh)
        print(f"\n{thresh.upper()} threshold:")
        print(f"  Full universe: {alpha['full_evaluable']} eval, {alpha['full_n_deteriorated']} det = "
              f"{(alpha['full_deterioration_rate'] or 0)*100:.0f}% rate")
        print(f"  Clean basket:  {alpha['clean_evaluable']} eval, {alpha['clean_n_deteriorated']} det = "
              f"{(alpha['clean_deterioration_rate'] or 0)*100:.0f}% rate")
        print(f"  Excluded:      {alpha['excluded_evaluable']} eval, {alpha['excluded_n_deteriorated']} det = "
              f"{(alpha['excluded_deterioration_rate'] or 0)*100:.0f}% rate")
        if alpha['exclusion_alpha_pp'] is not None:
            print(f"  *** BLIND EXCLUSION ALPHA: {alpha['exclusion_alpha_pp']:+.1f} pp ***")

    print(f"\n=== COMPARISON: IN-SAMPLE vs BLIND ===")
    print(f"In-sample (n=49, 2022-2025): +8.4 pp exclusion alpha (LOOSE)")
    blind_alpha = measure_exclusion_alpha(result, outcomes, threshold="loose").get('exclusion_alpha_pp')
    print(f"Blind     (n={result['n_universe']}, 2017-2019): {blind_alpha:+.1f} pp exclusion alpha (LOOSE)" if blind_alpha is not None else "Blind: not computable")

    out_path = OUTPUTS / "blind_union_exclusion_results.json"
    out_path.write_text(json.dumps({
        "blind_universe_result": result,
        "blind_alpha_loose": measure_exclusion_alpha(result, outcomes, threshold="loose"),
        "blind_alpha_strict": measure_exclusion_alpha(result, outcomes, threshold="strict"),
    }, indent=2, default=str))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
