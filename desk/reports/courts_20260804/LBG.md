# LBG — LBG Media plc (AIM: LBG, "LADbible Group") — LSE shelf court, 2026-08-04

**Verdict: 1/10 REJECT.** The screen row is not corrupt — it is *arithmetically exact* against the
filings. It is the **definition** that is wrong, and the corrected number is a different stock: 7.9x
statutory EV/EBIT (not 3.9x), 1.48x tangible book (not 0.86x book), and the net cash was spent in June.

---

## 1. Identity resolution

| Item | Source | Result |
|---|---|---|
| Shelf row | LSE_SHELF TIDM `LBG`, ISIN GB00BKPH9R58, AIM, `lse_segment` AMSM | LBG MEDIA PLC |
| Legal entity | Companies House search → **company number 13693251**, LBG MEDIA PLC | Resolved |
| Business | LADbible / UNILAD / SPORTbible / Betches (US) — social entertainment publisher, young-adult audience ~0.5bn | — |
| **Year end** | Companies House filing history: accounts "made up to **30 September** 2025" | **FYE is 30 SEPTEMBER, not December** — see defect 5 |
| Offer period | LSE_OFFER_PERIODS.json — no LBG entry | Not a special situation |
| Prior art | grep research_ledger.json + resolution_packs.json | **None** |

**Name-collision warning for the generator:** "LBG" is also the common market shorthand for **Lloyds
Banking Group** (LSE TIDM `LLOY`). The row is correctly LBG Media, confirmed three ways (ISIN
GB00BKPH9R58, AIM segment AMSM, and 209,079,740 shares matching the interim balance sheet). Flagged
because any future free-text or news join on "LBG" will pull a FTSE-100 bank into a £71m AIM microcap.

---

## 2. Tape verification — in pence, both units stated

| Item | Source | Result |
|---|---|---|
| Price | yfinance LBG.L, `currency = GBp`, 2026-08-04 close | **34.0p = £0.34** |
| Shares | interim balance sheet + yfinance | 209,079,740 |
| Market cap | 34.0p × 209,079,740 | **£71.09m** (~$95.6m) — matches shelf `mktcap` exactly |
| 52w high | 105.0p, 2025-10-06 | **−67.6% from the high** |
| 52w low | intraday 20.67p 2026-06-09; **close basis 25.0p** same day | — |
| Path | 34.0/25.0 close basis | **+36.0% off a 56-day low** |
| Touch | shelf bid 33 / offer 34 → 1p on 34 = **299bp round-trip**; half-touch ~150bp | AIM ⇒ stamp 0%, but 299bp is 6x the stamp exemption it saves |
| Liquidity | `adv_usd` 99,731 (median of 63 sessions); `max_order_usd` $19,946 | Thin |
| Float | `float_pct` **0.302** — 30.2%, $28.9m | ~70% closely held (founder/management) |
| **IBKR line** | shelf `conid: null`, `ibkr_symbol: null`, `ibkr_verified_utc: null`. `search_contracts("LBG Media")` → **zero results** | **EXECUTABILITY: DATA-GATED — unverified** |

**Path ruling (contract §4):** +36% off a **56-day** low is inside the 90-day window and over the 35%
threshold. This is a **late bounce**. The shelf's own `entry_exhausted: true` flag fired correctly and
should have stopped the row before it reached a court.

---

## 3. Cause-check — the drawdown is fully explained and it is structural

