"""Broker-free regressions for the successive 0DTE execution and recovery reviews."""
import datetime as dt
import copy
import functools
from types import SimpleNamespace as NS

import pytest

from desk.odte import capture as C, rail as L, runner as R, shadow as S, risk
from desk.odte.templates import build_condor
from test_odte import chain
from test_odte_data_quality import capture, NOW
from test_odte_execution import Broker, session, rail, LEGS, DATE, isolation, reconnect_broker  # noqa: F401


def test_unchanged_wing_quote_is_still_a_quote():
    c = capture()
    # the two wings have not ticked for 20 minutes; the rest of the chain is live
    for key in ((670.0, "P"), (690.0, "C")):
        cid = c.tickers[key].contract.conId
        c._quote_times[cid] = {f: NOW - dt.timedelta(minutes=20) for f in ("bid", "ask", "last")}
    snap = c.snapshot(NOW)
    assert snap["chain_live"]
    wings = [r for r in snap["rows"] if (r["strike"], r["right"]) in ((670.0, "P"), (690.0, "C"))]
    assert all(r["live_eligible"] and r["bid"] is not None and r["quote_age_s"] == 1200 for r in wings)
    assert build_condor([r for r in snap["rows"] if r["live_eligible"]], .1, 2)["ok"]


def test_silent_chain_is_dead_even_if_one_leg_is_recent():
    c = capture()
    for cid in list(c._quote_times):
        c._quote_times[cid] = {f: NOW - dt.timedelta(minutes=10) for f in ("bid", "ask", "last")}
    for t in c.idx.values():                                   # indices stay fresh
        c._quote_times[t.contract.conId] = {f: NOW for f in ("bid", "ask", "last")}
    snap = c.snapshot(NOW)
    assert not snap["chain_live"] and not any(r["live_eligible"] for r in snap["rows"]) and snap["n_quoted"] == 0


def test_leg_silent_beyond_window_is_not_live_eligible():
    c = capture(); cid = c.tickers[(670.0, "P")].contract.conId
    c._quote_times[cid] = {f: NOW - dt.timedelta(minutes=45) for f in ("bid", "ask", "last")}
    snap = c.snapshot(NOW)
    row = next(r for r in snap["rows"] if (r["strike"], r["right"]) == (670.0, "P"))
    assert not row["live_eligible"] and row["bid"] is not None          # shadow keeps it; live refuses it


def test_expired_condor_is_settled_off_official_close_and_does_not_lock(monkeypatch):
    ib = Broker(["fill"]); s = session(ib); s.tick(NOW)
    assert s.lv["status"] == "OPEN"
    # the bell: contracts leave the account, the official close lands between the shorts
    ib.quantities.clear()
    monkeypatch.setattr(L, "_now_et", lambda: dt.datetime(2026, 10, 8, 16, 30, tzinfo=C.ET))
    ib.reqHistoricalData = lambda *a, **k: [NS(date=dt.date(2026, 10, 8), close=680.0)]
    s._reconcile_live(force=True)
    assert s.lv["status"] == "CLOSED" and s.lv["exit_reason"] == "EXPIRED_SETTLED" and s.lv["exit_cost"] == 0.0
    row = L.read_live()[0]
    assert row["accounting_status"] == "pending_statement" and row["gross_pnl_usd"] == 35 and row["settlement"]["xsp_official_close"] == 680.0
    ctx = {"date": "2026-10-09", "calendar_verified": True, "vix1d_now": 18., "first30_range": .005}
    ok, reasons, _ = risk.live_gates(R._envelope(), [row], ctx)
    assert ok, reasons


def test_expired_condor_waits_for_official_close(monkeypatch):
    ib = Broker(["fill"]); s = session(ib); s.tick(NOW)
    ib.quantities.clear()
    monkeypatch.setattr(L, "_now_et", lambda: dt.datetime(2026, 10, 8, 16, 30, tzinfo=C.ET))
    ib.reqHistoricalData = lambda *a, **k: []
    assert not s._reconcile_live(force=True)
    assert s.lv["status"] == "OPEN" and "official close" in s.lv["reconciliation_error"]


