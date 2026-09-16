"""Classification accuracy backtest.

Tests each muni-credit signal against the verified rating outcomes:
  1. 4-axis composite STRONG_SELL → predicts deterioration
  2. Covenant tripwire TRIPWIRED → predicts covenant pressure / distress
  3. R/f/M honesty SUSPECT → predicts framing-driven deterioration

For each signal:
  - True positive: signal fires AND outcome deteriorates
  - False positive: signal fires AND outcome stable/improves
  - True negative: signal doesn't fire AND outcome stable/improves
  - False negative: signal doesn't fire AND outcome deteriorates

Two threshold definitions for "deterioration":
  STRICT: only DOWNGRADE, MULTI_DOWNGRADE, DEFAULT count
  LOOSE: also count AFFIRM_NEGATIVE_OUTLOOK

For each (signal × threshold), reports:
  - Confusion matrix
  - Precision = TP / (TP + FP)
  - Recall = TP / (TP + FN)
  - F1
  - Accuracy vs base rate (what would "always predict majority class" achieve?)
"""
from __future__ import annotations

import json
import glob
from pathlib import Path
from collections import Counter

HERE = Path(__file__).parent
OUTCOMES_DIR = HERE / "data" / "verified_outcomes_2023_2025" / "per_obligor"


def load_verified_outcomes() -> dict:
    """Load all per-obligor verified outcomes.

    Returns dict keyed by every known name AND alias, mapping to the same
    outcome record. This way callers can look up by any reasonable name variant.
    """
    outcomes = {}
    for f in sorted(OUTCOMES_DIR.glob("*.json")):
        d = json.loads(f.read_text())
        name = d.get("obligor_name")
        if not name:
            continue
        record = {
            "outcome_class": d.get("computed_outcome_class"),
            "rationale": d.get("outcome_class_rationale"),
            "aliases": d.get("obligor_aliases", []),
            "canonical_name": name,
            "file": f.name,
        }
        # Index by canonical name
        outcomes[name] = record
        # Index by name with state stripped: "Mount Sinai Health System (NY)" → "Mount Sinai Health System"
        import re as _re
        bare = _re.sub(r"\s*\([^)]+\)\s*", "", name).strip()
        if bare and bare not in outcomes:
            outcomes[bare] = record
        # Index by aliases too
        for alias in d.get("obligor_aliases", []) or []:
            if alias and alias not in outcomes:
                outcomes[alias] = record
    return outcomes


def classify_deterioration(outcome_class: str, threshold: str = "loose") -> bool:
    """Map outcome class to binary deterioration flag.

    STRICT: only formal downgrades and defaults
    LOOSE: also include outlook-negative revisions
    """
    if outcome_class is None:
        return None  # unknown
    deteriorated_strict = {"DOWNGRADE", "MULTI_DOWNGRADE", "DEFAULT"}
    deteriorated_loose = deteriorated_strict | {"AFFIRM_NEGATIVE_OUTLOOK"}
    if threshold == "strict":
        return outcome_class in deteriorated_strict
    return outcome_class in deteriorated_loose


def compute_confusion(signal_fires: dict, outcomes: dict, threshold: str = "loose") -> dict:
    """Compute confusion matrix for one signal.

    signal_fires: dict {obligor_name → bool} (does signal fire on this obligor?)
    outcomes: dict from load_verified_outcomes
    """
    tp = fp = tn = fn = unknown = 0
    per_obligor = []
    for obligor, fires in signal_fires.items():
        if obligor not in outcomes:
            unknown += 1
            per_obligor.append({"obligor": obligor, "signal": fires, "outcome": "?", "cell": "unknown"})
            continue
        outcome = outcomes[obligor]["outcome_class"]
        if outcome == "UNVERIFIABLE" or outcome is None:
            unknown += 1
            per_obligor.append({"obligor": obligor, "signal": fires, "outcome": outcome, "cell": "unknown"})
            continue
        deteriorated = classify_deterioration(outcome, threshold)
        if fires and deteriorated:
            tp += 1; cell = "TP"
        elif fires and not deteriorated:
            fp += 1; cell = "FP"
        elif not fires and deteriorated:
            fn += 1; cell = "FN"
        else:
            tn += 1; cell = "TN"
        per_obligor.append({"obligor": obligor, "signal": fires, "outcome": outcome, "cell": cell})

    n_evaluable = tp + fp + tn + fn
    n_positive_outcome = tp + fn
    base_rate = n_positive_outcome / max(1, n_evaluable)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = (2 * precision * recall) / max(1e-9, precision + recall)
    accuracy = (tp + tn) / max(1, n_evaluable)
    # Always-predict-majority baseline accuracy
    baseline_majority_accuracy = max(base_rate, 1 - base_rate)
    return {
        "threshold": threshold,
        "n_evaluable": n_evaluable,
        "n_unknown": unknown,
        "confusion": {"TP": tp, "FP": fp, "TN": tn, "FN": fn},
        "base_rate_of_deterioration": base_rate,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
        "baseline_majority_accuracy": baseline_majority_accuracy,
        "lift_over_baseline_acc": accuracy - baseline_majority_accuracy,
        "per_obligor": per_obligor,
    }


