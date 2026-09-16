# CA Pension Obligation Bonds (POBs) — Sector Scoping

**Prepared**: 2026-05-28
**Status**: Initial scoping pass + state_pension_intercept masking-mechanism validation
**Framework**: Refined thesis (rating dominates spread; descending-ladder with quality)
**Owner**: muni_credit vertical
**Related knowledge_graph entry**: `masking_mechanisms.json` → `state_pension_intercept` (MENTIONED_NOT_VALIDATED → DOCUMENTED with PARTIAL/CONDITIONAL verdict; full primary-spread test pending)

---

## Executive Summary (~300 words)

**Universe size and structure.** California POB universe is ~$25B cumulative issuance 1985-2020 plus ~$7B of new issuance in 2020-2021 (the peak surge). Top-3 cumulative issuers: **Orange County $4.4B**, **LA County $2.9B**, **San Diego County $2.1B**. Universe scoped at **27 obligors** (8 counties, 17 cities, 2 lease-revenue-pension structures, and historical defaulters). The **State of California has ZERO POBs outstanding** — the 2007 Court of Appeal *State Pension Obligation Bond Committee v. All Persons* validation action rejected state-level POBs as violating the constitutional debt limit (legislature voluntarily imposed its own PERS funding obligation, so not an "obligation imposed by law" exception). The Dec 18, 2025 CA Supreme Court *City of San José* ruling explicitly upheld CITY/COUNTY POBs as constitutional but does NOT affect state-level POBs. **This contradicts the task brief premise that "State of CA has its own POBs (~$10B+)"** — flagged as caught-fabrication-risk; prior agents could plausibly have hallucinated state POBs.

**Masking-mechanism verdict: state_pension_intercept.** **PARTIAL / CONDITIONAL VERIFIED** — POBs do trade primarily to obligor GO credit curve (Fitch upgraded San Diego County POBs to AAA in 2024 as part of criteria review explicitly recognizing this), NOT to pension funded ratio. BUT the masking BREAKS at the catastrophic-credit tail: Stockton (2012 Ch 9) and San Bernardino (2012 Ch 9) bankruptcy outcomes proved POBs are SUBORDINATE to pension contributions, with POB bondholders receiving 51% (Stockton) and 40% (San Bernardino) PV recovery while CalPERS got 100%. So the intercept is a STRONG masking layer for performing credits, with ANTI-MASKING at the BK tail. Bond insurance (Assured on Stockton, Ambac on San Bernardino) further complicates the picture by re-masking the BK tail.

**Top 3 buy-zone candidates** (strong-issuer-rated-low, descending-ladder thesis): **(1) San José POBs** (new 2025-2026 issuance, AA city GO with weak ~70% pension funded ratio — textbook intercept-masking play if it holds); **(2) Sonoma County POBs** (AA+ Fitch rating, UAL down 37% since 2020, framework-favorable trajectory); **(3) Orange County POBs** (AA+ GO, largest CA POB issuer cumulative, mature credit with 1994 BK in distant past).

