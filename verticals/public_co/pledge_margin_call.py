"""Triangulate a bounded margin-call band for an insider stock pledge.

WHAT THIS DOES (and does NOT do)
--------------------------------
The exact margin-call trigger price is UNVERIFIABLE from public data: it equals
loan / (pledged_shares x maintenance_LTV), and neither the loan principal nor the
maintenance covenant is disclosed in any SEC filing or even the UCC record. What
IS knowable is the pledge INCEPTION DATE (proxy time-series brackets it; a UCC-1
pins it to the day), and therefore the share PRICE at inception. A rational lender
sized the loan as advance_rate x shares x P_inception, so the two unknowns
collapse into a ratio:

    P_call / P_inception  =  advance_rate / maintenance_LTV

For a single cross-collateralized facility that has been topped up over time, the
call price is (advance_rate / maint_LTV) x the SHARE-WEIGHTED-AVERAGE inception
price across tranches. This module:
  1. takes the pledge time-series (date, cumulative pledged_shares) from proxies
     (+ optional precise UCC-1/UCC-3 dates),
  2. detects TOP-UP increments and anchors each to the price (or price WINDOW,
     when the exact top-up date is unknown) at that time,
  3. sweeps a coherent set of lender RISK PROFILES (advance_rate + maint_LTV move
     together — see LENDER_PROFILES),
  4. emits a BOUNDED call-price band + a central point estimate + a behavioral
     state vs the current price.

The output is a BAND + a STATE, never a single number, and is flagged
UNVERIFIABLE_BOUNDED. Pair with a Form-4 code-S monitor: if the current price is
below the whole band yet no forced sale (code S) has printed, the loan is either
conservatively levered or being actively maintained/topped — which is the signal.
"""
from __future__ import annotations

import sys
from bisect import bisect_left
from datetime import date, timedelta
from typing import Any, Optional

import httpx

# Lender RISK PROFILES for CONCENTRATED single-stock insider collateral (restricted,
# illiquid relative to position size). advance_rate (loan / collateral at inception)
# and maint_LTV (call when loan / collateral exceeds this) are POSITIVELY CORRELATED:
# both express one latent thing — the lender's risk appetite for this collateral. A
# desk that only advances 25% (cautious) does NOT also tolerate 70% LTV before calling
# (lax); those off-diagonal corners are internally incoherent. The earlier code took
# the full cartesian product and set the band from min(a/m) and max(a/m) — i.e. from
# exactly those incoherent corners — which manufactured a 2.8x-wide ratio band
# (P_call from 0.36x to 1.00x of inception: useless). Sweeping a coherent 1-parameter
# diagonal instead nearly halves it (~1.85x) with no new data. Each tuple is one
# self-consistent lender; index the middle one as the central point estimate.
LENDER_PROFILES = (
    # (advance_rate, maint_ltv, label) — ordered conservative -> aggressive
    (0.250, 0.600, "conservative"),   # low entry LTV, standard call buffer
    (0.375, 0.625, "standard"),       # central point estimate
    (0.500, 0.650, "aggressive"),     # high advance, higher call tolerance
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com/",
}


def fetch_price_series(ticker: str, years: int = 5,
                       end: Optional[str] = None,
                       assetclass: str = "stocks") -> list[tuple[str, float]]:
    """Daily close series from the Nasdaq historical API, ascending by date.
    Returns [(YYYY-MM-DD, close)]. (Stooq's bulk endpoint now requires an API
    key; the Nasdaq endpoint is keyless with browser headers.)

    `end` ("YYYY-MM-DD") caps the series at a historical date — the point-in-time
    seam for backtests, so no post-cutoff prices are ever fetched. Defaults to
    today (live)."""
    end_d = date.fromisoformat(end) if end else date.today()
    frm = end_d - timedelta(days=365 * years + 5)
    url = f"https://api.nasdaq.com/api/quote/{ticker.upper()}/historical"
    params = {"assetclass": assetclass, "fromdate": frm.isoformat(),
              "todate": end_d.isoformat(), "limit": "9999"}
    with httpx.Client(timeout=30, headers=HEADERS) as c:
        r = c.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    rows = (((data or {}).get("data") or {}).get("tradesTable") or {}).get("rows") or []
    out: list[tuple[str, float]] = []
    for row in rows:
        try:
            m, d, y = row["date"].split("/")
            iso = f"{y}-{int(m):02d}-{int(d):02d}"
            close = float(row["close"].replace("$", "").replace(",", ""))
            out.append((iso, close))
        except (ValueError, KeyError, AttributeError):
            continue
    out.sort()
    if end:  # defensive: never return a row past the cutoff
        out = [x for x in out if x[0] <= end]
    return out


