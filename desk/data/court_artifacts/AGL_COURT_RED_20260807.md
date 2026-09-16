# AGL — agilon health, inc. · RED BENCH (Fable tier) · default-REJECT the LONG

**Run date:** 2026-08-07 · **CIK** 0001831097 · **NYSE: AGL** · conid 866485437
**Posture:** adversarial. The long must clear the bar; silence is a REJECT.
**Referred from:** `VELOCITY_20260806_REFUTABILITY_20260807.md` §7, triage 7/10 DAMAGE-ARRIVING + masking flag.

**Session constraint (declared up front):** the WebSearch budget for this session was exhausted
(200/200) before this court opened, and cms.gov returned HTTP 403 to direct fetches. **No sell-side
consensus, no CMS CY2027 Rate Announcement, and no Q2 earnings-call transcript was read.** Every
finding below is sourced to EDGAR primary documents or IBKR bars. Where a question could not be
closed, it is marked **UNVERIFIABLE — which is not the same as clean.**

---

## 0. Verdict in one paragraph

The triage's headline catch — "Raises Guidance" sitting on an implied negative H2 — is **arithmetically
correct but analytically wrong as a masking finding**, and this court **overturns it**. The negative H2
was already embedded in the *prior* guide (implied H2 of −$48.8M in May), the forward half actually
**improved by $10.4M**, and H2-worse-than-H1 is this company's shape in **every year 2022-2025** by an
average of −$180M. That is claims-completion mechanics, not a new break.

But the long still fails, on grounds the triage did not reach. **~32% of the raised FY26 EBITDA guide
comes from a CMS program that agilon's own 10-K says terminates on 2026-12-31**, whose successor has
undefined economics and which agilon has not committed to joining — a fact the "Raises Guidance"
release does not mention once. And the H1 that produced the raise **consumed $99.5M of unrestricted
liquidity**. That is the real takeaway-vs-data divergence, and it is not priced.

---

## 1. Mode B — first principles, no promoter framing

Four questions I would ask if I had never seen the release:

1. What does this business earn in a year in which no prior-period reserve releases run through it?
2. Of the FY26 EBITDA guide, how much survives into FY27 as a matter of contract and statute?
3. Does the cash agree with the profit?
4. Is the price a dislocation or a de-crowding?

Answers, in order: **unknown — the company won't quantify it** (§3); **roughly two-thirds, and the
missing third has a hard statutory expiry** (§5); **no, and the gap is widening** (§6); **a de-crowding**
(§7). Only one of those four is a company-disclosed number.

---

## 2. Mode A — claim ledger

Format: **{claim | source | method | result | verdict}**. All dollar figures as filed.

### 2.1 The arithmetic the triage ran

| # | Claim | Source | Result | Verdict |
|---|---|---|---|---|
| 1 | Q2-26 Adjusted EBITDA $70M | 8-K 2026-08-05, acc. `0001628280-26-053328`, Ex-99.1 | $69,571k exactly | **VERIFIED** |
| 2 | H1-26 Adjusted EBITDA $124M | same Ex-99.1, six-month column | $123,410k; Q1 derived = $53,839k | **VERIFIED** (triage rounding fair) |
| 3 | FY26 guide raised to $75–95M from $10–40M | Q2 Ex-99.1 guidance table vs Q1 Ex-99.1 (acc. `0001628280-26-031254`) | confirmed both endpoints | **VERIFIED** |
| 4 | Implied H2-26 Adjusted EBITDA = −$49M to −$29M | subtraction from #2, #3 | $75−123.4 = −$48.4M; $95−123.4 = −$28.4M | **VERIFIED** |
| 5 | Q3-26 guided Adjusted EBITDA −$5M/+$5M vs $70M in Q2 | Q2 Ex-99.1 Q3 guidance table | confirmed | **VERIFIED** |
| 6 | Members 549,000, −10% y/y; MA 437,000, −12% | Q2 Ex-99.1 metrics table; 10-Q p. "Overview" (437,500 / 112,200) | confirmed | **VERIFIED** |
| 7 | Second consecutive "Raises Full-Year… Guidance" headline | Q1 Ex-99.1 title line vs Q2 Ex-99.1 title line | both carry it verbatim | **VERIFIED** |
| 8 | Reverse split occurred in 2026; ratio unverified by triage | 10-Q Note 1 and MD&A "Recent Developments"; 8-K 2026-03-30 acc. `0001628280-26-022074` | **1-for-25**, effective 2026-03-30 | **VERIFIED — triage gap closed** |
| 9 | 16.785M shares; cash+securities $257M; debt $32M | Q2 Ex-99.1 balance sheet | 16,785k shares; $257.25M; term loan $31.5M | **VERIFIED** |

