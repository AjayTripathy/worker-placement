"""antibook_performance — track whether our non-owned WATCH / anti-book CALLS actually work. For every catalyst
prediction (direction + conviction), snapshot a baseline price and measure the return since, scored vs the CALL
DIRECTION and vs SPY. This is the honesty test on our thesis-picking: do the names we flag bullish go up, the
ones we flag bearish go down, and do the high-conviction calls beat the low-conviction ones?

Baseline = first time we see a name (starts the clock; most predictions were made recently so ~today's price is
the call price). Runs accrue performance forward. Persists to desk/data/antibook_perf.json.

  python3 -m desk.antibook_performance          # snapshot/refresh + score
"""
from __future__ import annotations
import json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / "desk" / "data" / "catalyst_predictions.json"
PERF = ROOT / "desk" / "data" / "antibook_perf.json"
OVERRIDE = ROOT / "desk" / "ui" / "data" / "krx_px_override.json"
YF = {"COSMECCA": "241710.KQ", "SILICON2": "257720.KQ", "COSMAX": "192820.KS", "HUGEL": "145020.KQ"}
LONG = {"BULLISH", "LONG"}
SHORT = {"BEARISH", "SHORT"}
# STANCE overrides — our ACTIONABLE position stance where it differs from the catalyst-prediction direction.
# A bullish forecast we DIDN'T act on (waited for a cheaper entry) is scored on the WAIT, not the forecast:
# a WAIT name that runs AWAY from our band = a MISS (opportunity cost + no position), NOT a hit.
STANCES = {"COSMECCA": {"stance": "WAIT", "band": 62900, "note": "accumulate <62.9k / base FV 67k — NOT a buy above the band"}}


def _prices(tickers) -> dict:
    import yfinance as yf
    out = {}
    # KRX override first (authoritative)
    if OVERRIDE.exists():
        try:
            ov = json.loads(OVERRIDE.read_text()).get("prices", {})
        except Exception:
            ov = {}
    else:
        ov = {}
    ymap = {t: YF.get(t, t) for t in tickers}
    syms = sorted({v for v in ymap.values()})
    try:
        data = yf.download(syms + ["SPY"], period="5d", progress=False, auto_adjust=True)["Close"]
    except Exception:
        data = None
    def last(sym):
        try:
            s = data[sym].dropna()
            return round(float(s.iloc[-1]), 4) if len(s) else None
        except Exception:
            return None
    for t in tickers:
        if t in ov and ov[t].get("px"):
            out[t] = ov[t]["px"]
        else:
            out[t] = last(ymap[t])
    out["SPY"] = last("SPY")
    return out


