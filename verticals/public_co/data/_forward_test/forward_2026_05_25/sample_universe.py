"""Sample 60 names from the forward-test candidate pool.

Pure random sample (seeded), -25% drawdown floor. Same design as Tier 3.
No forward returns available yet — measurement is in 12-24 months.
"""
import json
import random
from pathlib import Path

HERE = Path(__file__).parent
N = 60
SEED = 20260525
DRAWDOWN_FLOOR = -0.25


def main():
    pool = json.loads((HERE / "candidate_pool.json").read_text())
    distressed = [r for r in pool if r["drawdown_2026_05_25"] <= DRAWDOWN_FLOOR]
    print(f"Distressed pool: {len(distressed)}")

    rng = random.Random(SEED)
    sampled = rng.sample(distressed, N)
    sampled.sort(key=lambda r: r["ticker"])

    # No leak fields needed — there are no forward returns yet.
    # But keep structure consistent with prior tiers.
    (HERE / "forward_test_set.json").write_text(json.dumps(sampled, indent=2))
    (HERE / "_unblinded" / "forward_test_set.json").write_text(json.dumps(sampled, indent=2))

    print(f"Sampled {N} → forward_test_set.json")
    print()
    print(f"{'TK':6}  {'sector':22}  {'dd':>7}  {'price':>8}  CIK")
    for r in sampled:
        print(f"  {r['ticker']:6}  {(r.get('sector') or '')[:22]:22}  {r['drawdown_2026_05_25']*100:>+6.1f}%  ${r['price_2026_05_25']:>6.2f}  {r['cik']}")


if __name__ == "__main__":
    main()
