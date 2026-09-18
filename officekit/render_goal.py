"""render_goal — the per-goal projection page.

Click a goal on the office page and land here: the strategies currently serving
it, and a projection of when that serving capital — grown at its blended
expected return — reaches the goal. No-growth stays the floor; this shows the
growth path and the date it crosses the target.
"""
from __future__ import annotations

from officekit.fmt import esc, fmt_usd as _fmt
from officekit.goal_projection import EXPECTED_RETURN, DEFAULT_RETURN

CSS = """
body{margin:0;background:#0b0e12;color:#e8ebee;font:14px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.wrap{max-width:940px;margin:0 auto;padding:26px 24px 90px}
a{color:#b1a5ff} h1{font-size:23px;margin:0 0 4px;letter-spacing:-.02em}
.sub{color:#9aa4b0;margin:0 0 18px;font-size:13px}
h2{font-size:11.5px;text-transform:uppercase;letter-spacing:.12em;color:#9aa4b0;margin:26px 0 10px}
.panel{background:#14181d;border:1px solid #242a31;border-radius:14px;padding:16px 18px;margin-bottom:14px}
.verdict{font-size:15px;font-weight:600;margin:0 0 4px}
.stats{display:flex;gap:26px;flex-wrap:wrap;margin:10px 0 2px}
.stat .l{font-size:10.5px;color:#9aa4b0;text-transform:uppercase;letter-spacing:.09em}
.stat .n{font:660 21px/1.1 ui-monospace,Menlo,monospace;letter-spacing:-.02em;margin-top:3px}
table{width:100%;border-collapse:collapse;font-size:13px}
td,th{padding:8px 10px;border-bottom:1px solid #242a31;text-align:left}
th{font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:#9aa4b0}
td.n,th.n{text-align:right;font-family:ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums}
.note{font-size:11.5px;color:#9aa4b0;line-height:1.55;margin-top:10px}
.k{font-size:10px;font-weight:700;letter-spacing:.05em;padding:2px 8px;border-radius:20px}
.k-implemented{color:#8ee5c1;background:rgba(53,201,143,.15)}
.k-considering,.k-planned{color:#eccb8a;background:rgba(217,164,65,.15)}
.on{color:#35c98f} .off{color:#e0736a} .mid{color:#d9a441}
.spending-basis{display:flex;align-items:end;gap:10px;flex-wrap:wrap;margin:0 0 18px}
.spending-basis label{display:grid;gap:4px;max-width:100%;color:#9aa4b0;font-size:12px}
.spending-basis select,.spending-basis button{box-sizing:border-box;max-width:100%;background:#1a1f25;color:#e8ebee;border:1px solid #39424d;border-radius:8px;padding:9px 12px;font:inherit}
.spending-basis button{cursor:pointer;color:#8ee5c1;border-color:#35c98f66}
.spending-basis :focus-visible{outline:2px solid #b1a5ff;outline-offset:3px}
"""

_ON = {"on track", "already funded", "above the floor"}


