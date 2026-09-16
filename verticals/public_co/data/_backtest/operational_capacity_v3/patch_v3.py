"""Patch the 5 remaining v3 names that the main probe didn't finish."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from probe_v3 import probe, TARGETS

HERE = Path(__file__).parent

REMAINING = ["ASIX", "TROX", "AMSC", "FOR", "MTW"]


def main():
    results_all = []
    # Load already-completed
    for tk in TARGETS:
        p = HERE / f"probe_{tk}.json"
        if p.exists():
            results_all.append(json.loads(p.read_text()))

    for tk in REMAINING:
        if (HERE / f"probe_{tk}.json").exists():
            continue
        try:
            r = probe(tk, TARGETS[tk])
        except Exception as e:
            r = {"ticker": tk, "error": str(e)}
        (HERE / f"probe_{tk}.json").write_text(json.dumps(r, indent=2, default=str))
        results_all.append(r)

    (HERE / "probe_all.json").write_text(json.dumps(results_all, indent=2, default=str))
    print(f"\nTotal probes: {len(results_all)}")


if __name__ == "__main__":
    main()
