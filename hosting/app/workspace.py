"""Authenticated transport for the shared office application, not a second UI.

Each request works on a private temporary copy. Successful mutations publish an
immutable revision with a compare-and-swap; no user data lives in process globals.
The local HTTP listener, machine discovery and background workers are not run.
"""
import base64
from email.message import Message
from html import escape
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import secrets
import tempfile

from officekit.migration import (CHUNK, MAX_TOTAL, canonical, digest, inspect_document,
                                 snapshot, validate_documents)
from officekit.runtime import hosted_office
from .auth import AuthFailure
from .offices import stamp
from .store import Conflict

POSTS = {'/assets', '/goals', '/goals/add', '/goals/remove', '/goals/mortgage',
         '/goal/params', '/growth', '/harvest', '/holdings', '/strategy/goal-unadopt',
         '/commitments/add', '/commitments/update', '/inflows/preview', '/inflows/apply',
         '/strategy/adopt', '/strategy/new', '/strategy/goal-adopt', '/strategy/propose',
         '/strategy/proposal/retry', '/strategy/proposal/revise', '/strategy/proposal/decide',
         '/api-errors/dismiss', '/import/files', '/import/remove', '/adapter/import', '/chat', '/court', '/docket', '/signals/run', '/commitments/preview'}
from officekit.research_routes import POSTS as RESEARCH_POSTS
POSTS |= RESEARCH_POSTS
GETS = {'/', '/state', '/api-errors', '/strategy/proposals/status', '/research'}
ONBOARD_POSTS = {'/draft', '/onboard', '/onboard/confirm', '/import/files', '/import/remove',
                '/adapter/import', '/chat', '/api-errors/dismiss'}
EXTRAS = {'api_errors.json', 'commitment_history.jsonl'}
EXTRA_DIRS = {'inflow_previews', 'commitment_previews'}
DISABLED = {'/key': 'Connect your AI key in Office settings.',
            '/import/desk-board': 'Use the local desktop app for desk imports; office sync brings the results online.'}



def extra_path(name):
    return name in EXTRAS or bool(re.fullmatch(
        r'(?:inflow_previews|commitment_previews)/[a-f0-9-]{36}\.json', name))


def materialize(folder, record):
    if record.get('onboarding'):
        from .onboarding import validate
        docs = validate(record)
    else:
        docs = {name: base64.b64decode(raw, validate=True) for name, raw in record['documents'].items()}
        validate_documents(record['manifest'], docs)
    for name, raw in record.get('workspace', {}).items():
        if not extra_path(name):
            raise ValueError('Unsupported workspace document')
        data = base64.b64decode(raw, validate=True)
        inspect_document(name, data)
        docs[name] = data
    if sum(map(len, docs.values())) > MAX_TOTAL:
        raise ValueError('Office exceeds the workspace size limit')
    for name, data in docs.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def capture(folder, oid=None):
    if not (folder / 'balance_sheet.json').exists():
        from .onboarding import capture as capture_draft
        record = capture_draft(folder, oid)
    else:
        manifest, chunks = snapshot(folder)
        if oid and manifest['office_id'] != oid:
            raise ValueError('Office identity cannot change during onboarding')
        documents = {f['path']: base64.b64encode(b''.join(chunks[h] for h in f['chunks'])).decode()
                     for f in manifest['files']}
        record = {'manifest': manifest, 'documents': documents}
    extra = {}
    for path in folder.rglob('*'):
        name = path.relative_to(folder).as_posix()
        if path.is_file() and extra_path(name):
            data = path.read_bytes()
            inspect_document(name, data)
            extra[name] = base64.b64encode(data).decode()
    if sum(len(base64.b64decode(b)) for b in record['documents'].values()) + sum(len(base64.b64decode(b)) for b in extra.values()) > MAX_TOTAL:
        raise ValueError('Office exceeds the workspace size limit')
    return dict(record, workspace=extra)


