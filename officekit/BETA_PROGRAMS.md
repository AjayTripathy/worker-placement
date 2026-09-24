# Private beta and tax-loss harvesting programs

`/pages/beta_programs.html` is the shared workspace reached from Strategies,
incoming-money deployment pages and Harvest. Every office receives a suitability
assessment, including ETF and existing-manager alternatives. A saved program
contains a long-only policy, account, explicit inflow allocations, dated public
benchmark snapshot, approval provenance and operating records. It stays private.
The research catalog indexes the mandate as an `office_program`; it does not
publish the policy or household trading activity to the shared research exchange.

## Lifecycle and readiness

Eligible → Proposed (dated basket) → Approved (matching policy fingerprint) →
Funded (received-cash reconciliation) → Operating (fresh reconciliation, marks,
exact lots and complete household wash review). Readiness is separate: imported
historical approval survives stale data and reported broker errors without
claiming operation. Policy or funding-link edits invalidate approval; reapproval
requires a fresh funding reconciliation. Pauses/errors and all transitions keep
their references in history. Evidence cannot be future-dated. Operating records,
lots and household reviews expire after seven days; replacements after 30 days.

## Allocation and research

The same funding model protects tax, commitments, liquidity goals and recurring
income bills before allocating windfalls or income. Each inflow can be linked up
to 100% across programs. An approved reserve floor can retain more than the latest
tax estimate; the discrepancy stays visible. Bound shares are withheld from new
strategy proposals, including program cash retained, to prevent double allocation.
Unlink or reduce the share to propose something else. No balances are changed.

Public SPTM holdings refresh only on an explicit action. Constituent selection
uses benchmark weights, explicit exclusions, a name count and a per-name cap;
integer-cent allocations reconcile exactly. Infeasible caps produce no basket.
Active share is measured; statistical tracking error is not estimated. Missing
sector classifications remain unknown. The basket is a planning allocation,
not executable share quantities or an order file. Fees must be supplied, and a
short investment horizon requires review before approval. The Capital Planner
receives program context with goals, disasters, strategies and existing research;
full benchmark universes and raw household transaction records are omitted from
the proposal model's office-context payload.

## Harvesting overlay

The overlay uses reconciled account-level tax lots and the existing basis-review
workflow. Position estimates, unknown basis, stale marks, unresolved account
facts, missing replacement reviews, household buys inside ±30 days and open buy
instructions block a candidate. Activity and repurchase locks are combined across
all programs in the office. Replacement review must address substantially
identical securities; a ticker match alone cannot prove deductibility.

Overlay states are Awaiting lots, Needs data, Review available and Monitoring.
Completed-sale references create a 31-day repurchase calendar and can be voided
with a correction reference. These are review records, not broker tax accounting.
Projected loss value requires explicit tax-year gain capacity and tax-rate inputs.
Neither projections nor manually recorded harvests release the tax reserve.

All mutations use `/beta/program` with office revision checks and the hosted
owner/CSRF boundary. Portable imports normalize policy and ignore claimed runtime
funding/operation state. They may preserve an explicitly dated approval reference.
There is no brokerage execution path, automatic short extension, or public export.

Tests: `tests/test_beta_programs.py`, capital-planning, deployment, strategy,
donation-security, inference and hosted-workspace suites.
