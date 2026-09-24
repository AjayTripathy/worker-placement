"""Browser migration uses real snapshot/hosted contracts with synthetic offices."""
import json
import re
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest
from officekit import cloud
from officekit.hosting_ui import Hosting
from officekit.migration import snapshot, validate_manifest
from test_hosted_migration import office, client, ORIGIN


@pytest.fixture
def bridge(office, client, monkeypatch, tmp_path):
    auth = {'origin': ORIGIN, 'token': 'alice', 'email': 'alice@example.com', 'expires_at': time.time()+3600}
    monkeypatch.setenv('WORKER_PLACEMENT_CONFIG_DIR', str(tmp_path/'credentials'))
    monkeypatch.setattr(cloud, 'credentials', lambda: dict(auth))
    calls = []

    def request(origin, path, payload=None, token=None):
        assert origin == ORIGIN
        calls.append((path, payload))
        headers = {'Authorization': 'Bearer '+token} if token else {}
        response = client.get(path, headers=headers) if payload is None else client.post(path, json=payload, headers=headers)
        if response.status_code >= 400:
            raise ValueError(response.json()['error'])
        return response.json()
    monkeypatch.setattr(cloud, 'request', request)
    return Hosting(office), calls, auth, request


def settled(hosting):
    deadline = time.monotonic()+8
    while time.monotonic() < deadline:
        state = hosting.view()
        if not state['busy']:
            return state
        time.sleep(.01)
    raise AssertionError('Hosting action did not finish')


def review(hosting):
    hosting.review()
    state = settled(hosting)
    assert state['phase'] == 'review', state
    return state['preview']


def test_review_is_read_only_then_explicit_upload_preserves_files(bridge, office):
    hosting, calls, _, _ = bridge
    before = snapshot(office)
    preview = review(hosting)
    assert preview['email'] == 'alice@example.com'
    assert any(f['path']=='research/memo.md' for f in preview['files'])
    assert not any(path.startswith('/api/migrations') for path, _ in calls)
    assert 'token' not in json.dumps(hosting.view()) and 'proof' not in json.dumps(hosting.view())
    hosting.upload(preview['id'])
    state = settled(hosting)
    assert state['phase']=='complete', state
    assert state['url'].startswith(ORIGIN+'/app/offices/')
    assert validate_manifest(snapshot(office)[0])==validate_manifest(before[0])
    assert (office/'.hosted-receipt.json').exists()


@pytest.mark.parametrize('change', ['files', 'account', 'expiry'])
def test_stale_review_never_starts_a_transfer(bridge, office, change):
    hosting, calls, auth, _ = bridge
    preview = review(hosting)
    if change=='files':(office/'research/memo.md').write_text('New finding after review')
    elif change=='account':auth['token']='bob'
    else:hosting.prepared['created']-=901
    if change=='expiry':
        with pytest.raises(ValueError, match='expired'):hosting.upload(preview['id'])
    else:
        hosting.upload(preview['id'])
        assert settled(hosting)['phase']=='error'
    assert not any(path.startswith('/api/migrations') for path, _ in calls)


def test_replacement_requires_explicit_confirmation_of_reviewed_revision(bridge, office):
    hosting, calls, _, _ = bridge
    hosting.upload(review(hosting)['id']);assert settled(hosting)['phase']=='complete'
    previous = json.loads((office/'.hosted-receipt.json').read_text())['digest']
    (office/'research/memo.md').write_text('A newer finding')
    preview = review(hosting)
    assert preview['replace_required']
    count = len(calls)
    with pytest.raises(ValueError, match='Confirm'):hosting.upload(preview['id'])
    assert len(calls)==count
    hosting.upload(preview['id'], True)
    assert settled(hosting)['phase']=='complete'
    activations = [payload for path,payload in calls if path.endswith('/activate')]
    assert activations[-1]['replace_revision']==previous


def test_failed_upload_can_resume_without_repeating_stored_chunks(bridge, monkeypatch):
    hosting, calls, _, original = bridge
    preview = review(hosting)
    stored = []
    failed = False

    def flaky(origin, path, payload=None, token=None):
        nonlocal failed
        if path.endswith('/chunks'):
            if stored and not failed:
                failed=True
                raise ValueError('The hosted service could not be reached. Retry when your connection returns.')
            stored.append(payload['sha256'])
        return original(origin,path,payload,token)
    monkeypatch.setattr(cloud,'request',flaky)
    hosting.upload(preview['id']);assert settled(hosting)['phase']=='error'
    hosting.upload(preview['id']);assert settled(hosting)['phase']=='complete'
    assert len(stored)==len(set(stored))


def test_login_keeps_proof_and_credential_out_of_browser(office, monkeypatch, tmp_path):
    monkeypatch.setenv('WORKER_PLACEMENT_CONFIG_DIR',str(tmp_path/'auth'))
    def missing():raise ValueError('Run ./wp login')
    monkeypatch.setattr(cloud,'credentials',missing)
    monkeypatch.setattr(cloud,'begin_login',lambda:{'origin':ORIGIN,'proof':'PRIVATE_DEVICE_PROOF','code':'AABBCCDD','url':ORIGIN+'/cli','device':'test'})
    monkeypatch.setattr(cloud,'poll_login',lambda pending:{'status':'approved','email':'alice@example.com','token':'PRIVATE_SESSION','expires_at':time.time()+3600})
    hosting=Hosting(office);hosting.login();state=settled(hosting)
    assert state['connected'] and state['email']=='alice@example.com'
    assert 'PRIVATE' not in json.dumps(state)
    assert cloud.config_path().stat().st_mode & 0o777 == 0o600
    assert not (office/'.hosted-receipt.json').exists()


def test_loopback_origin_and_page_token_protect_http_bridge(bridge, office):
    from officekit.serve import make_handler
    server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(office))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base='http://127.0.0.1:'+str(server.server_address[1])
    try:
        with urllib.request.urlopen(base+'/hosting') as response:
            html=response.read().decode()
            assert response.headers['Cache-Control']=='no-store'
            assert response.headers['Content-Security-Policy']=="frame-ancestors 'self'"
        csrf=json.loads(re.search(r'const token=("[^"]+")',html).group(1))
        from local_http import headers as session_headers
        local_token = session_headers(base)['X-Office-Local-CSRF']
        def req(path, payload=None, **headers):
            request=urllib.request.Request(base+path,data=None if payload is None else json.dumps(payload).encode(),headers=headers)
            try:
                with urllib.request.urlopen(request) as r:return r.status,json.load(r)
            except urllib.error.HTTPError as e:return e.code,json.load(e)
        assert req('/hosting/status')[0]==403
        good={'X-Office-Hosting':csrf,'X-Office-Local-CSRF':local_token,'Content-Type':'application/json','Origin':base}
        assert req('/hosting/status',**good)[0]==200
        assert req('/hosting/review',{},**{**good,'Origin':'https://evil.example'})[0]==403
        assert req('/hosting/review',{},**{**good,'Host':'evil.example'})[0]==403
        assert req('/hosting/review',{},**{k:v for k,v in good.items() if k!='Origin'})[0]==403
        assert req('/hosting/review',{},**good)[0]==202
        with urllib.request.urlopen(base+'/') as r:
            assert 'href="/settings"' in r.read().decode()
    finally:
        server.shutdown();server.server_close()
