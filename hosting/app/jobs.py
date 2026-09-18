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
from .auth import AuthFailure
from .store import Conflict

LOG = logging.getLogger(__name__)
LONG_PATHS = {'/import/files', '/adapter/import', '/chat', '/court', '/docket',
              '/signals/run', '/commitments/preview', '/strategy/new', '/strategy/propose',
              '/strategy/adopt', '/strategy/goal-adopt', '/strategy/proposal/retry',
              '/strategy/proposal/revise'}
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
        self.offices.read(uid, oid)
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
            job.update(status='complete', response={'status': status, 'headers': headers,
                       'body': base64.b64encode(data).decode()}, receipt=receipt)
        except Exception as error:
            LOG.exception('Office job failed: %s', jid)
            job.update(status='error', error=str(error) if isinstance(error, AuthFailure) else 'Background work failed. Saved checkpoints are retained. Review them before retrying.')
        job.pop('raw', None)
        job['finished'] = time.time()
        self.offices.db().put(self.key(uid, oid, jid), job, generation)
        self.release(uid, oid, jid)


def progress_page(jid):
    from officekit.serve import STYLE
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Office working</title><style>''' + STYLE + '''</style></head><body><main class="wrap"><h1>Working on your office</h1><p id="job-status" role="status">Queued securely. You can leave this page and return from Office settings.</p><p>Saved pages stay available while this work runs. Editing resumes when it finishes.</p><a href="/" target="_top">Open office</a><script>
(async function poll(){try{const r=await fetch('/jobs/''' + jid + '''/status'),s=await r.json();if(!r.ok)throw new Error(s.error||'Could not load status');if(s.status==='complete'){location.replace((window.officeBase||'')+'/jobs/''' + jid + '''/result');return;}if(s.error){document.getElementById('job-status').textContent=s.error;return;}document.getElementById('job-status').textContent=s.status==='running'?'Running. Progress and completed research are saved as checkpoints.':'Queued securely…';}catch(e){document.getElementById('job-status').textContent=e.message;}setTimeout(poll,2500);})();
</script></main></body></html>'''
