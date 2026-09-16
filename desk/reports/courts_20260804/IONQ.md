# IONQ — IonQ, Inc. | COURT_QUEUE_20260804 (tier-2 AI/frontier-hype cohort #2)

**Court date** 2026-08-03 · **Verdict: 0/10 REJECT — ATTENTION name, no floor, no short**
Queue flag: GUIDE-DECEL · score 50.8 · "-56% from own 3y high, gm 36%, rev3y 126.9%"

---

## 0. Price basis (tape-verified)

| item | value |
|---|---|
| 08-03 last | **$38.83** (+6.6% on the day) |
| 07-31 close | $36.44 |
| 3y / 52w high | $82.09 |
| 60-session low | **$31.99 on 2026-07-29 — 2 SESSIONS AGO** |
| off that low | **+21.4%** |
| beta | **3.30** |
| implied shares (mktcap ÷ close) | ~398M → market cap at $38.83 ≈ **$15.45B** |

Days with a ±10% move in 2026 YTD: **10**. This is an attention instrument, not a security with a price.

---

## 1. The decisive finding — IONQ's GAAP profit is a warrant mark

XBRL companyfacts, CIK 1824920, quarter ended 2026-03-31:

| tag | value |
|---|---|
| `NetIncomeLoss` | **+$805.4M** |
| `FairValueAdjustmentOfWarrants` | **−$1,057.6M** (i.e. a **$1.058B gain** to net income) |
| `OperatingIncomeLoss` | **−$271.5M** |
| `ResearchAndDevelopmentExpense` | $125.7M (one quarter) |
| `RevenueFromContractWithCustomerExcludingAssessedTax` | $64.7M |
| `NetCashProvidedByUsedInOperatingActivities` | **−$151.0M** (one quarter) |
| `Goodwill` | **$2,127.7M** |
| `CommonStockSharesOutstanding` | 373.2M |

**IonQ reported an $805M "profit" on $64.7M of revenue while losing $271.5M at the operating line and burning
$151M of cash in the quarter.** The swing is a SPAC-legacy warrant liability remarked as the stock fell. The
symmetric prior-period entry confirms it: `NetIncomeLoss` was **−$1,055.0M** in the quarter ended 2025-09-30,
when the stock rose.

**SCREEN-INTEGRITY FINDING (report to the desk).** Vendor fields for IONQ read `trailingPE = 99.6` and
`profitMargins = +174.9%`. Any screen ranking on trailing GAAP net income classifies IonQ as a **profitable**
company. It is not. This corrupted the tier-2 ranking that put IONQ in this queue at score 50.8.
**Recommended gate:** for any SPAC-legacy issuer, net-income-derived screen fields must be adjusted by
`FairValueAdjustmentOfWarrants` (and `FairValueAdjustmentOfConvertibleNotes`) before ranking.

---

## 2. Mode B — is there ANY fundamental floor?

**Cash floor:** cash $493.5M + short-term investments $1,539.9M = **$2.03B** = **$5.10/share** against $38.83.
**The floor is 87% below spot.** There is no valuation support of any kind between here and there.

