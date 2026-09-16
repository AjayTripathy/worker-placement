# CACI — CACI International Deep Dive

_As of 2026-05-24 · Price $501.35 · Market cap ~$11.1B · 10-K filed 2025-08-07 (FY ended 2025-06-30)_

## DISCLAIMER

Algorithmic research output, not investment, fiduciary, or tax advice. Position decisions are the reader's responsibility.

## TL;DR — DO NOT LONG

Framework scores CACI **0.125 LONG** (composite-tier) but **the framework missed a major signal**: `insider_vs_calendar` returns **`CLUSTERED_DISCRETIONARY`** — the canonical IONQ-pattern detector firing on **9 of 10 proximate insider sales being DISCRETIONARY (not 10b5-1)**, two unique insiders, clustered within 7 days of the **FY27 J-Book release on April 28, 2026**.

Specifically:
- **Marshall D. Akins** sold 8 times on 2026-05-05 totaling **$5.2M** at $437-444/share — 7 days after FY27 J-Book published
- **Hart Anastasios John** sold $318K on 2026-05-04 — 6 days after J-Book published
- Both insiders' sales coded as discretionary (Form 4 code S, not 10b5-1)

The framework's 0.125 LONG composite reflects LLM scoring of disclosed claims. The cohort-level insider signal **didn't flow into the composite** because the planner didn't query `insider_vs_calendar` while scoring specific claims. **This is the bigger framework gap than CDRE's organic-decline or PLTR's valuation: a `CLUSTERED_DISCRETIONARY` signal should outweigh a clean composite.**

**My recommendation: NEUTRAL at best, possibly SHORT pending understanding of WHY two insiders distributed discretionarily right after J-Book.** Not a LONG candidate.

## Headline framework verdict — with the critical override

| | Value |
|---|---|
| Framework composite | 0.125 (LONG tier) |
| **Insider signal** | **`CLUSTERED_DISCRETIONARY`** ⚠ |
| Adjusted view | **NEUTRAL-to-SHORT** (insider override) |
| Claims | 11 (8 PASS / 1 MODERATE / 0 SEVERE / 0 RED / 2 UNVERIFIABLE) |
| Drawdown | −24.3% from 52w high $662.19 |
| Distance above 52w low | +20.4% above $416.26 |
| Market cap | $11.1B (LARGE) |
| Federal direct-prime (USAspending FY23-25) | $14.1B / 1,830 awards |

## The insider activity in detail

`insider_vs_calendar` query (cik=0000017843, 365-day lookback, 14-day window):

| Metric | Value |
|---|---|
| Form 4 filings | 46 |
| Total insider sales | 56 |
| Total sale value | **$76.5M** (~0.7% of mkt cap, 12mo) |
| Proximate to budget events | 10 |
| Proximate value | $5.65M |
| **Discretionary proximate** | **9 of 10** |
| Unique discretionary owners | 3 |
| Signal | **`CLUSTERED_DISCRETIONARY`** |

The single largest matched-event cluster:

> **April 28, 2026: FY27 J-Book Release**
> "DoD published FY27 RDT&E and Procurement J-Books. Confirmed Tranche 3 Transport Layer unfunded for second year; SDA dissolution implied..."
> **Within +7 days**: 9 discretionary sales, 2 unique owners (AKINS MARSHALL D, HART ANASTASIOS JOHN), $5.53M total.

**Marshall D. Akins** (President since 2022, Chief Operating Officer prior) executed 8 discretionary sales on 2026-05-05 totaling $5.21M:

| Date | Shares | Price | Value |
|---|---:|---:|---:|
| 2026-05-05 | 3,434 | $443.37 | $1,522,533 |
| 2026-05-05 | 2,947 | $442.15 | $1,303,016 |
| 2026-05-05 | 1,953 | $441.18 | $861,625 |
| 2026-05-05 | 999 | $438.87 | $438,431 |
| 2026-05-05 | 850 | $439.86 | $373,881 |
| 2026-05-05 | 837 | $437.86 | $366,489 |
| 2026-05-05 | 560 | $436.37 | $244,367 |
| 2026-05-05 | 235 | $443.78 | $104,288 |
| **Total** | **10,815** | | **$5.214M** |

