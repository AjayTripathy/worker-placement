"""strategy_book — the book, organized by EDGE SOURCE, with dates and the full
executed-vs-tracked record. Renders strategy_book.html.

Born 2026-07-09 (user: "a page with dates and all the data categorized by strategy;
it needs reports for catalysts we picked up and didn't execute like IVN too").

For each edge-source class (FLOW/INFO/VALUE/CARRY/CONVEXITY/EXCLUSION/UNCLASSIFIED):
  - EXECUTED — positions we actually took (held snapshot + closed/realized trades),
    with entry, mark, and P&L.
  - TRACKED (not executed) — every catalyst we handicapped in the calibration ledger
    on a name we DON'T hold: made-date, catalyst date, our call, status/outcome. This
    is the IVN record — theses we formed a view on but didn't put money behind.
  - Calibration scoreboard for the class (open / resolved / Brier), graded WITHIN class.

Sources: research_ledger.json, calibration_ledger.jsonl, edge_source_map.json,
positions_snapshot.json (refreshed on desk IBKR polls).

    python3 -m desk.strategy_book         # writes desk/ui/strategy_book.html
READ-ONLY; renders state, never trades.
"""
from __future__ import annotations

import datetime
import html
import json
from collections import defaultdict
from pathlib import Path

from desk.tearsheet import sleeve_stats, MIN_DIST_N

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "desk" / "data"
OUT = ROOT / "desk" / "ui" / "static" / "strategy_book.html"   # served in-app at /static/strategy_book.html (Strategy tab)

ORDER = ["FLOW", "INFO", "VALUE", "CARRY", "CONVEXITY", "EXCLUSION", "UNCLASSIFIED"]
DOCTRINE = {
    "FLOW": "corporate-action / forced-flow — a price-insensitive agent must trade; event-dated, pre-registered exit",
    "INFO": "nowcast / MFT — beat analyst latency on thin-coverage names; this cohort is the MFT forward test",
    "VALUE": "fundamental mispricing — worth ≠ price; months-quarters; exit at fair value or thesis-break",
    "CARRY": "risk premium / RP_FAIR — paid to hold a bounded risk others avoid; open-ended",
    "CONVEXITY": "tail / regime — asymmetric payoff to a crisis, inflation, or gold-bid regime shift",
    "EXCLUSION": "honesty / diligence-alpha — the value is in what we DON'T own (the anti-portfolio)",
    "UNCLASSIFIED": "no structural edge-class yet — mostly covered-name catalyst handicaps; flagged for review",
}
ACCENT = {"FLOW": "#3fb6a8", "INFO": "#c9922e", "VALUE": "#5b8def", "CARRY": "#8a7fd6",
          "CONVEXITY": "#c56b6b", "EXCLUSION": "#6b7280", "UNCLASSIFIED": "#4b5563"}

# A calibration CALL is graded by the SKILL it tests (its event_type), NOT the class of the
# position it informed — "grade WITHIN class, never pooled": a monthly-comp nowcast is an INFO/MFT
# skill even when it times a VALUE hold (e.g. BKE). Unmapped event_types (scenario / regulatory /
# political — genuinely tied to the name's thesis) fall back to the position's edge-class.
EVENT_CLASS = {
    "monthly_data": "INFO",       # nowcast — the MFT forward-test cohort
    "earnings_print": "INFO",     # nowcast on a print
    "peer_read": "INFO",          # nowcast read off a peer's print
    "production_ops": "INFO",     # operational nowcast
    "deal_corporate": "FLOW",     # corporate-action / forced-flow event
    "nat_cat_season": "CONVEXITY",  # catastrophe / regime tail
}


def call_class(r, ticker, verdict, m):
    """Skill-class of a calibration CALL: its event_type if mapped, else the position's class."""
    et = r.get("event_type")
    return EVENT_CLASS.get(et) or classify(ticker, verdict, m)
FAIL_PCT = -15.0   # a held position underwater beyond this is flagged a FAILURE (drawdown), not noise


