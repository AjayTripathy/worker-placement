"""intl_dislocation_sweep tests — OFFLINE (synthetic bars, no network).

Covers the four things that make this watch trustworthy rather than noisy:
  1. threshold fire logic vs the LOCAL index (beta-bleed suppression + the raw fallback)
  2. degraded-LOUD counting (no-data / thin-history / not-swept are all named, never silent)
  3. new-vs-deepened state dedup
  4. UNRESEARCHED vs ledger tagging (and the enqueue-candidacy routing language)
"""
import datetime
import json

import pytest

from verticals.generators import intl_dislocation_sweep as S


def _bars(closes, start="2026-06-15"):
    """Synthetic daily series on a CONTIGUOUS calendar grid (dates matter: the bench is date-aligned)."""
    d0 = datetime.date.fromisoformat(start)
    return {"close": list(closes),
            "dates": [(d0 + datetime.timedelta(days=i)).isoformat() for i in range(len(closes))]}


def _flat(n=30, level=100.0):
    return _bars([level] * n)


def _uni(sym="AAA.L", bench="^FTSE", researched=False, verdict=None, shelf="lse_universe"):
    return {sym: {"shelf": shelf, "bench": bench, "researched": researched,
                  "verdict": verdict or ("HOLD" if researched else "UNRESEARCHED")}}


# ------------------------------------------------------------------ 1. threshold fire logic
def test_idiosyncratic_drop_fires_vs_local_index():
    bars = {"AAA.L": _bars([100] * 25 + [100, 100, 100, 100, 80]),   # -20% on the last session
            "^FTSE": _flat()}
    hits, state, n = S.scan(bars, _uni(), {}, "2026-08-11")
    assert n == 1 and len(hits) == 1
    h = hits[0]
    assert h["severity"] == "HIGH" and h["benchmark"] == "^FTSE"
    assert h["excess5_pct"] == pytest.approx(-20.0, abs=0.1)


def test_market_wide_selloff_is_suppressed():
    """The name fell 20% and so did its index — beta, not a dislocation."""
    bars = {"AAA.L": _bars([100] * 29 + [80]), "^FTSE": _bars([100] * 29 + [80])}
    hits, _, n = S.scan(bars, _uni(), {}, "2026-08-11")
    assert n == 1 and hits == []


def test_med_vs_high_tiers():
    med = {"AAA.L": _bars([100] * 29 + [91]), "^FTSE": _flat()}          # -9%/5d
    high = {"AAA.L": _bars([100] * 29 + [86]), "^FTSE": _flat()}         # -14%/5d
    assert S.scan(med, _uni(), {}, "2026-08-11")[0][0]["severity"] == "MED"
    assert S.scan(high, _uni(), {}, "2026-08-11")[0][0]["severity"] == "HIGH"


def test_shallow_drop_does_not_fire():
    bars = {"AAA.L": _bars([100] * 29 + [95]), "^FTSE": _flat()}          # -5%: inside both gates
    assert S.scan(bars, _uni(), {}, "2026-08-11")[0] == []


def test_moonshot_pullback_excluded():
    """+30% over 21d then a hard 5d fade is a pullback, not cheapness."""
    bars = {"AAA.L": _bars([100] * 25 + [150, 150, 150, 150, 130]), "^FTSE": _flat()}
    assert S.scan(bars, _uni(), {}, "2026-08-11")[0] == []


def test_missing_benchmark_falls_back_to_raw_and_says_so():
    bars = {"AAA.XX": _bars([100] * 29 + [80])}                            # no bench series at all
    uni = _uni("AAA.XX", bench=None, shelf="euronext_universe")
    hits, _, _ = S.scan(bars, uni, {}, "2026-08-11")
    assert len(hits) == 1 and hits[0]["benchmark"] == "UNAVAILABLE(raw)"
    assert "UNAVAILABLE(raw)" in S.fire_line(hits[0])


def test_thin_history_is_never_screened():
    bars = {"AAA.L": _bars([100] * 10 + [50]), "^FTSE": _flat()}           # < MIN_BARS sessions
    hits, _, n = S.scan(bars, _uni(), {}, "2026-08-11")
    assert n == 0 and hits == []


