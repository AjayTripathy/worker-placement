"""render_office — the family-office dashboard page (the desk's OFFICE tab).

Ported from desk/household.py build() (Phase-0 extraction, byte-parity tested).
Everything client-specific comes from the model's data dict: owner name, category
labels, the opportunity inbox (templated items), the liquidity-note tail, sleeve
shorts. READ-ONLY — renders HTML, never places orders.
"""
from __future__ import annotations

from officekit.commitments import pending_deployable, tax_funding

import math
from datetime import datetime
from urllib.parse import quote

from officekit.fmt import esc, fmt_usd as _fmt, betacell as _betacell
from officekit.model import catmap_for, strategy_tags


def _greeting(now=None):
    h = (now or datetime.now()).hour
    return "Good morning" if h < 12 else "Good afternoon" if h < 18 else "Good evening"


def _donut(segs, center_top, center_bot):
    """segs = [(label, value, hex)]. Returns the donut+legend html. Ring of gross assets."""
    tot = sum(v for _, v, _ in segs) or 1
    R, SW = 54, 20
    C = 2 * math.pi * R
    parts = ['<svg viewBox="0 0 140 140" width="180" height="180" style="transform:rotate(-90deg)">']
    parts.append(f'<circle cx="70" cy="70" r="{R}" fill="none" stroke="#1b2027" stroke-width="{SW}"/>')
    acc = 0.0
    for label, val, hexc in segs:
        frac = val / tot
        parts.append(
            f'<circle cx="70" cy="70" r="{R}" fill="none" stroke="{hexc}" stroke-width="{SW}" '
            f'stroke-dasharray="{frac*C:.2f} {C:.2f}" stroke-dashoffset="{-acc*C:.2f}" '
            f'stroke-linecap="butt"><title>{esc(label)} {frac*100:.1f}%</title></circle>')
        acc += frac
    parts.append('</svg>')
    leg = ['<div class="legend">']
    for label, val, hexc in segs:
        pct = val / tot * 100
        leg.append(
            f'<div class="lg"><span class="dot" style="background:{hexc}"></span>'
            f'<span class="lgn">{esc(label)}</span>'
            f'<span class="lgv">{_fmt(val)}</span><span class="lgp">{pct:.1f}%</span></div>')
    leg.append('</div>')
    svg = (f'<div class="donutwrap"><div class="donut">{"".join(parts)}'
           f'<div class="dc"><div class="dct">{center_top}</div><div class="dcb">{center_bot}</div></div></div>'
           f'{"".join(leg)}</div>')
    return svg


def _default_opportunities(m, ctx):
    """Generic on-deck items when the client's data supplies none."""
    d = m["d"]
    items = []
    if any(s["category"] == "cash_pending" for s in m["assets"]):
        items.append({"icon": "💧", "title": "Deploy the incoming powder", "tone": "violet", "chip": "PLANNING",
                      "body": "{net_txt} — the largest allocation decision on the board; new capital is the cheapest rebalancing lever.",
                      "value": "{net_deployable}"})
    tbd = [s for s in d["sleeves"] if s.get("_confidence") == "tbd"]
    if tbd:
        items.append({"icon": "📝", "title": "Complete the balance sheet", "tone": "slate", "chip": "TODO",
                      "body": f"{len(tbd)} sleeves still TBD: {', '.join(s.get('short') or s['name'].split(' ')[0] for s in tbd)}. "
                              "Confirm values from statements + set targets; then the numbers drive the Scenario Planner cleanly.",
                      "value": f"{len(tbd)} TBD"})
    else:
        items.append({"icon": "✅", "title": "Balance sheet — sourced", "tone": "emerald", "chip": "OK",
                      "body": "Every sleeve carries a confidence tag. Next: confirm target weights per sleeve, "
                              "then the numbers drive the Scenario Planner cleanly.",
                      "value": "DONE"})
    return items


def _opportunities(m):
    """The on-deck inbox — client items (templated) or generic defaults; no fabricated savings."""
    d, A = m["d"], m["A"]
    tax = m["tax"]
    pending_tax = tax_funding(m)["pending"]
    pending = sum(s["value"] for s in m["assets"] if s["category"] == "cash_pending")
    para = next((s for s in d["sleeves"] if s["category"] == "direct_index"), None)
    ctx = {
        "net_txt": (f"{_fmt(pending)} gross → ~{_fmt(pending_deployable(m))} net after an est. {_fmt(pending_tax)} tax reserve "
                    f"({tax['char'].upper()}, less harvest)" if pending > 0 and pending_tax > 0 else f"{_fmt(pending)}"),
        "net_deployable": _fmt(pending_deployable(m)) if pending > 0 and pending_tax > 0 else _fmt(pending),
        "para_pct": (para["value"] / A * 100) if para else 0,
    }
    items = d.get("opportunities") or _default_opportunities(m, ctx)
    rows = ['<div class="oppinbox">']
    for it in items:
        rows.append(
            f'<div class="opp"><div class="oppic t-{it["tone"]}">{it["icon"]}</div>'
            f'<div class="oppmid"><div class="oppt">{esc(it["title"].format(**ctx))} <span class="chip c-{it["tone"]}">{esc(it["chip"].format(**ctx))}</span></div>'
            f'<div class="opps">{esc(it["body"].format(**ctx))}</div></div>'
            f'<div class="oppv">{esc(it["value"].format(**ctx))}</div></div>')
    rows.append('</div>')
    return "\n".join(rows)


_EDITOR_STYLE = """<style>
.nlbox{display:flex;gap:8px;margin-bottom:6px}
.nlbox input{flex:1;background:#1a1f25;color:#e8ebee;border:1px solid #242a31;border-radius:8px;padding:8px 10px;font:500 13px -apple-system,BlinkMacSystemFont,sans-serif}
.grow4{display:grid;grid-template-columns:1.1fr 1.3fr .9fr .8fr;gap:8px;margin-top:8px}
.grow4 input,.grow4 select{background:#1a1f25;color:#e8ebee;border:1px solid #242a31;border-radius:8px;padding:8px 10px;font:500 13px -apple-system,BlinkMacSystemFont,sans-serif}
.gchip{background:#1a1f25;color:#e8ebee;border:1px solid #242a31;border-radius:16px;padding:4px 11px;font-size:11.5px;cursor:pointer}
.gchip:hover{border-color:#b1a5ff}
.gbtn{background:#35c98f;color:#08110d;border:0;border-radius:9px;padding:9px 18px;font-weight:700;cursor:pointer}
.gbtn2{background:#1a1f25;color:#e8ebee;border:1px solid #242a31;border-radius:9px;padding:9px 14px;font-weight:600;cursor:pointer}
.goalrow{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid #242a31;font-size:13px}
.goalrow .g b{font-family:ui-monospace,Menlo,monospace}
.gx{background:transparent;color:#9aa4b0;border:0;font-size:18px;line-height:1;cursor:pointer;padding:0 4px;border-radius:6px}
.gx:hover{color:#e0736a;background:rgba(224,115,106,.12)}
.goallink{color:#e8ebee;text-decoration:none;border-bottom:1px dashed rgba(53,201,143,.45);cursor:pointer;font-weight:600}
.goallink:hover{color:#35c98f;border-bottom-color:#35c98f}
.goal-serving{margin:12px 0 18px}.goal-serving-label{font-size:11px;color:#9aa4b0;margin:0 0 6px}
.goal-strategies{list-style:none;padding:0;margin:0;display:grid;gap:6px}
.goal-strategies a{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:5px 16px;padding:9px 12px;border:1px solid #242a31;border-radius:8px;text-decoration:none;color:#35c98f;font-size:12px}
.goal-strategies a:hover{background:#1a1f25;border-color:#35c98f66}.goal-strategies a:focus-visible{outline:2px solid #35c98f;outline-offset:3px}
.goal-strategy-name{font-weight:600;overflow-wrap:anywhere}.goal-strategy-meta{color:#9aa4b0;font-size:11px}
.intuited{font-size:9.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#c3b8fb;background:rgba(177,165,255,.15);border-radius:20px;padding:2px 8px;margin-left:6px}
.implicit-why{color:#9aa4b0;font-size:12px;line-height:1.5;padding:2px 0 10px 14px}
.implicit-actions{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:6px}
.implicit-add{display:inline-flex;gap:6px;margin:0}
.implicit-add input{width:92px;background:#1a1f25;color:#e8ebee;border:1px solid #242a31;border-radius:8px;padding:6px 9px;font-size:12px}
.linkish{background:transparent;border:0;color:#35c98f;cursor:pointer;font:600 12px -apple-system,sans-serif;padding:0}
.linkish:hover{text-decoration:underline}
</style>"""

