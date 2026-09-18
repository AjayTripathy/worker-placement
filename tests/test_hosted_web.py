"""Public boundary and verified-session contract; no mail or cloud calls."""
import logging
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient
from hosting.app.auth import AuthFailure, RateLimit
from hosting.app.main import create_app, CSRF, SESSION

ORIGIN = 'https://office.example'

class Backend:
    def __init__(self):
        self.sent = []
        self.used = set()
        self.revoked = False
    def send_email(self, email):
        self.sent.append(email)
    def complete(self, email, code):
        if code in self.used or code != 'a-valid-code-123':
            raise AuthFailure('This link is invalid, expired or already used.')
        self.used.add(code)
        return 'verified-session'
    def verify(self, cookie):
        if cookie != 'verified-session' or self.revoked:
            raise AuthFailure('Sign in again to continue.', 401)
        return {'uid':'member-a', 'email':'member@example.com', 'email_verified':True}

@pytest.fixture
def client():
    backend = Backend()
    with TestClient(create_app(backend, ORIGIN), base_url=ORIGIN) as client:
        client.backend = backend
        client.get('/signup')
        yield client

def post(client, path, data=None, **kwargs):
    headers = {'Origin':ORIGIN, 'X-CSRF-Token':client.cookies.get(CSRF), **kwargs.pop('headers',{})}
    return client.post(path, json=data or {}, headers=headers, **kwargs)

def sign_in(client):
    return post(client, '/api/auth/complete', {'email':'member@example.com','code':'a-valid-code-123'})

def test_public_pages_are_private_data_free_and_hardened(client):
    for path in ('/', '/welcome','/signup','/guides/local','/privacy'):
        r=client.get(path)
        assert r.status_code == 200
        assert r.headers['cache-control'] == 'no-store'
        assert r.headers['referrer-policy'] == 'no-referrer'
        assert "frame-ancestors 'none'" in r.headers['content-security-policy']
        assert 'data-office-api-errors' not in r.text
    for path in ('/answers.json','/api-errors','/pages/office.html','/openapi.json','/public/landing.html'):
        assert client.get(path).status_code == 404
    assert client.get('/public/site.css').status_code == 200
    assert client.get('/api/me').status_code == 401
    assert client.get('/app',follow_redirects=False).headers['location'] == '/signup'

def test_scanner_get_does_not_exchange_or_reflect_code(client):
    r=client.get('/auth/finish?mode=signIn&oobCode=secret-test-code')
    assert r.status_code == 200 and 'secret-test-code' not in r.text
    assert not client.backend.used and not client.cookies.get(SESSION)

def test_email_send_requires_csrf_and_same_origin(client):
    data={'email':'member@example.com'}
    assert client.post('/api/auth/email',json=data).status_code == 403
    assert post(client,'/api/auth/email',data,headers={'Origin':'https://evil.example'}).status_code == 403
    assert post(client,'/api/auth/email',data,headers={'X-CSRF-Token':'wrong'}).status_code == 403
    assert not client.backend.sent
    assert post(client,'/api/auth/email',data).status_code == 200
    assert client.backend.sent == [data['email']]
    assert post(client,'/api/auth/email',data).status_code == 429

def test_verified_session_replay_logout_and_revocation(client):
    r=sign_in(client)
    assert r.status_code == 200
    cookie=r.headers['set-cookie']
    assert '__Host-wp_session=' in cookie and 'HttpOnly' in cookie and 'Secure' in cookie and 'SameSite=lax' in cookie and 'Path=/' in cookie
    assert client.get('/api/me').json() == {'email':'member@example.com','email_verified':True,'office_migration':'not_available'}
    assert 'member@example.com' in client.get('/app').text
    assert sign_in(client).status_code == 400
    client.backend.revoked = True
    assert client.get('/api/me').status_code == 401
    client.backend.revoked = False
    assert post(client,'/api/auth/logout').status_code == 200
    assert not client.cookies.get(SESSION)
    assert client.get('/api/me').status_code == 401

def test_forged_session_is_rejected(client):
    client.cookies.set(SESSION,'forged')
    assert client.get('/api/me').status_code == 401
    assert client.get('/app',follow_redirects=False).status_code == 303

def test_bad_input_and_body_limit(client):
    assert post(client,'/api/auth/email',{'email':'bad'}).status_code == 400
    assert post(client,'/api/auth/email',{'email':'x'*5000}).status_code == 413
    assert post(client,'/api/auth/complete',{'email':'a@example.com','code':'bad?'}).status_code == 400
    headers={'Origin':ORIGIN,'X-CSRF-Token':client.cookies.get(CSRF),'Content-Type':'application/json'}
    assert client.post('/api/auth/email',content=b'{',headers=headers).status_code == 400

def test_unexpected_error_logged_but_not_returned(client,caplog):
    def fail(email):raise RuntimeError('private-server-detail')
    client.backend.send_email=fail
    with caplog.at_level(logging.ERROR):
        r=post(client,'/api/auth/email',{'email':'a@example.com'})
    assert r.status_code == 500 and 'private-server-detail' not in r.text
    assert 'private-server-detail' in caplog.text

def test_provider_failure_remains_friendly(client):
    def fail(email):raise AuthFailure('Email provider is unavailable.',502)
    client.backend.send_email=fail
    assert post(client,'/api/auth/email',{'email':'a@example.com'}).status_code == 502

def test_unconfigured_service_fails_closed():
    with TestClient(create_app(origin=''),base_url=ORIGIN) as c:
        assert 'being configured' in c.get('/signup').text
        assert c.post('/api/auth/email',json={'email':'a@example.com'}).status_code == 503
        assert c.get('/api/me').status_code == 401

@pytest.mark.parametrize('origin',['http://example.com','https://u:p@example.com','https://example.com/path','https://example.com?x=1'])
def test_invalid_origin_rejected(origin):
    with pytest.raises(ValueError):create_app(Backend(),origin)

def test_source_staging_contains_shared_engine_but_no_customer_data(tmp_path):
    from hosting.gcp.stage_web import stage
    target=stage(tmp_path/'source')
    assert (target/'officekit/public/landing.html').is_file()
    assert (target/'officekit/serve.py').exists()
    assert (target/'officekit/runtime.py').exists()
    assert not (target/'desk').exists()
    assert not (target/'officekit/evals').exists()
    assert not (target/'officekit/answers.json').exists()
    assert not list(target.rglob('.git'))
    with pytest.raises(ValueError):stage(target)


def test_deleted_account_session_requires_signin(monkeypatch):
    from firebase_admin import auth
    from hosting.app.auth import FirebaseBackend
    backend=FirebaseBackend.__new__(FirebaseBackend)
    backend.app=object()
    def missing(*args,**kwargs):
        raise auth.UserNotFoundError('No user record')
    monkeypatch.setattr(auth,'verify_session_cookie',missing)
    with pytest.raises(AuthFailure) as caught:
        backend.verify('previously-valid-session')
    assert caught.value.status == 401
