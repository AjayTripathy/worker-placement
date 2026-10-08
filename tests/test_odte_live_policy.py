"""2026-10-08 live policy: the one live contract follows the SEALED arm decision (T3..T18 / CASH)
and executes as a MAKER (post at mid, patience, one re-post, stand down). Broker-free."""
import datetime as dt
import json

import pytest

from desk.odte import arms as A, grader as G, runner as R, shadow as S, templates as T, doctrine as D
from test_odte import chain
from test_odte_execution import Broker, Capture, session, DATE, NOW, isolation  # noqa: F401

POLICY = {"follow": "arm_selector", "fallback": "stand_down", "execution": "maker"}


@pytest.fixture
def live_policy(monkeypatch):
    monkeypatch.setattr(R, "LIVE_POLICY", POLICY)
    monkeypatch.setattr(R, "MAKER_PATIENCE_S", 120)


def seal_decision(tmp_path, monkeypatch, legs, selected="T5", verdict="take", protocol="p"):
    root = S.DATA / "arm_experiment"; (root / "decisions").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(A, "protocol", lambda r: {"protocol": protocol, "arms": {"T3": {"label": "Calendar baseline"}, "T5": {"label": "volatility"}, "CASH": {"label": "Always cash control"}}})
    row = {"date": DATE, "protocol": protocol, "entry_at": NOW.isoformat(),
           "snapshot_digest": A.E.digest(Capture().snapshot(NOW)),
           "candidate": {"legs": legs, "credit": 1.0, "max_loss_usd": 100.0},
           "arms": {"T3": {"decision": "take"}, "T5": {"decision": verdict}, "CASH": {"decision": "skip"}},
           "allocation": {"selected_arm": selected, "selected_probability": 1 / 17, "status": "uniform_warmup"},
           "gates": {"volatility": {"pass": True}}, "forecast": {"forecast": {"stop_probability": 0.1, "severe_probability": 0.02}}}
    return A.seal(root / "decisions" / (DATE + ".json"), row)


def test_mid_credit_and_ladder():
    rows = chain(); c = T.build_condor(rows, .1, 2)
    mid = T.mid_credit(c["legs"], rows)
    assert mid == 1.1                                                # each leg's mid is 0.025 better than its touch
    assert mid > c["credit"] == 1.0
    assert T.mid_credit(c["legs"]) == 1.1                            # from the legs' own quotes
    s = R.Session.__new__(R.Session)
    assert s._maker_ladder(1.0, 1.1) == ([1.1, 1.09], "mid")
    assert s._maker_ladder(1.0, None) == ([1.0], "touch (no mid improvement available)")
    assert s._maker_ladder(1.0, 1.005) == ([1.0], "touch (no mid improvement available)")
    assert s._maker_ladder(1.0, 1.01) == ([1.01, 1.0], "mid")


def test_no_arm_experiment_means_stand_down(live_policy):
    ib = Broker(["fill"]); s = session(ib); s.tick(NOW)
    assert not ib.orders and s.lv["status"] == "SKIPPED" and "no registered arm experiment" in s.lv["why"]
    row = {r["date"]: r for r in R.read_live()}[DATE]
    assert row["reason"] == "NO_ENTRY" and row["accounting_status"] == "complete" and row["policy"]["follow"] == "arm_selector"


def test_selected_cash_arm_stands_down(live_policy, tmp_path, monkeypatch):
    legs = T.build_condor(chain(), .1, 2)["legs"]
    d = seal_decision(tmp_path, monkeypatch, legs, selected="CASH")
    ib = Broker(["fill"]); s = session(ib); s.tick(NOW)
    assert not ib.orders and s.lv["status"] == "SKIPPED"
    assert s.lv["policy"]["decision"]["arm"] == "CASH" and s.lv["policy"]["decision"]["decision_id"] == d["id"]


def test_candidate_mismatch_stands_down(live_policy, tmp_path, monkeypatch):
    legs = T.build_condor(chain(), .1, 2)["legs"]
    other = {k: dict(v, conId=v["conId"] + 1000) for k, v in legs.items()}
    seal_decision(tmp_path, monkeypatch, other, selected="T5")
    ib = Broker(["fill"]); s = session(ib); s.tick(NOW)
    assert not ib.orders and s.lv["status"] == "SKIPPED" and "!=" in s.lv["why"]


