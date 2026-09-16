"""Blind OOS backtest analyzer — 2016-12-31 → 2019-12-31 window.

Uses 33-obligor universe identified blindly to 2024-2025 outcomes.
Tests whether the in-sample signal generalizes to:
  - a different macro regime (pre-COVID normal cycle)
  - a different obligor universe (genuinely blind selection)

This is the dispositive test for overfit.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from core.firewall import confusion_matrix

HERE = Path(__file__).parent
OOS_DIR = HERE / "data" / "blind_oos_2017_2019" / "per_obligor"
COVENANT_FILE = HERE / "data" / "covenant_terms.json"
OUT_JSON = HERE / "outputs" / "blind_oos_results.json"


def normalize_outcome(outcome_class: str) -> str:
    """Map agent-introduced outcome variants to the canonical set."""
    if outcome_class is None:
        return None
    mapping = {
        "ACQUIRED_UPGRADE": "AFFIRM_POSITIVE_OUTLOOK",  # bondholders absorbed into stronger parent
        "ACQUIRED": "AFFIRM_STABLE",                     # neutral acquisition
        "ACQUIRED_DISTRESSED": "MULTI_DOWNGRADE",        # standalone was failing; rescue prevented default
        "DOWNGRADE_TO_NON_IG": "MULTI_DOWNGRADE",        # fallen angel
        "OUTLOOK_NEGATIVE": "AFFIRM_NEGATIVE_OUTLOOK",
        "AFFIRM_NEGATIVE": "AFFIRM_NEGATIVE_OUTLOOK",
        "TERMINATED_BY_MERGER": "AFFIRM_STABLE",         # at window end, no clear deterioration
        "MERGER_PENDING": "AFFIRM_STABLE",
    }
    return mapping.get(outcome_class, outcome_class)


def classify_deterioration(outcome_class: str, threshold: str = "loose") -> bool | None:
    outcome = normalize_outcome(outcome_class)
    if outcome in (None, "UNVERIFIABLE"):
        return None
    deteriorated_strict = {"DOWNGRADE", "MULTI_DOWNGRADE", "DEFAULT"}
    deteriorated_loose = deteriorated_strict | {"AFFIRM_NEGATIVE_OUTLOOK"}
    if threshold == "strict":
        return outcome in deteriorated_strict
    return outcome in deteriorated_loose


def compute_tripwire_fires(metrics: dict, covenants: dict) -> bool | None:
    if not metrics or not covenants:
        return None
    fired = False
    can_eval = False

    days_cash = metrics.get("days_cash_on_hand")
    dc_cov = covenants.get("days_cash_on_hand_minimum") or {}
    dc_min = dc_cov.get("value") if isinstance(dc_cov, dict) else None
    if days_cash is not None and dc_min:
        can_eval = True
        if (days_cash - dc_min) / dc_min * 100 < 5:
            fired = True

    rev = metrics.get("total_operating_revenue_usd")
    margin = metrics.get("operating_margin_pct")
    inv = metrics.get("investment_income_usd") or 0
    debt_svc = metrics.get("annual_debt_service_usd_estimated")
    dscr_cov = covenants.get("debt_service_coverage_minimum") or {}
    dscr_min = dscr_cov.get("value") if isinstance(dscr_cov, dict) else None
    if rev and margin is not None and debt_svc and dscr_min:
        can_eval = True
        noi_all = rev * margin / 100 + inv
        dscr = noi_all / debt_svc
        if (dscr - dscr_min) / dscr_min * 100 < 5:
            fired = True

    return fired if can_eval else None


def compute_ma_red_fires(ma_events: list, revenue: float) -> bool:
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


def find_covenant(name: str, covenants_data: dict) -> dict:
    """If obligor isn't in our covenant data, fall back to industry-typical defaults."""
    if name in covenants_data:
        return covenants_data[name]
    # Fallback: industry-typical covenants for hospital muni
    return {
        "days_cash_on_hand_minimum": {"value": 65, "confidence": "INDUSTRY_DEFAULT"},
        "debt_service_coverage_minimum": {"value": 1.10, "confidence": "INDUSTRY_DEFAULT"},
    }


def compute_confusion(per_obligor: list, signal_key: str, threshold: str) -> dict:
    cm = confusion_matrix(
        (r[signal_key], r["deteriorated_" + threshold]) for r in per_obligor
    )
    return {
        "threshold": threshold,
        "n_evaluable": cm["n_evaluable"], "n_unknown": cm["n_unknown"],
        "confusion": cm["confusion"],
        "base_rate_of_deterioration": cm["base_rate"],
        "precision": cm["precision"], "recall": cm["recall"],
        "f1": cm["f1"],
        "accuracy": cm["accuracy"], "baseline_majority_accuracy": cm["baseline_majority_accuracy"],
        "lift_over_baseline_acc": cm["lift_over_baseline_acc"],
    }