| Date | Move | Event (primary: RNS via investegate) |
|---|---|---|
| 2026-02-03 | — | **FY2025 results** (12m to 30-Sep-25): revenue £92.2m (+7% statutory), adj EBITDA £25.2m (+3%), PBT £14.0m (−3%), cash £30.8m. Headline: *"Double-digit revenue growth"*; bullet: *"**Stabilisation of Indirect revenues**"* |
| 2026-02-04 | — | **"Full year results — Correction"**: expectation for Direct margins before central costs **corrected down** to "the mid-20% range" |
| 2026-03-03 | −12.8% | — |
| 2026-04-22 | **−16.0%** | **Half-year trading update**: revenue guidance **raised to £110m**, adj EBITDA guidance **cut to £22m** |
| 2026-06-09 | **−28.6%** | **H1-2026 results** (6m to 31-Mar-26) + second guidance cut in seven weeks |
| 2026-06-09 | — | **Companies House: fixed charge registered, HSBC UK Bank plc as Security Agent** (code 1369 3251 0001, outstanding) — the **first charge in the company's history** |
| 2026-06-19 | — | **Acquisition of 75% of Uncovered Holdings** for **£26.8m initial cash** |
| 2026-07-25 | — | **AMENDED** group accounts for the year to 30-Sep-2025 filed, superseding the originals filed 15-Mar-2026 |

### The cause, in the company's own words (RNS 09-Jun-2026, verbatim)

> "Indirect revenues declined 41% to £14.5m (1H25: £24.5m)… due to previously announced changes to
> **Meta's Facebook algorithm** in line with trends outlined in 2H25, which remain challenging, as
> well as **lower traffic from search engines due to AI Overviews**."

> "The revised guidance reflects an anticipated further decline in Web and Social revenues… which has
> reduced visibility as part of a **long-term structural shift** away from websites towards social
> platforms and video content."

> "…the **low end of the EBITDA range cited above reflects a continuation of the current monthly
> trend**."

This is not a cycle. Meta's feed ranking and Google's AI Overviews are product decisions by two
platforms LBG does not control and cannot negotiate with, and 28% of group revenue still depends on
them. Management says "structural" itself.

---

## 4. The screen defect — reconciled line by line to the filings

The dead agent's last transmission was *"LBG's screen defect now reconciles exactly to the filings."*
It does. **It is neither a securities-as-cash misclassification nor a unit error.** Every
balance-sheet input in the row ties to the pence against the unaudited consolidated statement of
financial position as at 31-Mar-2026 in the 09-Jun-2026 RNS:

| Shelf field | Shelf value | Filed value @31-Mar-2026 | Tie |
|---|---|---|---|
| `cash` / `cash_strict` | 28,438 | Cash and cash equivalents **28,438** | **EXACT** |
| `eq` | 82,701 | Total equity **82,701** | **EXACT** |
| `lease_debt` | 14,302 | Non-current lease liability 13,561 + current 741 = **14,302** | **EXACT** |
| `debt` | 14,713.75 | leases 14,302 + provisions 549 × (1 − 0.25 tax) = **14,713.75** | **EXACT** |
| `pension_gross` | 549 | Provisions **549** (correctly self-labelled `long_term_provisions_proxy`) | **EXACT** |
| `rev` | 100,644 | LTM: FY25 92,225 + 1H26 52,400 − 1H25 43,900 = 100,725 (interim highlights rounded to £0.1m) | **ties to 0.08%** |
| `ebit_reported` | 7,283 | LTM statutory operating profit: FY25 **13,684** + 1H26 **1,965** − 1H25 **8,366** = **7,283** | **EXACT** |

The row is clean. The **definitions** are not. Six defects, in order of how much damage each does:

### DEFECT-1 — the 3.9x is an adjusted-vs-statutory EBIT swap. **THE HEADLINE IS 2.04x TOO CHEAP.**

`am` = 3.863 is computed as `ev / ebit`, where `ebit` = **14,849** is the vendor's **LTM ADJUSTED
operating profit** (before exceptionals, acquisition-related costs and amortisation of acquired
intangibles). The **statutory** LTM figure — **7,283** — is sitting in the *same row* under
`ebit_reported`, unused.

> **Honest multiple: `ev` 57,362,862 / `ebit_reported` 7,283,000 = 7.88x, not 3.86x.**

The row already carries the tell: **`unusual_r: −0.465`**. It is populated, it is large, and nothing
gates on it.

