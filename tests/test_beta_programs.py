"""Private beta/TLH lifecycle, real funding ceilings and household loss gates."""
import base64
from copy import deepcopy
from datetime import date, timedelta
import json

import pytest
from fastapi.testclient import TestClient

from officekit import build_from_answers, build_model
from officekit import beta_programs as B
from officekit.beta_harvest import overlay, review_household, record_harvest
from officekit.commitments import revision
from officekit.serve import build_office
from test_deployment_plan import answers, Form
from test_hosted_migration import Backend, MemoryStore, ORIGIN, office, upload, send


def snapshot():
    return {'name': 'Synthetic broad benchmark', 'as_of': date.today().isoformat(), 'source': 'Synthetic issuer file',
            'rows': [{'symbol': s, 'weight': w, 'sector': sec} for s, w, sec in [('AAA', .4, 'A'), ('BBB', .35, 'B'), ('CCC', .25, 'A')]]}


def setup(received=False, lots=True):
    a = answers()
    a['as_of'] = date.today().isoformat()
    a['positions'] = {'rows': [{'symbol': 'AAA', 'value': 80000, 'cost_basis': 100000, 'account': 'Taxable A', 'taxable': True,
        'lots': [{'taxlot_id': 'lot-a', 'value': 80000, 'cost': 100000, 'open': '2020-01-01'}] if lots else []}]}
    build_from_answers(a)
    if received:
        from officekit.inflows import propose
        a['sleeves'][0]['value'] += 5000000
        a = propose(a, {'action': 'receive', 'inflow_id': a['incoming']['id'], 'gross': '5000000', 'withheld': '0',
                       'date': date.today().isoformat(), 'account_id': a['sleeves'][0]['id'], 'reference': 'Synthetic receipt', 'included': 'yes'}, revision(a))
    p = B.normalize({'id': 'test-beta', 'label': 'Private beta plan', 'account': 'Taxable A', 'taxable': True,
        'bindings': {a['incoming']['id']: 100}, 'policy': {'max_names': 3, 'max_weight': .5, 'fee_bps': 10,
        'tax_rate': .3, 'gain_capacity': 1000000}, 'benchmark_snapshot': snapshot()})
    a['beta_programs'] = {p['id']: p}
    return a, p


def model(a):
    return build_model(build_from_answers(a))


def reviewed(p):
    review_household(p, {'complete': True, 'reference': 'Reviewed all household/spouse/IRA accounts', 'transactions': []})
    p['replacements']['AAA'] = {'symbol': 'ZZZ', 'rationale': 'Reviewed distinct exposure', 'reference': 'Replacement review', 'as_of': date.today().isoformat()}


def test_funding_and_constituents_are_source_bound_and_cents_reconcile():
    a, p = setup()
    before = deepcopy(a)
    v = B.view(p, model(a))
    assert v['state'] == 'proposed' and v['ready']
    assert v['budget']['current'] == 0 and v['budget']['pending'] == 3500000
    assert sum(r['pending'] for r in v['basket']['rows']) == 3500000
    assert max(r['weight'] for r in v['basket']['rows']) <= .5
    assert v['basket']['active_share'] == 0
    assert a == before


def test_infeasible_caps_do_not_allocate_or_renormalize_above_cap():
    a, p = setup()
    p['policy']['exclusions'] = ['BBB', 'CCC']
    v = B.view(p, model(a))
    assert not v['ready'] and not v['basket']['rows']


def test_combined_programs_cannot_double_allocate_an_inflow():
    a, p = setup()
    second = deepcopy(p); second['id'] = 'second'
    with pytest.raises(ValueError, match='100%'):
        B.save_program(a, second, model(a))
    p['bindings'][a['incoming']['id']] = 60
    second['bindings'][a['incoming']['id']] = 40
    updated = B.save_program(a, second, model(a))
    assert sum(B.allocation(p, model(updated))['pending'] for p in B.programs(updated).values()) == 3500000


@pytest.mark.parametrize('received', [False, True])
def test_approved_tax_floor_retained_once_before_and_after_receipt(received):
    a, p = setup(received)
    p['policy']['reserve_floor'] = 1855000
    v = B.view(p, model(a))
    assert v['budget']['total'] == 3145000
    assert v['budget']['additional_reserve'] == 355000
    assert not v['ready']


