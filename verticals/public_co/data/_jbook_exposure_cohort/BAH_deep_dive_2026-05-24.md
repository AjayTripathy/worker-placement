# BAH — Booz Allen Hamilton Deep Dive

_As of 2026-05-24 · Price $78.68 · Market cap ~$9.4B · 10-K filed 2025-05-23 (FY ended 2025-03-31)_

## DISCLAIMER

Algorithmic research output, not investment, fiduciary, or tax advice. The author is **not** a fiduciary or licensed advisor. Framework composite scores measure *claim verifiability* against M-sources at a point in time; they are not buy/sell recommendations. Position decisions are the reader's responsibility.

## TL;DR

Framework scores BAH **composite 0.091 LONG** at trough (+10% above 52w low, −39% from 52w high). Unlike CDRE, BAH is a **higher-conviction asymmetric long** because:

- **Genuinely cheap**: 10x P/E, 8.9x EV/EBITDA, 2.8% forward dividend yield
- **High-quality growth**: revenue +12% YoY, net income +54% YoY
- **Organic, not acquisition-driven** (the trap CDRE has)
- **Aggressive capital return**: $764M FY25 buyback (+$408M YoY); $745M still authorized; +5% dividend increase to $0.55/qtr
- **Cleared workforce moat**: 25,776 cleared employees (72% of headcount) — high barriers
- **Insider activity is clean**: 18 sales / $10.57M / `ROUTINE_10B5_1` (not distress)

The **−39% drawdown is real-news-driven**: the new administration's spending-review Executive Orders have already led to BAH contracts being "**impacted, reduced or canceled**" (filing language, not hypothetical). That's the one MODERATE in the composite (BAH-11) — legitimate, not a framework miss.

Net: BAH is a quality compounder with a real but partially-priced-in federal-spending overhang. The framework score (0.091) overstates the cleanliness slightly but understates the conviction. I'd put BAH ahead of CDRE on quality-of-setup at similar drawdown.

## Headline framework verdict

| | Value |
|---|---|
| Composite | **0.091** |
| Tier | **LONG** (≤ 0.20 threshold) |
| Claims | 12 (10 PASS / 1 MODERATE / 0 SEVERE / 0 RED / 1 UNVERIFIABLE) |
| Drawdown | −39.1% from 52w high $129.13 |
| Distance above 52w low | +9.9% above $71.59 |
| Market cap | $9.4B (MID) |
| `insider_vs_calendar` signal | **ROUTINE_10B5_1** (clean) |

## Financial snapshot (FY25 ended March 31, 2025)

| | FY25 | FY24 | YoY | FY23 |
|---|---:|---:|---:|---:|
| Revenue | $11,980M | $10,659M | **+12.4%** | $9,259M |
| Net income | $935M | $606M | **+54%** | $272M |
| Operating cash flow | $1,009M | $259M | timing | $603M |
| Total debt | $3,998M | $3,412M | +17% | $2,812M |
| Cash | $885M | $554M | +60% | $405M |
| Backlog | $37.0B | $32.2B | **+15%** | $29.4B |
| Share repurchases | $764M | $373M | **+$408M** | n/d |
| Dividends paid | $254M | $240M | +6% | n/d |
| Headcount | 35,800 | 33,000 | +8% | n/d |
| **Cleared %** | **72%** | 69% | n/d | n/d |

## Segment mix (FY25)

| Segment | Revenue | % | YoY |
|---|---:|---:|---:|
| **Defense** | $5,900M | **49%** | up from 47% (FY24) |
| **Civil** | $4,200M | **35%** | (homeland/health/justice/labor/etc.) |
| **Intelligence** | $1,900M | **16%** | up from $1,800M (1% point of mix down) |
| Total | $11,980M | 100% | |

**No single customer >10% of revenue.** Federal direct-prime visible in USAspending: **$16.65B aggregate awards FY23-25 across 2,729 awards** with top 5 at $1B+ each (GSA-administered + VA T4NG/PTEMS).

## What the framework caught (10 PASS claims via the new M-sources)

| Claim | M-source that fired |
|---|---|
| BAH-01 Defense customer mix ($5.9B, 49%) | usaspending + pentagon_jbook |
| **BAH-02 Intel customer mix ($1.9B, 16% / 18 IC orgs)** | **`ic_contracting_proxy`** (cleared-FTE benchmark consistent) |
| BAH-03 Civil customer mix ($4.2B, 35%) | usaspending |
| **BAH-04 85% from 2,596 IDIQ TOs** | **`revenue_concentration`** (operationally diversified) |
| **BAH-05 Top vehicle = 18% of revenue** | **`revenue_concentration`** (50th peer percentile) |
| **BAH-06 Largest TO = 4% of revenue** | **`revenue_concentration`** (50th peer percentile) |
| BAH-07 35,800 employees / 72% cleared | usaspending + Human Capital cross-check |
| BAH-08 Backlog $37B (+15%) | self-disclosure + revenue_concentration peer norms |
| **BAH-09 Cyber mission customer mix (NSA, DIA)** | **`cybercom_budget`** ($1.96B FY26 envelope FUNDED_STEADY) |
| BAH-10 2025 Appropriations Act / CR timing | macro budget context |

