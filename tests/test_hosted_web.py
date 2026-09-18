"""Public boundary and verified-session contract; no mail or cloud calls."""
import logging
from urllib.parse import urlparse, parse_qs

import pytest
from fastapi.testclient import TestClient
from hosting.app.auth import AuthFailure, RateLimit
from hosting.app.main import create_app, CSRF, SESSION, OAUTH

ORIGIN = 'https://office.example'

class Backend:
    def __init__(self):
        self.sent = []
        self.used = set()
        self.revoked = False
        self.google_calls = []
    def begin_google(self):
        return 'https://accounts.google.com/o/oauth2/auth?state=provider-state', 'p'*43
    def complete_google(self, callback, proof):
        self.google_calls.append((callback, proof))
        values = parse_qs(urlparse(callback).query)
        if values != {'code':['google-code'], 'state':['provider-state']} or proof != 'p'*43 or 'google-code' in self.used:
            raise AuthFailure('This sign-in attempt could not be verified.', 401)
        self.used.add('google-code')
        return 'verified-session'
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

def test_retired_email_send_requires_csrf_and_never_sends(client):
    data={'email':'member@example.com'}
    assert client.post('/api/auth/email',json=data).status_code == 403
    assert post(client,'/api/auth/email',data,headers={'Origin':'https://evil.example'}).status_code == 403
    assert post(client,'/api/auth/email',data,headers={'X-CSRF-Token':'wrong'}).status_code == 403
    assert not client.backend.sent
    assert post(client,'/api/auth/email',data).status_code == 410
    assert not client.backend.sent

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
    assert post(client,'/api/auth/complete',{'email':'bad'}).status_code == 400
    assert post(client,'/api/auth/email',{'email':'x'*5000}).status_code == 413
    assert post(client,'/api/auth/complete',{'email':'a@example.com','code':'bad?'}).status_code == 400
    headers={'Origin':ORIGIN,'X-CSRF-Token':client.cookies.get(CSRF),'Content-Type':'application/json'}
    assert client.post('/api/auth/email',content=b'{',headers=headers).status_code == 400

def test_unexpected_error_logged_but_not_returned(client,caplog):
    def fail():raise RuntimeError('private-server-detail')
    client.backend.begin_google=fail
    with caplog.at_level(logging.ERROR):
        r=post(client,'/api/auth/google/start')
    assert r.status_code == 500 and 'private-server-detail' not in r.text
    assert 'private-server-detail' in caplog.text

def test_provider_failure_remains_friendly(client):
    def fail():raise AuthFailure('Google is unavailable.',502)
    client.backend.begin_google=fail
    assert post(client,'/api/auth/google/start').status_code == 502

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


def google_complete(client, query='code=google-code&state=provider-state'):
    return post(client, '/api/auth/google/complete', {'query': query})


def test_google_signup_and_inert_callback(client):
    html=client.get('/signup').text
    assert 'Continue with Google' in html and 'id="email"' not in html
    assert 'Send me a sign-in link' not in html
    html=client.get('/auth/google/finish?code=secret-code&state=secret-state').text
    assert 'secret-code' not in html and 'secret-state' not in html
    assert not client.backend.google_calls and not client.cookies.get(SESSION)
    assert client.get('/api/health').json()['google_signin_configured'] is True


def test_google_start_requires_same_origin_csrf_and_sets_short_httponly_proof(client):
    assert client.post('/api/auth/google/start', json={}).status_code == 403
    assert post(client,'/api/auth/google/start',headers={'Origin':'https://evil.example'}).status_code == 403
    assert post(client,'/api/auth/google/start',headers={'X-CSRF-Token':'wrong'}).status_code == 403
    r=post(client,'/api/auth/google/start')
    assert r.json()['url'].startswith('https://accounts.google.com/')
    cookie=r.headers['set-cookie']
    assert OAUTH+'=' in cookie and 'Max-Age=600' in cookie and 'HttpOnly' in cookie and 'Secure' in cookie and 'SameSite=lax' in cookie


def test_google_completes_into_existing_account_and_rejects_replay(client):
    post(client,'/api/auth/google/start')
    r=google_complete(client)
    assert r.status_code == 200 and r.json()['next']=='/app'
    assert client.cookies.get(SESSION)=='verified-session' and not client.cookies.get(OAUTH)
    assert client.get('/api/me').json()['email']=='member@example.com'
    assert client.backend.google_calls == [(ORIGIN+'/auth/google/finish?code=google-code&state=provider-state', 'p'*43)]
    assert google_complete(client).status_code==401
    post(client,'/api/auth/google/start')
    assert google_complete(client).status_code==401


