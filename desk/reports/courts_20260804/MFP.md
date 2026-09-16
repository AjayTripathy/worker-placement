# MFP — Midera Food Processing, Inc.
**Court:** court_queue_20260804, TIER_4 spinoffs · **Date:** 2026-08-03 (grades for the 08-04 session)
**Live:** $47.29 (2026-08-03 close, IBKR ctr 895214815 NASDAQ, `is_close: true`)
**Queue label:** FORCED_SELL_DOWNGRADE, LATE_WINDOW, dist 2026-06-29
**Prior art (research_ledger):** CLOSED 2026-07-09, realized **+$613 net (+11.5%)**, 2-day hold.
Bought 150 @ $35.50 into the 07-07 dump, sold 75 @ $39.47 + 75 @ $39.75 on 07-09.
Standing instruction: *"RE-BUY only <$31… otherwise done."*

## VERDICT: 2/10 — PASS at spot. But the standing re-buy trigger is WRONG and must be raised to $38–41.
The flow edge was real and we harvested a third of it. What the prior underwrite missed is that this
is not a plain cyclical: **Ed Garden's fund holds 7.5% and put its Head of Research on the board
before the shares ever traded.** That changes the asset, not the price we should pay today.

---

## 1. TAPE VERIFICATION — the queue's distribution date is wrong by five sessions

| Claim | Method / source | Result | Finding |
|---|---|---|---|
| Distribution 2026-06-29 | 8-K 0001193125-26-295649 (event 07-02), Item 1.01 | *"**On July 6, 2026**, The Middleby Corporation completed its spin-off of Midera Food Processing, Inc."* | **REFUTED.** 06-29 is the **credit-agreement closing** date (8-K 0001193125-26-288554), not the distribution |
| Record date / ratio | SC 13D 0001213900-26-078067, Item 3 | *"Each holder of Middleby common stock received **one share of Common Stock for each share** of Middleby common stock held of record as of 4:00 p.m., Central Time, on **June 26, 2026**"* | CONFIRMED — 1:1, record 06-26 |
| First regular-way trade | same 13D: *"The Common Stock commenced trading on The Nasdaq Stock Market LLC on **July 7, 2026**"* | IBKR bars corroborate exactly: 06-29→07-06 volumes 82,142 / 28,572 / 105,728 / 148,377 / 89,135, then **07-07 = 2,312,906** | **CONFIRMED: 2026-07-07** |
| "first_close 35.00, early_high 40.00, trough 35.00, +37%" | IBKR bars | every one of those prints is from the 06-29→07-06 **when-issued** window (ticker MFPVV) | **REFUTED as price premises** |

**Corrected path (regular way only, from 2026-07-07):**
first close **$36.60** → **$47.29** (08-03) = **+29.2% in 19 sessions**. No trough after day 1; the low
of the regular-way series is the 07-07 intraday **$34.65**, and it has not been revisited.
- **Days since distribution = 28**, not 35. The window is at the **ACTIVE→LATE boundary**, closing ~10-05.
- Off the low: **+36.5%**, 19 sessions. PATH CHECK: this is not a bounce to buy, it is a completed move.

**The trade we actually did, re-measured against the clean tape:** we bought day 1 at $35.50 and exited
day 3 at ~$39.61 for +11.5%. Held to today the same 150 shares would be **+$1,768 (+33.2%)** against the
realized **+$613**. We captured **35% of the available move.**

---

## 2. FLOW SIGN — and a doctrine contradiction in our own house

**Index placement: UNVERIFIED from primary.** The generator records Middleby in the S&P MidCap 400 and
MFP placed down into the S&P SmallCap 600 — the genuine forced-SELL sub-cohort, of which MBGL is the
type specimen. **S&P DJI's announcement pages return HTTP 403 across this entire lane**, so neither the
placement nor its effective date was confirmed against an S&P primary. Recorded as UNVERIFIED, not as
supporting evidence. Russell June-2026 recon status also unchecked for this name.

