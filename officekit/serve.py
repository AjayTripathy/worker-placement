"""serve — the Tier-0 local app: onboard in the browser, then live in the pages.

    python3 -m officekit.serve --dir ./office --port 8787

Cold start: a new office shows the public landing page; /start opens onboarding — name, a
brokerage-CSV upload, manual sleeves (home / mortgage / cash), income-as-an-asset,
an optional windfall, life goals, and the five risk-profile questions. Submit
runs the SAME intake funnel as the CLI wizard (officekit.intake.build_from_answers:
beta priors, validation, never fabricate), saves the folder (answers +
balance sheet + rendered pages), and lands in the APP SHELL — Office and
Scenario Planner tabs over the rendered pages, with a rebuild link.

stdlib-only (http.server + officekit.formdata), no accounts, no network calls: localhost is the
product surface, and the office folder stays the source of truth — the same
folder `officekit link` will one day upload to the hosted tier. READ-ONLY beyond
its own folder; never places orders.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import threading
from functools import wraps
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from officekit.runtime import hosted, credential

from officekit import (build_from_answers, build_model, render_office, render_scenarios,
                       render_strategies)

def _ai(folder=None, slot="intake"):
    """The intelligence plugin, iff installed AND the slot's BYOM provider can
    construct a client (models.json decides provider/model/key env-var;
    Anthropic + ANTHROPIC_API_KEY is only the zero-config default) — else None
    and every AI affordance simply doesn't render (INTELLIGENCE.md principle 1)."""
    if hosted():
        from officekit.runtime import credential
        if not credential("ANTHROPIC_API_KEY"):
            return None
    try:
        import officekit_ai
        return officekit_ai if officekit_ai.available(folder, slot) else None
    except ImportError:
        return None


STYLE = """
:root{--bg:#0b0e12;--panel:#14181d;--panel2:#1a1f25;--line:#242a31;--ink:#e8ebee;--dim:#9aa4b0;
--emerald:#35c98f;--violet:#b1a5ff;--amber:#d9a441;--coral:#e0736a}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.wrap{max-width:880px;margin:0 auto;padding:34px 24px 90px}
h1{font-size:25px;margin:0 0 4px;letter-spacing:-.02em} .sub{color:var(--dim);margin:0 0 26px}
h2{font-size:11.5px;text-transform:uppercase;letter-spacing:.13em;color:var(--dim);margin:26px 0 10px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin-bottom:14px}
label{display:block;font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em;margin:10px 0 4px}
input,select{width:100%;background:var(--panel2);color:var(--ink);border:1px solid var(--line);
border-radius:8px;padding:9px 11px;font:500 13.5px -apple-system,BlinkMacSystemFont,sans-serif}
input[type=file]{padding:7px}
.src-auto input,.src-auto select{border-left:3px solid var(--emerald)}
.src-manual input,.src-manual select{border-left:3px solid var(--amber)}
.row-liab select{border-left:3px solid var(--coral)}
.row-liab input[name=u_value]{color:var(--coral)}
.row-liab input[name=u_value]::after{content:" (subtracted)"}
.dz{border:2px dashed var(--line);border-radius:12px;padding:26px 18px;text-align:center;
cursor:pointer;color:var(--dim);transition:border-color .15s,background .15s;background:var(--panel2)}
.dz:hover{border-color:var(--violet)} .dz.over{border-color:var(--violet);background:#1f2530;color:var(--ink)}
.dz b{color:var(--ink)} input:focus,select:focus{outline:2px solid var(--violet);outline-offset:1px}
.row{display:grid;grid-template-columns:1.2fr 1fr 1fr .7fr 26px;gap:10px;align-items:center} .row3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
.rmrow{background:none;border:0;color:var(--coral);cursor:pointer;font-size:17px;line-height:1;padding:0;width:auto}
.rmrow:hover{color:#f0a8a1}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.chk{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--line);font-size:13.5px}
.chk:last-child{border-bottom:0} .chk input{width:auto}
.chk .why{color:var(--dim);font-size:12px}
button,.btn{background:var(--emerald);color:#08110d;border:0;border-radius:9px;padding:12px 22px;
font:700 14px -apple-system,BlinkMacSystemFont,sans-serif;cursor:pointer}
.btn2{background:var(--panel2);color:var(--ink);border:1px solid var(--line);font-weight:600}
.err{border:1px solid var(--coral);border-left:4px solid var(--coral);border-radius:10px;
padding:12px 14px;margin-bottom:16px;color:#f0a8a1;font-size:13px}
.note{font-size:11.5px;color:var(--dim);line-height:1.5;margin-top:8px}
.foot{font-size:11px;color:var(--dim);margin-top:26px;border-top:1px solid var(--line);padding-top:12px;line-height:1.6}
/* app shell */
.bar{display:flex;gap:8px;align-items:center;padding:10px 16px;background:var(--panel);border-bottom:1px solid var(--line);
position:sticky;top:0;z-index:5}
.tab{background:transparent;color:var(--dim);border:1px solid transparent;border-radius:8px;padding:7px 14px;
font:700 12.5px -apple-system,BlinkMacSystemFont,sans-serif;cursor:pointer;letter-spacing:.04em}
.tab.on{background:var(--panel2);color:var(--ink);border-color:var(--line)}
.brand{font:700 13px -apple-system,BlinkMacSystemFont,sans-serif;margin-right:10px;letter-spacing:.02em}
.brand span{color:var(--emerald)} .grow{flex:1}
.reb{color:var(--dim);font-size:12px;text-decoration:none} .reb:hover{color:var(--ink)}
iframe{width:100%;height:calc(100vh - 53px);border:0;background:var(--bg)}
"""

ONBOARD = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Worker Placement — put your capital to work</title>
<style>{style}</style></head><body><div class="wrap">
<h1>Worker Placement</h1>
<p class="sub">Put your capital to work — deliberately: every dollar is a worker you place into a strategy. Drop a statement, add what it can't see, set your goals. Nothing is fabricated — unknowns are tagged TBD, and every estimate says so.</p>
{err}
{settings_link}
{adapters}
{dropzone}
{key_form}
<form id="onboarding-form" method="POST" action="/onboard" enctype="multipart/form-data">
<h2>1 · Your holdings</h2><div class="panel" id="holdings">
  {import_totals}
  <div class="row"><label>Type</label><label>Ticker or name</label><label>Value ($; debts positive)</label><label>Rate % (debt)</label><label></label></div>
  <details id="hdet" {hold_open}><summary class="note" style="cursor:pointer;margin:4px 0">holdings rows \u2014 click to expand / collapse</summary>
  <div id="hrows">{u_rows}</div></details>
  <div class="row2" style="margin-top:10px">
    <button type="button" class="btn2" onclick="addURow()">+ add another</button>
    <div><label style="margin-top:0">Account label (for tickers)</label><input name="account" value="brokerage"></div>
  </div>
  <p class="note">Tickers are classified into sleeves (funds pooled by kind; a single stock ≥20% of the account splits out as concentrated); everything else is a sleeve as typed.
  Have a positions CSV export? <label style="display:inline;text-transform:none;letter-spacing:0">Upload it: <input type="file" name="positions_csv" accept=".csv" style="width:auto;display:inline"></label></p>
</div>
{chat}
<h2>2 · Your income, as an asset</h2><div class="panel">
  <div class="row3">
    <div><label>Annual income ($)</label><input name="income_annual" placeholder="280000"></div>
    <div><label>Years it keeps coming</label><input name="income_years" placeholder="20"></div>
    <div><label>Style</label><select name="income_style"><option value="">balanced</option>
      <option value="equity_linked">equity-linked (tech / startup comp)</option>
      <option value="stable">stable (tenure, government)</option></select></div>
  </div>
  <p class="note">Capitalized earnings become a sleeve with a beta like everything else — and unlock the income-shock scenario. Blank = skip.</p>
</div>
<h2>3 · Life goals</h2><div class="panel">
  <div class="row3">
    <div><label>Retire — date</label><input name="ret_date" placeholder="2052-01-01"></div>
    <div><label>Retire — spend/yr ($)</label><input name="ret_spend" placeholder="110000"></div>
    <div><label>Liquidity floor ($)</label><input name="floor_amount" placeholder="50000"></div>
  </div>
  <div class="row3" style="margin-top:10px"><label>Dated target — label</label><label>— when</label><label>— amount ($)</label></div>
  <div id="goals">
  <div class="row3">
    <input name="goal_label" placeholder="College fund"><input name="goal_date" placeholder="2040-09-01"><input name="goal_amount" placeholder="250000">
  </div>
  </div>
  <button type="button" class="btn2" onclick="addGoal()" style="margin-top:8px">+ another dated target</button>
  <div class="chk" style="margin-top:10px"><input type="checkbox" name="goal_taxharvest" value="1">
    <span>Harvest tax losses / tax-efficiency <span class="why">— an ongoing objective; offers a lot-level-harvesting strategy</span></span></div>
  <p class="note">The Scenario Planner re-scores every goal through each tail. Blank = skip.</p>
</div>
{goals_chat}
<details class="panel" style="padding:14px 20px"><summary style="cursor:pointer;font-weight:600;font-size:13px">Advanced — name, windfall, dated targets, risk profile <span class="why" style="color:var(--dim);font-weight:400">(defaults: accumulator — net buyer, unlevered, no premium selling)</span></summary>
  <div class="row2" style="margin-top:12px">
    <div><label>First name (for the greeting)</label><input name="owner" placeholder=""></div>
    <div><label>As-of date</label><input name="as_of" value="{today}"></div>
  </div>
  <div class="row" style="margin-top:8px"><div><label>Windfall — gross ($)</label><input name="wind_amount"></div>
    <div><label>— when (label)</label><input name="wind_eta" placeholder="Dec"></div>
    <div><label>— tax character</label><select name="wind_character"><option>ltcg</option><option>ordinary</option><option>return_of_capital</option></select></div>
    <div><label>— state</label><input name="wind_state" placeholder="CA" maxlength="2"></div></div>
  <p class="note" style="margin:4px 0 0">A capital gain is reserved for tax automatically — leave rate blank to use a conservative floor (23.8% federal + your state's top rate), or set an exact rate: <input name="wind_rate" placeholder="0.371" style="width:90px;display:inline;padding:4px 8px"></p>
  <p class="note" style="margin:6px 0 0">Capital-loss carryforward ($): <input name="loss_carryforward" placeholder="0" style="width:120px;display:inline;padding:4px 8px"> — banked losses that offset gains; tracked at face and valued as a deferred tax asset (rate × unused).</p>

  <div style="margin-top:12px">
  <div class="chk"><input type="checkbox" name="p_net_buyer" checked><div>Still adding savings most years <span class="why">— a net buyer of assets</span></div></div>
  <div class="chk"><input type="checkbox" name="p_uses_leverage"><div>Use margin / portfolio leverage</div></div>
  <div class="chk"><input type="checkbox" name="p_decumulating"><div>Drawing income from the portfolio <span class="why">— retired / decumulating</span></div></div>
  <div class="chk"><input type="checkbox" name="p_premium_selling_allowed"><div>Comfortable selling options premium <span class="why">— collars, covered calls</span></div></div>
  <div class="chk"><input type="checkbox" name="p_concentrated_low_basis"><div>Hold a large low-basis position you can't cheaply sell</div></div>
  </div>
</details>
<button type="submit" style="margin-top:14px">Build my office →</button>
<p id="draft-status" class="note" role="status" aria-live="polite"></p>
<div class="foot">Betas are category priors (first-pass estimates, refined from returns later). Read-only — this app never places orders. {storage_note}</div>
</form></div>
<script>
function addURow(){{
  var d=document.createElement('div'); d.className='row'; d.style.marginTop='8px';
  d.innerHTML='<select name="u_kind"><option value="">—</option>{cat_opts}</select>'+
    '<input name="u_name" placeholder="ticker or name"><input name="u_value" placeholder="$">'+
    '<input name="u_rate" placeholder="">'+
    '<button type="button" class="rmrow" title="remove row">&times;</button>';
  d.querySelector('.rmrow').addEventListener('click',function(){{removeURow(this);}});
  var h=document.getElementById('hrows');
  h.appendChild(d);
  document.getElementById('hdet').open=true;
  if(window.recomputeTyped)window.recomputeTyped();
}}
function removeURow(btn){{ var r=btn.closest('.row'); if(r)r.remove(); if(window.recomputeTyped)window.recomputeTyped(); document.getElementById('onboarding-form').dispatchEvent(new Event('input')); }}
function addGoal(){{
  var d=document.createElement('div'); d.className='row3'; d.style.marginTop='8px';
  d.innerHTML='<input name="goal_label" placeholder="label"><input name="goal_date" placeholder="YYYY-MM-DD">'+
    '<input name="goal_amount" placeholder="$">';
  document.getElementById('goals').appendChild(d);
}}
</script>{chat_js}{draft_js}</body></html>"""


def _server_draft_blob(folder):
    """Inject the on-disk draft (manual entries saved as they were typed) so the
    page restores server-side — robust across reloads, new tabs, even a different
    browser, unlike the localStorage-only fallback."""
    p = Path(folder) / "draft.json"
    try:
        raw = p.read_text()
        raw = json.dumps(json.loads(raw)).replace('<', '\\u003c')
        return f"<script>window.__OFFICEKIT_DRAFT__={raw};</script>"
    except Exception:
        return ""


# Auto-save typed onboarding entries (rows you type, income, goals, profile) to
# DISK as they're added (POST /draft) so a reload/new tab/other browser restores
# them — imports already survive in staging; this closes the gap for MANUAL rows
# (2026-09-07, after a mortgage was lost to a page reload more than once).
# Single-brace JS (passed as a format VALUE, not itself formatted).
_DRAFT_JS = """<script>
(function(){
  var KEY='officekit_draft_'+location.host+location.pathname;
  var form=document.getElementById('onboarding-form'); if(!form)return;
  var SCALARS=['owner','as_of','account','income_annual','income_years','income_style',
    'wind_amount','wind_eta','wind_character','wind_state','wind_rate','loss_carryforward','ret_date','ret_spend','floor_amount'];
  function typedRows(){
    var out=[];
    document.querySelectorAll('#hrows .row').forEach(function(r){
      if(r.classList.contains('src-auto')||r.classList.contains('src-manual'))return; // imports persist server-side
      var k=r.querySelector('[name=u_kind]'),n=r.querySelector('[name=u_name]'),
          v=r.querySelector('[name=u_value]'),rt=r.querySelector('[name=u_rate]');
      if(!k||!n)return;
      if((k.value||'')||(n.value||'')||(v&&v.value||'')) out.push([k.value,n.value,v?v.value:'',rt?rt.value:'']);
    });
    return out;
  }
  function collect(){
    var d={rows:typedRows(),scalars:{},goals:[],profile:{}};
    SCALARS.forEach(function(nm){var e=document.getElementsByName(nm)[0]; if(e)d.scalars[nm]=e.value;});
    var gl=document.getElementsByName('goal_label'),gd=document.getElementsByName('goal_date'),ga=document.getElementsByName('goal_amount');
    for(var i=0;i<gl.length;i++){ if(gl[i].value||ga[i]&&ga[i].value) d.goals.push([gl[i].value,gd[i]?gd[i].value:'',ga[i]?ga[i].value:'']); }
    document.querySelectorAll('[name^=p_]').forEach(function(e){ if(e.checked)d.profile[e.name]=1; });
    var th=document.getElementsByName('goal_taxharvest')[0]; if(th&&th.checked)d.taxharvest=1;
    return d;
  }
  var _t, pending=Promise.resolve(), dirty=false, leaving=false;
  var status=document.getElementById('draft-status');
  function persist(){
    clearTimeout(_t);
    if(!dirty)return pending;
    var d=collect(); dirty=false;
    pending=pending.catch(function(){}).then(async function(){
      status.textContent='Saving your progress…';
      try{
        var r=await fetch('/draft',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d),keepalive:true});
        if(!r.ok)throw new Error('Your progress could not be saved. Keep this page open; reload and review if another tab changed the office.');
        status.textContent='Progress saved.';
      }catch(e){dirty=true;status.textContent=e.message;throw e;}
    });
    return pending;
  }
  function save(){
    if(leaving)return;
    dirty=true;
    try{localStorage.setItem(KEY,JSON.stringify(collect()));}catch(e){}
    clearTimeout(_t);
    _t=setTimeout(function(){persist().catch(function(){});},400);
  }
  function restore(){
    var d=window.__OFFICEKIT_DRAFT__;         // server-side draft (authoritative)
    if(!d){ var raw; try{raw=localStorage.getItem(KEY);}catch(e){return;} if(!raw)return;
            try{d=JSON.parse(raw);}catch(e){return;} }
    (d.rows||[]).forEach(function(row){
      addURow();
      var rows=document.querySelectorAll('#hrows .row'), r=rows[rows.length-1];
      r.querySelector('[name=u_kind]').value=row[0]||'';
      r.querySelector('[name=u_name]').value=row[1]||'';
      r.querySelector('[name=u_value]').value=row[2]||'';
      var rt=r.querySelector('[name=u_rate]'); if(rt)rt.value=row[3]||'';
    });
    Object.keys(d.scalars||{}).forEach(function(nm){var e=document.getElementsByName(nm)[0]; if(e&&SCALARS.indexOf(nm)>=0)e.value=d.scalars[nm];});
    (d.goals||[]).forEach(function(g,i){
      var gl=document.getElementsByName('goal_label');
      while(gl.length<=i){ addGoal(); gl=document.getElementsByName('goal_label'); }
      if(!gl[i].value)gl[i].value=g[0]||'';
      var gd=document.getElementsByName('goal_date'),ga=document.getElementsByName('goal_amount');
      if(gd[i]&&!gd[i].value)gd[i].value=g[1]||''; if(ga[i]&&!ga[i].value)ga[i].value=g[2]||'';
    });
    if(d.profile)document.querySelectorAll('[name^=p_]').forEach(function(e){e.checked=!!d.profile[e.name];});
    if(d.taxharvest){var th=document.getElementsByName('goal_taxharvest')[0]; if(th)th.checked=true;}
    if(window.recomputeTyped)window.recomputeTyped();
  }
  restore();
  form.addEventListener('input',save);
  window.officeDraftReady=async function(){clearTimeout(_t);await persist();if(window.officeRequestsIdle)await window.officeRequestsIdle();if(dirty)await persist();};
  // Flush before imports/builds navigate away; the hosted revision advances on
  // each saved draft. Resume the normal submit after its CSRF/revision update.
  document.addEventListener('submit',function(event){
    var target=event.target;
    if(target.dataset.draftReady==='yes'){leaving=true;clearTimeout(_t);if(target===form){try{localStorage.removeItem(KEY);}catch(e){}}return;}
    event.preventDefault();event.stopImmediatePropagation();
    var submitter=event.submitter;
    window.officeDraftReady().then(function(){
      target.dataset.draftReady='yes';
      target.querySelectorAll('button').forEach(function(b){b.disabled=false;});
      setTimeout(function(){target.requestSubmit(submitter||undefined);},0);
    }).catch(function(){});
  },true);
  document.addEventListener('click',function(event){
    var link=event.target.closest('a');if(!link||link.target==='_blank'||event.metaKey||event.ctrlKey)return;
    if(!dirty)return;
    event.preventDefault();window.officeDraftReady().then(function(){location.assign(link.href);}).catch(function(){});
  });
  window.addEventListener('beforeunload',function(event){if(dirty){event.preventDefault();event.returnValue='';}});
})();
</script>"""

# the AI-2 chat panel — rendered ONLY when the intelligence plugin is keyed.
# The agent fills the FORM, visibly; the human still clicks Build.
CHAT_PANEL = """<div class="panel" id="chatp">
  <div style="font-weight:700;font-size:13px;margin-bottom:2px">Or describe your assets <span style="color:var(--dim);font-weight:400">— the agent fills the table above; you review and build.</span></div>
  <div id="chatlog_assets" style="max-height:220px;overflow-y:auto;font-size:13px;line-height:1.5;margin:8px 0">{chat_first}</div>
  <div class="row2"><input id="chatin_assets" placeholder="e.g. about 400k at Fidelity mostly index funds, home worth 1.2M with a 480k mortgage…">
  <button type="button" class="btn2" onclick="chatSend('assets')">Send</button></div>
  <p class="note">Nothing is fabricated — approximate figures are tagged as assumptions on the page.</p>