def publish(offices, uid, receipt, record, job_id=None):
    prefix = offices.prefix(uid, receipt['office_id'])
    current, generation = offices.db().get(prefix + 'active')
    if not current or current['digest'] != receipt['digest']:
        raise AuthFailure('The office changed in another tab. Reload and review before saving.', 409)
    from .jobs import writable
    writable(current, job_id)
    revision = digest(canonical(record))
    try:
        offices.db().put(prefix + 'revisions/' + revision, record)
    except Conflict:
        pass
    answers = json.loads(base64.b64decode(record['documents']['answers.json']))
    balance = json.loads(base64.b64decode(record['documents'].get('balance_sheet.json', 'e30=')))
    updated = dict(current, digest=revision, activated_at=stamp(), as_of=balance.get('as_of', ''),
                   status='onboarding' if record.get('onboarding') else 'active',
                   name=str(answers.get('owner') or 'Your office')[:180],
                   documents=len(record['documents']), source='hosted')
    try:
        offices.db().put(prefix + 'active', updated, generation)
    except Conflict:
        raise AuthFailure('The office changed while you were saving. Reload and review before trying again.', 409) from None
    return updated


def local_request(folder, method, path, raw, content_type):
    from officekit.serve import make_handler
    handler = make_handler(folder)

    class InProcess(handler):
        def __init__(self):
            self.path, self.command = path, method
            self.headers = Message()
            self.headers['Content-Type'] = content_type
            self.headers['Content-Length'] = str(len(raw))
            self.rfile, self.wfile = io.BytesIO(raw), io.BytesIO()
            self.response_headers = {}
            self.status = 200

        def send_response(self, code, message=None):
            self.status = code

        def send_header(self, name, value):
            self.response_headers[name] = str(value)

        def end_headers(self):
            pass

    request = InProcess()
    (request.do_POST if method == 'POST' else request.do_GET)()
    return request.status, request.response_headers, request.wfile.getvalue()


def dispatch(offices, uid, oid, method, path, raw=b'', content_type='', expected=None, job_id=None):
    receipt, record = offices.read(uid, oid)
    if method == 'POST':
        from .jobs import writable
        writable(receipt, job_id)
    if method == 'POST' and path != '/api-errors/dismiss' and expected != receipt['digest']:
        raise AuthFailure('The office changed since this page was opened. Reload and review before saving.', 409)
    if method == 'GET' and path == '/state':
        return 200, {'Content-Type': 'application/json'}, json.dumps({'v': receipt['digest']}).encode(), receipt
    allowed_posts = ONBOARD_POSTS if record.get('onboarding') else POSTS
    if method == 'POST' and path not in allowed_posts:
        raise AuthFailure(DISABLED.get(path, 'This action is not available in the hosted office yet.'), 400)
    if method == 'GET' and path not in GETS and not re.fullmatch(r'/pages/[A-Za-z0-9_.-]+\.html', path):
        raise AuthFailure('Page not found.', 404)
    with tempfile.TemporaryDirectory(prefix='wp-office-') as directory:
        folder = Path(directory)
        materialize(folder, record)
        from .credentials import Credentials
        credentials, _ = Credentials(offices).read(uid, oid)
        pending = []
        def checkpoint():
            nonlocal receipt, record
            updated = capture(folder, oid)
            receipt = publish(offices, uid, receipt, updated, job_id=job_id)
            record = updated
        with hosted_office(folder, credentials, enqueue=pending.append if job_id else None, checkpoint=checkpoint if job_id else None):
            from officekit.serve import render_saved_office
            if method == 'GET' and (path == '/' or path.startswith('/pages/')):
                if not record.get('onboarding'):
                    render_saved_office(folder)
                elif path.startswith('/pages/'):
                    from officekit.serve import write_imports_page
                    write_imports_page(folder)
            status, headers, data = local_request(folder, method, path, raw, content_type)
            for pid in pending:
                checkpoint()
                from officekit.strategy_proposals import run
                run(folder, pid)
            if method == 'POST' and (status < 400 or job_id):
                updated = capture(folder, oid)
                # Rendering and exploratory calculations need no new revision.
                if updated['documents'] != record['documents'] or updated['workspace'] != record.get('workspace', {}):
                    receipt = publish(offices, uid, receipt, updated, job_id=job_id)
        if status >= 400 and 'text/plain' in headers.get('Content-Type', ''):
            from officekit.serve import STYLE
            data = ('<!doctype html><html lang="en"><head><title>Request needs attention</title><style>' + STYLE + '</style></head><body><main class="wrap"><h1>Changes were not saved</h1><p role="alert">' + escape(data.decode()) + '</p><button type="button" onclick="history.back()">Back to your edits</button></main></body></html>').encode()
            headers['Content-Type'] = 'text/html; charset=utf-8'
        headers['X-Office-Revision'] = receipt['digest']
        return status, headers, data, receipt


