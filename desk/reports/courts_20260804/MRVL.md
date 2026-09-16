# MRVL — Marvell Technology | COURT_QUEUE_20260804, tier-2 AI-COMPLEX conflict cohort #1

**Court date** 2026-08-03 (evening, US) for the 2026-08-04 session.
**Verdict: REJECT 2/10 — the drawdown denominator is a related-party soundbite.**
**Basis: IBKR live snapshot 2026-08-03, `last` $196.57, `is_close:false`, +1.45%. 52w range $61.32–$329.88 (IBKR `misc_statistics`). Historic bars from yfinance daily closes.**

---

## 1. Cause-check — reconstructed from primary filings and the tape

This is the decisive section. The chain, in order:

| # | Date | Event | Source | Result |
|---|---|---|---|---|
| 1 | **2026-03-31** | Marvell sold **2,000,000 shares of Series A Convertible Preferred to NVIDIA Corporation for $2,000,000,000 cash**. $1,000 stated value, **initial conversion price ~$91.8355**, max **21,778,000** common shares. Pari passu with common on liquidation, votes as-converted, dividends as-converted, no redemption/preemptive rights. | 8-K 0001193125-26-134462, Items 3.02 & 5.03 | **CONFIRMED** |
| 2 | 2026-05-27 | Q1 FY27: revenue **$2.418B, +28% y/y** (record); GAAP diluted EPS **$0.04**; non-GAAP **$0.80**; OCF $638.8M. Q2 guide **$2.700B ±5% (+35% y/y)**, non-GAAP EPS $0.93. Management: "we are significantly raising Marvell's revenue outlook for both fiscal 2027 and fiscal 2028." | 8-K 0001835632-26-000014 EX-99.1 | **CONFIRMED** |
| 3 | **2026-06-01/02** | **NVIDIA's CEO publicly called Marvell "the next trillion-dollar company."** MRVL gapped from a $219.43 close to a **$253.46 open** and closed **$290.79 — +32.5% on 112.6M shares** (vs ~30M normal). No 8-K, no company press release, no guidance change. It ran to $316.43 by 6/04 and an intraday $329.88. | yfinance daily bars (open/high/low/close/volume, verified) + Google-News RSS headlines dated 2026-06-01/02 (TradingView, XTB, eciks) | **CONFIRMED (tape) / PLAUSIBLE (attribution — headline-sourced, not a filing)** |
| 4 | 2026-06-11 | CFO transition: Willem Meintjes out, **Dan Durn in** (ex-CFO of GlobalFoundries, Freescale, NXP, Applied Materials). Q2 outlook reaffirmed same day. | 8-K 0001193125-26-267688 EX-99.1 | **CONFIRMED** |
| 5 | 2026-06-22 | Added to the S&P 500 — mechanical index-inclusion demand on top of (3). | Google-News RSS | PLAUSIBLE (not filing-verified) |
| 6 | June 15 → Aug 3 | A continuous stream of **Rule 144 notices and Form 4s**: 144s filed 6/01, 6/15 (×2), 6/16, 6/23, 6/29, 7/01, 7/16 and **8/03**; Form 4 clusters 6/15–6/17 and 6/29. Insiders registered and filed sales into and through the spike. | EDGAR submissions index, CIK 0001835632 | **CONFIRMED (filings exist)** / counts and dollar amounts NOT tabulated this session |
| 7 | July 2026 | **−31.1% on the month**, low $163.40 on 7/29, closing $187.56 on 7/31. −40.4% from the 6/04 high. | yfinance bars | **CONFIRMED** |

### The ruling

**Neither a de-rate nor a derailment. It is the retrace of a promotional spike created by a related party.**

The "own three-year high" that the screen measures −40% against was printed on a verbal endorsement from the holder of a $2.0B convertible preferred struck at **$91.8355**. At the June-4 high of $316.43 that paper was worth ~$6.9B against a $2.0B cost — a 3.4× mark — and at tonight's $196.57 it is still worth ~$4.28B, +114% in four months. The speaker was long. The screen's denominator is that speaker's sentence.

