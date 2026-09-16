# HOUSEHOLD FINANCIAL PLAN
## Deployment & tax-harvest architecture · the alpha sleeve · the AI-drawdown program · hedges · the disaster book
**SignalOS desk · 2026-08-29 (renamed from TLH_SLEEVE_ARCHITECTURE_20260828_v2 — the scope outgrew the name) · supersedes v1 (8/26) and incorporates TLH_HEDGE_PROPOSALS_20260828 + AI_BREAK_ENSEMBLE_FINDINGS (2026-07-30)**


## ABSTRACT

**The problem.** A ~$5.0M zero-basis payment lands in September. Roughly $1.855M of it is already
the government's; the remaining ~$3.2M must be deployed so that enough capital losses are
*realized by December 31, 2026* to offset the gain at a ~37.1% marginal rate — inside a household
that already carries $9.2M of externally-managed levered tax-harvesting (Parametric), holds ~26%
of its wealth in the AI complex, and expects further inflows.

**The design, in one paragraph.** The money deploys into a separate rule-driven account (BETA)
that can never hold a courted name: ~$1.9M goes directly into 32 pre-ruled single-name slots
(single names disperse — dispersion is what produces harvestable losers before year-end) and
~$1.3M into a two-fund index completion sleeve whose job is beta, not losses. Two rotation rules
convert index dips and court gates into harvests; every name carries a pre-assigned wash-safe
replacement partner (the pair map, with November 28 as the last doubling-up date); and a small
code layer — pair validation, cross-account wash checks, a constructive-sale screen that already
rejected the obvious short candidates — makes the tax rails machine-enforced rather than
remembered. Order-integrity sentinels, band-tripwire discipline, and a live status page provide
the operational floor, each guard built from a failure the desk actually observed.

**The risk, and the hedge derived from first principles.** The desk's seven-model ensemble puts
the probability of an AI-complex credit event by end-2027 at a frozen 0.45, and — more usefully —
predicts its *sequence*: credit breaks first (neoclouds, then Oracle, then the credit channel),
equity multiples last. Because the household already owns three layers of implicit protection
(harvest convexity worth ~37 cents per dollar of drawdown, an anti-correlated tax reserve, and
tripwires that fire before the equity leg), and because a net buyer should never sell its
melt-up branch, the previously-ratified call-collar is withdrawn. The recommendation is a
**two-layer hedge matched to the information structure**: a small standing put-spread
(~10–17% of the AI overlap, ~$10–18k/yr) covering only the no-warning branch, plus a
pre-registered escalation to ~50% of the overlap — executed within five sessions of any named
gate firing — accepting crisis volatility as the known price of certainty. Cheaper than the
collar when nothing happens, larger when it matters, upside never sold.

**What awaits the principal:** ratify the two-layer hedge and its doctrine amendment
(protection phases with deployment *and information*, not calendar); rule on the bounded
dispersion sleeve; set the ALPHA-migration gates; complete the BETA activation checklist at
account approval. Nothing stages until the money lands.

---

# PART I — THE SLEEVE (deployment + harvest machinery)

## 1. Objective and binding constraints
Realize enough capital losses by **2026-12-31** to offset the ~$5.0M zero-basis gain landing in
September (~37.1% combined marginal → each harvested dollar saves ~$0.37 *this year*; 2027
harvests are only carryforwards) — without ever letting the harvest machine contaminate the
judgment machine.

| # | Constraint | Design consequence |
|---|---|---|
| C1 | Losses realize by 12/31/26 | slots-first (dispersion now); index residual accepts ~zero 2026 harvest |
| C2 | Tax reserve ≈ $1.855M (true-up at landing) | bills/SGOV day 0; deployable ≈ $3.2M |
| C3 | Household wash surface = Parametric singles + GOOGL + BETA basket | completion-set construction + pre-rotation sweeps + harvest_engine checks |
| C4 | Household AI complex ≈ $5.18M ≈ 26% of household (Parametric 38% internal) | no QQQ; broad index only; hedge sized to the OVERLAP (Part III) |
| C5 | Judgment-vs-rule boundary (principal-ratified) | two accounts; courted names structurally barred from BETA |
| C6 | Ops maturity | BETA has NO automated order paths — staged CSVs, principal clicks |

