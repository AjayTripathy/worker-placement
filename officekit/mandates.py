"""mandates — pure mandate helpers, with a paper trail.

Current HTTP creation uses strategy_routes / strategy_proposals: research,
courts and Risk Officer review precede the human adoption decision. The pure
helpers below remain compatibility APIs; they do not dispatch paid research.

Ruling (principal, 2026-09-03): strategies are built BOTH ad-hoc with principal
input AND from the Scenario Planner. Two actions, one record shape:

  create_adhoc(answers, title, ...)          — principal-directed: a decision on a
      library strategy (title matches) or a fully CUSTOM strategy (title, desc,
      subassets of the principal's own design).
  adopt_from_scenario(answers, opt, scenario) — planner-sourced: an EXPLICIT human
      click on a mitigation adopts its strategy as `planned`.

Every action appends an ORIGIN to the decision — {"source": "principal"|"scenario",
"ref", "date"} — so a strategy card can always answer "who mandated this, and
when". This is the v1 resolution of the mandate-authority question: the planner
PROPOSES, the human ADOPTS; nothing is auto-mandated and nothing is merely
tagged.

Ruling (principal, 2026-09-04): `agent` is RATIFIED as the third origin source,
with QUEUE-FOR-ADOPTION semantics — queue_agent_proposal() can only ever file
`considering` and can never touch an existing status; binding a proposal takes
the same explicit human action as any other adoption. This closes the
automated-mandate question: automated sources queue, humans bind.

Actions mutate the ANSWERS dict (the durable intake record) so rebuilds keep
decisions; intake passes `strategy_decisions` through to the balance sheet.
"""
from __future__ import annotations

import re
import math
from datetime import date


def _slug(title):
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_") or "strategy"


def validate_target_pct(value):
    """One allocation contract for UI, agent and durable proposal writers."""
    if value is None:
        return None
    try:
        if isinstance(value, bool):
            raise ValueError()
        target = float(value)
        if not math.isfinite(target) or not 0 < target <= 100:
            raise ValueError()
        return target
    except (ValueError, TypeError, OverflowError):
        raise ValueError("Target allocation must be above zero and at most 100%") from None


def require_revision(answers, expected):
    from officekit.commitments import revision
    if not expected or expected != revision(answers):
        raise ValueError("The office changed since this page was loaded. Reload and review the latest values.")


def stamp_forms(body, revision):
    """Stamp strategy/research forms from their rendered snapshot, never on submit."""
    if not revision:
        return body
    from html import escape
    return re.sub(r'(<form\b[^>]*\baction=[\"\']/(?:strategy|research)/[^\"\']+[\"\'][^>]*>)',
                  lambda m: m[1] + '<input type="hidden" name="revision" value="' + escape(revision, quote=True) + '">', body)


def _origin(source, ref, today=None):
    return {"source": source, "ref": ref, "date": (today or date.today()).isoformat()}


def adopt_from_scenario(answers, opt_id, scenario_key, today=None):
    """Explicit human adoption of a mitigation's strategy. Sets status `planned`
    when no decision exists; NEVER downgrades an existing status (an implemented
    strategy stays implemented — adoption just records another origin)."""
    from officekit.mitigations import OPT_STRATEGY
    sid = OPT_STRATEGY.get(opt_id)
    if not sid:
        raise ValueError(f"mitigation {opt_id!r} has no strategy mapping (deliberate for 'accept')")
    decs = answers.setdefault("strategy_decisions", {})
    dec = decs.setdefault(sid, {})
    dec.setdefault("origins", []).append(_origin("scenario", f"{scenario_key}/{opt_id}", today))
    if not dec.get("status"):
        dec["status"] = "planned"
    return sid


def queue_agent_proposal(answers, title, ref, target_pct=None, note=None,
                         subassets=None, desc=None, today=None):
    """An agent-drafted strategy proposal, QUEUED for human adoption. `ref` is
    the frozen agent_call ledger-record id, so the origin points at the exact
    call that argued for it. Queue-only by construction: files `considering`
    when no decision exists and NEVER writes status otherwise — no agent path
    can implement, adopt, or decline anything."""
    from officekit.render_strategies import STRATEGY_LIB
    target_pct = validate_target_pct(target_pct)
    sid = _slug(title)
    decs = answers.setdefault("strategy_decisions", {})
    dec = decs.setdefault(sid, {})
    if not dec.get("status"):
        dec["status"] = "considering"
    if target_pct is not None and dec.get("target_pct") is None:
        dec["target_pct"] = target_pct
    if note and not dec.get("note"):
        dec["note"] = note
    if sid not in STRATEGY_LIB and not dec.get("title"):   # custom draft, human may edit
        dec["title"] = title
        if desc:
            dec["desc"] = desc
        if subassets:
            dec["subassets"] = list(subassets)
    dec.setdefault("origins", []).append(_origin("agent", ref, today))
    return sid


def create_adhoc(answers, title, status="considering", target_pct=None, note=None,
                 subassets=None, desc=None, today=None):
    """Principal-directed strategy. If the title slugs to a library strategy the
    decision attaches there; otherwise a CUSTOM strategy is defined in place
    (title/desc/subassets live in the decision record)."""
    from officekit.render_strategies import STRATEGY_LIB
    if status not in ("implemented", "considering", "planned", "declined"):
        raise ValueError(f"bad status {status!r}")
    target_pct = validate_target_pct(target_pct)
    sid = _slug(title)
    decs = answers.setdefault("strategy_decisions", {})
    dec = decs.setdefault(sid, {})
    dec["status"] = status
    if target_pct is not None:
        dec["target_pct"] = target_pct
    if note:
        dec["note"] = note
    if sid not in STRATEGY_LIB:                     # custom definition, principal's design
        dec["title"] = title
        if desc:
            dec["desc"] = desc
        if subassets:
            dec["subassets"] = list(subassets)
    dec.setdefault("origins", []).append(_origin("principal", title, today))
    return sid
