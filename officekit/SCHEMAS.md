# Schema Reference — Every JSON the Platform Emits

**2026-09-13 contract supplement:** the reconciliation report, per-account custody
provenance, and broker-owned-sleeve metadata are now formally specified as
**contract 12** below; the staging coverage envelope, fixed-horizon grade fields,
and frozen paired-evaluation inputs live in
[OPERATING_CONTRACTS.md](OPERATING_CONTRACTS.md). Existing imports without coverage
metadata are partial; no destructive migration is required.

Companion to [PRD v1.2](PRD.md) · v1.9 · 2026-09-04 · authority note: **code is canonical** (`officekit/schema.py` validates; this doc describes). This is the seam ARCHITECTURE.md calls the schema registry — the contracts that make local↔hosted graduation a transport problem.

**The inventory.** Twelve contracts, three tiers of durability:

| # | Contract | File / transport | Written by | Read by |
|---|---|---|---|---|
| 1 | **Answers** (intake) | `answers.json` | wizard, serve form, LLM intake agent, mandate endpoints | `build_from_answers` |
| 2 | **BalanceSheet v1** | `balance_sheet.json` | intake only (never hand-edited downstream) | `build_model`, all three renderers |
| 3 | **Goals** | inside #1/#2 | user's mouth only | goals engine, scenario planner |
| 4 | **Scenario overlay** | inside #1/#2 | client data / principal / (proposed: agent) | `scenarios_for` |
| 5 | **Strategy decisions + origins** | inside #1/#2 | `mandates.create_adhoc` / `adopt_from_scenario` | strategies renderer |
| 6 | **SyncSnapshot + freshness** | in-memory (connector return) | registered connectors | `sync.apply`, office badges |
| 7 | **Learning ledger** | `learning.jsonl` (append-only) | `learning.observe` | future grading; `export_shareable` for phone-home |
| 8 | **Harvest feed** | in-memory (injected) | desk `_load_harvest` (or any TLH engine) | `build_model` tax reserve |
| 9 | **Personal context** (plane 2) | `personal_context.json` | onboarding (empty skeleton), then the tenant | every shipped agent (mandatory), `check_exclusions` |
| 10 | **Model slots** (BYOM) | `models.json` (optional — defaults apply) | the tenant | `officekit_ai.models` — every AI capability |
| 11 | **Adjudications** (Q6) | `adjudications.jsonl` (append-only) | `officekit_ai.court.run_court` | strategy cards, holdings refs, the two-way exchange |
| 12 | **Reconciliation + custody** | inside #1/#2 (`positions.rows[].accounts[]`, `sleeve.meta.custody_key`, `answers.reconciliation`) | `reconciliation.reconcile` via `sync_office_from_staging` | office rows, Imports page audit block |

**Identity (multitenant, v1.1).** Every durable document carries a GUID trail so N offices can share one store without collisions:

- **`office_id`** — one UUID per office, minted by intake on first build and written back into `answers.json` (so every rebuild keeps it), stamped at the root of both `answers.json` and `balance_sheet.json` and onto every learning-ledger record. It is the tenant-side join key for everything an office ever emits.
- **Per-goal `id`** — UUID minted at intake. Goal *grading over time* must survive goals being reordered, relabeled, or deleted; ledger `goal_status` payloads now carry it (the positional `i` is kept for back-compat but `id` is authoritative).
- **Per-record `id`** — UUID on every learning-ledger record, so hosted-tier upload/ingest is idempotent (dedupe by record id, not by content hash).

Deliberately **not** GUID-stamped: SyncSnapshots and the harvest feed (runtime-injected into an already-identified document — transport carries the tenant), strategy decisions (keyed by stable strategy slug inside an identified document), and rendered pages (no GUID ever renders — goldens stay byte-stable). All ids are `uuid4`; `schema.validate()` checks the format when present; pre-GUID folders stay valid and upgrade in place on their next build.

