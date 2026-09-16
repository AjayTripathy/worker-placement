# Diligence Report — San Bernardino County School GO

**CUSIP:** 926055KH6
**Issuer (RESOLVED):** **Victor Valley Union High School District**, San Bernardino County, California (Victorville / High Desert)
**Issue:** $52,140,000 General Obligation Refunding Bonds, 2016 Series B — the 2037 term maturity (this CUSIP)
**Coupon / Maturity:** 4.000% / stated August 1, 2037
**Insurance / Ratings:** Insured by Assured Guaranty Municipal Corp. (AGM, now Assured Guaranty Inc.); insured rating S&P "AA", underlying Moody's "A1" at issuance
**Cutoff:** 2026-06-18
**Last trade:** 2026-06-08 @ 99.66 / 4.038% yield-to-worst

---

## (a) Verdict, thesis, and the issuer-resolution finding

**Verdict: BUYABLE, but DO NOT buy this as an 11-year bond. Buy it (if at all) as a ~7-week par-call instrument.** Two findings reframe the trade versus how it was screened:

1. **ISSUER RESOLVED — the prior screens were mis-attributed.** The true issuer is **Victor Valley Union High School District** (a 7–12 *high* school district, ~9,100–10,700 ADA, Victorville). It is **NOT** Victor Elementary School District. Our internal `screens_and_sources.json` carried `issuer: "Victor Elementary"` from a CDE fuzzy-match error, even though the same file's OpenFIGI name ("VICTOR VLY SD-B-REF") and EMMA label ("Victor Valley Union HSD GO") both pointed to the high school district. The Official Statement, the EMMA security page, the FY2025 audit, and the 15c2-12 disclosure notice all name **Victor Valley Union High School District** unambiguously. **The AB-1200 fiscal certification and the seismic screen must be read against Victor Valley UHSD, not Victor Elementary.** Both districts sit in the same county and the same High Desert seismic setting, so the screen *values* (positive cert; Inland Empire Ss ≈ 1.42) happen to remain qualitatively correct for the resolved issuer — but they were obtained for the wrong legal entity and have been re-confirmed below for the correct one.

2. **NEAR-TERM PAR CALL — the decisive economic finding.** Per the Official Statement maturity schedule, this 2037 maturity was *priced to the call*: footnote "(c) Priced to call at par on August 1, 2026." The bonds maturing on/after 8/1/2027 are **callable at par (no premium), at the District's option, on any date on or after August 1, 2026** (`official_statement.pdf`, "Optional Redemption"). Today is 2026-06-18, so the first par call is **~7 weeks away**. The market is already pricing this: recent EMMA yield-to-worst prints cluster around 4.0% to the call, and the bond trades at ~par (99.66–100.07). The "~8.04% after-tax TEY / 11-year hold" framing in the work order is **misleading** — it reads like an 11-year bond when the realistic horizon is weeks-to-the-call. Treat this as a short, near-par, callable position: tax-equivalent carry is attractive *while held*, but principal can be returned at par as early as 8/1/2026, creating reinvestment risk and capping upside.

**Thesis.** Credit quality is solid and honestly disclosed: an unlimited ad-valorem GO of a ~$10.9B-AV high school district, secured by an SB-222 statutory lien, levied/collected by San Bernardino County under a Teeter Plan (delinquency risk shifted to the County), insurance-wrapped by AGM/AG, low direct debt (~1.07% of AV), no taxpayer concentration. The catch is not credit — it is **structure and labeling**: a short callable bond dressed up as a long one, on a district whose FY2025 audit (honestly) reports a material weakness in financial-reporting controls and a "not low-risk auditee" status. None of this is hidden; it is all in primary documents. The position is acceptable for a buyer who understands they are buying ~7 weeks of ~4% YTW carry with par-call optionality, NOT a locked 11-year 8% TEY.

---

## (b) Security & pledge

