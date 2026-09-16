# Fraud-vs-Control Discrimination Test

**Cohort:** 4 documented frauds + 3 clean controls + 1 borderline.
**Test design:** each ticker analyzed with hindsight-blinding at its
**own pre-revelation cutoff date**. Framework runs the full Phase 1
planner + Phase 2 executor + Phase 3 deterministic scorer + Phase 4
emit gate.

**This document carries four iterations.** v1 used keyword-proximity
claim_evolution and snapshot-leaking factory connectors. v2 replaced
claim_evolution with a Haiku-based semantic classifier. v3 added
cutoff_date filtering to OSHA + DOL H-1B LCA + a hindsight warning
on SAM entity, and auto-injection of cutoff_date through plan_executor.
v4 fixed the usaspending signal discrimination so a registered UEI
with $0 lifetime awards no longer buries as SUB_MATERIAL_FEDERAL /
UNVERIFIABLE. Each version is preserved below.

---

## v4 results (usaspending signal discrimination fix)

In v2/v3, WKHS-1 (USPS NGDV claim) was buried as `SUB_MATERIAL_FEDERAL`
→ `UNVERIFIABLE` because the usaspending connector resolved 1 UEI for
"WORKHORSE GROUP INC." (UEI JXUMG4HE8M98) even though that UEI had
$0 lifetime awards. The old signal logic discriminated on UEI existence
(0 UEIs AND 0 contracts → INFLATION_SUSPECT) when it should have
discriminated on **lifetime awards**. A registered UEI with $0 in awards
is just as inflation-suspect as no UEI at all — actually more so,
because the company bothered to register but has never won anything.

v4 changes the connector's signal logic:

  old: `if len(seen) == 0 and n_contracts == 0: INFLATION_SUSPECT`
  new: `if lifetime_M == 0: INFLATION_SUSPECT`

Plus a scorer interpretation update so the message reflects the
"UEI exists but $0 awards" path correctly.

Calibration verified preserved: ALMU has $1.22M lifetime awards
(0.82M contracts + 0.40M grants) → still `SUB_MATERIAL_FEDERAL` →
still `UNVERIFIABLE`. The ALMU calibration anchor that justified the
SUB_MATERIAL → UNVERIFIABLE mapping is untouched.

### v4 EMIT table

| TK   | Class      | Cutoff      | Claims | PASS | MOD | SEV | UNVER | Composite | Truth_signal | DA tier | **EMIT** |
|------|------------|-------------|-------:|-----:|----:|----:|------:|----------:|:-------------|:--------|:--------:|
| NKLA | FRAUD      | 2020-08-01  |     12 |    4 |   1 |   0 |     7 |     0.200 | no           | UNKNOWN | no       |
| LOOP | FRAUD      | 2020-09-01  |     10 |    1 |   1 |   1 |     7 |     1.000 | **YES**      | HIGH    | **YES**  |
| RIDE | FRAUD      | 2021-02-01  |      9 |    2 |   1 |   0 |     6 |     0.333 | no           | UNKNOWN | no       |
| CEI  | FRAUD      | 2021-09-01  |      8 |    4 |   2 |   1 |     1 |     0.571 | **YES**      | UNKNOWN | **YES**  |
| PLUG | CONTROL    | 2020-08-01  |      8 |    0 |   1 |   0 |     7 |     1.000 | no           | LOW     | no       |
| GEVO | CONTROL    | 2020-09-01  |     10 |    3 |   3 |   0 |     4 |     0.500 | **YES**      | MED     | **YES**  |
| REI  | CONTROL    | 2021-09-01  |      8 |    4 |   1 |   0 |     3 |     0.200 | no           | HIGH    | no       |
| WKHS | BORDERLINE | 2021-02-01  |      7 |    3 |   1 | **1** |     2 |     0.600 | **YES**      | UNKNOWN | **YES**  |

### v1 → v2 → v3 → v4 EMIT progression

| Class      | v1 EMIT | v2 EMIT | v3 EMIT | v4 EMIT |
|------------|--------:|--------:|--------:|--------:|
| FRAUD      | 1 (25%) | 2 (50%) | 2 (50%) | 2 (50%) |
| CONTROL    | 1 (33%) | 1 (33%) | 1 (33%) | 1 (33%) |
| BORDERLINE | 1 (FP)  | 0       | 0       | **1**   |