### 2.2 Claims the triage did not test — where the case actually turns

| # | Claim | Source | Result | Verdict |
|---|---|---|---|---|
| 10 | "The forward half is guided to a LOSS" is *new* damage | Q1 Ex-99.1 guidance table, arithmetic in §3 | H2 was implied at **−$48.8M in May**; it is now **−$38.4M**. Forward half **improved $10.4M** | **REFUTED** |
| 11 | H2-negative is genuinely seasonal, not deterioration | XBRL `NetIncomeLoss` quarterly, 2022–2025 (companyconcept API) | H2 worse than H1 in **4/4 years**: −$67.8M, −$261.2M, −$186.6M, −$206.7M. FY26 implied swing −$162M is **inside** and better than the 3-yr mean | **CONFIRMED — seasonal by construction** |
| 12 | ACO REACH contributes $25–30M of the FY26 guide | Q2 Ex-99.1 footnote 3 to guidance table | confirmed; = **26–40% of the guide, 32% at midpoints** | **VERIFIED** |
| 13 | ACO REACH terminates 2026-12-31 | **10-K FY2025, filed 2026-02-25, acc. `0001628280-26-011655`**, Business + Risk Factors | *"CMS has announced that the ACO REACH Model will terminate at the end of 2026, and will be replaced by the Long-term Enhanced ACO Design ('LEAD') Model beginning on January 1, 2027… many unknowns… which will have a significant impact on whether agilon will participate in the model."* | **VERIFIED — and omitted from the Q2 release entirely** |
| 14 | ACO segment economics are improving | 10-Q Note 12, combined ACO operating results | Q2 revenue $379.3M vs $434.8M (−12.8%); Q2 **net loss −$7.59M vs +$5.40M**; H1 net income **$4.07M vs $18.07M (−77%)** | **REFUTED — deteriorating** |
| 15 | "Medical margin includes favorable… claims development" | Q2 Ex-99.1 bullet; 10-Q MD&A | Direction disclosed. **Magnitude never quantified anywhere in the 8-K or the 10-Q** | **UNQUANTIFIED — see §3.3** |
| 16 | Cash+securities of $257M is available liquidity | Q2 Ex-99.1 "Capital Position" vs 10-Q balance sheet + Note | **$71.6M of the $257M is RESTRICTED** (LC cash collateral). Release labels the sum "cash, cash equivalents and marketable securities" with no restricted qualifier | **MISLEADING PRESENTATION (consistent across Q1 and Q2)** |
| 17 | No covenant/liquidity cliff | 10-Q Note 10 (Debt) | **$50.0M minimum Total Cash required at the end of EACH BUSINESS DAY** (Third Amendment, 2026-02-12); revolver availability only **$20.8M** (LCs $69.2M outstanding); in compliance at 6/30/26; maturity Feb-2028 | **NO NEAR-TERM CLIFF — conceded** |
| 18 | Market reaction was −30%+ to the print | IBKR daily bars, conid 866485437 | One-day print reaction **−19.5%** ($107.85 → $86.83). The −33% is **Jul-17 peak to Aug-6** and its first leg (−16.4% on Jul-23) **preceded** the print | **PREMISE CORRECTED** |
| 19 | Medical margin by cohort/class year | 10-K FY2025, 10-Q Q2-26 | **No cohort or "Class of" table exists in either filing.** Investor-deck-only; deck not fetchable this session | **UNVERIFIABLE** |
| 20 | Which markets/payors exited, and why | 10-K FY2025, Q2 Ex-99.1, 10-Q | Described only as "previously disclosed market exits" and "payor exits in certain markets." **No market is named in any of the three documents** | **UNVERIFIABLE** |
| 21 | FY27 Medicare Advantage rate environment | CMS CY2027 Rate Announcement | cms.gov 403; no web-search budget. 10-K contains **no** "Rate Announcement," "v28," or "Advance Notice" discussion to substitute | **UNVERIFIABLE — open hole** |

---

## 3. Priority 1 — decomposing the "raise"

### 3.1 The guidance ladder (all from the company's own tables)

