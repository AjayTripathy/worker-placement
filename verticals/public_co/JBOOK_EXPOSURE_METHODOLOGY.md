# J-Book Exposure Cohort — Architecture & Methodology

*End-to-end documentation of the forward-test cohort that screens public companies for the YSS / IONQ short-thesis pattern: a company names a Pentagon (or DOE) program as a material revenue contributor while the relevant forward-looking budget book shows that program going unfunded, shrinking, or terminated. Companion to the broader `public_co/ARCHITECTURE.md` — this doc covers the J-Book-specific machinery; framework-wide patterns live there.*

---

## 1. The pattern under test

The Wolfpack Research short reports on **York Space Systems (YSS, private)** and **IonQ (IONQ)** share one structural feature: each company derived a material slice of revenue from a *named* Pentagon program element (PE), and that PE had already been zeroed out in the most recent Pentagon J-Book by the time the short report dropped. The customer base was disappearing on a timeline visible to anyone reading the budget docs — months before management acknowledged it in earnings.

In the Signal OS R/f/M framing:

- **R** (Record / claim) — the company's own statement in a 10-K, 10-Q, 8-K, or investor materials that program *X* is a material revenue contributor.
- **f** (the relationship between R and an authoritative external record) — if R is true, the program should appear in the Pentagon's forward-looking J-Book at funded, ideally growing, levels.
- **M** (the measurement) — what the J-Book actually shows: funded, shrinking, unfunded one year, unfunded multiple years, or terminated.
- **Gap** — divergence between R and M is the signal.

This cohort tests whether the Signal OS framework can detect that gap *before* the market repricing event, using only pre-cutoff filings + pre-cutoff budget documents.

---

## 2. End-to-end data flow

Two phases:

### Build phase (one-time, refreshed annually)

```
Pentagon J-Book PDFs ────┐
DOE Budget PDFs ─────────┤
                         ▼
                  ingest_jbook.py  +  ingest_doe_budget.py
                         │
                         ▼
              data/_jbook_data/programs.json  (410 entries)
              data/_doe_data/programs.json    (78 entries, 18 QIS-relevant)
                         │
                         ▼
              extract_pe_narratives.py
                         │
                         ▼
              backfill_contractors.py  (LLM contractor extraction)
                         │
                         ▼
              build_jbook_entity_index.py
                         │
                         ▼
              data/_jbook_data/by_entity.json  (entity → programs[])
```

Independently:

```
For each ticker:
  edgar.py  ──→  data/<ticker>/filings/         (already in repo from prior runs)
  edgar_exhibit_21.py  +  LLM
       │
       ▼
  data/_entity_resolution/ticker_entity_resolution.json
                              (130+ name variants across 22 cohort tickers)
```

USAspending crosswalk (orthogonal evidence layer):

```
usaspending_pe_crosswalk.py
  │  for each ticker:
  │    fetch every DoD contract under every resolved name variant
  │    LLM-match each contract to a PE in programs.json
  ▼
data/_entity_resolution/ticker_pe_crosswalk.json
```

### Run phase (per cohort, per cutoff date)

```
jbook_exposure_cohort.py   ← cohort definition (13 tickers, cutoff 2026-05-20)
        │
        ▼
jbook_exposure_subagent_prompt.build_prompt(ticker)
        │
        ▼
Agent (claude subagent)  ─── runs once per ticker, in isolation, blinded
   reads filing  →  slices to 120K chars  →  extracts 4-10 claims
   →  picks M-sources from catalog  →  queries them (with checkpointing)
   →  scores per J-Book calibration heuristics
        │
        ▼
data/_local/<TICKER>.jbook.input.json     (claims + queries)
data/_local/<TICKER>.jbook.scores.json    (severities)
        │
        ▼
jbook_exposure_aggregate.py
        │
        ▼
data/_jbook_exposure_cohort/PREDICTIONS.md  +  matrix.json
```

---

## 3. Build phase

### 3.1 Pentagon J-Book corpus

DoD's annual J-Books are the comptroller's per-program funding tables. Two exhibit formats matter:

- **R-2 exhibits** — RDT&E justification. Header: `Exhibit R-2, RDT&E Budget Item Justification: PB <YYYY> <Service>`. Per-PE narrative + "Program Change Summary" funding table. Identifier: PE number (e.g., `0603287F`).
- **P-40 exhibits** — Procurement line items. Header: `Exhibit P-40, Budget Line Item Justification`. Identifier: P-1 Line Item Number (e.g., `B02100` for B-21 Raider). Funding row: `Net Procurement (P-1) ($ in Millions)`.

**Acquisition.** comptroller.war.gov hosts the Defense-Wide books (DARPA, MDA, SOCOM, OSD). Service-specific Air Force and Space Force books are on `saffm.hq.af.mil`, which is unreachable from the sandbox; we pull those via the Wayback Machine CDX API. As of the current corpus build:

