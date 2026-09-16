# Hospital Muni Credit MVP — Scope & Build Plan

**Date**: 2026-05-27
**Status**: Proposed
**Owner**: TBD

## Thesis

Hospital revenue bonds are the cleanest small-issue inefficiency in the muni market:

- ~$300B outstanding across ~500 obligated issuers
- The canonical authority for the financial inputs that determine credit quality (**CMS HCRIS** Worksheet E + balance sheet items) is free, federal, and structured
- Rating agencies (Moody's, S&P, Fitch) update hospital ratings on 1-3 year cycles using stale CAFR data
- We already built `cms_cost_reports.py` and validated CMS data extraction works end-to-end (Ensign Group test: 12 CCN match, healthy SNF margin signal)
- Most muni SMAs (Parametric, Nuveen, BlackRock) can't deploy capital efficiently into <$50M individual issues — leaves the small-issue alpha unharvested

**Alpha hypothesis**: A model that scores each hospital obligor's true credit using CMS HCRIS + state regulatory data — and benchmarks that against the explicit Moody's/S&P/Fitch rating — will identify under-rated and over-rated issuers ≥6 months before rating agencies act. The under-rated cohort tightens spreads; the over-rated cohort widens.

This is the muni-credit version of the honesty-alpha framework, applied where canonical authorities are dense.

---

## What we already have that applies

| Component | Status | Usage in this MVP |
|---|---|---|
| `cms_cost_reports.py` | Built + validated | Pull hospital financials per CCN |
| `llm_10k_extract.py` | Built + validated | Extract CCN rosters + obligor data from Official Statements |
| `xbrl_panel.py` | Built | Not directly (munis don't XBRL); methodology pattern reusable |
| `revenue_concentration.py` | Built | Apply to hospital payer-mix concentration |
| `bls_qcew.py` | Built | Local economic-base context for issuer's service area |
| `epa_emissions.py` | Built | Some hospital obligors have environmental exposure |
| f(M) / R/f/M methodology | Validated (Parametric DD, AHC) | Per-claim canonical-authority verification |
| Form ADV pull + parsing | Built | Apply to muni manager DD if needed |

**What needs to be built fresh**:
1. MSRB EMMA universe crawler — pull all hospital revenue bond CUSIPs + continuing disclosures
2. Obligor → CCN mapping at scale (~500 hospital systems)
3. Hospital-specific composite score model
4. MMD AAA curve integration for spread-to-benchmark
5. Backtest harness (snapshot-and-forward-return for muni spreads)

---

## Universe definition

**Target**: US tax-exempt hospital revenue bonds, outstanding, $5M+ par per issue, taxable equivalent if any.

**Filters**:
- Sector code: hospital / health care system (MSRB classification)
- Outstanding (not redeemed/called)
- Conduit issuer + obligor structure (state hospital authority issues; hospital system is obligated party)
- Exclude: critical access hospitals if HCRIS data sparse, federal/military hospitals
- Time range: 2018-2026 for backtest

**Expected universe**: 500-800 obligated hospital systems, 30K-60K active CUSIPs

**How we pull it**:
- MSRB EMMA (free, public): `emma.msrb.org/Search/Issuer` filtering by sector
- For each obligor, pull continuing disclosure filings (CDFs) — annual financial reports posted to EMMA
- Cross-reference with American Hospital Association's hospital directory if needed
- Final obligor list mapped to CCNs (next section)

---

## Obligor → CMS CCN mapping

This is the single biggest data engineering task. Each hospital system might:
- File OS as a single "obligor" but operate 5-50 facilities under different CCNs
- Have a parent holding (e.g., HCA, Tenet) with regional subsidiaries
- Restructure obligors over time as systems acquire/divest hospitals

**Approach (3 layers)**:

1. **LLM extraction from OS** (HEALTHCARE_SERVICES schema, already built): for each obligor in the universe, pull most recent OS PDF from EMMA, LLM-extract facility roster with CCNs. We did this for Ensign (returned 1 CCN — sparse). Hospital systems typically disclose more.

2. **CMS Provider of Services file** (free quarterly): name-based fuzzy match obligor → POS file → CCN list with state, address, capacity.

3. **Hospital Compare + HCRIS cross-validation**: for each candidate CCN, validate it exists in HCRIS data + appears as expected facility type.

**Expected coverage**:
- LLM extraction: ~60% of obligors get clean CCN list
- POS file fuzzy match: covers another ~25%
- Manual curation for top 50 systems (~15%) to start the dataset

**Validation**: total facility count from our mapping × average revenue per facility should match obligor's audited financial revenue from CAFR.

---

## True credit score model

Composite Z-score across 4 axes, each axis sourced from a canonical authority.

### Axis 1 — Operating margin trajectory (40% weight)

**Inputs (CMS HCRIS)**:
- Net Income from service to patients / Net Patient Revenue
- 3yr YoY trend
- Volatility (std dev across 5 years)

**Scoring**:
- ≥ +3% operating margin, improving → AAA equivalent
- 0% to +3%, stable → AA equivalent
- −3% to 0% → A
- −6% to −3% → BBB
- < −6% → BB or below

**Why this matters**: Operating margin is the most direct measure of whether the hospital generates enough cash to service debt. CMS HCRIS Worksheet E is the canonical source and the rating agencies use it (lagged by 9-18 months).

### Axis 2 — Days cash on hand (25% weight)

**Inputs (CMS HCRIS balance sheet)**:
- Cash + STI / (Total Operating Expenses / 365)

**Scoring**:
- ≥ 250 days → AAA
- 150-250 days → AA
- 75-150 days → A
- 25-75 days → BBB
- < 25 days → BB or below

### Axis 3 — Payer-mix concentration (20% weight)

**Inputs (CMS HCRIS Title-day breakdown + revenue mix)**:
- % revenue from Medicare (Title XVIII)
- % from Medicaid (Title XIX) — higher = more reimbursement risk
- % uncompensated care

**Scoring**:
- Medicaid + uncompensated <30%, Medicare <60% → favorable
- Medicaid + uncompensated 30-50% → mixed
- Medicaid + uncompensated >50% → adverse (safety net hospitals)

### Axis 4 — Local economic base + competitive position (15% weight)

**Inputs**:
- BLS QCEW employment in service area NAICS 622 (hospitals) — growth signals
- Census ACS demographic trends (population growth, median age, insurance coverage)
- HRSA hospital service area data
- Local market share if available

**Scoring**:
- Service area pop growth ≥ +1%, median age stable, multiple competitors → favorable
- Pop decline, single-hospital town → adverse

### Final composite score

Weighted sum → mapped to letter rating equivalent (AAA, AA, A, BBB, BB, B, CCC, distressed).

**Divergence signal** = our letter rating MINUS explicit Moody's/S&P/Fitch rating.

- +2 notches or more (we say AA, they say BBB+) → strong BUY signal
- +1 notch → weak BUY
- 0 → consensus
- −1 notch → weak SELL
- −2 or more → strong SELL

---

## Backtest design

### Snapshot framework

Pick historical snapshots: **2018-12-31, 2020-06-30, 2022-06-30** (3 cuts).

At each snapshot:
1. Build universe of hospital obligors with CMS HCRIS data and outstanding bonds
2. Compute composite score using ONLY data available at that date (no look-ahead — CAFRs are 9-15 months delayed; HCRIS data is ~12 months delayed)
3. Pull explicit ratings from MSRB EMMA / Bloomberg as of that date
4. Compute divergence signal

### Forward outcome measurement

For each obligor in the snapshot, measure 12m, 24m, 36m forward:
1. **Rating migration**: did Moody's/S&P/Fitch upgrade or downgrade?
2. **Spread change**: bond's option-adjusted spread to MMD AAA, change vs benchmark
3. **Default/restructuring event**: did the obligor default, file Chapter 9/11, or undergo material restructuring?

### Hit rate metrics

Primary metric: of our "strong BUY" basket (+2 notches), what % experienced rating upgrade OR ≥25bps spread tightening at 24m?

Target: ≥55% (vs ~33% random baseline if 3 outcomes are roughly equiprobable).

Secondary metric: spread compression on EW basket of "strong BUY" vs same-rating-class benchmark. Target: ≥10 bps net of bid-ask.

### Survivorship-bias controls

Critical for muni backtests:
- **Include defaulted obligors** (Steward Health Care, Westchester Medical, etc.) at their pre-default snapshot dates
- **Track called bonds** as a separate outcome (mandatory redemption ≠ market signal)
- **Track restructured bonds** explicitly — some "spread tightening" comes from credit-event recovery

---

## Build phases (8-week MVP)

### Phase 0 — Pre-work (~3 days)

- Confirm MSRB EMMA crawler access + rate limits
- Source MMD AAA curve (ICE Data Services has historical; ~$5K/yr license)
- Pick 50-name pilot subset (mix of credit qualities) for initial validation
- Procure Bloomberg terminal or equivalent for explicit rating history (if needed)

### Phase 1 — Universe + data acquisition (Week 1-2)

- MSRB EMMA crawler: pull all hospital revenue bond CUSIPs outstanding
- For each obligor: pull most recent OS PDF + continuing disclosures
- LLM-extract obligor → CCN mapping for top 100 systems
- POS file fuzzy match for next 200 systems
- Manual curation for any high-priority gaps
- **Deliverable**: `data/hospital_muni_universe.json` with ~300 obligors, each mapped to CCN list, outstanding CUSIPs, and CDFs

### Phase 2 — Score engine (Week 3-4)

- Extend `cms_cost_reports.py` with hospital-specific Worksheet E fields
- Build composite scoring function: 4 axes → letter rating
- Validate on top 50 systems: does our score correlate with explicit ratings?
  - Target: 70%+ correlation (we should mostly agree with agencies; divergences are the alpha)
- Tune weights using only training subset (e.g., top 30 systems)
- **Deliverable**: `composite_score.py` + `validation_report.md`

### Phase 3 — Backtest harness (Week 5-6)

- Build snapshot framework with point-in-time correct HCRIS data
- Compute forward spread changes using MSRB trade data + MMD benchmark
- Track rating migrations from agency action reports
- Compute hit-rate + spread compression metrics
- Bootstrap confidence intervals
- **Deliverable**: `backtest_report.md` with results across 3 snapshot dates

### Phase 4 — Production prototype (Week 7-8)

If backtest hits success criteria:
- Daily refresh pipeline (CMS HCRIS quarterly update + MSRB CDF event listener)
- Dashboard: top 20 most-under-rated + top 20 most-over-rated
- Alert system: notify when score changes by 1+ notch OR explicit rating changes
- Documentation + onboarding doc for first external user
- **Deliverable**: `dashboard.html` + `daily_refresh.py` + `top_signals.json`

---

## Decision gates

| Week | Gate | Pass criteria | If fail |
|---|---|---|---|
| 2 | Coverage | ≥200 obligors mapped to CCNs with HCRIS data | Pivot to top-50-system focus |
| 4 | Score validity | ≥70% correlation with explicit ratings | Rework axis weights |
| 6 | Backtest hit-rate | ≥55% on strong-BUY basket at 24m | Pivot or kill |
| 6 | Spread compression | ≥10 bps net on EW BUY basket | Pivot or kill |
| 8 | Production readiness | Daily refresh works + 3+ external use cases | Iterate before commercializing |

---

## Resource requirements

| Resource | MVP estimate | Notes |
|---|---|---|
| Engineering (8 weeks) | 1.5 senior engineers | ~$100K loaded cost |
| Data licensing | ~$30K/yr | ICE MMD curve ($5K), MSRB EMMA (free), HCRIS (free), Bloomberg ($25K opt) |
| Compute | <$1K | Local + light cloud |
| Legal | ~$10K | Compliance review for score-publishing model |
| LLM API | ~$2K | One-shot LLM extraction across ~500 OS PDFs |
| **Total MVP** | **~$150K** | All-in for 8-week proof |

---

## Commercialization paths

If backtest validates:

### Path A — License the score feed (asset-light)

Sell to existing muni SMA managers + RIA platforms:
- Parametric, Nuveen, BlackRock SMA, Wasmer Schroeder, Eaton Vance Tax-Managed, Western Asset
- Schwab, Fidelity, LPL platforms for advisor-facing tools
- Pricing: $25K-100K/yr per manager (depending on AUM tier)
- Target: 10 licensees in year 1 = $500K-1M ARR
- Margin: software business, ~70% gross margin after data costs

### Path B — Launch focused fund

Niche fund product targeting small-issue muni inefficiency:
- Target AUM: $50-200M
- Strategy: long under-rated A/BBB hospital munis vs short over-rated AA hospital munis (within sector)
- Fee: 50-80 bps mgmt (higher than passive but justified by signal)
- Capacity-limited: cap at ~$200M before efficiency degrades
- Margin: traditional asset management economics

### Path C — White-label to advisor platforms

Build the score → embed in advisor UI at Schwab/Fidelity/LPL:
- Per-advisor or per-account licensing
- ~$5-10 per account per year
- Scales to millions of accounts with no marginal cost
- Margin: SaaS economics

### Recommended: A → C transition

Start with Path A (license feed to 3-5 muni managers as design partners). Once we have 2 years of live track record, expand to Path C. Avoid Path B initially because launching a fund adds 18 months of compliance work that competes with the engineering build.

---

## Risks (and mitigations)

### R1 — CMS HCRIS data lag

HCRIS data has ~12-month lag. Our model can't beat agencies on names where everyone is working off the same lagged data.
- **Mitigation**: layer in continuous-disclosure event triggers from MSRB EMMA — material events (CFO departure, missed covenant, large operating loss) appear on EMMA in real-time and supplement the lagged HCRIS data.

### R2 — Obligor structure complexity

A "system" obligor might issue debt for 30 facilities; some are strong, some are weak. Our composite score on the aggregate could mask underlying mix.
- **Mitigation**: provide both system-level and facility-weighted breakdowns; flag systems with high dispersion (one facility carrying the rest).

### R3 — Cross-default and parent-guarantee structures

Some bonds have parent guarantees that make obligor analysis less relevant.
- **Mitigation**: parse bond covenants (LLM extraction from OS) to identify guarantee structures and adjust scoring.

### R4 — Survivorship bias

Defaulted hospitals (Steward, etc.) need to remain in the dataset.
- **Mitigation**: build dataset from snapshot dates backward; include all then-outstanding obligors regardless of subsequent status.

### R5 — Liquidity friction in execution

Small-issue muni bid-ask is 50-200 bps. Backtest alpha must net of realistic transaction costs.
- **Mitigation**: model 75-100 bps round-trip costs in backtest; alpha must clear that threshold to be productizable.

### R6 — Rating agency lag could shrink

Rating agencies have been getting faster (post-financial-crisis pressure). If the lag compresses, our edge compresses.
- **Mitigation**: focus on signals agencies *can't* see — granular CMS quality scores, demographic shifts, payer-mix evolution — not just margin trends agencies will eventually catch.

### R7 — Regulatory: publishing scores

Publishing "Hospital X is over-rated" scores attracts liability. The big rating agencies have NRSRO designation; we don't.
- **Mitigation**: position as "factor research" not "credit ratings." Add boilerplate language. Consult securities counsel before any external publication.

### R8 — Competing infrastructure exists

Nuveen, Eaton Vance, Western Asset all have internal muni credit research teams that do versions of this.
- **Mitigation**: our edge isn't "we do credit research" — it's "we systematically apply canonical-authority cross-checks at scale across the full universe, not just the top 50 names." Small-issue obligors don't get covered by big internal teams.

---

## Why this MVP is uniquely well-suited to Signal OS

1. **Methodology fit**: this IS the honesty-alpha framework — canonical-authority cross-check (CMS HCRIS) vs claimed/disclosed credit quality (CAFR + rating)
2. **Reused infrastructure**: ~5 already-built m-sources directly apply (`cms_cost_reports`, `llm_10k_extract`, `bls_qcew`, `epa_frs`, `revenue_concentration`)
3. **Validated capability**: Phase 5 of the IJR backtest already validated that openFDA recall = canonical-authority catastrophe detection works at 38% precision (devices); CMS HCRIS for hospitals is the same pattern
4. **Differentiated wedge**: no existing manager systematically applies authority cross-checks at universe scale; the big ones can't deploy capital into small issues anyway
5. **Tractable scope**: 8 weeks of engineering + ~$150K, not a multi-year build

---

## What I'd actually do this week

If you give this green light:

**Day 1-2**: Pick top 10 hospital systems by outstanding bond debt (HCA-issuing entities like Health Trust Inc, Cleveland Clinic Health System, Sutter Health, Mayo Clinic, etc.). Pull their most recent OS from EMMA.

**Day 3-4**: Run `llm_10k_extract.py` with HEALTHCARE_SERVICES schema on those 10 OS PDFs. Validate CCN mapping completeness.

**Day 5**: For each of the 10 systems, run `cms_cost_reports.query_operator_margin` on their mapped CCNs. Pull most recent 3-year financial trajectory.

**Day 6-7**: Compare our 10-system credit signals to their explicit ratings. Where do we agree, where do we disagree? Are the disagreements explainable (e.g., we see negative margin trend that hasn't shown up in current rating yet)?

Outcome: by end of week, you have a 10-name proof of concept showing the signal is computable and produces non-trivial divergences from rating agencies. If yes → full MVP. If no → debug or kill.

---

## Files this would produce

```
verticals/muni_credit/
├── HOSPITAL_MUNI_MVP_SCOPE.md      (this doc)
├── data/
│   ├── hospital_obligor_universe.json
│   ├── obligor_ccn_mapping.json
│   ├── hcris_panel.json
│   ├── ratings_history.json
│   └── mmd_curve.csv
├── pipeline/
│   ├── emma_crawler.py
│   ├── obligor_mapper.py
│   ├── composite_score.py
│   ├── backtest_harness.py
│   └── daily_refresh.py
├── outputs/
│   ├── backtest_report.md
│   ├── top_signals_<date>.json
│   └── dashboard/
└── m_sources/
    └── msrb_emma.py    (new — universal EMMA connector)
```

Next decision: greenlight the 10-name proof-of-concept (5-7 days, ~$5K of engineering time + LLM costs)?
