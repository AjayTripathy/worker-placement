"""Tests for the CONSUMER PRODUCTS LANE (consumer_product_heat + consumer_product_reviews).

Offline only — no network. Covers:
  * the scoring math (trend acceleration, heat-score union + renormalization)
  * the cohort-delta arithmetic and the velocity/trajectory guards
  * degraded-loud behaviour: an unfetchable source must lower confidence and be NAMED, never
    imputed to zero, and never silently dropped
  * APPLIES_TO dispatch: matches a consumer SIC, does NOT match an industrial one
"""
from __future__ import annotations

import json

import pytest

from knowledge_graph.dispatch import _matches, relevant_for_issuer
from verticals.buyside_dd.connectors import consumer_product_heat as cph
from verticals.buyside_dd.connectors import consumer_product_reviews as cpr


# ── trend acceleration math ─────────────────────────────────────────────────────────────────
def test_trend_stats_rising_flat_decaying():
    flat = cph.trend_stats([{"value": 50} for _ in range(20)])
    assert flat["direction"] == "FLAT" and flat["ratio"] == 1.0

    rising = cph.trend_stats([{"value": 40}] * 13 + [{"value": 60}] * 4)
    assert rising["direction"] == "RISING" and rising["ratio"] == 1.5

    decaying = cph.trend_stats([{"value": 80}] * 13 + [{"value": 40}] * 4)
    assert decaying["direction"] == "DECAYING" and decaying["ratio"] == 0.5


def test_trend_stats_refuses_short_history():
    s = cph.trend_stats([{"value": 10}, {"value": 12}, {"value": 14}])
    assert s["direction"] == "INSUFFICIENT_HISTORY"
    assert s["ratio"] is None                      # no ratio invented from 3 points
    assert cph.trend_stats([])["direction"] == "NO_DATA"


def test_yoy_seasonal_control_is_computed_on_a_12m_series():
    """A whole cohort printing DECAYING in August is a calendar artifact; the YoY read is the
    like-for-like control and must exist on a 52-week series."""
    seasonal = [{"value": v} for v in ([30] * 4 + [70] * 44 + [45] * 4)]   # 52 weekly points
    s = cph.trend_stats(seasonal)
    assert s["direction"] == "DECAYING"          # vs the peak-summer trailing baseline
    assert s["yoy_ratio"] == pytest.approx(1.5)  # but +50% vs the SAME weeks last year
    assert s["yoy_direction"] == "RISING"
    # short series must NOT fabricate a YoY
    assert "yoy_ratio" not in cph.trend_stats([{"value": 50}] * 20)


def test_yoy_anchors_on_timestamps_not_series_start():
    """A 5-year request must not compare to 2021 under a YoY label."""
    wk = 7 * 86400
    t0 = 1_600_000_000
    # 5 years of weekly points: 2021 level 10, last-year window 40, now 20
    pts = [{"ts": t0 + i * wk, "value": 10} for i in range(206)]
    for i in range(206, 210):                      # the 4 weeks ~52w before the end
        pts.append({"ts": t0 + i * wk, "value": 40})
    for i in range(210, 262):
        pts.append({"ts": t0 + i * wk, "value": 20 if i >= 258 else 30})
    s = cph.trend_stats(pts)
    assert s["yoy_ratio"] == pytest.approx(0.5, abs=0.01)   # 20 vs 40, NOT 20 vs 10
    assert s["yoy_direction"] == "DECAYING"
    assert s["yoy_anchor"] is not None


def test_trend_slope_sign_and_peak():
    s = cph.trend_stats([{"value": 50}] * 13 + [{"value": v} for v in (40, 35, 30, 25)])
    assert s["slope_pct_per_week"] < 0
    assert s["peak"] == 50 and s["last_vs_peak"] == 0.5


# ── heat score: union, symmetry, renormalization, no zero-imputation ────────────────────────
def test_heat_score_is_log_symmetric_around_flat():
    flat = cph.heat_score({"ratio": 1.0}, None, None)
    up = cph.heat_score({"ratio": 2.0}, None, None)
    down = cph.heat_score({"ratio": 0.5}, None, None)
    assert flat["score"] == pytest.approx(50.0, abs=0.5)
    assert up["score"] > 90 and down["score"] < 10
    assert (up["score"] - 50) == pytest.approx(50 - down["score"], abs=0.5)


