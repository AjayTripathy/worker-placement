# Signal OS — Architecture

**Family office product update, 2026-09-13:** this document describes the research
framework. The current Worker Placement / OfficeKit operating loop, custody and
evaluation boundaries are documented in [officekit/OPERATING_CONTRACTS.md](officekit/OPERATING_CONTRACTS.md).
See [the agent handoff](officekit/AGENT_HANDOFF.md) for migration status and next work.

*The cross-record divergence framework: R, f, M, and the engine that operationalizes them.*

---

## Abstract

**Core insight:** Regulated or self-reported records (`R`) have institutional incentive to diverge from reality. Market or independently-observed records (`M`) do not. When `R ≠ f(M)` — where `f` is a known legal, contractual, or physical relationship — the gap is a signal.

```
Signal = R - f(M)
```

- **Direction of gap** → who is manipulating what, and why
- **Magnitude of gap** → severity (financial impact, regulatory exposure, reputational risk)
- **Pattern across entities** → distinguishes error from fraud, isolated from systemic

The signal value, when economically findable, is governed by:

```
Signal value ≈ I × L × accessibility(M)
```

- **I — Incentive:** financial benefit of non-compliance is large in absolute terms relative to detection risk × penalty
- **L — Structural Lag:** decoupling of obligation from enforcement (self-reporting, agency silos, complaint-driven enforcement, weak penalties, slow audit cycles)
- **accessibility(M):** a property of M itself — how operationally observable the underlying reality is in public records, and at what cost (free API ≫ scrape ≫ paid ≫ FOIA ≫ inaccessible). Captures whether f(M) can be computed cheaply and at scale.

All three terms must be non-zero. This is the pre-screening filter for which verticals merit building.

> **Note on naming:** Earlier drafts called the third term "D" (Data Residue) or "R" (Residue), but both naming choices were misleading. R collided with the claim-side R in the divergence formula. D was just shorthand for what is really a property of M. Expressing it as `accessibility(M)` makes the relationship explicit: observability is part of how we parameterize M, not a separate axis.

> **accessibility(M) varies geographically and over time** even within a single vertical. Same f, same I × L, but `accessibility(M)` for Carbon Mapper-covered geographies is high while for Asian/Eastern European geographies it's currently zero (CM coverage stops at lon 57). The pre-screening should check accessibility for the *specific entities* in scope, not just the abstract domain.

---

## Canonical form across built verticals

Four verticals built so far. Same structure, different domain:

| | Detroit Property Tax | NYC J-51 Rent | Carbon REDD+ | Carbon Methane |
|---|---|---|---|---|
| **R** (claimed) | Assessor's Taxable Value | Owner's stabilization compliance / registration | PDD's claimed annual emission reduction (tCO2/yr) | Project's claimed methane capture rate (kg CH4/hr) |
| **f** (relationship) | TV must reset to ~50% market price on transfer (MCL 211.27a) | Legal max rent = base × RGB cumulative factor; all units must be registered ≤ legal max | Implied avoided deforestation = claim_tCO2 / carbon_stock; observed reduction = pre-mean − post-mean | Capture rate = claim / (claim + observed_leakage); should be 70–90% |
| **M** (observed) | Sale price (MLS, Zillow, deed consideration) | Listed asking rents (StreetEasy, Trulia); DOF comparable income | Annual deforestation in AOI (Hansen GFC satellite) | Plume detections at site (Carbon Mapper L4A, sector-filtered) |
| **Signal** | TV << SEV implied by sale → uncollected tax | Listed rent >> legal max → overcharge liability | Observed reduction << implied avoided → phantom credits | Observed plume / claimed capture too high → low actual capture |
| **Scoring** | $ underpaid/yr per parcel | $ overcharge/yr per unit × units | Severity tier (NEGATIVE / SEVERE / MODERATE / PASS) | Capture-rate tier (<30% / 30–50% / 50–70% / >70%) |

Each vertical is an instance of the abstraction. The framework's value is generality across them.

---

## Architecture overview

Three input pipelines, one decomposer, four compounding assets, one feedback loop.