CLIENT = r'''<script nonce="NONCE">
window.officeBase=BASE;
(function(){
 const base=window.officeBase, csrf=__WP_CSRF__;
 let revision=REVISION;
 const resolve=value=>typeof value==='string'&&value.startsWith('/')&&!value.startsWith('//')&&value!=='/app'&&!value.startsWith('/app/')?base+value:value;
 const original=window.fetch.bind(window);
 let writes=Promise.resolve();
 window.officeRequestsIdle=()=>writes;
 window.fetch=function(input,options){
   const mutating=(options?.method||(input instanceof Request?input.method:'GET')).toUpperCase()==='POST';
   const execute=()=>{
   const url=typeof input==='string'?resolve(input):input;
   const target=new URL(typeof url==='string'?url:url.url,location.href);
   if(target.origin===location.origin&&target.pathname.startsWith(base+'/')){
     options=Object.assign({},options);options.headers=new Headers(options.headers|| (input instanceof Request?input.headers:{}));
     options.headers.set('X-CSRF-Token',csrf);options.headers.set('X-Office-Revision',revision);
   }
   return original(url,options).then(async response=>{
     if(mutating&&response.ok&&target.origin===location.origin&&target.pathname.startsWith(base+'/')&&target.pathname!==base+'/api-errors/dismiss')revision=response.headers.get('X-Office-Revision')||revision;
     if(response.status!==202||!response.headers.get('content-type')?.includes('application/json'))return response;
     const queued=await response.clone().json();if(!queued.job)return response;
     const job=new URL(queued.job,location.href);if(job.origin!==location.origin||!job.pathname.startsWith(base+'/jobs/'))throw new Error('Invalid job destination');
     for(;;){await new Promise(r=>setTimeout(r,2000));const r=await original(job.pathname+'/status');const s=await r.json();if(!r.ok||s.error)throw new Error(s.error||'Background work failed');if(s.status==='complete'){const result=await original(job.pathname+'/result');if(result.ok)revision=result.headers.get('X-Office-Revision')||revision;return result;}}
   });
   };
   if(mutating){
     const result=writes.then(execute);writes=result.then(()=>{},()=>{});return result;
   }
   return execute();
 };
 document.addEventListener('click',function(event){const a=event.target.closest('a');if(a){const value=a.getAttribute('href');if(value)a.setAttribute('href',resolve(value));}},true);
 document.addEventListener('submit',function(event){
   const form=event.target;form.action=resolve(form.getAttribute('action')||location.pathname);
   if(new URL(form.action).pathname.startsWith(base+'/')){
     for(const [name,value] of [['_csrf',csrf],['_office_revision',revision]]){
       let input=form.querySelector('input[name="'+name+'"]');if(!input){input=document.createElement('input');input.type='hidden';input.name=name;form.appendChild(input);}input.value=value;
     }
   }
 },true);
})();
</script>'''


