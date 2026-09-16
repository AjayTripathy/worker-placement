# Court Doctrine — the adversarial adjudication layer
*2026-08-06 · codifies practice accumulated May–Aug 2026 across THESIS_PIPELINE.md v1.1–v1.5, the tiered-model policy, and ~40 courted names. Companion to `PIPELINE_PRD.md` (courts are the human-checkpointed stage of every pipeline) and `THESIS_PIPELINE.md` (where courts sit in the 11-stage flow). Case citations are the doctrine — each rule below exists because a specific name broke the naive version.*

## What a court is
A court is the **independent adjudication** of a thesis by adversarial benches, with SignalOS as its quantitative analyst. It is not a second opinion or a vibe check: it is the one stage whose job is to be *wrong-seeking* — the generator found reasons to act; the court's product is the strongest case against, the strongest case against THAT, and a verdict that survived both.

**The prime invariant: the generator never grades itself.** A scanner's embedded two-mode check is a first pass, never the court (ADMA: a scan's own court missed the escalation a contested-short name required). This applies recursively — the court tier itself is independent of the finding tier, and a red team never adjudicates its own findings (that's the blue team's job).

## The bench structure — red/blue symmetry
- **Red team** (type-I adversary): prosecute the thesis. Attack every load-bearing number, hunt the base-effect trick, the stale quote, the wrong-NCT-class binding error, the peak-cycle multiple. Default-REJECT posture: the thesis must *earn* survival.
- **Blue team** (type-II adversary): prosecute the red team. Its target is the red case, not the original thesis — every red finding gets the same hostile audit (is the "killer fact" itself an artifact?). III is the canonical case: red killed on "FY25 rev −1.2%"; blue showed that number was itself a divestiture-comp artifact (+7% ex-automation) — **both benches caught one base-effect trick each, one per side**. Without a symmetric blue bench, courts are biased toward type-II error by construction.
- **Adjudication** synthesizes: findings that survived blue, classified through the response taxonomy (below), into a verdict + envelope.
- Benches must be **evenly matched in intelligence** (see escalation). An Opus red team against a Fable blue team (or vice versa) is a rigged court.

## Escalating intelligence — the tier policy (v1.2, user-directed 2026-07-04)
- **Volume tier (Opus)**: Stage-2 DDs, censuses, trap-verification batches, classification sweeps, standing watches. This is where breadth lives; ~8-name parallel batches are the economic unit.
- **Court tier (Fable)**: any red team on a verdict ≥6/10 conviction, or any contested/decisive adjudication — AND its blue team, same tier, always. Escalations of decisive findings likewise.
- **Escalate-on-decisive (the AVIR rule)**: when a single finding would flip the verdict, re-verify that finding with **full context and the stronger model before acting** — a blind spot-check caught the wrong-NCT binding that the volume tier missed. Decisive findings are never acted on at the tier that produced them.
- Cost shape this produces: cheap wide funnel, expensive narrow apex — spend scales with decision weight, not with name count (mirrors PRD RX.6).

