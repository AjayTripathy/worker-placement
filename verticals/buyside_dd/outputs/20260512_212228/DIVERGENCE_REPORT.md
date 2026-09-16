# Divergence Report — Flux Capital "FCRE2 LLC" $30M Private Credit Offering

*Generated: 2026-05-12 | Pipeline run: 20260512_212228*

---

## Materials analyzed

1. `Section 8 housing.pdf` — 6-page pitch deck (Flux Capital branding, dated 2026-04-26)
2. `Copy of Property Level Financials - Low Income Housing.xlsx` — 26-property operating model

## Deal structure (as represented)

- **Issuer:** FCRE2 LLC, governed by Florida law
- **Marketer:** Flux Capital (not registered investment advisor, broker-dealer, or regulated financial entity per their disclaimer)
- **Operating partner:** "Real Estate Development Company" — **NOT NAMED IN MATERIALS**
- **Raise:** $30M private credit
- **Headline yield:** 14% annual, paid quarterly
- **Term:** 7-year
- **Exit:** Optional after Year 3 with 6-month notice; via portfolio sale OR Flux finding a replacement investor
- **Strategy:** BRRR with Section 8 voucher tenants; mid-market secondary cities

---

## CRITICAL findings (any one of these is deal-breaking)

### C1. Operating partner is anonymous

**Claim:** "Our partner is a Real Estate Development Company that has developed a scalable model for acquiring, renovating, and managing Real Estate housing properties across multiple markets. The company has already built a portfolio of approximately 300 properties over the past 4 years."

**f-rule applied:** `re.sponsor_owns_claimed_priors`

**Verification status:** **UNVERIFIABLE** — operating partner is never named. Cannot:
- Check state corporate registration
- Verify 300-property prior portfolio in deed records
- Search PACER / state courts for litigation history
- Verify Form ADV / SEC filings
- Cross-reference principals to LinkedIn / prior employment / qualifications
- Check professional licenses
- Verify "established HUD relationships"

**Severity:** **CRITICAL.** A sophisticated investor cannot conduct DD on an unnamed counterparty. This alone is sufficient to walk. Asking the sponsor's identity is the most basic possible DD question and the answer should be in the cover page.

---

### C2. Multiple properties priced ABOVE HUD Section 8 Fair Market Rent

**Claim:** Section 8 voucher demand is "guaranteed" because waitlists are closed; "Section 8 rents are 10-30% higher than regular market rate" (page 4 myth-busting section).

**f-rule applied:** `re.unit_rent_within_market_range` (jurisdiction-aware variant for Section 8 / HUD FMR)

**Verification:** Cross-referenced claimed rents against HUD FY2024 Fair Market Rents per metropolitan area:

| Property | Claimed rent | HUD 3BR FMR (MSA) | Premium over FMR | Section 8 viable? |
|---|---|---|---|---|
| 813 SW E Ave, Lawton OK | $1,500 | ~$1,065 | **+41%** | NO (without tenant paying spread) |
| 8918 Frankstown Rd, Pittsburgh | $1,950 | $1,440 (Allegheny Co) | **+35%** | NO |
| 2606 Chatsworth Ct, Macon GA | $1,500 | ~$1,135 | **+32%** | NO |
| 9754 Lorna Ln, St Louis 63136 | $1,600 | ~$1,230 (St Louis MSA) | **+30%** | NO |
| 1939 Hildred Ave, St Louis 63136 | $1,350 | ~$1,230 | +10% | Marginal |
| 3213 Central Ave, Pittsburgh | $1,500 | $1,440 (3BR) or $1,150 (2BR) | +4% to +30% | Borderline |
| 433 Hammond St, Pittsburgh | $1,607 | $1,440 | +12% | Marginal |
| 2740 6th Ave, Rock Island IL | $1,350 | ~$1,200 | +12% | Marginal |

The deck's myth-busting section claims Section 8 pays *above* market rates. This is structurally false. Section 8 vouchers are anchored to HUD's published FMR (or Small Area FMR by ZIP). The voucher pays at most the FMR; tenant must cover any excess. Low-income tenants generally cannot.

