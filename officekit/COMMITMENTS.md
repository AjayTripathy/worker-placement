# Capital and commitments

Implemented 2026-09-14. This document supersedes the earlier notes that treated
confirmed spending as a new discretionary goal and described a cash reservation
view as entirely future work.

## Durable facts and identity

`answers.json` is authoritative. `commitments.prepare_answers` gives manually
entered sleeves UUIDs before normalization. Mortgage rate, remaining term and
`terms_as_of` survive in normalized sleeve metadata. A derived mortgage ID follows
its sleeve UUID; a property-tax ID follows its home UUID. An inferred home gets a
real sleeve on the first value edit and retains the original property-tax ID in
`property_tax_id`. Further edits update that sleeve. Names and list positions are
never edit keys. The old `/goals/mortgage` route remains a compatibility adapter
and rejects ambiguous names.

`answers.commitments` holds overrides for derived records and fully specified
manual obligations. `balance_sheet.commitments` is the resolved projection:
identity, label, source, amount, annual amount where applicable, funding source,
frequency, next payment, optional end date, amount status, timing/funding
assumption flags and provenance. A resolved record is not a second asset or NAV.

The narrow legacy migration moves an expense goal with the exact old confirmation
button label `Lifestyle spending` into the stable `implicit:spending:lifestyle`
override, retaining its old goal ID. Unrelated expenses never remove lifestyle.
Retirement targets can refine the estimate under the spending rule below while
retaining the commitment's identity. This migration does not infer household intent
from arbitrary labels. Existing strategy links to a migrated legacy goal are not
reassigned to commitments; commitments do not need strategy adoption.

## Budget and payment model

Mortgage service uses monthly, fully amortizing principal and interest, including
zero-interest loans. The remaining term is anchored at `terms_as_of`, so moving
the balance date does not move the contractual payoff date. The calculation uses
the recorded outstanding balance and remaining months; it does not simulate or
write future principal reductions. A positive loan balance after its recorded
payoff remains a one-time principal cash requirement until corrected.

Derived annual commitments are exposed as implicit expense goals for existing
renderers. Confirming an amount does not remove their implicit/fixed role. Manual
recurring obligations also enter this first-call budget. The shared
`goal_projection._existing_debt_service` reserves active, portfolio-funded annual
amounts before discretionary affordability and contention checks. It counts each
mortgage once by sleeve identity. A commitment's own expense assessment excludes
itself from the already-reserved sum. Income-funded obligations remain visible
without drawing on the portfolio. The annual budget is conservative and
annualized; it is not a time-varying retirement simulation.

Retirement goals use `spending_basis: household_total` by default: annual spending
includes lifestyle. In decumulation, a current (undated or already-started)
retirement target replaces the statistical lifestyle amount until actual spending
is confirmed. It is visibly described as a retirement-target assumption. Actual
confirmed lifestyle is never silently reduced by a lower goal. The goal planner
claims only spending above what lifestyle already reserves. Several household
retirement targets share one spending pool and claim their maximum, not their sum.
Future targets do not replace today's lifestyle; accumulating households still
show lifestyle as income-funded. On the retirement goal page, `additional` marks
spending that really is separate and must be counted on top of lifestyle.

Home, Risk and Scenarios use the same saved terms and amounts. Scenario goal
overlays can target a stable ID. Kind-only overlays target discretionary goals;
they cannot accidentally change the first inferred mortgage. A scenario's
effective commitment amounts flow into its shared budget without mutating base
records. Retirement assessments deduct other fixed commitments while counting
the included lifestyle once. Plain dated-target and growth heuristics remain.

## Calendar semantics

`cash_calendar` covers the balance month and the next eleven calendar months;
payments before the balance date are excluded from recurring schedules. Cash
available to commit equals recorded cash less scheduled portfolio payments and
other reserved amounts, floored at zero. A deficit is reported separately and
feeds the Risk Officer and Home brief. Exact dollar amounts appear on Capital.

Investments, future income, pending inflows and forecast returns do not become
cash automatically. Outside-income obligations are displayed separately. Dates
default to the next first of the month and remain visibly estimated until set.
For mortgages this is strictly the month after the balance-sheet date, including
when that date is itself the first. An explicitly entered payment date takes
precedence. Other recurring estimates may start on the balance date if it is the
first of a month.
Monthly/quarterly schedules retain their anchor day across short months. Recurring
payments before the balance date are assumed paid; overdue one-time obligations
stay reserved until explicitly settled. Future one-time obligations beyond the
calendar also remain reserved.

Current tax reserves are held aside immediately. Tax explicitly linked to a pending
inflow stays reserved against those excluded proceeds, not current cash. Intake
persists `incoming.id`, copies it to the pending sleeve's `id` and
`tax_model.inflow_id`, and the generated liability carries `meta.inflow_id`.
`tax_funding` follows that identity; matching labels or amounts alone never exempt
a liability. The pending proceeds cap the amount excluded from current reserves.
Tax remains a liability in net worth. If the linked asset becomes received cash,
the tax becomes a current cash reserve; receipt must replace, not duplicate, the
pending asset. The page exposes the pending-funded amount separately.

