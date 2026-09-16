"""Office-wide API failure notices, independent of financial facts and pages."""
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import re
import tempfile
import threading
import uuid

_LOCK = threading.RLock()
LIMIT = 20
LOGGER = logging.getLogger(__name__)
UNEXPECTED = 'Something went wrong. Your request could not be completed. Try again; details are in the server log.'


def classify(error):
    """Classify before formatting; unexpected implementation details stay local."""
    if isinstance(error, ValueError) and not isinstance(error, json.JSONDecodeError):
        return 400, message(str(error))
    friendly = message(str(error))
    if friendly.startswith(('The configured model provider ', 'The API could not authenticate.',
                            'The API rate limit ', 'The API could not be reached.')) and not isinstance(error, (KeyError, AttributeError, TypeError)):
        return 502, friendly
    return 500, UNEXPECTED


def log_exception(error, context):
    if not isinstance(error, ValueError) or isinstance(error, json.JSONDecodeError):
        LOGGER.error('Request failed: %s', context,
                     exc_info=(type(error), error, error.__traceback__))


def message(error):
    if isinstance(error, BaseException):
        return classify(error)[1]
    detail = str(error)
    low = detail.lower()
    if 'credit balance' in low or 'insufficient_quota' in low or 'insufficient api credit' in low:
        return 'The configured model provider has insufficient API credit. Add credit with that provider, then retry or resume the review. Completed reviews are retained.'
    if any(s in low for s in ('api_key', 'authentication', 'unauthorized', 'invalid api key')):
        return "The API could not authenticate. Check this office's provider credentials, then try again."
    if any(s in low for s in ('rate_limit', 'rate limit', 'too many requests')):
        return 'The API rate limit was reached. Wait a moment, then try again.'
    if any(s in low for s in ('timed out', 'timeout', 'connection refused', 'connection error')):
        return 'The API could not be reached. Check the connection or provider status, then try again.'
    # Provider errors occasionally echo headers/URLs. Never put credentials in
    # the browser notice. Raw diagnostics remain with the original caller.
    detail = re.sub(r'(?i)(bearer\s+|(?:api[_-]?key|token|secret)\s*[=:]\s*)[^\s,}\]&]+', r'\1[redacted]', detail)
    detail = re.sub(r'\bsk-[A-Za-z0-9_-]+', '[redacted]', detail)
    detail = re.sub(r'(?i)(?:[A-Z]:[\\/]|/(?:Users|home|tmp|var|private|etc)/)[^\s\'"<>]+', '[local path]', detail)
    return detail[:600] or 'The API request failed. Try again from the original action.'


def _path(folder):
    return Path(folder) / 'api_errors.json'


def active(folder):
    with _LOCK:
        try:
            data = json.loads(_path(folder).read_text())
            if not isinstance(data, list):
                return []
            return [e for e in data if isinstance(e, dict) and all(isinstance(e.get(k), str) for k in ('id', 'context', 'title', 'message'))][-LIMIT:]
        except (OSError, ValueError):
            return []


def _save(folder, data):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=folder, prefix='.api-errors-', delete=False) as f:
        json.dump(data[-LIMIT:], f)
    try:
        os.replace(f.name, _path(folder))
    finally:
        Path(f.name).unlink(missing_ok=True)


def report(folder, context, title, error, href=None):
    """Best effort: recording a notice must not mask the original API failure."""
    if isinstance(error, BaseException):
        log_exception(error, context)
    try:
        with _LOCK:
            rows = active(folder)
            msg = message(error)
            old = next((e for e in rows if e['context'] == context and e['message'] == msg), None)
            event = {'id': old['id'] if old else str(uuid.uuid4()), 'context': context,
                     'title': str(title)[:120], 'message': msg,
                     'at': datetime.now(timezone.utc).isoformat(),
                     'href': href if href and re.fullmatch(r'/pages/[A-Za-z0-9_.-]+\.html(?:#[A-Za-z0-9_-]+)?', href) else None}
            _save(folder, [e for e in rows if e['context'] != context] + [event])
            return event
    except OSError:
        return None


def clear(folder, context=None, event_id=None):
    """Dismiss the exact displayed event, or clear a successfully retried action."""
    try:
        with _LOCK:
            rows = active(folder)
            remaining = [e for e in rows if not (e['id'] == event_id or e['context'] == context)]
            if len(remaining) != len(rows):
                _save(folder, remaining)
    except OSError:
        pass


