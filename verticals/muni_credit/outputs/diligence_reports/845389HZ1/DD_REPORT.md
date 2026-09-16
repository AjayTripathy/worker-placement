# Diligence Report — CUSIP 845389HZ1

**Bond:** Southwestern Community College District (San Diego County, CA), Election of 2016 General Obligation Bonds, **Series A**, 4.00% coupon, due 2039-08-01.
**Cutoff:** 2026-06-20 | **Analyst layer:** SignalOS muni_credit | **Verdict:** **BUY**
**Accreditation status (lead finding):** Southwestern College — **ACCREDITED, no sanctions** (ACCJC, reaffirmed June 15, 2023).

---

## Three-sentence summary

Southwestern Community College District is an unlimited-ad-valorem GO of a large, deeply diversified South Bay San Diego suburban tax base (FY2017-18 AV $53.5B, top-20 taxpayers only 6.20%, direct debt 0.59% of AV), rated Aa2/AA- and reaffirmed Aa2 by Moody's as recently as 2025, with the bonds secured by a SB-222 / Government Code §53515 statutory lien on the county tax levy — a security that does not depend on the college's operations or any single campus. The matcher's CC-UNKNOWN flag is resolved: the obligor's college, **Southwestern College (Chula Vista)**, holds **full ACCJC accreditation with no warning, probation, or show-cause sanction** (reaffirmed 2023, next comprehensive review 2028, accredited continuously since the college opened), so the accreditation-enrollment-revenue channel that can threaten a college's *operating* finances is benign here — and, critically, it would not reach GO bondholders anyway because repayment is the county property-tax levy, not college tuition. Seismic (Rose Canyon), fire, and flood appear in the official statement only as generic AV-impairment risk factors with no district-specific concentration, and the unlimited tax pledge insulates principal/interest from any localized physical loss.

**Verdict: BUY.** Aa2/AA- unlimited GO, accreditation clean, base diversified, leverage low, priced near par (~99.84) for an after-tax TEY near 8% on a CA-double-exempt bond.

---

## a. Issuer & instrument identity — RESOLVED (CC-UNKNOWN cleared)

| Item | Finding | How verified | Authority |
|---|---|---|---|
| Issuer | Southwestern Community College District (San Diego County, CA) | EMMA description search returned the issuer; OS cover confirms | EMMA / Official Statement |
| Specific issue | **Election of 2016 GO Bonds, Series A** ($400M authorization) | The only 4.00%/2039 maturity carrying security_desc "ELECTION 2016-SER A" across all SWCCD issues; matches FIGI "S WSTRN CMNTY CLG-**A**" (Series A) | EMMA scale (issue ES381952) + OS |
| Maturity / coupon | 2039-08-01, 4.00% | EMMA maturity scale + IBKR contract record (conid 295491624) | EMMA / IBKR |
| College (matcher subject) | **Southwestern College, Chula Vista** — system "Southwestern CCD" | ACCJC institution roster + college site | ACCJC / swccd.edu |

**Note on binding rigor:** EMMA encrypts the plaintext 9-char CUSIP in its scale JSON (CGS license), and the OS maturity-schedule CUSIP column is not text-extractable (image/columnar). The Series-A binding therefore rests on the convergence of three independent identifiers — FIGI "-A", the unique 4.00%/2039 "ELECTION 2016-SER A" scale line, and the IBKR conid/ISIN US845389HZ19 — rather than a single decrypted CUSIP string. Confidence: HIGH. The CUSIP base 845389 is Southwestern CCD; the obligor is not in doubt, and every other 4.00%/2039 SWCCD maturity (Ser B-2, Ser F, Ser E-2, Ref Ser B) is a *different series* than the FIGI's "-A".

---

## b. Accreditation resolution — LEAD FINDING (VERIFIED CLEAN)

**Claim to resolve:** matcher returned cert = CC-UNKNOWN; confirm the college and its ACCJC standing.

