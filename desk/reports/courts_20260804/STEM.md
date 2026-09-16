# STEM — SThree plc — COURT (LSE shelf rank 22, band 16-30)

**Date** 2026-08-04 · **Lane** `lse_shelf_20260804` · **Verdict: REJECT 2/10 — NOT A DRAWDOWN**

## Identity and unit basis
SThree plc, ISIN GB00B0KM9T71, **LSE Main Market**, UK-incorporated (so 0.5% SDRT applies on buys).
IBKR line **conid 39131980, exchange LSE, STK** — executability CONFIRMED at the line level.
Quotes in **GBp (pence)**. Close 2026-08-04 = **265.5p = £2.655**; IBKR touch 265.5 / 266.5 (38bp).
Specialist STEM staffing — contract and permanent placement, Netherlands/Germany/US-weighted.

Market cap: the screen carries $454M (£337.8M) on a **filing share count of 127.24M**. The LSE-implied
count is **118.45M** — a 7.4% divergence. Cause identified: SThree has been running a **continuous
buyback since at least 27 Mar 2026** (weekly "Transaction in Own Shares" RNS, 18 of them through
24 Jul 2026), cancelling stock. The LSE-implied count is the fresher figure, so the true cap is
nearer **£315M**. The screen's count is stale in the *conservative* direction (it overstates the cap
and therefore understates cheapness) — no action needed, but the four-way share-count check is
explained, not clean-by-luck.

## Cause check — what actually happened
The price did not fall. **It nearly doubled.**

| fact | source | figure |
|---|---|---|
| Close 2026-08-04 | yfinance daily bars, GBp | **265.5p — this IS the 52-week high** |
| 52-week low | same | 137.29p on 17-Sep-2025 |
| Move off the low | same | **+93.2%**, 321 days |
| Move in the last three months | same | **+45.3%** |
| Off the 52-week high | same | **0.0%** |

Meanwhile the business went the other way. H1-FY26 (reported 16 Jun trading update, 21 Jul full
interims): **net fees down 8%**, half-year profit described in trade coverage as having "plunged as
AI, war weigh on hiring", US the only growth geography, FY26 outlook *maintained* (not raised).

So: **the multiple re-rated ~90% on an estimate base that is still falling.** That is the exact
inverse of the pattern this frame is built to buy (multiple compressed on stable or rising
estimates). It is a cyclical being bid for a recovery that has not yet appeared in the numbers.

## Ruling — NOT A DRAWDOWN (frame-reject)
Under quality-at-own-history-discount, a name printing its 52-week high after a 93% run is not a
candidate. The screen ranked STEM on **trailing** cheapness that the last three months have already
consumed. It is neither a de-rate nor a derailment — it is a re-rate we missed, and the court's job
is to say so rather than to reverse-engineer a reason to buy it.

## Earnings position — the melting flag is real and severe
`ebit_hist` (newest first, £): **27.6M · 65.1M · 84.7M · 84.0M**.
- **EBIT is 0.33x its own four-year peak.** Both the peak anchor and the legacy anchor agree here
  (0.33 either way), so this is not a trough-anchor artifact in either direction — it is a genuine
  67% earnings collapse from the 2022-23 contractor boom.
- **EBIT margin 2.1%** on £1.302bn of revenue. Note this is *gross* revenue — staffing's real
  revenue line is **net fees**, and revenue/EBIT ratios on a staffing company are close to
  meaningless. The screen used gross revenue; the honest denominator is net fees, which the screen
  does not carry. Flagging as a **screen metric-choice defect for the staffing sector**, not a
  refutation of the multiple itself (EV/EBIT is unaffected).
- EV/EBIT **11.6x on trough earnings**; on peak EBIT of £84.7M the same EV is 3.8x. The gap between
  those two numbers *is* the entire investment debate, and nothing in the H1 print resolves it
  toward the second.

## The FCF yield is the screen's load-bearing metric and it is the suspect one
The composite ranks STEM largely on a **15.7% FCF yield** — implying roughly £53M of free cash flow
against £27.6M of EBIT, i.e. **cash flow at ~1.9x operating profit**. On a staffing company whose
contractor book is *contracting*, the mechanism that produces this is well known and is not
earnings: **a shrinking contractor book releases receivables**. Fewer contractors on assignment
means less working capital tied up, and the release shows up as operating cash flow exactly once.
The screen's `wc_fcf` guard reads **False** on this name — **the guard did not fire on a name whose
FCF is 1.9x EBIT while net fees fall 8%.** That is a guard-coverage gap worth recording alongside
the intake's section-5 defect list.

**Status: PLAUSIBLE, not confirmed** — I did not obtain the H1-FY26 cash-flow statement itself, so
the decomposition of the £53M between earnings and working-capital release is **UNVERIFIED**. It is
the top gap on this name, and it cuts against the screen, not for it.

