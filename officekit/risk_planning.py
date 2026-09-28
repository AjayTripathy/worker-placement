"""Private household loss capacity and dated funding stresses.

One deterministic model serves Risk, Scenarios and deployment comparisons. The
recommended limit is conditional planning capacity, never a maximum possible
loss or a probability. Defaults are visible assumptions; absent facts stay absent.
"""
from copy import deepcopy
from datetime import date
import math

from officekit.commitments import add_months, cash_calendar, tax_funding

VERSION = 1
MARKETABLE = {'public_equity', 'single_name_equity', 'direct_index',
              'municipal_credit', 'fixed_income', 'alpha_market_neutral', 'options_overlay'}
FIELDS = {
    'annual_spending': (0, 1e12), 'annual_income': (0, 1e12),
    'horizon_years': (1, 60), 'reserve_months': (0, 60),
    'income_interruption_months': (0, 120), 'buffer_pct': (0, 50),
    'comfort_loss_pct': (0, 100), 'uninsured_loss': (0, 1e12),
}


def number(value, default=0):
    try:
        n = float(value)
        return n if math.isfinite(n) else default
    except (ValueError, TypeError):
        return default


def validate(policy):
    if not isinstance(policy, dict) or set(policy) - (set(FIELDS) | {'income_end_date', 'goal_priority', 'confirmed_at'}):
        raise ValueError('Unrecognized risk planning input')
    for k, (lo, hi) in FIELDS.items():
        if k in policy and (isinstance(policy[k], bool) or not lo <= number(policy[k], -1) <= hi):
            raise ValueError(k.replace('_', ' ') + ' is outside its supported range')
    if policy.get('income_end_date'):
        date.fromisoformat(policy['income_end_date'])
    priorities = policy.get('goal_priority', {})
    if not isinstance(priorities, dict) or any(v not in {'protect', 'flexible'} for v in priorities.values()):
        raise ValueError('Choose protect or flexible for each goal')
    return policy


def inputs(m):
    d = m['d']
    saved = validate(d.get('risk_policy') or {})
    commitments = [c for c in d.get('commitments', []) if c.get('active', True)]
    spending = sum(number(c.get('annual_amount')) for c in commitments if c.get('cadence') != 'once')
    goals = [g for g in d.get('goals', []) if not g.get('implicit')]
    retirement = max([number(g.get('annual_spending')) for g in goals
                      if g.get('kind') == 'retirement' and g.get('spending_basis', 'household_total') == 'household_total'] or [0])
    spending = max(spending, retirement)
    defaults = {'annual_spending': spending, 'annual_income': 0, 'horizon_years': 30,
                'reserve_months': 24 if d.get('profile', {}).get('decumulating') else 12,
                'income_interruption_months': 12, 'buffer_pct': 10, 'uninsured_loss': 0}
    values = {**defaults, **saved}
    rows = []
    for k, value in defaults.items():
        source = ('Confirmed in risk planning' if k in saved else
                  'Goals and scheduled household bills; confirm essential spending' if k == 'annual_spending' else
                  'Unknown; no future income credited' if k == 'annual_income' else
                  'Unknown; no insured or uninsured loss assumed' if k == 'uninsured_loss' else
                  'Planning assumption; editable')
        rows.append({'key': k, 'value': values[k], 'source': source, 'confirmed': k in saved})
    gaps = []
    if 'annual_spending' not in saved:
        gaps.append('Confirm essential annual household spending, including housing and scheduled recurring bills.')
    if 'annual_income' not in saved:
        gaps.append('Confirm reliable after-tax income; the calculation currently credits none.')
    if values['annual_income'] and not values.get('income_end_date'):
        gaps.append('Confirm when reliable income ends; until then it is excluded.')
    if any(c.get('estimated') or c.get('schedule_estimated') for c in commitments):
        gaps.append('Some payment amounts or dates are estimated. Review the cash calendar.')
    if any(s['category'] in MARKETABLE | {'cash'} and not accessible(s) for s in m['sleeves']):
        gaps.append('Restricted or mixed-account pools are excluded; split accessible accounts before counting their funds.')
    if any(s.get('kind') == 'liability' and s['category'] not in {'real_estate_debt', 'tax_reserve'} for s in m['sleeves']):
        gaps.append('Other liabilities need explicit payment schedules; add their repayments to the cash calendar.')
    if any(s.get('_sync_stale') for s in m['sleeves']):
        gaps.append('Some holdings are stale. Refresh them before relying on the loss limit.')
    return {'values': values, 'rows': rows, 'gaps': gaps, 'goals': goals,
            'source_date': d['as_of'], 'version': VERSION}


