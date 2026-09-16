# Honesty-Signal Coverage Expansion — Design Doc & Execution Plan

**Status**: Proposed
**Owner**: TBD
**Last updated**: 2026-05-26

## Background

Phase 5 of the IJR backtest validated the framework's honesty signal as a precision
tool (46% precision at SEVERE+, −37 pp basket vs IJR) but exposed structural
coverage limits: only **145 of 548 IJR names (26%)** had any honesty module
evaluated, and only **47 of 99 catastrophes (47%)** were in clusters with
canonical-authority coverage. The remaining 53% of catastrophes were in
clusters where we have no canonical authority module: retail, restaurants,
business services, real estate (most), materials/chemicals, tech software,
energy, transport, construction.

This plan proposes building out the long-tail cluster-canonical authority
modules, plus regime-validating against a hostile period (2022-2023
small-cap drawdown including SVB era).

## Goals

1. **Coverage**: lift honesty-signal coverage from 26% → 60-70% of IJR universe
2. **Recall**: lift catastrophe-detection recall from current 13% (of evaluated)
   to 30%+ at universe scale
3. **Validation**: confirm whether honesty-alpha signal holds in a hostile
   regime (2022-2023 SVB-era small-cap drawdown)
4. **Aggregate alpha**: determine if expanded coverage moves honesty-only
   alpha from +1 pp → meaningfully positive

## Non-goals

- Adding new distress signals (already validated as quality-factor re-derivation)
- Optimizing composite math (already tested in Phase 3)
- Building cohort-specific factor ETF substitutes (already exist commercially)
- Replacing the validated narrow-domain risk-management overlay use case

---

## Coverage gap inventory

From Phase 5, the cluster-by-cluster honesty coverage with catastrophe counts:

### Tier 1: high catastrophe count, no/low honesty coverage (highest priority)

| Cluster | n | n_cat | % evaluated | % fired |
|---|---|---|---|---|
| MATERIALS_CHEMICALS | 29 | **11** | 24% | 0% |
| BUSINESS_SERVICES | 26 | **12** | 31% | 0% |
| TECH_SOFTWARE_SERVICES | 21 | **10** | 24% | 0% |
| REAL_ESTATE | 53 | 7 | 9% | 2% |
| CONSUMER_RETAIL | 24 | 6 | **0%** | 0% |

These five clusters contain 46 of 99 universe catastrophes (46%).

### Tier 2: medium catastrophe count, partial or fixable coverage

| Cluster | n | n_cat | % evaluated | Notes |
|---|---|---|---|---|
| CONSUMER_STAPLES_FOOD | 8 | 4 | 25% | openfda food recall works but rarely fires |
| INDUSTRIALS_CONSTRUCTION | 21 | 5 | 0% | Census BPS + state permits — buildable |
| INDUSTRIALS_TRANSPORT | 17 | 2 | 0% | BTS metrics built; cache empty |
| COMMUNICATIONS | 16 | 4 | 13% | FCC Form 477 built; cache empty |
| HEALTHCARE_SERVICES | 13 | 2 | 100% | CMS HCRIS data extraction broken |
| CONSUMER_RESTAURANTS | 10 | 3 | 0% | FDA RFR + state health |
| TECH_HARDWARE | 30 | 4 | 3% | BIS Entity List integration broken |

These contribute 24 catastrophes; mostly suffer from cache/integration
issues on built modules rather than missing modules.

### Tier 3: low catastrophe count or low tractability (defer)

| Cluster | n | n_cat | % evaluated | Notes |
|---|---|---|---|---|
| ENERGY | 21 | 2 | 0% | EIA + state O&G; specialty |
| CONSUMER_DISCRETIONARY | 25 | 3 | 12% | NHTSA partial; rest hard |
| INDUSTRIALS_ELECTRICAL | 9 | 1 | 0% | Solar-specific (NREL has, partial) |
| INDUSTRIALS_INSTRUMENTS | 8 | 1 | 0% | Niche measurement |
| CONSUMER_SERVICES | 9 | 1 | 0% | IPEDS (for-profit edu) niche |
| UTILITIES | 11 | 0 | 0% | No catastrophes — skip |

