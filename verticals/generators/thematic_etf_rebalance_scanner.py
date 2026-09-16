"""thematic_etf_rebalance_scanner — Stage 0b FLOW: thematic-ETF (ARK) rebalance forced-flow.

THE CAPACITY EDGE. When a thematic fund (ARK et al.) adds or drops a $1-3B name it forces DAYS of
concentrated, price-INSENSITIVE flow into a float too small for anyone big to arbitrage — the exact
opposite of S&P/Russell recon, where the whole street front-runs a large-cap add. Here the underlying
names are small enough that ONLY WE care: ARK often owns a double-digit % of a small name's public
float, so an ARK trim = a tradeable air-pocket (the drop) and an ARK add = a pop, and neither is
crowded because the ticket is beneath institutional attention. FLOW/MFP class.

DATA (free, keyless): ARK publishes DAILY holdings CSVs. Each row is
    date,fund,company,ticker,cusip,shares,market value ($),weight (%)
We pull TODAY's holdings for ARKK/ARKG/ARKW/ARKF/ARKQ/ARKX.

SIGNAL 1 — rebalance-flow RISK (ownership concentration, always computable):
  For every holding we estimate ARK's position as a share of the name's PUBLIC FLOAT (ark_shares /
  float via yfinance) and as DAYS-OF-ADV (ark_shares / average daily volume). A high float-share or
  high days-of-ADV = a name where any ARK add/trim moves the tape for days (the tradeable event).
  We flag the top names by concentration. float% is an ESTIMATE (yfinance floatShares); days-of-ADV
  is the harder, cleaner number (a trim of N ARK-days of ADV must clear against the market).

SIGNAL 2 — day-over-day DELTA (accumulates over runs):
  ARK's CSV URL is same-day only — there is NO stable historical URL, so a same-run delta is NOT
  possible on a cold start. We therefore PERSIST today's holdings to a state file; every subsequent
  run diffs today's shares vs the stored prior day and emits share/weight deltas (an ADD = pop setup,
  a DROP/trim = air-pocket setup). The cron accumulates the history the URL won't give us. First run
  reports deltas: [] and says so.

    python3 verticals/generators/thematic_etf_rebalance_scanner.py
Writes data/THEMATIC_ETF_REBALANCE.json  +  data/thematic_etf_state.json. READ-ONLY, never orders.
"""
from __future__ import annotations

import csv
import datetime
import io
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "THEMATIC_ETF_REBALANCE.json"
STATE = HERE / "data" / "thematic_etf_state.json"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}

_BASE = "https://assets.ark-funds.com/fund-documents/funds-etf-csv"
# fund -> exact CSV URL (the '&' funds are URL-encoded as %26; verified live).
FUNDS = {
    "ARKK": f"{_BASE}/ARK_INNOVATION_ETF_ARKK_HOLDINGS.csv",
    "ARKG": f"{_BASE}/ARK_GENOMIC_REVOLUTION_ETF_ARKG_HOLDINGS.csv",
    "ARKW": f"{_BASE}/ARK_NEXT_GENERATION_INTERNET_ETF_ARKW_HOLDINGS.csv",
    "ARKF": f"{_BASE}/ARK_FINTECH_INNOVATION_ETF_ARKF_HOLDINGS.csv",
    "ARKQ": f"{_BASE}/ARK_AUTONOMOUS_TECH._%26_ROBOTICS_ETF_ARKQ_HOLDINGS.csv",
    "ARKX": f"{_BASE}/ARK_SPACE_EXPLORATION_%26_INNOVATION_ETF_ARKX_HOLDINGS.csv",
}

# concentration flag thresholds (a name clears if it trips EITHER — both are FLOW-forcing).
ADV_DAYS_FLOOR = 3.0      # ARK holds >=3 days of the name's ADV -> a trim/add takes days to clear
FLOAT_PCT_FLOOR = 5.0     # ARK holds >=5% of estimated public float -> outsized single-holder pressure
TOP_N = 30                # cap the flagged list


def _get(url: str) -> str | None:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return None


