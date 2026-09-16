"""Output-side detector-coverage validator for the RIPO diligencer run.

For each ticker, re-derives the graph-applicable detector/M-source set from
union(agent-declared issuer_features, keyword-net features over the filing) and
classifies each as DISPATCHED / DECLINED / GAP against the subagent's own
`detector_dispatch` accounting + the M-sources it actually queried.

A GAP = the graph says this detector applies to this issuer, but the agent
neither queried its source nor recorded a decline. That is the failure mode that
let pentagon_jbook silently vanish from the original RIPO run.

Run:  python3 -m verticals.public_co.ripo_coverage [TICKER ...]
      (no args = whole cohort)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .kg_index import coverage_gaps
from .ripo_cohort import COHORT

HERE = Path(__file__).parent
LOCAL = HERE / "data" / "_local"
DATA = HERE / "data"


def _filing_text(ticker: str, input_obj: dict) -> str | None:
    fn = input_obj.get("filing")
    if not fn:
        return None
    p = DATA / ticker.lower() / "filings" / fn
    if not p.exists():
        # tolerate index-relative or bare names
        hits = list((DATA / ticker.lower() / "filings").glob(f"*{Path(fn).stem}*"))
        p = hits[0] if hits else None
    try:
        return p.read_text(errors="ignore") if p and p.exists() else None
    except Exception:
        return None


def coverage_for(ticker: str) -> dict | None:
    fi = LOCAL / f"{ticker}.input.json"
    if not fi.exists():
        return None
    inp = json.loads(fi.read_text())
    cov = coverage_gaps(inp, filing_text=_filing_text(ticker, inp))
    cov["ticker"] = ticker
    return cov


def _print(cov: dict) -> None:
    t = cov["ticker"]
    print(f"\n=== {t} ===")
    print(f"  agent features ({len(cov['agent_features'])}): {', '.join(cov['agent_features']) or '—'}")
    if cov["keyword_only_features"]:
        print(f"  !! keyword-net caught features the agent did NOT declare: "
              f"{', '.join(cov['keyword_only_features'])}")
    print(f"  applicable={cov['n_applicable']}  dispatched={cov['n_dispatched']}  "
          f"declined={cov['n_declined']}  WEAK={cov.get('n_weak',0)}  GAPS={cov['n_gap']}")
    marks = {"DISPATCHED": "✓", "DECLINED": "·", "GAP": "✗", "WEAK_DISPATCH": "⚠"}
    for r in cov["rows"]:
        mark = marks.get(r["status"], "?")
        extra = f"  ({r['reason']})" if r["reason"] and r["status"] != "GAP" else ""
        print(f"    {mark} [{r['status']:13}] {r['kind']:8} {r['name']}"
              f"  via {', '.join(r['match_reasons'])}{extra}")
    for wd in cov.get("weak_dispatches", []):
        print(f"  ⚠⚠ WEAK: {wd['name']} queried with keys {wd['query_keys']} — "
              f"needs one of {wd['required']} to be a real check")
    for g in cov["gaps"]:
        print(f"  >>> GAP: {g['name']} ({g['kind']}) — {g['vq'] or ''}")


def main() -> None:
    tickers = sys.argv[1:] or [m.ticker for m in COHORT]
    total_gaps = 0
    for tk in tickers:
        cov = coverage_for(tk)
        if cov is None:
            print(f"\n=== {tk} === (no input.json)")
            continue
        _print(cov)
        total_gaps += cov["n_gap"]
    print(f"\nTOTAL COVERAGE GAPS across {len(tickers)} ticker(s): {total_gaps}")


if __name__ == "__main__":
    main()
