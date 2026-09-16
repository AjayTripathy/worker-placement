"""Tests for the auto-court conveyor: queue semantics, runner validators, stage routing."""
import json

import pytest

from desk import court_queue as CQ
from desk import court_runner as CR
from desk.store import Store


@pytest.fixture
def env(tmp_path, monkeypatch):
    data = tmp_path / "desk" / "data"
    data.mkdir(parents=True)
    monkeypatch.setattr(CQ, "ROOT", tmp_path)
    monkeypatch.setattr(CQ, "QUEUE", Store(data / "court_queue.json",
                                           list_path="items", key=lambda r: r["ticker"]))
    (data / "research_ledger.json").write_text(json.dumps(
        {"names": [{"ticker": "HELD.L"}]}))
    # 2026-09-10: the runner's evidence/atlas/backfill paths read AND WRITE the live repo
    # (facilities/X_T.json, filing_watch.json, issuer_sic_cache.json ...) and hit yfinance —
    # stub them so the suite is hermetic.
    monkeypatch.setattr(CR, "_evidence", lambda t: f"## EVIDENCE PACK — {t}\n")
    monkeypatch.setattr(CR, "_atlas", lambda t, ctx: "")
    monkeypatch.setattr(CR, "_manifest", lambda: "VERIFICATION TOOLKIT (stub)")
    monkeypatch.setattr(CR, "_reject_feedback", lambda item, stage: "")
    import desk.deck_writer as DW
    import desk.queue_hygiene as QH
    monkeypatch.setattr(DW, "backfill", lambda limit=1, dry_run=False: [])
    monkeypatch.setattr(QH, "run_hygiene", lambda verbose=False: {"evicted": [], "flagged": []})
    return tmp_path


def test_enqueue_skips_ledger_and_dupes(env):
    rows = [{"sym": "NEW.L", "score": 0.7}, {"sym": "HELD.L"}, {"sym": "NEW.L"}]
    c = CQ.enqueue_candidates([{**r, "ticker": r["sym"]} for r in rows], source="t")
    assert c["added"] == 1
    c2 = CQ.enqueue_candidates([{"ticker": "NEW.L"}], source="t")   # idempotent re-run
    assert c2["added"] == 0
    (item,) = CQ.pending("TRAP_VERIFY")
    assert item["ticker"] == "NEW.L" and item["screen_row"]["score"] == 0.7


def test_advance_records_history(env):
    CQ.enqueue_candidates([{"ticker": "A.T"}], source="t")
    CQ.advance("A.T", "COURT_RED", artifact="/tmp/x.md")
    (item,) = CQ.pending("COURT_RED")
    assert item["history"][0]["from"] == "TRAP_VERIFY"
    assert item["history"][0]["artifact"] == "/tmp/x.md"
    with pytest.raises(ValueError):
        CQ.advance("A.T", "NOT_A_STAGE")
    with pytest.raises(KeyError):
        CQ.advance("GHOST", "COURT_RED")


def test_stuck_item_flags_critical(env):
    CQ.enqueue_candidates([{"ticker": "OLD.T"}], source="t")
    items = CQ.QUEUE.rows()
    items[0]["enqueued_utc"] = "2020-01-01T00:00:00Z"
    CQ.QUEUE.upsert(items, generated_by="t")
    flags = []
    CQ.check_queue_health(flags)
    assert len(flags) == 1 and flags[0].startswith("CRITICAL COURT-QUEUE-STUCK")


def test_terminal_stages_not_pending(env):
    CQ.enqueue_candidates([{"ticker": "A.T"}, {"ticker": "B.T"}], source="t")
    CQ.advance("A.T", "KILLED", note="trap")
    assert [i["ticker"] for i in CQ.pending()] == ["B.T"]


# ---------- runner validators + routing (no dispatch) ----------
GOOD_VERIFY = ("### X.T (widgets) — screen 3x — **PERPETUAL-TRAP**\n" + "detail " * 80 +
               "\nKILL: {claim | tool | https://example.com/a | REFUTED}\nRESOLVES ON: x\nDisposition: AVOID")
GOOD_VERIFY_REAL = GOOD_VERIFY.replace("PERPETUAL-TRAP", "REAL CANDIDATE")
GOOD_RED = ("## RED BENCH — X.T — RECOMMEND: REJECT\n" + "1. {a | b | c | REFUTED} FATAL KILL-CLASS: NOVEL\n" * 3 +
            "x " * 200 + "https://example.com STRONGEST SINGLE KILL: y\nWHAT WOULD CHANGE MY MIND: z\n"
            "PRINT PROXIMITY: NONE — next report unverified\nPACK: acknowledged\n"
            "## DETECTORS CONSULTED\n- rpo_drift — NOT-FIRED")
GOOD_BLUE = ("## BLUE BENCH — X.T — RED CASE: PARTIALLY OVERTURNED\n" + "1. ruling\n" * 3 +
             "x " * 200 + "https://example.com NET POSITION AFTER BOTH BENCHES: hold small\nPACK: acknowledged\n"
             "## DETECTORS CONSULTED\n- rpo_drift — NOT-FIRED")


def test_validators():
    assert CR._validate("TRAP_VERIFY", GOOD_VERIFY) is None
    assert CR._validate("TRAP_VERIFY", "too short") is not None
    assert CR._validate("TRAP_VERIFY", ("no verdict here " * 50) + "https://x.com") is not None
    assert CR._validate("COURT_RED", GOOD_RED) is None
    assert CR._validate("COURT_RED", GOOD_BLUE) is not None          # wrong bench header
    assert CR._validate("COURT_BLUE", GOOD_BLUE) is None
    no_cite = GOOD_RED.replace("https://example.com", "")
    assert CR._validate("COURT_RED", no_cite) == "no primary citation (http) anywhere in the output"


