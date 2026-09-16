"""implicit_strategies — the strategies the office is ALREADY running.

An asset allocation IS a set of strategies, held rather than proposed: a
public-equity sleeve is core equity, a direct-index SMA is direct indexing, a
muni sleeve is municipal credit, a bond sleeve is core fixed income, cash/MMF is
cash management. resolve_strategies already SIZES these by category fallback and
marks them implemented — but nothing LINKS them to the goals they fund, so a
goal reads "no strategy serving yet" beside the very assets serving it.

Run at build (idempotent), this registers each held allocation as an IMPLEMENTED
strategy decision (origin source "holding" — the sleeve is the evidence) and
attaches it to every goal whose strategy menu names it. It never downgrades an
explicit adoption, and stale goal links drop out of coverage on their own once
the goal is deleted.

    register(answers, data, pc=None) -> bool   # True if it changed anything
"""
from __future__ import annotations


def category_to_strategy():
    """{sleeve_category: strategy_sid} — the INVERSE of the strategy library's
    own category tags, so this stays in lockstep with resolve_strategies'
    category-fallback sizing (no second, drifting map to maintain)."""
    from officekit.render_strategies import STRATEGY_LIB
    return {v["category"]: sid for sid, v in STRATEGY_LIB.items() if v.get("category")}


def derive(data) -> dict:
    """{sid: [sleeve names]} — the strategies implied by the held asset sleeves
    (assets only, non-zero value)."""
    cat2sid = category_to_strategy()
    out = {}
    for s in data.get("sleeves", []):
        if s.get("kind") != "asset":
            continue
        try:
            if abs(float(s.get("value") or 0)) < 1:
                continue
        except (TypeError, ValueError):
            continue
        sid = cat2sid.get(s.get("category"))
        if not sid:
            continue
        out.setdefault(sid, []).append(s.get("name") or s.get("category"))
    return out


def harvest_evidence(data, folder=None):
    """Evidence that direct indexing / a tax-loss-harvest engine is ALREADY running.
    The core insight (principal 2026-09-10): ANY equity held as INDIVIDUAL LOTS —
    not a pooled fund — IS direct-indexed, i.e. lot-level tax-loss-harvestable. So
    a sleeve of individual holdings is itself the implicit strategy, alongside a
    labeled direct-index sleeve, realized harvest activity, or the principal's
    Parametric bridge. Returns a short evidence string, or None."""
    for s in data.get("sleeves", []):
        if s.get("kind") != "asset":
            continue
        cat = s.get("category")
        if cat == "direct_index":
            return s.get("name") or "direct-index SMA"
        # individually-held equities (line-item holdings, not a fund ticker) are
        # direct-indexed by construction — you own the lots, so you can harvest them
        if cat in ("public_equity", "single_name_equity") and (s.get("holdings")):
            n = len(s["holdings"])
            return (s.get("name") or "individually-held equities") + f" ({n} lots — lot-level TLH)"
    tm = data.get("tax_model") or {}
    try:
        if float(tm.get("realized_losses_ytd") or tm.get("harvest_losses_2026") or 0) > 0:
            return "realized tax-loss harvest activity"
    except (TypeError, ValueError):
        pass
    try:
        from officekit import harvest as _hv
        if folder and _hv._is_principal_office(folder):
            pb = _hv._parametric_bridge(folder)
            if pb:
                return pb.get("label") or "Parametric direct-index SMA"
    except Exception:
        pass
    return None


def register(answers, data, pc=None, today=None, folder=None) -> bool:
    """Register implied strategies as IMPLEMENTED decisions and attach them to
    the goals they fund. Mutates answers['strategy_decisions']. Returns True if
    anything changed (so the caller can re-materialize the balance sheet)."""
    from officekit.goal_mandates import _menu, _years_out
    from officekit.mandates import _origin
    implied = derive(data)
    decs = answers.setdefault("strategy_decisions", {})
    changed = False

    # a direct-index SMA / harvest engine that runs via the Harvest bridge (not a
    # plain sleeve) is IMPLEMENTED — intuit it so it never reads "not implemented".
    ev = harvest_evidence(data, folder)
    if ev:
        ref = f"held: {ev} (see Harvest page)"[:120]
        for sid in ("direct_index", "harvest_engine"):
            dec = decs.setdefault(sid, {})
            if dec.get("status") not in ("implemented", "declined"):
                dec["status"] = "implemented"
                changed = True
            origins = dec.setdefault("origins", [])
            hold = next((o for o in origins if o.get("source") == "holding"), None)
            if hold is None:
                origins.append(_origin("holding", ref, today))
                changed = True
            elif hold.get("ref") != ref:                 # refresh a stale evidence label
                hold["ref"] = ref
                changed = True

    if not implied:
        return changed

    # 1) each held allocation becomes an implemented strategy (one holding origin,
    #    naming the sleeves as evidence). Never downgrade an explicit decision.
    for sid, sleeves in implied.items():
        dec = decs.setdefault(sid, {})
        origins = dec.setdefault("origins", [])
        if not dec.get("status"):
            dec["status"] = "implemented"
            changed = True
        if not any(o.get("source") == "holding" for o in origins):
            origins.append(_origin("holding", ("held: " + ", ".join(sleeves))[:120], today))
            changed = True

    # 2) attach: a held strategy serves a goal when it's in that goal's menu.
    as_of = data.get("as_of") or ""
    for g in data.get("goals") or []:
        gid = g.get("id")
        if not gid:
            continue
        yrs = _years_out(g.get("date"), as_of)
        for sid, _why in _menu(g, yrs, pc):
            if sid not in implied:
                continue
            origins = decs[sid].setdefault("origins", [])
            if not any(o.get("source") == "goal" and o.get("ref") == gid for o in origins):
                origins.append(_origin("goal", gid, today))
                changed = True
    return changed
