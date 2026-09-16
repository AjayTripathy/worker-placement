# Diligence Report — CUSIP 050002AW4

**Prepared:** 2026-06-20 (cutoff = today)
**Analyst layer:** SignalOS / muni_credit
**Status of bond in book:** Tagged in DILIGENCE_MASTER (`in_book: true`), flagged for verification due to a pledge/cert data conflict.

---

## VERDICT (read this first)

**REJECT for new purchase at ~100.89 (premium). Reclassify, do not buy more; existing lot is a HOLD-to-call at best.**

- **TRUE security (resolved): City of Atwater (Merced County) WASTEWATER REVENUE Refunding Bonds, Series 2017A, 5.000% Term Bond due 5/1/2040.** This is a **municipal utility-revenue bond**, NOT a school general-obligation bond. The "school" signal in our master was a **field artifact**, not a real security feature (see Section a).
- **Call finding — this is a near-par-call trap.** The bond is **continuously callable at PAR (no premium) on any date on or after 5/1/2027** (≈10.5 months away). At our 100.888 price the **yield-to-worst is 3.94% gross (~7.9% TEY) to the 2027 par call**, not the 4.91%/~9.9% the 14-year maturity would imply. A buyer at a premium **forfeits the 0.89-pt premium against ~10 months of carry if called.** The OS itself prices this CUSIP "to call" (114.060%**(C)**, 3.290% yield-to-call at issue).
- **Pledge correctly = revenue (water/wastewater).** It is a **special, limited obligation** — explicitly **NOT** full-faith-and-credit, **NO** tax pledge, **NO** unlimited ad-valorem. So the SB-222 / §53515 GO-lien protection, AB-1200 school-cert framework, and "unlimited ad-valorem" language do **not** apply and were never the right lens.

**3-sentence summary:** CUSIP 050002AW4 resolves unambiguously, from its own official statement, to a City of Atwater wastewater **revenue** bond (5.000% term, due 5/1/2040, base CUSIP 050002), so the master's `pledge=water` was right and the `cert_status=POSITIVE(absent)` "school" tell was a defaulted AB-1200 field that should never have populated on a city utility credit. The decisive economic finding is the **premium-plus-par-call structure**: at 100.89 the bond yields only ~3.94% gross / ~7.9% TEY to a par call available continuously from 5/1/2027, so the marketed ~8% TEY is a sub-1-year bridge yield, not a locked 14-year coupon, and any further premium paid is at risk of being called away. Credit is adequate but unexciting (AGM-insured to "AA", BBB- underlying, 1.46x net-revenue coverage, 24.6% top-10 customer concentration anchored by a single wholesale district) — none of which is the catch; **the catch is buying a callable premium bond as if it were a long GO.**

---

## a. Pledge / Security Resolution — THE DATA CONFLICT

**The conflict in our master:**
- `pledge = "water"`, `security = "essential-service water/wastewater revenue"`, `system_type=combined`, `dscr=1.46` (a REVENUE profile), **but**
- `cert_status = "POSITIVE(absent)"` — an **AB-1200 school-district** financial-certification field that only has meaning for a K-12 LEA, **and** the master `issuer="Atwater Elementary"`.

These contradict: a city wastewater revenue bond has no AB-1200 cert, and a school GO has no wastewater DSCR.

**How resolved (primary source):**
1. Pulled the official statement EMMA had bound to this CUSIP (`raw/official_statement.pdf`, EMMA doc `ER1077935-ER843996-ER1244777.pdf`).
2. Cover page reads: **"$56,600,000 CITY OF ATWATER WASTEWATER REVENUE REFUNDING BONDS, SERIES 2017A,"** dated 8/30/2017, **Base CUSIP: 050002**, Nossaman LLP bond counsel.
3. Located our exact CUSIP in the OS maturity schedule:
   > **"$8,945,000 5.000% Term Bonds Due May 1, 2040; Price - 114.060%(C); Yield - 3.290%; CUSIP - AW4"**
   050002 + AW4 = **050002AW4**. Coupon 5.000% and maturity 5/1/2040 match our master **exactly**.