**FIX:** rank `am` on `ebit_reported`. If an adjusted figure must be used, hard-gate any row where
`|unusual_r| > 0.20` into a review queue. Print both multiples in the shelf row so no downstream reader
can quote the cheap one without seeing the other.

### DEFECT-2 — "below book" is above **tangible** book, and the tangible residue is an IFRS-16 gross-up

`pb` 0.8596 is arithmetically correct. It is also economically empty:

| | £'000 |
|---|---|
| Total equity @31-Mar-26 | 82,701 |
| Less goodwill and other intangible assets | (34,720) |
| **Tangible book** | **47,981** |
| **P/TBV at £71.09m market cap** | **1.48x — ABOVE tangible book** |

Worse, PP&E leapt **3,059 → 17,789** in six months. The interim narrative gives the reason verbatim:
*"recognition of the right-of-use asset for the new London office lease and the capitalisation of
associated fit-out costs. This was matched on the liability side by a corresponding increase in
non-current lease liabilities to £13.6m."* So **the same office lease inflates the asset side of book
equity and supplies 97% of the `debt` the screen subtracts**. The screen books the liability and lets
the matching asset flatter the book — it double-counts the lease against itself.

**FIX:** carry `ptbv` beside `pb` and rank on it for asset-light media/services. Net the ROU asset
against the lease liability, or count neither.

### DEFECT-3 — contingent consideration is invisible to `netcash`

The 31-Mar-26 balance sheet carries **£8,615k of CURRENT contingent consideration** (Betches earnout;
was 5,710 non-current + current at 30-Sep-25). It is a dated cash claim and it is excluded from both
`debt` and `netcash`.

| | £'000 |
|---|---|
| Cash | 28,438 |
| Less lease liabilities | (14,302) |
| **Less contingent consideration** | **(8,615)** |
| **True net cash** | **5,521** |
| `ncash_r` truth vs shelf | **7.8% vs 19.3% — overstated 2.49x** |

**FIX:** add contingent consideration, put-option liabilities over NCI, and deferred consideration to
the debt-like stack.

### DEFECT-4 — `fy_stale: false` on a semi-annual UK reporter with three superseding post-period events

The row is struck at 31-Mar-2026. As of 2026-08-04, three separate filings have superseded it:

1. **09-Jun-2026 — HSBC UK Bank plc fixed charge** (Companies House charge code 1369 3251 0001,
   delivered 12-Jun-2026, status Outstanding, 52 pages). The **first charge ever registered** against
   company 13693251. The "no borrowings" premise underneath `netcash` died on that date.
2. **19-Jun-2026 — acquisition of 75% of Uncovered Holdings Limited.** Verbatim from the RNS: *"initial
   cash consideration of £26.8 million… with an earnout cash payment of up to £7.0 million… funded
   through a combination of LBG Media's existing cash resources and a **new £50.0 million debt
   facility**."* Plus put-and-call options over the remaining 25% at **"an agreed nine times multiple
   of respective adjusted EBITDA in each of the calendar years 2028, 2029 and 2030… payable in cash."*
   £26.8m against £28.4m of cash: **the entire net-cash position was consumed nine weeks before this
   court**, and an uncapped 9x-EBITDA cash put was added.
3. **25-Jul-2026 — AMENDED group accounts** for the year to 30-Sep-2025 (AAMD, 136 pages), superseding
   the originals filed 15-Mar-2026. Combined with the 04-Feb-2026 *"Full year results — Correction"*
   RNS, **the same financial year has now been corrected twice.**

**FIX (highest value, cheapest to build):** a Companies House pre-flight for every UK row — pull
`/company/<n>/charges` and `/company/<n>/filing-history`, and hard-fail `fy_stale:false` on (a) any
charge created after the balance-sheet date, (b) any AAMD/amended-accounts filing, (c) any RNS matching
acquisition/disposal/placing since the period end. All three are free and unauthenticated.

### DEFECT-5 — `ebit_hist` is a non-contiguous series with a silent hole

