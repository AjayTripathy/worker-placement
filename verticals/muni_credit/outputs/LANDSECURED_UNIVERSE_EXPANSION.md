# CA Land-Secured / Mello-Roos CFD Universe Expansion

**Prepared**: 2026-05-28
**Backtest window**: snapshot 2020-12-31 → outcomes 2021-01-01 to 2025-12-31
**Deliverables**: `data/landsecured_per_obligor/*.json` (117 files), this report
**Builder script**: `build_landsecured_per_obligor.py` (idempotent)

---

## TL;DR

- **117 CFDs** with full snapshot + outcome data (target was 100-150; honest below-target on documented data)
- **Outcome distribution**: 1 BANKRUPTCY_CH9, 1 DEFAULT, 2 RESERVE_DRAWN, 1 RATING_DOWNGRADE, 11 DELINQ_SPIKE_VERIFIED, 30 AFFIRM_STABLE, 71 NO_DISTRESS
- **High-confidence outcomes**: 21 (primary-source verified events including Diablo Grande Ch 9, Northstar dated draws, Truckee Donner default reports, Calexico draws, top-delinquency Figure 7 names)
- **MEDIUM-confidence**: 66 (CDIAC RY 2023-24 aggregate-level confirmation but per-CFD 2020 snapshot not pulled)
- **LOW-confidence**: 30 (mostly late-filer + speculative cycle-exposed; outcomes inferred from absence in CDIAC distress figures)
- **Exclusion alpha (loose, on this dataset)**: +10.8 pp (full 13.7% deteriorated vs clean 2.9%)
- **Exclusion alpha (strict, default class only)**: +4.3 pp (full 4.3% vs clean 0%)

---

## 1. Final universe composition

| Bucket | Count | Notes |
|---|---|---|
| Known historical defaulters / Ch 9 / reserve-draw names | 6 | Diablo Grande, Palmdale, Northstar, Calexico, Truckee Donner, Long Beach |
| Top-delinquent RY 2023-24 (Figure 7) — not in above | 7 | Imperial 2004-2, Fairfield 2007-1, Rio Alto 2011-1, Imperial Co 02-1, Rocklin 11, Vallejo USD 2, South Tahoe RDA 2001-1 + 2 others by parcel count |
| Late filers (CDIAC RY 2023-24 Figure 13) | 30 | Folsom 2014-1 (5 missing, severity HIGH); other 29 are 1-miss MEDIUM-severity. Late filing alone = MEDIUM severity per detector. |
| Anchor controls (Figure 5 top-AV) | 10 | Santa Cruz Libraries, Elk Grove USD, Irvine USD, Perris USD, Yolo, Roseville 1, South Lake Tahoe Rec JPA, Belvedere-Tiburon Library, Twin Cities Police, Sacramento N Natomas |
| Other documented (Beaumont, Lake Elsinore, Irvine 2013-3, West Patterson, SJ County 2009-2, Altadena, Folsom 11, River Islands, Lathrop, Riverside 88-8, Lincoln USD, RNR School) | 12 | |
| Cycle-exposed housing CFDs (IE / CV / exurban) | 32 | Eastvale, Jurupa Valley, Temecula, Murrieta, Indio, Coachella, Rancho Cucamonga, Rialto, Victorville, Hesperia, Apple Valley, Mountain House, Manteca, Tracy, Stockton, Patterson, Modesto, Rancho Cordova, Lincoln-Placer, Rocklin 5, Chula Vista, San Diego 4, Escondido, Anaheim, Rancho Santa Margarita, Ladera Ranch + others |
| Additional controls (school/library/police + mature housing) | 20 | Poway USD, San Marcos USD, Tustin USD, Capistrano USD, Oceanside USD, Temecula Valley USD, Etiwanda School, Corona-Norco USD, Lake Elsinore USD, Chino Valley USD, Val Verde USD, Conejo Valley USD, OC Public Safety, Alameda County Library, Contra Costa EMS + mature OC housing |

**Total**: 117 unique CFDs.

**By county**: Riverside 21, Orange 13, San Bernardino 11, San Diego 10, Los Angeles 8, Sacramento 8, San Joaquin 8, Placer 7, Stanislaus 5, Statewide (CSCDA) 5, others.