| Element | Finding | Source |
|---|---|---|
| Obligation type | Unlimited ad-valorem general obligation of the District | `official_statement.pdf` cover + "Security" |
| Levy / collection | San Bernardino County Board of Supervisors is empowered and **obligated to levy and collect ad valorem taxes** sufficient to pay debt service | `official_statement.pdf` |
| Statutory lien | **Gov. Code §53515 + SB-222 (2015)** statutory lien on all ad-valorem tax revenues; arises automatically, valid/binding from execution & delivery | `official_statement.pdf`, "Statutory Lien for General Obligation Bonds" |
| Pledge | District pledges all property-tax revenues from the County levy + debt-service-fund amounts; immediate lien/security interest | `official_statement.pdf`, "Pledge of Tax Revenues" |
| Teeter Plan | County (since 1993) advances 100% of the secured levy to taxing entities and keeps delinquencies/penalties — **shifts collection risk off the District** | `official_statement.pdf`, "Teeter Plan" |
| Tax status | **Tax-exempt** (federal §103(a) exclusion; exempt from CA personal income tax; AMT discussion in OS) | `emma_security_details.html` ("Tax Status: Tax Exempt"); `official_statement.pdf` cover |
| Insurance | Insured by **AGM** (now **Assured Guaranty Inc.** after the 8/1/2024 merger); insured S&P "AA", underlying Moody's "A1" | `official_statement.pdf` cover; `emma_significant_event_agm_merger.pdf` |
| **Optional redemption** | **Callable at par, no premium, any date on/after 8/1/2026, District's option** — this CUSIP was "priced to call at par on August 1, 2026" | `official_statement.pdf`, "Optional Redemption" + maturity-schedule footnote (c) |

CONFIRMED: unlimited ad-valorem GO, SB-222/§53515 statutory first lien, tax-exempt. The only material qualifier on the pledge section is the **par call**, addressed in (a) and (g).

---

## (c) Issuer & tax base (RESOLVED district)

**Victor Valley Union High School District**, Victorville, San Bernardino County. Grades 7–12; operates the high schools plus an alternative education center; under the authority of the San Bernardino County Superintendent of Schools.

- **Enrollment / ADA:** ~9,138 students at issuance (OS); FY2025 audited total ADA ≈ **10,700** (Schedule of Average Daily Attendance, `vvuhsd_audit_fy2025.pdf`). Large, stable district.
- **Assessed valuation (tax base):** 2015-16 AV **$10,868,296,643** (~$10.9B); 2014-15 $10,263,578,808. Six-year AV trend was rising (2011-12 $9.64B → 2015-16 $10.87B). (`official_statement.pdf`, "Assessed Valuation of Property Within the District.")
- **Concentration:** No taxpayer dominates — the largest local secured taxpayer (a shopping center) is ~1.6% of local secured AV; tax base is ~65% residential / single-family. **Anti-concentration is a credit positive** (no single-employer / single-parcel cliff risk).
- **Direct debt burden:** Direct debt ~**1.07% of AV**; combined direct ~1.31%; total direct & overlapping tax/assessment debt ~2.84% of AV — **low** for a CA school district. (`official_statement.pdf`, debt-ratio table.)
- **Current finances (FY2025 audit, dated 3/13/2026):**
  - Auditor's opinion: **Unmodified** ("present fairly, in all material respects"). **No going-concern doubt** (the "going concern" language in the report is the standard auditor-responsibility boilerplate, not a finding).
  - General Fund unassigned balance ~**$58.7M**; GF balance **up ~$23.4M over the prior two years**; FY2025 GF drew down ~$8.2M (-12.3%) — a budgeted/managed drawdown, not distress.
  - Long-term GO bonds grew **$136.4M → $194.9M** (FY2024 → FY2025), i.e., the District issued new GO money in FY2025. Direction of travel (rising leverage) is worth monitoring but remains modest against a ~$11B AV base.
  - **HONESTLY-DISCLOSED NEGATIVE:** the FY2025 Summary of Auditor's Results reports a **material weakness** and **significant deficiency** in internal control over financial reporting, **noncompliance material to the financial statements**, and the District does **NOT** qualify as a low-risk auditee. Financial-statement findings 2025-001..003 involve **overstated receivables (~$3.0M)** and inventory/cash-disbursement misstatements; findings 2025-004..009 are routine CA state-compliance items (ADA accounting, independent study, instructional materials, transportation, Prop 28). This is a *financial-reporting-controls* weakness, not a solvency or going-concern problem — but it is a real, current internal-control tell and is flagged in Risks. (`vvuhsd_audit_fy2025.pdf`, Schedule of Findings and Questioned Costs.)

