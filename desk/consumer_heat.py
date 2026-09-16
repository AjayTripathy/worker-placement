"""consumer_heat — the CONSUMER TRENDING HEATMAP page (desk/ui/static/consumer_heat.html).

Born 2026-08-15 (principal directive: "for consumer products like Suja we need to add a trending
heatmap and reviews"). Rows = tracked consumer brands, columns = the lane's channels:

    trend heat | trend direction | review velocity | rating delta | tape 5d / 21d

Data comes from ONE json the two connectors write and MERGE into —
verticals/buyside_dd/outputs/consumer_heat/CONSUMER_HEAT.json (heat block + reviews block). This
module is the RENDERER (same static-regeneration pattern as desk/thesis_index.py) plus a --refresh
that runs the lane end-to-end for the daily watch.

    python3 -m desk.consumer_heat              # render from the stored JSON (offline, no network)
    python3 -m desk.consumer_heat --refresh    # run both connectors, then render (the daily watch)
    python3 -m desk.consumer_heat --refresh SUJA LWAY

Degradation is SHOWN, not hidden: a cell whose channel did not answer renders as "—" with the
reason in the row's degradation column, never as a zero.
"""
from __future__ import annotations

import html
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEAT_JSON = ROOT / "verticals" / "buyside_dd" / "outputs" / "consumer_heat" / "CONSUMER_HEAT.json"
OUT = ROOT / "desk" / "ui" / "static" / "consumer_heat.html"

# heat-score bands -> tone
HOT, WARM, COOL = 62.0, 45.0, 35.0


def esc(x):
    return html.escape(str(x if x is not None else ""))


def _tone_heat(v):
    if v is None:
        return "na"
    return "hot" if v >= HOT else "warm" if v >= WARM else "cold" if v < COOL else "mid"


def _tone_dir(d):
    return {"RISING": "hot", "FLAT": "mid", "DECAYING": "cold"}.get(d, "na")


def _tone_traj(f):
    return {"IMPROVING": "hot", "STABLE": "mid", "DETERIORATING": "cold"}.get(f, "na")


def _tone_ret(r):
    if r is None:
        return "na"
    return "hot" if r > 0.03 else "cold" if r < -0.03 else "mid"


def tape(tickers: list[str]) -> dict:
    """5d / 21d total return per ticker. Best-effort: a price failure degrades that cell only."""
    out = {}
    try:
        import yfinance as yf
    except Exception:
        return {t: {"note": "yfinance unavailable"} for t in tickers}
    try:
        from desk import prices as dprices
    except Exception:
        dprices = None
    try:
        from verticals.buyside_dd.connectors.consumer_product_heat import TRACKED
    except Exception:
        TRACKED = {}
    for t in tickers:
        # lane hint first (BRBY is BRBY.L — a bare 'BRBY' 404s at Yahoo), then the desk registry
        sym = (TRACKED.get(t) or {}).get("yf") or t
        if sym == t:
            try:
                if dprices:
                    sym = dprices.resolve(t)["yf"]
            except Exception:
                sym = t
        try:
            h = yf.Ticker(sym).history(period="3mo")["Close"].dropna()
            if len(h) < 22:
                out[t] = {"note": f"short history ({len(h)} bars)"}
                continue
            last = float(h.iloc[-1])
            out[t] = {"sym": sym, "px": round(last, 2),
                      "r5": round(last / float(h.iloc[-6]) - 1, 4),
                      "r21": round(last / float(h.iloc[-22]) - 1, 4)}
        except Exception as e:
            out[t] = {"note": f"price fetch failed: {str(e)[:60]}"}
    return out


def _pct(x):
    return "—" if x is None else f"{x*100:+.1f}%"


