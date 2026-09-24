"""Private, evidence-backed beta mandates. Planning and records; never orders.

Lifecycle records are separate from readiness: an approved mandate can have a
stale basket, missing lots or a broken broker connection without losing history.
All financial ceilings come from the shared incoming-money model.
"""
from copy import deepcopy
from datetime import date
import math
import re
import uuid

from officekit.strategy_proposals import digest

VERSION = 1
STATES = ('eligible', 'proposed', 'approved', 'funded', 'operating')
LIMIT = 24


def number(value, lo=0, hi=1e12):
    if isinstance(value, bool):
        raise ValueError('Enter a finite number.')
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError('Enter a finite number.') from None
    if not math.isfinite(result) or not lo <= result <= hi:
        raise ValueError(f'Enter a number between {lo:g} and {hi:g}.')
    return result


def text(value, limit=1000):
    if not isinstance(value, str) or len(value) > limit:
        raise ValueError(f'Enter text up to {limit} characters.')
    return value.strip()


def symbol(value):
    value = text(value, 20).upper().replace(' ', '.')
    if not re.fullmatch(r'[A-Z0-9][A-Z0-9.^-]{0,19}', value):
        raise ValueError('Enter a valid security symbol.')
    return value


def canon(value):
    return re.sub(r'[ .-]', '', symbol(value))


def dated(value):
    if not isinstance(value, str):
        raise ValueError('Enter an ISO calendar date.')
    return date.fromisoformat(value).isoformat()


def fresh(value, today=None, days=7):
    try:
        age = ((today or date.today()) - date.fromisoformat(value)).days
        return 0 <= age <= days
    except (TypeError, ValueError):
        return False


def programs(answers):
    return answers.get('beta_programs') or {}


def policy_hash(p):
    # Market/benchmark refreshes do not change approved mandate terms.
    return digest({**{k: p.get(k) for k in ('id', 'account', 'taxable', 'bindings', 'policy')},
                   'benchmark_identity': (p.get('benchmark_snapshot') or {}).get('name')})


def normalize_snapshot(raw):
    if not isinstance(raw, dict) or not isinstance(raw.get('rows'), list) or not 2 <= len(raw['rows']) <= 5000:
        raise ValueError('Supply a dated benchmark with 2–5,000 constituents.')
    rows, seen = [], set()
    for item in raw['rows']:
        s = symbol(item['symbol'])
        if canon(s) in seen:
            raise ValueError('Duplicate benchmark constituent.')
        seen.add(canon(s))
        rows.append({'symbol': s, 'name': text(item.get('name', s), 200),
                     'weight': number(item['weight'], 0.000000001, 1),
                     'sector': text(item.get('sector', 'Unclassified'), 100)})
    total = sum(r['weight'] for r in rows)
    if not .95 <= total <= 1.05:
        raise ValueError('Benchmark weights must sum to approximately 1, not percentages.')
    for r in rows:
        r['weight'] /= total
    result = {'name': text(raw.get('name', 'Imported benchmark'), 150),
              'as_of': dated(raw['as_of']), 'source': text(raw['source'], 1000), 'rows': rows}
    if not result['source']:
        raise ValueError('A benchmark source reference is required.')
    result['sha256'] = digest(result)
    return result


