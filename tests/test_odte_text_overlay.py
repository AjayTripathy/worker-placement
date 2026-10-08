"""Prospective research lifecycle, no broker sockets or model/network calls."""
import copy
import datetime as dt
import json
import math
from types import SimpleNamespace as NS

import pytest

from desk.odte import text_overlay as E, forecast_worker as W, shadow as S, doctrine as D, grader as G, volatility as V
from officekit_ai.intelligence import Response, Text, Usage
from test_odte import chain
from test_odte_execution import isolation  # noqa: F401

DATE = "2026-10-08"
START = dt.datetime(2026, 10, 8, 9, 0, tzinfo=E.ET)


@pytest.fixture
def lab(tmp_path, monkeypatch):
    monkeypatch.setattr("officekit_ai.models.resolve", lambda *a: ("codex", {"reasoning_effort": "medium"}, "test-model"))
    root = tmp_path / "text_overlay"
    m = E.initialize(root, tmp_path, "office-test", now=START)
    st = S.load_state(DATE)
    clock = [START]
    def tick(hour, minute, *, rows=None, **updates):
        now = START.replace(hour=hour, minute=minute)
        snap = {"ts": now.isoformat(), "rows": rows or [dict(r, iv=.20, live_eligible=True) for r in chain()],
                "spx": 6800., "xsp": 680., "vix1d": 18., "indices_live": True,
                "data_type": "live", "greeks": "model", **updates}
        S.step(st, snap, (hour, minute), False)
        E.observe(root, st, snap, {"events": [], "verified_through": "2026-12-31"}, now=now)
        clock[0] = now
        return snap
    tick(9, 31); tick(9, 50)
    sources = []
    for url in m["sources"][:2]:
        src = {"feed": url, "url": url, "text": "An auction is scheduled for 13:00 ET. Market response is uncertain.",
               "published_at": START.replace(hour=9, minute=30).isoformat(),
               "fetched_at": START.replace(hour=9, minute=51).isoformat(), "visibility": "public_feed_excerpt"}
        src["id"] = E.digest(src); sources.append(src)
    out = {"stop_probability": .8, "severe_probability": .2, "incremental_information": "Conditional event interaction, uncertain.",
           "gaps": ["No direct flow observations"], "reasons": [{"source_id": sources[0]["id"],
           "quote": "An auction is scheduled for 13:00 ET.", "mechanism": "The event occurs within the holding window.",
           "falsifier": "Observed volatility does not increase after the auction.",
           "event_type": "auction", "novelty": "scheduled", "timing": "holding_window",
           "channel": "rates", "expected_volatility": "up"}]}
    class Client:
        calls = 0
        def complete(self, request):
            self.calls += 1
            assert request.model == "test-model" and request.schema is not None
            assert "untrusted data" in request.system
            return Response([Text(json.dumps(out))], "test-model-v1", usage=Usage(100, 50))
    client = Client()
    def forecast():
        clock[0] = START.replace(hour=9, minute=52)
        return W.run_job(root, DATE, client=client, collector=lambda _: (sources, []), clock=lambda: clock[0])
    return NS(root=root, m=m, st=st, tick=tick, forecast=forecast, sources=sources, out=out, client=client, clock=clock)


def stopped(lab):
    lab.tick(10, 0)
    rows = [dict(r, iv=.20, live_eligible=True) for r in chain()]
    for row in rows:
        if row["right"] == "P" and row["strike"] == 672:
            row.update(bid=1.45, ask=1.5)
    lab.tick(10, 1, rows=rows)
    return E.read(lab.root / "sessions" / (DATE + ".json"))


