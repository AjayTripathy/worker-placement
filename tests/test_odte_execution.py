"""Broker-free regressions for submission, cancellation, crash recovery and fees."""
import datetime as dt
import copy
import itertools
import json
import socket
from types import SimpleNamespace as NS

import pytest

from desk.odte import rail as L, runner as R, shadow as S, risk, doctrine as D
from desk.odte.capture import ET
from desk.odte.templates import build_condor
from test_odte import chain

DATE = '2026-10-08'
NOW = dt.datetime(2026, 10, 8, 10, 5, tzinfo=ET)
LEGS = build_condor(chain(), .1, 2)['legs']


class Broker:
    """In-memory broker with asynchronous order/cancel outcomes and real order structs."""
    def __init__(self, behaviors=()):
        self.behaviors = list(behaviors)
        self.orders = []; self.executions = []; self.quantities = {}
        self.client = NS(getReqId=itertools.count(1).__next__)
        self.connected = True
        self.before_place = None

    def placeOrder(self, bag, order):
        if self.before_place:
            self.before_place(order)
        mode = self.behaviors.pop(0) if self.behaviors else 'pending'
        tr = NS(order=order, contract=bag, mode=mode,
                orderStatus=NS(status='Submitted', filled=0., avgFillPrice=0., permId=order.orderId))
        self.orders.append(tr)
        if mode == 'fill':
            self.fill(tr)
        return tr

    def fill(self, tr, qty=None, price=None, fee=2.6):
        qty = tr.order.totalQuantity if qty is None else qty
        price = (-.35 if tr.order.action == 'BUY' else -.10) if price is None else price
        old = tr.orderStatus.filled
        tr.orderStatus.avgFillPrice = (old * tr.orderStatus.avgFillPrice + qty * price) / (old + qty)
        tr.orderStatus.filled += qty
        tr.orderStatus.status = 'Filled' if tr.orderStatus.filled == tr.order.totalQuantity else 'Submitted'
        exec_id = f'{tr.order.orderId}.{len(self.executions)}'
        ex = NS(execId=exec_id, acctNumber='FAKE', orderRef=tr.order.orderRef,
                time=NOW, shares=qty, price=price, side='BOT' if tr.order.action == 'BUY' else 'SLD')
        report = NS(execId=exec_id if fee is not None else '', commission=fee or 0., currency='USD')
        self.executions.append(NS(execution=ex, contract=tr.contract, commissionReport=report))
        for leg in tr.contract.comboLegs:
            sign = (1 if leg.action == 'BUY' else -1) * (1 if tr.order.action == 'BUY' else -1)
            self.quantities[leg.conId] = self.quantities.get(leg.conId, 0) + sign * qty

    def cancelOrder(self, order):
        tr = next(t for t in self.orders if t.order is order)
        if tr.mode == 'fill_on_cancel':
            self.fill(tr)
        elif tr.mode == 'cancel':
            tr.orderStatus.status = 'Cancelled'
        else:
            tr.orderStatus.status = 'PendingCancel'

    def sleep(self, seconds): pass
    def isConnected(self): return self.connected
    def managedAccounts(self): return ['FAKE']
    def disconnect(self): self.connected = False
    def reqAllOpenOrders(self): return self.openTrades()
    def reqCompletedOrders(self, apiOnly): return [t for t in self.orders if t.orderStatus.status in L.TERMINAL]
    def reqExecutions(self, filt): return self.executions
    def fills(self): return self.executions
    def trades(self): return self.orders
    def openTrades(self): return [t for t in self.orders if t.orderStatus.status not in L.TERMINAL]
    def reqPositions(self):
        return [NS(account='FAKE', position=q, contract=NS(conId=k, symbol='XSP',
                   lastTradeDateOrContractMonth='20261008')) for k, q in self.quantities.items() if q]
    def whatIfOrder(self, bag, order):
        return NS(initMarginChange='100', maintMarginChange='100', commission='2.60', status='', warningText='')


