# BDC 10-Q Schedule-of-Investments Parser — Data-Quality Memo (amendment A-5)

**As-of 2026-06-24. Source of authority: SEC EDGAR inline XBRL (10-Q, period 2026-03-31).**
Code: `engine/bdc_soi.py` · tests `engine/test_bdc_soi.py` · batch `run_bdc_soi.py` ·
parsed holdings `outputs/bdc_holdings/<ticker>_2026-03-31.json`.

## What this does
Brings the six high-moat BDCs that do **not** file NPORT-P (Phase-1 finding) into Arm A at
quarterly cadence. For each 10-Q it parses the Consolidated Schedule of Investments from the
inline-XBRL instance, computes the moat metric (A-1: **L3 ÷ total investments**), and exposes
a derived-NAV re-mark path `bdc_derived_nav(ticker, asof)`.

## Why XBRL, not the rendered HTML table
The SoI in the financial-report R-files (e.g. `R5.htm`) is a *vertical* render — one
(concept, value) cell per axis member, 30k rows, no per-holding fair-value level — that
double-counts issuer subtotals and is fragile to parse positionally. The authoritative,
machine-clean source is the inline-XBRL instance: every holding is an
`us-gaap:InvestmentOwnedAtFairValue` fact whose context carries a **typed member** on
`InvestmentIdentifierAxis` ("<issuer>, <type>" or "<issuer> | <field> | …") plus an explicit
period `<instant>`. We join cost / principal / coupon / spread by shared context.

## Which BDCs parse cleanly

| BDC  | period     | holdings | FV ($B) | BS total inv ($B) | tie-out | L3 % (A-1) | grade |
|------|-----------|---------:|--------:|------------------:|--------:|-----------:|-------|
| ARCC | 2026-03-31 |   1,425 |  29.55  | 29.50 | **+0.19%** | 97.76 | **CLEAN** |
| GBDC | 2026-03-31 |   1,779 |   8.24  |  8.32 | **−0.97%** | 100.00 | **CLEAN** |
| OBDC | 2026-03-31 |     556 |  16.00  | 15.34 | +4.30% | 93.51 | USABLE |
| PSEC | 2026-03-31 |     218 |   6.50  |  6.30 | +3.19% | 99.57 | USABLE |
| FSK  | 2026-03-31 |     618 |  13.66  | 12.27 | +11.37% | 85.98 | NEEDS_WORK |
| MAIN | 2026-03-31 |     706 |   6.15  |  5.67 | +8.39% | 99.57 | NEEDS_WORK |

Grade = |holdings-sum vs balance-sheet total investments|: CLEAN <2%, USABLE <5%, else
NEEDS_WORK.

**All six are confirmed Arm A** (L3 ÷ total investments ≥ 50%): 86–100%. The moat
classification is robust for the whole set; only the per-holding list tie-out varies.

## Two metrics that are reliable for ALL six (they do not depend on the holdings tie-out)
1. **Moat metric (L3%)** — read from the *filed aggregate* fair-value-hierarchy disclosure
   (`InvestmentOwnedAtFairValue` dimensioned by `FairValueByFairValueHierarchyLevelAxis`),
   not summed from holdings. ARCC 97.76% reproduces the Phase-1 XBRL figure (~97.8%) exactly.
2. **NAV reconstruction** — `net assets ÷ shares outstanding` reproduces the filed
   `NetAssetValuePerShare` to **< $0.005** on every BDC (ARCC error $0.0009).

