# SHORT **AFRM** / LONG **COF** — Fintech lending / BNPL

**Tier:** TIER2   ·   **Composite (short):** 0.67   ·   **Flags (short):** 0R / 0S / 2M

**Long-leg composite:** 0.25 (in-cohort cleanest follow)

**Short-leg filing analyzed:** `0001820953-25-000080_10-K.txt`

---

## Thesis

Tier 2 (lower-conviction, MOD-pattern): composite 0.60–1.20 with ≥2 MODERATE findings and no RED_FLAG. The thesis is a **disclosure-quality re-rating** — the market eventually penalizes the multiple applied to filings where claims don't independently verify. Holding period typically 6–12 months; basket sizing preferred over single-name conviction.

---

## Evidence (R / F(M) / M)

#### 🟡 MOD — `AFRM-2`
- **R (claim):** Affirm has a material installment-financing services agreement with Amazon.com Services LLC and Amazon Payments, Inc., supported by issued warrants to Amazon (most recently the Second Replacement Warrant dated February 14, 2025).
- **Source quote:** _Amended and Restated Installment Financing Services Agreement, dated as of November 10, 2021, by and among Affirm Holdings, Inc., Amazon.com Services LLC and Amazon Payments, Inc. ... Second Replacement Warrant to Purchase Class A Common Stock of Affirm Holdings, Inc., by and bet_
- **F (M-source check):** edgar_fts.query_fulltext
- **M (observed):** edgar_fts: 0 hits for 'Affirm' on cik=0001018724
- **Why this severity:** Heuristic 7: counterparty CIK 0001018724 returns 0 filings naming the claim's subject; counterparty-disclosure gap.

#### 🟡 MOD — `AFRM-3`
- **R (claim):** Affirm has a Global Customer Installment Program Agreement with Shopify Inc. dated February 14, 2025.
- **Source quote:** _Global Customer Installment Program Agreement, dated February 14, 2025, by and between Shopify Inc. and Affirm, Inc._
- **F (M-source check):** edgar_fts.query_fulltext
- **M (observed):** edgar_fts: 0 hits for 'Affirm' on cik=0001594805
- **Why this severity:** Heuristic 7: counterparty CIK 0001594805 returns 0 filings naming the claim's subject; counterparty-disclosure gap.

---

## Execution

### Shortability
- **Tier:** `SHORTABLE`
- Price: $65.82
- Market cap: $21.92B
- Daily $ volume: $372.54M
- Short float: 6.8%

### IBKR borrow
- **Latest fee:** **0.25%** annualized (2026-05-15)
- Shares available: 2.3M
- 30-day avg: 0.26%
- 30-day max: 0.30%
- Trend: **stable**

### Hedge ratio
- **Beta-neutral:** **3.55×** (short β=3.69, long β=1.04)
- _Method: beta-neutral (short_beta / long_beta)_
- For every $1 long COF, short $3.55 of AFRM.

### Notional cap (5% daily $ vol)
- Short daily $ vol: $372.54M → cap $18.63M
- Long daily $ vol: $924.62M → cap $46.23M
- **Binding leg: short**
- **Max long-leg notional:** $18.63M

### Suggested conservative entry (30% of cap)
- Long COF: **$5.59M**
- Short AFRM: **$19.83M**
- Annualized borrow carry on short: **$49,568/yr** (0.25% × $19.83M)

---

## Risk + falsification

- **Falsification window:** 12 months from cutoff (2026-05-16). Pair survives if either leg moves >50% against the thesis OR the divergence claim is corroborated post-cutoff and the pair returns ~0.
- **Suggested exit rule:** close on +20% adverse move on the short leg, OR 6 months without confirming evidence, whichever comes first.
- **Hedge ratio reliability:** if either β was missing (default 1:1 fallback), the hedge is approximate. Watch correlation drift quarterly.

## Pair metadata
- Theme: Fintech lending / BNPL
- Generated: 2026-05-17 from frozen position_sizing.json + borrow_rates.json