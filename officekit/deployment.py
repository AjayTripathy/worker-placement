"""Funding for an incoming-capital proposal, shared by Home and the planner."""
from officekit.commitments import cash_calendar, pending_deployable, tax_funding
import hashlib
from datetime import date


def _apportion(nets, held):
    """Distribute one reserve over identified pending sources in integer cents."""
    total = sum(nets.values())
    held = min(total, max(0, round(held)))
    reserved = {sid: held * amount // total if total else 0 for sid, amount in nets.items()}
    residual = held - sum(reserved.values())
    for sid in sorted(reserved):
        extra = min(residual, nets[sid] - reserved[sid])
        reserved[sid] += extra
        residual -= extra
    return reserved


def _income_obligations(model, selected, calendar):
    """Only the explicitly bounded period; never infer payroll from lifetime PV."""
    if selected['id'] != (model['d'].get('inflow') or {}).get('id'):
        return 0, []
    terms = model['d'].get('inflow_terms') or {}
    problems = []
    tm = model['d'].get('tax_model') or {}
    if terms.get('character') == 'ordinary' and (tm.get('inflow_id') != selected['id'] or 'rate_ordinary' not in tm):
        problems.append('Confirm an ordinary-income tax rate before allocating this inflow.')
    cadence = terms.get('cadence', 'once')
    if cadence == 'once':
        return 0, problems
    if cadence not in {'monthly', 'quarterly', 'annual'}:
        return 0, problems + ['Choose a supported income cadence.']
    period = terms.get('planning_period') or {}
    try:
        from officekit.commitments import add_months
        start = date.fromisoformat(period['start'])
        end = date.fromisoformat(period['end'])
        stop = add_months(date.fromisoformat(model['d']['as_of']).replace(day=1), 12)
        if start < date.fromisoformat(model['d']['as_of']) or start > end or (end - start).days > 366 or end >= stop:
            raise ValueError()
    except (ValueError, KeyError, TypeError):
        return 0, problems + ['Recurring income needs a dated planning period within the cash calendar. The gross amount is the total for that period.']
    amount = sum(p['amount'] for row in calendar['months'] for p in row['payments']
                 if p['funding_source'] == 'income' and p['source'] != 'tax'
                 and start.isoformat() <= p['date'] <= end.isoformat())
    return round(amount, 2), problems


def page_key(source_id):
    return hashlib.sha256(str(source_id).encode()).hexdigest()[:24]


def href(source_id):
    return '/pages/deployment_' + page_key(source_id) + '.html'


def sources(model):
    """Identified inflows, including received proceeds; never income's capitalized PV."""
    result = {}
    for s in model['assets']:
        if s['category'] == 'cash_pending' and s.get('id'):
            sid = s['id']
            row = result.setdefault(sid, {'id': sid, 'label': s.get('name') or 'Incoming money',
                'gross': 0, 'pending': 0, 'received': 0, 'cash_received': 0, 'eta': s.get('eta'), 'status': 'expected'})
            row['gross'] += s['value']
            row['pending'] += s['value']
    inc = model['d'].get('inflow') or {}
    if inc.get('id') and inc.get('gross', 0) > 0:
        previous = result.get(inc['id'], {})
        result[inc['id']] = {**inc, 'label': previous.get('label', 'Incoming proceeds'), 'eta': model.get('eta')}
    return sorted(result.values(), key=lambda s: (-s['pending'], s['id']))


def source_for(model, source_id=None, key=None):
    choices = sources(model)
    if not source_id and not key and len(choices) == 1:
        return choices[0]
    found = next((s for s in choices if s['id'] == source_id or (key and page_key(s['id']) == key)), None)
    if found is None:
        raise ValueError('Choose an incoming-money source from Capital & Commitments.')
    return found


def for_source(proposal, source):
    if not is_deployment(proposal):
        return False
    bound = proposal.get('deployment_source')
    if bound:
        return bound['id'] == source['id']
    # Older aggregate plans only belong to an inflow when their frozen office
    # contained exactly that one source. Never attach one to a new windfall.
    from officekit import build_model
    original = sources(build_model(proposal['snapshot']['data']))
    return len(original) == 1 and original[0]['id'] == source['id']


def latest(proposals, source):
    return next((p for p in proposals if for_source(p, source) and p['status'] not in {'declined', 'superseded'}), None)


def funding(model, source_id=None):
    calendar = cash_calendar(model)
    if source_id is None and len(sources(model)) == 1:
        source_id = sources(model)[0]['id']
    if source_id is not None:
        all_sources = sources(model)
        selected = source_for(model, source_id)
        taxes = {s['id']: {'pending': 0, 'current': 0} for s in all_sources}
        remaining = {s['id']: s['pending'] for s in all_sources}
        for s in model['sleeves']:
            meta = s.get('meta') or {}
            sid = meta.get('inflow_id')
            if s['category'] != 'tax_reserve' or sid not in taxes:
                continue
            amount = abs(s['value'])
            pending_tax = min(amount, remaining[sid], max(0, meta.get('pending_tax', amount)))
            remaining[sid] -= pending_tax
            taxes[sid]['pending'] += pending_tax
            taxes[sid]['current'] += amount - pending_tax
        # Distribute the cash shortfall once across pending sources, in cents.
        nets = {sid: max(0, round(value * 100)) for sid, value in remaining.items()}
        reservations = _apportion(nets, calendar['shortfall'] * 100)
        floor = round(sum(max(0, float(g.get('amount') or 0)) for g in model['d'].get('goals', [])
                          if g.get('kind') == 'liquidity_floor'), 2)
        floor_reservations = _apportion({sid: cents - reservations[sid] for sid, cents in nets.items()},
                                       max(0, floor - calendar['available']) * 100)
        sid = selected['id']
        current = round(min(max(0, calendar['available'] - floor), max(0, selected['cash_received'] - taxes[sid]['current'])), 2)
        contingent = (nets[sid] - reservations[sid] - floor_reservations[sid]) / 100
        income_expenses, gaps = _income_obligations(model, selected, calendar)
        income_current = min(current, income_expenses)
        income_pending = min(contingent, income_expenses - income_current)
        current = round(current - income_current, 2)
        contingent = round(contingent - income_pending, 2)
        if gaps:
            current, contingent = 0, 0
        return {'source_id': sid, 'pending_gross': selected['pending'], 'pending_tax': round(taxes[sid]['pending'], 2),
                'current_tax': round(taxes[sid]['current'], 2),
                'pending_net': nets[sid] / 100, 'commitment_reserve': reservations[sid] / 100,
                'liquidity_floor': floor, 'liquidity_reserve': floor_reservations[sid] / 100,
                'income_expenses': income_expenses, 'income_reserve_current': income_current,
                'income_reserve_pending': income_pending,
                'income_expense_shortfall': round(income_expenses - income_current - income_pending, 2),
                'blocking_gaps': gaps,
                'current_cash': calendar['available'], 'current_budget': current,
                'proposal_ceiling': round(current + contingent, 2), 'contingent_budget': contingent,
                'sizing_basis': 'Only this inflow funds this strategy. Received proceeds are capped by reconciled net '
                                'receipts and unreserved cash today. Pending proceeds remain conditional, after linked '
                                'tax and their share of unfunded commitments. Cash floors and income-period bills '
                                'are protected before allocation. Unallocated amounts stay in cash. '
                                'Plans record intent and do not reserve or spend balances.'}
    net = round(pending_deployable(model), 2)
    reserve = min(net, calendar['shortfall'])
    amount = round(max(0, net - reserve), 2)
    return {'pending_gross': round(sum(s['value'] for s in model['assets'] if s['category'] == 'cash_pending'), 2),
            'pending_tax': round(tax_funding(model)['pending'], 2),
            'pending_net': net, 'commitment_reserve': reserve,
            'current_cash': calendar['available'], 'current_budget': 0,
            'proposal_ceiling': amount, 'contingent_budget': amount,
            'sizing_basis': 'Incoming proceeds after tax and any unfunded cash commitments. '
                            'Existing cash is not allocated by this plan. All purchases depend on receipt '
                            'and a fresh tax, commitment and suitability check; any unallocated amount stays in cash.'}


def is_deployment(proposal):
    return proposal.get('brief', {}).get('option') == 'new_capital'
