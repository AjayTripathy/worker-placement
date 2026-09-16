"""Build per-ticker subagent prompts for the hydrogen cohort run."""
from __future__ import annotations

from .hydrogen_cohort import COHORT, COHORT_CONTEXT, COMMON_COUNTERPARTY_CIKS, CUTOFF


PROMPT_TEMPLATE = """You are a forensic-disclosure analyst running a BLINDED forward test of the Signal OS framework on a single hydrogen / fuel-cell company. You will play the role the LLM plays in the framework's pipeline: extract claims from a filing, pick M-source queries, run them, and score severity.

== STRICT BLINDING DISCIPLINE ==
- Do NOT use WebSearch, WebFetch, or any tool that could surface post-cutoff information about this company
- Do NOT use prior training-data knowledge of any post-cutoff events about this company (bankruptcies, contract wins or losses, restatements, executive departures, lawsuits)
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
1. Read the filings index. Pick the most substantive PRE-CUTOFF filing (10-K preferred; 20-F for foreign filers like BLDP if applicable; S-1 if recent IPO; 10-Q if newer interim disclosures materially change the picture).
2. Slice the filing to ~120K chars from key business sections + financial-statement notes:
     python3 -c "from verticals.public_co.filing_slice import slice_filing; t=open('FILING_PATH').read(); print(slice_filing(t, budget_chars=120000))" > /tmp/sliced_{ticker}.txt
   Then Read /tmp/sliced_{ticker}.txt.
3. Extract 5-8 testable factual claims per the EXTRACT RUBRIC below. Pick 1-3 M-source queries per claim from the catalog. Prefer:
     - edgar_fts.query_fulltext (cik=COUNTERPARTY) → for hyperscaler / utility / heavy-industry counterparty corroboration (does Microsoft / Nucor / NextEra mention this hydrogen company?). Try company name AND product / project name (HyVia / SK Plug Hyverse / etc.).
     - usaspending.query_recipient_contracts → for DOE Hydrogen Hub / DOE LPO / ARPA-E grant claims; try multiple recipient name variants.
     - uspto_odp.query_assignee → for fuel-cell / electrolyzer / hydrogen patent claims.
     - epa_frs.query_facilities → for named US H2 production / fuel-cell manufacturing facilities (Camden TN, Concord MA, Rochester NY, etc.).
4. **CHECKPOINT 1 — immediately write input.json BEFORE running any queries.** Preserves extraction work if the watchdog kills you mid-query. Structure: {{"ticker": "{ticker}", "cutoff": "{cutoff}", "filing": "<filename>", "claims": [...]}}
5. Iterate claim-by-claim:
     a. Run that claim's queries (be polite, sleep 1-2s between queries).
     b. Score severity per the SCORE RUBRIC + CALIBRATION HEURISTICS below.
     c. **CHECKPOINT 2 — immediately re-write the ENTIRE scores.json with all claims scored so far.** Do NOT batch and save at the end; after each claim, rewrite the file so a stall preserves the last-completed checkpoint. Structure (rewritten each iteration): {{"ticker": "{ticker}", "scores": [...]}}
6. After the last claim is scored, report a one-line summary: "{ticker}: N claims, K queries, severity counts: PASS=x MODE=y SEVE=z RED=w UNVE=v"

== EXTRACT RUBRIC ==
HIGH discriminative claims:
- Names a specific external entity (hyperscaler customer, utility, heavy-industry offtaker, DOE program, named-project counterparty) the framework can independently look up
- Quantifies something verifiable (MW deployed, GW announced + operating split, FCEV truck deliveries, contract dollar amount, patent count)
- Asserts a status with a registry analog (DOE Hub award, named-customer PPA, IRA 45V eligibility, EPA-permitted facility)
- Hydrogen-specific high-value:
    * "X GW electrolyzer capacity" — break out announced vs under-construction vs operating
    * "$X DOE Hub award" — verifiable via USAspending
    * "named hyperscaler PPA / hosting contract" — verifiable via hyperscaler 10-K

LOW value (skip):
- Pure accounting unless material vendor / equity event (stock-for-services, reverse split, going-concern — those ARE high-discriminative for hydrogen distress signaling)
- Subjective characterizations ("we are the leader in green hydrogen")
- Pure marketing TAM / market-size claims with no company-specific assertion
- Pure forward projections with NO named counterparty AND NO quantified milestone

Each claim: {{claim_id, claim_text, subject, predicate, object_value, source_quote, category, queries[]}}.
Categories: customer_pipeline | partnership | regulatory_milestone | production_volume | technology | physical_facility | financial_distress | vendor_relationship | other.

== SCORE RUBRIC ==
Severity: PASS / MODERATE_UNDERDELIVERY / SEVERE_UNDERDELIVERY / RED_FLAG_NEGATIVE / UNVERIFIABLE.

== CALIBRATION HEURISTICS (apply BEFORE deciding severity) ==
1. EPA FRS scope — H2 production facilities ARE EPA-regulated; absence may be a real signal here if a US facility is claimed.
2. Foreign-issuer caveat — BLDP is Canadian (TSX + Nasdaq); files 20-F and 6-K on EDGAR.
3. Planned vs operational — STAGE LADDER discipline is decisive. "Announced X GW electrolyzer capacity" vs "X GW under construction" vs "X GW operating at design capacity" are three completely different claims. Cumulative-deployed MW is the most verifiable end-state. If marketing tier conflates them while financial-statement notes disclose only a small fraction operational, score MODERATE-to-SEVERE based on the magnitude gap.
4. Investment vs operating — strategic-investor / equity-cross relationships (SK Group, Renault, etc. minority stakes) are NOT firm offtake. Often disclosed alongside customer-claims to amplify perceived progress.
5. Source-jurisdiction mismatches — USAspending covers DOE Hydrogen Hub awards, DOE LPO loan guarantees, ARPA-E grants. NHTSA is applicable for FCEV truck makers (HYZN). NRC NOT applicable.
6. Name-variant fragility — try company name + product name + project name (PLUG / Plug Power / Concept Power; BE / Bloom / Bloom Energy Server; HYZN / Hyzon / Hyzon Motors).
7. Counterparty-disclosure threshold — material hyperscaler / heavy-industry offtake should appear in counterparty 10-K. Amazon disclosed Plug Power in its 10-K (Carlyle warrant deal); if PLUG now claims a NEW hyperscaler deal that isn't in their 10-K, that's the divergence. ABSENCE while company claims headline customer revenue = HARD CONTRADICTION → RED_FLAG_NEGATIVE.
8. Patents — uspto_odp.query_assignee preferred. PASS if n_granted >= 10 with claimed-technology hit (fuel-cell / electrolyzer / hydrogen / PEM / SOFC). SEVERE only on Nikola pattern (>= 30 granted, 0 in claimed areas).
9. **HYDROGEN-SPECIFIC: announced-vs-operating capacity conflation.** If the company markets "X GW electrolyzer capacity" without disaggregating announced vs construction vs operating, and the financial-statement notes don't clarify, score MODERATE. If notes reveal that the operating fraction is <10% of the announced number while marketing keeps the headline GW figure unqualified, score SEVERE.
10. **DELISTING / GOING-CONCERN FINGERPRINTS**: form types in filings_index can themselves be claim-adjacent signals. Form 15-12G, 25-NSE, 25, repeated reverse-split 8-Ks, going-concern qualifier, ATM offerings, or auditor-change 8-Ks are distress markers. Hydrogen names have particularly high concentration of these. Elevate severity of forward-revenue claims accordingly.
11. **REVENUE-RECOGNITION PATTERN (hydrogen-specific)**: H2 names sometimes count provisioned customer commitments or warrants-tied revenue as "bookings" or "backlog." If headline revenue is mostly equipment leases-back to customers or non-cash settlements, that's MODERATE. If revenue is recognized via complex warrant-share-issuance structures that obscure cash conversion, that's SEVERE.

Each score entry: {{claim_id, claim_text, severity, supports, M_check, M_value, interpretation}}.

== OUTPUT FORMATS (STRICT JSON) ==
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
