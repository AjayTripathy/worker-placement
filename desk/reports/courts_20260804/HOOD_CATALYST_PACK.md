# HOOD — 9th Circuit Event-Contract Catalyst: INSTRUMENTATION + MISPRICING PACK

**Date:** 2026-08-04 · **Live basis:** IBKR **$92.17** last (bid 92.17 / ask 92.20, +2.03% d/d, 9.52M sh, `is_close=false`), contract 504546674
**Companion to:** `desk/reports/courts_20260804/HOOD.md` (WATCH 4/10) and `desk/data/edge_classifications/HOOD.json`
**Headline verdict:** The catalyst is **REAL, correctly identified, and now fully instrumented from the primary docket — but it is NOT tradeable through options.** The event is FAIRLY PRICED, and it is fairly priced for a structural reason, not an accidental one. **Recommendation: no pre-position. Equity Branch B on the ruling day only — with the $95 cap restated (see §6), because as written it almost never fires.**

---

## 0. WHAT THIS PACK CORRECTS IN THE COURT FILE

The court's gap list said *"Ninth Circuit docket not read directly — status rests on the 10-Q narrative plus secondary headlines."* It has now been read. Five corrections, two of them material to sizing.

| # | Court file said | Primary docket says | Materiality |
|---|---|---|---|
| 1 | "Nevada district loss, 9th Cir. appeal pending"; the April-2026 argument treated as a Kalshi proxy event | **Robinhood's own appeal, No. 25-7831, was consolidated with the Kalshi and Nadex appeals and was itself ARGUED AND SUBMITTED on 2026-04-16.** HOOD is a direct party to the submitted case, not a bystander to a Kalshi precedent. | **HIGH** — the binary is bound to HOOD's own docket; a ruling is directly, not derivatively, dispositive |
| 2 | "argued ~Apr-2026" (approximate) | **2026-04-16, 9:00 AM, Courtroom 1, San Francisco. Submitted the same day.** 110 days pending as of today. | Enables the hazard model |
| 3 | Realized vol 90d = **57.4%** | 63-trading-day close-to-close = **69.7%**; IBKR HV30 = **68.5%** | **HIGH** — the stale 57.4% makes 73% implied look ~15 vol points rich (a "sell premium" signal the taxable book forbids acting on) when the true IV/HV is **1.02**. Any option sizing built on 57.4% is wrong. |
| 4 | Branch B: favorable ⇒ bear p collapses to 0.12 | Two adverse channels survive a favorable ruling: (a) Nevada's **state-court** enforcement action against Kalshi is proceeding post-remand (Kalshi's removal appeal 26-1304 is **not yet briefed**, reply due 2026-08-12); (b) the **tribal/IGRA channel**, *Blue Lake Rancheria v. Kalshi* (25-7504), was argued 2026-07-10 before a **different, all-Democrat-appointed panel** and is undecided. | **MODERATE** — post-favorable bear p should be ~0.18, not 0.12; E[FV] ≈ $108, not $112 |
| 5 | "panel signalled skepticism" (news, 2026-04-17) | Still **PLAUSIBLE only** — I could not verify from the audio (110 min of argument, no transcript available and no transcription capability here). Replaced with a harder primary proxy: **the argument ran 6,610 seconds = 110 minutes against a 75-minute allocation (+47%)**. | Reclassified: a hot-bench/hard-case signal, not a direction signal |

---

## 1. DOCKET FACTS (all primary; CourtListener API v4 + docket HTML, anonymous access)

### 1.1 The HOOD-specific appeal — RESOLVED, not assumed

> **Robinhood Derivatives, LLC v. Dreitzer, et al., No. 25-7831 (9th Cir.)**
> CourtListener docket id **72247926** · appeal from **D. Nev. No. 2:25-cv-01541-APG-DJA** (Judge Andrew P. Gordon)

| Item | Value | Docket authority |
|---|---|---|
| Notice of appeal / case opened | **2025-12-12** | DE 1 |
| Posture | **RHD is the APPELLANT** — it lost the preliminary injunction below | DE 2 (PI briefing schedule) |
| Injunction pending appeal | Moved 2025-12-24 (DE 10); **referred to the merits panel, never granted** — motions panel **Barry G. Silverman, Holly A. Thomas**: *"The motion … for injunctive relief is referred to the panel assigned to decide the merits of this appeal. The clerk will place this case on the calendar for April 2026."* | DE 22, 2026-01-27 |
| **Consolidation** | **GRANTED 2026-02-26**: 25-7187 (*North American Derivatives Exchange, Inc. v. State of Nevada* — Nadex) + 25-7516 (*KalshiEX, LLC v. Hendrick/Assad*) + **25-7831 (Robinhood)**. Appellants share 45 min; appellees share 30 min. | **DE 45** |
| CFTC posture | Filed an **amicus brief** (DE 48) and **was granted leave to participate in oral argument** (DE 62 → DE 70, 2026-03-05) — **on the appellants' side** | DE 48, 62, 70 |
| **Argument & submission** | **"ARGUED AND SUBMITTED to Ryan D. NELSON, Bridget S. BADE, Kenneth K. LEE."** 2026-04-16, 09:00, Courtroom 1, San Francisco | **DE 136** |
| Argument length | **6,610 s = 110 min** vs 75 min allotted (**+47%**) | CourtListener audio 104377; source `ca9.uscourts.gov/datastore/media/2026/04/16/25-7187.mp3` |
| Post-argument filings | **18 supplemental-authority (28(j)) letters and responses**, 2026-04-28 → **2026-06-30** (last: DE 154, Nevada Resort Association). **No docket activity in July 2026.** | DE 137–154 |
| Submission status | **SUBMITTED and pending.** No en-banc petition, no order vacating submission, no supplemental-briefing order, no partial disposition. | full docket read |
| **Days pending** | **110** (2026-04-16 → 2026-08-04) | — |

