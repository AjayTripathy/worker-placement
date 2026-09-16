"""factor_drift — quantify FF5 factor drift PRE/POST tax-loss-harvesting across the COMBINED household book
(the Parametric direct-indexing SMA + our IBKR positions), reusing the msprime app's factor model.

WHY COMBINED: §1091 wash sales AND factor exposure both aggregate across every account you control, so the
drift that matters is the whole book's tilt, not either sleeve in isolation. The msprime app already simulates
harvest factor-drift for the Parametric SMA (POST /harvest-simulator); this extends it to include the IBKR
positions and reports IBKR-only / Parametric-only / Combined.

Pipeline:
  1. FF5 loadings (mkt_rf, smb, hml, rmw, cma) from the shared msprime factor_loadings table; missing IBKR
     names are computed via the msprime YFinanceProvider and written back (so both apps share the cache).
  2. Positions: Parametric (msprime.db latest reporting_date, signed market values incl. shorts) + IBKR
     (positions_cache.json, avg-cost for loss identification).
  3. Harvest set = unrealized LOSERS (long: mkt<cost). Simulate selling them.
  4. NET factor exposure = Σ (signed_mv_i / gross_mv) · β_i,f  — pre, post, vs the S&P500 benchmark.
     Reports per-factor active exposure (vs benchmark), the L2 active-exposure norm (tracking-error proxy)
     before/after, concentration (HHI), and the harvest tax benefit.

  python3 -m desk.factor_drift                     # combined book
  python3 -m desk.factor_drift --book ibkr         # IBKR only
  python3 -m desk.factor_drift --compute           # force-compute any missing FF5 loadings (network)
"""
from __future__ import annotations
import os, sys, json, math, sqlite3, argparse
from pathlib import Path

MSPRIME_DB = os.environ.get("MSPRIME_DB", "/Users/ajay/msprime/app/data/msprime.db")
MSPRIME_BACKEND = os.environ.get("MSPRIME_BACKEND", "/Users/ajay/msprime/app/backend")
IBKR_POS = Path(__file__).resolve().parent / "ui" / "data" / "positions_cache.json"
FACTORS = ["mkt_rf", "smb", "hml", "rmw", "cma"]
FACTOR_LABEL = {"mkt_rf": "Mkt", "smb": "Size(SMB)", "hml": "Value(HML)", "rmw": "Qual(RMW)", "cma": "Inv(CMA)"}


# ---------- factor loadings (shared msprime table; compute+cache misses) ----------
def _benchmark_exposures(name="sp500_proxy") -> dict:
    if MSPRIME_BACKEND not in sys.path:
        sys.path.insert(0, MSPRIME_BACKEND)
    try:
        from benchmark import get_benchmark
        return get_benchmark(name).get_exposures()
    except Exception:
        # S&P500 long-run FF5 approximation (fallback if the msprime module won't import)
        return {"mkt_rf": 1.0, "smb": -0.15, "hml": -0.05, "rmw": 0.10, "cma": -0.05}


def loadings(tickers: list, compute_missing=True) -> tuple[dict, list]:
    """{ticker: {factor: beta}} from the shared table; compute+cache any missing US names. Returns (map, missing)."""
    tickers = sorted({t for t in tickers if t})
    out, con = {}, sqlite3.connect(MSPRIME_DB)
    try:
        q = ",".join("?" * len(tickers))
        for r in con.execute(f"SELECT ticker,{','.join(FACTORS)} FROM factor_loadings "
                             f"WHERE provider='yfinance' AND ticker IN ({q})", tickers):
            out[r[0]] = {f: (r[i + 1] or 0.0) for i, f in enumerate(FACTORS)}
    finally:
        con.close()
    missing = [t for t in tickers if t not in out]
    if missing and compute_missing:
        computed = _compute_loadings(missing)
        out.update(computed)
        missing = [t for t in missing if t not in computed]
    return out, missing