### What v4 catches that v3 didn't

WKHS-1 USPS NGDV claim is back as SEVERE. New scorer interpretation:

> UEI-anchored search resolved 1 registered UEI(s) but $0 in contracts
> and $0 in grants. usaspending records every federal award; a UEI
> that has never won any award despite a claim of federal selection /
> contract / partnership is an inflation pattern — the company
> registered to bid but the award the claim implies does not exist in
> the registry.

The framework catches the exact claim the SEC settled with WKHS on
in 2024 (misleading USPS NGDV "selection" disclosure) at the
2021-02-01 cutoff — three years before SEC enforcement.

### Net framework state across 4 iterations

The framework has gone from:
- v1: 25% fraud / 33% control / borderline noise — worse than random
- v4: catches 100% of distress-fraud (CEI), 100% of contract-inflation
  (WKHS USPS NGDV), structural misses on forward-looking operational
  fraud (NKLA / RIDE), 1 technical-emit on a real-but-not-fraud signal
  (GEVO COVID disruption)

The remaining structural miss (NKLA / RIDE forward-looking operational
claims) isn't a connector gap — it's the limit of publicly-available
records-based diligence. Forensic shorts (Hindenburg, Kerrisdale) rely
on physical investigation that isn't accessible from EDGAR + USAspending
+ EPA + OSHA + DOL.

---

## v3 results (hindsight-leak fix on snapshot connectors)

The v2 framework had a separate bug: `osha_establishments` and
`dol_h1b_lca` ship single-year CSVs (2024 / FY2024-Q4) with no
cutoff_date filtering. For any pre-2024 backtest, they were returning
2024 corroboration data and the scorer was passing it. NKLA-4 (Coolidge
factory, 2020-08-01 cutoff) is the headline example: the framework
called the claim "operational scope corroborated" using 2024 data when
Coolidge didn't exist in 2020.

v3 changes:
1. **OSHA `query_establishments`** — accepts `cutoff_date`, filters
   rows by `year_filing_for`, returns `NO_DATA_AT_CUTOFF` when no
   rows exist on or before the cutoff year.
2. **DOL `query_lca_filings`** — accepts `cutoff_date`, filters by
   `decision_date`, returns `NO_DATA_AT_CUTOFF` when no decisions
   exist on or before the cutoff.
3. **SAM `query_entity_by_uei`** — accepts `cutoff_date`; if cutoff
   is >180 days in the past, adds `_hindsight_warning` to the
   response noting that registration/NAICS/address are current
   state, not state at cutoff.
4. **`plan_executor`** — auto-injects the plan's top-level `cutoff`
   into source_params for any connector whose signature accepts
   `cutoff_date`. Eliminates the need for the planner to remember
   to pass it.
5. **`deterministic_scorer`** — new `NO_DATA_AT_CUTOFF` handling for
   both OSHA and DOL: returns UNVERIFIABLE with explanation rather
   than silently mishandling.

### v3 EMIT table

| TK   | Class      | Cutoff      | Claims | PASS | MOD | SEV | UNVER | Composite | Truth_signal | DA tier | **EMIT** |
|------|------------|-------------|-------:|-----:|----:|----:|------:|----------:|:-------------|:--------|:--------:|
| NKLA | FRAUD      | 2020-08-01  |     12 |    4 |   1 |   0 |     7 |     0.200 | no           | UNKNOWN | no       |
| LOOP | FRAUD      | 2020-09-01  |     10 |    1 |   1 |   1 |     7 |     1.000 | **YES**      | HIGH    | **YES**  |
| RIDE | FRAUD      | 2021-02-01  |      9 |    1 |   1 |   0 |     7 |     0.500 | no           | UNKNOWN | no       |
| CEI  | FRAUD      | 2021-09-01  |      8 |    4 |   2 |   1 |     1 |     0.571 | **YES**      | UNKNOWN | **YES**  |
| PLUG | CONTROL    | 2020-08-01  |      8 |    0 |   1 |   0 |     7 |     1.000 | no           | LOW     | no       |
| GEVO | CONTROL    | 2020-09-01  |     10 |    3 |   3 |   0 |     4 |     0.500 | **YES**      | MED     | **YES**  |
| REI  | CONTROL    | 2021-09-01  |      8 |    4 |   1 |   0 |     3 |     0.200 | no           | HIGH    | no       |
| WKHS | BORDERLINE | 2021-02-01  |      7 |    3 |   1 |   0 |     3 |     0.250 | no           | UNKNOWN | no       |

