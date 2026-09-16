"""Sample 50 boring-middle names from the candidate pool.

Pure random sample (seeded) — no sector stratification, since
stratifying could itself be a form of selection. The 220-name pool
already represents the SP600 boring middle by drawdown filter; the
goal is to test the framework on a fair draw from that pool, not a
hand-curated subset.

Writes:
  - tier2_test_set.json  (unblinded, has forward_return — measurement use only)
  - tier2_test_set_blinded.json (agent-facing, leak fields stripped)
  - tier2_agent_manifest.json (unblinded — for synthesis only)

Run:
    python3 verticals/public_co/data/_backtest/boring_middle_2025_05/sample_universe.py
"""
import json
import random
from pathlib import Path

HERE = Path(__file__).parent
N = 50
SEED = 20260525

LEAK_FIELDS = {"forward_return", "price_2026_05_15"}


def main():
    pool = json.loads((HERE / "candidate_pool.json").read_text())
    boring = [r for r in pool if -0.25 <= r["drawdown_2025_05_15"] <= -0.10]
    print(f"Boring-middle pool: {len(boring)}")

    rng = random.Random(SEED)
    sampled = rng.sample(boring, N)
    sampled.sort(key=lambda r: r["ticker"])

    # Unblinded test set (for synthesis.py measurement)
    unblinded_dir = HERE / "_unblinded"
    unblinded_dir.mkdir(exist_ok=True)
    (unblinded_dir / "tier2_test_set.json").write_text(json.dumps(sampled, indent=2))

    # Blinded test set (for agents)
    blinded = []
    for r in sampled:
        b = {k: v for k, v in r.items() if k not in LEAK_FIELDS}
        blinded.append(b)
    (HERE / "tier2_test_set.json").write_text(json.dumps(blinded, indent=2))

    print(f"Sampled {N} names")
    print(f"  → {unblinded_dir}/tier2_test_set.json (unblinded)")
    print(f"  → {HERE}/tier2_test_set.json (blinded, agent-facing)")
    print()
    # Show what was sampled
    import statistics
    rets = [r["forward_return"] for r in sampled]
    print(f"Sampled universe baseline forward return: mean={statistics.mean(rets)*100:+.1f}%, median={statistics.median(rets)*100:+.1f}%")
    print()
    for r in sampled:
        print(f"  {r['ticker']:6}  {r['sector'][:20]:20}  dd={r['drawdown_2025_05_15']*100:+.1f}%  fwd={r['forward_return']*100:+.1f}%")


if __name__ == "__main__":
    main()
