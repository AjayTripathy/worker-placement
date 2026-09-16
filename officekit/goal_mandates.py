"""goal_mandates — the third mandate source: goals decompose into strategies.

The sketch's dashed arrow, made mechanical (ratified path, 2026-09-04):

  goal -> funding requirement -> gap posture -> horizon template -> sized
  proposal -> QUEUED for adoption (origin {source: "goal", ref: <goal_id>})

Every step is arithmetic over data the pages already compute — no model in
the loop. The I3 advisor later ARGUES these proposals; it never generates
them (generator-never-grades-itself). The already-ratified authority rule
applies unchanged: automated sources queue, humans bind — a goal proposal
files `considering` and can never touch an existing decision.

The mapping:
  liquidity_floor          -> cash_mgmt   (standing claim, certainty ~1)
  spending due < 2y        -> cash_mgmt   (T-bill ladder maturing into the date)
  spending 2-7y / undated  -> muni when plane-2 declares a tax state, else
                              bonds       (duration-matched to the date)
  spending 7y+             -> core_equity (time to carry equity risk)
  retirement               -> core_equity (the accumulation engine; no sized
                              target — the required corpus is the whole
                              engine's job, stated in the note instead)

Posture comes from the goal engine's own scoring: an underfunded goal (SHORT/
TIGHT) mandates growth or contribution; a funded goal near its date mandates
defeasance — same goal, opposite emphasis, decided by ratio and clock.
Sizing: target_pct = the claim / NW (the first DERIVED target in the system;
its arithmetic is shown in the note). Overlap across goals is legitimate per
the membership ruling — one ladder can serve two dated goals as views.
"""
from __future__ import annotations

from datetime import date


def _years_out(gdate, as_of):
    if not gdate:
        return None
    try:
        d0 = date.fromisoformat(str(as_of)[:10]) if as_of else date.today()
        return max(0.0, (date.fromisoformat(str(gdate)) - d0).days / 365.25)
    except ValueError:
        return None


def _menu(goal, yrs, pc):
    """-> ranked [(sid, why)] — a HANDFUL of strategy options per goal, primary
    first (UX ruling 2026-09-04: OFFER the menu; the user adopts). Pure
    horizon/kind arithmetic; the tenant's tax state reorders, never hides."""
    kind = goal.get("kind")
    taxed = bool(((pc or {}).get("jurisdictions") or {}).get("tax_state"))
    if kind == "tax_efficiency":
        opts = [("direct_index", "own the index as individual lots so losers can be harvested to offset gains"),
                ("core_equity", "the same market exposure without lot-level harvesting")]
        if taxed:
            opts.append(("muni", "tax-exempt income per your tax state — pairs with harvesting"))
        return opts
    if kind == "liquidity_floor":
        return [("cash_mgmt", "a standing claim you must always be able to pay — cash and T-bill ladders"),
                ("bonds", "short-duration bonds — slightly more yield, slightly less certainty")]
    if kind == "retirement":
        return [("core_equity", "the accumulation engine behind the retirement corpus"),
                ("direct_index", "the same engine as individual lots — adds lot-level tax-loss harvesting"),
                ("bonds", "the glide-path ballast that grows as the date approaches")]
    if yrs is not None and yrs < 2:
        return [("cash_mgmt", f"due in {yrs:.1f}y — certainty, not return; a ladder maturing into the date"),
                ("bonds", "short-duration bonds if you can tolerate small marks")]
    if yrs is None or yrs < 7:
        horizon = f"{yrs:.0f}y out" if yrs is not None else "undated"
        opts = [("bonds", (f"{horizon} — match duration to the goal date" if yrs is not None else "set a target date before choosing bond duration")),
                ("cash_mgmt", "the certainty-first alternative — accepts lower yield"),
                ("core_equity", f"{horizon} — potential growth with drawdown risk; reassess against the spending date")]
    else:
        opts = [("core_equity", f"{yrs:.0f}y out — long enough to carry equity risk"),
                ("bonds", "the conservative alternative — certainty over growth")]
    if taxed:
        muni = ("muni", "compare after-tax yields and match duration to the goal horizon")
        if yrs is None or yrs < 7:
            opts.insert(0, muni)
        else:
            opts.append(muni)
    return opts[:4]


