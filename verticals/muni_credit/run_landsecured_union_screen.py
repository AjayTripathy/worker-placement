"""CA land-secured / Mello-Roos CFD muni union exclusion screen.

V1 runs on the 9-CFD sample from data/landsecured_initial_detector_data/ as
a baseline / sanity test. Once universe is expanded by the dispatch agent
(target: 100-150 CFDs), this same script will produce the validation alpha.

Stale-distress handling: a CFD with `_distress_origination_date` more than
STALE_DISTRESS_YEARS ago is classified as "stale" — framework still flags
it correctly, but alpha is measured only on FRESH-distress exclusions.
This was the bug surfaced by the validation pass (Palmdale CFD 93-1 has
been distressed since 1998 and is fully priced; celebrating it as a
fresh exclude inflates alpha).
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter
from datetime import datetime

from detectors.union_runner import run, measure_exclusion_alpha

HERE = Path(__file__).parent
# Default to expanded 117-CFD universe; fall back to 9-CFD initial sample for legacy
DATA_EXPANDED = HERE / "data" / "landsecured_per_obligor"
DATA_INITIAL = HERE / "data" / "landsecured_initial_detector_data"
DATA = DATA_EXPANDED if DATA_EXPANDED.exists() and any(DATA_EXPANDED.glob("*.json")) else DATA_INITIAL
OUTPUTS = HERE / "outputs"
OUTPUTS.mkdir(exist_ok=True)

CA_TEY_MULTIPLIER = 1 / (1 - 0.37 - 0.133)
HONEST_BPS_PER_PP = 4
STALE_DISTRESS_YEARS = 5
TODAY = datetime(2026, 5, 28)

# CFD-applicable detectors only (skip hospital/NH-specific)
CFD_DETECTOR_KEYS = (
    "value_to_lien_collapse",
    "delinquency_spike",
    "reserve_fund_drawn",
    "reserve_fund_burndown",
    "foreclosure_active",
    "issuer_administration_concern",
    "buildout_stalled",
    "top_taxpayer_concentration",
    "coverage_ratio_thin",
    "developer_bankruptcy",
    # Diligence-replication layer
    "nod_recorder_filing",
    "developer_corp_credit",
)


def parse_iso_date(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", ""))
    except (ValueError, AttributeError):
        return None


def classify_freshness(data: dict) -> str:
    """Classify a CFD's distress as FRESH or STALE based on origination date."""
    origin = parse_iso_date(data.get("_distress_origination_date"))
    if not origin:
        # No origination known → assume fresh until proven otherwise
        return "UNKNOWN"
    years = (TODAY - origin).days / 365.25
    return "STALE" if years > STALE_DISTRESS_YEARS else "FRESH"


def normalize_outcome(oc):
    """Map land-secured outcome classes to canonical set.

    Default class (= bondholder loss):
      DEFAULT, BANKRUPTCY_CH9, RESERVE_DEPLETED, BOND_IMPAIRMENT
    Deterioration class (= material credit weakening, no bondholder loss yet):
      RESERVE_DRAWN, RATING_DOWNGRADE, DELINQ_SPIKE_VERIFIED, FORECLOSURE_ACTIVE
    Stable class:
      AFFIRM_STABLE, NO_DISTRESS
    """
    if oc is None:
        return None
    mapping = {
        "BANKRUPTCY_CH9": "DEFAULT",
        "RESERVE_DEPLETED": "DEFAULT",
        "BOND_IMPAIRMENT": "DEFAULT",
        "RESERVE_DRAWN": "MULTI_DOWNGRADE",
        "RATING_DOWNGRADE": "DOWNGRADE",
        "DELINQ_SPIKE_VERIFIED": "AFFIRM_NEGATIVE_OUTLOOK",
        "FORECLOSURE_ACTIVE": "DOWNGRADE",
        "NO_DISTRESS": "AFFIRM_STABLE",
        "SURVIVED_WINDOW": "AFFIRM_STABLE",
    }
    return mapping.get(oc, oc)


def load_cfd_data():
    detector_data = {}
    outcomes = {}
    distress_freshness = {}
    cfd_metadata = {}

    for f in sorted(DATA.glob("*.json")):
        d = json.loads(f.read_text())
        name = d.get("cfd_name") or d.get("obligor_name")
        if not name:
            continue
        detector_data[name] = {}
        for k in CFD_DETECTOR_KEYS:
            if k in d and isinstance(d[k], dict):
                detector_data[name][k] = d[k]

        # Outcome — multiple possible keys
        vo = d.get("verified_outcome") or {}
        oc = vo.get("computed_outcome_class") if isinstance(vo, dict) else None
        oc = oc or d.get("computed_outcome_class") or d.get("outcome_class")
        outcomes[name] = normalize_outcome(oc)

        # Freshness classification
        distress_freshness[name] = classify_freshness(d)

        cfd_metadata[name] = {
            "cfd_id": d.get("cfd_id"),
            "distress_origination_date": d.get("_distress_origination_date"),
            "freshness": distress_freshness[name],
        }

    return detector_data, outcomes, distress_freshness, cfd_metadata


