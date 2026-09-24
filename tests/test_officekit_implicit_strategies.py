"""implicit_strategies — the asset allocation IS a set of running strategies.
Registered as implemented decisions at build and attached to the goals they
fund, so a goal never reads "no strategy serving" beside the serving assets."""
from officekit import implicit_strategies as I
from officekit.schema import validate


DATA = {
    "as_of": "2026-09-07", "factors": ["S&P 500"],
    "sleeves": [
        {"name": "VTI", "kind": "asset", "category": "public_equity", "value": 500000, "beta": {}},
        {"name": "VCLAX", "kind": "asset", "category": "municipal_credit", "value": 100000, "beta": {}},
        {"name": "US Bond", "kind": "asset", "category": "fixed_income", "value": 30000, "beta": {}},
        {"name": "MMF", "kind": "asset", "category": "cash", "value": 50000, "beta": {}},
        {"name": "Mortgage", "kind": "liability", "category": "real_estate_debt", "value": -300000, "beta": {}},
    ],
    "goals": [{"id": "g1", "kind": "liquidity_floor", "label": "Floor", "amount": 50000},
              {"id": "g2", "kind": "retirement", "label": "Retire", "annual_spending": 120000,
               "date": "2050-01-01"}],
    "profile": {}}


def test_derive_maps_assets_only():
    implied = I.derive(DATA)
    assert set(implied) >= {"core_equity", "muni", "bonds", "cash_mgmt"}
    assert "real_estate_debt" not in implied and "concentrated" not in implied   # no such asset
    assert implied["core_equity"] == ["VTI"]


def test_register_marks_implemented_with_holding_origin():
    answers = {"as_of": "2026-09-07"}
    assert I.register(answers, DATA) is True
    decs = answers["strategy_decisions"]
    assert decs["cash_mgmt"]["status"] == "implemented"
    assert any(o["source"] == "holding" for o in decs["cash_mgmt"]["origins"])
    # idempotent
    assert I.register(answers, DATA) is False


def test_register_attaches_to_matching_goals_only():
    answers = {"as_of": "2026-09-07"}
    I.register(answers, DATA)
    decs = answers["strategy_decisions"]
    # liquidity_floor menu = cash_mgmt, bonds -> both held -> linked to g1
    assert any(o["source"] == "goal" and o["ref"] == "g1" for o in decs["cash_mgmt"]["origins"])
    assert any(o["source"] == "goal" and o["ref"] == "g1" for o in decs["bonds"]["origins"])
    # retirement menu = core_equity, direct_index, bonds -> held core_equity+bonds linked to g2
    assert any(o["source"] == "goal" and o["ref"] == "g2" for o in decs["core_equity"]["origins"])
    # muni is NOT in the liquidity/retirement menu (untaxed pc) -> not linked to either
    assert not any(o["source"] == "goal" for o in decs["muni"]["origins"])


def test_register_never_downgrades_explicit_decision():
    answers = {"strategy_decisions": {"core_equity": {"status": "declined", "origins": []}}}
    I.register(answers, DATA)
    assert answers["strategy_decisions"]["core_equity"]["status"] == "declined"


def test_holding_origin_passes_schema():
    data = {"as_of": "2026-09-07", "factors": ["S&P 500"], "profile": {},
            "sleeves": [{"name": "C", "kind": "asset", "category": "cash", "value": 1, "beta": {}}],
            "strategy_decisions": {"cash_mgmt": {"status": "implemented",
                                                 "origins": [{"source": "holding", "ref": "held: MMF",
                                                              "date": "2026-09-07"}]}}}
    assert validate(data) == []


def test_realized_losses_do_not_prove_an_operating_harvest_program():
    from officekit import implicit_strategies as IS
    # no direct_index sleeve, but realized harvest activity in the tax model
    data = {"sleeves": [{"kind": "asset", "category": "public_equity", "name": "Eq", "value": 1_000_000}],
            "tax_model": {"realized_losses_ytd": 494000}, "goals": []}
    answers = {}
    assert IS.harvest_evidence(data) is None
    IS.register(answers, data)
    for sid in ("direct_index", "harvest_engine"):
        assert sid not in answers["strategy_decisions"]


def test_no_harvest_evidence_leaves_direct_index_undecided():
    from officekit import implicit_strategies as IS
    data = {"sleeves": [{"kind": "asset", "category": "public_equity", "name": "Eq", "value": 1_000_000}],
            "tax_model": {}, "goals": []}
    answers = {}
    assert IS.harvest_evidence(data) is None
    IS.register(answers, data)
    assert "direct_index" not in answers.get("strategy_decisions", {})


def test_individual_equities_do_not_prove_direct_indexing_or_harvest_operation():
    from officekit import implicit_strategies as IS
    data = {"sleeves": [{"kind": "asset", "category": "public_equity",
                         "name": "Individual stocks", "value": 5_000_000,
                         "holdings": [{"company": "NVDA", "amount": 1e6},
                                      {"company": "AAPL", "amount": 1e6}]}],
            "tax_model": {}, "goals": []}
    assert IS.harvest_evidence(data) is None
    answers = {}
    IS.register(answers, data)
    assert 'direct_index' not in answers['strategy_decisions']
    assert 'harvest_engine' not in answers['strategy_decisions']


def test_legacy_auto_status_repaired_without_overwriting_explicit_approval():
    a = {'strategy_decisions': {'direct_index': {'status': 'implemented', 'origins': [{'source': 'holding', 'ref': 'old lots inference'}]},
                                'harvest_engine': {'status': 'implemented', 'origins': [{'source': 'principal', 'ref': 'reviewed program'}]}}}
    I.register(a, DATA)
    assert a['strategy_decisions']['direct_index']['status'] == 'considering'
    assert a['strategy_decisions']['harvest_engine']['status'] == 'implemented'


def test_fund_only_equity_sleeve_is_not_direct_indexed():
    """A pooled-fund sleeve (VTI/VTSAX — no individual holdings) is NOT direct
    indexed; you can't harvest its constituents."""
    from officekit import implicit_strategies as IS
    data = {"sleeves": [{"kind": "asset", "category": "public_equity",
                         "name": "US Equity — VTI + VTSAX", "value": 2_000_000}],  # no holdings
            "tax_model": {}, "goals": []}
    assert IS.harvest_evidence(data) is None
