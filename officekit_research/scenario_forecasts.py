"""Scenario annotations on the existing immutable prediction ledger.

Probability inputs are never predictions. Only explicit, dated, attributable
claims enter this library and scorecard. Imported identity remains claimed.
"""
from datetime import date
import hashlib
import json
import math
from copy import deepcopy
from pathlib import Path
from statistics import mean

from officekit_research import predictions
from officekit_research.cases import safe_url

META_FIELDS = {'scenario_key', 'summary', 'condition', 'dependency_group', 'evidence', 'gaps',
               'symbols', 'origin', 'intelligence', 'reviewed', 'event_start'}


def validate_metadata(meta):
    if not isinstance(meta, dict) or set(meta) != META_FIELDS:
        raise ValueError('Invalid scenario research metadata')
    for key in {'scenario_key', 'summary', 'condition', 'dependency_group', 'origin', 'intelligence', 'event_start'}:
        if not isinstance(meta[key], str) or len(meta[key]) > (12000 if key == 'summary' else 300):
            raise ValueError('Invalid scenario research ' + key)
    if not meta['scenario_key'].strip():
        raise ValueError('A scenario subject is required')
    if meta['event_start']:
        date.fromisoformat(meta['event_start'])
    if type(meta['reviewed']) is not bool or meta['origin'] not in {'own', 'imported', 'ai'}:
        raise ValueError('Invalid scenario origin or review status')
    if not isinstance(meta['symbols'], list) or len(meta['symbols']) > 12 or any(not isinstance(s, str) or len(s) > 15 for s in meta['symbols']):
        raise ValueError('At most twelve ticker subjects')
    if not isinstance(meta['gaps'], list) or len(meta['gaps']) > 40 or any(not isinstance(g, str) or len(g) > 1500 for g in meta['gaps']):
        raise ValueError('Invalid research gaps')
    if not isinstance(meta['evidence'], list) or len(meta['evidence']) > 30:
        raise ValueError('At most thirty evidence items')
    for e in meta['evidence']:
        if set(e) != {'url', 'text', 'sha256', 'fetched_at', 'visibility'}:
            raise ValueError('Evidence needs a source, exact text, digest, date and visibility')
        safe_url(e['url'])
        if not isinstance(e['text'], str) or not e['text'].strip() or len(e['text']) > 60000:
            raise ValueError('Evidence text must be present and bounded')
        if hashlib.sha256(e['text'].encode()).hexdigest() != e['sha256']:
            raise ValueError('Evidence digest does not match the supplied text')
        if e['visibility'] not in {'private', 'public_document', 'public_market'}:
            raise ValueError('Evidence class must be explicitly declared')
        if date.fromisoformat(e['fetched_at'][:10]) > date.today():
            raise ValueError('Evidence cannot be fetched in the future')
    return meta


def metadata(key, *, summary='', symbols=(), evidence=(), condition='', dependency_group='',
             origin='own', intelligence='human', gaps=(), reviewed=False, event_start=''):
    return validate_metadata(dict(scenario_key=key, summary=summary, symbols=list(symbols), evidence=list(evidence),
                                  condition=condition, dependency_group=dependency_group, origin=origin,
                                  intelligence=intelligence, gaps=list(gaps), reviewed=reviewed, event_start=event_start))


def records(folder, key=None):
    p = Path(folder) / 'research' / 'scenario_reviews.json'
    if p.is_symlink() or any(parent.is_symlink() for parent in p.absolute().parents):
        raise ValueError('Research reviews cannot follow symlinks')
    reviews = json.loads(p.read_text()) if p.exists() else {}
    from officekit_research.index import load_outcomes
    outcomes = load_outcomes(folder)
    rows = []
    for r in predictions.load(folder):
        if r.get('scenario') and (key is None or r['scenario']['scenario_key'] == key):
            r = deepcopy(r)
            r['scenario']['reviewed'] = r['id'] in reviews
            r['_resolved'] = r['id'] + ':0' in outcomes
            rows.append(r)
    return rows


def review(folder, rid):
    from officekit.office_lock import locked
    from datetime import datetime, timezone
    if not any(r['id'] == rid and r.get('scenario') and r['scenario']['evidence'] for r in predictions.load(folder)):
        raise ValueError('Unknown forecast')
    with locked(folder):
        p = Path(folder) / 'research' / 'scenario_reviews.json'
        if p.is_symlink():
            raise ValueError('Research reviews cannot follow symlinks')
        existing = json.loads(p.read_text()) if p.exists() else {}
        existing[rid] = {'reviewed_at': datetime.now(timezone.utc).isoformat(), 'reviewer': 'office owner'}
        p.write_text(json.dumps(existing, indent=2) + '\n')


def event_identity(r):
    return (r['event_key'], r['statement'], r['resolution_criteria'], r['resolve_by'], r['scenario']['event_start'])


def aggregate(rows):
    """Equal weight per declared source family; no vote count or skill gating."""
    groups = {}
    latest = {}
    for r in rows:
        latest[(r['submitter'], r['agent'], r['event_key'])] = r
    for r in latest.values():
        m = r['scenario']
        if not m['reviewed'] or m['condition'] or r.get('_resolved') or date.fromisoformat(r['resolve_by']) <= date.today():
            continue
        group = groups.setdefault(event_identity(r), [])
        group.append(r)
    out = []
    for identity, members in groups.items():
        families = {}
        for r in members:
            # Unknown dependence is pooled together, never counted as independent.
            family = r['scenario']['dependency_group'] or 'shared-or-unknown'
            families.setdefault(family, []).append(r['probability'])
        p = mean(mean(values) for values in families.values())
        out.append({'contract_id': hashlib.sha256(json.dumps(identity).encode()).hexdigest(), 'event_key': identity[0], 'statement': identity[1], 'criteria': identity[2],
                    'resolve_by': identity[3], 'event_start': identity[4], 'probability': p,
                    'range': [min(r['probability'] for r in members), max(r['probability'] for r in members)],
                    'submissions': len(members), 'source_families': len(families), 'ids': [r['id'] for r in members],
                    'method': 'Average within declared source families, then equal family weights. '
                              'Shared evidence can still correlate families; the range is disagreement, not a confidence interval.'})
    return out


def import_forecast(folder, raw):
    """Explicit office import. No network, public admission, or trusted identity."""
    from officekit.migration import parse_json
    r = parse_json(raw)
    predictions.validate(r)
    if not r.get('scenario'):
        raise ValueError('Choose a scenario forecast with evidence and an event definition')
    m = dict(r['scenario'], origin='imported', reviewed=False)
    # Capture at import time; never backdate a newly entered, scoreable forecast.
    # Original capture metadata stays in the explanatory text.
    m['summary'] = ('Imported claim from ' + r['recorded_at'] + '. Original ID ' + r['id'] + '.\n' + m['summary'])[:12000]
    return predictions.record(folder, **{k: r[k] for k in
        ('symbol', 'statement', 'resolution_criteria', 'resolve_by', 'probability', 'base_rate', 'submitter', 'agent', 'model', 'protocol', 'event_key', 'strategy')}, scenario=m)