The four NEW M-sources fired on five claims (BAH-02, 04, 05, 06, 09), converting them from UNVERIFIABLE / MODERATE in the prior run to PASS with real signal.

## The one MODERATE (BAH-11) — the federal-spending-review overhang

**Direct quote from BAH's 10-K, Item 1A Risk Factors:**

> "Following the change in U.S. presidential administration in 2025, the U.S. government has paused or initiated review of certain forms of federal government spending across federal civilian, defense, and intelligence departments and agencies, **we have had, and may in the future have, certain of our contracts impacted, reduced or canceled** as a result of these reviews."

This is **not a hypothetical risk** — it's a current-event disclosure. The MODERATE_UNDERDELIVERY flag is methodologically correct. The market knows this and is pricing the stock at −39% drawdown accordingly.

The question is whether the disclosed impact is the FULL impact or the LEADING EDGE of a larger overhang. Two scenarios:

| Scenario | Outcome | Probability (judgment) |
|---|---|---|
| **Disclosed impact = full impact** | Stock has overcorrected; LONG works | ~50% |
| **Disclosed impact = leading edge** | More contract cancellations coming; stock drifts | ~30% |
| **Acceleration** (deeper cuts) | Stock breaks 52w low | ~20% |

## The one UNVERIFIABLE (BAH-12) — DCAA reserve

**$245M cumulative reserve for DCAA-disputed executive comp going back to FY 2011**. 14+ years of unaudited claimed-cost adjustments are still subject to resolution.