class FreshBroker(Broker):
    """New connection, empty local cache, and a separate server execution history.

    The default models Gateway's since-midnight execution query. history_days=7
    explicitly models a TWS Trade Log configured to expose older executions.
    Completed-order replies must be supplied explicitly; we never inherit the
    old connection's completed-trade cache.
    """
    def __init__(self, source, now, *, history_days=1, completed=(), behaviors=()):
        super().__init__(behaviors)
        self.now = now
        self.history_days = history_days
        self.history = copy.deepcopy(getattr(source, 'history', source.executions))
        self.quantities = copy.deepcopy(source.quantities)
        self.orders = copy.deepcopy(source.openTrades() + list(completed))
        self.client = NS(getReqId=itertools.count(1000).__next__)
        self.expiries = {k: DATE.replace('-', '') for k in self.quantities}

    def reqExecutions(self, filt):
        cutoff = self.now.replace(hour=0, minute=0, second=0, microsecond=0) - dt.timedelta(days=self.history_days - 1)
        found = [copy.deepcopy(f) for f in self.history
                 if cutoff <= f.execution.time <= self.now and f.execution.acctNumber == filt.acctCode]
        cached = {f.execution.execId: f for f in self.executions}
        cached.update({f.execution.execId: f for f in found})
        self.executions = list(cached.values())
        return found

    def fill(self, tr, qty=None, price=None, fee=2.6):
        super().fill(tr, qty, price, fee)
        self.executions[-1].execution.time = self.now
        self.history.append(copy.deepcopy(self.executions[-1]))
        for leg in tr.contract.comboLegs:
            self.expiries[leg.conId] = self.now.strftime('%Y%m%d')

    def reqPositions(self):
        return [NS(account='FAKE', position=q, contract=NS(conId=k, symbol='XSP',
                   lastTradeDateOrContractMonth=self.expiries[k])) for k, q in self.quantities.items() if q]


@pytest.fixture
def reconnect_broker(monkeypatch):
    def connect(source, now=NOW.replace(day=9, hour=9, minute=28), **kwargs):
        monkeypatch.setattr(L, '_now_et', lambda: now)
        fresh = FreshBroker(source, now, **kwargs)
        assert fresh.fills() == []
        return fresh
    return connect


class Capture:
    def __init__(self, *args): pass
    def _spot(self): return 680.
    def ensure_band(self, spot): pass
    def maybe_fallback_delayed(self): pass
    def close(self): pass
    @staticmethod
    def write(*args): pass
    def snapshot(self, now):
        return {'ts': now.isoformat(), 'rows': [dict(r, live_eligible=True) for r in chain()],
                'spx': 6800., 'xsp': 680., 'vix1d': 18., 'data_type': 'live', 'indices_live': True}


@pytest.fixture(autouse=True)
def isolation(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs): raise AssertionError('No sockets allowed in ODTE execution tests')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(R, '_mail', lambda *a: None)
    monkeypatch.setattr(R, 'ChainCapture', Capture)
    monkeypatch.setattr(R, '_halted', lambda: None)
    monkeypatch.setattr(R, 'HALT_FILE', tmp_path / 'HALT')
    monkeypatch.setattr(R, 'LOCK_FILE', tmp_path / 'lock')
    monkeypatch.setattr(R, 'DATA', tmp_path)
    monkeypatch.setattr(L, 'DATA', tmp_path)
    monkeypatch.setattr(L, 'LIVE_LEDGER', tmp_path / 'live.jsonl')
    monkeypatch.setattr(S, 'DATA', tmp_path)
    monkeypatch.setattr(S, 'SHADOW_LEDGER', tmp_path / 'shadow.jsonl')
    monkeypatch.setattr(R.cal, 'EVENT_CALENDAR', tmp_path / 'event_calendar.json')
    monkeypatch.setattr(R.cal, 'is_event_day', lambda date: False)
    monkeypatch.setattr(R.cal, 'calendar_verified_for', lambda date: True)
    monkeypatch.setattr(R, '_envelope', lambda: {'status': 'ARMED', 'origin': 'signalos_desk+principal', 'expires': '2026-12-31'})
    monkeypatch.setattr('desk.account_registry.require_alpha', lambda ib: 'FAKE')
    # These suites test the RAIL mechanics on an unconditional T3 taker entry. The 2026-10-08 live
    # policy (follow the sealed arm decision, maker execution) has its own suite: test_odte_live_policy.
    monkeypatch.setattr(R, 'LIVE_POLICY', {'follow': 'template', 'fallback': 'stand_down', 'execution': 'taker'})


def rail(ib):
    intents = []
    out = L.LiveRail(ib, 'FAKE', date=DATE, checkpoint=intents.append)
    out.margin_checked = True
    return out, intents


def session(ib):
    if not S._state_path(DATE).exists():
        st = S.load_state(DATE)
        st['session'] = {'spx_open': 6800., 'spx_hi30': 6805., 'spx_lo30': 6800., 'vix1d_open': 18.}
        st['live_session'] = dict(st['session'])
        S.save_state(st)
    return R.Session(ib, DATE, True)


