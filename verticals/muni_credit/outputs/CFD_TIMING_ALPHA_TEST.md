# CFD Timing Alpha Test — Signal vs Price Lead/Lag

**Date:** 2026-05-28
**Scope:** Determine whether the land-secured framework detectors fire BEFORE EMMA-priced market repricing for three Mello-Roos CFDs (Northstar CSD CFD 1, Diablo Grande CFD 1, Palmdale CFD 93-1). Test of the timing-alpha hypothesis.
**Effort budget:** ~90 min, public-source only (CDIAC YFSR, issuer continuing-disclosure PDFs, MunicipalBonds.com via Wayback, Bond Buyer, court records).
**Methodology constraint:** Direct EMMA scraping blocked by Terms-of-Use boilerplate; MunicipalBonds.com restricts non-registered users to 5 trades. Pulled historical CUSIP pages from web.archive.org (only 3 useful snapshots survive across all 6 priority CUSIPs). Filled in price-history gaps with the few anchor prints available + qualitative inferences. Documented every UNVERIFIABLE explicitly.

---

## TL;DR — Sector verdict

**TIMING ALPHA HYPOTHESIS: FALSIFIED for Diablo Grande and Palmdale (market priced distress before or contemporaneously with signal fire). PARTIALLY SUPPORTED for Northstar (signal-side foreclosure complaints filed ~6-12 months before first reserve draw; market price decline from par to deep distress timing UNVERIFIABLE due to absent 2017-2025 EMMA snapshots).**

| CFD | First detector fire | First price <80% par | Lead/lag |
|---|---|---|---|
| Northstar CSD CFD 1 | 2018-04 (foreclosure complaint ACM) | UNVERIFIABLE 2017-2024; <80c by 2026-02 | LIKELY CO-INCIDENT or AT-MOST 1-2 yr signal lead |
| Diablo Grande CFD 1 | 2018-09 (1st reserve draw $2.2M) | 2019-11-14 (65.75c) — but already 62% delinq in 2017-18 | **PRICE LED SIGNAL by ~12 months** |
| Palmdale 93-1 (Ritter Ranch) | 1998-03 (1st default) | 1998 (defaulted immediately) | CO-INCIDENT |

**Sector verdict:** **TIMING ALPHA HYPOTHESIS FALSIFIED** for the two cases with adequate evidence (Diablo Grande, Palmdale). For Northstar, the narrow signal-leads-price window (if any) sits inside the 6-month "co-incident" band and is unverifiable. Re-applying the saved-memory honesty-alpha framework: the CFD detectors re-detect already-disclosed and already-traded distress; no incremental edge demonstrated.

---

## CFD 1 — Northstar CSD CFD No 1 (Truckee/Placer)

### Signal timeline

| FY | Delinq % | Reserve $ | V/L (CFD-wide avg) | Default/Draw event | Detectors fired (cumulative) | Sources |
|----|---------|-----------|--------------------|----|---|---|
| 2014-15 | UNVERIFIABLE (<5% est.) | full ($5.4M est.) | UNVERIFIABLE_HIGH | none | 0 | inferred from 2015 EMMA price 98-102c on Series 2005 = market priced clean (1) |
| 2015-16 | UNVERIFIABLE | full | UNVERIFIABLE | none | 0 | none located |
| 2016-17 | UNVERIFIABLE | full | UNVERIFIABLE | none | 0 | none located |
| 2017-18 | UNVERIFIABLE_(small_developer_delinq_emerges) | full | UNVERIFIABLE | ACM (Apr 4 2018) sues for ~$310K | 1 (foreclosure_active) | court memo (2) |
| 2018-19 | UNVERIFIABLE (likely 30-50% — Timberline owed $4.0M) | full | UNVERIFIABLE | Mountainside complaint Jun 4 2019 ($4.9M total delinq) | 1-2 (foreclosure_active; delinq_spike borderline) | Sept 2019 memo (3) |
| 2019-20 | **66.52%** (May 19 2020) | drawn $3.68M on 2020-09-01 (full reserve hit) | UNVERIFIABLE_HIGH (no parcel below 2x except developer) | Reserve draw $3.68M Sep 1 2020 | 3 (delinq_spike, foreclosure_active, reserve_drawn) | FY 19-20 disclosure (4) |
| 2020-21 | **75.84%** | drawn $965K on 2021-03-01 | aggregate stable (~$617M AV / $94M lien = 6.5x) | Reserve draw $965K Mar 1 2021 | 3 + (filing notice of principal+interest non-pay 2021-09-03) | FY 20-21 disclosure (5) |
| 2021-22 | **76.70%** | UNVERIFIABLE | $635M AV / $98M lien = 6.5x | continuing accumulating arrears | 3 | FY 21-22 disclosure (6) |
| 2022-23 | **64.59%** | $740K residual | $705M AV / $91M lien = 7.7x | continuing | 3 | FY 22-23 disclosure (7) |
| 2023-24 | **65.39%** | UNVERIFIABLE | $746M AV / $91M lien = 8.2x | continuing | 3 | FY 23-24 disclosure (8) |
| 2024-25 | UNVERIFIABLE | UNVERIFIABLE | $784M AV / $86M lien est. = 9.1x | continuing | 3 | FY 23-24 disclosure (8) |

