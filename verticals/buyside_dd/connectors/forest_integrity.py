"""Forest Integrity Panel — satellite verification of a forest-asset mark's QUANTITY half ($0).

WHY — a paper forest mark (e.g. Stora Enso STERV: ~2M ha, FV ~EUR8.5bn = EUR10.80/sh,
Sweden-dominant) has two halves: PRICE (verifiable from transaction comps — Stora's
May-2025 sale of 12.4% of the Swedish estate closed "in line with accounting fair
value") and QUANTITY (is the physical inventory actually there, healthy, and being cut
no faster than the stated sustainable plan?). Carbon Mapper sees emitters; the
sentinel2_buildout connector sees construction. This is the third physical sensor:
standing-forest health (NDVI) + a clear-cut / final-fell proxy graded against the
company's own stated harvest intensity and the Swedish industry norm.

This is the same free data path as sentinel2_buildout / crop_yield_ndvi — ESA
Sentinel-2 L2A (10 m red/nir) via the public Element84 Earth Search STAC + the open
`sentinel-cogs` bucket (no auth, no key). We LIFT `_s2util` for STAC search + COG reads.

SIGNAL — for each AOI (a ~5-10 km managed-forest box), over Jun-Aug summer windows:
  Layer 1 (health):  mean NDVI per year -> YoY delta. Standing conifer forest sits
                     high (~0.7-0.9 in summer); a falling mean is stress/loss.
  Layer 2 (harvest): a per-pixel clear-cut proxy. Of pixels that were FORESTED in the
                     baseline year (baseline NDVI >= FOREST_BASELINE), what fraction
                     DROPPED by >= CLEARCUT_DROP into the current year? Bare felled
                     ground reads NDVI ~0.1-0.3; standing forest ~0.7-0.9, so a
                     >=0.25 collapse from a forested baseline is a clear-cut tell.
                     Reported with a +/- band from cloud/coverage, never as false
                     precision.

GRADING — the panel compares each Stora-region AOI clear-cut % to (a) the CONTROLS
[a protected national park where ~0 harvest should occur = the method-validation, and
a non-Stora managed region = the peer], (b) the Swedish commercial final-fell NORM
(~1%/yr of productive area, Skogsstyrelsen), and (c) the company's stated harvest
intensity (the PAPER comparator; UNVERIFIABLE-gated if the exact figure isn't found).
A protected-park AOI reading material "harvest" means the METHOD is broken, not the
park — that is the whole point of the control.

HONESTY / LIMITS (report these, don't hide them):
  - 10 m NDVI clear-cut detection has real error bands. We report % +/- a band driven
    by cloud-cover coverage and treat any AOI/year with no usable scene as MISSING,
    never zero (the desk's standing no-zero-imputation rule).
  - The AOIs are a SAMPLE of an UNPUBLISHED estate. v1 reads REGIONS Stora is known to
    concentrate in (Bergvik Skog Öst geography), not the parcel-level deed map. Read the
    Stora-region AOIs as an estate SAMPLE, not the whole holding.
  - PAPER-GATED: this grades the MARK's plausibility (is the quantity/health/cut-rate
    consistent with the stated sustainable plan?). It does NOT time the stock.
  - No cron. Forest change is a Hansen/seasonal-cadence signal — run ON DEMAND. Re-run
    reminder: QUARTERLY (fresh summer composites land Jun-Sep; a winter re-run adds
    little). Cat overlay (fire/beetle) is the faster-moving channel between re-runs.

Inputs (ConnectorRequest):
  - extra={"aoi": {...one AOI dict from forest_aoi.json...}}  (single-AOI query)
    OR the panel runner (run_panel below) iterates the whole forest_aoi.json file.
  - extra optional: {"years":[2024,2025,2026], "baseline_year":2024,
                     "peak_start_md":"06-01", "peak_end_md":"08-31", "cloud_max":30}
"""
from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [], "sic_prefixes": ["08", "24", "26"],
    "issuer_features": ["forest_asset_mark", "physical_plant_operations", "agricultural_exposure"],
    "asset_classes": ["public_equity", "real_assets"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "Sentinel-2 forest-integrity panel: NDVI standing-forest health + clear-cut proxy graded against the issuer's stated sustainable harvest plan (the QUANTITY half of a forest mark; STERV first use).",
}


