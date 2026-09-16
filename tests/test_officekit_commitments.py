"""Durable edits, first-call budgeting and a cash-only calendar via real HTTP.

Provider calls are stubbed; no financial account or browser automation required.
"""
import copy
import json
import re

import pytest

from officekit import build_from_answers, build_model
from officekit.commitments import (LIFESTYLE, add_commitment, apply_edit, cash_calendar, revision)
from officekit.goal_contention import contention
from officekit.goal_projection import _existing_debt_service
from officekit.goals import evaluate_in_model
from officekit.serve import build_office
from test_officekit_onboarding_e2e import server, _post, _get


def answers():
    return {"as_of": "2026-09-01", "owner": "Commitment test", "profile": {"decumulating": True},
            "sleeves": [{"name": "Cash", "category": "cash", "value": 500000},
                        {"name": "Index", "category": "public_equity", "value": 4500000},
                        {"name": "Home", "category": "real_estate", "value": 1000000},
                        {"name": "Mortgage", "category": "real_estate_debt", "value": 720000}],
            "goals": [{"id": "house", "label": "Second home", "kind": "spending", "amount": 1000000,
                       "finance": {"down_pct": 25, "rate_pct": 5, "term_years": 30}}]}


def by_source(data, source):
    return next(c for c in data["commitments"] if c["source"] == source)


def edit(a, cid, patch):
    return apply_edit(a, cid, patch, revision(a))


def add(a, source="recurring_expense", **fields):
    values = {"source": source, "label": "School fees", "amount": 20000, "cadence": "annual",
              "next_due": "2026-09-01", "funding_source": "portfolio", **fields}
    return add_commitment(a, values, revision(a))


def test_save_build_and_restart_acceptance_journey(server):
    base, folder = server
    original = answers()
    built = build_office(original, folder)
    mortgage = by_source(built, "mortgage")
    home = by_source(built, "property_tax")

    def post(cid, **patch):
        saved = json.loads((folder / "answers.json").read_text())
        status, _, body = _post(base + "/commitments/update", {"cid": cid, "revision": revision(saved), **patch})
        assert status == 303, body

    post(mortgage["id"], rate_pct=5, term_years=10)
    post(home["id"], home_value=1200000)
    post(LIFESTYLE, annual_amount=200000)
    saved = json.loads((folder / "answers.json").read_text())
    status, _, body = _post(base + "/commitments/add", {"revision": revision(saved), "source": "recurring_expense",
        "label": "School fees", "amount": 20000, "cadence": "annual", "next_due": "2026-09-10", "funding_source": "portfolio"})
    assert status == 303, body

    # Cold rebuild from disk: no surviving Python or browser state.
    saved = json.loads((folder / "answers.json").read_text())
    restarted = build_office(json.loads(json.dumps(saved)), folder)
    m = build_model(restarted)
    assert len([s for s in restarted["sleeves"] if s["category"] == "real_estate"]) == 1
    assert next(s for s in restarted["sleeves"] if s["category"] == "real_estate")["value"] == 1200000
    mort = by_source(restarted, "mortgage")
    assert mort["id"] == mortgage["id"] and mort["facts"]["term_years"] == 10
    assert mort["annual_amount"] == 91641 and mort["facts"]["payoff_year"] == 2036
    assert by_source(restarted, "lifestyle")["status"] == "confirmed"
    assert _existing_debt_service(m) == 91641 + 13200 + 200000 + 20000
    assert not evaluate_in_model(restarted["goals"][0], m)["assessment"]["affordable"]
    assert not contention(m, restarted["goals"])["feasible"]
    # The web routes render the same saved amounts and stable identities.
    for page in ("office", "capital", "risk", "scenarios"):
        html = _get(base + f"/pages/{page}.html")
        assert "Traceback" not in html
    assert len((folder / "commitment_history.jsonl").read_text().splitlines()) == 4


