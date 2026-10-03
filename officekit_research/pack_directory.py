"""Small office-owned directory; research content is fetched only when selected."""
import json
from pathlib import Path

from officekit.migration import canonical


def path(folder):
    return Path(folder) / 'research' / 'pack_directory.json'


def read(folder):
    p = path(folder)
    if p.is_symlink() or p.parent.is_symlink():
        raise ValueError('Research directory cannot be a symbolic link.')
    from officekit_research.pack_transfer import validate_descriptor, MAX_PACKS
    from officekit_research.private_packs import HASH
    value = json.loads(p.read_text()) if p.exists() else {}
    if not isinstance(value, dict) or len(value) > MAX_PACKS:
        raise ValueError('Invalid research directory.')
    try:
        for bid, manifest in value.items():
            if not HASH.fullmatch(bid):
                raise ValueError('Invalid research version ID.')
            validate_descriptor(manifest)
    except (TypeError, KeyError, AttributeError):
        raise ValueError('Malformed research directory.') from None
    return value


def add(folder, bundle):
    from officekit_research.pack_transfer import MAX_PACKS
    directory = read(folder)
    bid, m = bundle['id'], bundle['manifest']
    if bid in directory:
        if directory[bid] != m:
            raise ValueError('Research directory integrity mismatch.')
        return
    if len(directory) >= MAX_PACKS:
        raise ValueError('This office has reached its research directory limit.')
    c = m.get('private_court')
    if c and c['revision'] == 1 and any((p['id'], p['author']) == (m['id'], m['author']) and 'private_court' in p for p in directory.values()):
        raise ValueError('A revised court must name its preceding version.')
    if c and c['supersedes']:
        old = directory.get(c['supersedes'])
        if not old or (old['id'], old['author']) != (m['id'], m['author']) or old['private_court']['revision'] + 1 != c['revision']:
            raise ValueError('Upload the preceding court revision first.')
        if any(p.get('private_court', {}).get('supersedes') == c['supersedes'] for p in directory.values()):
            raise ValueError('Conflicting court revisions require explicit reconciliation.')
    directory[bid] = m
    p = path(folder)
    p.parent.mkdir(parents=True, exist_ok=True)
    temp = p.with_suffix('.tmp')
    temp.write_bytes(canonical(directory))
    temp.replace(p)


def packs(folder):
    return [{**m, 'bundle_id': bid} for bid, m in read(folder).items()]


def bundle(folder, bid):
    from officekit.runtime import private_research
    from officekit_research.pack_transfer import validate
    from officekit_research.private_packs import HASH
    if not HASH.fullmatch(str(bid)) or bid not in read(folder):
        raise ValueError('Research version is not in this office directory.')
    provider = private_research()
    if provider:
        value = provider.bundle(bid)
    else:
        p = Path(folder) / '.research-content' / (bid + '.json')
        if not p.is_file() or p.is_symlink():
            raise ValueError('Research content is not cached locally. Open the linked hosted office or download its research archive.')
        value = json.loads(p.read_text())
    validate(value)
    if value['id'] != bid or value['manifest'] != read(folder)[bid]:
        raise ValueError('Research content does not match the office directory.')
    return value


def deck(folder, pack):
    if pack.get('bundle_id'):
        return bundle(folder, pack['bundle_id'])['deck']
    return Path(pack['deck_path']).read_text(encoding='utf-8')


def all_packs(folder):
    from officekit.strategy_packs import load_packs
    from officekit_research.pack_transfer import roots
    retained = packs(folder)
    superseded = {(m['author'], m['id']) for m in retained if 'private_court' in m}
    local, problems = load_packs([Path(folder) / 'strategies', *roots(folder)], superseded=superseded)
    return local + retained, problems


def cache(folder, value, pdf=None):
    """Private local original plus an atomic directory update, with no publication."""
    from officekit.office_lock import locked
    from officekit.cloud import save_private
    from officekit_research.pack_transfer import validate
    from officekit_research.private_packs import import_forecasts, pdf_bytes
    import base64
    validate(value)
    with locked(folder):
        import_forecasts(folder, value, dry_run=True)
        base = Path(folder) / '.research-content'
        if base.is_symlink():
            raise ValueError('Research cache cannot be a symbolic link.')
        if pdf is not None:
            pdf_bytes(base64.b64encode(pdf).decode(), value['manifest']['attachment'])
            base.mkdir(parents=True, exist_ok=True, mode=0o700)
            target = base / (value['manifest']['attachment']['sha256'] + '.pdf')
            if target.is_symlink():
                raise ValueError('Research file cannot be a symbolic link.')
            temp = target.with_suffix('.tmp')
            temp.write_bytes(pdf)
            temp.replace(target)
        save_private(base / (value['id'] + '.json'), value)
        add(folder, value)
        import_forecasts(folder, value)


def upload(folder, office_id, progress=None):
    """Resume by immutable ID; each batch merges into the current hosted office."""
    import base64
    from officekit import cloud
    auth = cloud.credentials()
    prefix = '/api/offices/' + office_id + '/research/'
    call = lambda route, body=None: cloud.request(auth['origin'], prefix + route, body, auth['token'])
    remote = call('directory')
    if remote.get('office_id') != office_id:
        raise ValueError('Hosted research destination mismatch.')
    local = read(folder)
    pending = sorted(set(local) - set(remote['ids']), key=lambda bid: (local[bid].get('private_court', {}).get('revision', 0), bid))
    sent, receipts = 0, []
    while pending:
        ids, bundles, files, size = [], [], {}, 0
        for bid in pending[:25]:
            b = bundle(folder, bid)
            a = b['manifest'].get('attachment')
            raw = (Path(folder) / '.research-content' / (a['sha256'] + '.pdf')).read_bytes() if a else None
            extra = len(canonical(b)) + (len(raw) * 4 // 3 + 4 if raw else 0)
            if ids and size + extra > 8 * 1024 * 1024:
                break
            ids.append(bid); bundles.append(b); size += extra
            if a:
                files[a['sha256']] = base64.b64encode(raw).decode()
        # Read the current revision immediately before each additive commit.
        revision = cloud.request(auth['origin'], '/api/offices/' + office_id + '/revision', token=auth['token'])
        result = call('batch', {'revision': revision['digest'], 'bundles': bundles, 'files': files})
        if result.get('office_id') != office_id or {p['id'] for p in result.get('packs', [])} != set(ids):
            raise ValueError('Hosted research receipt does not match the uploaded batch.')
        pending = pending[len(ids):]
        sent += len(ids)
        receipts += result['packs']
        if progress:
            progress(sent, sent + len(pending))
    verified = call('directory')
    if not set(local) <= set(verified['ids']):
        raise ValueError('Hosted research directory is missing uploaded versions; rerun to resume.')
    result = {'office_id': office_id, 'uploaded': sent, 'retained_versions': len(local), 'revision': verified['revision'], 'receipts': receipts}
    cloud.save_private(Path(folder) / '.research-upload-receipt.json', result)
    return result
