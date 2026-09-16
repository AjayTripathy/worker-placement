"""Review regressions: funding provenance, overlapping spend, disposable previews."""
import copy
from datetime import datetime, timedelta, timezone
import json
import uuid

import pytest

from officekit import build_from_answers, build_model
from officekit.commitments import (LIFESTYLE, cash_calendar, revision, tax_funding)
from officekit.goal_contention import contention
from officekit.goal_projection import _existing_debt_service
from officekit.goals import apply_goal_ov, evaluate_in_model
from officekit.serve import build_office
from test_officekit_commitments import answers, by_source, edit
from test_officekit_onboarding_e2e import server, _post


def pending_office():
    a = answers()
    a["as_of"] = "2026-09-07"
    a["profile"]["decumulating"] = False
    a["sleeves"] = [s for s in a["sleeves"] if s["category"] != "real_estate"]
    a["sleeves"][0]["value"] = 249288
    a["incoming"] = {"amount": 5000000, "rate": .3342982, "character": "ltcg", "eta": "2026-09"}
    return a


def test_pending_inflow_and_its_tax_are_excluded_symmetrically():
    a = pending_office()
    data = build_from_answers(a)
    m = build_model(data)
    cal = cash_calendar(m)
    assert cal["cash"] == 249288
    assert cal["pending_tax_reserve"] == 1671491
    assert cal["tax_reserve"] == 0 and cal["held"] == 0 and cal["shortfall"] == 0
    assert cal["available"] == 190152.91
    baseline = copy.deepcopy(a)
    del baseline["incoming"]
    assert cal["available"] == cash_calendar(build_model(build_from_answers(baseline)))["available"]
    # Tax remains a liability in net worth; only its cash funding is different.
    assert sum(abs(s["value"]) for s in m["liabs"] if s["category"] == "tax_reserve") == 1671491
    restored = build_model(build_from_answers(json.loads(json.dumps(a))))
    assert cash_calendar(restored) == cal


def test_receiving_linked_inflow_keeps_tax_reserved_without_duplicating_cash():
    data = build_from_answers(pending_office())
    before = build_model(data)
    received = copy.deepcopy(data)
    pending = next(s for s in received["sleeves"] if s["category"] == "cash_pending")
    pending["category"] = "cash"  # receipt transition, same asset ID; no second asset
    after = build_model(received)
    cal = cash_calendar(after)
    assert cal["pending_tax_reserve"] == 0 and cal["tax_reserve"] == 1671491
    assert cal["cash"] == 5249288
    assert cal["available"] == cash_calendar(before)["available"] + 5000000 - 1671491
    assert before["NW"] == after["NW"]


def test_unrelated_tax_and_scheduled_tax_still_require_current_cash():
    from officekit.commitments import add_commitment
    a = pending_office()
    a["sleeves"].append({"name": "Prior year taxes", "category": "tax_reserve", "value": 20000})
    build_from_answers(a)
    a = add_commitment(a, {"source": "tax", "label": "Confirmed tax payment", "amount": 25000,
                           "cadence": "once", "next_due": "2026-10-15", "funding_source": "portfolio"}, revision(a))
    cal = cash_calendar(build_model(build_from_answers(a)))
    assert cal["pending_tax_reserve"] == 1671491
    assert cal["held"] == 0  # 20k existing liability is scheduled, not counted twice
    assert cal["available"] == 190152.91 - 25000


def test_matching_amount_or_label_is_not_an_inflow_link():
    data = build_from_answers(pending_office())
    data["tax_model"].pop("inflow_id")
    cal = cash_calendar(build_model(data))
    assert cal["pending_tax_reserve"] == 0 and cal["held"] == 1671491


def test_tax_cannot_be_ring_fenced_beyond_linked_pending_proceeds():
    data = build_from_answers(pending_office())
    next(s for s in data["sleeves"] if s["category"] == "cash_pending")["value"] = 100000
    funding = tax_funding(build_model(data))
    assert funding == {"current": 1571491, "pending": 100000}