def _num(s):
    """'2,192,620' or '$894,062,731.20' or '10.54%' -> float; None on junk."""
    if s is None:
        return None
    s = str(s).replace(",", "").replace("$", "").replace("%", "").strip()
    try:
        return float(s)
    except Exception:
        return None


def _clean_ticker(t: str) -> str:
    """ARK tickers sometimes carry an exchange suffix (e.g. 'RKLB UQ', 'RKLB.US') — strip to root."""
    t = (t or "").strip().upper()
    if not t:
        return ""
    t = t.split(" ")[0]          # 'RKLB UQ' -> 'RKLB'
    t = t.split(".")[0]          # 'RKLB.US' -> 'RKLB'
    return t


def _fetch_fund(fund: str, url: str) -> tuple[list[dict], str | None]:
    """Return (rows, asof_date). Each row: fund, ticker, company, shares, mv, weight. Bad rows dropped."""
    raw = _get(url)
    if not raw:
        return [], None
    rows, asof = [], None
    reader = csv.DictReader(io.StringIO(raw))
    for r in reader:
        # ARK appends a legal-disclaimer paragraph as a final pseudo-row; it has no numeric shares -> drops.
        tk = _clean_ticker(r.get("ticker", ""))
        shares = _num(r.get("shares"))
        if not tk or not shares or shares <= 0:
            continue        # cash / GS treasury sweep / warrants-w/o-ticker / disclaimer line -> prune
        if asof is None:
            d = (r.get("date") or "").strip()
            try:                # ARK prints MM/DD/YYYY
                asof = datetime.datetime.strptime(d, "%m/%d/%Y").date().isoformat()
            except Exception:
                asof = d or None
        rows.append({
            "fund": fund,
            "ticker": tk,
            "company": (r.get("company") or "").strip(),
            "shares": shares,
            "market_value": _num(r.get("market value ($)")),
            "weight": _num(r.get("weight (%)")),
        })
    return rows, asof


def _float_and_adv(tickers: list[str]) -> dict:
    """floatShares + ADV + quoteType/marketCap per ticker via yfinance. Missing -> absent (self-prune).
    yfinance logs 404/500s to stderr for foreign/unit tickers; we silence it (those simply self-prune)."""
    import logging
    import os
    import sys
    import warnings
    warnings.filterwarnings("ignore")
    logging.getLogger("yfinance").disabled = True
    import yfinance as yf
    out = {}
    _devnull = open(os.devnull, "w")
    _real_err = sys.stderr
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            sys.stderr = _devnull          # mute yfinance's per-ticker HTTP-error prints
            try:
                info = tk.info or {}
            except Exception:
                info = {}
            finally:
                sys.stderr = _real_err
            flt = info.get("floatShares") or info.get("sharesOutstanding")
            adv = (info.get("averageDailyVolume3Month") or info.get("averageVolume")
                   or info.get("averageDailyVolume10Day"))
            out[t] = {
                "float": float(flt) if flt else None,
                "adv": float(adv) if adv else None,
                "quote_type": (info.get("quoteType") or "").upper(),
                "market_cap": info.get("marketCap"),
            }
        except Exception:
            sys.stderr = _real_err
            continue
    try:
        _devnull.close()
    except Exception:
        pass
    return out


def _load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except Exception:
            return {}
    return {}


def _compute_deltas(prior: dict, today_holdings: dict, today_asof: str | None) -> list[dict]:
    """Diff today's per-(fund,ticker) shares vs the persisted prior run. ADD/NEW = pop; DROP/EXIT = air-pocket."""
    if not prior or not prior.get("holdings"):
        return []
    prior_date = prior.get("asof")
    if prior_date and today_asof and prior_date == today_asof:
        return []       # same publish date (weekend / stale) -> no new delta
    prev = prior["holdings"]
    deltas = []
    keys = set(prev) | set(today_holdings)
    for k in keys:
        p = prev.get(k, {}).get("shares", 0.0)
        c = today_holdings.get(k, {}).get("shares", 0.0)
        if p == c:
            continue
        meta = today_holdings.get(k) or prev.get(k) or {}
        fund, ticker = k.split("|", 1) if "|" in k else ("?", k)
        if p == 0 and c > 0:
            kind, dir_ = "NEW", "pop"
        elif c == 0 and p > 0:
            kind, dir_ = "EXIT", "air-pocket"
        else:
            kind = "ADD" if c > p else "TRIM"
            dir_ = "pop" if c > p else "air-pocket"
        dpct = ((c - p) / p * 100) if p else None
        deltas.append({
            "fund": fund, "ticker": ticker, "company": meta.get("company", ""),
            "kind": kind, "direction": dir_,
            "prior_shares": round(p), "today_shares": round(c),
            "delta_shares": round(c - p), "delta_pct": round(dpct, 1) if dpct is not None else None,
        })
    # biggest moves first (by |delta shares|)
    deltas.sort(key=lambda d: -abs(d["delta_shares"]))
    return deltas


