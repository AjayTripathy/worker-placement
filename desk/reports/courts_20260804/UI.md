# UI — Ubiquiti Inc. — COURT_QUEUE_20260804 (Tier 1)

**Date:** 2026-08-03 (US evening; grades for the 08-04 session)
**Verdict: REJECT 3/10.** Not a de-rate of a good business — the unwind of a 4-month, news-free
melt-up. The business is genuinely excellent and genuinely intact; the price is not a discount.
**Red team: NOT required (score < 6).**
**Instrument: price gate. WATCH ≤ $415. Size today = 0%.**

---

## 0. Basis and cap structure (pulled BEFORE any EV claim)

| Item | Value | Source |
|---|---|---|
| Last | **$548.66** (`is_close: true`, 2026-08-03 close) | IBKR snapshot, conid 379198868, NYSE |
| Shares outstanding | 60,522,085 (as of 2026-05-07) | 10-Q FQ3-26 cover (dei) |
| Market cap | $33.21B | computed |
| Debt | **$0**. Term Loan fully repaid 2026-02-27; Revolving Facility $0 at maturity 2026-03-30. New PNC 2026 Revolver entered 2026-05-07, undrawn. | 10-Q Note 7 + Note 15 |
| Cash | $368.7M | 10-Q balance sheet |
| **Net cash** | **+$368.7M ($6.09/sh)** | computed |
| Converts / preferred / warrants | **none** | equity note; XBRL LongTermDebt = 0 |
| **EV** | **$32.84B** | computed |
| 52w high / low | $1,099.99 (intraday 2026-04-21) / $378.41 | IBKR misc_statistics |
| Dividend | $0.80/qtr ($3.20/yr), 0.58% yield, ~21% payout | 10-Q cash-flow ($145.2M 9M) |
| **Listed options at IBKR** | **NONE** (sections = STK, CFD, IOPT; `get_option_parameters` returns empty) | IBKR |

The last row is load-bearing: **we cannot hedge the August print and we get no implied-move read.**
In a name whose print-day history is −19.4% / +30.6% / +30% / −31%, "stock only, no protection" is a
sizing fact, not a footnote.

---

## 1. CAUSE-CHECK — what actually happened (tape-verified, every date from IBKR daily bars)

The screen says "−49% from own 3y high." The cause is not one event; it is four, and only two of
them are fundamental.

| Date | Close | Move | Cause | Grade |
|---|---|---|---|---|
| 2025-08-14 | 417.19 | **−13.9%** | no filing, no identified event | UNVERIFIABLE |
| 2025-08-22 | 510.23 | **+30.6%** | FY25 Q4 + 10-K (rev $759.1M, EPS $4.41) | CONFIRMED (8-K/10-K 08-22) |
| 2025-11-07 | 612.19 | **−19.4%** | FQ1-26 10-Q (rev $733.8M, **+33% y/y**) — sold off on a *beat* | CONFIRMED (10-Q 11-07) |
| 2026-01-27 | 548.99 | **+0.16%** | Hunterbrook: "The U.S. Tech Enabling Russia's Drone War" | CONFIRMED (Google News RSS) |
| 2026-02-06→10 | 548.24→712.38 | **+30.0% / 3 sessions** | FQ2-26 10-Q (rev $814.9M, **+35.8% y/y**, NI +70.8%) | CONFIRMED (10-Q 02-06) |
| 2026-02-10→04-21 | 712→**1,099.99** | **+54%** | **ZERO company filings in the window** (EDGAR: nothing between 02-06 and 05-08 except a Conflict-Minerals SD) | CONFIRMED-as-newsless |
| 2026-05-07→05-11 | 1,028.31→738.61 | **−28.2% / 3 sessions** | FQ3-26 10-Q (rev $788.2M, +19% y/y but **−3.3% q/q**) | CONFIRMED (10-Q 05-08) |
| 2026-07-29 | 522.87 | 52w-low close | slow bleed, no filing | — |