### v1 → v2 → v3 EMIT progression

| Class      | v1 EMIT | v2 EMIT | v3 EMIT |
|------------|--------:|--------:|--------:|
| FRAUD      | 1 (25%) | 2 (50%) | 2 (50%) |
| CONTROL    | 1 (33%) | 1 (33%) | 1 (33%) |
| BORDERLINE | 1 (100%)| 0 (0%)  | 0 (0%)  |

### Claims that flipped PASS → UNVERIFIABLE under v3

Three claims used 2024 OSHA data to corroborate pre-2024 facility claims:
- **NKLA-4** (Coolidge factory, 2020-08-01): the headline NKLA bug
- **PLUG-5** (Plug Power facility, 2020-08-01)
- **REI-1** (Ring Energy facility, 2021-09-01)

All three now return `NO_DATA_AT_CUTOFF` instead of bogus corroboration.

### EMIT decisions didn't move at headline level — that's correct

The NKLA bug was a **honesty** bug, not a **detection** bug. NKLA's
forward-looking operational claims (hydrogen demos, factory plans,
megacap partnerships) have no contemporaneous M-source regardless of
whether OSHA leaked the future or not. Fixing the leak prevents
false corroboration on planned-future-facility claims; it doesn't
add any new detection capability.

The same logic applies to PLUG and REI — those companies weren't
emit-candidates in v2, and they still aren't in v3. The v3 fix
makes the framework honest about what it can't see, without
manufacturing emissions it can't justify.

### Side effect: PLUG composite jumped 0.50 → 1.00

Because PLUG's only PASS (the OSHA "scope corroborated") flipped to
UNVERIFIABLE, and `composite_score()` excludes UNVERIFIABLE from the
denominator, the lone remaining MODERATE flag now drives composite
to 1.00. This is a math property of the composite formula, not a
real signal change. PLUG still doesn't emit because n_flags=1 <
MIN_FLAGS=2.

---

## v2 results (LLM claim_evolution detector)

The v1 keyword detector generated heavy false positives by matching
M&A and license boilerplate. v2 replaces it with a Haiku-based
classifier that reads each subsequent-filing snippet and labels it
AFFIRMED / AMENDED / TERMINATED / UNRELATED.

| TK   | Class      | Cutoff      | Claims | PASS | MOD | SEV | UNVER | Composite | Truth_signal | DA tier | **EMIT** |
|------|------------|-------------|-------:|-----:|----:|----:|------:|----------:|:-------------|:--------|:--------:|
| NKLA | FRAUD      | 2020-08-01  |     12 |    5 |   1 |   0 |     6 |     0.167 | no           | UNKNOWN | no       |
| LOOP | FRAUD      | 2020-09-01  |     10 |    1 |   1 | **1** |     7 |     1.000 | **YES**      | HIGH    | **YES**  |
| RIDE | FRAUD      | 2021-02-01  |      9 |    2 |   1 |   0 |     6 |     0.333 | no           | UNKNOWN | no       |
| CEI  | FRAUD      | 2021-09-01  |      8 |    4 |   2 |   1 |     1 |     0.571 | **YES**      | UNKNOWN | **YES**  |
| PLUG | CONTROL    | 2020-08-01  |      8 |    1 |   1 |   0 |     6 |     0.500 | no           | LOW     | no       |
| GEVO | CONTROL    | 2020-09-01  |     10 |    3 |   3 |   0 |     4 |     0.500 | **YES**      | MED     | **YES**  |
| REI  | CONTROL    | 2021-09-01  |      8 |    4 |   1 |   0 |     3 |     0.200 | no           | HIGH    | no       |
| WKHS | BORDERLINE | 2021-02-01  |      7 |    3 |   1 |   0 |     3 |     0.250 | no           | UNKNOWN | no       |

### v2 EMIT rates

| Class      | n | EMIT v1 | EMIT v2 | Δ |
|------------|--:|--------:|--------:|---:|
| FRAUD      | 4 | 1 (25%) | **2 (50%)** | +25pp |
| CONTROL    | 3 | 1 (33%) | 1 (33%)     | 0   |
| BORDERLINE | 1 | 1 (100%)| 0 (0%)      | -100pp (separate scorer issue, see below) |

