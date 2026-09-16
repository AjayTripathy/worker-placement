# Signal OS framework — consolidated findings + deployment plan

_Run 2026-05-25. Synthesizes Tier 1 + Tier 2 + Tier 3 + 24m extension._

## What we tested

| backtest | window | universe | result on basket | catastrophe recall |
|---|---|---|---|---|
| Tier 1 | 2025-05 → 2026-05 (12m) | 66 hand-picked distressed (32 removed + 34 controls) | LOOSE_LONG +64.6%, alpha +57.6 pp | **93%** |
| Tier 2 | 2025-05 → 2026-05 (12m) | 50 SP600 "boring middle" (-10% to -25% dd) | LOOSE_LONG +8.5%, alpha -0.7 pp | n/a (only 1 cat) |
| Tier 3 | 2024-05 → 2025-05 (12m) | 60 point-in-time distressed (≤-25% dd, no hindsight) | LOOSE_LONG -22.7%, alpha -8.6 pp | **85%** |
| Tier 3 @ 24m | 2024-05 → 2026-05 (24m) | same 60 names | LOOSE_LONG **+27.5%**, alpha **+17.4 pp** | **80%** |

## What's validated (high confidence)

1. **Catastrophe-detection is durable across windows, universes, and horizons.**
   80-93% recall on -40%-or-worse outcomes. Same recipe works on a hand-picked cohort, a mechanical point-in-time cohort, and at both 12-month and 24-month horizons.

2. **The framework's signal is HORIZON-conditional.** 12-month measurement clips the recovery signal because distressed-name reversals take 18-24 months. At 24m, the LONG basket generated +17 pp alpha on Tier 3 (vs -8.6 pp at 12m).

3. **The framework's signal is REGIME-conditional.** Works on distressed cohorts (Tier 1, Tier 3). Does not work on healthy small-caps (Tier 2 boring middle: -0.7 pp alpha, ρ=-0.053).

4. **The narrative-quality signal is real but not cleanly tunable.** Agents independently noted "honest disclosure" vs "obscuring" patterns in 50+ verdicts. The composite formula throws this away. A regex-based override fit on Tier 1 did NOT cleanly generalize to Tier 3 (caught 2 winners, 1 catastrophe, 8 noise — basket return improved via dilution not selection).

## What's NOT validated (don't claim)

- A LONG basket strategy that generates alpha at 12-month holds in continued-distress tapes
- Generalizability beyond distressed cohorts
- The specific +57.6 pp Tier 1 number as a forward expectation (regime-specific)
- The honesty-override rule as a deployable enhancement (failed OOS test)

## Option 1 deployment plan — catastrophe-avoidance overlay

**Thesis**: hold a passive small-cap position (IJR / IWM / a value sleeve). Quarterly, run the framework over current constituents. Underweight or hedge the SHORT-flagged names. Capture market beta + catastrophe-avoidance.

### Expected edge

Based on Tier 1 + Tier 3 catastrophe recall (80-93%):

- If your watchlist has a typical small-cap catastrophe rate (~3-5%/year for SP600; higher for distressed sleeves):
- Framework identifies ~80%+ of these names in advance
- Each avoided catastrophe is ~-40% to -100% on that position
- At a 5% portfolio weight per name: avoiding 80% of a 4%/year catastrophe rate saves ~0.5-1.5 pp/year of drawdown
- On a distressed sleeve (22% catastrophe rate): saves 4-8 pp/year

**This is not Sharpe-changing alpha for a diversified small-cap index. It IS meaningful for a distressed-value sleeve or trough-buying strategy.**

### Implementation

**Universe**: SP600 constituents (or your active small-cap watchlist).

**Frequency**: Quarterly. Score every name in your portfolio that had its most recent 10-K filed in the prior quarter.

**Inputs per ticker**:
- Most recent 10-K filed pre-decision-date
- All 10-Qs filed pre-decision-date
- The framework agents (existing prompt at `boring_middle_2025_05/AGENT_PROMPT.md` works; just swap cutoff date)

