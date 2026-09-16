"""Build per-ticker subagent prompts for the solid-state battery cohort run."""
from __future__ import annotations

from .ssbattery_cohort import COHORT, COHORT_CONTEXT, COMMON_COUNTERPARTY_CIKS, CUTOFF


PROMPT_TEMPLATE = """You are a forensic-disclosure analyst running a BLINDED forward test of the Signal OS framework on a single solid-state / next-gen battery company (or upstream lithium-supply control). You will play the role the LLM plays in the framework's pipeline: extract claims from a filing, pick M-source queries, run them, and score severity.

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
1. Read the filings index. Pick the most substantive PRE-CUTOFF filing (10-K preferred; S-1 if recent IPO; 10-Q if newer interim disclosures materially change the picture).
2. Slice the filing to ~120K chars from key business sections + financial-statement notes:
     python3 -c "from verticals.public_co.filing_slice import slice_filing; t=open('FILING_PATH').read(); print(slice_filing(t, budget_chars=120000))" > /tmp/sliced_{ticker}.txt
   Then Read /tmp/sliced_{ticker}.txt.
3. Extract 5-8 testable factual claims per the EXTRACT RUBRIC below. Pick 1-3 M-source queries per claim from the catalog. Prefer:
     - edgar_fts.query_fulltext (cik=COUNTERPARTY) → for auto-OEM customer corroboration (Ford / GM / Stellantis / Honda / Toyota; note that VW / BMW / Mercedes / Hyundai are foreign filers with partial EDGAR coverage).
     - uspto_odp.query_assignee → for lithium-metal / sulfide / silicon-anode / electrolyte / cathode patent claims.
     - usaspending.query_recipient_contracts → for DOE LPO / ARPA-E grant claims.
     - epa_frs.query_facilities → for claimed US production / pilot facilities.
4. **CHECKPOINT 1 — immediately write input.json BEFORE running any queries.** Preserves extraction work if the watchdog kills you mid-query. Structure: {{"ticker": "{ticker}", "cutoff": "{cutoff}", "filing": "<filename>", "claims": [...]}}
5. Iterate claim-by-claim:
     a. Run that claim's queries (be polite, sleep 1-2s between queries).
     b. Score severity per the SCORE RUBRIC + CALIBRATION HEURISTICS below.
     c. **CHECKPOINT 2 — immediately re-write the ENTIRE scores.json with all claims scored so far.** Do NOT batch and save at the end; after each claim, rewrite the file so a stall preserves the last-completed checkpoint. Structure (rewritten each iteration): {{"ticker": "{ticker}", "scores": [...]}}
6. After the last claim is scored, report a one-line summary: "{ticker}: N claims, K queries, severity counts: PASS=x MODE=y SEVE=z RED=w UNVE=v"

== EXTRACT RUBRIC ==
HIGH discriminative claims:
- Names a specific external entity (auto OEM JDA partner, DOE program, named pilot facility, consumer-electronics customer) the framework can independently look up
- Quantifies something verifiable (energy density Wh/kg/L, cycle life, GWh capacity, JDA stage A-B-C-sample, SOP year, contract dollar amount, patent count)
- Asserts a status with a registry analog (DOE LPO loan/award, named-OEM JDA, EPA-permitted facility)
- Battery-specific high-value:
    * Energy-density claim **with test conditions** (rate, T, DoD) vs unconditional claim — distinct stages
    * Cycle-life claim **at automotive rate / DoD** vs lab-scale — distinct stages
    * "Planned X GWh by 20YY" vs "X GWh installed today" — distinct stages

LOW value (skip):
- Pure accounting unless material vendor / equity event (stock-for-services, reverse split, going-concern — distress signaling)
- Subjective characterizations ("we are the leader in solid-state batteries")
- Pure marketing TAM / market-size claims with no company-specific assertion
- Pure forward projections with NO named counterparty AND NO quantified milestone

Each claim: {{claim_id, claim_text, subject, predicate, object_value, source_quote, category, queries[]}}.
Categories: customer_pipeline | design_win | regulatory_milestone | production_volume | technology | physical_facility | financial_distress | vendor_relationship | other.

== SCORE RUBRIC ==
Severity: PASS / MODERATE_UNDERDELIVERY / SEVERE_UNDERDELIVERY / RED_FLAG_NEGATIVE / UNVERIFIABLE.

== CALIBRATION HEURISTICS (apply BEFORE deciding severity) ==
1. EPA FRS scope — battery pilot / production facilities ARE EPA-regulated (hazmat handling, air permits). Absence in FRS for a claimed US production facility IS a real signal.
2. Foreign-issuer caveat — most major OEM customers (VW, BMW, Mercedes, Hyundai, Toyota) file foreign annual reports (20-F or none); US 10-K coverage is partial. UNVERIFIABLE rather than false-clean.
3. Planned vs operational — STAGE LADDER discipline is decisive. Battery design-wins move JDA -> A-sample -> B-sample -> C-sample -> validation -> SOP -> series production. Each stage is a different claim. Conflating JDA with SOP is the central evasion pattern. Energy-density claims without test conditions (rate, temperature, depth-of-discharge) are aspirational, not commercial.
4. Investment vs operating — OEM equity stakes (VW in QS, Hyundai in SES, etc.) are NOT design-wins. Often disclosed alongside JDA-claims to amplify perceived progress.
5. Source-jurisdiction mismatches — USAspending covers DOE LPO loan guarantees (LAC's Thacker Pass loan, ENVX's Malaysia loan-equivalent). NHTSA registers complete vehicles, not battery suppliers; do not query for the battery company name.
6. Name-variant fragility — try company name + product name (QS / QuantumScape / QSE-5; SES / SES AI / Apollo / Hermes; SLDP / Solid Power / SP2 / FY27 prototype; MVST / Microvast; ENVX / Enovix / Fab-2).
7. Counterparty-disclosure threshold — material OEM JDA (especially for SOP-claimed periods) should appear in the OEM's 10-K / 20-F. If VW's annual report doesn't mention QS series production by the claimed SOP year, that's the divergence. ABSENCE while battery company claims series-production OEM revenue = HARD CONTRADICTION → RED_FLAG_NEGATIVE. ABSENCE for a pre-SOP JDA = MODERATE_UNDERDELIVERY (the OEM has no recognition obligation yet).
8. Patents — uspto_odp.query_assignee preferred. PASS if n_granted >= 10 with claimed-technology hit (lithium / battery / electrolyte / cathode / anode / sulfide / solid-state). SEVERE only on Nikola pattern (>= 30 granted, 0 in claimed areas).
9. **BATTERY-SPECIFIC: energy-density without test conditions.** If the company claims "X Wh/kg" without specifying rate, T, and DoD, AND the financial-statement notes don't clarify, score MODERATE (disclosure-quality issue). If the conditions disclosed elsewhere imply the reported number is lab-scale or low-rate, while marketing uses it as a series-production target, score SEVERE.
10. **DELISTING / GOING-CONCERN FINGERPRINTS**: many SPAC-era battery names are now low-priced. Form 15-12G, 25-NSE, repeated reverse splits, going-concern qualifier, ATM offerings are distress markers. Elevate severity of forward-revenue / SOP claims accordingly.
11. **REVENUE-RECOGNITION PATTERN (battery-specific)**: pre-revenue battery names often recognize "sample revenue" or "validation revenue" from OEM JDA partners. If material revenue is sample-shipments rather than series-production commercial revenue, this is MODERATE. Also check for related-party / strategic-investor revenue (OEM partner pays the battery company for development services as part of a JDA).

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
