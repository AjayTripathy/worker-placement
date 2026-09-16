"""jp_accum_core — shared engine for Japanese chunked-accumulation envelopes.

Generalizes desk/sanyu_accumulator.py (the proven first envelope: staged, gated, filled 100 @ 825
on 2026-08-21) so that new court-ratified names ship as thin config wrappers instead of copied
logic. Every control that episode earned is preserved verbatim:

  - LIVE TAPE EVERY RUN (kabutan, browser fingerprint; no TSE entitlement at IBKR) with a hard
    refusal if the fetch fails or the limit strays >TAPE_SANITY from it;
  - chunks sized at runtime to real 20d median volume, board lots, DAY orders only, one execution
    per Tokyo date, displaySize=lot;
  - ceiling / pause-below / target gates in code, never overridable by flag;
  - SMART + primaryExchange routing (Gateway precautions discard direct-routed API orders, 10311);
  - pre-placement tombstone on disk -> VERIFY_BROKER refusal if a run ever dies mid-place;
  - Cancelled orders release the day's slot and carry the broker's own log message;
  - outcome-truthful reporting and attribution-ledger entries.

CONTEXT FOR THE NEW ENVELOPES (2026-08-21): the principal ratified the CLEAN-COURT MINIMUM-STARTER
default — a court whose findings are all risk/timing-class (no data-integrity kill, no valuation
kill) now defaults to a 0.25-0.5% starter inside an envelope, not FLAT. 7239/2819/4625 are the
first three names staged under it. See memory: feedback_clean_court_minimum_starter_default.

sanyu_accumulator remains standalone (it is live and filling); it should migrate here once its
campaign completes rather than mid-flight.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ATTR = ROOT / "desk" / "data" / "antigravity_attributed_orders.json"
_HDRS = {"User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"),
         "Accept-Language": "ja,en-US;q=0.9", "Referer": "https://www.google.com/",
         "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "none"}


def _today() -> str:
    return dt.datetime.now(ZoneInfo("Asia/Tokyo")).date().isoformat()


def fetch_tape(code: str) -> dict:
    import requests
    r = requests.get(f"https://kabutan.jp/stock/kabuka?code={code}", headers=_HDRS, timeout=25)
    if r.status_code != 200:
        raise RuntimeError(f"kabutan {r.status_code} — refusing to price without a tape")
    live = re.search(r'kabuka">([0-9,]+(?:\.[0-9]+)?)円', r.text)
    t = re.sub(r"<[^>]+>", " ", r.text)
    rows = re.findall(r"\d{2}/\d{2}/\d{2}\s+[\d,.]+\s+[\d,.]+\s+[\d,.]+\s+([\d,.]+)"
                      r"\s+[▲△+\-0-9.,]+\s+[+\-0-9.,]+\s+([\d,]+)", t)
    if not rows:
        raise RuntimeError("kabutan table parse failed — refusing to price without a tape")
    closes = [float(c.replace(",", "")) for c, _ in rows[:20]]
    vols = sorted(int(v.replace(",", "")) for _, v in rows[:20])
    px = float(live.group(1).replace(",", "")) if live else closes[0]
    return {"px": px, "prev_close": closes[0], "median20_vol": vols[len(vols) // 2],
            "fetched_utc": dt.datetime.utcnow().isoformat() + "Z"}


def gateway_position(symbol: str) -> int | None:
    try:
        from ib_insync import IB
        ib = IB(); ib.connect("127.0.0.1", 4001, clientId=64, timeout=8, readonly=True)
        try:
            for p in ib.positions():
                if p.contract.symbol == symbol and p.contract.currency == "JPY":
                    return int(p.position)
            return 0
        finally:
            ib.disconnect()
    except Exception:
        return None



def _session_open() -> bool:
    """Tokyo cash session, with margin: 08:00-15:25 JST weekdays. Placing OUTSIDE it queues a DAY
    order into the NEXT session while state stamps TODAY's date — and the next morning's run then
    stages a fresh chunk for the new date: two chunks working one session. Refuse instead."""
    now = dt.datetime.now(ZoneInfo("Asia/Tokyo"))
    return now.weekday() < 5 and (8, 0) <= (now.hour, now.minute) < (15, 25)


def build(cfg: dict):
    """Returns (run, plan_chunk) closures for one envelope config.

    cfg keys: symbol, ticker, target_sh, ceiling, pause_below, state_file,
              lot=100, participation=0.02, max_lots=2, tape_sanity=0.03, client_id=65
    """
    state_path = ROOT / "desk" / "data" / cfg["state_file"]
    LOT = cfg.get("lot", 100)

    def _state() -> dict:
        try:
            return json.loads(state_path.read_text())
        except Exception:
            return {"chunks": [], "halted": None}

    def plan_chunk() -> dict:
        tape = fetch_tape(cfg["symbol"])
        st = _state(); today = _today()
        if st.get("halted"):
            return {"action": "HALTED", "why": st["halted"], "tape": tape}
        if any(c["tokyo_date"] == today and c.get("executed") for c in st["chunks"]):
            return {"action": "ALREADY_EXECUTED_TODAY", "tape": tape}
        if any(c["tokyo_date"] == today and c.get("placing") for c in st["chunks"]):
            return {"action": "VERIFY_BROKER", "why": ("a placement attempt today never resolved — "
                    f"check open orders (orderRef {cfg['ticker']}-ACCUM) then clear 'placing' in "
                    f"{state_path.name}"), "tape": tape}
        pos = gateway_position(cfg["symbol"])
        held = pos if pos is not None else sum(c.get("qty", 0) for c in st["chunks"] if c.get("executed"))
        note = f"gateway position {pos}" if pos is not None else \
               "GATEWAY UNREACHABLE — state-file tally; verify before executing"
        if held >= cfg["target_sh"]:
            return {"action": "TARGET_REACHED", "held": held, "tape": tape}
        px = tape["px"]
        if px < cfg["pause_below"]:
            return {"action": "PAUSED_DISLOCATION", "why": f"tape {px} < {cfg['pause_below']} — "
                    "review event, never an auto-buy", "tape": tape}
        if px > cfg["ceiling"]:
            return {"action": "PAUSED_ABOVE_CEILING", "why": f"tape {px} > {cfg['ceiling']}", "tape": tape}
        lots = max(1, min(cfg.get("max_lots", 2),
                          int(tape["median20_vol"] * cfg.get("participation", 0.02) / LOT)))
        qty = min(lots * LOT, ((cfg["target_sh"] - held) // LOT) * LOT or LOT)
        limit = min(int(min(px, tape["prev_close"])), cfg["ceiling"])
        if abs(limit - px) / px > cfg.get("tape_sanity", 0.03):
            return {"action": "REFUSED_TAPE_SANITY",
                    "why": f"limit {limit} strays >3% from tape {px}", "tape": tape}
        return {"action": "CHUNK", "qty": qty, "limit": limit, "tif": "DAY", "held": held,
                "remaining_after": cfg["target_sh"] - held - qty,
                "participation": qty / tape["median20_vol"], "position_note": note, "tape": tape}

    def run(execute: bool = False) -> dict:
        plan = plan_chunk()
        st = _state(); today = _today()
        if plan["action"] != "CHUNK":
            print(f"[{cfg['ticker']}-accum] {plan['action']}: {plan.get('why','')}")
            return plan
        rec = {"tokyo_date": today, "qty": plan["qty"], "limit": plan["limit"], "tif": "DAY",
               "staged": True, "executed": False, "tape_px": plan["tape"]["px"],
               "participation": round(plan["participation"], 4),
               "ts": dt.datetime.utcnow().isoformat() + "Z"}
        if execute and not _session_open():
            print(f"[{cfg['ticker']}-accum] SESSION_CLOSED — Tokyo cash session is 09:00-15:30 JST; "
                  "run during 08:00-15:25 JST or let the morning cron/daemon handle it. Placing now "
                  "would double-chunk tomorrow's session.")
            return {**plan, "action": "SESSION_CLOSED"}
        if execute:
            rec["placing"] = True
            st["chunks"].append(rec)
            state_path.write_text(json.dumps(st, indent=1))
            from ib_insync import IB, Stock, LimitOrder
            from desk.account_registry import require_alpha
            ib = IB(); ib.connect("127.0.0.1", 4001, clientId=cfg.get("client_id", 65), timeout=10)
            try:
                acct = require_alpha(ib)
                c = Stock(symbol=cfg["symbol"], exchange="SMART", currency="JPY",
                          primaryExchange="TSEJ")
                ib.qualifyContracts(c)
                o = LimitOrder("BUY", rec["qty"], rec["limit"], tif="DAY", outsideRth=False)
                o.account = acct
                o.displaySize = LOT
                o.orderRef = f"{cfg['ticker']}-ACCUM"
                tr = ib.placeOrder(c, o); ib.sleep(3)
                status = tr.orderStatus.status
                rec.update(order_id=tr.order.orderId, status=status,
                           broker_log=[l.message for l in tr.log if l.message][-4:])
                rec["executed"] = status in ("Submitted", "PreSubmitted", "PendingSubmit", "Filled")
                if not rec["executed"]:
                    print(f"[{cfg['ticker']}-accum] ORDER NOT LIVE — {status}; {rec['broker_log']}")
            finally:
                ib.disconnect()
                rec["placing"] = False
                state_path.write_text(json.dumps(st, indent=1))
            try:
                led = json.loads(ATTR.read_text()) if ATTR.exists() else []
                led.append({**rec, "cohort": "jp_accum_core", "agent_origin": "signalos_desk",
                            "ticker": cfg["ticker"], "action": "BUY"})
                ATTR.write_text(json.dumps(led, indent=2))
            except Exception:
                pass
        else:
            st["chunks"].append(rec)
            state_path.write_text(json.dumps(st, indent=1))
        mode = ("EXECUTED" if rec.get("executed") else
                f"PLACEMENT FAILED ({rec.get('status','?')})" if execute else
                "STAGED (no order placed)")
        msg = (f"{cfg['ticker']} day-chunk {mode}: BUY {rec['qty']} @ ¥{rec['limit']} DAY "
               f"({rec['participation']:.1%} of 20d median vol). Held {plan['held']}, target "
               f"{cfg['target_sh']}, remaining {plan['remaining_after']}. Tape ¥{plan['tape']['px']} "
               f"({plan['position_note']}). Ceiling {cfg['ceiling']} / pause {cfg['pause_below']}.")
        print(f"[{cfg['ticker']}-accum] {msg}")
        try:
            from desk.mailer import send as msend
            msend(f"{cfg['ticker']} ACCUM {mode.split()[0]}: {rec['qty']} @ {rec['limit']}",
                  [("envelope", [msg])])
        except Exception as e:
            print(f"[{cfg['ticker']}-accum] mail failed ({e})")
        return {**plan, "record": rec}

    return run, plan_chunk
