"""One workspace across transports; durable edits, isolation and optional AI."""
import base64
from copy import deepcopy
import json
import re
import uuid

import pytest
from fastapi.testclient import TestClient

from test_hosted_migration import Backend, MemoryStore, ORIGIN, office, upload, send
from hosting.app.main import create_app, SESSION, CSRF
from hosting.app.offices import Offices
from hosting.app.workspace import dispatch, publish
from hosting.app.auth import AuthFailure
from officekit.commitments import revision
from officekit.personal_context import empty


@pytest.fixture
def workspace(office):
    answers = json.loads((office / 'answers.json').read_text())
    (office / 'personal_context.json').write_text(json.dumps(empty(answers['office_id'])))
    store = MemoryStore()
    with TestClient(create_app(Backend(), ORIGIN, store=store), base_url=ORIGIN) as client:
        client.store = store
        _, sid = upload(client, office)
        receipt = send(client, '/api/migrations/' + sid + '/activate', {}).json()
        client.cookies.set(SESSION, 'alice')
        client.get(receipt['path'])
        yield client, receipt, office


def post(client, receipt, path, fields=None, **kwargs):
    return client.post(receipt['path'] + path, data={
        '_csrf': client.cookies.get(CSRF), '_office_revision': receipt['digest'], **(fields or {})},
        headers={'Origin': ORIGIN}, follow_redirects=False, **kwargs)


def test_same_shell_all_pages_and_reads_preserve_saved_facts(workspace):
    client, receipt, folder = workspace
    before = deepcopy(client.store.rows)
    response = client.get(receipt['path'])
    assert response.status_code == 200
    assert 'Office workspace' in response.text and 'id="workspace-nav"' in response.text
    assert '<nav class="workspace-nav"' in response.text and '<select' not in response.text
    assert 'id="t_goals"' in response.text
    assert 'Host office ↗' not in response.text and 'Office settings' in response.text
    assert receipt['path'] + '/pages/office.html' in response.text
    assert 'nonce-' in response.headers['content-security-policy']
    assert "script-src 'self' 'unsafe-inline'" not in response.headers['content-security-policy']
    assert ' onclick=' not in response.text and 'addEventListener("click"' in response.text
    assert response.headers['x-frame-options'] == 'SAMEORIGIN'
    assert response.headers['referrer-policy'] == 'same-origin'
    assert 'href="/app"' in response.text
    assert "headers.set('X-CSRF-Token',csrf)" in response.text
    for page in ('office', 'goals', 'capital', 'strategies', 'scenarios', 'growth', 'harvest', 'risk', 'imports', 'signals'):
        response = client.get(receipt['path'] + '/pages/' + page + '.html')
        assert response.status_code == 200, (page, response.text)
        assert '<html' in response.text
        assert 'action="/goals' not in response.text
    assert client.store.rows == before
    assert client.get(receipt['path'] + '/state').json() == {'v': receipt['digest']}


def test_edits_persist_on_new_process_and_stale_tabs_reject(workspace):
    client, receipt, folder = workspace
    response = post(client, receipt, '/growth', {'stocks_pct': '55', 'bonds_pct': '35'})
    assert response.status_code == 303, response.text
    assert response.headers['location'] == receipt['path'] + '/pages/growth.html'
    current, record = Offices(client.store).read('alice', receipt['office_id'])
    assert current['digest'] != receipt['digest']
    assert json.loads(base64.b64decode(record['documents']['answers.json']))['target_mix']['stocks_pct'] == 55
    assert 'research/memo.md' in record['documents']
    with TestClient(create_app(Backend(), ORIGIN, store=client.store), base_url=ORIGIN) as restarted:
        restarted.cookies.set(SESSION, 'alice')
        response = restarted.get(receipt['path'] + '/pages/growth.html')
        assert response.status_code == 200 and 'value="55"' in response.text
    rejected = post(client, receipt, '/growth', {'stocks_pct': '20', 'bonds_pct': '80'})
    assert rejected.status_code == 409 and 'Changes were not saved' in rejected.text
    assert Offices(client.store).read('alice', receipt['office_id'])[0] == current


def test_hosted_commitments_use_shared_editor(workspace):
    client, receipt, folder = workspace
    answers = json.loads((folder/'answers.json').read_text())
    response = post(client, receipt, '/commitments/add', {
        'revision': revision(answers), 'source': 'recurring_expense', 'label': 'School',
        'amount': '1200', 'cadence': 'monthly', 'next_due': '2026-10-01', 'funding_source': 'portfolio'})
    assert response.status_code == 303, response.text
    _, record = Offices(client.store).read('alice', receipt['office_id'])
    assert 'commitment_history.jsonl' in record['workspace']
    page = client.get(receipt['path'] + '/pages/capital.html')
    assert 'School' in page.text


