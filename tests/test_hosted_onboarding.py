"""The local onboarding handler, persisted through the hosted transport."""
import base64
from copy import deepcopy
import json

import pytest
from fastapi.testclient import TestClient

from test_hosted_migration import Backend, MemoryStore, ORIGIN, client
from test_hosted_workspace import post
from test_hosted_parity import Queue
from hosting.app.main import create_app, SESSION, CSRF
from hosting.app.offices import Offices
from hosting.app.credentials import Credentials
from hosting.app.workspace import local_request, materialize, present
from officekit.runtime import hosted_office


def start(client):
    client.cookies.set(SESSION, 'alice')
    client.get('/app')
    response = client.post('/api/offices/start', json={}, headers={
        'Origin': ORIGIN, 'X-CSRF-Token': client.cookies.get(CSRF)})
    assert response.status_code == 200, response.text
    return response.json()


def draft(client, receipt, data):
    return client.post(receipt['path'] + '/draft', json=data, headers={
        'Origin': ORIGIN, 'X-CSRF-Token': client.cookies.get(CSRF),
        'X-Office-Revision': receipt['digest']})


def read(client, receipt):
    return Offices(client.store).read('alice', receipt['office_id'])


def test_new_office_uses_shared_onboarding_and_no_fabricated_balances(client, tmp_path):
    receipt = start(client)
    assert start(client) == receipt
    _, record = read(client, receipt)
    assert 'balance_sheet.json' not in record['documents']
    materialize(tmp_path, record)
    with hosted_office(tmp_path):
        status, _, html = local_request(tmp_path, 'GET', '/', b'', '')
    page = client.get(receipt['path'])
    assert status == page.status_code == 200
    for label in ('1 · Your holdings', '2 · Your income, as an asset', '3 · Life goals',
                  'Build my office', 'Read documents', 'id="onboarding-form"'):
        assert label in html.decode() and label in page.text
    assert receipt['path'] + '/onboard' in page.text
    assert 'read-only scan of this machine' not in page.text
    assert 'Install the local app' in page.text and 'IBKR Flex reports' in page.text
    assert 'nonce-' in page.headers['content-security-policy']
    assert ' onclick=' not in page.text and "querySelector('.rmrow').addEventListener" in page.text
    assert 'Continue setup' in client.get('/app').text


def test_creation_needs_session_origin_and_csrf(client):
    assert client.post('/api/offices/start', json={}).status_code == 401
    client.cookies.set(SESSION, 'alice'); client.get('/app')
    assert client.post('/api/offices/start', json={}).status_code == 403
    assert client.post('/api/offices/start', json={}, headers={'Origin': ORIGIN}).status_code == 403
    assert client.store.rows == {}


def test_bring_office_opens_shared_onboarding_not_backup_upload(client):
    assert client.get('/app/import', follow_redirects=False).headers['location'] == '/signup'
    client.cookies.set(SESSION, 'alice')
    first = client.get('/app/import', follow_redirects=False)
    assert first.status_code == 303 and first.headers['location'].startswith('/app/offices/')
    assert client.get('/app/import', follow_redirects=False).headers['location'] == first.headers['location']
    page = client.get(first.headers['location'])
    assert 'Build my office' in page.text and 'Your saved office folder' not in page.text
    assert 'Your saved office folder' in client.get('/app/import/saved').text


def test_draft_survives_restart_rejects_stale_tabs_and_is_private(client):
    receipt = start(client)
    data = {'rows': [['cash', 'Savings', '12345', '']], 'scalars': {'owner': 'Example'}, 'goals': [], 'profile': {}}
    result = draft(client, receipt, data)
    assert result.status_code == 204
    current, record = read(client, receipt)
    assert result.headers['x-office-revision'] == current['digest'] != receipt['digest']
    assert json.loads(base64.b64decode(record['documents']['draft.json'])) == data
    assert draft(client, receipt, {'rows': []}).status_code == 409
    with TestClient(create_app(Backend(), ORIGIN, store=client.store), base_url=ORIGIN) as restarted:
        restarted.cookies.set(SESSION, 'alice')
        assert 'Savings' in restarted.get(receipt['path']).text
        restarted.cookies.set(SESSION, 'bob')
        for suffix in ('', '/settings', '/export', '/documents'):
            assert restarted.get(receipt['path'] + suffix).status_code == 404


def test_draft_cannot_inject_script_or_credentials(client):
    receipt = start(client)
    payload = {'scalars': {'owner': '</script><script>window.bad=true</script>'}}
    assert draft(client, receipt, payload).status_code == 204
    page = client.get(receipt['path'])
    assert '<script>window.bad=true' not in page.text
    current, _ = read(client, receipt)
    before = deepcopy(client.store.rows)
    assert draft(client, current, {'api_key': 'private'}).status_code == 400
    assert client.store.rows == before


def test_build_preserves_identity_and_opens_shared_workspace(client):
    receipt = start(client)
    response = post(client, receipt, '/onboard', {'owner': 'Sample household', 'as_of': '2026-09-18',
        'u_kind': 'cash', 'u_name': 'Savings', 'u_value': '25000',
        'income_annual': '120000', 'income_years': '15', 'floor_amount': '10000', 'p_net_buyer': 'on'})
    assert response.status_code == 303, response.text
    current, record = read(client, receipt)
    assert current['status'] == 'active' and current['office_id'] == receipt['office_id']
    answers = json.loads(base64.b64decode(record['documents']['answers.json']))
    assert answers['office_id'] == receipt['office_id'] and answers['income']['annual'] == 120000
    assert 'draft.json' not in record['documents']
    page = client.get(receipt['path'])
    assert 'id="workspace-nav"' in page.text
    for page in ('office', 'goals', 'capital', 'strategies', 'imports'):
        assert client.get(receipt['path'] + '/pages/' + page + '.html').status_code == 200
    assert post(client, current, '/onboard', {'owner': 'overwrite'}).status_code == 400
    assert draft(client, current, {'rows': []}).status_code == 400
    assert start(client)['office_id'] != receipt['office_id']


