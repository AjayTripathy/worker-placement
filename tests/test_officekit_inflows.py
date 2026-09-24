"""Receipts reconcile expectations to existing cash without crediting it twice."""
import copy
from datetime import datetime, timedelta, timezone
import json
import re
import uuid

import pytest

from officekit import build_from_answers, build_model
from officekit.commitments import cash_calendar, revision, tax_funding
from officekit.inflows import active_receipts, progress, propose
from officekit.serve import build_office
from test_officekit_onboarding_e2e import server, _post
from test_officekit_source_isolation import pull, sync


def office(cash=250000):
    a = {"as_of": "2026-09-14", "owner": "Receipt test", "profile": {"decumulating": False},
         "sleeves": [{"category": "cash", "name": "Receiving account", "value": cash}],
         "incoming": {"amount": 5000000, "rate": .30, "character": "ltcg", "eta": "September"}}
    build_from_answers(a)
    return a


def fields(a, **kw):
    return {"action": "receive", "inflow_id": a["incoming"]["id"], "gross": "2000000",
            "withheld": "0", "date": "2026-09-14", "account_id": a["sleeves"][0]["id"],
            "reference": "Bank receipt A", "included": "yes", **kw}


def receive(a, **kw):
    return propose(a, fields(a, **kw), revision(a))


def model(a):
    return build_model(build_from_answers(copy.deepcopy(a)))


def test_partial_then_full_receipt_preserves_cash_and_total_net_worth():
    a = office()
    baseline_nw = model(a)["NW"]
    a["sleeves"][0]["value"] += 2000000  # account import already contains first deposit
    received = receive(a)
    assert received["sleeves"] == a["sleeves"] and "inflow_events" not in a
    m = model(received)
    assert progress(received)["pending"] == 3000000
    assert tax_funding(m) == {"current": 600000, "pending": 900000}
    assert cash_calendar(m)["available"] == 1650000 and m["NW"] == baseline_nw
    received["sleeves"][0]["value"] += 3000000  # next imported balance
    received = receive(received, gross="3000000", reference="Bank receipt B")
    m = model(received)
    assert progress(received)["status"] == "received"
    assert not any(s["category"] == "cash_pending" for s in m["assets"])
    assert cash_calendar(m)["cash"] == 5250000 and cash_calendar(m)["available"] == 3750000
    assert tax_funding(m) == {"current": 1500000, "pending": 0} and m["NW"] == baseline_nw
    assert model(json.loads(json.dumps(received)))["NW"] == baseline_nw


@pytest.mark.parametrize("gross,withheld,balance,current,pending,credit", [
    (2000000, 500000, 1750000, 100000, 900000, 0),
    (2000000, 800000, 1450000, 0, 700000, 0),
    (5000000, 1500000, 3750000, 0, 0, 0),
    (5000000, 2000000, 3250000, 0, 0, 500000),
])
def test_withholding_reduces_tax_once_and_excess_is_not_cash(gross, withheld, balance, current, pending, credit):
    a = office(balance)
    updated = receive(a, gross=gross, withheld=withheld)
    m = model(updated)
    assert tax_funding(m) == {"current": current, "pending": pending}
    assert cash_calendar(m)["cash"] == balance
    assert m["NW"] == 3750000
    assert sum(s["value"] for s in m["assets"] if (s.get("meta") or {}).get("withholding_credit")) == credit


def test_reverse_and_replace_retains_evidence_without_touching_cash():
    a = receive(office(2250000))
    receipt = copy.deepcopy(a["inflow_events"][0])
    a = propose(a, {"action": "reverse", "inflow_id": a["incoming"]["id"],
                   "receipt_id": receipt["id"], "reason": "Wrong amount on statement"}, revision(a))
    assert progress(a)["pending"] == 5000000 and not active_receipts(a)
    assert cash_calendar(model(a))["cash"] == 2250000
    assert a["inflow_events"][0] == receipt
    a = receive(a, gross=1800000)  # same reference can replace the reversed attribution
    assert len(a["inflow_events"]) == 3 and len(active_receipts(a)) == 1
    assert progress(a)["pending"] == 3200000