**The ruling on cause:** the drawdown decomposes into (a) a real growth-deceleration re-rate
(May print, ~−28%) and (b) the full round-trip of a **54% melt-up that contained no company
information at all**. Buying the −49% is mostly buying the unwind of a flow event in a 7%-float
stock, not a de-rating of a franchise.

**PATH CHECK:** spot $548.66 is **+5.0% off the 52w-low close ($522.87, 2026-07-29 — five sessions
ago)** and +5.7% off the 13w intraday low. This is *not* a late bounce. Path is clean; price is not.

**The one genuinely bullish tape fact:** $548.66 ≈ the 2026-02-05 close of $548.24 — i.e. the level
**immediately before** the two best quarters in company history were disclosed. TTM EPS since that
date has gone $13.08 → $15.57 (+19%) while the price is unchanged. That is real multiple compression
on rising earnings, and it is why this is a 3 and not a 1.

---

## 2. MODE B — leading, no promoter framing

### B1. Is `ai_complex: true` even correct? **NO on demand. The tag is wrong.**

| Test | Finding | Grade |
|---|---|---|
| Revenue mix | Enterprise Technology $717.9M = **91%** (UniFi APs/switches/cameras/access control, sold to prosumers/SMB); Service Provider (WISP airMAX/UISP) $70.3M = 9% **and shrinking −10.3% y/y** | CONFIRMED (10-Q revenue note) |
| Datacenter / AI-fabric product | none. No hyperscaler SKU, no 400/800G, no optics | CONFIRMED (product description, 10-Q Overview) |
| Customer concentration | "**no customers representing net revenues of 10% or greater**"; one customer at 10% of *AR* only | CONFIRMED (10-Q Note 12) |
| "AI" in the filing | appears exactly twice, both as **risk**: (i) incorporating AI into products/processes "may present business, compliance, and reputational risks"; (ii) AI-enabled cyberattacks | CONFIRMED (10-Q Item 1A) |
| Channel | 55% distributors / 45% own webstore; **no direct sales force** | CONFIRMED (10-Q Overview) |

There is no AI demand channel. The screen tagged it on "networking = AI adjacency," which is
category-matching, not analysis.

**But there IS a real AI-cycle linkage, and it runs the other way — on the COST side.** The 10-Q
names **Qualcomm and Broadcom as single-source chipset suppliers** and lists among supply risks
"*reservation of manufacturing capacity at our contract manufacturers by other companies, inside or
outside of our industry.*" AI capex is the thing reserving that capacity, and bidding for memory,
substrates and leading-edge wafers.

**Against the frozen house call AI-BREAK | 2027-12-31 @ 0.45:**
- Does the entry **require** the cycle holding? **No.** Zero revenue dependency on AI capex.
- Does the de-rate **already price** the break? **Irrelevant** — the de-rate is orthogonal to AI
  entirely. Do not credit UI with "AI already priced out"; nothing AI was ever priced in.
- **Direction of the conflict: UI is a modest AI-BREAK BENEFICIARY at the gross-margin line.** A
  break relieves component cost and lead-time pressure on a business already absorbing tariffs. The
  offset is generic: a disorderly break hits SMB IT budgets through the macro channel, which is beta,
  not AI-complex.
- **Portfolio fit:** against $5.2M / 26% household AI-complex exposure, UI is a genuine
  **diversifier**. This is the single strongest argument for the name and it is a *portfolio*
  argument, not a valuation one. It is not sufficient at this price.

**Correct tag: `ai_complex: false` (demand); `ai_cost_exposure: true`, sign = negative-to-AI-capex.**

### B2. The masking/signal structure — and why the honesty framework has no purchase here

Ubiquiti's disclosure surface is the smallest of any $33B US company I have courted:
**no guidance, no earnings call, no transcript, essentially no IR, four directors (three independent),
controlled company, 8-K and 10-Q filed the same morning.** Pera **93.0%** (56,278,181 of 60,499,655
— DEF 14A 2025-10-24 ownership table, CONFIRMED). Free float ≈ **4.21M shares ≈ 7.0% ≈ $2.31B**.

