# TDG — TransDigm Group Deep Dive

_As of 2026-05-24 · Price $1,213.51 · Market cap ~$67.9B · 10-K filed 2025-11-12 (FY ended 2025-09-30)_

## DISCLAIMER

Algorithmic research output, not investment, fiduciary, or tax advice. Position decisions are the reader's responsibility.

## TL;DR — AVOID (insider override)

Framework scores TDG **0.125 LONG** composite. **Reject this verdict.** `insider_vs_calendar` returns **`CLUSTERED_DISCRETIONARY`** with severity unparalleled in the cohort:

- **97 of 97 proximate sales are DISCRETIONARY** (zero 10b5-1)
- **$131M distributed** in 14-day windows around budget events
- **Kevin Stein** (CEO) alone executed at least 8 sales between $5.6M-$9.5M each, clustered around the January 20, 2026 bipartisan budget signing — totaling **~$59M just from those 8 sales**
- 4 unique owners participating discretionarily

This is the most severe IONQ-pattern insider distribution in the cohort — **larger and more concentrated than CACI's $5.5M / 2 owners**. The CEO is the lead seller.

Context: TDG executed an **$90/share special dividend in August 2025** funded by $5B in new debt. The insider sales likely have a tax-funding component, but **9-figure CEO discretionary sales around budget events is still the canonical signal the framework was built to catch**. The combination of: maximum-leverage capital structure + CEO distributing > $50M discretionarily + 22x EV/EBITDA + congressional scrutiny on aftermarket pricing = **NOT a long candidate**.

## Headline framework verdict — with insider override

| | Value |
|---|---|
| Framework composite | 0.125 LONG-tier |
| **Insider signal** | **`CLUSTERED_DISCRETIONARY`** ⚠⚠ |
| Adjusted view | **AVOID** (insider override) |
| Claims | 10 (7 PASS / 1 MODERATE / 0 SEVERE / 0 RED / 2 UNVERIFIABLE) |
| Drawdown | −25.1% from 52w high $1,620.83 |
| Distance above 52w low | +7.1% above $1,132.88 |
| Market cap | $67.9B (MEGA) |
| Federal direct-prime (USAspending FY23-25) | **$50M** (sells through OEM channels — usaspending undercounts) |

## The insider activity in detail

`insider_vs_calendar` query (cik=0001260221, 365-day lookback, 14-day window):

| Metric | Value |
|---|---|
| Form 4 filings | 86 |
| Total insider sales | **478** |
| Total sale value | **$538M** |
| Proximate to budget events | **97** |
| Proximate value | **$131M** |
| **Discretionary proximate** | **97 of 97 (100%)** |
| Unique discretionary owners | 4 |
| Signal | **`CLUSTERED_DISCRETIONARY`** |

The largest single-event cluster is around **January 20, 2026 bipartisan budget signing**. Top 8 sales from Kevin Stein (CEO):

| Date | Days from event | Owner | Value |
|---|---:|---|---:|
| 2026-02-02 | +13 | Stein Kevin M | $9,513,515 |
| 2026-01-08 | −12 | Stein Kevin M | $8,971,439 |
| 2026-02-02 | +13 | Stein Kevin M | $8,419,438 |
| 2026-02-02 | +13 | Stein Kevin M | $8,081,724 |
| 2026-01-08 | −12 | Stein Kevin M | $7,378,815 |
| 2026-02-02 | +13 | Stein Kevin M | $6,921,488 |
| 2026-02-02 | +13 | Stein Kevin M | $5,690,381 |
| 2026-01-14 | −6 | Stein Kevin M | $5,575,009 |
| **Total** | | **Stein** | **$60.5M** |

This is roughly **half** of TDG's $131M proximate-discretionary total in 8 sales by the CEO alone.

**Counter-argument**: TDG just paid a $90/share special dividend (~$5B total) in August 2025, funded by new debt. The CEO and other insiders may have substantial deferred-comp / vested-options unwinding that requires liquidating around tax events. The Form 4 filings often distinguish exercise-and-hold from sell-on-exercise; in TDG's case the cluster suggests sell-on-exercise.

**Even with the tax-funding context**, the framework's signal is the framework's signal. **The CEO of a 22x EV/EBITDA, 7x leverage aftermarket monopoly distributing $60M discretionarily around a budget action is exactly what the IONQ-pattern detector is designed to flag.**

## Financial snapshot (FY25 ended September 30, 2025)

| | FY25 | FY24 | YoY |
|---|---:|---:|---:|
| Net sales | **$8,831M** | n/d | n/d |
| Gross profit | $5,311M (60.1% margin) | n/d | n/d |
| Net income (TD Group) | **$2,074M** | n/d | n/d |
| EBITDA As Defined (segment-level) | **$4,279M** | n/d | n/d |
| Operating cash flow | $2,038M | $2,045M | flat |
| Cash + ST investments | $2,808M | n/d | n/d |
| **Total debt** | **$30,015M** | $24,880M | **+$5.1B** |
| TD Group stockholders' deficit | **$(9,686)M** | $(6,290)M | structural |

