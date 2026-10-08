"""Maker permission, crash recovery and research-lineage regressions; no broker IO."""
import datetime as dt

import pytest

from desk.odte import runner as R, rail as L, templates as T, shadow as S, arms as A
from test_odte import chain
from test_odte_execution import Broker, session, DATE, NOW, isolation  # noqa: F401
from test_odte_live_policy import live_policy, seal_decision  # noqa: F401


@pytest.mark.parametrize('delay', [1, 3])
@pytest.mark.parametrize('gate', ['halt', 'vix_jump', 'paused_envelope', 'stale_quotes', 'weekly_cap'])
def test_maker_does_not_repost_after_entry_permission_is_lost(live_policy, tmp_path, monkeypatch, gate, delay):
    legs = T.build_condor(chain(), .1, 2)['legs']
    seal_decision(tmp_path, monkeypatch, legs)
    ib = Broker(['cancel', 'cancel'])
    s = session(ib)
    s.tick(NOW)
    original = s.cap.snapshot
    if gate == 'halt':
        monkeypatch.setattr(R, '_halted', lambda: 'operator requested halt')
    elif gate == 'paused_envelope':
        monkeypatch.setattr(R, '_envelope', lambda: {'status': 'PAUSED', 'origin': 'signalos_desk+principal'})
    elif gate == 'weekly_cap':
        L.append_live({'date': '2026-10-07', 'template': R.LIVE_TEMPLATE, 'pnl_usd': -500., 'accounting_status': 'complete'})
    else:
        def changed(now):
            snap = original(now)
            if gate == 'vix_jump':
                snap['vix1d'] = 30.
            else:
                snap['indices_live'] = False
                for row in snap['rows']:
                    row['live_eligible'] = False
            return snap
        monkeypatch.setattr(s.cap, 'snapshot', changed)
    s.tick(NOW + dt.timedelta(minutes=delay))
    assert len(ib.orders) == 1, f'{gate}: posted another opening order after the gate failed'
    assert not ib.openTrades(), 'Unsafe entry remains resting during patience'
    assert s.lv['status'] == 'NO_FILL' and s.lv['maker']['finished']


def test_maker_crash_after_submit_is_recoverable(live_policy, tmp_path, monkeypatch):
    class SimulatedCrash(BaseException):
        pass
    legs = T.build_condor(chain(), .1, 2)['legs']
    seal_decision(tmp_path, monkeypatch, legs)
    ib = Broker(['cancel'])
    s = session(ib)
    audit = L._audit
    def crash_after_post(kind, row):
        if kind == 'POST_OPEN':
            raise SimulatedCrash()
        return audit(kind, row)
    monkeypatch.setattr(L, '_audit', crash_after_post)
    with pytest.raises(SimulatedCrash):
        s.tick(NOW)
    assert len(ib.openTrades()) == 1
    monkeypatch.setattr(L, '_audit', audit)
    resumed = session(ib)
    resumed.tick(NOW + dt.timedelta(minutes=3))
    assert not R.HALT_FILE.exists(), R.HALT_FILE.read_text()
    assert len(ib.orders) == 2 and ib.orders[0].orderStatus.status == 'Cancelled'
    assert resumed.lv['maker']['attempt'] == 2


def test_legacy_checkpoint_recovers_outstanding_reference_and_cancels(live_policy, tmp_path, monkeypatch):
    legs = T.build_condor(chain(), .1, 2)['legs']
    seal_decision(tmp_path, monkeypatch, legs)
    ib = Broker(['cancel'])
    s = session(ib); s.tick(NOW)
    saved = S.load_state(DATE)
    saved['live']['maker'].pop('last_order')
    saved['live']['maker'].pop('posted_at')
    saved['live']['maker']['attempt'] = 0
    S.save_state(saved)
    resumed = session(ib); resumed.tick(NOW + dt.timedelta(minutes=1))
    assert not R.HALT_FILE.exists()
    assert not ib.openTrades() and len(ib.orders) == 1
    assert 'incomplete maker checkpoint' in resumed.lv['why']


def test_crash_before_broker_submission_never_resends_unacknowledged_intent(live_policy, tmp_path, monkeypatch):
    class SimulatedCrash(BaseException):
        pass
    legs = T.build_condor(chain(), .1, 2)['legs']
    seal_decision(tmp_path, monkeypatch, legs)
    ib = Broker()
    def crash(order):
        raise SimulatedCrash()
    ib.before_place = crash
    s = session(ib)
    with pytest.raises(SimulatedCrash):
        s.tick(NOW)
    ib.before_place = None
    resumed = session(ib); resumed.tick(NOW + dt.timedelta(minutes=3))
    assert not ib.orders
    assert resumed.lv['status'] == 'OPENING'
    assert len(resumed.lv['orders']) == 1


def test_halt_during_cancel_forbids_repost(live_policy, tmp_path, monkeypatch):
    legs = T.build_condor(chain(), .1, 2)['legs']
    seal_decision(tmp_path, monkeypatch, legs)
    ib = Broker(['cancel', 'cancel'])
    s = session(ib); s.tick(NOW)
    cancel = ib.cancelOrder
    def halt_on_cancel(order):
        cancel(order)
        monkeypatch.setattr(R, '_halted', lambda: 'halt during acknowledgement')
    monkeypatch.setattr(ib, 'cancelOrder', halt_on_cancel)
    s.tick(NOW + dt.timedelta(minutes=3))
    assert len(ib.orders) == 1 and s.lv['maker']['finished']