def _price_on(series: list[tuple[str, float]], d: str) -> Optional[float]:
    """Close on or immediately before date d (nearest prior trading day)."""
    if not series:
        return None
    dates = [x[0] for x in series]
    i = bisect_left(dates, d)
    if i < len(dates) and dates[i] == d:
        return series[i][1]
    if i == 0:
        return series[0][1]
    return series[i - 1][1]


def _window_minmax(series: list[tuple[str, float]], d0: str, d1: str) -> tuple[Optional[float], Optional[float]]:
    """Min/max close over [d0, d1] inclusive — the inception price RANGE for an
    increment whose exact top-up date is unknown."""
    vals = [p for (dt, p) in series if d0 <= dt <= d1]
    if not vals:
        p = _price_on(series, d1)
        return p, p
    return min(vals), max(vals)


# --------------------------------------------------------------------------- #
# Concentration-conditioned advance-rate prior
# --------------------------------------------------------------------------- #
# A lender does NOT advance the same fraction against a concentrated, illiquid
# insider block as against a liquid marginable position: it can't be liquidated
# quickly without crashing the very collateral backing the loan, and an affiliate's
# resale is throttled by Rule 144 (~max(1% of shares out, 4-wk avg vol) per quarter).
# So the generic 0.50 advance ceiling is unrealistic for a position worth many days
# of volume / a big slice of float. We haircut the advance rate by two concentration
# metrics; a lower advance => a LOWER call price => more cushion (the concentrated
# borrower is harder to call, but the lender also knows the exit is slow).
PARTICIPATION = 0.15   # frac of ADV sellable per day without major market impact
_SEC_HDRS = {"User-Agent": "Signal OS Research backtest@signalos.local"}


def _lin(x: float, x0: float, x1: float, y0: float, y1: float) -> float:
    """Piecewise-linear ramp from (x0,y0) to (x1,y1), clamped outside [x0,x1]."""
    if x <= x0:
        return y0
    if x >= x1:
        return y1
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def _adv_asof(ticker: str, as_of: Optional[str], lookback_td: int = 60,
              assetclass: str = "stocks") -> Optional[float]:
    """Average daily volume over the ~lookback_td trading days ending at as_of.

    The Nasdaq historical API silently returns 0 rows for short date windows
    (<~1.5yr), so fetch a wide window and slice — same quirk fetch_price_series
    works around with a years-wide range."""
    end_d = date.fromisoformat(as_of) if as_of else date.today()
    frm = end_d - timedelta(days=365 * 3)
    url = f"https://api.nasdaq.com/api/quote/{ticker.upper()}/historical"
    params = {"assetclass": assetclass, "fromdate": frm.isoformat(),
              "todate": end_d.isoformat(), "limit": "9999"}
    try:
        with httpx.Client(timeout=30, headers=HEADERS) as c:
            r = c.get(url, params=params)
            r.raise_for_status()
            rows = ((((r.json() or {}).get("data") or {}).get("tradesTable") or {})
                    .get("rows") or [])
    except Exception:
        return None
    dated = []
    for row in rows:
        try:
            m, d, y = row["date"].split("/")
            iso = f"{y}-{int(m):02d}-{int(d):02d}"
            if as_of and iso > as_of:
                continue
            v = float(str(row["volume"]).replace(",", ""))
            dated.append((iso, v))
        except (ValueError, KeyError, AttributeError, TypeError):
            continue
    dated.sort()
    vols = [v for _, v in dated[-lookback_td:]]
    return sum(vols) / len(vols) if vols else None


def _shares_outstanding_asof(cik: str, cutoff: Optional[str]) -> Optional[float]:
    """Latest dei:EntityCommonStockSharesOutstanding with end <= cutoff (PIT)."""
    cik_padded = str(cik).lstrip("0").rjust(10, "0")
    url = (f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik_padded}"
           "/dei/EntityCommonStockSharesOutstanding.json")
    try:
        with httpx.Client(timeout=15, headers=_SEC_HDRS) as c:
            r = c.get(url)
            if r.status_code != 200:
                return None
            units = (r.json().get("units", {}) or {}).get("shares", []) or []
    except Exception:
        return None
    if cutoff:
        units = [u for u in units if u.get("end", "") <= cutoff]
    if not units:
        return None
    units.sort(key=lambda x: x.get("end", ""))
    return float(units[-1].get("val", 0)) or None


