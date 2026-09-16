"""risk_officer — deterministic risk lint across the whole book.

The principal-ratified role (2026-09-02): conflict adjudication across mandates
AND goals; deterministic lint first (this module), complemented by the
allocation review in officekit_ai.strategy_proposal. It ADVISES, never vetoes. Findings are severity-ranked and each carries a
concrete next step (rebalance in the growth calculator, reprioritize goals,
hedge, harvest). Fed by the stock/bond mix (portfolio_mix) and goal contention.

    review(m, answers) -> [ {severity, title, detail, advice, action} ]
"""
from __future__ import annotations

from officekit.fmt import fmt_usd as _fmt

_SEV_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}
_GROWTH = {"kind": "growth", "label": "open the growth calculator"}
_OFFICE = {"kind": "link", "href": "/pages/office.html", "label": "reprioritize goals"}


def review(m, answers=None, personal_context=None):
    d = m["d"]
    NW = m.get("NW") or 0
    assets = m["assets"]
    goals = d.get("goals") or []
    F = []
    if d.get("commitments"):
        from officekit.commitments import cash_calendar
        cal = cash_calendar(m)
        if cal["shortfall"]:
            F.append({"severity": "high", "title": "Cash needed for commitments",
                      "detail": f"Scheduled obligations and reserves exceed current cash by {_fmt(cal['shortfall'])}. "
                                "Future income and investment sales are excluded.",
                      "advice": "review payment dates and decide how to fund the cash gap before committing more",
                      "action": {"href": "/pages/capital.html", "label": "Open cash calendar"}})

    # 1) concentration — a single sleeve driving the whole book
    for s in sorted(assets, key=lambda x: -x["value"]):
        pct = s["value"] / NW * 100 if NW else 0
        if pct >= 25 and s["category"] not in ("cash", "cash_pending"):
            F.append({"severity": "high" if pct >= 40 else "medium",
                      "title": (f"Large direct-index allocation — {pct:.0f}% of net worth" if s["category"] == "direct_index" else f"Concentration — {s['name']} is {pct:.0f}% of net worth"),
                      "detail": (f"{_fmt(s['value'])} in a diversified index sleeve. Review equity and sector exposure; sleeve size alone does not imply single-name concentration."
                                 if s["category"] == "direct_index" else f"{_fmt(s['value'])} in one sleeve; its moves dominate the whole book's risk."),
                      "advice": ("review sector and single-name exposures within this SMA, then compare diversification or an index hedge."
                                 if s["category"] == "direct_index" else
                                 "compare diversification, an index hedge, or a tax-aware transition into a direct-index SMA."),
                      "action": _GROWTH})
            break

    # 2) stock/bond mix — volatility / drawdown
    from officekit.portfolio_mix import current_mix, mix_stats
    cur = current_mix(m)
    st = mix_stats(cur["stocks_pct"], min(cur["bonds_pct"], 100 - cur["stocks_pct"]))
    if cur["stocks_pct"] >= 75 and cur["total"] > 0:
        F.append({"severity": "medium",
                  "title": f"Stock-heavy mix — {cur['stocks_pct']:.0f}% equities",
                  "detail": f"~{st['vol']*100:.0f}% volatility; about -{st['drawdown_1in20']*100:.0f}% "
                            f"({_fmt(cur['total']*st['drawdown_1in20'])}) in a 1-in-20 year.",
                  "advice": "if any goal is near-term, shift toward bonds to shorten the funding gap.",
                  "action": _GROWTH})

    # Individual affordability is the same contract used by Home and Scenarios.
    from officekit.goals import evaluate_in_model
    for g in goals:
        if g.get("implicit"):
            continue                       # intuited estimates aren't flagged as funding gaps
        ev = evaluate_in_model(g, m)
        if ev["status"] == "SHORT" and g.get("kind") != "liquidity_floor":
            F.append({"severity": "high", "title": f"Funding gap — {ev['label']}",
                      "detail": ev["detail"], "advice": "review the cost, timing and funding alternatives.",
                      "action": {"kind": "link", "href": f"/pages/goal_{g['id']}.html" if g.get("id") else "/pages/office.html",
                                 "label": "Review goal options"}})
    if m.get("sync_stale"):
        F.append({"severity": "high", "title": "Some balances need a refresh",
                  "detail": f"{m['sync_stale']} synced sleeves have stale source data. Refresh before acting on these estimates.",
                  "advice": "refresh the source or review the statement date.",
                  "action": {"kind": "link", "href": "/pages/imports.html", "label": "Review sources"}})

    # 3) goal contention — do the goals fit together
    active = [g for g in goals if g.get("kind") != "tax_efficiency"]
    if len(active) >= 2:
        from officekit.goal_contention import contention
        con = contention(m, goals)
        if not con["feasible"]:
            F.append({"severity": "high", "title": "Goals conflict — they can't all be funded",
                      "detail": con["verdict"],
                      "advice": "prioritize: trim or defer the squeezed goals, or add income.",
                      "action": _OFFICE})

    # 4) factor tilt — the whole-portfolio exposure vector (the Risk Officer's read)
    from officekit.harvest import factor_tilt
    tilt = factor_tilt(m)
    spx = tilt.get("S&P 500", 0)
    tilt_txt = " · ".join(f"{esc_f}{v:+.2f}" for esc_f, v in
                          [(f.replace(" 500", "") + " ", tilt[f]) for f in m["factors"]])
    # flag the largest exposure outside a comfort band (market up to ~1.0, others ~0.5)
    off = [(f, tilt[f]) for f in m["factors"]
           if abs(tilt[f]) > (1.05 if f == "S&P 500" else 0.6)]
    if off:
        worst = max(off, key=lambda kv: abs(kv[1]))
        F.append({"severity": "medium", "title": f"Factor tilt — heavy {worst[0]} exposure ({worst[1]:+.2f})",
                  "detail": f"portfolio tilt: {tilt_txt}. A 1% {worst[0]} move ≈ "
                            f"{worst[1]*100:+.0f}bp on net worth.",
                  "advice": "steer the stock/bond mix or add a hedge to bring the tilt back to intent.",
                  "action": _GROWTH})
    else:
        F.append({"severity": "info", "title": "Factor tilt — within band",
                  "detail": f"portfolio tilt: {tilt_txt}.",
                  "advice": "no single factor dominates beyond intent; revisit if the mix shifts.",
                  "action": _GROWTH})

    # 5) liquidity vs floors
    cash = sum(s["value"] for s in assets if s["category"] == "cash")
    floors = sum(float(g.get("amount") or 0) for g in goals if g.get("kind") == "liquidity_floor")
    if floors and cash < floors:
        F.append({"severity": "high", "title": "Liquidity below your floor",
                  "detail": f"{_fmt(cash)} in cash vs a {_fmt(floors)} liquidity floor.",
                  "advice": "raise cash or hold a T-bill ladder maturing into the claim.",
                  "action": None})

    # 6) leverage / shorts (the 131/31 extension carries a real short book)
    shorts = sum(s["value"] for s in m["sleeves"] if s.get("kind") == "asset" and s["value"] < 0)
    if shorts < -0.05 * NW and NW:
        F.append({"severity": "medium", "title": f"Leverage — {_fmt(-shorts)} short book",
                  "detail": "a long/short extension adds financing cost and a borrow/short-squeeze tail.",
                  "advice": "confirm the extension's financing drag is covered by its alpha.", "action": None})

    # 7) tax reserve (a risk the Officer flags; harvesting it is its own app)
    tax = m.get("tax") or {}
    if tax.get("net_tax", 0) > 0:
        F.append({"severity": "info", "title": f"Tax reserve on incoming gain — {_fmt(tax['net_tax'])}",
                  "detail": f"reserved against the {tax.get('char', 'ltcg').upper()} inflow at "
                            f"{tax.get('rate', 0)*100:.1f}%.",
                  "advice": "loss harvesting can shrink this — see the Harvest tab.",
                  "action": {"kind": "link", "href": "/pages/harvest.html", "label": "open loss harvesting"}})

    # Tenant exclusions are facts supplied by that tenant, never package defaults.
    from officekit.personal_context import check_exclusions
    if personal_context is None:
        F.append({"severity": "info", "title": "Exclusions not checked — personal context unavailable",
                  "detail": "Load this office's personal context to check its restrictions.",
                  "advice": "review the personal-context document", "action": None})
    else:
        for violation in check_exclusions(d, personal_context):
            e = violation["exclusion"]
            F.append({"severity": "high", "title": f"Tenant exclusion — {e['value']} present",
                      "detail": violation["where"] + (f". {e['reason']}" if e.get("reason") else ""),
                      "advice": "review this holding against your recorded restriction", "action": None})

    F.sort(key=lambda x: _SEV_ORDER.get(x["severity"], 9))
    return F