This is a **new factor-costume mode** and it should be encoded: `quality_drawdown.py` already tests whether a drawdown is sector beta in disguise (`factor_costume`, which correctly caught AEM/gold). It has no test for whether the *high* was manufactured. Two cheap gates would have caught it:

1. **Age-of-high gate** — reject when the 3-year high is younger than ~180 days. MRVL's high was **60 days old** at the screen date; ARM's 46 days; KLAC's 33.
2. **Promotional-high gate** — flag when the 3y high was set within 5 sessions of a >3σ single-day advance that has **no corresponding company filing**. MRVL's +32.5% day on 3.7× normal volume with an empty EDGAR docket is exactly that signature.

**Gate test as filed:** `EXHAUSTED` fired and was **RIGHT** — MRVL is **+220.6% off its 52-week low** ($61.32, 331 days old), the most extreme in the cohort and far past `HARD_OFF_LOW = 0.50`. The ×0.45 demotion is doing real work. The `depth` term (0.35 weight, rewarding proximity to a −46% drawdown) is actively harmful here and outweighs it.

## 2. Which leg of the AI cycle funds the earnings — the purest exposure in the set

Management's own list of drivers: "800G and 1.6T scale-out optics, 51.2T Ethernet scale-out switches, scale-up optical solutions for NPO and CPO applications, scale-across datacenter interconnect modules, and **custom XPU and XPU-attach solutions**."

Every item on that list is a **line inside a hyperscaler or neocloud capital budget**. There is no consumer leg, no government leg, no maintenance/services annuity of consequence. Marvell's revenue *is* the capex. Under the house call this is the maximum-beta expression, and there is nothing on the other side of the ledger.

Aggravating structure pulled before any valuation claim:

- **Debt $4,961M** (10-Q 5/2/26), refinanced in April 2026 via a senior-notes offering (424B5 filed 2026-04-06 — proceeds "for the repayment of debt, including our 1.650% senior notes due 2026," remainder general corporate incl. **acquisitions**).
- Cash $3,844M → net debt ~$1.12B (post the $2.0B NVIDIA proceeds, which are inside that cash).
- **Goodwill $13,884M against total equity $18,216M — 76% of book.** Celestial AI (closed 2026-02-02) and XConn (2026-02-10) were bought at cycle-peak prices; a capex break is precisely the event that impairs them.
- Fully-diluted share count: 915M guided diluted for Q2 **plus** 21.778M preferred-as-converted (EPS is computed under the two-class method, so the preferred is *not* in the 915M) ≈ **937M**.

## 3. Valuation and what the −40% actually prices

At $196.57 × ~937M fully diluted = **~$184.2B market cap**, EV ~**$185.3B**.

| metric | value | context |
|---|---|---|
| TTM revenue (Q2-Q4 FY26 $2,006+$2,074+$2,220M + Q1 FY27 $2,418M) | $8,718M | XBRL companyfacts + FY26 total $8,195M |
| **P/S trailing** | **21.1×** | 3-yr range **9.0× – 31.1×** → ~75th percentile |
| P/S on FY27E ~$11.4B | 16.2× | vs 9–13× through 2023–2025 |
| Non-GAAP P/E on FY27E ~$3.85 | ~51× | |
| **GAAP P/E on FY27E ~$1.30** | **~151×** | Q1 GAAP EPS was **$0.04** vs $0.80 non-GAAP — a 20× gap, the widest in the cohort |

**The −40% drawdown prices none of the break.** It prices the removal of the June soundbite premium. MRVL is still two-thirds above the multiple it carried through the entire 2023–2025 period, on a revenue base that the house call gives a 45% chance of being disrupted by end-2027.

## 4. Conflict resolution vs AI-BREAK | 2027-12-31 @ 0.45

- **Does the entry require the cycle holding?** Yes — completely, on both the revenue and the multiple leg, with a goodwill-impairment amplifier and a levered balance sheet. There is no version of this position that survives the house call being right.
- **Does the de-rate price it?** No (see §3).
- **Not averaged away:** the honest statement is that MRVL at $196.57 is roughly *fairly* priced for a coin-flip, and that is the problem — a coin flip at **100% implied volatility** (IBKR `implied_vol_underlying` annual 100.2%, `historical_vol` 101.5%) with zero compensation for the fact that the reference price was set by an interested party.

