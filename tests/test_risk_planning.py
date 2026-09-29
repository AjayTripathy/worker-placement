"""Synthetic household invariants; no real investor facts or external providers."""
from copy import deepcopy
from datetime import date, timedelta
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

from officekit import build_model, build_from_answers
from officekit.risk_planning import capacity, stress, schedule, compare
from officekit.short_exposure import inventory
from officekit_research import predictions, index
from officekit_research.scenario_forecasts import metadata, review, records, aggregate, import_forecast
from officekit_ai.scenario_forecast import run
from test_deployment_plan import answers, Form
from test_officekit_onboarding_e2e import server, _get  # noqa: F401
from test_local_security import request


def household(**policy):
    a = answers()
    a.pop('incoming'); a.pop('desk_theses')
    a['as_of'] = date.today().isoformat()
    a['sleeves'] = [{'id': 'bank', 'name': 'Bank', 'category': 'cash', 'value': 200000},
                    {'id': 'stocks', 'name': 'Stocks', 'category': 'public_equity', 'value': 800000}]
    a['risk_policy'] = dict(annual_spending=100000, annual_income=0, horizon_years=5, reserve_months=12,
                           income_interruption_months=0, buffer_pct=10, **policy)
    return a


def model(a):
    return build_model(build_from_answers(deepcopy(a)))


def test_capacity_protects_lifestyle_and_preference_cannot_raise_limit():
    a = household()
    c = capacity(model(a))
    assert c['required_capital'] == pytest.approx(600000, abs=1)
    assert c['recommended_loss'] == pytest.approx(360000, abs=1)
    a['risk_policy']['comfort_loss_pct'] = 90
    assert capacity(model(a))['recommended_loss'] == c['recommended_loss']
    a['risk_policy']['comfort_loss_pct'] = 5
    assert capacity(model(a))['recommended_loss'] == 50000
    a['risk_policy']['annual_spending'] = 300000
    assert capacity(model(a))['recommended_loss'] == 0
    assert capacity(model(a))['funding_gap'] > 0


def test_home_pending_and_restricted_balances_cannot_fund_capacity():
    a = household()
    m = model(a)
    baseline = capacity(m)['resources']['total']
    a['sleeves'] += [{'name': 'Restricted cash', 'category': 'cash', 'value': 1000000, 'meta': {'restricted': True}},
                     {'name': 'Private stake', 'category': 'venture_private', 'value': 1000000},
                     {'name': 'Residence', 'category': 'real_estate', 'value': 1000000},
                     {'name': 'Pending', 'category': 'cash_pending', 'value': 1000000}]
    assert capacity(model(a))['resources']['total'] == baseline


@pytest.mark.parametrize('restriction', [{'restricted': True}, {'pledged': True}, {'account_type': 'roth_ira'}, {'account_type': '401(k)'}])
def test_restrictions_survive_normalization(restriction):
    a = household()
    a['sleeves'][0].update(restriction)
    assert capacity(model(a))['resources']['cash'] == 0


def test_goals_count_together_with_reservations_once_and_flexible_excluded():
    a = household()
    a['goals'] = [{'id': 'school', 'kind': 'spending', 'label': 'School', 'amount': 50000, 'date': (date.today()+timedelta(days=30)).isoformat()},
                  {'id': 'trip', 'kind': 'spending', 'label': 'Travel', 'amount': 20000}]
    base = capacity(model(a))['required_capital']
    assert base == pytest.approx(670000, abs=1)
    a['risk_policy']['goal_priority'] = {'trip': 'flexible'}
    assert capacity(model(a))['required_capital'] == pytest.approx(650000, abs=1)
    m = model(a)
    m['d']['commitments'].append(dict(id='reserved-school', goal_id='school', source='goal_reservation',
        label='School', amount=50000, next_due=a['goals'][0]['date'], cadence='once', portfolio_funded=True,
        funding_source='portfolio', active=True, status='confirmed'))
    assert capacity(m)['required_capital'] == pytest.approx(650000, abs=1)


def test_once_expense_is_added_and_recurring_bill_is_inside_spending():
    a = household()
    a['commitments'] += [dict(id='bills', source='recurring_expense', label='Bills', amount=1000,
                            next_due=date.today().isoformat(), cadence='monthly', funding_source='income'),
                         dict(id='emergency', source='recurring_expense', label='Repair', amount=20000,
                            next_due=date.today().isoformat(), cadence='once', funding_source='portfolio')]
    assert schedule(model(a), 1)['months'][0]['outflow'] == pytest.approx(100000/12 + 20000, abs=.01)


def test_financed_goal_uses_down_payment_and_carry_and_scenario_goals():
    a = household()
    a['goals'] = [dict(id='home', kind='spending', label='Home purchase', amount=1000000, date=date.today().isoformat())]
    plan = schedule(model(a), 2)
    assert 250000 < plan['months'][0]['goals_due'][0]['amount'] < 400000
    assert plan['months'][1]['spending'] > 100000/12
    no_goal = household()
    sc = {'goal_ov': {'add': [dict(id='help', kind='spending', label='Help family', amount=10000)]}}
    assert schedule(model(no_goal), 2, scenario=sc)['held'] == 10000