def accessible(s):
    from officekit.donation_securities import RETIREMENT
    def restricted(row):
        account = str(row.get('account_type', '')).lower().replace('_', ' ')
        return (any(row.get(k) for k in ('restricted', 'pledged', 'nontransferable'))
                or account in {'daf', 'charitable', 'trust restricted'} or bool(RETIREMENT.search(account)))
    meta = s.get('meta') or {}
    holdings = s.get('holdings', [])
    accounts = [a for h in holdings for a in h.get('accounts', [])]
    # A mixed restricted pool needs a split before household access is assumed.
    return not any(restricted(row) for row in [s, meta] + holdings + accounts)


def resources(m):
    cash = marketable = 0.0
    excluded = []
    for s in m['sleeves']:
        cat = s['category']
        if s.get('kind') != 'asset':
            continue
        if cat in {'cash'} | MARKETABLE and accessible(s):
            if cat == 'cash':
                cash += s['value']
            else:
                marketable += s['value']  # signed short values remain liabilities
        elif s['value'] > 0:
            excluded.append({'name': s['name'], 'amount': s['value'], 'reason': 'Pending, illiquid, restricted or non-spendable'})
    return {'cash': cash, 'marketable': marketable, 'total': cash + marketable, 'excluded': excluded}


def schedule(m, months, *, scenario=None, include_pending=False):
    """Monthly household uses, counting recurring bills inside total spending.

    Includes all funding sources: losing income does not make an income-funded
    mortgage disappear. Pending cash appears only on an explicit dated scenario.
    A goal already represented by a reservation is counted only once.
    """
    sc = scenario or {}
    config = inputs(m)
    v = config['values']
    cal = cash_calendar(m, months=months)
    start = date.fromisoformat(m['d']['as_of']).replace(day=1)
    today = date.fromisoformat(m['d']['as_of'])
    scheduled = {r['month']: r for r in cal['months']}
    from officekit.goals import apply_goal_ov
    goals = apply_goal_ov(config['goals'], sc.get('goal_ov', {}))
    priorities = v.get('goal_priority', {})
    protected = [g for g in goals if priorities.get(g.get('id'), 'protect') == 'protect']
    reserved_ids = {c.get('goal_id') for c in m['d'].get('commitments', []) if c.get('active', True)}
    by_goal = {}
    carrying = []
    assumptions = []
    undated = []
    floor = max([number(g.get('amount')) for g in protected if g['kind'] == 'liquidity_floor'] or [0])
    floor = max(floor, v['annual_spending'] / 12 * v['reserve_months'])
    for g in protected:
        if g['kind'] not in {'spending', 'charitable'} or g.get('id') in reserved_ids:
            continue
        # Giving from an already irrevocably funded vehicle cannot be spent twice.
        if g['kind'] == 'charitable' and (g.get('charitable') or {}).get('funding') == 'existing_daf':
            continue
        when = g.get('date')
        amount = number(g.get('amount'))
        from officekit.goal_projection import is_financed_purchase, project
        if is_financed_purchase(g):
            projection = project(g, [], m['d']['as_of'], m)
            amount = projection['cash_needed']
            carrying.append((when[:7] if when else today.isoformat()[:7], projection['annual_carry']))
            assumptions.append(g['label'] + ': modeled down payment, closing and liquidation tax, plus annual financing/carry; confirm financing terms.')
        if not when:
            undated.append({'label': g['label'], 'amount': amount})
        else:
            month = max(when[:7], today.isoformat()[:7])
            by_goal.setdefault(month, []).append({'label': g['label'], 'amount': amount, 'id': g.get('id')})
    held = cal['held'] + sum(g['amount'] for g in undated)
    # A dated protected goal outside the horizon remains reserved, not forgotten.
    last = add_months(start, months).isoformat()[:7]
    held += sum(g['amount'] for month, gs in by_goal.items() if month >= last for g in gs)
    income_end = v.get('income_end_date') or ''
    interrupt = int(sc.get('income_interruption_months', 0))
    delay = int(sc.get('pending_delay_months', 0))
    inflation = number(sc.get('annual_inflation_pct')) / 100
    inflows, notes = {}, assumptions
    cadence = {c['id']: c.get('cadence') for c in m['d'].get('commitments', [])}
    def recurring_payment(p):
        return cadence.get(p['id']) != 'once' and p['source'] in {'lifestyle', 'mortgage', 'property_tax', 'recurring_expense'}
    if include_pending:
        from officekit.deployment import sources
        taxes = tax_funding(m)['pending']
        total_pending = sum(s['pending'] for s in sources(m))
        for s in sources(m):
            if s['pending'] <= 0:
                continue
            eta = sc.get('pending_date') or s.get('eta') or ''
            try:
                eta_date = date.fromisoformat(eta if len(eta) == 10 else eta + '-01')
                eta_date = max(today, add_months(eta_date, delay))
            except ValueError:
                notes.append('No exact receipt date for ' + s['label'] + '; pending proceeds excluded.')
                continue
            net = max(0, s['pending'] - taxes * s['pending'] / total_pending) if total_pending else 0
            inflows[eta_date.isoformat()[:7]] = inflows.get(eta_date.isoformat()[:7], 0) + net
    rows = []
    for i in range(months):
        month = add_months(start, i).isoformat()[:7]
        payments = scheduled[month]['payments']
        recurring = sum(p['amount'] for p in payments if recurring_payment(p))
        dated = sum(p['amount'] for p in payments if not recurring_payment(p))
        retirement = max([number(g.get('annual_spending')) for g in protected if g['kind'] == 'retirement'
                          and g.get('spending_basis', 'household_total') == 'household_total'
                          and (not g.get('date') or g['date'][:7] <= month)] or [0])
        extra = sum(number(g.get('annual_amount', g.get('amount'))) for g in protected if g['kind'] == 'expense')
        extra += sum(number(g.get('annual_spending')) for g in protected if g['kind'] == 'retirement'
                     and g.get('spending_basis') == 'additional' and (not g.get('date') or g['date'][:7] <= month))
        extra += sum(cost for when, cost in carrying if when <= month)
        living = max(v['annual_spending'] / 12, recurring, retirement / 12) + extra / 12
        living *= (1 + inflation) ** (i / 12)
        income = v['annual_income'] / 12 if income_end and month <= income_end[:7] and i >= interrupt else 0
        if income and month == income_end[:7]:
            import calendar
            income *= date.fromisoformat(income_end).day / calendar.monthrange(int(month[:4]), int(month[5:]))[1]
        goals_due = by_goal.get(month, [])
        outflow = living + dated + sum(g['amount'] for g in goals_due)
        if i == 0:
            outflow += number(sc.get('uninsured_loss', 0))
        rows.append({'month': month, 'spending': round(living, 2), 'payments': payments,
                     'goals_due': goals_due, 'outflow': round(outflow, 2), 'income': round(income, 2),
                     'pending': round(inflows.get(month, 0), 2)})
    return {'months': rows, 'held': held, 'floor': floor, 'notes': notes, 'undated_goals': undated}


