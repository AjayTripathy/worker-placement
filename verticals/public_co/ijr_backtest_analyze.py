"""IJR Phase-1 backtest analyzer.

Joins per-ticker composite scores from phase1_scores.json to forward
returns (12m, 24m) and computes:
  - Decile tables: by distress_composite and by recovery_composite
  - Tier baskets: HIGH_CONV_LONG, HIGH_CONV_SHORT, LONG_TIER, SHORT_TIER, NEUTRAL
  - Equal-weight and cap-weight basket returns
  - Comparison to IJR benchmark

OUTPUT TABLES

  By distress decile (high distress = expected underperformance):
    decile  n   mean_dist  mean_rec   12m_avg   24m_avg   12m_vs_ijr   24m_vs_ijr

  By recovery decile (high recovery = expected outperformance):
    decile  n   mean_dist  mean_rec   12m_avg   24m_avg   12m_vs_ijr   24m_vs_ijr

  By tier:
    tier            n   12m_avg   24m_avg   12m_vs_ijr  24m_vs_ijr

  Asymmetry tests (per HANDOFF.md framework):
    Universe-equal-weight vs IJR
    Exclude-bottom-distress-decile-EW vs IJR  (the framework's core thesis)

Usage:
  python3 -m verticals.public_co.ijr_backtest_analyze
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).parent
SCORES = HERE / "data" / "_ijr_manifest" / "phase1_scores.json"
RETURNS = HERE / "data" / "_ijr_manifest" / "forward_returns.json"
HOLDINGS = HERE / "data" / "_ijr_manifest" / "ijr_holdings_2024_06_30.json"


def _load() -> tuple[dict, dict, dict]:
    scores = json.loads(SCORES.read_text())
    returns = json.loads(RETURNS.read_text())
    holdings_raw = json.loads(HOLDINGS.read_text())
    if isinstance(holdings_raw, dict) and "holdings" in holdings_raw:
        holdings_raw = holdings_raw["holdings"]
    holdings = {h["ticker"]: h for h in holdings_raw if h.get("ticker")}
    return scores, returns, holdings


def _join(scores: dict, returns: dict, holdings: dict) -> list[dict]:
    """Build per-ticker rows with composite + forward returns + market cap."""
    rows = []
    r12 = returns.get("returns_12m", {})
    r24 = returns.get("returns_24m", {})
    for ticker, s in (scores.get("scores") or {}).items():
        ret12 = r12.get(ticker)
        ret24 = r24.get(ticker)
        if ret12 is None and ret24 is None:
            continue  # no price data
        h = holdings.get(ticker, {})
        rows.append({
            "ticker":   ticker,
            "cluster":  s.get("cluster"),
            "distress": s.get("distress_composite"),
            "recovery": s.get("recovery_composite"),
            "tier":     s.get("tier"),
            "n_formal": s.get("n_formal_tuples", 0),
            "ret_12m":  ret12,
            "ret_24m":  ret24,
            "value_usd": h.get("value_usd"),
        })
    return rows


def _basket_return(
    rows: list[dict],
    return_field: str,
    weight: str = "equal",
) -> tuple[Optional[float], int, float]:
    """Compute basket return (equal or cap weight). Returns (return, n, total_weight)."""
    relevant = [r for r in rows if r.get(return_field) is not None]
    if not relevant:
        return None, 0, 0.0
    if weight == "equal":
        ret = sum(r[return_field] for r in relevant) / len(relevant)
        return ret, len(relevant), float(len(relevant))
    elif weight == "cap":
        weighted = [(r[return_field], r.get("value_usd") or 0) for r in relevant]
        total_w = sum(w for _, w in weighted)
        if total_w <= 0:
            return None, len(relevant), 0.0
        ret = sum(rr * w for rr, w in weighted) / total_w
        return ret, len(relevant), total_w
    raise ValueError(f"bad weight {weight}")


def _deciles(rows: list[dict], sort_field: str, *, reverse: bool = False) -> list[list[dict]]:
    """Sort and split into 10 deciles."""
    sorted_rows = sorted(
        [r for r in rows if r.get(sort_field) is not None],
        key=lambda r: r[sort_field],
        reverse=reverse,
    )
    n = len(sorted_rows)
    if n == 0:
        return []
    size = max(1, n // 10)
    deciles = []
    for i in range(10):
        start = i * size
        end = start + size if i < 9 else n
        deciles.append(sorted_rows[start:end])
    return deciles


def _format_pct(x: Optional[float]) -> str:
    return f"{x*100:+6.2f}%" if x is not None else "    n/a"


def print_decile_table(rows: list[dict], sort_field: str, ijr_12m: float, ijr_24m: float,
                       *, label: str, reverse: bool = False) -> None:
    deciles = _deciles(rows, sort_field, reverse=reverse)
    print(f"\n=== Decile table by {label} (sort_field={sort_field}, "
          f"{'desc' if reverse else 'asc'}) ===")
    print(f"{'dec':>3} {'n':>4} {'mean_dist':>10} {'mean_rec':>10} "
          f"{'12m_avg':>9} {'24m_avg':>9} {'12m_vs_ijr':>11} {'24m_vs_ijr':>11} "
          f"{'12m_cw':>9} {'24m_cw':>9}")
    for i, d in enumerate(deciles, 1):
        ret12_ew, n12, _ = _basket_return(d, "ret_12m", "equal")
        ret24_ew, n24, _ = _basket_return(d, "ret_24m", "equal")
        ret12_cw, _, _ = _basket_return(d, "ret_12m", "cap")
        ret24_cw, _, _ = _basket_return(d, "ret_24m", "cap")
        dist_mean = statistics.mean(r["distress"] for r in d if r.get("distress") is not None) if d else 0
        rec_mean = statistics.mean(r["recovery"] for r in d if r.get("recovery") is not None) if d else 0
        v12 = (ret12_ew - ijr_12m) if (ret12_ew is not None) else None
        v24 = (ret24_ew - ijr_24m) if (ret24_ew is not None) else None
        print(f"{i:>3} {len(d):>4} {dist_mean:>10.3f} {rec_mean:>10.3f} "
              f"{_format_pct(ret12_ew):>9} {_format_pct(ret24_ew):>9} "
              f"{_format_pct(v12):>11} {_format_pct(v24):>11} "
              f"{_format_pct(ret12_cw):>9} {_format_pct(ret24_cw):>9}")


def print_tier_table(rows: list[dict], ijr_12m: float, ijr_24m: float) -> None:
    print("\n=== By tier ===")
    print(f"{'tier':>18} {'n':>4} {'12m_avg':>9} {'24m_avg':>9} {'12m_vs_ijr':>11} {'24m_vs_ijr':>11}")
    by_tier: dict[str, list[dict]] = {}
    for r in rows:
        by_tier.setdefault(r.get("tier") or "UNTIERED", []).append(r)
    order = ["HIGH_CONV_LONG", "LONG_TIER", "NEUTRAL", "SHORT_TIER", "HIGH_CONV_SHORT", "UNSCOREABLE", "UNTIERED"]
    for tier in [t for t in order if t in by_tier] + [t for t in by_tier if t not in order]:
        d = by_tier[tier]
        ret12, n12, _ = _basket_return(d, "ret_12m", "equal")
        ret24, n24, _ = _basket_return(d, "ret_24m", "equal")
        v12 = (ret12 - ijr_12m) if ret12 is not None else None
        v24 = (ret24 - ijr_24m) if ret24 is not None else None
        print(f"{tier:>18} {len(d):>4} {_format_pct(ret12):>9} {_format_pct(ret24):>9} "
              f"{_format_pct(v12):>11} {_format_pct(v24):>11}")


def print_exclusion_test(rows: list[dict], ijr_12m: float, ijr_24m: float) -> None:
    """The honesty-alpha thesis: exclude the bottom decile by recovery score."""
    print("\n=== Exclusion test (core honesty-alpha thesis) ===")
    print("Hypothesis: dropping the highest-distress / lowest-recovery names")
    print("from the universe should net positive alpha vs IJR.\n")

    univ12 = _basket_return(rows, "ret_12m", "equal")[0]
    univ24 = _basket_return(rows, "ret_24m", "equal")[0]
    print(f"  Universe-EW:                  12m {_format_pct(univ12)} (vs IJR {_format_pct(univ12-ijr_12m)})  "
          f"24m {_format_pct(univ24)} (vs IJR {_format_pct(univ24-ijr_24m)})")

    # Exclude by distress (high distress dropped)
    dist_sorted = sorted([r for r in rows if r.get("distress") is not None], key=lambda r: r["distress"])
    for cut in (0.10, 0.20, 0.30):
        keep_n = int(len(dist_sorted) * (1 - cut))
        kept = dist_sorted[:keep_n]
        r12 = _basket_return(kept, "ret_12m", "equal")[0]
        r24 = _basket_return(kept, "ret_24m", "equal")[0]
        v12 = r12 - ijr_12m if r12 is not None else None
        v24 = r24 - ijr_24m if r24 is not None else None
        print(f"  Drop top {int(cut*100):>2}% distress (n={len(kept)}): "
              f"12m {_format_pct(r12)} (vs IJR {_format_pct(v12)})  "
              f"24m {_format_pct(r24)} (vs IJR {_format_pct(v24)})")

    # Long the HIGH_CONV_LONG basket
    hcl = [r for r in rows if r.get("tier") == "HIGH_CONV_LONG"]
    if hcl:
        r12 = _basket_return(hcl, "ret_12m", "equal")[0]
        r24 = _basket_return(hcl, "ret_24m", "equal")[0]
        v12 = r12 - ijr_12m if r12 is not None else None
        v24 = r24 - ijr_24m if r24 is not None else None
        print(f"  HIGH_CONV_LONG basket (n={len(hcl)}): "
              f"12m {_format_pct(r12)} (vs IJR {_format_pct(v12)})  "
              f"24m {_format_pct(r24)} (vs IJR {_format_pct(v24)})")


def print_cluster_breakdown(rows: list[dict], ijr_12m: float, ijr_24m: float) -> None:
    print("\n=== By cluster ===")
    print(f"{'cluster':>30} {'n':>4} {'12m_avg':>9} {'24m_avg':>9} {'12m_vs_ijr':>11} {'24m_vs_ijr':>11}")
    by_c: dict[str, list[dict]] = {}
    for r in rows:
        by_c.setdefault(r.get("cluster") or "UNKNOWN", []).append(r)
    for c in sorted(by_c, key=lambda k: -len(by_c[k])):
        d = by_c[c]
        r12 = _basket_return(d, "ret_12m", "equal")[0]
        r24 = _basket_return(d, "ret_24m", "equal")[0]
        v12 = r12 - ijr_12m if r12 is not None else None
        v24 = r24 - ijr_24m if r24 is not None else None
        print(f"{c:>30} {len(d):>4} {_format_pct(r12):>9} {_format_pct(r24):>9} "
              f"{_format_pct(v12):>11} {_format_pct(v24):>11}")


def main():
    global SCORES
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", default=str(SCORES))
    args = ap.parse_args()

    SCORES = Path(args.scores)
    scores, returns, holdings = _load()
    rows = _join(scores, returns, holdings)

    ijr_12m = returns.get("ijr_12m", 0.0)
    ijr_24m = returns.get("ijr_24m", 0.0)

    n_scored = len(scores.get("scores") or {})
    n_with_returns = len(rows)
    print(f"Scored: {n_scored} | With forward returns: {n_with_returns}")
    print(f"IJR benchmark: 12m {_format_pct(ijr_12m)} | 24m {_format_pct(ijr_24m)}")

    print_tier_table(rows, ijr_12m, ijr_24m)
    print_decile_table(rows, "distress", ijr_12m, ijr_24m,
                       label="distress (asc = least distressed)")
    print_decile_table(rows, "recovery", ijr_12m, ijr_24m,
                       label="recovery (desc = highest recovery first)", reverse=True)
    print_exclusion_test(rows, ijr_12m, ijr_24m)
    print_cluster_breakdown(rows, ijr_12m, ijr_24m)


if __name__ == "__main__":
    main()
