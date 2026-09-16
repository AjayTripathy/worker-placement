"""Out-of-sample backtest analyzer — Dec 2020 → Dec 2022 window.

Self-contained: doesn't depend on the path-coupled in-sample engines.
For each OOS obligor:
  1. Load FY2020 operating metrics + 2021-2022 M&A events + outcome from per_obligor/*_oos.json
  2. Apply same covenant tripwire logic as in-sample (using covenant_terms.json — MTIs don't change)
  3. Apply same M&A leverage detector
  4. Compute combined signal
  5. Compare to OOS outcome
  6. Produce confusion matrices side-by-side with in-sample
"""
from __future__ import annotations

import json
import glob
from pathlib import Path
from datetime import datetime
from collections import Counter

HERE = Path(__file__).parent
OOS_DIR = HERE / "data" / "oos_2020_2022" / "per_obligor"
COVENANT_FILE = HERE / "data" / "covenant_terms.json"
OUT_JSON = HERE / "outputs" / "oos_results.json"


def classify_deterioration(outcome_class: str, threshold: str = "loose") -> bool | None:
    if outcome_class in (None, "UNVERIFIABLE"):
        return None
    deteriorated_strict = {"DOWNGRADE", "MULTI_DOWNGRADE", "DEFAULT"}
    deteriorated_loose = deteriorated_strict | {"AFFIRM_NEGATIVE_OUTLOOK"}
    if threshold == "strict":
        return outcome_class in deteriorated_strict
    return outcome_class in deteriorated_loose


def compute_tripwire_fires(metrics: dict | None, covenants: dict | None) -> bool | None:
    """Returns True if TRIPWIRED or RED tier; None if can't evaluate."""
    if not metrics or not covenants:
        return None
    fired = False
    can_evaluate = False

    # Days cash check
    days_cash = metrics.get("days_cash_on_hand")
    dc_cov = covenants.get("days_cash_on_hand_minimum") or {}
    dc_min = dc_cov.get("value") if isinstance(dc_cov, dict) else None
    if days_cash is not None and dc_min:
        can_evaluate = True
        headroom_pct = (days_cash - dc_min) / dc_min * 100
        if headroom_pct < 5:  # TRIPWIRED (< 0%) or RED (0-5%)
            fired = True

    # DSCR (all-income) check
    rev = metrics.get("total_operating_revenue_usd")
    margin = metrics.get("operating_margin_pct")
    inv = metrics.get("investment_income_usd") or 0
    debt_svc = metrics.get("annual_debt_service_usd_estimated")
    dscr_cov = covenants.get("debt_service_coverage_minimum") or {}
    dscr_min = dscr_cov.get("value") if isinstance(dscr_cov, dict) else None
    if rev and margin is not None and debt_svc and dscr_min:
        can_evaluate = True
        noi_all = rev * margin / 100 + inv
        dscr = noi_all / debt_svc
        headroom_pct = (dscr - dscr_min) / dscr_min * 100
        if headroom_pct < 5:
            fired = True

    return fired if can_evaluate else None


def compute_ma_red_fires(ma_events: list[dict] | None, revenue: float | None) -> bool:
    """Returns True if any M&A event is high-leverage."""
    if not ma_events:
        return False
    for e in ma_events:
        dv = e.get("deal_value_usd")
        impact = e.get("leverage_impact")
        if impact == "high":
            return True
        if dv and revenue and (dv / revenue) >= 0.15:
            return True
    return False


def load_oos_records() -> list[dict]:
    records = []
    for f in sorted(OOS_DIR.glob("*_oos.json")):
        d = json.loads(f.read_text())
        records.append(d)
    return records


def find_covenant_for_obligor(name: str, aliases: list[str], covenants_data: dict) -> dict | None:
    """Match obligor name (or alias) to covenant_terms entry."""
    candidates = [name] + (aliases or [])
    for cand in candidates:
        if cand in covenants_data:
            return covenants_data[cand]
        # Strip "(STATE)" suffix and try
        import re as _re
        bare = _re.sub(r"\s*\([^)]+\)\s*", "", cand).strip()
        if bare in covenants_data:
            return covenants_data[bare]
    return None


def compute_confusion(per_obligor: list[dict], signal_key: str, threshold: str = "loose") -> dict:
    tp = fp = tn = fn = unknown = 0
    for r in per_obligor:
        fires = r[signal_key]
        deteriorated = r["deteriorated_" + threshold]
        if fires is None or deteriorated is None:
            unknown += 1
            continue
        if fires and deteriorated:
            tp += 1
        elif fires:
            fp += 1
        elif deteriorated:
            fn += 1
        else:
            tn += 1
    n_eval = tp + fp + tn + fn
    base_rate = (tp + fn) / max(1, n_eval)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-9, precision + recall)
    accuracy = (tp + tn) / max(1, n_eval)
    baseline = max(base_rate, 1 - base_rate)
    return {
        "threshold": threshold,
        "n_evaluable": n_eval, "n_unknown": unknown,
        "confusion": {"TP": tp, "FP": fp, "TN": tn, "FN": fn},
        "base_rate_of_deterioration": base_rate,
        "precision": precision, "recall": recall, "f1": f1,
        "accuracy": accuracy, "baseline_majority_accuracy": baseline,
        "lift_over_baseline_acc": accuracy - baseline,
    }


