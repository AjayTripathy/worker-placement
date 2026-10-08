"""Matched prospective forecasts and economics, entirely synthetic and offline."""
import datetime as dt
import json
from types import SimpleNamespace as NS

import pytest

from desk.odte import edge_trial as X, edge_stats as B, arms as A, text_overlay as E
from officekit_ai.intelligence import Response, Text, Usage
from test_odte_arms import lab, DATE, REGISTER, ENTRY  # noqa: F401
from test_odte_execution import isolation  # noqa: F401


@pytest.fixture
def matched(lab, tmp_path):
    morning = ENTRY.replace(hour=9)
    job = {"date": DATE, "protocol": lab.sm["protocol"], "created_at": morning.isoformat(),
           "snapshot": None, "opening": {}, "market_features": {}, "indicative_candidate": None,
           "calendar": {"events": []}, "event_kinds": [], "market_context": {"kind": "unavailable"}}
    sources = []
    for feed in lab.sm["sources"][:2]:
        s = {"feed": feed, "url": feed, "text": "A scheduled auction occurs today.",
             "published_at": morning.isoformat(), "fetched_at": morning.isoformat(), "visibility": "public_feed_excerpt"}
        s["id"] = E.digest(s); sources.append(s)
    corpus = {"protocol": lab.sm["protocol"], "sources": sources, "coverage_gaps": [], "cutoff": morning.isoformat()}
    E.seal(lab.source/"jobs"/(DATE+".json"), job)
    E.seal(lab.source/"corpora"/(DATE+".json"), corpus)
    A.seal(lab.source/"forecasts"/(DATE+".json"), {"date": DATE, "protocol": lab.sm["protocol"],
        "issued_at": morning.isoformat(), "job_digest": E.digest(job), "corpus_digest": E.digest(corpus),
        "status": "accepted", "forecast": {"stop_probability": .8, "severe_probability": .2}})
    root = tmp_path/"matched"
    m = X.initialize(root, lab.root, start_date=DATE, now=REGISTER)
    class Client:
        requests = []
        fail = False
        def complete(self, request):
            self.requests.append(request)
            if self.fail:
                raise RuntimeError("sensitive provider diagnostic must not be saved")
            payload = json.loads(request.messages[0]["content"])
            sources = payload["evidence"]
            out = {"stop_probability": .8 if sources else .1, "severe_probability": .2 if sources else .02,
                "expected_gross_return_on_risk": -.3 if sources else .2,
                "rationale": "Synthetic controlled forecast.",
                "citations": [{"source_id": sources[0]["id"], "quote": "scheduled auction"}] if sources else []}
            return Response([Text(json.dumps(out))], "fixture-resolved", usage=Usage(100, 50))
    clock = [morning+dt.timedelta(minutes=1)]
    return NS(root=root, m=m, lab=lab, client=Client(), clock=clock, job=job, corpus=corpus)


def run(x):
    return X.once(x.root, clock=lambda: x.clock[0], client=x.client)


def test_matched_inputs_no_forecast_leak_and_end_to_end_economics(matched):
    x = matched
    before = x.lab.m["protocol"]
    assert run(x)["status"] == "accepted"
    requests = [json.loads(r.messages[0]["content"]) for r in x.client.requests]
    assert len(requests) == 2
    assert requests[0]["common"] == requests[1]["common"]
    assert sorted(bool(r["evidence"]) for r in requests) == [False, True]
    assert "source_forecast" not in json.dumps(requests)
    assert x.client.requests[0].system == x.client.requests[1].system
    x.lab.tick(10, 0); x.lab.tick(10, 1, stop=True)
    r = X.report(x.root)
    day = r["sessions"][DATE]
    assert day["text"]["take"] is False and day["no_text"]["take"] is True
    assert day["text"]["net_pnl_usd"] == -1
    assert day["no_text"]["net_pnl_usd"] == pytest.approx(day["no_text"]["gross_usd"]-8.2)
    group = next(g for g in r["calibration_by_submitter_agent"] if g["variant"] == "text")
    assert group["stop_brier"] == pytest.approx(.04)
    assert group["severe_brier"] == pytest.approx(.64)
    assert group["resolved_model"] == "fixture-resolved" and group["resolved"] == 1
    comparison = r["comparisons"]["discovery"]["text_minus_no_text"]
    assert comparison["sessions"] == 1 and comparison["interval_usd"] is None
    assert comparison["mean_usd"] > 0
    assert not r["promotion_allowed"] and A.protocol(x.lab.root)["protocol"] == before
    old = len(x.client.requests)
    assert run(x)["status"] == "accepted" and len(x.client.requests) == old


