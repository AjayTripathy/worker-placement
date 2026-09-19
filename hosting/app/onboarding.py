"""Persist the shared app's unfinished office without inventing a balance sheet."""
import base64
import json
import uuid

from officekit.migration import MAX_FILES, MAX_TOTAL, canonical, digest, inspect_document, safe_path
from .auth import AuthFailure
from .offices import stamp, tenant
from .store import Conflict


def validate(record):
    documents = record['documents']
    if not 1 <= len(documents) <= MAX_FILES or 'balance_sheet.json' in documents:
        raise ValueError('Invalid onboarding documents')
    decoded = {}
    for name, encoded in documents.items():
        if not safe_path(name):
            raise ValueError('Unsupported onboarding document')
        raw = base64.b64decode(encoded, validate=True)
        inspect_document(name, raw)
        decoded[name] = raw
    if sum(map(len, decoded.values())) > MAX_TOTAL:
        raise ValueError('Office exceeds the workspace size limit')
    answers = json.loads(decoded['answers.json'])
    if answers != {'office_id': str(uuid.UUID(record['office_id']))}:
        raise ValueError('Invalid onboarding identity')
    return decoded


def capture(folder, oid):
    folder = folder.resolve()
    documents = {}
    for path in sorted(folder.rglob('*')):
        name = path.relative_to(folder).as_posix()
        if not safe_path(name) or not path.is_file():
            continue
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != folder.parent):
            raise ValueError('Symlinks cannot be saved')
        if path.stat().st_size > MAX_TOTAL:
            raise ValueError('Office exceeds the workspace size limit')
        documents[name] = base64.b64encode(path.read_bytes()).decode()
    record = {'onboarding': True, 'office_id': oid, 'documents': documents, 'workspace': {}}
    validate(record)
    return record


def start(offices, uid):
    """Resume one unfinished office per account; POST + CAS makes retries safe."""
    key = 'onboarding/' + tenant(uid)
    for _ in range(3):
        pending, generation = offices.db().get(key)
        if pending:
            active, _ = offices.db().get(offices.prefix(uid, pending['office_id']) + 'active')
            if active and active['status'] == 'onboarding':
                return active
            if active is None:
                oid = pending['office_id']
                break
        oid = str(uuid.uuid4())
        try:
            offices.db().put(key, {'office_id': oid}, generation)
            break
        except Conflict:
            continue
    else:
        raise AuthFailure('Another tab is opening your office. Try again.', 409)
    record = {'onboarding': True, 'office_id': oid, 'documents': {
        'answers.json': base64.b64encode(canonical({'office_id': oid})).decode()}, 'workspace': {}}
    revision = digest(canonical(record))
    prefix = offices.prefix(uid, oid)
    receipt = {'status': 'onboarding', 'office_id': oid, 'digest': revision, 'activated_at': stamp(),
               'path': '/app/offices/' + oid, 'name': 'Your new office', 'as_of': '', 'documents': 1}
    try:
        offices.db().put(prefix + 'revisions/' + revision, record)
    except Conflict:
        pass
    try:
        offices.db().put(prefix + 'active', receipt)
    except Conflict:
        receipt, _ = offices.read(uid, oid)
    return receipt
