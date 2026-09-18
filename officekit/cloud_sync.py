"""Opt-in, conflict-safe synchronization of saved office data (never keys).

The common base is a map of file digests. One-sided edits and deletions travel
as a snapshot. If both copies change, a reviewed choice is required. Local writes
use the same office lock as editors; a recovery journal survives process death.
"""
import base64
import json
import os
import re
from pathlib import Path
import time

from officekit import cloud
from officekit.migration import snapshot, digest, canonical, validate_documents, safe_path, inspect_document
from officekit.office_lock import locked

STATE = '.office-sync.json'
JOURNAL = '.office-sync-transaction'


def local(folder):
    manifest, chunks = snapshot(folder)
    docs = {f['path']: b''.join(chunks[h] for h in f['chunks']) for f in manifest['files']}
    return manifest, chunks, docs


def hashes(docs):
    return {name: digest(data) for name, data in docs.items()}


def read(folder):
    path = Path(folder) / STATE
    return json.loads(path.read_text()) if path.exists() else {'enabled': False, 'status': 'off'}


def write(folder, value):
    cloud.save_private(Path(folder) / STATE, value)


def remote(auth, oid):
    result = cloud.request(auth['origin'], '/api/offices/' + oid + '/snapshot', token=auth['token'])
    receipt, record = result['receipt'], result['record']
    cloud.receipt_url(auth['origin'], receipt)
    if receipt['office_id'] != oid:
        raise ValueError('The downloaded office identity did not match.')
    docs = {name: base64.b64decode(raw, validate=True) for name, raw in record['documents'].items()}
    validate_documents(record['manifest'], docs)
    # Older hosted revisions stored previews/history in a separate allowlist.
    from officekit.migration import MAX_TOTAL
    for name, raw in record.get('workspace', {}).items():
        if name == 'api_errors.json':
            continue  # Delivery errors are local to each runtime, not office facts.
        if not safe_path(name):
            raise ValueError('Unsupported document in hosted snapshot.')
        data = base64.b64decode(raw, validate=True)
        inspect_document(name, data)
        if name in docs and docs[name] != data:
            raise ValueError('Hosted snapshot has conflicting document versions.')
        docs[name] = data
    if sum(map(len, docs.values())) > MAX_TOTAL:
        raise ValueError('Hosted office exceeds the sync size limit.')
    return receipt, docs


def target(folder, name):
    if not safe_path(name):
        raise ValueError('Unsupported sync document.')
    root = Path(folder).resolve()
    result = root / name
    if any(p.is_symlink() for p in [result, *result.parents] if p != root.parent):
        raise ValueError('Sync refuses symbolic links.')
    return result