| Source book | Programs ingested |
|---|---:|
| FY 2026 DARPA RDT&E Master Justification Book | 24 |
| FY 2026 MDA RDT&E Vol 2 | 31 |
| FY 2026 SOCOM RDT&E | 14 |
| FY 2026 OSD RDT&E | 2 |
| FY 2026 Air Force RDT&E Vol I–IV | 256 |
| FY 2026 Space Force RDT&E | 63 |
| FY 2026 AF Aircraft Procurement Vol I (P-40s) | 7 |
| FY 2026 AF Other Procurement (P-40s) | 1 |
| FY 2026 Procurement Defense-Wide Vol 1 | 2 |
| Hand-curated YSS/IONQ seed programs | 7 |
| **Total** | **407–410 deduped** |

**Parser** (`scripts/ingest_jbook.py`). For each page: detect exhibit header → extract PE number + title via combined regex → parse `Program Change Summary` text section to recover per-FY funding. P-40 pages branch into `_parse_p40_page`, which extracts the Line Item Number + title + `Net Procurement (P-1)` row.

**Narrative capture** (`scripts/extract_pe_narratives.py`). The page-1 ingest captures only ~400 chars of boilerplate per PE. To extract contractor names, we re-open the source PDF for each PE, walk pages from the PE's first page until the next PE starts, concatenate text, and store as `narrative_text`.

**Contractor backfill** (`scripts/backfill_contractors.py`). For each PE with empty `primary_contractors`, send the narrative to Claude Haiku with a strict extraction schema. Output: `primary_contractors[]`, `other_named_parties[]` (with role: subcontractor / performer / university / etc.), confidence, and a verbatim evidence quote. LLM correctly returns `confidence: none` when text is boilerplate-only.

**Entity inversion** (`scripts/build_jbook_entity_index.py`). Reads `programs.json` and inverts it to `by_entity.json`: each normalized contractor name → list of programs they appear on. Filters out non-commercial entities (federal labs, universities, generic "small businesses", etc.) so the index only contains ticker-mappable names.

**Status derivation.** Each program's `funding_history` (FY → funded_M) drives the status enum via `pentagon_jbook._latest_funding_status`:

| Trajectory | Status |
|---|---|
| Most recent FY $0, consecutive prior FY $0 | `UNFUNDED_TWO_PLUS_YEARS` |
| Most recent FY $0, prior FY > 0 | `UNFUNDED_THIS_YEAR` |
| FY explicitly killed in narrative | `TERMINATED` |
| Recent < 85% of prior funded year | `FUNDED_SHRINKING` |
| Recent > 115% of prior funded year | `FUNDED_GROWING` |
| Otherwise, with at least one funded year | `FUNDED_STEADY` |
| No matching program | `NOT_FOUND` |
| Cutoff filter strips all years | `NOT_FOUND_IN_TIMERANGE` |

### 3.2 DOE Office of Science corpus

DOE budget documents are *narrative* chapters per program area (ASCR, BES, BER, FES, HEP, NP) with embedded funding tables — not standardized R-2 exhibits. Regex parsing fails; we use direct LLM extraction (`scripts/ingest_doe_budget.py`):

1. Walk the PDF in 10-page chunks (`scripts/ingest_doe_budget.py:chunk_pdf`).
2. Send each chunk to Claude Haiku with a schema that asks for: `program_name`, `parent_office`, `fy_funding{FY2024, FY2025, FY2026}`, named subprograms, named commercial contractors, `qis_relevant` boolean, and a verbatim evidence quote.
3. Discard entries without explicit funding numbers (no fabrication).
4. Merge into `data/_doe_data/programs.json` with the same shape `pentagon_jbook` expects, so status derivation works identically.

Current DOE corpus: **78 programs, 18 QIS-relevant**, from `FY-2026-Office-of-Science-Budget-Request.pdf`. NNSA / ARPA-E / EERE volumes not yet ingested.

### 3.3 Ticker entity resolution

Companies don't appear in J-Books under their NYSE ticker name. They appear as their federal-contracting subsidiary (e.g., `IonQ Federal, LLC`, `Rocket Lab National Security LLC`, `BigBear.ai Federal, LLC`, `iRobot Federal LLC`) or as recent acquisitions whose pre-rebrand names still appear on legacy contracts (`Capella Space`, `Oxford Ionics`, `SolAero Technologies`, `Made In Space`, `Pangiam`).

**Exhibit 21 fetcher** (`scripts/edgar_exhibit_21.py`). For a given CIK: pull latest 10-K from EDGAR submissions JSON → find Exhibit 21 attachment (regex over filing-index documents) → fetch + parse. The parser tries two strategies in order:

