# LYFT — Lyft, Inc. (Class A) | COURT_QUEUE_20260804, Tier 1
**Court date 2026-08-03 (US evening, grading for the 08-04 session) · independent adversarial court · Mode-B led**

**VERDICT: 4/10 — PRINT-CONDITIONAL WATCH. No entry at $16.38.**
Classification: **RISK_PREMIUM**, no edge claim.
Ruling: **DE-RATE on the reported metric; EARLY-STAGE DERAILMENT on the underlying unit metric.**
Red team required? **No** (score < 6).

---

## 0. Live basis

| Item | Value | Basis |
|---|---|---|
| Last | **$16.38** | IBKR close, 2026-08-03, `is_close: true`, prior close $16.38, contract 359130923 NASDAQ |
| 52w high / low | $25.54 (2025-11-12) / **$12.46 (2026-03-30)** | IBKR `misc_statistics` + daily bars |
| Off 52w low | **+31.5%**, **126 calendar / 88 trading days** since the low | daily bars |
| 13w high | $16.52 — **spot is 0.8% below the 3-month high** | IBKR `misc_statistics` |
| YTD | −15.4% | IBKR `year_to_date_change` |
| Underlying annual IV | **68.8%** | IBKR `implied_vol_underlying` |
| Aug-7 $16.5 straddle | call $0.85 + put $1.00 = $1.85 → **±11.3% implied** on the Aug-6 print | IBKR option marks; **close-only, put OI = 8 — approximate** |
| Shares out | 379.7M (Class A; 382.5M at 3/31/26, no Class B outstanding) | yfinance; 10-Q balance sheet |
| Market cap | **$6,219M** | 379.7M × $16.38 |

**PATH CHECK — LATE, and the contract requires me to say so.** +31.5% off a low that is **126 days old**, and the stock is sitting **0.8% under its 3-month high** going into a ±11% binary in three days. This is the top of the bounce, not the bottom of the drawdown. The favourable entry geometry existed in late March and no longer does.

---

## 1. CAUSE-CHECK — what actually happened

**Peak 2025-11-12 at $25.54**, immediately after a strong Q3-25 print (Nov-5). Drift lower into February.

**Event — 2026-02-10 AMC (Q4-25 print) → −17.0% on 2026-02-11, 74.3M shares (~7× normal).**
Source: 8-K 0001628280-26-006817, EX-99.1 `lyft-2025x12x31pressreleas.htm`.
The release was headlined *"Record Q4 and Full-Year 2025 Results — Delivered accelerated Q4 Gross Bookings growth — Announces new $1 billion share repurchase program."* Three things in it broke the stock:

1. **Gross Bookings +19% but revenue only +3%** — a ~1,600bp divergence in a single quarter, caused by *"a $168 million impact from certain legal, tax, and regulatory reserve changes and settlements"* charged **against revenue**.
2. **Net income of $2,755.1M is economically empty** — XBRL `IncomeTaxExpenseBenefit` FY25 = **−$2,897.3M**, a deferred-tax valuation-allowance release. Derived GAAP **operating income for Q4-25 was −$185.0M** (FY25 `OperatingIncomeLoss` −$188.4M less 9M-25 −$3.4M), against +$23.1M in Q3-25. Confirmed no impairment: `GoodwillImpairmentLoss` and `ImpairmentOfLongLivedAssetsHeldForUse` both **$0** for FY25 — so the entire Q4 swing is the legal/regulatory charge and opex.
3. **Rides growth decelerated to +11.4%** from +14.7% in Q3-25.

A $1B buyback authorization announced in the same release did **not** offset it.

**Trough 2026-03-30 at $12.46** — a drift, no single event; the AV news cycle and the broad tape.
**Q1-26 print 2026-05-07** produced **no move >8%** — the market took it neutrally.
**Recovery to $16.38** over the following three months.

**Verdict on cause: fully read.** One print, one charge, one deceleration. Nothing unknown.

---

## 2. MODE B — first principles, no promoter framing (lead)

### B-1. The 19% Gross Bookings headline decomposes to ~8.5pp volume + ~9.5pp price/mix

From Lyft's own metric tables (Q4-25 and Q1-26 EX-99.1):

