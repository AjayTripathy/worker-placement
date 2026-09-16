# Diligence Report — CUSIP 587619BF3

**Merced Irrigation District — Water and Hydroelectric System Refunding Revenue Bonds, Series 2014A**
4.00% coupon · Term due 2038-10-01 · uninsured · net-revenue pledge (2008 Installment Purchase Agreement)
Cutoff: 2026-06-20 · Analyst desk: SignalOS muni_credit

---

## (a) Verdict, thesis, and resolved issuer

**Verdict: HOLD (clean senior net-revenue pledge with solid recent coverage, but hydrology-driven coverage
volatility + a FERC relicensing overhang on the core asset keep it off BUY).**

**Resolved issuer (CONFIRMED from on-file OS).** Obligor is the **Merced Irrigation District (MID) Water and
Hydroelectric System** — the District's combined irrigation-water and Merced River hydroelectric enterprise.
The specific security is the **Series 2014A** (tax-exempt) tranche of the Water and Hydroelectric System
Refunding Revenue Bonds; **CUSIP 587619BF3 = the $7,920,000 4.00% Term Bond due 2038-10-01** (OS inside cover).
**Taxable-gate check: this is the 2014A TAX-EXEMPT tranche, NOT the companion 2014B (Taxable) tranche** — verified
from the OS cover and maturity schedule. Bonds issued under the 2008 Installment Purchase Agreement / 2014
Indenture — a true net-revenue installment-sale pledge, not a COP/lease/special tax.

**Thesis.** Senior net-revenue lien on the Water & Hydroelectric System, ~3.22x coverage cited (most recent
~2.69x in the OS table), 120% rate covenant, uninsured. The HOLD drivers: (1) **coverage is hydrology-volatile**
— the OS coverage history swings **1.78x → 6.63x** across water years because hydroelectric generation and
irrigation deliveries depend on Merced River snowmelt; and (2) the Merced River Hydroelectric Project (New
Exchequer Dam / Lake McClure) was, at issuance, operating under a **one-year FERC license** — relicensing/
operating-condition risk on the asset that generates a chunk of pledged revenue.

**Note on the cache parse artifact:** the cached `current_dscr` of **22.12x is a PARSE ARTIFACT** and is
disregarded. The verified anchor is the OS coverage table: most-recent ~2.69x, range 1.78x–6.63x, headline 3.22x.

---

## (b) Security — the revenue pledge

| Claim | How verified | Source / authority | Finding |
|---|---|---|---|
| Senior net-revenue pledge (Water & Hydroelectric System) | Read OS security clause | OS cover + Indenture of Trust (8/1/2014) | **VERIFIED.** Net-revenue pledge of the Water & Hydroelectric System under the 2008 Installment Purchase Agreement; single senior coverage line in the historical table. |
| 587619BF3 is the tax-EXEMPT 2014A tranche | Read OS inside cover + maturity schedule | OS lines: "$7,920,000 4.00% Term Bonds due Oct 1, 2038 … CUSIP 587619BF3" under "SERIES 2014A"; tax opinion §"2014A excluded from gross income" | **VERIFIED.** 587619BF3 = 2014A = tax-exempt. The 2014B Taxable tranche is a different CUSIP. |
| Lien vs 2014B | Read flow-of-funds | OS p.~454/484 | **VERIFIED.** Revenues applied to the (subordinate) 2014B after senior obligations; certain Hydroelectric/Energy System obligations rank ahead of 2014B. 2014A is the senior tax-exempt piece. |
| Insurance | Read cover | OS cover | **NONE (uninsured).** |

---

## (c) System and customers (concentration test)

- **System type:** **Irrigation-water + hydroelectric** enterprise — an agricultural irrigation district (water
  delivered to growers) combined with the Merced River Hydroelectric Project. This is a different customer model
  than a retail municipal water utility: the "customers" are largely **agricultural irrigation users**, plus the
  hydroelectric output (sold wholesale).
- **Concentration:** the OS does not isolate a single dominant water/irrigation customer share (cache null).
  Irrigation deliveries are spread across many growers within the District; hydroelectric revenue is a wholesale
  generation stream. **The concentration risk here is sector/commodity (ag water-year + power price), not a single
  named offtaker.**

---

## (d) DSCR / rate covenant / WATER SUPPLY / Prop 218

### Debt-service coverage (DSCR)
From the OS coverage table (layout-preserved read), across the presented years:

| Metric | Value |
|---|---|
| Coverage range across the table | **1.78x – 6.63x** |
| Most recent year in table | **~2.69x** |
| Headline cited (cache / OS senior line) | **3.22x** |
| Basis | Senior-lien coverage under 2008 Installment Purchase Agreement; no RSF transfer in the historical table (organic) |

- The **volatility is the story**: coverage tracks the water year (snowmelt → hydro generation + irrigation
  deliveries). The 1.78x trough is a dry-year reading; the 6.63x peak is a wet-year reading. The bond clears the
  covenant in the years shown, but a multi-year drought sequence is the stress case.
- **DISREGARD cache `current_dscr` 22.12x — confirmed parse artifact.** Anchor on the OS table (~2.69x recent,
  1.78x dry-year floor).

### Rate covenant
- **120% rate covenant** (cache `rate_covenant` 1.2): the District covenants to set rates/charges yielding Net
  Revenues ≥ 120% of Debt Service. Self-tightening above a 1.0x floor.

