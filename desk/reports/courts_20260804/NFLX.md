# NFLX — Netflix, Inc. | COURT_QUEUE_20260804, Tier 1
**Court date 2026-08-03 (grades for the 08-04 session). Verdict: RP_FAIR 5/10. No red team required.**

Live basis: **$73.53** — IBKR last, 2026-08-03 session, `is_close=false`, ts 1785820108, prior close
$73.33 (+0.27%). All price premises in this court are struck off IBKR daily bars + yfinance 3y closes
(the two agree to the cent on every close checked). Split-adjusted throughout: NFLX did a **10-for-1
split on 2025-11-17** (confirmed in the IBKR `corp_actions` payload) — every pre-split price quoted
here is post-split-adjusted.

---

## 1. CAUSE-CHECK — what actually happened (this is the whole job)

The queue's "-46% from own 3y high" is **tape-confirmed**: 3y closing high **$133.91 on 2025-06-30**,
now $73.53 = **−45.1%**. But the drawdown is not one event. It is four distinct legs, and three of
them have a named, primary-sourced cause. Reading it as a single "premier compounder broke" story is
the error the tape punishes.

| Leg | Dates | Move | Cause | Evidence | Status |
|---|---|---|---|---|---|
| **A. Q3'25 print** | 2025-10-22 | −10.1% in a day, 67M shares | Q3'25 operating margin collapsed to 28.2% from 34.1% in Q2'25 | 8-K 2025-10-21 (items 2.02/9.01); margin table in the Q2'26 letter | CONFIRMED |
| **B. WBD acquirer-overhang** | 2025-12-04 → 2026-02-12 | ~$104 → $75.86, **−27%** | Netflix signed to buy Warner Bros. Discovery's Streaming & Studios business; market repriced Netflix as a levered acquirer | 8-K 2025-12-05 (Item 1.01, Merger Agreement w/ WBD + Nightingale Sub + New Topco 25); 8-K 2025-12-22 (Item 2.03: bridge commitment, 2025 RCF, DDTL); A&R Merger Agreement 2026-01-19; 20 Form 425s; 14 DFAN14A solicitations Jan–Feb | CONFIRMED |
| **B′. Termination relief** | 2026-02-27 | **+13.8% in a day** | WBD terminated to take a Superior Proposal from PSKY (Paramount Skydance). **PSKY paid Netflix the $2,800,000,000 termination fee on WBD's behalf.** All bridge/RCF/DDTL commitments auto-terminated. | 8-K 2026-02-27, Item 1.02, verbatim | CONFIRMED |
| **C. Guide-down-on-beat, twice** | 2026-04-17 (−9.7%), 2026-07-17 (−7.3%, 105M shares) | ~$107 → $67.60 | **Both quarters BEAT. Both forward guides stepped the growth rate down.** | Q1'26 and Q2'26 shareholder letters (EX-99.1) — see §2 | CONFIRMED |
| **D. Beta bleed** | 2026-06-17 → 06-25 (incl. −5.8% on 06-22) | ~$82 → $73 | No 8-K, no 10-Q, no company event on or near 06-22. Contemporaneous coverage attributes it to a Nasdaq tech sell-off under a hawkish new Fed. | EDGAR filing index (nothing filed 06-05 → 07-16 except Form 4s); Google News RSS: "Netflix Stock Price Today Nears 52-Week Lows Amid Nasdaq Tech Sell-off" (06-17), "…Under a Hawkish New Fed" (06-15) | **PLAUSIBLE, not CONFIRMED** — top unverifiable item |

**The load-bearing cause is Leg C**, and its shape matters more than its size. Netflix did not miss.
It beat, and guided the growth rate down, twice:

- **Q1'26 (Apr 16):** revenue +16.2% (above forecast), OI +18% (above forecast), FY26 guide maintained
  — **and it guided Q2'26 to +13.5%**, a 2.7pp step down. Stock −9.7%.
- **Q2'26 (Jul 16):** revenue +13.4% (essentially in line, $12,560 vs $12,574 guided), OI $4,193 vs
  $4,105 guided (ahead), EPS $0.80 vs $0.78 guided (ahead) — **and it guided Q3'26 to +11.7%**, the
  first sub-12% quarter. Stock −7.3%, then to a fresh 52w low.

So: **the market is not repricing broken estimates. It is repricing the growth rate itself.** That
distinction is the entire de-rate-vs-derailment call and it is resolved in §3.

