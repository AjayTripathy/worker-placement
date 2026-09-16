"""Tier 3 — exclusion-basket returns, survivorship-honest + placebo-controlled.

The framework's claimed value is EXCLUSION (don't buy the liars). So the test is:
buy every 2024-25 IPO at first-day close, hold to 2026-05-29; does excluding the
flagged names beat the all-in basket — and beat a RANDOM exclusion of the same
size (placebo)?

Survivorship honesty: delisted/deregistered names with no yfinance price are
assigned -1.0 (total loss), NOT dropped. Names with no ticker / no price and no
delisting evidence are excluded and counted separately.

Caveat (audit): the alpha leg is the part the small-cap backtest already
falsified (+57pp in-sample -> -8.6pp walk-forward). RIPO is a loose reference
only — it holds large IPOs, this cohort is micro-caps.

Run: python3 verticals/buyside_dd/data/_ipo_backtest_2024_2025/tier3_basket.py
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

HERE = Path(__file__).parent
OUT = HERE / "tier3_results.json"
_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from core.control_suite import basket_stats  # noqa: E402

OFFSHORE = {"E9", "D8", "D0"}
ASIA = {"F4", "K3", "U0", "F5", "N8"}
SEED = 20260529
N_TRIALS = 10_000
END = "2026-05-29"


def build_rows():
    feats = {f["cik"]: f for f in json.loads((HERE / "features.json").read_text())["features"]}
    outs = json.loads((HERE / "outcomes.json").read_text())["labels"]
    rows, excluded_nodata = [], 0
    for o in outs:
        f = feats.get(o["cik"], {})
        r = o.get("r_current")
        if r is None:
            if o.get("delisted_no_price"):
                r = -1.0  # adverse delist/dereg, no price -> total loss
            else:
                # merger/take-private cash-out (no buyout px) or genuinely no data
                excluded_nodata += 1
                continue
        rows.append({
            "cik": o["cik"], "ticker": o.get("ticker"), "name": o.get("company_name"),
            "r": r,
            "foreign_issuer": int(bool(f.get("foreign_private_issuer"))),
            "offshore": int(f.get("incorp_code") in OFFSHORE),
            "asia": int(f.get("biz_country_code") in ASIA),
        })
        rows[-1]["archetype"] = rows[-1]["offshore"] + rows[-1]["asia"] + rows[-1]["foreign_issuer"]
    return rows, excluded_nodata


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def placebo_exclusion(rows, n_excluded, seed=SEED, n_trials=N_TRIALS):
    """Distribution of retained-basket mean when n_excluded names are dropped at RANDOM."""
    import random
    rets = [x["r"] for x in rows]
    total, N = sum(rets), len(rets)
    rng = random.Random(seed)
    keep = N - n_excluded
    means = []
    for _ in range(n_trials):
        dropped = rng.sample(rets, n_excluded)
        means.append((total - sum(dropped)) / keep)
    means.sort()
    return means


def pct_rank(sorted_vals, x):
    import bisect
    return bisect.bisect_left(sorted_vals, x) / len(sorted_vals)


def ripo_reference():
    try:
        import yfinance as yf
        h = yf.Ticker("IPO").history(start="2024-01-12", end=END, auto_adjust=True)["Close"].dropna()
        return round(float(h.iloc[-1]) / float(h.iloc[0]) - 1, 4) if len(h) else None
    except Exception:
        return None


def main():
    rows, excl = build_rows()
    N = len(rows)
    all_rets = [r["r"] for r in rows]

    strategies = {
        "buy_all": rows,
        "exclude_foreign_issuer": [r for r in rows if not r["foreign_issuer"]],
        "exclude_archetype_ge2": [r for r in rows if r["archetype"] < 2],
        "exclude_archetype_ge1": [r for r in rows if r["archetype"] < 1],
    }
    table = {}
    for name, kept in strategies.items():
        rets = [r["r"] for r in kept]
        n_excl = N - len(kept)
        entry = {
            "n_held": len(kept), "n_excluded": n_excl,
            "mean_return": round(mean(rets), 4) if rets else None,
            "median_return": round(sorted(rets)[len(rets)//2], 4) if rets else None,
            "pct_positive": round(sum(1 for x in rets if x > 0) / len(rets), 3) if rets else None,
        }
        if 0 < n_excl < N:
            dist = placebo_exclusion(rows, n_excl)
            actual = mean(rets)
            entry["placebo"] = {
                "actual_retained_mean": round(actual, 4),
                "random_exclusion_mean_p50": round(dist[len(dist)//2], 4),
                "percentile_vs_random": round(pct_rank(dist, actual), 4),
                "uplift_vs_buy_all_pp": round((actual - mean(all_rets)) * 100, 1),
            }
        table[name] = entry

    results = {
        "n_in_basket": N,
        "n_excluded_nodata": excl,
        "delisted_assigned_total_loss": sum(1 for r in rows if r["r"] == -1.0),
        "buy_all_mean": round(mean(all_rets), 4),
        "ripo_reference_return": ripo_reference(),
        "strategies": table,
        "note": "Equal-weight, entry=first-day close, hold to 2026-05-29. Placebo = "
                "10k random exclusions of equal size. Exclusion 'alpha' here is a "
                "1-bit screen (don't buy foreign micro-cap IPOs), not framework alpha.",
    }
    OUT.write_text(json.dumps(results, indent=2))

    print(f"N in basket={N} (delisted total-loss={results['delisted_assigned_total_loss']}, "
          f"excluded no-data={excl})")
    print(f"RIPO reference (large-IPO ETF): {results['ripo_reference_return']}")
    print(f"\n{'strategy':<26}{'n_held':<8}{'mean':<10}{'median':<10}{'%pos':<7}{'vs_all_pp':<10}{'pctile_vs_random'}")
    for name, e in table.items():
        pb = e.get("placebo", {})
        print(f"{name:<26}{e['n_held']:<8}{e['mean_return']:<10}{e['median_return']:<10}"
              f"{e['pct_positive']:<7}{pb.get('uplift_vs_buy_all_pp','-'):<10}{pb.get('percentile_vs_random','-')}")
    print(f"\nWrote {OUT.name}")


if __name__ == "__main__":
    main()