```
═══════════════════════════════════════════════════════════════════
                     INPUT PIPELINES
═══════════════════════════════════════════════════════════════════

  ┌───────────────────┐  ┌──────────────────┐  ┌────────────────────┐
  │ A: AUTONOMOUS     │  │ B: BUYSIDE DD    │  │ C: THESIS-DRIVEN   │
  │    DISCOVERY      │  │    (user upload) │  │    RESEARCH        │
  │                   │  │                  │  │  (operator-AI      │
  │ Crawls universe,  │  │ One deal, all    │  │   collaboration)   │
  │ hypothesizes      │  │ docs in one      │  │                    │
  │ (R, f, M) triples │  │ batch, output =  │  │ Operator seeds     │
  │ continuously      │  │ per-deal report  │  │ thesis; researcher │
  │                   │  │                  │  │ structures, runs,  │
  │ → continuous      │  │ → on-demand      │  │ surfaces; iterate  │
  │                   │  │                  │  │                    │
  │ Mature mode       │  │ Customer-facing  │  │ Bootstrap +        │
  │ (after >100 f's,  │  │ mode (after      │  │ persistent center  │
  │  >500 sources)    │  │ brand exists)    │  │ of gravity         │
  └────────┬──────────┘  └─────────┬────────┘  └─────────┬──────────┘
           │                       │                     │
           ▼                       │                     │
  ┌──────────────────┐             │                     │
  │ PRIORITIZATION   │             │                     │
  │ V(R, f, M)       │             │                     │
  │ → build queue    │             │                     │
  └────────┬─────────┘             │                     │
           │                       │                     │
           └───────────┬───────────┴─────────────────────┘
                       ▼
═══════════════════════════════════════════════════════════════════
            LAYER 1: DECOMPOSER (operational core)
═══════════════════════════════════════════════════════════════════

  ┌─────────────────────────────────────────────────────────────┐
  │ Stage 1 — CLAIM EXTRACTOR                                   │
  │ LLM reads documents → structured claims                     │
  │ Out: [{subject, predicate, object, scope, source_quote}]    │
  └────────────────────────────┬────────────────────────────────┘
                               ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ Stage 2 — REFERENT TYPER                                    │
  │ LLM + ONTOLOGY → typed referent per claim                   │
  │ Out: [{claim, referent_type, attributes, jurisdiction}]     │
  └────────────────────────────┬────────────────────────────────┘
                               ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ Stage 3 — f CONSTRUCTOR                                     │
  │ Lookup f-LIBRARY by (predicate, referent_type, jurisdiction)│ ◄──┐
  │ If miss: LLM constructs from statute, flags for review      │    │
  │ Out: [{claim, f, expected(M), tolerance, severity_rubric}]  │    │
  └────────────────────────────┬────────────────────────────────┘    │
                               ▼                                     │
  ┌─────────────────────────────────────────────────────────────┐    │
  │ Stage 4 — M SOURCE MAPPER                                   │    │
  │ Lookup SOURCE ATLAS by (referent_type, attribute,           │ ◄──┤
  │                          jurisdiction, granularity)         │    │
  │ If miss: LLM searches for sources, flags for review         │    │
  │ Out: [{claim, f, source[], cost, latency, completeness}]    │    │
  └────────────────────────────┬────────────────────────────────┘    │
                               ▼                                     │
  ┌─────────────────────────────────────────────────────────────┐    │
  │ Stage 5 — ACQUISITION + COMPARISON + SCORING                │    │
  │ • Connector framework fetches M from each source            │    │
  │ • ENTITY RESOLUTION joins R-side and M-side identities      │ ◄──┤
  │ • Compute f(M); divergence = R − f(M)                       │    │
  │ • Apply severity rubric → flag tier                         │    │
  │ • Build evidence trail (source quotes, queries, raw values) │    │
  │ Out: per-claim row in divergence report                     │    │
  └────────────────────────────┬────────────────────────────────┘    │
                               ▼                                     │
                ╔═══════════════════════════════╗                    │
                ║   COMPOUNDING ASSETS          ║                    │
                ║                               ║                    │
                ║   • f-library (~200 rules)    ║ ───────────────────┤
                ║   • Source atlas (~500 srcs)  ║                    │
                ║   • Entity resolution graph   ║                    │
                ║   • Severity calibration      ║                    │
                ║   • Historical signal outcomes║                    │
                ╚═══════════════════════════════╝                    │
                               │                                     │
                               ▼                                     │
                  ┌────────────────────────────┐                     │
                  │     DIVERGENCE REPORT      │                     │
                  │                            │                     │
                  │ • Per-claim severity flag  │                     │
                  │ • R vs. f(M) numerics      │                     │
                  │ • Evidence trail           │                     │
                  │ • $ aggregate exposure     │                     │
                  │ • Recommended further DD   │                     │
                  └────────┬───────────────────┘                     │
                           │                                         │
                           ▼ feedback                                │
                ┌──────────────────────────┐                         │
                │ Outcome calibration      │                         │
                │ (which signals paid off) │ ────────────────────────┘
                │ → updates V-weights,     │
                │   f-library priors,      │
                │   severity thresholds    │
                └──────────────────────────┘
```

---

## The three input pipelines

**Pipeline A — Autonomous Discovery (continuous, agent-driven)**

Discovery agent crawls regulatory text and public registries continuously. For each candidate R it identifies, hypothesizes possible f and M sources. Emits `(R, f, M)` triples. Prioritization function ranks them by `V(R, f, M)`. Highest-scoring become the build queue. Output is a candidate vertical opportunity that then enters the decomposer.

Mature-mode operation. Requires the f-library and source atlas to already cover most common referent types so the agent's hypotheses can be validated cheaply. Becomes viable after ~10 manually-built verticals provide the calibration substrate.

