# Diligence Report — CUSIP 925836KH0

**Victor Elementary School District (San Bernardino County, California), Election of 2008 General Obligation Bonds, Series C**
4.00% coupon · maturity 08/01/2044 · callable 08/01/2028 @ 100

Cutoff: 2026-06-18 · Prepared for: intended purchase, ~$40,000 par

---

## (a) Verdict, thesis, and issuer resolution

**Verdict: CLEAR TO BUY.** This is a clean, plain-vanilla California school general obligation bond with a strong pledge, a moderate-to-low debt burden, an investment-grade rating, current and unblemished financial disclosure, and adequate two-way liquidity for a $40k lot.

**Thesis.** You are buying an unlimited-tax claim on a large ($7B+ assessed value), growing San Bernardino County property-tax base, secured by an automatic statutory first lien on the tax revenues. The District self-certifies it can meet its obligations (AB-1200 POSITIVE), its most recent audit is clean with healthy reserves, and there is no sign of credit distress anywhere in the public record. At 4.12% gross yield-to-worst (≈8.28% taxable-equivalent for a top-bracket California resident, double tax-exempt) the bond compensates fairly for a moderate-duration (≈12.6) high-grade hold-to-maturity position.

**Issuer-resolution finding (VERIFIED — the fuzzy match was correct).**
The CDE fuzzy match "Victor Elementary" is **confirmed correct** against the primary source. The EMMA security header and the cover page of the Final Official Statement (`raw/official_statement.pdf`, p.1) both read:

> "VICTOR ELEMENTARY SCHOOL DISTRICT (San Bernardino County, California), Election of 2008 General Obligation Bonds, Series C, Current Interest Bonds"

The true issuer is the **Victor Elementary School District (VESD)**, a K-8 district formed in 1896 serving a 44-square-mile area that includes all of the City of Victorville. It is **NOT** the City of Victorville and **NOT** the Victor Valley Union High School District. Those two are *separate, distinct issuers* whose boundaries *overlap* VESD — the OS direct-and-overlapping-debt table lists "Victor Valley Union High School District" as a 56.462%-applicable **overlapping** entity, i.e. a different obligor sharing the same Victorville tax base. The sister CUSIP6 prefix 926055 that also fuzzy-matched "Victor" is therefore almost certainly one of those *other* Victor-family issuers (Victor Valley UHSD or Victor Valley Community College District), not this bond's issuer.

**Because the match was correct, no screen re-run was required** — the AB-1200 certification, seismic, and wildfire screens were all attributed to the right district (Victor Elementary SD).

---

## (b) Security and pledge

| Item | Finding | Source |
|---|---|---|
| Pledge | **Unlimited ad-valorem general obligation.** San Bernardino County is obligated to annually levy property taxes on all taxable property in the District *without limitation as to rate or amount* to pay debt service. | `official_statement.pdf` cover + "THE BONDS — Security and Sources of Payment" |
| Statutory lien | **VERIFIED.** Under California Government Code Section 53515 (the "SB-222" statutory-lien regime), the bonds carry a statutory lien on the ad-valorem tax revenues that attaches automatically, is valid and binding from delivery, and is enforceable against the District and its creditors. | `official_statement.pdf`, "Statutory Lien" |
| Tax status | **VERIFIED double tax-exempt.** Bond counsel opines interest is excluded from federal gross income and is **not** an AMT preference item, and is exempt from California personal income tax. | `official_statement.pdf`, "TAX MATTERS" |
| Insured? | **No** — uninsured; the Aa3 is the District's own underlying rating, not a wrap. | EMMA security details ("Insured: No") |
| Rating | **Moody's Aa3** at issuance. No subsequent rating-change notice on EMMA (i.e., no downgrade flagged through cutoff). | `official_statement.pdf`, "Rating" + EMMA event-notice scan |
| Call | First optional call 08/01/2028 @ 100. At today's discount price (98.475) the call is out-of-the-money, so the 2044 maturity is the worst case and yield-to-worst equals yield-to-maturity. | `emma_security_details.html` + analytics recompute |

One honest caveat on the lien: the OS states the Section 53515 statutory lien secures these bonds *and* all other parity GO bonds of the District, and "does not specify the relative priority… or a method of allocation" among them. In practice this is standard for CA GO and not a concern given the moderate debt load, but it is a shared (not exclusively senior) lien.

---

## (c) Issuer and tax base (resolved district)

**Victor Elementary School District** — K-8, formed 1896, San Bernardino County (High Desert / Victorville).

