"""Capital planning contracts. All tax rates, offices and model replies are synthetic."""
from copy import deepcopy
import json

import pytest

from officekit import build_from_answers, build_model, strategy_proposals as proposals
from officekit.capital_planning import inputs
from officekit.commitments import revision
from officekit.deployment import funding, sources
from officekit.inflows import propose
from officekit.personal_context import empty
from officekit_ai import strategy_proposal as pipeline
from test_deployment_plan import answers
from test_officekit_strategy_proposals import Provider, clients, execute, fake_sources


def planning_answers(kind='windfall'):
    a = answers()
    a['goals'] = [{'id': 'reserve', 'kind': 'liquidity_floor', 'label': 'Emergency reserve', 'amount': 120000},
                  {'id': 'school', 'kind': 'spending', 'label': 'School target', 'amount': 40000, 'date': '2027-06-01'}]
    a['strategy_decisions'] = {'diversify': {'status': 'planned', 'note': 'Keep sector exposure bounded'}}
    a['scenarios'] = {'replace': {'liqfreeze': {'name': 'Private liquidity disruption',
                        'shocks': {'S&P 500': -.25}, 'tripwires': ['PRIVATE_CASH_DELAY'],
                        'goal_ov': {'add': [{'id': 'support', 'kind': 'spending', 'label': 'Family support', 'amount': 20000}]}}}}
    if kind == 'income':
        a['incoming'] = {'amount': 20000, 'rate': .25, 'character': 'ordinary', 'cadence': 'monthly',
                         'planning_period': {'start': '2026-09-21', 'end': '2026-09-30'}}
        a['income'] = {'annual': 240000, 'years': 20}
        a['goals'][0]['amount'] = 50000
        a['commitments'].append({'id': 'bills', 'source': 'recurring_expense', 'label': 'Monthly bills',
                                 'amount': 6000, 'cadence': 'monthly', 'next_due': '2026-09-25', 'funding_source': 'income'})
    return a


def model(a):
    return build_model(build_from_answers(a))


def seed_plan(folder, a):
    m = model(a)
    (folder / 'personal_context.json').write_text(json.dumps(empty(a['office_id'])))
    return proposals.create(folder, a, m, 'deploy_powder', 'principal', 'incoming', option='new_capital',
                            deployment_source=sources(m)[0])


def record_receipt(a, gross, withheld):
    model(a)  # stable account / inflow identities
    a['sleeves'][0]['value'] += gross - withheld  # bank import, not the receipt action, credits cash
    return propose(a, {'action': 'receive', 'inflow_id': a['incoming']['id'], 'gross': str(gross),
                       'withheld': str(withheld), 'date': a['as_of'], 'account_id': a['sleeves'][0]['id'],
                       'reference': 'Synthetic reconciled deposit', 'included': 'yes'}, revision(a))


@pytest.mark.parametrize('kind,received,withheld,current,pending', [
    ('windfall', 0, 0, 0, 3480000),
    ('windfall', 2000000, 500000, 1380000, 2100000),
    ('windfall', 5000000, 1500000, 3480000, 0),
    ('income', 0, 0, 0, 9000),
    ('income', 10000, 2000, 1500, 7500),
    ('income', 20000, 5000, 9000, 0),
])
def test_deployment_receipt_and_reserve_arithmetic(kind, received, withheld, current, pending):
    a = planning_answers(kind)
    if received:
        a = record_receipt(a, received, withheld)
    m = model(a)
    before = deepcopy(a)
    f = funding(m, a['incoming']['id'])
    assert f['current_budget'] == current
    assert f['contingent_budget'] == pending
    assert f['proposal_ceiling'] == current + pending
    assert sum(s['value'] for s in m['assets'] if s['category'] == 'cash') == 100000 + received - withheld
    assert a['sleeves'] == before['sleeves']
    if kind == 'income':
        assert f['income_reserve_current'] + f['income_reserve_pending'] == 6000
        assert f['proposal_ceiling'] == 9000  # same gross, tax and bills through partial/full receipts
        assert sum(s['value'] for s in m['assets'] if s['category'] == 'human_capital') > 20000


def test_cash_floor_and_commitments_reserved_once_across_sources():
    a = planning_answers()
    a['sleeves'].append({'id': 'other', 'category': 'cash_pending', 'value': 200000, 'name': 'Separate proceeds'})
    a['commitments'].append({'id': 'closing', 'source': 'goal_reservation', 'label': 'Closing payment',
                             'amount': 400000, 'cadence': 'once', 'next_due': '2026-09-30', 'funding_source': 'portfolio'})
    m = model(a)
    fs = [funding(m, s['id']) for s in sources(m)]
    assert sum(f['pending_tax'] for f in fs) == 1500000
    assert sum(f['commitment_reserve'] for f in fs) == 300000
    assert sum(f['liquidity_reserve'] for f in fs) == 120000
    assert sum(f['contingent_budget'] for f in fs) == 3280000
    assert all(f['current_budget'] == 0 for f in fs)
    p = {'brief': {'option': 'new_capital'}, 'snapshot': {'data': m['d']}, 'target_pct': None}
    with pytest.raises(ValueError, match='Choose an incoming-money source'):
        pipeline.budget(p)


