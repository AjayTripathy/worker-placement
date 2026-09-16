# Public-Co Vertical — Architecture

*Public-company SEC-filing forensic divergence screen for the Signal OS framework. Same pipeline runs forward (current ticker) and as a backtest (historical ticker, known outcome). Companion to top-level `signalos/ARCHITECTURE.md` — this doc covers public-co-vertical-specific machinery; cross-vertical operational discipline lives there.*

---

## What this vertical does

Takes a cohort of public companies with known cutoff dates and (for validation) known outcomes, runs the Signal OS framework against each company's pre-cutoff SEC filings, and produces:

1. **Per-company analysis JSON** with extracted claims (R), M-source queries run, evidence retrieved, and severity scores
2. **Cohort-level confusion matrix** comparing severity ranking to revealed outcomes at multiple thresholds
3. **A/B comparison artifacts** (`.hindsight.json` vs `.preslicer.json` vs current) for tracking how methodology changes affect signal

Used for two things:
- **Forward tests:** "does the framework catch known-bad-outcome companies BEFORE the bad event, and clear known-clean ones?"
- **Methodology validation:** "does change X to the slicer / recipe library / calibration heuristics actually improve discrimination, or is it artifact?"

---

## File layout

```
verticals/public_co/
├── ARCHITECTURE.md                  ← this doc
├── EVTOL_FORWARD_TEST.md            ← cohort case study (eVTOL)
├── __init__.py
├── edgar.py                         ← SEC EDGAR puller (CIK → filings)
├── filing_slice.py                  ← HTML strip + section detection + budget allocation
├── m_source_catalog.py              ← LLM-facing catalog of M-sources with descriptions
├── m_recipes.py                     ← Analyst-curated recipe library (claim-shape → query template)
├── m_sources/                       ← One module per M-source (uspto_odp, edgar_fts, epa_frs, ...)
│   ├── uspto_odp.py                 ← USPTO ODP patent connector (preferred over google_patents)
│   ├── edgar_fts.py
│   ├── epa_frs.py
│   ├── nhtsa.py
│   ├── nrel_fuel.py
│   ├── google_patents.py            ← deprecated; rate-limits aggressively
│   ├── clinical_trials.py
│   ├── openfda.py
│   └── fmcsa.py
├── analysis_types.py                ← Shared dataclass contract (Claim, MQuery, Evidence, Finding, CompanyAnalysis)
├── providers.py                     ← Provider protocol + LocalProvider + ApiProvider
├── llm_pipeline.py                  ← API-driven pipeline (extract / pick / score via Claude)
├── unified_runner.py                ← Provider-agnostic runner (analyze_company)
├── scoring.py                       ← Severity enum + weights
├── evtol_cohort.py                  ← eVTOL cohort definition (no outcomes in tuple)
├── _evtol_outcomes.py               ← eVTOL outcomes (revealed at matrix time)
├── threedp_cohort.py                ← 3D printing cohort definition
├── _threedp_outcomes.py             ← 3D printing outcomes
└── data/
    ├── <ticker>/                    ← per-company filings + filings_index.json
    ├── _local/                      ← LocalProvider scratch (input/scores/evidence JSONs)
    ├── _evtol_cohort/               ← per-company analysis output
    └── _threedp_cohort/             ← per-company analysis output
```

---

## Pipeline stages

Maps onto Layer 1 of the top-level ARCHITECTURE.md. In code:

```
filings_index.json
        │
        ▼
   pick_filing()                          ← evtol_cohort.py
        │
        ▼
   slice_filing()                         ← filing_slice.py
        │
        ▼
   provider.extract_and_pick()            ← providers.py
        │  ├── claims (R)
        │  └── queries_per_claim (M targets)
        │
        ▼
   run_queries() → m_source_catalog.call() ← unified_runner.py
        │  └── evidence_per_claim
        │
        ▼
   provider.score()                       ← providers.py
        │  └── findings_by_claim (f outputs)
        │
        ▼
   CompanyAnalysis (saved to data/_<cohort>_cohort/<ticker>.<provider>.json)
```

---

## The Provider pattern

Two implementations of the same interface, swappable at runtime via `--provider {local|api}`:

### `LocalProvider`
Reads pre-written JSON files from `data/_local/`. Used when:
- API credits are constrained
- Subagent firewall is in use (subagents write input.json + scores.json; LocalProvider reads them)
- The analyst is hand-curating claims for a specific cohort

Files:
- `<ticker>.input.json` — claims + queries (written by analyst or subagent)
- `<ticker>.scores.json` — severities (written by analyst or subagent)
- `<ticker>.evidence.json` — evidence retrieved by `stage_extract_only` (intermediate)

