# 0DTE research module

**Start here:** [run only this module](../../ODTE.md) for setup, offline tests,
paper capture, morning forecasts and post-close reports without the web app.
This directory is `desk.odte`; it is runnable from the repository checkout,
not yet a standalone pip distribution.

For a future LLM picking up the work, read [AGENT_HANDOFF.md](AGENT_HANDOFF.md)
for the dependency map, private artifact locations, failure handling and
sharing boundary. [AGENTS.md](AGENTS.md) carries the local working instructions.
Check actual manifests and preflight results rather than assuming this README
describes the currently running process. Read the invariants below before
changing capture, accounting, or execution.

For research design, coverage gaps and the matched text/no-text trial, start with
[EXPERIMENT.md](EXPERIMENT.md). For another agent's operational entry point,
module boundaries and sharing checklist, see [AGENT_HANDOFF.md](AGENT_HANDOFF.md).
The additive evaluation runs with `python -m desk.odte.edge_trial`; it does not
change the original frozen arms or place orders.

## Execution and grading invariants

The live runner must be launched explicitly by the principal. Unit tests do not
connect to a Gateway or submit orders. Run the regression suite with:

```sh
python -m pytest --offline -q tests/test_odte.py tests/test_odte_execution.py tests/test_odte_data_quality.py tests/test_odte_fixes.py tests/test_odte_text_overlay.py tests/test_odte_arms.py tests/test_odte_research_health.py tests/test_odte_edge_trial.py
```

Use the same interpreter for validation and the runner. Python 3.12 is the
tested collector runtime; the supported research setup requires Python >=3.11
on macOS/Linux. Follow [ODTE.md](../../ODTE.md) to create `.venv/odte` independently
of the office app's environment. Older-interpreter compatibility tests do not
change the supported Python range.

## Order recovery

The daemon holds an OS file lock. Each submission gets a unique order reference
and an atomic, fsynced checkpoint containing its intent, account-independent leg
identifiers, action, quantity, and order ID **before** the broker call. A failed
checkpoint prevents submission.

Each checkpoint also contains its intended ledger row. The runner saves state
and this row together before upserting the ledger. Startup replays a missing or
outdated row, even for a completed session that otherwise needs no broker work.
It also repairs older terminal checkpoints whose ledger row is missing or still
`pending_execution`. Replays use the same session key and do not duplicate P&L.

`OPENING` and `CLOSING` remain pending until broker reconciliation establishes
what happened. A cancellation request is not cancellation confirmation. The rail
waits for a terminal response, rereads fills, and replaces only the unfilled
quantity. An unresolved cancellation prevents replacement.

On startup, reconnect, and each live tick, the runner checks account-scoped open
and completed orders, executions, and positions. A new connection always gets a
new session and subscriptions. Balanced executions must agree with broker leg
positions before another action. Unknown orders, unbalanced positions, missing
execution details, or legacy position state without order intents require
reconciliation; the runner records the reason and blocks new submissions.

An intent with no broker acknowledgement remains pending. Absence from a broker
response does not prove an order was never submitted. Resolve these cases using
broker records rather than deleting the checkpoint to force a retry.

IBKR's [order status documentation](https://interactivebrokers.github.io/tws-api/order_submission.html)
describes `PendingCancel` and the need to monitor execution callbacks as well as
order-status callbacks.

## Market data

Live entry requires fresh XSP, SPX and VIX1D last-price ticks (maximum price-tick
age 90 seconds; size or greek updates do not refresh that age). Option legs are
different: IBKR only sends a tick when a quote changes, so an unchanged wing is
still a quote. A leg is live-eligible while the CHAIN is alive (any option price
tick within 120 seconds) and the leg itself has quoted within 30 minutes; a
silent chain nulls every quote. Every selected feed must report IBKR market-data
type 1. Previous closes never substitute for current indices.
The live opening-range/VIX baseline is kept separately from shadow observations
so delayed data cannot seed a live risk gate. Shadow capture retains feed labels.

See IBKR's [market-data types](https://interactivebrokers.github.io/tws-api/market_data_type.html).

## Accounting

The live ledger contains one upserted row per template and date. Repeated
reconciliation and later commission reports update that row without adding a
second realized result. Executions are deduplicated by execution ID. When both
leg and BAG records exist, the leg records supply quantity, price and fees so the
synthetic BAG does not double-count them.

`gross_pnl_usd` records execution-price P&L. `pnl_usd` is net of reported USD
commissions, and stays null while fees are missing. Genuine zero fees require an
actual commission report. Only an unresolved POSITION (`pending_execution`: an
order intent with no reconciled outcome) blocks new entries. A closed trade
awaiting its fee report (`pending_fees`) or an expired one awaiting the statement
(`pending_statement`) does not lock the rail; the loss caps count gross minus
reported commissions and a $3 reserve while fee reports remain missing. Legacy
gross-only rows are marked `pending_legacy`.

