# GAW.L — GAMES WORKSHOP GROUP PLC · FULL TIER-1 SOLO COURT
**Court:** `principal_seed_20260804` · **Date:** 2026-08-04 · **Frame:** thesis-first (Stage-0), principal-seeded
**Seed thesis:** *"the Warhammer franchise heat is real and GAW is the royalty carrier."*
**Verdict: REJECT 3/10** — the franchise heat is real, GAW is genuinely the carrier, and the carry is
**quantifiably immaterial** to a £6.3bn market cap. Meanwhile the core engine's **second-half exit rate is
flat-to-down**, the multiple sits at the **64th percentile of its own 7-year band**, and the company's own
**forward-contracted licensing book is down 30–77% on every leading metric it discloses.**

---

## 0. TAPE + UNITS (LSE addendum §1 — priceMagnifier discipline)

| item | value | source |
|---|---|---|
| Spot | **19,080.0 GBp = £190.80** | IBKR snapshot conid **35151400** (LSE), tick **2026-08-04 15:29:41 UTC**, `is_close:false` (LSE open) |
| Cross-check, GBP plane | daily bar 2026-08-04 close **190.80** | IBKR `get_price_history` STK/LSE/ONE_DAY — **both planes agree, 100× error excluded** |
| Cross-check, third source | 19,030 (Aug monthly) | yfinance GAW.L — within 0.3% |
| Prior close | 19,230.0 GBp | IBKR |
| 52w high / low | 22,260 / 13,794.5 GBp | IBKR misc_statistics |
| Shares in issue | **33,044,841** (nil treasury) | RNS Total Voting Rights, 03-Aug-2026 |
| Market cap | **£6,305.0m** | 33,044,841 × £190.80 |
| ADV (90d) | **US$13.28m** | IBKR `avg_90d_usd_volume` |
| Executability | **VERIFIED** — conid 35151400 resolves, live numeric quote returned | not DATA-GATED |
| LSE account permission | **PROVEN** — BRBY (940sh) and TW. (2,700sh) held live | `get_account_positions` 2026-08-04 |
| Live touch | **DATA-GATED** — `bid_ask` returned `{}` at the pull | assume ~10–20bp (FTSE-100) |

**Staleness (addendum §8): NOT stale.** FY26 annual results printed **28-Jul-2026, seven days ago**. This court
is built on days-old primary data. H1 FY26 (to 30-Nov-2025) is used only for the half-split bridge.

---

## 1. WHAT ACTUALLY PRINTED — FY26 (52wks to 31-May-2026), RNS 28-Jul-2026 07:00

| £m | FY26 | FY25 | Δ |
|---|---|---|---|
| Core revenue | 626.8 | 565.0 | **+10.9%** (+12.2% cc) |
| **Licensing revenue** | **32.9** | **52.5** | **−37.3%** |
| Revenue | 659.7 | 617.5 | +6.8% |
| Core operating profit | 245.1 | 211.8 | +15.7% |
| Licensing operating profit | 29.9 | 49.5 | −39.6% |
| Operating profit | 275.0 | 261.3 | +5.3% |
| Profit before tax | 275.7 | 262.8 | +5.7% |
| **EPS (basic)** | **624.0p** | **594.9p** | **+4.9%** |
| DPS declared & paid in period | 485p | 520p | −6.7% (April deferral, not a cut) |
| Core gross margin | 71.1% | 69.5% | +1.6pp |
| Core ROCE | **196%** | 191% | — |
| Cash | 182.9 | 132.6 | +50.3 |

Guidance: **none.** GAW has never guided. Outlook in full: *"After a record year, we remain customer focused
and look forward to building on the progress we have made… Exciting times."* There is no estimate trajectory
to read — the contract's DE-RATE-vs-DERAILMENT test has to be run off actuals, which is what §3 does.

**Market reaction (cause-check, daily bars):** 27-Jul close 203.0 → 28-Jul (results) open 200.0, low **187.5**,
close **198.2 (−2.4%)** → 04-Aug **190.8**. Cumulative **−6.0% over 5 sessions**. Google News RSS headline:
*"Games Workshop falls despite record year"* (Yahoo Finance UK, 28-Jul); *"EPS Beats Expectations, Revenues Lag"*
(31-Jul). **The print was received as a revenue miss with an EPS beat — consistent with the licensing shortfall.**

---

## 2. MODE B FIRST — the three findings the seed framing hid

### 2.1 DECISIVE: the second half was flat, and adjusted for a one-off tariff credit it was DOWN

Nothing in the RNS says this. It falls out of subtracting the H1 FY26 interim (26wks to 30-Nov-2025,
RNS ~mid-Jan-2026) from the full year.

| £m (H2 = FY − H1) | H2 FY26 | H2 FY25 | Δ |
|---|---|---|---|
| Core revenue | 310.7 | 295.6 | **+5.1%** (H1 was **+17.3%**) |
| Core operating profit | 119.0 | 113.7 | **+4.7%** (H1 was **+28.5%**) |
| Core operating margin | 38.3% | 38.5% | **−0.2pp** |
| Licensing operating profit | 15.6 | 21.5 | **−27.4%** |
| **EPS** | **304.1p** | **306.0p** | **−0.6%** |

**And then the tariff credit.** H1 FY26 reported *"c.£6.0 million in the period reported as a direct consequence
of US tariff changes"* — a straight cost, **no reclaim**. The FY26 report says the group paid c.£12m gross and
*"Following the US Supreme Court ruling we reclaimed £7.8 million… We have recognised all of this reclaim in the
period to May 2026."* The ruling and the reclaim application necessarily post-date the H1 close, so **the entire
£7.8m credit sits in H2 and inside core gross margin** (the GM walk confirms: tariffs net −0.7pp for the year,
which is gross −1.9pp plus reclaim +1.2pp).