def test_end_to_end_skip_still_resolves_brier_and_net_lift(lab):
    f = lab.forecast()
    assert f["status"] == "accepted" and f["usage"]["input_tokens"] == 100
    row = stopped(lab)
    assert row["status"] == "resolved" and not row["text_trade"]
    assert row["outcome"]["stop"] == 1 and row["outcome"]["severe"] == 1
    assert row["candidate"]["legs"] == lab.st["templates"]["T3_BLACKOUT"]["legs"]
    report = E.report(lab.root)
    group = report["calibration_by_submitter_agent"][0]
    assert group["submitter"] == "office-test" and group["agent"] == "odte-forecaster"
    assert group["resolved_model"] == "test-model-v1" and group["resolved"] == 1
    assert group["stop"]["brier"] == pytest.approx(.04)
    assert group["severe"]["brier"] == pytest.approx(.64)
    expected = -1 - (row["outcome"]["gross_pnl_usd"] - 7.2)
    assert report["comparisons"]["T3_BLACKOUT"]["total_diff_usd"] == pytest.approx(expected)
    assert report["numerical_warmup_sessions"] == 1
    assert not report["promotion_allowed"] and D.LIVE_TEMPLATE == "T3_BLACKOUT"
    # Replay cannot duplicate the scored outcome or overwrite the forecast.
    lab.tick(10, 2)
    assert E.report(lab.root)["paired_forecasts"] == 1
    with pytest.raises(ValueError, match="already sealed"):
        lab.forecast()
    assert lab.client.calls == 1


def test_time_exit_scores_negative_stop_event_and_charges_costs(lab):
    lab.out.update(stop_probability=.1, severe_probability=.02)
    lab.forecast(); lab.tick(10, 0)
    for minute in range(10 * 60 + 1, 15 * 60 + 46):
        lab.tick(*divmod(minute, 60))
    row = E.read(lab.root / "sessions" / (DATE + ".json"))
    assert row["outcome"]["stop"] == 0 and row["outcome"]["severe"] == 0 and row["text_trade"]
    report = E.report(lab.root)
    assert report["comparisons"]["T3_BLACKOUT"]["total_diff_usd"] == -1
    assert report["calibration_by_submitter_agent"][0]["stop"]["brier"] == pytest.approx(.01)


@pytest.mark.parametrize("failure", ["invalid_probability", "unsupported_quote", "future_source", "insufficient_sources", "model_error"])
def test_pipeline_failures_are_recorded_without_forecasts(lab, failure):
    if failure == "invalid_probability":
        lab.out["stop_probability"] = 1.1
    elif failure == "unsupported_quote":
        lab.out["reasons"][0]["quote"] = "unsupported claim"
    elif failure == "future_source":
        lab.sources[0]["published_at"] = START.replace(hour=11).isoformat()
        lab.sources[0]["id"] = E.digest({k: v for k, v in lab.sources[0].items() if k != "id"})
    elif failure == "insufficient_sources":
        lab.sources.pop()
    else:
        def failed(request):
            raise RuntimeError("provider secret diagnostics must not persist")
        lab.client.complete = failed
    f = lab.forecast()
    assert f["status"] == "failed" and "provider secret" not in json.dumps(f)
    row = stopped(lab)
    assert row["text_trade"] is None and row["outcome"]
    report = E.report(lab.root)
    assert report["paired_forecasts"] == 0 and report["forecast_failures"] == 1
    assert report["missing_forecasts_at_entry"] == 1


def test_late_forecast_never_changes_the_frozen_entry_decision(lab):
    original = lab.client.complete
    def late(request):
        result = original(request)
        lab.clock[0] = START.replace(hour=10, minute=1)
        return result
    lab.client.complete = late
    assert lab.forecast()["status"] == "late"
    row = stopped(lab)
    assert row["forecast"] is None and row["text_trade"] is None


def test_forecast_cannot_be_run_after_deadline(lab):
    with pytest.raises(ValueError, match="window closed"):
        W.run_job(lab.root, DATE, client=lab.client, clock=lambda: START.replace(hour=10))
    assert lab.client.calls == 0


def test_deadline_is_eastern_even_when_entry_timestamp_is_utc(lab):
    f = lab.forecast()
    entry = START.replace(hour=10).astimezone(dt.timezone.utc)
    assert E.admitted_forecast(lab.root, DATE, lab.m, entry)["id"] == f["id"]


def test_deadline_does_not_parse_a_platform_specific_offset(lab, monkeypatch):
    lab.forecast()
    original = E.timestamp
    def portable_timestamp(value):
        # Python 3.9 rejects the offset without its colon; fail on that form
        # even when the test suite happens to be running on a newer Python.
        if value.endswith("-0400"):
            raise ValueError("nonportable numeric UTC offset")
        return original(value)
    monkeypatch.setattr(E, "timestamp", portable_timestamp)
    assert E.admitted_forecast(lab.root, DATE, lab.m, START.replace(hour=10))