def test_confirming_lifestyle_and_adding_school_never_improves_house_affordability():
    a = answers()
    data = build_from_answers(a)
    baseline = evaluate_in_model(data["goals"][0], build_model(data))["assessment"]["sustainable"]
    a = edit(a, LIFESTYLE, {"annual_amount": 200000})
    confirmed = build_model(build_from_answers(a))
    assert evaluate_in_model(confirmed["d"]["goals"][0], confirmed)["assessment"]["sustainable"] == baseline
    a = add(a)
    after = build_model(build_from_answers(a))
    assert evaluate_in_model(after["d"]["goals"][0], after)["assessment"]["sustainable"] == baseline - 20000
    # The same reservation is present when asset marks are shocked.
    stress = evaluate_in_model(after["d"]["goals"][0], after, [(s, -s["value"] * .1) for s in after["sleeves"]])
    assert stress["assessment"]["existing_service"] == _existing_debt_service(after)


def test_mortgage_zero_rate_identity_reorder_and_anchored_payoff():
    a = answers()
    data = build_from_answers(a)
    cid = by_source(data, "mortgage")["id"]
    a = edit(a, cid, {"rate_pct": 0, "term_years": 10})
    first = by_source(build_from_answers(a), "mortgage")
    assert first["annual_amount"] == 72000
    a["sleeves"].reverse()
    a["as_of"] = "2027-09-01"
    later = by_source(build_from_answers(a), "mortgage")
    assert later["id"] == cid and later["ends_on"] == first["ends_on"]
    assert later["facts"]["term_years"] == 9


def test_inferred_home_becomes_one_idempotently_editable_home():
    a = answers()
    a["sleeves"] = [s for s in a["sleeves"] if s["category"] != "real_estate"]
    cid = by_source(build_from_answers(a), "property_tax")["id"]
    a = edit(a, cid, {"home_value": 1000000})
    a = edit(a, cid, {"home_value": 1200000, "annual_amount": 9000})
    homes = [s for s in a["sleeves"] if s["category"] == "real_estate"]
    assert len(homes) == 1 and homes[0]["value"] == 1200000
    c = by_source(build_from_answers(a), "property_tax")
    assert c["id"] == cid and c["annual_amount"] == 9000 and c["status"] == "confirmed"


def test_duplicate_home_names_are_edited_by_id():
    a = answers()
    a["sleeves"].append({"category": "real_estate", "name": "Home", "value": 300000})
    data = build_from_answers(a)
    taxes = [c for c in data["commitments"] if c["source"] == "property_tax"]
    a = edit(a, taxes[1]["id"], {"home_value": 350000})
    assert [s["value"] for s in a["sleeves"] if s["category"] == "real_estate"] == [1000000, 350000]


@pytest.mark.parametrize("patch", [{"rate_pct": "NaN"}, {"rate_pct": -1}, {"term_years": 0},
    {"term_years": 1000}, {"amount": 55}, {"rate_pct": True}, {"annual_amount": 100},
    {"next_due": "2026-02-30"}, {"funding_source": "pending"}, {"cadence": "once"}])
def test_invalid_patch_never_mutates_answers(patch):
    a = answers()
    cid = by_source(build_from_answers(a), "mortgage")["id"]
    before = copy.deepcopy(a)
    with pytest.raises(ValueError):
        edit(a, cid, patch)
    assert a == before


def test_legacy_lifestyle_migration_is_narrow_and_idempotent():
    a = answers()
    a["goals"] += [{"kind": "expense", "label": "Lifestyle spending", "annual_amount": 150000},
                   {"kind": "expense", "label": "School", "annual_amount": 20000}]
    build_from_answers(a)
    again = build_from_answers(a)
    assert by_source(again, "lifestyle")["annual_amount"] == 150000
    assert len(a["commitments"]) == 1
    assert any(g["label"] == "School" for g in a["goals"])


