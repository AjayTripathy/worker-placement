"""Version 1 validation and non-destructive projection of legacy research.

Never infer an outcome, size, actor or event taxonomy from prose. Historical
ambiguities remain in the ledger and are excluded from performance/routing
with their content digest and reasons available for explicit adjudication.
"""
from collections import Counter
from copy import deepcopy
from datetime import date
import hashlib
import json
import math

VERSION = 1
STATUSES = {'OPEN', 'RESOLVED', 'VOIDED', 'EXCLUDED_LOOKAHEAD'}


def identity(row):
    return hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def key(row):
    return row.get('ticker'), row.get('cat_date'), row.get('event_type')


def calibration_issues(row):
    from desk.events import EVENT_TYPES
    from desk.calibration import _y
    problems = []
    if not row.get('ticker'):
        problems.append('missing ticker')
    if row.get('status') not in STATUSES:
        problems.append('unrecognized status; explicit outcome adjudication required')
    if row.get('event_type') not in EVENT_TYPES:
        problems.append('unrecognized event taxonomy; frozen cohort must not be inferred')
    p = row.get('our_p')
    if type(p) not in (float, int) or not math.isfinite(p) or not 0 <= p <= 1:
        problems.append('invalid forecast probability')
    try:
        made, due = date.fromisoformat(row['made'][:10]), date.fromisoformat(row['cat_date'][:10])
        if made > due and row.get('status') != 'EXCLUDED_LOOKAHEAD':
            problems.append('forecast recorded after event deadline')
    except (KeyError, TypeError, ValueError):
        problems.append('missing or invalid forecast/event dates')
    if row.get('status') == 'RESOLVED' and _y(row) not in (0., .5, 1.):
        problems.append('resolved record lacks a supported outcome')
    return problems


def project_calibration(rows):
    duplicates = Counter(key(r) for r in rows if r.get('status') == 'OPEN')
    projected, quarantine = [], []
    for row in rows:
        issues = calibration_issues(row)
        if row.get('status') == 'OPEN' and duplicates[key(row)] > 1:
            issues.append('duplicate OPEN identity; all versions await explicit supersession')
        copy = deepcopy(row)
        if issues:
            quarantine.append({'record_sha256': identity(row), 'ticker': row.get('ticker'), 'issues': issues})
            copy.update(status='EXCLUDED_REVIEW', contract_version=VERSION, contract_issues=issues)
        projected.append(copy)
    return projected, {'contract_version': VERSION, 'total': len(rows), 'excluded': len(quarantine), 'records': quarantine}


def validate_new(row, existing):
    issues = calibration_issues(row)
    if any(key(r) == key(row) for r in existing):
        issues.append('prediction identity already frozen; use explicit supersession')
    if issues:
        raise ValueError('; '.join(issues))


def routing_issues(ledger, record):
    from desk.verdicts import STATES
    issues = []
    states = [ledger.get('verdict'), ledger.get('state'), record.get('verdict_state')]
    if any(s not in STATES for s in states) or len(set(states)) != 1:
        issues.append('structured verdict mismatch; adjudication required')
    sizing = record.get('sizing')
    if not isinstance(sizing, dict) or not all(type(sizing.get(k)) in (int, float) and math.isfinite(sizing[k]) for k in ('pct_lo', 'pct_hi')):
        issues.append('missing structured sizing {pct_lo, pct_hi}; do not infer from prose')
    elif not 0 < sizing['pct_lo'] <= sizing['pct_hi'] <= 100:
        issues.append('invalid structured sizing bounds')
    return issues
