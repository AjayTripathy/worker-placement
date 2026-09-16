"""discovery_state(ticker, asof) — the Conditioning-Layer aggregator.

THE GOAL (do not lose it): this is the NO-EDGE control layer. It measures how DISCOVERED / CROWDED a
ticker already is, so the 120 divergence connectors can be filtered to UN-discovered names and the
signal-to-price latency mapped. It is the data-level version of the A/B control that killed the CEF
false positive. It does NOT predict returns; it conditions every other signal.

Contract (per CONDITIONING_LAYER_SPEC.md §C):
  {
    "ticker", "asof",
    "attention_score": 0..1,        # composite of the 4 attention sources (own-history + cross-section)
    "positioning_score": 0..1,      # composite of the 2 positioning sources
    "regime": "UNDISCOVERED" | "DISCOVERING" | "DISCOVERED_CROWDED",
    "components": {...},            # raw + per-source sub-scores, incl. UNAVAILABLE flags
    "confidence": "HIGH|MED|LOW",
    "asof_lags": {...}              # each source's own staleness in days
  }

Regime thresholds (spec §C, pre-set/tunable):
  UNDISCOVERED       = attention < 40th pctile AND short-interest < 10% AND no FTD spike
  DISCOVERED_CROWDED = attention > 80th pctile OR  short-interest > 20% OR  FTD spike
  else                 DISCOVERING

SCORING HONESTY:
  - Each attention component is mapped to a 0-1 sub-score against (a) the NAME'S OWN trailing history
    (the *_vs_baseline ratios the connectors already compute) and (b) a CROSS-SECTION anchor (fixed,
    documented saturation points — a proper cross-sectional percentile needs a universe panel, which is
    Phase 2; the fixed anchors are conservative stand-ins, flagged in components._scoring).
  - UNAVAILABLE components (Google Trends blocked, no Wikipedia article with 0 signal, GDELT 429) are
    DROPPED from the composite and lower the confidence — never imputed.
  - Lags are surfaced, never used to backfill. A stale positioning read down-weights confidence.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'helper',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ['public_equity', 'corporate_ipo_dd'],
    # 2026-08-08 (bespoke-promotion): universal — the standing doctrine is "gate every
    # divergence through the conditioning layer"; every court name is a public equity.
    "applies_universally": True,
    "summary": 'Conditioning layer: UNDISCOVERED/DISCOVERING/CROWDED — is the divergence already priced/crowded? Gate every divergence claim through it.',
}

from datetime import datetime, timezone
from typing import Any, Optional

from .base import ConnectorRequest
from .stocktwits import StockTwitsConnector
from .wikipedia_pageviews import WikipediaPageviewsConnector
from .gdelt_news import GdeltNewsConnector
from .google_trends import GoogleTrendsConnector
from .sec_ftd import SecFtdConnector
from .finra_short_interest import FinraShortInterestConnector
from .options_positioning import OptionsPositioningConnector
from .analyst_coverage import AnalystCoverageConnector
from .thirteenf_diff import ThirteenFDiffConnector

# Spec thresholds
ATTN_LOW_PCTILE = 0.40
ATTN_HIGH_PCTILE = 0.80
SI_PCT_LOW = 10.0
SI_PCT_HIGH = 20.0

# ── Phase 2: INSTITUTIONAL crowding ──────────────────────────────────────────
# Phase 1 was BLIND to institutional crowding — it read PODD (>$20B-class medtech, 20+ analysts, a
# press-released Class-I recall) as UNDISCOVERED because no retail channel was screaming. The
# institutional channel (options skew/IV + analyst density + 13F breadth) fixes that half.
INST_HIGH = 0.60        # institutional_score above this == institutionally DISCOVERED/PRICED
INST_LOW = 0.30         # below this == institutional channel confirms genuinely un-priced
# cap-tier guard: a name this big that reads UNDISCOVERED on RETAIL cannot be called UNDISCOVERED
# outright — the street watches every name this size. It must clear the institutional gate too.
CAP_TIER_GUARD_USD = 5_000_000_000        # $5B
# cross-section anchors for the institutional sub-scores (documented fixed stand-ins, like Phase 1):
_ANALYSTS_SAT = 20.0          # >=20 covering analysts == saturated institutional coverage
_FILERS_SAT = 400.0           # >=400 13F filers == saturated institutional breadth
_OPT_OI_SAT = 200_000.0       # >=200k contracts OI on one monthly == deep options crowding
_RR_SAT_PTS = 8.0             # 25d RR of +8 vol pts == heavy downside-insurance skew (full sub-score)
_IVPCT_SAT = 1.0              # IV-percentile-of-52wk already 0-1
_MODERATE_FILERS_CROWD = 100  # >=100 distinct 13F filers == institutionally crowded breadth
# When the single strongest attention channel exceeds this, the composite is pulled toward it
# (a name screaming on one retail channel is discovered even with no Wikipedia/news footprint).
_ATTN_DOMINANT = 0.70

# Cross-section saturation anchors (conservative fixed stand-ins until a universe panel exists).
# These map a raw level -> a 0-1 "how big vs the typical small/mid-cap" sub-score. Documented and
# surfaced so they can be replaced by an empirical percentile in Phase 2.
_ST_MSGS_PER_DAY_SAT = 200.0     # >=200 msgs/day on the 30-window == saturated retail attention
_WIKI_VIEWS_SAT = 5000.0         # >=5000 views/day == high public attention
_GDELT_VOL_SAT = 0.05            # GDELT normalized recent-vol that reads as "heavily covered"
_FTD_SHARES_SAT = 1_000_000.0    # >=1M-share daily fails == extreme FTD crowding


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _blend_own_xs(vs_baseline: Optional[float], xs_level: Optional[float], xs_sat: float) -> Optional[float]:
    """Combine the name's own-history ratio (centered at 1.0) with a cross-section saturation score.
    Returns None if both inputs are missing (component UNAVAILABLE)."""
    own = None
    if vs_baseline is not None and vs_baseline not in (float("inf"),):
        # ratio 1.0 -> 0.5 (at its own baseline); 2x -> ~0.75; 0.5x -> ~0.25
        own = _clip01(0.5 * vs_baseline) if vs_baseline <= 2 else _clip01(0.5 + 0.25 * min(vs_baseline - 2, 2) / 2)
    elif vs_baseline == float("inf"):
        own = 1.0
    xs = None
    if xs_level is not None:
        xs = _clip01(xs_level / xs_sat)
    if own is None and xs is None:
        return None
    if own is None:
        return xs
    if xs is None:
        return own
    # weight cross-section a bit higher (it anchors the absolute level)
    return _clip01(0.45 * own + 0.55 * xs)


def discovery_state(ticker: str, asof: Optional[str] = None,
                    company_name: Optional[str] = None,
                    float_shares: Optional[int] = None,
                    shares_outstanding: Optional[int] = None,
                    cusip: Optional[str] = None,
                    market_cap: Optional[float] = None,
                    mcp_options_underlying: Optional[dict] = None,
                    enable_options: bool = True,
                    enable_13f: bool = True) -> dict[str, Any]:
    """Compute the conditioning-layer discovery state for a ticker as-of a date.

    ticker                  : symbol (StockTwits/FTD/FINRA/options/analyst key)
    asof                    : 'YYYY-MM-DD' (point-in-time); defaults to today UTC
    company_name            : for Wikipedia + GDELT (name-indexed); defaults to ticker
    float/shares_out        : optional, enables short-interest % (FINRA feed has no float)
    cusip                   : enables the 13F-breadth institutional channel (FTS keys on CUSIP)
    market_cap              : enables the cap-tier guard; if None, taken from analyst_coverage feed
    mcp_options_underlying  : optional dict of IBKR-MCP underlying-level option fields (annual_iv,
                              hist_vol_annual, iv_pctile_52w, call_volume, put_volume, avg_call_volume,
                              avg_put_volume, last_price) — used when the TWS per-strike socket is down,
                              so the options channel still has REAL live data (not fabricated).
    enable_options/13f      : toggles the heavier institutional pulls.

    REGIME (Phase 2): a name with market_cap > $5B that is UNDISCOVERED on the RETAIL channels is
    DOWNGRADED to 'UNDISCOVERED_RETAIL_ONLY' (institutional UNVERIFIED) UNLESS the institutional
    channel positively confirms it is un-priced (low options skew/IV + sparse analyst coverage + no
    13F crowding). The street watches every $5B+ name; absence of retail noise is not absence of
    discovery.
    """
    asof = asof or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    name = company_name or ticker
    extra_common = {"asof": asof}

    components: dict[str, Any] = {"_scoring": {
        "note": "attention sub-scores blend the name's OWN trailing-history ratio with a fixed "
                "cross-section saturation anchor (true cross-sectional percentile = Phase 2 panel). "
                "UNAVAILABLE components are dropped and lower confidence; lags surfaced not backfilled.",
        "xs_anchors": {"stocktwits_msgs_per_day_sat": _ST_MSGS_PER_DAY_SAT,
                       "wiki_views_per_day_sat": _WIKI_VIEWS_SAT,
                       "gdelt_vol_sat": _GDELT_VOL_SAT, "ftd_shares_sat": _FTD_SHARES_SAT},
    }}
    asof_lags: dict[str, Any] = {}

    # ── Attention sources ────────────────────────────────────────────────────
    attn_subscores: dict[str, Optional[float]] = {}
    retail_attention_spike = False   # StockTwits 30-message window saturating in < 1 day

    # StockTwits (~live)
    st = StockTwitsConnector().query(ConnectorRequest(entity_name=ticker, extra=extra_common))
    if st.success:
        d = {o.attribute: o.value for o in st.observations}
        # capture the msgs_per_day observation's ceiling flag: the public stream is a 30-message
        # window, so when those 30 posts span < 1 day the velocity is CENSORED (undercounted) and
        # the name is high-velocity by definition (DXYZ posts 30 msgs in ~11h). Treat a saturated
        # sub-day window as high attention regardless of the raw msgs/day point estimate.
        mpd_obs = next((o for o in st.observations if o.attribute == "msgs_per_day"), None)
        ceiling = bool(mpd_obs and (mpd_obs.extra or {}).get("ceiling"))
        mpd = d.get("msgs_per_day")
        retail_attention_spike = ceiling
        if ceiling:
            sub = 1.0
        elif mpd is None:
            sub = None
        else:
            sub = _clip01(mpd / _ST_MSGS_PER_DAY_SAT)
        attn_subscores["stocktwits"] = sub
        components["stocktwits"] = {"message_count_30": d.get("message_count_30"),
                                    "msgs_per_day": mpd, "window_saturated_sub_day": ceiling,
                                    "bull_count": d.get("bull_count"),
                                    "bear_count": d.get("bear_count"),
                                    "bull_bear_ratio": d.get("bull_bear_ratio"),
                                    "tracked": d.get("stocktwits_tracked"), "subscore": sub}
        asof_lags["stocktwits"] = "~live (last-30-message window)"
    else:
        components["stocktwits"] = {"status": "UNAVAILABLE", "error": str(st.error_kind), "detail": st.error_detail}
        attn_subscores["stocktwits"] = None
        asof_lags["stocktwits"] = "unavailable"

    # Wikipedia pageviews (~1 day)
    wk = WikipediaPageviewsConnector().query(ConnectorRequest(entity_name=name, extra=extra_common))
    if wk.success:
        d = {o.attribute: o.value for o in wk.observations}
        if not d.get("has_article"):
            # no article == genuinely low public attention; a real (low) signal, not unavailable
            attn_subscores["wikipedia"] = 0.0
            components["wikipedia"] = {"has_article": False, "subscore": 0.0,
                                       "note": "no en.wikipedia article = low public attention"}
        else:
            recent7 = d.get("recent_views_7d") or 0
            per_day = recent7 / 7.0
            sub = _blend_own_xs(d.get("recent_vs_baseline"), per_day, _WIKI_VIEWS_SAT)
            attn_subscores["wikipedia"] = sub
            components["wikipedia"] = {"has_article": True, "wiki_title": d.get("wiki_title"),
                                       "recent_views_7d": recent7, "views_per_day": round(per_day, 1),
                                       "baseline_views_per_day": d.get("baseline_views_per_day"),
                                       "recent_vs_baseline": d.get("recent_vs_baseline"), "subscore": sub}
        asof_lags["wikipedia"] = "~1 day"
    else:
        components["wikipedia"] = {"status": "UNAVAILABLE", "error": str(wk.error_kind)}
        attn_subscores["wikipedia"] = None
        asof_lags["wikipedia"] = "unavailable"

    # GDELT news (~15 min; rate-limit prone)
    gd = GdeltNewsConnector().query(ConnectorRequest(entity_name=name, extra=extra_common))
    if gd.success:
        d = {o.attribute: o.value for o in gd.observations}
        recent = d.get("recent_vol_avg_7d")
        sub = _blend_own_xs(d.get("vol_vs_baseline"), recent, _GDELT_VOL_SAT)
        attn_subscores["gdelt"] = sub
        components["gdelt"] = {"recent_vol_avg_7d": recent, "baseline_vol_avg": d.get("baseline_vol_avg"),
                               "vol_vs_baseline": d.get("vol_vs_baseline"), "n_points": d.get("n_points"),
                               "subscore": sub}
        asof_lags["gdelt"] = "~15 min"
    else:
        components["gdelt"] = {"status": "UNAVAILABLE", "error": str(gd.error_kind), "detail": gd.error_detail}
        attn_subscores["gdelt"] = None
        asof_lags["gdelt"] = "unavailable (GDELT rate-limit)"

    # Google Trends (~1 day; usually blocked on cloud IP)
    gt = GoogleTrendsConnector().query(ConnectorRequest(entity_name=name, extra={**extra_common, "geo": "US"}))
    if gt.success:
        d = {o.attribute: o.value for o in gt.observations}
        recent = d.get("recent_interest_7d")
        sub = _blend_own_xs(d.get("interest_vs_baseline"), recent, 100.0)
        attn_subscores["google_trends"] = sub
        components["google_trends"] = {"recent_interest_7d": recent,
                                       "interest_vs_baseline": d.get("interest_vs_baseline"), "subscore": sub}
        asof_lags["google_trends"] = "~1 day"
    else:
        components["google_trends"] = {"status": "UNAVAILABLE", "error": str(gt.error_kind),
                                       "detail": "Google Trends blocks datacenter IPs (expected); "
                                                 "works opportunistically from residential IP / proxy"}
        attn_subscores["google_trends"] = None
        asof_lags["google_trends"] = "unavailable (Google Trends block)"

    # ── Positioning sources ──────────────────────────────────────────────────
    pos_subscores: dict[str, Optional[float]] = {}
    ftd_spike = False
    si_pct: Optional[float] = None
    days_to_cover: Optional[float] = None

    # SEC FTD (~1 month)
    ftd = SecFtdConnector().query(ConnectorRequest(entity_name=ticker, extra=extra_common))
    if ftd.success:
        d = {o.attribute: o.value for o in ftd.observations}
        max_fails = d.get("max_daily_fails") or 0
        ftd_spike = bool(d.get("ftd_spike"))
        sub = _clip01(max_fails / _FTD_SHARES_SAT)
        pos_subscores["ftd"] = sub
        components["ftd"] = {"max_daily_fails": max_fails, "mean_daily_fails": d.get("mean_daily_fails"),
                             "ftd_spike": ftd_spike, "file": d.get("ftd_file"), "subscore": sub}
        asof_lags["sec_ftd"] = f"{d.get('asof_lag_days')} days (SEC publishes bi-monthly w/ ~2-4wk delay)"
    else:
        components["ftd"] = {"status": "UNAVAILABLE", "error": str(ftd.error_kind), "detail": ftd.error_detail}
        pos_subscores["ftd"] = None
        asof_lags["sec_ftd"] = "unavailable"

    # FINRA short interest (~2 weeks)
    fi = FinraShortInterestConnector().query(ConnectorRequest(
        entity_name=ticker, extra={**extra_common, **({"float_shares": float_shares} if float_shares else {}),
                                   **({"shares_outstanding": shares_outstanding} if shares_outstanding else {})}))
    if fi.success:
        d = {o.attribute: o.value for o in fi.observations}
        si_pct = d.get("short_interest_pct")
        days_to_cover = d.get("days_to_cover")
        # sub-score: prefer SI% vs the 20% crowded line; fall back to days-to-cover vs ~10d
        if si_pct is not None:
            sub = _clip01(si_pct / SI_PCT_HIGH)
        elif days_to_cover is not None:
            sub = _clip01(days_to_cover / 10.0)
        else:
            sub = None
        pos_subscores["short_interest"] = sub
        components["short_interest"] = {"short_position_qty": d.get("short_position_qty"),
                                        "days_to_cover": days_to_cover, "short_interest_pct": si_pct,
                                        "short_change_pct": d.get("short_change_pct"),
                                        "settlement_date": d.get("settlement_date"),
                                        "si_crowded": d.get("si_crowded"), "subscore": sub,
                                        "note": ("si_pct from supplied shares" if si_pct is not None
                                                 else "si_pct UNAVAILABLE (no float supplied); using days_to_cover")}
        asof_lags["finra_short_interest"] = f"{d.get('asof_lag_days')} days (bi-monthly, ~1-2wk delay)"
    else:
        components["short_interest"] = {"status": "UNAVAILABLE", "error": str(fi.error_kind), "detail": fi.error_detail}
        pos_subscores["short_interest"] = None
        asof_lags["finra_short_interest"] = "unavailable"

    # ── Institutional sources (Phase 2) ──────────────────────────────────────
    inst_subscores: dict[str, Optional[float]] = {}
    options_priced_risk = False
    inst_breadth_crowded = False
    n_analysts: Optional[int] = None

    # analyst_coverage (yfinance; ~daily). Also our market_cap source if caller didn't pass one.
    ac = AnalystCoverageConnector().query(ConnectorRequest(entity_name=ticker, extra=extra_common))
    if ac.success:
        d = {o.attribute: o.value for o in ac.observations}
        n_analysts = d.get("n_analysts")
        if market_cap is None:
            market_cap = d.get("market_cap")
        # sub-score: analyst density vs saturation; proxy coverage maps to a level
        if n_analysts is not None:
            a_sub = _clip01(n_analysts / _ANALYSTS_SAT)
        else:
            lvl = d.get("coverage_level")
            a_sub = {"HEAVY": 0.85, "MODERATE": 0.5, "LIGHT": 0.2, "NONE": 0.0}.get(lvl)
        inst_subscores["analyst_coverage"] = a_sub
        components["analyst_coverage"] = {"n_analysts": n_analysts, "coverage_level": d.get("coverage_level"),
                                          "institutionally_watched": d.get("institutionally_watched"),
                                          "recommendation_mean": d.get("recommendation_mean"),
                                          "recommendation_key": d.get("recommendation_key"),
                                          "target_upside_pct": d.get("target_upside_pct"),
                                          "revision_direction": d.get("revision_direction"),
                                          "market_cap": d.get("market_cap"), "subscore": a_sub}
        asof_lags["analyst_coverage"] = "~1 day (Yahoo aggregates; individual revisions lag broker notes)"
    else:
        components["analyst_coverage"] = {"status": "UNAVAILABLE", "error": str(ac.error_kind),
                                          "detail": ac.error_detail}
        inst_subscores["analyst_coverage"] = None
        asof_lags["analyst_coverage"] = "unavailable"

    # options_positioning (IBKR/TWS per-strike skew; degrades to MCP underlying-level if injected)
    if enable_options:
        opt_extra = dict(extra_common)
        if mcp_options_underlying:
            opt_extra["mcp_underlying"] = mcp_options_underlying
        op = OptionsPositioningConnector().query(ConnectorRequest(entity_name=ticker, extra=opt_extra))
        if op.success:
            d = {o.attribute: o.value for o in op.observations}
            options_priced_risk = bool(d.get("options_priced_risk"))
            underlying_only = bool(d.get("underlying_level"))
            # sub-score: blend skew (RR) + OI crowding (per-strike path), or IV-percentile +
            # option-activity (underlying-level path). Either path yields a 0-1 institutional read.
            if not underlying_only:
                rr = d.get("rr_25d_vol_pts")
                total_oi = d.get("total_oi") or 0
                rr_sub = _clip01((rr / _RR_SAT_PTS)) if rr is not None and rr > 0 else 0.0
                oi_sub = _clip01(total_oi / _OPT_OI_SAT)
                o_sub = _clip01(0.55 * rr_sub + 0.45 * oi_sub)
            else:
                ivp = d.get("iv_pctile_52w")
                iv_hv = d.get("iv_over_hv")
                vva = d.get("option_volume_vs_avg")
                ivp_sub = _clip01(ivp / _IVPCT_SAT) if ivp is not None else None
                # vol-bid bonus: IV above realized adds; below realized (fear fading) subtracts
                bid = 0.0
                if iv_hv is not None:
                    bid = _clip01((iv_hv - 0.85) / 0.5)  # 0 at IV/HV=0.85, 1 at 1.35
                act = _clip01((vva - 1.0) / 1.0) if vva is not None else 0.0
                parts = [p for p in (ivp_sub, bid, act) if p is not None]
                o_sub = round(sum(parts) / len(parts), 3) if parts else None
            inst_subscores["options_positioning"] = o_sub
            components["options_positioning"] = {**{k: d.get(k) for k in (
                "spot", "expiry", "atm_iv_pct", "rr_25d_vol_pts", "put_oi_total", "call_oi_total",
                "total_oi", "pc_oi_ratio", "elevated_put_skew", "high_oi", "options_priced_risk",
                "hist_vol_pct", "iv_over_hv", "iv_pctile_52w", "total_option_volume",
                "option_volume_vs_avg", "elevated_iv_regime", "high_option_activity", "underlying_level")
                if d.get(k) is not None}, "subscore": o_sub}
            asof_lags["options_positioning"] = ("~live during RTH (TWS per-strike)" if not underlying_only
                                                else "~live underlying-level (IBKR MCP; per-strike skew degraded)")
        else:
            components["options_positioning"] = {"status": "UNAVAILABLE", "error": str(op.error_kind),
                                                 "detail": op.error_detail}
            inst_subscores["options_positioning"] = None
            asof_lags["options_positioning"] = "unavailable (TWS down / no MCP underlying injected)"
    else:
        components["options_positioning"] = {"status": "DISABLED (enable_options=False)"}
        inst_subscores["options_positioning"] = None

    # thirteenf_diff (EDGAR FTS; needs CUSIP). Filer-count breadth + QoQ direction.
    if enable_13f and cusip:
        tf = ThirteenFDiffConnector().query(ConnectorRequest(entity_name=ticker,
                                            extra={**extra_common, "cusip": cusip}))
        if tf.success:
            d = {o.attribute: o.value for o in tf.observations}
            n_cur = d.get("n_filers_current")
            inst_breadth_crowded = (n_cur is not None and n_cur >= _MODERATE_FILERS_CROWD)
            f_sub = _clip01((n_cur or 0) / _FILERS_SAT)
            inst_subscores["thirteenf"] = f_sub
            components["thirteenf"] = {"cusip": cusip, "n_filers_current": n_cur,
                                       "n_filers_prior": d.get("n_filers_prior"),
                                       "n_filers_change_pct": d.get("n_filers_change_pct"),
                                       "institutional_breadth": d.get("institutional_breadth"),
                                       "positioning_direction": d.get("positioning_direction"),
                                       "share_aggregate": d.get("sampled_shares"),
                                       "subscore": f_sub}
            asof_lags["thirteenf_diff"] = "45-135 days (13F-HR filed up to 45d after quarter-end)"
        else:
            components["thirteenf"] = {"status": "UNAVAILABLE", "error": str(tf.error_kind),
                                       "detail": tf.error_detail}
            inst_subscores["thirteenf"] = None
            asof_lags["thirteenf_diff"] = "unavailable"
    elif enable_13f:
        components["thirteenf"] = {"status": "UNVERIFIABLE (no CUSIP supplied; 13F FTS keys on CUSIP)"}
        inst_subscores["thirteenf"] = None
    else:
        components["thirteenf"] = {"status": "DISABLED (enable_13f=False)"}
        inst_subscores["thirteenf"] = None

    # ── Composites ───────────────────────────────────────────────────────────
    # Attention is a SATURATION-AWARE blend of mean and max, NOT a plain average. Rationale: the
    # "price led the mark via retail anticipation" case the spec targets (SPCX/DXYZ) screams on the
    # dominant RETAIL channel (StockTwits/Trends) while having little encyclopedic/news footprint —
    # a plain average would dilute a genuinely crowded name to UNDISCOVERED. So when any single
    # attention channel is extreme (>= _ATTN_DOMINANT), the composite is pulled toward that max:
    # one channel saturating == the name is discovered. In the normal regime the mean dominates.
    attn_vals = [v for v in attn_subscores.values() if v is not None]
    pos_vals = [v for v in pos_subscores.values() if v is not None]
    if attn_vals:
        a_mean = sum(attn_vals) / len(attn_vals)
        a_max = max(attn_vals)
        # weight on the max grows as the strongest channel saturates (0 below _ATTN_DOMINANT,
        # ramping to 0.7 at full saturation) — a single screaming retail channel can carry the name.
        sat = _clip01((a_max - _ATTN_DOMINANT) / (1.0 - _ATTN_DOMINANT)) if a_max > _ATTN_DOMINANT else 0.0
        w_max = 0.7 * sat
        attention_score = round((1 - w_max) * a_mean + w_max * a_max, 3)
    else:
        attention_score = None
    positioning_score = round(sum(pos_vals) / len(pos_vals), 3) if pos_vals else None

    # INSTITUTIONAL score — saturation-aware like attention: any one institutional channel saturating
    # (20+ analysts OR a deep options book with put skew OR 400+ 13F filers) is enough to call a name
    # institutionally discovered, so the composite is pulled toward the max when extreme.
    inst_vals = [v for v in inst_subscores.values() if v is not None]
    if inst_vals:
        i_mean = sum(inst_vals) / len(inst_vals)
        i_max = max(inst_vals)
        sat_i = _clip01((i_max - _ATTN_DOMINANT) / (1.0 - _ATTN_DOMINANT)) if i_max > _ATTN_DOMINANT else 0.0
        w_i = 0.6 * sat_i
        institutional_score = round((1 - w_i) * i_mean + w_i * i_max, 3)
    else:
        institutional_score = None

    components["_subscores"] = {"attention": attn_subscores, "positioning": pos_subscores,
                                "institutional": inst_subscores,
                                "attention_blend": ("saturation-aware mean/max" if attn_vals else None),
                                "institutional_blend": ("saturation-aware mean/max" if inst_vals else None)}

    # ── Regime (spec thresholds) ─────────────────────────────────────────────
    # attention_score IS the percentile proxy here (0-1). SI% from float when available.
    attn = attention_score if attention_score is not None else 0.0
    # CROWDED triggers (spec's OR set + one mechanism-grounded addition). The spec lists three
    # discrete spike triggers (attention >80th pctile OR SI >20% OR FTD spike); a StockTwits
    # 30-message window that SATURATES in under a day is the SAME class of discrete event — an
    # active retail-attention spike — so it is added as a fourth OR-trigger. This is grounded in
    # the discovery mechanism (a name posting 30 retail messages in <0.5 day is being actively
    # piled into), NOT curve-fit to any one validation name: it fires identically for SPCX/DXYZ/
    # RCAT (all sub-day windows) and stays silent for a quiet name like GROW (6-month window).
    inst = institutional_score if institutional_score is not None else None
    # RETAIL crowded triggers (Phase-1 set).
    retail_crowded = ((attn > ATTN_HIGH_PCTILE) or (si_pct is not None and si_pct > SI_PCT_HIGH)
                      or ftd_spike or retail_attention_spike)
    # INSTITUTIONAL crowded triggers (Phase-2). Any one is sufficient — the same OR logic the spec
    # uses for retail spikes: a name the street is already insuring/covering/holding is discovered.
    inst_crowded = ((inst is not None and inst > INST_HIGH) or options_priced_risk
                    or inst_breadth_crowded
                    or (n_analysts is not None and n_analysts >= 15))
    crowded = retail_crowded or inst_crowded

    si_low = (si_pct is None) or (si_pct < SI_PCT_LOW)
    retail_undiscovered = (attn < ATTN_LOW_PCTILE) and si_low and (not ftd_spike) and (not retail_attention_spike)

    # Institutional channel POSITIVELY confirms un-priced only when ALL available institutional reads
    # are quiet: low composite, no options-priced-risk, sparse coverage, no 13F crowding.
    inst_confirms_unpriced = (
        (inst is None or inst < INST_LOW) and (not options_priced_risk)
        and (not inst_breadth_crowded)
        and (n_analysts is None or n_analysts < 5)
    )
    # did we actually MEASURE the institutional channel? (>=1 inst sub-score present)
    inst_measured = len(inst_vals) >= 1

    big_cap = (market_cap is not None and market_cap > CAP_TIER_GUARD_USD)
    # FIX 2026-07-11: when we could NOT determine market_cap (analyst_coverage feed down → market_cap
    # None), the cap-tier guard used to silently disable and print a clean UNDISCOVERED on mega-caps
    # (false-flagged COHR, a ~$35B NVDA-partner, as UNDISCOVERED). An UNKNOWN cap must be treated
    # conservatively: we cannot confirm the name is small, so we cannot assert clean UNDISCOVERED.
    cap_unknown = market_cap is None

    if crowded:
        regime = "DISCOVERED_CROWDED"
    elif retail_undiscovered:
        # Phase-2 cap-tier guard: a >$5B name (or an UNKNOWN-cap name we can't confirm is small)
        # quiet on RETAIL cannot be called UNDISCOVERED outright.
        if (big_cap or cap_unknown) and not inst_confirms_unpriced:
            # institutional says priced, we never measured it, OR the cap is unverifiable → UNVERIFIED.
            regime = "UNDISCOVERED_RETAIL_ONLY"
        else:
            regime = "UNDISCOVERED"
    else:
        regime = "DISCOVERING"

    # which condition fired (auditability)
    fired = []
    if attn > ATTN_HIGH_PCTILE:
        fired.append(f"retail attention {attn:.2f} > {ATTN_HIGH_PCTILE}")
    if si_pct is not None and si_pct > SI_PCT_HIGH:
        fired.append(f"short_interest {si_pct}% > {SI_PCT_HIGH}%")
    if ftd_spike:
        fired.append("FTD spike")
    if retail_attention_spike:
        fired.append("live retail-attention spike (StockTwits 30-msg window saturated in < 1 day)")
    if inst is not None and inst > INST_HIGH:
        fired.append(f"institutional_score {inst:.2f} > {INST_HIGH}")
    if options_priced_risk:
        fired.append("options already pricing the risk (elevated put skew/IV + deep OI/activity)")
    if inst_breadth_crowded:
        fired.append(f"13F breadth crowded (>= {_MODERATE_FILERS_CROWD} filers)")
    if n_analysts is not None and n_analysts >= 15:
        fired.append(f"heavy analyst coverage ({n_analysts} analysts)")
    if regime == "UNDISCOVERED_RETAIL_ONLY":
        reason = ("institutional channel says PRICED" if (inst is not None and inst >= INST_LOW)
                  else "institutional channel UNVERIFIED (not measured)")
        fired.append(f"cap-tier guard: market_cap > ${CAP_TIER_GUARD_USD/1e9:.0f}B, quiet on retail but "
                     f"{reason} → downgraded from UNDISCOVERED")
    components["_regime_drivers"] = fired or (
        ["retail quiet + institutional channel confirms un-priced"] if regime == "UNDISCOVERED"
        else ["mid-range — discovering"])
    components["_regime_logic"] = {
        "retail_crowded": retail_crowded, "inst_crowded": inst_crowded,
        "retail_undiscovered": retail_undiscovered, "inst_confirms_unpriced": inst_confirms_unpriced,
        "inst_measured": inst_measured, "big_cap": big_cap, "market_cap": market_cap,
        "options_priced_risk": options_priced_risk, "inst_breadth_crowded": inst_breadth_crowded,
        "n_analysts": n_analysts}

    # ── Confidence ───────────────────────────────────────────────────────────
    n_attn_avail = len(attn_vals)
    n_pos_avail = len(pos_vals)
    n_inst_avail = len(inst_vals)
    have_si_pct = si_pct is not None
    # HIGH now also requires the institutional channel to be measured (the Phase-1-only blind spot).
    if n_attn_avail >= 3 and n_pos_avail >= 2 and have_si_pct and n_inst_avail >= 2:
        confidence = "HIGH"
    elif n_attn_avail >= 2 and n_pos_avail >= 1 and n_inst_avail >= 1:
        confidence = "MED"
    else:
        confidence = "LOW"

    # cap-tier label
    if market_cap is None:
        cap_tier = "UNKNOWN"
    elif market_cap >= 10e9:
        cap_tier = "LARGE (>=$10B)"
    elif market_cap >= CAP_TIER_GUARD_USD:
        cap_tier = "MID ($5-10B)"
    elif market_cap >= 2e9:
        cap_tier = "SMID ($2-5B)"
    elif market_cap >= 300e6:
        cap_tier = "SMALL ($0.3-2B)"
    else:
        cap_tier = "MICRO (<$0.3B)"

    return {
        "ticker": ticker,
        "asof": asof,
        "company_name": name,
        "market_cap": market_cap,
        "cap_tier": cap_tier,
        "attention_score": attention_score,        # RETAIL attention
        "positioning_score": positioning_score,    # RETAIL/short positioning
        "institutional_score": institutional_score,  # Phase 2: options skew/IV + analysts + 13F
        "regime": regime,
        "components": components,
        "confidence": confidence,
        "asof_lags": asof_lags,
        "n_sources_available": {"attention": n_attn_avail, "positioning": n_pos_avail,
                                "institutional": n_inst_avail},
    }


if __name__ == "__main__":
    import json
    st = discovery_state("RCAT", asof="2026-06-24", company_name="Red Cat Holdings",
                         shares_outstanding=122_742_361)
    print(json.dumps({k: v for k, v in st.items() if k != "components"}, indent=2))
    print("regime drivers:", st["components"].get("_regime_drivers"))


# ── Uniform-contract wrapper (bespoke-promotion 2026-08-08) ─────────────────────
# Lets the court pre-flight executor (desk/detector_preflight.py, R1.12) run the
# conditioning layer through the standard load_connector().query() path.
from .base import BaseConnector, ConnectorObservation, ConnectorResult, ErrorKind


class DiscoveryStateConnector(BaseConnector):
    source_id = "discovery_state"

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        x = request.extra or {}
        ticker = x.get("ticker") or request.entity_name
        if not ticker or " " in str(ticker):
            return self._fail(request, ErrorKind.UNSUPPORTED,
                              "discovery_state needs a TICKER (extra.ticker or entity_name)")
        st = discovery_state(str(ticker).upper(),
                             company_name=x.get("company_name"),
                             # headless court runs: options leg needs the broker MCP —
                             # off by default, degradation is SURFACED not hidden
                             enable_options=bool(x.get("enable_options", False)),
                             enable_13f=bool(x.get("enable_13f", True)))
        degraded = [k for k, v in (st.get("n_sources_available") or {}).items() if not v]
        conf_label = str(st.get("confidence") or "LOW")
        conf = {"HIGH": 0.9, "MED": 0.6, "LOW": 0.3}.get(conf_label, 0.3)
        return self._ok(request, [
            ConnectorObservation(attribute="discovery_regime", value=st.get("regime"),
                                 confidence=conf,
                                 extra={"confidence_label": conf_label,
                                        "degraded_layers": degraded,
                                        "asof_lags": st.get("asof_lags")}),
            ConnectorObservation(attribute="attention_score", value=st.get("attention_score")),
            ConnectorObservation(attribute="positioning_score", value=st.get("positioning_score")),
            ConnectorObservation(attribute="institutional_score", value=st.get("institutional_score"),
                                 extra={"cap_tier": st.get("cap_tier"),
                                        "note": "verify analyst count before trusting UNDISCOVERED "
                                                "when layers are degraded (RCAT lesson)"}),
        ], raw=__import__('json').dumps({k: v for k, v in st.items() if k != 'components'}, default=str))
