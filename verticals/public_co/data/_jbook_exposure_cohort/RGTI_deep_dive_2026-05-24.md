# RGTI — Rigetti Computing Deep Dive

_As of 2026-05-24 · Price $26.42 · Market cap ~$8.8B · 10-K filed 2026-03-04 (FY ended 2025-12-31)_

## DISCLAIMER

Algorithmic research output, not investment, fiduciary, or tax advice. Position decisions are the reader's responsibility.

## TL;DR — NOT a trough setup (already mean-reverted)

Framework scores RGTI **0.200 LONG** (border — exactly at the LONG threshold). The composite reflects clean disclosure but **RGTI is not actually a trough-asymmetric long**:

- Price $26.42 is **+145% above 52w low $10.79** — the trough already mean-reverted
- −53% from 52w high $56.34 — but at the 52w low it was −81% from the high
- The asymmetric setup was when RGTI was $11; at $26 the multiple is already restored

**Business fundamentals**:
- Net loss $216M FY25 (vs $201M FY24 — losses growing)
- Accumulated deficit $771M
- Revenue tiny (<$15-20M est) — model is pre-commercial government R&D contracts
- $347M ATM raise FY25 — capital structure depends on continuous dilution
- ~$300M cash, ~$200M annual burn = ~18 months runway
- Will need MORE dilution in 12-18 months

**Earmark exposure red flag**: `earmark_detector` returns 2 matched earmarks — one is the IONQ-linked AFRL Quantum Networking line ($51M FY22-24) that is **EARMARK_SUNSET** (sponsors lost power). RGTI shares AFRL quantum-networking exposure; the same defunding mechanism that hit IONQ is structurally present.

**Insider signal CLEAN**: `ROUTINE_10B5_1`, no discretionary proximate sales.

**Net view: NOT a LONG candidate.** The framework's 0.200 LONG is border-tier and reflects judgment-call thresholds, not a clean asymmetric setup. For trough-asymmetry: the price already bounced. For quantum-AI-optionality: only as a tiny tail bet (50-100bps), not a 2-5% position.

## Headline framework verdict

| | Value |
|---|---|
| Composite | **0.200** (border — at LONG threshold) |
| Tier | LONG (technically) |
| Claims | 9 (4 PASS / 1 MODERATE / 0 SEVERE / 0 RED / 4 UNVERIFIABLE) |
| Drawdown | −53.1% from 52w high $56.34 |
| **Distance above 52w low** | **+144.9% above $10.79** ← KEY |
| Market cap | $8.8B (MID) |
| `insider_vs_calendar` | **`ROUTINE_10B5_1`** (clean) |
| `earmark_detector` | 2 matched earmarks (1 EARMARK_SUNSET) |

The +145% above 52w low is the killer. The asymmetric trade was made; the price has reverted; further upside requires actual commercial inflection, not multiple expansion.

## Financial reality

| | FY25 | FY24 |
|---|---:|---:|
| Net loss | **$(216.2)M** | $(201.0)M |
| Loss growth | +7.6% (losses growing) | n/d |
| Accumulated deficit | $(771.0)M | n/d |
| Cash + ST investments | ~$300M (est) | n/d |
| **ATM program proceeds FY25** | **$346.7M (30.3M shares)** | n/d |
| Quanta private placement | $35.0M (3.0M shares) | n/d |
| Warrant exercises | $50.0M | n/d |
| Total financing FY25 | **$439.1M** | n/d |
| **Revenue** | **<$20M (est)** | similar |

**Burn rate**: ~$200M/year. Cash runway ~18 months. The 10-K's "sufficient for at least the next twelve months" language is the standard going-concern caveat that resets each fiscal year.

**Dilution**: 30.3M shares from ATM + 3.0M from Quanta + ~5M from warrants = **~38M shares issued FY25** out of ~330M total. ~12% annual dilution. At current price, another $200M raise = another 7.6M shares (~2.3% more dilution).

## Revenue model — pre-commercial government R&D

From the 10-K MD&A:
> "Currently, we generate the majority of our revenues from technology development contracts with various partners. We believe our longer-term business model will be more weighted towards QPU sales and recurring revenues generated from quantum computing systems made accessible via the cloud..."