def normalize(raw):
    if not isinstance(raw, dict):
        raise ValueError('Supply a program object.')
    pid = text(raw.get('id') or str(uuid.uuid4()), 80)
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', pid):
        raise ValueError('Invalid program ID.')
    policy = raw.get('policy') or {}
    if not isinstance(policy, dict) or not isinstance(policy.get('exclusions', []), list):
        raise ValueError('Supply a policy object and an exclusions list.')
    if policy.get('mode', 'long_only') != 'long_only':
        raise ValueError('Short extensions require a separately reviewed mandate; this program is long-only.')
    bindings = raw.get('bindings') or {}
    if not isinstance(bindings, dict) or len(bindings) > 32:
        raise ValueError('Supply up to 32 incoming-money bindings.')
    p = {'id': pid, 'label': text(raw.get('label') or 'Beta & tax-loss harvesting', 180),
         'account': text(raw.get('account', ''), 180),
         'taxable': raw.get('taxable') if isinstance(raw.get('taxable'), bool) else None,
         'bindings': {text(k, 180): number(v, .01, 100) for k, v in bindings.items()},
         'policy': {'mode': 'long_only', 'benchmark': text(policy.get('benchmark', 'SPTM'), 100),
                    'max_names': int(number(policy.get('max_names', 150), 2, 500)),
                    'max_weight': number(policy.get('max_weight', .025), .002, .5),
                    'horizon_years': number(policy.get('horizon_years', 5), 0, 100),
                    'fee_bps': number(policy['fee_bps'], 0, 1000) if policy.get('fee_bps') is not None else None,
                    'min_loss': number(policy.get('min_loss', 1000), 0, 1e9),
                    'tax_rate': number(policy['tax_rate'], 0, .7) if policy.get('tax_rate') is not None else None,
                    'gain_capacity': number(policy['gain_capacity']) if policy.get('gain_capacity') is not None else None,
                    'tax_year': int(number(policy.get('tax_year', date.today().year), 2000, 2100)),
                    'reserve_floor': number(policy.get('reserve_floor', 0)),
                    'capital_cap': number(policy['capital_cap']) if policy.get('capital_cap') is not None else None,
                    'exclusions': sorted({symbol(s) for s in policy.get('exclusions', [])})},
         'history': [], 'replacements': {}, 'harvests': []}
    if len(p['policy']['exclusions']) > 5000:
        raise ValueError('Too many exclusions.')
    if raw.get('benchmark_snapshot'):
        p['benchmark_snapshot'] = normalize_snapshot(raw['benchmark_snapshot'])
    if p['policy']['max_names'] != float(policy.get('max_names', 150)):
        raise ValueError('Maximum constituents must be a whole number.')
    for k in ('provenance', 'execution_note'):
        p[k] = text(raw.get(k, ''), 4000)
    return p


def validate(value):
    try:
        if not isinstance(value, dict) or len(value) > LIMIT:
            raise ValueError('Too many beta programs.')
        totals = {}
        for key, p in value.items():
            cleaned = normalize(p)
            if key != cleaned['id']:
                raise ValueError('Program identity mismatch.')
            for field in ('label', 'account', 'taxable', 'bindings', 'policy'):
                if p.get(field) != cleaned[field]:
                    raise ValueError('Program policy and bindings must use normalized values.')
            for sid, pct in p['bindings'].items():
                totals[sid] = totals.get(sid, 0) + pct
                if totals[sid] > 100.000001:
                    raise ValueError('Combined allocations exceed 100% of an inflow.')
            validate_records(p)
        return []
    except (ValueError, TypeError, KeyError, AttributeError) as error:
        return ['Invalid beta program: ' + str(error)]


def validate_records(p):
    """Validate imported durable state as strictly as interactive form writes."""
    def record(r, date_key='as_of', past=True):
        if not isinstance(r, dict) or not text(r['reference']):
            raise ValueError('A dated evidence reference is required.')
        d = dated(r[date_key])
        if past and d > date.today().isoformat():
            raise ValueError('Evidence cannot be future-dated.')
    snap = p.get('benchmark_snapshot')
    if snap:
        if snap.get('sha256') != digest({k: v for k, v in snap.items() if k != 'sha256'}):
            raise ValueError('Benchmark fingerprint does not match its contents.')
        for row in snap['rows']:
            if not isinstance(row['weight'], (float, int)) or isinstance(row['weight'], bool) or row['symbol'] != symbol(row['symbol']):
                raise ValueError('Benchmark rows must use normalized symbols and numeric weights.')
    for key in ('approval', 'funding', 'operation'):
        if p.get(key):
            r = p[key]
            record(r)
            if key == 'approval' and not re.fullmatch('[a-f0-9]{64}', r['policy_hash']):
                raise ValueError('Invalid approval fingerprint.')
            if key == 'funding':
                number(r['amount'], .01)
                if not isinstance(r['amount'], (int, float)):
                    raise ValueError('Funding must be numeric.')
            if key == 'operation' and r['status'] not in {'operating', 'paused', 'error'}:
                raise ValueError('Invalid operating state.')
    for key, maximum in [('history', 10000), ('harvests', 10000)]:
        if not isinstance(p.get(key, []), list) or len(p.get(key, [])) > maximum:
            raise ValueError('Too many program records.')
        for r in p.get(key, []):
            record(r, 'at' if key == 'history' else 'date')
            if key == 'history':
                text(r['action'], 100)
            else:
                symbol(r['symbol']); text(r['security_id'], 180)
                if r.get('voided'):
                    text(r['voided'])
    replacements = p.get('replacements', {})
    if not isinstance(replacements, dict) or len(replacements) > 5000:
        raise ValueError('Too many replacements.')
    for key, r in replacements.items():
        symbol(key); record(r); symbol(r['symbol']); text(r['rationale'])
    if p.get('wash_review'):
        r = p['wash_review']
        record(r)
        from officekit.beta_harvest import review_household
        check = deepcopy(p)
        review_household(check, r)
        if check['wash_review'] != r:
            raise ValueError('Household activity must use normalized values.')


