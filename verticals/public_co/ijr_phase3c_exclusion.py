"""IJR Phase 3c — exclusion alpha vs IJR using high-precision signals only.

The strategy: buy the IJR universe equal-weight, except drop any name
where ANY high-precision signal fires at the configured threshold.
Compare basket return to (a) IJR cap-weighted benchmark, (b)
universe-EW (no exclusion).

Three runs:
  1. Theory-driven whitelist on FULL universe (in-sample, all 548 names)
  2. Same whitelist on TEST fold only (220 names, out-of-sample)
  3. LR-trained-positive-coef gating: derive whitelist from train-fold
     LR coefficients, apply to test fold (rigorous OOS)

REPORTING

For each run:
  - n_flagged / n_kept
  - excluded basket: avg return + n_catastrophes captured
  - kept basket: avg return EW + cap-weighted
  - alpha vs IJR + alpha vs universe-EW

Severity threshold sweep: fires at MODERATE+ and SEVERE+.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression

from .ijr_phase3_tuning import (
    _load_all, _build_features, _stratified_split,
    SEED, TEST_FRAC, SEV_W, DATA,
)
from .ijr_phase3b_isolate import HIGH_PRECISION_SIGNALS


def _build_with_value(merged: dict, holdings_path: Path) -> dict:
    """Add value_usd from holdings file to the merged dict."""
    h_raw = json.loads(holdings_path.read_text())
    if isinstance(h_raw, dict) and "holdings" in h_raw:
        h_raw = h_raw["holdings"]
    val = {h["ticker"]: h.get("value_usd") for h in h_raw if h.get("ticker")}
    for t, d in merged.items():
        d["value_usd"] = val.get(t)
    return merged


def _exclusion_alpha(
    merged: dict,
    feat_names: list[str],
    X: np.ndarray,
    y: np.ndarray,
    tickers: list[str],
    whitelist: set[str],
    threshold_sev_weight: int,
    ijr_24m: float,
) -> dict:
    """Compute exclusion-strategy returns vs IJR.

    threshold_sev_weight: 1 = MODERATE+, 2 = SEVERE+, 3 = RED only
    """
    wl_idx = [i for i, fn in enumerate(feat_names) if fn in whitelist]
    if not wl_idx:
        return {"error": "no whitelist columns present"}
    sub = X[:, wl_idx]
    flagged = (sub >= threshold_sev_weight).any(axis=1)

    flagged_tickers = [tickers[i] for i, f in enumerate(flagged) if f]
    kept_tickers = [tickers[i] for i, f in enumerate(flagged) if not f]

    # Returns
    flag_rets = []
    kept_rets = []
    kept_caps = []
    flag_caps = []
    flag_catastrophes = 0
    kept_catastrophes = 0
    for i, t in enumerate(tickers):
        d = merged.get(t, {})
        r = d.get("ret_24m")
        if r is None:
            continue
        cap = d.get("value_usd") or 0
        is_cat = y[i] == 1
        if flagged[i]:
            flag_rets.append(r)
            flag_caps.append(cap)
            if is_cat:
                flag_catastrophes += 1
        else:
            kept_rets.append(r)
            kept_caps.append(cap)
            if is_cat:
                kept_catastrophes += 1

    def _ew(rets):
        return sum(rets) / len(rets) if rets else None

    def _cw(rets, caps):
        total = sum(caps)
        return sum(r * c for r, c in zip(rets, caps)) / total if total > 0 else None

    n_total = sum(1 for i, t in enumerate(tickers)
                  if merged.get(t, {}).get("ret_24m") is not None)
    universe_ew = (sum(flag_rets) + sum(kept_rets)) / n_total if n_total else None

    return {
        "threshold_sev_weight":  threshold_sev_weight,
        "n_total_with_returns":  n_total,
        "n_flagged":             len(flag_rets),
        "n_kept":                len(kept_rets),
        "n_catastrophes_total":  int(y.sum()),
        "n_catastrophes_flagged": flag_catastrophes,
        "n_catastrophes_kept":   kept_catastrophes,
        "flagged_basket_ew":     _ew(flag_rets),
        "kept_basket_ew":        _ew(kept_rets),
        "kept_basket_cw":        _cw(kept_rets, kept_caps),
        "universe_ew":           universe_ew,
        "alpha_kept_ew_vs_ijr":  (_ew(kept_rets) - ijr_24m) if _ew(kept_rets) is not None else None,
        "alpha_kept_cw_vs_ijr":  (_cw(kept_rets, kept_caps) - ijr_24m) if _cw(kept_rets, kept_caps) is not None else None,
        "alpha_kept_vs_universe_ew": (_ew(kept_rets) - universe_ew) if (_ew(kept_rets) is not None and universe_ew is not None) else None,
        "flagged_tickers_sample": flagged_tickers[:20],
    }


def main():
    merged, ret_map = _load_all()
    # Reload holdings to get value_usd
    holdings_path = DATA / "ijr_holdings_2024_06_30.json"
    merged = _build_with_value(merged, holdings_path)

    tickers, feat_names, X, y, clusters = _build_features(merged)
    train_idx, test_idx = _stratified_split(y, clusters)
    test_tickers = [tickers[i] for i in test_idx]
    train_tickers = [tickers[i] for i in train_idx]

    ijr_24m = json.loads((DATA / "forward_returns.json").read_text())["ijr_24m"]
    print(f"IJR benchmark 24m: {ijr_24m:+.2%}")
    print(f"Universe: {len(tickers)} names with returns, "
          f"{int(y.sum())} catastrophes ({100*y.mean():.1f}%)\n")

    # ─── RUN 1: Theory-driven whitelist on FULL universe ───
    print("=" * 80)
    print("RUN 1 — Theory-driven whitelist on FULL universe (in-sample reference)")
    print("=" * 80)
    for sev in (1, 2):
        thresh_name = "MODERATE+" if sev == 1 else "SEVERE+"
        r = _exclusion_alpha(merged, feat_names, X, y, tickers,
                              HIGH_PRECISION_SIGNALS, sev, ijr_24m)
        _print_run(r, thresh_name, ijr_24m)

    # ─── RUN 2: Same whitelist on TEST fold only ───
    print("\n" + "=" * 80)
    print("RUN 2 — Theory-driven whitelist on TEST fold only (220 names, OOS)")
    print("=" * 80)
    X_test = X[test_idx]
    y_test = y[test_idx]
    for sev in (1, 2):
        thresh_name = "MODERATE+" if sev == 1 else "SEVERE+"
        r = _exclusion_alpha(merged, feat_names, X_test, y_test, test_tickers,
                              HIGH_PRECISION_SIGNALS, sev, ijr_24m)
        _print_run(r, thresh_name, ijr_24m)

    # ─── RUN 3: Train-fold-learned coefficients applied to test fold ───
    print("\n" + "=" * 80)
    print("RUN 3 — Train-fold-learned positive-coef gating, applied to TEST fold")
    print("=" * 80)
    X_train = X[train_idx]
    y_train = y[train_idx]
    model = LogisticRegression(penalty="l2", C=1.0,
                                class_weight="balanced", max_iter=2000,
                                solver="lbfgs", random_state=SEED)
    model.fit(X_train, y_train)
    train_coefs = list(zip(feat_names, model.coef_[0]))
    train_positive_wl = {fn for fn, c in train_coefs if c > 0.1}
    print(f"Train-fold whitelist (coef > 0.1): {sorted(train_positive_wl)}\n")
    for sev in (1, 2):
        thresh_name = "MODERATE+" if sev == 1 else "SEVERE+"
        r = _exclusion_alpha(merged, feat_names, X_test, y_test, test_tickers,
                              train_positive_wl, sev, ijr_24m)
        _print_run(r, thresh_name, ijr_24m)


def _print_run(r: dict, thresh_name: str, ijr_24m: float) -> None:
    if "error" in r:
        print(f"  {thresh_name}: {r['error']}")
        return
    print(f"\n  -- fires at {thresh_name} --")
    print(f"  Flagged (excluded):   n={r['n_flagged']:>3}, "
          f"caught {r['n_catastrophes_flagged']:>2}/{r['n_catastrophes_total']} catastrophes, "
          f"avg return {_pct(r['flagged_basket_ew'])}")
    print(f"  Kept (held):          n={r['n_kept']:>3}, "
          f"missed {r['n_catastrophes_kept']:>2} catastrophes")
    print(f"  Kept basket EW:       {_pct(r['kept_basket_ew'])}")
    print(f"  Kept basket cap-wt:   {_pct(r['kept_basket_cw'])}")
    print(f"  Universe EW:          {_pct(r['universe_ew'])}")
    print(f"  IJR benchmark:        {_pct(ijr_24m)}")
    print(f"  Alpha (kept EW vs IJR): {_pct(r['alpha_kept_ew_vs_ijr'])}")
    print(f"  Alpha (kept CW vs IJR): {_pct(r['alpha_kept_cw_vs_ijr'])}")
    print(f"  Alpha (kept EW vs univ EW): {_pct(r['alpha_kept_vs_universe_ew'])}")
    if r['n_flagged'] and r['n_flagged'] <= 20:
        print(f"  Flagged tickers: {', '.join(r['flagged_tickers_sample'])}")


def _pct(x):
    if x is None:
        return "    n/a"
    return f"{x*100:+6.2f}%"


if __name__ == "__main__":
    main()
