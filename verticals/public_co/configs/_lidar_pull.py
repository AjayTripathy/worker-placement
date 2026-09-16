"""Pull filings for the lidar / ADAS cohort.

Run from repo root:
    python3 -m verticals.public_co.configs._lidar_pull
"""
from __future__ import annotations

import sys
from pathlib import Path

from verticals.public_co import edgar
from verticals.public_co.lidar_cohort import COHORT, CUTOFF

HERE = Path(__file__).parent.parent
DATA = HERE / "data"

PRIORITY_FORMS = {"10-K", "10-Q", "S-1", "S-1/A", "S-4", "S-4/A",
                  "DEF 14A", "DEFM14A", "20-F", "F-1", "S-3", "S-3/A",
                  "8-K", "8-K/A"}


def main():
    for m in COHORT:
        print(f"\n=== {m.ticker} (CIK {m.cik}) ===", file=sys.stderr)
        out = DATA / m.ticker.lower()
        edgar.pull(cik=m.cik, cutoff_date=CUTOFF, priority_forms=PRIORITY_FORMS, out_dir=out)


if __name__ == "__main__":
    main()