_GOALS_JS = """<script>
function goalAdd(){
  var d=document.createElement('div'); d.className='grow4';
  d.innerHTML='<input type="hidden" name="gid" value=""><select name="gkind"><option value="">— kind —</option>'+
    '<option value="retirement">Retirement (spend/yr)</option><option value="spending">Dated target ($)</option>'+
    '<option value="liquidity_floor">Liquidity floor ($)</option></select>'+
    '<input name="glabel" placeholder="label"><input name="gdate" placeholder="YYYY-MM-DD"><input name="gamt" placeholder="$">';
  var f=document.getElementById('goalform'); f.insertBefore(d, f.children[f.children.length-2]); return d;
}
function goalChip(s){
  var rows=document.querySelectorAll('#goalform .grow4'), row=null;
  for(var i=0;i<rows.length;i++){var k=rows[i].querySelector('[name=gkind]');
    if(!k.value && !rows[i].querySelector('[name=glabel]').value){row=rows[i];break;}}
  if(!row)row=goalAdd();
  row.querySelector('[name=gkind]').value=s.kind; row.querySelector('[name=glabel]').value=s.label;
  row.querySelector('[name=gamt]').value=s.amount;
  if(s.years_out){var d=new Date();
    row.querySelector('[name=gdate]').value=(d.getFullYear()+s.years_out)+'-'+
      ('0'+(d.getMonth()+1)).slice(-2)+'-'+('0'+d.getDate()).slice(-2);}
}
function goalNL(){
  var box=document.getElementById('goalnl'); if(!box)return; var txt=box.value.trim(); if(!txt)return;
  var st=document.getElementById('goalnlstatus'); st.textContent='reading…';
  fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({scope:'goals',messages:[{role:'user',content:txt}]})})
   .then(function(r){return r.json();}).then(function(t){
     if(t.error){st.textContent=t.error;return;}
     var gs=((t.answers||{}).goals)||[], n=0;
     gs.forEach(function(g){var row=goalAdd();
       row.querySelector('[name=gkind]').value=g.kind||'spending';
       row.querySelector('[name=glabel]').value=g.label||'';
       if(g.date)row.querySelector('[name=gdate]').value=g.date;
       var amt=(g.kind==='retirement')?g.annual_spending:g.amount;
       if(amt!=null)row.querySelector('[name=gamt]').value=amt; n++;});
     st.textContent = n?('filled '+n+' goal(s) — review, then Save goals'):(t.reply||'nothing recognized');
     box.value='';
   }).catch(function(e){st.textContent='error: '+e;});
}
</script>"""

_ASSETS_JS = """<script>
function assetAdd(){
  var rows=document.querySelectorAll('#arows .arow');
  var c=rows[rows.length-1].cloneNode(true);
  c.querySelectorAll('input').forEach(function(i){i.value='';});
  c.querySelector('select').value='';
  document.getElementById('arows').appendChild(c); return c;
}
function assetFill(kind,name,value,rate){
  var rows=document.querySelectorAll('#arows .arow'), row=null;
  for(var i=0;i<rows.length;i++){var k=rows[i].querySelector('[name=u_kind]'),
    nm=rows[i].querySelector('[name=u_name]');
    if(!k.value && !nm.value){row=rows[i];break;}}
  if(!row)row=assetAdd();
  row.querySelector('[name=u_kind]').value=kind||'ticker';
  row.querySelector('[name=u_name]').value=name||'';
  row.querySelector('[name=u_value]').value=(value!=null?value:'');
  if(rate)row.querySelector('[name=u_rate]').value=rate;
}
function assetNL(){
  var box=document.getElementById('assetnl'); if(!box)return; var txt=box.value.trim(); if(!txt)return;
  var st=document.getElementById('assetnlstatus'); st.textContent='reading…';
  fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({scope:'assets',messages:[{role:'user',content:txt}]})})
   .then(function(r){return r.json();}).then(function(t){
     if(t.error){st.textContent=t.error;return;}
     var a=t.answers||{}, n=0;
     (a.sleeves||[]).forEach(function(s){assetFill(s.category,s.name||'',s.value,s.rate_pct||'');n++;});
     (((a.positions||{}).rows)||[]).forEach(function(p){assetFill('ticker',p.symbol,p.value,'');n++;});
     st.textContent = n?('filled '+n+' row(s) — review, then Add to office'):(t.reply||'nothing recognized');
     box.value='';
   }).catch(function(e){st.textContent='error: '+e;});
}
</script>"""


def _implicit_goal_row(g, add_ep, mortgage_ep, chat, assets_ep=None, revision=None):
    from officekit.render_capital import commitment_card
    return commitment_card(g, revision, chat, back="office")


