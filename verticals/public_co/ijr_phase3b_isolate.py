"""IJR Phase 3b — isolate high-precision signals, re-test on held-out fold.

The Phase 3 logistic regression showed:
  - Composite mean-severity has near-zero catastrophe discrimination
  - A handful of signals had positive train-fold coefficients
  - Several signals (working_capital_drift, share_count_drift) had
    NEGATIVE coefficients — they anti-predict catastrophes in this regime

This Phase 3b builds a theory-driven "high-precision" detector:
  HIGH_PRECISION_SIGNALS = signals that, when they fire, are designed
  to identify a specific catastrophe mechanism (FDA recall, patent
  LOE, etc.), not generic "company looks stressed."

Two detector variants tested on the SAME train/test split:

  ANY-FIRE: flag a name if ANY high-precision signal fires ≥ MODERATE
            (severity weight ≥ 1). Binary decision.

  MAX-SEV:  score a name by the MAX severity among high-precision
            signals. Threshold-sweep for precision/recall.

Both are compared to:
  - Baseline (mean-severity composite, all 23 features)
  - LR-tuned from Phase 3
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
from sklearn.metrics import precision_recall_curve, average_precision_score

from .ijr_phase3_tuning import (
    _load_all, _build_features, _stratified_split, _evaluate,
    _baseline_mean_severity, SEED, TEST_FRAC, SEV_W, DATA,
)

# Theory-driven whitelist: signals designed to fire on specific catastrophe
# mechanisms, not generic "company is messy". Each is included because its
# trigger condition is mechanism-specific (FDA recall event, patent LOE,
# explicit going concern language, etc.).
HIGH_PRECISION_SIGNALS = {
    # FDA + drug-specific
    "openfda_inspection_device",
    "openfda_inspection_drug",
    "openfda_inspection_food",
    "openfda_inspection_supp",
    "orange_book_loe",
    # SEC narrative / regulator-flagged
    "going_concern_detector",
    "mw_lifecycle",
    "lender_concession",
    "auditor_change_tracker",
    "filing_timeliness",
    # Runway / dilution thresholds (these target specific failure modes)
    "runway_calculator",
    # SaaS-specific
    "rpo_drift",
    # LLM-extracted cluster-specific
    "llm_real_estate_extract",
    "llm_communications_extract",
    "llm_tech_software_services_extract",
    "llm_business_services_extract",
    "llm_healthcare_pharma_extract",
}

# Explicitly EXCLUDED from high-precision whitelist:
#  - working_capital_drift  (LR coef = -0.20; correlates with deep value)
#  - share_count_drift      (LR coef = -0.26; same)
#  - insider_buy_timing     (mostly returns UNVERIFIABLE; weak signal)
#  - osha_establishments    (occupational safety; weak catastrophe link)
#  - epa_emissions          (long-tail liability; rarely fires SEVERE)
#  - nhtsa_manufacturer     (registry-presence; not catastrophe signal)


def _high_precision_score(X: np.ndarray, feat_names: list[str],
                          method: str = "max") -> np.ndarray:
    """Compute per-row score using only HIGH_PRECISION_SIGNALS columns.

    method='max'    → max severity weight among whitelist (graded)
    method='count'  → count of whitelist signals firing ≥ MODERATE (graded)
    method='any'    → 1 if any whitelist signal fires ≥ MODERATE, else 0
    """
    wl_idx = [i for i, fn in enumerate(feat_names) if fn in HIGH_PRECISION_SIGNALS]
    if not wl_idx:
        return np.zeros(X.shape[0])
    sub = X[:, wl_idx]
    if method == "max":
        return sub.max(axis=1)
    if method == "count":
        return (sub >= 1).sum(axis=1).astype(float)
    if method == "any":
        return (sub >= 1).any(axis=1).astype(float)
    raise ValueError(method)


def _confusion_at_threshold(scores: np.ndarray, y: np.ndarray,
                             threshold: float) -> dict:
    flagged = scores >= threshold
    tp = int(((flagged) & (y == 1)).sum())
    fp = int(((flagged) & (y == 0)).sum())
    fn = int(((~flagged) & (y == 1)).sum())
    tn = int(((~flagged) & (y == 0)).sum())
    n_flagged = int(flagged.sum())
    precision = tp / n_flagged if n_flagged else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return {
        "threshold": threshold,
        "n_flagged": n_flagged,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0,
    }


def main():
    merged, ret_map = _load_all()
    tickers, feat_names, X, y, clusters = _build_features(merged)
    train_idx, test_idx = _stratified_split(y, clusters)
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    print(f"Total: {len(tickers)}, catastrophes: {int(y.sum())} ({100*y.mean():.1f}%)")
    print(f"Train: {len(train_idx)} ({int(y_train.sum())} catastrophes)")
    print(f"Test:  {len(test_idx)} ({int(y_test.sum())} catastrophes)\n")

    # Show which whitelist columns exist
    wl_present = [fn for fn in feat_names if fn in HIGH_PRECISION_SIGNALS]
    wl_missing = HIGH_PRECISION_SIGNALS - set(feat_names)
    print(f"High-precision whitelist columns present: {len(wl_present)}")
    for fn in wl_present:
        n_fires_train = int((X_train[:, feat_names.index(fn)] >= 1).sum())
        n_fires_test = int((X_test[:, feat_names.index(fn)] >= 1).sum())
        print(f"  {fn:<40}  train_fires={n_fires_train:>3}  test_fires={n_fires_test:>3}")
    if wl_missing:
        print(f"\nWhitelist signals not observed in dataset: {sorted(wl_missing)}")
    print()

    # ─── Test-fold evaluation: 3 detector variants ───
    print("=== TEST-FOLD COMPARISON ===\n")

    # 1. Baseline (mean severity, ALL features) — same as Phase 3 baseline
    base_scores = _baseline_mean_severity(X_test)
    print("BASELINE — mean severity over ALL 23 features:")
    _print_sweep(base_scores, y_test)

    # 2. High-precision MAX-SEVERITY
    hp_max_test = _high_precision_score(X_test, feat_names, method="max")
    print("\nHIGH-PRECISION MAX — max severity over whitelist only:")
    _print_sweep(hp_max_test, y_test)

    # 3. High-precision COUNT — number of whitelist signals firing
    hp_count_test = _high_precision_score(X_test, feat_names, method="count")
    print("\nHIGH-PRECISION COUNT — # of whitelist signals firing:")
    _print_sweep(hp_count_test, y_test)

    # 4. High-precision ANY-FIRE — binary
    hp_any_test = _high_precision_score(X_test, feat_names, method="any")
    print("\nHIGH-PRECISION ANY-FIRE — any whitelist signal fires (binary):")
    conf = _confusion_at_threshold(hp_any_test, y_test, threshold=0.5)
    print(f"  n_flagged={conf['n_flagged']:>3}  TP={conf['tp']:>3}  FP={conf['fp']:>3}  "
          f"FN={conf['fn']:>3}")
    print(f"  precision={conf['precision']:.1%}  recall={conf['recall']:.1%}  "
          f"F1={conf['f1']:.3f}")

    # 5. Train-fold "best whitelist threshold" applied to test (no peeking)
    # Pick threshold maximizing F1 on TRAIN, then apply to TEST.
    hp_max_train = _high_precision_score(X_train, feat_names, method="max")
    p_tr, r_tr, t_tr = precision_recall_curve(y_train, hp_max_train)
    # Threshold the operating point
    f1_tr = np.where((p_tr + r_tr) > 0, 2 * p_tr * r_tr / (p_tr + r_tr), 0)
    best_i = int(np.argmax(f1_tr[:-1]))
    best_thresh = float(t_tr[best_i]) if best_i < len(t_tr) else 0
    train_f1 = float(f1_tr[best_i])
    train_recall = float(r_tr[best_i])
    train_precision = float(p_tr[best_i])
    print(f"\n=== Train-fold optimal threshold = {best_thresh:.2f} "
          f"(train F1={train_f1:.3f}, P={train_precision:.1%}, R={train_recall:.1%}) ===")
    test_at_train_thresh = _confusion_at_threshold(hp_max_test, y_test, best_thresh)
    print(f"Applied to TEST fold (frozen threshold, no peeking):")
    print(f"  n_flagged={test_at_train_thresh['n_flagged']:>3}  "
          f"TP={test_at_train_thresh['tp']:>3}  FP={test_at_train_thresh['fp']:>3}  "
          f"FN={test_at_train_thresh['fn']:>3}")
    print(f"  precision={test_at_train_thresh['precision']:.1%}  "
          f"recall={test_at_train_thresh['recall']:.1%}  "
          f"F1={test_at_train_thresh['f1']:.3f}")

    # ─── Train-fold-derived NEGATIVE-EXCLUSION test ───
    # Use the whole composite but EXCLUDE the two anti-predictive features
    # learned from train. Tests: does removing bad signals help?
    exclude = {"working_capital_drift", "share_count_drift"}
    keep_idx = [i for i, fn in enumerate(feat_names) if fn not in exclude]
    excl_score = X_test[:, keep_idx].mean(axis=1)
    print("\n=== ALL-FEATURES MINUS anti-predictive (WC, share dilution) ===")
    _print_sweep(excl_score, y_test)

    # Save
    out = DATA / "phase3b_isolation_report.json"
    out.write_text(json.dumps({
        "high_precision_whitelist": sorted(HIGH_PRECISION_SIGNALS),
        "whitelist_present_in_data": sorted(wl_present),
        "test_fold_metrics": {
            "baseline_mean_severity": _summary_metrics(base_scores, y_test),
            "high_precision_max":     _summary_metrics(hp_max_test, y_test),
            "high_precision_count":   _summary_metrics(hp_count_test, y_test),
            "high_precision_any":     _confusion_at_threshold(hp_any_test, y_test, 0.5),
            "exclude_anti_predictive": _summary_metrics(excl_score, y_test),
        },
        "train_threshold_applied_to_test": test_at_train_thresh,
    }, indent=2))
    print(f"\nSaved → {out}")


def _summary_metrics(scores: np.ndarray, y: np.ndarray) -> dict:
    if scores.max() == scores.min():
        return {"auc_pr": 0.0, "best_f1": 0.0, "_note": "constant scores"}
    p, r, thresh = precision_recall_curve(y, scores)
    f1 = np.where((p + r) > 0, 2 * p * r / (p + r), 0)
    best_i = int(np.argmax(f1[:-1]))
    return {
        "auc_pr":          float(average_precision_score(y, scores)),
        "best_f1":         float(f1[best_i]),
        "best_thresh":     float(thresh[best_i]) if best_i < len(thresh) else None,
        "best_precision":  float(p[best_i]),
        "best_recall":     float(r[best_i]),
    }


def _print_sweep(scores: np.ndarray, y: np.ndarray) -> None:
    m = _summary_metrics(scores, y)
    print(f"  AUC-PR: {m.get('auc_pr', 0):.3f}  Best F1: {m.get('best_f1', 0):.3f}  "
          f"@P={m.get('best_precision', 0):.1%}, R={m.get('best_recall', 0):.1%}")


if __name__ == "__main__":
    main()
