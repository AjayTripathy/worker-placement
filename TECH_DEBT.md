# Tech Debt

Honest accounting of gaps between what `ARCHITECTURE.md` claims and what the code actually does, plus shortcuts taken in implementation. Read this if you're trying to understand the codebase or deciding whether to refactor before extending.

Most of these are **deliberate non-decisions**, not bugs. Forcing the refactor would be churn until a second concrete use case demands the abstraction. They're documented so the gap doesn't surprise anyone and so the conscious decision to defer is on the record.

---

## Cross-vertical reuse is mostly aspirational

`ARCHITECTURE.md` describes f-library and source atlas as compounding assets that grow monotonically across verticals (~200 f-rules and ~500 sources after 10 verticals). The code is closer to "each vertical bespoke."

### What's actually shared
- `core/protocols.py` — `GapFunction`, `Source`, `RuleInterpreter`, `Scorer`, `SignalStore` Protocols (interfaces only)
- `core/models.py` — `Entity`, `GapResult`, `Record`, `Signal`, `SignalRule`, `VerticalManifest`
- `core/engine.py` — orchestration loop (vertical-agnostic)
- `core/llm.py` — `AnthropicClient` + `NullLLMClient`
- `store/sqlite.py` — `SQLiteSignalStore`

### What isn't shared (each vertical bespoke)

| Vertical | f implementation | Schema for f | Lines |
|---|---|---|---|
| `buyside_dd/` | `f_library.py` (28 FRule entries) + `comparator.py` | `buyside_dd/schemas.py:FRule` | 882 |
| `property_tax/` | `gap.py` + `cap_law.py` (MCL 211.27a hand-coded) | implicit in code | 288 |
| `rent_stabilization/` | `gap.py` + `rgb_schedule.py` (NYC RSL hand-coded) | implicit in code | 317 |
| `public_co/` | `m_recipes.py` (8 recipes in dict-of-dicts format) | own ad-hoc schema | ~230 |
| `carbon_offsets/` | raw Python in `scan_forest_v2.py` etc., no f abstraction | none | — |

Three different schemas exist for what the architecture calls "FRule": `buyside_dd/schemas.py:FRule`, `core/models.py:SignalRule`, `public_co/m_recipes.py` recipe dicts. Predicates rarely overlap across the verticals built so far, so there's been nothing to actually consolidate at the rule level.

**Decision:** keep bespoke until a second vertical needs the same predicate. The first time `acquired_at_price` shows up in two verticals at once, promote `FRule` to `core/`.

---

## Empty placeholder directories

| Path | Intended purpose | Actual state |
|---|---|---|
| `compiler/` | LLM-driven tool to take statute text and emit an `FRule` + formula | empty `__init__.py` only |
| `sources/` | Cross-vertical `MSource` registry that `buyside_dd/source_atlas.py` and `public_co/m_source_catalog.py` would both consume | empty `__init__.py` only |

Both are flagged as "Reserved" in the top-level README. Listed here so the discrepancy with the architecture promises is on the record.

**Decision:** keep as placeholders. Build them only when the second consumer appears.

---

## Duplicated connectors

| Source | Where it exists | Notes |
|---|---|---|
| **SEC EDGAR fulltext + submissions** | `buyside_dd/connectors/sec_edgar.py` AND `public_co/m_sources/edgar_fts.py` + `public_co/edgar.py` | Different code paths, same upstream API. Probably `public_co` versions are newer / better-tested. |
| **USPTO patents** | `buyside_dd/connectors/uspto_patents.py` (legacy PatentsView; sunset upstream) AND `public_co/m_sources/uspto_odp.py` (current ODP) | The buyside_dd path is dead code in practice — PatentsView was decommissioned. New work uses `uspto_odp`. |

**Decision:** acceptable for now. Consolidating would touch both vertical surfaces and the `public_co` connector is the actively-maintained one. Mark `buyside_dd/connectors/uspto_patents.py` as deprecated in a docstring; redirect to `public_co/m_sources/uspto_odp.py` when buyside_dd next needs patent data.

---

## Calibration heuristics tuned on a single cohort

The 7 calibration heuristics in `verticals/public_co/llm_pipeline.py:SCORE_SYSTEM` (EPA FRS scope, foreign-issuer ADR disclosure, planned-vs-operational, etc.) were authored after observing the framework's behavior on the eVTOL cohort.