1. **HTML-table parse** (BeautifulSoup) — walk every `<tr>` / `<td>`; cell-0 is name, find a US-state / country jurisdiction token in the remaining cells. Reliable for filers using HTML-table formatting.
2. **Text fall-back** — regex `Name <suffix> <Jurisdiction>` across the flattened text. Catches filers who render Exhibit 21 as a single paragraph.

**LLM synthesis** (`scripts/resolve_ticker_entities.py`). Send the Exhibit 21 subsidiary list to Claude Haiku with a schema that asks for a flat `name_variants[]` list, each tagged with type (`registered_name`, `short_form`, `federal_subsidiary`, `acquisition`, `domestic_operating_subsidiary`, `historical_parent`, `product_line`) and confidence. Foreign-only subs and acquisition holding shells are excluded.

Outputs across the 22-ticker universe: **130+ resolved name variants**, including the federal-contracting LLCs and recent-acquisition names that USAspending and J-Book matching require.

### 3.4 USAspending PE crosswalk

USAspending's public API doesn't expose PE numbers on contract awards (Treasury Account / Program Activity / Federal Account fields are consistently `None` for DoD contracts). The PE link is recoverable from contract metadata — PIID prefix, awarding office, contract description, NAICS, PSC, solicitation ID — but only via LLM-mediated matching, not a clean lookup.

The crosswalk (`scripts/usaspending_pe_crosswalk.py`) does this per ticker:

1. Fetch every DoD contract under every resolved name variant (with retry-on-transient).
2. Take the top 25 contracts by obligated $.
3. For each, send `{PIID, description, awarding/funding office, NAICS, PSC, amount}` + a compact corpus summary to Claude Haiku, asking which PE in the corpus it's most likely funded under, or `no_match`.
4. The prompt explicitly warns against DARPA-umbrella PEs as a "good-enough" fallback for contracts awarded by AFRL / SDA / Navy / Space Force — those need agency-specific matches or `no_match`.
5. Bucket by matched PE; aggregate obligated $ per bucket.

The crosswalk's value is **orthogonal evidence**: when a subagent's R-side claim says "Program X is material to FY 2025 revenue," the crosswalk can confirm the company actually received contracts attributable to Program X.

Honest limit: the LLM still has to text-match, so noise is real (we saw the LLM force IONQ-Qubitekk into the Rigetti row in one early run because Rigetti has no PE of its own in the corpus). Conservative tuning of the prompt (`no_match` over forced match) is the mitigation.

---

## 4. Run phase

### 4.1 Cohort

`jbook_exposure_cohort.py` defines:
- **`COHORT`** — 13 `CohortMember(ticker, cik, name, notes)` tuples. The `notes` field is hand-curated *factual* metadata about the company; it does **not** name outcomes, short-report sponsors, or post-cutoff events.
- **`COHORT_CONTEXT`** — the framing string the subagent sees. Describes the YSS/IONQ pattern abstractly without naming specific tickers, and enumerates the available M-sources.
- **`COMMON_COUNTERPARTY_CIKS`** — Lockheed, Northrop, Raytheon, L3Harris, GD, Boeing, Honeywell. For counterparty-disclosure verification via `edgar_fts.query_fulltext`.
- **`CUTOFF`** — ISO date. All M-source calls accept `cutoff_date=` and filter to FYs ≤ that year for historical backtests.

### 4.2 Subagent architecture

Each ticker is analyzed by an **isolated, blinded Claude Code subagent** with no shared context. The subagent prompt (`jbook_exposure_subagent_prompt.build_prompt(ticker)`) is ~11,500 chars and contains:

1. **Strict blinding discipline** (no WebSearch / WebFetch, no training-data hindsight, file-exclusion list).
2. **Assignment** (ticker, CIK, company name, factual notes, cutoff, filing paths).
3. **Cohort context** (the abstract pattern, no outcome-leaking specifics).
4. **Resource pointers** (M-source catalog path, filing slicer, corpus paths, entity-resolution + crosswalk artifacts).
5. **Workflow** — pick filing → slice → extract claims → pick M-sources → run queries with two-checkpoint write discipline → score.
6. **Extract rubric** — focus on J-Book-grounded language (PE numbers, named programs, IDIQ ceilings, multi-year program-of-record narratives).
7. **Score rubric** with explicit severity-to-J-Book-status mapping:

```
FUNDED_GROWING / FUNDED_STEADY    → PASS
FUNDED_SHRINKING                  → MODERATE_UNDERDELIVERY
UNFUNDED_THIS_YEAR                → SEVERE_UNDERDELIVERY
UNFUNDED_TWO_PLUS_YEARS           → RED_FLAG_NEGATIVE
TERMINATED                        → RED_FLAG_NEGATIVE
NOT_FOUND                         → UNVERIFIABLE
```

8. **J-Book calibration heuristics** — materiality test (prime vs sub vs prospect), reorganization caveat (DARPA FY26 consolidation), PE name ambiguity, earmark sub-signal (pair with `earmark_detector`), USAspending cross-check, NOT_FOUND-isn't-RED, procurement vs RDT&E distinction.