def test_selected_take_posts_at_mid_waits_reposts_and_fills(live_policy, tmp_path, monkeypatch):
    legs = T.build_condor(chain(), .1, 2)["legs"]
    seal_decision(tmp_path, monkeypatch, legs, selected="T5", verdict="take")
    import functools
    ib = Broker(["cancel", "fill"]); ib.fill = functools.partial(Broker.fill, ib, price=-1.09)   # fills AT the posted price
    s = session(ib)
    s.tick(NOW)                                                      # post #1 at the mid, resting
    assert len(ib.orders) == 1 and s.lv["status"] == "OPENING"
    assert ib.orders[0].order.lmtPrice == -1.1 and s.lv["maker"]["attempt"] == 1 and s.lv["maker"]["touch"] == 1.0
    s.tick(NOW.replace(minute=6))                                    # 60s: inside patience, no cancel
    assert len(ib.orders) == 1 and ib.orders[0].orderStatus.status == "Submitted"
    s.tick(NOW.replace(minute=8))                                    # 180s: cancel (acknowledged), re-post #2 one step lower
    assert ib.orders[0].orderStatus.status == "Cancelled" and len(ib.orders) == 2
    assert ib.orders[1].order.lmtPrice == -1.09 and s.lv["maker"]["attempt"] == 2 and s.lv["status"] == "OPENING"
    s.tick(NOW.replace(minute=9))                                    # the resting re-post filled at 1.09
    assert s.lv["status"] == "OPEN" and s.lv["credit"] == pytest.approx(1.09)
    assert s.lv["maker_edge"] == pytest.approx(0.09)                 # 9 cents over the touch = the maker edge
    row = {r["date"]: r for r in R.read_live()}[DATE]
    assert row["maker"]["ladder"] == [1.1, 1.09] and row["policy"]["decision"]["arm"] == "T5"


def test_maker_stands_down_after_the_ladder(live_policy, tmp_path, monkeypatch):
    legs = T.build_condor(chain(), .1, 2)["legs"]
    seal_decision(tmp_path, monkeypatch, legs, selected="T5", verdict="take")
    ib = Broker(["cancel", "cancel"]); s = session(ib)
    s.tick(NOW); s.tick(NOW.replace(minute=8)); s.tick(NOW.replace(minute=11))
    assert len(ib.orders) == 2 and s.lv["status"] == "NO_FILL" and "no maker fill after 2" in s.lv["why"]
    row = {r["date"]: r for r in R.read_live()}[DATE]
    assert row["reason"] == "NO_FILL" and row["accounting_status"] == "complete" and row["pnl_usd"] is None
    s.tick(NOW.replace(minute=12))
    assert len(ib.orders) == 2                                       # one structure a day, never a third post


def test_unacknowledged_cancel_keeps_waiting(live_policy, tmp_path, monkeypatch):
    legs = T.build_condor(chain(), .1, 2)["legs"]
    seal_decision(tmp_path, monkeypatch, legs, selected="T5", verdict="take")
    ib = Broker(["pending"]); s = session(ib)
    s.tick(NOW); s.tick(NOW.replace(minute=8))
    assert len(ib.orders) == 1 and s.lv["status"] == "OPENING" and "not yet acknowledged" in s.lv["last_why"]


def test_finalize_stale_records_unresolved_not_settled(tmp_path, monkeypatch):
    st = S.load_state("2026-10-07")
    st["session"] = {"xsp_last": 680.0}
    c = T.build_condor(chain(), .1, 2)
    st["templates"]["T1_MECH"].update(status="OPEN", credit=c["credit"], legs=c["legs"])
    st["templates"]["T2_REGIME"].update(status="CLOSED", exit_reason="CLOSE_STOP")
    S.save_state(st)
    rows = S.finalize_stale("2026-10-08")
    by = {r["template"]: r for r in rows}
    assert by["T1_MECH"]["reason"] == "UNRESOLVED" and by["T1_MECH"]["pnl_usd"] is None and by["T1_MECH"]["skip_kind"] == "data_unavailable"
    assert by["T3_BLACKOUT"]["reason"] == "NO_ENTRY" and "T2_REGIME" not in by
    assert S.load_state("2026-10-07")["finalized"] and S.finalize_stale("2026-10-08") == []
    assert G.stats(S.read_ledger())["traded"] == 0                   # unresolved never counts as a result


def test_execution_stats():
    twin = [{"date": DATE, "credit": 0.30}]
    live = [{"date": DATE, "credit": 0.34, "reason": "CLOSE_TIME", "maker": {"attempt": 1}, "maker_edge": 0.04,
             "policy": {"decision": {"arm": "T5", "take": True}}},
            {"date": "2026-10-09", "credit": None, "reason": "NO_FILL", "maker": {"attempt": 2}, "policy": {"decision": {"arm": "T3", "take": True}}},
            {"date": "2026-10-10", "credit": None, "reason": "NO_ENTRY", "policy": {"decision": {"arm": "CASH", "take": False}}}]
    x = G.execution_stats(live, twin)
    assert x["maker_posts"] == 2 and x["maker_fills"] == 1 and x["fill_rate"] == 0.5
    assert x["mean_maker_edge_vs_touch_usd"] == 4.0 and x["mean_live_credit_minus_twin_touch_usd"] == 4.0
    assert x["selector_stand_downs"] == 1 and x["followed_arms"]["CASH"] == {"sessions": 1, "takes": 0}