def concentration_haircut(ticker: str, cik: Optional[str], pledged_shares: int,
                          ref_date: Optional[str],
                          assetclass: str = "stocks") -> dict[str, Any]:
    """Haircut factor in (0,1] applied to the advance-rate ceiling, from how hard
    the pledged block is to liquidate. Liquidity (days-to-liquidate via ADV) and
    legal throttle (% of shares outstanding ~ Rule 144) each imply a haircut; take
    the more binding (min). Returns the factor + the metrics behind it."""
    adv = _adv_asof(ticker, ref_date, assetclass=assetclass)
    so = _shares_outstanding_asof(cik, ref_date) if cik else None

    dtl = (pledged_shares / (PARTICIPATION * adv)) if adv else None
    # liquidity haircut: <=5d liquidate -> 1.0 ; 60d+ -> 0.45
    h_liq = _lin(dtl, 5, 60, 1.0, 0.45) if dtl is not None else 1.0

    so_pct = (pledged_shares / so) if so else None
    # legal/float haircut: <=2% of SO -> 1.0 ; >=10% -> 0.60
    h_flt = _lin(so_pct, 0.02, 0.10, 1.0, 0.60) if so_pct is not None else 1.0

    h = min(h_liq, h_flt)
    return {
        "advance_haircut": round(h, 3),
        "adv_shares": round(adv) if adv else None,
        "days_to_liquidate": round(dtl, 1) if dtl is not None else None,
        "shares_outstanding": round(so) if so else None,
        "pct_shares_outstanding": round(so_pct * 100, 2) if so_pct is not None else None,
        "h_liquidity": round(h_liq, 3), "h_float": round(h_flt, 3),
        "ref_date": ref_date,
    }