| Date | Document | FY26 Adj. EBITDA guide | Midpoint |
|---|---|---|---|
| 2026-02-25 | 8-K acc. `0001628280-26-011630`, Ex-99.1 — *"Issues 2026 Guidance Highlighting Expected Breakeven Adjusted EBITDA Midpoint"* | −$15M to +$15M | **$0M** |
| 2026-05-06 | 8-K acc. `0001628280-26-031254`, Ex-99.1 — *"Raises… Guidance"* | $10M to $40M | **$25M** |
| 2026-08-05 | 8-K acc. `0001628280-26-053328`, Ex-99.1 — *"Raises… Guidance"* | $75M to $95M | **$85M** |

### 3.2 The decomposition — it reconciles exactly

At the Q1 print, the company had Q1 actual $53.8M in hand and guided Q2 to $15–25M (mid $20M).
So the May guide implied **H2-26 = $25M − ($53.8M + $20M) = −$48.8M**.

At the Q2 print, H1 actual is $123.4M against a FY midpoint of $85M.
So the August guide implies **H2-26 = $85M − $123.4M = −$38.4M**.

| Component | $M | Share of raise |
|---|---|---|
| Q2 beat vs the Q2 guide ($69.6M actual vs $20M mid) — **backward** | **+49.6** | **82.6%** |
| Change in implied H2 (−$48.8M → −$38.4M) — **forward** | **+10.4** | **17.4%** |
| **Total FY raise ($25M → $85M mid)** | **+60.0** | 100% |

**Answer to Priority 1a: the raise is 82.6% backward-looking.** But the residual matters as much as
the headline: **the forward half was not degraded — it was raised $10.4M.** The triage read the
negative implied H2 as the catch. It is not a catch, because the identical arithmetic run on the May
release produced a *worse* number. Anyone doing this subtraction in May already knew H2 was guided
to a loss. **Nothing about the forward half got worse on 2026-08-05.**

### 3.3 Is H2 negative by construction? Yes — and the audited record proves it

Quarterly GAAP net income from XBRL (`us-gaap:NetIncomeLoss`, 10-Q/10-K as filed; Q4 derived as
FY minus nine-month):

| Year | Q1 | Q2 | Q3 | Q4 | H1 | H2 | **H2 − H1** |
|---|---|---|---|---|---|---|---|
| 2022 | +1.2 | −20.6 | −30.7 | −56.5 | −19.4 | −87.2 | **−67.8** |
| 2023 | +16.0 | −16.7 | −31.4 | −230.5 | −0.7 | −261.9 | **−261.2** |
| 2024 | −6.1 | −30.7 | −117.6 | −105.8 | −36.8 | −223.4 | **−186.6** |
| 2025 | +12.1 | −104.4 | −110.2 | −188.8 | −92.3 | −299.0 | **−206.7** |
| 2026 | +48.9 | +18.0 | — | — | +66.9 | *guide implies ≈ −162 on Adj. EBITDA* | |

**Four years out of four, H2 is materially worse than H1; mean −$180.6M.** The FY26 guided Adjusted
EBITDA swing of **−$162M** sits inside that range and is *better* than the 2023–2025 mean.

The mechanism is exactly the claims-completion story: agilon books favorable development on the
*prior* year's reserves in H1 as those claims complete, and absorbs current-year adverse development,
Q4 utilization, and the annual physician surplus-share true-up in H2. Confirmation in the company's
own words — 10-Q MD&A: *"medical services expense for the three months ended June 30, 2026 benefited
from positive claims development from 2025 and the first quarter of 2026."*

**Verdict on the masking flag: DOWNGRADE. This is not masking.** Every input — the Q3 guide, the FY
guide, the development disclosure, the membership decline — is in the same table or the same page of
the same document. The divergence is between the headline and a *naive reader's inference*, not
between the headline and the data. Under this desk's standing boundary (grade takeaway-vs-data
divergence, not datum disclosure), the H2 arithmetic **does not clear ELEVATE**.

### 3.4 What *does* clear the bar: asymmetric quantification of development

The company quantifies prior-period development when it is **unfavorable** and declines to when it is
**favorable**.

- FY2025 10-K MD&A, explaining a revenue *decline*: *"lower risk adjustment revenue, including
  **unfavorable prior period development of approximately 1%**, as a result of additional risk
  adjustment data received from payors."* — a number is given.
- Q2-2026 8-K and 10-Q, explaining a **$67–82M medical-margin beat versus their own $115–130M guide**:
  *"Medical margin includes favorable first quarter 2026 and prior year claims development."* — **no
  number anywhere.**

