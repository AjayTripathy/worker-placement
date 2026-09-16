# SHORT **OUST** / LONG **INVZ** — Lidar / ADAS

**Tier:** TIER2   ·   **Composite (short):** 0.67   ·   **Flags (short):** 0R / 0S / 2M

**Long-leg composite:** 0.14 (in-cohort cleanest follow)

**Short-leg filing analyzed:** `0001628280-26-013313_10-K.txt`

---

## Thesis

Tier 2 (lower-conviction, MOD-pattern): composite 0.60–1.20 with ≥2 MODERATE findings and no RED_FLAG. The thesis is a **disclosure-quality re-rating** — the market eventually penalizes the multiple applied to filings where claims don't independently verify. Holding period typically 6–12 months; basket sizing preferred over single-name conviction.

---

## Evidence (R / F(M) / M)

#### 🟡 MOD — `OUST-2`
- **R (claim):** DF solid-state lidar designed for automotive OEM ADAS production wins.
- **F (M-source check):** q2_oem_aptiv
- **M (observed):** EDGAR FTS: 0 hits for 'Ouster' in Aptiv (CIK 0001521332) 10-K/20-F/8-K filings.
- **Why this severity:** Heuristic 3 (planned vs operational): filing language is 'prototypes' / 'will meet requirements' / 'positioned to capture' — pre-SOP and no named OEM design-win or SOP date; no Tier-1 (Aptiv) counterparty corroboration. Claim is aspirational, not a hard contradiction (no series-production claim asserted), so MODERATE rather than RED.

#### 🟡 MOD — `OUST-5`
- **R (claim):** $211.2M liquidity supports >=12 months operations despite $973.4M accumulated deficit.
- **F (M-source check):** n/a (filing-internal financials)
- **M (observed):** FY2025 net loss $60.4M; FY2024 net loss $97.0M; operating cash burn $40.0M FY25; $97.5M raised via ATM in FY25 at $20.88/share; ATM remaining capacity only $2.5M; reverse stock split referenced; accumulated deficit $973.4M.
- **Why this severity:** Heuristic 10-adjacent: while no Form 15 / 25-NSE filed, the ATM is essentially exhausted ($2.5M remaining of $100M), historical reliance on equity issuance to fund losses, and large accumulated deficit relative to liquidity make the 12-month runway dependent on continued operating-loss reduction or new financing. Disclosure-quality issue: 'adequate for 12 months' is true under current burn but understates dilution/financing risk implicit in covering recurring losses. MODERATE.

---

## Execution

### Shortability
- **Tier:** `BORROW_AT_PREMIUM`
- Price: $34.86
- Market cap: $0.00B
- Daily $ volume: $0.00M
- Short float: 8.9%
- ⚠ daily $ vol $0.00M < $1M (liquidity gate)

### IBKR borrow
- **Latest fee:** **0.27%** annualized (2026-05-15)
- Shares available: 1.3M
- 30-day avg: 0.28%
- 30-day max: 0.38%
- Trend: **stable**

### Hedge ratio
- **Beta-neutral:** **1.00×** (short β=?, long β=?)
- _Method: default 1:1 (missing beta data)_
- For every $1 long INVZ, short $1.00 of OUST.

### Notional cap (5% daily $ vol)
- Short daily $ vol: $0.00M → cap $0.00M
- Long daily $ vol: $0.00M → cap $0.00M
- **Binding leg: long**
- **Max long-leg notional:** $0.00M

### Suggested conservative entry (30% of cap)
- Long INVZ: **$0.00M**
- Short OUST: **$0.00M**
- Annualized borrow carry on short: **$0/yr** (0.2693% × $0.00M)

---

## Risk + falsification

- **Falsification window:** 12 months from cutoff (2026-05-16). Pair survives if either leg moves >50% against the thesis OR the divergence claim is corroborated post-cutoff and the pair returns ~0.
- **Suggested exit rule:** close on +20% adverse move on the short leg, OR 6 months without confirming evidence, whichever comes first.
- **Hedge ratio reliability:** if either β was missing (default 1:1 fallback), the hedge is approximate. Watch correlation drift quarterly.

## Pair metadata
- Theme: Lidar / ADAS
- Generated: 2026-05-17 from frozen position_sizing.json + borrow_rates.json