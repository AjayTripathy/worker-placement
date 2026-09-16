# J-Book Exposure Cohort — 2024 Backtest

_Generated 2026-05-20T19:14:25.106693Z — backtest cutoff 2024-09-01_

_12 completed, 1 not-run_

## Methodology — backtest mode

Same subagent + same M-source catalog as the 2026-05-20 forward test, with two changes:

1. Cutoff set to 2024-09-01. Each subagent picks the most-recent pre-cutoff filing (typically Feb-Apr 2024 10-Ks for FY 2023 fiscal year).
2. `cutoff_date="2024-09-01"` passed to every pentagon_jbook + doe_budget query. The corpus filters out FY 2025+ funding rows that wouldn't have been knowable in fall 2024.

**Limitation:** the corpus _vintage_ is FY 2026 (programs that exist in our JSON are 2026-era PEs). We cannot replicate PEs that have since been renamed/consolidated. The cutoff filter is best-effort but not historically perfect.

## Backtest composite ranking

| Rank | Ticker | Company | Filing | Claims | JBook hits | PASS | MOD | SEVE | RED | UNV | BT Composite | FW Composite | Δ |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | IONQ | IonQ, Inc. | 0000950170-24-022072_10-K.txt | 9 | 7 | 1 | 3 | 3 | 0 | 2 | 1.29 | 1.33 | -0.05 |
| 2 | ARQQ | Arqit Quantum Inc. | 0001558370-23-019267_20-F.txt | 8 | 5 | 1 | 3 | 1 | 0 | 3 | 1.00 | 1.40 | -0.40 |
| 3 | QBTS | D-Wave Quantum Inc. | 0001907982-24-000049_10-K.txt | 8 | 4 | 3 | 2 | 0 | 1 | 2 | 0.83 | 1.25 | -0.42 |
| 4 | QUBT | Quantum Computing Inc. | 0001213900-24-028799_10-K.txt | 10 | 4 | 3 | 0 | 0 | 1 | 6 | 0.75 | 1.25 | -0.50 |
| 5 | RDW | Redwire Corporation | 0001819810-24-000025_10-K.txt | 10 | 6 | 6 | 1 | 0 | 1 | 2 | 0.50 | 1.10 | -0.60 |
| 6 | BBAI | BigBear.ai Holdings, Inc. | 0001628280-24-011538_10-K.txt | 10 | 5 | 3 | 3 | 0 | 0 | 4 | 0.50 | 1.33 | -0.83 |
| 7 | RCAT | Red Cat Holdings, Inc. | 0001554795-24-000195_10-K.txt | 12 | 4 | 3 | 3 | 0 | 0 | 6 | 0.50 | 1.00 | -0.50 |
| 8 | ASTS | AST SpaceMobile, Inc. | 0000950170-24-039342_10-K.txt | 8 | 5 | 3 | 2 | 0 | 0 | 3 | 0.40 | 0.67 | -0.27 |
| 9 | KTOS | Kratos Defense & Security Solu | 0001069258-24-000007_10-K.txt | 10 | 8 | 5 | 3 | 0 | 0 | 2 | 0.38 | 0.78 | -0.40 |
| 10 | RKLB | Rocket Lab USA, Inc. | 0000950170-24-022160_10-K.txt | 10 | 5 | 5 | 2 | 0 | 0 | 3 | 0.29 | 0.38 | -0.09 |
| 11 | RGTI | Rigetti Computing, Inc. | 0001558370-24-003234_10-K.txt | 10 | 6 | 3 | 1 | 0 | 0 | 6 | 0.25 | 0.33 | -0.08 |
| 12 | PL | Planet Labs PBC | 0001836833-24-000037_10-K.txt | 10 | 3 | 6 | 0 | 0 | 0 | 4 | 0.00 | 0.25 | -0.25 |

_Pending: AIRO_

## Interpretation

**Δ** column = backtest composite − forward composite. Positive Δ means the framework reads MORE severe at 2024 cutoff than at 2026 cutoff (rare, would suggest the program eventually got refunded). Negative Δ means the forward view exposes more divergence than was knowable in fall 2024 (expected for tickers whose programs only got de-funded after the cutoff).

**The interesting cases are the ones where the backtest already showed SEVERE/RED.** Those are framework hits with pre-knowable evidence — what we'd have flagged in fall 2024 with the same pipeline.

## Per-ticker backtest findings

### IONQ — IonQ, Inc.

- **Filing analyzed:** `0000950170-24-022072_10-K.txt`
- **Claims:** 9  (J-Book M-source fired on 7)
- **Severity:** PASS=1, MOD=3, SEVE=3, RED=0, UNV=2
- **Composite (backtest):** 1.29  (forward: 1.33)