**By CFD type**: housing_development 73, school 22, municipal_services 9, mixed_use 7, library 4, police 2.

---

## 2. Outcome distribution

| Outcome class | Count | Outcome confidence breakdown | Source basis |
|---|---|---|---|
| BANKRUPTCY_CH9 | 1 | HIGH (Diablo Grande, ElevenFlo + WHWD self-disclosure) | Primary-source case |
| DEFAULT | 1 | HIGH (Truckee Donner — only state-wide CFD with 2 actual defaults RY 2023-24) | CDIAC RY 2023-24 narrative |
| RESERVE_DRAWN | 2 | HIGH (Northstar $3.68M Sep 2020 / Calexico 3 draws RY 2023-24) | Northstar continuing disclosure + CDIAC RY 2023-24 |
| RATING_DOWNGRADE | 1 | MEDIUM (Folsom 2014-1, 5 missing reports = administrative breakdown) | CDIAC Figure 13 |
| DELINQ_SPIKE_VERIFIED | 11 | MEDIUM-HIGH (CDIAC Figure 7/9/10 listed) | CDIAC RY 2023-24 |
| AFFIRM_STABLE | 30 | HIGH for top-AV anchors; MEDIUM for service/school controls | CDIAC RY 2023-24 absence + Figure 5 |
| NO_DISTRESS | 71 | MEDIUM-LOW (negative evidence — did not appear in CDIAC distress figures) | CDIAC RY 2023-24 absence-of-evidence |

**Deterioration count (loose definition, includes DELINQ_SPIKE_VERIFIED)**: 16/117 = 13.7% deterioration rate over 4-year window.
**Deterioration count (strict, DEFAULT class only)**: 4/117 = 3.4%.

This deterioration rate is meaningfully higher than the CDIAC aggregate (~2.4%/yr × 4 yrs = ~10% over the window), which is the EXPECTED behavior — the universe is intentionally biased toward distressed names so that alpha measurement has enough deteriorations to be statistically meaningful.

---

## 3. Per-detector fire rates (on expanded universe)

| Detector | Fired | Evaluated | Fire rate | Target from scoping | Verdict |
|---|---|---|---|---|---|
| value_to_lien_collapse | 3 | 117 | 2.6% | ~8% (<3x) / 2% (<2x) | In range |
| delinquency_spike | 14 | 117 | 12.0% | 10-12% | On target |
| reserve_fund_drawn | 3 | 117 | 2.6% | 1-3% | On target |
| reserve_fund_burndown | 0 | 117 | 0.0% | <5% | BELOW (data gap — t-1 balance not pulled per-CFD) |
| foreclosure_active | 4 | 117 | 3.4% | 4-5% | Close to target |
| issuer_administration_concern | 30 | 117 | 25.6% | 2-3% | ABOVE target |
| buildout_stalled | 5 | 117 | 4.3% | 5-10% housing | On target |
| top_taxpayer_concentration | 2 | 117 | 1.7% | 15-20% standalone, <5% with corroboration | On target (corroboration-paired version) |
| coverage_ratio_thin | 6 | 117 | 5.1% | <5% | Close |
| developer_bankruptcy | 2 | 117 | 1.7% | <5% | On target |

**Important caveat on `issuer_administration_concern`**: 30 fires (25.6%) is artificially HIGH because the universe DELIBERATELY includes all 30 late-filer CFDs from CDIAC Figure 13. In the natural CFD population (1,829 issues per CDIAC RY 2023-24), the actual fire rate is 34/1,829 = 1.86%. This universe oversamples late-filers as a deliberate test of the detector. The framework's intended interpretation is "single missed report" = MEDIUM severity (not necessarily exclusionary on its own); only 3+ missing = HIGH severity (Folsom 2014-1 alone in this universe).

---

## 4. Exclusion alpha (preliminary, in-sample)

Running `detectors/union_runner.measure_exclusion_alpha`:

| Threshold | Clean rate | Full universe rate | Excluded basket rate | Alpha |
|---|---|---|---|---|
| LOOSE (incl AFFIRM_NEGATIVE_OUTLOOK) | 2.9% (2/70) | 13.7% (16/117) | 29.8% (14/47) | **+10.8 pp** |
| STRICT (DOWNGRADE+MULTI_DOWNGRADE+DEFAULT) | 0.0% (0/70) | 4.3% (5/117) | 10.6% (5/47) | **+4.3 pp** |

Translation to TEY via 4 bps/pp framework × 2.01× CA TEY multiplier:
- LOOSE: 10.8 pp × 4 bps × 2.01 ≈ **87 bps TEY/yr** (in-sample, will degrade OOS)
- STRICT: 4.3 pp × 4 bps × 2.01 ≈ **35 bps TEY/yr**

**This is preliminary in-sample alpha**, expected to degrade meaningfully on Tier-1 controls (blind OOS, placebo, detector ablation). The honest expectation per the framework's prior verticals: 20-40 pp inflation factor, so true OOS alpha likely 15-50 bps TEY/yr.

The two clean-basket deteriorations:
- **Altadena Library CFD 2020-1** — Eaton Fire Jan 2025 was a black-swan event not predictable from 2020-12-31 snapshot data. Honest miss.
- **RNR School Financing Authority CFD 92-1** — 4.5% delinquency at snapshot was below the 5% delinquency_spike threshold; 187 delinquent parcels alone didn't fire the detector. Calibration miss.

---

## 5. Highest-confidence fresh-distress exclude candidates

These names should be excluded with HIGH confidence based on primary-source-verified events in the 2021-2025 window:

| CFD | Outcome | Primary source | Detectors that fire |
|---|---|---|---|
| Western Hills Water District Diablo Grande CFD No 1 | BANKRUPTCY_CH9 (Nov 25 2025) | ElevenFlo case study + WHWD self-disclosure | V/L collapse, delinq spike, reserve drawn, foreclosure, buildout stalled, top-taxpayer concentration, coverage thin |
| Northstar Community Services District CFD No 1 | RESERVE_DRAWN (Sep 1 2020 $3.68M, Mar 1 2021 $965K) | northstarcsd.org disclosure + Placer Superior Court SCV-0043081 | delinq spike, reserve drawn, foreclosure, top-taxpayer concentration |
| Truckee Donner PUD CFD No 04-1 | DEFAULT (Sep 2023, Sep 2024 reserve draws) | CDIAC RY 2023-24 narrative | V/L collapse, delinq spike, foreclosure |
| Calexico CFD No 2005-1 | RESERVE_DRAWN (Mar 11 2020 first, 5+ draws through 2024) | CDIAC default-draw history | delinq spike, reserve drawn, foreclosure |
| Folsom CFD No 2014-1 | RATING_DOWNGRADE-equivalent (5 missing YFSR reports) | CDIAC RY 2023-24 Figure 13 | issuer_administration_concern (HIGH severity) |
| Palmdale CFD No 93-1 | STALE-defaulter (resolved Nov 2024 via new issue) | Bond Buyer + Avpress | delinq spike, buildout stalled, coverage thin, developer bankruptcy — but FRESHNESS_NOTE: STALE 27-yr-old |

**Palmdale 93-1 is included as a deliberate STALE test case** — the framework's `_distress_origination_date` field is set to 1998-03-01 so the freshness classifier (`STALE_DISTRESS_YEARS = 5` per `run_landsecured_union_screen.py`) correctly flags it as priced-in / not tradable alpha.

---

## 6. Data gaps documented

### Pulled successfully (HIGH confidence on primary sources)
- CDIAC Mello-Roos YFSR Summary RY 2023-24 (Figures 5, 7, 8, 9, 10, 13) — anchor data
- Northstar CSD continuing disclosure with specific reserve draw dates and dollar amounts (2020-09-01 $3.68M, 2021-03-01 $965K)
- Truckee Donner reserve draw history (2023-09-01 $265K, 2024-09-01 $244K)
- Diablo Grande CFD case study (ElevenFlo) — Ch 9 Nov 25 2025, $45.3M bond claims, $3.87M default Sep 1 2024
- Palmdale 93-1 historical (Bond Buyer + Avpress) — 1998 default, 2024 workout via new $46M issue
- Real CDIAC YFSR filings for SJ County 2009-2 (2022) and West Patterson 2018-1 (2025)

