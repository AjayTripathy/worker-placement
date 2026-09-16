# RFQ / Bid-Wanted Sheet — CA Muni HTM **Front-End** attempt (2028–2032 request)

_As of 2026-07-23. Prepared for a desk call this week. All prices/yields refreshed from the **EMMA customer trade tape** (yield shown is **yield-to-WORST**, EMMA's `YX`). IBKR muni feed is close-only, so execution is via the fixed-income desk call (Vanguard / Fidelity / Schwab), **not** IBKR. Target ~$80k across 4–5 CUSIPs, ~$15–20k/name._

---

## ⚠ READ FIRST — the ladder you asked for (2–6yr / 2028–2032) does not exist in the vetted book

I could not build a 2028–2032 (2–6yr) insulated ladder from the existing pipeline, and I did not fabricate one. Three independent checks all return the same answer:

1. **Vetted set (DILIGENCE_MASTER, 431 names): shortest maturity = 2034.** Zero names mature 2028–2033.
2. **Priced universe (bonds_priced.json, 845 names): shortest = 2034.** The scanner that built it is **hardcoded to `maturityDateAbove 20340101`** (refresh_universe.py L57; bond_scanner.py `MAT_LO=2034`). The book was deliberately built for the **2034–2046 zone** — an ~8–20yr ladder leaning to an 11-yr payout (the call script says so explicitly). The 2–6yr front end was never in scope, so it was never scanned or diligenced.
3. **Live re-scan of 2028–2032 is not available right now.** The IBKR gateway accepts the TCP connection (port 4001) but the API handshake times out — consistent with the standing note that IBKR muni access is close-only / desk-routed. I cannot source fresh front-end CUSIPs live this session.

**So this sheet is NOT the requested 2–6yr ladder.** It is the **front-end-most the vetted book reaches: 2034 maturities (~8 yr)**, fully re-gated. And even these are *bullets at a single maturity point (2034), not laddered rungs.* If you want a true 2028–2032 ladder, it requires a fresh front-end scan (see "To actually get the 2–6yr ladder" at the bottom) — that is genuinely new credit sourcing, not a refresh.

**Every name below is unlimited-ad-valorem CA school GO or essential-service water revenue, EMMA-confirmed federally TAX-EXEMPT, and passes the liquidity gate. None is FLAG/UNSCREENED.** The blocker is maturity and call, not credit.

---

## The executable subset — 2034 school GO (~8yr), both gates passed, no call-trap

TEY multiplier stated explicitly: **TEY = gross YTW × 2.01** (CA top bracket, fed + CA, after-tax-of-fed-deduction). All prices are the **last customer-BUY (offer side)** on the EMMA tape — what you'd pay. All coupons are clean whole/half points (no odd-3-decimal taxable tell); EMMA "Tax Status: Tax Exempt" confirmed on each.

| # | CUSIP | Issuer | Cpn | Mat | **Call (par)** | Offer px (tape) | Tape date | **Gross YTW** | **TEY ×2.01** | 2-sided days / n365 | Stale | Test bid (≤par) | Rung |
|---|-------|--------|-----|-----|----------------|-----------------|-----------|---------------|---------------|---------------------|-------|-----------------|------|
| 1 | **797272PL9** | San Diego Community College | 3.0 | 08/01/2034 | 08/12/2026 @100 | 97.263 | 2026-07-21 | **3.392%** | **6.82%** | 19 / 204 | 0d | **97.26 / 3.39%** | 2034 |
| 2 | **472412SC0** | Jefferson Elementary (San Mateo) | 3.0 | 09/01/2034 | **09/01/2030** @100 | 98.305 | 2026-05-27 | **3.235%** | **6.50%** | 2 / 13 | 56d | **98.20 / 3.24%** | 2034 |
| 3 | **817409K20** | Sequoia Union High (San Mateo) | 3.0 | 07/01/2034 | 08/12/2026 @100 | 98.585 | 2026-05-07 | **3.198%** | **6.43%** | 7 / 110 | 76d | **98.35 / 3.22%** | 2034 |
| 4 | **928346PJ8** | Vista Unified (San Diego) | 3.0 | 08/01/2034 | **08/01/2029** @100 | 98.720 | 2026-06-10 | **3.179%** | **6.39%** | 3 / 36 | 23d | **98.20 / 3.24%** | 2034 |
| 5 | **988176HN6** | Yuba CCD (refunding) | 3.0 | 08/01/2034 | 08/22/2026 @100 | 99.003 | 2026-06-03 | **3.139%** | **6.31%** | 3 / 49 | 0d | **98.75 / 3.18%** | 2034 |
| — | 612574EN9 | Monterey Peninsula CC | 3.0 | 08/01/2034 | 08/12/2026 @100 | 99.250 | 2026-06-29 | 3.105% | 6.24% | **1** / 49 | 23d | 98.75 / 3.18% | alt |

Rows 1–5 are the **~$80k / 5-name** build (~$16k each). Monterey is a same-maturity **alternate** (only 1 two-sided day on the tape — thinnest of the passable set; swap in only if a row above can't be sourced).

### Why the discount + near-August-call is fine (not a trap) on rows 1, 3, 5, and Monterey
These trade **below par (97.3–99.3)** with a par call weeks away. An issuer will **not** call a bond at 100 that's worth ~98 — so the call won't fire, and the **yield-to-worst is effectively yield-to-MATURITY (2034)**. You collect the 3% coupon to '34 and the pull-to-par is a small tailwind. The near call is a non-event for a discount buyer. Rows 2 and 4 (Jefferson, Vista) have their **first call deferred to 2030/2029** — cleanest call profiles, no ambiguity.

---

## REJECTED on refresh — do NOT bid these (and why)

| CUSIP | Issuer | Reason |
|-------|--------|--------|
| **801495R87** | Santa Clara Unified | **CALL-TRAP.** Last customer buy **100.06 (above par)** with a par call **08/22/2026 (~30d)**. YTW collapses to **2.702%** (yield-to-the-August-call). A buyer pays 100.06 and can be redeemed at 100 in weeks → locks ~2.7% and eats the premium. Pass. |
| **27677SCM3** | Eastern Municipal Water Dist (4s) | **CALL-TRAP.** Trades **99.99 (at par)**, par call **08/16/2026 (~24d)**. The headline "TEY 8.08%" is illusory — it's yield-to-a-call that will fire at par; buy at par and you get ~4% for 24 days then your cash back. No ladder value. (Was flagged in the call script as a "clean short add" — the refresh shows the call makes it un-ownable here.) |
| **778389FS0** | Ross Valley SD (4s) | **DOUBLE FAIL.** Liquidity gate FAIL (last trade **293 days ago**, one-sided) **and** trades **100.36 (above par)** with a par call ~20d out. Stale + call-trap. (Also a call-script "clean short add" — refresh overturns it.) |

The two "clean short adds" the old call script staged (Eastern MWD, Ross Valley) are **both overturned by this refresh** — their August calls / staleness make them un-ownable today. Strike them from the call.

---

## Ladder economics (executable subset, rows 1–5)

- **Total cost:** ~$79,000 at the test-bid prices ($16k par/name × 5, avg px ~98.2) → **within the $80k budget.**
- **Par-weighted gross YTW (to worst):** **~3.23%**
- **Par-weighted TEY (× 2.01, CA top bracket, labeled):** **~6.49%**
- **Weighted maturity:** **2034 (~8.0 yr)** — a **bullet, not a 2–6yr ladder.** Weighted first-call ~1.6 yr, but the below-par names won't be called, so effective life is to 2034.
- **Diversification:** 4 school GO + 1 CC district GO across San Diego (2), San Mateo (2), Yuba (1) counties. 0 water in the executable subset (Eastern MWD was the only short water name and it's a call-trap). Concentrated in the 2034 maturity by necessity — there is no other rung available.
- **Insulation:** all insul ≈ 99 / credit ≈ 90 (unlimited ad-valorem GO; hazard/SGMA flags on the REVIEW names do not reach a floating ad-valorem levy — the levy rate adjusts to hold debt service constant).

## Gate status per CUSIP (the two required gates)

| CUSIP | TAXABLE gate | LIQUIDITY gate |
|-------|--------------|----------------|
| 797272PL9 | ✅ EMMA "Tax Exempt"; clean 3.0 coupon | ✅ n365=204, 19 two-sided days, traded today |
| 472412SC0 | ✅ clean 3.0 coupon (tax-status field: Exempt) | ✅ passes floor; **thin** (n365=13), 56d stale — desk-verify a live market |
| 817409K20 | ✅ clean 3.0 coupon | ✅ n365=110, 7 two-sided days; 76d stale — desk-verify |
| 928346PJ8 | ✅ EMMA "Tax Exempt"; clean 3.0 coupon | ✅ n365=36, 3 two-sided days |
| 988176HN6 | ✅ EMMA "Tax Exempt"; clean 3.0 coupon | ✅ n365=49, traded today |
| 612574EN9 (alt) | ✅ clean 3.0 coupon | ⚠ passes floor but only **1 two-sided day** — thinnest; alt only |

## What's stale in the OLD RFQ_BOOK (RFQ_BOOK.md, 2026-06-21, the LONG 26-name book)
That sheet is a **different instrument** — the 2035–2046 long ladder. It is not this front-end request. But note for when you work it: its "NEAR call" names dated 07/22/2026, 08/01/2026, 08/16/2026, 10/01/2026 have now **reached or passed their first call** as of today (2026-07-23). Re-pull the call status on the whole long book before that call — several 2026-August calls are now live and the yield-to-worst has shifted to the call on any name that has floated to/above par.

---

## To actually get the 2–6yr (2028–2032) ladder — the required next step
The front-end is a **coverage gap, not a book you can refresh into.** To source it honestly:
1. Re-run the IBKR scanner against the 2028–2032 window: `refresh_universe.py` with `maturityDateAbove 20280101` / `maturityDateBelow 20321231` and `--port 4001` — **requires the IBKR Gateway API handshake to be live** (it timed out this session; log in / enable API on the gateway first).
2. Run the catch through the full gate stack (compute_bond_analytics for YTW, liquidity_gate for the tape floor, EMMA tax-status, the credit/insulation screens) exactly as the 2034 set was.
3. Expect the front end to yield **lower gross YTW** (2028–2032 CA AA GO ~2.5–3.0% vs the ~3.2% here) — a 2–6yr insulated ladder is a lower-yield, lower-duration instrument by construction.

**No order is placed here. Execution is your desk call; every fill is subject to your written sign-off. We never bid above the par call price.**