**Capital structure** (the famous TDG playbook):
- **$30B total debt** — among the most leveraged industrials in the cohort
- $11B in debt financing transactions completed FY25 (mix of new issuance + refi)
- $5B new debt August 2025 to fund the special dividend
- November 2025 BOD authorized additional $5B share repurchase
- No maturity until August 2028 — all FY25 debt issuance pushed maturities out
- **Stockholders' deficit −$9.7B** (book equity is negative because TDG buys back / dividends out more than retained earnings → balance sheet capital is debt-only)

**Revenue mix** (FY25):
- **~55% aftermarket** revenue (high-margin, recurring, sole-source)
- **~90% proprietary products** (sole-source content)
- **~43% defense** ($3,761M)
- ~57% commercial (commercial aerospace + non-aviation)
- **No customer >10%; top 10 customers ~40%**
- ~120 manufacturing facilities, 25 US states, 14 countries

## What the framework caught

| Claim | Verdict | Notes |
|---|---|---|
| C1 Defense sales ~35-40%; FY25 defense $3,761M (43%) | PASS | Disclosed |
| C2 Power & Control segment defense rev +19% YoY | UNVERIFIABLE | Specific segment-level claim |
| C3 Airframe segment defense rev +20% YoY | UNVERIFIABLE | Specific segment-level claim |
| C4 DoD budget trending upward → defense outlook | PASS | Macro context |
| C5 Products on every commercial+military aircraft; top 10 ~40% | PASS | Verified |
| C6 ~55% aftermarket; 25-30 yr aircraft life | PASS | Disclosed |
| C7 ~90% proprietary (sole-source) | PASS | Disclosed |
| C8 Simmonds Precision acquisition ~$757M (Oct 6 2025) | PASS | Disclosed subsequent event |
| C9 ~120 facilities | PASS | Verified |
| **C10 ~$413M acquisitions FY25 incl. Servotronics $133M; rollup strategy** | **MODERATE** | Rollup-dependence flag |

The single MODERATE (C10) is on rollup-dependence — appropriate. TDG's growth has historically been ~40% organic + ~60% acquisition. The framework correctly flags the structural acquisition reliance.

## What the framework misses

### 1. Insider signal (covered above)

### 2. Stockholders' deficit + maximum leverage capital structure

TDG operates with **structurally negative book equity** ($-9.7B). The capital structure is built around:
- Continuous debt issuance
- Periodic special dividends ($90/share August 2025 = $5B; prior: $35 in 2024, $18.50 in 2022, $32.50 in 2021)
- Acquisition rollup

The model **works** as long as:
- Aftermarket pricing power holds
- Refinancing markets stay open
- Boeing/Airbus build rates support aerospace cycle

It **breaks** if:
- Congress restricts aftermarket pricing on sole-source DoD spare parts
- Commercial aerospace cycle turns down + refinancing markets close
- A major proprietary line is lost to competitor product

### 3. The congressional pricing scrutiny overhang

TDG has been under recurring DoD IG and congressional investigation for:
- Charging the DoD multiples of cost on sole-source aerospace spare parts (some markups 1000%+)
- Defense Logistics Agency contract pricing reviews
- House Oversight Committee investigations

This isn't a new risk but it sits in the background. A regulatory action (DoD pricing rules, sole-source restrictions) could materially compress aftermarket margins. None disclosed in current 10-K, but the historical pattern matters.

### 4. Valuation

| Metric | Value |
|---|---:|
| Market cap | $67.9B |
| Total debt | $30.0B |
| Cash | $2.8B |
| **Enterprise value** | **~$95.1B** |
| FY25 EBITDA As Defined | $4,279M |
| **EV / EBITDA** | **~22x** |
| Net debt / EBITDA | **~6.4x** |
| FY25 net income | $2,074M |
| **P / E** | **~33x** |
| Special dividend yield (Aug 2025) | $90/share = 7.4% one-time |
| Regular dividend yield | 0% (no ongoing dividend; only special) |

**22x EV/EBITDA at 6.4x leverage** is rich even for the best-in-class capital allocator. Compare to:
- HEI (Heico, peer aerospace aftermarket) at 30x+ EBITDA — but with less leverage (~1.5x)
- Aerospace primes (LMT, RTX, NOC) at 11-15x EBITDA
- Engine OEMs (GE Aerospace) at 25x EBITDA

TDG's premium reflects the proprietary-aftermarket moat, but the leverage means equity is highly geared. Mean reversion to 18-20x EBITDA + spread compression → equity could give back 30-40%.

