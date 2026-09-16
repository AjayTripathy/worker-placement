# SHORT **AEVA** / LONG **INVZ** — Lidar / ADAS

**Tier:** TIER2   ·   **Composite (short):** 0.75   ·   **Flags (short):** 0R / 0S / 3M

**Long-leg composite:** 0.14 (in-cohort cleanest follow)

**Short-leg filing analyzed:** `0001193125-26-116518_10-K.txt`

---

## Thesis

Tier 2 (lower-conviction, MOD-pattern): composite 0.60–1.20 with ≥2 MODERATE findings and no RED_FLAG. The thesis is a **disclosure-quality re-rating** — the market eventually penalizes the multiple applied to filings where claims don't independently verify. Holding period typically 6–12 months; basket sizing preferred over single-name conviction.

---

## Evidence (R / F(M) / M)

#### 🟡 MOD — `AEVA-1`
- **R (claim):** Selected by a top European passenger OEM (unnamed).
- **F (M-source check):** n/a (counterparty unnamed)
- **M (observed):** OEM is not identified in filing; impossible to cross-check against any OEM 10-K/20-F per Heuristic 7. Disclosure is gated as 'strategic initiative' that 'may not be successful' — pre-SOP / pre-revenue language per Heuristic 3. No SOP date, no platform name, no contract value disclosed.
- **Why this severity:** Pre-SOP design-win-style claim with anonymized counterparty and no platform/SOP date triggers Calibration Heuristic 3 (planned vs operational) — disclosure-quality issue without rising to a hard contradiction since the OEM is not named.

#### 🟡 MOD — `AEVA-3`
- **R (claim):** $100M Apollo convertible notes due 2032 at 4.375%, closed Nov 6, 2025.
- **F (M-source check):** q3_apollo_notes
- **M (observed):** EDGAR full-text search for 'Aeva' restricted to Apollo Global Securities CIK 0001858681 returns 0 hits (private credit lenders typically do not disclose individual investments). Cash flow shows $96.9M of convertible note proceeds, corroborating issuance. However: (a) intent to pay interest in shares of common stock, (b) accumulated deficit of $757.3M, (c) cash and marketable securities only $121.9
- **Why this severity:** Note issuance verified via own cash flow; transaction itself is real. Severity elevated to MODERATE due to (i) Heuristic 10 — 25-NSE filed 2026-03-11 in filings_index plus prior 1-for-5 reverse split (March 2024) constitute a delisting fingerprint, and (ii) interest-in-stock structure plus $757.3M accumulated deficit signal future dilution risk that the marketing-tier 'sufficient for at least 12 months' framing understates.

#### 🟡 MOD — `AEVA-5`
- **R (claim):** Three customers = 72% of AR (FY2025); customers undisclosed.
- **F (M-source check):** n/a (customers anonymized)
- **M (observed):** Concentration disclosure is in Note 1; customers are not identified. Total FY2025 revenue is $18.1M (vs $9.1M FY2024) and 26% is from outside the US. With customers unnamed, counterparty corroboration per Heuristic 7 is impossible. Gross loss still negative ($660K) at this revenue scale.
- **Why this severity:** Single-customer-default risk is material at $18M revenue with 72% AR concentration in 3 customers — disclosure-quality issue (anonymized counterparties) combined with pre-commercial revenue scale rates MODERATE rather than UNVERIFIABLE because the concentration itself is a confirmed risk factor.

---

## Execution

### Shortability
- **Tier:** `BORROW_AT_PREMIUM`
- Price: $20.48
- Market cap: $0.00B
- Daily $ volume: $0.00M
- Short float: 18.9%
- ⚠ daily $ vol $0.00M < $1M (liquidity gate)

### IBKR borrow
- **Latest fee:** **0.43%** annualized (2026-05-15)
- Shares available: 0.8M
- 30-day avg: 0.54%
- 30-day max: 0.66%
- Trend: **stable**

### Hedge ratio
- **Beta-neutral:** **1.00×** (short β=?, long β=?)
- _Method: default 1:1 (missing beta data)_
- For every $1 long INVZ, short $1.00 of AEVA.

### Notional cap (5% daily $ vol)
- Short daily $ vol: $0.00M → cap $0.00M
- Long daily $ vol: $0.00M → cap $0.00M
- **Binding leg: long**
- **Max long-leg notional:** $0.00M

### Suggested conservative entry (30% of cap)
- Long INVZ: **$0.00M**
- Short AEVA: **$0.00M**
- Annualized borrow carry on short: **$0/yr** (0.4333% × $0.00M)

---

## Risk + falsification

- **Falsification window:** 12 months from cutoff (2026-05-16). Pair survives if either leg moves >50% against the thesis OR the divergence claim is corroborated post-cutoff and the pair returns ~0.
- **Suggested exit rule:** close on +20% adverse move on the short leg, OR 6 months without confirming evidence, whichever comes first.
- **Hedge ratio reliability:** if either β was missing (default 1:1 fallback), the hedge is approximate. Watch correlation drift quarterly.

## Pair metadata
- Theme: Lidar / ADAS
- Generated: 2026-05-17 from frozen position_sizing.json + borrow_rates.json