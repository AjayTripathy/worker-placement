# APP (AppLovin Corp) — BLUE BENCH, prosecution of the RED case

**Date:** 2026-08-07 · **Tier:** Fable · **Posture:** prosecute every RED kill; default is that a kill
survives unless a primary source breaks it
**Subject:** CIK 0001751008 · NASDAQ: APP
**Live:** **$338.30** (IBKR contract 481863646, 2026-08-07; bid 338.30 / ask 339.00; +0.78%;
prior close 335.67; 52-wk low **$332.19** set 2026-08-06; annualized IV 63.9%)
**Under review:** `desk/data/court_artifacts/APP_COURT_RED_20260807.md` — REJECT, 6/10

---

## 0. WHAT THE RED GOT RIGHT (conceded up front, so the rest is not special pleading)

I independently re-verified and **concede** the following. A blue bench that finds only
pro-long facts is worthless.

| RED finding | My independent check | Ruling |
|---|---|---|
| **APP is net DEBT, not net cash** (~$462M) | XBRL companyfacts 2026-06-30: `CashAndCashEquivalentsAtCarryingValue` $3,053,306k; `LongTermDebtNoncurrent` $3,515,072k; **no** `LongTermDebtCurrent`, **no** `ShortTermInvestments`/`MarketableSecuritiesCurrent` tag exists → net debt **$461,766k** | **UPHELD** — correct, and correctly pulled before the EV claim |
| Buyback timing is poor | Q2 repurchase ~$501/sh avg vs $338.30 = **~32.5% underwater**; ~$3.72B over 18 months for ~1.4% net share reduction (341.97M → 337.03M diluted) because SBC ran $169.0M in H1-26 alone | **UPHELD** — a real negative |
| Q2-26 was **not** a beat vs the Street | Cannot independently verify the ~$1,940M consensus — **the session web-search budget was exhausted (200/200)**, same constraint the red disclosed. Treated as SECONDARY. | **UPHELD, source-limited** (see §4 for the material qualification) |
| Every fraud/regulatory channel resolved in APP's favour | Confirmed 0 hits for "subpoena" / "SEC investigation" / "informal inquiry" in the Q2-26 10-Q and FY25 10-K. **Sharpening against both benches:** the closure rests on an **oral CFO statement only** — *"It was a voluntary request, which we never deemed material. **The SEC has recently advised us that it concluded its inquiry with no recommended action**"* (Stumpf, 2026-08-05). It appears in **no filing**, including the same-day 10-Q; there is no 8-K item and no SEC document. Consistent with a matter never deemed material enough to disclose on the way in, but it is **assertion, not documentation** | **UPHELD, oral-only** |
| **Secondary kill: no informational edge** | Correct, and it is the binding constraint on my own recommendation | **UPHELD — see §7** |

I also found **one small artifact the red missed that cuts the red's way partially, and one that
cuts mine** — both are reported in §1.

---

## 1. KILL #1 — "the units→price inversion" — **OVERTURNED (interpretation); data VERIFIED**

> RED: *"In two years AppLovin has inverted its growth engine… Essentially 100% of current growth is
> higher extraction per install… Revenue-per-install is bounded by advertiser ROAS… an
> arithmetically capped lever, unlike unit growth."*

The five numbers are real. I re-pulled every one from the three filings and they are quoted
correctly. **The inference drawn from them is not supported, and the company's own filings say why.**

### 1.1 "Installation" is not AppLovin's pricing unit — the company says so explicitly

FY2025 10-K, Item 1 (Business — *Axon Ads Manager*), acc. `0001751008-26-000010`,
https://www.sec.gov/Archives/edgar/data/1751008/000175100826000010/app-20251231.htm :

> *"Advertisers set return goals for their campaigns and Axon Ads Manager targets users to match
> those goals. Return on advertising spend is measured based on either third-party or
> self-attribution. **Advertisers are charged dynamically based on their campaign goals, rather than
> a simple fixed price per impression or per action (click or installation).**"*

Repeated in the Q2-26 10-Q, Item 2, *Components of Results of Operations — Revenue*
(acc. `0001751008-26-000059`):

> *"We generate substantially all of our revenue from fees collected from advertisers spending on
> AppLovin Ads, **which are determined dynamically based on advertisers' campaign goals**."*

The red's kill treats "net revenue per installation" as a **price** — a take-per-unit with an
arithmetic ceiling. The issuer states, in both filings, that it is **not** a price. It is a
**quotient**: total advertising revenue ÷ a count of one particular campaign outcome. A quotient
whose denominator the company says it does not charge for has no "arithmetic cap" of the kind the
kill asserts.

### 1.2 The denominator does not span the numerator — this is the decisive point

FY2025 10-K, Note 2 (Summary of Significant Accounting Policies — *Revenue from Contracts with
Customers*):

> *"Revenue is recognized for **impression-based arrangements** when an ad impression is delivered;
> for **action-based arrangements**, when the specified action (such as a click or install) occurs."*

There are **two** revenue-recognition bases. An installation is *one* specified action inside *one*
of them. Revenue recognised on impression-based arrangements — Wurl CTV, brand/streaming — and on
click/site-visit actions (web e-commerce) produces **zero installations in the denominator**.

The same 10-K describes exactly the mix that breaks the ratio:

- *"Advertisers are not only able to attract users that initially download their app **or visit their
  website**…"* (Item 1)
- *"Our technology finds the users at that value who are most likely to engage with the app **or
  website**."* (Item 1, *Reach*)
- *"**Our app-based clients** can analyze by retention periods from initial app download onwards…"*
  (Item 1 — the filing itself carves out "app-based clients" as a **subset**)
- Seasonality: *"As the breadth and scale of advertisers using our platform continues to expand,
  **including increased participation from large e-commerce advertisers**, the magnitude and impact
  of these seasonal trends may become more pronounced over time."*

**Therefore: "revenue per installation up, installation volume down" is the exact arithmetic
signature of a mix shift out of app-install campaigns into web/CTV campaigns — and it is equally the
signature of per-install extraction. The two are observationally identical in this disclosure.**

### 1.2b — CORRECTION AGAINST MY OWN ARGUMENT: the mix channel is BOUNDED, and management supplies a better mechanism

I pushed the mix hypothesis hard, then went to the call to size it. **It is much more bounded than my
§1.2 implies, and I am correcting my own case.** On 2026-08-05 Foroughi stated that the
non-install supply the hypothesis relies on is **not live**:

> *"in consumer, **we're still budgetarily constrained.** … We think the **first path to supply
> expansion will be on device, and the second path will be Connected TV.** … It's an opportunity
> that's sitting there. **We're just not at the point yet where we can go execute on it.**"*
> *"**Step one** would be the obvious, just non-gaming apps… **Step two** would be the open web.
> **Step three** would be Connected TV."*
> *"If you split the world up into consumer business, e-commerce on the web, and then non-gaming
> apps… **We will go after the second later, and it just hasn't been a focus of ours yet.**"*
> — and the anchor: *"**Gaming is still the majority of our revenue.**"*

So open-web supply and CTV are **roadmap, not run-rate**. The live non-install channel is the
"consumer"/e-commerce book only, which management says *"isn't yet large enough to fully smooth a
quarter like this."* **My §1.2 mechanism is real but cannot carry a 58-point move.**

**But the kill still fails — on a better, management-stated mechanism I did not have.** Asked
directly by Wells Fargo about mobile game downloads being down 10–15% y/y, Foroughi gave an
**intra-gaming** explanation:

> *"**when it comes to installs, the trend over the last few years has been a movement away from very
> high install, low quality, hyper casual, much more to casual and deeper games and in-app
> purchasing. As you get into deeper funnels, you get a much higher CPI and a much higher LTV. As the
> cost goes up, it does not mean that the value goes down. Everything is on a return on ad spend
> basis.**"* — Foroughi, 2026-08-05

**A shift from hyper-casual (many cheap, low-value installs) to mid-core (fewer expensive,
high-value installs) produces the identical signature — falling install volume, rising revenue per
install — with zero mix contamination and zero extraction.** It is a change in *what an installation
is*, not in what AppLovin charges for one. The denominator is a **non-constant unit**.

That is the decisive point, and it does not depend on my mix hypothesis at all: **the red's kill
requires "installation" to be a stable unit of account across four years. It is not, on the
company's own account of its own market.**

