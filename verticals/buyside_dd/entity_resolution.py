"""
Stage 1.5: Entity Resolution.

Between Mode A/B claim production and dispatch, an LLM agent does basic
research to resolve deck-level subjects (issuer name, deal name, generic
descriptors) into the actual queryable real-world entities those claims
refer to.

WHY THIS STAGE EXISTS
The deck's stated subject is rarely the right query subject for downstream
M-sources. A pitch deck says "factory in Austin TX" but the permit database
is keyed on the property address, the GC, and the landlord — none of which
the deck names. Tenants don't file permits; GCs and property owners do.
Querying austin_permits by issuer name returns 0 hits and produces a
false-positive SEVERE absence-of-record finding. The factory actually
exists; we just need to do basic research to find its address first.

WHAT THIS DOES
For each Mode A/B claim where the subject isn't directly queryable, the
resolver agent:
  1. Identifies the resolution question (e.g., "what address corresponds
     to the claimed Austin TX factory?").
  2. Iterates through a bounded multi-turn loop with web_search + registry
     tools, gathering evidence to fill the missing query slots.
  3. Produces child claims with the resolved subjects + a full evidence
     trail (parent_claim_id, resolution_question, resolution_provenance).

The child claims are appended to the pipeline's claim list and dispatched
alongside the originals. The original claim is preserved so the comparator
can distinguish "deck subject doesn't query" from "even after resolution,
no record exists."

DESIGN NOTES
- Multi-turn agent uses Anthropic's tool-use API. Each tool wraps a single
  existing connector (web_discovery, austin_permits, sec_edgar_company,
  tx_comptroller_corp). Turn cap + token budget both enforced.
- Tools include a terminating `submit_resolution` that returns the
  structured output. If the agent doesn't call submit_resolution before
  the turn cap, the resolver returns an empty result (resolution_status=
  "failed_no_submission") so the pipeline continues without bad data.
- All tool calls are logged with input + output_summary + source_url so
  the per-run resolution_log.json answers exactly the questions
  "what entities did the R claims refer to, how were they resolved, and
  what's the supporting evidence?"
- Not every claim needs resolution. The agent can declare
  resolution_status="no_resolution_needed" and the original claim flows
  through unchanged. This keeps the agent cheap on the common case
  (specific addresses, known CIKs already present in the claim).
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .connectors.base import ConnectorRequest


# ─────────────────────────────────────────────────────────────────────────
# Tool registry — Anthropic tool_use schemas
# ─────────────────────────────────────────────────────────────────────────

RESOLVER_TOOLS: list[dict] = [
    {
        "name": "web_search",
        "description": (
            "Tier 1 open-web search. Given a query string, returns the top 5-10 "
            "URLs + titles + snippets. Use this to surface facts the deck doesn't "
            "state directly: factory addresses, related entities, news, LinkedIn "
            "profiles, Crunchbase mentions. Returns rate-limit error if the "
            "underlying engines throttle; in that case try a more specific query."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query, e.g., '\"American Housing Corporation\" Austin factory address'",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "austin_permits_search",
        "description": (
            "Search the Austin TX building permit database. Either by address (returns "
            "ALL permits at that address regardless of who filed — including the "
            "contractor name and original applicant) or by entity_name (returns permits "
            "where the named entity is contractor or appears in description). Address "
            "mode is preferred — tenants don't file permits, GCs and landlords do."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Street address, e.g., '4422 Supply Ct'"},
                "entity_name": {"type": "string", "description": "Company or contractor name (used only if address not provided)"},
            },
        },
    },
    {
        "name": "bozeman_permits_search",
        "description": "Search Bozeman MT building permits. Same shape as austin_permits_search.",
        "input_schema": {
            "type": "object",
            "properties": {
                "address": {"type": "string"},
                "entity_name": {"type": "string"},
            },
        },
    },
    {
        "name": "albuquerque_permits_search",
        "description": "Search Albuquerque NM building permits. Same shape as austin_permits_search.",
        "input_schema": {
            "type": "object",
            "properties": {
                "address": {"type": "string"},
                "entity_name": {"type": "string"},
            },
        },
    },
    {
        "name": "sec_edgar_company_search",
        "description": (
            "Search SEC EDGAR for any registered filer matching the given name. Returns "
            "matched company names + CIKs + recent filings count. Use to resolve a "
            "deck-named entity to its CIK, or to surface SPV/Series LLC vehicles "
            "(e.g., 'American Housing' may surface Sydecar-administered SPVs)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Entity name to search; partial matches are OK"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "sec_edgar_form_d_search",
        "description": (
            "Pull Form D filings for a SEC-registered filer. Requires CIK or exact "
            "company name. Returns each filing's totalAmountSold, totalOfferingAmount, "
            "filing date, and related-persons list."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cik": {"type": "string", "description": "10-digit zero-padded CIK"},
                "company_name": {"type": "string", "description": "Exact company name on EDGAR"},
            },
        },
    },
    {
        "name": "tx_corp_search",
        "description": (
            "Search Texas state corporate registry. Returns matched entities + taxpayer "
            "ID + mailing address. Useful for verifying entity formation, mailing "
            "address (which may diverge from claimed operational address), and DBA names."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Entity name; partial match OK"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "tdlr_ihb_search",
        "description": (
            "Search the Texas TDLR Industrialized Housing & Buildings registry — the "
            "statutory roll of modular-home MANUFACTURERS and BUILDERS. Given a company "
            "name, returns each registration's number, expiration date, PHYSICAL PLANT "
            "ADDRESS, and phone. This is the authority that turns a deck's unaddressed "
            "'Factory 1 in Austin' into a concrete street address you can then hand to "
            "austin_permits_search / OSHA. Use it whenever a claim asserts the issuer "
            "OPERATES A MODULAR/INDUSTRIALIZED-HOUSING FACTORY in Texas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_name": {"type": "string", "description": "Operating company name; suffix/case-insensitive partial match OK"},
            },
            "required": ["entity_name"],
        },
    },
    {
        "name": "submit_resolution",
        "description": (
            "TERMINATING tool. Call this exactly once when you have completed your "
            "resolution work. Returns the structured output the pipeline downstream "
            "consumes. Set resolution_status='no_resolution_needed' if the claim's "
            "subject is already directly queryable and no research is required."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "resolution_status": {
                    "type": "string",
                    "enum": ["resolved", "no_resolution_needed", "ambiguous", "failed"],
                    "description": (
                        "resolved = produced concrete resolved entities; "
                        "no_resolution_needed = claim's subject is already queryable; "
                        "ambiguous = found conflicting candidates; "
                        "failed = couldn't surface enough info to resolve"
                    ),
                },
                "resolution_question": {
                    "type": "string",
                    "description": "1-line description of what you were trying to figure out",
                },
                "resolved_entities": {
                    "type": "array",
                    "description": "Each entry is one resolved real-world entity backing the original claim",
                    "items": {
                        "type": "object",
                        "properties": {
                            "subject": {"type": "string", "description": "The queryable entity name / address / CIK"},
                            "referent_type": {
                                "type": "string",
                                "enum": ["entity", "building", "person", "parcel", "geographic_area"],
                            },
                            "role": {
                                "type": "string",
                                "description": "Why this entity matters: 'primary_facility_address', 'general_contractor', 'landlord', 'spv_vehicle', 'parent_entity', 'founder', etc.",
                            },
                            "predicate": {
                                "type": "string",
                                "description": "f_library predicate this resolved subject feeds (e.g., 'located_at_address', 'filed_permit_for', 'owns_property_at', 'raise_amount')",
                            },
                            "referent_attributes": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "M-source attribute keys to dispatch against (e.g., ['building_permits'])",
                            },
                            "confidence": {
                                "type": "number",
                                "description": "0-1 — how confident you are this resolution is correct",
                            },
                            "evidence_turn_indices": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "Indices into the tool-call log that support this entity",
                            },
                        },
                        "required": ["subject", "referent_type", "role", "predicate", "confidence"],
                    },
                },
                "notes": {
                    "type": "string",
                    "description": "Any caveats, alternative interpretations, or follow-up suggestions",
                },
            },
            "required": ["resolution_status"],
        },
    },
]


# ─────────────────────────────────────────────────────────────────────────
# Tool dispatch — maps LLM tool calls to existing connectors
# ─────────────────────────────────────────────────────────────────────────

def _dispatch_tool(tool_name: str, tool_input: dict) -> dict:
    """Execute a resolver tool call and return a compact result for the LLM.

    The compact result is what the LLM sees as `tool_result.content` —
    aim for ~1-2KB so context budget doesn't blow up over 5-6 turns.
    The full ConnectorResult is logged separately in the resolution log.
    """
    from .connectors.web_discovery import WebDiscoveryConnector
    from .connectors.austin_permits import AustinPermitsConnector
    from .connectors.bozeman_permits import BozemanPermitsConnector
    from .connectors.albuquerque_permits import AlbuquerquePermitsConnector
    from .connectors.sec_edgar import SecEdgarConnector
    from .connectors.tx_comptroller_corp import TxComptrollerCorpConnector
    from .connectors.tdlr_ihb import TdlrIhbConnector

    if tool_name == "web_search":
        c = WebDiscoveryConnector()
        # The resolver hands us a fully-composed natural-language query. Send it
        # verbatim — quote-wrapping the whole string forces an exact-phrase match
        # that returns noise/nothing (the AHC factory-address failure).
        req = ConnectorRequest(
            entity_name=tool_input["query"],
            extra={"verbatim_query": True},
        )
        r = c.query(req)
        if not r.success:
            return {"ok": False, "error": f"{r.error_kind} {(r.error_detail or '')[:200]}"}
        # Summarize for the LLM: extracted facts first, then the raw search
        # hits (so the agent can reason over snippets the fact-extractor's
        # regexes never matched — e.g. an address stated in prose).
        hits = []
        raw_results = []
        for obs in r.observations[:10]:
            if obs.attribute == "discovery_meta":
                raw_results = (obs.value or {}).get("raw_results", []) if isinstance(obs.value, dict) else []
                continue
            hits.append({
                "attr": obs.attribute,
                "value": str(obs.value)[:200],
                "url": obs.source_url,
                "snippet": (obs.extra or {}).get("snippet", (obs.extra or {}).get("title", ""))[:200],
            })
        for rr in raw_results:
            hits.append({
                "attr": "search_result",
                "value": (rr.get("title") or "")[:160],
                "url": rr.get("url"),
                "snippet": (rr.get("snippet") or "")[:240],
            })
        return {"ok": True, "n_hits": len(hits), "hits": hits}

    if tool_name in ("austin_permits_search", "bozeman_permits_search", "albuquerque_permits_search"):
        if tool_name == "austin_permits_search":
            c = AustinPermitsConnector()
        elif tool_name == "bozeman_permits_search":
            c = BozemanPermitsConnector()
        else:
            c = AlbuquerquePermitsConnector()
        req = ConnectorRequest(
            address=tool_input.get("address"),
            entity_name=tool_input.get("entity_name"),
        )
        r = c.query(req)
        if not r.success:
            return {"ok": False, "error": f"{r.error_kind} {(r.error_detail or '')[:200]}"}
        # Slim down to a useful summary
        permit_count = next((o.value for o in r.observations
                             if o.attribute.endswith("_permit_count")), 0)
        permits = []
        for obs in r.observations:
            if obs.attribute.endswith("_permit_count"):
                continue
            if isinstance(obs.value, dict):
                permits.append({k: obs.value.get(k) for k in
                                 ("permit_number", "permit_type_desc", "issue_date",
                                  "original_address1", "contractor_company_name",
                                  "description")
                                 if obs.value.get(k)})
        return {
            "ok": True,
            "permit_count": permit_count,
            "permits": permits[:10],
            "source_url": r.observations[0].source_url if r.observations else None,
        }

    if tool_name == "sec_edgar_company_search":
        c = SecEdgarConnector()
        req = ConnectorRequest(
            entity_name=tool_input["name"],
            extra={"edgar_mode": "company"},
        )
        r = c.query(req)
        if not r.success:
            return {"ok": False, "error": f"{r.error_kind} {(r.error_detail or '')[:200]}"}
        matches = []
        for obs in r.observations[:15]:
            if isinstance(obs.value, dict):
                matches.append({k: obs.value.get(k) for k in
                                ("company_name", "cik", "filings_count")
                                if obs.value.get(k)})
        return {"ok": True, "matches": matches}

    if tool_name == "sec_edgar_form_d_search":
        from .connectors.sec_edgar import SecEdgarConnector
        c = SecEdgarConnector()
        extra: dict[str, Any] = {"edgar_mode": "form_d_detail"}
        if tool_input.get("cik"):
            extra["cik"] = tool_input["cik"]
        req = ConnectorRequest(
            entity_name=tool_input.get("company_name"),
            extra=extra,
        )
        r = c.query(req)
        if not r.success:
            return {"ok": False, "error": f"{r.error_kind} {(r.error_detail or '')[:200]}"}
        filings = []
        for obs in r.observations[:10]:
            if isinstance(obs.value, dict):
                filings.append({k: obs.value.get(k) for k in
                                ("filing_date", "totalAmountSold", "totalOfferingAmount",
                                 "entity_name", "cik")
                                if obs.value.get(k) is not None})
        return {"ok": True, "filings": filings}

    if tool_name == "tx_corp_search":
        c = TxComptrollerCorpConnector()
        req = ConnectorRequest(entity_name=tool_input["name"])
        r = c.query(req)
        if not r.success:
            return {"ok": False, "error": f"{r.error_kind} {(r.error_detail or '')[:200]}"}
        matches = []
        for obs in r.observations[:10]:
            if isinstance(obs.value, dict):
                matches.append({k: obs.value.get(k) for k in
                                ("name", "taxpayer_id", "mailing_zip", "mailing_city")
                                if obs.value.get(k)})
        return {"ok": True, "matches": matches}

    if tool_name == "tdlr_ihb_search":
        c = TdlrIhbConnector()
        req = ConnectorRequest(entity_name=tool_input["entity_name"])
        r = c.query(req)
        if not r.success:
            return {"ok": False, "error": f"{r.error_kind} {(r.error_detail or '')[:200]}"}
        registrations = [o.value for o in r.observations if isinstance(o.value, dict)]
        return {
            "ok": True,
            "registrations": registrations,
            "source_url": r.observations[0].source_url if r.observations else None,
        }

    return {"ok": False, "error": f"unknown tool: {tool_name}"}


# ─────────────────────────────────────────────────────────────────────────
# Per-claim agent loop
# ─────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an entity-resolution agent doing Stage 1.5 of a due-diligence pipeline.

The pipeline has already extracted claims from a deal's materials (Mode A) and derived implied verifications (Mode B). Some of those claims have subjects that aren't directly queryable in downstream registries — a tenant company name won't appear in a permit database (only GCs and landlords do); a deal-name SPV doesn't have its own CIK; a founder's prior-venture patents are under their personal name, not the current company.

Your job: for ONE such claim, identify the queryable real-world entities behind it. Use the tools available to do basic research. Iterate with at most 6 tool calls. When done, call submit_resolution exactly once with your structured findings.

DISCIPLINE
- Prefer fact-surfacing (web_search) before fact-verifying (registry lookups). The deck rarely gives you the lookup key directly; you usually need to find an address/CIK/SPV name first, then verify it.
- Each resolved entity must cite the tool-call turn(s) that support it (`evidence_turn_indices`).
- If the claim's subject is ALREADY a queryable entity (specific address, known CIK, registered entity name with no SPV layer), call submit_resolution with status="no_resolution_needed" and return no entities.
- If you can't make progress in 2-3 tool calls, call submit_resolution with status="failed" and explain in notes.
- Don't fabricate. If the tool returns 0 hits, say so. Don't invent addresses or CIKs.

OUTPUT
- The submit_resolution `resolved_entities` field is where you put the new query subjects. Each entry's `predicate` should match an f_library predicate so downstream dispatch knows what to verify. Common predicates: located_at_address, owns_property_at, filed_permit_for, raise_amount, led_investment_round, registered_as_entity, previously_acquired.
"""


