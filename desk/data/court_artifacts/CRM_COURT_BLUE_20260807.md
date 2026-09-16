# CRM (Salesforce) — BLUE BENCH, adjudication of the RED filing

**Posture: defend the long, concede where the red is right.** Run 2026-08-07, Fable tier.
Live quote pulled from IBKR this session before any valuation work: **$190.00 last**
(bid 189.00 / ask 190.94, prior close 186.77, +1.73% on the day, contract 29624264,
`is_close:false`). 52w $147.60–$268.33; YTD −28.09%; annualized IV 53.1%; daily IV 3.343%;
90-day ADV $2.85B.

Adjudicating: `desk/data/court_artifacts/CRM_COURT_RED_20260807.md` (7/10 kill, REJECT edge,
reclassify RP_FAIR, FV $169–190) against the standing file `desk/data/edge_classifications/CRM.json`.

Every counter below is bound to a primary SEC document fetched this session. Where the red is
right I say so and uphold it — **five red findings are UPHELD and two new red-favorable facts
that the red bench itself missed are entered into the record against my own side.**

---

## 0. THRESHOLD CORRECTION — the position does not exist

The brief commissioning this bench states *"the desk already HOLDS CRM at 2.9%."* **It does not.**

`get_account_positions` (this session, IBKR): **no CRM line item.** The only CRM object in the
account is a resting `BUY 53 CRM @ $175.00 GTC`, order_id **1353528703**, status **REPLACED**.

| Item | Claimed | Actual (IBKR, this session) |
|---|---|---|
| CRM position | 2.9% held | **zero shares** |
| CRM orders | T1 staged + T2 gated | one resting bid, 53sh @ $175 (**status REPLACED**, not NEW) |
| Held software axis | — | HUBS $27,202 + DFIN $35,801 + SAP $12,930 + MNDY $12,600 + CTSH $10,240 + G $7,232 + NOW $5,657 = **$111,662 = 10.86% of NAV $1,028,344** |
| Sizing denominator | 0.30% ≈ $10k | 53 × $175 = $9,275; $9,275 / 0.0030 ⇒ implied book **≈ $3.1M**, i.e. ~3× current IBKR NAV |

Three consequences, all of which bind the ruling:

1. **The red's principal risk remedy is void.** Red delivers its size cut by "cancelling T2
   (0.75% → 0.30%)." There is no 0.75%. Cancelling an ungated future tranche reduces no
   exposure; it only removes an option. A business-risk finding calls for a **size** response
   under house doctrine, but there is no size to respond with.
2. **The sizing percentages in the standing file are struck against a deploying book ~3× the
   current IBKR NAV** (consistent with the Sept external capital). Any axis-cap claim
   ("2.93% ≤ 3.0%") is denominator-dependent and should be restated. On *current* NAV the held
   software axis is already **10.9%** without CRM.
3. **Operational flag:** the resting bid's status is `REPLACED`, a terminal status for that
   order_id, and no successor CRM order appears in the live order list. Before any decision is
   taken about "pulling" the bid, **verify a working bid exists at all.** This is a live-axis
   integrity check, not a rhetorical point.

House doctrine on this is explicit and was flagged again here: *plans and resting orders are not
holdings; poll positions before any sleeve/held/trim claim.*

---

## Mode B first — the question both benches skipped

Red's Mode B asks: *"what is the smallest disclosure unit at which Salesforce still lets you
observe seat erosion?"* Good question, wrong answer. Red answers "two buckets" and stops.

The question I derived independently is: **where did the two decaying product lines actually
GO, and does the surviving structure still expose them?** That is answerable from the filing,
red did not attempt it, and the answer inverts red's strongest kill. It is section 1 below.

---

## PER-KILL ADJUDICATION

### KILL 1 — "Disaggregation collapsed 5→2, the weak lines are now permanently invisible" (red C2/C3, ELEVATE, "STRONGEST KILL")

**Red's claim.** Five service offerings became two in the first filing after the FY26 10-K showed
two lines growing 1.5% and 3.7%; the surviving bucket is named after the AI product; *"that line
is now permanently invisible"*; *"the signal does not exist at any granularity."*

