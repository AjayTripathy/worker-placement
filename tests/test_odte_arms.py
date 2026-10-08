"""Prospective factorial arms, shared counterfactuals and prior-only paper learning."""
import datetime as dt
import itertools
import json
from types import SimpleNamespace as NS

import pytest

from desk.odte import arms as A, text_overlay as E, shadow as S, doctrine as D
from desk.odte.render_arms import render
from test_odte import chain
from test_odte_execution import isolation  # noqa: F401

DATE = "2026-10-08"
REGISTER = dt.datetime(2026, 10, 7, 9, tzinfo=E.ET)
ENTRY = REGISTER.replace(day=8, hour=10)


@pytest.fixture
def lab(tmp_path, monkeypatch):
    # Report finalization must use the simulated clock, not the date CI runs.
    monkeypatch.setattr(E, "utcnow", lambda: ENTRY.replace(hour=9))
    monkeypatch.setattr("officekit_ai.models.resolve", lambda *a: ("codex", {}, "fixture-model"))
    source = tmp_path / "text_overlay"
    sm = E.initialize(source, tmp_path, "fixture-office", now=REGISTER, premarket=True, session_date=DATE)
    root = tmp_path / "arm_experiment"
    m = A.initialize(root, start_date=DATE, forecast_root=source, now=REGISTER)
    st = S.load_state(DATE)

    def forecast(stop=.1, severe=.02, issued=None):
        return A.seal(source / "forecasts" / (DATE + ".json"), {
            "protocol": sm["protocol"], "date": DATE, "status": "accepted",
            "issued_at": (issued or ENTRY.replace(hour=9, minute=5)).isoformat(),
            "forecast": {"stop_probability": stop, "severe_probability": severe}, "fixture": True})

    def tick(hour, minute, *, stop=False, missing=False, event=False, now=None):
        stamp = ENTRY.replace(hour=hour, minute=minute)
        rows = [dict(r, iv=.20, live_eligible=not missing) for r in chain()]
        if stop:
            for r in rows:
                if r["strike"] == 672 and r["right"] == "P":
                    r.update(bid=1.45, ask=1.5)
        snap = {"ts": stamp.isoformat(), "rows": rows, "spx": 6800.+minute%2, "xsp": 680.,
                "vix1d": 18., "indices_live": True, "data_type": "live", "greeks": "model"}
        S.step(st, snap, (hour, minute), event)
        A.observe(root, st, snap, {"events": []}, now=now or stamp)
        return snap

    for minute in range(30, 60):
        tick(9, minute)
    return NS(root=root, source=source, sm=sm, m=m, st=st, tick=tick, forecast=forecast)


def decision(lab):
    return A.checked(lab.root / "decisions" / (DATE + ".json"))


def outcome(lab):
    return A.checked(lab.root / "outcomes" / (DATE + ".json"))


def test_registry_is_complete_factorial_and_preserves_baselines(lab):
    combos = {frozenset(a["factors"]) for n, a in lab.m["arms"].items() if n != "CASH"}
    expected = {frozenset(c) for count in range(5) for c in itertools.combinations(A.FACTORS, count)}
    assert combos == expected and len(lab.m["arms"]) == 17
    assert lab.m["arms"]["T3"]["factors"] == []
    assert lab.m["arms"]["T4"]["factors"] == ["news"]
    assert not lab.m["live_enabled"] and not lab.m["promotion_allowed"]
    assert D.LIVE_TEMPLATE == "T3_BLACKOUT"


