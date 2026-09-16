"""A synthetic second tenant: evidence -> docket -> court -> custody -> grade.

Fake model responses and recorded prices prove integration, not investment skill.
No desk files, real account data, credentials or external requests are needed.
"""
import json
from datetime import date
from types import SimpleNamespace

import pytest

from officekit import staging
from officekit.personal_context import empty
from officekit_ai.evaluation import compare, grade_direction


def client(payloads):
    def create(**kw):
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(
            type="text", text=json.dumps(payloads.pop(0)))])
    return SimpleNamespace(messages=SimpleNamespace(create=create))


def test_native_operating_cycle_survives_restart(tmp_path, monkeypatch):
    from officekit.serve import build_office, sync_office_from_staging
    from officekit_ai.docket import enqueue, drain, load_docket
    from officekit_ai.court import load_adjudications
    from officekit_research import SOURCES
    from officekit.thesis_board import from_adjudications
    from officekit_signals import run_capability

    # Stop discovery/model configuration from consulting this developer's machine.
    monkeypatch.setattr("officekit.serve._discover_cached", lambda: [])
    monkeypatch.setattr("officekit.serve._key_status", lambda _: None)
    monkeypatch.setattr("officekit.serve._ai", lambda *a, **kw: False)
    answers = {"as_of": "2026-01-01", "profile": {}, "positions": {"rows": [
        {"symbol": "AAA", "value": 1000}]}, "goals": [
        {"kind": "spending", "label": "Education", "amount": 500, "date": "2031-09-01"}],
        "strategy_decisions": {"quality_value": {"status": "considering", "title": "Quality"}}}
    build_office(answers, tmp_path)
    # One changed filing, observed through the real registry/state store.
    monkeypatch.setattr("officekit_research._cik", lambda *a: 1)
    accession = {"value": "one"}
    monkeypatch.setitem(SOURCES, "filings", lambda *a: {"recent": [
        {"form": "8-K", "date": "2026-01-02", "acc": accession["value"]}]})
    ctx = {"office_data": {"sleeves": [{"holdings": [{"company": "AAA"}]}]}, "contact": "test@example.invalid"}
    assert run_capability(tmp_path, "filing_watch", ctx)["events"] == []
    accession["value"] = "two"
    event = run_capability(tmp_path, "filing_watch", ctx)["events"][0]
    enqueue(tmp_path, "AAA", "quality_value", "filing_watch", context=json.dumps(event), recourt=True)
    clients = {"bench": (client([
        {"case": "Audit the filing", "key_points": [], "unverified": ["unit margins"], "lean": "watch"},
        {"case": "Dated catalyst", "key_points": [], "unverified": [], "lean": "starter"},
    ]), "claude-opus-5"), "adjudicate": (client([
        {"verdict": "STARTER", "conviction": 6, "rationale": "Synthetic fixture decision",
         "decisive_points": [], "unverified_items": []},
    ]), "claude-fable-5")}
    drain(tmp_path, empty(), answers["strategy_decisions"], clients=clients,
          today=date(2026, 1, 2), max_dispatch=1)
    assert load_docket(tmp_path)[0]["status"] == "DONE"
    adj = load_adjudications(tmp_path)[0]
    assert adj["unverified_items"] == ["unit margins"]  # union is enforced, not merely prompted

    # Implementation is imported as actual custody, never synthesized from a verdict.
    staging.record_pull(tmp_path, "broker", "adapter", "Synthetic broker", [
        {"symbol": "AAA", "account": "A", "sec_type": "STK", "value": 1050},
        {"symbol": "USD", "account": "A", "sec_type": "CASH", "value": 450}], "auto",
        as_of="2026-01-03", snapshot={"mode": "complete", "accounts": ["A"],
            "security_types": ["STK", "CASH"], "totals": {"A": 1500}})
    sync_office_from_staging(tmp_path)
    # Re-read all state after a simulated restart; no in-memory objects are needed.
    saved = json.loads((tmp_path / "answers.json").read_text())
    build_office(saved, tmp_path)
    assert from_adjudications(tmp_path)[0]["value"] == 1050
    assert (tmp_path / "pages" / f"deck_{adj['id'][:8]}.html").exists()
    prices = lambda *a: [("2026-01-01", 50), ("2026-01-02", 100),
                        ("2026-02-01", 110), ("2026-03-01", 200)]
    grade_ctx = {"today": "2026-03-02", "price_history": prices}
    grade = run_capability(tmp_path, "verdict_outcomes", grade_ctx)["graded"][0]
    assert grade["move_pct"] == 10 and grade["exit_date"] == "2026-02-01"
    assert run_capability(tmp_path, "verdict_outcomes", grade_ctx)["graded"] == []
    from officekit_signals import load_state, save_state
    state = load_state(tmp_path)
    state.pop("verdict_outcomes")  # simulate a lost cursor after successful append
    save_state(tmp_path, state)
    assert run_capability(tmp_path, "verdict_outcomes", grade_ctx)["graded"] == []


