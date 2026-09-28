"""Revision-checked risk policy, stress assumptions and scenario research."""
from copy import deepcopy
from datetime import datetime, timezone, date
import json
import re

from officekit.office_lock import locked
from officekit.mandates import require_revision

POSTS = {'/risk/policy', '/risk/scenario', '/risk/forecast', '/risk/forecast-review', '/risk/forecast-import'}


def handle(path, folder, get, build):
    from officekit import build_model, build_from_answers
    from officekit.risk_planning import FIELDS, validate
    from officekit.render_scenarios import applicable_scenarios
    from officekit.render_scorecard import ledger_revision
    with locked(folder):
        answers = json.loads((folder / 'answers.json').read_text())
        require_revision(answers, get('revision'))
        updated = deepcopy(answers)
        model = build_model(build_from_answers(deepcopy(answers)))
        if path == '/risk/policy':
            policy = {k: float(get(k)) for k in FIELDS if get(k)}
            policy['income_end_date'] = get('income_end_date')
            policy['goal_priority'] = {(g.get('id') or g['label']): get('goal_' + (g.get('id') or g['label'])) or 'protect'
                                       for g in model['d'].get('goals', []) if not g.get('implicit')}
            policy['confirmed_at'] = datetime.now(timezone.utc).isoformat()
            updated['risk_policy'] = validate(policy)
            build(updated, folder)
            return '/pages/risk.html'
        key = get('scenario_key')
        scenario = next((sc for sc in applicable_scenarios(model) if sc['key'] == key), None)
        if path == '/risk/scenario':
            if scenario is None:
                raise ValueError('Unknown scenario')
            mode = get('probability_mode')
            if mode not in {'stress', 'manual', 'research'}:
                raise ValueError('Choose a probability source')
            def value(name, default, lo, hi):
                import math
                n = float(get(name)) if get(name) else default
                if not math.isfinite(n) or not lo <= n <= hi:
                    raise ValueError('Invalid ' + name.replace('_', ' '))
                return n
            patch = {'enabled': get('enabled') == 'yes', 'probability_mode': mode,
                     'p': value('probability_pct', 0, 0, 100) / 100,
                     'p_basis': 'Office scenario assumption; not a registered forecast',
                     'forecast_contract_id': get('forecast_contract_id'),
                     'shocks': {f: value('shock_' + f, 0, -95, 500) / 100 for f in model['factors']}}
            for name, default, hi in [('horizon_months', 24, 120), ('income_interruption_months', 0, 120), ('pending_delay_months', 0, 120),
                                      ('sale_haircut_pct', 2, 100), ('annual_inflation_pct', 0, 30), ('uninsured_loss', 0, 1e12)]:
                patch[name] = value(name, default, 1 if name == 'horizon_months' else 0, hi)
                if name.endswith('_months') and float(patch[name]).is_integer() is False:
                    raise ValueError('Use a whole number of months')
            patch['pending_date'] = date.fromisoformat(get('pending_date')).isoformat() if get('pending_date') else ''
            if mode == 'research':
                from officekit_research.scenario_forecasts import records, aggregate
                if not any(g['contract_id'] == patch['forecast_contract_id'] for g in aggregate(records(folder, key))):
                    raise ValueError('Choose a current, reviewed, unconditional forecast for this scenario')
            updated.setdefault('scenarios', {}).setdefault('replace', {}).setdefault(key, {}).update(patch)
            build(updated, folder)
            return '/pages/scenarios.html#scenario-' + key
        if get('ledger_revision') != ledger_revision(folder):
            raise ValueError('Research changed. Reload before saving a forecast or review.')
        if path == '/risk/forecast-review':
            if get('reviewed') != 'yes':
                raise ValueError('Review the event, evidence, horizon and conditions first')
            from officekit_research.scenario_forecasts import review
            review(folder, get('forecast_id'))
            return '/pages/scenario_research.html#forecast-' + get('forecast_id')
        if path == '/risk/forecast-import':
            from officekit_research.scenario_forecasts import import_forecast
            raw = get('forecast_json')
            if len(raw.encode()) > 2_000_000:
                raise ValueError('Forecast exceeds the import limit')
            r = import_forecast(folder, raw)
            return '/pages/scenario_research.html#forecast-' + r['id']
        if scenario is None:
            raise ValueError('Choose a known scenario')
        definition = {k: get(k) for k in ('event_key', 'statement', 'resolution_criteria', 'resolve_by', 'event_start')}
        if any(not definition[k].strip() or len(definition[k]) > (1200 if k in {'statement', 'resolution_criteria'} else 200) for k in definition):
            raise ValueError('Give the event, exact outcome criteria, window and deadline')
        start, end = date.fromisoformat(definition['event_start']), date.fromisoformat(definition['resolve_by'])
        if start > end or end <= date.today():
            raise ValueError('The event needs a valid window and future deadline')
        symbols = [s.strip().upper() for s in get('symbols').split(',') if s.strip()]
        if len(symbols) > 12 or any(not re.fullmatch(r'[A-Z0-9][A-Z0-9.^-]{0,14}', s) for s in symbols):
            raise ValueError('Enter at most twelve valid ticker symbols')
        definition.update(symbols=symbols, scenario_key=key, submitter='office:' + answers['office_id'])
        updated.setdefault('scenario_research', {})[key] = definition
        # Validate revisions before making a paid call.
        from officekit_research.scenario_forecasts import records
        for r in records(folder, key):
            if r['event_key'] == definition['event_key'] and any(r[k] != definition[k] for k in ('statement', 'resolution_criteria', 'resolve_by')):
                raise ValueError('Use a new event key when changing the event or deadline')
        from officekit_ai.scenario_forecast import run
        run(folder, definition)
        build(updated, folder)
        return '/pages/scenario_research.html#' + key
