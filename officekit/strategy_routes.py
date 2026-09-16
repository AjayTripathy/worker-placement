"""Every strategy creation door opens the same durable proposal workflow."""
from copy import deepcopy
import json

from officekit import strategy_proposals as proposals

PATHS = {"/strategy/adopt", "/strategy/new", "/strategy/goal-adopt", "/strategy/propose",
         "/strategy/proposal/retry", "/strategy/proposal/revise", "/strategy/proposal/decide"}


def handle(route, folder, get, build, model_for_answers):
    from officekit.mandates import require_revision
    if not (folder / "answers.json").exists():
        raise ValueError("Build your office before creating a strategy")
    answers = json.loads((folder / "answers.json").read_text())
    # Exact successful decision replay can repair a derived page after publication.
    # New decisions, including decline, always require the page's office revision.
    if route == "/strategy/proposal/decide":
        p = proposals.load(folder, get("pid"))
        decision = (answers.get("strategy_decisions", {}).get(p["strategy_id"], {}).get("proposal_decision") or {})
        if decision.get("id") == p["id"] and decision.get("action") == get("action"):
            p.update(status="adopted" if get("action") == "adopt" else "declined", stage="Decision recorded")
            proposals.save(folder, p)
            return p["id"], False
    require_revision(answers, get("revision"))
    model = model_for_answers(answers, folder)
    old = None
    if route == "/strategy/proposal/retry":
        p = proposals.retry(folder, get("pid"))
    elif route == "/strategy/proposal/decide":
        updated, p = proposals.decide(folder, answers, get("pid"), get("action"), model)
        build(updated, folder)
        p.update(status="adopted" if get("action") == "adopt" else "declined", stage="Decision recorded")
        p["history"].append({"at": proposals.now(), "stage": p["status"]})
        proposals.save(folder, p)
        return p["id"], False
    else:
        from officekit.render_strategies import STRATEGY_LIB
        option, title, target = None, None, None
        request = get("note") or ""
        if route == "/strategy/adopt":
            from officekit.mitigations import OPT_STRATEGY
            from officekit.strategy_playbooks import PLAYBOOKS
            from officekit.render_scenarios import applicable_scenarios
            option = get("opt")
            sid = OPT_STRATEGY.get(option) or ("risk_acceptance" if option == "accept" else None)
            if not sid or option not in PLAYBOOKS:
                raise ValueError("Choose a supported mitigation")
            sc = next((s for s in applicable_scenarios(model) if s["key"] == get("scenario")), None)
            if not sc or option not in sc.get("opts", []):
                raise ValueError("This mitigation is not on the selected scenario")
            source, ref = "scenario", get("scenario") + "/" + option
            title = PLAYBOOKS[option][0]
            request = "Scenario: " + sc["name"] + ". " + (sc.get("desc") or "")
        elif route == "/strategy/goal-adopt":
            from officekit.goal_mandates import proposal_for
            from officekit.personal_context import load
            goal = proposal_for(model, load(folder), get("gid"), get("sid"))
            sid, source, ref = goal["sid"], "goal", goal["goal_id"]
            request, target = goal["note"], goal["target_pct"]
            # Goal claims may exceed NW. Keep the full claim in the brief;
            # allocation percentages are bounded and cannot promise the gap.
            target = min(100, target) if target and target > 0 else None
        elif route == "/strategy/proposal/revise":
            old = proposals.load(folder, get("pid"))
            if old["status"] in {"queued", "running", "superseded"}:
                raise ValueError("Finish or resume the current review before revising")
            sid, source, ref = old["strategy_id"], old["source"], old["source_ref"]
            option, title, target = old["brief"]["option"], old["brief"]["title"], old["target_pct"]
            request = old["brief"]["request"]
            if get("request"):
                request += "\nRevision: " + get("request")
        elif route == "/strategy/propose":
            sid = get("sid")
            dec = (answers.get("strategy_decisions") or {}).get(sid)
            if sid not in STRATEGY_LIB and dec is None:
                raise ValueError("Choose an existing strategy")
            dec = dec or {}
            source, ref = "principal", sid
            origin = next((o for o in reversed(dec.get("origins", [])) if o.get("source") == "agent"), None)
            if origin:
                source, ref = "agent", origin["ref"]
            title, request, target = dec.get("title"), dec.get("note", ""), dec.get("target_pct")
        else:
            from officekit.mandates import _slug
            title = get("title").strip()
            if not title:
                raise ValueError("Name the strategy to investigate")
            sid = _slug(title)
            source, ref = "principal", title
            target = get("target_pct") or None
            if get("subassets"):
                request += "\nCandidates to compare: " + get("subassets")
        updated = deepcopy(answers)
        p = proposals.create(folder, updated, model, sid, source, ref, option=option, title=title,
                             request=request, target_pct=target, revision_of=old["id"] if old else None)
        if p["status"] == "queued" and updated != answers:
            try:
                build(updated, folder)
            except Exception:
                p.update(status="error", stage="Office publication failed", errors=["The proposal was saved, but its mandate could not be published. Create a revision after correcting the office error."])
                proposals.save(folder, p)
                raise
            proposals.bind_snapshot(folder, p, updated, model_for_answers(updated, folder))
        if old:
            old.update(status="superseded", stage="Revised", superseded_by=p["id"])
            proposals.save(folder, old)
    return p["id"], p["status"] in {"queued", "running"}
