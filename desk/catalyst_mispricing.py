"""catalyst_mispricing — portfolio-wide catalyst-mispricing SCANNER. Generalizes the single-name catalyst-
prediction pass (Aumovio) across every diligenced name that carries a 3-scenario FV set + our probabilities:
for each, compute (a) our probability-weighted FV vs the live price (UPSIDE) and (b) the market-implied
probability of the base/re-rate outcome vs OUR predicted probability (EDGE_pp) — the same invert the Aumovio
watch uses. Rank by the probability edge, gate on an entry band + non-trap, and REPORT ENTRIES.

This is the SCANNER (find + rank candidates); a per-name deep catalyst-prediction pass (e.g. aumovio_peer_watch)
is the CONFIRM that refines the tail/probability. Reads desk/data/edge_classifications/*.json +
catalyst_scenarios.json, prices live (yfinance + KRX override, stored live_px fallback), writes
desk/data/CATALYST_MISPRICING.{json,md}. READ-ONLY; never places orders.

  python3 -m desk.catalyst_mispricing
"""
from __future__ import annotations
import json, re, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EC = ROOT / "desk" / "data" / "edge_classifications"
SCEN = ROOT / "desk" / "data" / "catalyst_scenarios.json"
KRX_OV = ROOT / "desk" / "ui" / "data" / "krx_px_override.json"
OUT_J = ROOT / "desk" / "data" / "CATALYST_MISPRICING.json"
OUT_M = ROOT / "desk" / "data" / "CATALYST_MISPRICING.md"

# fire thresholds (mirror the Aumovio watch discipline: edge scales with price, so the edge gate ~= the band gate)
FIRE_EDGE_PP = 15          # our p(base) exceeds market-implied by >=15pp = a real probability mispricing
STRONG_EDGE_PP = 30        # deep mispricing
TRAP_TYPES = ("TRAP", "REFUTED", "DILIGENCE", "PASS")   # never fire an entry on these

YF = {"028260.KS": "028260.KS", "AMV0.DE": "AMV0.DE", "KB": "KB", "PKO.WA": "PKO.WA", "SHG": "SHG",
      "HSBK.L": "HSBK.L", "PRY.MI": "PRY.MI", "FXPO.L": "FXPO.L"}


def _yf_sym(t):
    """yfinance symbol: explicit map wins, else the ticker itself (US symbols + .L/.PA-style pass through)."""
    return YF.get(t, t)


def _num(x):
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, str):
        m = re.search(r"-?\d[\d,]*\.?\d*", x.replace(",", ""))
        return float(m.group()) if m else None
    return None


def _scenarios(d):
    """(bear, base, bull, p_bear, p_base, p_bull) from a record's varied fields, or None."""
    bear = d.get("fv_bear")
    base = d.get("fv_base") or d.get("fv_base_1_25x") or d.get("prob_weighted_fv")
    bull = d.get("fv_bull")
    if bear is None or base is None or bull is None:
        return None
    p_base = d.get("p_base")
    p_bull = d.get("p_bull") if d.get("p_bull") is not None else d.get("our_p_bull")
    if p_base is None or p_bull is None:
        return None
    p_bear = d.get("p_bear")
    if p_bear is None:
        p_bear = round(1 - p_base - p_bull, 3)
    return (float(bear), float(base), float(bull), float(p_bear), float(p_base), float(p_bull))


def _buy_below(eb):
    """Highest price we'd still buy at (top of the accumulate band), or None if unparseable/prose-only."""
    if eb is None:
        return None
    if isinstance(eb, (int, float)):
        return float(eb)
    if isinstance(eb, list):                       # e.g. FOUR: [43, 49] -> top of band
        vals = [v for v in eb if isinstance(v, (int, float))]
        return float(max(vals)) if vals else None
    if isinstance(eb, dict):
        for k in ("starter_at_market", "accumulate_below", "scale", "reopen_quality_compounder", "starter"):
            if k in eb:
                v = eb[k]
                if isinstance(v, (int, float)):
                    return float(v)
                m = re.search(r"(\d[\d,]*\.?\d*)\s*[-–]\s*(\d[\d,]*\.?\d*)", str(v))
                if m:
                    return float(m.group(2).replace(",", ""))
                n = _num(v)
                if n:
                    return n
        vals = [v for v in eb.values() if isinstance(v, (int, float))]
        return max(vals) if vals else None
    if isinstance(eb, str):
        m = re.search(r"(\d[\d,]*\.?\d*)\s*[-–]\s*(\d[\d,]*\.?\d*)", eb)   # first "A-B" range -> top B
        return float(m.group(2).replace(",", "")) if m else None
    return None