| | Q1-25 | Q2-25 | Q3-25 | Q4-25 | Q1-26 |
|---|---|---|---|---|---|
| Rides (M) | 218.4 | 234.8* | 248.8 | 243.5 | **236.9** |
| Rides y/y | +16.2% | +14.5% | +14.7% | +11.4% | **+8.5%** |
| Gross Bookings ($M) | 4,162.4 | — | 4,780.4 | 5,074.2 | **4,946.0** |
| Bookings y/y | — | — | — | +18.6% | **+18.8%** |
| Active Riders (M) | 24.2 | — | 28.7 | 29.2 | **28.3** |
| **Rides per Active Rider** | **9.02** | — | 8.67 | 8.34 | **8.37** |
| **Rides/AR y/y** | — | — | — | — | **−7.3%** |

\*Q2-25 derived: FY25 945.5 − 218.4 − 248.8 − 243.5.

**Three things follow that Lyft does not print:**

1. **Rides growth has more than halved in five quarters: +16.2% → +8.5%.** Rides is the unit of consumption; Gross Bookings is rides × price/mix. Of the +18.8% bookings growth in Q1-26, **only ~8.5pp is volume; ~9.5pp is price and mix** — US fare increases plus the European taxi mix from FreeNow (closed Jul-2025) and Gett UK (closed ~May-2026), where fares per ride are structurally higher.
2. **Engagement is falling: rides per Active Rider is −7.3% y/y.** Lyft headlines *"Active Riders growth of 17% year over year"* — the metric that acquisitions and low-frequency new cohorts inflate — and never the ratio, which is the metric that says the incremental rider is worth less.
3. **They are paying for those riders.** Q1-26 income statement: **Sales & marketing $272.9M vs $182.0M = +50.0% y/y** on revenue +13.8%. S&M as a share of Gross Bookings went **4.4% → 5.5%, +110bps**. G&A +25.5%. That is why `OperatingIncomeLoss` is still **−$5.3M** in Q1-26.

**The synthesis:** *Active Riders +17%, Gross Bookings +19%* is a true statement whose components are decelerating volume, rising price/mix, falling frequency, and a 50% increase in customer-acquisition spend. **The reported metric improves because price/mix and M&A improve, not because the core does.** This is the LYFT analogue of the take-rate/GSV divergence, and it is the finding.

**Isolating M&A:** FreeNow closed 2025-07-31 (`GoodwillAcquiredDuringPeriod` FY25 = $181.7M, consistent with a ~$200M purchase). Q3-25 rides growth was +14.7% **with** two months of FreeNow vs +14.5% in Q2-25 **without** — so FreeNow's ride contribution is modest, roughly 4-6M/qtr. Backing it out, **organic rides growth in Q1-26 is ~+6%**, down from ~+15% a year earlier. Gett UK closed after quarter-end and will inflate Q2-26's Active Riders and Bookings without adding proportionate rides — **read Q2-26 rides, not Q2-26 bookings.**

### B-2. "All-time-high free cash flow of $1.1 billion" is 62% non-earnings

Lyft's Q1-26 release: *"generating over $1 billion in cash for the trailing twelve months… free cash flow was $1.1 billion, an all-time high."* Decomposing TTM operating cash flow of ~$1,189M from primary:

| Component | Amount | Share of OCF | What it is |
|---|---|---|---|
| **Insurance-reserve build** | **+$421.5M** | **35%** | `AccruedInsuranceCurrent` 3/31/25 $1,823.5M → 3/31/26 $2,245.0M. Premiums collected now against claims paid later — **float, i.e. a liability that gets paid, not profit.** |
| **SBC add-back** | ~$316M | 27% | `ShareBasedCompensation` FY25 $322.3M; Q1-26 $86.9M. A real economic cost. |
| Residual (true operating cash) | ~$450M | 38% | |

Less capex (~$50-80M): **cash earnings ex-float, ex-SBC ≈ $380-400M, not $1.1B.**

**The honesty question this raises is real and it is about capital allocation, not about the disclosure of any single number.** Lyft has now repurchased **$500.0M in FY25 plus $300.0M in Q1-26 = $800M** (`PaymentsForRepurchaseOfCommonStock`) and has authorized $1B more — funded, in a mechanical sense, out of a cash balance that is 35% insurance float. And the float is thinly collateralised:

| 3/31/2026 | $M |
|---|---|
| Insurance reserves (current) | **2,245.0** |
| Restricted cash & equivalents | 792.5 |
| Restricted investments | 1,205.8 |
| **Restricted assets total** | **1,998.3** |
| **Gap** | **−246.7** |

The gap is not widening fast (reserves +$64.6M in Q1-26 vs restricted assets +$62.2M), so this is a **thin buffer, not a deteriorating one**. But it is the reason the next item matters so much.

### B-3. NEW — the mass-tort docket against Lyft is accelerating right now, three days before the print

CourtListener RECAP federal-docket screen, `"Lyft, Inc."` as defendant, by period:

| Window | "v. Lyft, Inc." captions on page 1 | N.D. Cal. share |
|---|---|---|
| 2025 H1 | 3 | 0 |
| 2025 H2 | 2 | 0 |
| 2026 Q1 | 12 | 6 |
| 2026 Q2 | 11 | 5 |
| **2026-07-01 → 08-03 (34 days)** | **14** | **13** |

The July captions are **anonymised**: `JANE SL110 v. Lyft, Inc.` (3:26-cv-07604), `S. v. Lyft, Inc.` (×2), `H. v. Lyft, Inc.`, `B. v. Lyft, Inc.`, `C. v. Lyft, Inc.`, `M. v. Lyft, Inc.` — initials-only and Doe pleadings, filed in Lyft's home district, with a **sequential plaintiff-numbering convention ("SL110")** that is the signature of coordinated aggregate litigation, not scattered individual suits.

**Tie it to the balance sheet:** Lyft carries `LossContingencyAccrualCarryingValueCurrent` = **$211.6M** at 12/31/25, and has already taken a **$168M contra-revenue charge** for *"legal, tax, and regulatory reserve changes and settlements"* — the charge that cost the stock 17%. The filing rate against that accrual has risen roughly **eight-fold** in the last five weeks.

**This is the most likely source of the next negative surprise, it is un-narrated by the sell side, and the print is in three days.** It is also the item that makes the thin insurance-reserve collateralisation in §B-2 matter: the same reserve pool funding the buyback is the pool this docket is aimed at.

*Caveat, stated plainly:* these are page-1 API counts, not an exhaustive census, and RECAP coverage is incomplete. **The direction and the concentration are solid; the levels are floors.**

### B-4. The AV axis — courting it for symmetry with the house's UBER pack

The house's frozen UBER pack (2026-07-30, court 5.5/10, WAIT) armed **bar 3: "NO new AV-partner defection disclosure,"** on the back of the finding that **Waymo's exclusivity with Uber ended in Atlanta and Austin on 2026-07-24** (cars stay on Uber through May-2028). The symmetric question for the #2 is not "does Lyft lose a partner" — it is **"is anything Lyft calls an AV win actually differentiated?"**

**Finding: Lyft's marketed AV wins are non-exclusive, and one of them is shared with Uber in the same city.**
Lyft's Q1-26 release highlights *"Confirmed our first Baidu vehicles have been secured in the UK."* On **2026-07-29, Baidu-backed Apollo Go began London autonomous testing "following Lyft, Uber deals"** — **Uber holds the same partner in the same city.** Whatever Apollo Go's UK entry is worth, it is not a Lyft advantage; it is a Lyft *parity*.

Lyft's genuinely differentiated AV asset is **Flexdrive** — depot, charging, cleaning and fleet operations, opening in **Nashville this fall**. That is a real asset (Lyft is the only US rideshare player that owns fleet management at scale) and it is the one leg of the AV story that a Waymo-goes-direct world does *not* automatically destroy — an AV owner still needs depots.

**The #2 asymmetry, quantified — this is the mechanism, not a vibe.**
Lyft's adjusted EBITDA is **2.7% of Gross Bookings** (Q1-26: $132.8M on $4,946.0M); Q2-26 is guided to 3.0-3.3%. Uber's rate is roughly 2.5-3× that. Two consequences:

