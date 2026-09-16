"""ai_lppl — the critical-point member of the AI-capex break ensemble.

Frame: desk/models/ai_capex_break.py is the MECHANISM member (refinance wall + 2008-sequence
gates). This module is the agnostic complement: it asks the tape itself whether the AI complex
is in a critical regime, via two independent statistical signatures that require believing NO
story about OpenAI, capex, or credit:

1. LPPL (Sornette log-periodic power law). A bubble driven by imitation/herding grows
   SUPER-exponentially with accelerating log-periodic oscillations, and that trajectory has a
   finite-time singularity at critical time tc — the end of the regime (crash odds cluster
   at/before tc; tc is NOT a guaranteed crash date). Fit
        ln p(t) = A + B*(tc-t)^m + (tc-t)^m * [C1*cos(w*ln(tc-t)) + C2*sin(w*ln(tc-t))]
   with A,B,C1,C2 linearized by OLS inside a nonlinear search over (tc, m, w)
   [Filimonov & Sornette 2013 reparameterization]. Bounds: m in [0.1,0.9], w in [4,25],
   tc in (last_date, last_date + 2y]. >=25 random restarts; the reported tc is the
   distribution (median + IQR) across qualified converged restarts, not the single best fit.
   QUALIFICATION (all must hold, else NO_SIGNAL — a clean NO_SIGNAL is a valid vote):
     - R^2 > 0.8 on log price;
     - LPPL beats BOTH a plain power law A + B*(tc-t)^m and an exponential (ln p linear in t)
       on BIC (penalizes LPPL's 3 extra params — raw SSE always "wins");
     - B < 0 (super-exponential ACCELERATION into tc; B>0 fits a decelerating top, not a bubble);
     - >=2.5 log-periodic oscillations in-sample (w/2pi * ln(span ratio)) — fewer means the
       cosine is fitting noise, the classic LPPL false positive.

2. CRITICAL SLOWING DOWN (CSD). Near a bifurcation a system's recovery from shocks slows:
   rolling lag-1 autocorrelation AND rolling variance of returns both TREND up (Scheffer 2009).
   We compute 90d rolling lag-1 AC and variance on daily log returns (plus the same stats on
   30d realized vol as corroboration) and take the Kendall tau of each rolling stat over the
   final year. Both taus rising (>0.15) = AMBER; both strongly rising (>0.5) = RED. This is a
   regime thermometer, not a date.

Series: NVDA, SOXX, and an equal-weight AI-complex basket (NVDA, AVGO, ORCL, SMCI, VRT —
each normalized to 1.0 at the common start, averaged). ~3y of daily closes via yfinance.

Probability mapping (honest by construction): P_break_by_20xx is populated ONLY if LPPL is
MEANINGFUL on >=1 series, as the empirical mass of the qualified-restart tc distribution at
or before that year-end — i.e. it is CONDITIONAL on the LPPL bubble description being right,
and the notes say so. If LPPL is NO_SIGNAL everywhere, P stays null and the state comes from
CSD alone (GREEN/AMBER/RED); NO_SIGNAL as the member state means nothing was computable.

Output contract: desk/data/ai_ensemble/lppl.json (same shape as contagion.json).

    python3 -m desk.models.ai_lppl
"""
from __future__ import annotations

import json
import warnings
from datetime import date, timedelta
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "ai_ensemble" / "lppl.json"

# ── Parameters ────────────────────────────────────────────────────────────────
P = {
    "series": {  # name -> ticker list (len 1 = single name; len >1 = equal-weight basket)
        "NVDA": ["NVDA"],
        "SOXX": ["SOXX"],
        "AI_BASKET": ["NVDA", "AVGO", "ORCL", "SMCI", "VRT"],
    },
    "lookback": "3y",            # daily closes fetched per ticker
    "m_bounds": (0.1, 0.9),
    "w_bounds": (4.0, 25.0),
    "tc_horizon_td": 504,        # tc searched in (last_day, last_day + ~2y of trading days]
    "n_restarts": 25,            # random restarts of the (tc, m, w) search
    "r2_floor": 0.80,            # qualification: minimum R^2 on log price
    "min_oscillations": 2.5,     # qualification: in-sample log-periodic cycles
    "sse_basin_tol": 1.10,       # restarts within 10% of best SSE define the tc distribution
    "csd_ret_window": 90,        # rolling window for lag-1 AC and variance
    "csd_rv_window": 30,         # realized-vol window (annualized 30d)
    "csd_trend_days": 252,       # Kendall-tau trend measured over the final year
    "csd_rising_tau": 0.15,      # both taus above -> AMBER ("rising"; 0 would fire on noise)
    "csd_red_tau": 0.50,         # both taus above -> RED (spec threshold)
    "seed": 7,
}

TD_PER_YEAR = 252


