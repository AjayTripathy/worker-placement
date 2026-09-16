# Cell/Gene Therapy Cohort — Blinded Forward-Test Predictions (v1)

_Generated 2026-05-17T08:31:59.304576Z — cutoff 2026-05-16_

## Methodology

Seven names spanning cell/gene-therapy and CRISPR pure-plays (SAVA Cassava Sciences, CRSP CRISPR Therapeutics Swiss 20-F, BEAM Beam Therapeutics base-editing, EDIT Editas Medicine, NTLA Intellia in-vivo CRISPR) and mature commercial-biotech controls (REGN Regeneron, VRTX Vertex). Each ticker analyzed by an isolated, **blinded** Claude Code subagent with no outcome labels, no WebSearch / WebFetch, no shared context. Subagent workflow includes checkpointing.

Biotech-specific calibration emphasis: **trial-phase ladder** discipline (Heuristic 9). preclinical -> IND -> Phase 1 -> Phase 2 -> Phase 3 -> filed -> approved are six distinct claims with distinct ClinicalTrials.gov registrations. Conflating interim Phase 2a with pivotal Phase 3 status is the central evasion pattern.

**Killer M-source for this cohort:** clinical_trials.gov is directly plumbed; pipeline-asset claims are verifiable at the NCT-number level. openFDA cross-checks approval claims.

Forward-bet emission uses the shared v2 emitter.

## Composite ranking

Composite = weighted-mean severity per non-UNVERIFIABLE claim (PASS=0, MODERATE=1, SEVERE=2, RED=3).

| Rank | Ticker | Company | Claims | PASS | MOD | SEVE | RED | UNV | Composite |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | EDIT | Editas Medicine, Inc. | 8 | 5 | 3 | 0 | 0 | 0 | 0.38 |
| 2 | SAVA | Cassava Sciences, Inc. | 9 | 7 | 2 | 0 | 0 | 0 | 0.22 |
| 3 | CRSP | CRISPR Therapeutics AG | 8 | 7 | 1 | 0 | 0 | 0 | 0.12 |
| 4 | BEAM | Beam Therapeutics Inc. | 9 | 8 | 1 | 0 | 0 | 0 | 0.11 |
| 5 | NTLA | Intellia Therapeutics, Inc. | 8 | 8 | 0 | 0 | 0 | 0 | 0.00 |
| 6 | REGN | Regeneron Pharmaceuticals, Inc. | 8 | 8 | 0 | 0 | 0 | 0 | 0.00 |
| 7 | VRTX | Vertex Pharmaceuticals Incorporated | 8 | 8 | 0 | 0 | 0 | 0 | 0.00 |

## Per-ticker findings

### EDIT — Editas Medicine, Inc.

- **Filing analyzed:** `0001650664-26-000017_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=5, MODERATE=3, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.38

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C3** — BMS / Juno collaboration has produced 14 programs; BMS CD19 HD Allo CAR T in Phase 1.
  - Interpretation: EDGAR fulltext search of BMS (CIK 0000014272) returns ZERO hits for 'Editas' across all forms — a notable absence given Editas has received $159M cumulative from BMS and claims 14 active programs. Juno's 27 trials on ClinicalTrials.gov list BMS and Celgene as collaborators but NOT Editas in the coll
- **C7** — Cash $146.6M at 12/31/2025; runway into Q3 2027; $1.6B accumulated deficit; 2025 net loss $160.1M.
  - Interpretation: No going-concern qualifier in any Editas filing — consistent with the company's stated 18+ month runway. However, several latent distress markers are present and accurately disclosed: (a) lost well-known seasoned issuer (WKSI) status in March 2025, forcing a downsized shelf and reduced ATM capacity 
- **C8** — Cumulative BMS payments $159.0M; 2025 BMS collaboration revenue $23.2M; $44.5M deferred revenue at YE 2025.
  - Interpretation: Revenue is overwhelmingly 'collaboration revenue' rather than product sales (Heuristic 11) — disclosed as such, structural fact. The 2024 Amendment extending the BMS collaboration to November 2026 with one expiring extension option already used reduces forward visibility. BMS's EDGAR filings do not 

### SAVA — Cassava Sciences, Inc.

- **Filing analyzed:** `0001437749-26-007962_10-K.txt`
- **Claims extracted:** 9
- **Severity distribution:** PASS=7, MODERATE=2, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.22

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C7** — Recorded loss contingencies of $35.25M in FY2025 for legal matters relating to terminated simufilam/SavaDx programs.
  - Interpretation: MODERATE because this is a material adverse fact (signal of unresolved securities-class-action / research-integrity allegation exposure). The disclosure itself is honest, but the $35.25M accrual and 'reasonably possible additional loss not estimable' language indicates substantial open-ended litigat
- **C8** — Liquidity: $95.5M cash; $496.1M accumulated deficit; $50M ATM undrawn; 12 months of runway claimed.
  - Interpretation: MODERATE: 12-month runway claim is conservative; actual runway is materially longer at maintenance burn. However, accumulated deficit of $496.1M with no approved product and clinical hold on the sole remaining program means commercial trajectory is highly uncertain. NOT a going-concern issue at this

### CRSP — CRISPR Therapeutics AG

- **Filing analyzed:** `0001193125-26-048957_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=7, MODERATE=1, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.12

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C4** — Sirius Therapeutics partnership (May 2025): CTX611 (FXI siRNA) in ongoing Phase 2 TKA trial; up to ~$407.5M milestones; 1.84M CRSP shares issued at $38 as partial consideration.
  - Interpretation: Partnership existence corroborated by own-filing share-issuance event. Trial registration is jurisdictionally fragile (Sirius is China-domiciled). MODERATE because the operational claim (Phase 2 TKA underway) is not independently verifiable in ClinicalTrials.gov — could be in NMPA/CDE registry only.