`ebit_hist: [18671, 9948, 10591, 13737]` maps to FY2025 (12m to **30-Sep-25**), FY2023 (12m to
**31-Dec-23**), FY2022, FY2021. **LBG changed its year end from 31 December to 30 September**, and the
resulting **9-month transition period to 30-Sep-2024 is silently dropped from the series.** The screen
therefore compares a 12-month figure to a series with a gap and a period-length change in the middle.
`ebit_trend: 1.08`, `ebit_vs_peak: 0.80` and, critically, **`melting: false`** are all unearned.

A name whose adjusted EBITDA guidance was cut from ~£25m to **£15-20m** in seven weeks is precisely
what `melting` exists to catch, and the flag reads `false`.

**FIX:** read the `made up to` dates from Companies House filing history; refuse all trend and
peak-ratio metrics across a period-length change or a missing year.

### DEFECT-6 — cross-cutting: `yfinance fast_info.market_cap` is 100x wrong on GBp lines

`fast_info.market_cap` returns **7,108,711,194** for LBG (and 4,234,166,475 for CHH) — pence × shares.
The correct figures are £71,087,112 and £42,341,664. `.info['marketCap']` is right and the shelf used
it. A live priceMagnifier trap for anything downstream that reaches for `fast_info`.

---

## 5. Mode B — the questions the release framing hid

### B-1. The 1H26 headline is a revenue-level APM, and it is the second consecutive one

The 09-Jun-2026 release leads with **"Acceleration of revenue growth"** and a financial-highlights
table whose first line is **"Adjusted Group Revenue 53.6, +22%"** — above the statutory **"Total Group
Revenue 52.4, +19%."** An *adjusted revenue* APM is unusual; revenue is the least adjustable line in a
P&L. Underneath the headline, on the same page:

| 1H26 vs 1H25 | | |
|---|---|---|
| Adjusted Group Revenue (APM) | 53.6 vs 43.9 | **+22%** ← the headline |
| Total Group Revenue (statutory) | 52.4 vs 43.9 | +19% |
| Adjusted EBITDA | 8.0 vs 12.2 | **−34%** |
| Adjusted EBITDA margin | 15.4% vs 27.8% | **−12.4 ppts** |
| **Profit before tax** | **1.8 vs 8.6** | **−79%** |
| Cash generated from operations | 3.5 vs 13.4 | **−74%** |

The same device ran four months earlier: the FY2025 release headlined **"Double-digit revenue
growth"** while its own table shows **Total Group Revenue +7%** — the "double-digit" is only reachable
through "Adjusted Group Revenue +10%," itself *"adjusted for the impact of ANZ and currency."*

**Grade: takeaway-vs-data divergence, twice, on the top line.** Every number is disclosed in the same
table — this is emphasis, not concealment, so it is a **review flag rather than an elevate**. But the
pattern is deliberate and repeated, and the divergence is on the one line a reader assumes is
unadjustable.

### B-2. "Stabilisation of Indirect revenues" — refuted by the company's own next print, in 18 weeks

**03-Feb-2026, FY2025 results, bullet 2, verbatim:** *"**Stabilisation of Indirect revenues**…
revenues up 1%, with growth on social platforms ('Social') offsetting lower revenues from our
websites ('Web'), as previously indicated."*

**09-Jun-2026, 18 weeks later:** Indirect **−41%**, Social −44%, Web −36% — and the release attributes
it to Meta changes *"in line with trends outlined in **2H25**."*

2H25 ended 30-Sep-2025 — **four months before** the company published the word "Stabilisation." By its
own June account, management was watching the deterioration during the very half it later called
stable. This is the strongest honesty finding in the file: not a false number, but a **characterisation
that the company's own subsequent disclosure contradicts, on evidence it already held.**

### B-3. Debt-funded M&A at ~13x, into a de-rate, by a company trading at ~5x