#### 🟠 SEVERE_UNDERDELIVERY (pre-knowable at 2024-09-01)
- **C3** — Two significant customers accounted for 58% (FY2023) / 79% (Q2-2024) / 75% (H1-2024) of revenue.
  - Interp: Customer concentration (79% Q2-2024) ramping while the primary J-Book program (AFRL Quantum Networking) is already FUNDED_SHRINKING is the classic divergence pattern. The 'revenue concentration' jumped from 58% FY23 → 79% Q2-24 — i.e., the small customer base is getting MORE concentrated even as the underlying federal program funding is declining. Per heuristic 6 (USAspending cross-check): usaspen

- **C4** — Q2-2024 revenue +106% YoY to $11.4M driven by 'arrangements to build specialized quantum computing hardware'.
  - Interp: The 10-Q attributes ~half its 106% Q2 revenue jump to 'arrangements to build specialized quantum computing hardware'. The single matching DoD vehicle in the pre-cutoff record is exactly the AFRL FA875022C1022 trapped-ion hardware contract — which is on an already-declining FY funding trajectory and is congressionally-earmark-funded (Pentagon never requested it; see C6). This means the headline rev

- **C6** — Future growth depends on selling effectively to government entities and large enterprises.
  - Interp: Even using only cutoff-knowable facts, the structural risk is severe: the program funding the company's primary DoD revenue line is (a) FUNDED_SHRINKING in trajectory (FY24 $12M vs FY23 $26M, a >50% cut), (b) entirely non-requested by Pentagon (purely congressional add), (c) sponsored by a coalition of MD/MT Democrats whose collective approps power had already shrunk between FY23 and FY24 (Hoyer d


### ARQQ — Arqit Quantum Inc.

- **Filing analyzed:** `0001558370-23-019267_20-F.txt`
- **Claims:** 8  (J-Book M-source fired on 5)
- **Severity:** PASS=1, MOD=3, SEVE=1, RED=0, UNV=3
- **Composite (backtest):** 1.00  (forward: 1.40)

#### 🟠 SEVERE_UNDERDELIVERY (pre-knowable at 2024-09-01)
- **C6** — Arqit announced (May 2023) a sale process for its satellite division; $17.6m impairment recorded FY23; $38.7m intangible reclassified as held-for-sale.
  - Interp: The satellite division was the original technology differentiator at SPAC merger (replicated entropy via quantum satellite). Its impairment + held-for-sale reclassification (2 years post-SPAC) is a SEVERE_UNDERDELIVERY against the original thesis. While not strictly a J-Book divergence claim, it indicates the company has materially rebuilt its core product narrative once already pre-cutoff.


### QBTS — D-Wave Quantum Inc.

- **Filing analyzed:** `0001907982-24-000049_10-K.txt`
- **Claims:** 8  (J-Book M-source fired on 4)
- **Severity:** PASS=3, MOD=2, SEVE=0, RED=1, UNV=2
- **Composite (backtest):** 0.83  (forward: 1.25)

#### 🔴 RED_FLAG_NEGATIVE (pre-knowable at 2024-09-01)
- **C5** — D-Wave Government Inc. is the primary federal contracting entity for D-Wave; named in the venture/term loan structure as a co-borrower.
  - M-check: `usaspending.query_federal_presence(name_variants=['D-Wave Government Inc.','D-Wave Government','D-Wave Systems','D-Wave Quantum','D-Wave US Inc.','D-Wave Commercial Inc.'], end_date='2024-09-01')`
  - M-value: signal=INFLATION_SUSPECT; 1 UEI resolved (D-WAVE GOVERNMENT INC.); 0 contracts; $0M contract obligations; 0 grants; $0M grant obligations; no agency activity
  - Interp: This is the strongest finding in the analysis. The federal-contracting-subsidiary framing in the loan agreement and Item 1A risk-factor language implies a federal channel that does not exist in the federal-recipient registry as of cutoff. RED_FLAG_NEGATIVE per Calibration Rule 6 (USAspending shows ZERO obligations under the claimed channel → claim itself was inflated). Caveat: this is a STRUCTURAL


### QUBT — Quantum Computing Inc.

- **Filing analyzed:** `0001213900-24-028799_10-K.txt`
- **Claims:** 10  (J-Book M-source fired on 4)
- **Severity:** PASS=3, MOD=0, SEVE=0, RED=1, UNV=6
- **Composite (backtest):** 0.75  (forward: 1.25)