Two items the queue prompt asked about, resolved:
- **"Sub disclosure withdrawal aftermath"** — real, and it got a *second* instalment in the Q2'26
  letter. Treated properly in §4, because the honest reading is not the obvious one.
- **"Content-spend guide"** — NOT a cause. Cash content spend / amortisation ratio guided at ~1.1x
  and **reaffirmed unchanged** in both the Q1'26 and Q2'26 letters. Content amortisation guided to
  +~10% for 2026. Nothing here moved the stock.
- **"A competitor event"** — the competitor event was Netflix *losing* the WBD auction to Paramount
  Skydance, and the stock went **up 13.8%** on it. The market's revealed preference was emphatic:
  it did not want Netflix to own Warner Bros.

---

## 2. MODE A — claim verification against primaries

Rule: verdicts rest on CONFIRMED / REFUTED only. UNVERIFIABLE is listed, not waved through.

| # | Claim | Method / source | Result | Finding |
|---|---|---|---|---|
| 1 | "FY26 guidance is consistent with prior guidance" (Q2'26 letter) | Compare Q1'26 letter (EX-99.1, 2026-04-16) to Q2'26 letter (EX-99.1, 2026-07-16), verbatim | Q1'26: "We continue to project 2026 revenue of **$50.7–$51.7B** and an operating margin of **31.5%**." Q2'26: "we've narrowed our forecasted revenue range to **$51.0–$51.4B** and continue to forecast an operating margin of **31.5%**." Midpoint $51.2B **both times.** | **CONFIRMED.** A genuine narrow-within, not a stealth cut. This is the single strongest de-rate datum in the file. |
| 2 | "FY26 FCF of approximately $12.5B" | Q2'26 letter, cross-read to the Q1'26 letter where the guide was raised | Q1'26 letter, verbatim: "We now expect 2026 FCF of approximately $12.5B, **an increase from our previous projection of $11B due primarily to the after-tax impact of the Warner Bros.-related termination fee.**" | **CONFIRMED — and the headline number is not the number to value on.** Netflix's own **organic FY26 FCF guide is ~$11.0B.** The $12.5B is windfall-inflated. Anyone striking a FCF yield on $12.5B is 14% too generous. Netflix disclosed this itself, plainly, in the sentence that raised the guide. |
| 3 | Q2'26 FCF collapsed −33% YoY ($1,525M vs $2,267M) — is a cash-conversion break being hidden? | Q2'26 letter cash-flow section + 10-Q (2026-07-17) income-tax note | Letter: "This included higher cash tax payments **due in part to the Warner Bros. termination fee.**" 10-Q Note 11: 6-mo effective tax rate **18% vs 12%** in the prior-year 6-mo; 6-mo other income **$2,903.8M vs $90.5M** — the $2.8B fee sits in Other income in Q1 and its cash tax lands in Q2. | **CONFIRMED, and benign.** The Q2 FCF "collapse" is the tax bill on the Q1 windfall. Mechanically explained, primary-sourced, self-disclosed. Not a masking event. |
| 4 | Q1'26 net income $5,283M exceeded operating income $3,957M — one-timer? | XBRL companyfacts (CIK 0001065280) + 10-Q income statement | 6-mo other income $2,903.8M (prior year $90.5M). The $2.8B PSKY/WBD fee is below the operating line. | **CONFIRMED.** FY26 reported EPS is windfall-inflated by ~$0.51. Clean FY26 EPS ≈ **$3.07**, not the ~$3.58 reported. |
| 5 | Balance sheet / cap structure before any EV or yield claim | 10-Q 2026-06-30, balance sheet + Note on debt | Short-term debt **$2,483.8M** + long-term **$11,825.5M** = **$14,310M gross**; cash & equivalents $9.1B → **net debt ≈ $5.2B**. Shares issued & outstanding **4,163,939,676**; diluted weighted **4,261,300k**. Treasury 413.4M shares at cost $28.39B. | **CONFIRMED. Cap structure is pristine** — no preferred, no converts, no warrants, no pre-funded anything. EV = **$318.5B** at $73.53 on FD shares. |
| 6 | The July debt raise — distress, or routine? | 8-K 2026-07-22, Item 8.01 | $1.0B of **5.250% senior unsecured notes due 2036**, S-3ASR shelf (333-281071). Proceeds: "**for the repayment at maturity of its outstanding 4.375% Senior Notes due 2026**, and for general corporate purposes." | **CONFIRMED ROUTINE.** A same-size refi of a maturing bond, flagged in the Q2 letter a week earlier ("We have $1B of debt maturing later this year, which we plan to refinance"). Kills the "levering up into the fall" reading. |
| 7 | SBC honesty — is GAAP being flattered? | 10-Q, stock-based compensation note | Q2'26 SBC **$131M** on $12,560M revenue = **1.04% of revenue**; 6-mo $272M. | **CONFIRMED CLEAN.** ~1% of revenue against software peers at 8–15%. GAAP EPS *is* the economics here. No non-GAAP bridge to police. |
| 8 | Buyback capacity and pace | 8-K 2026-04-23 (Item 8.01) + Q2'26 letter | Board authorised **an additional $25B** on 2026-04-22 on top of $6.8B remaining. Q2'26: **$4.7B repurchased — largest quarter in company history**; $27.1B capacity remaining (**8.7% of market cap**). FD shares 4,349M → 4,261M YoY (**−2.0%**). | **CONFIRMED.** But see the disconfirming read in §4, finding B4 — this cuts both ways. |
| 9 | Content-cost race re-igniting? | 10-Q content-obligations note, vs 2025-12-31 | Total content obligations **$25.11B** (from $24.04B at YE25, +4.4%). Due <1yr $11.94B (from $11.53B). **Due 1–3yr $9.55B from $8.38B, +14.0%.** | **CONFIRMED STABLE in aggregate**, with one live thread: the 1–3yr bucket is building faster than the book, consistent with the NFL/MLB/WWE/boxing forward commitments. Watch item, not a flag, against $51B of revenue. |
| 10 | Governance — two board departures in 2026 | Q1'26 letter + 8-K 2026-04-16 (5.02); 8-K 2026-07-30 (5.02, event 2026-07-26) | Reed Hastings did not stand for re-election at the June AGM ("to focus on his philanthropy"). Anne Sweeney resigned from the board 2026-07-26 — "**not due to any disagreement with the Company.**" | **CONFIRMED, low signal.** Founder-chair exit is a real end-of-era marker; the Sweeney resignation ten days after a −7% print is worth *noting* but the boilerplate no-disagreement language is standard and there is no corroborating evidence. Not scored. |
| 11 | Prior art / doctrine conflicts | grep `desk/data/research_ledger.json`, `CALIBRATION.json`, `resolution_packs.json` | **No NFLX entry in the research ledger. No NFLX prediction in the calibration ledger** — the "NFLX-class megacaps were run as CONTROL predictions" prior in the queue prompt **is not borne out by the file**; there is no prior NFLX control art to respect or contradict. NFLX appears only in `parametric_holdings.json` (qty **0**) and `setup_drought_diagnosis_20260803.json` (as a screen output). | **No frozen call to contradict.** Clean slate. |
| 12 | **Cross-account wash-sale surface** | `desk/data/parametric_realized.json` | Parametric realised **15 NFLX loss lots totalling −$2,014.90, all closed 2026-07-06**, and the Parametric NFLX line is now **0**. | **CONFIRMED — actionable, and it changes the order date.** §1091 runs 30 days each way: the window closes **2026-08-05**. A fill on 08-04 or 08-05 disallows those losses. See §7. |

---

## 3. THE RULING — DE-RATE, with a real growth-rate reset inside it

The contract's test: *multiple compressed on stable/rising estimates* (de-rate — the HUBS/CTSH/SAP
winner pattern) *versus estimates falling with the multiple following* (derailment in growth costume).

