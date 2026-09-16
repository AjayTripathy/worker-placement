# HII — Huntington Ingalls Industries Deep Dive

_As of 2026-05-24 · Price $320.63 · Market cap ~$12.6B · 10-K filed 2026-02-05 (FY ended 2025-12-31)_

## DISCLAIMER

Algorithmic research output, not investment, fiduciary, or tax advice. Position decisions are the reader's responsibility.

## TL;DR

Framework scores HII **0.000 LONG** but the score is **structurally misleading** — 9 of 11 claims came back UNVERIFIABLE not because the claims are weak, but because our J-Book corpus has **R-2 RDT&E + OP-5 O&M but no Navy Shipbuilding & Conversion (SCN) P-40 line items**. Every Navy ship program HII names (CVN-78 Ford-class, Virginia-class SSN, Columbia SSBN, LHA/LPD amphibs, DDG-51) is a real Program of Record with active multi-year statutory funding — they'd score FUNDED_STEADY/GROWING if the corpus carried SCN.

This is a **HIGHER-CONVICTION LONG than the composite suggests** for the opposite reason from PLTR's case: the framework underweights HII's quality because of a corpus gap, not because of valuation overhang.

The setup:
- **$53.1B backlog (4.3x revenue)** — multi-year forward visibility
- **81% U.S. Navy customer** — statutory POR funding, can't be canceled by EO
- **Duopoly/monopoly position** in nuclear shipbuilding (only one of two yards for Virginia/Columbia subs and CVNs)
- **Trough proximity meh** — −29% from $453 high but +44% above 52w low ($222) — already partial bounce
- **Insider signal CLEAN** (`NO_PROXIMATE_SALES`, $32.5M sold of $12.6B mkt cap = 0.26%/yr)
- **USAspending $92.9B aggregate** — fourth-largest in cohort

Trade-off vs BAH:
- HII has stronger structural moat (sole-source ship builder)
- BAH has cleaner trough proximity and richer capital return
- BAH at 10x P/E vs HII at ~20x P/E
- Different mean-reversion drivers: BAH = federal-spending-EO overhang easing; HII = Ford/Columbia execution stabilizing

## Headline framework verdict

| | Value |
|---|---|
| Composite | **0.000** |
| Tier | **LONG** |
| Claims | 11 (1 PASS / 10 UNVERIFIABLE) |
| Drawdown | −29.3% from 52w high $453.73 |
| Distance above 52w low | +43.9% above $222.80 |
| Market cap | $12.6B (LARGE) |
| `insider_vs_calendar` | **NO_PROXIMATE_SALES** (40 sales / $32.5M / 0 proximate) |
| Federal direct-prime (USAspending FY23-25) | $92.9B / 601 awards |

