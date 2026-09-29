"""Durable, owner-scoped jobs. A delivery never repeats an in-flight paid call.

One writer per office while a job runs; reads and checkpoints remain available.
An expired attempt requires an explicit resubmission. Cloud Tasks retries only
transport/claim failures, not model calls that may already have been billed.
"""
import base64
import json
import logging
import os
import re
import time
import uuid
from html import escape
from .auth import AuthFailure
from .store import Conflict

LOG = logging.getLogger(__name__)
LONG_PATHS = {'/risk/forecast', '/import/files', '/adapter/import', '/chat', '/court', '/docket',
              '/signals/run', '/commitments/preview', '/strategy/new', '/strategy/propose',
              '/strategy/adopt', '/strategy/goal-adopt', '/strategy/proposal/retry',
              '/strategy/proposal/revise', '/strategy/deploy'}
TTL = 1800


def writable(current, job_id=None):
    active = current.get('job') or {}
    if job_id:
        if active.get('id') != job_id or active.get('expires', 0) <= time.time():
            raise AuthFailure('This background attempt expired. Its saved checkpoints are available for review.', 409)
    elif active.get('expires', 0) > time.time():
        raise AuthFailure('Background work is updating this office. Wait for it to finish, then reload before saving.', 409)


class CloudQueue:
    def __init__(self, origin):
        self.origin = origin
        self.queue = os.environ['OFFICE_TASK_QUEUE']
        self.service_account = os.environ['OFFICE_TASK_ACCOUNT']

    def submit(self, uid, oid, jid):
        from google.cloud import tasks_v2
        from google.protobuf.duration_pb2 import Duration
        tasks_v2.CloudTasksClient().create_task(request={'parent': self.queue, 'task': {
            'name': self.queue + '/tasks/' + jid,
            'dispatch_deadline': Duration(seconds=TTL),
            'http_request': {'http_method': tasks_v2.HttpMethod.POST,
                'url': self.origin + '/internal/office-job',
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'uid': uid, 'oid': oid, 'job': jid}).encode(),
                'oidc_token': {'service_account_email': self.service_account, 'audience': self.origin}}}})

    def verify(self, bearer):
        from google.oauth2 import id_token
        from google.auth.transport.requests import Request
        try:
            claims = id_token.verify_oauth2_token(bearer, Request(), self.origin)
            if claims.get('email') != self.service_account or claims.get('email_verified') is not True:
                raise ValueError()
        except Exception:
            raise AuthFailure('Worker authentication required.', 403) from None


