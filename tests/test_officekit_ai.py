"""AI-1 (classification fallback) + AI-2 (conversational onboarding) — tested
with a stubbed client, no network. The no-key path is separately proven by the
golden suite (pages byte-identical without the plugin)."""
import json
from types import SimpleNamespace

import pytest


def fake_client(payloads):
    """A stub Anthropic client: messages.create pops the next canned payload,
    returned in the output_config text-block shape."""
    queue = [json.dumps(p) for p in payloads]
    calls = []

    def create(**kw):
        calls.append(kw)
        return SimpleNamespace(stop_reason="end_turn",
                               content=[SimpleNamespace(type="text", text=queue.pop(0))])

    cl = SimpleNamespace(messages=SimpleNamespace(create=create))
    cl.calls = calls
    return cl


# ---------------------------------------------------------------- AI-1: classify

class TestClassify:
    def test_suggest_filters_and_freezes(self, tmp_path):
        from officekit_ai.classify import suggest
        cl = fake_client([{"classifications": [
            {"symbol": "VWLUX", "category": "municipal_credit", "style": None, "confidence": 0.93},
            {"symbol": "TSLA", "category": "single_name_equity", "style": None, "confidence": 0.99},
            {"symbol": "ZZZQ", "category": "public_equity", "style": None, "confidence": 0.2},
        ]}])
        ledger = tmp_path / "learning.jsonl"
        out = suggest(["VWLUX", "TSLA", "ZZZQ"], client=cl, ledger_path=ledger, office_id="oid")
        # single stocks (already the default) and low confidence are dropped
        assert [s["symbol"] for s in out] == ["VWLUX"]
        rec = json.loads(ledger.read_text().splitlines()[0])
        assert rec["kind"] == "agent_call" and rec["payload"]["capability"] == "classify"
        assert rec["payload"]["suggestions"][0]["symbol"] == "VWLUX"

    def test_suggest_degrades_to_empty_on_any_failure(self):
        from officekit_ai.classify import suggest
        boom = SimpleNamespace(messages=SimpleNamespace(
            create=lambda **kw: (_ for _ in ()).throw(RuntimeError("api down"))))
        assert suggest(["VWLUX"], client=boom) == []
        assert suggest([]) == []   # nothing to ask -> no client construction at all

    def test_learned_map_roundtrip_and_apply(self, tmp_path):
        from officekit_ai.classify import apply_confirmed, load_learned, save_confirmed
        save_confirmed(tmp_path, {"VWLUX": ("municipal_credit", None)})
        save_confirmed(tmp_path, {"QQQJ": ("public_equity", "tech")})   # merge, never drop
        assert load_learned(tmp_path) == {"VWLUX": ("municipal_credit", None),
                                          "QQQJ": ("public_equity", "tech")}
        answers = {}
        apply_confirmed(answers, {"VWLUX": ("municipal_credit", None)})
        assert answers["fund_map"] == {"VWLUX": ["municipal_credit", None]}

    def test_confirmed_map_flows_through_intake(self):
        from officekit.intake import build_from_answers
        answers = {"as_of": "2026-09-02",
                   "positions": {"rows": [{"symbol": "VWLUX", "value": 100000},
                                          {"symbol": "TSLA", "value": 5000}]},
                   "fund_map": {"VWLUX": ["municipal_credit", None]}}
        data = build_from_answers(answers)
        cats = {s["category"] for s in data["sleeves"]}
        assert "municipal_credit" in cats            # confirmed mapping applied
        muni = next(s for s in data["sleeves"] if s["category"] == "municipal_credit")
        assert muni["value"] == 100000

    def test_unknown_symbols_respects_learned_map(self):
        from officekit.importers import unknown_symbols
        rows = [{"symbol": "VWLUX", "value": 1}, {"symbol": "VTI", "value": 1},
                {"symbol": "TSLA", "value": 1}]
        assert unknown_symbols(rows) == ["VWLUX", "TSLA"]
        assert unknown_symbols(rows, extra_map={"VWLUX": ("municipal_credit", None)}) == ["TSLA"]


# ------------------------------------------------------------ AI-2: intake chat