def retired_office(spend=150000, basis="household_total"):
    a = {"as_of": "2026-09-07", "profile": {"decumulating": True},
         "sleeves": [{"category": "cash", "name": "Cash", "value": 5000000}],
         "goals": [{"id": "retire", "kind": "retirement", "label": "Retirement",
                    "annual_spending": spend, "spending_basis": basis}]}
    return a


def test_current_retirement_target_replaces_estimate_and_is_reserved_once():
    a = retired_office()
    m = build_model(build_from_answers(a))
    life = by_source(m["d"], "lifestyle")
    assert life["annual_amount"] == 150000
    assert life["retirement_goal_ids"] == ["retire"] and life["status"] == "estimated"
    assert _existing_debt_service(m) == 150000
    assert cash_calendar(m)["outflow"] == 137500  # next eleven monthly payments
    plan = contention(m, m["d"]["goals"])
    assert plan["existing_service"] == 150000 and plan["carry_claim"] == 0 and plan["feasible"]
    ev = evaluate_in_model(a["goals"][0], m)
    assert ev["ratio"] == pytest.approx(200000 / 150000)
    assert "counted once" in ev["detail"]


def test_confirmed_spend_is_not_silently_lowered_by_a_retirement_target():
    a = retired_office(100000)
    build_from_answers(a)
    a = edit(a, LIFESTYLE, {"annual_amount": 180000})
    m = build_model(build_from_answers(a))
    assert by_source(m["d"], "lifestyle")["annual_amount"] == 180000
    plan = contention(m, m["d"]["goals"])
    assert plan["existing_service"] == 180000 and plan["carry_claim"] == 0
    # A higher retirement target claims only the extra spending.
    a["goals"][0]["annual_spending"] = 220000
    m = build_model(build_from_answers(a))
    plan = contention(m, m["d"]["goals"])
    assert plan["carry_claim"] == 40000 and not plan["feasible"]


def test_multiple_household_targets_share_one_spending_pool():
    a = retired_office(160000)
    a["goals"].append({"id": "retire2", "kind": "retirement", "label": "Later retirement", "annual_spending": 190000})
    m = build_model(build_from_answers(a))
    assert _existing_debt_service(m) == 190000
    assert contention(m, m["d"]["goals"])["carry_claim"] == 0
    a = edit(a, LIFESTYLE, {"annual_amount": 150000})
    for ordered in (a["goals"], list(reversed(a["goals"]))):
        test = dict(a, goals=ordered)
        m = build_model(build_from_answers(test))
        assert contention(m, m["d"]["goals"])["carry_claim"] == 40000


def test_additional_spending_is_not_merged_and_future_goal_does_not_replace_current_lifestyle():
    a = retired_office(30000, basis="additional")
    m = build_model(build_from_answers(a))
    assert _existing_debt_service(m) == 200000
    assert contention(m, m["d"]["goals"])["carry_claim"] == 30000
    a = retired_office(150000)
    a["goals"][0]["date"] = "2040-01-01"
    m = build_model(build_from_answers(a))
    assert by_source(m["d"], "lifestyle")["annual_amount"] == 200000
    a["profile"]["decumulating"] = False
    m = build_model(build_from_answers(a))
    assert _existing_debt_service(m) == 0
    assert contention(m, m["d"]["goals"])["carry_claim"] == 150000


def test_scenario_retirement_change_flows_into_shared_fixed_budget_without_mutation():
    a = retired_office()
    m = build_model(build_from_answers(a))
    goal = {"kind": "spending", "label": "Home", "amount": 1000000, "finance": {"down_pct": 25}}
    baseline = evaluate_in_model(goal, m)["assessment"]
    eff = apply_goal_ov(m["d"]["goals"], {"modify": [{"id": "retire", "annual_spending": 180000}]})
    after = evaluate_in_model(goal, m, effective_goals=eff)["assessment"]
    assert after["existing_service"] == baseline["existing_service"] + 30000
    lifestyle = next(g for g in eff if g.get("source") == "lifestyle")
    assert evaluate_in_model(lifestyle, m, effective_goals=eff)["assessment"]["annual"] == 180000
    assert _existing_debt_service(m) == 150000


