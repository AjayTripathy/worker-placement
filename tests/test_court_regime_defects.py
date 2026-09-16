"""Regression suite for the 2026-09-08..10 defects — every one of these shipped a wrong output
that LOOKED right (a deck stamped ADJUDICATED, benches arguing the wrong brief, a harvest number
2.5x too high, a brief that silently died for 7 weeks, a grade against '(gate not recorded)').
Each test is the invariant that would have caught it. No LLM, no network, no live data.
"""
import datetime
import json
import sqlite3

import pytest

from desk import court_queue as CQ
from desk import court_runner as CR
from desk import deck_writer as DW
from desk import grade_brief as GB
from desk import harvest_ledger as HL
from desk import pipeline_monitor as PM
from desk.store import Store


# ---------------------------------------------------------------- fixtures
@pytest.fixture
def env(tmp_path, monkeypatch):
    data = tmp_path / "desk" / "data"
    (data / "court_artifacts").mkdir(parents=True)
    monkeypatch.setattr(CQ, "ROOT", tmp_path)
    monkeypatch.setattr(CQ, "QUEUE", Store(data / "court_queue.json",
                                           list_path="items", key=lambda r: r["ticker"]))
    (data / "research_ledger.json").write_text(json.dumps({"names": [{"ticker": "HELD"}]}))
    # runner stubs: no evidence pack, no atlas, no dispatch
    monkeypatch.setattr(CR, "_evidence", lambda t: f"## EVIDENCE PACK — {t}\n")
    monkeypatch.setattr(CR, "_atlas", lambda t, ctx: "")
    monkeypatch.setattr(CR, "_manifest", lambda: "")
    monkeypatch.setattr(CR, "_reject_feedback", lambda item, stage: "")
    monkeypatch.setattr(CR, "OUT_DIR", data / "court_artifacts")
    return tmp_path


REGIME_ROW = {"ticker": "MNDY", "thesis": "duration bucket mis-sort", "kill": "Nov guide-down",
              "context": "THESIS: contractual enterprise subs have no channel to an oil shock."}


# ------------------------------------------------- 1. thesis source recognition
def test_generator_thesis_source_is_thesis_sourced():
    assert CQ.is_thesis_sourced("thesis:regime_drawdown_20260910")
    assert CQ.is_thesis_sourced("principal_directive")
    assert not CQ.is_thesis_sourced("dual_class_screen/extremes")


# ------------------------------------------------- 2. reused terminal row litigates the NEW thesis
def test_reused_row_renders_new_thesis_not_old_brief(env, monkeypatch):
    CQ.enqueue_candidates([{"ticker": "MNDY", "score": 1}], source="agentic_saas_screen")
    CQ.advance("MNDY", "COURT_RED", artifact=None)
    # simulate the OLD court: a TRAP_VERIFY artifact exists from the August thesis
    monkeypatch.setattr(CR, "_artifact_text",
                        lambda item, st: "OLD AUGUST BRIEF: damage-absent dislocation" if st == "TRAP_VERIFY" else None)
    # re-stage under the regime thesis, context attached (what the desk did on 9/10)
    (it,) = CQ.pending("COURT_RED")
    it["source"] = "thesis:regime_drawdown_20260910"; it["context"] = REGIME_ROW["context"]
    CQ.QUEUE.upsert([it], generated_by="t")
    (it,) = CQ.pending("COURT_RED")
    prompt, _ = CR._render("COURT_RED", it)
    assert "THESIS UNDER COURT (current)" in prompt
    assert REGIME_ROW["context"] in prompt
    # the old brief may appear only as evidence, and AFTER the current thesis
    assert prompt.find("THESIS UNDER COURT") < prompt.find("OLD AUGUST BRIEF")
    assert "do not re-litigate" in prompt


def test_screen_sourced_row_keeps_screen_brief(env, monkeypatch):
    CQ.enqueue_candidates([{"ticker": "NEWCO", "score": 1, "context": "screen context"}], source="dual_class_screen")
    CQ.advance("NEWCO", "COURT_RED")
    monkeypatch.setattr(CR, "_artifact_text", lambda item, st: "TRAP VERIFY BRIEF" if st == "TRAP_VERIFY" else None)
    (it,) = CQ.pending("COURT_RED")
    prompt, _ = CR._render("COURT_RED", it)
    assert "TRAP VERIFY BRIEF" in prompt and "THESIS UNDER COURT" not in prompt


# ------------------------------------------------- 3. drain(only=) is not starved by the backlog
def test_drain_only_filter_dispatches_just_those_tickers(env, monkeypatch):
    CQ.enqueue_candidates([{"ticker": "SOFI"}, {"ticker": "MNDY"}, {"ticker": "HUBS"}],
                          source="thesis:x", stage="COURT_RED")
    seen = []
    def fake_dispatch(prompt, model):
        seen.append(prompt.split("EVIDENCE PACK — ")[1].split("\n")[0])
        return {"error": "stub"}          # logged + skipped; no artifact written
    monkeypatch.setattr(CR, "_dispatch", fake_dispatch)
    monkeypatch.setattr(CR, "_artifact_text", lambda item, st: None)
    import desk.queue_hygiene as QH
    monkeypatch.setattr(QH, "run_hygiene", lambda verbose=False: {"evicted": [], "flagged": []})
    monkeypatch.setattr(DW, "backfill", lambda limit=1, dry_run=False: [])   # arrears deck work reads the REAL repo — keep it out of the test
    CR.drain(max_dispatch=9, only={"MNDY", "HUBS"})
    assert sorted(seen) == ["HUBS", "MNDY"]


