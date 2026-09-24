"""Frozen planning inputs from the same goals, cash and disaster models as the UI."""
from copy import deepcopy

VERSION = 4


def needs_refresh(proposal):
    """Old research must be revised, not relabeled as having seen new inputs."""
    from officekit.deployment import is_deployment
    return (is_deployment(proposal) and bool(proposal.get('research'))
            and (proposal.get('capital_plan') or {}).get('version') != VERSION)


def model_from_snapshot(proposal):
    """Older queued jobs retain the same declared inflow terms in their answers."""
    from officekit import build_model
    snapshot = proposal['snapshot']
    data = deepcopy(snapshot['data'])
    inc = snapshot.get('answers', {}).get('incoming') or {}
    if 'inflow_terms' not in data and inc.get('id') and inc['id'] == (data.get('inflow') or {}).get('id'):
        data['inflow_terms'] = {key: inc.get(key, default) for key, default in
                               [('character', 'ltcg'), ('cadence', 'once'), ('planning_period', None)]}
    return build_model(data)


def inputs(proposal):
    from officekit.render_scenarios import compute_results
    from officekit.goals import evaluate_in_model, apply_goal_ov
    from officekit.commitments import cash_calendar
    from officekit.deployment import source_for
    from officekit.charitable import plans as charitable_plans
    from officekit.beta_programs import summaries as beta_summaries

    snapshot = proposal['snapshot']
    model = model_from_snapshot(proposal)
    bound = proposal.get('deployment_source')
    selected = source_for(model, bound['id'] if bound else None)
    goals = [g for g in model['d'].get('goals', []) if not g.get('implicit')]
    _, _, results = compute_results(model)
    disasters = []
    for r in results:
        sc = r['sc']
        disasters.append({'id': sc['key'], 'name': sc['name'], 'description': sc.get('desc'),
                          'estimated_loss': round(r['dd'], 2), 'estimated_net_worth_after': round(r['nw_after'], 2),
                          'cash_today': round(r['cash_now'], 2), 'marketable_after_haircut': round(r['mkt'], 2),
                          'pending_proceeds': round(r['sept'], 2),
                          'factor_shocks': sc.get('shocks', {}), 'tripwires': sc.get('tripwires', []),
                          'response_options': sc.get('opts', []),
                          'goals_after': apply_goal_ov(goals, sc.get('goal_ov', {})),
                          'probability_assumption': sc.get('p'), 'probability_basis': sc.get('p_basis')})
    return deepcopy({'version': VERSION, 'as_of': model['d']['as_of'], 'source': selected,
                     'source_terms': model['d'].get('inflow_terms', {}) if selected['id'] == (model['d'].get('inflow') or {}).get('id') else {},
                     'goals': [{'goal': g, 'baseline': evaluate_in_model(g, model)} for g in goals],
                     'strategies': snapshot['answers'].get('strategy_decisions', {}),
                     'allocation_targets': [{'id': s.get('id'), 'category': s['category'], 'target_pct': s.get('target_pct')}
                                            for s in model['sleeves'] if s.get('target_pct') is not None],
                     'cash_calendar': cash_calendar(model), 'disasters': disasters,
                     'charitable_goals': charitable_plans(model),
                     'beta_programs': beta_summaries(snapshot['answers'], model, selected['id']),
                     'limitations': ['Scenario estimates describe the existing portfolio, not the proposed basket.',
                                     'Scenario probabilities and factor shocks are modeling assumptions, not forecasts.',
                                     'Future income, pending proceeds and capitalized earnings are not cash available today.']})
