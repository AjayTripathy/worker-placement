"""Verify that no agent-facing JSON contains post-cutoff leak fields.

Agent-facing files in this directory MUST NOT contain:
  - forward_return
  - price_2026_05_15
  - date_removed
  - reason         (post-cutoff removal narrative)
  - date           (removal date)

The unblinded sources live in `_unblinded/`. This script verifies the
top-level files are blinded; the unblinded directory is intentionally
excluded and warned about by `_unblinded/README.md`.

Exits 0 if clean, 1 if any leak field is found.

Run:
    python3 verticals/public_co/data/_backtest/survivorship_2025_05/verify_blinded.py
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
LEAK_FIELDS = {"forward_return", "price_2026_05_15", "date_removed", "reason", "date"}

AGENT_FACING = [
    "combined_test_set.json",
    "control_survivors.json",
    "sp600_removals.json",
    "agent_manifest.json",
    "test_universe.json",
]


def walk(node, path="$"):
    """Yield (path, key) for every dict key encountered."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield (path, k)
            yield from walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}[{i}]")


def main():
    fails = []
    for fn in AGENT_FACING:
        p = HERE / fn
        if not p.exists():
            print(f"  MISSING: {fn}")
            fails.append((fn, "MISSING"))
            continue
        data = json.loads(p.read_text())
        leaks = []
        for path, key in walk(data):
            if key in LEAK_FIELDS:
                leaks.append((path, key))
        if leaks:
            example = leaks[0]
            print(f"  FAIL: {fn}  -- found {len(leaks)} leak field(s), first at {example[0]}.{example[1]}")
            fails.append((fn, leaks))
        else:
            print(f"  OK:   {fn}")

    if fails:
        print(f"\nFAIL: {len(fails)} file(s) contain leak fields.")
        sys.exit(1)
    print("\nAll agent-facing files are clean of post-cutoff leak fields.")


if __name__ == "__main__":
    main()