# ------------------------------------------------- 4. deck header: prior court cannot stamp a new court
def _touch_bench(root, t, stamp):
    (root / "desk" / "data" / "court_artifacts" / f"{t}_COURT_BLUE_{stamp}.md").write_text("x")


def test_prior_classification_is_not_current(tmp_path):
    (tmp_path / "desk" / "data" / "court_artifacts").mkdir(parents=True)
    _touch_bench(tmp_path, "CTSH", "202609101713")
    assert not DW.classification_is_current("CTSH", {"date": "2026-08-11", "recommendation": "OWNABLE"}, tmp_path)
    assert not DW.classification_is_current("CTSH", {"date": None, "recommendation": "OWNABLE"}, tmp_path)   # undated = CTSH's case
    assert DW.classification_is_current("CTSH", {"date": "2026-09-10", "recommendation": "WATCH"}, tmp_path)
    assert DW.classification_is_current("CTSH", {"date": "2026-09-11"}, tmp_path)


def test_no_bench_artifacts_dated_classification_is_current(tmp_path):
    (tmp_path / "desk" / "data" / "court_artifacts").mkdir(parents=True)
    assert DW.classification_is_current("XYZ", {"date": "2026-01-01"}, tmp_path)
    assert not DW.classification_is_current("XYZ", {}, tmp_path)


# ------------------------------------------------- 5. grade_brief reads the bar wherever it lives
def test_grade_brief_reads_claim_field():
    row = {"ticker": "SPCX-SUBS", "cat_date": "2026-08-05", "our_p": 0.55, "claim": "subs >= 12.8M"}
    txt = GB.brief(row)
    assert "subs >= 12.8M" in txt and "(gate not recorded)" not in txt
    assert "(gate not recorded)" in GB.brief({"ticker": "X", "cat_date": "2026-08-05", "our_p": 0.5})


# ------------------------------------------------- 6. morning brief must ship (silence != health)
def test_brief_dead_flags():
    today = datetime.date(2026, 9, 9)
    ok = "SIGNALOS — ON DECK for Wednesday 2026-09-09\n...\n"
    assert PM.brief_dead_flags(ok, today) == []
    stale = "SIGNALOS — ON DECK for Tuesday 2026-07-21\n...\n" + "Traceback (most recent call last):\n" * 36
    flags = PM.brief_dead_flags(stale, today)
    assert len(flags) == 1 and flags[0].startswith("CRITICAL BRIEF-DEAD") and "Traceback" in flags[0]
    # header present today but the run crashed AFTER it -> still dead
    crashed_after = ok + "Traceback (most recent call last):\nTypeError: '<' not supported\n"
    assert PM.brief_dead_flags(crashed_after, today)
    assert PM.brief_dead_flags("", today)[0].startswith("CRITICAL BRIEF-DEAD")


def test_morning_brief_overdue_sort_does_not_compare_dicts():
    # the exact shape that crashed 07-22..09-08: equal dates, dict payloads
    d = datetime.date(2026, 8, 5)
    rows = [(d, {"ticker": "A"}), (d, {"ticker": "B"})]
    with pytest.raises(TypeError):
        sorted(rows)                                   # the old code
    assert [r[1]["ticker"] for r in sorted(rows, key=lambda x: x[0])] == ["A", "B"]   # the fix


# ------------------------------------------------- 7. harvest ledger dedupes overlapping extracts
def test_parametric_realized_dedupes_overlapping_daily_extracts(tmp_path):
    db = tmp_path / "msprime.db"
    con = sqlite3.connect(db)
    con.execute("create table gainloss (taxlot_id text, date_closed text, quantity real, cusip text, "
                "issue_gainloss real, source_file text)")
    lot = ("L1", "2026-07-06", 100, "C1", -1000.0)
    for f in ("06Jul", "14Jul", "21Jul", "28Jul", "31Jul"):      # same lot in five overlapping windows
        con.execute("insert into gainloss values (?,?,?,?,?,?)", lot + (f,))
    con.execute("insert into gainloss values ('L2','2026-08-16',10,'C2',250.0,'16Aug')")
    con.execute("insert into gainloss values ('L3','2025-12-01',10,'C3',-9999.0,'old')")   # prior year excluded
    con.commit(); con.close()
    assert HL.parametric_realized(db=str(db)) == pytest.approx(750.0)     # -1000 + 250, counted ONCE


# ------------------------------------------------- 8. thesis-sourced enqueue routes to the red bench
def test_thesis_enqueue_routes_to_court_red_and_allows_ledger_names(env):
    c = CQ.enqueue_candidates([{"ticker": "HELD", "context": "regime"}], source="thesis:regime", allow_ledger=True)
    assert c["added"] == 1
    (it,) = CQ.pending("COURT_RED")
    assert it["ticker"] == "HELD"
