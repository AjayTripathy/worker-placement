# SHORT **SES** / LONG **ALB** — Solid-state battery

**Tier:** TIER1   ·   **Composite (short):** 1.50   ·   **Flags (short):** 1R / 1S / 4M

**Long-leg composite:** 0.12 (in-cohort cleanest follow)

**Short-leg filing analyzed:** `0001819142-26-000010_10-K.txt`

---

## Thesis

Tier 1 (high-conviction): composite ≥ 0.75 with at least one RED_FLAG or two SEVERE findings. The trade thesis is a **factual revision** — restatement, registry contradiction, regulator action, or counterparty churn that will be visible in subsequent filings within the 12-month falsification window.

---

## Evidence (R / F(M) / M)

#### 🔴 RED — `C4`
- **R (claim):** Strategic pivot from in-house Li-Metal battery manufacturing toward AI/Molecular Universe; capex redirected from manufacturing equipment to AI infrastructure; reduced headcount.
- **F (M-source check):** epa_frs.query_facilities for Woburn MA
- **M (observed):** SES (search='SES', state=MA, city=Woburn): 0 facilities. SolidEnergy (state=MA): 1 facility found — SOLIDENERGY SYSTEMS CORP, 35 Cabot Rd, Woburn MA — registered under legacy name, NOT updated to current SES AI branding
- **Why this severity:** Pattern-recognition RED_FLAG: A pre-revenue battery name that originally raised SPAC capital on the OEM JDA / Li-Metal SOP story has, by FY2025, (a) seen its three US-named OEM JDAs all conclude or downshift, (b) zeroed out OEM-funded R&D ($0 vs $8.575M PY), (c) explicitly redirected capex AWAY from battery manufacturing equipment toward 'AI infrastructure / GPU rental / software,' (d) rebranded itself to 'SES AI' and stood up Molecular Universe and a JV with Hisun (which 'will allow us to manufacture our newly discovered materials at commercial scale for customers' — i.e. SES is no longer pla

#### 🟠 SEVERE — `C1`
- **R (claim):** Hyundai B-sample JDA concluded December 2025; no announced advancement to C-sample, validation, or SOP.
- **F (M-source check):** edgar_fts.query_fulltext (general 'SES AI'); Hyundai files no SEC forms (Korean issuer, EDGAR not applicable)
- **M (observed):** 271 EDGAR hits for 'SES AI' but no SEC-filer corroboration possible for Hyundai (foreign issuer not on EDGAR for annual report)
- **Why this severity:** Calibration Heuristic 3 (planned vs operational / STAGE LADDER): Hyundai started in Dec 2020 with a discovery JDA, advanced to A-sample (Aug 2021), then to B-sample (March 2024 extension). The B-sample JDA *concluded* in December 2025 with NO disclosed follow-on for C-sample or validation. Under the framework's stage ladder, this is a STALLED ladder: the JDA reached B-sample and then was let to expire, despite >5 years of joint work. Combined with $0 JDA reimbursements from any OEM partner in 2025 vs $8.575M in 2024 (also disclosed in Note 5), all OEM-funded R&D has dried up. The pre-SPAC narr

#### 🟡 MOD — `C2`
- **R (claim):** GM JDA concluded September 2024 and GM mutually terminated Director Nomination Agreement October 29, 2024; GM no longer a related party.
- **F (M-source check):** edgar_fts.query_fulltext cik=0001467858 (GM) for 'SES AI' and 'SolidEnergy'
- **M (observed):** GM 10-K mentions of 'SES AI' = 0; mentions of 'SolidEnergy' = 0
- **Why this severity:** Calibration Heuristic 7 (counterparty-disclosure threshold): SES's flagship US-OEM JDA (one of the framework's HARD-CONTRADICTION candidates per the cohort prompt) concluded September 2024 and GM exited the board the next month. GM's 10-K filings contain ZERO references to SES AI or SolidEnergy. While JDAs typically don't appear in OEM 10-Ks pre-SOP (so absence alone wouldn't be RED_FLAG), here the company itself discloses the termination, and the equity stake on which the board seat was conditioned has been allowed to fall below 5%. Under Heuristic 4 (investment vs operating), the original GM
- **Audit:** originally `SEVERE_UNDERDELIVERY` — adjusted by rescoring.

#### 🟡 MOD — `C3`
- **R (claim):** Honda A-sample JDA concluded June 2023; replaced by B-sample services agreement (Jan 2025 through June 2026). Another OEM B-Sample JDA concluded December 2025.
- **F (M-source check):** edgar_fts.query_fulltext cik=0000715153 (Honda 20-F) for 'SES AI', 'SolidEnergy', 'Apollo'
- **M (observed):** Honda 20-F mentions of 'SES AI' = 3 hits (filings dated 2022-06-22, 2023-06-23, 2024-06-20); 'SolidEnergy' = 0; 'Apollo' = 0. Most recent Honda 20-F filed 2025-06-18 (covers FY ending March 2025) does NOT appear in 'SES AI' hits.
- **Why this severity:** Calibration Heuristic 7: Honda IS a SEC-filer (HMC 20-F), so this is partially verifiable. Honda's FY2022-2024 20-Fs reference SES AI as a battery JDA counterparty (consistent with disclosed Honda A-sample JDA Dec 2021-June 2023). However the MOST RECENT pre-cutoff Honda 20-F (filed June 18, 2025, covering FY ending March 2025) does NOT mention SES AI. SES disclosed in this 10-K that Honda replaced the original JDA with a B-sample services agreement in January 2025 — Honda's contemporaneous 20-F omits this. That is a notable divergence: a JDA-style relationship being downgraded to a services a

#### 🟡 MOD — `C5`
- **R (claim):** Acquired UZ Energy (China BESS manufacturer) on September 15, 2025 for ~$25.8M; UZ Energy contributed ~35% of FY2025 revenue.
- **F (M-source check):** edgar_fts.query_fulltext('UZ Energy')
- **M (observed):** 20 EDGAR hits for 'UZ Energy', all from SES AI 8-Ks/10-Q/10-K filings starting July 2025 — no independent third-party SEC corroboration (consistent with UZ Energy being a private China company)
- **Why this severity:** Calibration Heuristic 11 (revenue-recognition pattern): SES's $21.0M of FY2025 'revenue from customers' is essentially manufactured: $13.6M is service revenue from OEM JDA contracts that have now all concluded; the $7.4M of product revenue is driven almost entirely by UZ Energy ESS systems sales — a business model entirely unrelated to the original Li-Metal EV cell thesis, in a different country, in a different end-market (residential/commercial BESS in China). The Sept 15, 2025 close means UZ Energy contributed only ~3.5 months of FY2025 yet drove 35% of total revenue and is excluded from FY2

#### 🟡 MOD — `C6`
- **R (claim):** Plan to develop NDAA-compliant drone cell manufacturing capacity in Korean facility for U.S. government and defense-related customers as a future revenue driver.
- **F (M-source check):** usaspending.query_recipient_contracts (SES AI), usaspending.query_dod_contracts (SolidEnergy)
- **M (observed):** 0 federal contracts under 'SES AI' (any agency, 2022-2026). 0 DoD contracts under 'SolidEnergy' (2020-2026). Total federal award $: 0.
- **Why this severity:** Calibration Heuristic 5 (source-jurisdiction): USAspending covers DoD contracts that would feed an NDAA-compliant drone-cell program. SES has ZERO federal contracts of any kind through cutoff. The claim is explicitly phrased as forward-planned ('we are planning to develop... uncertainty regarding the timing and magnitude of customer demand'), so it is not RED_FLAG for absence — but it is MODERATE because the company is signaling a defense-customer revenue thesis with no contracts, no MOUs, no SBIR/STTR awards, no DoD validation, and the Korean facility is not yet NDAA-compliant. Per Heuristic 

---

## Execution

### Shortability
- **Tier:** `BORROW_AT_PREMIUM`
- Price: $1.13
- Market cap: $0.42B
- Daily $ volume: $10.49M
- Short float: 7.2%
- ⚠ price $1.13 < $5 (most retail brokers prohibit short)

### IBKR borrow
- **Latest fee:** **0.79%** annualized (2026-05-15)
- Shares available: 6.2M
- 30-day avg: 0.63%
- 30-day max: 2.00%
- Trend: **rising**

### Hedge ratio
- **Beta-neutral:** **0.62×** (short β=0.83, long β=1.34)
- _Method: beta-neutral (short_beta / long_beta)_
- For every $1 long ALB, short $0.62 of SES.

### Notional cap (5% daily $ vol)
- Short daily $ vol: $10.49M → cap $0.52M
- Long daily $ vol: $384.21M → cap $19.21M
- **Binding leg: short**
- **Max long-leg notional:** $0.52M

### Suggested conservative entry (30% of cap)
- Long ALB: **$0.16M**
- Short SES: **$0.10M**
- Annualized borrow carry on short: **$771/yr** (0.7913% × $0.10M)

---

## Risk + falsification

- **Falsification window:** 12 months from cutoff (2026-05-16). Pair survives if either leg moves >50% against the thesis OR the divergence claim is corroborated post-cutoff and the pair returns ~0.
- **Suggested exit rule:** close on +20% adverse move on the short leg, OR 6 months without confirming evidence, whichever comes first.
- **Hedge ratio reliability:** if either β was missing (default 1:1 fallback), the hedge is approximate. Watch correlation drift quarterly.
- **Borrow trend:** ⬆ **rising** — other shorts are crowding in, which often front-runs the thesis. If borrow keeps tightening, position may need to be sized down.

## Pair metadata
- Theme: Solid-state battery
- Generated: 2026-05-17 from frozen position_sizing.json + borrow_rates.json