def test_halt_latches_through_unacknowledged_cancel_and_restart(live_policy, tmp_path, monkeypatch):
    legs = T.build_condor(chain(), .1, 2)['legs']
    seal_decision(tmp_path, monkeypatch, legs)
    ib = Broker(['pending'])
    s = session(ib); s.tick(NOW)
    monkeypatch.setattr(R, '_halted', lambda: 'halt while entry rests')
    s.tick(NOW + dt.timedelta(minutes=1))
    assert ib.orders[0].orderStatus.status == 'PendingCancel'
    monkeypatch.setattr(R, '_halted', lambda: None)
    ib.orders[0].mode = 'cancel'
    resumed = session(ib); resumed.tick(NOW + dt.timedelta(minutes=3))
    assert not ib.openTrades() and len(ib.orders) == 1
    assert resumed.lv['maker']['finished']


def test_fill_during_halt_cancellation_is_managed_on_same_tick(live_policy, tmp_path, monkeypatch):
    legs = T.build_condor(chain(), .1, 2)['legs']
    seal_decision(tmp_path, monkeypatch, legs)
    ib = Broker(['fill_on_cancel', 'fill'])
    s = session(ib); s.tick(NOW)
    monkeypatch.setattr(R, '_halted', lambda: 'halt while entry rests')
    s.tick(NOW + dt.timedelta(minutes=1))
    assert [o.order.action for o in ib.orders] == ['BUY', 'SELL']
    assert s.lv['status'] == 'CLOSED' and s.lv['exit_reason'].startswith('KILL:HALT')


def test_entry_window_end_cancels_before_patience_expires(live_policy, tmp_path, monkeypatch):
    legs = T.build_condor(chain(), .1, 2)['legs']
    seal_decision(tmp_path, monkeypatch, legs)
    ib = Broker(['cancel'])
    s = session(ib); s.tick(NOW)
    s.lv['maker']['posted_at'] = NOW.replace(minute=20).isoformat()
    s.tick(NOW.replace(minute=21))
    assert len(ib.orders) == 1 and not ib.openTrades()
    assert s.lv['maker']['finished']


@pytest.mark.parametrize('change', ['time', 'snapshot', 'credit'])
def test_sealed_entry_must_match_all_lineage_fields(live_policy, tmp_path, monkeypatch, change):
    legs = T.build_condor(chain(), .1, 2)['legs']
    seal_decision(tmp_path, monkeypatch, legs)
    s = session(Broker())
    snap = s.cap.snapshot(NOW); c = T.build_condor(snap['rows'], .1, 2)
    if change == 'time':
        snap['ts'] = (NOW + dt.timedelta(minutes=1)).isoformat()
    elif change == 'snapshot':
        snap['vix1d'] += .1
    else:
        c['credit'] += .1
    assert not s._arm_decision(c, snap)['take']


def test_late_entry_does_not_reuse_gate_from_different_quotes(live_policy, tmp_path, monkeypatch):
    old = T.build_condor(chain(), .1, 2)
    root = S.DATA / 'arm_experiment'
    monkeypatch.setattr(A, 'protocol', lambda root: {'protocol': 'p', 'arms': {'T7': {'label': 'execution'}}})
    A.seal(root/'decisions'/(DATE+'.json'), {
        'protocol': 'p', 'date': DATE, 'entry_at': NOW.isoformat(), 'candidate': old,
        'arms': {'T7': {'decision': 'take'}}, 'allocation': {'selected_arm': 'T7'},
        'gates': {'execution': {'pass': True}}})
    rows = chain()
    for row in rows:
        if (row['right'], row['strike']) in [('P', old['legs']['sp']['strike']), ('C', old['legs']['sc']['strike'])]:
            row['bid'] -= .20
    current = T.build_condor(rows, .1, 2)
    assert current['ok'] and current['credit'] != old['credit']
    assert sum(r['ask']-r['bid'] for r in current['legs'].values())/current['credit'] > .5
    ib = Broker(['cancel'])
    s = session(ib)
    now = NOW + dt.timedelta(minutes=3)
    snap = s.cap.snapshot(now)
    snap['rows'] = [dict(row, live_eligible=True) for row in rows]
    S.update_session(s.st['live_session'], snap, (now.hour, now.minute))
    s._live_tick(snap, (now.hour, now.minute))
    assert not ib.orders, 'A later live entry uses a T7 take even though its current spread/credit gate fails'


def test_stale_sweep_does_not_turn_incomplete_regime_session_into_cash():
    st = S.load_state('2026-10-07')
    st['session'] = {'spx_open': 6800., 'spx_hi30': 6805., 'spx_lo30': 6800., 'vix1d_open': 18.}
    # T2 skips because VIX is rising at 10:00, but could enter later if it falls.
    snap = {'ts': '2026-10-07T10:00:00-04:00', 'spx': 6800., 'xsp': 680., 'vix1d': 19., 'rows': chain()}
    S.step(st, snap, (10, 0), False)
    assert st['templates']['T2_REGIME']['status'] == 'NONE'
    assert st['templates']['T2_REGIME']['saw_strategy_skip']
    # The mechanical benchmark stops before collection fails, so falsely
    # assigning T2 a cash day can actually improve its paired comparison.
    snap['ts'] = '2026-10-07T10:01:00-04:00'
    for row in snap['rows']:
        if row['right'] == 'P' and row['strike'] == 672:
            row.update(bid=3., ask=3.05)
    for row in S.step(st, snap, (10, 1), False):
        S.append_ledger(row)
    assert st['templates']['T1_MECH']['status'] == 'CLOSED'
    S.save_state(st)
    rows = S.finalize_stale('2026-10-08')
    row = next(r for r in rows if r['template'] == 'T2_REGIME')
    assert row['skip_kind'] == 'data_unavailable', 'A partial entry window is counted as a successful cash decision'