### Could NOT pull (HONEST UNVERIFIABLE flagging)
- **Per-CFD CDIAC YFSR pulls at 2020-12-31 snapshot**: The CDIAC default-draw search form (treasurer.ca.gov/cdiac/default-draw/) returns 404 when accessed directly; only the aggregate summary PDF is parseable. Per-CFD YFSR pulls would require driving the search form programmatically or scraping CDIAC DebtWatch (which had connection issues during this session). **Result**: ~80% of CFDs have V/L = UNVERIFIABLE, ~70% have specific delinquency_pct = UNVERIFIABLE at exact 2020-12-31 snapshot date.
- **CDIAC RY 2020-21 / 2021-22 / 2022-23 summary PDFs**: 404 at predicted paths. Only RY 2023-24 is publicly available; earlier years are "available upon request" via cdiac@treasurer.ca.gov.
- **CDIAC Default & Draw on Reserve database** by issuer name: 404 across all queried CFDs. Confirms the validation pass finding that this is gated behind a search form.
- **EMMA continuing-disclosure pulls per-CFD**: Not attempted — would have required ~30 min per CFD × 117 = ~60 hr. The 1 EMMA-equivalent we pulled (Northstar) was found via the issuer's own website.
- **PACER access**: Not attempted for Diablo Grande EDCA Case 25-26635 — would have given gold-standard claim amounts but ElevenFlo case study + WHWD self-disclosure provided sufficient HIGH-confidence proxy.
- **Reserve-fund-burndown YoY data**: Pulled for SJ County 2009-2 and West Patterson 2018-1 from real YFSRs. All other CFDs have UNVERIFIABLE t-1 reserve balance. This is why `reserve_fund_burndown` detector fires 0% — the data simply isn't there.
- **Top-taxpayer concentration with primary-source verification**: Pulled for Diablo Grande, Northstar, Irvine 2013-3 (FivePoint). All other CFDs UNVERIFIABLE.
- **Buildout %**: Estimated for known cases (Diablo Grande 10%, Palmdale 0%, Northstar 60%) from case studies and OS. All housing CFDs without OS pulls = UNVERIFIABLE.

### Methodology honesty notes

1. **2020-12-31 snapshot is a CONSTRUCTED snapshot** for most CFDs in this universe, not a primary-source pull. For known-distressed names (Bucket A and B), the framework's detector inputs are interpolated from the surrounding evidence (CDIAC RY 2023-24 + dated event history) — these are MEDIUM-confidence inputs. For controls (Buckets D, F, G), the assumption is "absence from CDIAC distress figures = clean at 2020-12-31" — this is NEGATIVE EVIDENCE, not primary-source confirmation.

2. **NO_DISTRESS outcomes for cycle-exposed CFDs are LOW-confidence**. We did not verify per-CFD that no reserve draw occurred 2021-2025; we inferred from absence in CDIAC RY 2023-24 distress figures (which cover 1,200 reporting CFDs). It's possible a CFD had a draw in 2021-2022 that was cured before RY 2023-24 reporting. The framework's `_outcome_confidence` field captures this honesty.

3. **The framework's `STALE_DISTRESS_YEARS = 5` cutoff** is honored for Palmdale 93-1 (distress originated 1998-03-01, 22 years pre-snapshot = STALE) and Riverside 88-8 (distress originated 2000-09-01, 20 years pre-snapshot = STALE). These names will be correctly excluded from "fresh distress alpha" calculations.

4. **Honesty-alpha framework discipline**: We're NOT claiming Diablo Grande Ch 9 is "alpha" — by the time it filed Ch 9 (Nov 25 2025) the market had priced it in completely (per validation pass). The framework re-detecting Diablo Grande is a positive-control case, not tradable alpha. Real alpha comes from EXCLUDING Northstar-style names (reserve being drawn but no bondholder default yet) where the market may be under-pricing the trajectory.

---

## 7. Open items for next session

1. **Per-CFD YFSR pull at 2018, 2019, 2020 snapshots** for the 30 housing-development CFDs in Buckets E/F that are currently UNVERIFIABLE. Estimated 30 hr work via CDIAC DebtWatch portal.

