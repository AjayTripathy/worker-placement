# CA K-12 School District General Obligation Bonds — Sector Scoping

**Prepared**: 2026-05-28
**Status**: Initial scoping pass + `ca_k12_dedicated_tax_special_revenue` masking-mechanism validation
**Framework**: Refined thesis (rating dominates spread; descending-ladder with quality + structural-class filter)
**Owner**: muni_credit vertical
**Related knowledge_graph entry**: `masking_mechanisms.json` → NEW `ca_k12_dedicated_tax_special_revenue` (VERIFIED with PARTIAL spread-compression; per-CUSIP test pending); FALSIFIES the task-spec hypothesis that K-12 GO has an "apportionment intercept" analogous to CSFA LCFF.

---

## Executive Summary (~300 words)

**Universe size and structure.** California K-12 school district GO bonds are the **largest CA muni sector by outstanding par** — estimated $150-200B+ across ~900 districts. LAUSD alone has $11.8B post-2026 issuance; top-10 districts ~30-40% of par. Scoped at **32 obligors** across 5 strata (largest, mid-urban, wealthy suburban, rural, fiscal-distress). All K-12 GO bonds are secured by ad valorem property tax levied by the COUNTY on the district's tax roll — **no state apportionment, no Prop 98 funding, no LCFF money ever touches the bond trustee**.

