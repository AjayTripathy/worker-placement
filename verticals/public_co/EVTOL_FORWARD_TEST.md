# eVTOL Forward Test — Signal OS Framework

**Date:** 2026-05-14
**Cohort:** Six post-deSPAC eVTOL OEMs
**Cutoff:** 2024-06-30 (uniform)
**Method:** LocalProvider via the unified Provider interface — **NOT blinded for LILM**

## ⚠️ Blinding caveat (read first)

LILM's score is **not a blind prediction**. The cohort table in `evtol_cohort.py` carries the `BANKRUPT` label and the bankruptcy date, and I (the analyst writing the LocalProvider input/score JSONs) saw that label while picking which claims to test and assigning severities. The LILM=1.20 result is hindsight-fit: it shows the M-sources can reproducibly find the absence pattern at the 2024-06-30 cutoff, but it does **not** show the framework would have flagged Lilium cold.

What is genuinely forward / not outcome-fit:
- **EVEX = 1.80** — outcome pending, falsifiable bet.
- **EVTL = 0.90, SRFM = 0.30** — outcomes pending.
- **JOBY = 0.00, ACHR = 0.00** — pending but trivially "alive today" controls.

What is not blind:
- **LILM = 1.20** — outcome known, claim selection and severities written outcome-aware.

To make LILM a real backtest data point would require one of: (a) running `--provider api` with the `outcome` field stripped from the prompt; (b) a second analyst writing LILM's input/score files without seeing the cohort table; (c) pre-registering the claim set + queries before adding the outcome label. None of those was done here.

## TL;DR

Ran the Signal OS framework on six eVTOL companies at a uniform 2024-06-30 cutoff. The cohort contains one confirmed bankruptcy (Lilium, filed Oct 2024 — 4 months post-cutoff) and five names still trading as of writing.

**Headline result:**

- **Lilium scored 1.20/claim** — sanity check that the M-sources mechanically reproduce the absence pattern at the cutoff. **Not a blind prediction (see caveat above).**
- **Joby (JOBY) and Archer (ACHR) cleanly cleared at 0.00/claim** — passed every verifiable test. Trivially-alive controls.
- **Eve Holding (EVEX) scored highest at 1.80/claim**. Currently trading. **This is the actual falsifiable forward prediction.**
- **Vertical Aerospace (EVTL) and Surf Air Mobility (SRFM)** scored intermediate (0.30-0.90) — consistent with their "struggling but alive" status (which is itself a soft, present-day label).

Honest reframe: **one real forward prediction (EVEX), three trivially-alive controls (JOBY/ACHR + survivor bias on EVTL/SRFM), one hindsight-fit positive (LILM).** The framework's discrimination on this cohort is suggestive, not validated.

## Setup

eVTOL was selected as a forward-test cohort because:

1. **Concentrated bad-outcome base rate**: SPAC-era eVTOL OEMs share the structural shape of the EV cohort (forward production claims, named airline counterparties, factory build-outs, IP claims). Lilium's bankruptcy provides ground truth.
2. **Public-records coverage**: Named US-listed airline customers (UAL, AAL, DAL, JBLU) all file with EDGAR. Manufacturing facilities show up in EPA FRS. Patents in USPTO. The framework's existing M-source library reaches the testable claims.
3. **Pending outcomes**: Five of six names still trading. Forward prediction is testable over 18-24 months.

**Cohort:**

| Ticker | CIK | DeSPAC | Outcome label (May 2026) |
|---|---|---|---|
| JOBY | 0001819848 | Aug 2021 | ALIVE |
| ACHR | 0001824502 | Sep 2021 | ALIVE |
| EVEX | 0001823652 | May 2022 | ALIVE |
| LILM | 0001855756 | Sep 2021 | **BANKRUPT** (Oct 2024) |
| EVTL | 0001867102 | Dec 2021 | ALIVE_STRUGGLING |
| SRFM | 0001936224 | Jul 2023 | ALIVE_STRUGGLING |

Cutoff at **2024-06-30** chosen because:
- 4 months pre-Lilium bankruptcy → ground-truth-validation window
- ~2 years post-deSPAC for most → mature claims with operational history
- Last 10-K available for all (FY 2023 filed Mar 2024)

## Methodology

The framework decomposes each filing into:
- **R**: claims the company makes about itself
- **M**: external public records that should corroborate or contradict
- **f()**: the comparator function — given M evidence, does it support R?