The instinct is "opacity = masking channel = hunt for divergence." **That instinct is wrong here,
and the anti-finding is worth banking.** There is no narrative layer to diverge *from*: the company
markets nothing, so there is no marketed takeaway to test against the data. The 10-Q's segment and
geography notes hit the tape **simultaneously with the headline**. Signal-to-price latency on the
print is **zero**. You cannot front-run a Ubiquiti print with disclosure analysis — the only
available edge is an external nowcast of the numbers themselves.

**Corroborating microstructure finding (this is the transferable one):** on 2026-01-27 Hunterbrook
published a full short-style investigation alleging Ubiquiti gear powers Russian battlefield comms
and drone operations in Ukraine — picked up by Investing.com, Yahoo Finance, NewsNation, theins.press
(2026-02-20). Tape response: **+0.16% that day, −0.42% the next.** A sanctions-evasion allegation
against a $33B company moved it 16 basis points. With 93% locked in one hand, **the marginal-seller
pool is too small for a bear thesis to transmit into price.** That cuts both ways and is the reason
the Feb–Apr +54% happened on nothing: in a 7% float, market cap is a scarcity price, not a valuation.

### B3. The forward signal a no-guidance company still leaks

With no guide, the **purchase-commitment line in the contingencies note is the only forward-looking
quantitative disclosure Ubiquiti makes.** Pulled from XBRL (`PurchaseObligation`):

| Quarter-end | Commitments $M | Coverage (÷ TTM COGS) |
|---|---|---|
| 2025-03-31 | 1,264.5 | 0.94 yr |
| 2025-06-30 | 1,295.1 (peak) | — |
| 2025-09-30 | 1,249.8 | — |
| 2025-12-31 | 1,263.8 | — |
| **2026-03-31** | **1,226.7 (−3.0% y/y)** | **0.73 yr** |

Revenue +29% over 9M FY26; the committed supply book is **flat-to-down in absolute dollars and down
from 3.4 to 2.9 quarters of coverage.** Two readings and I cannot separate them: (a) benign supply
normalisation after the 2022-23 shortage over-commit — supported by inventory falling $675.1M →
$654.0M on rising revenue; (b) management is not committing to more product because forward volume
isn't accelerating. **Grade: PLAUSIBLE, not CONFIRMED.** But it does not support acceleration, and
it is the best forward proxy that exists for this name. Made a tripwire.

### B4. The decisive finding — the August print faces a rigged EPS comp

Derived from audited XBRL, not disclosed by the company anywhere in narrative form:

| | FY2025 full year | 9M FY2025 | **implied FQ4-FY25 (Jun-25)** |
|---|---|---|---|
| Pre-tax income | $805.7M | $547.4M | **$258.3M** |
| Income tax expense | $93.7M | $102.2M | **−$8.5M (a BENEFIT)** |
| Effective rate | **11.6%** | 18.7% | **−3.3%** |
| Net income | $711.9M | $445.2M | **$266.8M** |
| Diluted EPS | $11.77 | $7.36 | **$4.41** |

Net income *exceeded* operating income in that quarter. At the company's ~19.4% run-rate tax, FQ4-25
EPS would have been **$3.44** — meaning **~$0.97/share (22%) of the reported $4.41 was a
non-recurring tax item.** With no press-release adjustment and no call, nothing flagged it. That
$4.41 is the comp the market will use on or about 2026-08-20.

**Consequence:** on my base case (FQ4-26 revenue ~$820M, +8.0% y/y; op margin ~36.5%; pre-tax ~$305M;
19.4% tax) FQ4-26 EPS ≈ **$4.02 — DOWN ~9% y/y on revenue UP ~8%.** In a stock with no call to
explain the tax comp and a habit of 20-30% print gaps, that is a dated, mechanical, identifiable
risk sitting **17–18 days ahead of us that we cannot hedge.**