1. **There is no margin buffer.** Contribution margin in rideshare is concentrated in dense, high-utilisation metros — exactly the metros an AV network enters first. A 10% loss of bookings concentrated in Lyft's top AV-exposed metros removes **far more than 10% of EBITDA**, because those bookings carry above-average contribution and the fixed cost base does not shrink with them. At a 2.7% take of bookings, operating leverage runs in reverse violently. *This — not share loss per se — is the mechanism by which "AV kills #2 first" is true.*
2. **There is nowhere to dilute it.** Lyft is US/Canada plus a new European taxi footprint. Waymo's US metro expansion addresses essentially 100% of Lyft's core; Uber has 70+ countries over which to spread the same shock.

**Is it priced?** LYFT at ~7.9× EV/FY26E adj EBITDA against Uber at ~13-14× is a ~43% discount — which is approximately Lyft's *historical* discount to Uber. **The market is therefore not pricing an AV-specific #2 penalty beyond the ordinary quality discount.** The −35% drawdown was caused by a legal charge and a rides deceleration, not by AV. **The AV-existential risk is, on this evidence, unpriced.** That is the single most important sentence in this file for anyone tempted by the bounce.

### B-5. "Buyback authorization vs the FreeNow acquisition" — the premise as framed is REFUTED

The tension does not exist at the scale implied. `GoodwillAcquiredDuringPeriod` FY25 = **$181.7M** (all acquisitions), consistent with a FreeNow purchase price around **$200M**; Gett UK is smaller and undisclosed. Against that: **$800M of buybacks already executed** (FY25 $500.0M + Q1-26 $300.0M) and **$1B newly authorized**. M&A is roughly **one-fifth of a single year's repurchase.** It is not competing for capital.

**And the buyback is not cosmetic.** Class A shares outstanding went **400,856k → 382,531k in Q1-26 alone (−4.6%)**, now ~379.7M; additional paid-in capital fell $250.8M net of an $86.9M SBC credit. FY25 SBC of $322.3M against $500.0M of repurchase means FY25's buyback was ~64% dilution-offset — but **Q1-26's $300M against $86.9M of SBC was overwhelmingly net retirement.** If sustained at even half that pace, the share count shrinks ~10%/yr. **This is the strongest, most verifiable bull leg on the name and it is underweighted in the bear framing.**

**The real capital-allocation tension is different, and the court should name it correctly:** it is **buyback vs AV capex** (Flexdrive depots are capital-hungry and are the one credible AV defence) and **buyback vs insurance-reserve adequacy** (§B-2's −$247M gap and §B-3's accelerating docket). Not buyback vs M&A.

---

## 3. MODE A — claim verification

