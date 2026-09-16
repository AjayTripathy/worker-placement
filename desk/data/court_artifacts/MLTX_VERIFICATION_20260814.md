# MLTX — POST-ADJUDICATION VERIFICATION PACK
**Run 2026-08-14 · SignalOS · primary-source only**
Mandate: the 2026-08-14 court adjudicated HALF-STARTER GATED but left the load-bearing claims unverified. Both gates are now resolved from primary sources. Live tape pulled before any valuation claim.

**Live tape (IBKR, 2026-08-14):** last **$16.52**, bid 16.52 / ask 16.54, prior close 16.50. 13w high 23.29 · 52w high 62.75 · 52w low 5.95. (Court used a pack-sourced $16.59.)

**Primary sources read this session:** Q2-26 10-Q (accession 0001821586-26-000010, `mnlk-20260630.htm`, 1.20MB, fetched clean via `desk/sec_fetch.py` — no 403), 8-K 2026-08-10 + Exhibit 99.1 press release, 8-K 2026-06-25, 8-K 2026-07-15, SEC XBRL companyfacts, CT.gov v2 records + posted results for 14 trials.

**The EDGAR 403 that blocked all three court stages was an artifact of the caller, not of sec.gov.** `desk/sec_fetch.py` returned 200 on every document on the first attempt. No r.jina.ai proxy was needed. Every "COVERAGE GAP — EDGAR 403" flag in the court record is void.

---

## PER-CLAIM TABLE