def main():
    covenants_data = json.loads(COVENANT_FILE.read_text())["obligors"]
    records = [json.loads(f.read_text()) for f in sorted(OOS_DIR.glob("*.json"))]
    print(f"Blind OOS records loaded: {len(records)}")

    outcomes_raw = Counter(r.get("computed_outcome_class") for r in records)
    outcomes_norm = Counter(normalize_outcome(r.get("computed_outcome_class")) for r in records)
    print("\n=== RAW outcome distribution ===")
    for cls, n in outcomes_raw.most_common(): print(f"  {cls}: {n}")
    print("\n=== NORMALIZED outcome distribution ===")
    for cls, n in outcomes_norm.most_common(): print(f"  {cls}: {n}")

    per_obligor = []
    for r in records:
        name = r.get("obligor_name", "?")
        metrics = r.get("operating_metrics_fy2016") or {}
        ma_events = r.get("ma_events_2017_2018") or []
        outcome = r.get("computed_outcome_class")
        rev = metrics.get("total_operating_revenue_usd")
        covs = find_covenant(name, covenants_data)

        tw = compute_tripwire_fires(metrics, covs)
        ma = compute_ma_red_fires(ma_events, rev)
        combined = (tw or ma) if (tw is not None or ma) else None

        per_obligor.append({
            "obligor": name,
            "outcome_class": outcome,
            "outcome_normalized": normalize_outcome(outcome),
            "deteriorated_loose": classify_deterioration(outcome, "loose"),
            "deteriorated_strict": classify_deterioration(outcome, "strict"),
            "tripwire_fires": tw, "ma_fires": ma, "combined_fires": combined,
        })

    signals = [("tripwire_fires", "Covenant tripwire"),
               ("ma_fires", "M&A leverage RED"),
               ("combined_fires", "Combined")]
    print(f"\n=== BLIND OOS CONFUSION MATRICES ===")
    all_results = {}
    for key, label in signals:
        all_results[key] = {}
        print(f"\n{label}:")
        for thresh in ("loose", "strict"):
            cm = compute_confusion(per_obligor, key, thresh)
            all_results[key][thresh] = cm
            c = cm["confusion"]
            print(f"  {thresh.upper()}: TP={c['TP']} FP={c['FP']} TN={c['TN']} FN={c['FN']} unknown={cm['n_unknown']}")
            print(f"     P={cm['precision']*100:.0f}% R={cm['recall']*100:.0f}% "
                  f"Acc={cm['accuracy']*100:.0f}% Base={cm['baseline_majority_accuracy']*100:.0f}% "
                  f"Lift={cm['lift_over_baseline_acc']*100:+.0f}pp")

    # 3-way comparison
    print(f"\n=== IN-SAMPLE vs SAME-UNIV OOS vs BLIND OOS (LOOSE) ===")
    is_n = {"tripwire_fires": (71, 63, 11, 40),
            "ma_fires": (83, 45, 5, 28),
            "combined_fires": (71, 75, 18, 49)}
    oos_n = {"tripwire_fires": (50, 92, 0, 35),
             "ma_fires": (43, 20, -3, 39),
             "combined_fires": (46, 92, -6, 35)}
    print(f"{'Signal':<20}{'In-sample 22-25':<30}{'OOS 20-22 (same univ)':<35}{'BLIND 17-19 (new univ)':<35}")
    print("-" * 120)
    for key, label in signals:
        b = all_results[key]["loose"]
        is_p, is_r, is_l, is_nn = is_n[key]
        oos_p, oos_r, oos_l, oos_nn = oos_n[key]
        bs = (f"P={b['precision']*100:.0f}% R={b['recall']*100:.0f}% "
              f"L={b['lift_over_baseline_acc']*100:+.0f}pp n={b['n_evaluable']}")
        iss = f"P={is_p}% R={is_r}% L={is_l:+}pp n={is_nn}"
        oss = f"P={oos_p}% R={oos_r}% L={oos_l:+}pp n={oos_nn}"
        print(f"{label:<20}{iss:<30}{oss:<35}{bs:<35}")

    OUT_JSON.parent.mkdir(exist_ok=True)
    OUT_JSON.write_text(json.dumps({
        "blind_oos_window": {"start": "2016-12-31", "end": "2019-12-31"},
        "n_records": len(records),
        "outcome_distribution_raw": dict(outcomes_raw),
        "outcome_distribution_normalized": dict(outcomes_norm),
        "per_obligor": per_obligor,
        "results": all_results,
    }, indent=2, default=str))
    print(f"\nSaved: {OUT_JSON}")


if __name__ == "__main__":
    main()