**What the tape does confirm:** a single 2.31M-share day on 07-07 (regular-way day 1) against a 45.2M
share count — **5.1% of shares outstanding in one session** — then an immediate, uninterrupted 19-session
grind higher on decaying volume. That is the signature of a mechanical sell that clears on day 1 and a
discretionary re-rating afterwards.

### The doctrine contradiction worth banking
The orphan generator's own doctrine states: *"the durable edge is the DISCRETIONARY orphan drift over
the following 4-8 weeks, not the mechanical print."* Our execution rule was *"never marry the flow"* —
and we exited on day 3. **The doctrine and the execution rule pointed in opposite directions, and the
tape says the doctrine was right.** On this single observation (n=1, FLOW cohort calibration datapoint
#1), the 2-day zone-exit forfeited about two-thirds of the move. That is not a reason to change the
rule on one datapoint, but it *is* the reason to record the cohort's post-day-3 drift as an explicit,
measured quantity rather than leaving it to a habit.

---

## 3. CAPITAL STRUCTURE LOADED AT SEPARATION (all CONFIRMED from the Form 10 information statement,
EX-99.1 to the 8-K of 2026-06-22, accession 0001193125-26-276742)

| Item | Value | Source |
|---|---|---|
| Shares outstanding | **45,214,588** | Pro Forma Note (h) |
| Distribution ratio | **1 MFP : 1 MIDD**, record 2026-06-26 | SC 13D Item 3 |
| Credit facility | **$1.0B** five-year senior **secured**: $750M USD revolver + $250M multi-currency revolver; BofA agent; accordion = greater of $151M and 100% of consolidated EBITDA | 8-K 06-29, Item 1.01 |
| **Debt actually drawn** | **$252.0M** ("Cash received from issuance of debt $252,000" thousand) | Pro Forma Note (a) |
| **Cash distribution TO Middleby** | **$(229.0)M** at separation | Pro Forma Notes (a) and (g) |
| Debt issuance costs | $(3.0)M | Pro Forma Note (a) |
| Net pro forma cash adjustment | **+$20.0M** | Pro Forma Note (a) |
| Pro forma interest on new debt | **$13.466M/yr** at a weighted-average **4.75%** + 0.20% undrawn commitment fee | Pro Forma Note (b) |
| Related-party loans settled | $(11.5)M | Pro Forma Note (d) |
| Net parent investment reclassified to APIC | $1,049.9M | Pro Forma Note (g) |
| Dividend policy | **None.** *"We do not currently intend to pay any cash dividends in the foreseeable future."* | "Dividend Policy" |
| Filer status | **Emerging growth company** (elects the extended transition period) | 8-K cover |

**Leverage is trivial: $252M drawn against $152M of FY25 adjusted EBITDA ≈ 1.7x gross, with $748M
undrawn on the revolver.** Contrast HONA (3.2x) and FDXF (2.6x, negative equity). Middleby did **not**
strip this one — $229M out on $853M of revenue is a modest dividend. Combined with a 1.7x-levered
balance sheet and a $1.0B facility with an EBITDA-sized accordion, **MFP was deliberately capitalized
as an acquisition platform**, not as a cash extraction.

**Standalone cost load — $32M/yr. CONFIRMED from the investor deck, and higher than I first estimated.**
The information statement itself discloses nothing: *"We expect to incur incremental costs as a
standalone public company in certain corporate support functions… **however, such costs are not
reflected in the unaudited pro forma condensed combined statement of earnings as these dis-synergies
are not considered autonomous entity adjustments.**"* On that basis I first wrote that no figure exists
and used a $15–25M estimate.

**That was wrong.** The investor deck (slide 66 vs slide 75) reconciles exactly: FY2026 guidance on the
**segment** basis is Adj. EBITDA **$186–208M**; on the **standalone** basis it is **$154–176M**. The
difference is **$32M at both ends** — the standalone public-company cost load, quantified. It is **28%
above the top of my estimated range**, and it flows straight through the equity.

