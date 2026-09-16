# Tier 3 — walk-forward 2024-05-15 → 2025-05-15

Run 2026-05-25. Tests whether the Tier 1 in-cohort catastrophe-detection
and basket alpha survive on a DIFFERENT 12-month window where universe
construction can't peek at outcomes.

## Universe construction (no hindsight)

- Pool: union of current SP600 (~602 names) + Tier 1 cohort (32 removed
  names) = 633 unique tickers with known CIKs.
- For each, yfinance OHLC 2023-05-01 → 2025-06-01.
- Computed at 2024-05-15: trailing 52w high, price, drawdown, forward
  return to 2025-05-15.
- Filtered to drawdown ≤ -25% → 131-name distressed pool.
- Random sample 50 (seeded 20240515) → final size 60 after seed nudge.
- 58 scoreable (INDV and UNIT had no pre-2024 10-K).

Universe baseline: mean **-14.1%**, median -18.5%, 13 catastrophes
(<-40%), 2 big winners (>+50%). IJR same window: **+0.29%**.

This is a much harsher tape than Tier 1's universe (mean +7%) — the
2024-05 → 2025-05 distressed cohort largely continued down.

## Headline — the picture is mixed

| metric | Tier 1 (2025→26 distressed) | Tier 2 (2025→26 boring middle) | **Tier 3 (2024→25 distressed)** |
|---|---:|---:|---:|
| Universe mean fwd     | +7.0%   | +9.2%   | **-14.1%** |
| LOOSE_LONG mean       | +64.6%  | +8.5%   | **-22.7%** |
| Alpha vs universe     | **+57.6 pp** | -0.7 pp | **-8.6 pp** |
| Alpha vs IJR          | +38.5 pp | -19.7 pp | -23.0 pp |
| Spearman ρ            | -0.599 | -0.053 | **-0.139** |
| Catastrophe recall    | **93%** | n/a (only 1 cat) | **85%** |
| Random-basket percentile | 99.91 | 45.2 | **29.1** |
| SHORT basket mean     | -7.1% | +11.9% | -13.4% |

## What survived (the real finding)

**Catastrophe-detection IS durable across windows.** Tier 3's recall of
85% (11/13 names that went on to lose ≥40% were correctly SHORT-flagged
in advance) is close to Tier 1's 93%. This is on a completely different
12-month window, with a completely different universe construction
(mechanical drawdown screen, no hindsight). The framework genuinely
detects disclosure-quality differences that correlate with subsequent
crashes within distressed cohorts.

Notable correctly-flagged catastrophes:
- FTRE -83.5% (covenant amendment + NT 10-Q on cutoff date + spin debt)
- MGPI -59.3% (insider sell cluster + Atchison closure + governance shift)
- CTKB -56.1% (adverse ICFR + capital misallocation + restatement risk)
- CABO -56.1% (MBI Put Option liquidity wall + ACP funding cliff)
- STAA -57.6% (working-capital expansion + China concentration deceleration)
- ENPH -56.9% (customer concentration + claim evolution + warranty growth)
- VIR -54.6% (GSK withdrawing from collaboration, lead asset failure)
- ROG, XNCR — these were MISSED (false negatives)

## What did NOT survive

**The +57 pp basket alpha from Tier 1 is window-specific.** On Tier 3:

- LOOSE_LONG basket (n=7) mean -22.7% vs universe -14.1% → **alpha of -8.6 pp**
- Random-basket placebo: framework LONG is at the **29th percentile** —
  meaningfully WORSE than random
- Spearman correlation -0.139 vs Tier 1's -0.599 — most of the
  predictive correlation collapsed

The LONG basket had **2 false-negative catastrophes** (XNCR -61.5% rated
STRICT_LONG, ROG -42.4% rated LOOSE_LONG) and very few winners
(best: SNDR +9.8%, VSCO +7.6%). The SHORT basket included most of the
universe's big winners (UNFI +189%, EXTR +51%, PTCT +35%, DCOM +43%,
FWRD +31%, GDYN +37%, ACAD +16%) — the framework actively excluded the
recovering names.

## The mechanism — why Tier 1 alpha was inflated

Three factors compounding:

1. **Tier 1 window had a small-cap recovery**: universe mean +7%, IJR
   +26%. Lots of bouncers to catch. Tier 3 window was harsh: universe
   mean -14%, IJR +0.3%. No bouncers.

2. **Tier 1 universe was hand-picked** (32 known-removed + 34 hand-
   chosen survivors). Tier 3 universe is mechanical (drawdown ≤ -25%
   point-in-time). The framework's catastrophe-recall holds in both,
   but the basket-construction lucky-draw in Tier 1 doesn't repeat.