---

## Per-cluster module designs

### CLUSTER: MATERIALS_CHEMICALS (Tier 1, 11 catastrophes)

**Catastrophe mechanisms**: PFAS / Superfund litigation, customer concentration loss,
EPA enforcement, raw-material cost shocks, M&A integration failure.

**Modules to build / extend**:

1. **`epa_superfund.py`** *(new — extends epa_frs)*
   - Source: EPA CERCLIS / Superfund database (free, downloadable JSON)
   - Cross-check: company-claimed facility list vs Superfund/RCRA sites
   - Signal: SUPERFUND_LIABILITY at 3+ NPL sites associated; CERCLIS_LISTED if any
   - Effort: 8 hours
   - Coverage impact: ~20 of 29 names

2. **`pacer_class_action.py`** *(already built; needs CourtListener API token)*
   - Source: CourtListener federal docket
   - Signal: PFAS-class-action presence, product-liability tier
   - Effort: 30 min to provision token; module exists
   - Coverage impact: universal but most relevant here

3. **`cogs_pass_through.py`** *(new)*
   - Source: BLS PPI by chemical NAICS + 10-K GM trajectory
   - Signal: claimed pass-through vs actual GM evolution
   - Effort: 12 hours (BLS PPI integration + XBRL GM derivation)
   - Coverage impact: ~15 of 29

**Sub-total**: ~22 hours, lifts MATERIALS_CHEMICALS from 24% → ~70%

### CLUSTER: BUSINESS_SERVICES (Tier 1, 12 catastrophes)

**Catastrophe mechanisms**: Customer concentration loss, government contract
recompete failure, TAM compression (e.g., advertising spend cuts for
ad-services names like CARS, DV, MGNI).

**Modules to build / extend**:

1. **Universal sweep with `usaspending.query_federal_presence`** *(already built)*
   - Cross-check: implied federal revenue % vs actual contract obligations
   - Signal: INFLATION_SUSPECT, SUB_MATERIAL_FEDERAL, RECURRING_FEDERAL
   - Effort: 2 hours (add BUSINESS_SERVICES to dispatch)
   - Coverage impact: All 26 evaluable; 5-8 likely flagged

2. **`bls_qcew.query_county_naics` sector-level employment** *(already built)*
   - Source: BLS QCEW
   - Cross-check: staffing/consulting demand vs national employment trend
   - Signal: SECTOR_SHRINKING for fed-IT / staffing
   - Effort: 4 hours (add cluster dispatch + interpretation)
   - Coverage impact: Staffing subset (~7 names)

3. **`counterparty_reciprocity` on extracted customers** *(needs LLM customer extraction)*
   - Source: customer 10-Ks; check named customer mentions the issuer
   - Cross-check: claimed customer relationship vs customer's own filings
   - Signal: NOT_RECIPROCATED if customer doesn't mention us
   - Effort: 8 hours (extend Phase 2.5 LLM extract to all 26 + reciprocity check)
   - Coverage impact: All 26

**Sub-total**: ~14 hours, lifts BUSINESS_SERVICES from 31% → ~95%

### CLUSTER: TECH_SOFTWARE_SERVICES (Tier 1, 10 catastrophes)

**Catastrophe mechanisms**: NRR collapse, customer concentration on enterprise
deals, market saturation, engineering attrition.

**Modules to build / extend**:

1. **`nrr_extraction.py`** *(new — LLM-driven)*
   - Source: 10-K + 10-Q narratives, segment disclosures
   - Cross-check: NRR YoY claim vs implied from booking growth + churn
   - Signal: NRR_DECELERATING, NRR_INVERTED if NRR < 100 and declining
   - Effort: 6 hours
   - Coverage impact: ~15 of 21