def _chart(proj):
    """SVG: the growth curve vs the target line, with the goal-date marker."""
    series = proj.get("series") or []
    if not series or len(series) < 2:
        return ""
    W, H, PL, PR, PT, PB = 640, 240, 52, 16, 14, 26
    xs = [y for y, _ in series]
    vals = [v for _, v in series]
    target = proj["target"]
    ymax = max(max(vals), target) * 1.08 or 1
    x0, x1 = xs[0], xs[-1]

    def px(year):
        return PL + (year - x0) / (x1 - x0 or 1) * (W - PL - PR)

    def py(val):
        return H - PB - (val / ymax) * (H - PT - PB)

    pts = " ".join(f"{px(y):.1f},{py(v):.1f}" for y, v in series)
    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:{W}px">']
    # baseline
    parts.append(f'<line x1="{PL}" y1="{H-PB}" x2="{W-PR}" y2="{H-PB}" stroke="#242a31"/>')
    # target line
    ty = py(target)
    parts.append(f'<line x1="{PL}" y1="{ty:.1f}" x2="{W-PR}" y2="{ty:.1f}" stroke="#d9a441" '
                 f'stroke-width="1" stroke-dasharray="4 4"/>')
    parts.append(f'<text x="{W-PR}" y="{ty-4:.1f}" fill="#d9a441" font-size="10" text-anchor="end">'
                 f'target {_fmt(target)}</text>')
    # goal-date marker
    gy = proj.get("goal_year")
    if gy and x0 <= gy <= x1:
        gx = px(gy)
        parts.append(f'<line x1="{gx:.1f}" y1="{PT}" x2="{gx:.1f}" y2="{H-PB}" stroke="#b1a5ff" '
                     f'stroke-width="1" stroke-dasharray="3 3"/>')
        parts.append(f'<text x="{gx:.1f}" y="{PT+9:.1f}" fill="#c3b8fb" font-size="10" '
                     f'text-anchor="middle">goal {gy}</text>')
    # growth curve
    parts.append(f'<polyline points="{pts}" fill="none" stroke="#35c98f" stroke-width="2"/>')
    # crossover dot
    ry = proj.get("reach_year")
    if ry and x0 <= ry <= x1:
        parts.append(f'<circle cx="{px(ry):.1f}" cy="{py(target):.1f}" r="4" fill="#35c98f"/>')
    # y ticks
    for val in (0, target, ymax):
        parts.append(f'<text x="{PL-6}" y="{py(val)+3:.1f}" fill="#9aa4b0" font-size="9" '
                     f'text-anchor="end">{_fmt(val)}</text>')
    # x ticks (start / end)
    for yr in (x0, x1):
        parts.append(f'<text x="{px(yr):.1f}" y="{H-PB+14:.1f}" fill="#9aa4b0" font-size="9" '
                     f'text-anchor="middle">{yr}</text>')
    parts.append('</svg>')
    return '<div class="panel">' + "".join(parts) + '</div>'


def _rec_action(action, gid, params_endpoint):
    """Visible, explicit action text for one recommendation."""
    if not action:
        return ""
    label = action.get("label") or ("Explore growth" if action.get("kind") == "growth" else "Review this option")
    tip = esc(label[:1].upper() + label[1:])
    if action.get("kind") == "apply":
        fields = "".join(f'<input type="hidden" name="{esc(k)}" value="{esc(str(v))}">'
                         for k, v in (action.get("fields") or {}).items())
        return (f'<form method="POST" action="{esc(params_endpoint)}" class="usethis" title="{tip}">'
                f'<input type="hidden" name="gid" value="{esc(gid)}">{fields}'
                f'<button class="use" type="submit">{tip}</button></form>')
    href = "/pages/growth.html" if action.get("kind") == "growth" else action.get("href", "#")
    return (f'<a class="use usethis" href="{esc(href)}" title="{tip}">'
            f'{tip}</a>')


def _recs_html(recs, gid="", params_endpoint="/goal/params"):
    if not recs or not (recs.get("headline") or recs.get("items")):
        return ""
    P = ['<style>'
         '.usethis{margin-left:10px;flex:0 0 auto}'
         '.use{display:inline-flex;align-items:center;gap:0;background:transparent;border:1px solid #35c98f66;'
         'color:#35c98f;border-radius:20px;padding:5px 9px;font:600 12px -apple-system,sans-serif;cursor:pointer;'
         'text-decoration:none;overflow:hidden;white-space:nowrap}'
         '.use span{font-size:13px} .use em{max-width:0;opacity:0;font-style:normal;transition:max-width .2s,opacity .2s,margin .2s}'
         '.use:hover{background:rgba(53,201,143,.12)} .use:hover em{max-width:140px;opacity:1;margin-left:6px}'
         '.recrow{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}'
         '.use{white-space:normal;text-align:left}.usethis{margin-left:0}'
         '</style><h2>How to get there</h2>']
    if recs.get("headline"):
        P.append(f'<div class="panel"><p class="verdict" style="font-size:14px;margin:0">'
                 f'{esc(recs["headline"])}</p></div>')
    for it in recs.get("items") or []:
        P.append('<div class="panel" style="padding:12px 16px"><div class="recrow">'
                 f'<div><b>{esc(it["lever"])}</b>'
                 f'<div class="sub" style="margin:2px 0 0">{esc(it["detail"])}</div></div>'
                 f'{_rec_action(it.get("action"), gid, params_endpoint)}</div></div>')
    return "".join(P)


