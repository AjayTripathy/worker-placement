# Refutability Triage — cohort `agentic_saas_exposed` stragglers

**Run date 2026-08-07 (Opus volume tier).** Cohort event 2026-08-06: n=15, median drawdown −32%, SPY-residual −31%. Narrative under test: *AI agents replace the seats that per-seat SaaS bills for.* Every metric below is read from the SEC-filed primary document (8-K EX-99.1, 10-Q, 10-K) fetched this session; prices are live IBKR snapshots taken 2026-08-07. Two of my own early reads were **corrected by verification** and are marked as such — an ESTC "masking" flag that the 10-K refuted, and a DOCU "no guidance" flag that was my grep error, not the filing's.

**Framing correction that precedes the table:** the cohort treats "seat-billed" as a single exposure. It is not. Three of these eleven (TWLO, BRZE, ESTC) bill on *consumption* — messages, MAU/message volume, and cloud resource units — where an agent workforce is a demand *tailwind*, not a substitution. One (PATH) bills per automation, not per human. The narrative can only be literally true for WDAY, GTLB, FRSH, DOCU, CRM's core, HUBS and NOW. Grading on drawdown alone therefore mixes a real thesis with a category error, and the category error is where the sizing mistakes live.

---

## Triage table

| Ticker | Billing model | Class | Named refuting/confirming metric | Current value & trend (primary cite) | Next print carrying it |
|---|---|---|---|---|---|
| **DOCU** | Seat + envelope allowance | **DAMAGE-ARRIVING** | **Billings growth — WITHDRAWN.** Substitute: total ARR growth | Billings reported every quarter through Q4 FY26 (**$1.0B, +10%**) then **absent from the Q1 FY27 release and from the 10-Q**; billings *guidance* was replaced by ARR-growth guidance one quarter earlier. FY26 ARR **$3,272M, +8.0%**; FY27 ARR growth guided **8.25–8.75%**; Q2 FY27 revenue guided **+8%** incl. ~1.3pts FX → **~6.7% cc**. IAM 10.8% → **12.6% of ARR** (mix metric, rises on migration alone). [Q1 FY27 EX-99.1](https://www.sec.gov/Archives/edgar/data/1261333/000126133326000072/q127ex-991er.htm) · [Q4 FY26 EX-99.1](https://www.sec.gov/Archives/edgar/data/1261333/000126133326000017/) · [10-Q](https://www.sec.gov/Archives/edgar/data/1261333/000126133326000074/docu-20260430.htm) | Q2 FY27, **est. ~2026-09-03** (prior yr 2025-09-04); not yet announced |
| **WDAY** | Per-worker seat — purest exposure | **DAMAGE-ARRIVING** | **Total subscription revenue backlog growth**, read *against* 12-month backlog growth | Total backlog: **+19% → +17% → +17% → +12% → +10.9%** ($27.294B). 12-month backlog: 15.6 → 16.4 → 17.6 → 15.8 → **15.5%** ($8.806B). **The gap inverted** — 12-mo share of total rose 31.0% → **32.3%**, i.e. contract duration is compressing. Q3/Q4 FY26 figures *include* Paradox and Sana acquisitions (company-disclosed), so organic total-backlog growth is worse than 10.9%. FY27 subscription revenue guided **12–13%**. [Q1 FY27 EX-99.1](https://www.sec.gov/Archives/edgar/data/1327811/000132781126000024/wday-04302026x991.htm) | Q2 FY27, **est. ~2026-08-27** (prior yr 2025-08-21) — **imminent** |
| **CRM** | Seat core; Agentforce = consumption (Flex Credits) | **DAMAGE-ARRIVING** | **Organic (ex-Informatica) subscription & support growth cc** — CFO has staked a dated claim on it | FY27 sub&support guided **~11% cc incl. ~3pts Informatica → ~8% organic**; Q2 FY27 revenue guided 10–11% incl. **"slightly above 4pts" Informatica → ~6% organic**. cRPO cc: 11 → 9 → 10 → 11 → 13 → **13%**. CFO Robin Washington: *"We remain confident in delivering **organic revenue acceleration in the second half of FY27**"* — named, dated, falsifiable. [Q1 FY27 EX-99.1](https://www.sec.gov/Archives/edgar/data/1108524/000110852426000125/crm-q1fy27xexhibit991.htm) | Q2 FY27, **est. ~2026-09-02** (prior yr 2025-09-03) |
| **PATH** | Per-automation/robot, **not** per-seat | **DAMAGE-ABSENT** | **Dollar-based net retention** + **net new ARR** | DBNR **110 → 108 → 108 → 107 → 107 → 109** — *inflected up*. Net new ARR **$27M (Q1 FY26) → $49M (Q1 FY27), +81% y/y**. ARR $1.901B **+12%**; FY27 ARR guide $2.058–2.063B (~+11%). The single most conceptually agent-disrupted category in the cohort has retention rising and net-new ARR nearly doubling. [Q1 FY27 EX-99.1](https://www.sec.gov/Archives/edgar/data/1734722/000173472226000037/path-2026430xex991.htm) | Q2 FY27, **est. ~2026-09-03** (prior yr 2025-09-04) |
| **TWLO** | Pure consumption (per message/call) | **DAMAGE-ABSENT** | **Dollar-Based Net Expansion Rate** + organic revenue growth | DBNE **107 → 108 → 109 → 109 → 114 → 116%** — monotonic acceleration, **+8pts y/y**. Organic growth 8 → 13 → 13 → 12 → 16 → **17%**. FY26 organic guide **raised to 13–13.5% from 9.5–10.5%**. Agents make *more* API calls. Q3 organic guide of 11–12% is the company's standing sandbag (guided 8–9% for Q3'25, printed 13%). [Q2 2026 EX-99.1](https://www.sec.gov/Archives/edgar/data/1447669/000144766926000088/twloq226ex991.htm) | Q3 2026, **est. ~2026-10-29** (prior yr 2025-10-30) |
| **FRSH** | Seat-billed ITSM/CX | **DAMAGE-ABSENT** | **Constant-currency net dollar retention** (the reported NDR is an FX artifact) | cc NDR **105 → 104 → 104 → 104 → 105 → 105%** — **flat six quarters**. Reported NDR fell 108 → 106 → **104%**, but that decline is *currency, not churn* — a disambiguation the headline invites you to miss. Revenue +16% (+15% cc); $100k+ customers +25%; $50k+ customers +18% (decel from +22%); first GAAP-profitable quarter; $7M restructuring **complete**. [Q2 2026 EX-99.1](https://www.sec.gov/Archives/edgar/data/1544522/000154452226000135/q226quarterlyearningsrelea.htm) · [8-K Item 2.05](https://www.sec.gov/Archives/edgar/data/1544522/000154452226000135/frsh-20260804.htm) | Q3 2026, **est. ~2026-11-04** (prior yr 2025-11-05) |
| **GTLB** | Per-seat DevOps — self-referentially exposed | **STRUCTURAL** | **DBNRR** + **customers >$5,000 ARR growth**; the offset metric is **paid Consumption Run Rate (CRR)** | DBNRR **122 → 121 → 119 → 118 → 117%** — monotonic, −1pt/qtr, five straight. Customers >$5k ARR: **+13% → +11% → +10% → +8% → +7%** — also monotonic. Management cut **14% of global workforce and exited 22 countries** (~37% geographic-footprint reduction, $30–35M charge) **the same day** it reported +23% revenue. **Decisive:** CRR — the entire consumption bridge off per-seat — was stated as **"nearly $20 million"** on the 2026-06-02 call, then **restated to "closer to $15 million"** in a *furnished* 8-K five weeks later (**−25%**), with management stating the definition "will continue to evolve." [Q1 FY27 EX-99.1](https://www.sec.gov/Archives/edgar/data/1653482/000162828026039805/gitlab-ex99120260430fy27.htm) · [8-K Item 2.05](https://www.sec.gov/Archives/edgar/data/1653482/000162828026039805/gtlb-20260601.htm) · [8-K 2026-07-08 CRR restatement](https://www.sec.gov/Archives/edgar/data/1653482/000165348226000145/gtlb-20260708.htm) | Q2 FY27, **est. ~2026-09-02** (prior yr 2025-09-03) |
| **BRZE** | Consumption (MAU × message volume) | **DAMAGE-ABSENT** *(growth claim UNVERIFIABLE)* | **DBNR all customers** — clean; **organic revenue** — not disclosed | DBNR **111 → 109 → 108 → 108 → 109 → 110%** — bottomed, rising two straight quarters. Customers >$500k ARR **262 → 349, +33%**. Revenue $211.0M **+30.2%** — but **OfferFit closed 2025-06-02**, so this laps a base quarter with *zero* OfferFit. CEO claims *"the fourth straight quarter of **organic revenue acceleration**"*; Braze **defines** organic revenue in the release yet **prints the figure nowhere** — "organic" appears **0 times** in the 10-Q body. The load-bearing growth claim cannot be verified from primary sources. [Q1 FY27 EX-99.1](https://www.sec.gov/Archives/edgar/data/1676238/000167623826000024/a20260430-brazeincxq127ear.htm) · [10-Q](https://www.sec.gov/Archives/edgar/data/1676238/000167623826000027/brze-20260430.htm) | Q2 FY27, **est. ~2026-09-03** (prior yr 2025-09-04) |
| **ESTC** | Consumption (Elastic Cloud) | **DAMAGE-ABSENT** | **Annual Elastic Cloud revenue growth** (committed consumption) | FY26 Annual Elastic Cloud **$640.9M vs $502.3M = +27.6%**; Monthly (self-serve) Elastic Cloud **$196.3M vs $185.3M = +5.9%**, falling 12% → 11% of revenue. Total revenue +16%; Q1 FY27 guided **+13.1%** — decelerating. Net Expansion Rate "**approximately** 112%" for **six consecutive quarters** — genuinely low-resolution, but fully defined in the 10-K. 7% workforce reduction (June 2026) and **CPO Ken Exner resigned** eff. 2026-07-17. [FY26 10-K revenue disaggregation](https://www.sec.gov/Archives/edgar/data/1707753/000170775326000018/estc-20260430.htm) · [Q4 FY26 EX-99.1](https://www.sec.gov/Archives/edgar/data/1707753/000170775326000008/a26q4erex991.htm) · [8-K Items 2.05/5.02](https://www.sec.gov/Archives/edgar/data/1707753/000170775326000024/estc-20260618.htm) | Q1 FY27, **est. ~2026-08-27** (prior yr 2025-08-28) — **imminent** |
| **HUBS** | Seat + credits hybrid — *courted 2026-08-05* | **DAMAGE-ARRIVING** | **Calculated billings growth** (court gate: Breeze consumption metric restored + no 2nd FY26 guide cut) | Q2 2026 calculated billings **$929.7M, +14% reported / +17% cc** — decelerating from Q1 2026's **+19%** reported ($912M vs $766M). Revenue $911M. No material NEW information post-court: the court and the print are the same date. [Q2 2026 EX-99.1](https://www.sec.gov/Archives/edgar/data/1404655/000119312526335148/hubs-ex99_1.htm) | Q3 2026, **2026-11-04** (court-set gate) |
| **NOW** | Seat → consumption (AI Pro Plus) — *courted 2026-07* | **DAMAGE-ABSENT** | **cRPO cc growth** (court gate: organic cRPO cc ≥17.5%) | Q2 2026 cRPO **$13.20B, +21% reported / +21.5% cc** — **clears the gate with wide margin**. Subscription revenue **+24.5% / +23% cc, accelerating** (Q1 was +22%/+19%). 123 deals >$1M net-new ACV (+40% y/y); 658 customers >$5M ACV (+23%). **Caveat:** the 21.5% is disclosed as *total*, not organic — the gate specifies organic, and NOW has been acquisitive. [Q2 2026 EX-99.1](https://www.sec.gov/Archives/edgar/data/1373715/000137371526000072/erq2fy26.htm) | Q3 2026, **2026-10** (court-set gate) |

### Price context (live IBKR, 2026-08-07)

| Ticker | Last | YTD | vs 52w high | Note |
|---|---|---|---|---|
| TWLO | $225.00 | **+58.2%** | −5.6% | **+16.5% today**; cohort membership is stale |
| GTLB | $36.55 | −2.6% | −30.2% | ~2× off 52w low $18.73 — *re-rated up* while seat metrics decay |
| FRSH | $11.71 | −4.4% | −16.7% | barely dislocated |
| ESTC | $69.95 | −7.3% | −27.1% | |
| PATH | $14.04 | −14.3% | −29.2% | |
| DOCU | $57.39 | −16.1% | −33.8% | |
| WDAY | $173.55 | −19.2% | −30.5% | |
| NOW | $120.27 | −21.5% | −38.2% | |
| BRZE | $25.71 | −25.0% | −31.1% | |
| CRM | $186.77 | −29.3% | −30.4% | |
| HUBS | $203.00 | **−49.4%** | **−61.3%** | most damaged in cohort |

Median drawdown from 52w high across the eleven: **−30.4%**, consistent with the cohort's −32%.

---

## Court-worthiness ranking

Scored on **how much a full adversarial court would change the sizing decision** — not on how interesting the finding is. TWLO scores low *despite* having the cohort's cleanest data, because the re-rating already happened; a court cannot improve a decision on a name that gapped +16% to a 52-week high this morning. That distinction — right thesis, dead edge — is the one the drawdown screen cannot make on its own.

1. **GTLB 9/10** — auto-escalate
2. **WDAY 8/10** — auto-escalate
3. **CRM 7/10** — auto-escalate
4. **DOCU 7/10** — auto-escalate
5. **PATH 7/10** — auto-escalate
6. **BRZE 6/10** — auto-escalate
7. ESTC 5/10
8. FRSH 4/10
9. TWLO 3/10
10. NOW 3/10 *(courted)*
11. HUBS 2/10 *(courted)*

### Score lines

COURT-WORTHINESS GTLB: 9/10 — per-seat model with DBNRR and >$5k-customer growth both decaying monotonically for five straight quarters, management cutting 14% of its own developer headcount, and the CRR metric carrying the entire consumption-offset case restated down 25% within five weeks of being marketed on the call — on a stock that has *re-rated up* off its low on that same story.

COURT-WORTHINESS WDAY: 8/10 — total subscription backlog growth has halved (19% → 10.9%) and inverted against the 12-month figure the market actually watches, making contract-duration compression an under-followed leading indicator with an imminent (late-Aug) print to resolve it.

COURT-WORTHINESS CRM: 7/10 — the CFO has staked a named, dated claim on organic H2 FY27 revenue acceleration while H1 organic decelerates to ~6% under a 4pt Informatica screen, and the "$3.4B combined AI and data ARR" headline relabels $1.1B of acquired data-integration ARR as AI.

COURT-WORTHINESS DOCU: 7/10 — billings was retired from both the release and the 10-Q in two steps ending exactly at the narrative onset, and it is reconstructible by us from the deferred-revenue roll-forward, so a court either confirms ~7% cc growth or materially downgrades it.

COURT-WORTHINESS PATH: 7/10 — the cohort's most conceptually agent-disrupted name has DBNR inflecting up (107 → 109) and net new ARR up 81% y/y against a −29% drawdown, so the court's job is to test whether the stabilization is durable or a one-quarter artifact.

COURT-WORTHINESS BRZE: 6/10 — consumption-billed with DBNR bottomed and rising two quarters, but the CEO's "fourth straight quarter of organic revenue acceleration" is unverifiable against a +30.2% headline that laps a zero-OfferFit base, and quantifying that gap is decision-changing.

COURT-WORTHINESS ESTC: 5/10 — consumption-billed with committed cloud revenue accelerating to +27.6%, disclosure verified clean in the 10-K after an initial masking flag of mine was refuted, leaving an honestly-disclosed deceleration that is a valuation question rather than a mispricing.

COURT-WORTHINESS FRSH: 4/10 — constant-currency NDR flat at 104–105% for six quarters shows the reported decline is an FX artifact rather than seat churn, but at −4% YTD the name is not dislocated enough for a court to move sizing.

COURT-WORTHINESS TWLO: 3/10 — DBNE accelerating 107 → 116% and an organic guide raised 350bps decisively refute the narrative, but the stock is +58% YTD and 5.6% off its high, so the edge is already priced and the cohort tag is stale.

COURT-WORTHINESS NOW: 3/10 — courted 2026-07 and the Q2 print cleared the cRPO gate at 21.5% cc with subscription revenue accelerating; the only open item is confirming organic-versus-total, which is an addendum, not a court.

COURT-WORTHINESS HUBS: 2/10 — courted 2026-08-05 on this exact print with the gate already set at 2026-11-04; billings decelerating 19% → 14% reported is consistent with the court's EDGE_HALVED verdict and adds nothing new.

---

## Method notes and self-corrections

- **Next-print dates are estimated** from prior-year cadence and fiscal period-end except HUBS (2026-11-04) and NOW (Q3 2026-10), which are court-set. Neither Workday nor Elastic nor GitLab IR had announced a date as of this run; the web-search budget for the session was exhausted, so these are marked *est.* rather than asserted.
- **ESTC correction.** I initially flagged the disappearance of the "Elastic Cloud revenue" line from the Q3/Q4 FY26 releases — after four quarters of visible deceleration (26 → 23 → 24 → 22%) — as a masking channel, with "sales-led subscription revenue (excluding Monthly Elastic Cloud)" as the flattering substitute. **The FY26 10-K refutes this:** it discloses the full revenue disaggregation with *more* granularity than the release ever carried, splitting Annual from Monthly Elastic Cloud. Disclosed is clean. ESTC is not a masking case.
- **DOCU correction.** An early read that the Q1 FY27 exhibit contained no forward guidance was my own grep error (line-counting on single-line stripped text). DOCU guides revenue and margins normally. What it genuinely dropped is **billings** — the actual *and* the guide — which survives the correction and is the real finding.
- **UNVERIFIABLE is not clean.** BRZE's organic-acceleration claim and DOCU's withdrawn billings are both scored as open exposures, not as passes.
- Grading is on **takeaway-versus-data divergence**, not on whether bad news was disclosed. ESTC's deceleration and HUBS's billings slowdown are disclosed and therefore clean; GTLB's restated CRR and BRZE's unprinted organic figure are not.
