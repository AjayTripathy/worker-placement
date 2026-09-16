# Signal OS — Cross-Cohort Paired Long/Short Trade Sheet

_Generated 2026-05-17T22:14:11.303343Z — cutoff varies per cohort_

**Construction:** for every name the v2 forward-bet emitter would EMIT
(composite >= 0.6 AND discovery_advantage_tier in {HIGH, MED}),
the cleanest in-cohort long candidate is paired against it. Long candidates
are picked in priority order: notes-marked **CONTROL** > lowest-composite
in-cohort name > an external sector-beta long as a fallback.

**Hedge ratio default is dollar-neutral 1:1.** The framework's job is to
surface the pair, not to optimize the hedge. Adjust for beta differential,
borrow cost, liquidity, and your own market view.

**Falsification window is 12 months** from each cohort's cutoff date.
A pair survives if EITHER leg moves >50% against the thesis, OR neither
leg moves materially and the divergence claim is corroborated post-cutoff.

## Pairs

### Defense-tech

#### SHORT **AIRO** / LONG **KTOS**
- **Short leg:** AIRO (AIRO Group Holdings, Inc.)
  - Composite: 0.75   PASS=3 MOD=0 SEVE=0 RED=1 UNV=4
  - Discovery_advantage: MED (short_float=10.7%, inst_own=29%, recom=1.67)
  - Filing analyzed: `0001493152-26-014116_10-K.txt`
- **Long leg (in-cohort):** KTOS (Kratos Defense & Security Solutions, Inc.)
  - Composite: 0.00  (in-cohort control)
  - Discovery_advantage: LOW (short_float=5.6%, inst_own=91%)
- **Pair thesis:** short the Defense-tech name where R - f(M) divergence is high AND the bear case isn't already crowded; long the Defense-tech name where the framework finds no divergence (sector-beta hedge).
- **Hedge ratio:** dollar-neutral 1:1 default; adjust for beta, borrow cost, and liquidity.
- **Falsification:** within 12 months, the short leg either materially restates the flagged claims, files distress paperwork, or trades >50% lower; OR the divergence claim is corroborated by counterparty disclosure and the pair returns ~0.

### Lidar / ADAS

#### SHORT **AEVA** / LONG **INVZ**
- **Short leg:** AEVA (Aeva Technologies, Inc.)
  - Composite: 0.75   PASS=1 MOD=3 SEVE=0 RED=0 UNV=1
  - Discovery_advantage: MED (short_float=18.9%, inst_own=60%, recom=1.4)
  - Filing analyzed: `0001193125-26-116518_10-K.txt`
- **Long leg (in-cohort):** INVZ (Innoviz Technologies Ltd.)
  - Composite: 0.14  (in-cohort cleanest follow)
  - Discovery_advantage: MED (short_float=10.0%, inst_own=25%)
- **Pair thesis:** short the Lidar / ADAS name where R - f(M) divergence is high AND the bear case isn't already crowded; long the Lidar / ADAS name where the framework finds no divergence (sector-beta hedge).
- **Hedge ratio:** dollar-neutral 1:1 default; adjust for beta, borrow cost, and liquidity.
- **Falsification:** within 12 months, the short leg either materially restates the flagged claims, files distress paperwork, or trades >50% lower; OR the divergence claim is corroborated by counterparty disclosure and the pair returns ~0.

#### SHORT **OUST** / LONG **INVZ**
- **Short leg:** OUST (Ouster, Inc.)
  - Composite: 0.67   PASS=1 MOD=2 SEVE=0 RED=0 UNV=2
  - Discovery_advantage: HIGH (short_float=8.9%, inst_own=46%, recom=1.43)
  - Filing analyzed: `0001628280-26-013313_10-K.txt`
- **Long leg (in-cohort):** INVZ (Innoviz Technologies Ltd.)
  - Composite: 0.14  (in-cohort cleanest follow)
  - Discovery_advantage: MED (short_float=10.0%, inst_own=25%)
- **Pair thesis:** short the Lidar / ADAS name where R - f(M) divergence is high AND the bear case isn't already crowded; long the Lidar / ADAS name where the framework finds no divergence (sector-beta hedge).
- **Hedge ratio:** dollar-neutral 1:1 default; adjust for beta, borrow cost, and liquidity.
- **Falsification:** within 12 months, the short leg either materially restates the flagged claims, files distress paperwork, or trades >50% lower; OR the divergence claim is corroborated by counterparty disclosure and the pair returns ~0.

### Quantum computing