def test_economic_gate_can_reject_calm_but_underpaid_trade(matched):
    m = matched.m; candidate = {"max_loss_usd": 175}
    calm = {"stop_probability": .1, "severe_probability": .01, "expected_gross_return_on_risk": .01}
    take, expected = X.policy(calm, candidate, "text", m)
    assert not take and expected < 0
    calm["expected_gross_return_on_risk"] = .2
    assert X.policy(calm, candidate, "text", m)[0]


def test_all_model_failures_are_visible_costed_and_not_retryable(matched):
    x = matched; x.client.fail = True
    assert run(x)["status"] == "partial_failure"
    x.lab.tick(10, 0); x.lab.tick(10, 1, stop=True)
    r = X.report(x.root)
    assert r["forecast_status_counts"]["failed"] == 2
    assert r["operational"]["text"]["assumed_all_attempt_cost_usd"] == 1
    assert r["operational"]["text"]["resolved_trading_subtotal_less_all_attempt_costs_usd"] == -1
    assert r["comparisons"]["discovery"]["text_minus_no_text"]["sessions"] == 0
    assert "sensitive provider diagnostic" not in json.dumps(r)
    run(x); assert len(x.client.requests) == 2


def test_missing_path_is_not_cash_win_or_calibration_success(matched):
    x = matched; run(x); x.lab.tick(10, 0); x.lab.tick(10, 3, stop=True)
    r = X.report(x.root)
    assert r["sessions"][DATE]["text"]["net_pnl_usd"] == -1
    assert r["sessions"][DATE]["no_text"]["net_pnl_usd"] is None
    assert r["comparisons"]["discovery"]["text_minus_no_text"]["sessions"] == 0
    assert r["calibration_by_submitter_agent"] == []
    assert r["operational"]["no_text"]["unresolved_takes"] == 1
    audit = r["existing_arm_audit"]["arms"]["T3"]
    assert audit["unresolved_takes"] == 1
    assert audit["unresolved_stress_totals_usd"]["lose_entry_max_risk"] < 0


@pytest.mark.parametrize("problem", ["future_start", "too_early", "deadline", "past_date"])
def test_no_out_of_window_calls(matched, problem):
    x = matched
    if problem == "future_start":
        with pytest.raises(ValueError, match="future start"):
            X.initialize(x.root/"other", x.lab.root, start_date=DATE, now=ENTRY)
        return
    x.clock[0] = {"too_early": ENTRY.replace(hour=8, minute=44), "deadline": ENTRY.replace(hour=9, minute=15),
                  "past_date": REGISTER}[problem]
    with pytest.raises(ValueError, match="prospective"):
        run(x)
    assert not x.client.requests


def test_reserved_crash_never_selects_a_replacement_answer(matched):
    x = matched
    A.seal(x.root/"runs"/(DATE+".json"), {"date": DATE, "protocol": x.m["protocol"]})
    assert run(x)["status"] == "incomplete_attempt"
    assert not x.client.requests
    assert X.report(x.root)["incomplete_runs"] == 1


def test_future_or_modified_evidence_fails_before_inference(matched):
    x = matched
    path = x.lab.source/"corpora"/(DATE+".json")
    corpus = E.read(path); corpus["sources"][0]["text"] += " manipulated"
    path.write_text(json.dumps(corpus))
    assert run(x)["status"] == "failed" and not x.client.requests
    assert X.report(x.root)["run_status_counts"]["failed"] == 1