def test_ai_preview_targets_one_record_requires_apply_and_rejects_stale_proposal(server, monkeypatch):
    import officekit.serve as serve
    import officekit_ai.commitment_edit as ai
    monkeypatch.setattr(serve, "_ai", lambda *a, **k: True)
    monkeypatch.setattr(ai, "propose", lambda record, instruction, **kw:
                        {"patch": {"rate_pct": 5, "term_years": 10}, "note": "Updated mortgage terms", "model": "fixture"})
    base, folder = server
    a = answers()
    data = build_office(a, folder)
    before = (folder / "answers.json").read_text()
    cid = by_source(data, "mortgage")["id"]
    status, _, body = _post(base + "/commitments/preview", {"cid": cid, "revision": revision(a), "instruction": "5%, ten years"})
    assert status == 200 and "On file" in body and "Proposed" in body
    assert (folder / "answers.json").read_text() == before
    token = re.search(r'name="token" value="([^"]+)"', body)[1]
    status, _, body = _post(base + "/commitments/apply", {"token": token})
    assert status == 303, body
    saved = json.loads((folder / "answers.json").read_text())
    assert by_source(build_from_answers(saved), "mortgage")["annual_amount"] == 91641
    assert saved["goals"] == a["goals"]
    status, _, body = _post(base + "/commitments/apply", {"token": token})
    assert status == 400 and "already applied" in body.lower()


def test_ai_cannot_retarget_or_change_arbitrary_assets(server, monkeypatch):
    import officekit.serve as serve
    import officekit_ai.commitment_edit as ai
    monkeypatch.setattr(serve, "_ai", lambda *a, **k: True)
    monkeypatch.setattr(ai, "propose", lambda *a, **kw: {"patch": {"id": "another", "value": 999}, "note": "bad"})
    base, folder = server
    a = answers()
    data = build_office(a, folder)
    before = (folder / "answers.json").read_text()
    status, _, body = _post(base + "/commitments/preview", {"cid": by_source(data, "mortgage")["id"],
        "revision": revision(a), "instruction": "change it"})
    assert status == 400 and "selected commitment" in body
    assert (folder / "answers.json").read_text() == before


def calendar_answers():
    a = {"as_of": "2026-09-01", "profile": {"decumulating": False},
         "sleeves": [{"category": "cash", "name": "Cash", "value": 100000},
                     {"category": "public_equity", "name": "Index", "value": 5000000},
                     {"category": "cash_pending", "name": "Pending", "value": 1000000},
                     {"category": "tax_reserve", "name": "Tax", "value": 20000}]}
    build_from_answers(a)
    return a


def test_calendar_uses_cash_only_and_reserves_tax_exactly_once():
    a = add(calendar_answers(), "tax", label="Taxes", amount=12000, cadence="once")
    a = add(a, "capital_call", label="Fund call", amount=10000, cadence="once", next_due="2027-03-15")
    a = add(a, "goal_reservation", label="Home earmark", amount=15000, cadence="once", next_due="2028-01-01")
    cal = cash_calendar(build_model(build_from_answers(a)))
    assert cal["cash"] == 100000 and cal["tax_reserve"] == 8000
    assert cal["held"] == 23000 and cal["outflow"] == 22000
    assert cal["available"] == 55000 and len(cal["months"]) == 12


def test_overdue_one_time_stays_reserved_until_explicit_settlement():
    a = add(calendar_answers(), "capital_call", amount=5000, cadence="once", next_due="2026-08-01")
    c = a["commitments"][-1]
    cal = cash_calendar(build_model(build_from_answers(a)))
    assert cal["months"][0]["outflow"] == 5000
    assert any(p["overdue"] for p in cal["months"][0]["payments"])
    a = edit(a, c["id"], {"settled": True})
    assert cash_calendar(build_model(build_from_answers(a)))["outflow"] == 0


def test_calendar_frequency_end_date_and_income_source():
    a = add(calendar_answers(), amount=3000, cadence="quarterly", next_due="2026-09-30", ends_on="2027-03-30")
    a = add(a, label="Income-funded expense", amount=90000, cadence="annual", funding_source="income")
    m = build_model(build_from_answers(a))
    cal = cash_calendar(m)
    assert cal["outflow"] == 9000
    assert _existing_debt_service(m) == 12000
    # Quarterly end-of-month schedule keeps the anchor across shorter months.
    assert [p["date"] for r in cal["months"] for p in r["payments"] if p["label"] == "School fees"] == [
        "2026-09-30", "2026-12-30", "2027-03-30"]