**Metadata trap worth banking:** CourtListener's structured `dateArgued` field is **null** for 25-7831 (the court posted only one audio file, under lead case 25-7187). Reading the API field alone would have produced the false conclusion *"Robinhood's appeal has not been argued."* **The docket TEXT is authoritative; the structured field is not.** This is a general lesson for the litigation connector — on consolidated appeals, `dateArgued` is populated only on the lead docket.

### 1.2 Panel composition and appointment priors

| Judge | Seat | Appointed | Party (CourtListener) | Person id |
|---|---|---|---|---|
| **Ryan D. Nelson** | 9th Cir. | Trump, 2019 | R | (named in DE 136) |
| **Bridget S. Bade** | 9th Cir. | Trump, 2019-01-23 | **r** | 8538 |
| **Kenneth K. Lee** | 9th Cir. | Trump, 2019-02-06 | **r** | 8657 |

**A unanimously Republican-appointed, 2019-vintage panel.** This cuts *both* ways and I will not pretend otherwise: textualism favors the industry (the CEA's text plainly covers these contracts — even the Third Circuit **dissent** conceded it); federalism and the presumption against preemption of traditional state police powers favor Nevada. This panel is not a clean read from appointment party alone.

### 1.3 Related dockets — the full instrument set

| Court | No. | Case | Argued | Panel | Status |
|---|---|---|---|---|---|
| **9th** | **25-7187 / 25-7516 / 25-7831** | Nadex + Kalshi + **Robinhood** v. Nevada (consolidated) | **2026-04-16** | **R. Nelson, Bade, Lee** | **SUBMITTED, pending 110d — THE BINARY** |
| 9th | 25-7504 | *Blue Lake Rancheria v. Kalshi* (tribal/IGRA) | 2026-07-10 | **Murguia, McKeown, Paez** (all D-appointed) | pending 25d — **second, independent adverse channel** |
| 9th | **26-1304** | *Nevada ex rel. NGCB v. KalshiEX* — D. Nev. 2:26-cv-00406-MMD (J. Du), **removal/remand** appeal | not argued | R. Nelson, Bade, Lee | **NOT YET BRIEFED**; Kalshi reply due **2026-08-12**. Stay **DENIED** 2026-05-21. |
| 9th | 26-3106 / 26-2978 / 26-1343 | Washington v. Kalshi · Kalshi v. Johnson · Nevada v. Blockratize (Polymarket) | none | — | briefing — the next wave |
| **3rd** | **25-1922** | ***KalshiEX v. Flaherty* (NJ)** | 2025-09-10 | Chagares C.J., **Porter** (auth.), Roth (**dissenting**) | **DECIDED 2026-04-06, PUBLISHED — AFFIRMED for Kalshi, 2-1** |
| 4th | 25-1892 | *Kalshiex v. Martin* (MD) | 2026-05-07 | Gregory, Thacker, Benjamin | pending 89d |
| **6th** | **26-3196** | *KalshiEX v. Schuler* (OH) | **2026-07-30** | — | pending **5d** — newest front |
| D.C. | 24-5205 | *KalshiEX v. CFTC* (election contracts) | 2025-01-17 | Millett, Pillard, Pan | decided; industry-favorable |

### 1.4 The Third Circuit holding — read in full (41 pp), not summarized second-hand

*KalshiEX, LLC v. Flaherty*, No. 25-1922 (3d Cir. Apr. 6, 2026), Porter, J.:
- **"We hold that both field and conflict preemption apply."** The district court "did not err in holding that New Jersey law is field preempted by the Act."
- Framing is the whole case: *"New Jersey frames the issue broadly (regulating all sports gambling) rather than narrowly (regulating trading on federally designated contract markets). The text of the Act suggests that the narrow framing is the better reading."*
- The CFTC has **not** invoked the Dodd-Frank "special rule" (7 U.S.C. § 7a-2(c)(5)(C)(ii)) and **"has already certified many 'sporting events' contracts for listing"** (citing 91 Fed. Reg. 12517 n.9).
- **The dissent concedes the text:** *"[a] plain reading of the Act's text suggests that Kalshi's sports-event contracts fit comfortably within the statutory definition."* It would rule for New Jersey on the presumption against preemption and the special rule.
- **Caveat that limits the precedent's weight:** this is a **preliminary-injunction** posture — "reasonable chance of success," reviewed for abuse of discretion. It is not a final merits judgment.
- **Amicus alignment:** 34 States + D.C. + CNMI, the American Gaming Association, and the Casino Association of New Jersey filed **against** Kalshi.

---

## 2. TIMING HAZARD — empirical, from the 9th Circuit's own output

**Method.** Pulled every 9th Circuit opinion in CourtListener filed 2025-07-01 → 2026-08-04 (472 clusters; 334 carry both an argument date and a filing date; **status mix is 100% "Published"** — CourtListener's ca9 feed is published-opinion-only, which is exactly the right reference class, since a consolidated three-appeal preemption case with a 110-minute argument will not be resolved by unpublished memorandum). Restricted to argue-cohorts with **≥300 days of observation** to limit right-truncation. **n = 244.**

**Unconditional lag, argued → filed (n=244):** median **183 d** · p25 **113 d** · p75 **287 d** · p90 **385 d**

**Our case is at 110 days and pending — that is entirely ordinary.** Only ~25% of published ca9 opinions land inside 110 days.

**Conditional on still being pending at 110 days (n = 188):**

| Decision by | Raw empirical | **Hardness-adjusted (used)** | of which ADVERSE | of which FAVORABLE |
|---|---|---|---|---|
| **2026-09-30** | 27.7% | **22.1%** | 9.7% | 7.5% |
| **2026-10-31** | 39.9% | **31.8%** | 14.1% | 10.8% |
| 2026-11-30 | 52.7% | 42.1% | 18.6% | 14.3% |
| **2026-12-31** | 62.8% | **52.2%** | 23.0% | 17.7% |
| 2027-01-15 (Jan expiry) | 66.0% | 54.5% | 24.1% | 18.5% |
| **2027-03-31** | 81.4% | **75.0%** | 33.1% | 25.5% |

**Hardness adjustment (stated so it can be challenged):** I moved 20% of the mass out of the first four months into the tail, because this case is materially harder than the median published ca9 appeal — three consolidated appeals, a 110-minute argument against a 75-minute grant, a live circuit split to either create or avoid, a CFTC amicus arguing separately, and near-certain separate writings. **Direct comparator: the Third Circuit took 208 days on the identical question**, which is above the ca9 median of 183. Without the adjustment, shift every row up ~6–10 pp.

**Bottom line: there is a ~78% chance nothing has happened by Sep 30 and a ~48% chance nothing has happened by year-end.** The dominant state of the world through the entire visible option horizon is **no decision**.

---

## 3. DIRECTION — the FOR / AGAINST ledger

### FOR the industry (favorable to HOOD)

| # | Evidence | Source | Weight |
|---|---|---|---|
| F1 | **Third Circuit published holding for Kalshi on BOTH field and conflict preemption**, issued **10 days before** this argument. Panels are institutionally reluctant to manufacture a circuit split. | 3d Cir. 25-1922, read in full | **HIGH** |
| F2 | **The CFTC — the agency with exclusive jurisdiction — filed an amicus brief on the appellants' side and was granted argument time.** This is a docket fact, not a press characterization. An agency telling the court it does not want the state regulating its DCMs is the single strongest structural argument. | DE 48, 62, 70 | **HIGH** |
| F3 | The statutory text is the industry's ground, and **even the Third Circuit dissenter conceded** the contracts "fit comfortably within the statutory definition." An all-textualist panel is the best available audience for that argument. | 3d Cir. dissent | MODERATE |
| F4 | CFTC has not invoked the § 7a-2(c)(5)(C) special rule and has certified sporting-event contracts. | 91 Fed. Reg. 12517 n.9 (via 3d Cir.) | MODERATE |
| F5 | Additional amici for the industry: Paradigm Operations LP; **Former Federal Government Officials and Experts on the Scope of CFTC Jurisdiction**. | DE 46, 47 | LOW |

### AGAINST

| # | Evidence | Source | Weight |
|---|---|---|---|
| A1 | **STANDARD OF REVIEW — the most underweighted fact in the file.** All three appellants **lost below**. The panel reviews *denials* of preliminary injunctions for **abuse of discretion**. Affirmance is the low-energy path and requires no circuit split on the merits — the panel can affirm on the discretionary factors and never squarely hold that the CEA fails to preempt. | DE 1, 2, 22 | **HIGH** |
| A2 | Institutional amicus alignment is lopsided: **Amici States, Tribal Amici, American Gaming Association, North American Gaming Regulators Association + IAGR, Better Markets, Stop Predatory Gambling, Nevada Council on Problem Gambling**, plus the Nevada Resort Association as a party. (In the parallel 3rd Cir. case: **34 states + D.C. + CNMI**.) | DE 72–93 | MODERATE |
| A3 | **Same panel, five weeks post-argument (2026-05-21), wrote: *"Principles of federalism and comity tip the balance of hardships and public interest in favor of allowing Nevada an opportunity to enforce its laws in state court."*** | 9th Cir. 26-1304, DE 20 (order PDF read in full) | **MODERATE — see the re-verification note below** |
| A4 | Nevada retained **Nicole A. Saharsky** (Mayer Brown; former Assistant to the Solicitor General, 60+ Supreme Court arguments) as appellate counsel. States do not buy that for a case they expect to lose quietly. | DE 103, 26-1304 DE 26 | LOW–MODERATE |
| A5 | Secondary press, 2026-04-17: *"Ninth Circuit Signals Skepticism on Prediction Markets' Bid to Bypass State Gambling Laws."* | news RSS | **PLAUSIBLE only** — unverified from the audio |
| A6 | Independent second channel: **tribal/IGRA** appeal (25-7504) argued 2026-07-10 before Murguia/McKeown/Paez. A loss there impairs the same revenue line regardless of this panel. | CourtListener audio 105733 | MODERATE (separate binary) |

### Re-verification of the decisive-looking finding (escalate-on-decisive-findings doctrine)

A3 initially read as a smoking gun: *the same merits panel, after argument, denying Kalshi relief.* **Pulling the order PDF defuses most of it.** No. 26-1304 is an appeal from a **remand order** — Kalshi removed a Nevada state-court enforcement action under 28 U.S.C. § 1442 and the district court sent it back. The panel's "not likely to succeed" finding is about **federal-question jurisdiction and the well-pleaded-complaint rule**, and it expressly says the opposite of a merits ruling:

> *"Kalshi's argument that the Commodity Exchange Act (CEA) preempts Nevada gaming law is **an affirmative defense**, which cannot by itself give rise to federal question jurisdiction, 'even if both parties concede that the federal defense is the only question truly at issue.'"* (citing *Caterpillar v. Williams*)

**So A3 is NOT a merits signal on preemption, and I am downgrading it accordingly.** What survives is (a) genuinely federalism-forward *atmospherics* from the exact panel five weeks after hearing the merits, and (b) a hard structural fact: **Nevada now has a live state-court enforcement action against Kalshi that a favorable federal ruling does not extinguish.**

### Composite

| Outcome | Court file | **This pack** | Reasoning for the shift |
|---|---|---|---|
| **FAVORABLE** (reverse; preemption; sports contracts relistable in the 9th Cir. states) | 0.40 | **0.34** | F1+F2 are strong, but A1 (abuse-of-discretion review of a denial) is a structural headwind the file omitted |
| **ADVERSE** (affirm; circuit split created; state enforcement green-lit across CA/WA/NV/AZ/OR) | 0.45 | **0.44** | essentially unchanged — I am not manufacturing a differentiated view |
| **MIXED / NARROW / REMAND** (procedural affirmance, holding confined to the PI record, or partial) | 0.15 | **0.22** | the abuse-of-discretion path *is* the mixed path; for the equity this is roughly a non-event |

**I agree with the court's bear lean.** The change is that ~6pp moves from FAVORABLE into MIXED, which is the more honest home for "the panel affirms without reaching preemption."

---

## 4. THE VENUE PRIOR — the absence is the finding

**Kalshi.** Searched the v1 series-search endpoint across 12 query terms and scanned 1,000 open markets. **There is no Kalshi market on the Ninth Circuit ruling, on prediction-market legality, on CFTC jurisdiction, or on any court decision affecting event contracts.** Zero.

**But Kalshi does list markets on Robinhood's event-contract business:**

| Series | Question | Strikes | Closes | Bid | Ask | Volume | Open interest |
|---|---|---|---|---|---|---|---|
| **KXHOOD** | Robinhood event-contract trading volume, Q3 2026 | $10bn → $24bn | 2027-03-04 | **None** | **None** | **None** | **None** |
| **KXHOODA** | Robinhood event-contract volume, FY2026 | $50bn → $100bn | 2027-05-12 | **None** | **None** | **None** | **None** |
| KXHOOD / KXHOODA | HOOD funded customers, Gold subscribers | various | 2027–2028 | None | None | None | None |

**Every single strike is listed and has never been quoted or traded.**

**Polymarket.** No court-ruling market either. Nearest live instruments:

| Market | YES | Liquidity | Volume | Ends |
|---|---|---|---|---|
| "Law banning sports prediction markets enacted in 2026?" | **0.22** | $409 | $17.5k | 2026-06-30 — **stated end date already passed, unresolved ⇒ stale/broken, do not use** |
| "Sports Prediction Markets taxed as gambling?" | **0.095** | $2,920 | $44.0k | 2027-04-16 |
| "Which DCMs self-certify sports event contracts by Dec 31, 2026?" (ForecastEx / Cboe / ICE / Small Exchange) | 0.10–0.14 | $250–$960 | $0.6–3.1k | 2026-12-31 |

**FINDING — no venue anywhere prices this binary, and there is therefore NO ANCHOR.** The political-class doctrine (venue price is the anchor; ±0.05 deviation needs a named mechanism) **does not bind here**, and our composite in §3 stands on its own evidence.

**The absence is itself a positive microstructure datum, and it is the sharpest thing in this pack.** The industry will list a market on its own quarterly notional, on its competitor's funded-customer count, and on whether Congress caps gambling-loss deductions — but not on the appeal that decides whether the product is lawful in five states. Two candidate mechanisms, neither verified:
1. **Self-referential listing constraint** — a CFTC-regulated DCM listing a contract on its own regulatory survival is a conflict a compliance function would not clear, and it would be an unhelpful exhibit in the very litigation at issue.
2. **Settlement ambiguity** — "rules against prediction markets" is not a clean binary. Affirm-on-abuse-of-discretion / reverse / partial / remand / dismiss-as-moot-on-CFTC-rulemaking is a five-way outcome space with no crisp settlement source. My own §3 needed three states, not two.

Mechanism (1) is the interesting one and it generalises: **self-referential regulatory binaries are a structural blind spot in event-contract venues — the exact questions where the venue has the best information are the ones it cannot list.** That is a permanent aggregation-cost moat, not a temporary gap. Bank it.

**Do not anchor on the 0.22 / 0.095 Polymarket prints.** At $409 and $2,920 of liquidity those are opinions, not prices; one of the two is a broken market past its own end date; and both ask about **legislative/tax** channels, not the judicial one.

---

## 5. MISPRICING CHECK — joint, coupled, terminal-payoff

### 5.1 (a) Term structure — flat, with NO event hump anywhere

Spot $92.17. yfinance mid-IV, ATM = nearest strike to spot; 08-04 close.

| Expiry | DTE | ATM call IV | ATM put IV | c110 IV | p75 IV | **skew (c110 − p75)** | call OI | put OI |
|---|---|---|---|---|---|---|---|---|
| Sep-18 | 45 | 73.9% | 66.4% | 73.4% | 69.2% | **+4.2** | 111,515 | 84,196 |
| Oct-16 | 73 | 72.4% | 65.5% | 71.3% | 68.9% | **+2.4** | 45,007 | 31,549 |
| **Nov-20** | 108 | **73.9%** | 66.7% | 71.4% | 69.7% | **+1.7** | 33,854 | 24,377 |
| **Dec-18** | 136 | **74.5%** | 67.0% | 71.7% | 69.6% | **+2.1** | 71,299 | 44,112 |
| Jan-15 | 164 | 74.5% | 65.0% | 71.9% | 67.9% | **+4.0** | 177,048 | 125,004 |
| Mar-19 | 227 | 73.0% | 66.3% | 71.6% | 67.6% | +4.0 | 44,998 | 26,474 |
| Jun-17 | 317 | 73.5% | 65.4% | 73.1% | 65.6% | +7.5 | 34,683 | 23,941 |

**Two findings, and the second is the more important one.**

1. **The term structure is flat — 72–75% ATM from September through June. There is no hump, no kink, no bump at any tenor.** For an unscheduled decision that could land in any week, the market has priced in exactly nothing. Cross-checked against IBKR: **underlying IV 69.7% vs HV30 68.5% ⇒ IV/HV = 1.02.** HOOD options are neither rich nor cheap; there is no event premium to buy *and none to sell*.
2. **The skew is INVERTED at every single tenor.** At equal percentage moneyness (+19.4% / −18.6% from spot), calls trade **1.7 to 7.5 vol points OVER** the equidistant puts. If the market feared an adverse ruling gapping the stock toward $50–70, downside puts would be bid. They are not. Today's IBKR flow corroborates: **call volume 87,147 vs put volume 24,231 = 3.6:1.**

**The market is not underpricing the direction of this event. It is not pricing the event at all** — the surface is a pure high-beta, upside-speculation retail surface.

### 5.2 (b) Joint scenario pricing — ONE pass over timing × outcome

Per house doctrine (`feedback_catalyst_option_couple_timing_outcome`): a single joint simulation, never a timing pdf multiplied by a separate outcome probability. 600,000 paths.

- **Decision date** sampled from the §2 empirical hardness-adjusted hazard (right-truncation-corrected ca9 cohort, n=244).
- **Outcome | decision** = FAVORABLE 0.34 / ADVERSE 0.44 / MIXED 0.22 (§3).
- **Jump at the decision date**, lognormal with dispersion (so the outcome is not a point mass): favorable ×1.21 (σ 0.10), adverse ×0.72 (σ 0.12), mixed ×1.00 (σ 0.06). Adverse ×0.72 from $92.17 ⇒ ~$66, consistent with the bear path toward the court's $50 FV as estimates are rebuilt.
- **Diffusion between now and expiry** — and this is the step that makes the test honest: **the diffusion σ is solved at each tenor so that the model's TOTAL log-return volatility equals that expiry's own market ATM IV.** Without this, adding a jump on top of a market-level diffusion inflates total variance above the market's and makes every long option look cheap by construction. Calibrated diffusion σ ≈ 0.66–0.68, with the jump supplying ~0.27–0.31 of vol.
- Payoffs are **TERMINAL at expiry** (options pay terminal, not touch). Debits are struck at the **ASK** — the buyer's real price.

**Result — the question is now purely whether the SHAPE is mispriced, with the LEVEL held at market:**

| Structure | Debit (ask) | E[payoff] | **EV $** | **EV %** | P(profit) |
|---|---|---|---|---|---|
| Sep 95/115 call spread | 5.54 | 5.35 | −0.19 | **−3.5%** | 32.1% |
| Oct 95/115 call spread | 6.20 | 5.84 | −0.36 | **−5.8%** | 32.9% |
| **Nov 95/115 call spread** | 7.10 | 6.10 | −1.00 | **−14.1%** | 32.7% |
| **Dec 95/115 call spread** | 7.10 | 6.17 | −0.93 | **−13.1%** | 32.8% |
| Jan 95/115 call spread | 7.00 | 6.18 | −0.82 | **−11.7%** | 32.9% |
| Jan 100/120 call spread | 6.00 | 5.52 | −0.48 | **−8.0%** | 30.0% |
| Nov 80/65 put spread | 5.10 | 5.11 | +0.01 | +0.2% | 37.1% |
| Dec 80/65 put spread | 5.40 | 5.61 | +0.21 | +3.9% | 39.8% |
| Jan 80/65 put spread | 5.65 | 5.96 | +0.31 | **+5.4%** | 41.8% |
| Dec 75P + 115C strangle | 16.75 | 16.80 | +0.05 | +0.3% | 36.6% |
| Jan 75P + 110C strangle | 20.00 | 20.51 | +0.51 | +2.5% | 37.7% |

**Which expiry actually spans the hazard mass?** None of the liquid ones do well. Cumulative P(decision) by expiry: **Sep-18 → 20%, Oct-16 → 26%, Nov-20 → 40%, Dec-18 → 49%, Jan-15 → 55%.** Even the January contract is a coin-flip on whether the event occurs inside its life. To capture 75% of the hazard mass you need **March/April 2027**, where the bid/ask is wide and the theta bill for a 73-vol name is enormous.

### 5.3 (c) VERDICT: **FAIRLY PRICED — and structurally un-extractable through options**

**The event is not underpriced. It is fairly priced, for a reason that is worth encoding.**

- **The event is sub-sigma.** At Nov-20, σ√T = 0.735 × √0.296 = **40.0%**. The favorable jump (+21%) is **0.5σ**; the adverse jump (−28%) is **0.7σ**. **A binary that moves the stock less than one standard deviation does not require a vol hump.** HOOD's ambient 73% implied volatility already spans the entire outcome range. There is no vol-surface anomaly to arbitrage, and the flat term structure is *correct*, not an oversight.
- **Every long call structure has negative EV** (−3.5% to −14.1%) — you are buying a 73-vol option, paying the ask, and being paid off in only ~33% of paths.
- **The only positive-sign structures are bearish put spreads (+0.2% to +5.4%)**, which is the coherent consequence of our composite leaning adverse (0.44) against a call-skewed surface. **But +5.4% is inside the bid/ask** — the Nov 110 call alone quotes 7.90/8.90, a 12% spread; one round trip erases it — and it is well inside the model's own error bars on P_ADV, on the jump magnitudes, and on the hazard. **It is not a trade. It is noise with a sign.**
- **And the taxable book cannot express the one thing that IS mispriced.** The genuine anomaly is the *inverted skew* — calls bid over puts into a binary whose bad tail is a −28% gap. The clean expression is selling upside calls, which the standing no-premium-selling doctrine forbids (non-deferrable short-term ordinary income). Correctly forbidden: this is exactly the case where a small theoretical edge would be paid for with an unbounded meme-momentum tail, per `feedback_meme_momentum_overruns_covered_call_strike`.
- **Direction contradiction, stated plainly:** the court's preferred Branch B is a *bullish conditional buy*, while our composite is *bear-leaning* (0.44 vs 0.34). Those are consistent only because Branch B is conditioned on the favorable branch **having already resolved**. **Any pre-positioned long is therefore an unconditional bet the court's own scenario weights do not support.**

**Single best expression: EQUITY, BRANCH B, ON THE RULING DAY. NO PRE-POSITION.**

Buying the resolution rather than the drawdown was the court's own conclusion, and instrumentation confirms it for a reason the court did not have: **~78% of the time nothing happens by Sep 30 and ~48% of the time nothing has happened by year-end, so any pre-position is ~half theta and ~half a coin-flip on an outcome we grade at 44% adverse.** Waiting is free. The optionality is in the equity, at the ask, on the day.

---

## 6. PACK SPEC

### 6.1 Pre-committed branches

**⚠️ BRANCH B MUST BE RESTATED — as written it almost never fires.** The simulation is unambiguous: **P(spot ≤ $95 AND a favorable ruling has already landed) = 5.0% by Nov-20, 6.6% by Dec-18, 7.8% by Jan-15.** A favorable ruling *is* a +21% jump, so from a $92 spot the stock clears $95 on the headline in almost every favorable path. **A $95 cap is a limit that fills only if the market ignores the ruling.**

| Branch | Trigger (verified from primary, not press) | Action |
|---|---|---|
| **A — de-rate completes, binary has not fired** | Spot ≤ $80 with **no** docket disposition in 25-7187/7516/7831 and no adverse tribal ruling in 25-7504 | GTC ladder $80 (0.35% of book) / $70 (0.25%); total 0.60%. **Standing cancel on any adverse disposition, cert grant, or new state cease-offering agreement.** Unchanged from the court. |
| **B — FAVORABLE (RESTATED)** | 9th Cir. reverses or holds the CEA preempts, in the consolidated appeal | Rebuild E[FV] with bear p = **0.18** (not 0.12) ⇒ **E[FV] ≈ $108**. **Buy at ≤ 0.88 × rebuilt E[FV] (≈ $95 only if the stock has not moved; ≈ $95–100 realistically), NOT at a fixed $95.** Size 0.6–0.9% of book. Do not chase above 0.95 × E[FV]. |
| **C — ADVERSE** | 9th Cir. affirms the PI denials / holds no preemption | **No knife-catch. Cancel all resting Branch-A legs same session.** Re-court from scratch at $55–65 against a rebuilt FY27 with the event-contract line impaired. |
| **D — MIXED / NARROW / REMAND** (p 0.22, the second-most-likely single outcome) | Affirmance on abuse-of-discretion without reaching preemption, or partial/remand | **Decay branch — not a catalyst.** The binary is not resolved; it is deferred to a merits judgment 12–18 months out. Reduce the catalyst's weight in E[FV] toward zero, hold WATCH, do **not** treat it as a Branch-B trigger. |
| **E — MOOTED BY CFTC RULEMAKING OR LEGISLATION** | A CFTC final rule under 7 U.S.C. § 7a-2(c)(5)(C) / 17 C.F.R. § 40.11, or CLARITY-Act-style federal preemption enacted | Separate branch: the judicial binary is superseded. Re-court against the rule's text — a CFTC rule *prohibiting* gaming contracts is the true worst case (it closes every circuit at once), and a rule *permitting* them ends the litigation nationally. **Asymmetrically larger than the appeal.** |
| **F — EN BANC / CERT** | Rehearing en banc granted, or SCOTUS cert granted on the 3rd Cir. split | Decay branch: 9–18 month extension, volatility without resolution. Cancel Branch A; do not initiate Branch B. |

### 6.2 Tripwires — cadence and plane

| Plane | Instrument | Cadence | Fires on |
|---|---|---|---|
| **Docket (primary)** | CourtListener docket alerts on **72247926** (25-7831), **72229053** (25-7187), **72237443** (25-7516) | **daily** — a disposition can land any Tuesday–Friday | any ORDER / OPINION / MEMORANDUM / "submission vacated" entry |
| **Docket (second channel)** | **72251825** (25-7504 Blue Lake tribal, Murguia/McKeown/Paez) | daily | disposition — an independent impairment of the same revenue line |
| **Docket (next wave)** | **72376508** (26-1304, Kalshi reply due **2026-08-12**), 73351175 (WA), 73324497, 72376505 (Polymarket) | weekly | briefing completion, calendaring |
| **Sister circuits** | ca4 25-1892 (argued 05-07, 89d) · **ca6 26-3196 (argued 07-30, 5d)** · any cert petition from 3d Cir. 25-1922 | weekly | a ca4/ca6 decision either deepens or resolves the split and **will move HOOD before the 9th Cir. rules** — this is the most likely *early* mover |
| **CFTC** | cftc.gov press releases + Federal Register § 40.11 / event-contract rulemaking docket | weekly | Branch E |
| **State AG (entity-disclosure doctrine)** | NV / NJ / MA / MI / WA / AZ / OR AG + gaming-regulator releases; **MA Securities Division** investigation | weekly | new cease-and-desist, new suit, or a **cease-offering agreement** — kill trigger #2 in the court file |
| **Kalshi PR plane** | Kalshi + Polymarket blog/press; **and re-check whether either venue ever lists a legality market** | monthly | a listing appearing **is itself the signal** — it would create the anchor this pack says does not exist, and would supersede our §3 composite |
| **Company** | HOOD 8-K / 10-Q Legal Proceedings; event-contract revenue in the Note-6 disaggregation | per filing | sequential decline in event-contract revenue = court kill trigger #2 |

### 6.3 Freezable calls

**PRIMARY — timing (this is where the empirical base rate lives and where the pack is falsifiable):**

> **HOOD-9CIR-TIMING | 2026-12-31 | BAR: The U.S. Court of Appeals for the Ninth Circuit files a disposition (opinion, memorandum, or order resolving the appeal) in the consolidated appeals Nos. 25-7187 / 25-7516 / 25-7831 on or before 2026-12-31. | our_p = 0.52**
> *Venue anchor: NONE EXISTS — verified across Kalshi (v1 series search, 12 terms, 1,000 open markets) and Polymarket (Gamma public-search, 6 terms). Resolves from the public CourtListener/PACER docket. Base rate: 62.8% raw from the n=244 ca9 published-opinion cohort conditional on pendency at 110 days, marked down to 52% for case hardness (3 consolidated appeals, 110-min argument, near-certain separate writings, 3d Cir. comparator 208 days).*

**SECONDARY — direction, graded only if the primary resolves YES:**

> **HOOD-9CIR-OUTCOME | conditional on a disposition by 2027-06-30 | BAR: The disposition is favorable to event contracts — i.e. it reverses or vacates the denial of preliminary injunctive relief as to Robinhood Derivatives, or holds that the Commodity Exchange Act preempts the Nevada gaming-law enforcement at issue. | our_p = 0.34**
> *Complement: ADVERSE (affirmance on the merits of preemption) 0.44; MIXED/NARROW/REMAND (affirmance without reaching preemption, or partial/remand) 0.22. No venue anchor exists.*

### 6.4 Constraint check

- **Open pre-print binaries: NO BREACH.** This pack recommends **no position**, so it consumes **zero** of the house-wide 2-binary cap. Flagging explicitly: had the recommendation been a Nov/Dec call spread, it would have consumed one slot **and** breached the spirit of the cap, since ~50% of its life is a pure coin-flip on an unscheduled ruling.
- **Binary tails: capped and unlevered.** Branch A total 0.60% of book, Branch B 0.6–0.9%, both cash equity, no leverage, no premium sold. HOOD shares the single "retail speculative flow" axis cap with COIN (ρ 0.787 since the BTC top) — **do not size against independent name caps.**
- **Taxable-book doctrine: respected.** No premium selling. The one genuinely mispriced object identified here (the inverted call skew) is deliberately left on the table.
- HOOD's existing frozen call (2026-11-15, Q3 revenue ≥ $1.30bn & crypto ≤ $125M, our_p 0.66) is a **prediction**, not a position, and is unaffected.

---

## 7. MECHANISM — what to encode in the knowledge graph

**Masking channel:** *venue non-listing of self-referential regulatory binaries.* A CFTC-regulated DCM will list markets on its own quarterly notional and on a competitor's funded-customer count, but not on the appeal that determines whether its product is lawful. The best-informed participants are structurally barred from posting a price.

**Signal channel:** the **federal appellate docket** — free, primary, and daily. Consolidation orders, submission entries, panel identity, argument duration, and 28(j) traffic are all public and machine-readable, and a disposition posts to CourtListener the same day it is filed.

**Signal-to-price latency: ~0.** This is the crucial asymmetry and it is why the correct trade is *no pre-position*. Unlike the Note-6 revenue-mix mechanism in the parent court (1–3 quarters of latency, a real aggregation-cost moat), a court disposition is public, instantaneous, and simultaneously visible to everyone. **There is no latency to harvest, so there is no edge in anticipating it — only risk in doing so.** The edge available here is entirely in *reaction quality*: having the rebuilt E[FV], the branch map, and the size pre-committed before the headline prints, so the response is mechanical rather than improvised.

**Anti-masking finding (bank per `feedback_anti_masking_findings_have_value`):** the *expected* masking — an IV hump or downside skew ahead of an unscheduled legal binary — is **absent**, and the absence is correct rather than an oversight. When ambient implied volatility exceeds the event's own magnitude (event jump < 1σ over the option's life), a rational surface shows **no** event structure. **Generalisable screen: before pricing any legal/regulatory catalyst through options, compute `|jump| / (σ_IV × √T)`. If that ratio is below ~1.0, the option market cannot express the event and the correct instrument is the underlying.** Here it is 0.5 (favorable) and 0.7 (adverse).

---

## 8. VERIFICATION LEDGER

| Claim | Method / authority | Finding |
|---|---|---|
| HOOD's own 9th Cir. appeal exists and is identified | CourtListener search API v4, `type=r&court=ca9` | **VERIFIED** — *Robinhood Derivatives, LLC v. Dreitzer*, No. 25-7831, docket 72247926 |
| Appeal from the Nevada PI denial | Docket DE 1, DE 2 | **VERIFIED** — D. Nev. 2:25-cv-01541-APG-DJA (J. Gordon); RHD is appellant |
| Consolidated with Kalshi and Nadex | Docket **DE 45** (2026-02-26) | **VERIFIED** — 25-7187 + 25-7516 + 25-7831; 45 min / 30 min |
| Argued and submitted 2026-04-16 | Docket **DE 136** | **VERIFIED** — verbatim: *"ARGUED AND SUBMITTED to Ryan D. NELSON, Bridget S. BADE, Kenneth K. LEE"* |
| Panel identity and appointment party | DE 136 + CourtListener people 8538 / 8657 | **VERIFIED** — Bade (r, 2019-01-23), Lee (r, 2019-02-06), R. Nelson (Trump 2019) |
| Argument duration 110 min vs 75 allotted | CourtListener audio 104377 (`duration` 6610 s) + DE 45 | **VERIFIED** |
| CFTC amicus on the appellants' side, granted argument time | DE 48, DE 62, DE 70 | **VERIFIED** |
| No post-argument order; case still submitted | full docket read to DE 154 (2026-06-30) | **VERIFIED** — 18 28(j) letters, no disposition, no July activity |
| 3rd Cir. ruled for Kalshi | ca3 25-1922 opinion PDF, 41 pp, read in full | **VERIFIED** — affirmed 2-1, field AND conflict preemption, Porter J., Roth dissenting; argued 09-10-2025, decided 04-06-2026 (208 d) |
| Same panel's 2026-05-21 stay denial is a merits signal | 9th Cir. 26-1304 DE 20 order PDF, read in full | **REFUTED as a merits signal** — the holding is on federal-question jurisdiction; the panel calls CEA preemption "an affirmative defense." Downgraded. |
| ca9 argued→decided base rate | 472 ca9 opinion clusters, 334 with both dates, 244 mature (≥300 d observed), 100% Published | **VERIFIED** — median 183 d; 62.8% by 2026-12-31 conditional on pendency at 110 d |
| No Kalshi market on the ruling | Kalshi v1 series search, 12 terms; 1,000 open markets scanned | **VERIFIED ABSENT** |
| Kalshi lists HOOD event-contract volume markets, untraded | Kalshi v2 `markets?series_ticker=KXHOOD/KXHOODA` | **VERIFIED** — all strikes bid/ask/volume/OI = null |
| No Polymarket market on the ruling | Gamma `public-search` (6 terms) + `events?slug=` | **VERIFIED ABSENT**; nearest live 0.22 / 0.095, both legislative/tax, both sub-$3k liquidity, one past its own end date |
| Live spot | IBKR snapshot, contract 504546674 | **VERIFIED** — $92.17, bid 92.17 / ask 92.20, `is_close=false` |
| Options term structure flat, skew inverted | yfinance chains, 7 expiries; cross-checked vs IBKR IV/HV | **VERIFIED** — ATM 72–75% Sep→Jun; c110 over p75 at every tenor; IV/HV 1.02; today's flow 3.6:1 calls |
| Court file's 57.4% realized vol | recomputed, 63-trading-day close-to-close + IBKR HV30 | **CORRECTED** — 69.7% / 68.5% |
| Branch B's $95 cap executes | 600k-path joint simulation | **REFUTED** — P(spot ≤ 95 AND favorable already ruled) = 5.0% / 6.6% / 7.8% at Nov / Dec / Jan |

### GAPS — UNVERIFIABLE ≠ CLEAN

1. **Oral-argument question-count asymmetry NOT measured.** The audio is available (110 min) but there is no transcript and no transcription capability in this session. **The "panel signalled skepticism" claim therefore remains PLAUSIBLE-secondary and is doing no work in the §3 composite.** *This is the highest-value remaining escalation: transcribe `ca9.uscourts.gov/datastore/media/2026/04/16/25-7187.mp3` and count questions per side. It would be the only direct read on the panel's lean, and it is free.*
2. **The briefs were not read.** RHD's opening brief (DE 15), reply (DE 58), and the CFTC amicus (DE 48) are downloadable from CourtListener/Internet Archive. The precise question presented — pure preemption vs. abuse-of-discretion framing — determines how much weight ledger item A1 deserves, and A1 is currently the single largest driver of the shift from 0.40 to 0.34.
3. **Sports vs non-sports split of event-contract revenue still NOT DISCLOSED** (inherited top gap). Only sports contracts are exposed. The 40–60% impairment in the bear case remains an assumption, not a finding, and it sizes the entire adverse branch.
4. **Outcome probabilities are judgment, not frequency.** 0.34 / 0.44 / 0.22 rests on a ledger of eight items with no base rate behind it. There is no venue anchor to check it against — that is §4's finding, and it is a genuine limitation of this pack, not a strength.
5. **Hardness adjustment (20% mass shift) is a judgment call**, defensible from the 208-day 3rd Cir. comparator and the 110-minute argument but not itself estimated. Raw empirical rows are printed in §2 so the principal can use them unadjusted.
6. **Jump magnitudes (+21% / −28%) are assumptions** carried from the court's $112 / $50–70 scenario FVs, not estimated from comparable rulings. The §5.3 verdict is robust to them, however: the conclusion that the event is sub-sigma holds for any jump under ~±40%.
7. **RECAP/CourtListener docket coverage is not real-time.** Entries appear when a user pulls them from PACER. A disposition could be filed hours before it surfaces. **The daily docket alert is necessary but not sufficient — pair it with a price tripwire.**
