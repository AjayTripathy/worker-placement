# Diligence Report — CUSIP 271014D58

**East Bay Municipal Utility District (EBMUD) — Water System Revenue Bonds, Series 2017A/B (5% coupon)**
5.00% coupon · due 2045-06-01 · callable at par 2027-06-01 · uninsured (AAA/Aa1-category) · subordinated net-revenue pledge
Cutoff: 2026-06-20 · Analyst desk: SignalOS muni_credit

---

## (a) Verdict, thesis, and resolved issuer

**Verdict: BUY (same benchmark-grade EBMUD credit and same Official Statement as 271014D66; this is the 5%-coupon
maturity of the identical issuer/system/pledge — the only differences are coupon, price and secondary liquidity).**

**Resolved issuer (CONFIRMED — identical to 271014D66).** Obligor is the **East Bay Municipal Utility District
(EBMUD)** Water System; the security is the **Series 2017 Water System Revenue Bonds**, payable from
**Subordinated Water Revenues**. This CUSIP is the **5.00% coupon** line of the same Series 2017 issue (271014D66 is
the 4.00% line). Same pledge, same supply, same coverage, same ratings, same OS — see CUSIP 271014D66 for the full
credit derivation; this report carries the same findings and flags the line-specific differences (price/liquidity).

**Why BUY:** identical clean subordinated net-revenue pledge, ~1.4M-person diversified base (top customer 4.3% of
revenue), Mokelumne Sierra-snowmelt supply (NOT Colorado/SGMA — see correction below), uninsured top-tier ratings,
double tax-exemption. The 5% coupon trades at a premium (~101.2), so the **par call 2027-06-01 is the worst-case
date** and yield-to-worst governs.

**Supply correction (carried from the issuer file):** a prior screen mislabeled EBMUD as "Colorado River / SGMA
Kings basin HIGH." **WRONG — corrected.** EBMUD runs on **Mokelumne River Sierra snowmelt** (Pardee/Camanche) with
a Sacramento River (Freeport) drought supplement; no Colorado dependence, not in the Kings/Tulare SGMA basin.

---

## (b) Security — the revenue pledge

| Claim | How verified | Source / authority | Finding |
|---|---|---|---|
| Subordinated net-revenue pledge | Read OS security clause (same OS as 271014D66) | OS cover/p.2 | **VERIFIED.** "Special obligations … payable solely from … a pledge of Subordinated Water Revenues." Junior to senior Water System Revenue Bonds. |
| Not Wastewater / not COP-lease / not special tax | Read carve-out | OS p.2 | **VERIFIED.** Pure Water System net-revenue credit; not payable from Wastewater revenues. |
| 5% coupon line of the same issue | Cross-check cache + structure | `water_revenue_cache.json`; structure screen (coupon 5.0) | **VERIFIED.** Same Series 2017 issue, 5.00% maturity (vs the 4.00% on 271014D66). |
| Insurance | Read cover | OS cover | **NONE (uninsured).** |

---

## (c) System and customers (concentration test)

- **System type:** Large retail **water** utility, ~1.4M people (Oakland/Berkeley/East Bay); separate wastewater
  (not pledged).
- **Customer diversification — CONFIRMED extreme:** largest account = 7.0% of water sold but only **4.3% of total
  water-sales revenue**; ten-largest are a small share. No single-customer dependency. Best-diversified base in
  the sleeve.

---

## (d) DSCR / rate covenant / WATER SUPPLY / Prop 218

(Identical to CUSIP 271014D66 — same issuer, same OS.)

### Debt-service coverage (DSCR)
- **Rate covenant: 1.1x** on Subordinated Water Revenues.
- **Coverage:** managed to a **1.6x policy target** (FY18 1.60x incl. $26M RSF draw; FY19 1.60x incl. $2M RSF draw;
  FY20–22 1.64/1.70/1.77x with **no further draws** and RSF replenished). **Cached continuing-disclosure series
  2.14 → 2.33 → 2.17 → 2.23 → 2.51x** — comfortably above both the 1.6x target and the 1.1x covenant. Modest RSF use
  is prudent reserve management against >$350M reserves, **not covenant engineering** (policy target >> covenant).

### WATER SUPPLY (load-bearing — lead here; CACHE LABEL CORRECTED)
- **Source: Mokelumne River, Sierra Nevada snowmelt (NOT Colorado, NOT Kings/SGMA).** 627-sq-mi watershed,
  Pardee/Camanche reservoirs, Mokelumne Aqueducts, with a **Sacramento River / Freeport (Bay-Delta)** drought
  supplement. Risk = Mokelumne multi-year-drought hydrology + Bay-Delta on the supplement; **no Colorado/SWP import-
  allocation dependence**. Drought surcharges + Water Supply Management Plan disclosed. More self-sufficient than
  the import-fed SoCal names.

### Prop 218
- Water rates are Prop 218 fees/charges (majority-protest, cost-of-service); multi-year rate schedule adopted.

