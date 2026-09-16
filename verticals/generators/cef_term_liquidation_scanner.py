"""cef_term_liquidation_scanner — Stage 0b CARRY generator: TERM / TARGET-TERM CEFs converging to NAV.

THE TERMINATION DATE IS THE EDGE. A TERM (or target-term) closed-end fund has a STATED
termination/liquidation date baked into its prospectus. On that date the fund winds down and returns
its NET ASSET VALUE per share to holders (target-term funds are structured to return ~the original
$ offering NAV; plain term funds return the then-current NAV). So a term CEF's discount-to-NAV is a
DATED, MECHANICAL convergence: buy the discount, and as the termination date approaches the discount
is pulled to ~zero (you collect (nav - price)/nav on top of the fund's distributions). The nearer the
term date and the wider the discount, the higher the annualized convergence carry.

Institutions ignore the small/illiquid odd-lot names in this universe — exactly the office-thesis
capacity edge (fee-replication CARRY, capacity-ceilinged). A small investor + AI screening the whole
term-CEF universe IS the edge.

MECHANISM NOTE (why this is a NEW leg): our prior frontrun_engine CEF work REFUTED the pre-IPO NAV
re-mark leg (price LEADS the sponsor's mark — no frontrun there). THIS is a DIFFERENT mechanism: the
term date is a hard contractual forcing event that pulls price to NAV regardless of who leads the
daily mark. Untested here — this generator surfaces the candidates; the convergence itself is the DD.

v1 screens a SEED universe of KNOWN term / target-term CEFs (ticker + VERIFIED stated termination
date) on the two things computable from live data:
  1. PRICE  — live last close (yfinance)
  2. NAV    — the fund's daily NAV, via the 'X<TICKER>X' NAV pseudo-quote (e.g. XBTTX for BTT);
              fall back to yfinance navPrice. If NAV won't resolve cleanly, discount is left NULL
              and FLAGGED (honest coverage gap) — a NAV is NEVER fabricated.
  → discount_to_nav = (nav - price)/nav ; days_to_term ; annualized_convergence = discount / (days/365).

The universe is a SEED to EXPAND + VERIFY; unresolvable tickers self-drop (reported, never silent).
Term dates are hardcoded from PRIMARY sources (prospectus/fact sheet) with a per-name source note —
NO term date is guessed; a name whose date can't be verified is dropped from the seed, not invented.

    python3 verticals/generators/cef_term_liquidation_scanner.py
Writes data/CEF_TERM.json. READ-ONLY. (A CARRY generator — never an order.)
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "CEF_TERM.json"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}

# ---------------------------------------------------------------------------------------------------
# SEED universe of TERM / TARGET-TERM CEFs. Each row: ticker | name | term_date (YYYY-MM-DD) | source.
# term_date is the STATED termination/liquidation date from a PRIMARY source (prospectus/fact sheet).
# Where only a month is disclosed, the date is set to the disclosed end-of-term month-end (noted).
# A SEED to EXPAND (v2: auto-discover the term-CEF universe via N-2/N-CEN filings). Names that have
# already terminated, or whose date can't be verified, are DROPPED — never guessed. Unresolvable
# tickers self-drop at scan time (reported in `dropped`).
# ---------------------------------------------------------------------------------------------------
SEED = [
    # nearest-dated first. All dates verified from a PRIMARY source (prospectus/N-2/N-CSR/sponsor page).
    # NOTE: for most of these the stated date is a SOFT target — boards can extend or, after an
    # "Eligible Tender Offer", convert to perpetual (esp. all RiverNorth, NMCO, NDMO, BGB, BSL, WDI, ETX).
    # Treat the term as a schedule with embedded optionality, not a hard bond maturity (see caveats).
    ("BSL",  "Blackstone Senior Floating Rate 2027 Term Fund",      "2027-05-31", "src: Blackstone fund page / Businesswire 2026-05-29"),
    ("BGB",  "Blackstone Strategic Credit 2027 Term Fund",          "2027-09-15", "src: Blackstone fund page (dissolves absent extension)"),
    ("ETX",  "Eaton Vance Municipal Income 2028 Term Trust",        "2028-06-30", "src: Eaton Vance fund page + N-CSR (15y term, Board may extend <=12mo)"),
    ("RMI",  "RiverNorth Opportunistic Municipal Income Fund",      "2030-10-25", "src: N-CSR / RiverNorth page (extendable to 2031-10 / 2032-04)"),
    ("BTT",  "BlackRock Municipal 2030 Target Term Trust",          "2030-12-31", "src: prospectus / N-CSR (targets return of $25.00/sh)"),
    ("PDX",  "PIMCO Dynamic Income Strategy Fund",                  "2031-01-29", "src: PIMCO CEF release (ex-NRGX, renamed Nov-2023)"),
    ("RMM",  "RiverNorth Managed Duration Municipal Income Fund",   "2031-07-25", "src: N-CSR (extendable +1yr / +6mo)"),
    ("NMCO", "Nuveen Municipal Credit Opportunities Fund",          "2031-10-01", "src: N-2 (Board may extend 2x1yr)"),
    ("NDMO", "Nuveen Dynamic Municipal Opportunities Fund",         "2032-09-01", "src: N-2 / prospectus (Board may extend 2x1yr)"),
    ("PDO",  "PIMCO Dynamic Income Opportunities Fund",             "2033-01-27", "src: PIMCO CEF press release"),
    ("WDI",  "Western Asset Diversified Income Fund",               "2033-06-24", "src: Franklin/FT N-2 (dissolution date)"),
    ("PAXS", "PIMCO Access Income Fund",                            "2034-01-27", "src: PIMCO CEF press release"),
    ("RFM",  "RiverNorth Flexible Municipal Income Fund",           "2035-03-26", "src: prospectus (extendable to 2036-03 / 2036-09)"),
    ("RFMZ", "RiverNorth Flexible Municipal Income Fund II",        "2036-02-26", "src: N-2 / prospectus"),
    ("BMN",  "BlackRock 2037 Municipal Target Term Trust",          "2037-01-23", "src: BlackRock fund page / N-2"),
    ("RMMZ", "RiverNorth Managed Duration Municipal Income Fund II","2037-02-16", "src: N-2 / prospectus (extendable +1yr / +6mo)"),
]

WIDE_DISCOUNT = 0.03      # >=3% below NAV = a convergence candidate worth flagging
NEAR_TERM_DAYS = 365 * 3  # <=~3y to term = the convergence pull is meaningfully annualized


def _nav_price_via_yf(ticker: str):
    """Live price + NAV for a CEF. price from yfinance; NAV via the 'X<TICKER>X' NAV pseudo-quote
    (the data-vendor convention CEF NAVs publish under), falling back to yfinance navPrice.
    Returns (price, nav, nav_source) — any of price/nav may be None (self-prune / honest NULL)."""
    import yfinance as yf

    def _last(sym):
        try:
            tk = yf.Ticker(sym)
            fi = getattr(tk, "fast_info", {}) or {}
            px = fi.get("last_price") or fi.get("lastPrice")
            if px:
                return float(px), tk
            info = tk.info or {}
            px = info.get("regularMarketPrice") or info.get("previousClose")
            if px:
                return float(px), tk
            hist = tk.history(period="5d")
            if len(hist):
                cl = hist["Close"].dropna()
                if len(cl):
                    return float(cl.iloc[-1]), tk
        except Exception:
            return None, None
        return None, None

    price, tk = _last(ticker)

    # NAV: try yfinance navPrice first (rarely populated for CEFs), then the X<TICKER>X pseudo-quote.
    nav, nav_source = None, None
    try:
        if tk is not None:
            info = tk.info or {}
            npv = info.get("navPrice")
            if npv:
                nav, nav_source = float(npv), "yfinance navPrice"
    except Exception:
        pass
    if nav is None:
        nav_sym = f"X{ticker.upper()}X"
        navpx, _ = _last(nav_sym)
        if navpx:
            nav, nav_source = navpx, f"NAV pseudo-quote {nav_sym}"
    return price, nav, nav_source


def scan() -> dict:
    today = datetime.date.today()
    resolved, dropped, rows = 0, [], []

    for ticker, name, term_date, source in SEED:
        # drop names already past their term date (nothing left to converge)
        try:
            td = datetime.date.fromisoformat(term_date)
        except Exception:
            dropped.append({"ticker": ticker, "why": f"unparseable term_date {term_date!r}"})
            continue
        days_to_term = (td - today).days
        if days_to_term < 0:
            dropped.append({"ticker": ticker, "why": f"already terminated ({term_date})"})
            continue

        price, nav, nav_source = _nav_price_via_yf(ticker)
        if price is None:
            dropped.append({"ticker": ticker, "why": "no live price (yfinance unresolved)"})
            continue
        resolved += 1

        note_bits = []
        discount_pct, annualized = None, None
        if nav is not None and nav > 0:
            disc = (nav - price) / nav
            discount_pct = round(disc * 100, 2)
            yrs = days_to_term / 365.0
            if yrs > 0:
                annualized = round((disc / yrs) * 100, 2)
            note_bits.append(f"NAV from {nav_source}")
        else:
            note_bits.append("NAV UNRESOLVED (no X<ticker>X pseudo-quote / navPrice) — discount NULL, "
                             "FLAG: pull NAV from the sponsor's daily fact sheet")
        note_bits.append(source)

        rows.append({
            "ticker": ticker, "name": name,
            "term_date": term_date, "days_to_term": days_to_term,
            "price": round(price, 2),
            "nav": round(nav, 4) if nav is not None else None,
            "discount_pct": discount_pct,
            "annualized_convergence": annualized,
            "note": " | ".join(note_bits),
        })

    # candidates = a KNOWN wide discount within the near-term window (the annualized convergence trade).
    cands = [r for r in rows
             if r["discount_pct"] is not None
             and r["discount_pct"] >= WIDE_DISCOUNT * 100
             and r["days_to_term"] <= NEAR_TERM_DAYS]
    cands.sort(key=lambda r: -(r["annualized_convergence"] or -99))

    priced = [r for r in rows if r["discount_pct"] is not None]
    nav_gap = [r["ticker"] for r in rows if r["discount_pct"] is None]

    return {
        "asof": today.isoformat(),
        "n_universe": len(SEED),
        "n_resolved": resolved,
        "n_nav_resolved": len(priced),
        "nav_coverage_pct": round(100 * len(priced) / resolved, 1) if resolved else None,
        "candidates": cands,
        "all_priced": sorted(priced, key=lambda r: -(r["discount_pct"] or -99)),
        "nav_coverage_gap": nav_gap,
        "dropped": dropped,
        "distribution": {
            "n_priced": len(priced),
            "n_wide_disc_near_term": len(cands),
            "median_discount_pct": round(sorted(r["discount_pct"] for r in priced)[len(priced) // 2], 2) if priced else None,
        },
        "caveats": [
            "TARGET-TERM vs PLAIN TERM: a TARGET-term fund is STRUCTURED to return ~the original $ NAV "
            "at termination (e.g. $25); a plain TERM fund returns the then-current NAV (which can drift). "
            "This scanner converges price->CURRENT NAV; for target-term names also compare price to the "
            "target return-of-capital amount, which is the harder floor.",
            "NAV COVERAGE IS THE KEY LIMITATION: NAV comes from the 'X<ticker>X' pseudo-quote (a data-vendor "
            "convention) or yfinance navPrice; neither is guaranteed per name. Names with no NAV are in "
            "nav_coverage_gap with discount NULL — never a fabricated NAV. v2 needs a robust NAV feed.",
            "DISTRIBUTIONS ERODE NAV: term/muni CEFs pay out; the NAV you converge to is net of the "
            "distribution stream. Total return = convergence + distributions - any NAV drift. Don't count "
            "the discount as pure alpha on top of a NAV that is itself declining from over-distribution.",
            "TERM CAN BE EXTENDED / CONVERTED: boards can extend the term, convert to perpetual, or run a "
            "tender at <100% of NAV — read the latest N-CSR/proxy. An 'eligible tender offer' (common in the "
            "target-term series) may repurchase only a slice at ~98-100% of NAV, not the whole position.",
            "LEVERAGE UNWIND + ILLIQUIDITY at termination: the fund sells assets into the wind-down; muni "
            "names especially can realize NAV below the last mark in a stressed tape. The convergence is to "
            "the REALIZED liquidation NAV, not necessarily today's struck NAV.",
            "PRIOR CEF FRONTRUN LEG WAS REFUTED: the pre-IPO NAV re-mark frontrun failed (price LEADS the "
            "mark). This is the term-EVENT leg (a hard contractual forcing date), a different mechanism — "
            "untested; the term-convergence itself is the DD, not a proven alpha.",
        ],
        "note": "CARRY class — TERM / TARGET-TERM CEFs converge their discount-to-NAV to ~zero on a DATED "
                "termination event (prospectus liquidation date). Buy the discount, collect the mechanical "
                "pull-to-NAV; nearer the date + wider the discount = higher annualized convergence. "
                "Odd-lot / illiquid names institutions ignore = the office capacity edge. Price live from "
                "yfinance; NAV from the X<ticker>X pseudo-quote (honest NULL where it won't resolve). Term "
                "dates are hardcoded from PRIMARY sources (prospectus/fact sheet) per the source note — a "
                "SEED to EXPAND (v2: auto-discover via N-2/N-CEN filings + a robust NAV feed + an "
                "activist-tender leg). NOT proven alpha: the term-convergence mechanism is untested here "
                "(distinct from the REFUTED pre-IPO frontrun leg) — the convergence is the DD.",
    }


def main():
    res = scan()
    OUT.write_text(json.dumps(res, indent=1))
    d = res["distribution"]
    print(f"=== CEF TERM / TARGET-TERM LIQUIDATION SCANNER  {res['asof']}  "
          f"({res['n_resolved']}/{res['n_universe']} resolved, NAV {res['n_nav_resolved']}/{res['n_resolved']} "
          f"= {res['nav_coverage_pct']}% coverage) ===")
    print(f"  distribution: {d['n_priced']} priced | {d['n_wide_disc_near_term']} WIDE-disc & near-term | "
          f"median disc {d['median_discount_pct']}%")
    if res["candidates"]:
        print("  WIDE-DISCOUNT NEAR-TERM CANDIDATES (buy the discount; verify term/tender terms in the proxy):")
        for r in res["candidates"][:15]:
            yrs = r["days_to_term"] / 365.0
            print(f"    {r['ticker']:6} {r['name'][:34]:34} px ${r['price']:6.2f} nav ${r['nav']:7.4f} "
                  f"{r['discount_pct']:+5.2f}% disc  term {r['term_date']} ({yrs:4.1f}y)  "
                  f"~{r['annualized_convergence']:+5.2f}%/yr")
    else:
        print("  no wide-discount near-term names this run — tightest of the priced set:")
        for r in res["all_priced"][:10]:
            print(f"    {r['ticker']:6} {r['name'][:34]:34} px ${r['price']:6.2f} nav ${r['nav']:7.4f} "
                  f"{r['discount_pct']:+5.2f}% disc  term {r['term_date']}")
    if res["nav_coverage_gap"]:
        print(f"  NAV coverage gap (discount NULL, FLAGGED): {res['nav_coverage_gap']}")
    if res["dropped"]:
        print(f"  dropped (unresolved/terminated, {len(res['dropped'])}): {[x['ticker'] for x in res['dropped']]}")
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
