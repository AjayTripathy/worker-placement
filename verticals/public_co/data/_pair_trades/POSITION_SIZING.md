# Signal OS — Paired Trades: Position Sizing + Shortability Pass

Two tiers, both pulled from `PAIR_TRADES.md`:

- **Tier 1 (high-conviction):** short composite >= 0.75 AND (>=1 RED_FLAG_NEGATIVE OR >=2 SEVERE_UNDERDELIVERY)
- **Tier 2 (lower-conviction, MOD-pattern):** short composite >= 0.6 AND >=2 MODERATE_UNDERDELIVERY (and doesn't already qualify for Tier 1)
- Both tiers require long composite <= 0.3 (clean control) and max 2 pairs per long-side ticker.

## Why Tier 2 scores are softer

A composite in the **0.60–0.74** range with no RED_FLAG and <2 SEVERE typically reflects a different *kind* of finding than the Tier-1 pattern. Tier 1 captures **hard contradictions** — counterparty disclosures or registries flatly contradict the filing's claim (RED_FLAG) or the filing materially overstates a verifiable metric (SEVERE). Tier 2 captures **disclosure-quality issues**:

- **Heuristic 7 firing** — the focal company names a Tier-1 counterparty at material $-scale, but the counterparty's 10-K returns 0 hits for the focal company / product. Counterparties don't unilaterally hide material partnerships, so silence is meaningful, but it could also be a search-coverage artifact (different naming convention, filing-date offset, etc.). MODERATE rather than RED because the absence-of-evidence isn't conclusive.
- **Filing-discipline gaps** — claimed regulatory filings (ABS-15G cadence, sales-agent underwriting agreements, etc.) not located in the expected SEC submission window. Often a CIK-scope or form-type-naming issue, occasionally a real disclosure miss.
- **Quantitative claims with weak corroboration** — specific $-amounts or percentages named in the filing where the M-side registry has *some* data but the data doesn't directly compare (different scope, different perimeter, different reporting cadence).

**Trade thesis difference:** Tier 1 shorts are betting on a **factual revision** (restatement, customer churn, regulator action). Tier 2 shorts are betting on a **disclosure-quality re-rating** — the market eventually penalizes the multiple applied to filings where claims don't independently verify. Tier 2 trades typically need a longer holding period and benefit more from being part of a basket than from a concentrated single-name bet.

**Hedge ratio** is beta-neutral: short_beta / long_beta. Interpretation: for every $X long the long-leg, short $(X × ratio) of the short-leg.
**Notional cap** is 5% of the more-illiquid leg's daily $ volume.
**Shortability tier** flags the short-leg's practical executability: sub-$5 retail-broker prohibition, sub-$50M mcap HTB territory, daily $ vol below $1M liquidity gate, short_float >25% squeeze risk.

## Tier 1 — high-conviction (6 pairs)

| # | SHORT | LONG | Comp | Flags | Long comp | Shortability | Beta-neutral hedge | Max long notional ($) |
|---:|---|---|---:|---|---:|---|---:|---:|
| 1 | **MVST** | ALB | 1.57 | 2R/2S/1M | 0.12 | BORROW_AT_PREMIUM | 2.61 | $0.31M |
| 2 | **SES** | ALB | 1.50 | 1R/1S/4M | 0.12 | BORROW_AT_PREMIUM | 0.62 | $0.52M |
| 3 | **KSCP** | TER | 1.44 | 3R/0S/4M | 0.11 | HARD_TO_BORROW_OR_RETAIL_RESTRICTED | 0.71 | $0.08M |
| 4 | **BLDP** | LIN | 1.22 | 1R/1S/6M | 0.00 | BORROW_AT_PREMIUM | 2.68 | $1.07M |
| 5 | **FCEL** | LIN | 1.00 | 0R/2S/4M | 0.00 | SHORTABLE | 3.22 | $4.72M |
| 6 | **AIRO** | KTOS | 0.75 | 1R/0S/0M | 0.00 | SHORTABLE | 1.00 | $0.18M |

## Tier 2 — lower-conviction, MOD-pattern (6 pairs)

| # | SHORT | LONG | Comp | Flags | Long comp | Shortability | Beta-neutral hedge | Max long notional ($) |
|---:|---|---|---:|---|---:|---|---:|---:|
| 7 | **IREN** | EQIX | 1.17 | 0R/1S/5M | 0.00 | SHORTABLE | 4.24 | $31.85M |
| 8 | **CIFR** | EQIX | 0.83 | 0R/0S/5M | 0.00 | BORROW_AT_PREMIUM | 1.00 | $31.85M |
| 9 | **AEVA** | INVZ | 0.75 | 0R/0S/3M | 0.14 | BORROW_AT_PREMIUM | 1.00 | $0.00M |
| 10 | **RDW** | IRDM | 0.71 | 0R/1S/3M | 0.12 | SHORTABLE | 3.07 | $4.72M |
| 11 | **OUST** | INVZ | 0.67 | 0R/0S/2M | 0.14 | BORROW_AT_PREMIUM | 1.00 | $0.00M |
| 12 | **AFRM** | COF | 0.67 | 0R/0S/2M | 0.25 | SHORTABLE | 3.55 | $18.63M |

_Flag column: R/S/M = RED_FLAG / SEVERE / MODERATE counts. Tier 2 rows show a 0/0/N or 0/1/N pattern — the composite is built from MODERATEs, not from hard contradictions._

## Per-pair detail

### 1. SHORT **MVST** / LONG **ALB**  (Solid-state battery)  **[Tier 1]**

**Truth_signal:** composite 1.57, 2 RED_FLAG, 2 SEVERE, 1 MODERATE  (long ALB composite 0.12)

**Short leg (MVST) shortability — BORROW_AT_PREMIUM:**
- price: $1.42
- market cap: $0.47B
- daily $ vol: $6.26M
- short_float: 10.2%
- **gating concerns:**
  - price $1.42 < $5 (most retail brokers prohibit short)

**Long leg (ALB) snapshot:**
- price: $180.38
- market cap: $21.27B
- daily $ vol: $384.21M

**Beta-neutral hedge ratio:** **2.61** (short β=3.50, long β=1.34; beta-neutral (short_beta / long_beta))
- For every $1.00 long ALB, short $2.61 of MVST to be beta-neutral.

**Liquidity-based notional cap:**
- short daily $ vol: $6.26M → 5% = $0.31M
- long  daily $ vol: $384.21M → 5% = $19.21M
- **binding leg: short**, max long-leg notional ≈ $0.31M

---

### 2. SHORT **SES** / LONG **ALB**  (Solid-state battery)  **[Tier 1]**

**Truth_signal:** composite 1.50, 1 RED_FLAG, 1 SEVERE, 4 MODERATE  (long ALB composite 0.12)

**Short leg (SES) shortability — BORROW_AT_PREMIUM:**
- price: $1.13
- market cap: $0.42B
- daily $ vol: $10.49M
- short_float: 7.2%
- **gating concerns:**
  - price $1.13 < $5 (most retail brokers prohibit short)

**Long leg (ALB) snapshot:**
- price: $180.38
- market cap: $21.27B
- daily $ vol: $384.21M

**Beta-neutral hedge ratio:** **0.62** (short β=0.83, long β=1.34; beta-neutral (short_beta / long_beta))
- For every $1.00 long ALB, short $0.62 of SES to be beta-neutral.

**Liquidity-based notional cap:**
- short daily $ vol: $10.49M → 5% = $0.52M
- long  daily $ vol: $384.21M → 5% = $19.21M
- **binding leg: short**, max long-leg notional ≈ $0.52M

---

### 3. SHORT **KSCP** / LONG **TER**  (Robotics / autonomy)  **[Tier 1]**

**Truth_signal:** composite 1.44, 3 RED_FLAG, 0 SEVERE, 4 MODERATE  (long TER composite 0.11)

**Short leg (KSCP) shortability — HARD_TO_BORROW_OR_RETAIL_RESTRICTED:**
- price: $2.95
- market cap: $0.05B
- daily $ vol: $1.54M
- short_float: 18.5%
- **gating concerns:**
  - price $2.95 < $5 (most retail brokers prohibit short)
  - market cap $48M < $50M (thin / no borrow expected)

**Long leg (TER) snapshot:**
- price: $337.88
- market cap: $52.89B
- daily $ vol: $1169.06M

**Beta-neutral hedge ratio:** **0.71** (short β=1.27, long β=1.78; beta-neutral (short_beta / long_beta))
- For every $1.00 long TER, short $0.71 of KSCP to be beta-neutral.

**Liquidity-based notional cap:**
- short daily $ vol: $1.54M → 5% = $0.08M
- long  daily $ vol: $1169.06M → 5% = $58.45M
- **binding leg: short**, max long-leg notional ≈ $0.08M

---

### 4. SHORT **BLDP** / LONG **LIN**  (Hydrogen / fuel-cell)  **[Tier 1]**

**Truth_signal:** composite 1.22, 1 RED_FLAG, 1 SEVERE, 6 MODERATE  (long LIN composite 0.00)

**Short leg (BLDP) shortability — BORROW_AT_PREMIUM:**
- price: $4.45
- market cap: $1.34B
- daily $ vol: $21.40M
- short_float: 7.1%
- **gating concerns:**
  - price $4.45 < $5 (most retail brokers prohibit short)

**Long leg (LIN) snapshot:**
- price: $506.11
- market cap: $234.13B
- daily $ vol: $1209.60M

**Beta-neutral hedge ratio:** **2.68** (short β=1.98, long β=0.74; beta-neutral (short_beta / long_beta))
- For every $1.00 long LIN, short $2.68 of BLDP to be beta-neutral.

**Liquidity-based notional cap:**
- short daily $ vol: $21.40M → 5% = $1.07M
- long  daily $ vol: $1209.60M → 5% = $60.48M
- **binding leg: short**, max long-leg notional ≈ $1.07M

---

### 5. SHORT **FCEL** / LONG **LIN**  (Hydrogen / fuel-cell)  **[Tier 1]**

**Truth_signal:** composite 1.00, 0 RED_FLAG, 2 SEVERE, 4 MODERATE  (long LIN composite 0.00)

**Short leg (FCEL) shortability — SHORTABLE:**
- price: $21.36
- market cap: $1.13B
- daily $ vol: $94.41M
- short_float: 8.7%

**Long leg (LIN) snapshot:**
- price: $506.11
- market cap: $234.13B
- daily $ vol: $1209.60M

**Beta-neutral hedge ratio:** **3.22** (short β=2.38, long β=0.74; beta-neutral (short_beta / long_beta))
- For every $1.00 long LIN, short $3.22 of FCEL to be beta-neutral.

**Liquidity-based notional cap:**
- short daily $ vol: $94.41M → 5% = $4.72M
- long  daily $ vol: $1209.60M → 5% = $60.48M
- **binding leg: short**, max long-leg notional ≈ $4.72M

---

### 6. SHORT **AIRO** / LONG **KTOS**  (Defense-tech)  **[Tier 1]**

**Truth_signal:** composite 0.75, 1 RED_FLAG, 0 SEVERE, 0 MODERATE  (long KTOS composite 0.00)

**Short leg (AIRO) shortability — SHORTABLE:**
- price: $6.37
- market cap: $0.20B
- daily $ vol: $3.55M
- short_float: 10.7%

**Long leg (KTOS) snapshot:**
- price: $52.09
- market cap: $9.77B
- daily $ vol: $233.36M

**Beta-neutral hedge ratio:** **1.00** (short β=?, long β=1.01; default 1:1 (missing beta data))
- For every $1.00 long KTOS, short $1.00 of AIRO to be beta-neutral.

**Liquidity-based notional cap:**
- short daily $ vol: $3.55M → 5% = $0.18M
- long  daily $ vol: $233.36M → 5% = $11.67M
- **binding leg: short**, max long-leg notional ≈ $0.18M

---

### 7. SHORT **IREN** / LONG **EQIX**  (AI-DC / crypto-pivot)  **[Tier 2 — MOD-pattern]**

**Truth_signal:** composite 1.17, 0 RED_FLAG, 1 SEVERE, 5 MODERATE  (long EQIX composite 0.00)

**Conviction note:** this pair's composite is driven by MODERATE_UNDERDELIVERY flags (disclosure-quality issues — typically counterparty 10-Ks silent on the claimed relationship, or quantitative claims with weak corroboration) rather than RED_FLAG or SEVERE patterns. Lower conviction than Tier 1; treat as a softer disclosure-quality trade, not a hard-contradiction short.

**Short leg (IREN) shortability — SHORTABLE:**
- price: $52.94
- market cap: $18.89B
- daily $ vol: $2067.31M
- short_float: 18.0%

**Long leg (EQIX) snapshot:**
- price: $1059.44
- market cap: $104.49B
- daily $ vol: $636.96M

**Beta-neutral hedge ratio:** **4.24** (short β=4.20, long β=0.99; beta-neutral (short_beta / long_beta))
- For every $1.00 long EQIX, short $4.24 of IREN to be beta-neutral.

**Liquidity-based notional cap:**
- short daily $ vol: $2067.31M → 5% = $103.37M
- long  daily $ vol: $636.96M → 5% = $31.85M
- **binding leg: long**, max long-leg notional ≈ $31.85M

---

### 8. SHORT **CIFR** / LONG **EQIX**  (AI-DC / crypto-pivot)  **[Tier 2 — MOD-pattern]**

**Truth_signal:** composite 0.83, 0 RED_FLAG, 0 SEVERE, 5 MODERATE  (long EQIX composite 0.00)

**Conviction note:** this pair's composite is driven by MODERATE_UNDERDELIVERY flags (disclosure-quality issues — typically counterparty 10-Ks silent on the claimed relationship, or quantitative claims with weak corroboration) rather than RED_FLAG or SEVERE patterns. Lower conviction than Tier 1; treat as a softer disclosure-quality trade, not a hard-contradiction short.

**Short leg (CIFR) shortability — BORROW_AT_PREMIUM:**
- price: $20.33
- market cap: $0.00B
- daily $ vol: $0.00M
- short_float: 16.8%
- **gating concerns:**
  - daily $ vol $0.00M < $1M (liquidity gate)
- _data-completeness warning: short-leg DA cache missing ['avg_volume', 'market_cap', 'beta']; shortability tier and sizing degraded._

**Long leg (EQIX) snapshot:**
- price: $1059.44
- market cap: $104.49B
- daily $ vol: $636.96M

**Beta-neutral hedge ratio:** **1.00** (short β=?, long β=0.99; default 1:1 (missing beta data))
- For every $1.00 long EQIX, short $1.00 of CIFR to be beta-neutral.

**Liquidity-based notional cap:**
- short daily $ vol: $0.00M → 5% = $0.00M
- long  daily $ vol: $636.96M → 5% = $31.85M
- **binding leg: short**, max long-leg notional ≈ $31.85M

---

### 9. SHORT **AEVA** / LONG **INVZ**  (Lidar / ADAS)  **[Tier 2 — MOD-pattern]**

**Truth_signal:** composite 0.75, 0 RED_FLAG, 0 SEVERE, 3 MODERATE  (long INVZ composite 0.14)

**Conviction note:** this pair's composite is driven by MODERATE_UNDERDELIVERY flags (disclosure-quality issues — typically counterparty 10-Ks silent on the claimed relationship, or quantitative claims with weak corroboration) rather than RED_FLAG or SEVERE patterns. Lower conviction than Tier 1; treat as a softer disclosure-quality trade, not a hard-contradiction short.

**Short leg (AEVA) shortability — BORROW_AT_PREMIUM:**
- price: $20.48
- market cap: $0.00B
- daily $ vol: $0.00M
- short_float: 18.9%
- **gating concerns:**
  - daily $ vol $0.00M < $1M (liquidity gate)
- _data-completeness warning: short-leg DA cache missing ['avg_volume', 'market_cap', 'beta']; shortability tier and sizing degraded._

**Long leg (INVZ) snapshot:**
- price: $0.74
- market cap: $0.00B
- daily $ vol: $0.00M
- _data-completeness warning: long-leg DA cache missing ['avg_volume', 'market_cap', 'beta']; notional cap and hedge ratio degraded._

**Beta-neutral hedge ratio:** **1.00** (short β=?, long β=?; default 1:1 (missing beta data))
- For every $1.00 long INVZ, short $1.00 of AEVA to be beta-neutral.

**Liquidity-based notional cap:**
- short daily $ vol: $0.00M → 5% = $0.00M
- long  daily $ vol: $0.00M → 5% = $0.00M
- **binding leg: long**, max long-leg notional ≈ $0.00M

---

### 10. SHORT **RDW** / LONG **IRDM**  (Space / satcom)  **[Tier 2 — MOD-pattern]**

**Truth_signal:** composite 0.71, 0 RED_FLAG, 1 SEVERE, 3 MODERATE  (long IRDM composite 0.12)

**Conviction note:** this pair's composite is driven by MODERATE_UNDERDELIVERY flags (disclosure-quality issues — typically counterparty 10-Ks silent on the claimed relationship, or quantitative claims with weak corroboration) rather than RED_FLAG or SEVERE patterns. Lower conviction than Tier 1; treat as a softer disclosure-quality trade, not a hard-contradiction short.

**Short leg (RDW) shortability — SHORTABLE:**
- price: $14.06
- market cap: $2.80B
- daily $ vol: $311.85M
- short_float: 14.6%

**Long leg (IRDM) snapshot:**
- price: $41.62
- market cap: $4.40B
- daily $ vol: $94.48M

**Beta-neutral hedge ratio:** **3.07** (short β=2.52, long β=0.82; beta-neutral (short_beta / long_beta))
- For every $1.00 long IRDM, short $3.07 of RDW to be beta-neutral.

**Liquidity-based notional cap:**
- short daily $ vol: $311.85M → 5% = $15.59M
- long  daily $ vol: $94.48M → 5% = $4.72M
- **binding leg: long**, max long-leg notional ≈ $4.72M

---

### 11. SHORT **OUST** / LONG **INVZ**  (Lidar / ADAS)  **[Tier 2 — MOD-pattern]**

**Truth_signal:** composite 0.67, 0 RED_FLAG, 0 SEVERE, 2 MODERATE  (long INVZ composite 0.14)

**Conviction note:** this pair's composite is driven by MODERATE_UNDERDELIVERY flags (disclosure-quality issues — typically counterparty 10-Ks silent on the claimed relationship, or quantitative claims with weak corroboration) rather than RED_FLAG or SEVERE patterns. Lower conviction than Tier 1; treat as a softer disclosure-quality trade, not a hard-contradiction short.

**Short leg (OUST) shortability — BORROW_AT_PREMIUM:**
- price: $34.86
- market cap: $0.00B
- daily $ vol: $0.00M
- short_float: 8.9%
- **gating concerns:**
  - daily $ vol $0.00M < $1M (liquidity gate)
- _data-completeness warning: short-leg DA cache missing ['avg_volume', 'market_cap', 'beta']; shortability tier and sizing degraded._

**Long leg (INVZ) snapshot:**
- price: $0.74
- market cap: $0.00B
- daily $ vol: $0.00M
- _data-completeness warning: long-leg DA cache missing ['avg_volume', 'market_cap', 'beta']; notional cap and hedge ratio degraded._

**Beta-neutral hedge ratio:** **1.00** (short β=?, long β=?; default 1:1 (missing beta data))
- For every $1.00 long INVZ, short $1.00 of OUST to be beta-neutral.

**Liquidity-based notional cap:**
- short daily $ vol: $0.00M → 5% = $0.00M
- long  daily $ vol: $0.00M → 5% = $0.00M
- **binding leg: long**, max long-leg notional ≈ $0.00M

---

### 12. SHORT **AFRM** / LONG **COF**  (Fintech lending / BNPL)  **[Tier 2 — MOD-pattern]**

**Truth_signal:** composite 0.67, 0 RED_FLAG, 0 SEVERE, 2 MODERATE  (long COF composite 0.25)

**Conviction note:** this pair's composite is driven by MODERATE_UNDERDELIVERY flags (disclosure-quality issues — typically counterparty 10-Ks silent on the claimed relationship, or quantitative claims with weak corroboration) rather than RED_FLAG or SEVERE patterns. Lower conviction than Tier 1; treat as a softer disclosure-quality trade, not a hard-contradiction short.

**Short leg (AFRM) shortability — SHORTABLE:**
- price: $65.82
- market cap: $21.92B
- daily $ vol: $372.54M
- short_float: 6.8%

**Long leg (COF) snapshot:**
- price: $187.17
- market cap: $116.47B
- daily $ vol: $924.62M

**Beta-neutral hedge ratio:** **3.55** (short β=3.69, long β=1.04; beta-neutral (short_beta / long_beta))
- For every $1.00 long COF, short $3.55 of AFRM to be beta-neutral.

**Liquidity-based notional cap:**
- short daily $ vol: $372.54M → 5% = $18.63M
- long  daily $ vol: $924.62M → 5% = $46.23M
- **binding leg: short**, max long-leg notional ≈ $18.63M

---

## Aggregate position-book considerations

**Long-side concentration (multiple pairs sharing same long):**

- **ALB** appears in 2 pairs — 2× exposure on the long side. Reduce per-pair sizing proportionally OR diversify to external long.
- **LIN** appears in 2 pairs — 2× exposure on the long side. Reduce per-pair sizing proportionally OR diversify to external long.
- **EQIX** appears in 2 pairs — 2× exposure on the long side. Reduce per-pair sizing proportionally OR diversify to external long.
- **INVZ** appears in 2 pairs — 2× exposure on the long side. Reduce per-pair sizing proportionally OR diversify to external long.

**Cleanly executable pairs (no shortability gating concerns):** 5 of 12.
**Tier mix:** 6 Tier 1 + 6 Tier 2 = 12 total.

**Reminder:** the framework's 12-month falsification window means slow-bleeding shorts that move <50% in either direction stay non-falsified. Consider an exit rule (e.g. close on +20% or after 6 months without confirmation). Tier 2 pairs in particular may benefit from a wider time window and basket sizing.