def test_strategy_brief_waits_for_key_without_starting_job(workspace, monkeypatch):
    import officekit.strategy_proposals as proposals
    import officekit_ai
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'must-not-be-used')
    monkeypatch.setattr(proposals, 'dispatch', lambda *a, **k: pytest.fail('No hosted jobs before a scoped key'))
    monkeypatch.setattr(officekit_ai, 'available', lambda *a, **k: pytest.fail('Must not inspect machine keys'))
    client, receipt, folder = workspace
    answers = json.loads((folder/'answers.json').read_text())
    response = post(client, receipt, '/strategy/new', {'revision': revision(answers),
        'title': 'Defensive stock rotation', 'target_pct': '10', 'request': 'Compare defensive ETFs'})
    assert response.status_code == 303, response.text
    page = client.get(response.headers['location'])
    assert 'Ready for an AI agent key' in page.text
    assert 'http-equiv="refresh"' not in page.text
    _, record = Offices(client.store).read('alice', receipt['office_id'])
    name = next(k for k in record['documents'] if k.startswith('strategy_proposals/'))
    proposal = json.loads(base64.b64decode(record['documents'][name]))
    assert proposal['status'] == 'awaiting_key' and proposal['research'] is None


@pytest.mark.parametrize('path', ['', '/pages/capital.html', '/state', '/settings', '/documents', '/export'])
def test_every_workspace_read_is_owner_scoped(workspace, path):
    client, receipt, _ = workspace
    client.cookies.set(SESSION, 'bob')
    assert client.get(receipt['path'] + path).status_code == 404


def test_csrf_origin_unknown_paths_and_validation_do_not_mutate(workspace):
    client, receipt, _ = workspace
    before = deepcopy(client.store.rows)
    fields = {'stocks_pct': '1', 'bonds_pct': '99'}
    assert client.post(receipt['path'] + '/growth', data=fields).status_code == 403
    assert client.post(receipt['path'] + '/growth', data=fields, headers={'Origin': ORIGIN}).status_code == 403
    assert post(client, receipt, '/key', {'api_key': 'never-store'}).status_code == 400
    assert post(client, receipt, '/reset').status_code == 400
    assert client.get(receipt['path'] + '/answers.json').status_code == 404
    assert post(client, receipt, '/growth', {'stocks_pct': '999', 'bonds_pct': '1'}).status_code == 400
    assert client.store.rows == before


def test_compare_and_swap_does_not_overwrite_concurrent_save(workspace, monkeypatch):
    client, receipt, _ = workspace
    offices = Offices(client.store)
    _, record = offices.read('alice', receipt['office_id'])
    original = client.store.put
    key = offices.prefix('alice', receipt['office_id']) + 'active'
    def raced(name, value, generation=0):
        if name == key:
            original(key, dict(receipt, digest='b'*64), generation)
        return original(name, value, generation)
    monkeypatch.setattr(client.store, 'put', raced)
    with pytest.raises(AuthFailure) as caught:
        publish(offices, 'alice', receipt, record)
    assert caught.value.status == 409
    assert client.store.get(key)[0]['digest'] == 'b'*64


def test_hosted_csv_paths_cannot_read_machine_files(tmp_path):
    from officekit.runtime import hosted_office
    from officekit.importers import run_import
    sentinel = tmp_path/'outside.csv'
    sentinel.write_text('Symbol,Value\nPRIVATE,777\n')
    root = tmp_path/'office';root.mkdir()
    with hosted_office(root):
        for path in (str(sentinel), '../outside.csv', 'file:///etc/passwd'):
            with pytest.raises(ValueError): run_import({'path': path})


def test_missing_csrf_is_visible_inside_workspace_frame(workspace):
    client, receipt, _ = workspace
    response = client.post(receipt['path'] + '/growth', data={'stocks_pct': '50'},
                           headers={'Origin': ORIGIN, 'Accept': 'text/html'})
    assert response.status_code == 403
    assert response.headers['x-frame-options'] == 'SAMEORIGIN'
    assert 'Request not completed' in response.text and 'role="alert"' in response.text


def test_sma_label_and_office_owned_realized_tax_survive_hosted_rebuild(tmp_path):
    from officekit.intake import build_from_answers
    from officekit.serve import _capital_model
    from officekit.runtime import hosted_office
    answers = {'as_of': '2026-09-17', 'positions': {'account': 'SMA', 'rows': [
        {'symbol': 'STOCK' + str(i), 'value': 1000} for i in range(8)]},
        'incoming': {'amount': 100000, 'character': 'ltcg', 'rate': 0.238}}
    symbols = {r['symbol'] for r in answers['positions']['rows']}
    data = build_from_answers(answers, sma_symbols=symbols, sma_label='Sample SMA (131/31)')
    (tmp_path/'balance_sheet.json').write_text(json.dumps(data))
    (tmp_path/'parametric_scorecard.json').write_text(json.dumps({'realized_ytd': {'net': -1000, 'st_net': -300, 'lt_net': -700}}))
    with hosted_office(tmp_path):
        rebuilt = _capital_model(answers, tmp_path)['d']
    before = next(s for s in data['sleeves'] if s['category'] == 'direct_index')
    after = next(s for s in rebuilt['sleeves'] if s['category'] == 'direct_index')
    assert before == after
    assert rebuilt['tax_model']['realized_losses_ytd'] == 1000


def test_html_user_text_is_not_executed(workspace):
    client, receipt, _ = workspace
    response = post(client, receipt, '/assets', {'u_kind': 'cash',
        'u_name': '</title><script>window.stolen=true</script>', 'u_value': '25'})
    assert response.status_code == 303
    page = client.get(receipt['path'] + '/pages/office.html')
    assert '<script>window.stolen' not in page.text
    assert '&lt;script&gt;window.stolen' in page.text
