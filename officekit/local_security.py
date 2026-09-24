"""Loopback browser boundary shared by every local route.

The random token lasts for one server session. Hosted dispatch has its own
authenticated Origin/CSRF boundary and never uses this local transport.
"""
import hmac
import io
import json
import re
import secrets

MAX_BODY = 64 * 1024 * 1024
HEADER = 'X-Office-Local-CSRF'
FIELD = '_local_csrf'


class Boundary:
    def __init__(self):
        self.token = secrets.token_urlsafe(32)

    def check(self, request):
        port = request.server.server_address[1]
        hosts = {f'127.0.0.1:{port}', f'localhost:{port}', f'[::1]:{port}'}
        host = request.headers.get('Host', '')
        if len(request.headers.get_all('Host', [])) != 1 or host not in hosts:
            return 'Open the app using its loopback address.'
        origin = request.headers.get('Origin')
        if origin is not None and origin != 'http://' + host:
            return 'Requests must come from this local app.'
        if request.headers.get('Sec-Fetch-Site') == 'cross-site':
            return 'Cross-site requests are not accepted.'
        if request.command != 'POST':
            return None
        try:
            sizes = request.headers.get_all('Content-Length', [])
            if len(sizes) != 1 or request.headers.get('Transfer-Encoding'):
                raise ValueError()
            size = int(sizes[0])
            if not 0 <= size <= MAX_BODY:
                raise ValueError()
        except ValueError:
            return 'Invalid request size.'
        supplied = request.headers.get(HEADER, '')
        if not supplied and request.headers.get_content_type() in {'application/x-www-form-urlencoded', 'multipart/form-data'}:
            from officekit.formdata import parse
            raw = request.rfile.read(size)
            if len(raw) != size:
                return 'Incomplete request.'
            request.rfile = io.BytesIO(raw)
            supplied = parse(io.BytesIO(raw), request.headers).getvalue(FIELD, '')
        if not isinstance(supplied, str) or not hmac.compare_digest(supplied, self.token):
            return 'Reload the local app before saving; the session token is missing or expired.'
        return None

    def inject(self, body):
        # Rendered HTML is app-owned. Relative POST actions receive a hidden
        # field, including native forms submitted without JavaScript.
        def stamp(match):
            tag = match[0]
            action = re.search(r'\baction=[\"\']([^\"\']*)[\"\']', tag, re.I)
            if action and (action[1].startswith('//') or re.match(r'^[a-zA-Z][\w+.-]*:', action[1])):
                return tag
            if not re.search(r'\bmethod=[\"\']POST[\"\']', tag, re.I):
                return tag
            return tag + f'<input type="hidden" name="{FIELD}" value="{self.token}">'
        body = re.sub(r'<form\b[^>]*>', stamp, body, flags=re.I)
        script = '''<script>(function(){
const localSessionToken=TOKEN, original=window.fetch.bind(window);
window.fetch=function(input, options){
 const url=new URL(typeof input==='string'?input:input.url,location.href);
 if(url.origin===location.origin){
  options=Object.assign({},options);options.headers=new Headers(options.headers||(input instanceof Request?input.headers:{}));
  options.headers.set('X-Office-Local-CSRF',localSessionToken);
 }
 return original(input,options);
};
document.addEventListener('submit',function(event){
 const form=event.target;
 if(form.method.toUpperCase()!=='POST'||new URL(form.action,location.href).origin!==location.origin)return;
 let field=form.querySelector('input[name="_local_csrf"]');
 if(!field){field=document.createElement('input');field.type='hidden';field.name='_local_csrf';form.appendChild(field);}
 field.value=localSessionToken;
},true);
})();</script>'''.replace('TOKEN', json.dumps(self.token))
        return re.sub(r'(<head\b[^>]*>)', lambda m: m[0] + script, body, count=1, flags=re.I)
