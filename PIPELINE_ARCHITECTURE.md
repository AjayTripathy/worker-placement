# Pipeline hardening — production architecture for the three doubles
*2026-08-06 · companion to `ARCHITECTURE.md` (aspirational core) and `TECH_DEBT.md` (honest gaps). Scope: the three pipelines the attribution work identified as where returns actually come from. Design stance: BROWNFIELD — every component below extends an existing module; nothing is greenfield.*

## Why now (the failure evidence)
- **STEM.L +26.6% uncaught**: batch-1 named the exact tripwire in prose; nothing was wired. Verdicts without triggers don't trade. (Fixed retroactively 2026-08-06; the *class* of failure is unfixed.)
- **Screen lease/debt blindness, 4th confirmation** (Tokmanni → VERK → CARD → KSL): a defect filed in a batch doc in July recurred in August because batch docs aren't a defect tracker. Two of three batch-2 rejections were *our* artifacts.
- **Batch orchestration = a chat session**: corpus refresh → screen → diff → agent dispatch → ledger upsert → pack wiring ran as one assistant session with manual steps between. Every gap is a place the next session forgets.
- **$133k of held cost unclassified**: attribution had a blind spot a third of the book wide.

## Cross-cutting substrate (all three pipelines)

### S1. Store contract (`desk/store.py`, new, ~100 LOC)
Every JSON store R/W goes through one helper:
- **MERGE-only upsert** with key function, atomic replace (tmp+rename), corrupt-file backup — the clobber lesson is recurring; `BROKEN_PRINTS.json` already does this locally, promote the pattern.
- **Provenance stamp** on every write: `{asof, generated_by, run_id, schema_version}`.
- **Schema validation on write** (jsonschema, `desk/schemas/*.json`): research_ledger names, resolution packs, edge classifications, shortlists, batch verdicts. Invalid write = loud failure, never a partial store.
Migration: wrap the top-5 stores first (research_ledger, resolution_packs, edge_classifications/*, entry_plan, shortlists). Do NOT rewrite existing writers wholesale — adopt on touch.

### S2. Run manifests (`desk/data/run_manifests/{pipeline}/{run_id}.json`)
Every batch/screen/detector run writes: input digests (corpus store hash, price-cache asof), code git-SHA, counts at each gate (indexed → extracted → scored → shortlisted → fresh → dispatched → promoted), and exclusion reasons. Today's "scored_by_country identical to July" suspicion becomes a checkable diff instead of an eyeball.

### S3. Agent-step protocol (`desk/agent_steps/`)
LLM stages (trap-verify, refutability triage, court-lite classification) are the only non-deterministic components. Contract:
- **Versioned prompt templates in-repo** (`agent_steps/templates/*.md`, with `{screen_row}`-style slots) — not composed ad hoc in a session. Template changes are diffs, reviewable.
- **Structured output schema** per step (verdict enums, `resolves`, `disposition`, `citations[]`, `corrections[]` — the batch-2 verifiers refuting my prompt premises earned a first-class field).
- **Output-side validator** (deterministic, the dispatch doctrine): verdict ∈ enum; ≥1 primary citation per dated claim; UNVERIFIED markers preserved; refuses to persist otherwise.
- **Dispatcher** (`agent_steps/dispatch.py`): fan out K names in parallel (Task/Agent API or claude -p), collect, validate, write via S1. Model tier per step config (volume=opus, escalation=fable — the tiered-court doctrine).
- Every step supports `--dry-run` (render prompts, no dispatch) and is idempotent by (template_version, input_digest).

### S4. Enforcement point = `consistency_check` (exists; add invariants)
New checks, each routing CRITICAL per its existing escalation path:
1. Every ledger name in state WATCH / STAGE2-CANDIDATE has ≥1 **future-dated** resolution pack. *(The STEM invariant.)*
2. Every held position (positions_cache STK) has an edge classification with a non-empty `edge_type` or an explicit `unclassified_ok` waiver. *(The $133k invariant.)*
3. Every pack past its date is adjudicated within 72h (headless_grader) or flagged.
4. Every trap-batch verdict name exists in the ledger. *(Batch docs can't silently diverge from the ledger.)*
5. Screen-defect ledger (S5) entries older than 30d with no linked fix-commit → surface weekly.

### S5. Defect ledger (`desk/data/screen_defects.jsonl`)
Append-only: `{date, screen, defect, names_hit[], fix_direction, status}`. TECH_DEBT.md stays the narrative; this is the machine-checkable list consistency_check reads. The Tokmanni recurrence happens because prose isn't polled.

---

## Pipeline 1 — Orphan verification (screen → trap-verify → Stage-2 → court → starter)

**Current**: per-geo screens (`verticals/deep_value/global/{screen_europe,screen_japan,screen_korea}.py`) + corpus adapters (esef/edinet/dart) — solid; everything downstream is session-driven.

**Cadence principle**: the layers have different natural frequencies — filings arrive in seasonal waves, prices move daily, verification is batch-economic. So the top of the funnel is EVENT-DRIVEN off a cheap daily poll, not blind-scheduled at any cadence. (Amended 2026-08-06 from blind-weekly after review: "why not daily" — because a daily *full* run re-crawls ~1,700 filings to learn nothing and churns agent dispatches on price noise; a daily *delta-poll* gets same-day responsiveness for ~6 HTTP requests.)

**Target flow** (registry-scheduled, each stage a separate cron entry so failures isolate):
1. **`corpus_index_poll`** (daily, cheap): one JSON:API index page per country — any filings `date_added` since last poll? On delta → trigger **`corpus_refresh`** for the delta only (existing adapters + manifest; refuse store merge if extraction rate < 95% of indexed or filing count drops >20% vs prior). Weekly full-reconciliation crawl stays as the drift backstop. This is also how filing season handles itself: the poll fires daily in June for Japan, spring for Nordics, without a seasonal config. Feed-lag flags (SE/NO/PL) carried into every downstream row — already done, keep.
2. **`screen_runner`** (on corpus delta + a daily price-only re-mark of the existing shortlist, cached batch quote, no crawl): fix the three filed defects *in code* (lease-liability tags into `ncash_r`+FCF; `ncash_r=None` when no debt-side tag — never default missing debt to zero; `one_off_suspect` when |ΔEBIT|>50% on <10% Δrev). Emit shortlist + **machine diff**: new entrants after the exclusion join (ledger fams ∪ resting-order fams ∪ batch history) → `data/batch_candidates_{geo}.json`, with **hysteresis** — a name enters the candidate queue only on crossing the rank/score threshold by a buffer and holding it across two marks (no churn from ±3% price noise). The FDM.L resting-ladder catch becomes code, not vigilance.
3. **`trap_verifier`** (triggered at ≥6 candidates or 30d staleness): S3 dispatch of the batch-2 template (trap catalog + per-name priors slot). Output: per-name verdict JSONs + assembled `EUROPE_TRAP_BATCH{n}.md` (generated, not hand-assembled).
4. **`promotion_gate`** (deterministic, same run): Stage-2 → ledger upsert (S1 merge) with sleeve+source; WATCH → ledger + **mandatory pack** (refuse promotion without a dated gate — S4.1 makes the gap impossible, this makes it not even transient); AVOID(artifact) → S5 defect entry; AVOID(company) → ledger with thesis.
5. **Stage-2 / court** stays human-triggered (doctrine: generator never grades itself; courts need the user checkpoint) but consumes the queue from the ledger state, and court outputs land as edge_classification files via S1.
6. **Calibration hook**: starter entries from this pipeline get cohort tag `small_orphan` in the calibration ledger at entry — the N≥20 evidence accrues as a byproduct.

**Failure modes handled**: yahoo rate limits (pace + fail-loud, the broken_print_radar pattern); partial corpus (gate 1); agent hallucination (output validator + citation floor); duplicate promotion (S1 merge keys); silent universe drift (manifest diffs).
**Tests**: KSL/VERK/CARD/Tokmanni become golden regression fixtures for screen math — every caught bug is a permanent test. Validator unit tests per schema.

---

## Pipeline 2 — Class-dislocation refutability engine

**Current**: `broken_print_radar` (whole-tape single-day breaks, triage-only, hard-won operational notes), `dislocation_sweep` (known-name re-underwrite), `discovery_state` conditioning, courts manual. Missing: the CLASS lens — nothing detects "one narrative just repriced an entire cohort" (saaspocalypse, muni-headline pattern).

**Target flow**:
1. **`cohort_map`** (`knowledge_graph/` extension, refreshed weekly): name → cohorts (sector/industry from existing universe files + hand-curated narrative cohorts: `agentic_saas_exposed`, `gtc_ladder_smallcaps`, etc.). Curated cohorts are versioned data, not code.
2. **`class_derate_detector`** (daily, after close; extends broken_print_radar's store discipline): per cohort compute median drawdown from trailing high, cross-sectional dispersion, and **market-residual** (cohort move minus beta×index — the beta-bleed guard: an indiscriminate class de-rate has LOW dispersion and HIGH residual). Fire → `class_dislocation_event` (S1 store, merge by cohort+window) with member list + narrative anchor requirement (attention/news spike via existing attention connectors; no anchor = flag as UNEXPLAINED, don't suppress).
3. **`refutability_triage`** (S3 agent step, per member, the saaspocalypse template): identify the bear claim; classify `damage_absent | damage_arriving | structural`; name the **data test** (the cRPO-style metric that refutes or confirms) + its next print date; cite current values. Validator: classification requires a named metric with a date — no metric, no classification.
4. **`dispersion_ranker`** (deterministic): rank members refutable+damage-absent first; auto-wire a resolution pack per named data test (the HUBS-Q3-gate pattern, generated); route top-K to the court queue. Sizing doctrine attaches at court, not here — capacity-uncapped ≠ conviction-uncapped.
5. **Grading**: every fired event gets a 90d outcome row (did dispersion realize? did damage-absent outperform damage-arriving?) → calibration cohort `class_dislocation`. The detector earns its keep empirically or dies like MAUDE-velocity did.

**Failure modes**: beta selloffs (residual gate); degraded discovery_state (verify analyst-count freshness before trusting UNDISCOVERED); narrative anchor hindsight bias (anchor must be dated ≤ window start); cohort-map staleness (weekly refresh + member-count sanity).

---

## Pipeline 3 — Trigger conversion + classification hygiene

**Current**: resolution_packs consumed by calendar/grader; headless_grader on launchd (Keychain-reachable, fail-fast auth); edge_classifications at ~2/3 coverage of held names; consistency_check detects-and-routes.

**Target**:
1. **Pack lifecycle states** in the pack schema: `armed → due → adjudicated → branch_executed | expired`. Grader stamps transitions; S4.3 catches stuck packs. Branch execution stays human (orders) but the *branch decision* is recorded even when the action is "did nothing" — unexecuted branches are the missed-entry ledger's input.
2. **Miss taxonomy**: graded outcomes carry `miss_type` (`unwired_tripwire` — STEM's class, `late_adjudication`, `wrong_branch`, `execution_gap`). You can't reduce a failure class you don't count.
3. **`classification_sweep`** (weekly + backlog run now): held positions without edge_type → S3 court-lite classification template (cheap tier) → edge file via S1; output feeds S4.2. Backlog: the 16 unclassified names (~$133k).
4. **Surfacing**: packs due ≤7d land in morning_brief + the positions board's next-date column (already wired); CRITICAL invariant failures push-notify.

---

## Court & staging components (PRD §Courts, §Execution staging — added in reconciliation 2026-08-06)
- **Pitch docs** (`dd_reports/pitch_{TICKER}_{date}.md`): rendered from a versioned template (S3); the four panes map to edge-classification fields (`we_believe`/`market_believes` exist; add `edge_claim`/`priced_in`). Invariant S4.6: ledger verdict with `court` set and date ≥ 2026-08-06 ⇒ pitch doc on file.
- **AI-queue stager** (`desk/queue_stager.py`): reads court-approved envelopes (entry_plan + edge classifications), diffs against current AI-queue instructions, emits create/withdraw actions. **Auth constraint (July rail test): the AI-instructions panel is fed ONLY by the claude.ai IBKR connector (interactive auth) — headless cron cannot call it.** Design: the stager computes a deterministic *staging plan* file (`desk/data/staging_plan.json`, S1 store); a session lane or scheduled cloud agent executes the plan through the connector and marks each action done. The plan file is the audit log; consistency_check flags plans unexecuted >24h. LIMIT-only, venue-ccy rails, provenance (court date, pack id) on every instruction; TCA ledger rows at staging and fill.

## Observability: metrics + email monitoring (PRD success metrics need a computer)
- **`desk/pipeline_metrics.py`** (cron, 2x/day): computes the PRD metric set — P1: % WATCH/STAGE2 with future-dated packs, candidate-queue depth+age, batch advance rates by batch, artifact-AVOID rate; P2: events fired / triaged ≤48h (once the detector exists); P3: unclassified held cost $, pack adjudication latency p90, miss-taxonomy counts; cross: store-write failures, manifest gaps. Output `desk/data/pipeline_metrics.json` (S1 store, history-keeping: one snapshot row per run, merge by date) + served at `/api/pipeline_metrics` and rendered on the /health board.
- **`desk/pipeline_monitor.py`** (cron, hourly): reads consistency_check CRITICALs + metrics deltas; emails via `desk.mailer` with two channels: **IMMEDIATE** (new CRITICAL invariant breach, store-write failure, staging plan unexecuted >24h) rate-limited to one email per breach-key per 24h (the alarm-rate-limit lesson from the grader), and **WEEKLY DIGEST** (Monday: metric trends, defect-ledger aging, batch stats, cohort P&L snapshots). Silence is never success: the digest reports "0 checks ran" as a failure if the metrics file is stale (RX.4).

## Migration order (each step ships alone, value-first)
1. **S4 invariants + S5 defect ledger** (~1 day): catches today's leak classes immediately, zero new architecture.
2. **S1 store contract on the top-5 stores + schemas** (~1-2 days).
3. **Screen defect fixes + golden fixtures** (pipeline 1 stage 2; ~1 day): the next Europe/Japan batch runs on corrected math.
4. **S3 agent-step protocol + trap_verifier/promotion_gate** (~2-3 days): batch N+1 runs end-to-end from the registry, session-optional.
5. **Pipeline 3 lifecycle + classification backlog** (~1 day).
6. **Pipeline 2 cohort_map + detector** (~2-3 days), triage template after the first live fire.
7. Run manifests (S2) accrete alongside each of the above, not as a separate project.

**Non-goals (deliberate)**: no queue/broker infra (cron + launchd + files is the operating model and it's fine at this scale); no DB migration (JSON stores + S1 contract); no automation of court verdicts; no order EXECUTION (Rung 0.5: pipelines stage instructions to the AI queue per the PRD; the principal executes each order; transmitting executable orders stays out of scope until Rung-1 gates are met).


## Court conveyor v2 — the evidence/deck/sensor layer (added 2026-08-08)

Components added in the 08-07/08 hardening sessions, mapped to their PRD rules:

**Transport (the Keychain lesson, second instance):** `court_runner` runs under launchd
(`com.signalos.court-runner`, hourly, RunAtLoad), NOT cron — the cron path had 13/13 auth
failures and zero dispatches ever, because `claude -p`'s credential lives in the login
Keychain. Any future module that shells the CLI gets a LaunchAgent, never a crontab line.
The registry invocation remains as a harmless fail-fast.

**Evidence pack (R1.10):** `court_evidence.build_pack` — deterministic per-ticker machine
layer (EDGAR filing inventory, audited XBRL quarterly series, dual-anchor tape [dd52 AND
pct-off-low], print date w/ confidence label, the desk's ACTUAL book state) prepended to
EVERY stage's prompt (trap-verify, refutability, red, blue). Both benches receive the
identical pack; the validator requires PACK acknowledgment; contradicting the pack demands
a cited primary. Rationale: the 08-07 campaign's blue-bench overturns were ~all
machine-layer errors (grep artifacts, stale anchors, SBC double-counts, phantom positions).

**Retry-with-feedback:** validator rejections are recorded on the queue item and injected
into the next render ("your prior attempt failed on X") — proven on ET/LMT/SAAB. Blind
retry is purgatory; feedback converges in one pass.

**Deck-on-completion (RC.7):** after any COURT_BLUE success, `deck_writer` synthesizes the
full pitch deck (headless court-model pass over red + blue + evidence pack + the
armed-sensors snapshot), validates REQUIRED sections (four panes, what-we-checked incl.
own-bench errors, PROPOSED ENTRY BANDS, ARMED SENSORS, unverified), renders PDF, and
EMAILS it (attachment) labeled PROPOSED — PENDING ADJUDICATION. Incomplete decks are
saved raw, never emailed. Session adjudication (auto, unprompted — standing behavior
2026-08-08) ratifies or amends.

**Instrumentation doctrine (the FLAT-sensors rule):** a gate without a sensor is
decoration. Every adjudication price gate is armed in `research_ledger.alert_below`
(band_watch → sentinel rail: macOS + ntfy + EMAIL, ~15-min class); event gates go to
`filing_watch` (same rail); slow gates get dedicated samplers routed through the monitor
rail (hourly email, 24h dedup, PRINCIPAL/DESK routing): `fungibility_watch` (dual-listing
spreads = capital-controls gauge, 06:40 daily), `usdc_supply_watch` (CRCL's 72B/21d gate,
06:45 daily), `order_hygiene` (resting-order × print-date, the NATR rule, hourly).

**Candidate manufacture:** `convert_screener` (weekly, Mon 07:15) — EDGAR-FTS convert
universe → terms/busted/control extraction → accessibility-first scoring (private
placements and company-option PIK are score poisons — the FUBO lesson) → auto-enqueue
top-K to TRAP_VERIFY. `dataroom_dd` (R4.1) — the same stage discipline for delivered
data rooms (inventory → extraction → external battery → bench → render).

**Runner hygiene:** per-watch fault isolation in `desk/runner.py` (one malformed registry
entry must never decapitate the belt — 25/113 entries lacked keys and were silently
killing every later watch); court_runner geo branches now include US (bare tickers were
falling into the EU trap catalog).
