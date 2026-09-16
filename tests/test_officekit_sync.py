"""officekit sync + learning + human-capital tests (rulings of 2026-09-02):
the connector interface compounds, failures degrade loud, learning records are
born multi-tenant-shareable, and income is an asset with a beta.
"""
from __future__ import annotations

import json
from datetime import date

import pytest

from officekit import build_from_answers, build_model, render_office, render_scenarios
from officekit import learning, sync
from officekit.render_scenarios import compute_results

TODAY = date(2026, 9, 2)

DATA = {
    "as_of": "2026-09-01",
    "factors": ["S&P 500", "Venture Capital", "Mortgage Debt", "Inflation", "Rates", "USD"],
    "profile": {"net_buyer": True, "uses_leverage": False, "premium_selling_allowed": False,
                "decumulating": False, "concentrated_low_basis": False},
    "sleeves": [
        {"name": "Alpha sleeve (IBKR)", "kind": "asset", "category": "alpha_market_neutral",
         "value": 211000, "target_pct": None, "_confidence": "known", "risks": [],
         "beta": {"Venture Capital": 0.1}},
        {"name": "Index funds", "kind": "asset", "category": "public_equity", "value": 500000,
         "target_pct": None, "_confidence": "known", "risks": [], "beta": {"S&P 500": 1.0}},
    ],
}


@pytest.fixture()
def clean_registry(monkeypatch):
    monkeypatch.setattr(sync, "REGISTRY", {})
    return sync.REGISTRY


# ------------------------------------------------------------------------- sync

def test_sync_apply_stamps_and_staleness(clean_registry):
    @sync.connector(id="fresh_src", label="Fresh broker", max_age_days=2)
    def fresh():
        return {"as_of": "2026-09-02", "provenance": "test feed",
                "updates": [{"match": {"category": "alpha_market_neutral"}, "value": 931473.33}]}

    @sync.connector(id="stale_src", label="Stale custodian", max_age_days=7)
    def stale():
        return {"as_of": "2026-07-07", "provenance": "old bundle",
                "updates": [{"match": {"category": "public_equity"}, "value": 512000}]}

    @sync.connector(id="broken_src", label="Broken API", max_age_days=1)
    def broken():
        raise ConnectionError("timeout")

    data = json.loads(json.dumps(DATA))
    report = sync.apply(data, sync.run(), today=TODAY)
    by = {r["connector"]: r for r in report}
    assert by["fresh_src"]["status"] == "FRESH"
    assert by["stale_src"]["status"] == "STALE" and by["stale_src"]["age_days"] == 57
    assert by["broken_src"]["status"] == "ERROR" and "timeout" in by["broken_src"]["detail"]
    alpha = next(s for s in data["sleeves"] if s["category"] == "alpha_market_neutral")
    assert alpha["value"] == 931473 and alpha["sync"]["connector"] == "fresh_src"
    m = build_model(data, today=TODAY)
    assert m["sync_n"] == 2 and m["sync_stale"] == 1
    html = render_office(m)
    assert "2 sleeves live-synced, 1 STALE" in html
    assert "synced 2026-09-02" in html and "STALE · 2026-07-07" in html


def test_sync_unmatched_update_warns_not_silently(clean_registry):
    @sync.connector(id="orphan", label="No such sleeve", max_age_days=2)
    def orphan():
        return {"as_of": "2026-09-02", "updates": [{"match": {"category": "venture_private"}, "value": 1}]}

    report = sync.apply(json.loads(json.dumps(DATA)), sync.run(), today=TODAY)
    assert any(r["status"] == "WARN" and "no sleeve matched" in r["detail"] for r in report)


def test_no_sync_means_no_badges():
    m = build_model(json.loads(json.dumps(DATA)), today=TODAY)
    assert m["sync_n"] == 0
    assert "live-synced" not in render_office(m)


# --------------------------------------------------------------------- learning