Adverse development is sized and attributed to the past; favorable development is mentioned without
magnitude, leaving a $70M beat to read as operational. **This is a real, narrow honesty finding**, and
it is the reason no one can answer Mode-B question #1. It does not by itself carry a short.

---

## 4. Priority 2 — the honesty question, answered precisely

**Does the marketed takeaway diverge from the data? Partially — but not where the triage said.**

- **"Raises Full-Year 2026 Guidance"** — *literally true and fairly framed.* The guide did rise
  $10–40M → $75–95M. **NOT masking.**
- **Implied negative H2** — *disclosed in the same table, and better than the prior guide.*
  **NOT masking.** (Triage finding overturned.)
- **Unquantified favorable development driving a $70M beat, against a filed precedent of quantifying
  adverse development** — **YES, a genuine asymmetry.** Narrow.
- **A guidance-raise release that omits, in full, that ~32% of the guided EBITDA comes from a program
  its own 10-K says dies in 148 days** — **YES. This is the divergence.** See §5.
- **"cash, cash equivalents and marketable securities of $257 million"** where $71.6M is restricted
  LC collateral, the word "restricted" appearing nowhere in the release — **YES.** Applied
  identically in Q1 and Q2, so consistent, but it overstates available liquidity by 28%.

**Is anything LEFT to catch after −19.5%?** Yes — but first correct the premise. Per IBKR daily bars:

| Date | Close | Note |
|---|---|---|
| 2026-05-11 | 59.61 | start of the 3-month window |
| 2026-07-17 | 129.84 | **peak** (intraday high 133.04) — same day the CTO was terminated |
| 2026-07-22 | 119.88 | 8-K acc. `0001628280-26-049080` filed (Item 5.02, CTO separation) |
| 2026-07-23 | 100.27 | **−16.4%**, 319.5k shares — *before the print* |
| 2026-08-05 | 107.85 | **+13.8%** into the print on 724k shares (print landed after the close) |
| 2026-08-06 | 86.83 | **−19.5%** on 554k shares |

The one-day earnings reaction was **−19.5%, not −30%+**. The −33% is peak-to-trough across three
weeks and its first leg preceded the release. **And AGL still sits +45.7% above its May-11 level after
a +123% run into the July high.** This is a momentum unwind in a name with **95.7% annualized implied
vol** (IBKR `implied_vol_underlying`), not a value dislocation. Under the conditioning doctrine this
reads **CROWDED / de-crowding**, not UNDISCOVERED.

*(Quote hygiene: the $86.83 mark is the 2026-08-06 close, `is_close: true`, volume 0. The
bid 55.00 / ask 97.50 returned by the snapshot is a stale closed-market spread and is **not**
executable — do not price anything off it.)*

**What is left to catch:** §5 and §6. Neither appears in the release, and neither is a
one-day-reaction item.

---

## 5. STRONGEST KILL — a third of the guide has a statutory expiry, unmentioned in the raise

**agilon's own 10-K, filed 2026-02-25 (acc. `0001628280-26-011655`), Business and Risk Factors:**

> "CMS has announced that the ACO REACH Model **will terminate at the end of 2026**, and will be
> replaced by the Long-term Enhanced ACO Design ("LEAD") Model beginning on January 1, 2027. CMS has
> indicated that LEAD will maintain some of the ACO REACH Model's core design features… There are,
> however, **many unknowns** concerning the technical, operational and financial aspects of the LEAD
> Model, including benchmark calculation, risk adjustment methodology and quality measures, which
> will have a significant impact on **whether agilon will participate in the model**."

Now size it against the raise:

| Item | $M | Source |
|---|---|---|
| FY26 Adjusted EBITDA guide (mid) | 85.0 | Q2 Ex-99.1 guidance table |
| — of which ACO model entities | **25–30 (mid 27.5)** | Q2 Ex-99.1 **footnote 3** to the guidance table |
| **ACO share of the guide** | **26%–40%; 32% at midpoints** | |
| H1-26 ACO Adjusted EBITDA already booked | **34.0** ($27M Q1 + $7M Q2) | Q1 & Q2 Ex-99.1 footnote 3 |
| ⇒ implied H2-26 ACO contribution | **−9 to −4** | subtraction |

Three compounding facts:

1. **The program ends 2026-12-31.** Not a forecast — CMS-announced, in the company's own risk factors.
2. **agilon has not said it will join the successor.** The 10-K says LEAD's unknowns "will have a
   significant impact on *whether* agilon will participate." A guidance raise 32% funded by a
   terminating program, from an issuer that has not committed to its replacement.