def test_late_entry_fill_is_not_lost():
    ib = Broker(['fill_on_cancel']); r, intents = rail(ib)
    result = r.open_condor(LEGS, .35, wait_s=1)
    assert result['status'] == 'Filled' and result['filled'] == 1
    live = {'legs': LEGS, 'orders': intents}
    reconciled = r.reconcile(live, DATE)
    assert reconciled['ok'] and reconciled['remaining'] == 1 and not reconciled['pending']


def test_late_close_fill_does_not_send_replacement():
    ib = Broker(['fill_on_cancel']); r, _ = rail(ib)
    result = r.close_condor(LEGS, .10, wait_s=1)
    assert len(ib.orders) == 1 and result['filled_total'] == 1


def test_unacknowledged_cancel_prevents_replacement():
    ib = Broker(['pending']); r, _ = rail(ib)
    result = r.close_condor(LEGS, .10, wait_s=1)
    assert len(ib.orders) == 1 and result['status'] == 'PendingCancel'
    assert result['debit_paid'] is None


def test_market_exit_remains_pending_until_execution():
    ib = Broker(['fill', 'cancel', 'cancel', 'pending']); s = session(ib)
    s.tick(NOW)
    assert s.lv['status'] == 'OPEN'
    s.tick(NOW.replace(hour=15, minute=45))
    assert s.lv['status'] == 'CLOSING' and L.read_live()[0]['pnl_usd'] is None
    s.tick(NOW.replace(hour=15, minute=46))
    assert len(ib.orders) == 4  # no duplicate closes on the next tick
    ib.fill(ib.orders[-1])
    s.tick(NOW.replace(hour=15, minute=47))
    row = L.read_live()[0]
    assert s.lv['status'] == 'CLOSED'
    assert row['gross_pnl_usd'] == 25 and row['pnl_usd'] == 19.8


def test_partial_cancel_replacement_uses_remaining_quantity():
    ib = Broker(['cancel', 'fill']); r, _ = rail(ib)
    original = ib.placeOrder
    def place(bag, order):
        tr = original(bag, order)
        if len(ib.orders) == 1:
            ib.fill(tr, qty=.5, price=-.10)
        return tr
    ib.placeOrder = place
    result = r.close_condor(LEGS, .10, wait_s=1)
    assert [t.order.totalQuantity for t in ib.orders] == [1, .5]
    assert result['filled_total'] == 1


def test_durable_intent_precedes_submission():
    ib = Broker(['fill']); s = session(ib)
    def verify(order):
        saved = S.load_state(DATE)['live']
        assert saved['status'] == 'OPENING'
        assert saved['legs'] and saved['orders'][0]['ref'] == order.orderRef
    ib.before_place = verify
    s.tick(NOW)
    assert s.lv['status'] == 'OPEN'


def test_checkpoint_failure_prevents_order(monkeypatch):
    ib = Broker(); s = session(ib)
    original = S.save_state
    def fail_intent(st):
        if st.get('live', {}).get('orders'):
            raise OSError('checkpoint failed')
        original(st)
    monkeypatch.setattr(S, 'save_state', fail_intent)
    with pytest.raises(OSError): s.tick(NOW)
    assert not ib.orders


def test_restart_after_fill_and_failed_checkpoint_does_not_reenter(monkeypatch):
    ib = Broker(['fill']); s = session(ib)
    original = S.save_state
    def fail_after_fill(st):
        if ib.orders: raise OSError('save after broker fill failed')
        original(st)
    with monkeypatch.context() as patcher:
        patcher.setattr(S, 'save_state', fail_after_fill)
        with pytest.raises(OSError): s.tick(NOW)
    assert S.load_state(DATE)['live']['status'] == 'OPENING'
    restarted = session(ib)
    assert restarted.lv['status'] == 'OPEN'
    restarted.tick(NOW)
    assert sum(t.order.action == 'BUY' for t in ib.orders) == 1


def test_unknown_submission_stays_unresolved_after_restart():
    ib = Broker(); s = session(ib)
    s.lv['legs'] = LEGS
    s._journal_order({'ref': f'{D.ENVELOPE}:{DATE}:unknown', 'order_id': 999,
                      'action': 'BUY', 'quantity': 1., 'filled': 0., 'status': 'INTENT', 'fills': {}})
    restarted = session(ib)
    restarted.tick(NOW)
    assert restarted.lv['status'] == 'OPENING' and not ib.orders


def test_orphan_broker_position_blocks_new_entry():
    ib = Broker(); ib.quantities[12345] = -1
    s = session(ib); s.tick(NOW)
    assert s.lv['reconciliation_error'] and not ib.orders


