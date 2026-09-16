"""Hermetic tests for the agent-herd pilot: parsing, homogeneity, grading arithmetic. No network."""
import datetime as dt
import json

import pandas as pd
import pytest

from desk import agent_herd_pilot as AH


def test_parse_picks_tolerates_fences_and_junk():
    txt = "Sure! ```json\n{\"buy\": [{\"ticker\": \"$nvda\", \"reason\": \"ai\"}, {\"ticker\": \"BTC.X\"}, " \
          "{\"ticker\": \"nvda\"}, {\"ticker\": \"AAPL\"}], \"sell\": [{\"ticker\": \"tsla\", \"reason\": \"x\"}]}\n```"
    p = AH.parse_picks(txt)
    assert [r["ticker"] for r in p["buy"]] == ["NVDA", "AAPL"]        # $ stripped, .X dropped, dedupe
    assert [r["ticker"] for r in p["sell"]] == ["TSLA"]
    assert AH.parse_picks("no json here")["parse_error"] == "no-json"
    assert AH.parse_picks("{bad json}")["parse_error"] == "bad-json"


def test_parse_caps_counts():
    rows = [{"ticker": f"T{i}"} for i in range(9)]
    p = AH.parse_picks(json.dumps({"buy": rows, "sell": rows}))
    assert len(p["buy"]) == AH.MAX_BUY and len(p["sell"]) == AH.MAX_SELL


def test_homogeneity_jaccard_and_consensus():
    panel = {"haiku": {"buy": [{"ticker": "A"}, {"ticker": "B"}]},
             "sonnet": {"buy": [{"ticker": "B"}, {"ticker": "C"}]},
             "opus": {"buy": [{"ticker": "B"}, {"ticker": "D"}]},
             "broken": {"error": "timeout"}}
    h = AH.homogeneity(panel)
    assert h["pairwise_jaccard"]["haiku|sonnet"] == pytest.approx(1 / 3, abs=1e-3)   # stored rounded to 3dp
    assert h["consensus_buy"] == ["B"]                       # picked by >=2 models
    assert h["union_buy"] == ["A", "B", "C", "D"]
    assert AH.homogeneity({})["mean_jaccard"] is None


def test_is_trading_day_weekend():
    assert not AH.is_trading_day(dt.date(2026, 9, 12))        # Saturday
    assert not AH.is_trading_day(dt.date(2026, 9, 13))


def _fake_px(dates, series):
    idx = pd.to_datetime(dates)
    close = pd.DataFrame({t: v for t, v in series.items()}, index=idx)
    opn = close * 0.99
    return pd.concat({"Close": close, "Open": opn}, axis=1)


def test_grade_day_excess_vs_spy_and_control(monkeypatch):
    dates = ["2026-09-11", "2026-09-14", "2026-09-15"]           # d0 = 9/14; T-1 = 9/11; T+1 = 9/15
    series = {"PICK": [100, 104, 110], "CTRL": [50, 50, 51], "SPY": [10, 10, 10.1], "SHORTY": [20, 20, 18]}
    monkeypatch.setattr(AH, "_closes", lambda tickers, s, e: _fake_px(dates, series))
    rec = {"date": "2026-09-14", "validation": False,
           "context": {"most_active": ["CTRL", "PICK"], "stocktwits": []},
           "panel": {"haiku": {"buy": [{"ticker": "PICK"}], "sell": [{"ticker": "SHORTY"}]}}}
    nxt = {"context": {"stocktwits": ["PICK"], "most_active": []}}
    rows = AH.grade_day(rec, dt.date(2026, 9, 16), nxt)
    r = {x["ticker"]: x for x in rows}
    assert r["PICK"]["ret_1"] == pytest.approx(0.10)                       # 100 -> 110 over T-1..T+1
    assert r["PICK"]["xs_spy_1"] == pytest.approx(0.10 - 0.01)
    assert r["PICK"]["xs_ctrl_1"] == pytest.approx(0.10 - 0.02)           # control = CTRL only (PICK excluded)
    assert r["SHORTY"]["xs_spy_1"] == pytest.approx(-(-0.10 - 0.01))       # sell side sign-flipped
    # PICK was already on the most-actives list at T, so it is a flow HIT at T+1 but NOT a NEW appearance
    assert r["PICK"]["was_trending_T"] is True and r["PICK"]["flow_hit_T1"] is True and r["PICK"]["flow_new_T1"] is False
    assert r["PICK"]["ret_5"] is None                                       # horizon not matured


def test_summary_kill_logic(tmp_path, monkeypatch):
    monkeypatch.setattr(AH, "DATA", tmp_path)
    rows = []
    for i in range(35):                                                    # 35 trading days, tiny effect
        d = f"2026-10-{(i % 28) + 1:02d}" if i < 28 else f"2026-11-{i - 27:02d}"
        rows.append({"date": d, "graded": "2026-12-01", "model": "haiku", "side": "buy", "ticker": f"T{i}",
                     "validation": False, "xs_ctrl_1": 0.0005, "xs_ctrl_5": 0.0, "xs_ctrl_20": 0.0,
                     "xs_spy_1": 0.0, "xs_spy_5": 0.0, "xs_spy_20": 0.0, "was_trending_T": False, "flow_new_T1": False})
    (tmp_path / "grades.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    s = AH.summary()
    assert s["trading_days"] == 35 and s["kills"]["K2_no_price_effect_T1"] is True
    assert s["flow_new_T1_hit_rate"] == 0.0