| # | Claim | Method / source | Result | Finding |
|---|---|---|---|---|
| 1 | "−35% from own 3y high" (queue) | IBKR daily bars | 52w high $25.54 (2025-11-12); $16.38/$25.54 = **−35.9%** | **CONFIRMED** |
| 2 | "rev3y 15.5%" | XBRL, CIK 1759509 | FY25 `Revenues` $6,316.3M vs FY24 $5,786.0M = +9.2%; Q1-26 +13.8% y/y | **CONFIRMED directionally**; note the tag switch (`Revenues` vs `RevenueFromContractWithCustomer`) — use `Revenues` for comparability |
| 3 | "finally FCF-positive" | 8-K EX-99.1; XBRL `NetCashProvidedByUsedInOperatingActivities` | FY25 OCF $1,168.4M, FCF $1,115.6M; TTM FCF $1.1B | **CONFIRMED at the cash level — but see §B-2: 35% is insurance float, 27% is SBC add-back** |
| 4 | "duopoly-#2 economics" / profitability | XBRL `OperatingIncomeLoss` | FY24 **−$118.9M**; FY25 **−$188.4M** (worse); Q1-26 **−$5.3M** | **GAAP OPERATING INCOME IS NEGATIVE AND FY25 WAS WORSE THAN FY24.** The profitability narrative rests entirely on adjusted EBITDA. |
| 5 | FY25 net income $2.8B | XBRL `IncomeTaxExpenseBenefit` FY25 = **−$2,897.3M** | Valuation-allowance release; pre-tax FY25 was a loss | **CONFIRMED as economically empty.** yfinance trailing P/E of 2.39 is an artefact — **do not use it.** |
| 6 | $1B buyback authorization | 8-K EX-99.1 2026-02-10; `PaymentsForRepurchaseOfCommonStock` | Authorized 2026-02-10; $500.0M executed FY25, $300.0M Q1-26; shares 400.9M → 382.5M (−4.6%) in Q1-26 | **CONFIRMED and material** |
| 7 | Net cash | 10-Q 3/31/26 balance sheet | Cash $1,034.9M + ST inv $686.1M = $1,721.0M unrestricted; LT debt $986.6M; **restricted $1,998.3M correctly EXCLUDED** | **Net cash +$734.4M → EV ≈ $5,485M. CONFIRMED.** |
| 8 | Insurance-cost cycle | `AccruedInsuranceCurrent`; restricted assets | Reserves $1,823.5M → $2,245.0M (+$421.5M/yr); restricted assets $1,998.3M → **−$247M gap** | **CONFIRMED — thin, not deteriorating** |
| 9 | Q2-26 print date | Motley Fool 2026-08-03 ("Uber Aug 5, Lyft Aug 6") + yfinance calendar; consistent with the Feb-10 / May-7 / Nov-5 cadence | **2026-08-06.** Consensus rev $1,806M, EPS $0.395 | **CONFIRMED (secondary ×2, cadence-consistent)**; no 8-K date filing obtainable |
| 10 | AV partner status | Google News RSS; Q1-26 EX-99.1 | Apollo Go began London testing 2026-07-29 *"following Lyft, Uber deals"*; May Mobility / Flexdrive Nashville opens this fall | **Lyft's Baidu UK "win" is NON-EXCLUSIVE — Uber holds the same partner in the same city.** |
| 11 | Board / governance | 8-Ks 2026-06-03, 2026-07-23 | Ben Minicucci (CEO, Alaska Air Group) added to the board 2026-07-23 — a genuine transportation-safety and operations appointment; charter cleaned up (Class B removed), PwC ratified | **CONFIRMED — a positive, and a plausible response to the safety/litigation exposure in §B-3** |

---

## 4. DE-RATE vs DERAILMENT — the ruling

Applying the queue's test literally:

- **On the reported metric, this is a DE-RATE.** Adjusted-EBITDA guidance has kept *rising* through the drawdown: FY25 $528.8M (from $382.4M), Q1-26 $132.8M (+25% y/y), **Q2-26 guided $160-180M vs $137.5M actual in Q2-25 = +16 to +31%**, with margin guided up to 3.0-3.3% of bookings from 2.6%. Gross Bookings guidance is +18-21%. The multiple compressed while management's numbers went up. That is the HUBS/CTSH/SAP signature.

- **On the underlying unit metric, this is an EARLY-STAGE DERAILMENT.** Rides growth +16.2% → **+8.5%**; rides per Active Rider **−7.3%**; S&M **+50%** to buy the growth; GAAP operating income **still negative and worse in FY25 than FY24**. The metric that is rising is adjusted; the metrics that are falling are the ones that determine whether the adjusted metric can keep rising.

**Direct estimate-revision test — and it fires.** Applying the test proposed by the parallel lane in `_GATE_TEST_GUIDE_DECEL.md` (consensus FY+1 EPS down >3% over the trailing 90 days; source `yfinance eps_trend`):

| Consensus, 90-day change | LYFT |
|---|---|
| Current quarter EPS | **−8.6%** |
| Next quarter EPS | **−9.4%** |
| **FY26 EPS** | **−13.0%** |
| FY27 EPS | **−3.2%** |
| **DERAIL flag** | **FIRES** |

**This upgrades the derailment side of the ruling and it is the single most damaging fact for an entry here.** I wrote above that management's adjusted-EBITDA guidance kept rising — that is true and verified. But **the sell side has cut FY26 GAAP EPS by 13% over the same 90 days.** Estimates are not stable; they are falling, and falling hard, while the company's *adjusted* number rises. That divergence is itself the §B-1/§B-2 finding restated by a third party: **the adjusted line is rising precisely because it excludes what is deteriorating** (the legal/regulatory reserve line, SBC, and the operating loss).

