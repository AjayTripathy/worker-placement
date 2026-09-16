"""B-style MECHANISM backtest for the insider share-pledge signal.

THE QUESTION
------------
NOT "do pledged-stock names underperform" (that just re-prices an honestly
disclosed risk — weak under the honesty-alpha framing). Instead, the mechanism:
when a pledged-stock name's price crosses DOWN into its bounded margin-call band,
does it suffer EXCESS forward downside vs a matched benchmark — and does Form-4
code-S (insider selling) near the crossing partition the severe (forced-deleverage)
cases from the maintained ones?

  Event      = first close <= call_band_high on/after the pledge is DISCLOSED
               (point-in-time: we can only know the pledge once it is filed).
  Outcome    = excess forward return (name - benchmark) at 20/60/120 trading days.
  Partition  = code-S insider sale within [-30, +90] cal. days of the event.
  Null       = placebo events on random in-window dates for the same names.

POINT-IN-TIME DISCIPLINE
------------------------
The band is computed with `triangulate_with_filings(as_of=disclosure_date)`, so
its inception anchor and the price used never look past disclosure. The pledge
SIZE used is only what was filed by then. Forward prices are the ONLY post-event
data, used solely as the outcome label.

KNOWN LIMITATIONS (state them, don't bury them)
-----------------------------------------------
1. SURVIVORSHIP: the case universe is seeded from TODAY's S&P 600 prevalence run —
   delisted names are missing, so excess-downside magnitudes are UPWARD-biased
   (the worst pledge blowups that delisted are absent). The engine is survivorship-
   agnostic; only the seed list is biased. A clean run needs a point-in-time
   constituent set.
2. SMALL N: ~4% base rate -> a handful of names; treat every magnitude as a pilot,
   gate any alpha claim on the placebo percentile AND N>=20 (per prior backtests).
3. APPROX INCEPTION: prevalence-seeded cases use a single tranche anchored to the
   first-disclosure date (real inception is earlier/higher), so the band is a
   conservative lower bound. CAI is the one fully-specified multi-tranche case.
4. code-S is an OUTCOME/mediator (known only after the event), so the partition is
   EXPLANATORY, not a tradeable rule.
"""
from __future__ import annotations

import json
import random
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Optional

from . import pledge_filings
from . import pledge_margin_call as pmc
from .edgar import cik_for, fetch_filing_text, list_filings
from .pledge_prevalence_sample import _strip, classify

HORIZONS_TD = (20, 60, 120)            # trading-day forward horizons (~1/3/6 mo)
CODE_S_PRE, CODE_S_POST = 30, 90       # calendar-day window around the event
N_PLACEBO = 25                         # random pseudo-events per case
BENCH = "IJR"                          # S&P SmallCap 600 ETF
PREVALENCE = (Path(__file__).parent / "data" / "_smallcap_universe" / "pledge_prevalence.json")
OUT_DIR = (Path(__file__).parent / "data" / "_backtest" / "pledge_mechanism")


@dataclass
class PledgeCase:
    ticker: str
    cik: str
    insider_name: str
    pledge_observations: list[dict]            # [{date, pledged_shares, exact_date}]
    disclosure_date: str                       # first PIT date the pledge is known
    earliest_pledge_date: Optional[str] = None  # legal/economic inception floor
    approx_inception: bool = False
    note: str = ""


# ----------------------------------------------------------------------------- #
# price helpers (calendar-aligned; reuse pmc's nearest-prior lookup)
# ----------------------------------------------------------------------------- #
def _idx_on(series: list[tuple[str, float]], d: str) -> Optional[int]:
    from bisect import bisect_right
    dates = [x[0] for x in series]
    i = bisect_right(dates, d) - 1
    return i if i >= 0 else None