*(This also withdraws a flag: the two EBITDA bases are arithmetically identical, not competing
presentations. Management's disclosure here is internally clean.)*

---

## 4. THE BUSINESS AND WHAT THE PRIOR UNDERWRITE MISSED

**FY2025 (fiscal year ended January 3, 2026), from the information statement:**
- Net sales **$853M** — equipment and installation $512M (60%), **aftermarket parts and service $341M (40%)**
- Net earnings **$83M (9.7%)**
- **Adjusted EBITDA $152M (17.8%)**
- 29 manufacturing sites globally (13 US, 16 across Denmark, France, Germany, India, Italy, Sweden, UK);
  innovation centres in the US, India and Italy
- 56% of sales in US/Canada, 44% EMEA/LatAm/APAC
- Customers: large protein processors (bacon, charcuterie, sausage, hot dogs, poultry, alternative
  protein, case-ready, lunch meat, pet food) and bakery (bread, buns, artisan, sweet goods, cakes,
  biscuits, crackers, pizza, pastries, tortilla, snacks)

A 40% aftermarket mix on an installed base of food-processing lines is a genuinely defensive revenue
stream — this is a better business than "cyclical capital equipment" implies, and the prior underwrite
under-weighted it.

### ⚠️ THE FINDING THE PRIOR UNDERWRITE MISSED ENTIRELY: an activist with a board seat from day zero
**SC 13D filed 2026-07-14, accession 0001213900-26-078067**, event date 2026-07-07:
- Reporting persons: **Garden Investment Management, L.P. ("GIM")**, GI SPV I L.P., GI SPV I GP LLC,
  Garden Investment Management GP LLC, and **Edward P. Garden** — 73 Arch Street, Greenwich CT;
  counsel Willkie Farr & Gallagher.
- **3,380,845 shares = 7.5%**, shared voting and dispositive power on all of it. Acquired **in the
  spin-off** (they were Middleby holders), not bought in the open market.
- GIM's stated purpose, verbatim: *"The present principal business of GSI is to seek long-term capital
  appreciation primarily through investments in **The Middleby Corporation** and the Issuer."* This is a
  dedicated Middleby-complex vehicle.
- **Board seat already taken:** *"effective as of immediately prior to the consummation of the Spin-Off,
  **Brian Jacoby, Founding Partner and Head of Research at GIM, was appointed to serve as a member of
  the board of directors of the Issuer**."*
- Item 4, verbatim: *"The Reporting Persons may consider, explore or develop plans or make proposals…
  with respect to, among other things, potential changes in the Issuer's **operations, governance,
  capital structure, capital allocation policy, management compensation policies and approach, and/or
  corporate strategy and plans**."*

Edward Garden co-founded Trian Fund Management. This is an inside-the-tent activist with a
research-partner director, a 7.5% economic stake, a 1.7x-levered balance sheet and a $748M undrawn
revolver. **That is a materially different asset from "a fairly-valued food-processing-equipment
cyclical in a margin trough."** Our own file is stale on this point and the ledger note should be
corrected rather than left standing.

### The 08-03 Form 4 cluster is benign — hypothesis raised and killed
Eleven Form 4s filed 2026-08-03 (accessions …-330321, -330295, -330260, -330226, -330206, -330197,
-330185, -330168, -329845, -329842, -329820) into a +29% move looked like an insider-selling cluster.
It is not. Contemporaneous headlines identify them as post-spin equity awards — *"Midera Food Processing
(MFP) grants RSUs after Middleby spin-off"*, *"Director Nerbonne of Midera Food Processing (MFP) reports
new RSUs"*, *"Midera Food Processing (MFP) CEO reports RSU grants tied to spin-off"* (Stock Titan,
2026-08-03), consistent with the S-8 filed 2026-07-02. **Routine spin-related grants, not distribution.**
Recorded as a raised-and-refuted hypothesis, not as a clean bill — the Form 4 bodies themselves were
not read line by line (see §8).

---

### ⚠️ THE GUIDANCE EXISTS — and the marketed margin story is a RECOVERY, not an expansion
**Correcting my own first pass:** I wrote that "MFP has published no financial targets of any kind…
there is nothing to hold management to." **That is refuted.** An **82-slide Midera investor deck**
exists and carries full guidance.

