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


def install(app, offices, research, origin, member, body, csrf_page, limiter):
    async def private(request):
        claims=await member(request)
        # CLI APIs use explicit bearer credentials, never ambient browser cookies.
        if not request.headers.get('authorization','').startswith('Bearer '):raise AuthFailure('Sign in from the command line first.',401)
        return claims

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

    @app.get('/app/offices/{oid}')
    async def office(oid:str,request:Request):
        try:claims=await member(request)
        except AuthFailure as e:
            if e.status==401:return RedirectResponse('/signup',303)
            raise
        receipt,record=await run_in_threadpool(offices.read,claims['uid'],oid)
        return csrf_page(views.office(receipt,record),request)

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
                for path,encoded in record['documents'].items():z.writestr(path,base64.b64decode(encoded))
                z.writestr('migration-receipt.json',json.dumps(receipt,indent=2))
            return output.getvalue()
        return Response(await run_in_threadpool(build),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="worker-placement-office.zip"'})

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
