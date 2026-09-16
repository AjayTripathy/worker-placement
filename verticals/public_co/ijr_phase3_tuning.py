"""IJR Phase 3 — train/test split + logistic regression tuning.

Methodology (Option A from the discussion):
  1. Build per-ticker feature matrix where each m-source contributes one
     column with the severity weight emitted (0/1/2/3) or 0 if not fired
     (UNVERIFIABLE, PASS, or module not run).
  2. Label = is_catastrophe (24m return ≤ -30%).
  3. Stratified random 60/40 train/test split, seed=42, stratified by
     the joint (cluster_bucket, is_catastrophe) to keep both folds
     representative.
  4. Fit L2-regularized logistic regression on TRAIN fold only.
  5. Report per-feature coefficients (signals ordered by weight).
  6. Apply the FROZEN model to TEST fold and report recall/precision
     vs the mean-severity baseline.

WHAT THIS CATCHES
  - Threshold-fitting and composite-aggregation overfit (the rules learn
    different weights on different folds → punished by test recall)

WHAT THIS DOES NOT CATCH
  - Signal-type cherry-picking (m-source choices are baked in regardless
    of fold)
  - Sector-bound generalization (random split keeps clusters balanced)

USAGE
  python3 -m verticals.public_co.ijr_phase3_tuning
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.metrics import precision_recall_curve, average_precision_score

HERE = Path(__file__).parent
DATA = HERE / "data" / "_ijr_manifest"
P1 = DATA / "phase1_scores.json"
P2 = DATA / "phase2_scores.json"
P25 = DATA / "phase25_scores.json"
RETURNS = DATA / "forward_returns.json"

# Map composite-recompute severity strings to numeric weights
SEV_W = {"PASS": 0, "UNVERIFIABLE": 0,
         "MODERATE_UNDERDELIVERY": 1, "SEVERE_UNDERDELIVERY": 2,
         "RED_FLAG_NEGATIVE": 3}

SEED = 42
TEST_FRAC = 0.40
CATASTROPHE_THRESHOLD = -0.30  # 24m return


def _load_all() -> tuple[dict, dict]:
    p1 = json.loads(P1.read_text())["scores"]
    p2 = json.loads(P2.read_text())["scores"]
    p25 = json.loads(P25.read_text())["scores"]
    ret = json.loads(RETURNS.read_text())["returns_24m"]

    # Merge all RFM tuples per ticker
    merged: dict[str, dict] = {}
    for t, s in p1.items():
        merged[t] = {
            "cik": s.get("cik"),
            "cluster": s.get("cluster") or "UNKNOWN",
            "tuples": list(s.get("rfm_tuples") or []),
            "ret_24m": ret.get(t),
        }
    for t, s in p2.items():
        if s.get("skipped") or t not in merged:
            continue
        merged[t]["tuples"].extend(s.get("p2_tuples") or [])
    for t, s in p25.items():
        if "error" in s or t not in merged:
            continue
        # phase25 stores the LLM signal as a single derived tuple at scoring time;
        # reconstruct one here
        sig = s.get("llm_signal")
        sev = s.get("llm_severity")
        if sig and sev:
            # Direction guess from signal text
            direction = "negative" if sev not in ("PASS", "UNVERIFIABLE") else "positive"
            merged[t]["tuples"].append({
                "M_source": f"llm_{merged[t]['cluster'].lower()}_extract",
                "severity": sev,
                "direction": direction,
                "signal": sig,
            })
    return merged, ret


def _build_features(merged: dict) -> tuple[list[str], list[str], np.ndarray, np.ndarray, list[str]]:
    """Returns (tickers, feature_names, X, y, clusters)."""
    # Collect every m-source name observed across the universe
    all_modules: set[str] = set()
    for d in merged.values():
        for t in d["tuples"]:
            ms = t.get("M_source")
            if ms:
                all_modules.add(ms)
    feature_names = sorted(all_modules)

    rows: list[dict] = []
    for ticker, d in merged.items():
        ret = d.get("ret_24m")
        if ret is None:
            continue
        feat = {fn: 0.0 for fn in feature_names}
        for t in d["tuples"]:
            ms = t.get("M_source")
            sev = t.get("severity") or "PASS"
            w = SEV_W.get(sev, 0)
            if ms and w > feat[ms]:  # keep max severity per module
                feat[ms] = w
        rows.append({
            "ticker": ticker, "cluster": d["cluster"], "ret_24m": ret,
            "is_catastrophe": int(ret <= CATASTROPHE_THRESHOLD),
            **feat,
        })

    tickers = [r["ticker"] for r in rows]
    clusters = [r["cluster"] for r in rows]
    X = np.array([[r[fn] for fn in feature_names] for r in rows], dtype=float)
    y = np.array([r["is_catastrophe"] for r in rows], dtype=int)
    return tickers, feature_names, X, y, clusters


def _stratified_split(y: np.ndarray, clusters: list[str], seed: int = SEED, test_frac: float = TEST_FRAC):
    """Stratify by joint (cluster_bucket, is_catastrophe).

    Cluster_bucket = top 10 clusters (by count) + 'OTHER'; reduces strata
    cardinality so each stratum has enough members to split.
    """
    from collections import Counter
    cluster_counts = Counter(clusters)
    top10 = set(c for c, _ in cluster_counts.most_common(10))
    bucketed = [c if c in top10 else "OTHER" for c in clusters]
    strata = [f"{b}|{lbl}" for b, lbl in zip(bucketed, y)]

    # Drop singleton strata (StratifiedShuffleSplit requires ≥2 per stratum);
    # promote them to OTHER|<label>
    from collections import Counter as _Counter
    sc = _Counter(strata)
    strata = [s if sc[s] >= 2 else f"OTHER|{s.split('|')[-1]}" for s in strata]

    sss = StratifiedShuffleSplit(n_splits=1, test_size=test_frac, random_state=seed)
    train_idx, test_idx = next(sss.split(np.zeros(len(y)), strata))
    return train_idx, test_idx


def _baseline_mean_severity(X: np.ndarray) -> np.ndarray:
    """Existing composite — mean severity weight across all observed columns."""
    # Per-row mean over only the columns that fired (treat 0 as 'didn't fire')
    # To match composite_recompute exactly, we divide by N_formal_tuples
    # which is len(columns) here.
    return X.mean(axis=1)


def _evaluate(scores: np.ndarray, y: np.ndarray, name: str) -> dict:
    """Compute precision/recall sweep + best-F1 threshold."""
    if scores.max() == scores.min():
        return {"name": name, "auc_pr": 0.0, "best_f1": 0.0}
    p, r, thresh = precision_recall_curve(y, scores)
    f1 = np.where((p + r) > 0, 2 * p * r / (p + r), 0)
    best_i = int(np.argmax(f1[:-1]))  # last point is precision/recall at -inf
    return {
        "name": name,
        "auc_pr": float(average_precision_score(y, scores)),
        "best_f1": float(f1[best_i]),
        "best_thresh": float(thresh[best_i]) if best_i < len(thresh) else None,
        "best_precision": float(p[best_i]),
        "best_recall": float(r[best_i]),
        "base_rate": float(y.mean()),
        "n_pos": int(y.sum()),
        "n_total": int(len(y)),
    }


def main():
    merged, returns = _load_all()
    tickers, feat_names, X, y, clusters = _build_features(merged)
    print(f"Loaded {len(tickers)} tickers with returns; "
          f"{int(y.sum())} catastrophes ({100*y.mean():.1f}%); "
          f"{len(feat_names)} features.\n")

    train_idx, test_idx = _stratified_split(y, clusters)
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    print(f"Train: {len(train_idx)} names ({int(y_train.sum())} catastrophes)")
    print(f"Test:  {len(test_idx)} names ({int(y_test.sum())} catastrophes)\n")

    # ── Baseline: mean-severity composite (no tuning) ─────────────
    base_test_scores = _baseline_mean_severity(X_test)
    base_metrics = _evaluate(base_test_scores, y_test, "BASELINE_MEAN_SEVERITY")
    print("=== BASELINE (no tuning) on TEST fold ===")
    _print_metrics(base_metrics)

    # ── Logistic regression tuned on TRAIN, evaluated on TEST ─────
    model = LogisticRegression(
        penalty="l2", C=1.0,            # moderate L2 regularization
        class_weight="balanced",         # account for class imbalance
        max_iter=2000,
        solver="lbfgs",
        random_state=SEED,
    )
    model.fit(X_train, y_train)
    train_scores = model.predict_proba(X_train)[:, 1]
    test_scores = model.predict_proba(X_test)[:, 1]

    train_metrics = _evaluate(train_scores, y_train, "LR_TUNED_TRAIN")
    test_metrics  = _evaluate(test_scores,  y_test,  "LR_TUNED_TEST")

    print("\n=== LOGISTIC REGRESSION on TRAIN fold (in-sample) ===")
    _print_metrics(train_metrics)
    print("\n=== LOGISTIC REGRESSION on TEST fold (HONEST out-of-sample) ===")
    _print_metrics(test_metrics)

    # ── Signal weights, ordered ───────────────────────────────────
    coefs = list(zip(feat_names, model.coef_[0]))
    coefs.sort(key=lambda x: -x[1])  # most positive (catastrophe-predictive) first
    print("\n=== SIGNAL WEIGHTS (ordered by catastrophe predictiveness) ===")
    print(f"{'rank':>4} {'m-source':<40} {'coef':>8} {'sign':>10}")
    for i, (fn, c) in enumerate(coefs, 1):
        sign = "→ catastrophe" if c > 0 else "→ survives"
        print(f"{i:>4} {fn:<40} {c:>+8.3f} {sign:>10}")

    print(f"\nIntercept: {model.intercept_[0]:+.3f}")

    # Save report
    out = DATA / "phase3_tuning_report.json"
    out.write_text(json.dumps({
        "seed": SEED,
        "test_frac": TEST_FRAC,
        "n_total": len(tickers),
        "n_catastrophes": int(y.sum()),
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
        "n_features": len(feat_names),
        "baseline_test_metrics": base_metrics,
        "lr_train_metrics": train_metrics,
        "lr_test_metrics": test_metrics,
        "signal_weights": [{"m_source": fn, "coef": c} for fn, c in coefs],
        "intercept": float(model.intercept_[0]),
    }, indent=2))
    print(f"\nSaved → {out}")


def _print_metrics(m: dict) -> None:
    print(f"  AUC-PR:        {m['auc_pr']:.3f}")
    print(f"  Best F1:       {m['best_f1']:.3f} "
          f"@ thresh={m.get('best_thresh') or 'n/a'}")
    print(f"  At best F1:    precision={m['best_precision']:.1%} recall={m['best_recall']:.1%}")
    print(f"  Base rate:     {m['base_rate']:.1%}  (n={m['n_total']}, "
          f"n_catastrophes={m['n_pos']})")


if __name__ == "__main__":
    main()