def test_a_name_that_rose_is_never_a_dislocation():
    """RAW-DROP GUARD (from the first live run): +7.4%/5d vs a +15.9%/5d index is relative
    weakness, not a dislocation — it must not fire."""
    bars = {"AAA.KQ": _bars([100] * 29 + [107.4]),
            "^KQ11": _bars([100] * 29 + [115.9])}
    uni = _uni("AAA.KQ", bench="^KQ11", shelf="krx_universe")
    hits, _, n = S.scan(bars, uni, {}, "2026-08-11")
    assert n == 1 and hits == []
    # …but the same excess with the name actually DOWN does fire
    bars["AAA.KQ"] = _bars([100] * 29 + [92])
    bars["^KQ11"] = _bars([100] * 29 + [101])
    assert len(S.scan(bars, uni, {}, "2026-08-11")[0]) == 1


def test_benchmark_is_date_aligned_not_positionally_aligned():
    """The index grid differs from the tape grid (holidays / missing days). Positional alignment
    reads a 5-session stock window against a 7-session index window and manufactures excess."""
    stock = _bars([100] * 29 + [95], start="2026-07-01")             # dates 07-01..07-30
    bench = {"close": [100] * 12 + [96, 93, 90],                      # falls only in the last week
             "dates": [(datetime.date.fromisoformat("2026-07-01") + datetime.timedelta(days=i)).isoformat()
                       for i in range(0, 30, 2)]}                     # every OTHER day: 07-01..07-29
    bm = S._bench_moves(bench, S._moves(stock)[3])
    assert bm is not None
    # date-aligned: t-5 anchor = 2026-07-25 -> bench 96; now -> bench 90  =>  -6.25%
    assert bm[0] == pytest.approx((90 / 96 - 1) * 100, abs=0.01)
    # positional alignment would have read close[-6] (2026-07-19, still 100) => -10%, a 3.75pp
    # phantom on the excess of every name on that grid
    assert bm[0] > (90 / 100 - 1) * 100


def test_stale_benchmark_is_refused_not_stretched():
    stock = _bars([100] * 29 + [80], start="2026-07-01")
    stale = _bars([100] * 30, start="2026-05-01")                    # ends long before the stock
    assert S._bench_moves(stale, S._moves(stock)[3]) is None
    hits, _, _ = S.scan({"AAA.L": stock, "^FTSE": stale}, _uni(), {}, "2026-08-11")
    assert hits[0]["benchmark"] == "UNAVAILABLE(raw)"                 # raw, and labelled raw


def test_implausible_move_is_labelled_a_suspected_corporate_action():
    """First live run: 49GP.L printed -99%/21d — a consolidation stub, not a break. It still fires
    (we don't silently drop tape), but the line says SUSPECT and names the check."""
    bars = {"AAA.L": _bars([100] * 29 + [1]), "^FTSE": _flat()}
    hits, _, _ = S.scan(bars, _uni(), {}, "2026-08-11")
    assert hits[0]["suspect_corporate_action"] is True
    line = S.fire_line(hits[0])
    assert "SUSPECT" in line and "CORPORATE ACTION" in line and S.DOCTRINE in line
    # a normal-sized break carries no such label
    ok, _, _ = S.scan({"AAA.L": _bars([100] * 29 + [80]), "^FTSE": _flat()}, _uni(), {}, "2026-08-11")
    assert ok[0]["suspect_corporate_action"] is False and "SUSPECT" not in S.fire_line(ok[0])


def test_bench_symbol_map():
    assert S.bench_symbol("7203.T") == "^N225"
    assert S.bench_symbol("BP.L") == "^FTSE"
    assert S.bench_symbol("005930.KS") == "^KS11" and S.bench_symbol("241710.KQ") == "^KQ11"
    assert S.bench_symbol("AI.PA") == "^STOXX" and S.bench_symbol("CTM.ST") == "^OMX"
    assert S.bench_symbol("FOO.ZZ") is None