def test_prior_session_settles_at_next_startup(reconnect_broker):
    ib = Broker(["fill"]); s = session(ib); s.tick(NOW)
    ib.quantities.clear()
    ib = reconnect_broker(ib)
    ib.reqHistoricalData = lambda *a, **k: [NS(date=dt.date(2026, 10, 8), close=700.0)]   # through the call wing
    nxt = R.Session(ib, "2026-10-09", True)
    assert ib.fills() == []                 # prices and fees came from the durable checkpoint
    prior = S.load_state(DATE)["live"]
    assert prior["status"] == "CLOSED" and prior["exit_cost"] == 2.0 and prior["settlement"]["xsp_official_close"] == 700.0
    rows = {r["date"]: r for r in L.read_live()}
    assert rows[DATE]["gross_pnl_usd"] == -165 and rows[DATE]["accounting_status"] == "pending_statement"
    assert nxt.lv["status"] == "NONE"
    assert risk.week_pnl(list(rows.values()), "2026-10-09") == -167.6     # net (fees reconciled) counts against the caps
    assert risk.week_pnl([{**rows[DATE], "pnl_usd": None}], "2026-10-09") == -167.6   # gross minus reported fees when net is pending


# ---- 2026-10-07 second review (six items) ------------------------------------------------------
def test_external_close_is_not_settlement(monkeypatch):
    ib = Broker(["fill"]); s = session(ib); s.tick(NOW)
    sp = s.lv["legs"]["sp"]["conId"]
    # someone buys back the short put by hand in TWS: a fill on our leg with a foreign orderRef, position flat
    ib.executions.append(NS(execution=NS(execId="manual.1", acctNumber="FAKE", orderRef="", time=NOW, shares=1, price=1.5, side="BOT"),
                            contract=NS(conId=sp, secType="OPT"), commissionReport=NS(execId="manual.1", commission=0.65, currency="USD")))
    ib.quantities.clear()
    monkeypatch.setattr(L, "_now_et", lambda: dt.datetime(2026, 10, 8, 16, 30, tzinfo=C.ET))
    ib.reqHistoricalData = lambda *a, **k: [NS(date=dt.date(2026, 10, 8), close=680.0)]
    assert not s._reconcile_live(force=True)
    assert "external" in s.lv["reconciliation_error"] and s.lv["status"] == "OPEN"
    assert L.read_live()[0]["accounting_status"] == "pending_execution"


def test_entry_forces_fresh_broker_read():
    ib = Broker(); s = session(ib)                    # startup reconcile: clean
    ib.quantities[12345] = -1                         # an orphan position appears before the entry window
    s.tick(NOW)
    assert not ib.orders and s.lv["reconciliation_error"]          # detected BEFORE submission, not after


def test_caps_deduct_reported_fees_and_reserve_unknown_ones():
    row = {"date": DATE, "gross_pnl_usd": -398.0, "pnl_usd": None, "commissions_usd": 3.0, "fees_complete": False, "accounting_status": "pending_fees"}
    assert risk._pnl(row) == -404.0                   # -398 - 3 reported - 3 reserve
    ctx = {"date": DATE, "calendar_verified": True, "vix1d_now": 18., "first30_range": .005}
    assert any("weekly" in r for r in risk.live_gates(R._envelope(), [row], ctx)[1])
    assert risk._pnl({**row, "fees_complete": True}) == -401.0


@pytest.mark.parametrize("reply_available", [False, True])
def test_overnight_cancel_requires_a_broker_reply(reconnect_broker, reply_available):
    ib = Broker(["pending"]); s = session(ib); s.tick(NOW)
    assert s.lv["status"] == "OPENING"
    ib.orders[0].orderStatus.status = "Cancelled"
    ib = reconnect_broker(ib, completed=ib.orders if reply_available else ())
    nxt = R.Session(ib, "2026-10-09", True)
    prior = S.load_state(DATE)["live"]; rows = {r["date"]: r for r in L.read_live()}
    assert ib.fills() == []
    assert prior["status"] == ("NO_FILL" if reply_available else "OPENING")
    assert rows[DATE]["accounting_status"] == ("complete" if reply_available else "pending_execution")
    assert nxt._prior_unresolved == (0 if reply_available else 1)
    ctx = {"date": "2026-10-09", "calendar_verified": True, "vix1d_now": 18., "first30_range": .005}
    assert risk.live_gates(R._envelope(), list(rows.values()), ctx)[0] == reply_available