def _load(p, d=None):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return d if d is not None else {}


def _jsonl(p):
    out = []
    if Path(p).exists():
        for line in Path(p).read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def _map():
    return _load(D / "edge_source_map.json").get("map", {})


def classify(ticker, verdict, m):
    if ticker in m:
        return m[ticker]
    base = str(ticker).split(".")[0]
    if base in m:
        return m[base]
    if (verdict or "").upper() == "AVOID":
        return "EXCLUSION"
    return "UNCLASSIFIED"


def esc(s):
    return html.escape(str(s if s is not None else ""))


def tklink(sym):
    """The RULE: every ticker links to its canonical dossier (/ticker/{sym}) — all its DD + analysis."""
    return f'<a class="tklink" href="/ticker/{esc(sym)}" target="_blank">{esc(sym)}</a>'


def _cleandir(s):
    """Turn a gate string ('FAVORABLE=july_comp_positive') into plain words ('july comp positive')."""
    if not s:
        return ""
    s = s.split("(")[0]
    for pre in ("FAVORABLE =", "FAVORABLE=", "FAVORABLE"):
        if s.strip().startswith(pre):
            s = s.strip()[len(pre):]
            break
    return s.replace("_", " ").strip(" =")


def build():
    m = _map()
    led = {n["ticker"]: n for n in _load(D / "research_ledger.json").get("names", [])}
    snap = _load(D / "positions_snapshot.json")
    held = snap.get("positions", {})
    closed_trades = _load(D / "closed_trades.json").get("trades", [])
    closed_by_class = defaultdict(list)
    for tr in closed_trades:
        closed_by_class[tr.get("class")].append(tr)
    notes = snap.get("notes", {})
    calls = _jsonl(D / "calibration_ledger.jsonl")
    today = datetime.date.today().isoformat()

    # no-go's we DECLINED: AVOID-verdict names in the ledger, with the reason we passed
    declines = {}
    for tk, n in led.items():
        if (n.get("verdict") or "").upper() == "AVOID":
            reason = (n.get("thesis") or n.get("conviction") or "").strip()
            declines[tk] = reason.split(". ")[0][:150]

    # upcoming / staged pipeline: NOT_YET names, with their clock from the event windows
    ev = {w.get("symbol"): w for w in _load(D / "event_windows.json").get("windows", [])}
    upcoming = [t for t, n in led.items() if (n.get("verdict") or "").upper() == "NOT_YET"]

    # classify positions + calls
    held_class = {t: classify(t, (led.get(t) or {}).get("verdict"), m) for t in held}
    # calibration: keep latest per (ticker, cat_date); group by class then ticker
    seen = {}
    for r in calls:
        if r.get("ticker") in ("BOOK-SHARPE", "HONESTY-BACKTEST"):
            continue
        seen[(r.get("ticker"), r.get("cat_date"))] = r
    calls_by_class = defaultdict(lambda: defaultdict(list))
    brier = defaultdict(list)
    graded_calls = defaultdict(list)
    open_ct = defaultdict(int)
    for (tk, _), r in seen.items():
        cls = call_class(r, tk, (led.get(tk) or {}).get("verdict"), m)   # by SKILL/event_type, not position class
        calls_by_class[cls][tk].append(r)
        res = r.get("resolution")
        if res and isinstance(res.get("y"), (int, float)) and isinstance(r.get("our_p"), (int, float)):
            b = (r["our_p"] - res["y"]) ** 2
            brier[cls].append(b)
            pl = r.get("plain") if isinstance(r.get("plain"), dict) else {}
            graded_calls[cls].append({"tk": tk, "cat_date": r.get("cat_date"), "our_p": r["our_p"],
                                      "outcome": res.get("outcome"), "brier": b, "when": res.get("date"),
                                      "predicted": pl.get("what") or _cleandir(r.get("direction")),
                                      "how": pl.get("how") or "", "reasoning": r.get("reasoning") or "",
                                      "made": r.get("made"), "px_at_pred": r.get("px_at_pred"),
                                      "detectors": r.get("detectors") or [],
                                      "result": res.get("note") or ""})
        else:
            open_ct[cls] += 1

    def unreal(t):
        sh, avg, mk = held[t][0], held[t][1], held[t][2]
        return (mk / avg - 1) * 100 if avg else 0.0

    # ---- render ----
    P = []
    P.append(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Strategy Book</title>
<style>
:root{{--bg:#0e1113;--panel:#161a1d;--line:#262b30;--ink:#e6e9ec;--dim:#8a9199;--good:#3fb6a8;--bad:#d4736b}}
*{{box-sizing:border-box}} body{{margin:0}}
.wrap{{max-width:1100px;margin:0 auto;padding:34px 22px 80px;font:14px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:var(--ink);background:var(--bg)}}
h1{{font-size:25px;letter-spacing:-.01em;margin:0 0 4px}} .sub{{color:var(--dim);font-size:13px;margin:0 0 26px}}
.cls{{margin:30px 0 0;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--panel)}}
.clshead{{display:flex;align-items:baseline;gap:12px;padding:14px 18px;border-left:4px solid var(--acc)}}
.clshead h2{{font-size:17px;margin:0;letter-spacing:.02em}} .clshead .doc{{color:var(--dim);font-size:12.5px;flex:1}}
.chip{{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:var(--dim);white-space:nowrap}}
.sec{{padding:2px 18px 16px}} .sec h3{{font-size:11px;text-transform:uppercase;letter-spacing:.12em;color:var(--dim);margin:16px 0 7px;font-weight:600}}
table{{width:100%;border-collapse:collapse;font-size:12.5px}}
th{{text-align:left;color:var(--dim);font-weight:500;font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;padding:5px 9px;border-bottom:1px solid var(--line)}}
td{{padding:6px 9px;border-bottom:1px solid var(--line);vertical-align:top}} tr:last-child td{{border-bottom:none}}
.mono{{font-family:ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums}}
.tk{{font-weight:600}} .pos{{color:var(--good)}} .neg{{color:var(--bad)}}
.pill{{font-size:10px;padding:1px 7px;border-radius:20px;border:1px solid var(--line);color:var(--dim);white-space:nowrap}}
.win{{color:var(--good);border-color:var(--good)}} .miss{{color:var(--bad);border-color:var(--bad)}} .open{{color:var(--dim)}}
.fail{{color:var(--bad);border-color:var(--bad);background:rgba(212,115,107,.08)}}
.noterow td.note{{color:var(--bad);font-size:11.5px;padding-top:0;padding-bottom:9px;border-bottom:1px solid var(--line)}}
.lfail b{{color:var(--bad)}}
.up{{color:#d0a13a}} .lup b{{color:#d0a13a}}
.ts{{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:12px;color:var(--dim);padding:2px 0 2px}}
.ts b{{color:var(--ink);font-variant-numeric:tabular-nums}} .ts .pos{{color:var(--good)}} .ts .neg{{color:var(--bad)}}
.tsdist{{font-size:11.5px;color:var(--dim);margin-top:6px;padding-top:6px;border-top:1px dashed var(--line)}}
.tsdist b{{color:var(--ink)}} .supp{{color:#b08948;font-style:italic}}
.thinflag{{font-size:10.5px;color:var(--bad);font-weight:400;text-transform:none;letter-spacing:0}}
.tklink{{color:inherit;text-decoration:none;border-bottom:1px dotted #3a4048}} .tklink:hover{{border-bottom-color:var(--ink);color:#fff}}
.calsum{{font-size:12.5px;color:var(--dim);padding:2px 0 6px}} .calsum b{{color:var(--ink);font-variant-numeric:tabular-nums}}
.calsum .bgood{{color:var(--good)}} .calsum .bbad{{color:var(--bad)}} .calnote{{font-size:11px}}
.gcall{{background:#12161a;border:1px solid var(--line);border-radius:8px;margin:8px 0;overflow:hidden}}
.gchd{{display:flex;align-items:center;gap:9px;padding:9px 13px;cursor:pointer;list-style:none;user-select:none}}
.gchd::-webkit-details-marker{{display:none}}
.gchd::before{{content:"▸";color:var(--dim);font-size:10px;transition:transform .12s}}
details[open] .gchd::before{{transform:rotate(90deg)}}
.gchd:hover{{background:#161b20}} .gcdt{{color:var(--dim);font-size:11.5px}}
.predsum{{color:var(--dim);font-size:12px}} .predsum b{{color:var(--ink)}}
.bmono{{margin-left:auto;font-family:ui-monospace,Menlo,monospace;font-size:11.5px;font-variant-numeric:tabular-nums}}
.bmono.bgood{{color:var(--good)}} .bmono.bbad{{color:var(--bad)}}
.gcbody{{padding:2px 13px 11px 26px;border-top:1px solid var(--line)}}
.gcrow{{font-size:12.5px;margin:6px 0;color:#c3c9d4;line-height:1.5}} .gcrow b{{color:var(--ink)}} .gcrow.gcdim{{color:var(--dim)}}
.gcrow .lbl{{display:inline-block;width:70px;color:var(--dim);text-transform:uppercase;font-size:10px;letter-spacing:.08em;vertical-align:top}}
.gcinterp{{font-size:11px;color:var(--dim);margin-top:8px;padding-top:6px;border-top:1px dashed var(--line);font-style:italic}}
.gcinterp b{{color:var(--ink);font-style:normal}}
.cat{{color:var(--dim);font-size:11.5px}} .empty{{color:var(--dim);font-size:12px;padding:4px 9px}}
.cslink{{font-size:11px;color:var(--good);text-decoration:none;border-bottom:1px dotted var(--good)}}
.legend{{display:flex;flex-wrap:wrap;gap:14px;margin:8px 0 22px;font-size:12px;color:var(--dim)}}
.legend b{{color:var(--ink)}}
</style></head><body>
<div class="wrap">
  <h1>Strategy Book</h1>
  <p class="sub">The book by edge source — what we executed, what we only tracked, and every dated catalyst call. As of {today}. Read-only.</p>
""")

    # top summary
    tot_held = len(held)
    tot_calls = len(seen)
    tot_resolved = sum(len(v) for v in brier.values())
    n_fail = sum(1 for t in held if unreal(t) <= FAIL_PCT)
    n_tracked = len({t for v in calls_by_class.values() for t in v if t not in held and t not in declines})
    P.append('<div class="legend">'
             f'<span><b>{tot_held}</b> live positions</span>'
             f'<span><b>{len(closed_trades)}</b> closed</span>'
             f'<span class="lup"><b>{len(upcoming)}</b> staged / upcoming</span>'
             f'<span class="lfail"><b>{n_fail}</b> failure{"" if n_fail==1 else "s"} (≤{FAIL_PCT:.0f}%)</span>'
             f'<span><b>{n_tracked}</b> no-go / watching</span>'
             f'<span><b>{len(declines)}</b> no-go / declined</span>'
             f'<span><b>{tot_resolved}</b> calls graded</span>'
             '<span>Brier = calibration error (lower = better; 0.25 = a coin-flip)</span></div>')

    for cls in ORDER:
        held_here = sorted([t for t in held if held_class[t] == cls])
        closed_here = closed_by_class.get(cls, [])   # list of closed-trade dicts
        calls_here = calls_by_class.get(cls, {})
        tracked = sorted([t for t in calls_here if t not in held and t not in declines])  # picked up, watching, NOT executed
        declined_here = sorted([t for t in declines if classify(t, (led.get(t) or {}).get("verdict"), m) == cls])
        upcoming_here = sorted([t for t in upcoming if classify(t, (led.get(t) or {}).get("verdict"), m) == cls])
        if not (held_here or closed_here or tracked or declined_here or upcoming_here):
            continue
        acc = ACCENT[cls]
        bl = brier.get(cls, [])
        bstr = f"Brier {sum(bl)/len(bl):.3f} (n={len(bl)})" if bl else "no resolved calls yet"
        ncalls = sum(len(v) for v in calls_here.values())
        P.append(f'<div class="cls" style="--acc:{acc}"><div class="clshead" style="--acc:{acc}">'
                 f'<h2 style="color:{acc}">{cls}</h2><span class="doc">{DOCTRINE[cls]}</span>'
                 f'<span class="chip">{ncalls} calls · {bstr}</span></div>')

        # UPCOMING / STAGED — the forward pipeline, what's on the clock to execute
        if upcoming_here:
            P.append('<div class="sec"><h3>Upcoming — staged / on the clock</h3><table>'
                     '<tr><th>Name</th><th>Window</th><th>Next step / plan</th></tr>')
            for t in upcoming_here:
                w = ev.get(t, {})
                win = f'{w.get("start","")} → {w.get("end","")}' if w.get("start") else "—"
                plan = (w.get("action") or (led.get(t) or {}).get("thesis") or "")[:170]
                P.append(f'<tr><td class="tk up">{tklink(t)}</td><td class="mono">{esc(win)}</td>'
                         f'<td class="cat">{esc(plan)}</td></tr>')
            P.append('</table></div>')

        # EXECUTED
        if held_here or closed_here:
            P.append('<div class="sec"><h3>Executed</h3><table>'
                     '<tr><th>Name</th><th>Shares</th><th>Entry</th><th>Mark</th><th>P&amp;L</th><th>Status</th></tr>')
            for t in held_here:
                sh, avg, mk, cur = (held[t] + ["USD"])[:4]
                u = unreal(t)
                cx = "pos" if u >= 0 else "neg"
                status = '<span class="pill fail">failure ⚠</span>' if u <= FAIL_PCT else '<span class="pill">held</span>'
                P.append(f'<tr><td class="tk">{tklink(t)}</td><td class="mono">{sh:g}</td>'
                         f'<td class="mono">{avg:g} {cur}</td><td class="mono">{mk:g}</td>'
                         f'<td class="mono {cx}">{u:+.1f}%</td><td>{status}</td></tr>')
                if notes.get(t):
                    P.append(f'<tr class="noterow"><td></td><td colspan="5" class="note">{esc(notes[t])}</td></tr>')
            for c in closed_here:
                won = (c.get("realized_usd", 0) or 0) >= 0
                cs = f' <a class="cslink" href="{esc(c["case_study"])}" target="_blank">case study →</a>' if c.get("case_study") else ""
                sign = "+" if won else "−"
                held_str = f'{esc(c.get("open",""))}→{esc(c.get("close",""))}'
                P.append(f'<tr><td class="tk">{tklink(c.get("ticker",""))}{cs}</td><td class="mono">{c.get("shares","")}</td>'
                         f'<td class="mono">{c.get("entry","")}</td><td class="mono">{c.get("exit","")}</td>'
                         f'<td class="mono {"pos" if won else "neg"}">{sign}${abs(c.get("realized_usd",0)):,} ({c.get("ret_pct","")}%)</td>'
                         f'<td><span class="pill {"win" if won else "fail"}">closed {held_str}</span></td></tr>')
            P.append('</table></div>')

        # TEARSHEET — realized trade stats; distributional metrics N-gated
        st = sleeve_stats(closed_here)
        if st:
            pf = "∞" if st["pf"] is None else f"{st['pf']:.1f}"
            wl = "—" if st["winloss"] is None else f"{st['winloss']:.1f}x"
            mae = "—" if st["avg_mae"] is None else f"{st['avg_mae']:+.1f}%"
            mfe = "—" if st["avg_mfe"] is None else f"{st['avg_mfe']:+.1f}%"
            e2h = "—" if st["avg_e2h"] is None else f"{st['avg_e2h']:.1f}x"
            thin = ' <span class="thinflag">⚠ thin (n&lt;5) — directional only</span>' if st["thin"] else ""
            dist = (f'Sharpe (per-trade) <b>{st["sharpe"]:.2f}</b>' if (st["dist_ok"] and st["sharpe"] is not None)
                    else f'Sharpe · Sortino · α · β — <span class="supp">suppressed until N≥{MIN_DIST_N} closed (this sleeve: N={st["n"]})</span>')
            P.append('<div class="sec"><h3>Tearsheet — realized' + thin + '</h3>'
                     '<div class="ts">'
                     f'<span><b>{st["n"]}</b> closed</span>'
                     f'<span>hit <b>{st["hit"]*100:.0f}%</b></span>'
                     f'<span>avg win <b class="pos">+{st["avg_win"]:.1f}%</b></span>'
                     f'<span>avg loss <b class="neg">{st["avg_loss"]:.1f}%</b></span>'
                     f'<span>win/loss <b>{wl}</b></span>'
                     f'<span>profit factor <b>{pf}</b></span>'
                     f'<span>avg return <b>{st["avg_ret"]:+.1f}%</b></span>'
                     f'<span>realized <b>${st["total_usd"]:,.0f}</b></span>'
                     f'<span>avg MAE <b>{mae}</b> · MFE <b>{mfe}</b></span>'
                     f'<span>return/heat <b>{e2h}</b></span>'
                     '</div>'
                     f'<div class="tsdist">{dist}</div></div>')

        # CALIBRATION — inline, per strategy: the graded record + Brier (graded WITHIN class)
        gc = graded_calls.get(cls, [])
        nopen = open_ct.get(cls, 0)
        if gc or nopen:
            bl = brier.get(cls, [])
            bmean = (sum(bl) / len(bl)) if bl else None
            bcls = ("bgood" if bmean < 0.25 else "bbad") if bmean is not None else ""
            bhtml = f'Brier <b class="{bcls}">{bmean:.3f}</b>' if bmean is not None else 'Brier <b>—</b>'
            P.append('<div class="sec"><h3>Calibration</h3>'
                     f'<div class="calsum"><b>{len(gc)}</b> graded · {bhtml} · <b>{nopen}</b> open '
                     '<span class="calnote">— Brier = (prediction − outcome)²; 0 = perfect, 0.25 = a coin-flip, lower is better</span></div>')
            for g in sorted(gc, key=lambda x: x["cat_date"] or "", reverse=True):
                oc = g["outcome"] or ""
                ocls = "win" if oc == "FAVORABLE" else "miss" if oc == "UNFAVORABLE" else ""
                pctp = int(round(g["our_p"] * 100))
                resolved = "YES" if oc == "FAVORABLE" else "NO" if oc == "UNFAVORABLE" else "MIXED"
                quality = ("sharp" if g["brier"] < 0.05 else "good" if g["brier"] < 0.15
                           else "fair" if g["brier"] < 0.25 else "poor")
                bq = "bgood" if g["brier"] < 0.25 else "bbad"
                how, reason = g.get("how", ""), g.get("reasoning", "")
                howrows = ""
                if how:
                    howrows += f'<div class="gcrow"><span class="lbl">How</span>{esc(how)}</div>'
                if reason and reason != how:
                    howrows += f'<div class="gcrow"><span class="lbl">Analysis</span>{esc(reason)}</div>'
                if not howrows:
                    howrows = '<div class="gcrow gcdim"><span class="lbl">How</span>(no reasoning recorded for this call)</div>'
                dets = g.get("detectors") or []
                if dets:
                    detlinks = " · ".join(f'<a class="tklink" href="/detector/{esc(dd)}" target="_blank">{esc(dd)}</a>' for dd in dets)
                    howrows += f'<div class="gcrow"><span class="lbl">Detectors</span>{detlinks}</div>'
                else:
                    howrows += '<div class="gcrow gcdim"><span class="lbl">Detectors</span>(provenance not recorded)</div>'
                madept = f' · at prediction {esc(g["made"])}' + (f', px {esc(g["px_at_pred"])}' if g.get("px_at_pred") else "") if g.get("made") else ""
                P.append('<details class="gcall">'
                         f'<summary class="gchd">{tklink(g["tk"])}<span class="gcdt mono">{esc(g["cat_date"])}</span>'
                         f'<span class="predsum">said <b>{pctp}%</b></span>'
                         f'<span class="pill {ocls}">{esc(oc.title())}</span>'
                         f'<span class="bmono {bq}">Brier {g["brier"]:.3f}</span></summary>'
                         '<div class="gcbody">'
                         f'<div class="gcrow"><span class="lbl">Predicted</span><b>{pctp}%</b> — {esc(g.get("predicted",""))}{madept}</div>'
                         f'{howrows}'
                         f'<div class="gcrow"><span class="lbl">Result</span>{esc((g.get("result") or "—")[:280])}</div>'
                         f'<div class="gcinterp">we said <b>{pctp}%</b>, it resolved <b>{resolved}</b> → {quality} '
                         f'(gap {abs(g["our_p"]-(1.0 if oc=="FAVORABLE" else 0.0 if oc=="UNFAVORABLE" else 0.5)):.2f}, squared = Brier {g["brier"]:.3f})</div>'
                         '</div></details>')
            P.append('</div>')

        # TRACKED (watching, not executed) — the IVN record: theses we handicapped but haven't put money behind
        if tracked:
            P.append('<div class="sec"><h3>No-go — handicapped &amp; watching, not executed</h3><table>'
                     '<tr><th>Name</th><th>Flagged</th><th>Catalyst date</th><th>Our call</th><th>Catalyst</th><th>Result</th></tr>')
            # order names by nearest upcoming catalyst
            def nextdate(t):
                ds = [r.get("cat_date") for r in calls_here[t] if r.get("cat_date")]
                fut = sorted([d for d in ds if d >= today]) or sorted(ds)
                return fut[0] if fut else "9"
            for t in sorted(tracked, key=nextdate):
                rows = sorted(calls_here[t], key=lambda r: r.get("cat_date") or "")
                for i, r in enumerate(rows):
                    res = r.get("resolution")
                    if res:
                        oc = res.get("outcome", "")
                        pill = f'<span class="pill {"win" if oc=="FAVORABLE" else "miss" if oc=="UNFAVORABLE" else ""}">{esc(oc.title())}</span>'
                    else:
                        pill = '<span class="pill open">open</span>'
                    p = r.get("our_p")
                    pc = f'{int(round(p*100))}%' if isinstance(p, (int, float)) else ''
                    d = r.get("direction") or ""
                    d = d.split("(")[0].replace("FAVORABLE=", "").replace("FAVORABLE =", "").replace("_", " ")[:28]
                    nm = f'<td class="tk">{tklink(t)}</td>' if i == 0 else '<td></td>'
                    P.append(f'<tr>{nm}<td class="mono">{esc(r.get("made",""))}</td>'
                             f'<td class="mono">{esc(r.get("cat_date",""))}</td>'
                             f'<td class="mono">{pc} {esc(d)}</td>'
                             f'<td class="cat">{esc((r.get("catalyst") or "")[:88])}</td><td>{pill}</td></tr>')
            P.append('</table></div>')

        # NO-GO — DECLINED: names we researched and passed on (the anti-portfolio)
        if declined_here:
            P.append('<div class="sec"><h3>No-go — declined (researched, passed)</h3><table>'
                     '<tr><th>Name</th><th>Why we passed</th></tr>')
            for t in declined_here:
                P.append(f'<tr><td class="tk">{tklink(t)}</td><td class="cat">{esc(declines[t])}</td></tr>')
            P.append('</table></div>')
        P.append('</div>')

    P.append('</div></body></html>')
    return "\n".join(P)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build())
    print(f"[strategy_book] rendered -> {OUT}")


if __name__ == "__main__":
    main()