**Pipeline B — Buyside Due Diligence (user-triggered, on-demand)**

User uploads a data room — PPM, OM, deck, term sheet, sponsor track-record claims, financial projections, prior fund performance, anything. Decomposer treats every uploaded document as the source of R: claim extraction runs over each doc, every claim gets typed, the f-library and source atlas drive verification, output is a divergence report keyed to the deal.

**Status (May 2026):** Prototype operational. Two real deals processed end-to-end: FCRE2 LLC ($30M Section 8 housing private credit) caught systematic cost-basis inflation; AHC Series A ($50M venture round) caught Form D dollar mismatches and absence of factory permits. Architecture for productization (policy/materiality/dispatcher) described in Layer 2 below. Customer-facing mode pending credibility from published work in Pipelines A and C.

**Pipeline C — Thesis-Driven Research (operator-AI collaboration)**

Operator supplies a thesis seed ("the Detroit turnkey rental I was pitched looks fraudulent," "the Signal OS framework should apply to NYC rent stabilization"). Researcher (AI) generates the structured hypothesis — turns the seed into a candidate `(R, f, M)` triple by reading statutes, identifying data sources, drafting f. Operator validates the hypothesis and pushes back on methodology. Researcher executes — builds connectors, runs scans. Operator adjudicates findings, picks threads to follow. Both iterate.

**Bootstrap mode and persistent center of gravity.** This is how the f-library and source atlas get built in the first place. The four built verticals (Detroit, NYC J-51, Carbon REDD+, Carbon Methane) each populated ~10–30 entries in each compounding asset through Pipeline C. It remains the highest-value mode even after A and B come online, because operator strategic judgment + AI execution capacity is the highest-leverage human-AI interaction pattern.

---

## Layer 1 Decomposer — five-stage detail

### Stage 1 — Claim Extractor

LLM reads any input document (PDF, HTML, spreadsheet, KML, JSON) and emits structured claims.

**Per-claim schema:**
```python
class Claim:
    claim_id: str
    subject: str            # entity ID or descriptive identifier
    predicate: str          # from controlled vocabulary
    object: dict            # value + units
    scope: dict             # area, time period, population
    source_doc: str
    source_quote: str       # exact text from doc (anti-hallucination)
    confidence: float       # LLM's confidence in extraction
    extraction_notes: str   # ambiguity flags
```

**Failure modes:** image-only PDFs need OCR; foreign-language docs need translation; tables need extraction upstream; LLM hallucination mitigated by requiring `source_quote` to appear in document.

### Stage 2 — Referent Typer

For each claim, classifies what real-world thing it refers to.

**Referent ontology:**
```
geographic_area   (polygon, point, region)
physical_object   (building, parcel, vehicle, facility, infrastructure)
person            (individual, role)
entity            (company, LLC, government body, project developer, fund)
event             (transaction, transfer, payment, regulatory action)
amount            ($, headcount, emission, rent, tax, volume)
time_period       (year, quarter, range, lifecycle stage)
quantity          (count, area, density, rate)
intangible        (license, certification, exemption, obligation)
```

Per-referent attributes drive Stage 4 source matching.

### Stage 3 — f Constructor

Lookup the expected relationship between claim and observable reality. Keyed by `(predicate, referent_type, jurisdiction, time_period)`.

**f-library entry schema:**
```python
class FRule:
    rule_id: str
    predicate: str
    referent_type: str
    jurisdiction: str
    time_period: str

    expected_value_formula: str    # human-readable
    formula_inputs: list[str]       # M attributes feeding it

    noise_tolerance: float          # +/- band considered noise
    severity_thresholds: dict       # {"PASS": 0.25, "MODERATE": 0.5, ...}

    source_statute: str             # MCL 211.27a, RSL § 26-510, etc.
    source_methodology: str         # VM0007, etc.
    promoted_by: str                # human reviewer who approved
    confidence_after_use: float     # updated based on outcomes
```

If the lookup misses, LLM constructs `f` from statute or methodology document and flags for human review before promotion to library.

### Stage 4 — M Source Mapper

For each typed claim with an f, identifies which observable data sources can supply the inputs.

**Source atlas entry schema:**
```python
class MSource:
    source_id: str
    referent_type: str
    attribute: str               # what about the referent it observes
    jurisdiction: str
    granularity: str             # spatial/temporal resolution

    access_pattern: str          # api, scrape, file_download, foia
    endpoint: str
    auth_required: bool
    rate_limit: dict
    cost_per_query: float

    completeness: float          # 0-1, fraction of universe covered
    latency_days: int
    accuracy_estimate: float

    publisher: str
    legal_terms: str
    promoted_by: str
    validation_date: str

    connector_module: str        # path to code that fetches it
```

If lookup misses, LLM searches for candidates, validates accessibility, flags for atlas promotion after first successful use.

### Stage 5 — Acquisition + Comparison + Scoring

