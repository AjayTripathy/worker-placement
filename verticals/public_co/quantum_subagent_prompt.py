"""Build per-ticker subagent prompts for the quantum cohort run.

HELD-OUT cohort: the calibration heuristics in this prompt were authored
from the eVTOL/defense/lidar/nuclear runs, NOT from any quantum-cohort
outcomes. This is the validation that the heuristics generalize.
"""
from __future__ import annotations

from .quantum_cohort import COHORT, COHORT_CONTEXT, COMMON_COUNTERPARTY_CIKS, CUTOFF


PROMPT_TEMPLATE = """You are a forensic-disclosure analyst running a BLINDED forward test of the Signal OS framework on a single quantum-computing or QKD company. You will play the role the LLM plays in the framework's pipeline: extract claims from a filing, pick M-source queries, run them, and score severity.

== STRICT BLINDING DISCIPLINE ==
- Do NOT use WebSearch, WebFetch, or any tool that could surface post-cutoff information about this company
- Do NOT use prior training-data knowledge of any post-cutoff events about this company (bankruptcies, contract wins, restatements, executive departures, lawsuits)
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
1. Read the filings index. Pick the most substantive PRE-CUTOFF filing (10-K preferred for US filers; 20-F for foreign private issuers like ARQQ; S-1 / S-1/A if recent IPO and no 10-K yet; 10-Q if newer interim disclosures materially change the picture).
2. Slice the filing to ~120K chars from key business sections + financial-statement notes:
     python3 -c "from verticals.public_co.filing_slice import slice_filing; t=open('FILING_PATH').read(); print(slice_filing(t, budget_chars=120000))" > /tmp/sliced_{ticker}.txt
   Then Read /tmp/sliced_{ticker}.txt.
3. Extract 5-8 testable factual claims per the EXTRACT RUBRIC below. Pick 1-3 M-source queries per claim from the catalog. Prefer:
     - edgar_fts.query_fulltext (cik=COUNTERPARTY) → for hyperscaler / Tier-1 financial / defense-prime counterparty corroboration (does AWS / Microsoft / JPM / Lockheed mention this quantum company?). Try both company name AND product name (Forte / Tempo / Advantage2 / Ankaa / Lyra / Dirac-3 / SKA, etc.).
     - usaspending.query_recipient_contracts → for AFRL / ARL / DARPA / IARPA / national-lab contract claims. Try multiple recipient-name variants.
     - uspto_odp.query_assignee → for quantum / qubit / photonic / superconducting / trapped-ion / annealing patent claims.
     - edgar_fts.query_fulltext (no cik) → for general counterparty corroboration across all filers — how often does anyone mention this company's headline product?
4. **CHECKPOINT 1 — immediately write input.json BEFORE running any queries.** Preserves extraction work if the watchdog kills you mid-query. Structure: {{"ticker": "{ticker}", "cutoff": "{cutoff}", "filing": "<filename>", "claims": [...]}}
5. Iterate claim-by-claim:
     a. Run that claim's queries (be polite, sleep 1-2s between queries).
     b. Score severity per the SCORE RUBRIC + CALIBRATION HEURISTICS below.
     c. **CHECKPOINT 2 — immediately re-write the ENTIRE scores.json with all claims scored so far.** Do NOT batch and save at the end; after each claim, rewrite the file so a stall preserves the last-completed checkpoint. Structure (rewritten each iteration): {{"ticker": "{ticker}", "scores": [...]}}
6. After the last claim is scored, report a one-line summary: "{ticker}: N claims, K queries, severity counts: PASS=x MODE=y SEVE=z RED=w UNVE=v"

== EXTRACT RUBRIC ==
HIGH discriminative claims:
- Names a specific external entity (hyperscaler, defense prime, national lab, named commercial customer, named DoD contract / program) the framework can independently look up
- Quantifies something verifiable (qubit count + benchmark conditions, contract dollar amount, patent count, revenue from a named customer)
- Asserts a status with a registry analog (granted patent count, named-program contract, cloud-platform availability, NIST standards-track participation)
- Quantum-specific high-value:
    * "X qubits available on AWS Braket / Azure / GCP" — verifiable via the hyperscaler's 10-K / partner-list
    * "$X DoD contract with AFRL/ARL/DARPA" — verifiable via USAspending
    * "logical qubit demonstration" vs "physical qubit count" — stage-ladder distinction
    * "commercial revenue from quantum services" vs "research grants from federal agencies"

LOW value (skip):
- Pure accounting (cash, share counts) unless a material vendor / equity event (stock-for-services, reverse split, going-concern — those ARE high-discriminative)
- Subjective characterizations ("we are the leader in quantum computing")
- Pure marketing TAM / market-size claims with no company-specific assertion
- Pure forward projections with NO named counterparty AND NO quantified milestone

Each claim: {{claim_id, claim_text, subject, predicate, object_value, source_quote, category, queries[]}}.
Categories: customer_pipeline | partnership | regulatory_milestone | technology_milestone | production_volume | financial_distress | vendor_relationship | other.

== SCORE RUBRIC ==
Severity: PASS / MODERATE_UNDERDELIVERY / SEVERE_UNDERDELIVERY / RED_FLAG_NEGATIVE / UNVERIFIABLE.

== CALIBRATION HEURISTICS (apply BEFORE deciding severity) ==
1. EPA FRS scope — quantum companies typically have light fab footprint (often outsourced to foundries). Absence in FRS is NOT a red flag. Do not red-flag absence.
2. Foreign-issuer caveat — ARQQ is a UK foreign private issuer filing 20-F. 20-F sections of interest: Item 4 (Information on Company), Item 5 (Operating and Financial Review), Item 10 (Additional Information). DO NOT score ARQQ's lack of 10-K filings as a signal.
3. Planned vs operational — STAGE LADDER discipline is decisive. "Targeting X qubits by 2026" vs "demonstrated X qubits in benchmark X" vs "X qubits available to paying customers on AWS Braket" are three completely different claims. Cloud-platform availability is the most verifiable end-state — if a company claims "available on AWS Braket" but Amazon's 10-K and Braket partner page (visible via edgar_fts on AMZN) don't mention them, that's a strong signal. Logical-qubit vs physical-qubit distinction matters: error-corrected (logical) qubit counts are 1-2 orders of magnitude smaller than headline physical-qubit numbers.
4. Investment vs operating — strategic-investor / equity-cross relationships (e.g. an OEM took a minority stake) are NOT design-wins or commercial deployments. Often disclosed alongside customer-claims to amplify perceived progress.
5. Source-jurisdiction mismatches — USAspending covers all federal contracts including AFRL / ARL / DARPA awards. EDGAR full-text search covers hyperscaler 10-Ks. NHTSA is NOT applicable to quantum (do not query). NRC is NOT applicable.
6. Name-variant fragility — try multiple variants: brand name (Rigetti / IonQ / D-Wave / Arqit / Quantum Computing Inc), legal entity (e.g. Rigetti Computing, Inc.), product name (Forte / Tempo / Advantage / Ankaa / Lyra / Dirac-3 / SKA / Ouroboros / Quantum Bridge), subsidiary names.
7. Counterparty-disclosure threshold — for any claim naming a hyperscaler / defense prime / national lab / Tier-1 financial as a customer, run edgar_fts.query_fulltext with both the company name AND the product name, restricted to the counterparty's CIK. A material commercial-deployment relationship with a $1T-market-cap hyperscaler is material to the counterparty (especially in the AI / cloud roadmap section of their 10-K) and should appear. ABSENCE while the quantum player claims headline customer revenue is a HARD CONTRADICTION → RED_FLAG_NEGATIVE. ABSENCE while the quantum player only claims "available via" / "partner ecosystem" pre-deployment is MODERATE_UNDERDELIVERY (the hyperscaler distribution is real but the revenue scale is small).
8. Patents — uspto_odp.query_assignee preferred. PASS if n_granted >= 10 with claimed-technology-area hit (quantum / qubit / photonic / superconducting / ion / annealing / cryostat / dilution-refrigerator). SEVERE only on Nikola pattern (>= 30 granted, 0 in claimed areas).
9. **QUANTUM-SPECIFIC: physical vs logical qubit conflation.** If the company claims "X qubits" without specifying physical vs logical, and the financial-statement notes don't clarify, score MODERATE. If they explicitly conflate (e.g. claim error-correction-capability of X logical qubits when the underlying physical count couldn't support that ratio), score SEVERE.
10. **DELISTING / GOING-CONCERN FINGERPRINTS**: form types in the filings_index can themselves be claim-adjacent signals. Form 15-12G (registration termination), Form 25-NSE (notification of removal from listing), Form 25 (delisting), repeated reverse-split 8-Ks, large balance-sheet-pivot acquisitions are distress markers. If the latest pre-cutoff filing list contains any of these, flag the relevant filing's claims (e.g. "we expect commercial revenue by 20XX") with elevated severity.
11. **REVENUE-RECOGNITION PATTERN (quantum-specific)**: many quantum names have "bookings" or "cumulative bookings" headlines that diverge from GAAP revenue. If the company emphasizes "$X bookings" but recognized GAAP revenue is small or non-existent, score MODERATE.

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
