"""render_strategies — the STRATEGIES page: every sleeve you run, every sleeve
you could, as dropdown cards.

The sketch's box 4 made navigable (principal-directed 2026-09-03): mitigation
rows on the Scenario Planner link here with an anchor, and the linked strategy
card arrives OPEN — showing whether it's been decided (implemented / considering
/ declined / not decided), its current vs target percentage, sample subassets,
which scenarios recommend it, and (for current sleeves) the actual holdings with
their adjudication coverage.

Decision state is CLIENT DATA — data["strategy_decisions"] = {strategy_id:
{"status", "target_pct"?, "note"?}} — never inferred: a strategy with no matching
sleeve and no recorded decision is honestly "NOT DECIDED". This is the bottom-up
(coverage/tag) half of the mandate loop; the top-down authority model stays an
open PRD question. READ-ONLY — never places orders.
"""
from __future__ import annotations

from officekit.fmt import esc, fmt_usd as _fmt

# Court verdicts are recorded as machine codes; readers need plain language.
_VERDICT_LABELS = {
    "HELD_PENDING_DECISION": "Held — decision pending",
    "PENDING_DECISION": "Decision pending", "PENDING": "Decision pending",
    "WATCH": "Watching", "UNREVIEWED": "Not yet reviewed", "DRAFT": "Draft",
    "BUY": "Cleared to buy", "ENTER": "Cleared to enter", "STARTER": "Starter position",
    "ADD": "Add to position", "ADVANCE": "Advanced to next stage",
    "HOLD": "Hold", "TRIM": "Trim", "SELL": "Exit", "EXIT": "Exit",
    "PASS": "Passed", "REJECT": "Passed", "FLAT": "No position", "KILL": "Killed",
}


def _verdict_label(v):
    """Machine verdict code -> plain-language label (raw code kept for tooltips)."""
    if not v:
        return ""
    key = str(v).upper().strip()
    return _VERDICT_LABELS.get(key, key.replace("_", " ").capitalize())

# ---------------------------------------------------------------- the library --
# strategy id -> {title, ic, desc, category (matches current sleeves), subassets}
# Sample subassets are EXAMPLES of how the strategy is typically expressed, not
# recommendations of specific securities.
STRATEGY_LIB = {
    "core_equity":   {"ic": "📊", "title": "Core public equity", "category": "public_equity",
                      "desc": "Broad cap-weighted funds — the compounding base of the balance sheet.",
                      "subassets": ["VTI / total-market", "VXUS / international", "S&P 500 index funds", "target-date funds"]},
    "direct_index":  {"ic": "🧮", "title": "Direct indexing / SMA", "category": "direct_index",
                      "desc": "Own the index as individual lots — tracking plus lot-level tax-loss harvesting.",
                      "subassets": ["S&P 500 SMA", "custom index w/ exclusions", "long/short tax-aware extension"]},
    "concentrated":  {"ic": "🎯", "title": "Concentrated single names", "category": "single_name_equity",
                      "desc": "Sized single-stock positions — managed with floors, collars, or deliberate holds.",
                      "subassets": ["founder / RSU stock", "protective puts", "staged diversification plan"]},
    "muni":          {"ic": "🏛️", "title": "Municipal credit", "category": "municipal_credit",
                      "desc": "Tax-exempt income; state-specific where the tax math says so.",
                      "subassets": ["VTEB / MUB", "state-specific fund", "individual muni ladder"]},
    "bonds":         {"ic": "📜", "title": "Core fixed income", "category": "fixed_income",
                      "desc": "Duration ballast and dry-powder-adjacent stability.",
                      "subassets": ["BND / AGG", "treasury ladder", "short-duration funds"]},
    "cash_mgmt":     {"ic": "💵", "title": "Cash management", "category": "cash",
                      "desc": "The buffer that makes every drawdown a discount instead of a margin call.",
                      "subassets": ["money-market funds", "SGOV / BIL", "T-bill ladder"]},
    "real_estate":   {"ic": "🏠", "title": "Real estate", "category": "real_estate",
                      "desc": "The residence — a consumption asset with a rate-hedged liability against it.",
                      "subassets": ["primary residence", "hazard + umbrella coverage"]},
    "venture":       {"ic": "🌱", "title": "Venture / private", "category": "venture_private",
                      "desc": "Illiquid power-law exposure — paced commitments, reserves for follow-ons.",
                      "subassets": ["fund LP positions", "direct seed checks", "follow-on reserve"]},
    "human_capital": {"ic": "🧑‍💼", "title": "Human capital", "category": "human_capital",
                      "desc": "Capitalized future earnings — insured, not traded.",
                      "subassets": ["earnings stream (PV)", "own-occupation LTD", "level term life"]},
    "deploy_powder": {"ic": "💧", "title": "New-capital deployment", "category": "cash_pending",
                      "desc": "Routing incoming cash — the cheapest concentration-dilution lever there is.",
                      "subassets": ["tranched deployment calendar", "non-correlated sleeve routing"]},
    # planned-only strategies (no sleeve category until implemented)
    "index_hedge":   {"ic": "🛡️", "title": "Index hedge overlay", "category": None,
                      "desc": "Puts / put spreads / collars over the equity book — drawdown insurance.",
                      "subassets": ["SPX/XSP puts (~5% OTM, rolled)", "put spreads", "zero-cost collars"]},
    "tail_vol":      {"ic": "🌪️", "title": "Tail-risk / long-vol sleeve", "category": None,
                      "desc": "Convex crash payoff that bleeds in calm markets.",
                      "subassets": ["long-vol funds", "far-OTM index puts", "VIX call ladders"]},
    "trend":         {"ic": "📈", "title": "Managed futures / trend", "category": None,
                      "desc": "Crisis-alpha: positive expectancy in sustained selloffs and inflation shocks.",
                      "subassets": ["trend-following funds", "commodity CTA sleeve"]},
    "real_assets":   {"ic": "🥇", "title": "Real-asset ballast", "category": None,
                      "desc": "Inflation & stagflation hedge via reallocation, no derivatives.",
                      "subassets": ["gold (GLD/PHYS-class)", "TIPS", "broad commodities"]},
    "harvest_engine": {"ic": "🌾", "title": "Tax-loss harvest engine", "category": None,
                      "desc": "Systematically manufactures losses to offset realized gains — the tax-bomb's antidote.",
                      "subassets": ["direct-index SMA harvesting", "lot-level TLH on liquid sleeves"]},
    "gifting":       {"ic": "🎁", "title": "Charitable gifting", "category": None,
                      "desc": "Appreciated shares out, FMV deduction in — the gain never realizes.",
                      "subassets": ["donor-advised fund", "appreciated-share gifts"]},
    "monetization":  {"ic": "🔄", "title": "Concentration monetization", "category": None,
                      "desc": "Diversify or raise cash against a low-basis block without a taxable sale.",
                      "subassets": ["exchange fund (7-yr lock)", "prepaid variable forward"]},
    "insurance_program": {"ic": "☂️", "title": "Insurance program", "category": None,
                      "desc": "Insure the earner and the hard assets — the highest-probability tails.",
                      "subassets": ["own-occupation LTD", "level term life", "umbrella liability", "hazard coverage"]},
    "credit_line":   {"ic": "🏦", "title": "Standby credit line", "category": None,
                      "desc": "Liquidity without selling into weakness; undrawn until needed.",
                      "subassets": ["pledged-asset line", "HELOC standby"]},
    "duration_mgmt": {"ic": "⏱️", "title": "Duration management", "category": None,
                      "desc": "Shorten or hedge the rate-sensitive sleeves when the rate tail worries you.",
                      "subassets": ["VGSH / SHY rotation", "payer swaption overlay"]},
}

