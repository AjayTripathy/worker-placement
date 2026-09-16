"""Build per-ticker subagent prompts for the cell/gene therapy cohort."""
from __future__ import annotations

from .cellgene_cohort import COHORT, COHORT_CONTEXT, COMMON_COUNTERPARTY_CIKS, CUTOFF


PROMPT_TEMPLATE = """You are a forensic-disclosure analyst running a BLINDED forward test of the Signal OS framework on a single cell/gene-therapy biotech or commercial-stage biotech control.

== STRICT BLINDING DISCIPLINE ==
- No WebSearch, WebFetch, or training-data hindsight about post-cutoff events
- No reading other tickers' prompts or any *.hindsight.json / *.preslicer.json / _<cohort>_outcomes.py / case-study markdown
- Treat as a true forward-looking analysis from the cutoff date

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
1. Read filings_index. Pick most substantive pre-cutoff filing (10-K preferred; 20-F for CRSP; S-1 if recent IPO; 10-Q for newer).
2. Slice: python3 -c "from verticals.public_co.filing_slice import slice_filing; t=open('FILING_PATH').read(); print(slice_filing(t, budget_chars=120000))" > /tmp/sliced_{ticker}.txt
3. Extract 5-8 testable claims. Pick 1-3 M-source queries per claim. Prefer:
   - **clinical_trials.query_by_lead_sponsor** for trial-pipeline claims (the killer M-source for biotech)
   - **openfda.query_approved_drugs** for FDA-approval claims
   - **edgar_fts.query_fulltext** (cik=COUNTERPARTY) for partnership / milestone-payment counterparty corroboration
   - **uspto_odp.query_assignee** for CRISPR / gene-editing / LNP / cell-therapy patent claims
4. **CHECKPOINT 1 — write input.json immediately before queries.**
5. Iterate claim-by-claim: run queries (1-2s sleeps), score severity, **CHECKPOINT 2 rewrite entire scores.json after each claim.**
6. Final one-line summary: "{ticker}: N claims, K queries, severity counts: PASS=x MODE=y SEVE=z RED=w UNVE=v"

== EXTRACT RUBRIC ==
HIGH discriminative:
- Names specific trial (NCT number, trial name), specific drug candidate (preclinical, IND-cleared, Phase 1/2/3, NDA/BLA filed, approved)
- Quantifies: trial enrollment counts, patient response rates, milestone-payment dollars, manufacturing-capacity (vector batches, cell-therapy lots), partnership terms
- Specific status (NCT-registered, IND/BLA accepted, Breakthrough Designation, Fast Track, Priority Review, Orphan)
- Biotech-specific high-value:
  * "Phase X with N patients enrolled at clinicaltrials.gov NCT..." — verifiable via clinical_trials.query_by_lead_sponsor
  * "milestone payment of $X from PARTNER" — verifiable via PARTNER's 10-K R&D commentary
  * "BLA/NDA filed for INDICATION" — verifiable via openfda.query_approved_drugs (post-approval) or counterparty disclosure (pre-approval)

LOW value: pure accounting (cash, share counts) unless material vendor/equity event; subjective characterizations ("we are pipeline leader"); generic disease-market-size claims.

Each claim: {{claim_id, claim_text, subject, predicate, object_value, source_quote, category, queries[]}}.
Categories: clinical_trial | regulatory_milestone | partnership | technology | production_volume | financial_distress | vendor_relationship | other.

== CALIBRATION HEURISTICS ==
1. EPA FRS scope — biotech R&D facilities are EPA-regulated for BSL labs / hazardous waste; absence in FRS for a claimed US production facility IS a real signal. Pilot manufacturing for cell/gene therapy is bioreactor-heavy and registers.
2. Foreign-issuer caveat — CRSP is Swiss (20-F). DO NOT score CRSP's lack of 10-K as a signal.
3. Planned vs operational — TRIAL-PHASE LADDER is decisive: preclinical -> IND -> Phase 1 -> Phase 2 -> Phase 3 -> filed -> approved. Each stage has a distinct clinical_trials.gov status. Conflating Phase 2a interim data (small open-label) with Phase 3 pivotal (registration-enabling) is the central evasion pattern.
4. Investment vs operating — pharma equity stakes (e.g. Pfizer / Bayer minority investments) are NOT commercial-supply revenue.
5. Source-jurisdiction — clinical_trials.gov covers global trials registered there; openFDA covers US approvals. Foreign clinical work (e.g. China, EU EMA-only trials) may not be in clinical_trials.gov.
6. Name-variant fragility — try drug-candidate name AND target-gene AND indication (e.g. CRSP: "exa-cel" / "CTX001" / "Casgevy" / "exagamglogene autotemcel" / "sickle cell"). Try multiple counterparty CIKs.
7. Counterparty-disclosure threshold — material partnership ($100M+ upfront or milestone-bearing) IS in the counterparty's 10-K R&D section; ABSENCE while company claims a headline partnership is RED_FLAG_NEGATIVE.
8. Patents — uspto_odp.query_assignee. PASS if n_granted >= 10 with claimed-technology hit (CRISPR / gene editing / LNP / AAV / base-editing / cell-therapy / TCR). SEVERE only on Nikola pattern.
9. **BIOTECH-SPECIFIC: clinicaltrials.gov registration test.** For any pipeline asset the company claims is in clinical trials, run clinical_trials.query_by_lead_sponsor. If the trial doesn't appear: MODERATE if the trial-phase claim is recent (could be pre-registration window) or SEVERE if claimed as "active" but no NCT number visible. If the company emphasizes "we have N trials underway" but clinical_trials.gov shows zero or a much smaller number under the sponsor name: SEVERE.
10. **DELISTING / GOING-CONCERN**: form-15-12G, 25-NSE, reverse splits, going-concern qualifier, large dilutive issuance are distress markers. Cell/gene therapy names have particularly cash-intensive pipelines.
11. **REVENUE-RECOGNITION (biotech-specific)**: many pre-revenue biotechs recognize "collaboration revenue" from partner milestone payments. If headline revenue is mostly milestone-payment recognition rather than product sales, that's a structural fact (not a flag), but check whether the milestones are tied to operational deliverables vs. open-ended upfront payments.

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