def restore(folder, docs, previous_names):
    for name in sorted(set(docs) | set(previous_names)):
        path = target(folder, name)
        if name not in docs:
            path.unlink(missing_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_name('.sync-' + path.name)
            if temp.is_symlink():
                raise ValueError('Sync refuses symbolic links.')
            with temp.open('wb') as f:
                f.write(docs[name]);f.flush();os.fsync(f.fileno())
            os.replace(temp, path)


def pages(folder):
    directory = Path(folder) / 'pages'
    if directory.is_symlink():
        raise ValueError('Sync refuses symbolic links.')
    return {p.name: base64.b64encode(p.read_bytes()).decode() for p in directory.glob('*.html')
            if p.is_file() and not p.is_symlink() and re.fullmatch(r'[A-Za-z0-9_.-]+\.html', p.name)}


def restore_pages(folder, saved):
    directory = Path(folder) / 'pages'
    if directory.is_symlink():
        raise ValueError('Sync refuses symbolic links.')
    directory.mkdir(exist_ok=True)
    for name in set(pages(folder)) | set(saved):
        if not re.fullmatch(r'[A-Za-z0-9_.-]+\.html', name):
            raise ValueError('Invalid generated page in recovery journal.')
        path = directory / name
        if path.is_symlink():
            raise ValueError('Sync refuses symbolic links.')
        if name in saved:
            path.write_bytes(base64.b64decode(saved[name], validate=True))
        else:
            path.unlink(missing_ok=True)


def recover(folder):
    transaction = Path(folder) / JOURNAL
    if not transaction.exists():
        return
    journal = json.loads(transaction.read_text())
    old = {name: base64.b64decode(raw, validate=True) for name, raw in journal['before'].items()}
    restore(folder, old, journal['after_names'])
    restore_pages(folder, journal.get('pages', {}))
    transaction.unlink()


def apply(folder, before, after):
    """Caller holds the office lock. Keep a recoverable, private backup."""
    for name in set(before) | set(after):
        target(folder, name)
    transaction = Path(folder) / JOURNAL
    cloud.save_private(transaction, {'before': {n: base64.b64encode(v).decode() for n, v in before.items()},
                                     'after_names': list(after), 'pages': pages(folder)})
    try:
        restore(folder, after, before)
        # Render only; do not re-import, infer fresh balances or call agents.
        from officekit.serve import render_saved_office
        render_saved_office(folder)
        backups = Path(folder) / '.sync-backups'
        backups.mkdir(exist_ok=True, mode=0o700)
        os.replace(transaction, backups / (str(time.time_ns()) + '.json'))
        for stale in sorted(backups.glob('*.json'))[:-5]:
            stale.unlink()
    except BaseException:
        recover(folder)
        raise


def enrollment(folder):
    """Enable only after explicitly reviewing or migrating this office."""
    auth = cloud.credentials()
    who = cloud.request(auth['origin'], '/api/me', token=auth['token'])
    with locked(folder):
        recover(folder)
        manifest, _, docs = local(folder)
        receipt, other = remote(auth, manifest['office_id'])
        state = dict(enabled=True, origin=auth['origin'], email=who['email'], office_id=manifest['office_id'],
                     base=hashes(docs) if hashes(docs) == hashes(other) else None,
                     revision=receipt['digest'], status='ready', last_sync=None)
        write(folder, state)
    return tick(folder)


def tick(folder, choice=None, review=None):
    with locked(folder):
        recover(folder)
        state = read(folder)
        if not state.get('enabled'):
            return state
        auth = cloud.credentials()
        if auth['origin'] != state['origin'] or auth['email'] != state['email']:
            raise ValueError('The signed-in account changed. Pause sync and reconnect this office explicitly.')
        manifest, chunks, docs = local(folder)
        if manifest['office_id'] != state['office_id']:
            raise ValueError('The local office identity changed. Pause sync and reconnect explicitly.')
        receipt = cloud.request(auth['origin'], '/api/offices/' + manifest['office_id'] + '/revision', token=auth['token'])
        cloud.receipt_url(auth['origin'], receipt)
        if receipt.get('office_id') != manifest['office_id']:
            raise ValueError('The hosted office identity did not match.')
        base = state.get('base')
        if base is not None and receipt['digest'] == state.get('revision'):
            other, rh = None, base
        else:
            receipt, other = remote(auth, manifest['office_id'])
            rh = hashes(other)
        lh = hashes(docs)
        fingerprint = digest(canonical([lh, rh, receipt['digest']]))
        if choice and (choice not in {'local', 'hosted'} or review != fingerprint):
            raise ValueError('One of the copies changed after this review. Refresh the conflict before choosing.')
        if (receipt.get('job') or {}).get('expires', 0) > time.time():
            state.update(status='waiting', message='Hosted background work is running; sync will resume afterward.')
        elif lh == rh:
            state.update(base=lh, revision=receipt['digest'], status='synced', last_sync=time.time())
        elif choice == 'local' or (base is not None and rh == base):
            receipt = cloud.upload_snapshot(manifest, chunks, auth, receipt['digest'])
            state.update(base=lh, revision=receipt['digest'], status='synced', last_sync=time.time())
        elif choice == 'hosted' or (base is not None and lh == base):
            apply(folder, docs, other)
            state.update(base=rh, revision=receipt['digest'], status='synced', last_sync=time.time())
        else:
            changed = sorted(n for n in set(lh) | set(rh) if lh.get(n) != rh.get(n))
            state.update(status='conflict', review=fingerprint, files=changed,
                         message='Both copies differ. Review them and choose which saved copy to keep. Neither copy has been replaced.')
        if state['status'] == 'synced':
            for key in ('message', 'review', 'files', 'error'):
                state.pop(key, None)
            cloud.save_private(Path(folder) / '.hosted-receipt.json', receipt)
        write(folder, state)
        return state


def pause(folder):
    with locked(folder):
        state = read(folder);state.update(enabled=False, status='paused');write(folder, state)
    return state


def safe_tick(folder):
    try:
        return tick(folder)
    except Exception as error:
        from officekit.api_errors import classify, log_exception
        log_exception(error, 'office-sync')
        with locked(folder):
            state = read(folder)
            state.update(status='error', message=classify(error)[1])
            write(folder, state)
        return state


def loop(folder):
    while True:
        if read(folder).get('enabled'):
            safe_tick(folder)
        time.sleep(30)
