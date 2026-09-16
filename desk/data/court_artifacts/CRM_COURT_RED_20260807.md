# CRM (Salesforce) — RED BENCH, full adversarial court

**Posture: default-REJECT the LONG.** Run 2026-08-07, Fable tier. Live quote pulled this session
from IBKR before any valuation work: **$189.32** (bid 189.00 / ask 190.00, prior close 186.77,
+1.37% on the day, contract 29624264, `is_close:false`). 52w range $147.60–$268.33; YTD −28.35%;
annualized implied vol 53.5%; 90-day avg dollar volume $2.84B.

Cohort context: `agentic_saas_exposed`, triage 7/10 DAMAGE-ARRIVING
(`desk/data/court_artifacts/SAAS_STRAGGLERS_REFUTABILITY_20260807.md`). Standing house position:
`desk/data/edge_classifications/CRM.json` — STARTER-SMALL 5/10, OWNABLE, T1 53sh @ $175 staged,
T2 0.45% gated on a three-leg Q2 test.

Every number below is read from the SEC-filed primary document fetched this session. Two of the
existing court's load-bearing framings are **refuted** here and are marked as such. Where the red
case is weak I say so — three of my own lines were softened or conceded after checking the data.

---

## Mode B first — what the promoter framing hid

I derived the decisive question independently before reading the memo's framing. The memo's
question is *"is the organic deceleration masked by Informatica, and does the mask expire in
Feb-2027?"* That is the **wrong** question, and it is wrong in a way that flatters the long.

The right question is: **what is the smallest disclosure unit at which Salesforce still lets you
observe seat erosion?** The answer, as of the Q1 FY27 10-Q, is **two buckets covering a $42B
subscription base** — the coarsest product-level disclosure in the company's public history. And
the granularity was removed in the very next filing after the FY26 10-K showed two of five product
lines growing at 1.5–3.7%.

The Informatica mask is real, quantified by the company, and **expires on a known date**. The
disaggregation mask is **permanent** — reclassifications conform prior periods and do not reverse.
The existing court's central comfort ("rare case where a masking channel has a KNOWN EXPIRY") is
built on the *smaller* of the two masks.

---

## Claim table — {claim | source | result | verdict}

### A. The organic-vs-reported gap (Informatica contribution math)