- They survived blinded subagent re-runs on eVTOL (the subagent firewall preserves outcome blinding even though the heuristics carry hindsight)
- They produced weaker discrimination on the held-out 3D-printing cohort (P=50% R=50% loose) before the slicer fix
- **Held-out validation (quantum cohort, 2026-05-16):** the post-improvement heuristics, now embedded in per-cohort `*_subagent_prompt.py` templates (defense / lidar / nuclear / quantum), were applied to a held-out quantum-computing cohort (RGTI, IONQ, QBTS, ARQQ, QUBT) the heuristics had never been tuned on. Result: framework cleanly discriminated 3/5 names with composite >= 1.25 (ARQQ 1.50 with 2 RED + 1 SEVE; QUBT 1.38 with 2 RED + 1 SEVE; QBTS 1.25 with 2 SEVE) and 2/5 names clean (RGTI 0.50; IONQ 0.38). The v2 Discovery_advantage gate then correctly suppressed QUBT (30.1% short float — bear case already crowded post-LSI-acquisition) and emitted 2 forward bets (ARQQ + QBTS). See `verticals/public_co/data/_quantum_cohort/PREDICTIONS.md`. Calibration is now empirically validated on a true held-out cohort.

This is documented in `signalos/ARCHITECTURE.md` Layer 3 §6 and in `public_co/ARCHITECTURE.md` "Calibration heuristics" section, but is repeated here because it affects how to interpret cohort confusion matrices.

**Updated decision (post-quantum):** the heuristics generalize. Next risk to monitor is sub-vertical drift — quantum-computing-specific Heuristic 9 (physical-vs-logical qubit conflation) and Heuristic 11 (bookings-vs-GAAP-revenue) were added to the quantum prompt; if a future cohort needs analogous bespoke heuristics for its sub-vertical, that's worth factoring out into a structured config rather than free-text prompt edits.

---

## Other shortcuts noted in code

| Where | Shortcut | Implication |
|---|---|---|
| `verticals/public_co/providers.py:LocalProvider.score()` | Falls back to text-prefix matching across all `*.scores.json` files when ticker isn't stashed; LLMs paraphrase between input.json and scores.json so this is fragile | Was a real bug — fixed by stashing `_current_ticker`. Fallback path remains for backwards-compat but is unreliable. Cleaner fix: pass ticker through the `score()` interface explicitly. |
| `verticals/public_co/filing_slice.py:_find_section_starts` | Heuristic skips section headers followed by 1-3 digit page numbers to avoid TOC false-positives. Doesn't catch all formats. | Real Item 1 Business sometimes gets masked by its TOC counterpart. Affected SRFM 10-K (the Palantir-stock-for-services slice still picked up the right section because of multi-section overlap). Worth a more robust TOC-detection pass. |
| `verticals/public_co/m_sources/nrel_fuel.py` | Hard-codes `DEMO_KEY` instead of reading `NREL_API_KEY` env var | Rate-limited under heavy use. Two-line fix when needed. |
| `verticals/buyside_dd/materiality.py` + `comparator.py` | Hardcoded `predicate→derivation` tables (`SCOPE_DISCRIMINATORS`, `PREDICATE_TO_ATTR`) | Won't scale cleanly to new domains without a meta-layer (LLM-aided extension or generic rule classes). Documented in `ARCHITECTURE.md` "Known limits and product gaps." |
| `verticals/property_tax/lasalle_v2/coverage_assessment.md` | `mls_sales` table in `detroit_fraud/uncap_tracker.db` is **99.9999% assessor-record-repackaged** (285,489 of 285,490 rows are `source='assessor_record'`) | The Redfin/Zillow/PropStream/ATTOM connectors exist as code but produce zero rows. The `method_agreement = both` flag in v1 LA Salle output is misleading — both methods derive from the same source. Detroit data layer needs the MLS connectors actually wired up to populate the table for real cross-source corroboration. |
| `verticals/property_tax/jurisdictions/detroit/` (legacy in `/Users/ajay/exalted/detroit_fraud/`) `analysis/uncap.py` fraud_score weights | Authored knowing the LASALLE pattern (the canonical case). Score weights encode the case shape. | Score is a useful ranking heuristic but NOT a falsifiable probability. Holdout-validation against a non-LASALLE neighborhood not done. |
| `verticals/buyside_dd/connectors/state_corp_pa.py` | Pennsylvania SoS portal is Cloudflare-blocked from this environment | Connector fails gracefully but means PA-deal verification is partial. Could be unblocked with a paid proxy or scraper API. |

---

## Architectural limitations not yet addressed