def render_goal(goal, serving, proj, office_href="/pages/goals.html",
                params_endpoint="/goal/params", recommendations=None):
    label = goal.get("label") or goal.get("kind", "Goal")
    P = [f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
         f'<meta name="viewport" content="width=device-width,initial-scale=1">'
         f'<title>{esc(label)} — projection</title><style>{CSS}</style></head><body><div class="wrap">'
         f'<p class="sub"><a href="{esc(office_href)}">← Goals</a></p>'
         f'<h1>{esc(label)}</h1>']

    if not proj.get("applicable"):
        P.append(f'<p class="sub">{esc(proj.get("reason") or "No funding target for this goal.")}</p>')
        P.append('<div class="panel">This goal is an ongoing objective, not a funding target — '
                 'there is nothing to project a date for. It shapes strategy (e.g. lot-level harvesting), '
                 'not a balance that must reach a number.</div>')
        P.append('</div></body></html>')
        return "".join(P)

    mode = proj.get("mode")
    gid = esc(str(goal.get("id") or ""))
    if goal.get("kind") == "retirement":
        basis = goal.get("spending_basis", "household_total")
        P.append('<p class="sub">Household retirement spending includes lifestyle. The shared budget counts '
                 'that spending once. Choose additional spending only for a separate obligation.</p>'
                 f'<form method="POST" action="{esc(params_endpoint)}" class="spending-basis"><input type="hidden" name="gid" value="{gid}">'
                 '<label>Retirement spending basis <select name="spending_basis">'
                 f'<option value="household_total"{" selected" if basis == "household_total" else ""}>Household total, including lifestyle</option>'
                 f'<option value="additional"{" selected" if basis == "additional" else ""}>Additional to lifestyle</option>'
                 '</select></label> <button>Save spending basis</button></form>')

    if mode == "financed":
        P.append(_financed_body(proj, gid, params_endpoint))
        P.append(_recs_html(recommendations, gid, params_endpoint))
        P.append(_serving_table(serving) + _NOTE + '</div></body></html>')
        return "".join(P)

    if mode == "expense":
        P.append(_expense_body(proj, gid, params_endpoint))
        P.append(_recs_html(recommendations, gid, params_endpoint))
        P.append(_serving_table(serving) + _NOTE + '</div></body></html>')
        return "".join(P)

    v0, target, r = proj["v0"], proj["target"], proj["blended"]
    vcls = "on" if proj["verdict"].split()[0] in ("on", "already", "above") else \
           ("off" if "short" in proj["verdict"] or "below" in proj["verdict"] or "doesn't" in proj["verdict"] else "mid")
    P.append(f'<div class="panel"><p class="verdict {vcls}">{esc(proj["verdict"])}</p>'
             f'<p class="sub" style="margin:0">Serving capital grown at a blended '
             f'<b>{r*100:.1f}%/yr</b> expected return.</p>'
             '<div class="stats">'
             f'<div class="stat"><div class="l">Serving today</div><div class="n">{_fmt(v0)}</div></div>'
             f'<div class="stat"><div class="l">Target</div><div class="n">{_fmt(target)}</div></div>'
             f'<div class="stat"><div class="l">Funded now</div><div class="n">{proj["funded_ratio"]*100:.0f}%</div></div>')
    if not proj.get("is_floor"):
        reach_txt = (f'{proj["reach_year"]}' if proj.get("reach_year") else "—")
        P.append(f'<div class="stat"><div class="l">Reaches target</div><div class="n">{reach_txt}</div></div>')
        if proj.get("goal_year"):
            P.append(f'<div class="stat"><div class="l">Your date</div><div class="n">{proj["goal_year"]}</div></div>')
        if proj.get("funded_at_date") is not None:
            P.append(f'<div class="stat"><div class="l">At your date</div>'
                     f'<div class="n">{proj["funded_at_date"]*100:.0f}%</div></div>')
    P.append('</div></div>')

    if not proj.get("is_floor"):
        P.append('<h2>Projection</h2>' + _chart(proj))

    P.append(_recs_html(recommendations, gid, params_endpoint))
    P.append(_serving_table(serving) + _NOTE + '</div></body></html>')
    return "".join(P)


