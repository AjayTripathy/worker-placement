"""sanyu_accumulator — chunked accumulation of 5697.T (Sanyu) sized to the tape, not to a table.

WHY THIS EXISTS (2026-08-20). A foreign agent (antigravity_v2, ~/.gemini) staged this exact name as
a 4-rung GTC ladder with a 700-share top rung — ~8% of a typical day's volume resting visibly at one
price — and transmitted 24 orders across 9 names with prices HARDCODED at code-writing time. At
least one was a row-swap from another name's shelf price (9713 got 6286's ¥1,385), and 800 shares
filled 53% above where the writer thought the tape was. The failure was not the thesis (5697 is
court-ratified STARTER, verification 2026-08-20) and not the data (the July shelf was accurate);
it was an order layer with NO LIVE-TAPE CHECK between a language model's table and the exchange.

THIS SCRIPT IS THE CONTROL THAT WAS MISSING, plus the chunking the position actually needs:
  - Every run FETCHES THE LIVE TAPE (kabutan, full browser fingerprint — the account has no TSE
    market-data entitlement at IBKR, so the quote comes from the public tape) and REFUSES to act
    if the fetch fails, is stale, or the computed limit strays >3% from it. A limit price that
    cannot be tied to today's tape is not an order, it is a guess.
  - ONE day-chunk per session, sized to REAL volume computed at runtime (never hardcoded):
    min(MAX_LOTS_PER_DAY, max(1 lot, PARTICIPATION_CAP of 20d median volume)). At ~9k sh/day
    median that is 100-200 shares — invisible, vs the 700-share rung it replaces.
  - Position-aware: reads the live gateway position and its own state file; stops at TARGET_SH
    including anything the old ladder already filled. Idempotent per Tokyo date.
  - ENVELOPE GATES, all stated here and none overridable by flag: ceiling ¥860 (no chasing the
    thesis away), pause-below ¥770 (a -8% day is a band-touch/dislocation event — those get
    REVIEWED, never bought blind; GILT/NNE/KLAR 2026-08-18), halt on target.

EXECUTION AUTHORITY. Default mode STAGES: prints + emails the day's envelope (qty/limit/rationale)
and writes it to the state file. It places NOTHING. `--execute` places the day's chunk as a live
DAY limit order (board lot, displaySize=100) — that flag is the principal's trigger, run by the
principal or by cron ONLY after the principal edits CRON_MODE below to "execute". The desk does
not pull triggers; it loads them. (transmit=False staging is not usable here: IB Gateway is
headless — a pending-transmit order can never be clicked. The flag IS the click.)

    python3 -m desk.sanyu_accumulator             # stage today's envelope (no orders)
    python3 -m desk.sanyu_accumulator --execute   # place today's chunk (principal's trigger)
    python3 -m desk.sanyu_accumulator --status    # tally
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

STATE = ROOT / "desk" / "data" / "sanyu_accum_state.json"
ATTR = ROOT / "desk" / "data" / "antigravity_attributed_orders.json"  # same attribution ledger

SYMBOL, EXCHANGE, CURRENCY = "5697", "TSEJ", "JPY"
LOT = 100
TARGET_SH = 1400            # ~0.75% sleeve at ¥8xx ≈ $7.4k — the ratified STARTER size
CEILING = 860               # never bid above; tape was 836 at ratification (2026-08-20)
PAUSE_BELOW = 770           # -8%: dislocation -> review, not auto-buy
PARTICIPATION_CAP = 0.02    # of 20d median volume per day
MAX_LOTS_PER_DAY = 2
TAPE_SANITY_PCT = 0.03      # limit must sit within 3% of the live tape — THE missing control
CRON_MODE = "stage"         # principal edits to "execute" to arm the daily trigger

_HDRS = {"User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
         "Accept-Language": "ja,en-US;q=0.9", "Referer": "https://www.google.com/",
         "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "none"}


def _tokyo_today() -> str:
    return dt.datetime.now(ZoneInfo("Asia/Tokyo")).date().isoformat()


def fetch_tape() -> dict:
    """Live-ish price + 20d volume from kabutan. Raises on ANY doubt — no tape, no order."""
    import requests
    r = requests.get(f"https://kabutan.jp/stock/kabuka?code={SYMBOL}", headers=_HDRS, timeout=25)
    if r.status_code != 200:
        raise RuntimeError(f"kabutan {r.status_code} — refusing to price without a tape")
    t = re.sub(r"<[^>]+>", " ", r.text)
    # header carries the live quote; the table carries daily rows: date o h l c chg chg% volume
    m = re.search(r"(\d{2}/\d{2}/\d{2})\s+([\d,]+(?:\.\d)?)\s+[\d,.]+\s+[\d,.]+\s+([\d,]+(?:\.\d)?)"
                  r"\s+[▲△+\-0-9.,]+\s+[+\-0-9.,]+\s+([\d,]+)", t)
    rows = re.findall(r"\d{2}/\d{2}/\d{2}\s+[\d,.]+\s+[\d,.]+\s+[\d,.]+\s+([\d,.]+)"
                      r"\s+[▲△+\-0-9.,]+\s+[+\-0-9.,]+\s+([\d,]+)", t)
    if not rows:
        raise RuntimeError("kabutan table parse failed — refusing to price without a tape")
    closes = [float(c.replace(",", "")) for c, _ in rows[:20]]
    vols = sorted(int(v.replace(",", "")) for _, v in rows[:20])
    live = re.search(r"kabuka\">([0-9,]+(?:\.[0-9]+)?)円", r.text)
    px = float(live.group(1).replace(",", "")) if live else closes[0]
    return {"px": px, "prev_close": closes[0], "median20_vol": vols[len(vols) // 2],
            "asof_row": m.group(1) if m else rows[0], "fetched_utc": dt.datetime.utcnow().isoformat() + "Z"}


def gateway_position() -> int | None:
    """Filled shares per the gateway; None (loud) if unreachable — never silently zero."""
    try:
        from ib_insync import IB
        ib = IB(); ib.connect("127.0.0.1", 4001, clientId=61, timeout=8, readonly=True)
        try:
            for p in ib.positions():
                if p.contract.symbol == SYMBOL and p.contract.currency == CURRENCY:
                    return int(p.position)
            return 0
        finally:
            ib.disconnect()
    except Exception:
        return None


def _state() -> dict:
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {"chunks": [], "halted": None}



def _session_open() -> bool:
    """Tokyo cash session, with margin: 08:00-15:25 JST weekdays. Placing OUTSIDE it queues a DAY
    order into the NEXT session while state stamps TODAY's date — and the next morning's run then
    stages a fresh chunk for the new date: two chunks working one session. Refuse instead."""
    now = dt.datetime.now(ZoneInfo("Asia/Tokyo"))
    return now.weekday() < 5 and (8, 0) <= (now.hour, now.minute) < (15, 25)


def plan_chunk() -> dict:
    tape = fetch_tape()
    st = _state()
    today = _tokyo_today()
    if st.get("halted"):
        return {"action": "HALTED", "why": st["halted"], "tape": tape}
    # A chunk staged today but NOT executed is a live envelope, not a duplicate: --execute must be
    # able to consume it (re-priced against the CURRENT tape below, never the morning's). Only an
    # already-EXECUTED chunk blocks the day.
    if any(c["tokyo_date"] == today and c.get("executed") for c in st["chunks"]):
        return {"action": "ALREADY_EXECUTED_TODAY", "tape": tape}
    # UNRESOLVED PLACEMENT TOMBSTONE. The tombstone is written to disk BEFORE placeOrder and
    # resolved after. If one is still open, a prior run died mid-placement — the order may be LIVE
    # at the broker while this state file never learned of it. Re-placing would double-buy; the
    # only safe move is a human check of open orders, then clearing the tombstone.
    stuck = [c for c in st["chunks"] if c["tokyo_date"] == today and c.get("placing")]
    if stuck:
        return {"action": "VERIFY_BROKER", "why": ("a placement attempt today never resolved "
                "(process died between placeOrder and state write). CHECK OPEN ORDERS at the "
                "broker for orderRef SANYU-ACCUM before re-running; then set 'placing': false on "
                f"the stuck record in {STATE.name}"), "tape": tape}

    pos = gateway_position()
    held = pos if pos is not None else sum(c.get("qty", 0) for c in st["chunks"] if c.get("executed"))
    if pos is None:
        note = "GATEWAY UNREACHABLE — using state-file tally; verify position before executing"
    else:
        note = f"gateway position {pos}"
    if held >= TARGET_SH:
        return {"action": "TARGET_REACHED", "held": held, "tape": tape}

    px = tape["px"]
    if px < PAUSE_BELOW:
        return {"action": "PAUSED_DISLOCATION", "why": f"tape {px} < {PAUSE_BELOW} — a -8% move is a "
                "review event (news/court re-check), never an auto-buy", "tape": tape}
    if px > CEILING:
        return {"action": "PAUSED_ABOVE_CEILING", "why": f"tape {px} > {CEILING}", "tape": tape}

    lots = max(1, min(MAX_LOTS_PER_DAY, int(tape["median20_vol"] * PARTICIPATION_CAP / LOT)))
    qty = min(lots * LOT, ((TARGET_SH - held) // LOT) * LOT or LOT)
    limit = min(int(min(px, tape["prev_close"])), CEILING)   # passive at tape, ¥1 tick
    if abs(limit - px) / px > TAPE_SANITY_PCT:               # THE control the old stager lacked
        return {"action": "REFUSED_TAPE_SANITY", "why": f"limit {limit} strays >{TAPE_SANITY_PCT:.0%} "
                f"from tape {px}", "tape": tape}
    return {"action": "CHUNK", "qty": qty, "limit": limit, "tif": "DAY", "held": held,
            "remaining_after": TARGET_SH - held - qty, "participation": qty / tape["median20_vol"],
            "position_note": note, "tape": tape}


def run(execute: bool = False) -> dict:
    plan = plan_chunk()
    st = _state(); today = _tokyo_today()
    if plan["action"] != "CHUNK":
        print(f"[sanyu_accumulator] {plan['action']}: {plan.get('why','')}")
        return plan

    rec = {"tokyo_date": today, "qty": plan["qty"], "limit": plan["limit"], "tif": "DAY",
           "staged": True, "executed": False, "tape_px": plan["tape"]["px"],
           "participation": round(plan["participation"], 4), "ts": dt.datetime.utcnow().isoformat() + "Z"}

    if execute and not _session_open():
        print("[sanyu_accumulator] SESSION_CLOSED — Tokyo cash session is 09:00-15:30 JST; run during "
              "08:00-15:25 JST or let the morning cadence handle it. Placing now would double-chunk "
              "tomorrow's session.")
        return {**plan, "action": "SESSION_CLOSED"}
    if execute:
        # Tombstone ON DISK before the broker sees anything: if we die mid-placement, the next run
        # refuses with VERIFY_BROKER instead of silently double-buying.
        rec["placing"] = True
        st["chunks"].append(rec)
        STATE.write_text(json.dumps(st, indent=1))
        from ib_insync import IB, Stock, LimitOrder
        from desk.account_registry import require_alpha
        ib = IB(); ib.connect("127.0.0.1", 4001, timeout=10, clientId=62)
        try:
            # Two managed accounts since BETA (ACCOUNT_BETA) appeared in the login: an account-less
            # order dies with Error 435 (first live failure 2026-08-24 08:49 JST). Pin ALPHA.
            acct = require_alpha(ib)
            # SMART + primaryExchange, NOT direct exchange routing: the Gateway's API
            # Precautionary Settings discard direct-routed orders (Error 10311 -> Error 201
            # "Order was discarded", first live attempt 2026-08-21 12:29 JST). SMART routing with
            # primaryExchange=TSEJ is the proven path on this account.
            c = Stock(symbol=SYMBOL, exchange="SMART", currency=CURRENCY, primaryExchange=EXCHANGE)
            ib.qualifyContracts(c)
            o = LimitOrder("BUY", rec["qty"], rec["limit"], tif="DAY", outsideRth=False)
            o.displaySize = LOT
            o.orderRef = "SANYU-ACCUM"
            o.account = acct
            tr = ib.placeOrder(c, o); ib.sleep(3)
            status = tr.orderStatus.status
            # The broker's reason travels in trade.log — without it a Cancelled order is a mute
            # failure (learned 2026-08-21: first live chunk came back 'Cancelled' with no reason
            # recorded, placed at 12:04 JST — inside the Tokyo lunch break).
            rec.update(order_id=tr.order.orderId, status=status,
                       broker_log=[l.message for l in tr.log if l.message][-4:])
            # Only a LIVE or FILLED order counts as the day's execution. A Cancelled/Inactive one
            # must NOT burn the one-execution-per-day slot, or a transient reject locks the day.
            rec["executed"] = status in ("Submitted", "PreSubmitted", "PendingSubmit", "Filled")
            if not rec["executed"]:
                print(f"[sanyu_accumulator] ORDER NOT LIVE — status {status}; "
                      f"broker log: {rec['broker_log']}")
        finally:
            ib.disconnect()
            rec["placing"] = False                      # tombstone resolved, whatever the outcome
            STATE.write_text(json.dumps(st, indent=1))
        try:
            led = json.loads(ATTR.read_text()) if ATTR.exists() else []
            led.append({**rec, "cohort": "sanyu_accumulator", "agent_origin": "signalos_desk",
                        "ticker": "5697.T", "action": "BUY"})
            ATTR.write_text(json.dumps(led, indent=2))
        except Exception:
            pass
    else:
        st["chunks"].append(rec)

    STATE.write_text(json.dumps(st, indent=1))

    # Report the OUTCOME, not the intent: the first live failure printed "EXECUTED" for an order
    # the broker had just discarded, because this line keyed on the execute FLAG.
    mode = ("EXECUTED" if rec.get("executed") else
            f"PLACEMENT FAILED ({rec.get('status','?')} — see broker_log)" if execute else
            "STAGED (no order placed — run --execute to place)")
    filled_so_far = plan["held"]
    msg = (f"5697.T Sanyu day-chunk {mode}: BUY {rec['qty']} @ ¥{rec['limit']} DAY "
           f"({rec['participation']:.1%} of 20d median volume). Held {filled_so_far}, "
           f"target {TARGET_SH}, remaining after this {plan['remaining_after']}. "
           f"Tape ¥{plan['tape']['px']} ({plan['position_note']}). Ceiling {CEILING} / pause {PAUSE_BELOW}.")
    print(f"[sanyu_accumulator] {msg}")
    try:
        from desk.mailer import send as msend
        msend(f"SANYU ACCUM {mode.split()[0]}: {rec['qty']} @ {rec['limit']}", [("envelope", [msg])])
    except Exception as e:
        print(f"[sanyu_accumulator] mail failed ({e}) — envelope above is authoritative")
    return {**plan, "record": rec}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="place today's chunk (principal's trigger)")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    if a.status:
        print(json.dumps(_state(), indent=1))
    else:
        run(execute=a.execute)