## 2. Account architecture
ALPHA (ACCOUNT_ALPHA) = the court book: every courted name, envelopes, options templates — judgment,
gated by courts. BETA (ACCOUNT_BETA, pending) = the $5M: 32 pre-ruled slots + index completion
residual + hedge + reserve — rule, no courts. Parametric ($9.19M, 131/31) = the external
levered TLH engine (~$105k/mo realized losses, −$425k banked YTD). The wash perimeter is
household-wide; `beta_basket_generator.py` makes BETA non-colliding **by construction**
(index minus Parametric bundle minus ALPHA book minus GOOGL). `require_alpha()` pins all four
automated placement paths to ALPHA; the Error-435 incident is the reason.

## 3. Deployment lanes (amended 8/21: SLOTS FIRST)
1. **Weeks 1–3:** ~$1.8–1.9M directly into the 32 pre-ruled slots (lots 2–3 of the 8/02 map) —
   staged ladders, envelope-chunked where thin. Every week earlier = more dispersion before 12/31.
2. **Index residual ~$1.2–1.4M** same week, two non-identical broad funds (VTI+SPLG class) so
   future index-level harvests swap wash-free. Job = beta, not losses.
3. **Completion criterion:** whatever index remains unrotated at month 12 (~$0.5M floor) IS the
   permanent completion sleeve.

## 4. Harvest machinery
- **Rotation rules:** R1 (harvest-driven — index loss ≥$5k or a ≤−1.5% day → sell high-basis
  index lots, buy slot names at bands) and R2 (gate-driven — court gates outrank harvest timing).
- **Harvest-pair map** (33 pairs on file, validated 8/26 against the live wash surface): every
  slot name has a designated non-identical partner for the 31-day window. *No pair, no harvest.*
  **Nov 28 = last doubling-up date** (buy the partner 31 days before selling the loser).
- **`desk/harvest_engine.py` (built 8/26):** Phase 0/1 live — pair-map validation vs the live
  surface, per-name wash checks (PARAMETRIC_SELF protocol), the **§1259 constructive-sale short
  screen** (first run rejected NVDA/AAPL/UNH/DE as short candidates — shorting a name the
  household holds appreciated force-realizes Parametric's gains: the anti-TLH trap, now
  machine-enforced), and the R1 staged-basket stub that goes live at landing. Phase 2 (a
  $150–300k completion-set short-clip pilot) and Phase 3 (closed-loop) remain principal-gated.
- **Proposed, unratified:** the bounded diligenced-dispersion sleeve ($750k–1M long-only of
  FLAT-ruled names passing three filters: liquid, not RP_TAINTED, no live gate in the harvest
  horizon) — est. 2–3× harvest yield per dollar vs the index residual.

## 5. Operating infrastructure (all observed-failure-driven, none hypothetical)
Order sentinel (30-min: zombie cancels, PendingCancel SLA, cancel-by enforcement, gateway
2-strike alarm, runner liveness) · order-intent ledger (every directive machine-checked) ·
band watcher w/ live-blotter coverage + 48h touch-disposition invariant · consistency guards
(pack dates, drain stalls, **rubber-stamp/artifact guard**) · §BANDS-OVER-RESTING-GTC (tripwires
+ native alerts over resting GTCs wherever a cancel-by would exist) · pipeline status UI
(`/status`). Cadences: weekly bundle→basket regen; monthly migration/hedge-phase/reserve
review + MR-scorecard; quarterly AI-break re-freeze (Part II) gating hedge tranche 3.

---

# PART II — THE AI-DRAWDOWN RESEARCH PROGRAM
*Why a tax-harvesting document carries a bubble model: C4. The household is ~26% AI-complex, the
sleeve adds index beta on top, and the harvest engine's own convexity is a drawdown instrument.
The hedge decision (Part III) is priced off this program's frozen number.*

## 6. The seven-model AI-break ensemble (built 7/30; findings doc + runnable models in desk/models/)
Prompted by the "Second Derivative" thesis (AI buildout = credit-financed real-estate cycle that
breaks on capex *deceleration* — the 2008 mechanism). Seven independent epistemologies, read for
their disagreement:

| Member | Vote | One-line reading |
|---|---|---|
| Mechanism (refi wall + gates + 2008 clock) | AMBER 0.30 | wall binds 2028 only in bust regime; Gate A half-lit |
| LPPL / Sornette critical-point | RED 0.86* | super-exponential fits on all 3 series; **t_c ≈ Dec-2026** |
| Credit-vs-equity basis (the 2007 ABX signature) | GREEN | no divergence *because periphery equity is already soft* (eq-wt basket −1.6%/6m vs SOXX +40%) |
| Reference class (8 capex manias) | AMBER 0.46 | telecom = closest analog, broke 1–4q post-peak **because vendor financing** — intensity today HIGH |
| Minsky financing-stage | RED | **AMZN 1.02 / ORCL 1.74 capex-to-OCF = Ponzi-stage**; $197B trailing net debt issuance |
| Behavior tells | AMBER | **CRWV insiders 10× intensity, 82 sellers — FIRED** |
| Network contagion (Eisenberg-Noe) | structural | invariant order: **neoclouds seize first (even at 50% shock) → ORCL secondary-defaults → credit channel → megacap margins → multiples** |

**Frozen: `AI-BREAK|2027-12-31 @ 0.45`** (median 0.46, range 0.30–0.86); companion ~0.72 by
end-2028. "Credit event" = neocloud default/seizure, take-or-pay impairment, GPU-ABS downgrade
cascade, or RPO counterparty reprice — **not an equity drawdown**; equity multiples are the LAST
step of the predicted sequence, which is what makes the sequence tradeable.

**Convergent findings:** CRWV is the canary in three unrelated datasets (Merton DD 1.6, insider
10×, first node to breach in every clearing scenario). ORCL is the concentrated hyperscaler
(Ponzi financing + worst hit-to-buffer + equity already −26% while the index rose). The complex
is **already repricing beneath the index surface** — the equal-weight periphery is negative while
cap-weight melts up, historically the *late* configuration.

**Gates and watch order:** CRWV credit/insiders (firing) → OpenAI IPO terms (Gate A: pricing
<$852B or slip past Q1-27) → the **Nash flip** (first capex guide-down the tape *rewards*; while
all five hyperscalers raise guides, near-term P stays capped). Kill condition for the whole
frame: lab revenue becoming independent end-demand rather than recycled capex.
**Standing instrumentation:** `ai_capex_watch` (weekday: realized-accel clock + guide event
studies); ensemble re-run quarterly, after hyperscaler prints, and on any gate event — **the
quarterly re-freeze is a live input to Part III.**

## 7. The rest of the AI-drawdown book (the same graph, other edges)
- **WAL NDFI kill-class:** the bank edge of the contagion graph — WAL lends to levered funds;
  the break transmits through fund-finance. Human-observer channel carries the only sensor
  (NAV-facility/sub-line tightening chatter); a pattern of observations legitimately moves the
  ensemble p at re-freeze. Position instrumented (650 sh, kill-triggers armed).
- **AI-crash-insulated CA munis:** the fiscal downstream channel — the muni work screens CA
  districts for AI-payroll/property-tax sensitivity so the muni sleeve is the *insulated* cohort,
  not the exposed one (AI_CRASH_INSULATED_CA_MUNI work, muni stack).
- **CRWV canary + CIFR/IREN gates:** the desk's neocloud exposure is gated, never resting —
  CIFR reopens only ≤$12.50 w/ delivery verified (hiring-confirmed 8/26); the first hyperscaler
  JV is the kill variable.
- **Software-sleeve displacement watch:** the seat-erosion question (NOW/SAP/MNDY/HUBS + the
  DOCU IAM/LLM-substitution disclosure) is the *revenue-side* AI risk — tracked per-name in
  courts, human-observable at renewals.
- **Household quantification:** AI complex $3.52M inside Parametric (38% of its NAV; NVDA $575k,
  AAPL $561k, MSFT $399k, AMZN $295k, GOOGL+GOOG $485k, AVGO $257k) + ~$700k external GOOGL +
  VTSAX tech weight ≈ **$5.18M on ~$19M** (26%). A −30% AI drawdown ≈ −$1.55M household.

## 8. How the AI work and the TLH sleeve interlock (the design's spine)
1. **The hedge is priced off the frozen number** — tranche 3 exists only while the quarterly
   re-freeze holds ≥0.45 (Part III).
2. **The harvest is the second hedge**: a drawdown *feeds the product* — ~37¢/$ of decline in
   tax value against this year's gain. The two mechanisms split the loss curve: options cover
   the first leg, the tax code monetizes the rest.
3. **The reserve is anti-correlated by construction** (bills; the gain it reserves against
   shrinks in the same states).
4. **The sequence is the tripwire ladder**: because the ensemble predicts credit-before-equity,
   the desk's earliest signals (CRWV credit, neocloud seizure, Gate A) fire *before* the index
   drawdown the hedge covers — re-freezes can raise the hedge before the equity leg moves.