def _build_user_prompt(claim: dict, deal_context: dict) -> str:
    return f"""DEAL CONTEXT:
{json.dumps(deal_context or {}, indent=2, default=str)}

CLAIM TO RESOLVE:
- claim_id: {claim.get("claim_id")}
- subject: {claim.get("subject")!r}
- predicate: {claim.get("predicate")}
- object_value: {claim.get("object_value")!r}
- object_unit: {claim.get("object_unit")}
- scope: {json.dumps(claim.get("scope") or {}, default=str)}
- mode: {claim.get("mode", "A")}
- source_quote: {(claim.get("source_quote") or "")[:300]}

Your task: figure out which real-world entities the framework should query in order to actually verify this claim. The current subject may or may not be directly queryable. Do the research, then submit_resolution.
"""


def resolve_one_claim(
    claim: dict,
    deal_context: dict,
    client,
    model: str = "claude-sonnet-4-5",
    max_turns: int = 6,
) -> dict:
    """Run the resolver agent on a single claim.

    Returns a dict with:
      resolution_status, resolution_question, resolved_entities, notes,
      tool_calls (the full per-turn log), turns_used, terminated_by.
    """
    if client is None:
        return {
            "resolution_status": "failed",
            "notes": "no LLM client available",
            "tool_calls": [],
            "resolved_entities": [],
            "turns_used": 0,
            "terminated_by": "no_client",
        }

    messages = [{"role": "user", "content": _build_user_prompt(claim, deal_context)}]
    tool_call_log: list[dict] = []
    submission: Optional[dict] = None
    terminated_by = "turn_cap"

    for turn in range(max_turns):
        try:
            # Use streaming for the same reason pipeline.py does — max_tokens
            # is high enough to need it.
            parts: list[Any] = []
            with client.messages.stream(
                model=model,
                max_tokens=8000,
                system=SYSTEM_PROMPT,
                tools=RESOLVER_TOOLS,
                messages=messages,
            ) as stream:
                for event in stream:
                    pass  # consume the stream
                final = stream.get_final_message()
                parts = list(final.content)
                stop_reason = final.stop_reason
        except Exception as e:
            return {
                "resolution_status": "failed",
                "notes": f"LLM error on turn {turn}: {str(e)[:300]}",
                "tool_calls": tool_call_log,
                "resolved_entities": [],
                "turns_used": turn,
                "terminated_by": "llm_error",
            }

        # Append the assistant's message
        messages.append({"role": "assistant", "content": [b.model_dump() for b in parts]})

        # Process tool_use blocks
        tool_results_for_user = []
        for block in parts:
            if getattr(block, "type", None) == "tool_use":
                tool_name = block.name
                tool_input = block.input or {}

                if tool_name == "submit_resolution":
                    submission = tool_input
                    terminated_by = "submit_resolution"
                    # Echo back a tiny ack so the conversation closes cleanly
                    tool_results_for_user.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": "submission accepted",
                    })
                    continue

                result = _dispatch_tool(tool_name, tool_input)
                tool_call_log.append({
                    "turn": turn,
                    "tool": tool_name,
                    "input": tool_input,
                    "result_summary": result,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                # Truncate result content so it fits LLM context cleanly
                content_str = json.dumps(result, default=str)
                if len(content_str) > 3500:
                    content_str = content_str[:3500] + "... [truncated]"
                tool_results_for_user.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": content_str,
                })

        if submission is not None:
            break

        if not tool_results_for_user:
            # Model produced no tool calls — done
            terminated_by = "end_turn"
            break

        messages.append({"role": "user", "content": tool_results_for_user})

    # Pull out the structured submission (or fall back to empty)
    if submission is None:
        return {
            "resolution_status": "failed",
            "resolution_question": None,
            "notes": f"agent didn't call submit_resolution within {max_turns} turns",
            "resolved_entities": [],
            "tool_calls": tool_call_log,
            "turns_used": max_turns,
            "terminated_by": terminated_by,
        }

    return {
        "resolution_status": submission.get("resolution_status", "failed"),
        "resolution_question": submission.get("resolution_question"),
        "resolved_entities": submission.get("resolved_entities") or [],
        "notes": submission.get("notes"),
        "tool_calls": tool_call_log,
        "turns_used": len([c for c in tool_call_log]) or 0,
        "terminated_by": terminated_by,
    }


