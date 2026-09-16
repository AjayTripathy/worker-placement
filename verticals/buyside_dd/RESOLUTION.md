# Stage 1.5 — Entity Resolution

Sits between Mode A/B claim production and Stage 2 typing. An LLM agent does basic research to convert deck-level subjects (issuer names, deal names, generic descriptors) into the actual queryable real-world entities those claims refer to, with a full evidence trail.

## Why this stage exists

The deck's stated subject is rarely the right query subject for downstream M-sources:

| Deck-level claim | Why direct query fails | What the agent resolves to |
|---|---|---|
| "AHC factory in Austin TX" | Permits are keyed on address + GC + landlord; tenants don't appear | A specific street address; the GC of record; the landlord LLC |
| "Antler led the Series A" | Form D doesn't reliably list lead investors; SPV may be the actual filer | The Sydecar/Carta SPV name + CIK that filed Form D for the round |
| "Founder previously sold Tudu" | USPTO and prior-co records key on the founder's personal name | The founder's personal name; alt-spellings |

Without resolution, queries against the deck-level subject return 0 hits and produce false-positive SEVERE absence-of-record findings on relationships that *do* exist.

## Architecture

```
Stage 1c  (Mode A)        ─→ all_claims  ─┐
Stage 1c-B (Mode B)       ─→ all_claims  ─┤
                                          ├─→ Stage 1.5: Resolver
                                          │     • LLM agent w/ tools
                                          │     • per-Mode-B-claim multi-turn
                                          │     • bounded: 6 turns, ~$0.10/claim
                                          │
                                          └─→ Stage 2 typing → … → Findings
                                              (resolved children dispatched
                                               alongside parents)
```

For each Mode B claim, the agent:

1. Reads the claim + deal context.
2. Decides whether resolution is needed (a specific address already in the subject? Skip).
3. Calls tools in a multi-turn loop:
   - **Fact-surfacing** (`web_search`) typically first — surfaces candidate addresses, related entities, news mentions.
   - **Fact-verifying** (`austin_permits_search`, `sec_edgar_company_search`, `tx_corp_search`, etc.) — looks up the surfaced candidates in authoritative registries.
4. Terminates by calling `submit_resolution` with the structured output (status + resolved entities + evidence references).

Each resolved entity becomes a new child claim with `parent_claim_id` linking back to the Mode B parent, `resolution_question` capturing what the agent was trying to figure out, and `resolution_provenance` carrying the per-tool-call evidence trail. Children are appended to the claim list and dispatched alongside parents in Stage 5.

## Tool catalog

| Tool | Connector | What it answers |
|---|---|---|
| `web_search` | `web_discovery` (Brave / DDG) | "What does the open web say about this entity?" Returns top URLs + snippets. Use for fact-surfacing — addresses, related entities, news. |
| `austin_permits_search` | `austin_permits` | "What permits exist at this address (or under this contractor name) in Austin?" Returns permit list + contractor + applicant. |
| `bozeman_permits_search` | `bozeman_permits` | Same shape for Bozeman MT. |
| `albuquerque_permits_search` | `albuquerque_permits` | Same shape for Albuquerque NM. |
| `sec_edgar_company_search` | `sec_edgar` | "Does SEC EDGAR list any company matching this name?" Returns name + CIK + filings count. Use to surface SPV/Series LLC vehicles. |
| `sec_edgar_form_d_search` | `sec_edgar_form_d` | "What Form D filings exist for this CIK or company name?" Returns totalAmountSold + dates + related persons. |
| `tx_corp_search` | `tx_comptroller_corp` | "Is this entity registered in TX?" Returns name + taxpayer ID + mailing address. |
| `submit_resolution` | — | TERMINATING tool. Returns the structured output. The agent must call this exactly once to complete its turn. |

## Termination and budgets