# ------------------------------------------------------------------ 2. degraded-LOUD counting
def test_degraded_loud_counts_and_names_every_casualty():
    requested = ["A.L", "B.L", "C.L", "D.L"]
    bars = {"A.L": _flat(), "B.L": _bars([100] * 5)}       # B thin, C absent, D never swept
    line, rep = S.degraded_line(requested, bars, not_swept=["D.L"], gw_alive={})
    assert rep == {"requested": 4, "priced": 1, "degraded": 3, "unpriced_no_data": 1,
                   "thin_history": 1, "not_swept_time_budget": 1, "gw_probe": "not attempted",
                   "gw_alive_no_history": [], "degraded_names": ["B.L", "C.L", "D.L"]}
    assert line.startswith("DEGRADED-LOUD: 1 of 4 priced; 3 DEGRADED")
    for tk in ("B.L", "C.L", "D.L"):
        assert tk in line                                   # named, not counted-and-forgotten


def test_gateway_alive_names_are_flagged_as_infra_failure():
    line, rep = S.degraded_line(["A.L", "B.L"], {"A.L": _flat()}, not_swept=[],
                                gw_alive={"B.L": {"px": 12.3, "venue": "LSE"}},
                                gw_status="ran on 1 name(s) across 1 venue(s)")
    assert rep["gw_alive_no_history"] == ["B.L"]
    assert "QUOTE LIVE at the IBKR gateway" in line and "INFRA failure" in line


def test_probe_that_never_ran_is_not_reported_as_probe_found_nothing():
    """'the gateway said no' and 'we never asked' are different facts — the line must say which."""
    ran, _ = S.degraded_line(["A.L"], {}, [], {}, gw_status="ran on 1 name(s) across 1 venue(s)")
    never, rep = S.degraded_line(["A.L"], {}, [], {},
                                 gw_status="NOT RUN (desk.gw_quotes unimportable: ImportError)")
    assert "ran on 1 name(s)" in ran and "0 alive" in ran
    assert "NOT RUN" in never and rep["gw_probe"].startswith("NOT RUN")


def test_degraded_names_truncate_but_point_at_the_store():
    requested = [f"X{i}.L" for i in range(60)]
    line, rep = S.degraded_line(requested, {}, not_swept=[], gw_alive={}, name_cap=10)
    assert rep["degraded"] == 60 and len(rep["degraded_names"]) == 60
    assert "+50 more" in line and "INTL_DISLOCATION_SWEEP.json" in line


def test_unpriced_name_can_never_pass_as_quiet():
    """The core degraded-loud invariant: a name with no bars is absent from hits AND from priced."""
    requested = ["A.L", "B.L"]
    bars = {"A.L": _flat()}
    hits, _, n = S.scan(bars, {**_uni("A.L"), **_uni("B.L")}, {}, "2026-08-11")
    _, rep = S.degraded_line(requested, bars, [], {})
    assert n == 1 and hits == [] and rep["priced"] == 1 and rep["degraded_names"] == ["B.L"]


# ------------------------------------------------------------------ 3. state dedup
def test_repeat_fire_suppressed_then_deepening_refires():
    bars = {"AAA.L": _bars([100] * 29 + [91]), "^FTSE": _flat()}          # MED
    hits, state, _ = S.scan(bars, _uni(), {}, "2026-08-11")
    assert len(hits) == 1 and state["AAA.L"]["sev"] == "MED"
    # same tier, next day -> quiet
    assert S.scan(bars, _uni(), state, "2026-08-12")[0] == []
    # deepens to HIGH -> fires again
    deeper = {"AAA.L": _bars([100] * 29 + [80]), "^FTSE": _flat()}
    hits2, state2, _ = S.scan(deeper, _uni(), state, "2026-08-12")
    assert len(hits2) == 1 and hits2[0]["severity"] == "HIGH" and state2["AAA.L"]["sev"] == "HIGH"


def test_same_tier_refires_after_the_quiet_window():
    bars = {"AAA.L": _bars([100] * 29 + [91]), "^FTSE": _flat()}
    _, state, _ = S.scan(bars, _uni(), {}, "2026-07-01")
    assert S.scan(bars, _uni(), state, "2026-07-10")[0] == []             # inside ~15 calendar days
    assert len(S.scan(bars, _uni(), state, "2026-07-25")[0]) == 1         # window elapsed