from typing import Optional

import numpy as np

from . import _s2util as S2
from .base import BaseConnector, ConnectorObservation, ConnectorRequest, ConnectorResult, ErrorKind

# ── Thresholds (documented; see tests/test_forest_integrity.py for the sanity gates) ──
# A pixel counts as "forested" in the baseline if its summer NDVI is at least this high.
# Boreal conifer forest sits ~0.7-0.9 in summer; 0.6 is a conservative forest floor that
# excludes clear-cuts, water, bog and bare rock from the denominator.
FOREST_BASELINE = 0.60
# A forested pixel counts as "cleared" if its NDVI falls by at least this much YoY.
# Standing forest ~0.8 -> fresh clear-cut ~0.2-0.4 is a >=0.4 drop; 0.25 is a
# conservative floor that still admits partial/selective fells while rejecting the
# ~0.05-0.10 noise of an ordinary cloud-free-to-hazier summer scene.
CLEARCUT_DROP = 0.25
# Swedish commercial final-fell (föryngringsavverkning) norm, % of PRODUCTIVE forest area
# per year. PRIMARY: SLU Riksskogstaxeringen + Skogsstyrelsen official statistics —
# "0.9% of productive forest land felled annually 2020-2024" (209,000 ha/yr of 23.5M ha;
# the two agencies' pipelines reconcile to 0.889%). Implies ~110yr rotation. This is the
# operative benchmark; Stora's OWN derived rate (~0.76-1.07%/yr from AR2024 note 4.2)
# independently converges here. QUESTION: do Stora-region AOIs run materially hotter?
SWEDISH_FINAL_FELL_NORM_PCT = 0.9
# An AOI clear-cut % above this (and above the controls) is flagged ELEVATED for review.
# 2x the norm is the materiality line — inside sampling error you cannot call 1% vs 1.4%.
ELEVATED_MULT = 2.0
# YoY mean-NDVI move beyond this (absolute) is a material health change worth surfacing.
MATERIAL_DNDVI = 0.05
# BAD-SCENE GUARD. A real final-fell affects a FRACTION of an AOI; thin haze / smoke /
# cirrus depresses NDVI UNIFORMLY across the whole tile. The STAC eo:cloud_cover flag is
# a scene-average that misses thin cirrus, and coverage_frac stays ~1.0 because hazy
# pixels are non-zero (not fill) — so both pass while the NDVI is corrupted. Learned from
# STORA-VARMLAND-1 (2026-07-23): a 3.5%-flagged scene collapsed forest NDVI 0.79->0.36
# uniformly and manufactured a fake 84% "clear-cut". If MORE than this fraction of the
# baseline-forested pixels "drop", it is a data-quality reject -> the year is MISSING,
# never a signal. No commercial forest fells >30% of a landscape PER YEAR — so the guard
# is applied as a PER-YEAR (annualized) rate by the caller (analyze scales it by the
# baseline->current span), NOT as a raw cumulative fraction. A 30%/yr "drop" is thin haze.
BAD_SCENE_CLEARED_FRAC_PER_YEAR = 0.30
# Hard cumulative ceiling regardless of span — even over many years, a single AOI losing
# more than this share of its forest in one differenced step is a data artifact, not a
# real fell sequence we would trust from a 10 m proxy.
BAD_SCENE_CLEARED_FRAC_MAX = 0.60
# HAZE GUARD. Real forest AOIs sit at a stable summer forest_frac (~0.9 in central
# Sweden). Thin haze depresses it. If even the GREENEST current-year candidate's
# forest_frac falls more than this below the baseline's, the AOI is haze-degraded for
# that year -> MISSING/UNVERIFIABLE, never a partial-haze "clear-cut" (learned from
# STORA-VARMLAND-1: a cloud-prone corner where every 2026 scene reads 0.75-0.90 forest
# and the "clear-cut" swings 5-21% across scenes = haze, not harvest).
HAZE_FRAC_TOL = 0.12
# CLOUD-DIFFERENTIAL guard. The clear-cut proxy differences two scenes; if the CURRENT
# scene is materially cloudier than the (near-clean) BASELINE, thin residual haze inflates
# the "drop" even when forest_frac barely moves. Learned from STORA-VARMLAND-1: clean
# 2024->2025 (both ~0% cloud) read 0.44%; 2024->2026 with an 8.7%-cloud current scene
# jumped to 4.87% — a cloud artifact, not real incremental harvest. If a clear-cut year's
# current-scene cloud exceeds this AND is well above the baseline's, the read is
# low-confidence: widen the band and DON'T let it drive an ELEVATED call (-> UNVERIFIABLE).
CLOUD_DIFF_LOWCONF_PCT = 5.0
# FULL-TILE guard. A Sentinel-2 granule that only clips the AOI covers fewer pixels than
# a granule centered on it. Differencing a partial tile against a full-window baseline
# crops the overlap to a narrow strip -> a spurious clear-cut (DALARNA-1 2025: a 228x803
# edge tile read 3.96% vs the full-tile 0.37%). A candidate must cover >= this fraction
# of the largest available candidate's pixel count to be eligible.
FULL_TILE_FRAC = 0.80