### BEAM — Beam Therapeutics Inc.

- **Filing analyzed:** `0001193125-26-065194_10-K.txt`
- **Claims extracted:** 9
- **Severity distribution:** PASS=8, MODERATE=1, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.11

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C9** — $500M senior secured term loan with Sixth Street Lending Partners (Feb 24, 2026; SOFR+6.50%, matures 2033, secured by IP, liquidity covenant $40M-$125M tied to market-cap floor $1.75B); net losses $80
  - Interpretation: Calibration heuristic 10 (distress markers): this is a real signal even though disclosure is accurate. The facility is high-cost (SOFR+650 bps, 1% floor) and secured by Beam's core IP including risto-cel — an aggressive collateral package that creates real downside if the BLA slips or the market cap

### NTLA — Intellia Therapeutics, Inc.

- **Filing analyzed:** `0000950170-25-029007_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=8, MODERATE=0, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.00


### REGN — Regeneron Pharmaceuticals, Inc.

- **Filing analyzed:** `0000872589-26-000008_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=8, MODERATE=0, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.00


### VRTX — Vertex Pharmaceuticals Incorporated

- **Filing analyzed:** `0000875320-26-000056_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=8, MODERATE=0, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.00


## Forward predictions (12-month falsification window)

Falsification date: **2027-05-16**

**Emission rule (v2):** a bet emits iff `composite_score >= 0.6` (Truth_signal) AND `discovery_advantage_tier IN (HIGH, MED)` (signal is novel — not already discounted by short interest, institutional ownership, or analyst coverage). Discovery_advantage source: finviz.com short_float + inst_own + recom. See `discovery_advantage.py` for tier rules.

### EDIT
- Composite: **0.38**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **MED**   short_float=10.3%   inst_own=54%   recom=2.17
- **Decision: no bet.** Composite 0.38 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### SAVA
- Composite: **0.22**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **MED**   short_float=14.5%   inst_own=28%   recom=1.00
- **Decision: no bet.** Composite 0.22 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### CRSP
- Composite: **0.12**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=25.1%   inst_own=73%   recom=1.93
- **Decision: no bet.** Composite 0.12 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### BEAM
- Composite: **0.11**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=22.3%   inst_own=96%   recom=1.28
- **Decision: no bet.** Composite 0.11 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### NTLA
- Composite: **0.00**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=32.9%   inst_own=76%   recom=2.21
- **Decision: no bet.** Composite 0.00 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### REGN
- Composite: **0.00**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=3.2%   inst_own=87%   recom=1.57
- **Decision: no bet.** Composite 0.00 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### VRTX
- Composite: **0.00**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=1.7%   inst_own=94%   recom=1.59
- **Decision: no bet.** Composite 0.00 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

## What this is NOT

- **Not a fraud accusation.** Biotech pipelines fail for many legitimate reasons unrelated to disclosure quality.
- **ClinicalTrials.gov coverage is non-exhaustive** for preclinical or foreign-only trials.
- **Not pre-registered.** Commit this report's hash to git.

## Debt and tradeoffs

- **Foreign-trial coverage gap.** China-only and EMA-only trials may not appear in clinical_trials.gov.
- **Manufacturing-capacity verification** for cell/gene therapy is partial: viral-vector and LNP CDMO capacity isn't in a single registry.
