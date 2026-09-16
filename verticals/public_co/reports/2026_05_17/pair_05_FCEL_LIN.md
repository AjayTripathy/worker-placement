# SHORT **FCEL** / LONG **LIN** — Hydrogen / fuel-cell

**Tier:** TIER1   ·   **Composite (short):** 1.00   ·   **Flags (short):** 0R / 2S / 4M

**Long-leg composite:** 0.00 (in-cohort cleanest follow)

**Short-leg filing analyzed:** `0001104659-25-122302_10-K.htm`

---

## Thesis

Tier 1 (high-conviction): composite ≥ 0.75 with at least one RED_FLAG or two SEVERE findings. The trade thesis is a **factual revision** — restatement, registry contradiction, regulator action, or counterparty churn that will be visible in subsequent filings within the 12-month falsification window.

---

## Evidence (R / F(M) / M)

#### 🟠 SEVERE — `C5_reverse_split_dilution`
- **R (claim):** 1-for-30 reverse split Nov 2024 (611M -> 20.4M shares), then 25.6M new ATM shares sold in FY25 at avg $7.44 ($190.4M gross). Net share count expansion in 12 months largely offsets the reverse split's optical effect.
- **F (M-source check):** Internal corroboration only (filings_index shows 8-K dated 2025-12-30 + 424B5 same date — confirming ongoing ATM activity post fiscal year-end). 1.6M additional shares sold post-Oct-31 at $8.37 confirms continued ATM dependence. Combined with FY24 10-K disclosure of the reverse split itself, the dil
- **M (observed):** {'reverse_split_ratio': 30, 'atm_shares_fy25_millions': 25.6, 'atm_gross_proceeds_fy25_usd': 190400000, 'post_quarter_atm_shares_millions': 1.6, 'atm_capacity_remaining_usd': 1100000}
- **Why this severity:** Calibration Heuristic 10 (delisting / going-concern fingerprints, elevated weight for hydrogen names). FCEL has done multiple reverse splits historically (subject-note confirms). The pattern — large reverse split, then immediately re-dilute via ATM at the higher per-share price, then exhaust the ATM ($1.1M remaining = effectively zero) — is the textbook hydrogen / EV-SPAC capital-stack treadmill. Combined with chronic negative gross margins (-16.7% FY25; -32.0% FY24; gross loss every year), continuous outside-financing requirement (explicitly required per the 10-K liquidity-management list), a

#### 🟠 SEVERE — `C8_backlog_decline`
- **R (claim):** Product backlog fell from $111.3M (Oct 2024) to $66.2M (Oct 2025), -41% YoY, while reported revenue grew via GGE module-replacement consumption.
- **F (M-source check):** Internal disclosure consistency — no external query needed; the backlog roll-forward arithmetic is in the filing. Combined with Claim C1 (single-customer concentration) and C3 (zero hyperscaler contracts) this is fully cross-validated.
- **M (observed):** {'product_backlog_oct2024_usd_millions': 111.3, 'product_backlog_oct2025_usd_millions': 66.2, 'yoy_change_pct': -40.5, 'service_backlog_oct2025_usd_millions': 162.4, 'service_backlog_oct2024_usd_millions': 174.2}
- **Why this severity:** Calibration Heuristic 3 + 11 applied. Headline revenue growth (+41%) is misleading: it is the mechanical recognition of pre-existing GGE LTSA modules (22 modules in FY25 vs 6 in FY24), not new commercial momentum. The leading indicator — product backlog — fell 41%. At current burn-down rate ($69M of product revenue, $66M backlog remaining), the company has roughly ONE YEAR of product revenue runway from the existing book before the GGE replacement cycle exhausts. With no signed hyperscaler / data-center / utility offtake to replace it (Claim C3), and the data-center marketing pivot unsubstanti

#### 🟡 MOD — `C1_GGE_korea_concentration`
- **R (claim):** FCEL recognized $66.0M of $69.1M FY25 product revenue under LTSA with Gyeonggi Green Energy (Hwaseong-si, S. Korea, 58.8 MW). Single-customer concentration.
- **F (M-source check):** edgar_fts.query_fulltext('Gyeonggi') => 402 hits, top filing is FCEL's own 8-K (2023-07-28). GGE is a real Korean IPP affiliate (Korea Southern Power related). The relationship is internally consistent and corroborated by FCEL's own historic 8-K disclosures.
- **M (observed):** {'gyeonggi_total_hits': 402, 'fcel_top_match': True}
- **Why this severity:** The customer / project is real and verifiable. However, 95.5% product-revenue concentration in a single Korean module-replacement contract is a structural fragility: revenue 'growth' of 169% is mechanical (counted modules delivered per LTSA cadence) not new-customer acquisition. Product backlog fell from $111.3M to $66.2M YoY (Claim C8), implying the GGE pipeline is being consumed faster than replaced. Calibration Heuristic 11 (revenue-recognition pattern): this is concentrated 'bookings burn-down' rather than diversified commercial expansion. Score MODERATE — claim is factually true but mater

