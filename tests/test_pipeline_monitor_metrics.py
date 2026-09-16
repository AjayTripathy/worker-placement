"""Tests for pipeline_metrics + pipeline_monitor (mailer mocked; sandboxed stores)."""
import datetime
import json

import pytest

from desk import pipeline_metrics as PM
from desk import pipeline_monitor as PMON


@pytest.fixture
def env(tmp_path, monkeypatch):
    data = tmp_path / "desk" / "data"
    (data / "edge_classifications").mkdir(parents=True)
    (tmp_path / "desk" / "ui" / "data").mkdir(parents=True)
    (tmp_path / "desk" / "ui" / "static").mkdir(parents=True)
    for mod in (PM, PMON):
        monkeypatch.setattr(mod, "ROOT", tmp_path)
        monkeypatch.setattr(mod, "DATA", data)
    monkeypatch.setattr(PMON, "STATE", data / "pipeline_monitor_state.json")
    from desk.store import Store
    monkeypatch.setattr(PM, "OUT", Store(data / "pipeline_metrics.json",
                                         list_path="snapshots", key=lambda s: s["date"]))
    return tmp_path


def _seed_minimal(env):
    data = env / "desk" / "data"
    (data / "research_ledger.json").write_text(json.dumps({"names": [
        {"ticker": "AAA", "verdict": "WATCH", "source": "trap-batch1"},
        {"ticker": "BBB", "verdict": "WATCH", "source": "trap-batch1"},
    ]}))
    (data / "resolution_packs.json").write_text(json.dumps({"packs": {
        "AAA|2099-01-01": {"tier": "B"},                       # future: AAA wired
        "OLD|2020-01-01": {"tier": "B"},                       # stale, unadjudicated
        "DONE|2020-01-05": {"tier": "B", "lifecycle": "adjudicated"},
    }}))
    (data / "calibration_ledger.jsonl").write_text(
        json.dumps({"ticker": "X", "cat_date": "2020-01-01", "status": "RESOLVED",
                    "resolution": {"date": "2020-01-02"}}) + "\n")
    (env / "desk/ui/data/positions_cache.json").write_text(json.dumps({"positions": [
        {"symbol": "ZZZ", "sec_type": "STK", "qty": 10, "avg_cost": 5.0, "ccy": "USD"}]}))
    (env / "desk/ui/static/positions_board.json").write_text(json.dumps(
        {"fx": {"USD": 1.0}, "generated_utc": "2026-01-01T00:00:00Z"}))


def test_snapshot_computes_and_persists(env):
    _seed_minimal(env)
    s = PM.snapshot()
    assert s["p1"]["watch_count"] == 2 and s["p1"]["watch_wired"] == 1
    assert s["p1"]["watch_wired_pct"] == 50.0
    assert s["p2"]["status"] == "detector_not_built"
    assert s["p3"]["packs_past_date"] == 2 and s["p3"]["packs_stale"] == 1
    assert s["p3"]["unclassified_held"] == ["ZZZ"]
    assert s["p3"]["unclassified_cost_usd"] == 50
    PM.OUT.upsert([s], generated_by="t")
    again = PM.OUT.rows()
    assert len(again) == 1
    # same-day rerun MERGES, never duplicates
    PM.OUT.upsert([s], generated_by="t")
    assert len(PM.OUT.rows()) == 1


def test_monitor_rate_limits_by_breach_key(env, monkeypatch):
    _seed_minimal(env)
    sent = []
    monkeypatch.setattr(PMON, "collect_criticals",
                        lambda: ["CRITICAL STALE-PACK: OLD|2020-01-01 is 999d past"])
    import types
    fake_mailer = types.SimpleNamespace(
        send_raw=lambda subj, body: sent.append((subj, body)) or True,
        send=lambda *a, **k: True,
        event_subject=lambda m, prefix="SignalOS": m)
    monkeypatch.setitem(__import__("sys").modules, "desk.mailer", fake_mailer)
    first = PMON.immediate_pass()
    assert len(first) == 1 and len(sent) == 1
    second = PMON.immediate_pass()          # same breach within 24h: suppressed
    assert second == [] and len(sent) == 1
    # a DIFFERENT breach key still gets through
    monkeypatch.setattr(PMON, "collect_criticals",
                        lambda: ["CRITICAL UNWIRED-TRIPWIRE: NEWNAME (WATCH) has no pack"])
    third = PMON.immediate_pass()
    assert len(third) == 1 and len(sent) == 2


def test_metrics_staleness_is_a_breach(env, monkeypatch):
    _seed_minimal(env)
    monkeypatch.setattr("desk.pipeline_invariants.run_all", lambda flags=None: [])
    crits = PMON.collect_criticals()        # no metrics snapshot exists yet
    assert any("METRICS-STALE" in c for c in crits)
    # write a fresh snapshot -> breach clears
    (env / "desk/data/pipeline_metrics.json").write_text(json.dumps(
        {"snapshots": [{"date": datetime.date.today().isoformat(), "p1": {}, "p3": {}}]}))
    crits2 = PMON.collect_criticals()
    assert not any("METRICS-STALE" in c for c in crits2)