def test_lifecycle_requires_actual_funding_monitoring_and_current_approval():
    a, p = setup()
    pid = p['id']
    a = B.transition(a, model(a), pid, 'approve', 'Reviewed mandate')
    assert B.view(B.programs(a)[pid], model(a))['state'] == 'approved'
    with pytest.raises(ValueError, match='reconciled received'):
        B.transition(a, model(a), pid, 'fund', 'Wishful funding', 100)
    a, p = setup(True)
    a = B.transition(a, model(a), pid, 'approve', 'Reviewed mandate')
    a = B.transition(a, model(a), pid, 'fund', 'Custody reconciliation', 100000)
    assert B.view(B.programs(a)[pid], model(a))['state'] == 'funded'
    with pytest.raises(ValueError, match='Operating requires'):
        B.transition(a, model(a), pid, 'operate', 'No monitoring')
    reviewed(B.programs(a)[pid])
    a = B.transition(a, model(a), pid, 'operate', 'Lot and cash reconciliation')
    assert B.view(B.programs(a)[pid], model(a))['state'] == 'operating'
    B.programs(a)[pid]['policy']['max_weight'] = .45
    assert B.view(B.programs(a)[pid], model(a))['state'] == 'proposed'
    assert not B.view(B.programs(a)[pid], model(a))['approved']


def test_stale_lots_or_monitoring_drop_operating_readiness_without_erasing_history():
    a, p = setup(True)
    reviewed(p)
    p['approval'] = {'policy_hash': B.policy_hash(p), 'reference': 'Approved', 'as_of': date.today().isoformat()}
    p['funding'] = {'amount': 100000, 'reference': 'Bank', 'as_of': date.today().isoformat()}
    p['operation'] = {'status': 'operating', 'as_of': date.today().isoformat(), 'reference': 'Review'}
    assert B.view(p, model(a))['state'] == 'operating'
    p['wash_review']['as_of'] = (date.today() - timedelta(days=8)).isoformat()
    assert B.view(p, model(a))['state'] == 'funded'
    assert p['approval']['reference'] == 'Approved'


@pytest.mark.parametrize('days', [-30, 0, 30])
def test_household_buys_including_scheduled_buys_block_harvest(days):
    a, p = setup(); reviewed(p)
    p['wash_review']['transactions'] = [{'symbol': 'AAA', 'side': 'buy', 'account': 'Spouse IRA',
                                       'date': (date.today() + timedelta(days=days)).isoformat()}]
    result = overlay(p, model(a))
    assert not result['candidates'][0]['ready_for_review']
    assert result['reviewable_losses'] == 0


def test_overlay_records_lockout_but_never_releases_tax_cash():
    a, p = setup(); reviewed(p)
    baseline = B.allocation(p, model(a))
    h = overlay(p, model(a))
    assert h['reviewable_losses'] == 20000 and h['potential_tax_value'] == 6000
    r = h['candidates'][0]
    record_harvest(p, model(a), r['id'], r['fingerprint'], 'Broker confirmation')
    h = overlay(p, model(a))
    assert h['reviewable_losses'] == 0
    assert h['locks'][0]['repurchase_after'] == (date.today() + timedelta(days=31)).isoformat()
    assert not p['harvests'][0]['tax_reconciled']
    assert B.allocation(p, model(a)) == baseline
    with pytest.raises(ValueError):
        record_harvest(p, model(a), r['id'], r['fingerprint'], 'Duplicate')


def test_unknown_basis_and_position_estimates_cannot_be_harvest_ready():
    a, p = setup(lots=False); reviewed(p)
    h = overlay(p, model(a))
    assert not h['candidates'][0]['ready_for_review']
    a['positions']['rows'][0]['cost_basis'] = None
    h = overlay(p, model(a))
    assert not h['candidates'] and h['needs_review'][0]['cost_basis'] is None


def test_replacement_lockout_and_class_share_aliases_are_checked():
    a, p = setup(); reviewed(p)
    p['replacements']['AAA']['symbol'] = 'BRK.B'
    p['harvests'] = [{'symbol': 'BRK B', 'security_id': 'another', 'date': date.today().isoformat(), 'reference': 'Other household sale'}]
    assert any('replacement' in reason for reason in overlay(p, model(a))['candidates'][0]['reasons'])


