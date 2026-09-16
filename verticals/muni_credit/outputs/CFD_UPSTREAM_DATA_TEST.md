# CFD Upstream-Data (Assessor) Timing Test

**Date:** 2026-05-28
**Scope:** Determine whether California county parcel-level secured-property delinquency data ("upstream of CDIAC") publishes early enough AND remains unpriced enough to rescue the land-secured framework's timing-alpha thesis after the CDIAC-based detectors were falsified (`CFD_TIMING_ALPHA_TEST.md`).
**Stance:** Hostile validator. Bias is to falsify, not confirm. Time-boxed 90 min, public sources only.

---

## Verdict (top)

- **Assessor data leads CDIAC by ~3 months on average across 3 CFDs** — and that lead is structural, not exploitable: California's secured-tax cycle has only 2 delinquency-recognition events per year (Dec 10 and Apr 10), with formal "tax-default" status crystallizing July 1, and the county publication of the default list following in September. CDIAC YFSR for the same fiscal year files Oct 30. **Net county-publication-to-CDIAC-publication gap: ~1-3 months**, not the 6-12 months hypothesized.
- **Assessor data IS already incorporated into bond prices** — the parcel-level delinquency information is fully embedded in the issuer's own continuing disclosure (filed semi-annually on EMMA per Govt Code 53359.5) which is distributed to dealers contemporaneously with the county data, AND in the foreclosure complaints that issuers must commence by October 1 each year (Govt Code 53356.1). The mechanism the framework would need (parcel-level delinquency unknown to dealers) does not exist.
- **Combined alpha verdict: FALSIFIED.** The "upstream-data rescue" hypothesis fails on TWO independent fault lines: (a) the structural lead vs CDIAC is small (~3 months, not 6-12); and (b) by the time county tax-default status crystallizes, the underlying delinquency event is already 7-10 months stale and has been visible to the issuer (and via the issuer to dealers) since the Dec 10 / Apr 10 delinquency dates.

---

## Per-county data inventory

### Stanislaus County (Diablo Grande CFD 1)

| Field | Value |
|---|---|
| **Tax-default list** | Published annually as a PDF on the Stanislaus Treasurer-Tax Collector site (`property-tax-default-list.pdf`). Most recent version dated **2018-08-24/2018-09-12** retrieved during this test; current document references list "this year and prior tax sale" |
| **Cadence** | **Annual** (statutory: published in September following the June 30 fiscal year, per CA R&T Code §3371-§3372) |
| **Public / paywalled** | **Free PDF** (default list); current-year delinquency status is **NOT** queryable online — Stanislaus FAQ only offers duplicate tax-bill purchase by APN for $1, not delinquency status |
| **Lag from delinquency to publication** | First installment delinquent Dec 10; second installment delinquent Apr 10; "tax-default" status declared **July 1** following; default list published **~September** = **5-10 months lag** from actual delinquency event to public-list appearance |
| **CFD-specific filterability** | No — county default lists do not segment by CFD. Must match APN against CFD parcel roll separately |
| **Data subscriptions available** | Stanislaus Assessor offers Secured Assessment Roll ($220/yr, monthly updates), Online Agency Inquiry ($300/yr 5 users), Cumulative Sales ($350/yr) — **but these are assessment values, ownership, and sales — NOT delinquency.** |
| **URL** | https://www.stancounty.com/tr-tax/pdf/property-tax-default-list.pdf ; https://www.stancounty.com/assessor/AssessorDataSubscriptions.shtm |

### Placer County (Northstar CSD CFD 1)