**Important bug history:** `LocalProvider.score()` originally matched scores entries across all `*.scores.json` files using claim_id as the key. When two tickers used the same claim_id pattern (e.g. both used "C-001" through "C-008"), it would return the wrong ticker's score. Fixed by stashing `_current_ticker` in `extract_and_pick()` and using it to target the right scores.json directly. The fallback path (text-disambiguation by first 60 chars of claim_text) still exists but is unreliable because LLMs paraphrase between input.json and scores.json.

### `ApiProvider`
Calls Claude via the Anthropic SDK (key from `~/.anthropic_api_key`). Wraps `llm_pipeline.py` functions. Each Claude call is parameterized by the prompts in `llm_pipeline.py` (EXTRACT_SYSTEM, PICK_SYSTEM_TEMPLATE, SCORE_SYSTEM), all of which carry the BLINDING preamble.

**Outcome leakage prevention:** the `outcome` field on `CompanyAnalysis` is never passed into any LLM prompt. The model sees ticker + cutoff_date + filing_text + (for scoring) claim + evidence — never the outcome label. Calibration heuristics in SCORE_SYSTEM tell the model to ignore any prior knowledge of post-cutoff events.

---

## Cohort module structure

Each cohort lives in two files:

**`<cohort>_cohort.py`** — runner module, contains:
- `COHORT` tuple list: `(ticker, cik, cutoff_date, region_hint, priority_forms)` — **no outcome labels**
- `COMMON_CIKS` dict of counterparty CIKs for hint injection
- `ensure_filings()`, `pick_filing()` helpers
- `confusion_matrix()` helper (takes outcomes dict explicitly)
- `main()` with `--provider {local|api}` and `--reveal-outcomes` flags

**`_<cohort>_outcomes.py`** — outcome labels:
- `OUTCOMES` dict mapping ticker → `(outcome_label, detail_string)`
- Read ONLY when `--reveal-outcomes` is passed
- Subagents producing `<ticker>.input.json` / `<ticker>.scores.json` files MUST never read this module

**Why split:** the cohort module gets shown to subagents (they need to know which filings to pull, what cutoff, etc.). The outcomes module is the firewall. Confusion matrix computation merges the two only at report time.

---

## M-source library

### Catalog (`m_source_catalog.py`)
LLM-facing dictionary of available query sources. Each entry has `description`, `params`, `good_for`, and a `fn` that's called via `call(source_name, kwargs)`. Catalog includes:

| Source | Use case | Notes |
|---|---|---|
| `uspto_odp.query_assignee` | Patent portfolios by assignee | **Preferred** patent source. Free key from data.uspto.gov, saved to `~/.uspto_api_key`. Multi-word names need quoted-phrase syntax. |
| `google_patents.query_assignee` | Patent portfolios | Deprecated — rate-limits aggressively. Fallback only. |
| `edgar_fts.query_fulltext` | Counterparty disclosure of issuer | Single-word search terms work best. Counterparty CIK restriction is the high-signal mode. |
| `epa_frs.query_facilities` | US industrial facility existence | Only EPA-regulated activities (chemical, paint, foundry, large emissions). Light assembly / R&D / offices NOT in registry. |
| `nhtsa.query_manufacturer` | Vehicle OEM registration | Ground motor vehicles only. Aircraft / charging networks / biotech NOT applicable. |
| `nrel_fuel.query_alt_fuel_stations` | DOE alt-fuel station counts | HY (hydrogen) or ELEC (charging) station network claims. |
| `clinical_trials.query_by_lead_sponsor` | Biotech clinical pipelines | ClinicalTrials.gov v2 API. |
| `openfda.query_approved_drugs` | FDA-approved pharma products | Drugs only — does NOT cover medical devices (510(k) submissions). |
| `fmcsa.safer_search` | Motor carrier registration | Interstate trucking only. |

### Recipe library (`m_recipes.py`)
Analyst-curated mapping of claim shapes to query templates with placeholder variables. The LLM's job in Stage 2 (Pick) is reduced to: match claim to recipe(s), fill in placeholders. Recipes:

- `production_vehicle_check` → NHTSA
- `factory_at_state` → EPA FRS
- `fueling_network_count` → NREL
- `named_counterparty_order` → EDGAR FTS with counterparty CIK
- `external_brand_validation` → EDGAR FTS broad
- `patent_portfolio_in_area` → USPTO ODP (with category buckets)
- `clinical_trial_program` → ClinicalTrials.gov
- `fda_approved_products` → openFDA

Each recipe has `applies_when` (plain English), `queries` (template), and `scoring_hints` (severity rubric).

