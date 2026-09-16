"""render_scenarios — the Scenario Planner page (the desk's SCENARIOS tab).

Renamed from render_disaster (principal-ratified 2026-09-02): the engine hosts
market, tax, income, and life-event scenarios — "disaster" was always just
"scenario with a bad sign". Worst-first framing stays.

Ported from the original desk/disaster.py build() (Phase-0 extraction, byte-parity tested).
Runs on the SAME build_model() output as the office dashboard, so the two never
drift. Scenario prose, playbook lead, liquidity read, and mitigation labels are
personalized through the data dict (see officekit.scenarios / schema); the engine
holds only the math and the generic library. READ-ONLY — never places orders.
"""
from __future__ import annotations

import json

from officekit import effects
from officekit import goals as goals_mod
from officekit.fmt import esc, fmt_usd as _fmt
from officekit.mitigations import (OPT, OPT_STRATEGY, FIT_TONE, PRESETS, default_preset,
                                   exposures, fit as _fit)
from officekit.scenarios import TAG_TONE, scenarios_for

# sleeves whose NOMINAL value doesn't move in a market shock (cash is flat; a fixed
# mortgage / accrued tax reserve is a fixed claim, not a marked asset).
NOMINAL_FIXED = {"cash", "cash_pending", "tax_reserve", "real_estate_debt"}

# liquidity tier by category
LIQ = {"cash": "now", "cash_pending": "sept", "public_equity": "mkt", "direct_index": "mkt",
       "single_name_equity": "mkt", "municipal_credit": "mkt", "fixed_income": "mkt",
       "alpha_market_neutral": "mkt", "venture_private": "frozen", "real_estate": "frozen",
       "tax_reserve": "claim", "real_estate_debt": "claim",
       "human_capital": "income"}   # you cannot sell your career — excluded from every liquidity sum

# effect id -> display icon (registry presentation, not client data)
ICON = {"tax_harvest_hedge": "🌾", "fixed_debt_rate_short": "🏠", "illiquid_mark_lag": "🕰️",
        "short_book_rotation": "⚖️", "correlation_compression": "🔗"}

# generic default prose — a client's data["scenario_text"] overlay replaces any of
# these (the legacy "disaster" key is still honored)
DEFAULT_TEXT = {
    "playbook_lead": "<b>Highest-leverage move (hits the top scenarios at once):</b> route new capital into sleeves "
                     "uncorrelated with the largest one — cuts it from <b>{p0}%</b> to <b>{p1}%</b> of invested (at-risk) capital at <b>$0 tax</b>.",
    # used instead of playbook_lead when there is no pending inflow (p0 == p1 —
    # a "cuts it from X to X" claim would be vacuous)
    "playbook_lead_static": "<b>Highest-leverage move (hits the top scenarios at once):</b> the largest sleeve is "
                            "<b>{p0}%</b> of invested (at-risk) capital — routing new savings into uncorrelated sleeves "
                            "is the cheapest dilution, at <b>$0 tax</b>.",
    "liquidity_read": "<b>Watch liquidity AND concentration.</b> Even a {dd_pct}% worst case leaves <b>{worst_access}</b> raisable "
                      "from cash + marketable holdings alone against {claims} of claims. An unlevered net buyer is never a forced seller: drawdowns are discounts.",
    "liquidity_note": "The real tail is <b>magnitude &amp; concentration</b>: the largest correlated block drives most of the worst-case loss. "
                      "Where a tax reserve exists it is <b>not</b> a fixed claim — a selloff spikes harvesting and shrinks it, in the worst case by "
                      "<b>~{thedge}</b>, an automatic cushion (see Microstructure below).",
    "liquidity_note_no_tax": "The real tail is <b>magnitude &amp; concentration</b>: the largest correlated block drives most of the "
                             "worst-case loss, and the natural hedges (bonds, cash) are usually the small sleeves. Diversifying new capital "
                             "into uncorrelated sleeves is the cheapest fix.",
    "claims_label": "Claims due (liabilities)",
    "foot": "Scenario shocks are CALIBRATED estimates applied through the sleeve factor-betas (first-pass, to refine from realized returns). "
            "Nominal marks: cash/pending held flat; fixed-rate debt held at principal; any tax reserve is scenario-responsive (shrinks as harvesting "
            "spikes — see Microstructure). Idiosyncratic scenario overrides layered on top. Mitigation costs are computed from the account's real "
            "exposures. The second-order effects are heuristics, flagged ENCODED (in the numbers) vs NOTED (context). Read-only — never places orders.",
}


def _move(s, scen):
    if s["category"] in NOMINAL_FIXED:
        return 0.0
    m = sum((s["beta"].get(f) or 0.0) * shk for f, shk in scen["shocks"].items())
    m += scen.get("cat_ov", {}).get(s["category"], 0.0)
    for key, ov in scen.get("name_ov", {}).items():
        if key in s["name"]:
            m += ov
    return max(m, -0.95)