def main():
    print("=" * 80)
    print("CA LAND-SECURED / CFD MUNI — UNION EXCLUSION SCREEN (BASELINE)")
    print("=" * 80)
    detector_data, outcomes, freshness, meta = load_cfd_data()
    print(f"CFD universe: {len(detector_data)}")

    outcome_dist = Counter(outcomes.values())
    print(f"\nOutcome distribution: {dict(outcome_dist)}")

    freshness_dist = Counter(freshness.values())
    print(f"Distress freshness: {dict(freshness_dist)}")

    result = run(detector_data)
    print(f"\n=== UNION RESULT ===")
    print(f"Universe: {result['n_universe']}, excluded: {result['n_excluded']}, "
          f"clean: {result['n_clean']}")
    print(f"Exclusion rate: {result['exclusion_rate']*100:.0f}%")

    print(f"\nPer-detector fire rates (CFD-relevant only):")
    cfd_only = {k: v for k, v in result["detector_fire_rates"].items() if k in CFD_DETECTOR_KEYS}
    for det, rate in sorted(cfd_only.items(), key=lambda kv: -kv[1]):
        n_fire = result["detector_fire_counts"][det]
        n_eval = result["detector_eval_counts"].get(det, 0)
        print(f"  {det:<35} {n_fire}/{n_eval} = {rate*100:.0f}%")

    print(f"\nExcluded CFDs:")
    for r in result["per_obligor"]:
        if r["excluded"]:
            outcome = outcomes.get(r["obligor"], "?")
            fresh = freshness.get(r["obligor"], "?")
            cfd_fires = [d for d in r["fired_by"] if d in CFD_DETECTOR_KEYS]
            print(f"  {r['obligor']:<60}")
            print(f"    fires: {cfd_fires}")
            print(f"    outcome: {outcome}, freshness: {fresh}")

    print(f"\nClean CFDs:")
    for r in result["per_obligor"]:
        if not r["excluded"]:
            outcome = outcomes.get(r["obligor"], "?")
            print(f"  {r['obligor']:<60} outcome: {outcome}")

    print(f"\n=== EXCLUSION ALPHA (all-vs-clean) ===")
    for thresh in ("loose", "strict"):
        alpha = measure_exclusion_alpha(result, outcomes, threshold=thresh)
        pp = alpha.get("exclusion_alpha_pp")
        if pp is not None:
            est_bps = pp * HONEST_BPS_PER_PP
            est_tey = est_bps * CA_TEY_MULTIPLIER
            print(f"\n{thresh.upper()}:")
            print(f"  Full universe: {alpha['full_evaluable']} eval, "
                  f"{alpha['full_n_deteriorated']} det "
                  f"({(alpha['full_deterioration_rate'] or 0)*100:.0f}%)")
            print(f"  Clean basket:  {alpha['clean_evaluable']} eval, "
                  f"{alpha['clean_n_deteriorated']} det "
                  f"({(alpha['clean_deterioration_rate'] or 0)*100:.0f}%)")
            print(f"  EXCLUSION ALPHA: {pp:+.1f} pp = ~{est_bps:.0f} bps muni / ~{est_tey:.0f} bps CA TEY")
        else:
            print(f"\n{thresh.upper()}: insufficient outcome data to measure alpha (initial sample)")

    print(f"\n=== STALE-vs-FRESH BREAKDOWN ===")
    stale_excluded = [r for r in result["per_obligor"]
                      if r["excluded"] and freshness.get(r["obligor"]) == "STALE"]
    fresh_excluded = [r for r in result["per_obligor"]
                      if r["excluded"] and freshness.get(r["obligor"]) == "FRESH"]
    unknown_excluded = [r for r in result["per_obligor"]
                        if r["excluded"] and freshness.get(r["obligor"]) == "UNKNOWN"]
    print(f"  Stale exclusions (>5yr distressed, alpha already priced): {len(stale_excluded)}")
    for r in stale_excluded:
        print(f"    - {r['obligor']}")
    print(f"  Fresh exclusions (alpha potentially available): {len(fresh_excluded)}")
    for r in fresh_excluded:
        print(f"    - {r['obligor']}")
    print(f"  Unknown freshness: {len(unknown_excluded)}")
    for r in unknown_excluded:
        print(f"    - {r['obligor']}")

    out_path = OUTPUTS / "landsecured_baseline_results.json"
    out_path.write_text(json.dumps({
        "universe_result": result,
        "outcomes": outcomes,
        "freshness": freshness,
        "alpha_loose": measure_exclusion_alpha(result, outcomes, threshold="loose"),
        "alpha_strict": measure_exclusion_alpha(result, outcomes, threshold="strict"),
    }, indent=2, default=str))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
