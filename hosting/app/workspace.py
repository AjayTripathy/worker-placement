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
         '/api-errors/dismiss'}
GETS = {'/', '/state', '/api-errors', '/strategy/proposals/status'}
EXTRAS = {'api_errors.json', 'commitment_history.jsonl'}
EXTRA_DIRS = {'inflow_previews', 'commitment_previews'}
DISABLED = {'/key': 'AI agent keys can be connected in a later update.',
            '/adapter/import': 'Live broker connections need a hosted connector.',
            '/import/files': 'Statement uploads will be available with hosted imports.',
            '/import/remove': 'Manage imported sources locally for now.',
            '/import/desk-board': 'Local desk imports are not available online.',
            '/signals/run': 'Signal execution will be available with a hosted agent.',
            '/court': 'Connect an AI agent key to run the courts.',
            '/docket': 'Connect an AI agent key to run the courts.',
            '/chat': 'Connect an AI agent key to use chat.',
            '/commitments/preview': 'AI editing needs an agent key. Use the manual editor.'}


def extra_path(name):
    return name in EXTRAS or bool(re.fullmatch(
        r'(?:inflow_previews|commitment_previews)/[a-f0-9-]{36}\.json', name))


def materialize(folder, record):
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


def capture(folder):
    manifest, chunks = snapshot(folder)
    documents = {f['path']: base64.b64encode(b''.join(chunks[h] for h in f['chunks'])).decode()
                 for f in manifest['files']}
    extra = {}
    for path in folder.rglob('*'):
        name = path.relative_to(folder).as_posix()
        if path.is_file() and extra_path(name):
            data = path.read_bytes()
            inspect_document(name, data)
            extra[name] = base64.b64encode(data).decode()
    if sum(f['size'] for f in manifest['files']) + sum(len(base64.b64decode(b)) for b in extra.values()) > MAX_TOTAL:
        raise ValueError('Office exceeds the workspace size limit')
    return {'manifest': manifest, 'documents': documents, 'workspace': extra}


def publish(offices, uid, receipt, record):
    prefix = offices.prefix(uid, receipt['office_id'])
    current, generation = offices.db().get(prefix + 'active')
    if not current or current['digest'] != receipt['digest']:
        raise AuthFailure('The office changed in another tab. Reload and review before saving.', 409)
    revision = digest(canonical(record))
    try:
        offices.db().put(prefix + 'revisions/' + revision, record)
    except Conflict:
        pass
    answers = json.loads(base64.b64decode(record['documents']['answers.json']))
    balance = json.loads(base64.b64decode(record['documents']['balance_sheet.json']))
    updated = dict(receipt, digest=revision, activated_at=stamp(), as_of=balance['as_of'],
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


def dispatch(offices, uid, oid, method, path, raw=b'', content_type='', expected=None):
    receipt, record = offices.read(uid, oid)
    if method == 'POST' and path != '/api-errors/dismiss' and expected != receipt['digest']:
        raise AuthFailure('The office changed since this page was opened. Reload and review before saving.', 409)
    if method == 'GET' and path == '/state':
        return 200, {'Content-Type': 'application/json'}, json.dumps({'v': receipt['digest']}).encode(), receipt
    if method == 'POST' and path not in POSTS:
        raise AuthFailure(DISABLED.get(path, 'This action is not available in the hosted office yet.'), 400)
    if method == 'GET' and path not in GETS and not re.fullmatch(r'/pages/[A-Za-z0-9_.-]+\.html', path):
        raise AuthFailure('Page not found.', 404)
    with tempfile.TemporaryDirectory(prefix='wp-office-') as directory:
        folder = Path(directory)
        materialize(folder, record)
        with hosted_office(folder):
            from officekit.serve import render_saved_office
            if method == 'GET' and (path == '/' or path.startswith('/pages/')):
                render_saved_office(folder)
            status, headers, data = local_request(folder, method, path, raw, content_type)
            if method == 'POST' and status < 400:
                updated = capture(folder)
                # Rendering and exploratory calculations need no new revision.
                if updated['documents'] != record['documents'] or updated['workspace'] != record.get('workspace', {}):
                    receipt = publish(offices, uid, receipt, updated)
        if status >= 400 and 'text/plain' in headers.get('Content-Type', ''):
            from officekit.serve import STYLE
            data = ('<!doctype html><html lang="en"><head><title>Request needs attention</title><style>' + STYLE + '</style></head><body><main class="wrap"><h1>Changes were not saved</h1><p role="alert">' + escape(data.decode()) + '</p><button type="button" onclick="history.back()">Back to your edits</button></main></body></html>').encode()
            headers['Content-Type'] = 'text/html; charset=utf-8'
        return status, headers, data, receipt


CLIENT = r'''<script nonce="NONCE">
window.officeBase=BASE;
(function(){
 const base=window.officeBase, revision=REVISION, csrf=__WP_CSRF__;
 const resolve=value=>typeof value==='string'&&value.startsWith('/')&&!value.startsWith('//')&&value!=='/app'&&!value.startsWith('/app/')?base+value:value;
 const original=window.fetch.bind(window);
 window.fetch=function(input,options){
   const url=typeof input==='string'?resolve(input):input;
   const target=new URL(typeof url==='string'?url:url.url,location.href);
   if(target.origin===location.origin&&target.pathname.startsWith(base+'/')){
     options=Object.assign({},options);options.headers=new Headers(options.headers|| (input instanceof Request?input.headers:{}));
     options.headers.set('X-CSRF-Token',csrf);options.headers.set('X-Office-Revision',revision);
   }
   return original(url,options);
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
    html = html.replace('<a class="host-office" href="/hosting" target="_blank" rel="noopener">Host office ↗</a>',
                        '<a class="host-office" href="' + base + '/settings">Hosted office</a>')
    html = html.replace('<a class="reb" href="/reset">start over</a>', '<a class="reb" href="/app" target="_top">Account</a>')
    nonce = secrets.token_urlsafe(24)
    parser = Presentation(base, receipt['digest'], csrf, nonce)
    parser.feed(html)
    parser.close()
    policy = ("default-src 'self'; script-src 'self' 'nonce-" + nonce + "'; style-src 'self' 'unsafe-inline'; "
              "img-src 'self' data:; connect-src 'self'; frame-src 'self'; frame-ancestors 'self'; "
              "base-uri 'none'; object-src 'none'; form-action 'self'")
    return ''.join(parser.output), policy


def settings(receipt):
    from officekit.serve import STYLE
    base = receipt['path']
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Hosted office</title><style>' + STYLE + '</style></head><body><main class="wrap"><a class="reb" href="' + base + '">← Back to your office</a><h1>Hosted office</h1><p class="sub">The same workspace, saved online.</p><section class="panel"><h2>Private &amp; saved</h2><p>Your edits are saved to your signed-in account. Your local copy stays separate; export a copy whenever you need it.</p><a class="btn" href="' + base + '/export">Export office</a></section><section class="panel"><h2>AI agent</h2><p>No key connected. Manual planning and the model-based Risk Officer work now. Strategy briefs are saved for research, courts and pitch decks once an agent key is connected.</p></section><section class="panel"><h2>Research</h2><p>Your retained research stays with this office. The included SignalOS library is available to every account.</p><a class="reb" href="' + base + '/documents">Saved documents &amp; research →</a><br><a class="reb" href="/app/research">Open SignalOS library →</a></section></main></body></html>'