def candidate(model):
    """Every office gets an assessment, including why inputs/alternatives matter."""
    from officekit.deployment import sources
    from officekit.donation_securities import inventory
    rows = inventory(model)
    taxable = any(r['taxable'] is True for r in rows)
    retirement_only = bool(rows) and all(r['taxable'] is False for r in rows) and not sources(model)
    return {'status': 'not_suitable' if retirement_only else 'eligible' if taxable else 'needs_inputs',
            'reason': 'Retirement-only holdings do not generate deductible capital losses.' if retirement_only else
            'Compare a long-only benchmark basket with ETFs and existing managed accounts; confirm account tax status, costs and horizon.',
            'alternatives': ['Low-cost index funds', 'Coordinate an existing direct-index manager', 'New direct-index basket']}


def allocation(p, model):
    from officekit.deployment import funding
    current, pending, tax, gaps = 0, 0, 0, []
    for sid, pct in p['bindings'].items():
        try:
            f = funding(model, sid)
        except ValueError:
            gaps.append('A linked incoming-money source is no longer available.')
            continue
        current += f['current_budget'] * pct / 100
        pending += f['contingent_budget'] * pct / 100
        tax += (f['pending_tax'] + f.get('current_tax', 0)) * pct / 100
        gaps.extend(f['blocking_gaps'])
    if not p['bindings']:
        gaps.append('Link an incoming-money source and allocation percentage.')
    extra = max(0, p['policy']['reserve_floor'] - tax)
    # Preserve approved reserve terms until explicitly changed; never spend the
    # discrepancy merely because a newer model computes a lower tax bill.
    take = min(pending, extra)
    pending -= take
    current = max(0, current - (extra - take))
    cap = p['policy'].get('capital_cap')
    if cap is not None:
        current = min(current, cap)
        pending = min(pending, max(0, cap - current))
    return {'current': round(current, 2), 'pending': round(pending, 2),
            'total': round(current + pending, 2), 'additional_reserve': round(extra, 2), 'gaps': gaps}


def basket(p, budget):
    snap = p.get('benchmark_snapshot') or {}
    universe = snap.get('rows') or []
    excluded = {canon(s) for s in p['policy']['exclusions']}
    selected = sorted((r for r in universe if canon(r['symbol']) not in excluded),
                      key=lambda r: (-r['weight'], r['symbol']))[:p['policy']['max_names']]
    cap = p['policy']['max_weight']
    if not selected or len(selected) * cap < 1 - 1e-8:
        return {'rows': [], 'gaps': ['Too few eligible constituents for the position cap; refresh the benchmark or review the policy.'],
                'active_share': None, 'sector_deviations': {}}
    free = {r['symbol']: r['weight'] for r in selected}
    weights, remaining = {}, 1.0
    while free:
        total = sum(free.values())
        over = {s for s, w in free.items() if remaining * w / total > cap + 1e-12}
        if not over:
            weights.update({s: remaining * w / total for s, w in free.items()})
            break
        for s in over:
            weights[s] = cap
            remaining -= cap
            del free[s]
    amounts = {}
    for column in ('current', 'pending'):
        cents = round(budget[column] * 100)
        allocated = {s: int(cents * w) for s, w in weights.items()}
        residual = cents - sum(allocated.values())
        for s in sorted(weights, key=lambda s: (-(cents * weights[s] - allocated[s]), s))[:residual]:
            allocated[s] += 1
        amounts[column] = allocated
    rows = [{**r, 'weight': weights[r['symbol']], 'current': amounts['current'][r['symbol']] / 100,
             'pending': amounts['pending'][r['symbol']] / 100} for r in selected]
    sector = {}
    for r in universe:
        sector[r['sector']] = sector.get(r['sector'], 0) + weights.get(r['symbol'], 0) - r['weight']
    active = .5 * sum(abs(weights.get(r['symbol'], 0) - r['weight']) for r in universe)
    return {'rows': rows, 'gaps': [], 'active_share': active, 'sector_deviations': sector}