**Finding — VERIFIED, with a resolved artifact:**
- The TRUE issuer is the **City of Atwater** (a municipal corporation), not Atwater Elementary School District. The two share the name "Atwater," which is what mis-seeded `issuer="Atwater Elementary"` in the master. The **CUSIP6 050002 belongs to the City** (confirmed on the OS cover), so the security itself was correctly priced/marked.
- **`pledge=water` is CORRECT.** The OS: *"The obligation of the City to make Debt Service Payments is a special obligation of the City, payable solely from and secured by Gross Revenues … of the City's wastewater collection, treatment and disposal system."* It expressly states the bonds are **NOT** a full-faith-and-credit pledge, the City **shall not levy or pledge any form of taxation**, and they are **not secured by a lien on physical assets.**
- **`cert_status = POSITIVE(absent)` is the ARTIFACT.** The AB-1200 county-cert pipeline ran against a city-utility obligor where no school certification exists, defaulted to "absent," and that "absent-school-negative-cert" rendered as a misleading POSITIVE(absent). **It is not evidence of a school GO.** Treat it as N/A for this CUSIP.
- **Revenue lens is the correct lens** (applied in Sections b–d). The school lens (UNLIMITED ad-valorem GO, SB-222/§53515 lien, AB-1200 Merced cert, enrollment) does **NOT apply** and is dropped.
- **Tax status:** Tax-EXEMPT. Nossaman opinion: interest excludable from federal gross income (not an AMT preference item) and **exempt from California personal income tax.** Passes the taxable-muni gate — TEY gross-up is legitimate.

**Net: the master's economic tags are right; its issuer label and school-cert field are wrong and must be corrected to "City of Atwater — wastewater revenue."**

---

## b. The System, Revenue, Coverage & Concentration (Revenue Lens)

**Obligor / system:** City of Atwater wastewater collection, treatment & disposal system ("Wastewater System"). Special limited obligation secured by Gross Revenues; parity-debt structure (refunds the 2008/2010/2011 prior obligations).

**Debt service coverage (OS Table, cash basis, City of Atwater source):**
- Parity obligation coverage on **GROSS** revenues: 2.03x → 2.30x across the historical window.
- Parity obligation coverage on **NET** revenues: 1.32x–1.34x historically, **1.46x** most recent year — this is the `dscr=1.46` in our master. VERIFIED to the OS coverage table.
- **Rate covenant:** 1.20x (net). 1.46x actual gives ~26% headroom over covenant — adequate but not robust; a modest revenue shock or large-customer loss compresses it toward covenant.

**Customer concentration (OS Table 4, FY2016-17):**
- **Top-10 wastewater customers = 24.63% of system revenues.** VERIFIED to OS verbatim. Falls in our REVIEW band (15–25%).
- **#1 customer = Winton Sanitary District, $1,153,809** — a **wholesale inter-agency** customer (one neighboring district buys treatment capacity). Single-counterparty wholesale exposure is the meaningful tail here: loss/renegotiation of the Winton contract is the scenario that moves DSCR, analogous to the Tulare wholesale-customer lesson. Mitigant: Winton is itself a public agency with its own ratepayer base, not a private industrial taker, so default-then-disappear risk is lower than a single corporate plant.

**Rate-setting:** Subject to **CA Prop 218** majority-protest. Mitigant per OS: City adopted a **multi-year rate schedule**, reducing the need for fresh 218 votes to hit covenant.

---

## c. Credit Wrap & Ratings

- **Insured: S&P "AA"** via **Assured Guaranty Municipal Corp. (AGM)** municipal-bond insurance policy (issued concurrently with the bonds; DSRF insurance policy also purchased).
- **Underlying: S&P "BBB-"** at issuance (2017).
- **Wrap-compression read (KG mechanism):** AGM on a **BBB- underlying** is exactly the band where wrap value is largest (AGM compression curve ~0 / ~140 / ~360 bps at AA- / BBB- / CCC-). The "AA" you see in the tape is insurance-driven; the **standalone credit is low-investment-grade**. **However**, at the current ~0.9y duration-to-worst the wrap is largely economically inert — principal returns at par inside a year, so the insurance only matters in the (low) tail of a default-before-the-2027-call. **Do not pay up for the "AA" line; you are effectively buying a short BBB- bridge with a par cap.**
- **No post-issuance rating action found** that changes this read as of cutoff; trade tape continued to mark near par (EMMA continuing-disclosure/material-event endpoints were rate-limited (403) at cutoff — flagged as a coverage caveat, not a clean).

