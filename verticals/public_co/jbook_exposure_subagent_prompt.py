"""Build per-ticker subagent prompts for the J-Book exposure cohort run.

REQUIRES: refresh_cohort_filings.py must be run first to produce
data/<ticker>/current_filing.json. build_prompt() loads that file and
stamps the validated filing path directly into the prompt so the
subagent cannot pick the wrong file or short-circuit on cached output.
"""
from __future__ import annotations

import json
from pathlib import Path

from .jbook_exposure_cohort import COHORT, COHORT_CONTEXT, COMMON_COUNTERPARTY_CIKS, CUTOFF

DATA = Path(__file__).resolve().parent / "data"


PROMPT_TEMPLATE = """You are a forensic-disclosure analyst running a BLINDED forward test of the Signal OS framework on a single company. Your focus for this cohort is the J-BOOK EXPOSURE DIVERGENCE PATTERN: the company names specific Pentagon programs as material revenue contributors while the Pentagon's forward J-Book shows those programs going unfunded or shrinking.

== STRICT BLINDING DISCIPLINE ==
- Do NOT use WebSearch, WebFetch, or any tool that could surface post-cutoff information about this company
- Do NOT use prior training-data knowledge of any post-cutoff events about this company
- Do NOT browse files matching `*.hindsight.json`, `*.preslicer.json`, `_<cohort>_outcomes.py`, or short-report case-study files (e.g., Wolfpack PDFs)
- If you find yourself reasoning "I know X happened after cutoff", STOP. The point is to test whether the framework catches the divergence at the cutoff date.

== ASSIGNMENT ==
Ticker: {ticker}
CIK: {cik_padded}
Company name: {company_name}
Subject notes (cohort metadata, no outcome labels): {notes}
Cutoff date: {cutoff}

FILING (pre-validated by refresh_cohort_filings.py — do NOT pick your own):
  Path: {filing_path}
  Form: {filing_form}
  Filed: {filing_date}  (age vs cutoff: {filing_age_days} days{fallback_note})

Output (you MUST write both):
  /Users/ajay/exalted/signalos/verticals/public_co/data/_local/{ticker}.jbook.input.json
  /Users/ajay/exalted/signalos/verticals/public_co/data/_local/{ticker}.jbook.scores.json

FORCE-FRESH: cached files at the output paths above are stale. DELETE them before starting:
  rm -f /Users/ajay/exalted/signalos/verticals/public_co/data/_local/{ticker}.jbook.input.json
  rm -f /Users/ajay/exalted/signalos/verticals/public_co/data/_local/{ticker}.jbook.scores.json
You MUST re-extract claims fresh and re-run pentagon_jbook queries. Do NOT short-circuit on cached files.

== COHORT CONTEXT ==
{cohort_context}

== RESOURCES ==
- M-source catalog: /Users/ajay/exalted/signalos/verticals/public_co/m_source_catalog.py
- Filing slicer: /Users/ajay/exalted/signalos/verticals/public_co/filing_slice.py
- Pentagon J-Book corpus (~410 programs): /Users/ajay/exalted/signalos/verticals/public_co/data/_jbook_data/programs.json
- J-Book entity index (contractor → programs): /Users/ajay/exalted/signalos/verticals/public_co/data/_jbook_data/by_entity.json
- Ticker entity resolution (parent → subs/acquisitions/federal-contracting LLCs): /Users/ajay/exalted/signalos/verticals/public_co/data/_entity_resolution/ticker_entity_resolution.json
- Crosswalk (past USAspending contracts → matched PEs per ticker): /Users/ajay/exalted/signalos/verticals/public_co/data/_entity_resolution/ticker_pe_crosswalk.json

Common counterparty CIKs (use with edgar_fts.query_fulltext to test counterparty disclosure):
{counterparty_block}

To call an M-source query, from the repo root:
    python3 -c "from verticals.public_co.m_source_catalog import call; import json; print(json.dumps(call('SOURCE_NAME', {{'kwarg':'val'}}), default=str, indent=2))"

== WORKFLOW ==
1. The filing path is pre-validated and stamped above. Do NOT browse other files in the filings/ directory. Do NOT inspect cached output.
2. Slice the filing to ~120K chars:
     python3 -c "from verticals.public_co.filing_slice import slice_filing; t=open('{filing_path}').read(); print(slice_filing(t, budget_chars=120000))" > /tmp/sliced_{ticker}.txt
   Read /tmp/sliced_{ticker}.txt.
3. **EXTRACT CLAIMS — focus on J-Book-grounded language.** This cohort prioritizes claims that name SPECIFIC Pentagon programs. Look for:
     - Named Program Elements (PE numbers like "0603287F", "1206410SF")
     - Named program titles ("AFRL Quantum Networking", "Short Range Reconnaissance Program of Record", "SDA Tracking Layer T3", "Skyborg", "Collaborative Combat Aircraft", "Space Test Program", "BQM-167 AFSAT", "XQ-58 Valkyrie", "Project Maven")
     - Named DoD customers + revenue concentration ("X% of FY 2025 revenue came from program Y")
     - IDIQ ceilings + obligated-to-date vs ceiling
     - Multi-year program-of-record narratives ("we expect FY 2026 deliveries under contract Z")
   Extract 4-10 J-Book-grounded claims. Also extract 2-3 non-J-Book claims (patents, facilities, counterparty disclosure) for control.
4. **PICK M-SOURCE QUERIES PER CLAIM — for J-Book-grounded claims, pentagon_jbook is the PRIMARY verifier.** Pair with usaspending for cross-check:
     - pentagon_jbook.query_program_funding(program_name="AFRL Quantum Networking") OR
       pentagon_jbook.query_program_funding(pe_number="0603287F") OR
       pentagon_jbook.query_program_funding(contractor_name="IonQ") with cutoff_date="{cutoff}"
     - usaspending.query_dod_contracts(recipient_name="IonQ Federal, LLC") — to confirm the company actually received contracts they claim
     - earmark_detector.query_earmark_status(program_name="...") — if the program is unfunded, was it an earmark whose sponsor lost power?
   For non-J-Book claims, use the standard catalog (edgar_fts for counterparty, uspto_odp for patents, epa_frs for facilities).

   **SERVICES-PRIME-SPECIFIC ROUTING (use these BEFORE marking UNVERIFIABLE):**
   - **revenue_concentration.query_revenue_concentration** — for ANY claim about top customer/vehicle/task-order concentration (e.g., "85% of revenue from N IDIQ TOs", "top vehicle = X% of revenue", "largest TO = Y%"). Adjudicates against hand-curated peer benchmarks (BAH/SAIC/CACI/LDOS/KBR/VVX/PSN). 18% top vehicle + 4% top TO is INDUSTRY-STANDARD → PASS, not MODERATE. Required params: recipient_name + at least one of top_vehicle_pct, top_task_order_pct.
   - **ic_contracting_proxy.query_ic_revenue_consistency** — for ANY claim disclosing IC revenue % (BAH 16%, CACI ~70%, SAIC ~25%, LDOS ~30%). Pentagon J-Book has limited IC visibility (NIP/MIP classified); this triangulates cleared-FTE benchmark × disclosed × USAspending IC-agency floor. Required params: recipient_name + disclosed_ic_revenue_M + cleared_employees (from 10-K Human Capital section).
   - **cybercom_budget.query_cybercom_envelope** — for ANY claim about CMF / CYBERCOM / cyber-mission customer mix. CMF funding spans Army/Navy/USMC/SOCOM cyber SAGs + USCYBERCOM unified appropriation. Single PE lookup misses this. Required params: cutoff_date + (optional) contractor_name for the cross-reference note.
5. **CHECKPOINT 1 — write input.json BEFORE running queries.**
6. Run queries claim-by-claim, sleeping 1-2s between calls. Be polite.
7. **SCORE per the J-BOOK CALIBRATION HEURISTICS below.** **CHECKPOINT 2 — re-write the ENTIRE scores.json after each claim is scored.** Never batch-save.
8. Final message: exactly one line:
   "{ticker}: N claims, K queries, severity counts: PASS=x MODE=y SEVE=z RED=w UNVE=v, J-Book hits: pentagon_jbook fired on M of N J-Book-grounded claims"

== EXTRACT RUBRIC ==
HIGH discriminative claims (J-Book pattern):
- Names a specific DoD program / PE number / line-item the framework can look up in pentagon_jbook
- Quantifies revenue or contract value attributed to that program
- Asserts a forward expectation tied to that program ("we expect FY 2027 deliveries", "we are positioned to win Phase 3")

Each claim: {{claim_id, claim_text, subject, predicate, object_value, source_quote, category, queries[]}}.
Categories: jbook_program_revenue | jbook_program_pipeline | dod_customer_concentration | patent | counterparty_disclosure | facility | rollup_thesis | other.

== SCORE RUBRIC ==
Severity: PASS / MODERATE_UNDERDELIVERY / SEVERE_UNDERDELIVERY / RED_FLAG_NEGATIVE / UNVERIFIABLE.

== J-BOOK CALIBRATION HEURISTICS (apply BEFORE deciding severity) ==
1. **pentagon_jbook signals → severity mapping for claimed-program-revenue claims:**
   - FUNDED_GROWING                  → PASS
   - FUNDED_STEADY                   → PASS
   - FUNDED_SHRINKING                → MODERATE_UNDERDELIVERY
   - UNFUNDED_THIS_YEAR              → SEVERE_UNDERDELIVERY
   - UNFUNDED_TWO_PLUS_YEARS         → RED_FLAG_NEGATIVE
   - TERMINATED                      → RED_FLAG_NEGATIVE
   - NOT_FOUND                       → UNVERIFIABLE (not necessarily bad — corpus may not cover this PE; note coverage gap)
   - NOT_FOUND_IN_TIMERANGE          → UNVERIFIABLE

2. **Materiality test:** the company's RANK on this program matters.
   - "Our prime contract on Program X represents 35% of FY 2025 revenue" + Program X UNFUNDED → RED_FLAG_NEGATIVE (existential)
   - "We participated as a sub on Program X" + Program X UNFUNDED → MODERATE
   - "We expect to compete for Program X" (future, not booked) + UNFUNDED → still material if narrative-load-bearing, downgrade to MODERATE

3. **Reorganization caveat:** a PE labeled UNFUNDED may have been folded into a new PE (DARPA reorgs in FY26 consolidated several PEs into umbrellas like EMERGING OPPORTUNITIES). Before scoring SEVERE/RED, check whether the corpus has a `replacement_program` / `replacement_pe` field. If yes, the funding may have moved, not disappeared — downgrade severity.

4. **PE name ambiguity:** if the company says "AFRL Quantum Networking" and pentagon_jbook returns multiple candidate PEs (e.g., 0603287F + 0603287E + 0602601E), check each — they may have different statuses. Score the MOST-LIKELY-MATCHED PE (use synonyms list in the program entry).

5. **Earmark sub-signal:** if pentagon_jbook returns UNFUNDED_* AND earmark_detector returns EARMARK_SUNSET (sponsor lost power) → the unfunded status is structurally durable; bump severity up one tier.

6. **USAspending cross-check:** if pentagon_jbook says UNFUNDED_* AND usaspending shows the company received the contracts they claim → the past revenue was real but the forward pipeline is gone. SEVERE_UNDERDELIVERY at minimum. If usaspending shows ZERO obligations under the claimed program, the original claim itself was inflated → RED_FLAG_NEGATIVE.

7. **NOT_FOUND in J-Book ≠ red flag.** Our corpus is 410 PEs but does not cover every J-Book line worldwide. Treat NOT_FOUND as UNVERIFIABLE unless the company names a PE explicitly that's clearly outside the corpus scope.

8. **Procurement vs RDT&E:** the J-Book corpus has both. RDT&E PEs (R-2 exhibits) appear as 7-8 digit + letter codes (e.g., 0603287F). Procurement line items (P-40 exhibits) appear as B/C/M/F-prefix codes (B02100=B-21, F02200=F-22A). When the company claims a *production* line, look for the P-40 line item; when they claim *development* exposure, look for the R-2 PE.

Each score entry: {{claim_id, claim_text, severity, supports, M_check, M_value, interpretation}}.

== OUTPUT FORMATS ==
input.json: {{"ticker": "{ticker}", "cutoff": "{cutoff}", "filing": "<filename>", "claims": [...]}}
scores.json: {{"ticker": "{ticker}", "scores": [...]}}

== START NOW ==
Be efficient. Independent bash queries can run in parallel. Final message must be exactly one line.
"""