#### SHORT **ARQQ** / LONG **IONQ**
- **Short leg:** ARQQ (Arqit Quantum Inc.)
  - Composite: 1.50   PASS=1 MOD=4 SEVE=1 RED=2 UNV=0
  - Discovery_advantage: MED (short_float=12.4%, inst_own=26%, recom=1.0)
  - Filing analyzed: `0001104659-25-119500_20-F.txt`
- **Long leg (in-cohort):** IONQ (IonQ, Inc.)
  - Composite: 0.38  (in-cohort cleanest follow)
  - Discovery_advantage: LOW (short_float=23.0%, inst_own=56%)
- **Pair thesis:** short the Quantum computing name where R - f(M) divergence is high AND the bear case isn't already crowded; long the Quantum computing name where the framework finds no divergence (sector-beta hedge).
- **Hedge ratio:** dollar-neutral 1:1 default; adjust for beta, borrow cost, and liquidity.
- **Falsification:** within 12 months, the short leg either materially restates the flagged claims, files distress paperwork, or trades >50% lower; OR the divergence claim is corroborated by counterparty disclosure and the pair returns ~0.

#### SHORT **QBTS** / LONG **IONQ**
- **Short leg:** QBTS (D-Wave Quantum Inc.)
  - Composite: 1.25   PASS=0 MOD=6 SEVE=2 RED=0 UNV=0
  - Discovery_advantage: MED (short_float=14.6%, inst_own=47%, recom=1.27)
  - Filing analyzed: `0001907982-26-000026_10-K.txt`
- **Long leg (in-cohort):** IONQ (IonQ, Inc.)
  - Composite: 0.38  (in-cohort cleanest follow)
  - Discovery_advantage: LOW (short_float=23.0%, inst_own=56%)
- **Pair thesis:** short the Quantum computing name where R - f(M) divergence is high AND the bear case isn't already crowded; long the Quantum computing name where the framework finds no divergence (sector-beta hedge).
- **Hedge ratio:** dollar-neutral 1:1 default; adjust for beta, borrow cost, and liquidity.
- **Falsification:** within 12 months, the short leg either materially restates the flagged claims, files distress paperwork, or trades >50% lower; OR the divergence claim is corroborated by counterparty disclosure and the pair returns ~0.

### Hydrogen / fuel-cell

#### SHORT **BLDP** / LONG **LIN**
- **Short leg:** BLDP (Ballard Power Systems, Inc.)
  - Composite: 1.22   PASS=1 MOD=6 SEVE=1 RED=1 UNV=2
  - Discovery_advantage: HIGH (short_float=7.1%, inst_own=31%, recom=3.0)
  - Filing analyzed: `0001628280-26-017045_40-F.txt (FY2025 40-F shell; substantive content via incorporated exhibits 99.1-99.3 AIF/MD&A/F.S., plus material 6-K press-release titles 2024-2026 in /Users/ajay/exalted/signalos/verticals/public_co/data/bldp/filings/)`
- **Long leg (in-cohort):** LIN (Linde plc)
  - Composite: 0.00  (in-cohort control)
  - Discovery_advantage: LOW (short_float=1.3%, inst_own=86%)
- **Pair thesis:** short the Hydrogen / fuel-cell name where R - f(M) divergence is high AND the bear case isn't already crowded; long the Hydrogen / fuel-cell name where the framework finds no divergence (sector-beta hedge).
- **Hedge ratio:** dollar-neutral 1:1 default; adjust for beta, borrow cost, and liquidity.
- **Falsification:** within 12 months, the short leg either materially restates the flagged claims, files distress paperwork, or trades >50% lower; OR the divergence claim is corroborated by counterparty disclosure and the pair returns ~0.

#### SHORT **FCEL** / LONG **LIN**
- **Short leg:** FCEL (FuelCell Energy, Inc.)
  - Composite: 1.00   PASS=2 MOD=4 SEVE=2 RED=0 UNV=0
  - Discovery_advantage: HIGH (short_float=8.7%, inst_own=47%, recom=3.57)
  - Filing analyzed: `0001104659-25-122302_10-K.htm`
- **Long leg (in-cohort):** LIN (Linde plc)
  - Composite: 0.00  (in-cohort control)
  - Discovery_advantage: LOW (short_float=1.3%, inst_own=86%)
- **Pair thesis:** short the Hydrogen / fuel-cell name where R - f(M) divergence is high AND the bear case isn't already crowded; long the Hydrogen / fuel-cell name where the framework finds no divergence (sector-beta hedge).
- **Hedge ratio:** dollar-neutral 1:1 default; adjust for beta, borrow cost, and liquidity.
- **Falsification:** within 12 months, the short leg either materially restates the flagged claims, files distress paperwork, or trades >50% lower; OR the divergence claim is corroborated by counterparty disclosure and the pair returns ~0.

