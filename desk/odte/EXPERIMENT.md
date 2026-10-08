# 0DTE research: claims, controls, and evidence gaps

Design reviewed 2026-10-07. No measured investment edge has been established.
These are prospective paper experiments on the first eligible XSP T3 condor.
Passing software tests establishes implementation behavior, not profitability.

## What the original trial tests

T1 is mechanical; T2 adds opening-range/VIX gates and calendar blackouts; T3
uses calendar blackouts. Actual T2 can enter later at different strikes, so its
unmatched return is not a clean estimate of a regime filter's contribution.

The independent arm trial takes the first T3 candidate and evaluates all 16
subsets of news, IV/realized-vol ratio, path efficiency and spread/credit filters,
plus CASH. Every arm has the same candidate, entry time, legs and exit policy.
It evaluates conjunctions of fixed gates, not a model of joint causal effects.
FOMC/CPI/NFP/half-day blackouts create no T3 candidate and hence no arm trial.

The selector is a **full-information experts simulation**, not a bandit. All
available hypothetical outcomes are observed, whether or not the selector chose
that arm. Sampling does not generate new learning information in this setting.
Seventeen arms on one date are one correlated session, not 17 independent tests.

## Hypothesis coverage

| Hypothesis | Implemented measurement | Remaining gap / disconfirmation |
|---|---|---|
| Text adds information beyond numbers/calendar | `edge_trial`: same model/prompt/common information cutoff, with versus without supplied text; prior-only numerical probabilities; stop/severe Brier scores | A positive text comparison must survive fresh validation and costs. One draw per condition cannot distinguish particular reasoning mechanisms from model variability. No comprehensive event corpus or verified resolved model identity is guaranteed. |
| Selective risk bearing pays enough | Gross return / entry maximum-risk forecast, deterministic net-EV gate, matched net paper returns, CASH/T3 and equal-participation controls | This forecasts a future selection policy. Exact-strike expected close-out cost, return distributions/quantiles, capital opportunity cost and rare tails still need separate prospective tests. Calm is not synonymous with underpriced risk. |
| Small size and patience create an advantage | Deliberate abstention and equal-participation comparison | No depth/size/queue/latency observations or capacity curve. Fixed one-contract touch marks cannot establish this edge. |
| Execution and behavioral discipline add value | Existing recovery, risk caps, idempotency and fee-reconciliation tests; costs and failures recorded in research | No controlled comparison of operator behavior and no implementation-shortfall study linking decision quotes to actual fills. Do not create reckless trades to manufacture a retail comparator. |
| Cheaper research improves decisions | Immutable attempts, fixed hypotheses, measured token usage/wall time when available, failed calls counted, later validation phase | Model dollars are unknown unless measured. No measured total engineering/research cost, all-hypothesis organization-wide registry or replicated improvement per research dollar yet. |
| We beat institutions or retail | None | Participant labels are not benchmarks. Requires comparable net returns, capital, risks and execution data. Positive paper P&L does not identify whose losses we capture. |

## Matched-input side trial

`edge_trial.py` is additive: it reads original frozen source inputs and arm
artifacts but cannot change their manifests, thresholds, decisions or runner.

After the existing morning forecast completes, it checks the original job and
corpus digests against that forecast. The original probabilities/reasons are
never passed to the new model calls. Both LLM conditions receive identical
market snapshot, features, indicative candidate, structured calendar and cutoff.
Only the evidence excerpts differ. Calls are fresh, their order is deterministically
counterbalanced by date, and the provider/model/reasoning settings are identical.
The corpus is reused: it is not fetched again at a later time.

The numerical control sees features from that same premarket snapshot, with
missingness indicators and declared calendar flags. It uses the original
regularized logistic algorithm, restricted to this trial's prior resolved
sessions known by the common input cutoff. Before 20 training sessions it uses
smoothed base rates. Expected return is the prior observed mean shrunk toward
zero with 20 observations of prior strength. This is an intentionally modest
baseline, not a competitive institutional pricing model.

