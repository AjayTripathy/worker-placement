"""us_broad_dislocation_sweep tests — OFFLINE (recorded/synthetic bars, no network).

The acceptance test is the SPGI REGRESSION: the July-August 2026 tape that ground -11.4% under
every screen the desk owned must fire this one. Everything else exists to keep that fire from
being bought with noise:

  1. the SPGI regression on RECORDED closes (and the documented fact that the 5d/21d
     point-to-point legs alone would still have missed it)
  2. grind21 guards — a market-wide slide, a 2-day break, and a single-session crash must NOT
     be re-reported here as slow grinds
  3. the 63d long-window leg + its raw-move floor (the beta-bleed error in long-window form)
  4. the bleed52 widening leg — fires while the gap opens, goes quiet when it stops
  5. universe construction: researched names excluded, class-share punctuation, degraded-loud
  6. fire-line contract: DETFIRE|us_broad_dislocation|..., UNRESEARCHED routing, doctrine verbatim
"""
import datetime
import json

import pytest

from verticals.generators import intl_dislocation_sweep as I
from verticals.generators import us_broad_dislocation_sweep as U


# --------------------------------------------------------------------------- helpers
def _bars(closes, start="2026-06-15"):
    """Synthetic series on a contiguous calendar grid (dates matter — the bench is date-aligned)."""
    d0 = datetime.date.fromisoformat(start)
    return {"close": [float(c) for c in closes],
            "dates": [(d0 + datetime.timedelta(days=i)).isoformat() for i in range(len(closes))]}


def _uni(sym="AAA", shelf="sp500"):
    return {sym: {"shelf": shelf, "bench": "SPY", "researched": False, "verdict": "UNRESEARCHED"}}


def _flat(n=30, level=100.0):
    return _bars([level] * n)


# --------------------------------------------------------------------------- 1. SPGI regression
# RECORDED closes, yfinance auto-adjust, pulled 2026-08-13. The window ends 2026-08-06 — the
# trough close of the slide (405.24, off a 457.38 high on 07-16 = -11.4%) with SPY up over the
# same span. 26 sessions is enough for the 5d / 21d / grind21 legs.
SPGI_DATES = ["2026-07-01", "2026-07-02", "2026-07-06", "2026-07-07", "2026-07-08", "2026-07-09",
              "2026-07-10", "2026-07-13", "2026-07-14", "2026-07-15", "2026-07-16", "2026-07-17",
              "2026-07-20", "2026-07-21", "2026-07-22", "2026-07-23", "2026-07-24", "2026-07-27",
              "2026-07-28", "2026-07-29", "2026-07-30", "2026-07-31", "2026-08-03", "2026-08-04",
              "2026-08-05", "2026-08-06"]
SPGI_CLOSE = [414.97, 439.89, 447.22, 443.46, 430.79, 432.96, 430.50, 437.84, 438.87, 444.48,
              457.38, 450.84, 448.35, 431.26, 429.06, 420.00, 426.40, 439.83, 424.36, 419.64,
              415.00, 411.93, 416.25, 412.53, 410.03, 405.24]
SPY_CLOSE = [745.76, 744.78, 751.28, 747.71, 745.40, 751.71, 754.95, 749.17, 751.83, 754.81,
             750.72, 743.29, 742.09, 748.28, 747.41, 738.18, 738.93, 739.09, 740.86, 729.46,
             741.69, 747.03, 757.67, 771.33, 769.79, 768.56]

SPGI_BARS = {"SPGI": {"dates": SPGI_DATES, "close": SPGI_CLOSE},
             "SPY": {"dates": SPGI_DATES, "close": SPY_CLOSE}}


def test_spgi_regression_the_sweep_fires_on_the_real_tape():
    """THE ACCEPTANCE TEST. -11.4% over 17 sessions, SPY flat, and nothing on the desk saw it."""
    hits, state, n = I.scan(SPGI_BARS, _uni("SPGI"), {}, "2026-08-06", legs=I.LEGS_ALL)
    assert n == 1, "SPGI must be screened, not skipped for thin history"
    assert len(hits) == 1, "the SPGI slide MUST fire the broad-US sweep"
    h = hits[0]
    assert h["severity"] in ("MED", "HIGH")
    assert "grind21" in h["legs"], f"the grind leg is the one that sees this shape: {h['legs']}"
    assert h["shape"] == "GRIND"
    assert h["excess_dd21_pct"] <= I.GRIND_MIN_EXCESS_DD21          # ≈ -11.0pp
    assert h["dd21_pct"] == pytest.approx(-11.4, abs=0.1)           # the -11.4% in the brief
    assert h["peak_date"] == "2026-07-16" and h["peak_age_sessions"] == 15
    assert state["SPGI"]["sev"] == h["severity"]