*Honest counter (and the reason my freezable call is calibrated, not padded):* Ubiquiti trues its
annual tax up in Q4 **every** year — FQ4-24 rate 14.7% vs 18.6% 9M; FY22 14.8%; FY21 15.3%. FY25's
outright benefit was the extreme, not the pattern. A repeat 10-12% Q4 rate would put FQ4-26 EPS at
~$4.45 and the headline survives. This is why the call below is framed on *EPS growth vs revenue
growth*, which holds under both tax paths, rather than on an absolute EPS threshold.

---

## 3. MODE A — claim verification

| Claim | Method / authority | Result | Grade |
|---|---|---|---|
| "−49% from own 3y high, gm 46%, rev3y 15%" (screen) | IBKR bars; XBRL companyfacts | −50.1% from $1,099.99; TTM GM 46.0%; 3y revenue CAGR $1,940.5M(FY23)→~$3,157M(FY26E) = **17.6%** | CONFIRMED |
| Founder holds ~90%+ | DEF 14A 2025-10-24 ownership table | Pera 56,278,181 = **93.0%**; all D&O 93.1%; float ~4.21M sh | CONFIRMED |
| No guidance / no calls / minimal IR | EDGAR filing pattern: 8-K and 10-Q same day, no transcript-type exhibits, no interim 8-Ks; 4-person board; "no traditional direct sales force" | consistent in every period examined | PLAUSIBLE→ treated as true |
| Tariff / Vietnam-China exposure | 10-Q MD&A "Tariff and Trade Tensions" | Explicit: tariffs on China **and Vietnam**; "*the magnitude and scope of the recent changes have increased our product costs*"; "*our historical and current gross profit margins may not be indicative of… future periods*" | CONFIRMED |
| …yet margin is *rising* | XBRL: GM 26.2% (Mar-24) → 45.9% → 47.0% (Mar-26); op margin 36.9% | Full tariff pass-through achieved. Real pricing power. But it means part of "growth" is price. | CONFIRMED |
| Fiscal-Q4 print ~late Aug | FY25 8-K/10-K 2025-08-22; FY24 08-23; FY23 08-25 | **~2026-08-20/21, high confidence. 17–18 days out.** | CONFIRMED (pattern) |
| Growth intact | FQ1 +33.3% → FQ2 +35.8% → **FQ3 +18.7% y/y, and −3.3% q/q** | Sequential decline broke a streak: Dec→Mar was +10.7% q/q (FY25) and +6.0% (FY24). **First Q3 sequential decline on record in the window.** | CONFIRMED |
| Channel stuffing? | DSO = 28.4d (Mar-26) vs 30.4d (Mar-25); inventory $654.0M vs $675.1M on +19% revenue | **Clean.** Growth came with *falling* receivable days and *falling* inventory. Real sell-through. | CONFIRMED — no red flag |
| Earnings quality | TTM OCF ~$760M vs TTM NI $942M = **81% conversion**; TTM FCF ~$740M | Below 100%. Working-capital absorption. Worth naming: **FCF yield 2.2%**, P/FCF ~45x. | CONFIRMED |
| Buyback support | $500M authorised 2025-08-21, **expires 2026-09-30, $0 used** in FQ1/FQ2/FQ3 — including at $520 | No buyback bid under the stock at any price. FY23 and FY24 repurchases were also $0. | CONFIRMED (10-Q Note 13) |
| Insider distribution at the top? | Form 144 2026-05-13 + Form 4 2026-05-15 | **CFO Kevin Radigan, 500 shares (~$340k), RSU-related.** Pera sold nothing at $1,100. | CONFIRMED — clean |
| Hunterbrook Russia allegations addressed? | 10-Q filed 2026-05-08, 3½ months post-report: searched Russia / sanctions / export control | **Only the unchanged 2022-vintage boilerplate** ("monitoring… impact has not been material"). **No acknowledgment, no new risk factor, no disclosed inquiry, nothing in Legal Proceedings or Contingencies.** | **UNVERIFIABLE — the top gap** |