**FY2026 guidance (slide 66, segment basis):** net sales **$915–945M** (vs FY25 $853M = **+7.3% to
+10.8%**), Adj. EBITDA **$186–208M**. **Standalone basis (slide 75): $154–176M**, midpoint **$165M**.
2019–2025 actuals shown with a *"CAGR (Incl. M&A): ~11%"* on sales and *"~12%"* on EBITDA. Soft hedge
on the same slide: *"Quarter to quarter growth can be volatile, and we measure ourselves on rolling
12-month performance basis."*

**Q1-2026 actuals (slide 69, segment basis):**
| | Q1-25 | Q1-26 | Δ |
|---|---|---|---|
| Segment net sales | $168M | $224M | **+34%** (organic +29.1%) |
| Segment Adj. EBITDA | $30M | $41M | +38% |
| Margin | 17.9% | 18.5% | +60bp |
| Orders | $184M | $231M | +25% |
| **Backlog** | $274M | **$416M** | **+52%** |

Management: *"Record backlog and strong order demand provide confidence in 2026 guide."*

**The nuance cuts against the headline.** Backlog went **$410M (Q4-25) → $416M (Q1-26) — +$6M, flat
sequentially** — while the quarter shipped $224M. Book-to-bill was ~1.03x in the quarter (≈1.02x over
the trailing eight). The +52% year-over-year is measured against a **depressed Q1-25 base**, and the
+29.1% organic surge is substantially **backlog conversion of tariff-delayed orders releasing**, not a
step-change in new demand.

**The divergence, in two parts:**
1. **The deck markets a *"~500 basis point uplift"* to a 20–23% margin by 2028.** But **estimated
   standalone margin was 21.3% in 2024A and 16.4% in 2025A.** The "uplift" is measured off the
   depressed 2025 base and merely **returns the business to where it already was in 2024.** Two
   independent routes reach this — the segment margin history (19.8–25.6% since 2019) and the
   standalone reconciliation (21.3% → 16.4%). **This is a recovery target sold as an expansion target,
   and it is the correction that most matters to the "margin trough" framing** in our own prior file.
2. **The M&A algorithm works against the margin target, and the deck never reconciles them.**
   Slide 63: *"EPS Accretive Year 1"*, *"ROIC Target DD+ by Year 3"*, **_"M&A Velocity ~3-5 deals per
   year"_**, *"Target Size Avg. ~$25-$50M"*, **_"~11% EBITDA margin"_** on the ~35 identified targets,
   *"Maintaining Strong Balance Sheet sub 3x Net Leverage"* — against a fragmented market of *"2,500+
   Food Processing equipment manufacturers globally"* where Midera holds **~1% share of a ~$70B TAM**.
   Acquiring at **~11% EBITDA margins into a 16–20% base is structurally dilutive on entry** — which is
   precisely what compressed 2025 — yet the 20–23% 2028E target explicitly **_"Excludes contribution
   from future acquisitions."_** Executing the stated 3–5 deals a year ($75–250M/yr) would hold
   *reported* margin below the 20–23% path even if the organic bridge works perfectly. **The margin
   target and the M&A-velocity target cannot both be read off reported results.** That is the question
   to press on the call.

No forward-looking non-GAAP reconciliation appears anywhere — every target slide carries the *"cannot
be reasonably estimated"* footnote. **No EPS, standalone-ROIC, tax-rate or working-capital target
exists**, and **no dividend and no buyback appears anywhere across all 82 slides.**

---

## 5. VALUATION — why it is a pass at $47.29

- Market cap = 45.215M × $47.29 = **$2.138B**
- Debt $252M; net debt ≈ **$200M** (after the +$20M pro forma cash adjustment) → **EV ≈ $2.34B**
- FY25 net sales $853M → **EV/Sales 2.74x**; FY26E $915–945M → **2.50x**
- FY25 Adjusted EBITDA $152M → EV/EBITDA **15.4x**
- **FY2026E standalone Adj. EBITDA $165M (guide midpoint) → EV/EBITDA 14.2x** ← the right anchor
- Standalone earnings bridge: FY26E standalone EBITDA $165M − D&A (~$35M) − $13.5M interest, taxed at
  24% ≈ **$88M** → EPS ≈ **$1.95** → **P/E ≈ 24x** *(better than the 33–39x in my first pass, which
  used trailing earnings and understated the cost load at the same time — the two errors partly
  offset)*
