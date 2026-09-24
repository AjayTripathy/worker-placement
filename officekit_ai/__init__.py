"""officekit_ai — the intelligence plugin tier (AI-0 skeleton).

Ratified (principal, 2026-09-04): `agent` is the third mandate-origin source,
queue-for-adoption. This package is the only place agent behavior lives —
officekit core keeps its zero-dependency, offline, never-phones-home guarantee,
and every affordance here degrades to graceful absence when the plugin can't
run (no configured provider SDK or API key). No key -> the deterministic
paths keep working unchanged and pages render byte-identically.

Contract (INTELLIGENCE.md, principles 2-4):
  - agents emit CONTRACTS, not state: answers JSON, queued strategy proposals
    (officekit.mandates.queue_agent_proposal), classification suggestions a
    human confirms. Nothing here writes balance_sheet.json directly.
  - every claim is a FROZEN CALL: record_agent_call() writes an `agent_call`
    ledger record before the claim is used anywhere, and the record id is the
    origin `ref` on any proposal it argues for — the gradeable paper trail.
  - never executes; proposals queue and humans bind. The strategy-proposal
    pipeline researches and proposes bounded allocations through configured
    model providers; it never purchases or reserves cash.

Ships in-monorepo today; publish-time split target is `officekit[ai]` with the
OpenAI and Anthropic SDK adapters (user-supplied credentials).
"""
from __future__ import annotations


# Research uses the requested GPT-6 provider; classification retains its
# inexpensive, separately configurable slot rather than a flagship-only router.
DEFAULT_MODEL = "gpt-6-astra"
CLASSIFY_MODEL = "claude-haiku-4-5"


def available(folder=None, slot="intake"):
    """True iff a slot's provider can actually construct a client (BYOM: the
    slot's models.json config decides which provider and which key env-var —
    defaults use OpenAI for reasoning and Anthropic for classification). Callers
    gate every AI affordance on this — False means the affordance simply
    doesn't render, never an error."""
    from officekit_ai.models import slot_available
    return slot_available(slot, folder)


def client(folder=None, slot="intake"):
    """A (client, model-agnostic) client for a slot via the provider registry.
    Raises RuntimeError with a plain-language reason when unavailable."""
    from officekit_ai.models import client_for
    return client_for(slot, folder)[0]


def record_agent_call(ledger_path, capability, model, payload, office_id=None, today=None):
    """Freeze one agent claim to the learning ledger BEFORE it is used.
    Returns the record; its `id` is the `ref` for any mandate origin or
    confirmation step the claim feeds. `payload` should carry the claim and
    its confidence in gradeable form (never raw document text beyond what the
    grade needs). agent_call records are deliberately NOT in the shareable
    allowlist — they may contain client-specific text."""
    from officekit.learning import record
    return record(ledger_path, "agent_call",
                  {"capability": capability, "model": model, **payload},
                  today=today, office_id=office_id)


def propose_strategy(answers, ledger_path, title, argument, personal_context,
                     model=DEFAULT_MODEL, target_pct=None, subassets=None,
                     desc=None, office_id=None, today=None):
    """File an agent-drafted strategy proposal the ratified way: freeze the
    call, then queue for adoption with the record id as the origin ref.
    Queue-only semantics are enforced by mandates.queue_agent_proposal —
    this can never implement, adopt, or decline anything.

    `personal_context` is the plane-2 gate (ruling 2026-09-04): pass the
    tenant's loaded document (personal_context.load(folder)) — empty is fine,
    None refuses. Every advise-class entry point in this package takes it."""
    from officekit.mandates import queue_agent_proposal, validate_target_pct
    from officekit.personal_context import require
    require(personal_context, "propose")
    target_pct = validate_target_pct(target_pct)
    rec = record_agent_call(ledger_path, "strategy_draft", model,
                            {"title": title, "argument": argument},
                            office_id=office_id, today=today)
    sid = queue_agent_proposal(answers, title, ref=rec["id"], target_pct=target_pct,
                               note=argument, subassets=subassets, desc=desc, today=today)
    return sid, rec
