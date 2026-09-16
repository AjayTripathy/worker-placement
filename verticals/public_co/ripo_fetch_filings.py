"""Pull pre-cutoff (=IPO-date) prospectus filings for the RIPO cohort.

Each name's cutoff is its IPO date, so this captures the registration/prospectus
documents (S-1, F-1, and the 424B final prospectuses) that an investor reading
at the offering would have. Writes into data/{ticker_lower}/filings/ + an index,
exactly where the blinded subagent expects them.

Run: python3 -m verticals.public_co.ripo_fetch_filings
"""
from __future__ import annotations

import sys
from pathlib import Path

from .edgar import pull
from .ripo_cohort import COHORT

DATA = Path(__file__).parent / "data"

# Prospectus + registration families (US S-1 and foreign-issuer F-1), plus the
# 424B final-prospectus variants filed at pricing.
PRIORITY_FORMS = {
    "S-1", "S-1/A", "F-1", "F-1/A",
    "424B1", "424B2", "424B3", "424B4", "424B5",
}


def main() -> None:
    only = set(sys.argv[1:])  # optional: restrict to given tickers
    for m in COHORT:
        if only and m.ticker not in only:
            continue
        out_dir = DATA / m.ticker.lower()
        print(f"\n=== {m.ticker} ({m.name}) cik={m.cik} cutoff={m.cutoff} ===",
              file=sys.stderr)
        try:
            pre = pull(m.cik, m.cutoff, PRIORITY_FORMS, out_dir)
            got = list((out_dir / "filings").glob("*.txt"))
            forms = sorted({r["form"] for r in pre if r["form"] in PRIORITY_FORMS})
            print(f"  -> {len(pre)} pre-cutoff filings, prospectus forms present: "
                  f"{forms or 'NONE'}, downloaded {len(got)} files", file=sys.stderr)
        except Exception as e:
            print(f"  !! ERROR pulling {m.ticker}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