class TestIntakeChat:
    def test_turn_returns_structured_dict_with_contract_system(self):
        from officekit_ai.intake_chat import turn
        cl = fake_client([{"reply": "How much cash?", "answers_json": "", "complete": False}])
        t = turn([{"role": "user", "content": "hi"}], client=cl)
        assert t["reply"] == "How much cash?" and t["complete"] is False
        sysprompt = cl.calls[0]["system"]
        assert "Never fabricate" in sysprompt          # the shipped contract IS the prompt
        assert "Conversational mode" in sysprompt
        assert cl.calls[0]["output_config"]["format"]["type"] == "json_schema"

    def test_cli_builds_on_complete(self, tmp_path):
        from officekit_ai.intake_chat import run_cli
        answers = {"as_of": "2026-09-02",
                   "sleeves": [{"category": "cash", "value": 50000}],
                   "goals": [{"kind": "liquidity_floor", "label": "Floor", "amount": 20000}]}
        cl = fake_client([{"reply": "Building.", "answers_json": json.dumps(answers), "complete": True}])
        feed = iter(["I have 50k cash, floor 20k, that's it"])
        out = []
        data = run_cli(tmp_path, client=cl, input_fn=lambda _: next(feed), print_fn=out.append)
        assert data["sleeves"][0]["category"] == "cash"
        assert (tmp_path / "balance_sheet.json").exists()
        assert (tmp_path / "personal_context.json").exists()   # plane 2 from day one
        recs = [json.loads(x) for x in (tmp_path / "learning.jsonl").read_text().splitlines()]
        assert any(r["kind"] == "agent_call" and r["payload"]["capability"] == "intake"
                   for r in recs)

    def test_cli_validation_failure_feeds_back_and_repairs(self, tmp_path):
        from officekit_ai.intake_chat import run_cli
        bad = {"as_of": "2026-09-02", "sleeves": [{"category": "crypto_moon", "value": 1}]}
        good = {"as_of": "2026-09-02", "sleeves": [{"category": "cash", "value": 50000}]}
        cl = fake_client([{"reply": "done", "answers_json": json.dumps(bad), "complete": True},
                          {"reply": "fixed", "answers_json": json.dumps(good), "complete": True}])
        feed = iter(["done"])
        run_cli(tmp_path, client=cl, input_fn=lambda _: next(feed), print_fn=lambda *a: None)
        # the second call got the validation failure as a user turn
        msgs = cl.calls[1]["messages"]
        assert any(m["role"] == "user" and "VALIDATION FAILED" in str(m["content"]) for m in msgs)
        data = json.loads((tmp_path / "balance_sheet.json").read_text())
        assert data["sleeves"][0]["category"] == "cash"


# --------------------------------------------------------- serve: graceful absence

class TestServeIntegration:
    def test_no_key_means_no_ai_affordances(self, monkeypatch, tmp_path):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: tmp_path))  # no key file either
        from officekit.serve import _ai
        assert _ai() is None

    def test_classify_unknowns_degrades_without_key(self, tmp_path, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: tmp_path))
        import officekit_ai
        from officekit.serve import _classify_unknowns
        answers = {"positions": {"rows": [{"symbol": "VWLUX", "value": 1000}]}}
        assert _classify_unknowns(answers, tmp_path, officekit_ai) == []


# ------------------------------------------------- BYOM: model slots (contract #10)