This is the canonical pre-commercial pattern: revenue comes from government R&D grants (DARPA, AFRL, DOE/Fermilab, NASA, Innovate UK), not paying enterprise customers. Path to commercialization:
- $8.4M India C-DAC purchase order — small but **first real commercial system sale** (delivery 2H 2026)
- AWS, Standard Chartered, Moody's listed as "customers" but distribution is via Amazon Braket / Azure Quantum (i.e., pay-per-shot, low recurring revenue)
- Quanta investment: at least $250M over 5 years in field of quantum computing

## What the framework caught

| Claim | Verdict | Notes |
|---|---|---|
| C1 AFRL Quantum Networking R&D relationship | PASS | Verified via filings BUT see earmark below |
| C2 DARPA/NASA multi-year partnerships | UNVERIFIABLE | Real but PE-specific not in corpus |
| C3 DOE/Fermilab/SQMS Center | PASS | Real, ongoing DOE program |
| **C4 "Substantial majority of revenue from technology development contracts"** | **MODERATE** | Correctly flagged — pre-commercial |
| C5 Rigetti UK / Innovate UK | UNVERIFIABLE | International program |
| C6 India C-DAC $8.4M PO | UNVERIFIABLE | Real but small |
| C7 AWS/Standard Chartered/Moody's customers | UNVERIFIABLE | Distribution channels, not paying customers |
| C8 121 patents issued + 160 pending | PASS | Verified |
| C9 Fab-1 Fremont CA facility | PASS | Verified |

The MODERATE on C4 is the key signal — RGTI's revenue model is structurally R&D-grant-dependent, which puts them in the same fragility class as IONQ.

## The earmark overlap with IONQ — the hidden structural risk

`earmark_detector` returns 2 matched earmarks. The first:

| Field | Value |
|---|---|
| earmark_id | `ionq-afrl-quantum-fy22-fy24` |
| program_name | AFRL Quantum Networking (IONQ) |
| Agency | AFRL |
| Sponsoring lawmakers | Cardin (MD), Van Hollen (MD), Hoyer (MD), Tester (MT) |
| FY22 | $13M (Pentagon requested $0) |
| FY23 | $26M (Pentagon requested $0) |
| FY24 | $12M (Pentagon requested $0) |
| FY25 | $0 (sponsors lost power) |
| Signal | **EARMARK_SUNSET** |

This is the canonical IONQ short-thesis case: the entire $51M FY22-24 line was a **congressional add by Maryland senators**, never requested by Pentagon. After Nov 2024 election, the sponsors lost majority power. FY25 was zeroed.

**Does RGTI receive money from this earmark?** The earmark is labeled "AFRL Quantum Networking (IONQ)" — IONQ is the named recipient. But RGTI's 10-K explicitly states "Rigetti has a contracted relationship with AFRL for quantum networking hardware R&D / superconducting quantum networking" (C1). If RGTI's AFRL revenue comes from the same congressional-add line, RGTI faces the same defunding mechanism.

**This is a structural risk the framework partially caught (C4 MODERATE for R&D-grant revenue dependence) but the specific earmark linkage isn't explicit in the score**. The deep dive question to investigate further: **what portion of RGTI's FY25 revenue came from AFRL quantum networking-coded lines, and is that revenue at risk in FY26?**

## Insider activity — clean

`insider_vs_calendar` query:

| Metric | Value |
|---|---|
| Form 4 filings | 33 |
| Total insider sales | 33 |
| Total sale value | $39.9M |
| Proximate to budget events | 2 |
| Proximate value | $436K |
| Discretionary proximate | **0** |
| Signal | **`ROUTINE_10B5_1`** |

$39.9M / $8.8B mkt cap = 0.45%/yr — modest distribution rate. Zero clustered-discretionary pattern. Unlike CACI/TDG, no insider warning signal here.

## Valuation — astronomical multiples

| Metric | Value |
|---|---:|
| Market cap | $8.8B |
| Diluted shares | ~330M |
| Cash | ~$300M |
| Total debt | $0 |
| Enterprise value | ~$8.5B |
| FY25 revenue (est) | <$20M |
| **EV / Revenue** | **>400x** |
| FY25 net loss | $(216M) |
| **EV / negative earnings** | n/m |
| Cash runway | ~18 months |

For context: pre-commercial deep-tech companies often trade 30-50x revenue at peak hype, 5-15x at moderate optimism, 1-3x at distress. RGTI at 400x+ EV/Revenue is **in the peak-hype band** — not the trough.

