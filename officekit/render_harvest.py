"""render_harvest — the whole-portfolio loss-harvesting page."""
from __future__ import annotations

from officekit.fmt import esc, fmt_usd as _fmt

CSS = """
body{margin:0;background:#0b0e12;color:#e8ebee;font:14px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.wrap{max-width:980px;margin:0 auto;padding:26px 24px 90px}
a{color:#b1a5ff} h1{font-size:23px;margin:0 0 4px;letter-spacing:-.02em}
.sub{color:#9aa4b0;margin:0 0 18px;font-size:13px}
h2{font-size:11.5px;text-transform:uppercase;letter-spacing:.12em;color:#9aa4b0;margin:26px 0 10px}
.panel{background:#14181d;border:1px solid #242a31;border-radius:14px;padding:16px 18px;margin-bottom:14px}
.stats{display:flex;gap:26px;flex-wrap:wrap}
.stat .l{font-size:10.5px;color:#9aa4b0;text-transform:uppercase;letter-spacing:.09em}
.stat .n{font:660 24px/1.1 ui-monospace,Menlo,monospace;margin-top:3px}
table{width:100%;border-collapse:collapse;font-size:13px}
td,th{padding:8px 10px;border-bottom:1px solid #242a31;text-align:left}
th{font-size:10.5px;text-transform:uppercase;letter-spacing:.08em;color:#9aa4b0}
td.n,th.n{text-align:right;font-family:ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums}
.loss{color:#e0736a} .pos{color:#35c98f}
.k{font-size:10px;font-weight:700;letter-spacing:.05em;padding:2px 7px;border-radius:20px}
.k-known{color:#8ee5c1;background:rgba(53,201,143,.14)} .k-unknown{color:#b3bcc6;background:rgba(138,147,158,.14)}
.note{font-size:11.5px;color:#9aa4b0;line-height:1.55;margin-top:10px}
input[type=number]{width:80px;background:#1a1f25;color:#e8ebee;border:1px solid #242a31;border-radius:8px;padding:6px 8px}
.btn{background:#35c98f;color:#08110d;border:0;border-radius:9px;padding:9px 18px;font-weight:700;cursor:pointer}
.big{font-size:40px;color:#35c98f}
.warn{background:rgba(217,164,65,.08);border:1px solid rgba(217,164,65,.4);border-radius:14px;padding:14px 18px;margin-bottom:14px}
.warn h2{color:#d9a441;margin-top:0}
.warn.hi{background:rgba(224,115,106,.09);border-color:rgba(224,115,106,.45)}
.warn.hi h2{color:#e0736a}
.washrev{margin-bottom:14px}.washrev>summary{cursor:pointer;font-size:15px;font-weight:600;color:#eccb8a}.washrev[open]>summary{margin-bottom:12px}.washrev.hi>summary{color:#f0b3ad}.washrev .warn:last-child{margin-bottom:0}.panel{overflow-x:auto}
.warn ul{margin:6px 0 0;padding-left:18px} .warn li{margin:5px 0;font-size:12.5px;color:#c8ced4}
.wflag{color:#d9a441;cursor:help;margin-left:5px}
.k-wash{color:#e6bd6f;background:rgba(217,164,65,.16)}
"""


