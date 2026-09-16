"""dossier_page — the canonical, linkable per-ticker analysis page (served at /ticker/{sym}).

The RULE: every ticker anywhere in the app links here — to ALL its deep diligence and analysis.
Works from iframes and static pages (the SPA modal can't). Renders from aggregator.ticker_dossier:
  - THE EDGE / risk we're paid for  (edge_source + plain edge explainer + thesis)
  - US vs THE MARKET                (each frozen call: our_p vs market_p, the gap = our edge)
  - DEEP DILIGENCE                  (the full conviction writeup)
  - CALIBRATION record             (graded calls + Brier)
  - POSITION & TRADES / BRIEFS / RESEARCH DOCS / DETECTOR FEATURES
"""
from __future__ import annotations

import html

ES_DOC = {
    "FLOW": "corporate-action / forced-flow — paid to provide liquidity to a price-insensitive seller",
    "INFO": "nowcast / MFT — paid for beating analyst latency on a thin-coverage name",
    "VALUE": "fundamental mispricing — paid for being right on worth vs price",
    "CARRY": "risk premium / RP_FAIR — paid to hold a real, bounded risk others avoid",
    "CONVEXITY": "tail / regime — paid off asymmetrically in a crisis/inflation/gold-bid regime",
    "EXCLUSION": "diligence-alpha — the value is in NOT owning it (a decline)",
}


def esc(x):
    return html.escape(str(x if x is not None else ""))


def _pct(p):
    return f"{int(round(p*100))}%" if isinstance(p, (int, float)) else "—"


