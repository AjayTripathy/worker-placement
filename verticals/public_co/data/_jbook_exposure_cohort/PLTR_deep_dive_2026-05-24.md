# PLTR — Palantir Technologies Deep Dive

_As of 2026-05-24 · Price $136.88 · Market cap ~$314B · 10-K filed 2026-02-17 (FY ended 2025-12-31)_

## DISCLAIMER

Algorithmic research output, not investment, fiduciary, or tax advice. Position decisions are the reader's responsibility.

## TL;DR

Framework scores PLTR **0.000 LONG** at trough (+14% above 52w low, −34% from 52w high). The composite is technically clean but the score is uninformative for a stock whose entire question is **multiple, not narrative**. PLTR's fundamentals are exceptional (revenue +50%, adj margin 50%, government remaining deal value +90% YoY). The drawdown took it from ~100x EV/Sales to ~68x — but **68x is still in the top decile of public-software valuations**. This is a *lower-conviction long than BAH* despite the cleaner composite.

The framework cannot price a stock; it can only adjudicate disclosed claims. All 8 PLTR claims are factually correct or reasonable-to-believe. **The bear case is valuation, not honesty.**

## Headline framework verdict

| | Value |
|---|---|
| Composite | **0.000** |
| Tier | **LONG** |
| Claims | 8 (5 PASS / 0 MODERATE / 0 SEVERE / 0 RED / 3 UNVERIFIABLE) |
| Drawdown | −33.9% from 52w high $207.18 |
| Distance above 52w low | +14.2% above $119.91 |
| Market cap | $314B (MEGA) |
| `insider_vs_calendar` | **ROUTINE_10B5_1** (but $1.06B / 476 sales over 12 months) |

## Financial snapshot (FY25 ended December 31, 2025)

| | FY25 | FY24 | YoY |
|---|---:|---:|---:|
| Revenue | $4,500M | ~$2,866M | ~**+57%** |
| Government segment (~54% of revenue) | $2,430M | $1,608M | +51% |
| Adj operating income | $2,254M | $1,128M | **+100%** |
| Adj operating margin | **50%** | 39% | +11pp |
| Total SBC | $684M | $692M | flat |
| Cash + Treasuries | $7,200M | n/d | growing |
| Contract liabilities (deferred revenue) | $812M | $566M | **+44%** |
| Government remaining deal value | $4,400M | ~$2,316M | **+90%** |
| Total debt | $0 | $0 | undrawn $500M revolver |

## What the framework caught

**5 PASS / 3 UNVERIFIABLE breakdown:**

| Claim | Verdict | Notes |
|---|---|---|
| C1 Gotham defense/intel franchise | PASS | Verified via usaspending $275M Gotham TO + $2.6B aggregate DoD |
| C2 Project Maven (Army intel AI) | PASS | Verified via usaspending $633M+ in Maven Smart System TOs including a FY26 obligation ($270M W9128Z26FA001) |
| C3 TITAN Army targeting node | UNVERIFIABLE | Not in J-Book corpus; usaspending shows Army Vantage adjacent work but no explicit TITAN award |
| C4 MetaConstellation | UNVERIFIABLE | Cohort-attributed product name; not in corpus |
| C5 Government 54% / $4.4B remaining deal value | PASS | Disclosed in MD&A; +90% YoY growth |
| C6 Forward thesis: capture more federal software spending | PASS | Disclosed strategy |
| C7 Office locations | UNVERIFIABLE | Control claim, not material |
| C8 $1.95B cloud commitment | UNVERIFIABLE | Control claim, not material |

**The two material UNVERIFIABLEs (C3 TITAN, C4 MetaConstellation) are cohort-attributed product names**. The 10-K doesn't explicitly name them — the cohort metadata added them. Per the BAH-style NOT_IN_FILING fix, these should rebucket — but since they don't change composite, the verdict stands.

## What the framework misses — VALUATION

The framework adjudicates disclosed claims. It doesn't price the stock. PLTR's bear case isn't a falsified claim; it's:

| Metric | Value |
|---|---:|
| Market cap | $314B |
| Cash + Treasuries | $7.2B |
| Total debt | $0 |
| Enterprise value | ~$307B |
| FY25 revenue | $4.5B |
| **EV / Sales** | **~68x** |
| FY25 Adj operating income | $2.254B |
| **EV / Adj operating income** | **~136x** |