def test_end_to_end_shared_trade_costs_lineage_and_immutable_selection(lab):
    f = lab.forecast(stop=.8, severe=.2)
    lab.tick(10, 0)
    before = decision(lab)
    assert before["candidate"]["legs"] == lab.st["templates"]["T3_BLACKOUT"]["legs"]
    assert before["forecast"]["id"] == f["id"]
    assert before["arms"]["T3"]["decision"] == "take"
    assert before["arms"]["T4"]["decision"] == "skip"
    assert before["arms"]["T5"]["decision"] == "take"
    assert before["allocation"]["training_sessions"] == 0
    lab.tick(10, 1, stop=True)
    r = outcome(lab)
    assert r["decision_id"] == before["id"] and r["counterfactual"]["gross_pnl_usd"] < 0
    assert r["arms"]["T4"]["net_pnl_usd"] == -1
    assert r["arms"]["CASH"]["net_pnl_usd"] == 0
    assert r["arms"]["T3"]["net_pnl_usd"] == pytest.approx(r["counterfactual"]["gross_pnl_usd"] - 7.2)
    assert r["arms"]["T5"]["net_pnl_usd"] == r["arms"]["T3"]["net_pnl_usd"]
    lab.tick(10, 2)
    assert decision(lab) == before and outcome(lab) == r
    with pytest.raises(ValueError, match="already sealed"):
        A.seal(lab.root / "decisions" / (DATE + ".json"), before)
    report = A.report(lab.root)
    assert report["arms"]["T4"]["vs_t3"]["sessions"] == 1
    assert report["factor_effects"]["news"]["stats"]["sessions"] == 1
    assert report["factor_effects"]["news"]["daily"][0]["paired_combinations"] == 8


@pytest.mark.parametrize("kind", ["missing", "late", "changed_source"])
def test_missing_news_is_unavailable_not_a_cash_win(lab, kind):
    if kind == "late":
        lab.forecast(issued=ENTRY.replace(hour=9, minute=15))
    if kind == "changed_source":
        p = lab.source / "manifest.json"
        m = E.read(p); m["requested_model"] = "changed"; p.write_text(json.dumps(m))
    lab.tick(10, 0); d = decision(lab)
    assert d["arms"]["T4"]["decision"] == "unavailable"
    assert "T4" not in d["allocation"]["probabilities"]
    assert d["arms"]["T3"]["decision"] == "take"
    if kind == "changed_source":
        assert "integrity" in d["forecast_error"]
    if kind == "missing":
        # Even a file arriving later with an earlier claimed time cannot alter entry.
        lab.forecast()
    lab.tick(10, 1, stop=True)
    assert outcome(lab)["arms"]["T4"]["net_pnl_usd"] is None
    assert decision(lab) == d


def test_missing_factor_dominates_another_failed_filter(lab):
    lab.forecast(stop=.8); lab.tick(10, 0)
    d = decision(lab)
    features = {**d["features"], "iv_to_realized_15m": None}
    gates, arms = A.evaluate(features, d["candidate"], d["forecast"], lab.m)
    assert gates["volatility"]["pass"] is None
    assert arms["T12"]["decision"] == "unavailable"
    assert arms["T12"]["missing"] == ["volatility"] and arms["T12"]["failed"] == ["news"]


@pytest.mark.parametrize("kind", ["gap", "stale_leg"])
def test_incomplete_trade_path_never_teaches_cash_to_win(lab, kind):
    lab.forecast(stop=.8); lab.tick(10, 0)
    if kind == "gap":
        lab.tick(10, 3, stop=True)
    else:
        lab.tick(10, 1, missing=True); lab.tick(10, 2, stop=True)
    r = outcome(lab)
    assert r["counterfactual"] is None and r["arms"]["T3"]["net_pnl_usd"] is None
    assert r["arms"]["CASH"]["net_pnl_usd"] == 0
    d = decision(lab)
    selected = A.allocation(lab.m, d["arms"], d["context"], [(d, r)], "2026-10-09")
    assert selected["training_sessions"] == 0
    assert selected["incomplete_sessions"] == 1 and selected["warmup_remaining"] == 20
    assert selected["missing_by_arm"]["T3"] == 1 and selected["missing_by_arm"]["CASH"] == 0