### 4.3 Blinding discipline

The forward test is only meaningful if the subagent isn't peeking. Concrete measures:

- **No WebSearch / WebFetch.** The subagent's tool set is the M-source catalog + filing reads + local artifacts. It can't see post-cutoff news.
- **No file access to outcomes.** Explicit exclusion list: `*.hindsight.json`, `*.preslicer.json`, `_<cohort>_outcomes.py`, any short-report case-study PDFs.
- **Training-data hindsight discipline.** The prompt's STRICT BLINDING DISCIPLINE block tells the subagent: "If you find yourself reasoning *I know X happened after cutoff*, STOP." We trust the subagent's reasoning self-discipline rather than mechanical filters — failure modes are visible in scored interpretations.
- **Outcome-stripped metadata.** The `notes` field for each `CohortMember` describes *what the company does*, not what subsequently happened to it. We caught and fixed two leaks during build: the IONQ note originally said "subject of Wolfpack short report" (removed); the `COHORT_CONTEXT` originally named YSS and IONQ as canonical examples (removed, generic phrasing now).
- **Isolation.** 13 subagents run in parallel without shared scratch state. Each writes its own `.jbook.input.json` + `.jbook.scores.json`.
- **Two-checkpoint discipline.** Subagent writes `input.json` after extraction (before any M-source queries) and re-writes `scores.json` after *every* claim is scored (not at the end). If the subagent crashes mid-run (we saw one socket-level API failure across the 16+1 subagent runs), partial state is preserved and the re-launch can be a continuation rather than full restart.

### 4.4 Scoring + aggregation

`jbook_exposure_aggregate.py` reads each `<TICKER>.jbook.{input,scores}.json` and produces:

**Severity counts** (`PASS`, `MODERATE_UNDERDELIVERY`, `SEVERE_UNDERDELIVERY`, `RED_FLAG_NEGATIVE`, `UNVERIFIABLE`).

**Composite score** = weighted-mean severity per *non-UNVERIFIABLE* claim, with weights `PASS=0, MODERATE=1, SEVERE=2, RED=3`. UNVERIFIABLE is excluded so coverage gaps don't dilute the signal.

**J-Book hit count** — how many scored claims actually used `pentagon_jbook` (or `jbook` in M-check). A high hit count means the cohort matched the framework's intent; a low hit count means the corpus didn't cover the claims.

Output: `_jbook_exposure_cohort/PREDICTIONS.md` (composite ranking table + per-ticker forward predictions with RED / SEVERE / MODERATE claim details) and `matrix.json` (machine-readable).

---

## 5. Backtesting + A/B hooks

The broader `public_co` framework (`ARCHITECTURE.md`) supports running the same pipeline as either:
- **Forward test** — current ticker, current cutoff, outcome is unknown.
- **Backtest** — historical ticker, historical cutoff, outcome was revealed *after* the cutoff and is held in `_<cohort>_outcomes.py` (never passed into any LLM prompt).

The blinded scoring writes `<ticker>.scores.json` independent of outcome. The outcome is joined in only at matrix-build time to produce a confusion matrix (true positives = SEVERE/RED scores on revealed-bad outcomes; false positives = SEVERE/RED scores on revealed-clean outcomes).

A/B mechanism for methodology changes:
- After a successful run, copy `<ticker>.scores.json` to `<ticker>.preslicer.json` (the "before" snapshot).
- Change one variable (a slicer parameter, a calibration heuristic, the M-source catalog).
- Re-run, producing a new `<ticker>.scores.json`.
- Compare confusion matrices between the two scoring sets. The known outcome labels enable measuring whether the change improved discrimination or was artifact.

The `.hindsight.json` artifact is the same scoring run done *without* blinding (outcome label visible during scoring). Difference between hindsight and blinded scores quantifies how much the framework leaves on the table from being honest.

For the J-Book exposure cohort, the cutoff is current (`2026-05-20`), so we're in forward-test mode. Backtest validation would require re-running against a historical cutoff (e.g., `2024-01-01` to test whether the framework would have caught the IONQ AFRL Quantum Networking de-funding before it became public knowledge).

---

## 6. Prompts (verbatim)

### 6.1 Subagent prompt template

Located in `jbook_exposure_subagent_prompt.PROMPT_TEMPLATE`. Full text (with `{placeholders}` filled per ticker by `build_prompt`):