Manual `tax` payments schedule current reserves first; only the excess is an
additional requirement. An explicitly scheduled payment remains a cash need even
when a pending inflow exists. Unlinked and unrelated taxes remain current; their
unscheduled remainder is visibly undated. This is funding attribution, not a rule
about when a tax is legally due or an automated tax-entity match. Property tax has
its own recurring card and should be edited there. Tax amounts still come from
the balance-sheet/tax model.

Capital calls and goal reservations are explicit one-time entries. A goal
reservation is an earmark, not an additional payment or a recorded purchase.
Release it when the payment is represented elsewhere. Settling a record changes
the obligation schedule only; it never changes custody balances, forgives a tax
liability, places an order or sends a payment. Discretionary goals are not
automatically cash reservations; their analytical capital claims remain in the
existing goal contention planner. Avoid adding both a reservation and a second
payment for the same obligation.

## Incoming money and receipts

Capital shows the existing `incoming` record's gross, estimated net, expected
date, received amount and remaining proceeds. `/inflows/preview` and
`/inflows/apply` record a receipt against a durable cash sleeve selected by ID.
The user confirms the net deposit is already included and supplies its date and
statement/transaction reference. This is user-confirmed balance attribution,
not automatic bank-transaction verification. Refresh/import the account first;
receipt recording never increments cash. Account/source/evidence snapshots are
retained on each receipt, even after subsequent imports, spending or account
closure. Duplicate active references within an account are rejected.

`answers.inflow_events` is an append-only list of receipts and reversals. Each
receipt carries an ID, inflow ID, gross proceeds, withholding, date, account ID,
reference, evidence snapshot and recorded timestamp. A reversal references an
active receipt and requires a reason; replacement receipts are separate events.
Repeated apply tokens are no-ops, even after preview cleanup. Invalid, stale and
expired proposals never publish an event. Previews share the commitment TTL and
cap. Cash-source/tax-model changes invalidate a review even without an answers
revision change. Receipt facts and audit are published together via an atomic
replacement of answers.json; derived pages remain rebuildable, not a multi-file
transaction. Existing cross-process concurrency limitations still apply.

Received gross reduces pending gross. The tax model retains the full expected
gross and uses received fraction to allocate its modeled tax. Recorded
withholding reduces the outstanding liability once, first against the received
share; excess withholding reduces the pending share. Any credit above the total
modeled liability is a non-cash `tax_asset`, explicitly estimated. Liability
plus credit, cash and pending proceeds conserve net worth across a correctly
matched receipt. Home and Scenario Planner use only the remaining net proceeds
in deployment illustrations. Cash and pending sleeves retain cents.

Receipts cannot be future-dated or postdate the selected account snapshot. A
receipt newer than the office planning date advances that date, disclosed with
the changed calendar in the preview. It does not redate other source marks.
Earlier recurring payments follow the existing assumed-paid convention; overdue
one-time obligations stay reserved. No receipt is inferred from an expected date.

This first workflow supports the existing single inflow and partial receipts.
Multiple expected inflows, verified transaction matching, settlement of actual
outgoing payments, and manual account balance replacement are later extensions.

## Edits and AI review

Forms identify the commitment and carry a digest of the saved office revision.
The server validates finite amounts, rate/term bounds, enums and dates. Blank
fields mean unchanged, so saving a date does not confirm an assumed amount.
`/commitments/preview` sends only the selected commitment's editable facts and the
request to the configured intake model. It validates the bounded patch and the
whole candidate before showing a before/after table. Previews live in
`commitment_previews/<uuid>.json`; `/commitments/apply` loads the saved proposal
and rejects stale/replayed revisions. Unapplied previews expire after 24 hours;
applied files are retained for seven days, with at most 100 token files in total.
Cleanup runs at server startup and on commitment actions. Expired apply requests
require a new preview. The separate before/after history remains durable and
includes the applied proposal ID. No model patch goes through goal creation.

Successful new-route edits append before/after records to
`commitment_history.jsonl`. An in-process write lock coordinates commitment
actions with builds. Capital and Risk are rendered with the other core pages before any
answers are written. This does not make the entire folder transactionally atomic:
cross-process edits, crash-safe publication and atomic audit+state writes remain
separate infrastructure work. The existing legacy editors are not all protected
by optimistic concurrency.

## Verification and next boundaries

`tests/test_officekit_commitments.py` drives the real HTTP routes in a synthetic
office, rebuilds from disk, and checks mortgage terms, home identity, spending
priority, school fees, AI review/apply, stale proposals, invalid fields, payment
frequencies, tax reserve conservation and overdue obligations. Provider responses
are stubbed; no live model or broker is required. Browser acceptance uses a
separate synthetic office, never edits the principal's financial facts.
The wheel includes this contract and the public design/architecture references;
the internal agent handoff stays outside the distribution.

The old `/goals/mortgage` POST remains reachable for forms in cached older pages;
current Home and Capital forms use `/commitments/update`. Regression tests cover
legacy saves and rejection of ambiguous names. It can be removed with an explicit
compatibility cutoff rather than silently breaking those tabs.

Next extensions: imported statement payment terms; richer links between tax
entities, goal reservations and actual payment records; account-level funding
sources; scheduled verified net income; recurrence exceptions and per-payment
settlement; inflation and time-varying retirement spending. Feed independence for
identical non-generic account labels remains explicitly deferred.
