"""Tenant-scoped encrypted immutable content, separate from the office snapshot."""
import base64
from officekit.migration import digest
from officekit_research.private_packs import HASH
from .auth import AuthFailure
from .store import Conflict


class PrivateResearch:
    def __init__(self, offices, uid, oid):
        self.offices = offices
        self.prefix = offices.prefix(uid, oid) + 'research-content/'

    def put(self, key, value):
        try:
            self.offices.db().put(self.prefix + key, value)
        except Conflict:
            existing, _ = self.offices.db().get(self.prefix + key)
            if existing != value:
                raise AuthFailure('Stored research failed its integrity check.', 409) from None

    def bundle(self, bid):
        if not HASH.fullmatch(str(bid)):
            raise AuthFailure('Research not found.', 404)
        value, _ = self.offices.db().get(self.prefix + 'bundles/' + bid)
        if value is None:
            raise AuthFailure('Research content is unavailable; retry its upload.', 404)
        return value

    def pdf(self, sha):
        if not HASH.fullmatch(str(sha)):
            raise AuthFailure('Research file not found.', 404)
        value, _ = self.offices.db().get(self.prefix + 'files/' + sha)
        if value is None:
            raise AuthFailure('Research PDF is unavailable; retry its upload.', 404)
        raw = base64.b64decode(value['data'], validate=True)
        if digest(raw) != sha:
            raise AuthFailure('Research PDF failed its integrity check.', 409)
        return raw


def import_batch(offices, uid, oid, bundles, files, expected):
    from pathlib import Path
    import tempfile
    from .workspace import materialize, capture, publish
    from .jobs import writable
    from officekit_research.pack_transfer import validate
    from officekit_research.private_packs import pdf_bytes, import_forecasts
    from officekit_research import pack_directory
    from officekit_research.discovery import reference_key, manifest_digest
    receipt, record = offices.read(uid, oid)
    writable(receipt)
    if receipt['digest'] != expected:
        raise AuthFailure('The office changed. Retry against its current revision.', 409)
    if record.get('onboarding'):
        raise AuthFailure('Build your office before importing research.')
    if not isinstance(bundles, list) or not 1 <= len(bundles) <= 25 or not isinstance(files, dict):
        raise AuthFailure('Upload 1–25 research versions per batch.')
    service = PrivateResearch(offices, uid, oid)
    try:
        for b in bundles:
            validate(b)
        attachments = {b['manifest']['attachment']['sha256']: b['manifest']['attachment'] for b in bundles if b['manifest'].get('attachment')}
        if set(files) - set(attachments):
            raise ValueError('Unreferenced research files cannot be uploaded.')
        for sha, a in attachments.items():
            raw = pdf_bytes(files[sha], a) if sha in files else service.pdf(sha)
            if len(raw) != a['size']:
                raise ValueError('PDF size does not match its research directory.')
        # Work on a disposable revision: any invalid row rejects the whole batch.
        with tempfile.TemporaryDirectory(prefix='wp-research-directory-') as temp:
            folder = Path(temp).resolve()
            materialize(folder, record)
            for b in bundles:
                pack_directory.add(folder, b)
                import_forecasts(folder, b)
            updated = capture(folder, oid)
            for sha, encoded in files.items():
                service.put('files/' + sha, {'data': encoded})
            for b in bundles:
                service.put('bundles/' + b['id'], b)
            if updated != record:
                receipt = publish(offices, uid, receipt, updated)
    except (ValueError, TypeError, KeyError) as e:
        raise AuthFailure(str(e), 400) from None
    return {'office_id': oid, 'revision': receipt['digest'], 'status': 'imported',
            'packs': [{'id': b['id'], 'href': receipt['path'] + '/pages/research_' + reference_key('strategy_pack', b['manifest']['id'], manifest_digest(b['manifest'])) + '.html'} for b in bundles]}
