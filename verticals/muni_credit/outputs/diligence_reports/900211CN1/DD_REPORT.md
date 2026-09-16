# Diligence Report — CUSIP 900211CN1
## Turlock Unified School District (Stanislaus + Merced Counties, CA) GO, 3.0% of 08/01/2042

**Prepared:** 2026-06-20 (cutoff = today) · **Vertical:** muni_credit · **Analyst layer:** SignalOS verification
**Status in book:** held / reference name (deep-discount de-minimis math anchor)
**Verdict:** **BUY (HOLD-grade credit; deep-discount-not-distress confirmed)** — see Section (h)

---

### a. Snapshot & the question being tested

| Field | Value | Source |
|---|---|---|
| Issuer | Turlock Unified School District, California | EMMA issue ER390593; OS p.1 |
| Issue | GO Bonds, Election of 2016, Series 2019 | EMMA scale / OS cover |
| Coupon / Maturity | 3.000% / 08/01/2042 | EMMA Security/Details; scale row matches ($1,875,000 principal, 3.14% offer yield) |
| Dated date | 05/22/2019 | EMMA Security/Details |
| Call | 08/01/2026 @ 100 (par, no premium); bonds due ≤08/01/2026 are non-callable | OS "Optional Redemption," p.~8 |
| Pledge | **Unlimited ad valorem GO** + statutory lien (Gov. Code §53515) | OS "Security and Source of Payment" |
| Tax status | Federally tax-exempt; CA-exempt; **not** AMT preference | OS cover + Tax Matters |
| Last trade (sale-to-customer) | **81.913** @ **4.584% YTW**, 2026-03-24 | EMMA trade tape |
| Most recent print (inter-dealer) | 81.86, 2026-03-24 | EMMA trade tape |
| Trades on tape | 196 (active two-sided market 2019→2026) | EMMA trade tape |

The thesis under test: **this is a deep discount because of coupon/rate structure, not because of credit distress.** A 3% coupon bond in a ~4.5% market trades to a price discount mechanically; the diligence job is to confirm the issuer credit is sound and that the deep-discount-to-par economics (and the after-tax TEY) are correctly characterized. Both confirm.

---

### b. Issuer & pledge verification (Item 1)

**Claim → method → authority → finding.**

