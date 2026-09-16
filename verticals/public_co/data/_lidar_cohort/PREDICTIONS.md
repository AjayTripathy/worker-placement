# Lidar / ADAS Cohort — Blinded Forward-Test Predictions (v1)

_Generated 2026-05-17T07:20:48.219623Z — cutoff 2026-05-16_

## Methodology

Five US-listed automotive-lidar / ADAS sensor pure-plays: LAZR, AEVA, OUST, INVZ (Israeli foreign private issuer, 20-F filer), MVIS. Each ticker was analyzed by an isolated, **blinded** Claude Code subagent with no outcome labels, no WebSearch / WebFetch access, no shared context with other tickers. Each subagent:

1. Read the company's most recent pre-cutoff filing (most recent 10-K for US filers, 20-F for INVZ, S-1 if no 10-K yet, 10-Q for newer interim disclosures).
2. Extracted 5-8 specific, testable, falsifiable factual claims.
3. Picked M-source queries from the catalog (EDGAR full-text against counterparty CIKs for OEM-design-win cross-check, USPTO ODP for FMCW / MEMS / optics patent claims, EPA FRS for manufacturing claims, USAspending for federal-contract claims).
4. Executed queries and scored each claim PASS / MODERATE_UNDERDELIVERY / SEVERE_UNDERDELIVERY / RED_FLAG_NEGATIVE / UNVERIFIABLE.

**Lidar-specific calibration emphasis:** the **design-win stage ladder** discipline (Heuristic 3 with extra weight) — RFQ → selection → design-win awarded → A/B/C-sample → tooling-complete → Start-of-Production (SOP) → series production at volume. Conflating these stages in marketing-tier language while the financial-statement notes reveal a lower stage is the central evasion pattern. Counterparty-disclosure threshold (Rule 7) applied hard: claimed series-production contracts with Tier-1 OEMs should appear in the OEM's 10-K / 20-F; absence is a hard contradiction.

## Composite ranking

Composite = weighted-mean severity per non-UNVERIFIABLE claim (PASS=0, MODERATE=1, SEVERE=2, RED=3).

| Rank | Ticker | Company | Claims | PASS | MOD | SEVE | RED | UNV | Composite |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | AEVA | Aeva Technologies, Inc. | 5 | 1 | 3 | 0 | 0 | 1 | 0.75 |
| 2 | MVIS | MicroVision, Inc. | 5 | 2 | 1 | 1 | 0 | 1 | 0.75 |
| 3 | OUST | Ouster, Inc. | 5 | 1 | 2 | 0 | 0 | 2 | 0.67 |
| 4 | INVZ | Innoviz Technologies Ltd. | 8 | 6 | 1 | 0 | 0 | 1 | 0.14 |
| 5 | LAZR | Luminar Technologies, Inc. | 5 | 4 | 0 | 0 | 0 | 1 | 0.00 |

## Per-ticker findings

### AEVA — Aeva Technologies, Inc.

- **Filing analyzed:** `0001193125-26-116518_10-K.txt`
- **Claims extracted:** 5
- **Severity distribution:** PASS=1, MODERATE=3, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=1
- **Composite severity:** 0.75

#### 🟡 MODERATE_UNDERDELIVERY claims
- **AEVA-1** — Selected by a top European passenger OEM (unnamed).
  - Interpretation: Pre-SOP design-win-style claim with anonymized counterparty and no platform/SOP date triggers Calibration Heuristic 3 (planned vs operational) — disclosure-quality issue without rising to a hard contradiction since the OEM is not named.
- **AEVA-3** — $100M Apollo convertible notes due 2032 at 4.375%, closed Nov 6, 2025.
  - Interpretation: Note issuance verified via own cash flow; transaction itself is real. Severity elevated to MODERATE due to (i) Heuristic 10 — 25-NSE filed 2026-03-11 in filings_index plus prior 1-for-5 reverse split (March 2024) constitute a delisting fingerprint, and (ii) interest-in-stock structure plus $757.3M a