def _clearcut_stats(base_ndvi: np.ndarray, cur_ndvi: np.ndarray,
                    forest_baseline: float = FOREST_BASELINE,
                    clearcut_drop: float = CLEARCUT_DROP,
                    bad_scene_frac: Optional[float] = None,
                    span_years: int = 1) -> Optional[dict]:
    """Per-pixel clear-cut proxy on two co-registered summer NDVI arrays.

    Returns fraction of BASELINE-FORESTED pixels whose NDVI dropped >= clearcut_drop.
    Pure/no-network so it is unit-testable on synthetic arrays. Returns None if either
    array is empty or there is no forested baseline pixel (=> MISSING, never 0). Sets
    bad_scene=True when the "cleared" fraction exceeds the bad-scene threshold — a near-
    total uniform NDVI collapse is thin-haze contamination, not a harvest.

    The bad-scene threshold is a PER-YEAR rate scaled by span_years (a legitimate 11-year
    cumulative fell can reach 30%+ and must NOT be rejected as haze), capped at
    BAD_SCENE_CLEARED_FRAC_MAX. Pass bad_scene_frac to override explicitly.
    """
    if bad_scene_frac is None:
        bad_scene_frac = min(BAD_SCENE_CLEARED_FRAC_MAX,
                             BAD_SCENE_CLEARED_FRAC_PER_YEAR * max(1, span_years))
    if base_ndvi is None or cur_ndvi is None:
        return None
    if base_ndvi.size == 0 or cur_ndvi.size == 0:
        return None
    h = min(base_ndvi.shape[0], cur_ndvi.shape[0])
    w = min(base_ndvi.shape[1], cur_ndvi.shape[1])
    if h == 0 or w == 0:
        return None
    b = base_ndvi[:h, :w].astype("float64")
    c = cur_ndvi[:h, :w].astype("float64")
    valid = np.isfinite(b) & np.isfinite(c)          # both scenes have a real pixel
    forested = valid & (b >= forest_baseline)        # forest in the baseline year
    n_forest = int(forested.sum())
    if n_forest == 0:
        return None                                   # nothing to measure -> MISSING
    cleared = forested & ((b - c) >= clearcut_drop)  # forest -> collapsed NDVI
    n_cleared = int(cleared.sum())
    frac = n_cleared / n_forest
    bad_scene = frac > bad_scene_frac                # uniform collapse = thin-haze reject
    return {
        "clearcut_frac": frac,
        "n_forest_px": n_forest,
        "n_cleared_px": n_cleared,
        "coverage_frac": float(valid.sum()) / float(b.size),  # non-cloud/non-fill share
        "bad_scene": bad_scene,
    }