def render(d: dict) -> str:
    sym = d.get("ticker", "?")
    name = d.get("name") or sym
    led = d.get("ledger") or {}
    pos = d.get("position")
    verdict = led.get("verdict") or ("HELD" if pos else "—")
    es = d.get("edge_source") or "—"
    thesis = led.get("thesis") or ""
    conviction = led.get("conviction") or ""
    explainer = d.get("edge_explainer") or ""
    calls = d.get("frozen_calls") or []
    briefs = d.get("briefs") or []
    trades = d.get("trades") or []
    docs = d.get("docs") or []
    feats = d.get("features") or []

    S = []
    if not d.get("found"):
        S.append(f'<div class="empty">No analysis on file yet for <b>{esc(sym)}</b>. '
                 'It has no ledger entry, position, catalyst, brief, or research doc.</div>')
    else:
        # THE EDGE / risk we're paid for
        S.append('<section><h2>The edge — what risk we\'re paid for</h2>')
        S.append(f'<div class="badge es-{esc(es)}">{esc(es)}</div>'
                 f'<div class="esdoc">{esc(ES_DOC.get(es,""))}</div>')
        if explainer:
            S.append(f'<div class="edge">{esc(explainer)}</div>')
        if thesis:
            S.append(f'<p class="thesis">{esc(thesis)}</p>')
        S.append('</section>')

        # US vs THE MARKET
        if calls:
            S.append('<section><h2>Us vs. the market</h2>'
                     '<p class="hint">Our probability vs the market-implied one where recorded — the gap is the edge.</p>')
            for c in calls:
                our, mkt = c.get("p"), c.get("market_p")
                gap = (f'<span class="gap">edge {our-mkt:+.0%}</span>'
                       if isinstance(our, (int, float)) and isinstance(mkt, (int, float)) else "")
                res = c.get("resolution")
                if res:
                    oc = res.get("outcome", "")
                    badge = f'<span class="pill {"win" if oc=="FAVORABLE" else "miss" if oc=="UNFAVORABLE" else ""}">{esc(oc.title())}</span>'
                else:
                    badge = '<span class="pill open">open</span>'
                pl = c.get("plain") or {}
                plain = ""
                if isinstance(pl, dict) and pl.get("what"):
                    plain = (f'<div class="plain"><b>What:</b> {esc(pl.get("what"))} '
                             f'<b>How:</b> {esc(pl.get("how",""))} <b>Read:</b> {esc(pl.get("conclusion",""))}</div>')
                S.append('<div class="call">'
                         f'<div class="callhd"><span class="cd mono">{esc(c.get("cat_date"))}</span> {badge} '
                         f'<span class="ps">ours <b>{_pct(our)}</b> · market <b>{_pct(mkt)}</b> {gap}</span></div>'
                         f'<div class="cat">{esc(c.get("catalyst"))}</div>'
                         f'{plain}'
                         + (f'<div class="reason">{esc(c.get("reasoning"))}</div>' if c.get("reasoning") else "")
                         + '</div>')
            S.append('</section>')

        # CONVEXITY BUCKET ROLE
        bucket = d.get("bucket")
        if bucket:
            S.append('<section><h2>Convexity bucket role</h2>'
                     f'<div class="row">Sleeve <b>{esc(bucket.get("sleeve"))}</b> · weight ~<b>{esc(bucket.get("w"))}%</b> · '
                     f'convexity <b>{esc(bucket.get("conv"))}</b> · carry <b>{esc(bucket.get("carry"))}</b></div>')
            if bucket.get("role"):
                S.append(f'<div class="conv">{esc(bucket.get("role"))}</div>')
            S.append('</section>')

        # DEEP DILIGENCE
        if conviction:
            S.append(f'<section><h2>Deep diligence</h2><div class="conv">{esc(conviction)}</div></section>')

        # POSITION & TRADES
        if pos or trades:
            S.append('<section><h2>Position &amp; trades</h2>')
            if pos:
                S.append(f'<div class="row">Held: <b>{esc(pos.get("position"))}</b> @ '
                         f'{esc(pos.get("average_price"))} · mkt {esc(pos.get("market_price"))} · '
                         f'uPnL {esc(round(pos.get("unrealized_pnl",0),0))}</div>')
            for t in trades:
                won = (t.get("realized_usd", 0) or 0) >= 0
                cs = f' · <a href="{esc(t["case_study"])}" target="_blank">case study →</a>' if t.get("case_study") else ""
                S.append(f'<div class="row {"pos" if won else "neg"}">Closed {esc(t.get("open"))}→{esc(t.get("close"))}: '
                         f'{esc(t.get("entry"))}→{esc(t.get("exit"))} = <b>{"+" if won else ""}${t.get("realized_usd")}</b> '
                         f'({t.get("ret_pct")}%){cs}</div>')
            S.append('</section>')

        # BRIEFS
        if briefs:
            S.append('<section><h2>Briefs</h2>')
            for b in briefs:
                S.append(f'<div class="row"><a href="{esc(b.get("file"))}" target="_blank">'
                         f'[{esc(b.get("tag"))}] {esc(b.get("title"))}</a> <span class="mut">{esc(b.get("date"))}</span></div>')
            S.append('</section>')

        # RESEARCH DOCS
        if docs:
            S.append('<section><h2>Research docs</h2>')
            for doc in docs[:20]:
                S.append(f'<div class="row"><a href="/doc?file={esc(doc.get("file"))}" target="_blank">'
                         f'{esc(doc.get("title") or doc.get("file"))}</a> <span class="mut">{esc(doc.get("kind"))}</span></div>')
            S.append('</section>')

        # DETECTOR FEATURES
        if feats:
            S.append('<section><h2>Detector features</h2><div class="feats">'
                     + " ".join(f'<span class="feat">{esc(f)}</span>' for f in feats) + '</div></section>')

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(sym)} · dossier</title>
<style>
:root{{--bg:#0b0e14;--panel:#131722;--line:#252b3b;--fg:#d7dce5;--mut:#7d869c;--blu:#3d7eff;--grn:#26a17b;--red:#e0524a;--amb:#e0a106}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
.wrap{{max-width:840px;margin:0 auto;padding:26px 22px 80px}}
.hd{{display:flex;align-items:baseline;gap:12px;border-bottom:1px solid var(--line);padding-bottom:14px;margin-bottom:8px}}
.hd h1{{font-size:26px;margin:0;font-family:ui-monospace,Menlo,monospace}} .hd .nm{{color:var(--mut);font-size:15px}}
.hd .vd{{margin-left:auto;font:600 12px ui-monospace,Menlo,monospace;color:var(--amb);border:1px solid var(--line);border-radius:20px;padding:3px 11px}}
section{{margin:26px 0}} h2{{font-size:12px;text-transform:uppercase;letter-spacing:.12em;color:var(--mut);margin:0 0 10px;font-weight:600}}
.badge{{display:inline-block;font:700 12px ui-monospace,Menlo,monospace;padding:3px 11px;border-radius:20px;border:1px solid var(--blu);color:var(--blu)}}
.esdoc{{color:var(--mut);font-size:13px;margin:6px 0 12px}}
.edge{{background:var(--panel);border-left:3px solid var(--blu);border-radius:6px;padding:12px 15px;font-size:14.5px;margin:8px 0}}
.thesis{{font-size:14px;color:#c3c9d4;max-width:70ch}}
.hint{{color:var(--mut);font-size:12.5px;margin:-4px 0 12px}}
.call{{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:12px 15px;margin:9px 0}}
.callhd{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:5px}}
.cd{{color:var(--mut);font-size:12px}} .ps{{margin-left:auto;font-size:12.5px;color:var(--mut)}} .ps b{{color:var(--fg)}}
.gap{{color:var(--grn);font-weight:600;margin-left:6px}}
.cat{{font-size:13.5px;margin:3px 0}} .plain{{font-size:13px;color:#c3c9d4;margin:6px 0}} .plain b{{color:var(--fg)}}
.reason{{font-size:12.5px;color:var(--mut);margin-top:5px;border-top:1px dashed var(--line);padding-top:5px}}
.conv{{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:14px 16px;font-size:13px;line-height:1.6;color:#c3c9d4;white-space:pre-wrap;max-width:74ch}}
.row{{padding:5px 0;border-bottom:1px solid var(--line);font-size:13.5px}} .row:last-child{{border:none}}
.row.pos b{{color:var(--grn)}} .row.neg b{{color:var(--red)}}
.pill{{font-size:10px;padding:1px 8px;border-radius:20px;border:1px solid var(--line);color:var(--mut)}}
.pill.win{{color:var(--grn);border-color:var(--grn)}} .pill.miss{{color:var(--red);border-color:var(--red)}}
a{{color:var(--blu);text-decoration:none}} a:hover{{text-decoration:underline}} .mut{{color:var(--mut);font-size:12px}}
.mono{{font-family:ui-monospace,Menlo,monospace}} .feat{{display:inline-block;font-size:11px;color:var(--mut);border:1px solid var(--line);border-radius:5px;padding:2px 7px;margin:2px}}
.empty{{color:var(--mut);padding:30px 0}} .bk{{margin-bottom:14px}}
</style></head><body>
  <div class="wrap">
    <div class="bk"><a href="javascript:history.back()">← back</a></div>
    <div class="hd"><h1>{esc(sym)}</h1><span class="nm">{esc(name)}</span><span class="vd">{esc(verdict)}</span></div>
    {''.join(S)}
  </div>
</body></html>"""
