Verified — and it killed the thesis I was building. The Feb-2024 convertible (90%-VWAP conversion, Oct-31-2026 maturity) was **amended and restated on 2025-11-09**: no conversion feature, maturity pushed to **2027-12-15**. There is no 74-day dilution cliff. Good thing that was checked before it went in the table.

---

LVWR is a **misclassified cohort member**: the Consumer-Discretionary demand narrative is testably *absent* from its numbers (Q2 revenue +55%, EV units +386%), but the −82% drawdown never priced demand — it prices a pre-scale P&L with a **negative gross margin** and a funding stack whose sponsor backstop is now fully drawn.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| LVWR | STRUCTURAL | **Gross margin + operating loss vs revenue growth** (the cohort's demand metric is refuted; this one is not) | Q2-26 rev $9.1M **+55% YoY**, EV moto units 267 **+386%**, EV rev $3.6M +333%, 76% US share of 50+kW on-road; **but COGS $9.2M > rev $9.1M (negative gross margin)** and op loss **$18.0M — FLAT YoY on +55% revenue**. Cash $82.8M (12/31/25) → $67.5M (3/31/26) → **$52.9M (6/30/26)**; H1 OCF −$26.4M (vs −$32.4M, 18% better). [10-Q](https://www.sec.gov/Archives/edgar/data/0001898795/000189879526000085/lvwr-20260630.htm) · [8-K Ex-99.1](https://www.sec.gov/Archives/edgar/data/0001898795/000189879526000064/lvwrexhibit9916-30x2026.htm) | 2026-11-04 (yfinance-derived, UNCONFIRMED) | Demand damage ABSENT; the discount is structural for an **orthogonal** reason — see below |

**Why STRUCTURAL despite a clean demand refutation.** Growth is producing **no operating leverage**: revenue +55% while operating loss held flat at $18.0M, with gross margin still negative — every incremental unit currently destroys cash at the gross line. Revenue must rise roughly 5–10× just to cover today's opex. Three dated constraints bound the runway:

- **Cash exhausts ~Q2 2027.** $52.9M at 6/30/26 against ~$14.5M/qtr FCF burn ⇒ ~$38M (9/30/26), ~$24M (12/31/26), ~$9M (3/31/27). The Q1 10-Q's "sufficient for at least the next twelve months from issuance" expires ~May 2027 — precisely when the cash does.
- **The H-D backstop is EXHAUSTED.** The A&R term loan's $75.0M was **fully drawn 2025-12-15**; the balance is $76.8M and accreting at SOFR-6M + 4.00%, compounding semi-annually. Maturity 2027-12-15 — i.e. **the cash runs out ~6 months before the loan comes due**, with no undrawn capacity behind it.
- **Flow gate — hard fail.** $47.8M of ATM capacity remains (~20% of the ~$236M cap) at ~$1.15, of which the **first $10M must mandatorily prepay the H-D loan**, so only ~$37.8M is usable for operations. The ATM requires **H-D board approval** (controlled company), so a ~89% holder decides when to dilute the minority. Bidding LVWR is bidding into a registered, price-insensitive seller. ([Q1 10-Q](https://www.sec.gov/Archives/edgar/data/1898795/000189879526000048/lvwr-20260331.htm))

**COURT-WORTHY (damage-absent, ranked):** *none.* LVWR clears the demand refutation but fails the second gate — the dispersion is real and the market is pricing it correctly, just under a different heading than the cohort assigned.

**COURT-WORTHINESS LVWR: 3/10** — negative gross margin, flat op loss on +55% revenue, cash out ~Q2 2027 against a fully-drawn sponsor loan, and a 20%-of-cap ATM controlled by the 89% holder; size is zero at any price, so a court cannot move the sizing decision.

**PRINT PROXIMITY: 2026-11-04 — yfinance-derived, UNCONFIRMED; no company PR names it.** ~54 trading days out, well outside the 5-day window, so no print-decisive reconstruction is triggered. Plausible on cadence (Q2 printed 2026-07-23). **PRE-PRINT POSITION: FLAT** — no position, no starter; the next print's decisive line is whether gross margin crosses zero, and nothing in the pre-print record suggests it does.

---

### Two pipeline defects this surfaced

**1. The evidence pack's XBRL series is a full year stale.** It shows revenue peaking at $8.1M (2023) and decaying to $5.9M (2025-06-30), with **zero 2026 rows** — despite the pack's own filing list containing the Q2-2026 10-Q (0001898795-26-000085, filed 08-05) and a Q1-2026 10-Q existing (…-26-000048). Anyone sizing off the pack alone models a *decaying* business and misses the +55%/+386% inflection entirely. The `rev`/`sbc`/`dil_sh`/`ocf` extractor is not picking up FY2026 filings.

**2. This is commit `c2dd2cc5` recurring.** You just fixed blob_sweep for "selecting LEVERAGE and reporting it as DISLOCATION." LVWR is exactly that pattern — a capital-structure/funding situation scored as a Consumer Discretionary sector dislocation, where `excess_dd −0.608` vs the sector median is a category error rather than measured dispersion. This item is from the **2026-08-14** sweep, so it predates the fix; it's residual, not a regression — and it independently confirms the fix was aimed correctly.

### Verification caveats, stated plainly

- **SEC.gov returned 403 to every direct fetch** (fingerprint issue, per the known pattern). Figures were read from secondary renderings of the *exact accessions* in the evidence pack — accession numbers tie out to the pack's filing list, so the documents are right, but I did not read the primary HTML myself. The gross-margin and cash figures are consistent across three independent sources and internally consistent with the pack's own Q2-2025 revenue of $5.873M (9.1/5.873 = +55%, matching the reported growth rate).
- **The five Form 144s (07-28 → 07-31, one for 230,557 shares) filed into the post-earnings pop are UNVERIFIED as open-market sales.** At an 89%-controlled company with routine RSU comp these are commonly 10b5-1/vest-related. The check is the Form 4 transaction codes (07-31 ×2, 08-03, 08-04): code **S** = open-market sale, code **F** = tax withholding. I did not read them, and I would not treat the cluster as a signal until someone does.
- **No going-concern/substantial-doubt language** appears — the filing affirmatively states resources are sufficient for twelve months. My runway conclusion is arithmetic from disclosed cash and burn, not a company warning.

One more piece of context worth carrying: the NYSE sub-$1.00 deficiency notice landed **2026-07-23 — the same day as the Q2 earnings release** — and compliance was regained 2026-08-03 on the 30-day VWAP through 07-31. At $1.15 the stock sits ~15% above the level that re-triggers it, and the company has said it may consider a reverse split subject to shareholder approval.