def build_prompt(ticker: str, *, cutoff: str | None = None,
                  output_infix: str = "jbook") -> str:
    """Build per-ticker subagent prompt. Requires data/<ticker>/current_filing.json
    (produced by refresh_cohort_filings.py).
    """
    member = next(m for m in COHORT if m.ticker == ticker)
    counterparty_block = "\n".join(
        f"  - {label}: {cik}" for label, cik in COMMON_COUNTERPARTY_CIKS.items()
        if cik is not None
    )
    use_cutoff = cutoff or CUTOFF

    cf_path = DATA / ticker.lower() / "current_filing.json"
    if not cf_path.exists():
        raise FileNotFoundError(
            f"{cf_path} missing — run refresh_cohort_filings.py first:\n"
            f"  python3 -m verticals.public_co.scripts.refresh_cohort_filings "
            f"--cutoff {use_cutoff} --tickers {ticker}"
        )
    cf = json.loads(cf_path.read_text())
    if cf.get("status") == "no_acceptable_filing":
        raise RuntimeError(f"{ticker}: no fresh filing — {cf.get('reason')}")
    if cf["cutoff"] != use_cutoff:
        raise RuntimeError(
            f"{ticker}: current_filing.json was refreshed for cutoff {cf['cutoff']!r}, "
            f"not {use_cutoff!r}. Re-run refresh_cohort_filings.py."
        )
    fallback_note = " [FALLBACK 10-Q used]" if cf.get("fallback_used") else ""

    p = PROMPT_TEMPLATE.format(
        ticker=ticker,
        ticker_lower=ticker.lower(),
        cik_padded=member.cik,
        company_name=member.name,
        notes=member.notes,
        cutoff=use_cutoff,
        cohort_context=COHORT_CONTEXT,
        counterparty_block=counterparty_block,
        filing_path=cf["filing_path"],
        filing_form=cf["filing_form"],
        filing_date=cf["filing_date"],
        filing_age_days=cf["filing_age_days"],
        fallback_note=fallback_note,
    )
    if output_infix != "jbook":
        p = p.replace(f"{ticker}.jbook.input.json", f"{ticker}.{output_infix}.input.json")
        p = p.replace(f"{ticker}.jbook.scores.json", f"{ticker}.{output_infix}.scores.json")
    return p