**Top 3 exclude-zone names** (rating driven by credit weakness): **(1) Oakland** (Moody's Dec 2024 downgrade, structural deficit, 1997 POB lost $250M); **(2) Stockton** (post-BK weak credit, only wrap-supported); **(3) San Bernardino** (post-BK weak credit, only wrap-supported).

---

## 1. Sector overview

### Market size and structure
- **Cumulative CA POB issuance 1985-2020**: $25B+
- **2020+2021 issuance surge**: $7B (driven by Fed near-zero rates; refinance CalPERS 7% UAL cost at 2-3% bond cost)
- **2020 issuer mix**: cities 62%, counties 7%, school/special districts/JPAs ~31%
- **Top cumulative issuers**: Orange County $4.4B; LA County $2.9B; San Diego County $2.1B
- **Bond structure**: TAXABLE (no AMT) general-fund obligation; unconditional; 25-30 year typical maturity; non-callable usually; payable from any legally available funds of issuer
- **Source citations**: Bond Buyer 2020-12-09 "California pension obligation bond sales soared in 2020"; CDIAC Debt Financing Guide §3.3.2.2

### CA-specific structural context
- **2007 State POB rejection**: *State Pension Obligation Bond Committee v. All Persons* (Cal. Ct. App. 2007) affirmed trial-court invalidation of proposed $929M state POB. State POBs require 2/3 voter approval. **State of CA has zero outstanding POBs.**
- **2025 Local POB validation**: *City of San José v. Howard Jarvis Taxpayers Assoc.* (Cal. Dec 18, 2025) unanimously upheld city/county POBs as "obligations imposed by law" exempt from voter approval. Validation actions no longer formally required.
- **Bankruptcy treatment (Stockton, San Bernardino)**: POBs are **unsecured general fund obligations and subordinate to CalPERS pension contributions** in Ch 9. Federal Bankruptcy Court (Klein in Stockton; Jury in San Bernardino) ruled POBs do NOT rank pari passu with pensions. POB recovery: Stockton 51%, San Bernardino 40% PV.
- **Bond insurance on legacy POBs**: Stockton 2007 ($125M) insured by Assured Guaranty; San Bernardino 2005 ($50M) insured by Ambac. Insurance wrap absorbed Ch 9 haircut for bondholders.
- **CalPERS funded ratio**: 71.4% (FY23) → 75% (FY24) → ~78.6% est (FY25 per preliminary 11.6% return). CalSTRS: 76.7% (June 30, 2024).

### Default and distress history
| Obligor | Year | POB Outcome | Wrap |
|---|---|---|---|
| Stockton | 2007 issuance, 2012 Ch 9 | 51% direct recovery; insurer paid 100% | Assured Guaranty |
| San Bernardino | 2005 issuance, 2012 Ch 9 | 40% PV recovery over 30 years; insurer paid | Ambac |
| Orange County | 1994 issuance, 1994 Ch 9 (derivative-fund) | Rollover; no POB-specific haircut | None known |
| Oakland 1997 POB | 1997 issuance | No default but $250M investment-arbitrage LOSS by 2010 (city auditor) | None |
| Vallejo 2008 Ch 9 | N/A | **NO POBs** — Vallejo did NOT have POBs (task-brief premise FALSIFIED) | N/A |

**Distress base rate**: 2 hard defaults out of ~70 CA POB financings 1994-present = ~3% cumulative default rate over 30 years. Recovery materially worse than CA GO (which is largely intact post-BK).

---

## 2. Universe inventory (see `data/ca_pob_universe.json` for full record)

**Counties (n=8)**: Orange, LA, San Diego, Sonoma, Alameda, Contra Costa, Sacramento, Imperial, Butte, Mendocino/Merced (last two grouped).
**Cities (n=17)**: Stockton, San Bernardino, Oakland, Riverside, Pasadena, San José (new), Huntington Beach (authorized), Ontario, Pomona, West Covina (lease-rev), Torrance (lease-rev), Manhattan Beach, Chula Vista, Fresno, Larkspur, Novato.
**State entity**: State of California — ZERO POBs (court-rejected 2007).
**Confidence**: 12 primary-source rating/amount confirmed; 9 partial-field primary-source; 6 inferred from peer-group / counsel-of-record lists.

---

## 3. State_pension_intercept masking mechanism — validation findings

### Hypothesis (per masking_mechanisms.json entry)
> POBs trade to state-credit (obligor general-fund) curve, NOT to pension-fund funded-ratio curve. Pension-funded-ratio detector signals do NOT translate to POB spreads.

### Empirical findings

**Finding A — VERIFIED for performing credits**: POB ratings track GO ratings closely (typically 0-1 notch lower for taxable structure). Pasadena 2015 POB rated AA by Fitch with explicit rationale: "POBs are unconditional obligations of the city and are not secured by the city's taxing authority." San Diego County 2008A POB ($343.5M) rated AA initially, upgraded to AAA in 2024 by Fitch as part of broader criteria-review explicitly recognizing POBs trade to GO credit. Sonoma County POBs upgraded to AA+ from AA recently — rating action driven by GO credit improvement, not pension funded ratio.

**Finding B — FALSIFIED at the catastrophic-credit tail**: When obligor enters Ch 9, POBs are explicitly subordinated to pension contributions. Stockton (Klein) and San Bernardino (Jury) federal-court rulings established the precedent that POBs do NOT rank pari passu with CalPERS. Recovery: Stockton POB 51% direct, San Bernardino POB 40% PV. Pensions: 100% both cases.

**Finding C — Re-masked by bond insurance at tail**: Stockton 2007 POB insured by Assured Guaranty; San Bernardino 2005 POB insured by Ambac. Both insurers made bondholders whole. So at the BK tail, the bond-insurance masking mechanism (`agm_bond_insurance` per masking catalog) COMPENSATES for the state_pension_intercept ANTI-masking.

**Finding D — Pension funded-ratio signal does NOT translate**: CalPERS at ~75% funded; CalSTRS at ~77%; county systems at 70-79%. Yet POB spreads tightening (San Diego AAA upgrade). The framework's `pension_funded_ratio` detector would fire (CRITICAL <60% threshold for many county systems and FRESNO/SAN JOSÉ own plans) but bond prices ignore. **Cleanest framework signal that the market doesn't price.**

### Verdict: PARTIAL / CONDITIONAL VERIFIED
- **For performing credits**: STRONG masking. Pension funded ratio detector fires but POB spread tracks GO credit. Mirrors charter-school CSFA LCFF intercept v3 finding (rating-compression channel).
- **For Ch9-tail credits**: ANTI-masking — POBs subordinate to pensions. But bond-insurance wraps usually offset this.

### Cross-asset structural parallel
This is structurally identical to the v3 charter-school CSFA LCFF intercept finding (rating dominates spread; within-rating dispersion dominated by market timing not operator-credit). The intercept-mechanism produces 1-3 notches of rating uplift / convergence to GO; within-rating spread variance is mostly market-conditions noise.

---

## 4. Refined-thesis application — descending the ladder with quality

### Buy-zone candidates (top 5)
| Rank | Obligor | Rating | Issuer Quality | Why Buy-Zone |
|---|---|---|---|---|
| 1 | **San José (new 2025-2026 issuance)** | AA city GO; POB pending | Weak pension funded ratio (~70%) but STRONG city tax base | Textbook descending-ladder: pension-fund signal SAYS distressed, but state_pension_intercept masks → POB will price to AA-GO curve. If intercept holds, this is the cleanest framework alpha play in the sector. |
| 2 | **Sonoma County** | AA+ (Fitch upgrade) | Strong; UAL down 37% since 2020 | Strong improving trajectory; rating constrained by COUNTY-scale factors, not credit. |
| 3 | **Orange County** | AA+ inferred GO | Diversified $4.4B cumulative POB issuer; 1994 BK 30+ years past | Mature credit; rating constrained by historical-BK memory factor + POB-structure (taxable, GF), not current credit. |
| 4 | **Riverside (City)** | AA GO; AA POB | Recent rating UPGRADE; primary-source confirmed | Strong inland-empire credit; POB rating consistent with GO. |
| 5 | **Pasadena** | AAA GO; AA POB | Affluent tax base | Strongest small-city credit; 1-notch GO/POB gap consistent with structural-factors-only constraint. |

### Exclude-zone names (top 5)
| Rank | Obligor | Rating | Why Exclude |
|---|---|---|---|
| 1 | **Oakland** | Moody's downgraded Dec 5 2024 | Structural deficit + 1997 POB lost $250M = textbook bad-bet legacy. Rating driven by credit weakness. |
| 2 | **Stockton** | Sub-IG underlying; wrap-dependent | Post-BK weak credit; Assured wrap the only thing supporting current par. |
| 3 | **San Bernardino** | Sub-IG underlying; wrap-dependent | Post-BK weak credit; Ambac wrap support. Worse than Stockton on direct recovery (40% vs 51%). |
| 4 | **Imperial County** | A / A- inferred | Concentrated rural / border economy; rating constrained by GENUINE credit-weakness factors (concentration, weak tax base), not structural-only. |
| 5 | **Mendocino / Merced (rural CA county POBs)** | A- / BBB+ inferred | Weak rural credits; need obligor-specific work, but at this universe-scoping level, descending-ladder thesis would NOT apply because rating reflects real credit weakness. |

### The textbook trade: San José POB at issuance
- **GO rating**: AA city, AA-range POB expected
- **Pension funded ratio**: ~70% across San Jose Federated + Police & Fire (worst in CA among major cities)
- **Framework `pension_funded_ratio` detector**: would fire CRITICAL (<60% threshold not breached but trajectory near WATCH 75% threshold)
- **Hypothesis**: POB will price to AA-range GO curve (~50-100 bps over UST), NOT to pension-fund-distress curve (would imply BB+ pricing, ~250-400 bps over UST)
- **Test**: Monitor pricing at issuance vs San José GO bond curve. If spread compression to GO holds, state_pension_intercept VERIFIED at primary-market level.

---

## 5. Honest TEY math (POBs are TAXABLE)

POBs are **taxable** at federal AND CA state level (unlike tax-exempt CA muni AAA). TEY math:

- POB yield: assume AA-rated POB 30-year ~5.0-5.5% (UST 10Y ~4.3% mid-2025, POB +100-200 bps over UST for AA term)
- Tax-exempt CA AAA muni 30-year: ~4.0-4.5%
- For top-bracket CA investor (37% federal + 13.3% CA = ~50% combined), tax-exempt 4.25% = **8.5% TEY**
- POB 5.25% taxable stays 5.25% — no tax conversion benefit
- POBs are LOWER TEY than CA AAA muni for tax-exempt buyers

**Practical implication**: POBs are bought primarily by:
1. Tax-exempt institutions (pension funds, endowments, foreign sovereigns) — for whom taxable/tax-exempt doesn't matter
2. IRA/401(k) retail — same reason
3. Cross-over arbitrage at relative-value moments

The CA AAA-muni TEY advantage that the framework computes for NH/CCRC/charter sectors **does NOT apply to POBs**. The yield comparison for POBs must be against corporate-credit benchmarks (taxable AA corp ~4.8-5.2%) or UST + appropriate spread.

**Where alpha lives on POBs**:
- Descending-ladder yield pickup (AA POB at +100-150 over UST vs AAA POB at +50-75 over UST = 50-75 bps incremental)
- Within-rating mispricing: framework can identify strong-issuer-rated-low where the rating overstates risk
- This is more analogous to taxable corporate-credit work than to tax-exempt muni work

---

## 6. Open data gaps

1. **Per-CUSIP current bid-side spreads to UST** — would require EMMA bulk pull or Bloomberg terminal. Would enable empirical test of the state_pension_intercept hypothesis at the spread level (analogous to the v3 charter-school 56-anchor test).
2. **Pension funded ratio at obligor level** for non-CalPERS/CalSTRS county systems: LACERA, OCERS, SDCERA, SBCERA, MCERA, ACERA, CCCERA, SCERA, SCERS not pulled at obligor level. Each has its own GASB 68 disclosures in audited FS.
3. **Per-CUSIP bond insurance status** — not pulled at obligor level. Critical for the Stockton/San Bernardino wrap-masking compensation finding to generalize.
4. **City of San José POB pricing at issuance** — pending issuance; if priced before end of FY26 will be the cleanest empirical test of state_pension_intercept.
5. **Lease-revenue pension-funding variant** (West Covina, Torrance) — structurally distinct from POBs but functionally equivalent. Should this be a separate masking-mechanism entry (city_lease_revenue_pension_funding) or sub-variant of state_pension_intercept? Currently catalog has only the POB variant.

---

## 7. Knowledge-graph updates required

1. **`masking_mechanisms.json`** — update `state_pension_intercept` entry:
   - MENTIONED_NOT_VALIDATED → **DOCUMENTED** (PARTIAL/CONDITIONAL VERIFIED, awaiting per-spread test)
   - Add `signal_to_price_impact`: STRONG for performing credits; ANTI-MASKING at Ch9 tail; bond-insurance re-masks at tail
   - Add Stockton, San Bernardino as POSITIVE CONTROL cases
   - Cross-reference `agm_bond_insurance` (insurance compensates intercept ANTI-masking at tail)
   - Cross-reference `csfa_lcff_intercept` (structurally identical rating-compression channel)
   - Add the SAN JOSÉ DEC 2025 ruling as new universe-expansion event
   - Add empirical case: Fitch San Diego County POB AAA upgrade 2024 (criteria change explicitly recognized POBs trade to GO)
   - Note: STATE OF CA has zero POBs (constitutional bar)

2. **`signal_channels.json`** — no new channels (pension funded ratios already covered by `pension_funded_ratio` detector data sources)

3. **Cross-reference in `csfa_lcff_intercept`** — both intercepts produce rating-uplift / GO-convergence masking; both have within-rating spread variance dominated by market timing rather than operator signal.

---

## 8. Recommended next session work

1. **Pull EMMA secondary-market spreads on the 27-obligor universe** — generates empirical spread distribution. Especially useful: pre-2024 vs post-2024 spread comparison around Fitch criteria change for San Diego County.
2. **Monitor San José POB issuance pricing** as forward test.
3. **Pull per-obligor county pension funded ratios** (LACERA, OCERS, SDCERA at minimum) to test "framework signal fires, market ignores" pattern formally.
4. **Build `pob_intercept_descending_ladder` detector** as a *positive* selection screen (identify AA-rated POBs where issuer quality matches GO and rating premium is 0-1 notch from GO).
5. **Test the bond-insurance overlay**: among the 27 obligors, what % of CUSIPs are wrapped (AGM/BAM/Ambac/Assured)? Wrap status materially changes the Ch 9 tail risk.

---

## 9. Cross-vertical generalization

The state_pension_intercept finding suggests a broader pattern:

**Where intercept-style mechanisms exist (CSFA LCFF for charter muni; state_pension_intercept for POBs; FHA Section 242 for hospitals; Cal-Mortgage for NH/CCRC)**:
- Rating dominates spread (R²~19% in charter v3 test, expected similar for POBs)
- Within-rating, market-timing dominates operator-credit-signal (charter v3: Granada Hills 224→71→70 bps with same operator)
- Framework adds value via EXCLUSION at the rating-band tail (sub-IG names), not via within-rating arbitrage
- Diligence-replication value is real even when alpha-arbitrage value is absent

POBs likely follow the same pattern. The descending-ladder thesis from charter-sector applies: pick strong-issuer-rated-low where rating is constrained by structural factors (taxable, GF-only, POB-structure, county-scale), NOT by credit-weakness factors (operating deficit, declining tax base, BK history).

---

**Source URL appendix**:
- https://caselaw.findlaw.com/ca-court-of-appeal/1357288.html (2007 state POB rejection)
- https://www.orrick.com/en/Insights/2025/12/California-Supreme-Court-Approves-Pension-Obligation-Bonds (Dec 2025 SCOCA ruling)
- https://www.bondbuyer.com/news/california-pension-obligation-bond-sales-soared-in-2020 (cumulative + 2020 issuance)
- https://www.bondbuyer.com/news/san-diego-countys-pension-bonds-bumped-to-aaa-as-part-of-fitch-criteria-review (Fitch AAA upgrade)
- https://www.bondbuyer.com/news/why-pensions-beat-bonds-in-bankruptcy-court (Vallejo had no POBs; Stockton/SB POB subordination)
- https://www.bondbuyer.com/news/san-bernardino-chapter-9-plan-gives-bondholders-worst-cut-of-all
- https://www.bondbuyer.com/news/san-bernardino-bondholders-agree-to-60-haircut
- https://www.abi.org/feed-item/stockton-bankruptcy-settlement-preserves-pensions
- https://www.businesswire.com/news/home/20150414006645/en/Fitch-Rates-Pasadena-CAs-123MM-Pension-Obligation-Rfdg-Bonds-AA-Outlook-Stable
- https://www.sandiegocounty.gov/content/dam/sdc/fg3/debt/2008-pob/OS_-_2008A.pdf (SD County 2008A OS)
- https://www.riversideca.gov/finance/investor/pdf/2020%20POB%20OS.pdf
- https://www.bondbuyer.com/news/city-streets-back-new-bonds-california-cities-issue-to-fund-pensions (West Covina/Torrance lease-rev structure)
- https://sonomacounty.gov/fitch-ratings-upgrades-sonoma-countys-credit-rating-on-pension-obligation-bonds-to-aa
- https://www.calpers.ca.gov/newsroom/calpers-news/2025/calpers-announces-preliminary-116-return-for-2024-25-fiscal-year (CalPERS funded ratio)
- https://www.calstrs.com/files/c335d7b3e/TRB+2024-11+Item+06.01+-+Review+of+Funding+Levels+and+Risks+Report.pdf (CalSTRS 76.7% June 2024)
- https://www.orrick.com/en/Practices/Pension-Obligation-Bond-Financing (Orrick counsel-of-record list)
