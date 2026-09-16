"""officekit Phase-2 tests: goals through the tail, the tax-bomb scenario, and
the strategy-sleeve / adjudication seams (principal-ratified 2026-09-02).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from officekit import build_model, render_office, render_scenarios, validate
from officekit.goals import evaluate
from officekit.scenarios import scenarios_for

FIX = Path(__file__).resolve().parent / "fixtures" / "officekit"

GOALS = [
    {"kind": "retirement", "label": "Retirement", "date": "2050-01-01", "annual_spending": 120000},
    {"kind": "spending", "label": "College — eldest", "date": "2034-09-01", "amount": 300000},
    {"kind": "liquidity_floor", "label": "Emergency floor", "amount": 60000},
]

BASE = {
    "as_of": "2026-09-01",
    "factors": ["S&P 500", "Venture Capital", "Mortgage Debt", "Inflation", "Rates", "USD"],
    "profile": {"net_buyer": True, "uses_leverage": False, "premium_selling_allowed": False,
                "decumulating": False, "concentrated_low_basis": False},
    "owner": {"first_name": "Sam"},
    "goals": GOALS,
    "sleeves": [
        {"name": "Index funds", "kind": "asset", "category": "public_equity", "value": 3000000,
         "target_pct": None, "_confidence": "known", "risks": ["Market drawdown"],
         "beta": {"S&P 500": 1.0, "Venture Capital": 0.45, "Rates": -0.3}},
        {"name": "Home", "kind": "asset", "category": "real_estate", "value": 800000,
         "target_pct": None, "_confidence": "known", "risks": ["Illiquid"],
         "beta": {"S&P 500": 0.4, "Rates": -0.6, "Inflation": 0.5}},
        {"name": "Cash", "kind": "asset", "category": "cash", "value": 200000,
         "target_pct": None, "_confidence": "known", "risks": [], "beta": {"Inflation": -1.0}},
        {"name": "Mortgage", "kind": "liability", "category": "real_estate_debt", "value": -400000,
         "target_pct": None, "_confidence": "known", "risks": [],
         "beta": {"Mortgage Debt": 1.0, "Rates": 1.0}},
    ],
}


# ------------------------------------------------------------------- goal math

def test_goal_math_retirement_floor_spending():
    # retirement: 4% of 3.0M investable = 120k vs 120k spend -> exactly OK (1.0x)
    ev = evaluate(GOALS[0], nw_inv=3_000_000, liquid=1_000_000, as_of="2026-09-01")
    assert ev["status"] == "OK" and ev["ratio"] == pytest.approx(1.0)
    # a 40% investable hit -> 0.6x -> SHORT
    ev = evaluate(GOALS[0], nw_inv=1_800_000, liquid=600_000, as_of="2026-09-01")
    assert ev["status"] == "SHORT"
    # floor: 90k liquid vs 60k floor = 1.5x OK; 66k = 1.1x TIGHT; 50k BREACH->SHORT
    assert evaluate(GOALS[2], 0, 90_000, "2026-09-01")["status"] == "OK"
    assert evaluate(GOALS[2], 0, 66_000, "2026-09-01")["status"] == "TIGHT"
    assert evaluate(GOALS[2], 0, 50_000, "2026-09-01")["status"] == "SHORT"
    # dated spending is a no-growth liquidity check
    assert evaluate(GOALS[1], 0, 600_000, "2026-09-01")["status"] == "OK"
    assert evaluate(GOALS[1], 0, 320_000, "2026-09-01")["status"] == "TIGHT"


def test_goal_residence_excluded_from_investable():
    m = build_model(BASE)
    scen = render_scenarios(m)
    # investable = 3.0M equity + 200k cash (home + mortgage excluded);
    # retirement sustains 4% * 3.2M = 128k vs 120k -> OK in the Today column
    assert "Goals through the tail" in scen
    assert "3 goals × 8 scenarios" in scen
    office = render_office(m)
    assert "Your goals" in office and "Retirement" in office and "$120k/yr in 23y" in office


def test_goals_absent_means_no_section():
    data = {k: v for k, v in BASE.items() if k != "goals"}
    m = build_model(data)
    assert "Goals through the tail" not in render_scenarios(m)
    assert "Goals — life planning" not in render_office(m)


def test_goal_schema_validation():
    bad = json.loads(json.dumps(BASE))
    bad["goals"].append({"kind": "yacht"})
    bad["goals"].append({"kind": "retirement", "label": "no spend"})
    problems = validate(bad)
    assert any("yacht" not in p and "kind must be" in p for p in problems)
    assert any("annual_spending" in p for p in problems)
    assert validate(BASE) == []


# ---------------------------------------------------------------- tax-bomb scenario

def _account_model():
    from datetime import datetime
    from officekit import load_balance_sheet
    root = FIX / "root"
    sc = json.loads((root / "desk/data/parametric_scorecard.json").read_text())
    ry = sc.get("realized_ytd") or {}
    lots = json.loads((root / "desk/data/parametric_realized.json").read_text()).get("lots", {})
    dates = [v.get("closed") for v in lots.values() if v.get("closed")]
    start = min(dates) if dates else None
    loss = max(0.0, -float(ry["net"]))
    d0, d1 = datetime.strptime(start, "%Y-%m-%d"), datetime.strptime(ry["asof"], "%Y-%m-%d")
    days = max((d1 - d0).days, 1)
    harvest = {"net": ry["net"], "loss": loss, "asof": ry["asof"], "coverage_start": start,
               "coverage_days": days, "daily_rate": loss / days}
    data = load_balance_sheet(root / "desk/data/household.json")
    return build_model(data, harvest=harvest)


def test_taxbomb_present_iff_offset_at_risk():
    # the reference account has a harvest offset -> the scenario appears,
    # and its drawdown equals exactly the offset at risk
    m = _account_model()
    html = render_scenarios(m, effects_label="desk/effects.py")
    assert "Unsheltered gain (harvest engine fails)" in html
    assert "Systematic tax-loss harvesting" in html
    from officekit.fmt import fmt_usd
    off = m["tax"]["offset"]
    assert off > 0 and fmt_usd(-off) in html          # the scenario's dd == the offset at risk
    # a client with no tax model never sees it
    assert "Unsheltered gain" not in render_scenarios(build_model(BASE))


def test_taxbomb_markets_flat_only_tax_row_moves():
    m = _account_model()
    sc = next(s for s in scenarios_for(m["d"]) if s["key"] == "taxbomb")
    assert sc["shocks"] == {} and sc["tax_ov"] == {"no_offset": True}


# ------------------------------------------------- strategy sleeves + adjudication

def test_strategy_and_adjudication_chips_render():
    data = json.loads(json.dumps(BASE))
    data["sleeves"][0]["strategy"] = "quality_drawdown"
    data["sleeves"][0]["holdings"] = [
        {"company": "DSGX", "amount": 40000,
         "adjudication": {"verdict": "STARTER 6/10", "date": "2026-08-03", "ref": "courts_20260803/DSGX"}},
        {"company": "PINS", "amount": 30000},
    ]
    assert validate(data) == []
    office = render_office(build_model(data))
    assert "quality_drawdown" in office and "1 adjudicated" in office
    # a holdings adjudication without a verdict is rejected
    data["sleeves"][0]["holdings"][0]["adjudication"] = {"date": "2026-08-03"}
    assert any("adjudication" in p for p in validate(data))


# ----------------------------------------------- life events via goal_ov

def test_goal_ov_life_event_scenario():
    from officekit.goals import apply_goal_ov
    kid = {"kind": "spending", "label": "College — new kid", "date": "2045-09-01", "amount": 350000}
    ov = {"add": [kid], "modify": [{"kind": "retirement", "annual_spending_delta": 40000}]}
    eff = apply_goal_ov(GOALS, ov)
    assert len(eff) == len(GOALS) + 1
    assert next(g for g in eff if g["kind"] == "retirement")["annual_spending"] == 160000
    assert GOALS[0]["annual_spending"] == 120000            # base never mutated

    data = json.loads(json.dumps(BASE))
    data["scenarios"] = {"add": [{
        "key": "new_kid", "ic": "👶", "name": "Having a kid",
        "desc": "Spending rises, a college target appears — the goal set itself changes.",
        "shocks": {}, "goal_ov": ov, "opts": ["cash_buffer", "term_life"],
        "fix": {"tag": "INSURE / HOLD", "action": "Raise the floor, insure the earner, start the college sleeve."}}]}
    html = render_scenarios(build_model(data))
    assert "Having a kid" in html and "College — new kid" in html
    # the added goal exists only in the kid column: dash cells elsewhere
    grid = html.split("Goals through the tail")[1].split("</table>")[0]
    kid_row = [r for r in grid.split("<tr>") if "College — new kid" in r][0]
    assert kid_row.count(">—</td>") >= 8                    # absent from Today + the 8 market columns
    assert "4 goals ×" in html                              # row union includes the added goal


# ------------------------------------------------- strategies page (box 4 wired)

def test_every_mitigation_maps_to_a_strategy_or_accept():
    from officekit.mitigations import OPT, OPT_STRATEGY
    from officekit.render_strategies import STRATEGY_LIB
    for oid in OPT:
        if oid == "accept":
            assert oid not in OPT_STRATEGY       # deliberate: accepting needs no strategy page
            continue
        assert oid in OPT_STRATEGY, f"{oid} has no strategy mapping"
        assert OPT_STRATEGY[oid] in STRATEGY_LIB, f"{oid} maps to unknown strategy"


def test_strategy_statuses_and_decisions():
    from officekit import render_strategies
    data = json.loads(json.dumps(BASE))
    data["strategy_decisions"] = {
        "index_hedge": {"status": "declined", "note": "accumulator doctrine"},
        "real_assets": {"status": "considering", "target_pct": 5},
    }
    html = render_strategies(build_model(data))
    assert 'id="strat-core_equity"' in html and "IMPLEMENTED" in html   # matching sleeve
    assert "DECLINED" in html and "accumulator doctrine" in html
    assert "CONSIDERING" in html and "5%</b> target" in html
    assert "NOT DECIDED" in html                                        # undecided stays honest
    assert "openHash" in html                                           # anchor-open JS
    # invalid decision status fails validation loudly
    data["strategy_decisions"]["trend"] = {"status": "yolo"}
    assert any("strategy_decisions[trend]" in p for p in validate(data))


# ------------------------------------------- mandates: two doors, one paper trail

def test_adopt_from_scenario_records_origin_and_never_downgrades():
    from officekit.mandates import adopt_from_scenario
    answers = {"strategy_decisions": {"harvest_engine": {"status": "implemented", "note": "x"}}}
    sid = adopt_from_scenario(answers, "put_index", "crash", today=__import__("datetime").date(2026, 9, 3))
    assert sid == "index_hedge"
    dec = answers["strategy_decisions"]["index_hedge"]
    assert dec["status"] == "planned"
    assert dec["origins"][0] == {"source": "scenario", "ref": "crash/put_index", "date": "2026-09-03"}
    # adopting an implemented strategy adds an origin but keeps the status
    adopt_from_scenario(answers, "harvest_engine", "taxbomb")
    kept = answers["strategy_decisions"]["harvest_engine"]
    assert kept["status"] == "implemented" and kept["origins"][0]["source"] == "scenario"
    with pytest.raises(ValueError):
        adopt_from_scenario(answers, "accept", "crash")     # deliberate: no strategy for 'accept'


def test_create_adhoc_custom_and_library_attach():
    import importlib
    from officekit.mandates import create_adhoc
    from officekit import render_strategies
    rs_mod = importlib.import_module("officekit.render_strategies")
    answers = {}
    sid = create_adhoc(answers, "Japan value", status="implemented", target_pct=4,
                       note="TSE-reform cash fortresses", subassets=["8135.T-class nets", "TOB anticipation"])
    assert sid == "japan_value" and sid not in rs_mod.STRATEGY_LIB
    assert answers["strategy_decisions"][sid]["title"] == "Japan value"
    # a title matching the library attaches there instead of defining a custom
    sid2 = create_adhoc(answers, "Trend", status="declined")
    assert sid2 == "trend" and "title" not in answers["strategy_decisions"]["trend"]
    with pytest.raises(ValueError):
        create_adhoc(answers, "Bad", status="yolo")

    data = json.loads(json.dumps(BASE))
    data["strategy_decisions"] = answers["strategy_decisions"]
    html = render_strategies(build_model(data))
    assert "Japan value" in html and "TSE-reform cash fortresses" in html
    assert "principal-directed" in html                     # the mandate trail renders
    assert "8135.T-class nets" in html


def test_mandate_affordances_only_render_with_endpoints():
    from officekit import render_scenarios as rscen, render_strategies
    m = build_model(json.loads(json.dumps(BASE)))
    assert "Adopt →" not in rscen(m)                        # static pages: goldens safe
    assert "Build proposal →" in rscen(m, adopt_endpoint="/strategy/adopt")
    assert "Record the mandate" not in render_strategies(m)
    assert "Build proposal →" in render_strategies(m, create_endpoint="/strategy/new")


# ------------------------------------------------- many-to-many strategy membership

class TestStrategyMembership:
    """Principal ruling 2026-09-04: strategies are views over the one asset
    pool — many-to-many, whole-asset edges, at sleeve AND holding level.
    Explicit tags are authoritative; category match is only a fallback for
    strategies with no explicit member, over sleeves with no tags at all."""

    def _model(self, sleeves):
        from officekit.model import build_model
        return build_model({"as_of": "2026-09-02",
                            "factors": ["S&P 500", "Rates"],
                            "profile": {}, "sleeves": sleeves})

    def _rows(self, m):
        from officekit.render_strategies import resolve_strategies
        return {r["sid"]: r for r in resolve_strategies(m, [])}

    def test_sleeve_in_many_strategies_and_overlapping_rollups(self):
        m = self._model([
            {"name": "T&D", "kind": "asset", "category": "public_equity", "value": 100000,
             "beta": {"S&P 500": 1.0, "Rates": 0.5},
             "strategies": ["core_equity", "duration_mgmt"]}])
        rows = self._rows(m)
        assert rows["core_equity"]["sleeves"] == rows["duration_mgmt"]["sleeves"]
        # overlap is legitimate: both views claim the full value
        assert rows["core_equity"]["cur_pct"] == rows["duration_mgmt"]["cur_pct"] == 100.0
        assert rows["duration_mgmt"]["status"] == "implemented"
        assert rows["duration_mgmt"]["expo"]["Rates"] == 0.5

    def test_holding_level_membership_and_beta_rollup(self):
        m = self._model([
            {"name": "Alpha book", "kind": "asset", "category": "public_equity",
             "value": 500000, "beta": {"S&P 500": 0.2, "Rates": 0.8},
             "strategies": ["core_equity"],
             "holdings": [{"company": "8795.T", "amount": 50000,
                           "strategies": ["duration_mgmt"]}]}])
        rows = self._rows(m)
        dm = rows["duration_mgmt"]
        assert not dm["sleeves"] and len(dm["holds"]) == 1
        assert dm["holds"][0][0]["company"] == "8795.T"
        assert dm["mem_val"] == 50000
        assert dm["expo"]["Rates"] == 0.8  # holding rides its parent sleeve's loadings
        # the parent sleeve is a member of core_equity, not double-listed in duration_mgmt
        assert rows["core_equity"]["mem_val"] == 500000

    def test_tagged_sleeve_never_claimed_by_category_fallback(self):
        m = self._model([
            {"name": "Japan value", "kind": "asset", "category": "public_equity",
             "value": 100000, "beta": {}, "strategies": ["custom_japan"]},
            {"name": "VTI", "kind": "asset", "category": "public_equity",
             "value": 300000, "beta": {}}])
        m["d"]["strategy_decisions"] = {"custom_japan": {"status": "implemented", "title": "Japan value"}}
        rows = self._rows(m)
        # core_equity's category fallback sees only the UNTAGGED sleeve
        assert [s["name"] for s in rows["core_equity"]["sleeves"]] == ["VTI"]
        assert [s["name"] for s in rows["custom_japan"]["sleeves"]] == ["Japan value"]

    def test_legacy_singular_strategy_tag_still_binds(self):
        from officekit.model import strategy_tags
        m = self._model([
            {"name": "SMA", "kind": "asset", "category": "direct_index",
             "value": 100000, "beta": {}, "strategy": "direct_index"}])
        assert strategy_tags({"strategy": "a", "strategies": ["b", "a"]}) == ["b", "a"]
        assert [s["name"] for s in self._rows(m)["direct_index"]["sleeves"]] == ["SMA"]

    def test_schema_validates_strategies_lists(self):
        from officekit.schema import validate
        base = {"as_of": "2026-09-02", "factors": [], "profile": {}}
        bad = {**base, "sleeves": [{"name": "X", "kind": "asset", "category": "cash",
                                    "value": 1, "beta": {}, "strategies": "core_equity",
                                    "holdings": [{"company": "Y", "strategies": [1]}]}]}
        probs = validate(bad)
        assert any("strategies must be a list" in x for x in probs)
        assert any("holdings[0].strategies" in x for x in probs)


# ---------------------------------------------------- agent origin (ratified 2026-09-04)

class TestAgentOrigin:
    """`agent` is the third origin source, queue-for-adoption: an agent path can
    only ever file `considering`, never touch an existing status, and every
    proposal's origin ref points at a frozen agent_call ledger record."""

    def test_queue_files_considering_with_agent_origin(self):
        from officekit.mandates import queue_agent_proposal
        answers = {}
        sid = queue_agent_proposal(answers, "Japan value", ref="rec-123",
                                   target_pct=4, note="fit argument", desc="d")
        dec = answers["strategy_decisions"][sid]
        assert dec["status"] == "considering"
        assert dec["origins"] == [{"source": "agent", "ref": "rec-123",
                                   "date": dec["origins"][0]["date"]}]

    def test_queue_never_touches_an_existing_status(self):
        from officekit.mandates import queue_agent_proposal
        answers = {"strategy_decisions": {"index_hedge": {
            "status": "declined", "note": "doctrine", "target_pct": 0}}}
        queue_agent_proposal(answers, "Index hedge", ref="rec-9", target_pct=5, note="agent says")
        dec = answers["strategy_decisions"]["index_hedge"]
        assert dec["status"] == "declined"          # queue-only: no overwrite
        assert dec["note"] == "doctrine"
        assert dec["target_pct"] == 0
        assert dec["origins"][-1]["source"] == "agent"   # but the proposal IS on the trail

    def test_trail_renders_agent_origin_and_schema_accepts_it(self):
        from officekit.model import build_model
        from officekit.render_strategies import render_strategies
        from officekit.schema import validate
        data = {"as_of": "2026-09-02", "factors": ["S&P 500"], "profile": {},
                "sleeves": [{"name": "Cash", "kind": "asset", "category": "cash",
                             "value": 1000, "beta": {}}],
                "strategy_decisions": {"japan_value": {
                    "status": "considering", "title": "Japan value",
                    "origins": [{"source": "agent", "ref": "rec-123", "date": "2026-09-04"}]}}}
        assert validate(data) == []
        html = render_strategies(build_model(data))
        assert "agent-proposed (rec-123) — queued, human adopts" in html
        bad = {**data, "strategy_decisions": {"x": {
            "status": "planned", "origins": [{"source": "robot", "ref": "r"}]}}}
        assert any("origin source" in x for x in validate(bad))

    def test_plugin_graceful_absence_and_frozen_call_flow(self, tmp_path, monkeypatch):
        import json
        import officekit_ai as ai
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: tmp_path))
        assert ai.available() is False
        import pytest as _pytest
        with _pytest.raises(RuntimeError):
            ai.client()
        # the frozen-call flow needs no API: freeze, then queue with the record id as ref
        answers = {}
        ledger = tmp_path / "learning.jsonl"
        from officekit.personal_context import empty
        sid, rec = ai.propose_strategy(answers, ledger, "Japan value",
                                       argument="fits the goals grid",
                                       personal_context=empty("oid-1"), office_id="oid-1")
        assert answers["strategy_decisions"][sid]["origins"][0]["ref"] == rec["id"]
        row = json.loads(ledger.read_text().splitlines()[0])
        assert row["kind"] == "agent_call" and row["office_id"] == "oid-1"
        assert row["payload"]["capability"] == "strategy_draft"
        # agent_call never leaves through the shareable exit
        from officekit.learning import export_shareable
        assert export_shareable(ledger) == []