@pytest.mark.parametrize("patch", [
    {"gross": "NaN"}, {"gross": "Infinity"}, {"gross": -1}, {"gross": 0}, {"gross": True},
    {"gross": "12.001"}, {"gross": "5000001"}, {"withheld": "2000001"}, {"withheld": "-1"},
    {"withheld": "nan"}, {"date": "2026-02-30"}, {"date": "2099-01-01"},
    {"account_id": "missing"}, {"inflow_id": "missing"}, {"included": ""}, {"reference": "  "},
])
def test_invalid_receipt_is_nonmutating(patch):
    a = office()
    before = copy.deepcopy(a)
    with pytest.raises(ValueError):
        receive(a, **patch)
    assert a == before


def test_old_account_snapshot_and_duplicate_reference_fail_closed():
    a = office()
    a["sleeves"][0]["meta"] = {"custody_row": {"as_of": "2026-09-01", "source_id": "bank"}}
    with pytest.raises(ValueError, match="predates"):
        receive(a)
    a["sleeves"][0]["meta"]["custody_row"]["as_of"] = "2026-09-14"
    a = receive(a)
    with pytest.raises(ValueError, match="already linked"):
        receive(a, reference="  BANK   receipt a ")
    with pytest.raises(ValueError, match="changed"):
        propose(a, fields(a, reference="New"), "old revision")


def test_cash_cents_and_duplicate_account_names_keep_their_identity():
    a = office(250000.27)
    a["sleeves"].append({"id": str(uuid.uuid4()), "category": "cash", "name": "Receiving account", "value": 1000.53})
    a = receive(a, gross="1000.53", account_id=a["sleeves"][1]["id"])
    assert a["inflow_events"][0]["account_id"] == a["sleeves"][1]["id"]
    m = model(a)
    assert cash_calendar(m)["cash"] == 251000.8
    assert next(s["value"] for s in m["assets"] if s["category"] == "cash_pending") == 4998999.47


def test_fresh_account_receipt_advances_planning_date_without_redating_other_marks():
    a = office(2250000)
    a["as_of"] = "2026-09-07"
    a["sleeves"][0]["meta"] = {"custody_row": {"as_of": "2026-09-14", "source_id": "bank"}}
    updated = receive(a)
    assert updated["as_of"] == "2026-09-14" and updated["sleeves"] == a["sleeves"]


def test_return_of_capital_receipt_has_no_tax_and_withholding_is_a_credit():
    a = office(2250000)
    a["incoming"]["character"] = "return_of_capital"
    updated = receive(a)
    assert tax_funding(model(updated)) == {"current": 0, "pending": 0}
    updated = receive(a, withheld=10000)
    assert sum(s["value"] for s in model(updated)["assets"] if s["category"] == "tax_asset") == 10000


def test_repeated_imports_preserve_receipt_and_do_not_recredit_cash(tmp_path):
    a = office()
    a["sleeves"] = []
    pull(tmp_path, "bank", 2250000, 14, complete=True, sec="CASH")
    a, _ = sync(tmp_path, a)
    build_from_answers(a)  # assign persistent account ID
    a = receive(a)
    evidence = copy.deepcopy(a["inflow_events"][0]["evidence"])
    baseline = cash_calendar(model(a))
    for _ in range(2):
        pull(tmp_path, "bank", 2250000, 14, complete=True, sec="CASH")
        a, _ = sync(tmp_path, json.loads(json.dumps(a)))
        assert cash_calendar(model(a)) == baseline
        assert a["inflow_events"][0]["evidence"] == evidence
    # A subsequent balance decline is source-owned and doesn't reopen the receipt.
    pull(tmp_path, "bank", 1000000, 15, complete=True, sec="CASH")
    a, _ = sync(tmp_path, a)
    assert cash_calendar(model(a))["cash"] == 1000000
    assert progress(a)["pending"] == 3000000


