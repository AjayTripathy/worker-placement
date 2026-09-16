"""
Generic backtest cohort aggregator: build matrix.json + pairs.json from
scores.json files in a backtest data directory. Replicates the
per-cohort aggregator + pair_trades logic without depending on the
12 hand-written cohort aggregator scripts.

Usage:
    python3 -m verticals.public_co.backtest_aggregate \
        --cohort fintech_cohort --cutoff 2024-05-17
"""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"

SEVERITY_WEIGHTS = {
    "PASS":                  0,
    "MODERATE_UNDERDELIVERY":1,
    "SEVERE_UNDERDELIVERY":  2,
    "RED_FLAG_NEGATIVE":     3,
}

# Forward-bet emitter v2 thresholds (mirror pair_trades.py)
EMIT_MIN_COMPOSITE = 0.6
EMIT_DA_TIERS = {"HIGH", "MED", "UNKNOWN"}  # accept UNKNOWN for backtest (DA data is current)


def composite_for_scores(scores: list[dict]) -> tuple[float, dict[str, int]]:
    counts = {}
    weighted = 0.0
    n_non_unv = 0
    for sc in scores:
        sev = sc.get("severity", "?")
        counts[sev] = counts.get(sev, 0) + 1
        if sev in SEVERITY_WEIGHTS:
            weighted += SEVERITY_WEIGHTS[sev]
            n_non_unv += 1
    composite = round(weighted / n_non_unv, 2) if n_non_unv else 0.0
    return composite, counts


def load_da_tier(ticker: str) -> str:
    """Look up Discovery Advantage tier from cache (may be current-state)."""
    cache = DATA / "_discovery_advantage_cache" / f"{ticker}.json"
    if not cache.exists():
        return "UNKNOWN"
    d = json.loads(cache.read_text())
    return d.get("tier", "UNKNOWN")


def build_matrix(cohort_module: str, backtest_dir: Path) -> list[dict]:
    m = importlib.import_module(cohort_module)
    rows = []
    for member in m.COHORT:
        tk = member.ticker.upper()
        sp = backtest_dir / f"{tk}.scores.json"
        if not sp.exists():
            continue
        scores_data = json.loads(sp.read_text())
        composite, counts = composite_for_scores(scores_data.get("scores", []))
        # filing reference
        plan = json.loads((backtest_dir / f"{tk}.plan.json").read_text())
        rows.append({
            "ticker":          tk,
            "name":            member.name,
            "is_control":      "control" in (member.notes or "").lower(),
            "composite_score": composite,
            "severity_counts": counts,
            "n_claims":        len(scores_data.get("scores", [])),
            "filing":          plan.get("filing", ""),
            "discovery_advantage_tier": load_da_tier(tk),
        })
    return sorted(rows, key=lambda r: -r["composite_score"])


def emit_pairs(matrix: list[dict], theme: str) -> list[dict]:
    """Emit short/long pairs for a cohort matrix per v2 forward-bet rules."""
    if not matrix:
        return []
    # Candidate shorts: composite >= threshold AND DA tier acceptable AND not control
    shorts = [r for r in matrix
              if r["composite_score"] >= EMIT_MIN_COMPOSITE
              and r["discovery_advantage_tier"] in EMIT_DA_TIERS
              and not r["is_control"]]
    if not shorts:
        return []
    # Long candidate: explicit control > lowest-composite non-control
    controls = [r for r in matrix if r["is_control"]]
    if controls:
        long_leg = controls[0]
    else:
        non_short_tickers = {r["ticker"] for r in shorts}
        candidates = [r for r in matrix if r["ticker"] not in non_short_tickers]
        if not candidates:
            return []
        long_leg = min(candidates, key=lambda r: r["composite_score"])

    pairs = []
    for s in shorts:
        pairs.append({
            "theme":            theme,
            "short":            s["ticker"],
            "short_composite":  s["composite_score"],
            "short_counts":     s["severity_counts"],
            "short_filing":     s["filing"],
            "short_da_tier":    s["discovery_advantage_tier"],
            "long":             long_leg["ticker"],
            "long_composite":   long_leg["composite_score"],
            "long_da_tier":     long_leg["discovery_advantage_tier"],
        })
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", required=True)
    ap.add_argument("--cutoff", required=True)
    args = ap.parse_args()

    cohort_full = (
        args.cohort if args.cohort.startswith("verticals.public_co.")
        else f"verticals.public_co.{args.cohort}"
    )
    cutoff_slug = args.cutoff.replace("-", "_")
    backtest_dir = DATA / "_backtest" / cutoff_slug
    if not backtest_dir.exists():
        print(f"ERROR: {backtest_dir} not found", flush=True)
        return

    m = importlib.import_module(cohort_full)
    theme = getattr(m, "COHORT_NAME", args.cohort.replace("_cohort", "").title())

    matrix = build_matrix(cohort_full, backtest_dir)
    pairs  = emit_pairs(matrix, theme)

    (backtest_dir / f"{args.cohort}_matrix.json").write_text(json.dumps(matrix, indent=2, default=str))
    (backtest_dir / f"{args.cohort}_pairs.json").write_text(json.dumps(pairs, indent=2, default=str))

    print(f"=== {args.cohort} @ {args.cutoff} ===")
    print(f"Matrix ({len(matrix)} rows):")
    for r in matrix:
        is_ctrl = " (control)" if r["is_control"] else ""
        print(f"  {r['ticker']:>5}  composite={r['composite_score']:.2f}  "
              f"counts={r['severity_counts']}  DA={r['discovery_advantage_tier']}{is_ctrl}")
    print(f"\nPairs emitted: {len(pairs)}")
    for p in pairs:
        print(f"  SHORT {p['short']:>5} / LONG {p['long']:>5}  composite={p['short_composite']}")


if __name__ == "__main__":
    main()
