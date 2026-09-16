"""goal_projection — when the serving strategies reach the goal."""
from officekit import goal_projection as GP


def _serving(pairs):
    return [{"sid": sid, "title": sid, "status": "implemented", "cur_val": v, "cur_pct": 0}
            for sid, v in pairs]


def test_blended_return_is_value_weighted():
    s = _serving([("core_equity", 300000), ("bonds", 100000)])   # .07 and .04
    assert abs(GP.blended_return(s) - (300000*0.07 + 100000*0.04)/400000) < 1e-9


def test_spending_reach_year_and_series():
    goal = {"kind": "spending", "amount": 1_000_000, "date": "2036-01-01"}
    p = GP.project(goal, _serving([("core_equity", 500000)]), "2026-01-01")
    assert p["applicable"] and not p["is_floor"]
    # 500k at 7% -> ~10.2y to 1M
    assert 9 < p["reach_years"] < 11
    assert p["series"][0][1] == 500000 and p["series"][-1][1] > 1_000_000
    assert p["target"] == 1_000_000


def test_already_funded_spending():
    goal = {"kind": "spending", "amount": 100000, "date": "2030-01-01"}
    p = GP.project(goal, _serving([("cash_mgmt", 250000)]), "2026-01-01")
    assert p["reach_years"] == 0.0 and p["funded_ratio"] >= 2.0
    assert "already funded" in p["verdict"]


def test_retirement_corpus_target():
    goal = {"kind": "retirement", "annual_spending": 120000, "date": "2050-01-01"}
    p = GP.project(goal, _serving([("core_equity", 1_000_000)]), "2026-01-01")
    assert abs(p["target"] - 120000 / GP.SWR) < 1     # 25x at 4% SWR


def test_liquidity_floor_is_hold_not_growth():
    goal = {"kind": "liquidity_floor", "amount": 50000}
    below = GP.project(goal, _serving([("cash_mgmt", 30000)]), "2026-01-01")
    above = GP.project(goal, _serving([("cash_mgmt", 80000)]), "2026-01-01")
    assert below["is_floor"] and "below" in below["verdict"]
    assert "above" in above["verdict"]
    assert below["series"] == []                      # a floor isn't a growth curve


def test_no_growth_never_reaches():
    goal = {"kind": "spending", "amount": 1_000_000, "date": "2030-01-01"}
    p = GP.project(goal, _serving([("cash_mgmt", 0)]), "2026-01-01")   # nothing serving
    assert p["reach_years"] is None and "doesn't reach" in p["verdict"]


def test_tax_efficiency_not_applicable():
    p = GP.project({"kind": "tax_efficiency", "label": "Harvest"}, _serving([("direct_index", 5_000_000)]), "2026-01-01")
    assert p["applicable"] is False


# ---- financed-purchase affordability + expense drag (2026-09-08) ----

def _mini_model(marketable=14_000_000, mortgage=720000):
    from officekit import build_model
    from officekit.intake import build_from_answers
    data = build_from_answers({
        "as_of": "2026-09-07", "profile": {},
        "sleeves": [{"category": "public_equity", "value": marketable, "name": "Equity"},
                    {"category": "real_estate_debt", "value": -mortgage, "name": "Mortgage",
                     "rate_pct": 6.0}]})
    return build_model(data)


def test_financed_house_is_not_affordable():
    m = _mini_model()
    goal = {"kind": "spending", "label": "San Francisco property purchase", "amount": 10_000_000,
            "id": "h1"}
    p = GP.project(goal, [], "2026-09-07", m)
    assert p["mode"] == "financed" and p["affordable"] is False
    assert p["mortgage"] == 10_000_000 * 0.75            # 25% down default
    assert p["annual_carry"] > p["sustainable"] * 1.5    # clearly over
    assert "NOT affordable" in p["verdict"]


def test_financed_respects_adjusted_params():
    m = _mini_model()
    goal = {"kind": "spending", "label": "beach house", "amount": 2_000_000, "id": "h2",
            "finance": {"down_pct": 60, "rate_pct": 5.0, "term_years": 15}}
    p = GP.project(goal, [], "2026-09-07", m)
    assert abs(p["mortgage"] - 800_000) < 1              # 40% financed
    assert p["down_pct"] == 60


def test_expense_drag_vs_sustainable():
    m = _mini_model()
    goal = {"kind": "expense", "label": "Overhead", "annual_amount": 600000, "id": "e1"}
    p = GP.project(goal, [], "2026-09-07", m)
    assert p["mode"] == "expense"
    # 14M * 4% - 720k*6% ~= 560k - 43k = 517k sustainable < 600k
    assert p["sustainable"] < 600000 and p["affordable"] is False


def test_small_expense_is_sustainable():
    m = _mini_model()
    goal = {"kind": "expense", "label": "Club dues", "annual_amount": 50000, "id": "e2"}
    p = GP.project(goal, [], "2026-09-07", m)
    assert p["affordable"] is True and "sustainable" in p["verdict"]
