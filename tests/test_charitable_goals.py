"""Giving goals across budgeting, review and both HTTP transports. Synthetic inputs."""
from copy import deepcopy
import json

import pytest

from officekit import build_from_answers, build_model, strategy_proposals as proposals
from officekit.charitable import assessment, validate
from officekit.commitments import cash_calendar, tax_funding, revision, apply_edit
from officekit.deployment import funding
from officekit.goal_contention import claims
from officekit.goal_mandates import goal_strategy_menu, goal_coverage
from officekit.goals import evaluate_in_model
from officekit.personal_context import empty
from officekit.serve import build_office
from test_deployment_plan import answers, Form
from test_officekit_strategy_proposals import Provider, execute, fake_sources
from test_officekit_onboarding_e2e import server, _get, _post
from test_hosted_workspace import workspace, post
from test_hosted_migration import office


def gift(**terms):
    return {'id': 'giving', 'kind': 'charitable', 'label': 'Community giving', 'amount': 200000,
            'date': '2026-12-15', 'charitable': {'funding': 'cash', 'vehicle': 'direct', **terms}}


def giving_office(goal=None):
    a = answers()
    a['goals'] = [goal if goal is not None else gift()]
    a['sleeves'].append({'category': 'public_equity', 'name': 'Public stocks', 'value': 300000,
                         'holdings': [{'symbol': 'VDC', 'mv': 300000}]})
    return a


def model(a):
    return build_model(build_from_answers(a))


def reviewed(**terms):
    return gift(recipient='Example charity', recipient_qualified=True, deductible_amount=150000,
                deduction_tax_rate=.35, tax_review_reference='Synthetic preparer review 2026-09-21', **terms)


def test_first_class_goal_offers_existing_gifting_strategy():
    a = giving_office()
    m = model(a)
    assert goal_strategy_menu(m)['giving']['options'][0]['sid'] == 'gifting'
    a['strategy_decisions'] = {'gifting': {'status': 'planned', 'origins': [{'source': 'goal', 'ref': 'giving'}]}}
    assert goal_coverage(model(a))['by_goal']['giving'][0]['sid'] == 'gifting'
    assert evaluate_in_model(a['goals'][0], m)['kind'] == 'charitable'
    assert claims(a['goals'][0], m)['capital'] == 200000


@pytest.mark.parametrize('change', [
    {'amount': 0}, {'amount': -1}, {'amount': float('nan')}, {'amount': True}, {'date': '2026-02-30'},
    {'charitable': {'funding': []}}, {'charitable': {'funding': 'private_deal'}},
    {'charitable': {'reserve_cash': True}}, {'charitable': {'deductible_amount': 200001}},
    {'charitable': {'deduction_tax_rate': 1.5}}, {'charitable': {'recipient_qualified': 'yes'}},
    {'charitable': {'symbol': '<script>'}}, {'charitable': {'cost_basis': float('inf')}},
    {'charitable': []}, {'charitable': None},
])
def test_invalid_giving_data_is_rejected(change):
    g = {**gift(), **change}
    assert validate(g)
    with pytest.raises((ValueError, TypeError)):
        model(giving_office(g))


def test_reviewed_deduction_is_a_scenario_and_never_releases_tax_cash():
    a = giving_office(reviewed())
    before = deepcopy(a)
    m = model(a)
    plan = assessment(a['goals'][0], m)
    assert plan['deduction_tax_benefit'] == 52500
    assert plan['avoided_gain_tax'] is None
    assert tax_funding(m)['pending'] == 1500000
    assert funding(m)['contingent_budget'] == 3500000
    assert cash_calendar(m)['available'] == 100000
    assert [s['value'] for s in a['sleeves']] == [s['value'] for s in before['sleeves']]
    assert claims(a['goals'][0], m)['capital'] == 200000  # not net of hypothetical savings


def test_unknown_tax_assumptions_remain_unknown():
    a = giving_office(gift(deductible_amount=200000, deduction_tax_rate=.37))
    plan = assessment(a['goals'][0], model(a))
    assert plan['deduction_tax_benefit'] is None and plan['gaps']
    assert any('AGI' in gap for gap in plan['gaps'])