def _pnlcell(pnl, scale):
    """Color a $ P&L cell: coral loss, emerald gain, intensity vs the scenario's worst."""
    if abs(pnl) < 1:
        return "background:rgba(138,145,153,.08)", "—"
    frac = min(1.0, abs(pnl) / scale) if scale else 0
    rgb = "53,201,143" if pnl > 0 else "224,115,106"
    return f"background:rgba({rgb},{0.12 + frac*0.5})", _fmt(pnl)


def applicable_scenarios(m):
    """The client's scenario set with data-preconditions applied — e.g. the
    tax-bomb needs a harvest offset at risk, the income shock needs a
    capitalized-income sleeve. Shared with the strategies page."""
    def _applicable(sc):
        req = sc.get("requires")
        if not req:
            return True
        if req == "tax_offset":
            return bool(m["tax"] and m["tax"]["offset"] > 0)
        if req == "human_capital":
            return any(s["category"] == "human_capital" for s in m["assets"])
        return True
    return [sc for sc in scenarios_for(m["d"]) if _applicable(sc)]


def compute_results(m):
    """The per-scenario stress results — one computation shared by the renderer
    and the learning ledger (predictions recorded = pixels rendered, so grading
    later grades what the user actually saw). Returns (SCEN, X, results) with
    results sorted worst-first."""
    sleeves = m["sleeves"]
    assets = m["assets"]
    SCEN = applicable_scenarios(m)
    # per-scenario results — DISPATCH the effects registry per scenario
    X = exposures(m)
    results = []
    for sc in SCEN:
        ctx = {"m": m, "sc": sc, "move": (lambda s, sc=sc: _move(s, sc)), "X": X}
        effs = effects.run(ctx)
        enc = {e["id"]: e for e in effs if e["kind"] == "ENCODED"}
        thedge = enc.get("tax_harvest_hedge", {}).get("delta", 0.0)
        # tax override: 'no_offset' snaps the reserve from net to gross — the offset IS the loss
        no_offset = bool(sc.get("tax_ov", {}).get("no_offset")) and m["tax"] is not None
        tax_delta = -m["tax"]["offset"] if no_offset else thedge
        rows = [(s, _move(s, sc), (tax_delta if s["category"] == "tax_reserve" else s["value"] * _move(s, sc)))
                for s in sleeves]
        # any ENCODED effect beyond the tax hedge (already in its row) also books to NW
        other_encoded = sum(e.get("delta", 0.0) for e in effs if e["kind"] == "ENCODED" and e["id"] != "tax_harvest_hedge")
        dd = sum(p for _, _, p in rows) + other_encoded
        # top bleeder / hedge among asset sleeves
        asset_rows = [(s, pct, p) for s, pct, p in rows if s["kind"] == "asset"]
        bleeder = min(asset_rows, key=lambda r: r[2])
        hedge = max(asset_rows, key=lambda r: r[2])
        # liquidity: cash flat + marketable at shocked marks (2% fire-sale haircut); frozen; claims
        cash_now = sum(s["value"] for s in assets if LIQ.get(s["category"]) == "now")
        sept = sum(s["value"] for s in assets if LIQ.get(s["category"]) == "sept")
        mkt = sum(s["value"] * (1 + _move(s, sc)) for s in assets if LIQ.get(s["category"]) == "mkt") * 0.98
        frozen = sum(s["value"] * (1 + _move(s, sc)) for s in assets if LIQ.get(s["category"]) == "frozen")
        results.append({"sc": sc, "rows": rows, "dd": dd, "nw_after": m["NW"] + dd,
                        "dd_pct": dd / m["NW"] * 100 if m["NW"] else 0,
                        "bleeder": bleeder, "hedge": hedge, "thedge": thedge, "effs": effs,
                        "cash_now": cash_now, "sept": sept, "mkt": mkt, "frozen": frozen})
    results.sort(key=lambda r: r["dd"])   # worst first
    return SCEN, X, results