- Even at the top of the FY26 guide ($176M), EV/EBITDA is **13.3x** — still at the ceiling of the comp
  range

**Comparable set:** food-processing equipment (JBT Marel, GEA, Bühler) has historically cleared at
roughly 9–13x EV/EBITDA, and Marel itself was acquired at ~13x. **MFP at 15.4x trailing is at or above
the top of the range for the sector, on a margin the company itself characterises as depressed.**

**What our own $31 re-buy trigger implies:** market cap $1.40B, EV ~$1.60B, **10.5x FY25 EBITDA.** That
is a fair level for the business as the prior underwrite understood it — but it is not a level this
stock is likely to see with a 7.5% activist holder and a board seat in place. **The trigger is stale and
under-specified, and leaving it at $31 guarantees we never re-engage.**

### Scenarios (anchored on the FY2026E standalone Adj. EBITDA guide of $154–176M)
| | p | Path | Multiple / base | FV |
|---|---|---|---|---|
| **Bear** | 0.30 | The Q1 organic surge was one-time backlog conversion (sequential backlog flat, book-to-bill 1.03x); FY26 lands at the low end; M&A at ~11% target margins dilutes reported margin | 11x on $154M | **$33** |
| **Base** | 0.45 | FY26 delivered at the midpoint; margin recovers toward 2024's level by 2028 but M&A velocity holds *reported* margin below the 20–23% path | 13x on $165M | **$43** |
| **Bull** | 0.25 | Top of the guide, the 2028 target is hit *and* deals prove accretive; re-rate on activist plus platform credibility | 15x on $176M | **$54** |

**E[FV] = $42.75 vs $47.29 → edge = −9.6%.** The edge got *more* negative once the deck was read: the
standalone cost load is **$32M, above the top of my $15–25M estimate**, and FY26E standalone EBITDA of
$165M is only ~9% above the $152M trailing. More data pulled the number down, not up.

---

## 6. FOUR-IDEA FRAME
1. **Consensus:** thin. The only substantive coverage located is *"Midera Food Processing: A First Look
   Without Middleby"* (Seeking Alpha, 07-08) and a Barron's consumer piece (*"Costco Hot Dog: Company
   That Helps Keep It at $1.50 Is Now a Publicly Traded Stock,"* 07-07). **No sell-side initiation with
   a price target was located.** This is the least-covered name in the batch — genuinely under-followed,
   which is the one thing still working in its favour.
2. **Our prior variant (now superseded):** "a fairly-valued food-processing-equipment cyclical in a
   margin trough; we owned the index-cross dislocation, not the business." Correct on the trade,
   **incomplete on the asset** — it missed the activist and the platform balance sheet.
3. **Our variant now:** an under-covered 38–40%-aftermarket industrial with a 1.7x-levered balance
   sheet, a $748M undrawn revolver, an EBITDA-sized accordion, a Trian-lineage activist holding 7.5%
   with its Head of Research on the board, and ~1% share of a fragmented ~$70B TAM. A genuine
   re-rating and roll-up setup. **But** it is up 29% in 19 sessions at **14.2x the FY26E standalone
   EBITDA guide** against a 9–13x comp set; the marketed *"~500bps uplift"* is a **recovery to the
   2024 margin, not an expansion**; the standalone cost load is **$32M**, above my estimate; and the
   stated M&A velocity (3–5 deals/yr at ~11% target margins) **works against** the very margin target
   the deck excludes acquisitions from. The asset improved; the price improved faster, and the story
   improved fastest of all.
4. **What would change our mind:** Q2 backlog **building** (not converting), **or** management
   reconciling the margin target with M&A velocity on the call, **or** the first acquisition closing
   above ~15% entry EBITDA margin, **or** a pullback into $35–38 on no news.