Executes data fetches, runs entity resolution to join R and M, computes f(M), measures divergence, applies severity rubric, builds evidence trail.

**Sub-modules:**

- **Connector framework:** uniform interface for httpx APIs, vsicurl raster reads, STAC searches, scrape pipelines, file downloads. Handles caching, rate limits, retries, timeouts.
- **Entity resolution:** joins R-side identifiers (parcel ID, project ID, BBL, LLC name) to M-side observations. Uses fuzzy matching + cross-reference graph + LLM disambiguation. The graph itself becomes a compounding asset.
- **f(M) computation:** straightforward once data is loaded.
- **Severity scoring:** apply the f-library's severity_thresholds.
- **Evidence builder:** every finding gets a trail of (R source quote → M source query → raw values → divergence calc → severity assignment). Required for any publishable or saleable output.

---

## Layer 2 — Productization (buyside DD vertical)

The decomposer is a research-grade engine: claim → typed claim → f-rule → source → comparison → finding. To turn it into a product institutional DD teams can run, three additional concerns have to be encoded:

1. **When to spend money on verification** — paid sources cost real $; FOIA costs time; some claims aren't worth the spend
2. **When to stop investigating** — perfect verification is unbounded work; product needs explicit stopping rules
3. **How to defend each finding** — DD teams need to answer "why did/didn't you check X?" with traceable, reproducible answers

These get encoded in three modules layered on top of the decomposer.

### Materiality

Every claim carries a `Materiality{status, estimated_usd, estimated_pct, derivation}` where `status ∈ {known, estimated, unclear}`. Materiality drives source dispatch. **Asymmetric:** free sources always run regardless of materiality; paid sources only run when materiality is `known` or `estimated` *and* clears a configurable floor.