def view(p, model, today=None):
    today = today or date.today()
    budget = allocation(p, model)
    built = basket(p, budget)
    gaps = list(budget['gaps']) + built['gaps']
    if p['taxable'] is not True:
        gaps.append('Confirm this is a taxable account; TLH does not create deductions inside a retirement account.')
    if not p['account']:
        gaps.append('Identify the program account so lots and cash can be reconciled.')
    if p['policy']['horizon_years'] < 5:
        gaps.append('Review a shorter-horizon alternative before committing this money to equity beta.')
    if p['policy']['fee_bps'] is None:
        gaps.append('Record annual all-in cost assumptions before activation or new approval.')
    if not fresh((p.get('benchmark_snapshot') or {}).get('as_of'), today):
        gaps.append('Refresh benchmark constituents; the saved snapshot is missing, future-dated or over seven days old.')
    approved = bool(p.get('approval')) and p['approval'].get('policy_hash') == policy_hash(p)
    state = 'proposed' if p.get('benchmark_snapshot') else 'eligible'
    if approved:
        state = 'approved'
    funded = p.get('funding') or {}
    if approved and funded.get('amount', 0) > 0 and funded.get('reference'):
        state = 'funded'
    operation = p.get('operation') or {}
    if state == 'funded' and operation.get('status') == 'operating' and fresh(operation.get('as_of'), today) and not gaps:
        from officekit.beta_harvest import overlay
        monitoring = overlay(p, model, today)['monitoring_gaps']
        gaps.extend(monitoring)
        if not monitoring:
            state = 'operating'
    if p.get('approval') and not approved:
        gaps.append('Policy or source allocation changed; approve the revised mandate.')
    if p.get('execution_note'):
        gaps.append(p['execution_note'])
    if budget['additional_reserve'] > .01:
        gaps.append('Approved reserve exceeds the current pending-tax model. The difference remains reserved until terms are reconciled.')
    if operation.get('status') in {'error', 'paused'}:
        gaps.append('Program ' + operation['status'] + ': ' + operation.get('reference', 'review the operating record'))
    if operation.get('status') == 'operating' and not fresh(operation.get('as_of'), today):
        gaps.append('Operating evidence is over seven days old; refresh the reconciliation.')
    if state == 'operating' and gaps:
        state = 'funded'
    fee = p['policy']['fee_bps']
    return {'id': p['id'], 'label': p['label'], 'state': state, 'ready': not gaps,
            'account': p['account'], 'bindings': p['bindings'], 'budget': budget, 'basket': built,
            'gaps': list(dict.fromkeys(gaps)), 'benchmark': (p.get('benchmark_snapshot') or {}).get('name', p['policy']['benchmark']),
            'benchmark_as_of': (p.get('benchmark_snapshot') or {}).get('as_of'),
            'annual_fee_estimate': budget['total'] * fee / 10000 if fee is not None else None,
            'approved': approved, 'funded_amount': funded.get('amount', 0),
            'method': 'Long-only capped benchmark sampling. Active share and sector deviations are measured; statistical tracking error and outperformance are not predicted.'}


def summaries(answers, model, source_id=None):
    result = []
    for p in programs(answers).values():
        if source_id and source_id not in p['bindings']:
            continue
        v = view(p, model)
        v['href'] = '/pages/beta_programs.html#program-' + p['id']
        result.append(v)
    return result