STATUS_TONE = {"implemented": ("IMPLEMENTED", "emerald"), "considering": ("CONSIDERING", "amber"),
               "planned": ("PLANNED", "violet"), "declined": ("DECLINED", "coral"),
               "not_decided": ("NOT DECIDED", "slate")}


def resolve_strategies(m, applicable_scen):
    """The client's strategy list: library defaults + member assets + recorded
    decisions + which applicable scenarios recommend each. Returns ordered rows.

    Membership model (principal ruling 2026-09-04): strategies are VIEWS over
    the one asset pool, many-to-many and whole-asset. Explicit `strategies`
    tags (sleeve- or holding-level) are the authoritative edges; category
    match survives only as a fallback, for strategies with no explicit member
    anywhere, over sleeves that carry no tags at all. Rollups (value, beta)
    sum over members per view — totals across strategies may legitimately
    exceed 100% of NW, because one asset can serve several mandates. NW never
    rolls up from strategies."""
    from officekit.mitigations import OPT_STRATEGY
    from officekit.model import strategy_tags
    d = m["d"]
    decisions = d.get("strategy_decisions") or {}
    rec = {}   # sid -> [scenario names]
    for sc in applicable_scen:
        for oid in sc.get("opts", []):
            sid = OPT_STRATEGY.get(oid)
            if sid:
                rec.setdefault(sid, [])
                if sc["name"] not in rec[sid]:
                    rec[sid].append(sc["name"])
    # library strategies + the principal's CUSTOM ones (defined inside their decision)
    all_ids = list(STRATEGY_LIB) + [sid for sid in decisions if sid not in STRATEGY_LIB]
    rows = []
    for sid in all_ids:
        dec = decisions.get(sid, {})
        lib = STRATEGY_LIB.get(sid) or {
            "ic": dec.get("ic", "✳️"), "title": dec.get("title", sid),
            "desc": dec.get("desc", "Principal-designed strategy."),
            "category": dec.get("category"), "subassets": dec.get("subassets", [])}
        # explicit edges first: whole sleeves, then holdings inside non-member sleeves
        sleeves = [s for s in m["assets"] if sid in strategy_tags(s)]
        holds = [(h, s) for s in m["assets"] if s not in sleeves
                 for h in (s.get("holdings") or []) if sid in strategy_tags(h)]
        if not sleeves and not holds and lib["category"]:
            # fallback: only untagged sleeves — a tagged sleeve has opted into
            # explicit membership and is never claimed by category coincidence
            sleeves = [s for s in m["assets"]
                       if s["category"] == lib["category"] and not strategy_tags(s)]
        status = dec.get("status") or ("implemented" if sleeves or holds else "not_decided")
        mem_val = (sum(s["value"] for s in sleeves)
                   + sum(float(h.get("amount") or 0.0) for h, _ in holds))
        cur_pct = mem_val / m["NW"] * 100 if m["NW"] and mem_val else 0.0
        # value-weighted factor rollup — holdings ride their parent sleeve's loadings
        expo = {}
        for s in sleeves:
            for f, b in (s.get("beta") or {}).items():
                expo[f] = expo.get(f, 0.0) + s["value"] * float(b or 0.0)
        for h, parent in holds:
            for f, b in (parent.get("beta") or {}).items():
                expo[f] = expo.get(f, 0.0) + float(h.get("amount") or 0.0) * float(b or 0.0)
        expo = {f: v / mem_val for f, v in expo.items() if mem_val} if mem_val else {}
        tgt = dec.get("target_pct")
        if tgt is None:
            tgts = [s.get("target_pct") for s in sleeves if s.get("target_pct") is not None]
            tgt = sum(tgts) if tgts else None
        rows.append({"sid": sid, "lib": lib, "sleeves": sleeves, "holds": holds,
                     "mem_val": mem_val, "expo": expo, "status": status,
                     "cur_pct": cur_pct, "target_pct": tgt, "note": dec.get("note"),
                     "origins": dec.get("origins", []),
                     "recommended_by": rec.get(sid, [])})
    # current first (by size), then the rest (decided before undecided)
    order = {"implemented": 0, "considering": 1, "planned": 1, "declined": 2, "not_decided": 3}
    rows.sort(key=lambda r: (order.get(r["status"], 3), -r["cur_pct"]))
    return rows


def _adopt_toggle(adopted, gid, sid, adopt_ep, unadopt_ep):
    """A check/uncheck toggle: checked = adopted for this goal (click to remove),
    unchecked = offered (click to adopt). Falls back to nothing if no endpoints."""
    from officekit.fmt import esc
    if adopted and unadopt_ep:
        return (f'<form method="POST" action="{esc(unadopt_ep)}" style="margin:0" title="adopted — click to remove">'
                f'<input type="hidden" name="gid" value="{esc(gid)}"><input type="hidden" name="sid" value="{esc(sid)}">'
                f'<button type="submit" class="adoptck on">☑ adopted</button></form>')
    if not adopted and adopt_ep:
        return (f'<form method="POST" action="{esc(adopt_ep)}" style="margin:0" title="adopt this strategy for the goal">'
                f'<input type="hidden" name="gid" value="{esc(gid)}"><input type="hidden" name="sid" value="{esc(sid)}">'
                f'<button type="submit" class="adoptck">Build proposal</button></form>')
    return ""