- **Turn cap:** 6 tool calls per claim by default. Hard ceiling.
- **`submit_resolution` is mandatory:** if the agent doesn't call it within the turn cap, the result is logged with `terminated_by="turn_cap"` and `resolution_status="failed"` — the parent claim flows through unchanged.
- **No per-claim cost cap yet** in v1; rely on turn cap + Anthropic's per-call max_tokens=8000 ceiling. ~$0.05-0.15 per claim at Sonnet pricing on typical resolutions.

## Resolution log format (`outputs/<run>/02d_resolution_log.json`)

Per claim that was sent through the resolver, one entry:

```json
{
  "parent_claim_id": "iv_factory_austin_permits",
  "parent_subject": "The American Housing Corporation",
  "parent_predicate": "operates_industrial_facility",
  "parent_object_value": "Austin, TX",

  "resolution_status": "resolved" | "no_resolution_needed" | "ambiguous" | "failed",
  "resolution_question": "What specific physical address corresponds to AHC's claimed Austin factory, and who are the GC and landlord on permits there?",
  "terminated_by": "submit_resolution" | "turn_cap" | "end_turn" | "llm_error" | "no_client",
  "turns_used": 3,
  "n_tool_calls": 3,

  "tool_calls": [
    {
      "turn": 0,
      "tool": "web_search",
      "input": {"query": "\"American Housing Corporation\" Austin factory address"},
      "result_summary": {
        "ok": true,
        "n_hits": 8,
        "hits": [
          {"attr": "discovery_address", "value": "4422 Supply Ct, Austin, TX",
           "url": "https://loopnet.com/...", "snippet": "..."}
        ]
      },
      "timestamp": "2026-05-19T18:30:00Z"
    },
    {
      "turn": 1,
      "tool": "austin_permits_search",
      "input": {"address": "4422 Supply Ct"},
      "result_summary": {
        "ok": true,
        "permit_count": 12,
        "permits": [
          {"permit_number": "...", "issue_date": "2025-10-08",
           "contractor_company_name": "CM Constructors",
           "description": "600A electrical service upgrade"}
        ]
      },
      "timestamp": "2026-05-19T18:30:12Z"
    }
  ],

  "resolved_entities": [
    {
      "subject": "4422 Supply Ct, Austin, TX 78744",
      "referent_type": "building",
      "role": "primary_facility_address",
      "predicate": "located_at_address",
      "referent_attributes": ["building_permits"],
      "confidence": 0.95,
      "evidence_turn_indices": [0, 1]
    },
    {
      "subject": "CM Constructors",
      "referent_type": "entity",
      "role": "general_contractor",
      "predicate": "filed_permit_for",
      "referent_attributes": ["building_permits"],
      "confidence": 0.90,
      "evidence_turn_indices": [1]
    },
    {
      "subject": "IGX Burleson Park LLC",
      "referent_type": "entity",
      "role": "landlord",
      "predicate": "owns_property_at",
      "referent_attributes": ["corporate_registration"],
      "confidence": 0.85,
      "evidence_turn_indices": [1]
    }
  ],
  "notes": null
}
```

`evidence_turn_indices` are indices into the `tool_calls` array of THIS log entry; every resolved entity must cite at least one supporting tool call.

## Resolved children format

When status="resolved", new claims are appended to the pipeline's claim list (`02d_resolved_children.json` records them). Each child carries:

- `claim_id` = `<parent_id>.r<N>` (so `iv_factory_austin_permits.r1`, `.r2`, `.r3`)
- `subject` = the resolved entity name/address
- `predicate` = the f_library predicate the resolver chose
- `referent_type` + `referent_attributes` = what M-source to dispatch against
- `mode` = `"R"` (Resolution)
- `parent_claim_id` = `iv_factory_austin_permits`
- `resolution_question` = carried over from the agent's output
- `resolution_provenance` = the cited tool calls inlined with full result_summary + source_url + timestamp
- `source_quote` = a 1-line explainer ("Resolved from parent claim X via Stage 1.5; role=...; confidence=...")