def test_digest_renders_without_mail(env):
    _seed_minimal(env)
    s = PM.snapshot()
    PM.OUT.upsert([s], generated_by="t")
    out = PMON.digest(dry_run=True)
    assert "P1 orphan verification" in out and "stale packs" in out
    assert "1/2" in out          # wired 1 of 2


def test_breach_key_stability():
    a = PMON._breach_key("CRITICAL STALE-PACK: AAA|2020-01-01 is 9d past its date with no adjudication")
    b = PMON._breach_key("CRITICAL STALE-PACK: AAA|2020-01-01 is 10d past its date with no adjudication")
    assert a == b                # ageing wording never re-alarms


def test_packs_due_advance_notice(env):
    import datetime as _dt
    import json as _j
    data = env / "desk" / "data"
    tomorrow = (_dt.date.today() + _dt.timedelta(days=1)).isoformat()
    far = (_dt.date.today() + _dt.timedelta(days=30)).isoformat()
    (data / "resolution_packs.json").write_text(_j.dumps({"packs": {
        f"SOON|{tomorrow}": {"tier": "A", "adjudication": "the gate", "branches": {}},
        f"FAR|{far}": {"tier": "B", "adjudication": "later", "branches": {}},
        f"DONE|{tomorrow}": {"tier": "B", "adjudication": "x", "lifecycle": "adjudicated"},
    }}))
    notices = PMON.packs_due()
    assert len(notices) == 1 and "SOON" in notices[0]


def test_due_notice_rate_limited_like_breaches(env, monkeypatch):
    import datetime as _dt
    import json as _j
    data = env / "desk" / "data"
    tomorrow = (_dt.date.today() + _dt.timedelta(days=1)).isoformat()
    (data / "resolution_packs.json").write_text(_j.dumps({"packs": {
        f"SOON|{tomorrow}": {"tier": "A", "adjudication": "gate", "branches": {}}}}))
    monkeypatch.setattr(PMON, "collect_criticals", lambda: [])
    sent = []
    import types, sys as _sys
    fake = types.SimpleNamespace(send_raw=lambda s, b: sent.append(s) or True,
                                 send=lambda *a, **k: True,
                                 event_subject=lambda m, prefix="SignalOS": m)
    monkeypatch.setitem(_sys.modules, "desk.mailer", fake)
    assert len(PMON.immediate_pass()) == 1 and len(sent) == 1
    assert PMON.immediate_pass() == [] and len(sent) == 1     # same pack-key suppressed 24h


# ---------- order_hygiene (NATR postmortem, 2026-08-07) ----------
def test_order_hygiene_flags(tmp_path, monkeypatch):
    import importlib, datetime, time, json
    import desk.order_hygiene as OH
    importlib.reload(OH)
    today = datetime.date.today()
    soon = (today + datetime.timedelta(days=2)).isoformat()
    far = (today + datetime.timedelta(days=40)).isoformat()
    oc = tmp_path / "orders_cache.json"
    oc.write_text(json.dumps({"asof": time.time(), "orders": [
        {"ticker": "AAA", "side": "BUY", "qty": 100, "limit": 10.0, "order_id": "1"},
        {"ticker": "BBB", "side": "SELL", "qty": 50, "limit": 99.0, "order_id": "2"},
        {"ticker": "CCC", "side": "BUY", "qty": 10, "limit": 5.0, "order_id": "3"},
        {"ticker": "DDD", "side": "BUY", "qty": 10, "limit": 5.0, "order_id": "4"},
    ]}))
    st = tmp_path / "state.json"
    st.write_text(json.dumps({"earnings_cache": {
        "AAA": {"next": soon, "fetched": today.isoformat()},
        "BBB": {"next": soon, "fetched": today.isoformat()},
        "CCC": {"next": far, "fetched": today.isoformat()},
        "DDD": {"next": soon, "fetched": today.isoformat()},
    }}))
    rat = tmp_path / "rat.json"
    rat.write_text(json.dumps({"4": {"until": far, "basis": "court-blessed test ride"}}))
    monkeypatch.setattr(OH, "ORDERS_CACHE", oc)
    monkeypatch.setattr(OH, "STATE", st)
    monkeypatch.setattr(OH, "RATIFICATIONS", rat)
    flags = OH.sweep()
    joined = "\n".join(flags)
    assert "CRITICAL PULL-BEFORE-PRINT: AAA" in joined          # buy into print
    assert "TRIM-RIDES-PRINT: BBB" in joined                    # sell into print = notice
    assert "CCC" not in joined                                  # print outside window
    assert "DDD" not in joined                                  # ratified ride skipped
    # empty cache = blind, never silent
    oc.write_text(json.dumps({"asof": time.time(), "orders": []}))
    assert any("ORDER-HYGIENE-BLIND" in f for f in OH.sweep())
