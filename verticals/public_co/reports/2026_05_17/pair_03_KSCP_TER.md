# SHORT **KSCP** / LONG **TER** — Robotics / autonomy

**Tier:** TIER1   ·   **Composite (short):** 1.44   ·   **Flags (short):** 3R / 0S / 4M

**Long-leg composite:** 0.11 (in-cohort cleanest follow)

**Short-leg filing analyzed:** `0001104659-26-036240_10-K.txt`

---

## Thesis

Tier 1 (high-conviction): composite ≥ 0.75 with at least one RED_FLAG or two SEVERE findings. The trade thesis is a **factual revision** — restatement, registry contradiction, regulator action, or counterparty churn that will be visible in subsequent filings within the 12-month falsification window.

---

## Evidence (R / F(M) / M)

#### 🔴 RED — `KSCP-C2`
- **R (claim):** Going concern: $227.0M accumulated deficit, $33.8M net loss, $30.3M cash used in operating activities for FY2025; auditor issued substantial-doubt going-concern qualifier.
- **F (M-source check):** edgar_fts.query_fulltext (KSCP own filings) + 10-K/10-Q text
- **M (observed):** {'accumulated_deficit_M': 227.0, 'FY2025_op_cash_burn_M': 30.3, 'YE2025_cash_M': 20.6, 'Q1_2026_op_burn_M': 11.6, 'Mar31_2026_cash_M': 11.4, 'implied_runway_quarters': '<3 without new ATM issuance'}
- **Why this severity:** Going-concern qualifier is explicit and reaffirmed in Q1 2026. Cash burn accelerated QoQ (from ~$7.6M/quarter FY2025 avg to $11.6M in Q1 2026, partly due to KSF acquisition cash outflow of $6.1M). Company is structurally dependent on ATM equity issuance — see C8.

#### 🔴 RED — `KSCP-C5`
- **R (claim):** Total order backlog of approximately $3.1M as of March 24, 2026 ($0.6M ASR + $2.5M ECD).
- **F (M-source check):** internal_disclosure + cross-check via Q1 2026 10-Q (no backlog uplift disclosed)
- **M (observed):** {'total_backlog_M': 3.1, 'ASR_backlog_M': 0.6, 'ECD_backlog_M': 2.5, 'backlog_to_FY2025_revenue_pct': 27}
- **Why this severity:** Tiny $0.6M ASR backlog is direct quantitative contradiction of the 'building the nation's first Autonomous Security Force' positioning. With ASR depreciation alone at $2.0M/yr and ASR-related service revenue ~$8.0M total, $0.6M of new ASR orders implies the install-base lift is decelerating. Combined with the going-concern overhang, this is a HARD signal of forward-revenue weakness in the core platform.

#### 🔴 RED — `KSCP-C8`
- **R (claim):** ATM offering program produced $42.8M FY2025 + $9.0M Q1 2026 + $3.3M April-May 8 2026 ($55M+ net in 16 months); $18.3M remaining on shelf at May 8 2026. Class A shares grew from 4.07M (YE2024) to 12.19M (YE2025) and ~14.9M+ post Event Risk issuance.
- **F (M-source check):** internal_filings + edgar_fts (KSCP S-3, 424B5, 8-K)
- **M (observed):** {'ATM_net_FY2025_M': 42.8, 'ATM_net_Q1_2026_M': 9.0, 'ATM_net_AprMay8_2026_M': 3.3, 'shelf_remaining_M_May8': 18.3, 'share_count_YE2024_M': 4.07, 'share_count_YE2025_M': 12.19, 'share_count_post_KSF_M_est': 14.91, 'dilution_multiplier_15mo': '~3.7x'}
- **Why this severity:** ~3.7x share-count expansion in 15 months funded almost entirely by ATM dilution — this IS the going-concern remediation. Combined with multiple historical reverse-splits (per cohort metadata and the 'fractional share adjustment due to reverse stock split' line in FY2024 equity rollforward), the structural dependence on ATM issuance against a declining ASR backlog is a classic distress fingerprint per Calibration 10. Listed price reference ($10.00 Nov-2024 offering) implies ATM issuance well above $10/share now, but each issuance is highly dilutive given the low share count base.

#### 🟡 MOD — `KSCP-C3`
- **R (claim):** One client = 19% of FY2025 revenue (zero such clients in 2024); two clients = 28% and 11% of AR at YE2025.
- **F (M-source check):** edgar_fts.query_fulltext(search_term='Knightscope', forms='10-K')
- **M (observed):** {'total_10K_hits': 57, 'non_KSCP_filers_in_top_results': 0, 'concentrated_client_revenue_est_M': 2.15, 'ar_concentration_pct': [28, 11]}
- **Why this severity:** Per Calibration 7, absence of counterparty disclosure for a $2M customer is NOT a hard contradiction — too immaterial to trigger 10-K mention on the customer side. Score MODERATE because the named-customer transparency is missing and the new concentration risk (zero to 19% YoY) suggests a single-deal lift rather than broad commercial scaling.