def _catalyst(d):
    cat = (d.get("catalyst") or d.get("flips_to_edge") or
           (d.get("catalyst_predictions", {}) or {}).get("swing_catalysts") or "")
    if isinstance(cat, list):
        # tolerate dict-shaped entries ({"event": ..., "p_of_favorable": ...} — the VMD.json shape)
        cat = ", ".join(x.get("event") or x.get("catalyst") or json.dumps(x) if isinstance(x, dict) else str(x)
                        for x in cat)
    # catalyst DATE: search the catalyst text first, then the record minus its own bookkeeping dates
    # ("date"/"as_of"/px timestamps) — grepping the whole JSON matched the record's analysis date (a bug:
    # every scenario name inherited cat_date=analysis-date and instantly showed RESOLVE-NEEDED).
    pat = r"20(?:2[6-9]|3\d)-\d\d-\d\d"
    today = datetime.date.today().isoformat()
    # prefer the nearest FUTURE date in the catalyst text (a past date there is an effective-date reference,
    # e.g. 028260.KS "KCC effective 2026-03-06", not the upcoming catalyst); then the scrubbed record.
    fut = [x for x in re.findall(pat, str(cat)) if x > today]
    if fut:
        return (str(cat)[:90], min(fut))
    scrub = {k: v for k, v in d.items() if k not in ("date", "as_of", "px_asof")}
    cp = scrub.get("catalyst_predictions")
    if isinstance(cp, dict):
        scrub["catalyst_predictions"] = {k: v for k, v in cp.items() if k not in ("as_of",)}
    fut = [x for x in re.findall(pat, json.dumps(scrub)) if x > today]
    return (str(cat)[:90], min(fut) if fut else None)


def _live_px(records):
    syms = sorted({_yf_sym(r["ticker"]) for r in records})
    live = {}
    try:
        import yfinance as yf
        df = yf.download(syms, period="3d", progress=False, auto_adjust=True)["Close"]
        for s in syms:
            try:
                col = df[s] if hasattr(df, "columns") and s in getattr(df, "columns", []) else df
                v = col.dropna()
                if len(v):
                    live[s] = round(float(v.iloc[-1]), 2)
            except Exception:
                pass
    except Exception:
        pass
    ov = {}
    if KRX_OV.exists():
        try:
            ov = json.loads(KRX_OV.read_text()).get("prices", {})
        except Exception:
            ov = {}
    for r in records:
        t = r["ticker"]
        if t in ov and ov[t].get("px"):
            r["px"], r["px_src"] = ov[t]["px"], "IBKR-KRX"
        elif _yf_sym(t) in live:
            r["px"], r["px_src"] = live[_yf_sym(t)], "yfinance"
        else:
            r["px"], r["px_src"] = r.get("live_px"), "stored (stale)"


def scan():
    recs, scen_extra, prev = [], {}, {}
    if SCEN.exists():
        scen_extra = json.loads(SCEN.read_text())
    if OUT_J.exists():   # prior run's edges -> compute the run-over-run edge DELTA (the "edge changed" alert)
        try:
            prev = {r["ticker"]: r.get("edge_pp") for r in json.loads(OUT_J.read_text()).get("scored", [])}
        except Exception:
            prev = {}
    for f in sorted(EC.glob("*.json")):
        d = json.loads(f.read_text())
        t = d.get("ticker") or f.stem
        sc = _scenarios(d)
        if not sc:
            recs.append({"ticker": t, "computable": False,
                         "thesis_type": d.get("thesis_type") or d.get("final_thesis_type") or d.get("edge_species", ""),
                         "catalyst": _catalyst(d)[0], "cat_date": _catalyst(d)[1], "live_px": d.get("live_px")})
            continue
        bear, base, bull, p_bear, p_base, p_bull = sc
        cat, cdate = _catalyst(d)
        recs.append({"ticker": t, "computable": True, "bear": bear, "base": base, "bull": bull,
                     "p_bear": p_bear, "p_base": p_base, "p_bull": p_bull,
                     "thesis_type": d.get("thesis_type") or d.get("final_thesis_type") or d.get("edge_species", ""),
                     "catalyst": cat, "cat_date": cdate, "live_px": d.get("live_px"),
                     "buy_below": _buy_below(d.get("entry_band"))})
    _live_px(recs)
    today = datetime.date.today()
    for r in recs:
        if not r["computable"] or not r.get("px"):
            continue
        px = r["px"]
        pwfv = r["p_bear"] * r["bear"] + r["p_base"] * r["base"] + r["p_bull"] * r["bull"]
        denom = r["base"] - r["bear"]
        # CLIP to [0,1]: an unclipped solve can go NEGATIVE when px < bear+tail (wide scenario ranges), which
        # inflates edge_pp into the +70s — a model artifact, not a market probability (skeptic-flagged circularity:
        # this whole number is OUR FVs inverted; treat it as a consistency gauge, not the market's confession).
        mkt_p_base = (max(0.0, min(1.0, (px - r["bear"] - r["p_bull"] * (r["bull"] - r["bear"])) / denom))
                      if denom else None)
        r["pwfv"] = round(pwfv, 2)
        r["upside_pct"] = round((pwfv / px - 1) * 100) if px else None
        r["mkt_p_base"] = round(mkt_p_base, 3) if mkt_p_base is not None else None
        r["edge_pp"] = round((r["p_base"] - mkt_p_base) * 100) if mkt_p_base is not None else None
        pe = prev.get(r["ticker"])
        r["prev_edge"] = pe
        r["edge_delta"] = (r["edge_pp"] - pe) if (pe is not None and r["edge_pp"] is not None) else None
        r["days_to_cat"] = None
        if r.get("cat_date"):
            try:
                r["days_to_cat"] = (datetime.date.fromisoformat(r["cat_date"]) - today).days
            except Exception:
                pass
        bb = r.get("buy_below")
        r["in_band"] = (bb is not None and px <= bb * 1.02)          # within 2% of the buy level
        is_trap = any(tp in str(r["thesis_type"]).upper() for tp in TRAP_TYPES)
        # FIRE: a real probability edge, in the buy band, and not a trap/pass name
        if is_trap or r["edge_pp"] is None:
            r["fire"] = "AVOID/PASS" if is_trap else "n/a"
        elif r["edge_pp"] >= STRONG_EDGE_PP and r["in_band"]:
            r["fire"] = "ENTRY-STRONG"
        elif r["edge_pp"] >= FIRE_EDGE_PP and r["in_band"]:
            r["fire"] = "ENTRY"
        elif r["edge_pp"] >= FIRE_EDGE_PP:
            r["fire"] = "WATCH (edge, wait for band)"
        elif r["edge_pp"] <= -FIRE_EDGE_PP:
            r["fire"] = "RICH (fade/avoid)"
        else:
            r["fire"] = "priced"
    comp = [r for r in recs if r.get("edge_pp") is not None]
    comp.sort(key=lambda r: -r["edge_pp"])
    uncomp = [r for r in recs if not r["computable"]]
    return comp, uncomp