On 19-Jun-2026 — ten days after the profit warning, with the stock down 68% from its high — LBG
committed **£26.8m cash for 75% of Uncovered** (calendar-2025 revenue £10.2m, adjusted EBITDA £2.7m),
plus **up to £7.0m of earnout**, plus a **9x-EBITDA put/call on the remaining 25% for 2028/29/30**,
funded by cash and a **new £50m secured HSBC facility**.

- 100%-equivalent on the initial consideration alone: £26.8m / 0.75 = **£35.7m ⇒ ~13.2x EV/EBITDA**
- LBG's own stock at the time: ~£71m market cap on FY26 guided adjusted EBITDA of £15-20m ⇒ **~4-5x**

**They issued debt to buy a private asset at roughly three times their own trading multiple, at the
moment their core business was breaking, having just told the market visibility had reduced.** The
strategic logic (buy Direct revenue to replace collapsing Indirect revenue) is coherent. The price,
the funding, the timing and the uncapped 9x put are four separate capital-allocation red flags in one
transaction.

Note also what the transaction does to disclosure quality: Uncovered's £10.2m of revenue and £2.7m of
EBITDA arrive inside the FY26 comparative, making the organic Indirect decline harder to isolate from
FY27 onward.

### B-4. Anti-masking credit — real, and it does not rescue the name

To grade honestly in both directions, LBG did disclose several things a promoter would have buried:
it **named Meta and Google AI Overviews explicitly** as the cause rather than blaming "macro"; it put
the **−41% Indirect** and **−79% PBT** in the highlights table, not the appendix; it disclosed a
**£2.8m overdue customer payment** inside the receivables bridge (subsequently collected in April);
and it stated that **"the low end of the EBITDA range… reflects a continuation of the current monthly
trend"** — a specific, falsifiable, unflattering sentence.

That is genuine. It is why this is a *reject on economics*, not a fraud flag. A business that
discloses its impairment is CLEAN; it is simply not cheap.

### B-5. Cap structure — pulled before any EV claim

209,079,740 ordinary shares; treasury shares (3,944) in reserves; no preferred, no warrants, no
converts. Non-equity claims that a naive EV misses: lease liabilities £14.30m, contingent
consideration £8.62m, Uncovered earnout up to £7.0m, the 25% put at 9x 2028-30 EBITDA (**uncapped**),
and drawings on the £50m HSBC facility (quantum undisclosed pending the FY26 report).

### B-6. AI-complex test — stated explicitly, not averaged away

LBG is not an AI-capex beneficiary; it is an **AI-disruption casualty**. Google AI Overviews are
suppressing the referral traffic that monetises its owned-and-operated Web estate.

Test against the frozen house call **AI-BREAK | 2027-12-31 @ 0.45**:

- **Does the entry require the AI cycle to hold?** No.
- **Does the de-rate already price the break?** Wrong question here — **the break does not help.** AI
  Overviews are a shipped search product, not a capex-cycle artifact; they survive a capex bust intact.
  And a capex break would compress the brand advertising budgets that fund the Direct business now
  carrying 72% of revenue.

**LBG is short-gamma to AI in both states of the world.** There is no state of the frozen call in
which this position is helped. That is disqualifying on its own for a name that would otherwise be
sized against a $5.2M/26% AI-complex household exposure.

---

## 6. Mode A — claim verification

