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
    if not isinstance(row, dict) or set(row) != fields or row['schema'] != 1:
        raise ValueError('Invalid prediction schema')
    for key in fields - {'id', 'schema', 'probability', 'base_rate'}:
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
    return row


def load(folder):
    p = path(folder)
    if p.is_symlink() or any(parent.is_symlink() for parent in p.absolute().parents):
        raise ValueError('Prediction storage cannot follow symbolic links')
    if not p.exists():
        return []
    rows = [validate(parse_json(line)) for line in p.read_bytes().splitlines() if line.strip()]
    keys = [(r['submitter'], r['agent'], r['event_key']) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate prediction identity; reconcile without deleting history')
    return rows


def record(folder, *, symbol, statement, resolution_criteria, resolve_by, probability,
           base_rate, submitter, agent, model, protocol, event_key, strategy=''):
    row = dict(schema=1, recorded_at=datetime.now(timezone.utc).isoformat(), symbol=symbol.upper(),
               statement=statement, resolution_criteria=resolution_criteria, resolve_by=resolve_by,
               probability=probability, base_rate=base_rate, submitter=submitter, agent=agent,
               model=model, protocol=protocol, strategy=strategy, event_key=event_key)
    row['id'] = hashlib.sha256(canonical(row)).hexdigest()
    validate(row)
    with locked(folder):
        if any((r['submitter'], r['agent'], r['event_key']) == (submitter, agent, event_key) for r in load(folder)):
            raise ValueError('This submitter and agent already registered that event; forecasts are immutable')
        p = path(folder)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')
    return row


def agent_identity(record):
    """Credit the adjudicator who supplied the forecast, not all court roles."""
    run = (record.get('runs') or {}).get('adjudicate') or {}
    cfg = {'model': record['models']['adjudicate'], 'protocol': record['protocol_hash'],
           'reasoning': run.get('reasoning_configuration'), 'provider': run.get('provider')}
    return 'general_adjudicate / ' + cfg['model'] + ' / ' + hashlib.sha256(canonical(cfg)).hexdigest()[:16]


def joint_identity(submitter, agent):
    return json.dumps([submitter, agent], ensure_ascii=False, separators=(',', ':'))