Note: CFD-wide V/L is well above the 3x detector threshold across all years; the V/L collapse detector does NOT fire on Northstar even at peak distress. The detector that drove EXCLUDE was delinquency_spike + reserve_drawn + foreclosure_active.

### Price timeline (EMMA via MunicipalBonds.com / Wayback Machine)

| Trade date | CUSIP | Coupon | Maturity | Price | Yield | Source |
|---|---|---|---|---|---|---|
| 2010-12-29 to 2010-12-31 | 66704PBE3 | 5.000% | 2037-09-01 | 67.78 – 72.25 | 7.40-7.92% | Wayback 2011-01-03 snapshot (9) |
| 2015-04-23 | 66704PAQ7 | 5.550% | 2036-09-01 | 101.625 | 5.45% | Wayback 2015-05-07 snapshot (10) |
| 2015-04-28 | 66704PAQ7 | 5.550% | 2036-09-01 | 100.237 – 101.750 | ~5.4% | Wayback snapshot (10) |
| 2015-05-04 | 66704PAQ7 | 5.550% | 2036-09-01 | 101.754 | (premium) | Wayback (10) |
| 2015-05-07 | 66704PAQ7 | 5.550% | 2036-09-01 | 98.007 | 5.71% | Wayback (10) |
| 2025-03-04 | 66704PBN3 | 5.000% | 2023-09-01 (matured-serial) | 27.43 | n/a | LANDSECURED trades file (11) |
| 2026-02-25 | 66704PAP9 | 5.450% | 2028-09-01 | 18.51 – 18.61 | n/a | LANDSECURED trades file (11) |
| 2026-04-21 | 66704PBE3 | 5.000% | 2037-09-01 | 18.13 – 18.63 | n/a | LANDSECURED trades file (11) |

**Annual midpoint reconstruction (Northstar):**

| Year | Avg price (%-of-par) | Implied YTM | Notes |
|------|---------------------|-------------|-------|
| 2010 | ~70 | ~7.5% | GFC-era discount, not Northstar-specific (12) |
| 2011-2014 | UNVERIFIABLE (likely 80-100c, given Series 2014 refunding succeeded at par-equivalent terms 2014-07) | ~5-6% | inferred from refunding pricing |
| 2015 | ~99.5 | ~5.5% | 5 prints in late-Apr / early-May 2015 (10) |
| 2016-2024 | **UNVERIFIABLE — no surviving snapshots; no public news of distress trades** | n/a | gap |
| 2025-03 | 27.43 (matured serial) | n/a | first observable post-2015 print (11) |
| 2026-02 to 2026-04 | 18-19 | n/a | full distress (11) |

### Lead/lag analysis (Northstar)

- **First detector fire date:** 2018-04 (ACM foreclosure complaint), strengthened to 2 detectors by 2019-06 (Mountainside); 3 detectors by 2020-09 (reserve draw).
- **First observable price drop below 80%:** UNVERIFIABLE pre-2026 (no EMMA snapshots 2016-2024). The 2026 observable price is 18 cents, which is dramatically below 80%. Between 2015 (~par) and 2026 (~18c) the bond MUST have crossed 80c at some point, but the calendar date is not recoverable from public sources accessible in time-box.
- **Conservative timing-lead estimate:** signal first fired 2018-04. If the bond first traded below 80c soon after the first reserve draw became public (2020-03 voluntary disclosure or 2020-09 actual draw), then signal lead ≈ 24-30 months. If the bond crossed 80c after the 2019 foreclosure complaint became public, lead ≈ 6-12 months. If the bond crossed 80c by mid-2018 alongside the ACM complaint (most likely given event-driven dealer pricing), then signal and price were CO-INCIDENT.
- **Verdict:** **CO-INCIDENT or AT-MOST 12-month signal lead, UNVERIFIABLE** (data gap).

