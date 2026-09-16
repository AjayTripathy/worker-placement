# IJR Manifest — Gap m-source Prioritization

**Generated**: 2026-05-26 (follows MANIFEST.md)
**Purpose**: Rank the ❌ GAP m-sources from MANIFEST.md by build-priority so we know what to build before running the IJR deterministic exclusion test.

## Scoring rubric

Priority = `(coverage × determinism × signal) / build_effort`

- **coverage** = number of IJR names this m-source verifiably covers
- **determinism** (1-3): 1 = paywalled/scraping/cross-source entity-resolution required; 2 = public but needs joins/fuzzy matching; 3 = public clean API with ticker/CIK/EIN/NAICS join key
- **signal** (1-3): 1 = marginal lift; 2 = meaningful warning sign w/ false positives; 3 = catches a specific catastrophe pattern with high precision (e.g., Steward tenant credit risk, going-concern, FDA Warning Letter)
- **build_effort** (1-3): 1 = <1 day single-API client; 2 = 1-3 days multi-source join; 3 = >1 week scraping + entity resolution

Use the priority score as a relative rank, not an absolute. The asymmetric-payoff math in HANDOFF.md (5x false-positives still net-positive) argues for prioritizing **coverage breadth** over signal precision at the early tiers.

---

## Tier 1 — Build before IJR test (priority ≥100)

| Rank | m-source | Cov | Det | Sig | Eff | Priority |
|---|---|---|---|---|---|---|
| 1 | `working_capital_drift.py` | 450 | 3 | 2 | 2 | **1350** |
| 2 | `pacer_class_action.py` | 600 | 2 | 1.5 | 3 | **600** |
| 3 | `tenant_credit_watch.py` | 56 | 3 | 3 | 2 | **252** |
| 4 | `orange_book.py` | 25 | 3 | 2 | 1 | **150** |
| 5 | `export_control_check.py` | 22 | 3 | 2 | 1 | **132** |

### 1. `working_capital_drift.py` (priority 1350)

- **What**: DSI/DSO/DPO inflection detector. Pull XBRL inventory, receivables, payables, COGS, revenue across 8 quarters. Flag names where any of (a) inventory days growing faster than revenue, (b) DSO bleed >10% QoQ for 2+ Qs, (c) DPO stretch concurrent with covenant amendment. Output: 3-state signal {clean, drift, severe}.
- **Why it's #1**: Touches all goods-producing names (~400-450), the inventory-overhang catastrophe pattern is responsible for AAP-style blowups (auto retail), apparel rolloffs (VFC/KTB), semis cycle write-downs, builders' spec-home overhang, and food distrib (BGS/HAIN). Universal coverage + clean XBRL source.
- **Build**: SEC `companyconcept` API with Inventory, AccountsReceivable, AccountsPayable, Revenue, COGS tags. Need to handle XBRL multi-context for fiscal period. Most signal-laden m-source we don't yet have.
- **Risk**: XBRL tagging inconsistency across filers; may need extension fact-set fallback.

### 2. `pacer_class_action.py` (priority 600)

- **What**: Federal class-action/securities-litigation tracker. CourtListener RECAP for free index, fall back to PACER paid for fresh dockets. Match by defendant EIN / company name. Bucket by (a) securities/10b-5, (b) wage-hour, (c) ADA, (d) product liability.
- **Why**: Universal. Wage-hour drag is real for staffing/retail/restaurants; securities suits often telegraph accounting issues.
- **Build**: CourtListener API is free; entity resolution to ticker is the hard part. Plan to use CL's "Cases by Party" + fuzzy match on company name + cross-ref EDGAR conformed name.
- **Risk**: Signal noisy — most public companies have routine litigation. Need to focus on ≥$25M reserves or new filings post-quiet-period.

### 3. `tenant_credit_watch.py` (priority 252)