| Claim | Method / authority | Finding |
|---|---|---|
| Price 34p, unit is pence | yfinance LBG.L `currency=GBp`, 2026-08-04 close 34.0 | **CONFIRMED** |
| +36% off a 56-day low | Close-basis 52w low 25.0p on 2026-06-09; 56 calendar days to 08-04 | **CONFIRMED** (intraday low 20.67p same day) |
| Shelf `pb` 0.8596 is an artifact | Total equity **82,701** @31-Mar-26 vs £71.09m cap — arithmetic correct; goodwill+intangibles 34,720 ⇒ P/TBV **1.48x** | **Arithmetic CONFIRMED; economic claim REFUTED** |
| Shelf `am` 3.86x is an artifact | `ev` 57,362,862 / `ebit_reported` 7,283,000 = **7.88x** | **REFUTED — 2.04x too cheap** |
| LTM statutory EBIT is 7,283 | 13,684 (FY25) + 1,965 (1H26) − 8,366 (1H25), all from the 09-Jun-26 RNS | **CONFIRMED — exact** |
| Net cash £13.7m | Contingent consideration 8,615 excluded; true 5,521 pre-acquisition, and £26.8m spent since | **REFUTED** |
| FYE is 30 September | Companies House filing history, "made up to 30 September 2025" | **CONFIRMED** |
| First-ever charge, HSBC, 09-Jun-2026 | Companies House `/charges`: code 1369 3251 0001, HSBC UK Bank PLC as Security Agent, fixed charge, Outstanding; 1 charge total in company history | **CONFIRMED** |
| Uncovered: £26.8m cash + £7.0m earnout + 9x put, £50m facility | RNS 19-Jun-2026, verbatim | **CONFIRMED** |
| FY26 guidance cut twice | 22-Apr-26: rev £110m / adj EBITDA £22m. 09-Jun-26: rev £100-107m / adj EBITDA **£15-20m** | **CONFIRMED** |
| FY25 base: rev £92.2m, adj EBITDA £25.2m, PBT £14.0m, cash £30.8m | RNS 03-Feb-2026 | **CONFIRMED** |
| "Stabilisation of Indirect" (Feb) vs −41% (Jun) | Both RNS, verbatim, 18 weeks apart | **CONFIRMED — company-refuted** |
| FY2025 accounts amended | Companies House: AA 15-Mar-2026 superseded by **AAMD 25-Jul-2026**; plus RNS Correction 04-Feb-2026 | **CONFIRMED** |
| IBKR executability | shelf `conid: null`; `search_contracts("LBG Media")` → 0 results | **UNVERIFIED — DATA-GATED** |

### Gaps — UNVERIFIABLE is not clean

1. **Why the FY2025 accounts were amended is UNKNOWN.** The Companies House PDF is a 136-page **image
   scan** (`pdftotext` yields 136 bytes for 136 pages), and no RNS explains the July re-filing. This is
   the single most important open question on the name and it is unresolved. Resolving it needs OCR of
   the AAMD or a direct question to the Nomad.
2. **Facility drawings at 30-Jun-2026 are undisclosed.** The £50m HSBC facility exists and £26.8m was
   paid; the split between cash and debt is not public until the FY26 report (~Feb 2027). Pro-forma
   net debt below is **derived, not filed**.
3. **The 25% Uncovered put is unquantifiable** — 9x adjusted EBITDA of calendar 2028/2029/2030, so its
   size depends on results three to five years out. It is an uncapped cash liability with no
   balance-sheet anchor today.
4. **No sell-side estimate trajectory** — Zeus/Berenberg forecasts are outside the free corpus. The
   de-rate-vs-derailment test runs on company guidance, which here is sufficient because guidance was
   cut twice in seven weeks in the company's own words.

---

## 7. The ruling — DERAILMENT, structural, still in progress

De-rate requires the multiple to compress against **stable or rising** estimates. LBG's own guidance
moved as follows inside a single seven-week window, and neither move was upward on profit:

| Date | FY26 revenue guide | FY26 adjusted EBITDA guide |
|---|---|---|
| FY25 actual (Feb-26) | £92.2m delivered | **£25.2m delivered** |
| 22-Apr-2026 | £110m | **£22m** |
| 09-Jun-2026 | **£100-107m** | **£15-20m** (*"low end… reflects a continuation of the current monthly trend"*) |

Adjusted EBITDA margin: **27.4% (FY25) → 15.4% (1H26) → 15-19% guided.** Revenue grows while profit
halves, because the mix shift from Indirect (platform revenue share, near-100% incremental margin) to
Direct (agency and content production, low-20s margin at best per the corrected February disclosure)
is **structurally margin-dilutive**. Management describes the substitution as strategy. It is also
necessity — Indirect is being taken away from them by Meta and Google.