# ── Data ──────────────────────────────────────────────────────────────────────
def fetch_closes(tickers):
    """Adjusted daily closes, per ticker, joined on common dates. Raises on any failure."""
    import pandas as pd
    import yfinance as yf

    cols = {}
    for t in tickers:
        df = yf.download(t, period=P["lookback"], auto_adjust=True, progress=False)
        close = df["Close"]
        if hasattr(close, "columns"):        # multi-index frame from newer yfinance
            close = close.iloc[:, 0]
        close = close.dropna()
        if len(close) < 400:
            raise RuntimeError(f"{t}: only {len(close)} closes — refusing to fit")
        cols[t] = close
    return pd.DataFrame(cols).dropna()


def build_series(closes_by_name):
    """name -> (dates, prices). Baskets = equal-weight average of start-normalized closes."""
    out = {}
    for name, tickers in P["series"].items():
        df = closes_by_name[tickers].dropna()
        norm = df / df.iloc[0]
        px = norm.mean(axis=1) if len(tickers) > 1 else norm.iloc[:, 0]
        out[name] = (px.index, px.to_numpy(float))
    return out


# ── LPPL fit (Filimonov-Sornette linearized-in-ABC form) ──────────────────────
def _lppl_sse(theta, t, y):
    """OLS out A,B,C1,C2 for fixed (tc, m, w); return (SSE, coeffs). Inf if infeasible."""
    tc, m, w = theta
    if tc <= t[-1] + 1e-6:
        return np.inf, None
    dt = tc - t
    f = dt ** m
    ldt = np.log(dt)
    X = np.column_stack([np.ones_like(t), f, f * np.cos(w * ldt), f * np.sin(w * ldt)])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    sse = float(resid @ resid)
    return (sse, coef) if np.isfinite(sse) else (np.inf, None)


def _powerlaw_sse(theta, t, y):
    """Baseline: ln p = A + B*(tc-t)^m (no oscillation). Same linearization trick."""
    tc, m = theta
    if tc <= t[-1] + 1e-6:
        return np.inf
    f = (tc - t) ** m
    X = np.column_stack([np.ones_like(t), f])
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    sse = float(resid @ resid)
    return sse if np.isfinite(sse) else np.inf


def _bic(sse, n, k):
    return n * np.log(max(sse, 1e-12) / n) + k * np.log(n)