def triangulate(
    ticker: str,
    pledge_observations: list[dict],
    current_price: Optional[float] = None,
    price_series: Optional[list[tuple[str, float]]] = None,
    earliest_pledge_date: Optional[str] = None,
    as_of: Optional[str] = None,
    cik: Optional[str] = None,
    apply_concentration: bool = True,
) -> dict[str, Any]:
    """Compute the bounded margin-call band for a pledge time-series.

    Args:
      ticker: equity ticker (used to fetch the price series if not supplied).
      pledge_observations: ascending list of
          {"date": "YYYY-MM-DD",            # as-of date of the disclosure
           "pledged_shares": int,           # CUMULATIVE pledged shares at that date
           "source": "424B4 | DEF 14A | UCC-1 | UCC-3",
           "exact_date": bool}              # True if the date is the precise top-up
                                            # date (UCC); False if only a record-date
                                            # snapshot (proxy) -> increment anchored
                                            # to the price WINDOW since the prior obs.
      current_price: override; defaults to the latest close in the series.
      earliest_pledge_date: "YYYY-MM-DD" hard floor on when a pledge could have
          occurred (e.g. an IPO lock-up that bars pledging until expiry, or the
          earliest dated Form-4/13D pledge evidence). Clamps the LOWER bound of
          any window-anchored tranche's price window, so a top-up known not to
          predate this date is not anchored to earlier (often much higher) prices.

    Returns a dict with per-tranche anchors, the weighted-average inception price
    RANGE, the call-price band, and the behavioral state vs current price.
    Signal is always UNVERIFIABLE_BOUNDED.
    """
    series = price_series if price_series is not None else fetch_price_series(ticker, end=as_of)
    if as_of:  # hard PIT guarantee regardless of how the series was supplied
        series = [x for x in series if x[0] <= as_of]
    if not series:
        return {"error": f"no_price_series_for_{ticker}", "signal": "UNVERIFIABLE_NO_PRICE"}
    if current_price is None:
        current_price = _price_on(series, as_of) if as_of else series[-1][1]
    obs = sorted(pledge_observations, key=lambda o: o["date"])

    # Build tranches: each increase in cumulative pledged_shares is a tranche.
    tranches = []
    prev_shares = 0
    prev_date = None
    for o in obs:
        cum = int(o["pledged_shares"])
        inc = cum - prev_shares
        if inc <= 0:
            prev_shares = cum
            prev_date = o["date"]
            continue
        exact = bool(o.get("exact_date"))
        if exact or prev_date is None:
            p = _price_on(series, o["date"])
            plo = phi = p
            window = o["date"]
        else:
            w_start = prev_date
            if earliest_pledge_date and earliest_pledge_date > w_start:
                w_start = earliest_pledge_date
            plo, phi = _window_minmax(series, w_start, o["date"])
            window = f"{w_start}..{o['date']}"
        tranches.append({
            "increment_shares": inc,
            "as_of": o["date"],
            "anchor_window": window,
            "source": o.get("source", "?"),
            "inception_price_low": round(plo, 2) if plo else None,
            "inception_price_high": round(phi, 2) if phi else None,
        })
        prev_shares = cum
        prev_date = o["date"]

    total_shares = sum(t["increment_shares"] for t in tranches)
    if total_shares == 0:
        return {"error": "no_positive_pledge_tranches", "signal": "UNVERIFIABLE_NO_PLEDGE"}

    # Share-weighted-average inception price RANGE (single cross-collateralized facility).
    wavg_low = sum(t["increment_shares"] * t["inception_price_low"] for t in tranches) / total_shares
    wavg_high = sum(t["increment_shares"] * t["inception_price_high"] for t in tranches) / total_shares

    # Concentration-conditioned advance prior: a lender haircuts the advance ceiling
    # for a block that is slow to liquidate (days-to-liquidate via ADV) or large vs
    # the float (Rule-144 resale throttle). Apply the (more binding) haircut to each
    # profile's advance rate BEFORE forming ratios, so a concentrated/illiquid pledge
    # gets a structurally lower call band than a small liquid one.
    haircut_info = None
    h = 1.0
    if apply_concentration:
        ref_date = tranches[-1]["as_of"]
        try:
            haircut_info = concentration_haircut(ticker, cik, total_shares, ref_date)
            h = haircut_info["advance_haircut"]
        except Exception as exc:  # data flake -> fall back to ungutted advance, flagged
            haircut_info = {"advance_haircut": 1.0, "error": str(exc), "ref_date": ref_date}
            h = 1.0
    profiles = [(a * h, m, label) for a, m, label in LENDER_PROFILES]

    ratios = [a / m for a, m, _ in profiles]
    ratio_lo, ratio_hi = min(ratios), max(ratios)
    # Call band: lowest-ratio profile x lowest inception .. highest-ratio profile x
    # highest inception. Profiles are a coherent diagonal (correlated a, m), so the
    # band no longer convolves incoherent off-diagonal corners.
    call_low = ratio_lo * wavg_low
    call_high = ratio_hi * wavg_high

    # Central point estimate: the middle (standard) profile x mid inception. Report
    # this alongside the band — the band alone is wide by construction; the point
    # estimate is what a single best-guess lender implies.
    wavg_mid = (wavg_low + wavg_high) / 2
    a_c, m_c, _ = profiles[len(profiles) // 2]
    call_central = (a_c / m_c) * wavg_mid

    scenarios = []
    for a, m, label in profiles:
        pc = (a / m) * wavg_mid
        scenarios.append({
            "profile": label, "advance_rate": round(a, 4), "maint_ltv": m,
            "call_price": round(pc, 2),
            "called_at_current": current_price <= pc,
        })

    # Behavioral state vs current price.
    if current_price > call_high:
        state = "ABOVE_BAND"
        read = ("Current price is above the entire standard call band — no margin "
                "call under any standard advance/maintenance assumption.")
    elif current_price < call_low:
        state = "BELOW_BAND"
        read = ("Current price is BELOW the entire standard call band — a standard-"
                "LTV loan would already be in margin-call territory. If no Form-4 "
                "code-S forced sale has printed, the loan is either conservatively "
                "levered (sub-standard advance rate) or being actively maintained / "
                "topped up. The absence of forced selling IS the signal.")
    else:
        state = "IN_BAND"
        read = ("Current price sits inside the standard call band — a margin call "
                "is plausible under some advance/maintenance assumptions but not "
                "others. Watch Form-4 code-S as the trigger confirmation.")

    n_called = sum(1 for s in scenarios if s["called_at_current"])
    dd_low = current_price / wavg_high - 1.0
    dd_high = current_price / wavg_low - 1.0

    return {
        "ticker": ticker.upper(),
        "current_price": round(current_price, 2),
        "current_price_asof": series[-1][0],
        "total_pledged_shares": total_shares,
        "tranches": tranches,
        "wavg_inception_price_range": [round(wavg_low, 2), round(wavg_high, 2)],
        "drawdown_from_inception_range_pct": [round(dd_low * 100, 1), round(dd_high * 100, 1)],
        "call_price_band": [round(call_low, 2), round(call_high, 2)],
        "call_price_central": round(call_central, 2),
        "implied_loan_range_usd": [
            round(min(a for a, _, _ in profiles) * total_shares * wavg_low),
            round(max(a for a, _, _ in profiles) * total_shares * wavg_high)],
        "current_collateral_value_usd": round(total_shares * current_price),
        "concentration_haircut": haircut_info,
        "scenario_grid": scenarios,
        "n_scenarios_calling_now": f"{n_called}/{len(scenarios)}",
        "behavioral_state": state,
        "read": read,
        "signal": "UNVERIFIABLE_BOUNDED",
        "_caveat": ("Loan principal and maintenance LTV are never disclosed; this "
                    "is a scenario band anchored to inception PRICE, not a trigger. "
                    "Top-ups re-anchor the weighted price; proxy-only dates bracket "
                    "increments to a window. Pull UCC-1/UCC-3 to pin dates+lender."),
    }


def triangulate_with_filings(
    ticker: str,
    cik: str,
    proxy_observations: list[dict],
    insider_name: Optional[str] = None,
    earliest_pledge_date: Optional[str] = None,
    current_price: Optional[float] = None,
    cutoff: Optional[str] = None,
    as_of: Optional[str] = None,
) -> dict[str, Any]:
    """Triangulate, but first mine EDGAR for a denser pledge time-series.

    Pulls the Form-4 footnote ladder and Schedule 13D/13G Item-6 bounds (via
    `pledge_filings`), merges any count-bearing Form-4 snapshots into the proxy
    observations as extra tranches, and clamps window anchoring to the earliest
    dated pledge evidence (or the supplied `earliest_pledge_date`, whichever is
    later). The mined evidence is attached to the result for transparency — when
    the issuer does NOT restate the pledge in Form 4s / 13Ds (as with CAI), the
    ladder is simply empty and the window is shrunk only by the supplied floor.

    Point-in-time seam: `cutoff` caps the mined filings (no post-cutoff Form-4/13D)
    and `as_of` caps the price series + current_price. In a backtest pass both =
    the evaluation date; `cutoff` defaults to `as_of` when only `as_of` is given.
    """
    from . import pledge_filings

    if cutoff is None and as_of is not None:
        cutoff = as_of
    mined = pledge_filings.gather_pledge_observations(cik, insider_name, until=cutoff)
    merged = sorted([o for o in (*proxy_observations, *mined["form4_count_observations"])
                     if not cutoff or o["date"] <= cutoff],
                    key=lambda o: o["date"])
    floor = max([d for d in (earliest_pledge_date,
                             mined["earliest_pledge_evidence_date"]) if d],
                default=None)
    res = triangulate(ticker, merged, current_price=current_price,
                      earliest_pledge_date=floor, as_of=as_of, cik=cik)
    res["filings_mining"] = {
        "form4_pledge_snapshots": mined["form4_ladder"],
        "schedule_13_pledge_bounds": mined["schedule_13_bounds"],
        "earliest_pledge_evidence_date": mined["earliest_pledge_evidence_date"],
        "window_floor_applied": floor,
        "note": ("Form-4 footnote ladder and 13D/13G Item-6 are EMPTY when the "
                 "issuer's insiders do not restate the pledge in those venues; "
                 "the window is then shrunk only by the supplied floor (e.g. an "
                 "IPO lock-up that legally bars pledging until expiry)."),
    }
    return res


if __name__ == "__main__":
    import json
    # Worked example: Caris (CAI) founder pledge.
    #   424B4 (filed 2025-06-20): 1,660,000 shares pledged at IPO.
    #   DEF 14A (filed 2026-04-23): grown to 25,000,000 shares.
    # The 23.34M-share top-up date is unknown. The IPO lock-up (180 days from the
    # 2025-06-20 prospectus -> 2025-12-17) explicitly bars "pledge, sell, or
    # contract to sell any common stock", so the top-up legally could NOT predate
    # 2025-12-17 -> that is the window floor.
    cai_obs = [
        {"date": "2025-06-20", "pledged_shares": 1_660_000, "source": "424B4", "exact_date": True},
        {"date": "2026-04-23", "pledged_shares": 25_000_000, "source": "DEF 14A", "exact_date": False},
    ]
    ticker = sys.argv[1] if len(sys.argv) > 1 else "CAI"
    cik = sys.argv[2] if len(sys.argv) > 2 else "2019410"
    res = triangulate_with_filings(
        ticker, cik, cai_obs, insider_name="Halbert",
        earliest_pledge_date="2025-12-17",
    )
    print(json.dumps(res, indent=2, default=str))