## Per-holding fair-value LEVEL — a real data-quality limit (disclosed, not hidden)
BDCs do **not** tag a fair-value level on each holding the way NPORT does. The L1/L2/L3 split
is disclosed only at the **portfolio-aggregate** level in the Fair Value footnote. So:
- the **aggregate** L3% is authoritative (`level_basis` n/a — it's the filed figure);
- each holding's `level` is marked `L3_modeled` / `level_basis = modeled_structural` — we
  assign it by structure (the private loan book is L3; the small quoted sliver is L1), and we
  never fabricate a per-holding level the filing didn't disclose.

This is acceptable for the moat test (which needs the aggregate) and for the re-mark (which
keys off investment *type*, which IS in the identifier), but a per-name L1 carve-out (e.g.
ARCC's $35M quoted sliver) would need the footnote's L1 holding list, not the SoI.

## The ARCC unit test (locked, §4 of A-5) — PASS
- Fair-value tie-out: holdings sum $29.55B vs balance-sheet total investments $29.50B = **+0.19%**.
- L3% = **97.76%** vs Phase-1 ~97.8%.
- NAV reconstruction: $19.5891 vs filed $19.59 → **error $0.0009**.
- Flat-carry re-mark reproduces the filed NAV/share exactly (bookkeeping consistency); the
  residual non-investment of −$15.49B is the leverage (debt funding the loan book above NAV),
  as expected for a levered BDC.

## Re-mark driver design (`bdc_derived_nav`, models the OFFICIAL mark not fair value)
Between quarterly filings a BDC loan book has **no continuous markable NAV** — which is itself
the aggregation-cost moat (spec A-4). So the default is **carry-flat** (managers hold private
loans at last appraisal between marks). The official number departs from flat on two channels,
both observable at T−1 (no look-ahead):
- **Credit-spread channel** (`loan_index_bp_change`): a move in a broad leveraged-loan / HY
  credit-spread index marks the *debt* book by `smoothing × spread_duration × Δspread`. BDC
  loans are ~floating, so a SOFR move passes through to the **coupon**, not the par mark —
  only the **credit spread** repriced the fair value. `smoothing` (default 0.5) encodes the
  manager appraisal-lag vs traded credit; `spread_duration` default 2.5y (short direct loans).
- **Per-name event channel** (`name_events`, the A-4 primary signal): a discrete credit / IPO
  / restructuring / priced-secondary event on a portfolio company, applied as a multiplier to
  that issuer's holdings. This is where the frontrun edge lives — the official L3 number only
  moves on such datable events, and the re-mark anticipates the next print.
- `sofr_bp_change` is recorded (it drives income/coupon) but not applied to the FV mark by
  default for a par floater.

Equity stakes carry at last appraisal unless a name event fires.

## Which BDCs are blocked / need work, and why
- **None are blocked** — all six parse from primary XBRL, all six classify as Arm A, all six
  reconstruct filed NAV. The A-5 deliverable (moat confirmation + re-markable book + derived
  NAV) is met for the whole set.
- **FSK (+11.4%) and MAIN (+8.4%)** have an incomplete per-holding de-duplication: their SoI
  tags numbered-tranche and multi-section (LMM / private-loan) rollups whose values do **not**
  tie their children within the 1% gate the de-dup rule uses, so a residual double-count
  remains in the *holdings list*. Their **moat metric and NAV are still correct** (those read
  the filed aggregate). Closing the residual requires filer-specific rollup logic; deferred
  rather than forced, because an aggressive rule risks dropping real leaf positions (the
  discipline: never silently delete a holding to make a number tie).
- FSK note: its $1.707B "Credit Opportunities Partners JV" is correctly a **single** holding
  measured at NAV (`FairValueMeasuredAtNetAssetValuePerShareMember`), not a double-count — the
  bare/piped duplicate of it was removed; the residual is elsewhere and smaller-grained.

## Subtotal de-duplication (the core parsing problem)
Identifiers mix three rollup forms; we drop a row as a subtotal when:
1. another identifier extends it with a field separator (`H, …` ARCC-comma / `H | …` pipe);
2. it is a bare-issuer row duplicating a piped detail row of the same issuer at an **identical
   value** (FSK/OBDC footnote-superscript and numbered bare rollups), value-gated so a genuine
   standalone bare holding is never dropped;
3. it is a number-less parent of ≥2 numbered children whose values **sum to it within 1%**
   (MAIN `X | Secured Debt` over `… Debt 1/2`).