# ------------------------------------------- personal context (plane 2, contract #9)

class TestPersonalContext:
    """Ruling 2026-09-04: personal context never ships as content, ALWAYS ships
    as structure. Empty-but-asserted passes the gate; absent refuses. Exclusions
    are enforced in code; the document never reaches the shareable path."""

    def test_empty_validates_and_passes_the_gate(self):
        from officekit.personal_context import empty, require, validate
        pc = empty("a11e0f5e-9e1c-4f6d-8c2a-000000000001")
        assert validate(pc) == []
        assert require(pc) is pc

    def test_absent_refuses_loudly(self):
        import pytest as _pytest
        from officekit.personal_context import require
        with _pytest.raises(RuntimeError, match="empty is fine; absent is not"):
            require(None)

    def test_agent_advise_path_is_gated(self, tmp_path):
        import pytest as _pytest
        import officekit_ai as ai
        with _pytest.raises(RuntimeError, match="personal context required"):
            ai.propose_strategy({}, tmp_path / "l.jsonl", "X", argument="a",
                                personal_context=None)

    def test_validation_catches_bad_fields(self):
        from officekit.personal_context import validate
        probs = validate({"v": 1,
                          "exclusions": [{"scope": "planet", "value": "IBM"}, {"scope": "ticker"}],
                          "doctrine": [{"id": "x"}]})
        assert any("scope" in x for x in probs)
        assert any("value is required" in x for x in probs)
        assert any("id and rule" in x for x in probs)

    def test_exclusion_checker_catches_sleeve_and_holding(self):
        from officekit.personal_context import check_exclusions
        pc = {"v": 1, "exclusions": [{"scope": "issuer", "value": "IBM"},
                                     {"scope": "sector", "value": "defense"}]}
        data = {"sleeves": [
            {"name": "IBM RSUs (vested)", "holdings": []},
            {"name": "Alpha book", "holdings": [{"company": "IBM", "amount": 1000},
                                                {"company": "DSGX", "amount": 500}]}]}
        v = check_exclusions(data, pc)
        wheres = [x["where"] for x in v]
        assert any("sleeve" in w for w in wheres) and any("holding IBM" in w for w in wheres)
        assert len(v) == 2  # sector exclusions are advisory, not code-checked

    def test_desk_flagship_instance_is_valid_and_asserts_ibm(self):
        import json
        from pathlib import Path as _P
        from officekit.personal_context import validate
        pc = json.loads(_P("desk/data/personal_context.json").read_text())
        assert validate(pc) == []
        assert any(e["value"] == "IBM" for e in pc["exclusions"])

    def test_serve_onboarding_writes_empty_but_asserted(self, tmp_path):
        import json
        from officekit.personal_context import load
        from officekit.serve import build_office
        answers = {"as_of": "2026-09-02",
                   "sleeves": [{"category": "cash", "value": 1000}]}
        build_office(answers, tmp_path)
        pc = load(tmp_path)
        assert pc is not None and pc["office_id"] == answers["office_id"]
        assert pc["exclusions"] == []
        # a second build never overwrites tenant content
        pc["doctrine"].append({"id": "r1", "rule": "no crypto"})
        (tmp_path / "personal_context.json").write_text(json.dumps(pc))
        build_office(answers, tmp_path)
        assert load(tmp_path)["doctrine"] == [{"id": "r1", "rule": "no crypto"}]


