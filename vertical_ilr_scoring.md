# Signal OS Vertical Roadmap — ILR Scoring

*Strategy document. Not implementation. Prepared 2026-05-11 for review before launching a build agent.*

---

## ILR Framework (Quick Reference)

A vertical produces *findable* fraud signals only when **all three** are non-zero:

| Dimension | Definition | Failure mode if absent |
|-----------|-----------|----------------------|
| **I — Incentive** | Financial benefit of non-compliance >> cost of compliance, large in absolute terms | No fraud occurs at all |
| **L — Structural Lag** | Decoupling of obligation from enforcement (self-report, agency silo, complaint-driven, weak penalty) | Fraud happens but is caught quickly — no detectable backlog |
| **R — Data Residue** | Public records leave a cross-referenceable trace not designed to be cross-referenced | Fraud is invisible without subpoena/FOIL |

`Signal quality ≈ I × L × R`

**Generative heuristic:** Look for government benefit programs with *self-reported* compliance and *separate* obligation-tracker vs. enforcement agencies that don't share data.

---

## Tier 1 — Built and Validated

### 1. Property Tax Uncapping (Detroit / Michigan) — BUILT

| | Score | Notes |
|---|---|---|
| I | HIGH | $5–30k/yr per property × decades; Detroit total $13–15M/yr uncollected |
| L | HIGH | Buyer-filed PTA, $200 max penalty, no automated deed↔assessor cross-ref |
| R | HIGH | Wayne County deeds + Detroit Open Data assessor + Zillow/Redfin MLS, joinable by parcel ID |

**Status:** 8,126 overdue parcels surfaced citywide; tool at `/Users/ajay/exalted/detroit_fraud`. La Salle case + assessor's-office confirmation written up.