---

## d. PREMIUM PRICE & CALL RISK — the decisive structural check

**Why it matters:** A 5.000% coupon trading at **100.888 (a ~+0.89 pt premium)** is unusual for our (mostly-discount) book. On a premium bond, the call schedule, not the maturity, sets the realized yield.

**Call schedule (OS "Redemption of the Bonds," VERIFIED verbatim):**
- *"The Bonds maturing on or after May 1, 2028, are subject to redemption … on any date on or after May 1, 2027, at a redemption price equal to the principal amount … without premium."*
- → **Optional call: continuously callable at PAR (100), no call premium, from 5/1/2027 onward.**
- Mandatory sinking fund on the 2040 term begins 5/1/2038 (also at par) — secondary; the 2027 optional par call is the binding worst case.

**Independent bond math (our engine, settle 2026-06-20, price 100.888):**

| Measure | Value |
|---|---|
| Yield to **maturity** (5/1/2040) | **4.910%** |
| Yield to **first par call** (5/1/2027) | **3.939%**  ← yield-to-WORST |
| Modified duration **to worst** | **~0.84** |
| Years to par call | **0.86** |
| TEY-to-worst (× 2.01 CA top bracket) | **~7.92%** |

- Our master's `ytw = 3.972%` and `tey_aftertax = 7.98%` tie out to our independent **3.939% YTC / 7.92% TEY** within ~3 bps (settle/rounding). **So the marketed "~8.0% TEY" is the yield-to-CALL, and is internally consistent — it is NOT a 14-year lock.** This is the one thing the master got right and the framing must preserve: the 8% is a **sub-1-year bridge yield.**
- **Trap mechanics:** Buy at 100.888 → if called 5/1/2027 at 100, you book a **−0.89 pt capital loss** against ~10 months of 5% carry, netting the 3.94% YTW. Any incremental premium paid above ~100 is **pure call-away risk** with no upside (you cannot earn the 4.91% maturity yield unless the City chooses NOT to call — and with a BBB-/AGM credit refinancing into a lower-coupon deal, the City is **incentivized to call** a 5% coupon).
- **Master correction needed:** `call_risk` is currently **`UNVERIFIABLE`** with `next_call_date: null`. **Resolved:** call_risk = **HIGH / near-par-call**, next_call_date = **2027-05-01**, call_price = **100**, years_to_call ≈ **0.86**.

**This is the catch.** Takeaway-vs-data divergence: the book's framing ("8% TEY, 2040 maturity, AA-insulated, AI-99") reads like a long, safe, high-yield hold. The data says it is a **10-month, premium-dollar, par-capped revenue bridge on a BBB- underlying** — fine to *hold to the call* if already owned at/near par, **wrong to BUY at a premium** as a yield-book anchor.

---

## e. Trade Tape / Liquidity

- Desk authoritative ingest (as-of 2026-06-20): last px **100.888**, EMMA reported YTW **3.972%**, **65 trades** trailing 365d, **5 two-sided days/yr**, quoted px-spread **~0.011 pt**, max observed block **$1.25M**.
- Liquidity gate: **THIN.** 5 two-sided days/yr means ~once-every-10-weeks two-way printing; acquisition at the scanner mark is not guaranteed and exit before the call is dealer-dependent. For a ~0.9y-to-call bond this is tolerable as a **hold**, but the thinness plus the call cap removes any "trade the premium" exit thesis.
- **Caveat (honest):** Live IBKR returned **no quotable contract** for this CUSIP (close-only muni feed, expected), and EMMA's per-CUSIP RTRS trade endpoint was **rate-limited (403)** at cutoff. The mark therefore rests on the desk ingest, not a fresh independent tape pull. Treated as a coverage caveat — **not** a clean verification of today's bid.

---

## f. AI-Crash Insulation / Hazard Screens (revenue-credit lens)

