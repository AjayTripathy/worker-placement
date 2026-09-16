# Tier 1 control tests — small-cap honesty backtest

Run on 2026-05-25 against the 64-name scored universe (cutoff 2025-05-15,
measurement 2026-05-15). Baseline: LOOSE_LONG basket (n=13) mean
+64.6%, alpha vs full survivorship-aware universe +57.6 pp.

## Test B — random-LONG placebo (10k draws of 13)

| metric | value |
|---|---|
| placebo mean | +9.3% |
| placebo p50  | +8.6% |
| placebo p95  | +37.5% |
| placebo p99  | +49.3% |
| placebo max  | +81.1% |
| framework mean | **+64.6%** |
| framework percentile | **99.91** |
| one-sided p | **0.0009** |
| z-score | **+3.36** |

Framework basket is at the 99.91 percentile of random 13-name baskets
drawn from the same 64 scored names. Strong evidence that the LLM is
doing real picking work within the universe; the +64.6% is not just a
basket-size effect on a fat-upside-tail universe.

→ Run script: `tier1_test_B_placebo.py`  · output: `tier1_test_B_results.json`

## Test A — deterministic-screen ablation

Built a deterministic LONG screen from cached EDGAR data:
- `going_concern_signal == NO_GOING_CONCERN` (m_sources/going_concern_detector)
- `auditor_signal == CLEAN_BIG4_TENURE` (continuous Big-4 — implies no Item 4.01 8-K change)
- 10-K covenant-stress regex hits ≤ 3 (proxy for covenant amendment / forbearance / debt-mod)
- 10-K dividend-cut regex hits ≤ 0

Baseline screen produced n=13 (coincidentally same size as framework),
mean **+15.4%**. Overlap with framework LOOSE_LONG = 2 of 13 (ICHR,
IOSP — those two returned +126.7% mean).

| basket | n | mean | median |
|---|---|---|---|
| Framework LOOSE_LONG | 13 | +64.6% | +77.5% |
| Deterministic LONG   | 13 | +15.4% | -9.8%  |
| - agreement (both)   | 2  | +126.7%| +126.7%|
| - det-only           | 11 | -4.9%  | -24.4% |
| - framework-only     | 11 | +53.3% | +77.5% |

Marginal LLM lift (framework-only minus det-only) = **+58.2 pp**.

### Sensitivity sweep

Tried 10 plausible variants of the deterministic screen (Tier-2 auditor
yes/no × covenant-threshold ∈ {3, 5, 10, 20, none}). Deterministic
basket mean ranged from +17.5% to +22.5% — never within 40 pp of the
framework. **The +45-49 pp gap is robust to threshold choice.**

The deterministic screen's 11 "det-only" picks (rejected by framework)
include several names the framework correctly SHORTed:
JACK -59.9%, MGPI -46.2%, WOLF -100%, XRX -49.2%, AZTA -24.4%,
BDN -29.4%. These pass GC+Big-4+covenant text checks but had business-
quality issues the LLM picked up.

→ Run scripts: `tier1_test_A_ablation.py`, `tier1_test_A_sensitivity.py`
   outputs: `tier1_test_A_results.json`, `tier1_test_A_sensitivity.json`

### Limitations

- Dividend-cut regex is weak (rarely fires in 10-K narrative; the
  signal lives mostly in 8-K / press release).
- Covenant-amendment regex picks up routine credit-facility discussion
  (e.g. ANDE had 10 hits with no actual stress); the threshold sweep
  controls for this but the signal isn't crisp.
- 8-K Item 4.01 auditor-change is approximated via `auditor_signal`
  (FREQUENT_TURNOVER / UPGRADE_OR_LATERAL bucketing), not via direct
  8-K parsing.

## Test C — blinding-leak audit

### The leak

The agent prompt directs agents at `combined_test_set.json`, which
contains `forward_return` and `price_2026_05_15` (post-cutoff data)
alongside `price_2025_05_15`. **The agents could see the answer.**

The prompt does say "Do NOT use prior knowledge of what happened
after 2025-05-15" — but it then provides the data via the file the
agent is told to read.

### Narrative contamination