2. **`dol_h1b_lca.query_lca` engineering headcount** *(already built; add to dispatch)*
   - Source: DOL Labor Condition Applications
   - Cross-check: claimed engineering headcount vs H1B filing trajectory
   - Signal: HEADCOUNT_DECLINE if YoY H1B fall > 20%
   - Effort: 4 hours
   - Coverage impact: ~10 of 21

3. **`counterparty_reciprocity` on extracted customers**
   - Same as BUSINESS_SERVICES
   - Effort: shared with above
   - Coverage impact: ~15 of 21

**Sub-total**: ~14 hours, lifts TECH_SOFTWARE from 24% → ~70%

### CLUSTER: REAL_ESTATE (Tier 1, 7 catastrophes)

**Catastrophe mechanisms**: Tenant collapse, refinancing failure, vacancy spike
(office), cannabis-tenant license revocation (IIPR).

**Modules to build / extend**:

1. **`tenant_credit_watch.py` scaled with LLM tenant extraction** *(both built)*
   - Source: per-REIT 10-K → LLM-extracted tenant roster → tenant SEC 8-K
     monitoring
   - Effort: 4 hours (orchestrate LLM extract on all 53 REITs, feed
     tenant_credit_watch)
   - Cost: ~$25-50 in Sonnet API calls for 53 REIT 10-Ks
   - Coverage impact: 53 REITs, ~20 with extractable tenant lists

2. **`cms_facility_search`** for healthcare REIT tenants (CTRE, MPW)
   - Already built; needs CCN curation refinement
   - Effort: 6 hours (CCN-roster manual curation for 2-3 healthcare REIT tenant
     lists)
   - Coverage impact: 2-3 names but high signal value

3. **`cannabis_license_state.py`** *(new — small build for IIPR)*
   - Source: state cannabis license registries (CO, FL, MI, MA, NJ, CA)
   - Cross-check: claimed cannabis tenant license validity
   - Effort: 8 hours (50-state but most relevant 6)
   - Coverage impact: IIPR only (1 name)

4. **Office occupancy / vacancy YoY KPI** via 10-K extract
   - Already covered by LLM extract Phase 2.5; needs deeper cohort run
   - Effort: 4 hours
   - Coverage impact: ~15 office/strip-mall REITs

**Sub-total**: ~22 hours + $50 API, lifts REAL_ESTATE from 9% → ~80%

### CLUSTER: CONSUMER_RETAIL (Tier 1, 6 catastrophes)

**Catastrophe mechanisms**: Same-store sales collapse, foot-traffic decline,
inventory glut, brand erosion, cyber breach.

**Modules to build / extend**:

1. **`google_trends_brand.py`** *(new)*
   - Source: pytrends or unofficial Google Trends API
   - Cross-check: brand search volume YoY vs claimed traffic/SSS growth
   - Signal: BRAND_DECLINING if 12m relative interest down >20%
   - Effort: 6 hours
   - Coverage impact: ~20 of 24 (brand-named retailers)

2. **`8k_item_105_cyber_breach.py`** *(new — applies to all clusters but high
   value for retail)*
   - Source: SEC EDGAR 8-K filings, Item 1.05 (cyber breach disclosure;
     mandatory since Dec 2023)
   - Effort: 4 hours
   - Coverage impact: universal, but retail has high relevance

3. **`pacer_class_action`** wage-hour subset *(already built)*
   - Coverage impact: all 24 (wage-hour suits common in retail)

**Sub-total**: ~10 hours, lifts CONSUMER_RETAIL from 0% → ~80%

### TIER 2 CACHE POPULATION (lower effort, immediate coverage lift)

These are modules already built but blocked on cache population:

1. **FCC Form 477 cache population** (`fcc_form_477.py` built)
   - Process: bulk-download FCC Form 477 December 2023 zip; aggregate by
     provider name into `subscriber_panel.json`
   - Effort: 4 hours
   - Coverage impact: 6-8 COMMUNICATIONS names (CABO, GOGO, TDS, SATS, CALX,
     CABO)

