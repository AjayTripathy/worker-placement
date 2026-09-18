"""Private hosted endpoints; tenant identity comes only from verified sessions."""
import base64
import io
import json
from pathlib import PurePosixPath
from urllib.parse import quote
import re
import zipfile
from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.concurrency import run_in_threadpool
from .auth import AuthFailure
from . import views

PENDING='__Host-wp_cli_pending'


def install(app, offices, research, origin, member, body, csrf_page, limiter, jobs):
    async def private(request):
        claims=await member(request)
        # CLI APIs use explicit bearer credentials, never ambient browser cookies.
        if not request.headers.get('authorization','').startswith('Bearer '):raise AuthFailure('Sign in from the command line first.',401)
        return claims

    @app.post('/internal/office-job')
    async def run_job(request: Request):
        if jobs.queue is None:
            raise AuthFailure('Workers are not configured.', 503)
        authorization = request.headers.get('authorization', '')
        if not authorization.startswith('Bearer '):
            raise AuthFailure('Worker authentication required.', 403)
        await run_in_threadpool(jobs.queue.verify, authorization[7:])
        data = await body(request, require_browser=False)
        if set(data) != {'uid', 'oid', 'job'} or not all(isinstance(v, str) and len(v) <= 128 for v in data.values()):
            raise AuthFailure('Invalid job request.')
        await run_in_threadpool(jobs.run, data['uid'], data['oid'], data['job'])
        return {'ok': True}

    @app.get('/api/offices/{oid}/revision')
    async def office_revision(oid: str, request: Request):
        claims = await private(request)
        receipt, _ = await run_in_threadpool(offices.db().get, offices.prefix(claims['uid'], oid) + 'active')
        if not receipt:
            raise AuthFailure('Office not found.', 404)
        return receipt

    @app.get('/api/offices/{oid}/snapshot')
    async def office_snapshot(oid: str, request: Request):
        claims = await private(request)
        receipt, record = await run_in_threadpool(offices.read, claims['uid'], oid)
        return {'receipt': receipt, 'record': record}

    @app.get('/cli')
    async def cli(request:Request):
        saved=request.cookies.get(PENDING,'').split(':',1)
        device=request.query_params.get('device',saved[0] if len(saved)==2 else '')
        code=request.query_params.get('code',saved[1] if len(saved)==2 else '')
        if not re.fullmatch('[a-f0-9-]{36}',device) or not re.fullmatch('[A-F0-9]{8}',code):raise AuthFailure('Run ./wp login to start a device connection.')
        await run_in_threadpool(offices.device,device)
        try:claims=await member(request)
        except AuthFailure as e:
            if e.status!=401:raise
            claims=None
        response=csrf_page(views.device(device,code,claims['email'] if claims else None),request)
        response.set_cookie(PENDING,device+':'+code,secure=True,httponly=True,samesite='lax',path='/',max_age=900)
        return response

    @app.post('/api/cli/start')
    async def start(request:Request):
        data=await body(request,require_browser=False)
        limiter.claim(request.client.host if request.client else 'anonymous','device')
        return await run_in_threadpool(offices.start,data.get('proof'),origin)

    @app.post('/api/cli/poll')
    async def poll(request:Request):
        data=await body(request,require_browser=False)
        limiter.claim(request.client.host if request.client else 'anonymous','poll')
        return await run_in_threadpool(offices.poll,data.get('device'),data.get('proof'))

    @app.post('/api/cli/approve')
    async def approve(request:Request):
        if request.headers.get('authorization'):raise AuthFailure('Approve the device from your signed-in browser.',403)
        data=await body(request);claims=await member(request)
        cookie=request.cookies.get('__Host-wp_session','')
        if not cookie:raise AuthFailure('Sign in in this browser before connecting a device.',401)
        result=await run_in_threadpool(offices.approve,data.get('device'),data.get('code'),claims,cookie)
        response=JSONResponse(result);response.delete_cookie(PENDING,secure=True,httponly=True,samesite='lax',path='/')
        return response

    @app.post('/api/migrations')
    async def begin(request:Request):
        claims=await private(request);data=await body(request,limit=1024*1024,require_browser=False)
        return await run_in_threadpool(offices.begin,claims['uid'],data.get('manifest'))

    @app.post('/api/migrations/{sid}/chunks')
    async def upload(sid:str,request:Request):
        claims=await private(request);data=await body(request,limit=1500000,require_browser=False)
        return await run_in_threadpool(offices.upload,claims['uid'],sid,data.get('sha256'),data.get('data'))

    @app.post('/api/migrations/{sid}/activate')
    async def activate(sid:str,request:Request):
        claims=await private(request);data=await body(request,require_browser=False)
        return await run_in_threadpool(offices.activate,claims['uid'],sid,data.get('replace_revision'))

    @app.get('/api/offices')
    async def listing(request:Request):
        claims=await member(request)
        return {'offices':await run_in_threadpool(offices.listing,claims['uid'])}

    from . import workspace
    import secrets

    def workspace_response(request, receipt, html, status=200):
        csrf = request.cookies.get('__Host-wp_csrf', '')
        if not re.fullmatch(r'[A-Za-z0-9_-]{43}', csrf):
            csrf = secrets.token_urlsafe(32)
        html, policy = workspace.present(html, receipt, csrf)
        response = HTMLResponse(html, status_code=status, headers={
            'Content-Security-Policy': policy, 'X-Frame-Options': 'SAMEORIGIN',
            'Referrer-Policy': 'same-origin'})
        response.set_cookie('__Host-wp_csrf', csrf, secure=True, httponly=False, samesite='lax', path='/')
        return response

    async def workspace_request(oid, path, request):
        try:
            claims = await member(request)
        except AuthFailure as error:
            if error.status == 401:
                return RedirectResponse('/signup', 303)
            raise
        raw, expected = b'', None
        ctype = request.headers.get('content-type', '')
        if request.method == 'POST':
            if request.headers.get('origin') != origin:
                raise AuthFailure('Reload this office before saving.', 403)
            collected = bytearray()
            async for chunk in request.stream():
                collected.extend(chunk)
                if len(collected) > 20 * 1024 * 1024:
                    raise AuthFailure('This request is too large.', 413)
            raw = bytes(collected)
            token = request.headers.get('x-csrf-token', '')
            expected = request.headers.get('x-office-revision')
            if ctype.split(';', 1)[0] in {'application/x-www-form-urlencoded', 'multipart/form-data'}:
                from officekit.formdata import parse
                from email.message import Message
                headers = Message()
                headers['Content-Type'] = ctype
                headers['Content-Length'] = str(len(raw))
                form = parse(io.BytesIO(raw), headers)
                token = form.getvalue('_csrf') or token
                expected = form.getvalue('_office_revision') or expected
            elif ctype.split(';', 1)[0] != 'application/json':
                raise AuthFailure('Submit this action from your office.', 400)
            cookie = request.cookies.get('__Host-wp_csrf', '')
            if not re.fullmatch(r'[A-Za-z0-9_-]{43}', cookie) or not isinstance(token, str) or not secrets.compare_digest(cookie, token):
                raise AuthFailure('Reload this office before saving.', 403)
        from .credentials import Credentials
        from .jobs import LONG_PATHS, progress_page
        credentials = Credentials(offices)
        if request.method == 'POST' and path == '/settings/credentials':
            if ctype.split(';', 1)[0] != 'application/x-www-form-urlencoded':
                raise AuthFailure('Use the connection settings form.')
            data = {name: form.getvalue(name) or '' for name in
                    ('provider', 'credential_revision', 'remove', 'ANTHROPIC_API_KEY',
                     'APCA_API_KEY_ID', 'APCA_API_SECRET_KEY', 'APCA_API_BASE_URL',
                     'IBKR_FLEX_TOKEN', 'IBKR_FLEX_QUERY_ID', 'OFFICEKIT_CONTACT')}
            await run_in_threadpool(credentials.update, claims['uid'], oid, data)
            return RedirectResponse('/app/offices/' + oid + '/settings', 303)
        goal_intake = (request.method == 'POST' and path == '/goals/add'
                       and ctype.split(';', 1)[0] in {'application/x-www-form-urlencoded', 'multipart/form-data'}
                       and bool((form.getvalue('nl') or '').strip()))
        if request.method == 'POST' and (path in LONG_PATHS or goal_intake):
            values, _ = await run_in_threadpool(credentials.read, claims['uid'], oid)
            # Without a key, strategy briefs still save synchronously for later.
            if (not path.startswith('/strategy/') and not goal_intake) or values.get('ANTHROPIC_API_KEY'):
                jid = await run_in_threadpool(jobs.start, claims['uid'], oid, path, raw, ctype, expected)
                receipt, _ = await run_in_threadpool(offices.read, claims['uid'], oid)
                if ctype.split(';', 1)[0] == 'application/json':
                    return JSONResponse({'job': receipt['path'] + '/jobs/' + jid}, status_code=202)
                return RedirectResponse(receipt['path'] + '/jobs/' + jid, 303)
        try:
            status, headers, data, receipt = await run_in_threadpool(
                workspace.dispatch, offices, claims['uid'], oid, request.method, path,
                raw, ctype, expected)
        except AuthFailure as error:
            if error.status not in {400, 409} or request.headers.get('accept', '').startswith('application/json'):
                raise
            from html import escape
            from officekit.serve import STYLE
            receipt, _ = await run_in_threadpool(offices.read, claims['uid'], oid)
            html = '<!doctype html><html><head><title>Review before saving</title><style>' + STYLE + '</style></head><body><main class="wrap"><h1>Changes were not saved</h1><p role="alert">' + escape(str(error)) + '</p><a class="btn" target="_top" href="' + receipt['path'] + '">Reload office</a><p>Your current saved office is unchanged.</p></main></body></html>'
            return workspace_response(request, receipt, html, error.status)
        if 'Location' in headers:
            location = headers['Location']
            if not location.startswith('/') or location.startswith('//'):
                raise AuthFailure('The destination could not be opened.', 500)
            return RedirectResponse(receipt['path'] + location, status)
        if 'text/html' in headers.get('Content-Type', ''):
            return workspace_response(request, receipt, data.decode(), status)
        return Response(data, status_code=status, headers={k: v for k, v in headers.items()
                        if k.lower() in {'content-type', 'x-office-api-error-id', 'x-office-api-error-context'}})

    @app.get('/app/offices/{oid}')
    @app.get('/app/offices/{oid}/')
    async def office(oid: str, request: Request):
        return await workspace_request(oid, '/', request)

    @app.get('/app/offices/{oid}/document')
    async def document(oid:str,request:Request):
        claims=await member(request);_,record=await run_in_threadpool(offices.read,claims['uid'],oid)
        path=request.query_params.get('path','')
        if path not in record['documents']:raise AuthFailure('Document not found.',404)
        # Always download. User content never runs on the authenticated origin.
        return Response(base64.b64decode(record['documents'][path]),media_type='application/octet-stream',headers={'Content-Disposition':"attachment; filename*=UTF-8''"+quote(PurePosixPath(path).name,safe='')})

    @app.get('/app/offices/{oid}/export')
    async def export(oid:str,request:Request):
        claims=await member(request);receipt,record=await run_in_threadpool(offices.read,claims['uid'],oid)
        def build():
            output=io.BytesIO()
            with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as z:
                for path,encoded in {**record['documents'], **record.get('workspace', {})}.items():z.writestr(path,base64.b64decode(encoded))
                z.writestr('migration-receipt.json',json.dumps(receipt,indent=2))
            return output.getvalue()
        return Response(await run_in_threadpool(build),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="worker-placement-office.zip"'})

    @app.get('/app/offices/{oid}/settings')
    async def office_settings(oid: str, request: Request):
        claims = await member(request)
        receipt, _ = await run_in_threadpool(offices.read, claims['uid'], oid)
        from .credentials import Credentials
        connections = await run_in_threadpool(Credentials(offices).status, claims['uid'], oid)
        return workspace_response(request, receipt, workspace.settings(receipt, connections))

    @app.get('/app/offices/{oid}/documents')
    async def office_documents(oid: str, request: Request):
        claims = await member(request)
        receipt, record = await run_in_threadpool(offices.read, claims['uid'], oid)
        return csrf_page(views.office(receipt, record), request)

    @app.get('/app/offices/{oid}/jobs/{jid}')
    @app.get('/app/offices/{oid}/jobs/{jid}/{action}')
    async def office_job(oid: str, jid: str, request: Request, action: str = ''):
        claims = await member(request)
        job, _ = await run_in_threadpool(jobs.read, claims['uid'], oid, jid)
        receipt, _ = await run_in_threadpool(offices.read, claims['uid'], oid)
        if action == 'status':
            return {'status': job['status'], 'error': job.get('error')}
        if action == 'result':
            if job['status'] != 'complete':
                raise AuthFailure(job.get('error') or 'Work is still running.', 409)
            result = job['response'];headers = result['headers']
            if headers.get('Location'):
                return RedirectResponse(receipt['path'] + headers['Location'], 303)
            data = base64.b64decode(result['body'])
            if 'text/html' in headers.get('Content-Type', ''):
                return workspace_response(request, receipt, data.decode(), result['status'])
            return Response(data, status_code=result['status'], media_type=headers.get('Content-Type', 'application/json'))
        if action:
            raise AuthFailure('Page not found.', 404)
        from .jobs import progress_page
        return workspace_response(request, receipt, progress_page(jid))

    @app.api_route('/app/offices/{oid}/{path:path}', methods=['GET', 'POST'])
    async def office_action(oid: str, path: str, request: Request):
        return await workspace_request(oid, '/' + path, request)

    def library():
        if research is None:raise AuthFailure('The shared research library is being prepared. Please return shortly.',503)
        return research

    @app.get('/app/research')
    async def research_index(request:Request):
        try:await member(request)
        except AuthFailure as e:
            if e.status==401:return RedirectResponse('/signup',303)
            raise
        r=library();catalog=await run_in_threadpool(r.catalog)
        area=request.query_params.get('area');query=request.query_params.get('q','')[:200]
        try:offset=max(0,min(50000,int(request.query_params.get('offset','0'))))
        except ValueError:raise AuthFailure('Invalid page offset.') from None
        entries=await run_in_threadpool(r.entries,area) if area else []
        return csrf_page(views.research_index(catalog,area,entries,query,offset),request)

    @app.get('/app/research/document')
    async def research_document(request:Request):
        await member(request);r=library();area=request.query_params.get('area','');path=request.query_params.get('path','')
        data=await run_in_threadpool(r.read,area,path)
        if PurePosixPath(path).suffix.lower() in {'.txt','.md','.json','.csv','.jsonl','.py','.sh','.sql','.yaml','.yml','.toml'} and len(data)<2*1024*1024 and request.query_params.get('download')!='1':
            from html import escape
            from urllib.parse import urlencode
            from officekit.render_landing import page
            content='<main id="main" class="subpage wide"><p class="eyebrow">SHARED RESEARCH</p><h1 class="file-title">'+escape(PurePosixPath(path).name)+'</h1><p>'+escape(path)+'</p><a href="/app/research/document?'+urlencode({'area':area,'path':path,'download':'1'})+'">Download original</a><pre class="research-text">'+escape(data.decode('utf-8','replace'))+'</pre></main>'
            return csrf_page(page('Research document',content,signed_in=True,auth_script=True),request)
        return Response(data,media_type='application/octet-stream',headers={'Content-Disposition':"attachment; filename*=UTF-8''"+quote(PurePosixPath(path).name,safe='')})
