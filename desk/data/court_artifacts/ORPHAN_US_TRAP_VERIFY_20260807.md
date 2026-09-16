# ORPHAN US SCREEN — TRAP VERIFICATION
**Date:** 2026-08-07 · **Tier:** Opus volume · **Universe:** US orphan-screen candidates 2026-08-06
**Question asked:** the screen says these are statistically cheap. Is the cheapness REAL, before any
court time is spent?

**Answer: 11 of 12 are not.** Five are instrument-type artifacts (the screen priced preferred, a
baby bond, and a warrant as if they were common). Six are real commons, and five of those six have
cheapness manufactured by a single non-recurring item. **One name — SNFCA — survives.**

Prices are IBKR, pulled 2026-08-07. Every financial claim is bound to a primary SEC accession.

---

## VERDICT TABLE

| Ticker | Instrument | Verdict | Score | One-line reason |
|---|---|---|---|---|
| **SNFCA** | common (Class A) | **REAL CANDIDATE** | **6/10** | 7.2x earnings / 0.59x book on conservatively-accounted recurring income |
| ENLV | common (ordinary) | **TRAP** | 1/10 | Stale pre-split share count on a book that is 99% a Level-2 token mark |
| JAKK | common | **TRAP** | 2/10 | 27x trailing ex-refund; the cheap window is FY2024 peak earnings |
| HPK | common | **TRAP** | 2/10 | Book exceeds proved PV-10 by $873M; covenant cliff one quarter out |
| RILY | common | **TRAP** | 1/10 | TTM "earnings" is one Babcock & Wilcox mark, already reversed |
| MGRD | **BABY BOND** | **TRAP** | 0/10 | Instrument artifact — AMG 4.200% junior subordinated note due 2061 |
| FBIO | common | **TRAP** | 2/10 | One PRV sale; consolidated cash is not the parent's; preferred in arrears |
| FCNCP | **PREFERRED** | **TRAP** | 0/10 | Instrument artifact — 5.375% Series A depositary preferred |
| FCNCO | **PREFERRED** | **TRAP** | 0/10 | Instrument artifact — 5.625% Series C direct $25-par preferred |
| FCNCN | **PREFERRED** | **TRAP** | 0/10 | Instrument artifact — 6.625% Series E reset preferred (issued 2026-02) |
| CHSCM | **PREFERRED** | **TRAP** | 0/10 | Instrument artifact — CHS Class B Series 3; issuer has no listed common |
| CLSKW | **WARRANT** | **TRAP** | 0/10 | Instrument artifact — deep-OTM warrant, $11.50 cost for $0.91 of stock |

---

## PART 1 — INSTRUMENT-TYPE ARTIFACTS

A P/E or P/B screen ingesting these rows divides an *equity* earnings stream by a *non-equity*
security price. The result is arithmetic nonsense, not a valuation.

### MGRD — Affiliated Managers Group junior subordinated NOTE
**The dispatch brief classified MGRD as one of the "real commons." That is wrong — it is debt.**

- SEC's ticker map files MGRD under CIK 0001004434 (AFFILIATED MANAGERS GROUP) in a set of
  `AMG, MGR, MGRB, MGRD, MGRE` — one common plus four exchange-traded note series.
