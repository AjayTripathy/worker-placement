"""Order-integrity sentinel — the $5M-grade rail (2026-08-25, principal-directed hardening).

Failure classes this closes (all OBSERVED, not hypothetical):
  1. Cancels stuck in PendingCancel through a gateway restart (ACEL/6626/CRM sat 18h, 08-24/25).
  2. Gateway API wedge — handshake timeouts with no alarm (twice this week).
  3. Cancel-by dates on resting GTCs enforced only by session memory (resting-order-into-print
     rail, NATR lesson) — now machine-checked.
  4. Expected resting orders silently disappearing (WAL rungs — benign that time, unverified
     for days).
  5. envelope_runner absent while a Tokyo session approaches (Mac slept 08-17, session lost).

Intent ledger: desk/data/order_intents.json
  expected_cancelled: orders directed dead — CRITICAL if seen alive on the blotter.
  expected_resting:   orders that should be live — WARN if missing (fill? loss? verify),
                      CRITICAL if present past their cancel_by date.

Alerts via desk.mailer (subject carries the event); quiet when clean.
Runs from launchd every 30 min (com.signalos.order-sentinel) and by hand:
    python3 -m desk.order_sentinel [--dry]
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTENTS = ROOT / "desk" / "data" / "order_intents.json"
STATE = ROOT / "desk" / "data" / "order_sentinel_state.json"
PENDING_CANCEL_SLA_MIN = 30
GATEWAY_STRIKES_TO_ALERT = 2


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _load(path: Path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def _blotter():
    """Live open orders via the gateway. Returns (orders, None) or (None, error)."""
    try:
        from desk.order_executor import IBKROrderExecutor
        ex = IBKROrderExecutor(client_id=93)
        ex.connect(timeout=10)
        # non-zero clientId sees only its OWN orders unless all are requested explicitly
        ex._ib.reqAllOpenOrders()
        ex._ib.sleep(1.5)
        orders = ex.get_open_orders()
        try:
            poss = {p.contract.symbol: p.position for p in ex._ib.positions()}
        except Exception:
            poss = {}
        ex.disconnect()
        return orders, poss, None
    except Exception as e:
        return None, {}, str(e)


def _match(order: dict, spec: dict) -> bool:
    return (
        order.get("localSymbol", order.get("symbol")) == spec["symbol"]
        or order.get("symbol") == spec["symbol"]
    ) and order.get("action") == spec["action"] \
      and int(order.get("qty", -1)) == int(spec["qty"]) \
      and abs(float(order.get("limit_price", -1)) - float(spec["limit"])) < 1e-6


def _runner_alive() -> bool:
    out = subprocess.run(["pgrep", "-f", "desk.envelope_runner"], capture_output=True)
    return out.returncode == 0


def run(dry: bool = False) -> int:
    intents = _load(INTENTS, {"expected_cancelled": [], "expected_resting": []})
    state = _load(STATE, {"gateway_strikes": 0, "pending_cancel_first_seen": {}})
    findings: list[tuple[str, str]] = []  # (severity, message)
    now = _now()

    orders, positions, err = _blotter()
    if orders is None:
        state["gateway_strikes"] = state.get("gateway_strikes", 0) + 1
        if state["gateway_strikes"] >= GATEWAY_STRIKES_TO_ALERT:
            findings.append(("CRITICAL",
                f"GATEWAY WEDGED: {state['gateway_strikes']} consecutive connect failures "
                f"({err}). Orders, cancels and tonight's envelopes are all blind until it is "
                f"restarted. This is the 08-24 failure mode."))
    else:
        state["gateway_strikes"] = 0

        # 1. directed-dead orders seen alive
        for spec in intents.get("expected_cancelled", []):
            hits = [o for o in orders if _match(o, spec)]
            for o in hits:
                findings.append(("CRITICAL",
                    f"ZOMBIE ORDER: {spec['symbol']} {spec['action']} {spec['qty']}@{spec['limit']} "
                    f"was directed CANCELLED ({spec.get('directed','')}) but is ALIVE with status "
                    f"{o.get('status','?')}. Re-cancel and verify."))

        # 2. pending-cancel SLA
        pc_seen = state.get("pending_cancel_first_seen", {})
        live_pc_keys = set()
        for o in orders:
            if str(o.get("status", "")).lower().startswith("pendingcancel"):
                key = f"{o.get('symbol')}|{o.get('action')}|{o.get('qty')}|{o.get('limit_price')}"
                live_pc_keys.add(key)
                first = pc_seen.get(key)
                if first is None:
                    pc_seen[key] = now.isoformat()
                else:
                    age_min = (now - dt.datetime.fromisoformat(first)).total_seconds() / 60
                    if age_min > PENDING_CANCEL_SLA_MIN:
                        findings.append(("CRITICAL",
                            f"STUCK CANCEL: {key} in PendingCancel {age_min:.0f} min "
                            f"(SLA {PENDING_CANCEL_SLA_MIN}). The 18h ACEL/6626 failure mode — "
                            f"re-issue the cancel."))
        state["pending_cancel_first_seen"] = {k: v for k, v in pc_seen.items() if k in live_pc_keys}

        # 3.7 OPTION-GTC-AGE (principal preference 2026-09-04: no long-resting option GTCs -
        # stale quotes + vol-regime drift make unwatched option orders accidental positions).
        # Warn-only; pulls remain principal/court actions.
        try:
            import datetime as _dt
            for o in orders:
                sec = str(o.get("secondary_description", "")) + str(o.get("primary_description", ""))
                if (" Put" in sec or " Call" in sec) and o.get("order_time"):
                    age = (_dt.datetime.now(_dt.timezone.utc) -
                           _dt.datetime.fromisoformat(str(o["order_time"]).replace("Z", "+00:00"))).days
                    if age > 7:
                        warns.append((f"OPTION-GTC-AGE: {o.get('primary_description')} resting {age}d "
                                      f"(> 7d rail, principal 2026-09-04) — re-check the vol regime "
                                      f"or pull it"))
        except Exception:
            pass
        # 3. expected resting: presence + cancel-by enforcement
        for spec in intents.get("expected_resting", []):
            hits = [o for o in orders if _match(o, spec)]
            cb = spec.get("cancel_by")
            if not hits:
                if spec.get("awaiting_click"):
                    continue  # staged instruction, principal hasn't clicked yet — not a loss
                # FILL-vs-LOST discrimination (2026-08-29: a filled UCTT band order read as a
                # "missed touch" from the principal's seat because no fill notice exists — check
                # the position book before crying LOST, and report fills as INFO loudly).
                poss = positions
                sym = spec["symbol"]
                if spec["action"] == "BUY" and poss.get(sym, 0) > 0:
                    findings.append(("INFO",
                        f"ORDER FILLED: {sym} {spec['qty']}@{spec['limit']} is off the blotter and a "
                        f"long position exists ({poss[sym]:.0f} sh) — move the intent row to filled_log "
                        f"and run the post-fill instrumentation from its ruling."))
                else:
                    findings.append(("WARN",
                        f"MISSING RESTING ORDER: {sym} {spec['action']} "
                        f"{spec['qty']}@{spec['limit']} not on blotter and no matching position — "
                        f"verify at trades or LOST; update order_intents.json."))
            elif cb and now.date() >= dt.date.fromisoformat(cb):
                findings.append(("CRITICAL",
                    f"CANCEL-BY BREACHED: {spec['symbol']} {spec['qty']}@{spec['limit']} is live "
                    f"past its cancel-by {cb} ({spec.get('why_cb','pre-print rail')}). "
                    f"Cancel it TODAY — this is the resting-order-into-print rail."))

    # 3.5 settled-cash rule (principal-ratified 2026-09-01): a persistent debit is pure
    # negative carry (margin ~6% vs SGOV ~4.3%). No auto-placement — the executor has no
    # transmit=False path, and the write rail requires a click — so compute the exact trim
    # and email it once per episode.
    if orders is not None:
        try:
            # CURRENCY FIX (2026-09-04): BASE aggregates the INTENTIONAL local-currency
            # borrows (JPY/KRW financing = the designed FX hedge), so a negative BASE is not
            # a carry problem. The SGOV rule keys on the USD line only; non-USD debits warn
            # only when they EXCEED local stock value (i.e., an UNHEDGED borrow).
            cash = None; fx_cash = {}; fx_stock = {}
            try:
                from desk.order_executor import IBKROrderExecutor as _EX
                _e = _EX(client_id=94); _e.connect(timeout=10)
                for av in _e._ib.accountValues():
                    if av.tag == "TotalCashBalance" and av.currency == "USD":
                        cash = float(av.value)
                    elif av.tag == "TotalCashBalance" and av.currency not in ("BASE",):
                        fx_cash[av.currency] = float(av.value)
                    elif av.tag == "StockMarketValue" and av.currency not in ("BASE", "USD"):
                        fx_stock[av.currency] = float(av.value)
                _e.disconnect()
            except Exception:
                pass
            for ccy, bal in fx_cash.items():
                if bal < 0 and abs(bal) > 1.10 * max(fx_stock.get(ccy, 0.0), 0.0) \
                        and abs(bal) * 0.01 > 500:
                    findings.append(("WARN",
                        f"FX BORROW UNHEDGED: {ccy} cash {bal:,.0f} exceeds local stock "
                        f"{fx_stock.get(ccy, 0.0):,.0f} by >10% — the local-currency-funding "
                        f"policy covers borrows UP TO the local asset value; the excess is an "
                        f"open FX short, review it"))
            if cash is not None and cash < -10_000:
                first = state.get("cash_debit_first_seen")
                if first is None:
                    state["cash_debit_first_seen"] = now.isoformat()
                elif (now - dt.datetime.fromisoformat(first)).total_seconds() > 86_400 \
                        and not state.get("cash_debit_alerted"):
                    pending = sum(r["qty"] * r["limit"] for r in intents.get("expected_resting", [])
                                  if r.get("action") == "BUY" and r.get("awaiting_click"))
                    need = -cash + pending + 2_000
                    qty = int(need / 100.40) + 1
                    findings.append(("WARN",
                        f"SETTLED-CASH DEBIT {cash:,.0f} persisted >1d (+{pending:,.0f} pending buys). "
                        f"STAGE: SELL {qty} SGOV @ ~market limit (tax-costless, cures ~2pp negative carry). "
                        f"One click; the desk stages it next session if unactioned."))
                    state["cash_debit_alerted"] = True
            elif cash is not None and cash >= -1_000:
                state.pop("cash_debit_first_seen", None)
                state.pop("cash_debit_alerted", None)
        except Exception as e:
            print(f"[order_sentinel] cash rule errored: {type(e).__name__}: {e}")

    # 3.6 INTO-PRINT GUARD (principal-ratified standing rule 2026-09-02: "instead of just
    # warning me, the book removes GTCs as we approach relevant prints"). Resting BUYs on US
    # stocks whose next earnings print is within the buffer are AUTO-CANCELLED via clientId 0
    # (the ratified exception class, like envelope_runner), recorded in expected_cancelled,
    # and emailed as an action taken. Sells/trims are exempt (paid-trim rides are sanctioned);
    # intents whose `directed` text contains 'rides' or 'ride_print' are exempt (the AGX class
    # deliberately rides its print). Wrong-early is safe (restage post-print); the buffer leans
    # cautious. Print dates via yfinance calendar, cached 24h in state.
    if orders is not None:
        try:
            import time as _t
            pcache = state.setdefault("print_date_cache", {})
            exempt_syms = set()
            for r in intents.get("expected_resting", []):
                if "ride" in str(r.get("directed", "")).lower() or r.get("ride_print"):
                    exempt_syms.add(r.get("symbol"))
            buys = {}
            for o in orders:
                sym = o.get("symbol", "")
                if (o.get("action") == "BUY" and str(o.get("tif", "GTC")).upper() != "DAY"
                        and sym and sym.isalpha() and sym not in exempt_syms):
                    buys.setdefault(sym, []).append(o)
            to_cancel = []
            for sym in buys:
                ent = pcache.get(sym)
                if not ent or _t.time() - ent.get("ts", 0) > 86_400:
                    nxt = None
                    try:
                        import yfinance as yf
                        cal = yf.Ticker(sym).calendar
                        d = None
                        if cal is not None:
                            ed = cal.get("Earnings Date") if isinstance(cal, dict) else None
                            if ed:
                                d = ed[0] if isinstance(ed, (list, tuple)) else ed
                        if d is not None:
                            nxt = str(d)[:10]
                    except Exception:
                        pass
                    pcache[sym] = ent = {"date": nxt, "ts": _t.time()}
                nd = ent.get("date")
                if nd:
                    try:
                        days = (dt.date.fromisoformat(nd) - now.date()).days
                        if 0 <= days <= 3:
                            to_cancel.extend((sym, o, nd) for o in buys[sym])
                    except ValueError:
                        pass
            if to_cancel and not dry:
                try:
                    from desk.order_executor import IBKROrderExecutor as _EX0
                    _e0 = _EX0(client_id=0); _e0.connect(timeout=12)
                    _e0._ib.reqAllOpenOrders(); _e0._ib.sleep(2)
                    for sym, spec, nd in to_cancel:
                        for t in _e0._ib.openTrades():
                            oo = t.order
                            if (t.contract.symbol == sym and oo.action == "BUY"
                                    and int(oo.totalQuantity) == int(spec.get("qty", -1))
                                    and abs(float(oo.lmtPrice) - float(spec.get("limit_price", -1))) < 0.01):
                                _e0._ib.cancelOrder(oo)
                                intents.setdefault("expected_cancelled", []).append({
                                    "symbol": sym, "action": "BUY", "qty": int(oo.totalQuantity),
                                    "limit": float(oo.lmtPrice),
                                    "directed": f"INTO-PRINT GUARD auto-cancel {now.date()} (print ~{nd}; restage post-print if the court still wants it)"})
                                findings.append(("WARN",
                                    f"INTO-PRINT GUARD: cancelled {sym} BUY {int(oo.totalQuantity)}@{oo.lmtPrice} "
                                    f"(print ~{nd}). Court can restage post-print."))
                    _e0._ib.sleep(2); _e0.disconnect()
                    INTENTS.write_text(json.dumps(intents, indent=1))
                except Exception as e:
                    findings.append(("WARN", f"into-print guard cancel path failed: {type(e).__name__}: {e}"))
            elif to_cancel:
                for sym, spec, nd in to_cancel:
                    findings.append(("WARN", f"[dry] into-print guard would cancel {sym} BUY {spec.get('qty')}@{spec.get('limit_price')} (print ~{nd})"))
        except Exception as e:
            print(f"[order_sentinel] into-print guard errored: {type(e).__name__}: {e}")

    # 4. envelope runner liveness (weekdays; Tokyo session is always <24h away)
    if now.weekday() < 5 and not _runner_alive():
        findings.append(("WARN",
            "envelope_runner NOT RUNNING — Tokyo accumulators will not fire. "
            "Start it: caffeinate -is python3 -m desk.envelope_runner --daemon (plugged in)."))

    # DEDUP (2026-08-29: the UCTT/6804 fills generated 134 identical WARN lines over two days —
    # ~60 emails saying the same ambiguous thing; the principal read them as a missed band touch).
    # Email only when the finding SET changes (new finding, escalation, or resolution back to
    # clean); every run still logs to stdout.
    import hashlib
    digest = hashlib.sha256("\n".join(sorted(m for _, m in findings)).encode()).hexdigest()[:16]
    prev = state.get("last_finding_digest")
    changed = digest != prev
    state["last_finding_digest"] = digest if findings else None
    STATE.write_text(json.dumps(state, indent=1))

    if findings and not changed:
        print(f"[order_sentinel] {len(findings)} finding(s) unchanged since last email — logged, not re-sent")
        for sev, m in findings:
            print(f"  [{sev}] {m}")
        return 1
    if findings:
        crit = [m for s, m in findings if s == "CRITICAL"]
        body = "\n\n".join(f"[{s}] {m}" for s, m in findings)
        subject = (f"ORDER SENTINEL: {len(crit)} CRITICAL / {len(findings)-len(crit)} WARN"
                   if crit else f"ORDER SENTINEL: {len(findings)} WARN")
        print(body)
        if not dry:
            try:
                from desk.mailer import send_raw
                send_raw(subject, body)
            except Exception as e:
                print(f"[order_sentinel] mail failed: {e}", file=sys.stderr)
        return 1
    print(f"[order_sentinel] clean @ {now.isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(run(dry="--dry" in sys.argv))
