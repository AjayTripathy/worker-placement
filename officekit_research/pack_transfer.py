"""Portable transport for existing strategy packs, private to the receiving office.

An import is an attributed research lead, never a court, verified evidence,
forecast or public-exchange admission. Immutable versions retain their decks.
"""
from datetime import date
import json
from pathlib import Path
import re
import tempfile

from officekit.migration import canonical, digest, inspect_document, parse_json
from officekit.office_lock import locked
from officekit.strategy_packs import validate as validate_manifest

SCHEMA = 'strategy_pack_transfer_v1'
MAX_BYTES = 512 * 1024
FIELDS = {'id', 'name', 'bucket', 'thesis', 'author', 'deck', 'edge', 'as_of',
          'positions', 'goal_kinds', 'betas', 'agent', 'model', 'intelligence_level',
          'sources', 'gaps', 'deck_sha256'}


def validate(bundle):
    try:
        return _validate(bundle)
    except (TypeError, KeyError, AttributeError, OverflowError):
        raise ValueError('Malformed research pack.') from None


def _validate(bundle):
    if not isinstance(bundle, dict) or set(bundle) != {'schema', 'id', 'manifest', 'deck'} or bundle['schema'] != SCHEMA:
        raise ValueError('Choose a strategy pack exported with research-export.')
    raw = canonical(bundle)
    if len(raw) > MAX_BYTES:
        raise ValueError('Research pack exceeds 512 KiB.')
    inspect_document('research-pack.json', raw)
    body = {k: v for k, v in bundle.items() if k != 'id'}
    if bundle['id'] != digest(canonical(body)):
        raise ValueError('Research pack digest mismatch.')
    m, deck = bundle['manifest'], bundle['deck']
    if not isinstance(m, dict) or set(m) - FIELDS or validate_manifest(m):
        raise ValueError('Invalid strategy pack manifest or unsupported fields.')
    if not isinstance(deck, str) or not deck.strip() or m.get('deck') != 'DECK.md' or m.get('deck_sha256') != digest(deck.encode()):
        raise ValueError('Research deck does not match its manifest.')
    try:
        as_of = date.fromisoformat(m.get('as_of', ''))
    except (ValueError, TypeError):
        raise ValueError('Research needs an as-of date.') from None
    if as_of > date.today():
        raise ValueError('Research cannot be dated in the future.')
    symbols = m.get('positions')
    if not isinstance(symbols, list) or not 1 <= len(symbols) <= 30 or any(not re.fullmatch(r'[A-Z0-9][A-Z0-9.^-]{0,14}', s) for s in symbols):
        raise ValueError('Research needs 1–30 valid symbols.')
    for field in ('name', 'author', 'agent', 'model', 'intelligence_level'):
        if not isinstance(m.get(field), str) or not 1 <= len(m[field]) <= 200:
            raise ValueError('Research needs bounded author, agent, model and intelligence-level attribution; use unknown when unrecorded.')
    if len(m['thesis']) > 1400:
        raise ValueError('Keep the research summary within 1,400 characters.')
    gaps = m.get('gaps')
    if not isinstance(gaps, list) or len(gaps) > 20 or any(not isinstance(g, str) or len(g) > 1000 for g in gaps):
        raise ValueError('List the unresolved research gaps.')
    sources = m.get('sources')
    if not isinstance(sources, list) or not 1 <= len(sources) <= 20:
        raise ValueError('Research needs 1–20 source references.')
    from officekit_research.cases import safe_url, day
    for source in sources:
        if not isinstance(source, dict) or set(source) != {'title', 'url', 'retrieved_at'}:
            raise ValueError('Invalid research source reference.')
        if not isinstance(source['title'], str) or not 1 <= len(source['title']) <= 300:
            raise ValueError('Invalid research source title.')
        safe_url(source['url'])
        if day(source['retrieved_at']) > date.today():
            raise ValueError('A source retrieval date cannot be in the future.')
    if 'goal_kinds' in m and (not isinstance(m['goal_kinds'], list) or any(not isinstance(g, str) for g in m['goal_kinds'])):
        raise ValueError('Goal kinds must be a list of names.')
    if 'betas' in m:
        import math
        if not isinstance(m['betas'], dict) or any(type(v) not in {int, float} or not math.isfinite(v) for v in m['betas'].values()):
            raise ValueError('Factor betas must be finite numbers.')
    return bundle


def export(pack):
    pack = Path(pack)
    if pack.is_symlink() or (pack / 'pack.json').is_symlink() or (pack / 'DECK.md').is_symlink():
        raise ValueError('Research files must not be symlinks.')
    if (pack / 'pack.json').stat().st_size + (pack / 'DECK.md').stat().st_size > MAX_BYTES:
        raise ValueError('Research pack exceeds 512 KiB.')
    m = parse_json((pack / 'pack.json').read_bytes())
    if not isinstance(m, dict) or m.get('deck', 'DECK.md') != 'DECK.md':
        raise ValueError('Portable packs use DECK.md.')
    deck = (pack / 'DECK.md').read_text(encoding='utf-8')
    body = {'schema': SCHEMA, 'manifest': {**m, 'deck': 'DECK.md', 'deck_sha256': digest(deck.encode())}, 'deck': deck}
    return validate({'id': digest(canonical(body)), **body})


def roots(folder):
    base = Path(folder) / 'research' / 'strategy_packs'
    return [p for p in sorted(base.glob('*')) if re.fullmatch('[a-f0-9]{64}', p.name) and p.is_dir() and not p.is_symlink()]


def install(folder, bundle, proposal_id=None):
    from officekit.strategy_proposals import load
    from officekit_research.discovery import refresh_proposal_inventory, reference_key, manifest_digest
    validate(bundle)
    with locked(folder):
        if proposal_id:
            try:
                p = load(folder, proposal_id)
            except (ValueError, FileNotFoundError, TypeError, AttributeError):
                raise ValueError('Choose a saved proposal in this office.') from None
            if p.get('research') or p['status'] not in {'error', 'awaiting_key'}:
                raise ValueError('Attach to an unfinished, idle proposal, or create a fresh revision for completed research.')
        base = Path(folder) / 'research' / 'strategy_packs'
        if any(p.is_symlink() for p in (Path(folder), Path(folder) / 'research', base)):
            raise ValueError('Research directories must not be symlinks.')
        base.mkdir(parents=True, exist_ok=True)
        destination = base / bundle['id']
        if destination.is_symlink():
            raise ValueError('Research directories must not be symlinks.')
        if destination.exists():
            existing = export(destination / bundle['manifest']['id'])
            if existing != bundle:
                raise ValueError('The saved research version failed its integrity check.')
        else:
            if len(roots(folder)) >= 200:
                raise ValueError('This office has reached its imported strategy pack limit.')
            # Publish the two files together; interrupted writes remain hidden.
            with tempfile.TemporaryDirectory(prefix='.import-', dir=base) as temporary:
                root = Path(temporary) / bundle['id']
                pack = root / bundle['manifest']['id']
                pack.mkdir(parents=True)
                (pack / 'pack.json').write_bytes(canonical(bundle['manifest']))
                (pack / 'DECK.md').write_text(bundle['deck'], encoding='utf-8')
                root.rename(destination)
        if proposal_id:
            refresh_proposal_inventory(folder, p)
        key = reference_key('strategy_pack', bundle['manifest']['id'], manifest_digest(bundle['manifest']))
        return {'id': bundle['id'], 'href': '/pages/research_' + key + '.html',
                'proposal_href': '/pages/proposal_' + p['id'] + '.html' if proposal_id else None,
                'status': 'imported', 'review_status': 'research_lead'}
