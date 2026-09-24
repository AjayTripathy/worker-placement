"""officekit Phase-0 tests.

1. GOLDEN BYTE-PARITY: renders are byte-stable against frozen fixtures
   (tests/fixtures/officekit/, frozen clock). Golden HISTORY: v1 goldens were
   rendered by the ORIGINAL desk/household.py + desk/disaster.py at Phase-0
   extraction time and proved the carve-out changed nothing; v2 goldens
   (2026-09-02, Phase 2) regenerated when the tax-bomb scenario was added
   (audited: only the new scenario); v3 (2026-09-02) the ratified
   Disaster→Scenario Planner rename (audited rename-only); v4 (2026-09-02)
   body-background fix (audited: one CSS line); v5 (2026-09-03) the
   scenario-CARDS redesign — probability/tripwires/playbook fold into
   expandable cards; audited for ZERO content loss (every mitigation row and
   section survives); v6 (2026-09-03) mitigations became links into the new
   STRATEGIES page (audited: link-wrapping only) and golden_strategies.html
   v7 (2026-09-04): many-to-many strategy membership — golden_strategies.html
   regenerated; audited diff = additions only (one "Rolled-up exposure" line
   per member-bearing card, value-weighted factor loadings); membership,
   ordering, and all prior content unchanged
   v8 (2026-09-05): strategy->asset click-through — holding rows under member
   sleeves link asset_<SYM>.html pages; audited diff = additions only
   was born. Golden filenames keep their historical names.
   v9 (2026-09-13): Home daily brief and Strategies lifecycle workspace;
   editors / alternate groupings disclose on demand, all mandate and holding
   forms retained, tenant-authored notes retained, no execution actions added.
   v10 (2026-09-21): Home incoming-capital plan starts ticker research and shows
   reserved funding, replacing the pro-rata before/after illustration.
   Regenerate goldens only on an intentional, audited output change.
2. DE-PERSONALIZATION: a generic client's balance sheet renders both pages with
   no account-specific strings leaking from the package.
3. Effects contract + scenario overlay merge + schema validation.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from officekit import (build_model, load_balance_sheet, render_office, render_scenarios,
                       render_strategies, validate)
from officekit import effects as fx
from officekit.scenarios import DEFAULT_SCENARIOS, scenarios_for

FIX = Path(__file__).resolve().parent / "fixtures" / "officekit"
ROOT = FIX / "root"

FROZEN_NOW = datetime(2026, 9, 2, 9, 0, 0)


def _fixture_harvest():
    """The desk harvest loader, replayed against the frozen fixture files."""
    sc = json.loads((ROOT / "desk/data/parametric_scorecard.json").read_text())
    ry = sc.get("realized_ytd") or {}
    net, asof = ry.get("net"), ry.get("asof")
    lots = json.loads((ROOT / "desk/data/parametric_realized.json").read_text()).get("lots", {})
    dates = [v.get("closed") for v in lots.values() if v.get("closed")]
    start = min(dates) if dates else None
    loss = max(0.0, -float(net))
    days = rate = None
    if start:
        d0 = datetime.strptime(start, "%Y-%m-%d")
        d1 = datetime.strptime(asof, "%Y-%m-%d")
        days = max((d1 - d0).days, 1)
        rate = loss / days
    return {"net": net, "loss": loss, "asof": asof, "coverage_start": start,
            "coverage_days": days, "daily_rate": rate}


@pytest.fixture()
def fixture_model():
    data = load_balance_sheet(ROOT / "desk/data/household.json")
    # This fixture models one specific inflow and its tax, now explicitly linked.
    next(s for s in data["sleeves"] if s["category"] == "cash_pending")["id"] = "fixture-inflow"
    data["tax_model"]["inflow_id"] = "fixture-inflow"
    return build_model(data, harvest=_fixture_harvest())


# ---------------------------------------------------------------- golden parity

def test_office_golden_parity(fixture_model):
    html = render_office(fixture_model, now=FROZEN_NOW)
    assert html == (FIX / "golden_household.html").read_text()


def test_scenarios_golden_parity(fixture_model):
    html = render_scenarios(fixture_model, effects_label="desk/effects.py")
    assert html == (FIX / "golden_disaster.html").read_text()


def test_strategies_golden_parity(fixture_model):
    html = render_strategies(fixture_model, scenarios_href="scenarios.html")
    assert html == (FIX / "golden_strategies.html").read_text()


# ------------------------------------------------------- generic client, no leaks

GENERIC = {
    "as_of": "2026-01-15",
    "factors": ["S&P 500", "Venture Capital", "Mortgage Debt", "Inflation", "Rates", "USD"],
    "profile": {"uses_leverage": False, "net_buyer": False, "premium_selling_allowed": True,
                "decumulating": True, "concentrated_low_basis": False},
    "sleeves": [
        {"name": "Brokerage — index funds", "kind": "asset", "category": "public_equity",
         "value": 900000, "target_pct": 60, "_confidence": "known", "risks": ["Market drawdown"],
         "beta": {"S&P 500": 1.0, "Venture Capital": 0.45, "Rates": -0.3}},
        {"name": "Home", "kind": "asset", "category": "real_estate", "value": 600000,
         "target_pct": None, "_confidence": "tbd", "risks": ["Illiquid"],
         "beta": {"S&P 500": 0.4, "Rates": -0.6, "Inflation": 0.5}},
        {"name": "Money market", "kind": "asset", "category": "cash", "value": 150000,
         "target_pct": 10, "_confidence": "known", "risks": ["Inflation erosion"],
         "beta": {"Inflation": -1.0}},
        {"name": "Home loan", "kind": "liability", "category": "real_estate_debt",
         "value": -300000, "target_pct": None, "_confidence": "known",
         "risks": ["Fixed-rate debt"], "beta": {"Mortgage Debt": 1.0, "Rates": 1.0}},
    ],
}

# strings that belong to the desk account's data, never to the package
PERSONAL = ["Ajay", "Parametric", "GOOGL", "Alphabet", "Sept", "ADIG", "SG2-ZZ",
            "VTSAX", "VCLAX", "CA wildfire", "038CAG0E4"]


def test_generic_client_renders_without_personal_strings():
    assert validate(GENERIC) == []
    m = build_model(GENERIC)
    office = render_office(m, now=FROZEN_NOW)
    scenarios = render_scenarios(m)
    strategies = render_strategies(m)
    for page, label in ((office, "office"), (scenarios, "scenarios"), (strategies, "strategies")):
        for s in PERSONAL:
            assert s not in page, f"personal string {s!r} leaked into the generic {label} page"
    # decumulating profile -> the 'dec' preset is pre-selected and index puts score Core hedge
    assert '<option value="dec" selected>' in scenarios
    assert "Core hedge" in scenarios
    # TBD sleeve surfaces in the generic inbox
    assert "1 TBD" in office


def test_generic_client_no_tax_model_no_reserve():
    m = build_model(GENERIC)
    assert m["tax"] is None
    assert all(s["category"] != "tax_reserve" for s in m["sleeves"])


# ---------------------------------------------------------------- effects contract

def _ctx(m, shocks):
    nominal = {"cash", "cash_pending", "tax_reserve", "real_estate_debt"}

    def move(s):
        if s["category"] in nominal:
            return 0.0
        return max(sum((s["beta"].get(f) or 0.0) * v for f, v in shocks.items()), -0.95)
    return {"m": m, "sc": {"shocks": shocks}, "move": move, "X": {}}


def test_effects_fixture_contract(fixture_model):
    m = fixture_model
    assert fx.tax_harvest_hedge(_ctx(m, {"S&P 500": -0.05})) is None
    big = fx.tax_harvest_hedge(_ctx(m, {"S&P 500": -0.30, "Venture Capital": -0.10}))
    bigger = fx.tax_harvest_hedge(_ctx(m, {"S&P 500": -0.45, "Venture Capital": -0.15}))
    assert big and bigger and bigger["delta"] > big["delta"] > 0   # convex cushion
    assert fx.short_book_rotation(_ctx(m, {"S&P 500": -0.30}))["shadow"] > 0
    assert len(fx.index()) == len(fx.EFFECTS) == 5


def test_effects_absent_data_means_no_fire():
    """A generic client without the account's structures gets None, not a guess."""
    m = build_model(GENERIC)
    assert fx.tax_harvest_hedge(_ctx(m, {"S&P 500": -0.30})) is None      # no tax model
    assert fx.short_book_rotation(_ctx(m, {"S&P 500": -0.30})) is None    # no short book
    assert fx.illiquid_mark_lag(_ctx(m, {"S&P 500": -0.30})) is None      # no venture sleeve
    rs = fx.fixed_debt_rate_short(_ctx(m, {"Rates": 0.12}))
    assert rs and "below-market fixed loan" in rs["note"]                 # no rate_pct meta


