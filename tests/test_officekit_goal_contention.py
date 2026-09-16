"""goal_contention — goals compete for one shared capital + ongoing budget."""
from officekit import build_model
from officekit.intake import build_from_answers
from officekit.goal_contention import claims, contention


def _m(marketable=14_000_000, mortgage=720000, goals=None):
    return build_model(build_from_answers({
        "as_of": "2026-09-07", "profile": {},
        "sleeves": [{"category": "public_equity", "value": marketable, "name": "Eq"},
                    {"category": "real_estate_debt", "value": -mortgage, "name": "Mtg", "rate_pct": 6.0}],
        "goals": goals or []}))


HOUSE = {"kind": "spending", "label": "SF house", "amount": 10_000_000, "id": "h"}
FERRARI = {"kind": "spending", "label": "Ferrari", "amount": 500_000, "id": "f"}
RETIRE = {"kind": "retirement", "label": "Retire", "annual_spending": 300_000, "date": "2050-01-01", "id": "r"}


def test_claims_by_kind():
    m = _m()
    assert claims(HOUSE, m)["carry"] > 0 and claims(HOUSE, m)["capital"] > 0     # financed
    fc = claims(FERRARI, m)
    assert fc["carry"] == 0 and fc["capital"] > 500_000                          # cash, grossed up for tax
    assert claims(RETIRE, m)["capital"] == 0 and claims(RETIRE, m)["carry"] == 300_000


def test_house_plus_ferrari_plus_retirement_infeasible():
    m = _m(goals=[HOUSE, FERRARI, RETIRE])
    con = contention(m, [HOUSE, FERRARI, RETIRE])
    assert con["feasible"] is False
    assert con["carry_claim"] > con["carry_budget"]        # ongoing cost blows the budget
    assert "SF house" in con["squeezed"]                    # the house carry is what breaks it


def test_modest_goals_fit_together():
    small_house = {"kind": "spending", "label": "condo", "amount": 1_500_000, "id": "c",
                   "finance": {"down_pct": 30}}
    floor = {"kind": "liquidity_floor", "label": "Floor", "amount": 200_000, "id": "l"}
    m = _m(goals=[small_house, floor])
    con = contention(m, [small_house, floor])
    assert con["feasible"] is True and con["squeezed"] == []


def test_single_goal_has_no_contention_panel_data():
    # one goal still returns a coherent (feasible) result
    m = _m(goals=[FERRARI])
    con = contention(m, [FERRARI])
    assert con["n"] == 1 and con["feasible"] is True