---

## 7. CATALYST MAP

| Catalyst | Date | p | Magnitude | Notes |
|---|---|---|---|---|
| **First standalone quarterly report + call (Q2, fiscal quarter ended ~2026-07-04)** | **2026-08-13** — from the deck/IR read; **not independently confirmed against an IR release here** | 0.85 | ±8–15% | The quarter **ended two days before the distribution**, so it is substantially a carve-out period. Q3 (Oct/Nov) is the first true standalone quarter |
| **Q2 ending backlog** | 08-13 | — | — | **The number to read first.** Q1 backlog built only +$6M sequentially on 1.03x book-to-bill. If the Q1 organic surge was tariff-delayed conversion, Q2 backlog falls |
| Whether management reconciles the 20–23% margin target with 3–5 deals/yr at ~11% target margins | 08-13 call | 0.30 asked and answered | ±4% | The deck never does; the two targets cannot both be read off reported results |
| Activist agenda becomes public (operating plan, capital allocation, strategic review) | any time | 0.35 within 12m | +8–20% | The 13D reserves the full Item 4 menu; the board seat is already held |
| First acquisition off the $748M undrawn revolver | H2-26 / 2027 | **0.65 within 12m** (the deck guides 3–5 deals/yr) | ±6%, direction depends on entry margin | Accordion at 100% of consolidated EBITDA; >$700M of capacity under the sub-3x ceiling. **Deals at ~11% EBITDA margins are dilutive on entry** |
| S&P SmallCap 600 index effects | UNVERIFIED | — | — | Placement never confirmed against an S&P primary |
| Q3 — first true standalone quarter | Oct/Nov 2026 | 0.90 | ±10% | The quarter that actually prices the $32M cost load |

**A print lands inside two weeks.** Combined with a −9.6% edge, that settles it: no capital, and no
exposure into the first report.

---

## 8. PLAN, KILLS, AND THE CORRECTED TRIGGER

**Plan: no position, no order staged.** Nothing about this name at $47.29 clears the bar.

**Corrected re-open band — raise from $31 to $35–38.** Stated as a change to our own prior work rather
than a new idea. The $31 trigger was set against an asset description that omitted the 7.5% activist
stake, the board seat, the 1.7x leverage and the $748M dry-powder revolver — all of which argue for a
higher number. **But the deck read argues back down**: the standalone cost load is $32M (not the
$15–25M I assumed), FY26E standalone EBITDA of $165M is only ~9% above trailing, and the marketed
margin uplift is a recovery to 2024 rather than an expansion. **$35–38 is ~10–11x the FY26E standalone
guide** — inside the food-equipment comp range and 12–19% below the $43 base FV. My first pass wrote
$38–41; the deck pulled it back. Size on a fill **0.4%**, limits only, band expires **2026-11-30**
(after the Q3 print).

**Kill triggers:**
- **Q2 or Q3 ending backlog below $416M** → the Q1 organic surge was tariff-delayed conversion, not
  demand; base case to $33.
- FY26 standalone Adjusted EBITDA guidance **cut below $154M**, or reported standalone margin below
  **16%** in any quarter → the recovery premise is wrong.
- An acquisition closing at an entry EBITDA margin **below 11%**, or **net leverage above 3.0x** on a
  deal without a disclosed accretion case → the roll-up is buying revenue, not earnings.
- **GIM files an amended 13D below 5%, or Brian Jacoby leaves the board** → the asset reverts to the
  prior description and the trigger reverts to $31.
- Any restatement or material-weakness disclosure at the first standalone close → kill (EGC filers get
  reduced attestation; the first close is the risk point).

**FREEZABLE CALL:**
`MFP | 2026-08-13 | Q2-2026 ending backlog is BELOW the Q1-2026 level of $416M | our_p = 0.55`
Rationale: this is the crux of the whole underwrite. Q1 shipped $224M against $231M of orders and
backlog built only **+$6M sequentially** ($410M → $416M) on ~1.03x book-to-bill, so the headline "+52%
backlog, record demand" is a depressed-base comparison against Q1-25's $274M. If the +29.1% organic
quarter was tariff-delayed backlog releasing rather than new demand, Q2 backlog draws down. Only 0.55
because a single heavier shipping quarter can mechanically swing book-to-bill either way, and because
the backlog series is second-hand from a deck read (see §9).