# ------------------------------------------------------- the goals door (/goals)

class FakeForm:
    def __init__(self, d): self.d = d
    def getvalue(self, k): v = self.d.get(k); return v[0] if isinstance(v, list) else v
    def getlist(self, k): v = self.d.get(k, []); return v if isinstance(v, list) else [v]
    def __contains__(self, k): return k in self.d


class TestGoalsDoor:
    """Post-onboarding goal editing: edits preserve the goal's UUID (grading
    history spans the change), removes drop it, new rows get fresh ids at
    build. The editor renders only when a write endpoint is passed — the desk
    page and goldens stay byte-identical."""

    def test_edit_preserves_id_remove_drops_new_mints(self, tmp_path):
        from officekit.serve import build_office, goals_from_form
        answers = {"as_of": "2026-09-02",
                   "sleeves": [{"category": "cash", "value": 500000}],
                   "goals": [{"kind": "retirement", "label": "Retirement", "annual_spending": 100000},
                             {"kind": "liquidity_floor", "label": "Floor", "amount": 20000}]}
        data = build_office(answers, tmp_path)
        rid = data["goals"][0]["id"]
        fid = data["goals"][1]["id"]
        # edit retirement (keep id), remove the floor, add a college goal
        form = FakeForm({"gid": [rid, fid, ""],
                         "gkind": ["retirement", "", "spending"],
                         "glabel": ["Retirement", "Floor", "College"],
                         "gdate": ["2050-01-01", "", "2036-09-01"],
                         "gamt": ["120000", "20000", "300000"]})
        answers["goals"] = goals_from_form(form)
        data2 = build_office(answers, tmp_path)
        by_kind = {g["kind"]: g for g in data2["goals"]}
        assert by_kind["retirement"]["id"] == rid                  # identity survives the edit
        assert by_kind["retirement"]["annual_spending"] == 120000  # the edit landed
        assert "liquidity_floor" not in by_kind                    # removed
        assert by_kind["spending"]["id"] not in (rid, fid)         # fresh mint
        assert by_kind["spending"]["amount"] == 300000

    def test_editor_gated_on_endpoint(self):
        from officekit.model import build_model
        from officekit.render_office import render_office
        data = {"as_of": "2026-09-02", "factors": ["S&P 500"], "profile": {},
                "sleeves": [{"name": "Cash", "kind": "asset", "category": "cash",
                             "value": 1000, "beta": {}}]}
        m = build_model(data)
        assert 'action="/goals/add"' not in render_office(m)            # desk/golden path: no editor
        html = render_office(m, goals_endpoint="/goals")
        assert 'action="/goals/add"' in html                            # goal-less office can add
        assert "Sabbatical year" in html                                # sample quick-add chips render
        # remove forms appear once a goal exists
        m2 = build_model({**data, "goals": [{"kind": "spending", "label": "Car",
                                             "amount": 60000, "id": "g-1"}]})
        assert 'action="/goals/remove"' in render_office(m2, goals_endpoint="/goals")

    def test_goal_lib_samples_are_valid(self):
        from officekit.goals import GOAL_LIB
        from officekit.schema import GOAL_KINDS
        assert len(GOAL_LIB) >= 10
        assert all(s["kind"] in GOAL_KINDS and s["label"] and s["amount"] > 0 for s in GOAL_LIB)
        assert any(s["kind"] == "retirement" for s in GOAL_LIB)
        assert any(s["kind"] == "liquidity_floor" for s in GOAL_LIB)


