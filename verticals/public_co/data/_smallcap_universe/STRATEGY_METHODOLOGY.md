# Small-Cap "Honesty Alpha" Strategy — Methodology

_Last updated 2026-05-24 after the 5-name R/f/M pilot and the SRPT calibration discussion._

## Core thesis

The Signal OS framework's claim-verification engine generates alpha through **information asymmetry detection** — the gap between what management discloses (or implies) and what's externally verifiable. We call this **"honesty alpha"**:

> Long the names that aren't lying. Short / avoid the names that are.

The framework is fundamentally a **lying detector / negative-selection filter**. It is NOT a fundamental analyst.

## What counts as "lying" (where the framework finds alpha)

| Pattern | Example from pilots |
|---|---|
| Disclosed-but-misleading claim | INSP 10-K "code will transition to 64582" vs Q1 10-Q "AHA recommended 64999 (unlisted)" |
| Disclosed-but-hidden distress | SHAK "Fifth Amendment AND Waiver" in exhibit index, no MD&A narrative |
| Disclosed-but-not-framed-as-distress | FMC 5 covenant amendments + $750M 8.45% subordinated notes framed as routine refinancing |
| Disclosed-but-overstated growth | UPWK CEO 10b5-1 rotation pre-committing more selling while marketing AI growth |
| Cohort-attributed claims not in filing | BAH-style NOT_IN_FILING reclassification |
| Insider behavior + program exposure + event-content link | IONQ canonical: Chapman sold $37.5M day House passed FY25 approps confirming AFRL earmark gone |

## What does NOT count as "lying" (no framework alpha)

| Pattern | Example |
|---|---|
| Honestly disclosed catastrophic events | SRPT's 10-K openly discloses 3 patient deaths, FDA black-box warning, indication removal, EU rejection, ESSENCE trial failure |
| Standard financial metrics | EPS, margins, ratios — already in every analyst model |
| Standard quality factors | ROE, debt/EBITDA, free cash flow conversion |

**Rule**: if the information is in the issuer's filing AND framed accurately, the market has already priced it. Re-detecting it produces a true positive on disclosure quality but no actionable trading edge.

## The framework's role in the strategy

```
Universe (S&P 600 SmallCap, 339 names)
    ↓
Step 1: FRAMEWORK = LYING DETECTOR  ← This is where honesty alpha lives
    Composite threshold: ≤ 0.30 admits "not lying" (SRPT-style honest-but-impaired pass through)
    Composite > 0.30 = excluded from LONG universe
    ↓
Surviving universe = "not lying" small caps (~200-250 expected)
    ↓
Step 2: PORTFOLIO CONSTRUCTION  ← Two test paths, NOT framework alpha
    Path A: Equal-weight index of all survivors
    Path B: Apply quality / value factors, pick top 10-20
```

## The two strategy variants we'll test

### Strategy A — "Clean Index" (pure honesty alpha)

- **Hold**: equal-weight all survivors of the honesty filter (composite ≤ 0.30)
- **Rebalance**: quarterly (re-run framework, drop names that crossed the threshold, add new ones)
- **Expected count**: ~200-250 names
- **Benchmark**: IWM (Russell 2000 ETF)
- **Alpha hypothesis**: removing the worst-tail (liars, hidden distress) gives a positive return over IWM with similar or lower volatility — the "fraud-avoidance premium"
- **Reason to prefer**: cleanest attribution of the framework's alpha — no factor noise

### Strategy B — "Honesty + Quality" (filter then select)

- **Filter**: framework survivors (composite ≤ 0.30) — same as Strategy A
- **Select**: apply traditional factors to the ~200-250 survivors:
  - Quality: ROE > 15%, FCF positive, low leverage
  - Value: P/E < median, EV/EBITDA < median
  - Momentum: 6-month return > 0 OR trough-recovery setup
  - Capital return: buyback velocity, dividend hike at trough
- **Hold**: top 15-25 by combined factor score
- **Rebalance**: quarterly
- **Alpha hypothesis**: honesty filter + factor selection > each alone
- **Reason for caution**: mixes alpha sources; harder to attribute returns to the framework specifically

## The test protocol

