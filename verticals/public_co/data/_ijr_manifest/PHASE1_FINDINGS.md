# IJR Phase-1 Backtest — Findings

**Date**: 2026-05-26
**Universe**: 599 IJR holdings with CIK, cutoff 2024-05-15, 12m/24m forward returns
**Battery**: 10 universal m-sources (cik+cutoff only; no curated inputs)

## Headline result

**The honesty-alpha exclusion thesis did NOT generalize from distressed pools to the healthy IJR universe.**

Exclusion test (the framework's core claim — drop the highest-distress names, alpha vs IJR should be positive):

| Cut | n kept | 12m EW | vs IJR | 24m EW | vs IJR |
|---|---|---|---|---|---|
| Universe-EW (baseline) | 548 | +5.88% | +0.07pp | +36.79% | +2.29pp |
| Drop top 10% distress | 493 | +6.23% | +0.42pp | +34.76% | +0.26pp |
| Drop top 20% distress | 438 | +5.62% | **−0.18pp** | +32.70% | **−1.81pp** |
| Drop top 30% distress | 383 | +5.10% | **−0.70pp** | +30.05% | **−4.46pp** |

Versus HANDOFF's pre-test math which projected +3.5 to +20 pp alpha depending on recall — we got **−4.5 pp at the 30% cut**. Framework exclusion HURT performance.

## Distress decile gradient is INVERTED

| dec | n | mean_dist | 12m_avg | 24m_avg |
|---|---|---|---|---|
| 1 (lowest distress) | 54 | 0.000 | +5.55% | +22.38% |
| 2 | 54 | 0.000 | −1.85% | +7.37% |
| 5 | 54 | 0.000 | +9.83% | +33.37% |
| 7 | 54 | 0.100 | +3.19% | +47.03% |
| 8 | 54 | 0.172 | +8.27% | +61.47% |
| 9 | 54 | 0.200 | +14.13% | +57.77% |
| 10 (highest distress) | 62 | 0.347 | +2.88% | +50.42% |

High-distress names OUTPERFORMED at 24m (+47-61%) vs low-distress (+7-33%). This is the opposite of the framework's prediction.

Plausible reads:
1. 2024-2026 was a strong small-cap mean-reversion regime that favored "distressed" (deep value) over "clean" (quality)
2. The universal battery is signaling "value" (covenant amendments, dilution, working-capital strain) which is bid in this regime
3. The framework was trained on distressed-pool data where these signals correlate with bankruptcy; on a healthy IJR universe they correlate with deep value

## SHORT_TIER did show 1 textbook catch

The framework's highest-conviction shorts (n=6, distress ≥ 0.50):

| ticker | cluster | distress | 12m | 24m | call |
|---|---|---|---|---|---|
| **MARA** | FINANCIALS (misclass — bitcoin miner) | 0.60 | −21.2% | **−28.7%** | **TRUE POSITIVE**: −63pp vs IJR |
| CMA | MATERIALS_CHEMICALS (misclass — bank) | 0.80 | n/a | n/a | False positive: WC/runway modules applied to a bank |
| PTEN | ENERGY | 0.70 | −39.1% | +32.4% | Mixed (12m correct, 24m wrong) |
| EFC | REAL_ESTATE | 0.60 | +22.0% | +39.7% | False positive: mREIT growth via issuance |
| KLG | MATERIALS_METALS (misclass — cereal) | 0.80 | n/a | n/a | No return data |
| VVI | CONSUMER_RETAIL | 0.70 | n/a | n/a | No return data |

MARA is the textbook catch the framework was designed for. EFC and CMA are clean false-positives from applying universal modules to clusters where they shouldn't run (mortgage REIT growth model, bank balance sheet).

## Tier distribution is degenerate

| tier | n | % |
|---|---|---|
| HIGH_CONV_LONG | 592 | 98.8% |
| SHORT_TIER | 6 | 1.0% |
| LONG_TIER | 1 | 0.2% |

The composite math (`recovery >= 0.30 AND distress <= 0.50 → HIGH_CONV_LONG`) is too permissive. Healthy companies naturally emit 5-7 PASS+positive on a 10-module battery, putting recovery=0.5-0.7 and distress=0.0 → automatic HIGH_CONV_LONG. **No meaningful discrimination within the LONG basket.**

## Cluster dispersion dominated any composite signal

The 24m return spread across clusters was extreme:
- TECH_HARDWARE: +191% (AI infrastructure boom)
- COMMUNICATIONS: +133%
- INDUSTRIALS_ELECTRICAL: +110%
- MATERIALS_METALS: +85%
- FINANCIALS: +48%
- vs HEALTHCARE_DEVICES: −16%, CONSUMER_STAPLES_FOOD: −25%

A naive "buy TECH_HARDWARE + sell HEALTHCARE_DEVICES" would have generated more alpha than anything the m-source battery produced.

## What this means

**The framework is not (yet) generating alpha on the healthy IJR universe via the universal battery.** Three branches forward:

1. **Methodology debate**: argue 2024-2026 was hostile to the strategy (small-cap value/junk rally), and re-run on a different period (e.g., 2021-2023 covering Covid recovery + rate-hike phase). HANDOFF noted the historical Tier 1/3 backtests showed 85-93% recall on *distressed* universes.

2. **Add cluster-specific signals** (Phase 2): apply m-sources only where they belong. Banks shouldn't get WC/runway checks. mREITs shouldn't get share_count_drift as a negative signal (their growth model is issuance). REITs should get tenant_credit_watch. Healthcare should get CMS cost reports. This requires per-name input curation we don't yet have.

3. **Re-tune composite**: the 0.30 recovery / 0.50 distress thresholds are too permissive. Raise to 0.60 recovery / 0.20 distress for HIGH_CONV_LONG. Add a "HIGH_CONV_AVOID" tier at recovery <= 0.40 AND distress >= 0.20 — currently SHORT_TIER fires too rarely.

## Files

- `phase1_scores.json` — per-ticker rfm_tuples + composite (599 names, 0 errors)
- `ijr_universe_runner.py` — runner (37 min wall on 6 workers)
- `ijr_backtest_analyze.py` — analyzer (deciles, tiers, exclusion test)