</div>"""

GOALS_CHAT_PANEL = """<div class="panel" id="gchatp">
  <div style="font-weight:700;font-size:13px;margin-bottom:2px">Or describe your goals <span style="color:var(--dim);font-weight:400">— life plans are conversational; the agent fills the goal fields above.</span></div>
  <div id="chatlog_goals" style="max-height:220px;overflow-y:auto;font-size:13px;line-height:1.5;margin:8px 0"></div>
  <div class="row2"><input id="chatin_goals" placeholder="e.g. retire around 2050 on 120k a year, college for two kids, keep 50k cash…">
  <button type="button" class="btn2" onclick="chatSend('goals')">Send</button></div>
  <p class="note">Goals come only from your own words — never inferred from your statements.</p>
</div>"""

CHAT_JS = """<script>
var chats={assets:[],goals:[]};
function chatLine(scope,who,txt){var d=document.createElement('div');d.style.marginBottom='6px';
d.innerHTML='<b style="color:'+(who=='you'?'var(--emerald)':'var(--violet)')+'">'+who+'</b> '+
txt.replace(/&/g,'&amp;').replace(/</g,'&lt;');
var l=document.getElementById('chatlog_'+scope);l.appendChild(d);l.scrollTop=l.scrollHeight;}
function setV(n,v){var e=document.getElementsByName(n)[0];if(e&&v!=null&&v!=='')e.value=v;}
function fillArr(n,i,v){var es=document.getElementsByName(n);if(es[i]&&v!=null)es[i].value=v;}
function fillForm(a){if(!a)return;
 // assets-scoped: this chat NEVER touches the goals section
 if(a.owner)setV('owner',a.owner); if(a.as_of)setV('as_of',a.as_of);
 if(a.income){setV('income_annual',a.income.annual);setV('income_years',a.income.years);
   if(a.income.style)setV('income_style',a.income.style);}
 if(a.incoming){setV('wind_amount',a.incoming.amount);setV('wind_eta',a.incoming.eta);
   if(a.incoming.character)setV('wind_character',a.incoming.character);
   if(a.incoming.state)setV('wind_state',a.incoming.state);
   if(a.incoming.rate)setV('wind_rate',a.incoming.rate);}
 if(a.loss_carryforward)setV('loss_carryforward',a.loss_carryforward);
 if(a.profile)for(var k in a.profile){var e=document.getElementsByName('p_'+k)[0];
   if(e)e.checked=!!a.profile[k];}
 var sl=a.sleeves||[], rows=(a.positions&&a.positions.rows)||[];
 // NEVER overwrite imported rows: agent/typed data fills AFTER them (idempotent
 // within its own region across cumulative chat turns). 2026-09-06: filling from
 // index 0 silently clobbered the first imported position with an agent add.
 var imported=document.querySelectorAll('#hrows .row.src-auto, #hrows .row.src-manual').length;
 while(document.getElementsByName('u_kind').length<imported+sl.length+rows.length)addURow();
 var i=imported;
 sl.forEach(function(s){fillArr('u_kind',i,s.category);fillArr('u_name',i,s.name||'');
   fillArr('u_value',i,s.value);if(s.rate_pct)fillArr('u_rate',i,s.rate_pct);i++;});
 rows.forEach(function(r){fillArr('u_kind',i,'ticker');fillArr('u_name',i,r.symbol);
   fillArr('u_value',i,r.value);i++;});
 var det=document.getElementById('hdet'); if(det)det.open=true;   // reveal what was added
 if(window.recomputeTyped)window.recomputeTyped();}
function fillGoals(a){if(!a)return; var spendIdx=0;
 (a.goals||[]).forEach(function(g){
   if(g.kind=='retirement'){setV('ret_date',g.date);setV('ret_spend',g.annual_spending);}
   else if(g.kind=='liquidity_floor'){setV('floor_amount',g.amount);}
   else if(g.kind=='tax_efficiency'){var c=document.getElementsByName('goal_taxharvest')[0]; if(c)c.checked=true;}
   else{var i=spendIdx++;
     while(document.getElementsByName('goal_label').length<=i)addGoal();
     fillArr('goal_label',i,g.label);fillArr('goal_date',i,g.date);fillArr('goal_amount',i,g.amount);}});
 // a windfall mentioned in the goals chat is an ASSET — fill the assets-panel
 // windfall fields (2026-09-07 UX ruling: capture it, don't bounce to the other chat)
 if(a.incoming){setV('wind_amount',a.incoming.amount);setV('wind_eta',a.incoming.eta);
   if(a.incoming.character)setV('wind_character',a.incoming.character);
   if(a.incoming.state)setV('wind_state',a.incoming.state);}}
function chatSend(scope){var inp=document.getElementById('chatin_'+scope);var t=inp.value.trim();if(!t)return;
 inp.value='';chatLine(scope,'you',t);chats[scope].push({role:'user',content:t});
 Promise.resolve(window.officeDraftReady&&window.officeDraftReady()).then(function(){return fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({messages:chats[scope],scope:scope})});}).then(function(r){return r.json()})
 .then(function(t){if(t.error){chatLine(scope,'agent','(error: '+t.error+')');return;}
   chats[scope].push({role:'assistant',content:JSON.stringify(t)});
   chatLine(scope,'agent',t.reply||'');
   if(scope=='goals')fillGoals(t.answers);else fillForm(t.answers);
   var form=document.getElementById('onboarding-form');if(form)form.dispatchEvent(new Event('input'));})
 .catch(function(e){chatLine(scope,'agent','(request failed: '+e+')');});}
['assets','goals'].forEach(function(s){var e=document.getElementById('chatin_'+s);
 if(e)e.addEventListener('keydown',function(ev){if(ev.key=='Enter'){ev.preventDefault();chatSend(s);}});});
</script>"""

# the AI-1 confirmation step — suggestions are ACCEPTED by a human, never
# silently written. Unchecked = today's behavior (pooled individual stocks).
CONFIRM = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Worker Placement — confirm classifications</title>
<style>{style}</style></head><body><div class="wrap">
<h1>A few tickers we didn't recognize</h1>
<p class="sub">The classifier suggests these mappings. Confirm what's right — anything unchecked stays an individual stock, exactly as before. Confirmed mappings are remembered.</p>
<form method="POST" action="/onboard/confirm">
<div class="panel">{rows}</div>
<input type="hidden" name="answers_json" value="{answers_json}">
<button type="submit" style="margin-top:14px">Looks right — build my office →</button>
<div class="foot">Suggestions come from a small model and were frozen to your learning ledger before being shown. Nothing is applied without this confirmation.</div>
</form></div></body></html>"""

CATEGORIES = [("", "—"), ("cash", "Cash / money market"), ("public_equity", "Public equity funds"),
              ("single_name_equity", "Concentrated stock"), ("fixed_income", "Bonds"),
              ("municipal_credit", "Municipal bonds"), ("real_estate", "Real estate (home)"),
              ("real_estate_debt", "Mortgage / debt"), ("venture_private", "Venture / angel"),
              ("options_overlay", "Options / derivatives overlay"),
              ("alpha_market_neutral", "Alpha sleeve")]

_RESET_CONFIRM = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Worker Placement — start over?</title>
<style>{style}</style></head><body><div class="wrap">
<h1>Start over?</h1>
<p class="sub">This clears your built book, every staged import, and the rendered pages.
Your model key (models.json) is kept. This cannot be undone.</p>
<div style="display:flex;gap:10px">
<form method="POST" action="/reset"><button type="submit" style="background:var(--coral);color:#0b0e12">Yes, clear everything</button></form>
<a class="btn btn2" href="/" style="text-decoration:none;display:inline-block">Cancel</a>
</div></div></body></html>"""

APP = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Worker Placement — {owner}'s book</title>
<style>{style}</style>
<style>/* shell: a flex column so the iframe fills EXACTLY — no body scrollbar, no
  cut-off from a bar-height mismatch (2026-09-09) */
html,body{{height:100%;margin:0;overflow:hidden}}
body{{display:flex;flex-direction:column}}
.bar{{flex:0 0 auto;flex-wrap:wrap;gap:10px;padding:10px 20px}}
#pane{{flex:1 1 auto;width:100%;height:auto;border:0;display:block}}
.host-office{{color:#42dfb1;border:1px solid #31554a;border-radius:7px;padding:7px 10px;text-decoration:none;white-space:nowrap;font-size:12px}}
.workspace-nav{{display:flex;flex-wrap:wrap;gap:4px;order:1;flex-basis:100%;min-width:0}}
.tab{{padding:9px 12px;font-size:11px;white-space:nowrap;text-decoration:none;text-align:center}}
.tab:focus-visible,.host-office:focus-visible{{outline:2px solid #42dfb1;outline-offset:2px}}
.brand{{margin-right:auto}} .reb{{white-space:nowrap}}
#refresh-note{{padding:9px 16px;background:#2c2518;color:#edcc8a;font-size:12px}} #refresh-note button{{font-size:12px;padding:5px 10px;margin-left:10px}}
@media(max-width:600px){{.bar{{padding:10px 12px;gap:8px}} .brand{{font-size:13px}} .tab{{padding:8px 9px;font-size:10px}} .bar .reb{{font-size:11px}}}}
</style></head><body>
<div class="bar"><span class="brand">worker<span>placement</span></span>
  <nav class="workspace-nav" id="workspace-nav" aria-label="Workspace">
  <a class="tab on" id="t_office" href="#view=%2Fpages%2Foffice.html">OFFICE</a>
  <a class="tab" id="t_goals" href="#view=%2Fpages%2Fgoals.html">GOALS</a>
  <a class="tab" id="t_capital" href="#view=%2Fpages%2Fcapital.html">CAPITAL</a>
  <a class="tab" id="t_scenarios" href="#view=%2Fpages%2Fscenarios.html">SCENARIO PLANNER</a>
  <a class="tab" id="t_strategies" href="#view=%2Fpages%2Fstrategies.html">STRATEGIES</a>
  <a class="tab" id="t_growth" href="#view=%2Fpages%2Fgrowth.html">GROWTH</a>
  <a class="tab" id="t_harvest" href="#view=%2Fpages%2Fharvest.html">HARVEST</a>
  <a class="tab" id="t_risk" href="#view=%2Fpages%2Frisk.html">RISK OFFICER</a>
  <a class="tab" id="t_signals" href="#view=%2Fpages%2Fsignals.html">SIGNALS</a>
  <a class="tab" id="t_imports" href="#view=%2Fpages%2Fimports.html">IMPORTS</a>
  </nav><a class="host-office" href="/settings" target="_blank" rel="noopener">Office settings</a><a class="reb" href="/reset">start over</a></div>
<div id="refresh-note" role="status" hidden>Updated office data is available. Your unsaved edits are still here.<button type="button" onclick="reloadPane()">Reload page</button></div>
<iframe title="Office workspace" id="pane" src="/pages/office.html"></iframe>
<script>
var cur='office', pane=document.getElementById('pane'), dirty=false;
function viewPath(){{try{{var p=pane.contentWindow.location.pathname;var base=window.officeBase||'';if(base&&p.startsWith(base+'/'))p=p.slice(base.length);return p+pane.contentWindow.location.hash;}}catch(e){{return '/pages/office.html';}}}}
function validPath(p){{return /^\/pages\/[a-zA-Z0-9_.-]+\.html(?:#[^<>]*)?$/.test(p);}}
function fromHash(){{try{{var p=decodeURIComponent(location.hash.replace(/^#view=/,''));return validPath(p)?p:null;}}catch(e){{return null;}}}}
function navigate(p){{p=(window.officeBase||'')+p;try{{pane.contentWindow.location.replace(p);}}catch(e){{pane.src=p;}}}}
function show(k){{var p='/pages/'+k+'.html';if(!document.getElementById('t_'+k))return;history.pushState(null,'','#view='+encodeURIComponent(p));navigate(p);}}
function syncNav(){{
  var path=viewPath(),slug=path.split('/').pop().split('.html')[0];
  cur=document.getElementById('t_'+slug)?slug:slug.startsWith('goal_')?'goals':slug.startsWith('asset_')||slug.startsWith('deck_')||slug.startsWith('thesis_deck_')||slug.startsWith('proposal_')?'strategies':slug.startsWith('capability_')?'signals':slug.startsWith('import_')?'imports':cur;
  document.querySelectorAll('.tab').forEach(function(t){{var on=t.id==='t_'+cur;t.classList.toggle('on',on);if(on)t.setAttribute('aria-current','page');else t.removeAttribute('aria-current');}});
  if(validPath(path))history.replaceState(null,'','#view='+encodeURIComponent(path));
}}
pane.addEventListener('load',function(){{
  dirty=false;document.getElementById('refresh-note').hidden=true;syncNav();
  try{{pane.contentDocument.addEventListener('input',()=>dirty=true);pane.contentDocument.addEventListener('change',()=>dirty=true);pane.contentWindow.addEventListener('hashchange',syncNav);}}catch(e){{}}
}});
window.addEventListener('popstate',function(){{navigate(fromHash()||'/pages/office.html');}});
window.addEventListener('hashchange',function(){{var p=fromHash();if(p&&p!==viewPath())navigate(p);}});
var initial=fromHash();if(initial)navigate(initial);
function reloadPane(){{dirty=false;document.getElementById('refresh-note').hidden=true;var path=viewPath(),parts=path.split('#');navigate(parts[0]+'?v='+encodeURIComponent(_v)+(parts[1]?'#'+parts.slice(1).join('#'):''));}}
var _v=null;
setInterval(function(){{fetch('/state').then(r=>r.json()).then(function(s){{
  if(_v===null){{_v=s.v;return;}}if(s.v!==_v){{_v=s.v;if(dirty)document.getElementById('refresh-note').hidden=false;else reloadPane();}}
}}).catch(function(){{}});}},4000);
</script></body></html>"""


def _uopts():
    cats = [("ticker", "Ticker — classify for me")] + [c for c in CATEGORIES if c[0]]
    return "".join(f'<option value="{v}">{html.escape(t)}</option>' for v, t in cats)


