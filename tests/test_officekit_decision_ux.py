"""Regression contracts behind the daily brief and strategy workspace.

Browser acceptance (filters, preview math, navigation, responsive layout) is
recorded in AGENT_HANDOFF.md; these checks cover persisted financial semantics.
"""
import copy
import json
from datetime import date

import pytest

from officekit import build_model, render_office, render_scenarios, render_strategies
from officekit.intake import build_from_answers
from officekit.goals import evaluate_in_model
from officekit.goal_projection import project
from officekit.goal_mandates import goal_strategy_menu
from officekit.portfolio_mix import current_mix, target_mix, validate_mix, mix_stats
from officekit.render_growth import render_growth
from officekit.render_imports import _age_days, render_imports
from officekit.risk_officer import review
from test_officekit_onboarding_e2e import server, _post


def model(sleeves=None, goals=None):
    return build_model(build_from_answers({"as_of": "2026-09-13", "profile": {},
        "sleeves": sleeves or [{"name": "Equity", "category": "public_equity", "value": 14_000_000},
                              {"name": "Mortgage", "category": "real_estate_debt", "value": -720000, "rate_pct": 6}],
        "goals": goals or []}))


HOUSE = {"kind": "spending", "label": "Property purchase", "amount": 10_000_000, "id": "house"}


def test_property_status_agrees_across_surfaces_and_exposes_both_constraints():
    m = model(goals=[HOUSE])
    ev = evaluate_in_model(HOUSE, m)
    p = project(HOUSE, [], m["d"]["as_of"], m)
    assert p["cash_needed"] < p["marketable"]
    assert ev["status"] == "SHORT" and not p["affordable"]
    assert ev["closing_ratio"] > 1 and ev["carry_ratio"] < 1
    assert goal_strategy_menu(m)["house"]["eval"] == ev
    assert any(f["title"] == "Funding gap — Property purchase" and f["detail"] == ev["detail"] for f in review(m))
    for html in (render_office(m), render_strategies(m, goal_menu=goal_strategy_menu(m))):
        assert "Funding gap" in html and "Cash to close" in html and "Annual carry" in html
    scenarios = render_scenarios(m)
    assert f'SHORT ·{ev["ratio"]:.2f}x' in scenarios


def test_scenario_recalculates_affordability_from_shocked_marks_without_mutating_base():
    goal = {**HOUSE, "amount": 3_000_000}
    m = model(goals=[goal]); before = copy.deepcopy(m)
    baseline = evaluate_in_model(goal, m)
    stressed = evaluate_in_model(goal, m, [(s, -.9*s["value"] if s["category"] == "public_equity" else 0) for s in m["sleeves"]])
    assert baseline["status"] == "OK" and stressed["status"] == "SHORT"
    assert stressed["assessment"]["marketable"] < baseline["assessment"]["marketable"]
    assert stressed["assessment"]["sustainable"] < 0
    assert m == before


def test_pending_money_cannot_fund_current_affordability_or_allocation():
    m = model(sleeves=[{"name": "Cash", "category": "cash", "value": 10000},
                      {"name": "Expected", "category": "cash_pending", "value": 50_000_000},
                      {"name": "Private", "category": "venture_private", "value": 8_000_000}])
    assert current_mix(m)["total"] == 10000
    assert evaluate_in_model(HOUSE, m)["assessment"]["marketable"] == 10000
    assert evaluate_in_model(HOUSE, m)["status"] == "SHORT"


@pytest.mark.parametrize("values", [(100, 2), (-1, 20), (float('nan'), 10), (float('inf'), 0), (60, 30, 20), (100.01, 0), (True, 20)])
def test_impossible_allocations_are_rejected(values):
    with pytest.raises(ValueError):
        validate_mix(*values)
    with pytest.raises(ValueError):
        mix_stats(*values)


