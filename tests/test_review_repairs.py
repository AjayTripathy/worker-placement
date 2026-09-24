import json
from datetime import datetime, timedelta, timezone

import pytest


def test_local_scores_require_exact_company_input_source_and_cutoff(tmp_path):
    from verticals.public_co.providers import LocalProvider
    from verticals.public_co.analysis_types import Claim
    source = {'claims': [{'claim_id': 'c1', 'claim_text': 'Revenue grew'}]}
    (tmp_path / 'AAA.input.json').write_text(json.dumps(source))
    # An unrelated company uses the same non-global claim ID.
    score = {'claim_id': 'c1', 'severity': 'RED_FLAG_NEGATIVE', 'supports': False}
    (tmp_path / 'BBB.scores.json').write_text(json.dumps({'scores': [score]}))
    p = LocalProvider(tmp_path)
    claim = p.extract_and_pick('AAA', '2026-09-01', 'Filing A', {})[0][0]
    assert p.score(claim, []).severity == 'UNVERIFIABLE'
    target = tmp_path / 'AAA.scores.json'
    target.write_text(json.dumps({'scores': [score]}))
    assert p.score(claim, []).severity == 'UNVERIFIABLE'
    target.write_text(json.dumps({'binding': p.score_binding, 'scores': [score]}))
    assert p.score(claim, []).severity == 'RED_FLAG_NEGATIVE'
    assert p.score(Claim('c1', 'Different claim'), []).severity == 'UNVERIFIABLE'
    p.extract_and_pick('AAA', '2026-09-02', 'Filing A', {})
    assert p.score(claim, []).severity == 'UNVERIFIABLE'
    p.extract_and_pick('AAA', '2026-09-01', 'Different source', {})
    assert p.score(claim, []).severity == 'UNVERIFIABLE'


def test_current_company_incomplete_or_duplicate_scores_never_fall_back(tmp_path):
    from verticals.public_co.providers import LocalProvider
    (tmp_path / 'AAA.input.json').write_text(json.dumps({'claims': [{'claim_id': 'c1', 'claim_text': 'A'}]}))
    p = LocalProvider(tmp_path)
    claim = p.extract_and_pick('AAA', '2026-09-01', 'Filing', {})[0][0]
    for scores in ([], [{'claim_id': 'c2'}], [{'claim_id': 'c1'}, {'claim_id': 'c1'}]):
        (tmp_path / 'AAA.scores.json').write_text(json.dumps({'binding': p.score_binding, 'scores': scores}))
        assert p.score(claim, []).severity == 'UNVERIFIABLE'


@pytest.mark.parametrize('permanent', [False, True])
def test_windows_replace_sharing_errors_are_bounded_and_visible(tmp_path, monkeypatch, permanent):
    from officekit import staging
    original = staging.os.replace
    attempts = []
    def replace(*args):
        attempts.append(1)
        if permanent or len(attempts) < 3:
            error = PermissionError('sharing violation')
            error.winerror = 32
            raise error
        return original(*args)
    monkeypatch.setattr(staging.os, 'replace', replace)
    monkeypatch.setattr(staging.time, 'sleep', lambda _: None)
    if permanent:
        with pytest.raises(PermissionError):
            staging._atomic_write(tmp_path, {'sources': {'A': {'label': '日本'}}})
        assert len(attempts) == 6
    else:
        staging._atomic_write(tmp_path, {'sources': {'A': {'label': '日本'}}})
        assert staging.load(tmp_path)['sources']['A']['label'] == '日本'
    assert not list(tmp_path.glob('*.tmp'))


def test_corrupt_staging_is_not_silently_replaced(tmp_path):
    from officekit import staging
    (tmp_path / 'staging.json').write_text('{broken')
    with pytest.raises(json.JSONDecodeError):
        staging.load(tmp_path)