## UK battery
| item | result |
|---|---|
| **Pension by hand** | The screen's £2.58M is a **provisions proxy, not a pension** (`pension_is_proxy: true`) and is immaterial at 1% of equity either way. SThree floated in 2005 out of a business founded in 1986 — no legacy DB scheme is expected, and none is material to the P/B. **Not the CHH/COST failure mode.** Stated as checked; the IAS-19 note itself was not read, so this is PLAUSIBLE rather than CONFIRMED. Immaterial to the verdict at this scale. |
| **Capital commitments** | Not read — and **not required**, because no FCF-based claim is load-bearing in this verdict. The FCF yield is being *rejected*, not relied on. |
| **Cash quality** | Cash £68.0M, debt £49.4M of which **£47.5M is IFRS-16 lease liability**. Ex-leases the balance sheet is essentially debt-free with ~£66M cash. Net cash is only 5.5% of cap — small enough that no securities-as-cash correction changes anything. `securities_as_cash: false`, no short-term investments. **CONFIRMED not a CAPD-shaped problem.** |
| **Friction** | 0.5% SDRT + half of a 38bp touch = **~69bp all-in** — one of the cheapest entries in the band. |
| **Executability** | $826k median daily turnover; 20%-of-prints order cap = **$165k/day**. A 0.75% position ($24.75k) fills in well under a session. **Size is not the constraint here — the thesis is.** |
| **Withholding** | UK-incorporated, 0% dividend WHT. Genuine, but a *holding-period* edge that does nothing for an entry we are declining. |
| **Staleness** | Screen fundamentals are the **FY25 balance sheet dated 30-Nov-2025 — eight months old**, and the H1-FY26 print landed 21 Jul 2026 *after* them. The screen is ranking a pre-deterioration snapshot. Material. |

## Findings table
| claim | source | result |
|---|---|---|
| Quotes in GBp; 265.5p on 2026-08-04 | yfinance daily bars + IBKR live snapshot (conid 39131980) | CONFIRMED |
| Price is at its 52-week high, +93% off the low | yfinance 1y bars | CONFIRMED |
| H1-FY26 net fees −8%; FY26 outlook maintained | 16-Jun-2026 trading update, 21-Jul-2026 interims (via RNS index + trade press) | CONFIRMED |
| EBIT 0.33x its own 4-year peak | screen `ebit_hist`, both anchors agree | CONFIRMED |
| Continuous buyback since Mar-2026 explains the 7.4% share-count divergence | 18 "Transaction in Own Shares" RNS, 27-Mar→24-Jul-2026 | CONFIRMED |
| No takeover approach / not in a Code offer period | Takeover Panel disclosure table join (ISIN-exact), plus news sweep | CONFIRMED (checked negative) |
| 15.7% FCF yield is receivables release from a shrinking contractor book | mechanism identified; H1 cash-flow statement not obtained | **UNVERIFIABLE — top gap** |
| No material DB pension scheme | provisions proxy immaterial; IAS-19 note not read | PLAUSIBLE |

## The AI conflict — stated, not averaged away
SThree is **short AI adoption**, not long it: its product is placing technical and engineering
contractors, and the company's own H1 commentary cites AI as a hiring headwind. The house's frozen
call is AI-BREAK|2027-12-31 @ 0.45. Note carefully that **that call does not rescue this name**: an
AI *capex* break is a collapse in datacentre and model spending, which in the near term would
*further* depress technology hiring rather than send clients back to human contractors. The two
propositions — "AI capex breaks" and "firms stop substituting AI for junior technical labour" — are
different, and only the second would help STEM. The entry would require the second, for which there
is no evidence. Do not net the two.

## Scenarios (per share, pence, ~120M shares post-buyback)
| | p | FV | reasoning |
|---|---|---|---|
| Bear | 0.30 | **149p** | AI substitution is structural, not cyclical; net fees keep falling; EBIT settles ~£20M; 8x EV/EBIT |
| Base | 0.45 | **353p** | cycle troughs in FY26-27, EBIT recovers toward a £45M mid-cycle, 9x EV/EBIT |
| Bull | 0.25 | **599p** | full cycle recovery plus the US build-out, EBIT £70M at 10x |

**E[FV] ≈ 353p** vs 265.5p — a headline +33%.

**And that is exactly why the verdict is still REJECT.** Solving the two-point version of the same
scenario set for the price gives a **market-implied ~57% probability of the mid-cycle recovery
case**. Our honest probability, with net fees still falling eight weeks ago, is not above that. The
recovery is **already in the price** — bullish-but-priced is FAIR, not edge. There is no edge to
collect, only cyclical beta bought at the top of a 93% run.

## Kills / what would change this
1. A **pullback to 175-200p** (a 25-35% give-back) *combined with* evidence the fee decline has
   stopped — that would convert this from a chased re-rate into an actual entry.
2. **Two consecutive periods of positive net-fee growth**, contract book first. Until then the
   estimate direction is down and no multiple is low enough.
3. A **Code offer**. Would make it a merger-arb name, not this lane. (Free option, never a thesis;
   and the house's own cohort work says a takeout can be a down round.)

## Freezable call
**STEM | 2027-02-28 | SThree FY26 net fees decline again year-on-year (FY26 full-year net fees below
FY25) | our_p = 0.70.** This tests the load-bearing disagreement — the market has paid for the turn;
we say the turn is not yet in the numbers.

## Score: 2/10 — REJECT
Frame-reject on path (52-week high, +93% off the low, +45% in three months), corroborated by a 67%
earnings collapse from peak with fees still falling, a FCF yield that is probably working-capital
release, and an E[FV] whose upside is already priced. No red team required. Not a screen error —
the screen did its job on trailing data; the tape moved past it.