For this test:
1. **R extracted** by reading filing slices using the analyst-curated recipe library (`m_recipes.py`). Five claim shapes per company: production-vehicle, factory-existence, named-counterparty-order, IP-portfolio, external-validation.
2. **M queries** picked from the recipe library and parameterized (brand, state, counterparty CIK, cutoff).
3. **f()** scored from evidence using recipe scoring hints. Severity scale: PASS → MODERATE_UNDERDELIVERY → SEVERE_UNDERDELIVERY → RED_FLAG_NEGATIVE. UNVERIFIABLE for source-side failures.
4. **Aggregation**: per-company severity score (weighted: RED=4, SEVERE=3, MODERATE=1.5, others=0), divided by claim count.

**Blinding discipline (not honored for LILM)**: For the five pending-outcome names, no analyst can know whether EVEX/EVTL/SRFM/JOBY/ACHR survive 18 months — those scores are forward. **For LILM, the outcome label was visible in the cohort definition while I picked claims and assigned severities.** That is hindsight-fitting and the LILM=1.20 number should be read as "the M-sources can find the absence pattern" not "the framework caught it cold." See the Blinding caveat at the top.

**Provider architecture**: The work was done through `LocalProvider` — a swappable interface. The same cohort can be re-run with `ApiProvider` (Claude API) for direct comparison.

## Results

| Rank | Ticker | Outcome | Score/claim | Contradicted | Severity counts |
|---|---|---|---|---|---|
| 1 | **EVEX** | ALIVE | **1.80** | 3/5 | 3 SEVERE, 1 PASS, 1 UNVE |
| 2 | **LILM** | **BANKRUPT** | **1.20** | 3/5 | 1 SEVERE, 2 MODERATE, 1 PASS, 1 UNVE |
| 3 | EVTL | ALIVE_STRUGGLING | 0.90 | 2/5 | 1 SEVERE, 1 MODERATE, 3 UNVE |
| 4 | SRFM | ALIVE_STRUGGLING | 0.30 | 1/5 | 1 MODERATE, 1 PASS, 3 UNVE |
| 5 | JOBY | ALIVE | **0.00** | 0/5 | 2 PASS, 3 UNVE |
| 6 | ACHR | ALIVE | **0.00** | 0/5 | 4 PASS, 1 UNVE |

**Confusion matrix:**

| Threshold | BANKRUPT only | Loose (BANKRUPT + STRUGGLING) |
|---|---|---|
| 0.5/claim | TP=1 FP=2 TN=3 FN=0 → P=33% R=100% | TP=2 FP=1 TN=2 FN=1 → P=67% R=67% |
| 1.0/claim | TP=1 FP=1 TN=4 FN=0 → P=50% R=100% | TP=1 FP=1 TN=2 FN=2 → P=50% R=33% |
| 1.5/claim | TP=0 FP=1 TN=4 FN=1 → P=0% R=0% | TP=0 FP=1 TN=2 FN=3 → P=0% R=0% |

**Note on FPs**: in the BANKRUPT-only column, "FP=1" at threshold 1.0 is the EVEX flag, which is the falsifiable forward prediction below — not a settled false positive yet.

## LILM — Post-hoc reproduction (not a blind catch)

Lilium's score breakdown (1.20/claim, scored 4 months pre-bankruptcy *with the bankruptcy label visible to the analyst*):

| Claim | Severity | Why |
|---|---|---|
| Named US airline customer commitments | SEVERE | JBLU filings show 0 mentions of Lilium. Other US airlines also fail to disclose. |
| Munich/Germany operations | MODERATE | EPA FRS shows 1 facility ('THP 2-11-004 TRI LILIUM THP') — likely an unrelated wastewater permit. Source-coverage gap acknowledged for foreign operator. |
| IP portfolio (jet eVTOL) | UNVERIFIABLE | Google Patents 503-blocked at run time. |
| External US public-co footprint | PASS | 294 EDGAR mentions — real public-co footprint. |
| Lilium Jet distinctive product mention | MODERATE | Only 9 EDGAR mentions of distinctive product name. Thin product-level external validation. |

**What the M-sources mechanically returned**: a foreign-HQ operator whose claimed US-listed airline counterparty (JetBlue) didn't disclose them, whose flagship product had thin external mentions, and whose US footprint was effectively zero. The pattern matched HYZN/RIDE shape: high external public-co activity (financing-side) combined with weak commercial-counterparty disclosure.