---

# PART III — THE HEDGE DECISION (derived from first principles; prior ratification set aside at principal direction 8/28)

The full derivation lives in TLH_HEDGE_PROPOSALS_20260828 (v2). Summary of the chain:
**Risk:** $5.18M household AI complex; frozen P(credit event by end-27)=0.45; the equity leg is
the LAST step of the predicted sequence. **Pre-existing protection:** harvest convexity
(~37 cents/$), reserve anti-correlation, an alpha book the courts already kept light on AI, and — the
underused asset — the sequence itself, whose tripwires fire before the equity leg. **Net-buyer
test:** the household expects further inflows; any call leg sells the branch it most wants —
caps fail first principles regardless of their carry savings.

**RECOMMENDATION — the two-layer hedge, matched to the information structure:**
- **Layer 1 (standing, small):** Dec-27 XND put spreads 10/30% OTM, 15–25 spreads (~10–17% of
  overlap), ~$10–18k/yr — insurance for the ONE branch the models admit they would miss (no
  warning). No call leg.
- **Layer 2 (pre-registered, bought only on evidence):** on Gate A / a CRWV credit event / the
  Nash flip / a re-freeze >=0.55 — escalate within 5 sessions to ~50% of overlap in plain puts,
  accepting crisis IV as the known price of certainty. Decision made now; execution waits for
  the signal.
- **Layer 0 (owned already):** the tax code and the reserve carry the deep grind; Nov-28
  doubling-up is part of the hedge.
- **Wind-down:** re-freeze <0.35 two consecutive quarters -> Layer 1 non-renews.
- **Deployment floor:** no hedge notional before its capital lands — protection follows capital
  AND evidence, never calendar.

**Doctrine consequence (requires ratification):** conditioned-insurance amends from phase-with-
deployment-% to phase-with-deployment-AND-information; the 8/21 collar is withdrawn as default
(its call leg fails the net-buyer test; its full standing size pays for warning the ensemble
already supplies). Expected cost: ~$13–24k in the modal no-gate path vs the collar's ~$33–66k
path-independent — cheaper when nothing happens, bigger when it matters, upside never sold.


---

# PART IV — THE ALPHA SLEEVE: PURPOSE, ROTATION POSTURE, AND THE DISASTER BOOK

## 12. What the alpha sleeve is FOR (four purposes, in priority order)
1. **A deliberate anti-rotation fund.** The founding directive (7/22): *"build our own hedge fund
   to work against sector rotation."* The book is a ~90-position, 13-axis multi-sector
   fundamental long book constructed so that no single rotation carries it — measured, stressed,
   and construction-planned by `desk/rotation_fund.py`.
2. **The knowledge factory.** Every court feeds detectors into the knowledge graph; the KG, the
   Brier ledger, and the doctrine ARE the moat (the meta-thesis). The P&L is the grade, not the
   product.
3. **The edge barbell on the TLH core** — capacity-constrained edges (Japan micro, frontier
   GDRs, court-gated smallcaps) that big money structurally cannot reach, sized so the ceiling
   is the feature.
4. **The seed track record** for the first outside-capital product (Antifragile Carry — Part IV §14).

## 13. How much does it hedge sector rotation? (engine read, 8/28 — marks partially stale, directional)
Diversification: **10.6 effective axes / 21.2 effective names** across the mapped core.
Six rotation stresses on the deployed book:

| Rotation scenario | Unhedged | With designed IGV overlay | Worst axis |
|---|---|---|---|
| Risk-off (cyclical→defensive) | **−11%** | −10% | software_saas |
| Rate spike | −5% | −4% | software_saas |
| AI-capex derate | −5% | −3% | software_saas |
| Growth→value | −3% | −2% | software_saas |
| Software→energy | −1% | −0% | software_saas |
| US→intl / dollar down | ~0% | +0% | software_saas |

**The honest answer in three sentences.** Against *rotation proper* — money moving between
sectors/styles — the book is well-built: growth→value costs ~3%, software→energy ~1%,
US→international ~zero, because 13 axes catch what each other shed. The two residuals are
(a) the **correlated software/IT block (~21% of deployed — the worst axis in all six
scenarios)**, for which the designed-but-unstaged IGV short envelopes (368+69 IGV ≈ $39k)
exist awaiting principal staging, and (b) **DFIN at 11%** single-name. And the −11% risk-off
row is NOT rotation — it is market beta, which no amount of sector construction hedges; that
tail belongs to Part III's XND layers, which is exactly why the hedge decision lives in this
document.
**Self-cure:** both concentrations are relative to deployed capital; the construction plan
routes the ~$645k of remaining dry powder to the under-weight intended/idio axes (real-asset
ballast, Japan value, EM financials, insurance, energy, healthcare) and freezes the software
block — deployment fixes concentration without trimming conviction.