def _urows_html(n=6, prefill=None):
    """Blank holdings rows, optionally preceded by rows pre-filled from an
    auto-adapter import (kind, name, value, rate). Pre-filled rows use the same
    names/positions so the aligned-array parser and the classifier see them
    exactly as if typed."""
    out = []
    for row_ in (prefill or []):
        kind, name, value, rate = row_[:4]
        cls = row_[4] if len(row_) > 4 else ""
        opts = f'<option value="">—</option>' + _uopts()
        opts = opts.replace(f'value="{kind}"', f'value="{kind}" selected', 1)
        out.append(f'<div class="row {cls}" style="margin-top:8px"><select name="u_kind">' + opts + '</select>'
                   f'<input name="u_name" value="{html.escape(str(name))}">'
                   f'<input name="u_value" value="{html.escape(str(value))}">'
                   f'<input name="u_rate" value="{html.escape(str(rate or ""))}">'
                   '<button type="button" class="rmrow" title="remove row" onclick="removeURow(this)">&times;</button></div>')
    row = ('<div class="row" style="margin-top:8px"><select name="u_kind"><option value="">—</option>'
           + _uopts() + '</select>'
           '<input name="u_name" placeholder="ticker or name"><input name="u_value" placeholder="$">'
           '<input name="u_rate" placeholder="">'
           '<button type="button" class="rmrow" title="remove row" onclick="removeURow(this)">&times;</button></div>')
    return "".join(out) + row * n


# ---- auto-adapters: scan for live broker connections on the onboarding page ----
_DISCOVERY_CACHE = {"ts": 0.0, "results": None}


def _discover_cached(max_age_s=90):
    if hosted():
        import officekit_adapters
        return officekit_adapters.discover(names=["alpaca", "ibkr_flex"])
    import time as _t
    if _DISCOVERY_CACHE["results"] is None or _t.time() - _DISCOVERY_CACHE["ts"] > max_age_s:
        try:
            import officekit_adapters
            _DISCOVERY_CACHE.update(ts=_t.time(), results=officekit_adapters.discover())
        except ImportError:
            _DISCOVERY_CACHE.update(ts=_t.time(), results=[])
    return _DISCOVERY_CACHE["results"]


def _adapters_html():
    """The detected-connections panel: found connections lead with one-click
    import; near-misses show their unlock guidance; silent absences stay silent."""
    results = _discover_cached() or []
    rows = []
    for r in results:
        if not (r["found"] or r["status"] in ("needs_key", "needs_dep")):
            continue                                 # silent absences stay silent
        act = ""
        if r["found"] and r["can_fetch"] and r["status"] == "ready":
            act = (f'<form method="POST" action="/adapter/import" style="margin:0" {_BUSY_ATTR}>'
                   f'<input type="hidden" name="adapter" value="{html.escape(r["name"])}">'
                   f'<button type="submit" style="padding:7px 14px">Import positions</button></form>')
        elif hosted():
            act = '<a class="btn btn2" href="/settings">Connect in Office settings</a>'
        elif r.get("guidance"):
            act = f'<span class="why">{html.escape(r["guidance"])}</span>'
        detail = 'Not connected to this office' if hosted() and not r['found'] else r['detail']
        rows.append('<div class="chk"><div style="flex:1"><b>' + html.escape(r["label"]) + "</b>"
                    f'<div class="why">{html.escape(detail)}</div></div>{act}</div>')
    # the AI model key is an integration too — it ALWAYS shows, independent of
    # whether any broker connection was detected (regression fix 2026-09-06:
    # the key display used to vanish whenever the gateway wasn't found)
    ks = _key_status()
    key_row = ('<div class="chk"><div style="flex:1"><b>AI model key</b>'
               f'<div class="why">{html.escape(ks["label"])}</div></div>'
               + ('<span class="why" style="color:var(--emerald)">attached ✓</span>'
                  if ks["attached"] else
                  '<span class="why" style="color:var(--amber)">needs attaching</span>')
               + '</div>')
    heading = 'Office connections — read-only' if hosted() else 'Detected connections — read-only scan of this machine'
    return ('<div class="panel"><label style="margin-top:0">' + heading + '</label>'
            + "".join(rows) + key_row + "</div>")


def detection_summary():
    """Plain-text summary of what the auto-adapter scan found and HOW — the
    same facts the panel shows, phrased for the chat (and for the intake
    agent's context, so it never re-asks for what the scan already knows)."""
    found = [r for r in (_discover_cached() or []) if r["found"]]
    if not found:
        return None
    return "; ".join(f"{r['label']} — {r['detail']}"
                     + (f" ({r['guidance']})" if r.get("guidance") and r["status"] != "ready" else "")
                     for r in found)


def chat_first_line(notice=None, via=None):
    """The wizard's OPENING line (principal-directed 2026-09-05): lead the
    conversation with what was auto-detected and how — or, post-import, with
    what was just pulled in and from where."""
    if notice:
        return (notice + (f" Pulled read-only from your {via}." if via else "")
                + " That look right? Tell me anything the connection can't see — "
                  "other accounts, your home, a mortgage, private holdings.")
    summary = detection_summary()
    if hosted():
        return ((f"Your office connections: {summary}. Click “Import positions” above, then " if summary else
                 "Connect a broker in Office settings, or ") +
                "drop a statement or describe your holdings. I’ll fill the table for you to review.")
    if summary:
        return (f"I scanned this machine (read-only) and auto-detected: {summary}. "
                "Click “Import positions” above and I’ll fill the table from it — "
                "then describe anything the connection can’t see or add statements below.")
    return ("I scanned this machine for live broker connections — IBKR TWS/Gateway, "
            "a Client Portal gateway, Alpaca keys, recent broker CSVs in Downloads — "
            "and found none. Describe your holdings (or upload a positions CSV above) "
            "and I’ll fill the table.")


def _chat_first_html(notice=None, via=None):
    return ('<div style="margin-bottom:6px"><b style="color:var(--violet)">agent</b> '
            + html.escape(chat_first_line(notice, via)) + "</div>")


def _key_ask_html(notice=None, via=None):
    """The keyless wizard panel (principal ruling 2026-09-05: onboarding never
    REQUIRES a key — the deterministic path runs in full, and the agents ASK
    for one). Leads with the same detection/import first line (key-free facts),
    then the ask. The key goes to the process environment — never into the
    office folder — and to ~/.anthropic_key only if the user opts in."""
    if hosted():
        return '<div class="panel"><p>Connect your AI key to enable chat, extraction and courts.</p><a class="btn" href="/settings" target="_top">Office settings</a></div>'
    first = chat_first_line(notice, via)
    ask = ("To enable the wizard chat and ticker auto-classification, paste an Anthropic "
           "API key. It stays on this machine — never in your Worker Placement folder.")
    return ('<div class="panel" id="chatp">'
            '<div style="font-weight:700;font-size:13px;margin-bottom:2px">Or describe your assets '
            '<span style="color:var(--dim);font-weight:400">— the wizard agent fills the table; '
            'it runs on your own model key.</span></div>'
            '<div style="max-height:220px;overflow-y:auto;font-size:13px;line-height:1.5;margin:8px 0">'
            '<div style="margin-bottom:6px"><b style="color:var(--violet)">agent</b> '
            + html.escape(first) + "</div>"
            '<div style="margin-bottom:6px"><b style="color:var(--violet)">agent</b> '
            + html.escape(ask) + "</div></div>"
            '<div class="row2"><input type="password" name="api_key" placeholder="sk-ant-…" '
            'form="intake-key" autocomplete="off" required>'
            '<button type="submit" form="intake-key" class="btn2">Enable agents</button></div>'
            '<div class="chk" style="border:0;padding:6px 0 0"><input type="checkbox" name="remember" value="1" form="intake-key">'
            '<span class="why">remember on this machine (~/.anthropic_key, chmod 600) — otherwise '
            'it lives only in this server process</span></div>'
            '<p class="note">Everything else — the connection scan, position import, the form, '
            'building your office — works without any key.</p></div>')


GOALS_KEYLESS_NOTE = ('<div class="panel"><p class="note" style="margin:0">The goals chat unlocks '
                      'with the model key above — the goal fields here work without it.</p></div>')


_BUSY_ATTR = "onsubmit=\"var b=this.querySelector('button[type=submit]')||this.querySelector('button');b.dataset.t=b.textContent;b.textContent='\u23f3 working\u2026';setTimeout(function(){b.disabled=true},0)\""


def _key_status(folder=None):
    if hosted():
        from officekit.runtime import credential
        attached = bool(credential("ANTHROPIC_API_KEY"))
        return {"attached": attached, "label": "Connected privately to this office" if attached else "Connect your AI key in Office settings"}
    """The AI key, treated as an INTEGRATION (principal 2026-09-05): tell the
    user where we imported it from, or that one needs attaching and how."""
    try:
        from officekit_ai.models import key_source
        src = key_source()
    except ImportError:
        return {"attached": False, "how": None,
                "label": "AI plugin not installed (pip install officekit[ai])"}
    if src and src.startswith("env:"):
        return {"attached": True, "how": src,
                "label": f"attached via the {src[4:]} environment variable"}
    if src:
        return {"attached": True, "how": src, "label": "imported from ~/.anthropic_key"}
    return {"attached": False, "how": None,
            "label": ("not attached — agents (chat, classification, extraction, courts) are "
                      "disabled. Attach one: paste it in the wizard panel below, or write it to "
                      "~/.anthropic_key, or export ANTHROPIC_API_KEY before launching")}


_DROPZONE_JS = """<script>
(function(){
  var dz=document.getElementById('dz'),inp=document.getElementById('dzinput'),
      cnt=document.getElementById('dzcount');
  if(!dz||!inp)return;
  var OK=/\\.(csv|pdf|png|jpe?g|gif|webp)$/i;
  function setCount(n,folders){cnt.textContent=n?(n+' file(s) ready'+(folders?' (folder scanned)':'')+
    ' \\u2014 click Read documents'):'';}
  dz.addEventListener('click',function(){inp.click();});
  inp.addEventListener('change',function(){setCount(inp.files.length,false);});
  ['dragenter','dragover'].forEach(function(e){dz.addEventListener(e,function(ev){
    ev.preventDefault();dz.classList.add('over');});});
  ['dragleave','dragend'].forEach(function(e){dz.addEventListener(e,function(ev){
    dz.classList.remove('over');});});
  dz.addEventListener('drop',function(ev){
    ev.preventDefault();dz.classList.remove('over');
    var items=ev.dataTransfer.items,sawFolder=false;
    if(items&&items.length&&items[0].webkitGetAsEntry){
      var entries=[];for(var i=0;i<items.length;i++){var e=items[i].webkitGetAsEntry();
        if(e){entries.push(e);if(e.isDirectory)sawFolder=true;}}
      walkAll(entries,[],function(files){commit(files,sawFolder);});
    }else{commit([].slice.call(ev.dataTransfer.files),false);}
  });
  function walkAll(entries,files,done){
    var pending=entries.length;if(!pending)return done(files);
    function fin(){if(--pending===0)done(files);}
    entries.forEach(function(entry){
      if(entry.isFile){entry.file(function(f){files.push(f);fin();},fin);}
      else if(entry.isDirectory){
        var reader=entry.createReader(),kids=[];
        (function read(){reader.readEntries(function(b){
          if(b.length){kids=kids.concat([].slice.call(b));read();}
          else{walkAll(kids,files,fin);}
        },fin);})();
      }else{fin();}
    });
  }
  function commit(files,sawFolder){
    files=files.filter(function(f){return OK.test(f.name);});
    var dt=new DataTransfer();files.forEach(function(f){dt.items.add(f);});
    inp.files=dt.files;setCount(files.length,sawFolder);
    if(!files.length)cnt.textContent='nothing readable in that drop (statements, screenshots or CSVs only)';
  }
})();
</script>"""


def _dropzone_html(folder=None, back=None):
    """Key-aware drop zone: screenshots are a first-class input, but pixels
    need the extract model — with no key attached, say exactly that and point
    at the key panel instead of failing after the upload. `back` (an import
    slug) makes the upload return to that import's detail page."""
    back_field = (f'<input type="hidden" name="back" value="{html.escape(back)}">' if back else "")
    ks = _key_status(folder)
    if ks["attached"]:
        note = ("CSVs are parsed exactly; <b>screenshots</b> and PDFs go to your extraction model "
                "(AI key " + html.escape(ks["label"]) + "), which must also read the document's own "
                "printed total — rows that don't reconcile are flagged, never smoothed.")
    else:
        note = ("CSVs are parsed exactly and work right now. <b>Screenshots and PDFs need an agent "
                "key first</b> — " + html.escape(ks["label"]) + ".")
    saved_note = ("Uploads are saved privately. Reconciled position data updates this office; review source warnings below."
                  if folder and (Path(folder) / "balance_sheet.json").exists() else
                  "Files are retained in this office for review. Build the office to apply the staged positions.")
    return ('<div class="panel">'
            '<form id="dzform" method="POST" action="/import/files" enctype="multipart/form-data" '
            + _BUSY_ATTR + '>' + back_field +
            '<label style="margin-top:0">Or add anything that shows your positions '
            '\u2014 statements, screenshots, exports</label>'
            '<div id="dz" class="dz">'
            '<div id="dzmsg"><b>Drag files or a folder here</b>, or click to choose files</div>'
            '<input id="dzinput" type="file" name="docs" multiple '
            'accept=".csv,.pdf,.png,.jpg,.jpeg,.gif,.webp" style="display:none"></div>'
            '<div class="row2" style="align-items:center;margin-top:10px">'
            '<div id="dzcount" class="note" style="margin:0"></div>'
            '<button type="submit" class="btn2">Read documents</button></div>'
            '<p class="note">' + note + ' Drag a whole folder and it\u2019s scanned recursively \u2014 '
            'statements, screenshots and CSVs are read, everything else is ignored. ' + saved_note + '</p>'
            '</form>' + _DROPZONE_JS + '</div>')