def test_income_cessation_and_delayed_net_cash_have_visible_consequences():
    a = household()
    a['risk_policy'].update(annual_income=120000, income_end_date='2030-12-31')
    a['incoming'] = {'amount': 100000, 'rate': .3, 'character': 'ltcg'}
    m = model(a)
    early = stress(m, dict(shocks={}, pending_date=date.today().isoformat(), horizon_months=3), include_pending=True)
    delayed = stress(m, dict(shocks={}, pending_date=date.today().isoformat(), pending_delay_months=4,
                            income_interruption_months=3, horizon_months=3), include_pending=True)
    assert sum(r['pending'] for r in early['months']) == 70000
    assert sum(r['pending'] for r in delayed['months']) == 0
    assert sum(r['income'] for r in delayed['months']) == 0
    assert early['months'][-1]['liquid_remaining'] - delayed['months'][-1]['liquid_remaining'] == 100000


def test_deployment_conserves_cash_uses_fund_category_and_refuses_unknown_options():
    m = model(household()); saved = deepcopy(m['d'])
    sc = [dict(key='crash', name='Crash', shocks={'S&P 500': -.5}, sale_haircut_pct=0)]
    eq = compare(m, [dict(symbol='VTI', instrument='etf', amount=100000)], sc)
    cash = compare(m, [dict(symbol='SGOV', instrument='etf', amount=100000)], sc)
    assert eq['scenarios'][0]['additional_stressed_loss'] == 50000
    assert cash['scenarios'][0]['additional_stressed_loss'] == 0
    assert eq['before']['resources']['total'] == eq['after']['resources']['total'] == 1000000
    assert m['d'] == saved
    with pytest.raises(ValueError, match='options need'):
        compare(m, [dict(symbol='SPY', instrument='options', amount=1000)], sc)
    with pytest.raises(ValueError, match='available cash'):
        compare(m, [dict(symbol='VTI', amount=200001)], sc)


def test_short_account_lineage_and_unknown_manager_lookthrough():
    m = model(household())
    m['assets'][1]['strategy_ids'] = ['hedged']
    m['assets'][1]['holdings'] = [dict(symbol='AAA', qty=-10, value=-2000, account='Account A',
        borrow_rate_pct=5, strategies=['short_thesis'])]
    m['assets'].append(dict(name='Manager', category='alpha_market_neutral', value=10000, meta={'gross_short': 50000}))
    book = inventory(m)
    p = book['positions'][0]
    assert p['symbol'] == 'AAA' and p['account'] == 'Account A'
    assert p['squeeze_50'] == 1000 and p['annual_borrow_cost'] == 100
    assert book['gaps'][0]['unmapped'] == 50000


def evidence():
    text = 'The reference period contains ten observations and two events.'
    return [dict(url='https://www.federalreserve.gov/example', text=text, sha256=sha256(text.encode()).hexdigest(),
                 fetched_at=date.today().isoformat(), visibility='public_document')]


def forecast(folder, **kw):
    fields = dict(symbol='SCENARIO:tech', statement='A specified event occurs', resolution_criteria='Public primary release confirms event',
        resolve_by=(date.today()+timedelta(days=365)).isoformat(), probability=.8, base_rate=.2,
        submitter='researcher', agent='analyst', model='fixture', protocol='v1', event_key='event',
        scenario=metadata('tech', evidence=evidence(), event_start=date.today().isoformat()))
    fields.update(kw)
    return predictions.record(folder, **fields)


def test_revisions_immutable_and_primary_brier_per_submitter_agent(tmp_path):
    original = forecast(tmp_path)
    updated = forecast(tmp_path, supersedes=original['id'], probability=.6)
    review(tmp_path, updated['id'])
    assert aggregate(records(tmp_path))[0]['probability'] == .6
    index.resolve(tmp_path, updated['id']+':0', True, 'https://www.federalreserve.gov/example')
    board = index.scoreboard(tmp_path, 'submitter_agent')
    assert len(board) == 1 and board[0]['forecasts'] == 1 and board[0]['brier'] == .04
    assert aggregate(records(tmp_path)) == []
    assert predictions.load(tmp_path)[0] == original
    with pytest.raises(ValueError, match='resolved'):
        forecast(tmp_path, supersedes=updated['id'])


def test_import_needs_review_and_contracts_conditions_dependence_stay_separate(tmp_path):
    donor = tmp_path/'donor'; recipient=tmp_path/'recipient'
    original = forecast(donor)
    r = import_forecast(recipient, json.dumps(original))
    assert r['recorded_at'] >= original['recorded_at']
    assert aggregate(records(recipient)) == []
    review(recipient, r['id'])
    conditional = forecast(recipient, agent='conditional', scenario=metadata('tech', condition='if policy changes', evidence=evidence()))
    review(recipient, conditional['id'])
    other = forecast(recipient, agent='other-deadline', resolve_by=(date.today()+timedelta(days=400)).isoformat())
    review(recipient, other['id'])
    groups = aggregate(records(recipient))
    assert len(groups) == 2 and all(g['submissions'] == 1 for g in groups)
    assert len({g['contract_id'] for g in groups}) == 2
    changed = deepcopy(original['scenario']); changed['event_start']='2025-01-01'
    with pytest.raises(ValueError, match='window'):
        forecast(donor, supersedes=original['id'], scenario=changed)


