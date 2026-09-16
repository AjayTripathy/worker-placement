# COMMODITY COURT — PRECIOUS METALS AS BALLAST
**Date:** 2026-08-14 · **Book:** IBKR alpha book, NLV $1,035,102 (live) · **Held:** PHYS 320 units @ 31.205 basis, $10,634 = 1.03% of NLV
**Mode:** Two-mode, leading with disconfirmation of the add case.

---

## VERDICT (one line each)

| Question | Verdict |
|---|---|
| **Target ballast %** | **3% of the book it ballasts — AFFIRMED, but for a different reason than the July court gave.** Today that is ~$31k (934 units); post-September ~$168k (5,056 units). |
| **PHYS — add / hold / trim** | **HOLD 320. Do NOT add at market.** Fund the remaining 2% only through two rest-below rungs at 30.80 and 29.20 (both *below* our 31.205 basis). No trim. |
| **PSLV — yes / no** | **NO.** The July REJECT stands, and it now stands on a second, stronger leg that does not depend on squeeze mechanics at all. |
| **Vehicle** | **PHYS with a timely QEF election is correct** — but the election is worth ~$425 at today's size and ~$6,700 at target size. The vehicle choice only pays if the sizing decision is actually executed. |
| **Highest-value action** | Not a trade. **The 2026 Form 8621 QEF election deadline** — see the tripwire at the end. |

**No-change is most of this verdict, and it is a real verdict.** The strategic target survives; the tactical add does not.

---

## MODE B — FIRST PRINCIPLES (lead)

I derived the decisive questions without the July court's framing, then went looking for evidence against the add.

### B1. The lead finding: we have been sizing gold against the wrong exposure

The July court called PHYS *"uncorrelated crisis/inflation convexity for the accumulator book"* and sized it as a percentage of the equity book. Both halves of that are wrong.

**What gold actually hedges in THIS book.** The book is long quality equities, Japan/Europe value, EM banks, consumer recovery, energy — plus $475,820 of cash and T-bills (46.0% of NLV) and a $5M inflow. Four tails, and gold is the right instrument for exactly one:

| Tail | What actually hedges it | Gold's role |
|---|---|---|
| Equity drawdown / AI-capex break | 46% cash + the $5M inflow | Weak and regime-conditional — see B2 |
| Liquidity vacuum (everything sold) | Cash | Mild help; falls less than equities |
| **Monetary / inflation / debasement** | **Nothing else in the book** | **This is the whole job** |
| War / supply rupture | EQT (owned, designated supply-shock leg) | Secondary help |

In the debasement tail, cash and T-bills — the book's largest position — are *the thing being impaired*. That is the only tail where gold is not substitutable. So the correct sizing base is the **permanent nominal-claim exposure**, not the equity book.

Permanent nominal claims (excluding the transitional $5M and the working reserve that will deploy): household CA munis $351,605 + a steady-state T-bill reserve of roughly $400,000 ≈ **$751,605**. A conventional 10–20% debasement hedge on that is **$75k–$150k**.

