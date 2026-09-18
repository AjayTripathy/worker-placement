"""Local hosting workflow. Browser sees progress, never credentials or proofs."""
import hmac
import json
from pathlib import Path
import secrets
import threading
import time

from officekit import api_errors, cloud
from officekit import cloud_sync as sync
from officekit.migration import snapshot, validate_manifest
from officekit.render_hosting import render_hosting


class Hosting:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.csrf = secrets.token_urlsafe(32)
        self.lock = threading.RLock()
        self.prepared = None
        self.state = dict(phase='idle', busy=False, connected=False, email=None,
                          error=None, preview=None, url=None, done=0, total=0)
        try:
            auth = cloud.credentials()
            self.state.update(connected=True, email=auth['email'])
        except (ValueError, OSError, KeyError):
            pass

    def view(self):
        with self.lock:
            return json.loads(json.dumps(dict(self.state, sync=sync.read(self.folder))))

    def update(self, **values):
        with self.lock:
            self.state.update(values)

    def launch(self, phase, work, clear=False):
        with self.lock:
            if self.state['busy']:
                raise ValueError('An action is already in progress. Wait for it to finish.')
            if clear:
                self.prepared = None
                self.state.update(preview=None, url=None)
            self.state.update(phase=phase, busy=True, error=None, code=None, login_url=None)

        def run():
            try:
                work()
                api_errors.clear(self.folder, context='hosting')
            except Exception as error:
                api_errors.log_exception(error, 'hosting')
                detail = api_errors.classify(error)[1]
                if './wp login' in detail:
                    detail = 'Sign in with Google again, then review your office before uploading.'
                    self.update(connected=False)
                if '--replace-revision' in detail:
                    detail = 'The hosted office changed. Review the files again before replacing it.'
                detail = detail.replace('Rerun ./wp migrate', 'Choose Upload again')
                self.update(phase='error', error=detail)
                api_errors.report(self.folder, 'hosting', 'Hosting needs attention', detail)
            finally:
                self.update(busy=False)

        threading.Thread(target=run, daemon=True, name='office-hosting').start()
        return self.view()

    def login(self):
        def work():
            pending = cloud.begin_login()
            self.update(phase='authorizing', code=pending['code'], login_url=pending['url'])
            deadline = time.monotonic() + 900
            while time.monotonic() < deadline:
                result = cloud.poll_login(pending)
                if result.get('status') == 'approved':
                    cloud.remember_login(pending, result)
                    self.update(phase='connected', connected=True, email=result['email'],
                                code=None, login_url=None)
                    return
                time.sleep(3)
            raise ValueError('Sign-in expired. Choose Sign in with Google to try again.')
        return self.launch('connecting', work, clear=True)

    def review(self):
        def work():
            auth = cloud.credentials()
            who = cloud.request(auth['origin'], '/api/me', token=auth['token'])
            manifest, chunks = snapshot(self.folder)
            sid = validate_manifest(manifest)
            offices = cloud.request(auth['origin'], '/api/offices', token=auth['token'])['offices']
            current = next((o for o in offices if o['office_id'] == manifest['office_id']), None)
            if current:
                cloud.receipt_url(auth['origin'], current)
            answer_file = next(f for f in manifest['files'] if f['path'] == 'answers.json')
            answers = json.loads(b''.join(chunks[h] for h in answer_file['chunks']))
            preview = dict(id=secrets.token_urlsafe(24), name=answers.get('owner') or 'Your office',
                           as_of=answers.get('as_of'), email=who['email'],
                           files=[{'path': f['path'], 'size': f['size']} for f in manifest['files']],
                           bytes=sum(f['size'] for f in manifest['files']),
                           replace_required=bool(current and current['digest'] != sid),
                           already_hosted=bool(current and current['digest'] == sid),
                           hosted_at=current.get('activated_at') if current else None)
            with self.lock:
                self.prepared = dict(manifest=manifest, chunks=chunks, auth=auth,
                                     replacement=current['digest'] if current else None,
                                     id=preview['id'], created=time.monotonic(), email=who['email'])
                self.state.update(phase='review', connected=True, email=who['email'], preview=preview,
                                  url=cloud.receipt_url(auth['origin'], current) if current else None)
        return self.launch('reviewing', work, clear=True)

    def upload(self, preview_id, replace=False):
        with self.lock:
            prepared = self.prepared
            if not prepared or preview_id != prepared['id'] or time.monotonic() - prepared['created'] > 900:
                raise ValueError('This review expired. Review your saved files again before uploading.')
            if type(replace) is not bool or (self.state['preview']['replace_required'] and not replace):
                raise ValueError('Confirm that you want to replace the existing hosted snapshot.')
            if self.state['busy'] and self.state['phase'] in {'uploading', 'verifying'}:
                return self.view()

            def work():
                auth = cloud.credentials()
                if auth['origin'] != prepared['auth']['origin'] or auth['token'] != prepared['auth']['token']:
                    raise ValueError('Your signed-in account changed. Review the files again.')
                manifest, _ = snapshot(self.folder)
                if validate_manifest(manifest) != validate_manifest(prepared['manifest']):
                    raise ValueError('Your local office changed after this review. Review the saved files again.')
                who = cloud.request(auth['origin'], '/api/me', token=auth['token'])
                if who['email'] != prepared['email']:
                    raise ValueError('Your signed-in account changed. Review the files again.')
                receipt = cloud.upload_snapshot(prepared['manifest'], prepared['chunks'], auth,
                    prepared['replacement'], lambda phase, done, total: self.update(phase=phase, done=done, total=total))
                cloud.save_private(self.folder / '.hosted-receipt.json', receipt)
                self.update(phase='complete', url=cloud.receipt_url(auth['origin'], receipt))

            return self.launch('uploading', work)