_NOTE = ('<p class="note">Every figure is a first-pass house estimate (nominal, before tax), '
         'refined from realized returns later — not a forecast. Serving capital OVERLAPS across goals: '
         'one sleeve can fund several, so these balances are not exclusive to this goal. The no-growth '
         'check on the office page remains the conservative floor; the Scenario Planner re-scores through '
         'each tail. Adjust the assumptions above and hit Enter to re-run.</p>')


def _serving_table(serving):
    P = ['<h2>Strategies serving this goal</h2>']
    if serving:
        P.append('<table><tr><th>Strategy</th><th>Status</th><th class="n">Held now</th>'
                 '<th class="n">% of NW</th><th class="n">Assumed return</th></tr>')
        for e in sorted(serving, key=lambda x: -(x.get("cur_val") or 0)):
            er = EXPECTED_RETURN.get(e.get("sid"), DEFAULT_RETURN)
            st = (e.get("status") or "").replace("_", " ")
            P.append(f'<tr><td>{esc(e.get("title") or e.get("sid"))}</td>'
                     f'<td><span class="k k-{esc(e.get("status") or "")}">{esc(st.upper())}</span></td>'
                     f'<td class="n">{_fmt(e.get("cur_val") or 0)}</td>'
                     f'<td class="n">{(e.get("cur_pct") or 0):.1f}%</td>'
                     f'<td class="n">{er*100:.1f}%</td></tr>')
        P.append('</table>')
    else:
        P.append('<div class="panel">No strategy is serving this goal yet — attach one on the '
                 '<a href="/pages/strategies.html">Strategies page</a>.</div>')
    return "".join(P)


def _row(label, val, strong=False):
    b = ' style="font-weight:700"' if strong else ""
    return f'<tr{b}><td>{esc(label)}</td><td class="n">{_fmt(val)}</td></tr>'


def _num_input(name, value, suffix=""):
    return (f'<label style="font-size:11px;color:#9aa4b0">{esc(name.replace("_"," "))}'
            f'<input name="{name}" value="{value}" style="width:100%;margin-top:3px;background:#1a1f25;'
            f'color:#e8ebee;border:1px solid #242a31;border-radius:8px;padding:7px 9px">{suffix}</label>')