The child flows through the rest of the pipeline (typing → f-rule lookup → M-source lookup → dispatch → comparator) the same as any other claim.

## Reading a finding back to its evidence

For any finding in `06_findings.json`:

1. Look at `finding.claim.claim_id`. If it ends in `.rN`, it's a Stage 1.5 child.
2. `finding.claim.parent_claim_id` points back to the Mode B parent.
3. `finding.claim.resolution_question` is the question the resolver was answering.
4. `finding.claim.resolution_provenance` is the inlined evidence trail (tool calls + URLs).
5. For the full resolver log including the discarded tool calls and notes, look up `parent_claim_id` in `02d_resolution_log.json`.

This gives a complete audit chain: deck quote → Mode A claim → Mode B implied verification → Stage 1.5 resolved subject → dispatched M-source query → finding.

## Worked example: AHC's Austin factory

**Mode B claim (parent):**
```
iv_factory_austin_permits
subject: "The American Housing Corporation"
predicate: "operates_industrial_facility"
object_value: "Austin, TX"
referent_attributes: ["building_permits", "osha_establishment"]
```

**Resolution:** the deck says "Austin" but doesn't give the address. austin_permits keyed on the issuer name returns 0 hits. The resolver agent:

1. `web_search("\"American Housing Corporation\" Austin factory")` → surfaces LoopNet listing at 4422 Supply Ct
2. `austin_permits_search(address="4422 Supply Ct")` → 12 permits including Oct 2025 600A electrical upgrade by CM Constructors; original construction permit filed by IGX Burleson Park LLC
3. `submit_resolution(status="resolved", resolved_entities=[...])`

**Children appended:**
- `iv_factory_austin_permits.r1` — subject `4422 Supply Ct...`, predicate `located_at_address`, role `primary_facility_address`
- `iv_factory_austin_permits.r2` — subject `CM Constructors`, predicate `filed_permit_for`, role `general_contractor`
- `iv_factory_austin_permits.r3` — subject `IGX Burleson Park LLC`, predicate `owns_property_at`, role `landlord`

**Downstream:** `r1` dispatches `austin_permits` with `address=4422 Supply Ct` and gets 12 permits → PASS finding. The parent finding will still be UNVERIFIABLE-via-direct-query (queried by issuer name → 0 hits), but the audit chain shows resolution succeeded.

## Failure modes worth knowing

- **Rate limiting on web_search.** Brave/DDG throttle aggressive automation. The resolver gracefully handles HTTP 429 / 202 and the agent typically retries with a more specific query. For production, use Brave Search API (paid).
- **Agent doesn't call submit_resolution.** Caught by the turn cap; result logged with `terminated_by="turn_cap"`, status="failed", parent flows through unchanged.
- **Ambiguous resolution.** Agent can return status="ambiguous" with multiple candidate entities; the comparator surfaces this as a NEEDS_HUMAN_REVIEW finding rather than dispatching against an unconfirmed subject.
- **Resolver hallucination.** Mitigated by: (a) the system prompt explicitly tells the agent to not fabricate; (b) every resolved entity must cite `evidence_turn_indices`; (c) the citations are independently logged so a human can verify. If a resolved entity has 0 cited turns, that's a red flag in the resolution log.

## What's not in v1

- **Founder→prior-venture resolution** isn't supported yet because LinkedIn-style profile lookup needs auth that isn't wired. Web search can partially do it.
- **SPV-to-CIK resolution** is partially supported via `sec_edgar_company_search` but the prompt doesn't yet teach the agent the Sydecar/Carta/AngelList SPV naming patterns explicitly.
- **Outer-loop re-resolution** (resolve → dispatch → if Tier 2 ambiguous, re-resolve deeper) isn't implemented. Single-pass resolution per claim.
- **Resolved-claim corroboration upgrades** to parent claim severity (comparator's `CORROBORATED_VIA_RESOLUTION` rule) — deferred. For now, parent + child findings are independent in the output; the analyst reading the report should consult both.
