"""Local login and resumable, verified office handoff to the hosted service."""
import base64
import json
import os
from pathlib import Path
import secrets
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
import webbrowser
from officekit.migration import canonical, snapshot, validate_manifest
from officekit.render_landing import hosted_origin


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Authentication never follows an unexpected redirect to another origin.
        return None


def config_path():
    return Path(os.environ.get('WORKER_PLACEMENT_CONFIG_DIR', Path.home()/'.config/worker-placement'))/'login.json'

def save_private(path,value):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    if path.is_symlink():raise ValueError('Refusing a symlink for local credentials.')
    temp=path.with_name('.'+path.name+'.'+secrets.token_hex(8))
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:json.dump(value,f)
    os.replace(temp,path)

def request(origin,path,payload=None,token=None):
    if urlparse(origin).scheme!='https':raise ValueError('Hosted requests require HTTPS.')
    headers={'Content-Type':'application/json'}
    if token:headers['Authorization']='Bearer '+token
    req=Request(origin+path,data=None if payload is None else canonical(payload),headers=headers)
    try:
        with build_opener(NoRedirect()).open(req,timeout=300) as r:return json.load(r)
    except HTTPError as error:
        try:detail=json.loads(error.read()).get('error','The hosted request failed.')
        except ValueError:detail='The hosted request failed.'
        if error.code==401:detail='Your login expired. Run ./wp login and try again.'
        raise ValueError(str(detail)) from None
    except (URLError,TimeoutError):raise ValueError('The hosted service could not be reached. Retry when your connection returns.') from None


def login(origin=None,timeout=900):
    origin=origin or hosted_origin()
    proof=secrets.token_urlsafe(48)
    pending=request(origin,'/api/cli/start',{'proof':proof})
    print('Open '+pending['url']+'\nConfirm this device code: '+pending['code'],flush=True)
    webbrowser.open(pending['url'])
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        result=request(origin,'/api/cli/poll',{'device':pending['device'],'proof':proof})
        if result.get('status')=='approved':
            save_private(config_path(),{'origin':origin,'token':result['token'],'email':result['email'],'expires_at':result['expires_at']})
            print('Signed in as '+result['email']+'. Your office has not been uploaded.')
            return 0
        time.sleep(3)
    raise ValueError('Login timed out. Run ./wp login again.')


def credentials():
    p=config_path()
    if not p.exists():raise ValueError('Run ./wp login before migrating your office.')
    value=json.loads(p.read_text())
    if value.get('origin')!=hosted_origin():raise ValueError('The hosted destination changed. Run ./wp login again.')
    if value.get('expires_at',0)<=time.time():raise ValueError('Your login expired. Run ./wp login again.')
    return value


def migrate(folder,replace_revision=None,open_browser=True):
    auth=credentials();origin=auth['origin'];token=auth['token']
    who=request(origin,'/api/me',token=token)
    print('Preparing your saved office and retained research for '+who['email']+' at '+origin+'…',flush=True)
    manifest,chunks=snapshot(folder);sid=validate_manifest(manifest)
    print(str(len(manifest['files']))+' documents; '+str(sum(f['size'] for f in manifest['files']))+' bytes. Local copy is retained.',flush=True)
    state=request(origin,'/api/migrations',{'manifest':manifest},token)
    for i,h in enumerate(state.get('missing',[]),1):
        print('Transferring '+str(i)+'/'+str(len(state['missing']))+'…',flush=True)
        request(origin,'/api/migrations/'+sid+'/chunks',{'sha256':h,'data':base64.b64encode(chunks[h]).decode()},token)
    print('Checking document integrity and activating…',flush=True)
    receipt=request(origin,'/api/migrations/'+sid+'/activate',{'replace_revision':replace_revision},token)
    if receipt.get('digest')!=sid or receipt.get('office_id')!=manifest['office_id'] or receipt.get('status')!='active':
        raise ValueError('The hosted receipt does not match this office. No local completion was recorded.')
    save_private(Path(folder)/'.hosted-receipt.json',receipt)
    print('Hosted office ready: '+origin+receipt['path']+'\nThe local office remains available. Later local edits are not synced automatically.')
    if open_browser:webbrowser.open(origin+receipt['path'])
    return 0