```
You are a forensic-disclosure analyst running a BLINDED forward test of
the Signal OS framework on a single company. Your focus for this cohort
is the J-BOOK EXPOSURE DIVERGENCE PATTERN: the company names specific
Pentagon programs as material revenue contributors while the Pentagon's
forward J-Book shows those programs going unfunded or shrinking.

== STRICT BLINDING DISCIPLINE ==
- Do NOT use WebSearch, WebFetch, or any tool that could surface
  post-cutoff information about this company
- Do NOT use prior training-data knowledge of any post-cutoff events
- Do NOT browse files matching `*.hindsight.json`, `*.preslicer.json`,
  `_<cohort>_outcomes.py`, or short-report case-study files
- If you find yourself reasoning "I know X happened after cutoff", STOP.

== ASSIGNMENT == { ticker / cik / company_name / notes / cutoff /
                    filing paths / output paths }

== COHORT CONTEXT == { generic pattern description, M-source guide }

== RESOURCES == { catalog path, corpus paths, entity resolution + crosswalk
                  artifacts, counterparty CIKs }

== WORKFLOW ==
1. Read filings index. Pick most substantive pre-cutoff filing.
2. Slice to 120K chars via filing_slice.slice_filing.
3. Extract 4-10 J-Book-grounded claims + 2-3 control claims.
4. Pick M-source queries per claim. pentagon_jbook is PRIMARY for
   J-Book-grounded claims; pair with usaspending; consider
   earmark_detector / insider_vs_calendar / acq_coherence.
5. CHECKPOINT 1: write input.json before queries.
6. Run queries claim-by-claim, sleeping 1-2s between calls.
7. SCORE per J-BOOK CALIBRATION HEURISTICS. CHECKPOINT 2: re-write
   scores.json after each claim. Never batch-save.
8. Final message: one line with severity counts + J-Book hit count.

== EXTRACT RUBRIC ==
HIGH discriminative claims (J-Book pattern):
- Names a specific DoD program / PE number / line-item lookup-able in pentagon_jbook
- Quantifies revenue or contract value attributed to that program
- Asserts a forward expectation tied to that program

== SCORE RUBRIC ==
Severity: PASS / MODERATE_UNDERDELIVERY / SEVERE_UNDERDELIVERY /
          RED_FLAG_NEGATIVE / UNVERIFIABLE.

== J-BOOK CALIBRATION HEURISTICS ==
1. pentagon_jbook signal → severity mapping (see Section 4.2)
2. Materiality test (prime / sub / prospect)
3. Reorganization caveat (DARPA FY26 umbrella consolidations)
4. PE name ambiguity (multiple-candidate-PE handling)
5. Earmark sub-signal (pair with earmark_detector)
6. USAspending cross-check (contract reality vs claim)
7. NOT_FOUND ≠ red flag (corpus coverage gap)
8. Procurement (P-40) vs RDT&E (R-2) distinction

== OUTPUT FORMATS ==
input.json:  {ticker, cutoff, filing, claims[]}
scores.json: {ticker, scores[]}
```

### 6.2 DOE re-pass addendum

Appended to the v1 prompt for IONQ / RGTI / QBTS / QUBT re-runs after `doe_budget` was added to the catalog. Verbatim:

```
== ADDENDUM: DOE M-SOURCE NOW AVAILABLE ==
A new M-source, doe_budget.query_program_funding, has been added since
this ticker's first pass. It mirrors pentagon_jbook but for DOE Office
of Science programs (ASCR, BES, BER, FES, HEP, NP and their
subprograms). Corpus = 78 DOE programs, 18 QIS-relevant.

FOR THIS RE-PASS: when the company names a DOE program, NQI Center,
or national-lab partnership (Argonne Q-NEXT, Brookhaven C2QA, LBNL,
ORNL, Fermilab, PNNL, Sandia, Los Alamos), use BOTH:
  - pentagon_jbook.query_program_funding(...)
  - doe_budget.query_program_funding(program_name=..., qis_only=True)

A first pass that returned NOT_FOUND from pentagon_jbook on a DOE claim
should now be retried against doe_budget — independent funding lines.

OVERWRITE the existing .input.json and .scores.json with v2 results.
v1 copies are at .v1.input.json / .v1.scores.json.

Focus extra effort on the claims that previously came back UNVERIFIABLE.
PASS claims from v1 don't need re-verification.
```

### 6.3 Backfill extractor system prompt

Located in `scripts/backfill_contractors.py:_SYSTEM`. Extracts named prime contractors from per-PE narrative text. Conservative — returns empty `primary_contractors` and `confidence: none` when text doesn't support extraction (catches the boilerplate-only DARPA PE case).

### 6.4 DOE budget extractor system prompt

Located in `scripts/ingest_doe_budget.py:_SYSTEM`. Schema: program_name, parent_office, doe_program_code, fy_funding{FY2024, FY2025, FY2026}, subprograms, named_contractors, qis_relevant, narrative_snippet, evidence_quote.

---

## 7. M-source catalog (J-Book-relevant subset)

The full catalog is in `m_source_catalog.py`; 32 sources total. The J-Book-relevant subset:

