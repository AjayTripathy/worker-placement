"""IJR Phase 3d — distressed-pool inversion strategy.

Inversion of the original thesis. Instead of "buy IJR, exclude flagged
names":

  BUY the high-precision-flagged pool, then secondary-filter out the
  totally-catastrophic ones.

The flagged pool in Phase 3c had:
  - +52.87% avg return (SEVERE+ threshold, full universe, n=95)
  - 19 catastrophes (avg -50%) + 76 mean-reverters (avg +78%)
  - Alpha vs IJR: +18.4 pp BEFORE any secondary filtering

If we can identify and remove most of the 19 catastrophes while keeping
most of the 76 mean-reverters, alpha approaches the +43.5 pp ceiling.

SECONDARY FILTER CANDIDATES

  Tier A — single extreme signal:
    - runway_calculator = RED  (cash 3 mo or less)
    - mw_lifecycle = RECURRING_MW
    - going_concern_detector = EXPLICIT_GOING_CONCERN
    - lender_concession = MULTIPLE_CONCESSIONS

  Tier B — multi-signal compound:
    - 2+ high-precision signals firing at SEVERE+
    - filing_timeliness=RECURRING_AMENDMENTS + share_count_drift=SEVERE_DILUTION
    - working_capital_drift=SEVERE + runway TIGHT or SEVERE

  Tier C — sector-specific:
    - openfda_inspection_device = MULTIPLE_CLASS_I  (RED_FLAG_NEGATIVE)
    - orange_book = LOE_IMMINENT

We test each as an additional EXCLUDE filter on the flagged pool.
"""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np

from .ijr_phase3_tuning import (
    _load_all, _build_features, _stratified_split,
    SEED, TEST_FRAC, SEV_W, DATA,
)
from .ijr_phase3b_isolate import HIGH_PRECISION_SIGNALS
from .ijr_phase3c_exclusion import _build_with_value


def _flagged_pool(merged: dict, tickers: list[str], feat_names: list[str],
                  X: np.ndarray, threshold_sev: int) -> list[int]:
    """Indices of names where ANY high-precision signal fires ≥ threshold_sev."""
    wl_idx = [i for i, fn in enumerate(feat_names) if fn in HIGH_PRECISION_SIGNALS]
    sub = X[:, wl_idx]
    return [i for i, fires in enumerate((sub >= threshold_sev).any(axis=1)) if fires]


def _is_catastrophe(merged: dict, ticker: str) -> bool:
    r = merged.get(ticker, {}).get("ret_24m")
    return r is not None and r <= -0.30


def _basket_metrics(merged: dict, indices: list[int], tickers: list[str],
                    ijr_24m: float) -> dict:
    rets = []
    caps = []
    n_cat = 0
    for i in indices:
        t = tickers[i]
        d = merged.get(t, {})
        r = d.get("ret_24m")
        if r is None:
            continue
        rets.append(r)
        caps.append(d.get("value_usd") or 0)
        if _is_catastrophe(merged, t):
            n_cat += 1
    if not rets:
        return {"n": 0}
    ew = sum(rets) / len(rets)
    cap_total = sum(caps)
    cw = sum(r * c for r, c in zip(rets, caps)) / cap_total if cap_total > 0 else None
    return {
        "n":            len(rets),
        "n_catastrophes": n_cat,
        "pct_catastrophes": 100 * n_cat / len(rets),
        "ew_return":    ew,
        "cw_return":    cw,
        "alpha_ew_vs_ijr": ew - ijr_24m,
        "alpha_cw_vs_ijr": (cw - ijr_24m) if cw is not None else None,
    }


def _has_specific_signal(d: dict, m_source: str, signals: set[str]) -> bool:
    for t in d.get("tuples", []):
        if t.get("M_source") == m_source and t.get("signal") in signals:
            return True
    return False


def _count_severe_high_precision(d: dict) -> int:
    count = 0
    for t in d.get("tuples", []):
        if t.get("M_source") in HIGH_PRECISION_SIGNALS:
            sev = t.get("severity") or "PASS"
            if SEV_W.get(sev, 0) >= 2:  # SEVERE or RED
                count += 1
    return count