3. **The ACO business is already deteriorating, and they are already retreating from it.** 10-Q Note
   12, combined ACO results: Q2 revenue **$379.3M vs $434.8M (−12.8%)**; Q2 **net loss −$7.59M vs
   +$5.40M** a year ago; H1 net income **$4.07M vs $18.07M (−77%)**. And the 10-K: *"we have
   transitioned **three of our ACOs from ACO REACH to MSSP**… for the 2026 performance year"* —
   moving from global-capitation economics to thinner shared-savings economics, before the model
   even expires.

**The 2026-08-05 release contains zero occurrences of "LEAD," zero of "terminate," and zero
discussion of what happens to the ACO contribution on 2027-01-01.** The word "REACH" appears only as
a membership-count row and a footnote crediting it with EBITDA.

**That is the takeaway-vs-data divergence.** Not the H2 arithmetic — a "Raises Full-Year Guidance"
headline whose single largest incremental driver is a program its own annual report says dies in 148
days, with the successor's economics undefined and participation uncommitted.

### 5.1 The quality-of-earnings wrinkle underneath it

The $34M H1 "ACO contribution to Adjusted EBITDA" is a non-GAAP construct sitting on top of a GAAP
number of $4.1M. The reconciliation adds back **$29.7M of "EBITDA adjustments related to equity
method investments"** in H1 (footnote: *"Includes elimination of certain administrative services
provided by agilon health, inc. to equity method investments"*). Meanwhile 10-Q Note 12 footnote 2
discloses that the fees agilon charges those same unconsolidated ACOs rose to **$12.4M in Q2-26 from
$4.3M in Q2-25** ($24.9M H1-26). So agilon charges the ACOs roughly 3× more, that charge drives the
ACOs toward a GAAP loss, and agilon then adds the charge back as its own ACO EBITDA contribution.

The methodology is disclosed and eliminating intercompany charges is defensible in principle — I am
not calling this a fabrication. But the magnitude tripled year-over-year in the flattering direction,
and it means **the $34M is largely a fee-elimination artifact, not $34M of economics that would
survive the entity going away.** Verdict: **CONSISTENT but flattering. Quality-of-earnings flag.**

---

## 6. Priority 4 — balance sheet: no cliff, but the trend indicts the H1

**Conceded up front: there is no going-concern and no near-term liquidity cliff.** The 10-Q asserts
12-month sufficiency; maturity is Feb-2028; the company was in compliance with all covenants at
6/30/26. I will not manufacture a liquidity kill.

What the numbers do say:

| Date | Cash | Restricted | Securities | **Headline "cash+securities"** | **UNRESTRICTED** |
|---|---|---|---|---|---|
| 2025-12-31 | 173.7 | 0.0 | 111.4 | 285.1 | **285.1** |
| 2026-03-31 | 140.0 | 71.6 | 91.4 | "$303M" | **231.4** |
| 2026-06-30 | 107.2 | 71.6 | 78.4 | "$257M" | **185.6** |

**Unrestricted liquidity fell $99.5M — 35% — across the two best quarters this company has ever
reported.** It earned +$123.4M of Adjusted EBITDA in H1 and its spendable cash went down by roughly
that amount. That single line is the most useful control on the H1 narrative there is.

Corroborating structure, all 10-Q Note 10 / Note 11 / Note 12:

- **$50.0M minimum Total Cash required at the end of *each business day*** (Third Amendment,
  2026-02-12). Usable buffer is therefore ≈ $185.6M − $50M = **$135.6M**, plus **$20.8M** of revolver
  (the revolver is nearly consumed: **$69.2M of LCs outstanding**).
- **The restricted cash is LC collateral.** It went $0 → $71.6M in Q1-26 alongside the Feb-2026
  amendment — i.e. the banks now require essentially full cash-collateralization of the letters of
  credit. Disclosed only obliquely, via MD&A's *"cash collateral for issuing letters of credit."*
- **Two credit-agreement amendments in four months** (Feb-12 and Apr-9, 2026). Upstream payments are
  gated on *"positive EBITDA for two consecutive trailing four-quarter periods"* — a test agilon
  has not met.
- **Surety bonds:** $32.4M at the company plus **$133.0M supporting the unconsolidated ACOs**.
- **Seven consecutive years of negative operating cash flow**, 2019–2025, no exceptions:
  −103.9, −53.2, −148.2, −130.8, −156.2, −57.8, −105.8 = **−$755.9M cumulative** (XBRL
  `NetCashProvidedByUsedInOperatingActivities`). H1-26 is **−$33.6M** against +$123.4M Adjusted
  EBITDA and +$66.9M net income.