#### 🟡 MOD — `C2_EXIM_25m_financing`
- **R (claim):** FCEL closed $25M EXIM debt Nov 2025 at 5.29% (7yr), with covenant cash-floor cut from $100M to $55M.
- **F (M-source check):** usaspending.query_recipient_contracts(FuelCell Energy) => 0 awards (EXIM financing is debt, not USAspending grants). usaspending.query_recipient_grants => 10 DOE awards including DEEE0009290 ($8M), DEFE0026199 ($6.3M), DEAR0000808 ($4.6M) — confirming FCEL is a real DOE contractor.
- **M (observed):** {'contract_awards': 0, 'grant_awards': 10, 'top_grant_amount_usd': 8000000, 'agencies': ['Department of Energy']}
- **Why this severity:** Financial transaction itself is self-reported and corroborated by SEC filings. However, the simultaneous 45% reduction in minimum cash covenant ($100M -> $55M) suggests EXIM concession was necessary to give FCEL liquidity headroom — a tell that the company expected its FY26 cash position to test the prior covenant. Combined with $190M ATM raises in FY25 and 1-for-30 reverse split history, this $25M is incremental life-extension capital, not growth capital. Score MODERATE: claim is true, but interpretation is distress-adjacent.

#### 🟡 MOD — `C3_data_center_pivot`
- **R (claim):** FCEL repositions carbonate modules as the on-site behind-the-meter hyperscaler-data-center solution, marketing modular 1.25 MW blocks scalable to 'hundreds of megawatts'.
- **F (M-source check):** edgar_fts.query_fulltext('FuelCell Energy', cik=AMZN/MSFT/META/GOOGL): Amazon=0, Microsoft=0, Meta=0, Alphabet=0 hits.
- **M (observed):** {'AMZN_hits': 0, 'MSFT_hits': 0, 'META_hits': 0, 'GOOGL_hits': 0}
- **Why this severity:** Calibration Heuristic 3 (planned vs operational) + Rule 7 with extra weight. The 10-K dedicates substantial 'Market Opportunity' real-estate to AI data-center power demand but discloses ZERO named hyperscaler contract, LOI, MOU, or even a pilot deployment. Annualized production rate is 31.5 MW — a single 50 MW data-center customer would 1.6x consume the entire factory. The pivot is pure marketing tier with no Stage Ladder progression past 'announced opportunity'. Bloom Energy (BE) actually has signed and disclosed AEP/Equinix/data-center deals; FCEL has none. The disconnect between the size of
- **Audit:** originally `SEVERE_UNDERDELIVERY` — adjusted by rescoring.

#### 🟡 MOD — `C4_toyota_h2_project`
- **R (claim):** FCEL operates 20-year Toyota tri-gen hydrogen+power project at Port of Long Beach; fixed-price fuel hedge expires May 2026; listed among four projects with material fuel sourcing risk.
- **F (M-source check):** edgar_fts.query_fulltext('Tri-gen') => 38 hits, dominated by FCEL's own 8-Ks (2021-04-08, 2021-06-10, 2021-09-14, 2021-12-29, 2023-09-11). Toyota Motor Corp (CIK 0001094517) 20-F => 0 hits for 'FuelCell Energy' (expected — Toyota is a $200B+ revenue parent; a single tri-gen project at TMNA-Long Beac
- **M (observed):** {'trigen_hits': 38, 'toyota_parent_hits': 0, 'fcel_self_8k_hits': 5}
- **Why this severity:** Project itself is real (multiple FCEL 8-Ks document construction, completion, hydrogen production milestones). However, the financial-statement note flags the Toyota project among four with 'fuel sourcing risk' and explicitly warns of 'further charges for the Toyota project asset' if fuel cannot be secured on favorable terms post-May 2026 — i.e., the hedge that made the project economic is rolling off RIGHT AT the cutoff date (May 2026 = the cutoff month). This is an explicit forward-impairment-risk disclosure embedded in the boilerplate. Score MODERATE: project is operational and corroborated

---

## Execution

### Shortability
- **Tier:** `SHORTABLE`
- Price: $21.36
- Market cap: $1.13B
- Daily $ volume: $94.41M
- Short float: 8.7%

### IBKR borrow
- **Latest fee:** **0.68%** annualized (2026-05-15)
- Shares available: 5.0M
- 30-day avg: 1.08%
- 30-day max: 1.39%
- Trend: **stable**

### Hedge ratio
- **Beta-neutral:** **3.22×** (short β=2.38, long β=0.74)
- _Method: beta-neutral (short_beta / long_beta)_
- For every $1 long LIN, short $3.22 of FCEL.

### Notional cap (5% daily $ vol)
- Short daily $ vol: $94.41M → cap $4.72M
- Long daily $ vol: $1209.60M → cap $60.48M
- **Binding leg: short**
- **Max long-leg notional:** $4.72M

### Suggested conservative entry (30% of cap)
- Long LIN: **$1.42M**
- Short FCEL: **$4.55M**
- Annualized borrow carry on short: **$31,113/yr** (0.6831% × $4.55M)

---

## Risk + falsification

- **Falsification window:** 12 months from cutoff (2026-05-16). Pair survives if either leg moves >50% against the thesis OR the divergence claim is corroborated post-cutoff and the pair returns ~0.
- **Suggested exit rule:** close on +20% adverse move on the short leg, OR 6 months without confirming evidence, whichever comes first.
- **Hedge ratio reliability:** if either β was missing (default 1:1 fallback), the hedge is approximate. Watch correlation drift quarterly.

## Pair metadata
- Theme: Hydrogen / fuel-cell
- Generated: 2026-05-17 from frozen position_sizing.json + borrow_rates.json