**On the last row, applying our own doctrine correctly:** I have *not* verified the Hunterbrook
allegations and cannot from primary sources here (the authority would be BIS/OFAC enforcement
actions). COTS networking gear reaching Russia via third-country resellers is an industry-wide
distribution-control problem (Cisco, TP-Link, Mikrotik all appear in the same teardowns), and
materiality turns on knowledge, which is not resolvable from filings. So this is **not** a REFUTED
claim and **not** an ELEVATE. But the 10-Q is the *only* venue this management has, and it used that
venue to say nothing. **UNVERIFIABLE ≠ clean.** It stays on the gap list and it is a live tail.

**Recall-floor connectors — dispatched and dispositioned (not skipped):**
- `customer_id` (whale): **no-fire, correctly.** 10-Q states no customer ≥10% of revenue. Nothing to resolve.
- `hiring_velocity` (plant ramp): **N/A.** Fully outsourced to contract manufacturers; no owned plant to read.
- `restaurant_ratings`: **N/A.** No brick-and-mortar unit roster.
- Customs/BOL nowcast: **attempted and rejected as a channel.** Ubiquiti's ~$1.7B TTM COGS split
  across Vietnam/China contract manufacturers is a low-single-digit share of HS-8517 flows dominated
  by consumer-electronics majors; the free consignee route (importyeti) is Cloudflare-blocked per our
  connector notes. **Signal-to-noise does not clear.** Bank it: *HS4-level customs data cannot nowcast
  a sub-$2B-COGS importer inside a mega-category.*

---

## 4. THE RULING — de-rate or derailment?

**Neither, and that is the finding. It is a flow unwind sitting on top of a real deceleration.**

The queue frame offers two boxes: multiple compressed on stable/rising estimates (HUBS/CTSH/SAP) vs
estimates falling and the multiple following. UI fits neither cleanly:

- **Estimates are not falling** — revenue +19% y/y, margins at an all-time record, zero debt, cash
  building, no dilution, no concentration. The business is arguably at peak health.
- **But the multiple never compressed to a discount.** TTM P/E history: ~43x (Aug-25), ~42x (Feb-25),
  ~78x (Apr-26 peak), **35.2x today.** Cheapest in a year — and still at the *high end* of the 25-35x
  band the stock occupied from 2018 through 2024. The "−49%" is measured from a four-month bubble
  that contained no information.
- **And the forward is mechanically hostile.** FY26 EPS ≈ $15.18 (+29%). FY27 growth has to be
  delivered against a base that already includes the tariff-price step-up, with y/y comparisons that
  collapse from +36% to single digits, and with the committed-supply book flat.

**A quality business is being offered at a fair-to-full price, not at a discount to its own history.**

### Scenarios (FY27, June-2027 fiscal year)

| | p | FY27 rev | op mgn | EPS | multiple | FV |
|---|---|---|---|---|---|---|
| **Bear** — flat revenue $3.15B, tariff/component squeeze takes GM to 43%, op margin 31%, market re-rates a decelerating controlled hardware co toward its Netgear/Cisco neighbours | 0.30 | $3.15B | 31% | $13.2 | 22x | **$300** |
| **Base** — +14% to $3.6B on continued UniFi share gain, op margin 35%, multiple settles at the middle of its own 2018-24 band | 0.45 | $3.60B | 35% | $17.0 | 30x | **$530** |
| **Bull** — +23% to $3.9B, ecosystem attach (cameras/access/cloud gateway) re-accelerates, op margin 37%, market re-pays for a 20%+ compounder | 0.25 | $3.90B | 37% | $19.7 | 38x | **$750** |

**E[FV] = $516. Spot $548.66. Edge = −6.0%.**

**Market-implied check (per the prob-weighted-FV doctrine):** holding p_base at 0.45, the tape's
$548.66 implies **p_bull ≈ 0.32** against our 0.25. The market is *more* bullish than we are on the
same scenario set. There is no positive edge to claim, and I am not going to manufacture one by
widening the bull case.