**Burn:** operating cash flow −$151.0M in Q1'26 alone (annualising ≈ −$600M); operating loss run-rate ≈
−$1.09B/yr. Even the full $2.03B is ~3.4 years of the *current* burn, and the burn is accelerating
(FY25 CFO −$33.0M → Q1'26 alone −$151.0M).

**Dilution machine — CONFIRMED, and it is the business model.**
Shares outstanding (DEI cover): **296.8M (2025-07-30) → 354.3M (2025-10-29) → 366.6M (2026-02-18) →
373.3M (2026-04-29)** = **+25.8% in nine months.**
Stockholders' equity: $765.0M (2025-03-31) → **$4,976.0M (2026-03-31)** — $4.2B of equity created in twelve
months. **$2.13B of that is goodwill (43% of book)**, from stock-funded acquisitions. IonQ is buying revenue
with its own paper and printing the resulting goodwill as book value.

**Revenue quality:** the queue's "rev3y 126.9%" and the Q1 jump ($7.6M Q1'25 → $64.7M Q1'26) are dominated by
acquisitions, not organic scaling of quantum systems. Gross margin **36%** — a hardware/services mix, not a
software franchise.

**Multiples:** EV = $15.45B − $2.03B ≈ **$13.4B** on $187M TTM revenue = **EV/S ≈ 71x**, at a 36% gross margin,
burning $600M/yr.

---

## 3. AI-BREAK conflict (frozen: AI-BREAK | 2027-12-31 @ p=0.45)

IONQ is a **hype-beta cousin**, not a capex-chain name — no meaningful revenue is contingent on hyperscaler
capex. But its *multiple* is entirely a function of frontier-technology risk appetite, which is the same
sentiment channel that breaks. In an AI-capex break, IONQ has:
- no earnings to support a floor,
- an equity-funded burn that requires an open ATM window, and
- 43%-of-book goodwill from stock-funded deals that gets tested when the paper de-rates.

**Does the entry require the cycle holding? Yes, via the financing channel — which is worse than the revenue
channel, because it is what forces the dilution.**

---

## 4. discovery_state — why the house neither buys nor shorts this

- Market cap **$15.45B on $187M of TTM revenue** (≈83x sales) — the queue note's framing is confirmed.
- Sell-side: 13 analysts, `recommendationKey = strong_buy`, **target mean $68.41 = +76% above spot.**
- Beta 3.30; ten ±10% days YTD; +21.4% off a two-session-old low.

→ **CROWDED / ATTENTION.** Standing house doctrine: **never short an attention name** (the RCAT lesson — squeeze
fuel overturns the fundamental read), and **do not buy a hype-unwind without a mechanism**. There is no
mechanism here: no catalyst that forces the gap to close, no cash-flow date, no asset test.

Options are also off the table — premium-selling in the taxable book is barred (non-deferrable short-term
ordinary income at ~50%+).

---

## 5. Mode A — claim verification

| claim | authority | finding |
|---|---|---|
| "gm 36%" | vendor / XBRL | **CONFIRMED** |
| "-56% from own 3y high" | yfinance closes | **CONFIRMED** |
| "rev3y 126.9%" | XBRL | **CONFIRMED as arithmetic, MISLEADING as signal** — off a ~$0 base and acquisition-driven |
| GUIDE-DECEL flag | consensus Q2 rev $66.4M vs Q1 $64.7M | **CONFIRMED** — sequential growth has stalled at ~+3% q/q |
| "profitable" (implied by vendor trailing P/E) | XBRL `FairValueAdjustmentOfWarrants` | **REFUTED** — warrant mark; operating loss −$271.5M |
| dilution machine | DEI cover shares, 4 filings | **CONFIRMED** — +25.8% in 9 months |
| cash position | XBRL 2026-03-31 | **CONFIRMED** — $2.03B incl. short-term investments |
| next print 2026-08-05 | yfinance calendar | **CONFIRMED — 2 days out** |

**UNVERIFIABLE (gaps):** remaining ATM capacity and shelf availability; warrant strike/expiry schedule;
organic-vs-acquired revenue split (not disclosed at the level needed); goodwill impairment testing assumptions.

---

## 6. Scenarios (on $38.83) — stated, but the honest label is "not a valuation problem"

| | p | FV | logic |
|---|---|---|---|
| bear | **0.55** | $12 | attention unwind / quantum funding winter; reverts toward ~20x sales |
| base | 0.30 | $36 | revenue to ~$350M by 2027 at ~40x sales |
| bull | 0.15 | $90 | quantum-advantage narrative + $600M revenue at 60x |

**E[FV] = $30.90 → edge −20%.** These scenarios are sentiment multiples on a pre-profit story; they are not
load-bearing. The verdict rests on the floor (−87%) and the burn, not on the point estimate.

---

## 7. Ruling

**0/10 REJECT.** No long: 71x EV/sales, $600M/yr burn, 26%/9mo dilution, cash floor 87% below spot, prints in
two days. **No short:** attention name, beta 3.3, "strong buy" with a +76% street target — squeeze fuel.
**No options:** taxable-book premium ban.

Honesty axis: **the +$805M "net income" is the catch** — not because IonQ hid it (the warrant line is in the
filings), but because it is *load-bearing for every mechanical screen that touched this name*, including ours.
The finding is a **screen-integrity** fix, not a company-honesty exclusion.

**No band, no size, no order, no re-court date.** Remove from the courtable universe until either
(a) operating cash flow turns positive, or (b) the price reaches within 2x of the cash floor.

**Freezable call:** `IONQ | 2026-08-05 | bar: the Q2-2026 release reports GAAP net income whose sign is driven
by the warrant/derivative fair-value line rather than operations (i.e. |fair-value adjustment| > |operating
loss|) | our_p = 0.75`
(A gradeable test of the screen-integrity mechanism, not of the business.)

**RED TEAM REQUIRED? No** (0/10).

**Top UNVERIFIABLE:** remaining ATM/shelf capacity — the single number that determines how much more dilution
is coming and it is not disclosed.