All three conditions forecast:

- Stop before the 15:45 exit while the hypothetical position is still open.
- Realized gross loss at least half the actual candidate's entry maximum loss.
- Expected realized gross P&L divided by that candidate's entry maximum loss.

At entry the frozen policy multiplies the return forecast by the observed
candidate's risk, subtracts $7.20 assumed trading cost and $1 research cost
for an LLM condition, and requires at least $1 expected net profit. Stop and
severe probabilities must also be below .30 and .10. The numeric condition
has no model-call charge. This mapping is fixed before the session and can be
recomputed from the sealed forecast and source entry without using an outcome.
No side-trial decision is sent to the live rail.

These are experimental choices, including the $1 material-improvement threshold.
They are not optimized thresholds, calibrated cost estimates, or advice to trade.
The final candidate is unknown premarket; the return ratio is a policy forecast,
not a claim that yesterday's options are executable today.

The run and each model attempt are reserved before inference. A crash does not
authorize another answer. Failed and late responses remain visible. Model calls
must finish strictly before 09:15 Eastern. A missed session stays missing.
Fresh registrations are required after changes to any frozen dependency.

## Evaluation protocol

Primary comparison: text minus no-text daily net P&L on the same resolved dates.
Secondary comparisons: text minus numerical control, and text minus T3. A
uniform k-of-n control measures whether selection beats merely trading less.
Skipped trades are still Brier-scored when the underlying path is observed.
Return forecasts receive squared-error and bias diagnostics by submitter,
agent, provider, intelligence level, requested/resolved model, protocol and phase.

The first 60 source decision sessions after registration are discovery. The
next 60 are prospective validation of the same fixed policies. Missing forecasts
or outcomes do not extend either window. Later sessions are labeled extension.
Online numeric learning may use earlier resolved validation sessions: this tests
a frozen adaptive policy, not a frozen fitted model. Choosing a new winning arm,
threshold or feature set requires a separate future validation registration.

Reports use moving blocks of five ordered paired sessions with 4,000 deterministic
bootstrap draws. They withhold intervals below 20 paired sessions. The primary
comparison has its own approximate 95% interval; two secondary comparisons use
Bonferroni-adjusted percentile levels. Existing-arm comparisons versus T3 use a
16-comparison family. These approximate intervals can be unreliable under
nonstationarity, informative missingness and unobserved tails. Paired gaps mean
blocks are consecutive available observations, not necessarily consecutive days.
Repeated inspection is descriptive, not an alpha-spending or sequential-stopping
test. Sixty sessions is a review checkpoint, not a power calculation or proof.

Known trading P&L less **all** attempted-model costs is a separately labeled
subtotal, not a full deployed-policy return. A failed forecast is unavailable,
not a profitable cash decision. Unknown trade paths are never imputed into the
point estimate. Existing-arm reports show stress scenarios that assign unresolved
takes either entry max-risk loss or full entry credit; these are sensitivity
scenarios, not execution bounds. Fees and early close prices can violate them.
Cost sensitivity uses $7.20/$12/$20 per trade, holding frozen decisions fixed.

## Evidence still needed before any capital decision

1. Validate pricing forecasts on actual candidate quotes before a new entry;
   use prospective expected close-out cost/distribution targets, not just risk
   classification or retrospective quote selection.
2. Observe more event types using primary, timestamped auction, Fed-speaker,
   earnings and rebalance schedules; direct positioning data if claiming a
   positioning feature. RSS silence is not evidence that an event is absent.
3. Record quote sizes/depth, quote-to-decision latency and higher-frequency stop
   paths. Validate simulated fills against independently authorized execution
   observations, including missed/partial fills, fees and adverse selection.
4. Accumulate meaningful fresh validation and stress regimes. Calculate sample
   needs from observed session variability and a declared minimum useful effect;
   do not stop on the best of sixteen arms or on an attractive early interval.
5. Measure research costs and execution/behavior benefits against honest
   alternatives. Do not claim an institutional or retail advantage from these
   paper arms alone.