**And it collides with the path.** Over the same 90-day window in which FY26 consensus EPS fell 13%, **the stock rose from roughly $13.50 to $16.38.** Price and estimates moved in opposite directions over an identical window. That is the worst possible combination for a new position, and it converts the PATH CHECK from "late" into "late *and* unsupported."

**The ruling is that both are true and the distinction is the whole investment question.** If rides growth stabilises high-single-digit, the de-rate reading wins and the stock is cheap. If rides growth continues to halve every four quarters while S&M keeps climbing, the adjusted-EBITDA line follows within two to three quarters and the de-rate becomes the derailment. **Q2-26 rides, printing in three days, is the discriminating observation.** That is why this is print-conditional and not an entry.

---

## 5. AI-COMPLEX conflict

`ai_complex: false` in the queue, and that is **correct** — Lyft has no AI-capex exposure, no compute purchases, no dependence on the frozen **AI-BREAK | 2027-12-31 @ p=0.45** call. Neither the long nor the short requires the AI capex cycle to hold or break.

The honest nuance: **autonomy is not the AI-capex cycle.** Waymo's expansion is funded by Alphabet's operating cash flow and would survive an AI-capex break comfortably; a broad AI-capex break might even *accelerate* AV deployment by cheapening compute and redirecting capital toward the applications that work. **So the AV risk to LYFT is largely orthogonal to AI-BREAK and must be sized independently.** Do not net it against the household's ~$5.2M / 26% AI-complex exposure in either direction.

---

## 6. Four-idea frame

1. **The consensus long:** "#2 in a rational duopoly, finally FCF-positive at $1.1B, 7.9× EBITDA with $734M net cash, buying back 4.6% of the shares in a quarter." Every clause is verified true. It fails on quality-of-cash — 62% of the FCF is float and SBC add-back — and on the unpriced AV tail.
2. **The consensus short:** "Waymo eats rideshare." Correct in direction, useless in timing, and the drawdown to date was caused by a legal charge, not by AV. Shorting it here means paying 69% IV to wait years for a slow secular process.
3. **Our Mode-B read (the differentiated one):** the marketed takeaway (*Active Riders +17%, Bookings +19%, record FCF*) is composed of decelerating volume, rising price/mix, **falling frequency (−7.3%)**, and **+50% customer-acquisition spend** — while the FCF that funds the buyback is 35% insurance float sitting **$247M short of its restricted collateral**, aimed at by a federal docket whose filing rate against Lyft rose roughly **eight-fold in the last five weeks.**
4. **The genuinely underweighted bull leg:** the buyback is real, large and accelerating — 400.9M → 379.7M shares in five months. At a sustained pace this is a ~10%/yr share shrink at 7.9× EBITDA. If rides merely stabilise, per-share compounding does the work without any re-rating. **This is why the score is 4 and not 2.**

---

## 7. Catalyst map — probability × timing × magnitude

| Catalyst | Date | p | Magnitude | Leading indicator |
|---|---|---|---|---|
| **Q2-26 print** | **2026-08-06 AMC** | 1.00 | **±11.3% implied**; last print realized −17.0% | 68.8% IV; Aug-7 $16.5 straddle |
| **Rides growth prints <10% y/y** | 2026-08-06 | **0.72** | −8% to −15% | Q1-26 already +8.5%; Gett UK inflates riders, not rides |
| New legal/regulatory reserve charge | 2026-08-06 | 0.35 | −10% to −18% | §B-3 docket velocity; loss-contingency accrual >$260M |
| S&M >5.5% of bookings again | 2026-08-06 | 0.55 | −5% | Q1-26 was 5.5%, up 110bps |
| Buyback ≥$250M executed in Q2 | 2026-08-06 | 0.65 | +4% to +8% | Q1-26 pace was $300M |
| **Uber prints first (Aug-5) and sets the read-across** | **2026-08-05** | 1.00 | ±5% sympathy **before Lyft reports** | The house's UBER pack bars — Mobility GB ≥+13% cc |
| New Waymo US metro launch in a Lyft core market | rolling, H2-26 | 0.55 | −6% to −12% | Waymo announcements |
| Flexdrive Nashville AV opens | "this fall" 2026 | 0.80 | +3% to +6% | Company confirmation |
| Mass-tort coordination order (MDL/JCCP-style consolidation) | H2-26 to 2027 | 0.40 | −10% to −20% | N.D. Cal. filing velocity; JPML activity |
| FY27 target reaffirmation | Q3/Q4-26 | 0.60 | +5% | "on track with 2027 targets" language |

