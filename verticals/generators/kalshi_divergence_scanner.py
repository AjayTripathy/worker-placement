"""kalshi_divergence_scanner — Stage 0b INFO/FLOW: prediction-market vs equity-implied divergence.

Kalshi prices dated, equity-linked events. Two kinds are tradeable divergences against the stock:

  1. PRICE markets (index/stock level): "Will the Nasdaq-100 be above K at EOD?" — the crowd's
     P(S>K) is DIRECTLY comparable to the equity-implied P(S>K) (a lognormal from spot + realized
     vol). edge = kalshi_P − model_P. A gap = the crowd leads/lags the tape (caveat: model uses
     REALIZED vol, so a rich options IV vs HV explains part of any gap — the DD step).

  2. KPI markets (company print): "Will Chipotle report Above $4170M revenue?" laddered across
     strikes — a crowd-sourced probability DISTRIBUTION over the next print. The 50%-crossover strike
     = the crowd-implied MEDIAN for the metric. This is a prediction-market NOWCAST of the print:
     compare it to Street consensus / our own MFT nowcast. And for any OPEN earnings/monthly call we
     already froze, the ladder is the EXACT market_p we've lacked (Brier-vs-market, not RELATED).

v1 seeds the resolvable equity-linked series; EXPAND. Kalshi read API is keyless.
    python3 verticals/generators/kalshi_divergence_scanner.py
Writes data/KALSHI_DIVERGENCE.json. READ-ONLY. (A SIGNAL/nowcast generator — never an order.)
"""
from __future__ import annotations

import datetime
import json
import math
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parents[0]
OUT = HERE / "data" / "KALSHI_DIVERGENCE.json"
CALIB = HERE.parents[1] / "desk" / "data" / "calibration_ledger.jsonl"
B = "https://api.elections.kalshi.com/trade-api/v2"
HDRS = {"User-Agent": "signalos-research 4tripathy@gmail.com"}

# resolvable equity-linked Kalshi series. type: price (lognormal edge) | kpi (print-nowcast) | event (surface)
SERIES = {
    "KXNASDAQ100": {"ticker": "^NDX", "yf": "^NDX", "type": "price", "label": "Nasdaq-100 EOD level"},
    "KXINXE":      {"ticker": "^GSPC", "yf": "^GSPC", "type": "price", "label": "S&P 500 EOD level"},
    "KXCMG":  {"ticker": "CMG", "type": "kpi", "label": "Chipotle print"},
    "KXURBN": {"ticker": "URBN", "type": "kpi", "label": "Urban Outfitters print"},
    "KXLULUA": {"ticker": "LULU", "type": "kpi", "label": "Lululemon print"},
    "KXSCHW": {"ticker": "SCHW", "type": "kpi", "label": "Schwab print"},
    "KXCCL":  {"ticker": "CCL", "type": "kpi", "label": "Carnival print"},
    "KXAMZNA": {"ticker": "AMZN", "type": "kpi", "label": "Amazon print"},
    "KXMOA":  {"ticker": "MO", "type": "kpi", "label": "Altria print"},
    "KXCOINBASE": {"ticker": "COIN", "type": "kpi", "label": "Coinbase print"},
    "KXFDAAPPROVALDATELLY": {"ticker": "LLY", "type": "event", "label": "Eli Lilly FDA approval date"},
}
EDGE_FLOOR = 0.08          # |kalshi − model| >= 8pp on a price market = a divergence worth flagging


def _get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HDRS), timeout=25) as r:
            return json.load(r)
    except Exception:
        return {}


def _markets(series_ticker):
    d = _get(f"{B}/markets?series_ticker={series_ticker}&status=open&limit=200")
    return d.get("markets", []) if isinstance(d, dict) else []


def _hist_vol(yf_ticker):
    """Annualized realized vol from ~60 trading days (the equity-implied-P input)."""
    import yfinance as yf
    try:
        px = yf.download(yf_ticker, period="3mo", progress=False, auto_adjust=True)["Close"].dropna()
        if len(px) < 20:
            return None, None
        rets = (px / px.shift(1)).apply(lambda x: math.log(x) if x and x > 0 else 0).dropna()
        import statistics
        sd = statistics.pstdev(list(rets)[-60:])
        return float(px.iloc[-1]), float(sd * math.sqrt(252))
    except Exception:
        return None, None


def _p_above(spot, strike, vol_ann, days):
    if not (spot and strike and vol_ann and days and days > 0 and spot > 0 and strike > 0):
        return None
    T = days / 365.0
    d2 = (math.log(spot / strike) - 0.5 * vol_ann ** 2 * T) / (vol_ann * math.sqrt(T))
    return 0.5 * (1 + math.erf(d2 / math.sqrt(2)))


def _open_calls():
    calls = {}
    if CALIB.exists():
        for l in CALIB.read_text().splitlines():
            l = l.strip()
            if not l:
                continue
            try:
                r = json.loads(l)
            except Exception:
                continue
            if (r.get("status") or "").upper() == "OPEN":
                calls.setdefault(r.get("ticker"), []).append(r.get("cat_date"))
    return calls