#### 🔴 RED_FLAG_NEGATIVE (pre-knowable at 2024-09-01)
- **C9** — Going concern doubt as of Dec 31, 2023: $2.06M cash, $19.94M annual burn, $1.44M working-capital deficit, $149.7M accumulated deficit; auditor (BF Borgers CPA PC) issued going-concern paragraph.
  - M-check: `ucc_proxy.query_ucc_exposure (CIK 0001758009, 36-month window pre-cutoff)`
  - M-value: ucc_proxy: MODERATE_LIEN_EXPOSURE — 16 secured-debt term hits in SEC filings within the 36-month window (lien:9, security agreement:4, secured promissory note:2, ucc-1:1), no Item 2.03 8-Ks in window (so no NEW material secured-debt creation events) but the existing Streeterville
  - Interp: This is the load-bearing finding for QUBT at cutoff 2024-09-01. The going-concern paragraph + $2.06M cash + $19.94M annual operating cash burn implies <2 months runway absent the ATM equity-issuance pipe ($25.5M raised in FY2023 via Ascendiant 3% ATM). Auditor is BF Borgers CPA PC — independently sanctionable concern (BF Borgers's PCAOB record is itself a yellow flag, though using post-cutoff know


### RDW — Redwire Corporation

- **Filing analyzed:** `0001819810-24-000025_10-K.txt`
- **Claims:** 10  (J-Book M-source fired on 6)
- **Severity:** PASS=6, MOD=1, SEVE=0, RED=1, UNV=2
- **Composite (backtest):** 0.50  (forward: 1.10)

#### 🔴 RED_FLAG_NEGATIVE (pre-knowable at 2024-09-01)
- **C9** — Material weaknesses in ICFR unremediated through 2024-06-30.
  - M-check: `edgar_fts; insider_vs_calendar`
  - M-value: edgar_fts (own CIK 0001819810, 'material weakness remediation'): 0 hits in the fulltext index (likely indexing gap, not absence — the 10-Q text clearly contains the disclosure). insider_vs_calendar: 27 Form 4 filings, 17 sales total, 0 proximate to budget events — NO_PROXIMATE_SA
  - Interp: Self-disclosed material weakness persisting >2.5 years post-IPO is a structural governance/controls red flag, independent of J-Book pattern. Insider behavior does NOT show opportunistic budget-vote timing (clean). Score RED_FLAG_NEGATIVE on controls quality alone.


### BBAI — BigBear.ai Holdings, Inc.

- **Filing analyzed:** `0001628280-24-011538_10-K.txt`
- **Claims:** 10  (J-Book M-source fired on 5)
- **Severity:** PASS=3, MOD=3, SEVE=0, RED=0, UNV=4
- **Composite (backtest):** 0.50  (forward: 1.33)


### RCAT — Red Cat Holdings, Inc.

- **Filing analyzed:** `0001554795-24-000195_10-K.txt`
- **Claims:** 12  (J-Book M-source fired on 4)
- **Severity:** PASS=3, MOD=3, SEVE=0, RED=0, UNV=6
- **Composite (backtest):** 0.50  (forward: 1.00)


### ASTS — AST SpaceMobile, Inc.

- **Filing analyzed:** `0000950170-24-039342_10-K.txt`
- **Claims:** 8  (J-Book M-source fired on 5)
- **Severity:** PASS=3, MOD=2, SEVE=0, RED=0, UNV=3
- **Composite (backtest):** 0.40  (forward: 0.67)


### KTOS — Kratos Defense & Security Solutions, Inc.

- **Filing analyzed:** `0001069258-24-000007_10-K.txt`
- **Claims:** 10  (J-Book M-source fired on 8)
- **Severity:** PASS=5, MOD=3, SEVE=0, RED=0, UNV=2
- **Composite (backtest):** 0.38  (forward: 0.78)


### RKLB — Rocket Lab USA, Inc.

- **Filing analyzed:** `0000950170-24-022160_10-K.txt`
- **Claims:** 10  (J-Book M-source fired on 5)
- **Severity:** PASS=5, MOD=2, SEVE=0, RED=0, UNV=3
- **Composite (backtest):** 0.29  (forward: 0.38)


### RGTI — Rigetti Computing, Inc.

- **Filing analyzed:** `0001558370-24-003234_10-K.txt`
- **Claims:** 10  (J-Book M-source fired on 6)
- **Severity:** PASS=3, MOD=1, SEVE=0, RED=0, UNV=6
- **Composite (backtest):** 0.25  (forward: 0.33)


### PL — Planet Labs PBC

- **Filing analyzed:** `0001836833-24-000037_10-K.txt`
- **Claims:** 10  (J-Book M-source fired on 3)
- **Severity:** PASS=6, MOD=0, SEVE=0, RED=0, UNV=4
- **Composite (backtest):** 0.00  (forward: 0.25)

