"""Run the union-of-detectors exclusion screen.

Merges the 5 predictive detectors + M&A leverage signal, then measures
exclusion alpha (clean basket deterioration rate vs full universe rate)
using verified rating outcomes.
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
OUTPUTS.mkdir(exist_ok=True)


def load_detector_data() -> dict:
    """Merge all detector_data files into one per-obligor dict."""
    files_to_load = [
        "detector_data_auditor_pension.json",
        "detector_data_filing_payor.json",
        "detector_data_honesty_going_concern.json",
        "detector_data_doj_fca.json",  # may not exist yet
        "detector_data_cms_hrrp_cia.json",  # may not exist yet
    ]
    merged = {}
    for fname in files_to_load:
        path = DATA / fname
        if not path.exists():
            continue
        d = json.loads(path.read_text())
        for obligor, entry in d.get("obligors", {}).items():
            if obligor not in merged:
                merged[obligor] = {}
            # For DOJ FCA, pull in the in_sample_period block
            if "doj_fca" in entry and isinstance(entry["doj_fca"], dict):
                isp = entry["doj_fca"].get("in_sample_period_2020_2024")
                if isp:
                    merged[obligor]["doj_fca"] = isp
                else:
                    merged[obligor]["doj_fca"] = entry["doj_fca"]
            # CMS HRRP + CIA data has window-suffixed keys; map to engine input shape
            if "cms_readmissions_in_sample" in entry:
                merged[obligor]["cms_readmissions"] = entry["cms_readmissions_in_sample"]
            if "hhs_oig_cia_in_sample" in entry:
                merged[obligor]["hhs_oig_cia"] = entry["hhs_oig_cia_in_sample"]
            for k, v in entry.items():
                if k not in ("doj_fca", "cms_readmissions_in_sample", "hhs_oig_cia_in_sample",
                             "cms_readmissions_blind", "hhs_oig_cia_blind"):
                    merged[obligor][k] = v
    return merged


def load_ma_leverage_fires() -> dict:
    """Load M&A leverage RED signals from existing ma_leverage_events."""
    ma_path = DATA / "ma_leverage_events.json"
    if not ma_path.exists():
        return {}
    ma_data = json.loads(ma_path.read_text())
    op_path = DATA / "operating_metrics.json"
    op_data = json.loads(op_path.read_text()) if op_path.exists() else {"obligors": {}}

    fires = {}
    for obligor, entry in ma_data.get("obligors", {}).items():
        events = entry.get("ma_events", [])
        rev = (op_data.get("obligors", {}).get(obligor, {}).get("total_operating_revenue_usd")
               or entry.get("annual_revenue_at_event_usd"))
        for e in events:
            dv = e.get("deal_value_usd")
            impact = e.get("leverage_impact")
            if impact == "high":
                fires[obligor] = True
                break
            if dv and rev and (dv / rev) >= 0.15:
                fires[obligor] = True
                break
        if obligor not in fires:
            fires[obligor] = False
    return fires


def load_verified_outcomes(use_extended: bool = False) -> dict:
    """Load verified outcomes, keyed by canonical name AND aliases AND state-stripped.

    use_extended: if True, load from extended directory (Dec 2022 - May 2026, 40 mo window).
                  if False, load from original (Dec 2022 - Mar 2025, 27 mo window).
    """
    if use_extended:
        outcomes_dir = DATA / "verified_outcomes_extended" / "per_obligor"
        if not outcomes_dir.exists():
            print(f"WARNING: extended outcomes dir not found, falling back to original")
            outcomes_dir = DATA / "verified_outcomes_2023_2025" / "per_obligor"
    else:
        outcomes_dir = DATA / "verified_outcomes_2023_2025" / "per_obligor"
    outcomes = {}
    for f in sorted(outcomes_dir.glob("*.json")):
        d = json.loads(f.read_text())
        name = d.get("obligor_name")
        oc = d.get("computed_outcome_class")
        if not name or not oc:
            continue
        outcomes[name] = oc
        # Also index by state-stripped name
        bare = re.sub(r"\s*\([^)]+\)\s*", "", name).strip()
        if bare and bare not in outcomes:
            outcomes[bare] = oc
        for alias in d.get("obligor_aliases", []) or []:
            if alias and alias not in outcomes:
                outcomes[alias] = oc
    return outcomes


def main():
    detector_data = load_detector_data()
    print(f"Detector data loaded for {len(detector_data)} obligors")

    ma_fires = load_ma_leverage_fires()
    print(f"M&A fires: {sum(1 for v in ma_fires.values() if v)} of {len(ma_fires)}")

    import sys
    use_extended = "--extended" in sys.argv
    outcomes = load_verified_outcomes(use_extended=use_extended)
    print(f"Verified outcomes ({'EXTENDED 40-mo window' if use_extended else 'original 27-mo window'}): {len(outcomes)} keys")

    # Run union
    result = run(detector_data, ma_leverage_fires=ma_fires)
    print(f"\n=== UNION RESULT ===")
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

    # Measure exclusion alpha
    print(f"\n=== EXCLUSION ALPHA (clean basket vs full universe) ===")
    for thresh in ("loose", "strict"):
        alpha = measure_exclusion_alpha(result, outcomes, threshold=thresh)
        print(f"\n{thresh.upper()} threshold:")
        print(f"  Full universe: {alpha['full_evaluable']} evaluable, "
              f"{alpha['full_n_deteriorated']} deteriorated = "
              f"{(alpha['full_deterioration_rate'] or 0)*100:.0f}% rate")
        print(f"  Clean basket:  {alpha['clean_evaluable']} evaluable, "
              f"{alpha['clean_n_deteriorated']} deteriorated = "
              f"{(alpha['clean_deterioration_rate'] or 0)*100:.0f}% rate")
        print(f"  Excluded basket: {alpha['excluded_evaluable']} evaluable, "
              f"{alpha['excluded_n_deteriorated']} deteriorated = "
              f"{(alpha['excluded_deterioration_rate'] or 0)*100:.0f}% rate")
        if alpha['exclusion_alpha_pp'] is not None:
            print(f"  *** EXCLUSION ALPHA: {alpha['exclusion_alpha_pp']:+.1f} pp ***")

    # Per-detector marginal contribution: leave-one-out
    print(f"\n=== PER-DETECTOR MARGINAL EXCLUSION ALPHA (leave-one-out) ===")
    detector_names = list(result['detector_fire_rates'].keys())
    full_alpha_loose = measure_exclusion_alpha(result, outcomes, threshold="loose")
    full_alpha_pp = full_alpha_loose.get('exclusion_alpha_pp', 0)
    print(f"All detectors: {full_alpha_pp:+.1f} pp")
    for det in detector_names:
        # Recompute without this detector
        per_obligor_loo = []
        for r in result['per_obligor']:
            fired_by_loo = [d for d in r['fired_by'] if d != det]
            per_obligor_loo.append({
                **r,
                "fired_by": fired_by_loo,
                "excluded": len(fired_by_loo) > 0,
            })
        loo_clean = [r['obligor'] for r in per_obligor_loo if not r['excluded']]
        loo_excl = [r['obligor'] for r in per_obligor_loo if r['excluded']]
        loo_result = {"clean_basket": loo_clean, "excluded_basket": loo_excl}
        loo_alpha = measure_exclusion_alpha(loo_result, outcomes, threshold="loose")
        marginal = full_alpha_pp - (loo_alpha.get('exclusion_alpha_pp') or 0)
        print(f"  Remove {det}: {(loo_alpha.get('exclusion_alpha_pp') or 0):+.1f} pp "
              f"(marginal contribution: {marginal:+.1f} pp)")

    out_path = OUTPUTS / "union_exclusion_screen_results.json"
    out_path.write_text(json.dumps({
        "universe_result": result,
        "exclusion_alpha_loose": measure_exclusion_alpha(result, outcomes, threshold="loose"),
        "exclusion_alpha_strict": measure_exclusion_alpha(result, outcomes, threshold="strict"),
    }, indent=2, default=str))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