def scan() -> dict:
    today = datetime.date.today()
    open_calls = _open_calls()
    price_div, kpi_now, events, empty = [], [], [], []
    for st, cfg in SERIES.items():
        ms = _markets(st)
        if not ms:
            empty.append(st)
            continue
        tk = cfg["ticker"]
        if cfg["type"] == "price":
            spot, vol = _hist_vol(cfg["yf"])
            for m in ms:
                k = m.get("floor_strike")
                yes = m.get("last_price_dollars")
                close = (m.get("close_time") or "")[:10]
                if k is None or yes in (None, 0, 0.0):    # skip un-priced / non-floor legs
                    continue
                try:
                    days = (datetime.date.fromisoformat(close) - today).days
                except Exception:
                    continue
                mp = _p_above(spot, float(k), vol, days)
                if mp is None:
                    continue
                edge = float(yes) - mp
                if abs(edge) >= EDGE_FLOOR:
                    price_div.append({"series": st, "ticker": tk, "label": cfg["label"],
                                      "strike": float(k), "close": close, "days": days,
                                      "kalshi_p": round(float(yes), 3), "model_p": round(mp, 3),
                                      "edge_pp": round(edge * 100, 1),
                                      "read": "crowd HIGHER than vol-model" if edge > 0 else "crowd LOWER than vol-model"})
        elif cfg["type"] == "kpi":
            # a company series carries SEPARATE metric ladders (revenue / comps / EPS). Group by the
            # metric (the title text after the strike number) so each gets its own crowd-implied median.
            import re
            by_metric = {}
            for m in ms:
                k, yes, title = m.get("floor_strike"), m.get("last_price_dollars"), (m.get("title") or "")
                if k is None or yes is None:
                    continue
                mm = re.search(r"[Aa]bove\s+[-\d.,%]+\s*(.+)$", title)      # metric = phrase after "Above <num>"
                metric = (mm.group(1).strip() if mm else "level")[:32].rstrip(".") or "level"
                by_metric.setdefault(metric, []).append((float(k), float(yes)))
            close = (ms[0].get("close_time") or "")[:10]
            metrics = []
            for metric, ladder in by_metric.items():
                ladder.sort(key=lambda x: x[0])
                if len(ladder) < 2:
                    continue
                median = None
                for i in range(len(ladder) - 1):     # YES falls as strike rises -> find the 0.50 crossing
                    (k1, p1), (k2, p2) = ladder[i], ladder[i + 1]
                    if (p1 - 0.5) * (p2 - 0.5) <= 0 and p1 != p2:
                        median = k1 + (k2 - k1) * (p1 - 0.5) / (p1 - p2)
                        break
                metrics.append({"metric": metric, "n_strikes": len(ladder),
                                "crowd_implied_median": round(median, 2) if median is not None else None})
            metrics.sort(key=lambda x: -x["n_strikes"])
            kpi_now.append({"series": st, "ticker": tk, "label": cfg["label"], "close": close,
                            "metrics": metrics, "feeds_market_p": open_calls.get(tk) if tk in open_calls else None})
        else:
            top = sorted(ms, key=lambda m: -(m.get("last_price_dollars") or 0))[:3]
            events.append({"series": st, "ticker": tk, "label": cfg["label"],
                           "top": [{"title": (m.get("title") or "")[:60], "yes": m.get("last_price_dollars"),
                                    "close": (m.get("close_time") or "")[:10]} for m in top]})
    price_div.sort(key=lambda r: -abs(r["edge_pp"]))
    return {"asof": today.isoformat(), "series_scanned": len(SERIES), "empty": empty,
            "price_divergences": price_div, "kpi_nowcasts": kpi_now, "event_markets": events,
            "note": "PRICE divergences: kalshi P(S>K) vs a REALIZED-vol lognormal model — a gap is a lead/lag OR the "
                    "options vol-risk-premium (IV>HV); DD decomposes. KPI nowcasts: the crowd-implied print distribution "
                    "(50%-crossover = implied median) — compare to consensus/our MFT nowcast; feeds_market_p flags the "
                    "EXACT crowd read for an OPEN call we froze (the Brier-vs-market input we've lacked). Seed series — EXPAND."}


def main():
    res = scan()
    print(f"=== KALSHI DIVERGENCE  {res['asof']}  ({res['series_scanned']} series, "
          f"{len(res['price_divergences'])} price-div, {len(res['kpi_nowcasts'])} KPI-nowcasts) ===")
    if res["price_divergences"]:
        print("  PRICE DIVERGENCES (crowd vs vol-model P(S>K)):")
        for r in res["price_divergences"][:8]:
            print(f"    {r['ticker']:6} >{r['strike']:.0f} by {r['close']} ({r['days']}d): kalshi {r['kalshi_p']:.2f} vs model {r['model_p']:.2f}  edge {r['edge_pp']:+.0f}pp  {r['read']}")
    if res["kpi_nowcasts"]:
        print("  KPI PRINT-NOWCASTS (crowd-implied median per metric, native Kalshi units):")
        for r in res["kpi_nowcasts"]:
            fm = f"  ⚡feeds market_p for {r['feeds_market_p']}" if r["feeds_market_p"] else ""
            print(f"    {r['ticker']:6} print {r['close']}{fm}")
            for mt in r["metrics"][:4]:
                med = f"~{mt['crowd_implied_median']}" if mt["crowd_implied_median"] is not None else "n/a (no 0.5 crossing)"
                print(f"        {mt['metric'][:34]:34} median {med}  ({mt['n_strikes']} strikes)")
    if res["empty"]:
        print(f"  (no open markets: {res['empty']})")
    OUT.write_text(json.dumps(res, indent=1))
    print(f"[-> {OUT.name}]")


if __name__ == "__main__":
    main()