def remaining_funding(model, funding, source_id=None):
    """Reserve bound shares in planning arithmetic, including retained reserves.

    A linked draft already expresses an allocation choice. Its readiness gaps
    must not let a competing proposal spend those dollars. Unlink it to release.
    This does not mutate bank balances or create a tax deduction.
    """
    from officekit.deployment import sources, funding as source_funding
    current, pending, ids = 0, 0, []
    for source in sources(model):
        if source_id and source['id'] != source_id:
            continue
        bound = [p for p in programs(model['d']).values() if source['id'] in p['bindings']]
        pct = min(100, sum(p['bindings'][source['id']] for p in bound)) / 100
        if not pct:
            continue
        base = source_funding(model, source['id'])
        current += base['current_budget'] * pct
        pending += base['contingent_budget'] * pct
        ids.extend(p['id'] for p in bound)
    result = dict(funding)
    result['program_reserved_current'] = round(current, 2)
    result['program_reserved_pending'] = round(pending, 2)
    result['linked_programs'] = sorted(set(ids))
    if not ids:
        return result
    for field, reserved in [('current_budget', current), ('contingent_budget', pending)]:
        result[field] = round(max(0, result[field] - reserved), 2)
    result['proposal_ceiling'] = round(result['current_budget'] + result['contingent_budget'], 2)
    if ids:
        result['sizing_basis'] += ' Shares linked to beta programs are withheld from additional proposals, including program cash retained. Review or unlink that allocation to change it.'
    return result


def planning_data(data):
    """Bound agent context; full source constituents and activity stay in records."""
    result = {k: v for k, v in data.items() if k != 'beta_programs'}
    result['beta_programs'] = [{
        'id': p['id'], 'label': p['label'], 'account': p['account'], 'bindings': p['bindings'],
        'policy': {k: v for k, v in p['policy'].items() if k != 'exclusions'},
        'exclusion_count': len(p['policy']['exclusions']),
        'approval_recorded': bool(p.get('approval')), 'execution_note': p.get('execution_note', ''),
        'href': '/pages/beta_programs.html#program-' + p['id']
    } for p in programs(data).values()]
    return result


def event(p, action, reference):
    p.setdefault('history', []).append({'at': date.today().isoformat(), 'action': action,
                                       'reference': text(reference, 1000), 'policy_hash': policy_hash(p)})


def save_program(answers, p, model):
    from officekit.deployment import source_for
    updated = deepcopy(answers)
    existing = updated.setdefault('beta_programs', {})
    if p['id'] not in existing and len(existing) >= LIMIT:
        raise ValueError('Archive or reuse an existing beta program first.')
    for sid, pct in p['bindings'].items():
        source_for(model, sid)
        used = sum(q['bindings'].get(sid, 0) for key, q in existing.items() if key != p['id'])
        if used + pct > 100.000001:
            raise ValueError('Combined program allocations cannot exceed 100% of this inflow.')
    existing[p['id']] = p
    errors = validate(existing)
    if errors:
        raise ValueError('; '.join(errors))
    return updated


def transition(answers, model, pid, action, reference, amount=None):
    p = deepcopy(programs(answers)[pid])
    reference = text(reference)
    if not reference:
        raise ValueError('Record the decision, statement or operating-review reference.')
    v = view(p, model)
    if action == 'approve':
        check = deepcopy(p)
        check.pop('approval', None)
        gaps = view(check, model)['gaps']
        if gaps:
            raise ValueError('Resolve readiness gaps before approving: ' + '; '.join(gaps))
        if not v['approved']:
            p.pop('funding', None)
            p.pop('operation', None)
        p['approval'] = {'as_of': date.today().isoformat(), 'reference': reference, 'policy_hash': policy_hash(p)}
    elif action == 'fund':
        value = number(amount, .01)
        if not v['approved'] or v['gaps'] or value > v['budget']['current'] + .001:
            raise ValueError('Funding requires an approved, ready mandate and reconciled received cash within its allocation.')
        p['funding'] = {'as_of': date.today().isoformat(), 'reference': reference, 'amount': value}
    elif action == 'operate':
        from officekit.beta_harvest import overlay
        p.pop('operation', None)  # A new reconciliation can resolve a pause/error.
        v = view(p, model)
        o = overlay(p, model)
        if v['state'] != 'funded' or v['gaps'] or o['monitoring_gaps']:
            raise ValueError('Operating requires funded cash, current benchmark/lot data and a complete household wash review.')
        p['operation'] = {'status': 'operating', 'as_of': date.today().isoformat(), 'reference': reference}
    elif action in {'pause', 'error'}:
        p['operation'] = {'status': 'paused' if action == 'pause' else 'error', 'as_of': date.today().isoformat(), 'reference': reference}
    else:
        raise ValueError('Choose a supported lifecycle action.')
    event(p, action, reference)
    return save_program(answers, p, model)