def render_strategies(m, scenarios_href="scenarios.html", create_endpoint=None,
                      court_endpoint=None, holdings_endpoint=None, adjudications=None,
                      goal_menu=None, goal_adopt_endpoint=None, goal_unadopt_endpoint=None,
                      docket_items=None, harvest_href="harvest.html", desk_theses=None,
                      desk_import_endpoint=None, proposals=None):
    d = m["d"]
    # A court on an option structure or insurance program is not approval to
    # buy its displayed underlying/subject through the stock holdings form.
    adjudications = [a for a in (adjudications or []) if a.get("subject_kind", "security") == "security"]
    from officekit.render_scenarios import applicable_scenarios
    rows = resolve_strategies(m, applicable_scenarios(m))
    adj_by_sid = {}
    for a in (adjudications or []):
        adj_by_sid.setdefault(a.get("strategy"), []).append(a)
    from officekit.goal_mandates import goal_coverage
    goal_cov = goal_coverage(m)["by_strategy"] if (d.get("goals") or []) else {}
    n_cur = sum(1 for r in rows if r["sleeves"])
    n_dec = sum(1 for r in rows if r["status"] in ("implemented", "considering", "planned", "declined"))

    toolbar = (('<a href="#goal-plan">Review goal plan</a>' if goal_menu else '')
               + ('<a href="#create-strategy">＋ Create strategy</a>' if create_endpoint else '')
               + f'<a href="{esc(scenarios_href)}">Stress test portfolio</a>')
    P = []
    P.append(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Strategies</title>
<style>
:root{{--bg:#0b0e12;--panel:#14181d;--panel2:#1a1f25;--line:#242a31;--ink:#e8ebee;--dim:#9aa4b0;
--emerald:#35c98f;--violet:#b1a5ff;--amber:#d9a441;--coral:#e0736a;--slate:#8a939e}}
*{{box-sizing:border-box}} body{{margin:0;background:#0b0e12}}
.wrap{{max-width:1240px;margin:0 auto;padding:24px 24px 90px;font:14px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:var(--ink);background:var(--bg)}}
h1{{font-size:25px;margin:0 0 3px;letter-spacing:-.02em;font-weight:650}}
.sub{{color:var(--dim);font-size:13px;margin:0 0 22px}} .sub a{{color:var(--dim)}}
h2{{font-size:11.5px;text-transform:uppercase;letter-spacing:.13em;color:var(--dim);margin:28px 0 11px;font-weight:600}}
details.scard{{background:var(--panel);border:1px solid var(--line);border-radius:12px;margin-bottom:9px;overflow:hidden}}
details.scard summary{{list-style:none;cursor:pointer;display:flex;align-items:center;gap:12px;padding:12px 16px}}
details.scard summary::-webkit-details-marker{{display:none}}
details.scard[open] summary{{border-bottom:1px solid var(--line)}}
details.scard summary:hover{{background:var(--panel2)}}
.scic{{font-size:18px}} .scnm{{font-weight:600;font-size:13.5px}}
.scdd{{margin-left:auto;text-align:right;flex:0 0 auto;font:600 12px ui-monospace,Menlo,monospace;color:var(--dim)}}
.scdd b{{color:var(--ink)}}
.chev{{color:var(--dim);font-size:10px;margin-left:10px;flex:0 0 auto}}
details.scard[open] .chev{{transform:rotate(180deg)}}
.scbody{{padding:13px 16px 15px}}
.st{{font-size:9.5px;font-weight:700;letter-spacing:.05em;padding:2px 8px;border-radius:20px;white-space:nowrap}}
.st-emerald{{color:#8ee5c1;background:rgba(53,201,143,.15)}} .st-amber{{color:#eccb8a;background:rgba(217,164,65,.15)}}
.st-violet{{color:#c3b8fb;background:rgba(177,165,255,.15)}} .st-coral{{color:#f0a8a1;background:rgba(224,115,106,.15)}}
.st-slate{{color:#b3bcc6;background:rgba(138,147,158,.15)}}
.intuited{{font-size:9px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#c3b8fb;background:rgba(177,165,255,.15);border-radius:20px;padding:2px 7px}}
.intu{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:10px}}
.intu .refine{{color:var(--dim);font-size:11.5px;margin-left:12px}}
.ds{{font-size:12px;color:var(--dim);line-height:1.5}}
.tlab{{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--dim);margin:10px 0 5px;font-weight:600}}
.trip{{display:flex;flex-wrap:wrap;gap:6px}}
.trip span,.trip a{{font-size:11px;color:var(--ink);background:var(--panel2);border:1px solid var(--line);border-radius:16px;padding:3px 10px;text-decoration:none}}
.trip a:hover{{border-color:var(--violet)}}
.slv{{display:flex;justify-content:space-between;gap:10px;padding:7px 0;border-bottom:1px solid var(--line);font-size:12.5px}}
.slv:last-child{{border-bottom:0}} .slv b{{font-family:ui-monospace,Menlo,monospace}}
.slv .g{{color:var(--dim);font-size:11px}}
.adoptck{{background:var(--panel2);color:var(--dim);border:1px solid var(--line);border-radius:20px;
  padding:4px 12px;font:600 11.5px -apple-system,sans-serif;cursor:pointer;white-space:nowrap}}
.adoptck:hover{{border-color:var(--violet);color:var(--ink)}}
.adoptck.on{{color:#8ee5c1;background:rgba(53,201,143,.14);border-color:rgba(53,201,143,.5)}}
.adoptck.on:hover{{color:#f0b3ad;background:rgba(224,115,106,.14);border-color:rgba(224,115,106,.5)}}
.note{{font-size:12px;color:var(--dim);line-height:1.5;margin-top:9px;border-left:3px solid var(--line);padding-left:10px}}
.prov{{margin-top:5px}} .prov>summary{{cursor:pointer;color:var(--dim);font-size:11px}} .prov[open]>summary{{margin-bottom:4px}}
.note b{{color:var(--ink)}}
.foot{{font-size:11px;color:var(--dim);margin-top:26px;line-height:1.6;border-top:1px solid var(--line);padding-top:14px}}

a{{color:var(--violet);text-underline-offset:3px}} a:hover{{color:#d1caff}}
a:focus-visible,button:focus-visible,summary:focus-visible,input:focus-visible{{outline:2px solid var(--emerald);outline-offset:3px}}
h1{{font-size:32px;letter-spacing:-.035em}} .eyebrow{{color:var(--emerald);font-size:11px;letter-spacing:.15em;text-transform:uppercase;margin-bottom:8px}}
.strategy-toolbar{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:26px}} .strategy-toolbar a{{font-size:12px;text-decoration:none;border:1px solid var(--line);border-radius:8px;padding:8px 12px;color:var(--ink)}}
.strategy-toolbar a:first-child{{background:var(--emerald);color:#08110d;border-color:var(--emerald);font-weight:600}}
.lifecycle{{display:flex;gap:7px;flex-wrap:wrap;margin:16px 0}} .lifecycle button{{font:600 12px -apple-system,sans-serif;background:var(--panel);border:1px solid var(--line);color:var(--dim);border-radius:8px;padding:10px 13px;cursor:pointer}}
.lifecycle button[aria-pressed=true]{{background:#183b30;border-color:#328365;color:#a4edd0}} .lifecycle button span{{margin-left:8px;opacity:.8}}
.search-label{{display:block;color:var(--dim);font-size:12px;margin-bottom:6px}} #strategy-search{{box-sizing:border-box;width:100%;background:var(--panel);border:1px solid var(--line);border-radius:10px;color:var(--ink);padding:12px 14px;font:14px -apple-system,sans-serif}}
#strategy-count{{font-size:12px;color:var(--dim);margin:12px 0}} .strategy-empty{{padding:28px;border:1px dashed var(--line);border-radius:12px;color:var(--dim)}} [hidden]{{display:none!important}}
.thesis-card summary{{min-height:76px}} .thesis-card .scnm{{font-size:15px;flex:1;min-width:0}} .thesis-meta{{display:block;color:var(--dim);font-size:11px;font-weight:400;margin-top:3px}} .thesis-card .scdd{{font-size:14px}} .thesis-card .scdd small{{display:block;font:11px/1.5 -apple-system,sans-serif;margin-top:3px}}
.workspace-section{{margin-top:24px;border-top:1px solid var(--line);padding-top:20px}} .workspace-section>summary{{cursor:pointer;font-size:16px;font-weight:600}} .workspace-section>summary span{{display:block;font-size:12px;color:var(--dim);font-weight:400;margin-top:4px}}
.workspace-section[open]>summary{{margin-bottom:18px}} .scbody form{{flex-wrap:wrap}} .scbody input{{min-width:0}} .scnm{{overflow-wrap:anywhere}}
@media(max-width:650px){{.wrap{{padding:22px 16px 60px}} details.scard summary{{flex-wrap:wrap;gap:8px;padding:14px}} .scnm{{flex:1;min-width:160px}} .thesis-card .scic{{display:none}} .thesis-card .scdd{{margin-left:0;width:100%;text-align:left;display:flex;gap:8px;align-items:baseline}} details.scard.thesis-card summary{{display:grid;grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"title status" "stats chevron"}} .thesis-card .scnm{{grid-area:title;min-width:0}} .thesis-card .st{{grid-area:status}} .thesis-card .scdd{{grid-area:stats;width:auto}} .thesis-card .chev{{grid-area:chevron;justify-self:end;margin-left:0}} .scdd{{font-size:11px}} .create-grid{{grid-template-columns:1fr!important}}}}
</style></head><body><div class="wrap">
  <div class="eyebrow">Capital at work</div><h1>Strategies</h1>
  <p class="sub">See what you hold, what needs a decision, and what you’re exploring.</p>
  <div class="strategy-toolbar">{toolbar}</div>""")

    # ---- INTUITED strategies: what the balance sheet already implements, whether
    # or not it was ever adopted (the strategy analogue of intuited goals) ----
    from officekit.intuition import implicit_strategies
    istrats = implicit_strategies(m)
    if istrats:
        P.append('<h2>Already running — intuited from your holdings</h2>')
        P.append('<p class="sub">Strategies your positions already implement — you didn\'t opt in, your '
                 'balance sheet did. Manage or refine each where it lives.</p>')
        for s in istrats:
            P.append(
                f'<div class="intu">'
                f'<div style="display:flex;gap:10px;align-items:baseline;justify-content:space-between">'
                f'<div class="scnm">{esc(s["label"])} <span class="intuited">Intuited</span> '
                f'<span class="st st-emerald">Active</span></div><b>{_fmt(s["value"])}</b></div>'
                f'<div class="ds" style="margin-top:6px">{esc(s["why"])}</div>'
                f'<div class="tlab" style="margin-top:8px">'
                f'<a href="{esc(s["href"])}">{esc(s["cta"])} &rarr;</a>'
                f'<span class="refine">To refine, tell the AI: &ldquo;{esc(s["refine"])}&rdquo;</span>'
                f'</div></div>')

    taxonomy = []
    # ---- Thesis TAXONOMY: the same sleeves seen through two lenses — the goal each
    # funds, and how each behaves in the scenarios. A sleeve appears in both; these
    # groupings are for understanding, SEPARATE from the enumeration below (which is
    # where each thesis's positions + implementation live). Sleeves deep-link to that
    # enumeration card (#thesis-<sid>). (principal 2026-09-11)
    if desk_theses:
        from officekit import thesis_board as _tb

        def _chips(theses):
            return " · ".join(f'<a href="#thesis-{esc(t["sid"])}">{esc(t["label"])}</a> '
                              f'<span class="g">{_fmt(t["value"])}</span>' for t in theses)

        by_goal = _tb.by_goal(desk_theses, d.get("goals") or [], d.get("as_of", ""))
        if by_goal:
            taxonomy.append('<h2>Thesis strategies — by goal</h2>'
                     '<p class="sub">Thesis views relevant to each goal; values can overlap across views. No capital is reserved. Compare '
                     'horizon assumptions with the shared goal budget.</p>')
            for gg in by_goal:
                g = gg["goal"]
                taxonomy.append(f'<details class="scard" id="goalthesis-{esc(g.get("id",""))}" open>'
                         f'<summary><span class="scic">🎯</span>'
                         f'<span class="scnm">{esc(g.get("label") or g.get("kind"))}</span>'
                         f'<div class="scdd"><b>{_fmt(gg["value"])}</b> view exposure · {sum(len(b["theses"]) for b in gg["buckets"])} theses</div>'
                         f'<span class="chev">&#9660;</span></summary><div class="scbody">')
                for b in gg["buckets"]:
                    fit = (f' <span class="st st-amber">{esc(b["fit"])}</span>'
                           if b["fit"].startswith("long") else "")
                    why = (f'<div class="ds" style="color:#8ee5c1;margin:2px 0 2px">{esc(b["fit_why"])}</div>'
                           if b.get("fit_why") else "")
                    taxonomy.append(f'<div class="tlab">{esc(b["label"])} · {_fmt(b["value"])}{fit}</div>'
                             + why + f'<div class="ds">{_chips(b["theses"])}</div>')
                taxonomy.append('</div></details>')

        by_scn = _tb.by_scenario(desk_theses)
        if by_scn:
            taxonomy.append('<h2>Thesis strategies — by intended role</h2>'
                     '<p class="sub">The same sleeves grouped by intended role; these labels do not measure resilience to '
                     f'shocks. See the <a href="{esc(scenarios_href)}">Scenario Planner</a> for the full stress.</p>')
            for b in by_scn:
                taxonomy.append(f'<details class="scard" id="bucket-{esc(b["bucket"])}">'
                         f'<summary><span class="scic">🛡️</span>'
                         f'<span class="scnm">{esc(b["label"])}</span>'
                         f'<div class="scdd"><b>{_fmt(b["value"])}</b> · {len(b["theses"])} theses</div>'
                         f'<span class="chev">&#9660;</span></summary><div class="scbody">'
                         f'<div class="ds">{esc(b["scenarios"])}</div>'
                         f'<div class="tlab">Sleeves</div><div class="ds">{_chips(b["theses"])}</div>'
                         '</div></details>')

    # ---- Thesis sleeves: per-thesis strategies, office-owned (the ENUMERATION +
    # implementation: positions, verdict, edge — distinct from the taxonomy above) ----
    # assembled from the office's own court adjudications + positions, merged with an
    # owned snapshot of imported desk theses and authored, unadjudicated packs.
    if desk_theses:
        from officekit.render_signals import asset_slug
        queued = {i.get("strategy") for i in (docket_items or []) if i.get("status") in ("QUEUED", "RUNNING")}
        def lifecycle(t):
            if abs(t.get("value", 0)) > 0 or any(abs(p.get("mv") or 0) > 0 for p in t.get("positions", [])):
                return "held"
            if t["sid"] in queued or str(t.get("verdict") or "").upper() in ("PENDING", "PENDING_DECISION", "HELD_PENDING_DECISION"):
                return "review"
            if t.get("pack") and not t.get("court_date") and str(t.get("verdict") or "").upper() in ("", "UNREVIEWED", "DRAFT"):
                return "draft"
            return "watch"
        def needs_review(t):
            return (t["sid"] in queued or str(t.get("verdict") or "").upper() in ("HELD_PENDING_DECISION", "WATCH", "PENDING", "PENDING_DECISION")
                    or (lifecycle(t) == "held" and t.get("pack") and not t.get("court_date") and not t.get("verdict"))) or False
        counts = {k: sum(lifecycle(t) == k for t in desk_theses) for k in ("held", "review", "watch", "draft")}
        counts["review"] = sum(needs_review(t) for t in desk_theses)
        initial = next((k for k in counts if counts[k]), "all")
        P.append('<div class="lifecycle" role="group" aria-label="Strategy status">')
        for key, label in (("held", "Held"), ("review", "Under review"), ("watch", "Watching"), ("draft", "Drafts"), ("all", "All")):
            count = len(desk_theses) if key == "all" else counts[key]
            P.append(f'<button type="button" data-filter="{key}" aria-pressed="{"true" if key == initial else "false"}">{label} <span>{count}</span></button>')
        P.append('</div><label class="search-label" for="strategy-search">Find a strategy or ticker</label>'
                 '<input id="strategy-search" type="search" placeholder="Search your strategies…" autocomplete="off">'
                 '<p id="strategy-count" role="status" aria-live="polite"></p>'
                 '<div id="strategy-empty" class="strategy-empty" hidden>No strategies match this view. Try another status or search.</div>')
        P.append(f'<div class="ds" style="margin-bottom:16px">{len(desk_theses)} thesis views · '
                 'Review can include held strategies. Holdings can appear in multiple views; values should not be added together.</div>')
        import re as _re
        from officekit import thesis_board as _tb2
        _ref_goal = next((g for g in (d.get("goals") or []) if g.get("kind") in ("spending", "retirement")), None)

        def _md_b(s):
            return _re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", esc(s))

        for t in desk_theses:
            vraw = str(t["verdict"]).upper() if t.get("verdict") else ""
            vb = esc(_verdict_label(t["verdict"])) if t.get("verdict") else ""
            court = f' · reviewed {esc(t["court_date"])}' if t.get("court_date") else ""
            nxt = f' · next {esc(t["next_date"])}' if t.get("next_date") else ""
            state = lifecycle(t)
            review_needed = needs_review(t)
            state_label = {"held": "Held · review needed" if review_needed else "Held", "review": "Awaiting review", "watch": "Watching", "draft": "Draft · unreviewed"}[state]
            symbols = [p["symbol"] for p in t["positions"] if p.get("symbol")]
            subtitle = ' · '.join(symbols[:4]) + (f' · +{len(symbols)-4} more' if len(symbols) > 4 else '')
            subtitle = subtitle or 'No positions yet'
            search = ' '.join([t["label"], t["sid"]] + symbols)
            P.append(f'<details class="scard thesis-card" data-state="{state}" data-review="{str(bool(review_needed)).lower()}" data-search="{esc(search.lower())}" id="thesis-{esc(t["sid"])}">'
                     f'<summary><span class="scnm">{esc(t["label"])}<span class="thesis-meta">'
                     f'{esc(subtitle)}</span></span>'
                     f'<span class="st st-{"amber" if review_needed or state == "review" else "emerald" if state == "held" else "slate"}">{state_label}</span>'
                     f'<div class="scdd"><b>{_fmt(t["value"])}</b><small>{t["n"]} {("position" if t["n"] == 1 else "positions") if state == "held" else ("candidate" if t["n"] == 1 else "candidates")}</small></div>'
                     '<span class="chev">&#9660;</span></summary><div class="scbody">')
            if vb:
                P.append(f'<div class="note"><b>Reviewed:</b> <span title="court verdict code: {esc(vraw)}">{vb}</span>{court}{nxt}</div>')
            if t.get("pack"):
                reviewed = bool(t.get("court_date") or t.get("verdict"))
                lead = ("Reviewed by the court." if reviewed
                        else "Not yet reviewed by the court.")
                fmt_status = (t.get("review_status") or "schema_valid").replace("_", " ")
                auth = f' contributed by {esc(t.get("author"))}' if t.get("author") else ""
                P.append(f'<div class="note"><b>{lead}</b> Authored strategy pack{auth}.'
                         f'<details class="prov"><summary>Provenance &amp; format check</summary>'
                         f'<span class="ds">Automated format check: {esc(fmt_status)}. These checks validate the '
                         f'pack\'s structure only — they do not establish investment merit or that it has been '
                         f'through diligence.</span></details></div>')
            if t.get("thesis"):
                P.append(f'<div class="ds">{esc(t["thesis"])}</div>')
            # WHY IT FITS — sleeve-level explainer (edge + bucket + this goal)
            why = _tb2.explain_sleeve(t, _ref_goal, d.get("as_of", ""), model=m)
            if why:
                P.append(f'<div class="tlab">Thesis, risk and goal fit</div>'
                         f'<div class="ds">{_md_b(why)}</div>')
            # full thesis deck (contributed pack DECK.md, or a courted pitch deck)
            if t.get("deck"):
                auth = f' <span class="g">· by {esc(t.get("author",""))}</span>' if t.get("author") else ""
                P.append(f'<div class="ds"><a href="thesis_deck_{esc(t["sid"])}.html">full thesis deck &rarr;</a>{auth}</div>')
            if t.get("edge"):
                ed = t["edge"]
                et = ed.get("edge_type") if isinstance(ed, dict) else ed        # edge may be a rich dict
                if et:
                    P.append(f'<div class="tlab">Edge</div><div class="ds">{esc(str(et))}</div>')
            P.append(f'<div class="tlab">Positions{court}{nxt}</div>')
            for p in t["positions"]:
                hs = esc(asset_slug(p["symbol"] or "?"))
                pnl = p.get("upnl") or 0
                pv = esc(_verdict_label(p["verdict"])) if p.get("verdict") else ""
                P.append(f'<div class="slv"><span><a href="asset_{hs}.html">{esc(p["symbol"])}</a>'
                         + (f'<span class="g"> · {pv}</span>' if pv else "")
                         + (f'<span class="g"> · uPnL {_fmt(pnl)}</span>' if pnl else "")
                         + f'</span><b>{_fmt(p["mv"])}</b></div>')
            P.append('</div></details>')

    if not desk_theses:
        P.append('<div class="strategy-empty">No thesis views yet. Start with your goal plan or create a strategy below.</div>')
    if taxonomy:
        P.append('<details class="workspace-section" id="strategy-lenses"><summary>Explore by goal or intended role<span>Alternative views of the same holdings</span></summary>' + ''.join(taxonomy) + '</details>')
    imp = (f'<form method="POST" action="{esc(desk_import_endpoint)}" style="display:inline;margin-left:10px">'
               f'<button type="submit" class="btn2" style="font-size:11px;padding:3px 9px">↻ import from desk board</button></form>'
               if desk_import_endpoint else "")
    if desk_import_endpoint:
        P.append(f'<details class="workspace-section"><summary>Import research<span>Bring a snapshot from the desk board into this office</span></summary>{imp}</details>')

    # ---- the taxonomy: goal -> offered strategies -> courted assets -> decks ----
    if goal_menu:
        decisions = d.get("strategy_decisions") or {}

        def _goal_adopted(sid, gid):
            return any(o.get("source") == "goal" and o.get("ref") == gid
                       for o in (decisions.get(sid, {}).get("origins") or []))

        P.append('<details class="workspace-section" id="goal-plan" open><summary>Your goal plan<span>Funding gaps, adopted strategies and decisions</span></summary>')
        first = True
        for gid, entry in goal_menu.items():
            g, ev = entry["goal"], entry["eval"]
            P.append(f'<details class="scard" id="goal-{esc(gid)}"{" open" if first else ""}>'
                     f'<summary><span class="scic">🎯</span>'
                     f'<span class="scnm">{esc(ev["label"])} — {esc(ev["target_txt"])}</span>'
                     f'<span class="st st-{"emerald" if ev["status"] == "OK" else "amber" if ev["status"] == "TIGHT" else "coral"}">{esc({"OK": "On track", "TIGHT": "Close to limit", "SHORT": "Funding gap"}.get(ev["status"], ev["status"]))}</span>'
                     f'<div class="scdd">{ev["ratio"]:.2f}×</div><span class="chev">&#9660;</span></summary>'
                     f'<div class="scbody">')
            first = False
            P.append(f'<p class="ds">{esc(ev["detail"])}</p>')
            if "closing_ratio" in ev:
                P.append(f'<p class="ds">Cash to close: {ev["closing_ratio"]:.2f}× covered · Annual carry: {ev["carry_ratio"]:.2f}× covered</p>')
            for opt in entry["options"]:
                sid = opt["sid"]
                lib = STRATEGY_LIB.get(sid) or {"title": decisions.get(sid, {}).get("title", sid)}
                adopted = _goal_adopted(sid, gid)
                tag = ('<span class="st st-violet">PRIMARY</span> ' if opt["primary"] else "")
                if adopted:
                    st_label, st_tone = STATUS_TONE.get(decisions.get(sid, {}).get("status", "considering"),
                                                        STATUS_TONE["considering"])
                    toggle = _adopt_toggle(True, gid, sid, goal_adopt_endpoint, goal_unadopt_endpoint)
                    goal_proposal = next((p for p in (proposals or []) if p["strategy_id"] == sid and p["source"] == "goal" and p["source_ref"] == gid and p["status"] != "superseded"), None)
                    if goal_proposal and goal_proposal["status"] != "adopted":
                        toggle = f'<a href="/pages/proposal_{esc(goal_proposal["id"])}.html">Review proposal →</a>'
                    head = (f'<div class="slv"><span>{tag}<b>{esc(lib["title"])}</b>'
                            f'<span class="g"> · {esc(opt["why"])}</span></span>'
                            f'<span style="display:flex;gap:8px;align-items:center">'
                            f'<span class="st st-{st_tone}">{st_label}</span>{toggle}</span></div>')
                    P.append(head)
                    # the adopted strategy's courted assets, each with its full deck
                    for a in adj_by_sid.get(sid, [])[-8:]:
                        deck = f'deck_{a["id"][:8]}.html'
                        from officekit.render_signals import asset_slug as _slug2
                        aslug = esc(_slug2(a["symbol"]))
                        P.append(f'<div class="slv" style="padding-left:16px">'
                                 f'<span><a href="asset_{aslug}.html"><b>{esc(a["symbol"])}</b></a>'
                                 f'<span class="g"> · {esc(a["date"])} · <a href="{deck}">full pitch deck &rarr;</a>'
                                 f' · <a href="asset_{aslug}.html">signals &rarr;</a></span></span>'
                                 f'<b>{esc(a["verdict"])}</b></div>')
                    if court_endpoint:
                        P.append(f'<form method="POST" action="{esc(court_endpoint)}" style="display:flex;gap:8px;margin:6px 0 4px 16px">'
                                 f'<input type="hidden" name="sid" value="{esc(sid)}">'
                                 '<input name="symbol" placeholder="court a candidate ticker" required style="flex:1;background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:6px 10px">'
                                 '<button type="submit" style="background:var(--violet);color:#0b0e12;border:0;border-radius:8px;padding:6px 12px;font-weight:700;cursor:pointer">Run court</button></form>')
                    if holdings_endpoint:
                        P.append(f'<form method="POST" action="{esc(holdings_endpoint)}" style="display:flex;gap:8px;margin:0 0 10px 16px">'
                                 f'<input type="hidden" name="sid" value="{esc(sid)}">'
                                 '<input name="symbol" placeholder="bought ticker" required style="flex:1;background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:6px 10px">'
                                 '<input name="amount" placeholder="$" required style="flex:1;background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:6px 10px">'
                                 '<button type="submit" style="background:var(--emerald);color:#08110d;border:0;border-radius:8px;padding:6px 12px;font-weight:700;cursor:pointer">Record purchase</button></form>')
                elif goal_adopt_endpoint:
                    P.append(f'<div class="slv"><span>{tag}{esc(lib["title"])}'
                             f'<span class="g"> · {esc(opt["why"])}</span></span>'
                             f'{_adopt_toggle(False, gid, sid, goal_adopt_endpoint, goal_unadopt_endpoint)}</div>')
                else:
                    P.append(f'<div class="slv"><span>{tag}{esc(lib["title"])}'
                             f'<span class="g"> · {esc(opt["why"])}</span></span><b>—</b></div>')
            P.append('<div class="ds" style="margin-top:6px">Adopting queues the strategy under this goal '
                     '(origin recorded); courts adjudicate candidates inside the mandate; recorded purchases '
                     'become the sleeve that serves the goal.</div></div></details>')

    if goal_menu:
        P.append('</details>')
    P.append('<details class="workspace-section" id="strategy-library"><summary>Strategy library &amp; mandates<span>Current sleeves, available approaches, and recorded decisions</span></summary>')
    cur = [r for r in rows if r["sleeves"] or r["holds"]]
    rest = [r for r in rows if not (r["sleeves"] or r["holds"])]
    for heading, group in (("Current sleeves", cur), ("Planned &amp; available", rest)):
        P.append(f'<h2>{heading}</h2>')
        for r in group:
            lib, sid = r["lib"], r["sid"]
            st_label, st_tone = STATUS_TONE.get(r["status"], STATUS_TONE["not_decided"])
            cur_txt = f'<b>{r["cur_pct"]:.1f}%</b> now' if r["sleeves"] or r["holds"] else "—"
            tgt_txt = f' → <b>{r["target_pct"]:g}%</b> target' if r["target_pct"] is not None else " · no target"
            P.append(f'<details class="scard" id="strat-{sid}">'
                     f'<summary><span class="scic">{lib["ic"]}</span><span class="scnm">{esc(lib["title"])}</span>'
                     f'<span class="st st-{st_tone}">{st_label}</span>'
                     f'<div class="scdd">{cur_txt}{tgt_txt}</div><span class="chev">▼</span></summary>'
                     f'<div class="scbody"><div class="ds">{esc(lib["desc"])}</div>')
            # tax-loss-harvesting strategies live on the Harvest page — link there
            if sid in ("direct_index", "harvest_engine"):
                P.append('<div class="tlab">Where it runs</div>'
                         f'<div class="ds"><a href="{esc(harvest_href)}">&rarr; Loss harvesting page</a>'
                         ' — realized YTD, harvestable surface, and cross-account wash-sale checks.</div>')
            if r["sleeves"] or r["holds"]:
                P.append('<div class="tlab">In the office today</div>')
                for s in r["sleeves"]:
                    n_h = len(s.get("holdings") or [])
                    n_adj = sum(1 for h in s.get("holdings", []) if h.get("adjudication"))
                    extra = (f' · {n_h} holdings' + (f', {n_adj} adjudicated' if n_adj else '')) if n_h else ''
                    tgt_s = f' · target {s["target_pct"]:g}%' if s.get("target_pct") is not None else ''
                    P.append(f'<div class="slv"><span>{esc(s["name"])}<span class="g">{extra}{tgt_s}</span></span>'
                             f'<b>{_fmt(s["value"])}</b></div>')
                    from officekit.render_signals import asset_slug
                    for h in (s.get("holdings") or [])[:12]:
                        hs = esc(asset_slug(h.get("company", "?")))
                        adjv = (h.get("adjudication") or {}).get("verdict", "")
                        P.append(f'<div class="slv" style="padding-left:16px;font-size:12px">'
                                 f'<span><a href="asset_{hs}.html">{esc(str(h.get("company", "?")))}</a>'
                                 f'<span class="g"> · <a href="asset_{hs}.html">signals &rarr;</a>'
                                 + (f' · {esc(adjv)}' if adjv else '') + '</span></span>'
                                 f'<b>{_fmt(float(h.get("amount") or 0.0))}</b></div>')
                for h, parent in r["holds"]:
                    adj = ' · adjudicated' if h.get("adjudication") else ''
                    from officekit.render_signals import asset_slug as _slug
                    hs = esc(_slug(h.get("company", "?")))
                    P.append(f'<div class="slv"><span><a href="asset_{hs}.html">{esc(h.get("company", "?"))}</a>'
                             f'<span class="g"> · holding in {esc(parent["name"])}{adj}</span></span>'
                             f'<b>{_fmt(float(h.get("amount") or 0.0))}</b></div>')
                if r["expo"]:
                    factors = [f for f in m["factors"] if round(r["expo"].get(f, 0.0), 2)]
                    if factors:
                        P.append('<div class="ds" style="margin-top:7px">Rolled-up exposure — '
                                 + " · ".join(f'{esc(f)} <b>{r["expo"][f]:+.2f}</b>' for f in factors)
                                 + '</div>')
            P.append('<div class="tlab">Sample subassets — how this is typically expressed</div><div class="trip">'
                     + "".join(f'<span>{esc(x)}</span>' for x in lib["subassets"]) + '</div>')
            if r["recommended_by"]:
                P.append('<div class="tlab">Recommended by</div><div class="trip">'
                         + "".join(f'<a href="{esc(scenarios_href)}">{esc(n)}</a>' for n in r["recommended_by"]) + '</div>')
            gc = goal_cov.get(sid)
            if gc:
                pct = (f' — goal-mandated ≈ <b>{gc["mandated_pct"]:g}%</b> of NW (claims summed across goals)'
                       if gc["mandated_pct"] is not None else
                       ' — no sized claim (retirement corpus is the whole engine\'s job)')
                P.append(f'<div class="tlab">Serving goals</div><div class="ds">'
                         + " · ".join(esc(x) for x in gc["labels"]) + pct + '</div>')
            if r["origins"]:
                glabel = {g.get("id"): g.get("label") or g.get("kind")
                          for g in (d.get("goals") or []) if g.get("id")}

                def _orig_txt(o):
                    src_ = o.get("source")
                    if src_ == "scenario":
                        return f'adopted from the Scenario Planner ({esc(o.get("ref", ""))})'
                    if src_ == "agent":
                        return f'agent-proposed ({esc(o.get("ref", ""))}) — queued, human adopts'
                    if src_ == "goal":
                        lbl = glabel.get(o.get("ref"), "a former goal")
                        return f'mandated by your goal: {esc(lbl)} — queued, human adopts'
                    return "principal-directed"
                trail = " · ".join(_orig_txt(o) + f' {esc(o.get("date", ""))}'
                                   for o in reversed(r["origins"]))
                P.append(f'<div class="tlab">Mandate trail</div><div class="ds">{trail}</div>')
            if adj_by_sid.get(sid):
                P.append('<div class="tlab">Adjudications — every pick carries its deliberation</div>')
                for a in adj_by_sid[sid][-6:]:
                    P.append(f'<div class="slv"><span><b>{esc(a["symbol"])}</b>'
                             f'<span class="g" title="{esc(a.get("rationale", ""))}"> · {esc(a["date"])}'
                             f' · {esc(a.get("tier", ""))}</span></span>'
                             f'<b>{esc(a["verdict"])}</b></div>')
            if court_endpoint:
                P.append(f'<form method="POST" action="{esc(court_endpoint)}" style="display:flex;gap:8px;margin-top:9px">'
                         f'<input type="hidden" name="sid" value="{esc(sid)}">'
                         '<input name="symbol" placeholder="candidate ticker" required style="flex:1;background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:7px 10px">'
                         '<button type="submit" style="background:var(--violet);color:#0b0e12;border:0;border-radius:8px;padding:7px 14px;font-weight:700;cursor:pointer">Run court</button>'
                         '<button type="submit" formaction="/docket" name="action" value="queue" '
                         'title="add to the docket — the drain convenes courts in budgeted batches" '
                         'style="background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:7px 14px;font-weight:700;cursor:pointer">Queue</button></form>')
            sid_docket = [i for i in (docket_items or []) if i.get("strategy") == sid and i.get("status") == "QUEUED"]
            if sid_docket:
                P.append('<div class="tlab">Docket — awaiting court</div>')
                for it in sid_docket:
                    P.append(f'<div class="slv"><span><b>{esc(it["symbol"])}</b>'
                             f'<span class="g"> · queued {esc(it.get("enqueued_utc", "")[:10])}'
                             f' · {esc(it.get("source", ""))}</span></span></div>')
                P.append('<form method="POST" action="/docket" style="margin:4px 0 2px">'
                         f'<input type="hidden" name="sid" value="{esc(sid)}">'
                         '<button type="submit" name="action" value="drain" '
                         'style="background:var(--violet);color:#0b0e12;border:0;border-radius:8px;padding:6px 12px;font-weight:700;cursor:pointer">Drain docket (convene courts)</button></form>')
            if holdings_endpoint:
                P.append(f'<form method="POST" action="{esc(holdings_endpoint)}" style="display:flex;gap:8px;margin-top:7px">'
                         f'<input type="hidden" name="sid" value="{esc(sid)}">'
                         '<input name="symbol" placeholder="bought ticker" required style="flex:1;background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:7px 10px">'
                         '<input name="amount" placeholder="$ amount" required style="flex:1;background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:7px 10px">'
                         '<button type="submit" style="background:var(--emerald);color:#08110d;border:0;border-radius:8px;padding:7px 14px;font-weight:700;cursor:pointer">Record purchase</button></form>')
            if create_endpoint:
                related = [p for p in (proposals or []) if p["strategy_id"] == sid]
                if related:
                    P.append(f'<p><a href="/pages/proposal_{esc(related[0]["id"])}.html">Open latest proposal & pitch deck →</a></p>')
                else:
                    P.append(f'<form action="/strategy/propose" method="POST"><input type="hidden" name="sid" value="{esc(sid)}"><button type="submit">Build proposal & pitch deck →</button></form>')
            if r["note"]:
                P.append(f'<div class="note"><b>Decision note:</b> {esc(r["note"])}</div>')
            elif r["status"] == "not_decided":
                P.append('<div class="note">No decision recorded — honestly undecided, not implicitly rejected.</div>')
            P.append('</div></details>')

    P.append('</details>')

    if proposals:
        P.append('<section class="workspace-section" id="proposals"><h2>Strategy proposals</h2>')
        for proposal in proposals[:30]:
            P.append(f'<p><a href="/pages/proposal_{esc(proposal["id"])}.html">{esc(proposal["brief"]["title"])}</a> · '
                     f'<span data-proposal-status="{esc(proposal["id"])}">{esc(proposal["status"].replace("_", " "))} · {esc(proposal["stage"])}</span></p>')
        P.append('</section>')
        P.append('''<script>(function(){async function update(){try{const r=await fetch('/strategy/proposals/status');if(!r.ok)return;for(const p of await r.json()){const e=document.querySelector('[data-proposal-status="'+p.id+'"]');if(e)e.textContent=p.status.replaceAll('_',' ')+' · '+p.stage;}}catch(e){}}update();setInterval(update,10000);})();</script>''')

    if create_endpoint:
        P.append(f'''<details class="workspace-section" id="create-strategy"><summary>Create a strategy<span>Research, court review, Risk Officer sizing and a pitch deck</span></summary>
<form method="POST" action="{esc(create_endpoint)}" style="background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px">
  <div class="create-grid" style="display:grid;grid-template-columns:1.4fr .6fr;gap:10px">
    <input name="title" aria-label="Strategy name" placeholder="strategy name (e.g. Japan value)" required style="background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:9px 11px">
    <input name="target_pct" aria-label="Target allocation as percent of net worth" placeholder="target %" style="background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:9px 11px">
  </div>
  <input name="subassets" aria-label="Candidate tickers to investigate" placeholder="candidate tickers to investigate (optional)" style="width:100%;margin-top:8px;background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:9px 11px">
  <input name="note" aria-label="Investment thesis and constraints" placeholder="investment thesis, constraints and what you want to achieve" style="width:100%;margin-top:8px;background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:9px 11px">
  <button type="submit" style="margin-top:10px;background:var(--emerald);color:#08110d;border:0;border-radius:9px;padding:10px 18px;font-weight:700;cursor:pointer">Build proposal →</button>
  <div class="ds" style="margin-top:8px">A name matching a library strategy attaches the decision there; anything else defines a custom strategy. The proposal researches specific implementations, convenes courts, and produces a Risk Officer review and pitch deck. Model usage is billed through your configured providers.</div>
</form></details>''')
    P.append('<div class="foot">Statuses come from your recorded decisions (strategy_decisions) or the sleeves you actually hold — never inferred. '
             'Sample subassets are examples of typical expression, not recommendations of specific securities. '
             'Records decisions and holdings; never places orders.</div>')
    P.append("""<script>
(function(){
  var search=document.getElementById('strategy-search'), buttons=Array.from(document.querySelectorAll('[data-filter]'));
  var cards=Array.from(document.querySelectorAll('.thesis-card'));
  var active=buttons.find(b=>b.getAttribute('aria-pressed')==='true');
  var filter=active?active.dataset.filter:'all';
  function apply(){
    var q=search?search.value.toLowerCase().trim():''; var n=0;
    cards.forEach(function(c){c.hidden=!((filter==='all'||(filter==='review'?c.dataset.review==='true':c.dataset.state===filter))&&c.dataset.search.includes(q));if(!c.hidden)n++;});
    buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.filter===filter)));
    var count=document.getElementById('strategy-count');if(count)count.textContent=n+' of '+cards.length+' strategies shown';
    var empty=document.getElementById('strategy-empty');if(empty)empty.hidden=n!==0;
  }
  buttons.forEach(b=>b.addEventListener('click',function(){filter=b.dataset.filter;apply();}));
  if(search)search.addEventListener('input',apply);
  function openHash(){
    var h;try{h=decodeURIComponent(location.hash.slice(1));}catch(e){return;}
    var d=document.getElementById(h);if(!d)return;
    if(d.classList.contains('thesis-card')){filter='all';if(search)search.value='';apply();}
    for(var el=d;el;el=el.parentElement){if(el.tagName==='DETAILS')el.open=true;}
    d.scrollIntoView({block:'start'});
  }
  apply();openHash();window.addEventListener('hashchange',openHash);
})();
</script>""")
    P.append('</div></body></html>')
    from officekit.mandates import stamp_forms
    return stamp_forms("\n".join(P), m.get("_commitment_revision"))
