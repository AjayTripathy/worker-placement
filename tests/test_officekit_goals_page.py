"""Goals navigation and natural-language intake, without live provider calls."""
import json
import uuid

import pytest

from officekit.serve import build_office
from test_officekit_onboarding_e2e import server, _get, _post


def seed(folder):
    build_office({'as_of': '2026-09-18', 'profile': {},
                  'sleeves': [{'name': 'Cash', 'category': 'cash', 'value': 500000}],
                  'goals': [{'id': 'existing', 'kind': 'liquidity_floor', 'label': 'Emergency fund', 'amount': 50000}]}, folder)


def test_goals_destination_and_manual_edit_return(server, monkeypatch):
    base, folder = server
    monkeypatch.setattr('officekit.serve._ai', lambda *a, **k: False)
    seed(folder)
    page = _get(base + '/pages/goals.html')
    assert 'Emergency fund' in page and 'Describe a goal in your own words' in page
    assert 'name="nl"' in page and 'disabled aria-describedby="goal-key-note"' in page
    assert 'Office settings' in page and 'name="back" value="goals"' in page
    shell = _get(base)
    assert '<nav class="workspace-nav"' in shell and '<select' not in shell
    assert "slug.startsWith('goal_')?'goals'" in shell
    status, location, _ = _post(base + '/goals/add', {'back': 'goals', 'gkind': 'spending', 'glabel': 'College', 'gamt': '300000', 'gdate': '2038-01-01'})
    assert (status, location) == (303, '/pages/goals.html')
    goals = json.loads((folder / 'answers.json').read_text())['goals']
    college = next(g for g in goals if g['label'] == 'College')
    detail = _get(base + '/pages/goal_' + college['id'] + '.html')
    assert 'href="/pages/goals.html">← Goals' in detail
    status, location, _ = _post(base + '/goals/remove', {'back': 'goals', 'gid': college['id']})
    assert (status, location) == (303, '/pages/goals.html')
    assert [g['id'] for g in json.loads((folder / 'answers.json').read_text())['goals']] == ['existing']


def test_natural_language_adds_multiple_goals_preserves_saved_office(server, monkeypatch):
    base, folder = server
    monkeypatch.setattr('officekit.serve._ai', lambda *a, **k: True)
    seed(folder)
    before = json.loads((folder / 'answers.json').read_text())
    text = 'Retire in 2045 on $120k per year and save $300k for college in 2038.'
    def turn(messages, **kwargs):
        assert messages == [{'role': 'user', 'content': text}]
        assert kwargs == {'folder': folder, 'scope': 'goals'}
        return {'answers': {'goals': [
            {'id': '../unsafe', 'kind': 'retirement', 'label': 'Retirement', 'annual_spending': 120000, 'date': '2045-01-01'},
            {'id': 'existing', 'kind': 'spending', 'label': 'College', 'amount': 300000, 'date': '2038-01-01'}]}}
    monkeypatch.setattr('officekit_ai.intake_chat.turn', turn)
    assert 'disabled aria-describedby="goal-key-note"' not in _get(base + '/pages/goals.html')
    status, location, _ = _post(base + '/goals/add', {'back': 'goals', 'nl': text})
    assert (status, location) == (303, '/pages/goals.html')
    after = json.loads((folder / 'answers.json').read_text())
    assert after['goals'][0] == before['goals'][0] and len(after['goals']) == 3
    assert after['sleeves'] == before['sleeves']
    for goal in after['goals'][1:]:
        uuid.UUID(goal['id'])
        assert (folder / 'pages' / ('goal_' + goal['id'] + '.html')).exists()


@pytest.mark.parametrize('available,result,message', [
    (False, None, 'Connect an AI agent'),
    (True, {'answers': {}, 'reply': 'What amount would you like to set aside?'}, 'What amount'),
    (True, {'answers': {'goals': [{'kind': 'retirement', 'label': 'Incomplete'}]}}, 'annual_spending'),
])
def test_failed_intake_never_reports_success_or_changes_facts(server, monkeypatch, available, result, message):
    base, folder = server
    monkeypatch.setattr('officekit.serve._ai', lambda *a, **k: available)
    monkeypatch.setattr('officekit_ai.intake_chat.turn', lambda *a, **k: result)
    seed(folder)
    before = {name: (folder / name).read_bytes() for name in ('answers.json', 'balance_sheet.json')}
    status, _, page = _post(base + '/goals/add', {'back': 'goals', 'nl': 'Plan retirement'})
    assert status == 400 and message in page
    assert before == {name: (folder / name).read_bytes() for name in before}
