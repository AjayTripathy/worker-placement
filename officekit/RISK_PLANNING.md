# Goals-based risk planning

Risk, Scenarios, capital proposals, and beta/TLH comparisons share
`risk_planning.py`. The recommended loss limit is conditional funding capacity,
not a forecast of maximum loss, adviser approval, or a guarantee.

## Household capacity

Accessible cash plus signed marketable positions support dated bills, protected
goals, a spending reserve, and an unexpected uninsured bill. Home equity, private
assets, pending proceeds, and restricted accounts cannot support today's limit.
Mixed pools with a declared restriction are excluded until split. Mortgage
principal is not payable twice: scheduled payments enter the calendar; missing
other-debt schedules remain a coverage gap.

The horizon defaults to 30 years, cash protection to 12 months (24 for a
withdrawal-funded household), income interruption to 12 months, and the remaining
capacity buffer to 10%. All are visible, editable assumptions. Spending defaults
from goals and recurring bills. Reliable after-tax income needs both an amount
and an end date; no amount is inferred from capitalized lifetime earnings.

The largest cumulative funding requirement over the horizon determines capacity,
assuming zero real investment growth. Recurring bills are included within total
household spending. One-time payments and additional expense goals are added;
existing goal reservations avoid duplicate charges. Financing goals use the
existing down-payment and carrying-cost model, with explicit estimated terms.
A lower comfort preference can reduce financial capacity but cannot raise it.
Confirmed reserve inputs also enter incoming-money deployment budgets.

Scenarios independently edit factor shocks, inclusion, spending inflation,
income interruption, receipt delays, sale haircut, unexpected bills, and the
cash-flow horizon. Each timeline reports the first need for sales, reserve breach,
and funding shortfall. A mortgage due in a shortfall month flags payment risk;
it does not predict foreclosure. Sale taxes, contractual collateral requirements,
and intramonth timing still need account-level facts. Harvesting gains never
appear automatically as cash in this model; failed offsets can increase reserves.

## Research and scoring

Probability modes are stress-only, an office assumption, or reviewed research.
Scenarios overlap, so probabilities are not summed or normalized. Research
requires an explicit event, window, deadline, and resolution rule. Aggregation
matches that entire contract and excludes conditional, unreviewed, expired, or
resolved calls. Source families receive equal weight; unrecorded dependence is
pooled. Disagreement ranges are not confidence intervals and sample-poor skill
scores do not gate research or capital.

The scenario-forecaster profile uses the existing intelligence interface. Two
analyses see the same public evidence independently; adjudication sees both.
Connector admission is default-deny, source passages are digest-bound, and
citations must exist in the retrieved text. Human review remains necessary for
semantic support and applicability. All three calls validate before a single
ledger append. Retrieval gaps remain visible; provider or citation failures
cannot create successful forecasts. Hosted HTTP failures now produce failed jobs.

Schema-2 scenario records extend `research/predictions.jsonl`; they do not create
a second research store or reusable detector format. Catalog discovery includes
them. Native record import preserves claimed origin in the explanation, captures
at import time, and requires fresh review. It does not authenticate the submitter
or grant redistribution rights. Saving an office forecast never publishes its
identity, household inputs, or source text to the public exchange.

Updates link to the immediately preceding immutable call and cannot change the
event contract. The first call per submitter/agent/event is the primary Brier
observation; resolving a revision settles that original too. Outcome corrections
remain append-only. Conditional forecasts require distinct event identities and
are not mixed with unconditional scenario estimates.

## Deployment and shorts

Proposals show current-cash and conditional-receipt comparisons against holding
cash, using their frozen office snapshot. Beta programs use the same comparison.
Both sides receive identical hypothetical cash; no receipt or trade is recorded.
Known funds use existing category priors. Unknown fund classifications and option
contracts produce an incomplete comparison, rather than a fabricated payoff.
Breach findings keep new proposals in review; they do not execute allocations or
change an existing mandate's approval history.

Short look-through identifies signed positions by ticker, account, sleeve and
strategy, links matching catalog research, and shows stock-price squeeze
sensitivities and supplied borrow terms. Unknown manager gross exposure remains
unknown; net NAV is not a substitute. Short options require contract repricing.

## Verification

`tests/test_risk_planning.py` covers household arithmetic, cash conservation,
financing, pending receipts, income loss, revisions, Brier attribution, evidence,
and local forms. `tests/test_hosted_risk_planning.py` covers private durable saves,
queued forecasting, replay, review, stale writes, and failed-provider status.
Other capital, deployment, beta, calibration, privacy and admission suites cover
the shared paths. All fixtures are synthetic. Live research additionally requires
an operational model key with API credit and reachable primary sources.