def capacity(m):
    config = inputs(m)
    v = config['values']
    money = resources(m)
    plan = schedule(m, int(v['horizon_years'] * 12), scenario={'income_interruption_months': int(v['income_interruption_months'])})
    cumulative = peak = 0.0
    binding = None
    for row in plan['months']:
        cumulative += row['outflow'] - row['income']
        if cumulative >= peak:
            peak = cumulative
            binding = row
    required = max(0, plan['held'] + plan['floor'] + peak + v['uninsured_loss'])
    financial = max(0, money['total'] - required)
    recommended = financial * (1 - v['buffer_pct'] / 100)
    if 'comfort_loss_pct' in v:
        recommended = min(recommended, max(0, money['total']) * v['comfort_loss_pct'] / 100)
    return {'version': VERSION, 'inputs': config, 'resources': money, 'required_capital': round(required, 2),
            'financial_capacity': round(financial, 2), 'recommended_loss': round(recommended, 2),
            'recommended_loss_pct': round(100 * recommended / money['total'], 2) if money['total'] > 0 else 0,
            'funding_gap': round(max(0, required - money['total']), 2),
            'protected_reserve': round(plan['floor'], 2), 'held': round(plan['held'], 2),
            'binding_month': binding['month'] if binding else None,
            'binding_goals': [g['label'] for g in (binding or {}).get('goals_due', [])],
            'status': 'provisional' if config['gaps'] else 'modeled',
            'method': 'Zero real investment growth over the chosen horizon; dated bills, protected goals and reliable income are counted together. '
                      'Home equity, private assets, pending proceeds and restricted assets cannot support this loss limit. '
                      'Recurring bills are included within total household spending, not added again. The largest cumulative funding need sets the limit. '
                      'This is conditional planning capacity, not a guaranteed safe loss or maximum possible drawdown.'}