class Presentation(HTMLParser):
    """Mount shared HTML under an office; nonce scripts and bind inline handlers.

    Only server renderers enter this adapter. Migrated HTML is never served.
    Event handlers become nonce-bearing scripts, avoiding unsafe-inline JS.
    """
    def __init__(self, base, revision, csrf, nonce):
        super().__init__(convert_charrefs=False)
        self.base, self.revision, self.csrf, self.nonce = base, revision, csrf, nonce
        self.output, self.events, self.forms = [], [], []

    def url(self, value):
        if value.startswith('/') and not value.startswith('//') and value != '/app' and not value.startswith('/app/'):
            return self.base + value
        return value

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'script':
            values['nonce'] = self.nonce
        events = [(k[2:], v) for k, v in attrs if k.startswith('on') and v]
        if events:
            key = 'e' + str(len(self.events))
            values['data-wp-event'] = key
            self.events.extend((key, kind, code) for kind, code in events)
            for kind, _ in events:
                values.pop('on' + kind, None)
        if tag == 'form':
            reason = DISABLED.get(values.get('action'))
            self.forms.append(reason)
        for key in ('href', 'src', 'action', 'formaction'):
            if values.get(key):
                values[key] = self.url(values[key])
        self.output.append('<' + tag + ''.join(' ' + k + ('="' + escape(v, quote=True) + '"' if v is not None else '') for k, v in values.items()) + '>')
        if tag == 'head':
            client = CLIENT.replace('NONCE', self.nonce).replace('BASE', json.dumps(self.base)).replace('REVISION', json.dumps(self.revision)).replace('__WP_CSRF__', json.dumps(self.csrf))
            self.output.append(client)
        if tag == 'form':
            self.output.append('<input type="hidden" name="_csrf" value="' + escape(self.csrf) + '"><input type="hidden" name="_office_revision" value="' + self.revision + '">')
            if self.forms[-1]:
                self.output.append('<p role="note">' + escape(self.forms[-1]) + '</p><fieldset disabled style="border:0;margin:0;padding:0">')

    def handle_endtag(self, tag):
        if tag == 'form' and self.forms and self.forms.pop():
            self.output.append('</fieldset>')
        if tag == 'body' and self.events:
            code = ''.join('document.querySelector(\'[data-wp-event="' + key + '"]\').addEventListener(' + json.dumps(kind) + ',function(event){const result=(function(event){' + js + '\n}).call(this,event);if(result===false)event.preventDefault();});' for key, kind, js in self.events)
            self.output.append('<script nonce="' + self.nonce + '">' + code + '</script>')
        self.output.append('</' + tag + '>')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.handle_endtag(tag)

    def handle_data(self, data): self.output.append(data)
    def handle_entityref(self, name): self.output.append('&' + name + ';')
    def handle_charref(self, name): self.output.append('&#' + name + ';')
    def handle_decl(self, decl): self.output.append('<!' + decl + '>')
    def handle_comment(self, data): self.output.append('<!--' + data + '-->')


def present(html, receipt, csrf):
    base = receipt['path']
    html = html.replace('<a class="host-office" href="/settings" target="_blank" rel="noopener">Office settings</a>',
                        '<a class="host-office" href="' + base + '/settings">Office settings</a>')
    html = html.replace('<a class="reb" href="/reset">start over</a>', '<a class="reb" href="/app" target="_top">Account</a>')
    nonce = secrets.token_urlsafe(24)
    parser = Presentation(base, receipt['digest'], csrf, nonce)
    parser.feed(html)
    parser.close()
    policy = ("default-src 'self'; script-src 'self' 'nonce-" + nonce + "'; style-src 'self' 'unsafe-inline'; "
              "img-src 'self' data:; connect-src 'self'; frame-src 'self'; frame-ancestors 'self'; "
              "base-uri 'none'; object-src 'none'; form-action 'self'")
    return ''.join(parser.output), policy


def settings(receipt, connections=None):
    from officekit.render_settings import render_settings
    html = render_settings(hosted=True, connections=connections)
    if receipt.get('job') or receipt.get('last_job'):
        from .jobs import progress_page
        link = '<p class="panel"><a href="/jobs/' + (receipt.get('job', {}).get('id') or receipt['last_job']) + '">View latest background work →</a></p>'
        html = html.replace('</main>', link + '</main>')
    return html