@pytest.mark.parametrize('change', [{'max_weight': float('nan')}, {'max_names': 2.5}, {'fee_bps': -1}, {'mode': '130/30'}])
def test_invalid_or_leveraged_policy_rejected(change):
    with pytest.raises(ValueError):
        B.normalize({'policy': change})


def test_private_mandate_joins_discovery_and_capital_planner(tmp_path):
    from officekit_research.discovery import catalog
    from officekit.capital_planning import inputs
    a, p = setup()
    found = catalog(tmp_path, a)
    e = next(e for e in found['entries'] if e['kind'] == 'office_program')
    assert e['href'] == '/pages/beta_programs.html#program-test-beta'
    plan = inputs({'snapshot': {'answers': a, 'data': build_from_answers(a)}, 'deployment_source': {'id': a['incoming']['id']}})
    assert plan['beta_programs'][0]['id'] == p['id']
    assert plan['beta_programs'][0]['basket']['rows'][0]['symbol'] == 'AAA'


def test_hosted_import_is_private_linked_revision_guarded_and_read_only(office, monkeypatch):
    from hosting.app.main import create_app, SESSION, CSRF
    from hosting.app.offices import Offices
    from officekit.personal_context import empty
    from officekit.deployment import href
    a, p = setup()
    a.pop('beta_programs')
    a['office_id'] = json.loads((office / 'answers.json').read_text())['office_id']
    (office / 'personal_context.json').write_text(json.dumps(empty(a['office_id'])))
    build_office(a, office)
    store = MemoryStore()
    with TestClient(create_app(Backend(), ORIGIN, store=store), base_url=ORIGIN) as client:
        _, sid = upload(client, office)
        receipt = send(client, '/api/migrations/' + sid + '/activate', {}).json()
        client.cookies.set(SESSION, 'alice')
        page = client.get(receipt['path'] + '/pages/beta_programs.html')
        assert page.status_code == 200 and 'Eligible → Proposed' in page.text
        from bs4 import BeautifulSoup
        form = BeautifulSoup(page.text, 'html.parser').select('form')[-1]
        fields = {e['name']: e.get('value', '') for e in form.select('input[name]')}
        fields.update(action='import', inflow_id=a['incoming']['id'], allocation_pct='100',
                      program_json=json.dumps({'v': 1, 'program': p, 'approval': {'as_of': date.today().isoformat(), 'reference': 'Private approval'}}))
        result = client.post(receipt['path'] + '/beta/program', data=fields, headers={'Origin': ORIGIN}, follow_redirects=False)
        assert result.status_code == 303, result.text
        assert client.post(receipt['path'] + '/beta/program', data=fields, headers={'Origin': ORIGIN}).status_code == 409
        before = deepcopy(store.rows)
        monkeypatch.setattr('officekit.serve.render_saved_office', lambda *a: pytest.fail('Do not render unrelated pages'))
        detail = client.get(receipt['path'] + '/pages/beta_programs.html')
        assert 'Private beta plan' in detail.text and 'Private approval' in detail.text and 'Approved' in detail.text
        dep = client.get(receipt['path'] + href(a['incoming']['id']))
        assert 'program-test-beta' in dep.text
        assert store.rows == before
        client.cookies.set(SESSION, 'bob')
        assert client.get(receipt['path'] + '/pages/beta_programs.html').status_code == 404
        assert client.post(receipt['path'] + '/beta/program', data=fields, headers={'Origin': ORIGIN}).status_code == 404


def test_programs_withhold_linked_cash_from_additional_proposals():
    from officekit_ai.strategy_proposal import budget
    a, p = setup()
    proposal = {'brief': {'option': 'new_capital'}, 'snapshot': {'answers': a, 'data': build_from_answers(a)},
                'deployment_source': {'id': a['incoming']['id']}, 'target_pct': None}
    f = budget(proposal)
    assert f['current_budget'] == f['contingent_budget'] == f['proposal_ceiling'] == 0
    assert f['program_reserved_pending'] == 3500000
    p['bindings'][a['incoming']['id']] = 60
    proposal['snapshot']['data'] = build_from_answers(a)
    assert budget(proposal)['contingent_budget'] == 1400000