**For context** — high-growth software primes at 50-100% revenue growth trade 12-25x EV/Sales. PLTR's 68x reflects:
- Government-mission moat (durable, sticky, classified-data lock-in)
- Margin expansion runway (50% adj op margin and still climbing)
- Optionality on AIP / LLM workflow embedding
- Founder-led + secular AI tailwind

But 68x is still 3-5x the high-growth software peer median. The question for a long entry isn't "is the business good?" (yes) — it's "is +50%/yr growth + margin expansion already in the price?"

## The two real signals — buyback termination + heavy insider sales

### Buyback program TERMINATED in January 2026

> "During the year ended December 31, 2025, we repurchased 600,446 shares of our Class A common stock under the Share Repurchase Program. **The Share Repurchase Program was terminated in January 2026.**"

The $1.0B Share Repurchase Program (authorized August 2023) was terminated after using less than ~$110M (~0.6M shares × ~$180 avg). Three implications:
- Capital return story is over — no buyback bid under the stock
- PLTR effectively never used the buyback (used <11% of authorization in 2.5 years)
- Termination signal at a $314B market cap suggests management views shares as not-undervalued at current price

This is **the cleanest framework-incongruent signal**: management's revealed preference (terminated buyback) is at odds with the LONG-tier composite verdict.

### Insider sales: $1.06B over 12 months

| | Value |
|---|---|
| Form 4 filings | 65 |
| Total sales | 476 |
| **Total value sold** | **$1.06B** |
| Proximate-to-budget sales | 23 ($10.7M) |
| Discretionary proximate | **0** |
| Signal | **ROUTINE_10B5_1** |

The framework's signal is "clean" — all sales are 10b5-1 (pre-planned, not discretionary). But the **dollar volume** ($1.06B over 12 months on a $314B mkt cap = 0.34%) is among the heaviest in the cohort. By comparison, BAH's $10.57M is 50x smaller in dollar terms despite BAH being a $9.4B vs $314B mkt cap (so BAH is selling 0.11% — even cleaner).

**Notable individual seller**: Alexander D. Moore (Chief Architect) — multiple proximate sales in the table, including 9,212 shares on 2026-02-02 at $150.23 (13 days after Jan 20 bipartisan budget signed). All 10b5-1.

10b5-1 makes the sales legally clean but doesn't change the economic substance: insiders are continuously distributing $80-100M/month into the market.

### SBC dilution

FY25 SBC of $684M on $4.5B revenue = **15% of revenue as SBC expense**. At current price, $684M ≈ 5M shares of dilution per year (~0.2% annual dilution at current float). Modest relative to mega-cap norms but consistent — adj margins exclude it.

## The Federal Spending Review angle

Unlike BAH/CDRE/PSN, PLTR's 10-K does NOT contain the explicit "contracts impacted, reduced or canceled" language about the new administration's spending review. Instead, PLTR positions AS a beneficiary of efficiency-driven federal spending shifts — the AIP/Foundry platforms are positioned to *replace* legacy consulting contractors.

This is the opposite side of the BAH trade: if federal services budgets compress, traditional consultancy firms lose share but Palantir's AI platforms could be the replacement. **Long PLTR / Short BAH** is a thesis pair on this dynamic.

But: PLTR's government revenue is also dependent on the same federal procurement environment. A blanket budget freeze hurts everyone. The differential bet is on *substitution*, not absolute growth.

## What would need to be true for the LONG to work

1. **Government remaining deal value continues to grow 50%+ YoY**. FY25's +90% may be the peak; even +50% in FY26 would justify continued multiple support.

2. **Adj operating margin holds 50%+**. PLTR's earnings story is driven by margin expansion as much as revenue growth. A pullback to 40% margin would compress EV/EBITDA multiple meaningfully.

3. **AIP / LLM workflow becomes recurring high-volume revenue**, not just project work.

4. **No major insider event** beyond the routine 10b5-1 baseline. If insider selling shifts to discretionary or insider COUNT grows (current ~30-40 unique sellers per year), the framework's signal would flip.

5. **Federal procurement substitution narrative validates** — PLTR wins net new spend that's being pulled FROM traditional consulting.

## What would invalidate the LONG