---

## 8. Scenarios (FY2028 exit)

*(Weights below are the post-amendment set: the §4 estimate-revision test — FY26 consensus EPS −13.0% over 90 days while the stock rallied 21% — moved 4pp from base/bull into bear. The pre-amendment set was 0.38/0.44/0.18 for E[FV] $17.84 / +8.9%.)*

| | p | FV | Reasoning |
|---|---|---|---|
| **Bear** | **0.42** | **$7.00** | AV takes 15-20% of Lyft's top-10 US metro bookings by 2028; rides growth reaches zero and S&M cannot be cut without accelerating the loss; at a 2.7-3% take of bookings the reverse operating leverage takes adj EBITDA below $600M and falling; a coordinated mass-tort resolution of $400-700M consumes one to two years of buyback; multiple to 4-5×. |
| **Base** | **0.42** | **$21.00** | Rides growth settles +6-8%; bookings +12-14% on price/mix and Europe; adj EBITDA ~$950M-1.0B by 2028; buyback retires ~7%/yr to ~330M shares; 7-8× EV/EBITDA. Note this is ~10% above the Street's mean target ($19.03, 36 analysts) on a 24-month-longer horizon — deliberately not the conservative-reflex answer. |
| **Bull** | **0.16** | **$33.00** | Lyft becomes the neutral AV aggregation + fleet-operations layer; Flexdrive scales into a real third business; Europe compounds; adj EBITDA $1.3B in 2028 at 9-10×; buyback accelerates into a re-rating. |

**E[FV] = 0.42(7.00) + 0.42(21.00) + 0.16(33.00) = $17.04**
**Spot $16.38 → edge +4.0% / +$0.66.**

**Market-implied cross-check:** holding bull at 0.16, spot $16.38 implies **p(bear) ≈ 0.44** against my 0.42 — a **2pp gap**. **The market and this court agree to within noise.** That is the honest result and it is what "RISK_PREMIUM, no edge claim" means in its strongest form: **+4.0% expected edge against 68.8% annualised IV and an ±11.3% binary in three days is nothing.**

**Two process notes worth banking, because both are failure modes the discipline exists to catch:**
1. An earlier pass produced a **+27.5% "edge"** purely by using a $9.50 bear and a $23 base. Widening the bear to the honest AV-loss case and trimming the base collapsed it to +8.9%. Conservative-sounding scenario values are where fake edge hides.
2. The §4 estimate-revision test then moved a further 4pp into the bear and took it to **+4.0%**. **The edge was never there; it was an artefact of scenario construction, and two independent disciplines each removed roughly half of it.**

---

## 9. RULING, band, tranche, kills

**4/10 — PRINT-CONDITIONAL WATCH. NO ENTRY at $16.38.**

Three independent reasons not to buy here, any one of which is sufficient:
1. **Path** — +31.5% off a 126-day-old low, 0.8% under the 3-month high. Worst entry geometry in the cycle.
2. **Print** — ±11.3% implied in three days; the contract forbids blind entry inside two weeks of a print, and the last print was −17.0%.
3. **Edge** — **+4.0%** expected against 68.8% IV. There is nothing to be paid for.
4. **Estimates falling into a rising price** — FY26 consensus EPS **−13.0%** over the same 90 days in which the stock rallied ~21%. Buying that divergence is buying the wrong side of it.

**Entry band if and only if the print resets the price:** **$12.50 - $14.00** — the fresh-low zone, which is where the risk premium is actually paid. Limit-only.
**Size:** **0.4-0.5% of the $3.3M deployable ($13-17k), starter tranche only.** The contract directs red-team survivors toward the upper half of the ruled range; **this is a 4/10 and not a survivor**, so it sits at the bottom of the range by design. A second tranche only after a print that clears the bars below, never averaged into on price alone.