def test_spgi_would_still_have_been_missed_by_the_point_to_point_legs_alone():
    """WHY the grind leg had to exist. Closing only the UNIVERSE gap would not have caught SPGI:
    on its own tape the 21d point-to-point excess is ≈-9.0pp and the 5d ≈-6.0pp, both inside the
    -15/-8 gates dislocation_sweep and intl_dislocation_sweep use. Point-to-point is anchor-lucky
    — the t-21 anchor (2026-07-08) was itself already a local low, so the 07-16 peak is invisible
    to it. If this test ever starts failing, the grind leg has become redundant; until then it is
    the whole reason this module is not just a bigger universe."""
    hits, _, _ = I.scan(SPGI_BARS, _uni("SPGI"), {}, "2026-08-06", legs=("5d", "21d"))
    assert hits == []
    hits_all, _, _ = I.scan(SPGI_BARS, _uni("SPGI"), {}, "2026-08-06", legs=I.LEGS_ALL)
    assert hits_all[0]["excess21_pct"] > I.MIN_EXCESS_21            # ≈ -9.0, gate is -15
    assert hits_all[0]["excess5_pct"] > I.MIN_EXCESS_5              # ≈ -6.0, gate is -8


def test_spgi_fire_line_carries_the_grind_evidence_and_the_routing():
    hits, _, _ = I.scan(SPGI_BARS, _uni("SPGI"), {}, "2026-08-06", legs=I.LEGS_ALL)
    line = U.fire_line(hits[0])
    assert line.startswith("DETFIRE|us_broad_dislocation|SPGI|")
    assert "GRIND" in line and "off its 15-session-old high (2026-07-16)" in line
    assert "worst session -3.8%" in line                             # the not-a-break evidence
    assert "UNRESEARCHED" in line and "ENQUEUE-CANDIDATE" in line and "not a position" in line
    assert I.DOCTRINE in line and line.endswith(I.DOCTRINE)          # doctrine verbatim, and last
    assert "SECTOR" in line                                          # context sentence spliced in


# --------------------------------------------------------------------------- 2. grind21 guards
def test_grind_suppressed_when_the_whole_market_slid_with_it():
    """Peak-anchored beta-bleed: both the name and SPY are -12% off the same high."""
    slide = _bars([100] * 10 + [100 - 0.6 * i for i in range(20)])
    hits, _, n = I.scan({"AAA": slide, "SPY": slide}, _uni(), {}, "2026-08-13", legs=I.LEGS_ALL)
    assert n == 1 and hits == []


def test_grind_requires_the_high_to_be_old_enough_to_be_a_grind():
    """A high 2 sessions ago is a BREAK; broken_print_radar owns that and must not double-report."""
    two_day = _bars([100] * 27 + [100, 94, 88])          # peak_age = 2
    hits, _, _ = I.scan({"AAA": two_day, "SPY": _flat(30)}, _uni(), {}, "2026-08-13",
                        legs=("grind21",))
    assert hits == []
    # the SAME depth spread over 10 sessions IS a grind
    grind = _bars([100] * 20 + [100 - 1.5 * i for i in range(10)])
    hits2, _, _ = I.scan({"AAA": grind, "SPY": _flat(30)}, _uni(), {}, "2026-08-13",
                         legs=("grind21",))
    assert len(hits2) == 1 and hits2[0]["legs"] == ["grind21"]


def test_grind_refuses_a_window_containing_a_single_session_crash():
    """A -20% day inside the window makes this a break the radar already fired on."""
    crash = _bars([100] * 15 + [100, 80] + [79.5 - 0.2 * i for i in range(13)])
    hits, _, _ = I.scan({"AAA": crash, "SPY": _flat(30)}, _uni(), {}, "2026-08-13",
                        legs=("grind21",))
    assert hits == []