def _clearcut_band(frac: float, coverage_frac: float, n_forest_px: int) -> float:
    """Honest +/- band on the clear-cut %, in percentage points.

    Three error sources, added in quadrature and floored:
      (1) coverage-hidden: cloud/fill can HIDE a fell entirely, so the band must widen as
          coverage falls even when the measured frac is ~0. A frac-INDEPENDENT term: the
          lost pixel share can conceal up to that share of a norm-scale (~1%) fell.
      (2) coverage-inflate: cloud can also fake/inflate the measured drop -> a term that
          scales with the measured frac and blows up as coverage -> 0.
      (3) counting/registration noise on a 10 m proxy: a ~0.4pp floor plus a
          binomial-style sqrt(p(1-p)/n) term so tiny samples widen.
    Deliberately conservative — the point is to NOT over-claim precision at 10 m.
    """
    cov = max(0.01, min(1.0, coverage_frac))
    lost = 1.0 - cov                                          # share of the AOI unseen
    # (1) a fell could hide under the clouded share; scale to ~1 norm (SWEDISH ~0.9%) per
    #     full loss, so 40% cloud -> up to ~0.36pp of hidden fell (independent of frac).
    coverage_hidden_pp = lost * SWEDISH_FINAL_FELL_NORM_PCT
    # (2) cloud can inflate the observed drop; grows with the measured frac and 1/cov.
    coverage_inflate_pp = (lost / cov) * (frac * 100.0) * 0.5
    p = max(0.0, min(1.0, frac))
    binom_pp = 100.0 * (p * (1 - p) / max(1, n_forest_px)) ** 0.5
    floor_pp = 0.4
    return round((floor_pp ** 2 + coverage_hidden_pp ** 2 + coverage_inflate_pp ** 2 + binom_pp ** 2) ** 0.5, 2)


