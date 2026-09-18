"""Tenant isolation and durable delivery regression tests; no external calls."""
import base64
from copy import deepcopy
import io
import json
import time
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from test_hosted_migration import Backend, MemoryStore, ORIGIN, office, upload, send
from test_hosted_workspace import workspace, post
from hosting.app.main import create_app, SESSION
from hosting.app.credentials import Credentials
from hosting.app.offices import Offices
from hosting.app.jobs import Jobs
from hosting.app.auth import AuthFailure
from officekit.runtime import hosted_office


class Queue:
    def __init__(self): self.items = []
    def submit(self, uid, oid, jid): self.items.append((uid, oid, jid))
    def verify(self, token):
        if token != 'worker': raise AuthFailure('Worker authentication required.', 403)


def test_natural_language_goals_use_durable_office_scoped_intake(workspace, monkeypatch):
    client, receipt, folder = workspace
    queue = Queue(); client.app.state.jobs.queue = queue
    offices = Offices(client.store)
    Credentials(offices).update('alice', receipt['office_id'], {
        'provider': 'anthropic', 'credential_revision': '0', 'ANTHROPIC_API_KEY': 'tenant-key'})
    calls = []
    def turn(messages, **kwargs):
        from officekit_ai.models import resolve_key
        assert resolve_key() == 'tenant-key' and kwargs['scope'] == 'goals'
        calls.append(messages)
        return {'answers': {'goals': [{'kind': 'spending', 'label': 'College', 'amount': 300000, 'date': '2038-01-01'}]}}
    monkeypatch.setattr('officekit_ai.intake_chat.turn', turn)
    response = post(client, receipt, '/goals/add', {'back': 'goals', 'nl': 'Save $300k for college by 2038.'})
    assert response.status_code == 303 and '/jobs/' in response.headers['location']
    assert calls == []
    uid, oid, jid = queue.items[0]
    Jobs(offices, queue).run(uid, oid, jid)
    Jobs(offices, queue).run(uid, oid, jid)
    job, _ = client.app.state.jobs.read(uid, oid, jid)
    assert len(calls) == 1 and job['response']['status'] == 303
    assert job['response']['headers']['Location'] == '/pages/goals.html'
    page = client.get(receipt['path'] + '/pages/goals.html')
    assert 'College' in page.text and receipt['path'] + '/goals/add' in page.text
    assert 'nonce-' in page.headers['content-security-policy']


def test_manual_goal_does_not_need_background_queue(workspace):
    client, receipt, _ = workspace
    response = post(client, receipt, '/goals/add', {
        'back': 'goals', 'gkind': 'spending', 'glabel': 'Car', 'gamt': '50000'})
    assert response.status_code == 303
    assert response.headers['location'] == receipt['path'] + '/pages/goals.html'


def test_credentials_are_scoped_revisioned_and_never_exported(workspace):
    client, receipt, _ = workspace
    fields = {'provider': 'anthropic', 'credential_revision': '0', 'ANTHROPIC_API_KEY': 'tenant-key'}
    assert post(client, receipt, '/settings/credentials', fields).status_code == 303
    assert post(client, receipt, '/settings/credentials', fields).status_code == 409
    vault = Credentials(Offices(client.store))
    assert vault.read('alice', receipt['office_id'])[0]['ANTHROPIC_API_KEY'] == 'tenant-key'
    with pytest.raises(AuthFailure): vault.read('bob', receipt['office_id'])
    for suffix in ('/settings', '/export', '/documents', '/pages/imports.html'):
        assert b'tenant-key' not in client.get(receipt['path'] + suffix).content
    revision = vault.status('alice', receipt['office_id'])['revision']
    assert post(client, receipt, '/settings/credentials', dict(provider='anthropic', credential_revision=revision, remove='1')).status_code == 303
    assert not vault.read('alice', receipt['office_id'])[0]


