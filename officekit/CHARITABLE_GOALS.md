# Charitable goals

`kind: "charitable"` records giving intent separately from consumption and tax
efficiency. Create one through Goals or onboarding, then open its detail page.
Existing spending goals labeled philanthropy are not silently reclassified.

The goal carries its amount and intended gift date. Its `charitable` object holds:

| Field | Meaning |
| --- | --- |
| `vehicle` | `undecided`, `direct`, or `daf` |
| `funding` | `undecided`, `cash`, or `appreciated_securities` |
| `recipient`, `recipient_qualified` | Recipient/sponsor and explicit eligibility confirmation |
| `symbol`, `cost_basis` | Actual owned public ticker and basis of the proposed gift portion |
| `long_term`, `before_sale` | Confirmed holding period and transfer timing |
| `deductible_amount` | Reviewed deduction usable this gift year, after applicable limits |
| `deduction_tax_rate` | Reviewed effective benefit rate, as a fraction |
| `capital_gain_tax_rate` | Reviewed rate on the donated securities' gain, as a fraction |
| `tax_review_reference` | Reference and date for the review supporting these inputs |
| `reserve_cash` | Explicitly reserve a cash gift in the existing commitments calendar |

Omitted tax inputs remain unknown. The editor displays rates as percentages;
JSON stores fractions. A deduction cannot exceed the gift amount. An optional
cash reservation requires cash funding and a valid date. It has the stable ID
`charitable:<goal-id>` and is derived from the goal; edit or release it there,
not as a second manual commitment. No donation, sale or transfer is executed.

## Modeling and research

The goal evaluates available cash after other commitments and cash floors, or
the recorded owned market value of its selected public ticker. Disaster models
apply the sleeve's shock to that ticker's available value. Pending proceeds do
not count as available today. Goal contention counts the entire gift, with no
assumed replenishment from tax benefits.

The existing `gifting` strategy uses the charitable program playbook. Its goal
link opens the same saved-research discovery, independent review and proposal
workflow as other strategies. The Capital Planner and other new strategy
proposals receive a frozen private `charitable_goals` assessment. The proposal
page shows the gift, funding choice, reservation, tax scenarios and open items.
General security courts and shared research do not receive these private terms.
Capital planning version 3 marks older deployment research for a fresh review.

## Securities and missing basis

The giving page includes a deterministic shortlist and illustrative mix sized to
the gift. It ranks long-term appreciated holdings in confirmed taxable accounts
by embedded gain per donated dollar. Actual lots are kept separate by account;
aggregate rows are not counted alongside their lots. Position-level partial gifts
use proportional basis estimates and visibly require exact-lot confirmation.
The shortlist is a tax-efficiency comparison, not a portfolio optimizer, final
selection, transfer instruction or charitable deduction valuation. Sponsor
acceptance and portfolio fit remain part of the strategy review. Each goal's
comparison is independent; shared holdings cannot fund multiple gifts twice.

Missing basis, holding period and account status appear in an inline review form.
Enter total adjusted basis for the named lot or account position, never basis per
share. Blank stays unknown; zero must be entered explicitly. Reviews require a
statement/review reference, live in private `answers.security_basis_reviews`, and
are reused by other giving goals. Saved reviews can be edited or cleared. They
supplement missing source facts and cannot overwrite contradictory imported facts.
The review is bound to the holding, account, lot and source fingerprint; changing
the underlying snapshot requires reconfirmation. POST forms also reject stale
office revisions, and the hosted route retains normal tenant and CSRF checks.

Classification preserves holdings, accounts, lots and basis through the same
intake pipeline used to build NAV. CSV imports recognize total cost-basis columns;
Flex and currency conversion preserve missing/invalid basis as unknown. Loss
harvesting counts position-derived sleeves once after this metadata preservation.
Unreconciled lots, short positions, options, known retirement accounts, restricted
holdings, cost-only marks and unconverted currencies cannot enter the shortlist.
Candidates, missing facts and review provenance remain private proposal inputs.

Valuation reference: [IRS Publication 561](https://www.irs.gov/publications/p561).

An entered usable deduction multiplied by its reviewed effective benefit rate
is a scenario, not a computed tax return. Avoided-gain modeling additionally
requires sufficient actual owned shares, basis, eligible recipient, long-term
holding and pre-sale transfer confirmation, review reference and gain tax rate.
This gain belongs to the donated shares; it cannot erase an unrelated gain
already realized. Neither scenario reduces the windfall tax reserve or increases
deployment cash automatically. Review all gifts together so annual deduction
headroom is not reused across goals. There is no aggregate tax-return engine.

The vehicle comparison distinguishes direct giving from a DAF contribution.
A DAF contribution leaves household ownership; subsequent grants do not produce
another contribution deduction. Eligibility, lots, valuation, substantiation,
recipient acceptance and binding-sale issues remain review inputs.

Sources checked September 21, 2026: [IRS Publication 526](https://www.irs.gov/publications/p526),
[2026 Publication 505](https://www.irs.gov/publications/p505), and
[IRS donor-advised funds](https://www.irs.gov/charities-non-profits/charitable-organizations/donor-advised-funds).
The 2026 floor and itemized-deduction limits are why a gross gift multiplied by
an assumed marginal rate is not treated as a usable tax benefit.

## Validation

`tests/test_charitable_goals.py` covers validation, unknown assumptions, cash and
appreciated shares, stress, DAF treatment, reservations, windfall and income
funding, onboarding, local and hosted editing, private research inputs, catalog
reuse and the goal-to-strategy link. Model outputs and tax assumptions are
synthetic; these tests do not validate a provider's tax advice.

`tests/test_donation_securities.py` adds ranking, gift sizing, zero/missing basis,
multiple accounts, mixed holding periods, inconsistent lots, source refreshes,
review correction, import preservation, harvest deduplication, both HTTP transports
and exclusion of private custody/basis details from general security research.
