"""Build per-ticker subagent prompts for the defense cohort run."""
from __future__ import annotations

from .defense_cohort import COHORT, COHORT_CONTEXT, COMMON_COUNTERPARTY_CIKS, CUTOFF


PROMPT_TEMPLATE = """You are a forensic-disclosure analyst running a BLINDED forward test of the Signal OS framework on a single defense-tech company. You will play the role the LLM plays in the framework's pipeline: extract claims from a filing, pick M-source queries, run them, and score severity.

== STRICT BLINDING DISCIPLINE ==
- Do NOT use WebSearch, WebFetch, or any tool that could surface post-cutoff information about this company
- Do NOT use prior training-data knowledge of any post-cutoff events about this company (bankruptcies, contract wins, acquisitions, scandals)
- Do NOT browse files outside the explicitly-named paths below. In particular, do NOT read files matching `*.hindsight.json`, `*.preslicer.json`, `_<cohort>_outcomes.py`, or any case-study markdown files
- If you find yourself reasoning "I think this company later did X, so this is suspicious", STOP. The point is to test whether the framework can detect weak signals at the cutoff, not to confirm what you might already know
- Treat this as a true forward-looking analysis from the cutoff date

== ASSIGNMENT ==
Ticker: {ticker}
CIK: {cik_padded}
Company name: {company_name}
Subject notes (cohort metadata, no outcome labels): {notes}
Cutoff date: {cutoff}
Filings dir: /Users/ajay/exalted/signalos/verticals/public_co/data/{ticker_lower}/filings/
Filings index: /Users/ajay/exalted/signalos/verticals/public_co/data/{ticker_lower}/filings_index.json
Output (you MUST write both):
  /Users/ajay/exalted/signalos/verticals/public_co/data/_local/{ticker}.input.json
  /Users/ajay/exalted/signalos/verticals/public_co/data/_local/{ticker}.scores.json

== COHORT CONTEXT ==
{cohort_context}

== RESOURCES ==
- M-source catalog: /Users/ajay/exalted/signalos/verticals/public_co/m_source_catalog.py
- Filing slicer: /Users/ajay/exalted/signalos/verticals/public_co/filing_slice.py
- Common counterparty CIKs (use with edgar_fts.query_fulltext to test counterparty disclosure):
{counterparty_block}

To call an M-source query, from the repo root:
    python3 -c "from verticals.public_co.m_source_catalog import call; import json; print(json.dumps(call('SOURCE_NAME', {{'kwarg':'val'}}), default=str, indent=2))"

== WORKFLOW ==
1. Read the filings index. Pick the most substantive PRE-CUTOFF filing (10-K preferred for US filers; S-1 if recent IPO and no 10-K yet; then 10-Q for newer interim disclosures).
2. Slice the filing to ~120K chars from key business sections + financial-statement notes:
     python3 -c "from verticals.public_co.filing_slice import slice_filing; t=open('FILING_PATH').read(); print(slice_filing(t, budget_chars=120000))" > /tmp/sliced_{ticker}.txt
   Then Read /tmp/sliced_{ticker}.txt.
3. Extract 5-8 testable factual claims per the EXTRACT RUBRIC below. Pick 1-3 M-source queries per claim from the catalog. Prefer:
     - usaspending.query_recipient_contracts / query_dod_contracts → for any DoD / federal contract claim
     - uspto_odp.query_assignee → for patent / IP claims
     - edgar_fts.query_fulltext (cik=COUNTERPARTY) → for counterparty disclosure claims (does Lockheed's 10-K mention this company?)
     - epa_frs.query_facilities → for manufacturing-plant claims (if any)
4. **CHECKPOINT 1 — immediately write input.json BEFORE running any queries.** This preserves the extraction work if the watchdog kills you mid-query. Structure:
     {{"ticker": "{ticker}", "cutoff": "{cutoff}", "filing": "<filename>", "claims": [...]}}
5. Iterate claim-by-claim:
     a. Run that claim's queries (be polite, sleep 1-2s between queries).
     b. Score severity per the SCORE RUBRIC + CALIBRATION HEURISTICS below.
     c. **CHECKPOINT 2 — immediately re-write the ENTIRE scores.json with all claims scored so far.** Do NOT batch and save at the end. After claim 1 is scored, scores.json contains 1 entry. After claim 2, it contains 2 entries. The aggregator handles partial scores.json gracefully; what matters is that a stall preserves the last-completed checkpoint.
     scores.json structure (rewritten each iteration):
     {{"ticker": "{ticker}", "scores": [...]}}
6. After the last claim is scored, report a one-line summary in your final message: "{ticker}: N claims, K queries, severity counts: PASS=x MODE=y SEVE=z RED=w UNVE=v"

== EXTRACT RUBRIC ==
HIGH discriminative claims:
- Names a specific external entity (DoD program, customer, partner, registry) the framework can independently look up
- Quantifies something verifiable (contract dollar amount, number of units delivered, patent count, headcount)
- Asserts a status that registries record (granted patent count, awarded contract count, NDAA/Blue UAS compliance, named-program participation)

LOW value (skip):
- Pure accounting (cash, share counts) unless a material vendor/equity event
- HQ address / incorporation alone
- Subjective characterizations ("we are a leader in X")
- Market-size or industry-trend claims with no company-specific assertion
- Pure forward projections with NO named counterparty AND NO quantified milestone

Each claim: {{claim_id, claim_text, subject, predicate, object_value, source_quote, category, queries[]}}.
Categories: customer_pipeline | physical_facility | technology | partnership | regulatory_milestone | production_volume | financial_distress | vendor_relationship | other.

== SCORE RUBRIC ==
Severity: PASS / MODERATE_UNDERDELIVERY / SEVERE_UNDERDELIVERY / RED_FLAG_NEGATIVE / UNVERIFIABLE.

== CALIBRATION HEURISTICS (apply BEFORE deciding severity) ==
1. EPA FRS scope — only EPA-regulated facilities. Light defense electronics / drone assembly often NOT in FRS. Do not red-flag absence in those cases.
2. Foreign-issuer caveat — N/A for this cohort (all US-listed); skip.
3. Planned vs operational — "planned" / "to be delivered" / "won an award contingent on options being exercised" — track separately from real obligated $.
4. Investment vs operating — strategic investor partnerships usually NOT material; operating partnerships and named-program participation ARE material.
5. Source-jurisdiction mismatches — USAspending covers all federal contracts. NHTSA does NOT cover drones / UAS / military vehicles (motor-vehicle-only). Don't query NHTSA for this cohort.
6. Name-variant fragility — try multiple variants (brand, legal entity, subsidiary names). E.g. "Red Cat" may also appear as "Teal Drones" (subsidiary).
7. Counterparty-disclosure threshold — 0 mentions of company in counterparty's 10-K is SEVERE only if the counterparty is large and the claim is material.
8. Patents — uspto_odp.query_assignee preferred. PASS if n_granted >= 5 with any claimed-category hit. SEVERE only on Nikola pattern (>= 20 granted, 0 in claimed areas).
9. **DoD-CONTRACT-SPECIFIC**: if the company claims a SPECIFIC DoD program ("Replicator", "Short Range Reconnaissance Tranche 2", "Long Range Precision Fires"), USAspending should show contract obligations on that program. ABSENCE of any DoD contracts at all for a company claiming a named program is HARD CONTRADICTION → RED_FLAG_NEGATIVE.
10. **Realistic DoD timing**: contract claims often reference IDIQ ceiling rather than obligated amount. Check both ceiling ($large) and actually-obligated ($smaller). Disclosure of ceiling-only without obligated context is MODERATE.

Each score entry: {{claim_id, claim_text, severity, supports, M_check, M_value, interpretation}}.

== OUTPUT FORMATS ==
input.json: {{"ticker": "{ticker}", "cutoff": "{cutoff}", "filing": "<filename>", "claims": [...]}}
scores.json: {{"ticker": "{ticker}", "scores": [...]}}

== START NOW ==
Be efficient. Independent bash queries can run in parallel. Final message must be exactly one line with the summary.
"""


def build_prompt(ticker: str) -> str:
    member = next(m for m in COHORT if m.ticker == ticker)
    counterparty_block = "\n".join(
        f"  - {label}: {cik}" for label, cik in COMMON_COUNTERPARTY_CIKS.items()
    )
    return PROMPT_TEMPLATE.format(
        ticker=ticker,
        ticker_lower=ticker.lower(),
        cik_padded=member.cik,
        company_name=member.name,
        notes=member.notes,
        cutoff=CUTOFF,
        cohort_context=COHORT_CONTEXT,
        counterparty_block=counterparty_block,
    )
