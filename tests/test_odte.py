"""Hermetic tests for the 0DTE sleeve: strike selection at the touch, close/settle math, manage,
combo price sign, risk gates, shadow step, grader stats, template freezing."""
import json

import pytest

from desk.odte import templates as T, risk as R, shadow as S, grader as G, doctrine as D
from desk.odte.rail import combo_limit, live_pnl_usd


def chain(spot=680.0, width=12, put_skew=0.03):
    rows = []
    for i in range(-width, width + 1):
        k = spot + i
        dist = abs(i)
        pd = max(0.01, 0.5 + 0.05 * i)      # put |delta| falls as the strike falls below spot (i<0)
        cd = max(0.01, 0.5 - 0.05 * i)      # call delta falls as the strike rises above spot (i>0)
        pv = max(0.05, 3.0 - 0.3 * dist) if i < 0 else 3.0 + 0.3 * i
        cv = max(0.05, 3.0 - 0.3 * dist) if i > 0 else 3.0 - 0.3 * i
        rows.append({"strike": k, "right": "P", "bid": round(pv, 2), "ask": round(pv + 0.05, 2), "delta": -round(min(0.99, pd), 3), "conId": 1000 + 2 * (i + width)})
        rows.append({"strike": k, "right": "C", "bid": round(cv, 2), "ask": round(cv + 0.05, 2), "delta": round(min(0.99, cd), 3), "conId": 1001 + 2 * (i + width)})
    return rows


def test_build_condor_at_touch_and_max_loss():
    c = T.build_condor(chain(), short_delta=0.10, wing=2.0)
    assert c["ok"], c
    assert c["short_put"] == 672.0 and c["short_call"] == 688.0           # |delta| 0.10 is 8 strikes out
    assert c["legs"]["lp"]["strike"] == 670.0 and c["legs"]["lc"]["strike"] == 690.0
    sp, lp, sc, lc = (c["legs"][k] for k in ("sp", "lp", "sc", "lc"))
    assert c["credit"] == round((sp["bid"] - lp["ask"]) + (sc["bid"] - lc["ask"]), 2)   # sell at bid, buy at ask
    assert c["max_loss_usd"] == round((2.0 - c["credit"]) * 100, 2)
    assert all(c["legs"][k]["conId"] for k in c["legs"])


def test_build_condor_refuses_thin_credit_and_illiquid_legs():
    rows = chain()
    for r in rows:
        r["bid"] = 0.02; r["ask"] = 0.04
    assert not T.build_condor(rows, 0.10, 2.0)["ok"]
    rows = chain()
    for r in rows:
        if r["strike"] == 672.0 and r["right"] == "P":
            r["bid"] = 0.5; r["ask"] = 1.6                       # 1.10 wide on a 1.05 mid
    assert "illiquid" in T.build_condor(rows, 0.10, 2.0)["why"]


def test_cost_to_close_settle_and_manage():
    rows = chain(); c = T.build_condor(rows, 0.10, 2.0); pos = {"credit": c["credit"], "legs": c["legs"]}
    cc = T.cost_to_close(c["legs"], rows)
    assert cc > c["credit"]                                              # closing at the touch costs the spread
    assert T.manage(pos, rows, (12, 0), 2.0, (15, 45))["action"] == "HOLD"
    assert T.manage(pos, rows, (15, 45), 2.0, (15, 45))["action"] == "CLOSE_TIME"
    # blow the put side out: short put ask jumps
    for r in rows:
        if r["right"] == "P" and r["strike"] == 672.0:
            r["ask"] = 5.0; r["bid"] = 4.9
    assert T.manage(pos, rows, (12, 0), 2.0, (15, 45))["action"] == "CLOSE_STOP"
    legs = c["legs"]
    assert T.settle(legs, 700.0) == 2.0    # far above: call wing fully in (2.0 max)
    assert T.settle(legs, 680.0) == 0.0
    assert T.settle(legs, 671.0) == 1.0 and T.settle(legs, 600.0) == 2.0   # capped at the wing
    assert T.pnl_usd(0.40, 0.10) == 30.0 and T.pnl_usd(0.40, 2.0) == -160.0