def test_appreciated_lots_avoid_only_their_own_gain_and_follow_stresses():
    g = reviewed(funding='appreciated_securities', symbol='VDC', cost_basis=80000, long_term=True,
                 before_sale=True, capital_gain_tax_rate=.238)
    a = giving_office(g)
    m = model(a)
    plan = assessment(g, m)
    assert plan['embedded_gain_not_realized'] == 120000 and plan['avoided_gain_tax'] == 28560
    assert tax_funding(m)['pending'] == 1500000
    ev = evaluate_in_model(g, m, [(s, -s['value'] * .5 if s['category'] == 'public_equity' else 0) for s in m['sleeves']])
    assert ev['assessment']['available_today'] == 150000 and ev['status'] == 'SHORT'
    assert ev['assessment']['avoided_gain_tax'] is None
    for patch in [{'before_sale': False}, {'long_term': False}, {'symbol': 'MISSING'}]:
        changed = {**g, 'charitable': {**g['charitable'], **patch}}
        assert assessment(changed, m)['avoided_gain_tax'] is None


def test_daf_grants_never_add_a_second_deduction():
    g = reviewed(vehicle='daf')
    plan = assessment(g, model(giving_office(g)))
    assert plan['deduction_tax_benefit'] == 52500
    assert any('second contribution deduction' in s for s in plan['limitations'])
    assert validate({**g, 'charitable': {**g['charitable'], 'later_grant_deduction': 200000}})


def test_explicit_cash_reservation_reduces_deployment_once_and_can_be_released():
    a = giving_office(gift(reserve_cash=True))
    m = model(a)
    assert [c['id'] for c in m['d']['commitments'] if c.get('goal_id')] == ['charitable:giving']
    assert cash_calendar(m)['shortfall'] == 100000
    assert funding(m)['contingent_budget'] == 3400000
    assert assessment(a['goals'][0], m)['available_today'] == 100000
    with pytest.raises(ValueError, match='charitable goal'):
        apply_edit(a, 'charitable:giving', {'amount': 50000}, revision(a))
    a['goals'][0]['amount'] = 50000
    assert cash_calendar(model(a))['available'] == 50000
    a['goals'][0]['charitable']['reserve_cash'] = False
    assert cash_calendar(model(a))['available'] == 100000
    assert funding(model(a))['contingent_budget'] == 3500000


def form_fields(gid):
    return {'gid': gid, 'charitable_form': 'yes', 'label': 'Community giving', 'amount': '200000',
            'date': '2026-12-15', 'vehicle': 'daf', 'funding': 'cash', 'reserve_cash': 'yes',
            'recipient': 'Example sponsor', 'recipient_qualified': 'yes', 'deductible_amount': '150000',
            'deduction_tax_rate': '35', 'tax_review_reference': 'Synthetic review'}


def test_local_create_edit_reserve_and_research_giving_strategy(server, monkeypatch):
    base, folder = server
    build_office(answers(), folder)
    page = _get(base + '/pages/goals.html')
    assert '<option value="charitable">Charitable giving ($)</option>' in page
    code, location, body = _post(base + '/goals/add', {'back': 'goals', 'gkind': 'charitable', 'glabel': 'Community giving', 'gamt': '200000'})
    assert (code, location) == (303, '/pages/goals.html'), body
    a = json.loads((folder / 'answers.json').read_text())
    gid = a['goals'][0]['id']
    detail = '/pages/goal_' + gid + '.html'
    assert 'Reviewed tax assumptions' in _get(base + detail)
    code, location, body = _post(base + '/goal/params', form_fields(gid))
    assert (code, location) == (303, detail), body
    html = _get(base + detail)
    assert '$52,500.00' in html and 'Research this giving strategy' in html
    assert 'Edit charitable goal and reservation' in _get(base + '/pages/capital.html')
    a = json.loads((folder / 'answers.json').read_text())
    assert funding(model(a))['contingent_budget'] == 3400000
    fake_sources(monkeypatch)
    provider = Provider(program=True)
    from officekit_ai import strategy_proposal as pipeline
    from test_officekit_strategy_proposals import clients
    monkeypatch.setattr(proposals, 'dispatch', lambda directory, pid: proposals.run(directory, pid,
        lambda p, f, save: pipeline.build_proposal(p, f, save, clients(provider))))
    form = Form(html, '/strategy/goal-adopt')
    assert form.fields['sid'] == 'gifting'
    status, _, response_body = _post(base + form.action, form.fields)
    assert status == 303, response_body
    p = proposals.list_proposals(folder)[0]
    assert p['status'] == 'needs_review', p['errors']
    assert p['brief']['kind'] == 'program' and not p['basket']
    assert p['charitable_goals'][0]['goal_id'] == gid
    assert 'Synthetic review' in provider.calls[0]['messages'][0]['content']
    assert p['research_inventory']  # same catalog as every strategy
    assert not p.get('general')  # this is a private program review
    from officekit.render_proposal import render_proposal
    deck = render_proposal(p)
    assert 'Charitable goals behind this strategy' in deck and '$52,500.00' in deck
    assert detail in deck