def main():
    comp, uncomp = scan()
    today = datetime.date.today().isoformat()
    entries = [r for r in comp if str(r["fire"]).startswith("ENTRY")]

    print(f"=== CATALYST-MISPRICING SCAN  {today}  ({len(comp)} scenario-scored / {len(uncomp)} need quantification) ===")
    print(f"  edge_pp = OUR p(base re-rate) - MARKET-implied p (invert of live px vs the 3 scenarios). +ve = under-priced.")
    print(f"  {'ticker':<10}{'edge':>6}{'ups%':>6}{'px':>10}{'buy≤':>9}{'band':>6}  {'fire':<22} catalyst")
    for r in comp:
        bb = f"{r['buy_below']:.0f}" if r.get("buy_below") else "–"
        band = "IN" if r.get("in_band") else "–"
        px = f"{r['px']:.2f}" if r.get("px") else "?"
        print(f"  {r['ticker']:<10}{('%+d'%r['edge_pp']):>6}{('%+d'%r['upside_pct']):>6}{px:>10}{bb:>9}{band:>6}  {r['fire']:<22} {r['catalyst'][:40]}")

    if entries:
        print(f"\n  >>> FIRE — CATALYST ENTRIES ({len(entries)}): " +
              " | ".join(f"{r['ticker']} edge{r['edge_pp']:+d}pp/ups{r['upside_pct']:+d}% @{r['px']:.2f} (buy≤{r['buy_below']:.0f})" for r in entries))
    else:
        print(f"\n  quiet: no catalyst-entry fires (need edge>=+{FIRE_EDGE_PP}pp AND price in the buy band on a non-trap name)")
    # NOTE: rank on edge_pp AND upside together — a tight scenario spread (e.g. SHG) can show a big edge_pp but
    # small upside%; both must be meaningful for real conviction. Names our own verdict already PASS'd still show
    # their raw edge here (SHG) as a RE-EXAMINE flag, not an auto-buy.

    print(f"\n  need scenario quantification (dated catalyst, no 3-point FV yet): " +
          ", ".join(r["ticker"] for r in uncomp))

    OUT_J.write_text(json.dumps({"asof": today, "fire_edge_pp": FIRE_EDGE_PP, "scored": comp,
                                 "need_quant": [r["ticker"] for r in uncomp], "entries": [r["ticker"] for r in entries]}, indent=1))
    lines = [f"# Catalyst-Mispricing Scan — {today}", "",
             f"`edge_pp` = our p(base re-rate) − market-implied p (from live price vs the 3 scenarios). +ve = under-priced.",
             "", "| Ticker | edge_pp | upside | px | buy≤ | band | fire | catalyst |", "|---|---|---|---|---|---|---|---|"]
    for r in comp:
        bb = f"{r['buy_below']:.0f}" if r.get("buy_below") else "–"
        lines.append(f"| {r['ticker']} | {r['edge_pp']:+d} | {r['upside_pct']:+d}% | {r['px']:.2f} ({r['px_src']}) | {bb} | {'IN' if r.get('in_band') else '–'} | {r['fire']} | {r['catalyst']} |")
    lines += ["", f"**Entries:** {', '.join(r['ticker'] for r in entries) or 'none'}",
              f"**Need scenario quantification:** {', '.join(r['ticker'] for r in uncomp)}"]
    OUT_M.write_text("\n".join(lines) + "\n")
    print(f"\n[-> {OUT_J.name} / {OUT_M.name}]")


if __name__ == "__main__":
    main()