**Ruling: DERAILMENT, and unlike CHH it has not plateaued** — the June release says the trend has *not*
stabilised and the low end of guidance assumes it continues.

---

## 8. Valuation — the corrected picture

Pro-forma EV (post-Uncovered; net debt **derived**, flagged in gaps):

| | £m |
|---|---|
| Market cap (34.0p × 209.08m) | 71.09 |
| + Lease liabilities | 14.30 |
| + Contingent consideration (Betches) | 8.62 |
| + Uncovered earnout, risk-weighted (~50% of £7.0m) | 3.50 |
| + Estimated net debt post-£26.8m cash outflow | ~0 to 8 |
| **Pro-forma EV** | **~£97m** |

Against FY26 guided adjusted EBITDA of £15-20m plus ~£0.8m of part-year Uncovered ⇒ **~5.7x EV/adjusted
EBITDA**. On **statutory** operating profit — LTM £7.28m, before the new London lease's depreciation
and interest, and before Uncovered's acquisition accounting — **~13x EV/EBIT**.

The screen said **3.9x and 19.3% of market cap in net cash.** The truth is **~13x statutory EV/EBIT
with the net cash spent.**

| Scenario | p | Thesis | FV |
|---|---|---|---|
| **Bear** | 0.45 | Indirect keeps eroding (structural, not cyclical); Direct scales but at low-20s margin; FY26 adj EBITDA lands at the £15m low end and FY27 at ~£13m; earnouts and the 9x put consume cash; a 30%-float AIM microcap with debt de-rates to ~4x EV/EBITDA | **20p** |
| **Base** | 0.40 | Direct compounds, Uncovered is accretive as promised, Indirect finds a floor around £20m/yr; FY27 adj EBITDA ~£20m at 5.5x, less £30m+ of leases/contingents/net debt | **38p** |
| **Bull** | 0.15 | Indirect stabilises, Direct + Uncovered drive FY27 adj EBITDA to ~£26m, re-rated to 7x | **70p** |

**E[FV] = 34.7p vs 34.0p spot ⇒ +2.1%.**

After correcting the screen's two definitional errors, **the stock is approximately fairly priced.**
That is the real finding: the market has already done this work. There is no edge, in either
direction, and the +2.1% is inside the 299bp touch — the friction alone consumes it.

---

## 9. Score: 1/10 — REJECT

| Test | Result |
|---|---|
| Cause read? | Yes — Meta feed ranking + Google AI Overviews. Structural, named by the company |
| De-rate or derailment? | **Derailment, still in progress** — guidance cut twice in seven weeks |
| Path | **+36% off a 56-day low** — late bounce; `entry_exhausted: true` was correct |
| Screen premise | **REFUTED** — 7.9x not 3.9x; 1.48x tangible book not 0.86x book; net cash spent |
| Edge | **+2.1%**, inside a 299bp touch |
| Executability | **DATA-GATED** — no IBKR conid, `search_contracts` returns nothing |
| Liquidity | median ADV $99.7k, 30.2% float, $19.9k max order |
| AI-complex | **Short-gamma to AI in both states of the frozen call** |
| Accounts reliability | **The same financial year has been corrected twice** (RNS 04-Feb-26; AAMD 25-Jul-26), reason unknown |
| Honesty grade | **Review flag** — repeated revenue-level APM headlines; a "Stabilisation" claim its own next print refuted. Not fraud; genuine anti-masking credit on cause disclosure |

The one point is for disclosure quality: they named the platforms, published the −79% PBT, and told
the market the low end of guidance was the current run-rate.

**Not escalated to red team** (threshold is 6/10). No entry band, no tranche plan, no size — the
contract requires those only at ≥4.