2. **BTS airline metrics cache** (`bts_airline_metrics.py` built)
   - Process: TranStats T-100 Segment + OTP CSV downloads for IJR airlines
     (ALK, SKYW, etc.)
   - Effort: 3 hours
   - Coverage impact: 7 airlines + non-scheduled

3. **CMS HCRIS CCN-roster curation** for healthcare services
   - Process: Manual look-up of CCN rosters for 14 healthcare-services
     operators (ENSG, SEM, NHC, etc.) from CMS POS file
   - Effort: 8 hours
   - Coverage impact: 14 of 14 names

4. **Pentagon J-Book corpus expansion**
   - Process: add IJR defense names (AVAV, MOG/A, BWXT, KTOS, etc.) to
     `programs.json` with their DoD program codes
   - Effort: 4 hours (mostly DoD program-code research)
   - Coverage impact: 5-7 defense names

5. **BIS Entity List integration fix** (replace broken trade.gov)
   - Process: scrape BIS Entity List directly from Federal Register or BIS
     site
   - Effort: 4 hours
   - Coverage impact: ~30 names with China revenue (semis + machinery)

**Sub-total**: ~23 hours

---

## Phase plan + effort estimate

| Phase | Scope | Hours | Coverage lift | New catastrophes potentially caught |
|---|---|---|---|---|
| **A.1** Cache population + integration fixes | 5 modules (FCC, BTS, CMS CCN, J-Book, BIS) | ~23 | ~30 names | ~8-10 |
| **A.2** Tier 1 high-payoff (Materials + Business Services) | epa_superfund, pacer, usaspending sweep, cogs | ~36 | ~55 names | ~10-15 |
| **A.3** Tier 1 high-payoff (Tech Software + REIT + Retail) | nrr_extraction, tenant_credit scaling, google_trends, 8k cyber | ~46 | ~100 names | ~10-15 |
| **B.1** Tier 2 (food/restaurant + construction) | fda_rfr extension, census_bps, state_health | ~20 | ~40 names | ~5-8 |
| **B.2** Tier 3 (energy + remaining) | eia_production, msha_violations, ipeds_title_iv | ~25 | ~40 names | ~3-5 |

**Total expanded coverage build effort**: ~150 hours engineering + ~$200 LLM API

**Expected outcome**:
- Honesty-signal coverage: 26% → ~60-70%
- Catastrophe recall at universe scale (current 6%): expected 20-30%
- Universe-EW exclusion alpha: current +1 pp → projected +3-5 pp

---

## Regime validation: 2022-2023 small-cap drawdown

This is the *cleanest* test of the framework's signal validity across regimes
and is critical to do alongside the coverage expansion. Findings from Phase 5
showed that 2024-2026 was a value/junk rally that favored mean-reverters;
2022-2023 was the opposite — small-cap value crashed, bank failures hit,
quality outperformed.

### Design

- **Cutoff**: 2022-06-30 (pre-rate-hike-cycle equity rebalance)
- **Holdings universe**: IJR holdings as of 2022-06-30 (different from current
  set; need to pull historical N-PORT-P)
- **Forward returns**: 2022-06-30 → 2023-06-30 (12m) and 2024-06-30 (24m)
- **Period includes**:
  - 2022 rate-hike-driven small-cap drawdown (Q2-Q4 2022)
  - Tech wreck (META, NFLX, etc.)
  - Mar 2023 regional bank crisis (SVB, Signature, First Republic)
  - 2023 Q1-Q3 recovery
  - Israel-Hamas Oct 2023

### Why this regime matters

In 2024-2026 the framework's distress signals had negative LR coefficients
(working_capital_drift, share_count_drift) because they correlated with mean-
reverters. In 2022-2023 we expect:
- Distress signals positively predict catastrophes (junk got crushed)
- Bank cohort actually has catastrophes (regional bank crisis)
- Quality outperforms junk

