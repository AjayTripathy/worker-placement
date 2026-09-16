"""Build per-ticker subagent prompts for the AI-DC crypto-pivot cohort run."""
from __future__ import annotations

from .dcpivot_cohort import COHORT, COHORT_CONTEXT, COMMON_COUNTERPARTY_CIKS, CUTOFF


PROMPT_TEMPLATE = """You are a forensic-disclosure analyst running a BLINDED forward test of the Signal OS framework on a single AI / data-center company (often a former crypto miner pivoting to AI/HPC hosting). You will play the role the LLM plays in the framework's pipeline: extract claims from a filing, pick M-source queries, run them, and score severity.

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
1. Read the filings index. Pick the most substantive PRE-CUTOFF filing (10-K preferred; 20-F for foreign filers like BTDR/IREN if applicable; S-1 if recent IPO; 10-Q if newer interim disclosures materially change the picture).
2. Slice the filing to ~120K chars from key business sections + financial-statement notes:
     python3 -c "from verticals.public_co.filing_slice import slice_filing; t=open('FILING_PATH').read(); print(slice_filing(t, budget_chars=120000))" > /tmp/sliced_{ticker}.txt
   Then Read /tmp/sliced_{ticker}.txt.
3. Extract 5-8 testable factual claims per the EXTRACT RUBRIC below. Pick 1-3 M-source queries per claim from the catalog. Prefer:
     - edgar_fts.query_fulltext (cik=COUNTERPARTY) → for hyperscaler hosting / colocation contract corroboration. Try BOTH the AI-DC company's name AND the site name (e.g. "Ellendale", "Black Pearl", "Childress").
     - edgar_fts.query_fulltext (no cik) → asymmetric mention test: how often does anyone mention this company's MW-scale claims?
     - uspto_odp.query_assignee → for cooling / power-management patents (often light).
     - usaspending.query_recipient_contracts → rarely applicable (most DC pivots are private commercial — federal contracts uncommon).
4. **CHECKPOINT 1 — immediately write input.json BEFORE running any queries.** Preserves extraction work if the watchdog kills you mid-query. Structure: {{"ticker": "{ticker}", "cutoff": "{cutoff}", "filing": "<filename>", "claims": [...]}}
5. Iterate claim-by-claim:
     a. Run that claim's queries (be polite, sleep 1-2s between queries).
     b. Score severity per the SCORE RUBRIC + CALIBRATION HEURISTICS below.
     c. **CHECKPOINT 2 — immediately re-write the ENTIRE scores.json with all claims scored so far.** Do NOT batch and save at the end; after each claim, rewrite the file so a stall preserves the last-completed checkpoint. Structure (rewritten each iteration): {{"ticker": "{ticker}", "scores": [...]}}
6. After the last claim is scored, report a one-line summary: "{ticker}: N claims, K queries, severity counts: PASS=x MODE=y SEVE=z RED=w UNVE=v"

== EXTRACT RUBRIC ==
HIGH discriminative claims:
- Names a specific external entity (hyperscaler customer, neocloud customer like CoreWeave / Lambda, named site or substation) the framework can independently look up
- Quantifies something verifiable (MW interconnect approved / operating, contract dollar amount, lease TCV, GPU count / vendor)
- Asserts a status with a registry analog (interconnect approval, named-customer lease, grid-utility filing)
- AI-DC-specific high-value:
    * "X MW operating vs X MW under construction vs X MW announced" — break out clearly
    * "$X multi-year hyperscaler hosting deal" — verifiable via hyperscaler 10-K
    * "MOU with hyperscaler" vs "definitive lease" vs "energized + revenue-generating" — three different stages

LOW value (skip):
- Pure accounting unless material vendor / equity event (stock-for-services, reverse split, going-concern, large convertible-debt raise — distress signaling)
- Subjective characterizations ("we are the leader in sustainable AI infrastructure")
- Pure marketing TAM / market-size claims with no company-specific assertion
- Pure forward projections with NO named counterparty AND NO quantified milestone

Each claim: {{claim_id, claim_text, subject, predicate, object_value, source_quote, category, queries[]}}.
Categories: customer_pipeline | partnership | regulatory_milestone | production_volume | technology | physical_facility | financial_distress | vendor_relationship | other.

== SCORE RUBRIC ==
Severity: PASS / MODERATE_UNDERDELIVERY / SEVERE_UNDERDELIVERY / RED_FLAG_NEGATIVE / UNVERIFIABLE.

== CALIBRATION HEURISTICS (apply BEFORE deciding severity) ==
1. EPA FRS scope — data centers themselves are generally NOT EPA-regulated (no air-permit). Absence in FRS is NOT a red flag.
2. Foreign-issuer caveat — BTDR is Singapore-based (20-F); IREN is Australia-based (20-F). 20-F sections of interest: Item 4 (Information on Company), Item 5 (Operating and Financial Review), Item 10 (Additional Information).
3. Planned vs operational — STAGE LADDER discipline is decisive. Hosting contracts move term-sheet -> lease -> shell built -> commissioned -> energized -> generating revenue. Headline contract TCV (e.g. $1.5B over 12 years) is NOT current-period revenue; current-period MW operating + per-MW pricing is. If marketing tier conflates them while financial-statement notes disclose only a fraction operating, score MODERATE-to-SEVERE.
4. Investment vs operating — strategic investments (Nvidia-led financings, hyperscaler equity stakes) are NOT customer revenue.
5. Source-jurisdiction mismatches — Most AI-DC counterparty deals are commercial (no USAspending coverage). EDGAR is the primary M-source for hyperscaler counterparty disclosure. NHTSA, NRC, EPA FRS, USPTO ODP have limited applicability.
6. Name-variant fragility — try company name + site name + product name (Cipher / Cipher Mining / Black Pearl / Odessa; Applied Digital / APLD / Ellendale; Core Scientific / CORZ / Marble; Iris Energy / IREN / Childress / Sweetwater; Bitdeer / BTDR / Jigmeling).
7. Counterparty-disclosure threshold — for any claim naming a hyperscaler or hyperscaler-class counterparty (Microsoft, Amazon, Meta, Google, Oracle) as a customer at $100M+ multi-year TCV scale, run edgar_fts.query_fulltext with both the company name AND the site name, restricted to the counterparty's CIK. AI-hosting deals at hyperscaler scale ARE material to the hyperscaler's data-center capex commentary and SHOULD appear in their 10-K. ABSENCE while AI-DC claims headline customer revenue = HARD CONTRADICTION → RED_FLAG_NEGATIVE. EXCEPTION: CoreWeave is private and won't appear in EDGAR; CoreWeave-named deals are UNVERIFIABLE on counterparty axis.
8. Patents — uspto_odp.query_assignee. AI-DC pure-plays typically have light patent estates (real estate / infrastructure, not IP-heavy). Absence here is NOT a red flag.
9. **AI-DC-SPECIFIC: TCV vs current-period revenue conflation.** If the company headlines a multi-billion-dollar contract value but the financial-statement notes show only a small fraction recognized as current-period revenue, score MODERATE (disclosure-quality issue). If the company actively obscures the recognition timing in MD&A (e.g. uses TCV in headline language without breaking out recognized-vs-deferred), score SEVERE.
10. **DELISTING / GOING-CONCERN FINGERPRINTS**: many of these names came through reverse mergers / SPACs with thin balance sheets. Form 15-12G, 25-NSE, repeated reverse splits, going-concern qualifier, large dilutive issuance are distress markers. CORZ specifically emerged from Chapter 11 in 2024 — its post-emergence claims should be cross-checked against its plan of reorganization disclosures.
11. **REVENUE-RECOGNITION PATTERN (AI-DC-specific)**: legacy BTC mining revenue is volatile and not equivalent to AI-hosting revenue; if the company markets a pivot but most recognized revenue is still BTC, score MODERATE. Also check for related-party transactions between the AI-DC company and the customer (some neocloud deals are structurally circular).

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