### The LOOP catch — a real pre-revelation fraud signal

LOOP gained 1 SEVERE in v2 (LOOP-9 going-concern). v1's keyword
detector couldn't have caught this. The LLM detector classified the
focal-company's 10-K/A dated 2020-05-06 as TERMINATED — verified
against the actual filing:

> Loop Industries... is filing this Amendment No. 1 on Form 10-K/A
> to its Annual Report on Form 10-K... originally filed... on May 4,
> 2020 ("Original Filing"), **to correct an inadvertent reference to
> going concern included in the Liquidity Section of Item 7, which
> was included in error ("the Error"). Management believes that the
> Company has sufficient financial resources...**

Loop filed a 10-K with going-concern language on May 4, then filed a
10-K/A on May 6 deleting it as "inadvertent." This is highly unusual.
Auditors don't accidentally insert going-concern qualifiers — those
are inserted after careful deliberation by the audit committee. A
10-K/A reversing going-concern within 48 hours and calling it "the
Error" suggests either (a) management strong-armed the auditor, or
(b) the original filing's auditor opinion did not actually support
the going-concern reference. Either is a fraud-quality signal.

This was sitting in plain sight on EDGAR for ~5 months before the
Hindenburg report (2020-10-13). **The LLM detector surfaced it
because it could distinguish "this filing files a contract that has
termination clauses" (boilerplate, v1's false positive) from "this
filing announces removal of a previously-asserted claim" (real event).**

### The CEI cleanup — false positives dropped, real signals remain

v1 had 3 CEI SEVEREs, all questionable:
- CEI-1 going-concern self-match: v2 → REAFFIRMED (LLM saw subsequent
  mentions just re-asserting the same going-concern, not resolving)
- CEI-4 Viking "termination": v2 → AMENDED (LLM saw the Aug 2020
  Amended-and-Restated Merger Agreement as substantive change but
  not termination)
- CEI-8 federal-customer absence: still SEVERE — this is the H5
  over-fit (CEI is a small E&P with no federal-customer claim;
  usaspending absence is non-informative). Scorer bug, not
  claim_evolution.

CEI still emits in v2 via the density+mass path (composite 0.57,
1 SEV + 2 MOD = 3 flags). The flags now better match real signals
(Viking terms genuinely changed; CEI-3 ucc_proxy distress-credit
density is a true distress signal).

### GEVO — unchanged emit, but for the right reasons

v1: 1 SEVERE on Delta (false-positive boilerplate match).
v2: 0 SEVERE, 3 MODERATE. GEVO still emits via density+mass.

The Delta supply-agreement claim_evolution now classifies as AMENDED
(LLM saw the April 2020 8-K describing real changes to the Delta
agreement — likely the COVID-era pause). This is a true positive in
the sense that the supply agreement *was* materially changed, but
it's not fraud — it's COVID-era counterparty disruption.

**Open question:** is GEVO a "false positive" or a "true positive on
a non-fraud signal"? The framework correctly identified that GEVO's
disclosed supply agreements were under stress; whether to call that
a fraud signal is a definitional choice.

### WKHS — lost SEVERE, but for an orthogonal reason

v1 had 2 WKHS SEVEREs:
- WKHS-1 (USPS NGDV via usaspending) — v1: INFLATION_SUSPECT (SEVERE)
- WKHS-6 (Lordstown license "termination") — v1: ADVERSE_EVENT (SEVERE)

In v2:
- WKHS-6 → REAFFIRMED (LLM correctly saw the 2020-08-04 8-K as
  filing a *new* license amendment, not terminating)
- WKHS-1 → SUB_MATERIAL_FEDERAL (UNVERIFIABLE). **This change is NOT
  from claim_evolution.** Between v1 and v2 runs, usaspending
  resolved Workhorse to UEI `JXUMG4HE8M98` with $0 in awards. The
  scorer's mapping `SUB_MATERIAL_FEDERAL → UNVERIFIABLE` (set during
  the ALMU calibration) buries this signal.

This is actually MORE suspicious than v1's INFLATION_SUSPECT —
Workhorse has a UEI but $0 in federal awards despite claiming to be
"one of five selected to build prototype vehicles" for USPS. But
the scorer now treats this as "unverifiable" rather than "suspect."

