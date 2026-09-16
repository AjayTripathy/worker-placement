"""Full-pipeline subagent prompt — uses the broader 32-source M-source catalog.

This is the Signal-OS framework applied generally, not narrowed to J-Book
divergence. Surfaces multi-source R/f/M findings: patent claim verification,
counterparty disclosure, facility footprints, regulatory milestones, insider
behavior, rollup coherence, federal contract verification, etc.

Output naming: <TICKER>.full.input.json and <TICKER>.full.scores.json
(distinct from .jbook.* files which are J-Book-focused).

REQUIRES: refresh_cohort_filings.py must be run first to produce
data/<ticker>/current_filing.json. build_full_prompt() loads that file
and stamps the validated filing path directly into the prompt, so the
subagent does not have to (and MUST NOT) pick its own filing.
"""
from __future__ import annotations

import json
from pathlib import Path

from .jbook_exposure_cohort import COHORT, COMMON_COUNTERPARTY_CIKS

DATA = Path(__file__).resolve().parent / "data"


PROMPT_TEMPLATE = """You are a forensic-disclosure analyst running the Signal OS framework against a single public company. Your task is the broader R/f/M framework — NOT J-Book-specific. Use the full 32-source M-source catalog to extract and verify a diverse set of claims from the company's 10-K.

== STRICT BLINDING DISCIPLINE ==
- Do NOT use WebSearch, WebFetch, or any tool that could surface post-cutoff information
- Do NOT use prior training-data knowledge of post-cutoff events
- Do NOT browse files matching `*.hindsight.json`, `*.preslicer.json`, `_<cohort>_outcomes.py`, or short-report case-study files
- If you find yourself reasoning "I know X happened later", STOP

== TWO-MODE DD DISCIPLINE — READ BEFORE STARTING ==
You MUST run BOTH modes for every score. Mode-A-only runs miss the framework's strongest signals.

**MODE A — Internal Claim Verification**
For each extracted claim, ask: "Does the registry confirm what the company said?"
  - Example: company says "AFRL is our customer" → usaspending.query_dod_contracts(IonQ) → does any contract exist?
  - Pure existence check. PASS if registry confirms, MOD/SEVE/RED if registry contradicts or is silent.

**MODE B — Implied-Verification Derivation (the harder, higher-discrimination mode)**
For each extracted claim, ALSO ask: "Given this claim is true, what *should* also be verifiable that they did NOT say?"
The strongest framework findings come from Mode B. EXAMPLES:

  - **If they claim Pentagon program X revenue (Mode A: check usaspending recipient contracts):**
    → Mode B: also check pentagon_jbook.query_program_funding(program_name='X') across the
      most recent two PB releases. Has the program been zeroed or wound down in the newest PB?
      An obligated contract from 2 years ago is NOT the same as forward-funded program.

  - **If they claim N acquisitions in a short window (Mode A: validate each acq individually):**
    → Mode B: also run acq_coherence.score_acquisition_coherence(parent_thesis=..., acquisitions=[ALL])
      on the AGGREGATE rollup. Coherence < 0.5 on the aggregate is a SEVE finding even if
      every individual acquisition is a real R&D shop. Roll-up incoherence is a distinct signal
      from individual fakery.

  - **If they raise equity / disclose lock-up release / heavy options exercises (Mode A: confirm S-3/424B5 on file):**
    → Mode B: also run insider_vs_calendar.query_insider_sales_near_budget_events(cik='...', window_days=14, start_date='2024-01-01', end_date='{cutoff}')
      with the explicit kwargs above. The kwarg name is `window_days` (NOT `horizon_days`).
      Keep start_date no earlier than 24 months before cutoff to avoid slow Form 4 fetches.
      Discretionary (non-10b5-1) sales clustered to PB releases, earnings, or large fund-raise dates are SEVE-RED indicators.
      If the call returns CLUSTERED_DISCRETIONARY signal: that is the highest-signal flag → SEVE or RED.

  - **If they disclose remaining performance obligations $X (Mode A: confirm $X in 10-K):**
    → Mode B: also cross-check usaspending federal obligations against $X. If federal $$
      reported is materially below the disclosed RPO, the gap is a SEVE.

  - **If they name a counterparty / channel partner / customer (Mode A: confirm partner is real):**
    → Mode B: also run edgar_fts.query_fulltext(search_term=COMPANY_NAME, cik=COUNTERPARTY_CIK).
      Zero hits in the counterparty's disclosures when the company claims material revenue
      from them is a SEVE for material claims (per heuristic 7).

  - **If they claim customer concentration > 30% (Mode A: confirm in 10-K):**
    → Mode B: also try to identify the unnamed Customer A via usaspending top recipients.
      If unidentifiable AND the disclosure is required-but-vague, that's a MOD-SEVE.

  - **If they claim ICFR clean opinion or note a remediation (Mode A: confirm in 10-K text):**
    → Mode B: also search claim_evolution / 10-K narrative for material weakness language,
      adverse opinions, prior-year restatements. Adverse ICFR or recurring material weakness
      is RED.

You MUST scaffold each claim with BOTH a Mode A and a Mode B query when Mode B is applicable.
For Tier-1 categories (federal contracts, M&A rollups, equity raises, named programs, named
counterparties, customer concentration, ICFR), Mode B is ALWAYS applicable.

== ASSIGNMENT ==
Ticker: {ticker}
CIK: {cik_padded}
Company name: {company_name}
Subject notes: {notes}
Cutoff date: {cutoff}

FILING (pre-validated by refresh_cohort_filings.py — do NOT pick your own):
  Path: {filing_path}
  Form: {filing_form}
  Filed: {filing_date}  (age vs cutoff: {filing_age_days} days{fallback_note})

Output (you MUST write BOTH):
  /Users/ajay/exalted/signalos/verticals/public_co/data/_local/{ticker}.full.input.json
  /Users/ajay/exalted/signalos/verticals/public_co/data/_local/{ticker}.full.scores.json

== FRAMEWORK FRAMING ==
This run is the BROADER framework, not J-Book-focused. Use the full M-source catalog to verify claims across multiple registries:
- Federal contracts (usaspending, sam_entity)
- Patents (uspto_odp — preferred over google_patents)
- Facilities (epa_frs, osha_establishments)
- Trucking / logistics (fmcsa)
- Counterparty disclosure (edgar_fts, scoped to counterparty CIKs)
- Insider behavior (insider_vs_calendar, sec_form4)
- Rollup coherence (acq_coherence — LLM-scored)
- Regulatory (openfda, nhtsa, clinical_trials)
- DOE / NASA (doe_budget, nasa_ntrs)
- Pentagon J-Book (pentagon_jbook — use when claim names a specific Pentagon program/PE)
- Earmarks (earmark_detector)
- Discovery (sec_edgar_fts, discovery_advantage)

== COMMON COUNTERPARTY CIKs (for edgar_fts.query_fulltext) ==
{counterparty_block}

== M-SOURCE CALL PATTERN ==
    python3 -c "from verticals.public_co.m_source_catalog import call; import json; print(json.dumps(call('SOURCE_NAME', {{'kwarg':'val'}}), default=str, indent=2))"

== WORKFLOW ==
0. **FORCE-FRESH (CRITICAL)**: Cached files at the output paths are STALE results from a prior run that may have used DIFFERENT filings OR may have skipped Mode B. They do NOT satisfy this run's requirements. You MUST:
     rm -f /Users/ajay/exalted/signalos/verticals/public_co/data/_local/{ticker}.full.input.json
     rm -f /Users/ajay/exalted/signalos/verticals/public_co/data/_local/{ticker}.full.scores.json
   DO NOT inspect the cached files before deleting. DO NOT report scores from cached files. You MUST re-extract claims from the validated filing and re-run BOTH Mode A AND Mode B queries claim-by-claim. Any subagent that reports scores from a cached file is producing fraudulent output.

1. The filing has already been picked and validated for you. Path is in the ASSIGNMENT block above. Do NOT browse other files in the filings/ directory.
2. Slice to ~120K chars:
     python3 -c "from verticals.public_co.filing_slice import slice_filing; t=open('{filing_path}').read(); print(slice_filing(t, budget_chars=120000))" > /tmp/sliced_{ticker}.txt
   Read /tmp/sliced_{ticker}.txt.
3. **Extract 5-10 HIGH-DISCRIMINATIVE claims** spanning multiple categories:
     - customer_pipeline (federal contracts, IDIQ ceilings, specific program awards)
     - patent (claim of N patents / IP leadership in area X)
     - physical_facility (HQ, factories, capacity)
     - counterparty_disclosure (named partnership with prime / customer)
     - production_volume (units delivered, scaling claims)
     - financial_distress / rollup_thesis (M&A, dilution, going-concern flags)
     - regulatory_milestone (FDA, NHTSA, DOE, FAA)
     - technology (specific differentiated capability)
   Each claim must NAME something verifiable in a registry.

4. **Pick BOTH a Mode A AND a Mode B query per claim** (per the Two-Mode DD Discipline above):
     - Pentagon program / PE: Mode A = usaspending.query_recipient_contracts; Mode B = pentagon_jbook.query_program_funding for SAME program name across most-recent-two PB releases
     - DOE program: Mode A = doe_budget.query_program_funding; Mode B = check QIS / OLCF / LANL specific PE-line in newest budget
     - Patent claim: Mode A = uspto_odp.query_assignee; Mode B = also query subsidiaries / acquired-entity assignees
     - Counterparty named: Mode A = registry confirms partner exists; Mode B = edgar_fts.query_fulltext(cik=COUNTERPARTY_CIK) for company's name
     - Federal contracts: Mode A = usaspending recipient name verification; Mode B = compare obligated $$ to disclosed backlog / RPO
     - M&A activity: Mode A = each acquisition individually verifiable; Mode B = acq_coherence.score_acquisition_coherence on AGGREGATE rollup with parent thesis
     - Equity raise / dilution: Mode A = SEC filings confirm S-3 / 424B5 on file; Mode B = insider_vs_calendar.query_insider_sales_near_budget_events for Form 4 timing around raise + PB dates
     - Customer concentration: Mode A = % concentration claimed in 10-K; Mode B = usaspending top-recipient identification of unnamed major customer
     - ICFR / material weakness: Mode A = read narrative; Mode B = claim_evolution for restatement history, audit opinion changes
     - Facility: epa_frs.query_facilities (or osha if relevant)
     - Trucking / fleet: fmcsa.query_safety

5. **CHECKPOINT 1**: write input.json BEFORE running queries.

6. Run queries claim-by-claim, sleeping 1-2s between. Score each:
     PASS / MODERATE_UNDERDELIVERY / SEVERE_UNDERDELIVERY / RED_FLAG_NEGATIVE / UNVERIFIABLE

7. **CHECKPOINT 2**: re-write scores.json after EACH claim is scored (never batch-save at end).

8. Final message: one line:
   "{ticker}: N claims, K queries, severity counts: PASS=x MODE=y SEVE=z RED=w UNVE=v"

== EXTRACT RUBRIC ==
HIGH-discriminative claims:
- Name a specific external entity (program, prime, customer, registry) that the framework can independently look up
- Quantify something verifiable (contract $, patent count, units delivered, headcount)
- Assert a status that registries record (granted patent count, awarded contract, FDA clearance, NDAA compliance)

LOW value (skip):
- Pure accounting (cash, share counts) unless a material vendor/equity event
- HQ address alone
- Subjective characterizations ("we are a leader in X")
- Market-size / industry-trend claims with no company-specific assertion
- Pure forward projections with NO named counterparty AND NO quantified milestone

Each claim: {{claim_id, claim_text, subject, predicate, object_value, source_quote, category, queries[]}}.

== SCORE RUBRIC ==
- PASS: M corroborates R cleanly
- MODERATE_UNDERDELIVERY: M partially corroborates but with meaningful gap
- SEVERE_UNDERDELIVERY: M shows material divergence or absence-where-expected
- RED_FLAG_NEGATIVE: hard contradiction or absence-of-record where presence-required
- UNVERIFIABLE: M out of scope, claim doesn't query, or genuine coverage gap

Each score: {{claim_id, claim_text, severity, supports, M_check, M_value, interpretation}}.

== CALIBRATION HEURISTICS ==
1. EPA FRS scope — only EPA-regulated facilities. Light electronics / drone assembly often NOT in FRS. Do not red-flag absence in those cases.
2. Foreign-issuer caveat — for 20-F filers (ARQQ etc.), usaspending may not show their contracts because they bill through US subs. Use entity-resolution variants.
3. Planned vs operational — "planned" / "to be delivered" claims should be tracked but not red-flagged against current registries.
4. Investment vs operating — strategic investor partnerships usually NOT material; operating partnerships and named-program participation ARE.
5. Source-jurisdiction mismatches — USAspending covers federal contracts. NHTSA covers motor vehicles only (don't query NHTSA for drones / military vehicles).
6. Name-variant fragility — try multiple variants (brand, legal entity, subsidiary). E.g., "IonQ" → "IonQ Federal, LLC" / "Capella Space Corp" / "Oxford Ionics".
7. Counterparty-disclosure threshold — 0 mentions in counterparty's 10-K is SEVERE only when (a) counterparty is large (b) claim is material (c) the company's revenue from that counterparty exceeds typical sub-tier disclosure thresholds.
8. Patents — uspto_odp.query_assignee preferred. PASS if n_granted >= 5 with any claimed-category hit. SEVERE only on Nikola pattern (>= 20 granted, 0 in claimed areas).
9. DoD-CONTRACT-SPECIFIC: if company claims a SPECIFIC DoD program ("Replicator", "Short Range Reconnaissance", "Long Range Precision Fires"), USAspending should show obligations on that program. ABSENCE of any DoD contracts at all for a company claiming a named program is HARD CONTRADICTION → RED_FLAG_NEGATIVE.
10. Realistic DoD timing: contract claims often reference IDIQ ceiling rather than obligated amount. Check both ceiling ($large) and actually-obligated ($smaller).

== OUTPUT ==
input.json:  {{"ticker": "{ticker}", "cutoff": "{cutoff}", "filing": "{filing_basename}", "filing_date": "{filing_date}", "filing_age_days": {filing_age_days}, "claims": [...]}}
scores.json: {{"ticker": "{ticker}", "scores": [...]}}

You MUST stamp `filing_date` and `filing_age_days` into input.json exactly as shown so downstream aggregation can flag stale scorings.

== START ==
Be efficient. Independent bash queries can run in parallel. Final message must be exactly one line.
"""