- **Claim:** Unlimited ad valorem GO, SB-222 statutory lien, tax-exempt.
- **Method:** Downloaded the actual Official Statement from EMMA (post-disclaimer session), extracted text, read the security and tax sections verbatim.
- **Authority:** Official Statement, Series 2019 (saved to `raw/official_statement.pdf`, text in `raw/os.txt`); EMMA Security/Details/900211CN1.
- **Finding: VERIFIED.**
  - *Unlimited GO:* "The Stanislaus County Board and the Merced County Board are empowered and obligated to annually levy and collect, **without limitation as to rate or amount** … ad valorem taxes upon all property subject to taxation by the District" (OS ¶ ~933–946). This is a true unlimited-tax GO, the strongest muni security class.
  - *Statutory lien:* Gov. Code §53515 (effective 1/1/2016) creates an automatic statutory lien on all tax revenues, "valid and binding from the time the bonds are executed and delivered … irrespective of whether those parties have notice" (OS "Statutory Lien on Ad Valorem Tax Revenues"). (The desk's "SB-222" shorthand refers to this §53515 statutory-lien regime — confirmed.)
  - *Tax status:* "interest on the Bonds is **excludable from gross income for federal income tax purposes and is exempt from State of California personal income taxes** … not an item of tax preference for purposes of the alternative minimum tax" (OS cover + Tax Matters). **Tax-exempt gate PASSED** (not a federally-taxable name — this matters because our after-tax selection actively harvests taxable munis).

- **New fact the screen did not carry:** the District is a **two-county** credit — Stanislaus (98.1% of AV) **and Merced (1.9%)**. Both counties run the Teeter Plan (see (e)). The screen labeled this a "Stanislaus" name; that is 98% right but the Merced sliver is real.

- **CUSIP binding (no fabrication):** The 3.0%/2042 maturity in the EMMA scale for issue ER390593 carries $1,875,000 principal and a 3.14% reoffering yield — uniquely identifying 900211CN1 as the district-wide GO (Election of 2016, Series 2019), **not** the separately-issued *School Facilities Improvement District No. 1* (SFID) bonds that share the Turlock USD name. This distinction matters: the SFID is a smaller, sub-district tax base. Our bond is the full-district pledge. **Correctly bound.**

---

### c. Tax base — AV, concentration, debt-to-AV (Item 2)

The ag/dairy-concentration concern is the right first-principles question for a Central Valley food-processing economy. **The data refutes a concentration problem.**

**Assessed valuation (District-wide, from OS; FY shown is fiscal-year-ended June 30):**

| FY | Total AV | YoY |
|---|---|---|
| 2010 | $5.83B | — |
| 2013 (GFC trough) | $5.34B | −1.8% (cumulative −8.4% off 2010) |
| 2016 | $6.59B | +8.2% |
| 2019 (OS) | **$8.04B** | +6.3% |

AV grew every year 2014→2019 after a mild GFC dip that bottomed at −8% (vs −20%+ for bubble-era Inland Empire districts). Prop-13 base-year assessment makes this base sticky on the downside. **Current AV (2024-25):** not pulled to primary (EMMA continuing-disclosure CDN was rate-limiting, 403 — see (g)); city/county sources and a flat-to-up CA Central Valley AV trend imply continued growth, but I am marking current AV **UNVERIFIED (not clean)** and relying on the 2019 base for the credit ratios below.

**Top-taxpayer concentration (OS "Largest Taxpayers," FY2018-19):**

- **No single taxpayer owns more than 1.90%** of secured AV.
- **Top 20 combined = 13.00%** of local secured AV ($979.3M of $7.53B).
- Top names: #1 Excel Monte Vista LP (shopping center) 1.90%; #2 Doctors Medical Center (medical) 1.17%; #3 Foster Poultry Farms 1.14%; #4 Blue Diamond Growers 1.13%; then a string of dairies/food processors (San Joaquin Valley Dairymen, Valley Milk, Mid Valley Dairy, Hilmar-adjacent processors) each 0.3–0.8%.

**Read:** the economy *is* ag/dairy/food-processing anchored — but it is **diversified within ag** (poultry, almonds, dairy, cold storage, dehydrated flavors) and topped by non-ag retail/medical. No single-employer or single-crop cliff. A 1.90% top name on an unlimited-tax GO is immaterial to debt service. **Concentration concern: not supported.**

**Debt-to-AV (OS "Direct and Overlapping Bonded Debt," 4/1/2019, ÷ FY2018-19 AV $8.04B):**

| Metric | Ratio |
|---|---|
| Direct GO debt ($52.9M) | **0.66%** |
| Total direct + overlapping tax/assessment debt | 1.19% |
| Combined total debt | 1.75% |

Sub-1% direct and sub-2% combined leverage is **low** for a CA school district. Remaining Prop-39 bonding capacity at issuance was ~$76.2M (gross capacity ~$179.8M) — ample headroom, no over-levered tell.

---

### d. AB-1200 certification & enrollment (Item 3)

- **AB-1200:** Screen says POSITIVE (Stanislaus County Office of Education monitoring). Our internal issuer-credit record carries `cert_status = "POSITIVE(absent)"` (credit_score 90) — i.e., **positive certification inferred, the explicit signed cert not pulled to primary.** Secondary confirmation: TUSD's 2024-25 Adopted Budget (Board 6/18/2024) and 2024-25 Unaudited Actuals (Board 9/16/2025) are on file with no published negative/qualified interim flag, and no AB-1200 stress event appears on the issuer's EMMA material-event history. **Finding: CONSISTENT with POSITIVE, but graded VERIFIED-via-secondary, not primary.** A negative or qualified certification would be the single most important operating tell for a school GO; none is on record. (This is a *coverage* note, not a red flag — "UNVERIFIABLE ≠ clean," but here it is consistent-with-clean.)
- **Enrollment:** OS P-2 ADA grew 12,996 → 13,458 (2012-13 → 2018-19), **stable-to-up**. Current district enrollment ~**13,769 (2025-26)** per CDE/district reporting — *higher* than the OS-era figure, so no enrollment-decline funding spiral (the main soft-credit risk for CA LCFF-funded districts). District serves ~14,000 TK-12, nine elementary + middle + high schools. **Finding: enrollment stable/growing — positive.**

---

### e. Call schedule & structure (Item 4)

- **Optional call:** Bonds maturing on/after 08/01/2027 are callable **on any date on or after 08/01/2026 at 100 (par), no premium**, from any source (OS Optional Redemption). The 2042 bond is therefore continuously callable at par from 08/01/2026.
- **Economic relevance: effectively zero call risk at current price.** A bond trading at **81.9** will not be optionally called at **100** — the issuer would be paying 100 to retire something the market values at 82. The MSRB **yield-to-worst (4.584%) = yield-to-maturity** here, because for a discount bond callable only at par, the worst case *is* holding to maturity. No yield-to-call haircut. This is the clean case where YTW and YTM coincide.
- **Teeter Plan (both counties):** Stanislaus **and** Merced have adopted the Teeter Plan (R&T §4701 et seq.). The District is credited **100% of its tax levy regardless of the in-district delinquency rate** — delinquency risk is transferred to the county Tax Loss Reserve Fund. This is a **material credit enhancement** and is the direct structural answer to the SGMA/ag-AV slow-decline concern (see (f)): even if ag parcels were to go delinquent, the District still receives full debt-service funding while Teeter is in force.

---

### f. Trade tape, SGMA ag-AV tail, and the de-minimis / TEY math (Items 5 & 6)

#### Trade tape — deep-discount-not-distress (Item 5)

196 trades over 2019→2026. Recent tape (sale-to-customer "S", purchase "P", inter-dealer "D"):

| Date | Type | Price | YTW |
|---|---|---|---|
| 2026-03-24 | S | 81.913 | 4.584 |
| 2026-03-18 | S | 83.073 | 4.469 |
| 2025-12-03 | S | 84.150 | 4.347 |
| 2025-09-12 | S | 81.143 | 4.621 |
| 2025-08-19 | S | 77.319 | 5.000 |
| 2024-08-19 | S | 88.360 | 3.908 |
| 2024-06-14 | S | 81.079 | 4.543 |

**Read: peer-range, rate-driven, two-sided — NOT distressed.**
- Price moves track the rate cycle (88 in mid-2024 when rates dipped → 75-77 in the Aug-2025 rate spike → back to ~82-84). Yields oscillate **3.9%–5.2%**, a normal AA-school-GO band for a 16-year discount bond; there is **no one-way markdown, no yield blowout to distressed double-digits, no gapping on stale prints.**
- Customers are *both* buying and selling at these levels (S and P prints throughout) — a liquid, contested mark, not a single dealer marking down an orphan position.
- The deepest print (75.5, Aug-2025, 5.19% YTW) coincides with the broad-market rate spike, not an idiosyncratic credit event — it round-tripped back to 84 by Dec-2025.

**Liquidity caveat (per our EMMA-tape execution-floor discipline):** prints are episodic (clusters every ~1-3 months), so this is an HTM ladder name, not a trade-it name. Bid/ask is a one-time buy-side cost of ~1-3 bps/yr amortized over a 16-year hold — immaterial to a hold-to-maturity thesis, but do not assume an IBKR scanner ask is acquirable at the touch.

#### SGMA ag-AV tail (Item 6) — milder than the screen flagged

- **Screen said:** "Stanislaus critically-overdrafted SJV basin." **Correction (primary DWR classification):** the **Turlock Subbasin (5-022.03) is DWR High-Priority, NOT critically-overdrafted.** (Critically-overdrafted SJV basins are names like Tule, Tulare Lake, Kaweah, Kern — not Turlock.)
- **GSP status:** submitted 1/2022 → DWR "incomplete" 1/2024 → revised resubmission 7/2024 → **GSP APPROVED by DWR on 2025-02-27.** The basin is on an approved, not probationary, path (contrast Tule, which went to a State Water Board probationary hearing in 2024). The GSP targets arresting chronic decline by 2027 and sustainable management by 2042.
- **Channel mechanism (why it barely touches this credit):** SGMA's credit channel is *pumping restrictions → reduced irrigated ag productivity → slow erosion of ag-parcel AV → smaller levy base*. For Turlock the channel is **heavily attenuated** by four facts: (1) ag is a *minority* of a diversified, retail/medical/processing-topped tax base (top ag name 1.14%); (2) Prop-13 base-year assessment means AV doesn't reprice down with land economics unless ownership changes; (3) the **Teeter Plan** means the District is paid its full levy even if individual ag parcels go delinquent; (4) the basin is on an *approved* GSP glide path, not probation/curtailment. **Net: SGMA is a slow, second-order, well-mitigated tail here — REVIEW-worthy to monitor, not a credit impairment.** Keep the flood tail (25%, REVIEW) and fire pocket (4% tail, low) on the same monitor list; none is currently load-bearing.

#### De-minimis math behind the after-tax TEY (the anchor)

This is the reason 900211CN1 is our de-minimis reference name. **Get the tax characterization right or the TEY is overstated.**

- **Market discount:** 100 − 81.86 = **18.14 points.**
- **IRS de-minimis threshold:** 0.25% × full years to maturity = 0.25 × 16 = **4.00 points** → de-minimis price floor = **96.00**.
- **18.14 ≫ 4.00**, and purchase price 81.86 is far below the 96.00 floor → **the bond FAILS the de-minimis safe harbor by a wide margin.**
- **Tax consequence:** the entire accreted market discount (pull from 81.86 to par) is taxed as **ORDINARY income** at sale/maturity — **not** tax-free, and **not** the lower long-term capital-gains rate. Only the **3% coupon** is tax-exempt (fed + CA).

**After-tax TEY, three framings (CA top bracket: fed 37% + NIIT 3.8% + CA 13.3% = 54.1% combined):**

| Framing | Treatment of pull-to-par | After-tax yield | TEY |
|---|---|---|---|
| A — naïve whole-yield-exempt (WRONG) | all tax-free | 4.58% | **~10.0%** |
| B — cap-gains on accretion (WRONG — fails de-minimis) | accretion @ 23.8% LTCG | 4.37% | ~9.5% |
| **C — CORRECT (ordinary-income accretion)** | accretion @ 54.1% ordinary | **~4.09%** | **~8.9%** |
| Reference — coupon-only (the clean exempt component) | ignore accretion | 3.66% | **~8.0%** |

**The desk's quoted ~8.3% TEY is conservative and defensible** — it sits between the coupon-only TEY (8.0%) and the correct full-bond TEY (8.9%), and is *well below* the inflated 9.5–10% an investor would wrongly book by treating the discount as tax-free or cap-gains. **The honesty catch the de-minimis math protects against is the ~150–200 bps of phantom TEY that the naïve treatment manufactures.** On a correct ordinary-income basis the bond still clears ~8–9% TEY — genuinely attractive — but the number must be quoted with the ordinary-income accretion drag disclosed, which the ~8.3% mark does.

*(Gross math reconciliation: my independent YTM solve = 4.71% at 81.86/settle 6/5; EMMA's MSRB YTW = 4.584% at 81.913/trade 3/24. The ~12 bps gap is settle-date and price-source, not a methodology error; EMMA YTW used as authority. Both agree YTW = YTM for this par-callable discount bond.)*

---

### g. Verification ledger & coverage gaps (honest failures)

| Item | Method / authority | Finding |
|---|---|---|
| Issuer / unlimited GO pledge | OS verbatim (raw/official_statement.pdf) | **VERIFIED** |
| Statutory lien (§53515 / "SB-222") | OS Statutory Lien section | **VERIFIED** |
| Tax-exempt, non-AMT | OS cover + Tax Matters | **VERIFIED** |
| CUSIP↔maturity binding (district GO, not SFID) | EMMA scale ER390593 (3%/2042/$1.875M) | **VERIFIED** |
| Coupon/maturity/dated/call | EMMA Security/Details | **VERIFIED** |
| AV base + top-20 concentration (13.0%, top 1.90%) | OS Largest Taxpayers / AV tables (FY2018-19) | **VERIFIED (as-of 2019)** |
| Debt-to-AV 0.66% direct / 1.75% combined | OS Direct & Overlapping (4/1/2019) | **VERIFIED (as-of 2019)** |
| Teeter Plan both counties | OS Tax Collections | **VERIFIED** |
| Trade tape peer-range, not distressed | EMMA 196-trade tape | **VERIFIED** |
| De-minimis fails → ordinary-income accretion | IRS rule recomputed from EMMA price | **VERIFIED (computed)** |
| SGMA: high-priority (not crit-overdrafted), GSP approved 2/27/2025 | DWR / Groundwater Exchange | **VERIFIED — screen flag was overstated** |
| Enrollment stable→13,769 (2025-26) | OS + CDE/district | **VERIFIED** |
| AB-1200 POSITIVE certification | internal record "POSITIVE(absent)" + no negative event on EMMA | **CONSISTENT — secondary, not primary cert** |
| **Current AV (FY2024-25)** | EMMA continuing-disclosure CDN 403 rate-limited | **UNVERIFIED (not clean) — refresh next session** |
| **Latest audited financials / fund balance** | same CDN limit | **UNVERIFIED — refresh** |

**Two real coverage gaps, both refreshable:** (1) current-year AV and (2) the latest annual continuing disclosure / audit were blocked by EMMA's document-CDN 403 rate limit (known gotcha). Neither is a red flag; both should be pulled on the next pass via the authenticated session with throttle/back-off. The credit ratios above rest on 2019 data; given AV grew into 2019 and CA Central Valley AV has trended up since, the 2019 ratios are conservative, but they are not *current*.

---

### h. Verdict

**BUY — HOLD-grade credit, deep-discount-not-distress CONFIRMED.**

This is the clean case the screen suggested it was: a genuinely sound unlimited-tax school GO trading at a deep *price* discount for purely mechanical (low-coupon-in-a-higher-rate-world) reasons, **not** credit reasons. The pledge is the strongest muni class (unlimited ad valorem + automatic statutory lien), leverage is low (0.66% direct debt-to-AV), the tax base is diversified within ag with no concentration cliff (top name 1.90%, top-20 13.0%), enrollment is growing, and the Teeter Plan in both counties structurally insulates debt service from the one tail (SGMA ag delinquency) that the asset class would otherwise expose. The trade tape is two-sided and peer-range, not a marked-down orphan.

The de-minimis correction is the value-add: the ~8.3% TEY is **honest** only because it implicitly carries the ordinary-income accretion drag — the naïve "tax-free pull-to-par" framing would manufacture ~150-200 bps of phantom yield. On the correct basis the bond still clears ~8–9% TEY for a CA top-bracket holder, with YTW = YTM (no call risk at 82). **Hold the position / accumulate on rate-driven weakness toward the high-70s.** Treat as an HTM ladder name (episodic liquidity). **Two open items before marking fully clean:** refresh current-year AV and the latest audit/continuing-disclosure from EMMA (CDN was rate-limiting today), and obtain the primary AB-1200 certification rather than the inferred positive.

---

### Documents (absolute paths)

- Report: `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/900211CN1/DD_REPORT.md`
- Official Statement (primary): `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/900211CN1/raw/official_statement.pdf`
- OS extracted text: `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/900211CN1/raw/os.txt`
- EMMA issue: ER390593 — https://emma.msrb.org/QuickSearch/Navigate?type=Issue&key=ER390593
- EMMA security: https://emma.msrb.org/Security/Details/900211CN1
- DWR SGMA basin (Turlock 5-022.03): https://groundwaterexchange.org/basin/san-joaquin-valley-turlock-5-022-03/

<!-- current-state-refresh -->
### Current-State Verification (AV / coverage refresh — 2026-06-20)

Refreshed 2026-06-20 via a SERIAL, throttled EMMA continuing-disclosure pull (the original UNVERIFIABLE flag was an EMMA 403 rate-limit from concurrent scraping, not a real disclosure gap). Latest issuer annual report: _Annual Financial Disclosures Posted 04/05/2026  for the year ended 06/30/2025 (1 MB)_. **Current total assessed valuation (levy base): $9,090,796,840 for FY2025-26 (+3.9% YoY)**; secured-tax delinquency **1.58%**; audited FY2025 on file. — AV trend 2024-25 $8.75B → 2025-26 $9.09B For an unlimited ad-valorem GO the AV base + the delinquency cushion ARE the 'coverage' — there is no DSCR; the levy rate floats to hold debt service constant. **This resolves the prior 'current AV/coverage UNVERIFIABLE' caveat.**
