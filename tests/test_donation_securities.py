"""Synthetic donor portfolios: basis gaps, lots, custody identity and HTTP flows."""
from copy import deepcopy
import json

import pytest

from officekit import build_from_answers, build_model
from officekit.donation_securities import inventory, shortlist, record_review
from officekit.serve import build_office
from test_charitable_goals import gift
from test_deployment_plan import answers, Form
from test_officekit_onboarding_e2e import server, _get, _post
from test_hosted_workspace import workspace, post


def position(symbol='AAA', value=100000, basis=10000, **extra):
    return {'symbol': symbol, 'value': value, 'cost_basis': basis, 'account': 'Taxable A',
            'taxable': True, 'sec_type': 'STK', 'acquired': '2020-01-01', **extra}


def donor(rows=None):
    a = answers()
    a['goals'] = [{**gift(vehicle='daf', funding='appreciated_securities'), 'amount': 150000}]
    a['positions'] = {'rows': rows if rows is not None else [position()]}
    return a


def model(a):
    return build_model(build_from_answers(a))


@pytest.fixture
def office(tmp_path):
    folder = tmp_path / 'donor'
    build_office(donor([position(basis=None, taxable=None, acquired=None)]), folder)
    return folder


def test_ranks_gain_per_donated_dollar_and_builds_bounded_mix():
    a = donor([position(), position('BBB', 500000, 250000)])
    view = shortlist(a['goals'][0], model(a))
    assert [r['symbol'] for r in view['candidates']] == ['AAA', 'BBB']
    assert [(r['gift_amount'], r['gift_basis']) for r in view['suggested_mix']] == [(100000, 10000), (50000, 25000)]
    assert not view['suggested_mix'][0]['estimate'] and view['suggested_mix'][1]['estimate']
    assert view['unfilled'] == 0


def test_account_specific_lots_are_not_duplicated_by_aggregate():
    a = donor([{'symbol': 'AAA', 'value': 300000, 'cost_basis': 60000, 'accounts': [
        {'account': 'Taxable A', 'source': 'broker-a', 'value': 100000, 'taxable': True,
         'lots': [{'value': 80000, 'cost': 10000, 'open': '2020-01-01'}, {'value': 20000, 'cost': 1000, 'open': '2026-05-01'}]},
        {'account': 'Taxable B', 'source': 'broker-b', 'value': 200000, 'taxable': True, 'acquired': '2020-01-01'}]}])
    m = model(a)
    rows = inventory(m)
    assert len(rows) == 3 and sum(r['market_value'] for r in rows) == 300000
    assert next(r for r in rows if r['account'] == 'Taxable B')['cost_basis'] is None
    view = shortlist(a['goals'][0], m)
    assert len(view['candidates']) == 1 and view['candidates'][0]['market_value'] == 80000
    assert view['unfilled'] == 70000 and view['excluded_count'] == 1


def test_confirm_missing_basis_once_reuse_across_goals_and_reprompt_on_new_snapshot():
    a = donor([position(basis=None, acquired=None, taxable=None)])
    row = inventory(model(a))[0]
    assert set(row['missing']) == {'cost_basis', 'long_term', 'taxable'} and row['gain'] is None
    updated = record_review(a, model(a), row['id'], row['fingerprint'],
                            {'cost_basis': '0', 'long_term': 'yes', 'taxable': 'yes', 'reference': 'Reviewed zero basis statement'})
    fresh = inventory(model(updated))[0]
    assert fresh['eligible'] and fresh['cost_basis'] == 0 and fresh['gain_fraction'] == 1
    assert a['positions']['rows'][0]['cost_basis'] is None and updated['positions'] == a['positions']
    assert shortlist(gift(), model(updated))['candidates'][0]['id'] == fresh['id']
    cleared = record_review(updated, model(updated), row['id'], row['fingerprint'], {'reference': 'Facts need another review'})
    assert set(inventory(model(cleared))[0]['missing']) == {'cost_basis', 'long_term', 'taxable'}
    changed = deepcopy(updated)
    changed['positions']['rows'][0]['value'] = 110000
    stale = inventory(model(changed))[0]
    assert stale['review_stale'] and stale['cost_basis'] is None and not stale['eligible']
    with pytest.raises(ValueError, match='holding changed'):
        record_review(changed, model(changed), row['id'], row['fingerprint'], {'reference': 'old form'})


@pytest.mark.parametrize('basis', ['NaN', 'inf', '-1', 'unknown'])
def test_invalid_basis_cannot_turn_into_zero(basis):
    a = donor([position(basis=None)])
    row = inventory(model(a))[0]
    with pytest.raises(ValueError, match='finite'):
        record_review(a, model(a), row['id'], row['fingerprint'], {'cost_basis': basis, 'reference': 'test'})


def test_imported_basis_and_retirement_status_cannot_be_overwritten():
    a = donor([position(account='Roth IRA')])
    row = inventory(model(a))[0]
    assert row['taxable'] is False and not row['eligible']
    for fields in [{'cost_basis': '0'}, {'taxable': 'yes'}]:
        with pytest.raises(ValueError):
            record_review(a, model(a), row['id'], row['fingerprint'], {**fields, 'reference': 'test'})


