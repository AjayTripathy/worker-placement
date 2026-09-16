# APP (AppLovin Corp) — RED BENCH, full adversarial court
**Date:** 2026-08-07 · **Tier:** Fable · **Posture:** default-REJECT the LONG
**Subject:** CIK 0001751008 · NASDAQ: APP · live $340.09 (IBKR, 2026-08-07, bid 339.45 / ask 340.50, +1.32%)
**Triage under review:** `desk/data/court_artifacts/VELOCITY_20260806_REFUTABILITY_20260807.md` §1 (8/10)

---

## 0. HEADLINE CORRECTION TO THE TRIAGE

The triage's framing premise is **factually wrong**, and it is the reason the cause looked like a hole.

> Triage: "on 2026-08-05 APP printed a **BEAT** … and closed at a 52-WEEK LOW."

**It was a MISS.** Q2 revenue $1,923.7M came in ~$20M (**−1.0%**) *below* the ~$1,940M consensus;
adjusted EPS $3.76 was in line ($3.75E); and the Q3 revenue guide midpoint **$2,070M was below the
~$2,080M** the Street carried. So the second half of the assignment — "the beat may be a guide-down
in disguise" — resolves as: **there was no beat.** It was a small miss plus a small guide-down.

That removes the paradox the triage built its 8/10 on. A −19.7% response to a −1.0% revenue miss is
still a violent reaction, but it is a **re-rating of forward growth**, not an unexplained dislocation.

---

## 1. MODE B — FIRST PRINCIPLES, NO PROMOTER FRAMING (lead)

I derived the decisive question without the release's framing: *what actually produces AppLovin's
revenue growth, and is that mechanism repeatable?* The company answers this itself, in plain
English, in the MD&A of every filing — and it is absent from the press release, absent from the
marketed takeaway, and absent from the triage.

### 1.1 THE DECOMPOSITION — the single most important table in this name

AppLovin decomposes its own revenue growth into **net revenue per installation** × **volume of
installations**. Pulled verbatim from primary filings:

| Period | Revenue growth | Net revenue **per installation** | **Volume** of installations |
|---|---|---|---|
| FY2023 → FY2024 | +75% | +22% | **+50%** |
| FY2024 → FY2025 | +70% | +72% | **+3%** |
| Q1-26 y/y | +59% | **+93%** | **−18%** |
| Q2-26 y/y | +53% | +58% | **−2%** |
| H1-26 y/y | +56% | +75% | **−10%** |

