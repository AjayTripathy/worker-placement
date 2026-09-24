"""Charitable intent, funding and explicitly reviewed tax scenarios.

No tax-return engine, disposal, donation or automatic release of tax reserves.
Amounts represent the proposed gift; basis must describe that same gift portion.
"""
from copy import deepcopy
from datetime import date
import math
import re

VEHICLES = {'undecided': 'Compare direct giving and a donor-advised fund',
            'direct': 'Direct to charity', 'daf': 'Donor-advised fund'}
FUNDING = {'undecided': 'Compare cash and appreciated securities', 'cash': 'Cash',
           'appreciated_securities': 'Appreciated publicly traded securities'}
SOURCES = [
    {'title': 'IRS: charitable contributions and property gifts', 'url': 'https://www.irs.gov/publications/p526'},
    {'title': 'IRS: 2026 deduction floor and itemized-deduction limits', 'url': 'https://www.irs.gov/publications/p505'},
    {'title': 'IRS: donor-advised funds', 'url': 'https://www.irs.gov/charities-non-profits/charitable-organizations/donor-advised-funds'},
]
NUMBERS = {'cost_basis', 'deductible_amount', 'deduction_tax_rate', 'capital_gain_tax_rate'}
BOOLEANS = {'recipient_qualified', 'long_term', 'before_sale', 'reserve_cash'}
TEXT = {'recipient', 'symbol', 'tax_review_reference'}


def validate(goal):
    problems = []
    amount = goal.get('amount')
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount <= 0:
        problems.append('Charitable giving needs a positive, finite gift amount.')
    c = goal.get('charitable', {})
    if not isinstance(c, dict):
        return problems + ['Charitable details must be an object.']
    if set(c) - (NUMBERS | BOOLEANS | TEXT | {'vehicle', 'funding'}):
        problems.append('Unknown charitable detail; use the documented giving fields.')
    for key, choices in [('vehicle', VEHICLES), ('funding', FUNDING)]:
        if not isinstance(c.get(key, 'undecided'), str) or c.get(key, 'undecided') not in choices:
            problems.append('Choose a supported charitable ' + key + '.')
    for key in BOOLEANS:
        if key in c and not isinstance(c[key], bool):
            problems.append(key + ' must be true or false.')
    for key in TEXT:
        if key in c and (not isinstance(c[key], str) or len(c[key]) > 1000):
            problems.append(key + ' must be text up to 1,000 characters.')
    if c.get('symbol') and (not isinstance(c['symbol'], str) or not re.fullmatch(r'[A-Z0-9][A-Z0-9.^-]{0,14}', c['symbol'])):
        problems.append('Enter one publicly traded ticker for the proposed gift.')
    for key in NUMBERS:
        value = c.get(key)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            problems.append(key + ' must be a finite, nonnegative number.')
        elif key.endswith('_rate') and value > 1:
            problems.append(key + ' must be between zero and one.')
        elif key == 'deductible_amount' and not problems and value > amount:
            problems.append('The modeled deduction cannot exceed the gift amount.')
    if goal.get('date'):
        try:
            date.fromisoformat(goal['date'])
        except (TypeError, ValueError):
            problems.append('Use a valid gift date in YYYY-MM-DD form.')
    if c.get('reserve_cash') and (c.get('funding') != 'cash' or not goal.get('date')):
        problems.append('A cash reservation needs cash funding and a gift date.')
    return problems


def update(goal, get):
    """The dedicated form is complete; blank optional fields clear old assumptions."""
    result = deepcopy(goal)
    result['label'] = get('label').strip() or goal.get('label') or 'Charitable giving'
    result['date'] = get('date').strip()
    try:
        result['amount'] = float(get('amount').replace(',', '').replace('$', ''))
    except (ValueError, AttributeError):
        raise ValueError('Enter the proposed gift amount.')
    c = {key: get(key) or 'undecided' for key in ('vehicle', 'funding')}
    for key in TEXT:
        if get(key).strip():
            c[key] = get(key).strip().upper() if key == 'symbol' else get(key).strip()
    for key in BOOLEANS:
        if get(key) in {'yes', 'no'}:
            c[key] = get(key) == 'yes'
    for key in NUMBERS:
        if get(key).strip():
            try:
                value = float(get(key).replace(',', '').replace('$', '').replace('%', ''))
            except ValueError:
                raise ValueError('Enter a number for ' + key.replace('_', ' ') + '.')
            c[key] = value / 100 if key.endswith('_rate') else value
    result['charitable'] = c
    errors = validate(result)
    if errors:
        raise ValueError(' '.join(errors))
    return result