## 14. The disaster book (The Desk's disaster-planning corpus, unified here)
The desk's tail work spans four layers, each with its own instrument:

| Layer | Threat | Work product | Instrument / status |
|---|---|---|---|
| **Axis** | sector rotation | rotation_fund 3-stage engine (measure/hedge/construct) | live; IGV envelopes designed, unstaged |
| **Market** | beta drawdown / AI break | 7-model AI-break ensemble (Part II), frozen 0.45, credit-first sequence | two-layer XND hedge (Part III, awaiting ratification); harvest convexity |
| **Systemic-fiscal** | AI-crash fallout in munis / banks | AI-crash-insulated CA muni screen; WAL NDFI kill-class + observer channel | muni sleeve screened to the insulated cohort; WAL instrumented |
| **Civilizational** | the 7-tail wargame (freeze / war / infra / nuclear...) | tail-wargaming framework: Taleb barbell audit — 3 traps struck (self-dealing art trust, don't-pay-taxes bet, two-way leverage), 3 gaps filled | positive-carry convexity ONLY |

**The organizing principle that survived the wargame:** *positive-carry convexity* — every
black-swan long must pass "would I be happy owning it if the swan never comes?" The desk
explicitly declined negative-carry insurance (naked puts, tail programs) on net-buyer logic;
what it builds instead:
- **The convexity backtest verdict (the go/no-go, run honestly):** crash convexity is nearly
  monopolized by **gold-royalty** (the only vertical that held through the 2020 liquidation);
  defense/energy/ag are war-convex but crash-beta-worse (a latency trade); and four fashionable
  "chaos" verticals (cyber, uranium, rare-earth, reshoring) tested **beta-1 or worse and were
  dropped** — the discipline most thematic products lack. The surviving construction: gold-royalty
  core + resilient thin-coverage carry (CWCO/PLPC-class) + war/inflation satellite + metal tail.
  Current book expressions: PHYS 320 sh + resting adds, AAUC, CAML — the real-asset-ballast axis
  at $10k vs its $150k target is the most under-built intended axis in the construction plan.
- **Dry powder as the option:** the September $5M and the fade ladders far below market ARE the
  long-black-swan — a crash is a windfall to the resting buyer.
- **The mundane-tail correction:** P(death/illness/lawsuit) ≫ P(nuclear war); the cost-weighted
  priorities are boring (estate plan, insurance, custody diversification) and sit outside this
  doc but inside the household queue.
- **The deep reframe:** SignalOS itself is the ultimate antifragile asset — a *capability* (find
  dislocations, read thin paper, be the patient bidder when others are forced sellers) that
  appreciates in disorder. The product expression is **Antifragile Carry** (spec v0.1 on file:
  capacity-capped, carry-not-bleed, verified-not-thematic; the calibration ledger as the
  un-gameable track record).

## 15. The unified risk picture (how Parts I–IV interlock)
The TLH sleeve supplies the beta and the tax convexity; the alpha sleeve supplies the
anti-rotation construction and the capacity-walled edges; the ensemble supplies the one number
(0.45) and the sequence that price the hedge; the disaster book supplies the filter (carry-only
convexity) that keeps every layer positive-EV in the base case. One risk, one owner, no layer
asked to do another's job: rotation → construction; beta/AI-tail → the two-layer XND hedge +
the tax code; fiscal contagion → screened munis + the WAL instrumentation; the civilizational
tail → gold-royalty carry, dry powder, and a desk that gets more valuable in disorder.

## Decision queue (principal)
0. Stage (or decline) the designed IGV rotation-hedge envelopes and the real-asset-ballast deployment priority (Part IV).
1. Ratify the two-layer hedge + the conditioned-insurance amendment (or choose a Step-4 menu row).
2. Ratify or decline the dispersion sleeve (Part I §4).
3. Sec-ALPHA-MIGRATION gates into the runbook; gateway-restart + envelope-launchd autonomy calls.
4. BETA activation checklist on approval.

*Figures re-derive at landing and at each quarterly re-freeze; nothing stages until the $5M
lands and item 1 is ratified.*
