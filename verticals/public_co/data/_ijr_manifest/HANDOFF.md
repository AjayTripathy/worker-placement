# IJR R/f/M Manifest — Session Handoff

**Date written**: 2026-05-26 (updated post-assumption-test)
**Reason**: Original session ran low on context after universe construction + assumption test. Continue in fresh session.

## ⚠️ READ FIRST: Assumption test results (drives priorities)

Before writing the manifest we ran the test-design math. Key findings:

**Forward returns measured** (608 IJR holdings as of 2024-06-30, prices via yfinance):
- 550/608 have full prices (58 yfinance failures due to ticker renames/mergers)
- IJR benchmark: 12m +5.80%, 24m +34.51%
- Universe equal-weight: 12m +5.91%, 24m +36.87%
- Universe cap-weight (static, no rebalancing): 12m +6.15%, 24m +35.12%
- Static-CW vs IJR-rebalanced: **+0.62 pp at 24m** = small rebalancing penalty

**Catastrophe distribution (24m, threshold ≤-30%)**:
- 99 names (18.0% by count, 17.70% by cap-weight) — distribution barely changes
- Mean catastrophe return: -50.7%
- Mean universe-ex-catastrophe: +52%

**Alpha math (cap-weighted vs IJR, 24m, by precision × recall):**
```
                  P=30%  P=50%  P=70%  P=80%  P=90%  P=100%
Recall=10%        +1.4   +1.8   +1.9   +1.9   +1.8   +2.1
Recall=25%        +2.9   +3.5   +4.0   +4.3   +4.3   +4.3
Recall=50%        +5.1   +7.7   +8.2   +8.3   +8.5   +8.6
Recall=75%        +9.5  +12.3  +13.0  +13.1  +13.3  +13.3
Recall=100%      +19.2  +18.6  +18.7  +18.7  +19.0  +18.6
```
Subtract +0.62 pp baseline to isolate framework's contribution alone.

**Key takeaways:**
1. Catastrophe-exclusion is asymmetric: each correctly-excluded catastrophe ADDS ~85 pp swing across the kept basket; each false exclusion subtracts only ~15 pp. **Framework can have ~5x false positives per true positive and still net positive.**
2. Break-even precision is shockingly low (~10-18% at any recall ≥ 25%).
3. Framework's Tier 1/3 recall was 85-93% — if that translates to IJR healthy universe, we'd see +15 to +20 pp alpha at 24m.
4. **The real risk is whether recall translates**: framework was trained on already-distressed pools. On a healthy IJR universe most names have no obvious distress signature, so deterministic m-source recall may drop to 20-50%. Even at 25% recall × 50% precision, math says +3.5 pp alpha. Still wins, but barely.

Files: `forward_returns.json` has the full per-ticker return data. 

---

## Big picture: what we're building & why

We're testing whether the **Signal OS framework's exclusion signal** (avoid framework-flagged distressed names) generates real alpha on a **broad healthy index** (IJR ~600 small-caps), not just on the curated distressed universes we've used so far (Tier 1 small-cap, Tier 3 walk-forward).

The Tier 3 recovery backtest showed:
- Bottom-quintile by recovery_signal_score reliably underperformed (10/12 lost money)
- Top-quintile dispersion was high (selection unreliable)
- Result: framework's value is **catastrophe-exclusion**, not stock-picking

To test if the catastrophe-exclusion signal generalizes to the full small-cap index, we need to run the framework on all of IJR. But running the **agentic R/f/M scorer** on 600 names is ~$2-3k tokens and days of wall-clock.

The user's better idea (which is what THIS work supports): **before running anything, build the R/f/M manifest for the universe — diligencing all 600 names conceptually — and identify which f(M) checks we already have versus which deterministic gaps are worth building**. Then we can run a $0-token deterministic test on the full universe, escalating to agentic only where deterministic can't substitute.

## Current state

### ✅ DONE (this session)

1. **Universe acquired**: 608 IJR equity holdings as of 2024-06-30 (closest authoritative N-PORT-P quarter-end to our 2024-05-15 target cutoff). Source: SEC EDGAR series S000004313, accession 0001752724-24-191760.

2. **Enrichment**: 598/608 have SIC codes. 599/608 have CIKs. 9 unmapped (acquisitions, ticker variants — ~1.5% noise, acceptable).

3. **Clustering**: 26 GICS-style clusters. Top 6 cover 348/608 (57%):
   - FINANCIALS (106), REAL_ESTATE (56), INDUSTRIALS_MACHINERY (33), TECH_HARDWARE (31), BUSINESS_SERVICES (30), MATERIALS_CHEMICALS (30)
   - **Known SIC misclassifications to override**: MARA (bitcoin miner, mis-classified as FINANCIALS), MOG/A (Moog/defense, mis-classified via stale broker-dealer SIC), CMA (Comerica/bank, mis-classified via pharma SIC). Plan: hand-fix during manifest review.

### Files in `verticals/public_co/data/_ijr_manifest/`