def test_capital_loss_offset_is_not_applied_to_income():
    a = planning_answers('income')
    a['incoming']['harvest_losses'] = 10000
    a['loss_carryforward'] = 10000
    assert funding(model(a))['pending_tax'] == 5000
    a['incoming']['character'] = 'ltcg'
    assert funding(model(a))['pending_tax'] == 0


def test_windfall_tax_uses_declared_gain_fraction():
    a = planning_answers()
    a['incoming'].update(taxable_fraction=.5, harvest_losses=1000000)
    f = funding(model(a))
    assert f['pending_tax'] == 450000  # (5m * .5 - 1m) * stated .30
    assert f['contingent_budget'] == 4530000  # preserves the 20k cash-floor gap


@pytest.mark.parametrize('period', [None, {}, {'start': '2026-10-31', 'end': '2026-10-01'},
    {'start': '2026-09-01', 'end': '2026-09-30'}, {'start': '2026-09-21', 'end': '2027-09-30'}])
def test_recurring_income_requires_forward_bounded_period(period):
    a = planning_answers('income')
    a['incoming']['planning_period'] = period
    f = funding(model(a))  # legacy unbound callers must receive the same gate
    assert f['current_budget'] == f['contingent_budget'] == 0
    assert any('planning period' in gap for gap in f['blocking_gaps'])


def test_only_income_bills_inside_period_are_deducted():
    a = planning_answers('income')
    september = funding(model(a))
    a['incoming']['cadence'] = 'quarterly'
    a['incoming']['planning_period']['end'] = '2026-11-30'
    quarter = funding(model(a))
    assert september['income_expenses'] == 6000
    assert quarter['income_expenses'] == 18000 and quarter['contingent_budget'] == 0
    assert quarter['income_expense_shortfall'] == 3000
    # The amount is the stated period TOTAL, never multiplied by cadence.
    assert quarter['pending_gross'] == 20000
    a['commitments'][-1]['funding_source'] = 'portfolio'
    f = funding(model(a))
    assert f['income_expenses'] == 0  # already deducted by the cash calendar
    assert f['contingent_budget'] == 0  # protects the cash floor after portfolio-funded bills


def test_one_off_income_uses_explicit_payment_without_annualizing():
    a = planning_answers('income')
    a['incoming'].update(cadence='once', amount=20000.40)
    a['incoming'].pop('planning_period')
    f = funding(model(a))
    assert f['pending_tax'] == 5000.10
    assert f['contingent_budget'] == 15000.30
    assert f['income_expenses'] == 0  # no unspecified income period inferred from one payment


@pytest.mark.parametrize('kind', ['windfall', 'income'])
def test_planner_reviews_frozen_goals_strategies_disasters_and_research(tmp_path, monkeypatch, kind):
    fake_sources(monkeypatch)
    a = planning_answers(kind)
    p = seed_plan(tmp_path, a)
    provider = Provider()
    p = execute(tmp_path, p, provider)
    assert p['status'] == 'needs_review', p['errors']
    assert len(provider.calls) == 7
    assert 'Capital Planner' in provider.calls[0]['system']
    payload = json.loads(provider.calls[0]['messages'][0]['content'].split('\n', 1)[1])
    assert payload['capital_plan'] == p['capital_plan']
    assert payload['capital_plan']['strategies']['diversify']['status'] == 'planned'
    assert {g['goal']['id'] for g in payload['capital_plan']['goals']} == {'reserve', 'school'}
    freeze = next(sc for sc in p['capital_plan']['disasters'] if sc['id'] == 'liqfreeze')
    assert freeze['factor_shocks'] == {'S&P 500': -.25}
    assert any(g['id'] == 'support' for g in freeze['goals_after'])
    assert any(e['id'] == 'saved_staples' and e['verdict'] == 'WATCH' for e in payload['saved_research']['entries'])
    assert p['basket'][0]['symbol'] == 'VDC' and p['research_attachments'][0]['references']
    assert p['basket'][0]['contingent_amount'] == (4500 if kind == 'income' else 1740000)
    deck = (tmp_path / 'pages' / ('proposal_' + p['id'] + '.html')).read_text()
    assert 'Capital Planner · inputs behind this plan' in deck
    assert 'School target' in deck and 'Private liquidity disruption' in deck
    if kind == 'income':
        assert any(sc['id'] == 'income_shock' for sc in p['capital_plan']['disasters'])
    # General security courts and public research do not receive this private plan.
    for call in provider.calls[1:4]:
        assert 'PRIVATE_CASH_DELAY' not in json.dumps(call)
    assert 'PRIVATE_CASH_DELAY' not in json.dumps(p['general']['VDC']['record'])
    # Suitability, independent sizing and the final pitch all see disaster planning.
    for call in provider.calls[4:]:
        assert 'PRIVATE_CASH_DELAY' in json.dumps(call)
    assert inputs(p) == p['capital_plan']
    a['goals'][0]['amount'] = 999999
    a['scenarios']['replace']['liqfreeze']['tripwires'] = ['CHANGED']
    assert inputs(p) == p['capital_plan']  # frozen office, not mutable live answers
    assert execute(tmp_path, p, provider)['capital_plan'] == p['capital_plan']
    assert len(provider.calls) == 7


