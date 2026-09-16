# The Thesis Pipeline — end-to-end discipline (CANONICAL v1.0 — approved by the principal 2026-07-02)

Executors: [SOS]=SignalOS quant-analyst agents (judgment/verification) · [SKEP]=independent skeptic agent (deliberately NOT SignalOS — breaks the single-analyst loop) · [DESK]=deterministic modules/watches · [ME]=main-loop analyst (dispatch, adjudication, synthesis) · [USER]=principal.
Design invariant: JUDGMENT is separated from SCORING — SignalOS produces probabilities; deterministic modules freeze, monitor, and score them. The generator never grades itself.

Stage 0  GENERATION [ME + DESK models + USER direction] — slates of 3-4 w/ stated central questions; check factor overlap vs the book BEFORE diligencing; eat-own-cooking (model residuals) but audit the model itself.
Stage 0b INVERTED GENERATION [DESK scanners -> SOS mapping] — data first, idea second: whole-universe anomaly scanners (import_anomaly_scanner: all ~1,200 HS4 categories, acceleration + rollover; future: hiring waves, satellite buildout, award-flow) surface PHYSICAL-TRUTH movers; SignalOS maps category -> entities (customs-BOL consignees) -> tradeable vehicles (brand owner / ODM / distributor / supplier) and drafts the seed. Seeds enter Stage 1 like any other candidate — the scanner proposes, it never sizes.
Stage 1  TRAP-SCREEN [SOS, batched] — CLEAR/DROP/ESCALATE; hidden leverage/covenants, pending deals, SPENT catalysts, stale premises, WRONG DATES, tradeability, lookahead contamination. Gate: no money/deep-DD past an unresolved kill.
Stage 2  TWO-MODE DEEP DD [SOS; double-pass on the biggest positions] — disconfirmation FIRST; primary-source claim verification (cap structure always; "Verified"=traced to the document); conservative-FV guard; output = 3-scenario FV+probs, conviction 1-10, kill triggers, hold-into vs enter-after.
Stage 3  CATALYST PREDICTION [SOS judgment -> DESK instrumentation] — SignalOS forecasts probability x timing x magnitude per catalyst w/ leading indicators, names the SWING variable, runs evidence sweeps to convert the swing leg from prior to BASE RATE (peer read-across, consumption telemetry); then DESK wires the tripwires into cron and the print-day DECISION RUBRIC is written in advance. No fireable catalyst = dead money.
Stage 4  RED TEAM [SKEP attacks + SOS verifies, independently and in parallel; ME adjudicates] — skeptic attacks sizing philosophy and MECHANISMS; SignalOS re-verifies load-bearing claims against primaries. Healthy outcome = the thesis gets SMALLER (sizes trimmed, mechanisms downgraded, facts corrected in the artifacts themselves).
Stage 5  HONEST CLASSIFICATION [ME writes from the DD; SKEP reads it] — edge explainer: market believes / we believe / who's mispricing & why / why priced in / MECHANISM FALSIFIER / edge type. No-edge is OK (fairly-paid risk = default class) but the label must be honest (mislabeled carry corrupts sizing + calibration).
Stage 6  PRE-REGISTRATION [DESK: desk/calibration.py] — freeze the dated prediction BEFORE entry; frozen p is scored; later evidence (incl. SignalOS refinements) adjusts SIZING only, never the scored number; lookahead guards on ingestion.
Stage 7  SIZING [ME applies the rules; USER owns doctrine changes] — ladder: 1-2% screen-passed / 2-4% DD-survived / 5-10% ONLY after calibration validates (band: re-evaluate the gate at n=10, hard-apply at n=20). Sleeve caps at FACTOR level incl. existing holdings; binary tails capped+UNLEVERED; caps on NLV; circuit-breaker (no adds w/ sleeve >10% below cost); max 2 open pre-print binaries; tax asymmetry = EXIT mechanics only.
Stage 8  PROPAGATION [ME, same turn as the conclusion; DESK backstops] — ledger upsert -> edge record -> entry plan (incl. later adjudications) -> re-run scanner -> VERIFY via API. consistency_check runs hourly as the guard.
Stage 9  EXECUTION [ME stages; USER submits] — live price before staging; RE-POLL broker before status claims; disclose any deviation from reviewed numbers at staging.
Stage 10 RESOLUTION & LEARNING [DESK flags + scores; SOS adjudicates ambiguous outcomes; ME synthesizes; USER settles disputes] — resolve the ledger entry on the catalyst; grade vs the pre-written rubric; act the gate (scale/kill/harvest per Dec-15 rule); quarterly Brier-vs-market + conviction-inversion; failures -> memories with MECHANISM; agent-suggested framework fixes -> codified, not noted.