- **What**: REIT-tenant credit monitor. Parse 10-K named-tenant exposure tables. Build watchlist of all named tenants. Listen for tenant 8-K Item 1.03 (bankruptcy), 2.04 (default), 2.06 (impairment) events. Cross-ref tenant 10-K going-concern language. Output: REIT-level tenant-watchlist score.
- **Why**: Steward Health Care destroyed MPW. Steward filings telegraphed distress 12+ months before MPW disclosed it. Same pattern available for IIPR (cannabis tenants), CTRE (SNF operators), retail REITs.
- **Build**: 10-K table extraction (named-tenants frequently in supplemental schedules) + EDGAR 8-K stream + Going-Concern detector cross-ref. Reuses `going_concern_detector.py` + `claim_evolution.py`.
- **Risk**: Some REIT tenants are private companies (cannabis MSOs) — need state license registries as fallback.

### 4. `orange_book.py` (priority 150)

- **What**: FDA Orange Book parser. Load Orange Book (patents + exclusivity expirations) and match to assignee. Compute loss-of-exclusivity (LOE) gap years per drug. Cross-ref Paragraph IV challenges.
- **Why**: 25 pharma names. LOE is the dominant catastrophe pattern for marketed-Rx (OGN, ALKS, PBH, CORT, CPRX). Orange Book is the canonical source — already structured.
- **Build**: Orange Book is a free FDA download (text files, well-structured). One-day build.

### 5. `export_control_check.py` (priority 132)

- **What**: BIS Entity List + Denied Parties + DDTC list checker. Match company name + foreign subsidiaries. Also check for ZTE/Huawei-style 10-K Item 1A mentions about export-control exposure.
- **Why**: 22 names (semis with China revenue + industrial machinery exporters). One BIS designation = revenue cliff.
- **Build**: BIS publishes CSV. SAM.gov has merged consolidated screening list. One-day build.

---

## Tier 2 — Build during IJR test (priority 30-100)

| Rank | m-source | Cov | Det | Sig | Eff | Priority |
|---|---|---|---|---|---|---|
| 6 | `consumer_traffic_proxy.py` | 50 | 2 | 2 | 2 | 100 |
| 7 | `cogs_pass_through.py` | 70 | 2 | 1 | 2 | 70 |
| 8 | `bts_airline_metrics.py` | 7 | 3 | 3 | 1 | 63 |
| 9 | `hedge_book_check.py` | 30 | 2 | 2 | 2 | 60 |
| 10 | `runway_calculator.py` | 6 | 3 | 3 | 1 | 54 |
| 11 | `cms_cost_reports.py` | 11 | 3 | 3 | 2 | 49.5 |
| 12 | `reserves_revision.py` | 10 | 3 | 3 | 2 | 45 |
| 13 | `fcc_form_477.py` | 6 | 3 | 2 | 1 | 36 |
| 14 | `share_count_drift.py` | 6+ | 3 | 2 | 1 | 36 |
| 15 | `ipeds_title_iv.py` | 3 | 3 | 3 | 1 | 27 |

**Notes:**
- `consumer_traffic_proxy.py` — Google Trends free, app-store rank free; Placer.ai/SafeGraph paywalled. Build with free sources first.
- `bts_airline_metrics.py` — BTS T-100, Form 41, OTP all free CSV. Catches load-factor / OTP collapse early. Highest per-name signal in Tier 2.
- `runway_calculator.py` — pulls cash, burn from 10-Q. Trivial. Combine with `going_concern_detector.py`.
- `ipeds_title_iv.py` — for-profit education has chronic catastrophes (Corinthian, ITT, DeVry parent). IPEDS data is free.
- `cms_cost_reports.py` — HCRIS free FTP. Directly observes SNF/hospital revenue + margin. Should also flow into `tenant_credit_watch.py` for CTRE/MPW healthcare REITs.

---

## Tier 3 — Build if time permits (priority 10-30)