If the framework's honesty signals still fire at 46% precision on the
2022-2023 catastrophes, the validation is regime-independent. If they fire
even higher precision, the framework's signal is doubly validated.

### Implementation steps

1. **Pull historical IJR holdings** from SEC EDGAR N-PORT-P (~2 hours)
   - Look for series S000004313 quarterly N-PORT-P filings
   - Identify Q2 2022 or Q3 2022 holdings (~600 names)
2. **Compute 12m / 24m forward returns** via yfinance (1 hour)
   - Compare to IJR 12m return for that period
3. **Build catastrophe distribution** (1 hour)
   - Expect ~25-30% catastrophe rate (vs 18% in 2024-2026 — higher because of bear market)
4. **Re-run universe runner** at cutoff 2022-06-30 (1 day wall clock)
5. **Run Phase 4b cohort-canonical battery** on cohorts (~2 hours after re-run)
6. **Compute Phase 5 honesty-only analysis** (~1 hour)
7. **Compare to 2024-2026 numbers** — regime sensitivity analysis

**Total**: ~20 hours engineering + ~1 day compute wall clock

### Specific predictions to test

| Hypothesis | If true (validates framework) | If false (limits scope) |
|---|---|---|
| Honesty SEVERE+ precision in 2022-2023 ≥ 40% | Regime-independent precision | Regime-specific tuning needed |
| Bank cohort catastrophes ≥ 5 in 2022-2023 | FDIC signal generates real-money alpha | FDIC distress isn't catastrophe-translating |
| working_capital_drift LR coef flips POSITIVE | Distress signals work in hostile regime | Signals are systematically anti-predictive |
| Exclusion strategy beats universe-EW in 2022-2023 | Framework adds value when value-stocks crash | Strategy is regime-dependent factor exposure |

### Why this matters for the bigger picture

The 2024-2026 result alone is ambiguous — small-cap value tailwind explains
most of it. A consistent +2-5 pp honesty-only alpha across BOTH 2022-2023
and 2024-2026 would be **regime-independent evidence** that the framework
has real edge beyond factor exposure.

If 2022-2023 doesn't validate, the honest conclusion is the framework is a
quality-factor implementation with extra signal hardware — useful but not
distinctive.

---

## Execution sequence

Recommended priority ordering:

```
Step 1 (Week 1):  Regime validation setup
                    - Pull historical IJR holdings 2022-06-30
                    - Yfinance forward returns
                    - Re-run universe runner (existing 10-module battery)
                    Decision point: do Phase 1 results in 2022-2023 even
                    sanity-check?

Step 2 (Week 1):  Cache population + integration fixes (A.1)
                    - FCC Form 477 cache
                    - BTS airlines cache  
                    - CMS CCN curation (manual)
                    - J-Book corpus expansion
                    - BIS Entity List integration
                    These unlock signal coverage we've already built.

Step 3 (Week 2):  Tier 1 high-payoff modules (A.2)
                    - epa_superfund.py
                    - pacer_class_action (token provisioning)
                    - cogs_pass_through.py
                    - BLS QCEW + USAspending universal sweep on Business Services
                    Coverage lift: Materials + Business Services to ~70-90%

Step 4 (Week 3):  Tier 1 high-payoff modules (A.3)
                    - nrr_extraction.py + LLM scaling
                    - tenant_credit_watch scaled (REIT 10-K LLM extraction)
                    - google_trends_brand.py
                    - 8k_item_105_cyber_breach.py
                    Coverage lift: Tech Software + REIT + Retail to ~70-80%

Step 5 (Week 3):  Re-run Phase 5 + Phase 4 on 2024-2026 with expanded modules
                    Measure: did coverage expansion lift universe-level recall?

Step 6 (Week 4):  Run expanded pipeline on 2022-2023 regime
                    Measure: hypothesis tests above

Step 7 (Week 4):  Tier 2 + Tier 3 modules (B.1, B.2)
                    If Tier 1 results justify, build out remaining clusters.

Step 8 (Week 5):  Cross-regime synthesis + final executive summary update
                    - Combined alpha estimate across both regimes
                    - Decision on positioning: precision tool vs alpha generator
```