class Forecaster:
    messages = property(lambda self: self)
    def __init__(self, fail=False, fabricated=False): self.fail=fail; self.fabricated=fabricated; self.calls=[]
    def create(self, **kw):
        self.calls.append(kw)
        if self.fail: raise RuntimeError('Provider has no credit')
        out=dict(probability=.4, base_rate=.2, summary='Illustrative forecast', gaps=['Synthetic source'],
                 citations=[dict(source=0, quote='fabricated' if self.fabricated else evidence()[0]['text'], claim='Observed rate is two of ten')])
        return SimpleNamespace(stop_reason='end_turn', content=[SimpleNamespace(type='text', text=json.dumps(out))])


def definition():
    return dict(scenario_key='tech', event_key='event', statement='Specified event occurs',
                resolution_criteria='Primary release confirms event', resolve_by=(date.today()+timedelta(days=365)).isoformat(),
                event_start=date.today().isoformat(), symbols=[], submitter='test-office')


def test_forecasting_independent_benches_then_adjudication_and_all_or_none(tmp_path):
    f=Forecaster(); roles=['scenario-base-rate','scenario-mechanism','scenario-adjudicator']
    result=run(tmp_path, definition(), clients={r:(f,'fixture') for r in roles}, fetcher=lambda s:(evidence(),[]))
    assert len(result) == 3 and len(f.calls) == 3
    assert 'analyses' not in json.loads(f.calls[1]['messages'][0]['content'])
    assert len(json.loads(f.calls[2]['messages'][0]['content'])['analyses']) == 2
    assert aggregate(records(tmp_path)) == []
    for row in result: review(tmp_path,row['id'])
    assert aggregate(records(tmp_path))[0]['source_families'] == 1
    broken=tmp_path/'broken'
    with pytest.raises(RuntimeError, match='credit'):
        run(broken, definition(), clients={r:(Forecaster(fail=r==roles[-1]),'fixture') for r in roles}, fetcher=lambda s:(evidence(),[]))
    assert predictions.load(broken) == []
    with pytest.raises(ValueError, match='citation'):
        run(broken, definition(), clients={r:(Forecaster(fabricated=True),'fixture') for r in roles}, fetcher=lambda s:(evidence(),[]))
    assert predictions.load(broken) == []


def test_policy_and_scenario_forms_roundtrip_and_stale_revision(server):
    from officekit.serve import build_office
    base, folder=server
    build_office(household(),folder)
    form=Form(_get(base+'/pages/risk.html'),suffix='/risk/policy')
    form.fields.update(annual_spending='120000', annual_income='0')
    result = request(base,'POST',form.action,form.fields,Origin=base)
    assert result[0] == 303, result
    assert request(base,'POST',form.action,form.fields,Origin=base)[0] == 400
    assert json.loads((folder/'answers.json').read_text())['risk_policy']['annual_spending'] == 120000
    form=Form(_get(base+'/pages/scenarios.html'),suffix='/risk/scenario')
    form.fields.update(probability_mode='manual',probability_pct='25',enabled='yes',horizon_months='18')
    result = request(base,'POST',form.action,form.fields,Origin=base)
    assert result[0] == 303, result
    html=_get(base+'/pages/scenarios.html')
    assert '25.0% assumption' in html
    assert 'Forecast research library' in _get(base+'/pages/scenario_research.html')


def test_scenario_opens_saved_proposal_instead_of_submitting_another_job(tmp_path):
    from bs4 import BeautifulSoup
    from officekit.render_risk_planning import scenarios
    import uuid
    a = household(); m = model(a)
    pid = str(uuid.uuid4())
    saved = {'id': pid, 'source': 'scenario', 'source_ref': 'crash/put_index',
             'created_at': '2026-09-29T00:00:00Z', 'status': 'error', 'stage': 'Needs attention'}
    path = tmp_path/'strategy_proposals'/(pid+'.json')
    path.parent.mkdir()
    path.write_text(json.dumps(saved))
    page = BeautifulSoup(scenarios(m, a, tmp_path), 'html.parser')
    card = page.select_one('#scenario-crash')
    assert card.select_one('a[href="/pages/proposal_'+pid+'.html"]')
    assert card.select_one('input[name="opt"][value="put_index"]') is None
    saved['status'] = 'superseded'; path.write_text(json.dumps(saved))
    card = BeautifulSoup(scenarios(m, a, tmp_path), 'html.parser').select_one('#scenario-crash')
    assert card.select_one('input[name="opt"][value="put_index"]')
