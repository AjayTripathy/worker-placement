"""Lot-level harvesting review and household repurchase calendar; no execution."""
from copy import deepcopy
from datetime import date, timedelta

from officekit.beta_programs import canon, fresh, text, dated, symbol, number, event
from officekit.donation_securities import inventory


def overlay(program, model, today=None):
    today = today or date.today()
    household = inventory(model)
    rows = [r for r in household if r['account'] == program['account']]
    review = program.get('wash_review') or {}
    # All programs belong to one private household. Do not partition wash-sale
    # evidence by the mandate that happened to record it.
    peers = dict(model['d'].get('beta_programs') or {})
    peers[program['id']] = program
    reviews = [p.get('wash_review') or {} for p in peers.values()]
    harvests = [h for p in peers.values() for h in p.get('harvests', []) if not h.get('voided')]
    monitoring = []
    if not rows:
        monitoring.append('Import holdings and tax lots for the program account.')
    if not fresh(review.get('as_of'), today) or not review.get('complete'):
        monitoring.append('Review all household accounts, spouse/IRA activity, dividend reinvestments and open buy orders within seven days.')
    if any(not fresh(r['as_of'], today) for r in rows):
        monitoring.append('Refresh program marks and lots; at least one position is over seven days old.')
    if any(r['missing'] or r['blocked'] for r in rows):
        monitoring.append('Resolve missing basis, holding period, account tax status or unreconciled lots.')
    if any(r['level'] != 'lot' for r in rows):
        monitoring.append('Import exact tax lots before enabling the harvesting overlay.')
    if any(r['taxable'] is False for r in rows):
        monitoring.append('Program account facts conflict with imported retirement-account holdings.')
    results, gaps = [], []
    harvested_ids = {h['security_id'] for h in harvests if fresh(h['date'], today, 30)}
    locks = [{'symbol': h['symbol'], 'sold_on': h['date'],
              'repurchase_after': (date.fromisoformat(h['date']) + timedelta(days=31)).isoformat(),
              'reference': h['reference']} for h in harvests if fresh(h['date'], today, 30)]
    for row in rows:
        if row['taxable'] is False:
            continue
        if row['missing'] or row['blocked'] or row['review_stale']:
            gaps.append(row)
        if row['gain'] is None or row['gain'] >= 0:
            continue
        reasons = list(row['blocked']) + monitoring
        if row['level'] != 'lot':
            reasons.append('Position-level loss estimate; select exact tax lots before a harvest.')
        if row['missing']:
            reasons.append('Missing ' + ', '.join(row['missing']) + '.')
        if -row['gain'] < program['policy']['min_loss']:
            reasons.append('Below the mandate’s minimum loss threshold.')
        pair = next((v for k, v in program.get('replacements', {}).items() if canon(k) == canon(row['symbol'])), {})
        if not pair.get('reference') or not pair.get('rationale') or not fresh(pair.get('as_of'), today, 30):
            reasons.append('Review a replacement and document why it is not substantially identical.')
        for trade in (t for r in reviews for t in r.get('transactions', [])):
            age = (date.fromisoformat(trade['date']) - today).days
            if trade['side'] == 'buy' and -30 <= age <= 30 and canon(trade['symbol']) == canon(row['symbol']):
                reasons.append('Household purchase or scheduled buy falls inside the ±30-day wash window.')
        if any(canon(s) == canon(row['symbol']) for r in reviews for s in r.get('open_buys', [])):
            reasons.append('An open household buy order or reinvestment instruction conflicts with this sale.')
        if row['id'] in harvested_ids:
            reasons.append('A harvest is already recorded against this lot; refresh the broker import.')
        replacement = pair.get('symbol')
        if replacement:
            if canon(replacement) == canon(row['symbol']):
                reasons.append('A security cannot replace itself for harvesting.')
            if any(canon(h['symbol']) == canon(replacement) for h in locks):
                reasons.append('The replacement is inside an existing household repurchase lockout.')
        results.append({**row, 'loss': -row['gain'], 'replacement': replacement,
                        'repurchase_after': (today + timedelta(days=31)).isoformat(),
                        'ready_for_review': not reasons, 'reasons': list(dict.fromkeys(reasons))})
    results.sort(key=lambda r: (-r['loss'], r['id']))
    eligible = sum(r['loss'] for r in results if r['ready_for_review'])
    rate, capacity = program['policy'].get('tax_rate'), program['policy'].get('gain_capacity')
    # A user-reviewed tax-year gain capacity is required; never value all losses
    # at a wage rate or release the shared cash reserve from this scenario.
    tax_value = min(eligible, capacity) * rate if rate is not None and capacity is not None and program['policy']['tax_year'] == today.year else None
    return {'candidates': results, 'needs_review': gaps, 'locks': locks,
            'state': 'awaiting_lots' if not rows or any(r['level'] != 'lot' for r in rows) else
                     'needs_data' if monitoring else 'review_available' if eligible else 'monitoring',
            'monitoring_gaps': list(dict.fromkeys(monitoring)), 'reviewable_losses': round(eligible, 2),
            'potential_tax_value': round(tax_value, 2) if tax_value is not None else None,
            'realized_records': deepcopy(program.get('harvests', [])),
            'notes': ['Potential losses and tax value are scenarios, not cash or recognized tax deductions.',
                      'Wash-sale treatment includes substantially identical securities and household/IRA activity; a ticker check alone cannot establish deductibility.',
                      'Realized harvest records must be reconciled through the normal broker/tax import before they change tax reserves.',
                      'A harvestable loss is not evidence of investment outperformance. Compare after-cost returns and later realization taxes.']}


def review_household(program, raw):
    if raw.get('complete') is not True or not text(raw.get('reference', '')):
        raise ValueError('Confirm household coverage and provide a review reference.')
    trades = raw.get('transactions', [])
    if not isinstance(trades, list) or len(trades) > 10000:
        raise ValueError('Supply up to 10,000 household transactions.')
    if not isinstance(raw.get('open_buys', []), list) or len(raw.get('open_buys', [])) > 5000:
        raise ValueError('Supply up to 5,000 open-buy symbols.')
    normalized = []
    for t in trades:
        if t.get('side') not in {'buy', 'sell'}:
            raise ValueError('Transaction side must be buy or sell.')
        normalized.append({'symbol': symbol(t['symbol']), 'date': dated(t['date']),
                           'side': t['side'], 'account': text(t.get('account', ''), 180)})
    program['wash_review'] = {'as_of': dated(raw.get('as_of', date.today().isoformat())),
                             'reference': text(raw['reference']), 'complete': True,
                             'transactions': normalized,
                             'open_buys': sorted({symbol(s) for s in raw.get('open_buys', [])})}
    event(program, 'household_wash_review', raw['reference'])


def record_harvest(program, model, security_id, fingerprint, reference):
    row = next((r for r in overlay(program, model)['candidates'] if r['id'] == security_id), None)
    if not row or not row['ready_for_review'] or row['fingerprint'] != fingerprint:
        raise ValueError('Refresh this lot and clear its harvest-review gaps before recording a completed harvest.')
    if not text(reference):
        raise ValueError('Provide the broker confirmation reference for the completed sale.')
    program.setdefault('harvests', []).append({'security_id': row['id'], 'fingerprint': fingerprint,
        'symbol': row['symbol'], 'account': row['account'], 'lot': row['lot'],
        'date': date.today().isoformat(), 'estimated_loss_at_review': row['loss'],
        'reference': text(reference), 'tax_reconciled': False})
    event(program, 'recorded_harvest', reference)