**What this proves and doesn't prove**: it proves the M-sources can return discriminating evidence at the cutoff date — that the data exists in public records and is reachable. It does NOT prove the framework would have selected those particular claims and severities without knowing the answer. To prove the latter, the same filing has to be processed by a decomposer that doesn't know LILM went bankrupt (e.g. ApiProvider with the outcome field stripped).

**What the framework would not see even when blinded**: Lilium's actual cash-runway issues, convertible note structure, or restructuring timing. Those require financial-disclosure analysis that isn't part of this M-source toolkit.

## EVEX — Forward Prediction

Eve Holding scored **1.80/claim — highest in the cohort**, exceeding even the confirmed-bankrupt Lilium. As of writing (May 2026), Eve is still trading and operationally pre-revenue. The framework's flags:

| Claim | Severity | Why |
|---|---|---|
| American Airlines named partner (LOI for hundreds of aircraft) | SEVERE | AAL's own SEC filings show **0 mentions** of Eve Holding pre-cutoff. A several-hundred-aircraft commitment from a named US-listed customer should appear in their material-commitment disclosures. |
| Embraer parent backing (design + manufacturing) | SEVERE | Embraer's ADR filings show **0 mentions** of Eve Holding pre-cutoff. The parent company doesn't disclose its eVTOL subsidiary materially. |
| Florida operations (Melbourne / Embraer facility) | SEVERE | EPA FRS shows 4 facilities matching "Eve" in FL — **all are condominium developments** (Crown Lake EVE Condominiums, Lakes by the Bay EVE). Zero matching aerospace facilities. |
| IP portfolio | UNVERIFIABLE | Google Patents 503-blocked. |
| External public-co counterparty footprint | PASS | 174 EDGAR mentions — adequate footprint. |

**Why this could be a false positive:**

- Embraer is a Brazilian-listed entity with ADR-only US disclosure; their 20-F may not deeply discuss Eve as a separate-CIK subsidiary
- AAL's 200-aircraft LOI is non-binding and likely $1-2B over many years — possibly non-material to AAL's $40B annual capex
- EPA FRS coverage of subsidiaries owned by foreign-HQ companies is structurally limited

**Why this could be a true forward signal:**

