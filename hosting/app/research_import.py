"""Granular, owner-scoped research import into the latest office revision."""
from pathlib import Path
import tempfile

from .auth import AuthFailure
from .jobs import writable
from .workspace import materialize, capture, publish
from officekit.runtime import hosted_office
from officekit_research.pack_transfer import install


def import_pack(offices, uid, oid, bundle, expected, proposal_id=None):
    receipt, record = offices.read(uid, oid)
    writable(receipt)
    if expected != receipt['digest']:
        raise AuthFailure('The office changed. Reload before uploading research.', 409)
    if record.get('onboarding'):
        raise AuthFailure('Build your office before importing research.')
    with tempfile.TemporaryDirectory(prefix='wp-research-') as directory:
        folder = Path(directory).resolve()
        materialize(folder, record)
        with hosted_office(folder, {}, research_library=getattr(offices, 'research_library', None)):
            try:
                result = install(folder, bundle, proposal_id)
                updated = capture(folder, oid)
            except ValueError as error:
                raise AuthFailure(str(error), 400) from None
        if updated != record:
            receipt = publish(offices, uid, receipt, updated)
    return {**result, 'office_id': oid, 'revision': receipt['digest'],
            'href': receipt['path'] + result['href'],
            'proposal_href': receipt['path'] + result['proposal_href'] if result['proposal_href'] else None}