| # | Claim | Source / method | Result | Verdict |
|---|---|---|---|---|
| A1 | Informatica contributed $428M to Q1 FY27 subscription & support and $444M to total revenue | [Q1 FY27 8-K EX-99.1](https://www.sec.gov/Archives/edgar/data/1108524/000110852426000125/crm-q1fy27xexhibit991.htm), Financial Highlights bullets | Company quantifies it in dollars, every quarter, for revenue | **VERIFIED — and this is honest disclosure. Credit it.** |
| A2 | Organic sub&support growth is ~7.4% cc in Q1 FY27 | $428M / $9,297M prior-year sub&support = **4.60pts**; reported 12% cc − 4.60 = **7.4% cc**. Prior-year base from [Q1 FY27 10-Q](https://www.sec.gov/Archives/edgar/data/1108524/000110852426000127/crm-20260430.htm) income statement | Confirms the triage's ~8% figure, slightly lower on the cc basis | **VERIFIED** |
| A3 | Organic is *decelerating* into Q1 FY27 | Q4 FY26 sub&support +11% cc incl. $388M Informatica (4.10pts) → **6.9% cc organic**; Q1 FY27 → **7.4% cc organic** | Organic sub&support cc **ACCELERATED 6.9% → 7.4%**, it did not decelerate | **REFUTED — my own red line, conceded.** The bear cannot claim the sub&support line is rolling over. It is roughly flat at ~7%. |
| A4 | Q2 FY27 is guided to a company-record-low ~5.9% organic | Q2 guide 10% cc incl. "slightly above 4pts" Informatica → **~5.9% cc organic total revenue**; vs Q1 total-revenue organic of 12% − 4.52pts = **7.5% cc** | A guided **160bp step-down**, on total revenue (prof. services $540M vs $532M, +1.5%, is a minor drag) | **VERIFIED** |
| A5 | The FY30 "$63B target raise" is ~100% acquired revenue | Q3 FY26 release said "$60 billion plus **organic**"; [Q4 FY26 EX-99.1](https://www.sec.gov/Archives/edgar/data/1108524/000110852426000056/crm-q4fy26xexhibit991.htm) Benioff: "well on our way to **$63 billion in revenue in FY30**" — organic qualifier gone. Independently: $46.05B FY27 compounding at the guided ~7.5% organic reaches **$57.2B** by FY30 — **$5.8B short** | Marketed takeaway ("we raised the target") diverges from the data (organic target unchanged, and unreachable at guided organic) | **CONFIRMED — ELEVATE** (carried forward from the standing court, re-derived here) |

### B. The H2 FY27 acceleration claim — testability and credibility

| # | Claim | Source / method | Result | Verdict |
|---|---|---|---|---|
| B1 | The CFO's H2-acceleration claim is a single dated Q1 statement | [Q1 FY27 EX-99.1](https://www.sec.gov/Archives/edgar/data/1108524/000110852426000125/crm-q1fy27xexhibit991.htm): Robin Washington, *"We remain confident in delivering organic revenue acceleration in the second half of FY27"* | **It was made TWICE.** [Q4 FY26 EX-99.1](https://www.sec.gov/Archives/edgar/data/1108524/000110852426000056/crm-q4fy26xexhibit991.htm) (2026-02-25), same officer: *"Our performance makes us even more confident in our path to **reaccelerate organic revenue growth in H2 FY27**."* | **VERIFIED and STRENGTHENED** — a twice-stated, two-quarter-old commitment in a furnished 8-K exhibit. Higher credibility cost if missed. |
| B2 | H2 needs ~190bp of reacceleration | Independent re-derivation on the cc-organic total-revenue basis: FY27 organic cc ≈ 10.5% − 3pts = **7.5%**; Q1 organic cc 7.5%, Q2 guided 5.9% → H1 ≈ 6.7%; H2 must be ≈ **8.3% cc** | Requires **+240bp off the Q2 guided exit rate** and +80bp above the Q1 level | **CONSISTENT, and harder than the memo states** |
| B3 | The claim is falsifiable | Structural test: the claim is stated in **organic** terms, but Salesforce controls what "organic" excludes. Fin/Intercom ($3.6B, announced 2026-06-15) lands in customer support → **Agentforce Service → the "Agentforce Apps" bucket** — in H2 FY27, exactly when the claim resolves. No 8-K filed (below the significance test, so absence is expected); no disclosed close date or revenue contribution | **The company has already demonstrated it will withdraw an acquisition deflator selectively (see C1).** If Fin's contribution is not quantified the way Informatica's is, "organic H2 acceleration" becomes **self-laundering and un-gradeable** | **UNVERIFIABLE — and UNVERIFIABLE IS NOT CLEAN.** This is the single biggest problem with the standing T2 gate. |
| B4 | Credibility if missed | The claim is not upside — it is a **load-bearing assumption inside the FY27 guide**. A ~6% H2 misses the FY27 revenue guide by ~$400–600M and makes the FY30 $63B arithmetically unreachable without further M&A | Missing it invalidates the guide, the FY30 target and the CFO's forward credibility simultaneously | **VERIFIED — asymmetric downside** |

### C. Disclosure integrity — the masking channels

| # | Claim | Source / method | Result | Verdict |
|---|---|---|---|---|
| C1 | The Informatica deflator was dropped from the cRPO bullet | Q4 FY26: *"cRPO of $35.1 billion, up 16% Y/Y and 13% in CC, **including 4pts Informatica contribution**."* Q1 FY27: *"cRPO of $33.6 billion, up 14% Y/Y and 13% in CC"* — **no Informatica**, while the revenue bullets in the *same release* still quantify it in dollars | Selective de-quantification on the single most important forward metric | **CONFIRMED — ELEVATE** |
| C2 | **THE STRONGEST KILL — product-level disaggregation collapsed 5 lines → 2, one named for the AI product** | [Q3 FY26 10-Q](https://www.sec.gov/Archives/edgar/data/1108524/000110852425000238/crm-20251031.htm) (filed 2025-12-04) and [FY26 10-K](https://www.sec.gov/Archives/edgar/data/1108524/000110852426000060/crm-20260131.htm) (filed 2026-03-02) both disclose **five** service offerings. [Q1 FY27 10-Q](https://www.sec.gov/Archives/edgar/data/1108524/000110852426000127/crm-20260430.htm) (filed 2026-05-28) discloses **two**: "Agentforce Apps $6,910M" and "Data 360, Headless Platform, and Other $3,683M" | See the destroyed-data table below. Two of the five retired lines were growing **1.5%** and **3.7%** in their final disclosed quarter | **CONFIRMED — ELEVATE** |
| C3 | The collapse was announced with an AI rationale | Q1 FY27 10-Q MD&A: *"**Agentforce Apps** groups our applications with Agentforce, **reflecting how Agentforce is embedded in every app**"* | The stated rationale is the marketing claim itself. The bucket is ~96% legacy seat licences (see D2) | **CONFIRMED — takeaway-vs-data divergence** |
| C4 | The renaming step was concealed | Q3 FY26 10-Q footnote (1): *"In the third quarter of fiscal 2026, the Company **renamed its service offerings to reference Agentforce**. **There were no changes in the allocation of revenue** between these service offerings coming from this change."* | **Explicitly and honestly footnoted.** Sales Cloud → "Agentforce Sales" with zero revenue reallocation, and they said so | **CLEAN — anti-masking positive. Credit it.** The masking is the *subsequent collapse*, not the rename. |
| C5 | NNAOV — a metric introduced on a good print, withdrawn on a weak one | Q4 FY26 CFO quote: *"a record Q4 … **fueling NNAOV acceleration in H2 FY26**."* Q1 FY27: "NNAOV" is **defined in the release glossary** (net new annual order value) but **given no value anywhere** — 0 occurrences in the 10-Q, absent from every bullet and quote | A metric marketed as accelerating one quarter, then silent the next while the definition stays on the page. Same shape as the cRPO deflator withdrawal | **CONFIRMED — ELEVATE. New finding, not in the standing court or the triage.** |
| C6 | The FCF guide cut is honestly attributed | Q1 FY27 release: FCF growth cut to ~4–5% "to reflect the impact of the **$25 billion debt issuance for the ASR**" | Explicit causal attribution to its own capital action | **CLEAN — anti-masking positive** |

**What the collapse destroyed** — reconstructed from the FY26 10-K annual figures minus the Q3 FY26
10-Q nine-month figures (both primary; Informatica's $388M FY26 sub&support contribution sits in
Platform/Slack/Other, consistent with that line's jump):

| Service offering (final disclosed basis) | FY25 gr | FY26 gr | Q3 FY26 | **Q4 FY26** | Q4 ex-Informatica | % of FY26 sub&support |
|---|---|---|---|---|---|---|
| Agentforce Sales | +9.8% | +8.5% | +8.4% | +9.3% | +9.3% | 22.9% |
| Agentforce Service | +9.8% | +8.4% | +9.0% | +8.8% | +8.8% | 24.9% |
| Agentforce 360 Platform, Slack & Other | +9.6% | +22.6% | +19.5% | +38.4% | +18.2% | 22.6% |
| **Agentforce Marketing & Commerce** | +7.5% | +2.8% | **+2.0%** | **+1.5%** | **+1.5%** | **13.8%** |
| **Agentforce Integration & Analytics** | +11.3% | +7.9% | +6.1% | **+3.7%** | **+3.7%** | **15.8%** |
| Total subscription & support | +9.7% | +10.4% | +9.5% | +13.0% | +8.8% | 100% |

**29.6% of the $39.4B subscription base was growing at 1.5–3.7% in the last quarter it was
visible** — and Marketing, Commerce, MuleSoft and Tableau are precisely the seat-and-license
products an agentic workforce displaces first. That line is now permanently invisible.

The standing court's edge explainer states: *"The confirmation isn't arriving."* **It arrived, in
two of five product lines, and was then removed from disclosure.** That is the refutation.

### D. Agentforce monetization — dated evidence vs marketing

| # | Claim | Source / method | Result | Verdict |
|---|---|---|---|---|
| D1 | Salesforce discloses Agentforce **consumption** revenue | Full-text scan of the Q1 FY27 EX-99.1 and 10-Q | **"consumption" appears ZERO times in the earnings release.** In the 10-Q it appears 13 times — every one a boilerplate risk factor ("customer usage of consumption-based offerings"). **"usage-based": 0 occurrences** in both the 10-Q and the FY26 10-K. **"Flex Credit": 2 occurrences** in the 10-Q, both inside the category-definition sentence; **0 occurrences in the FY26 10-K**. There is **no Flex Credits revenue-recognition policy and no consumption revenue disaggregation anywhere** | **REFUTED — no consumption revenue is disclosed, at all** |
| D2 | "$1.2B Agentforce ARR, up 205%" evidences AI monetization | Company definition, Q1 FY27 release: ARR is *"the annualized recurring value of active Data 360 and **certain** generative AI **subscription agreements**, including those for Agentforce and generative AI products **and features**"* | It is a **subscription** metric covering bundled **features**, with "certain" left undefined and no reconciliation to GAAP revenue. $1.2B ARR ≈ $300M/qtr = **4.3% of the $6,910M "Agentforce Apps" bucket** and **2.7% of total revenue**. The bucket named for the AI product is **~96% legacy seat licences** | **VERIFIED as a divergence — the label carries 23× the revenue the product does** |
| D3 | The AI usage metrics evidence monetization | "3.8B AWUs delivered to date, growing 111% Q/Q"; "28.6 trillion tokens to date, up 152% Q/Q" | Both are **cumulative-to-date stocks carrying flow growth rates** (2.4B→3.8B AWUs is +58% on the stock, not 111%; 19T→28.6T tokens is +51%, not 152%). Reconciles only under an unstated flow reading. **Neither has any revenue attached.** The token perimeter also moved: Q3 FY26 "**Agentforce** has processed 3.2T tokens through our LLM gateway" → Q4 FY26 "**Salesforce** has processed 19T tokens, up 5x Y/Y" — growth-rated across a definition change | **REVIEW — confusing-by-construction, not false. Activity without monetization.** |
| D4 | Agentforce pricing history (per-conversation → Flex Credits → bundled editions) | Attempted; **session web-search budget exhausted (200/200)** | Could not be verified from primary or secondary sources this session | **UNVERIFIABLE THIS SESSION — declared, not assumed clean.** Note the primary evidence in D1 points the same way: if a consumption product were material, a revenue-recognition policy would exist. |

### E. Seat-count trends in the core clouds

| # | Claim | Source / method | Result | Verdict |
|---|---|---|---|---|
| E1 | Seat counts are observable | Full scan of the 10-K and 10-Q | Salesforce discloses **no seat count, no customer count, and no net revenue retention** — and has now removed per-cloud revenue. The only remaining forward proxy is cRPO, which had its acquisition deflator withdrawn (C1) | **UNVERIFIABLE — and the set of available proxies is shrinking, not stable** |
| E2 | Best available seat proxy | Per-cloud growth in the final granular disclosure (table above) | Sales +9.3% and Service +8.8% in Q4 FY26 — the pure-seat core is **holding**, not breaking. Marketing/Commerce +1.5% and Integration/Analytics +3.7% are where erosion shows | **PARTIALLY REFUTES the aggressive bear.** The seat core is intact; the *adjacent* licence products are where damage is arriving. Honest read: erosion is real but localised to ~30% of the base. |
| E3 | Salesforce is deflecting its own seats | Q1 FY26 8-K (primary, carried forward): *"On help.salesforce.com, Agentforce has handled over 750,000 requests, **cutting case volume by 7% Y/Y**."* Q1 FY27 10-Q MD&A on S&M: expenses may fall as a % of revenue via "increasing our sales productivity, **which includes the use of AI and agents**" | The company demonstrates seat-displacing deflection **on itself** and books the savings in its own opex | **VERIFIED — price seat erosion as live** |

### F. Buyback vs SBC — net dilution and the EPS engine

| # | Claim | Source / method | Result | Verdict |
|---|---|---|---|---|
| F1 | Share count is genuinely shrinking | XBRL companyfacts CIK 0001108524: diluted WASO **970M (Q1 FY26) → 871M (Q1 FY27), −10.2%**. Shares outstanding **819M** as of 2026-05-21 (10-Q cover, primary) | Real and large. ASR final settlement (~26M more shares) still due Q3 FY27 | **VERIFIED — the strongest genuine pillar of the long** |
| F2 | SBC discipline is real | XBRL: SBC **$857M** in Q1 FY27 on $11,133M revenue = **7.70%**; FY26 $3,509M / $41,525M = **8.45%**; guided ~9% flat | ~**half** ServiceNow's 16.5%-and-rising. Net float shrink ≈ 8.8% gross repurchase capacity − ~2.5% SBC dilution ≈ **6%/yr** if 100% of FCF goes to buyback | **VERIFIED — genuinely disciplined. Credit it.** |
| F3 | The buyback is self-funding | XBRL: `PaymentsForRepurchaseOfCommonStock` Q1 FY27 = **$27,248M** vs FY26 full year $12,596M. 10-Q: **$25.0B March 2026 Notes** (maturities 2028–2066) + **$6.0B 2026 Term Loan** | The Q1 buyback was a **debt-funded leveraged recapitalisation**, not FCF. Noncurrent debt **$10,439M → $39,280M**; equity **$59,142M → $34,235M**; treasury stock **−$32,228M → −$55,028M** | **REFUTED — the float shrink is real but was bought, once, with the balance sheet** |
| F4 | The interest cost is fully in the run-rate | 10-Q income statement: interest expense **$317M** vs $68M prior year. But the $25B notes were issued mid-March — Q1 (Feb–Apr) captured only ~1.5 months | Full run-rate ≈ **$420M/qtr (~$1.7B/yr)**, i.e. **~$100M/qtr of interest drag not yet in the printed number** | **VERIFIED — an un-modelled headwind of roughly $0.30/sh annualised** |
| F5 | Guides were "RAISED" while the stock fell — the long's central pillar | FY27 revenue guide midpoint moved **$46.00B → $46.05B (+$50M)** on a **$78M Q1 beat** | The remaining nine months were **implicitly TRIMMED ~$28M**. The "raise" is arithmetic pass-through of a beat, not incremental confidence | **REFUTED as evidence of confidence** |
| F6 | GAAP EPS "+52% Y/Y" evidences earnings power | 10-Q income statement: net income $2,107M vs $1,541M (+$566M). **Gains on strategic investments swung +$558M vs −$63M = +$621M pretax**; at the 22.6% effective rate = **+$481M after tax = 85% of the entire net-income increase**. Ex-swing: net income +5.5%, EPS $1.87 vs $1.59 = **+17.5%**, of which most is the −10.2% share count | The **$7,772M** strategic-investment portfolio is largely privately held; the 10-Q states *"Valuations of privately held securities are inherently complex and require judgment due to the lack of readily available market data"* | **REVIEW, not ELEVATE** — non-GAAP correctly excludes it and it sits on the face of the income statement. But **operating earnings grew 5.5%, not 52%**, and the headline bullet is the one that travels. |

### G. Activist positioning

| # | Claim | Source / method | Result | Verdict |
|---|---|---|---|---|
| G1 | Starboard Value exited, removing the capital-allocation discipline check | 13F info tables, Starboard Value LP CIK 0001517137, CUSIP 79466L302. Position history: 2,008,076sh (Jun-23) → 940,325sh (Dec-25) → **absent (Mar-26)**. Exit filing verified complete, not truncated: `reportType 13F HOLDINGS REPORT`, `isAmendment false`, no confidential-omission flag, `tableEntryTotal 26` and exactly 26 positions parsed, CRM not among them. [infotable.xml](https://www.sec.gov/Archives/edgar/data/1517137/000092189526001402/infotable.xml) | **CONFIRMED from primary — with a timing correction.** The position was liquidated during **Q1 CY2026 (Jan–Mar)**, *disclosed* 2026-05-15. "Exited ~May 2026" is right about the disclosure, wrong about the trade | **VERIFIED (timing corrected)** |
| G2 | Starboard's exit is the mechanical explanation for the June-2026 distribution | Trade window Jan–Mar 2026 vs the 06-22 low; disclosure 2026-05-15 | The **selling happened three to five months before** the June slide. A 940k-share position (~0.11% of shares out) liquidated in Q1 cannot mechanically explain a 28.4% drawdown in June | **REFUTED as a cause — the standing court's cause-check leans on it too hard** |
| G3 | The discipline check has left | Same 13F cycle, all filed 2026-05-15 for 2026-03-31 holdings | **ValueAct Holdings LP (CIK 0001418814) HELD 2,994,509 shares / $558,984,995 — unchanged q/q**, after adding 96,000 in Q4-25. That is a position **3.2× the size of Starboard's at its exit** and it did not move. Elliott (CIK 0001791786) and Third Point (CIK 0001040273) absent in both periods | **PARTIALLY REFUTED.** One activist left; the larger one held its full position. "The governance check has left" overstates it | **PARTIALLY REFUTED — cuts against my own bear** |
| G4 | The activist-accommodation reading | Feb-2026: $50B authorization + dividend increase; May–Jun 2026: **$3.6B Fin/Intercom**, the 4th large deal in 14 months, announced mid-slide | Capital-return pivot is **NOT a pivot** — it is both, financed with $29B of new debt. The M&A treadmill now runs *alongside* the buyback on a levered balance sheet | **VERIFIED from the filings** |

**13F blind spots**, stated so the finding is not over-read: 13F captures long US equity only — no
shorts, swaps/TRS, or non-reportable option structures. "Absent" means no reportable long common
position, not no economic exposure; Elliott in particular is a heavy swap user, so its absence is
weak evidence. Q2 CY2026 13Fs (June-30 holdings) are **due 2026-08-14, seven days out** — all four
readings are 2026-03-31 holdings and are four months stale.

### H. Valuation at the live quote

At **$189.32** and 819M shares: market cap **$155.1B**, net debt ~$27.7B, **EV $182.8B**.

| Metric | Value |
|---|---|
| P/E on FY27 non-GAAP EPS guide (mid $14.09) | **13.4×** |
| P/E on FY27 GAAP EPS guide (mid $7.96) | 23.8× |
| EV / FY27 revenue ($46.05B) | 3.97× |
| FCF ($15.1B) yield on equity / on EV | 9.7% / 8.3% |
| Owner earnings (FCF − SBC $4.14B = $10.96B) yield on equity | 7.1% |

**The valuation kill.** The standing court types this as *"quality-at-own-history-discount"* and
anchors on the 20.0× → 13.2× YTD compression. **That is the anchoring error.** The 20× was paid for
a business the market believed grew low-double-digits; the multiple is being re-set to a **~6–7.5%
organic grower carrying $39.5B of gross debt, with 30% of its base compounding at 2–4%**. A
de-rating to a new growth regime is not a dislocation, and "cheap vs. its own history" is not an
argument when the history had a different growth rate.

The right comparison set is high-margin software franchises that crossed below ~8% organic growth —
they settle at **11–15×**, not 20×. At 13.4× CRM is **inside that band, not below it**:

| Multiple on $14.09 | Implied price | vs live $189.32 |
|---|---|---|
| 10× | $141 | −26% |
| 11× | $155 | −18% |
| **12×** | **$169** | **−11%** |
| **13.4× (live)** | **$189** | **0%** |
| 15× | $211 | +12% |
| 16× (court base $225) | $225 | +19% |
| 21× (court bull $300) | $296 | +56% |

The court's base case of $225 requires a re-rate to **16×** — which requires the H2 organic
reacceleration to be both **real and believed**, on a metric the company has stopped deflating
(C1) and inside a bucket structure that can no longer show where the growth came from (C2). The
bull case at $300 requires **21×**, i.e. a full round-trip to the growth multiple.

**Red-bench fair value: $169–$190 (12–13.5×).** The stock is trading at fair, not at a discount.

---

## Where the red case is WEAK — concessions

Default-REJECT does not mean pretend. Five things cut against me and a fair court must weight them:

1. **Organic sub&support cc did not decelerate** — 6.9% (Q4 FY26) → 7.4% (Q1 FY27). The
   "derailment" framing is not supported on the aggregate line. My A3 line is refuted by the data.
2. **The seat core is holding.** Sales +9.3% and Service +8.8% in Q4 FY26 — 47.8% of the base and
   the purest seat exposure — show no erosion. The damage is in the adjacent licence products.
3. **cRPO cc at 13% is a healthy bookings signal**, and organic cRPO ~9% cc runs *above* organic
   revenue ~7.5% — the correct sign for a backlog that is not eroding.
4. **The disclosure record is genuinely mixed, not fraudulent.** Informatica is quantified in
   dollars every quarter for revenue; the FCF cut is causally attributed to the ASR; the ASR average
   price is disclosed; the Q3 FY26 rename was footnoted with an explicit "no reallocation"
   statement; SBC is disciplined and honestly guided; prior periods were conformed on the
   reclassification. **This is promotional framing on a well-disclosed base — not a fraud tell.**
5. **The activist read is weaker than both the standing court and I assumed.** Starboard's exit is
   real but was a 940k-share position (0.11% of shares out) sold in Q1, and **ValueAct held
   2,994,509 shares / $559M unchanged** through the same window — 3.2× Starboard's exiting size. A
   large, long-tenured activist reviewing the same disclosure changes did not sell. That is a
   genuine datapoint against the masking thesis, and I record it as such.

Per house doctrine that is a **SIZE CUT and tighter tripwires, not an exclusion**. The reason it
still rejects the *edge* claim is C2 + H together: the marketed takeaway diverges from the segment
data **and** you are paying a fair multiple for the privilege of not being able to check.

---

## The mechanism (for the knowledge graph)

- **Masking channel — primary (new):** product-line disaggregation collapsed **5 → 2**, with the
  surviving seat bucket **named for the AI product** ("Agentforce Apps"), justified in MD&A by the
  marketing claim itself ("Agentforce is embedded in every app"). Retires the two lines that were
  growing 1.5% and 3.7%.
- **Masking channel — secondary:** acquisition-inclusive headline growth (Informatica ~4pts) with
  the deflator **disclosed for revenue but withdrawn for cRPO** in the same release.
- **Signal channel:** per-cloud growth, reconstructible **only for periods through Q4 FY26** by
  differencing the FY26 10-K against the Q3 FY26 10-Q. After that the signal does not exist at any
  granularity.
- **Signal-to-price latency — THE CORRECTION:** the standing court records "~6 months and DATED —
  the mask mechanically expires at the Q4 FY27 print (~Feb-2027)." That is true of the *Informatica*
  mask only. The **disaggregation mask has NO expiry** — reclassifications conform prior periods and
  do not reverse — and Fin/Intercom lands in the same bucket in H2 FY27, replacing the expiring
  inorganic contribution with a new unquantified one. **Net: the mask does not expire; it rotates.**
- **Generalizable lesson:** when a company retires product-level disaggregation and names the
  surviving bucket after its newest product, difference the last annual filing against the last
  interim filing *before the change* — that reconstructs the final visible period and usually
  explains the timing. And check whether a *new* acquisition lands in the same bucket as the one
  that is about to anniversary: a mask with a known expiry can be rolled forward.

---

## STRONGEST KILL

**Salesforce collapsed its product revenue disclosure from five lines to two in the first filing
after the FY26 10-K revealed that two of those five lines had stopped growing — and named the
surviving seat bucket after the AI product it is marketing.**

The dated sequence, every step from a primary SEC filing:

1. **2025-12-04** (Q3 FY26 10-Q) — five service offerings, all renamed to carry the "Agentforce"
   prefix, with an honest footnote that no revenue was reallocated. Marketing & Commerce: **+2.0%**.
2. **2026-03-02** (FY26 10-K) — five offerings retained. Marketing & Commerce **+2.8% FY26**, and
   **+1.5%** in the derived Q4; Integration & Analytics **+3.7%** in Q4. Together **29.6% of the
   $39.4B subscription base growing at 1.5–3.7%**.
3. **2026-05-28** (Q1 FY27 10-Q) — five collapse to two. The seat clouds plus Slack become
   **"Agentforce Apps," $6,910M/quarter**, justified as *"reflecting how Agentforce is embedded in
   every app."* Agentforce's own ARR is **$1.2B (~$300M/quarter) — 4.3% of that bucket.**
4. **Same release** — the Informatica deflator is dropped from the cRPO bullet while remaining on
   the revenue bullets; **NNAOV**, marketed as "accelerating" one quarter earlier, keeps its glossary
   definition but is given **no value**.

The honesty lens returns a clear answer: **the marketed AI-transformation takeaway diverges from the
segment numbers.** A $6.9B/quarter bucket carrying the Agentforce name is ~96% legacy seat licences;
the AI product inside it is 4.3%; **no consumption revenue is disclosed anywhere** ("usage-based": 0
occurrences; no Flex Credits revenue-recognition policy); and the disclosure that would have let an
analyst locate the erosion was retired at the moment it began to show it.

This is not a fraud finding. It is a **takeaway-vs-data divergence with a permanent masking channel**,
priced at a **fair** multiple — which is exactly the configuration in which a long has no edge.

---

## WHAT WOULD CHANGE MY MIND

Ranked; the first two are decisive on their own.

1. **Disaggregation restored at Q2 FY27** — Salesforce reinstates per-cloud revenue, or discloses
   Agentforce revenue (not ARR) as its own line. This reverses the strongest kill outright and I
   would move to the long side of the standing court's 5/10.
2. **The cRPO Informatica deflator is restored at Q2** and organic cRPO prints **≥9% cc**. The
   deflator's return is the single cleanest honesty tell available, because its withdrawal was
   discretionary and one-directional.
3. **Fin/Intercom's contribution is quantified separately when it lands**, preserving the
   falsifiability of the "organic" claim through H2 FY27. Without this, B3 stands and the T2 gate
   cannot be graded.
4. **Marketing & Commerce / Integration & Analytics shown — in any venue — to have inflected above
   ~6%.** That would convert the 29.6% drag into a recovering cohort and make the H2 arithmetic
   reachable without heroics.
5. **Price does the work: ≤11× ($155) or below.** At an 11%+ FCF yield the terminal question stops
   binding and the name becomes ownable as fairly-paid risk regardless of the disclosure finding.
   The valuation kill in section H is a *price* objection, and price objections are cured by price.
6. **Q2 organic cc ≥8% on total revenue** — i.e. the reacceleration starts a quarter early rather
   than being promised for H2. That would make the twice-stated CFO claim look conservative instead
   of load-bearing.

Conversely, these would deepen the kill: NNAOV promoted into a headline metric replacing cRPO; a
fifth acquisition >$2B; the "H2 organic reacceleration" sentence quietly softened or dropped at Q2
(the standing court already grades this as a MISS); or Fin folded into "Agentforce Apps" with no
separate quantification.

---

## CONVICTION

**7/10 on the kill.**

Strong on the two axes that actually move the sizing decision — **disclosure integrity** (C2, C5,
C1 are three independent, dated, primary-sourced masking events inside two quarters) and
**valuation anchoring** (13.4× is fair, not cheap, for a ~7% organic grower with 30% of its base at
2–4%). Both survive every concession above: the disaggregation collapse is a filed fact, and the
multiple arithmetic does not depend on any judgement about management.

Held back from 8+ because three of my own lines were refuted by the data I went to check them with:
the aggregate organic line is **stable at ~7%, not deteriorating** (A3); the pure-seat core is
holding at ~9% (E2); and the activist-flight framing is overstated with **ValueAct holding $559M
unchanged** (G3). The disclosure base is genuinely mixed rather than deceptive. This is a
**fair-value name with a degrading information environment**, not a broken one — which is a reason
to decline the *edge* claim, not to exclude the name.

## RECOMMEND

**REJECT the long as an EDGE claim. Reclassify RP_FAIR (fairly-paid risk, edge overlay = zero).**

1. **Cancel T2 (0.45%).** Its three-leg gate is **no longer gradeable**: leg 1 (organic cRPO cc) rests
   on a deflator the company withdrew; leg 3 (H2 reaffirmation) will be confounded by Fin/Intercom
   landing in the same bucket. A gate you cannot score is not a gate. Per doctrine, metric
   non-restoration at Q2 already triggers automatic REVIEW — I am pulling that forward to a cancel.
2. **T1: hold the staged 53sh @ $175 as a resting limit, do not lift toward the $189.32 market.**
   The band sits at 12.4× — inside my $169–190 fair range and below the live quote, so it is a
   price-disciplined entry rather than an edge expression. **Response taxonomy: this is a valuation
   finding, and valuation findings gate on price** — which the existing $175 band already does. The
   *business-risk* finding (C2) additionally warrants the **size cut**, which cancelling T2 delivers
   (0.75% → 0.30%; enterprise-software axis 2.93% → ~2.48%).
3. **Add two disclosure tripwires** to the standing kill list, both scored at the Q2 FY27 print:
   *(a)* per-cloud disaggregation not restored **and** no separate Agentforce revenue line → hold at
   T1, no adds at any price above $169; *(b)* NNAOV promoted into a headline metric while cRPO is
   de-emphasised → full exit (that is the substitution completing).
4. **Q2 FY27 print date — NOW VERIFIED, and it resolves the standing court's top unverifiable.**
   **Wednesday 2026-08-26, 2:00pm PT**, company-confirmed from the Salesforce IR events feed
   (`investor.salesforce.com/feed/Event.svc/GetEventList`, EventId 1206, "Salesforce, Inc. Q2 FY27
   Earnings Webcast", StartDate 08/26/2026 14:00 PT). The feed was **calibrated against EDGAR before
   being trusted**: its past-event dates match the item-2.02 8-K filing dates exactly for Q2 FY26
   (2025-09-03), Q3 FY26 (2025-12-03), Q4 FY26 (2026-02-25) and Q1 FY27 (2026-05-27). No
   date-announcement 8-K exists, so the IR calendar is the sole authoritative source.
   **This breaks the historical cadence** — it is ~a week *earlier* than the naive extrapolation from
   2025-09-03 that produced the "Sept 2–3" estimate, which is almost certainly the prior run's error
   mode. **Consequence: the print is 19 days out, not 26.** The $175 T1 band sits inside a
   pre-print window that is materially shorter than assumed; it clears the house 2-week
   no-blind-entry rule, but only by five days. If it has not filled by **2026-08-19**, pull it and
   re-set after the print.
5. **Do not add on the axis.** CRM is the 4th position on an "agents eat seats" axis where the house
   already owns the two highest-edge names (HUBS 45pp, MNDY 28pp). With the edge overlay now graded
   to zero, the correlation is the only thing this adds.

---

### Closing verification note

- **Both delegated verifications returned and both changed the record.** The Q2 FY27 print date is
  **company-confirmed 2026-08-26** (a week earlier than the pattern-based estimate, closing the
  standing court's top unverifiable and shortening the pre-print window to 19 days). The Starboard
  exit is **confirmed from primary 13Fs** but mis-timed in the standing court — the trade was Q1
  CY2026, not May — and **ValueAct held 2,994,509 shares unchanged**, which partially refutes the
  "discipline check has left" framing that the standing court uses to justify a size cut.
- **A parser lesson worth carrying into the codebase.** The first 13F parse returned "no CRM" for
  *every* Starboard period, including ones where they demonstrably held it. Cause: 13F info tables
  use a **default XML namespace**, so `ElementTree` yields `{uri}nameOfIssuer` and every
  `findtext('nameOfIssuer')` silently returned empty — a false negative **indistinguishable from a
  real exit**. It was caught only because a raw CUSIP grep contradicted the parsed result. **Any 13F
  parser in this repo must be validated against a known-positive before its negatives are trusted.**
  Working approach: regex-extract `<infoTable>` blocks after stripping element prefixes
  (`/private/tmp/claude-501/-Users-ajay-exalted-signalos/19e93dcd-f148-4785-93b6-9c5d766d691a/scratchpad/p13f3.py`).
- **Session web-search budget was exhausted (200/200)** before the Agentforce pricing history (D4)
  could be sourced. It is declared UNVERIFIABLE rather than assumed clean. Every other finding in
  this document is sourced to an SEC-filed primary document fetched this session, and the live quote
  was pulled from IBKR before any valuation work.
- Prices, filings and XBRL all read 2026-08-07.
