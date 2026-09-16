"""CA-only hospital muni union exclusion screen.

Reads per-obligor data from data/ca_per_obligor/*.json + HCAI seismic data,
plus existing detector data for the 9 CA names already in main data files.
Runs the full union exclusion screen, reports alpha, and translates to
top-bracket CA TEY (multiplier ~2.01x).
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
OUTPUTS.mkdir(exist_ok=True)

# CA top-bracket TEY multiplier: 1 / (1 - 0.37 - 0.133)
CA_TEY_MULTIPLIER = 1 / (1 - 0.37 - 0.133)


# Canonical name map — merge known duplicate sources into one entry per obligor.
# Keys are alternate forms; values are the canonical name to use.
CANONICAL_NAMES = {
    "Adventist Health": "Adventist Health (West Coast)",
    "Children's Hospital Los Angeles (blind)": "Children's Hospital Los Angeles",
    "Children's Hospital of Orange County (CHOC)": "Children's Hospital of Orange County",
    "CommonSpirit Health (CA Dignity Health hospitals subset)": "CommonSpirit Health (Dignity)",
    "Cottage Health System": "Cottage Health",
    "El Camino Hospital": "El Camino Health",
    "Palomar Health (Palomar Health Care District)": "Palomar Health",
    "Pomona Valley Hospital Medical Center": "Pomona Valley Hospital",
    "Memorial Health Services (dba MemorialCare Health System)": "MemorialCare Health System",
    "Marin Healthcare District (MarinHealth Medical Center)": "MarinHealth Medical Center",
    "Kaweah Delta Health Care District": "Kaweah Health",
    "The Regents of the University of California - Medical Center Pooled Revenue Bonds": "University of California Medical Centers",
    "Providence St. Joseph Health (CA operations subsidiary of Renton, WA parent)": "Providence Health & Services (CA)",
}


def canonicalize(name: str) -> str:
    return CANONICAL_NAMES.get(name, name)


def normalize_outcome(oc: str) -> str:
    """Map new CA-specific outcome classes to canonical."""
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
        "TERMINATED_BY_MERGER": "AFFIRM_STABLE",
        "MERGER_PENDING": "AFFIRM_STABLE",
    }
    return mapping.get(oc, oc)


def load_ca_universe() -> list[str]:
    """Return list of all 39 CA obligor names."""
    d = json.loads((DATA / "ca_hospital_universe.json").read_text())
    return [o["name"] for o in d["obligors"] if "Verity" not in o["name"]]  # exclude defunct


def load_ca_detector_data() -> tuple[dict, dict, dict]:
    """Returns (detector_data, ma_fires, outcomes).

    Pulls from:
      - data/ca_per_obligor/*.json (new CA obligors)
      - data/operating_metrics.json + others (existing 9 CA obligors)
      - data/detector_data_ca_hcai_seismic.json (HCAI for all CA)
      - data/extension_outcomes_2025_2026.json (for extended outcomes)
    """
    detector_data = {}
    ma_fires = {}
    outcomes = {}

    # 1. Load per-obligor CA files
    ca_dir = DATA / "ca_per_obligor"
    for f in sorted(ca_dir.glob("*.json")):
        d = json.loads(f.read_text())
        name = canonicalize(d.get("obligor_name"))
        if not name:
            continue
        # Map per-obligor fields into detector input shapes
        if name not in detector_data:
            detector_data[name] = {}
        if "auditor_change" in d:
            detector_data[name]["auditor_change"] = d["auditor_change"]
        if "pension_funded_ratio" in d:
            detector_data[name]["pension_funded_ratio"] = d["pension_funded_ratio"]
        if "late_filing" in d:
            detector_data[name]["late_filing"] = d["late_filing"]
        if "payor_concentration" in d:
            detector_data[name]["payor_concentration"] = d["payor_concentration"]
        if "doj_fca" in d:
            detector_data[name]["doj_fca"] = d["doj_fca"]
        # M&A: collect events, compute fire flag
        ma_events = d.get("ma_events_in_window") or []
        rev = d.get("operating_metrics", {}).get("total_operating_revenue_usd") if isinstance(d.get("operating_metrics"), dict) else None
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
        outcome_block = d.get("verified_outcome") or d.get("computed_outcome_class")
        if isinstance(outcome_block, dict):
            outcomes[name] = normalize_outcome(outcome_block.get("computed_outcome_class"))
        elif isinstance(outcome_block, str):
            outcomes[name] = normalize_outcome(outcome_block)

    # 2. Augment with existing 9 CA obligors from main data files
    existing_ca = ["Adventist Health (West Coast)", "Loma Linda University Medical Center",
                   "Lompoc Valley Medical Center", "Children's Hospital Los Angeles",
                   "Children's Hospital Los Angeles (CHLA)"]
    # Use existing detector data for these
    for fname in ["detector_data_auditor_pension.json", "detector_data_filing_payor.json",
                  "detector_data_doj_fca.json"]:
        path = DATA / fname
        if not path.exists():
            continue
        existing = json.loads(path.read_text())
        for raw_name, entry in existing.get("obligors", {}).items():
            name = canonicalize(raw_name)
            if name not in detector_data and any(name.startswith(p[:10]) for p in existing_ca):
                detector_data[name] = {}
            if name in detector_data:
                for k in ("auditor_change", "pension_funded_ratio", "late_filing",
                          "payor_concentration"):
                    if k in entry:
                        detector_data[name][k] = entry[k]
                if "doj_fca" in entry and isinstance(entry["doj_fca"], dict):
                    isp = entry["doj_fca"].get("in_sample_period_2020_2024", entry["doj_fca"])
                    detector_data[name]["doj_fca"] = isp

    # 3. Add HCAI seismic data — note: HCAI is OVERLAY only, not in active DETECTORS
    # registry; populated here for the overlay report
    hcai_path = DATA / "detector_data_ca_hcai_seismic.json"
    if hcai_path.exists():
        hcai = json.loads(hcai_path.read_text())
        for raw_name, entry in hcai.get("obligors", {}).items():
            name = canonicalize(raw_name)
            if name not in detector_data:
                detector_data[name] = {}
            if "hcai_seismic" in entry:
                detector_data[name]["hcai_seismic"] = entry["hcai_seismic"]

    # 4. Add existing M&A leverage fires for the 9 CA obligors already in main data
    ma_existing_path = DATA / "ma_leverage_events.json"
    op_existing_path = DATA / "operating_metrics.json"
    if ma_existing_path.exists():
        ma_existing = json.loads(ma_existing_path.read_text())
        op_existing = json.loads(op_existing_path.read_text()) if op_existing_path.exists() else {"obligors": {}}
        for raw_name, entry in ma_existing.get("obligors", {}).items():
            name = canonicalize(raw_name)
            if name in detector_data and name not in ma_fires:
                events = entry.get("ma_events", [])
                rev = op_existing.get("obligors", {}).get(raw_name, {}).get("total_operating_revenue_usd")
                fired = False
                for e in events:
                    if e.get("leverage_impact") == "high":
                        fired = True
                        break
                    dv = e.get("deal_value_usd")
                    if dv and rev and (dv / rev) >= 0.15:
                        fired = True
                        break
                ma_fires[name] = fired

    # 5. Pull existing outcomes for the 9 CA obligors already in our data
    orig_outcomes_dir = DATA / "verified_outcomes_2023_2025" / "per_obligor"
    for f in sorted(orig_outcomes_dir.glob("*.json")):
        d = json.loads(f.read_text())
        name = canonicalize(d.get("obligor_name"))
        if name in detector_data and name not in outcomes:
            outcomes[name] = normalize_outcome(d.get("computed_outcome_class"))

    return detector_data, ma_fires, outcomes


def main():
    print("=" * 80)
    print("CA HOSPITAL MUNI — UNION EXCLUSION SCREEN")
    print("=" * 80)
    universe = load_ca_universe()
    print(f"CA universe: {len(universe)} obligors (excluded Verity defunct)")
    detector_data, ma_fires, outcomes = load_ca_detector_data()
    print(f"Detector data populated: {len(detector_data)} obligors")
    print(f"M&A fires: {sum(1 for v in ma_fires.values() if v)} of {len(ma_fires)}")
    print(f"Outcomes loaded: {len(outcomes)}")

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
            print(f"  {r['obligor']:<55} fired_by: {r['fired_by']}")

    print(f"\n=== CA EXCLUSION ALPHA ===")
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
            print(f"  *** CA EXCLUSION ALPHA: {alpha['exclusion_alpha_pp']:+.1f} pp ***")
            # Translate to TEY
            # Approximate: pp of deterioration avoidance × ~50 bps spread × ~8 dur / years
            # Use ~30 bps per pp as a rough mapping to annualized return alpha
            est_muni_alpha_bps = alpha['exclusion_alpha_pp'] * 30
            est_tey_alpha_bps = est_muni_alpha_bps * CA_TEY_MULTIPLIER
            print(f"  Approx muni alpha (annualized): {est_muni_alpha_bps:.0f} bps")
            print(f"  Approx CA top-bracket TEY alpha: {est_tey_alpha_bps:.0f} bps")

    # === HCAI overlay (Tier-3 risk flag, NOT exclusion) ===
    print(f"\n=== HCAI SEISMIC OVERLAY (Tier-3 risk flag, not exclusion) ===")
    hcai_warnings = []
    for obligor in sorted(detector_data.keys()):
        h_data = detector_data[obligor].get("hcai_seismic")
        if not h_data:
            continue
        h_result = hcai_seismic.evaluate(obligor, h_data)
        if h_result["fires"]:
            hcai_warnings.append({
                "obligor": obligor,
                "reason": h_result["reason"],
                "evidence": h_result["evidence"],
                "in_clean_basket": obligor in result["clean_basket"],
            })
    print(f"HCAI raised warnings on {len(hcai_warnings)} obligors")
    in_clean = [w for w in hcai_warnings if w["in_clean_basket"]]
    print(f"  Of those, {len(in_clean)} are in the CLEAN basket — these are names the exclusion screen didn't catch but carry long-horizon seismic risk:")
    for w in in_clean[:15]:
        print(f"    {w['obligor']:<50} ({w['reason']})")

    out_path = OUTPUTS / "ca_union_exclusion_results.json"
    out_path.write_text(json.dumps({
        "universe_result": result,
        "ca_alpha_loose": measure_exclusion_alpha(result, outcomes, threshold="loose"),
        "ca_alpha_strict": measure_exclusion_alpha(result, outcomes, threshold="strict"),
        "hcai_overlay_warnings": hcai_warnings,
    }, indent=2, default=str))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