- **`pentagon_jbook.query_program_funding`** — forward DoD funding by program_name / pe_number / contractor_name. Returns matched_programs[] + primary_status + signal enum. Corpus: 410 programs.
- **`doe_budget.query_program_funding`** — same shape, DOE Office of Science programs. Corpus: 78 programs.
- **`usaspending.query_dod_contracts`** — rear-view DoD contracts under a recipient name. Orthogonal evidence layer.
- **`usaspending.query_recipient_contracts`** — same but agency-agnostic (DOE, NASA, VA, …).
- **`edgar_fts.query_fulltext`** — full-text search over EDGAR filings, scopeable to a counterparty CIK. Tests "does the counterparty disclose us?"
- **`earmark_detector.query_earmark_status`** — was an unfunded program a congressional add whose sponsor lost power? Bumps severity when paired with `pentagon_jbook` UNFUNDED_*.
- **`insider_vs_calendar.query_insider_sales_near_budget_events`** — Form 4 insider sales within ±14 days of named budget-vote dates. Discretionary-sale clustering = SEVERE; 10b5-1 plan = PASS.
- **`acq_coherence.score_acquisition_coherence`** — LLM-scored technology coherence of acquisitions vs parent thesis. Detects "rollup distraction" pattern when PE losses force pivots.

Subagent picks 1-3 of these per claim from the catalog based on its descriptions.

---

## 8. Outputs

### Per-ticker

`data/_local/<TICKER>.jbook.input.json`:
```
{
  "ticker": "IONQ", "cutoff": "2026-05-20", "filing": "<accession>_10-K.txt",
  "claims": [
    {
      "claim_id": "C1",
      "claim_text": "...",
      "subject": "...", "predicate": "...", "object_value": "...",
      "source_quote": "...",
      "category": "jbook_program_revenue | jbook_program_pipeline | dod_customer_concentration | patent | counterparty_disclosure | facility | rollup_thesis | other",
      "queries": [{"source": "pentagon_jbook.query_program_funding", "params": {...}}, ...]
    }, ...
  ]
}
```

`data/_local/<TICKER>.jbook.scores.json`:
```
{
  "ticker": "IONQ",
  "scores": [
    {
      "claim_id": "C1", "claim_text": "...",
      "severity": "RED_FLAG_NEGATIVE",
      "supports": [...], "M_check": "pentagon_jbook.query_program_funding(...)",
      "M_value": "UNFUNDED_TWO_PLUS_YEARS — FY24=$12M, FY25=$0, FY26=$0",
      "interpretation": "Canonical J-Book divergence. ..."
    }, ...
  ]
}
```

### Cohort-level

`data/_jbook_exposure_cohort/PREDICTIONS.md` — human-readable forward predictions. Composite ranking table + per-ticker RED / SEVERE / MODERATE claim details.

`data/_jbook_exposure_cohort/matrix.json` — machine-readable equivalent for downstream tooling (confusion-matrix builders, A/B comparisons).

---

## 9. Honest limitations

- **Corpus coverage gaps.** 410 Pentagon PEs is broad but not exhaustive — Navy RDT&E and Army RDT&E aren't ingested; service-specific procurement books are partial (AF Vol I + Other; Vol II was a corrupted download). DOE coverage is Office of Science only — NNSA / ARPA-E / EERE not yet ingested. NOT_FOUND outcomes can therefore reflect either a real absence-of-program (signal) *or* a coverage gap (noise). The framework treats NOT_FOUND as UNVERIFIABLE for this reason.
- **LLM matching noise.** Both the contractor-backfill pass and the USAspending crosswalk depend on Haiku correctly disambiguating program names. We tightened prompts after observing an early failure mode where the LLM defaulted to DARPA-umbrella PEs as a "good-enough" fallback. False matches remain possible.
- **Subagent calibration variance.** The same prompt run on the same ticker can produce different claim counts and severity scores across runs. Two-checkpoint discipline preserves partial work but doesn't eliminate stochasticity. A/B mechanism is the disciplined response.
- **Procurement-side blind spot for small caps.** Companies like KTOS / AIRO / RCAT earn the majority of revenue from procurement subcontracts that don't surface at the P-1 line-item level (they sell components into bigger primes' lines). The crosswalk catches them as past obligations; the J-Book reads them as the prime's responsibility, not theirs.
- **Reorganization artifacts.** DARPA's FY26 consolidation produced several PEs that show `UNFUNDED_TWO_PLUS_YEARS` not because the work was killed but because it was folded into a new umbrella PE (`EMERGING OPPORTUNITIES`, `ACCESS AND AWARENESS`). Calibration heuristic 3 flags this; subagents are instructed to downgrade severity when a `replacement_program` field exists.
- **Forward test only — no historical validation yet.** The current cohort is forward-looking; we have no labeled outcomes to confusion-matrix against. Backtest validation against a 2024 cutoff is the natural next step.

---

## 10. File layout summary