def test_hosted_keys_never_fall_back_to_machine_even_in_upload_threads(tmp_path, monkeypatch):
    from officekit_ai.models import resolve_key, key_source
    from officekit.serve import import_files
    from officekit_ai import extract
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'machine-key')
    def extract_file(name, data, folder=None):
        assert resolve_key() == 'tenant-key'
        return {'rows': [], 'warnings': []}
    monkeypatch.setattr(extract, 'extract_file', extract_file)
    with hosted_office(tmp_path):
        assert resolve_key() is None and key_source() is None
    part = Mock(filename='statement.pdf', file=io.BytesIO(b'%PDF sample'))
    with hosted_office(tmp_path, {'ANTHROPIC_API_KEY': 'tenant-key'}):
        assert not any('FAILED' in v for v in import_files(tmp_path, [part]))
    assert resolve_key() == 'machine-key'


def test_broker_allowlist_applies_to_discovery_and_fetch(tmp_path, monkeypatch):
    import officekit_adapters as adapters
    monkeypatch.setenv('APCA_API_KEY_ID', 'machine-id')
    monkeypatch.setenv('APCA_API_SECRET_KEY', 'machine-secret')
    with hosted_office(tmp_path):
        results = adapters.discover()
        assert {r['name'] for r in results} == {'alpaca', 'ibkr_flex'}
        assert not any(r['found'] for r in results)
        for name in ('downloads_csv', 'ibkr_socket', 'ibkr_portal', 'unknown'):
            with pytest.raises(ValueError): adapters.fetch_snapshot(name)


def test_durable_jobs_survive_restart_reject_writes_and_duplicate_deliveries(workspace, monkeypatch):
    client, receipt, _ = workspace
    offices = Offices(client.store);queue = Queue();jobs = Jobs(offices, queue)
    raw = b'stocks_pct=51&bonds_pct=49'
    jid = jobs.start('alice', receipt['office_id'], '/growth', raw, 'application/x-www-form-urlencoded', receipt['digest'])
    assert post(client, receipt, '/growth', {'stocks_pct': '1'}).status_code == 409
    restarted = Jobs(Offices(client.store), queue)
    restarted.run('alice', receipt['office_id'], jid)
    record, _ = restarted.read('alice', receipt['office_id'], jid)
    assert record['status'] == 'complete', record
    assert record['response']['status'] == 303
    after = deepcopy(client.store.rows)
    restarted.run('alice', receipt['office_id'], jid)
    assert client.store.rows == after
    current, saved = offices.read('alice', receipt['office_id'])
    assert 'job' not in current
    assert json.loads(base64.b64decode(saved['documents']['answers.json']))['target_mix']['stocks_pct'] == 51
    with pytest.raises(AuthFailure): restarted.read('bob', receipt['office_id'], jid)


def test_running_or_expired_attempt_is_not_rebilled(workspace):
    client, receipt, _ = workspace
    jobs = Jobs(Offices(client.store), Queue());oid = receipt['office_id']
    jid = jobs.start('alice', oid, '/chat', b'{}', 'application/json', receipt['digest'])
    key = jobs.key('alice', oid, jid)
    record, generation = client.store.get(key)
    record.update(status='running', expires=time.time()-1)
    client.store.put(key, record, generation)
    before = deepcopy(client.store.rows)
    jobs.run('alice', oid, jid)
    assert client.store.rows == before
    assert jobs.read('alice', oid, jid)[0]['status'] == 'interrupted'


def test_upload_route_queues_and_result_is_saved(workspace):
    client, receipt, folder = workspace
    queue = Queue();client.app.state.jobs.queue = queue
    response = post(client, receipt, '/import/files', files={'docs': ('positions.csv', b'Symbol,Value\nTEST,123\n', 'text/csv')})
    assert response.status_code == 303, response.text
    assert '/jobs/' in response.headers['location']
    uid, oid, jid = queue.items[0]
    client.app.state.jobs.run(uid, oid, jid)
    record, _ = client.app.state.jobs.read(uid, oid, jid)
    assert record['response']['status'] == 303, record
    _, saved = Offices(client.store).read(uid, oid)
    assert any(n.startswith('attachments/') for n in saved['documents'])
    assert 'staging.json' in saved['documents']
    client.cookies.set(SESSION, 'bob')
    assert client.get(response.headers['location']).status_code == 404