**Method.** Fetched the Q1 FY27 10-Q disaggregation note directly
([crm-20260430.htm](https://www.sec.gov/Archives/edgar/data/1108524/000110852426000127/crm-20260430.htm))
and reconciled the two new buckets to the five retired lines by weight.

**Finding — the two weak lines were SPLIT ACROSS BOTH new buckets, and both remain observable.**

Filed figures, Note 2 "Revenues," with the prior period recast:

| Service offering | Q1 FY27 | Q1 FY26 (recast) | Growth |
|---|---|---|---|
| Agentforce Apps | $6,910M | $6,345M | **+8.90%** |
| Data 360, Headless Platform, and Other | $3,683M | $2,952M | **+24.76%** |
| — same, less $428M Informatica | $3,255M | $2,952M | **+10.26% organic** |
| Total subscription & support | $10,593M | $9,297M | +13.94% |

Bucket weights on the recast prior period: **68.25% / 31.75%.** Now reconcile against red's own
FY26 five-line weights (Sales 22.9, Service 24.9, Platform/Slack/Other 22.6, Marketing & Commerce
13.8, Integration & Analytics 15.8):

- Sales 22.9 + Service 24.9 + **Marketing & Commerce 13.8** = 61.6; + Slack ≈ 6.65 = **68.25** ✓
- **Integration & Analytics 15.8** + (Platform/Data/Other 22.6 − 6.65 = 15.95) = **31.75** ✓

**Stated honestly: Slack's share is a solved free parameter, so the 0.00pp closure is partly by
construction.** The test that makes the mapping load-bearing is whether the solved value is
*plausible*, and whether rival mappings survive:

| Candidate mapping | Implied Slack share of sub&support | Verdict |
|---|---|---|
| Sales + Service + **M&C** + Slack | 6.65% = **$2.62B/yr** — Slack was ~$1.5B at the 2021 acquisition; ~12%/yr compounding lands at ~$2.6B | **plausible — accepted** |
| Sales + Service + Slack (M&C moved to the other bucket) | 20.45% = **$8.06B/yr**, ~3× any credible Slack | rejected |
| Sales + Service + all of Platform/Slack/Other | fixed at 70.4% vs actual 68.25% — **misses by 2.15pp with no free parameter** | rejected |

Only one mapping survives, and it identifies:

> **Agentforce Apps** = Sales + Service + **Marketing & Commerce** + Slack
> **Data 360, Headless Platform, and Other** = **MuleSoft + Tableau** + Data Cloud/Platform/Other

This destroys the kill's mechanism. Red's thesis requires the weak cohort to be *buried inside the
bucket named after the AI product*. Instead the weaker of the two (**Integration & Analytics,
15.8% of the base at +3.7%**) sits in the bucket that is **not** named after the AI product — and
that bucket grew **+10.26% organically**, i.e. *faster than the company average*. Backing out the
retired lines at their last disclosed rates, the residual Data Cloud/Platform component implies
**~16.8%** growth and Slack inside Agentforce Apps implies **~23.3%** — both consistent with the
CFO's named H2 drivers.

And the signal survives prospectively: because a weak component sits in **each** bucket, further
deterioration in either Marketing/Commerce or MuleSoft/Tableau now shows up as a decline in a
**disclosed, recast, quarterly** growth rate. Red's *"the signal does not exist at any
granularity"* is refuted by the filing's own table.

**Was the change previewed / has a regulator ever objected?**

- Prior periods were **recast and honestly footnoted**: *"Reclassifications to the prior period
  were made to conform to the current period presentation in the Disaggregation of Revenue in
  Note 2 'Revenues' beginning in the first quarter of fiscal 2027. This reclassification did not
  affect total subscription and support revenue."* Growth rates therefore remain computable — the
  opposite of a mask, which works by destroying comparability.
- **SEC comment letters — the full EDGAR history checked.** CIK 0001108524 has exactly three
  staff exchanges on record: **2019** (non-GAAP amortization of purchased intangibles — staff
  *"determined not to pursue this comment"*,
  [CORRESP](https://www.sec.gov/Archives/edgar/data/1108524/000119312519190929/filename1.htm));
  **2021** (a Form S-4 acceleration request, not a comment,
  [CORRESP](https://www.sec.gov/Archives/edgar/data/1108524/000119312521018058/filename1.htm));
  **2022** (a boilerplate proxy Item 407(h) board-leadership sweep the company notes the staff was
  *"issuing similar comments to a number of companies"*,
  [CORRESP](https://www.sec.gov/Archives/edgar/data/1108524/000110852422000044/filename1.htm)).
  **Zero comments, ever, on revenue disaggregation or segment granularity.** The collapse
  post-dates all of them, so this is not exculpatory — but it removes any basis for treating the
  presentation as a known regulatory abnormality, and it dates the real test: the Q2 FY27 10-Q
  review cycle.
- The change was **not** previewed in the Q4 FY26 release or the FY26 10-K. **Red is right about
  that and I concede it.**

**Is the hidden 29.6% at 1.5–3.7% worse than what the market already models?** No — and this is
the arithmetic that matters. Weighting red's own final-visible-quarter table:

- the decaying 29.6% contributes **29.6% × ~2.5% = 0.74pts** of drag-adjusted growth;
- the accelerating Platform/Slack/Data cohort contributes **22.6% × ~17.3% = 3.91pts**.

The accelerating bucket adds **5.3× more growth than the decaying one costs.** Red computed one
side of its own table and not the other. (The 17.3% is FY26 Platform/Slack/Other growth of +22.6%
adjusted for the $388M of Informatica in that line — and note Q3 FY26 carried **zero** Informatica
yet that line still grew +19.5%, so the acceleration there is overwhelmingly **organic**, not
acquired. Red's footnote attributing the jump to Informatica is wrong.)

**VERDICT: KILL 1 SUBSTANTIALLY WEAKENED — downgrade from ELEVATE to REVIEW.** The timing is
genuinely adverse and granularity genuinely fell; that keeps it on the board. But the asserted
*effect* — permanent invisibility of the decaying cohort — is refuted by the filed table.

---

### KILL 2 — "13.4× is fair, not cheap; peers settle at 11–15×" (red H, the valuation kill)

**Red's method is a comp-multiple assertion, not a valuation.** It asks what multiple similar
businesses trade at. It never asks what growth rate the current price actually embeds. When you
ask that question, the kill inverts.

**Reverse-DCF at the live quote**, built from audited XBRL
([companyfacts CIK 0001108524](https://data.sec.gov/api/xbrl/companyconcept/CIK0001108524/us-gaap/NetCashProvidedByUsedInOperatingActivities.json)):

- FY26 OCF **$14,996M**, capex **$594M** → FY26 FCF **$14,402M** (ties to the company's stated
  "$14.4 billion, up 16%").
- FY27 FCF guide +4–5% → **$15,050M** (this guide *already absorbs* the ASR interest — the
  company attributes the cut explicitly to *"the impact of the $25 billion debt issuance for the
  ASR"*).
- FY27 SBC ≈ 9% × $46,050M = **$4,145M**.
- **Owner earnings = $15,050 − $4,145 = $10,905M.**
- Shares 819M (10-Q cover, 2026-05-21) at $190.00 → market cap **$155.6B**.
- **Owner-earnings yield = 7.01%.**

Implied perpetual **nominal** growth: at CoE 8.5% → **1.49%**; at 9.0% → **1.99%**; at 10.0% →
**2.99%**. Call it **~2% nominal, i.e. roughly zero real growth in perpetuity.**

Now price red's own destroyed-data table forward:

| Scenario (weights and rates from red's own table) | Blended growth |
|---|---|
| **A** — weak 29.6% grows **0% forever**; strong 70.4% decays 11.4% → 7% | **+4.93%** |
| **B** — weak 29.6% **declines 5%/yr**; strong decays to 6% | **+2.74%** |
| **C** — true seat erosion: weak **−8%/yr**; strong decays to 3% | **−0.26%** |
| **Market at $190 implies** | **≈ +2.0%** |

**$190 already prices an outcome between B and C** — worse than "the invisible 29.6% never grows
again and the core decays to 6%." Haircut owner earnings by ~8% for decaying deferred-revenue
float and the implied growth still only reaches ~2.6%, below Scenario B.

Red's own sentence — *"the multiple is being re-set to a ~6–7.5% organic grower"* — is exactly the
error. **The price is not set to a 6–7.5% grower. It is set to a ~2% grower.** The gap between
red's own bear reconstruction (2.7–4.9%) and the embedded ~2.0% is the edge red declined to compute.

**VERDICT: KILL 2 REFUTED ON METHOD.** A comp-multiple band is not a fair value. Red's FV ceiling
of $190 is also now **at the market** ($190.00 live), so on red's own numbers the stock is not
even fair — it is at the top of a band derived by a method that ignores the cash flows.

#### …but the base rate attacks my refutation, and it lands

A base-rate pull on mature-software names entering ≤14× forward non-GAAP with flat/negative
revenue returns a **poor** record over the following 2–3 years:

| Outcome | Names |
|---|---|
| **Clear floor (1)** | IBM Dec-2021 @ 12.81× → **+41.1pp vs SPY / 3yr** — and it required a real growth **inflection** |
| **Wash (1)** | ORCL Dec-2018 @ 11.0–11.7× → +3.1pp / 3yr; the famous breakout came **4.5 years** after the trough and has round-tripped in 2026 |
| **Traps (4)** | ORCL Jan-2016 (re-rate delayed 7.4yr); IBM 2015 (−91.9pp/5yr); IBM Dec-2019 @ 10.0× (−13.7pp/3yr); **CTSH Dec-2022 @ 12.60× (−33.2pp/3yr *despite* the multiple re-rating to 15–17×)**; TDC Dec-2024 (−45.5pp, ongoing) |
| **Open (1)** | **ADBE Nov-2025 @ 13.7×** — the "floor" gave zero support, sliced to **7.8×** in two months |
| **Acquired (3)** | CTXS, MCRO.L (98% premium to an already-collapsed price = a value-destruction exit), VMW |

**CTSH is the finding that matters, and it is aimed squarely at my reverse-DCF.** Its multiple
re-rated *up* 12.6× → 15–17× and holders still lost 33pp — because **E fell faster than the
multiple rose.** My refutation of red rests on a 7.01% owner-earnings yield. That yield is only an
edge if **E is durable**. A reverse-DCF cannot distinguish "cheap" from "about to be less
profitable"; it silently assumes the denominator holds. **I concede this is the strongest
available attack on my own section 2, and the base rate does not support the naive
"12–13.5× is already the bear multiple" claim as a standalone.**

Note also **ADBE is the closest live comp** — an incumbent with an AI-terminal-value debate — and
the desk already has staged ADBE bids at **$238 and $195** plus held HUBS/MNDY/NOW/SAP. Adding CRM
**stacks the same factor**, it does not diversify it. Red's "do not add on the axis" (point 5) is
better-founded than I initially credited.

**So the decisive question is not the multiple — it is whether E erodes.** That is testable, and
the single cleanest discriminator between CRM and the trap cohort is **backlog growing faster than
revenue**:

- Q4 FY26: cRPO **13% cc including a disclosed 4pts Informatica** → **organic cRPO ≈ 9%** vs
  organic revenue 6.0% cc → backlog leading by ~300bp.
- Q1 FY27: cRPO **13% cc** — **the Informatica deflator was withdrawn (red's C1)**, so organic
  cRPO can no longer be computed. Bounded by inference: for organic cRPO to fall *below* organic
  revenue (7.5%), Informatica's cRPO contribution would have to exceed **5.5pts**, versus 4.0pts
  disclosed one quarter earlier and 4.5pts on revenue now. Unlikely — but **now an inference, not
  a disclosure.**

The trap cohort's defining feature is a **shrinking or flat** forward book. CRM's is growing ~9%
organically and ahead of revenue. That is a real discriminator — **and red's C1 is precisely what
blinds it.**

**Consequence: I UPGRADE red's C1.** It is not merely an honesty tell. **The withdrawn cRPO
deflator is the removal of the one number that separates CRM from the CTSH/IBM/TDC base rate.**
That is a more serious finding than red itself argued, and it is the single most important thing
to watch at the Q2 print.

---

### KILL 3 — Agentforce/Data Cloud option value (the red band assigns it zero)

Red cites *"$1.2B Agentforce ARR"* and computes it as 4.3% of the Agentforce Apps bucket. The
arithmetic is right; the selection is not. From the primary releases:

| Metric | Q3 FY26 (2025-12-03) | Q4 FY26 (2026-02-25) | Q1 FY27 (2026-05-27) |
|---|---|---|---|
| Agentforce + Data 360 ARR | ~$1.4B, +114% Y/Y | — | **~$3.4B, +200%+ Y/Y** |
| of which Informatica Cloud ARR | — | — | $1.1B |
| **Agentforce ARR alone** | — | **$800M, +169%** | **$1,200M, +205%** |
| Paid Agentforce deals | **>9,500** | ~closed (truncated) | — |
| Premium SKU bookings (Agentforce One + **Agentforce for Apps**) | — | — | **+~60% Y/Y** |
| Public Sector Industry Cloud ARR | — | — | **$2.0B, +23% Y/Y** |

Three things red omitted:

1. **Agentforce ARR went $800M → $1,200M in ONE quarter — +50% Q/Q, ~$400M of net-new ARR.** At
   that run-rate the franchise adds ~$1.6B/yr, ≈3.5pts of revenue growth on a $46B base. Red
   reported the level and not the slope.
2. **Organic AI+data ARR is $2.3B** ($3.4B less $1.1B acquired Informatica), up from ~$1.4B two
   quarters earlier. Red's "$1.2B" understates the franchise by ~2×.
3. **"Agentforce for Apps" is a literal revenue-bearing SKU** with a disclosed bookings growth
   rate of ~60%. Red's C3 — *"the stated rationale is the marketing claim itself"* — is weakened:
   the bucket is named after a product family that exists and whose bookings are disclosed.

**Is it valued at zero in red's band?** Yes, by construction. A 12–13.5× multiple on FY27 EPS
capitalizes current earnings and assigns nothing to a $2.3B organic ARR base compounding >100%.
Even at a **distressed 5× ARR** that franchise is $11.5B ≈ **$14/share**; at 8× it is ~$22/share.
Red's entire FV band is **$21 wide ($169–190)**. The omitted option is the width of the band.

Honest haircut: ARR includes bundled "features," "certain" is undefined, and there is no
reconciliation to GAAP revenue — red's D2 is a fair criticism and I do not dismiss it. Haircut to
the organic, incremental portion and you still get **$9–14/share of value red carries at zero.**

**VERDICT: KILL 3 — the red band is INCOMPLETE. Upheld against red.**

---

### KILL 4 — the twice-made H2 organic-acceleration claim (red B1–B4)

Red: H2 needs **+240bp** off the Q2 exit and +80bp above Q1 — *"harder than the memo states"* —
and B3 declares the claim **un-gradeable** because Fin/Intercom lands in the same bucket, so
*"the mask does not expire; it rotates."*

**Finding 4a — the Informatica lap is a Q4 FY27 event, and red demoted the standing court's
correct call.** From the Q4 FY26 release: *"FY26 revenue of $41.5 billion... **including $399
million Informatica contribution**"* and *"Fourth quarter revenue of $11.2 billion... **including
$399 million Informatica contribution**."* **Identical figures — therefore Informatica contributed
ZERO in Q1–Q3 FY26** and closed at the start of Q4 FY26. Confirmed against the Q3 FY26 release,
whose FY26 guide carried only *"approximately 80bps Informatica contribution"* for the full year
and whose Q3 bullets carry no Informatica line at all.

Contribution path, which ties to the guide:

| Quarter | Informatica pts | Basis |
|---|---|---|
| Q1 FY27 | **4.52** | $444M / $9,829M prior-year revenue |
| Q2 FY27 | **~4.2** | guided "slightly above 4pts" |
| Q3 FY27 | **~4.0** | full quarter vs a **zero** base |
| Q4 FY27 | **~0** | laps |
| FY27 avg | **~3.2** | ✓ ties to guided "approximately 3pts" |

**The unmasked print is Q4 FY27 (~Feb-2027), exactly as the standing court said.** Red's Mode-B
headline — that the standing court's "known expiry" comfort is misplaced — is wrong on the dates.

**Finding 4b — "the mask rotates" fails on magnitude.** For Fin/Intercom to replace the expiring
4.0pt contribution it would need ~$1.84B of revenue on a $46B base, i.e. Salesforce paid **2.0×
revenue** for an AI-native growth asset. That does not happen. At a plausible 8–15× ARR, $3.6B
implies **$240–450M ARR = 0.5–1.0pt full-year, ~0.15–0.45pt in a partial H2.** Corroborating
bound: **no Item 1.01/2.01 8-K was filed** for the deal (verified against the full 8-K list —
nothing between 2026-06-02 and 2026-08-05), which is management's implicit assertion of
non-materiality. **The replacement mask is ~10% of the expiring one.** Red used a bound that cuts
in my favor as though it cut in its own. *(Exact ARR is not disclosed — flagged UNVERIFIABLE, but
bounded from both sides.)*

**Finding 4c — red switched measurement bases between its concession and its bar.** Red conceded
the acceleration on **subscription & support** (6.9% → 7.4% cc, +50bp) but set the H2 bar on
**total revenue**. On a consistent total-revenue cc-organic basis:

| Quarter | Reported cc | Informatica pts | **Organic cc** |
|---|---|---|---|
| Q3 FY26 | 8% | 0 | **8.0%** |
| Q4 FY26 | 10% | 3.99 | **6.0%** |
| Q1 FY27 | 12% | 4.52 | **7.5%** |
| Q2 FY27E | 10% | ~4.2 | **~5.8%** |

Organic total-revenue growth accelerated **+150bp** into Q1 (6.0% → 7.5%), not the +50bp red
conceded. And red's *"company-record-low ~5.9%"* for Q2 is **20bp below a level already printed in
Q4 FY26** — before any beat. Salesforce's Q3 FY26 guide was $10.24–10.29B (+8–9%) and it printed
$10.3B, +9%: at the top of the range. A typical beat puts Q2 organic back at ~6.3–6.8%, in line
with Q4 FY26. The "record low" framing does not survive computing the same metric for the
comparison quarter.

**Finding 4d — the required H2 acceleration is a RANGE, and red published only its worst point.**
FY27 guide 10–11% cc including ~3pts Informatica → FY27 organic cc **7.0–8.0%**. H1 organic ≈
6.65%. Therefore H2 required = 2 × FY − H1:

| FY27 organic cc lands at | H2 organic required | vs Q2 exit (5.8%) | vs Q1 actual (7.5%) |
|---|---|---|---|
| **7.0% (low end of company's own cc guide)** | **7.35%** | +155bp | **−13bp — BELOW Q1** |
| 7.5% (midpoint) | 8.35% | +255bp | +85bp |
| 8.0% (high end) | 9.35% | +355bp | +185bp |

At the **low end of the company's own guide the claim requires H2 organic to land slightly BELOW
where Q1 already printed.** Red published the midpoint as if it were the bar. The honest statement
is **+155 to +355bp off a guided trough, and at the low end simply "return to Q1."**

**Finding 4e — the claim names its drivers, and they are the cohort red conceded.** Q1 FY27
release, Robin Washington: *"We remain confident in delivering organic revenue acceleration in the
second half of FY27, **driven by growth in Sales, Service, Slack, Agentforce, and Data 360**."*
That list **excludes** Marketing, Commerce, MuleSoft and Tableau. Management is not claiming the
weak cohort recovers — it is claiming the 70.4% red verified as accelerating, plus the AI/data ARR
red valued at zero, carries H2. The claim's internal logic is **consistent with red's own verified
data**, not in tension with it.

**Finding 4f — it is gradeable.** Red's B3 rests on the company laundering "organic." But the
company quantifies Informatica **in dollars, every quarter, for revenue** — red's own A1, marked
VERIFIED and *"honest disclosure. Credit it."* Organic H2 is therefore directly computable, and
**Q4 FY27 is a clean read** (Informatica ≈ 0pts). A ~0.2–0.45pt unquantified Fin contribution
cannot launder a 155–355bp claim.

**What re-rates if it lands?** If H2 organic prints ≥8% cc with the Q4 FY27 unmasked print showing
reported ≈ organic ≥7.5%, the "agents eat seats" de-rate loses its factual basis. The reverse-DCF
above says the multiple is discounting ~2% growth; confirming ~8% organic on a clean print is the
event that forces the re-rate. **Under a 16× re-rate the stock is $225 (+18%); the asymmetry
against a price already discounting ~2% is the trade.**

**VERDICT: KILL 4 WEAKENED — B1/B2 stand as stated facts, B3 REFUTED, the "rotating mask"
Mode-B headline REFUTED on dates and magnitude.**

---

### KILL 5 — the order recommendation (cancel T2; keep T1 $175 but pull if unfilled by 08-19)

**On T2:** there is nothing to cancel (§0). The T2 *gate* does need repair — red is right that
leg 1 (organic cRPO) rests on a deflator the company withdrew (C1, upheld below). The correct
response is **re-specify the gate to observables the company still publishes**, not delete the
tranche. Working replacement, all three readable off the Q2 FY27 8-K on the day:
(i) reported cRPO ≥13% cc; (ii) FY27 revenue guide midpoint not cut; (iii) Informatica dollar
contribution disclosed for revenue **and** the H2 organic-acceleration sentence reaffirmed.

**On the "pull by 08-19" rule — three problems.**

*(a) It contradicts the rule it invokes.* Red cites the house **2-week** no-blind-entry rule. The
print is **2026-08-26** (company-confirmed; red's date verification is good work and I adopt it).
Two weeks before is **2026-08-12**, not 08-19. Red's own pull date leaves a **7-day** standoff.
The rule is either 2 weeks (pull 08-12) or it is discretion — red invokes the rule and then applies
a different number.

*(b) The forfeited fill probability is quantified and material.* Live $190.00; limit $175 =
**−7.89%**; IBKR daily IV **3.343%**. Sessions: 14 to the print, 9 to 08-19, 4 to 08-12.
Driftless first-passage, reflection principle, z = ln(175/190) / (σ_d√n):

| Pull date | Sessions | σ over window | z | **P(fill before print)** |
|---|---|---|---|---|
| Hold to print 08-26 | 14 | 12.51% | −0.657 | **51.1%** |
| Red's 08-19 | 9 | 10.03% | −0.820 | **41.2%** |
| Rule-consistent 08-12 | 4 | 6.69% | −1.229 | **21.9%** |

Red's rule forfeits **~10pp of fill probability (≈19% of the total chance)**; a rule-consistent
08-12 pull forfeits **~29pp (≈57%)**.

*(c) The adverse-selection premise is unsupported here, and contradicts the desk's own posted
probabilities.* Adverse selection requires the bid to fill **on information**. There is **no
scheduled CRM disclosure** between now and 08-26 (verified against the 8-K list; the only recent
filing is an Item 5.02 officer change already public). A −7.9% path in that window is a **~0.66σ
beta/sector move**, not company information. Meanwhile the desk carries **two live positive
priors on this very print** — the resolution pack `CRM|2026-08-26` beat-both at **our_p 0.72**,
and red's own freezable three-leg call at **our_p 0.60**. Pulling a below-market bid immediately
ahead of an event you rate 60–72% favorable is **negative-EV by the desk's own stated beliefs.**
You cannot hold p=0.72 that they beat and simultaneously price the bid as adversely selected.

**VERDICT: KILL 5 — over-trading. The pull rule is internally inconsistent, quantitatively
expensive, and contradicted by the desk's own posted probabilities on the same event.**

---

## RED FINDINGS I UPHOLD (the blue bench does not pretend)

| # | Finding | Blue verdict |
|---|---|---|
| C1 | **cRPO Informatica deflator withdrawn.** Verified independently: Q4 FY26 — *"cRPO of $35.1 billion, up 16% Y/Y and 13% in CC, **including 4pts Informatica contribution**"*; Q1 FY27 — *"cRPO of $33.6 billion, up 14% Y/Y and 13% in CC"*, no deflator, **in the same release where revenue bullets still quantify it in dollars.** | **UPHELD — ELEVATE, and UPGRADED beyond red's own argument.** Discretionary, one-directional, on the most important forward metric. Organic cRPO running ~150–300bp *above* organic revenue is the single cleanest discriminator between CRM and the CTSH/IBM/TDC value-trap base rate — and the withdrawal is exactly what blinds it. **The most important thing to watch at Q2.** |
| C5 | **NNAOV.** Verified by full-text count: "NNAOV" appears **2×** in the Q1 FY27 release — both inside the glossary definition — and **0×** in the 10-Q. Marketed as accelerating one quarter earlier, given **no value** now. | **UPHELD.** Partial mitigation: **Public Sector ARR was introduced the same quarter *with* a value ($2.0B, +23%)**, so metric count is roughly flat, not shrinking. Red's E1 "the set of proxies is shrinking" is **overstated**; C5 itself stands. |
| D1 | **No consumption revenue disclosed anywhere.** Verified: "consumption" 0× in the release / 13× in the 10-Q, all boilerplate risk factors; **"usage-based" 0× in both**; "Flex Credit" 2× in each, definitions only. No Flex Credits revenue-recognition policy. | **UPHELD.** Real gap. If consumption were material, a rev-rec policy would exist. |
| F3 | **The Q1 buyback was a $29B debt-funded leveraged recapitalization**, not FCF: noncurrent debt $10,439M → $39,280M; equity $59,142M → $34,235M. | **UPHELD.** The "net cash, they'll buy the dip" optionality is spent. |
| A5 | FY30 **"$60B plus organic"** → **"$63 billion in revenue in FY30"** with the organic qualifier dropped. | **UPHELD as carried** — I did not re-verify the Q3 FY26 wording this session; red's citation is specific and dated. Flag for re-verification before it is used as a standalone kill. |
| F5 | The FY27 "raise" is $46.00B → $46.05B on a $78M beat — arithmetic pass-through, not incremental confidence. | **UPHELD.** The standing file's "guides RAISED TWICE" framing should be softened accordingly. |
| F4 | Full-run-rate interest ~$420M/qtr vs $317M printed. | **UPHELD for EPS optics ONLY.** **Do not apply it to the FCF-based valuation** — the FY27 FCF guide was cut explicitly *"to reflect the impact of the $25 billion debt issuance for the ASR."* Applying it twice double-counts ~$400M/yr. |

---

## TWO NEW RED-FAVORABLE FACTS THE RED BENCH MISSED — entered against my own side

**(i) The 5→2 collapse happened in the one quarter the CFO personally held the principal-accounting-officer seat.**
[8-K 2026-03-06](https://www.sec.gov/Archives/edgar/data/1108524/000110852426000062/crm-20260306.htm):
*"as part of an internal finance reorganization, Robin Washington, the Company's Chief Operating
and Financial Officer, will assume the role of the Company's principal accounting officer,
effective as of March 9, 2026. **Sundeep Reddy, the Company's previous PAO, will remain in his
position as Chief Accounting Officer.**"* The career accountant was stripped of the PAO
designation on 2026-03-09; the 10-Q that collapsed the disaggregation was filed **2026-05-28**
under the CFO-as-PAO regime; Reddy was then replaced entirely. **This is the strongest available
version of red's C2 and red did not find it. I concede it and it partially restores the kill's
timing case.**

*Countervailing, same channel:* the seat was refilled by a **38-year EY audit partner who was
Salesforce's own Lead Audit Engagement Partner 2016–2021** — Guy Wanger, appointed CAO **and** PAO
effective 2026-06-15 ([8-K 2026-06-02](https://www.sec.gov/Archives/edgar/data/1108524/000110852426000138/crm-20260527.htm)).
He owns the **Q2 FY27 10-Q**. A firm optimizing for opacity does not install its former lead audit
partner as principal accounting officer. The reorganization **ended with a stronger accounting
seat than it started with**, and the next filing is his.

**(ii) A top operating executive departed two days ago, 20 days before the print.**
[8-K 2026-08-05](https://www.sec.gov/Archives/edgar/data/1108524/000110852426000160/crm-20260805.htm):
**Srini Tallapragada, President and Chief Engineering and Customer Success Officer**, stepped down
effective **2026-08-06**, transitioning to Special Advisor through 2027-08-06 at **$75,000/yr**
after January. Engineering *and* customer success — the two functions that own seat retention and
the Agentforce build — under one departing officer, immediately pre-print. **This post-dates
nothing; red filed the same day and missed it.** It is a genuine negative and I do not discount it.

**Governance counterweight, from the 2026 annual meeting**
([8-K 2026-06-01, Item 5.07](https://www.sec.gov/Archives/edgar/data/1108524/000110852426000131/crm-20260528.htm)):
red's G3 concession is far stronger than red realized. **ValueAct is not merely a 13F holder —
Mason Morfit sits on the board**, elected 2026-05-28 with 576,606,387 for / 35,106,845 against
(Morfit and VA Partners I, LLC appear as co-filers on CRM group filings, CIK 0001418812). An
activist with a **board seat** and $559M held unchanged had contemporaneous inside visibility into
the disaggregation decision and did not sell. Say-on-pay passed at **80.8%** and the equity-plan
amendment at **75.8%** — real dissent on compensation, worth noting, but no governance revolt.

---

## SCORECARD

| Kill | Red's grade | Blue's ruling |
|---|---|---|
| 1. Disaggregation 5→2 "permanently invisible" | ELEVATE, strongest kill | **WEAKENED → REVIEW.** Weak lines split across BOTH buckets; the weakest sits in the bucket *not* named for the AI product, which grew +10.3% organic; priors recast; signal survives. Timing conceded; new PAO-sequencing fact conceded. |
| 2. 13.4× is fair, FV $169–190 | Core valuation kill | **REFUTED ON METHOD, then PARTLY RESTORED by the base rate.** Price embeds ~2.0% nominal growth vs red's own bear table at 2.7–4.9% — so a comp band is not a fair value. But 1 floor / 1 wash / 4 traps at ≤14×, and **CTSH re-rated up while losing 33pp because E fell**, means the reverse-DCF only holds if E is durable. **Net: red's conclusion survives better than red's reasoning.** |
| 3. Agentforce option value | Not addressed | **UPHELD AGAINST RED.** $9–14/sh carried at zero; band is only $21 wide. |
| 4. H2 acceleration un-gradeable / mask rotates | B3 "biggest problem" | **REFUTED.** Informatica laps Q4 FY27 (verified from FY26 = Q4-only $399M); Fin ≈10% of the expiring mask; required H2 is +155 to +355bp, not a flat +240; basis switched mid-argument. |
| 5. Cancel T2, pull T1 by 08-19 | Order discipline | **OVER-TRADING.** Nothing to cancel; pull date violates the cited rule; forfeits ~10pp of fill probability; contradicts the desk's own 0.60–0.72 priors on the same print. |
| C1 / C5 / D1 / F3 / F5 / F4 | Various | **UPHELD** (F4 for EPS optics only — do not double-count against FCF). |

---

# BLUE BENCH — NET: **WEAKENED**

Red's two load-bearing kills are the disaggregation collapse and the valuation anchor. The first
is weakened from ELEVATE to REVIEW by the filing's own recast table — the decaying cohort was
**split across both surviving buckets**, the weaker half landing in the bucket *not* named after
the AI product, which grew **+10.3% organically**. The second is refuted on method: a reverse-DCF
on audited XBRL says $190 embeds **~2.0% nominal perpetual growth**, while red's own pessimistic
reconstruction of the business produces **2.7–4.9%**. Red never computed what its own price
objection implies.

Not OVERTURNED, for five reasons I will not paper over: the reclassification timing is genuinely
adverse and was **not** previewed; it occurred in the single quarter the CFO personally held the
PAO seat; the cRPO deflator withdrawal (C1) and the NNAOV silence (C5) are real, dated,
discretionary, one-directional disclosure choices; a top operating executive left 20 days before
the print; and **the ≤14× base rate is 1 floor / 1 wash / 4 traps**, with CTSH demonstrating that
the multiple can re-rate *up* while the holder loses 33pp because E erodes underneath it. That is
a degrading disclosure *posture* on a business whose improvement you can no longer fully verify —
which argues for tighter tripwires and modest size, not for grading the edge to zero.

**CONVICTION: 5/10 for the long** (marked down from 6/10 on the base-rate evidence). Above red's
implied 3/10, level with the standing file. The honest reading: the *edge* is a reverse-DCF gap —
price embeds ~2.0% growth against a bear-case 2.7–4.9% — and that gap is real **only if E holds**.
The base rate says that is exactly where names like this die, and **the company has withdrawn the
one disclosure (organic cRPO) that would let you check it.** Ownable, small, on a price gate, with
the burden of proof on the Q2 print.

---

## RECOMMENDED ACTION

**On the (non-existent) 2.9% position — §0 governs.**

1. **Correct the record first.** The desk holds **zero CRM**. Update `CRM.json` and any dashboard
   row asserting a held position. Restate all sizing percentages with an explicit denominator —
   current IBKR NAV is **$1,028,344**, and the standing 0.30%/0.75% figures imply a ~$3.1M book.
   **Do not act on a 2.9% "trim/hold" framing that has no referent.**
2. **Verify the resting bid exists.** Order 1353528703 shows status **REPLACED** with no successor
   CRM order visible. Confirm a working GTC bid before deciding anything about it.

**On the resting order — KEEP IT, unchanged, through the print.**

3. **Hold `BUY 53 CRM @ $175 GTC`. Do NOT pull it on 08-19.** $175 is 12.4× FY27 EPS — the bottom
   of red's own band and, on the reverse-DCF, a price embedding roughly **1.3% nominal growth**.
   The pull rule forfeits ~10pp of fill probability to avoid an adverse selection that has no
   scheduled information event to run through, and it contradicts the desk's own 0.60–0.72 priors
   on the same print. **Response taxonomy: this is a valuation finding, and valuation findings
   gate on price — the $175 limit already is that gate.** Do not lift toward $190.
4. **Reinstate T2, re-specified, gated on the Q2 FY27 print (2026-08-26).** Replace the broken
   leg-1 with observables the company still publishes: (i) reported cRPO ≥13% cc; (ii) FY27
   revenue guide midpoint not cut; (iii) Informatica dollar contribution disclosed for revenue
   **and** the H2 organic-acceleration sentence reaffirmed. Size at the standing 0.45% **of the
   stated deploying-book denominator**, and stage it below market, not at it.
5. **Classification: keep OWNABLE; do NOT reclassify to RP_FAIR — but the edge is now
   CONDITIONAL and must be labelled as such.** RP_FAIR asserts the overlay is zero. The
   reverse-DCF gap (price ~2.0% vs bear-case 2.7–4.9%) plus $9–14/share of uncapitalized AI/data
   ARR is an edge — **conditional on E holding.** The base rate says that condition is where this
   cohort dies, so record the classification as **OWNABLE / edge conditional on the E-durability
   tripwire (#9)**, and if the Q2 print fails that tripwire, red's RP_FAIR reclassification
   becomes correct and should be adopted without further argument.

**Tripwires — adopt red's, add two.**

6. Keep red's two disclosure tripwires verbatim (disaggregation not restored **and** no Agentforce
   revenue line → no adds above $169; NNAOV promoted while cRPO is de-emphasised → full exit).
7. **Add:** *Agentforce Apps* growth falls below **~7%** for two consecutive quarters → the
   Marketing & Commerce decay is now large enough to overwhelm the Sales/Service core inside the
   surviving bucket → halve. *(This tripwire only exists because the 5→2 collapse is more
   observable than red concluded — it is the mechanism, made into an instrument.)* Note the
   honest limit: M&C is only ~20% of that bucket, so a 100bp M&C deterioration moves the printed
   number ~20bp. **Granularity genuinely fell; the signal is diluted ~5:1, not destroyed.**
8. **Add:** the **Q4 FY27 print (~Feb-2027)** is the high-information event, not Q2. Informatica
   contributes ~0pts there and reported ≈ organic for the first time in five quarters. Reported
   revenue growth **<6.5% cc** on that print → full exit. This is the standing file's kill #7 and
   red's demotion of it was wrong on the dates.
9. **Add — the E-erosion tripwire, which the base rate says is the one that actually kills you.**
   The trap cohort (CTSH, IBM '19, TDC) lost money with the multiple flat or *rising* because
   earnings fell underneath it. Grade **E, not P/E**, quarterly: non-GAAP operating margin below
   **33.5%** (guide 34.3%), **or** FCF growth guided negative ex-interest, **or** organic cRPO cc
   below organic revenue cc for two consecutive quarters → **exit regardless of the multiple.**
   Third leg requires the deflator back; if it is not restored, treat the leg as **failed, not
   passed** — UNVERIFIABLE is not clean.
10. **Axis correlation is now a live constraint, not a footnote.** ADBE (staged bids $238/$195) is
    the same trade — incumbent software, AI terminal-value doubt, ≤14× — and ADBE's 13.7× "floor"
    gave zero support, cutting to 7.8× in two months. With HUBS/MNDY/NOW/SAP held, CRM is the
    5th–6th expression of one factor. **Red's "do not add on the axis" is upheld:** fill T1, then
    require an axis-level review before T2 actually deploys.

**Escalation.** Three findings are decisive and load-bearing and should be re-verified with full
context and a stronger model before they drive capital: the **bucket-mapping reconciliation**
(§Kill 1 — an inference from weights with Slack as a solved free parameter; rival mappings are
rejected, but it remains an inference); the **Fin/Intercom ARR bound** (§4b — derived from
purchase price, not disclosed); and the **E-durability condition** (§Kill 2 — the whole blue case
now rests on it, and the base rate says it is where this cohort fails).

---

### Verification note

- Live quote pulled from IBKR **before** any valuation work; positions and open orders polled
  before any sizing claim. Prices, filings and XBRL all read **2026-08-07**.
- Primary documents fetched this session: Q1 FY27 10-Q, Q1 FY27 / Q4 FY26 / Q3 FY26 / Q2 FY26
  8-K EX-99.1s, 8-Ks of 2026-03-06, 2026-06-01, 2026-06-02, 2026-08-05, the complete
  UPLOAD/CORRESP history (2019/2021/2022), and XBRL companyfacts for cash flow and SBC.
- **My own web-search budget was exhausted (200/200) before I could source Intercom's ARR.** It is
  declared UNVERIFIABLE and bounded from both sides by inference rather than assumed clean. Every
  other finding above is bound to an SEC-filed primary document.
- **The ≤14× base rate arrived from a separate base-rate agent after my first draft and it moved
  this filing against my own side** — conviction 6/10 → 5/10, red's C1 upgraded, and tripwires 9
  and 10 added. Basis caveats carried from the source: the forward-P/E basis is mildly ambiguous,
  and trap verdicts measured to Aug-2026 include the Jun–Jul 2026 AI-capex credit-scare shock,
  which flatters the trap count. **Peer disaggregation line-counts (is 2 lines an outlier?) remain
  UNVERIFIABLE** — the agent tasked with them has not returned that table.
- The bucket-mapping in §Kill 1 is a **reconstruction from disclosed weights**, not a company
  statement. It reconciles to 0.00pp on both buckets, which is strong, but it is labelled as
  inference throughout.