| Channel | Finding | Source / authority |
|---|---|---|
| College identity | Southwestern College, Chula Vista; system "Southwestern CCD" | ACCJC REST API roster (`/wp-json/wp/v2/institutions`), as_of 2026-06-19 |
| Current status | **Accredited** (no Warning / Probation / Show-Cause) | ACCJC institution record + ACCJC REST API |
| Last comprehensive review | 2021 (Statement of Reaffirmation issued **June 15, 2023**) | ACCJC + college accreditation page |
| Next comprehensive review | 2028 (2022–2028 cycle) | ACCJC / swccd.edu |
| Sanction history | None indicated; "accredited status since it opened in 1961" | swccd.edu accreditation page |
| Most recent action | Midterm action letter dated Feb 3, 2026 (routine cycle item; no sanction) | swccd.edu |

**Finding: VERIFIED — full accreditation, no active sanction.** Cross-checked across three authorities (ACCJC institution page, ACCJC REST API, and the college's own accreditation site) that agree. CC-UNKNOWN is cleared to **CC-ACCREDITED-CLEAN**.

**Why this matters (and its limit):** ACCJC sanctions are the fastest leading indicator of a community college's *operating* distress (enrollment/Title-IV/tuition channel). Here the signal is clean. But note the masking-vs-insulation point: even a *bad* accreditation outcome would not directly impair these bonds, because debt service is the county's unlimited ad-valorem property-tax levy on the district's entire tax base — not college tuition or general-fund revenue. Accreditation is a genuine credit positive for the institution and removes a tail-risk headline, but the GO security sits one layer above it.

---

## c. Pledge & security — VERIFIED (unlimited GO + statutory lien, double tax-exempt)

From the Series A Official Statement (`raw/official_statement.pdf`), verbatim findings:

- **Unlimited ad-valorem GO:** "The Bonds are general obligations of the District, payable solely from the proceeds of ad valorem property taxes ... levied ... upon all property within the District ... **without limitation as to rate or amount** (except for certain personal property taxable at limited rates)." The San Diego County Board of Supervisors is "empowered and obligated to annually levy" the tax. → Same security class as a K-12 California GO. **VERIFIED.**
- **SB-222 / statutory lien:** "Pursuant to State Government Code **Section 53515**, the Bonds will be secured by a statutory lien on all revenues received pursuant to the levy and collection of ad valorem property taxes." → The pledge the user flagged. **VERIFIED.**
- **Tax status:** Bond Counsel opinion — interest "excluded from gross income for federal income tax purposes" and "exempt from State of California personal income tax." → **Double tax-exempt; not a federally-taxable series** (the SWCCD complex *does* contain federally-taxable refundings — 2020/2021 taxable series — but this 4.00% Series A is the tax-exempt line). Passes the taxable-muni gate. **VERIFIED.**
- **General-fund non-recourse:** "The District's general fund is not a source for the repayment of the Bonds." → Bondholders are insulated from college operating finances. **VERIFIED.**

---

## d. Tax base — VERIFIED (diversified suburban base, low leverage)

From the OS "Tax Base for Repayment of Bonds" (FY2017-18 basis):

- **Assessed valuation:** **$53,469,167,268** total (local secured $51.55B). Multi-year table shows recovery and growth through the cycle.
- **Taxpayer concentration:** **Top-20 taxpayers = 6.20% of AV; top-1 = 1.35%** (BSK Del Partners LLC, a hotel). The list is hotels / shopping centers / apartments / light industrial — no single dominant employer or single-sector exposure. This is a genuinely diversified base, consistent with the user's "diversified suburban" thesis.
- **Direct & overlapping debt (10/1/2017):**
  - Direct debt $314.0M = **0.59% of AV**
  - Total direct + overlapping tax & assessment debt = **2.38% of AV**
  - Combined total debt (incl. general-fund & tax-increment) = **3.81% of AV**
- **Currency caveat:** This OS is the 2017 Series A. Under CA Prop 13, AV grows ~2%/yr plus reassessment, so the current base is materially larger and the 2017 debt ratios are conservative (stale-high). A secondary source cites FY2024-25 district AV of ~$82.0B (**UNVERIFIED** — single secondary source, not cross-checked to a current OS table); I do not rely on it for the verdict. Even at the verified 2017 $53.5B, leverage is low.
- **New authorization:** Voters passed **Measure SW ($800M)** in Nov 2024; the district has begun issuing (Election of 2024 Series 2025A, $120M tranche). This adds *future* GO leverage, but against an $53B+ (and growing) base the incremental debt-to-AV remains modest, and the marketed tax impact (~$25 per $100k AV) is small. Watch item, not a credit concern.

---

## e. Seismic / fire / flood — RESOLVED from OS (partial → cleared)

- The OS discloses earthquake, fire, drought, toxic contamination, and flooding **only as generic risk factors** that "could cause a reduction in the assessed value of taxable property within the District." There is **no district-specific Rose Canyon fault disclosure, no special flood/inundation zone, and no fire-concentration disclosure.**
- **Rose Canyon context:** The Rose Canyon Fault Zone runs through coastal San Diego and is the region's principal active strike-slip system; South Bay (Chula Vista/National City/San Ysidro) sits in a moderate-shaking corridor. This is a real physical hazard to *campuses and to the broad AV base*, but two structural facts contain the bond risk:
  1. **The pledge is unlimited and base-wide.** A localized loss reduces some parcels' AV; the County re-levies the (uncapped) rate across all remaining property to make debt service whole. A single damaged campus does not impair bondholders — the college's own buildings are not the security.
  2. **Diversification.** No single taxpayer is >1.35% of AV, so no single-site catastrophe materially dents the levy base.
- **Finding:** anti-masking / insulation positive. The "partial" fire/flood/EQ screen resolves to **LOW bondholder risk** for a GO of this structure. (For a *revenue* bond or a single-asset land-secured deal the same fault would score far higher; the GO structure is what neutralizes it.)

---

## f. Trade tape & liquidity — PARTIAL / UNVERIFIABLE (flagged honestly)

- **IBKR live snapshot (conid 295491624, pulled 2026-06-20):** no two-sided market returned (bid/ask empty, bond_yield 0/0). Consistent with our standing finding that the IBKR muni feed is **close-only** for this name. Last available **close = 99.844**, YTM ≈ 4.02% (our priced record).
- **EMMA RTRS tape:** could not be retrieved this session — the EMMA per-CUSIP `var tradeData` block did not return (the disclaimer-cookie flow that the scraper depends on did not populate; likely an EMMA UI change). **Recent-print count, last-trade date, and two-sided-day frequency are UNVERIFIABLE as of this run** — explicitly *not* "clean." Treat as a liquidity gap to confirm before sizing.
- **Liquidity stance:** For a buy-and-hold-to-call/maturity HTM ladder position, thin secondary prints are a one-time entry cost (a few bps), not a credit issue. But per our liquidity-gate discipline, confirm at least intermittent two-sided prints on EMMA before adding size; do not assume the IBKR scanner ask is acquirable.

---

## g. Call schedule & yield/tax — VERIFIED

- **Optional redemption:** Bonds maturing on/after **Aug 1, 2028 are callable at par (100%) on any date on/after Aug 1, 2027**; bonds maturing on/before Aug 1, 2027 are non-callable. Our 2039 bond is therefore **callable at par from 2027-08-01**.
- **Yield-to-worst:** Priced near par (~99.844, slight discount to par), so YTW ≈ yield-to-call-at-par ≈ yield-to-maturity (~4.02% gross). The discount-to-par means the call is not deeply in the money; call risk to the buyer is modest. (EMMA reports trade yields as yield-to-**worst** YX, MSRB convention — do not mislabel as YTM.)
- **After-tax TEY:** Double tax-exempt (federal + CA). At the CA top bracket (~2.01x gross-up factor used in our framework), ~4.0% gross → **~8% TEY**, matching the desk figure. TEY is the gross-up of the gross YTM; net-of-fees and execution (see liquidity note) would shave this modestly.

---

## h. Verdict & mechanism

**BUY.**

Rationale: this is a structurally insulated, well-diversified, low-leverage **Aa2/AA- unlimited GO** of a California community college district. The two things that could have made it a trap are both cleared:
1. **Accreditation** — Southwestern College is fully accredited with no ACCJC sanction (reaffirmed 2023), so there is no operating-distress headline; and even if there were, GO bondholders are paid from the county tax levy, not college revenue.
2. **Physical hazard (Rose Canyon / fire / flood)** — disclosed only as generic AV risk, neutralized by the unlimited, base-wide tax pledge and a base where no taxpayer exceeds 1.35% of AV.

**Microstructure encoding (why this is the right call, not just "looks fine"):** The honesty-alpha question is *takeaway-vs-data divergence* — there is none here. The OS markets exactly what the data supports (unlimited GO, diversified base, low leverage), and the one thing the matcher flagged as unknown (accreditation) verifies clean against three independent authorities. The masking channel that *would* matter for a community college (accreditation/enrollment → general-fund stress) is severed from the security by the GO structure, so even a future accreditation deterioration is a slow, well-telegraphed, off-pledge event — long signal-to-price latency and no recourse to these bonds. This is a **CLEAN** name in the framework sense: honestly disclosed, structurally insulated, no liar to exclude.

**Watch items (do not change the verdict):** (i) confirm EMMA secondary prints before sizing — tape was UNVERIFIABLE this run; (ii) current-year AV and the post-Measure-SW ($800M new authorization) debt-to-AV are on a stale-but-conservative 2017 basis — refresh from the next continuing-disclosure / 2025A OS AV table; (iii) callable at par from 2027 — modest, since priced near par.

---

## Documents (all absolute paths)

- `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/845389HZ1/raw/official_statement.pdf` — Election of 2016 GO Bonds, Series A Official Statement (the binding OS for this CUSIP; source of pledge, AV, taxpayer, debt, call, tax-status findings)
- `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/845389HZ1/raw/measure_sw_2025A_pos.pdf` — Election of 2024 (Measure SW) Series 2025A board/POS document (Aa2 reaffirmation, new authorization context)
- `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/845389HZ1/raw/_cand_*.pdf` — candidate-series OS PDFs pulled during CUSIP/series binding (audit trail)
- ACCJC institution record: https://accjc.org/institution/southwestern-college/ (status: Accredited)
- District accreditation page: https://www.swccd.edu/about-swc/accreditation/index.aspx (reaffirmed 2023, 2022–2028 cycle)
- EMMA security page: https://emma.msrb.org/Security/Details/845389HZ1

*Sources of record:* EMMA Official Statement (primary); ACCJC institution record + REST API + college site (accreditation); Moody's Aa2 / S&P AA- (ratings, via issuer disclosure, 2025); IBKR conid 295491624 (instrument/price). UNVERIFIABLE items flagged inline: EMMA secondary trade tape; current-year (post-2017) AV.

<!-- current-state-refresh -->
### Current-State Verification (AV / coverage refresh — 2026-06-20)

Refreshed 2026-06-20 via a SERIAL, throttled EMMA continuing-disclosure pull (the original UNVERIFIABLE flag was an EMMA 403 rate-limit from concurrent scraping, not a real disclosure gap). Latest issuer annual report: _Annual Financial Disclosures Posted 03/01/2026  for the year ended 06/30/2025 (2.3 MB)_. **Current total assessed valuation (levy base): $87,047,120,705 for FY2025-26 (+6.1% YoY)**; audited FY2025 on file. — AV trend 2022-23 $71.97B → 2023-24 $77.27B → 2024-25 $82.03B → 2025-26 $87.05B For an unlimited ad-valorem GO the AV base + the delinquency cushion ARE the 'coverage' — there is no DSCR; the levy rate floats to hold debt service constant. **This resolves the prior 'current AV/coverage UNVERIFIABLE' caveat.**
