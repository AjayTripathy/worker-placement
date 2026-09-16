# Advanced Nuclear / SMR Cohort — Blinded Forward-Test Predictions (v1)

_Generated 2026-05-17T07:20:48.312047Z — cutoff 2026-05-16_

## Methodology

Five US-listed advanced-nuclear / SMR / nuclear-fuel names: 3 speculative pre-revenue pure-plays (OKLO, NNE, ASPI) + 2 revenue-stage controls (LEU, BWXT). Each ticker was analyzed by an isolated, **blinded** Claude Code subagent (NNE / ASPI completed in-process after the cohort run stalled mid-scoring on 2026-05-16) with no outcome labels, no WebSearch / WebFetch access, no shared context with other tickers. Each subagent:

1. Read the company's most recent pre-cutoff filing (most recent 10-K or S-1).
2. Extracted 5-8 specific, testable, falsifiable factual claims.
3. Picked M-source queries from the catalog (USAspending, USPTO ODP, EDGAR full-text against counterparty CIKs, EPA FRS).
4. Executed queries and scored each claim PASS / MODERATE_UNDERDELIVERY / SEVERE_UNDERDELIVERY / RED_FLAG_NEGATIVE / UNVERIFIABLE.

**Calibration heuristics applied with extra weight here:** Heuristic 3 (planned vs operational — nuclear timelines slip routinely); Heuristic 7 (counterparty-disclosure threshold — Tier-1 utility / hyperscaler PPAs should appear in counterparty 10-Ks).

**Catalog gaps surfaced for the nuclear vertical specifically:** NRC ADAMS docket / topical-report registry; DFC commitment registry; DOE-OSTI / INL Strategic Partnership Project (SPP) agreement registry; foreign regulator coverage (UK ONR, Necsa, CNSC, Health Canada).

## Composite ranking

Composite = weighted-mean severity per non-UNVERIFIABLE claim (PASS=0, MODERATE=1, SEVERE=2, RED=3).

| Rank | Ticker | Company | Claims | PASS | MOD | SEVE | RED | UNV | Composite |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | ASPI | ASP Isotopes Inc. | 7 | 4 | 2 | 0 | 0 | 1 | 0.33 |
| 2 | OKLO | Oklo Inc. | 9 | 7 | 2 | 0 | 0 | 0 | 0.22 |
| 3 | NNE | NANO Nuclear Energy Inc. | 8 | 5 | 1 | 0 | 0 | 2 | 0.17 |
| 4 | LEU | Centrus Energy Corp | 8 | 6 | 0 | 0 | 0 | 2 | 0.00 |
| 5 | BWXT | BWX Technologies, Inc. | 8 | 8 | 0 | 0 | 0 | 0 | 0.00 |

## Per-ticker forward predictions

### ASPI — ASP Isotopes Inc.

- **Filing analyzed:** `0001193125-26-151294_10-K.txt`
- **Claims extracted:** 7
- **Severity distribution:** PASS=4, MODERATE=2, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=1
- **Composite severity:** 0.33

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C1** — ASPI/QLE has definitive agreements with TerraPower: a $22M (10% OID) term loan to partially fund construction of a uranium enrichment facility in Pelindaba, South Africa, plus an Initial Supply Agreem
  - Interpretation: Term loan ($22M with 10% OID = $19.8M cash) is verifiable in principle from ASPI cash flow disclosure (not part of M-source check here). The HALEU supply agreement is a binding contract per the filing, but is conditioned on facility construction completing and on commercial enrichment capability tha
- **C6** — In January 2026 ASPI acquired Renergen (formerly JSE:REN / ASX:RLT), South Africa's leading onshore natural gas explorer and first integrated producer of liquid helium and LNG; Renergen has IDC and DF
  - Interpretation: Acquisition is internally consistent across ASPI filings and verifiable via foreign-exchange delisting records. The pivot concern is the Heuristic 3 stage gap on the DFC funding: 'conditionally approved up to $500M' is being narrated alongside Phase 2 of a $1B+ build — without disclosure of the cond

### OKLO — Oklo Inc.

- **Filing analyzed:** `0001628280-26-018698_10-K.txt`
- **Claims extracted:** 9
- **Severity distribution:** PASS=7, MODERATE=2, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.22

#### 🟡 MODERATE_UNDERDELIVERY claims
- **C1** — Jan 2026 Prepayment Agreement with Meta Platforms to develop a 1.2 GW power campus in Pike County, OH.
  - Interpretation: The Prepayment Agreement is dated Jan 5, 2026. Meta has filed multiple 10-K/10-Q since then but does not yet mention Oklo by name. Under Heuristic 7, a real prepayment from a hyperscaler for 1.2 GW of nuclear power would likely be material to Meta. However, the deal is recent and the prepayment mech