# ---------------------------------------------------------------- scenarios/schema

def test_scenario_overlay_merge():
    data = {"scenarios": {
        "replace": {"crash": {"desc": "patched"}},
        "drop": ["housing"],
        "add": [{"key": "custom", "ic": "🌀", "name": "Custom", "desc": "d",
                 "shocks": {"S&P 500": -0.1}, "opts": ["accept"],
                 "fix": {"tag": "MAINTAIN", "action": "hold"}}],
    }}
    scen = scenarios_for(data)
    keys = [s["key"] for s in scen]
    assert "housing" not in keys and "custom" in keys
    assert next(s for s in scen if s["key"] == "crash")["desc"] == "patched"
    # defaults untouched (deep-copied)
    assert next(s for s in DEFAULT_SCENARIOS if s["key"] == "crash")["desc"] != "patched"
    assert len(scen) == len(DEFAULT_SCENARIOS)  # -1 drop +1 add


def test_schema_catches_problems():
    bad = json.loads(json.dumps(GENERIC))
    bad["sleeves"][0]["kind"] = "thing"
    bad["sleeves"][3]["value"] = 300000            # positive liability
    bad["sleeves"][1]["beta"]["Bitcoin"] = 1.0     # unknown factor
    del bad["profile"]
    problems = validate(bad)
    assert len(problems) >= 4
    assert any("kind" in p for p in problems)
    assert any("liability" in p for p in problems)
    assert any("Bitcoin" in p for p in problems)


def test_fixture_data_validates():
    data = load_balance_sheet(ROOT / "desk/data/household.json")
    assert validate(data) == []