def _goals_panel(m, d, assets, sleeves, cash_now, goals_endpoint, chat,
                 strategies_href="/pages/strategies.html", assets_endpoint=None,
                 back="office", natural_language=True):
    """The goals panel. Goals ADD-ON-ENTER (each form submits on Enter and
    rebuilds) — no separate Save, and each existing goal carries a × remove, so
    adding never overwrites (the 2026-09-08 fix). An unserved goal links to the
    Strategies page to create/attach one; existing strategies that fit are linked
    automatically on add. `goals_endpoint` is the base ('/goals'); add/remove
    hang off it."""
    goal_defs = d.get("goals") or []
    if not goal_defs and not goals_endpoint:
        return ""                          # static/export view: no goals, no editor -> no section
    add_ep = (goals_endpoint or "/goals") + "/add"
    rm_ep = (goals_endpoint or "/goals") + "/remove"
    mortgage_ep = (goals_endpoint or "/goals") + "/mortgage"
    P = [('<style>\n.commit-card{background:#11171d;border:1px solid #28313c;border-radius:12px;padding:15px;margin:12px 0}\n.commit-head{display:flex;justify-content:space-between;gap:12px}.commit-head h3{font-size:14px;margin:0}.commit-status{font-size:10px;text-transform:uppercase;color:#edcc8a}.commit-status.confirmed{color:#8ee5c1}.commit-amount{font-size:22px;font-weight:600;margin:8px 0}.commit-card .sub{color:#9aa4b0;font-size:12px;line-height:1.6}.commit-card details{border-top:1px solid #28313c;padding-top:10px;margin-top:12px}.commit-card summary{cursor:pointer;color:#b1a5ff;font-size:12px}.commit-fields{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:12px 0}.commit-card label{display:block;font-size:11px;color:#adb7c3}.commit-card input,.commit-card select,.commit-card textarea{width:100%;min-width:0;box-sizing:border-box;background:#0b0e12;border:1px solid #354050;border-radius:7px;padding:9px;color:#e8ebee;margin-top:4px;font:inherit}.commit-card input[type=hidden]{display:none}.commit-card textarea{min-height:80px}.commit-card button{background:#8ee5c1;color:#0b1511;border:0;padding:9px 14px;border-radius:7px;font-weight:600;cursor:pointer}.commit-card .muted{font-size:10px;color:#9aa4b0}@media(max-width:700px){.commit-fields{grid-template-columns:1fr}}\n</style>' if any(g.get('implicit') for g in goal_defs) else ''), '<div class="panel">',
         '<div class="ph"><h3>Your goals &amp; commitments</h3>'
         '<a class="hint" href="/pages/capital.html">Cash calendar →</a></div>']

    if goal_defs:
        from officekit import goals as goals_mod
        from officekit.goal_mandates import goal_coverage
        GOAL_COLOR = {"OK": "#35c98f", "TIGHT": "#d9a441", "SHORT": "#e0736a"}
        cov = goal_coverage(m)["by_goal"]
        for g in goal_defs:
            if g.get("implicit"):
                P.append(_implicit_goal_row(g, add_ep, mortgage_ep, chat, assets_endpoint, m.get("_commitment_revision") if goals_endpoint else None))
                continue
            ev = goals_mod.evaluate_in_model(g, m)
            gid = esc(str(g.get("id") or ""))
            color = GOAL_COLOR.get(ev["status"], "#8a939e")
            rm = (f'<form method="POST" action="{esc(rm_ep)}" style="margin:0">'
                  f'<input type="hidden" name="gid" value="{gid}">'
                  f'<button class="gx" title="Remove goal" aria-label="Remove {esc(ev["label"])}">&times;</button></form>') if g.get("id") else ""
            # the label links to the goal's projection page (when to reach it) —
            # styled so it clearly reads as clickable
            label = (f'<a class="goallink" href="/pages/goal_{gid}.html" title="open the projection">'
                     f'{esc(ev["label"])} <span style="color:var(--emerald)">→</span></a>'
                     if g.get("id") else esc(ev["label"]))
            status_label = {"OK": "On track", "TIGHT": "Close to limit", "SHORT": "Funding gap"}.get(ev["status"], ev["status"])
            P.append('<div class="goalrow">'
                     f'<div><div class="goal-title">{label}</div><div class="goal-target">{esc(ev["target_txt"])}</div></div>'
                     f'<span class="goal-status" style="color:{color}">{esc(status_label)}</span>{rm}</div>')
            if ev.get("assessment", {}).get("mode") == "financed":
                a = ev["assessment"]
                P.append(f'<div class="goal-measures"><span>Cash to close <b>{_fmt(a["cash_needed"])}</b>'
                         f' · {ev["closing_ratio"]:.2f}× covered</span><span>Annual carry <b>{_fmt(a["annual_carry"])}</b>'
                         f' · {_fmt(a["sustainable"])}/yr capacity</span></div>')
            else:
                P.append(f'<p class="goal-detail">{esc(ev["detail"])}</p>')
            serving = cov.get(g.get("id"), [])
            if serving:
                P.append('<div class="goal-serving"><p class="goal-serving-label">Served by</p>'
                         f'<ul class="goal-strategies" aria-label="Strategies serving {esc(ev["label"])}">')
                for e in serving:
                    href = strategies_href + '#strat-' + quote(str(e['sid']), safe='')
                    status = e['status'].replace('_', ' ').capitalize()
                    allocation = f' · {e["cur_pct"]:.1f}% now' if e['cur_val'] else ''
                    P.append(f'<li><a href="{esc(href)}"><span class="goal-strategy-name">{esc(e["title"])} '
                             f'<span aria-hidden="true">→</span></span>'
                             f'<span class="goal-strategy-meta">{esc(status)}{allocation}</span></a></li>')
                P.append('</ul></div>')
            elif g.get("id"):
                P.append(f'<div class="g" style="font-size:11px;padding:1px 0 8px 14px">'
                         f'→ no strategy serving this goal yet — '
                         f'<a href="{esc(strategies_href)}#goal-{gid}" style="color:var(--emerald)">'
                         f'create or attach one on the Strategies page →</a></div>')
        P.append(_contention_panel(m, goal_defs))

    if goals_endpoint:
        P.append('<details class="entry-tools" id="add-goal"><summary>＋ Add a goal</summary>')
        import json as _json
        from datetime import datetime as _dt
        from officekit.goals import GOAL_LIB
        try:
            _yr = int(str(d.get("as_of") or "")[:4])
        except ValueError:
            _yr = _dt.now().year
        # natural-language add — Enter submits, the server parses + appends + rebuilds
        if chat and natural_language:
            P.append(f'<form method="POST" action="{esc(add_ep)}" class="nlbox" style="margin-top:12px">'
                     '<input id="goalnl" name="nl" placeholder="Add a goal in plain words — '
                     'e.g. \'retire in 2050 spending 110k a year\' or \'300k for college in 2035\'" autocomplete="off">'
                     '<button class="gbtn2">Add</button></form>')
        # quick-add chips — each posts one sample goal directly
        chip_forms = []
        for s in GOAL_LIB:
            yo = s.get("years_out") or 0
            date_field = (f'<input type="hidden" name="gdate" value="{_yr + yo}-01-01">' if yo else "")
            chip_forms.append(
                f'<form method="POST" action="{esc(add_ep)}" style="margin:0;display:inline">'
                f'<input type="hidden" name="gkind" value="{esc(s["kind"])}">'
                f'<input type="hidden" name="glabel" value="{esc(s["label"])}">'
                f'<input type="hidden" name="gamt" value="{esc(str(s["amount"]))}">{date_field}'
                f'<button class="gchip" title="{esc(s["hint"])}">{esc(s["label"])} +</button></form>')
        P.append('<div style="display:flex;flex-wrap:wrap;gap:6px;margin:10px 0">' + "".join(chip_forms) + '</div>')
        # precise manual add — Enter on any field submits
        KINDS = [("spending", "Dated target ($)"), ("retirement", "Retirement (spend/yr)"),
                 ("expense", "Ongoing expense ($/yr)"), ("liquidity_floor", "Liquidity floor ($)")]
        kopts = "".join(f'<option value="{k}">{t}</option>' for k, t in KINDS)
        P.append(f'<form method="POST" action="{esc(add_ep)}" class="grow4">'
                 f'<select name="gkind" aria-label="Goal type">{kopts}</select>'
                 '<input name="glabel" aria-label="Goal name" placeholder="label"><input name="gdate" aria-label="Target date" placeholder="YYYY-MM-DD">'
                 '<input name="gamt" aria-label="Target amount" placeholder="$">'
                 '<button class="gbtn2" type="submit">Add goal</button></form>'
                 '<div class="hint" style="margin-top:6px">Type a goal and hit Enter — it adds and saves '
                 'immediately; the × removes it. Retirement reads the amount as total annual household spending, '
                 'including lifestyle. Its goal page lets you mark separate spending as additional.</div>')
        P.append('</details>')
    P.append('</div>' + _EDITOR_STYLE)
    result = "".join(P)
    if back == "goals":
        result = result.replace('Your goals &amp; commitments', 'Your goals')
        # Keep additions/removals in the page where the user started.
        result = result.replace('</form>', '<input type="hidden" name="back" value="goals"></form>')
    return result