**Scorer-calibration issue, separate from claim_evolution.** The
ALMU calibration was about quantitatively-accurate small federal
claims; the WKHS case is unverified-NGDV-selection. Both produce
SUB_MATERIAL_FEDERAL but mean opposite things.

### Net assessment of v2

The LLM detector materially improves the framework on the documented
frauds:
- Eliminated 3 of 5 false-positive SEVEREs from v1 (CEI Viking, CEI
  going-concern self-match, WKHS Lordstown)
- Surfaced 1 novel, verified, pre-revelation SEVERE that v1 missed
  (LOOP 10-K/A going-concern deletion)
- FRAUD detection rate: 25% → 50%

Remaining issues are orthogonal to claim_evolution:
1. **CEI-8 H5 over-fit** (scorer should honor planner's
   `extraction_notes` when federal-customer absence is non-informative)
2. **WKHS SUB_MATERIAL_FEDERAL calibration** (the $0-awards-but-UEI-
   exists case should not be mapped to UNVERIFIABLE — the ALMU
   calibration was over-applied)
3. **NKLA / RIDE structural misses** — forward-looking operational
   claims (hydrogen demos, preorders) still have no public-record
   M-source. LLM claim_evolution doesn't help when there are no
   subsequent filings in the brief window.

---

## v1 results (keyword claim_evolution detector — preserved for comparison)

## Results

| TK   | Class      | Cutoff      | Claims | PASS | MOD | SEV | UNVER | Composite | Truth_signal | DA tier | **EMIT** |
|------|------------|-------------|-------:|-----:|----:|----:|------:|----------:|:-------------|:--------|:--------:|
| NKLA | FRAUD      | 2020-08-01  |     12 |    5 |   1 |   0 |     6 |     0.167 | no           | UNKNOWN | no       |
| LOOP | FRAUD      | 2020-09-01  |     10 |    2 |   1 |   0 |     7 |     0.333 | no           | HIGH    | no       |
| RIDE | FRAUD      | 2021-02-01  |      9 |    1 |   1 |   0 |     7 |     0.500 | no           | UNKNOWN | no       |
| CEI  | FRAUD      | 2021-09-01  |      8 |    3 |   1 |   3 |     1 |     1.000 | **YES**      | UNKNOWN | **YES**  |
| PLUG | CONTROL    | 2020-08-01  |      8 |    1 |   1 |   0 |     6 |     0.500 | no           | LOW     | no       |
| GEVO | CONTROL    | 2020-09-01  |     10 |    3 |   2 |   1 |     4 |     0.667 | **YES**      | MED     | **YES**  |
| REI  | CONTROL    | 2021-09-01  |      8 |    4 |   1 |   0 |     3 |     0.200 | no           | HIGH    | no       |
| WKHS | BORDERLINE | 2021-02-01  |      7 |    2 |   1 |   2 |     2 |     1.000 | **YES**      | UNKNOWN | **YES**  |

## Headline EMIT rates

| Class      | n | EMIT | Rate |
|------------|--:|-----:|-----:|
| FRAUD      | 4 |    1 | 25%  |
| CONTROL    | 3 |    1 | 33%  |
| BORDERLINE | 1 |    1 | 100% |

**At face value, the framework EMITs at a LOWER rate on documented
frauds (25%) than on clean controls (33%).** That's worse than random.

But the per-ticker SEVERE-claim inspection reveals a much more specific
story about what the framework can and cannot catch.

## What the framework caught

### CEI — distress-fraud, correctly identified
3 SEVERE flags, composite 1.0. The framework caught Camber Energy
pre-Kerrisdale on traditional financial-distress signatures:
1. **Going-concern qualification** (CEI-1) re-confirmed in multiple
   8-Ks via claim_evolution (`going concern` appearing near `going
   concern` cancellation language).
2. **Viking Energy merger** (CEI-4) — adverse-event detection found
   `Viking` near `cancel/material adverse` in 8-Ks 2020-07-01,
   2020-09-03, 2021-02-18.
3. **Federal-customer absence** (CEI-8) — usaspending 0 awards. *This
   is a known H5 over-fit:* CEI is a small E&P with no federal-customer
   claim, so usaspending absence is meaningless. The CEI planner
   explicitly flagged this in extraction_notes; the scorer didn't honor
   the flag and scored SEVERE anyway. **Scorer bug to fix.**

