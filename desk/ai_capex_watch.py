"""ai_capex_watch — tripwires 1+2 of the AI-capex break model (desk/models/ai_capex_break.py).

Tripwire 1 — THE CLOCK-STARTER (realized capex acceleration): quarterly capex for the five
hyperscalers (MSFT GOOGL AMZN META ORCL) from reported cashflow statements. Signal series =
aggregate single-quarter capex YoY growth g(q), and its delta a(q) = g(q) - g(q-1), computed
on REALIZED data only (the model's measurement rule: consensus acceleration is a forecast
artifact — analysts under-extrapolate in booms). RED = a(q) < 0 for 2 consecutive quarters
-> the 2008-mapped hazard clock starts (borrower stress ~4-6q later).

Tripwire 2 — THE NASH FLIP (Gate B): on each hyperscaler's earnings day this watch emails a
guide-check reminder; the capex-guide DIRECTION needs a human/agent read of the call, logged
with:  python3 -m desk.ai_capex_watch guide TICKER up|flat|down [note]
On a logged guide-DOWN it computes the same-day tape reaction (stock vs SPY): a REWARDED
guide-down (outperformance) = GATE B FIRED — the moment capex stops being a call option —
and sends a loud email. Until Gate B fires, near-term break probability stays LOW no matter
what the narrative says.

yfinance serves only ~5-6 quarters, so the state file ACCUMULATES realized quarters across
runs; the acceleration series self-extends. INSUFFICIENT_HISTORY is reported, never guessed.

    python3 -m desk.ai_capex_watch            # daily run (registry)
    python3 -m desk.ai_capex_watch guide MSFT down "cut FY27 capex guide on the call"
READ-ONLY on markets.
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "desk" / "data" / "ai_capex_watch_state.json"

HYPERSCALERS = ["MSFT", "GOOGL", "AMZN", "META", "ORCL"]


def _load():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"capex_bn": {}, "guides": [], "alerted": {}, "_doctrine":
            "tripwires 1+2 of desk/models/ai_capex_break.py; capex_bn accumulates realized quarters"}


def _save(d):
    STATE.write_text(json.dumps(d, indent=1))


def _pull_capex(state) -> list[str]:
    """Merge newly-reported quarters into the accumulated per-name series. Never overwrite
    an existing quarter (realized data is immutable); log restatements instead."""
    import yfinance as yf
    notes = []
    for t in HYPERSCALERS:
        try:
            cf = yf.Ticker(t).quarterly_cashflow
            row = None
            for label in ("Capital Expenditure", "Capital Expenditures"):
                if label in cf.index:
                    row = cf.loc[label]
                    break
            if row is None:
                notes.append(f"{t}: no capex row")
                continue
            book = state["capex_bn"].setdefault(t, {})
            for ts, v in row.items():
                if v != v or v is None:      # NaN
                    continue
                q = str(ts.date())
                bn = round(abs(float(v)) / 1e9, 2)
                if q not in book:
                    book[q] = bn
                    notes.append(f"{t}: NEW quarter {q} capex ${bn}B")
                elif abs(book[q] - bn) > 0.5:
                    notes.append(f"{t}: RESTATED {q} {book[q]} -> {bn} (kept original)")
        except Exception as e:
            notes.append(f"{t}: DATA MISSING ({type(e).__name__})")
    return notes


def _signal(state):
    """Aggregate quarters where ALL five reported; YoY growth + acceleration on that series."""
    books = state["capex_bn"]
    if len(books) < len(HYPERSCALERS):
        return {"status": "INSUFFICIENT_HISTORY", "detail": f"only {len(books)}/5 names have data"}
    # RANK alignment, newest first: ORCL's Feb/May/Aug/Nov fiscal ends never share a calendar
    # month with the other four, so exact-month bucketing yields zero complete quarters. A
    # ±1-month offset is immaterial to a YoY-acceleration signal; label buckets by median date.
    series = {t: sorted(books[t].items(), reverse=True) for t in HYPERSCALERS}
    depth = min(len(s) for s in series.values())
    full = {}
    for r in range(depth - 1, -1, -1):
        qs = [series[t][r] for t in HYPERSCALERS]
        label = sorted(q for q, _ in qs)[2]          # median quarter-end as the bucket name
        full[label] = round(sum(v for _, v in qs), 1)
    full = dict(sorted(full.items()))
    buckets = list(full)
    if len(buckets) < 6:
        return {"status": "INSUFFICIENT_HISTORY",
                "detail": f"{len(buckets)} complete quarters accumulated; need 6 for an accel pair "
                          f"(series self-extends each quarter)", "aggregate_bn": full}
    g = {}
    for i, b in enumerate(buckets):
        if i >= 4:
            prev = full[buckets[i - 4]]
            g[b] = round(100 * (full[b] / prev - 1), 1)
    gb = list(g)
    a = {b: round(g[b] - g[gb[i - 1]], 1) for i, b in enumerate(gb) if i >= 1}
    ab = list(a)
    red = len(ab) >= 2 and a[ab[-1]] < 0 and a[ab[-2]] < 0
    return {"status": "RED_CLOCK_STARTED" if red else "GREEN",
            "aggregate_bn": full, "yoy_growth_pct": g, "accel_pp": a}


def _earnings_reminders(state):
    """Names printing today/tomorrow -> guide-check reminder lines."""
    import yfinance as yf
    today = datetime.date.today()
    due = []
    for t in HYPERSCALERS:
        try:
            cal = yf.Ticker(t).calendar
            dates = cal.get("Earnings Date") if isinstance(cal, dict) else None
            for d in dates or []:
                d = d if isinstance(d, datetime.date) else getattr(d, "date", lambda: None)()
                if d and 0 <= (d - today).days <= 1:
                    due.append(t)
                    break
        except Exception:
            pass
    return sorted(set(due))


def _mail(subject, sections, footer=None):
    try:
        from desk.mailer import send
        send(subject, sections, footer=footer)
    except Exception as e:
        print(f"[ai_capex_watch] mail failed: {e}")


def guide(ticker: str, direction: str, note: str = ""):
    """Log a capex guide direction; on 'down', run the Nash-flip event study."""
    assert direction in ("up", "flat", "down")
    state = _load()
    today = datetime.date.today().isoformat()
    entry = {"date": today, "ticker": ticker.upper(), "direction": direction, "note": note}
    if direction == "down":
        try:
            import yfinance as yf
            px = yf.download([ticker.upper(), "SPY"], period="5d", progress=False)["Close"]
            r = px.pct_change().iloc[-1]
            rel = round(100 * (r[ticker.upper()] - r["SPY"]), 2)
            entry["same_day_rel_spy_pct"] = rel
            entry["nash_flip"] = bool(rel > 0)
            if rel > 0:
                _mail(f"GATE B FIRED — {ticker.upper()} capex guide-down REWARDED (+{rel}pp vs SPY)",
                      [("What happened", [f"{ticker.upper()} guided capex DOWN and OUTPERFORMED SPY by {rel}pp same-day.",
                                          f"Analyst note: {note}" if note else ""]),
                       ("Why this matters", ["The Nash flip: the market now rewards NOT spending. Per the break model, "
                                             "this is the regime inversion that stalls the capex cycle — the clock "
                                             "accelerates and every AI-complex exposure needs a size review."]),
                       ("Model", ["desk/models/ai_capex_break.py — re-run and re-freeze the scenario tree."])])
        except Exception as e:
            entry["event_study"] = f"failed ({type(e).__name__}) — run manually"
    state["guides"].append(entry)
    _save(state)
    print(f"[ai_capex_watch] guide logged: {entry}")


def main():
    state = _load()
    notes = _pull_capex(state)
    sig = _signal(state)
    due = _earnings_reminders(state)
    today = datetime.date.today().isoformat()

    if due and state["alerted"].get(f"earnings:{today}") != due:
        state["alerted"][f"earnings:{today}"] = due
        _mail(f"AI-capex guide check due: {', '.join(due)} print today/tomorrow",
              [("What to do", [f"{t}: after the call, log the capex-guide direction with "
                               f"`python3 -m desk.ai_capex_watch guide {t} up|flat|down \"note\"`" for t in due]),
               ("Why", ["Tripwire 2 of the AI-capex break model: the first guide-DOWN the tape "
                        "rewards flips the Nash equilibrium (Gate B). Guides still rising = loop intact."])])
    if sig["status"] == "RED_CLOCK_STARTED" and not state["alerted"].get("red_clock"):
        state["alerted"]["red_clock"] = today
        _mail("RED — realized hyperscaler capex acceleration negative 2 consecutive quarters",
              [("The signal", [f"accel series (pp): {sig['accel_pp']}",
                               f"growth series (%): {sig['yoy_growth_pct']}"]),
               ("What it means", ["The break-model clock STARTS: 2008 mapping puts borrower stress "
                                  "~4-6 quarters out. Re-run desk/models/ai_capex_break.py; review "
                                  "AI-complex sizing (household beta, Parametric tech, GOOGL, semis)."])])

    _save(state)
    print(f"[ai_capex_watch] {today}: signal={sig['status']}"
          + (f" | earnings due: {', '.join(due)}" if due else "")
          + (f" | {len([n for n in notes if 'NEW' in n])} new quarters" if notes else ""))
    for n in notes:
        print(f"  {n}")
    if sig.get("accel_pp"):
        print(f"  growth% {sig['yoy_growth_pct']}")
        print(f"  accel pp {sig['accel_pp']}")
    elif sig["status"] == "INSUFFICIENT_HISTORY":
        print(f"  {sig['detail']}")
    if state["guides"]:
        g = state["guides"][-1]
        print(f"  last guide logged: {g['ticker']} {g['direction']} ({g['date']})")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "guide":
        guide(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "flat",
              " ".join(sys.argv[4:]))
    else:
        main()