def test_entry_windows_and_regime():
    base = {"now_et": (10, 5), "is_event_day": False, "first30_range": 0.004, "vix1d_open": 18.0, "vix1d_now": 17.0}
    assert T.entry_allowed("T1_MECH", base)[0]
    assert not T.entry_allowed("T1_MECH", {**base, "now_et": (10, 30)})[0]
    assert T.entry_allowed("T1_MECH", {**base, "is_event_day": True})[0]            # T1 trades every day: the climatology
    assert not T.entry_allowed("T3_BLACKOUT", {**base, "is_event_day": True})[0]
    assert T.entry_allowed("T2_REGIME", base)[0]
    assert not T.entry_allowed("T2_REGIME", {**base, "first30_range": 0.009})[0]
    assert not T.entry_allowed("T2_REGIME", {**base, "vix1d_now": 19.0})[0]


def test_combo_limit_sign():
    assert combo_limit("BUY", 0.35) == -0.35          # open: receive 0.35 -> BUY at negative
    assert combo_limit("SELL", -0.60) == -0.60        # close: pay 0.60 -> SELL at negative
    assert combo_limit("BUY", -0.20) == 0.20          # a debit structure bought = positive
    assert live_pnl_usd(0.35, 0.10) == 25.0 and live_pnl_usd(0.35, 0.10, commissions=2.6) == 22.4


def test_live_gates():
    env = {"status": "ARMED", "origin": "signalos_desk+principal", "expires": "2026-12-31"}
    ctx = {"date": "2026-10-08", "now_et": (10, 5), "vix1d_open": 18.0, "vix1d_now": 18.5, "first30_range": 0.005,
           "is_event_day": False, "calendar_verified": True, "halted": None, "structures_today": 0}
    ok, why, pause = R.live_gates(env, [], ctx); assert ok and not why and pause is None
    assert not R.live_gates({**env, "status": "DRAFT"}, [], ctx)[0]
    assert not R.live_gates({**env, "origin": "antigravity"}, [], ctx)[0]
    assert not R.live_gates(env, [], {**ctx, "calendar_verified": False})[0]
    assert not R.live_gates(env, [], {**ctx, "is_event_day": True})[0]
    assert not R.live_gates(env, [], {**ctx, "structures_today": 1})[0]
    assert not R.live_gates(env, [], {**ctx, "vix1d_now": 36.0})[0]
    assert not R.live_gates(env, [], {**ctx, "vix1d_now": 24.0})[0]            # +33% jump
    assert not R.live_gates(env, [], {**ctx, "first30_range": 0.02})[0]
    assert not R.live_gates(env, [], {**ctx, "halted": "why"})[0]
    led = [{"date": "2026-10-05", "pnl_usd": -180.0}, {"date": "2026-10-06", "pnl_usd": -190.0}, {"date": "2026-10-07", "pnl_usd": -40.0}]
    ok, why, pause = R.live_gates(env, led, ctx); assert not ok and any("weekly" in w for w in why) and pause is None
    led2 = [{"date": f"2026-10-0{d}", "pnl_usd": -150.0} for d in range(1, 7)]
    ok, why, pause = R.live_gates(env, led2, ctx); assert pause and "monthly" in pause
    assert R.consecutive_losses(led) == 3 and R.consecutive_losses(led + [{"date": "2026-10-08", "pnl_usd": 5}]) == 0
    assert R.flatten_now({**ctx, "vix1d_now": 25.0}) and R.flatten_now(ctx) is None