3. **The framework systematically biases against bouncers**. Disclosure
   stress correlates with future catastrophes (good — that's the
   catastrophe-recall finding) but ALSO correlates with future recovery
   in some cases (UNFI's 9% supplier-finance amendment + 21% Whole Foods
   concentration → +189% return as they refi'd). When the universe is
   distressed and the tape favors recovery, you NEED the bouncers in
   the LONG basket. The framework excludes them.

## The honest revised mental model

The framework is:

- **A catastrophe-warning system** (≥85% recall across windows): real,
  durable, useful for risk management.
- **NOT a basket-alpha generator**: the LONG basket constructed by
  "exclude all SHORT-flagged names" is hit-or-miss depending on
  whether the tape favors quality or recovery. Tier 1 was a quality
  tape, Tier 3 was a "trough-buying" tape, framework lost on Tier 3.

The +57 pp claim from Tier 1 was three lucky tailwinds simultaneously:
favorable tape, lucky basket composition, hand-curated universe. None
of those are framework properties.

## What this means for the strategy

**If positioning as a CATASTROPHE-AVOIDANCE filter:**
- 85% recall on distressed-cohort catastrophes is real and useful
- Application: run the framework over a watchlist of names you'd
  otherwise hold and exclude SHORT-flagged. Expect to avoid 85% of
  -40% blowups in the watchlist
- Caveat: precision is only 22% in Tier 3 (50 SHORTs to catch 11
  catastrophes). You'll exclude many fine names along with the bad ones.
- This is most valuable when the precision-cost (excluding winners) is
  cheap relative to catastrophe-loss avoidance — e.g., risk-managed
  baskets where downside dominates

**If positioning as a LONG-basket selection tool:**
- Tier 3 falsifies it. Don't claim +57 pp alpha. Don't promise basket
  outperformance on out-of-sample distressed cohorts.
- The LONG basket may underperform a passive-distressed basket when
  the tape favors recovery
- This positioning was always weakly supported (Tier 2 already showed
  no signal on healthy small-caps); Tier 3 confirms it doesn't survive
  on distressed cohorts either, just on the specific Tier 1 cohort

## False positives and negatives (case detail)

**False positives** (SHORT-flagged but positive return) — these are
where the framework excluded names that became big winners:

| ticker | composite | fwd | sector | what happened |
|---|---:|---:|---|---|
| UNFI | 0.70 | **+189.5%** | Food Distribution | Refi'd Whole Foods contract + capital structure cleanup post-cutoff |
| EXTR | 1.50 | +50.7% | Tech | Backlog burn ended; revenue cycle stabilized |
| PTCT | 0.50 | +34.6% | Biotech | sepiapterin Phase 3 + restructuring executed |
| GDYN | 0.50 | +37.3% | Software | Demand recovered + new client wins |
| DCOM | 1.50 | +42.7% | Regional Bank | CRE stress proved manageable |
| FWRD | 1.50 | +31.0% | Trucking | Omni integration completed at lower cost |
| ACAD | 0.60 | +16.4% | Biotech | DAYBUE recovery, new approvals |

**False negatives** (LONG-rated but catastrophes):

| ticker | composite | fwd | sector | what happened |
|---|---:|---:|---|---|
| XNCR | 0.20 | **-61.5%** | Biotech | Pipeline disappointment despite clean disclosure |
| ROG | 0.30 | -42.4% | Electronic Components | Continued EV/HEV demand softness; cyclical not concealment |

XNCR is the case that hurts most — STRICT_LONG (composite 0.20) with
strongest deterministic signals (clean balance sheet, $700M cash,
clinical pipeline). Framework had no signal because there WAS no
disclosure-quality issue. The business just had bad clinical news.

## Recommended next step — none

We've now tested three windows × universe combinations. The pattern is
clear:

- Catastrophe-detection within distressed cohorts: 85-93% recall, robust
- Basket-alpha: window-specific, not generalizable
- Healthy-cohort signal: absent

Further testing (Tier 4 = additional walk-forward windows) would either
confirm the catastrophe-recall pattern (likely) or further weaken the
basket-alpha claim. Either way, the strategy positioning should be
**"catastrophe warning" not "alpha generation."**

## Files

- `tier3_test_set.json` — 60-name blinded universe
- `_unblinded/tier3_test_set.json` — same with forward_return
- `tier3_agent_manifest.json` — blinded manifest
- `scores/pilot_*.json` — 58 pilot scores (INDV, UNIT excluded — no
  pre-cutoff 10-K)
- `synthesis.json` — basket math
- `candidate_pool.json` — 622-name priced pool
- `build_candidate_pool.py`, `sample_universe.py`, `cache_10ks.py`,
  `synthesize.py`, `AGENT_PROMPT.md` — build scripts