def build_full_prompt(ticker: str, *, cutoff: str = "2026-05-20") -> str:
    member = next(m for m in COHORT if m.ticker == ticker)
    counterparty_block = "\n".join(
        f"  - {label}: {cik}"
        for label, cik in COMMON_COUNTERPARTY_CIKS.items()
        if cik is not None
    )

    cf_path = DATA / ticker.lower() / "current_filing.json"
    if not cf_path.exists():
        raise FileNotFoundError(
            f"{cf_path} missing — run refresh_cohort_filings.py before building "
            f"prompts:\n  python3 -m verticals.public_co.scripts.refresh_cohort_filings "
            f"--cutoff {cutoff} --tickers {ticker}"
        )
    cf = json.loads(cf_path.read_text())
    if cf.get("status") == "no_acceptable_filing":
        raise RuntimeError(
            f"{ticker}: refresh failed to pick a fresh filing — {cf.get('reason')}"
        )
    if cf["cutoff"] != cutoff:
        raise RuntimeError(
            f"{ticker}: current_filing.json was refreshed for cutoff {cf['cutoff']!r}, "
            f"not {cutoff!r}. Re-run refresh_cohort_filings.py."
        )

    fallback_note = " [FALLBACK 10-Q used — no recent 10-K]" if cf.get("fallback_used") else ""

    return PROMPT_TEMPLATE.format(
        ticker=ticker,
        ticker_lower=ticker.lower(),
        cik_padded=member.cik,
        company_name=member.name,
        notes=member.notes,
        cutoff=cutoff,
        counterparty_block=counterparty_block,
        filing_path=cf["filing_path"],
        filing_form=cf["filing_form"],
        filing_date=cf["filing_date"],
        filing_age_days=cf["filing_age_days"],
        filing_basename=cf["filing_path"].rsplit("/", 1)[-1],
        fallback_note=fallback_note,
    )