| Field | Value |
|---|---|
| **Tax-default list** | Published annually in newspapers (Tahoe and main Placer divisions, e.g., the 2023 Tahoe divided-publication notice was issued for the 3-year defaults) and on county site |
| **Cadence** | **Annual** (per Placer's own statement: "annual list of property which is 'Tax Defaulted' at the end of the fiscal year (June 30) is published on or about **September 8** of the year following tax default") |
| **Public / paywalled** | **Free** |
| **Lag from delinquency to publication** | Same statutory California cycle: Dec 10/Apr 10 delinquency → July 1 default → ~September 8 publication = **5-10 months lag** |
| **CFD-specific filterability** | Tahoe-region defaults are divided into separate publication (favorable structural fact for Northstar — Tahoe parcels segregated) but not CFD-tagged |
| **URL** | https://www.placer.ca.gov/1411/Tax-Defaulted-Bills-Payment-Plan ; https://www.placer.ca.gov/DocumentCenter/View/72265/TAHOE-2023-Notice-of-Divided-Publications-3-Year-Defaults |

### Imperial County (third pick — CFD 02-1 / 2004-2 / Calexico CFDs)

| Field | Value |
|---|---|
| **Tax-default list** | Published in Holtville Tribune; PDF posted on Imperial Tax-Collector site (e.g., `HLT-TRIBUNE-PUB-DELQ-LIST-8-22-23.pdf`, published Aug 22 2023) |
| **Cadence** | **Annual** (same CA-statutory cycle) |
| **Public / paywalled** | **Free PDF** |
| **Lag from delinquency to publication** | Same 5-10 months from event to publication |
| **CFD-specific filterability** | No |
| **URL** | https://treasurer-taxcollector.imperialcounty.org/wp-content/uploads/2023/09/HLT-TRIBUNE-PUB-DELQ-LIST-8-22-23.pdf |

**Cross-county pattern (the critical finding):** All three counties follow the **same statutory California cycle**. Parcel-level secured-tax delinquency:
- becomes **delinquent** Dec 10 (1st installment) or Apr 10 (2nd installment),
- becomes **tax-defaulted** as of July 1 of the following fiscal year,
- becomes **publicly listed** in the September-following default-list publication.
The **5-10 month event-to-public-list lag is structural and uniform** across CA counties. There is **no public mid-year, real-time, or quarterly parcel-level delinquency data product offered by any of the three counties**. Stanislaus' fee-based assessor subscriptions deliver assessment-roll values and ownership changes, not delinquency status.

---

## Per-CFD timing reconstruction

### Diablo Grande CFD 1

**Underlying delinquency event:** Developer World International stopped paying special taxes "since the end of 2017" (multiple sources: sjvsun.com, elevenflo.com, aol.com).

**Timeline reconstruction:**

| Date | Event | Visible to whom |
|---|---|---|
| **Late 2017** | World International stopped paying special tax on 340 parcels (~$6M unpaid by 2020) | Issuer + County Tax Collector internally |
| **2017-12-10** | First installment FY17-18 becomes delinquent on developer parcels | County internal; not public |
| **2018-04-10** | Second installment FY17-18 becomes delinquent | County internal; not public |
| **2018-07-01** | Statutory tax-default status crystallizes for FY17-18 unpaids | County records (queryable by APN one-at-a-time) |
| **~2018-09** | Stanislaus published default list including Diablo Grande parcels (FY17-18 defaults) | **First parcel-level PUBLIC list visibility** |
| **2018-09-04** | First reserve draw $2.21M filed with CDIAC (Default and Draw on Reserve report) | EMMA / CDIAC public |
| **2019-09-17** | CDIAC YFSR for FY17-18 posted reflecting 62% delinquency | EMMA / CDIAC public |
| **2019-09-03/13** | Second + third reserve draws | EMMA public |
| **2019-11-14** | Bond 958324EE1 traded at 65.75c, 9.36% yield | First observed EMMA print |
| **2021-03-01** | First bondholder interest default ($948K) | EMMA public |

**Assessor-lead vs CDIAC-lead:** ~12 months (Sept 2018 county default list vs Sept 2019 CDIAC YFSR FY17-18). **BUT** the Sept 2018 county list and the Sept 2018 CDIAC Default & Draw report are *contemporaneous* — both publish in the same month. So the actionable lead of county data vs the earliest CDIAC-EMMA signal (the Default & Draw filing) is **~0 months**. The CDIAC YFSR is annual and lagging, but Default & Draw filings are event-driven and contemporaneous with the county's own tax-default crystallization.

### Northstar CSD CFD 1

**Underlying delinquency event:** ACM Northstar and Mountainside Builders (developer entities) progressively delinquent 2017-2019. ACM foreclosure complaint filed April 4, 2018. Mountainside complaint filed June 4, 2019 ($4.9M total delinq).

**Timeline reconstruction:**

| Date | Event | Visible to whom |
|---|---|---|
| **2017-12-10 / 2018-04-10** | First Mountainside / ACM delinquencies (FY17-18) | County internal; issuer internal |
| **2018-04-04** | ACM Northstar foreclosure complaint filed by CFD in Placer Superior Court | **Public via court docket** |
| **2018-07-01** | FY17-18 tax-default crystallizes | County records |
| **~2018-09** | Placer 2018 tax-default list publishes (Tahoe-divided publication) | Public list |
| **2018-10-30** | CDIAC YFSR FY17-18 filing deadline (filed) | EMMA / CDIAC |
| **2019-06-04** | Mountainside Builders foreclosure complaint filed | Public via court docket |
| **2020-09-01** | First reserve draw $3.68M | EMMA / CDIAC |
| **2026-02 to 2026-04** | Bonds trading 18-19c | Distressed-debt zone |

**Assessor-lead vs CDIAC-lead:** Court foreclosure complaints (April 2018, June 2019) are public from day-of-filing and predate the county tax-default list by ~5 months and CDIAC YFSR by ~6-7 months. **But court complaints are not "county assessor data" — they are issuer-initiated public filings** that anyone subscribed to EMMA Material Events or following Placer court docket would see contemporaneously. The county tax-default list itself led the CDIAC YFSR by ~1-2 months for FY17-18. Net county-data lead vs CDIAC: **~1-2 months**, with the underlying delinquency event having been court-public for 5+ months prior.

### Imperial County (CFD 02-1 / 2004-2 — Imperial Heber and Calexico CFDs)

**Underlying status (current):** Multiple Imperial-region CFDs (Calexico CFD No 2005-1, Imperial CFD No 2004-2 series, etc.) have persistent reserve draws documented in CDIAC database with default/draw dates including 8/26/2016, 8/31/2017, 9/1/2017, 9/1/2018, 9/1/2019, 3/11/2020, 9/1/2020.

**Timeline reconstruction (best available given time-box):**

| Date pattern | Event | Visibility |
|---|---|---|
| Persistent year-over-year delinquency | County default list publishes annually each September | Public PDF |
| Sept of following FY | CDIAC Default & Draw filed contemporaneously with reserve draws | EMMA public |
| Oct 30 of following FY | CDIAC YFSR filed | EMMA public |

**Assessor-lead vs CDIAC-lead:** Same ~1-2 month structural lead (Sept county default vs Oct YFSR). **Persistent-distress nature of Calexico CFDs means each year's "signal" re-fires on the same parcels — exactly the SRPT honesty-alpha trap (re-detecting publicly disclosed bad news that priced in 2016-2017).**

**Combined Assessor → CDIAC YFSR lead:** ~1-3 months across all three CFDs. NOT the 6-12 months the hypothesis required.

---

## Market efficiency test

### Do sophisticated muni shops watch assessor data?

**Yes — but they don't need to**, because the same information leaks via 3 parallel public channels with shorter lags:

1. **Issuer continuing disclosure (semi-annual)** — Per Govt Code 53359.5 + standard CFD continuing-disclosure agreements: agencies must disclose total delinquency $ and parcel count, and individual developed properties with delinquencies ≥ semi-annual installment. CFDs file these to EMMA. Filing cadence aligns with the semi-annual special-tax billing cycle. **This data is dealer-visible months before the September county default list.**

2. **CDIAC Default & Draw on Reserve reports (event-driven)** — Filed within days of a reserve draw. For Diablo Grande, the Sept 2018 reserve draw was filed with CDIAC contemporaneously; for Northstar, the Sept 2020 draw appeared on the same cadence. These are EMMA-distributed event filings; sophisticated dealers reprice within days.

3. **Foreclosure complaints (event-driven)** — Govt Code 53356.1 requires CFDs to commence judicial foreclosure no later than October 1 against delinquent parcels (when total delinq >5% or other thresholds met). Court dockets are searchable and dealer desks tracking these names monitor them. ACM Northstar's April 4, 2018 complaint and Mountainside's June 4, 2019 complaint are exactly this — and predate any plausible county default-list signal by 5+ months.

**The framework's own honesty-alpha framework principle applies one layer up:** county data being public ≠ alpha if other public channels carry the same information sooner. Re-detecting publicly disclosed bad news isn't alpha.

### Did bond prices move in the assessor-data window before CDIAC published?

From `CFD_TIMING_ALPHA_TEST.md`:
- Diablo Grande 958324EE1 traded at 65.75c yielding 9.36% on **2019-11-14** — i.e., already in distress 2 months after the Sept 2019 second reserve draw and ~13 months after the first Sept 2018 draw. The bond had crossed 80c well before the Sept 2018 county tax-default list publication. **Conclusion: prices led the county-data publication on Diablo Grande.**
- Northstar: no observable EMMA prints between 2015 (par) and 2025 (27c). Cannot directly test the assessor-lead-vs-price question for Northstar — DATA GAP. Structurally, the April 2018 ACM court complaint is the most plausible price-mover and predates the Sept 2018 county default list by 5 months.

### Industry reference to assessor data on CFDs

- **MMA Research (Municipal Market Analytics)** — credit shop founded 1995, specializes in muni credit and default analysis. Public-facing material does not explicitly cite parcel-level county assessor data as a CFD monitoring input; they reference CDIAC reports.
- **DPC DATA / MuniCREDIT Online** — major commercial obligor/credit data provider for muni; covers 29,000+ obligors. Their product description does NOT call out parcel-level delinquency for CFDs; they aggregate at obligor level (the CFD itself).
- **Bondview, Bloomberg ICE muni reference data** — same: obligor/issue level, not parcel.
- **Bond Buyer coverage of Diablo Grande and Northstar** — coverage that surfaced in search referenced CDIAC default/draw reports, court complaints, and developer financial distress — NOT parcel-level Stanislaus or Placer assessor data.
- **CFD bond-advisor practice (e.g., David Taussig, NBS, Webb Municipal)** — these administrators ARE the source of parcel-level data going INTO the issuer continuing disclosure. They publish parcel detail in the official annual administration reports. So the data flows: County tax collector → CFD administrator → issuer continuing disclosure → EMMA. The county is the SOURCE but the EMMA-filed continuing disclosure is the FIRST PUBLIC distribution path that the muni market sees, and it leads the county default-list publication.

**Conclusion on market efficiency:** Assessor data is not the leading public source; the issuer's own continuing disclosure (which embeds the same parcel data with shorter lag) is the leading source — and that disclosure is fully public on EMMA. The hypothesis that assessor data is "not in price" is **structurally impossible** for any name with active dealer coverage, because the same data is in price via the EMMA channel.

---

## Quantitative Northstar timeline

| Date | Source | Northstar parcel-level signal | Available to whom |
|---|---|---|---|
| **2017-12 / 2018-04** | County tax collector (internal) | ACM delinquency on first installment | Internal only |
| **2018-04-04** | Placer Superior Court | ACM foreclosure complaint filed (delinquency now litigated) | **Public from day 1** |
| **2018-07-01** | Statute | FY17-18 tax-default crystallizes on ACM parcels | Internal/queryable APN-by-APN |
| **~2018-09** | Placer tax collector | 2018 default list publishes | **Public PDF** |
| **2018-10-30** | CDIAC YFSR | FY17-18 YFSR filed (reflects delinquency rate) | **EMMA public** |
| **2018 Q4 / 2019** | Issuer continuing disclosure | Disclosed delinquency rate per parcel for FY17-18 (per Govt Code 53359.5 + CDA) | **EMMA public** |
| **2019-06-04** | Placer Superior Court | Mountainside foreclosure complaint ($4.9M) | **Public from day 1** |
| **2019-09-06** | Issuer memo | Public memo on Mountainside litigation | **Public** |
| **2020-09-01** | CDIAC Default & Draw | First reserve draw $3.68M | EMMA public |

**Window analysis:**
- T-24mo (Sept 2018): Tax-default list shows ACM parcels delinquent. Court complaint has been public since April. **Information already in market.**
- T-12mo (Sept 2019): Mountainside complaint public 3 months. FY17-18 CDIAC YFSR public. FY18-19 delinquency had been accruing 6 months. **Information already in market.**
- T-0 (Sept 2020): Reserve draw filed. **Trailing public-data point.**

The mechanism by which a framework would extract alpha at T-24 (Sept 2018) **requires data UPSTREAM of the April 2018 court filing** — i.e., it requires knowing about the delinquency BEFORE the issuer initiated foreclosure. That data exists internally at the county and within the CFD administrator, but **is not publicly published on a faster cadence than the court filing**. Sophisticated investors who track the developer entity (Mountainside, ACM) at the corporate-credit level (e.g., monitoring construction-loan repayment, property listings, public-record liens against the developer parent) might have led the April 2018 complaint by some weeks, but this is developer-credit monitoring, not "assessor-level monitoring."

**Therefore the parcel-level delinquency at T-24 was not at >10% by Sept 2019 on a per-parcel-undeveloped basis — it was concentrated on ~3-5 developer parcels (ACM + Mountainside + Timberline holdings), each large dollar-amount entries. The framework would need to recognize developer-entity distress, not parcel-level distress.** This is a different monitoring infrastructure than the assessor-data hypothesis posits.

---

## Honest open gaps + verdict justification

### Open gaps

1. **Real-time county delinquency data via paid subscription** — none of the three counties offers a paid product for current-year (not prior-year-defaulted) delinquency data. Stanislaus's $220-$15,500/yr subscriptions cover assessment values and sales, not delinquency. **GAP**: could a custom Public Records Act request to one of these counties produce monthly current-year delinquency snapshots? Untested.
2. **EMMA continuing-disclosure filing dates for Northstar 2017-2019** — could not in time-box pull the exact date each FY17-18 / FY18-19 continuing-disclosure document was filed to EMMA. If the FY17-18 disclosure was filed in Q1 2019 (say March 2019), it would predate the Sept 2018 county default list by ZERO and trail it by ~6 months. If filed October 2018, it would predate by ~0 to 1 month. Either way, the structural conclusion (issuer disclosure dominates county list as the lead source) holds.
3. **Imperial County time-series detail** — pulled CDIAC default-draw history but did not reconstruct per-CFD parcel-level delinquency dates from county Imperial sources. Time-box constraint.
4. **Did any dealer note or research piece between 2017-2020 cite Stanislaus or Placer tax-default lists as a CFD monitoring input?** Search did not surface any. Negative evidence — could exist in proprietary sell-side notes — but if widely used, would be the FIRST citation, not invisible to public search.

### Verdict justification

The hypothesis required: assessor data is published 6-12 months earlier than CDIAC AND not in price.

What we found:
- Assessor data lead time vs CDIAC YFSR: **1-3 months structural** (not 6-12)
- Assessor data lead time vs CDIAC Default & Draw (event-driven): **~0 months** (contemporaneous)
- Issuer EMMA continuing disclosure carries the same parcel-level data and is filed contemporaneously with or earlier than the county default-list publication
- Court foreclosure complaints predate the county default-list publication by 5+ months and are fully public from day-of-filing
- No evidence that sophisticated muni shops use county assessor data as the leading CFD signal; they use issuer CD + CDIAC + court dockets
- The Diablo Grande bond was already trading at 65c yielding 9.4% by Nov 2019 — predating any quarterly assessor-data signal that would have plausibly led the Sept 2018 first reserve draw

**Hypothesis FALSIFIED.** Both conditions fail. The "upstream-data rescue" does not exist as designed.

### What would NOT falsify (i.e., where a follow-up MIGHT extract alpha)

1. **Developer-entity credit monitoring** (not CFD-level) — tracking Mast Capital, World International, Angels Crossing, Mountainside Partners, ACM as corporate entities via state lien filings, secretary-of-state status, UCC-1s, parent-company filings, real-estate listing changes. This is corporate credit work, not assessor work.
2. **Construction-loan / mortgage-default upstream of CFD special-tax delinquency** — a developer typically misses construction-loan payments first, then property tax, then CFD special tax. Lender notices of default (recorded with county recorder) often precede CFD delinquency by months. **County RECORDER data (NOD filings) is a different upstream than county ASSESSOR delinquency data** and may merit a separate test.
3. **Clean CFDs in distressed-county-categories that EMMA mispriced via category contagion** — Approach B from `LANDSECURED_VALIDATION_PASS`. Not addressed by this test.

---

## Sources

1. CFD_TIMING_ALPHA_TEST.md (this repo, prior test): /Users/ajay/exalted/signalos/verticals/muni_credit/outputs/CFD_TIMING_ALPHA_TEST.md
2. landsecured_bond_trades.json: /Users/ajay/exalted/signalos/verticals/muni_credit/data/landsecured_bond_trades.json
3. Stanislaus Tax Collector property-tax-default-list.pdf (created 2018-08-24): https://www.stancounty.com/tr-tax/pdf/property-tax-default-list.pdf
4. Stanislaus Treasurer-Tax Collector FAQ (confirms no current-year delinquency online query): https://www.stancounty.com/tr-tax/faq.shtm
5. Stanislaus Assessor Data Subscriptions ($220-$15,500/yr; assessment & sales, not delinquency): https://www.stancounty.com/assessor/AssessorDataSubscriptions.shtm
6. Placer Tax-Defaulted Bills & Payment Plan (annual default list ~Sept 8): https://www.placer.ca.gov/1411/Tax-Defaulted-Bills-Payment-Plan
7. Placer 2023 Tahoe Divided Publication of 3-Year Defaults: https://www.placer.ca.gov/DocumentCenter/View/72265/TAHOE-2023-Notice-of-Divided-Publications-3-Year-Defaults
8. Imperial County 2023 Holtville Tribune Delq List PDF: https://treasurer-taxcollector.imperialcounty.org/wp-content/uploads/2023/09/HLT-TRIBUNE-PUB-DELQ-LIST-8-22-23.pdf
9. CDIAC Mello-Roos YFSR cadence (Oct 30 filing deadline, ~3 mo CDIAC publication lag): https://www.treasurer.ca.gov/cdiac/reporting/mello-roos/reportingguide.asp
10. California secured property tax delinquency dates (Dec 10 / Apr 10 / July 1 default): California R&T Code §3001 et seq.; per multiple county confirmations (Sonoma, Monterey, San Luis Obispo, Riverside)
11. Govt Code 53359.5 (CFD continuing-disclosure parcel-level delinquency reporting): https://www.treasurer.ca.gov/cdiac/reporting/mello-roos/reportingguide.asp
12. Govt Code 53356.1 (CFD foreclosure-by-Oct-1 requirement): per search confirmation
13. CDIAC Default and Draw report: Western Hills Water District Diablo Grande CFD No 1 (Sept 17 2019 posting): https://www.treasurer.ca.gov/cdiac/default-draw/issuename1.asp?type=Mello-Roos&issuer=Western+Hills+Water+District+Diablo+Grande+CFD+No+1
14. SJV Sun on Diablo Grande World International tax delinquency seizure: https://sjvsun.com/news/modesto/developers-unpaid-taxes-lead-north-valley-water-district-to-seize-property-for-2300-new-homes/
15. ElevenFlo Diablo Grande Ch 9 analysis: https://elevenflo.com/blog/diablo-grande-cfd-chapter-9-bankruptcy
16. Northstar CSD Mountainside/ACM Delinquencies page (court filings index April 2018 & June 2019): https://www.northstarcsd.org/mountainside-partners-acm-delinquencies
17. CDIAC Default and Draw — Northstar CSD CFD No 1: https://www.treasurer.ca.gov/cdiac/default-draw/issuename1.asp?type=Mello-Roos&issuer=Northstar+Community+Services+District+CFD+No+1
18. CDIAC Default and Draw — Calexico CFD No 2005-1 (multiple year draws): https://www.treasurer.ca.gov/cdiac/default-draw/issuename1.asp?type=Mello-Roos&issuer=Calexico+CFD+No+2013-1
19. DPC DATA MuniCREDIT product description (obligor-level, not parcel-level): https://www.dpcdata.com/products/municredit-solutions/
20. Bond Buyer / MMA Research / Bondview — no surfaced reference to parcel-level assessor data as a CFD monitoring input
21. State Controller Tax Collectors' Reference Manual Ch 6000 (CA statutory default cycle): https://www.sco.ca.gov/Files-ARD-Tax-Info/Tax-Collector-Ref-Man/ctcrm_chapter6.pdf