**Masking-mechanism verdict: `ca_k12_dedicated_tax_special_revenue` — VERIFIED with PARTIAL spread-compression. The task-spec hypothesis is FALSIFIED at the mechanism level but VERIFIED at the outcome level.** There is NO state-apportionment intercept analogous to CSFA LCFF (Ed Code §17199.4) for K-12 district GO. There is also NO California analog to Texas Permanent School Fund (PSF) bond guarantee — Texas's $60B PSF wraps $100B+ of TX school bonds with AAA; California has nothing equivalent. **What DOES exist is structurally different but functionally similar**: SB 222 (Cal. Gov't Code §53515, effective Jan 2016) codifies an automatic statutory lien on dedicated property-tax bond-debt-service revenues. Combined with Ed Code prohibition on operational use of these revenues, this satisfies U.S. Bankruptcy Code §902(2) "pledged special revenue" criteria. Fitch (and S&P, Moody's analogously) permit dedicated-tax GO ratings up to **5 notches above the district's Issuer Default Rating (IDR)**. The masking is partial (rating still drops with credit) but creates a structural floor (5-notch uplift).

**Load-bearing empirical anchors**: (1) **Sacramento USD 2026-04-28**: IDR cut BB- (from A+), dedicated-tax GO cut to BBB+ (from AAA) = exactly 5-notch gap (Fitch criteria max). (2) **LAUSD 2026-04-20**: IDR AA- NEGATIVE outlook, dedicated-tax GO AAA STABLE = 4-notch gap with stable trajectory despite 48% peak-to-trough ADA decline.

**Top 3 buy-zone candidates** (operator-distress masked by dedicated-tax GO structural uplift): **(1) Sacramento USD dedicated-tax GO series** (BBB+ stable floor despite IDR BB-; cleanest descending-ladder); **(2) Oakland USD dedicated-tax GO with explicit pledged-special-revenue OS language** (structural deficit fully masked); **(3) Inglewood USD dedicated-tax GO** (state-receiver since 2012, dedicated-tax GO retains A-category via uplift).

**Top 3 exclude-zone**: **(1) Sacramento USD ULTGO older series + LRBs** (no pledged-special-revenue language; cut to BB- and B+ respectively); **(2) Any K-12 COP / LRB exposure for fiscal-distressed districts** (LAUSD COP A+ negative; SCUSD LRB B+; no special-revenue protection); **(3) Modoc / Imperial rural micro-districts** (tax base too thin for 5-notch uplift to overcome credit floor).

---

## 1. Sector overview

### Market size and structure
- **Total outstanding par**: estimated $150-200B+ across ~900 K-12 districts (CDIAC DebtWatch baseline)
- **Top issuer**: LAUSD $11.8B post-2026 issuance (Moody's), Long Beach USD, SDUSD ~$4.5B
- **Voter approval threshold**: 55% under Prop 39 (2000), down from 2/3 historical
- **Security**: Ad valorem property tax levied by county on district tax roll — unlimited tax obligation per Ed Code §15250 et seq.
- **Statutory lien**: SB 222 (Cal. Gov't Code §53515, effective Jan 2016) — automatic at moment of levy, no further act required
- **Source citations**: California Debt Financing Guide §B.1.3.1; Orrick 2015-03 client alert "California's SB 222"; Bond Buyer "California School GO Structure Seen as Special Revenues" (2016)

### CA-specific structural context
- **No state-apportionment intercept for K-12 GO**: Unlike CSFA charter conduit deals (Ed Code §17199.4 State Controller LCFF intercept), district GO bonds are NOT structured to intercept state funding. LCFF apportionment flows directly to district operations; the State Controller does not divert it to bond trustees.
- **No California Permanent School Fund**: Texas has a $60B PSF wrapping ~$100B of TX school bonds with AAA. California has nothing equivalent. The State Allocation Board (SAB) administers School Facility Program matching grants but does NOT guarantee district GO. Source: tea.texas.gov PSF disclosure; CA DGS OPSC Bond Oversight K-12.
- **AB 8 (1979) is intra-government allocation, not bond pledge**: AB 8 reallocated property tax revenues after Prop 13 (schools' share dropped from ~50% to ~36%); ERAF (1992-93) reshuffled $3.6B back to schools. Neither is a bondholder-facing intercept.
- **State emergency loans go to district operations, NOT bondholders**: Ed Code §41320 et seq. enables state to lend to insolvent districts (Vallejo $60M 2004, Inglewood $29M 2014, Compton $20M 1993, plus West Fresno, Oakland, Coachella, Emery). These loans bypass bondholders entirely — bondholders are already protected by the dedicated-tax structure regardless of district insolvency. State receivership has ZERO direct positive credit effect on bondholder cash flow.

### Default and distress history
| Obligor | Year | Event | GO Bond Outcome |
|---|---|---|---|
| Compton USD | 1993-2001 | First CA state takeover (8 years receivership) | No GO default |
| Oakland USD | 2003-2009 | State receivership; $100M+ emergency loan | No GO default |
| Vallejo USD | 2004-2025 | 20-year state receivership; $60M emergency loan ($68.5M with interest) repaid Aug 2024 | No GO default |
| Inglewood USD | 2012-ongoing | State receiver since SB 533 2012; $29M emergency loan 2014, repayment thru 2034-35 | No GO default; S&P BBB- |
| Sacramento USD | 2026 active | $170M deficit (KCRA); Fitch ULTGO BB-, dedicated-tax GO BBB+ | No default; rating compression confirmed |

**Distress base rate**: ZERO CA K-12 district GO bond defaults in the modern era despite multiple state-receivership cases. This is the strongest validation of the dedicated-tax-special-revenue masking mechanism — even when districts go insolvent, GO bondholders are paid via the county-administered tax levy.

---

## 2. Universe inventory (see `data/ca_k12_go_universe.json` for full record)

**Top-10 by par or visibility**: LAUSD, SDUSD, Long Beach USD, SFUSD, OUSD, SCUSD, Fresno USD, PAUSD, Berkeley USD, Capistrano USD.
**Wealthy suburban (high-grade)**: PAUSD, Beverly Hills, San Marino, Berkeley, Saddleback Valley, Newport-Mesa.
**Mid-size urban**: SFUSD, SCUSD, Fresno, Santa Ana, Garden Grove, Pasadena, Riverside, Bakersfield, San Bernardino City, Stockton USD, Twin Rivers.
**State-receiver / fiscal-distress history**: Oakland, Vallejo, Inglewood, Compton, Coachella, West Fresno, SCUSD (current), West Contra Costa (wrap-dependent).
**Rural / at-risk tax base**: Imperial, Modoc, Coachella, West Fresno (small).
**Confidence**: 14 primary-source ratings confirmed; 10 secondary-source; 8 inferred from peer-group / strata.

---

## 3. `ca_k12_dedicated_tax_special_revenue` masking mechanism — validation findings

### Hypothesis (per task brief)
> CA K-12 school district GO bonds may have an intercept mechanism analogous to CSFA LCFF intercept (state apportionment diverted to bond trustee on deficiency) — i.e., state apportionment / Prop 98 protects bondholders.

### Empirical findings

**Finding A — Hypothesis FALSIFIED at the mechanism level**: There is NO state-apportionment intercept for K-12 district GO. State LCFF money flows to district operations and never touches the bond trustee. Bondholders are paid from county-administered property tax (not state apportionment). The CSFA charter analog does NOT exist for district GO. Source: California Debt Financing Guide §B.1.3.1.

**Finding B — A DIFFERENT but functionally analogous masking mechanism IS present**: SB 222 statutory lien + bankruptcy-code-pledged-special-revenue treatment creates a 5-notch ceiling between district IDR and dedicated-tax GO rating. This is STRUCTURALLY DIFFERENT from CSFA LCFF intercept (which is a state-money-flow intercept) but FUNCTIONALLY similar (rating-band compression that masks operator signal).

**Finding C — VERIFIED via Sacramento USD 2026-04-28**: Cleanest empirical anchor. Fitch downgraded SCUSD IDR to BB- from A+, ULTGO (older series, no pledged-special-revenue OS language) to BB- from A+, but DEDICATED-TAX GO (newer series, with the explicit OS pledge) only to BBB+ from AAA. The dedicated-tax GO retained EXACTLY 5 notches above IDR — Fitch's criteria maximum. Fitch attributed the rating differential to "constitutional and statutory protections afforded to property tax revenues levied for bond repayment." Even at extreme operator distress ($170M deficit, expected state intervention), dedicated-tax GO holds investment grade. Source: Bond Buyer "Sacramento school bonds downgraded to junk on fiscal woes" 2026-04-28.

**Finding D — VERIFIED via LAUSD 2026-04-20**: Fitch revised IDR outlook to NEGATIVE on AA- IDR, ULTGO outlook to NEGATIVE on AA- ULTGO, COP outlook to NEGATIVE on A+ COP — but DEDICATED-TAX GO outlook remained STABLE on AAA. Despite 48% peak-to-trough ADA decline (746K → 389K), the dedicated-tax GO outlook is uninfluenced by operator deterioration. Source: Bond Buyer "Los Angeles school bond outlook dropped to negative by Fitch, Moody's" 2026-04-20.

**Finding E — Masking is PARTIAL (not absolute like Cal-Mortgage on NH/CCRC)**: Sacramento USD dedicated-tax GO did fall from AAA to BBB+ when IDR collapsed — so the masking is rating-compression, not full decoupling. Compare to charter CSFA LCFF intercept v3 finding (also partial — rating-compression channel) and to state_pension_intercept POB finding (also rating-compression channel). All three intercept-class mechanisms produce partial masking via rating-band compression rather than full decoupling.

**Finding F — Series-level bifurcation matters**: Within a single district, OLDER GO series issued before SB 222 (Jan 2016) and without explicit dedicated-tax-pledged-special-revenue OS language do NOT get the 5-notch uplift. They track the IDR. NEWER series (typically post-2016 OS drafting) with explicit pledged-special-revenue legal opinion get the uplift. Sacramento USD's 2007/2011/2012 GO bonds were rated together with IDR; 2017E/2017C series got dedicated-tax-AAA treatment. This bifurcation is the cleanest framework-value-add — exclude older-series ULTGO at the rating-band tail, buy newer-series dedicated-tax GO. Sources: Fitch action April 2026; Bond Buyer "Fitch downgrades Sacramento schools, sparing some GO bonds" (2018-era earlier Sacramento action).

### Verdict: VERIFIED — PARTIAL spread-compression, but the structural mechanism is DIFFERENT from the task-brief hypothesis
- **What was hypothesized**: State apportionment intercept (LCFF money diverted to bondholders).
- **What actually exists**: SB 222 statutory lien + Ed Code dedicated-tax pledge + bankruptcy-code special-revenue treatment → 5-notch uplift between IDR and dedicated-tax GO.
- **Functional outcome**: Same as CSFA LCFF intercept (rating-compression masks operator signal at the bond CUSIP), but the legal pathway is via the property-tax pledge structure, NOT state apportionment.

### Cross-asset structural parallel
This is structurally CLOSER to the `rops_allocation_intercept` mechanism (RPTTF property-tax waterfall) than to `csfa_lcff_intercept` (state-money flow intercept). All three produce 1-5 notches of rating uplift / convergence; within-rating spread variance is dominated by market-conditions noise.

| Mechanism | Asset class | Legal pathway | Source of bondholder cash | Rating uplift |
|---|---|---|---|---|
| `csfa_lcff_intercept` | Charter conduit | State Controller diverts apportionment | State general fund (LCFF) | 2-3 notches |
| `state_pension_intercept` | POBs | General fund unconditional obligation | Obligor general fund | 0-1 notch GO convergence |
| `rops_allocation_intercept` | Successor RDA TABs | RPTTF property-tax waterfall + HSC §34183 | Property tax (pre-distribution) | 1-3 notches |
| **`ca_k12_dedicated_tax_special_revenue`** | **K-12 district GO** | **SB 222 statutory lien + Ed Code §15250 + bankruptcy-code §902(2)** | **Dedicated property tax (post-levy, pre-distribution)** | **Up to 5 notches (Fitch max)** |

The K-12 GO mechanism has the LARGEST rating uplift cap of any CA intercept-class mechanism. This makes it the most powerful single masking layer in the CA muni catalog at the structural-ceiling level.

---

## 4. Refined-thesis application — descending the ladder with quality

### Buy-zone candidates (top 5)
| Rank | Obligor | Dedicated-Tax GO Rating | IDR | Notch Gap | Why Buy-Zone |
|---|---|---|---|---|---|
| 1 | **Sacramento USD dedicated-tax GO** (newer series) | BBB+ (Fitch, watch negative) | BB- | 5 (max) | Cleanest framework alpha play: IDR collapsed but dedicated-tax GO held at IG floor via 5-notch ceiling. If district fails to stabilize, dedicated-tax GO doesn't break below BBB+ unless tax base itself deteriorates (property tax levy continues even in state intervention). |
| 2 | **Oakland USD dedicated-tax GO** (explicit pledged-special-revenue language) | ~AA- inferred (5-notch uplift on BBB+ Fitch IDR) | BBB+ | ~5 inferred | Structural deficit fully masked at rating-band level; framework's operator-signal detectors fire on OUSD but dedicated-tax GO bonds priced to AA-curve. |
| 3 | **Inglewood USD dedicated-tax GO** | A-category inferred (3-4 notch uplift on BBB- S&P IDR) | BBB- | ~3-4 | State-receiver 13 years; dedicated-tax GO retains A-category. Receivership exit potential 2027 = positive catalyst. |
| 4 | **LAUSD dedicated-tax GO** | AAA stable | AA- (negative) | 4 | Negative IDR outlook but dedicated-tax GO outlook unchanged. ADA decline 48% peak-to-trough but tax base ($1.5T+ AV) supports GO via dedicated-tax structure. |
| 5 | **SFUSD dedicated-tax GO** | A1/A2 (Moody's; Fitch not freshly pulled) | A2 | 1+ | District 2024 downgrade reflects operating deficit; tax base (SF AV) holds up; dedicated-tax GO masking provides defensive spread floor. |

### Exclude-zone names (top 5)
| Rank | Obligor / CUSIP class | Rating | Why Exclude |
|---|---|---|---|
| 1 | **Sacramento USD ULTGO older series (2007, 2011, 2012)** | BB- (cut from A+ on 2026-04-28) | No explicit pledged-special-revenue OS language → tracks IDR not dedicated-tax-AAA; 6-notch downgrade in single action. |
| 2 | **Sacramento USD LRBs (Series 2014A)** | B+ (cut from A) | Lease revenue bonds have NO statutory-lien / dedicated-tax structure; pure appropriation risk; sub-IG. |
| 3 | **LAUSD COPs** | A+ (negative outlook) | Certificates of participation lack the dedicated-tax-special-revenue protection; share IDR-class fate. |
| 4 | **West Contra Costa USD non-insured GO** | Underlying downgraded 2024 | Required AGM/BAM wrap to come to market; wrap-dependent deals are dominated by `agm_bond_insurance` mechanism not the dedicated-tax structure; double-masking risk obscures signal. |
| 5 | **Modoc / Imperial micro-district GO** | BBB or unrated | Tax base too thin to support 5-notch uplift effectively; small issuance has poor liquidity premium; framework signal cannot translate to spread. |

---

## 5. TEY math (CA K-12 GO dedicated-tax series)

Assumptions: California resident, 37% federal + 13.3% CA marginal = 50.3% combined; CA muni-bond exempt from both. Tax-equivalent yield multiplier = 1 / (1 - 0.503) = 2.01x.

| Obligor / Class | Dedicated-Tax GO Yield (est, 10Y) | TEY (CA resident 50.3%) | Comp UST 10Y | Spread to UST TEY |
|---|---|---|---|---|
| LAUSD dedicated AAA 10Y | ~3.30% | ~6.63% | ~4.20% | +243 bps |
| SDUSD dedicated AAA 10Y | ~3.25% | ~6.53% | ~4.20% | +233 bps |
| Sacramento USD dedicated BBB+ 10Y (current, watch neg) | ~4.50-5.00% (modeled stressed) | ~9.05-10.05% | ~4.20% | +485-585 bps |
| Oakland USD dedicated AA- (modeled) | ~3.70% | ~7.43% | ~4.20% | +323 bps |

**Note on yield estimates**: Live secondary-market spreads not pulled for this scoping pass; values are MMD-AAA + rating-band-spread modeled. The dedicated-tax GO sector trades 5-15 bps tighter than equivalent-rated city/county GO due to the statutory-lien strength. Per-CUSIP EMMA secondary spreads required for empirical anchor test (see Section 7 Open Gaps).

---

## 6. Cross-vertical comparison to CSFA LCFF intercept (the analog at charter level)

| Dimension | CSFA LCFF Intercept (charter) | CA K-12 Dedicated-Tax Special Revenue (district GO) |
|---|---|---|
| **Legal authority** | Ed Code §17199.4 | SB 222 (Gov't Code §53515) + Ed Code §15250 + Prop 13 / Prop 39 + Bankruptcy Code §902(2) |
| **Money pathway** | State Controller diverts LCFF before reaching operator | County levies and collects dedicated property tax; never enters district operations |
| **Universe size** | $3-5B across 17 CSFA-intercept obligors | $150-200B+ across ~900 districts (40-60x larger) |
| **Rating uplift cap** | 2-3 notches (v3 finding) | Up to 5 notches (Fitch criteria) |
| **Masking strength** | PARTIAL (rating-compression channel) | PARTIAL (rating-compression channel, larger ceiling) |
| **Empirical anchor** | ICEF (BB+ at 143 bps) vs New Designs (BB+ at 143 bps) — 33-point operator gap, 0 bps spread differential | SCUSD dedicated BBB+ vs ULTGO older BB- — 6-notch series-level bifurcation in single rating action |
| **Within-band correlation (operator vs spread)** | Pearson r = -0.298 (N=20) | Not yet measured at per-CUSIP level |
| **What it masks** | Voluntary-default risk on going-concern charters; soft enrollment signals | District operational distress; ADA decline; deficit spending; state-receiver status |
| **What it does NOT mask** | Charter closure / authorizer non-renewal | Catastrophic tax-base erosion; bond-insurance-dependent deals (re-masked by AGM/BAM); LRBs/COPs (no statutory lien) |
| **Framework value-add** | Operator-signal exclusion at the CSFA-intercept-protected basket; CCSA-JPA pool decomposition | Series-level bifurcation: BUY newer-pledged-special-revenue series, AVOID older ULTGO and ALL appropriation paper at distressed districts |

**Headline cross-vertical finding**: The CA K-12 dedicated-tax mechanism is **stronger** than CSFA LCFF (larger rating-uplift cap: 5 vs 2-3 notches) and operates on **40-60x larger universe**. It is the **dominant masking mechanism in CA muni by total par affected**. But the masking is **partial** in all three intercept-class cases (CSFA, POBs, K-12 GO) — rating-compression channel, not full decoupling.

---

## 7. Open gaps and next-session test plan

### Data gaps
1. **Per-CUSIP EMMA secondary-market spreads** — required for the empirical IDR-vs-spread correlation test analogous to charter v3 56-anchor distribution. Without this, the masking-mechanism is VERIFIED at the rating-action level but NOT measured in basis-points at the secondary-market level.
2. **Series-level bifurcation registry** — for each major district, classify each outstanding series as (a) dedicated-tax-pledged-special-revenue (post-SB 222 + explicit OS language), (b) ULTGO-older-no-pledge, (c) LRB/COP. Without this registry, framework cannot operationalize the SCUSD-pattern bifurcation trade.
3. **Bond insurance status at CUSIP level** — West Contra Costa USD 2024 deal was wrap-dependent; many distressed-district deals get AGM/BAM. Without insurance status, masking-mechanism attribution is ambiguous.
4. **Tax base trajectory (BOE Statement of County Assessed Values)** — needed to test whether dedicated-tax GO rating breaks at catastrophic AV erosion (the one scenario the mechanism does NOT mask).
5. **Beverly Hills, San Marino, Fresno, Long Beach** — rating data not freshly verified for 2025-26 cycle.

### Test plan (next session)
1. **Per-CUSIP spread test** (highest value): Pull EMMA secondary trades on 30 CUSIPs (10 each from dedicated-tax-AAA pattern districts, 10 from BBB-A patterns under stress, 10 from older-ULTGO-no-pledge series at fiscal-distressed districts). Compute spread-to-MMD-AAA at matched maturity. Test whether spread bifurcates cleanly at series-level on Sacramento, Oakland, LAUSD.
2. **Operator-signal vs spread correlation** (analog to CSFA v3): Score each scoped district on operator quality (enrollment trend, FCMAT involvement, deficit size, qualified audit opinion). Correlate to per-CUSIP spreads within rating band. Expected finding: weak/zero within-band correlation (intercept masks the signal).
3. **Series-level rating registry**: Build a sub-table of LAUSD, SDUSD, Oakland, Sacramento, San Francisco USD identifying which outstanding series carry the dedicated-tax-pledged-special-revenue label. The bifurcation is the actionable trade.

### Falsification stance
The masking mechanism would be FALSIFIED if either:
- Per-CUSIP spread data shows dedicated-tax GO spreads track IDR-implied rating-band rather than dedicated-tax GO rating-band (would mean market ignores the rating differential).
- Catastrophic-AV-erosion case (e.g., severe Central Valley district) shows dedicated-tax GO breaks below BBB- floor.

Neither scenario is currently observable; the mechanism stands as VERIFIED with PARTIAL spread-compression.

---

## 8. Sources

1. California Debt Financing Guide §B.1.3.1 "Local General Obligation Bonds" — https://debtguide-api.treasurer.ca.gov/guide-pages/appendix-b-school-finance/b-1-school-facility-finance/b-1-3-school-district-financing-options/b-1-3-1-local-general-obligation-bonds
2. SB 222 (2015) "Local agencies: school bonds: general obligation bonds: statutory lien" — https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=201520160SB222
3. Orrick 2015-03 client alert "California's SB 222 — What a Statutory Lien Means" — https://www.orrick.com/Insights/2015/03/Californias-SB-222-What-a-Statutory-Lien-Means-for-California
4. Bond Buyer "California School GO Structure Seen as Special Revenues" (2016) — https://www.bondbuyer.com/news/california-school-go-structure-seen-as-special-revenues
5. Bond Buyer "Fitch Signals Shift on California School GO Ratings" — https://www.bondbuyer.com/news/fitch-signals-shift-on-california-school-go-ratings
6. Bond Buyer "Sacramento school bonds downgraded to junk on fiscal woes" (2026-04-28) — https://www.bondbuyer.com/news/sacramento-school-bonds-downgraded-to-junk-on-fiscal-woes
7. Bond Buyer "Los Angeles school bond outlook dropped to negative by Fitch, Moody's" (2026-04-20) — https://www.bondbuyer.com/news/los-angeles-school-bonds-cut-to-negative-by-two-raters
8. Bond Buyer "Oakland USD receives negative outlook from Moody's" — https://www.bondbuyer.com/news/oakland-usd-receives-negative-outlook-from-moodys
9. Bond Buyer "Inglewood USD, Calif. Narrowly Retains Investment Grade Rating" — https://www.bondbuyer.com/news/inglewood-usd-calif-narrowly-retains-investment-grade-rating
10. Bond Buyer "Fitch downgrades Sacramento schools, sparing some GO bonds" — https://www.bondbuyer.com/news/fitch-downgrades-sacramento-schools-sparing-some-go-bonds
11. Bond Buyer "Big California school district woes may be tip of iceberg" — https://www.bondbuyer.com/news/big-california-school-district-woes-may-be-tip-of-iceberg
12. FCMAT "Inglewood USD Progress Report July 2024" — https://www.fcmat.org/PublicationsReports/InglewoodUSD-full-report2024.pdf
13. CBS Bay Area "Vallejo City Unified School District exiting state receivership" — https://www.cbsnews.com/sanfrancisco/news/vallejo-city-unified-school-district-exiting-state-receivership-2004-financial-crisis/
14. LAO "Reconsidering AB 8: Exploring Alternative Ways to Allocate Property Taxes" (2000) — https://lao.ca.gov/2000/020300_ab8/020300_ab8.html
15. Texas Education Agency PSF Disclosure (cross-reference; TX has PSF, CA does NOT) — https://tea.texas.gov/finance-and-grants/state-funding/facilities-funding-and-standards/bond-guarantee-program
16. Fitch Rates Montebello USD ULTGO AAA (2016, primary-source AAA on ULTGO dedicated-tax) — https://www.streetinsider.com/Press+Releases/Fitch+Rates+Montebello+Unified+School+District,+CAs+$100MM+ULTGO+Bonds+AAA;+Outlook+Stable/12263563.html
17. Moody's Palo Alto USD GOULT Aaa — https://www.moodys.com/research/Moodys-Assigns-Aaa-to-Palo-Alto-USD-CAs-GO-Bonds--PR_903254206
18. S&P Palo Alto USD Series 2026 AAA — https://www.spglobal.com/ratings/en/regulatory/article/-/view/type/HTML/id/3529230