- **Initial derivation** uses predicate-specific rules: `acquired_at_price → claim_value`; `charges_rent → annual_rent × 12.5x`; sponsor claims → deal_size; venture core-thesis claims → 100% of deal.
- **Re-derivation** runs after the free pass. Observation evidence can upgrade Unclear → Known. Example: a sponsor-anonymity claim with no derivation rule starts Unclear; if the free SoS search returns zero matches, materiality upgrades to deal-level (sponsor-verification failure on a $30M deal = $30M exposure regardless of the original claim's $-value).

Two units supported: USD (when `deal_size_usd` is known) and pct-of-deal (when only `asset_count` or relative weights are known). Lets the framework handle deals where dollar amounts are flexible or negotiable.

### RunPolicy

Three product presets, each parameterizing budget caps, source gating, convergence thresholds, and report severity floor:

| Preset | Cost cap | Wall budget | Paid sources | FOIA | Materiality floor | Surfaces |
|---|---|---|---|---|---|---|
| TRIAGE | $50 | 30 min | off | off | $1M (effectively off) | SEVERE+ |
| STANDARD | $500 | 4 hours | on | off | $25K | MODERATE+ |
| DEEP | $5,000 | 1 week | on | on | $5K | MINOR+ |

Per-customer overrides plug in via `policy.with_overrides()`. **A run with a given policy must be reproducible:** same input + same policy_version = same output. This is what makes findings billable and defensible.

### BudgetState + StopReason + Convergence

Live budget tracking checks before every paid source call. Per-claim stopping rules emitted as `StopReason` on each Finding:

```
CONVERGED      — informative observations from N sources at tier T meet
                 policy.convergence_by_tier (e.g. 1 Tier-1, or 2 Tier-2, or 4 Tier-5)
EXHAUSTED      — all applicable sources tried, no convergence
IMMATERIAL     — known materiality < policy floor; paid sources skipped
DEFERRED       — Unclear materiality after free pass; paid skipped,
                 human triage queued
BUDGET_HIT     — run-level cost or time cap hit
UNREACHABLE    — all sources failed (network/auth)
NOT_DISPATCHED — claim never queried (no f-rule, no source)
```

Convergence requires **informative** observations — a successful query returning `count=0` does not count as convergence (this prevents an empty full-text search from short-circuiting a more authoritative company-name search at the same tier).

Every Finding ships with its StopReason, materiality_at_stop, confidence (derived from authority tier of agreeing sources), and evidence_trail. The DD team can answer "why did/didn't you check more?" with the framework's own metadata.

### M source authority tiers

MSource entries carry an `authority_tier ∈ [1,5]`:

```
1 — government primary record    (deed recorder, court docket, SEC filing,
                                  OSHA establishment, county assessor)
2 — government derived/aggregate (HUD FMR, Census ACS, BLS QCEW)
3 — industry aggregator w/ audit (CoStar, OpenCorporates, RentCast)
4 — public web aggregator        (Zillow, Redfin)
5 — search snippet / Wayback     (DDG snippets, social, news mentions)
```

Convergence rules per policy use tier counts: 1 informative Tier-1 observation ends investigation; 4 Tier-5 observations needed to reach equivalent confidence. This is what separates "we found this in deed records" from "we found this in a Zillow snippet."

Confidence aggregation in the comparator uses `TIER_CONFIDENCE_BASE = {1: 1.0, 2: 0.85, 3: 0.70, 4: 0.50, 5: 0.30}` plus a corroboration bonus for multiple agreeing observations, discounted when stop_reason is DEFERRED or BUDGET_HIT.

### Cross-claim consistency check

A module orthogonal to R-vs-M dispatch. Runs over all extracted claims and finds `(subject, predicate, scope)` groups with conflicting values. Catches internal divergences that the R-vs-M flow misses by definition: when the deck contradicts itself, both values are claims (R), neither is M.

Scope-aware grouping prevents false positives across distinct rounds, cities, or projects (e.g. "Round 1 raised $2M" and "Round 2 raised $7M" share subject+predicate but distinct scope, not a contradiction).

Caught on AHC: pitch deck p.25 says "Factory 1 capacity 1,000 homes/yr"; financial model says "1,750 Townhomes" — same `(subject=AHC, predicate=factory_planned_capacity, scope={factory:Factory 1})`, 75% divergence, flagged SEVERE.

### Absence-of-record signal

The comparator special-cases "claim asserts existence; every source returned `count=0`" as a SEVERE finding rather than UNVERIFIABLE. Without this, the most informative case (we exhaustively queried and found nothing) gets the same severity as the least informative (we couldn't query). Caught on AHC: zero Austin permits + zero OSHA records under any AHC name variant → SEVERE absence-of-record.

### What's been built (buyside DD vertical, May 2026)

- 35+ `MSource` entries across deed records, mortgages, assessments, code violations, eviction filings, HUD subsidy data, market rents, corporate registries, federal & state litigation, UCC, sanctions, IRS 990
- ~10 working connectors: WPRDC Allegheny (sales/mortgages/assessment/PLI), SEC EDGAR (3 modes: full-text, company-name browse, Form D primary_doc.xml parser), HUD FMR, Census ACS B25031, TX Comptroller franchise tax, OSHA Establishment Search, Austin Socrata permits, company_signal (DDG snippets for Crunchbase / Preqin pivots)
- 22+ f-rules in `verticals/buyside_dd/f_library.py`
- Policy engine (TRIAGE/STANDARD/DEEP), BudgetState, Materiality model, asymmetric dispatcher, comparator with severity + confidence + stop_reason, cross-claim consistency check

### Validated against two real deals

- **FCRE2 LLC** — $30M Section 8 housing private credit. Caught: systematic cost-basis inflation in 9 of 16 verified properties (~17% aggregate inflation, ~$110K on the verified subset), Section 8 FMR violations (4 properties priced 30-41% above HUD FMR), one property with no recorded sale at all, sponsor anonymity escalated to deal-level material via materiality re-derivation. Full report at `verticals/buyside_dd/outputs/20260512_212228/DIVERGENCE_REPORT.md`.

- **AHC Series A** — $50M raise at $235M pre. Caught: Form D dollar mismatches on both prior rounds (deck $2M / $7M vs SEC $485K / $2M); zero parent-entity Form D filings under any "American Housing" search variant; zero Austin building permits or OSHA records under any AHC name; AHC TX entity registered in Dallas (zip 75201), not Austin where factory is claimed; internal capacity divergence (1,000 pitch vs 1,750 model = 75% overstatement, ~43% valuation impact). Full report at `verticals/buyside_dd/outputs/ahc_20260513_093817/DD_REPORT.md`.

### Known limits and product gaps

- Connector coverage is the biggest product gap (~10 working sources where a national real-estate-DD product needs 50–100+; venture DD needs USPTO, LinkedIn, PitchBook, Crunchbase paid tiers)
- LLM extraction stage (Stages 1–2) needs an API key in env; AHC run was driven by hand-typed claims because no key was set
- Several portals are blocked from this environment: PA SoS (Cloudflare), USPTO Google Patents (rate-limited), Bozeman OpenGov + ABQ ArcGIS (no public APIs without portal-specific reverse engineering)
- Both `materiality.derive_initial` and `comparator.PREDICATE_TO_ATTR` use hardcoded predicate→derivation tables. Won't scale cleanly to new domains without a meta-layer (LLM-aided extension or generic rule classes)
- Cross-claim `SCOPE_DISCRIMINATORS` is hardcoded; same scaling concern
- Light test coverage; many bugs surfaced by running the framework rather than by design (CIK-parsing, accession-number regex, boolean comparator, prefix-vs-exact observation match, entity_name dispatcher gating)

---

## Layer 3 — Operational discipline

Distilled from the public-co backtest vertical (`verticals/public_co`, May 2026). These are framework-general lessons about HOW to run R / f / M decomposition such that the output is honest and the discrimination is real, not artifact. Each is general across input pipelines (A, B, C); each was learned the hard way against a specific cohort.

### 1. Read the notes section, not just the marketing tier

The most discriminative disclosures live in the financial-statement notes — Commitments and Contingencies, Related Party Transactions, Going Concern, Liquidity and Capital Resources, Subsequent Events — not in the Item 1 Business / Property Description / Project Summary that the issuer wrote to make you bullish.

**Implementation:** the slicer that feeds Stage 1 (Claim Extractor) must weight these sections at 1.5–3.0×, not 0.5×. In the backtest vertical, the slicer originally dropped financial-statement notes entirely from the LLM's view; SRFM's stock-for-services arrangement with Palantir was disclosed plainly in Note 15 but invisible until the slicer was patched. Same fix moved LILM's blinded score from 0.56 (borderline) to 1.75 (strong distress, caught Chapter 11 cold).

**For DD memos and data-room reads:** any analyst process that reads "Item 1 Business" and stops is mis-calibrated. Read the notes. The body of the divergence signal is buried in commitments, related-party, and going-concern.

### 2. Coverage assessment before reading absences as signal

Stage 4 (M Source Mapper) outputs three states for any claim: corroborated, contradicted, or *no signal*. Confusing the third with the second produces both false positives ("0 hits = bearish") and false negatives ("0 hits = clean"). Before scoring, enumerate which M-sources cover the claim's referent type. If the answer is "none" or "only foreign / private actors who don't file with our queryable registries," the right verdict is UNVERIFIABLE — and that gap is itself a signal worth recording.

**Examples of coverage-gap-induced errors:**
- AHC false-negative: queried for tenant-as-permit-filer; tenants don't pull permits, GCs do. Wrong actor type for the claim profile.
- VLD false-clean: framework couldn't reach Velo3D's claim profile because dominant customer (SpaceX, 28% of revenue) is private and invisible to EDGAR. 0 hits ≠ clean.

**Implementation:** every framework output should distinguish "corroborated" / "contradicted" / "no-data" — and any "no-data" line should be paired with a coverage statement (which sources were queried for which actor types).

### 3. Divergence detection ≠ solvency model

The framework answers "does the issuer's R match observable M?" — not "is the entity operationally viable." A name can pass the divergence check (every claim corroborated by registries) and still be failing from cash burn, demand softness, or operational under-delivery. Desktop Metal scored 0.00 blinded (6 PASS + 1 UNVERIFIABLE on real EPA-permitted facilities, real Stratasys merger discussion) — and was acquired in distress. The framework was correctly answering "are they lying" (no); the company was failing for reasons the framework was structurally blind to.

**Implementation:** label which question each output is answering. "We found no divergence" ≠ "long this." Cohort screens that include both divergence and operational metrics rank differently than divergence-only screens. For DD memos, pair clean-bill-of-health divergence findings with separate operational/financial review.

### 4. Subagent firewall for blinded cohort scoring

When the analyst's context contains outcome knowledge for some or all cohort items, hindsight contaminates query selection, severity assignment, and interpretation in ways the analyst can't self-monitor. The fix is to spawn one isolated subagent per item with no outcome labels in its prompt; the subagent produces input.json + scores.json files independently; outcomes live in a separate `_<cohort>_outcomes.py` module the subagent never reads; the runner reveals them only at confusion-matrix time.

**When this matters:** cohort screens (Pipeline A discoveries, Carbon project ranking, Signal OS public-co backtests) where N items will be scored and the analyst has prior knowledge of some. Forensic single-deal DD does NOT need this — there the analyst should see everything and probe adversarially.

**Validation:** on the eVTOL backtest cohort, three iterations of the same cohort produced increasingly clean confusion matrices: hindsight (P=67%, R=67%) → blinded subagent (P=100%, R=67%) → blinded post-slicer (P=100%, R=100%). EVEX flipped from 1.80 (hindsight FP, the original "falsifiable bet" of EVTOL_FORWARD_TEST.md) to 0.00–0.21 (blinded TN). LILM came in at 1.75 (blinded TP) instead of 1.20 (hindsight inflated).

### 5. Stock-for-services / vendor-payable-to-equity is a generic distress fingerprint

When an issuer settles vendor invoices in stock instead of cash, that's a high-signal flag — recurring shape across SRFM (Palantir paid in shares), LILM (cloud-subscription vendor settled in 12.77M shares), and likely many private deals (deferred sponsor fees, F&B operators paid in equity, related-party loans subordinated to common). The disclosure is almost always plain English in the Commitments and Contingencies note. Marketing tier calls it a "strategic partnership"; financial-statement notes show "creditor we couldn't pay in cash."

**Implementation:** Stage 5 scoring should treat any disclosure of share-issuance-as-payment-to-vendor as a structural RED_FLAG candidate. The pattern transfers directly from public-co backtests to private DD; the only thing that changes is the wording.

### 6. Calibration heuristics tuned on known cohorts are contaminated

If you write scoring rules ("EPA FRS only registers EPA-regulated facilities, so absence isn't a red flag for office sites") after observing the framework misfire on a known-clean cohort, those rules carry hindsight even when applied via subagent blinding. The slicer fix and the operational-discipline lessons above are general (they reflect domain truths about SEC filings and document structure), but the per-source calibration heuristics in the backtest's SCORE_SYSTEM prompt were authored knowing eVTOL outcomes — they survived the subagent firewall but they didn't survive the held-out 3D-printing cohort test, which scored ~50/50 precision/recall instead of the eVTOL cohort's perfect ranking.

**Implementation:** maintain a strict train/test split. Calibration heuristics tuned on cohort X are contaminated for any future evaluation involving cohort X. Genuine validation requires a held-out cohort the analyst hasn't touched. The compounding-assets section above describes how f-library and source-atlas grow monotonically — calibration heuristics should be promoted to the f-library / scoring-rule layer only after they've survived held-out validation, not before.

### 7. R-side ingestion fidelity is upstream of every signal — clean text, tables, and document selection

`Signal = R − f(M)` silently degrades to noise when the **R is mis-read before it is even compared.** Three ingestion failures, all on the R side (Stage 1 Claim Extractor's input), each of which makes a real disclosure invisible to regex *and* to an LLM slicer — so the divergence is never computed:

1. **Tag pollution.** Raw SEC HTML wedges inline-XBRL tags between a trigger verb and its number (`"accounted for <ix:..>69</ix> %"`). A regex anchored on `accounted for … 69%` never matches, and an LLM window fed the raw markup wastes its budget on tag soup. Skyworks' Apple = 69%-of-revenue concentration is stated in plain prose in Note 14 and was *still* returned as `NO_CONCENTRATION` until the text was cleaned.
2. **Table-only / split-cell disclosure.** Concentration, customer lists, and segment tables live in `<table>`s whose number and `%` land in *adjacent* cells (`Nokia | 12.0 | %`), with the entity sometimes only in a column header or a footnote (`Customer A (1)` … `(1) NVIDIA`). Flat text-grep sees none of it. Cirrus discloses its sole customer *qualitatively* ("we had one end customer, Apple Inc.") with no percentage at all — a third disclosure shape entirely.
3. **Wrong document.** A "prefer the latest 10-Q" selector skips a just-filed annual 10-K — exactly the filing that carries the fuller concentration / going-concern / commitments notes — in favour of a stale quarterly that omits them.

None of these are detector bugs; they are **ingestion** bugs, and they were dragging recall harder than any amount of regex/prompt tuning could recover. A detector can be perfectly specified and still score `NO_CONCENTRATION` on a 69%-customer filing because the bytes it read were corrupt.

**Implementation.** The R-side ingestion layer is shared infrastructure, not per-detector code:
- **Clean-extract + table-flatten** (`edgar.html_to_clean_text` / `edgar.fetch_filing_clean`): bs4 strips tags and flattens each `<table>` to `cell | cell` lines, so prose *and* tables reach the reader. Prefer `fetch_filing_clean` over `fetch_filing_text` for any regex/LLM consumer.
- **Most-recent-of-either-form document selection** (`edgar.latest_filing`), never prefer-a-form.
- **A generic structured-fact ingestor** (`verticals/public_co/sec_tables.py`): caption-scoped table parsing with denominator tracking (revenue vs. accounts-receivable), footnote entity-resolution for *coded* customers only, a qualitative sole-customer pass, and a hard anti-screen that keeps volatility / margin / tax tables silent. It emits normalized `{entity, pct, denominator, source}` records the detector consumes instead of pattern-matching flattened prose. Validated on a cohort + external holdouts (Fabrinet named rows, Universal Display / Photronics coded rows, Cirrus qualitative) with zero spurious records.

The leverage is that this is *one* fix serving *every* SEC consumer: lifting clean-extract into the shared `edgar` module and migrating the ~dozen public_co detectors / m-sources / corpus-builders off raw `fetch_filing_text` fixes the tag-pollution recall ceiling for going-concern, lender-concession, auditor-change, insider-pledge and the rest at once — the same way the f-library and source atlas compound. **General rule: before tuning a detector, verify it is reading clean, complete, point-in-time-correct R. A signal computed on corrupt R is indistinguishable from no signal.**

---

## Compounding assets

The four assets are why the second vertical is faster than the first, and the tenth is faster than the second. Marginal cost per new vertical decays.

**1. f-library** — codified expected relationships. Grows with each new vertical or new statute read. ~200 entries after 10 verticals.

**2. Source atlas** — directory of observable sources by referent type. Grows monotonically. ~500 entries after 10 verticals.

**3. Entity resolution graph** — joins identifiers across systems (LLC parents, parcel IDs, BBLs, project developers, beneficial owners). Multi-domain moat — knowing that "MLC Rentals LLC" in Detroit is the same beneficial owner as "CAULIS NEGRIS II LLC" in Wayne County deeds, and that this LLC may also touch rent-stabilized buildings in NYC.

**4. Severity calibration + signal outcome history** — over time, thresholds get tuned based on which signals turned out to matter (enforcement action, lawsuit, market move, settlement) vs. which were noise. This is the calibration data that lets the prioritization V-function improve.

---

## Prioritization function (Pipeline A only)

For each candidate `(R, f, M)` triple emitted by Pipeline A, score on 0–100:

```
V(R, f, M) =
    + w1 · log10(Universe_economic_exposure_$)         // 0–10
    + w2 · log10(Annual_buyer_TAM_$)                   // 0–10
    + w3 · Signal_magnitude_estimate                   // 0–5
    + w4 · M_accessibility                             // 0–5
    + w5 · f_clarity                                   // 0–5
    + w6 · Novelty_score                               // 0–3

    − w7 · log10(Build_cost_hours)                     // 0–5
    − w8 · Methodology_risk                            // 0–5
    − w9 · Legal_risk                                  // 0–5
    − w10 · Adverse_party_incumbency                   // 0–3
```

Initial weights are calibrated against actual outcomes after each completed vertical. Verticals that produced revenue increase the relevant weights; verticals that flopped decrease them.

---

## Why this architecture supports all three input pipelines naturally

The autonomous discovery agent (A) emits the same kind of object that the buyside DD pipeline (B) and thesis-driven research pipeline (C) produce: a set of R claims that need verification.

Pipeline A generates them by reading regulatory text and hypothesizing what would be reported under that regime.  
Pipeline B receives them directly from the user's data room.  
Pipeline C generates them from operator thesis + researcher structuring.

All three then flow through Stage 1 (or skip it if claims are already structured), Stages 2–4 (typing, f construction, source mapping), and Stage 5 (acquisition, comparison, scoring).

The only architectural difference: Pipeline A's outputs feed back into prioritization weights; Pipeline B's outputs feed back into the per-customer report; Pipeline C's outputs typically feed back into operator strategic decisions for the next thesis. Same engine, three output channels.

---

## What this design supports that current state can't

| Today | With decomposer architecture |
|---|---|
| Each vertical hand-built, 1–2 weeks per | New vertical = config-only entries in f-library + source atlas, ~1 day |
| No way to handle ad-hoc DD requests | Customer uploads data room, gets divergence report in 24 hours |
| Strategic direction requires human roadmap entirely | Autonomous agent surfaces ranked candidates; human chooses among them |
| Each scan is one-shot | Continuous monitoring of any deployed signal; alerts on divergence |
| No reuse across verticals | Same engine, accumulating compound assets, marginal cost decays |

---

## Pipeline maturity sequencing

The three pipelines come online in order:

1. **Pipeline C is now.** Bootstrap mode. Built four verticals this way. Continues as the persistent center of gravity even after A and B come online.

2. **Pipeline B comes after credibility.** First customer data rooms appear once published work establishes the brand. ~6 months out conditional on closing first paying customer.

3. **Pipeline A comes last.** Requires the compounding assets to have enough coverage that the agent's hypotheses can be cheaply validated. Probably 12–18 months out, after 10+ verticals exist.

The whole architecture is designed so building any one pipeline pays back into the other two. Building Pipeline C verticals today populates the f-library and source atlas that make Pipeline A possible later. Building the decomposer now serves Pipeline C immediately, and serves B and A when those become viable.

---

## Files in this repo

- `verticals/<name>/` — per-vertical config + connectors
  - `verticals/buyside_dd/` — most fully-developed vertical (May 2026):
    - `schemas.py` — Pydantic models (Claim, TypedClaim, FRule, MSource, Materiality, StopReason, Observation, Finding)
    - `f_library.py` — 22+ encoded f-rules
    - `source_atlas.py` — 35+ MSource entries with authority tiers, plus the canonical M taxonomy as module docstring
    - `policy.py` — RunPolicy + TRIAGE/STANDARD/DEEP presets
    - `budget.py` — BudgetState (cost/time/calls)
    - `materiality.py` — derivation + re-derivation + auto-infer deal_context
    - `dispatcher.py` — policy-driven asymmetric dispatch
    - `comparator.py` — severity classification + confidence + stop_reason
    - `cross_claim_check.py` — internal-consistency finding generator
    - `connectors/` — base + ~10 implementations
    - `pipeline.py` — Stages 1–6 orchestrator (LLM-driven extraction + dispatch + report)
    - `inputs/`, `outputs/<run_id>/` — per-run materials + findings
  - `verticals/carbon_offsets/` — methane + REDD+ league table scans, satellite-anchored
- Other verticals have not yet been migrated to the buyside DD architecture (policy/materiality/dispatcher); they exist as standalone scan scripts.

The next concrete consolidation step is to extract the buyside DD's policy/dispatcher/comparator into a `core/` module so the other verticals can adopt the same productization layer.