**Estimates did not fall.** Verified across two consecutive prints from the primary letters (§2 #1):
FY26 revenue midpoint $51.2B both times, FY26 operating margin 31.5% both times, cash-content/amort
1.1x both times, FY26 organic FCF ~$11B both times. FY26 operating income is guided to **+20%+** and
margin to expand **200bps** (29.5% → 31.5%). Nothing in the guide broke.

**The multiple did fall, hard.** On clean FY26 EPS of ~$3.07:

| Metric | Value at $73.53 |
|---|---|
| Market cap (FD 4,261.3M sh) | $313.3B |
| EV (net debt $5.2B) | $318.5B |
| **P/E, FY26 clean (ex-$2.8B fee)** | **24.0x** |
| P/E, FY26 as reported | 20.5x |
| P/E, FY27E ($3.70) | 19.9x |
| EV/EBIT, FY26 ($16.1B) | 19.8x |
| **EV / FY26 organic FCF ($11.0B)** | **29.0x** |
| Organic FCF yield | 3.5% |
| NFLX's own 3y-high multiple (2025-06-30, $133.91 on FY25 EPS $2.52) | ~53x trailing |

**So: de-rate. But it is not a free de-rate, and this is where the court departs from the bull frame.**
The growth *rate* genuinely stepped down 5.9pp in three quarters — 17.6% (Q4'25) → 16.2% → 13.4% →
**11.7% guided**. A business decelerating from 17% to 12% revenue growth *should* carry a lower
multiple than one growing 17%. A large share of the 53x → 24x compression is **correct repricing,
not mispricing.** The claim on the table is only that the market has over-shot the correct new level
— and that is a much thinner claim than "premier compounder on sale."

The single most important number in the whole file is not in the headline table. It is regional:

| UCAN (43% of revenue, highest ARPU) | Q2'25 | Q3'25 | Q4'25 | Q1'26 | Q2'26 |
|---|---|---|---|---|---|
| Revenue growth Y/Y | 15% | 17% | 18% | 14% | **10%** |

UCAN grew **10% in a quarter that carried a US price increase** (partial-quarter, per the letter).
Strip the price effect and the core North American franchise is close to volume-flat. That is the
derailment-shaped fact hiding inside a de-rate-shaped guide, and it is the reason this court scores
5 and not 7.

---

## 4. MODE B — first principles, hunting disconfirmation

Run with no promoter framing: *what would have to be true for this to be a value trap, and does the
company's own data say it?*

**B1 — Growth has switched engines from volume to price, and the volume engine is stalled.**
Netflix's own letter: H1'26 view hours **+2%**, following **+1.5%** in 2025. Against a member base
"approaching 1B people" that the same letter says is still *growing*. Arithmetic consequence:
**hours per member are falling.** Revenue growth of 13.4% is therefore being carried by price and by
ads, not by usage. The letter names the drivers itself — "membership growth, pricing and increased
ad revenue" — and the price lever has finite headroom and elasticity risk. This is the strongest
bear fact in the file **and Netflix disclosed it in the third bullet of the letter.** Under the
honesty framework that makes it a *fundamental* risk, not a masking finding.

**B2 — Engagement disclosure is being withdrawn for the second time, and the timing is the tell.**
Netflix stopped reporting subscriber counts in 2025. In the Q2'26 letter it announced that the
*What We Watched* report — the last remaining external engagement metric — moves from **semi-annual
to annual beginning in 2027**, deliberately decoupled from earnings, with the stated rationale: "to
keep the focus on our primary financial metrics – revenue and operating profit."

The mechanism, encoded: **masking channel** = reduced disclosure *frequency* on the only metric that
lets an outsider decompose price-led growth from volume-led growth; **signal channel** = hours per
member; **signal-to-price latency** = the next engagement datapoint is the FY26 report in Q1'27, so
there is a **~9-month blind window** on the decisive variable, arriving after three more prints.
The announcement lands in the same letter as the slowest view-hours print and the sharpest revenue
deceleration. That co-timing is exactly the pattern the framework exists to catch.

**But the honest grade is REVIEW_FLAG, not ELEVATE, for two independent reasons.**
*(i)* The doctrine bar is **takeaway-vs-data divergence, not datum-disclosure.** Netflix printed the
+2%, printed the 17.6%→11.7% deceleration in its own table, printed the UCAN 10%, printed the FCF
decline with its cause, and named price as a growth driver. The letter's framing is promotional
("solid," "healthy"), but every number that contradicts the framing is on the page. Re-detecting
honestly disclosed bad news is not alpha.
*(ii)* **It is already priced.** Same-day CNBC: "Netflix stock falls as earnings forecast disappoints,
**company says it will give fewer engagement updates**"; Business Insider ran a piece specifically on
the disclosure change. The market discounted it inside one session. `discovery_state` on this name
is **CROWDED** on information — ~50 covering analysts, wall-to-wall coverage. There is no
informational edge here, only a possible positioning/valuation one.

**B3 — The de-rate is being driven by forward guides, twice, on beats. That is a repeatable pattern,
and Q3'26 sets up the same way.** Q3'26 is guided to +11.7% revenue and only **+2.4% sequential**
($12,560 → $12,860) in a quarter that carries the *full*-quarter UCAN price increase, a week-one NFL
game, two MLB events, and the strongest slate of the year. If the full-quarter price benefit only
buys 2.4% sequential, the underlying is softer than the headline. The mechanism that produced −9.7%
and −7.3% is intact into October.

**B4 — Management's own buying does not mark a floor.** Q1'26: 13.5M shares for $1.3B = **$96.30/sh**.
Q2'26: **$4.7B, the largest buyback quarter in company history**, executed across a quarter that
traded roughly $86–$107 — call it a high-$80s average. The stock is $73.53. Management's
largest-ever conviction purchase is **~15% above today's price and it did not hold.** The buyback is
a powerful mechanical bid (~$4.7B/qtr ≈ $75M/day ≈ 6%/yr of cap) but it is emphatically **not**
evidence that this level is the low.

**B5 — Where the AI axis actually cuts (queue flags this ai_complex:false; the court agrees, with a
correction).** NFLX is **AI-adjacent, not AI-levered**, and this deserves to be stated precisely
against the frozen house call **AI-BREAK | 2027-12-31 @ p=0.45**:
- **Does the entry REQUIRE the cycle holding? No.** Netflix has no AI capex, no datacentre build, no
  hyperscaler revenue dependency, no compute-SPV paper. Its FY26 guide contains nothing that breaks
  if AI capex stops. On *fundamentals* an AI-capex break is mildly **favourable** — cheaper GenAI
  production tooling, cheaper creative labour, and a consumer subscription that is defensive in a
  drawdown.
- **Does the de-rate already price the break? Not applicable in the usual sense** — this de-rate has
  a fully identified non-AI cause (§1 Leg C). But the **multiple is complex-correlated**: 24x does
  not survive an AI-BREAK beta event untouched; assume 18–20x on beta alone in that scenario. So
  NFLX is **neither a hostage nor a hedge** — cycle-neutral on fundamentals, cycle-correlated on
  multiple. Not averaged away: this is the honest split.
- **Portfolio-construction point, and it is the best argument in the file for owning this name at
  all:** the household already carries **~$5.2M / 26% AI-complex**. NFLX is one of very few
  large-cap growth exposures that **adds growth without adding to that concentration.** That is a
  real, non-alpha reason to own it.
- **The AI bear specific to NFLX is the slop/attention war, and B1 is its leading indicator.**
  View hours +2% while Netflix responds by buying *creators* (Ms. Rachel, Mark Rober, Danny Go!,
  the Stokes Twins), video podcasts, publisher deals (Condé Nast, Hearst, People) and cloud games —
  that is a company conceding its competitive front is **YouTube and short-form, not Disney+.**
  It is fighting an attention war whose supply curve AI is about to flatten.
- **The AI bull is real and quantified:** "In 2026, GenAI workflows have been used in **roughly 300**
  of our titles," concentrated in post-production, "higher quality output more quickly and at a
  lower cost." A specific, falsifiable number. Netflix's cost structure is un-unionised relative to
  legacy studios, so it captures this deflation faster than WBD/Paramount/Disney. This is the
  credible path to the 33–34% margin in the bull case.

**B6 — Anti-masking finding (positive, and worth cataloguing).** The places where a company under
this much pressure *would* normally hide are all clean: SBC at 1.0% of revenue (no non-GAAP bridge),
cap structure with zero contingent claims, the FCF-guide raise *self-labelled* as windfall-driven
rather than presented as organic strength, the Q2 OI beat *attributed by management to expense
timing* rather than claimed as strength, and the $2.8B fee booked transparently below the operating
line. **The absence of expected masking on the financials is itself a finding**: this is a company
telling the truth about a decelerating business, which is the CLEAN pattern, not the catch. The one
opacity vector is prospective and non-financial (B2).

---

## 5. PATH CHECK

| | |
|---|---|
| 52w closing high | $126.32 (2025-09-09) |
| 3y closing high | $133.91 (2025-06-30) |
| **52w closing low** | **$67.60 — 2026-07-20, 14 days ago** |
| 52w intraday low | $65.08 (2026-07-17) |
| Current vs closing low | **+8.8%** |
| 13w / 26w / 52w lows | **all $65.08 — they coincide** |
| YTD | −21.6% |
| Realised vol (30d, annualised) | **53.2%** |
| Implied vol (underlying, annualised) | **36.3%** |

**Reading: early in the path, not late.** The contract's warning case is a +35% bounce off a <90-day
low; this is **+8.8% off a 14-day-old low**, so the "you missed it" objection does not apply. The
opposite risk applies instead: the 13w, 26w and 52w lows are the *same print*, the low was made on a
105M-share earnings gap, and **no base has formed.** This is a downtrend with ten sessions of bounce
in it. Tranche accordingly — do not front-load.

One tape note worth flagging: **IV 36.3% against realised 53.2%.** The option market is not pricing
continuation of what this stock has actually been doing. That is an interesting dislocation, but it
is not our expression (see §6, idea 2).

---

## 6. FOUR-IDEA FRAME

**Idea 1 — the one we take: common stock, laddered, small.** 0.60% of the $3.3M deployable, three
equal tranches on GTC limits below spot. Rationale: de-rate verified from primaries, cap structure
pristine, earnings are real earnings, no AI-capex hostage, and the household needs non-AI growth
exposure. **No edge is claimed** — this is fairly-paid risk with a modest overlay (§8).

**Idea 2 — the one we decline: long premium.** IV 36% vs realised 53% is genuinely cheap convexity,
and a Jan-2027 call would express the "guide holds, multiple recovers" thesis with better convexity
than stock. **Declined** on two standing doctrines: this is the **taxable** book (option gains are
non-deferrable short-term ordinary income at ~50%+), and the deployment plan is
equities-for-max-TLH. Stock is the correct instrument. *Selling* premium is likewise barred in the
taxable book — no covered calls against this position, ever, and no cash-secured puts to enter.

**Idea 3 — the pair we do not put on: long NFLX / short PSKY.** Superficially attractive — Paramount
Skydance won the WBD auction that Netflix walked away from, and Netflix collected $2.8B for losing.
The tape already voted (NFLX +13.8% on the termination). **Declined:** a levered-acquirer short is a
different, unresearched thesis with its own financing and integration timeline, and pairing it here
would import risk we have not courted. Noted for a future court, not this one.

**Idea 4 — the pass case, stated fairly.** If UCAN's 10% is the beginning of a slide to 6–8% rather
than a price-timing artefact, then FY27 revenue growth is 9%, margin expansion stalls, and 24x is
not cheap — it is a GARP multiple on a name that has not yet been re-classified as GARP. The
**~9-month engagement blind window (B2) means we cannot falsify this until Q1'27.** That is the
honest reason this is 5/10 and 0.60%, not 7/10 and 1.2%.

---

## 7. ENTRY PLAN

**Size: 0.60% of the $3.3M deployable book ≈ $19,800 full position, in three equal ~$6,600 tranches.**
A 5/10 RP_FAIR that has not been through red team sits mid-range, not in the upper half — the
barbell instruction in the queue applies to red-team survivors.

> ### ⚠️ DO NOT FILL BEFORE 2026-08-06 — cross-account wash-sale block
> Parametric realised **15 NFLX loss lots totalling −$2,014.90 on 2026-07-06**, and the Parametric
> NFLX line is now **0** (`desk/data/parametric_realized.json`, `parametric_holdings.json`). The
> §1091 window runs **through 2026-08-05**. A fill on the 08-04 or 08-05 session disallows those
> losses across the household. The dollars are small (a deferral, not a loss) but the fix is free:
> **date the GTC ladder to activate 2026-08-06.** Standing note: holding NFLX at IBKR creates a
> permanent cross-account wash surface with Parametric's NFLX line in both directions.

| Tranche | Limit | Size | Logic |
|---|---|---|---|
| T1 | **≤ $72.50** GTC | $6,600 | Below spot. Do not chase a 14-day, +8.8% bounce off an unbased low. |
| T2 | **≤ $67.50** GTC | $6,600 | Retest of the 2026-07-20 closing low ($67.60). |
| T3 | **≤ $61.00** GTC | $6,600 | Capitulation leg, ≈20x clean FY26. **Only fills if no kill has fired.** |

Activate 2026-08-06. Limit orders only — no market orders, no premium sold or bought against it.

### Dated kill triggers

| # | Trigger | Date | Action |
|---|---|---|---|
| K1 | FY26 revenue guide cut below $51.0B **or** FY26 operating margin guide cut below 31.5% | Q3'26 print, ~2026-10-20 | **Exit in full.** The de-rate ruling is void; this is derailment. |
| K2 | Q4'26 revenue growth guided below **10.0%** | Q3'26 print | Cut to half size. Deceleration is structural, not a price-timing artefact. |
| K3 | FY26 **organic** FCF guide (~$11B, ex-fee) cut | Q3'26 print | Exit in full. Cash conversion is the thesis. |
| K4 | 2026 ads revenue tracking materially below the ~$3B path | Q3'26 or Q4'26 print | Cut to half. The reacceleration option is the bull case. |
| K5 | FY26 *What We Watched* shows view-hours growth **≤ 0%** | Q1'27 report, by 2027-04-30 | **Exit in full regardless of price.** The volume engine is in decline. |
| K6 | Content obligations > $30B **or** cash-content/amortisation > 1.25x | any print | Cut to half. The content-cost race has re-ignited. |
| K7 | UCAN revenue growth prints below 8% | Q3'26 print | Cut to half. B1 confirmed. |

No price stop. This is a quality name in a book that tranches rather than times; if $58 breaks on a
*fundamental* driver (not a beta event), re-court from scratch.

---

## 8. SCENARIOS & EDGE

Horizon ~18 months (through FY27). FY27 build: revenue +11% → $56.8B; margin 33.0% → OI $18.75B;
18% tax; FD shares ~4,120M after ~2.5%/yr net shrink → **FY27E EPS ≈ $3.70.**

| Scenario | p | Path | FY27 EPS | Multiple | FV |
|---|---|---|---|---|---|
| **Bear** | 0.35 | UCAN slides to 6–8%; FY27 revenue +9%; margin expansion stalls ~32.5%; ads undershoots the 2x; re-classified as GARP | $3.30 | 17x | **$56** |
| **Base** | 0.45 | Guide holds; growth settles 10–12%; margin to 33%; ads ~$3B on plan; buyback shrinks the count ~2.5%/yr | $3.70 | 25x | **$92** |
| **Bull** | 0.20 | Ads inflects past $3B on programmatic + upfront; view hours reaccelerate on creators/live; GenAI deflation carries margin to 34% | $3.95 | 30x | **$118** |

**E[FV] = $84.60** (0.35×56 + 0.45×92 + 0.20×118 = 19.60 + 41.40 + 23.60). Live $73.53.
**Edge = +15.1% to expected fair value over ~18 months ≈ +10%/yr.**

*Conservative-reflex check (standing correction for the two multiplicative FV errors):* the base
multiple of 25x is well below NFLX's own 30–50x history and below the 53x it carried 13 months ago,
and my E[FV] of $84.60 sits **far under the Street** — contemporaneous coverage in June had analysts at
roughly $119 ("55% upside" against a $77 price). I am below even a conservative sell-side read, so
the reflex is erring in the safe direction. I am content with that here **because** the growth-rate
reset is real and the 9-month blind window is real.

**Classification: RP_FAIR.** ~10%/yr to expected FV on a megacap is approximately a market return,
not alpha. The information is CROWDED (the disclosure change and the guide were same-day headlines);
there is no informational edge to harvest. What is genuinely on offer is **fairly-paid risk in a
verified-honest business at a verified-stable guide** — which the doctrine makes the deploying
book's *default* class, ownable without an edge claim, provided fairness is verified (it is, §2),
tails are bounded and unlevered (they are — no leverage, no contingent claims, $9.1B cash), and the
sleeve is capped (0.60%, well inside the 1.2% rule). The edge overlay is thin and is labelled as
such rather than dressed up.

---

## 9. CATALYST MAP — probability × timing × magnitude

| Catalyst | Date | p | Magnitude | Notes |
|---|---|---|---|---|
| **Q3'26 print** | **~2026-10-20** *(UNVERIFIED — precedent: Q3'25 on 2025-10-21, Q2'26 on 2026-07-16; confirm from IR before any pre-print sizing)* | 0.75 that FY26 guide is reaffirmed | **±8–12%** (last two prints: −9.7%, −7.3%) | The decisive event. **~11 weeks out — clears the 2-week no-blind-entry gate comfortably.** Positioning is washed after two negative reactions and a 52w low; a reaffirm + upfront beat is the +8% path. |
| **US upfront commitments close** | "next few weeks" from 2026-07-16 → **early-to-mid Aug 2026** | 0.5 that it is disclosed publicly | ±2–3% | The only near-dated catalyst and the least-modelled. Feeds the ~$3B ads number directly. |
| Buyback execution | continuous | 0.90 | Support, not catalyst | ~$4.7B/qtr ≈ $75M/day ≈ 6%/yr of cap; $27.1B authorised. Cushions drawdowns; does not mark a floor (B4). |
| **FY26 *What We Watched* (first annual)** | **Q1'27** | 0.95 it publishes | ±6% | **Resolves the masking channel.** The 9-month blind window ends here. K5 is armed against it. |
| Further M&A (Letterboxd, AI studios) | rolling | 0.4 by YE26 | ±1% | $587M Ben Affleck AI-film studio (Jul-20), Walking Dead rights (Jul-31), Letterboxd rumoured. Immaterial individually; watch only for a step-change in scale. |

**No fireable catalyst inside the entry window is a feature here, not a bug** — the ladder is meant
to fill into a quiet tape ahead of October, not to front-run a print.

---

## 10. FREEZABLE CALL

> **NFLX | 2026-10-31**
> **Bar:** At its Q3'26 earnings release, Netflix (a) reaffirms or narrows-within FY26 revenue
> guidance of **$51.0–$51.4B**, **and** (b) reaffirms FY26 operating margin of **31.5%**.
> **our_p = 0.75**
>
> This is the de-rate ruling itself, made falsifiable. If it resolves TRUE, estimates were stable
> through a −45% drawdown and the de-rate classification is validated. If FALSE, K1 fires, the
> position exits, and the correct verdict was derailment.

*Secondary, not frozen:* Q4'26 revenue growth guided **below 11.7%** (deceleration continues rather
than troughs) — **our_p = 0.62.** Tracked, not scored.

---

## 11. VERIFICATION GAPS (UNVERIFIABLE ≠ clean)

1. **Leg D, the 2026-06-17 → 06-25 decline including −5.8% on 06-22.** No 8-K, 10-Q or company event
   exists in the EDGAR index between 2026-06-05 and 2026-07-16 other than Form 4s. Contemporaneous
   coverage attributes it to a Nasdaq tech sell-off under a hawkish new Fed — **PLAUSIBLE, not
   CONFIRMED.** ~11% of the total drawdown is therefore attributed to beta on secondary evidence.
   Session WebSearch budget is exhausted; this could not be closed. **Top unverifiable item.**
   Materially, beta-bleed carries no information and no cause-based edge, so this gap does not
   change the ruling — but it means the cause-check is ~89% complete, not 100%.
2. **Q3'26 earnings date is precedent-derived (~2026-10-20), not confirmed from Netflix IR.**
   Immaterial at an 11-week distance; must be verified before any pre-print sizing decision.
3. **Sell-side consensus was not pulled.** Statements about "the guide came in below consensus" rest
   on the guide-vs-guide comparison in the primary letters and on headline characterisation
   ("earnings forecast disappoints"), not on a consensus datum. My valuation does not use consensus.
4. **The Q2'26 buyback average price (~high-$80s) is inferred** from the $4.7B spend across the
   quarter's traded range, not disclosed per-share. The Q1'26 figure ($96.30) *is* exact
   (13.5M shares / $1.3B, disclosed). B4's conclusion holds on the Q1 number alone.
5. **Ads revenue is not separately disclosed** in the financial statements — the ~$3B 2026 figure is
   a management assertion in the letter with no auditable line item. K4 is therefore a
   management-statement trigger, not an XBRL trigger. This is the weakest-evidenced leg of the bull
   case and it should be treated as such.
6. **The termination fee's exact after-tax value is bounded, not pinned.** Netflix disclosed a
   **$1.5B** FCF-guide delta ($11B → $12.5B) attributable "primarily" to the fee; the pre-tax fee is
   exactly $2.8B. I used the disclosed $1.5B delta to derive organic FCF of ~$11.0B (the
   conservative, company-stated figure) and a separate ~$2.2B after-tax estimate for the EPS
   adjustment. The two are not perfectly reconcilable from public data; the EPS clean-up of $0.51 is
   an estimate, the $11B organic FCF is not.

---

## 12. ONE-LINE SUMMARY

A −45% drawdown with a **fully identified, four-part cause**: a margin quarter, a 27% acquirer-overhang
round trip that ended with Netflix collecting **$2.8B for losing the auction**, a beta leg, and — the
load-bearing part — **two consecutive quarters of beating the print and guiding the growth rate down.**
Estimates never fell; the multiple did, from ~53x to **24x clean forward**, on a business still guiding
20%+ operating-income growth with a pristine balance sheet and 1%-of-revenue SBC. That is a **de-rate**.
But the growth rate genuinely reset 5.9pp, **UCAN — 43% of revenue — printed 10% *with* a price
increase in it**, view hours grew **2%**, and Netflix just moved its last engagement metric to annual
reporting, opening a **9-month window in which the decisive variable cannot be checked.** Cheap enough
and honest enough to own small at a fair price; not cheap enough, and not verifiable enough, to call
an edge.