**Open work:** Multi-county scaling. Each new state needs a `state_law` module (cap statute, transfer-trigger definition, exemption set). Top expansion candidates by ILR fit:
- **California (Prop 13):** Identical structure; LLC-to-LLC sales with no formal change-of-ownership filing are the analog. R = good (county recorders + MLS). L = high (BOE-100 self-filed).
- **Cook County, IL:** Erroneous Homestead Exemption fraud (Berkshire Hathaway / Crain's coverage). I + L + R all high.
- **Florida:** Save Our Homes cap. Snowbirds claiming homestead in two states.
- **Texas:** No state income tax → high property tax → high I; appraisal district lag is the L.

---

### 2. NYC Rent Stabilization (J-51) — BUILT

| | Score | Notes |
|---|---|---|
| I | HIGH | $1,000–$6,000/mo per unit overcharge potential; 75 confirmed bldgs = $54.9M/yr |
| L | HIGH | DHCR enforcement is complaint-driven; DOF tracks J-51 obligations, DHCR tracks rents — no cross-reference |
| R | HIGH | J-51 Socrata (y7az-s7wc) + DOF comparable rental income (myei-c3fa, 9ck6-2jew) + PLUTO, all joinable by BBL |

**Status:** 75 J51+DOF confirmed buildings, two spot-checked overcharge cases in Williamsburg (318 Grand St, 202 South 2nd).

**Open work:**
- 421-a equivalent in NYC (newer construction stabilization; same DOF/DHCR silo)
- DC TOPA / rent control in jurisdictions with proactive enforcement → likely fails L test (worth verifying before building)
- LA RSO was a dead end (L appears low — LAHD does proactive inspections)

---

## Tier 2 — Previously Discussed, Re-Scored

### 3. Conservation Easements (IRS Form 8283)

| | Score | Notes |
|---|---|---|
| I | VERY HIGH | Multi-million-dollar charitable deductions; syndicated easement market peaked at $10B+ deductions/yr |
| L | HIGH | IRS Listed Transaction designation (2017) helps but audit cycles still multi-year; appraiser self-selected |
| R | **MEDIUM** | Form 8283 details not public. Easement deeds ARE recorded at county. Comparable sales accessible (ATTOM/county recorders). Fund-level data accessible via Tax Court filings. |

**Verdict:** Strong candidate — R is the bottleneck but workable via county-level easement deed parsing + comparable sales modeling. Tax Court docket text is searchable on PACER.

**Recommended next step:** Pull recorded conservation easement deeds in 1-2 high-activity counties (e.g., Catoosa County GA — syndicated easement hotspot), match to recent comparable sales, flag valuation outliers.

---

### 4. Carbon Offset Projects (REDD+, agriculture)

| | Score | Notes |
|---|---|---|
| I | HIGH | Carbon credit prices $5–$80/ton; Verra-registered projects each generate millions of credits |
| L | HIGH | Third-party verification (Verra, Gold Standard) is paid by the project developer — incentive misalignment; auditing cycles slow |
| R | **HIGH** | Verra registry is public (project geometries, credit issuance); Global Forest Watch satellite forest cover is public; baseline counterfactual claims are testable |

**Verdict:** Strong candidate. The 2023 Guardian/Die Zeit/SourceMaterial investigation already validated this approach — they found ~94% of Verra rainforest credits were "phantom" using essentially this method. Productize it.

**Recommended next step:** Build a Verra registry → Global Forest Watch joiner. Score each REDD+ project on baseline accuracy. Repeat with Gold Standard.

---

### 5. Emissions / ESG (Scope 1/2/3 vs. Satellite)

| | Score | Notes |
|---|---|---|
| I | HIGH | Reputational + EU CSRD compliance (€10M / 5% revenue penalties) + carbon credit value |
| L | HIGH | Annual disclosure cycles, third-party verification weak, methane plumes invisible to disclosure regimes |
| R | HIGH | GHGSat, Carbon Mapper, MethaneSAT all publish point-source data; corporate disclosures via CDP, SASB, EU CSRD database |

**Verdict:** Strong candidate. EU Methane Regulation 2024 is the enforcement catalyst. Audience: short-sellers, ESG funds, regulators, journalists.

**Recommended next step:** Pick 5 oil & gas majors with public Scope 1 disclosures. Compare against Carbon Mapper / MethaneSAT plume data near their assets. Score divergence.

---

### 6. Customs / Import Undervaluation (CBP 7501)

| | Score | Notes |
|---|---|---|
| I | HIGH | Tariff savings on undervalued imports; Section 301 tariffs make this acute for China-origin goods |
| L | MEDIUM-HIGH | CBP audits reactive; export country valuations exist but not automatically cross-referenced |
| R | **LOW-MEDIUM** | CBP 7501 entries not fully public. Bill of lading data (PIERS, ImportGenius) accessible but matching to the customs entry is hard. |

**Verdict:** R is the bottleneck. Possible workaround: PIERS-style B/L data + manufacturer export records (Chinese export DB partially public). Higher-margin product line for trade lawyers and tariff arbitrage.

**Verdict:** Defer until R workaround validated.

---

### 7. 409A vs. Secondary Market FMV

| | Score | Notes |
|---|---|---|
| I | HIGH | Tax savings + employee comp economics |
| L | MEDIUM | IRS audits 409A only on triggering events |
| R | **LOW** | 409A reports are private. Secondary market data (Forge, Carta, EquityZen) partially accessible but matching to specific 409A vintages requires insider data. |

**Verdict:** Skip for now. R is structurally absent without paid data partnerships.

---

### 8. Estate Tax (Form 706)

| | Score | Notes |
|---|---|---|
| I | HIGH | 40% federal estate tax above exemption |
| L | HIGH | IRS audit slow; valuations self-selected |
| R | **LOW** | Form 706 not public. Probate records are public but matching to subsequent sales requires multi-jurisdiction tracking. |

**Verdict:** Defer. R requires a probate-records-to-property-sales pipeline that doesn't exist off-the-shelf.

---

### 9. Transfer Pricing (Multinational Intercompany)

| | Score | Notes |
|---|---|---|
| I | VERY HIGH | Multinationals shift hundreds of billions |
| L | HIGH | IRS audits years behind; OECD CbC reports filed but not public |
| R | **MEDIUM** | Comparable transaction data (RoyaltyStat, Bloomberg) accessible but expensive; internal pricing not public |

**Verdict:** Defer. Audience would be IRS / tax authorities, not market participants. Long sales cycle.

---

### 10. Art / Collectibles Donation Valuations

| | Score | Notes |
|---|---|---|
| I | HIGH | 6–7 figure charitable deductions |
| L | HIGH | IRS Art Advisory Panel reviews <0.1% of returns |
| R | **LOW-MEDIUM** | Auction records public (Christie's, Sotheby's, Heritage); donations not public except in Tax Court cases |

**Verdict:** Defer. Same R bottleneck as estate tax.

---

### 11. M&A Data Room Verification

**Not a fraud-detection vertical** — it's a buyer-side intelligence product. Different model. Skip from this roadmap.

---

### 12. Enterprise Truth-Gap (CRM vs. PM vs. Eng)

**Not fraud — internal misalignment.** Different go-to-market. Skip from this roadmap.

---

## Tier 3 — New Candidates from Generative Search

Generative heuristic: government benefit program + self-reported compliance + agency silo.

### 13. LIHTC (Low-Income Housing Tax Credit) Compliance

| | Score | Notes |
|---|---|---|
| I | HIGH | $13B/yr in federal credits; properties must charge restricted rents to income-qualified tenants for 15–30 years |
| L | HIGH | State HFA monitoring is sample-based and slow; IRS audits even rarer; recapture risk only triggers on flagrant violations |
| R | HIGH | HUD LIHTC database (property-level, public) + state HFA data + market rent data (Census ACS, RentCast) + tenant income brackets (Census tract) |

**Verdict:** Top-tier candidate. The pattern is identical to NYC J-51: tax credit creates rent restriction; restriction enforcement is weak; comparable market rents are knowable. The R stack is cleaner than J-51 because HUD publishes a national LIHTC database.

**Recommended next step:** Pull HUD LIHTC dataset. For each property, compute the maximum allowable rent (60% AMI × 30%) and compare against the area's market rent estimate. Flag properties showing market-rate listings on StreetEasy/Zillow that should be LIHTC-restricted.

---

### 14. NY 421-a / 421-g Stabilization (NYC, post-1974 construction)

| | Score | Notes |
|---|---|---|
| I | HIGH | Same gap economics as J-51, larger newer-construction unit base |
| L | HIGH | DHCR + DOF same silo as J-51 |
| R | HIGH | NYC Open Data publishes 421-a / 421-g recipient lists; rest of stack same as J-51 |

**Verdict:** Bolt-on to NYC RSL vertical. Reuse engine, swap source.

---

### 15. Federal Historic Preservation Tax Credit (Section 47)

| | Score | Notes |
|---|---|---|
| I | HIGH | 20% of qualified rehabilitation expenditures |
| L | HIGH | NPS audits architectural compliance; IRS audits financial side; the two don't reconcile |
| R | MEDIUM | NPS Part 3 approvals are public; rehabilitation expenditures are not directly public but inferable from building permit cost estimates and post-rehab assessed value jumps |

**Verdict:** Promising. Cross-reference NPS Part 3 list (Section 47 claimants) against assessor value jumps + building permit cost estimates. Outliers = inflated rehabilitation expenditure claims.

---

### 16. Opportunity Zone Funds (QOF compliance)

| | Score | Notes |
|---|---|---|
| I | HIGH | Capital gains deferral + step-up + exclusion |
| L | HIGH | IRS QOF compliance is 10-year horizon; substantially-all test self-reported on Form 8996 |
| R | LOW-MEDIUM | QOF identities public via Form 8996 filings; QOZ business activities partially public via business registrations; substantially-all test (90% of assets) hard to verify externally |

**Verdict:** Defer. R is the issue — would need to build a QOZ business activity inferrer (employee count via LinkedIn, address via business registrations, asset estimates via UCC filings).

---

### 17. Pharmaceutical 340B Drug Discount Program

| | Score | Notes |
|---|---|---|
| I | VERY HIGH | $54B+/yr in 340B discounts (2022); contract pharmacy expansion under-policed |
| L | HIGH | HRSA audits limited (~200/yr against 50,000+ entities); diversion to non-340B-eligible patients is the abuse pattern |
| R | MEDIUM | 340B-eligible entities public (HRSA database); contract pharmacy networks public; drug pricing partially public (CMS NADAC); patient-level data private |

**Verdict:** Strong potential, but the actionable analysis requires patient-level data that isn't public. Could work at the "covered entity expansion outlier" level (covered entity adding 50 contract pharmacies in a year).

---

### 18. Federal Contractor Pricing — GSA Schedule MFC Compliance

| | Score | Notes |
|---|---|---|
| I | HIGH | Vendors agree to give govt their best commercial price ("Most Favored Customer" / Price Reductions Clause) |
| L | HIGH | GSA audits years late; commercial pricing can drift below MFC and not be reported |
| R | MEDIUM | USAspending.gov + GSA Schedule pricing public; commercial pricing partially public (Amazon, vendor websites, public price lists) |

**Verdict:** Promising for IT and commodity goods sold both commercially and via GSA. Match GSA Schedule price to current Amazon/vendor list price; flag where govt is paying more.

---

### 19. State Tax Abatements (TX Chapter 313, NY 485-x, etc.)

| | Score | Notes |
|---|---|---|
| I | HIGH | Per-deal abatements often $10s of millions in school property tax |
| L | HIGH | State comptroller / state tax dept oversight typically weak; school district doesn't audit |
| R | VARIES | Texas had a public Chapter 313 database (program sunset 2022, replaced by Chapter 403); NY 485-x is on NYC Open Data |

**Verdict:** State-by-state research. Could be a high-leverage GTM (state attorneys general, school district unions, journalist coalitions like the Texas Observer / ProPublica Local).

---

### 20. Healthcare Provider Upcoding (CMS billing data)

| | Score | Notes |
|---|---|---|
| I | VERY HIGH | Medicare/Medicaid fraud is multi-billion |
| L | HIGH | CMS audits sample-based; qui tam suits are the main enforcement |
| R | HIGH | CMS Provider Utilization & Payment Data is public (provider × CPT code × volume × charge) |

**Verdict:** Well-trodden territory (qui tam attorneys actively pursue), but the data is genuinely good. Differentiation would have to come from better outlier detection or a better delivery surface to plaintiff firms.

---

### 21. Federal Crop Insurance / NAP Program

| | Score | Notes |
|---|---|---|
| I | HIGH | $20B+/yr in crop insurance subsidies; loss claims often inflated |
| L | HIGH | RMA spot-checks limited; private AIPs have incentive to approve claims |
| R | MEDIUM | RMA Summary of Business (county-level, public); satellite crop yield data (NASS Cropland Data Layer, Planet Labs) accessible |

**Verdict:** Promising. Cross-reference county-level insured-loss claims against satellite-observed crop yields. Anomalies = candidate fraud regions.

---

## Recommended Build Sequence

### Immediate next vertical (highest ILR × leverage of existing infrastructure)

**LIHTC compliance (#13)** — clearest rebuild of the NYC RSL vertical with stronger R (national HUD database vs. NYC-only). Same conceptual engine: legal max rent vs. market rent. Output is buildings nationwide that should be charging income-restricted rents but appear to be charging market.

### Second wave (independent, high-conviction)

- **Carbon offsets (#4)** — methodology already validated by Guardian/SourceMaterial; productizing this is mostly engineering, not novel discovery
- **Conservation easements (#3)** — Catoosa County GA pilot to validate R, then replicate

### Third wave (infrastructure-heavy, high-ceiling)

- **Emissions vs. satellite (#5)** — needs partnership/licensing for satellite data feeds at scale, but the framework fits
- **Crop insurance vs. satellite (#21)** — similar satellite-data requirements; could share infrastructure with #5

### Defer / not now

- 409A, Estate, Art, Customs, M&A, Enterprise — all blocked by R weakness or out-of-model

---

## What an Agent Should Do Next (Post-Review)

After your review, an agent could be tasked with:

1. **For LIHTC vertical:** Pull the HUD LIHTC Property Database. Confirm joinability to a market rent dataset (RentCast / Census ACS). Identify 1 metro area with high LIHTC density to spot-check (Atlanta, Houston, Charlotte are candidates). Build the engine using the existing `verticals/rent_stabilization` skeleton as a template.

2. **For conservation easements:** Pull the Catoosa County GA recorder data for the past 5 years. Filter to instruments tagged as conservation easements. For each, find the underlying parcel's recent comparable sales. Build a valuation outlier score.

3. **For carbon offsets:** Pull the Verra public registry. Get Global Forest Watch tile data for project AOIs. Compute baseline-vs-actual deforestation for a sample of REDD+ projects and reproduce the Guardian methodology.

4. **For each:** before any code, write the I/L/R section into `verticals/<name>/MANIFEST.md` and confirm with you before scaffolding.