## 5. Scenarios (FY-2028, ending Jan-2028)

| | p | assumption | FV/sh |
|---|---|---|---|
| Bear | 0.40 | break lands; FY28 revenue $9.0B, 8× sales, goodwill impairment | **$77** |
| Base | 0.42 | cycle holds; FY28 $14.5B, 16× sales | **$248** |
| Bull | 0.18 | share gains hold; FY28 $17.0B, 20× | **$363** |

**E[FV] $200.3 vs $196.57 → edge +1.9%.** Zero edge, ~±60% dispersion, 100% IV. That is a lottery ticket priced as a lottery ticket.

## 6. Four-idea frame

1. **Long here** — rejected. No edge, maximum cycle beta, promotional price formation.
2. **Long on a price gate** — a band would have to sit near **$105–115** (≈9–10× FY27 sales, the 2023–25 norm). That is −45% from here and coincides with the break beginning to price; arm nothing above it.
3. **Short / put structure** — rejected on doctrine (no premium selling in the taxable book) and on risk: shorting into +35% guided revenue growth and an Oct-6 investor day is the wrong side of the tape.
4. **No position; encode the mechanism** — adopted. Deliverables: the age-of-high gate, the promotional-high gate, and the related-party-endorsement costume.

## 7. Catalyst map

| Catalyst | date | p of firing | magnitude | leading indicator |
|---|---|---|---|---|
| **Q2 FY27 earnings call** | **2026-08-27** (company-announced) | 1.0 | ±15–25% (100% IV) | hyperscaler Q2 capex prints already in: GOOGL $44.9B, MSFT $35.8B, META $30.1B for Jun-26 — all up sharply, so the near-term order book is *supported* |
| **Investor Day** | **2026-10-06** (company-announced) | 1.0 | ±10% | a long-term TAM/model refresh; historically a re-rating venue |
| NVIDIA preferred conversion / HSR clearance | undated | 0.3 by end-27 | −2% (overhang) | 8-K or 13D |
| Goodwill impairment test | FY-end Jan-2028 | 0.25 | −10% GAAP optics | any two consecutive quarters of order-book decline |
| Insider 144/Form-4 cadence | continuous | — | — | **the standing tripwire**: the 6/15–8/03 filing stream is the cleanest available read on how insiders price this |

## 8. Kills

- **Hard kill on any long thesis** while the price sits above 12× forward sales.
- Kill the watch entirely if FY28 revenue guidance is cut at the Oct-6 investor day (that is the order-book confession).
- Re-court only after (a) price ≤$115 **and** (b) two consecutive quarters where GAAP EPS is at least 40% of non-GAAP EPS (today it is 5%).

## 9. Verification notes / gaps

- Cap structure pulled **before** any EV claim, per doctrine: $2.0B NVIDIA Series A convertible preferred (21.778M as-converted at $91.8355), $4.96B senior notes, 915M guided diluted common. No warrants found.
- **Top UNVERIFIABLE item:** the attribution of the 2026-06-02 +32.5% move to the NVIDIA CEO's remark rests on news headlines, not on a filing or a transcript. The *move* and the *absence of any company filing that day* are both filing-verified; the *cause* is headline-sourced. If that attribution is wrong the "promotional high" framing weakens — but the age-of-high and multiple-percentile objections stand on their own.
- Not tabulated this session: dollar value of the June–August insider sales (Form 4 XML not parsed); S&P 500 inclusion date not filing-verified; Celestial AI purchase price not pulled.
- Honesty read: **not a liar — a promoter's beneficiary.** Everything above is disclosed: the NVIDIA preferred is in an 8-K, the GAAP/non-GAAP gap is in the release, the goodwill is on the balance sheet. There is no fabricated datum. The divergence is that the *price* embedded a claim ("next trillion-dollar company") that the company never made in a filing and that no disclosure supports.
