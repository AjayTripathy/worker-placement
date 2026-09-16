"""Retained generic-account observations stay isolated through later refreshes.

These fixtures declare separate source contributions. They do not infer whether
matching non-generic account labels represent independent owners.
"""
import copy
import json

import pytest

from officekit import staging
from officekit.reconciliation import reconcile


def pull(folder, source, value, day, *, complete=False, sec="STK", **fields):
    row = {"symbol": "USD" if sec == "CASH" else "AAA", "account": "brokerage",
           "sec_type": sec, "ccy": "USD", "value": value, **fields}
    snapshot = {"mode": "partial"}
    if complete:
        snapshot = {"mode": "complete", "accounts": ["brokerage"],
                    "security_types": [sec], "totals": {"brokerage": value or 0}}
    staging.record_pull(folder, source, "adapter", source,
                        [] if value is None else [row], "auto",
                        as_of=f"2026-09-{day:02d}", snapshot=snapshot)


def sync(folder, answers):
    rows, _ = staging.merged_rows(folder)
    return reconcile(answers, rows, staging.load(folder)["sources"])


def test_complete_closure_preserves_other_source_and_survives_reload(tmp_path):
    pull(tmp_path, "a", 100, 12)
    pull(tmp_path, "b", 200, 13)
    answers, _ = sync(tmp_path, {})
    assert answers["positions"]["rows"][0]["value"] == 300
    # Emulate saved answers loaded by a restarted process.
    (tmp_path / "answers.json").write_text(json.dumps(answers))
    answers = json.loads((tmp_path / "answers.json").read_text())
    pull(tmp_path, "b", None, 14, complete=True)
    updated, report = sync(tmp_path, answers)
    position, = updated["positions"]["rows"]
    assert position["value"] == 100
    assert [a["source"] for a in position["accounts"]] == ["a"]
    assert report["closed"] == [{"symbol": "AAA", "account": "brokerage",
                                 "source": "b", "security_type": "equity"}]
    assert sync(tmp_path, updated)[0]["positions"] == updated["positions"]
    assert answers["positions"]["rows"][0]["value"] == 300  # pure transform


def test_partial_omission_preserves_other_source_value(tmp_path):
    pull(tmp_path, "a", 100, 12)
    pull(tmp_path, "b", 200, 13)
    answers, _ = sync(tmp_path, {})
    pull(tmp_path, "a", 150, 14)
    pull(tmp_path, "b", None, 15)
    updated, report = sync(tmp_path, answers)
    position, = updated["positions"]["rows"]
    assert position["value"] == 350
    assert {a["source"]: a["value"] for a in position["accounts"]} == {"a": 150, "b": 200}
    assert not report["closed"]
    assert sync(tmp_path, updated)[0]["positions"] == updated["positions"]


def test_failed_refresh_cannot_change_another_sources_marks(tmp_path):
    pull(tmp_path, "a", 100, 12)
    pull(tmp_path, "b", 200, 13)
    answers, _ = sync(tmp_path, {})
    pull(tmp_path, "a", 150, 14)
    staging.record_failure(tmp_path, "b", "offline")
    updated, report = sync(tmp_path, answers)
    assert updated["positions"]["rows"][0]["value"] == 350
    assert not report["closed"]


def test_cost_only_refresh_uses_its_own_sources_prior_mark(tmp_path):
    pull(tmp_path, "a", 100, 12)
    pull(tmp_path, "b", 200, 13)
    answers, _ = sync(tmp_path, {})
    pull(tmp_path, "a", 80, 14, value_is_cost=True, cost_basis=80)
    updated, _ = sync(tmp_path, answers)
    position, = updated["positions"]["rows"]
    assert position["value"] == 300
    assert {a["source"]: a["value"] for a in position["accounts"]} == {"a": 100, "b": 200}