*Self-audit against the "conservative FV reflexes" note:* (1) am I anchoring a share-gainer to a
decelerating aggregate? Partly — I gave base +14% against a flat SMB networking market, which credits
real share gain; NA revenue +27% y/y supports it. (2) am I stripping the multiple to peer-or-below?
No — 30x base is a **~2x premium to Netgear (~15x) and Cisco (~16x)** and sits mid-band of UI's own
history. If anything the base multiple is generous for a name with 2.2% FCF yield and zero recurring
revenue (deferred revenue is de minimis — the company has no subscription line). I am comfortable.

---

## 5. Why 3/10 and not 4

**For (real, and why it is not a 1):** 36% operating margin and 46-47% gross margin in *hardware*;
zero debt and $369M net cash after retiring $1.09B; no dilution in five years (60.47M → 60.52M
shares); founder with 93% and no sales at the top; no customer concentration; DSO and inventory both
*improving* into a growth acceleration; full tariff pass-through demonstrated; and the stock at the
exact price it held before its two best quarters were known. **Genuine AI-complex diversification**
against a household already 26% AI-exposed.

**Against (and this is the majority):**
1. **Negative computed edge (−6%)**; market implies more bull than we hold.
2. **2.2% FCF yield, 45x P/FCF, 35x TTM P/E** — a full price, not an own-history discount.
3. **A dated adverse catalyst 17–18 days out** with a mechanically contaminated EPS comp, **which we
   cannot hedge** (no listed options at our broker) and cannot pre-position on (zero disclosure
   latency).
4. **The −49% is largely the unwind of a newsless +54%.** Nothing was de-rated; a scarcity price
   was.
5. **Governance permanently caps the multiple, and correctly so:** 93% founder control, controlled-
   company status, no guidance, no calls, three independent directors, a $500M buyback authorised and
   untouched at every price from $520 to $1,100. That discount should exist — it is not present here.
6. **Liquidity is a one-way door.** 4.21M-share float; $68M/day. A 1.2% position ($39.6M) is 0.6 days
   ADV and **1.7% of the entire float**. Entering is fine; exiting into a −30% print gap is not.
7. **Unresolved sanctions tail** with zero acknowledgment in the only venue management has.

The response-taxonomy rule applies cleanly: **this is a valuation finding, and valuation findings get
a price gate — not a size cut, not a tranche.**

---

## 6. Four-idea frame

1. **Long the common at $548.66 — REJECTED.** Negative edge, un-hedgeable dated catalyst, full multiple.
2. **Price-gate WATCH — the live idea.** Re-court at **≤ $415** (E[FV] $516 less a 20% margin of
   safety for the governance + float + no-hedge stack; independently, 24x FY27E $17.0 = $408). That
   level is not fantasy — the tape traded $378-405 in August 2025, within twelve months. **This is
   the standing instruction.**
3. **Post-print re-court, unconditional on price.** The August 20/21 print collapses the single
   largest uncertainty (does the sequential break persist?) and, uniquely for this name, does it
   *instantly and completely* — zero latency, everything in one document. If FQ4 revenue lands
   ≥ $860M with the seasonal pattern restored, the base case moves up and the name deserves a fresh
   court **even at a higher price.** The right posture is a calendar reminder, not an order.
4. **Do not express this as a short or a pair.** The Hunterbrook episode is the proof: a
   well-researched bear case in a 7%-float, 93%-founder-held name produced a **16bp** move. The float
   structure refuses to transmit negative information. Borrow would be scarce and the squeeze
   asymmetry is exactly wrong. *(This is the `conditioning_layer` lesson from the RCAT reversal,
   re-confirmed on a completely different mechanism — worth banking.)*

---

## 7. Catalyst map (probability × timing × magnitude)