def fit_lppl(dates, px, rng):
    """Full LPPL pipeline on one series: restarts, baselines, qualification. Returns dict."""
    from scipy.optimize import minimize

    y = np.log(px)
    n = len(y)
    t = np.arange(n, dtype=float)
    tc_lo, tc_hi = t[-1] + 5.0, t[-1] + P["tc_horizon_td"]
    bounds = [(tc_lo, tc_hi), P["m_bounds"], P["w_bounds"]]

    # -- restarts over (tc, m, w) --
    fits = []
    for _ in range(P["n_restarts"]):
        x0 = np.array([rng.uniform(tc_lo, tc_hi),
                       rng.uniform(*P["m_bounds"]),
                       rng.uniform(*P["w_bounds"])])
        res = minimize(lambda th: _lppl_sse(th, t, y)[0], x0,
                       method="Nelder-Mead", bounds=bounds,
                       options={"maxiter": 2000, "xatol": 1e-4, "fatol": 1e-10})
        if not np.isfinite(res.fun):
            continue
        sse, coef = _lppl_sse(res.x, t, y)
        if coef is None:
            continue
        fits.append({"tc": float(res.x[0]), "m": float(res.x[1]), "w": float(res.x[2]),
                     "sse": sse, "coef": coef, "converged": bool(res.success)})
    if not fits:
        return {"state": "NO_SIGNAL", "why": ["optimizer produced no finite fit"]}

    converged = [f for f in fits if f["converged"]] or fits
    best = min(converged, key=lambda f: f["sse"])
    tss = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - best["sse"] / tss
    A, B, C1, C2 = best["coef"]

    # -- baselines --
    slope, icpt = np.polyfit(t, y, 1)
    sse_exp = float(((y - (icpt + slope * t)) ** 2).sum())
    pl_best = np.inf
    for _ in range(10):
        x0 = np.array([rng.uniform(tc_lo, tc_hi), rng.uniform(*P["m_bounds"])])
        res = minimize(lambda th: _powerlaw_sse(th, t, y), x0, method="Nelder-Mead",
                       bounds=[(tc_lo, tc_hi), P["m_bounds"]], options={"maxiter": 1000})
        pl_best = min(pl_best, float(res.fun))
    bic_lppl, bic_pl, bic_exp = _bic(best["sse"], n, 7), _bic(pl_best, n, 4), _bic(sse_exp, n, 2)

    # -- qualification --
    n_osc = best["w"] / (2 * np.pi) * np.log((best["tc"] - t[0]) / (best["tc"] - t[-1]))
    why = []
    if r2 <= P["r2_floor"]:
        why.append(f"R^2 {r2:.3f} <= {P['r2_floor']}")
    if not (bic_lppl < bic_pl and bic_lppl < bic_exp):
        why.append(f"LPPL does not beat baselines on BIC ({bic_lppl:.0f} vs pl {bic_pl:.0f} / exp {bic_exp:.0f})")
    if B >= 0:
        why.append(f"B {B:+.3f} >= 0 — no super-exponential acceleration (decelerating top, not a bubble)")
    if n_osc < P["min_oscillations"]:
        why.append(f"only {n_osc:.1f} log-periodic oscillations in-sample (<{P['min_oscillations']})")
    warns = []   # non-fatal, but disclosed: boundary-pinned params = fragile fit
    for pname, val, (lo, hi) in (("m", best["m"], P["m_bounds"]), ("omega", best["w"], P["w_bounds"])):
        if val - lo < 1e-3 or hi - val < 1e-3:
            warns.append(f"{pname}={val:.3g} pinned at search bound [{lo},{hi}] — fit is fragile there")
    if best["tc"] >= tc_hi - 1.0:
        warns.append("tc pinned at the 2y horizon bound — treat the date as censored, not estimated")

    # -- tc distribution across the good basin --
    basin = [f for f in converged
             if f["sse"] <= best["sse"] * P["sse_basin_tol"]
             and (1 - f["sse"] / tss) > P["r2_floor"]]
    last_day = dates[-1].date() if hasattr(dates[-1], "date") else dates[-1]

    def to_date(tc_td):
        return last_day + timedelta(days=round((tc_td - t[-1]) * 365.25 / TD_PER_YEAR))

    tcs = sorted(f["tc"] for f in basin) or [best["tc"]]
    q25, q50, q75 = np.percentile(tcs, [25, 50, 75])

    return {
        "state": "MEANINGFUL" if not why else "NO_SIGNAL",
        "why": why or ["all qualification gates passed"],
        "warnings": warns,
        "r2": round(r2, 4), "m": round(best["m"], 3), "omega": round(best["w"], 2),
        "B": round(float(B), 4), "C_over_B": round(float(np.hypot(C1, C2) / abs(B)), 3) if B else None,
        "n_oscillations": round(float(n_osc), 2),
        "bic": {"lppl": round(bic_lppl, 1), "powerlaw": round(bic_pl, 1), "exp": round(bic_exp, 1)},
        "restarts": {"total": len(fits), "converged": len(converged), "in_best_basin": len(basin)},
        "tc_best": str(to_date(best["tc"])),
        "tc_median": str(to_date(q50)),
        "tc_iqr": [str(to_date(q25)), str(to_date(q75))],
        "_tc_dates": [to_date(v) for v in tcs],   # internal: for probability mapping
    }


# ── Critical slowing down ─────────────────────────────────────────────────────
def _tau_last_year(series):
    from scipy.stats import kendalltau
    x = series.dropna().to_numpy(float)[-P["csd_trend_days"]:]
    if len(x) < 60:
        return None
    tau, _ = kendalltau(np.arange(len(x)), x)
    return round(float(tau), 3)


def fit_csd(dates, px):
    """Rolling lag-1 AC + variance trends on returns and on 30d realized vol."""
    import pandas as pd
    r = pd.Series(np.diff(np.log(px)), index=dates[1:])
    w = P["csd_ret_window"]
    ac = r.rolling(w).corr(r.shift(1))
    var = r.rolling(w).var()
    rv = r.rolling(P["csd_rv_window"]).std() * np.sqrt(TD_PER_YEAR)
    rv_ac = rv.rolling(w).corr(rv.shift(1))
    rv_var = rv.rolling(w).var()

    taus = {"ret_ac_tau": _tau_last_year(ac), "ret_var_tau": _tau_last_year(var),
            "rv30_ac_tau": _tau_last_year(rv_ac), "rv30_var_tau": _tau_last_year(rv_var)}
    a, v = taus["ret_ac_tau"], taus["ret_var_tau"]
    if a is None or v is None:
        state = "NO_SIGNAL"
    elif a > P["csd_red_tau"] and v > P["csd_red_tau"]:
        state = "RED"
    elif a > P["csd_rising_tau"] and v > P["csd_rising_tau"]:
        state = "AMBER"
    else:
        state = "GREEN"
    return {"state": state, **taus,
            "note": f"state keyed on RETURN-series taus (rising>{P['csd_rising_tau']}, "
                    f"red>{P['csd_red_tau']}); rv30 stats are corroboration only"}


# ── Aggregation ───────────────────────────────────────────────────────────────
_SEV = {"GREEN": 0, "AMBER": 1, "RED": 2}


