"""Private court lineage and explicitly registered forecasts carried by packs.

Historical verdicts remain attributed source claims, never live approvals.
Conviction ratings and legacy rows without a forecast contract are not scored.
"""
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from officekit.migration import canonical, digest
from officekit.office_lock import locked

MAX_PDF = 4 * 1024 * 1024
HASH = re.compile('[a-f0-9]{64}')


def validate_metadata(m):
    c = m.get('private_court')
    if c is not None:
        fields = {'revision', 'supersedes', 'source_digest', 'source_deck', 'ruling',
                  'reopen_gates', 'conviction', 'court', 'ledger_state', 'sleeve', 'provenance'}
        if not isinstance(c, dict) or set(c) != fields:
            raise ValueError('Invalid private court metadata.')
        if type(c['revision']) is not int or not 1 <= c['revision'] <= 100000:
            raise ValueError('Invalid private court revision.')
        if not HASH.fullmatch(str(c['source_digest'])) or (c['supersedes'] is not None and not HASH.fullmatch(str(c['supersedes']))):
            raise ValueError('Invalid private court lineage.')
        if (c['revision'] == 1) != (c['supersedes'] is None):
            raise ValueError('A revised court pack must retain its predecessor.')
        for k in ('source_deck', 'ruling', 'court', 'ledger_state', 'sleeve'):
            if not isinstance(c[k], str) or len(c[k]) > 2000:
                raise ValueError('Invalid private court text.')
        if not isinstance(c['reopen_gates'], list) or len(c['reopen_gates']) > 30 or any(not isinstance(g, str) or len(g) > 2000 for g in c['reopen_gates']):
            raise ValueError('Invalid reopen gates.')
        if c['conviction'] is not None and (type(c['conviction']) not in (int, float) or not 0 <= c['conviction'] <= 10):
            raise ValueError('Invalid conviction rating.')
        if not isinstance(c['provenance'], dict) or len(canonical(c['provenance'])) > 30000:
            raise ValueError('Invalid recorded run provenance.')
        if not m['sources'] and not any('source' in g.lower() for g in m['gaps']):
            raise ValueError('Missing structured source references must be disclosed.')
    a = m.get('attachment')
    if a is not None and (not isinstance(a, dict) or set(a) != {'sha256', 'size', 'name'} or
                          a['name'] != 'DECK.pdf' or not HASH.fullmatch(str(a['sha256'])) or
                          type(a['size']) is not int or not 1 <= a['size'] <= MAX_PDF):
        raise ValueError('Invalid PDF companion metadata.')
    from officekit_research.predictions import validate
    forecasts, outcomes = m.get('forecasts', []), m.get('outcomes', [])
    if not isinstance(forecasts, list) or len(forecasts) > 100 or not isinstance(outcomes, list) or len(outcomes) > 100:
        raise ValueError('Too many forecast records in one pack.')
    ids = {validate(r)['id'] + ':0' for r in forecasts}
    if len(ids) != len(forecasts):
        raise ValueError('Duplicate forecasts in research pack.')
    resolved = set()
    from officekit_research.cases import safe_url
    for r in outcomes:
        if not isinstance(r, dict) or set(r) != {'forecast_id', 'outcome', 'source_url', 'resolved_at', 'note'} or r['forecast_id'] not in ids or type(r['outcome']) is not bool:
            raise ValueError('Outcomes must resolve an explicit forecast in this pack.')
        if r['forecast_id'] in resolved:
            raise ValueError('A research pack may resolve each forecast only once.')
        resolved.add(r['forecast_id'])
        safe_url(r['source_url'])
        when = datetime.fromisoformat(r['resolved_at'])
        prediction = next(p for p in forecasts if p['id'] + ':0' == r['forecast_id'])
        if when.tzinfo is None or when > datetime.now(timezone.utc) or when < datetime.fromisoformat(prediction['recorded_at']):
            raise ValueError('Outcome timestamp must follow forecast capture.')
        if not isinstance(r['note'], str) or len(r['note']) > 600:
            raise ValueError('Invalid outcome note.')
        if prediction.get('scenario') and not r['outcome'] and when.date().isoformat() < prediction['resolve_by']:
            raise ValueError('Wait for the event deadline before resolving false.')


def pdf_bytes(encoded, attachment):
    try:
        if not isinstance(encoded, str) or len(encoded) > (MAX_PDF + 2) * 4 // 3:
            raise ValueError()
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) != attachment['size'] or digest(raw) != attachment['sha256'] or not raw.startswith(b'%PDF-'):
            raise ValueError()
        return raw
    except (ValueError, TypeError):
        raise ValueError('PDF companion failed its size, format or digest check.') from None


def import_forecasts(folder, bundle, dry_run=False):
    """Retain original capture/identity; outcome known-time starts at import."""
    from officekit_research import predictions, index
    rows = bundle['manifest'].get('forecasts', [])
    if not rows:
        return
    with locked(folder):
        existing = predictions.load(folder)
        by_id = {r['id']: r for r in existing}
        new = [r for r in rows if r['id'] not in by_id]
        if len({r['id'] for r in new}) != len(new):
            raise ValueError('Duplicate forecasts in research pack.')
        predictions._validate_history(existing + new)
        prior = index.load_outcomes(folder)
        if any(p.get('supersedes', '') + ':0' in prior for p in new):
            raise ValueError('A resolved event cannot receive another forecast.')
        for row in bundle['manifest'].get('outcomes', []):
            old = prior.get(row['forecast_id'])
            if old and any(old.get(k) != v for k, v in row.items()):
                raise ValueError('An imported outcome conflicts with a saved resolution; review the correction explicitly.')
        if dry_run:
            return
        attrs = Path(folder) / 'research' / 'prediction_imports.json'
        provenance = json.loads(attrs.read_text()) if attrs.exists() else {}
        when = datetime.now(timezone.utc).isoformat()
        for r in new:
            provenance[r['id']] = {'bundle_id': bundle['id'], 'imported_at': when, 'attribution': 'claimed_import'}
        if new:
            predictions.path(folder).parent.mkdir(parents=True, exist_ok=True)
            with predictions.path(folder).open('a', encoding='utf-8') as f:
                f.write(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in new))
            temporary = attrs.with_suffix('.tmp')
            temporary.write_bytes(canonical(provenance))
            temporary.replace(attrs)
        for row in bundle['manifest'].get('outcomes', []):
            old = prior.get(row['forecast_id'])
            if old and all(old.get(k) == v for k, v in row.items()):
                continue
            if old:
                raise ValueError('An imported outcome conflicts with a saved resolution; review the correction explicitly.')
            index.resolve(folder, **row)


def latest(packs):
    """Select the highest retained court revision; ordinary packs stay separate."""
    selected, other = {}, []
    for p in packs:
        if 'private_court' not in p:
            other.append(p)
            continue
        key = (p['author'], p['id'])
        previous = selected.get(key)
        if previous is None or p['private_court']['revision'] > previous['private_court']['revision']:
            selected[key] = p
    # Once migrated, do not rediscover the old mutable desk copy.
    other = [p for p in other if (p['author'], p['id']) not in selected]
    return other + list(selected.values())
