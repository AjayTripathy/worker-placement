"""Build per-ticker subagent prompts for the lidar / ADAS cohort run."""
from __future__ import annotations

from .lidar_cohort import COHORT, COHORT_CONTEXT, COMMON_COUNTERPARTY_CIKS, CUTOFF


PROMPT_TEMPLATE = """You are a forensic-disclosure analyst running a BLINDED forward test of the Signal OS framework on a single automotive-lidar / ADAS sensor company. You will play the role the LLM plays in the framework's pipeline: extract claims from a filing, pick M-source queries, run them, and score severity.

== STRICT BLINDING DISCIPLINE ==
- Do NOT use WebSearch, WebFetch, or any tool that could surface post-cutoff information about this company
- Do NOT use prior training-data knowledge of any post-cutoff events about this company (bankruptcies, going-private events, design-win wins or losses, executive departures, lawsuits)
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
1. Read the filings index. Pick the most substantive PRE-CUTOFF filing (10-K for US-listed filers; 20-F for foreign private issuers like INVZ; S-1 if recent IPO and no 10-K yet; 10-Q if newer interim disclosures materially change the picture).
2. Slice the filing to ~120K chars from key business sections + financial-statement notes:
     python3 -c "from verticals.public_co.filing_slice import slice_filing; t=open('FILING_PATH').read(); print(slice_filing(t, budget_chars=120000))" > /tmp/sliced_{ticker}.txt
   Then Read /tmp/sliced_{ticker}.txt.
3. Extract 5-8 testable factual claims per the EXTRACT RUBRIC below. Pick 1-3 M-source queries per claim from the catalog. Prefer:
     - edgar_fts.query_fulltext (cik=COUNTERPARTY) → for OEM-design-win / customer-corroboration claims (does Volvo's 10-K mention this lidar company?). Try multiple OEM CIKs + multiple search terms (company name, product name, platform name).
     - uspto_odp.query_assignee → for patent / FMCW / MEMS / optics IP claims. Lidar has heavy patent activity; n_granted >= 10 with claimed-technology hit is PASS.
     - edgar_fts.query_fulltext (no cik) → for general counterparty corroboration across all filers — how often does anyone mention this company? Asymmetry with company's own filing-count is a Heuristic-7 signal.
     - epa_frs.query_facilities → only for explicit US-state manufacturing-facility claims (lidar mostly assembled by EMS partners, so usually N/A — see Heuristic 1).
     - usaspending.query_recipient_contracts → only if the company claims DoD / DOT / federal contracts.
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
- Names a specific external entity (OEM customer, Tier-1 partner, platform name) the framework can independently look up
- Quantifies something verifiable: design-wins count, named-platform Start-of-Production (SOP) year, annualized unit-volume forecast, dollar revenue from a named customer, patent count, manufacturing-capacity claim
- Asserts a status with a registry analog: NDAA-compliance, ISO-26262 certification, AEC-Q100 qualification, named-OEM program participation
- Asserts a STAGE on the design-win ladder: RFQ vs nomination vs design-win vs A/B/C-sample vs SOP vs series-production

LOW value (skip):
- Pure accounting (cash, share counts) unless a material vendor/equity event (stock-for-services payment, reverse split, going-concern qualifier — those ARE high-discriminative for distress signaling)
- Subjective characterizations ("we are the leader in lidar")
- Market-size / TAM claims with no company-specific assertion
- Pure forward projections with NO named counterparty AND NO quantified milestone

Each claim: {{claim_id, claim_text, subject, predicate, object_value, source_quote, category, queries[]}}.
Categories: customer_pipeline | design_win | regulatory_milestone | production_volume | technology | partnership | physical_facility | financial_distress | vendor_relationship | other.

== SCORE RUBRIC ==
Severity: PASS / MODERATE_UNDERDELIVERY / SEVERE_UNDERDELIVERY / RED_FLAG_NEGATIVE / UNVERIFIABLE.

== CALIBRATION HEURISTICS (apply BEFORE deciding severity) ==
1. EPA FRS scope — lidar product is typically EMS-assembled (light electronics, not emissions-regulated). Absence in FRS is NOT a red flag for lidar pure-plays. Do not red-flag absence.
2. Foreign-issuer caveat — INVZ (Israel) files 20-F not 10-K. 20-F sections of interest: Item 4 (Information on Company), Item 5 (Operating and Financial Review), Item 10 (Additional Information). DO NOT score INVZ's lack of 10-K filings as a signal. Also note that Israeli filers may use shekel-denominated financials.
3. Planned vs operational — STAGE LADDER discipline is decisive for this cohort. "Selected" / "nominated" / "RFQ" / "evaluating" are pre-SOP and NOT revenue-bearing. "Design-win awarded" with no Start-of-Production date is also pre-SOP. Only "series production" / "SOP achieved" / "shipping at volume" counts as revenue-bearing. If a company conflates these stages in marketing-tier language, the severity tier depends on whether the gap is disclosed in the financial-statement notes:
    - Notes disclose stage clearly + marketing conflates → MODERATE_UNDERDELIVERY (disclosure quality issue)
    - Notes ALSO conflate stages → SEVERE_UNDERDELIVERY (substantive misstatement)
    - Notes describe a stage that contradicts marketing tier → RED_FLAG_NEGATIVE
4. Investment vs operating — strategic-investor / equity-cross relationships (e.g. OEM took a minority stake) are NOT design-wins. Often disclosed alongside design-wins to amplify perceived progress. Score these claims based on the operating-relationship dimension only.
5. Source-jurisdiction mismatches — NHTSA registers COMPLETE VEHICLES, not lidar components. Do NOT query nhtsa.query_manufacturer for the lidar company name (will always return 0 — not a signal). NHTSA queries CAN be useful for the OEM customer to verify platform existence.
6. Name-variant fragility — try multiple variants for OEM cross-check: brand name (Luminar / Aeva / Ouster / Innoviz / MicroVision), product name (Iris / Halo / OS-DOME / InnovizOne / InnovizTwo / MOVIA / MAVIN), platform name (Volvo EX90, Polestar 3, Mercedes EQS, BMW iX, VW Trinity).
7. Counterparty-disclosure threshold — for any claim naming a Tier-1 OEM as a series-production customer, run edgar_fts.query_fulltext with both the lidar company name AND the lidar product name, restricted to the OEM's CIK. A material series-production lidar contract with a $50B+ OEM is material to the OEM and should appear in the OEM's 10-K / 20-F. ABSENCE while the lidar player claims headline OEM-design-win revenue is a HARD CONTRADICTION → RED_FLAG_NEGATIVE. ABSENCE while the lidar player only claims a "selection" / "design-win awarded" pre-SOP is MODERATE_UNDERDELIVERY (the OEM doesn't yet have a series-production obligation to disclose).
8. Patents — uspto_odp.query_assignee preferred over google_patents. PASS if n_granted >= 10 with claimed-technology-area hit (lidar / FMCW / ToF / MEMS / optical-phased-array / silicon-photonics). SEVERE only on Nikola pattern (>= 30 granted, 0 in claimed areas).
9. **DESIGN-WIN-STAGE-LADDER (lidar-specific)**: if the company claims a "design-win" or "nomination" with a named OEM but provides no SOP date, no annualized volume, no platform name, AND the OEM 10-K mentions neither the lidar company nor the product line, score SEVERE_UNDERDELIVERY. If the OEM 10-K describes the platform (e.g. Volvo EX90) but does NOT mention the lidar supplier, and the lidar company claims to be supplying that platform in series production, that is a HARD CONTRADICTION → RED_FLAG_NEGATIVE.
10. **DELISTING / GOING-CONCERN FINGERPRINTS**: form types in the filings_index can themselves be claim-adjacent signals. Form 15-12G (registration termination), Form 25-NSE (notification of removal from listing), Form 25 (delisting), or repeated reverse-split 8-Ks are direct distress markers. If the latest pre-cutoff filing list contains any of these, flag the relevant filing's claims (e.g. "we are a viable going concern" or "we expect series-production revenue by 20XX") with elevated severity (MODERATE at minimum, SEVERE if the company also still represents future production in S-3 / 8-K language).

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
