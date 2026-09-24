"""officekit Phase-1 tests: beta priors, the CSV importer, intake, and the wizard
end-to-end — an external user's answers become their own office + disaster pages,
with no strings from the reference account leaking in.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from officekit import build_from_answers, build_model, render_office, render_scenarios, validate
from officekit.betas import DEFAULT_FACTORS, _BASE, default_beta
from officekit.importers import parse_positions_csv
from officekit.schema import CATEGORIES
from officekit.wizard import run as wizard_run

FIX = Path(__file__).resolve().parent / "fixtures" / "officekit"
CSV = FIX / "sample_positions.csv"

ANSWERS = {
    "owner": "Sam",
    "as_of": "2026-09-01",
    "profile": {"net_buyer": True, "uses_leverage": False, "premium_selling_allowed": False,
                "decumulating": False, "concentrated_low_basis": True},
    "sleeves": [
        {"category": "real_estate", "name": "Home", "value": 900000, "confidence": "tbd"},
        {"category": "real_estate_debt", "name": "Mortgage (6.1% fixed)", "value": 410000, "rate_pct": 6.1},
        {"category": "cash", "name": "Cash / MMF (Chase)", "value": 82000, "target_pct": 5},
    ],
    "imports": [{"kind": "positions_csv", "path": str(CSV), "account": "Fidelity brokerage"}],
    "incoming": {"amount": 250000, "eta": "Dec", "character": "ordinary", "rate": 0.42},
}


# ------------------------------------------------------------------- beta priors

def test_beta_priors_cover_every_category_and_factor():
    for cat in CATEGORIES:
        vec = default_beta(cat)
        assert set(vec) == set(DEFAULT_FACTORS), f"{cat} prior missing factors"
    assert set(_BASE) == CATEGORIES  # every schema category has an explicit prior


def test_beta_styles_modify_the_base():
    intl = default_beta("public_equity", "intl")
    assert intl["USD"] == -0.60 and intl["S&P 500"] == 0.85
    base = default_beta("public_equity")
    assert base["USD"] == 0.10
    assert default_beta("nonsense") == {f: 0.0 for f in DEFAULT_FACTORS}  # zero, not a guess


# ------------------------------------------------------------------ CSV importer

def test_csv_importer_classifies_and_splits():
    sleeves = parse_positions_csv(CSV, account="Fidelity brokerage")
    by_cat = {}
    for s in sleeves:
        by_cat.setdefault(s["category"], []).append(s)
    # statement total is fully accounted for (skip rows excluded)
    assert sum(s["value"] for s in sleeves) == 648095
    # NVDA is 28.6% of the statement -> its own concentrated sleeve
    conc = by_cat["single_name_equity"]
    assert len(conc) == 1 and "NVDA" in conc[0]["name"] and conc[0]["value"] == 185500
    # AAPL + SBUX pooled with a holdings list
    pooled = [s for s in by_cat["public_equity"] if s['name'].startswith('Individual stocks')]
    assert len(pooled) == 1 and len(pooled[0]["holdings"]) == 2 and pooled[0]["value"] == 42210
    # VTI + unknown mutual fund (FSXLX) share the plain US-equity bucket
    us = [s for s in by_cat["public_equity"] if "VTI" in s["name"]]
    assert us and us[0]["value"] == 250835 + 12300
    # intl style got the intl beta prior
    intl = [s for s in by_cat["public_equity"] if "Intl" in s["name"]]
    assert intl and intl[0]["beta"]["USD"] == -0.60 and intl[0]["value"] == 82080
    assert by_cat["fixed_income"][0]["value"] == 43920
    assert by_cat["cash"][0]["value"] == 31250      # SPAXX money market
    # every imported sleeve is statement-sourced and carries a beta + provenance note
    for s in sleeves:
        assert s["_confidence"] == "known" and s["beta"]
        assert any("positions export" in r for r in s["risks"])


def test_csv_importer_rejects_garbage(tmp_path):
    bad = tmp_path / "bad.csv"
    bad.write_text("just,some,cells\n1,2,3\n")
    with pytest.raises(ValueError):
        parse_positions_csv(bad)


# ------------------------------------------------------------------------ intake

def test_intake_builds_a_valid_sheet():
    data = build_from_answers(ANSWERS)
    assert validate(data) == []
    m = build_model(data)
    # liability sign flipped, rate_pct threaded into meta
    mort = next(s for s in m["sleeves"] if s["category"] == "real_estate_debt")
    assert mort["value"] == -410000 and mort["meta"]["rate_pct"] == 6.1
    # windfall -> pending sleeve with eta + an ORDINARY tax reserve (no loss offset)
    assert m["eta"] == "Dec"
    assert m["tax"]["net_tax"] == pytest.approx(250000 * 0.42)
    assert m["tax"]["offset"] == 0
    assert any(s["category"] == "tax_reserve" for s in m["sleeves"])
    # NW = assets (648,095 stmt + 900k home + 82k cash + 250k pending) - mortgage - reserve
    assert m["NW"] == 648095 + 900000 + 82000 + 250000 - 410000 - 105000


def test_intake_requires_an_asset():
    with pytest.raises(ValueError):
        build_from_answers({"owner": "X", "as_of": "2026-01-01",
                            "sleeves": [{"category": "real_estate_debt", "value": 100}]})


def test_intake_never_fabricates_the_unused_tax_rate():
    data = build_from_answers(ANSWERS)
    assert "rate_ltcg" not in data["tax_model"]      # character is ordinary
    assert data["tax_model"]["rate_ordinary"] == 0.42


# -------------------------------------------------------------- wizard end-to-end

PERSONAL = ["Ajay", "Parametric", "GOOGL", "Alphabet", "ADIG", "SG2-ZZ", "VCLAX", "038CAG0E4"]


def test_wizard_end_to_end(tmp_path):
    paths, m = wizard_run(ANSWERS, tmp_path)
    for k in ("answers", "balance_sheet", "office", "scenarios"):
        assert paths[k].exists(), f"{k} not written"
    office = paths["office"].read_text()
    scen = paths["scenarios"].read_text()
    strat = paths["strategies"].read_text()
    assert "Strategies" in strat and 'id="strat-index_hedge"' in strat
    assert 'href="sam_strategies.html#strat-' in scen        # mitigations are clickable
    assert ", Sam." in office and "Balance sheet as of 2026-09-01" in office
    assert "NVDA Concentrated" in office and "Mortgage (6.1% fixed)" in office
    assert "Scenario Planner" in scen and "Concentrated single-name shock" in scen
    # the account's data never leaks into an external client's pages
    for s in PERSONAL:
        assert s not in office and s not in scen and s not in strat, f"leak: {s}"
    # saved balance sheet re-validates and re-renders identically
    saved = json.loads(paths["balance_sheet"].read_text())
    assert validate(saved) == []
    assert render_scenarios(build_model(saved), strategies_href="sam_strategies.html") == scen
    assert render_office(build_model(saved), now=None) is not None


# --------------------------------------- typed holdings (no CSV) — same classifier

def test_typed_holdings_run_the_same_classifier():
    from officekit.importers import classify_positions
    rows = [{"symbol": "VTI", "value": 251000}, {"symbol": "VXUS", "value": 82000},
            {"symbol": "NVDA", "value": 185000}, {"symbol": "BND", "value": 44000},
            {"symbol": "SPAXX", "value": 31000}]
    sleeves = classify_positions(rows, account="typed test")
    by_cat = {s["category"]: s for s in sleeves}
    assert by_cat["single_name_equity"]["value"] == 185000        # NVDA >=20% -> concentrated
    assert "NVDA" in by_cat["single_name_equity"]["name"]
    assert by_cat["cash"]["value"] == 31000                        # SPAXX -> cash
    assert by_cat["fixed_income"]["value"] == 44000
    assert sum(s["value"] for s in sleeves) == 593000

    data = build_from_answers({"owner": "Kit", "as_of": "2026-09-03",
                               "profile": {"net_buyer": True},
                               "sleeves": [{"category": "cash", "value": 10000}],
                               "positions": {"account": "typed", "rows": rows}})
    assert validate(data) == []
    assert any(s["category"] == "single_name_equity" for s in data["sleeves"])


def test_classify_positions_rejects_empty():
    from officekit.importers import classify_positions
    with pytest.raises(ValueError):
        classify_positions([], account="x")
