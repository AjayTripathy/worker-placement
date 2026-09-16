"""IJR Phase-1 universe runner.

For each of the 608 IJR holdings, run the universal deterministic
m-source battery and produce a per-ticker composite score.

UNIVERSAL BATTERY (modules needing only (cik, cutoff_date), no curated
inputs — they auto-discover what they need from EDGAR):

  filing_timeliness        operational/accounting discipline
  mw_lifecycle             material weakness lifecycle
  going_concern_detector   going-concern paragraph presence
  auditor_change_tracker   auditor turnover
  lender_concession        credit-facility amendments
  insider_buy_timing       insider purchases vs calendar
  working_capital_drift    DSI/DSO/DPO YoY drift (NEW)
  share_count_drift        diluted share issuance velocity (NEW)
  runway_calculator        cash runway months (NEW, dev-stage only)
  rpo_drift                SaaS RPO vs revenue decel (NEW, SaaS only)

CLUSTER-SPECIFIC BATTERY (requires per-name inputs; deferred to Phase 2).

OUTPUT

  data/_ijr_manifest/phase1_scores.json:
    {
      "cutoff_date": "...",
      "n_names_attempted": 608,
      "n_names_scored": int,
      "n_errors": int,
      "scores": {
         "AFRM": {
            "cik": "0001820302",
            "cluster": "FINANCIALS",
            "rfm_tuples": [
              {"M_source": "filing_timeliness", "severity": "PASS",
               "direction": "positive", "signal": "ON_TIME_STREAK"},
              ...
            ],
            "distress_composite": 0.123,
            "recovery_composite": 0.4,
            "tier": "LONG_TIER"
         },
         ...
      }
    }

Usage:
  python3 -m verticals.public_co.ijr_universe_runner --cutoff 2024-05-15
  python3 -m verticals.public_co.ijr_universe_runner --cutoff 2024-05-15 --max 10  # smoke
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Optional

from .m_sources import (
    composite_recompute,
    filing_timeliness,
    going_concern_detector,
    auditor_change_tracker,
    lender_concession,
    insider_buy_timing,
    mw_lifecycle,
    working_capital_drift,
    share_count_drift,
    runway_calculator,
    rpo_drift,
)

HERE = Path(__file__).parent
HOLDINGS = HERE / "data" / "_ijr_manifest" / "ijr_holdings_2024_06_30.json"
OUT_FILE = HERE / "data" / "_ijr_manifest" / "phase1_scores.json"


# ============================================================
# Severity / direction mapping for legacy m-sources
# ============================================================
# Each module's `signal` field is mapped to (severity, direction).
# severity ∈ {PASS, UNVERIFIABLE, MODERATE_UNDERDELIVERY,
#             SEVERE_UNDERDELIVERY, RED_FLAG_NEGATIVE}
# direction ∈ {positive, neutral, negative}

_FT_MAP = {
    "ON_TIME_STREAK":       ("PASS", "positive"),
    "RECENT_NT_FILING":     ("MODERATE_UNDERDELIVERY", "negative"),
    "RECURRING_AMENDMENTS": ("SEVERE_UNDERDELIVERY", "negative"),
    "DRIFTING_TIMING":      ("MODERATE_UNDERDELIVERY", "negative"),
    "ERROR":                ("UNVERIFIABLE", "neutral"),
}

_GC_MAP = {
    "NO_GOING_CONCERN":         ("PASS", "positive"),
    "UNCERTAINTY_LANGUAGE":     ("MODERATE_UNDERDELIVERY", "negative"),
    "NEW_LANGUAGE_ADDED":       ("MODERATE_UNDERDELIVERY", "negative"),
    "SUBSTANTIAL_DOUBT":        ("SEVERE_UNDERDELIVERY", "negative"),
    "EXPLICIT_GOING_CONCERN":   ("RED_FLAG_NEGATIVE", "negative"),
    "GOING_CONCERN_ISSUED":     ("RED_FLAG_NEGATIVE", "negative"),
    "ERROR":                    ("UNVERIFIABLE", "neutral"),
}

_AC_MAP = {
    "CLEAN_AUDITOR_TENURE":         ("PASS", "positive"),
    "STABLE_AUDITOR":               ("PASS", "positive"),
    "RECENT_BIG4_TO_BIG4":          ("PASS", "neutral"),
    "RECENT_AUDITOR_CHANGE":        ("MODERATE_UNDERDELIVERY", "negative"),
    "RECENT_BIG4_TO_NON_BIG4":      ("SEVERE_UNDERDELIVERY", "negative"),
    "RECURRING_AUDITOR_TURNOVER":   ("SEVERE_UNDERDELIVERY", "negative"),
    "AUDITOR_DOWNGRADE":            ("SEVERE_UNDERDELIVERY", "negative"),
    "ERROR":                        ("UNVERIFIABLE", "neutral"),
}

_LC_MAP = {
    "NO_AMENDMENTS":          ("PASS", "positive"),
    "ROUTINE_AMENDMENT":      ("PASS", "neutral"),
    "PRICING_CONCESSION":     ("MODERATE_UNDERDELIVERY", "negative"),
    "COVENANT_WAIVER":        ("SEVERE_UNDERDELIVERY", "negative"),
    "MULTIPLE_CONCESSIONS":   ("RED_FLAG_NEGATIVE", "negative"),
    "ERROR":                  ("UNVERIFIABLE", "neutral"),
}

_IB_MAP = {
    "CLEAN_BUY_PATTERN":            ("PASS", "positive"),
    "INSIDER_BUYING":               ("PASS", "positive"),
    "QUIET_PERIOD_BUYS_ONLY":       ("PASS", "positive"),
    "NO_RECENT_INSIDER_ACTIVITY":   ("PASS", "neutral"),
    "NO_INSIDER_BUYS":              ("PASS", "neutral"),
    "NEAR_PROMOTIONAL_8K":          ("MODERATE_UNDERDELIVERY", "negative"),
    "DUMP_PATTERN":                 ("SEVERE_UNDERDELIVERY", "negative"),
    "ERROR":                        ("UNVERIFIABLE", "neutral"),
}

_MW_MAP = {
    "CLEAN":                    ("PASS", "positive"),
    "NO_MW":                    ("PASS", "positive"),
    "NO_MW_HISTORY":            ("PASS", "positive"),
    "REMEDIATED":               ("PASS", "neutral"),
    "MW_REMEDIATED":            ("PASS", "neutral"),
    "MW_HIGH_QUALITY_CURE":     ("PASS", "neutral"),
    "MW_LOW_QUALITY_CURE":      ("MODERATE_UNDERDELIVERY", "negative"),
    "OPEN_MW":                  ("SEVERE_UNDERDELIVERY", "negative"),
    "MW_OPEN":                  ("SEVERE_UNDERDELIVERY", "negative"),
    "RECURRING_MW":             ("RED_FLAG_NEGATIVE", "negative"),
    "NEW_MW":                   ("MODERATE_UNDERDELIVERY", "negative"),
    "ERROR":                    ("UNVERIFIABLE", "neutral"),
}

LEGACY_MAPS = {
    "filing_timeliness":        _FT_MAP,
    "going_concern_detector":   _GC_MAP,
    "auditor_change_tracker":   _AC_MAP,
    "lender_concession":        _LC_MAP,
    "insider_buy_timing":       _IB_MAP,
    "mw_lifecycle":             _MW_MAP,
}


# ============================================================
# Universal dispatch table
# ============================================================
# Each entry: (m_source_name, callable(cik, cutoff_date) -> dict)

UNIVERSAL_BATTERY: list[tuple[str, Callable[[str, str], dict]]] = [
    ("filing_timeliness",       filing_timeliness.query_filing_timeliness),
    ("going_concern_detector",  going_concern_detector.query_going_concern),
    ("auditor_change_tracker",
       lambda cik, c: auditor_change_tracker.query_auditor_changes(cik, cutoff_date=c)),
    ("lender_concession",       lender_concession.query_lender_concession),
    ("insider_buy_timing",      insider_buy_timing.query_insider_buy_timing),
    ("mw_lifecycle",            mw_lifecycle.query_mw_lifecycle),
    # New modules — return severity/direction natively
    ("working_capital_drift",   working_capital_drift.query_working_capital_drift),
    ("share_count_drift",       share_count_drift.query_share_count_drift),
    ("runway_calculator",       runway_calculator.query_runway),
    ("rpo_drift",               rpo_drift.query_rpo_drift),
]


# ============================================================
# Conversion to RFM-tuple format
# ============================================================

def _to_rfm_tuple(m_source_name: str, result: dict) -> dict:
    """Normalize an m-source result to {M_source, severity, direction, signal, _raw}.

    Three paths:
      1. Module returns severity + direction at top level → take them.
      2. Legacy module returns only `signal` → look up via LEGACY_MAPS.
      3. Neither → UNVERIFIABLE + neutral.
    """
    if not isinstance(result, dict):
        return {
            "M_source": m_source_name,
            "severity": "UNVERIFIABLE",
            "direction": "neutral",
            "signal": "BAD_RESULT_TYPE",
            "_raw": {"error": "result not a dict"},
        }

    sev = result.get("severity")
    direction = result.get("direction")
    signal = result.get("signal")

    if sev and direction:
        return {
            "M_source": m_source_name,
            "severity": sev,
            "direction": direction,
            "signal":   signal or "UNNAMED",
            "_raw":     {k: v for k, v in result.items()
                          if k in ("metrics", "_note", "cik", "cutoff_date")},
        }

    # Legacy mapping path
    leg = LEGACY_MAPS.get(m_source_name)
    if leg and signal in leg:
        sev, direction = leg[signal]
    elif leg:
        # Unmapped signal value
        sev, direction = "UNVERIFIABLE", "neutral"
        signal = signal or "UNMAPPED"
    else:
        sev, direction = "UNVERIFIABLE", "neutral"

    return {
        "M_source": m_source_name,
        "severity": sev,
        "direction": direction,
        "signal":   signal or "UNNAMED",
        "_raw":     {k: v for k, v in result.items() if k in ("_note",)},
    }


# ============================================================
# Per-name runner
# ============================================================

def run_one(cik: str, cutoff_date: str, *, verbose: bool = False) -> list[dict]:
    """Run the universal battery for one CIK; return list of RFM tuples."""
    tuples = []
    for name, fn in UNIVERSAL_BATTERY:
        t0 = time.time()
        try:
            res = fn(cik, cutoff_date)
        except Exception as e:
            res = {"signal": "ERROR", "_note": f"{type(e).__name__}: {e}"}
            if verbose:
                print(f"    {name} → exception {e}", file=sys.stderr)
        elapsed = time.time() - t0
        tup = _to_rfm_tuple(name, res)
        tup["_elapsed_s"] = round(elapsed, 2)
        tuples.append(tup)
        if verbose:
            print(f"    {name:30s} {tup['severity']:25s} {tup['direction']:8s} ({elapsed:.1f}s)")
    return tuples


# ============================================================
# Universe orchestration
# ============================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff", required=True, help="Cutoff date (YYYY-MM-DD)")
    ap.add_argument("--max", type=int, default=0, help="Cap names processed (smoke test)")
    ap.add_argument("--start", type=int, default=0, help="Skip first N names (resume)")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--out", default=str(OUT_FILE))
    ap.add_argument("--workers", type=int, default=4,
                    help="Concurrent ticker workers (SEC rate-limit safe at 4-8)")
    args = ap.parse_args()

    if not HOLDINGS.exists():
        print(f"Holdings file missing: {HOLDINGS}", file=sys.stderr)
        sys.exit(1)

    holdings = json.loads(HOLDINGS.read_text())
    # holdings is either a list of dicts or a dict with 'holdings' key
    if isinstance(holdings, dict) and "holdings" in holdings:
        holdings = holdings["holdings"]

    # Filter to names with CIK
    names = [h for h in holdings if h.get("cik")]
    print(f"Loaded {len(holdings)} holdings, {len(names)} with CIK", file=sys.stderr)

    if args.start:
        names = names[args.start:]
    if args.max:
        names = names[: args.max]

    # Resume support: load existing scores if present
    out_path = Path(args.out)
    scores: dict[str, dict] = {}
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text())
            scores = existing.get("scores", {})
            print(f"Resuming with {len(scores)} existing scores", file=sys.stderr)
        except Exception:
            pass

    todo = [h for h in names if h.get("ticker") and h["ticker"] not in scores]
    print(f"{len(todo)} names to process with {args.workers} workers", file=sys.stderr)

    save_lock = Lock()
    counters = {"done": 0, "err": 0}
    t_start = time.time()

    def _worker(h: dict) -> Optional[tuple[str, dict]]:
        ticker = h["ticker"]
        cik = str(h["cik"]).zfill(10)
        cluster = h.get("cluster", "UNKNOWN")
        try:
            tuples = run_one(cik, args.cutoff, verbose=False)
        except Exception as e:
            print(f"  {ticker} FAILED: {type(e).__name__}: {e}", file=sys.stderr)
            return None
        pilot = {"ticker": ticker, "cutoff": args.cutoff, "rfm_tuples": tuples}
        comp = composite_recompute.recompute(pilot)
        return ticker, {
            "cik": cik,
            "cluster": cluster,
            "rfm_tuples": tuples,
            "distress_composite": comp.get("distress_composite"),
            "recovery_composite": comp.get("recovery_composite"),
            "tier": comp.get("tier"),
            "n_formal_tuples": comp.get("n_formal_tuples"),
            "severity_counts": comp.get("severity_counts"),
        }

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(_worker, h): h for h in todo}
        for fut in as_completed(futures):
            result = fut.result()
            with save_lock:
                if result is None:
                    counters["err"] += 1
                else:
                    ticker, payload = result
                    scores[ticker] = payload
                    counters["done"] += 1

                n_done = counters["done"]
                # Persist + status every 20 names
                if n_done > 0 and n_done % 20 == 0:
                    _save(out_path, args.cutoff, scores, counters["err"])
                    elapsed = time.time() - t_start
                    rate = n_done / elapsed if elapsed > 0 else 0
                    remaining = (len(todo) - n_done) / rate if rate > 0 else float("inf")
                    print(f"  [{n_done}/{len(todo)}] rate={rate:.2f}/s ETA={remaining/60:.1f}m",
                          file=sys.stderr)

    _save(out_path, args.cutoff, scores, counters["err"])
    elapsed = time.time() - t_start
    print(f"\nDone. {counters['done']} scored, {counters['err']} errors, {elapsed/60:.1f}m elapsed.",
          file=sys.stderr)
    print(f"Output: {out_path}", file=sys.stderr)


def _save(out_path: Path, cutoff: str, scores: dict, n_err: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "cutoff_date":       cutoff,
        "n_names_scored":    len(scores),
        "n_errors":          n_err,
        "scores":            scores,
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