| # | Claim | Primary source | Found | Verdict |
|---|---|---|---|---|
| **1. HERCULES / RUNWAY** |
| 1a | Hercules facility size "$400M" | 10-Q Note 4 | Facility is **$500.0M** aggregate; $400M is the *undrawn* balance. Red's "$400M Hercules" was right as capacity, wrong as facility. | **CONFIRMED (as undrawn)** |
| 1b | Drawn balance unverifiable | 10-Q Note 4 + balance sheet | **$100.0M principal drawn** (Tranche 1 $75M funded 3/31/25 + Tranche 2 $25M funded 2/20/26). Carrying value $99.514M; End-of-Term Charge accreted $5.081M. | **REFUTED — fully verifiable** |
| 1c | Undrawn capacity is $400M "available" | 10-Q Note 4 + MD&A | $400M undrawn, but **$0 is committed-and-drawable today**. T3 $50M gated on IZAR-1 *and* IZAR-2 both hitting primary; T4 $50M **expires 2026-08-20 and its market-cap gate is already failing**; T5 $100M gated on FDA *approval*; T6 $200M "**subject to approval by the Lenders in their discretion**" — not committed capital at all. | **REFUTED as marketed** |
| 1d | Covenants / warrants | 10-Q Note 4 | "Customary covenants, such as financial covenants"; **in compliance as of 6/30/26**. **No warrants attached** — facility is explicitly non-dilutive. Secured first-priority on substantially all assets **including intellectual property**, guaranteed by material subsidiaries incl. foreign. Interest = max(WSJ prime +1.45%, 8.45%); effective rate 9.93%; matures 4/1/2030; EOT charge 4.25–6.95%; PIK option available, unused. | **CONFIRMED** |
| 1e | Cash / runway vs burn | XBRL + 10-Q | $537.0M cash + ST marketable securities at 6/30/26 ($477.9M cash alone). 1H26 operating cash outflow **$121.8M** (≈$60.9M/qtr); Q2 opex $61.66M; Q2 net loss $61.8M. Current assets exceed current liabilities by $524.6M. Company guides runway to **mid-2028** — arithmetically consistent at flat opex (8.7 quarters), not at a commercial build. | **CONFIRMED** |
| 1f | Cap structure | 10-Q Note 11/12 | 83,606,685 Class A at 6/30/26 → **85,106,685 at 8/1/26** (cover). Class B **0**, Class C **0** (all converted; NCI eliminated, A&R Shareholders' Agreement terminated), preference shares **0**. **1,000,000 pre-funded warrants** outstanding, $0.0001 strike, immediately exercisable, no expiry, equity-classified. Plus 3,001,553 options/unvested RSAs. ATM: $213.8M remaining. | **CONFIRMED** |
| 1g | Court's EV "~$845M, an upper bound" | derived from the above at live $16.52 | Market cap (86.1M incl. pre-funded) = **$1,422.5M**; + debt $100.0M − cash $537.0M = **EV ≈ $985M** (~$960M pro-forma for the $28.5M net over-allotment less burn). The court's $845M omitted the drawn debt and the pre-funded warrants. **Unverified debt made $845M a LOWER bound, not an upper bound** — the direction was backwards on both benches. EV is ~15% higher than courted. | **REFUTED** |
| **2. PLACEBO-FLOOR COMPUTATION (blue's decisive overturn)** |
| 2a | "42.1% ACR50" — company's actual disclosure | 8-K 2026-08-10 Ex-99.1 (primary) | **42.1% is the ACR50 response at Week 16 in the sonelokimab 60 mg *with-induction* arm only** — one of two active arms in a 3-arm trial. Company text: "Consistent with the unblinding protocol defined with the FDA, topline disclosure at Week 16 includes absolute response levels and endpoint outcomes for the sonelokimab 60 mg with induction arm." The without-induction arm is undisclosed. Selective, but **disclosed as selective and attributed to a pre-agreed FDA unblinding protocol**. | **CONFIRMED w/ material qualifier** |
| 2b | Trial-identity binding (AVIR lesson) | CT.gov NCT06641076 + PR + 10-Q | Binding is **clean**. NCT06641076 = IZAR-1, org study ID **M1095-PSA-301**, sponsor MoonLake Immunotherapeutics AG, Phase 3, 3-arm (60mg w/ induction, 60mg w/o induction, placebo), triple-masked, n=960 est., bio-naïve PsA, primary completion 2027-02-04, last updated 2026-08-10. The NCT appears in the company's own text. No extractor artifact. | **CONFIRMED** |
| 2c | **BLA-relevant program ≠ the 42.1% trial** | PR milestone table + 10-Q MD&A | **The ~9/30 BLA is for HIDRADENITIS SUPPURATIVA**, built on VELA-1/VELA-2 + MIRA + adolescent data ("We have started preparing the BLA to seek approval of SLK in the United States in HS and adolescent HS"). **IZAR-1 (PsA, the 42.1%) is a different indication and contributes nothing to the BLA.** Blue's placebo-floor bound therefore does **not** de-risk the ~9/30 submission or the end-Nov acceptance — it is a separate, later option. The court's verdict text runs the two together. | **PROGRAM-ATTRIBUTION ERROR IN THE RULING** |
| 2d | Placebo floor "stable 10-15%" | CT.gov **posted results**, 9 registrational PsA trials | Bio-naïve/csDMARD-IR placebo ACR50: BE OPTIMAL 10.0% (n=281, Wk16) · FUTURE 5 8.1% (n=332, Wk16) · SELECT-PsA 1 13.2% (n=423, Wk12) · SPIRIT-P1 15.1% (n=106, Wk24) · DISCOVER-2 14.2% (n=246, Wk24) · DISCOVER-1 9.6% (n=114, Wk24) · KEEPsAKE-1 11.3% (n=481, Wk24) · KEEPsAKE-2 9.3% (n=219, Wk24) · FUTURE 2 7.1% (n=98, Wk24). **Mean 10.9%, median 10.0%, range 7.1–15.1, SD 2.6pp.** Wk12–16 subset: 8.1/10.0/13.2, mean 10.4%. | **CONFIRMED — floor real, band slightly wider/lower (7–15%, centered ~11%) than blue's 10–15%** |
| 2e | Variance "actually low"? | same | **Yes — genuinely low.** SD 2.6pp across 9 trials, 4 sponsors, 6 mechanisms, 12 years. Every bio-naïve/csDMARD-IR trial lands in 7–15%. Contrast the HS HiSCR75 placebo that killed VELA-2: VELA-1 delta 17% (p<0.001) vs VELA-2 delta 9% (p=0.053) on identical design — company's own words, "intercurrent events in the higher-than-expected placebo arm." **Blue's core PsA-≠-HS distinction is empirically correct.** | **CONFIRMED** |
| 2f | "→ implies ~30pp delta" | derived | 42.1 − ~10.4 (Wk16 bio-naïve central) ≈ **~32pp**, consistent with blue. But this is a **cross-trial inference against a different drug's population**, and three qualifiers apply — see 2g. | **PLAUSIBLE-STRONG, not CONFIRMED** |
| 2g | *(new)* Imputation basis of the 42.1% | PR full text | **The PR never states the analysis basis** — no NRI, no non-responder imputation, no observed-case label, no p-value, no CI, no n. The comparators above are NRI. This company reported its Week-52 HS figure (67.2%) **as-observed, n=396 of ~840 randomized**. Mitigant, from the PR: "the drop-out rate of IZAR-1 until Week 16 is low and in line with other trials in PsA." Bounded, but the basis is undisclosed and neither bench raised it. | **UNVERIFIABLE — the sharpest open qualifier on blue's bound** |
| 2h | "Significance is asserted at topline" | PR full text | Partly. The PR says "The primary endpoint of ACR50 **was met**" and "met all clinical endpoints." But **"statistically significant" is applied explicitly only to HAQ-DI and SF-36 PCS**; ACR50/ACR20/MDA/PASI90 carry "met" and "significant responses were observed" (ambiguous register). And the same PR says "Comparative analyses versus placebo and detailed treatment arm data remain blinded." "Met the primary endpoint" in a placebo-controlled trial is a hard, 10b-5-consequential assertion — so blue is right that a VELA-2-style significance miss is off the table — but it rests **solely on the issuer's characterization**, with no p-value, no delta, no placebo rate, and no independent check before H1 2027. | **CONFIRMED with reduced weight** |
| **3. ENDPOINT HIERARCHY (RARE lesson)** |
| 3 | Is ACR50-at-Wk16 primary or an emphasized secondary? | CT.gov NCT06641076 + PR | **PRIMARY.** Registry: single primary outcome = "Response rate of participants achieving at least a 50% improvement in the ACR criteria (ACR50)", timeFrame Week 16. PR agrees verbatim. ACR20, MDA, HAQ-DI, PASI90, SF-36 PCS, vdHmTSS are the registered **key secondaries** — and the PR labels them as secondaries. **No hierarchy inversion, no endpoint-switching.** Registry record was updated 2026-08-10, the day of the release. | **CONFIRMED — clean, no flag** |
| **4. CALENDAR FROM PRIMARY** |
| 4a | BLA submission ~9/30 | PR milestone table + 10-Q MD&A | Company-stated, two independent places: "End Sep. 2026: Expected submission of Biologics License Application (BLA)" (PR) and "We expect to submit the BLA at the end of the third quarter of 2026" (10-Q MD&A). **HS indication.** | **CONFIRMED (issuer guidance)** |
| 4b | End-Nov event + the draft's "fake PDUFA" correction | PR milestone table | The company's own words: "**End Nov. 2026: Expected to receive Prescription Drug User Fee Act (PDUFA) date allocation and decision on Priority Review.**" The draft is **substantively right** that end-Nov is not a PDUFA *action* date — it is the filing-acceptance/date-allocation plus priority-review determination. But the draft's attribution is wrong: it blamed "a secondary summary," when the PDUFA wording comes from **the issuer's own primary milestone table**. Correct the attribution in the record. | **CONFIRMED substance / attribution REFUTED** |
| 4c | Priority-review *eligibility* | — | **No company statement of eligibility, no breakthrough/fast-track designation disclosed anywhere in the 10-Q or PR.** The company guides only to a "decision on Priority Review." Any assumption of a granted priority review is unsourced. | **UNVERIFIABLE** |
| 4d | Launch 2H27 | 10-Q MD&A | "subject to FDA approval, we expect a commercial launch in the United States in the second half of 2027." | **CONFIRMED (issuer guidance)** |
| 4e | *(new)* Catalysts both benches missed | PR + 10-Q | **P-OLARIS** (M1095-snSpA-202, PsA/axSpA) results **"end of 2026 or early 2027."** IZAR-2 completes enrollment Q3-2026. PPP Phase 3 **NOVA** enrollment starts H2-2026. Red's "nothing resolves before end-Nov" window is not as empty as ruled — but note none of these is a placebo-delta readout. | **CONFIRMED** |
| **5. COMPETITOR PASS** |
| 5a | Does a competitor dominate on the blessed endpoint? | CT.gov posted results NCT03895203 | **Yes — and it is already approved.** Bimekizumab (Bimzelx, UCB) BE OPTIMAL, same indication, same bio-naïve population, same ACR50 endpoint, same Week 16: **43.9% (n=431) vs placebo 10.0% (n=281)**, adalimumab reference 45.7%. **MoonLake's 42.1% is at or slightly below an approved incumbent on a like-for-like endpoint.** Red's PLAUSIBLE estimate of 43.9% is now CONFIRMED exactly. | **CONFIRMED — parity, not differentiation** |
| 5b | competitor_trial_omission — does it fire? | detector contract (KG dispatch_index) + PR | **NO-FIRE, and the no-fire is itself the finding.** The detector targets omission of competitor trials from a Competition section; this is an 8-K topline, not an S-1, and the CEO quote **volunteers the parity read**: "These data are also encouraging as they are **consistent with what was previously observed in other IL-17A/F programs.**" The company is not hiding the comparator — it is describing itself as class-consistent. Per the anti-masking doctrine, log it: absence of expected masking is a positive honesty observation. **But it also means the bull thesis's differentiation leg is contradicted by the issuer's own framing.** | **NOT-FIRED (honest) — but bearish for the thesis** |
| 5c | 12-month competitive readouts | CT.gov, industry-sponsored, Ph2/3, n≥100, PCD 2026-08-14→2027-08-14 | **HS:** AbbVie lutikizumab Ph3 *Intrepid* n=1,400 (Dec-2026) — most direct threat; Incyte ruxolitinib cream Ph3 ×2 (Oct-2026, topical/mild, different segment); Novartis Ph3 n=588 (May-2027) + RECHARGE-2 n=565 (Jun-2027); MSD tulisokibart Ph2 (Nov-2026); Zura tibulizumab Ph2 (Nov-2026); Sanofi brivekimig Ph2 (Aug-2027). **PsA:** J&J **ICONIC-PsA 2** icotrokinra (oral IL-23 peptide) n=750, PCD **2027-02-10** — reads out essentially alongside IZAR-1 and an oral would reprice the injectable-IL-17 slot; Takeda zasocitinib (oral TYK2) Ph3 ×2 (May-2027); Spyre SPY072 Ph2 (Oct-2026). | **CONFIRMED** |

---

## THE DECISIVE NEW FINDING — HERCULES TRANCHE 4 IS ARITHMETICALLY DEAD

Neither bench read the milestone architecture. It is the highest-value item in this pack.

**The covenant (10-Q Note 4, verbatim):** Tranche 4 ($50.0M) requires that "immediately prior to the advance of a fourth tranche, MoonLake has closed the previous **10 consecutive trading days with a market capitalization of at least $1,500.0 million**," available "through the earlier of (i) 60 days following the achievement of the Tranche 4 HS Milestone and (ii) December 15, 2026."

**The company's own MD&A confirms the deadline and the maintenance proviso:**
> "In June 2026, we achieved the Tranche 4 HS Milestone. For each trading day since July 3, 2026, we have closed the previous 10 consecutive trading days ... with a market capitalization of at least $1,500.0 million. Therefore, we have achieved the Amended Tranche 4 Milestone and a fourth tranche with additional term loans is available to us **until August 20, 2026** (provided that **we maintain** the Amended Tranche 4 Milestone market capitalization limit **for 10 consecutive trading days prior to funding**)."

**The test against the tape.** Threshold = $17.62/sh on 85.11M shares, $17.42/sh including the 1.0M pre-funded warrants. Last 10 sessions:

| Date | Close | Mkt cap (incl. PFW) | Test |
|---|---|---|---|
| 7/31 | 18.44 | $1,587.8M | PASS |
| 8/03 | 17.40 | $1,498.3M | **FAIL** |
| 8/04 | 17.93 | $1,543.9M | PASS |
| 8/05 | 17.55 | $1,511.2M | PASS |
| 8/06 | 18.03 | $1,552.5M | PASS |
| 8/07 | 18.26 | $1,572.3M | PASS |
| 8/10 | 17.33 | $1,492.2M | **FAIL** |
| 8/11 | 16.59 | $1,428.5M | **FAIL** |
| 8/12 | 17.23 | $1,483.6M | **FAIL** |
| 8/13 | 16.50 | $1,420.8M | **FAIL** |
| 8/14 | 16.54 | $1,424.2M | **FAIL** |

**Conclusion: the $50M Tranche 4 cannot be drawn.** Funding requires 10 *consecutive* qualifying closes immediately prior to the advance; 6 of the last 11 sessions fail, and only ~4 trading days remain before the 2026-08-20 outside date. It is not "at risk" — it is arithmetically impossible.

**The takeaway-vs-data divergence.** On 2026-08-10 MoonLake published, as a runway-reassurance bullet placed directly after the cash line: *"up to **$400 million in non-dilutive funds remain available** through its debt facility with Hercules Capital."* On that same day: the close was $17.33 ($1,492M — failing), the test had **already** been failing since 8/03, and the 10-Q filed **the same day** disclosed the 8/20 deadline and the maintenance proviso in precise terms.

Grading per the honesty boundary — **the datum is disclosed, and disclosed well**; the 10-Q is exact. This is not concealment. But the *marketed takeaway* ("$400M of non-dilutive funding stands behind the runway") diverges from the issuer's own arithmetic in the same-day filing. **Material divergence / REVIEW-FLAG, not fraud-grade ELEVATE.**

**What the $400M actually is, after 8/20:**

| Tranche | Size | Gate | Realistic availability |
|---|---|---|---|
| T3 | $50M | IZAR-1 **and** IZAR-2 both meet primary endpoint; outside date **2027-03-15** | IZAR-2 PCD 2027-01-15 — a ~2-month execution window, contingent on a trial still enrolling |
| T4 | $50M | $1.5B mkt cap × 10 consecutive days; outside date **2026-08-20** | **LOST** |
| T5 | $100M | FDA **approval** of the BLA; outside 2027-12-15 | Not before ~Mar–Jul 2027 PDUFA |
| T6 | $200M | "**Subject to approval by the Lenders in their discretion**" | **Not committed capital** |

**Committed, drawable non-dilutive capacity available to MoonLake today: $0.** Half of the advertised $400M is lender-discretionary; the rest is gated on events that have not happened.

**Why this matters to the ruling:** blue reduced red's shelf finding to "routine WKSI mechanics" and let "supply before launch stays near-certain" sit as a background fact. With the non-dilutive backstop now shown to be $0 committed — and the one near-term tranche expiring in six days — **equity supply is not merely near-certain, it is the only funded path**, against $213.8M of live ATM capacity plus a fresh S-3ASR, at a price 17% below where the June book cleared at $20.00. That is red's thesis, strengthened by a fact red never found.

*One honest caveat:* the Second Amendment (2026-08-03, 10-Q Item 5) did **not** modify the Tranche 4 gate — but it is plainly lease-driven housekeeping (LC basket $1.0M→$3.0M, landlord waiver $1.0M→$3.5M, tracking the new 11-year US office lease signed 7/1/26), and "did not modify the principal amount, interest rate, maturity date or financial covenants." Do not read it as a failed Tranche-4 negotiation.

---

## DO THE TWO GATES CLEAR?

**GATE 1 — Hercules facility balance: CLEARS, and it resolves against the position.**
Fully verified from Note 4, no proxy needed: $500M facility, **$100.0M drawn**, no warrants, no dilution, in covenant compliance, IP pledged first-priority. The unknown that made the court label EV an "upper bound" is closed — and closing it moves EV the *other* way, to **~$985M at the live $16.52**, ~15% above the courted $845M. The court's cheapness claim was inherited from an arithmetic error in the wrong direction. Layered on top: $0 committed non-dilutive capacity and a $50M tranche dying on 8/20.

**GATE 2 — The placebo-floor computation: CLEARS ON THE NARROW QUESTION, FAILS ON THE ONE THE THESIS NEEDS.**
The reopen-gate asked whether blue's bound is strong enough to underwrite a position or must be tagged PLAUSIBLE. Split the question:
- *Is the PsA ACR50 placebo floor real and tight?* **Yes — CONFIRMED** from posted registry results across 9 registrational trials: 7–15%, mean 10.9%, SD 2.6pp. Blue's PsA-≠-HS distinction is empirically correct and red's treating PsA like HS was a genuine error. Blue earned that overturn.
- *Does ~30pp follow?* **PLAUSIBLE-STRONG, not CONFIRMED.** It is a cross-trial inference against a different drug's population; the 42.1% is the **selected** arm of two; and the **imputation basis is undisclosed** by a company with a demonstrated habit of reporting as-observed.
- *Does it underwrite the position?* **No.** The bound establishes that **the drug works** — a VELA-2-style failure is off the table. It does **not** establish **differentiation**, which is what the thesis buys. At 42.1% vs bimekizumab's 43.9% in the same population on the same endpoint at the same week, sonelokimab is at parity-or-below versus an **already-approved** incumbent — and the CEO's own quote calls the data "consistent with what was previously observed in other IL-17A/F programs." **The issuer is describing parity.** Blue conceded "parity ≠ differentiation" and then sized as if the bound were bullish; it is efficacy-confirming and differentiation-neutral.

Plus a structural error the ruling embeds: **the placebo-floor bound is about PsA and the ~9/30 BLA is about HS.** Gate 2, however it resolves, does not de-risk either dated catalyst the ruling leaned on.

---

## DOES ANYTHING CHANGE THE HALF-STARTER RULING?

**Yes — SMALLER, and the entry logic inverts. Recommend: reduce to a quarter-starter, or stand down until after 2026-08-20 and the BLA submission.**

Nothing here is fraud. MoonLake's clinical disclosure is honest: endpoint hierarchy intact, NCT binding clean, selective-arm disclosure declared and attributed to an FDA-agreed protocol, VELA-2's miss described accurately with the p-value in its own PR, competitor parity volunteered in the CEO quote. **This is a clean issuer** — the honesty screen finds no liar. The problem is the *court's* arithmetic, not the company's.

What moved, and which way:

1. **EV is ~$985M, not $845M** (+~15%) — the "upper bound" label was backwards. The cheapness premise is weaker than adjudicated. *Smaller.*
2. **$0 committed non-dilutive capacity; $50M dies 8/20; $200M is lender-discretionary.** Equity supply is the only funded path, into a live $213.8M ATM and a fresh shelf, 17% below the $20.00 June clear. **This restores most of red's finding #3 that blue reduced.** *Smaller.*
3. **The 42.1% is parity with an approved incumbent, per the company's own framing.** Blue's bound proves efficacy, not the differentiation the thesis pays for. *Smaller.*
4. **Blue's placebo-floor logic survives independent verification** — genuinely 7–15%, SD 2.6pp. Red's PsA-as-HS error was real. Blue keeps the overturn. *Unchanged — the half-starter should not go to zero on differentiation fog alone.*
5. **The ~9/30 BLA and end-Nov acceptance are HS events; the verified bound is PsA.** The ruling's two dated buyer-favorable catalysts get no support from Gate 2. *Smaller.*
6. **New catalyst found:** P-OLARIS (PsA/axSpA) end-2026/early-2027, company-guided. *Marginally larger — a real event in the window red called empty.*
7. **The EDGAR 403 was self-inflicted.** Every "unverifiable" flag in the court record was a tooling failure, not a disclosure gap. Route court benches through `desk/sec_fetch.py`.

**Suggested gate edits (session applies — ledger/queue untouched per instruction):**
- **New tripwire, expires in 6 days:** `MLTX|2026-08-20` — Tranche 4 lapse. Confirm no 8-K reports a Tranche 4 draw. A draw would require 10 consecutive closes ≥$17.62 and is arithmetically foreclosed; treat any reported draw as a data error to re-verify.
- **Add to the 9/30 pack:** whether the ~$400M non-dilutive figure is restated to ~$350M once T4 lapses. Continued marketing of "$400M available" after 8/20 escalates this from review-flag to a genuine disclosure-integrity finding.
- **Add to the 11/30 pack:** priority-review *eligibility* has no company statement and no disclosed expedited designation — do not carry "priority review likely" into any write-up.
- **Correct in the record:** the end-Nov "PDUFA" wording originates in the issuer's own milestone table, not a secondary summary. The substance of the draft's correction stands; the attribution does not.
- **Correct in the record:** EV ≈ $985M at $16.52; $845M was a lower bound, not an upper bound.
- **Retire** every "EDGAR 403 / COVERAGE GAP" flag on this name.

**Bottom line:** Gate 1 clears and cuts against the position. Gate 2 clears on the narrow claim blue actually made, and does not reach the claim the thesis needs. The half-starter survives as a *smaller* position — the drug works and the issuer is honest — but it is a fair-value option on an HS approval, not a cheap option on a differentiated asset, and it is now demonstrably financed by equity.