def _template(goal, yrs, pc):
    """Primary recommendation — the head of the menu."""
    return _menu(goal, yrs, pc)[0]


def goal_strategies(m, pc=None):
    """Decompose every goal on the model into a sized strategy proposal.
    Returns [{goal_id, goal_label, sid, target_pct, note}] — deterministic,
    idempotent (same model -> same proposals). Goals without ids are skipped:
    the origin ref IS the goal id, and grading needs it."""
    from officekit.goals import evaluate_in_model
    d = m["d"]
    goals = d.get("goals") or []
    if not goals:
        return []
    NW = m.get("NW") or 0
    as_of = d.get("as_of", "")
    out = []
    for g in goals:
        gid = g.get("id")
        if not gid or g.get("implicit"):
            continue                       # intuited estimates aren't decomposed until confirmed
        ev = evaluate_in_model(g, m)
        yrs = _years_out(g.get("date"), as_of)
        sid, why = _template(g, yrs, pc)
        posture = ("defease — funded and close; convert certainty, not return"
                   if ev["ratio"] >= 1.2 and yrs is not None and yrs <= 5
                   else "grow / contribute — currently underfunded" if ev["status"] != "OK"
                   else "on track")
        claim = g.get("amount")
        tgt = None
        if claim and NW > 0 and g.get("kind") != "retirement":
            tgt = round(claim / NW * 100, 1)
        label = g.get("label") or g.get("kind")
        note = (f"{label}: {ev['target_txt']} — {ev['status']} at {ev['ratio']:.1f}x. "
                f"{why}. Posture: {posture}."
                + (f" Sizing: ${claim:,.0f} / NW = {tgt:g}% target." if tgt is not None else ""))
        out.append({"goal_id": gid, "goal_label": label, "sid": sid,
                    "target_pct": tgt, "note": note})
    return out


def queue_goal_proposals(answers, proposals, today=None):
    """File goal proposals through the mandate machinery — queue-only, exactly
    like the agent source: `considering` only when no decision exists, never
    touching an existing status/note/target; origin {source: "goal", ref:
    goal_id}. IDEMPOTENT: a decision already carrying a goal origin for the
    same goal is left alone, so an hourly rebuild never duplicates the trail.
    Returns the strategy ids newly proposed."""
    from officekit.mandates import _origin
    decs = answers.setdefault("strategy_decisions", {})
    queued = []
    for p in proposals:
        dec = decs.setdefault(p["sid"], {})
        origins = dec.setdefault("origins", [])
        if any(o.get("source") == "goal" and o.get("ref") == p["goal_id"] for o in origins):
            continue
        if not dec.get("status"):
            dec["status"] = "considering"
        if p.get("target_pct") is not None and dec.get("target_pct") is None:
            dec["target_pct"] = p["target_pct"]
        if p.get("note") and not dec.get("note"):
            dec["note"] = p["note"]
        origins.append(_origin("goal", p["goal_id"], today))
        queued.append(p["sid"])
    return queued