Sources (all primary, company's own MD&A):
- FY24/FY25: 10-K FY2025, filed 2026-02-19, acc. `0001751008-26-000010` —
  https://www.sec.gov/Archives/edgar/data/1751008/000175100826000010/app-20251231.htm
  *"the volume of installations increased 3% and net revenue per installation increased 72%"* (FY25);
  *"the volume of installations increased 50% and net revenue per installation increased 22%"* (FY24).
- Q1-26: 10-Q, filed 2026-05-06, acc. `0001751008-26-000044` —
  https://www.sec.gov/Archives/edgar/data/1751008/000175100826000044/app-20260331.htm
  *"net revenue per installation increased 93%, partially offset by a decrease in the volume of installations of 18%."*
- Q2-26 / H1-26: 10-Q, filed 2026-08-05, acc. `0001751008-26-000059` —
  https://www.sec.gov/Archives/edgar/data/1751008/000175100826000059/app-20260630.htm
  *"net revenue per installation increased 58%, partially offset by a decrease in the volume of installations of 2%"* (Q2);
  *"…increased 75%, partially offset by a decrease in the volume of installations of 10%"* (H1).

**The finding.** In two years AppLovin has inverted its growth engine. In 2024 it was a **unit**
business (+50% volume). It is now a **price** business delivering **fewer units** (H1-26 volume
−10%). Essentially 100% of current growth is higher extraction per install.

**Why this is the whole story.** Revenue-per-install is bounded by advertiser ROAS — an advertiser
pays more per install only while incremental installs still clear their return hurdle. It is an
arithmetically capped lever, unlike unit growth. A market that believed APP was a compounding
platform (Dec-2025, $733.60 close) is repricing it as a **decaying-lever** business. That is what
the −55% is, and it is rational, not a dislocation.

**Honesty grade on this channel: CLEAN.** The company discloses the volume decline and the
price-dependence explicitly in the MD&A. It is not hidden. It is simply not in the press release,
and the sell-side headline ("+53%, 84% margin") does not carry it. Per the framework, a disclosed
impairment is not an honesty catch — but it *is* the correct fundamental read.

### 1.2 THE 84% MARGIN IS A SYMPTOM, NOT A MOAT

Cost of revenue was $225.8M on $1,923.7M (**11.7%**), vs 12.3% a year ago (10-Q, MD&A). The margin
is high *because* the growth is price, not volume: serving 2% fewer installs at 58% higher revenue
each mechanically expands margin without any efficiency gain. **The 84% margin and the −2% volume
are the same fact.** Modelling the margin as durable operating leverage — as the triage's
"83.9% margin" framing implies — double-counts the price lever. If revenue-per-install growth
decays toward zero, margin does not stay at 84% on flat units; it compresses as fixed datacenter
and engineering costs (which the filing says are *rising*) spread over a flat revenue base.

### 1.3 SEASONALLY-MATCHED SEQUENTIALS — the guide, tested properly

I first framed this as "the guide requires a reacceleration." **That framing is wrong and I am
correcting it** — APP has real H2 seasonality, so raw sequentials mislead. Matched to the same
step a year earlier:

| Sequential step | 2025 | 2026 | 2026 as % of prior-year momentum |
|---|---|---|---|
| Q1 → Q2 | +8.61% | **+4.41%** | **51%** |
| Q2 → Q3 | +11.62% | **+7.61%** (guide mid) | **65%** |

Derivation: Q1-25 $1,158.974M; Q2-25 $1,258.754M; Q3-25 $1,405.045M; Q1-26 $1,842.449M;
Q2-26 $1,923.686M (XBRL `RevenueFromContractWithCustomerExcludingAssessedTax`, companyfacts API);
Q3-26 guide mid $2,070M (8-K 2026-08-05, acc. `0001751008-26-000057`, Ex-99.1).

**Honest reading:** Q2 delivered only **half** the prior-year seasonal step — that is the miss. The
Q3 guide embeds a *partial* recovery to 65% of prior-year momentum, which is a genuine bet, but not
an absurd one. Management's stated basis is timing:

> CEO Adam Foroughi: *"the pace of meaningful advertising model improvement was lighter than normal
> during the June quarter, and that the next significant model upgrade landed just after the quarter
> ended."* — with the explicit assertion of **"no indication of weaker advertiser demand or changes
> in the competitive landscape."**

**This concession is more damaging than the miss.** Management is stating that quarterly revenue is
a function of a **discrete internal model-release cadence**. That is an admission that growth is
R&D-event-driven, not demand-driven or annuity-like. A business whose revenue depends on shipping
the next model on schedule does not deserve a platform multiple.

### 1.4 THE CTO LINKAGE (my inference — dated, not company-asserted)

8-K filed 2026-04-07, acc. `0001751008-26-000014`, Item 5.02 —
https://www.sec.gov/Archives/edgar/data/1751008/000175100826000014/app-20260402.htm

Basil Shikin, CTO for ~10 years, notified the company on 2026-04-02 that he would step down
**effective 2026-07-01**, moving to "Distinguished Engineer." Per the press release he *"led
development of much of our technology stack over the nearly 10 years he was CTO."* The Chief
Administrative & Legal Officer also retired effective 2026-08-01.

**The June quarter — the quarter management says had a "lighter than normal" pace of model
improvement — is precisely the CTO transition quarter.** The company does not connect these; I do,
and I flag it as inference, not established causation. But if the growth driver is the model-release
cadence (§1.3) and the person who built the model stack departed mid-quarter, that is a
**structural** explanation competing directly with management's **timing** explanation. Timing
recovers in Q3. Structural does not.

### 1.5 THE DISCLOSURE ASYMMETRY — the one genuine takeaway-vs-data divergence

The entire multiple rests on TAM expansion into **e-commerce/CTV**. I grepped the full Q2-26 10-Q
(265,789 chars, extracted text) for the KPIs of that expansion:

| Term | Hits in Q2-26 10-Q |
|---|---|
| "pixel" | **0** |
| "merchant" | **0** |
| "self-service" | **0** |
| "e-commerce" | 8 — **all** in forward-looking/risk-factor boilerplate |

The company reports **no merchant count, no pixel count, no e-commerce revenue split, no
self-service cohort** — nothing. Meanwhile the *only* independent read of that segment says it is
decelerating: BofA (Omar Dessouky) found APP added **~750 new pixels in June vs ~950 in May**, with
merchant count stalled at **~8,300**, immediately after the **2026-06-22** launch of self-service
Axon. He cut 2026/2027 revenue estimates while keeping a $705 Buy. The stock fell **−12.6%** that
day (2026-07-13; $506.98 → $442.85, IBKR daily bars).

**Verdict on this channel: REVIEW_FLAG (divergence), not fraud.** Management markets a growth vector
it provides zero measurable disclosure for, and the sole third-party measurement contradicts it.
The marketed takeaway ("expanding into e-commerce and CTV") is **unfalsifiable from company
disclosure** while the available external data says the ramp stalled. That is a real asymmetry — but
it is an omission of KPI, not a misstatement, so it does not clear the ELEVATE bar.

---

## 2. MODE A — CLAIM VERIFICATION LEDGER

Every material claim: **{claim | source/method | authority | result}**.

| # | Claim | Method / Authority | Result |
|---|---|---|---|
| 1 | "APP printed a BEAT on 2026-08-05" (triage) | Consensus vs actual; press aggregation cross-checked to 8-K Ex-99.1 | **REFUTED.** Revenue $1,923.7M vs ~$1,940M consensus = −1.0% miss. EPS $3.76 vs $3.75 in line. |
| 2 | Q3 guide is above/at consensus | 8-K acc. `0001751008-26-000057` vs Street ~$2,080M | **REFUTED.** Guide mid $2,070M is ~0.5% *below* consensus. A guide-down, as suspected. |
| 3 | Q2 revenue $1,924M, +53% y/y | XBRL companyfacts, `RevenueFromContractWithCustomerExcludingAssessedTax` 2026-04-01→06-30 = **$1,923,686k** | **VERIFIED** (audited/reviewed tag). |
| 4 | Adj. EBITDA $1,614M @ 83.9%; FCF $863.3M | 8-K Ex-99.1 (non-GAAP, unaudited) | **CONSISTENT.** GAAP op income $1,494.277M (XBRL) ties directionally; the $120M gap is SBC ($169.0M H1) + D&A. Non-GAAP, so not independently auditable. |
| 5 | Net income $1,266.5M, diluted EPS $3.76 | XBRL `NetIncomeLoss` = $1,266,538k; `WeightedAverageNumberOfDilutedSharesOutstanding` = 337,031k → $3.758 | **VERIFIED** (recomputed). |
| 6 | Growth is price-driven with **shrinking units** | MD&A, 10-K FY25 + 10-Q Q1-26 + 10-Q Q2-26 (§1.1) | **VERIFIED** — company's own words across three filings. |
| 7 | **Short-seller channel:** CapitalWatch money-laundering allegations | Report 2026-01-20; APP cease-and-desist 2026-01-27; **retraction + apology 2026-02-09** (CNBC: cnbc.com/2026/02/09/short-seller-capitalwatch-retraction-applovin-hao-tang.html) | **REFUTED — in the company's favor.** Short thesis withdrawn by its author; stock +13.2% on 2026-02-09 (IBKR bars, $406.72→$460.38). **Not a live bear leg.** |
| 8 | **Regulatory channel:** SEC probe into data-collection / alleged systematic breach of platform partners' ToS | Opened ~2025-10-06 (Bloomberg); "still active and ongoing" 2026-02-20 (Bloomberg); **closed with no recommended action, disclosed on the Q2 call 2026-08-05** | **RESOLVED — in the company's favor.** Confirmed absent from both the FY25 10-K and Q2-26 10-Q: 0 hits for "subpoena", "SEC investigation", "informal inquiry", "document requests" in either. Non-disclosure is consistent with closure. |
| 9 | Securities class action / derivative suits are live | Q2-26 10-Q, Item 1 Legal Proceedings | **VERIFIED but STALE.** Class period **2024-11-07 → 2025-03-27** (the Fuzzy Panda/Culper era). MtD fully briefed **Feb 2026**, undecided. Derivative suits track it. Pre-dates the entire de-rate; not a cause. |
| 10 | Platform-policy (Apple/Google) risk is an active cause | Q2-26 10-Q risk factors | **UNVERIFIABLE as a *cause*.** Risk-factor boilerplate re: App Store/Play Store policy exists, but **no dated Apple/Google action** maps to any drawdown leg. No evidence this fired. |
| 11 | Big-customer concentration is a hidden risk | 10-Q searched: "no single customer" 0 hits, "one customer" 0 hits, no 10%-customer disclosure | **NO DISCLOSED CONCENTRATION.** Risk factor cites *channel* concentration (mobile gaming ecosystem), not a customer. Clients named include Meta and Google as *advertisers*. `customer_id` whale-detector **not fired**: no undisclosed-concentration claim is load-bearing here. |
| 12 | "Bought back stock at ~$501/sh" vs $335.67 (triage) | 8-K Ex-99.1 + XBRL | **VERIFIED-with-correction.** $551.3M / 1.1M sh = $501/sh is arithmetically right, but $551.3M = **$531.7M discretionary repurchase** (`StockRepurchasedAndRetiredDuringPeriodValue` Q2) **+ $19.6M RSU tax withholding** (`PaymentsRelatedToTaxWithholding…`, Q2 derived). Q2 closes ranged $372–$614; **$501 is above the quarter's average but is not a top-tick.** Fair reading: mildly poor timing, not a stunt. |
| 13 | APP is a net-cash company | XBRL `LongTermDebtNoncurrent` 2026-06-30 = **$3,515,072k**; `CashAndCashEquivalents` = **$3,053,306k** | **REFUTED. APP is ~$462M NET DEBT.** Cap structure pulled before any EV claim, per standing rule. |
| 14 | 07-13 −12.6% leg has a company cause | EDGAR full filing list 2026 | **REFUTED — no 8-K.** No company filing between 2026-06-05 (annual meeting, Item 5.07) and 2026-08-05. The July leg is **externally caused** (BofA pixel note, §1.5). |

---

## 3. DATED DRAWDOWN LEGS — every leg now has a cause

Reconstructed from IBKR daily bars (contract 481863646, 1Y, RTH). Peak close **$733.60 on
2025-12-22**; live $340.09 = **−53.6%**.

| Date | Move | Cause | Status |
|---|---|---|---|
| 2025-10-06 | −14.0% ($682.76→$587.00) | Bloomberg reports SEC probe into data-collection practices | **Now resolved** (no action, Aug-2026) |
| 2026-01-20→30 | −16.9% on 01-30 | CapitalWatch short report (01-20) + fallout | **Retracted 02-09** |
| 2026-02-04 | −11.6% | Short-report fallout continues | **Retracted 02-09** |
| 2026-02-09 | **+13.2%** | CapitalWatch retraction + apology | Bear leg removed |
| 2026-02-12 | **−19.7%** ($456.81→$366.91) | **Q4-25 print (02-11): revenue $1.66B beat $1.61B, EPS beat 10%, guidance raised — stock fell anyway.** Cited driver: Meta competitive threat | **Structural** |
| 2026-03-26 | −10.4% | No 8-K; sector/AI-adtech beta | Unattributed |
| 2026-06-09 | −7.6% | No 8-K | Unattributed |
| **2026-07-13** | **−12.6%** ($506.98→$442.85) | **BofA pixel data: e-commerce ramp decelerating (750 June vs 950 May adds; merchants stalled ~8,300) post the 06-22 self-service launch** | **Structural** |
| 2026-07-28 | — | Pomerantz opens class-action investigation re: "AI-driven merchant platform performance" | Follows the July leg |
| **2026-08-06** | **−19.7%** ($417.80→$335.67) | **Q2 revenue miss (−1.0%) + Q3 guide below consensus** | **Structural** |

### 3.1 THE MOST INFORMATIVE FACT IN THE ENTIRE COURT

**On 2026-08-05 AppLovin disclosed that the SEC had closed its investigation with no action — the
single largest binary overhang on the name, removed. The next day the stock made a new 52-week low,
−19.7%.**

The market was handed an unambiguous *positive* resolution of the fraud/regulatory channel and sold
the stock 20% anyway. Combined with the CapitalWatch retraction (Feb) and the Q4-25 beat-and-raise
that fell 19.7% (Feb), the conclusion is forced:

> **The de-rate is not, and has never been, about honesty, fraud, or regulation. Every one of those
> channels has been tested and resolved in AppLovin's favor. What is left is the growth-quality
> question in §1.1 — and the market is pricing that, repeatedly, through beats and clearances alike.**

This closes the triage's "unclosed cause hole" completely, and it closes it **against** the
mispricing interpretation. The triage's implicit hope — that an unfound off-P&L fact would explain
the gap and, once found, be either fatal or dismissible — resolves as: the causes were found, the
scary ones are dead, and the surviving one is on the face of the 10-Q.

---

## 4. VALUATION AT THE LOW — WHAT DECELERATION IS PRICED

At live **$340.09** (IBKR 2026-08-07), diluted shares 337.031M:

| Metric | Value |
|---|---|
| Market cap | **$114.6B** |
| Net debt (§2 #13) | **+$0.46B** |
| **Enterprise value** | **$115.1B** |
| EV / annualized Q3-guided revenue ($8.28B) | **13.9×** |
| EV / annualized Q3-guided adj. EBITDA ($6.90B) | **16.7×** |
| P/E on annualized Q2 EPS ($15.04) | **22.6×** |
| FCF yield on annualized Q2 FCF ($3.45B) | **3.0%** |

Guided Q3 y/y growth is **+47.3%** ($2,070M vs $1,405.045M). So the tape is paying ~22.6× earnings
for ~47% guided growth — **PEG well under 0.5**. On any conventional screen this is cheap.

**What is actually priced:** at 16.7× EV/EBITDA against a mature ad-platform terminal multiple of
~10–12×, the market is discounting a **fade to roughly GDP-plus growth inside ~3 years** — i.e. the
revenue-per-install lever exhausting on approximately the observed decay path (+93% → +58% → …).
The market is not pricing a fraud and it is not pricing a collapse. **It is pricing the §1.1
decomposition, correctly.** The "cheap PEG" is cheap only if you extrapolate a lever the company's
own filings show decaying.

**The sell-side is anchored and lagging, so "upside to consensus" is circular.** Post-print targets:
BTIG $640→$574 (Buy), Jefferies $700→$550 (Buy), Wells Fargo $357 (Equal Weight). Consensus PT
~$612 vs a $340 tape = a ~80% implied gap that no one is trading. **The tape is leading the analysts
down** — a bearish microstructure tell, and a warning that any "it's cheap vs consensus" argument is
resting on stale marks. Wells Fargo at $357 is the only target near the tape.

---

## 5. CAPITAL-ALLOCATION CREDIBILITY

- H1-26 repurchases **$1,532.95M** (`PaymentsForRepurchaseOfCommonStock`); FY25 **$2,191.94M**.
  ~$3.72B deployed over 18 months.
- Q2-26 discretionary repurchase **$531.68M** at ~$501/sh average → **~32% underwater** at $340.09
  (≈$170M of mark-to-market destruction on the quarter's tranche alone).
- Funded against a balance sheet that is **net-debt ~$462M**, not net cash. Buybacks are consuming
  ~90% of FCF while the company carries $3.5B of debt.
- Diluted shares fell only 341.97M (FY25) → 337.03M (Q2-26) — **~1.4% net reduction for ~$3.7B**,
  because SBC ($169.0M H1-26) offsets much of the gross repurchase.
- The 10-Q carries a risk factor conceding the point: *"We may not realize the anticipated long-term
  stockholder value of our share repurchase programs."*
- Insider flow runs the other way: near-weekly Form 4 / Form 144 filings May–Jul 2026 (e.g.
  144s on 06-04, 06-10, 06-11, 06-12, 06-16 ×2, 07-06).

**Verdict: NOT a credibility catch, but a negative.** Buying ~$501 into a decaying-lever multiple,
debt-funded, while insiders distribute, is value-destructive-so-far allocation. It is disclosed, it
is legal, and the $501 was near the quarter's average — I decline to call it a top-tick stunt. But
it is not the "management sees value" signal a long thesis would want to lean on.

---

## 6. STRONGEST KILL

> **AppLovin's growth is a price lever with an arithmetic ceiling, applied to a shrinking unit base,
> and the segment marketed to replace it is the one segment the company reports no metric for.**

Unit volume went **+50% (FY24) → +3% (FY25) → −18% (Q1-26) → −2% (Q2-26)**, while revenue per
install carried **+22% → +72% → +93% → +58%**. Roughly all growth is now extraction per install —
a lever bounded by advertiser ROAS, not a compounding asset. Management then conceded on the Q2
call that quarterly revenue tracks a **discrete internal model-release cadence** ("the pace of
meaningful advertising model improvement was lighter than normal"), which converts the growth rate
from an annuity into an R&D shipping schedule — one whose 10-year architect departed effective
2026-07-01. And the designated replacement engine, e-commerce/self-service Axon, is reported with
**zero** company KPIs (0 hits for pixel / merchant / self-service in the 10-Q) while the only
independent measurement shows adoption decelerating immediately after its 2026-06-22 launch.

**The kill is sharpened, not weakened, by the good news:** the SEC closed its probe with no action
and the short-seller retracted, and the stock still made a 52-week low. There is no hidden fact left
to find. The market is pricing the disclosed decomposition, and I agree with it.

**Secondary kill — no informational edge.** This is a $115B mega-cap with ~40 analysts, a $612
consensus PT, and 10.8M shares traded on the print. Fully DISCOVERED/CROWDED under the conditioning
layer. A long here is a bet that a saturated consensus has mis-modelled a ratio printed in the MD&A.
That is not an edge; it is a view. Per the standing rule, divergence claims in crowded names require
a materially higher bar than this clears.

---

## 7. WHAT WOULD CHANGE MY MIND (dated, falsifiable)

| # | Trigger | Threshold | Date |
|---|---|---|---|
| 1 | **Volume of installations turns positive y/y** | Q3-26 10-Q MD&A prints installation volume **≥ 0%** y/y (vs −2% Q2, −18% Q1). Volume −18%→−2% is already a real improvement; a positive print flips the engine back to units and breaks the §1.1 kill outright. | **~early Nov 2026** (Q3 10-Q) |
| 2 | Revenue-per-install decay arrests | Q3-26 net revenue per installation **≥ +55%** y/y (vs +58% Q2, +93% Q1). Stabilization, not decay, would extend the lever's life materially. | ~early Nov 2026 |
| 3 | Q3 revenue lands **above** the guide top | Actual **> $2,085M**, i.e. seasonally-matched sequential momentum recovers to **>75%** of the prior-year Q2→Q3 step (+11.62%). Validates management's "timing" explanation over my structural one. | ~early Nov 2026 |
| 4 | Company begins disclosing e-commerce KPIs | Any of: merchant count, pixel count, e-commerce revenue split, or a non-gaming cohort disclosure in the Q3-26 10-Q or on the Q3 call. Removes the §1.5 asymmetry and makes the growth vector testable. | ~early Nov 2026 |
| 5 | Independent pixel/merchant data re-accelerates | Third-party (BofA Dessouky or equivalent) shows monthly pixel adds back **>950/mo** and merchant count breaking **>8,300**. Leading indicator — fires *before* #1–#4. | rolling, monthly |
| 6 | CTO-transition risk proves cosmetic | Q3 model-upgrade cadence normalizes under Gio Ge with no further "lighter than normal" language. | ~early Nov 2026 |
| 7 | Capital allocation turns disciplined | Buyback pace cut and/or net debt eliminated; or credible insider *buying* on Form 4. | any |

**Reverse tripwire (would deepen the reject):** Q3 revenue **< $2,055M** (guide floor) or
installation volume worse than −2% y/y → the lever is exhausting faster than the decay path implies,
and 16.7× EV/EBITDA is then too high, not too low.

---

## 8. VERDICT

**CONVICTION: 6/10 — REJECT the LONG.**

Not 8, not 9, and I will not inflate it. The bull case has genuine, primary-sourced merit that a
fair court must record: every fraud and regulatory channel resolved **in AppLovin's favor** (SEC
closed no-action 2026-08-05; CapitalWatch retracted 2026-02-09); installation volume decline
**improved sharply from −18% to −2%**; a −19.7% day came off a **−1.0%** revenue miss with in-line
EPS; and 22.6× earnings on +47% guided growth is not an expensive multiple by any conventional
measure. This is a high-quality, cash-generative, **honestly-disclosing** business. It is emphatically
**not a short**, and it is **not a liar** — the honesty-alpha lens returns CLEAN on the financials
and the decomposition, with a single REVIEW_FLAG for the e-commerce KPI omission.

I reject the long anyway, on two grounds. First, the growth engine has inverted from units to price,
the price lever is decaying on the company's own numbers (+93% → +58%), management has conceded that
revenue tracks a discrete model-release cadence, and the replacement vector is unmeasurable from
disclosure while the sole external measurement says it stalled. Second, and independently: this is a
saturated mega-cap where the only "edge" on offer is a ratio printed in the MD&A that forty analysts
can read, and where sell-side targets ($550–$640) are stale relative to a $340 tape — so the
"cheap vs consensus" support is circular.

**RECOMMEND: REJECT.** Do not size. The name becomes genuinely interesting — and I would want it
re-courted, not dismissed — if trigger #1 or #3 fires in early November. The decisive datum is a
single line in the Q3 10-Q MD&A: **the y/y change in volume of installations.**

**Standing correction to the triage:** the 8/10 court-worthiness rested on "a 53%-growth 84%-margin
**beat** printing a new low." There was no beat, and the missing non-financial catalyst was not
missing — it was a July 13 sell-side pixel note plus a February competitive re-rate. Re-scored
**3/10**: cause fully established, no residual hole.

---
*Prepared under default-REJECT posture. Live price from IBKR at time of writing; all financials from
SEC primary filings and the XBRL companyfacts API. Web-search channel was exhausted at session level;
external reporting was reached via direct fetch and is labelled as secondary wherever it could not be
bound to a primary document — specifically the consensus figures, the BofA pixel data, and the SEC
closure, none of which appear in a company filing. Those three should be re-confirmed against the Q2
call transcript before any capital decision.*
