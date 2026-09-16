# SCM — ADJUDICATION (Fable tier) — 2026-08-28

**Verdict: FLAT at $8.66 (live) — no starter; the file's named kill is blue's corrected rate-beta, and the instrument date is the ~Oct 15 Q4 dividend declaration, not the November print.** Supersedes the reverted 8/27 rubber-stamp ("rate-beta kill; 100bp cut removes a quarter of the dividend" — a correct copy of blue's headline that skipped the re-court triggers, the instrument date, and the entire kill audit). Benches: RED 8/26 18:31 (REJECT, 8/10), BLUE 8/26 20:02 (partially overturned, 7/10).

## Tape (live, this session)
$8.66 (52w low $6.83, high $13.45; +26.8% off the low — not a fresh dislocation). Bench tape accurate.

## Decisive disputes resolved
1. **Red F1 ("FV = coupon/observed yield = $8.62, tape is fair") — REDUCED: right conclusion, circular proof.** Blue's algebra objection is correct — coupon ÷ (coupon÷price) ≡ price; the identity can't rule anything fair. **Blue's Gordon frame adopted as the court's valuation:** NII $1.04/yr on NAV $12.80 → ROE 8.13%; at r≈11.6%, P/B = ROE/r = 0.70× vs tape 0.676×. The 0.68× "NAV discount" is a **coherent sub-cost-of-capital residual** — not an untested credit mark, and it closes 1:1 with ROE, mechanically. No mispricing is on offer at the tape.
2. **The operative kill — blue's corrected F7, primary-verified this session:** the Q2 10-Q (8/10) carries the debt composition verbatim — **Credit Facility $222.2M (floating), SBA debentures $257.3M (fixed)** (both FTS-confirmed in the filing), 2030 Notes $122.9M fixed. Net floating exposure ≈ 0.97×$968M assets − $222.2M ≈ **$717M → each 100bp of easing ≈ −$7.2M/yr ≈ −$0.25/sh, a quarter of the entire $1.00 coupon**, with zero credit deterioration required. Red netted all $600M of debt as floating and understated its own best kill 2×. KILL-CLASS: NOVEL. SCM is **a $717M unhedged long-SOFR position wearing a private-credit costume.**
3. **Red F4 ("adviser subsidy exhausted, recovery re-triggers the fee") — OVERTURNED, verified:** the waiver ran under the IAA's **"total return limitation provision"** — contractual language confirmed present in both the 2025 and 2026 10-Ks (FTS). A contractual cap, not generosity; while cumulative returns stay impaired the same provision *suppresses* fees on the way up. Red's kg_candidate `adviser_fee_waiver_exhaustion` is built on the misread — **REJECT-AS-WRITTEN**.
4. **Red F2 (buyback aggregation artifact) — SUSTAINED:** Q2 actual 274,343 sh @ $8.92 = $2.45M (the brief's 467,317 was cumulative); accretion $0.037/sh not $0.05. Revealed-preference inference REDUCED (gross-asset fee conflict real; leverage constraint also real).
5. **Red F6 (non-accrual "inflection" = composition) — SUSTAINED** (cost down, FV up = mix, not marks). **Red F5 (realized yield −120bp) — REDUCED to non-independent** (double-counts F6 + the rate leg).
6. **Catalyst date corrected (red F8, sustained):** dividends declare ~2 weeks BEFORE the preliminary 8-K; Q4 declaration ≈ **Oct 15**. The November "print" (11/11 vs 11/16, both vendor-derived, UNCONFIRMED) is not the first-information event.

## §CONSENSUS-KILL census
NOVEL: rate-beta (the kill); buyback artifact; composition-not-inflection. CONSENSUS: under-earned quarter ($0.34 declared vs $0.26 NII — the cut is the market's own explanation). Clean-court default does not fire: a NOVEL kill is named. Not a short (MEME n/a; it's a $250M BDC — the bar is yield-trap discipline, and shorting a 11.6% yielder into potential SBIC accretion is negative-carry against an unpriced binary).

## Prob-weighted FV
Blue's scenario frame adopted: 100bp of cuts → coupon ~$0.75 → FV ≈ $6.50 (−25%); everything-works (SBIC III drawn cheap + non-accrual recycling, net of the incentive-fee ratchet blue corrected) → coupon ~$1.25 → FV ≈ $10.80 (+25%). Roughly symmetric at tape = **RP_FAIR without an edge**; fairness verified but there is nothing to be paid for bearing — §fairly-paid-risk requires bounded tails AND a reason; the rate tail is unbounded by any hedge in the wrapper.

## Gates / packs
- **SCM|2026-10-15 (tier B):** Q4 dividend declaration (~Oct 15, pattern-verified from the 7/16 Q3 PR). Grades SCM-Q4DIV. A hold at $0.0833/mo + Q3 TII ≥$22.3M = re-court eligible; a second cut = file closes (coupon-anchor confirms, FV steps to ~$6.50 class).
- **Re-court triggers (any):** 40-APP/A GRANTED **and** SBIC III debentures *drawn* at <6.0% all-in (the 8/14 40-APP/A remains UNVERIFIED by all three tiers — unverified-ledger row); the Oct-15 hold+TII combination; or a rate-hedged sleeve wrapper (the only structure that neutralizes the named kill).

## Pre-mortem (v1.7)
(1) The Fed cuts 100bp+ and the coupon-anchored tape reprices ~1:1 — our base case, sized zero. (2) SBIC III draws cheap, ROE walks to 10%+, P/B closes to 0.85× without us — accepted; the trigger is dated and we'd re-court behind the draw, paying up ~8% for confirmation. (3) Tripwire-less unknown-unknown: a below-NAV issuance authorization in the unread DEF 14A (blue's flag) — dilution at 0.68× would be the one self-inflicted wound no rate path predicts. **"If this position loses money, the most likely reason will be that we bought a fair-yielding BDC for its NAV discount and the Fed removed a quarter of the coupon that was the only thing holding the price."**

## Orders
**NONE.** No band, no tripwire — the re-court gates are event-keyed (declaration, 40-APP/A), not price-keyed.

## KG rulings
- red `adviser_fee_waiver_exhaustion` — **REJECT-AS-WRITTEN** (mechanism inverted: contractual total-return cap, not spent generosity; verified at both 10-Ks).
- red `coupon_anchor_no_nav_closure` — **ACCEPT-AMENDED**: the FV test must use an INDEPENDENT required yield (peer-BDC cohort), never the security's own coupon/price (that identity returns the tape by construction); the closure test is Gordon (P/B vs ROE/r), per blue.
- adjudication-original `net_floating_exposure_vs_distribution` — **ACCEPT**: for BDCs/mREITs, compute net floating exposure (floating assets − floating liabilities) and express per-100bp NII sensitivity as % of the distribution; fires when >15%/100bp — the coupon is short the front end and the holder base prices only the coupon. Evidence: SCM $717M net floating → 25%/100bp.

## Calibration (parent to freeze)
**SCM-Q4DIV**: "Q4 declaration ~Oct 15 holds the $0.0833/mo ($0.25/qtr) rate," p=0.80, cat 2026-10-16, px 8.66. (Climatology guard noted: the informative outcome is the miss — a second cut inside two quarters; Brier graded against the 0.80 with the base-rate caveat recorded.)

## Notes
Benches IBKR-denied (7th docket); tape accurate. Unverified-ledger rows owed: 40-APP/A (8/14) status; DEF 14A below-NAV issuance authorization; asset-side floating share (~97%) re-read at the Schedule of Investments.