def _fwd(series: list[tuple[str, float]], bench: list[tuple[str, float]],
         d0: str, h: int) -> Optional[dict]:
    """Name return over h trading days from d0, benchmark over the same CALENDAR
    window, and the excess. None if insufficient forward data."""
    i = _idx_on(series, d0)
    if i is None or i + h >= len(series):
        return None
    p0, p1 = series[i][1], series[i + h][1]
    target_date = series[i + h][0]
    if not p0:
        return None
    name_ret = p1 / p0 - 1.0
    b0, b1 = pmc._price_on(bench, d0), pmc._price_on(bench, target_date)
    bench_ret = (b1 / b0 - 1.0) if (b0 and b1) else None
    excess = (name_ret - bench_ret) if bench_ret is not None else None
    return {"horizon_td": h, "target_date": target_date,
            "name_ret": round(name_ret, 4),
            "bench_ret": round(bench_ret, 4) if bench_ret is not None else None,
            "excess_ret": round(excess, 4) if excess is not None else None}


def _first_band_entry(series: list[tuple[str, float]], threshold: float,
                      on_or_after: str) -> Optional[str]:
    """First date close <= threshold at/after `on_or_after` (a downward crossing,
    or already-inside at the disclosure date)."""
    prev_above = True
    for d, px in series:
        if d < on_or_after:
            continue
        if px <= threshold and (prev_above or d == on_or_after):
            return d
        prev_above = px > threshold
    return None


# ----------------------------------------------------------------------------- #
# per-case evaluation
# ----------------------------------------------------------------------------- #
def evaluate_case(case: PledgeCase, bench: list[tuple[str, float]]) -> dict[str, Any]:
    series = pmc.fetch_price_series(case.ticker, years=10)   # to today, for outcomes
    if not series:
        return {"ticker": case.ticker, "skip": "NO_PRICE_SERIES"}

    band = pmc.triangulate_with_filings(
        case.ticker, case.cik, case.pledge_observations,
        insider_name=case.insider_name,
        earliest_pledge_date=case.earliest_pledge_date,
        as_of=case.disclosure_date,          # PIT: band known only at disclosure
    )
    cband = band.get("call_price_band") or [None, None]
    call_low, call_high = cband[0], cband[1]
    call_central = band.get("call_price_central")
    if call_low is None:
        return {"ticker": case.ticker, "skip": f"NO_BAND ({band.get('signal')})"}

    # Event = price crossing into the CENTRAL (best-guess) call price, not the
    # lower band edge. call_low needs the worst-case ~64% drawdown and almost
    # never prints; central is the single most-likely lender's trigger.
    trigger = call_central if call_central is not None else call_low
    ev = _first_band_entry(series, trigger, case.disclosure_date)
    if ev is None:
        return {"ticker": case.ticker, "call_low": round(call_low, 2),
                "call_high": round(call_high, 2) if call_high is not None else None,
                "call_central": call_central,
                "px_at_disclosure": pmc._price_on(series, case.disclosure_date),
                "disclosure_date": case.disclosure_date, "skip": "NO_BAND_ENTRY"}

    fwd = [f for f in (_fwd(series, bench, ev, h) for h in HORIZONS_TD) if f]
    sales = [s for s in pledge_filings.form4_transaction_events(
                 case.cik, case.insider_name, codes=("S",),
                 since=(date.fromisoformat(ev) - timedelta(days=CODE_S_PRE)).isoformat(),
                 until=(date.fromisoformat(ev) + timedelta(days=CODE_S_POST)).isoformat())]
    px_at_disc = pmc._price_on(series, case.disclosure_date)
    already_inside = px_at_disc is not None and px_at_disc <= trigger
    return {
        "ticker": case.ticker, "approx_inception": case.approx_inception,
        "disclosure_date": case.disclosure_date, "call_low": round(call_low, 2),
        "call_high": round(call_high, 2) if call_high is not None else None,
        "call_central": call_central, "trigger_price": round(trigger, 2),
        "wavg_inception_range": band.get("wavg_inception_price_range"),
        "px_at_disclosure": px_at_disc, "already_inside_at_disclosure": already_inside,
        "entry_price": pmc._price_on(series, ev), "band_entry_date": ev,
        "code_s_near": bool(sales), "n_code_s": len(sales),
        "forward": fwd, "note": case.note,
    }