def scan() -> dict:
    today = datetime.date.today().isoformat()
    all_rows, funds_scanned, funds_failed, asof_seen = [], [], [], []
    for fund, url in FUNDS.items():
        rows, asof = _fetch_fund(fund, url)
        if rows:
            funds_scanned.append(fund)
            if asof:
                asof_seen.append(asof)
            all_rows.extend(rows)
        else:
            funds_failed.append(fund)

    # aggregate ARK's TOTAL shares per ticker across all funds (float/ADV pressure is family-wide).
    by_ticker = {}
    for r in all_rows:
        t = r["ticker"]
        agg = by_ticker.setdefault(t, {"ticker": t, "company": r["company"], "ark_shares": 0.0,
                                       "funds": set(), "weight_max": 0.0, "mv": 0.0})
        agg["ark_shares"] += r["shares"]
        agg["funds"].add(r["fund"])
        agg["weight_max"] = max(agg["weight_max"], r["weight"] or 0.0)
        agg["mv"] += r["market_value"] or 0.0

    fa = _float_and_adv(sorted(by_ticker)) if by_ticker else {}

    high_conc = []
    for t, agg in by_ticker.items():
        d = fa.get(t) or {}
        flt, adv, qt, mcap = d.get("float"), d.get("adv"), d.get("quote_type"), d.get("market_cap")
        # fund-of-fund holdings (ARK holds other ETFs, e.g. PRNT/3D-printing) are NOT the small-cap
        # capacity-edge thesis — a thin US-ADV read on an ETF is noise, not forced single-name flow.
        if qt == "ETF":
            continue
        pct_float = (agg["ark_shares"] / flt * 100) if flt else None
        adv_days = (agg["ark_shares"] / adv) if adv else None
        # days-of-ADV on a US line is only a valid flow proxy for genuinely small names; a thin US ADV on a
        # mega-cap foreign ADR (primary liquidity abroad) overstates it, so the pure-ADV flag needs the name
        # to be small (float% known OR market cap under the ceiling). float% alone always qualifies.
        SMALLCAP_MCAP_CEIL = 15e9
        adv_valid = adv_days is not None and (pct_float is not None or (mcap is not None and mcap <= SMALLCAP_MCAP_CEIL))
        flag = ((adv_valid and adv_days >= ADV_DAYS_FLOOR) or
                (pct_float is not None and pct_float >= FLOAT_PCT_FLOOR))
        if not flag:
            continue
        note = []
        if adv_valid and adv_days >= ADV_DAYS_FLOOR:
            note.append(f"ARK holds ~{adv_days:.1f} days of ADV -> a full exit takes days to clear")
        if pct_float is not None and pct_float >= FLOAT_PCT_FLOOR:
            note.append(f"~{pct_float:.1f}% of est. public float in one holder")
        high_conc.append({
            "ticker": t, "name": agg["company"], "fund": "+".join(sorted(agg["funds"])),
            "ark_shares": round(agg["ark_shares"]),
            "pct_of_adv": round(adv_days, 1) if adv_valid else None,
            "pct_of_float_est": round(pct_float, 1) if pct_float is not None else None,
            "weight": round(agg["weight_max"], 2),
            "ark_market_value": round(agg["mv"]),
            "note": "; ".join(note),
        })
    # rank by the flow-forcing severity: days-of-ADV first (the cleaner number), then float%
    high_conc.sort(key=lambda r: (-(r["pct_of_adv"] or 0), -(r["pct_of_float_est"] or 0)))
    high_conc = high_conc[:TOP_N]

    # ---- delta vs persisted prior run ----
    asof = sorted(asof_seen)[-1] if asof_seen else today   # most recent publish date across funds
    prior = _load_state()
    today_holdings = {f"{r['fund']}|{r['ticker']}": {"shares": r["shares"], "company": r["company"]}
                      for r in all_rows}
    deltas = _compute_deltas(prior, today_holdings, asof)

    # persist today's holdings for the NEXT run's delta
    try:
        STATE.write_text(json.dumps({"asof": asof, "saved_at": today, "holdings": today_holdings}, indent=0))
    except Exception:
        pass

    first_run = not prior or not prior.get("holdings")
    caveats = [
        "float% is an ESTIMATE (yfinance floatShares/sharesOutstanding) — treat as an order-of-magnitude "
        "ownership read, not a filing-grade number; days-of-ADV is the cleaner flow metric.",
        "ARK's CSV URL is same-day only with NO stable history URL, so a same-RUN delta is impossible; "
        "deltas ACCUMULATE across cron runs from the persisted state file. First run has deltas: [].",
        "concentration is the RISK setup (a name where ARK flow moves the tape), NOT a live event — the "
        "tradeable trigger is an actual ARK add/trim, which Signal-2 deltas catch once history builds.",
        "yfinance-unresolved tickers get no float/ADV and simply don't flag (self-prune, never fabricated).",
    ]
    return {
        "asof": asof,
        "funds_scanned": funds_scanned,
        "funds_failed": funds_failed,
        "holdings_count": len(all_rows),
        "unique_tickers": len(by_ticker),
        "high_concentration": high_conc,
        "deltas": deltas,
        "first_run": first_run,
        "note": "FLOW class — thematic-ETF (ARK) rebalance forced-flow, the CAPACITY edge: ARK adds/drops "
                "$1-3B names whose float is too small for anyone big to arbitrage, so an add = a pop and a "
                "trim = an air-pocket that ISN'T crowded (unlike S&P/Russell recon). Signal-1 = ownership "
                "concentration (days-of-ADV + est. float%) flags names where ARK flow forces days of trade. "
                "Signal-2 = day-over-day share deltas, which ACCUMULATE across cron runs (the CSV URL keeps "
                "no history, so the state file is the history). Verify direction/timing on the actual rebalance.",
        "caveats": caveats,
    }