- **AEVA-5** — Three customers = 72% of AR (FY2025); customers undisclosed.
  - Interpretation: Single-customer-default risk is material at $18M revenue with 72% AR concentration in 3 customers — disclosure-quality issue (anonymized counterparties) combined with pre-commercial revenue scale rates MODERATE rather than UNVERIFIABLE because the concentration itself is a confirmed risk factor.

### MVIS — MicroVision, Inc.

- **Filing analyzed:** `0001493152-26-008898_10-K`
- **Claims extracted:** 5
- **Severity distribution:** PASS=2, MODERATE=1, SEVERE=1, RED_FLAG=0, UNVERIFIABLE=1
- **Composite severity:** 0.75

#### 🟠 SEVERE_UNDERDELIVERY claims
- **MVIS-3** — IRIS sensor achieved start of production in April 2024.
  - Interpretation: Heuristic 3 violation: 'start of production in April 2024' is conflated with engineering-sample deliveries used for road-data collection and training. No OEM/Tier-1 disclosure of an IRIS series-production program exists in EDGAR; the original SOP claim belonged to Luminar, whose only known platform (Volvo EX90) was widely reported delayed/de-spec'd. Conflating sample-build with SOP without a named
#### 🟡 MODERATE_UNDERDELIVERY claims
- **MVIS-1** — Acquired Luminar's worldwide lidar business (IRIS, HALO) Feb 3, 2026 for $33.0M via bankruptcy-court approval.
  - Interpretation: Acquisition is documented in MVIS's own 10-K and 8-K/A trail (2026-04-21), but the IRIS/HALO assets came from a bankrupt seller whose own 10-K disclosure is unavailable post-Ch.11; combined with prior IRIS SOP being a Luminar (not MVIS) milestone, this is a distress-asset purchase whose claimed auto

### OUST — Ouster, Inc.

- **Filing analyzed:** `0001628280-26-013313_10-K.txt`
- **Claims extracted:** 5
- **Severity distribution:** PASS=1, MODERATE=2, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=2
- **Composite severity:** 0.67

