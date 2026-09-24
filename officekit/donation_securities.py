"""Private, basis-aware donation shortlist from the same owned holdings as NAV.

Reviews supplement missing facts for a specific custody snapshot. They never
overwrite imported facts or treat absent basis as zero. No transfer instructions.
"""
from copy import deepcopy
from datetime import date, datetime
import hashlib
import json
import math
import re

PUBLIC = {'public_equity', 'single_name_equity', 'direct_index', 'fixed_income', 'municipal_credit'}
SECURITIES = {'STK', 'ETF', 'FUND', 'US_EQUITY', 'ADR', 'BOND', 'BILL', 'NOTE', 'TBOND', 'TBILL', 'FIXED'}
RETIREMENT = re.compile(r'\b(?:ira|roth|401\w*|403\w*|457\w*|pension|retirement)\b', re.I)
LIMIT = 40


def number(value):
    if value is None or value == '' or isinstance(value, bool):
        return None
    try:
        n = float(str(value).replace(',', '').replace('$', '').strip())
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def _date(value):
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%Y%m%d'):
        try:
            return datetime.strptime(str(value or '')[:10], fmt).date()
        except ValueError:
            pass
    return None


def _term(row, as_of):
    opened = _date(row.get('open') or row.get('acquired') or row.get('date_acquired'))
    today = _date(as_of)
    if opened and today:
        try:
            anniversary = opened.replace(year=opened.year + 1)
        except ValueError:
            anniversary = date(opened.year + 1, 2, 28)
        return today > anniversary
    if row.get('term') in {'LT', 'ST'}:
        return row['term'] == 'LT'
    return row.get('long_term') if isinstance(row.get('long_term'), bool) else None


def inventory(model):
    """Keep accounts and lots separate; never count an aggregate beside its lots."""
    data = model.get('d', model)
    as_of = data.get('as_of', '')
    reviews = data.get('security_basis_reviews') or {}
    result = []
    for si, sleeve in enumerate(model.get('assets', data.get('sleeves', []))):
        if sleeve.get('category') not in PUBLIC:
            continue
        holdings = sleeve.get('holdings') or []
        custody = (sleeve.get('meta') or {}).get('custody_row')
        if not holdings and custody:
            holdings = [custody]
        for hi, holding in enumerate(holdings):
            sym = str(holding.get('symbol') or holding.get('company') or '').strip().upper()
            if not re.fullmatch(r'[A-Z0-9][A-Z0-9.^-]{0,14}', sym):
                continue
            accounts = holding.get('accounts') or [holding]
            for ai, account in enumerate(accounts):
                account_name = str(account.get('account') or holding.get('account') or sleeve.get('name') or 'Account unrecorded')
                source = account.get('source') or account.get('source_id') or holding.get('source_id') or 'office holding'
                value = number(account.get('value', account.get('mv', account.get('amount'))))
                kind = str(account.get('sec_type') or holding.get('sec_type') or 'STK').upper()
                if kind not in SECURITIES or value is None or value <= 0 or (number(account.get('qty')) or 0) < 0:
                    continue
                lots = account.get('lots') or []
                lot_values = [number(lot.get('value', lot.get('mv'))) for lot in lots]
                complete = not lots or (all(v is not None for v in lot_values)
                                       and abs(sum(lot_values) - value) <= max(.02, len(lots) * .02))
                lot_bases = [number(lot.get('cost')) for lot in lots]
                total_basis = number(account.get('cost_basis'))
                if lots and total_basis is not None and all(b is not None for b in lot_bases):
                    complete = complete and abs(sum(lot_bases) - total_basis) <= max(.02, len(lots) * .02)
                # Unreconciled lots remain a visible gap rather than invented position lots.
                parts = lots if lots and complete else [account]
                account_fingerprint = digest([as_of, holding, account])
                for li, part in enumerate(parts):
                    is_lot = bool(lots and complete)
                    raw_value = number(part.get('value', part.get('mv', part.get('amount'))))
                    if raw_value is None or raw_value <= 0 or (number(part.get('qty')) or 0) < 0:
                        continue
                    basis = number(part.get('cost' if is_lot else 'cost_basis'))
                    if basis is not None and basis < 0:
                        basis = None
                    taxable = account.get('taxable', holding.get('taxable'))
                    taxable = taxable if isinstance(taxable, bool) else None
                    account_type = str(account.get('account_type') or holding.get('account_type') or (sleeve.get('meta') or {}).get('account_type') or '')
                    if RETIREMENT.search(account_name + ' ' + account_type):
                        taxable = False
                    elif account_type.lower() in {'taxable', 'individual_taxable', 'joint_taxable'}:
                        taxable = True
                    term = _term(part, as_of)
                    key = digest([sleeve.get('id') or sleeve['name'], si, hi, sym, account_name, source, ai,
                                  part.get('taxlot_id') or part.get('lot_id') or li])[:24]
                    fingerprint = digest([account_fingerprint, part])
                    review = reviews.get(key) or {}
                    fresh = review.get('fingerprint') == fingerprint
                    imported_basis, imported_term, imported_taxable = basis, term, taxable
                    if fresh:
                        if basis is None:
                            basis = number(review.get('cost_basis'))
                        if term is None:
                            term = review.get('long_term') if isinstance(review.get('long_term'), bool) else None
                        if taxable is None:
                            taxable = review.get('taxable') if isinstance(review.get('taxable'), bool) else None
                    blocked = []
                    if not complete:
                        blocked.append('Imported lots do not reconcile to this position; refresh the lot statement.')
                    if account.get('value_is_cost') or holding.get('value_is_cost'):
                        blocked.append('Market value is a cost placeholder; import a current market value.')
                    if str(account.get('ccy') or holding.get('ccy') or 'USD').upper() != 'USD':
                        blocked.append('Convert the market value and basis to the office base currency first.')
                    if any(part.get(k) or account.get(k) or holding.get(k) for k in ('pledged', 'restricted', 'nontransferable')):
                        blocked.append('Restriction or pledge recorded; confirm transfer eligibility separately.')
                    value_now = raw_value * sleeve.get('_goal_shock_scale', 1)
                    gain = value_now - basis if basis is not None else None
                    missing = []
                    if basis is None:
                        missing.append('cost_basis')
                    if term is None:
                        missing.append('long_term')
                    if taxable is None:
                        missing.append('taxable')
                    result.append({'id': key, 'fingerprint': fingerprint, 'symbol': sym, 'account': account_name,
                        'source': source, 'as_of': part.get('as_of') or account.get('as_of') or holding.get('as_of') or as_of,
                        'lot': part.get('taxlot_id') or part.get('lot_id') or (str(li + 1) if is_lot else None),
                        'level': 'lot' if is_lot else 'position', 'market_value': round(value_now, 2),
                        'cost_basis': basis, 'gain': round(gain, 2) if gain is not None else None,
                        'gain_fraction': gain / value_now if gain is not None and value_now > 0 else None,
                        'long_term': term, 'taxable': taxable, 'missing': missing, 'blocked': blocked,
                        'review_stale': bool(review) and not fresh, 'review_reference': review.get('reference') if fresh else None,
                        'imported_basis': imported_basis, 'imported_term': imported_term, 'imported_taxable': imported_taxable,
                        'eligible': not blocked and not missing and term is True and taxable is True and gain is not None and gain > 0})
    return result