def test_cross_program_household_locks_and_buys_are_combined():
    a, p = setup(); reviewed(p)
    other = B.normalize({'id': 'other', 'account': 'Spouse', 'taxable': True})
    review_household(other, {'complete': True, 'reference': 'Spouse review', 'transactions': [], 'open_buys': ['AAA']})
    a['beta_programs']['other'] = other
    assert not overlay(p, model(a))['candidates'][0]['ready_for_review']
    other['wash_review']['open_buys'] = []
    other['harvests'] = [{'symbol': 'ZZZ', 'security_id': 'other-lot', 'date': date.today().isoformat(), 'reference': 'Spouse broker confirmation'}]
    h = overlay(p, model(a))
    assert not h['candidates'][0]['ready_for_review'] and h['locks'][0]['symbol'] == 'ZZZ'


def test_reapproval_and_resume_preserve_history_and_require_fresh_funding():
    a, p = setup(True); reviewed(p)
    pid = p['id']
    a = B.transition(a, model(a), pid, 'approve', 'First approval')
    a = B.transition(a, model(a), pid, 'fund', 'Bank statement', 100000)
    a = B.transition(a, model(a), pid, 'operate', 'First reconciliation')
    a = B.transition(a, model(a), pid, 'pause', 'Data feed unavailable')
    assert B.view(a['beta_programs'][pid], model(a))['state'] == 'funded'
    a = B.transition(a, model(a), pid, 'operate', 'Feed restored and reconciled')
    assert B.view(a['beta_programs'][pid], model(a))['state'] == 'operating'
    a['beta_programs'][pid]['policy']['max_weight'] = .45
    a = B.transition(a, model(a), pid, 'approve', 'Revised mandate approved')
    assert B.view(a['beta_programs'][pid], model(a))['state'] == 'approved'
    assert 'funding' not in a['beta_programs'][pid]
    assert len(a['beta_programs'][pid]['history']) >= 7


@pytest.mark.parametrize('field,value', [
    ('funding', {'amount': float('nan'), 'as_of': date.today().isoformat(), 'reference': 'Bad'}),
    ('operation', {'status': 'invented', 'as_of': date.today().isoformat(), 'reference': 'Bad'}),
    ('wash_review', {'complete': True, 'as_of': date.today().isoformat(), 'reference': 'Bad', 'transactions': 'bad'}),
    ('harvests', [{'date': 'invalid'}]),
    ('replacements', {'AAA': {'symbol': 'ZZZ'}}),
])
def test_malformed_durable_state_cannot_enter_office(field, value):
    a, p = setup(); p[field] = value
    assert B.validate(a['beta_programs'])
    with pytest.raises(ValueError):
        build_from_answers(a)


def test_agent_context_contains_policy_but_no_raw_activity_or_source_universe():
    a, p = setup(); reviewed(p)
    context = B.planning_data(build_from_answers(a))
    assert context['beta_programs'][0]['id'] == p['id']
    assert 'benchmark_snapshot' not in context['beta_programs'][0]
    assert 'wash_review' not in context['beta_programs'][0]


@pytest.mark.parametrize('kind,received,expected', [('windfall', False, 3480000), ('windfall', True, 3480000), ('income', False, 9000), ('income', True, 9000)])
def test_same_program_funds_windfall_and_income_after_goals_tax_and_bills(kind, received, expected):
    from test_capital_planning import planning_answers, record_receipt
    a = planning_answers(kind)
    if received:
        a = record_receipt(a, a['incoming']['amount'], 0)
    m = model(a)
    p = B.normalize({'id': 'same-program', 'bindings': {a['incoming']['id']: 100}, 'benchmark_snapshot': snapshot()})
    budget = B.allocation(p, m)
    assert budget['total'] == expected
    assert budget['current' if received else 'pending'] == expected
    assert budget['pending' if received else 'current'] == 0


def test_catalog_lists_selected_constituents_not_excluded_benchmark_members(tmp_path):
    from officekit_research.discovery import catalog
    a, p = setup()
    p['policy']['exclusions'] = ['AAA']
    entry = next(e for e in catalog(tmp_path, a)['entries'] if e['kind'] == 'office_program')
    assert set(entry['symbols']) == {'BBB', 'CCC'}


def test_additional_strategy_can_use_remaining_cash_after_program_reservation():
    from officekit_ai.strategy_proposal import budget
    a, p = setup(True)
    proposal = {'brief': {}, 'snapshot': {'answers': a, 'data': build_from_answers(a)}, 'target_pct': 10}
    f = budget(proposal)
    assert f['program_reserved_current'] == 3500000
    assert f['current_budget'] == 100000 and f['contingent_budget'] == 0