def test_registration_code_freeze_and_backfill_guard(lab, monkeypatch):
    with pytest.raises(ValueError, match="future session"):
        A.initialize(lab.root, start_date=DATE, forecast_root=lab.source, now=ENTRY)
    with pytest.raises(ValueError, match="prospective and current"):
        lab.tick(10, 0, now=ENTRY+dt.timedelta(hours=1))
    monkeypatch.setattr(A, "code_hash", lambda: "changed")
    with pytest.raises(ValueError, match="new experiment"):
        A.protocol(lab.root)


def test_prior_only_history_excludes_late_resolution_and_foreign_protocol(lab):
    lab.forecast(); lab.tick(10, 0); lab.tick(10, 1, stop=True)
    assert A.history(lab.root, lab.m, ENTRY) == []
    assert len(A.history(lab.root, lab.m, ENTRY+dt.timedelta(days=1))) == 1
    d = decision(lab); r = outcome(lab)
    for date, resolved, protocol in [
        ("2026-10-06", ENTRY+dt.timedelta(days=2), lab.m["protocol"]),
        ("2026-10-05", REGISTER, "foreign")]:
        row = {k: v for k, v in r.items() if k != "id"}
        row.update(date=date, protocol=protocol, resolved_at=resolved.isoformat())
        A.seal(lab.root / "outcomes" / (date + ".json"), row)
    assert len(A.history(lab.root, lab.m, ENTRY+dt.timedelta(days=1))) == 1


def test_full_information_learning_uses_pooled_history_and_exploration(lab):
    decisions = {n: {"decision": "take"} for n in lab.m["arms"]}
    ctx = {"volatility": "iv_above_rv", "path": "two_way"}
    past = [( {"context": {"volatility": "iv_below_rv", "path": "directional"}},
             {"id": str(i), "selected_arm": "T3", "arms": {n: {"net_pnl_usd": 40 if n == "T5" else -40}
                                                         for n in lab.m["arms"]}}) for i in range(30)]
    warmup = A.allocation(lab.m, decisions, ctx, past[:19], DATE)
    assert all(v == pytest.approx(1/17) for v in warmup["probabilities"].values())
    result = A.allocation(lab.m, decisions, ctx, past, DATE)
    assert result["status"] == "exploratory_learning" and result["context_blend"] == 0
    assert result["probabilities"]["T5"] > result["probabilities"]["T3"]
    assert min(result["probabilities"].values()) >= .20/17
    assert sum(result["probabilities"].values()) == pytest.approx(1)
    assert result == A.allocation(lab.m, decisions, ctx, past, DATE)
    assert result["training_sessions"] == 30  # all outcomes, even though T5 was never selected


def test_continuation_is_date_bound_and_cannot_replace_pilot(lab):
    continuation = lab.root / "news"
    cm = E.initialize(continuation, lab.root, "fixture-office", now=REGISTER, premarket=True)
    other = lab.root / "other"
    m = A.initialize(other, start_date=DATE, forecast_root=lab.source, continuation_root=continuation, now=REGISTER)
    pilot = lab.forecast()
    for date in (DATE, "2026-10-09"):
        A.seal(continuation / "forecasts" / (date+".json"), {
            "date": date, "protocol": cm["protocol"], "status": "accepted",
            "issued_at": date+"T09:05:00-04:00", "forecast": {"stop_probability": .9, "severe_probability": .2}})
    assert A.forecast_for(m, DATE, ENTRY)["id"] == pilot["id"]
    assert A.forecast_for(m, "2026-10-09", ENTRY+dt.timedelta(days=1))["forecast"]["stop_probability"] == .9


def test_empty_and_populated_directory_escape_source_content(lab):
    empty = A.write_report(lab.root)
    assert "No results yet" in render(empty) and empty["latest_allocation"] is None
    lab.forecast(); lab.tick(10, 0); lab.tick(10, 1, stop=True)
    result = A.write_report(lab.root)
    result["sessions"][0]["error"] = '<script>alert("injection")</script>'
    html = render(result)
    assert '<script>alert' not in html and '&lt;script&gt;' in html
    assert 'Record lineage' in html and 'data-name="T18"' in html
    assert result["selector_stats"]["sessions"] == 1


