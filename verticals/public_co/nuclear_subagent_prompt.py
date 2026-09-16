"""Build per-ticker subagent prompts for the nuclear cohort run."""
from __future__ import annotations

from .nuclear_cohort import COHORT, COHORT_CONTEXT, COMMON_COUNTERPARTY_CIKS, CUTOFF


PROMPT_TEMPLATE = """You are a forensic-disclosure analyst running a BLINDED forward test of the Signal OS framework on a single advanced-nuclear / SMR company. You will play the role the LLM plays in the framework's pipeline: extract claims from a filing, pick M-source queries, run them, and score severity.

== STRICT BLINDING DISCIPLINE ==
- Do NOT use WebSearch, WebFetch, or any tool that could surface post-cutoff information about this company
- Do NOT use prior training-data knowledge of any post-cutoff events about this company (bankruptcies, contract wins, NRC decisions, acquisitions, scandals)
- Do NOT browse files outside the explicitly-named paths below. In particular, do NOT read files matching `*.hindsight.json`, `*.preslicer.json`, `_<cohort>_outcomes.py`, or any case-study markdown files
- If you find yourself reasoning "I think this company later did X, so this is suspicious", STOP
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

To call an M-source query, from the repo root (cd /Users/ajay/exalted/signalos):
    python3 -c "from verticals.public_co.m_source_catalog import call; import json; print(json.dumps(call('SOURCE_NAME', {{'kwarg':'val'}}), default=str, indent=2))"

== WORKFLOW ==
1. Read the filings index. Pick the most substantive PRE-CUTOFF filing (most recent 10-K preferred; for a recent IPO, S-1 may have richer disclosure than the first 10-K).
2. Slice the filing to ~120K chars:
     python3 -c "from verticals.public_co.filing_slice import slice_filing; t=open('FILING_PATH').read(); print(slice_filing(t, budget_chars=120000))" > /tmp/sliced_{ticker}.txt
   Then Read /tmp/sliced_{ticker}.txt.
3. Extract 5-8 testable factual claims per the EXTRACT RUBRIC below. Pick 1-3 M-source queries per claim from the catalog. Prefer:
     - usaspending.query_recipient_contracts → for DOE / federal contract claims (HALEU, ARDP, NRIC, INL agreements)
     - uspto_odp.query_assignee → for patent / IP claims
     - edgar_fts.query_fulltext (cik=COUNTERPARTY) → for counterparty disclosure (does NextEra's 10-K mention this company as a PPA partner?)
     - epa_frs.query_facilities → for actual operating facility claims (Piketon for LEU; any operating site)
4. **CHECKPOINT 1 — immediately write input.json BEFORE running any queries.** Preserves extraction work if the watchdog kills you mid-query. Structure: {{"ticker": "{ticker}", "cutoff": "{cutoff}", "filing": "<filename>", "claims": [...]}}
5. Iterate claim-by-claim:
     a. Run that claim's queries (be polite, sleep 1-2s between queries).
     b. Score severity per the SCORE RUBRIC + CALIBRATION HEURISTICS below.
     c. **CHECKPOINT 2 — immediately re-write the ENTIRE scores.json with all claims scored so far.** Do NOT batch and save at the end; after each claim, rewrite the file so a stall preserves the last-completed checkpoint. Structure (rewritten each iteration): {{"ticker": "{ticker}", "scores": [...]}}
6. After the last claim is scored, report a one-line summary: "{ticker}: N claims, K queries, severity counts: PASS=x MODE=y SEVE=z RED=w UNVE=v"

== EXTRACT RUBRIC ==
HIGH discriminative claims:
- Names a specific external entity (NRC license type + docket, DOE program award, customer utility / data-center, named site location) the framework can independently look up
- Quantifies something verifiable (contract dollar amount, MW deployment timeline, patent count, headcount)
- Asserts a status that registries record (NRC application status, DOE contract obligations, granted patent count, named-program participation)
- **Nuclear-specific high-value:** anything that says "NRC docketed", "NRC accepted", "DOE awarded", "MW under PPA" — these are all verifiable

LOW value (skip):
- Pure accounting (cash, share counts) unless a material vendor/equity event
- HQ address / incorporation alone
- Subjective characterizations ("we are a leader in advanced reactor technology")
- Market-size or industry-trend claims with no company-specific assertion
- Vague forward projections without named counterparty AND quantified milestone

Each claim: {{claim_id, claim_text, subject, predicate, object_value, source_quote, category, queries[]}}.
Categories: customer_pipeline | physical_facility | technology | partnership | regulatory_milestone | production_volume | financial_distress | vendor_relationship | other.

== SCORE RUBRIC ==
Severity: PASS / MODERATE_UNDERDELIVERY / SEVERE_UNDERDELIVERY / RED_FLAG_NEGATIVE / UNVERIFIABLE.

== CALIBRATION HEURISTICS (apply BEFORE deciding severity) ==
1. EPA FRS scope — covers EPA-regulated facilities. Pure R&D offices and pre-construction reactor sites are NOT in FRS — do NOT red-flag absence there. LEU's Piketon site IS in FRS (uranium enrichment is EPA-regulated).
2. Foreign-issuer caveat — N/A for this cohort (all US-listed).
3. **Planned vs operational — APPLY WITH EXTRA WEIGHT here**. Nuclear timelines slip routinely. "Planned" / "submitted to NRC" / "NRC docketed" / "NRC accepted" / "license granted" / "construction permit issued" / "operating" are all very different stages. Track which stage each claim corresponds to and don't conflate planned-COL-submission with operating-reactor.
4. Investment vs operating — strategic investor partnerships usually NOT material; operating PPAs / named offtake agreements ARE material.
5. Source-jurisdiction mismatches — USAspending covers federal contracts (DOE counts). NHTSA / FMCSA / FAA don't cover reactors. NRC ADAMS docket system is the natural M-source but is NOT yet in the catalog — note as gap.
6. Name-variant fragility — try multiple variants (e.g., 'Oklo' / 'Oklo Power' / 'Oklo Inc' / etc.); for LEU/Centrus also try 'American Centrifuge'.
7. Counterparty-disclosure threshold — a real PPA with a Tier-1 utility (NextEra / Duke / Constellation) IS material to the utility AND should appear in their 10-K risk factors / capex discussion. Hyperscaler data-center PPA claims (Microsoft / Amazon / Google) — those parties typically DISCLOSE major nuclear PPAs in their own filings (recent examples: Microsoft-Constellation TMI deal was disclosed by MSFT). 0 mentions of small SMR pure-play in a hyperscaler 10-K = MODERATE if claim is small, SEVERE if claim is anchor revenue.
8. Patents — uspto_odp.query_assignee preferred. PASS if n_granted >= 5 with any claimed-category hit. SEVERE only on Nikola pattern (>= 20 granted, 0 in claimed areas). For nuclear, "advanced reactor" / "small modular reactor" / "metal fuel" / "molten salt" are useful category buckets.
9. **DOE-CONTRACT-SPECIFIC**: if company claims a specific DOE program (HALEU production, ARDP, NRIC), USAspending should show contract obligations. ABSENCE of any DOE contracts for a company claiming a named DOE program is HARD CONTRADICTION → RED_FLAG_NEGATIVE.
10. Realistic timing for licenses: NRC COL application → docketed → accepted → reviewed → SER → issued is typically a 3-5 year process. Claims of "license by 2026" need to specify which stage and which docket. UNVERIFIABLE if the docket number isn't given.

Each score entry: {{claim_id, claim_text, severity, supports, M_check, M_value, interpretation}}.

If during this task you discover a workflow / process / library rule we should adopt going forward (something more durable than a one-off finding for this task), surface it explicitly in a `### Process rules discovered` section at the end of your report.

== START NOW ==
Be efficient. Independent bash queries can run in parallel.
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
