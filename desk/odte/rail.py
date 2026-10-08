"""Live execution rail for the 0DTE sleeve — ONE XSP iron condor as a BAG combo through the
Gateway, under the ODTE-XSP-LIVE envelope. The runner calls this only when risk.live_gates passed.

Combo price sign (IBKR convention, tested in tests/test_odte.py::test_combo_limit_sign):
  the BAG is defined as the condor we are SHORT (legs: SELL sp, BUY lp, SELL sc, BUY lc).
  OPEN  = BUY  1 bag at a NEGATIVE limit  (negative on a BUY  = we RECEIVE the credit)
  CLOSE = SELL 1 bag at a NEGATIVE limit  (negative on a SELL = we PAY the debit)
Before the FIRST live open of a session the rail runs whatIfOrder and refuses if the initial
margin change is not within [0.5x, 1.5x] of the structure's max loss — a sign error or a wrong
leg shows up there as a wildly different margin number, before any order exists.

Every order carries orderRef=ENVELOPE and account=ALPHA (require_alpha). Nothing here is GTC.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import uuid
from zoneinfo import ZoneInfo

from desk.odte.storage import atomic_write

from desk.odte.doctrine import (ENVELOPE, INSTRUMENT, MULTIPLIER, CONTRACTS, LIVE_LEDGER, DATA)


def combo_limit(action: str, net_per_share: float) -> float:
    """Signed combo limit. net_per_share is the money we want: positive = receive (credit),
    negative = pay (debit). BUY at -credit receives; SELL at -debit pays."""
    if action == "BUY":
        return round(-abs(net_per_share), 2) if net_per_share > 0 else round(abs(net_per_share), 2)
    return round(-abs(net_per_share), 2) if net_per_share < 0 else round(abs(net_per_share), 2)


def bag_for(legs: dict):
    from ib_insync import Contract, ComboLeg
    order = [("sp", "SELL"), ("lp", "BUY"), ("sc", "SELL"), ("lc", "BUY")]
    cl = [ComboLeg(conId=int(legs[k]["conId"]), ratio=1, action=a, exchange="SMART") for k, a in order]
    assert all(legs[k].get("conId") for k, _ in order), "leg conId missing"
    return Contract(symbol=INSTRUMENT, secType="BAG", currency="USD", exchange="SMART", comboLegs=cl)


class LiveRail:
    def __init__(self, ib, account: str, *, date: str | None = None, checkpoint=None):
        self.ib = ib; self.account = account; self.margin_checked = False
        self.date = date
        self.checkpoint = checkpoint

    def _submit(self, bag, order):
        # Never send a live order without a durable intent. A crash between this
        # checkpoint and the reply is recovered using the unique orderRef.
        if self.checkpoint is None or self.date is None:
            raise RuntimeError("live orders require a durable checkpoint and session date")
        order.orderId = self.ib.client.getReqId()
        order.orderRef = f"{ENVELOPE}:{self.date}:{uuid.uuid4().hex[:12]}"
        self.checkpoint({"ref": order.orderRef, "order_id": order.orderId,
                         "action": order.action, "quantity": float(order.totalQuantity),
                         "status": "INTENT", "filled": 0.0, "fills": {}})
        return self.ib.placeOrder(bag, order)

    def _wait(self, trade, seconds):
        for _ in range(max(1, math.ceil(seconds))):
            if trade.orderStatus.status in TERMINAL:
                break
            self.ib.sleep(1)

    def _cancel(self, trade):
        if trade.orderStatus.status not in TERMINAL:
            self.ib.cancelOrder(trade.order)
            self._wait(trade, 10)
        # PendingCancel is NOT an acknowledgement. Re-read fills after waiting.
        return trade.orderStatus.status in TERMINAL

    def _result(self, trade, legs):
        st = trade.orderStatus
        filled = float(st.filled)
        avg_fill = float(st.avgFillPrice) if filled else None
        executions = {f.execution.execId: {"con_id": f.contract.conId, "sec_type": f.contract.secType,
                      "side": f.execution.side, "quantity": float(f.execution.shares),
                      "price": float(f.execution.price), "commission": None}
                      for f in self.ib.fills() if f.execution.acctNumber == self.account
                      and (f.execution.orderRef == trade.order.orderRef
                           or getattr(f.execution, "orderId", None) == trade.order.orderId)}
        qty, price, _, _ = execution_totals({"action": trade.order.action, "fills": executions}, legs)
        if qty > filled:
            filled = qty; avg_fill = -price
        # A terminal order-status callback can arrive before all four leg
        # execution reports. Never replace against that incomplete picture.
        incomplete_legs = bool(executions) and any(f["sec_type"] != "BAG" for f in executions.values()) and qty == 0
        return {"ref": trade.order.orderRef, "order_id": trade.order.orderId,
                "perm_id": st.permId, "status": st.status, "filled": filled,
                "avg_fill": avg_fill,
                "terminal": st.status in TERMINAL and not incomplete_legs}

    def _order(self, action: str, limit: float):
        from ib_insync import LimitOrder
        o = LimitOrder(action, CONTRACTS, limit, tif="DAY")
        o.orderRef = ENVELOPE; o.account = self.account; o.outsideRth = False
        return o

    def what_if(self, legs: dict, credit: float, max_loss_usd: float) -> dict:
        bag = bag_for(legs); o = self._order("BUY", combo_limit("BUY", credit))
        st = self.ib.whatIfOrder(bag, o)
        try:
            dm = float(st.initMarginChange)
        except (TypeError, ValueError):
            dm = float("nan")
        ok = (0.5 * max_loss_usd) <= dm <= (1.5 * max_loss_usd) if dm == dm else False
        rec = {"init_margin_change": dm, "maint_margin_change": getattr(st, "maintMarginChange", None),
               "commission": getattr(st, "commission", None), "max_loss_usd": max_loss_usd, "ok": ok,
               "status": getattr(st, "status", None), "warning": getattr(st, "warningText", None)}
        self.margin_checked = ok
        _audit("WHATIF", rec)
        return rec

    def open_condor(self, legs: dict, credit: float, wait_s: float = 45.0) -> dict:
        if not self.margin_checked:
            return {"status": "REFUSED", "why": "whatIf not passed this session"}
        tr = self._submit(bag_for(legs), self._order("BUY", combo_limit("BUY", credit)))
        self._wait(tr, wait_s)
        self._cancel(tr)
        rec = self._result(tr, legs)
        if rec["filled"]:
            rec["credit_filled"] = abs(rec["avg_fill"])
        _audit("OPEN", rec)
        return rec

    def close_condor(self, legs: dict, debit: float, wait_s: float = 45.0,
                     chase: float = 0.10, quantity: float = CONTRACTS) -> dict:
        """Replace only after terminal acknowledgement; sell only the remainder."""
        from ib_insync import MarketOrder
        bag = bag_for(legs)
        filled = 0.0; paid = 0.0
        for px in (debit, debit + chase, None):
            remaining = quantity - filled
            if remaining <= 0:
                break
            if px is None:
                o = MarketOrder("SELL", remaining, tif="DAY", account=self.account)
            else:
                o = self._order("SELL", combo_limit("SELL", -px))
                o.totalQuantity = remaining
            tr = self._submit(bag, o)
            self._wait(tr, wait_s if px is not None else 5)
            if px is not None:
                self._cancel(tr)
            rec = self._result(tr, legs)
            filled += rec["filled"]
            paid += rec["filled"] * abs(rec["avg_fill"] or 0)
            rec.update(filled_total=filled, debit_paid=paid / filled if filled else None)
            _audit("CLOSE", rec)
            if filled >= quantity or not rec["terminal"]:
                return rec
        return rec

    def cancel_all_ours(self) -> int:
        n = 0
        for tr in self.ib.openTrades():
            if self._ours(tr.order) and tr.orderStatus.status not in TERMINAL:
                self.ib.cancelOrder(tr.order); n += 1
        return n

    def _ours(self, order) -> bool:
        return order.account == self.account and (order.orderRef == ENVELOPE or
                                                  order.orderRef.startswith(ENVELOPE + ":"))

    def official_close(self, date: str) -> float | None:
        """The XSP official close for `date` from the broker's daily bar (XSP PM-settles to the
        closing index value). None if the bar is not available yet. Never a captured last print."""
        try:
            from ib_insync import Index
            xsp = Index(INSTRUMENT, "CBOE", "USD")
            try:
                self.ib.qualifyContracts(xsp)
            except Exception:
                pass                                  # fully specified index contract; qualification is optional
            bars = self.ib.reqHistoricalData(xsp, endDateTime=f"{date.replace('-', '')} 23:59:59 US/Eastern",
                                             durationStr="2 D", barSizeSetting="1 day", whatToShow="TRADES", useRTH=True)
            for b in bars:
                if str(b.date)[:10] == date and b.close and math.isfinite(float(b.close)):
                    return float(b.close)
        except Exception as e:
            _audit("OFFICIAL_CLOSE_ERROR", {"date": date, "error": f"{type(e).__name__}: {e}"[:200]})
        return None

    def reconcile(self, live: dict, date: str) -> dict:
        """Refresh orders/executions/positions; ambiguity blocks new submissions.

        Execution ids are retained across reconnects, and late commission reports
        replace earlier missing reports. Positions independently corroborate fills.
        """
        from ib_insync import ExecutionFilter
        trades = list(self.ib.reqAllOpenOrders()) + list(self.ib.reqCompletedOrders(apiOnly=False))
        self.ib.reqExecutions(ExecutionFilter(acctCode=self.account))
        positions = self.ib.reqPositions()
        trades += list(self.ib.trades())
        fills = [f for f in self.ib.fills() if f.execution.acctNumber == self.account
                 and f.execution.time.astimezone(ZoneInfo("America/New_York")).date().isoformat() == date]
        orders = live.setdefault("orders", [])
        by_ref = {o["ref"]: o for o in orders}
        prefix = f"{ENVELOPE}:{date}:"
        actual = {p.contract.conId: float(p.position) for p in positions
                  if p.account == self.account and p.contract.symbol == INSTRUMENT
                  and p.contract.lastTradeDateOrContractMonth[:8] == date.replace("-", "") and p.position}
        unknown_orders = [t for t in trades if self._ours(t.order) and
                          t.orderStatus.status not in TERMINAL and t.order.orderRef not in by_ref]
        # Broker order rows refresh each intent's status / permId first, so executions can be
        # matched by permId or orderId as well as orderRef.
        by_order_id = {int(o["order_id"]): o for o in orders if o.get("order_id") is not None}
        for tr in trades:
            o = by_ref.get(tr.order.orderRef) or (by_order_id.get(tr.order.orderId) if self._ours(tr.order) else None)
            if o is not None and self._ours(tr.order):
                # Do not let a stale open-order snapshot overwrite a terminal reply.
                if o["status"] not in TERMINAL or tr.orderStatus.status in TERMINAL:
                    o["status"] = tr.orderStatus.status
                o["perm_id"] = tr.order.permId or tr.orderStatus.permId

        def intent_for(e):
            """An execution is OURS if its orderRef, permId or orderId matches a durable intent. A
            combo leg execution can arrive with an empty orderRef (2026-10-07 review); the ids the
            checkpoint already holds decide, so our own fills are never misread as external."""
            o = by_ref.get(e.orderRef)
            if o is None and getattr(e, "permId", None):
                o = next((x for x in orders if x.get("perm_id") and x["perm_id"] == e.permId), None)
            if o is None and getattr(e, "orderId", None) is not None:
                o = by_order_id.get(int(e.orderId))
            return o

        unknown_fills = [f for f in fills if (f.execution.orderRef == ENVELOPE or
                         f.execution.orderRef.startswith(prefix)) and intent_for(f.execution) is None]
        # A manual close may be reported as a BAG with conId=0. Inspect its legs,
        # or the matching broker order if the execution omits the combo details.
        # Keep observed evidence in the checkpoint: Gateway's execution history
        # ends at midnight, so a fresh empty response cannot clear this block.
        leg_ids = {int(v["conId"]) for v in (live.get("legs") or {}).values() if v.get("conId")}
        external = live.setdefault("external_executions", {})
        if "external execution" in (live.get("reconciliation_error") or "").lower() and not external:
            external["legacy"] = {"reason": live["reconciliation_error"]}
        for f in fills:
            e = f.execution
            if intent_for(e) is not None:
                continue
            ids = contract_ids(f.contract)
            bag = f.contract.secType == "BAG"
            if bag and not ids and getattr(e, "permId", 0):
                for tr in trades:
                    perm_id = tr.order.permId or tr.orderStatus.permId
                    if tr.order.account == self.account and perm_id == e.permId:
                        ids |= contract_ids(tr.contract)
            ambiguous = bag and not ids and getattr(f.contract, "symbol", "") == INSTRUMENT
            if leg_ids and (ids & leg_ids or ambiguous):
                external[e.execId] = {"account": e.acctNumber, "order_ref": e.orderRef,
                                      "time": e.time.isoformat(), "sec_type": f.contract.secType,
                                      "con_ids": sorted(ids), "side": e.side,
                                      "quantity": str(e.shares), "price": str(e.price),
                                      "ambiguous_combo": ambiguous}
        if external:
            return {"ok": False, "why": f"{len(external)} external execution record(s) on or possibly on condor legs — reconcile using broker records"}
        if unknown_orders or unknown_fills or (actual and not orders):
            return {"ok": False, "why": "broker activity has no matching durable order intent"}
        if live.get("status") in {"OPEN", "OPENING", "CLOSING", "RECONCILING", "CLOSED"} and not orders:
            return {"ok": False, "why": "position state has no durable order history; reconciliation required"}
        for fill in fills:
            e = fill.execution
            o = intent_for(e)
            if o is None:
                continue
            report = fill.commissionReport
            fee = report.commission
            valid_fee = (report.execId == e.execId and report.currency == "USD"
                         and math.isfinite(fee) and abs(fee) < 1e6)
            previous = o.setdefault("fills", {}).get(e.execId, {})
            o["fills"][e.execId] = {"con_id": fill.contract.conId, "sec_type": fill.contract.secType,
                                    "side": e.side, "quantity": float(e.shares), "price": float(e.price),
                                    "commission": fee if valid_fee else previous.get("commission")}
        opened = closed = credit_value = debit_value = 0.0
        commissions = 0.0; fees_complete = True; pending = False
        legs = live.get("legs") or {}
        for o in orders:
            qty, price, fees, fee_ok = execution_totals(o, legs)
            o["filled"] = qty
            commissions += fees; fees_complete &= fee_ok
            if qty > o["quantity"]:
                return {"ok": False, "why": "executions exceed intended order quantity"}
            if o["status"] == "Filled" and qty != o["quantity"]:
                return {"ok": False, "why": "filled order awaiting complete execution details"}
            if qty == o["quantity"]:
                o["status"] = "Filled"
            pending |= o["status"] not in TERMINAL
            if o["action"] == "BUY":
                opened += qty; credit_value += qty * price
            else:
                closed += qty; debit_value += qty * price
        remaining = opened - closed
        if remaining < 0 or opened > CONTRACTS:
            return {"ok": False, "why": "broker exposure exceeds the one-structure contract"}
        expected = {int(legs[k]["conId"]): sign * remaining for k, sign in
                    (("sp", -1), ("lp", 1), ("sc", -1), ("lc", 1))} if remaining and legs else {}
        expired = False
        if remaining and not actual and not pending and expired_session(date):
            # The contracts have left the account after the bell: XSP cash-settled them. This is the
            # NORMAL end of a condor that was not closed, not an ambiguity (2026-10-07 review: the
            # old mismatch here locked the rail forever after the first run-to-settlement).
            expired = True
        elif actual != expected:
            return {"ok": False, "why": "broker positions do not match balanced condor executions"}
        return {"ok": True, "pending": pending, "opened": opened, "closed": closed, "expired": expired,
                "remaining": remaining, "credit": credit_value / opened if opened else None,
                "debit": debit_value / closed if closed else None, "commissions": commissions,
                "fees_complete": fees_complete}


TERMINAL = {"Filled", "Cancelled", "ApiCancelled", "Inactive"}
SETTLEMENT_CUTOFF_ET = (16, 15)


def contract_ids(contract) -> set[int]:
    if contract.secType == "BAG":
        return {int(leg.conId) for leg in (getattr(contract, "comboLegs", None) or []) if leg.conId}
    return {int(contract.conId)} if contract.conId else set()


def _now_et() -> dt.datetime:
    return dt.datetime.now(ZoneInfo("America/New_York"))


def expired_session(date: str) -> bool:
    """True once `date`'s 0DTE contracts have expired: a later date, or the same date past the
    settlement cutoff. Monkeypatch _now_et in tests."""
    now = _now_et(); today = now.date().isoformat()
    return date < today or (date == today and (now.hour, now.minute) >= SETTLEMENT_CUTOFF_ET)


def execution_totals(order: dict, legs: dict) -> tuple[float, float, float, bool]:
    """Use balanced leg fills when present, otherwise BAG executions; never both.

    A combo may deliver four leg reports as well as a synthetic BAG report.
    Selecting one representation avoids counting quantity or commissions twice.
    """
    fills = list(order.get("fills", {}).values())
    leg_fills = [f for f in fills if f["sec_type"] != "BAG"]
    selected = leg_fills or fills
    fee_ok = bool(selected) and all(f.get("commission") is not None for f in selected)
    fees = sum(f.get("commission") or 0 for f in selected)
    if not fills:
        return 0., 0., 0., True
    if not leg_fills:
        qty = sum(f["quantity"] for f in fills)
        return qty, abs(sum(f["price"] * f["quantity"] for f in fills) / qty), fees, fee_ok
    quantities = []; value = 0.
    for key, sign in (("sp", 1), ("lp", -1), ("sc", 1), ("lc", -1)):
        matching = [f for f in leg_fills if f["con_id"] == legs.get(key, {}).get("conId")]
        expected_side = "SLD" if (sign == 1) == (order["action"] == "BUY") else "BOT"
        if any(f["side"] != expected_side for f in matching):
            raise ValueError("execution side does not match intended condor")
        quantities.append(sum(f["quantity"] for f in matching))
        value += sign * sum(f["price"] * f["quantity"] for f in matching)
    if len(set(quantities)) != 1 or not quantities[0]:
        # Uneven legs must not be mistaken for a filled combo. Position checking
        # also prevents trading while those execution reports are incomplete.
        return 0., 0., fees, False
    return quantities[0], value / quantities[0], fees, fee_ok


def _audit(kind: str, rec: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / "rail_audit.jsonl").open("a") as f:
        f.write(json.dumps({"kind": kind, "envelope": ENVELOPE, **rec}, default=str) + "\n")


def append_live(row: dict) -> None:
    """Idempotent session upsert, including later commission reconciliation."""
    rows = {_ledger_key(r): r for r in read_live()}
    rows[_ledger_key(row)] = row
    atomic_write(LIVE_LEDGER, "".join(json.dumps(r, allow_nan=False) + "\n" for r in rows.values()))


def _ledger_key(row):
    return (row.get("book", "live"), row["date"], row["template"])


def read_live() -> list[dict]:
    if not LIVE_LEDGER.exists():
        return []
    rows = [json.loads(line) for line in LIVE_LEDGER.read_text().splitlines() if line.strip()]
    for row in rows:
        if row.get("pnl_usd") is not None and "accounting_status" not in row:
            # Legacy rows contain gross estimates, not reconciled net results.
            row.update(gross_pnl_usd=row["pnl_usd"], pnl_usd=None, accounting_status="pending_legacy")
    return list({_ledger_key(r): r for r in rows}.values())


def live_pnl_usd(credit_filled: float, debit_paid: float, contracts: int = CONTRACTS, commissions: float = 0.0) -> float:
    return round((credit_filled - debit_paid) * MULTIPLIER * contracts - commissions, 2)