def test_calendar_blackout_cannot_create_arm_entry(lab):
    lab.forecast(); lab.tick(10, 0, event=True); lab.tick(10, 21, event=True)
    assert not (lab.root / "decisions" / (DATE+".json")).exists()
    assert E.read(lab.root / "sessions" / (DATE+".json"))["status"] == "no_candidate"


def test_missed_first_candidate_cannot_be_backfilled(lab):
    # Simulate collector state restored after the entry while its observer was down.
    snap = {"ts": ENTRY.isoformat(), "rows": [dict(r, live_eligible=True) for r in chain()],
            "spx": 6800., "xsp": 680., "vix1d": 18., "indices_live": True}
    S.step(lab.st, snap, (10, 0), False)
    lab.tick(10, 1)
    assert not (lab.root / "decisions" / (DATE+".json")).exists()
    assert E.read(lab.root / "sessions" / (DATE+".json"))["status"] == "unavailable"


def test_crash_after_sealed_decision_resumes_without_reselection(lab):
    lab.forecast(); lab.tick(10, 0)
    before = decision(lab)
    sp = lab.root / "sessions" / (DATE+".json")
    E.atomic_json(sp, {"date": DATE, "protocol": lab.m["protocol"], "status": "collecting"})
    lab.tick(10, 1, stop=True)
    assert outcome(lab)["counterfactual"] is not None
    assert decision(lab) == before
    state = E.read(sp); state["status"] = "tracking"; E.atomic_json(sp, state)
    lab.tick(10, 2)
    assert E.read(sp)["status"] == "resolved"


def test_collector_disappearance_resolves_as_unknown_once(lab):
    lab.forecast(stop=.8); lab.tick(10, 0)
    A.finalize_missing(lab.root, now=ENTRY.replace(hour=15, minute=45))
    assert not (lab.root / "outcomes" / (DATE+".json")).exists()
    A.finalize_missing(lab.root, now=ENTRY.replace(hour=16, minute=20))
    r = outcome(lab)
    assert r["counterfactual"] is None and r["arms"]["T3"]["net_pnl_usd"] is None
    assert r["arms"]["T4"]["net_pnl_usd"] == -1
    A.finalize_missing(lab.root, now=ENTRY+dt.timedelta(days=1))
    assert outcome(lab) == r and A.report(lab.root)["unresolved_sessions"] == 1


def test_duplicate_snapshot_idempotent_but_conflicting_snapshot_rejected(lab):
    lab.forecast(); snap = lab.tick(10, 0)
    d = decision(lab)
    A.observe(lab.root, lab.st, snap, {}, now=ENTRY)
    assert decision(lab) == d
    snap["spx"] += 1
    with pytest.raises(ValueError, match="Conflicting snapshot"):
        A.observe(lab.root, lab.st, snap, {}, now=ENTRY)


def test_observer_runs_before_broker_management_and_error_is_persisted(lab, monkeypatch):
    # 2026-10-08 live policy: the live rail mirrors the arm decision the observer seals from the
    # same snapshot, so research observation runs FIRST; its failure still never blocks management.
    from desk.odte import runner as R
    from test_odte_execution import Broker, session
    events = []
    monkeypatch.setattr(R.Session, "_live_tick", lambda *a: events.append("managed"))
    def broken(*a, **kw):
        events.append("research"); raise ValueError("fixture unavailable")
    monkeypatch.setattr(A, "observe", broken)
    runner = session(Broker())
    runner.tick(ENTRY)
    assert events == ["research", "managed"]
    assert "fixture unavailable" in runner.st["arm_experiment_error"]