def test_unavailable_overnight_fees_keep_reserve_but_allow_entry(reconnect_broker):
    ib = Broker(["fill", "fill"]); ib.fill = functools.partial(Broker.fill, ib, fee=None)
    s = session(ib); s.tick(NOW); s.tick(NOW.replace(hour=15, minute=45))
    row = L.read_live()[0]
    assert s.lv["status"] == "CLOSED" and row["accounting_status"] == "pending_fees" and risk._pnl(row) == 22.0
    for f in ib.executions:
        f.commissionReport.execId = f.execution.execId; f.commissionReport.commission = 15.0
    ib = reconnect_broker(ib, behaviors=["fill"])
    nxt = R.Session(ib, "2026-10-09", True)
    assert ib.fills() == []
    assert nxt._prior_unresolved == 1
    row = {r["date"]: r for r in L.read_live()}[DATE]
    assert row["accounting_status"] == "pending_fees" and row["pnl_usd"] is None and risk._pnl(row) == 22
    nxt.st["live_session"] = dict(s.st["live_session"])
    nxt.tick(NOW.replace(day=9))
    assert len(ib.orders) == 1 and nxt.lv["status"] == "OPEN"
    assert nxt._prior_unresolved == 1         # still retried, not a blanket veto


def test_missing_official_close_is_retried_during_the_session(reconnect_broker):
    ib = Broker(["fill"]); s = session(ib); s.tick(NOW)
    ib.quantities.clear()
    ib = reconnect_broker(ib)
    ib.reqHistoricalData = lambda *a, **k: []
    nxt = R.Session(ib, "2026-10-09", True)
    assert nxt._prior_unresolved == 1 and S.load_state(DATE)["live"]["status"] == "OPEN"
    ib.reqHistoricalData = lambda *a, **k: [NS(date=dt.date(2026, 10, 8), close=680.0)]
    nxt._last_prior_sweep = 0
    nxt.tick(NOW.replace(day=9, hour=9, minute=40))
    assert nxt._prior_unresolved == 0 and S.load_state(DATE)["live"]["exit_reason"] == "EXPIRED_SETTLED"


def test_idle_reconcile_is_rate_limited(monkeypatch):
    ib = Broker(); s = session(ib)
    calls = []
    orig = s.rail.reconcile
    s.rail.reconcile = lambda live, date: calls.append(1) or orig(live, date)
    s.tick(NOW.replace(hour=9, minute=40)); s.tick(NOW.replace(hour=9, minute=41)); s.tick(NOW.replace(hour=9, minute=42))
    assert len(calls) == 0                                     # within 5 min of the startup reconcile
    s._last_recon = 0
    s.tick(NOW.replace(hour=9, minute=43))
    assert len(calls) == 1


# ---- reconciliation, restart and final-entry regressions -------------------------------------
@pytest.mark.parametrize("cap, dates, losses, fee, before, after", [
    ("weekly", ["2026-10-05", "2026-10-06", "2026-10-07"], [-150, -150, -119], 5, -397, -404),
    ("monthly", ["2026-10-01", "2026-10-02", "2026-10-03"], [-270, -270, -275], 5, -793, -800),
    ("consecutive", ["2026-10-05", "2026-10-06", "2026-10-07"], [-10, -10, -10], 15, 0, 4),
])
def test_final_entry_gates_use_reconciled_fees(monkeypatch, reconnect_broker, cap, dates, losses, fee, before, after):
    ib = Broker(["fill", "fill"]); ib.fill = functools.partial(Broker.fill, ib, fee=None)
    s = session(ib); s.tick(NOW); s.tick(NOW.replace(hour=15, minute=45))
    for d, loss in zip(dates, losses):
        L.append_live({"book": "live", "date": d, "template": R.LIVE_TEMPLATE,
                       "pnl_usd": loss, "accounting_status": "complete"})
    # Explicitly wider TWS history; the default Gateway fixture cannot fetch yesterday's fees.
    ib = reconnect_broker(ib, history_days=7)
    nxt = R.Session(ib, "2026-10-09", True)
    nxt.st["live_session"] = dict(s.st["live_session"])
    for f in ib.history:
        f.commissionReport.execId = f.execution.execId
        f.commissionReport.commission = fee
    snapshots = []; pauses = []
    gates = risk.live_gates
    def observe(env, ledger, ctx):
        metric = {"weekly": lambda: risk.week_pnl(ledger, ctx["date"]),
                  "monthly": lambda: risk.month_pnl(ledger, ctx["date"]),
                  "consecutive": lambda: risk.consecutive_losses(ledger)}[cap]
        snapshots.append(metric())
        return gates(env, ledger, ctx)
    monkeypatch.setattr(risk, "live_gates", observe)
    monkeypatch.setattr(R, "_set_envelope", lambda **kw: pauses.append(kw))
    nxt.tick(NOW.replace(day=9))
    assert snapshots == [before, after]
    assert cap in nxt.lv["last_why"] and not ib.orders
    assert bool(pauses) == (cap != "weekly")