@pytest.mark.parametrize('verdict', ['WATCH', 'AVOID', 'KILL'])
def test_capital_planner_cannot_overrule_a_court(tmp_path, monkeypatch, verdict):
    fake_sources(monkeypatch)
    p = execute(tmp_path, seed_plan(tmp_path, planning_answers('income')), Provider(verdict=verdict))
    assert p['basket'][0]['amount'] == p['basket'][0]['contingent_amount'] == 0
    assert not p['basket'][0]['eligible']


def test_missing_income_tax_rate_blocks_bullish_model_and_is_visible(tmp_path, monkeypatch):
    fake_sources(monkeypatch)
    a = planning_answers('income')
    del a['incoming']['rate']
    p = execute(tmp_path, seed_plan(tmp_path, a), Provider())
    assert p['status'] == 'needs_review', p['errors']
    assert p['funding']['current_budget'] == p['funding']['contingent_budget'] == 0
    assert not p['basket'][0]['eligible']
    assert any('ordinary-income tax rate' in c for c in p['basket'][0]['conditions'])


def test_resume_does_not_repeat_planning_or_mix_new_office_inputs(tmp_path, monkeypatch):
    fake_sources(monkeypatch)
    provider = Provider(fail_pitch=True)
    a = planning_answers('income')
    p = execute(tmp_path, seed_plan(tmp_path, a), provider)
    assert p['status'] == 'error' and p['capital_plan']
    original = deepcopy(p['capital_plan'])
    (tmp_path / 'answers.json').write_text(json.dumps({**a, 'goals': []}))
    proposals.retry(tmp_path, p['id'])
    provider.fail_pitch = False
    p = execute(tmp_path, p, provider)
    assert p['status'] == 'needs_review' and p['capital_plan'] == original
    assert len(provider.calls) == 8


def test_legacy_funding_checkpoint_is_recomputed_before_research(tmp_path, monkeypatch):
    fake_sources(monkeypatch)
    p = seed_plan(tmp_path, planning_answers('income'))
    p['funding'] = {**pipeline.budget(p), 'current_budget': 999999, 'contingent_budget': 999999}
    proposals.save(tmp_path, p)
    p = execute(tmp_path, p, Provider())
    assert p['status'] == 'needs_review', p['errors']
    assert p['funding']['current_budget'] == 0 and p['funding']['contingent_budget'] == 9000


def test_legacy_snapshot_recovers_income_terms_from_frozen_answers(tmp_path, monkeypatch):
    fake_sources(monkeypatch)
    a = planning_answers('income')
    del a['incoming']['rate']
    p = seed_plan(tmp_path, a)
    del p['snapshot']['data']['inflow_terms']
    proposals.save(tmp_path, p)
    p = execute(tmp_path, p, Provider())
    assert p['status'] == 'needs_review', p['errors']
    assert p['funding']['blocking_gaps'] and p['funding']['contingent_budget'] == 0
    assert p['capital_plan']['source_terms']['cadence'] == 'monthly'


def test_old_research_requires_revision_even_with_unchanged_answers(tmp_path, monkeypatch):
    from officekit import strategy_routes
    from officekit.serve import build_office
    from officekit.render_deployment import page
    fake_sources(monkeypatch)
    a = planning_answers('income')
    build_office(a, tmp_path)
    p = execute(tmp_path, seed_plan(tmp_path, a), Provider())
    del p['capital_plan']  # simulate a proposal completed before this planning contract
    proposals.save(tmp_path, p)
    build_office(a, tmp_path)
    m = model(a)
    html = page(m, sources(m)[0], [p], revision(a))
    assert 'Build a fresh ticker plan' in html and '$4,500.00' not in html
    with pytest.raises(ValueError, match='Capital planning inputs changed'):
        proposals.decide(tmp_path, a, p['id'], 'adopt')
    params = {'revision': revision(a), 'inflow_id': a['incoming']['id']}
    new_id, dispatch = strategy_routes.handle('/strategy/deploy', tmp_path, lambda key: params.get(key, ''),
                                              build_office, lambda a, folder: model(a))
    assert dispatch and new_id != p['id']
    assert proposals.load(tmp_path, p['id'])['status'] == 'superseded'