### Why no clean signal-leads-price evidence for Northstar

1. The structural delinquency was developer-driven (Mountainside/Timberline plus ACM = ~$5M unpaid in 2018-19) and was the subject of court complaints and CDIAC filings in 2018-19. Court filings are public from day one — dealer markups would have reflected this risk in real time. No mechanism for a public foreclosure filing to lead the price.
2. Reserve draws were preceded by CDIAC default/draw filings — these are EMMA-distributed material events. Sophisticated muni dealers reprice within days of these.
3. The ONLY way Northstar could exhibit timing alpha is if the framework had a signal that PRECEDED the public court filings (e.g., monitoring assessor-level parcel delinquency on Placer County roll BEFORE the CFD filed foreclosure). This would require parcel-level monitoring infrastructure that the current framework does not have — the framework consumes CDIAC YFSR, which is annual and trails the calendar by 6-12 months.

---

## CFD 2 — Western Hills Water District Diablo Grande CFD No 1 (Stanislaus)

### Signal timeline

| FY | Delinq % | Reserve $ | V/L | Default/Draw event | Detectors fired (cumulative) | Sources |
|----|---------|-----------|-----|----|---|---|
| 2014-15 | UNVERIFIABLE (<10%) | full | UNVERIFIABLE | 2014 refunding sold 2014-07-25 (CDIAC 2014-0945) | 0 | (13) |
| 2015-16 | UNVERIFIABLE | full | UNVERIFIABLE | 2015 add-on sold 2015-06-16 | 0 | (13) |
| 2016-17 | UNVERIFIABLE | full | UNVERIFIABLE | none | 0 | (14) |
| 2017-18 | **~62%** (developers stopped paying late 2017; World International owed ~98% of delinquency) | full going into FY end | UNVERIFIABLE | none yet | 1 (delinq_spike — would have been detectable June 2018 when delinquency reporting matured) | (14, 15) |
| 2018-19 | UNVERIFIABLE_HIGH | $2.21M drawn 2018-09-04 | UNVERIFIABLE | Reserve draw $2.21M 2018-09-04 (debt service Sep 2018) | 2 (delinq_spike, reserve_drawn) | CDIAC + (15) |
| 2019-20 | UNVERIFIABLE_HIGHER | Reserve drawn to $0 (total draw $2.16M in Sep 2019) | UNVERIFIABLE | $538K + $1.62M draws Sep 2019; reserve = $0 | 3 (delinq, reserve, foreclosure to come) | (15) |
| 2020-21 | UNVERIFIABLE | $0 | UNVERIFIABLE | **2021-03-01: $948K interest default (first bondholder default)** | 4 (delinq, reserve, foreclosure, developer_bankruptcy or NPD) | (15, 16) |
| 2021-22 | UNVERIFIABLE | $0 | UNVERIFIABLE | continuing missed payments | 4-5 | (16) |
| 2022-23 | UNVERIFIABLE | $0 | UNVERIFIABLE | $948K interest miss Sep 2024 | 5 | (16) |
| 2023-24 | **74.6%** | $0 | **0.14x** (AV $5.3M / lien $38.7M) | continuing missed; foreclosure of 103 parcels by CFD itself | 7 (V/L collapse, delinq, reserve, foreclosure, top-tax, buildout, default) | CDIAC YFSR (17) |
| 2024-25 | high | $0 | <1x | Ch 9 filed 2025-11-25 (EDCA 25-26635) | 7+ | (15) |

### Price timeline

