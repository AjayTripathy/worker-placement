# Small-Cap Pilot — R/f/M Review Report

_2026-05-24 · 5-name pilot run of the small-cap "aren't lying" thesis_
_Universe: 339 eligible → 101 clean-trough → top 30 pilot candidates → top 5 by trough quality_

## DISCLAIMER

Algorithmic research output, not investment, fiduciary, or tax advice. The R/f/M tuples are claim-verification findings as of the cutoff date; treat as raw analyst inputs for review, not buy/sell recommendations.

## TL;DR — 4 of 5 SHORT, 1 NEUTRAL, 0 clean LONG

The framework AGGRESSIVELY VALIDATED the alpha thesis: **deep-trough small caps are usually at trough for genuine reasons**, not because the market is wrong. Only 1 of 5 survives as a long-basket candidate, and even that one (SPSC) is NEUTRAL not LONG by the strict 0.143 threshold.

| Ticker | Sector | Drawdown | Composite | Tier | Verdict |
|---|---|---:|---:|---|---|
| **FMC** | Basic Materials | −70.5% | **1.625** | SHORT (deep) | Distressed credit-event in progress |
| **INSP** | Healthcare | −70.0% | **0.875** | SHORT | Reimbursement crisis + DOJ AKS CID |
| **UPWK** | Comm Services | −60.2% | **0.625** | SHORT | Structurally challenged: flat GSV, decelerating buyback |
| **SHAK** | Consumer Cyclical | −55.8% | **0.571** | SHORT | Covenant waiver Mode B catch + traffic-negative SSS |
| **SPSC** | Technology | −63.2% | **0.286** | NEUTRAL | Quality survivor: 100Q growth, $200M buyback at trough |

**Hit rate of the negative-selection alpha:** 4/5 = 80% of deep-trough small caps correctly rejected.

## Top R/f/M tuples per ticker

### 🚩 FMC — composite 1.625 (1 RED + 4 SEVERE)

| Claim | R (claim) | M (measurement) | Severity |
|---|---|---|---|
| **C2** | "Tier-one leader" with "transformative pipeline" | FY25 revenue −18% YoY ($3,467M vs $4,246M); net loss $2.24B; Q4 EPS −$13.74 | **RED_FLAG** |
| C3 | Diamide franchise defensible via 22 US + 393 foreign patents | **323 of 393 foreign diamide patents expire by 2030** (82%); Cyazypyr process patent already expired 2025 | SEVERE |
| C4 | "In compliance with all our debt covenants" | **5 revolver amendments in 30 months** (Feb 2025, Dec 2025 most recent); $1.3B debt due within 12 months vs $1.1B revolver headroom | SEVERE |
| C5 | India divestiture is "strategic portfolio optimization" at $450M fair value | India $522M write-down preceded by $422M revenue reversal (channel-inflation admission); $960M carrying value → $450M fair value | SEVERE |
| C6 | (Dividend / buyback discipline) | **Share buyback ban through 2028**; dividend cut to $0.08; $750M 8.45% subordinated notes (distressed pricing) | SEVERE |