def manual_fill(ib, contract=None, account="FAKE"):
    fill = copy.deepcopy(ib.executions[0])
    fill.execution.execId = "manual.1"
    fill.execution.orderRef = "MANUAL"
    fill.execution.acctNumber = account
    fill.execution.side = "SLD"
    fill.execution.price = -1.5
    fill.commissionReport.execId = "manual.1"
    if contract is not None:
        fill.contract = contract
    ib.executions.append(fill)
    return fill


@pytest.mark.parametrize("kind", ["leg", "bag", "unknown_combo"])
def test_external_evidence_survives_midnight_and_reconnect(reconnect_broker, kind):
    ib = Broker(["fill"]); s = session(ib); s.tick(NOW)
    contract = None
    if kind == "leg":
        contract = NS(conId=s.lv["legs"]["sp"]["conId"], secType="OPT")
    elif kind == "unknown_combo":
        contract = NS(conId=0, secType="BAG", symbol="XSP", comboLegs=[])
    manual_fill(ib, contract)
    ib.quantities.clear()
    assert not s._reconcile_live(force=True)
    assert S.load_state(DATE)["live"]["external_executions"]["manual.1"]["order_ref"] == "MANUAL"
    # Both executions are now unavailable; only the saved evidence prevents false expiry P&L.
    ib = reconnect_broker(ib)
    ib.reqHistoricalData = lambda *a, **k: [NS(date=dt.date(2026, 10, 8), close=680.0)]
    nxt = R.Session(ib, "2026-10-09", True)
    nxt.st["live_session"] = dict(s.st["live_session"])
    nxt.tick(NOW.replace(day=9))
    assert ib.fills() == [] and not ib.orders
    prior = S.load_state(DATE)["live"]
    assert "external" in prior["reconciliation_error"] and "settlement" not in prior
    row = next(r for r in L.read_live() if r["date"] == DATE)
    assert row["pnl_usd"] is None and row["accounting_status"] == "pending_execution"


def test_legacy_external_error_is_not_cleared_by_empty_history(reconnect_broker):
    ib = Broker(["fill"]); s = session(ib); s.tick(NOW)
    s.lv.pop("external_executions", None)
    s.lv["reconciliation_error"] = "1 external execution(s) on condor legs (manual close?) — reconcile by hand"
    S.save_state(s.st)
    ib.quantities.clear(); ib = reconnect_broker(ib)
    R.Session(ib, "2026-10-09", True)
    prior = S.load_state(DATE)["live"]
    assert "legacy" in prior["external_executions"] and "external" in prior["reconciliation_error"]


@pytest.mark.parametrize("other_account, missing_legs", [(False, False), (True, False), (False, True)])
def test_unrelated_combo_does_not_block(other_account, missing_legs):
    ib = Broker(["fill"]); s = session(ib); s.tick(NOW)
    f = manual_fill(ib, account="OTHER" if other_account else "FAKE")
    if not other_account:
        f.contract.comboLegs = [NS(conId=99999)]
    if missing_legs:
        # An execution without legs can be resolved from its account-scoped permanent order ID.
        tr = copy.deepcopy(ib.orders[0]); tr.contract = copy.deepcopy(f.contract)
        tr.order.account = "FAKE"; tr.order.orderRef = "MANUAL"; tr.order.permId = 444
        ib.orders.append(tr); f.execution.permId = 444; f.contract.comboLegs = []
    assert s._reconcile_live(force=True)
    assert not s.lv["external_executions"] and s.lv["status"] == "OPEN"