**Operations (from the FYE 6/30/2025 audited disclosure, `continuing_disclosure_fye2025.pdf`):**
- 16 district schools + 2 charter schools.
- Enrollment 11,864 (October 2024), projected stable for 2025-26.
- **Audit opinion: Unmodified ("clean").** Financials "present fairly in all material respects." No going-concern doubt (the only "going concern" mentions in the document are the auditor's standard responsibility boilerplate, not a doubt being raised).
- **General Fund available reserves = 8.1% of total outgo** — well above the ~3% state-recommended minimum for a district of this size.
- Combined governmental fund balances ≈ **$249.6M** at 6/30/2025.

**Tax base / assessed valuation (AV):**
- AV at issuance (2018-19): **$7,059,417,149.** The OS shows AV growing from ~$5.34B (2011-12 trough) to $7.06B (2018-19) — roughly +5%/yr in the years before issuance, recovering well past the pre-financial-crisis peak.
- District (direct) GO debt was **0.71% of AV**; total direct + overlapping tax/assessment debt **2.57%**; combined total debt (incl. overlapping general-fund and tax-increment debt) **5.22%**. These are **moderate-to-low** burdens for a California school district.
- Tax collection mechanics: San Bernardino County operates the **Teeter Plan** for the 1% general levy (county advances the District 100% of its levy regardless of delinquencies). See the Teeter caveat in Risks below.

**AB-1200 fiscal certification: POSITIVE.** The District self-certifies under AB-1200 that it can meet its financial obligations for the current and two subsequent fiscal years. This is corroborated independently by the clean FYE2025 audit and the 8.1% reserve level.

---

## (d) Three screens

**AI-crash insulation: 99 / 100 (fully insulated).** This is a *local property-tax* GO, repaid by an ad-valorem levy on Victorville-area real property. It does **not** depend on the California General Fund or on the state's capital-gains-driven income-tax revenue, which is the channel through which an AI/tech-equity crash would hit state-aid-dependent credits. School *operating* aid flows partly from the state, but *bond debt service* is funded by the dedicated property-tax levy, which is insulated from the AI/cap-gains channel. No concern.

**Wildfire: 8% high-fire tail (LOW-MODERATE — below review threshold).** FEMA National Risk Index census-tract wildfire data crossed to the District's tracts shows roughly **8.5% of the District's footprint in the "Relatively High" fire band**, worst-tract "Relatively High." This is **below the 15% high-fire-share threshold** at which we flag a name for fire review, so it does **not** trigger a fire concern. The mechanism to watch (not active here): a major fire event plus insurer withdrawal can erode the AV levy base — but at <9% exposure on a $7B base this is immaterial to debt-service coverage. The OS itself discloses natural-disaster (incl. wildfire) AV-reduction risk in standard boilerplate; nothing district-specific elevates it.

**Earthquake: Ss 1.42 (MODERATE-HIGH, Inland Empire — zone-diversified).** The District sits in the Inland Empire near the southern San Andreas / San Jacinto systems, with a USGS ASCE7-22 short-period spectral acceleration Ss ≈ 1.42 — genuinely a moderate-to-high seismic-hazard location. This matters for a GO because a damaging quake can destroy taxable improvements and depress AV. Two mitigants: (1) the levy is *unlimited*, so a tax-base shock raises the rate rather than impairing the pledge; (2) within our muni book this name provides **seismic zone diversification** rather than concentration — it is a single Inland Empire position, not part of a fire-or-quake-concentrated cluster, consistent with the cap-aggregate-not-per-zone discipline. Net: a real physical risk, adequately compensated and structurally buffered by the unlimited pledge.

---

## (e) Liquidity and execution

Recomputed directly from the EMMA trade tape (`emma_trade_tape.json`, 423 prints since 2019-05-15):

| Metric (trailing 365 days) | Value |
|---|---|
| Trades | **79** (matches the screen) |
| Distinct trading days | 31 |
| Two-sided days (dealer buy *and* sell) | **14** (the screen recorded 7; recompute is more favorable) |
| Trade-type mix | 43 dealer→customer sales · 17 customer→dealer · 19 inter-dealer |
| Median trade size | $30,000 |
| ≥$100k blocks / <$25k odd-lots | 13 / 29 |
| 12-month YTW range | 3.35% – 4.92% (last 4.12%) |
| 12-month price range | 88.75 – 101.53 (last 98.475) |
| Most recent print | 2026-06-03, dealer→customer, 98.475 / 4.12% YTW, $15k |

**Execution read:** liquidity is adequate-to-good for a $40k lot. The target size is below the median trade and far below the 13 block prints seen this year, and there are 14 genuine two-sided days, so acquisition should not require crossing a wide one-sided market. The screen's recorded limit price of ~100.22 sits above the last traded 98.475; bid around the recent customer-sale level (≈98.3–98.6) rather than chasing. Note for a hold-to-maturity ladder, bid/ask is a one-time entry cost, not a recurring drag.

**IBKR live quote: UNAVAILABLE.** IBKR returned no contract for this CUSIP (typical for an illiquid muni), so there is no live bid/ask. The EMMA trade tape (last print 2026-06-03) is the execution authority here; treat marks as close-only.

---

## (f) Tax and yield

- **Gross yield-to-worst: 4.12%** (last customer sale, 2026-06-03). Independently recomputed at **4.1198%** from coupon/price/dates — within 0.0002 pp of EMMA's figure (inside our ±0.003 tolerance). YTW = YTM here because the bond trades at a discount and the 2028 call is out-of-the-money.
- **Modified duration ≈ 12.6** (to maturity 2044) — meaningful rate sensitivity; this is a long bond.
- **Taxable-equivalent yield ≈ 8.28%.** This is the *gross* YTW grossed up by the ≈2.01 California top-bracket double-exempt factor (federal + CA exempt, no AMT add-back). **Be precise about the metric:** 8.28% is a gross TEY, **not** net-of-fees and **not** a forward total return; the comparable pre-tax taxable yield is ~8.28%, the actual coupon cash yield is 4.0% on a 98.475 cost.

---

## (g) Risks (honest)

1. **Long duration (~12.6).** A clean credit, but a 2044 maturity carries real mark-to-market rate risk. Appropriate as a hold-to-maturity tax-exempt income position; less so if you may need to sell mid-life into a higher-rate regime. Credit quality ≠ price stability.
2. **Teeter applicability to the GO levy — UNVERIFIABLE.** San Bernardino County runs the Teeter Plan for the 1% general levy, but the OS is explicit that whether the County *also* applies Teeter to the *GO debt-service* levy is at County option and not guaranteed. If it does not, the District bears delinquency timing risk on the bond levy. Not a default risk (the unlimited levy self-corrects via rate), but a cash-flow-timing caveat we could not close from the documents at hand.
3. **Seismic (Ss 1.42).** Genuine Inland Empire earthquake hazard; a severe event could damage the taxable base. Buffered by the unlimited pledge (rate rises to cover) and by holding this as a single diversifying zone rather than a concentrated cluster.
4. **Shared statutory lien.** The Section 53515 lien secures these bonds and any parity GO bonds without a stated priority/allocation method. Standard for CA GO and benign at this debt level, but not an exclusively senior claim.
5. **Concentration / High-Desert economy.** Victorville is a High-Desert community with historically below-average wealth metrics; an AV downturn would raise the levy rate on a less-affluent base. The 0.71% direct-debt ratio leaves ample headroom, and AV has grown steadily, so this is a watch-item, not a current concern.
6. **Rating staleness.** Aa3 is the at-issuance (2019) Moody's rating; no rating-change notice has been filed since, which we read as "no downgrade," but we did not pull a fresh 2026 rating affirmation. UNVERIFIABLE that the rating is currently still Aa3 — though the clean FYE2025 audit is strongly corroborative.

**No findings of distress.** EMMA shows zero event notices across every distress category (payment delinquency, default, rating change, bankruptcy, failure-to-file, unscheduled draws). The most recent annual disclosure (FYE 6/30/2025) was filed on time (02/25/2026) with a clean unmodified audit. This is a CLEAN credit in the honesty sense: there is no gap between how the issuer presents itself and what its own documents and tape show.

---

## (h) Sources and attached documents

All saved under `outputs/diligence_reports/925836KH0/raw/`:

- **`official_statement.pdf`** — EMMA Final Official Statement (MSRB doc ES1271382-ES995059-ES1396492, 1.6 MB). Primary authority for issuer identity, pledge, statutory lien, tax status, AV history, direct & overlapping debt, Teeter Plan, and rating. *(Newly added this run.)*
- **`continuing_disclosure_fye2025.pdf`** — Annual Financial Disclosure / audited financial statements for fiscal year ended 6/30/2025 (MSRB doc P22014374, posted 02/25/2026). Authority for current operations, enrollment, reserves, fund balances, and the unmodified audit opinion. *(Newly added this run.)*
- **`emma_security_details.html`** — EMMA security page (issuer header, terms, ratings field, event-notice categories, disclosure inventory).
- **`emma_trade_tape.json`** — 423 EMMA prints since 2019-05-15; basis for the liquidity recompute.
- **`screens_and_sources.json`** — input screens (AB-1200, AI insulation, wildfire, seismic, execution).
- **`verification_log.json`** — claim-by-claim verification record (claim → method → authority → finding). *(Newly added this run.)*
- **`os_text.txt`, `cd_full.txt`, `cd_text.txt`** — extracted text used for verification. *(Newly added this run.)*

External authorities referenced: MSRB EMMA (`emma.msrb.org/Security/Details/925836KH0`); California Government Code §53515 (statutory lien); California Department of Education AB-1200 interim certifications; USGS ASCE7-22 seismic design parameters; FEMA National Risk Index (wildfire) × NCES district-tract crosswalk; California Municipal Statistics, Inc. (AV and overlapping-debt tables within the OS).

<!-- current-state-refresh -->
### Current-State Verification (AV / coverage refresh — 2026-06-20)

Refreshed 2026-06-20 via a SERIAL, throttled EMMA continuing-disclosure pull (the original UNVERIFIABLE flag was an EMMA 403 rate-limit from concurrent scraping, not a real disclosure gap). Latest issuer annual report: _Annual Financial Disclosures Posted 02/27/2026  for the year ended 06/30/2025 (820 KB)_. **Current total assessed valuation (levy base): $10,661,166,541 for FY2025-26**. For an unlimited ad-valorem GO the AV base + the delinquency cushion ARE the 'coverage' — there is no DSCR; the levy rate floats to hold debt service constant. **This resolves the prior 'current AV/coverage UNVERIFIABLE' caveat.**