Dev-only: the demo recorder emits `<video>.cues.json` (`[[label, seconds], …]`) for the narration pipeline — tooling, not a product contract. Shipped with AI-1 (2026-09-04): `fund_map_learned.json` — the office-local cache of human-CONFIRMED symbol mappings `{SYM: [category, style|null]}`; the durable copy also lives in `answers["fund_map"]` so rebuilds re-classify identically with no model in the loop.

---

## 1 · Answers — the intake contract

The simplified shape every onboarding door writes (wizard interview, serve form, agent per INTAKE_AGENT.md). No betas (priors are assigned), debts positive (intake negates). Saved to the office folder so every build is reproducible.

```json
{
  "office_id": "1f6b…-uuid",                // minted by intake on first build; stable forever after
  "owner": "Maya",                          // optional — no name, no fabricated greeting
  "as_of": "2026-09-03",
  "profile": {"net_buyer": true, "uses_leverage": false, "premium_selling_allowed": false,
              "decumulating": false, "concentrated_low_basis": true},
  "sleeves": [
    {"category": "real_estate", "name": "Home", "value": 750000, "confidence": "tbd"},
    {"category": "real_estate_debt", "name": "Mortgage (5.9% fixed)", "value": 380000, "rate_pct": 5.9},
    {"category": "public_equity", "value": 300000, "style": "intl", "target_pct": 12,
     "strategies": ["core_equity"], "holdings": [], "risks": [], "eta": null, "meta": {}}
  ],
  "imports":   [{"kind": "positions_csv", "path": "positions.csv", "account": "Fidelity brokerage"}],
  "positions": {"account": "brokerage", "rows": [{"symbol": "VTI", "value": 251000}]},
  "income":    {"annual": 280000, "years": 25, "style": "equity_linked",
                "until": null, "discount": 0.04, "label": null},
  "incoming":  {"amount": 250000, "eta": "Dec", "character": "ordinary", "rate": 0.42,
                "taxable_fraction": 1.0, "harvest_losses": 0},
  "fund_map": {"VWLUX": ["municipal_credit", null]},   // human-CONFIRMED symbol mappings (AI-1) — overrides the built-in table
  "goals": [],                              // contract #3
  "scenarios": {},                          // contract #4 (passthrough)
  "strategy_decisions": {}                  // contract #5 (passthrough)
}
```

Semantics worth naming: `positions` rows run the **same classifier as the CSV** (fund map, ≥20% concentration split, pooling); `income` capitalizes to a `human_capital` sleeve (PV annuity at `discount`, default 4% real, capped 45y) tagged `assumption`; `incoming` becomes a `cash_pending` sleeve + a flat-mode tax model recording **only** the rate matching `character` (never the unused one); sleeve `confidence` ∈ `known | assumption | tbd`.

---

## 2 · BalanceSheet v1 — the product boundary

Everything downstream reads only this. `validate()` in `officekit/schema.py` is the gate; intake refuses to emit an invalid sheet.

**Required keys:** `office_id` (UUID, optional pre-v1.1 / required at the hosted tier) · `as_of` · `factors[]` (display order; the 6 defaults: S&P 500, Venture Capital, Mortgage Debt, Inflation, Rates, USD) · `sleeves[]` · `profile{}` (5 bools).

**Sleeve** — the asset contract:

```json
{
  "name": "Parametric Tech Direct-Index (131/31)",
  "kind": "asset",                          // asset | liability (liability value must be ≤ 0)
  "category": "direct_index",               // 13 categories incl. human_capital, tax_reserve
  "value": 9029897,
  "target_pct": 30,                         // null = "no target" honestly
  "_confidence": "known",                   // known | assumption | tbd
  "risks": ["…"],
  "beta": {"S&P 500": 1.15, "Rates": -0.35},   // FACTOR loadings — see note below
  "short": "Parametric",                    // card/matrix label (else first word)
  "eta": "Sept",                            // cash_pending only — the landing label
  "strategies": ["direct_index", "harvest_engine"],   // strategy membership — see note below
  "strategy": "direct_index",               // legacy singular form of strategies[]
  "meta": {"gross_long": 11850000, "gross_short": -2820000,
           "embedded_gain_pct": 0.159, "rate_pct": 2.5},   // effect/mitigation inputs — absent ⇒ effects decline to fire
  "holdings": [{"company": "DSGX", "amount": 40000,
                "strategies": ["custom_japan"],        // holding-level membership (finer than the sleeve)
                "adjudication": {"verdict": "STARTER 6/10", "date": "2026-08-03",
                                 "ref": "courts_20260803/DSGX"}}],   // verdict is required if adjudication present
  "sync": { "…": "see contract #6 — written by the sync layer, not by intake" }
}
```