def _compute_loadings(tickers: list) -> dict:
    """Compute FF5 betas for missing names via the msprime provider and write them back to the shared table."""
    if MSPRIME_BACKEND not in sys.path:
        sys.path.insert(0, MSPRIME_BACKEND)
    try:
        from factor_providers import get_provider
        df = get_provider("yfinance").get_loadings(tickers)
    except Exception as e:
        print(f"  [loadings] could not compute {tickers}: {type(e).__name__}: {str(e)[:80]}", file=sys.stderr)
        return {}
    if df is None or df.empty:
        return {}
    out, con = {}, sqlite3.connect(MSPRIME_DB)
    try:
        for _, row in df.iterrows():
            t = row["ticker"]
            out[t] = {f: float(row.get(f) or 0.0) for f in FACTORS}
            con.execute(
                "INSERT OR REPLACE INTO factor_loadings "
                "(ticker,mkt_rf,smb,hml,rmw,cma,alpha,r_squared,ann_vol,provider,sector,country,computed_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,'yfinance',?,?,?)",
                (t, out[t]["mkt_rf"], out[t]["smb"], out[t]["hml"], out[t]["rmw"], out[t]["cma"],
                 float(row.get("alpha") or 0.0), float(row.get("r_squared") or 0.0),
                 float(row.get("ann_vol") or 0.0), row.get("sector") or "Unknown", row.get("country") or "US",
                 __import__("datetime").datetime.utcnow().isoformat(timespec="seconds")))
        con.commit()
        print(f"  [loadings] computed + cached {len(out)} names: {', '.join(out)}")
    finally:
        con.close()
    return out


# ---------- positions ----------
def ibkr_positions() -> list:
    """[{sym, mv (signed), cost, unrl, side}] — STK only (options excluded from FF5)."""
    if not IBKR_POS.exists():
        return []
    d = json.loads(IBKR_POS.read_text())
    out = []
    for x in d.get("positions", []):
        if x.get("asset_class") != "STK":
            continue
        qty, avg = x.get("qty") or 0, x.get("avg_price") or 0
        mp = x.get("market_price") or avg
        mv = x.get("market_value") if x.get("market_value") is not None else mp * qty
        out.append({"sym": x["symbol"].split()[0].upper(), "mv": mv, "cost": avg * qty,
                    "unrl": (mp - avg) * qty, "side": "L" if qty >= 0 else "S", "src": "IBKR"})
    return out


def parametric_positions() -> tuple[list, str]:
    con = sqlite3.connect(MSPRIME_DB)
    try:
        d = con.execute("SELECT MAX(reporting_date) FROM positions").fetchone()[0]
        pos = con.execute(
            "SELECT symbol, current_quantity, market_value_usd, long_short_code FROM positions "
            "WHERE reporting_date=? AND product_type!='CASH' AND symbol!='' AND symbol IS NOT NULL", (d,)).fetchall()
        # unrealized via taxlots (weighted-avg cost), same logic as the msprime endpoint
        cost = {}
        for sym, cb in con.execute(
            "SELECT t.symbol, (SUM(t.issue_cost)/NULLIF(SUM(t.quantity),0))*p.current_quantity AS cost_basis "
            "FROM taxlots t JOIN positions p ON t.cusip=p.cusip AND p.reporting_date=? AND p.product_type!='CASH' "
            "WHERE t.quantity!=0 GROUP BY t.symbol, t.cusip", (d,)):
            cost[sym] = cb
    finally:
        con.close()
    out = []
    for sym, qty, mv, lsc in pos:
        sym = (sym or "").upper()
        cb = cost.get(sym)
        out.append({"sym": sym, "mv": mv or 0.0, "cost": cb, "side": lsc or "L", "src": "PARA",
                    "unrl": ((mv or 0.0) - cb) if cb is not None else None})
    return out, d


# ---------- factor exposure + simulation ----------
def _exposure(positions: list, ld: dict, exclude: set) -> tuple[dict, float, float]:
    """NET factor exposure = Σ (signed_mv/gross) · β. Returns (exp_by_factor, gross_used, covered_frac)."""
    use = [p for p in positions if p["sym"] not in exclude]
    gross = sum(abs(p["mv"]) for p in use) or 1.0
    covered = sum(abs(p["mv"]) for p in use if p["sym"] in ld)
    exp = {f: 0.0 for f in FACTORS}
    for p in use:
        fl = ld.get(p["sym"])
        if not fl:
            continue
        w = p["mv"] / gross
        for f in FACTORS:
            exp[f] += w * fl[f]
    return exp, gross, covered / gross


def _hhi(positions: list, exclude: set) -> float:
    use = [abs(p["mv"]) for p in positions if p["sym"] not in exclude]
    g = sum(use) or 1.0
    return sum((m / g) ** 2 for m in use)