def main():
    covenants_data = json.loads(COVENANT_FILE.read_text())["obligors"]
    records = load_oos_records()
    print(f"OOS records loaded: {len(records)}")

    # Outcome distribution
    outcomes = Counter(r.get("computed_outcome_class") for r in records)
    print("\n=== OOS outcome distribution (2020-12-31 → 2022-12-31) ===")
    for cls, n in outcomes.most_common():
        print(f"  {cls}: {n}")

    # Build per-obligor signal table
    per_obligor = []
    for r in records:
        name = r.get("obligor_name", "?")
        aliases = r.get("aliases") or r.get("obligor_aliases") or []
        metrics = r.get("operating_metrics_fy2020") or {}
        ma_events = r.get("ma_events_2021_2022") or []
        outcome = r.get("computed_outcome_class")
        rev = metrics.get("total_operating_revenue_usd")
        covs = find_covenant_for_obligor(name, aliases, covenants_data)

        tw_fires = compute_tripwire_fires(metrics, covs)
        ma_fires = compute_ma_red_fires(ma_events, rev)
        combined = (tw_fires or ma_fires) if (tw_fires is not None or ma_fires) else None

        per_obligor.append({
            "obligor": name,
            "outcome_class": outcome,
            "deteriorated_loose": classify_deterioration(outcome, "loose"),
            "deteriorated_strict": classify_deterioration(outcome, "strict"),
            "tripwire_fires": tw_fires,
            "ma_fires": ma_fires,
            "combined_fires": combined,
            "had_covenants": covs is not None,
            "had_metrics": bool(metrics.get("days_cash_on_hand") or metrics.get("total_operating_revenue_usd")),
        })

    # Confusion matrices for 3 signals × 2 thresholds
    signals = [("tripwire_fires", "Covenant tripwire"),
               ("ma_fires", "M&A leverage RED"),
               ("combined_fires", "Combined tripwire OR M&A")]
    print(f"\n=== OOS CONFUSION MATRICES ===")

    all_results = {}
    for key, label in signals:
        all_results[key] = {}
        print(f"\n{label}:")
        for thresh in ("loose", "strict"):
            cm = compute_confusion(per_obligor, key, thresh)
            all_results[key][thresh] = cm
            conf = cm["confusion"]
            print(f"  {thresh.upper()}: TP={conf['TP']} FP={conf['FP']} TN={conf['TN']} FN={conf['FN']} "
                  f"(unknown {cm['n_unknown']})")
            print(f"     Precision={cm['precision']*100:.0f}% Recall={cm['recall']*100:.0f}% "
                  f"F1={cm['f1']*100:.0f} Accuracy={cm['accuracy']*100:.0f}% "
                  f"Baseline={cm['baseline_majority_accuracy']*100:.0f}% "
                  f"Lift={cm['lift_over_baseline_acc']*100:+.0f}pp")

    # In-sample comparison
    print(f"\n=== IN-SAMPLE vs OUT-OF-SAMPLE COMPARISON (LOOSE threshold) ===")
    in_sample = {
        "tripwire_fires": {"precision": 71, "recall": 63, "lift": 11, "n": 40},
        "ma_fires": {"precision": 83, "recall": 45, "lift": 5, "n": 28},
        "combined_fires": {"precision": 71, "recall": 75, "lift": 18, "n": 49},
    }
    print(f"{'Signal':<25} {'In-sample':<35} {'Out-of-sample':<35} {'Lift Δ':<8}")
    print("-" * 110)
    for key, label in signals:
        is_p = in_sample[key]
        oos_p = all_results[key]["loose"]
        is_str = f"P={is_p['precision']}% R={is_p['recall']}% L={is_p['lift']:+}pp n={is_p['n']}"
        oos_str = (f"P={oos_p['precision']*100:.0f}% R={oos_p['recall']*100:.0f}% "
                   f"L={oos_p['lift_over_baseline_acc']*100:+.0f}pp n={oos_p['n_evaluable']}")
        delta = (oos_p['lift_over_baseline_acc'] * 100) - is_p['lift']
        print(f"{label:<25} {is_str:<35} {oos_str:<35} {delta:+.0f} pp")

    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps({
        "oos_window": {"start": "2020-12-31", "end": "2022-12-31"},
        "n_records": len(records),
        "outcome_distribution": dict(outcomes),
        "per_obligor": per_obligor,
        "results": all_results,
        "in_sample_comparison": in_sample,
    }, indent=2, default=str))
    print(f"\nSaved: {OUT_JSON}")


if __name__ == "__main__":
    main()
