"""
Stage A — cheap-detector sweep across a candidate cohort.

For each (ticker, cik, name): runs
  1. insider_vs_calendar  — Form 4 × federal budget calendar
  2. pentagon_jbook       — contractor_name lookup against J-Book corpus
  3. usaspending          — DoD contract presence sanity check

Ranks candidates by SEVERE-signal count and prints a table.
Designed to be fast: no LLM calls. Network only (EDGAR + USAspending).
"""
from __future__ import annotations

import importlib
import json
import sys
import time
import traceback
from pathlib import Path

from verticals.public_co.m_sources import (
    insider_vs_calendar,
    pentagon_jbook,
    usaspending,
)

OUT_DIR = Path("verticals/public_co/data/_stage_a")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Severity tiers we treat as "hit" for ranking
SEVERE_TIERS = {
    "PROXIMATE_DISCRETIONARY",
    "CLUSTERED_DISCRETIONARY",
    "UNFUNDED_THIS_YEAR",
    "UNFUNDED_TWO_PLUS_YEARS",
    "TERMINATED",
    "FUNDED_SHRINKING",
}


def _gather_universe() -> list[dict]:
    """Aggregate tickers from the defense/space/quantum/robotics cohorts."""
    relevant = ["defense_cohort", "space_cohort",
                "quantum_cohort", "robotics_cohort"]
    universe: dict[str, dict] = {}
    for modname in relevant:
        try:
            m = importlib.import_module(f"verticals.public_co.{modname}")
            for member in m.COHORT:
                tk = member.ticker.upper()
                if tk not in universe:
                    universe[tk] = {
                        "ticker": tk,
                        "cik": member.cik,
                        "name": getattr(member, "name", "") or "",
                        "cohort": modname,
                    }
        except Exception as e:
            print(f"  ! {modname}: {e}", file=sys.stderr)
    return list(universe.values())


def _run_insider(cik: str, cutoff: str, lookback_days: int = 540) -> dict:
    try:
        return insider_vs_calendar.query_insider_sales_near_budget_events(
            cik=cik, cutoff_date=cutoff, lookback_days=lookback_days,
        )
    except Exception as e:
        return {"signal": "ERROR", "error": str(e)}


def _run_jbook(name: str, cutoff: str) -> dict:
    try:
        return pentagon_jbook.query_program_funding(
            contractor_name=name, cutoff_date=cutoff,
        )
    except Exception as e:
        return {"signal": "ERROR", "error": str(e)}


def _run_usaspending(name: str) -> dict:
    """Return summary: total $ obligated DoD + recent activity."""
    try:
        result = usaspending.query_dod_contracts(
            recipient_name=name, start_date="2020-01-01",
            end_date="2026-12-31", page_size=25,
        )
        return result
    except Exception as e:
        return {"error": str(e)}


def sweep(universe: list[dict], cutoff: str = "2026-05-19") -> list[dict]:
    results = []
    for i, c in enumerate(universe, 1):
        tk = c["ticker"]
        nm = c["name"]
        cik = c["cik"]
        print(f"\n[{i}/{len(universe)}] {tk:6} {nm[:50]}", file=sys.stderr)

        # 1. insider_vs_calendar
        t0 = time.time()
        ins = _run_insider(cik, cutoff)
        print(f"   insider: {ins.get('signal'):28} ({time.time()-t0:.1f}s)",
              file=sys.stderr)

        # 2. pentagon_jbook
        t0 = time.time()
        jb = _run_jbook(nm, cutoff)
        print(f"   jbook:   {jb.get('signal'):28} ({time.time()-t0:.1f}s)",
              file=sys.stderr)

        # 3. usaspending (sanity check — federal exposure or none)
        t0 = time.time()
        us = _run_usaspending(nm)
        n_awards = us.get("n_awards") or 0
        total_obl = us.get("total_amount") or 0
        print(f"   us:      {n_awards} awards "
              f"${total_obl/1e6:.1f}M ({time.time()-t0:.1f}s)",
              file=sys.stderr)

        # Aggregate severity hits
        hits = []
        if ins.get("signal") in SEVERE_TIERS:
            hits.append(f"insider:{ins['signal']}")
        if jb.get("signal") in SEVERE_TIERS:
            hits.append(f"jbook:{jb['signal']}")

        results.append({
            "ticker": tk,
            "name": nm,
            "cik": cik,
            "cohort": c["cohort"],
            "insider_signal": ins.get("signal"),
            "insider_summary": {
                "n_form4_filings":  ins.get("n_form4_filings"),
                "n_total_sales":    ins.get("n_total_sales"),
                "n_proximate":      ins.get("n_proximate_sales"),
                "n_discretionary":  ins.get("n_discretionary_proximate"),
                "n_unique_owners":  ins.get("n_unique_owners_proximate"),
                "proximate_value_usd": ins.get("proximate_value_usd"),
                "matched_events":   [e["event_date"] for e in (ins.get("matched_events") or [])],
            },
            "jbook_signal": jb.get("signal"),
            "jbook_matches": len(jb.get("matched_programs") or []),
            "usaspending_awards": n_awards or 0,
            "usaspending_total_M": round(total_obl / 1e6, 2),
            "hit_count": len(hits),
            "hits": hits,
        })
    return results


def main():
    cutoff = "2026-05-19"
    universe = _gather_universe()
    print(f"Universe: {len(universe)} tickers", file=sys.stderr)
    print(f"Cutoff: {cutoff}\n", file=sys.stderr)

    results = sweep(universe, cutoff=cutoff)

    # Rank by hit_count, then by total proximate value
    results.sort(
        key=lambda r: (
            -r["hit_count"],
            -(r["insider_summary"].get("proximate_value_usd") or 0),
        )
    )

    # Write JSON
    out_path = OUT_DIR / "stage_a_results.json"
    out_path.write_text(json.dumps({
        "_meta": {"cutoff": cutoff, "n_universe": len(universe)},
        "results": results,
    }, indent=2, default=str))
    print(f"\nWrote {out_path}", file=sys.stderr)

    # Print summary table
    print("\n" + "=" * 100)
    print(f"{'TICKER':<7} {'COHORT':<18} {'INSIDER':<26} "
          f"{'JBOOK':<26} {'USA-$M':>8} {'HITS':>4}")
    print("=" * 100)
    for r in results:
        print(f"{r['ticker']:<7} {r['cohort'][:18]:<18} "
              f"{(r['insider_signal'] or '-')[:26]:<26} "
              f"{(r['jbook_signal'] or '-')[:26]:<26} "
              f"{r['usaspending_total_M']:>8.1f} "
              f"{r['hit_count']:>4}")


if __name__ == "__main__":
    main()