def test_verify_routing():
    assert CR._next_stage_after_verify(GOOD_VERIFY) == "KILLED"       # traps never reach court
    assert CR._next_stage_after_verify(GOOD_VERIFY_REAL) == "COURT_RED"
    assert CR._next_stage_after_verify(GOOD_VERIFY.replace("PERPETUAL-TRAP", "BORDERLINE")) == "COURT_RED"


def test_render_stages(env, monkeypatch):
    CQ.enqueue_candidates([{"ticker": "X.T", "score": 0.9}], source="t")
    monkeypatch.setattr(CR, "CQ", CQ)
    (item,) = CQ.pending("TRAP_VERIFY")
    p, model = CR._render("TRAP_VERIFY", item)
    assert "X.T" in p and "{TICKER}" not in p and "governance bloc" in p    # JP catalog for .T
    assert model == CR.MODEL_VOLUME
    # court stages use the court tier and embed the manifest
    item["history"] = []
    p2, model2 = CR._render("COURT_RED", item)
    assert model2 == CR.MODEL_COURT and "VERIFICATION TOOLKIT" in p2


def test_drain_dry_run_dispatches_nothing(env, monkeypatch):
    CQ.enqueue_candidates([{"ticker": "X.T"}], source="t")
    monkeypatch.setattr(CR, "CQ", CQ)
    monkeypatch.setattr(CR, "OUT_DIR", env / "desk" / "data" / "court_artifacts")
    called = []
    monkeypatch.setattr(CR, "_dispatch", lambda *a, **k: called.append(1) or {"text": ""})
    log = CR.drain(dry_run=True)
    assert called == [] and any("DRY X.T" in l for l in log)
    assert CQ.pending("TRAP_VERIFY")                                  # nothing advanced


def test_drain_auth_failure_aborts(env, monkeypatch):
    CQ.enqueue_candidates([{"ticker": "X.T"}, {"ticker": "Y.T"}], source="t")
    monkeypatch.setattr(CR, "CQ", CQ)
    monkeypatch.setattr(CR, "OUT_DIR", env / "desk" / "data" / "court_artifacts")
    calls = []
    monkeypatch.setattr(CR, "_dispatch", lambda *a, **k: calls.append(1) or {"error": "not-logged-in"})
    log = CR.drain()
    assert len(calls) == 1 and any("INFRA FAILURE" in l for l in log)   # one probe, then abort (log line renamed AUTH->INFRA)


def test_drain_happy_path_advances(env, monkeypatch):
    CQ.enqueue_candidates([{"ticker": "X.T"}], source="t")
    monkeypatch.setattr(CR, "CQ", CQ)
    monkeypatch.setattr(CR, "OUT_DIR", env / "desk" / "data" / "court_artifacts")
    monkeypatch.setattr(CR, "_dispatch", lambda *a, **k: {"text": GOOD_VERIFY_REAL})
    log = CR.drain()
    (item,) = CQ.pending("COURT_RED")
    assert item["ticker"] == "X.T"
    assert item["history"][0]["artifact"] and "TRAP_VERIFY" in item["history"][0]["artifact"]


def test_drain_validator_rejection_does_not_advance(env, monkeypatch):
    CQ.enqueue_candidates([{"ticker": "X.T"}], source="t")
    monkeypatch.setattr(CR, "CQ", CQ)
    monkeypatch.setattr(CR, "OUT_DIR", env / "desk" / "data" / "court_artifacts")
    monkeypatch.setattr(CR, "_dispatch", lambda *a, **k: {"text": "garbage " * 100})
    log = CR.drain()
    assert any("VALIDATOR REJECTED" in l for l in log)
    assert CQ.pending("TRAP_VERIFY")                                  # stayed put


def test_fair_carry_advances_to_court():
    fair = GOOD_VERIFY.replace("PERPETUAL-TRAP", "FAIR-CARRY")
    assert CR._next_stage_after_verify(fair) == "COURT_RED"
    assert CR._validate("TRAP_VERIFY", fair) is None


# ---------- automated 6/10 court-worthiness gate (2026-08-07) ----------
def test_route_refutability_gate():
    from desk.court_runner import _route_refutability
    t = ("triage table here http://x\nCOURT-WORTHINESS FLUT: 7/10 — funding moat intact\n"
         "COURT-WORTHINESS DKNG: 5/10 — borderline\nCOURT-WORTHINESS SRAD: 2/10 — structural")
    assert _route_refutability(t, "FLUT") == "COURT_RED"
    assert _route_refutability(t, "DKNG") == "ADJUDICATE"
    assert _route_refutability(t, "SRAD") == "KILLED"
    # ticker not scored in a scored doc -> best-member routing (cohort triage)
    assert _route_refutability(t, "GENI") == "COURT_RED"
    # legacy output with no scores anywhere -> session routes, never silent kill
    assert _route_refutability("old-style triage, no scores http://x", "FLUT") == "ADJUDICATE"


def test_validator_requires_court_worthiness_on_refutability():
    from desk.court_runner import _validate
    base = ("context line http://example.com/10q " + "x" * 400 +
            "\n| FLUT | DAMAGE-ABSENT | rev | +10% | 2026-11-12 | ok |")
    assert _validate("REFUTABILITY", base) is not None          # no score line -> rejected
    assert _validate("REFUTABILITY", base + "\nCOURT-WORTHINESS FLUT: 6/10 — x") is not None  # v3: still missing PRINT PROXIMITY
    assert _validate("REFUTABILITY", base + "\nCOURT-WORTHINESS FLUT: 6/10 — x\nPRINT PROXIMITY: 2026-11-12 (8-K)") is None