def run() -> dict:
    preds = json.loads(PRED.read_text()).get("predictions", {})
    perf = json.loads(PERF.read_text()) if PERF.exists() else {"baselines": {}, "history": []}
    base = perf["baselines"]
    tickers = [t for t in preds if not t.startswith("UKRAIN")]      # skip the bond (no equity px)
    px = _prices(tickers)
    today = datetime.date.today().isoformat()
    spy_now = px.get("SPY")
    rows, new = [], 0
    for t in tickers:
        p, cur = preds[t], px.get(t)
        if cur is None:
            continue
        d = (p.get("direction") or "").upper()
        if t not in base:
            base[t] = {"date": today, "px": cur, "direction": d,
                       "p_favorable": p.get("p_favorable"), "spy_base": spy_now, "catalyst_date": p.get("date")}
            new += 1
        b = base[t]
        ret = (cur / b["px"] - 1) if b["px"] else None
        spy_ret = (spy_now / b["spy_base"] - 1) if (b.get("spy_base") and spy_now) else None
        st = STANCES.get(t)
        if st and st["stance"] == "WAIT":
            bias, signed = "wait", None
            # a WAIT is scored on whether it came to our band, NOT on the forecast direction
            outcome = ("VINDICATED (in band)" if (cur is not None and cur <= st["band"])
                       else f"MISSED — ran {round(ret*100)}% away, no position" if (ret and ret > 0.05)
                       else "waiting")
        else:
            bias = "long" if d in LONG else "short" if d in SHORT else "neutral"
            signed = (ret if bias == "long" else -ret if bias == "short" else None) if ret is not None else None
            outcome = None
        rows.append({"ticker": t, "direction": (st["stance"] if st else d), "bias": bias,
                     "p_favorable": b.get("p_favorable"), "base_date": b["date"], "base_px": b["px"], "px": cur,
                     "ret_pct": (round(ret * 100, 1) if ret is not None else None),
                     "signed_ret_pct": (round(signed * 100, 1) if signed is not None else None),
                     "outcome": outcome,
                     "vs_spy_pct": (round((ret - spy_ret) * 100, 1) if (ret is not None and spy_ret is not None) else None)})
    # aggregate over directional (non-neutral) calls that have moved
    dirs = [r for r in rows if r["bias"] in ("long", "short") and r["signed_ret_pct"] is not None]
    hit = [r for r in dirs if r["signed_ret_pct"] > 0]
    hi = [r for r in dirs if (r["p_favorable"] or 0) >= 0.6]
    # ASYMMETRY DIAGNOSTIC — of the names we did NOT go long (WAIT + NEUTRAL passes), how much upside did we
    # LEAVE (regret) vs downside did we DODGE (savings)? regret >> savings = we price/wait too CONSERVATIVELY;
    # savings >> regret = our caution is earning its keep. This diagnoses the bias DIRECTION empirically.
    passed = [r for r in rows if r["bias"] in ("wait", "neutral") and r["ret_pct"] is not None]
    regret = round(sum(r["ret_pct"] for r in passed if r["ret_pct"] > 0), 1)          # missed upside
    savings = round(sum(-r["ret_pct"] for r in passed if r["ret_pct"] < 0), 1)         # avoided downside
    n_up = sum(1 for r in passed if r["ret_pct"] > 0)
    n_dn = sum(1 for r in passed if r["ret_pct"] < 0)
    lean = ("CONSERVATIVE (leaving upside — FVs/bands may be too low)" if regret > savings * 1.2 + 1 else
            "OPTIMISTIC/PROTECTIVE (dodging losses — caution earning its keep)" if savings > regret * 1.2 + 1 else
            "BALANCED")
    agg = {"n_calls": len(rows), "n_directional": len(dirs),
           "hit_rate": (round(len(hit) / len(dirs) * 100) if dirs else None),
           "avg_signed_ret_pct": (round(sum(r["signed_ret_pct"] for r in dirs) / len(dirs), 1) if dirs else None),
           "avg_vs_spy_pct": (round(sum(r["vs_spy_pct"] for r in rows if r["vs_spy_pct"] is not None) /
                                    max(sum(1 for r in rows if r["vs_spy_pct"] is not None), 1), 1)),
           "hi_conv_hit_rate": (round(sum(1 for r in hi if r["signed_ret_pct"] > 0) / len(hi) * 100) if hi else None),
           "asymmetry": {"regret_missed_upside_pct": regret, "savings_avoided_downside_pct": savings,
                         "n_passed_up": n_up, "n_passed_down": n_dn,
                         "ratio": (round(regret / savings, 2) if savings else None), "lean": lean}}
    perf["baselines"] = base
    perf["history"].append({"date": today, "agg": agg})
    perf["asof"] = today
    perf["last_rows"] = sorted(rows, key=lambda r: (r["signed_ret_pct"] is None, -(r["signed_ret_pct"] or -1e9)))
    perf["last_agg"] = agg
    PERF.write_text(json.dumps(perf, indent=1))
    rows.sort(key=lambda r: (r["signed_ret_pct"] is None, -(r["signed_ret_pct"] or -1e9)))
    return {"asof": today, "new_baselines": new, "agg": agg, "rows": rows}


def main():
    r = run()
    a = r["agg"]
    print(f"=== ANTI-BOOK PERFORMANCE  ({r['asof']}, {r['new_baselines']} new baselines) ===")
    print(f"  {a['n_calls']} calls | {a['n_directional']} directional | hit-rate {a['hit_rate']}% "
          f"(hi-conv {a['hi_conv_hit_rate']}%) | avg signed {a['avg_signed_ret_pct']}% | avg vs SPY {a['avg_vs_spy_pct']}%")
    print(f"  {'ticker':<10}{'dir':<9}{'P':>5}{'base':>10}{'px':>10}{'ret':>7}{'signed':>8}{'vsSPY':>7}")
    for r2 in r["rows"]:
        pf = f"{int(r2['p_favorable']*100)}%" if r2["p_favorable"] is not None else "–"
        for k in ("ret_pct", "signed_ret_pct", "vs_spy_pct"):
            r2[k] = ("–" if r2[k] is None else f"{r2[k]:+}")
        print(f"  {r2['ticker']:<10}{r2['direction'][:8]:<9}{pf:>5}{r2['base_px']:>10}{r2['px']:>10}{r2['ret_pct']:>7}{r2['signed_ret_pct']:>8}{r2['vs_spy_pct']:>7}")


if __name__ == "__main__":
    main()
