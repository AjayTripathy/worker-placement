# Frontrun Engine v0 — CEF/BDC NAV Re-mark · PRE-REGISTERED PILOT SPEC

**Status: LOCKED 2026-06-24, before any backtest data is gathered.** This document fixes the hypothesis,
universe, classifier, signal threshold, controls, and success criteria *in advance* so the result cannot be
fished. Any change after data is touched must be logged as an amendment with a reason, and the original
test reported alongside.

---

## 0. The principle being tested (the real claim)

The frontrun edge is NOT "front-run a known event." It is **"compute the not-yet-disclosed number from
primary sources that are expensive enough to aggregate that the market hasn't, and is therefore anchored on
the stale official print."** The *aggregation cost is the moat.* This pilot tests that claim directly via an
A/B (high-moat vs low-moat) split — the edge must VANISH in the low-moat control, or it isn't our edge
(it's just the known CEF-premium-mean-reversion factor).

## 1. Hypothesis (pre-registered)

> A same-day, point-in-time, primary-source re-mark of a fund's portfolio ("derived NAV") predicts (a) the
> direction of the next official NAV print's change and (b) subsequent premium/discount convergence —
> **materially in Arm A (high-moat, hard-to-aggregate holdings) and ~not at all in Arm B (low-moat, trivially
> computable holdings).** Confirmation requires `edge(A) − edge(B)` to be significant, not merely `edge(A) > 0`.

## 2. Universe & the moat classifier (objective, from NPORT)

**Moat score = % of fund NAV in Level-3 (unobservable-input) fair-value assets**, read from each fund's
NPORT-P fair-value-hierarchy disclosure. This is objective and pre-data.
- **Arm A (HIGH moat): Level-3 ≥ 50% of NAV.** Candidates (to be verified by the build, not assumed):
  DXYZ (pre-IPO venture); BDCs with private loan books — ARCC, ORCC, FSK, MAIN, PSEC, GBDC; any
  listed venture/pre-IPO CEF. Target ~8 funds.
- **Arm B (LOW moat / CONTROL): Level-3 ≤ 10% of NAV** (≥90% Level-1 public equities). Candidates:
  ADX, CET, GAB, USA, RVT, and similar liquid-equity CEFs. Target ~8 funds.
- Funds with 10% < L3 < 50% are EXCLUDED (ambiguous; keep the arms clean).
- **Survivorship:** the universe MUST include funds that liquidated/merged/delisted in the window. Build the
  list from a point-in-time membership as of the window start, not today's survivors.

## 3. Derived-NAV computation (point-in-time, no look-ahead)

At each official NAV date T, reconstruct **derived NAV as of T−1** using ONLY information public at T−1:
- Holdings = the most recent NPORT filed *before* T−1 (≈60-day lag — this is a real constraint, see §6).
- Marks: Level-1 holdings at their T−1 close; recently-IPO'd holdings at T−1 live price; private holdings at
  last disclosed round **plus** any mark-able public comp/credit-spread move; apply the fund's stated
  marking convention (DLOM for locked/recently-public, appraisal lag) — **we model the OFFICIAL number, not
  fair value** (see §6).

## 4. Signal (pre-registered threshold)

Fire when BOTH:
1. `|derived_NAV(T−1) − last_official_NAV| / last_official_NAV ≥ 5%` (the official print will surprise), AND
2. the price-implied NAV (price ÷ assumed premium/discount) still reflects the *stale* official NAV — i.e.,
   the market has not yet repriced toward the derived NAV.
Direction = sign(derived_NAV − last_official_NAV). Trade = long the discount / short the premium toward the
derived NAV; held to the official print (and a defined convergence window).

## 5. What we measure (the outcome)

Per fired event: (a) did the next official NAV print move in the predicted direction? (hit/miss); (b) did the
premium/discount converge toward the derived NAV? (bps of convergence); (c) trade P&L **net of borrow +
bid/ask**. Aggregate per arm → `edge(A)`, `edge(B)`, and `edge(A) − edge(B)`.

## 6. Controls (each one a discipline this pilot must honor)

- **NPORT lag = the main enemy.** Re-marked holdings are themselves ~60 days stale → the signal is GATED to
  **low-turnover funds** (annualized holdings turnover below a pre-set cap, measured from successive NPORTs).
  High-turnover funds are excluded by rule, not treated as a failure. (Low turnover overlaps with the
  high-moat venture/private set — convenient and intended.)
- **Model the OFFICIAL mark, not true value.** Score against the fund's *printed* NAV; our re-mark must
  predict their marking convention (DLOM/appraisal), not fair value.
- **Tradability gate (the DXYZ lesson).** Net of stock-borrow cost and bid/ask; flag hard-to-borrow / squeeze
  risk; a premium you can't short or a discount you can't access ≠ an edge.
- **Survivorship** (see §2). **No fishing:** threshold (§4) and arm split (§2) are locked here, pre-data.
- **Multiple comparisons:** one primary test (`A − B`); any secondary cut is exploratory and labeled so.

## 7. Success criteria (binary, pre-set)

- **Arm A:** NAV-surprise direction hit-rate **> 65%** AND convergence trade positive **net of costs**.
- **Arm B (control):** **not** statistically significant.
- **Primary:** `edge(A) − edge(B)` significant → the computation moat is real → scale to the CEF/BDC universe.
- **Kill:** if `A ≈ B` (both work) → it's CEF mean-reversion, not our moat → stop. If `A` insignificant → no
  edge → stop. Either way, the negative result is the finding (it still encodes microstructure knowledge).

## 8. Free out-of-sample: DXYZ live

We hold a derived NAV (~$26, 2026-06-24, est. ±$3). When Destiny prints its next official NAV, score it cold
— one forward, no-look-ahead data point graded against this spec while the backtest base rate is built.

## 9. Phasing

- **Phase 0 (this spec):** locked.
- **Phase 1:** finalize the two fund lists (verify Level-3 % + turnover from NPORT; build point-in-time
  survivorship membership), build the derived-NAV engine, gather point-in-time NAV/price/holdings data.
- **Phase 2:** run both arms; report `edge(A) − edge(B)` with all §6 controls applied.
- **Phase 3:** scale only if §7 primary criterion holds.

---

## AMENDMENTS (logged 2026-06-24, post-Phase-1, pre-Phase-2 scoring — all §1–§9 originals above PRESERVED)

- **A-1** — moat denominator for levered BDCs = **L3 ÷ total investments** (L3÷NAV gives meaningless 205–236% under leverage). Classification rule otherwise unchanged.
- **A-2** — the §6 turnover gate, left unspecified, is fixed at **30%/yr** (pre-registered before any scoring; passes DXYZ/RVT/GAB/CET, fails ADX).
- **A-3** — primary moat rule stays **L3 ≥ 50% / NAV**. ADD a *labeled secondary* "ex-cash-sweep L3" that admits **RVI / Robinhood Ventures Fund I** (48.3% raw, ~100% ex-cash) to an **Arm-A-extended** set. Primary test still uses the locked rule.
- **A-4 — THE PIVOT (primary Phase-2 test is now EVENT-DRIVEN).** Phase 1 proved the high-moat funds have *no continuous markable NAV* (BDCs don't file NPORT; DXYZ NAV is episodic; private holdings re-mark only on discrete events) — which is itself confirmation of the aggregation-cost moat. Therefore:
  - **Primary signal:** a private holding of an Arm-A fund undergoes a *datable MARK-EVENT* (priced round / large secondary / IPO / tender) that moves derived NAV ≥ **5%** (the §4 materiality threshold, unchanged) vs the last official NAV.
  - **Test:** does the fund's premium/discount (price vs last-official-NAV) converge toward the *derived* NAV **before** the next official NAV print? Measure pre-print convergence captured (the frontrun) vs post-print.
  - **Arms:** Arm A = venture/pre-IPO funds (DXYZ, RVI, + BDCs once the parser lands); **control** = event-matched liquid-equity CEFs, where the analogous holding move is already in the daily NAV (predict: **no** pre-print gap).
  - The daily-NAV panel is demoted to the engine unit-test / Arm-B mechanic. The **>65% hit-rate and the `edge(A) − edge(B)` primary criterion (§7) are UNCHANGED.**
- **A-5** — BDC 10-Q Schedule-of-Investments parser added to Phase-2 scope (enlarges Arm A to ARCC/FSK/GBDC/OBDC/MAIN/PSEC at quarterly cadence).