**No freezable call proposed.** A freezable call needs a bar whose resolution would change a decision.
Nothing about LBG's next print changes this verdict: the business is structurally impaired, the stock
is fairly priced for it, the line is not executable at IBKR, and the AI conflict is unresolvable in our
favour. Freezing a call here would manufacture a false catalyst.

**Disposition: remove from the LSE shelf candidate set. Retain solely as the generator-defect
exemplar** — it is the cleanest available case of a row that is arithmetically perfect and
economically wrong.

---

## 10. Kills (for the record, should the name ever return)

| Trigger | Action |
|---|---|
| FY26 report (~Feb 2027) shows net **debt** and adj EBITDA at or below £15m | Confirms bear; permanent discard |
| Indirect revenue declines a further >25% in FY27 | Structural thesis confirmed; discard |
| Any further amendment or restatement of filed accounts | **Immediate permanent discard** — three corrections is a control failure, not an accident |
| Uncovered earnout or the 25% put is settled above £10m | Capital allocation confirmed value-destructive |
| Indirect revenue flat or up for two consecutive halves **and** price ≤ 22p | Only condition under which a re-court is warranted |

---

## 11. Generator defect list — LBG row (consolidated for the maintainer)

1. **`am` uses adjusted EBIT while `ebit_reported` sits unused in the same row.** 3.86x → **7.88x**.
   `unusual_r: −0.465` is populated and ungated. *Rank on `ebit_reported`; hard-gate `|unusual_r| > 0.20`.*
2. **`pb` has no tangible-book sibling.** 0.86x book is **1.48x tangible book**; the ROU asset from the
   new London lease inflates book while its matching liability is counted as debt. *Add `ptbv`; net ROU
   against lease liability.*
3. **Contingent consideration is missing from the debt-like stack.** £8,615k excluded ⇒ `ncash_r`
   overstated **2.49x** (19.3% vs 7.8%). *Add contingent/deferred consideration and NCI puts.*
4. **`fy_stale: false` is wrong.** Three superseding filings since the 31-Mar-26 balance-sheet date:
   HSBC charge (09-Jun), £26.8m acquisition on a new £50m facility (19-Jun), amended FY25 accounts
   (25-Jul). *Add a free Companies House `/charges` + `/filing-history` + RNS post-period sweep as a
   UK pre-flight; hard-fail `fy_stale` on any hit.*
5. **`ebit_hist` silently drops the 9-month transition period** created by the December → September
   year-end change, invalidating `ebit_trend`, `ebit_vs_peak` and **`melting:false`** on a name whose
   EBITDA guidance fell ~40% in seven weeks. *Read `made up to` dates; refuse trend metrics across a
   period-length change.*
6. **`yfinance fast_info.market_cap` is 100x wrong on GBp lines** (LBG 7,108,711,194 vs £71,087,112;
   CHH 4,234,166,475 vs £42,341,664). *Ban `fast_info` for GBp; use `.info['marketCap']`.*
7. **Ticker collision:** "LBG" is market shorthand for Lloyds Banking Group (`LLOY`). *Key all news and
   free-text joins off ISIN GB00BKPH9R58 or company number 13693251, never the TIDM string.*
8. **Positive control — guards that worked:** `entry_exhausted: true`, `thin: true`,
   `wide_touch: true`, `adv_block_inflated: true`, and the `pension_source: long_term_provisions_proxy`
   note (which correctly told the reader the £549k was a provisions proxy, not a pension). The row's
   *warnings* were all correct. Only its *rankings* were wrong — which is why it reached a court.

---

*Court: `lse_shelf_20260804`. Price tape-verified 2026-08-04 in GBp (34.0p) from yfinance LBG.L;
IBKR line unverified. Primary sources: Companies House company 13693251 (filing history, charges),
RNS 03-Feb-2026 / 04-Feb-2026 / 22-Apr-2026 / 09-Jun-2026 / 19-Jun-2026 via investegate. Audited base
is FY to 30-Sep-2025; latest unaudited base is 31-Mar-2026, itself superseded by three post-period
filings. No shared stores written.*
