"""
Post-process ticker_pe_crosswalk.json: for each matched PE, look up its
status by deriving from funding_history via pentagon_jbook._latest_funding_status.

Also produces a summary table ranked by SEVERE-status hits.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from verticals.public_co.m_sources.pentagon_jbook import _latest_funding_status

DATA = Path("verticals/public_co/data")
CROSSWALK = DATA / "_entity_resolution" / "ticker_pe_crosswalk.json"
PROGRAMS  = DATA / "_jbook_data" / "programs.json"

SEVERE = {
    "UNFUNDED_TWO_PLUS_YEARS", "UNFUNDED_THIS_YEAR",
    "TERMINATED", "FUNDED_SHRINKING",
}


def main():
    xwalk = json.loads(CROSSWALK.read_text())
    corpus = {p["program_id"]: p for p in json.loads(PROGRAMS.read_text())["programs"]}

    n_status_set = 0
    for tk, info in xwalk["tickers"].items():
        severe_count = 0
        for pe in info.get("matched_pes") or []:
            pid = pe.get("program_id")
            canon = corpus.get(pid)
            if not canon:
                continue
            derived = _latest_funding_status(canon)
            pe["status_derived"]    = derived["status"]
            pe["latest_funded_fy"]  = derived["latest_funded_year"]
            pe["latest_funded_M"]   = derived["latest_funded_M"]
            pe["n_consec_unfunded"] = derived["n_consecutive_unfunded"]
            pe["history_rows"]      = derived["history_rows"]
            n_status_set += 1
            if derived["status"] in SEVERE:
                severe_count += 1
        info["n_severe_pes"] = severe_count

    CROSSWALK.write_text(json.dumps(xwalk, indent=2, default=str))
    print(f"Updated {n_status_set} PE entries with derived status.", file=sys.stderr)

    rows = sorted(xwalk["tickers"].values(),
                   key=lambda r: (-r.get("n_severe_pes", 0),
                                    -(r.get("n_pes_matched") or 0)))

    print(f"\n{'TICKER':<7} {'#CTR':>5} {'$TOT':>9} {'#PE':>4} {'SEV':>4}  PE STATUSES")
    print("=" * 110)
    for r in rows:
        pes = r.get("matched_pes") or []
        pe_str = " | ".join([
            f"{p.get('pe_number','?')}={p.get('status_derived','?')}"
            for p in pes[:4]
        ])
        print(f"{r['ticker']:<7} {r['n_contracts_total']:>5} "
              f"${r['contracts_total_M']:>7.1f}M "
              f"{r['n_pes_matched']:>4} {r.get('n_severe_pes',0):>4}  "
              f"{pe_str[:75]}")


if __name__ == "__main__":
    main()
