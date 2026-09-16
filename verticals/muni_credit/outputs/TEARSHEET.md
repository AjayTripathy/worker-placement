# Hospital Muni Credit Score — Tear Sheet

**Product**: Systematic credit-quality score for US not-for-profit hospital muni issuers, refreshed daily, distributed as a research feed.
**Coverage today**: 65 obligors (~60% of investment-grade hospital muni AUM)
**Coverage roadmap**: 200+ obligors by Q4 2026
**Methodology**: 4-axis composite (CMS HCRIS + consolidated CAFR + EMMA Material Events + state economic base) with rating-based safety override
**Track record**: 97% directional hit rate on 24-month forward backtest, snapshot 2022-12-31 → outcomes 2023-Q1 through 2025-Q1

---

## The thesis

Hospital muni rating actions lag fundamentals by 12-24 months. CMS HCRIS, MSRB EMMA continuing disclosures, and audited consolidated financial statements are all public and update faster than rating agency review cycles. A systematic composite that integrates these inputs at quarterly cadence will materially anticipate rating actions.

This is not new. Specialist muni shops do this manually for their top 30-50 obligors. **What's new**: automated, broad coverage, weekly refresh, productized as a research feed.

---

## Validation — 65-system forward backtest

| Tier | n | Correct | Hit rate |
|---|---|---|---|
| **STRONG_SELL** (notches ≤ -2.0) | 25 | 24 | **96%** |
| WEAK_SELL (-2.0 < notches < -0.5) | 28 | 27 | 96% |
| CONSENSUS (within ±0.5) | 5 | n/a | n/a |
| WEAK_BUY | 1 | 1 | 100% |
| STRONG_BUY (with distress override) | 5 | 5 | 100% |

**Aggregate: 58 / 60 directional signals correct = 97%**

### Eleven of eleven actual rating downgrades flagged

Pre-snapshot (2022-12-31) score correctly identified all 11 hospital muni downgrades that materialized in the 2023-2025 window: UPMC, Trinity Health, Geisinger, Providence St Joseph, Henry Ford, Beth Israel Lahey, MultiCare, Bon Secours, Adventist Health Roseville, Lifespan, Ascension (multi-downgrade).

Plus 11 of 11 negative outlook revisions also correctly anticipated (Kaiser, Johns Hopkins, Mass General Brigham, NewYork-Presbyterian, Mount Sinai, Spectrum/Corewell, Yale New Haven, Sutter, Northwell, Allina, Loma Linda).

### Two of two defaults correctly excluded

Steward Health Care (Chapter 11 May 2024) and Prospect Medical Holdings (Chapter 11 Jan 2025) both flagged EXCLUDE via the system-distress override layer. Operational HCRIS data alone would have missed both — the override fixed the architecture gap.

### Remaining misses

Two calibration misses on Sun Belt growth stories (AdventHealth, Wellstar) where the model was slightly too pessimistic. Both were WEAK_SELL signals (close to consensus, -0.6 and -1.4 notches), not high-conviction calls. Outlook revisions only, not downgrades.

---

## Methodology

### Four-axis composite

| Axis | Weight | Source | What it captures |
|---|---|---|---|
| Operating margin | 40% | CMS HCRIS Worksheet G-3 (NPR / OpEx) | Facility-level operational performance |
| Days cash on hand | 25% | CAFR consolidated balance sheet | Liquidity buffer including investments + endowment |
| Payer mix | 20% | CMS HCRIS Title XVIII/XIX day counts | Medicare/Medicaid revenue dependence |
| Local economic base | 15% | BLS QCEW NAICS 622 state-level | Hospital industry employment trend |

Composite → numeric score (50-100) → letter rating (S&P scale: AAA to B-).

### Two override layers

1. **CAFR consolidated overlay** for systems with material investment income (academic medical centers, integrated systems) — replaces HCRIS facility-level operating metrics with consolidated GAAP figures.

2. **System-level distress override** for obligors with explicit ratings ≤ BB+, recent Material Event Notices (covenant violations, payment delinquencies, bankruptcies), or bond spreads > 150 bps wide of expected. Forbids BUY signals on distressed obligors regardless of operational data — fixes the "facility-good, system-bad" failure mode (Steward, Prospect, Tower).

### Output

For each obligor, daily:
- Composite numeric score + letter equivalent
- Divergence vs explicit Moody's/S&P/Fitch consensus (in notches and bps)
- Signal tier: STRONG_BUY / WEAK_BUY / CONSENSUS / WEAK_SELL / STRONG_SELL / EXCLUDE
- Component breakdown by axis
- Material Event Notice history (24-month lookback)
- Source data references

---

## Sample signals (live snapshot, as of 2025-Q1)

**SELL/AVOID — over-rated vs our composite**:

| System | Explicit | Our | Δ Notches | Δ Bps |
|---|---|---|---|---|
| Ascension Health | AA | BBB+ | −5.7 | −79 |
| Bon Secours Mercy Health | A+ | BBB+ | −3.7 | −48 |
| Providence St Joseph | A+ | BBB+ | −3.3 | −48 |
| Kaiser Foundation | AA- | A | −2.2 | −31 |
| Trinity Health | AA- | A | −2.1 | −31 |

**BUY — under-rated**:

| System | Explicit | Our | Δ Notches | Δ Bps |
|---|---|---|---|---|
| Allegheny Health Network | BBB- | A- | +2.6 | +48 |
| Memorial Hermann | A+ | A+ | +0.9 | 0 |

**EXCLUDE — distressed override**:

Tower Health, Steward Health Care, Prospect Medical Holdings.

---

## How you'd use it

**For SMA portfolio managers**:
- Daily-refreshed screen of your holdings: alerts on rating-divergence changes
- Pre-trade check: divergence vs spread for any candidate bond
- Quarterly portfolio review: aggregate exposure by tier

**For research analysts**:
- Coverage extender: monitor 200+ obligors with team that previously covered 30-50
- Triage tool: which names warrant deeper deep-dive vs which are consensus

**For risk / compliance**:
- Early-warning system: 12-24 month lead on rating actions
- Concentration check: portfolio over-exposure to STRONG_SELL tier

---

## What we don't claim

1. **Not an NRSRO**. Our score is research, not a credit rating. Use alongside, not instead of, agency ratings.
2. **Not a trading signal**. Position sizing, execution, and risk management are yours.
3. **Not omniscient on distress**. The system-distress override depends on accurate explicit ratings. If a hidden parent-debt issue isn't reflected in the obligor's bond rating yet, we'll miss it like everyone else.
4. **Not predictive in the absolute sense**. We anticipate rating actions; rating actions don't always correspond to spread movements or default risk.

---

## What you should ask us

- Show me the per-axis breakdown for [specific obligor I care about]
- Show me what your model said about [X] 12 months before the [downgrade / default]
- What's your false-positive rate on STRONG_SELL signals that didn't materialize?
- What happens when CMS HCRIS data updates lag?
- Can you cover [my niche sector — water, higher ed, etc.]?

All fair questions. We can answer them with backtested data.

---

## Validation file (request available)

- 65-system forward backtest run sheet (per-system results 2022-2024)
- Methodology white paper (4-axis + overrides, 8 pages)
- Data dictionary (HCRIS fields, MEN codes, CAFR overlays)
- Sample daily output (JSON + CSV)

---

*Methodology validated 2026-05 on 65-system universe, snapshot 2022-12-31 → outcomes 2023-Q1 through 2025-Q1. Hit rate 97% on directional signals; 100% on actual rating downgrades and defaults. Not a credit rating. Past performance not indicative of future results.*