- **Confirmed from the 424B5**
  (https://www.sec.gov/Archives/edgar/data/1004434/000119312521211983/d163931d424b5.htm):
  **4.200% Junior Subordinated Notes due 2061**, **$25.00 denomination**, $200M issued 2021-07-13,
  quarterly interest, **maturity 2061-09-30**, first par call **2026-09-30**. Unsecured and junior;
  the issuer may **defer interest for up to 20 consecutive quarters**.
- Tape corroborates independently: MGRD last **$14.99**, dividend yield **7.0%** (IBKR 502415474).
  $14.99 x 7.0% = $1.05/yr; $1.05 on $25 par = a **4.20% coupon** — an exact match.
- AMG's common is **AMG**. The note trades at **60% of par**, which is a duration-and-credit
  observation on a 2061 junior claim, not a cheap equity.

**VERDICT: TRAP — instrument artifact.** Route to the income sleeve only on a yield-to-worst basis;
it never belongs in the value court.
**COURT-WORTHINESS MGRD: 0/10 — not an equity; the screened multiple has no referent.**

### FCNCP / FCNCO / FCNCN — First Citizens BancShares preferred
FCNCA is the common; FCNCB is the unlisted 16-vote Class B. All three screened tickers are
**non-cumulative perpetual preferred** (10-K Note 15,
https://www.sec.gov/Archives/edgar/data/798941/000079894126000015/fcnca-20251231.htm):

| Ticker | Series | Coupon | Structure | Liq. pref. | Earliest call |
|---|---|---|---|---|---|
| FCNCP | A | 5.375% fixed | depositary, 1/40th | $25/dep. share ($345M) | callable now |
| FCNCO | C | 5.625% fixed | **direct $25-par shares** (CIT legacy) | $25/share ($200M) | 2027-01-04 |
| FCNCN | E | 6.625%, resets 2031 to 5yr UST + 2.830% | depositary, 1/40th | $25/dep. share ($400M) | 2031-03-15 |

Tape confirms FCNCP: last **$20.06**, yield **6.7%** → $1.344/yr = **5.375% on $25 par**.
**Note FCNCN (Series E) did not exist at FY2025 year-end** — issued 2026-02-05, after the balance
sheet date. A preferred trading below par is a *rates* observation; it carries no claim on the
bank's earnings growth, so First Citizens' P/E is meaningless against it.

**VERDICT (each): TRAP — instrument artifact.** Preferred; income sleeve if the yield clears.
**COURT-WORTHINESS FCNCP: 0/10 · FCNCO: 0/10 · FCNCN: 0/10**

### CHSCM — CHS Inc preferred
**Class B Reset Rate Cumulative Redeemable Preferred, Series 3.** 19,700,000 shares, **$25.00
liquidation preference ($492.5M)**, **6.75% cumulative**, quarterly, redeemable at CHS's option
since 2024-09-30 (10-K, https://www.sec.gov/Archives/edgar/data/823277/000082327725000038/chscp-20250831.htm).
Tape confirms: last **$24.76**, yield **6.82%** → $1.689/yr = **6.75% on $25 par**.

Two structural points the screen could not have known:
- **The "Reset Rate" never floated.** Series 3 is *"subsequently fixed at a rate of 6.75%… based on
  the terms of the contract and application of the Adjustable Rate (LIBOR) Act."* LIBOR cessation
  froze it. Treat it as a permanently fixed-rate perpetual, not a floater.
- **CHS Inc is a Minnesota agricultural cooperative with NO listed common at all** — its Section
  12(b) securities are five preferred series and its 12(g) registration is *None*. Member equity is
  capital equity certificates distributed as patronage. **The screen computed a P/E against an
  entity with no common equity outstanding.**

**VERDICT: TRAP — instrument artifact.**
**COURT-WORTHINESS CHSCM: 0/10**

### CLSKW — CleanSpark redeemable WARRANT
Confirmed from the issuer's own cover page. CleanSpark 10-Q for the period ended 2026-06-30, filed
2026-08-06 (https://www.sec.gov/Archives/edgar/data/827876/000119312526338382/clsk-20260630.htm),
"Securities registered pursuant to Section 12(b)" lists the common (CLSK) and:

> **"Redeemable warrants, each exercisable for 0.069593885 shares of common stock at an exercise
> price of $165.24 per whole share"**

Moneyness at live spot — and note the strike must be quoted correctly or it is overstated 14.4x:
- Cost to exercise one warrant = 0.069593885 x $165.24 = **$11.50**
- Stock received = 0.069593885 x CLSK **$13.14** live (IBKR 395179962) = **$0.91**
- **Intrinsic value −$10.59.** CLSK must reach **$165.24 — 12.6x the current price** — to have any.

Origin (8-A12B, https://www.sec.gov/Archives/edgar/data/827876/000119312524248160/d861647d8a12b.htm):
these are the **GRIID Infrastructure SPAC public warrants** — 13.8M at an $11.50 strike, converted
at the merger exchange ratio on 2024-10-30 into warrants over 960,395 CLSK shares — **expiring
2028-12-29**. IBKR returns **no tradeable CLSKW row**, so the instrument is near-untradeable as well
as near-worthless.

**VERDICT: TRAP — instrument artifact, and economically worthless paper besides.**
**COURT-WORTHINESS CLSKW: 0/10**

---

## PART 2 — THE REAL COMMONS

### Valuation baseline
IBKR prices 2026-08-07. TTM from 10-Q/10-K quarterly XBRL; Q4 stubs derived as FY minus 9M with all
five FY anchors confirmed against the 10-K (not the proxy, whose pay-versus-performance tags are
mis-scaled).

| | SNFCA | JAKK | HPK | RILY | FBIO |
|---|---|---|---|---|---|
| Price | $9.63 | $25.47 | $6.86 | $7.26 | $2.77 |
| Shares (M) | 26.02 | 11.45 | 126.36 | 40.20 | 33.19 |
| Market cap ($M) | 250.5 | 291.6 | 866.8 | 291.9 | 91.9 |
| TTM net income ($M) | 34.8 | 16.2 | **−144.7** | **411.7** | **127.7** |
| TTM P/E as screened | **7.2** | 18.0 | n/m | **0.71** | **0.72** |
| **TTM P/E after adjustment** | **7.2** | **~27** | n/m | **~7-21** | n/m |
| P/B | **0.59** | 1.18 | 0.59 | 2.05 | 0.57 |
| Avg 90d $ volume | $0.32M | $1.85M | $4.53M | $6.49M | $1.58M |

**JAKK never screened cheap on TTM at all** (18x, and ~27x once a one-time tariff refund is
removed). **RILY and FBIO at ~0.7x** are single non-recurring items. **HPK has negative TTM
earnings**, so its only cheap metric is book — which Part 2 shows is overstated by $873M.

---

### SNFCA — Security National Financial · **REAL CANDIDATE**

The one name where the cheapness survives verification.

**Share count and book, from the filing rather than the aggregator.** The Q1 2026 balance-sheet
parenthetical (https://www.sec.gov/Archives/edgar/data/318673/000149315226022202/form10-q.htm)
shows Class A 22,432,763 issued less **1,137,578 treasury** and Class C 3,587,237 less **104,604
treasury** — the cover-page caption double-counts treasury. True outstanding at 3/31/26 is
**24,777,818**. A **5% stock dividend was then declared 2026-06-26 and issued 2026-07-17**
(8-K Item 8.01, https://www.sec.gov/Archives/edgar/data/318673/000149315226031035/form8-k.htm),
so the count behind today's $9.63 price is **~26.02M**.
→ market cap **~$250M**, **BVPS $16.36**, **P/B 0.59**, TTM EPS **$1.34**, **P/E 7.2**.

**Earnings quality is the best in the batch, and two anticipated traps are absent.**
- **MSRs are carried at amortized cost (LOCOM), not fair value.** Carrying value $2.46M against a
  disclosed fair value of $3.99M, **valuation allowance $0**. The classic mortgage-company
  earnings-inflation channel — marking MSRs up through the P&L — is **structurally unavailable**,
  and the book is a small *hidden asset*. The MSR book is trivial in any case (0.85% of FY2025
  originations retained), so this is a clean-bill finding rather than a driver.
- **FY2025 core pre-tax ex-gains was $36.77M of $41.41M reported (88.8%)**, versus $35.43M in
  FY2024 — a growing, recurring base. The real non-cash item is a **$3.98M unrealized mark on
  equity securities held = 9.6% of FY2025 pre-tax**, which reversed slightly negative in Q1'26.

**The mortgage segment is a loss centre, not a flatterer — the earnings are arguably depressed.**

| FY | Mortgage pre-tax | Consolidated pre-tax | Mortgage share |
|---|---|---|---|
| 2020 | **+$55.1M** | $71.5M | +77.2% |
| 2022 | +$14.1M | $34.4M | +41.0% |
| 2023 | **−$17.4M** | $16.3M | −106.8% |
| 2025 | **−$4.8M** | $41.4M | **−11.5%** |

FY2025 pre-tax splits **Life $37.35M (90.2%) / Funeral & Cemetery $8.82M (21.3%) / Mortgage
−$4.76M (−11.5%)**. Originations fell from 21,206 loans / $5.5bn (2020) to 6,844 / $2.30bn (2025).
So today's 7.2x is struck on earnings carrying a mortgage drag, not a mortgage boom — the opposite
of the peak-earnings trap. That $72.5M peak-to-trough swing is also the main forward volatility.

**Four real constraints, all disclosed, none deceptive:**
1. **Capital is trapped at the insurance subsidiaries.** No Article 7 Schedule I/II is filed, so
   there is no quantified restricted-net-assets figure. Ordinary 2026 dividend capacity without
   Commissioner approval is roughly **$11.4M** (Security National Life ~$8.5M, Kilpatrick $2.06M,
   First Guaranty $0.81M) against **$32.2M of consolidated net earnings**. SNFC has also committed
   to inject capital if Security National Life's RBC falls below 350% of the authorized control
   level. Earnings are real but only partly upstreamable.
2. **Family control by votes, with a live ratchet.** Class C carries **10 votes** to Class A's 1
   (except one third of directors elected solely by Class A). Class C is **14.1% of shares but
   62.1% of votes**; Quist-affiliated blocks hold ~85% of Class C. At the 2026-06-26 meeting
   shareholders approved reallocating **500,000 plan shares from Class A to Class C — adding
   4,500,000 votes**. *Correction to the dispatch premise: SNFC does **not** claim the Nasdaq
   Rule 5615(c) controlled-company exemption* — the board is majority independent (5 of 9) with
   independent compensation and nominating committees and a lead independent director. Related-party
   dealings are limited to family employment; no related-party leases, loans, or asset transfers.
3. **Book value just became rate-volatile.** SNFC adopted **LDTI (ASU 2018-12) on 2025-12-31**,
   modified-retrospective to 2024-01-01. FY2024 pre-tax was restated $34.10M → $37.37M and equity
   $338.8M → $381.9M. **FY2023 and prior are not restated and are not comparable for Life.** AOCI
   is now **$36.8M = 8.7% of equity**, dominated by the LDTI discount-rate remeasurement of future
   policy benefits ($39.5M) — not a bond mark (the AFS book is in a small net unrealized loss).
   It swings inversely with rates: Q1'26 OCI +$8.07M versus Q1'25 −$3.36M.
4. **Real estate held for investment is $234.3M — 14.8% of assets — and grew $19.4M in Q1 alone.**
   An unusual concentration for a life insurer, illiquid and carried at cost less $38.6M of
   accumulated depreciation.

**Liquidity is the binding practical constraint.** At **~$0.32M of average daily dollar volume**
SNFCA is an order of magnitude thinner than anything else here. Any position is capacity-capped.
Goodwill is immaterial ($5.25M) → tangible BVPS ~$16.00.

**VERDICT: REAL CANDIDATE.** Cheap on recurring, conservatively-accounted earnings from stable life
and funeral/cemetery operations, with the cyclical segment currently a drag rather than a boost.
The negatives are structural — trapped statutory capital, permanent minority voting position,
newly rate-sensitive book, and thin liquidity — not accounting deception.

**COURT-WORTHINESS SNFCA: 6/10 — the only name whose cheapness survived; escalate, but size for
$0.32M/day liquidity and a permanent 62%-vote family block.**

---

### RILY — BRC Group Holdings (ex-B. Riley Financial) · **TRAP**

**Identity first:** CIK 1464790 now files as **BRC Group Holdings, Inc.** (former names
"B. Riley Financial" and "Great American Group"). The common still trades as RILY; RILYG/K/L/N/P/T/Z
are baby bonds and preferreds, which is where the capital structure actually sits.

**THE DECISIVE FINDING — the $412M of TTM earnings is one stock position, and it has already
reversed.** The Q2 2026 10-Q, filed 2026-08-06
(https://www.sec.gov/Archives/edgar/data/1464790/000146479026000046/rily-20260630.htm), carries the
**Babcock & Wilcox (NYSE: BW)** holding at **$386,996K at 6/30/2026 versus $174,011K at 12/31/2025
— a +$213.0M increase the filing attributes explicitly to "an increase in the public share price."**
BW closed 6/30/26 at **$14.10**, back-solving to **27.447M shares**, a count that also reconciles to
the 12/31/25 carry at BW's $6.34 close — they never sold.

**BW last traded ~$9.38-9.46. Those same 27.447M shares are now worth ~$257M — a ~$130M pre-tax
markdown already sitting in Q3 2026, against $142.2M of total stockholders' equity.** Mark it there
and BRC's book equity is roughly **$13M — effectively zero.**

**Operations lose money once the marks come out:**
- **FY2025 recurring continuing operations ≈ −$136.2M pre-tax.** The +$307.4M headline was composed
  of a **$67.2M senior-note-exchange gain**, **$86.2M of sale/deconsolidation gains**, **$70.8M of
  discontinued operations**, **$125.5M of trading gains**, **$62.7M of investment gains**, and a
  **tax benefit on positive pre-tax income** (a $104.4M valuation-allowance movement; the low rate
  is NOL absorption against $602.9M federal / $688.2M state NOLs).
- **Q1 2026:** of $239.1M pre-tax, **$145.1M trading gains + $105.1M investment gains — ~$229.1M of
  it B&W alone.** Recurring operations ≈ **−$11M pre-tax**.
- **Q2 2026, the clean quarter: underlying pre-tax ≈ +$3.5M** on $239.1M of revenue.

Honest bracket on real earnings power: **$14M-$126M annualized** against a $412M headline. Note
management's own "Operating Adjusted EBITDA" bridge leans on a **+$28.0M "fixed income and variable
rate transaction spread" add-back that is larger than the entire $25.0M of Q2 investment gains it
is added back to.**

**The debt wall is seven weeks away.** Total debt **$1,277.1M** against **$154.1M** cash → **true
net debt $1,121.4M**. (The company advertises "Net Debt $285.2M" by netting the entire $804.5M
investment portfolio including the B&W mark; at today's BW price that is already ~$415M.)

| Maturity | Instrument | $M |
|---|---|---|
| **2026-09-30** | RILYN 6.50% | **142.1** |
| **2026-12-31** | RILYG 5.00% | **163.8** |
| 2028-01-01 | 8.00% "New Notes" — 2nd-lien **SECURED** | 258.9 |
| 2028-01-31 | RILYT 6.00% | 207.9 |
| 2028-08-31 | RILYZ 5.25% | 357.2 |

**$306M matures within five months** against $154.1M of cash; essentially the whole $1.28bn stack
matures inside 25 months. The **Oaktree term loan carries a springing maturity 91 days ahead of any
bond maturity over $10M** — already live, with a $797K derivative liability booked for it. (Nomura
is gone, repaid in full February 2025.) **Operations do not cover the coupon:** 6M 2026 operating
cash flow was **+$19.9M against $243.8M of net income** — the earnings were parked in a larger
trading book — versus **~$77M/yr of cash interest paid**.

**Equity turned positive on a mark plus dilution, not profit.** The −$171.5M → +$142.2M swing is
**+$233.8M of net income (~$213M of it the B&W mark)** plus **$67.8M of stock issued in Section
3(a)(9) note exchanges** — five exchanges with **DBA Trading, LLC, a >5% holder**, retiring $69.1M
of principal for **8,358,495 shares** at $6.60-$9.34, for a net extinguishment gain of only $1.3M.
Shares went **30,597,066 → 40,199,755 (+31.4%) in six months**. **Goodwill $392.7M plus intangibles
$101.9M = $494.6M against $142.2M of equity — tangible book is deeply negative even at the 6/30
mark.**

**The preferred is already in default.** RILYP (6.875%) and RILYL (7.375%) carry a combined
**$126.2M liquidation preference including $12.1M of cumulative unpaid dividends**, compounding
~$4.0M per half-year, suspended since 2025-01-21. **On 2026-04-30 the sixth missed dividend period
triggered a "Preferred Dividend Default"**, automatically expanding the board by two preferred-
elected seats until arrears are paid. That $126.2M ranks ahead of the $292M common.

**Governance and legal overhang is escalating.** Disclosure controls were **"not effective"** at
6/30/2026 with **two unremediated material weaknesses** (ITGC user access; segment reporting). An
**NT 10-K** was filed 2026-03-17, the 10-K on 3/31, and a **10-K/A one day later**. The SEC matter
has moved **from documents to testimony — "In June 2026, the SEC issued subpoenas to certain current
and former employees seeking their testimony."** Brian Kahn **pleaded guilty 2025-12-10** to
conspiracy to commit securities fraud; the related $200.5M Vintage Capital loan is a **total loss**
("the Company collected proceeds of **$1,855**… No additional collections are expected").

**Largest item absent from "Total Debt":** two 2025 **Written Put agreements** letting third-party
issuers force BRC to buy their convertible preferred — **$960M remaining, exercisable through
2029-08-27 at up to $150M per issuance, one notice per week.** A **$960M contingent cash call
against $154M of cash**, excluded from both Total Debt and the advertised Net Debt.

**VERDICT: TRAP — the clearest in the batch.** The 0.71x P/E is a fully non-cash, non-recurring,
**already-reversing** mark on one equity position. If the BW exposure is what's wanted, own BW
directly — same beta without $1.13bn of senior claims and $126M of defaulted preferred in front.

**COURT-WORTHINESS RILY: 1/10 — a single already-reversed mark masquerading as earnings, in front
of a five-month debt wall.**

---

### HPK — HighPeak Energy · **TRAP**

**The 0.59x book is an accounting artifact, and this is the decisive finding.** HighPeak has taken
**zero impairment** — but successful-efforts tests recoverability on an **undiscounted** basis.
Discount the same reserves (FY2025 10-K,
https://www.sec.gov/Archives/edgar/data/1792849/000143774926007770/hpe20251231_10k.htm):

| At 12/31/2025, SEC deck $65.34/Bbl, $3.387/MMBtu | $M |
|---|---|
| Net oil & gas properties, **carrying value** | **2,930.4** |
| Undiscounted future net cash flow, total proved | 3,688.2 ← *the only thing holding the book up* |
| **PV-10, total proved** | **2,057.0** |
| **PV-10, proved developed (PDP)** | **1,493.4** |
| Standardized measure (after tax) | 1,912.8 |

**Carrying value exceeds total-proved PV-10 by $873M and PDP PV-10 by $1,437M**, with only ~26%
cushion on the undiscounted test. Marked to its own reserves the equity is **not cheap — it is
roughly fairly priced**:
- Total proved: PV-10 $2,057 − net debt $1,104 − hedge liability $107 = **$846M vs $867M market cap
  (~1.0x)**
- PDP only: $1,493 − $1,104 − $107 = **$282M ≈ $2.23/share** against $6.86

**The Q1'26 −$127.4M is the least alarming item.** It reconciles exactly: operating income +36.0,
interest income +0.9, **interest expense −35.0**, **derivative loss −157.0** → pre-tax −155.1; tax
benefit +27.7 → **−127.4**. The derivative loss is **$139.5M non-cash MTM + $17.5M cash settlements**
— oil *rallied* against a lender-mandated hedge book, so it reverses at settlement. Q3'25's −$18.3M
was a **$25.4M loss on extinguishment** (August term-loan amendment). **Q4'25 is the worse quarter**:
an **operating loss of −$16.4M** including **$13.0M of exploration and abandonments — an $11.1M
unsuccessful exploratory well, the first dry hole in company history** — with DD&A at 67% of revenue.

**Covenant cliff, one quarter away.** No bonds outstanding; a **$725M senior-notes offering was
launched 2025-06-30 and abandoned**. The stack is a single **$1,200M term loan at SOFR + 750bps
(~11.7%)** maturing 2028-09-30, plus an undrawn $100M facility. **Three amendments in ten months**:
Aug-2025 (extend, upsize, defer $30M/qtr amortization a year), Dec-2025 (asset coverage 1.25x→1.00x,
net leverage 2.00x→2.50x, hedging raised to 75% of PDP oil, dividends prohibited until 9/30/26), and
**June-2026 (net leverage relaxed again to 2.25x for Q2'26)**. Leverage is ~2.03x at 3/31/26 and
~2.15x at 6/30/26 against the newly-amended 2.25x. **Q3'26 reverts to 2.00x with $30M/quarter
amortization restarting in September** — requiring net debt ≤ ~$1,014M against ~$1,080M actual.

There is no going-concern qualification, but the 10-Q language is as close as it gets without one:
> *"it is uncertain whether the Company will be able to comply with these covenants, in particular
> beginning in the Second Quarter of 2026… If such amounts were accelerated… the Company does not
> expect it would have sufficient liquidity to repay such indebtedness and would likely need to
> pursue a restructuring, refinancing or other strategic alternatives."*

**Reserves and production are deteriorating on well performance, not just price.** Total proved fell
**−12.6%** to 173,891 MBoe, including **11,531 MBoe of downward PUD revisions, of which 9,177 MBoe
was well performance**. Production went **53,128 Boe/d (Q1'25) → 45,629 (Q1'26)**, oil **−19% y/y**.
2026 capex is **$255-285M against $511.8M in 2025 (−45%)**, one rig, with guidance of
**41,000-44,000 Boe/d — management explicitly guiding to decline** ("protect profitability… not
chase production volumes"). That is a harvest budget, not maintenance.

**Hedged into the cap.** ~73% of oil hedged for Q2'26 (22,350 Bbl/d vs 30,826 produced), collars
~$59.80/$66.82 and swaps ~$63-65, running into Q1'27 and rolling off entirely by Q4'27; net hedge
**liability $106.5M**. Lender-mandated, so an oil rally deleverages only slowly while a selloff hits
immediately once hedges roll.

**Governance:** a **controlled company** — Principal Stockholder Group **~64.4%** (HighPeak Energy
Partners LP 34.0%, Partners II 29.1%, DeJoria Family Trust 11.8%, Jack Hightower personally 10.4%).
Hightower **retired as CEO and Chairman 2025-09-15**; his shares are **pledged as collateral for
personal loans** with disclosed forced-sale risk. A sale process announced **2023-01-23** is, three
years later, still described as *"preliminary… generally excluding substantive discussions regarding
potential valuation, structure or other key transaction terms."* A Change-in-Control severance plan
was adopted 2025-09-09. Past sponsor participation was at third-party prices and 2024-25 were net
buybacks — but a **$150M ATM launched 2026-05-06 equals 17% of the market cap**, which is the
clearest signal of how management ranks its own equity. Q2 2026 is not yet filed.

**VERDICT: TRAP.** The cheap metric is a book value $873M above proved PV-10, sustained only by an
undiscounted test. On its own reserves the equity is fairly priced at best and worth ~$2.23 on PDP.

**COURT-WORTHINESS HPK: 2/10 — book is not a margin of safety, and a 2.00x covenant test plus
amortization restart lands next quarter.**

---

### FBIO — Fortress Biotech · **TRAP**

The screen sees $91.9M of market cap against **$255.8M of consolidated cash** and a **0.72x TTM
P/E**. Three structural facts destroy both.

**1 — The earnings are one asset sale.** The Q1'26 line item is **"Gain on sale of priority review
voucher, net of expenses" = $158,873K**
(https://www.sec.gov/Archives/edgar/data/1429260/000110465926061233/fbio-20260331x10q.htm). Cyprium
received a Rare Pediatric Disease PRV on the 2026-01-13 approval of ZYCUBO for Menkes disease and
sold it for **$205.0M gross, closing 2026-03-30**, less 20% to NIH/NICHD and 2.5% to a third party.
Bridge: operating loss **−$7,739K** → PRV gain +158,873 → pre-tax 142,294 → tax −5,132 →
ProfitLoss 137,162 → **less NCI −26,789 → $110,373K to Fortress.**
*(The Checkpoint/Sun Pharma transaction is a different event — it closed 2025-05-30 for $28.0M cash
and a $27.1M deconsolidation gain.)* Meanwhile the operating business loses money every period:
**−$70.2M in FY2025**, with FY2025 operating cash flow of **−$65.8M**.

**2 — Read the right earnings line.** Fortress reports three bottom lines, and they disagree in sign:

| Period | ProfitLoss (incl. NCI) | NetIncomeLoss (parent) | **Available to COMMON** |
|---|---|---|---|
| FY2025 | **−32.9** | +37.0 | **−1.9** |
| Q1 2026 | +137.2 | +110.4 | +108.4 |

In FY2025 the consolidated group **lost $32.9M**; NCI absorbed **−$39.7M**, which is what flips the
parent line positive; and after preferred dividends the figure **available to common was −$1.9M**.

**3 — The consolidated cash is not the parent's.** The 10-Q liquidity note gives a four-way split:

| Bucket | 3/31/26 | Fortress ownership |
|---|---|---|
| **Fortress + private subs** (incl. Cyprium) | **$209.9M** | Cyprium ~80.4% |
| Journey Medical (DERM) | $27.2M | **36.3%** |
| Mustang Bio (MBIO) | $16.3M | **4.0%** |
| Avenue (ATXI) | $2.4M | **10.3%** |
| Consolidated | **$255.8M** | |

Haircuts against the $255.8M headline: **$46.1M of PRV proceeds owed to NIH and a third party,
accrued and unpaid** (payables jumped $47.1M→$93.0M — a real Q2 outflow); **$5.4M** of taxes
payable; **$45.9M** sitting at subsidiaries owned 4-36% that cannot be upstreamed. Fortress's own
statement of what it expects to end up controlling is **"at least $100.0 million"** from Cyprium —
against a pre-PRV parent balance of only **$35.2M**.

**Claims ranking ahead of a $92M common:** **3,427,138 preferred shares (FBIOP, 9.375% Series A) at
$25.00 = $85.7M liquidation preference**, **cumulative**, with the monthly dividend **paused since
2024-07-05** and **$14.0M of undeclared arrears at 3/31/26** accruing at $8.03M/yr. The arrears also
make FBIO **ineligible for Form S-3**, so it can only raise via S-1 or private placement. Separately
**NCI holds $40.2M of book equity** (up from $12.3M, having taken $26.8M of the Q1 gain).

**Dilution history, corrected.** The path was not 82M → 33M shares. A **1-for-15 reverse split
effective 2023-10-10** cured a Nasdaq bid-price deficiency: 131.7M shares (peak, 6/30/23) → **8.9M
post-split** → **33.2M now**, i.e. **3.7x re-dilution in ~2.5 years**, plus 8.28M warrants and 2.15M
unvested RSU/restricted outstanding. There is **no going-concern language** in either the FY2025
10-K or the Q1'26 10-Q, and parent burn is modest (~$4.5M/quarter operating, ~$5M forward).

**VERDICT: TRAP.** "Below cash at 0.7x earnings" is three artifacts stacked: subsidiary cash counted
as the parent's, one asset sale counted as run-rate, and $85.7M of preferred plus $14.0M of arrears
plus $40.2M of NCI ignored ahead of the common. Netting honestly — $209.9M parent-and-private less
$46.1M owed less $5.4M tax less $99.7M of preferred claims — leaves roughly **$59M** attributable
against a $92M market cap, before a ~$20M/yr parent burn and a ~20% Cyprium minority leak.

**COURT-WORTHINESS FBIO: 2/10 — holdco-consolidation artifact; the common is the residual behind
preferred arrears and NCI on a business that does not earn.**

---

### JAKK — JAKKS Pacific · **TRAP** (false signal on a clean company)

**JAKKS is not cheap on any current metric, and is more expensive than the headline.**

| Metric | Value |
|---|---|
| TTM net income (Q3'25-Q2'26) | $16.2M |
| TTM P/E as reported | **18.0x** |
| **TTM P/E ex one-time tariff refund** | **~27x** |
| TTM EBITDA (~$15.1M op income + ~$10M D&A) | ~$25M |
| EV ($291.6M − $60.6M net cash) | $231M |
| EV/EBITDA | ~9.2x |

**The Q2'26 "beat" is a government tariff refund, not operating recovery.** Q2'26 shows a **loss
from operations of −$142K** and net income of **+$5,863K**, bridged by **+$6,976K of other income**
(Q2'26 10-Q, https://www.sec.gov/Archives/edgar/data/1009829/000118518526003186/jakk10q063026.htm).
MD&A: *"The increase is mainly due to refunded import tariff expenditures."* The liquidity section
names it — **$11.1M refunded by the federal government related to import tariffs levied under the
IEEPA**, following a claims process established after a Supreme Court decision. **Strip it and Q2'26
was ~+$0.6M pre-tax and 1H26 was −$4.6M pre-tax.**

**The cheap signal is a base-effect / peak-earnings artifact** — the exact PEG-distortion mode
already catalogued in the GARP vertical. FY2024 net income was **$33.9M** (~8.6x); FY2025 collapsed
to **$9.9M**. Any window still reaching into FY2024 sees 8.6x. Note FY2024's **13.9% effective tax
rate** was itself flattered by a $1.4M discrete valuation-allowance benefit, against **33.1% in
FY2025** — so the stale year is doubly overstated. Revenue fell **$691.0M → $570.6M (−17.4%)**, with
**Q3'25 down 34%** on limited theatrical releases, lower Disney Princess/Style and Nintendo sales,
and *"US customers lowering their order levels based on tariffs"* — **not a lost license**. 1H26 has
recovered to $245.9M (+5.8%) on Super Mario Movie and Nintendo product.

**The anticipated accounting trap is genuinely absent — a clean finding.** The deferred-tax
valuation-allowance release ran through **FY2022** ($67,275K → $726K) and has been flat since
($714K in FY2025, a $4K change). **Nothing material flows through TTM earnings from it.**

**The balance sheet is genuinely clean**: **zero borrowings** at 6/30/26, a $70.0M BMO revolver
undrawn with $68.7M available, **$60.6M net cash**, **no preferred** (the Series A was fully redeemed
2024-03-11 for $20.0M cash plus 571,295 shares), **no buyback**, and a **$0.25 quarterly dividend**
initiated in 2025 (~3.9% yield). Share count drifts up only on equity comp; the $75M ATM has never
been used.

**Two live exposures worth carrying:** **minimum royalty guarantees of $185.0M aggregate, $60.7M due
within twelve months** — an off-balance-sheet fixed obligation that alone exceeds net cash; and
**Target 26.6% + Walmart 26.1% = 52.7% of FY2025 sales**. *"Substantially all"* product is sourced
from China with **no disclosed factory diversification**.

**VERDICT: TRAP — on the cheapness claim only.** JAKKS is an honest, debt-free, dividend-paying
company with no accounting deception; it is simply not cheap at ~27x trailing ex-refund on halved
earnings. The screen's signal is false, which is what this pass exists to catch.

**COURT-WORTHINESS JAKK: 2/10 — clean accounts and clean balance sheet, but the trailing multiple
is ~27x ex-refund; revisit only on a toy-cycle inflection.**

---

### ENLV — Enlivex Ltd. · **TRAP**

The most extreme artifact in the batch — two independent errors stack.

**Error 1 — the market cap in the screen is ~13x too high.** Enlivex executed a **1-for-15 reverse
share split on 2026-07-09**. Shares outstanding are **17,485,462 as of 2026-08-05**, per the F-3
filed 2026-08-06 (https://www.sec.gov/Archives/edgar/data/1596812/000121390026086195/ea0300828-f3_enlivex.htm),
which also prints a **$2.18** last sale. The XBRL count of 237.38M is the **pre-split** 12/31/2025
figure. Multiplying the stale count by the post-split price manufactures a ~$470M market cap for a
company actually worth **~$35-38M**.

**Error 2 — the book it was measured against is 99% a model output.** From the audited FY2025 20-F
(https://www.sec.gov/Archives/edgar/data/1596812/000121390026033857/ea0282960-20f_enlivex.htm):

| Balance sheet 12/31/2025 | $ thousands |
|---|---|
| Cash and equivalents | **1,894** |
| Short-term deposits | 3,861 |
| Digital assets at FV (RAIN token), current + non-current | 606,781 |
| **Digital assets purchase option ("RAIN Option")** | **1,708,789** |
| Total assets | 2,326,998 |
| Deferred tax liability on unrealized crypto gains | 382,646 |
| **Shareholders' equity** | **1,934,948** |

On 2025-11-24 Enlivex did a **$212M private placement funded in USDT, not dollars** (210.1M shares
+ 1.89M pre-funded warrants at $1.00), becoming a treasury vehicle for **RAIN**, the governance token
of an Arbitrum prediction-markets protocol; the name changed from Enlivex *Therapeutics* to Enlivex
Ltd. on 2026-02-10. The raise is booked as a **non-cash** financing item — only **$10.4M of actual
cash** came in from share issuance all year. Currency-artifact and reverse-merger hypotheses are both
**refuted**: reporting currency is USD under US GAAP, and it is the same legal entity, CEO, address,
and Allocetra program.

**73% of total assets is one Black-Scholes output.** The RAIN Option — a free right to buy 278.2bn
RAIN at $0.0033 — was recognized at $461.2M and marked to **$1,708.8M**, producing **$1,268.1M of
non-cash income**. It is modelled on **184% volatility** from ~three months of trading history and
classified **Level 2**. Disclosed sensitivity: **±10% of volatility moves the mark by +$1.91bn /
−$1.51bn** — the largest asset on the balance sheet has an error bar wider than the whole company.
The auditor (Yarel + Partners) issued a clean opinion but raised the fair value of RAIN and the RAIN
Option as its **one Critical Audit Matter**, including whether the principal market is *active*.

**Earnings quality is zero by construction.** FY2025 revenue **$0**; operating loss **−$15.0M**
(R&D $9.2M still running); reported net income **+$1,235.5M** (EPS $27.04) entirely unrealized;
operating cash flow **−$10.4M**.

**The tell — management's own NAV excludes its largest asset.** The 6-K dashboard of 2026-07-20
(https://www.sec.gov/Archives/edgar/data/1596812/000121390026079409/ea029849601ex99-1.htm) publishes
79.55bn RAIN worth ~$1.1bn and a "NAV per share of $66.16" — and **omits the $1.7bn RAIN Option
entirely**. The company stopped counting the asset that produced 100% of its reported profit.

**The market has fully rejected the mark:** RAIN is *up* ~73% since year-end while the equity is
*down* ~85% from the $1.00 PIPE price. The stock trades at roughly **2% of audited book** and **3%
of the company's own claimed treasury NAV**.

**Solvency, not valuation, is the live question.** On 2026-03-23 Enlivex issued a **$21M senior
secured convertible note for $19M cash** (Lind Global XIV), secured on the RAIN holdings, zero
coupon, **maturing 2027-03-23**, amortising in nine ~$2.33M monthly instalments payable in cash *or
in shares at 90% of the five lowest daily VWAPs over the prior 20 trading days* — floorless. Stated
conversion is $40.38 against $2.18, so **the repayment-share mechanic is the dilution engine**, and
the 2026-08-06 F-3 registering **10,000,000 shares against a 17.5M count (~66% dilution)** is that
engine being loaded. Against ~$8-9M of pro-forma liquidity and a $0.87M/month burn, that is **~9-10
months of runway before $21M of principal comes due**. The treasury cannot bridge it: the 20-F states
RAIN *"is traded exclusively in exchange for the USDT stablecoin,"* and 79.5bn tokens of a coin that
primary-listed on BingX in September 2025 cannot be sold at scale without destroying the price.

**VERDICT: TRAP.** Nothing here is disclosed dishonestly — the 20-F is unusually forthcoming — but
the *screen's* takeaway diverges from the data by two orders of magnitude.

**COURT-WORTHINESS ENLV: 1/10 — screen artifact stacked on a Level-2 mark; the only real question
is solvency, and it resolves against the equity.**

---

## OPEN ITEMS / WHAT REMAINS UNVERIFIED
- **SNFCA statutory dividend capacity** is derived from Note 23 state-by-state limits, not from an
  Article 7 Schedule I/II — **SNFC files none**, so there is no audited restricted-net-assets figure.
  Treat the ~$11.4M as an estimate.
- **HPK Q2 2026 is not yet filed** (last year's Q2 landed 8/11). The June covenant amendment implies
  Q2 leverage landed between 2.00x and 2.25x, but the Q3 test is the one that matters.
- **FBIO Q2 2026 is not yet filed** (due mid-August). The parent-versus-Cyprium cash split is *not
  disclosed* at any date; "at least $100.0M" is management's own characterisation, not a statement
  of segregated balances.
- **JAKK licensor concentration is not quantified** — no Disney percentage is disclosed. Royalty
  expense of $92.4M (16.2% of sales) is the only available proxy.

## METHOD NOTE — how the two biggest errors were caught
Both decisive corrections came from refusing to trust a derived number:
1. **ENLV** — the screen's market cap used a **pre-reverse-split share count with a post-split
   price**. Tape-verifying the price action instead of assuming a 94% crash surfaced the 1-for-15
   split and a 13x market-cap error.
2. **SNFCA** — the 10-Q **cover-page share count double-counts treasury stock**. Reading the
   balance-sheet parenthetical instead gave 24.78M rather than 26.04M shares, and the 5% stock
   dividend issued 2026-07-17 had to be layered on top to match today's price basis.

Neither error is visible without going to the filing.