class Jobs:
    def __init__(self, offices, queue):
        self.offices, self.queue = offices, queue

    def key(self, uid, oid, jid):
        if not isinstance(jid, str) or not re.fullmatch('[a-f0-9-]{36}', jid):
            raise AuthFailure('Job not found.', 404)
        return 'office-jobs/' + self.offices.prefix(uid, oid).removeprefix('offices/') + jid

    def read(self, uid, oid, jid):
        receipt, _ = self.offices.db().get(self.offices.prefix(uid, oid) + 'active')
        if receipt is None:
            raise AuthFailure('Office not found.', 404)
        value, generation = self.offices.db().get(self.key(uid, oid, jid))
        if not value:
            raise AuthFailure('Job not found.', 404)
        if value['status'] in {'queued', 'running'} and value['expires'] <= time.time():
            value = dict(value, status='interrupted', error='This attempt was interrupted. Saved checkpoints are retained. Review them before submitting again; provider charges may already have occurred.')
        return value, generation

    def start(self, uid, oid, path, raw, ctype, expected):
        if self.queue is None:
            raise AuthFailure('Background workers are being configured. Try again shortly.', 503)
        prefix = self.offices.prefix(uid, oid)
        receipt, generation = self.offices.db().get(prefix + 'active')
        if not receipt:
            raise AuthFailure('Office not found.', 404)
        writable(receipt)
        if receipt['digest'] != expected:
            raise AuthFailure('The office changed. Reload and review before starting.', 409)
        jid = str(uuid.uuid4())
        job = {'id': jid, 'status': 'queued', 'path': path, 'raw': base64.b64encode(raw).decode(),
               'content_type': ctype, 'expected': expected, 'created': time.time(), 'expires': time.time() + TTL}
        self.offices.db().put(self.key(uid, oid, jid), job)
        try:
            self.offices.db().put(prefix + 'active', dict(receipt, job={'id': jid, 'expires': job['expires']}), generation)
        except Conflict:
            raise AuthFailure('The office changed. Reload before starting.', 409) from None
        try:
            self.queue.submit(uid, oid, jid)
        except Exception:
            LOG.exception('Could not enqueue office job %s', jid)
            current, gen = self.offices.db().get(self.key(uid, oid, jid))
            # A delivery may already have started. Never overwrite its claim.
            if current['status'] == 'queued':
                try:
                    self.offices.db().put(self.key(uid, oid, jid), dict(current, status='error', error='Could not start the background job. Please try again.'), gen)
                    self.release(uid, oid, jid)
                except Conflict:
                    pass
            raise AuthFailure('Could not confirm the background job. Check Office settings before retrying.', 503) from None
        return jid

    def release(self, uid, oid, jid):
        key = self.offices.prefix(uid, oid) + 'active'
        current, generation = self.offices.db().get(key)
        if (current.get('job') or {}).get('id') == jid:
            current['last_job'] = jid
            current.pop('job', None)
            try:
                self.offices.db().put(key, current, generation)
            except Conflict:
                pass

    def run(self, uid, oid, jid):
        job, generation = self.read(uid, oid, jid)
        if job['status'] != 'queued':
            return  # Includes running: never repeat an uncertain paid call.
        job['status'] = 'running'
        try:
            self.offices.db().put(self.key(uid, oid, jid), job, generation)
        except Conflict:
            return
        _, generation = self.offices.db().get(self.key(uid, oid, jid))
        try:
            from .workspace import dispatch
            status, headers, data, receipt = dispatch(self.offices, uid, oid, 'POST', job['path'],
                base64.b64decode(job['raw']), job['content_type'], job['expected'], job_id=jid)
            job.update(status='error' if status >= 400 else 'complete', response={'status': status, 'headers': headers,
                       'body': base64.b64encode(data).decode()}, receipt=receipt)
            if status >= 400:
                job['error'] = 'Background request failed (HTTP ' + str(status) + '). Open the office for the saved error, correct its cause, then retry.'
            # A handler may redirect successfully after the research pipeline
            # saved an error. Transport success is not a completed review.
            _, record = self.offices.read(uid, oid)
            state = public_state(job, record)
            if state['status'] == 'error':
                job.update(status='error', error=state['error'])
        except Exception as error:
            LOG.exception('Office job failed: %s', jid)
            job.update(status='error', error=str(error) if isinstance(error, AuthFailure) else 'Background work failed. Saved checkpoints are retained. Review them before retrying.')
        job.pop('raw', None)
        job['finished'] = time.time()
        self.offices.db().put(self.key(uid, oid, jid), job, generation)
        self.release(uid, oid, jid)


def public_state(job, record):
    """Expose only persisted progress and safe links within this owned office."""
    from officekit.strategy_proposals import progress
    destination = (job.get('response') or {}).get('headers', {}).get('Location', '')
    linked = re.fullmatch(r'/pages/proposal_([a-f0-9-]{36})\.html', destination)
    proposals = []
    for name, encoded in record.get('documents', {}).items():
        match = re.fullmatch(r'strategy_proposals/([a-f0-9-]{36})\.json', name)
        if not match:
            continue
        p = json.loads(base64.b64decode(encoded))
        if p.get('job_id') == job['id'] or (linked and match[1] == linked[1]):
            proposals.append(progress(p))
    failed = next((p for p in proposals if p['status'] == 'error'), None)
    status = job['status']
    error = job.get('error')
    if failed and status in {'running', 'complete', 'error'}:
        status, error = 'error', failed['error'] or 'The saved proposal needs attention.'
    return {'status': status, 'error': error, 'proposals': proposals,
            'stage': proposals[-1]['stage'] if proposals else ('Waiting for a worker' if status == 'queued' else 'Preparing office inputs'),
            'elapsed_seconds': max(0, int(job.get('finished', time.time()) - job['created'])),
            'title': 'Strategy review' if job['path'].startswith('/strategy/') else 'Office task'}