@pytest.mark.parametrize("terminal", ["NO_FILL", "CLOSED", "EXPIRED_SETTLED"])
def test_terminal_checkpoint_replays_failed_ledger_write(monkeypatch, reconnect_broker, terminal):
    ib = Broker(["pending"] if terminal == "NO_FILL" else ["fill", "fill"])
    s = session(ib); s.tick(NOW)
    old = L.read_live()[0]
    assert old["accounting_status"] == "pending_execution"
    if terminal == "NO_FILL":
        ib.orders[0].orderStatus.status = "Cancelled"
    elif terminal == "EXPIRED_SETTLED":
        ib.quantities.clear()
        monkeypatch.setattr(L, "_now_et", lambda: NOW.replace(hour=16, minute=30))
        ib.reqHistoricalData = lambda *a, **k: [NS(date=dt.date(2026, 10, 8), close=680.0)]
    append = R.append_live
    def fail_terminal(row):
        if row["accounting_status"] != "pending_execution":
            raise OSError("ledger unavailable after checkpoint")
        append(row)
    with monkeypatch.context() as patch:
        patch.setattr(R, "append_live", fail_terminal)
        with pytest.raises(OSError, match="ledger unavailable"):
            if terminal == "CLOSED":
                s.tick(NOW.replace(hour=15, minute=45))
            else:
                s._reconcile_live(force=True)
    saved = S.load_state(DATE)["live"]
    assert saved["status"] == ("NO_FILL" if terminal == "NO_FILL" else "CLOSED")
    assert L.read_live()[0]["accounting_status"] == "pending_execution"
    ib = reconnect_broker(ib)
    R.Session(ib, "2026-10-09", True)
    R.Session(ib, "2026-10-09", True)      # repeated recovery stays idempotent
    assert L.read_live() == [saved["ledger_row"]]
    assert not ib.orders and not ib.fills()


@pytest.mark.parametrize("terminal", ["NO_FILL", "CLOSED"])
@pytest.mark.parametrize("missing_row", [False, True])
def test_pre_upgrade_terminal_checkpoint_repairs_ledger(reconnect_broker, terminal, missing_row):
    ib = Broker(["cancel"] if terminal == "NO_FILL" else ["fill", "fill"])
    s = session(ib); s.tick(NOW)
    if terminal == "CLOSED":
        s.tick(NOW.replace(hour=15, minute=45))
    expected = L.read_live()[0]
    s.lv.pop("ledger_row")                 # model the older checkpoint format
    S.save_state(s.st)
    if missing_row:
        L.LIVE_LEDGER.unlink()
    else:
        L.append_live({**expected, "pnl_usd": None, "accounting_status": "pending_execution"})
    ib = reconnect_broker(ib)
    R.Session(ib, "2026-10-09", True)
    row = L.read_live()[0]
    assert row["accounting_status"] == "complete" and row["pnl_usd"] == expected["pnl_usd"]
    assert row["reason"] == expected["reason"] and not ib.orders


def test_recovery_keeps_external_block_even_if_broker_is_unavailable(reconnect_broker):
    ib = Broker(["fill", "fill"]); s = session(ib)
    s.tick(NOW); s.tick(NOW.replace(hour=15, minute=45))
    # An older checkpoint records the external incident but still has its earlier ledger row.
    s.lv["reconciliation_error"] = "external execution on condor legs; reconcile by hand"
    S.save_state(s.st)
    ib = reconnect_broker(ib)
    def unavailable():
        assert L.read_live()[0]["accounting_status"] == "pending_execution"
        raise TimeoutError("broker unavailable")
    ib.reqAllOpenOrders = unavailable
    with pytest.raises(TimeoutError):
        R.Session(ib, "2026-10-09", True)
    assert L.read_live()[0]["pnl_usd"] is None


# ---- 2026-10-07 third review (two gaps) ---------------------------------------------------------
def _external_close(ib, s):
    sp = s.lv["legs"]["sp"]["conId"]
    ib.executions.append(NS(execution=NS(execId="manual.1", acctNumber="FAKE", orderRef="", time=NOW, shares=1, price=1.5, side="BOT"),
                            contract=NS(conId=sp, secType="OPT"), commissionReport=NS(execId="manual.1", commission=0.65, currency="USD")))
    ib.quantities.clear()