#### 🟡 MODERATE_UNDERDELIVERY claims
- **OUST-2** — DF solid-state lidar designed for automotive OEM ADAS production wins.
  - Interpretation: Heuristic 3 (planned vs operational): filing language is 'prototypes' / 'will meet requirements' / 'positioned to capture' — pre-SOP and no named OEM design-win or SOP date; no Tier-1 (Aptiv) counterparty corroboration. Claim is aspirational, not a hard contradiction (no series-production claim asse
- **OUST-5** — $211.2M liquidity supports >=12 months operations despite $973.4M accumulated deficit.
  - Interpretation: Heuristic 10-adjacent: while no Form 15 / 25-NSE filed, the ATM is essentially exhausted ($2.5M remaining of $100M), historical reliance on equity issuance to fund losses, and large accumulated deficit relative to liquidity make the 12-month runway dependent on continued operating-loss reduction or 

### INVZ — Innoviz Technologies Ltd.

- **Filing analyzed:** `0001178913-26-000724_20-F.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=6, MODERATE=1, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=1
- **Composite severity:** 0.14

#### 🟡 MODERATE_UNDERDELIVERY claims
- **INVZ-4** — Innoviz signed a 2024 Term Sheet with Mobileye Vision Technologies Ltd. for supply of Innoviz LiDARs for Mobileye programs.
  - Interpretation: Per Heuristic 7, absence in Mobileye filings for a pre-binding term sheet is MODERATE_UNDERDELIVERY (term sheet level — Mobileye has no obligation yet to recognize this commercially, but two years post-signing one would expect some directional language in Mobileye's filings if the program were progr

### LAZR — Luminar Technologies, Inc.

- **Filing analyzed:** `0001140361-26-011477_10-K.txt`
- **Claims extracted:** 5
- **Severity distribution:** PASS=4, MODERATE=0, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=1
- **Composite severity:** 0.00


## Forward predictions (12-month falsification window)

Falsification date: **2027-05-16**

**Emission rule (v2):** a bet emits iff `composite_score >= 0.6` (Truth_signal) AND `discovery_advantage_tier IN (HIGH, MED)` (signal is novel — not already discounted by short interest, institutional ownership, or analyst coverage). Discovery_advantage source: finviz.com short_float + inst_own + recom. See `discovery_advantage.py` for tier rules.

### AEVA
- Composite: **0.75**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: YES
- Discovery_advantage: **MED**   short_float=18.9%   inst_own=60%   recom=1.40
- **Decision: EMIT bearish forward bet.**
  - **Forward bet:** within 12 months, the underlying claims will (a) be revised down in the next 10-K / 20-F, (b) be supplanted by a different headline figure that obscures the original gap, or (c) trigger short-seller / analyst coverage that reflects the framework's findings.
  - **Falsification:** if by 2027-05-16 the claims are corroborated by matching counterparty / registry disclosure AND the stock is within ±20% of cutoff price AND no analyst or short-seller has independently identified the same divergence, the prediction is wrong.

### MVIS
- Composite: **0.75**   RED_FLAGs: 0   SEVERE: 1   → Truth_signal: YES
- Discovery_advantage: **LOW**   short_float=20.4%   inst_own=27%   recom=1.00
- **Decision: SUPPRESS** — Truth_signal present but Discovery_advantage LOW (crowded short, already-known bear case). Framework's edge is in novel divergence; this signal is real but not actionable as alpha. Recorded as a confirmation, not a bet.

### OUST
- Composite: **0.67**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: YES
- Discovery_advantage: **HIGH**   short_float=8.9%   inst_own=46%   recom=1.43
- **Decision: EMIT bearish forward bet.**
  - **Forward bet:** within 12 months, the underlying claims will (a) be revised down in the next 10-K / 20-F, (b) be supplanted by a different headline figure that obscures the original gap, or (c) trigger short-seller / analyst coverage that reflects the framework's findings.
  - **Falsification:** if by 2027-05-16 the claims are corroborated by matching counterparty / registry disclosure AND the stock is within ±20% of cutoff price AND no analyst or short-seller has independently identified the same divergence, the prediction is wrong.

### INVZ
- Composite: **0.14**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **MED**   short_float=10.0%   inst_own=25%   recom=2.00
- **Decision: no bet.** Composite 0.14 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### LAZR
- Composite: **0.00**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **UNKNOWN**   short_float=?   inst_own=?   recom=?
- **Decision: no bet.** Composite 0.00 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

## What this is NOT

- **Not a fraud accusation.** RED_FLAG_NEGATIVE means the filing claim diverges from independent registry evidence at the cutoff. It does not mean the company is lying. Multiple legitimate reasons exist for OEM-counterparty-disclosure absence (sub-tier supply through a Tier-1 integrator that obscures the lidar OEM name; platforms in pre-production not yet material to the OEM; confidential supplier-agreement clauses).
- **Not a trade recommendation.** Lidar names are mostly micro/small-cap and shortability is variable. See prior `_distress_sift/PREDICTIONS.md` for shortability methodology.
- **Not pre-registered.** For the predictions to count as honest forward bets they need a cryptographic timestamp. Recommend committing this report's hash to git or an external timestamp service.

## Debt and tradeoffs

- **Subagent variance.** Five independent runs produced different claim selection per ticker. Re-runs with different sampling can shift the result.
- **OEM 20-F counterparty disclosure.** Volvo, Mercedes, BMW, VW, Stellantis are foreign filers (20-F) — the EDGAR full-text search covers their US filings (20-F + 6-K) but their primary annual reports outside the US are not in EDGAR. Counterparty-absence in 20-F is suggestive but not definitive without checking the foreign filing.
- **NHTSA component scope.** NHTSA does not register lidar suppliers (it registers complete vehicles). Heuristic 5 explicitly excludes NHTSA queries against the lidar company name.
- **Coverage gaps surfaced by subagents (queued for `connectors_to_add.md`):**
  - IATF 16949 / AEC-Q100 automotive-supplier certification registries (no current connector)
  - ISO-26262 functional-safety certification registries
  - DOT NHTSA OEM-supplier disclosure database (sub-tier supplier names in vehicle compliance filings)
