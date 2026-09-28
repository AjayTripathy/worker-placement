"""Private, immutable binary predictions; general courts use their sealed forecasts.

Attribution here is an office assertion, not a verified public identity. Nothing
in this ledger is automatically contributed to the public research exchange.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from officekit.office_lock import locked
from officekit.migration import canonical, parse_json
from officekit_research.cases import day, text


def path(folder):
    return Path(folder) / 'research' / 'predictions.jsonl'


def validate(row):
    fields = {'id', 'schema', 'recorded_at', 'symbol', 'statement', 'resolution_criteria',
              'resolve_by', 'probability', 'base_rate', 'submitter', 'agent', 'model',
              'protocol', 'strategy', 'event_key'}
    if isinstance(row, dict) and row.get('schema') == 2:
        fields |= {'supersedes', 'scenario'}
    if not isinstance(row, dict) or set(row) != fields or row['schema'] not in {1, 2}:
        raise ValueError('Invalid prediction schema')
    for key in fields - {'id', 'schema', 'probability', 'base_rate', 'supersedes', 'scenario'}:
        text(row[key], 1200 if key in {'statement', 'resolution_criteria'} else 200)
        if not row[key].strip() and key != 'strategy':
            raise ValueError('Prediction requires ' + key)
    for key in ('probability', 'base_rate'):
        if type(row[key]) not in (float, int) or not 0 <= row[key] <= 1:
            raise ValueError('Probabilities must be finite numbers from 0 to 1')
    made = datetime.fromisoformat(row['recorded_at'])
    if made.tzinfo is None or made > datetime.now(timezone.utc):
        raise ValueError('Prediction capture time must be in the past with a timezone')
    if day(row['resolve_by']) <= made.date():
        raise ValueError('Resolution deadline must follow capture date')
    expected = hashlib.sha256(canonical({k: v for k, v in row.items() if k != 'id'})).hexdigest()
    if row['id'] != expected:
        raise ValueError('Prediction integrity check failed')
    if row['schema'] == 2:
        from officekit_research.scenario_forecasts import validate_metadata
        validate_metadata(row['scenario'])
        if row['scenario']['event_start'] and day(row['scenario']['event_start']) > day(row['resolve_by']):
            raise ValueError('Event window must start before the deadline')
        if row['supersedes'] is not None and not __import__('re').fullmatch('[a-f0-9]{64}', str(row['supersedes'])):
            raise ValueError('Invalid forecast revision')
    return row


def load(folder):
    p = path(folder)
    if p.is_symlink() or any(parent.is_symlink() for parent in p.absolute().parents):
        raise ValueError('Prediction storage cannot follow symbolic links')
    if not p.exists():
        return []
    rows = [validate(parse_json(line)) for line in p.read_bytes().splitlines() if line.strip()]
    _validate_history(rows)
    return rows


def _validate_history(rows):
    latest = {}
    for r in rows:
        key = (r['submitter'], r['agent'], r['event_key'])
        prior = latest.get(key)
        if prior:
            if r.get('supersedes') != prior['id']:
                raise ValueError('Duplicate prediction identity; reconcile without deleting history')
            if any(r[k] != prior[k] for k in ('symbol', 'statement', 'resolution_criteria', 'resolve_by')):
                raise ValueError('Forecast revisions cannot change the event or deadline')
            if r.get('scenario') and any(r['scenario'][k] != prior.get('scenario', {}).get(k) for k in ('scenario_key', 'event_start', 'condition')):
                raise ValueError('Forecast revisions cannot change the event window or conditions')
            if r['recorded_at'] <= prior['recorded_at']:
                raise ValueError('Forecast update must follow the prior version')
        elif r.get('supersedes'):
            raise ValueError('Forecast revision is missing its original')
        latest[key] = r


def _make(*, symbol, statement, resolution_criteria, resolve_by, probability,
           base_rate, submitter, agent, model, protocol, event_key, strategy='', scenario=None, supersedes=None):
    row = dict(schema=1, recorded_at=datetime.now(timezone.utc).isoformat(), symbol=symbol.upper(),
               statement=statement, resolution_criteria=resolution_criteria, resolve_by=resolve_by,
               probability=probability, base_rate=base_rate, submitter=submitter, agent=agent,
               model=model, protocol=protocol, strategy=strategy, event_key=event_key)
    if scenario is not None:
        row.update(schema=2, scenario=scenario, supersedes=supersedes)
    row['id'] = hashlib.sha256(canonical(row)).hexdigest()
    validate(row)
    return row


def record_many(folder, entries):
    """Validate a whole research run before one append; no partial successful bench."""
    rows = [_make(**fields) for fields in entries]
    with locked(folder):
        existing = load(folder)
        from officekit_research.index import load_outcomes
        outcomes = load_outcomes(folder)
        for row in rows:
            previous = [r for r in existing if (r['submitter'], r['agent'], r['event_key']) ==
                        (row['submitter'], row['agent'], row['event_key'])]
            if previous and not row.get('supersedes'):
                raise ValueError('This submitter and agent already registered that event; forecasts are immutable')
            if any(r['id'] + ':0' in outcomes for r in previous):
                raise ValueError('A resolved event cannot receive another forecast')
        _validate_history(existing + rows)
        p = path(folder)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('a', encoding='utf-8') as stream:
            stream.write(''.join(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n' for row in rows))
    return rows


def record(folder, **fields):
    return record_many(folder, [fields])[0]


def agent_identity(record):
    """Credit the adjudicator who supplied the forecast, not all court roles."""
    run = (record.get('runs') or {}).get('adjudicate') or {}
    cfg = {'model': record['models']['adjudicate'], 'protocol': record['protocol_hash'],
           'reasoning': run.get('reasoning_configuration'), 'provider': run.get('provider')}
    return 'general_adjudicate / ' + cfg['model'] + ' / ' + hashlib.sha256(canonical(cfg)).hexdigest()[:16]


def joint_identity(submitter, agent):
    return json.dumps([submitter, agent], ensure_ascii=False, separators=(',', ':'))