### WATER SUPPLY (load-bearing — lead here)
- **Source: Merced River, Sierra-local (SNOWMELT-fed).** The District owns and operates **New Exchequer Dam (Lake
  McClure, ~1,024,600 acre-feet storage)** and McSwain Dam, comprising the **Merced River Hydroelectric Project**.
  Supply is **Sierra Nevada snowmelt impounded on the Merced River**, conveyed via canals to growers; the District
  also pumps groundwater from 220 well sites within its boundaries.
- **The risk (genuine, but a DIFFERENT risk than the import-fed names):**
  - **Hydrology / drought:** Lake McClure inflow is snowmelt-dependent. Dry years cut both hydroelectric
    generation revenue AND irrigation deliveries — the source of the coverage swing. This is the load-bearing
    supply risk. (Note: the cache tagged supply "low" on an "no-Colorado-River" keyword basis — correctly, MID
    has **no Colorado River / SWP import dependence** — but the cache understated the **water-year/hydrology
    volatility**, which is the real supply risk here.)
  - **FERC relicensing:** at issuance the Merced River Hydroelectric Project was operating under a **one-year
    FERC license** pending relicensing. New license conditions (instream-flow / fishery requirements on the
    Merced River) could constrain operations and revenue. **Overhang to confirm current status before sizing.**
  - Mariposa County water-rights settlement and senior water-rights obligations are disclosed.
- **Mitigant:** large owned reservoir storage (Lake McClure ~1.0 MAF buffers single dry years), senior water
  rights, 120% rate covenant, and **no exposure to the Colorado/SWP import-allocation channel** that drives the
  other water names in this sleeve.

### Prop 218
- Irrigation-water charges follow the District's rate-setting process (Prop 218/26 framework). Standard friction.

---

## (e) Liquidity

- **EMMA trade tape (live, throttled, 2026-06-20):** **79 trades / 365 days** (the most-traded of the Merced
  names), 22 in last 90 days, last print 11 days ago, **7 two-sided days**, median block ~$25k, **~6 bps two-sided
  yield spread**. Adequate liquidity; ~6 bps round-trip cost in an HTM ladder. No flag.

---

## (f) Tax status and yield

- **Tax status: tax-exempt (verified — 2014A tranche).** OS: interest on the **2014A Bonds excluded from federal
  gross income** and (with the 2014 Bonds) **exempt from California personal income tax**. 4.000% round coupon.
  **The taxable 2014B tranche is a different CUSIP — gate cleared: 587619BF3 is double-exempt.**
- **Yield / TEY:** cached clean price ~100.0, after-tax-equivalent yield ~**8.06%** (CA gross-up of gross YTM, not
  net-of-fee). Issuance price was 97.873 / 4.14% on this term bond; confirm current YTW before executing.

---

## (g) Risks (lead with supply, then concentration/structure)

1. **WATER SUPPLY — hydrology/drought (primary):** Merced River snowmelt drives both irrigation deliveries and
   hydroelectric generation; dry years cut revenue and produce the 1.78x coverage trough. **No** Colorado/SWP
   import-allocation exposure (relative strength), but water-year volatility is the load-bearing risk.
2. **FERC relicensing overhang:** Merced River Hydroelectric Project on a one-year license at issuance —
   relicensing/instream-flow conditions could constrain operations. **Confirm current license status.**
3. **Coverage volatility:** 1.78x–6.63x range; ~2.69x recent. Clears covenant in years shown but cyclical.
   *(Cache 22.12x current DSCR is a parse artifact — disregarded.)*
4. **Structure:** uninsured; senior 2014A lien (ahead of taxable 2014B). 120% rate covenant. Sector concentration
   (ag water + power), not single-customer.
5. **Honesty assessment: CLEAN.** Supply, hydrology, FERC and the senior/subordinate structure are fully
   disclosed; takeaway does not diverge from OS data. Nothing to exclude. HOLD on genuine hydrology/relicensing
   grounds.

---

## (h) Sources

- **EMMA Official Statement — Merced Irrigation District Water and Hydroelectric System Refunding Revenue Bonds,
  Series 2014A / 2014B (Taxable).** On-file:
  `/Users/ajay/exalted/signalos/verticals/muni_credit/data/_water_os/587619BF3.txt` (+`.layout.txt`);
  PDF: https://emma.msrb.org/EA632082-ER620013-ER1021761.pdf
  - Sections relied on: cover + inside cover (2014A vs 2014B; 587619BF3 = $7.92M 4.00% Term 2038; tax opinion);
    Indenture / 2008 Installment Purchase Agreement (net-revenue pledge, flow of funds, 2014B subordination);
    coverage table (1.78x–6.63x, ~2.69x recent, 3.22x); "District Water Supply and Water Rights" + New Exchequer/
    Lake McClure / Merced River Hydroelectric Project / one-year FERC license; Mariposa water-rights settlement.
- **EMMA trade tape (live, 2026-06-20):** 79/yr, 7 two-sided days, ~6 bps spread (`liquidity_gate`).
- **Issuer-litigation screen (2026-06-20):** federal (RECAP) + FCMAT clean; SEC municipal-disclosure web search
  returned no enforcement action against Merced Irrigation District.
- **SignalOS stores:** `data/water_revenue_cache.json` (DSCR 3.22x; supply "low" — **note the cached current_dscr
  22.12x is a confirmed parse artifact, disregarded**).

*Prepared by SignalOS muni_credit desk. Verified ≠ guessed.*
