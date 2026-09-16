"""cohort_dislocation tests — OFFLINE (synthetic + one RECORDED tape, no network).

Covers what makes a cohort layer trustworthy rather than a theme-noise generator:
  1. aggregation math (median/breadth/ex-worst) and the date-aligned excess
  2. the breadth guard (a median carried by a minority must NOT fire)
  3. the single-name skew guard (fires, but capped at MED and labelled)
  4. degraded handling: unmapped/unpriced members are counted, never silently dropped
  5. THE REGRESSION: the financial-data-vendor cohort on the recorded 2026-08-12 tape — the
     de-rate every single-name screen missed — plus the proof that the coarse auto industry
     bucket (which mixes in the rallying exchanges) does NOT fire on the same tape.
"""
import datetime
import json
from pathlib import Path

import pytest

from verticals.generators import cohort_dislocation as C

GOLDEN = Path(__file__).parent / "golden" / "cohort_dislocation_datavendors_20260812.json"


def _bars(closes, start="2026-04-01"):
    """Contiguous daily grid — dates matter, the benchmark is looked up by date."""
    d0 = datetime.date.fromisoformat(start)
    return {"close": list(closes),
            "dates": [(d0 + datetime.timedelta(days=i)).isoformat() for i in range(len(closes))]}


def _tk(i, j):
    """Valid US-shaped ticker (letters only) — is_us_symbol rejects digits/underscores."""
    return "".join(chr(ord("A") + x) for x in (i // 26, i % 26, j))


def _flat(n=70, level=100.0):
    return _bars([level] * n)


def _drop(pct, n=70, level=100.0):
    """Flat, then a single-session move of `pct` — a clean 21d excess of `pct` vs a flat bench."""
    return _bars([level] * (n - 1) + [level * (1 + pct / 100)])


# ------------------------------------------------------------------ 1. aggregation math
def test_excess_is_date_aligned_and_benchmark_relative():
    bars, bench = _drop(-10), _drop(-4)
    assert C.excess_pct(bars, bench, 21) == pytest.approx(-6.0, abs=1e-6)


def test_excess_refuses_a_stale_benchmark():
    """A bench that stops 30 days before the member's anchor cannot anchor an excess."""
    bars = _drop(-10, n=70)
    bench = _bars([100] * 30, start="2026-04-01")      # ends long before the member's window
    assert C.excess_pct(bars, bench, 21) is None


def test_cohort_stats_median_breadth_and_ex_worst():
    ex = {"A": -20.0, "B": -7.0, "C": -6.0, "D": +2.0, "E": +9.0}
    st = C.cohort_stats(ex)
    assert st["n"] == 5
    assert st["median21"] == pytest.approx(-6.0)
    assert st["breadth21"] == pytest.approx(0.6)
    assert st["worst_member"] == "A" and st["worst21"] == pytest.approx(-20.0)
    # drop A -> [-7, -6, +2, +9] -> median (-6 + 2)/2 = -2.0
    assert st["ex_worst_median21"] == pytest.approx(-2.0)
    assert st["dispersion21"] == pytest.approx(29.0)


def test_member_floor_blocks_a_three_name_cohort():
    st = C.cohort_stats({"A": -30.0, "B": -25.0, "C": -20.0})
    v = C.evaluate(st)
    assert v["fires"] is False and "floor" in v["reason"]


# ------------------------------------------------------------------ 2. breadth guard
def test_breadth_guard_blocks_a_minority_driven_median():
    """Two names collapse, four rally: the mean would scream, the median+breadth must not fire."""
    ex = {"A": -40.0, "B": -35.0, "C": +5.0, "D": +6.0, "E": +7.0, "F": +8.0}
    v = C.evaluate(C.cohort_stats(ex))
    assert v["fires"] is False
    assert "breadth" in v["reason"] or "median21" in v["reason"]


def test_broad_uniform_derate_fires_high():
    ex = {"A": -14.0, "B": -13.0, "C": -12.5, "D": -12.0, "E": -11.0}
    v = C.evaluate(C.cohort_stats(ex))
    assert v["fires"] and v["severity"] == "HIGH" and v["skew"] is False and v["legs"] == ["21d"]


def test_63d_grind_leg_fires_when_the_21d_window_is_flat():
    st = C.cohort_stats({"A": -1.0, "B": -1.0, "C": -1.0, "D": +0.5},
                        {"A": -14.0, "B": -12.0, "C": -11.0, "D": -9.0})
    v = C.evaluate(st)
    assert v["fires"] and v["legs"] == ["63d"]


# ------------------------------------------------------------------ 3. skew guard
def test_single_name_skew_caps_severity_and_labels():
    """Deep enough for HIGH on the median, but the depth is one name — MED + SKEW."""
    ex = {"A": -45.0, "B": -13.0, "C": -12.0, "D": +1.0, "E": +3.0}
    st = C.cohort_stats(ex)
    v = C.evaluate(st)
    assert v["fires"] and v["skew"] is True
    assert v["severity"] == "MED", "a concentrated de-rate must never be sold to the court as HIGH"
    line = C.fire_line("narrative:x", {**st, "cohort": "narrative:x"}, v, None)
    assert "SKEW" in line and "CONCENTRATED" in line


# ------------------------------------------------------------------ 4. degraded / mapping
def test_unpriced_members_are_counted_not_silently_dropped():
    cohorts = {"narrative:t": ["AAA", "BBB", "CCC", "DDD", "EEE"]}
    bars = {"SPY": _flat(), "AAA": _drop(-12), "BBB": _drop(-11), "CCC": _drop(-10), "DDD": _drop(-9)}
    fires, _, cov = C.scan(cohorts, bars, {}, "2026-08-12")
    row = cov["evaluated"][0]
    assert row["n"] == 4 and row["unpriced"] == ["EEE"]
    assert fires and fires[0]["unpriced"] == ["EEE"]


def test_cohort_under_the_floor_is_reported_not_dropped():
    cohorts = {"narrative:t": ["AAA", "BBB", "CCC", "DDD"]}
    bars = {"SPY": _flat(), "AAA": _drop(-12), "BBB": _drop(-11)}
    fires, _, cov = C.scan(cohorts, bars, {}, "2026-08-12")
    assert fires == []
    assert cov["cohorts_below_member_floor"][0]["cohort"] == "narrative:t"
    assert cov["cohorts_below_member_floor"][0]["n"] == 2


def test_missing_benchmark_refuses_to_scan():
    with pytest.raises(RuntimeError, match="SPY"):
        C.scan({"narrative:t": ["AAA"]}, {"AAA": _drop(-12)}, {}, "2026-08-12")


def test_non_us_members_are_dropped_from_a_spy_benchmarked_cohort():
    cohorts = {"narrative:t": ["AAA", "BBB", "CCC", "DDD", "7203.T", "BRBY.L"]}
    bars = {"SPY": _flat(), **{t: _drop(-12) for t in ("AAA", "BBB", "CCC", "DDD")}}
    _, _, cov = C.scan(cohorts, bars, {}, "2026-08-12")
    assert cov["evaluated"][0]["dropped_non_us"] == ["7203.T", "BRBY.L"]


def test_unmapped_names_produce_no_auto_cohort():
    meta = {"AAA": {"mcap": 5e9}, "BBB": {"mcap": 5e9, "industry": ""},
            "CCC": {"mcap": 5e9, "industry": "Widgets"}, "DDD": {"mcap": 5e9, "industry": "Widgets"}}
    assert C.auto_cohorts(meta) == {}          # only 2 mapped Widgets < MIN_MEMBERS, rest unmapped


def test_auto_cohorts_respect_the_liquidity_floor():
    meta = {t: {"mcap": mc, "industry": "Widgets"} for t, mc in
            [("A", 5e9), ("B", 4e9), ("C", 3e9), ("D", 2e9), ("E", 5e8)]}
    assert C.auto_cohorts(meta)["industry:Widgets"] == ["A", "B", "C", "D"]


def test_curated_parser_rescues_the_top_level_cohort_slip():
    """The live cohorts.json has one cohort outside the "cohorts" key — a strict reader loses it."""
    blob = {"cohorts": {"a": {"members": ["X", "Y"]}}, "b": {"members": ["Z"]}, "_doc": "x"}
    got = C.parse_curated(blob)
    assert got == {"narrative:a": ["X", "Y"], "narrative:b": ["Z"]}


def test_sweep_context_tolerates_every_file_being_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "SWEEP_US", tmp_path / "nope.json")
    monkeypatch.setattr(C, "SWEEP_INTL", tmp_path / "nope2.json")
    monkeypatch.setattr(C, "DATA", tmp_path)
    ctx = C.load_sweep_context()
    assert "ABSENT" in ctx["files"]["DISLOCATION_SWEEP.json"]
    assert ctx["seed_tickers"] == set()


# ------------------------------------------------------------------ 5. best-in-class surfacing
def test_best_in_class_picks_the_largest_dragged_name_not_the_worst():
    ex = {"BIG": -7.0, "SMALL": -25.0, "MID": -8.0, "UP": +5.0}
    meta = {"BIG": {"mcap": 120e9, "cash": 2e9, "debt": 1e9},
            "SMALL": {"mcap": 1e9, "cash": 1e8, "debt": 3e9},
            "MID": {"mcap": 40e9, "cash": 5e8, "debt": 5e9}, "UP": {"mcap": 200e9}}
    b = C.best_in_class(ex, meta)
    assert b["ticker"] == "BIG"
    assert "UP" not in b["ranked"], "a member that RALLIED is not being dragged"
    assert b["net_cash"] == pytest.approx(1e9)


def test_missing_leverage_is_named_never_treated_as_clean():
    ex = {"A": -9.0, "B": -8.0}
    b = C.best_in_class(ex, {"A": {"mcap": 50e9}, "B": {"mcap": 10e9}})
    assert b["ticker"] == "A" and b["net_cash"] is None
    assert any("UNKNOWN" in g for g in b["data_gaps"])


def test_fire_line_grammar_and_proposes_only():
    st = C.cohort_stats({"A": -14.0, "B": -13.0, "C": -12.5, "D": -12.0, "E": -11.0})
    v = C.evaluate(st)
    best = C.best_in_class({"A": -14.0}, {"A": {"mcap": 30e9}})
    line = C.fire_line("narrative:data_vendors", st, v, best)
    head = line.split("|", 4)
    assert head[0] == "DETFIRE" and head[1] == "cohort_dislocation"
    assert head[2] == "narrative:data_vendors" and head[3] == "HIGH"
    assert "PROPOSES ONLY" in line and "court (v1.4)" in line
    assert "cohort de-rate: is A dislocated with its cohort or correctly repriced?" in line
    member = C.member_fire_line("narrative:data_vendors", v, best)
    assert member.split("|")[2] == "A" and "PROPOSES ONLY" in member


# ================================================================= THE REGRESSION (recorded tape)
def _golden_bars(names, upto="2026-08-12"):
    g = json.loads(GOLDEN.read_text())
    idx = [i for i, d in enumerate(g["dates"]) if d <= upto]
    return {n: {"dates": [g["dates"][i] for i in idx],
                "close": [g["close"][n][i] for i in idx]} for n in names}


VENDORS = ["SPGI", "MCO", "FDS", "MSCI", "MORN"]
AUTO_BUCKET = VENDORS + ["ICE", "NDAQ", "TRU"]      # what yfinance's industry label actually holds


def test_REGRESSION_financial_data_vendors_cohort_fires_on_the_recorded_tape():
    """The SPGI miss (2026-08-13). Each name individually sat under the single-name sweep's
    -15pp/21d bar; the COHORT median cleared -6pp with 60% breadth and nothing aggregated it."""
    bars = _golden_bars(VENDORS + ["SPY"])
    fires, _, cov = C.scan({"narrative:financial_data_vendors": VENDORS}, bars,
                           {t: {"mcap": mc} for t, mc in
                            [("SPGI", 124.6e9), ("MCO", 84.6e9), ("MSCI", 41.8e9),
                             ("FDS", 10.2e9), ("MORN", 7.8e9)]},
                           "2026-08-12")
    assert len(fires) == 1, f"cohort did not fire; evaluated={cov['evaluated']}"
    f = fires[0]
    assert f["n"] == 5
    assert f["median21"] == pytest.approx(-6.72, abs=0.05)
    assert f["breadth21"] == pytest.approx(0.6, abs=0.001)
    assert f["legs"] == ["21d"]

    # not one name individually past the single-name sweep's 21d bar -> the aggregate WAS the signal
    assert all(v > -15.0 for _, v in f["members_by_excess21"]), \
        "if a member cleared -15pp the old single-name sweep would have caught it"

    # the skew guard is honest about WHICH kind of de-rate this is
    assert f["skew"] is True and f["severity"] == "MED"
    assert f["ex_worst_median21"] == pytest.approx(-2.09, abs=0.05)

    # best-in-class dragged = SPGI (largest cap of the dragged three), with the court question
    assert f["best_in_class"]["ticker"] == "SPGI"
    assert f["court_question"] == ("cohort de-rate: is SPGI dislocated with its cohort or "
                                  "correctly repriced?")
    line = C.fire_line(f["cohort"], f, {"legs": f["legs"], "severity": f["severity"],
                                        "skew": f["skew"]}, f["best_in_class"])
    assert line.startswith("DETFIRE|cohort_dislocation|narrative:financial_data_vendors|MED|")
    assert "BEST-IN-CLASS DRAGGED: SPGI" in line and "PROPOSES ONLY" in line


def test_REGRESSION_coarse_auto_industry_bucket_does_NOT_fire_on_the_same_tape():
    """WHY the curated cohort exists. yfinance files the vendors together with the EXCHANGES under
    'Financial Data & Stock Exchanges'; on this tape ICE/NDAQ/TRU were rallying, so the auto
    bucket's median is positive and the real de-rate is averaged away. The auto leg is recall, the
    curated leg is precision — this test pins that the coarseness is a known, measured limit."""
    bars = _golden_bars(AUTO_BUCKET + ["SPY"])
    fires, _, cov = C.scan({"industry:Financial Data & Stock Exchanges": AUTO_BUCKET},
                           bars, {}, "2026-08-12")
    assert fires == []
    row = cov["evaluated"][0]
    assert row["n"] == 8 and row["median21"] > 0, \
        "the diluted bucket should look FLAT — that is the miss this layer documents"


def test_REGRESSION_vendor_cohort_is_quiet_earlier_in_the_summer():
    """Gate calibration: the same cohort must NOT fire on an ordinary mid-July tape, or the layer
    is a daily noise feed rather than a handful of theme events a year."""
    bars = _golden_bars(VENDORS + ["SPY"], upto="2026-07-17")
    fires, _, cov = C.scan({"narrative:financial_data_vendors": VENDORS}, bars, {}, "2026-07-17")
    assert fires == [], f"false positive on a quiet tape: {cov['evaluated']}"


def test_REGRESSION_state_dedup_suppresses_the_repeat_fire():
    bars = _golden_bars(VENDORS + ["SPY"])
    cohorts = {"narrative:financial_data_vendors": VENDORS}
    fires, state, _ = C.scan(cohorts, bars, {}, "2026-08-12")
    assert len(fires) == 1
    again, _, cov = C.scan(cohorts, bars, {}, "2026-08-13", state)
    assert again == [], "an unchanged cohort two days running must not re-fire"
    assert cov["evaluated"][0].get("suppressed_repeat") is True


def test_episode_dedup_collapses_the_recorded_may_selloff():
    """The May 2026 vendor de-rate is ONE episode. Gating on severity alone emitted six fires as
    the median oscillated across the HIGH boundary; the deepening rule must collapse them."""
    g = json.loads(GOLDEN.read_text())
    state, events = {}, []
    for k in range(22, len(g["dates"]) + 1):
        d = g["dates"][k - 1]
        if d > "2026-05-31":
            break
        bars = {n: {"dates": g["dates"][:k], "close": g["close"][n][:k]} for n in VENDORS + ["SPY"]}
        f, state, _ = C.scan({"narrative:financial_data_vendors": VENDORS}, bars, {}, d, state)
        events += [x["fired"] for x in f]
    assert len(events) <= 3, f"May episode fragmented into {len(events)} fires: {events}"
    assert events and events[0] == "2026-05-01"


def test_a_material_deepening_re_fires_inside_the_quiet_window():
    cohorts = {"narrative:t": ["AAA", "BBB", "CCC", "DDD"]}
    shallow = {"SPY": _flat(), **{t: _drop(-7) for t in ("AAA", "BBB", "CCC", "DDD")}}
    fires, state, _ = C.scan(cohorts, shallow, {}, "2026-08-01")
    assert len(fires) == 1
    deeper = {"SPY": _flat(), **{t: _drop(-14) for t in ("AAA", "BBB", "CCC", "DDD")}}
    again, _, _ = C.scan(cohorts, deeper, {}, "2026-08-04", state)
    assert len(again) == 1 and again[0]["median21"] == pytest.approx(-14.0, abs=0.01)


def test_regime_guard_flags_a_broad_rotation():
    """Many cohorts clearing at once is rotation, not twenty independent themes."""
    cohorts = {f"industry:c{i}": [_tk(i, j) for j in range(4)] for i in range(10)}
    bars = {"SPY": _flat()}
    for i in range(10):
        for j in range(4):
            bars[_tk(i, j)] = _drop(-12 if i < 5 else +3)
    fires, _, cov = C.scan(cohorts, bars, {}, "2026-08-12")
    assert cov["regime_warning"] is True and cov["gate_clearing"] == 5
    assert all(f["regime_warning"] for f in fires)
    line = C.fire_line("industry:c0", fires[0], {"legs": ["21d"], "severity": "HIGH", "skew": False},
                       None, "REGIME WARNING: rotation")
    assert "REGIME WARNING" in line


def test_auto_bucket_duplicating_a_curated_cohort_is_suppressed():
    """The first live run fired the identical five vendors twice, under both cohort names."""
    members = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    cohorts = {"narrative:vendors": members, "industry:Some Bucket": members}
    bars = {"SPY": _flat(), **{t: _drop(-12) for t in members}}
    fires, state, cov = C.scan(cohorts, bars, {}, "2026-08-13")
    assert [f["cohort"] for f in fires] == ["narrative:vendors"]
    dup = [r for r in cov["evaluated"] if r["cohort"] == "industry:Some Bucket"][0]
    assert dup["suppressed_duplicate_of"] == "narrative:vendors"
    # the suppressed twin still holds state, so it cannot fire as "new" tomorrow
    assert "industry:Some Bucket" in state


def test_a_genuinely_distinct_auto_cohort_is_not_suppressed():
    cohorts = {"narrative:vendors": ["AAA", "BBB", "CCC", "DDD"],
               "industry:Other": ["EEE", "FFF", "GGG", "HHH"]}
    bars = {"SPY": _flat(), **{t: _drop(-12) for t in
                               ("AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH")}}
    fires, _, _ = C.scan(cohorts, bars, {}, "2026-08-13")
    assert sorted(f["cohort"] for f in fires) == ["industry:Other", "narrative:vendors"]


def test_regime_guard_quiet_when_one_theme_fires_alone():
    cohorts = {f"industry:c{i}": [_tk(i, j) for j in range(4)] for i in range(10)}
    bars = {"SPY": _flat()}
    for i in range(10):
        for j in range(4):
            bars[_tk(i, j)] = _drop(-12 if i == 0 else +3)
    _, _, cov = C.scan(cohorts, bars, {}, "2026-08-12")
    assert cov["regime_warning"] is False and cov["gate_clearing"] == 1