def test_invalid_saved_mix_warns_without_silently_changing_answers():
    answers = {"target_mix": {"stocks_pct": 100, "bonds_pct": 2, "cash_pct": 0}}
    before = copy.deepcopy(answers); m = model()
    mix = target_mix(answers, m)
    assert sum(mix.values()) == pytest.approx(100)
    assert "saved target is invalid" in render_growth(m, answers)
    assert answers == before


def test_growth_post_rejects_invalid_mix_without_changing_saved_office(server):
    base, folder = server
    answers = {"as_of": "2026-09-13", "sleeves": [{"category": "cash", "value": 200000}]}
    from officekit.serve import build_office
    build_office(answers, folder)
    before = (folder / 'answers.json').read_bytes()
    status, _, body = _post(base + '/growth', {'stocks_pct': '100', 'bonds_pct': '2'})
    assert status == 400 and "100%" in body
    assert (folder / 'answers.json').read_bytes() == before
    status, loc, _ = _post(base + '/growth', {'stocks_pct': '60', 'bonds_pct': '30'})
    assert status == 303 and loc == '/pages/growth.html'
    assert json.loads((folder / 'answers.json').read_text())['target_mix'] == {'stocks_pct': 60, 'bonds_pct': 30, 'cash_pct': 10}


def test_future_utc_stamp_never_renders_a_negative_age():
    assert _age_days('2026-09-14T01:00:00+00:00', today=date(2026, 9, 13)) == 0
    assert _age_days('2026-09-01', today=date(2026, 9, 13)) == 12
    assert _age_days('unavailable') is None


def test_missing_credentials_offer_setup_but_previous_imports_can_retry():
    adapter = {'name': 'example', 'label': 'Example broker', 'kind': 'broker', 'can_fetch': True,
               'found': False, 'status': 'needs_key', 'detail': 'A key is needed.'}
    html = render_imports([adapter], [], [], [], pull_endpoint='/adapter/import')
    assert 'Set up connection' in html and 'Pull now' not in html
    ledger = [{'source_id': 'adapter:example', 'kind': 'adapter', 'pulled_utc': '2026-09-13', 'n_rows': 1}]
    html = render_imports([adapter], ledger, [], [], pull_endpoint='/adapter/import')
    assert 'Re-pull' in html


def test_unreviewed_pack_with_held_positions_is_a_holding_not_an_approval():
    t = {'sid': 'basket', 'label': 'Basket', 'value': 10, 'n': 1, 'thesis': 'A thesis',
         'pack': True, 'review_status': 'schema_valid', 'verdict': '', 'court_date': '',
         'next_date': '', 'positions': [{'symbol': 'X', 'mv': 10}]}
    html = render_strategies(model(), desk_theses=[t])
    assert 'data-state="held"' in html and 'Recorded court verdict' not in html
    t['value'], t['n'], t['positions'] = 0, 0, []
    html = render_strategies(model(), desk_theses=[t])
    assert 'data-state="draft"' in html and 'Draft · unreviewed' in html


def test_held_review_filters_work_without_pack_metadata():
    t = {'sid': 'basket', 'label': 'Basket', 'value': 10, 'n': 1, 'verdict': 'WATCH',
         'court_date': '', 'next_date': '', 'positions': []}
    html = render_strategies(model(), desk_theses=[t])
    assert 'data-state="held" data-review="true"' in html
    assert 'Under review <span>1</span>' in html
    t['verdict'] = 'BUY'
    html = render_strategies(model(), desk_theses=[t])
    assert 'data-review="false"' in html and 'Under review <span>0</span>' in html


def test_current_mix_rounding_reconciles_to_one_hundred_percent():
    m = model(sleeves=[{'category': 'public_equity', 'value': 1, 'name': 'Stock'},
                      {'category': 'fixed_income', 'value': 1, 'name': 'Bond'},
                      {'category': 'cash', 'value': 1, 'name': 'Cash'}])
    cur = current_mix(m)
    assert cur['stocks_pct'] + cur['bonds_pct'] + cur['cash_pct'] == pytest.approx(100)
    assert mix_stats(cur['stocks_pct'], cur['bonds_pct'], cur['cash_pct'])['vol'] > 0