def shortlist(goal, model):
    rows = inventory(model)
    candidates = sorted((r for r in rows if r['eligible']), key=lambda r: (-r['gain_fraction'], -r['gain'], r['id']))
    needs_review = sorted((r for r in rows if (r['missing'] or r['review_stale'] or r['blocked']) and r['taxable'] is not False),
                          key=lambda r: (-r['market_value'], r['id']))
    needs_ids = {r['id'] for r in needs_review}
    reviewed = [r for r in rows if r['review_reference'] and r['id'] not in needs_ids]
    remaining = round(goal['amount'], 2)
    mix = []
    for r in candidates[:LIMIT]:
        amount = round(min(remaining, r['market_value']), 2)
        if amount <= 0:
            break
        basis = round(r['cost_basis'] * amount / r['market_value'], 2)
        mix.append({**r, 'gift_amount': amount, 'gift_basis': basis, 'gift_gain': round(amount - basis, 2),
                    'estimate': r['level'] != 'lot' and amount < r['market_value']})
        remaining = round(remaining - amount, 2)
    return {'as_of': model.get('d', model).get('as_of'), 'candidates': candidates[:LIMIT],
            'needs_review': needs_review[:LIMIT], 'suggested_mix': mix, 'unfilled': remaining,
            'reviewed': reviewed[:LIMIT],
            'candidate_count': len(candidates), 'review_count': len(needs_review), 'inventory_count': len(rows),
            'excluded_count': sum(not r['eligible'] and r['id'] not in needs_ids for r in rows),
            'omitted': max(0, len(candidates) - LIMIT) + max(0, len(needs_review) - LIMIT),
            'method': 'Ranks confirmed taxable, long-term appreciated holdings by embedded gain per dollar donated. This is a tax-efficiency shortlist; portfolio fit and sponsor acceptance still need review.',
            'limitations': ['Position-level partial gifts use proportional basis estimates; confirm exact lots with the custodian before selecting shares.',
                            'Missing basis is unknown, never zero. Reviews must be refreshed when the source snapshot changes.',
                            'Each goal is a separate comparison; the same holdings cannot fund multiple gifts simultaneously.',
                            'Market values are portfolio marks, not final charitable deduction valuations.']}


def record_review(answers, model, security_id, fingerprint, fields):
    row = next((r for r in inventory(model) if r['id'] == security_id), None)
    if not row or row['fingerprint'] != fingerprint:
        raise ValueError('This holding changed. Reload the giving plan and review the latest source data.')
    reference = (fields.get('reference') or '').strip()
    if not reference or len(reference) > 1000:
        raise ValueError('Add a statement or review reference, up to 1,000 characters.')
    prior = (answers.get('security_basis_reviews') or {}).get(security_id) or {}
    review = deepcopy(prior) if prior.get('fingerprint') == fingerprint else {}
    review.update(fingerprint=fingerprint, reference=reference, reviewed_at=date.today().isoformat())
    if fields.get('cost_basis', '').strip():
        basis = number(fields['cost_basis'])
        if basis is None or basis < 0:
            raise ValueError('Enter a finite, nonnegative total basis; blank means unknown.')
        if row['imported_basis'] is not None and basis != row['imported_basis']:
            raise ValueError('Imported basis must be corrected at its source; this form only supplements missing facts.')
        review['cost_basis'] = basis
    else:
        review.pop('cost_basis', None)
    for field, imported in [('long_term', 'imported_term'), ('taxable', 'imported_taxable')]:
        value = fields.get(field, '')
        if value not in {'', 'yes', 'no'}:
            raise ValueError('Choose Yes, No or Not confirmed.')
        if value:
            flag = value == 'yes'
            if row[imported] is not None and row[imported] != flag:
                raise ValueError('Correct conflicting imported facts at their source before using this holding.')
            review[field] = flag
        else:
            review.pop(field, None)
    updated = deepcopy(answers)
    updated.setdefault('security_basis_reviews', {})[security_id] = review
    return updated