- **C2** — Dec 2024 12 GW Master Power Agreement with Switch, Ltd., 'one of the largest corporate PPAs in history'.
  - Interpretation: 'Master Power Agreement' is a framework — not a binding PPA with specific MW/date/price commitments per the Heuristic 3 stage ladder. Magnitude (12 GW = ~160 reactors) is implausibly large versus Oklo's actual stage (no licensed unit; first INL Aurora not yet built). Marketing language ('one of the 

### NNE — NANO Nuclear Energy Inc.

- **Filing analyzed:** `0001493152-25-028285_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=5, MODERATE=1, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=2
- **Composite severity:** 0.17

#### 🟡 MODERATE_UNDERDELIVERY claims
- **NNE-5** — HALEU Energy Fuel Inc. (NNE subsidiary) has a Memorandum of Understanding dated March 30, 2023 with Centrus Energy Corp for HALEU fuel supply collaboration.
  - Interpretation: Counterparty silence on a 3-year-old MoU with a small pre-revenue counterparty is consistent with Heuristic 4 (non-binding strategic understanding, not material to the larger party). However, the asymmetry — NNE keeps citing 'HALEU Energy Fuel' in 27 filings, Centrus in 0 — suggests the MoU has not 

### LEU — Centrus Energy Corp

- **Filing analyzed:** `0001628280-26-007117_10-K.txt`
- **Claims extracted:** 8
- **Severity distribution:** PASS=6, MODERATE=0, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=2
- **Composite severity:** 0.00


### BWXT — BWX Technologies, Inc.

- **Filing analyzed:** `None`
- **Claims extracted:** 8
- **Severity distribution:** PASS=8, MODERATE=0, SEVERE=0, RED_FLAG=0, UNVERIFIABLE=0
- **Composite severity:** 0.00


## Forward predictions (12-month falsification window)

Falsification date: **2027-05-16**

**Emission rule (v2):** a bet emits iff `composite_score >= 0.6` (Truth_signal) AND `discovery_advantage_tier IN (HIGH, MED)` (signal is novel — not already discounted by short interest, institutional ownership, or analyst coverage). Discovery_advantage source: finviz.com short_float + inst_own + recom. See `discovery_advantage.py` for tier rules.

### ASPI
- Composite: **0.33**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=22.1%   inst_own=56%   recom=1.00
- **Decision: no bet.** Composite 0.33 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### OKLO
- Composite: **0.22**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=20.2%   inst_own=53%   recom=1.85
- **Decision: no bet.** Composite 0.22 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### NNE
- Composite: **0.17**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=22.7%   inst_own=48%   recom=1.40
- **Decision: no bet.** Composite 0.17 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### LEU
- Composite: **0.00**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=22.7%   inst_own=71%   recom=1.71
- **Decision: no bet.** Composite 0.00 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

### BWXT
- Composite: **0.00**   RED_FLAGs: 0   SEVERE: 0   → Truth_signal: no
- Discovery_advantage: **LOW**   short_float=3.2%   inst_own=94%   recom=1.94
- **Decision: no bet.** Composite 0.00 < 0.6 and no RED_FLAG — framework didn't find divergence at the level that justifies a forward position.

## What this is NOT

- **Not a fraud accusation.** RED_FLAG_NEGATIVE means the filing claim diverges from independent registry evidence at the cutoff. It does not mean the company is lying. Multiple legitimate reasons exist for registry absence (early-stage programs, ADAMS coverage gap, private counterparties, foreign jurisdictions) and are noted per-claim where they apply.
- **Not a trade recommendation.** Nuclear pure-plays can take years to resolve milestones; short timing is hard. See `feedback_truth_vs_alpha.md` — Truth_signal ≠ Tradable_alpha.
- **Not pre-registered.** Recommend committing this report's hash to git for honest forward-bet bookkeeping.

## Debt and tradeoffs

- **NNE and ASPI scored in-process, not via isolated subagent.** The cohort runner stalled mid-scoring on 2026-05-16; the parent agent completed the scoring inline because the harness could not spawn isolated worktree-mode subagents from the non-git parent directory. Blinding discipline was preserved by (a) not reading hindsight / outcome files, (b) only reading OKLO.scores.json as a format reference (not for content cross-pollination), (c) applying the same rubric mechanically per ticker. Re-running these two through a proper isolated subagent (after fixing the worktree-creation path) is a fair next step.
- **Catalog gap — NRC ADAMS connector is the #1 blocker** for nuclear-vertical scoring quality. Several NNE / OKLO claims are UNVERIFIABLE in the current catalog despite being highly verifiable in principle.
- **Counterparty-silence threshold for hyperscaler PPAs needs calibration.** OKLO's Meta prepayment scored MODE (zero Meta mentions); a future hyperscaler 10-K disclosure window of 6-9 months may be the right validation cadence.
- **Process rules surfaced by subagents** are captured per ticker in the `process_rules_discovered` field of each `.scores.json`. Worth promoting to memory per `feedback_subagent_rule_capture.md`.