def _contention_panel(m, goal_defs):
    """Do the goals fit TOGETHER? One shared capital + ongoing budget."""
    active = [g for g in (goal_defs or [])
              if g.get("kind") != "tax_efficiency" and not g.get("implicit")]
    if len(active) < 2:
        return ""
    from officekit.goal_contention import contention
    con = contention(m, goal_defs)
    col = "#35c98f" if con["feasible"] else "#e0736a"
    P = [f'<div class="panel" style="margin-top:12px;border-color:{col}55">',
         '<div class="ph"><h3>Do your goals fit together?</h3>'
         f'<span class="hint">one shared pool · {con["n"]} goals</span></div>',
         f'<p style="color:{col};font-weight:600;margin:0 0 10px;font-size:13px">{esc(con["verdict"])}</p>',
         f'<div class="liqrow"><span class="g">Up-front capital needed</span>'
         f'<b>{_fmt(con["capital_claim"])} of {_fmt(con["capital_pool"])}</b></div>',
         f'<div class="liqrow"><span class="g">Ongoing cost / yr</span>'
         f'<b>{_fmt(con["carry_claim"])} of {_fmt(max(con["carry_budget"], 0))} sustainable</b></div>']
    for e in con["cascade"]:
        c = e["claim"]
        parts = []
        if c["capital"]:
            parts.append(f'{_fmt(c["capital"])} up front')
        if c["carry"]:
            parts.append(f'{_fmt(c["carry"])}/yr')
        detail = " · ".join(parts) or "no capital claim"
        mcol = "#35c98f" if e["feasible"] else "#e0736a"
        mark = "✓" if e["feasible"] else "✗"
        P.append(f'<div class="g" style="font-size:11.5px;padding:3px 0 3px 14px">'
                 f'<span style="color:{mcol}">{mark}</span> '
                 f'{esc(e["goal"].get("label") or e["goal"].get("kind"))} — {detail}</div>')
    P.append('<div class="hint" style="margin-top:6px">Funded in list order; the same capital can\'t serve '
             'two goals at once. Reorder or trim to change what fits.</div></div>')
    return "".join(P)


def _assets_panel(assets_endpoint, chat):
    """The 'Add to your office' panel: an asset-row editor + a natural-language
    box that fills the rows via /chat. Self-contained (JS inline)."""
    if not assets_endpoint:
        return ""
    AKINDS = [("ticker", "Ticker — classify for me"), ("cash", "Cash / MMF"),
              ("public_equity", "Public-equity fund"), ("single_name_equity", "Single stock"),
              ("fixed_income", "Bonds / fixed income"), ("municipal_credit", "Munis"),
              ("real_estate", "Real estate"), ("real_estate_debt", "Mortgage / debt (balance +)"),
              ("venture_private", "Private / venture"), ("human_capital", "Income (human capital)")]
    aopts = '<option value="">— type —</option>' + "".join(
        f'<option value="{k}">{esc(t)}</option>' for k, t in AKINDS)
    arow = (f'<div class="grow4 arow"><select name="u_kind">{aopts}</select>'
            '<input name="u_name" placeholder="ticker or name">'
            '<input name="u_value" placeholder="$"><input name="u_rate" placeholder="rate % (debt)"></div>')
    asset_nl = ('<div class="nlbox"><input id="assetnl" placeholder="Add an asset in plain words '
                '— e.g. \'$40k private stake in Acme\' or \'I own 500 shares of NVDA\'">'
                '<button type="button" class="gbtn2" onclick="assetNL()">Read it</button></div>'
                '<div id="assetnlstatus" class="hint" style="margin:2px 0 8px"></div>') if chat else ""
    return ('<div class="panel">'
            '<div class="ph"><h3>Add to your office</h3>'
            '<span class="hint">assets &amp; holdings · changes rebuild the office</span></div>'
            f'<form method="POST" action="{esc(assets_endpoint)}" id="assetform">'
            + asset_nl
            + '<div id="arows">' + arow + '</div>'
            '<div style="margin-top:8px;display:flex;gap:10px">'
            '<button type="button" class="gbtn2" onclick="assetAdd()">+ another</button>'
            '<button type="submit" class="gbtn">Add to office</button></div>'
            '<div class="hint" style="margin-top:6px">Tickers are classified into sleeves; everything else '
            'is a sleeve as typed. For a debt (mortgage) enter the balance as a positive number.</div>'
            '</form></div>' + _ASSETS_JS)


def _decision_brief(m):
    """The lead: the few things that need a decision, ordered urgent capital
    decisions → goal shortfalls → stale inputs → everything else. Deploying new
    capital is the largest lever, so it leads when there is powder to place."""
    from officekit.risk_officer import review
    P = []
    tax = m.get("tax")
    pending_tax = tax_funding(m)["pending"]
    pending = sum(s["value"] for s in m["assets"] if s["category"] == "cash_pending")
    if pending > 0:
        deployable = pending_deployable(m)
        net_txt = (f"{_fmt(deployable)} net after an est. {_fmt(pending_tax)} tax reserve"
                   if pending > 0 and pending_tax > 0 else _fmt(deployable))
        P.append(f'<a class="decision" href="#deploy-plan"><span class="decision-priority">Decide first</span>'
                 f'<strong>Deploy the incoming {_fmt(pending)}</strong>'
                 f'<span class="decision-copy">{net_txt} to place — the largest allocation decision on the '
                 f'board. New capital is the cheapest rebalancing lever.</span>'
                 f'<span class="decision-link">Compare the allocation →</span></a>')

    findings = review(m)
    items = findings.get("findings", []) if isinstance(findings, dict) else findings

    def _rank(f):
        t = f.get("title", "")
        cat = (0 if t.startswith("Funding gap") or "Goals conflict" in t          # goal shortfalls
               else 1 if "refresh" in t.lower() or "stale" in t.lower()           # stale inputs
               else 2)
        return (0 if f["severity"] == "high" else 1, cat)

    visible = sorted([f for f in items if f.get("severity") in ("high", "medium")],
                     key=_rank)[:4 - len(P)]
    for f in visible:
        action = f.get("action") or {}
        href = action.get("href") or ('/pages/growth.html' if action.get('kind') == 'growth' else '/pages/risk.html')
        label = action.get("label") or 'Review finding'
        label = label[:1].upper() + label[1:]
        P.append(f'<a class="decision" href="{esc(href)}"><span class="decision-priority">'
                 f'{"Review first" if f.get("severity") == "high" else "Worth a look"}</span>'
                 f'<strong>{esc(f.get("title", "Review finding"))}</strong>'
                 f'<span class="decision-copy">{esc(f.get("detail") or f.get("body") or "")}</span>'
                 f'<span class="decision-link">{esc(label)} →</span></a>')
    if not P:
        return '<div class="brief-empty">No high or medium priority findings in the current model. <a href="/pages/risk.html">Review all checks →</a></div>'
    return ''.join(P)