def test_heat_score_renormalizes_and_never_imputes_zero():
    stats = {"ratio": 1.0}
    full = cph.heat_score(stats, {"state": "OK", "velocity": 1.0}, {"status": "OK", "best_rank": 10})
    partial = cph.heat_score(stats, None, {"status": "FETCH_ERROR"})
    assert full["confidence"] == 1.0 and full["degraded"] == []
    # a dead channel must not drag the score toward zero — it is renormalized away, loudly
    assert partial["degraded"] == ["retail", "social"]
    assert partial["confidence"] == pytest.approx(cph.CHANNEL_WEIGHT["search"])
    assert partial["score"] == pytest.approx(50.0, abs=0.5)
    assert "DEGRADED" in partial["note"]


def test_heat_score_all_channels_dead_returns_none_not_zero():
    h = cph.heat_score({"ratio": None}, {"state": "ERROR"}, {"status": "HTTP_403"})
    assert h["score"] is None and h["confidence"] == 0.0
    assert set(h["degraded"]) == {"search", "social", "retail"}
    assert "not a zero" in h["note"]


def test_absent_from_reddit_is_an_observation_not_a_gap():
    """absence-is-observation (inherited from reddit_mentions): ABSENT scores, ERROR degrades."""
    assert cph._social_component({"state": "ABSENT"}) == 35.0
    assert cph._social_component({"state": "ERROR"}) is None


def test_retail_component_distinguishes_unranked_from_unfetchable():
    assert cph._retail_component({"status": "OK", "best_rank": 1}) == 100.0
    assert cph._retail_component({"status": "OK", "best_rank": None}) == 20.0   # present, unranked
    assert cph._retail_component({"status": "EMPTY_PARSE"}) is None             # could not read


# ── brand-identity gate (entity resolution before you trust the hit) ────────────────────────
def test_brand_tokens_drop_generic_product_nouns():
    toks = cph.brand_tokens("SUJA")
    assert "suja" in toks and "juice" not in toks and "soda" not in toks
    assert cph.brand_tokens("LWAY") == ["lifeway"]        # never bare 'kefir'


def test_excluded_ticker_is_refused_not_scored():
    assert "CPRT" in cph.EXCLUDED
    row = cph.read_brand("CPRT")                          # no network: returns before any fetch
    assert row["status"] == "OUT_OF_LANE"


# ── review trajectory math ──────────────────────────────────────────────────────────────────
def test_implied_cohort_rating_is_exact():
    # 100 reviews @4.50 -> 200 @4.60 means the 100 NEW ones averaged 4.70
    assert cpr.implied_cohort_rating(4.5, 100, 4.6, 200) == 4.7
    # a collapsing cohort is visible long before the lifetime mean moves
    assert cpr.implied_cohort_rating(4.6, 1000, 4.55, 1100) == pytest.approx(4.05, abs=0.01)


def test_implied_cohort_rating_refuses_impossible_inputs():
    assert cpr.implied_cohort_rating(4.5, 100, 4.6, 100) is None      # no new reviews
    assert cpr.implied_cohort_rating(4.5, 100, 4.6, 90) is None       # purge, not a signal
    assert cpr.implied_cohort_rating(4.5, 1000, 4.6, 1001) is None    # rounding blow-up guarded


def test_reviews_per_month_and_guards():
    assert cpr.reviews_per_month(100, 130, 30.4375) == 30.0
    assert cpr.reviews_per_month(100, 130, 0) is None
    assert cpr.reviews_per_month(100, 90, 30) is None


def test_trajectory_flag_direction_and_low_n_floor():
    assert cpr.trajectory_flag(4.8, 4.6, 50)["flag"] == "IMPROVING"
    assert cpr.trajectory_flag(4.6, 4.6, 50)["flag"] == "STABLE"
    assert cpr.trajectory_flag(4.3, 4.6, 50)["flag"] == "DETERIORATING"
    assert cpr.trajectory_flag(3.0, 4.6, 2)["flag"] == "LOW_N"        # 2 reviews claim nothing
    assert cpr.trajectory_flag(None, 4.6)["flag"] == "NO_COHORT"


def test_aggregate_is_review_weighted_not_sku_averaged():
    agg = cpr.aggregate_products([
        {"lifetime_rating": 4.6, "n_reviews": 2670},
        {"lifetime_rating": 2.0, "n_reviews": 1},
    ])
    assert agg["lifetime_rating_wavg"] == pytest.approx(4.6, abs=0.01)  # 1-review SKU can't swing it
    assert agg["cohort_rating_wavg"] is None                            # nothing claimed w/o cohorts


def test_snapshot_gap_constant_blocks_same_day_velocity():
    """Two snapshots hours apart must not be allowed to print a velocity."""
    assert cpr.MIN_SNAPSHOT_GAP_DAYS >= 1.0