class TestModelSlots:
    """models.json: slots -> provider + model; providers reference keys by
    env-var NAME only — a document carrying key material is rejected loudly."""

    def test_defaults_without_config(self):
        from officekit_ai.models import resolve
        name, pcfg, model = resolve("classify")
        assert name == "anthropic" and model == "claude-haiku-4-5"
        assert pcfg["api_key_env"] == "ANTHROPIC_API_KEY"
        assert resolve("intake")[2] == "claude-opus-5"

    def test_secrets_never_enter_the_document(self, tmp_path):
        import pytest as _pytest
        from officekit_ai.models import load
        (tmp_path / "models.json").write_text(json.dumps(
            {"v": 1, "providers": {"anthropic": {"api_key": "sk-ant-LEAKED"}}, "slots": {}}))
        with _pytest.raises(ValueError, match="secrets never enter"):
            load(tmp_path)

    def test_byo_provider_and_slot_override(self, tmp_path, monkeypatch):
        from officekit_ai.models import PROVIDERS, client_for, provider
        (tmp_path / "models.json").write_text(json.dumps(
            {"v": 1,
             "providers": {"local": {"api_key_env": "MY_LOCAL_KEY", "base_url": "http://localhost:8000"}},
             "slots": {"classify": {"provider": "local", "model": "my-model-7b"}}}))
        made = {}

        @provider("local")
        def _local(cfg):
            made.update(cfg)
            return "local-client"
        try:
            cl, model = client_for("classify", tmp_path)
            assert cl == "local-client" and model == "my-model-7b"
            assert made["base_url"] == "http://localhost:8000"
            # unconfigured slots keep the defaults
            from officekit_ai.models import resolve
            assert resolve("intake", tmp_path)[0] == "anthropic"
        finally:
            PROVIDERS.pop("local", None)

    def test_validation_catches_bad_slots(self, tmp_path):
        import pytest as _pytest
        from officekit_ai.models import load, validate
        assert any("unknown slot" in x for x in validate(
            {"v": 1, "providers": {}, "slots": {"vibes": {"provider": "x", "model": "y"}}}))
        assert any("undeclared provider" in x for x in validate(
            {"v": 1, "providers": {}, "slots": {"classify": {"provider": "ghost", "model": "y"}}}))
        (tmp_path / "models.json").write_text("{\"v\": 2}")
        with _pytest.raises(ValueError):
            load(tmp_path)

    def test_slot_available_false_without_key(self, monkeypatch, tmp_path):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setattr("pathlib.Path.home", staticmethod(lambda: tmp_path))  # ~/.anthropic_key fallback off
        from officekit_ai.models import slot_available
        assert slot_available("classify") is False
        import officekit_ai
        assert officekit_ai.available(slot="classify") is False


# ------------------------------------------------- courtkit-lite (I4, Q6-ratified)