@pytest.mark.parametrize("failure", ["gap", "delayed_leg"])
def test_missing_path_does_not_become_a_negative_label(lab, failure):
    lab.forecast(); lab.tick(10, 0)
    if failure == "gap":
        lab.tick(10, 3)
    else:
        rows = [dict(r, iv=.20, live_eligible=False) for r in chain()]
        lab.tick(10, 1, rows=rows)
    # Advance to a close; the gap stays latched even though quotes recover.
    lab.tick(15, 45)
    row = E.read(lab.root / "sessions" / (DATE + ".json"))
    assert row["status"] == "unresolved" and not row.get("outcome")
    assert E.report(lab.root)["paired_forecasts"] == 0


def test_manifest_rejects_mutation_and_code_drift(lab, monkeypatch):
    with pytest.raises(ValueError, match="already sealed"):
        E.initialize(lab.root, lab.root, "office-test", now=START)
    with monkeypatch.context() as patch:
        patch.setattr(E, "code_hash", lambda: "different")
        with pytest.raises(ValueError, match="code or templates changed"):
            E.protocol(lab.root)
    manifest = E.read(lab.root / "manifest.json"); manifest["stop_threshold"] = .9
    (lab.root / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="integrity"):
        E.protocol(lab.root)


def test_numeric_training_excludes_future_and_wrong_protocol(lab):
    lab.forecast(); row = stopped(lab)
    training = []
    for i in range(22):
        prior = copy.deepcopy(row)
        prior["date"] = (START.date() - dt.timedelta(days=i + 1)).isoformat()
        prior["outcome"]["resolved_at"] = prior["date"] + "T16:00:00-04:00"
        prior["outcome"]["stop"] = i % 3 == 0
        prior["outcome"]["severe"] = i % 7 == 0
        prior["features"]["opening_range_pct"] = i / 10
        E.atomic_json(lab.root / "sessions" / (prior["date"] + ".json"), prior)
        training.append(prior)
    training[0]["protocol"] = "another-protocol"
    E.atomic_json(lab.root / "sessions" / (training[0]["date"] + ".json"), training[0])
    training[1]["outcome"]["resolved_at"] = "2026-10-09T16:00:00-04:00"
    E.atomic_json(lab.root / "sessions" / (training[1]["date"] + ".json"), training[1])
    past = E.history(lab.root, START.replace(hour=10), lab.m)
    assert len(past) == 20 and all(r["date"] < DATE for r in past)
    result = E.numeric_forecast(row["features"], past, lab.m)
    assert result["status"] == "trained" and result["training_sessions"] == 20
    assert 0 < result["stop_probability"] < 1 and result["stop_probability"] != result["stop_base_rate"]


def test_report_includes_actual_t2_and_participation_control(lab):
    lab.out.update(stop_probability=.1, severe_probability=.01)
    lab.forecast(); row = stopped(lab)
    report = E.report(lab.root, shadow_rows=[{"template": "T2_REGIME", "date": DATE,
        "hash": D.template_hash("T2_REGIME"), "pnl_usd": None, "skip_kind": "strategy_cash"}])
    assert report["comparisons"]["T2_REGIME_ACTUAL_ENTRY"]["total_diff_usd"] == pytest.approx(row["outcome"]["gross_pnl_usd"] - 8.2)
    control = report["equal_participation_control"]
    assert control["traded"] == control["sessions"] == 1
    assert control["text_net_total_usd"] == pytest.approx(control["control_expected_total_usd"] - 1)


def test_grader_surfaces_experiment_and_agent_scores(lab, monkeypatch):
    lab.forecast(); stopped(lab)
    monkeypatch.setattr(D, "DATA", lab.root.parent)
    monkeypatch.setattr(G, "SCOREBOARD", lab.root / "scoreboard.json")
    monkeypatch.setattr(G, "UI_BOARD", lab.root / "ui.json")
    out = G.build()
    assert out["text_overlay"]["paired_forecasts"] == 1
    assert "office-test / odte-forecaster" in G.digest(out)