---

## 9. VERIFICATION NOTES — what is NOT verified
1. **S&P index placement and effective date — UNVERIFIED.** spglobal.com/spdji returns 403. The
   FORCED_SELL_DOWNGRADE classification rests on the generator's own membership table, not an S&P
   primary. Russell June-2026 recon status also unchecked.
2. **First earnings date 2026-08-13** comes from the deck/IR read and was **not independently confirmed
   against an IR press release in this court.** Treat as high-confidence, not verified.
3. **Pro forma cash and therefore exact net debt** — the information statement discloses only the
   +$20M adjustment, not a pro forma cash balance. Net debt of ~$200M is derived.
4. **The eleven 08-03 Form 4s** were classified from contemporaneous headlines plus the 07-02 S-8, not
   from reading each filing's transaction table. Directionally safe, not line-verified.
5. **Deck provenance.** The 82-slide investor deck is not on EDGAR as an exhibit. The three
   load-bearing slides (66 guidance, 69 Q1 actuals/backlog, 63 M&A algorithm) were re-read and
   confirmed at source. Second-hand and **not independently confirmed**: the FY24→FY25 orders series
   ($702M → $945M), the TAM decomposition, the 38% aftermarket average, the "5–7% organic CAGR"
   callouts, and the deck-wide absence of any dividend or buyback mention.
6. Middleby's own segment disclosures for the food-processing business were not pulled as a
   cross-check on the deck's backlog and organic-growth series. A gap for any re-underwrite at the
   $35–38 band.

**Two of my own findings were REFUTED by the deck read and are corrected above, not buried:**
(a) I wrote *"MFP has published no financial targets of any kind — there is nothing to hold management
to."* **False.** Full FY2026 guidance and 2028 margin targets exist. (b) I wrote *"the company published
no standalone cost figure; $15–25M is our estimate."* **False.** It is **$32M**, recoverable by
differencing slides 66 and 75, and above the top of my range. Both errors came from stopping at the
information statement instead of finding the deck — **exactly the failure the MBGL doctrine's
"always pull the pre-spin deck alongside the Form 10" rule exists to prevent.** The net effect moved
the edge from −5.6% to −9.6% and the re-open band from $38–41 down to $35–38.

## 10. DOCTRINE OUTPUT (for the generator)
- `distribution_date_from_completion_8k` — MFP is the cleanest failure case in the batch. The generator
  dated the distribution to **06-29** because that was the first traded bar; 06-29 was in fact the
  **credit-agreement closing**, and the actual completion was **07-06** with regular-way trading on
  **07-07**. Five sessions of when-issued tape were treated as the base, corrupting first_close, early
  high, trough and the total-return figure simultaneously. **Parse the completion 8-K's Item 1.01/5.01
  text ("On [date], [Parent] completed its spin-off of…"), never the first bar.**
- `activist_13d_on_spinco` — a spinco 13D filed within 30 days of distribution is a **high-value,
  low-cost** read that the orphan generator does not currently make. It resolves in one fetch whether
  the register contains a control block, a passive inheritor, or an activist with a board seat, and it
  changes both the asset description and the drift expectation. Add it to the recall floor for every
  spinco at day 30.
- `spin_capitalization_intent` — read the drawn/undrawn split and the accordion, not just total debt.
  $252M drawn on a $1.0B facility with an accordion sized at 100% of EBITDA and only $229M dividended
  to the parent is a **platform** capitalization; $4.1B dividended out with negative equity (FDXF) is an
  **extraction**. The same "total debt" field cannot distinguish them.
- `stale_rebuy_trigger_audit` — a re-buy trigger inherits the asset description that was current when it
  was written. When new primary facts change the asset (here: an activist and a board seat), the
  trigger must be re-derived, not left standing. Otherwise a stale number silently converts a WATCH
  into a permanent no.
