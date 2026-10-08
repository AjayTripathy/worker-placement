"""Mixed legacy inputs must not disable ingestion or hide the whole dashboard."""
import copy
import datetime as dt
import json

import pytest


@pytest.fixture
def calibration(tmp_path, monkeypatch):
    from desk import calibration as c
    for name, file in [('LEDGER', 'ledger.jsonl'), ('PRED', 'pred.json'), ('CATMIS', 'scanner.json'), ('OUT', 'score.json')]:
        monkeypatch.setattr(c, name, tmp_path / file)
    monkeypatch.setattr(c, '_px_many', lambda tickers: {t: 10. for t in tickers})
    c.CATMIS.write_text(json.dumps({'scored': []}))
    return c


def prediction(**kw):
    return {'date': '2099-01-01', 'p_favorable': .7, 'event_type': 'earnings_print', **kw}


def test_ingest_rejects_each_bad_row_and_admits_later_valid_rows(calibration):
    c = calibration
    preds = {'UNKNOWN': prediction(event_type='made_up'), 'LATE': prediction(date='2000-01-01'),
             'BAD': prediction(p_favorable='not a probability'), 'SHAPE': None,
             'GOOD': prediction(attribution={'submitter': 'test-office', 'agent': 'test-agent'})}
    c.PRED.write_text(json.dumps({'predictions': preds}))
    c.CATMIS.write_text(json.dumps({'scored': [None, {'ticker': 'SCENARIO', 'cat_date': '2099-01-01',
        'event_type': 'production_ops', 'p_base': .4, 'p_bull': .2, 'px': 20.}]}))
    assert c.ingest() == 2
    assert [r['ticker'] for r in c._load()] == ['GOOD', 'SCENARIO']
    assert c._load()[1]['event_type'] == 'production_ops'
    assert c._load()[0]['attribution']['agent'] == 'test-agent'
    audit = json.loads(c.LEDGER.with_name('calibration_ingest_report.json').read_text())
    assert audit['rejected'] == 5 and all(r['record_sha256'] and r['issues'] for r in audit['records'])
    before = c.LEDGER.read_bytes()
    assert c.ingest() == 0 and c.LEDGER.read_bytes() == before
    c.main()  # Scoring/reporting still completes with rejected source rows present.
    assert json.loads(c.OUT.read_text())['n_open'] == 2


def test_ingest_keeps_independent_events_and_existing_frozen_rows(calibration):
    c = calibration
    old = {'ticker': 'AAA', 'cat_date': '2099-01-01', 'event_type': 'stock_reaction',
           'made': '2026-01-01', 'our_p': .2, 'status': 'OPEN'}
    c._write([old]); c.PRED.write_text(json.dumps({'predictions': {'AAA': prediction()}}))
    assert c.ingest() == 1 and c._load()[0] == old
    assert {r['event_type'] for r in c._load()} == {'stock_reaction', 'earnings_print'}


def test_all_rejected_is_reported_without_creating_ledger(calibration):
    c = calibration
    c.PRED.write_text(json.dumps({'predictions': {'AAA': prediction(event_type=None)}}))
    assert c.ingest() == 0 and not c.LEDGER.exists()
    assert json.loads(c.LEDGER.with_name('calibration_ingest_report.json').read_text())['rejected'] == 1


def test_legacy_projection_has_provenance_and_does_not_mutate():
    from desk.research_contracts import routing_projection, routing_issues
    ledger = {'verdict': 'OWNABLE', 'state': 'OWNABLE', 'conviction': '6% dividend yield; 1-2% starter'}
    record = {'edge_explainer': {'we_believe': 'fixture'}}
    saved = copy.deepcopy((ledger, record))
    result = routing_projection(ledger, record)
    assert result['issues'] == [] and result['legacy_fallback']
    assert result['sizing'] == {'pct_lo': 1., 'pct_hi': 2.}
    assert result['sizing_source'] == 'ledger.conviction' and result['record_sha256']
    assert (ledger, record) == saved
    assert routing_issues(ledger, record)  # Strict write contract remains strict.
    assert routing_projection(ledger, record, allow_legacy=False)['issues']


@pytest.mark.parametrize('sizing', ['6% dividend yield', {'pct_lo': -1, 'pct_hi': 2}, {'pct_lo': 3, 'pct_hi': 2}])
def test_invalid_size_or_yield_cannot_become_ready(sizing):
    from desk.research_contracts import routing_projection
    ledger = {'verdict': 'OWNABLE', 'state': 'OWNABLE'}
    record = {'verdict_state': 'OWNABLE', 'sizing': sizing}
    assert routing_projection(ledger, record)['issues']


@pytest.mark.parametrize('state,mirror', [('HELD', None), ('OWNABLE', 'WATCH'), ('OWNABLE', 'AVOID')])
def test_explicit_verdict_conflicts_do_not_fall_back(state, mirror):
    from desk.research_contracts import routing_projection
    assert routing_projection({'verdict': 'OWNABLE', 'state': state},
                              {'verdict_state': mirror, 'sizing': '1% starter'})['issues']


@pytest.fixture
def dashboard(tmp_path, monkeypatch):
    from desk.ui import aggregator as a
    data = tmp_path / 'desk/data'; ec = data / 'edge_classifications'; ec.mkdir(parents=True)
    rows = [{'ticker': t, 'verdict': 'OWNABLE', 'state': 'OWNABLE'} for t in ['STRUCT', 'LEGACY', 'YIELD', 'CONFLICT']]
    (data/'research_ledger.json').write_text(json.dumps({'names': rows}))
    for t in ['STRUCT', 'LEGACY', 'YIELD', 'CONFLICT']:
        record = {'edge_explainer': {'we_believe': 'Synthetic'}, 'sizing': '1-2% starter'}
        if t == 'STRUCT':
            record.update(verdict_state='OWNABLE', sizing={'pct_lo': 1, 'pct_hi': 2})
        if t == 'YIELD':
            record['sizing'] = '6% yield'
        if t == 'CONFLICT':
            record['verdict_state'] = 'AVOID'
        (ec/(t+'.json')).write_text(json.dumps(record))
    monkeypatch.setattr(a, 'ROOT', tmp_path); monkeypatch.setattr(a, 'EC_DIR', ec)
    monkeypatch.setattr(a, 'ENTRY_PLAN', data/'absent-plan.json')
    monkeypatch.setattr(a, 'CATMIS', data/'absent-scanner.json')
    monkeypatch.setattr(a, '_approved_set', lambda: set())
    monkeypatch.setattr(a, '_live_prices', lambda *args: {})
    monkeypatch.setattr(a, '_catpred', lambda: {})
    monkeypatch.setattr(a, 'book', lambda: {})
    monkeypatch.setattr(a, 'watchlist', lambda: {})
    return a


def test_entry_and_alerts_share_legacy_projection_and_visible_rejections(dashboard):
    entry, alerts = dashboard.entry_candidates(), dashboard.alerts()
    for rows in [entry['live'], alerts['ready']]:
        by_ticker = {r['ticker']: r for r in rows}
        assert set(by_ticker) == {'STRUCT', 'LEGACY'}
        assert by_ticker['LEGACY']['legacy_fallback'] and by_ticker['LEGACY']['needs_review']
        assert not by_ticker['STRUCT']['legacy_fallback']
    for payload in [entry, alerts]:
        assert {r['ticker'] for r in payload['pending_review']} == {'YIELD', 'CONFLICT'}
    assert all(not r['approved'] for r in entry['live'])
    assert alerts['counts']['ready'] == alerts['counts']['pending_review'] == 2