def test_collection_freezes_excerpt_and_rejects_redirects(lab):
    class Feed:
        url = lab.m["sources"][0]
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, limit):
            return b'<rss><channel><item><title>Public news</title><pubDate>Thu, 08 Oct 2026 13:30:00 GMT</pubDate><description>Event text</description></item></channel></rss>'
    sources, gaps = W.collect(lab.m, clock=lambda: START.replace(hour=9, minute=51), opener=lambda *a, **k: Feed())
    assert len(sources) == 1 and len(gaps) == 2
    assert sources[0]["visibility"] == "public_feed_excerpt"
    assert sources[0]["text"] == "Public news Event text"


def test_event_taxonomy_and_falsifier_are_required(lab):
    lab.out["reasons"][0]["novelty"] = "definitely priced in"
    f = lab.forecast()
    assert f["status"] == "failed" and f["failed_stage"] == "validate_forecast"


def market_snapshot(now, move=0):
    return {"ts": now.isoformat(), "rows": [dict(r, live_eligible=True, quote_age_s=2,
            iv=.24 if r["right"] == "P" and r["strike"] == 675 else .20) for r in chain()],
            "spx": 6800 * math.exp(move), "xsp": 680., "vix1d": 18., "indices_live": True}


def test_feature_math_and_forward_outcomes_use_real_capture_seconds(lab):
    lab.forecast()
    # A real daemon samples at nonzero seconds and variable intervals.
    start = START.replace(hour=10, second=13)
    previous = []
    for minute in range(61):
        snap = market_snapshot(start + dt.timedelta(minutes=minute), minute * .0001)
        with E.locked(lab.root):
            observation = V.record(lab.root, snap, lab.m["protocol"], E.timestamp(snap["ts"]))
        previous.append(observation)
        if minute == 14:
            assert not list((lab.root / "volatility_outcomes").glob("*.json"))
    feature = previous[15]["features"]
    assert feature["skew_25d"] == pytest.approx(.04)
    assert feature["smile_curvature"] == pytest.approx(.02)
    assert feature["return_5m_pct"] == pytest.approx(.05)
    assert feature["path_efficiency_15m"] == pytest.approx(1)
    assert feature["realized_vol_15m"] == pytest.approx(.0001*math.sqrt(V.YEAR_SECONDS/60))
    for horizon in (15, 60):
        outcome = E.read(lab.root / "volatility_outcomes" / f"{DATE}_{horizon}m.json")
        assert outcome["status"] == "resolved" and outcome["elapsed_seconds"] == horizon * 60
        assert outcome["targets"]["forward_realized_vol"] == pytest.approx(feature["realized_vol_15m"])
        assert outcome["forecast_id"] and outcome["text_reasons"][0]["event_type"] == "auction"
    report = V.effects(lab.root)
    tag = next(r for r in report["text_tag_groups"] if r["tag"] == "auction" and r["target"] == "forward_realized_vol")
    assert tag["tagged_sessions"] == 1
    # Many observations within a day remain a single session, not 61 samples.
    assert max(r["sessions"] for r in report["associations"]) == 1
    assert all(r["pearson_r"] is None for r in report["associations"])


def test_volatility_missing_data_and_ledger_tampering_fail_closed(lab):
    start = START.replace(hour=10)
    with E.locked(lab.root):
        snap = market_snapshot(start)
        original = V.record(lab.root, snap, lab.m["protocol"], start)
        assert V.record(lab.root, snap, lab.m["protocol"], start)["id"] == original["id"]
        with pytest.raises(ValueError, match="Conflicting"):
            V.record(lab.root, {**snap, "spx": 1}, lab.m["protocol"], start)
        future = market_snapshot(start + dt.timedelta(minutes=15))
        observed = V.record(lab.root, future, lab.m["protocol"], E.timestamp(future["ts"]))
        assert observed["features"]["realized_vol_15m"] is None
    outcome = E.read(lab.root / "volatility_outcomes" / f"{DATE}_15m.json")
    assert outcome["status"] == "unresolved" and not outcome["targets"] and outcome["forecast_id"] is None
    file = lab.root / "observations" / (DATE + ".jsonl")
    file.write_text(file.read_text().replace('"spx": 6800.0', '"spx": 9999.0'))
    with pytest.raises(ValueError, match="integrity"):
        V.record(lab.root, market_snapshot(start + dt.timedelta(minutes=16)), lab.m["protocol"], start)