**Action rule**:

| Tier (deterministic composite) | Position action |
|---|---|
| STRICT_LONG (composite ≤0.20) | Normal weight |
| LOOSE_LONG (0.20 < composite ≤0.30) | Normal weight |
| NEUTRAL (0.30 < composite < 0.50) | Normal weight (no signal) |
| SHORT (composite ≥0.50) | **Halve position OR hedge with 12-month puts at -20% strike** |

Halve-don't-eliminate is the right default given the 22% precision (lots of SHORT-flagged names won't actually crash; you don't want to completely exit them).

### Honest expected performance

**Tier 3 (2024-05 → 2025-05) backtest as concrete example:**
- Universe (60 distressed): -14.1% over 12m, +10.1% over 24m
- If you'd held the universe equal-weight: -14.1% / +10.1%
- If you'd halved the 50 SHORT-flagged names: roughly cuts catastrophe loss exposure in half
- Estimated saved drawdown over 12m: 4-6 pp on the distressed-sleeve case
- Over 24m: signal degrades because some SHORTs (UNFI +379%, VSAT +286%) recover hard — you'd give up upside on the half-positions

**Critical implementation detail**: if your hold horizon is 12m, the catastrophe-avoidance overlay is net-positive. If your hold horizon is 24m+, the overlay leaves significant upside on the table because framework-SHORTs include big eventual recoveries. **Match the framework's measurement window to your hold horizon.**

### What this is NOT

- Not an alpha generator on its own. Use as a risk-management overlay.
- Not appropriate for non-distressed universes (Tier 2 showed no signal).
- Not appropriate if your hold horizon is >18 months (signal degrades).
- Not a put-buying alpha strategy (precision is too low for that).

## Bridge to Option 3 (recovery-signal layer)

The 24-month extension reveals interesting structure: **8 of the 10 biggest 24m winners (Tier 3) were framework-SHORT-flagged**. These are names where the framework correctly detected distress but the distress resolved over 18-24 months.

If we could distinguish "distress that resolves" from "distress that catastrophizes" with a complementary recovery-signal layer, the framework could generate genuine LONG alpha on 24m holds. Indicators worth building:

- Pre-cutoff insider buying (especially open-market by directors/officers)
- Lender concession (spread cut, maturity extension, revolver expansion) — distinct from amendment-with-tightening
- Cure language with quantified milestones AND Q1 progress against them
- Counterparty-mirror confirmation (the company's customers/lenders are showing increased commitment, not exit)

Validation path: 
1. Score these signals on the existing 120-pilot dataset (cheap, regex + structured re-prompting)
2. Test whether SHORT + recovery-signal > LONG-tier-by-composite predicts 24m outperformance
3. If yes, run a fresh 4th-window walk-forward with the integrated signal

Cost estimate: ~$50-150 of LLM cost for the rescoring + 2-3 days of analysis. Worth doing IF Option 1 is going to deploy real capital and you want a complementary long-side.

## Files

Tier 1: `verticals/public_co/data/_backtest/survivorship_2025_05/`
- `TIER1_RESULTS.md` — Tier 1 controls (placebo, ablation, blinding audit)
- `synthesis.json` — basket math
- `scores/pilot_*.json` — 64 pilots

Tier 2: `verticals/public_co/data/_backtest/boring_middle_2025_05/`
- `TIER2_RESULTS.md` — boring middle out-of-sample
- `synthesis.json`, `scores/`

Tier 3: `verticals/public_co/data/_backtest/walk_forward_2024_05/`
- `TIER3_RESULTS.md` — 12-month walk-forward
- `synthesis.json`, `scores/`
- `_unblinded/tier3_24m.json` — 24-month prices (NEW)

This synthesis: `verticals/public_co/data/_backtest/FINDINGS_AND_DEPLOYMENT.md`