def _financed_body(p, gid, params_endpoint):
    vcls = "on" if p["affordable"] else "off"
    SWR_pct = 4  # display; the model uses officekit.goals.SWR
    P = [f'<div class="panel"><p class="verdict {vcls}">{esc(p["verdict"])}</p>'
         f'<p class="sub" style="margin:0">A financed purchase: ~{p["down_pct"]:g}% down (raised from the '
         f'portfolio, capital-gains tax and all), the rest mortgaged, then carried for {p["term_years"]:g} years.</p>'
         '<div class="stats">'
         f'<div class="stat"><div class="l">Price</div><div class="n">{_fmt(p["price"])}</div></div>'
         f'<div class="stat"><div class="l">Cash to close</div><div class="n">{_fmt(p["cash_needed"])}</div></div>'
         f'<div class="stat"><div class="l">Mortgage</div><div class="n">{_fmt(p["mortgage"])}</div></div>'
         f'<div class="stat"><div class="l">Carry / yr</div><div class="n">{_fmt(p["annual_carry"])}</div></div>'
         f'<div class="stat"><div class="l">Portfolio sustains</div><div class="n">{_fmt(p["sustainable"])}/yr</div></div>'
         '</div></div>']
    # what it takes to buy
    P.append('<h2>What it takes to buy</h2><table>')
    P.append(_row(f'Down payment ({p["down_pct"]:g}% of price)', p["down"]))
    P.append(_row(f'+ cap-gains tax to raise it (~{p["embedded_gain_pct"]:g}% embedded @ {p["ltcg_rate"]*100:.1f}%)',
                  p["tax_to_raise"]))
    P.append(_row('+ closing costs', p["closing"]))
    P.append(_row('= liquidated from the portfolio', p["cash_needed"], strong=True))
    P.append('</table>')
    # what it costs to carry
    P.append('<h2>What it costs to carry (per year)</h2><table>')
    P.append(_row(f'Mortgage {_fmt(p["mortgage"])} @ {p["rate_pct"]:g}% / {p["term_years"]:g}y — P&I', p["annual_pi"]))
    P.append(_row('Property tax', p["prop_tax"]))
    P.append(_row('Maintenance', p["maint"]))
    P.append(_row('Insurance', p["insurance"]))
    P.append(_row('= annual carrying cost', p["annual_carry"], strong=True))
    P.append('</table>')
    # can the portfolio carry it
    P.append('<h2>Can the portfolio carry it?</h2><table>')
    P.append(_row('Marketable assets today', p["marketable"]))
    P.append(_row('− liquidated for the purchase', -p["cash_needed"]))
    P.append(_row('= post-purchase marketable', p["post_marketable"], strong=True))
    P.append(_row(f'sustainable at {SWR_pct}% withdrawal', p["post_marketable"] * 0.04))
    P.append(_row('− drag from existing debt', -p["existing_service"]))
    P.append(_row('= sustainable per year', p["sustainable"], strong=True))
    P.append(_row('vs the annual carrying cost', p["annual_carry"]))
    P.append('</table>')
    # adjustable assumptions
    fin = p.get("params", {})
    P.append(f'<h2>Adjust the deal</h2><form method="POST" action="{esc(params_endpoint)}">'
             f'<input type="hidden" name="gid" value="{gid}">'
             '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px">'
             + _num_input("amount", int(p["price"]))
             + _num_input("down_pct", fin.get("down_pct", 25))
             + _num_input("rate_pct", fin.get("rate_pct", 6.5))
             + _num_input("term_years", fin.get("term_years", 30))
             + _num_input("tax_pct", fin.get("tax_pct", 1.1))
             + _num_input("maint_pct", fin.get("maint_pct", 1.0))
             + '</div>'
             '<button type="submit" style="margin-top:10px;background:#35c98f;color:#08110d;border:0;'
             'border-radius:9px;padding:9px 18px;font-weight:700;cursor:pointer">Re-run</button>'
             '<span style="font-size:11px;color:#9aa4b0;margin-left:8px">or hit Enter in any field</span>'
             '</form>')
    return "".join(P)


def _expense_body(p, gid, params_endpoint):
    vcls = "on" if p["affordable"] else "off"
    P = [f'<div class="panel"><p class="verdict {vcls}">{esc(p["verdict"])}</p>'
         '<p class="sub" style="margin:0">An ongoing annual outlay — a permanent drag the portfolio must sustain.</p>'
         '<div class="stats">'
         f'<div class="stat"><div class="l">Annual expense</div><div class="n">{_fmt(p["annual"])}</div></div>'
         f'<div class="stat"><div class="l">Portfolio sustains</div><div class="n">{_fmt(p["sustainable"])}/yr</div></div>'
         f'<div class="stat"><div class="l">Covers</div><div class="n">{p["covers_pct"]:.0f}%</div></div>'
         '</div></div>']
    P.append('<h2>The math</h2><table>')
    P.append(_row('Marketable assets', p["marketable"]))
    P.append(_row('sustainable at 4% withdrawal', p["marketable"] * 0.04))
    P.append(_row('− drag from existing debt', -p["existing_service"]))
    P.append(_row('= sustainable per year', p["sustainable"], strong=True))
    P.append(_row('this expense', p["annual"]))
    P.append('</table>')
    P.append(f'<h2>Adjust the expense</h2><form method="POST" action="{esc(params_endpoint)}">'
             f'<input type="hidden" name="gid" value="{gid}">'
             '<div style="max-width:260px">' + _num_input("annual_amount", int(p["annual"]), " per year") + '</div>'
             '<button type="submit" style="margin-top:10px;background:#35c98f;color:#08110d;border:0;'
             'border-radius:9px;padding:9px 18px;font-weight:700;cursor:pointer">Re-run</button>'
             '<span style="font-size:11px;color:#9aa4b0;margin-left:8px">or hit Enter</span></form>')
    return "".join(P)