### AI-DC / crypto-pivot

#### SHORT **IREN** / LONG **EQIX**
- **Short leg:** IREN (Iris Energy Limited)
  - Composite: 1.17   PASS=0 MOD=5 SEVE=1 RED=0 UNV=2
  - Discovery_advantage: MED (short_float=18.0%, inst_own=45%, recom=1.88)
  - Filing analyzed: `0001878848-26-000026_10-Q.txt (FY26 Q3 10-Q, period ending 2026-03-31, filed 2026-05-08); cross-referenced with 0001878848-25-000063_10-K.txt (FY25 10-K, period ending 2025-06-30)`
- **Long leg (in-cohort):** EQIX (Equinix, Inc.)
  - Composite: 0.00  (in-cohort control)
  - Discovery_advantage: LOW (short_float=1.9%, inst_own=99%)
- **Pair thesis:** short the AI-DC / crypto-pivot name where R - f(M) divergence is high AND the bear case isn't already crowded; long the AI-DC / crypto-pivot name where the framework finds no divergence (sector-beta hedge).
- **Hedge ratio:** dollar-neutral 1:1 default; adjust for beta, borrow cost, and liquidity.
- **Falsification:** within 12 months, the short leg either materially restates the flagged claims, files distress paperwork, or trades >50% lower; OR the divergence claim is corroborated by counterparty disclosure and the pair returns ~0.

#### SHORT **CIFR** / LONG **EQIX**
- **Short leg:** CIFR (Cipher Mining Inc.)
  - Composite: 0.83   PASS=1 MOD=5 SEVE=0 RED=0 UNV=0
  - Discovery_advantage: MED (short_float=16.8%, inst_own=63%, recom=1.0)
  - Filing analyzed: `0001819989-26-000009_10-K.txt`
- **Long leg (in-cohort):** EQIX (Equinix, Inc.)
  - Composite: 0.00  (in-cohort control)
  - Discovery_advantage: LOW (short_float=1.9%, inst_own=99%)
- **Pair thesis:** short the AI-DC / crypto-pivot name where R - f(M) divergence is high AND the bear case isn't already crowded; long the AI-DC / crypto-pivot name where the framework finds no divergence (sector-beta hedge).
- **Hedge ratio:** dollar-neutral 1:1 default; adjust for beta, borrow cost, and liquidity.
- **Falsification:** within 12 months, the short leg either materially restates the flagged claims, files distress paperwork, or trades >50% lower; OR the divergence claim is corroborated by counterparty disclosure and the pair returns ~0.

### Solid-state battery

#### SHORT **MVST** / LONG **ALB**
- **Short leg:** MVST (Microvast Holdings, Inc.)
  - Composite: 1.57   PASS=2 MOD=1 SEVE=2 RED=2 UNV=2
  - Discovery_advantage: MED (short_float=10.2%, inst_own=23%, recom=1.0)
  - Filing analyzed: `0001628280-26-018264_10-K.txt`
- **Long leg (in-cohort):** ALB (Albemarle Corp.)
  - Composite: 0.12  (in-cohort control)
  - Discovery_advantage: LOW (short_float=8.8%, inst_own=92%)
- **Pair thesis:** short the Solid-state battery name where R - f(M) divergence is high AND the bear case isn't already crowded; long the Solid-state battery name where the framework finds no divergence (sector-beta hedge).
- **Hedge ratio:** dollar-neutral 1:1 default; adjust for beta, borrow cost, and liquidity.
- **Falsification:** within 12 months, the short leg either materially restates the flagged claims, files distress paperwork, or trades >50% lower; OR the divergence claim is corroborated by counterparty disclosure and the pair returns ~0.

#### SHORT **SES** / LONG **ALB**
- **Short leg:** SES (SES AI Corp.)
  - Composite: 1.50   PASS=0 MOD=4 SEVE=1 RED=1 UNV=1
  - Discovery_advantage: HIGH (short_float=7.2%, inst_own=19%, recom=2.0)
  - Filing analyzed: `0001819142-26-000010_10-K.txt`
- **Long leg (in-cohort):** ALB (Albemarle Corp.)
  - Composite: 0.12  (in-cohort control)
  - Discovery_advantage: LOW (short_float=8.8%, inst_own=92%)
- **Pair thesis:** short the Solid-state battery name where R - f(M) divergence is high AND the bear case isn't already crowded; long the Solid-state battery name where the framework finds no divergence (sector-beta hedge).
- **Hedge ratio:** dollar-neutral 1:1 default; adjust for beta, borrow cost, and liquidity.
- **Falsification:** within 12 months, the short leg either materially restates the flagged claims, files distress paperwork, or trades >50% lower; OR the divergence claim is corroborated by counterparty disclosure and the pair returns ~0.