def progress_page(jid, state=None):
    from officekit.serve import STYLE
    state = state or {'status': 'queued', 'stage': 'Waiting for a worker', 'proposals': [], 'title': 'Office task'}
    initial = json.dumps(state).replace('<', '\\u003c')
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Review progress</title><style>''' + STYLE + '''</style></head><body><main class="wrap">
<h1 id="job-title">''' + escape(state['title']) + '''</h1>
<p id="job-status" role="status" aria-live="polite">''' + escape(state.get('error') or state['stage']) + '''</p>
<p id="job-time"></p><div id="saved-work"></div>
<p>Your saved work remains available if you leave this page. Reopening it does not restart research. A resume reuses completed steps; a fresh revision reviews changed inputs.</p>
<p><a href="/pages/strategies.html#proposals">Saved strategies and proposals</a> · <a href="/" target="_top">Open office</a></p>
<script>
(function(){
 const initial=INITIAL_STATE, terminal=new Set(['complete','error','interrupted']);
 function render(s){
  document.getElementById('job-title').textContent=s.status==='error'?'Review needs attention':s.status==='interrupted'?'Review interrupted':s.status==='complete'?'Work saved':s.title;
  document.getElementById('job-status').textContent=s.error||s.stage;
  const seconds=s.elapsed_seconds||0;document.getElementById('job-time').textContent='Elapsed: '+Math.floor(seconds/60)+'m '+seconds%60+'s';
  const host=document.getElementById('saved-work');host.replaceChildren();
  for(const p of s.proposals||[]){
   const section=document.createElement('section');section.className='panel';
   const heading=document.createElement('h2');heading.textContent=p.title;section.append(heading);
   if(/^\/pages\/proposal_[a-f0-9-]{36}\.html$/.test(p.href)){const a=document.createElement('a');a.href=(window.officeBase||'')+p.href;a.textContent='Open saved proposal and completed results →';section.append(a);}
   const updated=document.createElement('p');updated.textContent='Last saved: '+p.updated_at+' · '+p.stage;section.append(updated);
   const label=document.createElement('h3');label.textContent='Saved so far';section.append(label);
   const saved=document.createElement('ul');for(const item of p.saved){const li=document.createElement('li');li.textContent=item;saved.append(li);}section.append(saved);
   const history=document.createElement('details'), summary=document.createElement('summary');summary.textContent='Recent checkpoints';history.append(summary);
   const list=document.createElement('ol');for(const item of p.history){const li=document.createElement('li');li.textContent=item.at+' · '+item.stage;list.append(li);}history.append(list);section.append(history);host.append(section);
  }
 }
 function done(s){if(s.status==='complete'){location.replace((window.officeBase||'')+'/jobs/JOB_ID/result');return true;}return terminal.has(s.status);}
 render(initial);if(done(initial))return;
 (async function poll(){try{const r=await fetch('/jobs/JOB_ID/status'),s=await r.json();if(!r.ok)throw new Error(s.error||'Could not load saved progress');render(s);if(done(s))return;}catch(e){document.getElementById('job-status').textContent=e.message+' — retrying the progress check.';}setTimeout(poll,2500);})();
})();
</script></main></body></html>'''.replace('JOB_ID', jid).replace('INITIAL_STATE', initial)