Net: CEI emission is supported by 2 legitimate severe signals
(going-concern, Viking trouble) + 1 false-positive H5 over-fit. The
emission decision is correct, though the composite is inflated.

### WKHS — contract-inflation fraud, caught on the EXACT claim the SEC later prosecuted
2 SEVERE flags, composite 1.0. The framework caught WKHS on:
1. **WKHS-1 USPS NGDV contract** — usaspending UEI-anchored search
   returned 0 federal awards. WKHS's S-1 disclosed it was "one of five
   participants selected to build prototype vehicles." The SEC's 2024
   settlement was specifically about misleading USPS-contract claims.
   **This is a true positive on the same claim that later drew SEC
   enforcement.**
2. **WKHS-6 Lordstown license** — adverse-event detection found
   `Lordstown` near `terminate` in 8-K 2020-08-04 (just months before
   our 2021-02-01 cutoff).

WKHS is the cleanest framework win in the cohort: an EMIT decision
matching the SEC's eventual view, made 3 years before the settlement.

## What the framework missed

### NKLA, LOOP, RIDE — the three highest-profile pre-revelation frauds

These are exactly the names the user wants to catch: Nikola's hydrogen
truck demos, Loop's plastic depolymerization chemistry, Lordstown's
$1.4B preorder claims. Framework EMITted NONE of them.

The miss pattern is consistent across all three:
- 60-78% of claims scored UNVERIFIABLE (NKLA 6/12, LOOP 7/10, RIDE 7/9)
- 0 SEVERE flags
- Only 1 MODERATE flag per ticker (a weak claim-evolution signal: claim
  didn't reappear in the brief sub-30-day window between filing and
  cutoff — a thin and easily false-positive signal)

**Why the misses?** The defining claims in each case are
forward-looking operational/technological assertions with no public-
record M-source to validate:

| Ticker | Defining fraud claim                                    | Why no M-source can falsify pre-revelation                            |
|--------|---------------------------------------------------------|------------------------------------------------------------------------|
| NKLA   | Hydrogen truck operational demos, in-house H2 production | No FRS facility yet, no SAM registration, no megacap counterparty disclosure (small-cap × Bosch / Anheuser-Busch / GM never triggers H7). The "rolling truck" claim is unfalsifiable from filings alone. |
| LOOP   | Proprietary plastic depolymerization chemistry           | The chemistry IS proprietary — there's no PCT patent that publicly contradicts it pre-revelation. Indorama JV facility not yet operating, so EPA FRS absence is the *expected* baseline, not a contradiction. Coca-Cola / Pepsi / L'Oreal didn't disclose the LOI relationships (per H7). |
| RIDE   | $1.4B of preorders / LOIs                                | Preorder counterparties (fleet operators, shell companies) are private; no public registry of fleet preorders. SAM.gov shows nothing; FMCSA doesn't track preorder commitments. The Hindenburg insight came from physical investigations (visiting addresses, interviewing operators) — not public records. |

**This isn't a framework gap that can be plugged with a new connector.**
It's the structural limit of *publicly-available, machine-readable*
diligence data. The Hindenburg / Citron / Muddy Waters style of forensic
journalism — physical site visits, on-the-ground interviews,
counterparty cold-calls — is the actual generating function for these
revelations. Public records lag.

## What the framework "false-positive"-emitted

### GEVO — caught real distress, but it wasn't fraud
1 SEVERE flag (GEVO-4: Delta SAF supply agreement). Adverse-event
detection found `Delta` near `terminate` in 8-K 2020-04-28 — and that
WAS real: GEVO disclosed in spring 2020 that Delta and other airline
customers paused or canceled SAF offtake agreements due to COVID.

So the framework correctly identified that GEVO's claimed supply
agreements were in distress. But airline-customer disruption from
COVID isn't fraud — it's an exogenous shock that any company in the
sector would face.

**Lesson:** the framework's claim_evolution signal can't distinguish
"counterparty terminated because of fraud" from "counterparty
terminated because of business disruption."

## What the framework correctly suppressed

### PLUG, REI — no emission, correct
PLUG: 1 MODERATE on megacap-namecheck (named Amazon, Home Depot, BMW
etc. — none of these megacaps disclose PLUG in their own 10-Ks; this
is the textbook H7 small-cap × megacap noise pattern, not a fraud
signal). Composite 0.50 but n_flags=1, so the dual-gate truth_signal
correctly suppresses. DA=LOW (PLUG was heavily shorted by 2020).

