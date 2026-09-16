"""render_growth — the growth calculator / simulator.

Any "wait for the book to grow" path in the app lands here: the whole marketable
book, its stock/bond/cash split, and a projection you can steer by adjusting the
mix. Higher stocks → higher expected growth AND higher volatility; the page shows
both, and the same mix feeds the Risk Officer.
"""
from __future__ import annotations

from officekit.fmt import esc, fmt_usd as _fmt
from officekit.portfolio_mix import current_mix, mix_stats, target_mix, validate_mix
import json

CSS = """
body{margin:0;background:#0b0e12;color:#e8ebee;font:14px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.wrap{max-width:940px;margin:0 auto;padding:26px 24px 90px}
a{color:#b1a5ff} h1{font-size:23px;margin:0 0 4px;letter-spacing:-.02em}
.sub{color:#9aa4b0;margin:0 0 18px;font-size:13px}
h2{font-size:11.5px;text-transform:uppercase;letter-spacing:.12em;color:#9aa4b0;margin:26px 0 10px}
.panel{background:#14181d;border:1px solid #242a31;border-radius:14px;padding:16px 18px;margin-bottom:14px}
.stats{display:flex;gap:26px;flex-wrap:wrap}
.stat .l{font-size:10.5px;color:#9aa4b0;text-transform:uppercase;letter-spacing:.09em}
.stat .n{font:660 21px/1.1 ui-monospace,Menlo,monospace;margin-top:3px}
.bar{display:flex;height:26px;border-radius:8px;overflow:hidden;margin:8px 0}
.bar .s{background:#4f7cf0} .bar .b{background:#35c98f} .bar .c{background:#8a939e}
.bar span{display:flex;align-items:center;justify-content:center;font-size:10.5px;color:#08110d;font-weight:700}
label.f{display:block;font-size:11px;color:#9aa4b0;margin-top:10px}
input[type=range]{width:100%}
input[type=number]{width:80px;background:#1a1f25;color:#e8ebee;border:1px solid #242a31;border-radius:8px;padding:6px 8px}
.note{font-size:11.5px;color:#9aa4b0;line-height:1.55;margin-top:10px}
.btn{background:#35c98f;color:#08110d;border:0;border-radius:9px;padding:9px 18px;font-weight:700;cursor:pointer}
"""


def _fan(v0, ret, vol, years=20, W=640, H=240):
    PL, PR, PT, PB = 54, 16, 12, 24
    lines = {"exp": ret, "up": ret + vol, "dn": max(-0.5, ret - vol)}
    series = {k: [v0 * (1 + r) ** t for t in range(years + 1)] for k, r in lines.items()}
    ymax = max(series["up"]) * 1.05 or 1
    def px(t): return PL + t / years * (W - PL - PR)
    def py(v): return H - PB - (v / ymax) * (H - PT - PB)
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" style="max-width:{W}px">',
           f'<line x1="{PL}" y1="{H-PB}" x2="{W-PR}" y2="{H-PB}" stroke="#242a31"/>']
    for key, color, wdt in (("up", "#2a3550", 1), ("dn", "#2a3550", 1), ("exp", "#4f7cf0", 2)):
        pts = " ".join(f"{px(t):.1f},{py(v):.1f}" for t, v in enumerate(series[key]))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{wdt}"/>')
    out.append(f'<text x="{W-PR}" y="{py(series["exp"][-1])-4:.1f}" fill="#4f7cf0" font-size="10" '
               f'text-anchor="end">{_fmt(series["exp"][-1])} expected</text>')
    out.append(f'<text x="{W-PR}" y="{py(series["up"][-1])-4:.1f}" fill="#9aa4b0" font-size="9" '
               f'text-anchor="end">{_fmt(series["up"][-1])} (+1σ)</text>')
    for v in (v0, ymax):
        out.append(f'<text x="{PL-6}" y="{py(v)+3:.1f}" fill="#9aa4b0" font-size="9" text-anchor="end">{_fmt(v)}</text>')
    out.append(f'<text x="{PL}" y="{H-8}" fill="#9aa4b0" font-size="9">now</text>')
    out.append(f'<text x="{W-PR}" y="{H-8}" fill="#9aa4b0" font-size="9" text-anchor="end">+{years}y</text>')
    out.append('</svg>')
    return "".join(out)