### Adding a new M-source
1. Create `m_sources/<name>.py` with a function returning a dict
2. Register in `m_source_catalog.CATALOG` with description, params, good_for
3. (Optional) Add to relevant recipes in `m_recipes.py` if the source enables a new claim shape
4. Smoke-test: `python3 -c "from verticals.public_co.m_source_catalog import call; print(call('<name>.<fn>', {...}))"`

---

## Slicer (`filing_slice.py`)

Takes raw HTML filing text and produces a budget-limited slice (default 120K chars) of the discriminative sections, weighted by section type. Critical for keeping LLM context small while preserving signal density.

### Section patterns (case-insensitive, page-number-skip heuristic)
- **Business / company description** (weight 4.0): `ITEM 1. BUSINESS`, `BUSINESS OF COMPANY`, `COMPANYS BUSINESS`
- **Risk factors** (weight 2.5): `ITEM 1A. RISK FACTORS`
- **MD&A** (weight 1.5): `ITEM 7. MD&A`
- **Financial-statement notes** (added in slicer fix, weights 1.5–3.0):
  - `GOING CONCERN` (3.0) — auditor PCAOB flag
  - `COMMITMENTS CONTINGENCIES` (2.5) — vendor concessions, payment-in-stock, accrued obligations
  - `RELATED PARTY TRANS` (2.5) — insider loans, sponsor fees, off-market deals
  - `LIQUIDITY CAPITAL` (2.0) — runway math, near-term obligations
  - `SUBSEQUENT EVENTS` (1.5) — post-period material developments
  - `NOTES TO FINANCIALS` (1.5) — broad bucket
- **S-4 / DEFM14A**: `BACKGROUND OF MERGER`, `REASONS FOR MERGER`, `INFORMATION ABOUT`
- **S-1 / F-1**: `PROSPECTUS SUMMARY`, `OUR COMPANY`, `OUR MISSION`

### Why financial-statement notes were added (slicer fix history)
Original slicer dropped notes sections entirely. The SRFM-Palantir miss surfaced because Note 15 contained "Palantir has agreed to accept either cash or Common Stock as compensation for their services" and "settled $2.0 million in outstanding payables to Palantir through the issuance of 1,755,156 shares" — disclosures invisible to the LLM until the slicer was patched. After the fix:
- SRFM blinded score: 0.86 → 1.38 (added 2 RED_FLAG_NEGATIVE)
- LILM blinded score: 0.56 → 1.75 (added going-concern + stock-for-services REDs)
- EVTL blinded score: 0.38 → 0.88 (added CEO-personal-rescue-financing RED)

Cross-cohort impact: eVTOL confusion matrix went from P=100% R=67% (pre-fix) to P=100% R=100% Sp=100% (post-fix) at threshold 0.5/claim Loose definition.

### Known slicer limitations
- TOC false positives: `ITEM 1. BUSINESS` and `ITEM 2. PROPERTIES` sometimes match the table-of-contents entry rather than the real section header. Heuristic skips entries followed by 1–3-digit page numbers but doesn't catch all variants.
- Section detection requires reasonable HTML structure; cover-page-heavy filings (DEFM14A) need different priority order
- 120K char budget is a heuristic; larger context windows could afford more

---

## Subagent firewall pattern

Operational pattern (not implemented as code in this vertical). Used for blinded cohort scoring. See top-level ARCHITECTURE.md "Layer 3 — Operational discipline" §4 for the general pattern; this section documents the backtest-specific implementation.

### Per-ticker subagent prompt structure
Each subagent receives:
1. **Blinding discipline** — strict rules: no WebSearch / WebFetch, no prior-knowledge of post-cutoff events, no reading of `*.hindsight.json` / `*.preslicer.json` / case-study `.md` files
2. **Assignment** — ticker, CIK, cutoff date, filings dir path, output paths
3. **Cohort context** — one paragraph describing the deal type (post-deSPAC eVTOL OEM, foreign issuer, etc.) and which calibration heuristics apply
4. **Resources** — paths to recipe library, M-source catalog, filing slicer; common counterparty CIK list
5. **Workflow** — pick filing → slice → extract claims → pick queries → save input.json → run queries → score → save scores.json
6. **Extract rubric** — what to look for, what to skip
7. **Score rubric + calibration heuristics** — severity scale, the 7 calibration rules
8. **Output schema** — JSON shapes for input.json and scores.json

### Files written by subagent
- `data/_local/<ticker>.input.json`
- `data/_local/<ticker>.scores.json`

### Cohort runner consumption
- Main session runs `python3 -m verticals.public_co.<cohort>_cohort --provider local --reveal-outcomes`
- Runner uses `LocalProvider` to read the subagent-written files
- Runner pulls outcomes from `_<cohort>_outcomes.py` and computes confusion matrix
- Subagent never has access to outcomes module