Both strategies will be backtested with the same methodology:
- Hold-out window: forward 6 / 12 / 24 months from each pilot rebalance date
- Benchmark: IWM with same start date
- Risk-adjusted return: Sharpe, Sortino, max drawdown
- Attribution: decompose alpha into (sector tilt) + (size tilt) + (residual = framework alpha)

If Strategy A's residual alpha is statistically significant, the honesty-alpha hypothesis is confirmed.
If Strategy B's residual alpha is similar to A's, factor overlay adds no edge → use A.
If Strategy B beats A materially, factor overlay adds edge → use B but track attribution.

## Key calibration notes from pilots

### From the 5-name + SRPT pilot (2026-05-24)

- 4 of 5 deep-trough names were correctly REJECTED by the framework as lying / obscuring distress (FMC, INSP, UPWK, SHAK)
- SRPT passed the filter (composite 0.125) despite being a fundamentally impaired business — this is the CORRECT framework output (SRPT isn't lying), but illustrates why filter ≠ buy signal
- SPSC was the only filter survivor that also has clean quality signals (100Q growth, $200M buyback at trough)

### Composite threshold guidance

- **≤ 0.143** (strict, defense-cohort default): admits only the cleanest names; rejects SPSC (0.286) and SRPT (0.125 — wait, 0.125 IS ≤ 0.143)
- **≤ 0.20** (standard): admits SPSC and SRPT; rejects everything ≥ 0.25
- **≤ 0.30** (small-cap loose, recommended): admits all "not lying" names including borderline NEUTRALs like SPSC

For Strategy A (index), use **≤ 0.30** to maximize survivor count and rely on diversification.
For Strategy B (factor selection), use **≤ 0.30** at filter step, then let factors do the concentration.

## Framework upgrades that DO add alpha (queued but unbuilt)

These extend the lying-detection surface area without becoming fundamental analyst:

1. **`auditor_change_tracker`** ✅ built — catches Big 4 resignations + affirmative disagreements
2. **`going_concern_detector`** ✅ built — catches substantial-doubt language
3. **`distress_pattern_detector`** — pattern composite of {covenant amendments, subordinated debt pricing, buyback bans, dividend cuts, write-down sequences} that catches FMC-style distress even when GC + auditor are clean. ALPHA: management is OBSCURING distress through framing.
4. **`buyback_velocity_tracker`** — detects buyback DECELERATION into trough (UPWK) vs ACCELERATION at trough (SPSC). The deceleration signal is the alpha — management is REVEALING low conviction by slowing buyback at lows while marketing continued confidence in narrative.
5. **`claim_evolution_drift_detector`** — already exists; force-run on every pilot name to catch INSP-style "10-K narrative drifted in next 10-Q" patterns.
6. **`latest_filing_not_just_10K`** — workflow rule to ALWAYS pull most-recent 10-Q + 8-K within cutoff, not just annual 10-K.

These all stay within the "what is management lying about / obscuring" frame. None of them re-detect honestly disclosed facts.

## Framework upgrades that DO NOT add alpha (rejected)

1. ❌ `disclosed_distress_event_counter` — would count honestly disclosed events (patient deaths, FDA actions, trial failures, etc.) and bump composite. This is fundamental analyst territory; market already prices it.
2. ❌ `business_quality_score` — would compute ROE, margins, growth rates. These are standard factors; we'd just be reinventing the quality factor.
3. ❌ `valuation_score` — same critique; standard value factor.

If we want these features, they go in Strategy B's factor selection step, NOT in the framework's composite.

## Open questions for next iteration

1. Should the strict-threshold for SHORT remain at composite ≥ 0.50, or tighten to ≥ 0.40? The current 0.50 missed UPWK (0.625) as a clean short — wait, that's the wrong direction. UPWK was caught at ≥ 0.50 ✓.
2. Should sectors be normalized? Healthcare names hit GC at 8.2% rate vs Industrials at 0%. Sector-normalized composite might be more comparable across the universe.
3. Should the validators (program_exposure_required + event_content_relevance) apply UNIVERSALLY in addition to insider signal? The IONQ pattern requires both; smaller-scale lying detection may not need event-content link.