def _deploy_plan(m):
    """A concrete allocation comparison for the incoming powder: the book now,
    versus after the inflow lands, its tax is reserved, and the net is deployed
    into the marketable sleeves. No target weights required — it shows what
    placing the cash actually does to the mix, and points to the Growth
    calculator to steer it deliberately."""
    assets, tax = m["assets"], m["tax"]
    A, NW = m["A"], m["NW"]
    pending = sum(s["value"] for s in assets if s["category"] == "cash_pending")
    if pending <= 0:
        return ""
    eta = m["eta"]
    net_tax = tax_funding(m)["pending"]
    deployable = pending_deployable(m)
    cash_now = sum(s["value"] for s in assets if s["category"] == "cash")
    cash_now = max(cash_now, 0)                          # a settled debit isn't dry powder
    MK = ("public_equity", "direct_index", "single_name_equity",
          "municipal_credit", "fixed_income", "alpha_market_neutral")
    marketable = sum(s["value"] for s in assets if s["category"] in MK)
    marketable_after = marketable + deployable
    # dry-cash share of the investable pool — falls as the powder is placed; stays
    # 0–100% (net worth as a denominator can exceed 100% once debt nets out).
    investable_now = cash_now + pending + marketable
    investable_after = cash_now + marketable_after
    dry_now = (cash_now + pending) / investable_now * 100 if investable_now else 0
    dry_after = cash_now / investable_after * 100 if investable_after else 0

    def row(label, now, after, coral=False, strong=False):
        nb = f'<b>{_fmt(now)}</b>' if strong else (_fmt(now) if now else "—")
        col = 'color:var(--coral)' if coral else ''
        ab = f'<b style="{col}">{_fmt(after)}</b>'
        return (f'<div class="cmprow"><span class="g">{esc(label)}</span>'
                f'<span class="cnow">{nb}</span><span class="arw">→</span>'
                f'<span class="caft">{ab}</span></div>')

    tax_note = (f' The inflow reserves {_fmt(net_tax)} for tax ({tax["char"].upper()} @ '
                f'{tax["rate"]*100:.1f}%, less {_fmt(tax["offset"])} harvested) before anything is placed.'
                if net_tax > 0 else "")
    P = ['<details class="explore" id="deploy-plan"><summary>Deploy plan — place the incoming '
         f'{_fmt(pending)}</summary>',
         '<div class="deploycmp">',
         '<style>.deploycmp .cmprow{display:grid;grid-template-columns:1fr auto 18px auto;align-items:baseline;'
         'gap:10px;padding:7px 0;border-bottom:1px solid var(--line);font-size:13px}'
         '.deploycmp .cnow,.deploycmp .caft{font-family:ui-monospace,Menlo,monospace;text-align:right;min-width:88px}'
         '.deploycmp .cnow{color:var(--dim)} .deploycmp .arw{color:var(--dim);text-align:center}'
         '.deploycmp .cmphd{display:grid;grid-template-columns:1fr auto 18px auto;gap:10px;font-size:10.5px;'
         'text-transform:uppercase;letter-spacing:.07em;color:var(--dim);padding-bottom:4px}'
         '.deploycmp .cmphd .r{text-align:right;min-width:88px}</style>',
         f'<p class="mnote">What placing the {eta} inflow does to the book — the cash lands, its tax is '
         f'reserved, and the {_fmt(deployable)} net is invested. Shares are of net worth.{tax_note}</p>',
         '<div class="cmphd"><span>Line</span><span class="r">Now</span><span></span><span class="r">Deployed</span></div>',
         row(f"Incoming cash ({eta})", pending, 0.0),
         (row("less: tax reserve", 0.0, -net_tax, coral=True) if net_tax > 0 else ""),
         row("Cash available now", cash_now, cash_now),
         row("Marketable, invested", marketable, marketable_after, strong=True),
         f'<div class="cmprow"><span class="g"><b>Dry cash, share of investable assets</b></span>'
         f'<span class="cnow">{dry_now:.0f}%</span><span class="arw">→</span>'
         f'<span class="caft"><b>{dry_after:.0f}%</b></span></div>',
         '</div>',
         '<p class="note">This holds your current mix (pro-rata into what you already own). To place it '
         'to a deliberate target instead — more bonds, an index hedge, a new sleeve — '
         '<a href="/pages/growth.html">steer the mix in the Growth calculator →</a> or set sleeve targets '
         'below, then the plan rebalances toward them.</p>',
         '</details>']
    return "".join(p for p in P if p)