def load_composite_signals() -> dict:
    """Load composite-score STRONG_SELL signals from the prior backtest output.

    Reads outputs/forward_backtest_results.json (the 65-system run).
    Returns dict {obligor_name → does composite STRONG_SELL fire (≤ -2.0 notches)}.
    """
    f = HERE / "outputs" / "forward_backtest_results.json"
    if not f.exists():
        return {}
    d = json.loads(f.read_text())
    results = d if isinstance(d, list) else d.get("results", [])
    signals = {}
    for r in results:
        obligor = r.get("system") or r.get("obligor")
        if not obligor:
            continue
        notches = r.get("divergence_notches")
        if notches is None:
            notches = r.get("delta_notches") or r.get("notches")
        if notches is None:
            continue
        # STRONG_SELL fires when notches ≤ -2.0 (model says BBB but explicit is AA, etc.)
        signals[obligor] = notches <= -2.0
    return signals


def load_tripwire_signals() -> dict:
    """Load covenant tripwire signals. Returns dict {obligor → does TRIPWIRED fire}."""
    signals = {}
    for fn in ["covenant_tripwire_results.json", "covenant_tripwire_bbb_results.json"]:
        f = HERE / "outputs" / fn
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        for r in d.get("results", []):
            obligor = r["obligor"]
            tier = r.get("worst_tier", "NO_DATA")
            # Fires on TRIPWIRED or RED (technical default or extreme covenant pressure)
            signals[obligor] = tier in ("TRIPWIRED", "RED")
    return signals