---

## (e) Liquidity

- **EMMA trade tape (live, throttled, 2026-06-20):** **69 trades / 365 days**, but **only 2 in the last 90 days**,
  last print 30 days ago, **6 two-sided days**, median block ~$25k. **This 5% line is materially THINNER than the
  4% line (271014D66 = 178/yr) and shows a WIDE two-sided yield spread (~82 bps, price spread ~1.29 pt).** That wide
  spread is partly a premium-coupon / odd-lot artifact, but it is a real **execution caveat: prefer the 4% line
  (271014D66) for liquidity, or work this line patiently in size.** Treat as a higher one-time round-trip cost in
  an HTM ladder. Credit is identical and BUY-grade; the caveat is purely execution.

---

## (f) Tax status and yield

- **Tax status: DOUBLE TAX-EXEMPT (verified — same OS).** Interest excluded from federal gross income + exempt from
  CA personal income tax. 5.000% round coupon — premium bond, not a taxable-OID line.
- **Yield / TEY:** cached clean price ~101.2, after-tax-equivalent yield ~**7.64%** (lower than the 4% line's 8.04%
  because of the premium price; CA gross-up of gross YTM, not net-of-fee). **Premium + par call 2027-06-01 ⇒
  yield-to-WORST is the yield to the 2027 call, NOT yield to 2045 maturity** — quote YTW only; do not quote YTM.

---

## (g) Risks (lead with supply, then concentration/structure)

1. **WATER SUPPLY — Mokelumne hydrology + Bay-Delta supplement (primary, self-sufficient vs peers):** Sierra
   snowmelt base + owned storage + Freeport drought backstop. No Colorado/SGMA exposure (cache corrected).
   Multi-year drought is the monitorable.
2. **Subordinated lien:** junior to senior Water System Revenue Bonds; offset by deep all-in coverage and
   AAA/Aa1-category ratings.
3. **LIQUIDITY / execution (line-specific):** this 5% line is thin (69/yr, only 2 prints in 90 days, ~82 bps two-
   sided spread) vs the deep 4% line. **Execution caveat — prefer 271014D66 for liquidity.** Credit unchanged.
4. **Concentration: LOW / NOT A RISK** (top customer 4.3%).
5. **Honesty assessment: CLEAN.** Same disclosures as the 4% line; no divergence; nothing to exclude. BUY on
   credit; the only deduction is the execution caveat on this premium/thin line.

---

## (h) Sources

- **EMMA Official Statement — EBMUD Water System Revenue Bonds, Series 2017A / 2017B** (same OS as 271014D66).
  On-file: `/Users/ajay/exalted/signalos/verticals/muni_credit/data/_water_os/271014D58.txt` (+`.layout.txt`);
  PDF: https://emma.msrb.org/ER1061739-ER831638-ER1232568.pdf
  - Sections relied on: identical to 271014D66 — Subordinated Water Revenues pledge; 1.1x rate covenant; 1.6x
    coverage policy (FY18 $26M / FY19 $2M RSF draws, FY20–22 1.64/1.70/1.77x no draws); customer table (largest
    4.3% of revenue); Appendix A Water Supply (Mokelumne Sierra snowmelt / Pardee-Camanche / Freeport drought
    supplement / Bay-Delta / drought surcharges); tax opinion (double-exempt).
- **EMMA trade tape (live, 2026-06-20):** 69/yr, 6 two-sided days, **~82 bps spread, only 2 prints/90d** —
  thinner than the 4% line; execution caveat (`liquidity_gate`).
- **Issuer-litigation screen (2026-06-20):** federal (RECAP) + FCMAT clean; SEC municipal-disclosure web search
  returned no enforcement action against EBMUD.
- **SignalOS stores:** `data/water_revenue_cache.json` (DSCR 2.14→2.51x; top customer 4.3%). **Cached supply label
  "Colorado / SGMA Kings HIGH" is a confirmed mislabel — corrected to Mokelumne Sierra snowmelt + Bay-Delta.**

*Prepared by SignalOS muni_credit desk. Verified ≠ guessed.*

<!-- current-state-refresh -->
### Current-State Verification (AV / coverage refresh — 2026-06-20)

Refreshed 2026-06-20 via a SERIAL, throttled EMMA continuing-disclosure pull (original UNVERIFIABLE flag = EMMA 403 rate-limit, not a real gap). Latest issuer annual report: _Annual Financial Disclosures Posted 12/22/2025  for the year ended 06/30/2025 (365 KB)_. This is a REVENUE/enterprise bond (no ad-valorem AV base), so the current-coverage metric is the **debt-service-coverage ratio = 2.51x** (series 2.14x → 2.33x → 2.17x → 2.23x → 2.51x) for the latest reported fiscal year. This resolves the prior 'current DSCR/coverage UNVERIFIABLE' caveat with the verified datum.
