"""Custody lifecycle invariants, using synthetic accounts and no broker calls."""
import json
import pytest

from officekit import staging
from officekit.reconciliation import reconcile


def pull(folder, rows, day="2026-09-13", account="A", total=None, sid="broker", mode="complete"):
    snapshot = {"mode": mode, "accounts": [account], "security_types": ["STK", "CASH", "OPT", "BOND"],
                "totals": {account: sum(r["value"] for r in rows) if total is None else total}}
    return staging.record_pull(folder, sid, "adapter", sid, rows, "auto", as_of=day, snapshot=snapshot)


def sync(folder, answers):
    rows, _ = staging.merged_rows(folder)
    return reconcile(answers, rows, staging.load(folder)["sources"])


def stock(value=100, account="A", **kw):
    return {"symbol": "AAA", "account": account, "value": value, "sec_type": "STK", **kw}


def test_sale_and_cash_settlement_preserve_account_total(tmp_path):
    pull(tmp_path, [stock(100), {"symbol": "USD", "sec_type": "CASH", "account": "A", "value": 20}], total=120)
    answers, _ = sync(tmp_path, {"as_of": "2026-09-12"})
    assert answers["positions"]["rows"][0]["value"] == 100
    pull(tmp_path, [{"symbol": "USD", "sec_type": "CASH", "account": "A", "value": 120}], day="2026-09-14", total=120)
    answers, report = sync(tmp_path, answers)
    assert answers["positions"]["rows"] == []
    assert sum(s["value"] for s in answers["sleeves"]) == 120
    assert report["removed"] == 1


def test_complete_snapshot_cannot_close_another_account_or_newer_mark(tmp_path):
    pull(tmp_path, [stock(100)], account="A")
    pull(tmp_path, [stock(200, account="B")], account="B", sid="other")
    answers, _ = sync(tmp_path, {})
    pull(tmp_path, [], day="2026-09-14", total=0)
    answers, _ = sync(tmp_path, answers)
    assert answers["positions"]["rows"][0]["value"] == 200
    assert answers["positions"]["rows"][0]["accounts"][0]["account"] == "B"
    older = {"snapshot": {"mode": "complete", "accounts": ["B"], "security_types": ["STK"]},
             "as_of": "2026-01-01"}
    updated, _ = reconcile(answers, [], {"old": older})
    assert updated["positions"]["rows"][0]["value"] == 200


def test_partial_and_failed_pulls_keep_previous_holdings(tmp_path):
    pull(tmp_path, [stock()])
    answers, _ = sync(tmp_path, {})
    pull(tmp_path, [], day="2026-09-14", mode="partial")
    answers, _ = sync(tmp_path, answers)
    assert answers["positions"]["rows"][0]["value"] == 100
    staging.record_failure(tmp_path, "broker", "connection unavailable")
    assert "failed" in staging.ledger(tmp_path)[0]["warnings"][0]
    assert sync(tmp_path, answers)[0]["positions"] == answers["positions"]


def test_invalid_snapshot_does_not_replace_last_good_pull(tmp_path):
    pull(tmp_path, [stock()])
    before = staging.load(tmp_path)
    with pytest.raises(ValueError, match="reconcile"):
        pull(tmp_path, [], total=100)
    with pytest.raises(ValueError, match="cost-only"):
        pull(tmp_path, [stock(value_is_cost=True)])
    with pytest.raises(ValueError, match="finite"):
        pull(tmp_path, [stock(float("nan"))])
    assert staging.load(tmp_path) == before


def test_new_complete_snapshot_suppresses_old_statement_and_cash(tmp_path):
    pull(tmp_path, [stock(), {"symbol": "USD", "account": "A", "sec_type": "CASH", "value": 10}], sid="old", day="2026-09-12")
    pull(tmp_path, [{"symbol": "USD", "account": "A", "sec_type": "CASH", "value": 110}], day="2026-09-13")
    rows, _ = staging.merged_rows(tmp_path)
    assert len(rows) == 1 and rows[0]["value"] == 110


def test_option_contracts_remain_distinct_and_expiry_closes_only_covered_account(tmp_path):
    def option(strike, value):
        return {"symbol": "AAA", "account": "A", "sec_type": "OPT", "strike": strike,
                "right": "P", "expiry": "20261016", "value": value, "description": "same underlying"}
    pull(tmp_path, [stock(), option(50, -10), option(60, 20)])
    answers, _ = sync(tmp_path, {})
    assert len(answers["sleeves"]) == 2
    pull(tmp_path, [stock(), option(60, 20)], day="2026-09-14")
    answers, _ = sync(tmp_path, answers)
    assert len(answers["sleeves"]) == 1 and answers["sleeves"][0]["value"] == 20


def test_unowned_manual_cash_requires_review_before_import(tmp_path):
    pull(tmp_path, [{"symbol": "USD", "account": "A", "sec_type": "CASH", "value": 100}])
    original = {"sleeves": [{"category": "cash", "name": "Manual cash", "value": 100}]}
    answers, report = sync(tmp_path, original)
    assert answers["sleeves"] == original["sleeves"]
    assert "Ownership review" in report["warnings"][0]


