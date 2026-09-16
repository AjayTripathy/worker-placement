# Fintech Lending / BNPL Cohort — Blinded Forward-Test Predictions (v1)

_Generated 2026-05-17T18:27:36.308919Z — cutoff 2026-05-16_

## Methodology

Five names spanning fintech lending (UPST AI-underwriting), BNPL (AFRM), iBuying (OPEN Opendoor), neobank (SOFI), and bank control (COF Capital One). Each ticker analyzed by an isolated, **blinded** Claude Code subagent with no outcome labels, no WebSearch / WebFetch, no shared context. Subagent workflow includes checkpointing.

Fintech-specific calibration emphasis: **origination-volume vs balance-sheet volume vs net revenue** (Heuristic 9). Fintech names routinely emphasize headline volume metrics that aren't balance-sheet risk; this is a disclosure-quality issue more than a fraud signal.

**Cohort caveat:** the framework is built for divergence detection where M-sources are authoritative registries. Consumer-credit-quality claims don't have a clean registry analog; this cohort is expected to produce more UNVERIFIABLE than other verticals. Emissions should be rare and high-conviction.

Forward-bet emission uses the shared v2 emitter.

## Composite ranking

Composite = weighted-mean severity per non-UNVERIFIABLE claim (PASS=0, MODERATE=1, SEVERE=2, RED=3).

| Rank | Ticker | Company | Claims | PASS | MOD | SEVE | RED | UNV | Composite |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | AFRM | Affirm Holdings, Inc. | 8 | 1 | 2 | 0 | 0 | 5 | 0.67 |
| 2 | UPST | Upstart Holdings, Inc. | 8 | 2 | 1 | 0 | 0 | 5 | 0.33 |
| 3 | COF | Capital One Financial Corporation | 8 | 3 | 1 | 0 | 0 | 4 | 0.25 |
| 4 | OPEN | Opendoor Technologies Inc. | 8 | 0 | 0 | 0 | 0 | 7 | 0.00 |
| 5 | SOFI | SoFi Technologies, Inc. | 7 | 4 | 0 | 0 | 0 | 4 | 0.00 |

## Per-ticker findings

### AFRM — Affirm Holdings, Inc.

- **Filing analyzed:** `0001820953-25-000080_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=1, MODERATE=2, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=5
- **Composite severity:** 0.67

#### 🟡 MODERATE_UNDERDELIVERY claims
- **AFRM-2** — Affirm has a material installment-financing services agreement with Amazon.com Services LLC and Amazon Payments, Inc., supported by issued warrants to Amazon (most recently the Second Replacement Warr
  - Interpretation: Heuristic 7: counterparty CIK 0001018724 returns 0 filings naming the claim's subject; counterparty-disclosure gap.
- **AFRM-3** — Affirm has a Global Customer Installment Program Agreement with Shopify Inc. dated February 14, 2025.
  - Interpretation: Heuristic 7: counterparty CIK 0001594805 returns 0 filings naming the claim's subject; counterparty-disclosure gap.

### UPST — Upstart Holdings, Inc.

- **Filing analyzed:** `0001647639-26-000027_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=2, MODERATE=1, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=5
- **Composite severity:** 0.33

#### 🟡 MODERATE_UNDERDELIVERY claims
- **UPST-5** — Upstart hosts its AI lending platform on Amazon Web Services (AWS).
  - Interpretation: Heuristic 7: counterparty CIK 0001018724 returns 0 filings naming the claim's subject; counterparty-disclosure gap.

### COF — Capital One Financial Corporation

- **Filing analyzed:** `0000927628-26-000024_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=3, MODERATE=1, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=4
- **Composite severity:** 0.25

#### 🟡 MODERATE_UNDERDELIVERY claims
- **COF-5** — Capital One relies on Amazon Web Services for cloud infrastructure, on Total System Services LLC (TSYS) for North American and U.K. consumer/commercial credit-card processing, and on Fidelity Informat
  - Interpretation: Heuristic 7: counterparty CIK 0001018724 returns 0 filings naming the claim's subject; counterparty-disclosure gap.

### OPEN — Opendoor Technologies Inc.

- **Filing analyzed:** `0001801169-26-000010_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=0, MODERATE=0, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=7
- **Composite severity:** 0.00


### SOFI — SoFi Technologies, Inc.

- **Filing analyzed:** `0001818874-26-000013_10-K.txt`
- **Claims extracted:** 7
- **Severity distribution:** PASS=4, MODERATE=0, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=4
- **Composite severity:** 0.00


## Forward predictions (12-month falsification window)

Falsification date: **2027-05-16**

**Emission rule (v2):** a bet emits iff `composite_score >= 0.6` (Truth_signal) AND `discovery_advantage_tier IN (HIGH, MED)` (signal is novel — not already discounted by short interest, institutional ownership, or analyst coverage). Discovery_advantage source: finviz.com short_float + inst_own + recom. See `discovery_advantage.py` for tier rules.

### AFRM
- Composite: **0.67**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: YES
- Discovery_advantage: **MED**   short_float=6.8%   inst_own=75%   recom=1.54
- **Decision: EMIT bearish forward bet.**
  - **Forward bet:** within 12 months, the underlying claims will (a) be revised down in the next 10-K / 20-F, (b) be supplanted by a different headline figure that obscures the original gap, or (c) trigger short-seller / analyst coverage that reflects the framework's findings.
  - **Falsification:** if by 2027-05-16 the claims are corroborated by matching counterparty / registry disclosure AND the stock is within ±20% of cutoff price AND no analyst or short-seller has independently identified the same divergence, the prediction is wrong.

### UPST
- Composite: **0.33**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=32.9%   inst_own=63%   recom=2.25
- **Decision: no bet.** Composite 0.33 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### COF
- Composite: **0.25**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=1.3%   inst_own=87%   recom=1.48
- **Decision: no bet.** Composite 0.25 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### OPEN
- Composite: **0.00**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **MED**   short_float=15.8%   inst_own=47%   recom=3.00
- **Decision: no bet.** Composite 0.00 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### SOFI
- Composite: **0.00**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **MED**   short_float=12.8%   inst_own=56%   recom=2.73
- **Decision: no bet.** Composite 0.00 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

## What this is NOT

- **Not a fraud accusation.** Consumer-credit cycles drive fintech results in ways the framework can't always discriminate.
- **Consumer-experience claims** (CFPB complaints, BBB scores) are not plumbed; partial coverage.
- **Not pre-registered.** Commit this report's hash to git.

## Debt and tradeoffs

- **CFPB consumer-complaint registry / FDIC call reports** are the #1 coverage gap for consumer-credit-quality claims. Both are free + structured; worth plumbing.
- **Securitization-trust disclosures** (loan-backed ABS trustee reports) sit off-EDGAR but are public; future-cohort opportunity.
