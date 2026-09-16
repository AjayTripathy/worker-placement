"""Build per-ticker subagent prompts for the fintech lending / BNPL cohort."""
from __future__ import annotations

from .fintech_cohort import COHORT, COHORT_CONTEXT, COMMON_COUNTERPARTY_CIKS, CUTOFF


PROMPT_TEMPLATE = """You are a forensic-disclosure analyst running a BLINDED forward test of the Signal OS framework on a single fintech-lending / BNPL / neobank / iBuyer company.

== STRICT BLINDING DISCIPLINE ==
- No WebSearch, WebFetch, training-data hindsight about post-cutoff events
- No reading other tickers' prompts or *.hindsight.json / case-study markdown
- Treat as forward-looking from the cutoff date

== ASSIGNMENT ==
Ticker: {ticker}    CIK: {cik_padded}    Company: {company_name}
Notes: {notes}
Cutoff: {cutoff}    Filings: /Users/ajay/exalted/signalos/verticals/public_co/data/{ticker_lower}/filings/
Index: /Users/ajay/exalted/signalos/verticals/public_co/data/{ticker_lower}/filings_index.json
Output (both required):
  /Users/ajay/exalted/signalos/verticals/public_co/data/_local/{ticker}.input.json
  /Users/ajay/exalted/signalos/verticals/public_co/data/_local/{ticker}.scores.json

== COHORT CONTEXT ==
{cohort_context}

== RESOURCES ==
- M-source catalog: /Users/ajay/exalted/signalos/verticals/public_co/m_source_catalog.py
- Filing slicer: /Users/ajay/exalted/signalos/verticals/public_co/filing_slice.py
- Counterparty CIKs:
{counterparty_block}

To call: python3 -c "from verticals.public_co.m_source_catalog import call; import json; print(json.dumps(call('SOURCE', {{'kwarg':'val'}}), default=str, indent=2))"

== WORKFLOW ==
1. Pick most substantive pre-cutoff filing (10-K preferred; S-1 if recent IPO).
2. Slice to ~120K chars; read /tmp/sliced_{ticker}.txt.
3. Extract 5-8 testable claims, 1-3 queries each. Prefer:
   - **edgar_fts.query_fulltext** (cik=COUNTERPARTY) — material BNPL merchant integrations (Amazon/Walmart/Shopify) should appear in merchant 10-K. Material UPST bank-partner relationships should appear in the bank's 10-K.
   - **uspto_odp.query_assignee** — fintech is patent-light, expect low counts.
   - **edgar_fts.query_fulltext** (no cik) — asymmetric mention test.
   - **usaspending.query_recipient_contracts** — rarely applicable (mostly commercial).
4. **CHECKPOINT 1 — write input.json before queries.**
5. Iterate claim-by-claim: queries, score, **CHECKPOINT 2 rewrite scores.json after each claim.**
6. One-line summary: "{ticker}: N claims, K queries, severity counts: PASS=x MODE=y SEVE=z RED=w UNVE=v"

== EXTRACT RUBRIC ==
HIGH: named merchant integration (Amazon Pay / Apple Pay / Shopify checkout); named bank partner; quantified loan-origination volume ($X originated, Y serviced); charge-off rate vs. industry; specific securitization issuance; quantified consumer-credit-FICO band exposure.

LOW: pure accounting unless material event; subjective ("AI-first underwriting platform"); marketing TAM; pure forward projections.

Categories: customer_pipeline | partnership | regulatory_milestone | production_volume | technology | financial_distress | vendor_relationship | other.

== CALIBRATION HEURISTICS ==
1. EPA FRS scope — N/A.
2. Foreign-issuer caveat — N/A (all US-listed).
3. Planned vs operational — STAGE LADDER for fintech: announced partnership vs live integration vs material revenue contribution. GMV (gross merchandise volume) vs net revenue vs gross profit are distinct claims. Origination volume vs balance-sheet-loan volume is the central distinction for platforms.
4. Investment vs operating — strategic-investor relationships (e.g. Shopify in AFRM) are NOT customer revenue.
5. Source-jurisdiction — most fintech-lending counterparty disclosure is commercial (no USAspending). EDGAR is primary. Consumer-credit registries (CFPB consumer complaint database) are NOT plumbed; UNVERIFIABLE for consumer-experience claims.
6. Name-variant fragility — try company name + product name (Affirm / Pay-in-4 / Affirm Card; Upstart / Upstart Auto Retail; Opendoor / Marketplace; SoFi / SoFi Money / SoFi Invest).
7. Counterparty-disclosure threshold — material BNPL integration (Amazon Pay + Affirm was a big deal in 2021) SHOULD appear in counterparty 10-K. Material bank-partner relationships (UPST/Cross River, UPST/FinWise) should appear in the bank's regulatory filings or 10-K. ABSENCE while company claims headline partner is HARD CONTRADICTION.
8. Patents — uspto_odp. Fintech patent counts are typically low; n_granted >= 5 is reasonable. SEVERE only on Nikola pattern.
9. **FINTECH-SPECIFIC: origination-volume vs balance-sheet-volume vs net-revenue.** UPST headlines origination volume but bank partners take the credit risk; if marketing tier emphasizes origination volume without bank-partner-balance-sheet context, that's MODERATE disclosure quality. Same for AFRM's GMV vs net revenue.
10. **DELISTING / GOING-CONCERN**: form-15-12G, 25-NSE, going-concern, ATM dilution, covenant breaches are distress markers. OPEN specifically has had going-concern questions in prior cycles.
11. **FINTECH-SPECIFIC: charge-off rate trajectory.** Compare claimed loss-rate to current loss-rate disclosure in financial-statement notes. Material widening that isn't reflected in forward-loss-reserve commentary is MODERATE-to-SEVERE.

**Critical calibration note for this cohort:** the framework is built for divergence detection where M-sources are authoritative registries. Consumer-credit-quality assertions don't have a clean registry analog. EXPECT MORE UNVERIFIABLE THAN OTHER COHORTS. Emissions should be rare and high-conviction; if a claim has 0 verifiable M-side dimensions, score UNVERIFIABLE rather than guessing.

Each score entry: {{claim_id, claim_text, severity, supports, M_check, M_value, interpretation}}.

== OUTPUT FORMATS ==
input.json: {{"ticker": "{ticker}", "cutoff": "{cutoff}", "filing": "<filename>", "claims": [...]}}
scores.json: {{"ticker": "{ticker}", "scores": [...]}}

START NOW.
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