# ----------------------------------------------------------------------------- #
# placebo: random in-window pseudo-events for the same name
# ----------------------------------------------------------------------------- #
def _placebo_excess(series, bench, lo: str, hi: str, h: int, k: int, rng) -> list[float]:
    dates = [d for d, _ in series if lo <= d <= hi]
    out = []
    for _ in range(min(k, len(dates))):
        d0 = rng.choice(dates)
        f = _fwd(series, bench, d0, h)
        if f and f["excess_ret"] is not None:
            out.append(f["excess_ret"])
    return out


def run(cases: list[PledgeCase], seed: int = 42, out: Optional[str] = None) -> dict:
    rng = random.Random(seed)
    bench = pmc.fetch_price_series(BENCH, years=10, assetclass="etf")
    per_case, placebo_pool = [], {h: [] for h in HORIZONS_TD}
    for c in cases:
        r = evaluate_case(c, bench)
        per_case.append(r)
        msg = r.get("skip") or f"entry {r['band_entry_date']} codeS={r['code_s_near']}"
        print(f"[{c.ticker:6}] {msg}", file=sys.stderr)
        if "skip" in r:
            continue
        series = pmc.fetch_price_series(c.ticker, years=10)
        hi = (date.today() - timedelta(days=int(max(HORIZONS_TD) * 1.5))).isoformat()
        for h in HORIZONS_TD:
            placebo_pool[h] += _placebo_excess(series, bench, c.disclosure_date, hi, h, N_PLACEBO, rng)

    events = [r for r in per_case if "skip" not in r]

    def _agg(rows, h):
        xs = [f["excess_ret"] for r in rows for f in r["forward"]
              if f["horizon_td"] == h and f["excess_ret"] is not None]
        return xs

    summary = {"n_cases": len(cases), "n_events": len(events),
               "benchmark": BENCH, "horizons_td": list(HORIZONS_TD),
               "by_horizon": {}, "by_code_s": {}, "caveats": [
                   "SURVIVORSHIP-biased seed (today's S&P600) -> downside UPWARD-biased",
                   "SMALL N -> pilot only; gate alpha on placebo percentile AND N>=20",
                   "approx single-tranche inception for prevalence-seeded cases",
                   "code-S partition is explanatory (post-event mediator), not tradeable"]}

    for h in HORIZONS_TD:
        xs = _agg(events, h)
        pl = placebo_pool[h]
        mean_x = sum(xs) / len(xs) if xs else None
        pctile = (sum(1 for p in pl if p < mean_x) / len(pl)) if (pl and mean_x is not None) else None
        summary["by_horizon"][h] = {
            "n": len(xs),
            "mean_excess_ret": round(mean_x, 4) if mean_x is not None else None,
            "placebo_n": len(pl),
            "placebo_mean": round(sum(pl) / len(pl), 4) if pl else None,
            "event_vs_placebo_percentile": round(pctile, 3) if pctile is not None else None,
        }
        for tag in ("code_s", "no_code_s"):
            want = tag == "code_s"
            xt = [f["excess_ret"] for r in events if r["code_s_near"] == want
                  for f in r["forward"] if f["horizon_td"] == h and f["excess_ret"] is not None]
            summary["by_code_s"].setdefault(tag, {})[h] = {
                "n": len(xt),
                "mean_excess_ret": round(sum(xt) / len(xt), 4) if xt else None}

    result = {"summary": summary, "per_case": per_case}
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(json.dumps(result, indent=2, default=str))
    return result


# ----------------------------------------------------------------------------- #
# case universe
# ----------------------------------------------------------------------------- #
def _earliest_affirmative_proxy(cik: str) -> Optional[dict]:
    """Walk DEF 14A history oldest->newest; return the FIRST proxy that classifies
    AFFIRMATIVE_PLEDGE (point-in-time first disclosure), with its shares + date."""
    try:
        _, rows = list_filings(cik)
    except Exception:
        return None
    proxies = sorted([r for r in rows if r["form"] == "DEF 14A"],
                     key=lambda r: r["filing_date"])
    for r in proxies:
        html = fetch_filing_text(cik, r["accession"], r["primary_document"])
        if not html:
            continue
        c = classify(_strip(html))
        if c["category"] == "AFFIRMATIVE_PLEDGE":
            return {"date": r["filing_date"], "shares": c.get("shares_pledged")}
    return None


