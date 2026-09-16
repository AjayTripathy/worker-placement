"""TIER-1 CONTROL VALIDATION — Step 0: reproduce the +38.5pp headline.

Claim under test (memory: project_smallcap_honesty_strategy):
  N=64 scored, LOOSE_LONG basket (n=13) mean +64.6%, "+38.5pp gross vs IJR".

This script recomputes everything from the raw artifacts:
  - scores/pilot_*.json  (R/f/M tuples, agent-scored)
  - _unblinded/combined_test_set.json (forward returns 2025-05-15 -> 2026-05-15)
using the same deterministic composite as synthesize.py.

Writes: data/_backtest/tier1_controls/step0_reproduction.json
READ-ONLY on all existing files.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

HERE = Path(__file__).parent
SURV = HERE / "data" / "_backtest" / "survivorship_2025_05"
OUT = HERE / "data" / "_backtest" / "tier1_controls"
OUT.mkdir(exist_ok=True)

SEV_W = {
    "PASS": 0,
    "UNVERIFIABLE": 0,
    "MODERATE_UNDERDELIVERY": 1,
    "SEVERE_UNDERDELIVERY": 2,
    "RED_FLAG_NEGATIVE": 3,
}

# Benchmark candidates for the same window (2025-05-15 -> 2026-05-15):
IJR_TIER2_SCRIPT = 134.94 / 105.256 - 1        # +28.21% — hardcoded in boring_middle synthesize.py
IJR_IMPLIED_BY_CLAIM = 0.646 - 0.385           # +26.1% — what the +38.5pp claim implies


def tier(c: float) -> str:
    if c <= 0.20:
        return "STRICT_LONG"
    if c <= 0.30:
        return "LOOSE_LONG"
    if c < 0.50:
        return "NEUTRAL"
    return "SHORT"


def load_rows():
    test_set = {r["ticker"]: r for r in json.loads((SURV / "_unblinded" / "combined_test_set.json").read_text())}
    rows, unscoreable = [], []
    for f in sorted((SURV / "scores").glob("pilot_*.json")):
        d = json.loads(f.read_text())
        tk = d.get("ticker") or f.stem.replace("pilot_", "")
        tuples = d.get("rfm_tuples") or []
        ts = test_set.get(tk, {})
        fwd = ts.get("forward_return")
        if not tuples:
            unscoreable.append({"ticker": tk, "forward_return": fwd})
            continue
        counts = {k: 0 for k in SEV_W}
        for t in tuples:
            s = t.get("severity")
            if s in counts:
                counts[s] += 1
        comp = sum(SEV_W[k] * v for k, v in counts.items()) / len(tuples)
        rows.append({
            "ticker": tk, "group": ts.get("group"),
            "composite": comp, "tier": tier(comp),
            "n_tuples": len(tuples), "forward_return": fwd,
            "tuples": tuples,
        })
    return rows, unscoreable, test_set


def mean_ret(rows):
    v = [r["forward_return"] for r in rows if r["forward_return"] is not None]
    return (statistics.mean(v), len(v)) if v else (None, 0)


def main():
    rows, unscoreable, test_set = load_rows()
    universe_all = [r for r in test_set.values() if r.get("forward_return") is not None]

    baskets = {}
    for name, pred in [
        ("STRICT_LONG", lambda r: r["tier"] == "STRICT_LONG"),
        ("LOOSE_LONG_incl_strict", lambda r: r["tier"] in ("STRICT_LONG", "LOOSE_LONG")),
        ("NEUTRAL", lambda r: r["tier"] == "NEUTRAL"),
        ("SHORT", lambda r: r["tier"] == "SHORT"),
        ("NOT_SHORT_exclusion", lambda r: r["tier"] != "SHORT"),
    ]:
        sub = [r for r in rows if pred(r)]
        m, n = mean_ret(sub)
        baskets[name] = {"n": n, "mean": m, "tickers": sorted(r["ticker"] for r in sub)}

    scored_mean, n_scored = mean_ret(rows)
    univ_mean = statistics.mean(r["forward_return"] for r in universe_all)

    cats = [r for r in rows if r["forward_return"] <= -0.40]
    cats_flagged = [r for r in cats if r["tier"] == "SHORT"]

    ll = baskets["LOOSE_LONG_incl_strict"]["mean"]
    ns = baskets["NOT_SHORT_exclusion"]["mean"]

    out = {
        "n_pilot_files": len(rows) + len(unscoreable),
        "n_scored": n_scored,
        "unscoreable": unscoreable,
        "universe_66_mean": univ_mean,
        "scored_64_mean": scored_mean,
        "baskets": baskets,
        "catastrophes": {"n": len(cats), "flagged_short": len(cats_flagged),
                         "recall": len(cats_flagged) / len(cats) if cats else None,
                         "missed": [r["ticker"] for r in cats if r["tier"] != "SHORT"]},
        "benchmarks": {
            "ijr_tier2_script_28_2pct": IJR_TIER2_SCRIPT,
            "ijr_implied_by_38_5pp_claim": IJR_IMPLIED_BY_CLAIM,
        },
        "headline_reconstruction": {
            "loose_long_mean": ll,
            "alpha_vs_universe66": ll - univ_mean,
            "alpha_vs_ijr_28_2": ll - IJR_TIER2_SCRIPT,
            "alpha_vs_ijr_26_1": ll - IJR_IMPLIED_BY_CLAIM,
            "exclusion_notshort_mean": ns,
            "exclusion_alpha_vs_universe66": ns - univ_mean,
            "exclusion_alpha_vs_ijr_28_2": ns - IJR_TIER2_SCRIPT,
        },
    }

    (OUT / "step0_reproduction.json").write_text(json.dumps(
        {k: v for k, v in out.items() if k != "rows"}, indent=2, default=str))

    print(f"pilots: {out['n_pilot_files']}  scored: {n_scored}  unscoreable: {[u['ticker'] for u in unscoreable]}")
    print(f"universe-66 mean: {univ_mean*100:+.1f}%   scored-64 mean: {scored_mean*100:+.1f}%")
    for k, b in baskets.items():
        print(f"  {k:24} n={b['n']:3}  mean={b['mean']*100:+7.1f}%")
    print(f"catastrophe recall: {len(cats_flagged)}/{len(cats)}  missed: {out['catastrophes']['missed']}")
    print()
    print(f"LOOSE_LONG mean          = {ll*100:+.1f}%  (claim: +64.6%)")
    print(f"alpha vs universe-66     = {(ll-univ_mean)*100:+.1f} pp  (claim: +57.6)")
    print(f"alpha vs IJR +28.2%      = {(ll-IJR_TIER2_SCRIPT)*100:+.1f} pp")
    print(f"alpha vs IJR +26.1%      = {(ll-IJR_IMPLIED_BY_CLAIM)*100:+.1f} pp  (claim: +38.5)")
    print(f"NOT-SHORT exclusion mean = {ns*100:+.1f}%  -> alpha vs IJR +28.2% = {(ns-IJR_TIER2_SCRIPT)*100:+.1f} pp")


if __name__ == "__main__":
    main()