| Catalyst | Date | p | Magnitude | Latency | Note |
|---|---|---|---|---|---|
| **FY26 Q4 + 10-K** | **~2026-08-20/21** (p 0.95 within 08-19…08-26) | 0.95 | **±15-30%**, direction ~coin-flip | **ZERO** | Print history: −19.4%, +30.6%, +30%/3d, −28%/3d. Un-hedgeable. |
| FQ4 revenue restores seasonality (≥$860M, +13.3% y/y) | same | 0.28 | +15-25% | zero | Requires reversing the FQ3 sequential break |
| FQ4 EPS growth < revenue growth (tax comp) | same | **0.78** | drives the bear tape | zero | **The freezable call** |
| $500M buyback used before expiry | by 2026-09-30 | 0.15 | **+10-20%** if used — it is 22% of the float, not 1.5% of the cap | days | $0 used in 4 quarters and in FY23/FY24. Low p, high convexity. Watch the FY26 10-K Item 5 table. |
| Buyback re-authorised/expanded at the 10-K | ~2026-08-21 | 0.55 | +3-6% | zero | Routine; only matters if paired with actual use |
| Take-private / squeeze-out by Pera | 24 months | 0.10-0.15 | +25-50% | months | Rational: 93% held, zero debt, ~$740M FCF, $2.3B float. Lowball risk cuts the other way. |
| BIS/OFAC/EU export-control action | 12 months | ~0.10 | **−15 to −30%** + a structural EMEA hit (39% of revenue) | weeks | Nothing disclosed as of the 2026-05-08 10-Q |
| Component cost relief from an AI-capex break | by 2027-12-31 | 0.45 (house) | +2-4pts GM | quarters | **UI benefits.** The only AI linkage that is real. |

**Dead-money check:** UI has fireable catalysts, so it is not dead money. It is *priced* money.

---

## 8. Freezable call

**`UI | 2026-08-31`** — **Bar:** Ubiquiti's fiscal-Q4-2026 (June-2026) reported **year-over-year
diluted EPS growth comes in BELOW its year-over-year revenue growth.**
**our_p = 0.78.**

**Mechanism (why this is a differentiated call, not a truism):** the year-ago quarter carried a net
tax *benefit* — FY2025 full-year tax expense $93.7M against 9M expense of $102.2M implies FQ4-FY25
tax of **−$8.5M** on $258.3M of pre-tax income, an FY effective rate of 11.6% against a 9M rate of
18.7%. Roughly $0.97 of the reported $4.41 was non-recurring. Nobody flagged it, because there is no
call and no adjusted-EPS press release. The call holds whether FY26-Q4 taxes at the 19.4% run rate
(EPS ≈ $4.02, down ~9% on revenue up ~8%) or repeats a low-double-digit Q4 true-up (EPS ≈ $4.45, up
~1% on revenue up ~8%). **It fails only if FY26-Q4 books an even larger tax benefit than FY25's
AND holds margin — the tail I am explicitly pricing at 0.22.**

---

## 9. Kill / re-entry triggers (dated)

**Kills (abandon the WATCH entirely):**
- **K1 — 2026-08-21:** FQ4-26 revenue prints **< $780M** (a second consecutive sequential decline).
  The deceleration is then a trend, not a comp artifact. Kill, do not buy the dip.
- **K2 — 2026-08-21:** TTM gross margin falls **below 44%** (from 46.0%). Tariff pass-through has
  failed; the entire margin story inverts.
- **K3 — any date:** purchase commitments fall **below $1.10B** (from $1,226.7M). The only forward
  signal the company emits turns negative.
- **K4 — any date:** a disclosed BIS/OFAC/EU inquiry, subpoena, or enforcement action, **or** any new
  Russia/export-control risk factor appearing in the FY26 10-K. Either confirms the tail is live.
- **K5 — any date:** Pera files a 144/4 for a material sale, **or** a going-private / tender proposal
  arrives below $600. Both are adverse to a minority holder here.

**Re-entry (converts WATCH to a live candidate):**
- **R1 — price:** trade at **≤ $415** with K1-K5 all clear.
- **R2 — fundamental, price-independent:** FQ4-26 revenue **≥ $860M** with gross margin ≥ 46% *and*
  purchase commitments back above $1.30B. Seasonality restored + forward book rebuilt = re-court at
  the then-prevailing price.
