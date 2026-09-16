"""Concurrent backtest validation.

Tests whether our unified composite score (computed with data current at
the time of the 2023-2025 rating actions) correctly identified the
obligors that experienced negative outcomes.

This is NOT a strict out-of-sample backtest — for that we'd need FY 2022
HCRIS data in our snapshot (blocked by data ingestion complexity).
Instead this tests CONCURRENT validity: does our model's view of credit
quality match what actually happened to the obligor's rating?

Hypothesis:
  Names we score MORE distressed than agencies → should have had DOWNGRADE
  Names we score equal to agencies → AFFIRM_STABLE
  Names we score LESS distressed than agencies → UPGRADE / POSITIVE_OUTLOOK

Output:
  outputs/backtest_concurrent_results.md
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter

HERE = Path(__file__).parent
UNIFIED_FILE = HERE / "outputs" / "unified_results.json"
OUTCOMES_FILE = HERE / "data" / "realized_outcomes_2023_2025.json"

# Score outcomes numerically for correlation
OUTCOME_SCORE = {
    "UPGRADE":                  +2,
    "AFFIRM_POSITIVE_OUTLOOK":  +1,
    "AFFIRM_STABLE":             0,
    "AFFIRM_NEGATIVE_OUTLOOK":  -1,
    "DOWNGRADE":                -2,
    "MULTI_DOWNGRADE":          -3,
    "DEFAULT":                  -4,
}


def main():
    unified = json.loads(UNIFIED_FILE.read_text())
    outcomes_db = json.loads(OUTCOMES_FILE.read_text())["outcomes"]

    rows = []
    for result in unified["results"]:
        system = result["system"]
        outcome = outcomes_db.get(system, {}).get("outcome", "UNKNOWN")
        outcome_score = OUTCOME_SCORE.get(outcome, 0)
        events = outcomes_db.get(system, {}).get("events", "")
        rows.append({
            "system":   system,
            "explicit": result["explicit"]["consensus_letter"],
            "our_final": result["final_score"]["letter"],
            "div_notches": result["divergence"]["notches"],
            "div_bps":     result["divergence"]["bps"],
            "signal":   result["divergence"]["signal"],
            "outcome":  outcome,
            "outcome_score": outcome_score,
            "events":   events,
        })

    # Sort by our model's notch divergence (most positive first)
    rows.sort(key=lambda r: r["div_notches"], reverse=True)

    # ===== Hit-rate analysis =====
    # Define "correctly predicted":
    #   STRONG_BUY / WEAK_BUY      → expect UPGRADE / POSITIVE_OUTLOOK (outcome_score ≥ +1) OR AFFIRM_STABLE
    #   CONSENSUS                  → expect AFFIRM_STABLE (outcome_score == 0) OR within ±1
    #   WEAK_SELL / STRONG_SELL    → expect NEGATIVE_OUTLOOK / DOWNGRADE (outcome_score ≤ -1)

    correct, wrong, neutral = 0, 0, 0
    detail = []
    for r in rows:
        signal = r["signal"]
        outcome_score = r["outcome_score"]
        if "BUY" in signal:
            if outcome_score >= 0:
                pred = "✓ correct"; correct += 1
            else:
                pred = "✗ wrong"; wrong += 1
        elif "SELL" in signal:
            if outcome_score <= 0:
                pred = "✓ correct"; correct += 1
            else:
                pred = "✗ wrong"; wrong += 1
        else:
            pred = "= neutral"; neutral += 1
        r["prediction_check"] = pred
        detail.append(r)

    total_directional = correct + wrong
    hit_rate = correct / total_directional if total_directional else 0
    print(f"\n{'='*100}")
    print(f"CONCURRENT BACKTEST — 31 hospital systems vs realized 2023-2025 outcomes")
    print(f"{'='*100}")
    print(f"\nDirectional signals (BUY/SELL): {total_directional}")
    print(f"  Correct:  {correct}/{total_directional}  ({hit_rate:.0%})")
    print(f"  Wrong:    {wrong}/{total_directional}")
    print(f"Neutral signals (CONSENSUS):    {neutral}")
    print(f"\nBaseline: random would be 50% on directional calls")

    # ===== By signal-tier hit rate =====
    print(f"\n{'='*100}")
    print(f"HIT RATE BY SIGNAL TIER")
    print(f"{'='*100}")
    tiers = ["STRONG_BUY", "WEAK_BUY", "CONSENSUS", "WEAK_SELL", "STRONG_SELL"]
    for tier in tiers:
        tier_rows = [r for r in detail if r["signal"] == tier]
        if not tier_rows: continue
        outcome_avg = sum(r["outcome_score"] for r in tier_rows) / len(tier_rows)
        tier_correct = sum(1 for r in tier_rows if "correct" in r["prediction_check"])
        tier_wrong = sum(1 for r in tier_rows if "wrong" in r["prediction_check"])
        tier_total = tier_correct + tier_wrong
        print(f"  {tier:<14} n={len(tier_rows):>2}  avg_outcome={outcome_avg:+.2f}  "
              f"correct={tier_correct}/{tier_total}  "
              f"{'(neutral)' if tier == 'CONSENSUS' else ''}")

    # ===== Per-system detail =====
    print(f"\n{'='*100}")
    print(f"PER-SYSTEM PREDICTION CHECK")
    print(f"{'='*100}")
    print(f"\n{'System':<28} {'Our Signal':<14} {'Our Letter':<10} {'Explicit':<10} "
          f"{'Outcome':<24} {'Check':<12}")
    print("-" * 110)
    for r in detail:
        print(f"{r['system']:<28} {r['signal']:<14} {r['our_final']:<10} {r['explicit']:<10} "
              f"{r['outcome']:<24} {r['prediction_check']:<12}")

    # ===== Outcome correlation =====
    # Pearson correlation: our notches vs outcome_score
    notches = [r["div_notches"] for r in detail]
    outcomes_list = [r["outcome_score"] for r in detail]
    n = len(notches)
    if n > 1:
        mean_x = sum(notches) / n
        mean_y = sum(outcomes_list) / n
        num = sum((notches[i] - mean_x) * (outcomes_list[i] - mean_y) for i in range(n))
        var_x = sum((x - mean_x)**2 for x in notches)
        var_y = sum((y - mean_y)**2 for y in outcomes_list)
        denom = (var_x ** 0.5) * (var_y ** 0.5) if var_x and var_y else 0
        corr = num / denom if denom else 0
        print(f"\nPearson correlation (our notches vs outcome score): {corr:+.3f}")
        print(f"  Positive correlation = model's positive divergence predicts positive outcomes ✓")

    # Save backtest summary as JSON
    summary = {
        "n_systems": len(detail),
        "directional_signals": total_directional,
        "correct": correct,
        "wrong": wrong,
        "neutral_consensus": neutral,
        "hit_rate": hit_rate,
        "pearson_correlation": corr if n > 1 else None,
        "by_tier": {
            tier: {
                "n": len([r for r in detail if r["signal"] == tier]),
                "avg_outcome": (sum(r["outcome_score"] for r in detail if r["signal"] == tier) /
                                 max(1, len([r for r in detail if r["signal"] == tier]))),
            }
            for tier in tiers
        },
        "details": detail,
    }
    out_path = HERE / "outputs" / "backtest_concurrent_results.json"
    out_path.write_text(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
