"""Browser transfer uses reviewed snapshots and CSRF, independently of CLI grants."""
import base64
import json

import pytest

from hosting.app.main import CSRF, SESSION
from hosting.app.offices import Offices
from hosting.app.credentials import Credentials
from officekit.migration import snapshot
from test_hosted_migration import client, office, ORIGIN


def browser(client):
    client.cookies.set(SESSION, 'alice')
    assert client.get('/app/import/saved').status_code == 200


def post(client, path, data):
    return client.post(path, json=data, headers={'Origin': ORIGIN, 'X-CSRF-Token': client.cookies.get(CSRF)})


def stage(client, folder):
    manifest, chunks = snapshot(folder)
    started = post(client, '/api/browser-migrations', {'manifest': manifest})
    assert started.status_code == 200, started.text
    sid = started.json()['digest']
    for digest in started.json()['missing']:
        result = post(client, '/api/browser-migrations/'+sid+'/chunks', {'sha256': digest, 'data': base64.b64encode(chunks[digest]).decode()})
        assert result.status_code == 200, result.text
    return sid, manifest


def test_account_and_signed_in_browser_import_page(client):
    assert client.get('/app/import/saved', follow_redirects=False).headers['location'] == '/signup'
    assert client.get('/api/browser-migrations/config').status_code == 401
    browser(client)
    page = client.get('/app/import/saved')
    assert 'webkitdirectory' in page.text and '/public/office-import.js' in page.text
    assert 'Nothing uploads until' in page.text and 'alice@example.com' in page.text
    assert "script-src 'self'" in page.headers['content-security-policy']
    assert '/app/import/saved' in client.get('/app').text
    assert client.get('/public/office-import.js').status_code == 200
    assert client.store.rows == {}


@pytest.mark.parametrize('suffix,payload', [('', {'manifest': {}}), ('/'+'a'*64+'/chunks', {}), ('/'+'a'*64+'/activate', {})])
def test_every_browser_mutation_requires_session_origin_and_csrf(client, suffix, payload):
    path = '/api/browser-migrations'+suffix
    assert client.post(path, json=payload).status_code == 401
    browser(client)
    assert client.post(path, json=payload).status_code == 403
    assert client.post(path, json=payload, headers={'Origin': 'https://evil.example', 'X-CSRF-Token': client.cookies.get(CSRF)}).status_code == 403
    assert client.post(path, json=payload, headers={'Origin': ORIGIN, 'X-CSRF-Token': 'wrong'}).status_code == 403
    assert client.store.rows == {}


def test_browser_upload_preserves_facts_and_research_and_resumes(client, office):
    browser(client)
    sid, manifest = stage(client, office)
    assert Offices(client.store).listing('alice') == []  # Upload alone never activates.
    assert post(client, '/api/browser-migrations', {'manifest': manifest}).json()['missing'] == []
    response = post(client, '/api/browser-migrations/'+sid+'/activate', {})
    assert response.status_code == 200, response.text
    receipt, record = Offices(client.store).read('alice', manifest['office_id'])
    assert base64.b64decode(record['documents']['answers.json']) == (office/'answers.json').read_bytes()
    assert base64.b64decode(record['documents']['research/memo.md']) == b'Retained diligence'
    assert client.get(receipt['path']).status_code == 200
    client.cookies.set(SESSION, 'bob')
    assert post(client, '/api/browser-migrations/'+sid+'/activate', {}).status_code == 404
    assert post(client, '/api/browser-migrations/'+sid+'/chunks', {'sha256': 'a'*64, 'data': ''}).status_code == 404
    assert client.get(receipt['path']).status_code == 404


def test_replacement_requires_reviewed_revision_and_keeps_hosted_key(client, office):
    browser(client)
    sid, manifest = stage(client, office)
    assert post(client, '/api/browser-migrations/'+sid+'/activate', {}).status_code == 200
    credentials = Credentials(Offices(client.store))
    credentials.update('alice', manifest['office_id'], {'provider': 'anthropic', 'credential_revision': '0', 'ANTHROPIC_API_KEY': 'test-key'})
    (office/'research/memo.md').write_text('Updated research')
    new_sid, _ = stage(client, office)
    path = '/api/browser-migrations/'+new_sid+'/activate'
    assert post(client, path, {}).status_code == 409
    assert post(client, path, {'replace_revision': 'stale'}).status_code == 409
    assert Offices(client.store).read('alice', manifest['office_id'])[0]['digest'] == sid
    assert post(client, path, {'replace_revision': sid}).status_code == 200
    assert credentials.status('alice', manifest['office_id'])['connected']['anthropic']


def test_incomplete_and_invalid_records_do_not_activate(client, office):
    browser(client)
    manifest, chunks = snapshot(office)
    sid = post(client, '/api/browser-migrations', {'manifest': manifest}).json()['digest']
    assert post(client, '/api/browser-migrations/'+sid+'/activate', {}).status_code == 409
    assert post(client, '/api/browser-migrations/'+sid+'/chunks', {'sha256': next(iter(chunks)), 'data': base64.b64encode(b'wrong').decode()}).status_code == 400
    manifest['files'][0]['path'] = '../credentials.json'
    assert post(client, '/api/browser-migrations', {'manifest': manifest}).status_code == 400
    assert Offices(client.store).listing('alice') == []


def test_credential_bearing_snapshot_is_rejected_on_activation(client, office):
    from officekit.migration import digest, CHUNK
    browser(client)
    manifest, chunks = snapshot(office)
    answers = json.loads((office/'answers.json').read_text())
    answers['api_key'] = 'synthetic-secret'
    raw = json.dumps(answers).encode()
    parts = [raw[i:i+CHUNK] for i in range(0, len(raw), CHUNK)]
    chunks.update({digest(part): part for part in parts})
    entry = next(f for f in manifest['files'] if f['path'] == 'answers.json')
    entry.update(size=len(raw), sha256=digest(raw), chunks=[digest(part) for part in parts])
    response = post(client, '/api/browser-migrations', {'manifest': manifest})
    assert response.status_code == 200
    sid = response.json()['digest']
    for h in response.json()['missing']:
        assert post(client, '/api/browser-migrations/'+sid+'/chunks', {'sha256':h, 'data':base64.b64encode(chunks[h]).decode()}).status_code == 200
    response = post(client, '/api/browser-migrations/'+sid+'/activate', {})
    assert response.status_code == 400 and 'synthetic-secret' not in response.text
    assert Offices(client.store).listing('alice') == []


def test_browser_configuration_matches_snapshot_limits(client):
    from officekit import migration
    browser(client)
    rules = client.get('/api/browser-migrations/config').json()
    assert set(rules['root_files']) == migration.ROOT_FILES
    assert set(rules['retained']) == migration.RETAINED
    assert set(rules['suffixes']) == migration.SUFFIXES
    assert rules['chunk_bytes'] == migration.CHUNK and rules['max_bytes'] == migration.MAX_TOTAL
    assert rules['max_files'] == migration.MAX_FILES
