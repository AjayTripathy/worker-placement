"""Intuited goals: the office derives commitments the balance sheet implies
(mortgage service, lifestyle spending), works up from whatever data exists,
flags its assumptions, and offers add-data + refine-with-AI affordances. Implicit
goals are re-derived every build and never persisted to the user's answers.
"""
import json

from officekit.intuition import implicit_goals, implicit_strategies, statistical_lifestyle_spend
from officekit.intake import build_from_answers
from officekit import build_model, render_office
from officekit.goal_projection import _existing_debt_service


def _data(sleeves, goals=None, profile=None):
    return {"as_of": "2026-09-02", "profile": profile or {"decumulating": False},
            "sleeves": sleeves, "goals": goals or []}


MORT = {"category": "real_estate_debt", "name": "Mortgage", "value": -720000, "kind": "liability"}
EQ = {"category": "public_equity", "name": "VTI", "value": 13_000_000, "kind": "asset"}


# ---- derivation --------------------------------------------------------------

def test_mortgage_goal_assumes_unknown_terms_and_flags_them():
    g = [x for x in implicit_goals(_data([MORT, EQ]), 16e6) if x["source"] == "mortgage"][0]
    assert g["kind"] == "expense" and g["annual_amount"] > 0
    assert set(g["missing"]) == {"rate_pct", "term_years"}          # both assumed
    assert g["facts"]["payoff_year"] == 2026 + 30
    assert any(a["assumed"] for a in g["assumptions"])


def test_mortgage_goal_uses_real_terms_when_present():
    debt = {**MORT, "rate_pct": 5.0, "term_years": 20}
    g = [x for x in implicit_goals(_data([debt, EQ]), 16e6) if x["source"] == "mortgage"][0]
    assert g["missing"] == [] and g["assumptions"] == []
    assert g["facts"]["rate_pct"] == 5.0 and g["facts"]["term_years"] == 20
    assert g["facts"]["payoff_year"] == 2026 + 20


def test_mortgage_carry_is_terminating():
    g = [x for x in implicit_goals(_data([MORT, EQ]), 16e6) if x["source"] == "mortgage"][0]
    assert g["terminating"] is True and g["ends_year"] == 2056


def test_property_tax_is_permanent_and_inferred_from_mortgage_when_no_home():
    g = [x for x in implicit_goals(_data([MORT, EQ]), 16e6) if x["source"] == "property_tax"][0]
    assert g["terminating"] is False and g["annual_amount"] > 0
    assert "home_value" in g["missing"] and g["facts"]["inferred_value"] is True


def test_property_tax_uses_real_home_value_when_present():
    home = {"category": "real_estate", "name": "Home", "value": 2_000_000, "kind": "asset"}
    g = [x for x in implicit_goals(_data([MORT, home, EQ]), 16e6) if x["source"] == "property_tax"][0]
    assert g["facts"]["inferred_value"] is False
    assert g["facts"]["home_value"] == 2_000_000 and "home_value" not in g["missing"]


def test_no_home_no_property_tax():
    srcs = {g["source"] for g in implicit_goals(_data([EQ]), 16e6)}
    assert "property_tax" not in srcs and "mortgage" not in srcs


def test_lifestyle_spend_is_estimated_and_income_funded_when_accumulating():
    g = [x for x in implicit_goals(_data([EQ]), 16e6) if x["source"] == "lifestyle"][0]
    assert g["estimated"] and g["portfolio_funded"] is False
    assert g["annual_amount"] == statistical_lifestyle_spend(16e6)


def test_lifestyle_spend_draws_on_portfolio_when_decumulating():
    g = [x for x in implicit_goals(_data([EQ], profile={"decumulating": True}), 16e6)
         if x["source"] == "lifestyle"][0]
    assert g["portfolio_funded"] is True


def test_unrelated_expense_preserves_intuited_lifestyle():
    goals = [{"kind": "expense", "label": "Spending", "annual_amount": 90000}]
    srcs = {g["source"] for g in implicit_goals(_data([EQ], goals=goals), 16e6)}
    assert "lifestyle" in srcs


def test_spend_bands_are_monotonic():
    xs = [statistical_lifestyle_spend(v) for v in (0.5e6, 3e6, 16e6, 50e6)]
    assert xs == sorted(xs) and len(set(xs)) == 4


# ---- integration: build, persistence, contention -----------------------------

def _answers():
    return {"as_of": "2026-09-02", "owner": "Test", "profile": {"decumulating": False},
            "sleeves": [dict(MORT), dict(EQ), {"category": "cash", "name": "Cash", "value": 250000}],
            "goals": [{"kind": "spending", "label": "House", "amount": 2_000_000, "id": "u1"}]}


def test_build_injects_implicit_goals_without_persisting_them():
    ans = _answers()
    data = build_from_answers(ans)
    implicit = [g for g in data["goals"] if g.get("implicit")]
    assert {g["source"] for g in implicit} == {"mortgage", "property_tax", "lifestyle"}
    # never written back into the user's answers dict
    assert all(not g.get("implicit") for g in ans["goals"])


def test_mortgage_counted_once_as_fixed_drag_not_doubled():
    m = build_model(build_from_answers(_answers()))
    goals = m["d"]["goals"]
    mort = next(g for g in goals if g.get("source") == "mortgage")
    ptax = next(g for g in goals if g.get("source") == "property_tax")
    # the fixed drag is exactly the portfolio-funded fixed carries (mortgage P&I +
    # property tax) — not those PLUS a separate interest subtraction on the same
    # debt (the double-count the reconciliation prevents)
    assert round(_existing_debt_service(m)) == mort["annual_amount"] + ptax["annual_amount"]


def test_direct_indexing_is_intuited_from_individual_equity():
    m = {"assets": [{"category": "direct_index", "value": 9_000_000,
                     "holdings": [{"company": "AAPL"}, {"company": "MSFT"}]},
                    {"category": "cash", "value": 250_000}]}
    strats = {s["id"]: s for s in implicit_strategies(m)}
    di = strats["implicit:strategy:direct_index"]
    assert di["status"] == "review" and di["href"] == "beta_programs.html"
    assert "direct index" in di["why"].lower()
    assert "implicit:strategy:cash_mgmt" in strats            # cash management too


def test_no_equity_no_direct_index_strategy():
    m = {"assets": [{"category": "cash", "value": 100_000}]}
    ids = {s["id"] for s in implicit_strategies(m)}
    assert "implicit:strategy:direct_index" not in ids


def test_strategies_page_renders_intuited_section():
    from officekit import render_strategies
    ans = {"as_of": "2026-09-02", "owner": "T", "profile": {},
           "sleeves": [{"category": "single_name_equity", "name": "AAPL", "value": 500_000},
                       {"category": "cash", "name": "Cash", "value": 100_000}]}
    m = build_model(build_from_answers(ans))
    html = render_strategies(m, scenarios_href="scenarios.html")
    assert "Strategies suggested by your holdings" in html
    assert "Direct indexing / tax-loss harvesting" in html
    assert "To refine, tell the AI" in html


def test_office_renders_intuited_badge_and_both_affordances():
    m = build_model(build_from_answers(_answers()))
    m["_commitment_revision"] = "fixture-revision"
    html = render_office(m, goals_endpoint="/goals", chat=True)
    assert "estimated" in html
    assert 'action="/commitments/update"' in html and "Save changes" in html
    assert "Refine with AI" in html and 'action="/commitments/preview"' in html
    assert "goalRefine(" not in html
    # intuited goals don't get a removable × or a projection link
    assert "goal_implicit" not in html