def test_grind_needs_a_real_drawdown_not_just_relative_weakness():
    """Flat name, ripping benchmark: -0.5% off its own high is not a dislocation at any excess."""
    flatish = _bars([100] * 25 + [99.5] * 5)
    ripping = _bars([100 + 0.8 * i for i in range(30)])
    hits, _, _ = I.scan({"AAA": flatish, "SPY": ripping}, _uni(), {}, "2026-08-13",
                        legs=("grind21",))
    assert hits == []


def test_grind_tiers_med_then_high():
    med = _bars([100] * 18 + [100 - 1.1 * i for i in range(12)])      # ≈ -12.1% dd
    high = _bars([100] * 18 + [100 - 1.7 * i for i in range(12)])     # ≈ -18.7% dd
    flat = _flat(30)
    assert I.scan({"AAA": med, "SPY": flat}, _uni(), {}, "2026-08-13",
                  legs=("grind21",))[0][0]["severity"] == "MED"
    assert I.scan({"AAA": high, "SPY": flat}, _uni(), {}, "2026-08-13",
                  legs=("grind21",))[0][0]["severity"] == "HIGH"


def test_bench_drawdown_is_peak_anchored_not_point_to_point():
    """The index's high need not fall on the stock's high. Measuring the benchmark point-to-point
    while measuring the stock peak-to-now compares two different questions and inflates the
    excess: here the index ends +5% on the span but is itself -4.5% off ITS high inside it."""
    stock = _bars([100] * 20 + [100 - 1.0 * i for i in range(10)])
    bench = _bars([100] * 20 + [100, 102, 104, 106, 108, 110, 108, 106, 105, 105])
    dd = I._drawdown(stock, I.MIN_BARS - 1)
    assert I._bench_drawdown(bench, dd["d_peak"], dd["d_now"]) == pytest.approx(-4.545, abs=0.01)
    assert I._bench_ret(bench, dd["d_peak"], dd["d_now"]) == pytest.approx(5.0, abs=0.01)
    # the leg uses the peak-anchored figure, so the excess is the smaller (honest) one
    out: dict = {}
    I._leg_grind21(stock, bench, out)
    assert out["excess_dd21_pct"] == pytest.approx(out["dd21_pct"] + 4.545, abs=0.05)


# --------------------------------------------------------------------------- 3. the 63d leg
def test_long_grind_that_no_21d_window_ever_sees_is_caught_by_the_63d_leg():
    """A 6-month -0.4%/day grinder: no 5d or 21d window ever looks bad enough to fire (the 21d
    point-to-point excess sits around -8pp against a flat benchmark, inside the -15 gate), but
    compounded over 63 sessions it is -22%."""
    n = 140
    grind = _bars([100 * (0.996 ** i) for i in range(n)])
    flat = _bars([100.0] * n)
    short_only, _, _ = I.scan({"AAA": grind, "SPY": flat}, _uni(), {}, "2026-08-13",
                              legs=("5d", "21d"))
    assert short_only == [], "the fixed short windows must miss this — that is the premise"
    hits, _, _ = I.scan({"AAA": grind, "SPY": flat}, _uni(), {}, "2026-08-13", legs=("63d",))
    assert len(hits) == 1 and hits[0]["legs"] == ["63d"] and hits[0]["shape"] == "GRIND"
    assert hits[0]["r63_pct"] <= I.MIN_RAW_63
    assert hits[0]["excess63_pct"] <= I.MIN_EXCESS_63


def test_63d_leg_refuses_to_fire_on_a_name_that_merely_lagged_a_ripping_tape():
    """The beta-bleed error in long-window form, and the reason for the raw floor: on 2026-06-30 a
    -14pp band with only a 'raw must be negative' guard fired 30% of the S&P 500 because SPY was
    +18.5%/63d. Flat is not a dislocation."""
    n = 90
    flatish = _bars([100 - 0.02 * i for i in range(n)])               # ≈ -1.8% raw over 63d
    ripping = _bars([100 * (1.004 ** i) for i in range(n)])           # ≈ +29% over 63d
    hits, _, _ = I.scan({"AAA": flatish, "SPY": ripping}, _uni(), {}, "2026-08-13", legs=("63d",))
    assert hits == []
    # the same excess with the name genuinely down 20% DOES fire
    falling = _bars([100 * (0.9965 ** i) for i in range(n)])
    hits2, _, _ = I.scan({"AAA": falling, "SPY": ripping}, _uni(), {}, "2026-08-13", legs=("63d",))
    assert len(hits2) == 1 and hits2[0]["r63_pct"] <= I.MIN_RAW_63