These are real structural shortcomings in the current pipeline that would require engineering work to close.

| Limitation | Where flagged | Status |
|---|---|---|
| **8-K item-filtered ingestion** (public_co) | `public_co/ARCHITECTURE.md` "Known limitations" + this session's discussion | The cohort runner picks one filing per ticker (10-K preferred) by design. Items 1.01 / 1.03 / 3.02 / 4.02 / 5.02 in pre-cutoff 8-Ks contain material events between 10-Ks. Indexing them would catch mid-window distress signals (LILM-style mid-year bankruptcy trail) that the 10-K-only mode misses. **Not built.** |

> **Discoveries from blinded re-runs are tracked elsewhere, not here.** When the methodology surfaces a new R/f/M triple (e.g. the PRE-on-LLC pattern surfaced by `lasalle_v2/`), that's a finding/win, not debt. See the relevant vertical's README ("Known triples" section) for the running list per vertical.

> **Coverage extensions** (M-sources that exist but aren't wired) are connector-roadmap items, not internal debt. Examples: Detroit L-4260 PTA filing log (FOIA-able from assessor); Michigan Tax Tribunal + Detroit BoR petition docket; Michigan SoS LARA LLC filings; CoStar / RentCast for income-property SEV cross-check. See `vertical_ilr_scoring.md` and per-vertical READMEs for the connector roadmap; treat coverage gaps as forward-looking opportunities, not backward-looking debt.

---

## Repository size

`verticals/carbon_offsets/data/` is **3.25 GB tracked** (469 KML files plus GMW mangrove zips + tiles). Largest single file is 99 MB (under GitHub's 100 MB hard limit; over its 50 MB warning).

Consequences:
- Slow `git clone` for collaborators (~3.25 GB pull)
- Approaches GitHub's per-repo soft cap if the repo grows much further
- The carbon scanner could re-fetch KMLs and GMW tiles from public sources on demand

**Decision:** kept tracked for now to make the carbon analysis reproducible without re-pulling. If repo size becomes a real problem, untrack `verticals/carbon_offsets/data/{kml_cache,gmw}/`, gitignore them, document the re-fetch path in `verticals/carbon_offsets/README.md`.

---

## Things this doc deliberately doesn't list

- **Bugs** — file as issues, fix in commits
- **Wishlist features** — different doc; this is for *gaps between architecture promises and code reality* and *known shortcuts taken*
- **Connector additions** — see `vertical_ilr_scoring.md` for what to build next; the gaps there are forward-looking, not debt

## 2026-08-06 — Europe screen (screen_europe.py / esef_fundamentals.py): balance-sheet blindness, 4th confirmation
Filed from EUROPE_TRAP_BATCH2 (verticals/deep_value/global/data/EUROPE_TRAP_BATCH2.md):
1. **IFRS16 lease-blind `ncash_r` + FCF** — Tokmanni (batch-1), VERK.HE, CARD.L, KSL.HE. FCF=CFO−PPE omits lease principal → FCFy overstated up to 2.4x on leased-footprint retailers. Fix: subtract LeaseLiabilities where tagged; else emit `fcf_lease_blind` flag, not a number.
2. **Total-debt blindness when `Liabilities`/borrowings tags absent** (194 SE rows, 24 FI, 23 DK): net-cash computed from cash alone → KSL printed +0.18 ncash vs real €54.6M net debt (7.9x fake vs 14.3x true EV/EBIT). Fix: ncash_r=None when no debt-side tag; missing debt must never default to zero.
3. **Statutory-EBIT one-off contamination** (VERK finance-book gain, THS $67.3M royalty reversal): add `one_off_suspect` flag when |ΔEBIT|>50% on <10% Δrevenue; comparable-EBIT stays a manual trap-verification job.

## 2026-08-14 (batch-adjudication systemic findings)
- **Pack drift between benches**: red and blue can render against DIFFERENT evidence packs (GOTU: red on 8/12 px 1.80 "bounced", blue on 8/14 px 1.68 "drifting to low"); the misquote checker compares each bench only to its own prompt, so real drift is invisible by construction. Fix: stamp packs with as-of + inject red's pack tape line into the blue prompt for explicit diffing.
- **Truncated-instrument FATALs (3 of 8 courts)**: red benches manufacture FATALs by reading half an instrument (PGY: stopped at investing subtotal, missed financing +$31M; CSHR: absence claim from wrong IR venue; UAMY: transcript vs written 8-K). Candidate validator rule: any REFUTED/FATAL grade must state which sections/venues were read.
- **dd52 anchor contamination (4 of 10)**: single-session binary gaps, SPAC trust prices, stale pre-crash highs, spike give-backs all corrupt the drawdown anchor. Guard drafted in KG (censor/re-anchor when drawdown is dominated by one session; re-rank on 26w/post-event high) — wire into blob_sweep + evidence packs.
- **Sector mistags propagate into dispatch (5 of 10)**: GOTU tagged Real Estate mis-dispatched US municipal permit connectors against a Beijing footprint. excess_dd-vs-sector-median is fabricated on mistagged names. Needs a sector-sanity check at pack build (SIC vs yfinance vs description cross-vote).
- **FPI XBRL blind spot**: 6-K/20-F filers (WDH/GOTU/TME) render empty quarterly XBRL in packs; needs a 6-K exhibit fallback series.

## 2026-08-15 (batch-4 systemic findings — several repeat, priority rises)
- **Sector mistags now 8/14 in one batch** (cumulative ~13 names): excess_dd-vs-sector-median is fabricated on mistagged names and mis-dispatches geographic connectors. The pack-build sector-sanity cross-vote (SIC vs vendor vs description) is now the highest-value single screen fix.
- **dd52 anchor contamination — 5 more names** (spike-anchored highs, phantom hi52 bars, rebrand round-trips): implement dd52_anchor_contamination_guard + spike_unwind check as ONE upstream gate in blob_sweep/pack build (censor or re-anchor to 26w/post-event high when the high is a single-session artifact).
- **Bench-side IBKR permission denial: 14/14 this batch** (works at adjudication). The runner subprocess needs the IBKR MCP allowlisted or a quotes-file handoff (pack could carry a fresher gateway tape stamped at render time).
- **Pack tape can REGRESS mid-session** (later builds served older closes on AXTI/KEEL): stamp packs with tape as-of and refuse to serve an older close than a prior same-day build.
- **Duplicate un-superseded artifacts** (OLMA: two REFUTABILITY files 8min apart, 8/10 then 4/10, no marker): runner should write a SUPERSEDED-BY header into the older file when a stage re-runs.
- **Dispatched-but-uninstrumented connectors read as absence-of-signal** (hiring_velocity on LRN — the single highest-value pre-Oct action; KEEL's whole physical layer UNCHECKABLE): preflight must mark NOT-RUN loudly, and LRN's enrollment-window hiring read should be run manually now.

## 2026-08-15 (batch-5 systemic findings)
- **Sector mistag, 3/5 THIS batch** (CLSK bitcoin miner, SECZ RWA tokenization, WYFI neocloud — all "Finance: Consumer Services"; ADTN→Utilities last batch): the pack-build sector cross-vote (SIC vs vendor vs description) remains the single highest-value screen fix and its priority rises again. Every excess_dd in the sweep is fabricated on these names.
- **blob_sweep selects damage-ARRIVING names into a damage-ABSENT court**: all five batch-5 triages wrote "COURT-WORTHY (damage-absent): none." A drawdown-selected universe systematically finds names that fell for good reasons. Candidate fix: require one damage-absent leg (or a named forced seller) at REFUTABILITY triage before a bench is paid for.
- **litigation_screen must emit ROUTE-TO-BROWSER, not UNCHECKABLE, on state/DC-court cases** (JBGS: both benches declared the DC Superior Court docket a coverage gap while the desk owns the real-Chrome CaseSearch path that produced the AHC Bozeman source). Wire the venue check into the connector's dispatch guard.
- **sentinel2_buildout / plant_thermal need a HARD scene-recency assertion** (WYFI red authored satellite_scene_recency_guard and violated it one finding later): connector must return INSUFFICIENT-COVERAGE when the most recent scene predates the claim window — prose rules demonstrably do not bind even their author. Sibling guard: completed_asset_reads_as_paused (activity=False on a FINISHED building; check for purchase/completion events in the same filing — WYFI MTL-3 was BOUGHT, not paused).
- **Misquote validator: FIXED this session** (fraction-vs-percent ~100x unit detection + SUPERSESSION-DECLARED tagging in desk/court_runner.py). Remaining: packs should stamp tape as-of so the validator can reconcile a declared supersession against the cited close mechanically.
- **failed-sale financing liabilities belong in pre-flight** (SPRY: -$28M net cash carried through triage AND red before blue caught +$47M): pack builder should flag any "financing liability" line whose note lacks a maturity/repayment mechanism before net-cash arithmetic reaches a bench.