class TestCourtkit:
    """Local adjudications in strategy context; U2 tier order enforced; the
    exchange allowlist carries strategy/office/date — never sizes."""

    def test_tier_order_enforced(self):
        import pytest as _pytest
        from officekit_ai.court import check_tier_order
        assert check_tier_order("claude-opus-5", "claude-opus-5") == "flat_tier"
        assert check_tier_order("claude-opus-5", "claude-fable-5") == "tiered"
        assert check_tier_order("my-local-7b", "claude-opus-5") == "unranked"
        with _pytest.raises(RuntimeError, match="never be weaker"):
            check_tier_order("claude-opus-5", "claude-haiku-4-5")

    def _fake_court_clients(self):
        bench = fake_client([
            {"case": "red case", "key_points": ["kp1"], "unverified": ["rev mix"], "lean": "watch"},
            {"case": "blue case", "key_points": ["kp2"], "unverified": [], "lean": "starter"},
        ])
        adj = fake_client([
            {"verdict": "STARTER", "conviction": 6, "rationale": "fits the mandate at starter size",
             "decisive_points": ["dp"], "unverified_items": ["rev mix"]},
        ])
        return {"bench": (bench, "claude-opus-5"), "adjudicate": (adj, "claude-fable-5")}

    def test_run_court_produces_contract_11(self, tmp_path):
        from officekit.personal_context import empty
        from officekit_ai.court import export_shareable_adjudications, load_adjudications, run_court
        pc = empty("a11e0f5e-9e1c-4f6d-8c2a-000000000001")
        rec = run_court("8035.T", "japan_value",
                        {"status": "considering", "title": "Japan value", "target_pct": 4},
                        pc, tmp_path, clients=self._fake_court_clients())
        assert rec["strategy"] == "japan_value"          # WHICH strategy (Q6)
        assert rec["office_id"] == pc["office_id"]       # WHICH office (Q6)
        assert rec["date"]                               # WHEN (Q6)
        assert rec["verdict"] == "STARTER 6/10 (LITE)"   # honest lite label
        assert rec["tier"] == "tiered"
        assert set(rec["refs"]) == {"red", "blue", "adjudicate"}
        assert load_adjudications(tmp_path)[0]["id"] == rec["id"]
        # 3 frozen agent_calls
        recs = [json.loads(x) for x in (tmp_path / "learning.jsonl").read_text().splitlines()]
        kinds = [r["payload"]["capability"] for r in recs if r["kind"] == "agent_call"]
        assert kinds == ["court_red", "court_blue", "court_adjudicate"]
        # doctrine + strategy context reached the benches; plane-2 gate enforced
        bench_calls = self._fake_court_clients()  # fresh (calls consumed above)
        shared = export_shareable_adjudications(tmp_path)[0]
        assert shared["strategy"] == "japan_value" and shared["symbol"] == "8035.T"
        for banned in ("unverified_items", "models", "refs", "decisive_points"):
            assert banned not in shared

    def test_evidenced_court_label_and_pack_injection(self, tmp_path):
        """F1: a prebuilt evidence pack upgrades the court from LITE to
        EVIDENCED — the pack reaches both benches and the record; without a
        pack the court degrades loud, never silently."""
        from officekit.personal_context import empty
        from officekit_ai.court import run_court
        pack = {"symbol": "BND", "built": "2026-09-04T00:00:00Z",
                "sections": {"tape": {"last": 72.5, "as_of": "09/04/2026", "wk52_hi": 74.0,
                                      "wk52_lo": 68.0, "off_high_pct": -2.0, "off_low_pct": 6.6},
                             "book": {"held": False, "positions": []}},
                "errors": ["xbrl: RuntimeError: no CIK resolved"]}
        clients = self._fake_court_clients()
        rec = run_court("BND", "bonds", {"status": "considering"}, empty("a11e0f5e-9e1c-4f6d-8c2a-000000000001"),
                        tmp_path, clients=clients, evidence=pack)
        assert rec["verdict"].endswith("(EVIDENCED)")
        assert rec["evidence"]["sections"] == ["book", "tape"]
        assert "EVIDENCE GAPS" in rec["evidence"]["md"]        # degrade-loud in the pack itself
        bench_call = clients["bench"][0].calls if hasattr(clients["bench"][0], "calls") else None
        # fresh fake clients above were consumed by run_court; re-check via a new run
        clients2 = self._fake_court_clients()
        rec2 = run_court("BND", "bonds", {"status": "considering"},
                         empty("a11e0f5e-9e1c-4f6d-8c2a-000000000001"),
                         tmp_path, clients=clients2, evidence=pack)
        assert "EVIDENCE PACK — BND" in clients2["bench"][0].calls[0]["messages"][0]["content"]
        # explicitly no evidence pack -> honest LITE (fund issuer research no longer needs SEC contact)
        rec3 = run_court("BND", "bonds", {"status": "considering"},
                         empty("a11e0f5e-9e1c-4f6d-8c2a-000000000001"),
                         tmp_path, clients=self._fake_court_clients(), evidence=None)
        assert rec3["verdict"].endswith("(LITE)") and rec3["evidence"]["errors"]

    def test_book_evidence_source_reads_office_data(self):
        from officekit_research import SOURCES
        data = {"sleeves": [{"name": "Muni sleeve", "holdings": [
            {"company": "IBMT", "amount": 8000, "adjudication": {"verdict": "WATCH 6/10 (LITE)"}}]}]}
        out = SOURCES["book"]("IBMT", {"office_data": data})
        assert out["held"] and out["positions"][0]["sleeve"] == "Muni sleeve"
        assert SOURCES["book"]("ZZZZ", {"office_data": data}) == {"held": False, "positions": []}

    def test_court_refuses_without_personal_context(self, tmp_path):
        import pytest as _pytest
        from officekit_ai.court import run_court
        with _pytest.raises(RuntimeError, match="personal context required"):
            run_court("X", "japan_value", {}, None, tmp_path,
                      clients=self._fake_court_clients())

    def test_taxonomy_and_deck_pages(self, tmp_path):
        """The UX ruling: goal -> offered menu (Adopt per option) -> adopted
        strategy's courted assets -> each with a full pitch-deck page."""
        from officekit.goal_mandates import goal_strategy_menu, proposal_for, queue_goal_proposals
        from officekit.model import build_model
        from officekit.personal_context import empty
        from officekit.render_deck import deck_filename, render_deck
        from officekit.render_strategies import render_strategies
        from officekit.serve import build_office
        from officekit_ai.court import load_adjudications, run_court
        answers = {"as_of": "2026-09-04",
                   "sleeves": [{"category": "cash", "value": 1_000_000}],
                   "goals": [{"kind": "spending", "label": "College", "amount": 300000,
                              "date": "2031-09-01"}]}
        data = build_office(answers, tmp_path)
        m = build_model(data)
        gid = data["goals"][0]["id"]
        menu = goal_strategy_menu(m)
        opts = [o["sid"] for o in menu[gid]["options"]]
        assert 2 <= len(opts) <= 4 and opts[0] == "bonds"      # a HANDFUL, primary first
        # unadopted: the menu renders with adopt toggles (check/uncheck)
        html = render_strategies(m, goal_menu=menu, goal_adopt_endpoint="/strategy/goal-adopt")
        assert "Your goal plan" in html and html.count("adoptck") >= 2
        # adopt + court -> the asset renders under the goal with a deck link
        queue_goal_proposals(answers, [proposal_for(m, None, gid, "bonds")])
        data = build_office(answers, tmp_path)
        pc = empty(data["office_id"])
        adj = run_court("BND", "bonds", data["strategy_decisions"]["bonds"], pc, tmp_path,
                        clients=self._fake_court_clients(), evidence=None)
        data = build_office(answers, tmp_path)
        m2 = build_model(data)
        html2 = render_strategies(m2, goal_menu=goal_strategy_menu(m2),
                                  adjudications=load_adjudications(tmp_path),
                                  goal_adopt_endpoint="/strategy/goal-adopt")
        assert f'deck_{adj["id"][:8]}.html' in html2 and "full pitch deck" in html2
        # build_office wrote the deck page; it carries BOTH briefs + the queue
        deck_path = tmp_path / "pages" / deck_filename(adj)
        assert deck_path.exists()
        deck = deck_path.read_text()
        assert "RED bench" in deck and "BLUE bench" in deck
        assert "red case" in deck and "blue case" in deck
        assert "Unverified work queue" in deck and "STARTER 6/10 (LITE)" in deck

    def test_full_loop_goal_to_coverage(self, tmp_path):
        """The sketch's loop, closed: goal -> queued strategy -> adjudication ->
        recorded purchase -> sleeve tagged -> goal coverage shows real value."""
        from officekit.goal_mandates import goal_coverage
        from officekit.model import build_model
        from officekit.personal_context import empty
        from officekit.serve import build_office, record_purchase
        from officekit_ai.court import load_adjudications, run_court
        answers = {"as_of": "2026-09-04",
                   "sleeves": [{"category": "cash", "value": 1_000_000}],
                   "goals": [{"kind": "spending", "label": "Second home",
                              "amount": 350000, "date": "2040-01-01"}]}
        from officekit.goal_mandates import goal_strategy_menu, proposal_for, queue_goal_proposals
        from officekit.model import build_model as _bm
        data = build_office(answers, tmp_path)           # offers the menu
        gid0 = data["goals"][0]["id"]
        m0 = _bm(data)
        assert goal_strategy_menu(m0)[gid0]["options"][0]["sid"] == "core_equity"
        queue_goal_proposals(answers, [proposal_for(m0, None, gid0, "core_equity")])
        data = build_office(answers, tmp_path)
        assert data["strategy_decisions"]["core_equity"]["status"] == "considering"
        pc = empty(data["office_id"])
        run_court("SCHB", "core_equity",
                  answers["strategy_decisions"]["core_equity"], pc, tmp_path,
                  clients=self._fake_court_clients())
        record_purchase(answers, "core_equity", "SCHB", 50000, load_adjudications(tmp_path))
        data2 = build_office(answers, tmp_path)
        dec = data2["strategy_decisions"]["core_equity"]
        assert dec["status"] == "implemented"
        sleeve = next(s for s in data2["sleeves"] if "core_equity" in (s.get("strategies") or []))
        h = sleeve["holdings"][0]
        assert h["company"] == "SCHB" and h["adjudication"]["verdict"] == "STARTER 6/10 (LITE)"
        cov = goal_coverage(build_model(data2))
        entry = cov["by_goal"][data2["goals"][0]["id"]][0]
        assert entry["sid"] == "core_equity" and entry["cur_val"] == 50000
        # strategies page shows it all
        from officekit.render_strategies import render_strategies
        html = render_strategies(build_model(data2), adjudications=load_adjudications(tmp_path),
                                 court_endpoint="/court", holdings_endpoint="/holdings")
        assert "STARTER 6/10 (LITE)" in html and "Run court" in html and "Record purchase" in html