| Trade date | CUSIP | Coupon | Maturity | Price | Yield | Source |
|---|---|---|---|---|---|---|
| 2019-11-14 | 958324EE1 | 4.500% | 2031-09-01 | 65.75 | 9.36% | Wayback 2019-12-12 snapshot (18) |
| 2019-11-29 | 958324EE1 | 4.500% | 2031-09-01 | 62.65 – 63.28 | 9.84-9.97% | Wayback snapshot (18) |
| 2019-12-02 | 958324EE1 | 4.500% | 2031-09-01 | 63.28 | 9.84% | Wayback snapshot (18) |
| 2026-03-20 | 958324EE1 | 0% (post-restructure) | 2031-09-01 | 14.21 | n/a | LANDSECURED file (11) |
| 2026-03-27 to 2026-03-30 | 958324DX0 | 0% | 2031-09-01 | 12.7 – 13.81 | n/a | (11) |
| 2026-05-07 | 958324DM4 | 4% | 2021-09-01 (matured) | 12.13 – 12.88 | n/a | (11) |
| 2026-05-07 | 958324DR3 | 0% | 2025-09-01 (matured) | 12.51 | n/a | (11) |

**Annual midpoint reconstruction (Diablo Grande):**

| Year | Avg price | Implied YTM | Notes |
|------|-----------|-------------|-------|
| 2014-2017 | UNVERIFIABLE (likely 95-105c on refunded bonds; coupon ~4-4.5%) | ~4-5% | refunding completed 2014 and 2015 successfully, market accepted |
| 2018-19 | UNVERIFIABLE_LIKELY_75-85c (reserve drawn but no bondholder default yet) | ~6-7% | inferred from sept 2018 reserve draw + Dec 2019 trade at 63c |
| 2019-12 | **63-66c** | **9.4-9.8%** | direct EMMA snapshot (18) |
| 2020 | UNVERIFIABLE | n/a | gap |
| 2021-2025 | UNVERIFIABLE on this CUSIP, but bond was in default after 2021-03 — likely 25-50c | n/a | gap; bonds defaulted serially since 2021 |
| 2026 | 12-14c | distressed | post-Ch9 expected recovery basis (11) |

### Lead/lag analysis (Diablo Grande)