def test_worker_endpoint_rejects_browser_and_unknown_identity(workspace):
    client, _, _ = workspace
    client.app.state.jobs.queue = Queue()
    assert client.post('/internal/office-job', json={}).status_code == 403
    assert client.post('/internal/office-job', json={}, headers={'Authorization': 'Bearer alice'}).status_code == 403


def test_greeting_uses_browser_time_without_injecting_owner(workspace):
    client, receipt, _ = workspace
    page = client.get(receipt['path'] + '/pages/office.html').text
    assert 'new Date().getHours()' in page and 'data-owner=' in page


def test_proposal_checkpoints_survive_new_worker_and_belong_to_office(workspace, monkeypatch):
    from officekit.commitments import revision
    import officekit_ai.strategy_proposal as pipeline
    import officekit_ai
    from hosting.app.workspace import materialize
    client, receipt, folder = workspace
    queue = Queue();client.app.state.jobs.queue = queue
    offices = Offices(client.store);vault=Credentials(offices)
    vault.update('alice',receipt['office_id'],{'provider':'anthropic','credential_revision':'0','ANTHROPIC_API_KEY':'tenant-key'})
    monkeypatch.setattr(officekit_ai,'available',lambda *a,**k:True)
    calls=[]
    def build(p, temp, checkpoint):
        from officekit_ai.models import resolve_key
        assert resolve_key()=='tenant-key'
        calls.append(p['id'])
        checkpoint('Synthetic research saved', research={'verified': True})
        _, current=offices.read('alice',receipt['office_id'])
        value=json.loads(base64.b64decode(current['documents']['strategy_proposals/'+p['id']+'.json']))
        assert value['research']=={'verified': True}
        checkpoint('Ready for review',status='needs_review')
    monkeypatch.setattr(pipeline,'build_proposal',build)
    answers=json.loads((folder/'answers.json').read_text())
    result=post(client,receipt,'/strategy/new',{'revision':revision(answers),'title':'Test proposal','target_pct':'5'})
    assert result.status_code==303,result.text
    uid,oid,jid=queue.items[0]
    Jobs(offices,queue).run(uid,oid,jid)
    state,_=client.app.state.jobs.read(uid,oid,jid)
    assert state['status']=='complete',state
    assert state['response']['status']==303,state
    assert len(calls)==1
    Jobs(offices,queue).run(uid,oid,jid)
    assert len(calls)==1


def test_flex_rejects_untrusted_report_destination(monkeypatch):
    from officekit_adapters import ibkr_flex
    calls=[]
    def http(url,**kwargs):
        calls.append(url)
        return '<FlexStatementResponse><Status>Success</Status><ReferenceCode>123</ReferenceCode><Url>https://example.invalid/report</Url></FlexStatementResponse>'
    monkeypatch.setattr(ibkr_flex,'_http_get',http)
    with pytest.raises(ValueError,match='unrecognized'):
        ibkr_flex.fetch_flex('test-token','123')
    assert len(calls)==1


def test_local_main_starts_server_and_sync_without_running_real_connectors(tmp_path, monkeypatch):
    import officekit.serve as serve
    started=[]
    class Thread:
        def __init__(self, target, **kwargs):self.target=target
        def start(self):started.append(self.target.__name__)
    class Server:
        def __init__(self, address, handler):assert address[0]=='127.0.0.1'
        def serve_forever(self):started.append('serve_forever')
    monkeypatch.setattr(serve.threading,'Thread',Thread)
    monkeypatch.setattr(serve,'ThreadingHTTPServer',Server)
    monkeypatch.setattr(serve,'make_handler',lambda folder:object())
    serve.main(['--dir',str(tmp_path/'office'),'--port','0'])
    assert set(started)=={'loop','_daily_pull_loop','serve_forever'}