def goal_coverage(m):
    """The bidirectional goal<->strategy association, DERIVED at read time from
    the origin edges — never stored, so it can't drift from the trail.

    Returns {"by_goal": {goal_id: [strategy entries]},
             "by_strategy": {sid: {goal_ids, labels, mandated_pct, n_goals}},
             "live": {goal_id: goal}}

    Only LIVE goals count (an origin whose goal was deleted stays on the trail
    as history but drops out of coverage). Strategy sizing comes from the same
    resolution the strategies page uses, so both surfaces show one number.
    mandated_pct aggregates the CLAIMS of every live goal referencing the
    strategy (the fix for first-proposal-wins targets); retirement goals count
    toward n_goals but carry no sized claim — the corpus is the engine's job.
    """
    from officekit.render_scenarios import applicable_scenarios
    from officekit.render_strategies import resolve_strategies
    d = m["d"]
    live = {g["id"]: g for g in (d.get("goals") or []) if g.get("id") and not g.get("implicit")}
    rows = {r["sid"]: r for r in resolve_strategies(m, applicable_scenarios(m))}
    NW = m.get("NW") or 0
    by_goal = {gid: [] for gid in live}
    by_strategy = {}
    for sid, dec in (d.get("strategy_decisions") or {}).items():
        gids = list(dict.fromkeys(
            o["ref"] for o in dec.get("origins") or []
            if o.get("source") == "goal" and o.get("ref") in live))
        if not gids:
            continue
        r = rows.get(sid)
        entry = {"sid": sid,
                 "title": (r["lib"]["title"] if r else dec.get("title", sid)),
                 "status": (r["status"] if r else dec.get("status", "considering")),
                 "cur_pct": (r["cur_pct"] if r else 0.0),
                 "cur_val": (r["mem_val"] if r else 0.0)}
        claims = 0.0
        for gid in gids:
            by_goal[gid].append(entry)
            if live[gid].get("amount"):
                claims += float(live[gid]["amount"])
        by_strategy[sid] = {
            "goal_ids": gids,
            "labels": [live[g].get("label") or live[g].get("kind") for g in gids],
            "mandated_pct": (round(claims / NW * 100, 1) if NW and claims else None),
            "n_goals": len(gids)}
    return {"by_goal": by_goal, "by_strategy": by_strategy, "live": live}


def goal_strategy_menu(m, pc=None):
    """The offered taxonomy layer: {goal_id: {"goal", "eval", "options":
    [{sid, why, primary}]}} — a handful of strategies per goal, primary first.
    Deterministic; the user ADOPTS from this menu (nothing auto-queues)."""
    from officekit.goals import evaluate_in_model
    d = m["d"]
    goals = [g for g in (d.get("goals") or []) if g.get("id") and not g.get("implicit")]
    if not goals:
        return {}
    as_of = d.get("as_of", "")
    out = {}
    for g in goals:
        ev = evaluate_in_model(g, m)
        yrs = _years_out(g.get("date"), as_of)
        opts = _menu(g, yrs, pc)
        out[g["id"]] = {"goal": g, "eval": ev,
                        "options": [{"sid": sid, "why": why, "primary": i == 0}
                                    for i, (sid, why) in enumerate(opts)]}
    return out


def proposal_for(m, pc, goal_id, sid):
    """One sized proposal for a USER-CHOSEN (goal, strategy) pairing off the
    menu — the adopt click's payload. Same sizing arithmetic as before."""
    menu = goal_strategy_menu(m, pc)
    entry = menu.get(goal_id)
    if not entry:
        raise ValueError(f"no goal with id {goal_id!r}")
    opt = next((o for o in entry["options"] if o["sid"] == sid), None)
    if opt is None:
        raise ValueError(f"strategy {sid!r} is not on the menu for this goal")
    g, ev = entry["goal"], entry["eval"]
    NW = m.get("NW") or 0
    claim = g.get("amount")
    tgt = round(claim / NW * 100, 1) if claim and NW > 0 and g.get("kind") != "retirement" else None
    label = g.get("label") or g.get("kind")
    note = (f"{label}: {ev['target_txt']} — {ev['status']} at {ev['ratio']:.1f}x. {opt['why']}."
            + (f" Sizing: ${claim:,.0f} / NW = {tgt:g}% target." if tgt is not None else ""))
    return {"goal_id": goal_id, "goal_label": label, "sid": sid,
            "target_pct": tgt, "note": note}