def test_old_option_warning_is_observable_without_broker_access():
    from desk.order_sentinel import option_age_findings
    now = datetime.now(timezone.utc)
    orders = [{'primary_description': 'AAA Call', 'order_time': (now - timedelta(days=9)).isoformat()},
              {'primary_description': 'AAA Put', 'order_time': 'broken'}]
    warnings = option_age_findings(orders, now)
    assert len(warnings) == 2 and all(level == 'WARN' for level, _ in warnings)
    assert '9d' in warnings[0][1] and 'invalid order time' in warnings[1][1]


def test_legacy_contract_projection_preserves_history_and_excludes_ambiguity():
    from desk.research_contracts import project_calibration, validate_new
    a = dict(ticker='AAA', made='2026-01-01', cat_date='2026-06-01', our_p=.7,
             event_type='earnings_print', status='OPEN')
    rows = [a, dict(a, our_p=.8), dict(a, ticker='BBB', status='GRADED', outcome='HIT')]
    before = json.dumps(rows)
    projected, audit = project_calibration(rows)
    assert json.dumps(rows) == before and audit['excluded'] == 3
    assert all(r['status'] == 'EXCLUDED_REVIEW' for r in projected)
    with pytest.raises(ValueError, match='already frozen'):
        validate_new(a, [a])


def test_incomplete_sizing_and_verdict_mismatch_cannot_route():
    from desk.research_contracts import routing_issues
    ledger = {'state': 'OWNABLE', 'verdict': 'OWNABLE'}
    record = {'verdict_state': 'OWNABLE', 'sizing': '2% yield is not a size'}
    assert routing_issues(ledger, record)
    record['sizing'] = {'pct_lo': 1, 'pct_hi': 2}
    assert routing_issues(ledger, record) == []
    record['verdict_state'] = 'AVOID'
    assert routing_issues(ledger, record)


def test_entry_view_keeps_incomplete_records_visible_outside_ready(tmp_path, monkeypatch):
    from desk.ui import aggregator as app
    folder = tmp_path / 'desk' / 'data'
    ec = folder / 'edge_classifications'
    ec.mkdir(parents=True)
    rows = [dict(ticker=t, verdict='OWNABLE', state='OWNABLE') for t in ('AAA', 'BBB', 'CCC')]
    (folder / 'research_ledger.json').write_text(json.dumps({'names': rows}))
    for t in ('AAA', 'BBB', 'CCC'):
        (ec / (t + '.json')).write_text(json.dumps({'verdict_state': 'AVOID' if t == 'CCC' else 'OWNABLE',
            'edge_explainer': 'Synthetic', 'sizing': '2% yield' if t == 'BBB' else {'pct_lo': 1, 'pct_hi': 2}}))
    plan = tmp_path / 'plan.json'
    plan.write_text(json.dumps({'target_nlv': 1000000, 'orders': []}))
    monkeypatch.setattr(app, 'ROOT', tmp_path)
    monkeypatch.setattr(app, 'EC_DIR', ec)
    monkeypatch.setattr(app, 'ENTRY_PLAN', plan)
    monkeypatch.setattr(app, '_approved_set', lambda: set())
    found = app.entry_candidates()
    assert [r['ticker'] for r in found['live']] == ['AAA']
    assert {r['ticker'] for r in found['pending_review']} == {'BBB', 'CCC'}
    assert found['live'][0]['est_usd_lo'] == 10000


def test_legacy_actor_scoring_does_not_invent_authorship_or_binary_mixed_outcomes():
    from desk.calibration import score_by_actor
    rows = [{'our_p': .8, 'status': 'RESOLVED', 'resolution': 'FAVORABLE',
             'attribution': {'submitter': 'alice', 'agent': 'analyst'}},
            {'our_p': .3, 'status': 'RESOLVED', 'resolution': 'MIXED'},
            {'our_p': .7, 'status': 'OPEN'}]
    board = score_by_actor(rows, 'submitter')
    assert board['alice']['brier'] == .04
    assert board['unattributed']['brier'] is None
    assert board['unattributed']['pending'] == 1 and board['unattributed']['excluded'] == 1