def test_premarket_workflow_then_same_day_shadow_outcome(lab, monkeypatch, tmp_path):
    root = tmp_path / "premarket"
    m = E.initialize(root, tmp_path, "office-test", now=START.replace(hour=8), premarket=True, session_date=DATE)
    chains = tmp_path / "chains"; chains.mkdir()
    monkeypatch.setattr(D, "CHAINS", chains)
    yesterday = market_snapshot(START.replace(day=7, hour=15, minute=45))
    (chains / "2026-10-07.jsonl").write_text(json.dumps(yesterday) + "\n")
    # Deliberately poison the same-day file: it must not be read premarket.
    (chains / (DATE + ".jsonl")).write_text("not JSON; future data")
    prepared = W.prepare_premarket(root, now=START.replace(hour=8, minute=45))
    assert prepared["market_context"]["kind"] == "prior_session_only"
    assert prepared["snapshot"]["ts"] == yesterday["ts"] and prepared["opening"] == {}
    for source in lab.sources:
        source.update(published_at=START.replace(hour=8, minute=30).isoformat(),
                      fetched_at=START.replace(hour=8, minute=46).isoformat())
        source["id"] = E.digest({k: v for k, v in source.items() if k != "id"})
    lab.out["reasons"][0]["source_id"] = lab.sources[0]["id"]
    forecast = W.run_job(root, DATE, client=lab.client, collector=lambda _: (lab.sources, []),
                         clock=lambda: START.replace(hour=8, minute=47))
    assert forecast["status"] == "accepted"
    state = S.load_state(DATE)
    for minute in (9*60+31, 10*60):
        now = START.replace(hour=minute//60, minute=minute%60)
        snap = market_snapshot(now)
        S.step(state, snap, (now.hour, now.minute), False)
        E.observe(root, state, snap, {"events": []}, now=now)
    decision = E.read(root / "sessions" / (DATE + ".json"))
    assert decision["forecast"]["id"] == forecast["id"] and decision["text_trade"] is False
    assert m["forecast_deadline_et"] == "09:15:00"
    with pytest.raises(ValueError, match="window closed"):
        W.run_job(root, DATE, client=lab.client, clock=lambda: START.replace(hour=9, minute=15))
    with pytest.raises(ValueError, match="Not the registered"):
        W.prepare_premarket(root, now=START.replace(day=9, hour=8, minute=45))


def test_premarket_no_history_is_explicit_and_window_is_enforced(lab, monkeypatch, tmp_path):
    root = tmp_path / "premarket-empty"
    E.initialize(root, tmp_path, "office-test", now=START.replace(hour=8), premarket=True, session_date=DATE)
    monkeypatch.setattr(D, "CHAINS", tmp_path / "no-data")
    with pytest.raises(ValueError, match="window"):
        W.prepare_premarket(root, now=START.replace(hour=7, minute=45))
    job = W.prepare_premarket(root, now=START.replace(hour=8, minute=45))
    assert job["snapshot"] is None and job["market_context"]["kind"] == "unavailable"


def test_research_error_never_preempts_broker_management(lab, monkeypatch):
    from desk.odte import runner as R
    from test_odte_execution import Broker
    session = R.Session(Broker(), DATE, False)
    session.live = True; session.rail = object()
    calls = []
    monkeypatch.setattr(session, "_live_tick", lambda *a: calls.append("broker_management"))
    def unavailable(*a, **k):
        calls.append("research")
        raise ValueError("research ledger unavailable")
    monkeypatch.setattr(E, "observe", unavailable)
    session.tick(START.replace(hour=9, minute=50))
    # 2026-10-08: research observation runs first (the live rail mirrors the decision it seals);
    # a research failure is persisted and broker management still runs on the same tick.
    assert calls == ["research", "broker_management"]
    assert "research ledger unavailable" in S.load_state(DATE)["text_overlay_error"]