- **The deferred cash claim is building.** Other medical expenses (physician surplus share) ran
  **$177.2M in H1-26 vs $82.4M in H1-25**; accounts payable and accrued expenses went $127.5M →
  $274.9M. Per the 10-Q, *"settlement payments are typically issued to providers on an annual basis
  in arrears."* The better the medical margin, the larger the cash owed to physician partners in the
  following year — against $185.6M of unrestricted liquidity. **This is the mechanism that keeps OCF
  negative while EBITDA prints positive, and it scales with the "good news."**

**Fairness to the company (three concessions):**
1. H1-26 OCF of −$33.6M is a **$33.5M improvement** on H1-25's −$67.1M.
2. Receivables at $1,059.8M are **0.709× quarterly revenue vs 0.751× a year ago** — DSO improved. The
   +$386M H1 build looks alarming versus 12/31/25 only because 12/31/25 was an abnormally low base
   after a collapsed 2025. **There is no receivables-quality kill here and I am not asserting one.**
3. FY26 will be, on any reading, a very large improvement on FY25's −$296M Adjusted EBITDA.

---

## 7. Priority 5 — does the VBC model work at current MA rates?

**Honest answer: undetermined, and the release does not let you determine it.** The strongest
argument *for* the model is in these filings: Q2 PMPM capitation rates **+19% y/y** (10-Q MD&A) on
reserved cost trend in the **low-7% range** (Q2 guidance assumptions; Q1 reserved at 7.4%). Price is
running roughly 12 points ahead of trend. That is the first time in this company's disclosed history
that has been true, and it is why H1 flipped positive.

The problem is that **it is not showing up in the durable metrics**:

- Revenue is *still* declining. FY26 guide $5,775–5,860M vs FY25 actual **$5,930M** — down ~1.6% at
  the midpoint *despite* +19% pricing, because membership is −10% to −12%.
- MA membership is guided to **435–445k exiting 2026 vs 511k exiting 2025 (−13%)**. FY27 therefore
  *starts* on a smaller base regardless of rates.
- Q4-26 is guided, by subtraction, to **medical margin of ~$29M** (FY mid $485M − H1 $345.6M − Q3 mid
  $110M) and **Adjusted EBITDA of ~−$38M**.
- Operating cash flow has never been positive in any year of the company's public existence.

**What would falsify a terminal-broken read** — the specific, dated tests:

1. **Q3-26 Adjusted EBITDA meaningfully above the +$5M high end**, with medical margin above the
   $105–115M guide **and management quantifying the prior-period-development component**. Absent the
   quantification the beat is uninterpretable. *(late Oct / early Nov 2026)*
2. **Q3 operating cash flow positive**, or FY26 OCF positive — which would be the **first positive
   year in eight**. This is the single cleanest falsifier of the whole bear case.
3. **An explicit LEAD-model participation decision with disclosed economics**, or a quantified FY27
   bridge showing what replaces the $25–30M ACO contribution. *(should land with Q3 or the FY26
   guide, ~Feb-2027)*
4. **MA membership guided flat-to-up for 2027** at the Q3 or Q4 print — i.e. the shrinkage was
   deliberate pruning that has finished, not attrition that continues.
5. **Unrestricted liquidity stabilizing or rising** while EBITDA is positive.

**What would confirm terminal-broken:** Q3 misses the ~$0 guide; FY27 guidance is issued without an
ACO/LEAD replacement; membership guides down again for 2027; unrestricted cash breaks below ~$120M
against the $50M daily floor.

---

## 8. What the price actually pays

| Input | Value | Source |
|---|---|---|
| Shares outstanding | 16,785k | Q2 Ex-99.1 balance sheet (post 1-for-25 reverse split) |
| Last | **$86.83** (2026-08-06 close, `is_close: true`) | IBKR conid 866485437 |
| Market cap | **$1,457M** | |
| Net cash (cash+restricted+securities − term loan) | $225.8M | |
| **Enterprise value** | **≈ $1,232M** | |

| Multiple | Value |
|---|---|
| EV / FY26 Adj. EBITDA midpoint ($85M, **includes** the terminating ACO contribution) | **14.5×** |
| EV / FY26 Adj. EBITDA **ex-ACO** ($57.5M — the part that structurally survives into 2027) | **21.4×** |
| EV / annualized Q3-26 guided run-rate ($0M) | **n/m** |