**Interesting wrinkle**: in FY25, BAH **released $122M of the reserve INTO revenue** (a positive adjustment based on management's revised estimate). That release accounts for **$122M of the +$1,321M YoY revenue increase** — i.e., ~9% of the headline +12% revenue growth was DCAA reserve release, not new bookings.

This isn't fraud — DCAA reserves are legitimately estimated and adjusted under GAAP. But it's a recurring **revenue-quality issue**: the reserve will continue to move +/- as audits resolve. The market may be discounting this.

UNVERIFIABLE is correct — no M-source covers contract-audit reserves. Worth building one (`dcaa_reserve_tracker`).

## What the framework MISSED — the quiet capital-return story

The framework's verdict is on claim verifiability. It doesn't fold in capital-return discipline, which for BAH is exceptional:

**FY25 capital return**:
- Buybacks: $764M (5.6M shares × ~$136 avg)
- Dividends: $254M (~$2.08/share)
- Total: **$1,018M return = ~101% of operating cash flow** (CFO was $1,009M)

**Buyback authorization remaining: $745M** (increased to $3,585M cumulative on Jan 28, 2025, just before the FY ended). At $78.68, $745M buys 9.5M shares = ~7.5% of current float.

**Dividend trajectory**: $2.20/year forward ($0.55/qtr, announced May 23, 2025) vs $2.08 paid FY25 (+5.8% increase) — **dividend hike at the drawdown**, signaling management confidence.

Net at $78.68: **2.8% dividend yield + ongoing buyback = ~10% total capital return run-rate** to current shareholders. That's a real floor for a quality compounder.

## Valuation context

| Metric | Value | vs Peer (SAIC/CACI/LDOS) |
|---|---:|---|
| Price | $78.68 | — |
| Diluted shares | ~120M | — |
| Market cap | ~$9.4B | mid-tier (SAIC $4.3B, CACI $11.1B, LDOS $15.9B) |
| Total debt | $4.0B | — |
| Cash | $885M | — |
| Enterprise value | ~$12.5B | — |
| FY25 net income | $935M | — |
| **P/E (LTM)** | **~10.1x** | cheap (SAIC 11x, CACI 15x, LDOS 12x) |
| **EV / EBITDA** | **~8.9x** | cheap (peers 11-14x) |
| Forward yield | 2.8% | high (SAIC 1.4%, CACI 0.5%, LDOS 1.0%) |

**BAH trades at a meaningful discount to direct peers**, with arguably the strongest organic growth (+12% revenue, +54% net income vs peers in the +6-9% revenue range).

## Insider activity — clean

`insider_vs_calendar` cohort signal: **ROUTINE_10B5_1**

| | Value |
|---|---|
| Form 4 filings (12mo) | 43 |
| Total insider sales | 18 |
| Total sale value | $10.57M (~0.1% of mkt cap) |
| Discretionary proximate sales | **0** |
| Proximate sale value | $20K (1 sale, noise) |

**No distress signal**. 18 sales / $10.57M over 12 months on a $9.4B mid-cap is well within the routine 10b5-1 baseline for a public services firm. Notably **zero clustering around budget actions** — this is the IONQ-pattern detector and BAH is clean.

## What would need to be true for the LONG to work

1. **Federal spending review impact stabilizes** rather than accelerates. BAH already disclosed contract-by-contract impact in the 10-K; need Q2/Q3 FY26 prints to NOT show further deterioration in funded-backlog burn.

2. **Buyback continues to absorb supply**. $745M remaining authorization buys 9.5M shares at current price — that's ~7.5% of float. At any meaningful pace this is a real bid under the stock.

3. **DCAA reserve doesn't reverse**. Material risk if the $245M reserve needs to be increased rather than released. FY25 saw a $122M release; future years could go either way.

4. **Defense segment growth continues**. Defense at 49% of revenue grew from $5.1B → $5.9B (+15.7%) in FY25. If FY26 prints flat-to-down on defense, the bull case weakens.

5. **No P/E re-rating below 8x.** Currently 10.1x. A break below $63/share would put it at 8x — would need to evaluate whether the macro overhang has worsened or this is forced selling.

## What would invalidate the LONG

- **Disclosed contract cancellation acceleration** in Q1 or Q2 FY26 prints. If "impacted, reduced or canceled" line grows materially in size or counts, the spending-review overhang is bigger than priced.
- **DCAA reserve increase** (the opposite of FY25's release) — would simultaneously hit revenue AND increase the contingent liability.
- **Buyback pace decelerates** to <$100M/quarter without commensurate dividend hike — would signal management capital-return discipline is breaking.
- **Insider sales accelerate** to clustered/discretionary pattern. Currently `ROUTINE_10B5_1`; transition to `CLUSTERED_DISCRETIONARY` would be a structural red flag.
- **Defense growth decelerates** below 5% YoY.

## BAH vs CDRE — head-to-head

| | BAH | CDRE |
|---|---|---|
| Composite | 0.091 LONG | 0.000 LONG |
| Size | MID $9.4B | SMALL $1.3B |
| Drawdown | −39% | −34% |
| Above 52w low | +10% | +11% |
| Revenue growth | **+12% (organic-led)** | +7.5% (acquisition-led; organic ~−1%) |
| Net income growth | **+54%** | +22% |
| Net leverage | ~2.2x | **~3.4-3.7x pro-forma post-TYR** |
| Covenant headroom | comfortable | **tight (3.5x step-down now in effect)** |
| Capital return / CFO | **~100%** | ~30% |
| Buyback runway | $745M auth | None active |
| Dividend yield | 2.8% | 1.3% |
| P/E (LTM) | **10x** | 21x |
| Insider signal | clean | clean |
| Acquisition-rollup risk | low | **high** |

**Net assessment**: BAH is the higher-conviction trade. Same trough optionality (both −34-39% with limited downside to 52w low), but BAH has cleaner growth quality, lower leverage, higher capital return, lower valuation, and no rollup dependence.

## Position-sizing recommendation

**Mid-conviction asymmetric long** (3-5% portfolio weight, materially larger than CDRE at 1-2%). The combination of:
- Trough proximity (+10% above 52w low)
- Cheap on earnings (10x) and EV/EBITDA (8.9x)
- High capital return (~10% combined buyback + dividend run-rate)
- Clean insider activity (`ROUTINE_10B5_1`)
- Strong organic growth (+12% / +54% EPS)
- Diversified, federal-customer base
- Cleared-workforce moat (25,776 cleared FTE)

...creates an asymmetric setup with bounded downside (52w low only −10% below current) and material upside if federal-spending-review impact stabilizes.

The MODERATE flag on federal-spending review is legitimate but partially priced. Position-size around the conviction-level, not the framework-purity composite.

## Pair candidates

- **Long BAH / short BAH-peer-with-worse-signal**: SAIC isn't in our scored set. KBR rescored to 0.400 NEUTRAL (off SHORT), so the BAH/KBR pair is less directional than before.
- **Long BAH / short ITA (defense ETF)**: cleanest β-neutral expression. Captures BAH's specific multiple-compression-reversion without market beta.
- **Standalone long**: most expressive of the thesis. Buyback + dividend yield provide downside cushion.

## Framework improvement notes triggered by this deep dive

1. **`dcaa_reserve_tracker`** — given a company's disclosed claimed-cost reserve history, flag year-over-year movement >5% of net income as material revenue-quality signal. Would have caught BAH's $122M FY25 release.

2. **`capital_return_velocity`** — given operating CF, buyback, and dividend, compute return-to-CFO ratio. >80% with shrinking share count is a quality signal; >100% with rising debt is a yellow flag.

3. **`administration_change_impact`** — given disclosed contract-cancellation language, classify severity tier (NONE / DISCLOSED_BOUNDED / DISCLOSED_OPEN_ENDED). BAH-11 would score DISCLOSED_OPEN_ENDED.

## Files & data

- Scores: `verticals/public_co/data/_local/BAH.jbook.scores.json`
- Input: `verticals/public_co/data/_local/BAH.jbook.input.json`
- 10-K: `verticals/public_co/data/bah/filings/0001443646-25-000076_10-K.txt` (filed 2025-05-23)
- USAspending: $16.65B aggregate awards / 2,729 awards FY23-25
- Insider activity: 18 sales / $10.57M / `ROUTINE_10B5_1` (clean)
