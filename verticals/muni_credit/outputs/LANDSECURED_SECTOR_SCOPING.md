# CA Land-Secured / Mello-Roos CFD Muni — Sector Scoping

**Prepared**: 2026-05-28
**Framework**: Union-of-detectors exclusion screen (per detector-composition principles validated on CA NH / CCRC / hospital verticals)
**Companion files**: `data/landsecured_universe.json` (50 CFDs), `data/landsecured_initial_detector_data/*.json` (8 sample CFDs)

---

## TL;DR Report (orchestrator summary)

- **Universe sized**: 50 CFDs scoped against the full $16.3B / 1,177-CFD CA Mello-Roos market (RY 2023-24 CDIAC data). Bias toward Inland Empire / Central Valley / exurban housing CFDs + historical defaulters + boring school/library controls.
- **Testable detectors**: **5 high-confidence (data exists in CDIAC YFSR), 4 lower-confidence (require OS / continuing-disclosure pulls)**. Net 4-5 working detectors after honesty cuts.
- **Hypothesized exclusion rate**: **15-25% of CA CFD universe** (driven by ~12% delinquency-spike + ~3% reserve-draw/default + ~2% extreme V/L + ~2% extreme late-filer, with overlap).
- **Hypothesized honest TEY alpha**: **40-80 bps/yr** (lower bound than NH because (a) Teeter plan masking depresses fire signal, (b) CFD non-rated paper already prices wide ~150-250 bps vs MMD so exclusion alpha is a smaller marginal lift). CA TEY multiplier ~2.01× still applies.
- **Top 3 EXCLUDE**: Diablo Grande CFD No 1 (Ch 9 filed Nov 2025); Palmdale CFD No 93-1 (100% delinquency, $32M cum arrears); Northstar CSD CFD 1 ($41M cum arrears + 3 reserve draws RY23-24).
- **Top 3 CLEAN**: Irvine CFD No 2013-3 (FivePoint Great Park, 0.1% delinq on $904M par); Elk Grove USD CFD 1 (school CFD, 463x V/L); Roseville CFD No 1 (long-running master-plan, 36x V/L).
- **Open data gaps**: (1) per-CFD V/L requires AV+par from individual YFSR pulls — feasible but laborious for full 50; (2) build-out % and top-taxpayer concentration NOT in YFSR — requires OS / Continuing Disclosure Annual Report (CDA) parsing; (3) Teeter plan participation masks underlying delinquency for ~50% of CFDs.

---

## 1. Sector market context

### 1.1 Market size (CDIAC RY 2023-24, published Jan 2025)