### File preservation pattern
After methodology changes, before re-running the cohort, preserve existing files as `.hindsight.json` (for hindsight-vs-blinded comparison) or `.preslicer.json` (for pre-vs-post-improvement comparison). This lets the cohort matrix be recomputed across iterations without losing earlier scoring.

---

## Calibration heuristics

Live in two places:
1. `llm_pipeline.py:SCORE_SYSTEM` prompt — for `ApiProvider` runs
2. Subagent prompts — for `LocalProvider` runs via subagent firewall

Both copies should be kept in sync. Current heuristics:

1. **EPA FRS scope** — only EPA-regulated facilities; offices/R&D/light assembly EXPECTED absent
2. **Foreign-issuer ADR disclosure** — 0–2 EDGAR mentions = NORMAL practice for foreign private issuers
3. **Planned vs operational** — planned facilities EXPECTED empty in registries
4. **Investment vs operating partner** — investment-only partners often don't disclose investees
5. **Source-jurisdiction mismatches** — NHTSA = ground vehicles; FAA/EASA not in catalog; EPA = US-only
6. **Name-variant fragility** — try multiple variants before flagging 0 hits
7. **Counterparty-side disclosure threshold** — 1–3 mentions = MODEST/PASS; SEVERE only if 0 AND counterparty would normally be expected to disclose materially

**Important caveat:** these heuristics were tuned with hindsight on the eVTOL cohort. They survived blinding-by-subagent on that cohort but produced weaker discrimination on the held-out 3D printing cohort (P=50% R=50% loose). Treat the per-source calibration rules as candidate heuristics pending validation on additional held-out cohorts; treat the operational-discipline lessons (notes section, coverage assessment, divergence-not-solvency, blinding, stock-for-services, hindsight-bias warning) as more durably established.

---

## Cohort iteration history

| Iteration | What changed | eVTOL cohort matrix (loose, thr 0.5) | 3D printing cohort matrix (loose, thr 0.5) |
|---|---|---|---|
| Hindsight | LocalProvider scoring with outcome knowledge | P=67% R=67% Sp=67% | (not run) |
| Blinded pre-slicer | Subagent firewall + USPTO ODP + calibration heuristics | P=100% R=67% Sp=100% | P=50% R=50% Sp=50% |
| Blinded post-slicer | + financial-statement notes in slice | **P=100% R=100% Sp=100%** | (not yet rerun) |

---

## Adding a new cohort

1. Create `<cohort>_cohort.py` mirroring `evtol_cohort.py` structure (cohort tuple WITHOUT outcomes; --reveal-outcomes flag)
2. Create `_<cohort>_outcomes.py` with OUTCOMES dict
3. Pull filings: `python3 -m verticals.public_co.<cohort>_cohort --stage pull`
4. Spawn one subagent per ticker with the standard blinded prompt template (eVTOL-style); each writes `data/_local/<ticker>.{input,scores}.json`
5. Run cohort matrix: `python3 -m verticals.public_co.<cohort>_cohort --provider local --reveal-outcomes`

For an honest held-out test, choose a cohort the analyst has not previously scored. The 3D printing cohort was the first such test for this vertical and produced ~50/50 results — a sobering reminder that the eVTOL "perfect" matrix likely overstates generalization.

---

## Known limitations and open issues

- **Single filing per ticker.** The cohort runner picks one pre-cutoff filing (10-K preferred). Material 8-Ks (Items 1.01, 1.03, 3.02, 4.02, 5.02) between 10-Ks are not ingested. This means events that happen mid-year (LILM bankruptcy filed Oct 2024) are only visible if the relevant signals are also in the prior 10-K's notes. Item-filtered 8-K ingestion is a candidate next architectural improvement.
- **TOC false-positives in slicer.** Real Item 1 Business sections sometimes get masked by their TOC-entry counterparts at the document front. Heuristic skips entries followed by page numbers but isn't bulletproof.
- **Calibration heuristics tuned on eVTOL.** Confounds held-out validation; need genuine fresh-cohort tests where the analyst hasn't seen the names.
- **No FAA / EASA / SAM.gov / USAspending coverage.** Aerospace cert claims and federal procurement contracts are structurally invisible to the current M-source library. Would need new connectors.
- **LocalProvider claim_id collision** was fixed but the underlying API (claim_id-based lookup with text-disambiguation fallback) is fragile. A cleaner fix would pass ticker through the score() interface explicitly.
- **n=6 to n=8 cohort sizes** make confusion matrix metrics statistically underpowered. Anything that looks like "perfect" on this N is suggestive, not validating.
