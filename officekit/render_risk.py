"""render_risk — the Risk Officer page. It ADVISES, never vetoes."""
from __future__ import annotations

from officekit.fmt import esc, fmt_usd as _fmt
from officekit.portfolio_mix import current_mix, mix_stats

CSS = """
body{margin:0;background:#0b0e12;color:#e8ebee;font:14px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.wrap{max-width:940px;margin:0 auto;padding:26px 24px 90px}
a{color:#b1a5ff} h1{font-size:23px;margin:0 0 4px;letter-spacing:-.02em}
.sub{color:#9aa4b0;margin:0 0 18px;font-size:13px}
h2{font-size:11.5px;text-transform:uppercase;letter-spacing:.12em;color:#9aa4b0;margin:26px 0 10px}
.stats{display:flex;gap:26px;flex-wrap:wrap;margin-bottom:6px}
.stat .l{font-size:10.5px;color:#9aa4b0;text-transform:uppercase;letter-spacing:.09em}
.stat .n{font:660 20px/1.1 ui-monospace,Menlo,monospace;margin-top:3px}
.f{border-left:3px solid #8a939e;background:#14181d;border-radius:0 12px 12px 0;padding:12px 16px;margin-bottom:10px}
.f.high{border-color:#e0736a} .f.medium{border-color:#d9a441} .f.low{border-color:#8a939e} .f.info{border-color:#4f7cf0}
.f .t{font-weight:600;font-size:14px} .f .d{color:#c7ccd2;font-size:12.5px;margin-top:3px}
.f .a{color:#9aa4b0;font-size:12px;margin-top:5px} .f .a b{color:#8ee5c1;font-weight:600}
.sev{font-size:9px;font-weight:700;letter-spacing:.06em;padding:2px 7px;border-radius:20px;margin-left:6px;vertical-align:middle}
.sev.high{color:#f0b3ad;background:rgba(224,115,106,.16)} .sev.medium{color:#eccb8a;background:rgba(217,164,65,.16)}
.sev.low{color:#b3bcc6;background:rgba(138,147,158,.16)} .sev.info{color:#a9c0f5;background:rgba(79,124,240,.16)}
.act{display:inline-block;margin-top:6px;font-size:11.5px;color:#8ee5c1;text-decoration:none;border-bottom:1px dashed rgba(53,201,143,.45)}
.act:hover{color:#35c98f}
.ok{color:#35c98f}
"""


def render_risk(m, findings, answers=None, growth_href="/pages/growth.html"):
    cur = current_mix(m)
    st = mix_stats(cur["stocks_pct"], cur["bonds_pct"])
    n_high = sum(1 for f in findings if f["severity"] == "high")
    P = [f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
         f'<meta name="viewport" content="width=device-width,initial-scale=1">'
         f'<title>Risk Officer</title><style>{CSS}</style></head><body><div class="wrap">'
         '<h1>Risk Officer</h1>'
         '<p class="sub">A standing read on where the book is exposed — concentration, mix, goal '
         'conflicts, liquidity, leverage, tax. It advises; you decide.</p>']

    P.append('<div class="stats">'
             f'<div class="stat"><div class="l">Findings</div><div class="n">{len(findings)}</div></div>'
             f'<div class="stat"><div class="l">High</div><div class="n" style="color:'
             f'{"#e0736a" if n_high else "#35c98f"}">{n_high}</div></div>'
             f'<div class="stat"><div class="l">Equity / vol</div>'
             f'<div class="n">{cur["stocks_pct"]:.0f}% · {st["vol"]*100:.0f}%</div></div>'
             f'<div class="stat"><div class="l">1-in-20 drawdown</div>'
             f'<div class="n">-{st["drawdown_1in20"]*100:.0f}%</div></div>'
             '</div>')
    P.append(f'<p class="sub">Current holdings: stocks {cur["stocks_pct"]:.1f}% · bonds {cur["bonds_pct"]:.1f}% · '
             f'cash {cur["cash_pct"]:.1f}% — preview a target in the '
             f'<a href="{esc(growth_href)}">growth calculator</a>.</p>')

    P.append('<h2>Findings</h2>')
    if m["d"].get("commitments"):
        from officekit.goal_projection import _existing_debt_service
        P.append(f'<p class="sub">Fixed commitments reserve {_fmt(_existing_debt_service(m))}/yr from the portfolio '
                 'before discretionary goals. '
                 '<a href="/pages/capital.html">Review payments and funding sources →</a></p>')
    if not findings:
        P.append('<div class="f low"><div class="t ok">No flags — the book is within tolerances.</div></div>')
    for f in findings:
        sev = f["severity"]
        act = ""
        a = f.get("action")
        if a:
            href = growth_href if a.get("kind") == "growth" else a.get("href", "#")
            act = f'<a class="act" href="{esc(href)}">{esc(a.get("label") or "act on this")} →</a>'
        P.append(f'<div class="f {sev}"><div class="t">{esc(f["title"])}'
                 f'<span class="sev {sev}">{sev.upper()}</span></div>'
                 f'<div class="d">{esc(f["detail"])}</div>'
                 f'<div class="a"><b>Advice:</b> {esc(f["advice"])}</div>{act}</div>')

    P.append('<p class="sub" style="margin-top:18px">The Risk Officer never places orders or blocks a '
             'decision — it surfaces the trade-offs. An allocation-court agent (a second opinion on the '
             'hardest conflicts) is the planned next layer.</p>')
    P.append('</div></body></html>')
    return "".join(P)