def test_63d_leg_is_silently_skipped_when_history_is_short_not_faked():
    short = _bars([100 - i for i in range(30)])
    hits, _, n = I.scan({"AAA": short, "SPY": _flat(30)}, _uni(), {}, "2026-08-13", legs=("63d",))
    assert n == 1 and hits == []                       # screened on 0 legs -> no fire, no invention


# --------------------------------------------------------------------------- 4. the bleed52 leg
def _widening_pair(n=200):
    """A name drifting steadily away from a flat benchmark: the gap opens every session, ~-5.3pp
    per 21 sessions, and no 5d/21d/63d window ever looks violent enough on its own."""
    return _bars([100 - 0.25 * i for i in range(n)]), _bars([100.0] * n)


def test_widening_bleed_fires_on_a_gap_that_is_still_opening():
    name, bench = _widening_pair()
    hits, _, _ = I.scan({"AAA": name, "SPY": bench}, _uni(), {}, "2026-08-13", legs=("bleed52",))
    assert len(hits) == 1
    h = hits[0]
    assert h["legs"] == ["bleed52"] and h["shape"] == "SLOW_BLEED"
    assert h["gap52_pct"] <= I.BLEED_GAP52
    assert h["gap52_widened_pp"] <= I.BLEED_WIDEN
    assert "SLOW_BLEED" in U.fire_line(h) and "WIDENING" in U.fire_line(h)


def test_stale_loser_whose_gap_stopped_opening_goes_quiet():
    """Without the widening test a name that fell once would re-fire forever. It fell; it is done."""
    fell = [100 * (0.995 ** i) for i in range(120)]
    name = _bars(fell + [fell[-1]] * 60)               # -45% then flat for 60 sessions
    bench = _bars([100.0] * 180)
    hits, _, n = I.scan({"AAA": name, "SPY": bench}, _uni(), {}, "2026-08-13", legs=("bleed52",))
    assert n == 1 and hits == [], "a gap that stopped widening is not news"


def test_bleed52_refuses_to_run_without_a_benchmark_rather_than_calling_drawdown_a_gap():
    """Unlike the other legs there is no honest raw fallback: without a benchmark the 'gap' is
    just drawdown-from-high, which is true of every name in a bear market."""
    name, _ = _widening_pair()
    uni = {"AAA": {"shelf": "sp500", "bench": None, "researched": False, "verdict": "UNRESEARCHED"}}
    hits, _, n = I.scan({"AAA": name}, uni, {}, "2026-08-13", legs=("bleed52",))
    assert n == 1 and hits == []


def test_dd_from_high_uses_only_bars_available_at_that_date():
    """The widening test compares now vs 21 sessions ago; a running high computed off the FULL
    series would leak the future into the 'before' reading and manufacture widening from nothing."""
    e = _bars([100] * 5 + [80] * 5 + [200] * 5, start="2026-01-01")
    early = e["dates"][4]
    assert I._dd_from_high(e, early, min_bars=1) == pytest.approx(0.0, abs=1e-9)
    assert I._dd_from_high(e, e["dates"][9], min_bars=1) == pytest.approx(-20.0, abs=1e-9)


# --------------------------------------------------------------------------- 5. universe
def test_researched_names_are_excluded_so_the_two_sweeps_never_double_fire(monkeypatch):
    monkeypatch.setattr(U, "sp500", lambda cache_only=False: (["AAA", "BBB", "CCC"], "2026-08-10"))
    monkeypatch.setattr(U, "cap_ladder", lambda refresh=False, size=0: (["CCC", "DDD"], "2026-08-10"))
    monkeypatch.setattr(U, "researched", lambda: {"BBB", "DDD"})
    uni, rep = U.load_universe()
    assert set(uni) == {"AAA", "CCC"}
    assert rep["excluded_already_researched"] == 2
    assert uni["AAA"]["shelf"] == "sp500" and uni["CCC"]["shelf"] == "sp500"   # first shelf wins
    assert all(m["bench"] == "SPY" and m["verdict"] == "UNRESEARCHED" for m in uni.values())