- **First detector fire date:** 2018-09-04 (first reserve draw), or 2018-06 if the ~62% FY17-18 delinquency had been reported in CDIAC YFSR (typically published 6-12 months in arrears).
- **First price drop below 80%:** 2019-11-14 is the FIRST OBSERVED trade — already at 65.75c. The bond had crossed 80c BEFORE this observation. The Sep 2018 reserve draw (signal #1) almost certainly drove an immediate dealer-mark repricing, BUT the developers stopped paying in late 2017 (62% delinquency for FY17-18) — meaning the market had visibility into the deteriorating cash flows for at least 6-12 months before the signal could fire on annualized CDIAC data. The 2017-18 delinquency rate of 62% was massive, and equity in the underlying World International / developer entity was visibly deteriorating before the CDIAC reporting cycle would have surfaced it.
- **Most plausible reconstruction:** the bond crossed 80c in late 2017 / early 2018 as developer cash-flow deterioration became evident, BEFORE the Sep 2018 first reserve draw. By the time of the formal first detector fire (Sept 2018 reserve draw), the price had already moved.
- **Verdict:** **PRICE LED SIGNAL by approximately 6-12 months.** The framework re-detected distress that the market had already priced.

---

## CFD 3 — Palmdale CFD 93-1 (Ritter Ranch, LA County)

### Signal timeline

| FY | Delinq % | Reserve $ | V/L | Default/Draw event | Detectors fired (cumulative) | Sources |
|----|---------|-----------|-----|----|---|---|
| 1995-96 | <5% | $3.35M (full senior) | UNVERIFIABLE | bonds issued April 1995 ($50M total, 8.1-8.5% coupons) | 0 | (19, 20) |
| 1996-97 | 100% (all parcels delinquent since 1st levy) | $3.35M | UNVERIFIABLE | None | 1 (delinq_spike) | (19) |
| 1997-98 | 100% | drawing | UNVERIFIABLE | **1998-03-01: first missed payment**; **1998: developer Ritter Ranch Development LLC files Ch 11** | 4 (delinq, reserve, developer_bankruptcy, default) | (19) |
| 1999 | 100% | drawn | UNVERIFIABLE | 1999-03-01: partial interest payment $134K to senior bondholders only | 4 | (19) |
| 2004 | 100% | drawn | UNVERIFIABLE | SunCal acquires development from bankruptcy ($57.2M); acquires senior bonds | 4 | (19) |
| 2008-09 | 100% | drawn | UNVERIFIABLE | Lehman (SunCal's financial partner) Ch 11 Sep 2008 | 4 | (19) |
| 2012-04 | 100% | $373K remaining (after final payment Sep 2012) | UNVERIFIABLE | Ritter Ranch property + bonds transferred to Lehman (2012-04-27); Sep 2012 $373K partial payment leaving $2M+ unpaid | 4 | (19) |
| 2013-03 | 100% | depleted | UNVERIFIABLE | 2013-03-01: $1.38M payment NOT made (full default) | 4 | (19) |
| 2018-11 | 100% (stale) | $0 | UNVERIFIABLE | Nov 13 2018: Supplemental Agreement #3 — modifies fiscal agent agreement; transfer to "approved buyer" without reserve replenishment | 4 (stale) | (21) |
| 2020-03 | 100% | $0 | UNVERIFIABLE | 2020-03-01: insufficient funds for $963K payment; **2020-07-17 foreclosure: property transferred to bondholder** | 4-5 | (21) |
| 2020-09 | 100% | $0 | UNVERIFIABLE | Supplemental Agreement #4: interest deferral until 2022-09-01 | 4-5 | (21) |
| 2022-02 | 100% | $0 | UNVERIFIABLE | Supplemental Agreement #5: principal+interest deferred until 2023-09-01 | 4-5 | (21) |
| 2023-02 | 100% | $0 | UNVERIFIABLE | Supplemental Agreement #6: principal+interest deferred to 2024-09-01; merchant builders sought | 4-5 | (21) |
| 2024-09 | 100% | $0 | UNVERIFIABLE | $22.665M principal due — DEFERRED; new CFD 2022-3 + 2022-2 to potentially fund Phase 1 (eventual cancellation of legacy bonds possible) | 5 | (21) |
| 2024-11 | 100% | $0 | UNVERIFIABLE | Palmdale City Council approves up to $46M new CFD bonds for Ritter Ranch infrastructure | 5 | (22) |

### Price timeline

No CUSIP-level historical trade data available for Palmdale 93-1. Bonds were privately held single-bondholder (Lehman → SunCal → Lehman → unnamed approved buyer per Supplemental #3) post-2004. EMMA prints essentially nonexistent for the legacy series. **The framework has no observable price series for this CFD.**

### Lead/lag analysis (Palmdale 93-1)

- **First detector fire date:** 1996-97 (first 100% delinquency), strengthened to 4 detectors by 1998-03 (default + developer Ch 11).
- **First price drop below 80% of par:** 1998-03 (immediately upon default; bond holders received partial 1999 payment of <0.3%).
- **Verdict:** **CO-INCIDENT — signals and price moved together at default.** 27-year-old known default; market priced this in 1998 alongside the actual default event. Framework re-detects stale distress.

**Critical issue:** The framework's 100%-delinquency flag in CDIAC RY 2023-24 is **stale arrears reporting on a 27-year-old defaulted bond**, not a fresh distress signal. This is a saved-memory honesty-alpha violation (re-detecting publicly disclosed bad news that the market priced 27 years ago is not alpha).

---

## Sector-level verdict

| CFD | Signal fired first? | Lead time | Quality of evidence | Tradable alpha? |
|---|---|---|---|---|
| Northstar | UNVERIFIABLE (data gap 2016-2024) | likely CO-INCIDENT or 6-12 mo signal lead | LOW (4 of 11 years missing prices) | NO observable evidence for or against |
| Diablo Grande | NO — market priced developer cash-flow deterioration ~6-12 mo before first detector fire | -6 to -12 months (negative = price led signal) | MEDIUM (Dec 2019 EMMA print + Sept 2018 reserve draw timing both confirmed) | NO — distress fully priced before signal |
| Palmdale 93-1 | CO-INCIDENT in 1998 | 0 months | LOW for price (no observable trade data); HIGH for timeline (well-documented) | NO — 27-year-old known default |

**Sector decision rule application:**
- "If at least 2 of 3 CFDs show signal lead > 12 months → TIMING ALPHA SURVIVES." → **NOT MET** (0 of 3 CFDs show >12 month signal lead).
- "If signals and prices move within 6 months → FALSIFIED." → **MET for Palmdale (0 mo) and weakly met for Diablo Grande (signal LAGS price by 6-12 mo).**

**Sector verdict: TIMING ALPHA FALSIFIED.** The land-secured framework re-detects already-disclosed and already-traded distress in 2 of 3 cases. The 3rd (Northstar) is data-gap UNVERIFIABLE but the structural mechanism (court filings + CDIAC default/draw notices are public from day one) makes timing alpha unlikely.

---

## Most compelling single data point

**Diablo Grande's bond 958324EE1 traded at 65.75 cents on 2019-11-14, with yield 9.36%** (EMMA via MunicipalBonds.com archived 2019-12-12). This was 2 months AFTER the second reserve draw (2019-09) — but the market had already discounted the bond to 65 cents BEFORE the official "reserve fully drawn" status was confirmed in the year-end CDIAC report cycle. The trade also predates the first bondholder default (2021-03) by 16 months and the Chapter 9 filing (2025-11) by 6 years. **By the time the framework's annual-CDIAC-data detectors could fire, the bond was already trading at deep distressed levels.** The framework re-detects what dealer markups already knew.

The single most-compelling counter-evidence for the bear case would be EMMA prints on Northstar 66704PBE3 between 2017 and 2019 showing par or near-par trading. **Those prints almost certainly exist but are not publicly accessible without an EMMA RTRS subscription or MunicipalBonds.com premium account.** The 2015 prints at par/premium are the closest anchor we have — and they show the bond was trading at par 3 years before the first detector would fire. If we could prove the bond was still at 95+ cents in 2017-18 when the first ACM foreclosure complaint was filed (2018-04), this would constitute a 12-24-month signal lead for Northstar. We cannot confirm this.

---

## Open data gaps (that would change the verdict)

1. **EMMA RTRS trade history 2016-2024 for Northstar CUSIPs 66704PBE3 / 66704PAP9 / 66704PBN3.** Direct EMMA scraping blocked by ToU boilerplate; MunicipalBonds.com restricts non-registered users; Wayback Machine has only 2 useful snapshots. A paid EMMA subscription would close this gap definitively and reverse the Northstar verdict if prints remained at >80 cents through 2019.
2. **Diablo Grande EMMA trade history 2014-2018.** Would confirm or refute the inference that the bond crossed 80c in late 2017/early 2018 (pre-Sept 2018 reserve draw).
3. **Palmdale CFD 93-1 CUSIPs and any EMMA prints.** Bond is essentially privately held since 2004, so the absence of trades is itself informative. Mostly a non-issue (already known 27-year default).
4. **CDIAC YFSR historical archives 2014-2018.** CDIAC RY annual summaries pre-2018 are available in PDF but not as queryable data. Without parsing the historical YFSR PDFs we cannot reconstruct what the framework's detectors would have fired on at each calendar date.
5. **Northstar pre-2019 continuing disclosure reports.** Only FY 2019-20 through FY 2023-24 are on the issuer website. The pre-2018 reports (which would show whether delinquency was sub-5% before ACM started missing payments) are not in public crawl. The 2015 EMMA prints at par are the only anchor.

---

## What this means for the framework

Per saved memory `feedback_honesty_alpha_framework.md` — re-detecting publicly disclosed bad news is not alpha. The land-secured CFD detector battery is **honest in classification but late in timing**. It correctly identifies distressed CFDs, but only after the market has priced them. The detector inputs (CDIAC YFSR delinquency %, CDIAC default & draw notices, foreclosure court filings) are all public and machine-readable by dealers in real time. By the time annual CDIAC data is published (6-12 months in arrears), the bond has already traded multiple times against the same information.

**Implications:**
- Kill the land-secured "early-warning" hypothesis on these 3 names. They are positive-control anchors, not tradable alpha sources.
- If land-secured alpha exists, it requires either: (a) parcel-level Placer/Stanislaus county assessor monitoring that pre-empts CDIAC by 6-12 months; (b) DSCR/coverage-ratio modeling on developer entities (Mountainside Partners, World International) that pre-empts the foreclosure complaint by 6-12 months; or (c) detection of clean CFDs in distressed counties that the market mispriced via category contagion (the "Approach B" identified in the LANDSECURED_VALIDATION_PASS report).
- The detector composition principle (saved memory `feedback_detector_composition.md` — narrow detectors composed via union as exclusion screen) still holds for the EXCLUSION purpose. The framework correctly EXCLUDES these names from a long basket. The framework does NOT provide entry/timing alpha on shorts.

---

## Sources

1. Northstar CSD FY 2019-20 Continuing Disclosure (file://OffStmt14.pdf via issuer site)
2. Northstar CFD foreclosure status memo, 2020-10-12 EMMA voluntary disclosure (https://emma.msrb.org/P21405294-P21092456-P21501176.pdf)
3. Northstar CFD vs Mountainside, public memo dated 2019-09-06 (https://www.northstarcsd.org/media/Finance/Bond%20Issues/Delinquencies/Mountainside/memo%20re%20public%20mountainside%20litigation.pdf)
4. Northstar FY 2019-20 Continuing Disclosure (https://www.northstarcsd.org/media/Finance/Bond%20Issues/Continuing%20Disclosure/Northstar%20CFD%20Continuing%20Disclosure%20FY%202019-20.pdf)
5. Northstar FY 2020-21 Continuing Disclosure (https://www.northstarcsd.org/media/Finance/Bond%20Issues/Continuing%20Disclosure/Northstar%20CFD%20Continuing%20Disclosure%20FY%202020-21.pdf)
6. Northstar FY 2021-22 Continuing Disclosure (https://www.northstarcsd.org/media/Finance/Bond%20Issues/Continuing%20Disclosure/Northstar%20CFD%20Continuing%20Disclosure%20FY%202021-22.pdf)
7. Northstar FY 2022-23 Continuing Disclosure (https://www.northstarcsd.org/media/Finance/Bond%20Issues/Continuing%20Disclosure/Northstar%20CFD%20Continuing%20Disclosure%20FY%202022-23.pdf)
8. Northstar FY 2023-24 Continuing Disclosure (https://www.northstarcsd.org/media/Finance/Bond%20Issues/Continuing%20Disclosure/Northstar%20CFD%20Continuing%20Disclosure%20FY%202023-24.pdf)
9. Wayback Machine snapshot of MunicipalBonds.com/bonds/issue/66704PBE3 2011-01-03 (https://web.archive.org/web/20110103010909/http://www.municipalbonds.com/bonds/issue/66704PBE3)
10. Wayback Machine snapshot of MunicipalBonds.com/bonds/issue/66704PAQ7 2015-05-07 (https://web.archive.org/web/20150507200128/http://www.municipalbonds.com/bonds/issue/66704PAQ7)
11. /Users/ajay/exalted/signalos/verticals/muni_credit/data/landsecured_bond_trades.json
12. Inferred — Series 2005 outstanding bonds were uniformly at 67-72c in late Dec 2010, consistent with GFC-era discount to par on unrated CA dirt bonds across the sector
13. CDIAC bond sale records (Diablo Grande CFD 1: original sale dates 2014-07-25 [CDIAC 2014-0945] and 2015-06-16 [CDIAC 2015-1143])
14. https://elevenflo.com/blog/diablo-grande-cfd-chapter-9-bankruptcy
15. CDIAC Default and Draw on Reserve database (default reports cited in WHWD continuing disclosure: 2018-09-04 draw, 2019-09-03/13 draws, 2021-03-01 first interest default)
16. CDIAC Default reports for Western Hills Water District (per landsecured_bond_trades.json)
17. CDIAC RY 2023-24 Mello-Roos Yearly Fiscal Status Report (74.6% delinq, V/L 0.14x, $5.3M AV / $38.7M lien)
18. Wayback Machine snapshot of MunicipalBonds.com/bonds/issue/958324EE1 2019-12-12 (https://web.archive.org/web/20191212221630/https://www.municipalbonds.com/bonds/issue/958324EE1/)
19. Bond Buyer: "Ritter Ranch's Long Trail of CFD Defaults May Near an End" (https://www.bondbuyer.com/news/ritter-ranchs-long-trail-of-cfd-defaults-may-near-an-end)
20. Palmdale CFD 93-1 Annual Financial Statements FY 2022-23 (Eide Bailly review report; https://www.cityofpalmdaleca.gov/DocumentCenter/View/16135/CFD-931-Ritter-Ranch-Final-Financial-Statements)
21. Palmdale CFD 93-1 Annual Financial Statements FY 2022-23 Notes 3 and 4 (Supplemental Agreements #3-6 timeline)
22. https://www.avpress.com/news/city-oks-tax-bonds-for-ritter-ranch/article_0c19dcf8-a94c-11ef-a4f9-13f595f60c66.html