def stress(m, scenario, *, include_pending=False, months=24):
    from officekit.render_scenarios import _move
    sc = {'shocks': {}, **(scenario or {})}
    sc.setdefault('income_interruption_months', 12 if sc.get('key') == 'income_shock' else 0)
    months = int(sc.get('horizon_months', months))
    plan = schedule(m, months, scenario=sc, include_pending=include_pending)
    offset_loss = number((m.get('tax') or {}).get('offset')) if sc.get('tax_ov', {}).get('no_offset') else 0
    if offset_loss:
        plan['held'] += offset_loss
        plan['notes'].append('Failed loss offsets add an undated tax reserve of $' + format(offset_loss, ',.0f') + '; confirm payment timing. No extra harvesting benefit is credited.')
    money = resources(m)
    cash = money['cash'] - plan['held']
    haircut = number(sc.get('sale_haircut_pct'), 2) / 100
    marketable = sum(s['value'] * (1 + _move(s, sc)) for s in m['assets']
                     if s['category'] in MARKETABLE and accessible(s))
    marketable = marketable - max(0, marketable) * haircut
    liquid = cash + marketable
    first_cash = first_gap = first_floor = None
    rows = []
    for row in plan['months']:
        change = row['income'] + row['pending'] - row['outflow']
        cash += change
        liquid += change
        r = {**row, 'cash_remaining': round(cash, 2), 'liquid_remaining': round(liquid, 2),
             'funding_gap': round(max(0, -liquid), 2), 'reserve_gap': round(max(0, plan['floor'] - liquid), 2)}
        rows.append(r)
        if cash < 0 and first_cash is None:
            first_cash = row['month']
        if liquid < 0 and first_gap is None:
            first_gap = row['month']
        if liquid < plan['floor'] and first_floor is None:
            first_floor = row['month']
    housing_months = [r['month'] for r in rows if r['funding_gap'] and any(p['source'] == 'mortgage' for p in r['payments'])]
    return {'scenario': sc.get('key', 'baseline'), 'months': rows, 'cash_sale_month': first_cash,
            'first_shortfall': first_gap, 'first_reserve_breach': first_floor,
            'housing_payment_at_risk': housing_months[0] if housing_months else None,
            'worst_gap': max([r['funding_gap'] for r in rows] or [0]),
            'starting_liquid': round(money['cash'] - plan['held'] + marketable, 2),
            'loss_of_accessible_assets': round(money['marketable'] - marketable + offset_loss, 2),
            'portfolio_mark_change': round(sum(s['value'] * _move(s, sc) for s in m['sleeves']) - offset_loss, 2),
            'reserve': plan['floor'], 'notes': plan['notes'],
            'basis': 'Monthly payments at shocked marks, no recovery or investment income assumed. '
                     'Selling marketable holdings is hypothetical; sale taxes, actual collateral calls and execution delays need account-level terms. '
                     'Pending cash is conditional and never recorded as a receipt.'}