def test_grade_rejects_preverdict_only_or_missing_horizon():
    adj = {"id": "x", "symbol": "AAA", "date": "2026-01-02", "verdict": "OWN"}
    with pytest.raises(ValueError, match="missing close"):
        grade_direction(adj, [("2026-01-01", 100), ("2026-02-01", 110)], today=date(2026, 3, 1))


def paired_case():
    def call(p):
        return {"p": p, "action": "accept", "evidence_hash": "frozen-fixture",
                "frozen_at": "2026-01-01T00:00:00+00:00", "cost_usd": 1,
                "latency_s": 10, "audited_claims": 5, "unsupported_claims": 1}
    return {"id": "synthetic", "event": "Synthetic event by February 1", "outcome": True,
            "evidence_hash": "frozen-fixture", "resolved_at": "2026-02-01T00:00:00+00:00",
            "audit_ref": "fixture, not a real accuracy study", "analyst": call(.6), "court": call(.8)}


def test_paired_evaluation_has_equal_denominators_and_no_lookahead():
    case = paired_case()
    out = compare([case, {"id": "unresolved", "outcome": None}])
    assert out["n_pairs"] == 1 and out["excluded_unresolved"] == ["unresolved"]
    assert out["methods"]["analyst"]["brier"] == .16
    assert out["methods"]["court"]["brier"] == .04
    case["court"]["frozen_at"] = case["resolved_at"]
    with pytest.raises(ValueError, match="before outcome"):
        compare([case])
    case = paired_case()
    case["court"]["evidence_hash"] = "different-inputs"
    with pytest.raises(ValueError, match="same frozen evidence"):
        compare([case])


def test_risk_uses_only_this_tenants_exclusions():
    from officekit import build_model
    from officekit.intake import build_from_answers
    from officekit.risk_officer import review
    model = build_model(build_from_answers({"profile": {}, "sleeves": [
        {"category": "public_equity", "value": 1000, "holdings": [{"company": "IBM", "amount": 500},
            {"company": "XYZ", "amount": 500}]}]}))
    assert not any("exclusion" in f["title"].lower() for f in review(model, personal_context=empty()))
    pc = {**empty(), "exclusions": [{"scope": "ticker", "value": "XYZ", "reason": "tenant restriction"}]}
    flags = review(model, personal_context=pc)
    assert any("XYZ" in f["title"] for f in flags)
    assert not any("IBM" in f["title"] for f in flags)


def test_strategy_explanations_are_estimates_with_coverage_not_bucket_promises():
    from officekit import build_model
    from officekit.intake import build_from_answers
    from officekit.thesis_board import stress_estimate, explain_fit
    model = build_model(build_from_answers({"as_of": "2026-01-01", "profile": {}, "sleeves": [
        {"category": "public_equity", "value": 1000, "holdings": [{"company": "AAA", "amount": 1000}]}]}))
    thesis = {"sid": "anything", "bucket": "defensive", "positions": [{"symbol": "AAA", "mv": 1000}]}
    out = stress_estimate(thesis, model)
    assert out["status"] == "estimated" and min(o["pnl"] for o in out["outcomes"]) < 0
    thesis["positions"].append({"symbol": "MISSING", "mv": 100})
    assert stress_estimate(thesis, model)["status"] == "unknown"
    assert "Horizon unknown" in explain_fit("growth", {"label": "Undated"})


def test_pack_cannot_rewrite_court_or_create_portfolio_money(tmp_path):
    from officekit.strategy_packs import load_packs, as_theses
    from officekit.thesis_board import merge
    pack = tmp_path / "quality"
    pack.mkdir()
    (pack / "DECK.md").write_text("Authored thesis")
    (pack / "pack.json").write_text(json.dumps({"id": "quality", "name": "Quality", "bucket": "defensive",
        "author": "contributor", "thesis": "New text", "value": 999999, "verdict": "OWN", "positions": ["AAA"]}))
    packs, errors = load_packs([tmp_path], include_defaults=False)
    assert errors == []
    thesis = as_theses(packs)[0]
    assert thesis["value"] == 0 and thesis["verdict"] == "" and thesis["review_status"] == "schema_valid"
    owned = {"sid": "quality", "value": 100, "verdict": "KILL", "court_date": "2026-01-01"}
    assert merge([owned], [thesis])[0]["verdict"] == "KILL"
    assert merge([owned], [{"sid": "quality", "value": 0, "verdict": "AVOID"}])[0]["value"] == 0
    manifest = json.loads((pack / "pack.json").read_text())
    manifest["deck"] = "../outside.md"
    (tmp_path / "outside.md").write_text("private file")
    (pack / "pack.json").write_text(json.dumps(manifest))
    assert load_packs([tmp_path], include_defaults=False)[1]