| Metric | Value | Source |
|---|---|---|
| Total principal outstanding | $16.3B | CDIAC Mello-Roos YFSR Summary Figure 4 |
| Issues outstanding | 1,829 | Figure 1 |
| Unique CFDs | 1,177 | Figure 1 |
| Total underlying AV | $790.6B | Figure 4 |
| Total special tax due annually | $5.67B | Figure 7 |
| Total delinquent tax | $134.9M (+49.5% YoY) | Figure 9 |
| Delinquent parcels | 16,685 (-10.4% YoY) | Figure 10 |
| Defaults RY 2023-24 | 2 (both Truckee Donner) | narrative |
| Draws on reserve RY 2023-24 | 8 (3 Calexico + 3 Northstar + 2 Diablo Grande) | narrative |
| Compliance with mandatory YFSR | 98.1% | Figure 1 |
| Rated issues | 12.4% (S&P 9.2%, Moody's 0.7%, Fitch 0.6%) | Figure 2 |

**Concentration**: Top 10 counties by AV hold ~$641B (81% of total). Riverside ($111B AV, $3.6B debt), Orange ($100B AV, $2.9B debt), Sacramento ($98B AV, $1.2B debt), San Diego ($89B AV, $1.1B debt), San Bernardino ($34B AV, $1.1B debt), San Joaquin ($33B AV, $1.2B debt) are the largest active markets.

### 1.2 Default history (long view)

- **1990s baseline**: Sporadic single-CFD defaults during 1990-93 recession. CDIAC default-draw database has continuous reporting from 1993.
- **2000-2004**: Riverside County CFD No 88-8 (North A Street) defaulted serially 2000-2004, ultimately ~$6.2M principal non-payment.
- **2008-2012 wave**: The big one. Inland Empire + Central Valley housing-development CFDs collapsed as builders went bankrupt mid-buildout and home values fell below assessed value. Major CFD bondholder losses occurred. (Search-engine evidence is sparse — most distress was resolved via refundings, reserve draws, or workouts rather than headline-grabbing Ch 9 filings.)
- **2014-2019 recovery**: Reserve fund balances rebuilt across the sector; new issuance picked up. Most 2005-2008 vintage CFDs that survived the crisis fully amortized.
- **2020-2024 cyclical normalization**: Total delinquencies stayed under $100M/yr through 2022-23. RY 2023-24 saw +49.5% spike in delinquencies ($90M→$135M) — first major warning sign of post-2022 housing cycle stress.
- **2024-2025 emerging cycle distress**: Western Hills Water District (Diablo Grande CFD 1) defaulted on $3.87M in Sep 2024 and filed **Chapter 9 on Nov 25, 2025** — the first major CFD Ch 9 in years. 74.6% delinquency, $45.3M bond claims. Truckee Donner PUD CFD 04-1 filed 2 actual defaults RY 2023-24.

### 1.3 Structural risk drivers

| Driver | Mechanism | Severity |
|---|---|---|
| **Housing cycle exposure** | Builder Ch 11 mid-buildout strands lots → no parcel taxes generated → CFD revenue collapses | HIGH for 2005-2008 + 2019-2022 vintages |
| **Developer concentration** | Single homebuilder owns >50% of pre-buildout parcels; their bankruptcy = CFD bankruptcy | HIGH for new issuances |
| **Geographic exurbanism** | Inland Empire + Central Valley CFDs have weakest housing-market liquidity in downturns; AV can fall 30-50% | HIGH for IE / CV / exurban SD |
| **Non-rated paper** | 87.6% of issues unrated; bondholders rely on OS + YFSR not external surveillance | STRUCTURAL |
| **Tax-burden ceiling** | Total ad valorem + Mello-Roos generally capped at 2-2.5% of AV → CFDs have limited ability to raise rates after a delinquency spike | HIGH ceiling effect |
| **Limited-obligation security** | Special tax bonds are NOT general obligations — county/city is NOT on the hook beyond tax-roll collection | STRUCTURAL — no implicit backstop |
| **Foreclosure-redemption lag** | CA judicial foreclosure of CFD-delinquent parcels takes 18-30 months; in this window bonds rely on reserve fund | MEDIUM |

### 1.4 Credit-enhancement masking (KEY NH-vertical lesson applied here)

In the NH vertical, Cal-Mortgage insurance wraps decoupled operator credit from bond pricing. For CFD muni, **the equivalent is the Teeter Plan**. In Teeter counties, the county tax collector advances 100% of levied taxes to the CFD regardless of actual collection; the county absorbs the delinquency risk in exchange for collecting penalties.

**Impact on detector signal**:
- CFDs in Teeter counties report **zero unpaid taxes** even when underlying parcel delinquency is high
- `delinquency_spike` detector silently misses true distress
- Per CDIAC RY 2023-24 Figure 8, **Solano (most CFDs), San Joaquin (most), Santa Cruz (most), El Dorado (most) are Teeter** — so a large share of cycle-exposed Central Valley CFDs have masked delinquency
- Mitigation: cross-check CDIAC YFSR-reported delinquency against county tax-collector secured-property delinquency dashboards (county-level data, not per-CFD)

A second masking layer: **overlapping general-obligation debt is senior to CFD special tax in property foreclosure proceeds**. School-district GO and city/county GO are paid first. The `senior_lien_pressure` detector below tries to capture this — but the data is in the Continuing Disclosure Annual Report, not YFSR.

---

## 2. Proposed detector library

### Hard data sources (YFSR-directly-computable — HIGH confidence)

#### 1. `value_to_lien_collapse`
- **Definition**: V/L = AV from YFSR / (Principal Outstanding from YFSR + estimated overlapping debt from CDA). YELLOW <3x, RED <2x.
- **Rationale**: Industry standard threshold; LA City Mello-Roos issuance policy requires 3x minimum at issuance; collapse to <2x = severe equity erosion. Below 1x = lien value exceeds property value (Diablo Grande at 0.14x is canonical example).
- **Fire rate target**: <8% of universe should be <3x; <2% should be <2x. (Honest estimate: most CFDs at issuance >4x; only post-distress names drop below 3x.)
- **Expected precision**: 80%+ at <2x; 60%+ at <3x.
- **Primary data source**: CDIAC YFSR direct fields (AV + Principal Outstanding).
- **Caveats**: AV is from county equalized tax roll (lagged 6-18 months). For new issuances pre-buildout, "AV" is replaced with appraisal — bondholder underwriting risk shifts.

#### 2. `delinquency_spike`
- **Definition**: Current-year special-tax delinquency >5% OR rising 2+ years in a row. RED at >15%.
- **Rationale**: CDIAC's own 5% threshold for "elevated" delinquency. Top-10 list in RY 2023-24 all >5%. Diablo Grande 74.6% canonical.
- **Fire rate target**: <12% of universe (RY 2023-24: ~10% of reporting CFDs had >5%).
- **Expected precision**: 70%+ at 5% threshold; 90%+ at 15% threshold.
- **Primary data source**: CDIAC YFSR `Total Amount of Unpaid Special Taxes Annually` / `Total Amount of Special Taxes Due Annually`.
- **Caveats**: **Teeter Plan masking** — about half of CA counties operate Teeter, in which case YFSR reports zero unpaid. Detector must check `Teeter Plan` field and cross-reference with county-level delinquency stats.

#### 3. `reserve_fund_drawn`
- **Definition**: Bond reserve fund balance < reserve fund minimum balance in current YFSR, OR draw-on-reserve filed with CDIAC in last 12 months.
- **Rationale**: Reserve draw = the bond's last layer of self-protection has been breached. CDIAC requires 10-day notification.
- **Fire rate target**: <3% of universe (8 draws in RY 2023-24 / 1,829 issues = 0.44% per year).
- **Expected precision**: 90%+ (these are nearly-certain distress).
- **Primary data source**: CDIAC `Reserve Fund` + `Reserve Fund Minimum Balance` YFSR fields + CDIAC Default & Draw on Reserve database (separate filing).
- **Caveats**: Some CFDs use surety bonds rather than cash-funded reserves — the YFSR will show $0 balance which is NORMAL; need to check OS structure.

#### 4. `foreclosure_active`
- **Definition**: YFSR `Total Number of Foreclosure Parcels` > 0 OR `Date Foreclosure Commenced` within last 24 months.
- **Rationale**: Bondholder-initiated judicial foreclosure on delinquent parcels = lender-of-last-resort signal.
- **Fire rate target**: <5% of universe (RY 2023-24: 7 YFSRs reported active foreclosure on 8 parcels — surprisingly low; actual count is higher in cumulative terms).
- **Expected precision**: 70%+ (some active foreclosures resolve cleanly via redemption).
- **Primary data source**: CDIAC YFSR Foreclosure section.
- **Caveats**: Foreclosure activity = LAGGING signal — typically 12-24 months after first delinquency.

#### 5. `issuer_administration_concern` (late-filing variant)
- **Definition**: YFSR due (Oct 30) but not received within 90 days post-deadline. Identical logic to existing `late_filing.py` detector but adapted to CDIAC Mello-Roos calendar.
- **Rationale**: Per CDIAC RY 2023-24 Figure 13, 34 CFDs missed filing — including Folsom CFD 2014-1 with 5 missing reports (extreme administrative breakdown). Late filing predicts deeper governance issues. SEC-style late-filing detector worked in NH/CCRC.
- **Fire rate target**: <3% of universe (34 / 1,829 = 1.9% in RY 2023-24).
- **Expected precision**: 60%+ (some late filings are administrative oversight not credit deterioration; severity scales with # of missing reports).
- **Primary data source**: CDIAC Figure 13 in annual summary report.
- **Caveats**: Single missed report = noise; 3+ missed = strong signal.

### Softer data sources (require OS / CDA parsing — MEDIUM confidence)

#### 6. `buildout_stalled`
- **Definition**: Build-out % from latest Continuing Disclosure Annual Report (CDA) stuck below 70% with bonds outstanding 5+ years. Sharper variant: build-out % unchanged or down over last 2 CDAs.
- **Rationale**: Pre-buildout CFDs depend on developer paying special tax across undeveloped parcels; if buildout stalls, tax base never matures. 2008-12 wave was almost entirely stalled-buildout cases.
- **Fire rate target**: <10% of housing-development CFDs (very few in mature municipal-service CFDs).
- **Expected precision**: 70%+ — but only if filtered to housing-development project type.
- **Primary data source**: Continuing Disclosure Annual Reports (CDAs) filed on EMMA; OS at issuance.
- **Caveats**: **Build-out % is NOT in YFSR**. Requires per-CFD CDA pull. Honest assessment: scaling this to 50 CFDs requires meaningful manual work.

#### 7. `top_taxpayer_concentration`
- **Definition**: Single property owner pays >25% of CFD's special tax bill per latest CDA. RED at >50%.
- **Rationale**: Builder concentration risk. If top taxpayer is solvent homebuilder (e.g., FivePoint), concentration is tolerable; if top taxpayer is distressed (e.g., Diablo Grande's master developer), concentration is bond-killing.
- **Fire rate target**: ~15-20% of housing CFDs (this is structurally common pre-buildout).
- **Expected precision**: 40-50% standalone (NEEDS pairing with developer financial health to reach high precision).
- **Primary data source**: CDA Section listing top 10 taxpayers; OS at issuance.
- **Caveats**: Calibration question — new/pre-buildout CFDs almost always have >50% master-developer concentration (e.g., Roseville Creekview Phase 5 at ~100%). Detector should fire only when concentration AND (delinquency >2% OR build-out stalled OR developer in distress).

#### 8. `coverage_ratio_thin`
- **Definition**: Annual special-tax revenue (collected, not just due) / Annual debt service < 1.10x.
- **Rationale**: Most CFDs structure at 1.10x minimum coverage; collapse below = imminent reserve draw.
- **Fire rate target**: <5% of universe.
- **Expected precision**: 80%+.
- **Primary data source**: Derived from CDIAC YFSR (taxes due) + manual debt-service calc OR pulled directly from CDA.
- **Caveats**: Need to use COLLECTED tax (= due × (1 - delinquency)) not just due. Teeter plan masking distorts.

#### 9. `developer_bankruptcy`
- **Definition**: Top property owner (from CDA) has filed Ch 11 OR is publicly distressed (sub-investment-grade with deteriorating ratings) OR has been delisted.
- **Rationale**: Direct credit-chain trace. 2008-12 wave was entirely Lennar/Pulte-tier failures dragging CFDs down.
- **Fire rate target**: <5% of housing CFDs.
- **Expected precision**: 80%+ (very strong signal when fires).
- **Primary data source**: CDA top-taxpayer list + Bloomberg/Moody's/S&P on each named developer.
- **Caveats**: Requires entity resolution between CDA-listed developer entity (often LLC) and parent public-co. Worth the work for top 20 housing CFDs.

### Detectors NOT proposed (intentionally cut)

- **senior_lien_pressure (overlapping debt / total tax % AV)**: Sounds compelling but the 2% rule is a CONSUMER protection (limits new CFD formation), not a bond-credit threshold. Cutting because the data is hard to pull and the precision is unclear. Re-evaluate if mature.
- **issuer-rated downgrade**: 87.6% of CFDs are unrated, so rating-action detector misses 88% of universe — fails the framework's coverage requirement.
- **CFD-OS-language opacity scoring**: Would be a "comprehensive score in disguise" — too broad, low precision.

### Detector composition summary

| Detector | Data source | Fire rate (estimated) | Expected precision | Confidence in detector design |
|---|---|---|---|---|
| value_to_lien_collapse | CDIAC YFSR direct | 8% (<3x) / 2% (<2x) | 60% / 80% | HIGH |
| delinquency_spike | CDIAC YFSR direct | 10-12% | 70-90% | HIGH (with Teeter caveat) |
| reserve_fund_drawn | CDIAC YFSR + Default DB | 1-3% | 90% | HIGH |
| foreclosure_active | CDIAC YFSR direct | 4-5% | 70% | HIGH |
| issuer_administration_concern | CDIAC Figure 13 | 2-3% | 60% (severity-scaled) | HIGH |
| buildout_stalled | CDA pull | 5-10% (housing only) | 70% | MEDIUM (data-pull dependent) |
| top_taxpayer_concentration | CDA pull | 15-20% | 50% standalone | MEDIUM (calibration needed) |
| coverage_ratio_thin | YFSR-derived | <5% | 80% | MEDIUM (Teeter distorted) |
| developer_bankruptcy | CDA + corp credit DB | <5% (housing only) | 80% | MEDIUM (entity-resolution work) |

**Honest scope cut**: build the union screen on **detectors 1-5** (all YFSR-directly-computable) for the V1 run. Detectors 6-9 require manual CDA parsing per CFD and should be added as a V2 enhancement after V1 alpha is validated.

---

## 3. Universe

50 CFDs in `data/landsecured_universe.json`. Composition:

| Bucket | Count | Examples |
|---|---|---|
| Historical / current defaulters | 7 | Diablo Grande 1, Palmdale 93-1, Calexico 2005-1, Truckee Donner 04-1, Northstar CSD 1, Riverside Co 88-8, Long Beach 5 |
| Top-delinquency RY 2023-24 (>5% unpaid, not in default bucket) | 6 | Imperial 2004-2, Imperial Co 02-1, Western Hills, Fairfield 2007-1, Rio Alto 2011-1, Rocklin 11 |
| Late-filer RY 2023-24 (Figure 13 of CDIAC) | 14 | Folsom CFD 2014-1 (5 missing), Moreno Valley 87-1, Rocklin Stanford Ranch 3, Brea 1996-1, Brea 2008-2, Newport-Mesa USD 90-1, CSCDA CFDs (4 variants), Menifee 2021-1, Mt Diablo USD 1, Galt 2020-2, Chino 2005-1, Fontana 11, Fontana 37, San Diego 2 |
| Cycle-exposed housing CFDs (Inland Empire / Central Valley / exurban) | 8 | Beaumont 93-1, Lake Elsinore 2007-5, River Islands 2003-1, Lathrop 2006-1, West Patterson 2018-1, SJ County 2009-2, Sacramento N Natomas 97-01, Roseville CFD 1 |
| Live new issues (test fresh data) | 2 | Roseville Creekview Phase 5 (Nov 2025), West Patterson 2018-1 (live 2024-25 YFSR) |
| Boring controls (school/library/service) | 7 | Elk Grove USD 1, Irvine USD 09-1, Santa Cruz Libraries 2016-1, Perris Union HSD 92-1, Twin Cities Police 2008-1, Yolo 1989-1, Belvedere-Tiburon Library 1995-1 |
| Anchor CLEAN candidates (housing but high quality) | 3 | Irvine 2013-3 (Great Park / FivePoint), Roseville CFD 1, Folsom 11 |
| Special situations | 3 | South Lake Tahoe Rec JPA (high parcel delinq but high V/L), Successor S Tahoe RDA 2001-1, Altadena Library 2020-1 (Eaton Fire post-disaster) |

Total: 50 CFDs covering ~$2.5B+ of CFD par across the riskiest segments of the CA market.

---

## 4. Pricing dynamics

**Current rate environment (as of late May 2026)**:
- MMD AAA muni: 10y ~2.84%, 30y ~4.25%
- IG-rated CA CFD muni (BBB+/A-): MMD +50-100 bps → ~3.34-3.84% (10y) / ~4.75-5.25% (30y)
- Non-rated CA CFD muni: MMD +150-250 bps → ~4.34-5.34% (10y) / ~5.75-6.75% (30y)

**Empirical anchor from Roseville Creekview Phase 5 OS (Nov 25, 2025, NOT RATED)**:
- 2030 term (5y): 4.00% YTM = MMD 5y ~2.40% + 160 bps spread
- 2035 term (10y): 4.25% YTM = MMD 10y ~2.84% + 141 bps
- 2045 term (20y): 4.77% YTM = MMD 20y ~3.55% + 122 bps
- 2055 term (30y): 4.97% YTM = MMD 30y ~4.25% + 72 bps
- Average non-rated CFD spread: **~120 bps over MMD AAA**

**TEY math** (CA top-bracket TEY multiplier = 2.01×):
- Non-rated 30y CFD at 4.97% = **TEY ~9.99%**
- IG-rated 30y CFD at 4.75% = **TEY ~9.55%**
- AAA muni 30y at 4.25% = TEY ~8.54%
- CFD TEY premium over AAA: **~100-145 bps TEY**

**Exclusion alpha translates honestly**: framework's 4 bps/pp deterioration-rate spread × 10-15 pp deterioration-rate gap = **40-60 bps muni alpha** × 2.01 TEY = **80-120 bps TEY/yr** if framework works as well as NH did.

**Critical caveat — the non-rated structural illiquidity**: 87.6% of CA CFDs are non-rated. Bid-ask on non-rated retail-targeted CFD bonds is often 50-200 bps — wide enough to eat much of the exclusion alpha if not held to maturity. Strategy is **buy-and-hold institutional / HNW**, not active trading.

---

## 5. Initial qualitative read — top 3 EXCLUDE and top 3 CLEAN

### EXCLUDE basket (3 names, all immediately flag-evident)

| CFD | Why exclude | Detectors that fire |
|---|---|---|
| **Western Hills Water District Diablo Grande CFD No 1** (Stanislaus Co) | Ch 9 filed Nov 25 2025. 74.6% delinquency. $45.3M bond claims. AV $5.3M against $38.7M par (V/L 0.14x). | value_to_lien_collapse (RED), delinquency_spike (RED), reserve_fund_drawn (RED), foreclosure_active (RED), buildout_stalled (RED), top_taxpayer_concentration (RED), developer_bankruptcy (RED). 7/7 housing fires. |
| **Palmdale CFD No 93-1** (LA Co) | 100% unpaid in RY 2023-24. $32.3M cumulative arrears against $22.7M outstanding par (arrears > par by 42%). | delinquency_spike (RED extreme), implied reserve_drawn (need verification). |
| **Northstar Community Services District CFD No 1** (Placer Co) | $41M cumulative delinquency. 3 draws on reserve in RY 2023-24 (37.5% of all CA reserve draws). 65.4% current delinquency. | delinquency_spike (RED), reserve_fund_drawn (RED, severity HIGH x3), foreclosure_active (LIKELY). |

### CLEAN basket (3 names, immediately strong)

| CFD | Why clean | All detectors quiet |
|---|---|---|
| **Irvine CFD No 2013-3** (Orange Co, Great Park Neighborhoods) | $904M par, $940K delinquent special tax = 0.1% delinquency. FivePoint Holdings (NYSE: FPH) master developer, solvent. Coastal OC market. | All 5 hard detectors quiet. |
| **Elk Grove USD CFD No 1** (Sacramento Co) | School-district CFD. $105M par against $48.7B AV = V/L 463x. Diversified residential tax base across entire USD. | All detectors quiet. School-CFD structural strength. |
| **Roseville CFD No 1** (Placer Co) | Long-running master-planned community CFD. 79% original principal paid down. V/L 35.8x. Multiple successful refundings 2006-2015. | All detectors quiet. Mature buildout. |

---

## 6. Initial alpha hypothesis

**Exclusion rate hypothesis** (V1 hard-detector union):
- value_to_lien_collapse at <3x: ~8% of universe
- delinquency_spike at >5%: ~10-12% (much lower in Teeter counties — actual signal closer to 6-8%)
- reserve_fund_drawn last 12mo: ~1-3%
- foreclosure_active: ~4-5%
- issuer_administration_concern (3+ missing filings): ~1%
- **Union overlap-adjusted**: **15-25% exclusion rate** (overlap is high — names that hit V/L collapse also hit delinquency)

**Deterioration-rate hypothesis**:
- Random CA CFD universe 3yr deterioration rate (any form of distress: missed payment, downgrade, reserve draw, late filing >2 reports): estimated 6-10% (RY 2023-24 saw 1.9% late filing + ~0.5% defaults+draws = ~2.4% in single year)
- Excluded basket 3yr deterioration rate: 40-60% (these are the names already in distress)
- Clean basket 3yr deterioration rate: 2-4%
- **Implied excess deterioration rate gap (clean vs unscreened)**: ~3-6 pp/yr

**TEY alpha translation**:
- 3-6 pp deterioration-rate gap × ~4 bps/pp ≈ **12-24 bps muni alpha**
- × CA TEY multiplier 2.01 = **24-48 bps TEY/yr**
- Plus implicit-distress-spread compression on rescreened-clean names: another ~20-30 bps muni / ~40-60 bps TEY
- **TOTAL honest TEY alpha range: 60-100 bps/yr**

This is **lower than the NH backtest** (~115 bps in-sample, ~45 bps in COVID stress) for two reasons:
1. **Teeter masking** in ~half of cycle-exposed CFDs reduces detector recall
2. **CFD non-rated paper already prices the average distress level** in its ~120 bps non-rated spread, so the marginal alpha from exclusion is the GAP between average distress and below-average distress, not the absolute exclusion of distress.

The framework adds value if and only if **the market is mispricing within the non-rated bucket** — pricing distressed CFDs only modestly wider than clean CFDs. Pre-evidence from Diablo Grande suggests this IS happening (bonds traded well above zero until very late in the distress timeline).

---

## 7. Open data-gap questions for next session

1. **Per-CFD individual YFSR pulls** for the 50 names — at the CDIAC DebtWatch portal — to populate V/L and delinquency for each. Manual effort ~2 hrs per CFD = ~100 hrs for full population, but ~50% of names already have data from CDIAC Figure 5/7/9/10 aggregates pulled here.

2. **OS / CDA pulls for top 20 housing CFDs** to populate build-out %, top-taxpayer concentration, coverage ratio. This unlocks detectors 6-9. ~3 hrs per CFD = ~60 hrs.

3. **Teeter county cross-checks**: pull county tax-collector secured-property delinquency dashboards for Solano, San Joaquin, Santa Cruz, El Dorado, Placer to compute UNDERLYING delinquency for Teeter-masked CFDs. ~1 hr per county = ~5 hrs.

4. **EMMA continuing-disclosure event filings** for the universe: scrape EMMA for "material event" filings (rating actions, missed debt service, reserve draws not yet on CDIAC) for the 50 CFDs. ~30 min per CFD = ~25 hrs.

5. **Historical defaulter list expansion**: full CDIAC Default & Draw on Reserve database export (if available) would give us the full 2008-2012 default population for backtest baseline. Currently relying on aggregate references.

6. **Developer entity resolution** for top 20 housing CFDs: map CDA-listed master developer (typically an LLC) to parent public/private credit. Names to look for: FivePoint, Lennar, Pulte, KB Home, Brookfield, Cambay Group, Newland Communities.

7. **Calibration of `top_taxpayer_concentration` detector**: needs threshold tuning so pre-buildout CFDs (where 100% master-developer concentration is normal) don't auto-fire. Proposed rule: fire only if concentration >50% AND (buildout >3yr post-issuance OR delinquency >2% OR developer in distress).

8. **Pricing data**: spread vs MMD AAA for each CFD's most recent traded series — pull from EMMA trade data. Required to compute realized alpha.

---

## Sources cited

- CDIAC Mello-Roos YFSR Summary RY 2023-24 (Jan 2025): https://www.treasurer.ca.gov/cdiac/reports/M-Roos/2023.pdf
- CDIAC Mello-Roos YFSR Report 2018-19 (CDIAC No. 21.06): https://www.octreasurer.gov/sites/ttc/files/2023-05/2019%20Mello%20Roos%20Bonds.pdf
- CDIAC Reporting Guidelines (Mello-Roos): https://www.treasurer.ca.gov/cdiac/reporting/mello-roos/reportingguide.asp
- CDIAC sample YFSR form: https://www.treasurer.ca.gov/cdiac/reporting/mello-roos/sample.pdf
- Real YFSR sample: San Joaquin County CFD No 2009-2 (CDIAC #2012-0441): https://www.sjgov.org/docs/default-source/public-works-documents/special-districts/san-joaquin-county-cfd-no-2009-2-cdiac-mello-roos-yearly-fiscal-status-report.pdf
- Real YFSR sample: West Patterson CFD 2018-1 (CDIAC #2024-0147, FY 6/30/2025): https://www.pattersonca.gov/DocumentCenter/View/13751/2025-Patterson-CFD-2018-1-CDIAC-for-2024-Bond
- Roseville Creekview Phase 5 CFD 1 Series 2025 OS: https://www.roseville.ca.gov/Documents/Departments/Finance/Special%20Taxes%20and%20Assessments/CFD%20Mello%20Roos%20Bond%20Districts/Creekview%20Phase%205%20CFD%201/Official%20Statement%20Series%202025.pdf
- Diablo Grande Ch 9 case study (ElevenFlo, Nov 25 2025): https://elevenflo.com/blog/diablo-grande-cfd-chapter-9-bankruptcy
- CDIAC Default & Draw on Reserve Reports by Issue Name: https://www.treasurer.ca.gov/cdiac/default-draw/