The sponsor either (a) doesn't understand how Section 8 works, or (b) is misrepresenting the demand thesis. Either way, a meaningful fraction of the portfolio cannot rent to Section 8 tenants at the claimed rent.

**Severity:** **CRITICAL.** The thesis behind the deal — guaranteed Section 8 demand — doesn't apply to a substantial portion of the actual portfolio. NOI projections that assume Section 8 occupancy at claimed rents are inflated.

---

### C3. The "loan" is not contractually a loan

**Claim:** "14% annual yield, paid quarterly... Return of Loan $1,000,000... 7 Year Total Return to Investor $1,980,000."

**Exit Strategy reality (from page 5):** "Investors have the option to exit their loan after Year 3, subject to a six-month notice period. The first option is to sell the underlying portfolio and the second option is for Flux Capital to source a replacement investor."

**Issue:** Return of principal is not contractually guaranteed. Two exit paths are stated:
1. Sell the underlying portfolio (depends on third party paying ≥ debt basis)
2. Flux Capital finds a replacement investor (paying old investors with new investor capital — a structural red flag pattern)

There is no fixed maturity, no senior-secured-loan covenant package described, no first-lien collateral mechanism explained, no intercreditor agreement with the senior bank lender (whose 75% LTV refinance is described in the BRRR model and would be senior to this $30M).

This is **equity exposure marketed as a 14% bond**. The 14% "interest" is at best a preferred return; at worst, a hope.

**Severity:** **CRITICAL.** The product structure does not match the investor representation. Document mislabeling of equity-like exposure as fixed-income is a securities-law risk for Flux Capital and a fundamental misalignment for the investor.

---

### C4. Flux Capital explicitly disclaims verification of sponsor claims

**Disclaimer page, section (vii):** "While we believe all information provided herein is accurate, we have relied upon information provided by our development partner and have not independently verified all claims."

