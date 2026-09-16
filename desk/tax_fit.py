"""tax_fit — this-year deployment fit per name: realized vol -> tax-option value (the 2026 asymmetry:
ST losses harvested by ~Dec-15 at ~50% subsidy, winners deferred). tax_option ~= 0.5 * 0.4*sigma*sqrt(tau).
A dated catalyst inside the window upgrades fit one notch (event-vol + fast resolution = capital doesn't trap).
ALLOCATOR among DD-cleared names only — never an entry justification (the guard from the doctrine).

  python3 -m desk.tax_fit    (weekday cron; caches to desk/data/tax_fit.json)
"""
from __future__ import annotations
import json, math, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "desk" / "data" / "tax_fit.json"
HARVEST_END = datetime.date(2026, 12, 15)


def main():
    import yfinance as yf
    led = json.loads((ROOT / "desk" / "data" / "research_ledger.json").read_text()).get("names", [])
    preds = {}
    p = ROOT / "desk" / "data" / "catalyst_predictions.json"
    if p.exists():
        preds = json.loads(p.read_text()).get("predictions", {})
    tau = max((HARVEST_END - datetime.date.today()).days, 0) / 365.0
    syms = [n.get("yf") or n["ticker"] for n in led]
    df = yf.download(sorted(set(syms)), period="6mo", progress=False, auto_adjust=True)["Close"]
    rows = {}
    for n in led:
        s = n.get("yf") or n["ticker"]
        try:
            r = df[s].dropna().pct_change().dropna()[-63:]
            vol = float(r.std()) * math.sqrt(252)
            if math.isnan(vol) or math.isinf(vol):
                continue
        except Exception:
            continue
        topt = 0.5 * 0.4 * vol * math.sqrt(tau)
        cat = preds.get(n["ticker"], {}).get("date")
        dated = bool(cat and cat <= HARVEST_END.isoformat())
        score = topt + (0.02 if dated else 0)      # dated resolver ~= a notch of fit
        fit = "STRONG" if score >= 0.08 else ("MID" if score >= 0.055 else "WEAK")
        rows[n["ticker"]] = {"vol_90d": round(vol, 3), "tax_option_pct": round(topt * 100, 1),
                             "dated_catalyst": cat if dated else None, "fit": fit}
    OUT.write_text(json.dumps({"asof": datetime.date.today().isoformat(), "tau_yr": round(tau, 2),
                               "names": rows}, indent=1))
    print(f"tax_fit: {len(rows)} names cached (tau {tau:.2f}yr)")
    for t, r in sorted(rows.items(), key=lambda kv: -kv[1]["tax_option_pct"])[:10]:
        print(f"  {t:<9} vol {r['vol_90d']:.0%}  tax-opt {r['tax_option_pct']}%  {r['fit']}{'  cat ' + r['dated_catalyst'] if r['dated_catalyst'] else ''}")


if __name__ == "__main__":
    main()