Cash settlement is never inferred from the last captured index price. A condor
that reaches the bell leaves the account overnight (XSP settles in cash to the
closing index value). Once the contracts are gone and the session is past the
16:15 ET cutoff, reconciliation books it `EXPIRED_SETTLED` off the broker's
official daily close (`reqHistoricalData`, 1-day bar) and marks the row
`pending_statement` until the statement confirms it. If the official close is
not yet available the position stays `pending_execution` (blocking) and is
retried on every reconcile. A flat position is NOT settlement when any execution
on our legs did not come from our orders (a manual close in TWS): that session
stays `pending_execution` for hand reconciliation. This includes BAG executions
identified through their constituent legs or matching broker order. An XSP BAG
with unavailable leg identifiers is also held for reconciliation. External
execution evidence is saved in the checkpoint; an empty later broker response
cannot erase it. Older checkpoints carrying only an external-execution error
retain that block as well. Clearing it requires reconciling the actual executions
and fees against broker records; absence of positions or fills is insufficient.
The command for that is offline and audited:

```sh
python3 -m desk.odte.runner --resolve 2026-10-08 --exit-cost 1.50 --fees 3.25 \
    --note "stmt 2026-10-08: bought back 672P by hand 14:12"   # add --credit if no entry fill was ever reconciled
```

It books the session CLOSED / MANUAL_CLOSE from the statement's exit cost and
fees (net, `complete`), clears the external-execution evidence and the error,
keeps both inside `manual_resolution` with who/when/why, and refuses a clean
session or an empty note.

An execution is OURS when its order reference, permanent id, or order id matches
a durable intent — a combo leg report can arrive with an empty reference, and
the ids the checkpoint already holds must not let our own fills read as external.

The startup sweep runs every
prior session that still needs work through the same state machine as the live
session — expiry, completed round trips, terminal zero-fill cancels (-> NO_FILL)
and closed trades whose commission reports were missing — and sessions still
unresolved are retried every five minutes during the day. Before any order
exists the broker is polled every five minutes for observation; the submission
path always takes a fresh read immediately before the order, then checks risk
again using the updated ledger and envelope. Fee-report retries remain scheduled
but do not themselves veto an entry; unresolved exposure and loss caps do.

IB Gateway's [execution query](https://interactivebrokers.github.io/tws-api/executions_commissions.html)
only exposes executions since midnight. TWS can expose older executions when its
Trade Log is configured for them. A fresh Gateway connection therefore cannot be
assumed to retrieve yesterday's missing fees or manual-close executions. Cached
executions in the durable checkpoint remain usable; missing fee reports stay
pending with the reserve until reconciled from an available source. The overnight
tests use a fresh connection with empty local caches and the midnight cutoff.
Tests requiring a wider TWS history or a completed-order reply declare it explicitly.

## Research comparison

Observed, deliberate blackout/regime abstentions carry `skip_kind=strategy_cash`.
The paired benchmark includes these as zero-return days on the common calendar.
Missing input data and unclassified legacy skips remain excluded. A missing-chain
opportunity cannot later be relabeled as a successful regime abstention.
Graduation's observation count uses the paired calendar, and its t statistic uses
sample standard deviation. Live scoreboard P&L is net; shadow touch fills remain
a gross simulation, not a forecast of after-fee performance.

## Prospective LLM forecast experiment

`text_overlay` is a separate, opt-in, paper-only experiment. Its observer runs
after ordinary broker management, records local data, and cannot place orders.
The forecast worker uses the existing intelligence interface. Local offices
default to signed-in Codex; hosted offices use their configured API provider.
Provider, requested model, reasoning level, prompt, rules, costs, code hash and
submitter are sealed in the manifest before the first observation.

For a one-session premarket experiment, replace `YYYY-MM-DD` with a future
Eastern session date and register before the session:

```sh
python -m desk.odte.forecast_worker --init --premarket --session-date YYYY-MM-DD --office ~/office --submitter local-office
```

At 08:45–09:00 Eastern on that date, run these in order:

```sh
python -m desk.odte.forecast_worker --prepare
python -m desk.odte.forecast_worker --once
```

Preparation freezes only already-captured prior-session context, explicitly
dated and at most four calendar days old. Missing prior data stays a coverage
gap. It does not connect to the broker or pretend yesterday's options are
today's tradable quotes. The forecast must finish strictly before 09:15 ET.
The normal shadow collector must be running from the open through the exit;
restart an already-authorized shadow collector to load a changed observer.
Keep this local machine and its Gateway available throughout the session.