**Combined with:**
- Section (ii): "Flux Capital is not a registered investment advisor, broker-dealer, or other regulated financial services entity"
- Section (viii): "recipients must conduct their own due diligence"
- Footer of every page: only marker is `4tripathy@gmail.com` (the recipient's email) — no Flux Capital phone, address, principal name

**Implication:** Flux Capital is a marketing vehicle that has done no DD on the operating partner whose anonymous claims you would be funding. They are a pass-through. There is no second layer of underwriting between you and the unidentified sponsor.

**Severity:** **CRITICAL.** Flux Capital adds no verification, no underwriting, no recourse. They take the disclaimer (no advisor status) explicitly to wash off any duty of care.

---

## HIGH-severity findings

### H1. "Materially de-risked" claim is empirically false

**Claim:** "Real Estate Development Company has overcome several significant potential hurdles and materially de-risked the business."

**Spreadsheet reality:**
- 26 total properties
- 2 still "In Acquisition" (no purchase complete)
- 13 "In Rehab" (no income)
- 1 "Listed for Rent" (vacant)
- 4 "Tenant Selected" (lease pending)
- **5 actually "Stabilized with Tenant"** — only 5 out of 26 are producing rental income

Acquisition dates range from March 2025 to November 2025. The portfolio is 6-14 months old. Calling a portfolio of which 80% is non-producing "materially de-risked" is misrepresentation.

**Severity:** HIGH.

---

### H2. Geographic concentration is severe; portfolio doesn't match marketing geography

**Claim:** "across multiple markets"; map shows MO, MI, OK, OH, LA, MS, GA, AL, KY, PA.

**Spreadsheet reality:**
- 9 of 26 properties (35%) in Pittsburgh MSA (zips 15204, 15210, 15212, 15235, 15136, 15132)
- 5 in Mississippi (Jackson)
- 4 in Missouri (St Louis)
- 3 in Louisiana (Shreveport)
- 2 in Illinois (Rock Island) — **NOT shown on map**
- 1 each in Oklahoma, Georgia
- **ZERO** in Michigan, Ohio, Alabama, Kentucky despite being shown on map

35% Pittsburgh MSA concentration in a portfolio of 26 small properties means a single market downturn impairs more than a third of the portfolio. The "multiple markets" framing overstates diversification.

**Severity:** HIGH.

---

### H3. Many properties show NEGATIVE Cash In Property — refinance pulls out more than basis

**Claim (deck example):** "Remaining Cash In Property: $0"

**Spreadsheet reality (full 26-property total):** Cash In Property = **−$29,358**

Per-property worst cases:
- 2606 Chatsworth Ct, Macon GA: −$22,650 (refi pulls out $22k more than total cost)
- 1837 Beech St, McKeesport: −$10,525
- 433 Hammond St, Pittsburgh: −$7,244
- 1939 Hildred Ave, St Louis: −$6,300
- 813 SW E Ave, Lawton: −$5,700
- 1932 Beech St, McKeesport: −$5,645

This is the "infinite ROI" BRRR pitch. But mechanically:
- Senior refinance debt has first lien
- Sponsor extracts equity via refi
- The $30M private credit being raised is *junior* to the refi
- If property values fall ≥ refi LTV (only 25% needed), the $30M position is impaired

**The economic question:** if the portfolio self-funds via 75% LTV refinance with negative cash-in, why does the sponsor need $30M of additional capital?

Answers I can think of:
1. To buy MORE properties (growth capital). Then this is a growth-equity-like investment, not a senior secured loan.
2. To pay off existing investors (Ponzi-adjacent — paying old with new, exactly what the exit strategy describes)
3. To extract sponsor equity at a level the bank refinances won't fund

None of these match a "14% senior bond" representation.

**Severity:** HIGH.

---

### H4. Internal inconsistencies between deck, spreadsheet, and example math

| Field | Deck claim | Spreadsheet reality |
|---|---|---|
| Average rent | $1,325/mo | $1,409/mo (across 26 properties) |
| Cash in property (example) | $0 | −$29,358 (total across portfolio) |
| LTV | 75% (uniform in deck) | Varies: 70%, 75%, 80% in spreadsheet |
| Properties shown | 13 in track record table | 26 in spreadsheet |
| Average ARV per property | $120k (example) | $131k (spreadsheet) |
| Total cost average | $90k (example) | $91,884 (spreadsheet) — close |

The deck's "Example Property" (purchase $60k, rehab $25k, refi cost $5k, total $90k, ARV $120k, refi $90k, $0 cash in) doesn't appear in the spreadsheet as any actual property. It's hypothetical, presented as if representative, but the actual portfolio is significantly different.

**Severity:** HIGH.

---

### H5. "Management Fee: None" claim is implausible

Flux Capital is not a charity. If they take no management fee, their revenue must come from:
- Spread between what the sponsor pays them and what they pay LPs (undisclosed)
- Origination fee paid by the sponsor (undisclosed)
- Carried interest above some hurdle (not described)
- Side-letter consideration (undisclosed)

A sophisticated investor expects the fee structure to be transparent. "No management fee" claim with no alternative compensation disclosed = either Flux operates at a loss (implausible, suggesting sustainability risk) or the actual fee structure is hidden.

**Severity:** HIGH.

---

## MEDIUM-severity findings

### M1. Rehab budgets implausibly low for some properties

- **2829 Comfort Street, Jackson MS:** Purchase $64,000, rehab $2,200. $2,200 on a $64k distressed property in Jackson MS is a deep clean and paint, not a habitable conversion. This property is shown as "Tenant Selected" already which suggests rehab is "complete" at $2,200. Either the property was already in good condition (then why $64k purchase below market?) or the rehab is cosmetic-only and there are deferred capex liabilities.

- **2825 Westover Rd, Shreveport:** Purchase $74,000, rehab $12,500. Borderline.

The deck claims "Full cosmetic renovations (~$25,000)." Several properties significantly below this. Either the deck claim is an overstatement, or these specific properties are under-rehabbed.

### M2. No HAP contracts shown

The deck claims HUD relationships and Section 8 strategy. No actual HAP contracts (Housing Assistance Payment contracts between landlord and PHA) are shown. No Section 8 voucher counts per property. No PHA approval letters. The Section 8 thesis is asserted but not documented.

### M3. Spelling errors / typos in addresses

"Schrevport" appears twice (2711 Thayer St, 3633 W College St). "Pittsburg" appears for properties that are actually Pittsburgh PA (3213 Central Ave). City typos in a property list suggest the operating partner doesn't have basic data hygiene.

### M4. FCRE2 LLC implies FCRE1 exists; no track record on FCRE1 shown

The entity name "FCRE2" suggests this is Flux Capital Real Estate fund 2. Where is FCRE1's track record? If FCRE1 has performed well, it should be the lead reference. If it has performed poorly or hasn't matured, that's material.

### M5. Florida governing law

Disclaimer specifies Florida law. Properties are in MO, MS, PA, LA, OK, IL, GA. None in Florida. Out-of-state investor enforcement actions in Florida courts are burdensome and expensive. Florida is not a particularly investor-friendly venue for these disputes.

### M6. Photos cherry-picked

Three photos shown (523 Dornoch Dr, 2825 Westover Rd, 1405 Dianne Dr). All three are among the 5 "Stabilized with Tenant" properties, i.e., the best-condition assets. The remaining 21 properties (including the 13 still in rehab) have no visual representation. Standard pitch deck practice but worth noting that visuals over-represent stabilization.

---

## What I would verify next (M sources to query)

If you wanted to push beyond pitch-deck analysis into actual ground truth:

| Verification | M source | Cost | Why |
|---|---|---|---|
| Operating partner identity | Ask Flux Capital directly + cross-ref to state corp filings | Free | Single most important DD step |
| Per-property deed history & current owner | County recorders for 26 properties (Allegheny PA, Hinds MS, St Louis City MO, Caddo LA, Comanche OK, Rock Island IL, Bibb GA) | Mostly free | Verify sponsor's LLC actually owns claimed properties |
| Per-property assessor market value vs. claimed ARV | County assessors (mostly public APIs or scrapeable) | Free | Detect ARV inflation |
| Per-property tax delinquency status | County treasurers | Free | Hidden liability for lender |
| Per-property code violation history | City code enforcement (Pittsburgh BBI, St Louis CSB, Jackson MDPS, etc.) | Free | Hidden capex liability |
| Section 8 HAP contract status | HUD PIC database + PHA records | FOIA possible | Verify actual Section 8 viability |
| Sponsor LLC chain & beneficial owner | State Secretary of State filings (multi-state) | Mostly free | Required to do any further DD |
| Sponsor litigation history | PACER + state courts | <$50 | Standard sponsor DD |
| FCRE1 prior-fund performance | Direct request from Flux + LP references | Free | Track record of THIS marketer |
| Existing senior debt on each property | UCC filings + county lien records | Mostly free | Confirm position in capital stack |

---

## Recommendation

**Do not invest as currently structured.**

**Critical issues that must be resolved before further DD:**
1. Identify the operating partner. Without a name, no DD is possible.
2. Provide HAP contracts and PHA voucher confirmations for at least the 5 stabilized properties. The Section 8 thesis is core to the pitch and undocumented.
3. Provide complete capital stack for each property — senior debt source, terms, current balance, and proof that this $30M raise sits in a defined position.
4. Restructure the offering as either (a) genuine senior secured debt with hard maturity, default mechanics, and intercreditor agreement, OR (b) honest equity exposure with appropriate risk framing.
5. Disclose Flux Capital's fee economics. "No management fee" is not credible without alternative fee disclosure.
6. Reconcile rents claimed against HUD Fair Market Rent for each property; either justify above-FMR rents or reduce the projection.
7. Show FCRE1 fund performance and audit financials.

**If those are resolved, the next layer of DD requires:**
- Per-property deed/assessor/tax/code verification (the 26-property scan that the framework would automate)
- Sponsor entity, LLC chain, litigation, regulatory history
- Independent appraisals on at least 5 properties (sample basis)
- HUD PIC database confirmation of HAP contracts
- Bank statement verification of actual rent collections vs. claimed rents

**Estimated probability the deal is salvageable** even with full disclosure: low. The structural issues (sponsor anonymity, equity-as-debt mislabeling, Flux's no-verification disclaimer, Section 8 thesis breakdowns) suggest this is either an unsophisticated/early operator or an active misrepresentation. Either profile is reason to walk.