| pattern | hits/66 |
|---|---|
| Summary explicitly quotes the forward return % | **31 (47%)** |
| Hindsight-language ("materialized", "known limitation", "turned out") | 2 (3%) |
| References to post-cutoff event timing | 2 (3%) |
| Any-pattern (union) | **34 (52%)** |

Examples (verbatim from summaries):
- ASIX: *"Modest -8% forward return is consistent with drift-down..."*
- AHRT: *"Forward -3.5% return (relatively benign) is consistent with NEUTRAL..."*
- AVNS: *"Given... the realized +93% forward return, AVNS is a known limitation of the framework"*
- ANGI: *"...-66% forward return..."*

Roughly half of all pilot summaries leak post-cutoff knowledge in
their narrative. This is a major methodology failure.

### But — severities appear blinded

The critical question: were the severity assignments (which drive
the composite and basket math) also contaminated?

Stratifying the universe by leak-vs-clean narrative:

| group | n | Spearman ρ(composite, fwd return) | LONG basket mean |
|---|---|---|---|
| All 64 scored        | 64 | -0.599 | +64.6% (n=13) |
| Leakers              | 19 | -0.500 | +39.2% (n=5)  |
| Non-leakers (clean)  | 45 | -0.671 | +80.5% (n=8)  |

If the leak had corrupted severities, leakers should show stronger
correlation between composite and forward return (cleaner alignment
with the known answer). The opposite is true: non-leakers have
**stronger** predictive correlation (-0.671 vs -0.500) and a higher
LONG basket return (+80.5% vs +39.2%).

Additional evidence severities were not back-engineered:
- AVNS scored SHORT (composite 1.7) despite +93% realized return —
  agent acknowledged this as a "known limitation" rather than rigging
  to PASS.
- FTRE scored SHORT (composite 0.8) despite +178.3% realized return.
- ELME scored LOOSE_LONG (composite 0.222) despite -87.4% return.

If agents were rigging severities, these high-profile mismatches
wouldn't exist.

### Test C verdict

There IS a significant blinding leak in the **narrative summaries**
(47% of pilots quote the realized return verbatim), but the leak does
**not** appear to have systematically contaminated the **severity
assignments** that drive basket selection. Headline numbers are
probably not severity-rigged — but the methodology has a hole that
must be patched for any future re-run: strip `forward_return` and
`price_2026_05_15` from the data files exposed to agents.

## Bottom line — Tier 1 sandbagging the headline?

Going into Tier 1, the open question (from RESUME_NEXT.md) was whether
the +57.6 pp alpha is 20-40 pp inflated by selection / blinding / single-
window effects. Tier 1 evidence:

| concern | Tier 1 evidence | residual risk |
|---|---|---|
| Random-pick artifact | Rejected: p=0.0009, z=+3.36 | low |
| Deterministic screen captures most alpha | Rejected: +49 pp robust gap | low |
| Severity contamination from forward-return leak | Probably not — non-leakers stronger | medium |
| Narrative contamination | Confirmed at 47% rate | n/a (cosmetic for basket math) |
| Universe-shape artifact (distressed-cohort fat tails) | Not addressed in Tier 1 | medium-high |
| Single-window 2025-2026 dependence | Not addressed in Tier 1 | high |

Tier 1 does NOT fully validate the headline. It does refute the two
simplest deflation hypotheses (random pick / deterministic screen).
The remaining concerns are universe-shape and walk-forward stability,
which need Tier 2 + Tier 3.

## Next steps

- **Strip leakage from prompt template** before any rerun: pass agents
  only `ticker`, `cik`, `group`, `drawdown_2025_05_15`, NOT
  `forward_return` or `price_2026_05_15`.
- **Tier 2** — boring-middle out-of-sample: pull 60 names from the
  same date range that are neither delisted nor catastrophes nor
  control_survivors (the index middle); score them; check basket
  alpha is real on names that don't share the distressed-cohort
  selection.
- **Tier 3** — walk-forward across 2-3 earlier 12-month windows
  (e.g. 2024-05 → 2025-05, 2023-05 → 2024-05). If alpha persists
  across windows it's much less likely to be artifact of the specific
  2025-2026 market.