# Injected only when served, so old rendered pages gain the banner too. Pure
# renderers and exported HTML stay offline and existing golden pages stay stable.
SCRIPT = r'''<script data-office-api-errors>
(function(){
 if(window.officeApiErrors)return;
 const originalFetch=window.fetch.bind(window), local=new Map(),dismissed=new Set();let remote=[],bar,signature='';
 let host;try{if(parent!==window&&parent.location.origin===location.origin)host=parent.officeApiErrors;}catch(e){}
 function show(context,title,msg,href,id){if(host)return host.show(context,title,msg,href,id);local.set(context,{id:id||'local:'+context,context,title,message:msg,href});render();}
 function clear(context){if(host)return host.clear(context);local.delete(context);remote=remote.filter(e=>e.context!==context);render();}
 window.officeApiErrors={show,clear};
 function render(){
  if(host||!document.body)return;
  const merged=new Map(remote.filter(e=>!dismissed.has(e.id)).map(e=>[e.context,e]));for(const [key,e] of local){merged.delete(key);merged.set(key,e);}
  const items=Array.from(merged.values()),e=items[items.length-1];
  const next=JSON.stringify(items);if(next===signature)return;signature=next;
  if(!bar){bar=document.createElement('aside');bar.id='api-error-banner';bar.setAttribute('role','alert');bar.setAttribute('aria-live','assertive');bar.setAttribute('aria-atomic','true');
   bar.innerHTML='<div class="api-error-copy"><strong></strong><div class="api-error-message"></div></div><span class="api-error-count"></span><a hidden>Review</a><button type="button" aria-label="Dismiss API error">Dismiss</button>';
   document.body.prepend(bar);
  }
  bar.hidden=!e;if(!e)return;
  bar.querySelector('strong').textContent=e.title;
  bar.querySelector('.api-error-message').textContent=e.message;
  bar.querySelector('.api-error-count').textContent=items.length>1?items.length+' API issues':'';
  const link=bar.querySelector('a');link.hidden=!/^\/pages\/[a-zA-Z0-9_.-]+\.html(?:#[a-zA-Z0-9_-]+)?$/.test(e.href||'');
  if(!link.hidden){link.href=e.href;link.onclick=function(ev){const pane=document.getElementById('pane');if(pane){ev.preventDefault();pane.src=e.href;}};}
  bar.querySelector('button').onclick=async function(){
   if(e.id.startsWith('local:')){local.delete(e.context);render();return;}
   try{const r=await originalFetch('/api-errors/dismiss',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:e.id})});if(!r.ok)throw Error();
    dismissed.add(e.id);remote=remote.filter(x=>x.id!==e.id);local.delete(e.context);render();
   }catch(err){show('notice-dismiss','Could not dismiss the error','The app could not save the dismissal. Check the connection and try again.');}
  };
 }
 window.fetch=async function(input,options){
  let path;try{const u=new URL(typeof input==='string'?input:input.url,location.href);if(u.origin===location.origin)path=u.pathname;}catch(e){}
  if(!path||path.startsWith('/api-errors'))return originalFetch(input,options);
  let context='request:'+path;
  try{
   const r=await originalFetch(input,options);
   const id=r.headers.get('X-Office-API-Error-Id');
   if(r.headers.get('X-Office-API-Error-Context'))context=decodeURIComponent(r.headers.get('X-Office-API-Error-Context'));
   if(!r.ok)show(context,'API request failed','The request failed (HTTP '+r.status+'). Try again from the original action.',null,id);
   else clear(context);
   if(r.status!==204&&(r.headers.get('Content-Type')||'').includes('application/json'))r.clone().json().then(data=>{
    if(data&&data.error)show(context,'API request failed',String(data.error),null,id);
   }).catch(()=>show(context,'API response could not be read','The server returned an invalid response. Try again from the original action.'));
   return r;
  }catch(e){show(context,'Connection interrupted','The API could not be reached. Check your connection, then try again.');throw e;}
 };
 async function poll(){
  try{const r=await originalFetch('/api-errors',{cache:'no-store'});if(!r.ok)throw Error();const data=await r.json();if(!Array.isArray(data))throw Error();
   remote=data;local.delete('notice-connection');local.delete('notice-dismiss');for(const e of remote)local.delete(e.context);render();
  }catch(e){show('notice-connection','Connection interrupted','The app could not check API status. Check the local server and your connection.');}
 }
 if(!host){function start(){render();poll();setInterval(poll,4000);}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start);else start();}
})();
</script>'''

STYLE = '''<style>
#api-error-banner[hidden]{display:none!important}
#api-error-banner{position:sticky;top:0;z-index:1000;display:flex;align-items:center;gap:14px;flex:0 0 auto;max-height:30vh;overflow:auto;box-sizing:border-box;padding:12px 20px;background:#351a20;border-bottom:1px solid #9a4653;color:#ffe1e5;font:13px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
#api-error-banner .api-error-copy{flex:1;min-width:0;overflow-wrap:anywhere}#api-error-banner strong{display:block;font-size:13px;color:#fff0f2}#api-error-banner .api-error-message{margin-top:2px}#api-error-banner .api-error-count{font-size:11px;white-space:nowrap;color:#f4b3bc}#api-error-banner a{color:#ffd7de;white-space:nowrap;font-weight:600}#api-error-banner button{background:transparent;color:#ffe1e5;border:1px solid #a56b75;border-radius:6px;padding:6px 10px;cursor:pointer;font:inherit;width:auto;flex:0 0 auto;margin:0}
@media(max-width:600px){#api-error-banner{padding:10px 12px;gap:10px;flex-wrap:wrap}#api-error-banner .api-error-copy{flex-basis:100%}}
@media print{#api-error-banner{display:none!important}}
</style>'''


def inject(body):
    if 'data-office-api-errors' in body:
        return body
    if '</head>' in body:
        return body.replace('</head>', STYLE + SCRIPT + '</head>', 1)
    return STYLE + SCRIPT + body
