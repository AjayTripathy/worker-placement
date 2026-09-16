# SHORT **CIFR** / LONG **EQIX** — AI-DC / crypto-pivot

**Tier:** TIER2   ·   **Composite (short):** 0.83   ·   **Flags (short):** 0R / 0S / 5M

**Long-leg composite:** 0.00 (in-cohort cleanest follow)

**Short-leg filing analyzed:** `0001819989-26-000009_10-K.txt`

---

## Thesis

Tier 2 (lower-conviction, MOD-pattern): composite 0.60–1.20 with ≥2 MODERATE findings and no RED_FLAG. The thesis is a **disclosure-quality re-rating** — the market eventually penalizes the multiple applied to filings where claims don't independently verify. Holding period typically 6–12 months; basket sizing preferred over single-name conviction.

---

## Evidence (R / F(M) / M)

#### 🟡 MOD — `C1`
- **R (claim):** 15-year, 300 MW Black Pearl HPC lease with Amazon Web Services; phased delivery commencing 2026.
- **F (M-source check):** Amazon EDGAR counterparty disclosure of Cipher / Black Pearl
- **M (observed):** 0/0/0 hits in Amazon filings 2025-01-01 to 2026-05-16 (Anthropic baseline = 23 hits, Trainium = 13 hits, so FTS index is reachable). Sanity: Amazon does not generally name individual colocation lessors in 10-K (no hits for 'Applied Digital', 'CoreWeave' either, with caveats due to the FTS API returning None for some short terms).
- **Why this severity:** Lease is real and disclosed in Cipher's 10-K with specificity (Cipher Black Pearl LLC subsidiary, 15-year term, 300 MW, phased delivery). Counterparty side: Amazon doesn't name Cipher in its filings — but Amazon rarely names individual DC lessors and a 300 MW lease (vs Amazon's hundreds of GW of global DC footprint) may be below materiality thresholds for named disclosure. NOT a hard contradiction. However, Calibration Heuristics 3 (stage ladder) and 9 (TCV vs current revenue) apply with weight: $0 current-period HPC revenue at Black Pearl (BTC mining ceased early 2026, lease rent commencement

#### 🟡 MOD — `C2`
- **R (claim):** Long-term HPC lease with Fluidstack USA II Inc. at 300 MW Barber Lake Facility; backstopped by Google LLC via Lease Recognition Agreement plus Google Warrants (exercise period to Sept 2030).
- **F (M-source check):** Alphabet (GOOGL CIK 0001652044) counterparty disclosure of Fluidstack / Cipher / Barber Lake
- **M (observed):** 0/0/0/0 hits in Alphabet filings 2025-01-01 to 2026-05-16 (Anthropic baseline = 4 hits, TPU = 4, Waymo = 11, so FTS index works). Fluidstack is a private neocloud — UNVERIFIABLE directly per Heuristic 7 (CoreWeave exception extends to other private neoclouds).
- **Why this severity:** The structure is layered: Cipher's primary tenant is a private neocloud (Fluidstack), with Google providing only a contingent backstop. Google's commitment is sized to the lease payments and is presumably below Alphabet's materiality threshold (Alphabet does not disclose individual lease-backstop obligations of this scale). Calibration Heuristics 3 + 9 apply: rent commencement targeted Sept 30, 2026 (Phase I) and Jan 31, 2027 (Phase II). $0 current-period HPC revenue from this site. The Google Warrants are an equity instrument issued to Google (a non-cash consideration received for services wo

#### 🟡 MOD — `C3`
- **R (claim):** 4.2 GW portfolio across 10 sites: 207 MW operating BTC (Odessa); 600 MW HPC under development (Barber Lake 300 + Black Pearl 300); 3.4 GW pipeline across seven Texas sites + one Ohio site.
- **F (M-source check):** Asymmetric mention test for MW-scale claims across EDGAR (any filer)
- **M (observed):** External validation is effectively zero — virtually 100% of mentions trace back to Cipher's own SEC filings. No utility / ERCOT filer, no hyperscaler, no co-developer references Cipher's MW figures.
- **Why this severity:** 207 MW operating + 600 MW under-construction is supported by Cipher's own contemporaneous 8-Ks (interconnection approvals, lease executions). But the 3.4 GW pipeline figure — '7 Texas sites + 1 Ohio site' — is mostly LAND OPTIONS or early-stage development without confirmed interconnect approvals nor named tenants (per Cipher's own disclosure language: 'pipeline of future sites that we expect to be suitable for HPC'). The 4.2 GW HEADLINE conflates 600 MW developed-for-HPC (visible counterparty contracts) with 3.4 GW aspirational. Heuristic 3 ladder: only 207 MW energized + producing revenue (a

#### 🟡 MOD — `C5`
- **R (claim):** Cipher raised ~$3.2B in 2025 (172.5M 2030 converts + $1.3B 2031 0% converts + $1.733B 7.125% 2030 senior secured notes at Cipher Compute SPV); subsequent $2.0B 6.125% 2031 senior secured notes at Black Pearl Compute SPV. FY2025 net loss $822.2M, accumulated deficit $1.004B, cash $628.3M, $207.9M cash used in ops, $725.7M ATM (33.3M shares issued at $5.88 avg).
- **F (M-source check):** Distress-marker checks: going-concern, reverse split, Form 15-12G, 25-NSE, large dilutive issuance
- **M (observed):** No going-concern auditor opinion. No Form 15-12G or 25-NSE in index. ATM share-count expansion = 33.3M shares (~10% of base). Convertible-notes $1.3B at $16.03 strike + $172.5M at $4.45 strike + Capped Call protection. Embedded-derivative GAAP loss of $450.4M (non-cash) drove most of the net-loss spike.
- **Why this severity:** Capital structure is leveraged but cleanly disclosed and well-corroborated by external evidence (high 8-K frequency for note issuances; SPV-level financing structure that requires lender diligence on site rights). No distress fingerprints per Heuristic 10. HOWEVER, Heuristic 11 applies: 100% of recognized FY2025 revenue is still BTC mining ($199.6M); zero HPC hosting revenue despite the AWS/Fluidstack-Google headline contracts. Combined with $822M net loss (even ex-$450M non-cash embedded-derivative loss, still ~$372M underlying loss) and dilutive ATM at $5.88 vs $16.03 conversion strike, this

#### 🟡 MOD — `C6`
- **R (claim):** Construction commitments of $713.5M (mostly Barber Lake, fully funded with restricted cash); Black Pearl BTC mining ceased early 2026 awaiting HPC lease commencement mid-2026; AWS/Fluidstack-Google rent commencement is Q4 2026 / Q1 2027 / Sept 2026 — disclosure-quality risk of TCV-vs-current-revenue conflation.
- **F (M-source check):** Counterparty corroboration of revenue timing + asymmetric external mention test
- **M (observed):** Amazon mentions of Cipher: 0 (since June 2025). External validation of MW pipeline: ~100% internal. Pattern: Cipher's MD&A foregrounds the 15-year x 300 MW AWS lease and the 'Fluidstack/Google' deal but does NOT break out a TCV figure (no aggregate $-value disclosed in the slice), nor a per-MW pricing schedule, nor a deferred-revenue waterfall. The $713.5M construction commitment is a real number;
- **Why this severity:** Cipher's disclosure is reasonably good on the construction-cost side ($713.5M committed, fully funded with restricted cash from the SPV note proceeds) and on stage-ladder language ('phased delivery', 'rent commencement'). But Heuristic 9 applies (TCV-vs-recognized-revenue): the company narratively conflates 'we entered into long-term HPC leases with Fluidstack and Amazon' with 'these represent a significant portion of our expected future revenues' WITHOUT quantifying expected first-year revenue. Combined with Black Pearl BTC mining HAVING CEASED in early 2026 (so even legacy revenue at that si

---

## Execution

### Shortability
- **Tier:** `BORROW_AT_PREMIUM`
- Price: $20.33
- Market cap: $0.00B
- Daily $ volume: $0.00M
- Short float: 16.8%
- ⚠ daily $ vol $0.00M < $1M (liquidity gate)

### IBKR borrow
- **Latest fee:** **0.25%** annualized (2026-05-15)
- Shares available: 8.4M
- 30-day avg: 0.32%
- 30-day max: 0.42%
- Trend: **stable**

### Hedge ratio
- **Beta-neutral:** **1.00×** (short β=?, long β=0.99)
- _Method: default 1:1 (missing beta data)_
- For every $1 long EQIX, short $1.00 of CIFR.

### Notional cap (5% daily $ vol)
- Short daily $ vol: $0.00M → cap $0.00M
- Long daily $ vol: $636.96M → cap $31.85M
- **Binding leg: short**
- **Max long-leg notional:** $31.85M

### Suggested conservative entry (30% of cap)
- Long EQIX: **$9.55M**
- Short CIFR: **$9.55M**
- Annualized borrow carry on short: **$23,886/yr** (0.25% × $9.55M)

---

## Risk + falsification

- **Falsification window:** 12 months from cutoff (2026-05-16). Pair survives if either leg moves >50% against the thesis OR the divergence claim is corroborated post-cutoff and the pair returns ~0.
- **Suggested exit rule:** close on +20% adverse move on the short leg, OR 6 months without confirming evidence, whichever comes first.
- **Hedge ratio reliability:** if either β was missing (default 1:1 fallback), the hedge is approximate. Watch correlation drift quarterly.

## Pair metadata
- Theme: AI-DC / crypto-pivot
- Generated: 2026-05-17 from frozen position_sizing.json + borrow_rates.json