def aggregate(readings):
    """Member state + probability mapping from per-series LPPL/CSD readings."""
    notes = []
    csd_states = [r["csd"]["state"] for r in readings.values() if r["csd"]["state"] != "NO_SIGNAL"]
    meaningful = {k: r for k, r in readings.items() if r["lppl"].get("state") == "MEANINGFUL"}

    if not csd_states and not meaningful:
        return "NO_SIGNAL", None, None, ["neither CSD nor LPPL produced a usable reading"]

    state = max(csd_states, key=_SEV.get) if csd_states else "GREEN"
    if meaningful:
        bumped = min(_SEV[state] + 1, 2)
        notes.append(f"LPPL MEANINGFUL on {sorted(meaningful)} — CSD state {state} escalated one notch")
        state = [k for k, v in _SEV.items() if v == bumped][0]
    else:
        fails = {k: r["lppl"].get("why", ["no fit"]) for k, r in readings.items()}
        notes.append("LPPL NO_SIGNAL on all series — P_break left null; state is CSD-only. "
                     "Per-series failure reasons: " + json.dumps(fails))

    p27 = p28 = None
    if meaningful:
        pool = [d for r in meaningful.values() for d in r["lppl"]["_tc_dates"]]
        p27 = round(sum(d <= date(2027, 12, 31) for d in pool) / len(pool), 2)
        p28 = round(sum(d <= date(2028, 12, 31) for d in pool) / len(pool), 2)
        notes.append(f"P_break = empirical mass of the qualified-restart tc distribution (n={len(pool)}) "
                     "at year-end — CONDITIONAL on the LPPL bubble description being right, and tc is "
                     "the end of the super-exponential regime, not a guaranteed crash date")
    return state, p27, p28, notes


# ── Runner ────────────────────────────────────────────────────────────────────
def run():
    asof = str(date.today())
    rng = np.random.default_rng(P["seed"])
    try:
        all_tickers = sorted({t for ts in P["series"].values() for t in ts})
        closes = fetch_closes(all_tickers)
    except Exception as e:  # yfinance down / short history — report, don't fabricate
        return {"member": "lppl_csd", "asof": asof, "state": "DATA_MISSING",
                "reading": {}, "P_break_by_2027": None, "P_break_by_2028": None,
                "notes": [f"data fetch failed: {type(e).__name__}: {e}"]}

    readings = {}
    for name, (dates, px) in build_series(closes).items():
        readings[name] = {"lppl": fit_lppl(dates, px, rng), "csd": fit_csd(dates, px),
                          "n_obs": len(px), "window": [str(dates[0].date()), str(dates[-1].date())]}

    state, p27, p28, notes = aggregate(readings)
    notes.append(f"universe: NVDA, SOXX, equal-weight basket {P['series']['AI_BASKET']}; "
                 f"{P['n_restarts']} restarts, seed {P['seed']}")
    for r in readings.values():          # strip internal fields before serializing
        r["lppl"].pop("_tc_dates", None)
    return {"member": "lppl_csd", "asof": asof, "state": state, "reading": readings,
            "P_break_by_2027": p27, "P_break_by_2028": p28, "notes": notes}


def main():
    out = run()
    print(f"=== AI-LPPL / CSD — critical-point member ({out['asof']}) ===\n")
    print(f"STATE: {out['state']}   P_break_by_2027: {out['P_break_by_2027']}   "
          f"P_break_by_2028: {out['P_break_by_2028']}\n")
    for name, r in out["reading"].items():
        L, C = r["lppl"], r["csd"]
        print(f"-- {name}  ({r['n_obs']} closes, {r['window'][0]} .. {r['window'][1]}) --")
        if L.get("r2") is not None:
            print(f"  LPPL {L['state']}: R2 {L['r2']}  m {L['m']}  omega {L['omega']}  B {L['B']}  "
                  f"osc {L['n_oscillations']}")
            print(f"       tc best {L['tc_best']}  median {L['tc_median']}  IQR {L['tc_iqr']}  "
                  f"(basin {L['restarts']['in_best_basin']}/{L['restarts']['total']} restarts)")
            print(f"       BIC lppl {L['bic']['lppl']} vs powerlaw {L['bic']['powerlaw']} / exp {L['bic']['exp']}")
        else:
            print(f"  LPPL {L['state']}")
        for w in L.get("why", []):
            print(f"       - {w}")
        for w in L.get("warnings", []):
            print(f"       ! {w}")
        print(f"  CSD  {C['state']}: ret_ac tau {C['ret_ac_tau']}  ret_var tau {C['ret_var_tau']}  "
              f"(rv30: ac {C['rv30_ac_tau']} var {C['rv30_var_tau']})\n")
    print("-- notes --")
    for n in out["notes"]:
        print(f"  {n}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=1) + "\n")
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()