def test_training_resolved_time_and_real_stop_label(matched):
    x = matched; run(x); x.lab.tick(10, 0); x.lab.tick(10, 1, stop=True)
    am = {**x.lab.m, "root": str(x.lab.root)}
    assert X.training(x.root, x.m, am, ENTRY) == []
    history = X.training(x.root, x.m, am, ENTRY+dt.timedelta(days=1))
    assert len(history) == 1 and history[0]["outcome"]["stop"] == 1
    assert history[0]["return_on_risk"] < 0
    op = x.lab.root/"outcomes"/(DATE+".json")
    r = A.checked(op); r.pop("id"); r["resolved_at"] = (ENTRY+dt.timedelta(days=2)).isoformat()
    op.unlink(); A.seal(op, r)
    assert X.training(x.root, x.m, am, ENTRY+dt.timedelta(days=1)) == []


def test_freeze_and_late_response_are_enforced(matched, monkeypatch):
    x = matched; original = x.client.complete
    def late(request):
        response = original(request)
        x.clock[0] = ENTRY.replace(hour=9, minute=15)
        return response
    x.client.complete = late
    r = run(x)
    assert r["status"] == "partial_failure" and len(x.client.requests) == 1
    assert "late" in r["variants"].values()
    monkeypatch.setattr(X, "fingerprints", lambda: {})
    with pytest.raises(ValueError, match="code changed"):
        X.protocol(x.root)


def test_validation_window_is_fixed_by_decisions_not_resolved_successes(matched):
    x = matched; run(x); x.lab.tick(10, 0); x.lab.tick(10, 3, stop=True)
    # Vary a synthetic read-only policy view, keeping record identities intact.
    import unittest.mock
    view = {**x.m, "discovery_decision_sessions": 0, "validation_decision_sessions": 1}
    with unittest.mock.patch.object(X, "protocol", return_value=(view, x.lab.m)):
        r = X.report(x.root)
    assert r["validation_decision_sessions"] == 1
    assert r["comparisons"]["validation"]["text_minus_no_text"]["sessions"] == 0
    assert r["validation_review_due"]  # Review of missingness, NOT graduation.


def test_empty_and_populated_page_escapes_dynamic_content(matched):
    from desk.odte.render_edge_trial import render
    x = matched
    empty = render(X.report(x.root))
    assert "Insufficient sessions" in empty and "No proven investment edge" in empty
    run(x); x.lab.tick(10, 0); x.lab.tick(10, 1, stop=True)
    r = X.report(x.root); r["limitations"].append('<script>alert("bad")</script>')
    html = render(r)
    assert '<script>' not in html and '&lt;script&gt;' in html
    assert "Calibration by submitter" in html


def test_statistics_use_daily_pair_counts_and_widen_family_intervals():
    values = [float(i % 9-4) for i in range(40)]
    single = B.paired_interval(values); family = B.paired_interval(values, family=16)
    assert single["sessions"] == 40
    assert family["interval_usd"][0] <= single["interval_usd"][0]
    assert family["interval_usd"][1] >= single["interval_usd"][1]
    assert B.paired_interval([])["mean_usd"] is None
    with pytest.raises(ValueError):
        B.paired_interval([float("nan")])
    control = B.participation_control([10, -20], [True, False], 1)
    assert control["uniform_expected_net_usd"] == -5
    assert control["strategy_net_usd"] == 8


def test_citation_and_finite_number_admission(matched):
    out = {"stop_probability": .2, "severe_probability": .1, "expected_gross_return_on_risk": .05,
           "rationale": "Fixture", "citations": []}
    X.validate(out, [])
    with pytest.raises(ValueError, match="Citations"):
        X.validate(out, matched.corpus["sources"])
    out["expected_gross_return_on_risk"] = float("inf")
    with pytest.raises(ValueError, match="Nonfinite"):
        X.validate(out, [])