def simulate(book="combined", tax_rate=0.238, benchmark="sp500_proxy", compute_missing=True) -> dict:
    para, asof = parametric_positions()
    ibkr = ibkr_positions()
    if book == "ibkr":
        pos = ibkr
    elif book == "parametric":
        pos = para
    else:
        pos = ibkr + para
    ld, missing = loadings([p["sym"] for p in pos], compute_missing=compute_missing)
    bm = _benchmark_exposures(benchmark)
    harvest = {p["sym"] for p in pos if p.get("unrl") is not None and p["unrl"] < 0}

    pre, _, cov = _exposure(pos, ld, set())
    post, _, _ = _exposure(pos, ld, harvest)

    def l2_active(exp):  # tracking-error proxy: L2 norm of active (vs benchmark) factor exposure
        return math.sqrt(sum((exp[f] - bm[f]) ** 2 for f in FACTORS))

    drift = {f: {"pre": round(pre[f], 3), "post": round(post[f], 3), "delta": round(post[f] - pre[f], 3),
                 "bm": round(bm[f], 3), "pre_active": round(pre[f] - bm[f], 3),
                 "post_active": round(post[f] - bm[f], 3)} for f in FACTORS}
    tax_benefit = sum(abs(p["unrl"]) for p in pos if p.get("unrl") is not None and p["unrl"] < 0) * tax_rate
    return {"book": book, "asof": asof, "n_positions": len(pos), "n_harvested": len(harvest),
            "harvest_set": sorted(harvest), "coverage": round(cov, 3), "missing_loadings": missing,
            "tax_benefit": round(tax_benefit), "tax_rate": tax_rate,
            "te_proxy_pre": round(l2_active(pre), 4), "te_proxy_post": round(l2_active(post), 4),
            "te_proxy_delta": round(l2_active(post) - l2_active(pre), 4),
            "hhi_pre": round(_hhi(pos, set()), 5), "hhi_post": round(_hhi(pos, harvest), 5),
            "drift": drift}


def _report(r: dict):
    print(f"\n=== FACTOR DRIFT — {r['book'].upper()} book (Parametric asof {r['asof']}) ===")
    print(f"  positions {r['n_positions']} | harvested (unrl losers) {r['n_harvested']}: {', '.join(r['harvest_set']) or '—'}")
    print(f"  factor coverage {r['coverage']:.0%}" + (f"  | NO loadings: {', '.join(r['missing_loadings'])}" if r['missing_loadings'] else ""))
    print(f"  harvest tax benefit @ {r['tax_rate']:.1%}: ${r['tax_benefit']:,}")
    print(f"  {'factor':<12}{'pre':>8}{'post':>8}{'Δ':>8}{'bm':>8}{'pre_act':>9}{'post_act':>10}")
    for f in FACTORS:
        d = r["drift"][f]
        print(f"  {FACTOR_LABEL[f]:<12}{d['pre']:>8.3f}{d['post']:>8.3f}{d['delta']:>+8.3f}{d['bm']:>8.3f}{d['pre_active']:>+9.3f}{d['post_active']:>+10.3f}")
    arrow = "WORSE (drifts AWAY from benchmark)" if r["te_proxy_delta"] > 0 else "BETTER (drifts TOWARD benchmark)"
    print(f"  TE-proxy (L2 active): {r['te_proxy_pre']:.4f} -> {r['te_proxy_post']:.4f}  (Δ {r['te_proxy_delta']:+.4f} = {arrow})")
    print(f"  concentration HHI:    {r['hhi_pre']:.5f} -> {r['hhi_post']:.5f}")


CACHE = Path(__file__).resolve().parent / "ui" / "data" / "factor_drift.json"


def write_cache(tax_rate=0.238) -> dict:
    """Run all three books and cache the result for the dashboard (computing loadings needs network, so the
    tab reads this cache + offers a recompute button rather than recomputing on every load)."""
    import datetime
    books = {b: simulate(b, tax_rate=tax_rate, compute_missing=True) for b in ("ibkr", "parametric", "combined")}
    r = {"generated": datetime.datetime.now().isoformat(timespec="minutes"), "tax_rate": tax_rate, "books": books}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(r, indent=1))
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--book", choices=["combined", "ibkr", "parametric"], default="combined")
    ap.add_argument("--tax-rate", type=float, default=0.238)
    ap.add_argument("--compute", action="store_true", help="force-compute missing FF5 loadings (network)")
    ap.add_argument("--all", action="store_true", help="report all three books")
    ap.add_argument("--cache", action="store_true", help="run all three + write the dashboard cache JSON")
    a = ap.parse_args()
    if a.cache:
        r = write_cache(a.tax_rate)
        print(f"[factor_drift] cached {list(r['books'])} -> {CACHE}")
        return
    books = ["ibkr", "parametric", "combined"] if a.all else [a.book]
    for b in books:
        _report(simulate(b, tax_rate=a.tax_rate, compute_missing=a.compute or b != "parametric"))


if __name__ == "__main__":
    main()