Twenty-one times a reserve-release-flattered, ex-ACO EBITDA number, for a business with seven
straight years of negative operating cash flow, membership down 12%, a 1-for-25 reverse split in
March to hold its listing, a CEO who started in May, a CTO terminated in July, and $50M of daily
minimum-cash covenant. **That is not a dislocation. There is no margin of safety in the price for the
2027 ACO hole, and the ACO hole is a matter of published CMS policy rather than forecast.**

---

## 9. Concessions the blue team is entitled to

I want these on the record so the blue brief does not have to spend its length finding them:

1. **The triage's core masking finding does not survive.** I overturned it with the company's own
   May guidance table. The forward half improved.
2. **H2-negative is genuinely structural**, proven across four audited years. Any bear note leading
   with "they guided H2 to a loss!" is making an error.
3. **The turnaround is real in magnitude.** H1 net income went from −$92.3M to +$66.9M year over
   year. FY26 will be several hundred million dollars better than FY25.
4. **Pricing is genuinely running ahead of trend** (+19% PMPM vs low-7s reserved) — the first time
   that has been true here.
5. **No going-concern, no covenant breach, no near-term maturity.** Feb-2028.
6. **No receivables-quality problem.** DSO improved year over year. I checked and it is not there.
7. **H1 OCF improved $33.5M year over year.**
8. **If agilon joins LEAD on REACH-like terms, my strongest kill loses most of its force** — that is
   the honest hinge, and it is a policy outcome I could not verify this session.

---

## 10. Open holes — UNVERIFIABLE, and therefore NOT clean

| Hole | Why it matters | How to close |
|---|---|---|
| **Magnitude of favorable prior-period development in Q2** | Determines the entire clean run-rate. Not in the 8-K or the 10-Q | Q2 earnings-call transcript (2026-08-05, 4:30pm ET) — management was almost certainly asked |
| **CY2027 MA Rate Announcement terms** | Sets whether +19% PMPM persists into FY27 | cms.gov 403'd; needs web budget or a browser session |
| **LEAD Model economics / agilon's participation intent** | Directly sizes the $25–30M 2027 hole | CMS Innovation Center; Q2 call; Q3 print |
| **Medical margin by cohort/class year** | The only way to see whether mature cohorts actually mature. **No cohort table exists in the 10-K or 10-Q** | Investor deck on investors.agilonhealth.com |
| **Which markets/payors exited and why** | "Disciplined pruning" vs "payors refused to renew" are opposite theses. **No market is named in any filing** | Investor deck; call transcript |
| **Short interest / borrow** | 95.7% IV and +123% May→July on 16.8M shares post-reverse-split suggests squeeze mechanics | Exchange short-interest file |
| **Cause of the −16.4% move on 2026-07-23** | Preceded the print; probably the CTO 8-K (filed 07-22) or an MA-sector peer print. Unresolved | News/peer tape |

The CTO datum is worth one line on its own: the Q1 release credited the beat to *"early returns from
investments in data and technology."* **Ten weeks later the Chief Technology Officer was terminated**
(8-K acc. `0001628280-26-049080`, notice given 2026-07-17 — the exact day of the price peak). Not a
thesis, but it is the second C-suite exit in three months and it lands directly on the function the
prior quarter's narrative rested on.

---

## 11. Disposition

