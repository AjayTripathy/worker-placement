"""Run 4-axis composite across all 31 hospital systems + historical backtest.

For each system:
  1. Pull all hospital cost reports across query variants (dedupe by CCN+FY)
  2. Compute current 4-axis composite using most-recent-FY data
  3. Compute historical composite at 2021 + 2022 fiscal-year snapshots
  4. Compare to explicit Moody's/S&P/Fitch ratings → divergence

For Tower Health (distressed): does our 2021/2022 snapshot predict the
2023 downgrade to CCC+?

Output:
  outputs/run30_results.json   — full per-system breakdown
  outputs/run30_summary.md     — readable findings
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from .composite_score import (
    gather_facilities, composite, consensus_explicit_score,
    divergence_signal, HOSPITAL_COLS,
)

HERE = Path(__file__).parent
SYSTEMS_FILE = HERE / "data" / "top_30_systems.json"
RESULTS_FILE = HERE / "outputs" / "run30_results.json"
SUMMARY_FILE = HERE / "outputs" / "run30_summary.md"


def _row_fy(r: dict) -> str:
    """Extract YYYY from Fiscal Year End Date."""
    fy = r.get(HOSPITAL_COLS["fy_end"]) or ""
    return fy[:4] if len(fy) >= 4 else ""


def process_system(sys_def: dict) -> dict:
    name = sys_def["name"]
    queries = sys_def["queries"]
    state = sys_def["state"]
    moodys = sys_def.get("moodys")
    sp = sys_def.get("sp")
    fitch = sys_def.get("fitch")

    print(f"\n=== {name} (state={state}) ===", file=sys.stderr)
    rows = gather_facilities(queries)
    n_rows = len(rows)
    n_ccns = len({r.get(HOSPITAL_COLS["ccn"]) for r in rows if r.get(HOSPITAL_COLS["ccn"])})
    fys_available = sorted({_row_fy(r) for r in rows if _row_fy(r)})
    print(f"  {n_rows} cost reports, {n_ccns} unique CCNs, FYs: {fys_available}", file=sys.stderr)

    # Current composite (most recent FY)
    latest_fy = fys_available[-1] if fys_available else None
    current = composite(rows, state=state, fiscal_year=latest_fy)

    # Historical snapshots: 2021 and 2022 fiscal years
    snap_2021 = composite(rows, state=state, fiscal_year="2021") if "2021" in fys_available else None
    snap_2022 = composite(rows, state=state, fiscal_year="2022") if "2022" in fys_available else None
    snap_2023 = composite(rows, state=state, fiscal_year="2023") if "2023" in fys_available else None

    # Divergence vs explicit
    explicit_score, explicit_letter = consensus_explicit_score(moodys, sp, fitch)
    if current.get("composite_score") is not None:
        notches, signal = divergence_signal(current["composite_score"], explicit_score)
    else:
        notches, signal = 0, "UNVERIFIABLE"

    return {
        "system": name,
        "state": state,
        "tier_notes": sys_def.get("tier", ""),
        "ratings_explicit": {
            "moodys": moodys, "sp": sp, "fitch": fitch,
            "consensus_score": explicit_score, "consensus_letter": explicit_letter,
        },
        "n_cost_reports": n_rows,
        "n_unique_ccns": n_ccns,
        "fiscal_years_available": fys_available,
        "current_score": {
            "fiscal_year": latest_fy,
            "composite": current.get("composite_score"),
            "letter": current.get("letter"),
            "axes": current.get("axes"),
        },
        "snap_2021": {
            "composite": snap_2021.get("composite_score") if snap_2021 else None,
            "letter":    snap_2021.get("letter") if snap_2021 else None,
        } if snap_2021 else None,
        "snap_2022": {
            "composite": snap_2022.get("composite_score") if snap_2022 else None,
            "letter":    snap_2022.get("letter") if snap_2022 else None,
        } if snap_2022 else None,
        "snap_2023": {
            "composite": snap_2023.get("composite_score") if snap_2023 else None,
            "letter":    snap_2023.get("letter") if snap_2023 else None,
        } if snap_2023 else None,
        "divergence_notches": notches,
        "signal": signal,
    }


def main():
    t0 = time.time()
    systems = json.loads(SYSTEMS_FILE.read_text())["systems"]
    print(f"Processing {len(systems)} systems...", file=sys.stderr)

    results = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(process_system, s): s["name"] for s in systems}
        for fut in as_completed(futures):
            results.append(fut.result())

    results.sort(key=lambda r: -r["divergence_notches"])

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_FILE.write_text(json.dumps({
        "run_date": "2026-05-27",
        "n_systems": len(results),
        "elapsed_seconds": round(time.time() - t0, 1),
        "results": results,
    }, indent=2, default=str))

    # Print summary
    print(f"\n{'='*120}", file=sys.stderr)
    print(f"DONE in {time.time()-t0:.1f}s — {len(results)} systems", file=sys.stderr)
    print(f"{'='*120}\n", file=sys.stderr)

    print(f"{'System':<32} {'Explicit':<10} {'Our (FY24)':<11} {'Notches':<10} {'Signal':<14} "
          f"{'2021':<6} {'2022':<6} {'2023':<6}")
    print("-" * 130)
    for r in results:
        cur_letter = r["current_score"]["letter"] or "UNV"
        explicit_letter = r["ratings_explicit"]["consensus_letter"]
        s21 = (r.get("snap_2021") or {}).get("letter") or "—"
        s22 = (r.get("snap_2022") or {}).get("letter") or "—"
        s23 = (r.get("snap_2023") or {}).get("letter") or "—"
        n_ccn = r["n_unique_ccns"]
        print(f"{r['system']:<32} {explicit_letter:<10} {cur_letter:<11} "
              f"{r['divergence_notches']:+.1f} ({n_ccn:>2}c) {r['signal']:<14} "
              f"{s21:<6} {s22:<6} {s23:<6}")


if __name__ == "__main__":
    main()