#### 🟡 MOD — `KSCP-C4`
- **R (claim):** K7 ASR remains in development; commercial production not expected until late 2026 or early 2027; K7 contributed zero revenue in 2025.
- **F (M-source check):** uspto_odp.query_assignee + filing text
- **M (observed):** {'K7_FY2025_revenue': 0, 'commercial_production_target': 'late 2026 / early 2027', 'uspto_granted_pre_cutoff': 11}
- **Why this severity:** Per Calibration 3 (planned vs operational): K7 is still at pre-commercial stage. The repeated push of commercial production timeline (now 'late 2026 or early 2027') is a soft-deferral pattern consistent with pilots-as-PR risk. Not a hard fabrication — the company is transparent that K7 has $0 revenue. Score MODERATE: company is honest about the gap but the new-platform optionality is being relied on to justify the R&D spike (R&D +77% YoY to $12.5M, 110% of revenue).

#### 🟡 MOD — `KSCP-C6`
- **R (claim):** Acquired Event Risk LLC (KSF) on Feb 27, 2026 for ~$18M total consideration; recorded $7.7M goodwill + $15.5M customer-relationships intangible.
- **F (M-source check):** edgar_fts.query_fulltext(search_term='Event Risk', cik=KSCP)
- **M (observed):** {'KSCP_filings_referencing_Event_Risk': 9, 'total_consideration_M': 18.0, 'goodwill_M': 7.7, 'customer_relationships_intangible_M': 15.5, 'deferred_cash_M': 4.0, 'shares_issued': 1724418}
- **Why this severity:** Acquisition is verified via 8-K/A with full Reg S-X financial statements (filed 2026-05-15). However, two cautions per Calibration 4: (a) for a $30M-burn microcap with going-concern qualifier to pay ~$11M cash+debt-repay+deferred (plus shares) for a security-guarding services business is a pivot away from the autonomous-robot pure-play, with $15.5M of intangibles (customer relationships) representing ~86% of purchase price — high reliance on retention of acquired customer book. Score MODERATE: real transaction but quality / strategic-fit risk is elevated.

#### 🟡 MOD — `KSCP-C9`
- **R (claim):** Knightscope serves government clients (per cohort metadata, municipal/private-security customers).
- **F (M-source check):** usaspending.query_recipient_contracts(recipient='Knightscope', 2020-2026)
- **M (observed):** {'n_awards': 5, 'total_amount_USD': 241512, 'agencies': {'VA': 2, 'DoD': 2, 'DoI': 1}, 'largest_award_USD': 88760, 'share_of_FY2025_revenue_pct': 2.1}
- **Why this severity:** Per Calibration 5 + 7: USAspending captures federal contracts. There IS one DoD/Air Force ASR contract ($73K — directly on-mission), which validates the existence of federal ASR pilot activity — score is NOT RED. However, $241K cumulative over 5+ years vs. company emphasis on 'government' as a market segment shows federal channel is sub-material. Municipal/private-security customers (the bulk of the cohort metadata's named segment) would not appear in USAspending; this is a true UNVERIFIABLE for municipal, but the federal slice is verifiably tiny. Score MODERATE: claim is technically true but 

---

## Execution

### Shortability
- **Tier:** `HARD_TO_BORROW_OR_RETAIL_RESTRICTED`
- Price: $2.95
- Market cap: $0.05B
- Daily $ volume: $1.54M
- Short float: 18.5%
- ⚠ price $2.95 < $5 (most retail brokers prohibit short)
- ⚠ market cap $48M < $50M (thin / no borrow expected)

### IBKR borrow
- ⚠ Not in IBKR lending universe (status_444). Genuine hard-to-borrow; specialty borrow desk required.

### Hedge ratio
- **Beta-neutral:** **0.71×** (short β=1.27, long β=1.78)
- _Method: beta-neutral (short_beta / long_beta)_
- For every $1 long TER, short $0.71 of KSCP.

### Notional cap (5% daily $ vol)
- Short daily $ vol: $1.54M → cap $0.08M
- Long daily $ vol: $1169.06M → cap $58.45M
- **Binding leg: short**
- **Max long-leg notional:** $0.08M

### Suggested conservative entry (30% of cap)
- Long TER: **$0.02M**
- Short KSCP: **$0.02M**

---

## Risk + falsification

- **Falsification window:** 12 months from cutoff (2026-05-16). Pair survives if either leg moves >50% against the thesis OR the divergence claim is corroborated post-cutoff and the pair returns ~0.
- **Suggested exit rule:** close on +20% adverse move on the short leg, OR 6 months without confirming evidence, whichever comes first.
- **Hedge ratio reliability:** if either β was missing (default 1:1 fallback), the hedge is approximate. Watch correlation drift quarterly.

## Pair metadata
- Theme: Robotics / autonomy
- Generated: 2026-05-17 from frozen position_sizing.json + borrow_rates.json