OPEN ITEMS (acknowledged at canonization): exit discipline for WINNERS (thesis-complete condition at entry, not just kill triggers) — proposed Stage 10.5, undrafted. User-checkpoint placement confirmed at: order submission, sizing-doctrine changes, resolution disputes.

META: exclusions are the product · a shrinking thesis is the process working · the user's intuition is a first-class input · judgment/scoring separation everywhere · nothing is done until visible in the app.

## v1.1 amendment (2026-07-03, user-directed after the missed-entry review)
**Stage 4 (red team) adjudication now applies the RESPONSE TAXONOMY:** each accepted finding is classified
{valuation | business_risk | timing_catalyst | data_integrity} and the modification instrument MUST match:
valuation -> price gate (the only legitimate gate); business_risk -> size cut + tripwires (never a price
gate); timing -> tranche structure; data -> kill. Every gate ships with a REGRET BOUND. WAIT/gate verdicts
receive a standing BLUE-TEAM pass (the symmetric adversary for type-II errors). The missed-entry ledger
(desk/missed_entry_score.py, weekly) grades all gates; realized dip-frequency vs required dip-probability
is the calibration metric. Born from: 10/13 gated entries unfilled at avg +13% with zero realized losses
avoided; IBEX's <=30 gate (category error) converted to 0.5%-at-market + Sept GO/NO-GO reserve.