## Decision gates

After **Step 5** (expanded 2024-2026 retest): if universe-level honesty-alpha
hasn't moved meaningfully from current +1 pp baseline, **pause and reconsider**
before doing Steps 7-8.

After **Step 6** (2022-2023 regime test): if the 2022-2023 result is
materially different from 2024-2026 in either direction, the conclusion shifts
significantly — either toward "regime-dependent factor" or "validated
cross-regime alpha." Update the executive summary accordingly.

## Open questions / risks

1. **LLM extraction cost scaling**: at 50+ tickers × Sonnet $0.05/call,
   ~$30-50 per phase. Cheap but not free. Budget ~$300 total for all
   LLM extraction work.

2. **2022-2023 data availability**: yfinance historical data should work back
   to 2018+. IJR holdings as of 2022-06-30 require N-PORT-P from that quarter
   (verified accessible via EDGAR).

3. **Capacity for the strategy**: if expanded honesty-alpha works at +3-5 pp
   level, what's the *capacity* before signal degrades? Small-caps have low
   ADV; AUM > $50M starts hitting friction. This isn't a billion-dollar
   strategy.

4. **Module maintenance**: J-Book + commercial-data feeds need continual updates.
   The framework becomes a maintained-data-product, not a one-shot library.

5. **Pre-registration**: if Tier 1 expansion happens before 2022-2023 test, the
   thresholds and decision rules MUST be locked in advance to avoid in-sample
   overfit. The 2022-2023 test should be conducted with the *exact* parameters
   tuned on 2024-2026.

## Budget summary

| Resource | Estimate |
|---|---|
| Engineering hours | ~150 total |
| LLM API costs | ~$300 |
| Compute (re-running pipelines) | ~5-10 hours wall clock |
| Manual curation (CMS CCNs, J-Book programs) | ~16 hours |
| Total project length | 4-5 weeks of focused engineering |

## Files to produce / update

- `verticals/public_co/m_sources/` — new module files (epa_superfund.py,
  cogs_pass_through.py, nrr_extraction.py, google_trends_brand.py,
  8k_item_105_cyber_breach.py, fda_rfr.py, eia_production.py,
  state_oag_filings.py, census_building_permits.py, cannabis_license_state.py,
  msha_violations.py, etc.)
- `verticals/public_co/data/_ijr_manifest/2022_cohorts.json` — historical
  holdings
- `verticals/public_co/data/_ijr_manifest/2022_forward_returns.json`
- `verticals/public_co/ijr_phase6_regime_validation.py` — 2022-2023 backtest
- `verticals/public_co/data/_ijr_manifest/PHASE6_FINDINGS.md` —
  cross-regime synthesis
- Update `MANIFEST.md`, `GAPS.md` to reflect closed gaps
- Update `EXECUTIVE_SUMMARY.md` with final cross-regime alpha numbers

## Success criteria

The expanded coverage + regime validation is successful if:

- Honesty-signal coverage reaches ≥ 60% of broad small-cap universe
- Universe-level honesty-alpha (exclusion vs universe-EW): ≥ +3 pp in BOTH
  2024-2026 AND 2022-2023 regimes
- Cohort-specific precision validation: at least 3 cohorts beyond medical devices
  show ≥ 40% catastrophe precision
- Long-only flagged-basket relative return: ≤ −20 pp vs sector ETF in BOTH regimes

If we hit these, the framework's distinctive contribution is validated as
both **precise** AND **cross-regime-stable** at meaningful universe scale — the
strong-form honesty-alpha claim.

If we miss them, the position is what Phase 5 showed: **narrow precision tool,
not alpha generator**. That's still a real product — just a different positioning.