### 1.2c — "Installation" is never defined in any filing, and the metric's referent changed

Per the parent's instruction I checked all three filings for a methodology or attribution-window
change (SKAdNetwork, self-attributing-network changes) that would make the inversion *measurement*
rather than *extraction*. Findings:

- **No definition exists.** The term "installation" is **never defined** in the FY25 10-K, the Q1-26
  10-Q, or the Q2-26 10-Q. There is no statement of whether web/e-commerce purchase conversions enter
  the denominator, no attribution-window disclosure, and no SKAN methodology note.
- **No attribution-methodology change is disclosed** in any of the three filings. The only
  attribution language is generic (*"Return on advertising spend is measured based on either
  third-party or self-attribution"*, FY25 10-K).
- **The metric's stated referent did change between quarters:** Q1-26 attributes the bridge to
  *"improved **Axon Ads Manager** performance"*; Q2-26 attributes the same bridge to *"improved
  **AppLovin Ads** performance."* This appears to be a **product rename, not a redefinition** — but it
  means the label is not constant across the series the red tabulated.

**Ruling on the parent's question: the inversion is NOT demonstrably a measurement artifact — no
methodology change is disclosed. But neither is it demonstrably extraction, because the unit is
undefined, unaudited as a unit, and (per management) changing in character.** The honest status is
that **the ratio is not decision-grade in either direction**, which is fatal to a kill built on it.

The red asserted one branch and called it *"the whole story."*

### 1.3 The red's two kills are mutually destructive

This is the sharpest internal problem in the red case:

- **§1.1** requires e-commerce/CTV to be **immaterial** — otherwise it contaminates the ratio and
  "essentially 100% of growth is extraction per install" is false.
- **§1.5** requires e-commerce to be **material** — otherwise its alleged stall is not a structural
  bear leg worth a −12.6% day.

**The red runs both at full strength. It can have one.** If e-commerce is big enough for its ramp to
matter, it is big enough to break the per-install denominator. If it is too small to break the
denominator, its ramp is too small to be a kill.

### 1.4 Numerator and denominator are one variable — the red double-counts

Revenue growth = (1 + Δvolume) × (1 + Δrev-per-install). The company's own pairs:

| | Δ volume | Δ rev/install | product | actual y/y |
|---|---|---|---|---|
| Q1-26 | −18% | +93% | **1.583** | +59.0% |
| Q2-26 | −2% | +58% | **1.548** | +52.8% |

**The product barely moved. The decomposition ROTATED toward units.** The red reads the numerator's
fall (+93%→+58%) as *"the price lever is decaying"* — bearish — while separately noting the
denominator's recovery (−18%→−2%) and discounting it. Under the mix reading these are **the same
variable moving once**, and it moved toward *normalization*, not decay: the unit base recovered
16 points of y/y growth while the ratio gave back 35 points, and total growth was essentially
unchanged.

The red's own change-my-mind trigger #1 is "volume of installations ≥ 0% y/y." **It is 2 points
away, having closed 16 points in a single quarter.**

### 1.5 An artifact I found, sized honestly, that cuts the RED's way — and is too small to matter

The Apps Business divestiture to Tripledot closed **2025-07-01** (Purchase Agreement 2025-05-07,
Amendment 2025-06-30, 8-K 2025-07-01). Post-close, the former in-house games portfolio's user-
acquisition spend converts from **eliminated intercompany** into **reported revenue** on installs
that were already in the denominator — mechanically inflating revenue-per-install with no economic
change. Direction favours the red's "the ratio is flattered" instinct.

Magnitude, from the primary note (Q2-26 10-Q, Note 12 *Related Party Transactions*):

> *"During the three and six months ended June 30, 2026, the Company recognized **$18.0 million** and
> **$42.9 million**, respectively, in revenue related to Tripledot and its subsidiaries' use of
> AppLovin Ads…"* (FY25 10-K Note 15: **$19.0M** from close through 2025-12-31.)

$18.0M is **0.94%** of Q2-26 revenue and ~1.4pp of the 53% y/y growth. Q2-25 was pre-close, so this
is structurally incremental — but it is **not** a material driver of a 58-point move. **Real
mechanism, immaterial magnitude. I raise it against myself and dismiss it on size.**

### 1.6 Ruling

**OVERTURNED as an interpretation. VERIFIED as data.** The five percentages are correctly quoted.
The claim that they establish a "decaying, arithmetically capped extraction lever on a shrinking
base" is not supported by the filings that produced them, is contradicted by the issuer's own
description of its pricing architecture and vertical mix, is internally inconsistent with the red's
own §1.5, and double-counts a single coupled variable whose net move was toward units.

---

## 2. KILL #2 — extraction vs efficiency — **RED WEAKENED; the discriminating evidence favours efficiency**

> RED: *"an advertiser pays more per install only while incremental installs still clear their return
> hurdle. It is an arithmetically capped lever."*

### 2.1 The pricing architecture is an ROAS-target auction — which inverts the red's logic

From the FY25 10-K, Item 1:

> *"**Advertisers set their goals and target return on ad spend and our algorithms adjust cost and
> campaign specifics to meet them.**"*
> *"**We generate revenue when our advertisers achieve their return on advertising spend targets**
> with our advertising solutions, ensuring that their success directly fuels our growth."*
> *"Reach: **Advertisers identify what they are willing to pay** to acquire their target users."*

Under a self-set-ROAS bidding architecture, **AppLovin cannot unilaterally raise revenue per install.**
If it charges above the advertiser's stated return target, the campaign stops clearing and the
budget leaves. Revenue per install can only rise **if the delivered value per acquired user rises** —
i.e. if targeting improved.

The red's own sentence concedes the mechanism but mislabels the ceiling. The binding constraint is
a **ratio** (ROAS), not a **level** (price). Better targeting → higher realised LTV per acquired
user → the *same* ROAS multiple supports a *higher* price. The ceiling is therefore total advertiser
budget, not an arithmetic cap on the ratio.

### 2.2 The agency accounting removes the "gross-up" escape

FY25 10-K Note 2: *"the Company is an agent in these arrangements and **presents revenue net of
advertising inventory costs**."* AppLovin's reported revenue **is** its net take. Net take per
install rose 58% y/y while total net revenue rose 53% — advertisers, who can leave at will
(*"Substantially all of the Company's contracts with customers are cancelable at any time"*, Note 2),
increased aggregate spend. Extraction against cancel-at-will counterparties producing +53% aggregate
spend is not a coherent story.

### 2.3 The company states the cohort mechanism the red says is undisclosed

Q2-26 10-Q, Item 2, *Factors Affecting Our Performance — Attract and retain clients*:

> *"**We rely on existing clients for a significant portion of our revenue. As we improve our
> advertising solutions, we can attract additional spend from these clients.**"*

That is management's stated growth mechanism: **existing-client budget expansion in response to
product improvement.** It is qualitative, not a quantified net-revenue-retention disclosure — so it
does not *prove* efficiency. But the red's framing implied no such disclosure exists.

### 2.4 The call record — the discriminating evidence the parent asked for

Management addressed cohort spend and churn directly. From the **official company-issued** Q1-26
transcript (2026-05-06, s21.q4cdn.com — higher authority than a third-party rendering):

> *"our business, as you know, as customers retain over time, the growth that will happen to the
> cohorts will be pretty material… **We almost never churned customers once they get through the
> first 30 days on our platform.** Right now, we're projecting well over $70,000 a year from every
> new customer."*
> *"…**customers almost never churn on our platform.** So it's our job to get them there… because,
> again, **we're selling profit to them.** So they launch, they see good return on ad spend out of
> the box… then they continue to invest in the platform."*
> *(on where growth comes from)* *"**it almost certainly is coming from the current existing customer
> base as they see the product improving.** … **we're always fixated on growth from current as the
> most important KPI**, and that's exactly what we're seeing as we improve the models."*

And Q4-25 (2026-02-11, official transcript): *"the current customers that had lapped Q4 2024 into
Q4 2025 saw **material increases in spend** as our models just keep getting better."*

**Two Q2-26 statements are the direct answer to "extraction or efficiency":**

> *"think of our consumer advertisers as… they're seeing really good ROAS, but **they're not even
> spending at their ceiling yet. We're not at a point where we have excess budgets to take out.**"*
> — Foroughi, 2026-08-05

> *"nothing we saw suggested weakening advertiser demand or a change in the competitive environment.
> In fact, **MAX publisher earnings grew double digits quarter-over-quarter, and our share of
> publisher waterfalls remained consistent.**"* — Foroughi, 2026-08-05

**The publisher datum is the strongest single item in this section, and it is the one an extraction
thesis has to beat.** AppLovin is an **agent**: its revenue is the spread between advertiser spend
and publisher payout. Extraction — widening that spread — shows up first as *compressing publisher
economics*. Management asserts publisher earnings grew **double digits sequentially** with
**waterfall share flat**. Rising publisher payouts and a rising take per install are hard to produce
simultaneously unless the underlying auction is delivering more value.

### 2.5 What remains genuinely UNVERIFIABLE — stated plainly

Every item in §2.4 is **unaudited management assertion on an earnings call**. There is **no**
disclosed net revenue retention, **no** churn rate, **no** cohort table, and **no** advertiser count
in any filing. The "$70,000 per new customer" figure is explicitly **forward-looking** (*"we're
projecting"*). Revenue is disaggregated **only by geography** (Q2-26: US $989.6M / RoW $934.1M; FY25:
US $2,827,248k / RoW $2,653,469k) — no product, vertical, or channel split anywhere.

**So the question cannot be closed from audited disclosure.** But it can be closed on the
*preponderance* of what exists: the pricing architecture (self-set ROAS targets), the agency
net-revenue presentation, cancel-at-will contracts, +53% aggregate net spend, the MD&A's stated
existing-client expansion mechanism, and management's on-record denial of excess budget extraction
plus rising publisher payouts **all point one way**, and nothing points the other.

### 2.6 Ruling

**OVERTURNED** (upgraded from my earlier WEAKENED after reading the call record). Efficiency is not
*proven* — it rests on unaudited assertion — but the red presented **extraction as established fact**
and there is **no affirmative evidence for it anywhere** in filings, transcripts, or third-party
data. An asserted mechanism with zero supporting evidence and six independent contra-indications
does not survive as a kill.

---

## 3. KILL #3 — the 84% margin is "a symptom, not a moat" — **RED WEAKENED**

> RED: *"serving 2% fewer installs at 58% higher revenue each mechanically expands margin without any
> efficiency gain… if revenue-per-install growth decays toward zero, margin compresses as fixed
> datacenter and engineering costs spread over a flat revenue base."*

Tested against XBRL (all figures `us-gaap` companyfacts, 10-Q filed 2026-08-05):

| | Q2-26 | Q2-25 | Δ |
|---|---|---|---|
| Revenue | $1,923,686k | $1,258,754k | +52.8% |
| Cost of revenue | $225,801k | $155,076k | **+45.6%** |
| R&D | $99,901k | $44,032k | **+126.9%** |
| GAAP operating income | $1,494,277k | $957,682k | +56.0% |
| **GAAP operating margin** | **77.68%** | **76.08%** | **+160bps** |
| Effective tax rate | 15.87% | 12.69% | **+318bps headwind** |

**GAAP operating margin expanded 160bps year-over-year while R&D grew 127% and SBC nearly doubled
($97.0M → $169.0M, H1 basis) — and while absorbing a 318bp higher tax rate.** That is the opposite
of a margin that exists only because units fell.

The red's compression mechanism also requires cost of revenue to be **fixed**. The 10-Q says it is
not: *"Cost of revenue consists primarily of datacenter costs related mainly to third-party [cloud]"*
— it grew +45.6% with revenue, i.e. it is variable.

**One item against my own case, which the red did not have.** The CFO disclosed on 2026-08-05 that
the Q3 guide is struck *"inclusive of… **the compute cost increase that we've seen**"* — and the Q3
adjusted-EBITDA margin guide is **83%**, down from 84–85% guided for Q2 and ~84% delivered in Q1.
**Management is guiding margin DOWN on rising compute cost.** That is a real, dated, forward margin
headwind and it is the best available support for the red's compression argument. It is ~100–200bps,
not a cliff — but it is directionally the red's point, sourced to the CFO.

**Ruling: WEAKENED, not overturned.** The red's *conditional* survives — if revenue-per-install
growth goes to zero on flat units, margins compress — and it now has a live compute-cost channel
behind it. But the conditional is downstream of Kill #1, and the realised data shows margin
**expansion of 160bps** through a 127% R&D ramp, which is the opposite of a margin that exists only
because units fell.

---

## 4. KILL #4 — "there was no beat" and the seasonally-matched guide math — **momentum math OVERTURNED; the broken beat-streak UPHELD**

This is where the red's strongest-looking quantitative work does not survive an apples-to-apples test.

### 4.1 The full guide-vs-print record — all primary, 8-K Ex-99.1 vs XBRL actuals

| Quarter | Guide range (8-K Ex-99.1, date) | Mid | Actual (XBRL) | **vs mid** |
|---|---|---|---|---|
| Q2-25 | $1,195–1,215 (2025-05-07) | 1,205 | 1,258.754 | **+4.46%** |
| Q3-25 | $1,320–1,340 (2025-08-06) | 1,330 | 1,405.045 | **+5.64%** |
| Q4-25 | $1,570–1,600 (2025-11-05) | 1,585 | 1,657.944 | **+4.60%** |
| Q1-26 | $1,745–1,775 (2026-02-11) | 1,760 | 1,842.449 | **+4.68%** |
| **Q2-26** | **$1,915–1,945 (2026-05-06)** | **1,930** | **1,923.686** | **−0.33%** |
| Q3-26 | $2,055–2,085 (2026-08-05) | 2,070 | — | — |

Accessions: `0001751008-25-000051`, `-25-000069`, `-25-000079`, `-26-000005`, `-26-000042`,
`-26-000057`. Actuals: `RevenueFromContractWithCustomerExcludingAssessedTax`, companyfacts API.

**Two readings, and both must be stated:**

**(a) CONCEDE — the streak broke, and that is genuinely informative.** Four consecutive quarters of
+4.46% to +5.64% above the midpoint is a near-mechanical guidance policy. Q2-26 at −0.33% is the
first break in the five quarters I verified from primary 8-Ks — and is reported in post-print
coverage as **the first time AppLovin has missed its own guidance midpoint since the IPO**
(SECONDARY, not independently verified beyond my five-quarter window). Against the company's *own
operating pattern* the shortfall is ~4.9% of revenue ≈ **~$95M**, not the ~$20M the consensus
comparison implies. **The red understated the disappointment while mislabelling its benchmark.**
(Secondary sources also disagree on the consensus itself — ~$1,940M per the red, ~$1,950M elsewhere;
the spread is immaterial to the ruling but the number is not firm.)

**(b) Revenue landed INSIDE the company's own guided range — but Adjusted EBITDA did NOT, and I am
correcting my own brief on this.** Revenue $1,923.686M sits at the **29th percentile** of
$1,915–1,945. **Adjusted EBITDA of $1,614M came in ~$1M BELOW the guided floor of $1,615–1,645M.**
The CEO said so himself on the call: *"we delivered almost $2 billion in revenue, which was **just
below the midpoint** of our guidance range, and our **Adjusted EBITDA was just below the range**.
We've always managed this business with the goal of outperforming our own expectations, and **this
quarter, we fell short of that standard**."* (Foroughi, 2026-08-05.)

So "delivered inside its own guidance" is true of revenue only. **On the profit line the company
missed its own floor, and management concedes the shortfall in its own words.** That is a real point
for the red that neither bench had, and it strengthens §4.1(a): the disappointment is against the
company's own commitment, not merely against a Street number.

**What still stands:** the Q3 guide range **brackets** the reported ~$2,080M consensus — its **high
end, $2,085M, is above consensus.** Characterising a range that contains the consensus as *"a
guide-down"* (red claim #2, "REFUTED") overstates it. The accurate statement is: *the Street modelled
the top of the range; the company delivered the lower-middle on revenue, missed the floor on EBITDA,
and guided a range around consensus.*

**And a structural feature of that guide that materially favours the long:** the CFO stated the Q3
number **excludes any model release not already shipped** —

> *"That outlook reflects the model improvements that are **already live and performing**… **It does
> not assume additional model releases that have not yet been deployed.**"* — Matt Stumpf, CFO,
> 2026-08-05

Against a five-quarter history of beating the midpoint by an average of **+4.85%**, a guide built
**only** on lifts already in production is structurally conservative. Foroughi also pre-committed
that the delayed upgrade *"landed just after quarter end"* and is *"now live"*, with *"Q3 off to a
strong start."* That is a dated, self-set falsification test (tripwire #2, §9.3).

### 4.2 The seasonally-matched sequential table compares a GUIDE to an ACTUAL

The red's §1.3 computes: Q2→Q3 step of +11.62% in 2025 vs **+7.61% guided** for 2026 = "65% of
prior-year momentum." **That compares this year's forecast against last year's outcome.** The
apples-to-apples comparison is guide-to-guide:

| Q2→Q3 step | Guided at the time | Realised |
|---|---|---|
| **2025** | 1,330 / 1,258.754 = **+5.66%** | 1,405.045 / 1,258.754 = **+11.62%** (2.05× the guide) |
| **2026** | 2,070 / 1,923.686 = **+7.61%** | *TBD* |

**Q3-26 is guided to a sequential step 1.34× larger than the step Q3-25 was guided to.** On the only
like-for-like basis available today, this is the **most aggressive Q2→Q3 guide in the observable
window** — not a deceleration to 65% of momentum. The red's 65% figure is an artifact of the
guide-vs-actual mismatch.

(Same test on the other steps — guided vs realised: Q4-25 +12.81% → +18.00% (1.41×); Q1-26 +6.16% →
+11.13% (1.81×); Q2-26 +4.75% → +4.41% (**0.93×**, the break).)

### 4.2b The cadence concession — **the RED was RIGHT and, if anything, UNDERSOLD it**

Two corrections, one procedural and one substantive.

**Procedural — the red quoted a paraphrase as verbatim.** Neither *"the pace of meaningful
advertising model improvement was lighter than normal during the June quarter"* nor *"no indication
of weaker advertiser demand or changes in the competitive landscape"* is what Foroughi said. Both are
MarketBeat's paraphrase, presented in the red brief inside quotation marks as the CEO's words. The
actual text (triangulated across three independent transcript renderings) is:

> *"**This quarter came down to timing.** Our pace of **meaningful model improvement** was lighter
> than normal **during the quarter**, and the next step up in model performance landed just after
> quarter end. Importantly, **nothing we saw suggested weakening advertiser demand or a change in the
> competitive environment.**"* — Foroughi, 2026-08-05

Note: AppLovin has **not** posted a company-issued Q2-26 transcript (only the webcast MP4), and the
"Financial Update" it posts is tables only with zero narrative. **All Q2-26 call quotes in both
briefs are third-party renderings.** The Q1-26 and Q4-25 transcripts *are* company-issued and are
higher authority.

**Substantive — the verbatim Q&A is MORE damaging than the red's paraphrase, and I uphold the kill
and strengthen it against my own side:**

> *"Look, **it's R&D, right? There's no guarantee that we're always going to have lifts in every
> single period of three months.** … We compound multiple small lifts. The impact was just smaller in
> Q2… **That's just the reality of when you're building models. You don't have a certainty on the
> impact of what you're testing. You're testing hypotheses hoping for a good result. The system is a
> whole bunch of A/B tests looking for lifts. There are going to be periods where we don't get
> material lifts.** There's going to be other periods where we have huge lifts that contribute to
> 12%, 13%, 15% quarter-over-quarter type quarters."* — Foroughi, 2026-08-05

**That is an explicit, on-record admission that quarters without material lifts are a recurring
expected state, not a one-off.** The red framed this as management conceding an R&D-shipping-schedule
dependence; the CEO went further and characterised the outcome distribution as **stochastic**. The
prepared remarks say *"this quarter came down to timing"*; the Q&A says there is *"no guarantee"* of
lifts in any given quarter. **The red's Kill on cadence dependence is UPHELD and I am upgrading its
force.**

The honest read of what this does and does not imply: it makes **quarterly revenue lumpy and
un-forecastable**, which fully justifies a lower multiple than a subscription annuity. It does **not**
imply the customer base is unstable — advertisers do not churn because a model shipped three weeks
late (§2.4). **A lumpy compounder is not a decaying one**, but it is worth less than the market paid
in December 2025, and the red is entitled to that point.

### 4.3 "Is the deceleration already paid for?" — the valuation test

At **$338.30**, diluted WA shares 337,031k (XBRL), 335M actually outstanding (8-K):

| Metric | Value | Basis |
|---|---|---|
| Market cap (diluted) | **$114.0B** | 337.031M × $338.30 |
| Net debt | **+$0.46B** | verified §0 |
| **Enterprise value** | **$114.5B** | |
| TTM revenue | **$6,829.1M** | Q3-25+Q4-25+Q1-26+Q2-26, summed from XBRL — independently ties to the $6,829M reported by Fiscal.ai |
| TTM P/E | **26.0×** | TTM EPS $13.01 |
| P/E on annualized Q2 EPS | 22.5× | the red's basis — the more generous of the two |
| EV / annualized Q3-guided EBITDA ($6.90B) | **16.6×** | |
| **FCF yield, H1-26 annualized** | **3.77%** | H1-26 FCF **$2,150,065k** (10-Q non-GAAP recon) × 2 = $4.30B |
| FCF yield, Q2-only annualized | 3.03% | the red's basis |

**A methodology note against the red:** it annualized **Q2 alone** ($863.3M × 4 = $3.45B, 3.0% yield)
without flagging that Q1-26 FCF was $1,286.8M and the H1 basis gives $4.30B (3.77%). Q2's softness
is a working-capital timing item (H1 *"Accrued and other liabilities (124,967)"*, cash-flow
statement), not a run-rate. **The red selected the lower of two available annualizations, unflagged.**

**The decisive framing — what perpetual growth the price requires.** At a 3.77% FCF yield and a 9%
cost of equity, the Gordon-implied perpetual FCF growth embedded in $338.30 is **≈5.2%, starting
now.** The market is not pricing "a fade to GDP-plus inside three years" (the red's read) — at this
price it is pricing **GDP-plus from today, forever**, against a company guiding **+47% y/y revenue**
with 83% EBITDA margins and negligible capex.

Three-scenario cross-check (9% CoE, 337.031M shares):

| Scenario | FCF path from $4.30B | Terminal | Value/sh |
|---|---|---|---|
| **Bear** — lever exhausts immediately | +20%, +8%, then 3% | 17× | **~$259** |
| **Base** — two more strong years, then fade | +35%, +20%, then 4% | 20× | **~$400** |
| **Bull** — mix rotation is real, 3 more years | +40%, +30%, +20%, then 4% | 20× | **~$490** |

At $338.30 the tape implies roughly **55% bear / 30% base / 15% bull**. Given that installation
volume closed 16 points of decline in one quarter and the Q3 sequential guide exceeds last year's
guided step, **a 55% weight on the immediate-exhaustion case is too heavy** — but it is not absurd,
and correcting it to ~35/40/25 gives a fair value of **~$373, i.e. ~+10% from the tape.**

**Ruling: the "no beat" headline is UPHELD but mis-benchmarked; the §1.3 momentum math is
OVERTURNED; the "deceleration is priced" conclusion is WEAKENED — the price requires only ~5%
perpetual growth, but the resulting edge is ~+10%, not a multiple.**

### 4.4 The reaction, sized

The 2026-08-06 move: $417.80 → $335.67 = **−19.66%** on 10.78M shares (2.4× the ~4.5M 20-day
average), closing near the low of $332.19 (IBKR daily bars, contract 481863646). That destroyed
**~$27.6B** of market value. Capitalizing the ~$95M quarterly shortfall-vs-pattern (§4.1a) at 83%
incremental margin and 16.6× EV/EBITDA gives **~$5.2B**. The tape took out **~5.3×** the
mechanically-capitalized shortfall. The excess is a **multiple de-rate on trajectory**, not a level
adjustment — which is exactly the red's thesis, and it stands or falls on Kill #1, which does not
stand. Note also the stock was already **−23.2% in the month into the print** ($543.79 on 07-06 →
$417.80 on 08-05); this was not a complacent setup being corrected.

---

## 5. KILL #5 — the CTO linkage — **WEAKENED on its own dates**

> RED (explicitly labelled as its own inference): *"The June quarter — the quarter management says had
> a 'lighter than normal' pace of model improvement — is precisely the CTO transition quarter."*

From the primary 8-K, filed 2026-04-07, acc. `0001751008-26-000014`, Item 5.02
(https://www.sec.gov/Archives/edgar/data/1751008/000175100826000014/app-20260402.htm): Basil Shikin
notified the company on **2026-04-02** that he would step down **effective 2026-07-01**, moving to
**Distinguished Engineer**.

Two problems with the inference:

1. **He was CTO for the entirety of the June quarter.** The transition took effect **2026-07-01** —
   the day *after* Q2-26 closed. The quarter the red attributes to a CTO transition was run by the
   same CTO who ran every prior quarter.
2. **He did not leave the company.** He moved to Distinguished Engineer, i.e. retained as an
   individual-contributor architect. The red's framing — *"the person who built the model stack
   departed"* — is not what the 8-K says.

The residual risk is real (an announced-then-transitioning executive may disengage; the Chief
Administrative & Legal Officer also retired effective 2026-08-01) and I do not dismiss it.

**Ruling: WEAKENED.** Legitimate as a risk to monitor; the specific timing linkage the red built is
contradicted by the effective date in the 8-K. The red labelled it as inference, which is to its
credit.

---

## 6. KILL #6 — the e-commerce disclosure asymmetry and the pixel stall — **substance UPHELD, support WEAKENED**

### 6.1 The grep was run against the wrong authority

The red searched the **Form 10-Q** for "pixel" / "merchant" / "self-service" and concluded from
0 hits that *"the company reports no merchant count, no pixel count… nothing."*

**A Form 10-Q has no Item 1 Business section.** Business-line strategy lives in the 10-K. Grepping a
quarterly report for a business-line KPI and inferring concealment is a method error. The FY25 10-K
discusses the vertical substantively:

> *"**New verticals:** One of our long-term objectives is to provide critical tools to advertisers
> across multiple verticals, including, for example, web-based e-commerce and social media. **We have
> made our advertising solutions available to web-based advertisers, and while we are early in this
> market expansion, our new customers have experienced positive results**, demonstrating the
> flexibility and future growth potential of our advertising solutions."* — Item 1, Growth Strategies

> *"…**including increased participation from large e-commerce advertisers**, the magnitude and
> impact of these seasonal trends may become more pronounced over time."* — Item 1, Seasonality

### 6.2 A factual error in the red's characterisation

RED: *"'e-commerce' — 8 hits, **all** in forward-looking/risk-factor boilerplate."*

I reproduced all 8 hits. **Hit #2 is in Item 2 MD&A, "Factors Affecting Our Performance"** — the
management discussion, not a risk factor and not the safe-harbour list:

> *"Our investments will also allow us to continue to enter into and expand into new verticals
> outside of gaming, such as e-commerce and CTV."*

"All boilerplate" is not accurate.

### 6.3 But the core of the flag survives, and I uphold it

There is genuinely **no merchant count, no pixel count, no e-commerce revenue split, no vertical
disaggregation** anywhere in the three filings. Revenue is disaggregated **only by geography**. For a
company whose multiple rests on non-gaming TAM expansion, that is a real gap and a legitimate
**REVIEW_FLAG**. The red is right about the *substance* of the asymmetry; its *support* was
mis-sourced and partly mis-stated.

I also checked the 8-K press release itself (Ex-99.1, acc. `0001751008-26-000057`): it is a bare
financial release — **zero** occurrences of "e-commerce", "merchant", "self-service", "advertiser",
"install", "retention" or "churn". It defers all commentary to a financial update posted on the IR
site. So the decomposition and the vertical commentary live **only** in the MD&A and on the call,
never in the release — which is the red's fair observation, and it applies symmetrically: the 8-K
carries no KPI in **either** direction.

Note the tension flagged in §1.3: this KPI gap is also what makes Kill #1 unfalsifiable in the
issuer's favour — neither bench can size the mix from disclosure. **That cuts both ways, and the red
took only the bearish side of an ambiguity it created.**

### 6.4 The BofA pixel note — **the "sole third-party measurement" claim is FACTUALLY WRONG**

> RED: *"the **only** independent read of that segment says it is decelerating… BofA (Omar Dessouky)
> found APP added ~750 new pixels in June vs ~950 in May, with merchant count stalled at ~8,300."*

The BofA note is verified: Omar Dessouky, 2026-07-13, ~750 June vs ~950 May pixel adds, ~8,300
merchants, estimates cut ~$130M (2026) / ~$255M (2027), **Buy and $705 PT maintained**
([coincentral, 2026-07-14](https://coincentral.com/applovin-app-stock-drops-13-after-bofa-flags-slower-e-commerce-growth/);
[finance.biggo, 2026-07-13](https://finance.biggo.com/news/5724e454-f710-498f-baa6-6185013987c9)).
Tape confirmed: $506.98 → $442.85 = −12.65%.

**But it was not the only read. On the same day, from the same vendor, Citi published the opposite
conclusion.**

Jason Bazinet (Citi), **2026-07-13**, headline *"Citi sees AppLovin US growth as solid"*:
**10,471 e-commerce clients** as of 2026-07-10, **+2.4% week-over-week**; 4,946 US stores, +1.3% WoW
([StreetInsider](https://www.streetinsider.com/General+News/Citi+sees+AppLovin+US+growth+as+solid/26761342.html);
[reportify](https://reportify.cn/reports/1274188827862372352)).

Two things break here:

1. **The counts are irreconcilable.** 8,300 (BofA) vs 10,471 (Citi) is a **26% gap** from the same
   nominal database — and 8,300 matches neither Citi's total nor its US subset (4,946). At least one
   desk is applying an undisclosed filter.
2. **+2.4% week-over-week compounds to roughly +10%/month.** That is not a stall.

**The market traded the bear framing of a number whose bull framing was published the same day.**
The red's §1.5 rests on "the sole third-party measurement contradicts it." There were two, they
disagreed by 26% on the level and in sign on the trend, and the red cited only the bearish one.

### 6.5 The measurement window is worse than "too short" — it is mostly PRE-launch

Self-service Axon opened to all e-commerce advertisers **2026-06-22**. BofA's figure is a **June
monthly** pixel count, so it contains only **~8 days** of post-launch data — **~27% of the month.**
The May-vs-June comparison is very largely a **pre-launch vs pre-launch** comparison. Dessouky's own
caveat was *"no clear jump in weekly data since"* launch — measured over ~3 weeks — and he noted
that **both installs and uninstalls rose** in the first week, the signature of advertiser **testing**,
not rejection.

**The vendor is measuring the wrong population.** The underlying data is **Store Leads**
(storeleads.app), a **Shopify-centric** storefront crawler doing browser-side technology detection.
Three structural limits: it sees only crawlable **Shopify** storefronts (missing
BigCommerce/WooCommerce/custom/enterprise); it detects only **browser-side pixels** (missing
server-side/CAPI and API integrations); and it counts **merchants, not dollars** — an 8,300-merchant
base can be economically trivial beside a handful of large accounts. Dessouky's earlier note
described his sample as *"smaller Shopify stores, not large Shopify Plus brands."*

Management stated on 2026-08-05 that the rollout *"was not intended to transform the business
immediately"* and that the strategy is **mid-market e-commerce via partnerships (e.g. Triple Whale)**
— explicitly **not** broad long-tail SMB outreach. **If AppLovin is deliberately not chasing
long-tail Shopify SMBs, a long-tail Shopify pixel crawl cannot measure its e-commerce ramp.**

### 6.6 A quantified e-commerce datapoint does exist — and it is management's, unaudited

On the Q2-26 call Foroughi stated e-commerce advertiser spending *"set another record and finished
**28% above fourth-quarter 2025 levels**"* — i.e. the vertical grew **through exactly the window BofA
called stalled** ([MarketBeat, 2026-08-05](https://www.marketbeat.com/instant-alerts/applovin-q2-earnings-call-highlights-2026-08-05/)).

**I discount this appropriately:** it is unaudited management commentary on an **undefined base**,
over a **two-quarter** span (≈13%/qtr), it appears in **no filing**, and "record" is trivially true
for a growing line. It does **not** close the KPI gap. But it does mean the red's *"the company
provides zero measurable disclosure"* overstates the vacuum, and it is directional evidence against
the stall.

**Ruling on Kill #6: substance UPHELD (the KPI gap is real and is a legitimate REVIEW_FLAG);
the evidentiary support is OVERTURNED** — the "sole independent measurement" was one of two
same-day, same-vendor reads that disagreed by 26%, taken over a window that was ~73% pre-launch,
from a crawler pointed at a population management says it is not targeting.

---

## 6B. THE META ADVANTAGE+ LEG — **NARRATIVE, NOT EVIDENCE; OVERTURNED**

The red's drawdown table attributes the 2026-02-12 −19.7% leg to *"Cited driver: Meta competitive
threat"* and grades it **"Structural."** I asked for dated evidence of actual gaming-budget loss.
There is none, and the named, dated evidence runs the other way.

**Meta's own Q2-26 call (2026-07-29) is silent on gaming.** I had the official transcript PDF
downloaded and keyword-counted
([s21.q4cdn.com](https://s21.q4cdn.com/399680738/files/doc_financials/2026/q2/META-Q2-2026-Earnings-Call-Transcript.pdf)):

| Term | Occurrences in Meta Q2-26 transcript |
|---|---|
| gaming | **0** |
| game / games | **0** |
| AppLovin | **0** |
| app install / mobile app promotion | **0** |
| Advantage | 13 — **all** e-commerce/SMB-framed |

Meta's disclosed Advantage+ figure (>$75B annual run-rate) and its sole case study (an online
apparel brand) are **e-commerce**. If there is a Meta collision, the evidence points at APP's *new*
vertical, not its *gaming core* — the inverse of the claim.

**The industry-standard gaming index shows APP gaining and Meta absent.** AppsFlyer Performance
Index, 2025 edition, published **2025-12-03**
([appsflyer.com](https://www.appsflyer.com/company/newsroom/pr/performance-index-2025/)): on iOS
gaming, *"**AppLovin narrowing the gap and leading in tier one North America and Western Europe**"*;
on Android gaming, *"**AppLovin**, Mintegral, and rewarded platforms such as adjoe **posted major
gains**."* **Meta Ads does not appear in the gaming rankings at all** (it appears only in
non-gaming).

**Channel checks run the opposite direction.** FundAI, **2026-05-04**, *"No META Impact Observed"*:
an agency source *"has **not** seen advertisers shifting toward META; instead, it sees **more META
budget rotating into AppLovin**"*
([fundaai.substack.com](https://fundaai.substack.com/p/previewapp-1q26-no-meta-impact-observed)).
A Jefferies Q2-26 survey called APP *"the standout winner in budget allocation shifts,"* with budget
moving **from** Meta and Google.

**The 2026-02-12 leg had a different, verifiable cause.** Tape confirmed: $456.81 → $366.91 =
−19.68%. Q4-25 was a genuine beat (revenue $1.66B, +66%; record 84.4% adj. EBITDA margin). What
broke the stock was the **Q1-26 guide of $1,745–1,775M — only ~5–7% sequential growth — against a
stock at >30× price-to-sales**
([Observer-Reporter, 2026-02-12](https://stocks.observer-reporter.com/observerreporter/article/marketminute-2026-2-12-ad-tech-giant-applovin-faces-priced-for-perfection-reckoning-as-shares-plunge-20)).
The Meta claim appears in that coverage only as *"reportedly… analysts"* — **unnamed, undated, no
data**. I could not find **a single named analyst at a named firm on a dated note** attributing that
move to Meta/Advantage+. **UNVERIFIABLE.**

**And the narrative already round-tripped once.** After the 2026-02-12 crash to $366.91, APP
recovered **+67.3% to a $613.70 peak on 2026-06-01** before rolling over. A thesis the tape refuted
within four months, being recycled, needs a higher bar than "reportedly."

Note also the 10-Q lists **Meta as both a competitor and a paying AppLovin advertising client**
(*"clients include… some of the largest global internet platforms, such as Meta and Google"*).

**Ruling: OVERTURNED.** The red graded this leg "Structural" on an unattributed press paraphrase.

### 6B.1 — BUT: the strongest version of the RED case is now on the record, named and dated

I will not let my own finding hide this. **Wells Fargo, 2026-08-06, downgrade to Equal Weight,
PT $357:** *"mobile-gaming market share is **plateauing** and growth will increasingly depend on
**take-rate expansion**."*

That is a named, dated, professional statement of **exactly the red's Kill #1** — and it is a
**saturation** argument, which is materially stronger than the share-loss-to-Meta argument the red
actually pleaded. It is the best evidence against my §1, and the court should weigh it. The
distinction matters: *saturation* (APP has already taken most of the takeable gaming share) is
survivable via mix rotation into web/CTV; *share loss to Meta* is not. **The red pleaded the weaker
of the two and mislabelled its evidence.**

### 6B.2 — Post-print sell-side, which cuts against the red's "stale targets" point

RED: *"sell-side targets ($550–$640) are stale relative to a $340 tape — so the 'cheap vs consensus'
support is circular."*

The targets were re-cut on **2026-08-06**, the day after the print: BofA **$705 → $430** (Buy
maintained); Jefferies $700 → $550; BTIG $640 → $574; **Piper Sandler downgrade to Neutral, PT
$385**; **Wells Fargo downgrade to Equal Weight, PT $357**.

**Both fresh downgrades still carry targets above the tape** ($385 and $357 vs $338.30). The
"stale marks" objection is weaker after the re-cut: the most bearish, freshly-published, post-print
professional marks sit **+5.5% to +13.8%** above where the stock trades. That is not proof of value —
sell-side targets rarely go below spot — but it removes the red's specific staleness argument.
**WEAKENED.**

---

## 7. KILL #7 — "no informational edge, saturated mega-cap" — **UPHELD IN FULL, and it binds my recommendation**

> RED: *"this is a $115B mega-cap with ~40 analysts… A long here is a bet that a saturated consensus
> has mis-modelled a ratio printed in the MD&A. That is not an edge; it is a view."*

**I concede this entirely and it is the most important thing the red wrote.** Nothing in §§1–6 is
non-public. The mix-contamination argument is available to any analyst who reads Note 2 of the 10-K.
Under the conditioning layer this name is **DISCOVERED/CROWDED**: ~40 covering analysts, 10.8M shares
on the print, saturated sell-side.

What §§1–6 establish is **not an information edge**. It is:
1. an **interpretation disagreement** about an under-identified ratio, and
2. a **valuation/dislocation** condition — a −19.7% single-day move that capitalized a ~$95M
   shortfall at ~5.3× its mechanical value, on top of a −23% month.

Per the standing framework, that is **RP_FAIR / valuation**, not EDGE. It is ownable — fairly-paid
risk does not require an edge — but it must be **sized as a valuation position, not an alpha
position.** This is why my recommendation below is a starter and not a core, notwithstanding that I
believe the central kill is wrong.

---

## 8. PER-KILL RULING TABLE

| # | RED kill | Attack | Ruling |
|---|---|---|---|
| **1** | Units→price inversion; growth is a capped, decaying extraction lever | Issuer states installs are **not** the pricing unit (10-K Item 1; 10-Q Item 2); revenue recognised on **impression-based AND action-based** arrangements (Note 2); **"installation" is never defined in any filing**, no attribution-methodology disclosure exists, and the metric's label changed Axon Ads Manager→AppLovin Ads between Q1 and Q2. Decisive: management's own cause for falling installs is an **intra-gaming hyper-casual→mid-core shift** — *"a much higher CPI and a much higher LTV… as the cost goes up, it does not mean that the value goes down"* — i.e. **the unit itself changed**. Numerator/denominator are one coupled variable whose product barely moved (1.583→1.548). **My own mix-shift argument is CORRECTED and bounded** (§1.2b): CTV/open-web are roadmap not run-rate, gaming is still the majority | **OVERTURNED** (interpretation) / data VERIFIED |
| **2** | Extraction, not efficiency | ROAS-target self-set bidding; **agent/net** presentation; cancel-at-will contracts; +53% aggregate net spend; MD&A existing-client expansion. **New from the call:** *"they're not even spending at their ceiling yet. We're not at a point where we have excess budgets to take out"*; *"we almost never churned customers once they get through the first 30 days"*; *"we're selling profit to them"*; and the decisive supply-side check — ***"MAX publisher earnings grew double digits quarter-over-quarter, and our share of publisher waterfalls remained consistent."*** Extraction by an **agent** compresses publisher economics; these did the opposite. All unaudited, but **zero affirmative evidence exists for extraction** | **OVERTURNED** (upgraded) |
| **3** | 84% margin is a symptom of falling units, not a moat | GAAP op margin **+160bps y/y** (76.08%→77.68%) *while* R&D +127%, SBC ~2×, tax +318bps; cost of revenue **variable** (+45.6%). **Against me:** CFO guides Q3 margin **down to 83%** (from 84–85%) on a disclosed **compute cost increase** — a live channel for the red's compression case | **WEAKENED** |
| **4a** | "There was no beat" | Correct vs Street (secondary). **Correction against my own brief:** revenue landed inside the guided range (29th pct) **but Adjusted EBITDA of $1,614M came in ~$1M BELOW the $1,615–1,645M floor**, and the CEO conceded *"this quarter, we fell short of that standard."* The true shortfall vs the company's own 5-quarter pattern is **~$95M, not ~$20M** — the red understated its own best fact. **But** the Q3 guide range **brackets** consensus (high end $2,085M above it), so "guide-down" still overstates | **UPHELD and STRENGTHENED for the red** |
| **4e** | Growth tracks a discrete internal model-release cadence | **RED UPHELD AND UNDERSOLD.** Verbatim Q&A is worse than the paraphrase the red quoted: *"it's R&D, right? **There's no guarantee that we're always going to have lifts in every single period of three months**… **There are going to be periods where we don't get material lifts.**"* An explicit admission the outcome distribution is **stochastic**, not a one-off. *(Procedural: both of the red's quoted "Foroughi" lines are MarketBeat paraphrases, not verbatim — corrected in §4.2b. AppLovin has issued no Q2-26 transcript.)* | **UPHELD, upgraded** |
| **4b** | Q3 guide = only 65% of prior-year momentum | Compares this year's **guide** to last year's **actual**. Guide-to-guide: Q3-25 guided +5.66% (realised +11.62%); Q3-26 guided **+7.61%** = **1.34× the prior-year guided step** — the most aggressive Q2→Q3 guide in the window | **OVERTURNED** |
| **4c** | Beat-streak broke in Q2-26 | Verified: +4.46 / +5.64 / +4.60 / +4.68 / **−0.33%**. First break in five quarters. Real and informative | **UPHELD** (red's strongest surviving fact) |
| **4d** | Deceleration is correctly priced at 16.6× | Price implies only **~5.2% perpetual FCF growth from today** (3.77% H1-annualized FCF yield, 9% CoE) against +47% guided growth; red used the **lower** of two FCF annualizations unflagged. Corrected scenario weights give ~$373 FV, **~+10%** | **WEAKENED** |
| **5** | CTO transition is a structural competing explanation | 8-K: effective **2026-07-01**, i.e. he was CTO for **all** of the June quarter; and he **stayed** (Distinguished Engineer), did not depart | **WEAKENED** |
| **6a** | Zero e-commerce KPIs in company disclosure | Grep run against a **Form 10-Q, which has no Item 1 Business**; the 10-K discusses the vertical substantively; "all 8 hits boilerplate" is **factually wrong** (hit #2 is MD&A). **But** no merchant/pixel/vertical split genuinely exists — revenue disaggregated **by geography only** | **UPHELD in substance / WEAKENED in support** |
| **6b** | "The **sole** third-party measurement says the ramp stalled" | **Factually wrong.** Citi (Bazinet) published **the same day, 2026-07-13, from the same vendor (Store Leads)**: 10,471 clients, **+2.4% WoW** (≈+10%/mo), *"growth as solid."* The two reads differ **26% on the level** and **in sign on the trend**. BofA's June figure contains only **~8 days post-launch** (self-service opened 06-22) — the comparison is ~73% **pre-launch vs pre-launch**. Vendor is a **Shopify long-tail crawler**, browser-side pixels only, counting **merchants not dollars** — and management says its target is **mid-market via partnerships, not long-tail SMB** | **OVERTURNED** |
| **6c** | Meta Advantage+ took gaming budget (red's cause for the 2026-02-12 −19.7% leg, graded "Structural") | Meta's own Q2-26 transcript: **gaming = 0 mentions, AppLovin = 0, app-install = 0**; all 13 "Advantage" mentions e-commerce. AppsFlyer Performance Index 2025: APP *"narrowing the gap and leading tier-one NA/W-Europe"*, **Meta absent from gaming rankings**. Channel checks show budget rotating **into** APP. The 02-12 leg's verifiable cause was the **Q1-26 guide of only ~5–7% sequential growth at >30× P/S**. No named/dated analyst ties it to Meta — **UNVERIFIABLE** | **OVERTURNED** |
| **6d** | Sell-side targets are stale, so "cheap vs consensus" is circular | Targets re-cut 2026-08-06: BofA $705→**$430**, Jefferies →$550, BTIG →$574, Piper **downgrade** →$385, Wells Fargo **downgrade** →$357. **Both fresh downgrades sit above the tape** (+5.5% / +13.8% vs $338.30) | **WEAKENED** |
| **6e** | *(strongest surviving bear evidence, found by me, against my own case)* | **Wells Fargo, 2026-08-06:** *"mobile-gaming market share is **plateauing** and growth will increasingly depend on **take-rate expansion**."* A named, dated professional statement of the red's Kill #1 — and a **saturation** argument, stronger than the Meta argument the red actually pleaded | **CORROBORATES RED** |
| **7** | No informational edge; crowded mega-cap | Conceded in full. Everything here is public. This is interpretation + dislocation, i.e. **RP_FAIR**, not EDGE | **UPHELD** |
| **—** | Net debt ~$462M, not net cash | Independently re-verified from XBRL | **UPHELD** |
| **—** | Buyback ~32.5% underwater; ~$3.7B for ~1.4% share reduction | Independently re-verified | **UPHELD** |

---

## 9. BLUE BENCH — NET: **RED CASE WEAKENED**

**Not UPHELD, and not OVERTURNED.** The red reached a defensible destination on broken roads.

**What broke.** The load-bearing kill — that AppLovin's growth is "essentially 100% extraction per
install," an arithmetically capped lever decaying on a shrinking base — **requires "installation" to
be a stable unit of account, and it is not.** The term is **never defined in any filing**; no
attribution methodology is disclosed; the metric's stated referent was renamed mid-series; revenue is
recognised on **both** impression-based and action-based arrangements so the denominator does not
span the numerator; and management's own explanation for the volume decline is an **intra-gaming
shift from hyper-casual to mid-core** — *"a much higher CPI and a much higher LTV… as the cost goes
up, it does not mean that the value goes down"* — which produces the identical signature with **zero
extraction**. The pair is also one coupled variable: the product barely changed (1.583 → 1.548).
Supporting kills fell with it: the "65% of prior-year momentum" figure compares a **guide to an
actual** (guide-to-guide, Q3-26 is the **most aggressive** Q2→Q3 guide in the window); the "sole
third-party measurement" was **one of two same-day, same-vendor reads that disagreed 26% on level and
in sign on trend**, over a window ~73% pre-launch, from a Shopify long-tail crawler pointed at a
population management says it is not targeting; the Meta leg is **unattributed press paraphrase**
contradicted by Meta's own transcript and the industry gaming index; and the CTO linkage is
contradicted by the 8-K's own effective date. On extraction specifically there is **no affirmative
evidence anywhere**, against six contra-indications including the decisive one for an *agent*:
**publisher earnings grew double digits sequentially with waterfall share flat.**

**Where I corrected myself.** My mix-shift argument (§1.2) was **too strong** and I bounded it in
§1.2b: CTV and open-web supply are **roadmap, not run-rate** (*"we're just not at the point yet where
we can go execute on it"*), and gaming is still the majority of revenue. The overturn does not need
it — it rests on the undefined, non-constant unit instead. I also **missed that Adjusted EBITDA came
in below its guided floor** ($1,614M vs $1,615–1,645M), which strengthens the red.

**What survived, and it is not trivial.** (1) The **guidance-beat streak genuinely broke** — +4.46 /
+5.64 / +4.60 / +4.68%, then **−0.33%** — EBITDA **missed its floor**, and the CEO conceded *"we fell
short of that standard."* The true shortfall vs the company's own pattern is **~$95M, not ~$20M**;
**the red understated its own best fact.** (2) The **cadence concession is upheld and I upgraded it
against my own side** — the verbatim Q&A (*"there's no guarantee that we're always going to have
lifts in every single period of three months… there are going to be periods where we don't get
material lifts"*) admits a **stochastic** outcome distribution, not one-off timing. That justifies a
structurally lower multiple than an annuity. (3) **Net debt ~$462M**, correctly caught. (4) Buyback
~32.5% underwater; ~$3.7B for ~1.4% of net share count. (5) The **e-commerce KPI gap is real** —
geography-only disaggregation, an explicit standing refusal to break out verticals (*"we're not going
to do that"*), and a direct on-call refusal to give an advertiser count — and that vacuum is exactly
what let a contradictory vendor crawl move the stock 12.6% in a day. (6) **Wells Fargo (2026-08-06)
puts a named, dated, professional version of the red's thesis on the record** — *"mobile-gaming market
share is plateauing and growth will increasingly depend on take-rate expansion"* — a **saturation**
argument stronger than the Meta argument the red pleaded, which nothing here refutes. (7) The CFO
guides **margin down to 83% on rising compute cost.** (8) And the red's **secondary kill is correct
in full**: ~40 analysts, nothing non-public, the "edge" is interpretation plus dislocation. **That is
RP_FAIR / valuation, not EDGE — and it is the binding constraint.**

**BLUE CONVICTION: 6/10** — that the correct disposition is a small, price-gated starter rather than
a reject. Held at 6 after the call record: Kill #2 upgraded to overturned in my favour, but the
cadence admission, the EBITDA floor miss, and the compute-cost margin guide all moved against me. The
name is a **lumpy compounder, not a decaying one** — but lumpy is worth less than December 2025 paid,
and the unrefuted saturation case caps conviction.

### 9.1 What is actually on offer

At **$338.30** the price embeds ≈**5.2% perpetual FCF growth from today** (3.77% H1-annualized FCF
yield, 9% CoE) against a **+47% guided** year. Three-scenario fair value **$259 / $400 / $490**; the
tape implies roughly **55/30/15**. Correcting the bear weight for the fact that installation volume
closed 16 points of decline in one quarter and the Q3 sequential guide **exceeds** last year's guided
step gives ~**35/40/25** → FV ≈ **$373, ~+10%**. That is a real but thin edge on a name with 64%
annualized IV. **It justifies a starter, not a core, and certainly not a table-pound.**

### 9.2 RECOMMENDED ACTION at live $338.30

**Classification: RP_FAIR (valuation / dislocation), with a small interpretation overlay. NOT an
information edge.** APP is **not currently held** (positions polled 2026-08-07).

**Do not reject; do not size to a core. Open a STARTER via a GTC limit ladder BELOW the tape.**

Per the response taxonomy, a valuation finding gets a **price gate** — the only case where that is
the correct instrument. Reasons not to pay up on day 2: the stock closed near its low on **2.4×**
volume on 2026-08-06; the 52-week low ($332.19) is 1.8% below the tape; and the decisive datum is
**~90 days out**.

| Tranche | Limit | Weight | Rationale |
|---|---|---|---|
| 1 | **$325** | 40% | below the 52-wk low — requires a fresh break, not a bounce |
| 2 | **$302** | 35% | ~−11% from tape; mid-point of base-vs-bear |
| 3 | **$278** | 25% | approaches the bear FV ($259); only fills if the saturation case is winning |

Weighted average if fully filled ≈ **$305**, which lifts expected value to ~**+22%** against the
$373 base — a properly compensated entry rather than a thin one. **Total starter size ≈ one-third of
a normal position** (order of ~$12k / ~38 shares on this book's scale), sized as fairly-paid risk,
sleeve-capped, unlevered.

**No premium selling.** At 64% annualized IV a cash-secured put is the tempting instrument and it is
**forbidden** in this taxable book — CSP/CC premium is non-deferrable short-term ordinary income at
~50%+. The GTC ladder achieves the same entry economics without the tax leak.

### 9.3 Tripwires — dated and falsifiable

| # | Trigger | Threshold | Date |
|---|---|---|---|
| **1** | **The decisive one — read the PAIR, not the ratio.** Q3-26 10-Q MD&A | **Mix rotation CONFIRMED → add to full size:** volume ≥ 0% y/y **and** rev/install ≥ +40%. **Saturation CONFIRMED → exit:** **both** decelerate — volume worse than −5% **and** rev/install below +40% (i.e. total growth < ~+33%). **Trap to avoid:** volume falling *further* while rev/install *re-accelerates* is **also** mix rotation, more aggressive — do not misread it as extraction | ~early Nov 2026 |
| **2** | Q3-26 revenue vs the guide | **≥ $2,085M** (guide high) restores the 5-quarter beat pattern → thesis intact. **< $2,055M** (guide low) → **reverse tripwire, exit.** Management pre-committed on the 08-05 call that the next model upgrade is live and *"contributed to a strong start to the third quarter"* — a clean, self-set falsification | ~early Nov 2026 |
| **3** | Model-cadence language recurs | If Q3 commentary again cites a *"lighter than normal"* improvement pace, cadence-dependence is **structural, not timing** → **exit regardless of the print** | ~early Nov 2026 |
| **4** | Third-party pixel/merchant data | Demand **both** the BofA and Citi series before acting. A single-desk read off a Shopify long-tail crawler is **not decision-grade** and has already moved this stock 12.6% in a day on a number whose bull framing published the same morning | rolling |
| **5** | Company begins disclosing an e-commerce KPI | Merchant count, vertical revenue split, or any non-gaming cohort in the Q3-26 10-Q → removes the §6 asymmetry and makes the growth vector testable → re-rate | ~early Nov 2026 |
| **6** | Capital allocation | Buyback pace cut, net debt eliminated, or credible insider **buying** on Form 4 | any |

### 9.4 Handoff note

This is a **bench brief, not an adjudication.** The court ledger write — ledger upsert,
`edge_classification` (proposed: **RP_FAIR**, not EDGE), `entry_plan` (the §9.2 ladder), scanner
re-run and `/api/everything` verification — belongs to the **adjudicating step**, not to either
bench, and is **owed**. Flagging explicitly so it is not dropped.

---

*Prepared under prosecution posture: each RED kill was attacked and had to survive. Live price from
IBKR at time of writing. All financial claims bound to SEC primary filings (10-K acc.
`0001751008-26-000010`; 10-Q acc. `0001751008-26-000044` and `0001751008-26-000059`; 8-K Ex-99.1
acc. `0001751008-25-000051`, `-25-000069`, `-25-000079`, `-26-000005`, `-26-000042`, `-26-000057`;
8-K Item 5.02 acc. `0001751008-26-000014`) and the XBRL companyfacts API. **Session web-search
budget was exhausted (200/200)**, so consensus figures and third-party analyst data remain SECONDARY
and are labelled as such wherever used.*

**Transcript-authority caveat, applying to BOTH benches.** AppLovin has **not** issued a Q2-26
transcript — only the webcast MP4 — and the "Financial Update" it posts
([s21.q4cdn.com/…/Financial-Update-Q2-2026.pdf](https://s21.q4cdn.com/165405286/files/doc_financials/2026/q2/Financial-Update-Q2-2026.pdf))
is **tables only, zero narrative**. Every Q2-26 call quote in either brief is a **third-party
rendering**; the load-bearing ones here were triangulated across three independent transcripts
(Yahoo timestamped, AlphaStreet, MarketBeat) and agree verbatim. The **Q1-26 (2026-05-06)** and
**Q4-25 (2026-02-11)** transcripts *are* company-issued and carry higher authority — the retention
and cohort quotes in §2.4 come from those. Before any capital decision the Q2 quotes should be
audio-verified against the MP4
([2026-Q2-Earnings-Call-w-QandA-02-Final-720.mp4](https://s21.q4cdn.com/165405286/files/doc_financials/2026/q2/2026-Q2-Earnings-Call-w-QandA-02-Final-720.mp4)).
All management commentary cited is **unaudited assertion**, not filing disclosure, and is labelled as
such throughout.