**AB-1200 fiscal certification (CORRECT district):** Victor Valley UHSD is **NOT listed among negative or qualified certifications** in the California Department of Education FY2025-26 First Interim Status Report; unlisted districts carry a **POSITIVE** certification, meaning the district self-certifies it can meet its obligations for the current and two subsequent fiscal years. This re-confirms the prior screen's POSITIVE result, now bound to the correct entity. (CDE First Interim Status Report FY2025-26.) NOTE: a historical FY2012-13 *negative* certification exists for this district in CDE archives — not current, but evidence the district has had fiscal-stress episodes before; consistent with the present internal-control findings.

---

## (d) Three screens (re-bound to Victor Valley UHSD)

| Screen | Result | Read |
|---|---|---|
| **AI-crash insulation** | **99 / 100 (fully insulated)** | Repayment is **local property tax via unlimited ad-valorem GO**, not the State General Fund. The State-GF capital-gains/AI-crash channel (which drove the dot-com −71% revenue / State-GO downgrade scenario) does **not** transmit to a locally-levied school GO. CONFIRMED insulated for the resolved district. |
| **Wildfire** | **0% high-fire tail** | High Desert / Victorville urbanized footprint; FEMA NRI × NCES district-tract crosswalk returned no high-fire tracts. The insurance-withdrawal-of-AV-base channel does not apply here. (Raw fire-score fields were null in the prior screen run; the 0% tail is consistent with the desert-valley geography but the underlying tract join should be re-run on the VVUHSD boundary to fully clear — see Risks.) |
| **Earthquake** | **Ss ≈ 1.42 (moderate-high)** | Inland Empire setting — **San Andreas (Mojave/San Bernardino segments) and San Jacinto** fault systems. This is the *moderate*-seismic case, not the worst. GO credit impact is muted because (i) the County, not the District, bears collection timing via the Teeter Plan, (ii) damage to the AV base from a major event is a tail, multi-year recovery risk, and (iii) **portfolio-level zone diversification** (do not stack VVUHSD with other Inland Empire / San Andreas-San Jacinto names) is the correct mitigant per our aggregate-not-per-zone fire/seismic capping rule. Note: seismic is a *physical/AV-base* risk, not a near-term debt-service risk given the statutory lien + County levy obligation. |

All three screens were originally run against "Victor Elementary." Because both districts share the county and seismic/fire setting, the values transfer, but they have been **re-bound to Victor Valley UHSD** above. The AB-1200 and seismic items are explicitly re-confirmed for the correct issuer.

---

## (e) Liquidity & execution

- **Activity:** **120 trades trailing 365 days** (confirmed by re-counting `emma_trade_tape.json`, 494 trades total back to 2016). Last 180 days: 18 distinct trading days, **16 two-sided days** — genuinely two-sided, not one-way dealer flow.
- **Recent prints:** 2026-06-08 @ 99.66 / 4.038% YTW; 2026-05-28 @ 99.991 / 4.000% (a $40k customer sale + matching inter-dealer). Trades cluster at/just under par.
- **Yield dispersion (last 180d):** YTW median ~3.99%, range ~1.36% to ~4.18%. The 1.36% outlier is a single small odd-lot print to the near call and is not representative; the ~4.0% median is the real market level. (`emma_trade_tape.json`.)
- **EMMA yield convention:** the tape's `YX` field is **yield-to-WORST** (MSRB convention), here measured to the **8/1/2026 par call** — not yield-to-maturity. Do not relabel it YTM.
- **Live two-sided quote:** **UNAVAILABLE.** IBKR contract search on 926055KH6 returned no instrument; the IBKR muni feed is close-only/thin for this name. Use the EMMA tape as the execution reference. A $40k buy is well within observed clip sizes (recent $40k blocks printed), so a small purchase is executable, but expect a one-time ~1–3 bps/yr-equivalent spread cost and confirm a live dealer offer before lifting.