**PRINT BARS — 2026-08-06 AMC. Entry requires ALL FIVE:**
1. **Rides ≥ 253.6M (+8.0% y/y vs Q2-25 234.8M)** — the volume deceleration must stop. *This is the discriminating bar.*
2. **Rides per Active Rider down no more than 5% y/y** — engagement, not bought riders. (Gett UK closed in-quarter and will inflate Active Riders; this ratio is the only defence against that.)
3. **NO new legal/regulatory contra-revenue charge, and the loss-contingency accrual ≤ ~$260M.**
4. **S&M ≤ 5.5% of Gross Bookings** — customer-acquisition cost must stop climbing.
5. **≥$200M of Q2 repurchase executed and shares ≤ 372M.**

**KILL TRIGGERS if owned:**
- Rides growth prints below +5% y/y in any quarter.
- A second legal/regulatory contra-revenue charge, or a coordinated mass-tort consolidation order.
- Insurance reserves exceed restricted assets by more than $400M.
- Adjusted EBITDA margin on Gross Bookings falls below 2.5% for two consecutive quarters.
- A Waymo direct launch in two or more additional Lyft top-10 US metros within any six-month window.
- Buyback suspended or slowed below $150M/quarter while shares are below $18.

**FREEZABLE CALL — LYFT | 2026-08-06 | *Q2-26 Rides growth prints below +10.0% y/y (rides < 258.3M vs Q2-25 234.8M)* | our_p = 0.72.**

**Cross-lane note for the principal:** the house's UBER pack is WAIT with an Aug-5 BMO print and four bars. **Uber reports the day before Lyft.** The two courts share three of their five bars in substance (volume growth, insurance accrual, AV-partner status). If the desk ever runs both, they are one AV-axis exposure and must share a cap — do not size them independently.

---

## 10. Verification notes and gaps (UNVERIFIABLE ≠ clean)

**Primary sources used:** SEC EDGAR CIK 0001759509 — 10-Q `lyft-20260331.htm` (2026-05-08); 10-K `lyft-20251231.htm` (2026-02-11); 8-K EX-99.1 Q1-26 (`lyft-20260331xpressrelease.htm`) and Q4-25 (`lyft-2025x12x31pressreleas.htm`); 8-Ks dated 2026-06-03 and 2026-07-23. XBRL `companyfacts` API. IBKR daily bars, snapshots, option chain. CourtListener RECAP v4. Google News RSS. House prior art: `desk/data/edge_classifications/UBER.json` (2026-07-30).

**Gaps — explicitly not clean:**
1. **The §B-3 docket counts are page-1 API results, not an exhaustive census,** and RECAP coverage of newly-filed dockets is incomplete. Nature-of-suit codes could not be retrieved for the individual N.D. Cal. cases (the docket endpoint returned empty for 3:26-cv-07604). **The characterisation of these as coordinated mass-tort filings rests on the caption convention ("JANE SL110", initials-only, single district, sequential numbering) — strong circumstantial inference, not a read complaint.** This is the top unverifiable in the file and it is load-bearing for the bear.
2. **Q2-26 print date (2026-08-06)** rests on two secondary sources plus cadence; no 8-K or IR primary obtainable.
3. **Q2-25 rides (234.8M) is derived**, not directly disclosed (FY25 945.5 less the three disclosed quarters). The freezable call's threshold depends on it.
4. **FreeNow's and Gett UK's separate ride/bookings contribution is not disclosed.** The ~4-6M/qtr FreeNow estimate is inferred from the Q2-25→Q3-25 growth-rate continuity and could be materially wrong; the organic-rides estimate inherits that error.
5. **Uber's EBITDA-to-bookings rate is stated from general knowledge, not recomputed** from Uber's filings in this court. The 2.5-3× relative statement should be re-derived before it is used in a sized decision.
6. **The straddle-implied move rests on closing marks with put open interest of 8** on the quoted line — directionally consistent with 68.8% IV over three days, but not a live two-sided quote.
7. **Whether the $168M Q4-25 charge is fully behind the company is unknown** — it was described as *"legal, tax, and regulatory reserve changes and settlements"* without itemisation, so the split between one-time settlement and ongoing reserve is not determinable from public filings.
8. **Insurance reserves noncurrent, if any, were not separately isolated** — the §B-2 float calculation uses `AccruedInsuranceCurrent` only, so the float share of OCF may be understated.