def reservation(goal):
    c = goal.get('charitable') or {}
    errors = validate(goal)
    if errors:
        raise ValueError(' '.join(errors))
    if not c.get('reserve_cash'):
        return None
    return {'id': 'charitable:' + goal['id'], 'goal_id': goal['id'], 'source': 'goal_reservation',
            'label': goal.get('label') or 'Charitable gift', 'amount': goal['amount'], 'cadence': 'once',
            'next_due': goal['date'], 'funding_source': 'portfolio', 'portfolio_funded': True,
            'active': True, 'status': 'confirmed', 'estimated': False, 'provenance': 'Explicit charitable goal reservation'}


def assessment(goal, model):
    from officekit.commitments import cash_calendar
    c = goal.get('charitable') or {}
    amount = goal['amount']
    funding = c.get('funding', 'undecided')
    calendar = cash_calendar(model)
    # The goal's own earmark is available to this goal; other commitments stay protected.
    gid = goal.get('id', '')
    own = sum(r['amount'] for row in calendar['months'] for r in row['payments'] if r['id'] == 'charitable:' + gid)
    own += sum(r['amount'] for r in calendar['outside'] if r['id'] == 'charitable:' + gid)
    floor = sum(max(0, float(g.get('amount') or 0)) for g in model['d'].get('goals', []) if g.get('kind') == 'liquidity_floor')
    available_cash = max(0, calendar['remaining'] + own - floor)
    available = available_cash
    if funding == 'appreciated_securities':
        from officekit.donation_securities import inventory
        available = sum(r['market_value'] for r in inventory(model) if c.get('symbol') == r['symbol']
                        and r['taxable'] is not False and not r['blocked'])
    gaps = []
    if funding == 'undecided':
        gaps.append('Choose cash or identify publicly traded securities to donate.')
    if c.get('vehicle', 'undecided') == 'undecided':
        gaps.append('Compare direct giving with a donor-advised fund and select a vehicle.')
    if not goal.get('date'):
        gaps.append('Set the gift date and tax year.')
    if not c.get('recipient') or c.get('recipient_qualified') is not True:
        gaps.append('Confirm the recipient or DAF sponsor and its eligibility.')
    deduction = c.get('deductible_amount')
    deduction_benefit = None
    review = bool(c.get('tax_review_reference'))
    if review and c.get('recipient_qualified') is True and goal.get('date') and funding != 'undecided' and c.get('vehicle', 'undecided') != 'undecided' and deduction is not None and c.get('deduction_tax_rate') is not None:
        deduction_benefit = round(deduction * c['deduction_tax_rate'], 2)
    else:
        gaps.append('Record the usable deduction after AGI limits, other gifts, the applicable floor and itemization; enter its reviewed effective tax rate and review reference.')
    avoided_gain = avoided_tax = None
    if funding == 'appreciated_securities':
        if not c.get('symbol') or available < amount:
            gaps.append('Verify sufficient owned shares and the exact gift lots; a ticker is not a lot instruction.')
        if c.get('long_term') is not True or c.get('before_sale') is not True:
            gaps.append('Verify a holding period over one year and transfer before sale or any binding sale obligation.')
        if (review and c.get('recipient_qualified') is True and c.get('long_term') is True
                and c.get('before_sale') is True and c.get('cost_basis') is not None and available >= amount):
            avoided_gain = round(max(0, amount - c['cost_basis']), 2)
            if c.get('capital_gain_tax_rate') is not None:
                avoided_tax = round(avoided_gain * c['capital_gain_tax_rate'], 2)
        if avoided_tax is None:
            gaps.append('Record basis for the gift portion and a reviewed applicable capital-gains tax rate.')
    from officekit.donation_securities import shortlist
    return {'goal_id': gid, 'label': goal.get('label') or 'Charitable giving', 'amount': amount,
            'securities': shortlist(goal, model),
            'date': goal.get('date'), 'vehicle': c.get('vehicle', 'undecided'), 'funding': funding,
            'available_today': round(available, 2), 'funding_ratio': available / amount if amount else 0,
            'cash_reserved': bool(c.get('reserve_cash')), 'deductible_amount': deduction,
            'deduction_tax_benefit': deduction_benefit, 'embedded_gain_not_realized': avoided_gain,
            'avoided_gain_tax': avoided_tax, 'tax_review_reference': c.get('tax_review_reference'),
            'terms': deepcopy(c), 'gaps': gaps, 'sources': SOURCES,
            'limitations': ['Tax figures are scenarios using entered, reviewed assumptions, not a calculated tax return.',
                           'A deduction is not a tax credit. Gifts do not automatically reduce the windfall tax reserve or increase deployment cash.',
                           'Avoided gain applies only to donated shares; it does not erase gains already realized elsewhere.',
                           'Review all gifts together by tax year so deduction headroom is not counted twice.',
                           'A DAF contribution leaves your ownership; later grants do not create a second contribution deduction.']}


def plans(model):
    return [assessment(g, model) for g in model['d'].get('goals', []) if g.get('kind') == 'charitable']