```
verticals/public_co/
├── JBOOK_EXPOSURE_METHODOLOGY.md          ← this doc
├── ARCHITECTURE.md                         ← framework-wide doc
├── jbook_exposure_cohort.py                ← cohort definition (13 tickers)
├── jbook_exposure_subagent_prompt.py       ← subagent prompt template
├── jbook_exposure_aggregate.py             ← rollup → PREDICTIONS.md
├── m_source_catalog.py                     ← 32 M-sources registered
├── m_sources/
│   ├── pentagon_jbook.py                   ← forward DoD funding
│   ├── doe_budget.py                       ← forward DOE funding
│   ├── usaspending.py                      ← rear-view contracts
│   ├── earmark_detector.py
│   ├── insider_vs_calendar.py
│   └── acq_coherence.py
├── scripts/
│   ├── ingest_jbook.py                     ← R-2 / P-40 parser
│   ├── extract_pe_narratives.py            ← full per-PE narrative capture
│   ├── backfill_contractors.py             ← LLM contractor extraction
│   ├── build_jbook_entity_index.py         ← PE-keyed → entity-keyed
│   ├── ingest_doe_budget.py                ← LLM-driven DOE extractor
│   ├── edgar_exhibit_21.py                 ← 10-K Exhibit 21 fetcher
│   ├── resolve_ticker_entities.py          ← LLM name-variant synthesis
│   ├── usaspending_pe_crosswalk.py         ← contract → PE LLM matcher
│   └── enrich_crosswalk_status.py          ← derive PE statuses post-hoc
└── data/
    ├── _jbook_data/                        ← 410 Pentagon programs + entity index
    ├── _doe_data/                          ← 78 DOE programs
    ├── _entity_resolution/                 ← ticker → name variants + crosswalk
    ├── _local/                             ← per-ticker input.json + scores.json
    ├── _jbook_exposure_cohort/             ← forward-test outputs (PREDICTIONS.md, matrix.json)
    └── _jbook_exposure_cohort_2024/        ← backtest outputs + return artifacts
```

---

## 11. Backtest verdicts

The framework was tested as a directional return signal across multiple structures using the 12-ticker cohort, a 10-ticker Phase 2 expansion, and three vintage-cutoff runs (2022-06-01, 2024-09-01, 2026-05-20). Each variant produced a distinct verdict.

| Strategy | Structure | Per-cycle return | Win rate | Verdict |
|---|---|---:|---:|---|
| Naked short divergent | Hold Sep 2024 → May 2026 | **-780%** to -1,167% | — | **Fails.** Caught the small-cap defense/quantum bull rally. Sector beta crushed the signal. |
| Pre-PB short basket | Short T-60 → T+45 around each PB | -16% / event | 19% (3/16) | **Fails.** Enters into the PB-rally upswing; wrong direction. |
| Post-peak short basket | Short PB+120 → next PB | +13% / trade | 89% (8/9) | **Marginally works** for divergent shorts but single-name squeeze risk (ARQQ FY25 -235%) dominates the mean. |
| Long J-Book-clean basket | Long PB-60 → next PB | +181% / event | 91% (27/30) | **Works**, but contaminated by sector beta. |
| **L/S pair (long clean / short divergent)** | Long ≤0.20 + short ≥0.50, both T-60 → next PB | **+146% / event** | **100% (3/3 events)** | **Validated alpha.** Strips sector beta; pair return is pure cross-sectional framework alpha. |

### What we learned about timing

1. **PB submission ignites a multi-month sector hype rally.** The framework's bearish signal is wrong-direction in the immediate post-PB window (-60 to +120 days). Sector beta dominates.
2. **The rally peaks ~120 days after PB submission**, then drawdowns run to the next PB cycle. Within that drawdown, the framework's composite predicts depth (r = -0.68 with peak-to-trough drawdown over n=22 names).
3. **Pre-PB entry (T-60) on the LONG side captures the entire rally + the next cycle's drawdown protection.** Pre-PB entry on the SHORT side captures the wrong half.
4. **The PB release isn't a stock-specific catalyst — it's a sector-wide repricing event.** Both clean and divergent names react. The framework's value is in predicting the **spread** between them, not the direction of either.

### What we learned about the signal itself