| Rank | m-source | Cov | Det | Sig | Eff | Priority |
|---|---|---|---|---|---|---|
| 16 | `homebuilder_permits.py` | 8 | 2 | 2 | 2 | 16 |
| 17 | `oem_rate_tracker.py` | 11 | 2 | 2 | 3 | 14.7 |
| 18 | `rig_utilization.py` | 12 | 2 | 2 | 3 | 16 |
| 19 | `faa_enforcement.py` | 9 | 2 | 2 | 1 | 36 |
| 20 | `msha_violations.py` | 8 | 3 | 2 | 1 | 48 |
| 21 | `hotel_revpar_proxy.py` | 4 | 1 | 3 | 3 | 4 |
| 22 | `cms_coverage.py` | 17 | 2 | 2 | 3 | 22.7 |
| 23 | `cms_nursing_home_compare.py` | 3 | 3 | 3 | 1 | 27 |
| 24 | `cms_hospital_compare.py` | 2 | 3 | 2 | 1 | 12 |
| 25 | `cms_home_health.py` | 3 | 3 | 2 | 1 | 18 |
| 26 | `cms_qcor.py` | 4 | 3 | 2 | 1 | 24 |
| 27 | `naic_serff.py` | 10 | 1 | 2 | 3 | 6.7 |
| 28 | `insurance_statutory.py` | 17 | 1 | 3 | 3 | 17 |
| 29 | `fda_food_inspection.py` | 8 | 3 | 2 | 1 | 48 |
| 30 | `patent_litigation.py` | 25 | 1 | 2 | 3 | 16.7 |
| 31 | `auto_dealer_signals.py` | 6 | 2 | 2 | 2 | 12 |
| 32 | `import_concentration.py` | 10 | 1 | 2 | 3 | 6.7 |
| 33 | `headcount_proxy.py` | 23 | 1 | 1 | 2 | 11.5 |
| 34 | `sbc_quality_check.py` | 23 | 3 | 1 | 1 | 69 (→ Tier 2 candidate) |
| 35 | `rpo_drift.py` | 23 | 3 | 2 | 1 | 138 (→ Tier 1 candidate) |
| 36 | `marketplace_health.py` | 5 | 1 | 2 | 3 | 3.3 |
| 37 | `fda_inspection.py` (extension of openFDA) | 17 | 3 | 3 | 1 | 153 (→ Tier 1 if treated as openFDA extension) |
| 38 | `eudamed.py` | 16 | 2 | 1 | 2 | 16 |
| 39 | `cannabis_licenses.py` | 2 | 2 | 3 | 2 | 6 |
| 40 | `cap_rate_bench.py` | 56 | 1 | 1 | 3 | 18.7 |

**Re-promotion notes**: items 34, 35, 37 score higher than initially placed and belong in Tier 1/2:
- `rpo_drift.py` — 138 priority. SaaS cRPO/revenue inflection is a clean catastrophe pattern (Twilio, Asana, ZScaler-style misses). Add to Tier 1.
- `fda_inspection.py` (extension of `openfda.py`) — 153 priority. Catches FDA-483/Warning Letter issuance. Add to Tier 1.
- `sbc_quality_check.py` — 69 priority. Tier 2.

---

## Tier 4 — Low priority / one-name / paywalled