def handle(handler, hosting):
    """Restrict this credentialed bridge to its loopback origin and page token."""
    host = handler.headers.get('Host', '')
    port = handler.server.server_address[1]
    if host not in {f'127.0.0.1:{port}', f'localhost:{port}', f'[::1]:{port}'}:
        return handler._send('{"error":"Open this page from the local app."}', 403, 'application/json', public=True)
    if handler.command == 'GET' and handler.path == '/hosting':
        return handler._send(render_hosting(hosting.csrf))
    token = handler.headers.get('X-Office-Hosting', '')
    if not hmac.compare_digest(token, hosting.csrf) or (
            handler.command == 'POST' and handler.headers.get('Origin') != 'http://' + host):
        return handler._send('{"error":"Reload the local hosting page and try again."}', 403, 'application/json', public=True)
    if handler.command == 'GET' and handler.path == '/hosting/status':
        return handler._send(json.dumps(hosting.view()), ctype='application/json', public=True)
    if handler.command != 'POST':
        return handler._send('Not found', 404, 'text/plain')
    size = int(handler.headers.get('Content-Length', '0'))
    if not 0 < size <= 2048 or handler.headers.get_content_type() != 'application/json':
        raise ValueError('Reload this page and try again.')
    data = handler._request_json(handler.rfile.read(size))
    if handler.path == '/hosting/login':
        result = hosting.login()
    elif handler.path == '/hosting/review':
        result = hosting.review()
    elif handler.path == '/hosting/sync':
        action = data.get('action')
        if action == 'enable':
            work = lambda: sync.enrollment(hosting.folder)
        elif action == 'pause':
            work = lambda: sync.pause(hosting.folder)
        elif action == 'resolve':
            work = lambda: sync.tick(hosting.folder, data.get('choice'), data.get('review'))
        elif action == 'now':
            work = lambda: sync.tick(hosting.folder)
        else:
            raise ValueError('Choose a sync action.')
        result = hosting.launch('syncing', work)
    elif handler.path == '/hosting/upload':
        result = hosting.upload(data.get('preview'), data.get('replace', False))
    else:
        return handler._send('Not found', 404, 'text/plain')
    return handler._send(json.dumps(result), 202, 'application/json', public=True)