def test_orphan_broker_fill_blocks_new_entry():
    ib = Broker(['fill']); r, _ = rail(ib)
    r.open_condor(LEGS, .35, wait_s=1)
    s = session(ib); s.tick(NOW)
    assert s.lv['reconciliation_error'] and len(ib.orders) == 1


def test_late_commissions_update_ledger_once_and_reduce_loss_budget():
    ib = Broker(['pending', 'pending']); s = session(ib)
    s.tick(NOW)
    ib.fill(ib.orders[0], fee=None)
    s.tick(NOW.replace(hour=15, minute=45))
    ib.fill(ib.orders[1], fee=None)
    s.tick(NOW.replace(hour=15, minute=46))
    row = L.read_live()[0]
    assert row['gross_pnl_usd'] == 25 and row['pnl_usd'] is None
    assert row['accounting_status'] == 'pending_fees'
    ctx = {'date': DATE, 'calendar_verified': True, 'vix1d_now': 18., 'first30_range': .005}
    # a CLOSED trade awaiting its fee report does not lock the rail; it counts at gross in the caps
    assert not any('unresolved' in reason for reason in risk.live_gates(R._envelope(), [row], ctx)[1])
    assert risk.week_pnl([row], DATE) == 22            # gross 25 minus the $3 reserve for the missing fee reports
    for f in ib.executions:
        f.commissionReport.execId = f.execution.execId
        f.commissionReport.commission = 15.
    s.tick(NOW.replace(hour=15, minute=47))
    s.tick(NOW.replace(hour=15, minute=48))
    assert len(L.read_live()) == 1
    row = L.read_live()[0]
    assert row['pnl_usd'] == -5 and risk.week_pnl([row], DATE) == -5
    assert row['accounting_status'] == 'complete'


def test_leg_and_bag_commissions_not_double_counted():
    order = {'action': 'BUY', 'fills': {}}
    for key, price, side in [('sp', .30, 'SLD'), ('lp', .10, 'BOT'), ('sc', .25, 'SLD'), ('lc', .10, 'BOT')]:
        order['fills'][key] = {'sec_type': 'OPT', 'con_id': LEGS[key]['conId'], 'quantity': 1.,
                              'price': price, 'side': side, 'commission': .65}
    order['fills']['bag'] = {'sec_type': 'BAG', 'quantity': 1., 'price': -.35, 'commission': 2.6}
    quantity, price, fees, complete = L.execution_totals(order, LEGS)
    assert quantity == 1 and price == pytest.approx(.35) and fees == 2.6 and complete


def test_reconnect_rebuilds_session(monkeypatch):
    old, new = Broker(), Broker()
    ticks = []
    class Clock(dt.datetime):
        @classmethod
        def now(cls, tz=None): return NOW
    class Session:
        def __init__(self, ib, date, live): self.ib = ib; self.date = date; self.cap = Capture()
        def tick(self, now): ticks.append(self.ib)
    def sleep_old(seconds): old.connected = False
    def sleep_new(seconds): raise KeyboardInterrupt
    old.sleep = sleep_old; new.sleep = sleep_new
    connects = iter([old, new])
    monkeypatch.setattr(R, '_lock', lambda: True)
    monkeypatch.setattr(R, 'freeze', lambda: None)
    monkeypatch.setattr(R, '_connect', lambda **kw: next(connects))
    monkeypatch.setattr(R, 'Session', Session)
    monkeypatch.setattr(R.dt, 'datetime', Clock)
    R.daemon(True)
    assert ticks == [old, new]


def test_executions_recover_fill_even_without_filled_status():
    ib = Broker(['fill']); r, intents = rail(ib)
    r.open_condor(LEGS, .35, wait_s=1)
    ib.orders[0].orderStatus.status = 'Submitted'
    result = r.reconcile({'legs': LEGS, 'orders': intents}, DATE)
    assert result['ok'] and result['remaining'] == 1 and not result['pending']


def test_filled_status_without_executions_is_unresolved():
    ib = Broker(['fill']); r, intents = rail(ib)
    r.open_condor(LEGS, .35, wait_s=1)
    ib.executions.clear()
    result = r.reconcile({'legs': LEGS, 'orders': intents}, DATE)
    assert not result['ok'] and 'execution details' in result['why']


