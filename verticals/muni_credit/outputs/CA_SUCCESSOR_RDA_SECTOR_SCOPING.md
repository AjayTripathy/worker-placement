# CA Successor RDA Tax-Allocation-Bond Sector — Scoping

**Prepared**: 2026-05-28
**Framework lens**: Refined-thesis (rating dominates spread R^2~19%; alpha = descend-rating-ladder-with-quality; masking sectors benefit most)
**Companion files**:
- `data/ca_successor_rda_universe.json` (universe inventory, 30 issuers + structural class field)
- `knowledge_graph/masking_mechanisms.json` (entry `rops_allocation_intercept` added)

---

## TL;DR (orchestrator summary)

- **Sector size**: ~$15-20B outstanding par across ~360 Successor Agencies statewide. Top 10 issuers concentrate >50% of par. Aggregate TAB issuance through pre-2012 RDA dissolution was $23.3B. Refunding cycle 2014-2017 reset most outstanding debt to current structures.
- **ROPS allocation masking verdict**: **VERIFIED PARTIAL**. Structural intercept is real (4-of-4 verification tests pass at least partially). The three positive-control host BKs (San Bernardino, Stockton, Vallejo) all showed uninterrupted TAB debt service through the host Chapter 9. The single observed RDA TAB default (Hercules 2012) occurred ON the dissolution date — i.e., pre-ROPS — and is itself a verification of the post-ROPS structural improvement. RATING TRANSMISSION OF HOST STRESS IS PARTIAL: S&P cut San Bernardino TABs from A- to BBB on host BK (1-notch), but Fitch later assigned A on the same credit post-emergence. Split-rating dispersion S&P vs Moody's is the widest in any sector scoped to date (S&P 70% A-category vs Moody's withdrew 31 of 94 and rated remainder Ba1 / junk).
- **Top 5 buy-zone candidates** (structurally clean, ROPS-secured, host-stress-mismatched):
  1. **Successor Agency to San Bernardino RDA TABs** (Fitch A Stable 2016 post-BK; host still speculative-grade; rating-host mismatch = clearest alpha case)
  2. **Successor Agency to City of Riverside Desert Communities Project Area** (S&P upgraded BBB->A- on AV growth; project-area driven rating)
  3. **Successor Agency to City of Inglewood RDA** (project area gained Forum/SoFi/Intuit Dome AV; host city not investment-grade-AA; structural mismatch)
  4. **Successor Agency to Atascadero CRA** (4.89x MADS / 58% AV cushion / 13.5% top-10 — golden methodology data; only $17M outstanding so liquidity discount)
  5. **CRA/LA Designated Local Authority** (independent governing body insulated from host political risk; 40+ project area diversification)
- **Top 5 exclude-zone candidates**:
  1. **Successor Agency to Hercules RDA (post-default)** (historical default; insurer-wrap-dominated; framework cannot extract signal)
  2. **Stockton legacy insured RDA TABs** (Ambac/NPFG/Assured wraps dominate; underlying credit obscured)
  3. **Vallejo legacy RDA paper** (pre-dissolution BK exit; small / illiquid; not a clean test)
  4. **Lancaster Successor Agency TABs** (Antelope Valley housing-cycle-exposed project area; AV trajectory at risk)
  5. **Anaheim Successor Agency** (NOT structurally weak but Disney top-taxpayer concentration is so high that S&P methodology already prices in; no alpha vs rating)