def build(doc: dict, tp: dict) -> str:
    tickers = doc.get("tickers", {})
    rows = []
    for tk, blk in tickers.items():
        heat = blk.get("heat") or {}
        rev = blk.get("reviews") or {}
        hd = heat.get("heat_detail") or {}
        srch = heat.get("search") or {}
        traj = (rev.get("trajectory") or {})
        rows.append({
            "ticker": tk, "name": heat.get("name") or rev.get("name") or tk,
            "brand": heat.get("brand_term"), "control": heat.get("control"),
            "heat": heat.get("heat_score"), "conf": hd.get("confidence"),
            "dir": srch.get("direction"), "ratio": srch.get("ratio"),
            "yoy": srch.get("yoy_ratio"), "yoydir": srch.get("yoy_direction"),
            "slope": srch.get("slope_pct_per_week"),
            "series": [p.get("v") for p in (srch.get("series") or [])],
            "rpm": rev.get("review_velocity_per_month"),
            "delta": rev.get("rating_delta"), "traj": traj.get("flag"),
            "life": (rev.get("aggregate") or {}).get("lifetime_rating_wavg"),
            "nsku": (rev.get("aggregate") or {}).get("n_with_rating"),
            "degraded": sorted(set((hd.get("degraded") or []) + (rev.get("degraded") or []))),
            "tape": tp.get(tk, {}),
        })
    rows.sort(key=lambda r: (r["heat"] is None, -(r["heat"] or 0)))
    live = [r for r in rows if r["heat"] is not None]
    hot = sum(1 for r in live if r["heat"] >= HOT)
    cold = sum(1 for r in live if r["heat"] < COOL)
    meta = doc.get("meta", {})

    def spark(vals):
        vals = [v for v in vals if v is not None][-26:]
        if len(vals) < 4:
            return ""
        lo, hi = min(vals), max(vals)
        rng = (hi - lo) or 1
        w, h = 96, 22
        step = w / (len(vals) - 1)
        pts = " ".join(f"{i*step:.1f},{h - (v-lo)/rng*(h-2) - 1:.1f}" for i, v in enumerate(vals))
        return (f'<svg class="spk" viewBox="0 0 {w} {h}" preserveAspectRatio="none">'
                f'<polyline points="{pts}"/></svg>')

    P = [f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Consumer Heatmap</title>
<style>
:root{{--bg:#0b0e12;--panel:#14181d;--line:#242a31;--ink:#e8ebee;--dim:#828a94;--faint:#5c646e;
--hot:#35c98f;--mid:#d9a441;--cold:#e0736a;--na:#3a424c}}
*{{box-sizing:border-box}}body{{margin:0}}
.wrap{{max-width:1280px;margin:0 auto;padding:24px 22px 80px;font:14px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:var(--ink);background:var(--bg)}}
h1{{font-size:23px;margin:0 0 3px;letter-spacing:-.02em;font-weight:650}}
.sub{{color:var(--dim);font-size:12.5px;margin:0 0 18px;max-width:900px;line-height:1.55}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-bottom:16px}}
.stats>div{{background:var(--panel);padding:12px 14px}}
.stats .n{{font:660 20px/1 ui-monospace,Menlo,monospace}} .stats .l{{font-size:10.5px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em;margin-top:5px}}
.tblwrap{{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel)}}
table{{border-collapse:collapse;width:100%;min-width:980px;font-size:12.5px}}
th{{text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:.09em;color:var(--dim);font-weight:600;padding:10px 12px;border-bottom:1px solid var(--line);white-space:nowrap}}
td{{padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:middle;white-space:nowrap}}
tr:last-child td{{border-bottom:0}}
.tk{{font:700 12.5px ui-monospace,Menlo,monospace}} .tk a{{color:var(--ink);text-decoration:none;border-bottom:1px dotted var(--faint)}}
.nm{{color:var(--dim);font-size:11px}}
.cell{{display:inline-block;min-width:58px;text-align:center;padding:3px 8px;border-radius:6px;font:600 12px ui-monospace,Menlo,monospace}}
.hot{{color:#8ee5c1;background:rgba(53,201,143,.16)}} .mid{{color:#eccb8a;background:rgba(217,164,65,.15)}}
.cold{{color:#f0a89f;background:rgba(224,115,106,.16)}} .na{{color:var(--faint);background:rgba(90,100,110,.12)}}
.warm{{color:#bfe0a8;background:rgba(120,190,110,.15)}}
.spk{{width:96px;height:22px;vertical-align:middle}} .spk polyline{{fill:none;stroke:#5b8def;stroke-width:1.4}}
.deg{{font-size:10px;color:var(--faint);white-space:normal;max-width:230px;line-height:1.35}}
.ctl{{font-size:9px;color:var(--faint);letter-spacing:.04em}}
.foot{{font-size:11px;color:var(--faint);margin-top:20px;border-top:1px solid var(--line);padding-top:13px;line-height:1.65;max-width:980px}}
.foot b{{color:var(--dim)}}
</style></head><body><div class="wrap">
<h1>Consumer Trending Heatmap</h1>
<p class="sub">Brand-level demand VELOCITY for the consumer book — search trend (Google Trends, recent 28d vs trailing 90d),
retail review velocity and the recent-cohort-vs-lifetime rating delta, against the tape. Direction, not level:
a 4.6-star brand decaying is the signal, a 4.6-star brand accelerating is a different name. Cells that could not be
sourced render "—" with the reason; nothing is imputed to zero.</p>
<div class="stats">
 <div><div class="n">{len(rows)}</div><div class="l">Brands tracked</div></div>
 <div><div class="n" style="color:var(--hot)">{hot}</div><div class="l">Heat &ge; {HOT:.0f}</div></div>
 <div><div class="n" style="color:var(--cold)">{cold}</div><div class="l">Heat &lt; {COOL:.0f} (decaying)</div></div>
 <div><div class="n" style="font-size:12px;padding-top:5px">{esc(doc.get('asof','—'))}</div><div class="l">Last refresh (UTC)</div></div>
</div>
<div class="tblwrap"><table>
<thead><tr><th>Brand</th><th>Heat</th><th>Trend</th><th>52w search</th><th>vs 90d</th><th>vs LY</th>
<th>Reviews/mo</th><th>Rating &Delta;</th><th>Lifetime</th><th>Tape 5d</th><th>Tape 21d</th><th>Degraded</th></tr></thead><tbody>"""]

    def cell(tone, text):
        return '<td><span class="cell %s">%s</span></td>' % (tone, text)

    for r in rows:
        t = r["tape"] or {}
        heat_txt = "—" if r["heat"] is None else "%.0f" % r["heat"]
        conf = "" if r["conf"] is None else '<div class="nm">conf %.2f</div>' % r["conf"]
        dir_txt = esc((r["dir"] or "—").replace("INSUFFICIENT_HISTORY", "SHORT"))
        ratio_txt = "—" if r["ratio"] is None else "%+.0f%%" % ((r["ratio"] - 1) * 100)
        yoy_txt = "—" if r["yoy"] is None else "%+.0f%%" % ((r["yoy"] - 1) * 100)
        rpm_txt = "—" if r["rpm"] is None else "%.1f" % r["rpm"]
        delta_txt = "—" if r["delta"] is None else "%+.2f" % r["delta"]
        life_txt = "—" if r["life"] is None else "%.2f" % r["life"]
        if r["life"] is not None and r.get("nsku"):
            life_txt += " (%d)" % r["nsku"]
        ctl = ('<div class="ctl">CONTROL — %s</div>' % esc(r["control"])) if r.get("control") else ""
        brand = (" · " + esc(r["brand"])) if r.get("brand") else ""
        note = (" · " + t["note"]) if t.get("note") else ""
        P.append(
            '<tr><td><span class="tk"><a href="/ticker/%s" target="_blank">%s</a></span>'
            '<div class="nm">%s%s</div>%s</td>' % (esc(r["ticker"]), esc(r["ticker"]),
                                                   esc(r["name"]), brand, ctl)
            + '<td><span class="cell %s">%s</span>%s</td>' % (_tone_heat(r["heat"]), heat_txt, conf)
            + cell(_tone_dir(r["dir"]), dir_txt)
            + "<td>%s</td>" % spark(r["series"])
            + cell(_tone_dir(r["dir"]), ratio_txt)
            + cell(_tone_dir(r["yoydir"]), yoy_txt)
            + cell("na" if r["rpm"] is None else "mid", rpm_txt)
            + cell(_tone_traj(r["traj"]), delta_txt)
            + cell("na", life_txt)
            + cell(_tone_ret(t.get("r5")), _pct(t.get("r5")))
            + cell(_tone_ret(t.get("r21")), _pct(t.get("r21")))
            + '<td class="deg">%s</td></tr>' % esc(("; ".join(r["degraded"]) or "—") + note))

    P.append(f"""</tbody></table></div>
<div class="foot">
<b>How to read it.</b> <b>Heat</b> = 0-100 union of three channels (search 0.55 / social 0.20 / retail-rank 0.25),
renormalized over the channels that answered — a missing channel lowers confidence, it is never scored as zero.
50 = flat vs the brand's own trailing 90 days; a doubling of search interest ≈ 95, a halving ≈ 5.
<b>Trend</b> is the acceleration flag (RISING ≥ +12%, DECAYING ≤ −12% vs the trailing 90d baseline).
<b>vs LY</b> is the seasonal control — the same 4 weeks one year earlier, same series, same scale. Read it whenever the
whole cohort moves together: run this lane in August and every seasonal brand prints DECAYING off a peak-summer
baseline, so the cross-sectional RANK and the YoY column carry the signal, not the raw own-baseline direction.
<b>Reviews/mo</b> and <b>Rating Δ</b> come from snapshot-diffing retailer review counts: the delta is the EXACT mean of the
reviews added between two snapshots minus the lifetime mean — the leading indicator (a fresh cohort is buried in a slow
lifetime average for months). Both need two snapshots ≥3 days apart; until then the row reads BASELINE_ONLY.
<b>Sources</b>: Google Trends widget JSON · ApeWisdom/Reddit · Amazon Best-Sellers and Walmart via the r.jina.ai text proxy
(FRAGILE — retailer reskins break the parse; failures surface in the Degraded column).
Generated by <code>desk.consumer_heat</code> from <code>{esc(HEAT_JSON.name)}</code>
(heat block {esc((meta.get('heat') or {}).get('asof','—'))} · reviews block {esc((meta.get('reviews') or {}).get('asof','—'))}).
</div></div></body></html>""")
    return "\n".join(P)


def render() -> Path:
    if not HEAT_JSON.exists():
        raise SystemExit(f"[consumer_heat] no data yet at {HEAT_JSON} — run with --refresh first")
    doc = json.loads(HEAT_JSON.read_text())
    tp = tape(sorted(doc.get("tickers", {})))
    OUT.write_text(build(doc, tp))
    print(f"[consumer_heat] rendered {len(doc.get('tickers', {}))} brands -> {OUT}")
    return OUT


def refresh(tickers=None, *, max_products: int = 3) -> None:
    """The daily lane: heat pass, then review pass, then render. Degraded-loud on both."""
    sys.path.insert(0, str(ROOT))
    from verticals.buyside_dd.connectors import consumer_product_heat as cph
    from verticals.buyside_dd.connectors import consumer_product_reviews as cpr
    print(f"=== consumer lane refresh {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} ===")
    print("-- trend heat --")
    cph.run(tickers)
    print("-- review trajectory --")
    cpr.run(tickers, max_products=max_products)
    render()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if "--refresh" in sys.argv:
        refresh(args or None)
    else:
        render()


if __name__ == "__main__":
    main()