def import_files(folder, parts, on_error=None):
    """The per-file router (ratified 2026-09-05): deterministic first, model
    second. CSV -> the exact header-sniffing importer; PDF/images -> the
    `extract` slot through the reconciliation gate. Every file becomes a
    staged SOURCE (refresh=manual) with its as-of and warnings — re-uploading
    the same filename replaces that source, never stacks it."""
    from officekit import staging
    SUPPORTED = (".csv", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp")
    MODEL_CONCURRENCY = 12                            # extractions in flight at once
    results = []
    skipped = 0
    seen = set()
    docs = []
    for part in parts:
        # webkitdirectory sends filenames as relative paths ("statements/x.pdf");
        # keep the basename for the source id, dedupe repeats across both inputs
        name = Path(part.filename).name
        data = part.file.read()
        if not name or not data:
            continue
        if not name.lower().endswith(SUPPORTED):
            skipped += 1                             # folder junk — ignored, counted, not failed
            continue
        if name in seen:
            continue
        seen.add(name)
        from officekit.migration import inspect_document, safe_path
        import hashlib
        retained = "attachments/" + hashlib.sha256(name.encode()).hexdigest()[:16] + Path(name).suffix.lower()
        if not safe_path(retained):
            raise ValueError("Unsupported upload filename")
        inspect_document(retained, data)
        target = Path(folder) / retained
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        docs.append((name, data))

    def failed(name, error):
        from officekit.api_errors import message
        staging.record_failure(folder, 'upload:' + name, error)
        results.append(f"{name}: FAILED — {message(error)}")
        if on_error:
            on_error(name, error)

    csvs = [(n, d) for n, d in docs if n.lower().endswith(".csv")]
    model_docs = [(n, d) for n, d in docs if not n.lower().endswith(".csv")]

    # a pull to stage + a result line; kept on the MAIN thread so staging.json
    # (single JSON file) is never written concurrently
    pulls = []                                        # (name, kwargs, result_line)

    for name, data in csvs:                           # deterministic, cheap — inline
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
                tf.write(data)
            try:
                from officekit.importers import read_positions_csv
                rows = [{"symbol": r.get("symbol", ""), "qty": r.get("qty"),
                         "value": r.get("value") or 0, "description": r.get("description", ""),
                         "sec_type": "STK"} for r in read_positions_csv(Path(tf.name))]
            finally:
                Path(tf.name).unlink(missing_ok=True)
            pulls.append((f"upload:{name}",
                          dict(kind="upload", ref=name, rows=rows, refresh="manual",
                               detail="CSV — parsed exactly, no model"),
                          f"{name}: {len(rows)} rows (exact CSV parse)"))
        except Exception as e:
            failed(name, e)

    # extractions: send MODEL_CONCURRENCY at a time, self-managed queue — the
    # executor pulls the next document as each in-flight one finishes, so the
    # whole selection drains in one submission (no deferral onto the user).
    # extract_file is pure (no staging writes); each carries its own 90s timeout.
    if model_docs:
        import concurrent.futures
        from officekit_ai.extract import extract_file

        def _do(nd):
            name, data = nd
            out = extract_file(name, data, folder=folder)
            # tag rows with the statement's OWN account so re-uploading the same
            # account under a different filename dedupes instead of double-counting
            # (extract rows otherwise have no account and bypass dedupe, 2026-09-06)
            acct = (out.get("account_label") or "").strip() or None
            rows = [{"symbol": r.get("symbol") or "", "qty": r.get("qty"),
                     "value": r.get("value") or 0, "description": r.get("description", ""),
                     "confidence": r.get("confidence"), "sec_type": "STK",
                     "ccy": out.get("currency") or "USD", "account": acct}
                    for r in out.get("rows") or []]
            return name, out, rows

        workers = min(MODEL_CONCURRENCY, len(model_docs))
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            from contextvars import copy_context
            futs = {ex.submit(copy_context().run, _do, nd): nd[0] for nd in model_docs}
            for fut in concurrent.futures.as_completed(futs):
                name = futs[fut]
                try:
                    name, out, rows = fut.result()
                    w = f"; {len(out['warnings'])} warning(s)" if out.get("warnings") else ""
                    pulls.append((f"upload:{name}",
                                  dict(kind="upload", ref=name, rows=rows, refresh="manual",
                                       as_of=out.get("as_of"), stated_total=out.get("stated_total"),
                                       warnings=out.get("warnings"), detail=out.get("account_label", "")),
                                  f"{name}: {len(rows)} rows via extraction "
                                  f"({out.get('account_label', '?')}, as-of {out.get('as_of') or '?'}{w})"))
                except Exception as e:
                    failed(name, e)

    for sid, kw, line in pulls:                       # serialized staging writes
        staging.record_pull(folder, sid, **kw)
        results.append(line)

    if skipped:
        results.append(f"ignored {skipped} unsupported file(s) in the selection")
    if not results:
        results.append("no readable statements/screenshots/CSVs in the selection")
    return results


def _import_totals_html(folder):
    """Totals by import source — a verification block at the top of the holdings
    section (principal-directed 2026-09-06): each import's own total, so a user
    checks it against the statement it came from before building. Reads the
    staged union so it reflects the deduped, merge-corrected numbers."""
    from officekit import staging
    from officekit.staging import num
    rows, _ = staging.merged_rows(folder)
    KIND = {"adapter": "live connection", "upload": "uploaded document",
            "proposed": "court-proposed", "manual": "typed"}
    agg = {}
    for r in rows:
        sid = r.get("source_id", "typed")
        a = agg.setdefault(sid, {"kind": r.get("source_kind", "manual"), "n": 0, "v": 0.0,
                                 "refresh": r.get("refresh", "manual")})
        a["n"] += 1
        a["v"] += num(r.get("value"))
    body = []
    for sid, a in sorted(agg.items(), key=lambda kv: -abs(kv[1]["v"])):
        label = sid.split(":", 1)[1] if ":" in sid else sid
        cls = "src-auto" if a["refresh"] == "auto" else "src-manual"
        rm = ("" if sid == "typed" else
              f'<form method="POST" action="/import/remove" style="margin:0" '
              f'onsubmit="return confirm(\'Remove this import and its {a["n"]} position(s)?\')">'
              f'<input type="hidden" name="source_id" value="{html.escape(sid)}">'
              f'<button type="submit" title="remove this import" '
              f'style="background:none;border:0;color:var(--coral);cursor:pointer;'
              f'font-size:15px;line-height:1;padding:0 4px">&times;</button></form>')
        body.append(
            f'<tr class="{cls}"><td>{html.escape(label)}</td>'
            f'<td class="sub">{html.escape(KIND.get(a["kind"], a["kind"]))}</td>'
            f'<td style="text-align:right" class="mono">{a["n"]}</td>'
            f'<td style="text-align:right" class="mono">${a["v"]:,.0f}</td>'
            f'<td style="text-align:center">{rm}</td></tr>')
    grand = sum(a["v"] for a in agg.values())
    n_staged = sum(a["n"] for a in agg.values())
    # a "typed / added here" row + grand total, both updated live from the form
    # (agent-chat and manual rows never touch staging, so JS is the only way to
    # count them into the verification block, 2026-09-06)
    return (f'<div id="imptot" data-staged-v="{grand}" data-staged-n="{n_staged}" '
            'style="margin-bottom:12px"><label style="margin-top:0">Totals by source '
            '— check each against its statement</label>'
            '<table style="width:100%;border-collapse:collapse;font-size:12.5px">'
            '<tr style="color:var(--dim)"><th style="text-align:left;padding:4px 6px">source</th>'
            '<th style="text-align:left;padding:4px 6px">type</th>'
            '<th style="text-align:right;padding:4px 6px">positions</th>'
            '<th style="text-align:right;padding:4px 6px">total</th><th></th></tr>'
            + "".join(body)
            + '<tr id="imptot-typed" style="display:none"><td>Added here</td>'
            '<td class="sub">typed / agent</td>'
            '<td style="text-align:right" class="mono" id="imptot-typed-n">0</td>'
            '<td style="text-align:right" class="mono" id="imptot-typed-v">$0</td><td></td></tr>'
            '<tr style="border-top:1px solid var(--line);font-weight:700">'
            '<td style="padding:6px" colspan="2">Everything</td>'
            f'<td style="text-align:right;padding:6px" class="mono" id="imptot-grand-n">{n_staged}</td>'
            f'<td style="text-align:right;padding:6px" class="mono" id="imptot-grand-v">${grand:,.0f}</td><td></td></tr>'
            '</table>'
            '<style>#holdings td{padding:3px 6px}</style>' + _IMPTOT_JS + '</div>')


_IMPTOT_JS = """<script>
window.recomputeTyped=function(){
  var LIAB={real_estate_debt:1, tax_reserve:1};   // entered 'debts positive' -> SUBTRACT
  // debts read AS debts wherever they sit in the shared holdings table (runs
  // even with no imports staged, so it's before the totals-box guard)
  document.querySelectorAll('#hrows .row').forEach(function(r){
    var k=r.querySelector('[name=u_kind]');
    r.classList.toggle('row-liab', !!(k && LIAB[k.value]));
  });
  var box=document.getElementById('imptot'); if(!box)return;
  var stagedV=parseFloat(box.dataset.stagedV||'0'), stagedN=parseInt(box.dataset.stagedN||'0');
  var tv=0, tn=0;
  document.querySelectorAll('#hrows .row').forEach(function(r){
    if(r.classList.contains('src-auto')||r.classList.contains('src-manual'))return; // imported = in staged total
    var name=r.querySelector('[name=u_name]'), val=r.querySelector('[name=u_value]'),
        kind=r.querySelector('[name=u_kind]');
    if(!name||!val)return;
    var v=parseFloat((val.value||'').replace(/[$,]/g,''));
    if(name.value.trim() && !isNaN(v)){
      if(kind && LIAB[kind.value]) v=-Math.abs(v);   // a mortgage reduces equity, never adds
      tv+=v; tn++;
    }
  });
  var trow=document.getElementById('imptot-typed');
  if(tn){ trow.style.display=''; document.getElementById('imptot-typed-n').textContent=tn;
          document.getElementById('imptot-typed-v').textContent='$'+Math.round(tv).toLocaleString(); }
  else trow.style.display='none';
  document.getElementById('imptot-grand-n').textContent=stagedN+tn;
  document.getElementById('imptot-grand-v').textContent='$'+Math.round(stagedV+tv).toLocaleString();
  box.style.display=(stagedN+tn)?'':'none';
};
(function(){var h=document.getElementById('hrows');
  if(h)h.addEventListener('input',window.recomputeTyped);
  window.recomputeTyped();})();
</script>"""


def _esc_import_totals(folder):
    try:
        return _import_totals_html(folder)
    except Exception:
        return ""                                    # verification block never blocks onboarding


def staged_prefill(folder):
    """Prefill + notice from the staged union (all pulls so far, deduped
    freshest-first). This is what makes multi-step onboarding coherent: import
    IBKR, then drop three statements — the table always shows the merged,
    overlap-annotated whole."""
    from officekit import staging
    rows, overlaps = staging.merged_rows(folder)
    if not rows:
        return None, ""
    prefill, note = adapter_prefill(rows)
    n_src = len(staging.load(folder).get("sources", {}))
    note = f"Showing the merged view of {n_src} source(s). " + note
    if overlaps:
        frag = "; ".join(f"{o['symbol']} kept from {o['kept']} (also in {', '.join(o['displaced'])})"
                         for o in overlaps[:5])
        note += (f" {len(overlaps)} symbol(s) appear in multiple sources — freshest wins, "
                 f"never double-counted: {frag}" + ("; …" if len(overlaps) > 5 else "") + ".")
    warn = [w for s in staging.load(folder)["sources"].values() for w in (s.get("warnings") or [])]
    if warn:
        note += f" ⚠ {len(warn)} reconciliation warning(s) — see the IMPORTS page before building."
    return prefill, note


def _safe_page(name):
    """Sanitize a `back` value to an import-detail page filename, or fall back to
    the imports index — never let a form value pick an arbitrary path."""
    n = re.sub(r"[^a-z0-9_-]", "", str(name or "").lower())
    return f"{n}.html" if n.startswith("import_") else "imports.html"


def _repull_button(name, back_slug, button, note):
    """A one-click adapter re-fetch (live API pull or on-disk re-read)."""
    return (f'<form method="POST" action="/adapter/import" style="margin:0" {_BUSY_ATTR}>'
            f'<input type="hidden" name="adapter" value="{html.escape(name)}">'
            f'<input type="hidden" name="back" value="{html.escape(back_slug)}">'
            f'<button type="submit" class="btn2">{button}</button></form>'
            f'<p class="note" style="margin:8px 0 0">{note}</p>')


def _remove_button(sid):
    return (f'<form method="POST" action="/import/remove" style="margin:10px 0 0" {_BUSY_ATTR}>'
            f'<input type="hidden" name="source_id" value="{html.escape(sid)}">'
            '<input type="hidden" name="back" value="imports">'
            '<button type="submit" class="btn2" style="background:#3a2326;color:#e0736a">'
            'Remove this import</button></form>')


def _import_refresh_html(folder, entry):
    """The right refresh control for one import, matched to how it gets its data:
      * live connection (broker API)  -> Re-pull now (button)
      * file/CSV import — an upload OR an on-disk file adapter -> the FULL file
        picker to re-upload/replace (a file adapter also keeps a re-scan button)
      * proposed (born of a verdict) -> nothing to refresh."""
    from officekit.render_imports import import_slug
    if hosted() and entry.get("source_id", "").startswith("adapter:") and entry["source_id"].split(":", 1)[1] not in {"alpaca", "ibkr_flex"}:
        return '<p class="note">This source runs on your computer. Refresh it in the local app and enable Hosting &amp; sync to share updates.</p><a href="/settings" target="_top">Office settings →</a>' + _remove_button(entry["source_id"])
    import officekit_adapters
    kind, sid = entry.get("kind"), entry.get("source_id", "")
    slug = import_slug(sid)

    if kind == "adapter":
        name = sid.split(":", 1)[1] if ":" in sid else sid
        a_kind = (officekit_adapters.ADAPTERS.get(name) or {}).get("kind", "broker")
        if a_kind != "file":                          # live connection — a real pull
            return ('<h2>Re-pull this import</h2>'
                    + _repull_button(name, slug, "↻ Re-pull now",
                        "Live connection — this fetches the latest positions read-only and "
                        "replaces this import's rows."))
        # file/CSV adapter: the full picker to re-upload a fresh file (a new upload
        # source; back to the index because it isn't this adapter's own rows), plus
        # a re-scan button for the auto-read-from-disk path.
        return ('<h2>Re-add file</h2>'
                '<p class="note" style="margin:0 0 4px">File-based import — drop the latest '
                'export to replace these holdings, using the full picker below.</p>'
                + _dropzone_html(folder, back="imports")
                + '<p class="note" style="margin:14px 0 4px">Or re-read the newest matching '
                  'file already on disk:</p>'
                + _repull_button(name, slug, "↻ Re-scan disk",
                    "Re-reads the newest matching file(s) on disk (e.g. the latest export in "
                    "Downloads or statement bundle)."))

    if kind == "upload":
        return ('<h2>Re-add file</h2>'
                '<p class="note" style="margin:0 0 4px">Uploaded document — refresh it by adding '
                'the file again with the full picker below. Re-uploading the SAME filename '
                'REPLACES this import; a new filename adds a separate one.</p>'
                + _dropzone_html(folder, back=slug) + _remove_button(sid))
    return None


def write_imports_page(folder):
    """Regenerate the audit page after every staging change — the page is the
    ledger's face; it must never lag the pulls it audits. Also writes a detail
    page per import (every asset it supplies, totals, and a refresh control)."""
    from officekit import staging
    from officekit.render_imports import render_imports, render_import_detail, import_slug
    rows, overlaps = staging.merged_rows(folder)
    ledger = staging.ledger(folder)
    disc = _discover_cached() or []
    pages = Path(folder) / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    (pages / "imports.html").write_text(render_imports(
        disc, ledger, rows, overlaps,
        key_status=_key_status(folder), pull_endpoint="/adapter/import",
        upload_html=_dropzone_html(folder, back="imports.html"),
        reconciliation=(json.loads((Path(folder) / "answers.json").read_text()).get("reconciliation")
                        if (Path(folder) / "answers.json").exists() else None)))

    # detail page per pulled source, plus per fetchable adapter not yet pulled
    st = staging.load(folder)
    seen = set()
    for e in ledger:
        sid = e["source_id"]
        seen.add(sid)
        srows = (st["sources"].get(sid) or {}).get("rows") or []
        label = e.get("ref") or sid
        (pages / f"{import_slug(sid)}.html").write_text(render_import_detail(
            f"{label} — import detail", f"{e.get('kind','')} · {e.get('detail','')[:80]}",
            e, srows, _import_refresh_html(folder, e)))
    for a in disc:
        sid = f"adapter:{a['name']}"
        if sid in seen or not a.get("can_fetch"):
            continue                                   # unpulled but connectable: offer Pull now
        stub = {"source_id": sid, "kind": "adapter", "refresh": "auto",
                "as_of": None, "pulled_utc": None, "warnings": [], "detail": a.get("detail", "")}
        (pages / f"{import_slug(sid)}.html").write_text(render_import_detail(
            f"{a['label']} — import detail", f"adapter · {a.get('detail','')[:80]}",
            stub, [], _import_refresh_html(folder, stub)))


def adapter_prefill(rows):
    """Map fetched positions to onboarding form rows. Stocks become ticker rows
    (the classifier takes it from there); everything else is summarized back to
    the caller rather than mislabeled into a category."""
    from officekit.staging import num
    # tolerate dirty rows from any source (a screenshot extraction can hand back
    # a missing sec_type or a string value — must never break the build)
    rows = [{**r, "sec_type": (r.get("sec_type") or "STK"), "symbol": (r.get("symbol") or ""),
             "value": num(r.get("value"))} for r in rows]
    stocks = [r for r in rows if r["sec_type"] in ("STK", "ETF", "FUND", "us_equity") and r["symbol"]]
    cash = [r for r in rows if r["sec_type"] == "CASH"]
    other = [r for r in rows if r not in stocks and r not in cash]
    def _cls(r):
        if r.get("refresh") == "auto":
            return "src-auto"
        return "src-manual" if r.get("source_id") else ""
    prefill = [("ticker", r.get("symbol", ""), round(r["value"], 2), "", _cls(r)) for r in stocks]
    prefill += [("cash", r.get("description") or "Brokerage cash", round(r["value"], 2), "", _cls(r))
                for r in cash]
    note = f"Imported {len(stocks)} stock/fund positions (${sum(r['value'] for r in stocks):,.0f})."
    if cash:
        note += f" Cash balance ${sum(r['value'] for r in cash):,.0f} added as a cash row."
    opts = [r for r in other if r["sec_type"] in ("OPT", "FOP")]
    rest = [r for r in other if r not in opts]
    if opts:
        # options are UNDERSTOOD, not skipped (principal 2026-09-05): the book
        # imports as ONE overlay row at net mark (category options_overlay) —
        # individual contracts are commitments, not holdings, and the labeled
        # lines below say exactly what they are
        net = sum(r["value"] for r in opts)
        prefill.append(("options_overlay", f"Options overlay ({len(opts)} positions)",
                        round(net, 2), "", _cls(opts[0])))
        note += (f" {len(opts)} option positions imported as one overlay row "
                 f"(${net:,.0f} net mark) — summarized:")
        try:
            from officekit_adapters import covered_call_summary, short_put_obligations
            sp = short_put_obligations(rows)
            if sp["count"]:
                top = ", ".join(f"{i['symbol']} ${i['obligation']:,.0f}" for i in sp["items"][:3])
                note += (f" Short puts: ${sp['total']:,.0f} of collateralized purchase "
                         f"obligations across {sp['contracts']} contracts ({top}"
                         + (", …" if sp["count"] > 3 else "") + ") — commitments, not holdings.")
            cc = covered_call_summary(rows)
            if cc["covered"]:
                frag = ", ".join(f"{c['shares']:.0f} {c['symbol']} @ ${c['strike']:g} "
                                 f"(callable for ${c['callable_for']:,.0f})" for c in cc["covered"])
                note += f" Covered calls encumber {frag}."
            if cc["spread_matched_contracts"]:
                note += (f" {cc['spread_matched_contracts']:.0f} short-call contract(s) are "
                         f"spread legs, matched by long calls.")
            if cc["naked"]:
                frag = ", ".join(f"{n['contracts']:.0f}x {n['symbol']} ${n['strike']:g}C"
                                 for n in cc["naked"])
                note += f" NAKED short calls (unbounded risk — review): {frag}."
        except Exception:
            note += " (option summary unavailable — review the option positions by hand.)"
    if rest:
        # PLACE every value-bearing 'other' row so the built office matches the
        # verification total — a counted-but-dropped row silently understates the
        # book (2026-09-06: the $11,735 "USD cash balance" line was shown in
        # totals yet never placed). Route by type; flag anything uncertain for
        # the user to recategorize rather than dropping it.
        def _route(r):
            st = (r.get("sec_type") or "").upper()
            desc = (r.get("description") or "").lower()
            if st in ("BOND", "BILL", "NOTE", "TBOND", "TBILL", "FIXED"):
                return "fixed_income"
            if st == "CASH" or "cash" in desc or not r.get("symbol"):
                return "cash"
            return "public_equity"                   # unknown security: least-wrong, editable, counted
        placed = []
        for r in rest:
            cat = _route(r)
            label = (r.get("symbol") or (r.get("description") or "").strip()
                     or "uncategorized position")
            placed.append((cat, label[:60], round(num(r.get("value")), 2), "", _cls(r)))
        prefill += placed
        note += (f" Placed {len(rest)} other position(s) "
                 f"(${sum(num(r.get('value')) for r in rest):,.0f}) — categorized best-effort "
                 f"(bonds→fixed income, cash lines→cash, else equity); review the Type on each.")
    return prefill, note


def _money(v):
    """Parse a money box: '$1,234', '500k', '1.2m' -> float; empty OR unparseable
    -> None (the caller skips it). NEVER raises — a single junk cell ('TBD',
    '~500k', 'call broker') must not abort the whole onboarding build, and
    inf/nan must never reach answers.json (invalid JSON). Coercion lesson,
    2026-09-06."""
    v = (v or "").strip().replace("$", "").replace(",", "").replace("−", "-").lower()
    if not v:
        return None
    mult = 1
    if v.endswith("k"):
        mult, v = 1_000, v[:-1]
    elif v.endswith("m"):
        mult, v = 1_000_000, v[:-1]
    try:
        f = float(v) * mult
    except ValueError:
        return None
    if f != f or f in (float("inf"), float("-inf")):     # NaN/inf never enter the book
        return None
    return f


def answers_from_form(form, folder):
    g = lambda k: (form.getvalue(k) or "").strip() if form.getvalue(k) else ""
    answers = {"owner": g("owner") or None, "as_of": g("as_of") or date.today().isoformat(),
               "sleeves": [], "imports": [], "profile": {}, "goals": []}
    identity = folder / 'answers.json'
    if identity.exists():
        oid = json.loads(identity.read_text()).get('office_id')
        if oid:
            answers['office_id'] = oid
    # csv upload
    if "positions_csv" in form:
        item = form["positions_csv"]
        if getattr(item, "filename", None):
            folder.mkdir(parents=True, exist_ok=True)   # survive the folder vanishing mid-run
            dest = folder / "positions.csv"
            dest.write_bytes(item.file.read())
            answers["imports"].append({"kind": "positions_csv", "path": 'positions.csv' if hosted() else str(dest),
                                       "account": g("account") or "brokerage"})
    # ONE holdings table: ticker rows run the classifier; everything else is a
    # sleeve as typed (principal ruling 2026-09-04: no separate section)
    kinds = form.getlist("u_kind") if form.getvalue("u_kind") is not None else []
    names = form.getlist("u_name")
    values = form.getlist("u_value")
    rates = form.getlist("u_rate")
    rows = []
    for i, kind in enumerate(kinds):
        val = _money(values[i] if i < len(values) else "")
        name = names[i].strip() if i < len(names) else ""
        if not kind or val is None:
            continue
        if kind == "ticker":
            if name:
                rows.append({"symbol": name, "value": val})
            continue
        s = {"category": kind, "value": val}
        if name:
            s["name"] = name
        if kind == "real_estate_debt":
            # fixed vs ARM survives the form via the name (the only field that
            # round-trips); default fixed. The chat agent labels ARM mortgages.
            s["style"] = "arm" if re.search(r"\barm\b|adjustable", name, re.I) else "fixed"
            if i < len(rates) and rates[i].strip():
                s["rate_pct"] = _money(rates[i].replace("%", "")) or None
        answers["sleeves"].append(s)
    if rows:
        answers["positions"] = {"account": g("account") or "brokerage", "rows": rows}
    # income as an asset
    if _money(g("income_annual")):
        inc = {"annual": _money(g("income_annual")), "years": _money(g("income_years")) or 20}
        if g("income_style") in ("equity_linked", "stable"):
            inc["style"] = g("income_style")
        answers["income"] = inc
    # windfall
    if _money(g("wind_amount")):
        w = {"amount": _money(g("wind_amount")), "eta": g("wind_eta") or "pending",
             "character": g("wind_character") or "ltcg"}
        if g("wind_state"):
            w["state"] = g("wind_state")
        if g("wind_rate"):
            w["rate"] = _money(g("wind_rate").replace("%", ""))
        answers["incoming"] = w
    # goals
    if g("ret_date") or _money(g("ret_spend")):
        answers["goals"].append({"kind": "retirement", "label": "Retirement",
                                 **({"date": g("ret_date")} if g("ret_date") else {}),
                                 "annual_spending": _money(g("ret_spend")) or 0})
    glabels = form.getlist("goal_label") if form.getvalue("goal_label") is not None else []
    gdates = form.getlist("goal_date")
    gamounts = form.getlist("goal_amount")
    for i, label in enumerate(glabels):
        amt = _money(gamounts[i] if i < len(gamounts) else "")
        if not label.strip() or not amt:
            continue
        gd = gdates[i].strip() if i < len(gdates) else ""
        answers["goals"].append({"kind": "spending", "label": label.strip(),
                                 **({"date": gd} if gd else {}),
                                 "amount": amt})
    if _money(g("floor_amount")):
        answers["goals"].append({"kind": "liquidity_floor", "label": "Liquidity floor",
                                 "amount": _money(g("floor_amount"))})
    if _money(g("loss_carryforward")):
        answers["loss_carryforward"] = _money(g("loss_carryforward"))
    if form.getvalue("goal_taxharvest") is not None:
        answers["goals"].append({"kind": "tax_efficiency", "label": "Harvest tax losses"})
    for flag in ("net_buyer", "uses_leverage", "decumulating", "premium_selling_allowed",
                 "concentrated_low_basis"):
        answers["profile"][flag] = form.getvalue("p_" + flag) is not None
    return answers


def _link_existing_strategies(answers, goal_ids, folder):
    """When a goal is added, any strategy the office ALREADY holds that fits the
    goal's kind should serve it immediately (principal-directed 2026-09-08) —
    file a goal origin on those existing decisions only (never create new ones;
    an unserved goal instead points the user to the Strategies page). Idempotent."""
    from officekit.goal_mandates import _menu, _years_out
    from officekit.mandates import _origin
    try:
        from officekit.personal_context import load as _pc_load
        pc = _pc_load(folder)
    except Exception:
        pc = None
    decs = answers.get("strategy_decisions") or {}
    as_of = answers.get("as_of", "")
    by_id = {x.get("id"): x for x in answers.get("goals", [])}
    for gid in goal_ids:
        goal = by_id.get(gid)
        if not goal:
            continue
        yrs = _years_out(goal.get("date"), as_of)
        for sid, _why in _menu(goal, yrs, pc):
            dec = decs.get(sid)
            if not dec:
                continue                       # only EXISTING strategies are auto-linked
            origins = dec.setdefault("origins", [])
            if not any(o.get("source") == "goal" and o.get("ref") == gid for o in origins):
                origins.append(_origin("goal", gid))


def _attach_lots(dst, src):
    """Copy lot-level harvest fields (from a Flex pull) onto an office position
    row, if the source carries them. Returns True if anything changed."""
    changed = False
    for k in ("lots", "loss_lt", "loss_st"):
        if src.get(k) is not None and dst.get(k) != src.get(k):
            dst[k] = src[k]
            changed = True
    return changed


def sync_office_from_staging(folder):
    """Apply scoped custody pulls; only complete, reconciled coverage closes assets."""
    from officekit import staging
    from officekit.reconciliation import reconcile
    rows, _ = staging.merged_rows(folder)
    answers = json.loads((folder / "answers.json").read_text())
    updated, report = reconcile(answers, rows, staging.load(folder)["sources"], _attach_lots)
    build_office(updated, folder)
    return report


def _sma_constituents(folder):
    """The principal's Parametric SMA constituent symbols + a labeled name (with the
    131/31 ratio), read from the newest MS bundle. Used to SPLIT the individual-
    equity book into the direct-index SMA vs deliberate single-name picks. None for
    any non-principal office (the split needs the SMA membership list)."""
    if hosted():
        saved_path = Path(folder) / "balance_sheet.json"
        saved = json.loads(saved_path.read_text()) if saved_path.exists() else {}
        sleeves = [s for s in saved.get("sleeves", []) if s.get("category") == "direct_index"]
        symbols = {h.get("company") for s in sleeves for h in s.get("holdings", []) if h.get("company")}
        return symbols or None, (sleeves[0]["name"].split(" — ", 1)[0] if sleeves else "Direct-index SMA")
    try:
        from officekit import harvest as _hv
        if not _hv._is_principal_office(folder):
            return None, "Direct-index SMA"
        from officekit_adapters import morgan_stanley as ms
        b = ms.newest_bundle()
        if not b:
            return None, "Direct-index SMA"
        syms = {(r.get("symbol") or "").upper() for r in ms.positions_rows(ms.parse_bundle(b))
                if (r.get("sec_type") or "STK") == "STK" and r.get("value") and r.get("symbol")}
        syms.discard("USD"); syms.discard("CASH")
        label = "Parametric direct-index SMA"
        try:
            from officekit import harvest as _hvr
            ratio = ((_hvr._read_scorecard(folder) or {}).get("structure", {}) or {}).get("ratio")
            if ratio:
                label = f"Parametric direct-index SMA ({ratio})"
        except Exception:
            pass
        return (syms or None), label
    except Exception:
        return None, "Direct-index SMA"


def _import_desk_board(folder):
    """TRANSITION import: snapshot the desk positions board into the thesis-sleeve
    shape (stored office-owned in answers['desk_theses']). Principal office only;
    the ONLY desk read, and it's explicit (the /import/desk-board action), never a
    per-build live dependency. [] for any other tenant or unreadable board."""
    try:
        from officekit import harvest as _hv
        from officekit import thesis_board
        if not _hv._is_principal_office(folder):
            return []
        return thesis_board.import_desk_board(Path("desk/ui/static/positions_board.json"))
    except Exception:
        return []


def _thesis_sleeves(answers, folder):
    """The office's thesis sleeves — OFFICE-NATIVE (its own court adjudications +
    positions), MERGED with the owned desk-import snapshot (answers['desk_theses'])
    AND contributed STRATEGY PACKS (strategies/<id>/pack.json + DECK.md, incl. any
    in the office folder). No desk read: assembled from owned + contributed data."""
    from officekit import thesis_board, strategy_packs
    packs, _probs = strategy_packs.load_packs([Path(folder) / "strategies"])
    return thesis_board.merge(
        thesis_board.merge(answers.get("desk_theses") or [],
                           thesis_board.from_adjudications(folder)),
        strategy_packs.as_theses(packs))


_OFFICE_WRITE_LOCK = threading.RLock()


def _office_write(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        from officekit.office_lock import locked
        office_folder = kwargs.get("folder", args[1] if len(args) > 1 else None)
        with locked(office_folder), _OFFICE_WRITE_LOCK:
            return fn(*args, **kwargs)
    return wrapped


def _apply_realized_tax(data, folder):
    # REALIZED capital losses are a tax ASSET (they offset this year's gains and any
    # excess carries forward). Fold the principal's banked Parametric losses into the
    # tax model so the reserve reflects them — and a deferred-tax-asset sleeve appears
    # if they exceed the gain (2026-09-10). Additive, principal-gated, never fatal.
    try:
        from officekit import harvest as _hv
        tm = data.get("tax_model")
        if tm and (_hv._is_principal_office(folder) or (hosted() and (Path(folder) / "parametric_scorecard.json").is_file())):
            rl = _hv._realized_split({"d": data}, folder)
            if rl["net"] > 0:
                tm["harvest_losses_2026"] = max(float(tm.get("harvest_losses_2026") or 0), rl["net"])
                tm.setdefault("realized_losses_ytd", round(rl["net"]))   # mutated in place on data
                tm["realized_st_ytd"], tm["realized_lt_ytd"] = round(rl["st"]), round(rl["lt"])
    except Exception:
        pass


def _capital_model(answers, folder):
    """Read-only receipt review uses the same tax enrichment as publication."""
    from copy import deepcopy
    sma_syms, sma_label = _sma_constituents(folder)
    data = build_from_answers(deepcopy(answers), sma_symbols=sma_syms, sma_label=sma_label)
    _apply_realized_tax(data, folder)
    return build_model(data)


@_office_write
def build_office(answers, folder):
    sma_syms, sma_label = _sma_constituents(folder)
    # OWN the desk's thesis sleeves: import a snapshot into the office's OWN answers,
    # so the office never depends on desk/data at read time and the theses survive
    # the desk's deprecation (desk-deprecation ruling: the app is the single source).
    # GENERATE the Parametric scorecard into the OFFICE folder from the MS bundles
    # (an officekit adapter) — the office no longer reads desk/data for it. Principal
    # only; the harvest bridge reads this office-owned copy first (desk-deprecation).
    try:
        from officekit import harvest as _hv0
        if _hv0._is_principal_office(folder):
            from officekit_adapters import morgan_stanley as _ms0
            _prev = None
            _cardp = folder / "parametric_scorecard.json"
            if _cardp.exists():
                _prev = json.loads(_cardp.read_text())
            _syms = {(r.get("symbol") or "").upper()
                     for r in (answers.get("positions") or {}).get("rows", []) if r.get("symbol")}
            _card = _ms0.build_scorecard(our_book=_syms, prev_card=_prev)
            if _card:
                _cardp.write_text(json.dumps(_card, indent=1))
    except Exception:
        pass                                         # generation never blocks a build
    data = build_from_answers(answers, sma_symbols=sma_syms, sma_label=sma_label)
    # the asset allocation IS a set of strategies already running — register them
    # as implemented and attach them to the goals they fund, so a goal never reads
    # "no strategy serving" beside the very assets serving it (2026-09-08).
    try:
        from officekit import implicit_strategies
        from officekit.personal_context import load as _pc_load
        try:
            _pc = _pc_load(folder)
        except Exception:
            _pc = None
        if implicit_strategies.register(answers, data, _pc, folder=folder):
            data = build_from_answers(answers, sma_symbols=sma_syms, sma_label=sma_label)  # re-materialize
    except Exception:
        pass                                       # implicit strategies never block a build
    _apply_realized_tax(data, folder)
    core = _render_core(answers, data, folder)
    pages = folder / "pages"
    pages.mkdir(parents=True, exist_ok=True)
    # Reject non-finite values before publishing either financial document.
    answers_json = json.dumps(answers, indent=1, ensure_ascii=False, allow_nan=False) + "\n"
    data_json = json.dumps(data, indent=1, ensure_ascii=False, allow_nan=False) + "\n"
    # Publish receipt facts and their embedded audit in one atomic replacement.
    # Other derived files can be rebuilt if publication is interrupted later.
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", dir=folder, prefix=".answers-", delete=False) as saved:
        saved.write(answers_json)
        saved.flush()
        os.fsync(saved.fileno())
    os.replace(saved.name, folder / "answers.json")
    (folder / "balance_sheet.json").write_text(data_json)
    pc_path = folder / "personal_context.json"
    if not pc_path.exists():   # empty-but-asserted from day one; never overwrite content
        from officekit.personal_context import empty as _pc_empty
        pc_path.write_text(json.dumps(_pc_empty(data.get("office_id")), indent=1) + "\n")
    for fn, htmlstr in core.items():
        (pages / fn).write_text(htmlstr)
    (folder / "draft.json").unlink(missing_ok=True)   # built into answers now
    try:
        write_imports_page(folder)
    except Exception:
        pass
    _render_additional(answers, data, folder)
    return data


def _render_core(answers, data, folder):
    """Same decision pages in both transports, rendered from saved financial facts."""
    m = build_model(data)
    # UX ruling 2026-09-04: goals OFFER a strategy menu; nothing auto-queues.
    # The user adopts from the taxonomy (goal -> strategy -> assets).
    from officekit.goal_mandates import goal_strategy_menu
    from officekit.personal_context import load as _pc_load
    try:
        pc = _pc_load(folder)
    except ValueError:
        pc = None
    goal_menu = goal_strategy_menu(m, pc)
    adjudications = []
    try:
        from officekit_ai.court import load_adjudications
        adjudications = load_adjudications(folder)
    except ImportError:
        pass
    docket_items = []
    try:
        from officekit_ai.docket import load_docket
        docket_items = load_docket(folder)
    except ImportError:
        pass
    # Render the decision CORE pages into memory BEFORE
    # writing anything. If a render raises, we raise here and the previous
    # office (answers/balance_sheet/pages) is left untouched — never a half-built
    # office that traps the user in a broken app shell needing /reset.
    from officekit.render_capital import render_capital
    from officekit.render_goals import render_goals
    from officekit.render_risk import render_risk
    from officekit.risk_officer import review
    from officekit.commitments import revision
    from officekit.strategy_proposals import list_proposals
    m["_commitment_revision"] = revision(answers)
    core = {
        "goals.html": render_goals(m, chat=bool(_ai(folder))),
        "capital.html": render_capital(m, answers, chat=bool(_ai(folder))),
        "risk.html": render_risk(m, review(m, answers, personal_context=pc), answers),
        "office.html": render_office(m, goals_endpoint="/goals", assets_endpoint="/assets",
                                     chat=bool(_ai(folder))),
        "scenarios.html": render_scenarios(m, adopt_endpoint="/strategy/adopt"),
        "strategies.html": render_strategies(
            m, create_endpoint="/strategy/new",
            court_endpoint="/court" if _ai(folder, slot="bench") else None,
            holdings_endpoint="/holdings", adjudications=adjudications,
            goal_menu=goal_menu, goal_adopt_endpoint="/strategy/goal-adopt",
            goal_unadopt_endpoint="/strategy/goal-unadopt", docket_items=docket_items,
            desk_theses=_thesis_sleeves(answers, folder),    # office-native + owned snapshot
            desk_import_endpoint=None if hosted() else "/import/desk-board", proposals=list_proposals(folder)),
    }
    return core


def _render_additional(answers, data, folder):
    m = build_model(data)
    pages = Path(folder) / "pages"
    try:
        from officekit_ai.court import load_adjudications
        adjudications = load_adjudications(folder)
    except ImportError:
        adjudications = []
    # one projection page per goal: when the serving strategies reach it
    try:
        from officekit.goal_mandates import goal_coverage
        from officekit.goal_projection import project, recommendations
        from officekit.render_goal import render_goal
        cov = goal_coverage(m)["by_goal"]
        for g in data.get("goals") or []:
            gid = g.get("id")
            if not gid or g.get("implicit"):
                continue                           # intuited goals live inline on Home, no projection page
            serving = cov.get(gid, [])
            proj = project(g, serving, data.get("as_of", ""), m)
            recs = recommendations(g, proj, m)
            (pages / f"goal_{gid}.html").write_text(render_goal(g, serving, proj, recommendations=recs))
    except Exception:
        pass                                   # a projection failure never blocks the build
    # the growth calculator + the Risk Officer (whole-portfolio surfaces)
    try:
        from officekit.render_growth import render_growth
        (pages / "growth.html").write_text(render_growth(m, answers))
    except Exception:
        pass
    try:
        from officekit import harvest as _hv
        from officekit.render_harvest import render_harvest
        col = _hv.collect(m, folder)
        rate = float((data.get("tax_model") or {}).get("rate_ltcg") or 0.238)
        default_sel = {p["id"] for p in col["positions"] if p["known"] and p["loss"] > 0}
        sim = _hv.simulate(col, default_sel, m, rate, data.get("as_of"))
        (pages / "harvest.html").write_text(render_harvest(m, col, sim, rate))
    except Exception:
        pass
    # every adjudication gets its full pitch-deck page (click-through taxonomy)
    from officekit.render_deck import deck_filename, render_deck, render_markdown_deck
    from officekit.render_strategies import STRATEGY_LIB
    for a in adjudications:
        title = (STRATEGY_LIB.get(a.get("strategy"), {}) or {}).get("title") \
            or (data.get("strategy_decisions", {}).get(a.get("strategy"), {}) or {}).get("title")
        (pages / deck_filename(a)).write_text(render_deck(a, strategy_title=title))
    # contributed strategy-pack decks (DECK.md) -> a deck page per pack
    try:
        from officekit import strategy_packs
        _packs, _pk_probs = strategy_packs.load_packs([folder / "strategies"])
        for p in _packs:
            if p.get("deck_path") and Path(p["deck_path"]).exists():
                md = Path(p["deck_path"]).read_text()
                (pages / f"thesis_deck_{p['id']}.html").write_text(
                    render_markdown_deck(p.get("name") or p["id"], md, author=p.get("author")))
        if _pk_probs:
            print(f"[serve] strategy-pack problems: {_pk_probs}")   # degrade loud
    except Exception as e:
        print(f"[serve] strategy-pack decks skipped: {type(e).__name__}: {e}")
    # F3a: the signals surfaces — index, one page per capability, one per asset
    try:
        import officekit_signals as sig
        import officekit_signals.fleet  # noqa: F401 — registers the full detector/generator fleet
        from officekit.model import strategy_tags
        from officekit.render_signals import render_asset, render_capability, render_signals_index
        rt = sig.runtime(folder)
        (pages / "signals.html").write_text(render_signals_index(sig.CAPABILITIES, rt))
        for name, cap in sig.CAPABILITIES.items():
            (pages / f"capability_{name}.html").write_text(
                render_capability(cap, rt.get(name), sig.source_code(name)))
        assets = {}
        for s in data.get("sleeves", []):
            for h in s.get("holdings", []):
                if h.get("company"):
                    assets.setdefault(str(h["company"]).upper(), set()).update(
                        strategy_tags(h) or strategy_tags(s))
        for a in adjudications:
            if a.get("symbol") and a.get("subject_kind", "security") == "security":
                assets.setdefault(a["symbol"].upper(), set()).add(a.get("strategy"))
        for sym, strats in assets.items():
            strats = sorted(x for x in strats if x)
            union, seen = [], set()
            for st in strats or [None]:
                for c in sig.applicable(symbol=sym, strategy=st):
                    if c["name"] not in seen:
                        seen.add(c["name"])
                        union.append(c)
            from officekit.render_signals import asset_slug
            (pages / f"asset_{asset_slug(sym)}.html").write_text(
                render_asset(sym, data, adjudications, union, strats))
    except ImportError:
        pass


def render_saved_office(folder):
    """Render an existing office without rebuilding or publishing its balances."""
    folder = Path(folder)
    answers = json.loads((folder / "answers.json").read_text())
    data = json.loads((folder / "balance_sheet.json").read_text())
    pages = folder / "pages"
    pages.mkdir(exist_ok=True)
    for name, content in _render_core(answers, data, folder).items():
        (pages / name).write_text(content)
    write_imports_page(folder)
    _render_additional(answers, data, folder)


def goals_from_form(form):
    """Reconstruct answers["goals"] from the office-page goals editor.

    Identity rules (the reason the editor exists server-side at all): a row
    carrying a `gid` keeps that goal's UUID — edits preserve identity, so
    ledger goal_status history spans the change; a row with kind set to
    "— remove —" (empty) is dropped; a new row gets no id here and intake
    mints a fresh one at build."""
    gids = form.getlist("gid") if form.getvalue("gid") is not None else []
    kinds = form.getlist("gkind")
    labels = form.getlist("glabel")
    dates = form.getlist("gdate")
    amts = form.getlist("gamt")

    def at(lst, i):
        return lst[i].strip() if i < len(lst) and lst[i] else ""
    goals = []
    for i in range(len(gids)):
        kind = at(kinds, i)
        amt = _money(at(amts, i))
        if not kind or amt is None:      # removed, or an untouched blank row
            continue
        g = {"kind": kind, "label": at(labels, i) or kind.replace("_", " ").title()}
        if at(gids, i):
            g["id"] = at(gids, i)
        if at(dates, i):
            g["date"] = at(dates, i)
        if kind == "retirement":
            g["annual_spending"] = amt
        else:
            g["amount"] = amt
        goals.append(g)
    return goals


def record_purchase(answers, sid, symbol, amount, adjudications=None):
    """E3 — strategy becomes asset: append the bought holding to the strategy's
    sleeve (created on first purchase), tag membership, attach the freshest
    adjudication for (strategy, symbol), and flip the decision to implemented.
    Recording only — the user bought at their own broker; nothing executes."""
    from officekit.mandates import _origin
    from officekit.render_strategies import STRATEGY_LIB
    symbol = symbol.upper().strip()
    holding = {"company": symbol, "amount": float(amount), "strategies": [sid]}
    latest = None
    for a in adjudications or []:
        if a.get("strategy") == sid and a.get("symbol") == symbol and a.get("subject_kind", "security") == "security":
            latest = a
    if latest:
        holding["adjudication"] = {"verdict": latest["verdict"], "date": latest["date"],
                                   "ref": latest["id"]}
    sleeve = next((s for s in answers.get("sleeves", [])
                   if sid in (s.get("strategies") or [])), None)
    if sleeve is None:
        lib = STRATEGY_LIB.get(sid, {})
        dec = (answers.get("strategy_decisions") or {}).get(sid, {})
        title = lib.get("title") or dec.get("title") or sid
        sleeve = {"category": lib.get("category") or dec.get("category") or "public_equity",
                  "name": f"{title} sleeve", "value": 0.0,
                  "strategies": [sid], "holdings": []}
        answers.setdefault("sleeves", []).append(sleeve)
    sleeve.setdefault("holdings", []).append(holding)
    sleeve["value"] = float(sleeve.get("value") or 0.0) + float(amount)
    dec = answers.setdefault("strategy_decisions", {}).setdefault(sid, {})
    dec["status"] = "implemented"                     # a purchase IS implementation
    dec.setdefault("origins", []).append(_origin("principal", f"implemented {symbol}"))
    return sleeve


def _classify_unknowns(answers, folder, ai):
    """Gather every position row (typed + CSV), find symbols the deterministic
    classifier can't place, and ask the classify model. Returns suggestions
    (possibly []) — any failure returns [] and the build proceeds unchanged."""
    from officekit.importers import read_positions_csv, unknown_symbols
    from officekit_ai.classify import load_learned, suggest
    rows = list((answers.get("positions") or {}).get("rows") or [])
    for spec in answers.get("imports") or []:
        try:
            from officekit.runtime import import_path
            rows += read_positions_csv(import_path(spec["path"]))
        except Exception:
            pass
    known = dict(load_learned(folder))
    known.update({k.upper(): tuple(v) for k, v in (answers.get("fund_map") or {}).items()})
    unknowns = unknown_symbols(rows, extra_map=known)
    if not unknowns:
        return []
    descs = {str(r.get("symbol", "")).upper(): str(r.get("desc", "")).strip()
             for r in rows if r.get("desc")}
    return suggest(unknowns, ledger_path=folder / "learning.jsonl",
                   office_id=answers.get("office_id"), folder=folder, descs=descs)


def make_handler(folder):
    folder = Path(folder)
    from officekit.hosting_ui import Hosting, handle as handle_hosting
    hosting = None if hosted() else Hosting(folder)
    from officekit.commitment_routes import prune_previews
    from officekit.strategy_proposals import recover_interrupted
    if not hosted():
        recover_interrupted(folder)
    prune_previews(folder)
    prune_previews(folder, directory="inflow_previews")

    class Handler(BaseHTTPRequestHandler):
        def _send(self, body, code=200, ctype="text/html; charset=utf-8", *, error_context=None, error_href=None, public=False):
            from officekit import api_errors
            public = public or getattr(self, '_public_request', False)
            is_notice = public or self.path.split('?', 1)[0].startswith('/api-errors')
            context = error_context or 'request:' + self.path.split('?', 1)[0]
            error = None
            event = None
            if not is_notice and isinstance(body, str):
                if 'application/json' in ctype:
                    try:
                        payload = json.loads(body)
                        if isinstance(payload, dict) and payload.get('error'):
                            error = api_errors.message(payload['error'])
                            payload['error'] = error
                            body = json.dumps(payload)
                    except ValueError:
                        pass
                if code >= 400:
                    error = error or (api_errors.message(body) if 'text/plain' in ctype else f'The request failed (HTTP {code}). Try again from the original action.')
                if error:
                    event = api_errors.report(folder, context, 'API request failed', error, href=error_href)
                elif code < 400 and ('application/json' in ctype or self.command == 'POST'):
                    api_errors.clear(folder, context=context)
                if code >= 400 and 'text/plain' in ctype and 'text/html' in self.headers.get('Accept', ''):
                    body = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                            '<title>Request needs attention</title></head><body style="margin:0;background:#0b0e12;color:#e8ebee;font:15px/1.6 -apple-system,sans-serif">'
                            '<main style="padding:24px"><h1>Request not completed</h1>'
                            '<button type="button" onclick="history.back()">Back to the previous page</button></main></body></html>')
                    ctype = 'text/html; charset=utf-8'
            if not public and isinstance(body, str) and 'text/html' in ctype:
                body = api_errors.inject(body)
            body = body.encode() if isinstance(body, str) else body
            self._response_started = True
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            if self.path == "/hosting" or self.path.startswith("/hosting/"):
                self.send_header("Cache-Control", "no-store")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("Content-Security-Policy", "frame-ancestors 'self'")
            if event:
                self.send_header("X-Office-API-Error-Id", event['id'])
                from urllib.parse import quote
                self.send_header("X-Office-API-Error-Context", quote(context, safe=':/'))
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _failure(self, error, *, json_response=False, context=None, href=None):
            from officekit import api_errors
            api_errors.log_exception(error, context or self.path.split('?', 1)[0])
            if getattr(self, '_response_started', False):
                return
            code, detail = api_errors.classify(error)
            try:
                return self._send(json.dumps({'error': detail}) if json_response else detail,
                                  code, 'application/json' if json_response else 'text/plain; charset=utf-8',
                                  error_context=context, error_href=href)
            except (BrokenPipeError, ConnectionResetError):
                return
            except Exception as reporting_error:
                api_errors.log_exception(reporting_error, 'error response')
                if getattr(self, '_response_started', False):
                    return
                body = b'{"error":"Something went wrong. See the server log."}'
                self._response_started = True
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        def _guard(self, action):
            self._response_started = False
            self._public_request = False
            try:
                return action()
            except (BrokenPipeError, ConnectionResetError):
                return
            except Exception as error:
                return self._failure(error, json_response='application/json' in self.headers.get('Content-Type', ''),
                                     context='hosting' if self.path.startswith('/hosting/') else None)

        def do_GET(self):
            return self._guard(self._get)

        def do_POST(self):
            if self.path.startswith("/hosting/"):
                return self._guard(self._post)
            from officekit.office_lock import locked
            with locked(folder):
                return self._guard(self._post)

        def _redirect(self, to):
            if self.command == 'POST':
                from officekit.api_errors import clear
                clear(folder, context='request:' + self.path.split('?', 1)[0])
            self._response_started = True
            self.send_response(303)
            self.send_header("Location", to)
            self.end_headers()

        def _flash(self, notice="", err=""):
            """Post/Redirect/Get: stash a one-shot message so a mutating POST can
            redirect (no 'confirm resubmission' on refresh) yet the next GET still
            shows the result. Cleared on read."""
            if err:
                raise err if isinstance(err, BaseException) else ValueError(err)
            try:
                (folder / ".flash.json").write_text(json.dumps({"notice": notice, "err": ""}))
            except OSError:
                pass

        def _pop_flash(self):
            p = folder / ".flash.json"
            try:
                d = json.loads(p.read_text())
                p.unlink(missing_ok=True)
                return d.get("notice", ""), d.get("err", "")
            except Exception:
                return "", ""

        def _onboard(self, err="", prefill=None, notice="", via=None):
            if err:
                return self._failure(err if isinstance(err, BaseException) else ValueError(err))
            if prefill is None:
                try:
                    prefill, staged_note = staged_prefill(folder)
                    notice = notice or staged_note
                except Exception as e:
                    return self._failure(e)
            err_html = ""
            if notice:
                err_html += ('<div class="err" style="border-color:var(--emerald);color:var(--emerald)">'
                             + html.escape(notice) + "</div>")
            ai = _ai(folder)
            self._send(ONBOARD.format(style=STYLE, err=err_html, today=date.today().isoformat(),
                                      key_form='' if hosted() else '<form id="intake-key" method="POST" action="/key"></form>',
                                      settings_link='<p><a href="/settings">Office settings</a></p>',
                                      storage_note=('Your office is saved privately to your account and can be exported.' if hosted() else 'Your data stays in a local folder you own.'),
                                      adapters=_adapters_html(), dropzone=_dropzone_html(folder),
                                      hold_open=('open' if len(prefill or []) <= 12 else ''),
                                      u_rows=_urows_html(prefill=prefill),
                                      import_totals=_esc_import_totals(folder),
                                      cat_opts=_uopts().replace('"', '\\"'),
                                      chat=CHAT_PANEL.format(
                                          chat_first=_chat_first_html(notice or None, via))
                                      if ai else _key_ask_html(notice or None, via),
                                      goals_chat=GOALS_CHAT_PANEL if ai else GOALS_KEYLESS_NOTE,
                                      chat_js=CHAT_JS if ai else "",
                                      draft_js=_server_draft_blob(folder) + _DRAFT_JS))

        def _confirm_page(self, answers, suggestions):
            rows = []
            for s in suggestions:
                label = f'{s["symbol"]} → {s["category"].replace("_", " ")}'
                if s.get("style"):
                    label += f' ({s["style"]})'
                rows.append(
                    f'<div class="chk"><input type="checkbox" name="acc" '
                    f'value="{html.escape(s["symbol"])}:{s["category"]}:{s.get("style") or ""}" checked>'
                    f'<div>{html.escape(label)} <span class="why">confidence '
                    f'{s.get("confidence", 0):.0%}</span></div></div>')
            self._send(CONFIRM.format(style=STYLE, rows="".join(rows),
                                      answers_json=html.escape(json.dumps(answers), quote=True)))

        def _get(self):
            if self.path == "/settings":
                from officekit.render_settings import render_settings
                return self._send(render_settings())
            self.path = self.path.split("?", 1)[0]       # strip query (cache-busters, ?v=)
            if self.path == "/hosting" or self.path.startswith("/hosting/"):
                return handle_hosting(self, hosting)
            from officekit.render_landing import asset, render_landing, render_local_guide, render_privacy, render_signup, hosted_origin
            if self.path in {'/welcome', '/guides/local', '/privacy', '/signup'} or self.path.startswith('/public/'):
                self._public_request = True
                if self.path == '/welcome':
                    return self._send(render_landing(local=True), public=True)
                if self.path == '/guides/local':
                    return self._send(render_local_guide(local=True), public=True)
                if self.path == '/privacy':
                    return self._send(render_privacy(local=True), public=True)
                if self.path == '/signup':
                    if hosted_origin():
                        return self._redirect(hosted_origin() + '/signup')
                    return self._send(render_signup(available=False), public=True)
                found = asset(self.path)
                return self._send(found[0], ctype=found[1], public=True) if found else self._send('Not found', 404, 'text/plain', public=True)
            if self.path == '/start':
                if (folder / 'balance_sheet.json').exists():
                    return self._redirect('/')
                notice, err = self._pop_flash()
                return self._onboard(notice=notice, err=err)
            if self.path == '/' and not any((folder / name).exists() for name in ('balance_sheet.json', 'answers.json', 'draft.json', 'staging.json', '.flash.json')):
                return self._send(render_landing(local=True), public=True)
            if self.path == '/api-errors':
                from officekit.api_errors import active
                return self._send(json.dumps(active(folder)), ctype='application/json')
            if self.path == "/strategy/proposals/status":
                from officekit.strategy_proposals import list_proposals
                return self._send(json.dumps([{k: p[k] for k in ("id", "status", "stage")} for p in list_proposals(folder)]), ctype="application/json")
            if self.path == "/state":
                # the office's build version — the shell polls this and reloads the
                # open tab when it changes, so any mutation (or the daily sync) is
                # reflected cross-tab without a manual refresh (2026-09-09).
                try:
                    v = (folder / "balance_sheet.json").stat().st_mtime_ns
                except OSError:
                    v = 0
                return self._send(json.dumps({"v": v}), ctype="application/json")
            if self.path.startswith("/pages/proposal_") and self.path.endswith(".html"):
                from officekit import strategy_proposals
                from officekit.commitments import revision
                from officekit.render_proposal import render_proposal
                proposal = strategy_proposals.load(folder, self.path[len('/pages/proposal_'):-5])
                answers = json.loads((folder / 'answers.json').read_text())
                return self._send(render_proposal(proposal, revision=revision(answers)))
            if self.path.startswith("/pages/"):
                p = folder / "pages" / Path(self.path).name
                if p.exists():
                    return self._send(p.read_text())
                # a stale app shell (tab open from before a /reset) requesting a
                # now-deleted page: bust the whole tab back to / rather than
                # showing a bare "not found" inside the iframe (self-heal, not
                # broken — 2026-09-07).
                if not (folder / "balance_sheet.json").exists():
                    return self._send("<!doctype html><script>top.location='/'</script>", 200)
                return self._send("not found", 404)
            if self.path == "/reset":
                # reset is DESTRUCTIVE — never on GET (a link prefetch/preconnect
                # could wipe the office). Show a confirm page that POSTs.
                return self._send(_RESET_CONFIRM.format(style=STYLE))
            if (folder / "balance_sheet.json").exists():
                owner = json.loads((folder / "balance_sheet.json").read_text()).get(
                    "owner", {}).get("first_name", "your")
                return self._send(APP.format(style=STYLE, owner=html.escape(owner)))
            notice, err = self._pop_flash()           # PRG: show the last POST's result
            return self._onboard(notice=notice, err=err)

        def _request_json(self, raw):
            try:
                def reject_constant(value):
                    raise ValueError('Non-finite JSON number')
                payload = json.loads(raw, parse_constant=reject_constant)
            except (ValueError, UnicodeError) as error:
                raise ValueError("The submitted JSON could not be read. Reload and try again.") from error
            if not isinstance(payload, dict):
                raise ValueError("Submit a JSON object")
            return payload

        def _post(self):
            if self.path.startswith("/hosting/"):
                return handle_hosting(self, hosting)
            if self.path == '/api-errors/dismiss':
                from officekit.api_errors import clear
                try:
                    n = int(self.headers.get('Content-Length', 0))
                    if not 0 < n <= 1024:
                        raise ValueError('Invalid dismissal')
                    payload = self._request_json(self.rfile.read(n))
                    import uuid
                    event_id = str(uuid.UUID(payload['id']))
                    clear(folder, event_id=event_id)
                    return self._send('{}', ctype='application/json')
                except (ValueError, KeyError, TypeError):
                    return self._send('{"error":"Invalid dismissal"}', 400, 'application/json')
            if self.path == "/draft":
                # server-side autosave: every manual change is written to disk
                # IMMEDIATELY (not held in the browser until Build), so a reload,
                # a new tab, or a different browser restores the in-progress
                # entries. JSON body = {rows, scalars, goals, profile, taxharvest}.
                try:
                    n = int(self.headers.get("Content-Length", 0) or 0)
                    raw = self.rfile.read(n).decode("utf-8", "replace") if n else "{}"
                    self._request_json(raw)              # validate before writing
                    from officekit.migration import inspect_document
                    inspect_document('draft.json', raw.encode())
                    folder.mkdir(parents=True, exist_ok=True)
                    (folder / "draft.json").write_text(raw)
                    return self._send('', 204, 'application/json')
                except Exception as e:
                    self._failure(e, json_response=True)
                return
            if self.path == "/chat":                    # AI-2: JSON in, JSON out
                try:
                    body = self._request_json(self.rfile.read(int(self.headers.get("Content-Length", 0))))
                    ai = _ai(folder)
                    if not ai:
                        raise ValueError("Configure an intake model in office settings before using chat")
                    from officekit_ai.intake_chat import turn
                    scope = body.get("scope") if body.get("scope") in ("assets", "goals") else "assets"
                    # the agent knows what the scan knows — it never re-asks for
                    # holdings a detected connection can already supply
                    ctx = detection_summary() if scope == "assets" else None
                    t = turn(body.get("messages") or [], folder=folder, scope=scope, context=ctx)
                    if t.get("complete"):
                        try:
                            ai.record_agent_call(folder / "learning.jsonl", "intake", ai.DEFAULT_MODEL,
                                                 {"n_sleeves": len((t.get("answers") or {}).get("sleeves") or []),
                                                  "n_goals": len((t.get("answers") or {}).get("goals") or []),
                                                  "complete": True})
                        except Exception:
                            pass
                    return self._send(json.dumps(t), ctype="application/json")
                except Exception as e:
                    return self._failure(e, json_response=True)
            # keep_blank_values: the aligned-array parsers (sleeves, holdings,
            # goals) rely on positional correspondence — silently dropping a
            # blank field (e.g. a new goal row's empty gid) desyncs every list
            from officekit import formdata
            form = formdata.parse(self.rfile, self.headers)
            g = lambda k: (form.getvalue(k) or "").strip()
            if self.path == "/key":
                # the agents' key intake: process env now, ~/.anthropic_key only
                # on explicit opt-in. Never logged, never echoed, never in the
                # office folder (models.json stays env-var-names-only).
                import os as _os
                k = (form.getvalue("api_key") or "").strip()
                if not k:
                    return self._onboard(err="no key provided")
                _os.environ["ANTHROPIC_API_KEY"] = k
                if (form.getvalue("remember") or "").strip():
                    try:
                        kp = Path.home() / ".anthropic_key"
                        kp.write_text(k + "\n")
                        kp.chmod(0o600)
                    except OSError as e:
                        return self._failure(e)
                return self._redirect("/")
            if self.path == "/reset":                 # destructive -> POST only
                for f in ("answers.json", "balance_sheet.json", "staging.json",
                          "docket.json", "adjudications.jsonl", ".flash.json", "draft.json", "api_errors.json"):
                    (folder / f).unlink(missing_ok=True)
                import shutil as _shutil
                _shutil.rmtree(folder / "pages", ignore_errors=True)
                return self._redirect("/")
            if self.path == "/import/desk-board":
                # TRANSITION: snapshot the desk positions board into the office-OWNED
                # thesis sleeves (answers['desk_theses']). The only desk read, and it's
                # explicit — after this the office assembles theses from its own data.
                try:
                    answers = json.loads((folder / "answers.json").read_text())
                    imported = _import_desk_board(folder)
                    if imported:
                        answers["desk_theses"] = imported
                        build_office(answers, folder)
                        self._flash(notice=f"Imported {len(imported)} thesis sleeves from the desk board "
                                           "(now office-owned).")
                    else:
                        raise ValueError("No desk board is available for this office")
                except Exception as e:
                    return self._failure(e)
                return self._redirect("/pages/strategies.html")
            if self.path == "/import/remove":
                # PRG: redirect after the mutation so refresh never resubmits
                try:
                    from officekit import staging
                    from officekit.render_imports import import_slug
                    sid = g("source_id")
                    staging.remove_source(folder, sid)
                    stale = folder / "pages" / f"{import_slug(sid)}.html"
                    if stale.exists():
                        stale.unlink()                  # its detail page is gone with it
                    write_imports_page(folder)
                    _, note = staged_prefill(folder)
                    self._flash(notice=note or "source removed")
                    if g("back"):
                        return self._redirect("/pages/imports.html")
                except Exception as e:
                    return self._failure(e)
                return self._redirect("/")
            if self.path == "/import/files":
                # drop-anything door: deterministic router first, model second,
                # every file a staged manual-refresh source on the audit page
                try:
                    parts = form.getparts("docs")
                    if not parts:
                        raise ValueError("Choose at least one file to import")
                    else:
                        failures = []
                        results = import_files(folder, parts, on_error=lambda name, error: failures.append((name, error)))
                        if (folder / "balance_sheet.json").exists():
                            sync_office_from_staging(folder)
                        write_imports_page(folder)
                        if failures:
                            name, error = failures[0]
                            return self._failure(error, context='import:upload:' + name, href='/pages/imports.html')
                        _, note = staged_prefill(folder)
                        self._flash(notice="; ".join(results) + ". " + note)
                        if g("back"):                   # came from an import-detail page
                            return self._redirect(f"/pages/{_safe_page(g('back'))}")
                except Exception as e:
                    return self._failure(e)
                return self._redirect("/")             # PRG: no confirm-resubmit on refresh
            if self.path == "/adapter/import":
                # the auto-adapter one-click: fetch positions read-only from the
                # detected connection and re-render onboarding with rows pre-filled
                name = g("adapter")
                try:
                    import officekit_adapters
                    if not name or name not in officekit_adapters.ADAPTERS:
                        # empty/unknown adapter (a browser that dropped the hidden
                        # field, a stale form): fall back to the one ready
                        # fetchable connection — the button's intent — else say so
                        ready = [r for r in (_discover_cached() or [])
                                 if r["found"] and r["can_fetch"] and r["status"] == "ready"]
                        if len(ready) == 1:
                            name = ready[0]["name"]
                        else:
                            raise ValueError(
                                "no connection specified" if not ready else
                                "multiple connections detected — pick one from the panel")
                    snapshot = officekit_adapters.fetch_snapshot(name)
                    rows = snapshot["rows"]
                    from officekit import staging
                    a = officekit_adapters.ADAPTERS.get(name, {})
                    # manual-only adapters (downloads_csv) stage as MANUAL so the
                    # daily loop leaves them alone — a deliberate pull, not a standing feed
                    refresh = "auto" if a.get("auto", True) and not hosted() else "manual"
                    staging.record_pull(folder, f"adapter:{name}", "adapter",
                                        a.get("label", name), rows, refresh=refresh,
                                        as_of=snapshot["as_of"], snapshot=snapshot["snapshot"],
                                        detail=f"{len(rows)} rows via {'manual' if refresh=='manual' else 'live'} pull")
                    write_imports_page(folder)
                    # sync the office balance sheet to the freshly pulled holdings
                    synced = None
                    if (folder / "balance_sheet.json").exists():
                        synced = sync_office_from_staging(folder)
                    sync_note = (f" Office synced: {synced['changed']} refreshed"
                                 + (f", {synced['added']} new" if synced.get('added') else "") + "."
                                 if synced else "")
                    back = g("back")
                    if back:                            # imports page or a specific import-detail page
                        page = "imports.html" if back == "imports" else _safe_page(back)
                        self._flash(notice=f"Re-pulled {len(rows)} rows from {a.get('label', name)}.{sync_note}")
                        return self._redirect(f"/pages/{page}")
                    _, note = staged_prefill(folder)
                    self._flash(notice=note + sync_note)
                    return self._redirect("/")         # PRG: no confirm-resubmit on refresh
                except Exception as e:
                    from officekit import staging
                    context = 'import:adapter:' + name
                    if name:
                        staging.record_failure(folder, f"adapter:{name}", e)
                        write_imports_page(folder)
                    return self._failure(e, context=context, href='/pages/imports.html')
            if self.path == "/onboard":
                try:
                    answers = answers_from_form(form, folder)
                    ai = _ai(folder, slot="classify")   # AI-1: confirm step for unknown tickers
                    if ai:
                        sugg = _classify_unknowns(answers, folder, ai)
                        if sugg:
                            return self._confirm_page(answers, sugg)
                    build_office(answers, folder)
                except Exception as e:                 # fail LOUD on the page, never a silent 500
                    return self._failure(e)
                return self._redirect("/")
            if self.path == "/onboard/confirm":         # AI-1: apply what the human accepted
                try:
                    answers = self._request_json(g("answers_json"))
                    if (folder / 'answers.json').exists():
                        answers['office_id'] = json.loads((folder / 'answers.json').read_text())['office_id']
                    accepted = {}
                    for v in (form.getlist("acc") if form.getvalue("acc") is not None else []):
                        sym, cat, style = v.split(":", 2)
                        accepted[sym] = (cat, style or None)
                    if accepted:
                        from officekit_ai.classify import apply_confirmed, save_confirmed
                        apply_confirmed(answers, accepted)
                        save_confirmed(folder, accepted)
                    build_office(answers, folder)
                except Exception as e:
                    return self._failure(e)
                return self._redirect("/")
            if self.path == "/signals/run":
                try:
                    import os
                    import officekit_signals as sig
                    answers = json.loads((folder / "answers.json").read_text())
                    data = json.loads((folder / "balance_sheet.json").read_text())
                    ctx = {"office_data": data, "contact": credential("OFFICEKIT_CONTACT")}
                    if g("symbol"):
                        ctx["symbol"] = g("symbol").upper()
                    if g("symbols"):
                        ctx["symbols"] = [s.strip() for s in g("symbols").split(",") if s.strip()]
                    sig.run_capability(folder, g("name"), ctx)
                    build_office(answers, folder)
                except Exception as e:
                    return self._failure(e, context='signal:' + g('name') + ':' + g('symbol').upper(),
                                         href=f"/pages/capability_{g('name')}.html")
                return self._redirect(f"/pages/capability_{g('name')}.html")
            from officekit.strategy_routes import PATHS as _proposal_paths
            if self.path in _proposal_paths:
                from officekit.strategy_routes import handle as _proposal_handle
                from officekit.strategy_proposals import dispatch
                try:
                    with _OFFICE_WRITE_LOCK:
                        pid, start_job = _proposal_handle(self.path, folder, g, build_office, _capital_model)
                    if start_job:
                        if hosted():
                            from officekit.strategy_proposals import load, save
                            proposal = load(folder, pid)
                            if _ai(folder):
                                from officekit.runtime import enqueue_proposal
                                enqueue_proposal(pid)
                            else:
                                proposal.update(status="awaiting_key", stage="Ready for an AI agent key", errors=[])
                                save(folder, proposal)
                        else:
                            dispatch(folder, pid)
                except Exception as e:
                    return self._failure(e)
                return self._redirect(f"/pages/proposal_{pid}.html")
            if self.path == "/strategy/goal-unadopt":
                # the un-check: drop this goal's origin from the strategy. If that
                # leaves an un-held, un-decided-elsewhere strategy with no origins,
                # remove the decision entirely (a held/implemented one stays).
                try:
                    with _OFFICE_WRITE_LOCK:
                        answers = json.loads((folder / "answers.json").read_text())
                        from officekit.mandates import require_revision
                        require_revision(answers, g('revision'))
                        gid, sid = g("gid"), g("sid")
                        decs = answers.get("strategy_decisions") or {}
                        dec = decs.get(sid)
                        if dec:
                            dec["origins"] = [o for o in (dec.get("origins") or [])
                                              if not (o.get("source") == "goal" and o.get("ref") == gid)]
                            if not dec["origins"] and dec.get("status") != "implemented":
                                decs.pop(sid, None)
                        build_office(answers, folder)
                except Exception as e:
                    return self._failure(e)
                return self._redirect(f"/pages/strategies.html#goal-{g('gid')}")
            if self.path == "/docket":
                # F2: queue-for-court + budgeted drain — the court-on-touch rail
                try:
                    from officekit.personal_context import load as _pc_load, require
                    from officekit.render_strategies import STRATEGY_LIB
                    from officekit_ai import docket
                    answers = json.loads((folder / "answers.json").read_text())
                    sid = g("sid")
                    if g("action") == "queue":
                        docket.enqueue(folder, g("symbol"), sid, source="ui/strategy-form")
                    else:                                     # drain
                        if not _ai(folder, slot="bench"):
                            raise ValueError("Configure a usable bench model in office settings before requesting court review")
                        pc = require(_pc_load(folder), "convene a court")
                        if answers.get("office_id") and not pc.get("office_id"):
                            pc = {**pc, "office_id": answers["office_id"]}
                        import os
                        docket.drain(folder, pc,
                                     decisions=answers.get("strategy_decisions") or {},
                                     lib=STRATEGY_LIB,
                                     office_data=json.loads((folder / "balance_sheet.json").read_text()),
                                     contact=credential("OFFICEKIT_CONTACT"))
                    build_office(answers, folder)
                except Exception as e:
                    return self._failure(e)
                return self._redirect(f"/pages/strategies.html#strat-{g('sid')}")
            if self.path == "/court":
                try:
                    ai = _ai(folder, slot="bench")
                    if not ai:
                        raise ValueError("Configure a usable bench model in office settings before requesting court review")
                    from officekit.personal_context import load as _pc_load, require
                    from officekit.render_strategies import STRATEGY_LIB
                    from officekit_ai.court import run_court
                    answers = json.loads((folder / "answers.json").read_text())
                    pc = require(_pc_load(folder), "convene a court")
                    if answers.get("office_id") and not pc.get("office_id"):
                        pc = {**pc, "office_id": answers["office_id"]}
                    sid = g("sid")
                    dec = (answers.get("strategy_decisions") or {}).get(sid, {})
                    import os
                    run_court(g("symbol"), sid, dec, pc, folder, lib=STRATEGY_LIB.get(sid),
                              office_data=json.loads((folder / "balance_sheet.json").read_text()),
                              contact=credential("OFFICEKIT_CONTACT"))
                    build_office(answers, folder)      # re-render with the verdict on the card
                except Exception as e:
                    return self._failure(e)
                return self._redirect(f"/pages/strategies.html#strat-{g('sid')}")
            if self.path == "/holdings":
                try:
                    from officekit_ai.court import load_adjudications
                    answers = json.loads((folder / "answers.json").read_text())
                    adjs = [a for a in load_adjudications(folder) if a.get("subject_kind", "security") == "security"]
                    sid, sym = g("sid"), g("symbol").upper().strip()
                    record_purchase(answers, sid, sym, _money(g("amount")), adjs)
                    # PROPOSED is a source kind too (principal 2026-09-05):
                    # an asset born from the app's own deliberation gets a
                    # provenance row — the adjudication that proposed it, under
                    # which strategy, when — so the audit page traces it like
                    # any import. A later live-adapter pull of the same symbol
                    # supersedes it (the proposal became a broker position).
                    try:
                        from officekit import staging
                        adj = next((a for a in reversed(adjs)
                                    if a.get("strategy") == sid and a.get("symbol") == sym), None)
                        staging.record_pull(
                            folder, f"proposed:{sid}:{sym}", "proposed",
                            f"strategy {sid}", refresh="manual",
                            rows=[{"symbol": sym, "value": _money(g("amount")),
                                   "sec_type": "STK"}],
                            as_of=date.today().isoformat(),
                            detail=(f"adjudication {adj['id'][:8]} — {adj['verdict']}"
                                    if adj else "recorded purchase (no adjudication on file)"))
                    except Exception:
                        pass                          # provenance never blocks the purchase record
                    build_office(answers, folder)
                except Exception as e:
                    return self._failure(e)
                return self._redirect(f"/pages/strategies.html#strat-{g('sid')}")
            if self.path in {"/inflows/preview", "/inflows/apply"}:
                from officekit.inflow_routes import handle
                try:
                    with _OFFICE_WRITE_LOCK:
                        result = handle(self.path, form, folder, build_office, _capital_model)
                    if result.get("redirect"):
                        return self._redirect(result["redirect"])
                    return self._send(result["html"])
                except Exception as e:
                    return self._failure(e)
            if self.path in {"/commitments/update", "/commitments/add", "/commitments/preview", "/commitments/apply"}:
                from officekit.commitment_routes import handle
                try:
                    # A preview may call the model; it reads a frozen snapshot
                    # and gets revision-checked again at application time.
                    if self.path == "/commitments/preview":
                        result = handle(self.path, form, folder, build_office, bool(_ai(folder)))
                    else:
                        with _OFFICE_WRITE_LOCK:
                            result = handle(self.path, form, folder, build_office, bool(_ai(folder)))
                    if result.get("redirect"):
                        return self._redirect(result["redirect"])
                    return self._send(result["html"])
                except Exception as e:
                    return self._failure(e)
            if self.path == "/goals":
                try:
                    answers = json.loads((folder / "answers.json").read_text())
                    # PRESERVE goals the row-editor can't represent (tax_efficiency
                    # and any amount-less kind) — else a bulk save silently drops
                    # them (the overwrite bug, 2026-09-08).
                    EDITABLE = {"retirement", "spending", "liquidity_floor"}
                    kept = [g for g in (answers.get("goals") or []) if g.get("kind") not in EDITABLE]
                    answers["goals"] = kept + goals_from_form(form)
                    build_office(answers, folder)      # rebuild keeps everything durable
                except Exception as e:
                    return self._failure(e)
                # page-relative target: the form lives inside the shell's iframe
                return self._redirect("/pages/office.html")
            if self.path == "/goals/add":
                # add-on-enter: APPEND a goal (never rebuild the list, so it can't
                # overwrite) from plain words (nl) OR explicit fields, mint its id,
                # auto-link any EXISTING strategy that already serves its kind, and
                # rebuild. 2026-09-08.
                try:
                    import uuid
                    answers = json.loads((folder / "answers.json").read_text())
                    goals = answers.setdefault("goals", [])
                    new = []
                    nl = g("nl")
                    if nl:
                        if len(nl) > 8000:
                            raise ValueError("Describe your goals in 8,000 characters or fewer.")
                        if not _ai(folder):
                            raise ValueError("Connect an AI agent in Office settings to describe goals in words, or use the goal fields.")
                        from officekit_ai.intake_chat import turn
                        t = turn([{"role": "user", "content": nl}], folder=folder, scope="goals")
                        new = (t.get("answers") or {}).get("goals") or []
                        if not new:
                            raise ValueError(t.get("reply") or "No goal could be added. Include an amount and a target date, or use the goal fields.")
                    elif g("gkind"):
                        kind = g("gkind")
                        goal = {"kind": kind, "label": g("glabel") or kind.replace("_", " ").title()}
                        if g("gdate"):
                            goal["date"] = g("gdate")
                        amt = _money(g("gamt"))
                        if kind == "retirement" and amt is not None:
                            goal["annual_spending"] = amt
                        elif kind == "expense" and amt is not None:
                            goal["annual_amount"] = amt
                        elif kind not in ("tax_efficiency",) and amt is not None:
                            goal["amount"] = amt
                        new = [goal]
                    ids = []
                    for goal in new:
                        goal["id"] = str(uuid.uuid4())
                        goals.append(goal)
                        ids.append(goal["id"])
                    if ids and answers.get("strategy_decisions"):
                        _link_existing_strategies(answers, ids, folder)   # existing strategies serve it now
                    if ids:
                        build_office(answers, folder)
                except Exception as e:
                    return self._failure(e)
                return self._redirect("/pages/goals.html" if g("back") == "goals" else "/pages/office.html")
            if self.path == "/goals/mortgage":
                # Compatibility for old pages. Name lookup must be unambiguous;
                # current editors always send a stable commitment ID/revision.
                try:
                    from officekit.commitments import apply_edit, revision
                    with _OFFICE_WRITE_LOCK:
                        answers = json.loads((folder / "answers.json").read_text())
                        data = build_from_answers(answers)
                        matches = [c for c in data["commitments"] if c["source"] == "mortgage"
                                   and (not g("sleeve") or c.get("sleeve") == g("sleeve"))]
                        if len(matches) != 1:
                            raise ValueError("Select a specific mortgage from Capital & Commitments")
                        patch = {k: g(k) for k in ("rate_pct", "term_years") if g(k)}
                        updated = apply_edit(answers, matches[0]["id"], patch, g("revision") or revision(answers))
                        build_office(updated, folder)
                except Exception as e:
                    return self._failure(e)
                return self._redirect("/pages/office.html")
            if self.path == "/goals/remove":
                try:
                    answers = json.loads((folder / "answers.json").read_text())
                    gid = g("gid")
                    answers["goals"] = [x for x in (answers.get("goals") or []) if x.get("id") != gid]
                    build_office(answers, folder)
                except Exception as e:
                    return self._failure(e)
                return self._redirect("/pages/goals.html" if g("back") == "goals" else "/pages/office.html")
            if self.path == "/goal/params":
                # adjust a goal's own knobs (price, financing, carry, expense) from
                # its projection page, then re-run and land back on that page.
                try:
                    answers = json.loads((folder / "answers.json").read_text())
                    gid = g("gid")
                    for goal in answers.get("goals") or []:
                        if goal.get("id") != gid:
                            continue
                        if g("spending_basis") and goal.get("kind") == "retirement":
                            if g("spending_basis") not in {"household_total", "additional"}:
                                raise ValueError("Choose household total or additional spending")
                            goal["spending_basis"] = g("spending_basis")
                        if g("amount"):
                            goal["amount"] = _money(g("amount"))
                        if g("annual_amount"):
                            goal["annual_amount"] = _money(g("annual_amount"))
                        for k in ("down_pct", "rate_pct", "term_years"):
                            if g(k):
                                goal.setdefault("finance", {})[k] = _money(g(k))
                        for k in ("tax_pct", "maint_pct", "insurance_pct"):
                            if g(k):
                                goal.setdefault("carry", {})[k] = _money(g(k))
                        break
                    build_office(answers, folder)
                except Exception as e:
                    return self._failure(e)
                return self._redirect(f"/pages/goal_{g('gid')}.html")
            if self.path == "/growth":
                # save the target stock/bond mix (steers the growth calc + risk officer)
                try:
                    answers = json.loads((folder / "answers.json").read_text())
                    from officekit.portfolio_mix import validate_mix
                    answers["target_mix"] = validate_mix(g("stocks_pct"), g("bonds_pct"))
                    build_office(answers, folder)
                except Exception as e:
                    return self._failure(e)
                return self._redirect("/pages/growth.html")
            if self.path == "/harvest":
                # recompute the harvest with the chosen tax rate + selection and
                # return the rendered page directly (exploratory; nothing persisted)
                try:
                    from officekit import harvest as _hv
                    from officekit.render_harvest import render_harvest
                    data = load_balance_sheet(folder / "balance_sheet.json", strict=False)
                    m = build_model(data)
                    col = _hv.collect(m, folder)
                    rate = _money(g("tax_rate"))
                    if rate is None:
                        rate = float((data.get("tax_model") or {}).get("rate_ltcg") or 0.238)
                    sel = set(form.getlist("sel")) if form.getvalue("sel") is not None else set()
                    sim = _hv.simulate(col, sel, m, rate, data.get("as_of"))
                    return self._send(render_harvest(m, col, sim, rate))
                except Exception as e:
                    return self._failure(e)
            if self.path == "/assets":
                # add sleeves/holdings to a LIVE office (the office-page editor;
                # rows may be typed OR filled by the natural-language box via
                # /chat). APPENDS to answers, dedupes tickers by symbol, rebuilds.
                try:
                    answers = json.loads((folder / "answers.json").read_text())
                    kinds = form.getlist("u_kind") if form.getvalue("u_kind") is not None else []
                    names = form.getlist("u_name")
                    values = form.getlist("u_value")
                    rates = form.getlist("u_rate")
                    added, rows = 0, []
                    for i, kind in enumerate(kinds):
                        val = _money(values[i] if i < len(values) else "")
                        name = names[i].strip() if i < len(names) else ""
                        if not kind or val is None:
                            continue
                        if kind == "ticker":
                            if name:
                                rows.append({"symbol": name.upper(), "value": val})
                            continue
                        s = {"category": kind, "value": val}
                        if name:
                            s["name"] = name
                        if kind == "real_estate_debt":
                            s["style"] = "arm" if re.search(r"\barm\b|adjustable", name, re.I) else "fixed"
                            if i < len(rates) and rates[i].strip():
                                s["rate_pct"] = _money(rates[i].replace("%", "")) or None
                        answers.setdefault("sleeves", []).append(s)
                        added += 1
                    if rows:
                        pos = answers.setdefault("positions", {"account": "brokerage", "rows": []})
                        by = {r["symbol"].upper(): r for r in pos.get("rows", [])}
                        for r in rows:
                            by[r["symbol"].upper()] = r     # dedupe: same ticker updates, never doubles
                        pos["rows"] = list(by.values())
                    if added or rows:
                        build_office(answers, folder)
                except Exception as e:
                    return self._failure(e)
                return self._redirect("/pages/office.html")
            return self._send("not found", 404)

        def log_message(self, *a):    # quiet
            pass

    return Handler


def _daily_pull_loop(folder, interval_s=24 * 3600):
    """While the app runs, re-pull every AUTO source daily (principal
    2026-09-05: 'automatically pull the holdings on a daily interval'); the
    IMPORTS page's Pull-now buttons cover the manual case. Startup pulls only
    sources whose last pull is older than the interval — never a surprise
    fetch on every restart. Failures log and wait for the next cycle."""
    import time as _t
    from datetime import datetime, timezone
    while True:
        try:
            from officekit import staging
            pulled_any = False
            import officekit_adapters
            for sid, src in list(staging.load(folder).get("sources", {}).items()):
                if src.get("refresh") != "auto" or not sid.startswith("adapter:"):
                    continue
                name = sid.split(":", 1)[1]
                if not officekit_adapters.ADAPTERS.get(name, {}).get("auto", True):
                    continue                          # manual-only (e.g. downloads_csv): never auto-pull
                try:
                    age = (datetime.now(timezone.utc)
                           - datetime.fromisoformat(src["pulled_utc"])).total_seconds()
                except Exception:
                    age = interval_s + 1
                if age <= interval_s:
                    continue
                try:
                    import officekit_adapters
                    snapshot = officekit_adapters.fetch_snapshot(name)
                    rows = snapshot["rows"]
                    staging.record_pull(folder, sid, "adapter", src.get("ref", name), rows,
                                        refresh="auto", as_of=snapshot["as_of"], snapshot=snapshot["snapshot"],
                                        detail=f"{len(rows)} rows via daily auto-pull")
                    write_imports_page(folder)
                    pulled_any = True
                    print(f"[serve] daily pull {name}: {len(rows)} rows")
                except Exception as e:
                    staging.record_failure(folder, sid, e)
                    write_imports_page(folder)
                    print(f"[serve] daily pull {name} FAILED: {type(e).__name__}: {e}")
            # once anything refreshed, sync the office balance sheet to it
            if pulled_any and (folder / "balance_sheet.json").exists():
                try:
                    s = sync_office_from_staging(folder)
                    print(f"[serve] daily sync: {s['changed']} refreshed, {s['added']} new")
                except Exception as e:
                    print(f"[serve] daily sync FAILED: {type(e).__name__}: {e}")
            # (the office no longer polls the desk board — thesis sleeves are assembled
            # office-native from adjudications + the owned snapshot; the desk board
            # enters only via the explicit /import/desk-board action. 2026-09-11.)
        except Exception as e:
            print(f"[serve] daily pull loop error: {type(e).__name__}: {e}")
        _t.sleep(3600)                               # check hourly, pull when a source ages out


def _watched_py_mtimes():
    """Every .py under the officekit packages — the reloader's watch set."""
    import officekit
    pkgs = ["officekit", "officekit_ai", "officekit_adapters",
            "officekit_research", "officekit_signals", "officekit_agents"]
    mt = {}
    for name in pkgs:
        try:
            mod = __import__(name)
            root = Path(mod.__file__).parent
        except Exception:
            continue
        for p in root.rglob("*.py"):
            try:
                mt[str(p)] = p.stat().st_mtime
            except OSError:
                pass
    return mt


def _reload_supervisor(argv):
    """Dev auto-reload (Flask/Django pattern, stdlib-only): run the server as a
    CHILD process and re-spawn it whenever a watched .py changes — so even edits
    to serve.py take effect without you restarting. Polls mtimes (no watchdog
    dependency). Ctrl-C stops both."""
    import subprocess
    import time as _t
    child_env = dict(os.environ, OFFICEKIT_RELOAD_CHILD="1")
    cmd = [sys.executable, "-m", "officekit.serve"] + list(argv or [])

    def spawn():
        return subprocess.Popen(cmd, env=child_env)

    print("[serve] auto-reload ON — watching officekit sources; edit and save to reload")
    proc = spawn()
    mtimes = _watched_py_mtimes()
    try:
        while True:
            _t.sleep(1.0)
            if proc.poll() is not None:              # child died on its own (e.g. syntax error)
                print("[serve] server exited; waiting for a source change to retry…")
                while _watched_py_mtimes() == mtimes:
                    _t.sleep(1.0)
                mtimes = _watched_py_mtimes()
                proc = spawn()
                continue
            now = _watched_py_mtimes()
            changed = [p for p, m in now.items() if mtimes.get(p) != m]
            if changed:
                print(f"[serve] change detected ({Path(changed[0]).name}"
                      + (f" +{len(changed)-1} more" if len(changed) > 1 else "") + ") — reloading")
                proc.terminate()
                try:
                    proc.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    proc.kill()
                mtimes = now
                proc = spawn()
    except KeyboardInterrupt:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="worker-placement serve", description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default="./office", help="office folder (created if missing)")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--reload", action="store_true",
                    help="auto-reload on source changes (dev) — no manual restart")
    args = ap.parse_args(argv)
    # the parent supervisor watches + re-spawns; the child (or a plain run)
    # actually serves. The child is marked by OFFICEKIT_RELOAD_CHILD.
    if args.reload and not os.environ.get("OFFICEKIT_RELOAD_CHILD"):
        return _reload_supervisor(["--dir", args.dir, "--port", str(args.port)])
    folder = Path(args.dir)
    folder.mkdir(parents=True, exist_ok=True)
    from officekit import cloud_sync as sync
    from officekit.office_lock import locked
    with locked(folder):
        sync.recover(folder)
    threading.Thread(target=sync.loop, args=(folder,), daemon=True, name="office-sync").start()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(folder))
    threading.Thread(target=_daily_pull_loop, args=(folder,), daemon=True).start()
    tag = " (auto-reload child)" if os.environ.get("OFFICEKIT_RELOAD_CHILD") else ""
    print(f"[serve] Worker Placement: http://localhost:{args.port}  (folder: {folder.resolve()}){tag}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