- **R3 — structural:** the $500M authorisation is actually used (≥$200M in a quarter). 22% of the
  float being retired changes the supply/demand of the security itself.

**If R1 or R2 fires:** starter **0.40%** of the deployable base, second tranche **+0.40%** only after
a *second* clean print, hard cap **0.80%** — below the 1.2% ruled cap and below the barbell's upper
half, because the float and the no-hedge constraint bind before conviction does.

---

## 10. Verification gaps (UNVERIFIABLE ≠ clean)

1. **Sell-side estimate trajectory — not obtained.** The queue's de-rate-vs-derailment test formally
   wants the consensus path; the WebSearch budget is exhausted and no estimate feed was reachable.
   **Mitigation:** the test was run on the *company's own* trajectory instead (revenue, margin,
   purchase commitments, sequential pattern), which for a no-guidance name with ~3 analysts is
   arguably the better instrument. But the gap is real and stated.
2. **Hunterbrook allegations — unverified in both directions.** No primary confirmation (no BIS/OFAC
   action found) and no primary refutation (company silent). Top gap.
3. **2025-08-14 −13.9% — cause never identified.** No filing, no headline located. A 14% single-day
   move in a $25B company with no discoverable cause is itself a float-structure datum.
4. **FQ4-FY25 tax benefit — magnitude confirmed, nature not.** The $8.5M credit is arithmetic from
   audited XBRL; *what* it was (excess stock-comp benefit, uncertain-tax-position release, valuation
   allowance) requires the FY25 10-K tax footnote, which was not read. Does not change the comp math.
5. **No implied-move read.** With no options chain, I cannot say whether the market has priced a
   ±20% August print. The scenarios are unconditioned by option-market information.

---

## 11. Knowledge-graph contributions (the durable output)

1. **Absence of a masking channel is a positive finding.** A company that markets nothing cannot
   produce takeaway-vs-data divergence. UI is the clean case: opacity without narrative → the
   honesty-alpha framework has **no purchase**, and the correct response is to say so rather than
   manufacture a flag. *(Extends `feedback_anti_masking_findings_have_value`.)*
2. **Float structure gates information transmission.** A researched sanctions-evasion allegation
   against a $33B issuer moved it **+0.16%**. Below roughly a 10% float with a single controlling
   holder, bear theses do not reach price — and neither do bull ones without a flow event. Add
   `float_pct` as a gate on any divergence-to-trade mapping, alongside `discovery_state`.
3. **Newsless melt-ups are identifiable in advance from EDGAR silence.** +54% over ten weeks with
   *zero* filings is a machine-checkable pattern (`price_move_pct` vs `filings_in_window == 0`) and it
   fully round-tripped. Worth building as a screen: **the "−X% from high" input to any value screen
   must be net of newsless run-ups**, or the screen manufactures fake discounts. **UI is the proof
   case: the screen scored it 87.7 on a −49% that was 100% flow.**
4. **The Q4 tax-true-up trap.** For June-FYE companies with a large Q4 annual tax true-up, the
   year-ago Q4 EPS comp can be silently inflated. Detectable purely from XBRL by differencing FY
   against 9M tax expense. Generalises to every FYE and is invisible in any screen that reads
   reported EPS. **Propose a detector: `q4_tax_trueup_comp` — fires when |FY rate − 9M rate| > 4pts.**
5. **Customs nowcast has a size floor.** HS4-level import data cannot resolve an importer whose COGS
   is low-single-digit percent of its category. Record the negative so the channel is not re-attempted.
6. **Correct the screen tag:** `ai_complex` must key off revenue/customer evidence, not sector
   adjacency. UI is AI-*cost*-exposed with the sign **negative to AI capex** — an AI-BREAK beneficiary
   at the margin line and a portfolio diversifier, which is the opposite of how it was queued.

---

*Prior art check: `research_ledger.json`, `resolution_packs.json`, `CATALYST_MISPRICING.json` —
zero prior UI/Ubiquiti records. No frozen call contradicted. Per the output contract, no shared store
was written by this lane.*
