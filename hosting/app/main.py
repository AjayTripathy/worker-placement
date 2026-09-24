"""Hosted accounts, private office snapshots and shared research; no local server."""
import json
import logging
import os
import re
import secrets
from urllib.parse import urlparse, parse_qs, urlencode

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.concurrency import run_in_threadpool

from officekit.render_landing import asset, render_landing, render_signup, render_local_guide, render_privacy
from .auth import AuthFailure, FirebaseBackend, RateLimit

LOGGER = logging.getLogger(__name__)
SESSION = '__Host-wp_session'
CSRF = '__Host-wp_csrf'
OAUTH = '__Host-wp_google'
CSP = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'self'"


def create_app(backend=None, origin=None, store=None, research=None, google_enabled=None, queue=None, exchange=None):
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    if google_enabled is None:
        google_enabled = backend is not None or os.environ.get('GOOGLE_SIGNIN_ENABLED') == 'true'
    origin = (origin if origin is not None else os.environ.get('PUBLIC_ORIGIN', '')).rstrip('/')
    if origin:
        parsed = urlparse(origin)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
            raise ValueError('PUBLIC_ORIGIN must be an HTTPS origin')
    project, api_key = os.environ.get('GOOGLE_CLOUD_PROJECT'), os.environ.get('FIREBASE_API_KEY')
    if backend is None and origin and project and api_key:
        backend = FirebaseBackend(project, api_key, origin)
    limiter = RateLimit()
    from .store import CloudStore
    from .offices import Offices
    from .research import Research
    from . import views
    if store is None and os.environ.get('OFFICE_BUCKET') and os.environ.get('OFFICE_KMS_KEY'):
        store = CloudStore(os.environ['OFFICE_BUCKET'], os.environ['OFFICE_KMS_KEY'])
    if research is None and os.environ.get('RESEARCH_BUCKET') and os.environ.get('RESEARCH_VERSION'):
        research = Research(os.environ['RESEARCH_BUCKET'], os.environ['RESEARCH_VERSION'])
    offices = Offices(store)
    offices.research_library = research
    from .exchange import configured_exchange
    app.state.research_exchange = exchange if exchange is not None else configured_exchange(store)
    offices.research_exchange = app.state.research_exchange
    from .jobs import CloudQueue, Jobs
    if queue is None and os.environ.get("OFFICE_TASK_QUEUE"):
        queue = CloudQueue(origin)
    jobs = Jobs(offices, queue)
    app.state.jobs = jobs

    @app.middleware('http')
    async def headers(request, call_next):
        try:
            response = await call_next(request)
        except Exception:
            LOGGER.exception('Unexpected hosted request failure on %s', request.url.path)
            response = JSONResponse({'error': 'Something went wrong. Please try again.'}, status_code=500)
        response.headers.setdefault('Content-Security-Policy', CSP)
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'no-referrer')
        response.headers.update({'Cache-Control': 'no-store',
                                 'X-Content-Type-Options': 'nosniff',
                                 'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'})
        if origin:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000'
        return response

    @app.exception_handler(AuthFailure)
    async def auth_error(request, error):
        if request.url.path.startswith('/app/offices/') and 'text/html' in request.headers.get('accept', ''):
            from html import escape
            from officekit.serve import STYLE
            html = '<!doctype html><html><head><title>Office needs attention</title><style>' + STYLE + '</style></head><body><main class="wrap"><h1>Request not completed</h1><p role="alert">' + escape(str(error)) + '</p><a class="btn" target="_top" href="/app">Return to your account</a></main></body></html>'
            return HTMLResponse(html, status_code=error.status, headers={
                'Content-Security-Policy': "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'self'; base-uri 'none'; form-action 'self'",
                'X-Frame-Options': 'SAMEORIGIN'})
        return JSONResponse({'error': str(error)}, status_code=error.status)

    def csrf_page(html, request):
        response = HTMLResponse(html)
        if not re.fullmatch(r'[A-Za-z0-9_-]{43}', request.cookies.get(CSRF, '')):
            response.set_cookie(CSRF, secrets.token_urlsafe(32), secure=True, httponly=False, samesite='lax', path='/')
        return response

    async def body(request, limit=4096, require_browser=True):
        if not backend or not origin:
            raise AuthFailure('Sign-in is being configured. Please return shortly.', 503)
        if require_browser:
            if request.headers.get('origin') != origin:
                raise AuthFailure('Reload this page before trying again.', 403)
            cookie, header = request.cookies.get(CSRF, ''), request.headers.get('x-csrf-token', '')
            if not re.fullmatch(r'[A-Za-z0-9_-]{43}', cookie) or not secrets.compare_digest(cookie, header):
                raise AuthFailure('Reload this page before trying again.', 403)
        if request.headers.get('content-type', '').split(';', 1)[0] != 'application/json':
            raise AuthFailure('Submit this form from the sign-in page.', 400)
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > limit:
                raise AuthFailure('The request is too large.', 413)
        try:
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError()
        except (ValueError, UnicodeError):
            raise AuthFailure('The request could not be read. Reload and try again.', 400) from None
        return value

    def email_from(data):
        email = data.get('email')
        if not isinstance(email, str) or len(email) > 254 or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email.strip()):
            raise AuthFailure('Enter a valid email address.')
        return email.strip()

    async def member(request):
        authorization = request.headers.get('authorization', '')
        cookie = authorization[7:] if authorization.startswith('Bearer ') else request.cookies.get(SESSION)
        if not backend or not cookie:
            raise AuthFailure('Sign in to continue.', 401)
        return await run_in_threadpool(backend.verify, cookie)

    @app.get('/')
    @app.get('/welcome')
    async def home():
        return HTMLResponse(render_landing())

    @app.get('/healthz')
    @app.get('/api/health')
    async def health():
        from pathlib import Path
        manifest = Path(__file__).resolve().parents[2] / 'release-manifest.json'
        release = json.loads(manifest.read_text(encoding='utf-8')) if manifest.is_file() else {}
        return {'status': 'ok', 'google_signin_configured': backend is not None and google_enabled, 'office_migration_configured': store is not None, 'research_configured': research is not None, 'office_jobs_configured': queue is not None,
                'source_sha256': release.get('source_sha256')}

    @app.get('/signup')
    async def signup(request: Request):
        return csrf_page(render_signup(available=backend is not None and google_enabled), request)

    @app.get('/auth/google/finish')
    async def google_finish(request: Request):
        # Never reflect provider query parameters. JS clears the address bar and
        # completes via same-origin CSRF-protected POST, using the HttpOnly proof.
        return csrf_page(render_signup(google_finish=True, available=backend is not None and google_enabled), request)

    @app.get('/auth/finish')
    async def finish(request: Request):
        # GET is deliberately inert: no code exchange, cookie session, or upload.
        return csrf_page(render_signup(finish=True, available=backend is not None), request)

    @app.get('/guides/local')
    async def guide():
        return HTMLResponse(render_local_guide())

    @app.get('/privacy')
    async def privacy():
        return HTMLResponse(render_privacy())

    @app.get('/public/{name}')
    async def public_asset(name: str):
        found = asset('/public/' + name)
        return Response(found[0], media_type=found[1]) if found else Response(status_code=404)

    @app.post('/api/auth/email')
    async def send_email(request: Request):
        await body(request)
        raise AuthFailure('Email links have been replaced by Google sign-in. Reload the sign-in page to continue.', 410)

    @app.post('/api/auth/google/start')
    async def google_start(request: Request):
        await body(request)
        if not google_enabled:
            raise AuthFailure('Google sign-in is being configured. Please return shortly.', 503)
        limiter.claim(request.cookies[CSRF], 'google_start')
        url, proof = await run_in_threadpool(backend.begin_google)
        response = JSONResponse({'url': url})
        response.set_cookie(OAUTH, proof, max_age=600, secure=True, httponly=True, samesite='lax', path='/')
        return response

    def session_response(cookie, request):
        response = JSONResponse({'next': '/cli' if request.cookies.get('__Host-wp_cli_pending') else '/app'})
        response.set_cookie(SESSION, cookie, max_age=5*24*3600, secure=True, httponly=True, samesite='lax', path='/')
        return response

    @app.post('/api/auth/google/complete')
    async def google_complete(request: Request):
        data = await body(request, limit=16384)
        if not google_enabled:
            raise AuthFailure('Google sign-in is being configured. Please return shortly.', 503)
        proof = request.cookies.get(OAUTH, '')
        try:
            if not re.fullmatch(r'[A-Za-z0-9_-]{43}', proof):
                raise AuthFailure('Start Google sign-in again in this browser. The attempt is missing or expired.', 401)
            limiter.claim(proof, 'google_complete')
            query = data.get('query')
            if not isinstance(query, str) or len(query) > 12000:
                raise AuthFailure('Google did not return a valid sign-in response. Please start again.')
            try:
                values = parse_qs(query, keep_blank_values=True, max_num_fields=20)
            except ValueError:
                raise AuthFailure('Google did not return a valid sign-in response. Please start again.') from None
            if 'error' in values:
                raise AuthFailure('Google sign-in was canceled or declined. You can try again.')
            for key in ('code', 'state'):
                if len(values.get(key, [])) != 1 or not 1 <= len(values[key][0]) <= 8192:
                    raise AuthFailure('Google did not return a valid sign-in response. Please start again.')
            # Fixed origin/path and only the two protocol fields: no user-supplied
            # request URL, redirect destination, provider ID or identity claim.
            callback = origin + '/auth/google/finish?' + urlencode({k: values[k][0] for k in ('code', 'state')})
            cookie = await run_in_threadpool(backend.complete_google, callback, proof)
            response = session_response(cookie, request)
        except AuthFailure as error:
            response = JSONResponse({'error': str(error)}, status_code=error.status)
        response.delete_cookie(OAUTH, path='/', secure=True, httponly=True, samesite='lax')
        return response

    @app.post('/api/auth/complete')
    async def complete(request: Request):
        data = await body(request)
        email = email_from(data)
        code = data.get('code')
        if not isinstance(code, str) or not re.fullmatch(r'[A-Za-z0-9_-]{10,1024}', code):
            raise AuthFailure('This old sign-in link is invalid. Continue with Google from the sign-in page.')
        limiter.claim(email, 'complete')
        cookie = await run_in_threadpool(backend.complete, email, code)
        return session_response(cookie, request)

    @app.post('/api/auth/logout')
    async def logout(request: Request):
        await body(request)
        response = JSONResponse({'status': 'signed_out'})
        response.delete_cookie(SESSION, path='/', secure=True, httponly=True, samesite='lax')
        response.delete_cookie(CSRF, path='/', secure=True, samesite='lax')
        response.delete_cookie(OAUTH, path='/', secure=True, httponly=True, samesite='lax')
        return response

    @app.get('/app')
    async def account(request: Request):
        try:
            claims = await member(request)
        except AuthFailure as error:
            if error.status != 401:
                raise
            response = RedirectResponse('/signup', status_code=303)
            response.delete_cookie(SESSION, path='/', secure=True, httponly=True, samesite='lax')
            return response
        rows = await run_in_threadpool(offices.listing, claims['uid']) if store else []
        return csrf_page(views.account(claims['email'], rows), request)

    @app.get('/api/me')
    async def me(request: Request):
        claims = await member(request)
        return {'email': claims['email'], 'email_verified': True, 'office_migration': 'available' if store else 'not_available'}

    from .routes import install
    install(app, offices, research, origin, member, body, csrf_page, limiter, jobs)

    @app.get('/install.sh')
    async def installer():
        from officekit.render_landing import PUBLIC
        return Response((PUBLIC/'install.sh').read_bytes(), media_type='text/plain')

    return app
