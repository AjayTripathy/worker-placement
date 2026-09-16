# TMUS — CONFIRMATION COURT (v1.6) — capital gate

**Date** 2026-08-05 (session opened under the 20260804 lane; date rolled mid-court — noted, all
prices re-pulled live). **Live** $172.94 (IBKR bid 172.93 / ask 172.98, intraday, `is_close:false`;
yfinance cross-check 173.23). **Prior batch court** RP_FAIR 5/10 @ $177.09, band 165-175.
**This court** 4/10 RP_FAIR-QUALIFIED. **Capital gate: NOT OPEN at spot.**

House rule satisfied: batch-courted 5 re-tried independently. Nothing inherited; every load-bearing
number re-derived from EDGAR/XBRL and the filed 8-K exhibits.

---

## MODE B FIRST — what the memo's framing hid

The batch court framed TMUS as a clean single-print de-rate ("fell 10.7% on subscriber COUNT while
every economic metric improved"). Three things that framing did not contain, each independently
verified below:

**B-1. The de-rate is 11 months old and sector-relative, not print-driven.** TMUS is −37.5% from its
March-2025 all-time high (276.49) and −33.0% from its 52-week high (258.17, ~Sept-2025). Over the
same YTD window **VZ is +16.1% and TMUS is −14.4%** — a 30-point intra-sector divergence. The
07-23 print was one −10.7% day inside a year-long compression. The driver is a terminal-value
narrative (below), not the quarter.

**B-2. The company silently stopped disclosing the metrics that would measure the risk.** Dated
below. This is the decisive finding of the court.

**B-3. The capital cycle is rising while the disclosed capex line is flat.** $2.7B of fiber
joint-venture equity calls sit *below* the Adjusted-FCF line and outside the ~$10.0B capex guide.

---

## 1. CARRY MATH — is the ~9.8% adjusted-FCF yield real?

**Definition, read from the source.** Q2-2026 8-K Ex-99.1 (acc. 0001283699-26-000100), Non-GAAP
reconciliation, verbatim: *"Adjusted Free Cash Flow — Net cash provided by operating activities less
Cash purchases of property and equipment, including capitalized interest."* Tied to the dollar
across six quarters: Q2-26 7,500 − 2,703 = **4,797**; H1-26 14,722 − 5,326 = **9,396**. No
add-backs of any kind.

| Claim | Method / authority | Finding |
|---|---|---|
| Adj FCF = OCF − capex, no add-backs | Q2-26 Ex-99.1 recon table vs 10-Q cash-flow statement | **CONFIRMED** — exact to $1M, six consecutive quarters |
| Metric excludes merger cash costs | Guidance text: "Adjusted Free Cash Flow, **including** net payments for UScellular merger-related costs" | **REFUTED** — merger cash costs are IN. Honest. |
| Securitization add-back gone | `ProceedsFromCollectionOfRetainedInterestInSecuritizedReceivables` = $0 FY2025 and every FY25/26 quarter (was $3,579M FY24) | **CONFIRMED** |
| Prior definition was dirtier | FY2024 guidance table (Q4-2023 8-K Ex-99.1): OCF 21,500-22,300 − capex (8,600-9,400) **+ securitization proceeds 3,400-4,000** = Adj FCF 16,300-16,900 | **CONFIRMED** — ~22% of the old metric was an add-back |
| The FY25 definition change was disclosed | Q4-2025 Ex-99.1 fn(2): receivable-sale proceeds moved investing→operating eff. Nov-1-2024, "did not have a net impact on Adjusted Free Cash Flow" | **CONFIRMED — clean disclosure** |
| OCF is not being pumped by scaling receivable sales | 10-Q Note 5: EIP Sale Arrangement funding $1.3B at both 6/30/26 and 12/31/25; Service Receivable Sale $775M at both dates | **CONFIRMED — flat, not scaled** |

**Ruling on the definition: TMUS's "Adjusted Free Cash Flow" is the cleanest version of this metric
the company has ever published, and cleaner than most large-cap "free cash flow." It is not an
adjusted-metric artifact.** The batch court's instinct here was right.

**But the metric excludes three real, recurring cash costs** (all sourced, all disclosed elsewhere):

| Excluded cash cost | Where it lives | FY24 | FY25 | FY26E |
|---|---|---|---|---|
| Spectrum & other intangible purchases | Investing — `PaymentsToAcquireIntangibleAssets` | $3,471M | $2,568M | ~$800M (H1 actual $510M; Auction 113 $278M total) |
| Finance-lease principal repayments | Financing — `FinanceLeasePrincipalPayments` | $1,367M | $1,252M | ~$1,330M (H1 $664M) |
| Fiber JV equity calls | Investing — "Investments in unconsolidated affiliates" | — | $983M (H1-25) | $700M (i3 Broadband, H2-26) |

Spectrum is lumpy and 2026 is a light year, but it is *not optional* for a wireless carrier: 10-Q
Note 6 also carries the Comcast 600MHz agreement at **$1.2-3.4B, targeted H1-2028**, and a
**$2.0B GoNetspeed/Greenlight JV call in H1-2027** (10-Q Note 3).

**The number, at live $172.94 × 1,072,671,613 shares (10-Q cover, 7/17/26) = $185.5B market cap:**

- FY26 Adjusted FCF guide midpoint $18.6B → **10.03% yield.** The 9.8% claim is real; at today's
  lower price it is better.
- Owner FCF = 18.6 − 2.28 (3-yr normalized spectrum) − 1.33 (finance-lease principal) − 0.70 (i3 JV)
  = **$14.3B → 7.70%.**

**FINDING: VERIFIED with a 230bp haircut.** The carry is real and the definition is honest; the
headline yield overstates distributable owner cash by ~2.3 points.

**Payout coverage.** H1-2026 buybacks $7,146M + dividends $2,221M = $9,367M vs H1 Adjusted FCF
$9,396M — **99.7% of the metric returned.** Net debt (excl. tower obligations) 12/31/25 $82,954M →
6/30/26 $84,095M (+$1.14B) and cash 5,598 → 2,825 (−$2.77B). So the return program is running
~$2.3B/yr ahead of owner cash, funded by balance sheet. Dividend $1,101M/qtr ≈ $4.10/sh ≈ **2.37%**
(IBKR 2.38%; batch's 2.43% was the stale-price artifact). Share count 1,125.4M (7/18/25) → 1,072.7M
(7/17/26) = **−4.7%/yr.** 2026 authorization $18.2B, **$8.9B remaining** at 6/30/26.
*Capital-allocation note: H1-2026 repurchases were struck at an average of $203.07/share (10-Q
equity note) against a $172.94 mark — a −15% carry on $7.1B. Price-insensitive buyer.*

---

## 2. FAIRNESS (RP_FAIR bar #1) — shown, not asserted

**Own 5-year band.** Core Adjusted EBITDA sourced from the Q4-2022, Q4-2023, Q4-2025 and Q2-2026
8-K Ex-99.1 reconciliations: FY21 $23,576M / FY22 $26,391M / FY23 $29,116M / FY24 $31,771M /
FY25 $33,924M / FY26 guide $37,100-37,500M. Net debt reconstructed as
`LongTermDebt + FinanceLeaseLiability − Cash` — **method validated exactly against the company's own
factbook table** (12/31/25: 86.28 + 2.27 − 5.60 = $82.95B vs company $82,954M; 6/30/26 = $84.09B vs
company $84,095M).

| Year-end | Px | Shares (M) | Mkt cap | Net debt | EV | EV/TTM Core EBITDA | **EV/FWD** |
|---|---|---|---|---|---|---|---|
| 2021-12-31 | 115.98 | 1,249.2 | 144.9 | 70.1 | 215.0 | 9.12x | **8.15x** |
| 2022-12-31 | 140.00 | 1,234.0 | 172.8 | 70.0 | 242.7 | 9.20x | **8.34x** |
| 2023-12-31 | 160.33 | 1,195.8 | 191.7 | 72.4 | 264.1 | 9.07x | **8.31x** |
| 2024-12-31 | 220.73 | 1,144.6 | 252.6 | 75.2 | 327.8 | 10.32x | **9.66x** |
| 2025-12-31 | 203.04 | 1,106.9 | 224.8 | 83.0 | 307.7 | 9.07x | **8.25x** |
| **2026-08-05** | **172.94** | **1,072.7** | **185.5** | **84.1** | **269.6** | **7.51x** | **7.23x** |

5-year forward band **8.15x-9.66x, median 8.31x. Today 7.23x = 11.3% below the 5-year LOW.**
Trailing band 9.07x-10.32x vs 7.51x today = 17% below the low. **"Bottom of own band" is not merely
met — the band is broken through.** CONFIRMED, shown.

**Cross-section, same FCF definition (FY2025 audited XBRL OCF − capex, over live market cap):**

| | OCF | Capex | FCF | Mkt cap | **Yield** |
|---|---|---|---|---|---|
| TMUS | 27,950 | 9,955 | 17,995 | 185.5 | **9.70%** (10.03% on FY26 guide) |
| VZ | 37,137 | 17,011 | 20,126 | 190.2 @ $45.77 | **10.58%** |
| T | 40,284 | 20,842 | 19,442 | 157.1 @ $22.92 | **12.38%** |

**TMUS has the LOWEST cash yield of the big three on the identical definition.** The "9.8% FCF
yield" reads cheap in isolation and is the most expensive of its own peer set.

**What is the market paying for the growth gap? Zero.** TMUS guides Core Adjusted EBITDA +10.0-10.5%
FY26 vs VZ/T low-single-digit, and trades at 7.23x forward — inside the range where VZ/T trade
(rough peer EV/EBITDA ~6-7x; *flagged approximate — peer EBITDA not re-derived, see gaps*). The
entire historical growth premium has compressed to nil.

**Ruling on bar #1: PASS, qualified.** Cheap versus its own history (verified, shown). Fair-to-rich
versus peers on cash yield. This is a *fair* price, not a bargain.

---

## 3. TAILS (RP_FAIR bar #2)

### (a) Capex / fiber cycle — **NOT bounded by the headline**
Capex guide unchanged at ~$10.0B (both Q1 and Q2 revisions: "No change"), and cash capex is a
modest 26% of service revenue. But 10-Q Note 3 discloses **new** commitments signed in April 2026:
- **i3 Broadband JV** (Wren House): ~**$700M** for 50%, closing H2-2026.
- **GoNetspeed + Greenlight JV** (Oak Hill): ~**$2.0B** for 50%, closing H1-2027.

Both are equity-method, so the cash lands in *Investments in unconsolidated affiliates* — inside
investing activities, **below the Adjusted-FCF line**, invisible to both the capex guide and the
FCF guide. $2.7B over four quarters ≈ 15% of one year's Adjusted FCF. **This is the masking channel
of the name: the fiber build is routed through JVs so it never touches the two metrics management
is measured on.** Fully disclosed in the notes, never in the release. Bounded in size, understated
in presentation.

### (b) Subscriber trajectory / promotional intensity — decelerating, guide achievable
Postpaid net account adds: Q2-25 318k → Q3-25 ~416k → Q4-25 261k → Q1-26 217k → Q2-26 277k
(−13% YoY). Account churn 0.92% → 1.04% (Q1-26) → 0.99%, attributed to "higher average
broadband-only accounts, including following the acquisition of Metronet." FY26 guide 950k-1,050k
reiterated; H1 actual 494k implies 456-556k in H2 vs 677k in H2-2025 — the guide already embeds
~20-30% YoY deceleration and is comfortably reachable. Factbook cites "increased promotional
activity, including the success of bundled offerings" as an ARPA headwind.

### (c) **Organic vs acquired — the batch court's TOP UNVERIFIABLE, now RESOLVED**
Factbook Ex-99.2 p.4 footnotes quantify the acquisitions: **Q3-2025 +1,448,000 postpaid accounts
(UScellular) and +633,000 (Metronet and other) = 2,081k acquired** inside the YoY window; base
adjustments −18k (Q1-26) and −16k (Q2-26).
Postpaid accounts 31,502k (Q2-25) → 34,700k (Q2-26) = **+3,198k**, of which
organic net adds (416+261+217+277) = **1,171k** and acquired **2,081k**, less −34k base = 3,218k ✓.

**~65% of the account growth is acquired; ~35% organic.** Accounts +10.2% YoY decomposes to ~6.6pp
acquired / ~3.6pp organic; times ARPA +2.0% → **the "+13% industry-leading postpaid service revenue
growth" headlined throughout the release is roughly 5-6% organic.** The split is never presented.
Still industry-leading (VZ/T grow 2-3%) — but half the marketed magnitude.

**Forward consequence:** UScellular closed 2025-08-01. From the **Q3-2026 print the acquired
contribution anniversaries**, and reported service-revenue growth drops mechanically from 8.9%
total / 12.6% postpaid to roughly 5-7%. This is arithmetic, not a forecast.

### (d) **Disclosure narrowing — the decisive finding**
| Metric | Q4-2025 release (2026-02-11) | Q1-2026 (2026-04-28) | Q2-2026 (2026-07-23) |
|---|---|---|---|
| Postpaid **phone** net customer adds | 962k Q4 / 3.3M FY25 | **absent** | **absent** |
| Postpaid **phone churn** | 1.02% Q4 / 0.93% FY25 | **absent** | **absent** |
| Total postpaid net **customer** adds | 2.4M Q4 / 7.8M FY25 | **absent** | **absent** |
| Broadband / High-Speed-Internet net adds | disclosed | **absent** | **absent** |
| Prepaid net adds + churn | 57k / 2.76% | **absent** | **absent** |

Verified by text search of the filed exhibits: "High Speed" appears **0 times** in the Q2-2026
release *and* the full SEC-filed Investor Factbook; "phone" survives only in equipment-mix
commentary and the glossary. The factbook's table of contents now reads *"4 Account Metrics"* — the
Customer Metrics section is gone, replaced by three account-level charts (Postpaid Accounts, ARPA,
Account Churn). For contrast, the FY2023 release headlined all five customer metrics as
"industry best."

**No announced methodology change.** Zero instances of "no longer," "beginning in 2026," "changed,"
"revised," or "metric" in the Q1-2026 release that dropped them. The Q1 headline over the removal
was *"Accelerating Account Growth."*

Under the honesty doctrine this is the one item that clears the elevate boundary: it is not
de-emphasis of a disclosed datum — **the datum is no longer available.** Postpaid phone churn is
precisely the series that would register satellite-substitution or cable-MVNO share loss, and it
went dark one quarter before that risk became the market's narrative. Intent is unknowable and is
not alleged; the monitoring channel for the load-bearing risk is nonetheless closed.

### (e) **The tail the batch court did not have: SpaceX / Starlink direct-to-device**
Cause chain, tape-verified daily bars + news channel:
- **2025-09**: SpaceX acquires EchoStar spectrum (~$17B). TMUS 52w high $258.17 dates from here.
- **2026-05**: FCC approves both the AT&T and SpaceX EchoStar purchases. TMUS/T/VZ agree in
  principle to a **three-way spectrum-pooling JV "to help satellite providers reach more
  customers"** (10-Q Note 3, announced 2026-05-14) — the incumbents' defensive response.
- **2026-06-30**: 52-week low **$165.66** (−4.8% on 6/29, −3.6% on 6/30) on Starlink-mobile fears.
- **2026-07-14**: Bernstein cuts targets across VZ/CHTR/T/CMCSA/TMUS on the SpaceX connection.
- **2026-07-23**: Q2 print. Open $175.75 from a $190.94 close → close **$170.42 = −10.75%**
  (CONFIRMED from bars). Coverage: *"T-Mobile Falls Despite Earnings Beat. CEO Shoots Down Expanded
  Starlink Deal"* — TMUS is the incumbent Starlink MNO partner and declined to expand.
- **2026-07-31**: Semafor — **Deutsche Telekom / T-Mobile full-combination talks stall.** −4.0% day
  (181.52 → 173.34). Removes whatever takeout bid was in the price.
- **2026-08-05 (today)**: SpaceX's first earnings report targets **global direct-to-device by
  2028**; T/VZ/TMUS lower premarket. TMUS **−2.4%** intraday.

This is an undated, unquantified terminal-multiple risk with live escalating news flow, and TMUS
carries it worse than peers (−14.4% YTD vs VZ +16.1%). The cable complex is the cautionary comp:
CHTR market cap ~$18.0B and CMCSA ~$87.3B — this market re-rates connectivity utilities violently
when a technology substitution story takes hold.

### (f) Regulatory — **clean**
No DOJ matter (zero mentions in the 10-Q). Residual FCC inquiries from the August-2021 cyberattack,
one resolved 2024-09-30, remainder immaterial beyond the $400M charge already taken (10-Q Note 14).
Auction 113: 102 AWS-3 licenses for $278M. **Bounded. This tail is genuinely small.**

### (g) DT ownership — **53.9%, verified from primary; no selldown**
10-Q Note 12: Q2-2026 dividends $1,101M total, **$593M paid to DT** → **53.86%**; six months
$1,200M of $2,221M → 54.0%. Buyback absorption is a non-issue — DT is not selling, and the reported
merger talks imply it wants *more*, not less. FCC foreign-ownership limits cap how far the stake can
drift up on buybacks. The real DT tail is governance, not overhang: a 54% controlling holder with
its own cash-flow problem sets the $18.2B return program.

### (h) Leverage and the maturity ladder — **comfortable, but it is eating the growth**
Net debt (excl. tower obligations) $84,095M / LTM Core Adjusted EBITDA $35,902M = **2.34x**. Total
debt $86.9B; short-term debt $6,117M + short-term finance leases $1,178M due inside 12 months;
$2.0B CP program undrawn. H1-2026: issued $6.4B, repaid $7.8B.
**Interest expense net: $922M (Q2-25) → $1,055M (Q2-26), +14.4% YoY** — ~$4.2B annualized on an
~4.9% average cost, and rising as 3.15-3.90% notes (TMUS29/32/35/36/37/38) roll into 5%+ paper.
This is the arithmetic behind the conversion gap: **Core Adjusted EBITDA +10% but Adjusted FCF
+2.2-4.5%.** FY24 Adj FCF $17,032M → FY25 $17,995M (+5.7%) → FY26E $18,600M (+3.4%). The cash line
compounds at ~3%, not 10%.
*Watch item: the EIP Sale Arrangement ($1.3B of funding) **expires November 2026** — inside the
guidance period.*

**Ruling on bar #2: FAIL.** (c)+(d)+(e) compound: a mechanical growth-optics reset in 11 weeks, an
unbounded and actively escalating terminal-value tail, and the removal of the series that would
have tracked it. (a) is bounded but understated. (f)(g)(h) are genuinely clean.

---

## 4. TAPE / PATH CHECK

52w high 258.17 → −33.0%. All-time high 276.49 (Mar-2025) → −37.5%. 52w low **165.66 on
2026-06-30**; today $172.94 = **+4.4% off the low, 36 days elapsed**, and the last five sessions are
177.09 → 177.21 → 172.94 with a −2.4% day today on live SpaceX news. **This is not a late bounce off
an old low — it is a re-test of a fresh low in an intact downtrend.** The correct risk framing is
continuation, not chasing. IV 33.9% annualized vs 30-day realized 47.6% — realized is running rich
to implied, i.e. the tape is more disorderly than options are pricing.

---

## 5. AI-BREAK CONFLICT CHECK (house frozen AI-BREAK|2027-12-31 @ 0.45)

TMUS 10-Q: "data center" **0 mentions**, "artificial intelligence" 1 (risk factors), "AI" 3. No
datacenter, no AI-capex revenue. The only AI-adjacent growth claim ever made is the Q1-2026 line
*"As an initial step for T-Mobile to support the broader evolution of physical AI, Figure AI's F03
humanoid robots in production are designed to connect to T-Mobile's 5G Advanced network"* —
unquantified marketing, and it was **dropped from the Q2-2026 release** (replaced by a "P3 AI
Services Champion" award). Enterprise/wholesale growth in the guide rests on postpaid business
accounts, not AI demand.

**Ruling: the entry does NOT require the AI cycle holding. Exposure ≈ nil, and the sign is
favorable** — a 2.3x-levered, 2.4%-yielding domestic cash utility is a rotation beneficiary if the
capex cycle breaks. Against ~$5.2M / 26% household AI-complex exposure, TMUS is a diversifier. This
is the strongest argument *for* the name and it survives the court.

---

## 6. FOUR-IDEA FRAME

1. **What we believe.** Fair, not cheap. A 7.2x-forward, 2.3x-levered, IG carry asset shrinking its
   share count 4.7%/yr, whose true owner-FCF yield is ~7.7% and whose reported growth is about to
   halve on an acquisition anniversary. The multiple has already broken below its 5-year floor,
   which prices a good deal of the satellite risk — but not all of it, and not the Q3 optics reset.
2. **What the market believes.** Two incompatible things. Bulls own a 10% FCF-yield compounder at
   the bottom of its band. Bears own a connectivity utility facing a 2028 satellite substitution,
   with a controlling holder that just walked away from buying the rest. VZ +16% / TMUS −14% YTD
   says the bears have had the tape since September 2025.
3. **What resolves it.** The **2026-10-22 Q3 print**: reported service-revenue growth mechanically
   resets to ~5-7%; whether the market treats that as news is the single cleanest read on how much
   of the growth story is still in the price. Second: whether TMUS restores phone net-adds and phone
   churn — restoring them would be a strong honesty signal and would reopen the monitoring channel.
4. **What proves us wrong.** Phone churn restored and flat-to-better; the Oct-22 print re-accelerates
   organic accounts above 300k; capex and the JV calls absorbed with Adjusted FCF guidance raised a
   third time; a re-rate back through 8.15x on FY27 numbers = ~$233. In that world we underwrote a
   fine business at a fair price and merely missed 15%.

---

## 7. VERDICT, SIZING, GATES

**4/10 RP_FAIR-QUALIFIED** (down from the batch 5/10). **RED TEAM REQUIRED: NO** (score < 6).
Escalation recommended on the metric-removal finding only.

**Which bar failed:** bar #1 (fairness) **PASSES** — verified and shown, below the 5-year floor.
Bar #2 (tails bounded) **FAILS** — the Starlink terminal tail is unbounded and escalating, the fiber
JV calls sit below the metric line, and the leading indicator for the decisive risk was withdrawn
from disclosure. Under the doctrine, one failed bar ⇒ **revert to gates. No in-band entry at spot.**

Instrument selection per the response taxonomy: this court produced *both* a business-risk finding
(satellite substitution — unquantifiable) → **size cut**, and a timing finding (Q3-26 optics reset)
→ **price gate + tranche**. Applied accordingly.

**Scenarios (FY27E Core Adj EBITDA base $39.0B, net debt ~$85B, ~1,000M shares):**

| | p | fv | basis |
|---|---|---|---|
| Bear | 0.32 | **140** | 6.0x fwd on a flat $37.3B — satellite narrative hardens, growth optics reset lands badly |
| Base | 0.45 | **185** | today's 7.23x held on FY27E + buyback, discounted ~1yr |
| Bull | 0.23 | **218** | re-rate to the 5-yr low 8.15x on FY27E |

**e_fv 178.2 vs $172.94 → edge +3.0pp.** Plus 2.37% dividend and ~4.7%/yr share shrink. The carry
is the return; there is no price edge. That is the correct RP_FAIR signature.

**Entry plan — gates, no spot fill. Ruled cap 1.2%; this court authorizes 0.5% total:**
- **No chase above $175.** (Tightened from the batch's 177.)
- **Tranche 1 — 0.25% (~$8.3k on the $3.3M deployable) at ≤ $163**, i.e. *below* the 52-week low of
  165.66. Rationale: the low is 36 days old and being re-tested on live news; a fill above it is
  paying for a break that has not been tested.
- **Tranche 2 — 0.25% at ≤ $152** (≈6.9x fwd / ~8.5% owner-FCF yield).
- **Remaining 0.2% to the 0.7% RP_FAIR full size unlocks only after a re-court on the 2026-10-22
  print.** If the growth-optics reset clears without damage and phone metrics are restored, this is
  a legitimate 0.7% carry position and the objection was always the entry price, not the name.
- Zero current telecom exposure verified (`get_account_positions`, 2026-08-05: no TMUS/VZ/T/CMCSA/
  CHTR). No sleeve conflict, no wash-sale surface.

**Kill triggers (dated):**
1. **2026-10-22** — postpaid net account adds < 200k, OR account churn > 1.05%.
2. **2026-10-22** — FY2026 Adjusted FCF guidance cut below $18.4B (a *raise* is the base case; a cut
   inverts the thesis).
3. **Any print** — FY2027 capex guide above ~$11.0B, or total announced fiber-JV equity commitments
   above ~$3.5B cumulative.
4. **2026-11** — EIP Sale Arrangement (expires Nov-2026) not renewed on comparable terms.
5. **Any date** — DT files a 13D/A or SC 13G/A reducing its stake below ~50%, or announces a
   secondary.
6. **Any date** — a commercially launched Starlink/SpaceX consumer postpaid tariff in the US
   (as opposed to a 2028 roadmap statement).
7. **Standing** — leverage above 3.0x net debt / Core Adj EBITDA.

**Frozen call (PROPOSE ONLY — not written to packs):**
```
id:    TMUS|2026-10-22
bar:   Q3-2026 reported TOTAL service revenue growth prints <= 7.0% YoY
       (vs +8.9% in Q2-2026), i.e. Q3-2026 total service revenues <= $19,518M
       against Q3-2025 $18,241M, as the UScellular acquisition (closed 2025-08-01)
       anniversaries out of the comparison.
our_p: 0.80
```
Derivation: Q2-2026 total service revenues $18,983M; Q2→Q3 sequential growth has run +1.0% to +2.5%
over the last four years, implying $19.17-19.46B, i.e. +5.1% to +6.7% YoY. Clearing 7.0% requires
sequential growth above +2.8%, which has not occurred without an acquisition closing in the quarter.

---

## VERIFICATION GAPS (UNVERIFIABLE ≠ clean)

1. **Peer EV/EBITDA not independently re-derived.** VZ and T EBITDA were not rebuilt from their
   filings; the "market pays zero for the growth gap" conclusion rests on the fully-sourced FCF-yield
   table, not on the approximate peer multiples. Peer net debt was pulled
   (`LongTermDebtAndCapitalLeaseObligations`: VZ $143.4B + $21.8B current − $1.8B cash; T $134.6B −
   $17.6B cash) but their EBITDA definitions were not normalized.
2. **Whether TMUS publishes phone net adds / phone churn in a non-SEC IR supplement.** Verified
   absent from the 8-K release and the full filed Investor Factbook (Ex-99.2, incl. its table of
   contents and all chart captions). Not checked against the IR website's standalone quarterly
   materials. If it turns up there, the finding downgrades from "removed" to "moved," and the court
   should be re-run — this is the single item most capable of changing the verdict.
3. **The Semafor DT-merger report was read through the news channel, not from a primary source.**
   No 8-K, 13D/A or DT ad-hoc release was located confirming or denying talks. Treated as PLAUSIBLE,
   not CONFIRMED; the verdict does not rest on it.
4. **Q3-2025 postpaid net account adds (~416k) is derived** (FY2025 1.2M − H1 523k − Q4 261k), not
   read from a filing. It feeds the organic/acquired split, which independently reconciles to the
   observed account balance within ~20k.
5. **Q2-2026 earnings call transcript not read.** Management's own framing of the metric change, the
   Starlink question and the fiber JV funding path was not obtained.
6. **WebSearch budget exhausted session-wide per the contract**; all news via the Google News RSS
   channel, which returns headlines and dates but thin article bodies.