The previous 52w low at $10.79 implied a ~$3.4B market cap or EV ~$3.1B, which would be ~155x EV/Revenue. Even at the 52w low, RGTI was expensive. At $26.42, the multiple is fully re-rated.

## Head-to-head vs cohort LONGs

| | RGTI | BAH | HII | CDRE | TDG | CACI |
|---|---|---|---|---|---|---|
| Composite | 0.200 | 0.091 | 0.000 | 0.000 | 0.125 | 0.125 |
| Drawdown | −53% | −39% | −29% | −34% | −25% | −24% |
| **Above 52w low** | **+145%** | +10% | +44% | +11% | +7% | +20% |
| Trough proximity | **already reverted** | tight | partial | tight | tight | mid |
| Revenue model | pre-commercial | mature | mature | mature | mature | mature |
| Net income | **$(216M) loss** | $935M | $605M | $44M | $2,074M | $500M |
| EV / Revenue | **>400x** | 1.0x | 1.2x | 2.7x | 11x | 1.4x |
| Cash runway | 18mo | indefinite | indefinite | indefinite | indefinite | indefinite |
| Capital structure | **dilutive ATM** | buyback | buyback | dividend | leveraged | leveraged |
| Insider signal | clean | clean | clean | clean | **⚠⚠** | **⚠** |
| **Verdict** | **PASS (no longer trough)** | **LONG** | **LONG** | **LONG (small)** | **AVOID** | **AVOID** |

RGTI's edge: quantum-AI optionality + clean insider signal.
RGTI's drawbacks: trough already mean-reverted + pre-commercial + dilution-financed + earmark-funding risk.

## What would change the recommendation

For RGTI to become an asymmetric LONG candidate:

1. **Price retraces to $15 or below** — putting it back near 52w-low trough proximity
2. **Earmark concern resolves** — explicit AFRL contract continuation in FY26 enacted budget, OR clean confirmation that RGTI's AFRL revenue is from non-earmark merit-based lines
3. **Commercial revenue materializes** — beyond the $8.4M India PO, additional 8-9 figure commercial system sales
4. **Quantum advantage milestone** — if RGTI achieves a publishable quantum-advantage demonstration on a commercial problem, multiple could re-rate higher

If any of those happen, re-engage. At $26 with +145% bounce already in the price, the asymmetric setup is broken.

## What would make RGTI a SHORT

- AFRL Quantum Networking confirmed defunded in FY26 enacted budget
- Cash runway falls below 12 months without raise
- ATM completed at lower share prices (forced dilution at trough)
- Quantum-advantage milestone missed in 2026

None of these are imminent risks per the 10-K, but the structural fragility (pre-commercial + R&D-grant-dependent + earmark-overlap) means the bear thesis is live.

## Position-sizing recommendation

**PASS** for trough-asymmetric trade. **Tiny tail position (0.5-1%)** acceptable for those who want quantum-computing optionality, but not as a portfolio-meaningful long.

For asymmetric trough exposure, **the trade has already been made** between $11 and $26. Waiting for a pullback to $15 or below would restore the asymmetric setup.

## Framework improvement triggered

1. **`trough_proximity_required_for_long`**: when distance-above-52w-low exceeds, say, 50%, downgrade LONG-tier composite to NEUTRAL automatically. RGTI's +145% above low while composite says LONG is exactly the case that should auto-flag.

2. **`earmark_program_overlap`**: cross-reference cohort members' named programs against `earmark_detector`'s corpus. RGTI's AFRL Quantum Networking claim should auto-link to the IONQ earmark and flag the funding-source-fragility.

3. **`going_concern_runway_tracker`**: pre-commercial companies with <24 months cash runway and ongoing ATM dilution should have a structural composite penalty applied. RGTI fits this profile.

4. **`commercial_revenue_inflection_milestone`**: companies whose revenue model is "we plan to commercialize" should be flagged distinctly from companies generating commercial revenue. RGTI vs HII is the contrast — both pre-revenue can be valid trades but for VERY different reasons.

## Files & data

- Scores: `verticals/public_co/data/_local/RGTI.jbook.scores.json`
- 10-K: `verticals/public_co/data/rgti/filings/0001104659-26-023454_10-K.txt` (filed 2026-03-04)
- Insider signal: `ROUTINE_10B5_1` (clean) — 33 sales / $39.9M / 0 discretionary
- Earmark exposure: AFRL Quantum Networking (IONQ-linked, EARMARK_SUNSET, sponsors gone)