def test_recovery_rearms_the_name():
    bars = {"AAA.L": _bars([100] * 29 + [91]), "^FTSE": _flat()}
    _, state, _ = S.scan(bars, _uni(), {}, "2026-08-11")
    recovered = {"AAA.L": _flat(), "^FTSE": _flat()}
    _, state2, _ = S.scan(recovered, _uni(), state, "2026-08-12")
    assert "AAA.L" not in state2
    assert len(S.scan(bars, _uni(), state2, "2026-08-13")[0]) == 1        # can fire fresh again


# ------------------------------------------------------------------ 4. researched vs unresearched
def test_unresearched_fire_routes_to_enqueue_candidacy():
    bars = {"AAA.L": _bars([100] * 29 + [80]), "^FTSE": _flat()}
    hits, _, _ = S.scan(bars, _uni(researched=False), {}, "2026-08-11")
    line = S.fire_line(hits[0])
    assert line.startswith("DETFIRE|intl_dislocation|AAA.L|HIGH|")
    assert hits[0]["researched"] is False and "UNRESEARCHED" in line
    assert "ENQUEUE-CANDIDATE" in line and "not a position" in line
    assert S.DOCTRINE in line                                             # doctrine sentence verbatim


def test_researched_fire_routes_to_re_underwrite():
    bars = {"AAA.L": _bars([100] * 29 + [80]), "^FTSE": _flat()}
    hits, _, _ = S.scan(bars, _uni(researched=True, verdict="STARTER"), {}, "2026-08-11")
    line = S.fire_line(hits[0])
    assert "STARTER (ledger" in line and "re-underwrite" in line
    assert "ENQUEUE-CANDIDATE" not in line and S.DOCTRINE in line


def test_dead_verdict_names_are_dropped_from_the_universe(tmp_path):
    src = tmp_path / "shelf.json"
    src.write_text(json.dumps({"rows": [{"sym": "AAA.L"}, {"sym": "BBB.L"}, {"sym": "CCC.L"}]}))
    ledger = {"AAA.L": "PASS", "BBB.L": "STARTER"}
    uni = S.load_universe([("test_shelf", src, "rows", "sym")], ledger=ledger)
    assert set(uni) == {"BBB.L", "CCC.L"}
    assert uni["BBB.L"]["researched"] is True and uni["BBB.L"]["verdict"] == "STARTER"
    assert uni["CCC.L"]["researched"] is False and uni["CCC.L"]["verdict"] == "UNRESEARCHED"
    assert uni["BBB.L"]["shelf"] == "test_shelf" and uni["BBB.L"]["bench"] == "^FTSE"


def test_universe_dedupes_and_keeps_the_first_shelf_tag(tmp_path):
    a = tmp_path / "a.json"; a.write_text(json.dumps({"rows": [{"sym": "AAA.L"}]}))
    b = tmp_path / "b.json"; b.write_text(json.dumps({"AAA.L": {}, "BBB.T": {}}))
    uni = S.load_universe([("first", a, "rows", "sym"), ("second", b, None, None)], ledger={})
    assert uni["AAA.L"]["shelf"] == "first" and uni["BBB.T"]["shelf"] == "second"
    assert uni["BBB.T"]["bench"] == "^N225"


# ------------------------------------------------------------------ fallback ladder helpers
def test_alt_symbols_covers_the_kospi_kosdaq_mislabel_and_dash_forms():
    assert "005930.KQ" in S.alt_symbols("005930.KS")
    assert "241710.KS" in S.alt_symbols("241710.KQ")
    assert "BRK.B" in S.alt_symbols("BRK-B")
    assert S.alt_symbols("BP.L") == []                       # nothing plausible to try


def test_real_sources_exist_and_have_symbols():
    """The stored shelves this watch is built on must actually be there (a silent empty universe
    is exactly the failure mode this whole module exists to prevent)."""
    found = [tag for tag, path, _, _ in S.SOURCES if path.exists()]
    assert len(found) >= 6, found
    uni = S.load_universe(ledger={})
    assert len(uni) > 3000
    assert sum(1 for m in uni.values() if m["bench"]) > 0.8 * len(uni)