def test_learning_observe_dedupe_and_shareable_export(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    data = json.loads(json.dumps(DATA))
    data["goals"] = [{"kind": "liquidity_floor", "label": "My secret floor", "amount": 50000}]
    m = build_model(data, today=TODAY)
    _, _, results = compute_results(m)
    assert set(learning.observe(m, ledger, results=results, today=TODAY)) == \
        {"snapshot", "scenario_run", "goal_status"}
    assert learning.observe(m, ledger, results=results, today=TODAY) == []   # daily idempotent
    recs = [json.loads(l) for l in ledger.read_text().splitlines()]
    assert all(r["tenant"] == "local" and r["v"] == 1 for r in recs)
    snap = next(r for r in recs if r["kind"] == "snapshot")["payload"]
    assert snap["nw_decade"] == 5 and abs(sum(snap["cat_weights"].values()) - 100) < 1
    # the export allowlist is the multi-tenant contract: no names, no dollars
    out = json.dumps(learning.export_shareable(ledger, tenant="t_042"))
    assert "t_042" in out
    for leak in ("Index funds", "Alpha sleeve", "My secret floor", "500000", "211000", "50000"):
        assert leak not in out, f"leak in shareable export: {leak}"


# --------------------------------------------- income is an asset with a beta

INCOME_ANSWERS = {
    "owner": "Kai", "as_of": "2026-09-01",
    "profile": {"net_buyer": True},
    "sleeves": [{"category": "cash", "value": 100000},
                {"category": "public_equity", "value": 400000}],
    "income": {"annual": 350000, "years": 20, "style": "equity_linked"},
}


def test_income_capitalizes_into_a_beta_bearing_sleeve():
    data = build_from_answers(INCOME_ANSWERS)
    hc = next(s for s in data["sleeves"] if s["category"] == "human_capital")
    assert 4_700_000 < hc["value"] < 4_800_000        # PV of 350k×20y at 4% ≈ $4.76M
    assert hc["beta"]["S&P 500"] == 0.70 and hc["beta"]["Inflation"] == 0.10   # equity_linked style
    assert hc["_confidence"] == "assumption"          # a model, not a statement
    m = build_model(data, today=TODAY)
    html = render_scenarios(m)
    assert "Income shock (job loss / disability)" in html
    assert "Long-term disability insurance" in html
    # capitalized income is NOT liquidity: raisable excludes the $4.7M sleeve
    _, _, results = compute_results(m)
    assert all(r["cash_now"] + r["mkt"] < 600_000 for r in results)


def test_income_shock_absent_without_human_capital():
    data = build_from_answers({k: v for k, v in INCOME_ANSWERS.items() if k != "income"})
    assert "Income shock" not in render_scenarios(build_model(data, today=TODAY))


# ---------------------------------------------------------------- identity (GUIDs)

class TestIdentity:
    """Multitenant identity: office_id minted once at intake and stamped on every
    durable document + ledger record; per-goal ids; per-record ids. No GUID ever
    renders into a page (goldens prove that separately by staying byte-identical)."""

    def _answers(self):
        return {"as_of": "2026-09-02",
                "sleeves": [{"category": "cash", "value": 50000}],
                "goals": [{"kind": "liquidity_floor", "label": "Floor", "amount": 20000}]}

    def test_office_id_minted_and_stable_across_rebuilds(self):
        import uuid
        from officekit.intake import build_from_answers
        answers = self._answers()
        d1 = build_from_answers(answers)
        oid = d1["office_id"]
        uuid.UUID(oid)  # valid UUID
        assert answers["office_id"] == oid  # written back so persisted answers keep it
        d2 = build_from_answers(answers)  # rebuild from the same answers
        assert d2["office_id"] == oid

    def test_goal_ids_minted_and_stable(self):
        from officekit.intake import build_from_answers
        answers = self._answers()
        d1 = build_from_answers(answers)
        gid = d1["goals"][0]["id"]
        assert gid and build_from_answers(answers)["goals"][0]["id"] == gid

    def test_schema_rejects_malformed_office_id(self):
        from officekit.schema import validate
        base = {"as_of": "2026-09-02", "factors": ["S&P 500"], "profile": {},
                "sleeves": [{"name": "Cash", "kind": "asset", "category": "cash",
                             "value": 1000, "beta": {}}]}
        assert not [x for x in validate(base) if "office_id" in x]  # optional
        assert not [x for x in validate({**base, "office_id": "a11e0f5e-9e1c-4f6d-8c2a-000000000001"}) if "office_id" in x]
        assert [x for x in validate({**base, "office_id": "not-a-uuid"}) if "office_id" in x]

    def test_ledger_records_carry_ids(self, tmp_path):
        import json
        from officekit.intake import build_from_answers
        from officekit.learning import export_shareable, observe
        from officekit.model import build_model
        answers = self._answers()
        data = build_from_answers(answers)
        m = build_model(data)
        ledger = tmp_path / "learning.jsonl"
        observe(m, ledger)
        recs = [json.loads(x) for x in ledger.read_text().splitlines()]
        assert recs
        ids = set()
        for r in recs:
            assert r["office_id"] == data["office_id"]
            assert r["id"] and r["id"] not in ids  # per-record, unique
            ids.add(r["id"])
        gs = [r for r in recs if r["kind"] == "goal_status"]
        assert gs and gs[0]["payload"]["goals"][0]["id"] == data["goals"][0]["id"]
        # ids survive the shareable exit path (they are identity, not personal data)
        shared = export_shareable(ledger)
        assert all(r["id"] and r["office_id"] == data["office_id"] for r in shared)
