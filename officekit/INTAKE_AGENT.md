# officekit intake agent — statement → answers JSON contract

This is the contract for an LLM agent that converts financial statements (brokerage
PDFs, 401k summaries, mortgage statements, venture spreadsheets — anything the
deterministic CSV importer can't parse) into the **answers JSON** that
`python3 -m officekit.wizard --answers <file>` turns into a rendered office
dashboard + scenario planner. The agent writes ANSWERS, never the balance-sheet
schema directly — intake owns beta assignment, kind derivation, and validation.

## The job

Read the documents the user supplied. Emit ONE answers JSON:

```json
{
  "owner": "<first name>",
  "as_of": "<YYYY-MM-DD — the LATEST statement date, not today>",
  "profile": {
    "net_buyer": true, "uses_leverage": false, "premium_selling_allowed": false,
    "decumulating": false, "concentrated_low_basis": false
  },
  "sleeves": [
    {"category": "cash",          "name": "Cash / MMF (Chase)",        "value": 82000},
    {"category": "public_equity", "name": "401(k) — Target 2050",      "value": 310000, "style": "target_date"},
    {"category": "real_estate",   "name": "Home",                      "value": 900000, "confidence": "tbd"},
    {"category": "real_estate_debt", "name": "Mortgage (6.1% fixed)",  "value": 410000, "rate_pct": 6.1}
  ],
  "imports": [{"kind": "positions_csv", "path": "positions.csv", "account": "Fidelity brokerage"}],
  "incoming": {"amount": 250000, "eta": "Dec", "character": "ordinary", "rate": 0.42},
  "income": {"annual": 350000, "years": 20, "style": "equity_linked"},
  "goals": [
    {"kind": "retirement",      "label": "Retirement", "date": "2050-01-01", "annual_spending": 120000},
    {"kind": "spending",        "label": "College — eldest", "date": "2034-09-01", "amount": 300000},
    {"kind": "liquidity_floor", "label": "Emergency floor", "amount": 60000}
  ]
}
```

Categories: `cash`, `cash_pending` (via `incoming`), `public_equity` (styles:
`intl`, `tech`, `target_date`), `single_name_equity` (style `megacap_tech`),
`fixed_income` (style `short_duration`), `municipal_credit`, `real_estate`,
`real_estate_debt`, `venture_private`, `direct_index`, `alpha_market_neutral`.

## Rules (non-negotiable)

1. **Never fabricate.** Every `value` must be traceable to a document or the
   user's explicit statement. A number the user "thinks is about right" is
   `"confidence": "assumption"`; a sleeve you know exists but can't value is
   `"confidence": "tbd"` with your best placeholder and a risk note saying so.
2. **Statement values win.** If a machine-readable positions CSV exists, list it
   under `imports` and let the deterministic importer classify it — do NOT
   re-type its rows into `sleeves`. Hand-extract only what the importer can't read.
3. **Debts are positive numbers** in answers (intake negates liabilities).
4. **Concentration is a fact, not a judgment.** A single stock ≥ ~15-20% of the
   investable total gets its own `single_name_equity` sleeve; note whether the
   basis is low (that flips the `concentrated_low_basis` profile flag — ask).
5. **The profile flags come from the user, not from vibes.** If the documents
   don't answer a flag, ask; if you can't ask, default conservatively
   (`net_buyer: true`, everything else `false`) and say so in a note.
6. **Windfalls:** anything not yet landed is `incoming` (never a `cash` sleeve).
   Tax `rate` only if the user confirmed character + rate; otherwise omit `rate`
   (the reserve simply won't be modeled — honest beats guessed).
7. **No betas.** Intake assigns category priors; do not invent loadings.
7b. **Goals come from the user's mouth, never inferred.** Retirement dates,
   spending targets, and liquidity floors are life-planning statements; documents
   don't contain them. Ask; if unanswered, omit the goal (no goals section is
   honest — a guessed goal is not).
8. **De-dup across documents** (the same account on two statements counts once;
   use the newer date).

## After emitting

Run `python3 -m officekit.wizard --answers <file> --out <dir>` and hand the user
their `<slug>_office.html` and `<slug>_scenarios.html`. If intake raises a
validation error, fix the answers — never hand-edit the generated balance sheet.