def render_scenarios(m, effects_label="officekit/effects.py", strategies_href="strategies.html",
                     adopt_endpoint=None):
    sleeves, NW = m["sleeves"], m["NW"]
    assets = m["assets"]
    d = m["d"]
    eta = m["eta"]
    overlay = d.get("scenario_text") or d.get("disaster") or {}
    txt = {**DEFAULT_TEXT, **overlay}
    if m["tax"] is None and "liquidity_note" not in overlay:
        txt["liquidity_note"] = txt["liquidity_note_no_tax"]
    labels = d.get("mitigation_labels") or {}
    profile = d.get("profile") or {}
    default_pk = default_preset(profile)

    SCEN, X, results = compute_results(m)
    worst = results[0]
    # accessible liquidity in the worst scenario (pre-inflow, no illiquid)
    worst_access = worst["cash_now"] + worst["mkt"]
    claims = sum(-s["value"] for s in sleeves if s["kind"] == "liability")  # positive magnitude

    P = []
    P.append(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Scenario Planner</title>
<style>
:root{{--bg:#0b0e12;--panel:#14181d;--panel2:#1a1f25;--line:#242a31;--ink:#e8ebee;--dim:#9aa4b0;
--emerald:#35c98f;--violet:#b1a5ff;--amber:#d9a441;--coral:#e0736a;--slate:#8a939e}}
*{{box-sizing:border-box}} body{{margin:0;background:#0b0e12}}
a{{color:var(--violet);text-underline-offset:3px}} a:hover{{color:#d1caff}}
a:focus-visible,button:focus-visible,summary:focus-visible{{outline:2px solid var(--emerald);outline-offset:3px}}
.wrap{{max-width:1240px;margin:0 auto;padding:24px 24px 90px;font:14px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:var(--ink);background:var(--bg)}}
h1{{font-size:25px;margin:0 0 3px;letter-spacing:-.02em;font-weight:650}}
.sub{{color:var(--dim);font-size:13px;margin:0 0 22px}}
h2{{font-size:11.5px;text-transform:uppercase;letter-spacing:.13em;color:var(--dim);margin:28px 0 11px;font-weight:600}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:12px;overflow:hidden}}
.stats>div{{background:var(--panel);padding:15px 16px}}
.stats .n{{font:660 21px/1.1 ui-monospace,Menlo,monospace;letter-spacing:-.02em}} .stats .n.bad{{color:var(--coral)}}
.stats .l{{font-size:10.5px;color:var(--dim);text-transform:uppercase;letter-spacing:.07em;margin-top:5px}}
.scen{{display:flex;flex-direction:column;gap:8px}}
.row{{display:grid;grid-template-columns:1.9fr 1fr 1.3fr;gap:14px;align-items:center;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 15px}}
.row .h{{display:flex;gap:10px;align-items:flex-start}} .row .ic{{font-size:18px}} .row .nm{{font-weight:600;font-size:13.5px}} .row .ds{{font-size:11.5px;color:var(--dim);margin-top:2px;line-height:1.4}}
.dd{{text-align:right}} .dd .d1{{font:660 17px ui-monospace,Menlo,monospace;color:var(--coral)}} .dd .d2{{font-size:11px;color:var(--dim);font-family:ui-monospace,Menlo,monospace}}
.ddbar{{height:6px;background:#0c0f13;border-radius:4px;overflow:hidden;margin-top:5px}} .ddbar>div{{height:100%;background:var(--coral)}}
.bh{{font-size:11px;line-height:1.6}} .bh b{{font-family:ui-monospace,Menlo,monospace}} .bh .bl{{color:var(--coral)}} .bh .hg{{color:var(--emerald)}}
.mtxwrap{{overflow-x:auto;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:6px 8px 8px}}
table.mtx{{width:100%;min-width:900px;border-collapse:collapse;font-size:12px}}
.mtx th{{color:var(--dim);font-size:10px;text-transform:uppercase;letter-spacing:.04em;padding:7px 6px;border-bottom:1px solid var(--line);white-space:nowrap;text-align:center}}
.mtx th.l,.mtx td.l{{text-align:left;font-weight:600;color:var(--ink);white-space:nowrap;position:sticky;left:0;background:var(--panel);z-index:1}}
.mtx td{{text-align:center;padding:7px 6px;border:1px solid var(--bg);font-family:ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums}}
.liq{{display:grid;grid-template-columns:1.1fr 1fr;gap:14px;align-items:start}}
@media(max-width:820px){{.liq{{grid-template-columns:1fr}} .row{{grid-template-columns:1fr}} .stats{{grid-template-columns:1fr 1fr}}}}
.panel{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px}}
.panel h3{{font-size:14px;margin:0 0 12px;font-weight:600}}
.liqrow{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--line);font-size:13px}}
.liqrow:last-child{{border-bottom:0}} .liqrow b{{font-family:ui-monospace,Menlo,monospace}}
.liqrow .g{{color:var(--dim)}} .tag{{font-size:9px;font-weight:700;letter-spacing:.05em;padding:1px 6px;border-radius:10px;margin-left:6px}}
.tag.ok{{color:#8ee5c1;background:rgba(53,201,143,.15)}}
.note{{font-size:11.5px;color:var(--dim);line-height:1.6;margin-top:10px}} .note b{{color:var(--ink)}}
.verdict{{background:linear-gradient(180deg,rgba(53,201,143,.06),transparent);border:1px solid var(--line);border-left:3px solid var(--emerald);border-radius:10px;padding:14px 16px;font-size:12.5px;line-height:1.55}}
.verdict b{{color:var(--ink)}}
.pb{{display:flex;flex-direction:column;gap:9px}}
.pbcard{{display:grid;grid-template-columns:1.75fr 1fr;gap:16px;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:13px 16px;align-items:start}}
@media(max-width:820px){{.pbcard{{grid-template-columns:1fr}}}}
.pbcard .l1{{font-weight:600;font-size:13.5px;margin-bottom:6px}}
.pbcard .act{{font-size:12px;color:var(--dim);line-height:1.5}}
.pbcard .res{{font-size:11px;color:var(--dim);margin-top:7px}} .pbcard .res b{{color:var(--ink)}}
.pbcost{{text-align:right}} .pbcost .c{{font:660 15px ui-monospace,Menlo,monospace}} .pbcost .cn{{font-size:10.5px;color:var(--dim);line-height:1.45;margin-top:5px}}
.tag2{{font-size:9px;font-weight:700;letter-spacing:.05em;padding:2px 7px;border-radius:20px;vertical-align:middle}}
.tg-violet{{color:#c3b8fb;background:rgba(177,165,255,.15)}} .tg-emerald{{color:#8ee5c1;background:rgba(53,201,143,.15)}}
.tg-amber{{color:#eccb8a;background:rgba(217,164,65,.15)}} .tg-teal{{color:#8fe6dc;background:rgba(45,212,191,.15)}} .tg-slate{{color:#b3bcc6;background:rgba(138,147,158,.15)}}
.tg-coral{{color:#f0a8a1;background:rgba(224,115,106,.15)}}
.pbcard2{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px}}
.pbcard2 .l1{{font-weight:600;font-size:14px}} .pbcard2 .dd2{{float:right;font:600 12px ui-monospace,Menlo,monospace;color:var(--coral)}}
.read{{font-size:12px;color:var(--dim);line-height:1.5;margin:8px 0 12px}} .read b{{color:var(--ink)}}
.mnote{{font-size:11.5px;color:var(--dim);line-height:1.55;margin:-4px 0 12px;max-width:960px}} .mnote b{{color:var(--ink)}}
.mnote code,.foot code{{font-family:ui-monospace,Menlo,monospace;font-size:11px;background:var(--panel2);padding:1px 5px;border-radius:4px}}
.echan{{font-size:9.5px;color:var(--dim);font-family:ui-monospace,Menlo,monospace;letter-spacing:.02em;margin-left:8px;text-transform:uppercase}}
.epeak{{font-size:10px;font-weight:600;color:var(--ink);float:right;font-family:ui-monospace,Menlo,monospace}}
.enote{{color:var(--ink)}}
.optswrap{{overflow-x:auto}}
table.opts{{width:100%;min-width:640px;border-collapse:collapse;font-size:12px}}
.opts th{{text-align:left;color:var(--dim);font-size:9.5px;text-transform:uppercase;letter-spacing:.05em;padding:6px 8px;border-bottom:1px solid var(--line);font-weight:600}}
.opts td{{padding:9px 8px;border-bottom:1px solid var(--line);vertical-align:top}} .opts tr:last-child td{{border-bottom:0}}
.opts .on{{font-weight:600;color:var(--ink);max-width:240px}} .opts .ocat{{display:block;font-size:9px;font-weight:600;color:var(--dim);letter-spacing:.04em;margin-top:2px}}
.opts .op{{color:var(--dim);max-width:190px}}
.opts .oc{{font-family:ui-monospace,Menlo,monospace;color:var(--ink);white-space:nowrap}} .opts .ocn{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;font-size:10px;color:var(--dim);white-space:normal;max-width:220px;margin-top:3px;line-height:1.4}}
.opts .of{{max-width:230px}} .fit{{display:inline-block;font-size:9px;font-weight:700;letter-spacing:.05em;padding:2px 7px;border-radius:20px}} .fw{{font-size:10px;color:var(--dim);margin-top:4px;line-height:1.4}}
.profbar{{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin:0 0 14px}}
.profbar .pl{{font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:.06em}}
.profbar select{{background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:7px 11px;font:600 12.5px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;cursor:pointer}}
.profbar select:focus{{outline:2px solid var(--violet);outline-offset:1px}}
.profbar .profhint{{font-size:11px;color:var(--dim)}}
/* scenario cards: click to reveal probability, tripwires, playbook */
details.scard{{background:var(--panel);border:1px solid var(--line);border-radius:12px;margin-bottom:9px;overflow:hidden}}
details.scard summary{{list-style:none;cursor:pointer;display:flex;align-items:center;gap:12px;padding:12px 16px}}
details.scard summary::-webkit-details-marker{{display:none}}
details.scard[open] summary{{border-bottom:1px solid var(--line)}}
details.scard summary:hover{{background:var(--panel2)}}
.scic{{font-size:18px}} .scnm{{font-weight:600;font-size:13.5px}}
.scp{{font-size:9.5px;font-weight:700;color:#c3b8fb;background:rgba(177,165,255,.15);border-radius:20px;padding:2px 8px;white-space:nowrap;font-family:ui-monospace,Menlo,monospace}}
.scdd{{margin-left:auto;text-align:right;flex:0 0 auto}}
.chev{{color:var(--dim);font-size:10px;margin-left:10px;flex:0 0 auto}}
details.scard[open] .chev{{transform:rotate(180deg)}}
.scbody{{padding:13px 16px 15px}}
.fcast{{font-size:12px;color:var(--dim);margin:9px 0 4px;line-height:1.5}} .fcast b{{color:var(--ink);font-family:ui-monospace,Menlo,monospace}}
.tlab{{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--dim);margin:10px 0 5px;font-weight:600}}
.trip{{display:flex;flex-wrap:wrap;gap:6px}}
.trip span{{font-size:11px;color:var(--ink);background:var(--panel2);border:1px solid var(--line);border-radius:16px;padding:3px 10px}}
.foot{{font-size:11px;color:var(--dim);margin-top:26px;line-height:1.6;border-top:1px solid var(--line);padding-top:14px}}
</style></head><body>
<div class="wrap">
  <h1>Scenario Planner</h1>
  <p class="sub">Your balance sheet through the tail. {len(SCEN)} scenarios via the factor-beta model · net worth {_fmt(NW)} · READ-ONLY.</p>

  <div class="stats">
    <div><div class="n bad">{_fmt(worst['dd'])}</div><div class="l">Worst-case drawdown</div></div>
    <div><div class="n bad">{worst['dd_pct']:.0f}%</div><div class="l">of net worth ({esc(worst['sc']['key'])})</div></div>
    <div><div class="n">{_fmt(worst['nw_after'])}</div><div class="l">NW after worst case</div></div>
    <div><div class="n">{_fmt(worst_access)}</div><div class="l">Liquid even then (no illiquid)</div></div>
  </div>
""")
    if d.get("commitments"):
        from officekit.goal_projection import _existing_debt_service
        P.append(f'<p class="sub">Fixed commitments reserve {_fmt(_existing_debt_service(m))}/yr from the portfolio '
                 'before discretionary goals, using the same terms as Home. '
                 '<a href="/pages/capital.html">Review commitments →</a></p>')
    # ---- SCENARIO CARDS: worst first; click to reveal probability, tripwires, playbook ----
    para = next((s for s in assets if s["category"] == "direct_index"), None) or \
        max((s for s in assets if s["category"] not in ("cash", "cash_pending")),
            key=lambda s: s["value"], default=None)
    invested = m["A"] - sum(s["value"] for s in assets if s["category"] in ("cash", "cash_pending"))
    from officekit.commitments import pending_deployable
    sept_net = pending_deployable(m)
    p0 = para["value"] / invested * 100 if para and invested else 0
    p1 = para["value"] / (invested + sept_net) * 100 if para and invested else 0
    lead_ctx = {"sept_net": _fmt(sept_net), "p0": f"{p0:.0f}", "p1": f"{p1:.0f}"}
    lead_key = "playbook_lead" if (round(p0) != round(p1) or "playbook_lead" in overlay) else "playbook_lead_static"
    P.append('<h2>Scenarios — worst first · click a card for probability, tripwires &amp; the playbook</h2>')
    P.append(f'<div class="verdict" style="border-left-color:var(--violet);margin-bottom:10px">'
             f'{txt[lead_key].format(**lead_ctx)} '
             f'Every option shows its real cost; the <b>Fit</b> badge scores each against a client profile — a lens, not a filter. '
             f'Insurance &amp; hedges are shown in full even where they score "Situational". Switch the profile to re-score every card:</div>')
    P.append('<div class="profbar"><span class="pl">Score the menu for</span> <select id="profileSel">')
    for pk, (pname, _) in PRESETS.items():
        selattr = " selected" if pk == default_pk else ""
        P.append(f'<option value="{pk}"{selattr}>{esc(pname)}</option>')
    P.append('</select> <span class="profhint">— the menu &amp; costs are identical; only the Fit column changes</span></div>')

    maxdd = abs(worst["dd"]) or 1
    for idx, r in enumerate(results):
        sc = r["sc"]
        fx = sc.get("fix", {})
        tone = TAG_TONE.get(fx.get("tag", ""), "slate")
        bl, hg = r["bleeder"], r["hedge"]
        if sc.get("tax_ov"):    # markets flat by construction; the bleeder is the tax row
            bh = f'<span class="bl">▼ Tax Rsv {_fmt(r["dd"])}</span> · <span class="hg">▲ markets ~flat</span>'
        else:
            bh = (f'<span class="bl">▼ {esc(bl[0]["_short"])} {_fmt(bl[2])}</span> · '
                  f'<span class="hg">▲ {esc(hg[0]["_short"])} {_fmt(hg[2]) if hg[2]>0 else "~flat"}</span>')
        pchip = f'<span class="scp">p≈{sc["p"]*100:.0f}%/yr</span>' if sc.get("p") else ""
        P.append(f'<details class="scard"{" open" if idx == 0 else ""}>'
                 f'<summary><span class="scic">{sc["ic"]}</span><span class="scnm">{esc(sc["name"])}</span>'
                 f'{pchip} <span class="tag2 tg-{tone}">{esc(fx.get("tag", ""))}</span>'
                 f'<div class="scdd"><div class="d1">{_fmt(r["dd"])}</div>'
                 f'<div class="d2">{r["dd_pct"]:.1f}% · NW→{_fmt(r["nw_after"])}</div>'
                 f'<div class="ddbar"><div style="width:{abs(r["dd"])/maxdd*100:.0f}%"></div></div></div>'
                 f'<span class="chev">▼</span></summary><div class="scbody">')
        P.append(f'<div class="ds" style="font-size:12px;color:var(--dim);line-height:1.5">{esc(sc["desc"])} '
                 f'<span class="bh" style="font-size:11px">{bh}</span></div>')
        if sc.get("p"):
            P.append(f'<div class="fcast"><b>Forecast: p≈{sc["p"]*100:.0f}%/yr</b> — {esc(sc.get("p_basis", ""))}. '
                     f'First-pass prior, not a measurement — every render freezes these predictions to the learning ledger, where outcomes grade them.</div>')
        if sc.get("tripwires"):
            P.append('<div class="tlab">Tripwires — what says this is starting</div><div class="trip">'
                     + "".join(f'<span>{esc(t)}</span>' for t in sc["tripwires"]) + '</div>')
        if fx.get("action"):
            P.append(f'<div class="tlab">The playbook</div>'
                     f'<div class="read" style="margin:2px 0 10px"><b>Our read ({esc(PRESETS[default_pk][0].split(" — ")[0])}):</b> {esc(fx["action"])}</div>')
        P.append('<div class="optswrap"><table class="opts"><tr><th>Mitigation</th><th>Protects against</th><th>Cost</th><th>Fit <span class="profname">for this account</span></th></tr>')
        for oid in sc.get("opts", []):
            name, cat, protect, costfn = OPT[oid]
            name = labels.get(oid, name)
            cost, note = costfn(X)
            fits = {pk: dict(zip(("t", "w"), _fit(cat, pflags))) for pk, (_, pflags) in PRESETS.items()}
            for pk in fits:
                fits[pk]["c"] = FIT_TONE.get(fits[pk]["t"], "slate")
            dflt = fits[default_pk]
            # clickable: land on the matching strategy card, open (OPT_STRATEGY map)
            sid = OPT_STRATEGY.get(oid) or ("risk_acceptance" if oid == "accept" and adopt_endpoint else None)
            name_html = (f'<a href="{esc(strategies_href)}#strat-{sid}" '
                         f'style="color:inherit;text-decoration:underline dotted var(--dim);text-underline-offset:3px">{esc(name)}</a>'
                         if sid and not adopt_endpoint else esc(name))
            if sid and adopt_endpoint:               # explicit human adoption — the mandate click
                name_html += (f'<form method="POST" action="{esc(adopt_endpoint)}" style="margin:4px 0 0">'
                              f'<input type="hidden" name="opt" value="{esc(oid)}">'
                              f'<input type="hidden" name="scenario" value="{esc(sc["key"])}">'
                              f'<button type="submit" style="background:var(--panel2);color:var(--emerald);'
                              f'border:1px solid var(--line);border-radius:14px;padding:2px 10px;'
                              f'font:700 10px -apple-system,sans-serif;cursor:pointer">Build proposal →</button></form>')
            P.append(f'<tr><td class="on">{name_html}<span class="ocat">{esc(cat.replace("_", " ").title())}</span></td>'
                     f'<td class="op">{esc(protect)}</td>'
                     f'<td class="oc">{esc(cost)}<div class="ocn">{esc(note)}</div></td>'
                     f'<td class="of" data-fits="{esc(json.dumps(fits))}">'
                     f'<span class="fit tg-{dflt["c"]}">{esc(dflt["t"])}</span><div class="fw">{esc(dflt["w"])}</div></td></tr>')
        P.append('</table></div></div></details>')

    # ---- SLEEVE x SCENARIO P&L HEATMAP ----
    P.append('<h2>Where it hurts — $ P&amp;L by sleeve × scenario</h2><div class="mtxwrap"><table class="mtx"><tr><th class="l">Sleeve</th>')
    for r in results:
        P.append(f'<th title="{esc(r["sc"]["name"])}">{r["sc"]["ic"]}</th>')
    P.append('</tr>')
    # order sleeves by size desc, assets then liabilities
    order = sorted([s for s in sleeves if s["kind"] == "asset"], key=lambda x: -x["value"]) + \
            [s for s in sleeves if s["kind"] == "liability"]
    pnl_by = {r["sc"]["key"]: {id(s): p for s, _, p in r["rows"]} for r in results}
    scales = {r["sc"]["key"]: max((abs(p) for _, _, p in r["rows"]), default=1) for r in results}
    for s in order:
        P.append(f'<tr><td class="l">{esc(s["_short"])}</td>')
        for r in results:
            style, tcell = _pnlcell(pnl_by[r["sc"]["key"]][id(s)], scales[r["sc"]["key"]])
            P.append(f'<td style="{style}">{tcell}</td>')
        P.append('</tr>')
    # household total row
    P.append('<tr><td class="l" style="border-top:2px solid var(--line)">◆ NET WORTH Δ</td>')
    for r in results:
        style, tcell = _pnlcell(r["dd"], maxdd)
        P.append(f'<td style="{style};border-top:2px solid var(--line);font-weight:700">{tcell}</td>')
    P.append('</tr></table></div>')

    # ---- LIQUIDITY SURVIVAL ----
    liq_ctx = {"dd_pct": f"{worst['dd_pct']:.0f}", "worst_access": _fmt(worst_access),
               "claims": _fmt(claims), "thedge": _fmt(worst["thedge"])}
    P.append(f"""<h2>Liquidity survival map</h2>
  <div class="liq">
    <div class="panel">
      <h3>In the worst case ({esc(worst['sc']['name'])})</h3>
      <div class="liqrow"><span class="g">Immediate cash (MMF, flat)</span><b>{_fmt(worst['cash_now'])}</b></div>
      <div class="liqrow"><span class="g">Marketable at crashed marks (−2% haircut)</span><b>{_fmt(worst['mkt'])}</b></div>
      <div class="liqrow"><span class="g"><b>= Raisable without illiquid / pre-{eta}</b></span><b>{_fmt(worst_access)}</b></div>
      <div class="liqrow"><span class="g">+ {eta} dry powder once landed</span><b>{_fmt(worst['sept'])}</b></div>
      <div class="liqrow"><span class="g">Frozen (venture + RE, shocked)</span><b style="color:var(--dim)">{_fmt(worst['frozen'])}</b></div>
      <div class="liqrow"><span class="g">{esc(txt["claims_label"])}</span><b style="color:var(--coral)">{_fmt(-claims)}</b></div>
    </div>
    <div class="panel">
      <h3>Read</h3>
      <div class="verdict">{txt["liquidity_read"].format(**liq_ctx)}</div>
      <div class="note">{txt["liquidity_note"].format(**liq_ctx)}</div>
    </div>
  </div>""")

    # ---- GOALS THROUGH THE TAIL (only when the balance sheet declares goals) ----
    goal_defs = d.get("goals") or []
    if goal_defs:
        as_of = d.get("as_of", "")
        base_liq = (sum(s["value"] for s in assets if LIQ.get(s["category"]) == "now")
                    + sum(s["value"] for s in assets if LIQ.get(s["category"]) == "mkt") * 0.98)
        base_inv = goals_mod.investable([(s, 0.0) for s in sleeves])
        # each column carries its scenario's EFFECTIVE goal set (goal_ov applied) —
        # a life-event scenario may add goals or change spending, not just marks
        cols = [("☀️", "Today (no shock)", base_inv, base_liq, list(goal_defs), None)]
        for r in results:
            inv_after = goals_mod.investable([(s, p) for s, _, p in r["rows"]])
            eff = goals_mod.apply_goal_ov(goal_defs, r["sc"].get("goal_ov"))
            cols.append((r["sc"]["ic"], r["sc"]["name"], inv_after, r["cash_now"] + r["mkt"], eff,
                         [(s, p) for s, _, p in r["rows"]]))
        # rows = base goals + any scenario-added goals, in first-seen order
        row_keys, row_src = [], {}
        for _, _, _, _, eff, _ in cols:
            for g in eff:
                k = goals_mod.goal_key(g)
                if k not in row_src:
                    row_keys.append(k)
                    row_src[k] = g
        TONE_RGB = {"emerald": "53,201,143", "amber": "217,164,65", "coral": "224,115,106"}
        P.append(f'<h2>Goals through the tail — {len(row_keys)} goals × {len(results)} scenarios</h2>')
        P.append('<p class="mnote">Property purchases must cover both cash to close and annual carrying costs, '
                 'using the same assessment as Home and Strategies. Pending inflows are excluded until received. '
                 'Other goals are re-scored in every scenario: retirement via a flat '
                 f'{goals_mod.SWR*100:.0f}% withdrawal on post-shock <b>investable</b> net worth (residence excluded), '
                 'floors and dated targets against post-shock liquidity. Life-event scenarios may change the goal '
                 'set itself (a "—" cell means the goal doesn\'t exist in that world). This is a deliberate '
                 '<b>no-growth heuristic</b> — a floor, not a forecast; the Simulation slot (reserved) upgrades it to path analysis.</p>')
        P.append('<div class="mtxwrap"><table class="mtx"><tr><th class="l">Goal</th>')
        for ic, name, _, _, _, _ in cols:
            P.append(f'<th title="{esc(name)}">{ic}</th>')
        P.append('</tr>')
        for k in row_keys:
            g0 = row_src[k]
            e0 = goals_mod.evaluate_in_model(g0, m)
            P.append(f'<tr><td class="l" title="{esc(e0["detail"])}">{esc(e0["label"])} '
                     f'<span style="color:var(--dim);font-weight:400">· {esc(e0["target_txt"])}</span></td>')
            for _, _, inv, liq, eff, pnls in cols:
                g = next((x for x in eff if goals_mod.goal_key(x) == k), None)
                if g is None:
                    P.append('<td style="background:rgba(138,145,153,.08)">—</td>')
                    continue
                ev = goals_mod.evaluate_in_model(g, m, pnls, effective_goals=eff)
                rgb = TONE_RGB[goals_mod.STATUS_TONE[ev["status"]]]
                P.append(f'<td style="background:rgba({rgb},0.18)" title="{esc(ev["detail"])}">'
                         f'{esc(ev["status"])} ·{ev["ratio"]:.2f}x'
                         + (f'<br><small>Cash to close: {ev["closing_ratio"]:.1f}x<br>Annual carry: {ev["carry_ratio"]:.2f}x</small>'
                            if "closing_ratio" in ev else "") + '</td>')
            P.append('</tr>')
        P.append('</table></div>')

    # ---- MICROSTRUCTURE & SECOND-ORDER EFFECTS (registry-driven) ----
    # each effect is a registered program in the effects module; the planner DISPATCHES
    # it per scenario. Here we show each effect's definition + its peak realized magnitude.
    peak = {}   # effect id -> (magnitude, scenario name, note)
    for r in results:
        for e in r["effs"]:
            mag = e.get("delta", 0.0) or e.get("shadow", 0.0)
            if e["id"] not in peak or mag > peak[e["id"]][0]:
                peak[e["id"]] = (mag, r["sc"]["name"], e.get("note", ""))
    P.append('<h2>Microstructure &amp; second-order effects — encoded as programs</h2>')
    P.append(f'<p class="mnote"><b>{len(effects.EFFECTS)} effects registered</b> in <code>{esc(effects_label)}</code>, dispatched per scenario '
             '(not hardcoded). <span class="tag2 tg-emerald">ENCODED</span> effects move the drawdown numbers above; '
             '<span class="tag2 tg-slate">NOTED</span> effects compute an unbooked shadow the linear model misses. '
             'Each is a tested function — a new insight is a new registered effect, never an engine edit.</p>')
    P.append('<div class="pb">')
    for fn in effects.EFFECTS:
        meta = fn.meta
        eid = meta["id"]
        kind = meta["kind"]
        tone = "emerald" if kind == "ENCODED" else ("teal" if meta.get("channel") == "rates" else "amber")
        pk = peak.get(eid)
        if pk and pk[0] >= 1:
            lbl = "cushion" if kind == "ENCODED" else "shadow"
            mag = f' <span class="epeak">peak ~{_fmt(pk[0])} {lbl} · {esc(pk[1])}</span>'
        else:
            mag = ' <span class="epeak" style="color:var(--dim)">does not fire in this set</span>'
        P.append(f'<div class="pbcard2"><div class="l1">{ICON.get(eid, "•")} {esc(meta["name"])} '
                 f'<span class="tag2 tg-{tone}">{esc(kind)}</span>'
                 f'<span class="echan">{esc(meta.get("channel", ""))} · {esc(meta.get("latency", ""))}</span>{mag}</div>'
                 f'<div class="read" style="margin-bottom:0">{esc(meta.get("doc", ""))}'
                 + (f' <span class="enote">→ worst case: {esc(pk[2])}.</span>' if pk and pk[2] else "")
                 + '</div></div>')
    P.append('</div>')

    P.append(f'<div class="foot">{txt["foot"]}</div>')
    P.append("""<script>
(function(){
  var sel=document.getElementById('profileSel'); if(!sel) return;
  function apply(k){
    document.querySelectorAll('.of[data-fits]').forEach(function(td){
      var f=JSON.parse(td.getAttribute('data-fits'))[k]; if(!f) return;
      var b=td.querySelector('.fit'); b.textContent=f.t; b.className='fit tg-'+f.c;
      td.querySelector('.fw').textContent=f.w;
    });
    var lbl=(sel.options[sel.selectedIndex].text||'').split(' — ')[0];
    document.querySelectorAll('.profname').forEach(function(e){e.textContent='for '+lbl;});
  }
  sel.addEventListener('change',function(){apply(sel.value);});
})();
</script>""")
    P.append('</div></body></html>')
    from officekit.mandates import stamp_forms
    return stamp_forms("\n".join(P), m.get("_commitment_revision"))


# back-compat alias (pre-rename name)
render_disaster = render_scenarios