def render_harvest(m, collected, sim, tax_rate, endpoint="/harvest",
                   risk_href="/pages/risk.html"):
    pos = collected["positions"]
    known = [p for p in pos if p["known"] and p["loss"] > 0]
    unknown = [p for p in pos if not (p["known"] and p["loss"] > 0)]
    sel_ids = {p["id"] for p in sim["selected"]}
    P = [f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
         f'<meta name="viewport" content="width=device-width,initial-scale=1">'
         f'<title>Loss harvesting</title><style>{CSS}</style></head><body><div class="wrap">'
         '<h1>Loss harvesting</h1>'
         '<p class="sub">Every asset, not just Parametric — measured where lot basis exists, flagged '
         'where it doesn\'t. Harvested losses offset your incoming capital gain and the banked '
         f'carryforward. Feeds the <a href="{esc(risk_href)}">Risk Officer</a>.</p>']

    # headline — REALIZED (banked) vs HARVESTABLE (unrealized) are different things:
    # realized losses are already locked in and offset the gain no matter what;
    # harvesting converts more unrealized loss into realized. Show both.
    realized = sim.get("realized", 0.0)
    P.append('<div class="panel"><div class="stats">'
             f'<div class="stat"><div class="l">Realized YTD (banked)</div>'
             f'<div class="n loss">{_fmt(-realized)}</div></div>'
             f'<div class="stat"><div class="l">Harvestable now (unrealized)</div>'
             f'<div class="n loss">{_fmt(-collected.get("harvestable_total", 0))}</div></div>'
             f'<div class="stat"><div class="l">Total tax benefit</div>'
             f'<div class="n big">{_fmt(sim["tax_benefit"])}</div></div>'
             f'<div class="stat"><div class="l">Gain reserve before → after</div>'
             f'<div class="n">{_fmt(sim["reserve_before"])} → <span class="pos">{_fmt(sim["reserve_after"])}</span></div></div>'
             '</div>')
    bits = []
    if realized > 0:
        st, lt = sim.get("realized_st", 0), sim.get("realized_lt", 0)
        split = f' ({_fmt(st)} short-term + {_fmt(lt)} long-term)' if (st or lt) else ""
        bits.append(f'<b>{_fmt(realized)}</b> of losses are already <b>realized</b> this year{split} — a banked '
                    f'tax asset worth <b>{_fmt(sim.get("realized_benefit",0))}</b> against the '
                    f'{_fmt(sim["gross_gain"])} gain (it cuts the reserve to {_fmt(sim.get("reserve_banked", sim["reserve_before"]))} before you harvest anything more).')
        if st > 0 and sim.get("st_at_blended", 0) > 0:
            note = (f'The {_fmt(sim.get("st_at_blended", st))} of short-term losses apply at your LTCG '
                    f'rate ({tax_rate*100:.1f}%) — you have no short-term gains for them to offset.')
            if sim.get("st_premium_foregone", 0) > 0:
                note += (f' Against ordinary-rate ST gains (~{sim["ord_rate"]*100:.1f}%) they would be worth '
                         f'~<b>{_fmt(sim["st_premium_foregone"])}</b> more — a reason to realize ST gains before LT.')
            bits.append(note)
    if sim.get("carryforward", 0) > 0:
        bits.append(f'Prior-year carryforward: {_fmt(sim["carryforward"])}.')
    if sim["harvested_loss"] > 0:
        bits.append(f'Harvesting {_fmt(sim["harvested_loss"])} more adds '
                    f'{_fmt(sim.get("harvest_benefit",0))}, taking the reserve to '
                    f'<span class="pos">{_fmt(sim["reserve_after"])}</span>.')
    if sim["residual_carryforward"] > 0:
        bits.append(f'Losses beyond the gain — <b>{_fmt(sim["residual_carryforward"])}</b> — carry forward '
                    f'as a deferred tax asset worth ~<b>{_fmt(sim["tax_asset"])}</b> against future gains '
                    f'(no federal expiry).')
    P.append(f'<div class="note">{" ".join(bits)}</div></div>')

    # cross-account wash-sale warnings (per-symbol overlaps + standing SMA caution)
    wash = collected.get("wash_risk") or {}
    has_wash_review = bool(wash.get("warnings") or wash.get("standing") or wash.get("multi_account"))
    if has_wash_review:
        tone = ' hi' if any(w.get('severity') == 'high' for w in wash.get('warnings', [])) else ''
        P.append(f'<details class="washrev{tone}"><summary>Review wash-sale exposure before harvesting</summary>'
                 '<p class="note">Cross-account positions and SMA activity can affect these losses. '
                 'The checks below may refer to the same holding from different perspectives.</p>')
    wash_syms = {}
    if wash.get("warnings"):
        hi = any(w["severity"] == "high" for w in wash["warnings"])
        P.append(f'<div class="warn{" hi" if hi else ""}">'
                 f'<h2>⚠ Possible wash sales between accounts</h2>'
                 '<div class="note" style="margin:2px 0 4px;color:#c8ced4">Selling a loss here can be '
                 'disallowed if the same security is bought — manually, by dividend reinvestment, or by an '
                 'SMA rebalance — in another account within ±30 days. Verify before harvesting these:</div><ul>')
        for w in wash["warnings"]:
            wash_syms[w["symbol"]] = w
            P.append(f'<li><b>{esc(w["symbol"])}</b> (loss {_fmt(w["loss"])}) — held in '
                     f'{esc(", ".join(w["accounts"]))}: {esc(w["note"])}</li>')
        P.append('</ul></div>')
    for s in (wash.get("standing") or []):
        P.append(f'<div class="warn"><h2>⚠ Direct-index SMA wash exposure</h2>'
                 f'<div class="note" style="margin:2px 0 0;color:#c8ced4">{esc(s["note"])}</div></div>')

    # stocks held in MULTIPLE ACCOUNTS — every one is a wash-sale trap the moment you
    # harvest it in one account while it's held/bought in another within ±30 days.
    ma = wash.get("multi_account") or []
    if ma:
        rows_ma = "".join(
            f'<li><b>{esc(x["symbol"])}</b> — {esc(", ".join(x["accounts"]))}'
            + ('<span class="g"> · incl. a direct-index SMA (actively traded)</span>' if x.get("sma") else "")
            + '</li>' for x in ma[:40])
        more = f'<div class="note" style="margin:6px 0 0">…and {len(ma)-40} more.</div>' if len(ma) > 40 else ""
        P.append('<div class="warn"><h2>⚠ Stocks held in multiple accounts</h2>'
                 f'<div class="note" style="margin:2px 0 4px;color:#c8ced4">{len(ma)} name(s) sit in more than '
                 'one account. Harvesting a loss on any of them in one account is a wash sale if the same name '
                 'is bought (or an SMA rebalances into it) in another within ±30 days — coordinate the sale, or '
                 'harvest a different lot.</div><ul>' + rows_ma + '</ul>' + more + '</div>')

    if has_wash_review:
        P.append('</details>')

    # candidates + controls
    P.append(f'<form method="POST" action="{esc(endpoint)}">'
             '<h2>Harvestable positions</h2><div class="panel">'
             '<div style="display:flex;gap:12px;align-items:center;margin-bottom:8px">'
             f'<label class="note" style="margin:0">Tax rate <input type="number" step="0.001" min="0" max="1" '
             f'name="tax_rate" value="{tax_rate:.3f}"></label>'
             '<button class="btn" type="submit">Re-run</button>'
             '<span class="note" style="margin:0">check the losses to harvest</span></div>')
    if known:
        P.append('<table><tr><th style="width:32px"></th><th>Asset</th><th>Type</th>'
                 '<th class="n">Value</th><th class="n">Harvestable loss</th><th>Lots</th><th>Term</th></tr>')
        for p in known:
            ck = "checked" if (p["id"] in sel_ids or not sim["selected"]) else ""
            # lot-level rows carry a real LT/ST split — show it (ST losses offset
            # ordinary-rate gains, so the split is the whole point of Flex basis)
            if p["term"] == "lot-level" and (p.get("lt") or p.get("st")):
                term_cell = (f'<span class="k k-known" title="long-term / short-term">'
                             f'LT {_fmt(p.get("lt") or 0)} · ST {_fmt(p.get("st") or 0)}</span>')
            else:
                term_cell = f'<span class="k k-known">{esc(str(p["term"]).upper())}</span>'
            wf = (f'<span class="wflag" title="{esc(wash_syms[p["label"].upper()]["note"])}">⚠</span>'
                  if p["label"].upper() in wash_syms else "")
            P.append(f'<tr><td><input type="checkbox" name="sel" value="{esc(p["id"])}" {ck}></td>'
                     f'<td style="font-weight:600">{esc(p["label"])}{wf}</td>'
                     f'<td>{esc(p["category"].replace("_"," "))}</td>'
                     f'<td class="n">{_fmt(p["value"] or 0)}</td>'
                     f'<td class="n loss">{_fmt(-p["loss"])}</td>'
                     f'<td>{p.get("n_lots") if p.get("n_lots") is not None else "—"}</td>'
                     f'<td>{term_cell}</td></tr>')
        P.append('</table>')
    else:
        P.append('<div class="note">No measured harvestable losses right now.</div>')
    if collected["carryforward"]:
        P.append(f'<div class="note">Plus a banked carryforward of {_fmt(collected["carryforward"])} '
                 '(already realized — offsets the gain directly).</div>')
    P.append('</div></form>')

    # factor-tilt drift
    P.append('<h2>Factor tilt — before vs after harvest</h2><div class="panel"><table>'
             '<tr><th>Factor</th><th class="n">Current tilt</th><th class="n">Post-harvest</th><th class="n">Δ</th></tr>')
    for f, row in sim["factor_drift"].items():
        big = abs(row["delta"]) > 0.03
        col = "#d9a441" if big else ("#35c98f" if row["delta"] >= 0 else "#e0736a")
        P.append(f'<tr><td style="font-weight:600">{esc(f)}</td>'
                 f'<td class="n">{row["before"]:+.2f}</td><td class="n">{row["after"]:+.2f}</td>'
                 f'<td class="n" style="color:{col};font-weight:700">{row["delta"]:+.2f}</td></tr>')
    P.append('</table><div class="note">Harvesting shifts the whole portfolio\'s factor tilt — the Risk '
             'Officer flags a drift that pulls you off your intended exposure.</div></div>')

    # concentration
    P.append('<h2>Concentration</h2><div class="panel"><div class="stats">'
             f'<div class="stat"><div class="l">Positions before → after</div>'
             f'<div class="n">{sim["positions_before"]} → {sim["positions_after"]}</div></div>'
             f'<div class="stat"><div class="l">HHI before → after</div>'
             f'<div class="n">{sim["hhi_before"]:.3f} → {sim["hhi_after"]:.3f}</div></div>'
             '</div></div>')

    # wash-sale lockout
    if sim["lockout"]:
        P.append('<h2>Wash-sale lockout — 31-day repurchase restriction</h2><div class="panel"><table>'
                 '<tr><th>Asset</th><th>Sale date</th><th>Earliest repurchase</th><th class="n">Loss</th></tr>')
        for r in sim["lockout"]:
            P.append(f'<tr><td style="font-weight:600">{esc(r["label"])}</td><td>{r["sale_date"]}</td>'
                     f'<td style="color:#d9a441">{r["earliest_repurchase"]}</td>'
                     f'<td class="n loss">{_fmt(-r["loss"])}</td></tr>')
        P.append('</table><div class="note">Sell the loss, then wait 31 days (or hold a correlated '
                 'not-substantially-identical proxy) to avoid a disallowed wash sale.</div></div>')

    # assets we can't measure
    measur_unknown = [p for p in unknown if p["value"] and p["value"] > 0]
    if measur_unknown:
        P.append('<h2>Not yet measurable</h2><div class="panel"><table>'
                 '<tr><th>Asset</th><th>Type</th><th class="n">Value</th><th>Why</th></tr>')
        for p in measur_unknown:
            P.append(f'<tr><td>{esc(p["label"])}</td><td>{esc(p["category"].replace("_"," "))}</td>'
                     f'<td class="n">{_fmt(p["value"])}</td>'
                     f'<td><span class="k k-unknown">BASIS NOT IMPORTED</span></td></tr>')
        P.append('</table><div class="note">Import lot-level cost basis (a broker taxlot export, or the '
                 'IMPORTS tab) to harvest these too.</div></div>')

    P.append('<p class="note">Estimates, not tax advice. A capital loss offsets capital gains (and up to '
             '$3,000 of ordinary income/yr); the rest carries forward. Long-term losses offset long-term '
             'gains first. Confirm timing and wash-sale substitutes with your preparer.</p>')
    P.append('</div></body></html>')
    return "".join(P)
