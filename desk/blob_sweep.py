"""blob_sweep — daily ranked drip of the breadth-rejected discovery blob into the Opus
triage conveyor (principal 2026-08-07: "why not do a cheap opus triage then court
everything 6/10 or higher?").

Tiering rationale: the blob is a regime fact (~1/3 of the liquid tape ≥20% off highs) —
running it ALL down at once would starve the conveyor and swamp adjudication, and below
the courtable tier the velocity + orphan screens already provide coverage. So: courtable
tier only (mcap ≥ $250M), ranked by EXCESS drawdown vs the name's own sector median
(FLUT-class names first — a −70% name in a −20% sector outranks a −40% name in a −35%
sector), top BLOB_DAILY per day into REFUTABILITY. court_runner's automated 6/10
court-worthiness gate then escalates to full Fable red/blue courts; ≤3 is killed with
the triage as the record. Queue dedupe (all rows, incl. DONE/KILLED) makes the drip
idempotent and self-advancing: each day picks the best names not yet seen.

  python3 -m desk.blob_sweep            # one drip (also called by class_dislocation.run)
"""
from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOB_FILE = ROOT / "desk" / "data" / "discovery_blob.json"
BLOB_DAILY = int(os.environ.get("BLOB_SWEEP_DAILY", "40"))
MIN_MCAP = 250e6


# EQUITY/EV BELOW THIS = the drawdown is capital-structure amplified before it is anything else.
# At mcap/EV = 0.125 (SID: R$6.0B cap against R$42.1B net debt) an 8% EV decline is a ~60% equity
# decline with NOTHING having gone wrong at the asset level.
LEVERED_STUB_RATIO = 0.25


def _leverage_flags(pick: list) -> dict:
    """Annotate picks whose 'excess drawdown' is manufactured by leverage rather than mispricing.

    WHY (2026-08-17, filed by SID's refutability bench). excess_dd is computed on MARKET CAP, so the
    screen systematically SELECTS LEVERAGE AND REPORTS IT AS DISLOCATION: a levered stub's equity
    amplifies every EV move, so it out-drawdowns its sector median by construction and sorts to the
    top of the queue. SID's -59.4% is arithmetically explained by equity being ~12.5% of EV, with
    leverage RISING through the drawdown (3.24x -> 3.49x) — the capital structure working as
    designed, not the market erring. All three names that reached ADJUDICATE from the 08-12 sweep
    came in this way.

    It ANNOTATES, it does not drop. A levered stub can be a real opportunity — but it is an
    EV-level question with an EVENT gate, and a price gate on one is a beta-carrier self-trigger
    that fires when the thesis is WORSE rather than when the name is cheaper. The bench must be
    told which kind of object it is holding before it spends a court on it.

    A failed lookup yields NO flag and says so — never a silent 'clean', which would read as
    'leverage checked and fine' when nothing was checked.
    """
    out = {}
    try:
        import yfinance as yf
    except Exception:
        return out
    for r in pick:
        t = r["ticker"]
        try:
            info = yf.Ticker(t).info or {}
            ev, mcap = info.get("enterpriseValue"), info.get("marketCap") or r.get("mcap")
            if not ev or not mcap or ev <= 0:
                out[t] = ("  [LEVERAGE UNCHECKED — enterprise value not resolvable; do NOT read this "
                          "as an unlevered name, establish the capital structure yourself]")
                continue
            ratio = float(mcap) / float(ev)
            if ratio < LEVERED_STUB_RATIO:
                out[t] = (f"  [LEVERED STUB: equity is {ratio:.0%} of EV — this excess drawdown is "
                          f"AMPLIFIED BY CAPITAL STRUCTURE and is not by itself evidence of "
                          f"mispricing. Test the dislocation at the EV level, check whether leverage "
                          f"ROSE through the drawdown, and strip net new borrowing out of any "
                          f"headline FCF. If it survives, gate it on a DATED EVENT — a price gate on "
                          f"a levered stub is a beta-carrier self-trigger.]")
        except Exception:
            out[t] = ("  [LEVERAGE UNCHECKED — lookup failed; do NOT read this as an unlevered name]")
    return out


def sweep(limit: int = BLOB_DAILY) -> dict:
    try:
        blob = json.loads(BLOB_FILE.read_text())
    except Exception:
        return {"skipped": "no discovery_blob.json (no breadth rejection persisted yet)"}
    from desk.court_queue import QUEUE, enqueue_candidates
    seen = {i["ticker"] for i in QUEUE.rows()}
    smed = blob.get("sector_median_dd", {})
    rows = []
    for r in blob.get("members", []):
        if (r.get("mcap") or 0) < MIN_MCAP or r["ticker"] in seen:
            continue
        r["excess_dd"] = round(r["dd52"] - smed.get(r.get("sector") or "", 0.0), 3)
        rows.append(r)
    rows.sort(key=lambda r: r["excess_dd"])                    # most negative excess first
    pick = rows[:limit]
    if not pick:
        return {"blob_date": blob.get("date"), "eligible": 0, "enqueued": 0}
    lev = _leverage_flags(pick)
    res = enqueue_candidates(
        [{**r, "context": f"blob_sweep {blob.get('date')}: dd52 {r['dd52']}, "
                          f"excess vs {r.get('sector')} sector median {r['excess_dd']} — "
                          f"cause-check FIRST, then refutability + court-worthiness score"
                          + lev.get(r["ticker"], "")}
         for r in pick],
        source=f"class_dislocation:blob_sweep/{blob.get('date')}",
        stage="REFUTABILITY", allow_ledger=False)
    return {"blob_date": blob.get("date"), "eligible": len(rows),
            "enqueued": res.get("added", 0), "top": [r["ticker"] for r in pick[:10]]}


if __name__ == "__main__":
    print(json.dumps(sweep(), indent=1))