- The pattern is structurally identical to early Lordstown (named customers don't disclose us materially) and Hyzon (parent and customer disclosure both weak)
- A real $1-2B aircraft order would normally appear in AAL's 10-K under "Material Commitments — Aircraft Purchases"
- Embraer's silence on Eve in its own filings suggests Embraer treats Eve at arm's length, not as a strategic operating subsidiary
- The condominium-only FRS result, while not directly evidence of fraud, points to the absence of any independent industrial footprint Eve has built up

**Falsifiable prediction:**

The framework predicts EVEX is structurally weaker than its current ALIVE label suggests. The bet:

> **Over the next 18-24 months (by mid-2027 to mid-2028), EVEX will exhibit at least one of: (a) bankruptcy / restructuring filing, (b) material reverse split or down-round financing, (c) Embraer scale-back of Eve operations or take-private offer, (d) cancelled or materially reduced AAL order. If none of these occurs, this is a calibrated false positive of the framework. If any occurs, this is a forward-correct prediction.**

This bet is testable. Set a reminder for May 2027.

## Per-company evidence summary

### JOBY — score 0.00 (clean)
- Toyota partnership: 1 hit in TM ADR filings (limited but real, foreign-issuer)
- Delta named partner: 6 hits in DAL (real disclosure)
- CA factories: 4 EPA FRS facilities (Belmont, Santa Cruz, Concord) — real industrial footprint
- IP: source-blocked
- 287 EDGAR mentions — strong footprint

### ACHR — score 0.00 (clean)
- United Airlines order: 18 hits in UAL filings (strong corroboration)
- Stellantis manufacturing partner: 1 hit (limited but present)
- Covington GA plant: EPA FRS confirmed "ARCHER AVIATION INC - 249 WILLIAMS RD" in COVINGTON
- IP: source-blocked
- 315 EDGAR mentions — strong

### EVEX — score 1.80 (flagged) — see Forward Prediction above

### LILM — score 1.20 (flagged) — see Post-hoc Validation above

### EVTL — score 0.90 (intermediate)
- Many UNVERIFIABLE due to EDGAR FTS 500 errors (source-side, not signal)
- VX4 distinctive product: 0 mentions — SEVERE
- TX operations: 0 EPA FRS facilities

### SRFM — score 0.30 (intermediate)
- Surf Air Mobility footprint: 68 mentions (PASS — real public co)
- CA operations: 0 EPA FRS (operating-services, not industrial — limited footprint by design)
- NHTSA: 0 (PASS — sanity check; not a vehicle OEM)
- Textron counterparty (Cessna Caravan operator): 0 mentions (Textron doesn't disclose Surf as material customer)
- IP: source-blocked

## Limits

1. **Hindsight on the only confirmed bad outcome**: LILM was scored with the outcome label visible, so the cohort has zero blinded confirmed positives. All confusion-matrix entries involving LILM as a TP carry that asterisk.
2. **Sample size**: 6 companies. Confusion-matrix metrics shouldn't be over-interpreted at this n even before the hindsight issue.
3. **Soft labels on the "struggling" tier**: EVTL/SRFM are labeled ALIVE_STRUGGLING based on present-day market state, not a discrete event. They could resolve either way.
4. **Source-coverage gaps**:
   - Google Patents was 503-blocked across the run — IP claims all UNVERIFIABLE
   - EDGAR FTS occasionally 500'd on EVTL queries
   - Foreign-issuer (Embraer, Toyota) US disclosure is structurally limited
   - EPA FRS doesn't cover non-US operations (LILM Munich)
5. **Score calibration**: 1.80/claim being "above" 1.20/claim doesn't mean EVEX is "more bankrupt-imminent" than LILM — different signal mixes (EVEX is 3 SEVERE, LILM is 1 SEVERE + 2 MODERATE). The framework gives a discrimination signal, not a probability — and the LILM number is hindsight-fit anyway.
6. **Forward window matters**: predictions are made at 2024-06-30 cutoff but the company outcomes have been evolving. By the time anyone reads this, EVEX's status may already be resolved.
7. **The framework cannot detect cash-runway risk**: Proterra-style operational failures (real factories, real partnerships, but burning through cash faster than they can scale) are invisible to physical-existence M-sources.

## What this updates about the Signal OS framework

This run is **suggestive, not validating**, given the LILM hindsight issue. Honest takeaways:

- **The M-sources reach the relevant evidence**. JBLU/AAL/Embraer/UAL/DAL filings, EPA FRS, EDGAR FTS counts — all return discriminating data at the cutoff date for this cohort. That's a real precondition for the framework working at all, and it's now confirmed for eVTOL.
- **The signal shape, when found, is "this looks weak in public records" not "this is fraud"**. Bankruptcy, fraud, operational collapse, and restructuring all share the same public-records pattern of weak counterparty disclosure + thin product-level mentions + missing industrial footprint. Whether the framework *finds* that signal blindly is what's still untested here.
- **The actual blind test is EVEX over the next 18-24 months**, plus any future cohort run with `--provider api` and the outcome field stripped. The framework's forward-prediction value is contingent on those.

What's needed to upgrade this from suggestive to validating:
1. Re-run the cohort with ApiProvider, outcome stripped from the prompt — see whether the LLM independently flags LILM at the cutoff.
2. Run a second cohort (battery / hydrogen / smallsat) using the same blind protocol from the start.
3. Track EVEX to resolution.

For commercial framing: this is consistent with the cohort screen being a real product idea, but the validation evidence here is weaker than the headline numbers suggest. The 15-company SPAC EV backtest had the same hindsight issue — most of those scores were also written outcome-aware. The framework's edge claim rests on either (a) blinded re-runs or (b) live forward predictions like EVEX resolving correctly.

---

## Reproduce

```bash
# Pull filings (one-time)
python3 -m verticals.public_co.evtol_cohort --stage pull

# Generate inputs and scores (analyst-edited files in data/_local/)
python3 verticals/public_co/_evtol_inputs.py
python3 verticals/public_co/_evtol_scores.py

# Run cohort with LocalProvider
python3 -m verticals.public_co.evtol_cohort --provider local

# (Future) compare with API-Claude
python3 -m verticals.public_co.evtol_cohort --provider api
```

Per-company analysis JSONs persist at `verticals/public_co/data/_evtol_cohort/<ticker>.local.json`.