| m-source | Cov | Reason for de-prioritization |
|---|---|---|
| `box_office_share.py` | 1 (CNK) | Single-name signal |
| `auto_auction_volume.py` | 1 (KAR) | Single-name; Manheim data partly paywalled |
| `btc_miner_signals.py` | 2 (MARA) | Niche; price-driven not framework-driven |
| `solar_install_proxy.py` | 1 (RUN) | Single-name; better covered by claim_evolution |
| `state_gaming_reports.py` | 2 (PENN) | 50-state scraping; low coverage |
| `state_puc_rate_cases.py` | 10 | 50-state PUC docket scraping; build_effort 3 |
| `state_dot_awards.py` | 5 | 50-state DOT awards scraping |
| `irs_tax_credit_transfer.py` | 2 | New IRS registry (post-IRA), data quality unclear |
| `eia_utility_data.py` | 13 | Public but signal is mostly recovery, not catastrophe |
| `usda_nass.py` | 2 | UVV, ANDE only |
| `dea_registration.py` | 6 | Tight coverage; FOIA-style retrieval |
| `eu_gmp.py` | 25 | EU-side; openfda extension is already on path |
| `fcc_uls.py` | ~3 | Niche to spectrum-holders |
| `bead_grant_tracker.py` | ~3 | New NTIA program, sparse data |
| `usace_404.py` | ~5 | Wetland permits, niche |
| `app_store_rank.py` | 5 | Rank-tracking APIs paywalled |
| `fda_rfr.py` | 20 | RFR is sparse; signal mostly captured by openfda recalls |
| `fda_pmta.py` | 1 (VGR) | Single-name |
| `accreditation_status.py` | 3 | Often catastrophe is concurrent w/ Title IV — covered by `ipeds_title_iv.py` |
| `design_win_proxy.py` | 31 | No clean public source; would be LLM-heavy → move to NARRATIVE_ONLY |

---

## Suggested build plan (sequenced)

**Sprint 1 (5-7 days, target: enable IJR test):**
1. `working_capital_drift.py` (2 days)
2. `orange_book.py` (1 day)
3. `export_control_check.py` (1 day)
4. `runway_calculator.py` (0.5 day)
5. `share_count_drift.py` (0.5 day)
6. `fda_inspection.py` extension to existing `openfda.py` (1 day)
7. `rpo_drift.py` (1 day)

Sprint 1 yields ~525 covered names with new signal (working_capital alone = ~450, the rest layered on top).

**Sprint 2 (5-7 days, deepen):**
1. `tenant_credit_watch.py` (3 days — big build, big payoff)
2. `pacer_class_action.py` (3 days)
3. `cms_cost_reports.py` + healthcare REIT tie-in (2 days)
4. `bts_airline_metrics.py` (1 day)

**Sprint 3 (optional, niche catches):**
- ipeds, msha, cms_nursing_home_compare, fcc_form_477, hedge_book_check, cogs_pass_through

---

## Cross-cutting build patterns

Several gaps share infrastructure. Build the shared layer once:

1. **CMS HCRIS / Compare ecosystem** — `cms_cost_reports.py`, `cms_nursing_home_compare.py`, `cms_hospital_compare.py`, `cms_home_health.py`, `cms_qcor.py`, `cms_coverage.py` all hit CMS data.gov / HCRIS FTP. Build a `cms_client.py` shared layer first.

2. **State scrapers** — `state_puc_rate_cases.py`, `state_dot_awards.py`, `state_gaming_reports.py`, `state_doi_filings.py` all need state-by-state scraping infrastructure. Build a `state_scraper_kit.py` with per-state adapter pattern.

3. **FDA family** — `fda_inspection.py`, `fda_food_inspection.py`, `fda_pmta.py`, `fda_rfr.py`, `eudamed.py` should all extend the existing `openfda.py` rather than be siblings.

4. **Working-capital and SBC quality** — both pull XBRL multi-period. Build a `xbrl_panel.py` shared helper.

5. **Hedge book and cogs pass-through** — both consume commodity reference data (NYMEX, ICE, BLS PPI). Build a `commodity_ref.py` shared.

---

## Open methodology questions (deferred to IJR test)

1. **Multi-source aggregation rule** — when 3+ m-sources fire on a name, how do we combine signals into a single exclude/keep decision? Currently using arithmetic mean composite (per `composite_recompute.py`). Should it be max-pooled for catastrophe signals?
2. **Sector calibration** — should gating thresholds be cluster-specific? E.g., a 10% DSO bleed means more for retail than for capital-goods.
3. **Lag handling** — manifest is point-in-time 2024-06-30. m-sources are real-time. For the 12m/24m backtest, we need each m-source frozen to 2024-05-15 data vintage (no look-ahead).