**Optional top-level personalization** (all with generic engine defaults): `owner{first_name}` · `category_labels{}` · `opportunities[]` (inbox items; `{icon,title,tone,chip,body,value}` with `{net_txt}/{net_deployable}/{para_pct}` template slots) · `office{liquidity_note_tail}` · `scenario_text{}` (planner prose templates; legacy key `disaster` honored) · `mitigation_labels{opt_id: name}` · `tax_model{}` · `income_streams[]` (informational only — superseded by income-as-asset) · `goals[]` · `scenarios{}` · `strategy_decisions{}`.

**Strategy membership is many-to-many and whole-asset** (principal ruling 2026-09-04): strategies are *views* over the one asset pool, not containers that partition it. An asset can serve several strategies at once (T&D is Japan value AND the steepener; SGOV is cash management AND CSP collateral), so `strategies[]` lists every mandate an asset serves — at the sleeve level, or on an individual holding when membership is finer than the sleeve. Edges never carry fractions; if a sleeve is genuinely split between mandates, split the sleeve. Explicit tags are authoritative; category match survives only as a fallback for strategies with no explicit member, over sleeves carrying no tags at all. Per-view rollups (value, value-weighted factor betas — holdings ride their parent sleeve's loadings) may legitimately sum past 100% of NW across strategies; NW itself never rolls up from strategies, only from sleeves.

**Why `beta` is a factor vector, not an asset×asset matrix:** each sleeve stores only its loadings on the 6 shared factors. The full asset-to-asset beta matrix (`beta[i][j]` = beta of sleeve *i* to sleeve *j*, what the office matrix page shows) is **derived at build time** in `model._pairwise` as B·Corr·Bᵀ over `FACTOR_CORR` plus per-category idiosyncratic variance. Storing K loadings instead of N² pairwise numbers keeps the contract O(N), makes every new sleeve immediately comparable to every existing one, and means the matrix can never drift out of consistency with its inputs. The pairwise matrix is runtime model output and is never emitted as JSON.

**tax_model** (two modes): flat — `{incoming_gross, character, rate_ltcg | rate_ordinary, taxable_fraction, harvest_losses_2026}`; progression (the desk) — adds `{harvest_mode: "progression", harvest_auto, harvest_realized_ytd, harvest_daily_rate, harvest_project_from/to, harvest_pre_coverage_adj}`, overridden live by contract #8. The model *injects* a `tax_reserve` liability sleeve at build time — it is computed state, never authored.

**Runtime-only fields** (computed in `build_model`, never persisted): `_short`, `_sync_age`, `_sync_stale`.

---

## 3 · Goals

```json
[
  {"id": "9c2e…-uuid", "kind": "retirement", "label": "Retirement", "date": "2052-01-01", "annual_spending": 110000},
  {"kind": "spending",        "label": "College fund",    "date": "2040-09-01", "amount": 250000},
  {"kind": "liquidity_floor", "label": "Emergency floor", "amount": 50000}
]
```

`kind` ∈ `retirement | spending | liquidity_floor` (extend from user feedback, per the ratified ruling). Validation: retirement needs numeric `annual_spending`; spending/floor need numeric `amount`; `date` is `YYYY-MM-DD`. Semantics: labels carry meaning (education/philanthropy = `spending` with a label); statuses (`OK/TIGHT/SHORT` + ratio) are **computed, never stored** — the office scores today, the planner scores per scenario, and only the learning ledger (#7) persists them as observations. `id` (UUID, minted at intake) is the goal’s durable identity — ledger observations key on it, so grading survives reorder/rename. Goals come from the user's mouth — the agent contract forbids inferring them from documents.

**Lifecycle (the goals door, 2026-09-04):** goals are editable post-onboarding — the office page renders an editor when the host app passes `goals_endpoint` (serve wires `/goals`). Identity rules: an edited row keeps its `id` (ledger `goal_status` grading history spans the change), a removed row is dropped, a new row gets a fresh UUID at build. `GOAL_LIB` in `officekit/goals.py` ships ~14 sample goals (college, down payment, sabbatical, parents' care, philanthropy, …) as editor quick-adds — every sample maps to an existing kind with the label carrying the meaning; amounts/horizons are starting points the user edits, and a goal exists only once the user commits it.

---

## 4 · Scenario overlay (+ scenario object)

Client data personalizes the neutral library:

```json
{"scenarios": {
  "replace": {"tech": {"desc": "…", "fix": {"tag": "DILUTE + TRIM", "action": "…"}}},
  "drop":    ["housing"],
  "add":     [{
    "key": "new_kid", "ic": "👶", "name": "Having a kid",
    "desc": "…", "p": 0.5, "p_basis": "…", "tripwires": ["…"],
    "shocks": {"S&P 500": -0.05},           // factor shocks (Rates 0.12 ≈ +200bp)
    "cat_ov": {"human_capital": -0.5},      // per-category idiosyncratic override
    "name_ov": {"GOOGL": -0.30},            // substring match on sleeve name
    "tax_ov": {"no_offset": true},          // reserve snaps net → gross
    "goal_ov": {"add": [{"kind": "spending", "label": "College — second kid", "amount": 300000}],
                "modify": [{"kind": "retirement", "annual_spending_delta": 30000}]},
    "requires": "human_capital",            // data gate: tax_offset | human_capital
    "opts": ["term_life", "cash_buffer"],   // mitigation ids → OPT catalog
    "fix": {"tag": "INSURE / HOLD", "action": "…"}
  }]
}}
```

Scenario fields shipped in the library that clients can also override: `p` / `p_basis` (annualized probability + its argument — every render freezes these to the ledger as pre-registered calls) and `tripwires[]` ("what says this is starting" chips). Life-event scenarios are client-added, never library defaults.

---

## 5 · Strategy decisions + mandate origins

```json
{"strategy_decisions": {
  "index_hedge": {"status": "declined",
                  "note": "Net-buyer doctrine: no index insurance while cash-rich…",
                  "origins": [{"source": "principal", "ref": "Index hedge overlay", "date": "2026-09-02"}]},
  "insurance_program": {"status": "planned",
                        "origins": [{"source": "scenario", "ref": "income_shock/disability_ins", "date": "2026-09-03"}]},
  "japan_value": {"status": "considering", "target_pct": 4,
                  "title": "Japan value", "desc": "…", "subassets": ["cash-fortress nets"], "ic": "✳️",
                  "origins": [{"source": "principal", "ref": "Japan value", "date": "2026-09-03"}]}
}}
```

`status` ∈ `implemented | considering | planned | declined` (schema-validated). No entry and no matching sleeve = rendered **NOT DECIDED** — never inferred. A key outside `STRATEGY_LIB` is a **custom strategy** whose `title/desc/subassets/ic/category` live in the decision itself. `origins[]` is the mandate paper trail — `source` ∈ `principal | scenario | agent | goal` (schema-validated). The `goal` source (`officekit/goal_mandates.py`) is the deterministic goal→strategy decomposition — funding requirement → gap posture → horizon menu → sized proposal, `ref = <goal_id>` (why goals carry GUIDs), idempotent per (strategy, goal). **UX ruling 2026-09-04: goals OFFER a menu, nothing auto-queues** — `goal_strategy_menu` presents a handful of options per goal (primary first, tax-state-aware) on the strategies page taxonomy (goal → strategy → assets), and the user's Adopt click files the chosen pairing via `proposal_for` + `queue_goal_proposals`. The goal↔strategy **association is derived, never stored**: `goal_coverage(m)` resolves the origin edges at read time into both directions — the office shows "→ served by …" under each goal, strategy cards show "Serving goals" with the **aggregated** mandated % (claims summed across every live goal referencing the strategy — deleted goals stay on the trail as history but drop out of coverage). One derivation, both surfaces, no dual-write to drift. The `agent` source is queue-only by construction: `queue_agent_proposal` can only file `considering`, never touches an existing status, and its `ref` is the frozen `agent_call` ledger-record id. Rules encoded in `mandates.py`: adoption never downgrades a status; every action appends an origin.

---

## 6 · SyncSnapshot + freshness stamps

What any custody connector returns (raise on failure — never a silent absence):

```json
{"as_of": "2026-09-02",
 "provenance": "gross positions MV, 93 positions, generated 2026-09-02T18:35Z (positions_board.json)",
 "updates": [{"match": {"category": "alpha_market_neutral"},   // and/or {"name_contains": "…"} — first match wins
              "value": 931473.33, "holdings": null}]}
```

`sync.apply` writes the matched sleeve's value in memory and stamps it:

```json
{"sync": {"connector": "ibkr_positions_board", "as_of": "2026-09-02",
          "provenance": "…", "max_age_days": 2}}
```

…and returns a report row per connector: `{connector, label, status: FRESH|STALE|ERROR|WARN, as_of, age_days, detail}` (WARN = an update matched no sleeve). The JSON balance sheet stays the manual base layer; sync is a live overlay with degrade-loud badges.

---

## 7 · Learning ledger records

Append-only JSONL, one record per kind per day, **born multi-tenant**: every record carries `v` (schema version, currently 1), a per-record `id` (upload dedupe), `tenant`, and the emitting `office_id`.

```json
{"v": 1, "id": "7d41…-uuid", "tenant": "local", "office_id": "1f6b…-uuid",
 "kind": "snapshot", "date": "2026-09-02", "ts": "2026-09-02T13:15:43",
 "payload": {"cat_weights": {"direct_index": 43.7, "cash": 3.8},
             "agg_beta": {"S&P 500": 0.72}, "nw_decade": 7, "n_sleeves": 14,
             "sync": {"n": 2, "stale": 1}}}

{"v": 1, "tenant": "local", "kind": "scenario_run", "date": "2026-09-02", "ts": "…",
 "payload": {"dd_pct": {"tech": -26.48, "taxbomb": -2.97}, "p": {"tech": 0.06}, "worst": "tech"}}

{"v": 1, "tenant": "local", "kind": "goal_status", "date": "2026-09-02", "ts": "…",
 "payload": {"goals": [{"i": 0, "id": "9c2e…-uuid", "kind": "retirement", "status": "OK", "ratio": 1.8}]}}
```

Payloads are **born shareable** — category weights, betas, ratios, a net-worth log-decade (`nw_decade`), never names/dollars/tickers. `export_shareable()`'s per-kind field allowlist is the phone-home contract and the only sanctioned exit path (enforced by a leak test; re-enforced server-side in the hosted tier). Fourth kind (ratified 2026-09-04): `agent_call` — a frozen intelligence-plugin claim `{capability, model, …}` whose record id is the `ref` on agent-origin mandates; deliberately **excluded** from the shareable allowlist because payloads may carry client-specific text.

---

## 8 · Harvest feed (injected)

The one contract that's an *input* the package never reads from disk itself — a live tax-loss-harvesting snapshot the caller injects into `build_model(data, harvest=…)`:

```json
{"net": -162046, "loss": 162046.0, "asof": "2026-07-07",
 "coverage_start": "2026-06-12", "coverage_days": 25, "daily_rate": 6482.0}
```

When present (and the tax model is progression-mode with `harvest_auto`), it overrides the static harvest figures so the tax reserve tracks reality. The desk feeds it from the Parametric scorecard; any TLH engine can implement it.

---

## 9 · Personal context — plane 2 as a contract

The tenant's own constraints, made structural (ruling 2026-09-04: personal context never ships as content, **always ships as structure**). Onboarding writes the empty-but-asserted skeleton; the tenant fills it; every shipped agent loads it before advising — `personal_context.require()` refuses on absence (empty passes: the tenant asserted "no constraints").

```json
{"office_id": "1f6b…-uuid", "v": 1,
 "exclusions": [{"scope": "issuer", "value": "ACME",
                 "reason": "employer — excluded from every book (employment conflict)", "date": "2026-09-04"}],
 "jurisdictions": {"tax_state": "CA", "country": "US"},
 "doctrine": [{"id": "no_premium_selling_taxable",
               "rule": "No premium selling in taxable except the three ratified templates…", "date": "2026-09-04"}],
 "external": [{"name": "VCLAX (household ballast)", "why": "held outside this office — never duplicate"}],
 "notes": ["…"]}
```

`exclusions[]` (`scope` ∈ `ticker | issuer | sector`) are enforced **in code**: `check_exclusions(data, pc)` flags any sleeve or holding matching an excluded ticker/issuer at build time (sector scopes are advisory — agents enforce them; code has no sector map). `doctrine[]` entries are the principal's standing rulings in plain language, cited by id whenever a ruling shapes an agent's answer. `external[]` names coordination surfaces outside the office (wash-sale checks, exposure a spouse's account already carries).

**Privacy + hosted tier**: this is the most personal document an office emits. It never enters the learning ledger, never passes `export_shareable()`, and on `officekit link` it uploads **with** the folder as the tenant's own envelope-encrypted document — the hosted agents need it there for exactly the same plane-2 gate, but the cross-tenant learning store never sees it.

---

## 10 · Model slots — bring-your-own-model as a contract

The Q2 ruling's BYOM role slots, as a document. Optional — no `models.json` means the zero-config default (the built-in `anthropic` provider keyed by the `ANTHROPIC_API_KEY` env var, Haiku for classify, Opus for intake).

```json
{"v": 1,
 "providers": {"anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
               "local":     {"api_key_env": "MY_LOCAL_KEY", "base_url": "http://localhost:8000"}},
 "slots": {"classify": {"provider": "local", "model": "my-model-7b"},
           "intake":   {"provider": "anthropic", "model": "claude-opus-5"}}}
```

Slots: `classify | intake | bench | adjudicate | verify` (the last three activate with the unified-layer courts; their ordering constraints — adjudicator never weaker than bench, generator never grades itself — are the U2 enforcement work). Providers are a registry (`@provider("name")`, same pattern as sync connectors): `anthropic` ships built in; a community OpenAI/local provider is a plugin returning a client that speaks `messages.create` with structured outputs. Unnamed slots and providers fall back to the defaults.

**The load-bearing rule: secrets never enter the document.** Providers reference credentials by environment-variable **name** (`api_key_env`); a `models.json` carrying actual key material (`api_key`, `token`, …) is **rejected loudly** at load. That is what keeps this document uploadable at `officekit link` like every other contract — the hosted tier gets your slot topology, never your keys.

---

## 11 · Adjudications — every pick carries its deliberation (Q6)

Ruled 2026-09-04: adjudications are generated LOCALLY, in the context of the strategy that convened the court; connected tenants exchange two-way (send theirs up, read ours down), building cross-tenant adjudication intelligence over all equities.

```json
{"id": "…uuid", "office_id": "…uuid",
 "strategy": "muni",                        // WHICH strategy convened the court
 "symbol": "VTEB", "date": "2026-09-04",    // WHAT and WHEN
 "verdict": "WATCH 7/10 (LITE)",            // LITE = no live connectors; honest label
 "rationale": "…", "decisive_points": ["…"],
 "unverified_items": ["…"],                 // the work queue a full court must verify at primary
 "tier": "flat_tier",                       // U2 runtime label: tiered | flat_tier | unranked
 "models": {"bench": "…", "adjudicate": "…"},
 "refs": {"red": "…", "blue": "…", "adjudicate": "…"}}   // frozen agent_call ids
```

The **exchange allowlist** (`export_shareable_adjudications`) sends only `{id, office_id, strategy, symbol, date, verdict, rationale, tier}` — which strategy built it, which office, and when, per the ruling — never sizes, dollars, or the unverified queue. This is a deliberately **separate sanctioned channel** from the learning ledger: that allowlist bans tickers; this one carries them by design. A recorded purchase copies `{verdict, date, ref}` onto the sleeve holding's `adjudication` field, closing the loop the sleeve schema anticipated. Records also carry `briefs` (the full red/blue adversarial record), rendered per adjudication as a **pitch-deck page** (`pages/deck_<id8>.html`) linked from the taxonomy — every courted asset sits alongside its full deliberation. Briefs stay LOCAL: the exchange allowlist excludes them.

---

## 12 · Reconciliation report + custody ownership

Added 2026-09-13. Scoped custody pulls are reconciled into the office **without
deleting assets a disconnected account still holds** (`officekit/reconciliation.py`,
pure; `sync_office_from_staging` persists only after the office rebuilds). The
collapse keeps **one row per symbol for the view** but records **per-account
ownership** so the owner stays recoverable, and it writes an audit **report** onto
the built document.

**a) `positions.rows[].accounts[]` — custody provenance (on contract 1/2 rows).**
The row's `value`/`cost_basis` are the SUM across accounts (the collapsed view);
`accounts[]` is the per-owner breakdown. A cost-only mark never becomes NAV.
For generic or missing account labels, the persisted `source` participates in
matching contributions for updates, stale marks and closures. An absent row in a
partial pull cannot discard another source's contribution with the same label.
The existing matching policy for non-generic labels is unchanged; inferring
whether those sources describe common ownership remains deferred.

```json
{"symbol": "AAPL", "value": 30000, "cost_basis": 22000,   // collapsed totals (the view)
 "accounts": [                                             // owner provenance (recoverable)
   {"account": "U0000001", "source": "adapter:ibkr_socket", "value": 18000,
    "cost_basis": 14000, "as_of": "2026-09-13", "pulled_utc": "…",
    "value_is_cost": false, "lots": [...], "loss_lt": 0, "loss_st": 0},
   {"account": "…SMA", "source": "adapter:morgan_stanley_bundle", "value": 12000}]}
```

**b) `sleeve.meta.custody_key` / `custody_row` — broker-owned non-equity sleeves.**
Cash / options / fixed-income marks stay their own sleeves. A sleeve minted from a
pull carries `custody_key` = the `staging.position_key` tuple as a list —
`[account, symbol, sec_type, ccy, contract]` (`contract` distinguishes option
strikes/expiries and bonds; empty for plain cash). Generic or missing account
labels append a sixth field, `source_id`, to isolate retained source observations
(2026-09-14). Existing five-field keys recover it from saved `custody_row`
provenance during reconciliation. `custody_row` is the source row that set the
mark, used for freshness and source-scoped closure. A sleeve **without**
`custody_key` is MANUAL — the reconciler never overwrites or double-books it, and
requires explicit review before a pull may create a same-category sleeve.

**c) `answers.reconciliation` — the audit report** (also returned by `reconcile`),
stamped on `answers.json`/`balance_sheet.json` after every sync and rendered on the
Imports page:

```json
{"changed": 3, "added": 1, "removed": 0,
 "warnings": ["Ownership review required for X: …", "Retained newer mark for Y in …"],
 "closed": [{"symbol": "Z", "account": "U…", "source": "adapter:broker",
             "security_type": "equity"}]}
```

`security_type` is `"equity"` for a position closure or the instrument code
(`CASH`/`OPT`/`BOND`/…) for a sleeve closure — **one shape** for both. A position is
`closed` ONLY when a complete, independently-control-totalled snapshot supersedes it
(see the coverage envelope + per-account control-total gate in
[OPERATING_CONTRACTS.md](OPERATING_CONTRACTS.md)); a partial or failed pull never
closes anything. Custody is imported, **never synthesized** from a court verdict.

---

## The office folder — where they live

```
office/
├── answers.json         # contract 1 (incl. 3, 4, 5 passthroughs) — the durable intent
├── balance_sheet.json   # contract 2 (incl. 3, 4, 5 resolved)   — the built artifact
├── personal_context.json# contract 9                            — plane 2: the tenant's constraints
├── adjudications.jsonl  # contract 11                           — every pick's deliberation
├── learning.jsonl       # contract 7                            — the memory
├── positions.csv        # raw upload (kept for rebuild)
├── fund_map_learned.json# AI-1 cache: confirmed symbol mappings (seed for future onboardings)
├── models.json          # contract 10 (optional)                — BYOM slot config, no secrets ever
├── signals_runs.jsonl   # capability run log                    — health derives from this
├── signals_state.json   # watcher cursors (last-seen state)     — stateful watchers only
└── pages/               # office.html · scenarios.html · strategies.html — the rendered product
```

Contracts 6 and 8 are runtime-injected (connectors, harvest feed) and appear only as `sync` stamps and computed reserve figures inside the rendered output — the folder never stores another system's live state, only your own intent and the built result.
# Commitment records — 2026-09-14

Receipt update: `answers.inflow_events` holds immutable `receipt` and `reversal`
events. Receipts contain `id`, `inflow_id`, `gross`, `withheld`, `date`,
`account_id`, `reference`, `evidence` (account/source/balance/as_of/custody key),
and `recorded_at`. Reversals contain `id`, `inflow_id`, `reverses`, `reason`, and
`recorded_at`. `balance_sheet.inflow` is their derived progress, not another
asset. `tax_model.received_gross` and `withheld` drive partial tax allocation;
liability `meta.pending_tax` bounds the tax funded by pending cash. The original
`incoming.amount` remains total expected proceeds. See the receipt contract in
[COMMITMENTS.md](COMMITMENTS.md).

Review update: `incoming.id` links the normalized pending sleeve and
`tax_model.inflow_id`; generated tax liabilities preserve it in `meta.inflow_id`.
Only tax with a matching pending asset is excluded from current cash reserves.
Retirement goals now persist `spending_basis` (`household_total`, the default, or
`additional`). Household totals include lifestyle; separate spending is additive.
See [COMMITMENTS.md](COMMITMENTS.md) for the reconciliation and receipt rules.

See [COMMITMENTS.md](COMMITMENTS.md) for semantics. Durable answers may include:

```json
{"commitments": [
  {"id": "implicit:spending:lifestyle", "annual_amount": 200000,
   "funding_source": "portfolio", "cadence": "monthly", "next_due": "2026-10-01"},
  {"id": "<uuid>", "source": "recurring_expense", "label": "School fees",
   "amount": 20000, "cadence": "annual", "next_due": "2026-09-10",
   "funding_source": "portfolio", "provenance": "user confirmed"}
]}
```

Manual sources: `recurring_expense`, `tax`, `capital_call`, `goal_reservation`.
The latter three require `once` cadence. Funding is `portfolio` or `income`;
`amount` is per payment, while derived-record `annual_amount` is per year.
Optional `ends_on` bounds recurrence; `settled` releases a manual schedule.
Mortgage overrides permit monthly scheduling and rate/remaining-term edits;
property-tax overrides permit home value and actual annual-tax edits. Mortgage
`term_years`, `rate_pct`, `terms_as_of` and `property_tax_id` survive sleeve
normalization in metadata. Resolved `balance_sheet.commitments` is generated,
including `status`, `portfolio_funded`, `active` and assumption flags. Never copy
the generated projection wholesale back into answers.

**Strategy proposal contract (2026-09-14):** `strategy_proposals/<uuid>.json` holds the durable job, frozen office/context snapshot, evidence, court references, Risk Officer sizing, pitch and investment basket. Mandates link via `proposal_ids`; reviewed decisions carry `proposal_decision`, with `adopted_proposal_id` retaining the accepted plan. Adjudications may carry `proposal_id` and `subject_kind` (`security` by default, or `options`/`program`); non-security subjects are excluded from equity holdings/grades/exchange. Fields and lifecycle are specified in [STRATEGY_PROPOSALS.md](STRATEGY_PROPOSALS.md).