def render_office(m, now=None, goals_endpoint=None, assets_endpoint=None, chat=False):
    d, factors, sleeves = m["d"], m["factors"], m["sleeves"]
    assets, liabs = m["assets"], m["liabs"]
    A, L, NW, agg = m["A"], m["L"], m["NW"], m["agg"]
    tax = m["tax"]
    pending_tax = tax_funding(m)["pending"]
    pnames, pshorts, pbeta, pidx = m["pnames"], m["pshorts"], m["pbeta"], m["pidx"]
    eta = m["eta"]
    owner = d.get("owner", {}).get("first_name")
    hello = f"{_greeting(now)}, {owner}." if owner else f"{_greeting(now)}."
    catmap = catmap_for(d)
    off = d.get("office") or {}
    cash_now = sum(s["value"] for s in assets if s["category"] == "cash")
    cash_label, cash_detail = "Cash available now", "Cash and money market balances"
    if d.get("commitments"):
        from officekit.commitments import cash_calendar
        cal = cash_calendar(m)
        cash_label = "Cash today"
        cash_detail = f'<a href="/pages/capital.html">{_fmt(cal["available"])} unreserved after planned obligations →</a>'
    pending = sum(s["value"] for s in assets if s["category"] == "cash_pending")
    marketable = sum(s["value"] for s in assets if s["category"] in ("public_equity", "direct_index", "single_name_equity", "municipal_credit", "fixed_income", "alpha_market_neutral"))
    expected_net = pending_deployable(m)
    liquid = cash_now + pending
    invested = A - cash_now - pending

    # allocation by category (of gross assets)
    catsum = {}
    for s in assets:
        catsum[s["category"]] = catsum.get(s["category"], 0) + s["value"]
    segs = []
    for cat, val in sorted(catsum.items(), key=lambda kv: -kv[1]):
        label, hexc = catmap.get(cat, (cat, "#6b7684"))
        segs.append((label, val, hexc))

    note_tail = off.get("liquidity_note_tail",
                        "New capital and rebalancing are the levers here; the Scenario Planner stresses exactly this balance sheet.")

    # data-freshness header line (only when the sync layer touched sleeves)
    sync_line = ""
    if m.get("sync_n"):
        color = "#e0736a" if m["sync_stale"] else "#35c98f"
        plural = "s" if m["sync_n"] != 1 else ""
        stale_txt = f", {m['sync_stale']} STALE" if m["sync_stale"] else ""
        sync_line = (f' <span style="color:{color}">· {m["sync_n"]} sleeve{plural}'
                     f' live-synced{stale_txt}</span>')

    tbd_count = sum(s.get("_confidence") == "tbd" for s in sleeves)
    if tbd_count:
        sync_line += f' · <span style="color:#eccb8a">{tbd_count} TBD valuation(s) to confirm</span>'

    # ==================================================================
    # Panels assembled as self-contained strings, then placed top-down:
    # daily decisions lead; editors and technical details disclose on demand.
    # Tenant-authored opportunity notes remain available as their own section.
    # ==================================================================
    office_notes = ('<details class="explore"><summary>Office notes &amp; opportunities</summary>' + _opportunities(m) + '</details>'
                    if d.get("opportunities") else '')
    goals_panel_html = _goals_panel(m, d, assets, sleeves, cash_now, goals_endpoint, chat,
                                    assets_endpoint=assets_endpoint)
    deploy_plan_html = _deploy_plan(m)
    assets_panel_html = _assets_panel(assets_endpoint, chat)
    donut_panel_html = (f'<div class="panel"><div class="ph"><h3>Asset Allocation</h3>'
                        f'<span class="hint">of {_fmt(A)} gross · a rough shape, not the driver</span></div>'
                        f'{_donut(segs, _fmt(A), "Assets")}</div>')

    P = []
    P.append(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Family Office</title>
<style>
:root{{--bg:#0b0e12;--panel:#14181d;--panel2:#1a1f25;--line:#242a31;--ink:#e8ebee;--dim:#9aa4b0;
--emerald:#35c98f;--violet:#b1a5ff;--amber:#d9a441;--coral:#e0736a;--slate:#8a939e;--blue:#4f7cf0}}
*{{box-sizing:border-box}} body{{margin:0;background:#0b0e12}}
.wrap{{max-width:1240px;margin:0 auto;padding:24px 24px 90px;
font:14px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:var(--ink);background:var(--bg)}}
a{{color:inherit}}
/* header */
.hdr{{display:flex;justify-content:space-between;align-items:flex-start;gap:24px;flex-wrap:wrap;margin-bottom:22px}}
.hi h1{{font-size:25px;margin:0 0 3px;letter-spacing:-.02em;font-weight:650}}
.hi .sub{{color:var(--dim);font-size:13px;margin:0}}
.stats{{display:flex;gap:26px}}
.stat .l{{font-size:10.5px;color:var(--dim);text-transform:uppercase;letter-spacing:.09em}}
.stat .n{{font:660 22px/1.1 ui-monospace,Menlo,monospace;letter-spacing:-.02em;margin-top:3px}}
.stat .d{{font-size:11px;color:var(--dim);margin-top:3px}}
/* section head */
h2{{font-size:11.5px;text-transform:uppercase;letter-spacing:.13em;color:var(--dim);margin:26px 0 11px;font-weight:600}}
.panel{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px}}
.panel .ph{{display:flex;justify-content:space-between;align-items:center;margin:-2px 0 12px}}
.panel .ph h3{{font-size:14px;margin:0;font-weight:600;letter-spacing:-.01em}}
.panel .ph .hint{{font-size:11px;color:var(--dim)}}
/* two-col grids */
.g2{{display:grid;grid-template-columns:1.35fr 1fr;gap:14px;align-items:start}}
.g2b{{display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:start}}
@media(max-width:860px){{.g2,.g2b{{grid-template-columns:1fr}}}}
/* opportunity inbox */
.oppinbox{{display:flex;flex-direction:column}}
.opp{{display:flex;gap:12px;align-items:flex-start;padding:12px 2px;border-bottom:1px solid var(--line)}}
.opp:last-child{{border-bottom:0}}
.oppic{{width:34px;height:34px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:16px;flex:0 0 auto;background:var(--panel2)}}
.t-violet{{box-shadow:inset 0 0 0 1px rgba(177,165,255,.35)}} .t-emerald{{box-shadow:inset 0 0 0 1px rgba(53,201,143,.35)}}
.t-amber{{box-shadow:inset 0 0 0 1px rgba(217,164,65,.35)}} .t-slate{{box-shadow:inset 0 0 0 1px rgba(138,147,158,.30)}}
.oppmid{{flex:1;min-width:0}} .oppt{{font-weight:600;font-size:13.5px}}
.opps{{font-size:12px;color:var(--dim);margin-top:3px;line-height:1.45}}
.oppv{{font:600 13px ui-monospace,Menlo,monospace;color:var(--ink);white-space:nowrap;flex:0 0 auto;padding-top:1px}}
.chip{{font-size:9px;font-weight:700;letter-spacing:.06em;padding:2px 6px;border-radius:20px;vertical-align:middle;margin-left:5px}}
.c-violet{{color:#c3b8fb;background:rgba(177,165,255,.15)}} .c-emerald{{color:#8ee5c1;background:rgba(53,201,143,.15)}}
.c-amber{{color:#eccb8a;background:rgba(217,164,65,.15)}} .c-slate{{color:#b3bcc6;background:rgba(138,147,158,.15)}}
/* donut */
.donutwrap{{display:flex;gap:18px;align-items:center;flex-wrap:wrap}}
.donut{{position:relative;width:180px;height:180px;flex:0 0 auto}}
.dc{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}}
.dct{{font:660 19px ui-monospace,Menlo,monospace;letter-spacing:-.02em}} .dcb{{font-size:10.5px;color:var(--dim);text-transform:uppercase;letter-spacing:.08em;margin-top:2px}}
.legend{{flex:1;min-width:180px;display:flex;flex-direction:column;gap:7px}}
.lg{{display:flex;align-items:center;gap:8px;font-size:12px}}
.dot{{width:9px;height:9px;border-radius:3px;flex:0 0 auto}}
.lgn{{flex:1;color:var(--ink)}} .lgv{{color:var(--dim);font-family:ui-monospace,Menlo,monospace}}
.lgp{{width:44px;text-align:right;font-family:ui-monospace,Menlo,monospace;color:var(--ink);font-variant-numeric:tabular-nums}}
/* risk summary */
.rgrid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px}}
.rk{{background:var(--panel2);border:1px solid var(--line);border-radius:10px;padding:10px 12px}}
.rk .l{{font-size:10px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em}}
.rk .v{{font:660 17px ui-monospace,Menlo,monospace;margin-top:4px}} .rk .v.pos{{color:var(--emerald)}} .rk .v.neg{{color:var(--coral)}}
.rk .s{{font-size:10.5px;color:var(--dim);margin-top:2px}}
.note{{font-size:11.5px;color:var(--dim);margin-top:11px;line-height:1.5}}
/* liquidity */
.liqrow{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--line);font-size:13px}}
.liqrow:last-child{{border-bottom:0}} .liqrow b{{font-family:ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums}}
.liqrow .g{{color:var(--dim)}}
/* sleeve cards */
.cards{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}
@media(max-width:860px){{.cards{{grid-template-columns:1fr}}}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:15px 16px}}
.card.liab{{border-left:3px solid var(--coral)}} .card.pending{{border-left:3px dashed var(--amber)}}
.card .nm{{font-weight:600;font-size:14.5px}} .card .val{{float:right;font:660 14px ui-monospace,Menlo,monospace}}
.card .tbd{{font-size:9px;color:var(--amber);border:1px solid var(--amber);border-radius:10px;padding:0 5px;margin-left:6px;vertical-align:middle}}
.curr{{font-size:12.5px;margin:9px 0 6px;color:var(--dim)}} .curr b{{color:var(--ink);font-family:ui-monospace,Menlo,monospace}}
.bar{{height:6px;background:#0c0f13;border-radius:4px;overflow:hidden;margin:5px 0 9px;position:relative}}
.bar .cur{{height:100%;background:var(--emerald)}} .bar .tgt{{position:absolute;top:-2px;bottom:-2px;width:2px;background:var(--amber)}}
.gap{{font-size:11px}} .gap.under{{color:var(--amber)}} .gap.over{{color:var(--coral)}} .gap.ok{{color:var(--emerald)}}
.risks{{font-size:11.5px;color:var(--dim);margin:6px 0}} .risks b{{color:var(--ink)}}
.betaline{{font-size:11.5px;color:var(--dim);font-family:ui-monospace,Menlo,monospace;margin-top:4px}}
.betaline .pos{{color:var(--emerald)}} .betaline .neg{{color:var(--coral)}}
/* matrix */
.mnote{{font-size:11.5px;color:var(--dim);margin:-4px 0 10px;line-height:1.5;max-width:900px}}
.mnote b{{color:var(--ink)}}
.mtxwrap{{padding:6px 8px 8px;overflow-x:auto}}
table.mtx{{width:100%;border-collapse:collapse;font-size:12px;margin-top:4px}}
table.mtx.xa{{min-width:960px}}
.mtx th{{text-align:center;color:var(--dim);font-size:10px;text-transform:uppercase;letter-spacing:.04em;padding:6px 5px;border-bottom:1px solid var(--line);white-space:nowrap}}
.mtx th.l,.mtx td.l{{text-align:left;font-weight:600;color:var(--ink);white-space:nowrap}}
.mtx td{{text-align:center;padding:7px 6px;border:1px solid var(--bg);font-family:ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums}}
.mtx .sticky{{position:sticky;left:0;background:var(--panel);z-index:1}}
.mtx th.sticky{{background:var(--panel)}}
/* lanes */
.lanes{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
@media(max-width:860px){{.lanes{{grid-template-columns:1fr}}}}
.lane{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 17px}}
.lane .ic{{font-size:20px}} .lane h3{{font-size:14px;margin:7px 0 6px;font-weight:600}}
.lane p{{font-size:12px;color:var(--dim);margin:0 0 9px;line-height:1.5}}
.lane .run{{font:600 11px ui-monospace,Menlo,monospace;color:var(--emerald)}}
.foot{{font-size:11px;color:var(--dim);margin-top:26px;line-height:1.6;border-top:1px solid var(--line);padding-top:14px}}

a:focus-visible,button:focus-visible,summary:focus-visible{{outline:2px solid var(--emerald);outline-offset:4px}}
.hdr{{margin-bottom:20px}} .hi h1{{font-size:32px;letter-spacing:-.035em}} .eyebrow{{color:var(--emerald);font-size:11px;letter-spacing:.15em;text-transform:uppercase;margin-bottom:8px}}
.stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:14px;overflow:hidden;margin:22px 0}}
.stat{{background:var(--panel);padding:20px}} .stat .n{{font-size:27px;margin:9px 0 7px}} .stat .d{{line-height:1.5}}
.section-head{{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin:28px 0 12px}} .section-head h2{{font-size:18px;letter-spacing:-.02em;text-transform:none;color:var(--ink);margin:0}} .section-head a{{font-size:12px;color:var(--emerald)}}
.decisions{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-bottom:24px}}
.decision{{display:flex;flex-direction:column;gap:10px;text-decoration:none;background:linear-gradient(145deg,#1c2329,#14181d);border:1px solid #343d45;border-radius:14px;padding:20px;transition:border-color .15s}}
.decision:hover{{border-color:var(--emerald)}} .decision-priority{{font-size:10px;color:#eccb8a;text-transform:uppercase;letter-spacing:.09em}} .decision strong{{font-size:16px;line-height:1.4}} .decision-copy{{font-size:12px;line-height:1.6;color:var(--dim)}} .decision-link{{font-size:12px;color:var(--emerald);margin-top:auto;padding-top:5px}}
.goalrow{{display:flex;gap:12px;align-items:center;margin-top:14px;padding-top:14px;border-top:1px solid var(--line)}} .goalrow>div:first-child{{flex:1;min-width:0}} .goal-title{{font-size:16px;font-weight:600}} .goal-target{{font-size:12px;color:var(--dim);margin-top:3px}} .goal-status{{font-size:11px;font-weight:600}}
.goal-measures{{display:flex;gap:10px;flex-wrap:wrap;margin:10px 0}} .goal-measures span{{padding:8px 11px;background:var(--panel2);border-radius:8px;font-size:12px;color:var(--dim)}} .goal-measures b{{color:var(--ink)}} .goal-detail{{font-size:12px;color:var(--dim);margin:8px 0}}
.entry-tools{{border-top:1px solid var(--line);margin-top:16px;padding-top:14px}} .entry-tools>summary{{cursor:pointer;color:var(--emerald);font-weight:600;font-size:12px}} .entry-tools[open]>summary{{margin-bottom:14px}}
.explore{{border:1px solid var(--line);border-radius:14px;padding:18px;margin-top:22px}} .explore>summary{{cursor:pointer;font-size:14px;font-weight:600}} .explore[open]>summary{{margin-bottom:18px}}
.panel .ph{{gap:12px;flex-wrap:wrap}} .cards .nm{{overflow-wrap:anywhere}}
@media(max-width:700px){{.wrap{{padding:22px 16px 60px}} .stats{{grid-template-columns:repeat(2,minmax(0,1fr))}} .stat{{padding:15px}} .stat .n{{font-size:23px}} .decisions{{grid-template-columns:1fr}} .hi h1{{font-size:27px}} .goalrow{{flex-wrap:wrap}} .goal-status{{margin-left:auto}} .liqrow{{gap:10px}} .entry-tools .grow4{{grid-template-columns:1fr 1fr}}}}
</style></head><body>
<div class="wrap">
  <div class="hdr"><div class="hi">
    <div class="eyebrow">Your family office</div><h1 id="office-greeting" data-owner="{esc(owner or "")}">{esc(hello)}</h1>
    <p class="sub">What needs your attention, and what your capital can support.</p>
    <p class="sub" style="margin-top:8px">Balance sheet as of {esc(d.get('as_of'))}{sync_line} · <a href="/pages/imports.html">Review sources</a></p>
  </div></div>
  <div class="stats">
    <div class="stat"><div class="l">Net worth</div><div class="n">{_fmt(NW)}</div><div class="d">Assets less liabilities · includes estimates</div></div>
    <div class="stat"><div class="l">{cash_label}</div><div class="n">{_fmt(cash_now)}</div><div class="d">{cash_detail}</div></div>
    <div class="stat"><div class="l">Marketable investments</div><div class="n">{_fmt(marketable)}</div><div class="d">Sale required · value can change</div></div>
    <div class="stat"><div class="l">Expected inflows, net</div><div class="n">{_fmt(expected_net)}</div><div class="d">{_fmt(pending)} gross · {esc(eta)} · not yet available</div></div>
  </div>
  <div class="section-head"><h2>Decisions &amp; attention</h2><a href="/pages/risk.html">All risk checks →</a></div>
  <div class="decisions">{_decision_brief(m)}</div>
{deploy_plan_html}
{goals_panel_html}
{office_notes}
  <details class="explore" id="add-asset"><summary>＋ Add assets or update the balance sheet</summary>{assets_panel_html}<a href="/pages/imports.html">Import a statement or refresh a connection →</a></details>
  <details class="explore" id="risk-model"><summary>Risk &amp; liquidity details</summary>
  <div class="g2b">
    <div class="panel">
      <div class="ph"><h3>Risk Summary — household factor beta</h3><span class="hint">net-worth-weighted</span></div>
      <div class="rgrid">""")
    # Risk summary: the aggregate factor betas as stat tiles (our differentiator)
    for f in factors:
        b = agg[f]
        cls = "pos" if b > 0.02 else "neg" if b < -0.02 else ""
        P.append(f'<div class="rk"><div class="l">{esc(f)}</div><div class="v {cls}">{b:+.2f}</div>'
                 f'<div class="s">β to household</div></div>')
    P.append(f"""</div>
      <div class="note">This is your <b>true</b> exposure once every sleeve is stacked — e.g. a +1% S&amp;P move ≈ {agg[factors[0]]*100:+.1f}bp on net worth.
      Realized Sharpe / vol / α are <b>suppressed until n≥20</b> closed trades (tearsheet rule); these are modeled factor betas, first-pass estimates to refine from returns.</div>
    </div>
    <div class="panel">
      <div class="ph"><h3>Cash &amp; Liquidity</h3><span class="hint">runway &amp; dry powder</span></div>
      <div class="liqrow"><span class="g">Available now (cash / MMF)</span><b>{_fmt(cash_now)}</b></div>
      <div class="liqrow"><span class="g">Incoming — {eta} dry powder (gross)</span><b>{_fmt(pending)}</b></div>
      {f'<div class="liqrow"><span class="g">less: tax reserve on inflow (est., {tax["char"].upper()})</span><b style="color:var(--coral)">{_fmt(-pending_tax)}</b></div>' if pending > 0 and pending_tax > 0 else ''}
      {f'<div class="liqrow"><span class="g"><b>= Net deployable ({eta}, after tax)</b></span><b>{_fmt(pending_deployable(m))}</b></div>' if pending > 0 and pending_tax > 0 else ''}
      <div class="liqrow"><span class="g">Invested (at risk)</span><b>{_fmt(invested)}</b></div>
      <div class="liqrow"><span class="g">Illiquid (venture + real estate)</span><b>{_fmt(sum(s['value'] for s in assets if s['category'] in ('venture_private','real_estate')))}</b></div>
      <div class="liqrow"><span class="g">Total liabilities</span><b style="color:var(--coral)">{_fmt(L)}</b></div>
      <div class="note">{f'The {eta} inflow is <b>{_fmt(pending)} gross → {_fmt(pending_deployable(m))} net</b> after an est. {_fmt(pending_tax)} tax reserve ({tax["char"].upper()} @ {tax["rate"]*100:.1f}%, less {_fmt(tax["offset"])} harvest). ' if pending > 0 and pending_tax > 0 else ''}{note_tail}</div>
    </div>
  </div></details>
""")

    # ---- SLEEVE CARDS ----
    def card(s):
        cur_pct = s["value"] / NW * 100 if NW else 0
        tgt = s.get("target_pct")
        kindcls = "liab" if s["kind"] == "liability" else ("pending" if s["category"].endswith("pending") else "")
        conf = s.get("_confidence")
        tbd = ('<span class="tbd">TBD</span>' if conf == "tbd"
               else '<span class="tbd" style="color:var(--violet);border-color:var(--violet)">EST</span>' if conf == "assumption"
               else "")
        if tgt is not None:
            gap = cur_pct - tgt
            gcls = "under" if gap < -1 else "over" if gap > 1 else "ok"
            gtxt = f"{gap:+.0f}pp {'under' if gap<0 else 'over' if gap>0 else 'on'} target"
            curline = f'Current: <b>{cur_pct:.1f}%</b> of a <b>{tgt}%</b> target <span class="gap {gcls}">· {gtxt}</span>'
            barw = min(100, abs(cur_pct) / max(tgt, 1) * 100)
            bar = f'<div class="bar"><div class="cur" style="width:{barw:.0f}%"></div><div class="tgt" style="left:100%"></div></div>'
        else:
            curline = f'Current: <b>{cur_pct:.1f}%</b> of net worth <span class="gap">· no target</span>'
            bar = ""
        hold = f' <span class="tbd" style="color:var(--emerald);border-color:var(--emerald)">{len(s["holdings"])} positions</span>' if s.get("holdings") else ""
        # strategies are sleeves: a strategy-tagged sleeve wears its strategy key,
        # and adjudicated tickers (courted picks) are counted on the card
        strat = "".join(f' <span class="tbd" style="color:var(--blue);border-color:var(--blue)">{esc(t)}</span>'
                        for t in strategy_tags(s))
        if s.get("sync"):
            c = "var(--coral)" if s.get("_sync_stale") else "var(--emerald)"
            lbl = f'STALE · {esc(s["sync"].get("as_of"))}' if s.get("_sync_stale") else f'synced {esc(s["sync"].get("as_of"))}'
            strat += (f' <span class="tbd" style="color:{c};border-color:{c}" '
                      f'title="{esc(s["sync"].get("provenance", ""))}">{lbl}</span>')
        n_adj = sum(1 for h in s.get("holdings", []) if h.get("adjudication"))
        if n_adj:
            strat += f' <span class="tbd" style="color:var(--violet);border-color:var(--violet)">{n_adj} adjudicated</span>'
        betas = " · ".join(
            f'<span class="{"pos" if (s["beta"].get(f) or 0)>0 else "neg" if (s["beta"].get(f) or 0)<0 else ""}">{s["beta"].get(f,0):+.2f} {esc(f.replace(" 500",""))}</span>'
            for f in factors[:3])
        # cross-asset co-moves: this sleeve's strongest betas to OTHER sleeves
        i = pidx[s["name"]]
        others = sorted(((pbeta[i][j], j) for j in range(len(pnames)) if j != i), reverse=True)
        picks = [o for o in others[:2] if o[0] > 0.05] + [o for o in others[-1:] if o[0] < -0.05]
        comoves = " · ".join(
            f'<span class="{"pos" if b>0 else "neg"}">{b:+.2f} {esc(pshorts[j])}</span>' for b, j in picks
        ) or '<span style="color:var(--dim)">~independent</span>'
        return (f'<div class="card {kindcls}"><span class="val">{_fmt(s["value"])}</span>'
                f'<span class="nm">{esc(s["name"])}{tbd}{hold}{strat}</span>'
                f'<div class="curr">{curline}</div>{bar}'
                f'<div class="risks"><b>Risks:</b> {esc(", ".join(s.get("risks", [])))}</div>'
                f'<div class="betaline">Factor β: {betas}</div>'
                f'<div class="betaline">Co-moves: {comoves}</div></div>')

    P.append('<h2>Assets</h2><div class="cards">')
    for s in sorted(assets, key=lambda x: -x["value"]):
        P.append(card(s))
    P.append('</div>')
    if liabs:
        P.append('<h2>Liabilities</h2><div class="cards">')
        for s in liabs:
            P.append(card(s))
        P.append('</div>')

    # ---- ASSET ALLOCATION (demoted here, above the beta matrixes) ----
    P.append('<h2>Asset allocation</h2>' + donut_panel_html)

    # ---- CROSS-ASSET (SLEEVE x SLEEVE) BETA MATRIX ----
    n = len(sleeves)
    P.append('<details class="explore" id="factor-model"><summary>Explore the factor model</summary>')
    P.append('<h2>Cross-asset beta — how each sleeve moves with every other</h2>')
    P.append('<p class="mnote">Read a <b>row</b>: how that sleeve responds to a 1% move in each <b>column</b> driver. '
             'Betas are directional (A→B ≠ B→A) and model-derived from the factor loadings + a per-category '
             'idiosyncratic-variance model — first-pass estimates, not realized-return regressions.</p>')
    P.append('<div class="panel mtxwrap"><table class="mtx xa"><tr><th class="l sticky">responds to ↓ / driver →</th>')
    for j in range(n):
        P.append(f'<th title="{esc(pnames[j])}">{esc(pshorts[j])}</th>')
    P.append('</tr>')
    for i in range(n):
        P.append(f'<tr><td class="l sticky" title="{esc(pnames[i])}">{esc(pshorts[i])}</td>')
        for j in range(n):
            style, txt = _betacell(round(pbeta[i][j], 2))
            diag = ';font-weight:700;color:var(--ink)' if i == j else ''
            P.append(f'<td style="{style}{diag}">{txt}</td>')
        P.append('</tr>')
    P.append('</table></div>')

    # ---- UNDERLYING FACTOR LOADINGS (the model layer) ----
    P.append('<h2>Underlying factor loadings — the model that generates the pairwise betas</h2>'
             '<div class="panel mtxwrap"><table class="mtx"><tr><th class="l sticky">Sleeve</th>')
    for f in factors:
        P.append(f'<th>{esc(f.replace(" 500",""))}</th>')
    P.append('</tr>')
    for s in sleeves:
        P.append(f'<tr><td class="l sticky">{esc(s["_short"])}</td>')
        for f in factors:
            style, txt = _betacell(s["beta"].get(f))
            P.append(f'<td style="{style}">{txt}</td>')
        P.append('</tr>')
    P.append('<tr><td class="l sticky" style="border-top:2px solid var(--line)">◆ HOUSEHOLD (weighted)</td>')
    for f in factors:
        style, txt = _betacell(round(agg[f], 2))
        P.append(f'<td style="{style};border-top:2px solid var(--line);font-weight:700">{txt}</td>')
    P.append('</tr></table></div>')

    P.append('</details>')

    P.append(f'<div class="foot">Values marked <b>at cost / est.</b>; sleeves tagged <b>TBD</b> are placeholders to correct from statements, never fabricated as fact. '
             f'Betas are first-pass estimates to refine from realized returns. Read-only — this dashboard never places orders. '
             f'Net worth reflects {len(assets)} asset sleeves less {_fmt(-L)} liabilities.</div>')
    P.append("""<script>
(function(){
  function openHash(){
    var id;try{id=decodeURIComponent(location.hash.slice(1));}catch(e){return;}
    var target=document.getElementById(id);if(!target)return;
    for(var el=target;el;el=el.parentElement){if(el.tagName==='DETAILS')el.open=true;}
    target.scrollIntoView({block:'start'});
  }
  openHash();window.addEventListener('hashchange',openHash);
})();
</script>""")
    P.append("""<script>(function(){const e=document.getElementById('office-greeting');if(!e)return;const h=new Date().getHours(),g=h<12?'Good morning':h<18?'Good afternoon':'Good evening';e.textContent=g+(e.dataset.owner?', '+e.dataset.owner:'')+'.';})();</script>""")
    P.append('</div></body></html>')
    return "\n".join(P)
