> Court lane: tier-2 small/misc EXHAUSTED tail (scores 17-39), COURT_QUEUE_20260804.
> Date 2026-08-03. Price basis: **IBKR daily close 2026-08-03, TRADES/RTH, ib_insync bars**.

# UMAC — Unusual Machines | 0/10 AVOID (accounting basis corrupt; the screen scored a mark-to-market)
**live 23.08** (IBKR close 08-03, +9.1% on the day) · 47.79M shares (2026-03-31) → cap ~$1.10B ·
**PRINTS 2026-08-06 — ENTRY BLOCKED**

## The instruction was to verify the accounting basis before anything. Here is what it is.

### FINDING 1 (decisive) — 100% of "net income" is investment marks, and operations lose money
Audited XBRL, quarter ended 2026-03-31:

| line | $ |
|---|---:|
| Revenues | 8,095,836 |
| Gross profit | 2,654,107 (32.8% GM) |
| Operating expenses | 9,913,094 |
| **Operating income** | **−7,258,987** |
| **Nonoperating income** | **+17,541,981** |
| — of which unrealized gain on investments | +9,492,076 |
| — of which realized investment gains | +7,264,743 |
| **Net income** | **+10,282,994** |
| **Operating cash flow** | **−17,412,987** |

**Net income exceeds revenue.** The entire profit — and more — is fair-value gains on a securities
portfolio funded by equity issuance. ~$16.8M of marks on a portfolio built inside the quarter is a
~11% quarterly return: **this is not a treasury; it is a proprietary book bolted onto a drone-parts
distributor.** The screen's `netIncomeToCommon` and every ratio built on it are meaningless.

*Note on the parent's hypothesis:* the flagged mechanism was **warrant-mark** net income (SPAC-legacy).
`ClassOfWarrantOrRightOutstanding` went 1,397,579 (2024-12) → **0 (2026-03-31)** and
`FairValueAdjustmentOfWarrants` is de minimis. **Warrant marks REFUTED; investment marks CONFIRMED.**
Same corruption class, different channel — the screen guard should key on
`NonoperatingIncomeExpense / |OperatingIncomeLoss| > 1`, not on the warrant tag specifically.

### FINDING 2 — the absent revenue floor (the queue's own "rev3y None%")
TTM revenue **$17.25M** against a **$1.10B** market cap = **64x trailing sales**, 34x the Q1-2026
annualised run-rate, on a **32.8%-gross-margin hardware distributor with an operating loss.**
`rev3y` is `None` because the company has no three-year revenue history (reverse-merger; the
Fat Shark / Rotor Riot assets arrived in 2024). **The `MIN_REV_CAGR_3Y` gate could not evaluate a
`None` and silently passed it.** A hard absolute floor (e.g. TTM revenue ≥ $100M, or cap/TTM-revenue
≤ 15x) would have excluded UMAC before any quality gate ran.

### FINDING 3 — dilution
Shares outstanding **15,122,018 (2024-12-31) → 47,793,923 (2026-03-31) = +216% in 15 months.**
Q1-2026 alone: **$150.0M offering proceeds**, $11.2M issuance costs, $3.4M warrant exercises,
$142.5M net financing inflow. Cash $103.3M → $222.9M. Goodwill $7.4M → $15.6M (a bolt-on).
Equity $174.9M → $331.6M. **The company's balance sheet is the story; the business is $2.7M of
quarterly gross profit.**

## PATH CHECK
52w low 7.76 (2025-11-20, 253 days) → **+197% off the low**; 3y/52w high 33.42 (2026-06-02) → −30.9%;
**+57.7% off its 60-day low**; YTD +66.1%; +9.1% on 08-03 into a 08-06 print.
**GATE VERDICT: EXHAUSTED = RIGHT.** Episode decomposition 06-02 → 08-03: ARKK explains −14.4pp of
the −36.7%, residual −14.4pp (share 0.39). A momentum name giving back, in a momentum tape.

## Attention / conditioning
Stock Titan 07-28: *"Unusual Machines Shareholders Who Loaned Shares May Need to Act"* — a share-recall
notice, i.e. a live short-interest/squeeze dynamic. Plus CEO forgoing base pay for equity (07-28),
375k options to the CRO (07-28), BlackRock 7.2% (index-mechanical), and an August one-on-one investor
roadshow. **Discovery state: CROWDED. This is an attention instrument, not a diligence candidate.**

## Scenarios
| | p | fv | logic |
|---|---|---|---|
| bear | 0.40 | 4.00 | marks reverse, burn continues, trades toward net cash |
| base | 0.45 | 7.70 | $32M revenue at 5x sales (distributor comp) + ~$210M net cash |
| bull | 0.15 | 16.30 | US-drone-mandate revenue to $80M at 8x sales |

**e_fv $7.52 vs $23.08 → edge −67%.**

## VERDICT — 0/10 AVOID
Should never have entered the queue. Filed as a **screen-guard specimen**, not a candidate.

## Freezable (gate-test)
**UMAC | 2026-08-06 — bar: Q2-2026 GAAP operating income is negative. our_p 0.93.**