def test_partial_refresh_preserves_unconnected_account_contribution(tmp_path):
    answers = {"positions": {"rows": [{"symbol": "AAA", "value": 300, "accounts": [
        {"account": "A", "source": "a", "value": 100}, {"account": "B", "source": "b", "value": 200}]}]}}
    pull(tmp_path, [stock(150)], mode="partial")
    result, _ = sync(tmp_path, answers)
    assert result["positions"]["rows"][0]["value"] == 350


def test_second_household_renders_closed_sale_without_desk(tmp_path, monkeypatch):
    from officekit.serve import build_office, sync_office_from_staging
    monkeypatch.setattr("officekit.serve._discover_cached", lambda: [])
    monkeypatch.setattr("officekit.serve._key_status", lambda _: None)
    monkeypatch.setattr("officekit.serve._ai", lambda *a, **kw: False)
    pull(tmp_path, [stock(1000), {"symbol": "USD", "account": "A", "sec_type": "CASH", "value": 500}])
    answers, _ = sync(tmp_path, {"as_of": "2026-09-13", "profile": {}, "goals": [
        {"kind": "spending", "label": "Education", "date": "2031-09-01", "amount": 1000}]})
    build_office(answers, tmp_path)
    pull(tmp_path, [{"symbol": "USD", "account": "A", "sec_type": "CASH", "value": 1500}], day="2026-09-14")
    report = sync_office_from_staging(tmp_path)
    saved = json.loads((tmp_path / "balance_sheet.json").read_text())
    assert sum(s["value"] for s in saved["sleeves"]) == 1500
    assert report["removed"] == 1
    assert (tmp_path / "pages" / "risk.html").exists()
    # the user's own goal survives; intuited goals (implicit) may accompany it in
    # the built sheet but are never persisted to answers.
    assert len([g for g in saved["goals"] if not g.get("implicit")]) == 1
    answers_saved = json.loads((tmp_path / "answers.json").read_text())
    assert all(not g.get("implicit") for g in answers_saved.get("goals", []))


def test_security_type_survives_ownership_and_scoped_etf_closure(tmp_path):
    row = stock(sec_type="ETF")
    answers = {}
    for day, rows in (("2026-09-13", [row]), ("2026-09-14", [])):
        staging.record_pull(tmp_path, "etf", "adapter", "etf", rows, "auto", as_of=day,
                            snapshot={"mode": "complete", "accounts": ["A"],
                                      "security_types": ["ETF"], "totals": {"A": sum(r["value"] for r in rows)}})
        answers, _ = sync(tmp_path, answers)
    assert answers["positions"]["rows"] == []


def test_stale_cash_and_cost_only_marks_cannot_degrade_nav(tmp_path):
    pull(tmp_path, [{"symbol": "USD", "account": "A", "sec_type": "CASH", "value": 100}])
    answers, _ = sync(tmp_path, {})
    older = {"symbol": "USD", "account": "A", "sec_type": "CASH", "value": 10, "as_of": "2026-01-01"}
    updated, report = reconcile(answers, [older], {})
    assert updated["sleeves"][0]["value"] == 100 and report["warnings"]
    pull(tmp_path, [stock(value_is_cost=True)], mode="partial", day="2026-09-14")
    updated, report = sync(tmp_path, updated)
    assert updated["positions"]["rows"] == [] and report["warnings"]


def test_partial_cost_basis_and_lots_are_not_reported_as_whole_position(tmp_path):
    from officekit.serve import _attach_lots
    rows = [stock(100, cost_basis=110, lots=[{"loss": 10}], loss_lt=10, loss_st=0),
            stock(200, account="B")]
    answers, report = reconcile({}, rows, {}, _attach_lots)
    result = answers["positions"]["rows"][0]
    assert result["value"] == 300 and "cost_basis" not in result and "loss_lt" not in result
    assert result["lots"][0]["account"] == "A" and report["warnings"]
    rows[1].update(cost_basis=220, lots=[{"loss": 20}], loss_lt=0, loss_st=20)
    result = reconcile({}, rows, {}, _attach_lots)[0]["positions"]["rows"][0]
    assert result["cost_basis"] == 330 and result["loss_lt"] == 10 and result["loss_st"] == 20


def test_adapter_snapshot_seam_preserves_last_good_pull_on_failure(tmp_path, monkeypatch):
    import officekit_adapters as adapters
    pull(tmp_path, [stock()])
    before = staging.load(tmp_path)
    monkeypatch.setitem(adapters.ADAPTERS, "fixture", {"factory": lambda: {"snapshot": lambda ctx: {
        "rows": [stock("bad")], "as_of": "2026-09-14", "snapshot": {
            "mode": "complete", "accounts": ["A"], "security_types": ["STK"], "totals": {"A": 100}}}}})
    with pytest.raises(ValueError, match="finite"):
        adapters.fetch_snapshot("fixture")
    assert staging.load(tmp_path) == before