### STRONGEST KILL
**Roughly 32% of the freshly-raised FY26 Adjusted EBITDA guide ($25–30M of $75–95M, per the
guidance table's own footnote 3) comes from ACO REACH — a CMS model that agilon's own 10-K states
"will terminate at the end of 2026," whose successor LEAD carries "many unknowns" over benchmarks and
risk adjustment, and which agilon has explicitly not committed to joining. The 2026-08-05 release
that headlines the raise does not mention any of this once.** The segment is already shrinking
(−12.8% revenue) and already loss-making at the GAAP line (−$7.6M in Q2), agilon has already moved
three ACOs out of REACH into thinner MSSP economics, and the $34M "H1 ACO contribution" is largely a
$29.7M intercompany-fee add-back rather than durable economics. Strip it and the market is paying
**21× EV/EBITDA** for a business with **seven straight years of negative operating cash flow**, whose
**unrestricted liquidity fell $99.5M during its two best quarters ever**, at a price still **+46% above
where it traded twelve weeks ago**.

*(Explicitly NOT my kill: the H2 arithmetic. I tested it and it failed — it was in the prior guide and
it is four-for-four seasonal. The triage's masking flag is overturned.)*

### WHAT WOULD CHANGE MY MIND
1. **agilon confirms LEAD participation on REACH-comparable benchmark economics**, or discloses a
   quantified FY27 bridge replacing the $25–30M. *(single biggest swing factor)*
2. **Q3-26 Adjusted EBITDA lands materially above +$5M with prior-period development quantified**
   and the ex-development number still positive.
3. **FY26 operating cash flow turns positive** — the first positive year in eight. This alone would
   force me to re-rate the whole model.
4. **FY27 MA membership guided flat or up**, confirming the −12% was completed pruning.
5. **CY2027 rates preserve the pricing-over-trend spread**, verified from the CMS Rate Announcement.
6. **The favorable development in Q2 turns out to be small** (say <$25M of the $67–82M beat), making
   the beat genuinely operational.

Items 1 and 3 are the real hinges. Either one landing moves me from REJECT toward WATCH; both landing
would make this a legitimate long at a lower multiple.

### CONVICTION: **8 / 10** on rejecting the long
Marked down from 9 by two honest weaknesses in my own case: (a) I could not read the earnings call,
so the development magnitude — the one number that decides the clean run-rate — is unknown to me as
well as to the reader, and it could cut either way; (b) the LEAD outcome is a policy event I could not
verify this session, and a REACH-comparable LEAD would blunt my strongest kill. The valuation, cash,
and membership legs of the case are independent of both and are verified from audited primary
sources.

### RECOMMEND: **REJECT the long. No position. Do not short.**

- **REJECT the long** at $86.83. No margin of safety for a known, dated, 32%-of-guide program expiry;
  21× ex-ACO EBITDA; seven years of negative operating cash flow; and a stock still 46% above its
  May level after a 123% run.
- **Do not initiate a short.** 95.7% implied vol, 16.8M shares post-1-for-25 reverse split, a
  +123% two-month run, and a genuine several-hundred-million-dollar year-over-year improvement are
  exactly the conditions where a correct fundamental view loses money. The de-crowding may well
  continue, but this is squeeze-shaped and the borrow is unverified.
- **Route to WATCH** with the Q3-26 print (~late Oct / early Nov 2026) as the gate. Tripwires:
  Q3 Adjusted EBITDA vs the −$5M/+$5M guide; quantified prior-period development; FY26 OCF sign;
  any LEAD-model disclosure; unrestricted (not headline) liquidity.
- **Reconsider as a long only** below roughly $55–60 — i.e. ~12× the ex-ACO $57.5M — or on
  confirmation of item 1 or item 3 above.

---

## Primary sources

- 8-K 2026-08-05, acc. `0001628280-26-053328`, Ex-99.1 —
  https://www.sec.gov/Archives/edgar/data/1831097/000162828026053328/agl-20260630xexx991.htm
- 10-Q Q2-2026, filed 2026-08-05, acc. `0001628280-26-053355` —
  https://www.sec.gov/Archives/edgar/data/1831097/000162828026053355/agl-20260630.htm
- 8-K 2026-05-06, acc. `0001628280-26-031254`, Ex-99.1 (Q1-26, prior guide) —
  https://www.sec.gov/Archives/edgar/data/1831097/000162828026031254/agl-20260331xexx991.htm
- 8-K 2026-02-25, acc. `0001628280-26-011630`, Ex-99.1 (FY25, initial FY26 guide) —
  https://www.sec.gov/Archives/edgar/data/1831097/000162828026011630/agl-20251231xexx991.htm
- **10-K FY2025, filed 2026-02-25, acc. `0001628280-26-011655`** (ACO REACH termination / LEAD) —
  https://www.sec.gov/Archives/edgar/data/1831097/000162828026011655/agl-20251231.htm
- 8-K 2026-03-30, acc. `0001628280-26-022074` (1-for-25 reverse split, Items 3.03/5.03)
- 8-K 2026-07-22, acc. `0001628280-26-049080` (Item 5.02, CTO separation, notice 2026-07-17)
- XBRL companyconcept API, `us-gaap:NetIncomeLoss`, `us-gaap:NetCashProvidedByUsedInOperatingActivities`,
  `us-gaap:ReceivablesNetCurrent` — https://data.sec.gov/api/xbrl/companyconcept/CIK0001831097/
- IBKR daily bars and snapshot, conid 866485437 (2026-05-11 → 2026-08-06)