def _secondary_filter_exclude(merged: dict, tickers: list[str],
                                pool_indices: list[int],
                                filter_name: str) -> tuple[list[int], list[int]]:
    """Return (kept_indices, excluded_indices) after applying secondary filter.

    filter_name selects one of the predefined heuristics.
    """
    excluded = []
    kept = []
    for i in pool_indices:
        t = tickers[i]
        d = merged.get(t, {})
        exclude = False
        if filter_name == "runway_red":
            exclude = _has_specific_signal(d, "runway_calculator", {"RED"})
        elif filter_name == "runway_severe_or_red":
            exclude = _has_specific_signal(d, "runway_calculator", {"RED", "SEVERE"})
        elif filter_name == "going_concern_explicit":
            exclude = _has_specific_signal(d, "going_concern_detector",
                                            {"EXPLICIT_GOING_CONCERN",
                                             "SUBSTANTIAL_DOUBT",
                                             "GOING_CONCERN_ISSUED"})
        elif filter_name == "recurring_mw":
            exclude = _has_specific_signal(d, "mw_lifecycle",
                                            {"RECURRING_MW", "OPEN_MW"})
        elif filter_name == "multi_signal_2plus":
            exclude = _count_severe_high_precision(d) >= 2
        elif filter_name == "multi_signal_3plus":
            exclude = _count_severe_high_precision(d) >= 3
        elif filter_name == "device_multi_class_i":
            exclude = _has_specific_signal(d, "openfda_inspection_device",
                                            {"MULTIPLE_CLASS_I"})
        elif filter_name == "loe_imminent":
            exclude = _has_specific_signal(d, "orange_book_loe",
                                            {"LOE_IMMINENT"})
        elif filter_name == "any_red_flag":
            # Any signal firing RED_FLAG_NEGATIVE
            for tup in d.get("tuples", []):
                if tup.get("severity") == "RED_FLAG_NEGATIVE":
                    exclude = True; break
        elif filter_name == "filing_amendments_plus_dilution":
            ft = _has_specific_signal(d, "filing_timeliness",
                                       {"RECURRING_AMENDMENTS"})
            sd = _has_specific_signal(d, "share_count_drift",
                                       {"SEVERE_DILUTION"})
            exclude = ft and sd
        else:
            raise ValueError(f"unknown filter {filter_name}")
        if exclude:
            excluded.append(i)
        else:
            kept.append(i)
    return kept, excluded


def main():
    merged, ret_map = _load_all()
    holdings_path = DATA / "ijr_holdings_2024_06_30.json"
    merged = _build_with_value(merged, holdings_path)
    tickers, feat_names, X, y, clusters = _build_features(merged)
    train_idx, test_idx = _stratified_split(y, clusters)

    ijr_24m = json.loads((DATA / "forward_returns.json").read_text())["ijr_24m"]
    universe_ew = float(np.mean([merged[t]["ret_24m"] for t in tickers
                                  if merged[t]["ret_24m"] is not None]))
    print(f"IJR 24m: {ijr_24m:+.2%}  |  Universe-EW 24m: {universe_ew:+.2%}")
    print(f"Total universe: {len(tickers)} names with returns, "
          f"{int(y.sum())} catastrophes ({100*y.mean():.1f}%)")

    for fold_name, idx_subset in [
        ("FULL UNIVERSE (in-sample reference)", list(range(len(tickers)))),
        ("TEST FOLD only (OOS)", test_idx.tolist()),
    ]:
        # Build sub-views
        sub_tickers = [tickers[i] for i in idx_subset]
        sub_X = X[idx_subset]
        sub_merged = {t: merged[t] for t in sub_tickers}

        print("\n" + "="*80)
        print(fold_name)
        print("="*80)

        for sev_label, sev_w in [("SEVERE+", 2), ("MODERATE+", 1)]:
            print(f"\n-- Primary filter: any HIGH_PRECISION signal at {sev_label} --")
            pool = _flagged_pool(sub_merged, sub_tickers, feat_names, sub_X, sev_w)
            base = _basket_metrics(sub_merged, pool, sub_tickers, ijr_24m)
            print(f"  Distressed pool: n={base['n']} ({base['n_catastrophes']} catastrophes = "
                  f"{base.get('pct_catastrophes', 0):.1f}%)")
            print(f"    EW {_pct(base['ew_return'])} (α vs IJR {_pct(base['alpha_ew_vs_ijr'])})")
            print(f"    CW {_pct(base['cw_return'])} (α vs IJR {_pct(base['alpha_cw_vs_ijr'])})")

            # Apply each secondary filter
            filters = [
                "runway_red",
                "runway_severe_or_red",
                "going_concern_explicit",
                "any_red_flag",
                "multi_signal_2plus",
                "multi_signal_3plus",
                "filing_amendments_plus_dilution",
                "device_multi_class_i",
                "loe_imminent",
                "recurring_mw",
            ]
            print(f"\n  Secondary filters (exclude these names from the pool):")
            print(f"  {'filter':<35} {'kept':>5} {'excl':>5} "
                  f"{'kept α (EW)':>13} {'kept α (CW)':>13} "
                  f"{'excl ret':>10} {'cat saved':>10}")
            for f in filters:
                kept, excl = _secondary_filter_exclude(sub_merged, sub_tickers, pool, f)
                if not kept:
                    continue
                kept_m = _basket_metrics(sub_merged, kept, sub_tickers, ijr_24m)
                excl_m = _basket_metrics(sub_merged, excl, sub_tickers, ijr_24m) if excl else {"n": 0}
                cat_saved = excl_m.get("n_catastrophes", 0)
                excl_ret = excl_m.get("ew_return")
                excl_ret_str = _pct(excl_ret) if excl_ret is not None else "    n/a"
                print(f"  {f:<35} {kept_m['n']:>5} {excl_m['n']:>5} "
                      f"{_pct(kept_m['alpha_ew_vs_ijr']):>13} "
                      f"{_pct(kept_m['alpha_cw_vs_ijr']):>13} "
                      f"{excl_ret_str:>10} {cat_saved:>10}")


def _pct(x):
    if x is None:
        return "    n/a"
    return f"{x*100:+6.2f}%"


if __name__ == "__main__":
    main()
