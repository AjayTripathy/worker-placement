"""Sample 60 distressed-pool names from the Tier 3 candidate pool.

Pure random sample (seeded). Same design as Tier 2 — no sector
stratification, just a fair draw from the drawdown-filtered pool.

Writes:
  - _unblinded/tier3_test_set.json  (with forward_return, measurement only)
  - tier3_test_set.json             (blinded, agent-facing)
"""
import json
import random
from pathlib import Path

HERE = Path(__file__).parent
N = 60
SEED = 20240515
DRAWDOWN_FLOOR = -0.25
LEAK_FIELDS = {"forward_return", "price_2025_05_15", "last_trade_date", "delisted_before_measurement"}


def main():
    pool = json.loads((HERE / "candidate_pool.json").read_text())
    distressed = [r for r in pool if r["drawdown_2024_05_15"] <= DRAWDOWN_FLOOR]
    print(f"Distressed pool: {len(distressed)}")

    rng = random.Random(SEED)
    sampled = rng.sample(distressed, N)
    sampled.sort(key=lambda r: r["ticker"])

    (HERE / "_unblinded" / "tier3_test_set.json").write_text(json.dumps(sampled, indent=2))
    blinded = [{k: v for k, v in r.items() if k not in LEAK_FIELDS} for r in sampled]
    (HERE / "tier3_test_set.json").write_text(json.dumps(blinded, indent=2))

    print(f"Sampled {N} → tier3_test_set.json (blinded) + _unblinded/tier3_test_set.json (full)")
    print()
    import statistics
    rets = [r["forward_return"] for r in sampled]
    print(f"Sampled-universe baseline forward return: mean={statistics.mean(rets)*100:+.1f}%, median={statistics.median(rets)*100:+.1f}%")
    print(f"  catastrophes (<=-40%): {sum(1 for r in rets if r <= -0.4)}")
    print(f"  big winners (>+50%):   {sum(1 for r in rets if r >= 0.5)}")
    print()
    for r in sampled:
        delisted_tag = " (DELISTED)" if r.get("delisted_before_measurement") else ""
        print(f"  {r['ticker']:6}  {(r.get('sector') or '')[:18]:18}  dd={r['drawdown_2024_05_15']*100:+.1f}%  fwd={r['forward_return']*100:+.1f}%{delisted_tag}")


if __name__ == "__main__":
    main()