def load_honesty_signals() -> dict:
    """Load honesty screen signals. Returns dict {obligor → does SUSPECT fire}."""
    f = HERE / "outputs" / "honesty_screen_results.json"
    if not f.exists():
        return {}
    d = json.loads(f.read_text())
    signals = {}
    slug_to_obligor = {
        "ascension": "Ascension Health",
        "upmc": "UPMC",
        "trinity_health": "Trinity Health",
        "cleveland_clinic": "Cleveland Clinic",
        "commonspirit": "CommonSpirit Health",
        "tower_health": "Tower Health",
        "mount_sinai": "Mount Sinai Health System",
        "allegheny_health": "Allegheny Health Network",
        "rwjbarnabas": "RWJBarnabas Health",
        "nyu_langone": "NYU Langone Health",
        "mass_general_brigham": "Mass General Brigham",
        "mgb": "Mass General Brigham",
        "atrium_health": "Atrium Health",
        "advocate_health": "Atrium Health",
        "providence": "Providence St Joseph",
        "geisinger": "Geisinger Health System",
        "iu_health": "Indiana University Health",
        "henry_ford": "Henry Ford Health System",
        "christianacare": "ChristianaCare",
        "yale_new_haven": "Yale New Haven Health",
        "kaiser": "Kaiser Foundation",
        "bjc": "BJC HealthCare",
        "banner_health": "Banner Health",
        "duke_health": "Duke University Health",
        "stanford_health": "Stanford Health Care",
        "mayo_clinic": "Mayo Clinic",
        "cedars_sinai": "Cedars-Sinai",
        "nyp": "NewYork-Presbyterian",
        "northwell": "Northwell Health",
        "johns_hopkins": "Johns Hopkins Health System",
        "memorial_sloan_kettering": "Memorial Sloan Kettering",
        "msk": "Memorial Sloan Kettering",
        "adventhealth": "AdventHealth",
        "memorial_hermann": "Memorial Hermann",
        "houston_methodist": "Houston Methodist",
        "texas_childrens": "Texas Children's Hospital",
        "chop": "Childrens Hospital Philadelphia",
        "uchealth": "UCHealth",  # CO
        "wellstar": "Wellstar Health System",
        "sutter": "Sutter Health",
        "ssm_health": "SSM Health",
        "bon_secours": "Bon Secours Mercy Health",
        "intermountain_test": "Intermountain Healthcare",
        "corewell": "Spectrum Health (Corewell)",
        "ohiohealth": "OhioHealth",
        "inova": "Inova Health System",
        "childrens_atlanta": "Children's Healthcare of Atlanta",
        "unc_health_test": "UNC Health Care",
        "multicare": "MultiCare Health System",
        "hackensack_meridian": "Hackensack Meridian Health",
        "carilion": "Carilion Clinic",
        "norton_healthcare": "Norton Healthcare",
        "baptist_health_florida": "Baptist Health South Florida",
        "lifespan": "Lifespan",
        "lehigh_valley": "Lehigh Valley Health Network",
        "penn_medicine": "Penn Medicine",
        "boston_childrens": "Children's Hospital Boston",
        "bilh": "Beth Israel Lahey Health",
        "chla": "Children's Hospital Los Angeles",
        "centura": "Centura Health (now CommonSpirit)",
        "allina": "Allina Health",
        "avera": "Avera Health",
        "sanford": "Sanford Health",
        "adventist_health": "Adventist Health (Roseville)",
        "loma_linda": "Loma Linda University Medical Center",
    }
    for slug, r in d.items():
        obligor = slug_to_obligor.get(slug, slug)
        score = r.get("aggregate_honesty_score", 100)
        # Fires on SUSPECT (aggregate < 50 AND 2+ red flags)
        signals[obligor] = "SUSPECT" in r.get("tier", "")
    return signals


def main():
    outcomes = load_verified_outcomes()
    print(f"Verified outcomes loaded: {len(outcomes)}")

    # Outcome class distribution
    outcome_classes = Counter(o["outcome_class"] for o in outcomes.values())
    print("\n=== Outcome class distribution ===")
    for cls, n in outcome_classes.most_common():
        print(f"  {cls}: {n}")

    tripwire = load_tripwire_signals()
    signals = {
        "composite_STRONG_SELL": load_composite_signals(),
        "covenant_tripwire": tripwire,
        "rfm_honesty_SUSPECT": load_honesty_signals(),
    }
    # Add M&A leverage signals if available
    try:
        from ma_leverage_detector import load_ma_red_signals, load_combined_signals
        ma_signals = load_ma_red_signals()
        if ma_signals:
            signals["ma_leverage_RED"] = ma_signals
            signals["tripwire_OR_ma_leverage"] = load_combined_signals(tripwire)
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"(M&A signal load skipped: {e})")

    all_results = {}
    for sig_name, sig_dict in signals.items():
        print(f"\n=== {sig_name} (n={len(sig_dict)} obligors evaluable) ===")
        all_results[sig_name] = {}
        for threshold in ("loose", "strict"):
            result = compute_confusion(sig_dict, outcomes, threshold=threshold)
            all_results[sig_name][threshold] = result
            cm = result["confusion"]
            print(f"  {threshold.upper():<6}: TP={cm['TP']} FP={cm['FP']} TN={cm['TN']} FN={cm['FN']} "
                  f"(unknown {result['n_unknown']})")
            print(f"     Precision: {result['precision']*100:.0f}% | Recall: {result['recall']*100:.0f}% "
                  f"| F1: {result['f1']*100:.0f} | Accuracy: {result['accuracy']*100:.0f}% "
                  f"(baseline {result['baseline_majority_accuracy']*100:.0f}%, "
                  f"lift {result['lift_over_baseline_acc']*100:+.0f} pp)")
            print(f"     Base rate of deterioration: {result['base_rate_of_deterioration']*100:.0f}%")

    out_path = HERE / "outputs" / "classification_accuracy_results.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(all_results, indent=2, default=str))
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