> **H2 FY26 core operating profit ex-reclaim ≈ £111.2m vs £113.7m — roughly −2.2% year-on-year, on +5.1%
> revenue, with core margin ~35.8% vs 38.5%. The full-year margin expansion from 69.5%→71.1% GM and
> 37.5%→39.1% core operating margin was an H1 phenomenon plus a non-recurring credit.**

Grade: **PLAUSIBLE (high confidence)** — every input is disclosed; the half-attribution of the reclaim is a
necessary inference, not a stated split. This is the single most important number in the court.

**Honesty grade on GAW: CLEAN.** Every component is disclosed plainly, tariffs are explicitly *not* treated as
exceptional (*"Unlike some companies, we do not consider tariffs as an exceptional item"*), and the licensing
decline is volunteered in the CEO's own words. The divergence here is between the **headline "record year"
framing and the H2 arithmetic**, not between GAW's marketing and GAW's data. Per the honesty-ELEVATE boundary,
a genuinely honest discloser is not the catch — **the error is in the pitch, not the issuer.**

### 2.2 DECISIVE: the franchise heat is real; GAW's forward-contracted royalty book is shrinking

The seed evidence (FDEV_TELEMETRY §3) is confirmed and *not* in dispute: Total War: WARHAMMER 40,000 sits at
**#7**, Dawn of War IV **#17**, Dark Heresy **#30** of 5,204 unreleased Steam titles — one of the strongest
franchise signals visible on the chart, and GAW collects on all of them regardless of studio. That leg is REAL.

But every **leading** licensing metric GAW discloses is down:

| leading metric (GAW's own disclosure) | FY26 | FY25 | Δ |
|---|---|---|---|
| Fixed income amounts signed under licensing contracts | **£2.5m** | £11.1m | **−77%** |
| Licensing receivables falling due within 12 months | **£11.5m** | £16.4m | **−30%** |
| Total licensing receivables | **£15.5m** | £24.3m | **−36%** |
| Cash received from licensees | £42.9m | £57.0m | −25% |
| Licensees who **terminated** in the period | **2** (£5.9m final contractual payments) | — | — |

**So the reported £32.9m includes £5.9m of termination money. Underlying licensing revenue ≈ £27.0m — below
FY24's £31.0m.** CEO, verbatim: *"The general backdrop, from our perspective, still remains challenging for
this industry."* FY27 licensing priority, verbatim: *"to sign a few significant licensing deals"* — i.e. **not
yet signed.** 85% of licensing revenue is PC/console.

**Full disclosed licensing series (primary, RNS-verified across five annual reports):**

| £m | FY19 | FY20 | FY21 | FY22 | FY23 | FY24 | FY25 | FY26 |
|---|---|---|---|---|---|---|---|---|
| Licensing / royalty revenue | 11.3 | 16.8 | 16.3 | 28.0 | 25.4 | 31.0 | **52.5** | 32.9 |
| Licensing operating profit | — | — | 15.0 | 25.4 | 22.0 | 27.0 | **49.5** | 29.9 |

FY25's £52.5m is the *Space Marine 2* year (launched Sep-2024). **It is a pulse, not a plateau — the series
proves it.** The 7-year CAGR is 16.5% but the shape is sawtooth, and the market has now seen the down-tooth.

**Timing:** *every* top-30 Warhammer title is **UNDATED** as of 04-Aug-2026 — TW:WH40K, Dawn of War IV, Dark
Heresy, and Frontier's Chaos Gate–Deathwatch (#379, three announcements ever, no date). Creative Assembly's
announce-to-launch cycle is 1–2 years, so TW:WH40K is a **FY28 event at the earliest (GAW FY28 = Jun-27→May-28)**.
**There is no dated licensing catalyst inside FY27.**

### 2.3 The entire visible game pipeline is worth 1–5% of the share price

This is the seed thesis quantified, using the FDEV telemetry calibration (**~50 units per Steam review**,
reproduced independently against two company-disclosed unit figures) and the anchor of what a genuine
megahit actually paid GAW.

**Anchor — Space Marine 2.** Best-selling Warhammer game ever (~7m units yr-1 at ~$60 ≈ $420m gross, ~$294m
net of platform). GAW's *entire* licensing revenue stepped from £31.0m (FY24) to £52.5m (FY25), i.e. **+£21.5m
across all licensees combined.** That implies an effective take of roughly 7–9% of publisher net receipts.
**A once-in-a-decade title is worth ~£20m of GAW revenue in its peak year.** *(Unit figure PLAUSIBLE from
public disclosure, not verified here; the £21.5m step IS verified.)*

**Applying that rate to the pipeline:**

| title | wishlist rank | plausible yr-1 units | GAW royalty (£m) | earliest GAW FY |
|---|---|---|---|---|
| Total War: WARHAMMER 40,000 | **#7** | 2–4m (TW:WH III ≈ 2m+) | **6–16** | FY28 |
| Dawn of War IV | #17 | 0.5–1.5m (DoW III ≈ 0.5m) | 1.5–5 | FY28+ |
| Warhammer 40,000: Dark Heresy | #30 | 0.5–1.5m | 1–3 | FY28+ |
| Chaos Gate – Deathwatch (FDEV) | #379 | ≤0.7m (predecessor ≈ 730k) | 1–2 | undated |
| Boltgun Boom (mobile), AoS Deathmaster | — | — | <1 each | FY27 |

**Peak-year incremental royalty if TW:WH40K and DoW IV both land well: ≈ £10–22m over the £27m underlying
base — a licensing line of £37–49m, i.e. back to roughly the FY25 level already achieved and already faded.**

**Translate to price.** Licensing operating expenses are **£3.0m flat** → licensing operating margin **90.9%**,
so this really is near-100%-margin money.

- £15m incremental licensing revenue → £13.6m operating profit → £10.2m after 25.3% tax → **30.8p of EPS**
  (+4.9% on FY26's 624.0p).
- Capitalised at the trailing 30.6x as if it were an annuity: **+942p, +4.9% of the share price.**
- Capitalised honestly for a **1–2 year pulse** (the series in §2.2 proves it is a pulse) at 8–12x:
  **+250–370p, +1.3–1.9% of the share price.**

> **The seed thesis is directionally right and materially wrong. The franchise heat is genuine, GAW is the
> carrier, and the whole visible pipeline is worth ~1–5% of a 19,080p share. The market is not "paying nothing
> for the royalty optionality" — it is paying about the right amount, which is very little, because the
> optionality is small relative to a £6.3bn core business.**

**The one thing that could be material is Amazon — and it is nowhere near.** §4 below.

---

## 3. THE CORE ENGINE — Mode-A claim verification

### 3.1 Channel mix: all of the growth is trade sell-in

| £m, actual rates | FY26 | FY25 | Δ actual | Δ cc | % of core |
|---|---|---|---|---|---|
| **Trade** (independents) | **405.3** | 345.7 | **+17.2%** | +18.3% | **65%** (was 61%) |
| **Retail** (own 598 stores) | 131.4 | 128.7 | **+2.1%** | +3.0% | 21% (was 23%) |
| **Online** (own web) | 90.1 | 90.6 | **−0.6%** | +2.3% | 14% (was 16%) |

- Trade accounts: **9,100 vs 8,100 (+1,000, +12.3%)**; revenue per account £44.5k vs £42.7k (+4.3%).
- Stores: **598 vs 570 (+28 net; 42 opened, 14 closed)**; retail revenue +2.1% → **revenue per store ≈ −2.7%**.
- Regional trade: NA £170.9m (+13.5%), UK/Europe £180.4m (+17.9%), Asia £23.1m (**+38.3%**), ANZ £22.3m (+21.2%).
- Retail by region: UK **−0.5%**, NA **−1.5% actual** (+2.5% cc), ANZ **−6.1%**, Cont. Europe +12.3%, Asia +19%.

**Reading.** The two channels that measure genuine **sell-through** to the end hobbyist — own retail and own
online — are **flat to negative at actual rates while the store estate grew 4.9%.** All the growth is
**sell-in to independents**, now 65% of core and rising, and GAW guides FY27 to more of the same: *"we expect
the majority of our incremental growth to be through sales to independents."* GAW itself flags the fragility:
*"our success with our independents is not completely in our control… Most are reliant on a mix of other
product lines to maintain that viability e.g. collectible cards and board games."*

**Blue team (and I concede most of it):** independents sell online too, so trade legitimately cannibalises own
online; +1,000 accounts is real distribution expansion, not stuffing; per-account revenue *rose* 4.3%; and
**inventory provisions fell because "new releases [sold] in line with planned levels"** — the single datum that
most cleanly cuts against a channel-stuffing reading. **Verdict: WATCH, not FLAG.** The mix is real and it
lowers the *quality and visibility* of the growth; it does not evidence stuffing.

### 3.2 Margin, price, cost

- Core GM 69.5% → **71.1%**. Walk: COGS +1.6, inventory provision +0.3, warehousing +0.2, carriage +0.2,
  price rises +0.2, **tariffs −0.7**, packaging taxes −0.2.
- **RRP increases averaged 3% — "in line with normal levels."** No evidence of price being pushed to cover
  tariffs; the fan-relations risk the seed asks about is **not currently being taken**. (H1 noted ~3.5%.)
- Core opex +10.9% to £200.4m = **32.0% of core revenue, identical to FY25** — genuine operating discipline.
  Drivers: staff +£10.3m, new stores +£2.8m, SBC +£2.7m, software (SIP) +£1.4m, events +£1.4m, IP protection
  +£1.1m, Group Profit Share **−£2.4m** (cut to fund capex — a small quality demerit, it flatters opex).
- FY27 pay award **c.3%**; UK base pay £13.14/hr.

### 3.3 Manufacturing / capex — Nottingham, and it is expanding

- Owned capacity: **F1** (tool room, 40 injection-moulding machines), **F2** (17 machines + main packing),
  Easter Park (paint/innovation), **F4 owned, in fit-out** — moulding machines and a tool room install in FY27,
  packing in the meantime. *"We aim for Factory 4 to be operational in 2026."*
- Logistics: EMG (leased, Nottingham) → hubs Memphis + Sydney; **new Sawley warehouse leased**.
- FY26 capital additions **£32.6m** (production equipment/tooling £14.9m, site £13.5m incl. Factory 4 £9.9m,
  computer £2.0m, shop fits £2.2m) + **product development £17.0m**.
- **FY27 capex guided up a net c.£8.0m** (US Warhammer World + Sawley) — the only quantified FY27 guidance given.
- New US Warhammer World (near Washington DC) opening **summer 2027**, *"running slightly behind agreed milestones."*
- FY27 plan: **c.30 new stores** (NA, Cont. Europe, Asia).

### 3.4 Edition cycle — UNVERIFIABLE from primary

40K 10th edition and Age of Sigmar 4th are **not mentioned anywhere in the FY26 RNS**, and GAW does not disclose
edition roadmaps. A new 40K edition (11th) inside FY27 would be a genuine starter-box supercycle tailwind and is
the largest un-modelled upside to the core. **I cannot confirm or refute it from any primary source available in
this court. Listed as the top UNVERIFIABLE item.**

### 3.5 CEO succession — the seed premise is REFUTED

| claim | method | authority | finding |
|---|---|---|---|
| "the new-CEO transition (Rountree succession)" | read every Directorate Change RNS + the results signature block | RNS 9560453 (28-May-2026); FY26 results 28-Jul-2026 | **REFUTED.** No CEO change has been announced. **Kevin Rountree signed the FY26 results as CEO on 28-Jul-2026.** The only board change: **Neil Tomlinson promoted Group Operations Director → COO effective 31-May-2026** (gaining the design studios and the full Design-to-Manufacture team); **Max Bottrill** stepped off the PLC board, remaining with the company reporting to Tomlinson. |

What *is* true: succession is flagged as a live workstream — *"This structure is likely to evolve in 2026/27 as
we implement some changes to help succession planning which is a key area of focus"* and *"executive directors
and non-executive directors are also more active in developing orderly succession plans."* Read the COO
promotion as internal bench-building. **A Rountree departure announcement is an un-modelled event risk on a
name whose culture and capital discipline are substantially personified in him** — but it has not happened.

*(Also verified and immaterial: RNS 03-Aug-2026 "Disclosure of New Directorship" = NED Randal Casson joining
Future PLC's board. Not a GAW event.)*

---

## 4. AMAZON / MEDIA — status verified, economics UNVERIFIABLE by contract

Verbatim from the FY26 report (28-Jul-2026), which is the only authority:

> *"On 10 December 2024 we announced the conclusion of our negotiations with Amazon… This is a long-term
> partnership with Amazon - and these adaptations will take years to bring successfully to market. The project
> continues in line with our contractual agreement with Amazon. **This same contract prohibits us from sharing
> certain specific details or commercial terms.** What we can share is that Amazon has brought onboard United
> Artists (UA) and Mike Flannigan. Vertigo and Henry Cavill remain involved… **Having completed initial outlines,
> Mike should soon be moving on to script.**"*

Plus: a **Secret Level S2** Age of Sigmar episode nearly complete, and a **full animated Warhammer 40,000
Deathwatch series** (writer John Orloff, Blur animating, released through Amazon) — *begun*.

**Findings.**
1. **Stage: pre-script.** Twenty months from signature (Dec-2024) to *"should soon be moving on to script."*
   A live-action series is realistically **2029+**. Nothing lands inside any FV window this court prices.
2. **Economics: UNVERIFIABLE, and contractually so.** No fee, no minimum guarantee, no merchandising split, no
   term is disclosed and none can be. This is the single largest unpriceable item in the name — a genuine gap,
   **not a clean.** Any bull FV that leans on Amazon is leaning on an unobservable.
3. **Signal quality is real but weak:** United Artists + Mike Flanagan + Cavill retained is a serious creative
   package, and GAW volunteers that UA *"have been decisive."* That is qualitative, from an interested party.
4. **The disconfirming precedent, and it is GAW's own.** The last time a Hollywood adaptation drove this
   business was **The Lord of the Rings (2001–03)** — Games Workshop's LOTR miniatures line drove a revenue boom
   and then a severe multi-year bust as the films ended, taking the multiple and the share price with it. LOTR
   remains, per this very report, *"our only licensed property."* **A media-driven demand pulse is, in GAW's own
   corporate history, a boom-bust, not a step-change in the annuity.** *(Grade: PLAUSIBLE — widely documented,
   not re-verified against primary filings in this court. It is a mechanism to hold, not a number to underwrite.)*

---

## 5. TARIFF / ORIGIN LANE — the house's live competence, applied

GAW manufactures **100% in Nottingham** and ships into its largest market. US-derived core revenue:
NA trade £170.9m + NA retail £50.9m + NA online £29.9m = **£251.7m ≈ 40% of core revenue.**

**GAW's own disclosure, verbatim** (the only authority I will rest on):

> *"During the period we paid c.£12 million in new US tariffs. Following the US Supreme Court ruling we reclaimed
> £7.8 million of tariffs for the period to February 2026… of which £1.0 million was received during the period
> and £6.8 million following the period end. **Since February 2026 there have been further changes to US tariff
> legislation; our current estimate is that we will pay c.£13 million of new US tariffs in 2026/27.**"*

And from the GM walk: *"An application to recover **IEEPA reciprocal tariffs, introduced in April 2025**, was made
following the US Supreme Court judgment. This recovery has been recognised in full. Payments of **Section 122
tariffs, introduced in February 2026**, have been charged to core gross margin."*

| | FY26 | FY27E (GAW) |
|---|---|---|
| Gross new US tariffs | c.£12m | **c.£13m** |
| Reclaim recognised | +£7.8m (one-off, IEEPA/SCOTUS) | **£0** |
| **Net P&L cost** | **≈ £4.2m** | **≈ £13m** |
| Incremental drag FY27 vs FY26 | — | **≈ £8.8m pre-tax ≈ 27p EPS ≈ −4.3% of FY26 EPS** |
| GM impact | −0.7pp net | ≈ **−2.1pp** |

**The live lane finding — and it is the sharpest dated risk in this name.** GAW's £13m estimate was struck
**28-Jul-2026**. The Section 122 balance-of-payments authority carries a **statutory 150-day life** from its
February-2026 introduction and cannot be extended without Congress; the substitution regime moving in around
**01-Aug-2026** is a **different legal instrument on a different basis**. **GAW's own FY27 number therefore
predates the regime change by four days and may not incorporate it.** I could not verify the current effective
duty on UK-origin plastic miniatures (HS 9503/3926) from a primary source within this court's tool budget —
**WebSearch is exhausted session-wide and no primary CBP/Federal Register text was reachable. This is
UNVERIFIABLE, and UNVERIFIABLE is not clean.** It is written into the kill triggers as a dated, checkable item.

**Mitigants, honestly stated:** 71.1% core gross margin absorbs a lot; RRPs rise ~3%/yr with a 40%+ US revenue
base to price into; GAW refuses to exceptionalise tariffs (*"rather part of the uncertainty of operating
globally"*) which is exactly the disclosure posture that earns trust; and the reclaim proves the group actually
recovers when the law turns. **Tariff is a margin headwind, not a thesis-breaker. But it lands squarely on the
year in which the core is already decelerating.**

---

## 6. BALANCE SHEET, PENSION, COMMITMENTS (LSE addendum §2, §3)

**Pension — done by hand, as required.** The word *"pension"* appears **zero times** in the FY26 announcement,
and I read the full consolidated balance sheet line by line: non-current assets are intangibles, PP&E,
right-of-use assets, deferred tax assets and non-current receivables — **there is no retirement-benefit asset
and no retirement-benefit obligation on either side.** Provisions total £3.3m, of which "Employee benefits"
£2.8m (long-service/leave in scale, not a DB scheme). **Finding: no DB scheme, therefore no surplus inflating
equity and no deficit requiring an EV adjustment. No adjustment made.** *(The addendum's CHH/COST failure mode —
a hidden DB surplus — is CHECKED AND ABSENT. P/B is irrelevant to this tier-1 frame regardless.)*

**Commitments — note 12 read in full (the THX lesson).** Capital expenditure contracted but not incurred
**£9.5m** (FY25 £5.3m); inventory purchase commitments **£10.7m** (£12.2m); lease commitments where the group has
an obligation but not yet control **£28.4m** (FY25: <£0.1m — this is the new US Warhammer World). **Total
£48.6m** against £182.9m cash and £267.7m operating cash flow. **Immaterial to any FCF claim. FCF yield stands.**

**Capital structure — pulled before any EV claim.**

| item | £m |
|---|---|
| Cash | 182.9 |
| External borrowings | **nil** (*"The Group pays for its operations entirely from its free cash flow"*) |
| Lease liabilities (current + non-current) | 56.0 |
| Net assets | 335.3 |
| **EV** = 6,305.0 − 182.9 + 56.0 | **6,178.1** |

No warrants, no preferred, no converts. Dilution is a **sharesave scheme only**: 80k share-option adjustment on
33.0m shares (**0.24%**), £4.5m issued in the period. SBC £4.0m (1.5% of operating profit) — trivially honest.

**Cash flow:** operating £267.7m − capex £32.4m − product development £17.0m − lease payments £15.0m = **FCF
£203.3m → 3.29% on EV.** Net cash rose £50.3m *after* £160.1m of dividends.

---

## 7. VALUATION — the multiple-vs-own-history gate (the WMT lesson)

**7-year trailing-P/E band, built from month-end prices (yfinance GAW.L, unadjusted) × the basic EPS actually
reported at each annual print (all eight EPS figures RNS-verified: FY19 202.9p · FY20 218.7p · FY21 372.7p ·
FY22 391.3p · FY23 409.7p · FY24 458.8p · FY25 594.9p · FY26 624.0p), n = 85 monthly observations:**

| statistic | trailing P/E |
|---|---|
| min (Aug-2022 trough) | 14.8x |
| 10th pct | 20.3x |
| **25th pct** | **24.1x** |
| **median** | **27.6x** |
| **75th pct** | **32.8x** |
| 90th pct | 45.3x |
| max (2021 hobby-boom peak) | 54.6x |
| **SPOT (19,080p ÷ 624.0p)** | **30.58x — 64th percentile** |

Annual means: 2019 25.0 · 2020 39.1 · 2021 40.1 · **2022 19.1** · 2023 25.5 · 2024 25.3 · 2025 31.1 · 2026 31.7.
*(A true 10-year band is not constructible on verified inputs: pre-2019 GAW traded at 8–15x as a fundamentally
different, pre-re-rating business, and I did not verify FY17/FY18 EPS. The 7-year band spans the entire modern
franchise era including both the 2021 peak and the 2022 trough — it is the fair comparator, and I state the
limitation rather than manufacture a 10-year number.)*

**Other multiples at spot:**

| metric | value |
|---|---|
| EV / total EBIT (FY26 £275.0m) | **22.5x** |
| EV / **core** EBIT (£245.1m) | **25.2x** |
| **P/E on core-only EPS** (556.2p — strip licensing, tax at 25.3%) | **34.3x** |
| FCF yield on EV | 3.29% |
| Dividend yield, FY26 declared 485p | **2.54%** (IBKR div yield 2.55% — cross-checked) |
| Dividend yield, run-rate ~575–600p | **≈3.0%** |

**Core-only EPS series** (the cleaner read, since licensing is a sawtooth): FY24 ≈406.6p → FY25 ≈482.7p →
FY26 ≈556.2p, **+15.2% in FY26**. So GAW trades at **34.3x for a ~15% core grower — a PEG of ~2.2 — with the
core's own H2 exit rate at roughly flat.**

> **GATE RESULT: FAIL.** The WMT gate requires today's multiple to sit meaningfully below its own history before
> a TINA claim is admissible. **30.6x is the 64th percentile of GAW's own 7-year band** — above median, not
> below. **TINA does not apply here.** TINA says *for durable quality, fair value IS the entry* — it does not say
> an upper-quartile-leaning multiple is fair value, and it explicitly does not license paying above the median
> multiple for a year in which EPS growth exits at −0.6%.

**Dividend / the 0% WHT holding edge (addendum §5).** FY26 declared 485p (FY25 520p) — the decline is a
**timing deferral, not a cut**: the board deferred April declarations that would straddle the year end, in both
FY25 and FY26. The forward signal is **better than the trailing**: dividends declared so far in FY27 total
**£2.30/share vs £1.40 at the same point last year (+64%)** — 90p (17-Jun) + 140p (28-Jul, ex-27-Aug, pay
05-Oct). Policy is *"truly surplus cash"* after a **£120m cash buffer** (raised from £100m), planned >£1m capital
purchases and Group Profit Share. FY26 net cash generation pre-dividends was £210.3m against £160.1m paid.
**A ~3.0% run-rate yield received with zero UK withholding is a real holding-period edge — but per addendum §5 it
cannot be used to justify an entry, only to grade the carry once the price gate is passed. It is not passed.**

**Friction (addendum §5).** Buy-side **stamp duty 0.5%** (Main Market) + touch (~10–20bp, DATA-GATED) +
commission ≈ **0.65–0.75% all-in on entry**. Against a ~3.0% net yield that is roughly one quarter of carry —
fine for a multi-year hold, prohibitive for anything tactical.

---

## 8. PATH CHECK (contract §4)

| | |
|---|---|
| 52w high | **22,260p** (25-Jun-2026 intraday, ~6 weeks ago) |
| 52w low | **13,794.5p** (Oct-2025, **~9–10 months ago**) |
| Spot vs high | **−14.3%** |
| Spot vs low | **+38.3%** |
| FY26 range travelled | Oct-25 ~14,070 → Jun-26 22,260 = **+58%**, then −14% |

**Ruling: LATE.** A +38% advance off a low that is nine to ten months old, with the stock still only 14% below
an all-time high set six weeks ago, is **not a drawdown court** — exactly as the seed's frame-inversion note
anticipated. There is no de-rate here to buy.

**And note what the June spike was.** The stock jumped **+6.5% on 24-Jun-2026** (203.4 → 216.6 on 51,925 shares,
~4× normal primary-venue volume) and ran to 222.6 the next day — during the same window in which the new
Warhammer game slate (including Total War: WARHAMMER 40,000) was being announced. **The market already marked
the royalty-pipeline news up, and has since given all of it back and more.** The seed evidence is not
un-priced; it was priced in June and then de-priced through July on the actual licensing print.

---

## 9. DE-RATE vs DERAILMENT (contract §3)

**Neither — and that is the ruling.** The winner pattern (HUBS/CTSH/SAP) is *multiple compressed on stable or
rising estimates*. GAW is the inverse: **the multiple never compressed** (64th percentile of its own band, 2026
mean 31.7x vs the 7-year 27.6x median) **while the near-term earnings line is the thing that decelerated**
(H1 core OP +28.5% → H2 +4.7%, or ≈−2.2% ex the one-off tariff reclaim; H2 EPS −0.6%).

**Classify as: FULL-MULTIPLE QUALITY, DECELERATING NEAR-TERM — the anti-pattern.** There is no derailment: the
business is not deteriorating, ROCE is 196%, cash is compounding, distribution is expanding. There is simply no
discount, and there is a visible air pocket in FY27.

---

## 10. SCENARIOS · FV · MARKET-IMPLIED

**FY27E build (base).** Core revenue +8% to £677m (trade-led, +1,000 accounts annualising, ~30 new stores,
Asia +38% base effect, 3% RRP). Core GM 71.1% − ~1.3pp incremental tariff → ~69.8%. Core opex +9% to £218m
(3% pay, 30 stores, SIP). Core operating profit ≈ **£254.5m (+3.8%)**. Licensing ≈ £30m revenue / £27m operating
profit (no dated major title; underlying base £27m; small titles only). PBT ≈ **£283m**, tax 25.3%, **EPS ≈ 640p
(+2.5%)**. *The core's own growth is very largely consumed by the £8.8m incremental tariff.*

| scenario | p | thesis | FY27–28E EPS | exit P/E | **FV (GBp)** | vs spot |
|---|---|---|---|---|---|---|
| **BEAR** | **0.25** | Trade sell-in normalises as independents digest +1,000 accounts; own retail/online stay negative; tariff runs above £13m post-01-Aug substitution; licensing stuck at ~£27m with no significant deal signed; post-10th-edition hobby fatigue. FY27 EPS £590–600p. | ~595p | **24.1x** (own-band p25) | **14,500** | **−24%** |
| **BASE** | **0.50** | Core compounds high-single-digit, trade-led; margin roughly flat as tariff offsets efficiency; licensing ~£30m FY27 then ~£38m FY28 as TW:WH40K lands late; Amazon still pre-production; multiple drifts toward — but stays above — the own-band median on quality. | 640p (FY27) | **29.0x** | **18,600** | **−2.5%** |
| **BULL** | **0.25** | New 40K edition supercycle inside FY27 + Asia inflects + trade accounts >10,000 → core +12%; TW:WH40K **and** Dawn of War IV both dated and land, licensing >£50m in FY28; Amazon gets a dated production start and a merchandising flywheel begins. FY28 EPS ~800p. | ~800p (FY28) | **32.0x** | **25,500** | **+34%** |

**E[FV] = 0.25(14,500) + 0.50(18,600) + 0.25(25,500) = 19,300p.**
**Spot 19,080p → edge = +220p = +1.2%.**

**Market-implied probability.** Holding p_bear at 0.25 and solving the same three-point grid for the spot:
17,575 + 6,900·p_bull = 19,080 → **market-implied p_bull ≈ 21.8% vs our 25%.**

> **Edge = +3.2pp of bull probability, or +1.2% of price. That is inside the noise of a three-point grid and far
> below any actionable bar. GAW is FAIRLY PRICED. The bull case is neither free nor mispriced — it is
> approximately correctly priced at a small number, because it is a small number.**

---

## 11. FOUR-IDEA FRAME

| idea | grade |
|---|---|
| **1. Is the franchise heat real?** | **YES — CONFIRMED.** TW:WH40K #7, DoW IV #17, Dark Heresy #30 of 5,204 unreleased Steam titles. The strongest franchise signal on the chart. Not in dispute. |
| **2. Is GAW the carrier?** | **YES — CONFIRMED.** GAW collects on every one regardless of studio; licensing opex is £3.0m flat against £32.9m of revenue → **90.9% operating margin**. Near-100%-margin royalty is real. |
| **3. Is the carry material?** | **NO — REFUTED, and this is the court.** The whole visible pipeline is worth **£10–22m of peak-year revenue ≈ 1–5% of the share price**, against a licensing series that has already printed £52.5m once and faded. Every forward-contracted metric is down 30–77%. Nothing is dated inside FY27. |
| **4. Is it priced?** | **YES — and slightly rich.** 30.6x = **64th percentile of its own 7-year band**; 34.3x on core-only EPS; +38% off a 9-month-old low. Market-implied p_bull 21.8% vs our 25%. Edge +1.2%. |

---

## 12. EVIDENCE TABLE (contract hard rule)

| # | claim | tool / source | result | grade |
|---|---|---|---|---|
| 1 | Spot 19,080 GBp = £190.80, both planes | IBKR snapshot + daily bars, conid 35151400 | agree; tick 2026-08-04 15:29 UTC, live | **CONFIRMED** |
| 2 | FY26 printed 28-Jul-2026; rev £659.7m, EPS 624.0p | RNS 9689924, full text pulled and parsed locally | as stated | **CONFIRMED** |
| 3 | Licensing revenue fell £52.5m → £32.9m (−37%) | same RNS, highlights + financial review | as stated | **CONFIRMED** |
| 4 | £5.9m of FY26 licensing is termination money from 2 exiting licensees | same RNS, CEO review + receivables note | underlying ≈ £27.0m | **CONFIRMED** |
| 5 | Fixed licensing income signed £11.1m → £2.5m (−77%) | same RNS, revenue note | as stated | **CONFIRMED** |
| 6 | 12-month licensing receivables £16.4m → £11.5m (−30%) | same RNS | as stated | **CONFIRMED** |
| 7 | Licensing series FY19–FY26 | RNS 6081740 / 6744294 / 7136158 / 7652313 / 8337097 / 9689924 | 11.3→16.8→16.3→28.0→25.4→31.0→52.5→32.9 | **CONFIRMED** |
| 8 | EPS series FY19–FY26 (band inputs) | same five annual RNS | 202.9 / 218.7 / 372.7 / 391.3 / 409.7 / 458.8 / 594.9 / 624.0 | **CONFIRMED** |
| 9 | **H2 FY26 EPS 304.1p vs 306.0p (−0.6%); H2 core OP +4.7%** | FY26 RNS − H1 RNS 9349031 | arithmetic | **CONFIRMED** |
| 10 | **H2 core OP ex-£7.8m tariff reclaim ≈ −2.2% YoY** | H1 reported £6.0m tariff cost with no reclaim; SCOTUS reclaim necessarily post-H1 | half-attribution is inference, not disclosed | **PLAUSIBLE (high conf.)** |
| 11 | FY27 tariff estimate c.£13m, no reclaim → ≈£8.8m incremental | FY26 RNS, CEO "Tariffs" section | as stated | **CONFIRMED** |
| 12 | GAW's £13m predates the ~01-Aug regime substitution | RNS dated 28-Jul-2026 | date arithmetic | **CONFIRMED (date); risk UNVERIFIABLE)** |
| 13 | Current effective US duty on UK-origin HS 9503/3926 | WebSearch exhausted; no primary CBP/Fed-Reg text reachable | **could not verify** | **UNVERIFIABLE** |
| 14 | Trade +17.2% / Retail +2.1% / Online −0.6%; 65/21/14 mix | FY26 RNS channel tables | as stated | **CONFIRMED** |
| 15 | 598 stores (+28 net); 9,100 trade accounts (+1,000) | FY26 RNS store table + business description | as stated | **CONFIRMED** |
| 16 | No CEO change; Rountree signed 28-Jul-2026; Tomlinson → COO 31-May-2026 | RNS 9560453 + results signature | seed premise wrong | **REFUTED (seed claim)** |
| 17 | Amazon at outline→script stage; terms contractually undisclosable | FY26 RNS, Media section, verbatim | as stated | **CONFIRMED (status) / UNVERIFIABLE (economics)** |
| 18 | Shares 33,044,841, nil treasury | RNS Total Voting Rights 03-Aug-2026 | as stated | **CONFIRMED** |
| 19 | No DB pension: zero "pension" mentions, no retirement-benefit line either side of the BS | FY26 RNS balance sheet + provisions note 11, read line by line | no adjustment needed | **CONFIRMED** |
| 20 | Commitments £9.5m capex + £10.7m inventory + £28.4m leases = £48.6m | FY26 RNS note 12 | immaterial vs £182.9m cash / £267.7m op CF | **CONFIRMED** |
| 21 | Zero external borrowings; only dilution is sharesave (0.24%) | FY26 RNS treasury note + EPS note 5 | net cash £182.9m; EV £6,178m | **CONFIRMED** |
| 22 | Spot P/E 30.58x = 64th pct of 7y band (median 27.6x) | 85 month-ends × RNS-verified EPS | computed | **CONFIRMED** |
| 23 | FY27 dividends declared to date £2.30 vs £1.40 (+64%) | RNS 9690132 (28-Jul) + 9621830 (17-Jun) | as stated | **CONFIRMED** |
| 24 | Not in an offer period | `LSE_OFFER_PERIODS.json` — no GAW / Games Workshop entry | clean | **CONFIRMED** |
| 25 | No prior art / no frozen call to respect | grep `research_ledger.json`, `resolution_packs.json` | zero hits | **CONFIRMED** |
| 26 | 40K 11th edition / AoS edition timing | not disclosed in any GAW RNS; no primary route | **could not verify** | **UNVERIFIABLE** |
| 27 | LOTR 2002–04 boom-bust precedent | GAW corporate history; not re-verified to filings here | mechanism only | **PLAUSIBLE** |
| 28 | Warhammer pipeline unit/royalty scenarios | FDEV_TELEMETRY ~50-units-per-review calibration + FY24→FY25 £21.5m step | derived | **DERIVED (stated as such)** |

**Consolidated UNVERIFIABLE list (per contract — these are gaps, not cleans):** (a) **Amazon economics** — the
largest unpriceable item, and contractually unobtainable; (b) **the current US duty rate on UK-origin miniatures
post-01-Aug**, which puts GAW's own £13m FY27 estimate at risk; (c) **edition-cycle timing**, the biggest
un-modelled core upside; (d) **live LSE touch** (market data returned an empty bid/ask).

---

## 13. VERDICT · SIZING · TRIGGERS

### REJECT — 3/10. No position.

**Why not 4+:** it fails the multiple gate (64th percentile of its own band, not below it), the path gate
(+38% off a 9-month-old low), and the estimate gate (H2 EPS −0.6%; core OP ≈−2.2% ex one-off; FY27 carries
£8.8m of incremental tariff with no dated licensing catalyst). Edge is +1.2% of price / +3.2pp of probability —
noise. **The seed thesis' load-bearing leg quantifies to 1–5% of market cap and was already marked up and
un-marked between 24-Jun and 28-Jul.**

**Why not lower:** this is a **high-quality reject, not an avoid.** 196% core ROCE, zero debt, 71.1% gross
margin, 32.0%-of-revenue opex held flat to the basis point, £182.9m net cash built *after* £160.1m of dividends,
best-in-class honesty (tariffs refused as an exceptional; the licensing decline volunteered by the CEO in his
own words), price-inelastic collectible IP, and a genuinely free — if small — royalty/media option. **This is a
name to own on a real de-rate. There simply isn't one today.** Per the response taxonomy, a valuation finding
gets a **price gate** — which is the only case where a gate is the right instrument.

**Sizing (if the gate ever clears):** vs the $3.3M deployable base, the UK cap is **0.75% ≈ $24,750**.
Liquidity is emphatically not the binding constraint — $13.28m ADV means a full position is **0.19% of one
day's volume**, and LSE execution is proven live (BRBY, TW.). The 0.75% addendum cap is calibrated for the thin
shelf; GAW is FTSE-100 and would justify the upper half of any ruled range on liquidity grounds alone.
**Not sized today.**

**Consumer-discretionary overlap (positions polled live, 2026-08-04):** held — **ONON** $15.9k, **BRBY**
£11.4k (≈$15.3k), **BKE** $4.3k, **OLLI** $2.8k ≈ **$48.3k / 1.5% of $3.3M**. GAW would be a fifth, on a
**genuinely different sub-axis**: collectible-hobby IP with a 71% gross margin, an owned manufacturing base and
no fashion-cycle or markdown risk — versus athletic footwear (ONON), luxury turnaround (BRBY), US value apparel
(BKE) and closeout trade-down (OLLI). The nearest neighbour is BRBY (UK-listed, brand/IP, discretionary) but
they sit at opposite ends of the same street: BRBY is a turnaround on a depressed multiple, GAW a compounder on
a full one. **Overlap noted, not binding.**

**Not AI-complex.** No AI-capex exposure; the frozen AI-BREAK|2027-12-31 @0.45 call is not engaged, and the
entry does not require the cycle holding either way.

### Price gate — the only instrument this finding earns

| level | basis | action |
|---|---|---|
| **≤ 17,500p** (−8.3%) | own-band **median 27.6x** on FY27E ~640p | **RE-LOOK** — re-run the court with H1 FY27 in hand |
| **≤ 15,500p** (−18.8%) | own-band **p25 24.1x** on FY27E | **BUY ZONE** — a genuine own-history discount on an elite compounder. *Reachable without a disaster: GAW traded 14,500–15,500p as recently as Aug–Oct 2025.* |
| ≥ 22,300p | new high on an un-dated pipeline | do nothing; the gate is a floor, not a chase |

### Dated kill / re-look triggers

| # | trigger | date | meaning |
|---|---|---|---|
| 1 | **H1 FY27 licensing revenue < £22.0m** (H1 FY26: £16.0m) | H1 report, **~mid-Jan-2027** | the freezable call — confirms the royalty inflection is not inside FY27 |
| 2 | **H1 FY27 core revenue growth < 6% cc** (H1 FY26: +17.3%) | ~mid-Jan-2027 | the H2-FY26 deceleration is the new run-rate, not a stumble |
| 3 | **FY27 tariff estimate restated above £18m** | any RNS / H1 report | GAW's 28-Jul £13m did not capture the ~01-Aug substitution; a further ~−2% EPS |
| 4 | **Trade accounts fall below 9,100 or trade growth turns negative while retail/online stay flat** | H1 FY27 | the sell-in unwind — the §3.1 WATCH converting to a FLAG |
| 5 | **Rountree departure announced** | any RNS | un-modelled culture/capital-discipline risk; re-court immediately |
| 6 | **Total War: WARHAMMER 40,000 gets a dated release inside FY28** | any time | **upgrade trigger** — moves licensing from bear/base toward bull |
| 7 | **Amazon 40K live-action gets a dated production start or first-look** | any time | the only event that can make the media leg material; re-court |

### ONE FREEZABLE CALL

> **`GAW.L | 2027-01-31` — H1 FY27 (26 weeks to ~29-Nov-2026) licensing revenue will print BELOW £22.0m.
> our_p = 0.75.**

**Bar and reasoning.** H1 FY26 licensing was £16.0m; underlying FY26 ex-terminations ≈ £27.0m. Clearing £22.0m
would require +37% on the comparable half. Nothing in the Jun–Nov-2026 window is dated: TW:WH40K, Dawn of War IV,
Dark Heresy and Chaos Gate–Deathwatch are all undated as of 04-Aug-2026; only mobile/small titles are plausible;
and the forward book is £11.5m of 12-month receivables with £2.5m of new fixed income signed all year.
**The residual 25% is honest: a single large signing minimum-guarantee is lumpy and recognised up front — which
is precisely the event that would falsify this court's central finding, and precisely why this is the right bar.**

---

## 14. WHAT WOULD MAKE ME WRONG

1. **A 40K 11th edition inside FY27.** Not disclosed anywhere, unverifiable here, and historically the single
   biggest core-revenue tailwind GAW has. It would take FY27 core growth to low-double-digits and make the
   base scenario look conservative. **This is the top UNVERIFIABLE item and it cuts bullish.**
2. **A significant licensing signing.** GAW says its FY27 priority is *"to sign a few significant licensing
   deals."* Minimum guarantees are recognised on signing — one deal falsifies the freezable call and reprices
   the leg overnight.
3. **Amazon terms leaking better than assumed.** Unknowable by construction. If the 40K deal carries a large
   annual licence fee plus a merchandising participation, the media leg stops being a rounding error.
4. **The trade channel is real distribution, not inventory.** If per-account revenue keeps compounding at 4%+
   on a 10,000-account base, my §3.1 WATCH is simply wrong and core growth is higher-quality than I graded it.
5. **The tariff resolves favourably.** GAW recovered £7.8m once already. A UK-origin carve-out would hand back
   ~27p of EPS and most of my FY27 deceleration.

*No shared stores written. `research_ledger.json`, `resolution_packs.json`, calibration ledger and entry_plan
untouched, per contract §3.*
