"""official_series failure/merge/nowcast semantics — all OFFLINE (adapters monkeypatched).

The contract under test:
  - INFRA failure (agency outage, wrong-shaped payload, unit drift) surfaces as
    degraded and MUST NOT be cached (fc34665d doctrine, mirrored from
    facilities_resolver) — a transient DICJ outage must never become a sticky
    "no observations" record.
  - A genuinely empty read (the document parsed, the agency has published nothing
    yet) IS a real observation of absence and IS cached.
  - History MERGES by period — the array is never overwritten wholesale, and a
    changed value is recorded as a REVISION rather than clobbered.
  - Partial-quarter nowcast is matched-month only: a missing month is DROPPED from
    both sums and flagged, never annualized or silently completed.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desk import official_series as OS

KEY = "macau_ggr"


@pytest.fixture
def cache_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(OS, "CACHE_DIR", tmp_path)
    return tmp_path


def _adapter(obs, degraded=None, url="https://example.test/report"):
    """Stand in for a per-agency adapter: (observations, degraded_reason, url)."""
    def _a(spec, **kw):
        return list(obs), degraded, url
    return _a


def _obs(*pairs):
    return [{"period": p, "value": float(v), "unit": OS.SERIES[KEY]["unit"],
             "source": "test"} for p, v in pairs]


def _install(monkeypatch, adapter):
    monkeypatch.setitem(OS.ADAPTERS, OS.SERIES[KEY]["adapter"], adapter)


# ── degraded: surfaced loud, NEVER cached ────────────────────────────────────
def test_degraded_fetch_is_not_cached(cache_dir, monkeypatch):
    _install(monkeypatch, _adapter([], degraded="DICJ report fetch failed (HTTP 503)"))
    rec = OS.fetch(KEY)
    assert rec["degraded"].startswith("DICJ report fetch failed")
    assert "DEGRADED" in rec["note"] and "not cached" in rec["note"]
    assert not (cache_dir / f"{KEY}.json").exists(), "an outage was written to cache"


def test_degraded_does_not_clobber_good_cache(cache_dir, monkeypatch):
    _install(monkeypatch, _adapter(_obs(("2026-06", 18522), ("2026-07", 20260))))
    OS.fetch(KEY)
    good = json.loads((cache_dir / f"{KEY}.json").read_text())

    _install(monkeypatch, _adapter([], degraded="DSEC returned Status='ERROR'"))
    rec = OS.fetch(KEY, refresh=True)
    assert rec["degraded"]
    # the good record is still on disk, untouched
    assert json.loads((cache_dir / f"{KEY}.json").read_text()) == good
    # and the caller still sees the last good history, explicitly marked degraded
    assert [o["period"] for o in rec["observations"]] == ["2026-06", "2026-07"]


def test_adapter_exception_is_degraded_not_empty(cache_dir, monkeypatch):
    def _boom(spec, **kw):
        raise TimeoutError("read timed out")
    _install(monkeypatch, _boom)
    rec = OS.fetch(KEY)
    assert "TimeoutError" in rec["degraded"]
    assert not (cache_dir / f"{KEY}.json").exists()


# ── genuine empty: a real observation of absence, IS cached ──────────────────
def test_genuine_empty_is_cached(cache_dir, monkeypatch):
    _install(monkeypatch, _adapter([]))            # parsed fine, nothing published
    rec = OS.fetch(KEY)
    assert "degraded" not in rec
    assert rec["observations"] == []
    p = cache_dir / f"{KEY}.json"
    assert p.exists(), "a genuine empty read must be cached (absence is an observation)"
    assert json.loads(p.read_text())["observations"] == []


# ── history MERGES by period, never overwritten wholesale ────────────────────
def test_observations_merge_by_period_no_clobber(cache_dir, monkeypatch):
    _install(monkeypatch, _adapter(_obs(("2026-05", 22611), ("2026-06", 18522))))
    OS.fetch(KEY)
    # next release ships only the newest two months — the older one must survive
    _install(monkeypatch, _adapter(_obs(("2026-06", 18522), ("2026-07", 20260))))
    rec = OS.fetch(KEY, refresh=True)
    assert [o["period"] for o in rec["observations"]] == ["2026-05", "2026-06", "2026-07"]
    assert [o["value"] for o in rec["observations"]] == [22611.0, 18522.0, 20260.0]


def test_merge_records_revision_rather_than_clobbering(cache_dir, monkeypatch):
    _install(monkeypatch, _adapter(_obs(("2026-06", 18500))))
    OS.fetch(KEY)
    _install(monkeypatch, _adapter(_obs(("2026-06", 18522))))
    rec = OS.fetch(KEY, refresh=True)
    row = rec["observations"][0]
    assert row["value"] == 18522.0
    assert row["revised_from"] == 18500.0, "a revision must be recorded, not silently clobbered"
    assert "1 revised period(s)" in rec["note"]


def test_unrevised_row_keeps_its_first_fetched_stamp(cache_dir, monkeypatch):
    _install(monkeypatch, _adapter(_obs(("2026-06", 18522))))
    first = OS.fetch(KEY)["observations"][0]["fetched"]
    _install(monkeypatch, _adapter(_obs(("2026-06", 18522), ("2026-07", 20260))))
    rec = OS.fetch(KEY, refresh=True)
    assert rec["observations"][0]["fetched"] == first


# ── partial-quarter nowcast: matched months only, missing month flagged ──────
def test_nowcast_full_quarter(cache_dir, monkeypatch):
    _install(monkeypatch, _adapter(_obs(
        ("2025-04", 100), ("2025-05", 100), ("2025-06", 100),
        ("2026-04", 110), ("2026-05", 105), ("2026-06", 100))))
    OS.fetch(KEY)
    out = OS.nowcast_quarter(KEY, ["2026-04", "2026-05", "2026-06"])
    assert out["partial"] is False and out["coverage"] == "3/3"
    assert out["current_sum"] == 315.0 and out["prior_sum"] == 300.0
    assert out["implied_yoy"] == 5.0


def test_nowcast_missing_current_month_is_flagged_partial(cache_dir, monkeypatch):
    _install(monkeypatch, _adapter(_obs(
        ("2025-04", 100), ("2025-05", 100), ("2025-06", 100),
        ("2026-04", 110), ("2026-05", 110))))          # June has not printed yet
    OS.fetch(KEY)
    out = OS.nowcast_quarter(KEY, ["2026-04", "2026-05", "2026-06"])
    assert out["partial"] is True and out["coverage"] == "2/3"
    assert out["missing_current_months"] == ["2026-06"]
    # the missing month is dropped from BOTH sides — never annualized
    assert out["current_sum"] == 220.0 and out["prior_sum"] == 200.0
    assert out["implied_yoy"] == 10.0
    assert "NOT annualized" in out["basis"] and "PARTIAL COVERAGE" in out["note"]


def test_nowcast_missing_prior_year_month_is_dropped_from_both_sides(cache_dir, monkeypatch):
    _install(monkeypatch, _adapter(_obs(
        ("2025-04", 100), ("2025-06", 100),
        ("2026-04", 110), ("2026-05", 999), ("2026-06", 100))))
    OS.fetch(KEY)
    out = OS.nowcast_quarter(KEY, ["2026-04", "2026-05", "2026-06"])
    assert out["missing_prior_year_months"] == ["2025-05"]
    assert out["matched_months"] == ["2026-04", "2026-06"]
    assert out["current_sum"] == 210.0 and out["prior_sum"] == 200.0


def test_nowcast_base_year_values_fill_unreachable_history(cache_dir, monkeypatch):
    _install(monkeypatch, _adapter(_obs(("2026-04", 110), ("2026-05", 110), ("2026-06", 110))))
    OS.fetch(KEY)
    out = OS.nowcast_quarter(KEY, ["2026-04", "2026-05", "2026-06"],
                             base_year_values={"2025-04": 100, "2025-05": 100, "2025-06": 100})
    assert out["partial"] is False and out["implied_yoy"] == 10.0


def test_nowcast_no_matched_months_is_unavailable_not_zero(cache_dir, monkeypatch):
    _install(monkeypatch, _adapter(_obs(("2026-04", 110))))
    OS.fetch(KEY)
    out = OS.nowcast_quarter(KEY, ["2026-04", "2026-05", "2026-06"])
    assert out["implied_yoy"] is None and "UNAVAILABLE, not zero" in out["note"]


def test_nowcast_refuses_to_sum_a_rate_series(cache_dir, monkeypatch):
    key = "macau_hotel_occupancy"
    assert OS.SERIES[key]["aggregatable"] is False
    out = OS.nowcast_quarter(key, ["2026-04", "2026-05", "2026-06"])
    assert out["implied_yoy"] is None and "REFUSES" in out["note"]


# ── YoY names its metric (pp for rates, % for levels) ────────────────────────
def test_yoy_mode_is_percentage_points_for_rate_series(cache_dir, monkeypatch):
    key = "macau_hotel_occupancy"
    monkeypatch.setitem(OS.ADAPTERS, OS.SERIES[key]["adapter"],
                        _adapter([{"period": p, "value": v, "unit": OS.SERIES[key]["unit"]}
                                  for p, v in (("2025-06", 88.4), ("2026-06", 85.8))]))
    OS.fetch(key)
    y = OS.yoy(key, "2026-06")
    assert y["mode"] == "pp_delta" and y["yoy"] == -2.6 and y["label"] == "-2.6pp"


def test_yoy_missing_prior_is_unavailable_not_zero(cache_dir, monkeypatch):
    _install(monkeypatch, _adapter(_obs(("2026-07", 20260))))
    OS.fetch(KEY)
    y = OS.yoy(KEY, "2026-07")
    assert y["yoy"] is None and "UNAVAILABLE, not zero" in y["note"]


# ── dispatch: geo guard + the render contract ────────────────────────────────
def test_series_for_matches_ticker_feature_and_geo_token():
    assert "macau_ggr" in OS.series_for("LVS")
    assert "macau_ggr" in OS.series_for(["casino_gaming_revenue"])
    assert "macau_ggr" in OS.series_for("operator of a Cotai integrated resort in Macau")
    # how detector_preflight calls it: "TICKER\n<case context>"
    assert "macau_ggr" in OS.series_for("MLCO\nMelco Resorts — integrated resort operator")


def test_sic_alone_never_fires_a_geo_specific_series():
    """SIC prefixes 70/79/58 would hand Macau GGR to Marriott and Chipotle."""
    assert OS.series_for("CMG") == []
    assert OS.series_for("Chipotle Mexican Grill, a US restaurant chain") == []


def test_render_series_is_empty_string_on_no_match():
    assert OS.render_series("CMG") == ""


def test_render_series_surfaces_degraded_loudly(cache_dir, monkeypatch):
    _install(monkeypatch, _adapter(_obs(("2026-06", 18522), ("2026-07", 20260))))
    OS.fetch(KEY)
    # age the cache so the render's fetch actually re-polls and hits the outage
    p = cache_dir / f"{KEY}.json"
    d = json.loads(p.read_text())
    d["asof"] = "2020-01-01T00:00:00Z"
    p.write_text(json.dumps(d))
    _install(monkeypatch, _adapter([], degraded="DICJ report fetch failed (HTTP 503)"))
    monkeypatch.setattr(OS, "SERIES", {KEY: OS.SERIES[KEY]})
    txt = OS.render_series("LVS")
    assert "DEGRADED" in txt and "last good cache" in txt


# ── staleness: a monthly series refetches when a release is plausibly out ────
def test_stale_when_latest_period_is_behind_the_expected_release(cache_dir, monkeypatch):
    import datetime
    spec = OS.SERIES[KEY]
    rec = {"asof": "2026-08-01T00:00:00Z", "observations": _obs(("2026-06", 18522))}
    assert OS._is_stale(rec, spec, today=datetime.date(2026, 8, 10)) is True
    rec2 = {"asof": "2026-08-01T00:00:00Z", "observations": _obs(("2026-07", 20260))}
    assert OS._is_stale(rec2, spec, today=datetime.date(2026, 8, 10)) is False
    # ... and goes stale again once the next month's release is due
    assert OS._is_stale(rec2, spec, today=datetime.date(2026, 9, 2)) is True


def test_registry_rows_declare_units_and_features():
    for key, s in OS.SERIES.items():
        # the TEY-conflation lesson: a bare "index"/"number" unit gets conflated
        assert len(s["unit"]) > 8, f"{key} unit {s['unit']!r} is not stated explicitly"
        for field in ("name", "agency", "geo", "unit", "cadence", "release_lag",
                      "adapter", "yoy_mode", "issuer_features", "status"):
            assert s.get(field), f"{key} missing {field}"
        assert s["adapter"] in OS.ADAPTERS, f"{key} names an unregistered adapter"
        assert set(s["issuer_features"]) <= set(OS.APPLIES_TO["issuer_features"]), \
            f"{key} serves a feature the m_source does not declare in APPLIES_TO"