- **AI-crash insulation: HIGH (master 99–100).** Correct *mechanism-wise*: this is a **local wastewater-rate** credit, not a state-GF cap-gains-income-tax credit, so the dot-com / AI-crash state-revenue channel does **not** transmit to debt service. Ratepayer billings are non-cyclical. **The AI-99 tag is genuinely benign here** — but note it measures the wrong risk for this bond; the binding risk is the call, not AI.
- **Fire:** Master shows a contradiction — top-line `fire_score=82.9` / `fire_worst_tract="Relatively High"` yet `fire_tail=0.048` (5%) and `hazard_tier=LOW`. For a **wastewater utility in the City of Atwater (valley floor, urbanized)**, the wildfire AV-levy-erosion channel is largely irrelevant (revenue is rate-based, not ad-valorem). Treat fire as **LOW/immaterial** for this credit; the high tract score is a join artifact of a non-applicable (school-AV) overlay.
- **Seismic:** Ss 0.70, Central Valley / Sierra (low). Low and correct.
- **SGMA / ag tail:** Merced County sits in the **critically-overdrafted San Joaquin Valley** groundwater region, but note the OS's own supply read for THIS system: *"no Colorado-River or critically-overdrafted-basin dependency detected"* for the wastewater system, and `supply_risk=low`. **Wastewater** (sewage treatment) is far less SGMA-exposed than a **water-supply** utility — SGMA pumping cuts hit drinking-water supply and ag AV, not sewage volumes, which track population/connections. So the **SGMA ag tail is a second-order indirect risk** here (regional ag contraction → slower household/connection growth → softer rate base over years), **not** a direct supply constraint. Real but slow; does not threaten near-term coverage or the sub-1-year hold horizon.

---

## g. Tax / Yield Summary

- **Tax-exempt** (federal + CA personal), VERIFIED (Nossaman). TEY gross-up legitimate.
- **Yield-to-worst 3.94% gross → ~7.92% TEY** (CA top bracket ×2.01) — to the **5/1/2027 par call.**
- Yield-to-maturity 4.91% gross / ~9.87% TEY — **only realized if the City declines to call**, which is the unfavorable assumption to underwrite on a callable 5% premium bond with a refinanceable BBB-/AGM credit.
- **Specify the metric:** the "~8% TEY" is **TEY-to-worst (to-call)**, not gross YTM and not net-of-fees. Quoting it as an 8%-to-2040 hold would overstate the locked yield ~1 pp.

---

## h. Conclusion, Master Corrections & Recommendation

**Security resolution:** CUSIP 050002AW4 = **City of Atwater, Wastewater Revenue Refunding Bonds, Series 2017A, 5.000% term due 5/1/2040, AGM-insured (S&P AA) / BBB- underlying, tax-exempt, base CUSIP 050002.** A **REVENUE** bond. Pledge=water CORRECT; school-cert tell is an ARTIFACT.

**Verdict: REJECT new purchase at the ~100.89 premium. Existing position: HOLD-to-call only.**
- The honesty-alpha catch is **structural framing, not undisclosed bad news**: the OS fully discloses the par call (it even prices the bond "to call"), so the bond is honestly disclosed — but our **book's marketed takeaway diverged from the bond's own data** (long high-yield insulated hold vs. 10-month premium par-capped bridge). Grade = ELEVATE on takeaway-divergence.
- Credit (1.46x net coverage, 24.6% top-10 with a single wholesale district, BBB- underlying behind an AGM wrap) is **adequate but unremarkable** and is *not* why we reject — we reject because **paying a premium for a continuously-callable 5% coupon caps upside at ~3.94% YTW while leaving full downside.**

**Required DILIGENCE_MASTER corrections (apply before any trade):**
1. `issuer`: "Atwater Elementary" → **"City of Atwater (wastewater revenue)"**
2. `cert_status`: "POSITIVE(absent)" → **"N/A (not a school GO — AB-1200 field artifact)"**
3. `call_risk`: "UNVERIFIABLE" → **"HIGH / near-par-call"**; `next_call_date`: null → **"2027-05-01"**; `call_price`: null → **100**; `years_to_call`: null → **~0.86**
4. Carry-forward note: report "~8% TEY" explicitly as **TEY-to-worst (to 2027 par call)**, never as a 2040 yield.
5. Flag fire/SGMA tags as **non-applicable overlay artifacts** for a revenue-utility credit (revenue is rate-based, not ad-valorem).

**Documents (all absolute paths):**
- Official statement (primary source, City of Atwater WW Rev 2017A): `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/050002AW4/raw/official_statement.pdf`
- This report: `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/050002AW4/DD_REPORT.md`