def render_growth(m, answers, endpoint="/growth", office_href="/pages/office.html",
                  risk_href="/pages/risk.html"):
    cur = current_mix(m)
    tm = target_mix(answers, m)
    st = mix_stats(tm["stocks_pct"], tm["bonds_pct"], tm["cash_pct"])
    v0 = cur["total"]
    warning = ""
    if answers.get("target_mix"):
        try:
            saved = answers["target_mix"]
            validate_mix(saved.get("stocks_pct"), saved.get("bonds_pct"), saved.get("cash_pct"))
        except (ValueError, TypeError, AttributeError):
            warning = '<div class="panel" role="alert" style="border-color:#d9a441">Your saved target is invalid. This preview starts from the current allocation. Review and save a valid mix to replace it.</div>'
    P = [f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
         f'<meta name="viewport" content="width=device-width,initial-scale=1">'
         f'<title>Growth calculator</title><style>{CSS}</style></head><body><div class="wrap">'
         f'<p class="sub"><a href="{esc(office_href)}">← office</a> · '
         f'<a href="{esc(risk_href)}">risk officer →</a></p>'
         '<h1>Growth calculator</h1>'
         f'<p class="sub">Your {_fmt(v0)} marketable book, and where it goes as you steer the '
         'stock/bond mix. More stocks means more expected growth and more volatility.</p>']

    P.append(warning)

    # current split bar
    P.append('<h2>Marketable book today</h2><div class="panel">')
    P.append('<div class="bar">'
             + (f'<div class="s" style="width:{cur["stocks_pct"]}%"><span>{("Stocks " + format(cur["stocks_pct"], ".1f") + "%") if cur["stocks_pct"] > 15 else ""}</span></div>'
                if cur["stocks_pct"] > 0 else "")
             + (f'<div class="b" style="width:{cur["bonds_pct"]}%"><span>{("Bonds " + format(cur["bonds_pct"], ".1f") + "%") if cur["bonds_pct"] > 15 else ""}</span></div>'
                if cur["bonds_pct"] > 0 else "")
             + (f'<div class="c" style="width:{cur["cash_pct"]}%"><span>{("Cash " + format(cur["cash_pct"], ".1f") + "%") if cur["cash_pct"] > 15 else ""}</span></div>'
                if cur["cash_pct"] > 0 else "")
             + '</div>')
    P.append(f'<div class="note">Stocks {_fmt(cur["stocks"])} ({cur["stocks_pct"]:.1f}%) · Bonds {_fmt(cur["bonds"])} ({cur["bonds_pct"]:.1f}%) · '
             f'Cash {_fmt(cur["cash"])} ({cur["cash_pct"]:.1f}%). Pending inflows and private assets are excluded.</div></div>')

    # projection + adjustable mix
    P.append('<h2>Projection at your target mix</h2><div class="panel">')
    P.append('<div class="stats">'
             f'<div class="stat"><div class="l">Expected return</div><div class="n" id="preview-return">{st["exp_return"]*100:.1f}%/yr</div></div>'
             f'<div class="stat"><div class="l">Volatility</div><div class="n" id="preview-vol">{st["vol"]*100:.0f}%</div></div>'
             f'<div class="stat"><div class="l">1-in-20 drawdown</div><div class="n" id="preview-drawdown">-{st["drawdown_1in20"]*100:.0f}%</div></div>'
             f'<div class="stat"><div class="l">Book in 20y (exp.)</div><div class="n" id="preview-value">{_fmt(v0*(1+st["exp_return"])**20)}</div></div>'
             '</div>')
    P.append('<div id="growth-chart" aria-label="Twenty year modeled growth projection">' + _fan(v0, st["exp_return"], st["vol"]) + '</div>')
    P.append(f'<form method="POST" action="{esc(endpoint)}" id="mixform">'
             f'<label class="f" for="stocks-mix">Stocks: <b id="sv">{tm["stocks_pct"]:g}</b>%</label>'
             f'<input id="stocks-mix" type="range" name="stocks_pct" min="0" max="100" step="0.1" value="{tm["stocks_pct"]:g}">'
             f'<label class="f" for="bonds-mix">Bonds: <b id="bv">{tm["bonds_pct"]:g}</b>%</label>'
             f'<input id="bonds-mix" type="range" name="bonds_pct" min="0" max="100" step="0.1" value="{tm["bonds_pct"]:g}">'
             f'<p>Cash: <b id="cv">{tm["cash_pct"]:g}</b>% <span class="note">· Total <b id="mix-total">100%</b></span></p>'
             '<div class="note">Moving either slider reduces the other if needed to keep the total at 100%. '
             'The figures and chart preview your changes immediately.</div>'
             '<p id="mix-status" class="note" role="status" aria-live="polite">Preview · no changes saved</p>'
             '<button class="btn" type="submit" style="margin-top:10px">Save target mix</button></form>')
    from officekit import portfolio_mix as pm
    config = {"value": v0, "sr": pm.STOCK_RET, "br": pm.BOND_RET, "cr": pm.CASH_RET,
              "sv": pm.STOCK_VOL, "bv": pm.BOND_VOL, "cv": pm.CASH_VOL, "correlation": pm.SB_CORR}
    P.append('<script>const MIX_CONFIG=' + json.dumps(config) + ';</script>')
    P.append("""<script>
(function(){
 const c=MIX_CONFIG, stocks=document.getElementById('stocks-mix'), bonds=document.getElementById('bonds-mix');
 const text=(id,value)=>document.getElementById(id).textContent=value;
 const dollars=v=>new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',notation:'compact',maximumFractionDigits:2}).format(v);
 function preview(changed){
   let s=Number(stocks.value),b=Number(bonds.value);
   if(s+b>100){if(changed===stocks){b=100-s;bonds.value=b;}else{s=100-b;stocks.value=s;}}
   const cash=Math.max(0,100-s-b), ws=s/100, wb=b/100, wc=cash/100;
   const ret=ws*c.sr+wb*c.br+wc*c.cr;
   const vol=Math.sqrt((ws*c.sv)**2+(wb*c.bv)**2+(wc*c.cv)**2+2*ws*wb*c.sv*c.bv*c.correlation);
   text('sv',s.toFixed(1));text('bv',b.toFixed(1));text('cv',cash.toFixed(1));
   text('preview-return',(100*ret).toFixed(1)+'%/yr');text('preview-vol',(100*vol).toFixed(0)+'%');
   text('preview-drawdown','−'+(100*Math.min(.95,1.645*vol)).toFixed(0)+'%');text('preview-value',dollars(c.value*(1+ret)**20));
   const rates=[ret+vol,Math.max(-.5,ret-vol),ret];
   const series=rates.map(r=>Array.from({length:21},(_,t)=>c.value*(1+r)**t));
   const max=Math.max(...series[0])*1.05||1, px=t=>54+t/20*570,py=v=>216-v/max*204;
   const lines=series.map((vs,i)=>'<polyline points="'+vs.map((v,t)=>px(t)+','+py(v)).join(' ')+'" fill="none" stroke="'+(i===2?'#78a0ff':'#53637e')+'" stroke-width="'+(i===2?2:1)+'"/>').join('');
   document.getElementById('growth-chart').innerHTML='<svg viewBox="0 0 640 240" width="100%" role="img" aria-label="Expected growth and illustrative range"><line x1="54" y1="216" x2="624" y2="216" stroke="#424b56"/>'+lines+'<text x="54" y="234" fill="#9aa4b0" font-size="10">Today · '+dollars(c.value)+'</text><text x="624" y="234" text-anchor="end" fill="#9aa4b0" font-size="10">20 years · '+dollars(series[2][20])+' expected</text></svg>';
   text('mix-status','Unsaved preview · save to apply this target');
 }
 stocks.addEventListener('input',()=>preview(stocks));bonds.addEventListener('input',()=>preview(bonds));
})();
</script>""")
    P.append('</div>')

    P.append('<p class="note">Expected returns and volatility are first-pass house estimates, not a '
             'forecast. The band is ±1σ per year, compounded — a rough cone, not a guarantee. Compare your target with '
             'current holdings in the <a href="' + esc(risk_href) + '">Risk Officer</a>.</p>')
    P.append('</div></body></html>')
    return "".join(P)
