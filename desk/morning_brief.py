"""morning_brief — the desk's daily on-deck digest, in plain analyst language.

Born 2026-07-09 (user: "give me everything on deck for tomorrow in plain analyst
language... then starting tomorrow I want that in an email"). Runs pre-open each
weekday. AUTO-DERIVES from the live desk state so it never goes stale:

  1. ACTIONS/DECISIONS — resting orders sitting near the live tape (could fill
     today), ledger alert levels within reach, active event-windows with an
     action, + hand-curated judgment items (desk/data/on_deck_manual.json).
  2. CATALYSTS LANDING — frozen calibration calls whose grade date is within the
     next 8 days (what prints this week), with our probability + plain read.
  3. ON THE HORIZON — the 9-21 day catalyst queue, one line each.
  4. STANDING — MFT forward-test grades + backtest/self-audit dates due soon.

Plain language ONLY — no R/f(M), no detector jargon (reports-keep-the-discipline-
drop-the-jargon). READ-ONLY: reports state, never trades, never restages.

    python3 -m desk.morning_brief            # prints the brief
    python3 -m desk.morning_brief --email    # prints AND emails it
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "desk" / "data"
NEAR_PCT = 3.0            # a resting buy within this % below the tape = "could fill"
LAND_DAYS = 8            # "this week" horizon for catalysts
HORIZON_DAYS = 21        # "on the horizon" queue


def _load(p, default=None):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return default if default is not None else {}


def _jsonl(p):
    out = []
    fp = Path(p)
    if fp.exists():
        for line in fp.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def _live_px():
    """Freshest live quotes from the daemon file (US names); tolerate staleness."""
    q = _load(D / "ib_live_quotes.json", {})
    px = {}
    for k, v in (q.get("quotes") or {}).items():
        if isinstance(v, dict) and v.get("px"):
            px[k.split()[0]] = float(v["px"])
    age_min = None
    if q.get("asof"):
        age_min = (datetime.datetime.now().timestamp() - q["asof"]) / 60
    return px, age_min


def _clean_dir(s):
    """Strip the gate jargon out of a frozen-call direction into a plain phrase."""
    if not s:
        return ""
    s = s.split("(")[0]
    for pre in ("FAVORABLE =", "FAVORABLE=", "FAVORABLE"):
        if s.strip().startswith(pre):
            s = s.strip()[len(pre):]
            break
    return s.replace("_", " ").strip(" =")


def build(today: datetime.date | None = None) -> str:
    today = today or datetime.date.today()
    px, age = _live_px()
    L = []
    def line(s=""):
        L.append(s)

    dow = today.strftime("%A")
    line(f"SIGNALOS — ON DECK for {dow} {today.isoformat()}")
    line("=" * 58)

    # ---------- 0. ARMED CATALYST ACTIONS (highest priority — a graded call's pre-registered
    # action is live and on an execution SLA; MFT edge decays with latency) ----------
    try:
        from desk.catalyst_action import pending as _pending
        armed = _pending()
    except Exception:
        armed = []
    if armed:
        line("\n■ ⚡ ARMED — PRE-REGISTERED ACTIONS (execute or stand down)")
        for a in armed:
            gtag = " · PROVISIONAL grade (unconfirmed)" if a.get("grade_status") == "PROPOSED" else ""
            anc = f" · anchor {a.get('anchor')}" if a.get("anchor") else ""
            line(f"• {a['ticker']} → {a['do']} ({a.get('outcome')}{gtag}, SLA {a.get('sla_min')}m{anc})")
            line(f"    {str(a.get('plan',''))[:200]}")

    # ---------- 1. ACTIONS / DECISIONS ----------
    line("\n■ ACTIONS & DECISIONS")
    actions = []

    # resting orders near the tape
    oc = _load(D.parent / "ui" / "data" / "orders_cache.json", {})
    for o in oc.get("orders", []):
        sym = str(o.get("symbol", "")).split(".")[0].split()[0]
        lim = o.get("limit")
        if not lim or sym not in px:
            continue
        p = px[sym]
        gap = (p / float(lim) - 1) * 100      # how far the tape sits ABOVE our buy
        if -1.0 <= gap <= NEAR_PCT:
            actions.append(f"• {sym}: tape {p:.2f} is ~{gap:+.1f}% vs your resting buy {lim} — could fill today; decide if the rung still stands.")

    # active event windows
    ew = _load(D / "event_windows.json", {})
    for w in ew.get("windows", []):
        if w.get("start", "9") <= today.isoformat() <= w.get("end", "0"):
            sym = w.get("symbol", "")
            tag = f" (tape {px[sym]:.2f})" if sym in px else ""
            actions.append(f"• {sym}{tag} — {w.get('name')}: {w.get('action','review the pre-registration')}")

    # ledger alert levels within reach
    led = _load(D / "research_ledger.json", {})
    for n in led.get("names", []):
        sym = n.get("ticker"); ab = n.get("alert_below")
        if not (sym and ab and sym in px):
            continue
        p = px[sym]
        if p <= float(ab) * (1 + NEAR_PCT / 100) and p >= float(ab) * 0.90:
            actions.append(f"• {sym}: tape {p:.2f} is near your {ab} action line — {(n.get('verdict') or '').upper()}.")

    # headless-graded prints awaiting your confirm (read by intelligence, not yet written)
    for p in _load(D / "pending_grades.json", {}).get("proposals", []):
        if p.get("status") == "AWAITING_CONFIRM":
            fp = p.get("first_pass") or {}
            if p.get("disagreement"):
                flag = (f"⚠ MODELS DISAGREED — sonnet said {fp.get('outcome')}, opus said {p.get('proposed_outcome')}; READ before confirming. ")
            elif p.get("escalated") is True:
                flag = "(escalated to opus) "
            else:
                flag = ""
            actions.append(f"• [GRADE READY] {flag}{p['ticker']} ({p['cat_date']}): proposes "
                           f"{p.get('proposed_outcome')} (conf {p.get('confidence')}) — {p.get('number','')}. "
                           f"Confirm: python3 -m desk.headless_grader --confirm {p['ticker']} {p['cat_date']}")

    # hand-curated judgment items
    for it in _load(D / "on_deck_manual.json", {}).get("items", []):
        actions.append(f"• [{it.get('tag','NOTE')}] {it.get('text','')}")

    if actions:
        for a in actions:
            line(a)
    else:
        line("• Nothing at a decision line today. Bids resting, watches armed.")

    # ---------- 2. CATALYSTS LANDING (this week) ----------
    cal = _jsonl(D / "calibration_ledger.jsonl")
    # de-dup to the latest record per (ticker, cat_date)
    seen = {}
    for r in cal:
        if (r.get("status") or "OPEN").upper() != "OPEN":
            continue
        cd = r.get("cat_date")
        if not cd:
            continue
        try:
            d = datetime.date.fromisoformat(cd)
        except Exception:
            continue
        seen[(r.get("ticker"), cd)] = (d, r)
    dated = sorted(seen.values(), key=lambda x: x[0])

    # LANDED — AWAITING GRADE: cat_date has PASSED but the call is still OPEN. This is the
    # gap that made a printed catalyst read as "hasn't happened" (BKE June comp, 2026-07-09):
    # the brief keys off call status, so a print that landed but wasn't auto-graded kept
    # showing as pending — and once its date slipped into the past it dropped out of the
    # windows below entirely. Surface it FIRST and loudly so grading gets closed.
    overdue_open = [(d, r) for d, r in dated if d < today and (today - d).days <= 45]
    if overdue_open:
        line("\n■ ⚠ LANDED — AWAITING GRADE (print date passed, call still OPEN — grade & resolve)")
        for d, r in sorted(overdue_open, key=lambda x: x[0]):   # tuples tie-break on dicts -> TypeError (crashed 9/9)
            ago = (today - d).days
            p = r.get("our_p")
            pd = f"our call {int(round(p*100))}%" if isinstance(p, (int, float)) else ""
            line(f"• {d.isoformat()} ({ago}d ago) {r.get('ticker')}: PRINTED — "
                 f"python3 -m desk.grade_brief --due  [{pd}]")

    landing = [(d, r) for d, r in dated if today <= d <= today + datetime.timedelta(days=LAND_DAYS)]
    line("\n■ CATALYSTS LANDING (next %d days)" % LAND_DAYS)
    if landing:
        for d, r in landing:
            days = (d - today).days
            when = "TODAY" if days == 0 else ("tomorrow" if days == 1 else f"in {days}d")
            p = r.get("our_p")
            pd = f"our call {int(round(p*100))}%" if isinstance(p, (int, float)) else ""
            line(f"• {d.isoformat()} ({when}) {r.get('ticker')}: {_clean_dir(r.get('direction'))[:95]}  [{pd}]")
    else:
        line("• Nothing frozen to grade this week.")

    # ---------- 3. ON THE HORIZON ----------
    horizon = [(d, r) for d, r in dated
               if today + datetime.timedelta(days=LAND_DAYS) < d <= today + datetime.timedelta(days=HORIZON_DAYS)]
    if horizon:
        line("\n■ ON THE HORIZON (%d–%d days)" % (LAND_DAYS + 1, HORIZON_DAYS))
        CAP = 12
        for d, r in horizon[:CAP]:
            line(f"• {d.isoformat()} {r.get('ticker')}: {_clean_dir(r.get('direction'))[:70]}")
        if len(horizon) > CAP:
            line(f"• …+{len(horizon) - CAP} more in the 3-week queue (full list on the dashboard).")

    # ---------- 4. STANDING ----------
    standing = []
    for d, r in dated:
        tk = str(r.get("ticker", ""))
        if tk in ("BOOK-SHARPE", "HONESTY-BACKTEST") and d <= today + datetime.timedelta(days=HORIZON_DAYS):
            days = (d - today).days
            standing.append(f"• {d.isoformat()} ({days}d) self-audit: {tk} — {_clean_dir(r.get('direction'))[:70]}")
    for r in _jsonl(D / "mft_forward_ledger.jsonl"):
        gd = r.get("grade_date") or r.get("cat_date")
        if gd:
            try:
                d = datetime.date.fromisoformat(gd)
                if today <= d <= today + datetime.timedelta(days=HORIZON_DAYS):
                    standing.append(f"• {gd} MFT forward-test grade: {r.get('ticker')}")
            except Exception:
                pass
    if standing:
        line("\n■ STANDING / SELF-AUDIT")
        for s in standing:
            line(s)

    if age is not None and age > 60:
        line(f"\n(note: live quotes were {age:.0f} min stale at build — order-proximity flags may lag)")
    line("\n— desk/morning_brief · read-only · reply to steer")
    return "\n".join(L)


def _email(body: str, day: datetime.date, nightly: bool = False):
    try:
        from desk.mailer import send_raw
        subj = (f"SignalOS — todos for tomorrow ({day.strftime('%a %b %d')})" if nightly
                else f"SignalOS — on deck {day.strftime('%a %b %d')}")
        if send_raw(subj, body):     # mono HTML part keeps the columns aligned in Gmail
            print("[morning_brief] emailed")
        else:
            print("[morning_brief] no SMTP credential — printed only")
    except Exception as e:
        print(f"[morning_brief] email failed: {e}")


def main():
    nightly = "--nightly" in sys.argv           # evening run: build TOMORROW's todos
    day = datetime.date.today() + datetime.timedelta(days=1) if nightly else datetime.date.today()
    body = build(day)
    if nightly:
        body = "TONIGHT'S PREP — your todos for tomorrow:\n" + body
    print(body)
    if "--email" in sys.argv:
        _email(body, day, nightly)


if __name__ == "__main__":
    main()