def test_duplicate_execution_delivery_does_not_double_count():
    ib = Broker(['fill']); r, intents = rail(ib)
    r.open_condor(LEGS, .35, wait_s=1)
    ib.executions.append(ib.executions[0])
    result = r.reconcile({'legs': LEGS, 'orders': intents}, DATE)
    assert result['ok'] and result['opened'] == 1 and result['commissions'] == 2.6


def test_broker_account_isolation():
    ib = Broker(['fill']); r, _ = rail(ib)
    r.open_condor(LEGS, .35, wait_s=1)
    ib.orders[0].order.account = 'OTHER'
    ib.executions[0].execution.acctNumber = 'OTHER'
    positions = ib.reqPositions()
    for p in positions: p.account = 'OTHER'
    ib.reqPositions = lambda: positions
    result = r.reconcile({'status': 'NONE'}, DATE)
    assert result['ok'] and result['remaining'] == 0 and result['opened'] == 0
    assert r.cancel_all_ours() == 0


def test_wrong_position_quantity_blocks_order_management():
    ib = Broker(['fill']); s = session(ib); s.tick(NOW)
    ib.quantities[LEGS['sp']['conId']] = -2
    s.tick(NOW.replace(hour=15, minute=45))
    assert 'positions' in s.lv['reconciliation_error']
    assert len(ib.orders) == 1
    assert L.read_live()[0]['accounting_status'] == 'pending_execution'


def test_pending_exit_survives_restart_without_replacement():
    ib = Broker(['fill', 'pending']); s = session(ib); s.tick(NOW)
    s.tick(NOW.replace(hour=15, minute=45))
    restarted = session(ib)
    restarted.tick(NOW.replace(hour=15, minute=46))
    assert restarted.lv['status'] == 'CLOSING' and len(ib.orders) == 2


def test_live_risk_baseline_cannot_come_from_delayed_shadow_data():
    ib = Broker(); s = session(ib)
    s.st['live_session'] = {}
    snap = Capture().snapshot(NOW)
    snap.update(indices_live=False, data_type='delayed')
    s.cap.snapshot = lambda now: snap
    s.tick(NOW.replace(hour=9, minute=45))
    snap.update(indices_live=True, data_type='live')
    s.tick(NOW)
    assert not ib.orders and 'first-30' in s.lv['last_why']


def test_legacy_gross_ledger_is_not_silently_net():
    L.LIVE_LEDGER.write_text(json.dumps({'date': DATE, 'template': D.LIVE_TEMPLATE, 'pnl_usd': 25}) + '\n')
    row = L.read_live()[0]
    assert row['gross_pnl_usd'] == 25 and row['pnl_usd'] is None
    assert row['accounting_status'] == 'pending_legacy'


def test_live_expiry_does_not_book_estimated_settlement():
    ib = Broker(['fill']); s = session(ib); s.tick(NOW)
    s._finish_live(Capture().snapshot(NOW))
    row = L.read_live()[0]
    assert s.lv['status'] == 'OPEN' and row['pnl_usd'] is None
    assert row['accounting_status'] == 'pending_execution'


def test_only_one_daemon_can_own_checkpoint_lock():
    try:
        assert R._lock()
        assert not R._lock()
    finally:
        R._unlock()
    assert R.LOCK_FILE.exists() and R.LOCK_FILE.read_text() == ''
    assert R._lock()
    R._unlock()


def test_crash_before_reply_also_blocks_next_day_entry(monkeypatch):
    ib = Broker(['fill']); s = session(ib)
    original = S.save_state
    def fail_after_fill(st):
        if ib.orders: raise OSError('checkpoint after fill failed')
        original(st)
    monkeypatch.setattr(S, 'save_state', fail_after_fill)
    with pytest.raises(OSError): s.tick(NOW)
    pending = L.read_live()
    assert pending[0]['accounting_status'] == 'pending_execution'
    ctx = {'date': '2026-10-09', 'calendar_verified': True, 'vix1d_now': 18., 'first30_range': .005}
    assert any('accounting' in reason for reason in risk.live_gates(R._envelope(), pending, ctx)[1])


def test_cancel_reply_with_stale_fill_count_uses_execution_details():
    ib = Broker(['fill_on_cancel']); r, _ = rail(ib)
    original = ib.cancelOrder
    def cancel(order):
        original(order)
        tr = ib.orders[0]
        tr.orderStatus.status = 'Cancelled'
        tr.orderStatus.filled = 0.
        tr.orderStatus.avgFillPrice = 0.
    ib.cancelOrder = cancel
    result = r.close_condor(LEGS, .10, wait_s=1)
    assert result['filled_total'] == 1 and len(ib.orders) == 1