- **The composite is timing-honest.** At 2022 cutoff, 6 of 7 marquee names returned 0.00 composite (the J-Book de-fundings that materialized in 2024-2026 weren't yet visible). The framework correctly didn't backfill signals.
- **ARQQ is the only name with material 2022-vintage signal (0.60)** — and the only marquee name with a catastrophic 4-year outcome (-97% / -99% drawdown). The framework caught it at the earliest the data could support.
- **Vintage compositing is required for honest backtests.** Using 2024 composites to backtest 2022 trades is hindsight contamination.
- **Composite is a stronger drawdown predictor than total-return predictor.** r = -0.68 (drawdown) vs r = -0.14 (total return) at n=22. In a sector bull regime, even divergent names go up — but they drawdown harder when sentiment reverses.

---

## 12. Validated alpha structure

### The strategy

```
L/S pair trade, anchored to the Pentagon President's Budget release calendar

For each PB cycle (released ~Feb-Jun, sometimes delayed):

  Entry date:    PB release - 60 calendar days (~Jan or Apr depending on cycle)
  Exit date:     Next PB release date (12-17 months later)
  Long basket:   tickers with composite ≤ 0.20 at the most recent
                 framework cutoff available BEFORE entry
  Short basket:  tickers with composite ≥ 0.50 at the same vintage
  Equal-dollar  weight per position on each leg
```

### Performance (backtested across FY24, FY25, FY26 PB cycles)

| Cycle | Entry | Exit | n long | n short | Long ret | Short P&L | **Pair return** | Alpha vs ITA |
|---|---|---|---:|---:|---:|---:|---:|---:|
| FY24 → FY25 | Jan 2023 | Mar 2024 | 6 | 1 | +75% | +70% | **+146%** | +130% |
| FY25 → FY26 | Jan 2024 | Jun 2025 | 6 | 1 | +272% | -158% | **+114%** | +65% |
| FY26 → FY27 | Apr 2025 | Apr 2026 | 8 | 7 | +243% | -66% | **+177%** | +132% |
| **Pooled** | | | | | **+197%** | **-51%** | **+146%** | **+109%** |

3 of 3 cycles produced positive pair returns. Mean alpha vs ITA: ~+109 points per cycle (each cycle ~12-17 months, so roughly 80-95% annualized excess vs the defense ETF).

### Why this beats the long-only variant

The long-only "Buy clean basket, hold to next PB" returned +181% per cycle. Critics could argue: "you bought defense small-caps during the strongest defense bull regime; the framework is incidental."

The pair trade addresses this. By shorting an equal-dollar basket of high-composite names in the *same sub-sector*, sector beta cancels out. The +146% pair return is the framework's cross-sectional stock-picking alpha — choosing the right defense names rather than just owning defense.

### Position sizing within the basket

- **Equal-weight** is the baseline (every name gets 1/N per leg).
- **Composite-weighted** is an alternative — name's weight ∝ (composite − threshold). Backtest results are similar.
- **Single-name caps** matter: the FY25 ARQQ short alone produced -158% short P&L. A 25-50% per-name cap would have softened that without hurting the FY26 cycle (broader basket).

### Caveats

- **n = 3 events.** Need more PB cycles before this is statistically defensible. The next test point is FY27 → FY28 (this section's forward test).
- **2022-2025 was a strong defense bull regime.** Pair structure should be more robust than long-only here — the alpha is cross-sectional, not directional — but absolute returns will scale with sector volatility.
- **Single-name short risk is real.** ARQQ FY25 +235% rally cost the FY25 short leg -158%. Diversified shorts (FY26 cycle, n=7) had cleaner returns. Don't run the pair with n<3 on either side.
- **Borrow cost on small-cap divergent names can be 15-50% APR.** Over a 14-month hold, borrow drag is 15-60 points. The +146% pre-borrow alpha leaves ample room, but realistic net returns are 80-130%.
- **Vintage discipline is non-negotiable.** Using forward composites on historical entries is hindsight; the framework must be re-run at each historical cutoff for honest backtests.

---

## 13. Forward test (FY27 → FY28 PB cycle)

### Setup

- **Current PB cycle**: FY27 PB was released 2026-04-28.
- **Next PB**: FY28 PB expected ~Mar 2027 (President's Budget conventional timing; could be Feb-Jun).
- **Canonical entry** (T-60 before FY28 PB): ~Jan 2027.
- **Earliest reasonable entry** (today): 2026-05-20 — already inside the cycle by ~22 days post-FY27 PB.
- **Exit**: FY28 PB release date when it materializes.

Two valid entry timings to log:

1. **Canonical (T-60)** — Jan 2027. Most consistent with the validated structure.
2. **Early (today)** — May 2026. Live-tracks the framework's prediction across the full cycle for richer evidence.

### Live position prescription (using composites from most recent framework cutoff)

See the artifact at `data/_jbook_exposure_cohort_2024/forward_test_FY27_FY28.json` for the per-ticker prescriptions, entry-window dates, and the rationale for each long/short selection.

### What we're predicting

If the validated alpha structure holds in the FY27 → FY28 cycle, the L/S pair will produce a positive return between the entry date and FY28 PB release, with the long basket outperforming the short basket. The most defensible read will be the pair (long − short) excluding ITA / SPY beta exposure.

If the pair return is materially negative, that's evidence the framework's alpha is not robust to different macro regimes (e.g., a defense drawdown, an AI/quantum hype unwind, or a different administration's budget priorities). Either outcome is valuable.