class ForestIntegrityConnector(BaseConnector):
    """Single-AOI forest health + clear-cut proxy. Use run_panel() for the full estate."""
    source_id = "forest_integrity"
    rate_limit_per_min = 30
    user_agent = "SignalOS-BuysideDD/0.1 (research; forest-integrity)"

    # ── AOI resolution ───────────────────────────────────────────────────────
    def _resolve_bbox(self, request: ConnectorRequest):
        x = request.extra or {}
        aoi = x.get("aoi")
        if aoi and aoi.get("bbox") and len(aoi["bbox"]) == 4:
            return [float(v) for v in aoi["bbox"]], aoi
        if x.get("bbox") and len(x["bbox"]) == 4:
            return [float(v) for v in x["bbox"]], None
        if aoi and aoi.get("lat") is not None and aoi.get("lon") is not None:
            return S2.bbox_from_point(float(aoi["lat"]), float(aoi["lon"]),
                                      float(aoi.get("radius_km", 3.0))), aoi
        if x.get("lat") is not None and x.get("lon") is not None:
            return S2.bbox_from_point(float(x["lat"]), float(x["lon"]),
                                      float(x.get("radius_km", 3.0))), None
        return None, None

    def _scene_candidates(self, bbox, year: int, ps: str, pe: str, cloud_max: int, limit: int = 6):
        """Lowest-cloud Jun-Aug candidate scenes for `year` (cloud-ascending)."""
        dt = f"{year}-{ps}T00:00:00Z/{year}-{pe}T23:59:59Z"
        body = {"collections": [S2.COLLECTION], "bbox": bbox, "datetime": dt,
                "query": {"eo:cloud_cover": {"lt": cloud_max}}, "limit": limit,
                "sortby": [{"field": "properties.eo:cloud_cover", "direction": "asc"}]}
        try:
            r = self._session().post(S2.STAC, json=body, timeout=self.timeout_s)
            if r.status_code >= 400:
                return []
            return r.json().get("features", [])
        except Exception:
            return []

    def _ndvi_from_scene(self, scene: dict, bbox) -> Optional[dict]:
        red = S2.read_window(S2.asset_href(scene, "red"), bbox)
        nir = S2.read_window(S2.asset_href(scene, "nir"), bbox)
        if red is None or nir is None:
            return None
        h, w = min(red.shape[0], nir.shape[0]), min(red.shape[1], nir.shape[1])
        red, nir = red[:h, :w], nir[:h, :w]
        both = (red > 0) & (nir > 0)                 # S2 L2A fill is 0
        denom = nir + red
        ndvi = np.where(both & (denom > 0), (nir - red) / np.where(denom > 0, denom, 1), np.nan)
        finite = np.isfinite(ndvi)
        veg = ndvi[finite & (ndvi >= FOREST_BASELINE)]
        return {
            "year": None, "date": S2.scene_date(scene), "cloud": S2.scene_cloud(scene),
            "ndvi": ndvi,
            "n_px": int(ndvi.size),           # window pixel count (partial tiles are smaller)
            "shape": list(ndvi.shape),
            "mean_ndvi": float(np.nanmean(ndvi)) if finite.any() else None,
            "forest_mean_ndvi": float(veg.mean()) if veg.size else None,
            "forest_frac": float(veg.size / ndvi.size) if ndvi.size else None,
            "coverage_frac": float(finite.sum()) / float(ndvi.size) if ndvi.size else 0.0,
        }

    # ── one year's summer NDVI array + scalar summary ────────────────────────
    def _summer_ndvi(self, bbox, year: int, ps: str, pe: str, cloud_max: int,
                     ref_forest_frac: Optional[float] = None) -> Optional[dict]:
        """Best usable Jun-Aug scene for `year` (per-pixel NDVI + summary). Reads all
        cloud-ascending candidates and picks the one whose forest_frac is HIGHEST (thin
        haze depresses forest_frac, so the greenest scene is the least-contaminated). If
        a reference forest_frac is given (the baseline's), the picked scene must come
        within HAZE_FRAC_TOL of it or the year is haze-flagged. Also returns
        `candidate_fracs` so callers can flag AOIs whose scenes disagree (persistent
        haze => UNVERIFIABLE, not a fake clear-cut). None => no usable scene (MISSING)."""
        cands = self._scene_candidates(bbox, year, ps, pe, cloud_max)
        reads = []
        for sc in cands:
            d = self._ndvi_from_scene(sc, bbox)
            if d is not None:
                reads.append(d)
        if not reads:
            return None
        # Reject PARTIAL-TILE scenes: a Sentinel-2 granule that only clips the AOI covers
        # fewer pixels; differencing a partial tile against a full baseline crops to a
        # narrow strip and manufactures a spurious clear-cut (learned from DALARNA-1 2025:
        # a 228x803 edge tile read 3.96% vs the full-tile 0.37%). Keep only candidates
        # whose window pixel count is >= FULL_TILE_FRAC of the largest candidate's.
        max_px = max((d.get("n_px") or 0) for d in reads)
        full = [d for d in reads if (d.get("n_px") or 0) >= FULL_TILE_FRAC * max_px] or reads
        # Among full-coverage candidates, pick the greenest (least haze-contaminated).
        full.sort(key=lambda d: (d.get("forest_frac") or 0.0), reverse=True)
        best = full[0]
        best["year"] = year
        best["candidate_fracs"] = [round(d.get("forest_frac") or 0.0, 3) for d in full]
        best["candidate_dates"] = [d["date"] for d in full]
        best["n_partial_rejected"] = len(reads) - len(full)
        # Haze flag: even the greenest full scene is materially below the reference forest.
        if ref_forest_frac is not None:
            best["haze_flag"] = (best.get("forest_frac") or 0.0) < (ref_forest_frac - HAZE_FRAC_TOL)
        return best

    # ── core: compute the panel for one AOI ──────────────────────────────────
    def analyze(self, bbox, aoi: Optional[dict], years: list[int], baseline_year: int,
                ps: str, pe: str, cloud_max: int) -> dict:
        """Returns a plain dict (no ConnectorResult) so run_panel can aggregate it."""
        self._throttle()
        per_year = {}
        # Baseline first (unconstrained) so its forest_frac can gate later-year haze.
        base_read = self._summer_ndvi(bbox, baseline_year, ps, pe, cloud_max)
        per_year[baseline_year] = base_read
        ref_ff = base_read.get("forest_frac") if base_read else None
        for yr in years:
            if yr == baseline_year:
                continue
            per_year[yr] = self._summer_ndvi(bbox, yr, ps, pe, cloud_max, ref_forest_frac=ref_ff)

        # Health series (mean NDVI) — MISSING preserved as None.
        health = {yr: (per_year[yr]["mean_ndvi"] if per_year[yr] else None) for yr in years}
        forest_health = {yr: (per_year[yr]["forest_mean_ndvi"] if per_year[yr] else None) for yr in years}
        yoy_deltas = {}
        for a, bnext in zip(years[:-1], years[1:]):
            if health[a] is not None and health[bnext] is not None:
                yoy_deltas[f"{a}->{bnext}"] = round(health[bnext] - health[a], 4)
            else:
                yoy_deltas[f"{a}->{bnext}"] = None

        # Harvest series: clear-cut % baseline_year -> each later year.
        base = per_year.get(baseline_year)
        clearcut = {}
        latest_cc = None
        for yr in years:
            if yr <= baseline_year:
                continue
            cur = per_year.get(yr)
            if base is None or cur is None:
                clearcut[yr] = {"status": "MISSING",
                                "reason": ("no baseline scene" if base is None else "no current scene")}
                continue
            if cur.get("haze_flag"):
                # Even the greenest current-year scene lost >HAZE_FRAC_TOL of the baseline
                # forest fraction -> the AOI is haze-degraded this year. UNVERIFIABLE, not
                # a partial-haze "clear-cut".
                cur_ff = cur.get("forest_frac") or 0.0
                base_ff = base.get("forest_frac") or 0.0
                clearcut[yr] = {"status": "MISSING",
                                "reason": (f"haze-degraded: greenest {yr} scene forest_frac "
                                           f"{cur_ff:.2f} << baseline {base_ff:.2f} "
                                           f"(> {HAZE_FRAC_TOL:.2f} drop); candidate forest_fracs disagree "
                                           f"{cur.get('candidate_fracs')} -> UNVERIFIABLE, not a fell"),
                                "current_date": cur["date"],
                                "candidate_fracs": cur.get("candidate_fracs")}
                continue
            # Baseline->current spans (yr - baseline_year) years; annualize so the rate is
            # apples-to-apples with the ~0.9%/yr Swedish final-fell NORM. Span>=1. The span
            # also scales the bad-scene (uniform-collapse) threshold so a legitimate
            # multi-year cumulative fell isn't rejected as haze.
            span_years = max(1, yr - baseline_year)
            st = _clearcut_stats(base["ndvi"], cur["ndvi"], span_years=span_years)
            if st is None:
                clearcut[yr] = {"status": "MISSING", "reason": "no forested-baseline pixels"}
                continue
            if st.get("bad_scene"):
                # Near-total uniform NDVI collapse (> the span-scaled bad-scene threshold) =
                # thin haze/smoke, not a harvest. Reject as MISSING (never a fake catastrophe).
                thr = min(BAD_SCENE_CLEARED_FRAC_MAX, BAD_SCENE_CLEARED_FRAC_PER_YEAR * span_years)
                clearcut[yr] = {"status": "MISSING",
                                "reason": (f"bad scene rejected: {st['clearcut_frac']*100:.0f}% of forest "
                                           f"'dropped' over {span_years}y (> {thr*100:.0f}% -> uniform NDVI "
                                           "collapse = thin-haze contamination, not a fell)"),
                                "rejected_current_date": cur["date"],
                                "rejected_current_cloud": cur["cloud"]}
                continue
            frac = st["clearcut_frac"]
            band = _clearcut_band(frac, st["coverage_frac"], st["n_forest_px"])
            frac_annual = frac / span_years
            # Cloud-differential guard: a materially-cloudier current scene than baseline
            # makes this read low-confidence (residual haze inflates the drop). Widen the
            # band to cover the ambiguity and flag it so grading won't call ELEVATED off it.
            # A MISSING cloud value (eo:cloud_cover absent) is treated as UNKNOWN -> cannot
            # certify clean, so it counts as low-confidence (never silently 'clear').
            cur_cloud_raw, base_cloud_raw = cur["cloud"], base["cloud"]
            cur_cloud = cur_cloud_raw if cur_cloud_raw is not None else 0.0
            base_cloud = base_cloud_raw if base_cloud_raw is not None else 0.0
            cloud_unknown = cur_cloud_raw is None
            low_conf = cloud_unknown or (cur_cloud >= CLOUD_DIFF_LOWCONF_PCT and cur_cloud > base_cloud + 3.0)
            band_final = round(band / span_years, 2)
            if low_conf:
                # Inflate the band by the excess-cloud fraction as a haze-uncertainty term
                # (use a nominal 10% penalty when the cloud level is unknown).
                haze_pct = cur_cloud if not cloud_unknown else 10.0
                band_final = round(((band / span_years) ** 2 + (haze_pct * 0.15) ** 2) ** 0.5, 2)
            rec = {"status": "OK",
                   "clearcut_pct_cumulative": round(frac * 100.0, 2),
                   "clearcut_pct": round(frac_annual * 100.0, 2),   # <- annualized (the graded figure)
                   "span_years": span_years,
                   "band_pp": band_final,          # band scales down with span, up with cloud diff
                   "low_confidence": low_conf,
                   "low_confidence_reason": (
                       ("current-scene cloud UNKNOWN (eo:cloud_cover absent) -> cannot certify clean"
                        if cloud_unknown else
                        f"current-scene cloud {cur_cloud:.1f}% >> baseline {base_cloud:.1f}%")
                       if low_conf else None),
                   "coverage_frac": round(st["coverage_frac"], 3),
                   "n_forest_px": st["n_forest_px"], "n_cleared_px": st["n_cleared_px"],
                   "baseline_year": baseline_year, "baseline_date": base["date"],
                   "current_date": cur["date"],
                   "baseline_cloud": base["cloud"], "current_cloud": cur["cloud"]}
            clearcut[yr] = rec
            latest_cc = rec  # last OK year wins

        # Scene provenance (for the evidence trail; MISSING preserved).
        scenes = {yr: ({"date": per_year[yr]["date"], "cloud_pct": per_year[yr]["cloud"],
                        "coverage_frac": round(per_year[yr]["coverage_frac"], 3)}
                       if per_year[yr] else {"status": "MISSING (no cloud-free scene)"})
                  for yr in years}

        return {
            "aoi": aoi,
            "bbox": [round(v, 4) for v in bbox],
            "health_mean_ndvi": {str(k): (round(v, 4) if v is not None else None) for k, v in health.items()},
            "forest_mean_ndvi": {str(k): (round(v, 4) if v is not None else None) for k, v in forest_health.items()},
            "ndvi_yoy_delta": yoy_deltas,
            "clearcut_by_year": {str(k): v for k, v in clearcut.items()},
            "latest_clearcut": latest_cc,
            "scenes": {str(k): v for k, v in scenes.items()},
        }

    # ── ConnectorResult wrapper (single-AOI dispatch path) ───────────────────
    def query(self, request: ConnectorRequest) -> ConnectorResult:
        bbox, aoi = self._resolve_bbox(request)
        if bbox is None:
            return self._fail(request, ErrorKind.UNSUPPORTED,
                              "need extra.aoi{bbox|lat+lon} or extra.bbox/lat+lon")
        x = request.extra or {}
        years = [int(y) for y in x.get("years", [2024, 2025, 2026])]
        baseline_year = int(x.get("baseline_year", min(years)))
        ps, pe = x.get("peak_start_md", "06-01"), x.get("peak_end_md", "08-31")
        cloud_max = int(x.get("cloud_max", 30))

        res = self.analyze(bbox, aoi, years, baseline_year, ps, pe, cloud_max)
        cc = res.get("latest_clearcut")
        if cc is None and not any(v is not None for v in res["health_mean_ndvi"].values()):
            return self._fail(request, ErrorKind.NOT_FOUND,
                              "no usable summer scene in any requested year (all MISSING)")

        url = f"https://earth-search.aws.element84.com/v1 (S2 L2A summer NDVI, bbox {res['bbox']})"
        label = (aoi or {}).get("name", "AOI")
        obs = [
            ConnectorObservation(attribute="forest_health_mean_ndvi", value=res["health_mean_ndvi"],
                                 value_unit="NDVI", confidence=0.9, source_url=url,
                                 extra={"aoi": label, "yoy_delta": res["ndvi_yoy_delta"]}),
            ConnectorObservation(attribute="clearcut_pct_latest",
                                 value=(cc["clearcut_pct"] if cc else None),
                                 value_unit="%_of_baseline_forest_per_year",
                                 confidence=(0.5 if (cc and cc.get("low_confidence")) else 0.8),
                                 source_url=url,
                                 extra={"aoi": label, "band_pp": (cc["band_pp"] if cc else None),
                                        "coverage_frac": (cc["coverage_frac"] if cc else None),
                                        "low_confidence": (cc.get("low_confidence") if cc else None),
                                        "clearcut_pct_cumulative": (cc.get("clearcut_pct_cumulative") if cc else None),
                                        "span_years": (cc.get("span_years") if cc else None),
                                        "vs_swedish_norm_pct": SWEDISH_FINAL_FELL_NORM_PCT}),
            ConnectorObservation(attribute="clearcut_by_year", value=res["clearcut_by_year"],
                                 confidence=0.8, source_url=url, extra={"aoi": label}),
            ConnectorObservation(attribute="scenes", value=res["scenes"], confidence=1.0,
                                 source_url=url, extra={"aoi": label}),
        ]
        return self._ok(request, obs)
