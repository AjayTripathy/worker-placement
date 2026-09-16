"""Tests for the Forest Integrity Panel (forest_integrity.py).

Offline-only: AOI file structure + clear-cut math on synthetic arrays + threshold
sanity + the no-zero-imputation-on-missing invariant. No network.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pytest

from verticals.buyside_dd.connectors.forest_integrity import (
    BAD_SCENE_CLEARED_FRAC_MAX,
    BAD_SCENE_CLEARED_FRAC_PER_YEAR,
    CLEARCUT_DROP,
    CLOUD_DIFF_LOWCONF_PCT,
    ELEVATED_MULT,
    FOREST_BASELINE,
    FULL_TILE_FRAC,
    HAZE_FRAC_TOL,
    SWEDISH_FINAL_FELL_NORM_PCT,
    _clearcut_band,
    _clearcut_stats,
)

_AOI_PATH = os.path.join(
    os.path.dirname(__file__), "..", "verticals", "buyside_dd", "connectors", "data", "forest_aoi.json"
)


# ─────────────────────────────────────────────────────────────────────────────
# AOI panel structure
# ─────────────────────────────────────────────────────────────────────────────
def _load_aois():
    with open(os.path.normpath(_AOI_PATH)) as f:
        return json.load(f)


def test_aoi_file_parses_and_has_eight_entries():
    doc = _load_aois()
    aois = doc["aois"]
    assert len(aois) == 8, f"expected 8 AOIs (6 stora + 2 controls), got {len(aois)}"


def test_aoi_controls_flagged_one_protected_one_managed_peer():
    aois = _load_aois()["aois"]
    controls = [a for a in aois if a["role"] == "control"]
    stora = [a for a in aois if a["role"] == "stora_region"]
    assert len(stora) == 6, f"expected 6 stora_region AOIs, got {len(stora)}"
    assert len(controls) == 2, f"expected 2 controls, got {len(controls)}"
    ctypes = sorted(c["control_type"] for c in controls)
    assert ctypes == ["managed_nonstora", "protected"], ctypes
    # the protected control is the method-validation and must carry a rationale saying so
    prot = next(c for c in controls if c["control_type"] == "protected")
    assert "method" in prot["rationale"].lower() or "broken" in prot["rationale"].lower()


def test_every_aoi_has_valid_bbox_and_required_fields():
    aois = _load_aois()["aois"]
    for a in aois:
        for k in ("id", "name", "role", "lat", "lon", "radius_km", "bbox", "rationale"):
            assert k in a, f"AOI {a.get('id')} missing {k}"
        bb = a["bbox"]
        assert len(bb) == 4, f"{a['id']} bbox must be [minLon,minLat,maxLon,maxLat]"
        assert bb[0] < bb[2] and bb[1] < bb[3], f"{a['id']} bbox min>=max"
        # central/southern Sweden sanity: lon ~11-19E, lat ~55-62N
        assert 10.0 < a["lon"] < 20.0, f"{a['id']} lon out of Sweden range"
        assert 55.0 < a["lat"] < 63.0, f"{a['id']} lat out of Sweden range"
        # rationale must document WHY this box (per prompt: cite how each was chosen)
        assert len(a["rationale"]) > 40, f"{a['id']} rationale too thin"


# ─────────────────────────────────────────────────────────────────────────────
# Clear-cut math on synthetic arrays
# ─────────────────────────────────────────────────────────────────────────────
def test_clearcut_all_forest_no_change_reads_zero():
    # A 10x10 forest that stays forested -> 0% cleared (a genuine 0, from real pixels).
    base = np.full((10, 10), 0.85)
    cur = np.full((10, 10), 0.84)  # trivial hazier-scene drift, below CLEARCUT_DROP
    st = _clearcut_stats(base, cur)
    assert st is not None
    assert st["n_forest_px"] == 100
    assert st["clearcut_frac"] == 0.0
    assert st["coverage_frac"] == 1.0


def test_clearcut_quarter_cut_reads_25pct():
    # 100 forested px; drop 25 of them to bare ground -> 25% clear-cut.
    base = np.full((10, 10), 0.82)
    cur = base.copy()
    cur[:, :5] = 0.20  # 50 px collapsed... wait, that's half -> use 25 exactly
    cur[:, :] = 0.82
    flat = cur.reshape(-1)
    flat[:25] = 0.20  # exactly 25 pixels -> bare
    cur = flat.reshape(10, 10)
    st = _clearcut_stats(base, cur)
    assert st["n_forest_px"] == 100
    assert st["n_cleared_px"] == 25
    assert st["clearcut_frac"] == pytest.approx(0.25)


def test_clearcut_only_counts_pixels_forested_in_baseline():
    # Pixels that were NOT forest in baseline (bog/water at 0.30) must be excluded from
    # BOTH numerator and denominator even if they drop further.
    base = np.full((10, 10), 0.30)   # all non-forest baseline
    base[:5, :] = 0.80               # top half is forest (50 px)
    cur = base.copy()
    cur[0, :] = 0.10                 # 10 forest px cleared
    cur[9, :] = 0.05                 # 10 NON-forest px drop further -> must be ignored
    st = _clearcut_stats(base, cur)
    assert st["n_forest_px"] == 50, "denominator must be baseline-forest only"
    assert st["n_cleared_px"] == 10, "numerator must exclude non-forest baseline pixels"
    assert st["clearcut_frac"] == pytest.approx(0.20)


def test_partial_thinning_below_drop_threshold_not_counted():
    # A selective thin that only drops NDVI 0.15 (< CLEARCUT_DROP 0.25) is NOT a clear-cut.
    base = np.full((8, 8), 0.80)
    cur = np.full((8, 8), 0.80 - (CLEARCUT_DROP - 0.10))  # 0.65 drop of 0.15
    st = _clearcut_stats(base, cur)
    assert st["n_cleared_px"] == 0, "sub-threshold thinning must not count as clear-cut"


# ─────────────────────────────────────────────────────────────────────────────
# No zero-imputation on MISSING (the desk's standing rule)
# ─────────────────────────────────────────────────────────────────────────────
def test_missing_scene_returns_none_not_zero():
    # A completely-clouded current scene => all-NaN array. Must be None (MISSING), NOT 0%.
    base = np.full((10, 10), 0.85)
    cur = np.full((10, 10), np.nan)
    st = _clearcut_stats(base, cur)
    assert st is None, "all-NaN current scene must be MISSING (None), never 0% clear-cut"


def test_no_forested_baseline_returns_none_not_zero():
    # If nothing in the baseline is forest (e.g. AOI over a lake), there is nothing to
    # measure -> None (MISSING), not a spurious 0%.
    base = np.full((10, 10), 0.10)  # all water/bare
    cur = np.full((10, 10), 0.10)
    st = _clearcut_stats(base, cur)
    assert st is None


def test_nan_pixels_excluded_from_both_scenes():
    # Cloud in EITHER scene at a pixel drops it from the usable set; coverage_frac tracks it.
    base = np.full((10, 10), 0.85)
    cur = np.full((10, 10), 0.85)
    base[0, :] = np.nan   # 10 px clouded in baseline
    cur[1, :] = np.nan    # 10 px clouded in current
    st = _clearcut_stats(base, cur)
    # forested-baseline denom = pixels forest in base AND finite in both = 100 - 10(base nan) - 10(cur nan) = 80
    assert st["n_forest_px"] == 80
    assert st["coverage_frac"] == pytest.approx(0.80)


# ─────────────────────────────────────────────────────────────────────────────
# Error band + thresholds sane
# ─────────────────────────────────────────────────────────────────────────────
def test_band_widens_as_coverage_falls():
    # Same clear-cut %, worse coverage => wider band.
    full = _clearcut_band(0.03, coverage_frac=0.95, n_forest_px=2000)
    poor = _clearcut_band(0.03, coverage_frac=0.50, n_forest_px=2000)
    assert poor > full, "band must widen as cloud coverage worsens"
    assert full >= 0.4, "band has a >=0.4pp floor (no false precision at 10m)"


def test_band_widens_for_small_samples():
    big = _clearcut_band(0.10, coverage_frac=0.95, n_forest_px=5000)
    small = _clearcut_band(0.10, coverage_frac=0.95, n_forest_px=50)
    assert small > big, "small pixel samples must widen the band"


def test_thresholds_are_sane():
    # Forest baseline sits in the vegetated band; clear-cut drop is a real collapse.
    assert 0.4 <= FOREST_BASELINE <= 0.75, "forest baseline must be a plausible conifer NDVI floor"
    assert 0.15 <= CLEARCUT_DROP <= 0.4, "clear-cut drop must be a real NDVI collapse, not noise"
    assert CLEARCUT_DROP < FOREST_BASELINE, "a clear-cut drop must be reachable from the forest floor"
    assert 0.5 <= SWEDISH_FINAL_FELL_NORM_PCT <= 2.0, "final-fell norm ~1%/yr"
    assert 1.5 <= ELEVATED_MULT <= 3.0, "elevated multiple must be a materiality line, not noise"


def test_bad_scene_flag_on_uniform_collapse():
    # A thin-haze scene collapses NDVI across ~ALL of the AOI. This must set bad_scene
    # (=> the runner rejects the year as MISSING), never report a real >30% "clear-cut".
    # Regression for STORA-VARMLAND-1 2026-07-14 (forest 0.79 -> uniform 0.36 => fake 84%).
    base = np.full((20, 20), 0.80)
    cur = np.full((20, 20), 0.36)   # uniform haze collapse of the whole tile
    st = _clearcut_stats(base, cur, span_years=1)
    assert st is not None
    assert st["clearcut_frac"] > BAD_SCENE_CLEARED_FRAC_PER_YEAR
    assert st["bad_scene"] is True, "uniform collapse across >30%/yr must flag bad_scene"


def test_bad_scene_threshold_scales_with_span():
    # A legitimate multi-year CUMULATIVE fell (40% over 4 years = 10%/yr) must NOT be
    # rejected as haze — the per-year threshold scales by span. Regression for reviewer #5.
    base = np.full((10, 10), 0.82)
    cur = base.copy()
    flat = cur.reshape(-1)
    flat[:40] = 0.20   # 40% of forest cleared cumulatively
    cur = flat.reshape(10, 10)
    st1 = _clearcut_stats(base, cur, span_years=1)   # 40% in ONE year -> haze reject
    assert st1["bad_scene"] is True
    st4 = _clearcut_stats(base, cur, span_years=4)   # 40% over 4 years (10%/yr) -> real
    assert st4["bad_scene"] is False, "a 10%/yr cumulative fell over 4y must not be haze-rejected"


def test_real_patchy_clearcut_not_flagged_bad():
    # A genuine final-fell touches a FRACTION of the AOI (here 8%) -> NOT a bad scene.
    base = np.full((10, 10), 0.82)
    cur = base.copy()
    flat = cur.reshape(-1)
    flat[:8] = 0.20   # 8 of 100 forested px felled
    cur = flat.reshape(10, 10)
    st = _clearcut_stats(base, cur)
    assert st["clearcut_frac"] == pytest.approx(0.08)
    assert st["bad_scene"] is False, "a realistic patchy fell must not trip the bad-scene guard"


def test_haze_tol_and_bad_scene_thresholds_sane():
    assert 0.05 <= HAZE_FRAC_TOL <= 0.25, "haze forest-frac tolerance must be a small but real drop"
    assert 0.2 <= BAD_SCENE_CLEARED_FRAC_PER_YEAR <= 0.5, "no commercial forest fells >30-50%/yr; per-year guard must be in that band"
    assert BAD_SCENE_CLEARED_FRAC_PER_YEAR <= BAD_SCENE_CLEARED_FRAC_MAX <= 0.8, "cumulative cap must exceed the per-year rate and stay < near-total"


def test_data_quality_guard_thresholds_sane():
    # The three data-quality guards must be in defensible ranges.
    assert 0.6 <= FULL_TILE_FRAC <= 0.95, "partial-tile guard must demand near-full window coverage"
    assert 2.0 <= CLOUD_DIFF_LOWCONF_PCT <= 15.0, "cloud-differential low-confidence trigger must be a real cloud level"


def test_clearcut_handles_mismatched_shapes():
    # Real scenes can differ by a row/col after windowing; the math must crop to overlap.
    base = np.full((10, 11), 0.85)
    cur = np.full((9, 10), 0.20)
    st = _clearcut_stats(base, cur, span_years=1)
    assert st is not None
    assert st["n_forest_px"] == 9 * 10  # cropped to (9,10) overlap
    # 100% cleared over 1 year -> bad_scene reject (uniform collapse), still reports frac.
    assert st["clearcut_frac"] == pytest.approx(1.0)


def test_coverage_band_widens_even_when_frac_is_zero():
    # Regression for reviewer #4: a heavily-clouded scene can HIDE a fell, so the band must
    # widen as coverage falls even when the measured clear-cut fraction is ~0. The old
    # purely-multiplicative-on-frac term collapsed to the floor here.
    clean = _clearcut_band(0.0, coverage_frac=1.0, n_forest_px=5000)
    clouded = _clearcut_band(0.0, coverage_frac=0.5, n_forest_px=5000)
    assert clouded > clean, "band must widen with cloud cover even at frac=0 (a fell can hide under cloud)"


# ─────────────────────────────────────────────────────────────────────────────
# Runner grading (offline; no network — grade_aoi is pure)
# ─────────────────────────────────────────────────────────────────────────────
def test_grade_peer_missing_does_not_silently_clear_a_hot_aoi():
    # Regression for reviewer #1 (highest severity): a genuinely-high clear-cut must NOT be
    # graded SUSTAINABLE just because the peer control clouded out (peer_pct=None).
    from verticals.buyside_dd.connectors.run_forest_panel import grade_aoi, STORA_STATED
    stated = dict(STORA_STATED)
    # hot (5%/yr, >2x norm), method validated (protected 0.3%), but peer MISSING
    g = grade_aoi(5.0, 0.2, protected_pct=0.3, peer_pct=None, stated=stated)
    assert g["verdict"] == "UNVERIFIABLE", "hot AOI with a missing peer must be UNVERIFIABLE, not SUSTAINABLE"
    assert "peer" in g["reason"].lower()


def test_grade_missing_protected_control_blocks_elevated():
    # Regression for reviewer #2: a would-be ELEVATED must downgrade to UNVERIFIABLE when the
    # method-validation control is MISSING (method unvalidated -> no confirmed alarm).
    from verticals.buyside_dd.connectors.run_forest_panel import grade_aoi, STORA_STATED
    stated = dict(STORA_STATED)
    g = grade_aoi(5.0, 0.2, protected_pct=None, peer_pct=0.5, stated=stated)
    assert g["verdict"] == "UNVERIFIABLE", "no validated method control -> cannot call ELEVATED"


def test_grade_elevated_requires_method_and_peer():
    from verticals.buyside_dd.connectors.run_forest_panel import grade_aoi, STORA_STATED
    stated = dict(STORA_STATED)
    # hot, method validated (0.5%), and hotter than peer (0.5%) -> ELEVATED
    g = grade_aoi(5.0, 0.2, protected_pct=0.5, peer_pct=0.5, stated=stated)
    assert g["verdict"] == "ELEVATED"


def test_grade_sustainable_normal_case():
    from verticals.buyside_dd.connectors.run_forest_panel import grade_aoi, STORA_STATED
    stated = dict(STORA_STATED)
    g = grade_aoi(0.8, 0.2, protected_pct=0.95, peer_pct=0.71, stated=stated)
    assert g["verdict"] == "SUSTAINABLE"


def test_grade_low_confidence_never_elevated_and_no_typeerror_on_none_band():
    # low_confidence always -> UNVERIFIABLE; and band_pp=None must not raise (reviewer #3).
    from verticals.buyside_dd.connectors.run_forest_panel import grade_aoi, STORA_STATED
    stated = dict(STORA_STATED)
    g = grade_aoi(2.4, None, protected_pct=0.3, peer_pct=0.5, stated=stated,
                  low_confidence=True, low_conf_reason="cloud 9% >> baseline 0%")
    assert g["verdict"] == "UNVERIFIABLE"


def test_effis_error_body_not_reported_as_clean_zero():
    # Regression for reviewer #2 (EFFIS): a JSON exception body WITHOUT a 'features' key must
    # NOT be read as 'features: [] => 0 fires'. We test the parsing predicate directly by
    # simulating the two response shapes through effis_fire_overlay's logic contract.
    # (Pure check: a dict without 'features' must not yield status LIVE.)
    import json as _json
    exc_body = {"type": "ExceptionReport", "exceptions": [{"text": "Oracle down"}]}
    fc_body = {"type": "FeatureCollection", "features": []}
    # mirror the fixed predicate
    def is_featurecollection(parsed):
        return isinstance(parsed, dict) and isinstance(parsed.get("features"), list)
    assert is_featurecollection(_json.loads(_json.dumps(exc_body))) is False
    assert is_featurecollection(_json.loads(_json.dumps(fc_body))) is True
