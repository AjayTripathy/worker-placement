"""missed_entry_review — grade the desk's SILENCES the way it grades its calls.

RATIFIED 2026-08-21 alongside the clean-court minimum-starter default. The first run of this
review (done by hand that day) found 52 passes against 1 take since 7/15 — and a passed-class
shadow P&L of mean +0.3% / median -0.9%, i.e. a wall that had not yet cost anything. Both facts
mattered: the ratio justified the amendment, the P&L kept it honest. This keeps both measured.

Monthly: re-price every non-buy adjudication at 30/90 days after its verdict. If the passed-class
MEDIAN beats +5% over a quarter, the conservatism bar ratchets DOWN (flag loudly, email); if it
lands negative, the amendment is working as designed and the record says so.

    python3 -m desk.missed_entry_review
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "desk" / "data" / "missed_entry_review.json"
TAKE_WORDS = ("STARTER", "OWN", "BUY", "ACCUMULATE")
PASS_WORDS = ("KILL", "AVOID", "REJECT", "FLAT", "WATCH", "DEFER", "WAIT", "NOT_YET")


def run(since: str = "2026-07-15", verbose: bool = True) -> dict:
    rows = []
    for f in glob.glob(str(ROOT / "desk/data/edge_classifications/*.json")):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        dtv = str(d.get("date", ""))
        if dtv < since or not d.get("ticker"):
            continue
        rec = (str(d.get("recommendation", "")) + " " + str(d.get("ledger_verdict", ""))).upper()
        if any(k in rec for k in TAKE_WORDS) and "NOT" not in rec:
            side = "TOOK"
        elif any(k in rec for k in PASS_WORDS):
            side = "PASSED"
        else:
            continue
        rows.append({"t": d["ticker"], "date": dtv, "side": side, "rec": rec[:60]})

    from desk.broken_print_radar import batch_history
    bars = batch_history(sorted({r["t"] for r in rows}), period="6mo", batch=60,
                         retries=3, pause=1.2, verbose=False)
    res = []
    for r in rows:
        b = bars.get(r["t"])
        if not b:
            res.append({**r, "ret": None, "note": "unpriced"})
            continue
        dts, cl = b["dates"], [c for c in b["close"] if c is not None]
        idx = next((i for i, x in enumerate(dts) if x >= r["date"]), None)
        if idx is None or idx >= len(cl) or len(cl) < 3:
            res.append({**r, "ret": None, "note": "no verdict-date bar"})
            continue
        r2 = {**r, "ret": round(100 * (cl[-1] / cl[idx] - 1), 2)}
        # 30-session mark where history allows
        if idx + 21 < len(cl):
            r2["ret_30s"] = round(100 * (cl[idx + 21] / cl[idx] - 1), 2)
        res.append(r2)

    summary = {}
    for side in ("PASSED", "TOOK"):
        rets = [x["ret"] for x in res if x["side"] == side and x["ret"] is not None]
        if rets:
            summary[side] = {"n": len(rets), "mean": round(statistics.mean(rets), 2),
                             "median": round(statistics.median(rets), 2),
                             "win_rate": round(100 * sum(x > 0 for x in rets) / len(rets))}
    # CONFIRMATION-PREMIUM TRACKING (added 2026-08-21, principal's optimism challenge). Evidence-
    # gated entries pay a premium when right: we enter at the gate-fire price, not the verdict
    # price. That cost was invisible. For every classification carrying a price-above-tape reopen
    # gate (basing gates, post-print adds), record verdict-day price vs gate level; the review
    # reports the premium we have PRE-COMMITTED to paying for confirmation. If the passed-class
    # keeps going nowhere while the premium column grows, the gates are correctly priced insurance;
    # if passes run and we re-enter above, the premium is the measurable cost of misplaced
    # skepticism. Numbers first, doctrine second.
    import re as _re
    premiums = []
    for f2 in glob.glob(str(ROOT / "desk/data/edge_classifications/*.json")):
        try:
            d2 = json.load(open(f2))
        except Exception:
            continue
        px = d2.get("live_px_at_verdict") or d2.get("spot_price")
        if not px:
            continue
        for g in (d2.get("reopen_gates") or []):
            m = _re.search(r"(?:basing|above|>)\s*\$?([0-9]+(?:\.[0-9]+)?)", str(g))
            if m:
                lvl = float(m.group(1))
                if lvl > float(px) * 1.02:
                    premiums.append({"t": d2.get("ticker"), "verdict_px": px, "gate": lvl,
                                     "premium_pct": round(100 * (lvl / float(px) - 1), 1)})
    ratchet = None
    p = summary.get("PASSED", {})
    if p.get("median", 0) > 5.0:
        ratchet = ("RATCHET-DOWN FLAG: passed-class median %+0.1f%% — the bar is too high; "
                   "review the named-kill list and starter sizing." % p["median"])
    payload = {"asof": dt.datetime.utcnow().isoformat() + "Z", "since": since,
               "summary": summary, "ratchet_flag": ratchet,
               "confirmation_premiums": premiums, "rows": res}
    OUT.write_text(json.dumps(payload, indent=1))
    if verbose:
        print(f"[missed_entry_review] since {since}: {json.dumps(summary)}")
        if ratchet:
            print(f"[missed_entry_review] {ratchet}")
    try:
        from desk.mailer import send as msend
        lines = [f"{s}: {json.dumps(v)}" for s, v in summary.items()]
        if ratchet:
            lines.insert(0, ratchet)
        msend("MISSED-ENTRY REVIEW: " + (", ".join(f"{s} med {v['median']:+.1f}%"
              for s, v in summary.items())), [("summary", lines)])
    except Exception as e:
        print(f"[missed_entry_review] mail failed ({e})")
    return payload


if __name__ == "__main__":
    run()