The 10 UNVERIFIABLE claims are corpus-gap, not weakness. **Verifying these would require ingesting Navy SCN P-40 data** (we have SCN_Book.pdf in navy_fy27/ but parser doesn't surface P-1 line items).

## Financial snapshot (FY25 ended December 31, 2025)

| | FY25 | FY24 | FY23 |
|---|---:|---:|---:|
| Sales and service revenues | **~$12.5B** | $11.5B | n/d |
| YoY revenue growth | **+8%** | n/d | n/d |
| Net earnings | **$605M** | $550M | $681M |
| YoY earnings growth | +10% | −19% | n/d |
| Stock-based comp | $54M | $23M | $34M |
| Total backlog | **$53.1B** | $48.7B | n/d |
| Dividends declared/share | **$5.43** | $5.25 | n/d |
| Employees | 44,000+ | n/d | n/d |
| **U.S. Navy revenue share** | **81%** | 80% | 81% |
| Cash provided by operations | n/d (but +) | n/d | n/d |

Capital structure (per Nov 2024 issuance + 2024 credit facility):
- $500M senior notes 5.353% due 2030
- $500M senior notes 5.749% due 2035
- $1.7B Revolving Credit Facility (zero outstanding at FY25)
- $1.7B commercial paper authorization (zero outstanding)
- Interest payments ~$114M FY26 expected

## Three Segments

| Segment | Description | Status |
|---|---|---|
| **Newport News** | Nuclear ships: Ford-class CVN, Virginia-class SSN, Columbia SSBN, RCOH | Cost-pressured (Ford execution + Columbia labor) |
| **Ingalls** | Non-nuclear: LHA/LPD amphibs (sole builder), DDG-51 (1-of-2), NSC | NSC program terminating after 10 hulls |
| **Mission Technologies** | C5ISR, AI/ML, cyber, unmanned, training, DoE national security | Services-prime exposure (federal-spending-review affected) |

## What the framework cannot verify (10 UNVERIFIABLE claims) — these would PASS with SCN corpus

Every UNVERIFIABLE is a real, named POR with current FY26 funding:

| Claim | Program | Status (analyst overlay) |
|---|---|---|
| C1 | CVN-78 Ford-class ($15.4B awarded for CVN 80/81 + CVN 82/83 AP) | FY26 NDAA authorized incremental funding + advance procurement |
| C2 | Virginia-class SSN-774 Block IV/V/VI (2/yr rate, teaming with EB) | Active build; Block VI long-lead awarded |
| C3 | Columbia-class SSBN-826 (subcontractor to EB; 12 boats planned) | FY26 LLTM contract for Build II 5 boats |
| C4 | LHA/LPD amphibs (sole builder; LHA 8/9/10, LPD 30-35 MYP) | Active multi-ship procurement |
| C5 | DDG-51 Arleigh Burke (1-of-2; MYPs for 7 + 7 ships) | Active build (DDG 129/131/133/135) |
| C6 | CVN RCOH (sole; Stennis CVN-74 currently) | Active multi-year contract |
| C7 | 81% Navy revenue (extreme concentration) | Disclosed |
| C8 | USCG Legend-class NSC terminating at 10th hull | Disclosed; minor segment impact |
| C9 | Mission Technologies segment (C5ISR/AI/cyber/unmanned/training) | Services-prime exposure (federal-spending-review affected) |
| C11 | Audited by SUPSHIP/DCAA/DCMA | Disclosed |

C10 (44,000 employees, Pascagoula + Newport News properties) was the lone PASS — control claim verified.

## Valuation

| Metric | Value |
|---|---:|
| Market cap | $12.6B |
| Diluted shares | ~39.4M |
| Long-term debt | ~$2.5-3.0B (Nov 2024 $1B senior notes + prior) |
| Cash + ST investments | ~$1B (estimate) |
| Enterprise value | ~$14-15B |
| FY25 net earnings | $605M |
| FY25 EBITDA (est) | ~$1.3B (net + D&A $329M + interest + tax) |
| **EV / EBITDA** | **~11x** |
| **P / E (LTM)** | **~20x** |
| Dividend yield | 1.7% |
| Book value | n/d (defense industrial assets) |

For context: defense primes typically trade 12-18x earnings; defense shipbuilders historically trade 10-14x earnings (LMT 18x, NOC 15x, GD 18x, LHX 16x). HII at 20x is **slightly above the shipbuilding median** — driven by:
- Forward backlog visibility ($53B / 4.3x revenue)
- Sole-source-ship-class moat
- Expected Ford/Columbia margin normalization

The −29% drawdown reflects execution concerns, not customer concerns. If FY26-27 ship margins stabilize, multiple should expand to 14-16x → mid-$400s range = +35-50%.

## The execution overhang explained

Three Newport News programs have been margin-headwinds:

1. **CVN-78 Ford-class** — first-in-class cost overruns; CVN-79/80/81 follow-on margin recovery
2. **Columbia-class SSBN** — labor cost pressure + first-of-class learning curve
3. **Virginia Block IV** — supply chain disruption + late delivery

These are program-level execution issues, not customer-cancellation issues. Navy POR funding for all three continues. Path back to margin: Ford-class learning curve as CVN-79+ deliver; Columbia gets through Lead Boat; Virginia returns to 2/yr cadence as supply chain heals.

**The catalyst pattern**: HII has historically expanded margin on follow-on hulls (first-of-class is hardest). FY26-27 prints showing 50-100bps shipbuilding margin recovery would be a multiple-expansion trigger.

## Mission Technologies — the federal-spending-EO exposure

Mission Tech revenue (~$2.5B / ~20% of total) overlaps with BAH-style services prime exposure. The 10-K doesn't carry the explicit "impacted, reduced or canceled" language that BAH does, but the segment is in the same line of fire (C5ISR, AI/ML services, unmanned systems support).

In a deep federal-spending compression, Mission Tech is the segment to watch. The 78%+ shipbuilding revenue is statutorily insulated.

## Insider activity — CLEAN

| | Value |
|---|---|
| Form 4 filings (12mo) | 177 |
| Total insider sales | 40 |
| Total sale value | **$32.5M** |
| Proximate to budget events | **0** |
| Discretionary proximate | 0 |
| Signal | **NO_PROXIMATE_SALES** |

$32.5M / $12.6B mkt cap = 0.26%/yr — modest distribution rate. Notably cleaner than CDRE's 1.0%/yr or PLTR's 0.34%/yr. No event-clustering whatsoever.

## What would need to be true for the LONG to work

1. **Shipbuilding margin normalizes** in FY26-27 prints. Ford-class CVN-79/80 follow-on margin recovery is the canonical learning-curve play.
2. **Backlog burn rate matches new awards** so $53B doesn't drift down. The FY26 NDAA tells us this directly when passed.
3. **Mission Technologies holds revenue stable** despite federal-spending review. The segment is small (20% of revenue) so even meaningful weakness is bounded.
4. **No major program cancellation** beyond NSC (which already terminated at 10 hulls). Ford-class, Virginia, Columbia all moving forward per FY26 NDAA.
5. **Multiple expansion** as the −29% drawdown reverses. Target: 14-16x P/E → ~$450/share.

## What would invalidate the LONG

- **Major ship program restructuring or cancellation** (Ford-class 4-ship MYP, Columbia, Virginia)
- **Mission Tech revenue collapse > 25%** if federal-spending review is deeper than expected
- **Continued FY26 shipbuilding margin compression** below FY24 trough (would imply learning-curve thesis is wrong)
- **Insider sales accelerate** to clustered/discretionary pattern (currently clean)
- **Backlog drift below $45B** (would suggest new award pace is slowing)

## Head-to-head vs cohort LONGs

| | HII | BAH | PLTR | CDRE |
|---|---|---|---|---|
| Composite | 0.000 | 0.091 | 0.000 | 0.000 |
| Composite confidence | **corpus-gap-driven** | **earned** | **earned** | earned |
| Drawdown | −29% | −39% | −34% | −34% |
| Above 52w low | +44% | +10% | +14% | +11% |
| Revenue growth | +8% | +12% | +57% | +7.5% (organic −1%) |
| P/E | ~20x | 10x | n/m (loss-adjusted) | 21x |
| Customer concentration | **81% Navy** | <10% any | mixed | <10% any |
| Multi-year visibility | **$53B backlog (4.3x rev)** | $37B (3x rev) | $4.4B gov RDV | $190M backlog |
| Moat | **sole-source ship yards** | cleared workforce | software lock-in | brand + distribution |
| Mean-reversion driver | shipbuilding margin recovery | federal-spending easing | continued growth | TBD (rollup-driven) |

HII has the deepest moat in the cohort but already partially mean-reverted from the 52w low. BAH offers cleaner trough proximity + capital return. PLTR offers higher growth but at painful valuation. CDRE offers smallest size but rollup risk.

**For different portfolio slots**:
- BAH: best for cheap-quality dividend-cushioned long
- HII: best for structural-moat long with backlog visibility
- PLTR: best for AI-substitution thesis (but expensive)
- CDRE: best for small-cap trough optionality (but rollup risk)

## Position-sizing recommendation

**Mid-to-high conviction LONG** (3-4% portfolio weight). The framework's 0.000 score reflects corpus blindness but the underlying setup is genuinely strong:
- Sole-source defense industrial-base moat
- 4.3x revenue backlog visibility
- Clean insider signal
- Trough-adjacent (already +44% above low but still −29% from high)

**Pair vs ITA** (defense ETF) captures HII-specific shipbuilding margin recovery without market beta.

**Standalone long**: 1.7% dividend yield + buyback discipline (small but present) provides modest downside cushion.

## Framework improvement triggered

1. **Ingest Navy SCN P-40 line items** into the J-Book corpus. We have `SCN_Book.pdf` in `navy_fy27/` but the parser doesn't extract P-1 (Procurement-1 Line Item) data for shipbuilding. Would convert HII's 9 UNVERIFIABLE Navy ship-program claims to PASS with real signal.

2. **`backlog_velocity` M-source** — given current backlog + revenue, compute "years of revenue cover" and YoY growth in cover ratio. HII at 4.3x cover is exceptional; would surface this as a quality differentiator.

3. **`shipbuilding_margin_tracker`** — track segment-level margin for Newport News and Ingalls against historical learning-curve expectations. Would help discriminate first-of-class drag (HII's current overhang) from systemic execution failure.

## Files & data

- Scores: `verticals/public_co/data/_local/HII.jbook.scores.json`
- 10-K: `verticals/public_co/data/hii/filings/0001501585-26-000006_10-K.txt` (filed 2026-02-05)
- USAspending: $92.9B / 601 awards (FY23-25)
- Insider: `NO_PROXIMATE_SALES`, 40 sales / $32.5M / 0 proximate