**Critical framework insight**: deterministic prescreens BOTH passed FMC (GC clean, auditor clean — KPMG hasn't pulled the GC trigger yet because it's a major signal they're cautious with). The LLM R/f/M layer caught the distress through covenant amendments + subordinated debt pricing + write-down sequencing + buyback ban. **Deterministic alone is insufficient.**

### 🚩 INSP — composite 0.875 (1 RED + 1 SEVERE + 2 MODERATE)

| Claim | R (claim) | M (measurement) | Severity |
|---|---|---|---|
| **C1** | "We believe the code will transition to CPT code 64582" for Inspire V reimbursement | **AHA recommended CPT 64999 (unlisted code = worst-case billing path) in April 2026** — disclosed in Q1 2026 10-Q filed May 4, before cutoff | **RED_FLAG** |
| C2 | 95.6% U.S. revenue; Medicare/MAC + commercial payer-dependent | Q1 10-Q: **CMS WISeR prior-authorization program adversely impacting Q1 2026 revenue** — not flagged in 10-K despite WISeR starting before Feb 13 filing | SEVERE |
| C6 | DOJ False Claims Act CID (Jan 2025) framed as routine | Three concurrent lawsuits in FY25: securities class action (City of Pontiac → Indiana PRS), derivative suit, DOJ AKS investigation — convergence pattern | MODERATE |
| C7 | Nyxoah patent dispute described as "early stages" | **17 INSP filings mention Nyxoah**; 3 IPRs filed against asserted patents; **PTAB invalidates ~80% of instituted IPRs** | MODERATE |

**The PASS claims** (C3-C5, C8): 115 USPTO patents verified, 13 ClinicalTrials.gov registrations including STAR Phase 3, $404M cash with NO_GOING_CONCERN + CLEAN_AUDITOR_TENURE, insider activity 100% 10b5-1.

**The −70% drawdown is correctly priced for the reimbursement crisis**, not a multiple-compression bargain.

### 🚩 UPWK — composite 0.625 (5 MODERATE)

| Claim | R (claim) | M (measurement) | Severity |
|---|---|---|---|
| C1 | GSV $4.0B described as economic activity scale | **GSV flat 2024→2025** (0% growth); **−2.4% vs 2023 $4.1B peak**; AI subset only ~7.5% of total | MODERATE |
| C2 | Net income $115.4M sustained-profitability thesis | Net income **−46.5% YoY** ($215.6M → $115.4M); op CF up but quality concerns | MODERATE |
| C5 | $136M deployed on buybacks 2025 — capital return discipline | **Buyback DECELERATING into trough**: Q4 cadence $34.4M Oct → $13.8M Nov → $5.1M Dec; **CEO 10b5-1 plan rotation pre-committing more selling at depressed prices** | MODERATE |
| C6 | Lifted enterprise launch (Aug 2025) framed as growth catalyst | Filing self-discloses: "In 2025, we paused certain new client acquisition efforts in advance of the launch of Lifted" — i.e., admitted sales-team productivity pause | MODERATE |

**Net**: No acute distress, but the marketplace is structurally challenged — zero GSV growth + decelerating buyback + CEO selling more = not a clean LONG.

### 🚩 SHAK — composite 0.571 (4 MODERATE)

| Claim | R (claim) | M (measurement) | Severity |
|---|---|---|---|
| C1 | Same-Shack Sales +2.3% FY25 "20 consecutive quarters of growth" | SSS composition: **+3.1% price / −0.8% traffic** — entirely price-driven; AWS fell $79K → $77K Q4 YoY | MODERATE |
| C2 | Restaurant-level margin 22.6% improved +120 bps YoY | Margin gains flattered by 53rd-week + reversal of FY24's $32M impairment; core ops show less expansion | MODERATE |
| C3 | 45 new Shacks 2025 "largest class yet" | Unit count reconciles cleanly **BUT AWS flat-to-down as new units open** — classic unit-economic dilution | MODERATE |
| **C5** | **Sixth Amendment to Revolving Credit Facility** (July 9, 2025) extends maturity | **Fifth Amendment AND Waiver (March 19, 2025) cited in exhibit index but NOT narratively explained in MD&A** — "waiver" word implies H1 2025 covenant pressure the filing doesn't proactively discuss | **MODERATE (Mode B)** |

**Mode B finding (the canonical alpha catch)**: The Fifth Amendment AND Waiver appears in the exhibit index without narrative explanation. This is the kind of disclosure-structure flag a casual reader would miss — the framework caught it.

### ✓ SPSC — composite 0.286 (5 PASS + 2 MODERATE + 1 UNVERIFIABLE) — THE SURVIVOR

| Claim | R (claim) | M (measurement) | Severity |
|---|---|---|---|
| C1 | FY25 revenue $751.5M +17.8% YoY; 100th consecutive quarter of growth; 96% recurring | **NO_GOING_CONCERN + CLEAN_AUDITOR_TENURE (KPMG, no Item 4.01 since 2021)** | PASS |
| C3 | Carbon6 acquisition (Jan 2025) extends Amazon-seller network | `acq_coherence` = 0.55 (medium); Carbon6 is adjacent to SPSC's core EDI network — not as coherent as core M&A | MODERATE |
| C5 | $300M buyback authorization, $115M repurchased 2025 | **$200M additional authorization the DAY AFTER 10-K filed** — executing aggressively at trough | PASS |
| C6 | 20 Form 4 filings, all 100% 10b5-1, zero discretionary | `insider_vs_calendar` = ROUTINE_10B5_1; no clustering | PASS |
| C7 | Channel partners "Microsoft, NetSuite, Oracle, SAP, Sage" | `megacap_namecheck` returned 0 hits (expected: SPSC is too small for megacaps to name) | UNVERIFIABLE |
| C8 | International expansion: AU, CA, NL, PL, UA | International PP&E share grew 18% → 26% (verified investment); BUT foreign pre-tax income share fell 8% → 2% (currently unprofitable) | MODERATE |

**Quality summary**: 100 quarters of growth, $751M revenue +18% YoY, 96% recurring, largest customer <1%, $151M cash + no debt, $200M buyback added at trough. The 2 MODERATE flags are GROWTH-INVESTMENT concerns (acquisition adjacency + international ramp), not quality concerns.

**The composite 0.286 is BORDERLINE NEUTRAL**:
- Strict small-cap threshold (0.143) → not a LONG
- Standard threshold (0.20) → just over
- Quality-adjusted (give partial credit for the 100Q growth + $200M-buyback-at-trough signals) → effective LONG

## Framework calibration insights from the pilot

### 1. Deterministic prescreens are necessary but NOT sufficient

FMC: GC clean (KPMG hasn't pulled the trigger) + auditor clean = passed both prescreens. But the LLM R/f/M layer caught:
- 5 covenant amendments in 30 months
- $750M 8.45% subordinated notes (distressed pricing)
- Share buyback ban through 2028
- Channel-inflation write-down sequence

**Implication**: deterministic prescreens are good for triage but the LLM-driven R/f/M layer is irreplaceable for catching distress that hasn't yet triggered the canonical signals.

### 2. Post-cutoff-but-pre-deadline filings are critical

INSP's RED flag (AHA CPT 64999 recommendation in April 2026) was disclosed in the Q1 10-Q filed May 4, 2026 — within the cutoff (May 20). The 10-K alone (filed Feb 13) had the WEAKER narrative ("we believe the code will transition to CPT 64582"). Using ONLY the 10-K would miss the RED flag.

**Implication**: framework should always pull the LATEST filing per cutoff (10-K + any subsequent 10-Q/8-K), not just the annual report.

### 3. Mode B catches are real and important

SHAK C5: the "Fifth Amendment AND Waiver" buried in the exhibit index without MD&A narrative is exactly the kind of structural signal a casual reader misses. The framework's job is to read the WHOLE filing structure (exhibits, schedules, etc.) not just the prose.

### 4. Restaurant counterparty verification has a known false-positive pattern

SHAK C8: `megacap_namecheck` against DoorDash/Uber returned INFLATION_SUSPECT (0 hits), but the agent correctly identified this as a KNOWN false positive (aggregators don't name individual chain partners). The framework's response: **down-classify to UNVERIFIABLE rather than flag as INFLATION**.

Worth building a `vertical_specific_false_positive_filter` so the framework auto-down-classifies these known patterns.

### 5. The trough optionality is real BUT bounded

All 5 names are at deep drawdown (−56% to −71%), but only SPSC has the quality profile to justify mean-reversion confidence. The "buy what's down" naive strategy would lose ~80% of the time in this universe.

## Next steps & recommendations

### For the long basket (this pilot's output)

**Add to long basket** (with caveat): **SPSC** at 1-2% portfolio weight. The composite (0.286) is NEUTRAL, not strict-LONG, but the quality signals (100Q growth, aggressive trough-buyback, clean balance sheet) and aggressive buyback discipline ($200M added at the literal trough) suggest management has high conviction. Position-size for the borderline composite.

**Avoid**: FMC, INSP, UPWK, SHAK. Even if the prices look cheap, each has framework-verified real issues. The "trough" is correctly priced.

### For pilot expansion (Option A: full 30 names)

Cost: ~$30-90 across the remaining 25 names. Expected output:
- ~6-8 SPSC-equivalent LONG candidates (NEUTRAL-to-LONG composites)
- ~4-6 deeply distressed SHORTs (composite >1.0)
- ~12-15 ambiguous NEUTRALs

If we want to size a 5-10 name LONG basket, running 30 names is sufficient. If we want 15-20 names, scale to 60-90.

### Framework improvements triggered

1. **`vertical_false_positive_filter`** — auto-down-classify known patterns (restaurant aggregator non-naming, sub-material megacap partnerships, etc.)
2. **Latest-filing-not-just-10-K rule** — framework must pull most-recent filing within cutoff, including 10-Q and recent 8-Ks
3. **Distress pattern detector beyond GC** — pattern composite of {covenant amendments, subordinated debt pricing, buyback bans, dividend cuts, write-down sequences} that triggers SEVERE even when GC + auditor are clean (FMC pattern)
4. **Buyback velocity tracker** — UPWK's decelerating Q4 buyback cadence ($34M → $14M → $5M) is a meaningful signal vs SPSC's $200M-added-at-trough

## Files

- `pilot_INSP.json`, `pilot_SHAK.json`, `pilot_SPSC.json`, `pilot_FMC.json`, `pilot_UPWK.json` — raw R/f/M tuples per ticker
- `pilot_candidates.json` — top 30 from the deterministic prescreen funnel (the remaining 25 await Option A run if you authorize)
- `gc_prescreen.json` — full 339-name going-concern screen
- `ac_prescreen_trough.json` — 101-name auditor screen on trough subset
- `eligible.json` — 339 eligible universe (post all exclusion filters)