def preview(base, a, **kw):
    status, _, body = _post(base + "/inflows/preview", {"revision": revision(a), **fields(a, **kw)})
    assert status == 200, body
    token = re.search(r'name="token" value="([^"]+)"', body)[1]
    return token, body


def test_http_review_cancel_apply_replay_and_restart(server):
    base, folder = server
    a = office(2250000)
    build_office(a, folder)
    before = (folder / "answers.json").read_text()
    token, body = preview(base, a)
    assert "$600,000" in body and "$900,000" in body and "Current cash (unchanged)" in body
    assert (folder / "answers.json").read_text() == before  # preview/cancel are read-only
    assert _post(base + "/inflows/apply", {"token": token})[0] == 303
    saved = (folder / "answers.json").read_text()
    # Even lost preview stamps/files cannot cause a second credit or event.
    (folder / "inflow_previews" / f"{token}.json").unlink()
    assert _post(base + "/inflows/apply", {"token": token})[0] == 303
    assert (folder / "answers.json").read_text() == saved
    restored = json.loads(saved)
    build_office(restored, folder)
    assert len(restored["inflow_events"]) == 1 and progress(restored)["pending"] == 3000000
    html = (folder / "pages/capital.html").read_text()
    assert "partially received" in html and "Correct this receipt" in html


def test_stale_and_expired_preview_never_change_answers(server):
    base, folder = server
    a = office()
    build_office(a, folder)
    token, _ = preview(base, a)
    a["owner"] = "New revision"
    build_office(a, folder)
    before = (folder / "answers.json").read_text()
    status, _, body = _post(base + "/inflows/apply", {"token": token})
    assert status == 400 and "changed" in body
    token, _ = preview(base, a)
    file = folder / "inflow_previews" / f"{token}.json"
    record = json.loads(file.read_text())
    record["created_at"] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    file.write_text(json.dumps(record))
    assert _post(base + "/inflows/apply", {"token": token})[0] == 400
    assert (folder / "answers.json").read_text() == before


def test_failed_render_does_not_publish_receipt_or_history(server, monkeypatch):
    import officekit.render_capital
    base, folder = server
    a = office()
    build_office(a, folder)
    token, _ = preview(base, a)
    before = (folder / "answers.json").read_text()
    def fail(*args, **kwargs):
        raise RuntimeError("synthetic render failure")
    monkeypatch.setattr(officekit.render_capital, "render_capital", fail)
    assert _post(base + "/inflows/apply", {"token": token})[0] == 500
    assert (folder / "answers.json").read_text() == before


def test_inflow_with_receipts_cannot_be_removed_or_reduced_below_receipts():
    a = receive(office())
    a["incoming"]["amount"] = 1000000
    with pytest.raises(ValueError, match="less than recorded"):
        build_from_answers(a)
    del a["incoming"]
    with pytest.raises(ValueError, match="cannot be removed"):
        build_from_answers(a)


def test_home_and_scenario_deployment_only_use_remaining_proceeds():
    from officekit.commitments import pending_deployable
    from officekit.render_office import render_office, _deploy_plan
    a = receive(office(2250000))
    m = model(a)
    assert pending_deployable(m) == 2100000
    from officekit.deployment import sources, funding
    assert 'deployment_' in _deploy_plan(m)
    assert funding(m, sources(m)[0]['id'])['contingent_budget'] == 2100000
    html = render_office(m)
    assert '$3.00M gross → $2.10M net' in html
    a = receive(a, gross=3000000, reference="Second")
    m = model(a)
    assert pending_deployable(m) == 0
    assert 'deployment_' in _deploy_plan(m)  # received proceeds retain their strategy link


def test_reference_is_escaped_on_preview_and_history(server):
    base, folder = server
    a = office()
    build_office(a, folder)
    token, body = preview(base, a, reference='<script>alert("x")</script>')
    assert '<script>alert' not in body and '&lt;script&gt;' in body
    assert _post(base + "/inflows/apply", {"token": token})[0] == 303
    html = (folder / "pages/capital.html").read_text()
    assert '<script>alert' not in html and '&lt;script&gt;' in html