def test_shadow_step_enters_manages_and_settles(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "SHADOW_LEDGER", tmp_path / "l.jsonl"); monkeypatch.setattr(S, "DATA", tmp_path)
    st = S.load_state("2026-10-08")
    snap = lambda ts, rows, spx, vix, xsp: {"ts": ts, "rows": rows, "spx": spx, "vix1d": vix, "xsp": xsp, "data_type": "live", "greeks": "model"}
    S.step(st, snap("09:31", chain(), 6800.0, 18.0, 680.0), (9, 31), False)
    S.step(st, snap("09:45", chain(), 6810.0, 18.5, 681.0), (9, 45), False)
    assert st["templates"]["T1_MECH"]["status"] == "NONE"
    closed = S.step(st, snap("10:01", chain(), 6805.0, 17.9, 680.5), (10, 1), False)
    assert st["session"]["first30_range"] == pytest.approx(10 / 6800, rel=1e-3)
    assert st["templates"]["T1_MECH"]["status"] == "OPEN" and st["templates"]["T2_REGIME"]["status"] == "OPEN" and not closed
    closed = S.step(st, snap("15:45", chain(), 6805.0, 17.9, 680.5), (15, 45), False)
    assert {r["template"] for r in closed} == {"T1_MECH", "T2_REGIME", "T3_BLACKOUT"} and all(r["reason"] == "CLOSE_TIME" for r in closed)
    assert all(r["pnl_usd"] < 0 for r in closed)                          # closing at the touch with unchanged quotes loses the spread
    # event day: T3/T2 skip, T1 trades
    st2 = S.load_state("2026-10-28")
    S.step(st2, snap("09:31", chain(), 6800.0, 18.0, 680.0), (9, 31), True)
    S.step(st2, snap("10:01", chain(), 6800.0, 17.0, 680.0), (10, 1), True)
    assert st2["templates"]["T1_MECH"]["status"] == "OPEN" and st2["templates"]["T3_BLACKOUT"]["status"] == "NONE"
    rows = S.finalize_day(st2)
    assert any(r["template"] == "T1_MECH" and r["reason"] == "SETTLED" and r["pnl_usd"] == round(st2["templates"]["T1_MECH"]["credit"] * 100, 2) for r in rows)
    assert any(r["template"] == "T3_BLACKOUT" and r["reason"] == "NO_ENTRY" and "blackout" in (r["skip_reason"] or "") for r in rows)


def test_grader_stats_and_benchmark():
    h = D.template_hash("T2_REGIME"); hb = D.template_hash("T1_MECH")
    b = [{"template": "T1_MECH", "hash": hb, "date": f"2026-10-{d:02d}", "pnl_usd": p, "reason": "SETTLED"} for d, p in [(1, 30), (2, -160), (3, 25), (5, 28)]]
    t = [{"template": "T2_REGIME", "hash": h, "date": f"2026-10-{d:02d}", "pnl_usd": p, "reason": "SETTLED"} for d, p in [(1, 30), (3, 25), (5, 28)]] + \
        [{"template": "T2_REGIME", "hash": h, "date": "2026-10-02", "pnl_usd": None, "reason": "NO_ENTRY", "skip_kind": "strategy_cash"}]
    sb = G.stats(b); assert sb["traded"] == 4 and sb["total_usd"] == -77 and sb["max_dd_usd"] == -160 and sb["win_rate"] == 0.75
    vb = G.vs_benchmark(t, b); assert vb["paired"] == 4 and vb["mean_diff_usd"] == 40.0
    g = G.graduation(G.stats(t), vb, sb); assert not g["graduated"] and not g["sessions_ok"]


def test_template_freeze_is_stable(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "DATA", tmp_path); monkeypatch.setattr(D, "FROZEN", tmp_path / "f.json")
    a = D.freeze(); b = D.freeze()
    assert a["hashes"] == b["hashes"] and len(a["hashes"]) == 3 and D.template_hash("T1_MECH") == a["hashes"]["T1_MECH"]
    assert D.LIVE_TEMPLATE == "T3_BLACKOUT" and D.CONTRACTS == 1 and D.WING_WIDTH == 2.0