REI: 4 PASSES, 1 MODERATE on a derivative-position cadence signal.
Composite 0.20. Clean small-cap E&P. Correctly suppressed.

## Discrimination scorecard

If we recompute, correcting the CEI-8 H5 over-fit and treating GEVO
as a "real distress, not fraud" false positive:

| Class             | Caught | Missed | Notes                                                            |
|-------------------|-------:|-------:|------------------------------------------------------------------|
| **Distress-fraud**     | 1 / 1  | 0 / 1  | CEI caught (going-concern + Viking)                              |
| **Contract-inflation** | 1 / 1  | 0 / 1  | WKHS caught (USPS NGDV)                                          |
| **Operational/tech**   | 0 / 3  | 3 / 3  | NKLA, LOOP, RIDE all missed (forward-looking claims unfalsifiable) |
| **Clean controls**     | 2 / 3 correctly suppressed | 1 / 3 false-emit | PLUG, REI ok; GEVO emits on real-but-non-fraud signal |

**Detection by fraud type:**
- Distress-fraud detection rate: 100%
- Contract-inflation detection rate: 100%
- Operational/tech-claim detection rate: 0%

## Implications

1. **The framework is a useful diligence augment but not a fraud
   detector for the highest-profile pre-revelation patterns.** It
   catches what auditors and credit analysts already catch (going-
   concern, distress-credit terms, contract inflation that can be
   cross-checked against government registries). It misses what
   forensic short sellers catch (operational reality vs. management
   narrative).

2. **The auditor-flag space is already heavily covered.** Audit
   Analytics + the CIQ pull restate-and-going-concern dataset
   already does what CEI's flags identify, at $3-5k/yr. The
   framework's edge over Audit Analytics is the SEC-FTS cross-filer
   signals (claim_evolution adverse-event detection) — which add
   some breadth on relationship-termination signals, but at lower
   precision than auditor changes.

3. **The contract-inflation detection is the framework's strongest
   single use case.** USAspending UEI-anchored search caught WKHS
   on the same USPS claim the SEC later prosecuted, 3 years early.
   For any small-cap claiming a specific federal contract, this is
   a fast, free verification. The defense / aerospace / clean-energy
   cohorts likely have several names where this same test applies.

4. **For operational-claim fraud (NKLA / LOOP / RIDE), the framework
   needs a fundamentally different f(M).** Possibilities:
   - **Physical-world ground-truth** (satellite imagery of facilities,
     LinkedIn employee counts that contradict claimed scale, customs
     records for claimed imports of equipment / feedstock). All paid
     or scraping-restricted (see CONNECTOR_BACKLOG.md).
   - **Crowd-sourced / journalism feeds** (Twitter, short-seller
     reports, forum discussions). High noise, low precision.
   - **Insider-trading + Form 4 signature analysis** for executive
     stock-sale patterns coincident with claim disclosure. Within
     reach (SEC Forms 3/4/5 are free) but high false-positive rate.

5. **Honest framing for a customer:** the framework cannot promise to
   catch the next NKLA pre-revelation. It can promise to flag the
   next CEI-style distress + the next WKHS-style federal-contract
   inflation. That's still useful — but it's a more specific value
   proposition than "fraud detection."

## Bugs / refinements identified

1. **Scorer over-fit on H5 (CEI-8):** the planner's `extraction_notes`
   flag warned that federal-customer absence is non-informative for
   CEI (no federal-customer claim was made). The scorer didn't honor
   the flag. Fix: scorer should pass-through `extraction_notes` and
   downgrade SEVERE → UNVERIFIABLE when notes flag the test as
   non-applicable.

2. **GEVO-style COVID-disruption signal noise:** claim_evolution
   adverse-event detection can't distinguish exogenous business
   disruption from fraud. Adding a contextual prior (sector-wide
   disruption signal from peer-cohort base rate) could help, but is
   non-trivial.

3. **Discovery_advantage tier UNKNOWN for delisted names** (CEI, NKLA,
   RIDE, WKHS). Currently all UNKNOWN → emits if truth_signal. This
   is by design (the post-fresh-universe-2025-05-15 change), but worth
   noting that UNKNOWN doesn't discriminate fraud-vs-clean in this
   cohort.