## Insider activity contextual analysis

Two interpretations of Kevin Stein's $60M+ in CEO discretionary sales:

**Interpretation A (benign)**: Standard CEO compensation unwind. TDG pays huge deferred-comp packages that vest annually; routine selling to fund taxes and diversification. The August 2025 $90/share special dividend created additional taxable events for option-equivalent grants.

**Interpretation B (warning)**: CEO and 3 other insiders distributing $131M discretionarily around budget actions suggests forward expectations are weakening. With debt at $30B and special-dividend funded by new debt, the leveraged capital structure depends on continued aftermarket pricing — any change in that view by insiders is material.

Without further investigation it's hard to disambiguate. But **the prudent investor errs toward Interpretation B** when the framework specifically detects this pattern.

## Head-to-head vs cohort LONGs

| | TDG | CACI | BAH | HII |
|---|---|---|---|---|
| Composite | 0.125 | 0.125 | 0.091 | 0.000 |
| **Insider signal** | **`CLUSTERED_DISCRETIONARY` ⚠⚠** | **`CLUSTERED_DISCRETIONARY` ⚠** | clean | clean |
| Proximate discretionary share | **97/97 (100%)** | 9/10 (90%) | 0/1 (0%) | 0/0 |
| CEO sold > $5M discretionarily | **YES (8+ times)** | YES (8 times) | no | no |
| Drawdown | −25% | −24% | −39% | −29% |
| Net leverage | **6.4x** | ~1.4x | ~2.2x | ~2.1x |
| EV/EBITDA | 22x | 12x | 8.9x | 11x |
| Dividend yield | 0% regular | 0% | **2.8%** | 1.7% |
| **Net verdict** | **AVOID** | **AVOID** | LONG | LONG |

Both TDG and CACI are AVOIDs despite cleanish composites. **TDG's case is more severe** because:
1. CEO is the lead seller (vs CACI President)
2. $60M from one person vs $5M
3. 100% of proximate are discretionary vs 90%
4. Leverage is 4-5x higher
5. Capital structure depends on continuous refi

## What would change the recommendation

For TDG to re-engage as a LONG candidate:
1. **Insider distribution stops**: 90+ days with no discretionary CEO sales
2. **Special dividend cycle clarity**: TDG hasn't disclosed expected timing of next special dividend; if the August 2025 was the cycle peak, leverage path is downward
3. **Margin trajectory**: aftermarket margin holds 60%+ and defense aftermarket continues +19-20% growth
4. **No pricing-regulation event**: DoD IG / House Oversight pricing actions remain dormant

If insider distribution stops and the leveraged-recap completes its arc (debt naturally declines as EBITDA grows), TDG's underlying aftermarket monopoly is genuinely valuable. But that's not the current setup.

## Position-sizing recommendation

**AVOID**. The framework's 0.125 LONG composite reflects clean disclosure, but the insider signal is the most severe in the cohort. The CEO is distributing $60M+ discretionarily around budget actions while leverage sits at 6.4x and the capital structure depends on continuous refi. This is the asymmetric SHORT setup, not LONG.

**For a directional view**: if you must trade TDG, prefer pair **short TDG / long HEI** (true aerospace aftermarket peer; HEI has 1.5x leverage vs TDG's 6.4x). Captures the aftermarket-multiple compression without taking the moat risk.

## Framework improvement triggered (repeats from CACI dive)

1. **`insider_vs_calendar` MANDATORY**: every cohort scoring run should include this query. TDG's $131M discretionary distribution should be impossible to miss.

2. **Insider signal should outweigh composite**: when `CLUSTERED_DISCRETIONARY` fires with >$50M proximate-discretionary value AND CEO/CFO is the lead seller, override the composite to NEUTRAL minimum (possibly SHORT).

3. **`special_dividend_history` tracker**: TDG-style serial-special-dividend names need their own classification. The capital-return story is real but the cycle creates artificial insider-comp-unwind patterns that confuse the framework.

4. **`net_leverage_at_cycle_peak` flag**: 6.4x leverage on TDG is the high end of its historical range. The asymmetric setup is short at peak leverage / long at trough leverage. Tracker would help time entry.

## Files & data

- Scores: `verticals/public_co/data/_local/TDG.jbook.scores.json`
- 10-K: `verticals/public_co/data/tdg/filings/0001260221-25-000081_10-K.txt` (filed 2025-11-12)
- USAspending: $50M / 1,301 awards FY23-25 (most TDG defense rev is via OEM channels, not direct)
- Insider signal: **`CLUSTERED_DISCRETIONARY`** ⚠⚠ — 97/97 discretionary, $131M proximate-discretionary, CEO Kevin Stein sold $60M+ in 8 chunks around Jan 2026 budget event