Without `--premarket`, the protocol instead uses the first 09:50–09:55 snapshot
and a strict 10:00 forecast deadline. Omitting `--session-date` allows subsequent
sessions under the same frozen protocol. The independent worker's `--daemon`
polls queued requests; it does not prepare premarket requests or start a broker.
Scheduling must explicitly choose the preparation and post-close review times.

The forecast concerns the **first eligible T3 condor at 10:00–10:20**, selected
with the existing delta, width and touch-price rules. Its final strikes and credit
cannot be known premarket. At entry, the observer links the actual shadow
candidate to the forecast. The text overlay takes exactly that candidate only
when stop probability is below 0.30 and severe-loss probability is below 0.10.
It retains the counterfactual outcome when it deliberately skips. Missing,
failed or late forecasts are unavailable, never successful cash decisions.

There are two distinct binary targets: a stop before 15:45 while still open,
and realized gross loss at least 50% of the entry maximum loss under the frozen
exit rules. Quotes are minute-sampled, so this cannot establish every intraminute
touch. A gap exceeding 90 seconds or missing live leg quotes leaves the trade
outcome unresolved. Expiry proxies never resolve these labels.

Public feed excerpts are timestamped and digested; quoted support must occur
verbatim in the frozen evidence. This verifies quotation, not the truth of an
article or the model's causal interpretation. The worker tags each cited reason
by event type, novelty, timing, transmission channel and expected volatility,
and records a falsifier. RSS coverage and the supplied calendar are incomplete;
auction, rebalance, earnings and dealer-positioning coverage is not implied by
an empty calendar. A source needs a declared public class; the observer never
ingests household or position documents. No automatic corpus publication occurs.

Market inputs include opening range, VIX1D level/change, credit and spreads;
ATM IV, 25-delta skew and smile curvature; straddle-implied move; quote coverage,
age and relative spread; trailing return, realized volatility and path
efficiency; IV/realized-vol ratio; and distances to the short strikes. Missing
features remain null in the research ledger and have explicit missingness
indicators in the numerical control. Dealer gamma is not inferred from prices.

Every observation retains its raw snapshot, candidate, timestamps and a hash
link to the previous observation. The feature catalog and units live in
`volatility.CATALOG`. The first observation within the 10:00 minute anchors
15- and 60-minute outcomes: forward realized volatility, IV change, VIX1D change
and spread change. Real capture seconds and jitter are supported. Incomplete
paths remain unresolved. The report shows feature correlations and text-tag
group means with session counts; these are exploratory associations with
confounding and multiple comparisons, not causal effects or feature selection.

After the close:

```sh
python -m desk.odte.forecast_worker --report
```

The report includes T3, T2's rule at the same entry, a numerical control, actual
T1/T2 entries where available, and a uniform equal-participation control. The
numerical learner uses only earlier, already-resolved sessions from this
protocol; before 20, it explicitly reports smoothed base-rate warmup. It sees
entry-time data, whereas the LLM sees the earlier snapshot. Brier scores include
every accepted resolved forecast, including deliberate skips, grouped by
submitter, agent, provider, intelligence level, requested/resolved model and
protocol. No reliability estimate gates the pilot.

Research comparisons assume $0.65 per leg for eight legs, $2 additional roundtrip
slippage, and $1 per research attempt. These are frozen assumptions, not broker
fees or measured model charges. Usage counts are retained when the provider
returns them. Paired results exclude unavailable forecasts and unresolved paths;
coverage, failed stages, incomplete attempts and total assumed research cost are
reported separately. A process crash reserves the attempt permanently rather
than selecting a second answer. The one-session run is an operational test;
60 paired sessions only trigger review and never enable live promotion.

Private files live in ignored `desk/data/odte/text_overlay/`: `manifest.json`,
`jobs/`, `attempts/`, `corpora/`, `forecasts/`, `sessions/`, `observations/` and
`volatility_outcomes/`. A protocol or code change fails closed. Archive the whole
directory and preregister a new one before resuming; never overwrite a manifest
or pool another protocol's history into this trial. Raw model output and exact
citation support stay in the forecast record; provider exception diagnostics
are excluded to avoid leaking credentials.

### Separate combinations and a paper selector

`desk.odte.arms` freezes a factorial directory, independent of the original
text-overlay registration. T3 is the calendar baseline. T4 is news only;
T5/T6/T7 add the volatility, trend and execution filters individually.
T8–T18 cover the remaining combinations. CASH is an always-cash control.
Every non-cash arm either takes or skips the **same first eligible T3 entry**:
same timestamp, strikes, quotes, contract count, stop and time exit. T1/T2
remain unchanged. This tests filters without confounding entry timing or width.