def main():
    res = scan()
    print(f"=== THEMATIC-ETF (ARK) REBALANCE FLOW  {res['asof']}  "
          f"({len(res['funds_scanned'])}/{len(FUNDS)} funds, {res['unique_tickers']} names) ===")
    print(f"  funds: {', '.join(res['funds_scanned'])}"
          + (f"   FAILED: {res['funds_failed']}" if res["funds_failed"] else ""))
    print(f"  HIGH OWNERSHIP-CONCENTRATION (an ARK add/trim forces days of flow — the tradeable air-pocket/pop):")
    for r in res["high_concentration"][:20]:
        adv = f"{r['pct_of_adv']:5.1f}d ADV" if r["pct_of_adv"] is not None else "  ?d ADV"
        flt = f"{r['pct_of_float_est']:4.1f}% float" if r["pct_of_float_est"] is not None else "  ?% float"
        print(f"    {r['ticker']:7} {r['name'][:26]:26} {r['fund']:14} {adv}  {flt}  wt {r['weight']:.2f}%")
    if res["deltas"]:
        print(f"  DAY-OVER-DAY DELTAS (ADD=pop / TRIM=air-pocket):")
        for d in res["deltas"][:12]:
            dp = f"{d['delta_pct']:+.0f}%" if d["delta_pct"] is not None else "  new/exit"
            print(f"    {d['kind']:5} {d['ticker']:7} {d['fund']:6} {d['delta_shares']:+,} sh ({dp})  -> {d['direction']}")
    elif res["first_run"]:
        print("  DELTAS: none — FIRST RUN (no prior state). Next run will diff against today's persisted holdings.")
    else:
        print("  DELTAS: none (no share changes since prior run, or same publish date).")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}  +  {STATE.name}]")


if __name__ == "__main__":
    main()