That brackets the post-September 3%-of-book figure ($168,000) closely enough that **the existing 3% target is affirmed** — but it is now anchored to something defensible. It also explains why the target should scale with *deployment*, not with the arrival of cash: the household already carries a large offsetting inflation hedge in a home with a fixed-rate mortgage (the desk's own disaster model flags this), which is why the number is 3% and not 10%.

### B2. Gold did not hedge equities in this book's own window — and our own note says it does

*Method:* 104 weekly returns, PHYS / PSLV / SPY, 2024-08 → 2026-08, pulled from IBKR price history. *Authority:* our own tape.

| Regime | n | mean SPY | mean PHYS | PHYS positive | mean PSLV |
|---|---|---|---|---|---|
| All weeks | 104 | — | corr +0.18, beta +0.25 | — | corr +0.36, beta +0.98 |
| SPY down weeks | 44 | −1.52% | **+0.39%** | 66% | −0.16% |
| **SPY weeks worse than −2%** | **13** | **−3.03%** | **−1.12%** | **46%** | **−3.37%** |

Named episodes (peak-to-trough weekly closes):

| Episode | SPY | PHYS | PSLV |
|---|---|---|---|
| Feb–Mar 2025 tariff shock | **−17.1%** | **+4.8%** | −6.9% |
| Jan–Mar 2026 drawdown | **−8.6%** | **−0.9%** | **−14.4%** |
| Feb→Jul 2026 metals bust | +7.2% | −20.7% | −32.9% |

**Finding:** gold hedged the 2025 shock and did **not** hedge the 2026 one. Across the 13 sharpest equity weeks it *lost* 1.12% on average and was positive less than half the time. Correlation to SPY is **+0.18**, beta **+0.25** — positive, not negative. Realized volatility is **21.1%**, higher than SPY's 15.5%.

This is a takeaway-versus-data divergence **in our own July court note**, not in a promoter's deck. "Uncorrelated crisis convexity" is not what the data says. The honest description is: *a low-beta, high-volatility asset with a fat right tail in monetary regime breaks, whose equity-hedge property is regime-conditional and was absent in 2026.* Corrected in the ledger.

### B3. A 3% sleeve is not a risk-reduction tool — it is a regime option

*Method:* two-asset variance, using the verified inputs (equity vol 15.5%, gold vol 21.1%, correlation 0.18).

| Gold weight | Book volatility | Change |
|---|---|---|
| 0% | 15.50% | — |
| 1% | 15.39% | −0.11pp |
| **3%** | **15.16%** | **−0.34pp (−2.2% relative)** |
| 10% | 14.49% | −1.01pp |

**Finding:** at 3%, gold removes about a third of a volatility point. Anyone holding this sleeve to smooth the ride is buying the wrong thing. It should be underwritten and sized like an **option premium on a monetary regime break** — a small, permanent, deliberately unlevered claim — and graded on whether that regime arrives, not on quarterly volatility contribution.

### B4. Silver is a symmetric lever on gold, not a diversifier

*Method:* same 104-week panel. *Authority:* our own tape.

| Measure | Value |
|---|---|
| Silver beta to gold | **1.56** (correlation 0.775) |
| Silver / gold move, **gold-up** weeks | **1.66×** |
| Silver / gold move, **gold-down** weeks | **1.68×** |
| Silver correlation / beta to SPY | **0.36 / 0.98** |
| Silver annualized volatility | **42.4%** (gold 21.1%) |
| Silver in the 13 worst SPY weeks | **−3.37% mean, positive 38% of the time** |

**Finding:** the up-capture and the down-capture are the *same number*. Silver gives you 1.6× of gold in both directions — that is the definition of a lever, not a diversifier. Worse, it carries a **full unit of equity beta (0.98)**. Adding PSLV to the ballast sleeve injects equity beta into the one sleeve whose entire purpose is to not have any.

This kills the silver case **independently of the squeeze mechanics** the July court rejected it on. Even if every tightness trigger fired tomorrow, PSLV would be a commodity *trade* funded from risk budget — never a ballast allocation. It should never again be evaluated inside a ballast frame.

The relative-value case is also absent: **gold/silver ratio 67.7**, near its long-run average. Silver is neither cheap nor expensive against gold.

---

## MODE A — CLAIM VERIFICATION

Each row: the claim → how it was checked → the authority → the finding.

| # | Claim | Method / Authority | Finding |
|---|---|---|---|
| A1 | PHYS trades at a discount to NAV | Sprott issuer page, 2026-08-13: NAV $33.72, price $33.00 | **VERIFIED −2.13%.** Live estimate −2.0% at $33.23. Unchanged from the −2.5% at our July entry — no vehicle-side improvement, no premium tax on entry |
| A2 | Spot gold and silver | Kitco, 2026-08-14 15:36 ET | **VERIFIED** gold **$4,376.30**/oz, silver **$64.65**/oz |
| A3 | Cross-check the metals prices independently | Sprott PSLV total NAV $13.92B ÷ 215,405,617 oz = **$64.62**/oz vs Kitco $64.65 | **VERIFIED** — two independent sources agree to 0.05% |
| A4 | Gold is "extended" after a big run | IBKR weekly history; PHYS 52-week range 25.43–42.07, live 33.23 | **REFUTED as stated.** Gold is **17.2% below** its Feb/Mar-2026 peak weekly close and at the **47th percentile** of its 52-week range. Mid-range, not extended |
| A5 | Money is fleeing gold during the drawdown | Sprott ounces held: 3,671,782 (2026-07-21, our July court source) → **3,705,131** (2026-08-13) | **REFUTED. +33,349 oz (+0.91%) in three weeks — net creations.** Real money accumulated *into* the correction. The most constructive verified datum in this court |
| A6 | Speculative positioning is washed out | CFTC Commitments of Traders, COMEX, report date 2026-08-04 | **REFUTED.** Gold non-commercial net long **+197,634 = 53.2% of open interest**; shorts only **7.9%** of OI; net long **grew +15,564** week-over-week. One-sided and adding |
| A7 | PSLV re-entry trigger "managed money net ≤ 0" has fired | Same COT report | **REFUTED.** Silver non-commercial net **+22,280** (19.9% of OI) — net long, not net short |
| A8 | PSLV trigger "two consecutive weekly increases off a trough with spot above the 20-day average" has fired | Same COT + PSLV weekly closes | **NOT MET.** Net rose only **+63** w/w (22,217 → 22,280) and is not off a trough. Price is above its 20-day average (21.06 vs ~19.85) — that leg alone is not the trigger |
| A9 | PSLV trigger "lease rate above 3–5%, or registered stock below 80 Moz and drawing" | Attempted CME / LBMA / Kitco lease pages | **UNVERIFIED this session.** Last known: lease 0.1%, registered rebuilding 75.7 → 93 Moz. No evidence of change, but treat as a gap, not a clean bill |
| A10 | Central-bank buying is accelerating and driving gold | World Gold Council, *Gold Demand Trends Q2 2026*, published 2026-07-30 | **PARTIALLY REFUTED.** Total gold demand including OTC was **1,269t in Q2, unchanged year-over-year**; H1-2026 2,522t at a record **US$380B**. The record is **price**, not incremental tonnage. Country-level central-bank detail sits behind a login — **UNVERIFIED** |
| A11 | Sprott trusts are PFICs requiring a QEF election | Sprott issuer page, 2026-08-13 | **VERIFIED, issuer's own words:** "all Sprott Physical Trusts are considered PFICs"; investors "must make a timely Qualified Electing Fund (QEF) election by filing IRS Form 8621" in their **first year of ownership**; Form 8621 must be filed **annually** while units are held, "even in years with no distributions" |
| A12 | PHYS management fee 0.39%; PSLV 0.52% | Sprott issuer pages, 2026-08-13 | **VERIFIED.** PHYS 0.39% MER, 3,705,131 oz. PSLV 0.52% MER, 215,405,617 oz, NAV $22.00, price $20.97, **discount −4.69%** |
| A13 | Real interest rates are the dominant gold driver and support the add | US Treasury real yield curve, FRED, YCharts — all blocked or timed out this session | **UNVERIFIABLE this session.** See the gap register. This is the single most important gold driver and I could not source it |

---

## GAP REGISTER — what is NOT verified

Recorded explicitly because **unverified is not clean**.

| Gap | Status | Consequence |
|---|---|---|
| 5-year and 10-year TIPS real yields | **UNVERIFIED** (Treasury timed out, FRED 403, YCharts 405) | The primary gold driver is unsourced — this alone bars an upsize |
| Trade-weighted US dollar | **UNVERIFIED** | Secondary driver unsourced |
| Central-bank net purchase tonnage, 2026 YTD | **UNVERIFIED** (WGC detail behind login) | The main structural bull leg is unquantified; only the flat total-demand figure (A10) is verified |
| Gold ETF flows, tonnes and US$ | **UNVERIFIED** (WGC login) | Partially substituted by the PHYS ounce count (A5), which is issuer-audited and *more* direct for our vehicle |
| COMEX registered silver; 1-month silver lease rate | **UNVERIFIED** | One PSLV trigger leg untested — does not change the verdict, since B4 rejects PSLV on structure regardless |
| Catalyst narrative for the Feb-2026 spike and bust | **UNVERIFIED** | We know the *shape* of the move from our own tape but not its cause |

**None of these gaps can turn the verdict bullish, and one of them (real rates) is load-bearing enough to bar an upsize on its own.** They can, however, turn it more bearish — so the asymmetry favors holding.

---

## THE TAPE — what actually happened (our own price history)

Derived from PHYS/PSLV weekly closes and the verified oz-per-unit ratio.

| | Aug-2024 | Peak (Feb/Mar-2026) | Trough (Jun/Jul-2026) | Now |
|---|---|---|---|---|
| **Gold** | ~$2,570 | ~**$5,290** | ~$3,990 | **$4,376** |
| **Silver** | ~$30 | ~**$116** | ~$53 | **$64.65** |
| **Gold/silver ratio** | ~86 | ~48 | ~74 | **67.7** |

Gold: **+106%** into a parabolic Feb-2026 peak, **−24.5%** peak-to-trough, now **+9.6% off the low and −17.2% below the peak**.
Silver: **+287%** into the peak, **−45.7%** peak-to-trough (a single week in Feb-2026 opened at 35.67 and closed at 26.41), now **+16.7% off the low and −36.6% below the peak**.

Silver's entire outperformance into the top has round-tripped and then some — the ratio went 86 → 48 → 74 → 67.7. That round trip *is* the B4 finding rendered in prices.

---

## THE ADD DECISION — disconfirming case first

### Against adding at market today

1. **Positioning is crowded long.** Gold speculative net long is 53.2% of open interest with shorts at 7.9%, and it *grew* in the latest week. Adding here joins a one-sided trade after a 10% bounce.
2. **We are inside the window our own knowledge graph says not to trust.** The July PSLV court encoded: *"conditional on within-6-months-of-a-parabolic-peak the low-positioning buy signal is roughly 0-for-3: 1980, 2011, 2013."* Gold's parabolic peak was Feb/Mar-2026. We are ~6 months past it. That lesson was written for silver; the mechanism is identical for gold, and applying our own rule to the metal we actually own is the point of having a knowledge graph.
3. **Demand tonnage is flat.** Q2-2026 demand unchanged year-over-year at 1,269t. The record dollar figure is price. The "structural central-bank bid" story is not supported by the one WGC number I could verify.
4. **The stated hedge property is refuted in-sample** (B2): gold averaged −1.12% in the 13 sharpest equity weeks.
5. **The book is 46% cash.** The standing net-buyer doctrine is explicit: a cash-rich book buys no insurance, because drawdowns are discounts. Ballast's premise — a book that cannot sell into a drawdown — does not describe this book today. The doctrine also says protection **phases in with deployment**; the corollary is that it should not phase in *ahead* of deployment.
6. **Gold is more volatile than the index it is meant to stabilize** (21.1% vs 15.5%), and at 3% removes 0.34pp of book volatility (B3).
7. **Adding at market costs 6.5% more than the July tranche** with no improvement in the vehicle (discount unchanged at ~2%) and no new verified evidence.
8. **The primary driver is unverified** (A13). Upsizing on an unsourced driver breaks our own standard.

### For adding

1. Gold is **17.2% below the peak** and at the **47th percentile** of its 52-week range — not an extended entry (A4).
2. **PHYS ounces grew 0.91% in three weeks** — verified net creations during the drawdown (A5). This is the strongest bullish datum in the court because it is issuer-audited and specific to our vehicle.
3. Discount stable at ~2% — near the trust's cheap end, no entry tax.
4. The debasement reframing (B1) says the strategic target is right and we are at one-third of it.
5. The $5M landing will **enlarge** the nominal-claim exposure gold exists to hedge.
6. Ballast requires no edge — the fairly-paid-risk doctrine makes a structural allocation ownable on its own.

### Resolution

The strategic target is right and the tactical timing is poor. Under the response taxonomy, a **timing** finding routes to *tranche, don't time*, and a **data gap** routes to *don't upsize until verified*. Both apply. So:

**HOLD 320 units. Add only below our own basis, via resting limits.**

| Rung | Price | Implied gold | Size | vs 31.205 basis |
|---|---|---|---|---|
| Held | 31.205 | ~$4,110 | 320 u / $9,986 | — |
| Rung 1 | **30.80** | ~$4,056 | 320 u / $9,856 | **−1.3%** |
| Rung 2 | **29.20** | ~$3,846 | 320 u / $9,344 | **−6.4%** |
| **Full ladder** | | | **960 u ≈ $31k ≈ 3.0% of NLV** | **average basis ~30.40 — below today's basis** |

Rung 1 sits just above the July trough (PHYS 30.31 weekly close, 29.76 low). Rung 2 sits below it — a genuine flush. This funds the entire 3% target **only at prices better than what we already paid**, and it never chases. If neither fills and the $5M deploys, re-size the target against the larger book and re-court rather than reaching.

**No trim.** Three reasons: the position is at a **short-term** gain (bought 2026-07-22, under one year) in a book whose whole design defers gains and harvests losses; 1% is below target, not above it; and selling a PFIC before the QEF election is in place invites the punitive excess-distribution regime. Holding strictly dominates.

---

## TAX — vehicle comparison

Top-bracket US taxable holder, rates including the 3.8% net investment income tax.

| Vehicle | Structure | Rate on a long-term gain | Annual filing | Verification |
|---|---|---|---|---|
| **PHYS / PSLV with timely QEF** | Ontario closed-end trust; PFIC | **23.8%** (20% + 3.8%) | **Form 8621 every year**, even with no distributions | PFIC status and QEF requirement **VERIFIED** from Sprott, 2026-08-13 |
| PHYS / PSLV **without** QEF | Same, falls into the §1291 excess-distribution regime | **~40.8% + an interest charge** — no long-term rate at all | Form 8621 | Sprott states the election is required to "preserve capital gains treatment" — **VERIFIED** |
| GLD / SLV / GLDM / SGOL / SIVR | US grantor trust; holder treated as owning the metal | **31.8%** (28% collectibles + 3.8%) | None (1099-B) | Standing desk treatment — **ASSERTED, not re-verified this session** |
| COMEX futures (GC, MGC) | §1256 contract | ~**30.6%** (60/40 blend) — but **marked to market annually**, forcing recognition | Form 6781 | **ASSERTED, not re-verified** |
| GDX / miners | Ordinary equity | 23.8% | None | Not ballast — this is equity beta. The desk's own AEM court called it *"gold beta in costume"* and frame-rejected it |

**The QEF advantage over the collectibles rate is 8.0 percentage points of the gain.** What that is worth:

| Position size | Gain | QEF saves vs GLD |
|---|---|---|
| $10,634 (today) | +50% | **$425** |
| $31,000 (3% today) | +50% | $1,240 |
| $168,000 (3% post-Sept) | +50% | **$6,720** |
| $168,000 | +100% | $13,440 |

Against roughly $150–400/year of Form 8621 preparation, **the QEF election is clearly worth it above ~$100k and roughly a wash at today's $10.6k.** The vehicle choice is therefore *coupled to the sizing decision*: PHYS-with-QEF is correct **because** the target is $168k. If the target were permanently $10k, GLDM at 0.10% and zero filings would be the better vehicle. The desk's standing "QEF committed" treatment is **affirmed**, conditional on actually funding the target.

### ⚠ Operational tripwire — the highest-value item in this court

The QEF election must be made for the **first year of the holding period**. PHYS was bought **2026-07-22**, so the election is due with the **2026 return filed in 2027**. It is still open — but if it is missed, the position becomes §1291-tainted and requires a purging election to fix. Note also that the election is **per fund**: if PSLV is ever bought, it needs its own timely election.

This is worth more than any trade in this court, and it is a calendar item, not a market call. The tax-guy email drafted in July needs to land before the 2026 return.

---

## WHAT WOULD CHANGE THIS VERDICT

| Trigger | Action |
|---|---|
| Real yields verified and falling (5y/10y TIPS) | Re-court the add; this is the missing driver |
| PHYS ounces held start **shrinking** | The one verified bull datum inverts — re-court immediately |
| Gold speculative net long falls below ~35% of open interest | Positioning objection clears |
| The $5M actually deploys into equities | Ballast target re-sizes against the larger book; protection follows deployment |
| PHYS trades at a **premium** to NAV | Entry tax appears — pause the ladder, that discount is the cheap-entry mechanism |
| Silver: registered stock below 80 Moz **and drawing**, or 1-month lease above 3–5% | Re-court PSLV **as a commodity trade at 1.5% max**, funded from risk budget — **never** from the ballast sleeve (B4) |
| WGC central-bank tonnage verified as accelerating | Strengthens the structural leg; still does not license a market add |

---

## LEDGER / DASHBOARD ACTIONS

- **PHYS** → state HOLD, sleeve `real_asset_ballast`, target 3% of book, held 1.03%, edge class **RP_FAIR** (structural allocation, **no information edge claimed**). Correct the conviction line: the July "uncorrelated crisis/inflation convexity" wording is refuted by our own tape (B2) and should read *low-beta, high-volatility, regime-conditional; the job is the monetary tail, not the equity tail*.
- **PSLV** → remains **WAIT/REJECT**. Add the new structural basis (B4): symmetric 1.6× lever on gold with a full unit of equity beta; **permanently disqualified from the ballast frame** regardless of trigger status. The weekly trigger pack keeps grading as a commodity-trade watch only.
- **Rungs 30.80 / 29.20** → stage as rest-below limits, not submitted; both below the 31.205 basis by design.
- **Form 8621 / QEF for tax-year 2026** → calendar tripwire, owner = the tax preparer, deadline = the 2026 return.
- **Gap register** → carry the six unverified items forward; real rates is the one that blocks an upsize.