**v1.1 tooling note (2026-07-03):** Stage-3 catalyst prediction and any print-based GO/NO-GO must invoke the
seasonality + capacity tools: `python3 -m desk.seasonality TICKER` (seasonal QoQ shape + hard/easy-comp flags
from XBRL — a YoY 'deceleration' must be read against the fiscal quarter's own median) and
`python3 -m desk.capacity_check TICKER` (utilization/occupancy/workstations/load-factor from the 10-K —
high utilization + capacity build = revealed demand forecast; NOT_DISCLOSED is itself a finding).

**v1.1 execution note (2026-07-03):** Stage 9 (execution) now runs the pre-order microstructure card
(`python3 -m desk.preorder_card TICKER --usd N --cap X`) before ANY staging — the card picks the
instrument (Midprice for thin floats, marketable limit for liquid names, DO_NOT_STAGE on quarantined
quotes) and the user's live screen outranks every desk feed. Every fill is scored in desk/execution_tca.py
(vs open/VWAP/close) — the calibration ledger for execution. Full doctrine: desk/EXECUTION_PLAYBOOK.md.

**v1.2 tiered model policy (2026-07-04, user-directed):** volume work (Stage-2 DDs, censuses,
evidence sweeps, trap screens) runs on Opus (`signalos-quant-analyst` default). The ADVERSARIAL
COURT runs on the top tier: any red team on a >=6/10 verdict is dispatched with `model: fable`,
and the corresponding blue-team pass (the symmetric type-II adversary on the red team's
modifications) runs at the SAME intelligence level — the prosecution and defense must be
evenly matched or the court is biased by construction. Decisive-finding escalations
(the escalate-intelligence rule) also go to fable.

**v1.3 court-evidence rule (2026-07-04, user-directed):** every red-team and blue-team dispatch MUST
embed the SignalOS verification manifest (`python3 -m desk.court_toolkit`) and both benches must verify
hypotheses FROM DATA: each load-bearing finding cites {claim | tool/connector | data result | grade},
where grade ∈ CONFIRMED/REFUTED (a data check ran) or PLAUSIBLE (none did). Verdicts may rest only on
CONFIRMED/REFUTED findings; PLAUSIBLE findings are argument, not evidence. 'No tool fits' must be stated
as a coverage gap. This extends route-through-pipeline doctrine to the adversarial court — the Hyundai
case showed the pattern works when done ad-hoc (the red team's 2-yr band reconstruction, the blue team's
down-capture empirics); v1.3 makes it mandatory and named.

**v1.4 staging gate (2026-07-24, user-directed):** NO order instruction is staged until BOTH exist:
(1) an INDEPENDENT full court on the name — a finder/scan agent grading its own candidates is a first
pass, never the court (generator-never-grades-itself applies to the court tier, not just discovery;
the ADMA case: a scan's embedded two-mode court missed the escalation a $12k contested-short name
required); and (2) a THESIS DOCUMENT — the reader-facing deck/memo (desk/reports/ HTML + artifact,
PDF export per the analyst-report convention) carrying the court's verdict, corrected numbers,
refusals where relevant, tripwires, position disclosure, and the standard disclaimer. The thesis doc
doubles as the content library (the publishing thread). Sequence is therefore:
find → independent court (red/blue at >=6/10 or contested) → thesis doc → STAGE envelope → user submits.
Sourcing agents deliver VERDICT CANDIDATES, not staged orders. Tempo cost accepted by design.

**v1.4.1 catalyst-carry (2026-07-24, user-directed):** for fast-moving / catalyst-driven names the
v1.4 gate is satisfied IN ADVANCE: the independent court runs and the thesis doc is built BEFORE the
catalyst that would move the name, and both are ATTACHED to the catalyst's resolution pack ("carry the
thesis with the catalyst"). The pack's pre-committed branches reference the thesis; when the catalyst
fires, the gate is graded, the thesis gets its verdict stamp, and the envelope stages immediately —
zero fresh research inside the reaction window. Every dated catalyst on the calendar that could
trigger a staging MUST carry: court record + thesis doc + conditional entry ("gate passes → stage X
@ Y"). A catalyst arriving without its thesis is a coverage failure, flagged by the pre-flight check.

**v1.5 forward instrumentation on owned names (2026-07-29, user-directed — "I shouldn't have to ask"):**
every court-cleared BUY/STARTER automatically gets STANDING FORWARD INSTRUMENTATION stood up at
staging time, without the user requesting it. Stage 3 already forecasts catalysts at underwriting;
v1.5 makes the instrumentation half MANDATORY and MECHANICAL for any name we actually own or stage:
(1) NAME the load-bearing operating variable — it is almost always what the kill triggers are written
against (Kalmar: equipment order intake; WAL: uninsured-deposit mix + fraud/NDFI charge-offs; VRLA:
volumes/margin vs the wine secular); (2) MAP it to SignalOS channels via the dispatch index — public
pre-award/procurement flow, customs BOL, hiring velocity, subsidy/award pages, monthly industry data,
own-PR floor detectors — anything public that LEADS the next print; (3) STAND UP a registry watch
(enabled:True — the dead-watch lesson) that nowcasts the variable and wires its flags to the EC kill
list; (4) FREEZE a graded calibration call on the next print (the nowcast's detectors named in the
record) so the instrument earns trust empirically or dies — nowcast updates SIZING only, never the
frozen number; (5) DOCTRINE GUARD: these are TRIPWIRE NOWCASTS, not alpha claims (the frontrun ledger
is 4-for-4 negative on pipeline-leads-the-stock); a blocked source is DATA MISSING, never zero.
First instance: kalmar_order_nowcast (2026-07-29). Owed at next touch: WAL (FDIC call-report
uninsured-% poll — quarterly, cheap), FSBW (construction/CRE concentration off the quarterly call
report), VRLA (monthly EU glass/wine data if a public series exists; else Q3 pack only).

**v1.6 position-doc completeness standard (2026-07-29, user-directed):** every FINAL document associated
with a position (held, or staged awaiting the click) MUST carry, per name — no exceptions, no format waivers:
(1) THE FOUR-IDEA FRAME as its own section: what the MARKET believes / what WE believe / why we might have
EDGE (with the honest "nobody is grossly mispricing" allowed and often correct for RP_FAIR) / why it may be
PRICED IN — plus the mechanism FALSIFIER and the EDGE TYPE label (EDGE / RISK_PREMIUM / RP_TAINTED / NONE);
(2) SIGNALOS VALIDATION of every load-bearing claim: an independent verification pass (fresh eyes, primary
documents, VERIFIED/CORROBORATED/REFUTED/UNVERIFIABLE per claim) rendered as a verification table in the doc —
courts and red teams GENERATE facts, the verification pass AUDITS them; a doc without the table is a fact
sheet, not an underwrite; (3) A CLEAR BRIER-BOOK ENTRY: the frozen calibration-ledger call (ticker|date, the
bar, our_p, the anchor if one exists) named in the doc, so every position's thesis grades on a date rather
than drifting — no frozen call, no final doc. ENFORCEMENT is mechanical, not remembered:
`consistency_check.check_position_docs_complete` flags every held/staged name whose doc chain is missing any
of the three legs. Standalone checklist: THESIS_DOC_STANDARD.md. Backfill of pre-v1.6 held names proceeds
flag-driven (the checker names them); new positions comply at staging or the envelope waits.