---

## (f) Tax & yield

- **Tax status:** tax-exempt (federal + CA), CONFIRMED (OS + EMMA). Not a taxable muni — passes the taxable-gate (coupon is a clean 4.000%, not the odd 3-decimal near-par signature of a federally-taxable issue).
- **Yield:** current **yield-to-worst ≈ 4.0%** measured to the **8/1/2026 par call** (recent prints). At a CA top-bracket gross-up (~2.01×), that is a **tax-equivalent yield of ~8.0%** — which reconciles the "~8.04% TEY" in the work order. BUT the TEY is on a **yield-to-worst over a ~7-week horizon to the call**, not a yield-to-maturity over 11 years. If the bond is *not* called and runs toward 2037, the YTW understates the realized return modestly; if it *is* called 8/1/2026, you receive par + accrued and must reinvest. **State the metric precisely: ~4.0% gross YTW-to-call / ~8.0% TEY-to-call — a short-horizon carry number, not a locked long yield.**
- Buying at/above par (limit ~100.5 in the prior screen) into a par call 7 weeks out risks a small **negative yield-to-call** on any premium paid; do not pay a premium with this call schedule.

---

## (g) Risks (lead with the structural caveat)

1. **NEAR-TERM PAR CALL (decisive).** Callable at par, no premium, any date on/after **8/1/2026** (~7 weeks). This is a short callable bond, not an 11-year bond. Reinvestment risk + capped upside; never pay a premium. (`official_statement.pdf`, Optional Redemption.)
2. **ISSUER-LABEL RISK (now resolved, but a process flag).** Our pipeline carried the wrong issuer ("Victor Elementary") into the screens via a CDE fuzzy-match; OpenFIGI and EMMA both already pointed to Victor Valley UHSD. RESOLVED to Victor Valley Union High School District via the OS, audit, and 15c2-12 notice. **Action: correct `issuer` in `screens_and_sources.json` and re-key any portfolio records to VVUHSD.** Mis-attribution of this kind, left unresolved, would have mis-bound the cert and seismic screens.
3. **FY2025 material weakness in financial-reporting controls + "not a low-risk auditee."** Honestly disclosed (unmodified opinion, no going concern), but a current internal-control tell: overstated receivables (~$3.0M), inventory/cash misstatements, multiple state-compliance findings, plus a historical FY2012-13 negative AB-1200 cert. Not a default signal; a governance/reporting-quality signal to monitor. (`vvuhsd_audit_fy2025.pdf`.)
4. **Rising leverage.** GO debt grew $136M → $195M FY2024→FY2025; still ~1.1% of AV, but direction is up.
5. **Seismic (moderate-high).** Inland Empire Ss ≈ 1.42; San Andreas / San Jacinto. AV-base tail risk over multi-year recovery; mitigate at portfolio level by not stacking Inland Empire seismic exposure. Statutory lien + County Teeter levy insulate near-term debt service.
6. **Wildfire tract join not fully re-run on VVUHSD boundary** — 0% tail is consistent with desert-valley geography but the underlying NCES-tract crosswalk should be re-executed on the correct district polygon to fully clear (currently CONSISTENT, not independently VERIFIED for this exact boundary).
7. **No live two-sided quote (IBKR).** Execution must be confirmed against a live EMMA/dealer offer; UNVERIFIABLE intraday liquidity.
8. **Insurer concentration.** Credit enhancement depends on Assured Guaranty Inc. (post-AGM merger). The wrap compresses spread but is only as good as AG; underlying Moody's "A1" stands on its own. The 8/2024 insurer-merger 15c2-12 notice was routine (ratings carried over) — **not** a distress event. (`emma_significant_event_agm_merger.pdf`.)