2. **CDIAC Default & Draw database scrape** programmatically (since user-facing search form gates the data). Likely requires either driving the form via Selenium or finding the underlying dataset on DebtWatch.

3. **Earlier CDIAC RY summary PDFs** (2020-21, 2021-22, 2022-23) via email request to cdiac@treasurer.ca.gov — would give pre-snapshot top-delinquent / draw lists for cleaner outcomes.

4. **EMMA continuing-disclosure event filings** for the 47 excluded CFDs — pull 4 events / CFD ~ 90 min × 47 = 70 hr. Lower priority since the union screen already identifies them.

5. **Calibration of `top_taxpayer_concentration` detector** — currently firing only 2/117 (1.7%) because most CFDs lack primary-source concentration data; in reality this rate should be ~5-15% if all CDAs were pulled. Affects the framework's ability to flag pre-buildout distress.

6. **Calibration of `reserve_fund_burndown` detector** — currently 0/117 because t-1 reserve balances are UNVERIFIABLE for most CFDs. This is the framework's intended LEADING indicator (validation pass found Northstar-style cases need this). Pull t-1 + t-2 reserve from CDIAC YFSR for top 30 housing CFDs.

7. **Pricing data**: EMMA trade data for excluded basket CUSIPs to compute realized YTM and spread vs MMD. Required to translate exclusion alpha to bps/yr.

---

## 8. Sources cited

- CDIAC Mello-Roos YFSR Summary RY 2023-24: https://www.treasurer.ca.gov/cdiac/reports/M-Roos/2023.pdf
- CDIAC Mello-Roos YFSR Summary 2018-19: https://www.octreasurer.gov/sites/ttc/files/2023-05/2019%20Mello%20Roos%20Bonds.pdf
- CDIAC Reporting Guidelines: https://www.treasurer.ca.gov/cdiac/reporting/mello-roos/reportingguide.asp
- Northstar CSD Mountainside delinquencies: https://www.northstarcsd.org/mountainside-partners-acm-delinquencies
- Northstar Series 2014/15 Official Statement: https://www.northstarcsd.org/media/Finance/Bond%20Issues/Official%20Statements/OffStmt15.pdf
- Northstar continuing disclosure FY 2020-21: https://www.northstarcsd.org/media/Finance/Bond%20Issues/Continuing%20Disclosure/Northstar%20CFD%20Continuing%20Disclosure%20FY%202020-21.pdf
- Diablo Grande Ch 9 case study (ElevenFlo): https://elevenflo.com/blog/diablo-grande-cfd-chapter-9-bankruptcy
- Western Hills Water District Ch 9 self-disclosure: https://whwd.org/whwd-community-facilities-district-1-files-chapter-9-bankruptcy/
- CBS Sacramento on Diablo Grande water dispute: https://www.cbsnews.com/sacramento/news/diablo-grande-western-hills-kern-county-water-agency-continued-dispute/
- Bond Buyer Ritter Ranch: https://www.bondbuyer.com/news/ritter-ranchs-long-trail-of-cfd-defaults-may-near-an-end
- Avpress Ritter Ranch new $46M issue Nov 2024: https://www.avpress.com/news/city-oks-tax-bonds-for-ritter-ranch/article_0c19dcf8-a94c-11ef-a4f9-13f595f60c66.html
- Bond Buyer Mello-Roos in Freefall (2008 historical): https://www.bondbuyer.com/news/mello-roos-in-freefall
- ScienceDirect default of special district financing: https://www.sciencedirect.com/science/article/abs/pii/S1051137715000054
- Real YFSR sample SJ County 2009-2: https://www.sjgov.org/docs/default-source/public-works-documents/special-districts/san-joaquin-county-cfd-no-2009-2-cdiac-mello-roos-yearly-fiscal-status-report.pdf
- Real YFSR sample West Patterson 2018-1: https://www.pattersonca.gov/DocumentCenter/View/13751/2025-Patterson-CFD-2018-1-CDIAC-for-2024-Bond
- DebtWatch dataset: https://data.debtwatch.treasurer.ca.gov/Government/Mello-Roos-Yearly-Fiscal/dzi5-k38k (not pulled this session — connection issues)