- `ijr_holdings_2024_06_30.json` — 608 holdings × {ticker, cik, name, sic, sicDescription, value_usd, shares, gics_sector, cluster, ...}
- `cluster_summary.json` — 26 clusters × {n_holdings, top_sics, 8 representative_samples}
- `forward_returns.json` — per-ticker 12m + 24m returns vs IJR benchmark
- `ijr_holdings_raw_2024_03_31.json` — legacy parse from N-CSR (creation basket, ~120 names; obsolete now, can delete)

## ✅ TODO in next session

### Task #34: Generate per-cluster R/f/M manifest

For each of the 26 clusters, produce a section in `MANIFEST.md` covering:
- **Cluster** (name + holdings count)
- **Representative samples** (5-8 by value)
- **Archetypal R-claims** (5-10 claims companies in this cluster make in their 10-K, ranked by relevance to catastrophe/recovery detection)
- **f(M) for each R-claim** (the verification source: existing m-source module OR a noted gap)
- **Coverage notes** (which R-claims are deterministic-verifiable; which require LLM narrative)

Format suggestion (per cluster):

```markdown
## FINANCIALS (n=106)

**Top SICs**: State Commercial Banks (28), National Commercial Banks (22), Fire/Marine Casualty (10), Investment Advice (8), Savings Institutions (6), Brokers/Dealers (5)

**Representative samples**: COOP (Mr Cooper Mortgage), AGO (Assured Guaranty Surety), LNC (Lincoln National Life)...

### R/f/M tuples for this cluster

| # | R-claim (archetypal) | f(M) source | Existing m-source | Coverage |
|---|---------------------|-------------|-------------------|----------|
| 1 | Bank deposits stable, no run risk | FDIC Call Report deposit composition | `fdic_call_reports.py` ✅ | Banks-only |
| 2 | Loan portfolio quality / NPL ratios | FDIC Call Report + 10-K Item 7 | `fdic_call_reports.py` ✅ partial | Banks-only |
| 3 | Insurance reserves adequate | A.M. Best ratings + state insurance dept filings | ❌ GAP: `insurance_reserves.py` | Insurance ~30 names |
| 4 | Broker-dealer in good standing | FINRA BrokerCheck | `finra_brokercheck.py` ✅ | Brokers ~5 names |
| 5 | No undisclosed self-dealing | Form 4 patterns + 8-K transactions | `form4.py` + `insider_buy_timing.py` ✅ | Universal |
| 6 | Capital ratios meet regulatory min | Bank-specific call reports / SEC Item 7 | `fdic_call_reports.py` ✅ partial | Banks |
| ... | ... | ... | ... | ... |
```

### Task #35: Gap consolidation + prioritization

After all 26 clusters have manifests, consolidate the `❌ GAP` items into:

- `GAPS.md` — ranked list of m-sources to build, scored by (coverage_count × determinism_score × signal_strength) / build_effort
- `NARRATIVE_ONLY.md` — R-claims that can only be verified by LLM (e.g., TAM inflation, customer mix qualitative)

## Existing m-source inventory (for cross-reference)

```
~25 modules in verticals/public_co/m_sources/
Universal: filing_timeliness, mw_lifecycle, lender_concession, auditor_change_tracker, 
           going_concern_detector, claim_evolution, form4, insider_buy_timing,
           insider_vs_calendar, sec_filings, edgar_fts, megacap_namecheck,
           revenue_concentration, acq_coherence, iborrow, counterparty_reciprocity
Defense/Gov: pentagon_jbook, ic_contracting_proxy, cybercom_budget, doe_budget,
             nasa_ntrs, earmark_detector, usaspending, sam_entity
Healthcare: clinical_trials, openfda
Financial: finra_brokercheck, fdic_call_reports
Industrial: osha_establishments, fmcsa, nhtsa, epa_emissions, epa_frs
Other: dol_h1b_lca, bls_qcew, nrel_fuel, google_patents, uspto_odp, ucc_proxy, az_corp
```

## Context for resumption

- See user's memory: [feedback_honesty_alpha_framework], [feedback_dd_two_modes], [project_smallcap_honesty_strategy]
- Token budget for manifest: ~300-400k of fresh-session Claude-Opus
- User's preference: do this MYSELF, no subagents
- Output grain: sector-archetypal, not per-name overrides for outliers

## Open methodology decisions to revisit

1. **Recovery vs Distress scoring** — manifest should cover BOTH catastrophe-detection R-claims (likely 60-70%) AND recovery-signal R-claims (30-40%)
2. **Coverage measurement** — for the eventual IJR exclusion test, what fraction of names get at least 3 m-source checks? Manifest should make this answerable.
3. **Candidate m-source mechanism** — if during manifest review you spot R-claims that suggest a new deterministic m-source we hadn't thought of, flag it (this is the "you can invent new m-sources" point from earlier in the project)

## How to resume

```bash
cd /Users/ajay/exalted/signalos
cat verticals/public_co/data/_ijr_manifest/HANDOFF.md  # this file
cat verticals/public_co/data/_ijr_manifest/cluster_summary.json  # cluster reps
ls verticals/public_co/m_sources/  # existing m-source inventory
```

Then start writing `verticals/public_co/data/_ijr_manifest/MANIFEST.md` per the format above. Estimate ~150-300 lines total at terse format, ~400-600 at detailed.

Mark TaskList #34 as in_progress before starting, #35 pending until #34 done.