@pytest.mark.parametrize("sec,fields", [
    ("CASH", {}), ("OPT", {"expiry": "20261016", "right": "P", "strike": 50}),
    ("BOND", {"cusip": "TEST00001"}),
])
def test_nonequity_partial_refresh_and_complete_closure_are_source_scoped(tmp_path, sec, fields):
    pull(tmp_path, "a", 100, 12, complete=True, sec=sec, **fields)
    pull(tmp_path, "b", 200, 13, complete=True, sec=sec, **fields)
    answers, _ = sync(tmp_path, {})
    assert len(answers["sleeves"]) == 2
    assert sum(s["value"] for s in answers["sleeves"]) == 300
    pull(tmp_path, "a", 150, 14, sec=sec, **fields)
    pull(tmp_path, "b", None, 15, sec=sec, **fields)
    updated, _ = sync(tmp_path, answers)
    assert len(updated["sleeves"]) == 2
    assert sum(s["value"] for s in updated["sleeves"]) == 350
    pull(tmp_path, "b", None, 16, complete=True, sec=sec, **fields)
    updated, report = sync(tmp_path, updated)
    sleeve, = updated["sleeves"]
    assert sleeve["value"] == 150 and sleeve["meta"]["custody_row"]["source_id"] == "a"
    assert [r["source"] for r in report["closed"]] == ["b"]
    assert sync(tmp_path, updated)[0]["sleeves"] == updated["sleeves"]


def test_legacy_cash_key_recovers_source_from_persisted_provenance(tmp_path):
    pull(tmp_path, "a", 100, 12, complete=True, sec="CASH")
    answers, _ = sync(tmp_path, {})
    answers["sleeves"][0]["meta"]["custody_key"] = answers["sleeves"][0]["meta"]["custody_key"][:5]
    original = copy.deepcopy(answers)
    pull(tmp_path, "b", None, 14, complete=True, sec="CASH")
    updated, report = sync(tmp_path, answers)
    assert len(updated["sleeves"]) == 1 and updated["sleeves"][0]["value"] == 100
    assert updated["sleeves"][0]["meta"]["custody_key"][-1] == "a"
    assert not report["closed"] and answers == original
    pull(tmp_path, "a", 150, 15, sec="CASH")
    assert sync(tmp_path, updated)[0]["sleeves"][0]["value"] == 150


def test_missing_source_cannot_authorize_generic_account_closure(tmp_path):
    original = {"positions": {"rows": [{"symbol": "AAA", "value": 100, "accounts": [
        {"account": "brokerage", "value": 100, "as_of": "2026-09-12"}]}]}}
    pull(tmp_path, "b", None, 14, complete=True)
    updated, report = sync(tmp_path, original)
    assert updated["positions"]["rows"][0]["value"] == 100
    assert not report["closed"]


def test_missing_account_refresh_does_not_duplicate_its_prior_contribution(tmp_path):
    pull(tmp_path, "a", 100, 12, account=None)
    pull(tmp_path, "b", 200, 13, account=None)
    answers, _ = sync(tmp_path, {})
    pull(tmp_path, "a", 150, 14, account=None)
    pull(tmp_path, "b", None, 15, account=None)
    assert sync(tmp_path, answers)[0]["positions"]["rows"][0]["value"] == 350


def test_another_sources_complete_coverage_cannot_authorize_cash_creation(tmp_path):
    pull(tmp_path, "a", 100, 12, sec="CASH")
    pull(tmp_path, "b", None, 14, complete=True, sec="CASH")
    updated, _ = sync(tmp_path, {})
    assert updated["sleeves"] == []  # A only has partial coverage


def test_saved_office_refresh_preserves_sources_after_restart(tmp_path, monkeypatch):
    from officekit.serve import build_office, sync_office_from_staging
    monkeypatch.setattr("officekit.serve._discover_cached", lambda: [])
    monkeypatch.setattr("officekit.serve._key_status", lambda _: None)
    monkeypatch.setattr("officekit.serve._ai", lambda *a, **kw: False)
    pull(tmp_path, "a", 100, 12)
    pull(tmp_path, "b", 200, 13)
    answers, _ = sync(tmp_path, {"as_of": "2026-09-13", "profile": {}})
    build_office(answers, tmp_path)
    pull(tmp_path, "a", 150, 14)
    pull(tmp_path, "b", None, 15)
    sync_office_from_staging(tmp_path)
    saved = json.loads((tmp_path / "answers.json").read_text())
    assert saved["positions"]["rows"][0]["value"] == 350
    build_office(saved, tmp_path)  # rebuild from durable state
    pull(tmp_path, "b", None, 16, complete=True)
    sync_office_from_staging(tmp_path)
    saved = json.loads((tmp_path / "answers.json").read_text())
    assert saved["positions"]["rows"][0]["value"] == 150
    sheet = json.loads((tmp_path / "balance_sheet.json").read_text())
    assert sum(s["value"] for s in sheet["sleeves"]) == 150