def test_negative_cash_capacity_is_a_shortfall_not_available_capital():
    a = add(calendar_answers(), "capital_call", amount=150000, cadence="once")
    cal = cash_calendar(build_model(build_from_answers(a)))
    assert cal["available"] == 0 and cal["shortfall"] == 70000


def test_schedule_edit_does_not_confirm_estimated_amount():
    a = calendar_answers()
    a = edit(a, LIFESTYLE, {"next_due": "2026-09-05", "cadence": "monthly"})
    c = by_source(build_from_answers(a), "lifestyle")
    assert c["status"] == "estimated" and not c["schedule_estimated"]


@pytest.mark.parametrize("as_of, expected", [
    ("2026-09-01", "2026-10-01"), ("2026-09-14", "2026-10-01"),
    ("2026-12-31", "2027-01-01"), ("2028-02-29", "2028-03-01"),
])
def test_mortgage_default_is_first_of_next_month_and_actual_date_wins(as_of, expected):
    a = answers()
    a["as_of"] = as_of
    c = by_source(build_from_answers(a), "mortgage")
    assert c["next_due"] == expected and c["schedule_estimated"]
    explicit = as_of[:8] + "15"
    a = edit(a, c["id"], {"next_due": explicit})
    restored = by_source(build_from_answers(json.loads(json.dumps(a))), "mortgage")
    assert restored["next_due"] == explicit and not restored["schedule_estimated"]


def test_scenario_commitment_overlay_uses_identity_and_shared_budget():
    from officekit.goals import apply_goal_ov
    a = answers()
    data = build_from_answers(a)
    m = build_model(data)
    eff = apply_goal_ov(data["goals"], {"modify": [{"id": LIFESTYLE, "annual_amount_delta": 30000}]})
    base = evaluate_in_model(data["goals"][0], m)["assessment"]
    after = evaluate_in_model(data["goals"][0], m, effective_goals=eff)["assessment"]
    assert after["sustainable"] == base["sustainable"] - 30000
    assert by_source(data, "lifestyle")["annual_amount"] == 200000


def test_matured_mortgage_balance_remains_due_in_calendar():
    a = answers()
    cid = by_source(build_from_answers(a), "mortgage")["id"]
    a = edit(a, cid, {"rate_pct": 0, "term_years": 1})
    a["as_of"] = "2028-09-01"
    m = build_model(build_from_answers(a))
    c = by_source(m["d"], "mortgage")
    assert c["amount"] == 720000 and c["active"] and c["cadence"] == "once"
    assert any(p["id"] == cid and p["amount"] == 720000
               for r in cash_calendar(m)["months"] for p in r["payments"])


def test_installments_conserve_annual_amount_including_cents():
    a = calendar_answers()
    a = edit(a, LIFESTYLE, {"annual_amount": 200000, "funding_source": "portfolio"})
    cal = cash_calendar(build_model(build_from_answers(a)))
    assert round(cal["outflow"], 2) == 200000


def test_mortgage_schedule_cannot_start_after_shortened_term():
    a = answers()
    cid = by_source(build_from_answers(a), "mortgage")["id"]
    with pytest.raises(ValueError, match="next payment"):
        edit(a, cid, {"term_years": 1, "next_due": "2035-01-01"})


def test_stale_form_does_not_overwrite_newer_saved_facts(server):
    base, folder = server
    a = answers()
    build_office(a, folder)
    old = revision(a)
    newer = edit(a, LIFESTYLE, {"annual_amount": 160000})
    build_office(newer, folder)
    before = (folder / "answers.json").read_text()
    status, _, body = _post(base + "/commitments/update", {"cid": LIFESTYLE, "revision": old, "annual_amount": 70000})
    assert status == 400 and "office changed" in body.lower()
    assert (folder / "answers.json").read_text() == before