_PREV_CACHE = (Path(__file__).parent / "data" / "_smallcap_universe" / "pledge_prevalence_cases.json")


def cases_from_prevalence(limit: Optional[int] = None, use_cache: bool = True) -> list[PledgeCase]:
    """Resolve the affirmative-pledge prevalence names into PledgeCases. Each name
    costs a cik_for + a full DEF 14A history walk against EDGAR, which 429-throttles
    on batch runs and makes reruns non-deterministic; cache the resolved cases to
    disk so a clean seed survives the next throttled run."""
    if use_cache and _PREV_CACHE.exists():
        cached = [PledgeCase(**c) for c in json.loads(_PREV_CACHE.read_text())]
        return cached[: limit or None]
    data = json.loads(PREVALENCE.read_text())
    names = data["summary"].get("affirmative_names", [])[: limit or None]
    # Warm the SEC ticker->CIK map (retry/backoff + on-disk fallback) so a single
    # 429 on www.sec.gov doesn't NO_CIK every name (cik_for's lru_cache does not
    # cache exceptions).
    try:
        from .pledge_universe_pit import _warm_ticker_map
        tmap = _warm_ticker_map()
    except Exception:
        tmap = {}
    cases: list[PledgeCase] = []
    cik_throttled = False
    for rec in names:
        tk = rec["ticker"]
        cik = tmap.get(tk.upper())
        if not cik:
            try:
                cik = cik_for(tk)
            except Exception:
                cik = None
        if not cik:
            print(f"  {tk}: no CIK, skip", file=sys.stderr)
            cik_throttled = True
            continue
        first = _earliest_affirmative_proxy(cik)
        if not first or not first.get("shares"):
            print(f"  {tk}: no datable affirmative pledge w/ share count, skip", file=sys.stderr)
            continue
        cases.append(PledgeCase(
            ticker=tk, cik=cik, insider_name="",   # any insider (proxy is issuer-level)
            pledge_observations=[{"date": first["date"],
                                  "pledged_shares": int(first["shares"]),
                                  "source": "DEF 14A", "exact_date": False}],
            disclosure_date=first["date"], approx_inception=True,
            note="single-tranche, inception anchored to first-disclosure date"))
    if cases and not limit and not cik_throttled:  # only persist a clean, complete resolve
        from dataclasses import asdict
        _PREV_CACHE.write_text(json.dumps([asdict(c) for c in cases], indent=2))
    return cases


# CAI: the one fully-specified multi-tranche case (recent disclosure -> short window).
CAI_CASE = PledgeCase(
    ticker="CAI", cik="2019410", insider_name="Halbert",
    pledge_observations=[
        {"date": "2025-06-20", "pledged_shares": 1_660_000, "source": "424B4", "exact_date": True},
        {"date": "2026-04-23", "pledged_shares": 25_000_000, "source": "DEF 14A", "exact_date": False}],
    disclosure_date="2026-04-23", earliest_pledge_date="2025-12-17",
    note="fully-specified; disclosure too recent for a long forward window")


def cases_from_pit_universe() -> list[PledgeCase]:
    """Survivorship-recovered cases: pledge-positive names REMOVED from the S&P 600
    (built by pledge_universe_pit.build). Empty if that universe hasn't been built."""
    p = Path(__file__).parent / "data" / "_smallcap_universe" / "pledge_pit_universe.json"
    if not p.exists():
        return []
    return [PledgeCase(**c) for c in json.loads(p.read_text()).get("cases", [])]


if __name__ == "__main__":
    cases = cases_from_prevalence()
    recovered = cases_from_pit_universe()
    print(f"survivor cases: {len(cases)}; recovered (removed) cases: "
          f"{[c.ticker for c in recovered]}", file=sys.stderr)
    cases += recovered
    cases.append(CAI_CASE)
    res = run(cases, out=str(OUT_DIR / "pledge_mechanism_backtest.json"))
    print(json.dumps(res["summary"], indent=2, default=str))