- **Government segment growth decelerates below +25%**. Revenue must keep up with the multiple.
- **Adj margin gives back gains** below 40%.
- **Insider selling becomes discretionary or accelerates**. Currently 10b5-1; transition to clustered discretionary would break the framework's clean signal.
- **AIP monetization stalls** — heavy current marketing suggests revenue per AIP customer is still being calibrated.
- **Multiple compression below 50x EV/Sales** — would imply the AI premium is being reassessed. At 50x EV/Sales × $4.5B revenue, PLTR's value would be ~$225B (~$98/share) — that's −28% from current.

## Valuation context vs cohort

| Ticker | EV/Sales | EV/Adj-Op-Income | Drawdown |
|---|---:|---:|---:|
| **PLTR** | **68x** | **136x** | −34% |
| BAH | 1.0x | ~9x | −39% |
| CACI | 1.3x | ~13x | −24% |
| LDOS | 1.0x | ~10x | −37% |
| SAIC | 0.6x | ~7x | −18% |

PLTR is fundamentally a different security class — software-revenue at 50%+ growth vs services-revenue at 5-15% growth. Comparing on EV/Sales isn't apples-to-apples, but the multiple-band differential is striking.

## Head-to-head vs BAH (the other framework-LONG-at-trough)

| | PLTR | BAH |
|---|---|---|
| Composite | 0.000 | 0.091 |
| Drawdown | −34% | −39% |
| Revenue growth | +57% | +12% |
| Adj op margin | 50% | ~13% |
| EV/Sales | 68x | 1.0x |
| Buyback runway | **terminated** | $745M active |
| Dividend yield | 0% | 2.8% |
| Insider $ sold | $1.06B (10b5-1) | $10.6M (10b5-1) |
| Net cash position | $7.2B | $(3.1B) net debt |
| Federal-spending-review impact | upside (substitution) | disclosed material |

**Different theses**:
- **BAH**: cheap services prime, mean-reversion bet, dividend + buyback cushion
- **PLTR**: expensive AI growth story, momentum/multiple bet, no capital return cushion

**For pure framework-purity**, PLTR's 0.000 wins. For asymmetric risk/reward at trough, **BAH > PLTR** because PLTR's valuation provides little downside cushion.

## Position-sizing recommendation

**LOW conviction asymmetric long at this price** (1-2% portfolio weight, not 3-5%). The 0.000 composite obscures that:

1. **Buyback termination is a tell.** Management used <11% of the auth before pulling it at $180 average — suggests they view current valuation as fair-to-rich rather than cheap.
2. **$1.06B of insider distribution** is 10b5-1 clean but enormous in absolute terms.
3. **68x EV/Sales** prices in continued ~50% growth + margin expansion. Mean reversion to 40-50x would be a $90-110 stock.
4. **Trough proximity (+14% above 52w low)** is real but the multiple-driven downside floor isn't bounded the way services-prime fundamentals would bound BAH.

If the LONG thesis is **federal-services substitution**, the cleaner expression is **long PLTR / short BAH** (or short ITA) as a pair — captures the relative-substitution dynamic without taking the absolute 68x EV/Sales risk on PLTR.

For a standalone position, prefer waiting for multiple to compress further OR for the buyback to be re-authorized at a lower price (a management revealed-preference signal).

## Framework improvement notes

1. **`valuation_overlay`** M-source — given market cap, EV, revenue, growth rate, and a peer-set valuation distribution, flag percentile-extreme valuations. Would surface PLTR's 68x as a yellow flag the composite doesn't see.

2. **`buyback_program_status_tracker`** — flag program terminations, authorization expirations, and active-vs-dormant status. Would have caught PLTR's January 2026 termination as a material capital-return-signal change.

3. **`insider_dollar_volume_normalizer`** — beyond proximity-to-events, flag absolute insider-sale dollar volume as % of market cap. PLTR's 0.34%/yr is within "normal" but in absolute terms ($1.06B) is a real distribution.

## Files & data

- Scores: `verticals/public_co/data/_local/PLTR.jbook.scores.json`
- 10-K: `verticals/public_co/data/pltr/filings/0001321655-26-000011_10-K.txt` (filed 2026-02-17)
- Insider signal: ROUTINE_10B5_1 (but $1.06B / 476 sales / 65 Form 4 filings)