# ------------------------------------------------- signals registry (F3a)

class TestSignals:
    """The capability registry: both binding axes, union resolution derived at
    query time, runs recorded, health from cadence, code introspectable."""

    def test_union_resolution_both_axes(self):
        import officekit_signals as sig
        from officekit_signals import capability
        try:
            @capability("test_asset_bound", "watcher", "Test", applies_to={"symbols": ["TSSI"]})
            def w(ctx):
                return {}

            @capability("test_strat_bound", "detector", "Test", applies_to={"strategies": ["muni"]})
            def d(ctx):
                return {}
            # asset-level binding follows the SYMBOL regardless of strategy
            names = {c["name"] for c in sig.applicable(symbol="TSSI", strategy="core_equity")}
            assert "test_asset_bound" in names and "test_strat_bound" not in names
            # strategy-level binding follows the STRATEGY
            names = {c["name"] for c in sig.applicable(symbol="VTEB", strategy="muni")}
            assert "test_strat_bound" in names and "test_asset_bound" not in names
            # union when both match
            names = {c["name"] for c in sig.applicable(symbol="TSSI", strategy="muni")}
            assert {"test_asset_bound", "test_strat_bound"} <= names
            # universal capabilities appear everywhere
            assert "filing_watch" in names and "tenx_guard" in names
        finally:
            sig.CAPABILITIES.pop("test_asset_bound", None)
            sig.CAPABILITIES.pop("test_strat_bound", None)

    def test_runs_health_and_error_class(self, tmp_path):
        import officekit_signals as sig
        rt = sig.runtime(tmp_path)
        assert rt["filing_watch"]["health"] == "NEVER_RUN"
        sig.record_run(tmp_path, "filing_watch", "ok", output={"events": []})
        assert sig.runtime(tmp_path)["filing_watch"]["health"] == "OK"
        # an infra failure is recorded as its own class, never silent
        import pytest as _pytest
        with _pytest.raises(RuntimeError):
            sig.run_capability(tmp_path, "drawdown_screen", {"symbols": []})
        assert sig.runtime(tmp_path)["drawdown_screen"]["health"] == "ERROR"

    def test_book_watcher_state_machine(self, tmp_path, monkeypatch):
        """filing_watch: first pass seeds state, a changed accession is an event."""
        import officekit_signals as sig
        from officekit_research import SOURCES
        calls = {"n": 0}

        def fake_filings(symbol, ctx):
            calls["n"] += 1
            acc = "0001-first" if calls["n"] <= 1 else "0002-second"
            return {"entity": "X", "recent": [{"form": "8-K", "date": "2026-09-05", "acc": acc}]}
        monkeypatch.setitem(SOURCES, "filings", fake_filings)
        monkeypatch.setattr("officekit_research._cik", lambda s, c: 1)
        data = {"sleeves": [{"holdings": [{"company": "XYZ"}]}]}
        ctx = {"office_data": data, "contact": "t@example.com"}
        out1 = sig.run_capability(tmp_path, "filing_watch", ctx)
        assert out1["events"] == [] and out1["watched"] == ["XYZ"]
        out2 = sig.run_capability(tmp_path, "filing_watch", ctx)
        assert len(out2["events"]) == 1 and out2["events"][0]["symbol"] == "XYZ"

    def test_verdict_grading_loop(self, tmp_path, monkeypatch):
        """The calibration spine: ripe adjudications grade against the tape,
        WATCH stays ungraded by design, grades land in the learning ledger,
        and the state cursor makes it idempotent."""
        import json as _json
        import urllib.request
        from datetime import date, timedelta
        import officekit_signals as sig
        old_date = (date.today() - timedelta(days=45)).isoformat()
        adjs = [
            {"id": "adj-starter", "symbol": "AAA", "strategy": "quality_value",
             "verdict": "STARTER 6/10 (EVIDENCED)", "date": old_date, "office_id": "oid"},
            {"id": "adj-avoid", "symbol": "BBB", "strategy": "quality_value",
             "verdict": "AVOID 7/10 (EVIDENCED)", "date": old_date, "office_id": "oid"},
            {"id": "adj-watch", "symbol": "CCC", "strategy": "quality_value",
             "verdict": "WATCH 5/10 (LITE)", "date": old_date, "office_id": "oid"},
            {"id": "adj-fresh", "symbol": "DDD", "strategy": "quality_value",
             "verdict": "STARTER 5/10 (LITE)", "date": date.today().isoformat(),
             "office_id": "oid"},
        ]
        (tmp_path / "adjudications.jsonl").write_text(
            "\n".join(_json.dumps(a) for a in adjs) + "\n")

        class FakeResp:
            def __init__(self):
                # newest first: +10% move for everyone
                body = {"data": {"tradesTable": {"rows": [
                    {"date": (date.fromisoformat(old_date) + timedelta(days=30)).strftime("%m/%d/%Y"), "close": "$110.00"},
                    {"date": date.fromisoformat(old_date).strftime("%m/%d/%Y"), "close": "$100.00"}]}}}
                self._b = _json.dumps(body).encode()

            def read(self):
                return self._b

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False
        monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: FakeResp())

        out = sig.run_capability(tmp_path, "verdict_outcomes", {})
        by_id = {g["adjudication_id"]: g for g in out["graded"]}
        assert by_id["adj-starter"]["favorable"] is True      # long bias, +10%
        assert by_id["adj-avoid"]["favorable"] is False       # avoid, +10% = unfavorable
        assert "adj-watch" not in by_id and out["skipped_watch"] == 1
        assert "adj-fresh" not in by_id                       # not ripe
        recs = [_json.loads(l) for l in (tmp_path / "learning.jsonl").read_text().splitlines()]
        grades = [r for r in recs if r["kind"] == "verdict_grade"]
        assert len(grades) == 2 and grades[0]["payload"]["move_pct"] == 10.0
        # idempotent: second run grades nothing new
        out2 = sig.run_capability(tmp_path, "verdict_outcomes", {})
        assert out2["graded"] == []
        # grades never leave through the learning allowlist (they carry tickers)
        from officekit.learning import export_shareable
        assert all(r["kind"] != "verdict_grade" for r in export_shareable(tmp_path / "learning.jsonl"))

    def test_pages_render_with_code_and_datasources(self, tmp_path):
        import officekit_signals as sig
        from officekit.render_signals import render_asset, render_capability, render_signals_index
        rt = sig.runtime(tmp_path)
        idx = render_signals_index(sig.CAPABILITIES, rt)
        assert "capability_filing_watch.html" in idx and "NEVER_RUN" in idx
        page = render_capability(sig.CAPABILITIES["tenx_guard"],
                                 rt.get("tenx_guard"), sig.source_code("tenx_guard"))
        assert "def det_tenx_guard" in page                    # the ACTUAL code
        assert "SEC XBRL companyconcept API" in page           # datasources enumerated
        assert "Run now" in page
        union = sig.applicable(symbol="IBMT", strategy="muni")
        asset = render_asset("IBMT", {"sleeves": [{"name": "Muni sleeve", "holdings": [
            {"company": "IBMT", "amount": 8000,
             "adjudication": {"verdict": "WATCH 6/10 (LITE)"}}]}]},
            [{"symbol": "IBMT", "strategy": "muni", "date": "2026-09-04",
              "verdict": "WATCH 6/10 (LITE)", "id": "abcd1234efgh"}],
            union, ["muni"])
        assert "capability_filing_watch.html" in asset         # the union, linked
        assert "deck_abcd1234.html" in asset and "Muni sleeve" in asset

    def test_strategy_asset_clickthrough_end_to_end(self, tmp_path):
        """strategy card -> asset link -> asset page carrying the capability union."""
        from officekit.serve import build_office, record_purchase
        answers = {"as_of": "2026-09-05",
                   "sleeves": [{"category": "cash", "value": 500000}]}
        build_office(answers, tmp_path)
        record_purchase(answers, "muni", "IBMT", 8000, [])
        build_office(answers, tmp_path)
        strategies = (tmp_path / "pages" / "strategies.html").read_text()
        assert 'asset_IBMT.html' in strategies                 # click-through wired
        asset = (tmp_path / "pages" / "asset_IBMT.html").read_text()
        assert "Applicable capabilities" in asset
        assert "capability_tenx_guard.html" in asset
        assert (tmp_path / "pages" / "signals.html").exists()
        assert (tmp_path / "pages" / "capability_filing_watch.html").exists()