# --------------------------------------- goal -> strategy decomposition (3rd source)

class TestGoalDecomposition:
    """goal -> funding requirement -> gap posture -> horizon template -> sized
    proposal -> queued (origin source "goal", ref = goal_id). Deterministic,
    idempotent, queue-only."""

    def _model(self, goals, nw_cash=1_000_000):
        from officekit.intake import build_from_answers
        from officekit.model import build_model
        answers = {"as_of": "2026-09-04",
                   "sleeves": [{"category": "cash", "value": nw_cash}],
                   "goals": goals}
        return build_from_answers(answers), answers

    def test_horizon_templates_and_sizing(self):
        from officekit.goal_mandates import goal_strategies
        from officekit.model import build_model
        data, _ = self._model([
            {"kind": "liquidity_floor", "label": "Floor", "amount": 50000},
            {"kind": "spending", "label": "Kitchen", "amount": 100000, "date": "2027-06-01"},
            {"kind": "spending", "label": "College", "amount": 300000, "date": "2031-09-01"},
            {"kind": "spending", "label": "Second home", "amount": 350000, "date": "2040-01-01"},
            {"kind": "retirement", "label": "Retirement", "date": "2050-01-01", "annual_spending": 100000}])
        props = {p["goal_label"]: p for p in goal_strategies(build_model(data))}
        assert props["Floor"]["sid"] == "cash_mgmt" and props["Floor"]["target_pct"] == 5.0
        assert props["Kitchen"]["sid"] == "cash_mgmt"          # <2y: certainty, not return
        assert props["College"]["sid"] == "bonds"              # 2-7y, no tax state
        assert props["Second home"]["sid"] == "core_equity"    # 7y+
        assert props["Retirement"]["sid"] == "core_equity" and props["Retirement"]["target_pct"] is None
        assert "$300,000 / NW = 30% target" in props["College"]["note"]

    def test_tax_state_routes_mid_horizon_to_muni(self):
        from officekit.goal_mandates import goal_strategies
        from officekit.model import build_model
        data, _ = self._model([{"kind": "spending", "label": "College",
                                "amount": 300000, "date": "2031-09-01"}])
        pc = {"v": 1, "jurisdictions": {"tax_state": "CA"}}
        assert goal_strategies(build_model(data), pc)[0]["sid"] == "muni"

    def test_queue_is_idempotent_and_never_touches_decisions(self):
        from officekit.goal_mandates import goal_strategies, queue_goal_proposals
        from officekit.model import build_model
        data, answers = self._model([
            {"kind": "liquidity_floor", "label": "Floor", "amount": 50000},
            {"kind": "spending", "label": "College", "amount": 300000, "date": "2031-09-01"}])
        answers["strategy_decisions"] = {"bonds": {"status": "declined", "note": "duration doctrine",
                                                   "target_pct": 0}}
        props = goal_strategies(build_model(data))
        q1 = queue_goal_proposals(answers, props)
        q2 = queue_goal_proposals(answers, props)      # rebuild: no duplicates
        assert set(q1) == {"cash_mgmt", "bonds"} and q2 == []
        decs = answers["strategy_decisions"]
        assert decs["cash_mgmt"]["status"] == "considering"
        assert decs["bonds"]["status"] == "declined"           # queue-only: untouched
        assert decs["bonds"]["note"] == "duration doctrine"
        assert decs["bonds"]["target_pct"] == 0
        # but the proposal IS on the trail, and only once
        goal_origins = [o for o in decs["bonds"]["origins"] if o["source"] == "goal"]
        assert len(goal_origins) == 1

    def test_trail_renders_goal_label_and_schema_accepts(self, tmp_path):
        from officekit.render_strategies import render_strategies
        from officekit.schema import validate
        from officekit.serve import build_office
        from officekit.goal_mandates import goal_strategy_menu, proposal_for, queue_goal_proposals
        from officekit.model import build_model
        answers = {"as_of": "2026-09-04",
                   "sleeves": [{"category": "cash", "value": 1_000_000}],
                   "goals": [{"kind": "spending", "label": "College", "amount": 300000,
                              "date": "2031-09-01"}]}
        data = build_office(answers, tmp_path)          # offers the menu; no PROPOSAL auto-queues
        # held allocations DO auto-register as implemented (the asset is the
        # strategy — cash here becomes cash_mgmt), but the goal's proposed primary
        # (bonds) is never auto-queued and no 'considering' proposal appears.
        decs0 = data.get("strategy_decisions") or {}
        assert "bonds" not in decs0
        assert all(dec.get("status") != "considering" for dec in decs0.values())
        m = build_model(data)
        gid = data["goals"][0]["id"]
        menu = goal_strategy_menu(m)[gid]
        assert menu["options"][0]["sid"] == "bonds"     # primary offer (no tax state)
        queue_goal_proposals(answers, [proposal_for(m, None, gid, "bonds")])
        data = build_office(answers, tmp_path)
        assert validate(data) == []
        dec = data["strategy_decisions"]["bonds"]
        assert dec["origins"][0] == {"source": "goal", "ref": gid, "date": dec["origins"][0]["date"]}
        from officekit.model import build_model
        html = render_strategies(build_model(data))
        assert "mandated by your goal: College — queued, human adopts" in html
        # a second build is a no-op on the trail (adoption is idempotent per goal)
        data2 = build_office(answers, tmp_path)
        assert len(data2["strategy_decisions"]["bonds"]["origins"]) == 1
        # and the taxonomy renders the menu with the adopted primary
        from officekit.goal_mandates import goal_strategy_menu as gsm
        html2 = render_strategies(build_model(data2), goal_menu=gsm(build_model(data2)),
                                  goal_adopt_endpoint="/strategy/goal-adopt")
        assert "Your goal plan" in html2 and "Adopt" in html2