#### SHORT **SLDP** / LONG **ALB**
- **Short leg:** SLDP (Solid Power, Inc.)
  - Composite: 1.11   PASS=2 MOD=5 SEVE=1 RED=1 UNV=1
  - Discovery_advantage: MED (short_float=11.1%, inst_own=40%, recom=1.0)
  - Filing analyzed: `0001104659-26-019435_10-K.txt`
- **Long leg (in-cohort):** ALB (Albemarle Corp.)
  - Composite: 0.12  (in-cohort control)
  - Discovery_advantage: LOW (short_float=8.8%, inst_own=92%)
- **Pair thesis:** short the Solid-state battery name where R - f(M) divergence is high AND the bear case isn't already crowded; long the Solid-state battery name where the framework finds no divergence (sector-beta hedge).
- **Hedge ratio:** dollar-neutral 1:1 default; adjust for beta, borrow cost, and liquidity.
- **Falsification:** within 12 months, the short leg either materially restates the flagged claims, files distress paperwork, or trades >50% lower; OR the divergence claim is corroborated by counterparty disclosure and the pair returns ~0.

### Robotics / autonomy

#### SHORT **KSCP** / LONG **TER**
- **Short leg:** KSCP (Knightscope, Inc.)
  - Composite: 1.44   PASS=2 MOD=4 SEVE=0 RED=3 UNV=0
  - Discovery_advantage: MED (short_float=18.5%, inst_own=10%, recom=1.0)
  - Filing analyzed: `0001104659-26-036240_10-K.txt`
- **Long leg (in-cohort):** TER (Teradyne, Inc.)
  - Composite: 0.11  (in-cohort control)
  - Discovery_advantage: LOW (short_float=3.5%, inst_own=95%)
- **Pair thesis:** short the Robotics / autonomy name where R - f(M) divergence is high AND the bear case isn't already crowded; long the Robotics / autonomy name where the framework finds no divergence (sector-beta hedge).
- **Hedge ratio:** dollar-neutral 1:1 default; adjust for beta, borrow cost, and liquidity.
- **Falsification:** within 12 months, the short leg either materially restates the flagged claims, files distress paperwork, or trades >50% lower; OR the divergence claim is corroborated by counterparty disclosure and the pair returns ~0.

### Space / satcom

#### SHORT **RDW** / LONG **IRDM**
- **Short leg:** RDW (Redwire Corp.)
  - Composite: 0.71   PASS=3 MOD=3 SEVE=1 RED=0 UNV=1
  - Discovery_advantage: MED (short_float=14.6%, inst_own=47%, recom=1.5)
  - Filing analyzed: `0001819810-26-000029_10-K.txt`
- **Long leg (in-cohort):** IRDM (Iridium Communications Inc.)
  - Composite: 0.12  (in-cohort control)
  - Discovery_advantage: LOW (short_float=5.9%, inst_own=85%)
- **Pair thesis:** short the Space / satcom name where R - f(M) divergence is high AND the bear case isn't already crowded; long the Space / satcom name where the framework finds no divergence (sector-beta hedge).
- **Hedge ratio:** dollar-neutral 1:1 default; adjust for beta, borrow cost, and liquidity.
- **Falsification:** within 12 months, the short leg either materially restates the flagged claims, files distress paperwork, or trades >50% lower; OR the divergence claim is corroborated by counterparty disclosure and the pair returns ~0.

### Fintech lending / BNPL

#### SHORT **AFRM** / LONG **COF**
- **Short leg:** AFRM (Affirm Holdings, Inc.)
  - Composite: 0.67   PASS=1 MOD=2 SEVE=0 RED=0 UNV=5
  - Discovery_advantage: MED (short_float=6.8%, inst_own=75%, recom=1.54)
  - Filing analyzed: `0001820953-25-000080_10-K.txt`
- **Long leg (in-cohort):** COF (Capital One Financial Corporation)
  - Composite: 0.25  (in-cohort control)
  - Discovery_advantage: LOW (short_float=1.3%, inst_own=87%)
- **Pair thesis:** short the Fintech lending / BNPL name where R - f(M) divergence is high AND the bear case isn't already crowded; long the Fintech lending / BNPL name where the framework finds no divergence (sector-beta hedge).
- **Hedge ratio:** dollar-neutral 1:1 default; adjust for beta, borrow cost, and liquidity.
- **Falsification:** within 12 months, the short leg either materially restates the flagged claims, files distress paperwork, or trades >50% lower; OR the divergence claim is corroborated by counterparty disclosure and the pair returns ~0.


---
**15 paired trades emitted** across 12 cohorts.