This is the EXACT IONQ-pattern the framework was designed to detect:
- Discretionary (not pre-planned 10b5-1)
- Clustered around a budget action
- Multiple insiders involved
- Within 1 week of a J-Book that confirmed unfunded status for SDA-adjacent programs

What I don't know without further investigation: **what specifically in the FY27 J-Book negatively affects CACI** that the disclosure-readable 10-K (filed 2025-08-07, well before FY27 J-Book) doesn't disclose. The pattern alone is sufficient to merit caution.

## Financial snapshot (FY25 ended June 30, 2025)

| | FY25 | FY24 | YoY |
|---|---:|---:|---:|
| Revenue (estimate from top-10 = 46.4% / $4.0B) | **~$8.55B** | ~$7.66B | +12% |
| Organic growth | **+7.2%** | n/d | n/d |
| Net income | **$499.8M** | $419.9M | **+19%** |
| Total backlog | **$31.4B** | $31.6B | **−0.6%** |
| Funded backlog | $4.2B | n/d | n/d |
| Cash + equivalents | $106M | n/d | n/d |
| **Total debt (est)** | **~$1.35B** | ~$300M | **+$1.05B** |

**Customer concentration**: 95.7% federal / 75.4% DoD — the most concentrated services prime in the cohort.

**Top 10 contracts = 46.4% of revenue / $4.0B** — significant individual-contract risk. Loss of any single major contract is material.

## Capital structure — heavy acquisition-financed leverage

| Component | Value | Notes |
|---|---:|---|
| Revolving Facility | $1,975M auth | $124.5M outstanding |
| Term Loan A | $1,225M outstanding | secured |
| 2033 Senior Notes | ~$1,000M (estimate) | new issue FY25 |
| **Total debt** | **~$1.35B (est)** | up from ~$300M FY24 |

CACI issued **$1.5B in new debt during FY25** to finance acquisitions ("Seven acquisitions in three fiscal years including Azure Summit RF/EMS/photonics"). Net debt jumped from <1x EBITDA to ~1.4x EBITDA in one year.

**No dividend** — explicitly stated: "do not intend to pay any cash dividends at this time."

**Buyback**: $750M ASR (Accelerated Share Repurchase) signed Jan 2023 with Citibank. Capital return is mostly buyback-only.

## What the framework caught

| Claim | Verdict | Notes |
|---|---|---|
| C1 75.4% DoD / 95.7% federal | PASS | Verified |
| C2 Top 10 contracts = 46.4% / $4.0B | PASS | Concentration disclosed |
| C3 Spectrum Superiority / EW / photonics | UNVERIFIABLE | Azure Summit acquisition adjacency |
| C4 C3I / SDR SIGINT + EW | PASS | Forward narrative |
| C5 Space domain awareness | PASS | Forward narrative |
| **C6 Full-spectrum cyber (offensive + defensive)** | **MODERATE** | New `cybercom_budget` would route here |
| C7 Enterprise IT for ~50 federal agencies | PASS | Verified |
| C8 7 acquisitions in 3 FYs incl Azure Summit | PASS | Rollup disclosed |
| C9 Mission/Engineering Support | UNVERIFIABLE | Generic |
| C10 Patents IP (control) | PASS | Verified |
| C11 ~25,000 employees | UNVERIFIABLE | Control claim |

C6 was the only MODERATE. With `cybercom_budget` query (FY26 envelope $1.96B FUNDED_STEADY), this could have moved to PASS — pushing composite to 0.000. But that **would have made the framework MORE wrong** in this case, because the insider signal is the real story.

## Valuation

| Metric | Value |
|---|---:|
| Market cap | $11.1B |
| Diluted shares | ~22.1M |
| Total debt | ~$1.35B |
| Cash | $106M |
| Enterprise value | ~$12.3B |
| FY25 revenue (est) | $8.55B |
| EV / Revenue | 1.4x |
| FY25 net income | $499.8M |
| **P / E (LTM)** | **~22x** |
| Estimated FY25 EBITDA | ~$1.0B |
| **EV / EBITDA** | **~12x** |
| Dividend yield | **0%** (no dividend) |
| Backlog growth | **−0.6%** |