# ── degraded-loud on unfetchable sources ────────────────────────────────────────────────────
def test_unfetchable_search_is_labelled_not_faked(monkeypatch):
    class _Blocked:
        def fetch_series(self, *a, **k):
            return {"status": "RATE_LIMIT", "points": [], "note": "429"}
    monkeypatch.setattr("verticals.buyside_dd.connectors.google_trends.GoogleTrendsConnector",
                        _Blocked)
    res = cph.search_trend("whatever")
    assert res["status"] == "RATE_LIMIT" and res["points"] == []
    assert "UNAVAILABLE" in res["source_label"]           # names the failure in the output
    stats = cph.trend_stats(res["points"])
    assert stats["direction"] == "NO_DATA" and stats["recent_avg"] is None


def test_unfetchable_retail_reports_status_not_empty_list(monkeypatch):
    class _Boom:
        @staticmethod
        def get(*a, **k):
            raise OSError("connection reset")
    monkeypatch.setitem(__import__("sys").modules, "requests", _Boom)
    out = cph.amazon_rank_proxy(["suja"], "grocery")
    assert out["status"] == "FETCH_ERROR" and "note" in out
    assert cph._retail_component(out) is None


def test_walmart_bot_wall_is_surfaced(monkeypatch):
    class _Resp:
        status_code = 200
        text = "Title: Robot or human?\n\nURL Source: x"

    class _Req:
        utils = __import__("requests").utils

        @staticmethod
        def get(*a, **k):
            return _Resp()
    monkeypatch.setitem(__import__("sys").modules, "requests", _Req)
    out = cpr.walmart_search("suja", tokens=["suja"])
    assert out["status"] == "BOT_WALL" and out["products"] == []


# ── APPLIES_TO dispatch contract ────────────────────────────────────────────────────────────
CONSUMER_ISSUER = {"name": "Suja Life Inc.", "sic": "2033",
                   "asset_classes": {"public_equity"}, "features": {"consumer_brand", "recent_ipo"}}
INDUSTRIAL_ISSUER = {"name": "Some Industrial Corp", "sic": "3559",
                     "asset_classes": {"public_equity"}, "features": {"capacity_ramp_claim"}}


@pytest.mark.parametrize("mod", [cph, cpr])
def test_applies_to_matches_consumer_sic(mod):
    assert _matches(mod.APPLIES_TO, CONSUMER_ISSUER) is True


@pytest.mark.parametrize("mod", [cph, cpr])
def test_applies_to_does_not_match_industrial(mod):
    assert _matches(mod.APPLIES_TO, INDUSTRIAL_ISSUER) is False


@pytest.mark.parametrize("mod", [cph, cpr])
def test_applies_to_matches_on_feature_even_off_sic(mod):
    """Keyed on the verification ATTRIBUTE, not the birth sector: a DTC brand filed under an odd
    SIC still dispatches (the multi_venue/FVRR lesson)."""
    odd = {"sic": "7372", "asset_classes": {"public_equity"}, "features": {"dtc_brand"}}
    assert _matches(mod.APPLIES_TO, odd) is True
    assert mod.APPLIES_TO["applies_universally"] is False


def test_lane_is_actually_dispatched_for_a_consumer_issuer():
    names = {m["name"] for m in relevant_for_issuer(CONSUMER_ISSUER)}
    assert {"consumer_product_heat", "consumer_product_reviews"} <= names


def test_lane_is_not_dispatched_for_an_industrial_issuer():
    names = {m["name"] for m in relevant_for_issuer(INDUSTRIAL_ISSUER)}
    assert "consumer_product_heat" not in names
    assert "consumer_product_reviews" not in names


# ── store merge (never clobber the sibling's half) ──────────────────────────────────────────
def test_merge_heat_store_merges_both_blocks(tmp_path, monkeypatch):
    monkeypatch.setattr(cph, "OUT_DIR", tmp_path)
    monkeypatch.setattr(cph, "HEAT_JSON", tmp_path / "CONSUMER_HEAT.json")
    cph.merge_heat_store("heat", {"SUJA": {"heat_score": 26.4}})
    cph.merge_heat_store("reviews", {"SUJA": {"rating_delta": -0.2}})
    doc = json.loads((tmp_path / "CONSUMER_HEAT.json").read_text())
    assert doc["tickers"]["SUJA"]["heat"]["heat_score"] == 26.4
    assert doc["tickers"]["SUJA"]["reviews"]["rating_delta"] == -0.2   # heat block survived
    assert set(doc["meta"]) == {"heat", "reviews"}