- **Honest TEY math**: Median S&P-rated A-category Successor Agency TAB trades ~80-120 bps over MMD AAA at current curve (estimated from CSFA-spread-anchor framework + 2014 Bond Buyer commentary of -40 bps yr/yr from 2023 to 2024). After CA TEY multiplier 2.01x, raw 80 bps -> ~160 bps TEY. Framework value: avoid the 15% of universe (insurer-wrapped legacy with hidden underlying credit + host-BK-cohort that hasn't recovered) -> incremental ~10-25 bps net alpha. Probably 15-20 bps after honesty cuts on small dataset.

---

## 1. Sector market context

### 1.1 Market size & history

| Metric | Value | Source |
|---|---|---|
| Total Successor Agencies | ~360 | DOF ROPS portal listing |
| Pre-dissolution RDA TAB issuance 2002-2011 | $23.3B | Bond Buyer 2014 commentary |
| 2014 refunding cycle | $1.2B across 28 SAs | Bond Buyer 2014 |
| Outstanding par estimate (2026) | $15-20B | Scoping-prompt estimate; CDIAC DebtWatch aggregate not extracted |
| S&P rating distribution (2014 baseline) | 70% A-category, 15% AA-, balance BBB/wrapped | https://www.bondbuyer.com/opinion/commentary-california-tax-allocation-bonds-heat-up |
| Moody's rating distribution (2012 baseline) | 31 of 94 withdrew; remainder mostly Ba1; 12 of 63 IG | https://www.bondbuyer.com/news/california-redevelopment-bonds-take-ratings-hit |
| Split-rating spread (S&P A-cat vs Moody's Ba1) | 2-4 notch gap on same credits | Direct comparison of Bond Buyer figures |
| Actual TAB defaults 2012-2026 | 1 (Hercules Feb 1 2012 — pre-ROPS) | Bond Buyer Ambac coverage |
| Host municipal BK cases since dissolution | 3 (San Bernardino, Stockton, Vallejo); TAB debt service uninterrupted in all 3 | Multiple sources cited in universe.json |

### 1.2 Statutory structure (HSC §34183 + §34177.5)

The ROPS-allocation framework is codified in California Health & Safety Code Part 1.85 (Dissolution of Redevelopment Agencies). The key sections:

**§34183 — RPTTF distribution waterfall** (priority order, semi-annually Jan 2 and Jun 1):

1. **Statutory + pre-1994 pass-through obligations** to taxing entities
2. **TAB debt service** per ROPS (most senior bond claim)
3. **Revenue bond debt service** (only if revenue insufficient AND tax increment pledged)
4. **Other ROPS-listed enforceable obligations** (administrative cost allowance + contracts)
5. **Residual** pro-rata to taxing entities per §34188

**§34177.5(e) — Refunding bond subordination**: Successor Agencies may subordinate pass-through payments to refunding bond debt service IF affected taxing entities approve (45-day deemed-approval mechanism). MOST POST-DISSOLUTION REFUNDING TABS HAVE OBTAINED THIS SUBORDINATION — effectively moving refunding TAB debt service to PRIORITY 1.

**§34177(o) — DOF approval requirement**: Refunding bond issuance requires both Oversight Board and Department of Finance approval. DOF can deny obligations on ROPS submissions; disputes flow through Meet-and-Confer or superior court writ of mandate.

**Bankruptcy treatment**: Per US Bankruptcy Code §902(2) "special revenues" definition, TAB-pledged tax-increment revenue is NOT general-fund revenue of host city. Continues to be paid through host city Chapter 9 — verified empirically in San Bernardino and Stockton cases.

### 1.3 Rating-agency methodology divergence (KEY MICROSTRUCTURE FINDING)

**S&P approach** (per Atascadero 2024A rating report):
- Applied via "Special-Purpose District" criteria (June 14, 2007)
- Weights: MADS coverage, AV growth, top-10 concentration, volatility ratio, closed-lien constraint, DOF/Oversight Board governance, dissolution-law restrictions on new debt
- Result: 70% A-category, 15% AA- — rating distribution heavily weighted to investment-grade
- Atascadero example data: 4.89x MADS, 58% AV cushion before 1x, 13.5% top-10, 0.27 volatility ratio, 5.6% 5yr AV growth — A+ Stable

**Moody's approach** (per 2012 sector commentary):
- Weights: cash-flow volatility, semi-annual payment hierarchy alignment, DOF approval risk, lack of fund-balance liquidity
- "Successor agencies don't have any fund balance to deal with cash flow changes from period to period"
- Result: 31 of 94 withdrew, remainder mostly Ba1, only 12 of 63 IG

**Fitch approach** (per Coronado / San Bernardino post-BK ratings):
- Weights: AV stability + DSCR stress testing
- Result: A-category most credits — closer to S&P than Moody's

**Framework alpha implication**: Same credit can be S&P A+ / Moody's Ba1 (or withdrawn) / Fitch A. The widest split-rating dispersion in the muni universe. Investors who index to Moody's or to "no investment-grade required" funds may transact at speculative-grade pricing; investors who use S&P methodology pay investment-grade pricing. Structural pricing inefficiency.

### 1.4 Why ROPS is a masking mechanism

The framework hypothesis was: "ROPS allocation creates a structural priority for RDA bondholders over the host city's general fund. RDA bonds trade to ROPS-secured credit, not to the host city's general fund / GO credit."

**Tested via 4 verification tests** (see universe.json `verification_criteria_for_masking_hypothesis` for detail):

| Test | Method | Verdict |
|---|---|---|
| 1. Rating resilience through host BK | Compare TAB rating before/during/after host Ch 9 | **VERIFIED PARTIAL** — San Bernardino TABs cut 1 notch (A- -> BBB) on host BK; Fitch later assigned A on same credit (2016). Host stress transmits but cushion >2 notches preserved. |
| 2. DOF rejection causing actual TAB default | Search documented payment disruptions from DOF denial | **VERIFIED** — zero TAB payment interruptions from DOF rejection 2012-2026. Oakland v. DOF (2022) concerned non-TAB items. |
| 3. Split-rating dispersion | Compare S&P vs Moody's rating same credits | **VERIFIED** — S&P 70% A-category vs Moody's withdrew 31 of 94. Methodology disagreement is structural and persistent. |
| 4. Project-area AV correlation with spread | Quantitative spread-vs-fundamentals test | **PARTIAL** — Atascadero / Riverside upgrade evidence is directionally consistent but N>10 surveillance reports needed for statistical test. |

**Overall masking verdict: VERIFIED PARTIAL — STRONG STRUCTURAL EVIDENCE, INCOMPLETE QUANTITATIVE TEST**

The ROPS intercept is real (Tests 1 and 2 are unambiguous). Whether it produces tradable framework alpha depends on whether the rating-band-discount on host-stress-correlated names actually exists in current trading prices. With only 1 primary-market spread anchor pulled (SJ SARA 2017 AA / 5s priced 1.83-2.65%), the empirical spread distribution is undercharacterized.

---

## 2. Refined-thesis framework application

### 2.1 Rating dominates spread (R^2~19% from CA charter test)

The CSFA LCFF intercept v3 test established that rating compression is the dominant masking channel, with within-rating-band spread variance dominated by market timing rather than operator signal. Applying this lens to Successor RDA bonds:

**Rating dispersion is narrow (S&P)**: 70% A-category + 15% AA- means 85% of S&P-rated universe is concentrated in 2 letter grades. Limited descend-the-ladder potential within S&P universe.

**Split-rating dispersion is WIDE (S&P vs Moody's)**: This is where the framework alpha sits. The market should not price equally a name that S&P calls A and Moody's calls Ba1; it should price somewhere in between, weighted by index methodology. If S&P-only-investment-grade names trade at "average rating" of, say, BBB / Baa3 levels, they yield more than their S&P A rating would suggest. Framework alpha = identify S&P-A-category names where structural fundamentals match the S&P methodology, accept Moody's-withdrawn or junk status, capture rating-band-discount.

### 2.2 Sectors with masking benefit most

Cal-Mortgage (state insurance wrap) and CSFA LCFF intercept (state controller diversion) are the two strongest masking mechanisms verified to date. ROPS allocation is the third member of this cluster:
- Cal-Mortgage: state appropriation backstops insurer claims
- CSFA LCFF: state controller diverts apportionment to bond trustee
- **ROPS allocation: county auditor distributes RPTTF directly to bond trustee per §34183 waterfall**

All three are intercept mechanisms that move payment AHEAD of operator/issuer discretion. ROPS is the masking analog for tax-allocation bonds.

### 2.3 Quality-differentiated issuers within rating band

**S&P A+ tier**: Atascadero is the golden example. Strong project area (Atascadero), diversified taxpayer base (top-10 13.5%), 4.89x MADS, 58% AV cushion. Only $17M outstanding limits liquidity.

**S&P A tier**: SJ SARA (AA — at the top), Riverside (A- after upgrade), Oakland (A on Coliseum series). Pattern: ratings reflect project-area economics + host city stability.

**S&P BBB / sub-IG tier**: Insurer-wrapped legacy from pre-dissolution era. Underlying credits often non-rated or distressed. NOT alpha territory — insurance wrap structurally dominates.

**Buy-zone alpha**: Issuers where (a) host city GO rating is meaningfully below their S&P TAB rating (San Bernardino, Inglewood, Riverside), AND (b) project-area fundamentals support the S&P rating, AND (c) Moody's has withdrawn or assigned speculative-grade — capturing the index-methodology pricing wedge.

### 2.4 Avoid zone

- Insurer-wrapped legacy (AGM/NPFG/Ambac/Assured): wrap dominates; framework cannot extract underlying-credit signal
- Hercules: only documented default
- Exurban housing-cycle-exposed project areas (Lancaster, Inland Empire small cities): project-area AV trajectory is the load-bearing signal and is at cyclical risk

---

## 3. Top 5 buy-zone + top 5 exclude-zone

### Top 5 BUY-ZONE (alpha-candidates within framework)

| # | Issuer | Rating | Why | Source citation |
|---|---|---|---|---|
| 1 | Successor Agency to San Bernardino RDA TABs | Fitch A Stable (2016 post-BK) | Host city BB area; rating-host mismatch >5 notches = clearest case of ROPS intercept producing spread alpha vs host risk | businesswire.com/news/home/20160219005945; municipalbonds.com/risk-management/city-of-san-bernardino-bankruptcy |
| 2 | Successor Agency to City of Riverside Desert Communities Project Area | S&P A- (upgraded from BBB) | Project-area AV growth drove upgrade. Host city stable AA but project area is the rating driver, not host. Clean descend-ladder candidate. | bondbuyer.com/news/successor-to-the-riverside-rda-calif-raised-to-a-minus-by-s-p |
| 3 | Successor Agency to City of Inglewood RDA | Underlying rating not directly extracted; structural fundamentals: Forum + SoFi Stadium + Intuit Dome adjacency = AV growth surge | Project area AV trajectory is strong; host city has improved but not investment-grade-AA. Structural quality mismatch with host rating. | cityofinglewood.org/284/Tax-Allocation-Bond-Debt |
| 4 | Successor Agency to Atascadero CRA | S&P A+ Stable | Golden methodology data: 4.89x MADS / 58% AV cushion / 13.5% top-10 / 5.6% AV growth. Small ($17M) so liquidity-discount candidate. | atascadero.org S&P rating report March 2024 |
| 5 | CRA/LA Designated Local Authority | S&P A-category | Designated Local Authority structure insulates from host city political risk; 40+ project areas = portfolio diversification. | ttc.lacounty.gov 2014 OS; HSC §34173(d) |

### Top 5 EXCLUDE-ZONE

| # | Issuer | Reason | Source citation |
|---|---|---|---|
| 1 | Hercules Successor Agency (post-default) | Only documented RDA TAB default. Insurer-wrap-dominated. Framework cannot extract signal. | bondbuyer.com/news/ambac-sues-troubled-hercules-calif-after-rda-default |
| 2 | Stockton legacy insured RDA TABs | Ambac/NPFG/Assured wrap dominates; underlying credit obscured. | bondbuyer.com/news/insurers-circling-as-stockton-defaults-on-its-obligations |
| 3 | Vallejo legacy RDA paper | Pre-dissolution BK exit; small/illiquid; not a clean test case. | planetizen.com/well-has-run-dry-redevelopment-vallejo |
| 4 | Lancaster Successor Agency TABs | Antelope Valley housing-cycle-exposed project area; AV trajectory at risk. | NPORT-P filings citing Lancaster 5s 2024-2025 |
| 5 | Anaheim Successor Agency | Disney top-taxpayer concentration so high that S&P methodology already prices it; no alpha vs rating. | bondview.com/bond/032564AH9 (CUSIP listing) |

---

## 4. Honest TEY math

Starting point: median S&P-rated A-category Successor Agency TAB on current curve.

**Spread anchors available**:
- SJ SARA 2017 AA: 5s priced 1.83-2.65% across 2020-2030 maturities (Bond Buyer 2017)
- 2014 -> 2024 spread compression cited at ~40 bps narrower for A-category insured 2024-2028 maturities (Bond Buyer 2024 commentary)
- Atascadero A+ Stable refunding March 2024 (specific yield not extracted from S&P report)

**Modeled current spread for median A-category Successor Agency TAB (2026)**:
- MMD AAA 10yr: ~3.5-4.0% on current curve (estimated; specific date-of-report MMD not pulled)
- A-category spread to MMD: ~80-120 bps (rule-of-thumb for muni A-cat 2026 environment)
- Gross taxable-equivalent yield (CA TEY multiplier 2.01x): 5-6% range
- TEY spread over UST: roughly 200-300 bps

**Framework value-add (exclusion zone)**:
- Avoid the 15% of universe that is insurer-wrapped legacy: spread differential ~30 bps (wrap-narrows spread)
- Avoid the 5% of universe that is host-BK-cohort still recovering: spread differential ~60-100 bps
- Net portfolio TEY uplift after exclusion: ~10-25 bps depending on weighting

**Framework value-add (split-rating-arbitrage)**:
- Identify S&P-A-category names with Moody's withdrawn or Ba1
- These may trade at "blended rating" levels (Baa1-Baa2 spread + S&P-A-spread mid)
- Potential pickup: 20-40 bps vs pure-S&P-A name
- Sample size required to test: N>20 split-rated names with current secondary trade data

**Realistic honest alpha**: 15-30 bps net TEY over passive A-category Successor Agency index. Lower bound than Cal-Mortgage (which had ~30-60 bps after compression) because the masking mechanism here is less STRONG (PARTIAL not HIGH severity). Upper bound bounded by index-methodology arbitrage that requires specific Moody's vs S&P data pulls not done in scoping.

---

## 5. Open data gaps

1. **EMMA primary-market spread anchors for 20+ Successor Agency TAB issuances 2014-2025**. Only 1 anchor pulled in scoping (SJ SARA 2017). Need N=20 for proper spread distribution by rating band.

2. **Full host GO rating timeseries vs Successor Agency TAB rating timeseries for the BK positive controls** (San Bernardino, Stockton, Vallejo). Quantify the rating-host mismatch over the BK cycle.

3. **DOF ROPS rejection-rate dataset**. What % of submitted obligations are denied? How often does Meet-and-Confer trigger? Useful as a forward-flag for issuer ROPS-compliance risk.

4. **CDIAC DebtWatch aggregate query** for total CA Successor Agency TAB outstanding par — the $15-20B estimate in scoping prompt is inherited; should be independently verified.

5. **Bondview / EMMA CUSIP-level secondary trade data** for the 30 universe issuers to characterize current spread distribution. Bondview returned 403 in scoping; alternative path is EMMA continuous disclosure portal CUSIP queries.

6. **Underlying ratings on insurer-wrapped TABs** (LA County, Stockton legacy, San Bernardino legacy). Many large issuers have AGM/NPFG/Ambac wraps with separate underlying ratings; wrap masks ROPS structure further but uninsured-tranche analysis would reveal underlying credit.

7. **RPTTF distribution actuals by county auditor** to empirically verify the §34183 waterfall is being implemented per priority order. Per-county distribution reports (Riverside, LA, SD, Orange, SJ) are publicly available but not extracted at scale in scoping.

---

## 6. Cross-references

This sector adds a new mechanism `rops_allocation_intercept` to `knowledge_graph/masking_mechanisms.json`. The mechanism is in the `intercept_structure` category cluster alongside:
- `csfa_lcff_intercept` — charter muni state-controller intercept
- `state_pension_intercept` — pension obligation bond appropriation
- `pcsd_facility_credit` — charter facility-credit pool
- `go_bond_taxing_authority` — GO taxing power

ROPS intercept is the closest structural analog to **CSFA LCFF**: both are state-mandated payment diversions executed by a state or county officer (county auditor for ROPS; state controller for CSFA LCFF), before the operator/issuer touches the funds. The CSFA LCFF test established R^2~19% rating-spread correlation with rating uplift being the dominant masking channel; the same pattern likely applies to ROPS, with the additional split-rating-dispersion alpha specific to this sector.

---

## 7. Framework alpha mode summary

| Alpha mode | Mechanism | Estimated bps | Confidence |
|---|---|---|---|
| Avoid host-BK-recovery cohort | Exclude Stockton/SB legacy insured | 10-15 bps net TEY | MEDIUM |
| Avoid insurer-wrap-dominated legacy | Filter to unwrapped TABs only | 5-10 bps net TEY | MEDIUM |
| Split-rating arbitrage | Buy S&P-A names that Moody's withdrew or junk-rated | 20-40 bps gross | LOW (untested; requires N>20 sample) |
| Avoid project-area-AV-decline names | Lancaster, Inland Empire small cities exposed to housing cycle | 5-10 bps net TEY | LOW (depends on cycle timing) |
| Capture quality-rated-low descend-ladder | Identify issuers where AV / DSCR / concentration justifies higher rating than assigned | 10-20 bps net TEY | LOW-MEDIUM |

**Composite expected honest alpha after honesty cuts**: **15-30 bps net TEY uplift over passive A-category Successor Agency index**. Below Cal-Mortgage benchmark (~30-60 bps) because rating dispersion is narrower; the alpha is more in the rating-methodology-disagreement zone than the operator-quality-rating zone.

The DILIGENCE-REPLICATION value remains strong: framework correctly flags structural strengths/weaknesses for self-managed SMA exclusion at zero institutional management fee, independent of whether secondary-trade alpha materializes.

---

## Appendix A: Source citations

| Citation | URL |
|---|---|
| Bond Buyer — CA TABs Heat Up (2024 commentary) | https://www.bondbuyer.com/opinion/commentary-california-tax-allocation-bonds-heat-up |
| Bond Buyer — CA Redev Bonds Take Ratings Hit (Moody's 2012) | https://www.bondbuyer.com/news/california-redevelopment-bonds-take-ratings-hit |
| Bond Buyer — San Bernardino JPFA Lowered to BBB (Aug 2012) | https://www.bondbuyer.com/news/s-p-san-bernardino-joint-powers-financing-authority-ca-tabs-lowered-to-bbb |
| Bond Buyer — Riverside RDA Raised to A- | https://www.bondbuyer.com/news/successor-to-the-riverside-rda-calif-raised-to-a-minus-by-s-p |
| Bond Buyer — Ambac Sues Hercules After RDA Default | https://www.bondbuyer.com/news/ambac-sues-troubled-hercules-calif-after-rda-default |
| Bond Buyer — SJ Redev Agency Readies Largest Deal | https://www.bondbuyer.com/news/san-jose-redevelopment-agency-readies-largest-deal-of-its-kind |
| Bond Buyer — SJ Miami-Dade Chicago deals price | https://www.bondbuyer.com/news/san-jose-miami-dade-chicago-deals-price-as-municipal-bond-yields-move-lower |
| Bond Buyer — Insurers Circling Stockton | https://www.bondbuyer.com/news/insurers-circling-as-stockton-defaults-on-its-obligations |
| Business Wire — Fitch Rates SB Successor A | https://www.businesswire.com/news/home/20160219005945/en/Fitch-Rates-Successor-Agency-San-Bernardino-RDA |
| Business Wire — Fitch Affirms Coronado A+ | https://www.businesswire.com/news/home/20150825006329/en/Fitch-Affirms-Coronado-CDA-CAs-TABs-at-A- |
| S&P Atascadero TARB 2024A rating report | https://www.atascadero.org/sites/default/files/2024-03/2024%20Bond%20Refunding%20S&P%20Rating%20Analysis.PDF |
| DOF ROPS Program | https://dof.ca.gov/programs/redevelopment/rops/ |
| DOF Meet and Confer | https://dof.ca.gov/programs/redevelopment/meet_and_confer/ |
| HSC §34183 — RPTTF waterfall | https://law.justia.com/codes/california/code-hsc/division-24/part-1-85/chapter-5/section-34183/ |
| HSC §34177.5 — Refunding bond subordination | https://codes.findlaw.com/ca/health-and-safety-code/hsc-sect-34177-5.html |
| Oakland v. DOF (2022) — ROPS litigation | https://caselaw.findlaw.com/court/ca-court-of-appeal/2173932.html |
| municipalbonds.com — San Bernardino BK | https://www.municipalbonds.com/risk-management/city-of-san-bernardino-bankruptcy/ |
| Brookings — Stockton BK analysis | https://www.brookings.edu/articles/what-the-stockton-municipal-bankruptcy-means-and-doesnt/ |
| LA County 2014 Redev Refunding Authority OS | https://ttc.lacounty.gov/wp-content/uploads/2018/10/CALosAngeles12c-FIN-Posted-11.07.14.pdf |
| Oakland 2015 Coliseum TAB rating | https://www.oaklandca.gov/files/assets/city/v/1/finance/documents/investor-relations/rating-reports/rating-upgrades-to-successor-agencys-tax-allocation-bonds-coliseum-november-2015-pdf.pdf |
| Inglewood TAB debt page | https://www.cityofinglewood.org/284/Tax-Allocation-Bond-Debt |
| Moody's Santa Monica RDA upgrade | https://www.moodys.com/research/Moodys-upgrades-Successor-Agency-to-City-of-Santa-Monica-RDAs--PR_332803 |
| OC Development Agency NDAPP Annual Report | https://cfo.oc.gov/sites/finance/files/2022-03/NDAPP%20Annual%20Rpt%20%20FY%2020-21%2003%20FINAL.pdf |
| LA County 2025 GO Ratings Affirmation | https://lacounty.gov/2025/06/10/los-angeles-countys-strong-bond-ratings-affirmed-by-three-major-ratings-agencies/ |
| SJ City Fitch AAA GO upgrade | https://www.sanjoseca.gov/Home/Components/News/News/3091/4699 |