def test_class_share_punctuation_excludes_both_ways(monkeypatch):
    """BRK.B in the index list and BRK-B in the ledger are the same company."""
    monkeypatch.setattr(U, "sp500", lambda cache_only=False: (["BRK.B", "AAA"], "2026-08-10"))
    monkeypatch.setattr(U, "cap_ladder", lambda refresh=False, size=0: ([], "2026-08-10"))
    monkeypatch.setattr(U, "researched", lambda: {t for x in ["BRK-B"]
                                                  for t in (x, x.replace("-", "."))})
    uni, _ = U.load_universe()
    assert set(uni) == {"AAA"}


def test_index_tickers_are_translated_to_the_yahoo_class_share_convention(monkeypatch):
    monkeypatch.setattr(U, "sp500", lambda cache_only=False: (["BRK.B", "BF.B"], "2026-08-10"))
    monkeypatch.setattr(U, "cap_ladder", lambda refresh=False, size=0: ([], "2026-08-10"))
    monkeypatch.setattr(U, "researched", lambda: set())
    uni, _ = U.load_universe()
    assert set(uni) == {"BRK-B", "BF-B"}
    assert "BRK-B" in I.alt_symbols("BRK.B")            # and the ladder can recover it either way
    assert "BRK.B" in I.alt_symbols("BRK-B")
    assert I.alt_symbols("BP.L") == []                  # intl suffixes untouched


def test_sp500_list_is_present_and_plausible():
    """A silently empty constituent list would make this watch print 'quiet tape' forever."""
    rows, asof = U.sp500(cache_only=True)
    assert 450 <= len(rows) <= 520, len(rows)
    assert asof and asof != "?"


def test_degraded_loud_names_every_casualty_and_points_at_this_store():
    requested = [f"X{i}" for i in range(60)]
    line, rep = I.degraded_line(requested, {}, not_swept=[], gw_alive={}, name_cap=10,
                                store="US_BROAD_DISLOCATION_SWEEP.json")
    assert rep["degraded"] == 60 and len(rep["degraded_names"]) == 60
    assert "US_BROAD_DISLOCATION_SWEEP.json" in line and "+50 more" in line


# --------------------------------------------------------------------------- 6. contract / dedup
def test_state_refires_when_a_new_leg_joins_at_the_same_tier():
    """A name that was grinding and now also breaks on 5d is new information even at MED->MED."""
    grind = _bars([100] * 18 + [100 - 1.1 * i for i in range(12)])
    flat = _flat(30)
    hits, state, _ = I.scan({"AAA": grind, "SPY": flat}, _uni(), {}, "2026-08-13",
                            legs=("5d", "21d", "grind21"))
    assert hits[0]["legs"] == ["grind21"] and state["AAA"]["legs"] == ["grind21"]
    # same tape next day -> quiet
    assert I.scan({"AAA": grind, "SPY": flat}, _uni(), state, "2026-08-14",
                  legs=("5d", "21d", "grind21"))[0] == []
    # now a 5d break joins at the same tier -> fires again
    breaking = _bars(list(grind["close"][:-1]) + [grind["close"][-1] * 0.92])
    hits2, _, _ = I.scan({"AAA": breaking, "SPY": flat}, _uni(), state, "2026-08-14",
                         legs=("5d", "21d", "grind21"))
    assert len(hits2) == 1 and "5d" in hits2[0]["legs"] and hits2[0]["shape"] == "BREAK"


def test_a_lone_half_priced_session_is_labelled_a_suspected_split(monkeypatch):
    """First live run: MNST printed -50.6%/5d. A mega-cap does not halve in a session; an
    unadjusted split does. The fire is LABELLED (verify the CA history), never suppressed —
    dropping tape we do not understand is how a real break gets lost."""
    split = _bars([100] * 25 + [100, 50, 50, 49.5, 49])
    hits, _, _ = I.scan({"AAA": split, "SPY": _flat(30)}, _uni(), {}, "2026-08-13",
                        legs=I.LEGS_ALL)
    assert len(hits) == 1
    h = hits[0]
    assert h["suspect_corporate_action"] is True
    assert h["worst_session_21d_pct"] == pytest.approx(-50.0, abs=0.1)
    assert h["r21_pct"] > I.SUSPECT_R21, "the old -70%/21d rule alone would have missed this"
    line = U.fire_line(h)
    assert "SUSPECT" in line and "CORPORATE ACTION" in line and "single session of -50%" in line
    # a genuine multi-session grind of the same depth carries no such label
    grind = _bars([100] * 8 + [100 - 2.3 * i for i in range(22)])
    ok, _, _ = I.scan({"AAA": grind, "SPY": _flat(30)}, _uni(), {}, "2026-08-13", legs=I.LEGS_ALL)
    assert ok[0]["suspect_corporate_action"] is False and "SUSPECT" not in U.fire_line(ok[0])


