# Charter Sector Validation Pass

**Pass type**: Shallow validation, ~60 min, 3 names
**Date**: 2026-05-28
**Operator**: Validation agent
**Purpose**: Confirm whether 3 "exclude"-flagged CA charter obligors (Today's Fresh Start, ICEF, Aveson) reflect real distress events, whether distress is priced into bonds, and whether the charter sector deserves deep validation. Hard-honest test of detector composition framework's first-pass scoping for charter sector.

---

## Per-name validation

### 1. Today's Fresh Start Charter School

**Framework flag reason** (per `data/charter_initial_detector_data/todays_fresh_start.json`):
7 detector fires — enrollment trajectory, charter_renewal_status, academic_performance_collapse, authorizer_relationship, lcff_funding_cut, going_concern_or_late_filing, financial_compliance_finding. Stated computed_outcome_class = "DETERIORATION_MULTIPLE_REVOCATIONS".

**Outcome verification — PRIMARY SOURCES**:

| Event | Date | Source |
|---|---|---|
| LA County BOE revoked charter | 2007 | [Today's Fresh Start v. LACOE](https://www.gmsr.com/wp-content/uploads/2016/06/S195852-AN-BOM.pdf) |
| State Board of Education-authorized Today's Fresh Start Charter — CLOSED | 6/30/2015 | [CDE School Directory CDS 19767370102020](https://www.cde.ca.gov/schooldirectory/details?cdscode=19767370102020) |
| LA County Board of Ed votes 7-0 to revoke Inglewood Today's Fresh Start | 1/8/2020 | [American School & University](https://www.asumag.com/facilities-management/article/21120018/la-county-school-board-votes-to-shut-down-charter-school-in-inglewood) |
| SBE denies renewal — operator history of related-party transactions, ambiguity, self-dealing | 7/9/2020 | [2 Urban Girls](https://2urbangirls.com/2020/04/state-department-of-education-should-move-forward-with-closing-todays-fresh-start-charter-school/) (LACOE/CDE-aligned reporting) |
| Inglewood Today's Fresh Start Charter School — CLOSED | 6/30/2020 | [CDE School Directory CDS 19646340119552](https://www.cde.ca.gov/schooldirectory/details?cdscode=19646340119552) |
| Inglewood USD appeal litigation | 5/26/2023 (Cal App) | [Today's Fresh Start v. Inglewood USD B314405](https://case-law.vlex.com/vid/today-s-fresh-start-932367419) |
| Self-dealing findings: Parkers' company received >$800k/yr rent from charter | LA Times investigation referenced in ASU article above | |

Outcome verified: **REAL DISTRESS** — operator effectively wound down at the obligor level via multiple authorizer revocations and SBE renewal denial. Closure confirmed in CDE database.

**Bond data**:
- Conduit issuer per universe.json: "CSCDA (historical) / private placement — VERIFY"
- EMMA search by obligor: **no observable trades found in this pass** (EMMA returned 403 to WebFetch; ICEF/Today's Fresh Start not surfaced in municipalbonds.com California issuer "T" or "I" listings reviewed). Universe.json itself flags "limited public detail" for the bonds. The bonds may be private placement (Ed Code 17199.4 intercept may not apply to private placement, and there are no SEC continuing-disclosure obligations on private-placement debt — so no EMMA material event filings to find).
- **Conclusion**: Operator-level distress is confirmed, but bond-level distress event is NOT directly verifiable from public sources. If the debt is private placement (as universe.json hypothesizes), the framework can't extract investable signal from this name regardless of operator outcome.

**Conduit structure**:
- Listed as CSCDA / private placement. CSCDA is a conduit without specific intercept structure (no LCFF intercept like CSFA). If bonds were privately placed, no rating, no continuing disclosure, no observable trade data.

**VERDICT**:
- Framework hit: **YES** (operator distress real and severe)
- Distress priced (Y/N/PARTIAL): **UNVERIFIABLE** (no observable trades; likely private placement)
- Alpha: **NONE** for public-muni framework — the bonds aren't analytically reachable. Useful only as a positive control / honesty calibration anchor.

---

### 2. ICEF Public Schools

**Framework flag reason** (per `data/charter_initial_detector_data/icef_public_schools.json`):
3 detector fires — enrollment_trajectory (-15% 5-yr), charter_renewal_status (claimed "View Park Prep Middle closed 2023"), lcff_funding_cut (enrollment-driven revenue compression). Computed_outcome_class = "UNVERIFIABLE — restructured 2011, stable since".

**Outcome verification — PRIMARY SOURCES**:

| Claim | Reality | Source |
|---|---|---|
| Universe.json EIN 95-4721536 | **WRONG** — correct EIN is **95-4548521** | [ProPublica Nonprofit Explorer](https://projects.propublica.org/nonprofits/organizations/954548521) |
| Framework claim: "View Park Prep Middle closed 2023" | **FALSE** — school is ACTIVE with 260 students FY24 | [CDE Directory CDS 19647336121081](https://www.cde.ca.gov/schooldirectory/details?cdscode=19647336121081); [CA School Dashboard 2023](https://www.caschooldashboard.org/reports/19647336121081/2023) |
| Framework claim: enrollment decline | Partly true at school level but ICEF aggregate REVENUE GROWING | ProPublica 990 data below |
| Going concern / audit qualified | No going-concern flag; "material weakness in internal controls" noted FY24 audit (per ProPublica summary) — worth tracking but not collapse-level | ProPublica |

**ICEF 990 financial trajectory FY20-FY24** ([ProPublica](https://projects.propublica.org/nonprofits/organizations/954548521)):

| FY | Revenue | Expenses | Net Income | Net Assets |
|---|---|---|---|---|
| 2020 | $29.3M | $34.1M | -$4.8M | $17.7M |
| 2021 | $41.8M | $34.2M | +$7.6M | $25.3M |
| 2022 | $43.4M | $42.3M | +$1.1M | $26.4M |
| 2023 | $51.3M | $50.2M | +$1.2M | $27.6M |
| 2024 | $55.8M | $53.2M | +$2.6M | $30.2M |

Revenue grew 90% FY20→FY24. Net assets grew 70% over same period. Four consecutive years of positive net income FY21-FY24. This is the financial profile of a RECOVERING / GROWING obligor, not a distressed one.

The 2011 near-collapse is real history (LA School Report archive corroborates Mike Piscal departure, Parker Hudnut restructuring). But that's 15 years stale.

**Bond data**:
- Conduit issuer: CSFA Series 2014 (View Park facilities — $22M tax-exempt confirmed via [PR Newswire 2013](https://www.prweb.com/releases/icef/vphs/prweb10963290.htm)) + CSFA Series 2019 refunding per universe.json (par ~$42M).
- EMMA returned no observable retail trades to WebFetch in this pass (EMMA gated 403; municipalbonds.com California issuer index doesn't show ICEF). Trade data likely exists on EMMA via direct CUSIP lookup — needs manual EMMA session.
- **Pricing estimate by comp**: ICEF is unrated or low-IG. CSFA's 2024 spread book ([CSFA 2024 Conduit Financing Program Report](https://www.treasurer.ca.gov/csfa/financings/conduit/2024.pdf)) shows:
  - BBB single-credit CSFA charter (Alliance College Ready, 10/24/2024): **91 bps** over 35-yr MMD AAA — "slimmest spread of a 2024 issuance"
  - BBB single-credit CSFA charter (Granada Hills, 8/20/2024): **110 bps** over 40-yr MMD AAA
  - BB+ single-credit CSFA charter (New Designs, 5/21/2024): **143 bps** over 40-yr MMD AAA
  - BB+ CSFA charter (Pacific Springs, 1/18/2024): **245 bps** over 30-yr MMD AAA
  - Unrated CSFA charters: 230-260 bps over MMD
- ICEF Series 2019 was rated BB+ at issuance per universe.json carry-forward. At ~143 bps over MMD 30yr (≈3.10% per scoping benchmark) → estimated current YTM ≈ **4.53%**, consistent with BB+ CA charter peer trading.

**Conduit structure**:
- **CSFA bonds — YES intercept**. Per Ed Code §17199.4 ([Justia codified](https://law.justia.com/codes/california/code-edc/title-1/division-1/part-10/chapter-18/section-17199-4/)), participating charter pledges intercept of state per-pupil apportionment; State Controller diverts to trustee on deficiency. This is real credit enhancement at the State Controller payment-mechanism level, but it is NOT a state guarantee (LISC explicitly excludes CA from its list of state debt-service guarantee programs — only CO/UT/TX/AZ/ID have those). The intercept gives operator-credit + state-payment-mechanism dual layer, which is why CSFA BBB charters trade ~90-145 bps over MMD vs unrated charters at 230+ bps.

**VERDICT**:
- Framework hit: **NO (false positive)** — enrollment soft at one school does not equal obligor distress. ICEF aggregate financials clearly recovering. The framework's flagship "School closure in window" claim is factually wrong (school still operating).
- Distress priced: **N/A** — there is no distress to price; current spread ~143 bps appears appropriate for a recovering BB+ obligator with intercept enhancement.
- Alpha: **NONE** — name would be a wrong "exclude" if added to a screen. ICEF should sit in clean basket, not exclude.

**Methodology bug surfaced**: detector data was apparently generated without verifying CDE closure dates and without pulling ProPublica 990 trajectory. This is the same class of error as the AHC entity-resolution problem in [feedback_dd_entity_resolution.md] — the detector was looking at one symptom in isolation (per-school enrollment decline) without rolling up to the obligor.

---

### 3. Aveson Charter Schools

**Framework flag reason** (per `data/charter_initial_detector_data/aveson_charter_schools.json`):
4 detector fires — enrollment_trajectory (-39% 5-yr), charter_renewal_status ("Pasadena USD denied 2022; LA COE upheld 2023"), authorizer_relationship (active conflict resolved adversely), lcff_funding_cut. Universe.json `_historical_default_or_distress_references` block claims "Charter renewal denial at Pasadena USD 2022; partial appeal outcome at LA COE; revocation of School of Creative Leadership 2023".

**Outcome verification — PRIMARY SOURCES**:

| Claim | Reality | Source |
|---|---|---|
| Aveson School of Leaders closed | **FALSE** — ACTIVE, K-5 PUSD-authorized, 334 students FY23-24 | [CDE Directory CDS 19648810113472](https://www.cde.ca.gov/schooldirectory/details?cdscode=19648810113472) (page updated 2/17/2026) |
| Aveson Global Leadership Academy closed | **FALSE** — ACTIVE, 6-12 PUSD-authorized | [CDE Directory CDS 19648810113464](https://www.cde.ca.gov/schooldirectory/details?cdscode=19648810113464) (page updated 2/17/2026) |
| Pasadena USD 2022 renewal denial | **NOT CORROBORATED** in this pass — search returned only 2012 Patch article about PUSD imposing conditions on Aveson renewal; LACOE March 2025 "District-Denied Charter Renewals on Appeal" guide listed but not parseable for Aveson specifically | [LACOE District-Denied Renewals on Appeal PDF](https://lacoe.edu/content/dam/lacoeedu/documents/generalcounsel/charter-school-office/District%20Charter%20Renewal%20on%20Appeal%20Guide.pdf); [Patch 2012](https://patch.com/california/altadena/etc) |
| "School of Creative Leadership" revocation 2023 | **NO PUBLIC CORROBORATION** — Aveson currently markets only 2 schools (School of Leaders TK-5, Global Leadership Academy 6-12). May be misnaming of a discontinued earlier program | Aveson site shows current 2-school footprint at [aveson.org](https://www.aveson.org/) |
| Enrollment decline | Real but smaller in magnitude than framework claims | See 990 data below |

**Aveson 990 financial trajectory FY22-FY24** ([ProPublica EIN 20-2937518](https://projects.propublica.org/nonprofits/organizations/202937518)):

| FY | Revenue | Expenses | Net Income | Net Assets |
|---|---|---|---|---|
| 2022 | $10.84M | $9.55M | +$1.29M | $2.80M |
| 2023 | $12.09M | $10.82M | +$1.27M | $4.07M |
| 2024 | $9.45M | $11.30M | **-$1.85M** | **$2.22M** |

Note: **Universe.json EIN 26-2144528 is WRONG** — correct EIN per ProPublica is **20-2937518**.

FY24 shows real financial deterioration — revenue dropped 22% YoY, net income flipped to large loss, net assets fell 45% in one year. This IS distress, though late-stage rather than the "renewal denial 2022" narrative the framework asserts.

**Bond data**:
- Universe.json: "Possibly CSCDA / PCSD lease structure — VERIFY". The detector data file itself flags: "most facilities are PCSD-leased not direct-issued".
- This means Aveson likely has **NO direct conduit revenue bonds** outstanding — its facility exposure is in PCSD's lease-backed deals. PCSD is the issuer; investor credit exposure is to the multi-asset PCSD portfolio, not to Aveson specifically. No Aveson Schedule K shown on the most recent 990 per ProPublica preview.
- **EMMA**: no Aveson-obligor bonds to search; PCSD-issued deals are facility-credit, not operator-credit.

**Conduit structure**:
- If PCSD-leased: investor is in a facility-credit pool, not direct operator exposure. Operator-level distress affects the cash flow into PCSD's debt service but doesn't translate 1:1 to single-CUSIP price action.

**VERDICT**:
- Framework hit: **PARTIAL** — there IS real financial deterioration in FY24 (loss of $1.85M, net assets down 45%), but the framework's stated triggering event (Pasadena USD 2022 renewal denial + 2023 LACOE revocation of School of Creative Leadership) is **not corroborated by public sources** and may be hallucinated detail. The true distress signal (steep FY24 revenue/net-assets decline) was not what the detector fires referenced.
- Distress priced: **N/A** — Aveson likely has no direct conduit bonds. PCSD pool exposure is the actual instrument and isn't analyzable as a single-obligor short.
- Alpha: **UNVERIFIABLE** — even if Aveson's financial distress is real, there's no direct-issued bond to trade on it.

---

## Sector-level verdict

### Confirmed framework hits: **1 of 3**
- **Today's Fresh Start**: real operator distress confirmed (closures, SBE denial, related-party-transaction findings)
- **ICEF**: false positive — financials clearly recovering, claimed school closure didn't happen
- **Aveson**: partial — real FY24 financial deterioration, but stated triggering events not corroborated

### Distress NOT priced into bonds: **0 of 3 actionable**
- Today's Fresh Start: not actionable (private placement / no public bonds)
- ICEF: no distress to price; trading consistent with peer
- Aveson: no direct conduit bonds (PCSD lease structure)

### Overall: **KILL ON THIS NARROW THESIS / NEEDS-MORE-DATA ON THE BROADER UNIVERSE**

The three "exclude" candidates do NOT produce actionable charter-muni short or avoid signals because:
1. The most distressed name (Today's Fresh Start) is private-placement / non-analyzable
2. The two analyzable names (ICEF, Aveson) either (a) aren't actually distressed (ICEF) or (b) don't have direct conduit bonds tradeable on their operator credit (Aveson)
3. The detector data files contain at least 3 factual errors (View Park Prep "closed" — wrong; Aveson schools "closed" — wrong; two wrong EINs)

**The framework's first-pass scoping for charter sector is not yet at the quality level reached on hospital + NH muni**. Before this sector deserves deep validation work:
- detector data must be regenerated with CDE closure-date verification as a hard precondition
- EINs must be cross-checked against ProPublica before any per-obligor pull
- the analyzable bond universe must be filtered to CSFA-issued obligor-credit (not PCSD facility, not CSCDA private placement)

**Recommendation: NEEDS-MORE-DATA. Do not invest agent hours deep-validating this sector until the 3 known data-quality issues are fixed. The "honesty-alpha" hurdle is harder here than in hospitals because operator-level distress is decoupled from analyzable bond credit by (a) facility-credit structures (PCSD), (b) State Controller intercept (CSFA Ed Code 17199.4), and (c) private-placement opacity for the worst names.**

---

## Methodology gaps surfaced

1. **EMMA is gated to WebFetch (403)**. Cannot pull trade-level data, CUSIPs, official statements, or material event notices in agent context. Workarounds:
   - municipalbonds.com (works, partial coverage)
   - CSFA's own annual conduit financing reports (pricing benchmarks only — works, used here)
   - ProPublica Schedule K (issuance par confirmation — works for some obligors)
   - **Fix needed**: a scraping module that uses full Chrome fingerprint per [feedback_scraping_browser_fingerprint.md] to access EMMA's IssuerHomePage and TradeData endpoints.

2. **CDE closure-date verification was not done in detector_data generation**. View Park Prep Middle and both Aveson schools were marked as closed in detector data but CDE shows them ACTIVE. This is the same class of error as the SRPT "comprehensive scores overfit" issue — composite scores aggregated false sub-signals.
   - **Fix**: regenerate `charter_initial_detector_data/*.json` with a hard precondition: `closed_in_window` boolean must be set ONLY from CDE School Directory (`Active` vs `Closed` field + `Closed Date`).

3. **EIN errors**: ICEF detector_data has 95-4721536, actual 95-4548521. Aveson detector_data has 26-2144528, actual 20-2937518. Universe.json `_ein_caveat` explicitly admits this risk ("SEVERAL EINs ARE LIKELY WRONG").
   - **Fix**: ProPublica EIN verification mandatory before any 990 / Schedule K pull.

4. **PCSD-lease-backed bonds vs operator-credit bonds are conflated** in universe.json. PCSD is a multi-asset facility lessor, not an operator obligor. Investors in PCSD bonds get a pool of lease payments, not single-charter exposure.
   - **Fix**: tag every obligor in universe.json with `direct_conduit_issuer` vs `pcsd_lease_pool` vs `pooled_jpa` so screening can filter to direct-obligor exposure only.

5. **Charter "distress" doesn't map cleanly to bond pricing** because of:
   - **State Controller LCFF intercept** (Ed Code 17199.4) — operator distress doesn't break debt service unless apportionment itself stops; this is closer to "moral certainty of payment" than to a pure operator-credit. Charter analog to Cal-Mortgage on the NH side. CSFA BBB charters trade ~90-145 bps; CSFA BB+ at 143-245 bps; **the spread compression evidence in 2024 was strongest for the most "honest" CSFA-issued, intercept-protected, multi-school operators**.
   - **Private placement** opacity for the worst names (e.g., Today's Fresh Start) — the distress that the framework correctly detects can't be traded.
   - **Facility-pool** structures (PCSD) — operator-level signal doesn't translate 1:1 to bond price.

6. **Honesty-alpha framing is harder here than in NH/hospital**: the question "did the framework re-detect already-disclosed bad news?" cuts even sharper in charter because most operator distress (rating actions, audit findings, FCMAT reviews) is disclosed via authorizer board minutes that ARE the official record — there's almost no "private information" to extract.

7. **No actionable single-obligor charter short found in this pass**. If charter sector is to be in the framework, it likely belongs as an **exclusion screen on highly-positively-correlated risk factors** (single-authorizer concentration, nonclassroom-based status, founder-CEO concentration, FCMAT review in last 24 months) applied to the CSFA-issued obligor-credit subset only, not as an alpha-generation pillar.

---

## Files referenced

- `/Users/ajay/exalted/signalos/verticals/muni_credit/data/charter_universe.json`
- `/Users/ajay/exalted/signalos/verticals/muni_credit/data/charter_initial_detector_data/todays_fresh_start.json`
- `/Users/ajay/exalted/signalos/verticals/muni_credit/data/charter_initial_detector_data/icef_public_schools.json`
- `/Users/ajay/exalted/signalos/verticals/muni_credit/data/charter_initial_detector_data/aveson_charter_schools.json`

## Primary sources cited (consolidated)

- CDE School Directory: Today's Fresh Start Charter (closed 6/30/2015), Today's Fresh Start Inglewood (closed 6/30/2020), ICEF View Park Prep Middle (active 260 students), Aveson School of Leaders (active 334 students FY24), Aveson Global Leadership Academy (active)
- ASU article on LACOE 1/8/2020 Inglewood vote
- LACOE Closed Authorized Charter Schools PDF (July 2025 revision)
- ProPublica Nonprofit Explorer: ICEF EIN 95-4548521; Aveson EIN 20-2937518
- CSFA 2024 Conduit Financing Program Report (PDF — pricing benchmarks)
- LISC Charter School Bond Study (CA not in state-enhancement-program tier)
- EFF/Equitable Facilities Fund 2022 Charter School Bond Sector Default Study (CA had 7 defaults through 2022)
- California Education Code §17199.4 (State Controller intercept mechanism)
- Cal App Today's Fresh Start v. Inglewood USD B314405 (2023)