# ------------------------------------------------- goal<->strategy coverage (derived)

class TestGoalCoverage:
    """The association, made legible both directions — derived from origin
    edges at read time, never stored. Live goals only; claims aggregate."""

    def _built(self, tmp_path):
        from officekit.goal_mandates import goal_strategy_menu, proposal_for, queue_goal_proposals
        from officekit.model import build_model
        from officekit.serve import build_office
        answers = {"as_of": "2026-09-04",
                   "sleeves": [{"category": "cash", "value": 1_000_000}],
                   "goals": [
                       {"kind": "retirement", "label": "Retirement", "date": "2050-01-01",
                        "annual_spending": 100000},
                       {"kind": "spending", "label": "Second home", "amount": 350000,
                        "date": "2040-01-01"},
                       {"kind": "spending", "label": "College", "amount": 300000,
                        "date": "2040-06-01"}]}
        data = build_office(answers, tmp_path)
        m = build_model(data)
        for gid, entry in goal_strategy_menu(m).items():   # user adopts the PRIMARY
            queue_goal_proposals(answers, [proposal_for(m, None, gid, entry["options"][0]["sid"])])
        return build_office(answers, tmp_path), answers

    def test_claims_aggregate_and_both_directions(self, tmp_path):
        from officekit.goal_mandates import goal_coverage
        from officekit.model import build_model
        data, _ = self._built(tmp_path)      # all three decompose to core_equity (7y+)
        cov = goal_coverage(build_model(data))
        ce = cov["by_strategy"]["core_equity"]
        assert ce["n_goals"] == 3
        assert sorted(ce["labels"]) == ["College", "Retirement", "Second home"]
        # claims SUM (350k + 300k; retirement carries no sized claim) — not first-wins
        assert ce["mandated_pct"] == 65.0
        for g in data["goals"]:
            if g.get("implicit"):
                continue  # fixed commitments are reserved before strategy goals
            assert [e["sid"] for e in cov["by_goal"][g["id"]]] == ["core_equity"]

    def test_deleted_goal_drops_from_coverage_but_stays_on_trail(self, tmp_path):
        from officekit.goal_mandates import goal_coverage
        from officekit.model import build_model
        from officekit.serve import build_office
        data, answers = self._built(tmp_path)
        gone = data["goals"][1]["id"]                       # delete Second home
        answers["goals"] = [g for g in answers["goals"] if g.get("id") != gone]
        data2 = build_office(answers, tmp_path)
        cov = goal_coverage(build_model(data2))
        ce = cov["by_strategy"]["core_equity"]
        assert ce["n_goals"] == 2 and ce["mandated_pct"] == 30.0   # live goals only
        # the trail keeps the history
        origins = data2["strategy_decisions"]["core_equity"]["origins"]
        assert any(o["ref"] == gone for o in origins)

    def test_office_served_by_and_strategy_serving_lines(self, tmp_path):
        from officekit.model import build_model
        from officekit.render_office import render_office
        from officekit.render_strategies import render_strategies
        data, _ = self._built(tmp_path)
        m = build_model(data)
        office = render_office(m)
        assert office.count("→ served by Core public equity") == 3
        strat = render_strategies(m)
        assert "Serving goals" in strat
        assert "goal-mandated ≈ <b>65%</b> of NW" in strat

    def test_unserved_goal_says_so(self):
        from officekit.model import build_model
        from officekit.render_office import render_office
        data = {"as_of": "2026-09-04", "factors": ["S&P 500"], "profile": {},
                "sleeves": [{"name": "Cash", "kind": "asset", "category": "cash",
                             "value": 1000, "beta": {}}],
                "goals": [{"id": "a11e0f5e-9e1c-4f6d-8c2a-000000000009",
                           "kind": "liquidity_floor", "label": "Floor", "amount": 500}]}
        assert "no strategy serving this goal yet" in render_office(build_model(data))
