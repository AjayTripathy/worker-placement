import json
from datetime import date, timedelta

import pytest

from officekit_research import predictions, index

SOURCE = 'https://www.sec.gov/Archives/example.htm'


def register(folder, **overrides):
    fields = dict(symbol='AAA', statement='Revenue exceeds 100', resolution_criteria='FY audited revenue > 100 USD million',
                  resolve_by=(date.today() + timedelta(days=90)).isoformat(), probability=.8,
                  base_rate=.5, submitter='researcher-a', agent='earnings-reviewer', model='test-model',
                  protocol='v1', event_key='AAA-FY-revenue-100', strategy='growth')
    return predictions.record(folder, **dict(fields, **overrides))


def test_exact_brier_and_independent_submitter_agent_groups(tmp_path):
    a = register(tmp_path)
    b = register(tmp_path, submitter='researcher-b', probability=.3)
    c = register(tmp_path, agent='other-agent', probability=.2)
    for r, outcome in [(a, True), (b, False), (c, True)]:
        index.resolve(tmp_path, r['id'] + ':0', outcome, SOURCE)
    register(tmp_path, event_key='another-event')
    board = {r['submitter']: r for r in index.scoreboard(tmp_path, 'submitter')}
    assert board['researcher-a']['brier'] == .34
    assert board['researcher-a']['resolved'] == 2
    assert board['researcher-a']['pending'] == 1
    assert board['researcher-a']['pooled_brier'] == pytest.approx(.2567)
    assert board['researcher-b']['brier'] == .09
    assert len(index.scoreboard(tmp_path, 'agent')) == 2
    assert len(index.scoreboard(tmp_path, 'submitter_agent')) == 3
    assert all(r['skill_vs_base_rate'] is None for r in board.values())
    assert len(index.query(tmp_path, strategy='growth')) == 4


@pytest.mark.parametrize('field,value', [('probability', float('nan')), ('probability', 2), ('base_rate', True),
                                        ('resolution_criteria', ''), ('agent', ''), ('resolve_by', '2020-01-01')])
def test_rejects_ungradeable_forecasts(tmp_path, field, value):
    with pytest.raises(ValueError):
        register(tmp_path, **{field: value})


def test_no_duplicate_or_silent_forecast_rewrite(tmp_path):
    a = register(tmp_path)
    with pytest.raises(ValueError, match='already registered'):
        register(tmp_path, probability=.99)
    a['probability'] = .99
    predictions.path(tmp_path).write_text(json.dumps(a) + '\n', encoding='utf-8')
    with pytest.raises(ValueError, match='integrity'):
        index.scoreboard(tmp_path)


def test_outcomes_boolean_sourced_append_only_and_known_time(tmp_path):
    a = register(tmp_path)
    fid = a['id'] + ':0'
    with pytest.raises(ValueError):
        index.resolve(tmp_path, fid, 1, SOURCE)
    with pytest.raises(ValueError):
        index.resolve(tmp_path, fid, True, SOURCE, resolved_at='2099-01-01T00:00:00+00:00')
    index.resolve(tmp_path, fid, True, SOURCE)
    index.resolve(tmp_path, fid, False, SOURCE, note='Restatement')
    assert index.scoreboard(tmp_path, 'agent')[0]['brier'] == .64
    rows = [json.loads(l) for l in index.outcomes_path(tmp_path).read_text().splitlines()]
    assert len(rows) == 2 and rows[1]['supersedes']
    assert index.load_outcomes(tmp_path, known_by=date.today() - timedelta(days=1)) == {}


def test_reimport_retains_original_identity_without_duplicate_scores(tmp_path):
    from test_research_index import _seed_forecasts
    from officekit_research import general
    _seed_forecasts(tmp_path / 'donor', 1, .8, .5, [True])
    r = general.load_all(tmp_path / 'donor')[0]
    origin = [{'record_id': r['id'], 'contributor': 'a' * 32, 'attribution': 'claimed'}]
    general.save(tmp_path / 'recipient', r, origin='imported', attributions=origin)
    general.save(tmp_path / 'recipient', r, origin='imported', attributions=origin)
    index.resolve(tmp_path / 'recipient', r['id'] + ':0', True, SOURCE)
    board = index.scoreboard(tmp_path / 'recipient', 'submitter')
    assert len(board) == 1 and board[0]['submitter'] == 'a' * 32
    assert board[0]['forecasts'] == 1 and board[0]['brier'] == .04


def test_scorecard_form_roundtrip_and_stale_correction(server):
    from test_officekit_onboarding_e2e import _get
    from test_deployment_plan import Form, answers
    from test_local_security import request
    from officekit.serve import build_office
    base, folder = server
    build_office(answers(), folder)
    a = register(folder)
    html = _get(base + '/research/scorecard')
    form = Form(html, suffix='/research/resolve')
    form.fields.update(outcome='true', source_url=SOURCE)
    assert request(base, 'POST', form.action, form.fields, Origin=base)[0] == 200
    assert index.scoreboard(folder, 'agent')[0]['brier'] == .04
    assert request(base, 'POST', form.action, form.fields, Origin=base)[0] == 400


from test_officekit_onboarding_e2e import server  # noqa: E402,F401