def test_inline_csv_is_retained_relative_and_can_rebuild(client):
    receipt = start(client)
    response = post(client, receipt, '/onboard', {'owner': 'CSV example', 'as_of': '2026-09-18'},
                    files={'positions_csv': ('example.csv', b'Symbol,Value\nBIL,15000\n', 'text/csv')})
    assert response.status_code == 303, response.text
    current, record = read(client, receipt)
    answers = json.loads(base64.b64decode(record['documents']['answers.json']))
    assert answers['imports'][0]['path'] == 'positions.csv'
    assert post(client, current, '/growth', {'stocks_pct': '50', 'bonds_pct': '50'}).status_code == 303


def test_statement_staging_survives_job_and_build(client):
    receipt = start(client)
    queue = Queue(); client.app.state.jobs.queue = queue
    response = post(client, receipt, '/import/files', files={'docs': ('example.csv', b'Symbol,Value\nBIL,15000\n', 'text/csv')})
    assert response.status_code == 303
    client.app.state.jobs.run(*queue.items[0])
    job, _ = client.app.state.jobs.read(*queue.items[0])
    assert job['status'] == 'complete' and job['response']['status'] == 303, job
    current, record = read(client, receipt)
    assert current['status'] == 'onboarding'
    assert 'staging.json' in record['documents'] and any(k.startswith('attachments/') for k in record['documents'])
    page = client.get(receipt['path'])
    assert 'BIL' in page.text and '15000' in page.text
    assert client.get(receipt['path'] + '/pages/imports.html').status_code == 200
    response = post(client, current, '/onboard', {'u_kind': 'ticker', 'u_name': 'BIL', 'u_value': '15000', 'as_of': '2026-09-18'})
    assert response.status_code == 303
    assert read(client, receipt)[0]['status'] == 'active'


def test_natural_language_intake_and_classification_use_tenant_jobs(client, monkeypatch):
    receipt = start(client)
    queue = Queue(); client.app.state.jobs.queue = queue
    Credentials(Offices(client.store)).update('alice', receipt['office_id'], {
        'provider': 'anthropic', 'credential_revision': '0', 'ANTHROPIC_API_KEY': 'tenant-key'})
    vault = Credentials(Offices(client.store))
    vault.update('alice', receipt['office_id'], {
        'provider': 'openai', 'credential_revision': vault.status('alice', receipt['office_id'])['revision'],
        'OPENAI_API_KEY': 'tenant-openai-key'})
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'machine-key')
    def turn(messages, **kwargs):
        from officekit_ai.models import resolve_key
        assert resolve_key('OPENAI_API_KEY') == 'tenant-openai-key'
        return {'reply': 'Review the goal fields.', 'answers': {'goals': [{'kind': 'liquidity_floor', 'amount': 50000}]}}
    monkeypatch.setattr('officekit_ai.intake_chat.turn', turn)
    page = client.get(receipt['path'])
    assert 'Or describe your assets' in page.text and 'Or describe your goals' in page.text
    response = client.post(receipt['path'] + '/chat', json={'scope': 'goals', 'messages': []}, headers={
        'Origin': ORIGIN, 'X-CSRF-Token': client.cookies.get(CSRF), 'X-Office-Revision': receipt['digest']})
    assert response.status_code == 202
    client.app.state.jobs.run(*queue.items[-1])
    result = client.get(response.json()['job'] + '/result')
    assert result.json()['answers']['goals'][0]['amount'] == 50000
    assert result.headers['x-office-revision'] == read(client, receipt)[0]['digest']
    # A completed response remains tied to the facts it used, even if another
    # tab saves before this browser retrieves it. Polling must not waive CAS.
    completed_revision = result.headers['x-office-revision']
    current, _ = read(client, receipt)
    assert draft(client, current, {'rows': [], 'scalars': {'owner': 'Newer tab'}}).status_code == 204
    assert client.get(response.json()['job'] + '/result').headers['x-office-revision'] == completed_revision
    monkeypatch.setattr('officekit.serve._classify_unknowns', lambda *a: [{'symbol': 'SAMPLE', 'category': 'equity', 'confidence': .9}])
    current, _ = read(client, receipt)
    response = post(client, current, '/onboard', {'u_kind': 'ticker', 'u_name': 'SAMPLE', 'u_value': '100'})
    assert '/jobs/' in response.headers['location']
    client.app.state.jobs.run(*queue.items[-1])
    result = client.get(response.headers['location'] + '/result')
    assert result.status_code == 200 and '/onboard/confirm' in result.text
    current, _ = read(client, receipt)
    response = post(client, current, '/onboard/confirm', {'answers_json': json.dumps({
        'owner': 'Example', 'as_of': '2026-09-18', 'sleeves': [{'category': 'cash', 'value': 100}]})})
    assert response.status_code == 303, response.text
    assert read(client, receipt)[0]['status'] == 'active'


def test_beginner_actions_do_not_mutate_draft_before_build(client):
    receipt = start(client)
    before = deepcopy(client.store.rows)
    assert post(client, receipt, '/growth', {'stocks_pct': '50'}).status_code == 400
    assert client.store.rows == before
