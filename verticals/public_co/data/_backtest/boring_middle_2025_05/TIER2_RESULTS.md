# Tier 2 — boring-middle out-of-sample backtest

Run 2026-05-25. Tests whether the +57 pp Tier 1 alpha survives on a
universe NOT selected for distress.

## Universe construction

- Start with SP600 enriched (602 names as of cutoff 2025-05-15)
- Exclude 66 Tier 1 backtest names
- Price 564 candidates via yfinance (2025-05-15 close + 2026-05-15 close)
- Filter to **drawdown -10% to -25%** at cutoff → 220 names
- Random sample of **50** (seeded 20260525), no sector stratification
- Cache 10-Ks (all pre-2025-05-15), score with blinded prompts

Universe baseline forward return: mean **+9.2%**, median +7.8%, IJR same
window +28.2%.

## Headline — alpha disappears on the boring middle

| metric | Tier 1 (distressed) | Tier 2 (boring middle) |
|---|---:|---:|
| Universe size           | 66 | 50 |
| Universe mean fwd ret   | +7.0% | +9.2% |
| LOOSE_LONG basket size  | 13 | 24 |
| LOOSE_LONG mean fwd ret | **+64.6%** | **+8.5%** |
| Alpha vs universe       | **+57.6 pp** | **-0.7 pp** |
| Alpha vs IJR            | +38.5 pp | -19.7 pp |
| Avoidance-alpha (skip SHORT) | +14.1 pp | -2.7 pp |
| Spearman ρ(composite, fwd ret) | **-0.599** | **-0.053** |
| Random-LONG placebo percentile | **99.91** | **45.2** |

**The framework's selection signal is statistically indistinguishable from
random on the boring middle.** Spearman correlation collapses to noise
(-0.053 vs -0.599); the LOOSE_LONG basket lands at the 45th percentile
of random draws (vs the 99.91 percentile in Tier 1).

The Pearson correlation actually flips slightly positive (+0.216) —
suggesting that within this universe, higher composite scores (worse
honesty grades) weakly co-occur with HIGHER returns. The SHORT basket
mean (+11.9%) is in fact higher than the LOOSE_LONG mean (+8.5%).

## Notable framework-shorts that were winners

| ticker | composite | tier | realized | finding (genuinely real) |
|---|---:|---|---:|---|
| MSGS | 1.500 | SHORT | **+78.7%** | Dolan dual-side related-party Knicks/Sphere media-rights cut + non-10b5-1 insider sales pre-TSA |
| ACMR | 1.100 | SHORT | **+161.7%** | BIS Entity List Dec-2024 hit, 99% China revenue exposure, Gartner -23.6% WFE forecast |
| PRIM | 1.100 | SHORT | **+50.6%** | CEO departure with $5.15M pre-departure sale, recurring percentage-of-completion catch-ups |
| CUBI | 1.500 | SHORT | **+32.9%** | Aug-2024 FRB Written Agreement (BSA/AML), CEO $11.3M post-enforcement selling |
| CATY | 1.500 | SHORT | **+28.8%** | NPLs +135% YoY, ACL coverage collapsed 222→99%, insider sales clustered to bad-news disclosures |
| SMP  | 0.600 | SHORT | +29.3% | $156M→$650M debt jump for Nissens, unquantified Mexico tariff exposure |
| MC   | 0.100 | STRICT_LONG | +8.6% | Clean — but UNDERPERFORMED the IJR by 20 pp despite "perfect" honesty score |

These are all real, well-documented forensic findings. The framework
genuinely detected what it's designed to detect. **The findings just
don't predict 1-year forward returns on healthy small-caps.**

## What this means for the honesty-alpha thesis

The reframing implied by Tier 2:

1. **Tier 1's +57 pp alpha appears to be a property of the distressed
   cohort, not of the framework.** The 66-name Tier 1 universe was
   curated as a distressed sample — 32 names known to be delisted plus
   34 control survivors. Within that universe, the framework's
   "exclude liars" filter worked because the liars in that distressed
   sample disproportionately catastrophized.

2. **On a representative SP600 sample, the framework adds no signal.**
   It still detects disclosure-quality differences (correctly!), but
   those differences don't manifest as 1-year forward return spreads.
   Lying boring-middle companies often muddle through. Honest
   boring-middle companies don't necessarily outperform.

3. **The framework is a "lying detector," not a return predictor.**
   This was the original explicit framing from the project memory
   ("Signal OS is a lying detector, not a fundamental analyst").
   Tier 2 confirms it stringently: the framework correctly identifies
   what it claims to identify — disclosure honesty — but that
   identification is necessary-not-sufficient for return prediction
   outside the distressed cohort where dishonesty correlates with
   catastrophic outcomes.

4. **The Tier 1 result is not invalid, but it is not generalizable.**
   A live LONG basket built on a deep-trough distressed cohort using
   this framework may indeed beat the basket-baseline (Tier 1 evidence
   is genuine: the placebo p=0.0009, det-screen gap +49 pp are robust).
   But you can't extrapolate to "honesty alpha works on small caps."
   It works on **distressed small caps**.

## What survives from Tier 1

The TIER 1 within-cohort findings still hold:

- Within a distressed cohort, the framework's LONG basket beats random
  (p=0.0009) and beats deterministic screens (+49 pp gap)
- The framework's catastrophe-detection (93% recall on -40% or worse)
  is real
- The framework correctly EXCLUDES liars whose lies actually crystallize

What does NOT survive:

- The claim that honesty-alpha is a general small-cap investing edge
- The implicit suggestion that the +57 pp generalizes outside the
  curated distressed cohort
- Any prospect of using the framework as a screen across the broader
  SP600 without first identifying a distressed cohort separately

## Forward implications

The honesty-alpha framework should be repositioned as:

- A **stress-conditional filter**: useful when constructing baskets
  from candidate pools that are *already* distressed (e.g., trough-
  buying small-caps with -40%+ drawdowns).
- A **negative selection tool**: identify catastrophes you should not
  hold, not winners you should hold. Avoidance-alpha within distressed
  cohorts is +14 pp (Tier 1).
- **Not** a universal small-cap screen.

The two key Tier 1 numbers (LOOSE_LONG +64.6%, alpha +57.6 pp) should
be quoted with the explicit qualifier "on a curated distressed cohort"
going forward.

## Methodology notes

- All 50 pilots were scored with the PATCHED, blinded prompt template
  (post-Tier-1 patch). Forward returns were not in the data files
  agents could read. Manifest verified by `verify_blinded.py`-equivalent.
- A 51st pilot (ABCB) was run as a "do credits work" test before the
  serial batches resumed; verified the limit reset before the 49-name
  run. Initial 50-agent parallel burst exhausted the session limit;
  no pilots were saved from that attempt.
- One agent (TRIP) noted a `going_concern_detector` cutoff-filter bug
  where `_latest_10k_or_10q` doesn't pre-filter by cutoff_date and
  fetched a post-cutoff 10-K; the agent correctly bypassed it manually.
  Worth fixing in m_sources/going_concern_detector.py before any
  future rerun.

## Files

- `tier2_test_set.json` — 50-name blinded universe (agent-facing)
- `_unblinded/tier2_test_set.json` — same with forward_return joined
- `tier2_agent_manifest.json` — blinded manifest
- `scores/pilot_*.json` — 50 pilot scores
- `synthesis.json` — basket math + per-name composites
- `candidate_pool.json` — 564-name priced SP600 pool
- `build_candidate_pool.py`, `sample_universe.py`, `cache_10ks.py`,
  `synthesize.py`, `AGENT_PROMPT.md` — build scripts