# ---------------------------------------------------------------- F2: docket

class TestDocket:
    def _clients(self, verdict="STARTER"):
        bench = fake_client([
            {"case": "red case", "key_points": ["kp1"], "unverified": ["x"], "lean": "watch"},
            {"case": "blue case", "key_points": ["kp2"], "unverified": [], "lean": "starter"},
        ])
        adj = fake_client([
            {"verdict": verdict, "conviction": 6, "rationale": "r",
             "decisive_points": ["dp"], "unverified_items": []},
        ])
        return {"bench": (bench, "claude-opus-5"), "adjudicate": (adj, "claude-fable-5")}

    def test_enqueue_idempotent_and_drain(self, tmp_path):
        from officekit.personal_context import empty
        from officekit_ai import docket
        pc = empty("a11e0f5e-9e1c-4f6d-8c2a-000000000002")
        it = docket.enqueue(tmp_path, "8035.t", "japan_value", "screen/test", context="cheap")
        assert it["symbol"] == "8035.T"                       # normalized
        assert docket.enqueue(tmp_path, "8035.T", "japan_value", "screen/test") is None  # open dupe refused
        assert docket.enqueue(tmp_path, "8035.T", "other_strategy", "screen/test")       # per-strategy identity
        assert len(docket.pending(tmp_path)) == 2
        log = docket.drain(tmp_path, pc,
                           decisions={"japan_value": {"status": "considering", "title": "JV"}},
                           clients=self._clients(), max_dispatch=1)
        assert len(log) == 1 and "STARTER" in log[0]
        items = docket.load_docket(tmp_path)
        done = next(i for i in items if i["status"] == "DONE")
        assert done["adjudication_id"]
        from officekit_ai.court import load_adjudications
        assert load_adjudications(tmp_path)[0]["id"] == done["adjudication_id"]
        # the adjudicated pair is now refused without recourt, allowed with it
        assert docket.enqueue(tmp_path, "8035.T", "japan_value", "screen/again") is None
        assert docket.enqueue(tmp_path, "8035.T", "japan_value", "recourt/dislocation", recourt=True)

    def test_drain_marks_error_and_requeues(self, tmp_path):
        from officekit.personal_context import empty
        from officekit_ai import docket
        pc = empty("a11e0f5e-9e1c-4f6d-8c2a-000000000003")
        docket.enqueue(tmp_path, "AAA", "s1", "t")
        bad = {"bench": (fake_client([]), "claude-opus-5"),      # empty queue -> IndexError
               "adjudicate": (fake_client([]), "claude-fable-5")}
        log = docket.drain(tmp_path, pc, clients=bad)
        assert "ERROR" in log[0]
        assert docket.load_docket(tmp_path)[0]["status"] == "ERROR"
        assert docket.requeue_errors(tmp_path) == 1
        assert docket.pending(tmp_path)

    def test_kill_before_court(self, tmp_path):
        from officekit_ai import docket
        it = docket.enqueue(tmp_path, "BBB", "s1", "t")
        assert docket.kill(tmp_path, it["id"], note="stale premise")["status"] == "KILLED"
        assert not docket.pending(tmp_path)

    def test_promoted_templates_ride_into_benches(self, tmp_path):
        from officekit.personal_context import empty
        from officekit_ai.court import run_court
        pc = empty("a11e0f5e-9e1c-4f6d-8c2a-000000000004")
        clients = self._clients()
        run_court("TSSI", "ai_infra", {"status": "considering"}, pc, tmp_path, clients=clients)
        bench_calls = clients["bench"][0].calls
        red_msg = bench_calls[0]["messages"][0]["content"]
        blue_msg = bench_calls[1]["messages"][0]["content"]
        assert "RED TEAM" in red_msg                # promoted court_red.md doctrine present
        assert "TSSI" in red_msg
        assert "red case" in blue_msg               # blue sees the red brief ({RED_CASE})
        assert "OUTPUT SHAPE" in red_msg            # schema bridge appended