def test_retirement_basis_can_be_reviewed_and_saved(server):
    base, folder = server
    a = retired_office()
    build_office(a, folder)
    html = (folder / "pages/goal_retire.html").read_text()
    assert "Household total, including lifestyle" in html and "Additional to lifestyle" in html
    status, _, body = _post(base + "/goal/params", {"gid": "retire", "spending_basis": "additional"})
    assert status == 303, body
    saved = json.loads((folder / "answers.json").read_text())
    assert saved["goals"][0]["spending_basis"] == "additional"
    m = build_model(build_from_answers(saved))
    assert contention(m, m["d"]["goals"])["carry_claim"] == 150000


def test_preview_cleanup_expiry_capacity_and_audit_preservation(tmp_path, monkeypatch):
    import officekit.commitment_routes as routes
    now = datetime.now(timezone.utc)
    directory = tmp_path / "commitment_previews"
    directory.mkdir()

    def write(age, applied=False):
        token = str(uuid.uuid4())
        record = {"created_at": (now - age).isoformat()}
        if applied:
            record["applied_at"] = record["created_at"]
        p = directory / (token + ".json")
        p.write_text(json.dumps(record))
        return p

    expired = write(timedelta(hours=25))
    old_applied = write(timedelta(days=8), applied=True)
    recent_applied = write(timedelta(days=2), applied=True)
    active = write(timedelta(hours=1))
    (directory / "notes.json").write_text('{}')
    (tmp_path / "commitment_history.jsonl").write_text('audit\n')
    routes.prune_previews(tmp_path, now)
    assert not expired.exists() and not old_applied.exists()
    assert recent_applied.exists() and active.exists()
    assert (directory / "notes.json").exists()
    monkeypatch.setattr(routes, "MAX_PREVIEWS", 2)
    newest = write(timedelta(minutes=1))
    routes.prune_previews(tmp_path, now)
    assert not recent_applied.exists() and newest.exists() and active.exists()
    assert (tmp_path / "commitment_history.jsonl").read_text() == 'audit\n'


def test_expired_preview_cannot_be_applied_even_if_revision_still_matches(server):
    base, folder = server
    a = answers()
    build_office(a, folder)
    before = (folder / "answers.json").read_text()
    token = str(uuid.uuid4())
    directory = folder / "commitment_previews"
    directory.mkdir()
    (directory / f"{token}.json").write_text(json.dumps({"revision": revision(a), "cid": LIFESTYLE,
        "patch": {"annual_amount": 10}, "created_at": (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()}))
    status, _, body = _post(base + "/commitments/apply", {"token": token})
    assert status == 400 and "expired" in body
    assert (folder / "answers.json").read_text() == before


def test_preview_has_explicit_document_wrappers_and_escapes_user_text():
    from officekit.render_capital import render_preview
    c = by_source(build_from_answers(answers()), "mortgage")
    html = render_preview(c, {"rate_pct": 5}, str(uuid.uuid4()), "<script>unsafe</script>")
    assert html.index('<head>') < html.index('<meta') < html.index('</head>') < html.index('<body>') < html.index('<main')
    assert html.endswith('</main></body></html>') and '<script>unsafe' not in html


def test_legacy_mortgage_route_updates_only_an_unambiguous_target(server):
    base, folder = server
    a = answers()
    build_office(a, folder)
    status, _, body = _post(base + "/goals/mortgage", {"sleeve": "Mortgage", "rate_pct": 5, "term_years": 10})
    assert status == 303, body
    saved = json.loads((folder / "answers.json").read_text())
    assert by_source(build_from_answers(saved), "mortgage")["annual_amount"] == 91641
    for page in ("office", "capital"):
        assert 'action="/goals/mortgage"' not in (folder / f"pages/{page}.html").read_text()
    saved["sleeves"].append({"name": "Mortgage", "category": "real_estate_debt", "value": 100000})
    build_office(saved, folder)
    before = (folder / "answers.json").read_text()
    status, _, body = _post(base + "/goals/mortgage", {"sleeve": "Mortgage", "rate_pct": 8})
    assert status == 400 and "specific mortgage" in body
    assert (folder / "answers.json").read_text() == before