def apply_allocations(m, allocations, *, cash_available=0):
    """A private hypothetical portfolio, conserving funding; never changes NAV files."""
    from officekit import build_model
    d = deepcopy(m['d'])
    amount = sum(number(a.get('amount')) for a in allocations)
    if amount < 0 or any(number(a.get('amount'), -1) < 0 for a in allocations):
        raise ValueError('Allocation amounts must be nonnegative')
    cash = sum(s['value'] for s in d['sleeves'] if s['category'] == 'cash' and accessible(s))
    if amount > cash + cash_available + .01:
        raise ValueError('Proposed deployment exceeds its available cash')
    if cash_available:
        d['sleeves'].append({'id': 'risk-comparison-receipt', 'name': 'Conditional net receipt', 'kind': 'asset',
                             'category': 'cash', 'value': cash_available, 'beta': {}, '_confidence': 'assumption'})
    remaining = amount
    for s in d['sleeves']:
        if s['category'] == 'cash' and accessible(s):
            take = min(max(0, s['value']), remaining)
            s['value'] -= take
            remaining -= take
    gaps = []
    for i, a in enumerate(allocations):
        from officekit.importers import FUND_MAP
        from officekit.betas import default_beta
        symbol = str(a.get('symbol', '')).upper()
        known, style = FUND_MAP.get(symbol, (None, None))
        cat = a.get('category') or known or ('single_name_equity' if a.get('instrument') == 'stock' else None)
        if not cat or a.get('instrument') == 'options':
            raise ValueError(symbol + ': classify the instrument and supply a verified risk model before comparing deployment; options need contract-level stresses')
        beta = a.get('beta')
        if beta is None:
            beta = default_beta(cat, style)
            gaps.append(str(a.get('symbol') or cat) + ': generic category shock; ticker-specific factor estimate unverified')
        d['sleeves'].append({'id': 'risk-allocation-' + str(i), 'name': a.get('symbol') or cat,
                            'kind': 'asset', 'category': cat, 'value': number(a.get('amount')),
                            'beta': beta, '_confidence': 'assumption'})
    return build_model(d), gaps


def compare(m, allocations, scenarios, *, cash_available=0):
    after, gaps = apply_allocations(m, allocations, cash_available=cash_available)
    before, _ = apply_allocations(m, [], cash_available=cash_available)
    rows = []
    before_capacity, after_capacity = capacity(before), capacity(after)
    for sc in scenarios:
        a, b = stress(before, sc), stress(after, sc)
        rows.append({'name': sc['name'], 'before': a, 'after': b,
                     'exceeds_loss_budget': b['loss_of_accessible_assets'] > after_capacity['recommended_loss'],
                     'additional_stressed_loss': round(b['loss_of_accessible_assets'] - a['loss_of_accessible_assets'], 2)})
    gaps = list(dict.fromkeys(gaps))
    return {'before': before_capacity, 'after': after_capacity, 'scenarios': rows, 'gaps': gaps,
            'conditional_receipt': cash_available,
            'basis': 'Same assets, obligations and conditional net receipt in both portfolios; compare holding cash with allocating it. '
                     'No receipt, trade or tax saving is recorded. Harvesting is not assumed to protect principal.'}


def proposal_comparisons(proposal):
    """Snapshot-based current and conditional deployment, with no cash double count."""
    from officekit.capital_planning import model_from_snapshot
    from officekit.render_scenarios import applicable_scenarios
    model = model_from_snapshot(proposal)
    scenarios = [s for s in applicable_scenarios(model) if s.get('enabled', True)]
    out = []
    for name, field, pending in [('Available cash', 'amount', False), ('After conditional receipt', 'contingent_amount', True)]:
        allocations = [dict(a, amount=number(a.get(field)) + (number(a.get('amount')) if pending else 0))
                       for a in proposal.get('basket', [])]
        allocations = [a for a in allocations if a['amount'] > 0]
        if not allocations or pending and not any(number(a.get('contingent_amount')) for a in proposal.get('basket', [])):
            continue
        funding = proposal.get('funding') or {}
        receipt = max(0, number(funding.get('pending_gross')) - number(funding.get('pending_tax'))) if pending else 0
        if pending:
            # A bound source's unallocated reserves also arrive, but remain held.
            receipt = max(receipt, number(funding.get('contingent_budget')))
        try:
            result = compare(model, allocations, scenarios, cash_available=receipt)
        except ValueError as exc:
            out.append({'label': name, 'error': str(exc)})
        else:
            out.append({'label': name, **result})
    return out


def beta_comparisons(model, view):
    from officekit.render_scenarios import applicable_scenarios
    scenarios = [s for s in applicable_scenarios(model) if s.get('enabled', True)]
    rows = view['basket']['rows']
    out = []
    for label, pending in [('Available cash', False), ('After conditional receipt', True)]:
        allocations = [{'symbol': r['symbol'], 'instrument': 'stock', 'category': 'direct_index',
                        'amount': r['current'] + (r['pending'] if pending else 0)} for r in rows]
        allocations = [a for a in allocations if a['amount'] > 0]
        if not allocations or pending and view['budget']['pending'] <= 0:
            continue
        try:
            out.append({'label': label, **compare(model, allocations, scenarios,
                        cash_available=view['budget']['pending'] if pending else 0)})
        except ValueError as exc:
            out.append({'label': label, 'error': str(exc)})
    return out
