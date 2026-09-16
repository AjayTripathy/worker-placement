"""Build per-ticker subagent prompts for the retail distress cohort."""
from __future__ import annotations

from .retail_cohort import COHORT, COHORT_CONTEXT, COMMON_COUNTERPARTY_CIKS, CUTOFF


PROMPT_TEMPLATE = """You are a forensic-disclosure analyst running a BLINDED forward test of the Signal OS framework on a single brick-and-mortar retailer.

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
1. Pick most substantive pre-cutoff filing (10-K preferred).
2. Slice to ~120K chars; read /tmp/sliced_{ticker}.txt.
3. Extract 5-8 testable claims, 1-3 queries each. Prefer:
   - **edgar_fts.query_fulltext** (cik=COUNTERPARTY) — material wholesale-supplier relationships: does HBI/LEVI/VFC/TPR's 10-K mention this retailer as a top customer? Mall-REIT landlords (SPG/MAC) disclose top-tenant exposure.
   - **edgar_fts.query_fulltext** (no cik) — asymmetric mention test.
   - **uspto_odp.query_assignee** — typically irrelevant for retail; expect low.
   - **usaspending.query_recipient_contracts** — N/A.
4. **CHECKPOINT 1 — write input.json before queries.**
5. Iterate claim-by-claim: queries, score, **CHECKPOINT 2 rewrite scores.json after each claim.**
6. One-line summary: "{ticker}: N claims, K queries, severity counts: PASS=x MODE=y SEVE=z RED=w UNVE=v"

== EXTRACT RUBRIC ==
HIGH: comp-store-sales trajectory + segment-level disclosure; store-count + planned-closure cadence; lease commitments (long-tail / front-loaded); inventory turns; going-concern qualifier / covenant compliance; material wholesale-supplier mentions; mall-REIT tenant exposure.

LOW: pure marketing ("evolving the customer experience"); seasonality boilerplate; pure forward projections.

Categories: customer_pipeline | partnership | production_volume | technology | physical_facility | financial_distress | vendor_relationship | other.

== CALIBRATION HEURISTICS ==
1. EPA FRS scope — retail is light-touch (no manufacturing emissions); N/A.
2. Foreign-issuer — N/A (all US-listed).
3. Planned vs operational — STAGE LADDER: announced store-closure vs executed closure; announced cost-savings vs realized cost-savings; announced transformation plan (year 1) vs progress (year N). Multi-year transformation plans are common in retail distress; verify against M-side evidence in financial-statement notes.
4. Investment vs operating — retail rarely has equity-cross relationships worth analyzing.
5. Source-jurisdiction — most retail-distress signals are *internal* (going-concern, comp-store-sales) rather than external (no USAspending, no NHTSA). Counterparty cross-check via supplier 10-K is the main external M-source.
6. Name-variant fragility — try retailer name + subsidiary brand (Macy's / Bloomingdale's / Bluemercury; Gap / Old Navy / Banana Republic / Athleta; Nordstrom / Nordstrom Rack).
7. Counterparty-disclosure threshold — material wholesale-supplier exposure (e.g. HBI sells ~10% of revenue to Walmart historically) means the supplier's 10-K names the retailer. ABSENCE while retailer claims to be a major customer of a supplier is HARD CONTRADICTION.
8. Patents — N/A for retail; absence is not a red flag.
9. **RETAIL-SPECIFIC: comp-store-sales claim test.** If marketing tier headlines positive comps but financial-statement notes disclose negative comps (or stagnant comps with negative traffic offset by positive AUR), that's MODERATE-to-SEVERE depending on the gap.
10. **DELISTING / GOING-CONCERN (CRITICAL for this cohort)**: form-15-12G, 25-NSE, going-concern qualifier, material lease-rejection 8-Ks, covenant-waiver disclosures, large impairment charges, ATM offerings, reverse splits, recently-emerged-from-Ch.11 status (BIG specifically). Elevate severity of forward-revenue claims accordingly.
11. **RETAIL-SPECIFIC: store-count trajectory.** Compare claimed new-store openings vs disclosed gross-closures. Net store count should match the disclosed running total.
12. **RETAIL-SPECIFIC: lease portfolio.** Long-tail lease commitments are a structural balance-sheet risk that often gets understated in marketing-tier disclosure. Check lease-maturity ladder.

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