## SignalOS as the court's quantitative analyst (v1.3 evidence rule)
Every red and blue dispatch **embeds the verification manifest** (`python3 -m desk.court_toolkit`) and both benches route every load-bearing claim through the matching tool — courts and red teams GENERATE facts; the SignalOS layer AUDITS them:
- **Price/tape claims** → `desk/prices.py` + IBKR bars (compute bands, never quote them; tape-verify the premise — FCT.MI's "−40% day" never happened) + `discovery_state` conditioning (is it already priced/crowded? — overturned the RCAT short).
- **Fundamentals claims** → SEC XBRL / DART audited series direct; `desk/seasonality.py` MANDATORY on any deceleration claim (hard/easy-comp flags); `capacity_check`; cap-structure pull BEFORE any per-share/EV claim (TENX).
- **Physical/operational claims** → satellite buildout, methane, customs BOL, hiring velocity, units-open — the alt-data connectors as ground truth.
- **Gov/legal claims** → primary statute/proclamation text (quote the operative words — the copper lesson), USASpending family rollups, RECAP dockets, EDGAR full-text.
- **Market-structure claims** → futures curves (does the CURVE price it?), FX+WHT math with the metric named (the TEY lesson).
- **The detector library and knowledge graph are the dispatch index**: claims route to detectors by APPLIES_TO contract (recall-floor matchers, three-ring dispatch); a claim no tool covers is **reported as a coverage gap, never silently skipped** — coverage gaps are findings (PL's unverified gov-revenue claim) and Ring-2 detector-invention candidates.
- **Grading rule**: every finding lands as `{claim | tool | data result | CONFIRMED/REFUTED/PLAUSIBLE}`; PLAUSIBLE means no data check ran; **verdicts may rest only on CONFIRMED/REFUTED findings**. The thesis doc renders this as the verification table — a doc without the table is a fact deficiency (v1.5).

## The response taxonomy — findings map to instruments (the category-error guard)
Accepted findings classify by TYPE, and the type determines the instrument — never default to a price gate:
- **Valuation finding** → price gate (the only case that gates entry on price).
- **Business-risk finding** → SIZE cut, not a gate (III again: an enter-after price gate on a business risk = category error; gate conjunction ~5% joint fill = never-own; regret ran 2:1 against gating).
- **Timing finding** → tranche structure.
- **Data-integrity finding** → kill (no instrument fixes a broken premise).
Every WAIT verdict gets blue-teamed (WAIT is a position too — the missed-entry ledger grades it). "Fairly valued" on a quality name is an ENTRY, not a WAIT (TINA rule); RP_FAIR is an ownable class with the edge overlay explicitly labeled NONE.

## The pitch doc (PRD RC.1–RC.4 — the court's mandatory artifact)
No verdict persists without the four panes: **what we believe / what the market believes / why we might have edge / why it's priced in** — plus scenario FVs with market-implied p (edge = ours − implied; bullish-but-priced = FAIR), kill triggers, and the entry envelope. The market-believes pane obeys the same honesty bar as the batch-2 verifiers: the *strongest* opposing case, and premise-refutation of our own brief is a first-class output (three prompt premises died in batch 2; that is the system working). Bond-dominance floors, segment-level flooring, and the conservative-FV double-haircut check (sanity vs the Street's lowest) run in the priced-in pane.

## Selection integrity (the count-goals lesson)
Courts held under count pressure (2/5 rejected when a "find 5" goal was set) but selection/tempo/framing leaked upstream. Rules: no count-shaped goals reach the court queue undisclosed; goal-cohorts are tagged in calibration so the empirics grade whether pressure bends outcomes; diversity constraints on any counted batch.

## After the verdict — the court's outputs are wired, not written
1. **Frozen prediction** (Stage-6 calibration): dated, probability-stamped BEFORE entry; later evidence adjusts sizing only, never the scored number. Cohort tags (`small_orphan`, `class_dislocation`, goal-cohort) ride the frozen row.
2. **Thesis doc** (reader-facing, plain language — claim/method/authority/finding, no detector jargon) with the verification table.
3. **Envelope → AI-queue staging** (PRD RE.1–RE.5): verdict → pitch doc → envelope → instruction; LIMIT-only, provenance-stamped, auto-withdrawn if the verdict is superseded.
4. **Standing forward instrumentation** (v1.5): every court-cleared BUY/STARTER gets its thesis-specific leading indicators stood up the same day (Kalmar: order intake; WAL: uninsured-deposit mix; FSBW: CRE concentration) — the court names what would change its mind, and a watch is built for exactly that.
5. **Resolution packs** for every dated gate the verdict names (P3 invariant: no WATCH without a future-dated pack — the STEM lesson).

## §DIVERGENCE-NOT-COVERAGE (principal-directed 2026-08-17)

**Analyst coverage is a MEASURING INSTRUMENT, not a verdict input. Stop spending tokens establishing
that a name is covered.** Benches have been counting analysts and ruling "8 analysts, Hold, $10.50
target — covered paper, no edge" (MFIC), "fully-discovered" (IBKR), "CROWDED, DILIGENCE-only" (ARE).
That is a category error: coverage says a name is MEASURED, not that it is measured CORRECTLY.

**The product is DIVERGENCE.** The question is never "does the street follow this name" but "what
does the street actually forecast, where do we differ, and WHY". A verdict that cannot state the
street's load-bearing number and ours beside it has not done the work, however many analysts it
counted.

**A covered name is BETTER than an orphan in one decisive respect,** and it is the respect the
mispricing-artifact taxonomy cares about: the street PUBLISHES A NUMBER, which is a genuine
EXTERNAL anchor we can be measurably right or wrong against. In an orphan our fair value is scored
against our own fair value — circular, and the recorded edge is an artifact. So coverage does not
destroy an edge claim; it is what makes one *gradeable*.

RULES:
1. **Never kill on coverage count.** The kill is "WE AGREE WITH THE STREET" — no divergence — not
   "the street exists". State the agreement as the finding if that is the finding.
2. **Extract the street's LOAD-BEARING NUMBER, not its rating.** Consensus revenue/EPS/NAV for the
   specific period the thesis turns on, and the range, not just the mean — dispersion is where a
   divergence lives. A price target is the weakest form of this and rarely the operative number.
3. **State our number against it, with the MECHANISM for the difference.** "Street models X, we
   model Y, because Z" — and Z must be checkable. Anchor-and-adjust applies: a deviation without a
   named mechanism is narrative, not edge.
4. **discovery_state CROWDED conditions SIZE and TIMING, it does not kill an edge.** Crowded means
   both tails are fat and squeeze risk is live — a sizing and tranche instrument per the response
   taxonomy, never a rejection.
5. **The orphan carve-out survives unchanged** (uncovered names cannot be efficiently priced; our
   FV carries a documented ~13% conservative bias) — but it is now the *narrow* case, not the only
   time coverage matters.

Sibling doctrine: the MFT sleeve exists to front-run the ANALYST'S REVISION — the street's number
is the target to diverge from, which is impossible if coverage is treated as a disqualifier.

## §BLUE-CORRECTIONS-AUDITED (batch-5 precedent, 2026-08-15 — the CLSK converts)
A blue-bench CORRECTION of a red number carries the same error risk as the number it replaces, and it arrives wearing the authority of a catch. The pipeline audits red by construction (blue exists to attack it); nothing audits blue. CLSK proved the cost: blue "corrected" red's verbatim-correct $14.80 conversion price to $24.05 with a ratio (41.5584 sh/$1,000) matching neither note series, and demoted a verbatim-correct put date to PLAUSIBLE — a wrong correction that would have propagated straight into the verdict had the adjudicator credited it by default. Rule: **when blue overturns a specific figure red sourced to a primary, the adjudicator re-fetches the primary before crediting the correction.** Same bar in the other direction: SPRY red refuted a basis artifact and replaced it with its mirror-image artifact (total COGS ÷ product-only revenue) — any "the true figure is Y%" replacement gets its numerator/denominator scope checked before Y is credited; mismatched scope → the honest output is NOT_DISCLOSED with a bounded interval.

## Re-courting
A verdict is re-courted (not merely re-dated) when: a kill trigger fires; the catalyst identity changes (bind to the SPECIFIC trial/print — AVIR); the entry basis moves >1 band; or the grading of a sibling cohort name reveals a shared premise error. Re-courts get fresh benches — the original adjudicator is now a generator defending its own verdict and is conflicted by definition. Backups of the superseded classification are kept (`*.bak_<date>_recourt` — the existing convention).

## Failure modes this doctrine exists against (the case law)
| Case | Failure | Rule it produced |
|---|---|---|
| III | red's killer fact was itself an artifact | symmetric blue bench, evenly matched tiers |
| AVIR | decisive finding acted on at volume tier | escalate-on-decisive with full context |
| ADMA | scan graded its own candidates | generator-never-grades-itself, court independence |
| FCT.MI | thesis seeded on a phantom −40% day | tape-verify premises before benches convene |
| RCAT | short thesis ignored crowding | discovery_state conditioning in the manifest |
| TENX | EV claim without cap structure | cap-structure pull before any per-share claim |
| Tokmanni→KSL | screen artifact survived to a verdict | filer-tie + defect ledger; artifacts are OUR findings |
| STEM.L | verdict's tripwire never wired | pack invariant; miss taxonomy `unwired_tripwire` |
| Cosmecca | staged on triage before the court reversed | v1.4: court + thesis doc BEFORE staging, no exceptions |
| SLS | valuation anchored on a stale spot | live IBKR price at court time, always |

**SNFCA (2026-08-07)** — FAIR-CARRY boundary: fair-value-in-the-research-desert is edge ONLY when the carry REACHES minorities. SNFCA: honest 0.697x book inside the justified band + 13% earnings yield, but 36 years of no dividends, $1M buyback cap, comp +48.6% — owner yield ~0.5%. DECLINE. Corollary: a controlled company's dividend initiation is itself a re-court trigger. Also: blue benches may be WAIVED on materiality when exitable size makes the sizing decision <10bps of book — record the waiver in queue history.

**String-artifact error class (2026-08-07, recurring)** — red benches repeatedly convicted on text-search artifacts: WDAY '24-month backlog retired' (grep missed 'next 12 and 24 months'), ASAN 'in-quarter NRR' (metric never existed), TEAM (different company's filing as source), TRIP take-rate seasonal comparison, AGL level-read-as-increment, MNDY stock-vs-flow 7 months apart. RULE: a disclosure-retirement or metric-change kill is INVALID unless the bench quotes the surrounding passage from BOTH periods verbatim; graders check the quote, not the claim. Options term structure is a legitimate print-date locator when no 8-K exists.

**TEAM print-race (2026-08-07)** — a court convened with a known print inside 5 trading days must run the print-decisive reconstruction FIRST (the blue's AR-cycle rebuild used only pre-print filings but was done post-print, after +30%) and file an explicit PRE-PRINT POSITION line. Validator-enforced via the mandatory PRINT PROXIMITY section (templates v3). The $110->$143 leg was a catchable miss; the $143->$126-gate refusal was deliberate and is graded in desk/data/missed_entries.jsonl.

**CAI rung exemption (2026-08-07)** — exit bands rest by default (§6), EXCEPT when the band's anchor is itself in formal dispute: a trim rung tied to a FV the desk has flagged stale (re-rate queued) is SUSPENDED until the court rules — anchoring sells to a number we've disputed is acting on evidence we don't believe. A bull-case ceiling rung stays (unbounded positions still forbidden). Corollary: never trim a line the record says to BUILD unless the FV is trusted or risk changed.

**Evidence-pack doctrine (2026-08-07)** — dataroom/court isomorphism: a company's IR narrative is a seller's data room. The machine layer (inventory, series, anchors, dates, book state) is built ONCE per court by court_evidence.py and shared by both benches; the judgment layer alone is adversarial. A bench spending tokens re-deriving facts is a defect; a bench contradicting the pack without a primary source is invalid.

**CAI reclassification (2026-08-08)** — EXIT MACHINERY FOLLOWS THESIS CLASS: FV trim bands are dislocation/RP_FAIR machinery; GROWTH theses get sharp kill-triggers + a size governor + review-dates (never auto-sell ceilings). Per response taxonomy, business/governance risk (the pledge) maps to SIZE CAP, not price trims. A value-priced ENTRY does not make a growth thesis a value POSITION — classify by the thesis, not the entry luck. Principal-ratified.

## §VERIFICATION-BEFORE-ADVANCE (principal-ratified 2026-08-14 — the MLTX precedent)

No ADVANCE ruling (any new-buy outcome: STARTER / OWNABLE / OWN) ratifies until a **verification
pack** has run on the ruling's decisive findings. The adversarial court tests *arguments*; the
verification pack tests the *numbers the winning argument rests on* — from primary, with the
session's full tooling (sec_fetch, CT.gov, proxy paths), not the benches' constrained reach.

Scope of a pack, minimum: (1) every FATAL/decisive quantitative claim re-derived from the primary
instrument end-to-end (the PGY lesson: red stopped at a subtotal); (2) identity binding for any
catalyst (the AVIR/MLTX lesson: the BLA was a different program than the readout); (3) capacity/
capital claims traced to committed-vs-discretionary language (MLTX: "$400M available" was $0
committed); (4) calendar items restricted to issuer-primary statements. Findings file to
desk/data/court_artifacts/<TICKER>_VERIFICATION_<date>.md; the adjudicator applies the delta —
a ruling the pack downsizes is the system working (MLTX: half → quarter), not a failure.

Enforced mechanically: pipeline_invariants.check_advance_has_verification flags CRITICAL any
post-2026-08-14 ADVANCE verdict with no pack on record. KILL rulings need no pack — the
asymmetric-error doctrine (trust cleans, scrutinize exclusions) already covers the other side
via blue-team review of borderline kills.

## §PRIZE-TABLE (principal-ratified 2026-08-14 — the SLI lesson)

Developer-class courts (pre-revenue: mines, plants, biotech, constellations) must compute the
**magic-funding counterfactual** — fully-funded value per share as a function of the price/
commodity variable — BEFORE litigating the financing path. The financing argument is only
meaningful relative to the prize: SLI's benches prosecuted the path in detail while the
fully-funded NPV at spot equaled the tape, making every financing catalyst a non-event for
entry. Both templates carry the mandate; the adjudicator must refuse ratification of any
developer-class verdict whose record lacks the table. Entry logic on such names is JOINT by
default (price-variable threshold AND funding milestone), never funding alone.

## §CLEAN-COURT-MINIMUM-STARTER (ratified by principal 2026-08-21)
A court whose surviving findings are ALL risk/timing-class defaults at adjudication to a 0.25-0.5%
starter inside a registered envelope carrying the court's gates — NOT to FLAT. Zero is a size that
must be EARNED by a named kill: data-integrity, RP_TAINTED, meme exclusion, a dated supply cliff
inside ~6 weeks, foreign-agent cleanup, or an un-buildable book (no finite build time = no size).
Rationale: the taxonomy routes risk to SIZE and timing to TRANCHE; the 2026-08-21 missed-entry
review (52 passes : 1 take) showed zero had silently become the default size. The adjudicator must
either stage the starter envelope or write the named kill — "no divergence" alone is a sizing
input, not a kill. The missed-entry review runs monthly and ratchets this bar in BOTH directions.

## §CONSENSUS-KILL (ratified by principal 2026-08-21)
Every surviving kill is tagged NOVEL (desk-sourced from a primary document ahead of the narrative)
or CONSENSUS (the known bear story). A court whose kills are ALL consensus-class, on a name
at-or-below the court's own fair value, adjudicates to a MINIMUM STARTER, not FLAT: avoidance
built entirely on priced risks has no edge — the symmetric application of divergence doctrine.
Unaffected regardless of tag: NOVEL kills, data-integrity kills, valuation kills (price above own
FV), unboundable tails, and every §CLEAN-COURT named kill. Origin: the antigravity bullish-override
review — its red benches kept reproducing desk findings (the risks were known) and its blue kept
overriding them; the legitimate content of the override is "the bear case is priced," and that
content is now measured per-finding instead of asserted per-name.

## §TINA-CLASS (ratified by principal 2026-08-21)
A name meeting ALL of: durable verified moat, anti-masking-clean accounting, net cash or trivial
leverage, and secular growth — adjudicated FAIR by a full court — takes its entry AT FAIR at
0.5-1.0%, with adds on CALENDAR TRANCHES, not price gates. Fair value IS the entry (TINA memory,
given teeth); the bargain band becomes acceleration, never permission. The quality bar is strict
and each criterion must be court-verified, not asserted: a contested moat (APP) or an integrity
overhang (SRAD) fails the class. Optimism lives in the prior and the sizing; it never touches
arithmetic.

## §TIER-STRUCTURE (ratified 2026-08-22, principal)
Benches (RED and BLUE) run on the volume tier (Opus-class): two lower courts doing diligence.
ADJUDICATION runs on Fable — the strong-model layer is the checkpoint, not the benches.
This supersedes the earlier "red>=6 + blue on fable" allocation. Rationale (empirical, this
docket): the Fable adjudication layer caught every load-bearing bench arithmetic error
(doubled dilution, half-quoted collar, sign-inverted carry, impossible decomposition) at a
fraction of the cost of running 88 Fable benches. Consequence that is now LOAD-BEARING:
adjudication may NEVER rubber-stamp — every load-bearing bench number gets re-verified
against a primary at adjudication, because the tier below is known to err on adversarial
arithmetic. Escalate-intelligence doctrine is satisfied AT adjudication.

## §BIOTECH-BASE-RATE (ratified 2026-08-22, principal challenge: "biotechs trade near net cash since most trials fail")
Every court on a clinical-stage name MUST:
1. State the unconditional stage->approval base rate for the indication AND the conditional rate
   given the disclosed data, with the delta JUSTIFIED from the data (n, confirmed vs unconfirmed,
   comparator precedent). A prize table without PoS weighting is a rejected artifact
   (KG: undiluted_prize_table_overstates_clearance, PROK court).
2. NEVER credit "net cash" as a floor without BOTH: (a) burn-to-catalyst haircut — the floor is
   cash AT the catalyst date, not cash today; (b) a capital-discipline check — biotech cash is
   payroll, not shareholders' capital, absent contractual delivery (LAB's merger collar) or a
   demonstrated return history. "Trading near cash" is CLIMATOLOGY (most trials fail; the market
   prices the modal zero), never a dislocation claim by itself.
3. Price dilution-before-crystallization explicitly when burn/runway collides with the value
   catalyst (the CTMX structure: no GTC, calendar tranches, hard stop — is the template response).

## §FIELD-VERIFIED-SIZING (ratified 2026-08-24, principal: "trades where we do physical legwork need to come up in sizing")
Pre-registered human observation that RESOLVES a named gate/unknown licenses ONE RUNG of size
upgrade on the court's own ladder (min-starter 0.25->0.5; quarter->third->half of licensed size).
Conditions, all required:
1. PRE-REGISTERED: the observation and its interpretation were written BEFORE looking (the
   observer-brief pattern). Post-hoc "I saw good things" licenses nothing.
2. DISCONFIRMATION-INCLUSIVE: the field pass checked the item that would HURT the position, and
   the record shows what was found (SUJA precedent: the same pass that confirmed core health also
   physically confirmed the Slice fade — that two-sidedness is what made it size-worthy).
3. STRUCTURAL CAPS SURVIVE: field work never overrides supply cliffs, ADV limits, axis caps, or
   RP_TAINTED ceilings (SUJA's 256%-of-float 11/02 unlock caps regardless of shelf checks).
4. ONE RUNG PER PASS, graded: field-sized upgrades carry a cohort tag (field_sized) and grade at
   90/180d like the clean-court cohort — the channel EARNS its multiplier empirically or loses it.
5. The n-of-1 rail stands for everything else: observations that don't resolve a NAMED gate still
   move only timing, never size.
Anti-bias note in the rule itself: physical effort is not evidence weight. The rung is licensed by
GATE RESOLUTION (a named unknown became a known), not by the miles driven to resolve it.

## §BIOTECH-SCIENCE-POSITION (principal-ratified 2026-08-26)
RP_FAIR is UNAVAILABLE to development-stage binary biotech. "Fairly priced" at the stage base
rate is not ownable there: the marginal price-setter is a specialist, so fair-to-a-generalist is
adverse selection, and absence-of-refutation is not a thesis. A dev-stage biotech position (long
or short) requires an AFFIRMATIVE science position: a desk-authored, mechanism-level biology view
producing a frozen, disconfirmable calibration call whose p MATERIALLY differs from the stage base
rate, with named disconfirmers (the BCYC/nuzefatide pattern: p=0.12 vs base, mechanism stated,
closure rule pre-registered). Size derives from that delta, never from "fair." Commercial-stage
biotech with earnings (CUV.AX class) is exempt — ordinary RP rules apply. §BIOTECH-BASE-RATE
still governs the arithmetic (net-cash haircuts, PoS-weighted prizes); this section governs
OWNABILITY. Existing gates on dev-stage names inherit a science-position rider: no fill without
the frozen differentiated call.

**Process (principal-amended 2026-08-26) — the funnel that earns the dive:**
1. **ECONOMICS GATE (cheap, first):** run the §BIOTECH-BASE-RATE prize table at the UNADJUSTED
   stage base rate. Only if the setup already shows real asymmetry there (implied PoS well below
   the defensible band, or payoff skew that pays even at base odds) does the name earn a science
   dive. Bad economics = no dive, file closes — never spend top-tier cycles verifying the science
   of a trade that doesn't pay.
2. **SCIENCE DIVE at the HIGHEST intelligence tier (Fable session/fork — never the volume-tier
   benches):** mechanism-level biology work producing implied probabilities via documented
   anchor-and-adjust, a PoS-weighted prize table, and named disconfirmers.
3. **PRINCIPAL REVIEW GATE:** the dossier + prize table + proposed frozen call are delivered to
   the principal (deck + email). The calibration call freezes and any staging occurs ONLY after
   principal review — dev-stage biotech entries are a human-gated class, regardless of autonomy
   rung elsewhere.

## §BANDS-OVER-RESTING-GTC (principal-directed 2026-08-26)
When a proposed entry would need a cancel-by (a print or dated catalyst inside the resting
window), the DEFAULT expression is a BAND TRIPWIRE, not a resting GTC: ledger alert_below with a
self-explaining gate_basis (the DOCU standard) + a native IBKR real-time alert expiring at the
old cancel-by date, followed by SAME-SESSION staging on touch. Resting GTCs remain appropriate
only where (a) no dated catalyst sits inside the window (pure washout ladders), (b) the venue is
thin/async (Tokyo lots, where staging latency loses the fill), or (c) the principal asks.
Rationale: a resting order is a liability that outlives its premise and needs cancel machinery;
a tripwire re-checks its premises (tripwires, taint, meme state) at the moment of action. Cost
acknowledged: a V-shaped intraday touch can be missed; the native alert bounds that to
minutes-not-days. First applied: FLNC #105 unwound same session it was staged.
