"""Fresh price evidence, cash-day comparisons and atomic persistence."""
import datetime as dt
import json
from types import SimpleNamespace as NS

import pytest

from desk.odte import capture as C, grader as G, shadow as S, storage, templates as T
from test_odte import chain

NOW = dt.datetime(2026, 10, 8, 10, 5, tzinfo=C.ET)


def capture():
    c = C.ChainCapture.__new__(C.ChainCapture)
    c.expiry = '20261008'; c.data_type = 'live'; c._quote_times = {}
    c.idx = {key: NS(last=value, close=value, marketDataType=1, contract=NS(conId=i))
             for i, (key, value) in enumerate([('XSP', 680.), ('SPX', 6800.), ('VIX1D', 18.)], 1)}
    c.tickers = {(r['strike'], r['right']): NS(bid=r['bid'], ask=r['ask'], last=r['bid'],
                 marketDataType=1, contract=NS(conId=r['conId']),
                 modelGreeks=NS(delta=r['delta'], impliedVol=.18)) for r in chain()}
    for t in list(c.idx.values()) + list(c.tickers.values()):
        c._quote_times[t.contract.conId] = {field: NOW for field in ('bid', 'ask', 'last')}
    return c


def test_fresh_live_candidate_is_accepted():
    snap = capture().snapshot(NOW)
    assert snap['indices_live'] and snap['data_type'] == 'live'
    assert T.build_condor([r for r in snap['rows'] if r['live_eligible']], .1, 2)['ok']


@pytest.mark.parametrize('data_type', [2, 3, 4])
def test_frozen_or_delayed_legs_are_not_live_candidates(data_type):
    c = capture()
    for t in c.tickers.values(): t.marketDataType = data_type
    snap = c.snapshot(NOW)
    assert not any(r['live_eligible'] for r in snap['rows'])


def test_stale_price_not_refreshed_by_other_ticker_updates():
    c = capture()
    for t in c.tickers.values():
        t.time = NOW
        t.ticks = [NS(tickType=0, time=NOW)]  # size update only
    c._quote_times = {k: {f: v - dt.timedelta(days=1) for f, v in times.items()} for k, times in c._quote_times.items()}
    c._on_ticks(c.tickers.values())
    snap = c.snapshot(NOW)
    assert not snap['indices_live'] and snap['xsp'] is None
    assert not any(r['live_eligible'] for r in snap['rows'])
    assert not T.build_condor(snap['rows'], .1, 2)['ok']


def test_missing_vix_last_does_not_use_previous_close():
    c = capture(); c.idx['VIX1D'].last = float('nan')
    snap = c.snapshot(NOW)
    assert snap['vix1d'] is None and not snap['indices_live']


def test_price_ticks_refresh_only_their_own_fields():
    c = capture(); ticker = next(iter(c.tickers.values()))
    c._quote_times[ticker.contract.conId]['bid'] = NOW - dt.timedelta(minutes=5)
    ticker.ticks = [NS(tickType=2, time=NOW)]
    c._on_ticks([ticker])
    assert not c._fresh(ticker, ('bid', 'ask'), NOW)
    ticker.ticks = [NS(tickType=1, time=NOW)]
    c._on_ticks([ticker])
    assert c._fresh(ticker, ('bid', 'ask'), NOW)


def test_frozen_index_disables_live_entry():
    c = capture(); c.idx['SPX'].marketDataType = 2
    assert not c.snapshot(NOW)['indices_live']


def test_blackout_benchmark_includes_cash_day_and_excludes_missing_data():
    benchmark = [{'date': f'd{i}', 'pnl_usd': p} for i, p in enumerate([30, -160, 25, 28, -200])]
    rows = [dict(r) for r in benchmark]
    rows[1].update(pnl_usd=None, reason='NO_ENTRY', skip_kind='strategy_cash')
    rows[4].update(pnl_usd=None, reason='NO_ENTRY', skip_kind='data_unavailable')
    result = G.vs_benchmark(rows, benchmark)
    assert result == {'paired': 4, 'cash_sessions': 1, 'mean_diff_usd': 40., 't_stat': 1.}


def test_shadow_marks_observed_blackout_as_cash_but_missing_regime_as_unknown(tmp_path, monkeypatch):
    monkeypatch.setattr(S, 'DATA', tmp_path)
    snap = {'ts': NOW.isoformat(), 'rows': chain(), 'spx': 6800., 'xsp': 680., 'vix1d': None, 'data_type': 'live'}
    st = S.load_state('2026-10-08')
    S.step(st, snap, (10, 5), True)
    closed = S.step(st, snap, (10, 21), True)
    assert next(r for r in closed if r['template'] == 'T3_BLACKOUT')['skip_kind'] == 'strategy_cash'
    st = S.load_state('2026-10-09')
    S.step(st, snap, (10, 5), False)
    closed = S.step(st, snap, (10, 21), False)
    assert next(r for r in closed if r['template'] == 'T2_REGIME')['skip_kind'] == 'data_unavailable'


def test_missing_chain_prevents_later_regime_skip_being_called_cash(tmp_path, monkeypatch):
    monkeypatch.setattr(S, 'DATA', tmp_path)
    st = S.load_state('2026-10-08')
    st['session'] = {'first30_range': .004, 'vix1d_open': 18.}
    snap = {'ts': NOW.isoformat(), 'rows': [], 'vix1d': 17.}
    S.step(st, snap, (10, 1), False)
    S.step(st, {**snap, 'vix1d': 20.}, (10, 5), False)
    closed = S.step(st, snap, (10, 21), False)
    assert next(r for r in closed if r['template'] == 'T2_REGIME')['skip_kind'] == 'data_unavailable'


def test_graduation_requires_sixty_common_observations():
    g = G.graduation({'traded': 60, 'max_dd_usd': -10}, {'paired': 2, 't_stat': 4}, {'max_dd_usd': -10})
    assert not g['sessions_ok'] and not g['graduated']


def test_atomic_checkpoint_preserves_previous_file_when_replace_fails(tmp_path, monkeypatch):
    path = tmp_path / 'state.json'; storage.atomic_json(path, {'status': 'OPENING'})
    def fail(*a): raise OSError('replace failed')
    monkeypatch.setattr(storage.os, 'replace', fail)
    with pytest.raises(OSError): storage.atomic_json(path, {'status': 'OPEN'})
    assert json.loads(path.read_text()) == {'status': 'OPENING'}
    assert list(tmp_path.iterdir()) == [path]