def test_shape_labels():
    assert I.shape_of(["5d"]) == "BREAK" and I.shape_of(["21d", "grind21"]) == "BREAK"
    assert I.shape_of(["grind21"]) == "GRIND" and I.shape_of(["63d"]) == "GRIND"
    assert I.shape_of(["bleed52"]) == "SLOW_BLEED"


def test_sector_clause_is_honest_when_the_sector_is_unresolved():
    h = {"ticker": "AAA", "sector": "UNKNOWN", "sector_bench": "UNAVAILABLE"}
    assert "SECTOR CONTEXT UNAVAILABLE" in U.sector_clause(h)
    h2 = {"ticker": "AAA", "sector": "Financial Services", "sector_bench": "XLF",
          "sector_excess21_pct": -1.2}
    assert "vs XLF" in U.sector_clause(h2) and "the sector, not the name" in U.sector_clause(h2)
    assert "XLF" in U.sector_clause(h2, short=True)


def test_sector_context_attaches_a_date_aligned_sector_excess(monkeypatch):
    monkeypatch.setattr(U, "sector_etf", lambda sym, cache, budget: ("XLF", "Financial Services"))
    monkeypatch.setattr(U, "SECTOR_CACHE", U.DATA / "_test_sector_cache_should_not_be_written.json")
    bars = dict(SPGI_BARS)
    bars["XLF"] = {"dates": SPGI_DATES, "close": [c * 0.97 for c in SPGI_CLOSE]}  # sector fell too
    hits, _, _ = I.scan(SPGI_BARS, _uni("SPGI"), {}, "2026-08-06", legs=I.LEGS_ALL)
    n, status = U.attach_sector_context(hits, bars, seed=False)
    assert n == 1 and "seed skipped" in status
    h = hits[0]
    assert h["sector_bench"] == "XLF"
    # sector moved identically -> the name's excess vs its sector is ~0: this is the sector
    assert h["sector_excess21_pct"] == pytest.approx(0.0, abs=0.1)
    assert h["sector_excess_dd21_pct"] == pytest.approx(0.0, abs=0.1)
    U.SECTOR_CACHE.unlink(missing_ok=True)


def test_sector_lookup_is_budgeted_and_a_throttled_miss_is_not_cached(monkeypatch):
    """The first live run resolved 0 of 114 sectors: a burst of yfinance .info straight after an
    875-name history sweep trips YFRateLimitError for every name. Two invariants come out of it —
    the budget stops asking once throttled, and a throttled miss is NEVER written to the cache as
    'sector UNKNOWN' (that would make an infrastructure failure permanent)."""
    class _RL(Exception):
        pass
    _RL.__name__ = "YFRateLimitError"
    calls = []

    class _T:
        def __init__(self, sym):
            calls.append(sym)

        @property
        def info(self):
            raise _RL("Too Many Requests")

    monkeypatch.setattr(U, "SECTOR_INFO_PAUSE", 0)
    monkeypatch.setitem(__import__("sys").modules, "yfinance",
                        type("m", (), {"Ticker": _T, "__spec__": None})())
    cache: dict = {}
    budget = [5]
    for tk in ("AAA", "BBB", "CCC"):
        assert U.sector_etf(tk, cache, budget) == (None, "UNKNOWN")
    assert calls == ["AAA"], "the budget must zero out on the first rate-limit, not burn through"
    assert cache == {}, "a throttled miss is an INFRA failure, never a cached fact"


