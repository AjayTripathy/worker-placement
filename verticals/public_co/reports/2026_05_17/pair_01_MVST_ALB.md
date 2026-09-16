# SHORT **MVST** / LONG **ALB** — Solid-state battery

**Tier:** TIER1   ·   **Composite (short):** 1.57   ·   **Flags (short):** 2R / 2S / 1M

**Long-leg composite:** 0.12 (in-cohort cleanest follow)

**Short-leg filing analyzed:** `0001628280-26-018264_10-K.txt`

---

## Thesis

Tier 1 (high-conviction): composite ≥ 0.75 with at least one RED_FLAG or two SEVERE findings. The trade thesis is a **factual revision** — restatement, registry contradiction, regulator action, or counterparty churn that will be visible in subsequent filings within the 12-month falsification window.

---

## Evidence (R / F(M) / M)

#### 🔴 RED — `C5`
- **R (claim):** Loss of conditional DOE grant; subject of stockholder demands and Schelling securities class action.
- **F (M-source check):** usaspending.query_recipient_contracts / grants for DOE award verification
- **M (observed):** Only $499,972 in cumulative DOE-grant assistance; no large-dollar DOE LPO / grant present
- **Why this severity:** Heuristic 5 (USAspending DOE coverage) — major DOE LPO and grant awards DO show up. The absence of any large MVST DOE award post-cutoff confirms the rescission. The company itself acknowledges loss of the conditional grant and resulting securities litigation, with class certification briefing scheduled for June-October 2026. This is a hard adverse signal: a flagship US-policy win that did not materialize, plus active securities-fraud allegations centered on that very disclosure. RED_FLAG_NEGATIVE — both the operational loss and the active litigation overhang.

#### 🔴 RED — `C6`
- **R (claim):** Going-concern doubt initially raised; $169.2M cash (only $105M unrestricted; $62.2M trapped in China + Europe subsidiaries); $140.9M convertible loan at SOFR+9.75%; stock at $2.10 vs $11.50 warrant strike.
- **F (M-source check):** edgar_fts.query_fulltext for capital-event 8-K cadence; self-disclosure of going concern
- **M (observed):** Going-concern doubt + distressed convertible coupon + trapped foreign cash + sub-$3 share price
- **Why this severity:** Heuristic 10 (delisting / going-concern fingerprints) — multiple distress markers present. Critically, $62.2M of cash is held in China/Europe subsidiaries and is NOT readily repatriable due to PRC FX controls + adverse US tax — effectively the US parent has only ~$43M of usable cash against $140.9M of distressed convertible debt and $19.95M+ in unpaid US construction liens. The going-concern qualification was 'alleviated' contingent on assumed refinancing and ATM dilution — both of which compound dilution risk for equity holders. RED_FLAG_NEGATIVE.

#### 🟠 SEVERE — `C4`
- **R (claim):** Clarksville, TN 577,000 sq ft owned facility for ESS/LFP cell production; construction slowed Q4 2023 due to financing; $19.95M DPR Construction lien dispute; $23.6M total liens received.
- **F (M-source check):** epa_frs.query_facilities for EPA-regulated factory existence
- **M (observed):** Zero Microvast operating facilities in EPA FRS for TN; only a TVA utility delivery point exists
- **Why this severity:** Heuristic 1 (EPA FRS scope) — battery production facilities ARE EPA-regulated for hazmat / air permits. Absence of a Microvast-named EPA-permitted facility in TN, despite a 577,000 sq ft 'owned manufacturing' property, confirms the structure exists but is NOT operating as a permitted battery factory. The disclosed mechanics liens ($23.6M), WARN-Act layoff class action, $19.95M unpaid contractor dispute, and impairment-restatement all corroborate that Clarksville is a stranded asset, not a producing US factory. SEVERE_UNDERDELIVERY relative to the original 2021 promise of US-domestic Clarksvill

#### 🟠 SEVERE — `C9`
- **R (claim):** Restatement of Q2 2024 and Q3 2024 quarterly financial statements due to Clarksville facility impairment error; material weakness in internal controls.
- **F (M-source check):** edgar_fts.query_fulltext for restatement / 10-Q/A filings
- **M (observed):** Restatement confirmed via 10-Q/A filing; multiple restatement references in MVST's own filings
- **Why this severity:** Restatement is corroborated by the actual 10-Q/A filing in EDGAR. Heuristic 11 (revenue-recognition pattern) is adjacent — material weakness + restatement focused on the SAME asset (Clarksville) that is the subject of mechanics liens, WARN-Act layoff settlement, and construction-dispute litigation. This is a clustered red-flag pattern: bad accounting and bad operating outcome on the same flagship US asset. Combined with the prior 2021 SPAC-period restatement of Tuscan/Microvast financials, this is a repeat-restater pattern. SEVERE_UNDERDELIVERY for governance and controls.

#### 🟡 MOD — `C7`
- **R (claim):** Order backlog of $196.1M as of YE2025, majority expected fulfilled in 2026 and 2027.
- **F (M-source check):** edgar_fts.query_fulltext for top-tier US OEM corroboration
- **M (observed):** No US OEM (Ford/GM) disclosure of Microvast as a counterparty
- **Why this severity:** MVST does not claim Ford or GM as customers, so the Ford/GM absence is not a contradiction. However, $196.1M of backlog (~12 months of revenue at current run rate) with no segmentation between firm POs and indicative orders, and 'majority' fulfilled across 2026 AND 2027 (i.e., back-end loaded), against a going-concern backdrop and Huzhou Phase 3.2 ramp risk, is soft. Heuristic 11 (revenue-recognition pattern) — at MVST's stage with material restatement history, an undifferentiated backlog should be discounted. MODERATE_UNDERDELIVERY for disclosure granularity, not for fabricated revenue.

---

## Execution

### Shortability
- **Tier:** `BORROW_AT_PREMIUM`
- Price: $1.42
- Market cap: $0.47B
- Daily $ volume: $6.26M
- Short float: 10.2%
- ⚠ price $1.42 < $5 (most retail brokers prohibit short)

### IBKR borrow
- **Latest fee:** **0.48%** annualized (2026-05-15)
- Shares available: 4.8M
- 30-day avg: 0.45%
- 30-day max: 0.55%
- Trend: **stable**

### Hedge ratio
- **Beta-neutral:** **2.61×** (short β=3.50, long β=1.34)
- _Method: beta-neutral (short_beta / long_beta)_
- For every $1 long ALB, short $2.61 of MVST.

### Notional cap (5% daily $ vol)
- Short daily $ vol: $6.26M → cap $0.31M
- Long daily $ vol: $384.21M → cap $19.21M
- **Binding leg: short**
- **Max long-leg notional:** $0.31M

### Suggested conservative entry (30% of cap)
- Long ALB: **$0.09M**
- Short MVST: **$0.25M**
- Annualized borrow carry on short: **$1,171/yr** (0.4773% × $0.25M)

---

## Risk + falsification

- **Falsification window:** 12 months from cutoff (2026-05-16). Pair survives if either leg moves >50% against the thesis OR the divergence claim is corroborated post-cutoff and the pair returns ~0.
- **Suggested exit rule:** close on +20% adverse move on the short leg, OR 6 months without confirming evidence, whichever comes first.
- **Hedge ratio reliability:** if either β was missing (default 1:1 fallback), the hedge is approximate. Watch correlation drift quarterly.

## Pair metadata
- Theme: Solid-state battery
- Generated: 2026-05-17 from frozen position_sizing.json + borrow_rates.json