"""dead_chain_pricer — derive the option price ENTIRELY from the model for a dead chain.

On a dead chain the mark is fiction and WE are the market, so nothing about the quote
comes from the tape: the price is re-derived from first principles —

    sigma   = max(RV_1y, RV_2y)  +  downside skew (0.30 vol pts per % OTM, K<S)
    theo    = AMERICAN put (CRR binomial, 400 steps — listed single-name puts are
              American; European BSM underprices the early-exercise right)
    ask     = theo re-priced at sigma + captivity margin (3-5 vol pts: the charge for
              being the only seller)
    floor   = an observed mark can only ever RAISE the ask (--mark), never lower it

The reverse mode is the per-leg staging gate: --check ASK reports implied vol vs the
skew-adjusted realized sigma and REFUSES any ask below theoretical. (Applied
retroactively: FAF experiment #1 filled at 3.40 vs theo 3.70 / reservation 4.41 —
at flat-vol actuarial but below fair once skew is counted; the ~$120-200 concession
is why this tool is now the mandatory staging step.)

LIQUID-CHAIN MODE (2026-08-05, principal correction on RDDT/NFLX/ISRG): pass the live
--bid/--ask and the tool prices the TWO-REGIME rule instead of quoting reservation:
    market above actuarial  -> MARKET-ANCHORED ask = max(reservation, ask - one tick
                               improvement); offering at the dead-chain reservation on a
                               live market is UNDERCUTTING (the FAF error's mirror)
    market below actuarial  -> DO NOT price down; rest ABOVE market at reservation as an
                               IV-spike limit, or drop the leg
Reservation is always the refuse-FLOOR, never the target, in both regimes.

Usage:
    python3 -m desk.dead_chain_pricer TICKER STRIKE EXPIRY [--spot S] [--div-yield q]
        [--margin 0.04] [--skew 0.30] [--mark M] [--rate 0.039] [--check ASK]
        [--closes-json FILE]

    --closes-json FILE  JSON list of daily closes (inject IBKR get_price_history bars
                        when Yahoo is rate-limited — paste, don't wait)

Price history FAILS LOUD on rate limits (never a silent default vol). Carry prints
pre-tax and after-tax against the CA-muni hurdle (premium = ST ordinary income).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys

TRADING_DAYS = 252
ST_TAX = 0.50           # short-term ordinary, fed+CA, the house's honest rate
MUNI_YIELD = 0.039      # CA muni tax-exempt yield, the after-tax hurdle
SGOV_YIELD = 0.043      # collateral yield stacked while the offer rests


def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def bsm_put(spot, strike, t_years, sigma, rate, div_yield) -> float:
    if t_years <= 0 or sigma <= 0:
        return max(strike - spot, 0.0)
    sq = sigma * math.sqrt(t_years)
    d1 = (math.log(spot / strike) + (rate - div_yield + sigma**2 / 2) * t_years) / sq
    d2 = d1 - sq
    return (strike * math.exp(-rate * t_years) * _norm_cdf(-d2)
            - spot * math.exp(-div_yield * t_years) * _norm_cdf(-d1))


def american_put(spot, strike, t_years, sigma, rate, div_yield, steps=400) -> float:
    """CRR binomial American put — listed single-name puts ARE American; BSM
    (European) underprices the early-exercise right, which matters at 4% rates."""
    if t_years <= 0 or sigma <= 0:
        return max(strike - spot, 0.0)
    dt = t_years / steps
    u = math.exp(sigma * math.sqrt(dt)); d = 1.0 / u
    disc = math.exp(-rate * dt)
    p = (math.exp((rate - div_yield) * dt) - d) / (u - d)
    p = min(max(p, 0.0), 1.0)
    vals = [max(strike - spot * (u ** j) * (d ** (steps - j)), 0.0) for j in range(steps + 1)]
    for i in range(steps - 1, -1, -1):
        for j in range(i + 1):
            cont = disc * (p * vals[j + 1] + (1 - p) * vals[j])
            ex = strike - spot * (u ** j) * (d ** (i - j))
            vals[j] = max(cont, ex)
    return vals[0]


def skew_bump(spot, strike, per_pct_otm=0.30) -> float:
    """Downside-skew adjustment in vol points: every liquid equity surface charges
    more vol for lower strikes (~0.2-0.4 pts per % OTM). Quoting a wing at flat
    ATM realized vol gives that premium away. Applied only for K < S."""
    otm_pct = max(-math.log(strike / spot), 0.0) * 100
    return (per_pct_otm / 100.0) * otm_pct


def implied_vol(price, spot, strike, t_years, rate, div_yield) -> float | None:
    lo, hi = 0.01, 2.0
    if not (bsm_put(spot, strike, t_years, lo, rate, div_yield) < price
            < bsm_put(spot, strike, t_years, hi, rate, div_yield)):
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if bsm_put(spot, strike, t_years, mid, rate, div_yield) < price:
            lo = mid
        else:
            hi = mid
    return mid


def realized_vols(closes: list[float]) -> dict:
    rets = [math.log(closes[i + 1] / closes[i]) for i in range(len(closes) - 1)]

    def ann(rs):
        if len(rs) < 40:
            return None
        m = sum(rs) / len(rs)
        var = sum((r - m) ** 2 for r in rs) / (len(rs) - 1)
        return math.sqrt(var * TRADING_DAYS)

    return {"rv_1y": ann(rets[-TRADING_DAYS:]), "rv_2y": ann(rets), "n_bars": len(closes)}


def fetch_closes(ticker: str):
    """yfinance daily closes, 2y. FAILS LOUD on rate limit — inject IBKR bars via
    --closes-json instead of waiting (the FAF post-mortem path)."""
    import warnings
    warnings.filterwarnings("ignore")
    import yfinance as yf
    try:
        h = yf.Ticker(ticker).history(period="2y")["Close"]
    except Exception as e:
        sys.exit(f"PRICE HISTORY UNAVAILABLE ({type(e).__name__}: {e}) — Yahoo is likely "
                 f"rate-limited. Pull daily bars from IBKR get_price_history and re-run "
                 f"with --closes-json FILE. NOT quoting a reservation ask on stale/no data.")
    closes = [float(x) for x in h.values if x == x]
    if len(closes) < 60:
        sys.exit(f"only {len(closes)} bars for {ticker} — refusing to quote off a thin series")
    return closes, yf.Ticker(ticker)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker")
    ap.add_argument("strike", type=float)
    ap.add_argument("expiry", help="YYYY-MM-DD")
    ap.add_argument("--spot", type=float, help="live spot (IBKR-verified preferred)")
    ap.add_argument("--div-yield", type=float, help="annual dividend yield, e.g. 0.029")
    ap.add_argument("--margin", type=float, default=0.04, help="captivity margin, vol pts")
    ap.add_argument("--skew", type=float, default=0.30,
                    help="downside skew, vol pts per %% OTM (0 disables)")
    ap.add_argument("--mark", type=float, help="observed mark - used ONLY as a floor on the ask")
    ap.add_argument("--bid", type=float, help="live market bid (liquid-chain mode)")
    ap.add_argument("--ask", type=float, help="live market ask (liquid-chain mode)")
    ap.add_argument("--rate", type=float, default=0.039)
    ap.add_argument("--check", type=float, help="grade this ask instead of quoting")
    ap.add_argument("--closes-json", help="JSON list of daily closes (IBKR bars)")
    a = ap.parse_args()

    tk = None
    if a.closes_json:
        closes = json.load(open(a.closes_json))
    else:
        closes, tk = fetch_closes(a.ticker)

    spot = a.spot
    if spot is None:
        if tk is None:
            sys.exit("--spot is required with --closes-json (use the live IBKR snapshot)")
        spot = float(closes[-1])
        print(f"[warn] spot from last close {spot:.2f} — pass --spot with the live IBKR "
              f"quote before staging (stale-spot rule)")
    q = a.div_yield
    if q is None:
        q = 0.0
        try:
            if tk is not None:
                q = float(tk.info.get("dividendYield") or 0.0)
                if q > 1:          # yfinance sometimes returns percent
                    q /= 100.0
        except Exception:
            pass
        print(f"[warn] div yield defaulted/fetched as {q:.3f} — verify against the filings")

    t_years = max((dt.date.fromisoformat(a.expiry) - dt.date.today()).days, 1) / 365.0
    rv = realized_vols(closes)
    sigma_atm = max(v for v in (rv["rv_1y"], rv["rv_2y"]) if v is not None)
    skew = skew_bump(spot, a.strike, a.skew)
    sigma = sigma_atm + skew

    theo = american_put(spot, a.strike, t_years, sigma, a.rate, q)
    euro = bsm_put(spot, a.strike, t_years, sigma, a.rate, q)
    ask = american_put(spot, a.strike, t_years, sigma + a.margin, a.rate, q)
    if a.mark is not None and a.mark > ask:
        print(f"[floor] observed mark {a.mark:.2f} > model reservation {ask:.2f} — "
              f"quote the mark (a floor only, NEVER a discount)")
        ask = a.mark

    def carry_lines(prem):
        gross = prem / a.strike / t_years
        stacked = gross + SGOV_YIELD
        after_tax = gross * (1 - ST_TAX) + SGOV_YIELD * (1 - ST_TAX)
        verdict = "CLEARS" if after_tax >= MUNI_YIELD else "FAILS"
        return (f"  yield on strike {gross*100:.2f}%/yr | stacked pre-tax {stacked*100:.2f}%"
                f" | after-tax {after_tax*100:.2f}% vs muni {MUNI_YIELD*100:.1f}% -> {verdict} the hurdle")

    print(f"\n{a.ticker} {a.expiry} {a.strike}p | spot {spot:.2f} | T {t_years:.2f}y | "
          f"q {q:.3f} | bars {rv['n_bars']}")
    print(f"realized vol: 1y {rv['rv_1y']*100:.1f}%"
          + (f" / 2y {rv['rv_2y']*100:.1f}%" if rv["rv_2y"] else "")
          + f" | skew +{skew*100:.1f} pts ({max(-math.log(a.strike/spot),0)*100:.1f}% OTM)"
          + f" -> pricing sigma {sigma*100:.1f}%")
    print(f"theoretical AMERICAN at sigma:  {theo:.2f}  (European {euro:.2f} — "
          f"early-exercise premium {theo-euro:.2f})")
    print(f"RESERVATION ASK (sigma+{a.margin*100:.0f}pt captivity): {ask:.2f}")
    print(carry_lines(ask))

    if a.ask is not None or a.bid is not None:
        print("\nLIQUID-CHAIN MODE (reservation = refuse-floor, never the target)")
        for label, px in (("bid", a.bid), ("ask", a.ask)):
            if px is not None:
                miv = implied_vol(px, spot, a.strike, t_years, a.rate, q)
                print(f"  market {label} {px:.2f} = implied vol "
                      f"{f'{miv*100:.1f}%' if miv else 'unresolvable'} vs actuarial {sigma*100:.1f}%")
        if a.ask is not None:
            tick = 0.05 if a.ask < 3.0 else 0.10
            join = round(a.ask - tick, 2)
            if join >= ask:
                rec = max(ask, join)
                riv = implied_vol(rec, spot, a.strike, t_years, a.rate, q)
                print(f"  REGIME: market ABOVE actuarial -> MARKET-ANCHORED ASK {rec:.2f} "
                      f"(one tick inside the {a.ask:.2f} ask, {rec-ask:+.2f} vs reservation"
                      f"{f', iv {riv*100:.1f}%' if riv else ''})")
                if a.bid is not None and a.bid >= ask:
                    print(f"  note: even the BID {a.bid:.2f} clears the floor — vol is rich; an "
                          f"immediate sale at the bid is legal, but offer at {rec:.2f} first")
                print(carry_lines(rec))
            else:
                print(f"  REGIME: market BELOW actuarial (ask {a.ask:.2f} < reservation {ask:.2f}) "
                      f"-> DO NOT PRICE DOWN. Rest ABOVE market at {ask:.2f} as an IV-spike "
                      f"limit, or drop the leg. Undercutting to market here is the FAF error.")
        elif a.bid is not None:
            print(f"  ask side missing — quote {max(ask, a.bid + 0.05):.2f} or better; never at/under "
                  f"the bid unless the bid itself clears the floor "
                  f"({'it does' if a.bid >= ask else 'it does NOT'})")

    if a.check is not None:
        iv = implied_vol(a.check, spot, a.strike, t_years, a.rate, q)
        iv_s = f"{iv*100:.1f}%" if iv else "unresolvable"
        ok = a.check >= theo
        print(f"\nCHECK ask {a.check:.2f}: implied vol {iv_s} vs RV {sigma*100:.1f}% -> "
              + ("PASS (at/above actuarial)" if ok else
                 f"REFUSE — prices {theo - a.check:.2f} below RV-theoretical; "
                 f"this is the FAF error, do not stage"))
        print(carry_lines(a.check))


if __name__ == "__main__":
    main()