def test_google_preserves_device_approval_destination(client):
    client.cookies.set('__Host-wp_cli_pending','device-intent')
    post(client,'/api/auth/google/start')
    assert google_complete(client).json()['next']=='/cli'


@pytest.mark.parametrize('query,status',[
    ('code=google-code&state=wrong',401),('code=wrong&state=provider-state',401),
    ('code=google-code',400),('code=google-code&state=',400),
    ('code=google-code&state=provider-state&state=other',400),
    ('error=access_denied&error_description=secret-detail',400),
    ('code='+('x'*12000)+'&state=a',400),('',400),
])
def test_google_invalid_callback_clears_attempt_without_session(client,query,status):
    post(client,'/api/auth/google/start')
    r=google_complete(client,query)
    assert r.status_code==status and not client.cookies.get(SESSION) and not client.cookies.get(OAUTH)
    assert 'secret-detail' not in r.text


def test_google_completion_requires_origin_csrf_and_same_browser(client):
    assert google_complete(client).status_code==401
    post(client,'/api/auth/google/start')
    assert post(client,'/api/auth/google/complete',{'query':'code=google-code&state=provider-state'},headers={'Origin':'https://evil.example'}).status_code==403
    assert not client.backend.google_calls
    assert google_complete(client).status_code==200


def test_google_ignores_submitted_redirects_and_uses_fixed_callback(client):
    post(client,'/api/auth/google/start')
    assert google_complete(client,'code=google-code&state=provider-state&next=https://evil.example&providerId=evil&requestUri=https://evil.example').json()['next']=='/app'
    assert client.backend.google_calls[0][0]==ORIGIN+'/auth/google/finish?code=google-code&state=provider-state'


def test_google_disabled_fails_closed():
    with TestClient(create_app(Backend(),ORIGIN,google_enabled=False),base_url=ORIGIN) as c:
        assert 'being configured' in c.get('/signup').text
        assert post(c,'/api/auth/google/start').status_code==503
        assert not c.get('/api/health').json()['google_signin_configured']


def test_google_provider_request_and_verified_uid(monkeypatch):
    from firebase_admin import auth
    from hosting.app.auth import FirebaseBackend
    import time
    backend=FirebaseBackend.__new__(FirebaseBackend);backend.app=object();backend.origin=ORIGIN
    calls=[]
    def provider(action,data):
        calls.append((action,data))
        if action=='createAuthUri':
            return {'authUri':'https://accounts.google.com/o/oauth2/auth?state=bound-state','sessionId':data['sessionId']}
        return {'idToken':'verified-id-token','localId':'existing-uid'}
    backend._request=provider
    claims={'uid':'existing-uid','email':'member@example.com','email_verified':True,'auth_time':time.time(),'firebase':{'sign_in_provider':'google.com'}}
    monkeypatch.setattr(auth,'verify_id_token',lambda token,**kw:claims)
    monkeypatch.setattr(auth,'create_session_cookie',lambda token,**kw:'same-uid-session')
    url,proof=backend.begin_google()
    assert len(proof)==43 and calls[0][1]['authFlowType']=='CODE_FLOW'
    assert calls[0][1]['continueUri']==ORIGIN+'/auth/google/finish'
    assert 'oauthScope' not in calls[0][1]  # Provider's default identity scopes only.
    assert backend.complete_google(ORIGIN+'/auth/google/finish?code=a&state=b',proof)=='same-uid-session'
    assert calls[1][1]['sessionId']==proof and calls[1][1]['returnRefreshToken'] is False
    # No UID remapping or lookup by entered email is involved.
    for change in ({'email_verified':False},{'auth_time':time.time()-301},{'firebase':{'sign_in_provider':'password'}},{'uid':''}):
        old=claims.copy();claims.update(change)
        with pytest.raises(AuthFailure):backend.complete_google(ORIGIN+'/auth/google/finish?code=a&state=b',proof)
        claims.clear();claims.update(old)
    backend._request=lambda *a:{'needConfirmation':True,'idToken':'must-not-use'}
    with pytest.raises(AuthFailure) as e:backend.complete_google('callback',proof)
    assert e.value.status==409


def test_google_provider_cannot_supply_arbitrary_redirect():
    from hosting.app.auth import FirebaseBackend
    backend=FirebaseBackend.__new__(FirebaseBackend);backend.origin=ORIGIN
    for url in ['https://evil.example/','http://accounts.google.com/','https://accounts.google.com@evil.example/']:
        backend._request=lambda action,data:{'authUri':url,'sessionId':data['sessionId']}
        with pytest.raises(AuthFailure):backend.begin_google()