CACI trades at peer-median P/E (22x) for IT services primes (LDOS 12x, SAIC 11x — CACI is the most expensive). The 19% net income growth justifies *some* premium, but the combination of:
1. Insider-distress signal
2. Declining backlog (-0.6%)
3. No dividend cushion
4. Rising leverage from rollup
5. Heavy single-contract concentration (top 10 = 46% of revenue)

...makes the 22x multiple unsustainable if any one of these weakens.

## What the framework would have flagged with proper M-source routing

Three signals that should have been in scope but weren't run during scoring:

1. **`insider_vs_calendar`** — would have surfaced `CLUSTERED_DISCRETIONARY` as a cohort-level signal. Currently the LLM scorer only queries this when a specific claim mentions insider activity (rare).

2. **`backlog_velocity`** (proposed M-source) — would flag the −0.6% backlog decline as a forward-revenue concern.

3. **`acq_coherence`** — would assess whether 7 acquisitions in 3 years across RF/EMS/photonics/cyber/SDA is COHERENT_ROLLUP or INCOHERENT. CACI's deals are mostly within stated verticals (suggests COHERENT) but the pace is escalating.

The current framework runs only what the planner picks per claim. Cohort-level signals like insider activity need to be **mandatory** for every score run, not opt-in.

## Head-to-head vs cohort LONGs

| | CACI | BAH | HII |
|---|---|---|---|
| Composite | 0.125 | 0.091 | 0.000 |
| **Insider signal** | **`CLUSTERED_DISCRETIONARY` ⚠** | clean | clean |
| Drawdown | −24% | −39% | −29% |
| P/E | ~22x | 10x | ~20x |
| Backlog growth | **−0.6%** | +15% | +9% |
| Customer concentration | 95.7% federal | <10% any | 81% Navy |
| Single-contract concentration | top 10 = 46% | top 10 = ~18% | n/d |
| Dividend yield | 0% | 2.8% | 1.7% |
| Acquisition rollup risk | high | low | low |
| Leverage trajectory | rising | rising | flat |
| **Net verdict** | **AVOID** | LONG | LONG |

**CACI is the worst-positioned of the framework-LONG-tier names.** Despite the composite verdict, the insider signal combined with declining backlog + rising leverage + no dividend cushion makes this a setup to avoid, not enter.

## What would change the recommendation

For me to re-engage as a LONG candidate:

1. **Insider distribution stops** — no further discretionary sales for 90+ days after the FY27 J-Book release
2. **Backlog returns to growth** in FY26 prints
3. **Buyback accelerates** to signal management views shares as undervalued
4. **DoD spending review impact disclosed** explicitly — if CACI hasn't been affected materially, that's the signal that the FY27 J-Book insider sales were idiosyncratic not informational

If any of these reverse, the bull case (rising margin, strong organic growth +7.2%, $14.1B aggregate awards, Azure Summit/photonics differentiation) remains intact.

## Framework improvement triggered

1. **`insider_vs_calendar` MANDATORY**: every cohort scoring run should automatically include this query and incorporate the signal into the composite. Currently opt-in via planner — this is the main framework gap CACI surfaced.

2. **`backlog_velocity` M-source**: track backlog growth as forward-revenue indicator. CACI's −0.6% backlog while revenue grew 12% means **revenue is being recognized faster than new bookings are being added** — book-to-bill below 1.0.

3. **`acquisition_pace_meter`**: 7 deals in 3 FYs is aggressive. Coupled with rising leverage, this is the kind of pattern the framework should flag as cautionary even if individual deal logic is sound.

4. **Cohort-level signal integration**: when `insider_vs_calendar` returns `CLUSTERED_DISCRETIONARY`, the composite scoring should apply a penalty equivalent to MODERATE_UNDERDELIVERY on a synthetic claim. Right now the signal is invisible to composite.

## Files & data

- Scores: `verticals/public_co/data/_local/CACI.jbook.scores.json`
- 10-K: `verticals/public_co/data/caci/filings/0001628280-25-038739_10-K.txt` (filed 2025-08-07)
- USAspending: $14.1B / 1,830 awards (FY23-25)
- Insider signal: **`CLUSTERED_DISCRETIONARY`** ⚠ — 9 of 10 proximate sales are discretionary, 2 unique owners, $5.53M clustered within 7 days of FY27 J-Book release