**Continuing-disclosure / no-distress check:** the only recent significant-event filing reviewed is the routine AGM→AG insurer-merger notice (8/14/2024); no default, draw-on-reserve, rating-downgrade, or financial-difficulty event observed. CONSISTENT with no distress. (A full EMMA continuing-disclosure list pull is recommended to confirm no later events; current review = no distress found.)

---

## (h) Sources & attached documents

All saved under `outputs/diligence_reports/926055KH6/raw/`:

- **`official_statement.pdf`** — $52,140,000 Victor Valley Union HSD GO Refunding Bonds, 2016 Series B Official Statement (212 pp). Source of: issuer identity, unlimited ad-valorem GO, SB-222/§53515 statutory lien, pledge, Teeter Plan, AV ($10.87B), debt ratios, taxpayer concentration, tax-exemption, AGM insurance, **and the 8/1/2026 par-call / "priced to call" maturity-schedule footnote.** Fetched from EMMA IssueView ES363755 (`https://emma.msrb.org/ES808386-ES634782-ES1030151.pdf`).
- **`vvuhsd_audit_fy2025.pdf`** — Victor Valley Union HSD Audit Report, FYE 6/30/2025 (121 pp), auditor's report dated 3/13/2026. Source of: unmodified opinion, no going concern, GF balances, ADA ~10,700, GO debt $194.9M, and the **material weakness / not-low-risk-auditee / findings 2025-001..009**. (EMMA `P22025401-P21542568-P22000127.pdf`.)
- **`emma_significant_event_agm_merger.pdf`** — 15c2-12 Notice of Significant Event (8/14/2024), naming **Victor Valley Union High School District**, Base CUSIP 926055, confirming AGM→AG insurer merger (no rating change). (EMMA `P21834504-P21406005-P21848149.pdf`.)
- **`emma_security_details.html`** — EMMA Security/Details for 926055KH6: "VICTOR VALLEY UNION HIGH SCHOOL DISTRICT … G.O. Ref B," Dated 9/8/2016, Maturity 8/1/2037, Coupon 4%, Tax Exempt, Source of Repayment General Obligation, Initial Offering 111.775% / 2.64%.
- **`emma_trade_tape.json`** — 494 EMMA trades (2016–2026); 120 trades trailing 365d; last print 2026-06-08 @ 99.66 / 4.038% YTW-to-call.
- **`screens_and_sources.json`** — internal screen file. **NOTE: `issuer` field reads "Victor Elementary" and must be corrected to "Victor Valley Union High School District."** OpenFIGI ("VICTOR VLY SD-B-REF") and the EMMA label already corroborated the correct issuer.
- External: CDE First Interim Status Report FY2025-26 (AB-1200 positive certification, by absence from negative/qualified lists); CDE district profile cds=36679340000000 (Victor Valley Union High).

**Verification discipline applied:** issuer identity — VERIFIED against OS, audit, 15c2-12 notice (REFUTES the "Victor Elementary" label). Pledge/lien/tax-exemption — VERIFIED (OS). Par call — VERIFIED (OS), and it REFRAMES the yield claim. AB-1200 positive cert — CONFIRMED for the correct district (CDE). AV/concentration/debt ratios — VERIFIED (OS). FY2025 internal-control weakness — VERIFIED (audit). Live two-sided quote / full continuing-disclosure ledger — UNVERIFIABLE / not fully pulled (flagged).

<!-- current-state-refresh -->
### Current-State Verification (AV / coverage refresh — 2026-06-20)

Refreshed 2026-06-20 via a SERIAL, throttled EMMA continuing-disclosure pull (the original UNVERIFIABLE flag was an EMMA 403 rate-limit from concurrent scraping, not a real disclosure gap). Latest issuer annual report: _Annual Financial Disclosures Posted 02/24/2026  for the year ended 06/30/2025 (915 KB)_. **Current total assessed valuation (levy base): $20,486,414,007 for FY2025-26**; secured-tax delinquency **0.14%**. For an unlimited ad-valorem GO the AV base + the delinquency cushion ARE the 'coverage' — there is no DSCR; the levy rate floats to hold debt service constant. **This resolves the prior 'current AV/coverage UNVERIFIABLE' caveat.**