# ─────────────────────────────────────────────────────────────────────────
# Pipeline-level entry
# ─────────────────────────────────────────────────────────────────────────

def _should_attempt_resolution(claim: dict) -> bool:
    """Heuristic: which claims to send through the resolver.

    For v1: any Mode B claim. Mode A claims are usually already specific
    (a quote from the deck). Mode B claims are derivations and often have
    the issuer name as subject, which is the case that needs resolving.

    Tier 1 web_discovery claims (source_doc=tier1_web_discovery) are skipped
    — they're already resolved facts.
    """
    if claim.get("mode") == "B":
        return True
    return False


def resolve_claims(
    claims: list[dict],
    deal_context: dict,
    client,
    model: str = "claude-sonnet-4-5",
    max_turns_per_claim: int = 6,
) -> tuple[list[dict], list[dict]]:
    """Run the resolver on every eligible claim. Returns (resolved_claims,
    resolution_log) where resolved_claims is the list of NEW child claims
    to append to the pipeline's claim set, and resolution_log is the
    auditable per-claim record."""
    resolution_log: list[dict] = []
    new_child_claims: list[dict] = []

    for parent in claims:
        if not _should_attempt_resolution(parent):
            continue

        parent_id = parent.get("claim_id")
        print(f"  [stage 1.5] resolving {parent_id} (subject={parent.get('subject','')[:50]!r}, predicate={parent.get('predicate')})", file=sys.stderr)

        result = resolve_one_claim(
            claim=parent,
            deal_context=deal_context,
            client=client,
            model=model,
            max_turns=max_turns_per_claim,
        )

        log_entry = {
            "parent_claim_id": parent_id,
            "parent_subject": parent.get("subject"),
            "parent_predicate": parent.get("predicate"),
            "parent_object_value": parent.get("object_value"),
            "resolution_status": result["resolution_status"],
            "resolution_question": result.get("resolution_question"),
            "terminated_by": result.get("terminated_by"),
            "turns_used": result.get("turns_used", 0),
            "n_tool_calls": len(result.get("tool_calls", [])),
            "tool_calls": result.get("tool_calls", []),
            "resolved_entities": result.get("resolved_entities", []),
            "notes": result.get("notes"),
        }
        resolution_log.append(log_entry)

        # Convert resolved_entities into new child Claims (dict shape that
        # matches the rest of the pipeline). Each child carries
        # parent_claim_id, resolution_question, and resolution_provenance.
        if result["resolution_status"] != "resolved":
            continue

        for i, entity in enumerate(result.get("resolved_entities", []) or []):
            # Build the per-entity provenance from the cited turns
            cited = entity.get("evidence_turn_indices") or []
            provenance = []
            for ci in cited:
                if 0 <= ci < len(result["tool_calls"]):
                    tc = result["tool_calls"][ci]
                    provenance.append({
                        "turn": tc["turn"],
                        "tool": tc["tool"],
                        "input": tc["input"],
                        "output_summary": tc.get("result_summary"),
                        "timestamp": tc.get("timestamp"),
                    })

            child_id = f"{parent_id}.r{i+1}"
            child = {
                "claim_id": child_id,
                "source_doc": "entity_resolution_stage_1_5",
                "source_quote": f"Resolved from parent claim {parent_id} ({parent.get('subject','')!r}) via Stage 1.5; role={entity.get('role')}; confidence={entity.get('confidence')}",
                "subject": entity["subject"],
                "predicate": entity.get("predicate") or parent.get("predicate"),
                "object_value": entity.get("object_value") or parent.get("object_value"),
                "object_unit": parent.get("object_unit"),
                "scope": {**(parent.get("scope") or {}), "resolved_from": parent_id, "role": entity.get("role")},
                "confidence": float(entity.get("confidence") or 1.0),
                "mode": "R",  # Resolution
                "referent_type": entity.get("referent_type"),
                "referent_attributes": entity.get("referent_attributes") or [],
                "parent_claim_id": parent_id,
                "resolution_question": result.get("resolution_question"),
                "resolution_provenance": provenance,
            }
            new_child_claims.append(child)

        print(f"    → status={result['resolution_status']}, {len(result.get('resolved_entities') or [])} children, "
              f"{len(result.get('tool_calls', []))} tool calls, terminated_by={result.get('terminated_by')}",
              file=sys.stderr)

    return new_child_claims, resolution_log


# ─────────────────────────────────────────────────────────────────────────
# Convenience: build an Anthropic client from the same key the pipeline uses
# ─────────────────────────────────────────────────────────────────────────

def get_resolver_client():
    """Returns (client, model) or (None, None) if no key is available."""
    try:
        import anthropic
    except ImportError:
        return None, None

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        key_file = Path("~/.anthropic_api_key").expanduser()
        if key_file.exists():
            key = key_file.read_text().strip()
    if not key or not key.startswith("sk-ant-"):
        return None, None

    return anthropic.Anthropic(api_key=key), "claude-sonnet-4-5"