def test_manual_resolve_books_statement_values_and_clears_the_block(monkeypatch):
    ib = Broker(["fill"]); s = session(ib); s.tick(NOW)
    _external_close(ib, s)
    monkeypatch.setattr(L, "_now_et", lambda: dt.datetime(2026, 10, 8, 16, 30, tzinfo=C.ET))
    ib.reqHistoricalData = lambda *a, **k: [NS(date=dt.date(2026, 10, 8), close=680.0)]
    assert not s._reconcile_live(force=True) and s.lv["external_executions"]
    row = R.resolve(DATE, exit_cost=1.5, fees=3.25, note="stmt 2026-10-08: bought back 672P by hand 14:12", by="test")
    lv = S.load_state(DATE)["live"]
    assert lv["status"] == "CLOSED" and lv["exit_reason"] == "MANUAL_CLOSE" and not lv["external_executions"] and "reconciliation_error" not in lv
    assert lv["manual_resolution"]["by"] == "test" and lv["manual_resolution"]["prior_status"] == "OPEN" and lv["manual_resolution"]["external_executions"]
    assert row["accounting_status"] == "complete" and row["pnl_usd"] == round((0.35 - 1.5) * 100 - 3.25, 2) and row["manual_resolution"]["note"].startswith("stmt")
    assert len([r for r in L.read_live() if r["date"] == DATE]) == 1
    # the next session finds nothing to do and the gates are open (the loss counts at net)
    monkeypatch.setattr(L, "_now_et", lambda: dt.datetime(2026, 10, 9, 9, 28, tzinfo=C.ET))
    nxt = R.Session(ib, "2026-10-09", True)
    assert nxt._prior_unresolved == 0 and S.load_state(DATE)["live"]["status"] == "CLOSED"
    ctx = {"date": "2026-10-09", "calendar_verified": True, "vix1d_now": 18., "first30_range": .005}
    ok, reasons, _ = risk.live_gates(R._envelope(), L.read_live(), ctx)
    assert ok, reasons
    assert risk.week_pnl(L.read_live(), "2026-10-09") == -118.25


def test_manual_resolve_refuses_clean_sessions_and_requires_a_note():
    ib = Broker(["fill"]); s = session(ib); s.tick(NOW)
    with pytest.raises(SystemExit):
        R.resolve(DATE, exit_cost=1.5, fees=3.25, note="")
    ib2 = Broker(); s2 = session(ib2)
    with pytest.raises(SystemExit):
        R.resolve("2026-10-09", exit_cost=0.1, fees=1.0, note="nothing here")


def test_manual_resolve_needs_a_credit_when_no_fill_was_reconciled():
    ib = Broker(["pending"]); s = session(ib); s.tick(NOW)
    assert s.lv["status"] == "OPENING"
    with pytest.raises(SystemExit):
        R.resolve(DATE, exit_cost=0.0, fees=0.0, note="stmt: order was actually filled and expired")
    row = R.resolve(DATE, exit_cost=0.0, fees=2.6, note="stmt: filled 0.30, expired worthless", credit=0.30)
    assert row["pnl_usd"] == 27.4 and S.load_state(DATE)["live"]["status"] == "CLOSED"


def test_leg_executions_without_orderref_are_still_ours():
    ib = Broker(["fill"]); r, intents = rail(ib)
    r.open_condor(LEGS, .35, wait_s=1)
    tr = ib.orders[0]; e = ib.executions[0].execution
    e.orderRef = ""; e.orderId = tr.order.orderId; e.permId = tr.orderStatus.permId    # the reference did not survive the leg report
    result = r.reconcile({"legs": LEGS, "orders": intents}, DATE)
    assert result["ok"] and result["opened"] == 1 and not result.get("expired") and intents[0]["fills"]
    # and a foreign execution with no ids at all is still external
    _external_close(ib, NS(lv={"legs": LEGS}))
    result = r.reconcile({"legs": LEGS, "orders": intents, "status": "OPEN"}, DATE)
    assert not result["ok"] and "external" in result["why"]


def test_result_matches_fill_by_order_id_when_ref_is_blank():
    ib = Broker(["fill"]); r, _ = rail(ib)
    original = ib.fill
    def fill(tr, **kw):
        original(tr, **kw); ib.executions[-1].execution.orderRef = ""; ib.executions[-1].execution.orderId = tr.order.orderId
    ib.fill = fill
    out = r.open_condor(LEGS, .35, wait_s=1)
    assert out["status"] == "Filled" and out["filled"] == 1 and out["credit_filled"] == pytest.approx(0.35)
