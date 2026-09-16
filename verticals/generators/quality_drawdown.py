"""quality_drawdown — the generator pointed at where the money actually came from.

Built 2026-08-03 after a P&L attribution showed the uncomfortable thing: 94% of the
book's gains came from software, services, insurance and brands — HUBS, GCT, DFIN,
CTSH, SAP, BRBY, MNDY, KNSL, G, HRTG — while every generator we owned screened for
cheap-on-assets industrials, distributors and banks. We had industrialised the search
for a kind of name that produced none of our returns.

Calibrating on those nine winners at their entry prices gave one shared signature:

    entry vs the name's OWN 3-year high
    HUBS -77%  MNDY -77%  CTSH -53%  SAP -48%  G -47%
    DFIN -41%  KNSL -41%  GCT -38%   (HRTG -13%, the outlier)

Median −46%. Not cheap on book — cheap against ITS OWN history, while still being a
good business. That is the pattern this screens for: high-quality economics, a deep
drawdown from its own multiple, and revenue that is still growing (the guard that
separates a fallen compounder from a melting ice cube).

Deliberately NOT a value screen. Book value is not consulted anywhere. A name can
trade at 6x sales and pass if the economics and the drawdown qualify — that is the
point, and it is why the existing deep_value / EDINET / Euronext stack cannot find
these.

    python3 verticals/generators/quality_drawdown.py [--min-dd 0.35] [--max-dd 0.75]

Writes verticals/generators/data/QUALITY_DRAWDOWN.json (MERGE by ticker — history is
the point; a name's drawdown depth over time is itself the signal).
PROPOSES ONLY: every hit routes cause-check -> discovery_state -> court before staging.

DEFECTS FIXED 2026-08-03 from the ten-court back-test (each one is a name this screen ranked
highly and a court then had to reject for a reason the score could not see):
  P1-1 PATH BLINDNESS  - the premise is buying capitulation, but it fired on GWRE at +54% off
                         a 42-day low and PINS at +57% off any low. Added pct_off_52w_low /
                         days_since_52w_low and two exhaustion modes.
  P1-2 FX/ADR BASIS    - marketCap is in the QUOTE currency, revenue in the FILING currency;
                         TCOM's 0.46 P/S was pure artifact. Ratios now recomputed in one
                         currency, or SUPPRESSED and flagged when the rate is unavailable.
  P1-3 FORWARD GUIDE   - BSX showed trailing revenue +8% while guiding +3-5%. Trailing growth
                         is the wrong tense for a de-rate thesis; now scored on forward/trailing.
  P1-4 FACTOR COSTUME  - AEM's drawdown WAS the gold price. Returns are regressed on the
                         sector's factor proxy and the drawdown re-run on the residual; if
                         under 60% of the fall survives, it is beta in costume.
  P2-5 GAAP MIXING     - GWRE's -65% "earnings growth" was FX. Earnings growth is suppressed
                         when it diverges from revenue by more than 45pp.
  P2-7 STALENESS       - read QUARTERLY financials (annual is ~1y stale by construction) and
                         flag a quarter-end older than ~4.5 months.
Back-test after the fixes: rank correlation vs the courts' own scores went from NEGATIVE to
+0.61. AEM 96.5->18.8, GWRE 91.5->26.8, PINS 99.2->44.7, while both 6/10 STARTERs (ISRG, DSGX)
held at 92.9. P2-6 (recurring-revenue multiple gate) NOT built - it needs segment-level data
this rail does not carry; left as an honest gap rather than a fake proxy.

DO NOT port the earnings-durability guard from euronext_shelf into this screen - the back-test
showed it BLOCKS HUBS, our single best position.

DEFECTS FOUND 2026-08-17 by the FIRST SIX COURTS this lane ever produced (2 trap-verify kills,
3 adjudicated, 1 validator-stuck). Every one is an admission ticket the score could not see was
counterfeit — i.e. the QUALITY inputs, which are this lane's whole differentiator, are the weak rail:
  Q1 EXTRACTIVE METRICS ARE NOT COMMENSURABLE (AGI, killed) - a miner's "gross margin" 70.8% is a
      CASH-COST construction excluding D&A and all capital, and its ROE 27.4% is struck on a
      cycle-peak realised price ($4,504/oz). Percentile-ranking those against a software cohort is
      a category error. Worse, fwd_rev_growth 27.6% was 100% PRICE DECK while guided VOLUME was cut
      -12%. FIX: exclude extractives, or carry all-in-sustaining-cost margins and VOLUME-based
      forward growth for them. NOT YET BUILT.
  Q2 ONE-TIME GAINS INFLATE ROE (GRAB, killed) - ROE 7.7% sat on $19M of operating profit against
      $235M of reported profit: a $307M consolidation remeasurement gain plus $66M of DTA
      recognition. Corrected ROE ~0.5-2%. The existing earnings_growth suppression (45pp vs revenue)
      does not catch this because it never compares NET income to OPERATING income. FIX: suppress or
      flag roe_pct when net income diverges from operating income beyond a threshold. NOT YET BUILT.
  Q3 FX-INFLATED GROWTH (AVPT, adjudicated) - 61% non-USD revenue and 3pts of FX in headline growth;
      constant-currency growth is ~19-20% vs the ~22-27% the screen scored. That single correction
      moved the name from "cheap-ish" to "fairly priced". FIX: prefer the issuer's FX-adjusted growth
      where disclosed. NOT YET BUILT.
  Q4 THE FACTOR-COSTUME CHECK DISAGREED WITH THE BENCH AND THE BENCH WAS RIGHT (AGI) - the screen
      computed residual_share 0.83 (i.e. "not costume") while the court measured AGI -38.0% against
      gold -21.1% = 1.80x beta and called it ordinary senior-producer beta. A high-beta name leaves a
      large residual against a beta-naive regression, so the current test cannot distinguish
      "idiosyncratic" from "amplified factor". FIX: judge the residual against the name's FITTED beta,
      not against the raw factor move. THIS IS A BUG, not a tuning question. NOT YET BUILT.
Recorded rather than silently patched: each fix changes what the lane admits, so they belong in a
dated back-test against the winners (the HUBS guard precedent — a plausible-sounding quality filter
already proved capable of blocking our single best position).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "verticals" / "generators" / "data" / "QUALITY_DRAWDOWN.json"

# Calibrated on the nine winners. The band matters: shallower than ~30% is noise,
# deeper than ~80% usually means the business broke rather than the multiple.
MIN_DD, MAX_DD = 0.35, 0.78
MIN_GROSS_MARGIN = 0.35          # the quality gate that book value cannot see
MIN_REV_CAGR_3Y = -0.02          # still growing, or at worst flat — the ice-cube guard
MAX_NET_DEBT_EBITDA = 3.5
MIN_MKTCAP = 400e6
MAX_OFF_LOW = 0.35               # P1-1 path: >35% off a fresh low = the entry is exhausted
FRESH_LOW_DAYS = 90              # ...and "fresh" means the low is younger than this
HARD_OFF_LOW = 0.50              # >50% off ANY low = the capitulation trade is over regardless of date
# P1-3: forward growth < 60% of trailing = decelerating. DO NOT RAISE THIS TO CATCH BSX.
# Cohort ratios center at 0.74 (p25 0.50, p75 1.16) — mild deceleration is the norm, not a tell.
# BSX (court 4/10 PASS) sits at 0.61 and ISRG (court 6/10 ENTER) at 0.68: four percentile points
# apart, so no aggregate threshold separates them. At 0.60 the gate fires only in the tail and is
# 3-for-3 on court rejections (AEM 0.08, ALNY 0.43, GWRE 0.57) with no false positive on a pass.
# The BSX miss is a RECALL HOLE THAT CANNOT BE CLOSED HERE: its break was segment-level
# (electrophysiology decelerating) and the consolidated ratio averages it away. Fixing it needs
# segment revenue, not a tighter cliff — see the segment-level-flooring rule.
FWD_TRAIL_FLOOR = 0.60
STALE_DAYS = 135                 # P2-7: a quarter-end older than ~4.5 months means the print is overdue/missing


def _f(x, d=None):
    try:
        v = float(x)
        return d if (v != v or math.isinf(v)) else v
    except Exception:
        return d


def universe():
    """Yahoo's server-side screener — the same rail broken_print_radar uses. Pulls US
    names above the cap floor with a gross-margin quality prefilter, so the expensive
    per-name work only runs on plausible candidates. FAILS LOUD: a silent empty
    universe is indistinguishable from 'no candidates found'."""
    import yfinance as yf
    from yfinance import EquityQuery
    syms, seen = [], set()
    # paginate the cap ladder — one query cannot return the whole mid/large universe
    bands = [(4e11, 1e13), (1e11, 4e11), (4e10, 1e11), (1.5e10, 4e10),
             (7e9, 1.5e10), (3e9, 7e9), (1.2e9, 3e9), (MIN_MKTCAP, 1.2e9)]
    for lo, hi in bands:
        q = EquityQuery("and", [
            EquityQuery("gte", ["intradaymarketcap", lo]),
            EquityQuery("lt", ["intradaymarketcap", hi]),
            EquityQuery("eq", ["region", "us"]),
        ])
        try:
            res = yf.screen(q, size=250, sortField="intradaymarketcap", sortAsc=False)
            for r in (res.get("quotes") or []):
                t = r.get("symbol")
                ex = r.get("fullExchangeName") or ""
                if t and t not in seen and "OTC" not in ex.upper() and "PINK" not in ex.upper():
                    seen.add(t); syms.append(t)
        except Exception as e:
            print(f"[warn] screener band {lo:.0e}-{hi:.0e} failed: {type(e).__name__}")
        time.sleep(0.4)
    if len(syms) < 300:
        raise SystemExit(f"universe only {len(syms)} names — refusing to run a screen "
                         f"that would report 'no candidates' for the wrong reason")
    return syms


# Factor proxies for defect P1-4 (AEM: "beta in costume"). A drawdown that is just the
# dominant sector factor is not a quality de-rate, however good the economics look.
FACTOR_PROXY = {
    "Basic Materials": "GLD", "Energy": "XLE", "Real Estate": "VNQ",
    "Utilities": "XLU", "Financial Services": "XLF",
}
RESIDUAL_DD_RATIO = 0.60      # residual DD must be >=60% of the raw DD, else the factor owns it


def _fx_to_usd(cur: str) -> float | None:
    """Defect P1-2: yfinance reports marketCap in the QUOTE currency and revenue in the
    FILING currency. For ADRs those differ (TCOM: USD cap over CNY revenue -> a 0.46 P/S
    that is pure artifact). Convert rather than compare across units."""
    if not cur or cur.upper() == "USD":
        return 1.0
    import yfinance as yf
    for sym in (f"{cur.upper()}USD=X", f"USD{cur.upper()}=X"):
        try:
            h = yf.Ticker(sym).history(period="5d")["Close"].dropna()
            if len(h):
                r = float(h.iloc[-1])
                return r if sym.startswith(cur.upper()) else 1.0 / r
        except Exception:
            pass
    return None


def _residual_drawdown(tk: str, sector: str, hist):
    """Regress daily returns on the sector's factor proxy and re-run the drawdown on the
    residual. Returns (residual_dd, beta, proxy) or (None, None, None) when not applicable."""
    proxy = FACTOR_PROXY.get(sector or "")
    if not proxy:
        return None, None, None
    import yfinance as yf
    try:
        f = yf.Ticker(proxy).history(period="3y")["Close"].dropna()
        j = hist.to_frame("x").join(f.to_frame("f"), how="inner").dropna()
        if len(j) < 250:
            return None, None, proxy
        rx = j["x"].pct_change().dropna(); rf = j["f"].pct_change().dropna()
        n = min(len(rx), len(rf)); rx, rf = rx[-n:], rf[-n:]
        vf = float((rf * rf).mean() - rf.mean() ** 2)
        if vf <= 0:
            return None, None, proxy
        beta = float((rx * rf).mean() - rx.mean() * rf.mean()) / vf
        resid = rx - beta * rf                       # factor-neutral return stream
        curve, lvl, peak, mdd = [], 1.0, 1.0, 0.0
        for r in resid:
            lvl *= (1 + r); peak = max(peak, lvl)
            mdd = min(mdd, lvl / peak - 1)
        return abs(mdd), beta, proxy
    except Exception:
        return None, None, proxy


def assess(tk: str):
    import yfinance as yf
    t = yf.Ticker(tk)
    h = t.history(period="3y")["Close"].dropna()
    if len(h) < 400:
        return None
    px, hi, lo = float(h.iloc[-1]), float(h.max()), float(h.min())
    dd = 1 - px / hi
    if not (MIN_DD <= dd <= MAX_DD):
        return None                      # cheap screen first — info costs a call

    # ---- defect P1-1: PATH. The screen's premise is buying capitulation; without these
    # it fired on GWRE at +54% off a 42-day low. A deep drawdown you are late to is a
    # different trade from a deep drawdown you are early to.
    h52 = h.tail(252)
    lo52 = float(h52.min()); lo52_date = h52.idxmin()
    off_low52 = px / lo52 - 1
    days_since_low = int((h.index[-1] - lo52_date).days)
    # Two exhaustion modes, both "you are late": a big bounce off a FRESH low (GWRE,
    # +54% off 42 days) or a very big bounce off any low (PINS, +57% off 170 days).
    exhausted = (off_low52 > MAX_OFF_LOW and days_since_low < FRESH_LOW_DAYS) or \
                (off_low52 > HARD_OFF_LOW)

    info = t.info or {}
    cap = _f(info.get("marketCap"), 0)
    if cap < MIN_MKTCAP:
        return None
    gm = _f(info.get("grossMargins"))
    if gm is None or gm < MIN_GROSS_MARGIN:
        return None

    # ---- defect P1-2: FX/ADR basis. Put cap and revenue in the SAME currency before
    # any ratio. Flag rather than silently emit a corrupt multiple.
    fin_cur = (info.get("financialCurrency") or "USD").upper()
    quote_cur = (info.get("currency") or "USD").upper()
    fx_note, ps_clean = None, _f(info.get("priceToSalesTrailing12Months"))
    if fin_cur != quote_cur:
        rate = _fx_to_usd(fin_cur)
        rev_local = _f(info.get("totalRevenue"))
        if rate and rev_local:
            ps_clean = cap / (rev_local * rate)
            fx_note = f"P/S recomputed: cap {quote_cur} vs revenue {fin_cur} (raw {_f(info.get('priceToSalesTrailing12Months'))} -> {ps_clean:.2f})"
        else:
            ps_clean, fx_note = None, f"CURRENCY MISMATCH {quote_cur}/{fin_cur} — ratios SUPPRESSED, unverifiable"

    # the ice-cube guard: is revenue still growing?
    rev_cagr = None
    try:
        fin = t.financials
        if fin is not None and "Total Revenue" in fin.index and fin.shape[1] >= 3:
            r = [_f(v) for v in fin.loc["Total Revenue"].values if _f(v)]
            if len(r) >= 3 and r[-1] > 0:
                rev_cagr = (r[0] / r[-1]) ** (1 / (len(r) - 1)) - 1
    except Exception:
        pass
    if rev_cagr is not None and rev_cagr < MIN_REV_CAGR_3Y:
        return None

    # ---- defect P1-3: FORWARD-GUIDE gate. BSX showed trailing revenue +8% while the
    # company guided +3-5%. Trailing growth is the wrong tense for a de-rate thesis.
    fwd_rev_growth, guide_ratio = None, None
    try:
        re_ = t.revenue_estimate
        if re_ is not None and "+1y" in re_.index:
            fwd_rev_growth = _f(re_.loc["+1y", "growth"])
    except Exception:
        pass
    trail_rev_growth = _f(info.get("revenueGrowth"))
    if fwd_rev_growth is not None and trail_rev_growth and trail_rev_growth > 0:
        guide_ratio = fwd_rev_growth / trail_rev_growth
    guide_flag = (guide_ratio is not None and guide_ratio < FWD_TRAIL_FLOOR)

    # ---- defect P2-5: GAAP/non-GAAP mixing. Suppress earnings-growth when the move is
    # not coming from operations (GWRE's -65% was FX; PINS's -3% op margin is seasonality).
    earn_growth = _f(info.get("earningsGrowth"))
    earn_note = None
    if earn_growth is not None and trail_rev_growth is not None:
        if abs(earn_growth) > 0.40 and abs(earn_growth - trail_rev_growth) > 0.45:
            earn_note = ("earnings growth SUPPRESSED — diverges from revenue by "
                         f"{abs(earn_growth - trail_rev_growth)*100:.0f}pp; likely non-operating "
                         "(FX/one-offs). Verify in the filing before using.")
            earn_growth = None

    ebitda = _f(info.get("ebitda"))
    nd = _f(info.get("totalDebt"), 0) - _f(info.get("totalCash"), 0)
    lev = (nd / ebitda) if (ebitda and ebitda > 0) else None
    if lev is not None and lev > MAX_NET_DEBT_EBITDA:
        return None

    # ---- defect P1-4: FACTOR-BETA gate. Is the drawdown just the sector factor?
    sector = info.get("sector")
    resid_dd, fbeta, proxy = _residual_drawdown(tk, sector, h)
    # ratio, not level: what fraction of the fall survives removing the sector factor?
    factor_costume = (resid_dd is not None and dd > 0 and (resid_dd / dd) < RESIDUAL_DD_RATIO)
    resid_share = round(resid_dd / dd, 2) if (resid_dd is not None and dd > 0) else None

    # ---- defect P2-7: STALENESS. DXCM cited 7-month-old customer counts; a screen that
    # reads stale fundamentals as current is reading fiction.
    stale_days = None
    try:
        qf = t.quarterly_financials              # QUARTERLY, not annual — annual is always ~1y stale
        if qf is not None and qf.shape[1]:
            import pandas as pd
            stale_days = int((pd.Timestamp.today(tz=None) - pd.Timestamp(qf.columns[0])).days)
    except Exception:
        pass

    last60 = h.tail(60)
    basing = float(last60.iloc[-1]) > float(last60.min()) * 1.05

    return {
        "ticker": tk, "price": round(px, 2),
        "drawdown_from_3y_high_pct": round(dd * 100, 1),
        "off_3y_low_pct": round((px / lo - 1) * 100, 1),
        "pct_off_52w_low": round(off_low52 * 100, 1),
        "days_since_52w_low": days_since_low,
        "entry_exhausted": exhausted,
        "basing": basing,
        "market_cap_musd": round(cap / 1e6),
        "gross_margin_pct": round(gm * 100, 1),
        "roe_pct": round(_f(info.get("returnOnEquity"), 0) * 100, 1),
        "rev_cagr_3y_pct": round(rev_cagr * 100, 1) if rev_cagr is not None else None,
        "fwd_rev_growth_pct": round(fwd_rev_growth * 100, 1) if fwd_rev_growth is not None else None,
        "guide_vs_trailing_ratio": round(guide_ratio, 2) if guide_ratio is not None else None,
        "guide_decel_flag": guide_flag,
        "earnings_growth_pct": round(earn_growth * 100, 1) if earn_growth is not None else None,
        "earnings_note": earn_note,
        "price_to_sales": round(ps_clean, 2) if ps_clean is not None else None,
        "fx_note": fx_note,
        "residual_drawdown_pct": round(resid_dd * 100, 1) if resid_dd is not None else None,
        "residual_share_of_drawdown": resid_share,
        "factor_beta": round(fbeta, 2) if fbeta is not None else None,
        "factor_proxy": proxy,
        "factor_costume": factor_costume,
        "financials_age_days": stale_days,
        "stale_flag": (stale_days is not None and stale_days > STALE_DAYS),
        "net_debt_ebitda": round(lev, 2) if lev is not None else None,
        "fcf_musd": round(_f(info.get("freeCashflow"), 0) / 1e6),
        "sector": sector, "industry": info.get("industry"),
        "name": (info.get("shortName") or "")[:40],
    }


def score(r):
    """Rank by how closely a name matches the winners' signature, not by cheapness.
    Depth near the winners' −46% median, quality economics, still growing, and
    basing rather than falling."""
    depth = 1 - abs(r["drawdown_from_3y_high_pct"] / 100 - 0.46) / 0.46
    qual = min(r["gross_margin_pct"] / 70, 1.0)
    grow = min(max((r["rev_cagr_3y_pct"] or 0) / 15, 0), 1.0)
    base = 1.0 if r["basing"] else 0.45
    raw = 100 * (0.35 * max(depth, 0) + 0.30 * qual + 0.20 * grow + 0.15 * base)
    # HARD DEMOTES from the 2026-08-03 court back-test — each one is a name the screen
    # surfaced and a court then had to reject for a reason the score could not see.
    if r.get("entry_exhausted"):    raw *= 0.45      # GWRE: +54% off a 42-day low
    if r.get("factor_costume"):     raw *= 0.30      # AEM: the drawdown was the gold price
    if r.get("guide_decel_flag"):   raw *= 0.65      # BSX: trailing +8% vs guided +3-5%
    if r.get("stale_flag"):         raw *= 0.85      # DXCM: 7-month-old metrics
    return round(raw, 1)


COURT_FRAME = (
 "QUALITY-DRAWDOWN LANE — the pond the P&L actually came from (attribution 2026-08-03: 94% of the "
 "book's gains came from software/services/insurance/brands bought at a median -46% against each "
 "name's OWN 3-year high, while every generator we owned hunted cheap-on-assets industrials that "
 "produced NONE of our returns). This row is NOT a dislocation candidate and must not be courted as "
 "one — book value is not consulted anywhere in this screen and a 6x-sales name can qualify.\n\n"
 "THE COURT QUESTION IS FALLEN COMPOUNDER vs MELTING ICE CUBE, and nothing else:\n"
 "  (1) Are the ECONOMICS intact? Gross margin, ROE and revenue growth are the screen's premise — "
 "re-derive them from PRIMARY filings, and say so if the screen's vendor figures do not survive.\n"
 "  (2) Is the de-rate MULTIPLE COMPRESSION on a working business, or the market correctly pricing "
 "deterioration? The winners were good businesses at a discount to their own valuation HISTORY; the "
 "kill is a business whose fundamentals are following the multiple down.\n"
 "  (3) VALUE-LADDER FLOW GATE (binding): if the de-rate is rational AND ongoing, do not bid into "
 "our own predicted flow. Entry needs exhaustion evidence — the downgrade cycle landed, volume decay, "
 "or a dated catalyst — not merely a deep number.\n"
 "  (4) FORWARD TENSE: trailing growth is the wrong tense for a de-rate thesis (the BSX defect). "
 "Grade guided/forward revenue against trailing, and treat a guide-deceleration as disqualifying "
 "unless the court can name why.\n"
 "  (5) FACTOR COSTUME: if the drawdown is the sector's factor (the AEM lesson — the fall WAS the "
 "gold price), this is beta wearing an idiosyncratic costume. Regress it or say the check did not run.\n\n"
 "SIZE IS NOT A DISQUALIFIER HERE and the queue-hygiene large-cap eviction DOES NOT APPLY to this "
 "source: the attribution's winners include SAP, CTSH, KNSL and HUBS. A covered mega-cap at a 46% "
 "discount to its own history is exactly the shape being hunted — the CROWDED conditioning kills the "
 "EDGE classification, not the position (RP_FAIR remains available on verified fairness).\n"
 "PROPOSES ONLY: cause-check -> discovery_state -> court before anything stages."
)


def enqueue_top(store: dict, n: int = 6, dry_run: bool = False) -> dict:
    """Wire the screen INTO the conveyor. Built 2026-08-17 after finding the gap that made this
    generator inert: it had run weekly since 2026-08-03, ranked 99 names, and enqueued ZERO — while
    100% of the live court queue came from drawdown/dislocation sweeps, i.e. the exact pond the
    attribution said produced none of our returns. The screen was right and unwired."""
    import sys as _sys
    from pathlib import Path as _P
    _root = _P(__file__).resolve().parents[2]
    if str(_root) not in _sys.path:
        _sys.path.insert(0, str(_root))
    from desk.court_queue import enqueue_candidates, QUEUE

    rows = [r for r in store["names"].values() if isinstance(r, dict) and r.get("score")]
    # Only CLEAN hits are courted — every flag below is a defect a court already had to reject for.
    clean = [r for r in rows if not (r.get("factor_costume") or r.get("stale_flag")
                                     or r.get("guide_decel_flag") or r.get("entry_exhausted"))]
    clean.sort(key=lambda r: -r["score"])

    # Rank first, THEN drop names we already track — and pick the top N of what remains.
    # Taking a naive top-N instead yields a silent zero: on the 2026-08-17 run, 35 of the 44
    # clean hits were already in the ledger, so "top 6" was entirely absorbed by the enqueue's
    # ledger filter and courted nothing while reporting success. Same silent-zero family as a
    # stale cache reading as all-clear. The already-known names are NOT waste — they are a
    # ranking of our own watchlist by the winners' signature, returned separately.
    import re as _re
    try:
        _led = {_re.split(r"[.\s]", n["ticker"])[0].upper()
                for n in json.loads((_root / "desk/data/research_ledger.json").read_text())["names"]}
    except Exception:
        _led = set()
    try:
        _queued = {r["ticker"].upper() for r in QUEUE.rows()}
    except Exception:
        _queued = set()
    fresh = [r for r in clean if r["ticker"].upper() not in _led and r["ticker"].upper() not in _queued]
    known = [r for r in clean if r["ticker"].upper() in _led]
    top = fresh[:n]
    if dry_run:
        return {"would_enqueue": [r["ticker"] for r in top],
                "fresh_pool": len(fresh), "already_tracked": len(known),
                "watchlist_ranking_top10": [(r["ticker"], r["score"]) for r in known[:10]],
                "clean_pool": len(clean), "total_ranked": len(rows)}
    res = enqueue_candidates(
        [{"ticker": r["ticker"], "name": r.get("name"), "px": r.get("price"),
          "mcap": (r.get("market_cap_musd") or 0) * 1e6,
          "dd3y": r.get("drawdown_from_3y_high_pct"), "score": r.get("score"),
          "gross_margin_pct": r.get("gross_margin_pct"), "roe_pct": r.get("roe_pct"),
          "fwd_rev_growth_pct": r.get("fwd_rev_growth_pct")} for r in top],
        source=f"quality_drawdown/{dt.date.today().isoformat()}")
    # per-name context: the signature that got it here, then the shared court frame
    if res.get("added"):
        qrows = QUEUE.rows()
        by = {r["ticker"]: r for r in top}
        touched = []
        for item in qrows:
            r = by.get(item["ticker"])
            if r is None or item.get("context"):
                continue
            item["context"] = (
                f"SIGNATURE: -{r['drawdown_from_3y_high_pct']:.0f}% vs its OWN 3-year high "
                f"(winners' median -46%), gross margin {r.get('gross_margin_pct') or 0:.0f}%, "
                f"ROE {r.get('roe_pct')}, 3y revenue CAGR {r.get('rev_cagr_3y_pct')}%, forward "
                f"revenue {r.get('fwd_rev_growth_pct')}%, {'BASING' if r.get('basing') else 'still falling'}, "
                f"+{r.get('pct_off_52w_low') or 0:.0f}% off the 52-wk low, score {r['score']}.\n\n"
                + COURT_FRAME)
            touched.append(item)
        if touched:
            QUEUE.upsert(touched, generated_by="quality_drawdown:context")
    res["already_tracked_skipped"] = len(known)
    res["watchlist_ranking"] = [{"ticker": r["ticker"], "score": r["score"],
                                 "dd3y_pct": r["drawdown_from_3y_high_pct"]} for r in known[:20]]
    # The watchlist ranking is a first-class output, not a byproduct: it says which names we
    # ALREADY track best match the signature that produced 94% of realised gains.
    store["watchlist_ranking_asof"] = dt.date.today().isoformat()
    store["watchlist_ranking"] = res["watchlist_ranking"]
    OUT.write_text(json.dumps(store, indent=1))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-dd", type=float, default=MIN_DD)
    ap.add_argument("--max-dd", type=float, default=MAX_DD)
    ap.add_argument("--limit", type=int, default=0, help="cap universe for a fast pass")
    ap.add_argument("--enqueue", type=int, default=0,
                    help="court the top N CLEAN hits (0 = propose only, the pre-2026-08-17 behaviour)")
    ap.add_argument("--enqueue-only", action="store_true",
                    help="skip the scan; enqueue from the stored ranking")
    a = ap.parse_args()
    if a.enqueue_only:
        store = json.loads(OUT.read_text())
        print("[quality_drawdown]", enqueue_top(store, a.enqueue or 6))
        return
    globals()["MIN_DD"], globals()["MAX_DD"] = a.min_dd, a.max_dd

    u = universe()
    if a.limit:
        u = u[: a.limit]
    print(f"[quality_drawdown] universe {len(u)} names, drawdown band "
          f"{a.min_dd:.0%}-{a.max_dd:.0%}")
    hits, errs = [], 0
    for i, tk in enumerate(u, 1):
        try:
            r = assess(tk)
            if r:
                r["score"] = score(r)
                hits.append(r)
                print(f"  HIT {tk:6s} dd -{r['drawdown_from_3y_high_pct']:.0f}% "
                      f"gm {r['gross_margin_pct']:.0f}% score {r['score']}")
        except Exception:
            errs += 1
        if i % 100 == 0:
            print(f"  ...{i}/{len(u)} scanned, {len(hits)} hits, {errs} errors")
        time.sleep(0.12)

    hits.sort(key=lambda r: -r["score"])
    store = json.loads(OUT.read_text()) if OUT.exists() else {"runs": [], "names": {}}
    store["runs"].append({"date": dt.date.today().isoformat(), "universe": len(u),
                          "hits": len(hits), "errors": errs,
                          "band": [a.min_dd, a.max_dd]})
    for r in hits:                       # MERGE by ticker — drawdown history is signal
        prev = store["names"].get(r["ticker"], {})
        r["first_seen"] = prev.get("first_seen", dt.date.today().isoformat())
        r["last_seen"] = dt.date.today().isoformat()
        r["seen_count"] = prev.get("seen_count", 0) + 1
        store["names"][r["ticker"]] = r
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(store, indent=1))

    print(f"\n[quality_drawdown] {len(hits)} candidates ({errs} errors) -> {OUT}")
    if a.enqueue:
        print(f"[quality_drawdown] enqueue ->", enqueue_top(store, a.enqueue))
    print(f"\n{'rank':>4s} {'tkr':7s} {'dd%':>6s} {'offLo':>6s} {'gm%':>5s} {'fwd/tr':>7s} "
          f"{'resid':>6s} {'cap$m':>8s} {'sc':>5s}  flags · name")
    for i, r in enumerate(hits[:25], 1):
        fl = []
        if r.get("entry_exhausted"): fl.append("EXHAUSTED")
        if r.get("factor_costume"):  fl.append(f"FACTOR({r.get('factor_proxy')})")
        if r.get("guide_decel_flag"):fl.append("GUIDE-DECEL")
        if r.get("stale_flag"):      fl.append("STALE")
        if r.get("fx_note"):         fl.append("FX-FIXED")
        if not r["basing"]:          fl.append("falling")
        print(f"{i:>4d} {r['ticker']:7s} {-r['drawdown_from_3y_high_pct']:>5.0f}% "
              f"{r['pct_off_52w_low']:>5.0f}% {r['gross_margin_pct']:>4.0f}% "
              f"{(str(r['guide_vs_trailing_ratio']) if r['guide_vs_trailing_ratio'] is not None else '—'):>7s} "
              f"{(str(r['residual_drawdown_pct'])+'%' if r['residual_drawdown_pct'] is not None else '—'):>6s} "
              f"{r['market_cap_musd']:>8,} {r['score']:>5}  {' '.join(fl)}{' · ' if fl else ''}{r['name']}")


if __name__ == "__main__":
    main()
