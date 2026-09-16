"""portfolio_mix + growth calculator + risk officer."""
from officekit import build_model
from officekit.intake import build_from_answers
from officekit.portfolio_mix import current_mix, mix_stats
from officekit.risk_officer import review


def _m(sleeves, goals=None):
    return build_model(build_from_answers({"as_of": "2026-09-08", "profile": {},
                                           "sleeves": sleeves, "goals": goals or []}))


def test_mix_stats_more_stocks_more_return_and_vol():
    a = mix_stats(80, 20)
    b = mix_stats(20, 80)
    assert a["exp_return"] > b["exp_return"] and a["vol"] > b["vol"]
    assert 0 < b["vol"] < a["vol"] < 0.20


def test_current_mix_splits_categories():
    m = _m([{"category": "public_equity", "value": 700000, "name": "Eq"},
            {"category": "fixed_income", "value": 200000, "name": "B"},
            {"category": "cash", "value": 100000, "name": "C"}])
    c = current_mix(m)
    assert c["stocks_pct"] == 70.0 and c["bonds_pct"] == 20.0 and c["cash_pct"] == 10.0


def test_risk_flags_concentration():
    m = _m([{"category": "single_name_equity", "value": 5_000_000, "name": "NVDA"},
            {"category": "cash", "value": 500000, "name": "C"}])
    titles = [f["title"] for f in review(m, {})]
    assert any("Concentration" in t for t in titles)
    assert all(f["severity"] in ("high", "medium", "low", "info") for f in review(m, {}))


def test_risk_flags_goal_conflict():
    goals = [{"kind": "spending", "label": "SF house", "amount": 10_000_000, "id": "h"},
             {"kind": "retirement", "label": "Retire", "annual_spending": 400000, "date": "2050-01-01", "id": "r"}]
    m = _m([{"category": "public_equity", "value": 5_000_000, "name": "Eq"}], goals)
    finds = review(m, {"goals": goals})
    assert any("conflict" in f["title"].lower() for f in finds)


def test_risk_findings_carry_advice_and_severity_order():
    m = _m([{"category": "single_name_equity", "value": 9_000_000, "name": "X"}])
    finds = review(m, {})
    assert finds and all("advice" in f and f["advice"] for f in finds)
    sev = [f["severity"] for f in finds]
    order = {"high": 0, "medium": 1, "low": 2, "info": 3}
    assert sev == sorted(sev, key=lambda s: order[s])       # severity-ranked
