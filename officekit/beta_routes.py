"""Tenant-independent form actions for private beta programs."""
from copy import deepcopy
from datetime import date
import csv
import io
import json

from officekit import beta_programs as B


def handle(folder, get, build, model_for_answers):
    from officekit.mandates import require_revision
    answers = json.loads((folder / 'answers.json').read_text(encoding="utf-8"))
    require_revision(answers, get('revision'))
    model = model_for_answers(answers, folder)
    action, pid = get('action'), get('pid')
    old = B.programs(answers).get(pid)
    p = deepcopy(old) if old else None
    if action == 'security-review':
        from officekit.donation_securities import record_review
        if not p:
            raise ValueError('Choose a saved beta program.')
        updated = record_review(answers, model, get('security_id'), get('fingerprint'),
                               {k: get(k) for k in ('cost_basis', 'long_term', 'taxable', 'reference')})
        build(updated, folder)
        return pid
    if action in {'create', 'edit'}:
        if action == 'edit' and not old:
            raise ValueError('Choose a saved beta program.')
        policy = {
            'mode': 'long_only', 'benchmark': (old or {}).get('policy', {}).get('benchmark', 'SPTM'),
            'max_names': get('max_names') or 150, 'max_weight': B.number(get('max_weight') or 2.5, .2, 50) / 100,
            'horizon_years': get('horizon_years') or 5, 'fee_bps': get('fee_bps') or None,
            'min_loss': get('min_loss') or 1000, 'tax_rate': B.number(get('tax_rate'), 0, 70) / 100 if get('tax_rate') else None,
            'gain_capacity': get('gain_capacity') or None, 'tax_year': get('tax_year') or date.today().year,
            'reserve_floor': get('reserve_floor') or 0, 'capital_cap': get('capital_cap') or None,
            'exclusions': [s.strip() for s in get('exclusions').split(',') if s.strip()]}
        raw = {'id': pid or None, 'label': get('label'), 'account': get('account'),
               'taxable': {'yes': True, 'no': False}.get(get('taxable')), 'policy': policy,
               'bindings': deepcopy((old or {}).get('bindings', {}))}
        if get('inflow_id'):
            raw['bindings'][get('inflow_id')] = get('allocation_pct') or 100
        p = B.normalize(raw)
        if old:
            for key in ('benchmark_snapshot', 'history', 'approval', 'funding', 'operation', 'wash_review',
                        'replacements', 'harvests', 'provenance', 'execution_note'):
                if key in old:
                    p[key] = deepcopy(old[key])
        B.event(p, action, 'Office program form')
    elif action == 'import':
        from officekit.migration import parse_json
        raw = parse_json(get('program_json'))
        if raw.get('v') != 1:
            raise ValueError('Unsupported portable program version.')
        p = B.normalize(raw['program'])
        if p['id'] in B.programs(answers):
            raise ValueError('That program is already imported. Edit or refresh the existing program.')
        # Source matching is an explicit office choice, never inferred from size.
        p['bindings'] = {get('inflow_id'): B.number(get('allocation_pct') or 100, .01, 100)} if get('inflow_id') else {}
        approval = raw.get('approval') or {}
        if approval:
            if not B.text(approval['reference']) or B.dated(approval['as_of']) > date.today().isoformat():
                raise ValueError('Import a past approval with a nonempty evidence reference.')
            p['approval'] = {'as_of': B.dated(approval['as_of']), 'reference': B.text(approval['reference']),
                             'policy_hash': B.policy_hash(p), 'imported': True}
        B.event(p, 'import', p['provenance'][:1000] or 'Private program import')
    else:
        if not p:
            raise ValueError('Choose a saved beta program.')
        if action in {'approve', 'fund', 'operate', 'pause', 'error'}:
            updated = B.transition(answers, model, pid, action, get('reference'), get('amount'))
            build(updated, folder)
            return pid
        if action == 'bind':
            if get('allocation_pct') == '0':
                p['bindings'].pop(get('inflow_id'), None)
            else:
                p['bindings'][get('inflow_id')] = B.number(get('allocation_pct'), .01, 100)
            B.event(p, 'bind', 'Incoming-money allocation updated')
        elif action == 'refresh':
            from officekit.beta_benchmark import fetch
            p['benchmark_snapshot'] = fetch()
            B.event(p, 'refresh', p['benchmark_snapshot']['source'])
        elif action == 'snapshot':
            from officekit.migration import parse_json
            p['benchmark_snapshot'] = B.normalize_snapshot(parse_json(get('snapshot_json')))
            B.event(p, 'snapshot', p['benchmark_snapshot']['source'])
        elif action == 'wash':
            from officekit.beta_harvest import review_household
            rows = csv.reader(io.StringIO(get('transactions')))
            trades = []
            for row in rows:
                if not row or not any(row):
                    continue
                if len(row) != 4:
                    raise ValueError('Each transaction needs date, symbol, buy/sell and account.')
                d, s, side, account = [x.strip() for x in row]
                trades.append({'date': d, 'symbol': s, 'side': side.lower(), 'account': account})
            review_household(p, {'complete': get('complete') == 'yes', 'reference': get('reference'),
                'as_of': date.today().isoformat(), 'transactions': trades,
                'open_buys': [s.strip() for s in get('open_buys').split(',') if s.strip()]})
        elif action == 'replacement':
            s, replacement = B.symbol(get('symbol')), B.symbol(get('replacement'))
            if B.canon(s) == B.canon(replacement):
                raise ValueError('Choose a distinct replacement security.')
            if not get('reference').strip() or not get('rationale').strip():
                raise ValueError('Document the replacement review and exposure rationale.')
            p.setdefault('replacements', {})[s] = {'symbol': replacement, 'rationale': B.text(get('rationale')),
                'reference': B.text(get('reference')), 'as_of': date.today().isoformat()}
            B.event(p, 'replacement', get('reference'))
        elif action == 'harvest':
            from officekit.beta_harvest import record_harvest
            record_harvest(p, model, get('security_id'), get('fingerprint'), get('reference'))
        elif action == 'void_harvest':
            if not get('reference').strip():
                raise ValueError('Record why the harvest record is being corrected.')
            index = int(B.number(get('index'), 0, len(p.get('harvests', [])) - 1))
            p['harvests'][index]['voided'] = B.text(get('reference'))
            B.event(p, 'void_harvest', get('reference'))
        elif action == 'clear_note':
            if not get('reference').strip():
                raise ValueError('Record evidence that the imported operating issue was resolved.')
            p['execution_note'] = ''
            B.event(p, 'resolved_import_issue', get('reference'))
        else:
            raise ValueError('Choose a supported program action.')
    updated = B.save_program(answers, p, model)
    build(updated, folder)
    return p['id']
