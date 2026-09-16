"""S4 invariant tests — each invariant exercised against synthetic stores (no live data)."""
import json

import pytest

from desk import pipeline_invariants as PI


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Redirect every store path the invariants read to a temp sandbox."""
    data = tmp_path / "desk" / "data"
    ec = data / "edge_classifications"
    dd = tmp_path / "dd_reports"
    for p in (data, ec, dd):
        p.mkdir(parents=True)
    monkeypatch.setattr(PI, "ROOT", tmp_path)
    monkeypatch.setattr(PI, "DATA", data)
    monkeypatch.setattr(PI, "EC_DIR", ec)
    monkeypatch.setattr(PI, "UNWIRED_QUEUE", data / "unwired_tripwires.json")
    return tmp_path


def _write(env, rel, payload):
    p = env / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload))


# ---------- I1 ----------
def test_promoted_watch_without_pack_fires(env):
    _write(env, "desk/data/research_ledger.json", {"names": [
        {"ticker": "AAA", "verdict": "WATCH", "source": "x-trap-batch9 (2026-08-01)"},
        {"ticker": "BBB", "verdict": "WATCH", "source": None},                    # passive: exempt
        {"ticker": "CCC", "verdict": "HELD", "source": "trap-batch9"},            # not WATCH: exempt
    ]})
    _write(env, "desk/data/resolution_packs.json", {"packs": {}})
    flags = []
    PI.check_watch_has_future_pack(flags)
    crit = [f for f in flags if f.startswith("CRITICAL")]
    assert len(crit) == 1 and "AAA" in crit[0]


def test_promoted_watch_with_future_pack_clean(env):
    _write(env, "desk/data/research_ledger.json", {"names": [
        {"ticker": "AAA.L", "verdict": "WATCH", "source": "trap-batch9"}]})
    _write(env, "desk/data/resolution_packs.json",
           {"packs": {"AAA.L-REVIEW|2099-01-01": {"tier": "B"}}})
    flags = []
    PI.check_watch_has_future_pack(flags)
    assert not [f for f in flags if "AAA" in f]


def test_past_dated_pack_does_not_satisfy_i1(env):
    _write(env, "desk/data/research_ledger.json", {"names": [
        {"ticker": "AAA", "verdict": "WATCH", "source": "trap-batch9"}]})
    _write(env, "desk/data/resolution_packs.json",
           {"packs": {"AAA|2020-01-01": {"tier": "B"}}})
    flags = []
    PI.check_watch_has_future_pack(flags)
    assert any("AAA" in f and f.startswith("CRITICAL") for f in flags)


def test_tail_aggregates_not_percritical(env):
    names = [{"ticker": f"T{i}", "verdict": "WATCH", "source": "hnw-shovels-screen"} for i in range(20)]
    _write(env, "desk/data/research_ledger.json", {"names": names})
    _write(env, "desk/data/resolution_packs.json", {"packs": {}})
    flags = []
    PI.check_watch_has_future_pack(flags)
    assert not [f for f in flags if f.startswith("CRITICAL")]        # screen-tail: not strict
    assert any("BACKLOG: 20" in f for f in flags)
    q = json.loads((env / "desk/data/unwired_tripwires.json").read_text())
    assert len(q["tail"]) == 20


# ---------- I2 ----------
def test_held_without_classification_fires(env):
    _write(env, "desk/ui/data/positions_cache.json", {"positions": [
        {"symbol": "XYZ", "sec_type": "STK", "qty": 10},
        {"symbol": "SGOV", "sec_type": "STK", "qty": 10},       # waiver
        {"symbol": "OPT1", "sec_type": "OPT", "qty": -1},       # not STK
    ]})
    flags = []
    PI.check_held_classified(flags)
    assert len(flags) == 1 and "XYZ" in flags[0] and flags[0].startswith("CRITICAL")


def test_held_with_empty_edge_file_flags_softly(env):
    _write(env, "desk/ui/data/positions_cache.json", {"positions": [
        {"symbol": "XYZ", "sec_type": "STK", "qty": 10}]})
    _write(env, "desk/data/edge_classifications/XYZ.json", {"ticker": "XYZ", "note": "no class"})
    flags = []
    PI.check_held_classified(flags)
    assert len(flags) == 1 and not flags[0].startswith("CRITICAL")


def test_held_classified_clean(env):
    _write(env, "desk/ui/data/positions_cache.json", {"positions": [
        {"symbol": "XYZ", "sec_type": "STK", "qty": 10}]})
    _write(env, "desk/data/edge_classifications/XYZ.json", {"edge_explainer": {"we_believe": "x"}})
    flags = []
    PI.check_held_classified(flags)
    assert flags == []


# ---------- I3 ----------
def test_stale_pack_fires_without_ledger_resolution(env):
    _write(env, "desk/data/resolution_packs.json",
           {"packs": {"AAA|2020-01-01": {"tier": "B"}}})
    flags = []
    PI.check_stale_packs(flags)
    assert any("AAA|2020-01-01" in f for f in flags)


def test_stale_pack_cleared_by_calibration_resolution(env):
    _write(env, "desk/data/resolution_packs.json",
           {"packs": {"AAA-REVIEW|2020-01-03": {"tier": "B"}}})
    (env / "desk/data/calibration_ledger.jsonl").write_text(
        json.dumps({"ticker": "AAA", "cat_date": "2020-01-01", "status": "RESOLVED"}) + "\n")
    flags = []
    PI.check_stale_packs(flags)
    assert not [f for f in flags if "AAA" in f]      # fam+near-date match clears it


def test_stale_pack_cleared_by_lifecycle_field(env):
    _write(env, "desk/data/resolution_packs.json",
           {"packs": {"AAA|2020-01-01": {"tier": "B", "lifecycle": "adjudicated"}}})
    flags = []
    PI.check_stale_packs(flags)
    assert flags == []


# ---------- I4 ----------
def test_batch_verdict_missing_from_ledger_fires(env):
    _write(env, "desk/data/research_ledger.json", {"names": [{"ticker": "AAA.L"}]})
    doc = env / "verticals/deep_value/global/data/X_TRAP_BATCH9.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("## Name One (AAA.L, GB) — screen — **REAL**\n\n"
                   "## Name Two (BBB.HE, FI) — screen — **AVOID**\n")
    flags = []
    PI.check_batch_docs_in_ledger(flags)
    assert len(flags) == 1 and "BBB.HE" in flags[0]


# ---------- I5 ----------
def test_defect_aging(env):
    from desk.store import append_jsonl
    append_jsonl(env / "desk/data/screen_defects.jsonl",
                 {"date": "2020-01-01", "screen": "s", "defect": "old defect text here",
                  "fix_direction": "fix it", "status": "open"}, generated_by="t")
    append_jsonl(env / "desk/data/screen_defects.jsonl",
                 {"date": "2020-01-01", "screen": "s", "defect": "closed defect",
                  "fix_direction": "done", "status": "fix_verified_e2e",
                  "e2e_verified": {"run_date": "2020-01-02", "assertions": ["x"]}},
                 generated_by="t")
    flags = []
    PI.check_defect_ledger_aging(flags)
    assert len(flags) == 1 and "OPEN >30d" in flags[0]


def test_fix_landed_without_e2e_is_critical(env):
    from desk.store import append_jsonl
    append_jsonl(env / "desk/data/screen_defects.jsonl",
                 {"date": "2099-01-01", "screen": "s", "defect": "guard added but never re-run",
                  "fix_direction": "done", "status": "fix_landed"}, generated_by="t")
    flags = []
    PI.check_defect_ledger_aging(flags)
    assert len(flags) == 1 and flags[0].startswith("CRITICAL FIX-NOT-E2E-VERIFIED")


def test_fix_landed_cleared_by_superseding_stamp(env):
    from desk.store import append_jsonl
    append_jsonl(env / "desk/data/screen_defects.jsonl",
                 {"date": "2099-01-01", "screen": "s", "defect": "guard added but never re-run",
                  "fix_direction": "done", "status": "fix_landed"}, generated_by="t")
    append_jsonl(env / "desk/data/screen_defects.jsonl",
                 {"date": "2099-01-02", "screen": "s", "defect": "E2E VERIFIED: guard added",
                  "supersedes": "guard added but never re-run",
                  "fix_direction": "verified", "status": "fix_verified_e2e",
                  "e2e_verified": {"run_date": "2099-01-02", "assertions": ["caught name ok"]}},
                 generated_by="t")
    flags = []
    PI.check_defect_ledger_aging(flags)
    assert flags == []


# ---------- I6 ----------
def test_court_without_pitch_doc_fires_after_epoch(env):
    _write(env, "desk/data/edge_classifications/NEW.json",
           {"ticker": "NEW", "court": "full court", "date": "2099-01-01"})
    _write(env, "desk/data/edge_classifications/OLD.json",
           {"ticker": "OLD", "court": "full court", "date": "2026-01-01"})   # pre-epoch: exempt
    flags = []
    PI.check_court_has_pitch_doc(flags)
    crit = [f for f in flags if f.startswith("CRITICAL")]
    assert len(crit) == 1 and "NEW" in crit[0]


def test_court_with_pitch_doc_clean(env):
    _write(env, "desk/data/edge_classifications/NEW.json",
           {"ticker": "NEW", "court": "full court", "date": "2099-01-01"})
    (env / "dd_reports" / "pitch_NEW_2099-01-01.md").write_text("# pitch")
    flags = []
    PI.check_court_has_pitch_doc(flags)
    assert flags == []


# ---------- I7 ----------
def test_unswept_staging_plan_fires(env):
    _write(env, "desk/data/staging_plan.json", {"actions": [
        {"action": "create", "ticker": "AAA", "side": "BUY", "qty": 1, "limit": 1.0,
         "ccy": "USD", "provenance": {"court_date": "2026-01-01", "source": "t"},
         "status": "planned", "planned_utc": "2020-01-01T00:00:00Z"},
        {"action": "create", "ticker": "BBB", "side": "BUY", "qty": 1, "limit": 1.0,
         "ccy": "USD", "provenance": {"court_date": "2026-01-01", "source": "t"},
         "status": "executed", "planned_utc": "2020-01-01T00:00:00Z"},
    ]})
    flags = []
    PI.check_staging_plan_executed(flags)
    assert len(flags) == 1 and "AAA" in flags[0]


def test_run_all_never_raises(env):
    # empty sandbox: every store missing — the suite must degrade to flags, not exceptions
    flags = PI.run_all()
    assert isinstance(flags, list)