def test_sector_seed_uses_the_free_index_table_and_is_cached(monkeypatch):
    """The free path: the constituent table carries Symbol + GICS Sector, so ~500 names resolve
    for one HTTP GET a week and zero Yahoo quota."""
    html = ('<table class="wikitable"><tr><th>Symbol</th><th>Security</th><th>GICS Sector</th></tr>'
            '<tr><td><a href="/x">SPGI</a></td><td>S&amp;P Global</td><td>Financials</td></tr>'
            '<tr><td>BRK.B</td><td>Berkshire</td><td>Financials</td></tr>'
            '<tr><td>AAPL</td><td>Apple</td><td>Information Technology</td></tr></table>')

    class _R:
        def read(self):
            return html.encode()

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: _R())
    cache: dict = {}
    status = U.seed_sectors(cache)
    assert "seeded 3 names" in status
    assert cache["SPGI"] == {"etf": "XLF", "sector": "Financials", "src": "index_table",
                             "asof": datetime.date.today().isoformat()}
    assert cache["BRK-B"]["etf"] == "XLF"          # translated to the Yahoo class-share convention
    assert cache["AAPL"]["etf"] == "XLK"           # GICS vocabulary, not yfinance's
    # a second call inside the week does not refetch
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: (_ for _ in ()).throw(AssertionError))
    assert "cached seed" in U.seed_sectors(cache)
    # ...and a seeded name never spends the yfinance budget
    budget = [3]
    assert U.sector_etf("SPGI", cache, budget) == ("XLF", "Financials") and budget == [3]


def test_detfire_line_parses_through_the_shared_extractor():
    from desk import extractors
    hits, _, _ = I.scan(SPGI_BARS, _uni("SPGI"), {}, "2026-08-06", legs=I.LEGS_ALL)
    h = dict(hits[0], sector="Financial Services", sector_bench="XLF",
             sector_excess21_pct=-3.1, sector_excess_dd21_pct=-4.2)
    sigs = extractors.detector_scan(U.fire_line(h))
    assert len(sigs) == 1
    assert sigs[0]["source"] == "detector:us_broad_dislocation"
    assert sigs[0]["asset"] == "SPGI" and sigs[0]["needs_verification"] is True
    assert sigs[0]["severity"] in ("MED", "HIGH")
    # THE TRUNCATION CONTRACT: signals.make cuts evidence at 600 chars, and the doctrine sentence
    # is the tail. It must survive the round trip, or the desk reads a fire as a recommendation.
    assert sigs[0]["evidence"].endswith(I.DOCTRINE.strip())


def test_the_proposes_only_sentence_survives_even_the_longest_possible_fire():
    """Worst case: every leg fires, on a long ticker, with full sector context."""
    h = {"ticker": "GOOGL", "severity": "HIGH", "px": 12.3456, "suspect_corporate_action": True,
         "r5_pct": -12.3, "r21_pct": -88.8, "excess5_pct": -14.1, "excess21_pct": -90.2,
         "benchmark": "SPY", "shelf": "us_tape", "researched": False, "verdict": "UNRESEARCHED",
         "legs": ["21d", "5d", "63d", "bleed52", "grind21"], "shape": "BREAK",
         "dd21_pct": -33.3, "excess_dd21_pct": -32.9, "bench_dd21_pct": -0.4,
         "peak_age_sessions": 14, "worst_session_pct": -6.7, "peak_date": "2026-07-16",
         "r63_pct": -44.4, "excess63_pct": -49.5, "bench_r63_pct": 5.1,
         "dd52_pct": -61.2, "bench_dd52_pct": -0.3, "gap52_pct": -60.9, "gap52_widened_pp": -12.4,
         "sector": "Communication Services", "sector_bench": "XLC",
         "sector_excess21_pct": -55.5, "sector_excess_dd21_pct": -30.1}
    ev = U.fire_line(h).split("|", 4)[-1]
    assert len(ev) <= U.EVIDENCE_BUDGET, len(ev)
    assert ev.endswith(I.DOCTRINE.strip()) or ev.endswith(I.DOCTRINE)
    # the two clauses that must NEVER be what gets shed
    for token in ("SUSPECT", "CORPORATE ACTION", "ENQUEUE-CANDIDATE", "not a position"):
        assert token in ev, token
    # and the shed order is legs-before-routing: the compact leg form keeps every number
    compact = I.leg_clause(h, compact=True)
    assert "-32.9pp" in compact and "-49.5pp" in compact and "-60.9pp" in compact
    assert len(compact) < len(I.leg_clause(h))


def test_registered_in_the_desk_registry():
    from desk import registry
    w = [x for x in registry.WATCHES if x["name"] == "us_broad_dislocation_sweep"]
    assert len(w) == 1, "an unregistered watch is a watch that never runs"
    assert w[0]["enabled"] and w[0]["extractor"] == "detector_scan"
    assert w[0]["cadence"] in ("daily", "weekday")
    assert json.loads(json.dumps(w[0]))          # serialisable manifest row