def test_hosted_charitable_goal_editor_and_tenant_isolation(workspace):
    from hosting.app.main import SESSION
    client, receipt, _ = workspace
    response = post(client, receipt, '/goals/add', {'back': 'goals', 'gkind': 'charitable', 'glabel': 'Community giving', 'gamt': '200000'})
    assert response.status_code == 303, response.text
    page = client.get(receipt['path'] + '/pages/goals.html')
    import re
    gid = re.search(r'/pages/goal_([a-f0-9-]+)\.html', page.text)[1]
    receipt = {**receipt, 'digest': client.get(receipt['path'] + '/state').json()['v']}
    response = post(client, receipt, '/goal/params', form_fields(gid))
    assert response.status_code == 303, response.text
    detail = client.get(response.headers['location'])
    assert '$52,500.00' in detail.text and receipt['path'] + '/strategy/goal-adopt' in detail.text
    assert 'nonce-' in detail.headers['content-security-policy']
    client.cookies.set(SESSION, 'bob')
    assert client.get(receipt['path'] + '/pages/goal_' + gid + '.html').status_code == 404


def test_capital_planner_sees_giving_without_public_research_leak(tmp_path, monkeypatch):
    from test_capital_planning import seed_plan
    fake_sources(monkeypatch)
    a = giving_office(reviewed(reserve_cash=True))
    provider = Provider()
    p = execute(tmp_path, seed_plan(tmp_path, a), provider)
    assert p['status'] == 'needs_review', p['errors']
    assert p['capital_plan']['charitable_goals'] == p['charitable_goals']
    assert p['funding']['contingent_budget'] == 3400000
    assert p['basket'][0]['contingent_amount'] == 1700000
    assert 'Community giving' in provider.calls[0]['messages'][0]['content']
    for call in provider.calls[1:4]:
        assert 'Synthetic preparer' not in json.dumps(call)
    assert 'Synthetic preparer' not in json.dumps(p['general'])


def test_onboarding_preserves_charitable_intent_and_review_terms(server):
    base, folder = server
    g = reviewed(vehicle='daf', reserve_cash=True)
    fields = {'owner': 'Giving test', 'as_of': '2026-09-21', 'u_kind': 'cash', 'u_name': 'Cash', 'u_value': '300000',
              'goal_kind': 'charitable', 'goal_label': g['label'], 'goal_amount': str(g['amount']),
              'goal_date': g['date'], 'goal_charitable': json.dumps(g['charitable'])}
    status, _, body = _post(base + '/onboard', fields)
    assert status == 303, body
    a = json.loads((folder / 'answers.json').read_text())
    saved = a['goals'][0]
    assert saved['kind'] == 'charitable' and saved['charitable'] == g['charitable']
    assert 'Reviewed tax assumptions' in _get(base + '/pages/goal_' + saved['id'] + '.html')


@pytest.mark.parametrize('kind', ['windfall', 'income'])
def test_giving_reservation_protects_both_income_and_windfall_plans(kind):
    from test_capital_planning import planning_answers
    a = planning_answers(kind)
    a['goals'].append({**gift(reserve_cash=True), 'amount': 100000})
    f = funding(model(a))
    assert f['contingent_budget'] == (3380000 if kind == 'windfall' else 0)
    assert f['pending_tax'] == (1500000 if kind == 'windfall' else 5000)
    assert f['liquidity_floor'] == (120000 if kind == 'windfall' else 50000)