The four frozen hypotheses are: accepted premarket stop probability below .30
and severe-loss probability below .10; entry ATM IV divided by trailing
15-minute realized volatility at least 1.10; 15-minute path efficiency no more
than .60; and summed selected-leg bid/ask widths divided by entry credit no
more than .50. These thresholds are research choices, not demonstrated edges.
The volatility ratio compares approximate quote IV with calendar-annualized
recent realized volatility; it is not itself a calibrated volatility forecast.
Missing required inputs make an arm unavailable even if another filter fails.

Registration must precede its start date. Both the definitions and the code
are hashed. Each entry seals features, raw-snapshot lineage, forecast identity,
all take/skip decisions, the historical training IDs, selection probabilities
and one sampled paper arm. Outcomes are separate immutable records. A missing
quote path remains null; a deliberate skip earns zero less any assumed research
cost. No candidate on a blackout day means no arm trial that day. Collector
disappearance is explicitly unresolved when the post-close report runs.

Because all simulated counterfactuals are observable, the selector uses
**full-information exponential weights**, not a reward observed only for its
chosen arm. It uses at most 60 completed earlier sessions, a common calendar
where all currently eligible arms have known outcomes, and uniform weights
until 20 such sessions exist. Reward is net P&L divided by $200, clipped to
[-1, 1], with an additional 50% penalty on negative normalized returns.
The learning rate is 2 times the square root of the training-session count.
IV/realized-vol and trend contexts shrink toward the pooled estimate with
20 sessions of pooling strength. A 20% uniform mixture regularizes the weights.
This is a full-information experts problem, not a bandit: sampling provides no
additional learning signal because all arm outcomes are already observed.
The sampled selector measures a prospective hypothetical policy, not live
allocation performance. Weights never route orders or promote a template.
Reports expose common-panel counts, excluded sessions, missing counts by arm
and the remaining warmup. Intermittent news can delay or restart warmup when the
eligible arm set changes. Do not relax the common-calendar rule to manufacture
sample size; numeric-arm ablations still accumulate on their available days.

Costs reuse $7.20 per completed hypothetical trade and $1 per available news
forecast for each news strategy, including a deliberate skip. These are
per-strategy comparisons, not sixteen additive real bills. Cash has no research
charge. Missing-data calendars, correlated arms, multiple comparisons and
simulated fills prevent treating a highest-ranked arm as validated alpha.

Example registration and reporting:

```sh
python -m desk.odte.arms --init --start-date 2026-10-08 \
  --forecast-root desk/data/odte/text_overlay \
  --page ~/office/pages/odte_arms.html
python -m desk.odte.arms --report
```

For continuing after a one-day pilot, separately register an ongoing premarket
forecast source with `forecast_worker --init --premarket --root <new-directory>`
and pass `--continuation-root <new-directory>` when registering the arms.
Its frozen source is used only after the pilot date; the original pilot stays
unchanged. Prepare and run exactly one source each weekday at 08:45 ET, before
the 09:15 deadline. The runner records that source's independent Brier scores
and the arm observations. The report does no inference. A scheduled afternoon
review should run both the applicable forecast report and the arms report.

The generated local page contains the directory, paired returns versus T3,
selection history, factor ablations and per-arm daily feature/gate/lineage
drilldowns. Factor effects average matched combinations within each day before
counting sessions; sixteen combinations are not sixteen independent samples.
The first day is an operational trial. No automatic winner or live promotion.
The ignored `desk/data/odte/arm_experiment/` holds `manifest.json`, `decisions/`,
`outcomes/`, `sessions/`, hash-linked `observations/`, `volatility_outcomes/`
and reports. A page may be served at `/pages/odte_arms.html` by the local office.

### Preflight and changes to frozen dependencies

Run `python -m desk.odte.research_health` before the morning forecast. It exits
nonzero when a manifest, source identity, source code or registration timestamp
is invalid. It writes `desk/data/odte/research_health.json`. The daemon checks at
startup and every loop, including outside market hours, logs **RESEARCH BLOCKED
— ACTION REQUIRED**, and repeats a blocked warning every 15 minutes. The arm
page shows the blocked status even if its last successful results cannot be
recomputed. Hash checks alone do not prove model or market-data availability.

New manifests include per-file hashes to name changed dependencies. Changes to
shadow, templates or doctrine deliberately invalidate research: these files
determine the trade being measured. Fixing the trading code must never silently
pool outcomes under old rules. Preserve the old directories and registrations,
validate the repaired code, then explicitly register a new future experiment.
The research preflight and observer errors do not disable the ordinary shadow
collector or enable the live rail. Old records are never rewritten to appear
valid under the new code.

Page output is an optional absolute local path chosen at registration. It is a
convenience for this office installation, not a portable hosted deployment.
Moving machines requires choosing that machine's output path explicitly.