@pytest.mark.parametrize('changes', [
    {'value_is_cost': True}, {'restricted': True}, {'pledged': True}, {'ccy': 'JPY'},
    {'lots': [{'value': 80000, 'cost': 10000, 'open': '2020-01-01'}]},
    {'acquired': '2025-09-21'}, {'basis': 110000}, {'taxable': None},
])
def test_no_recommendation_from_ineligible_or_unverified_data(changes):
    a = donor([position(**changes)])
    assert not shortlist(a['goals'][0], model(a))['candidates']


def test_shorts_and_options_are_not_donation_candidates():
    a = donor([position(value=-10000), position('OPT', 5000, 500, sec_type='OPT')])
    assert inventory(model(a)) == []


def test_csv_keeps_total_basis_zero_and_missing_distinct(tmp_path):
    from officekit.importers import read_positions_csv, classify_positions
    file = tmp_path / 'positions.csv'
    file.write_text('Symbol,Current Value,Total Cost Basis,Date Acquired,Account\nAAA,100000,,2020-01-01,A\nBBB,100000,0,2020-01-01,B\n')
    rows = read_positions_csv(file)
    assert 'cost_basis' not in rows[0] and rows[1]['cost_basis'] == 0
    sleeves = classify_positions(rows)
    assert sorted(h['symbol'] for s in sleeves for h in s['holdings']) == ['AAA', 'BBB']


def test_flex_missing_basis_survives_as_unknown():
    from officekit_adapters.ibkr_flex import parse_flex_positions
    from test_officekit_ibkr_flex import SAMPLE
    rows = parse_flex_positions(SAMPLE.replace('costBasisMoney="6000"', ''), as_of='2026-09-21')
    row = next(r for r in rows if r['symbol'] == 'ONON')
    assert row['cost_basis'] is None and row['lots'][0]['cost'] is None


@pytest.mark.parametrize('basis', ['unknown', 'NaN', float('inf'), None])
def test_currency_conversion_does_not_invent_zero_basis(basis):
    from officekit_adapters import convert_to_base
    row = convert_to_base([{'symbol': 'AAA', 'value': 100000, 'cost_basis': basis, 'ccy': 'USD'}], {})[0]
    assert row.get('cost_basis') is None


def test_preserved_basis_does_not_duplicate_harvest_loss(tmp_path):
    from officekit.harvest import collect
    a = donor([position(basis=125000)])
    build_office(a, tmp_path)
    assert collect(model(a), tmp_path)['harvestable_total'] == 25000


def review_fields(html):
    form = Form(html, '/goal/security-review')
    form.fields.update(cost_basis='40000', long_term='yes', taxable='yes', reference='Synthetic statement 2026-09-21')
    return form


def test_local_basis_prompt_save_refresh_and_stale_form_rejection(server):
    base, folder = server
    a = donor([position(basis=None, acquired=None, taxable=None)])
    build_office(a, folder)
    form = review_fields(_get(base + '/pages/goal_giving.html'))
    assert form.fields['revision']
    status, location, body = _post(base + form.action, form.fields)
    assert status == 303, body
    html = _get(base + location)
    assert '$40,000.00' in html and 'Illustrative gift / basis' in html
    assert 'saved review' in html
    assert _post(base + form.action, form.fields)[0] == 400
    saved = json.loads((folder / 'answers.json').read_text())
    assert inventory(model(saved))[0]['eligible']


def test_hosted_basis_review_persists_and_is_tenant_private(workspace):
    from hosting.app.main import SESSION
    client, receipt, folder = workspace
    response = client.get(receipt['path'] + '/pages/goal_giving.html')
    form = review_fields(response.text)
    response = post(client, receipt, '/goal/security-review', form.fields)
    assert response.status_code == 303, response.text
    assert '$40,000.00' in client.get(response.headers['location']).text
    assert post(client, receipt, '/goal/security-review', form.fields).status_code == 409
    client.cookies.set(SESSION, 'bob')
    assert client.get(receipt['path'] + '/pages/goal_giving.html').status_code == 404


def test_private_strategy_research_receives_rankings_not_public_security_court(tmp_path, monkeypatch):
    from test_officekit_strategy_proposals import Provider, execute, fake_sources
    from test_capital_planning import seed_plan
    fake_sources(monkeypatch)
    a = donor([position()])
    provider = Provider()
    p = execute(tmp_path, seed_plan(tmp_path, a), provider)
    assert p['status'] == 'needs_review', p['errors']
    assert p['charitable_goals'][0]['securities']['candidates'][0]['cost_basis'] == 10000
    assert 'Taxable A' in provider.calls[0]['messages'][0]['content']
    for call in provider.calls[1:4]:
        assert 'Taxable A' not in json.dumps(call)
    assert 'Taxable A' not in json.dumps(p['general'])
