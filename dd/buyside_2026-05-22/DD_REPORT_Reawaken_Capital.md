# Due Diligence Report — Reawaken Capital, LLC

*Prepared 2026-05-22. Data room received 2026-05-22 (zip dated 2026-05-22T18:53:22Z). Subject: Reawaken Capital, LLC (CIK 0002035385). 15 documents reviewed (FAQ deck, investment thesis, pipeline xlsx, 13 marketing blogs). Verification via SEC EDGAR (Form D), corporate registries, web research. Standard buyside R/f/M discipline applied.*

---

## Disclaimer

**This document is algorithmic research, not investment, legal, accounting, or tax advice.** The author is not a registered investment adviser, broker-dealer, attorney, CPA, or licensed fiduciary, and nothing in this report should be construed as creating a fiduciary, advisory, or professional-services relationship with any reader. The author has no duty of care to any recipient and is not acting on behalf of any investor.

This report is a private analytical exercise produced by automated and manual review of publicly available information (SEC EDGAR, corporate registries, web sources) plus documents shared in the named data room. All findings, severity scores, and recommendations reflect the author's research process at a point in time and may be incomplete, mistaken, or out of date. Material facts may exist that were not provided in the data room or are not visible in public records.

No warranty — express or implied — is made as to the accuracy, completeness, or currency of any statement in this report. Citations to third-party sources are provided as starting points for the reader's own verification, not as endorsements. Past performance, backtested returns, and pro-forma projections in any cited source are not indicative of future results.

**Any investment decision is solely the reader's responsibility.** Before committing capital, the reader should: (a) obtain and review the issuer's PPM, LPA, subscription agreement, and audited financials; (b) consult a qualified attorney regarding securities, partnership, and tax-law implications; (c) consult a CPA regarding personal tax consequences (including but not limited to UBTI, K-1 timing, state tax, and harvest mechanics if any are referenced herein); (d) consult a licensed investment adviser regarding suitability and portfolio fit; and (e) consider commissioning an independent background check on principals through a licensed provider.

This report contains observations and questions for the reader to put to the issuer — it does not substitute for direct dialogue with the issuer, independent counsel, or qualified investment professionals. The reader is responsible for assessing whether the issuer's responses to the questions raised herein are satisfactory.

The author may have, or may in the future acquire, positions in real estate, publicly traded securities, or private vehicles mentioned in this report, and has no obligation to update the reader on changes to such positions. Nothing herein is a solicitation, offer, or recommendation to buy or sell any security or interest.

By reading further, the reader acknowledges this disclaimer and agrees that no advisory relationship is created or implied.

---

## Executive Summary

**Conclusion: DECLINE pending material remediation.** Seven findings, listed in order of severity:

1. **🚩 Pipeline is unverifiable on its face.** Pipeline xlsx column titled "Address (Zillow Link)" contains **only city + zip code** for all 1,075 rows — zero street addresses, zero hyperlinks. The single most damning finding in the data room. Every purchase price, ARV, construction budget, and pro-forma return is self-attested with no documentary path for independent verification against Fulton County deed records, assessor data, or Zillow comps. See Appendix A for the full inspection.

2. **🚩 No verifiable prior track record.** Marketing material cites "historical ROI annualized from a separate investment vehicle managed by the same team over a 6-year period," but no such vehicle exists in any SEC filing, business registry, or public record. Full-text search of EDGAR returns exactly **one** filing naming Dylan Peters: Reawaken's own 2024 Form D. See Appendix D.

3. **🚩 Multiple direct contradictions** between data-room FAQ and the fund's own Form D filing:
   - FAQ: "minimum check $50K" vs Form D: minimum investment **$20,000**
   - FAQ: "accredited investors only" vs Form D: `hasNonAccreditedInvestors: TRUE`

4. **PadSplit operator dependency, not disclosed.** Pro forma includes a 12% "Platform Fee" matching PadSplit's host fee exactly; pipeline notes reference prior PadSplit conversions ("Harper", "Baywood"). The FAQ's "in-house portfolio management" claim is misleading — Reawaken depends on PadSplit as its tenant operator. See Appendix B.

5. **Single-principal structure** — Form D lists only Christopher Dylan Peters as related person. However pipeline notes reference active team members "Josh", "Scott", and "Bowser" — either a Form D under-disclosure or marketing-material misrepresentation of who the "team" is. See Appendix C.

6. **Misleading pro-forma math** — headline 24% "cap rate" is computed against purchase price only, ignoring construction cost; the spreadsheet's own UYOC column shows the honest metric at **10.8%**.

7. **Operational gaps** — mail-suite address in Las Vegas despite "Atlanta foothold" claim; principal's only formal commercial-RE role lasted 1 year (Jan 2021 – Jan 2022); $993K raised from 6 investors as of last Form D (fund still in early launch).

The verification matrix below details each finding. **Findings 1–3 are independent grounds for DECLINE.** Findings 4–7 are material context that would shape sizing and reporting requirements even if 1–3 were resolved.

---

## 1. Verified Facts (SEC EDGAR Form D, filing 0002035385-24-000001)

| Field | Value |
|---|---|
| Entity name | **Reawaken Capital, LLC** |
| CIK | 0002035385 |
| State of incorporation | **Nevada** |
| **Year of incorporation** | **2024** |
| Industry | Pooled Investment Fund (Other Investment Fund); NOT 40 Act registered |
| Exemption | **Reg D, Rule 506(b)** |
| Date of first sale | **2024-06-12** |
| Form D filing date | 2024-08-28 |
| **Minimum investment** | **$20,000** |
| Total offering | $4,000,000 |
| **Amount sold (as of filing)** | **$992,564** |
| Remaining | $3,007,436 |
| **Total investors** | **6** |
| **Has non-accredited investors** | **TRUE** |
| Sales commissions / finder fees | $0 / $0 |
| Gross proceeds used | $0 (no proceeds to officers) |
| Related persons disclosed | **Only one: Christopher Dylan Peters, Executive Officer / Managing Member** |
| Operating/mailing address | 304 S. Jones Blvd #4203, Las Vegas, NV 89107 (virtual mail suite) |
| Phone | 845-532-4034 |

**Source**: SEC EDGAR primary_doc.xml at https://www.sec.gov/Archives/edgar/data/2035385/000203538524000001/

---

## 2. Material Contradictions — FAQ vs Form D

This is the most important section. The fund's own SEC filing contradicts representations made to prospective LPs:

| Claim in FAQ deck | Stated in Form D | Severity |
|---|---|---|
| "Our minimum check is $50k. The average check is $250k." | Minimum investment $20K; 6 investors / $993K = **$165K average** | **MOD** — both numbers wrong; $20K min understates per-LP commitment narrative |
| "We work with accredited investors who meet specific criteria as defined by the SEC." | **`hasNonAccreditedInvestors: TRUE`** — non-accredited investors already accepted | **RED** — direct misrepresentation. Legal under 506(b) (up to 35 non-accreds with sophisticated-investor representation) but the FAQ statement is false on its face. |
| "We have in house portfolio management coupled with strong relationships with third party property managers **we have used for the past decade**." | Entity formed 2024; only related person is one principal whose prior RE role was 1 year. | **SEVE** — "past decade" implausible for the entity; ambiguous whether Peters personally has documented 10 years of RE PM relationships |
| "Family heritage in architecture, allowing us to oversee and enhance every aspect of the investment process" | Not in Form D; no verifiable family-firm reference in public records | **UNVERIFIABLE** — material to "unique advantage" claim; should be substantiated with named family business |
| "Returns are typically distributed on a quarterly basis" | Form D does not disclose distribution mechanics; fund is too new (~2 mo at filing) to have established cadence | **UNVERIFIABLE** — first cycle is forward-looking, not historical |
| "Currently developing a strong foothold in Atlanta" | Operating address is Las Vegas mail suite; no Atlanta office | **MOD** — no operational presence in target market; relies on contractors/third parties |

---

## 3. Principal — Christopher Dylan Peters

### What's verifiable
- **Formal commercial RE experience**: Vice President at Recreate Commercial Real Estate, Jan 2021 – Jan 2022 (~1 year)
- Subsequently: Reawaken Capital, General Partner / Managing Member (2024–present)
- LinkedIn bio claim: "over a decade of experience across real estate, technology, and operations" — *aggregate*, not RE-pure
- Identified at: https://www.linkedin.com/in/dylan-peters-re/

### What's NOT verifiable
- **No prior fund track record**. Reawaken's own website says "historical ROI annualized from a separate investment vehicle managed by the same team over a 6-year period" — but the dollar return is not specified, and no prior fund entity is publicly identifiable.
- **"Family heritage in architecture"** — the family business is not publicly named.
- **"Decade-long property manager relationships"** — no documentation of any specific PM relationship spanning 10 years.
- **No real estate license verified** for Peters in GA, NV, or CA (broader searches return no direct hit).
- **No CFO, COO, board member, or co-GP** listed on Form D. Single-principal structure with $4M offering.

### What this means
- **Key-person risk is extreme.** Death/disability/departure of Peters effectively dissolves the fund's operating capacity.
- **No segregation of duties** at the fund level. One person controls acquisitions, financing, valuations, and capital calls. Material for institutional investors who require operational controls.

---

## 4. Pipeline Snapshot (xlsx)

### 🚩 Critical: addresses are stripped — pipeline is unverifiable on its face

The pipeline xlsx column is literally titled **"Address (Zillow Link)"** but contains only city + zip code in every one of the 1,075 data rows. No street numbers. No hyperlinks. No way to cross-check any property against:
- Fulton County tax assessor (sq ft, year built, assessed value, owner of record)
- GSCCCA deed index (purchase date, purchase price, deed-holder LLC)
- Zillow / Redfin / MLS (asking price, days on market, sale comps)
- Building permits (work scope, contractor, certificate of occupancy)

**The pro-forma numbers are entirely self-attested. No independent verification path exists for any property.** The column header strongly implies the source spreadsheet contained full addresses and Zillow links, which were stripped before sharing. See Appendix A for full inspection details (sharedStrings, comments, drawing layers — all examined; no hidden addresses found).

This is a **RED_FLAG_NEGATIVE on the entire pipeline**. For any property-level diligence to proceed, the GP must provide a CSV/xlsx with addresses restored.

### What was provided (with addresses stripped)
- 1,076 rows × 64 columns spreadsheet titled "Current Pipeline Snapshot (Shared)"
- Status distribution: **"Won"** (verified count via parse), **"In Contract"**, **"Offer"**, **"Low Interest"**, **"Lost/Pending"**, **"Needs Input"**
- Investment type: mostly **Construction** (fix-and-flip-to-rental), some Turnkey
- Geographic concentration: **~95% Atlanta zip codes** — specifically 30310, 30314, 30315, 30318 (West Atlanta gentrifying neighborhoods: Pittsburgh, English Avenue, Westview, University Park, Lakewood Heights). **Caveat**: even the zip-level geography cannot be independently verified to any property Reawaken actually controls.

### Pro-forma metrics (sample "Won" property)
| Metric | Stated value | Independent check |
|---|---:|---|
| Purchase price | $128,000 | — |
| Construction cost | $145,000 | — |
| Total basis | $283,880 | — |
| ARV | $350,000 | (no MLS comp in data room) |
| Gross monthly rent | $4,875 | Assumes co-living: 5 ensuite × $975/wk + shared $715/mo |
| Annual NOI | $30,788 | — |
| **"CAP RATE"** | **24.0%** | **MISLEADING — computed NOI ÷ purchase price ($128K), NOT NOI ÷ total basis ($283K). Standard cap rate = NOI ÷ all-in basis = 10.8% (the "UYOC" column).** |
| Y1 levered return | 187.4% | Assumes 75% LTV refi + cash-out — heroic if achievable |
| ROI (after refi) | 154.2% | — |

### Pro-forma red flags

1. **The "24% cap rate" is misleading-by-construction.** A cap rate is universally NOI ÷ all-in basis. Reawaken's calc divides NOI by *purchase price only*, ignoring the $145K construction spend (~50% of basis). The honest metric is in their own spreadsheet as "UYOC" (Unlevered Yield on Cost) at **10.8%** — strong but not extraordinary. Showing the 24% number in marketing is misleading.

2. **Co-living rent assumptions are aggressive.** $975/wk per ensuite room = $4,225/mo. West Atlanta zip codes (30310, 30314, 30315) have median single-family rent of $1,500–$2,200/mo per Zillow/RentCafe. Achieving $4,225/mo from a single property requires 5-room co-living model with near-100% occupancy. Vacancy reserve in pro forma is 15% — may be too tight given coliving market churn.

3. **Refi assumption** of 75% LTV at 6.875% is current-market-reasonable, but assumes the ARV is realized post-construction. ARV of $350K on 30314 SFR is at the upper end of recent comps; sensitivity to neighborhood comps is high.

4. **No DSCR, IRR, or fund-level returns calculation** in the snapshot. Pro forma is per-property, not portfolio-level. Investors cannot verify the fund's blended target IRR from the data provided.

5. **"Pretty rough water issue downstairs"** type notes on multiple "Won" properties — water issues are expensive and the cost is not always reflected in the construction budget. Hidden capex risk.

---

## 5. Operational / Disclosure Gaps

### Items missing from the data room

| Item | Why it matters | Suggested ask |
|---|---|---|
| Audited financials (entity or prior vehicle) | Confirms historical performance claim | Request 2023 + 2024 audited statements; if not available, tax returns |
| LPA / PPM / subscription agreement | Defines economics, GP carry, fees, redemption mechanics | Standard request |
| Form ADV (if RIA) | Disciplinary history, AUM, conflicts | Confirm whether Peters is registered investment adviser |
| Prior fund track record (named entity) | "Separate investment vehicle over 6 years" needs to be a named LLC with provable returns | Ask for entity name, vintage, IRR, DPI, audit |
| Property closing statements | Confirms purchase prices and basis | Pick 3 "Won" properties — request HUD-1/CD plus rehab budget |
| Bank statements / capital account statements | Confirms $993K really held in trust | Pre-close requirement |
| Insurance certificates | E&O, GL, prop coverage | Standard request |
| Background check on Dylan Peters | Litigation, bankruptcies, judgments | Order independent check before commit |
| Construction subcontractor list with lien-history references | Material to value-add execution risk | Confirm GC track record |
| Property manager contracts | The "decade-long relationships" claim — name them | Critical because PM is in-house per FAQ but external partners cited too |

### Marketing content vs operating content

Of the 15 documents in the data room:
- **1** is operational (pipeline.xlsx)
- **1** is semi-operational (FAQ.docx — but mostly marketing)
- **1** is thesis (investment thesis.docx — narrative)
- **12** are blog posts (general real-estate marketing content; many indistinguishable from generic SFR-fund collateral)
- **0** are audited financials, legal docs, capital account statements, principal background, or third-party diligence

**This is a thin operational data room for a $4M offering.** Buyside diligence typically expects PPM, LPA, prior-vehicle audited returns, principal bios with references, and at minimum sample closing docs.

---

## 6. R/f/M Severity Scoring

| Claim | Severity | Source verification |
|---|---|---|
| Entity exists / registered | PASS | SEC EDGAR confirms NV LLC, 2024 |
| Filed Form D | PASS | EDGAR 2024-08-28 |
| Min investment $50K | **RED_FLAG** | Form D says $20K → direct contradiction |
| Accredited-only investor base | **RED_FLAG** | Form D `hasNonAccreditedInvestors: TRUE` |
| Past decade of PM relationships | **SEVERE_UNDERDELIVERY** | Entity 1 year old; principal's known RE role 1 year |
| Family heritage in architecture | UNVERIFIABLE | No public record of family firm |
| "$250K average check" | **MODERATE** | Implied math ($993K / 6) = $165K |
| 24% cap rate (per-property pro forma) | **SEVERE** | Misleading — computed against purchase price only; correct metric is UYOC 10.8% |
| Atlanta operating presence | **MODERATE** | LV mail suite; no GA office, no GA registered agent verified |
| Single-principal structure | **MODERATE** (structural, not a claim) | Form D lists one related person |
| 6-year prior-vehicle track record | UNVERIFIABLE | No named entity, no audit |
| Quarterly distributions | UNVERIFIABLE | Fund is too new |
| Portfolio sale / PE exit | UNVERIFIABLE | Future event |

**Composite severity (weighted average, excluding UNVERIFIABLE)**: 2 RED + 2 SEVE + 2 MOD on 8 verifiable claims = (2·3 + 2·2 + 2·1) / 8 = **1.50 — SHORT-tier conviction** under the framework rubric.

---

## 7. What's strong about Reawaken

To be fair to the fund:

- **Specific, narrow geographic focus** (West Atlanta) is defensible — these zips have legitimate gentrification momentum and the price points ($30K-80K/unit basis) are real wholesale opportunities for skilled rehabbers.
- **Form D was actually filed** — many sub-$1M raises operate under 4(a)(2) without filing. Voluntary 506(b) filing is the more compliant path.
- **Pro forma transparency** — even though the headline cap rate is misleading, the underlying UYOC/cash-on-cash math IS in the spreadsheet for an investor who reads carefully.
- **Marketing thesis is internally consistent** — inflation hedge, residential demand, gentrification arbitrage. Reasonable narrative for the strategy.
- **Reasonable fund size** — $4M is small enough to deploy in 15-25 SFR deals in West Atlanta, which is actually executable in 12-18 months.

---

## 8. Recommended Next Steps (Pre-Commit)

### Critical (DO NOT COMMIT WITHOUT)

1. **Principal interview** — 60-90 min with Dylan Peters:
   - Direct question on minimum-check inconsistency: is $50K policy or $20K legal floor?
   - Direct question: who are the non-accredited investors? sophisticated-investor representation in place?
   - Walk through prior 6-year vehicle: entity name, audit, GP/LP structure, performance metric reconciliation
   - Name the family architecture firm
   - Identify the "past decade" property managers — call references at 2 of them
   - Walk through 1 specific "Won" deal end-to-end: closing docs, rehab budget, comps, lender, current rent roll
2. **Independent background check** on Christopher Dylan Peters — litigation, bankruptcy, judgments, prior business filings
3. **PPM and LPA review** by counsel
4. **Audited returns from prior 6-year vehicle** — if no audit exists, that itself is a flag
5. **Title chain check** on 2-3 "Won" properties via Fulton County GSCCCA — confirm Reawaken-controlled LLC owns them
6. **GP carry / fee economics** — not in data room; must be disclosed

### Strong-to-have

7. Tour 2 properties in person (West Atlanta zips)
8. Talk to one named third-party PM
9. Independent appraisal review on 1-2 ARV claims
10. Verify Peters' VP-RecreateCRE tenure with company directly
11. State licensing check (NV broker, GA broker if operating)

### Nice-to-have

12. Identify the 6 existing LPs (sub-doc review during own subscription process)
13. Discuss reporting cadence and capital-call mechanics

---

## 9. Sizing Recommendation

If the principal interview clarifies the FAQ contradictions to satisfaction AND the audited prior-vehicle track record materializes:

| Verdict | Sizing |
|---|---|
| All critical items resolve cleanly | **Standard check ($50K–$250K)** with active reporting requirements |
| Some items remain unclear but no red flags surface | **Small test check ($20K–$50K minimum)** with quarterly check-ins |
| Material items remain unclear | **DECLINE** — too many disclosure gaps for $4M offering with single-principal exposure |

**Current state**: 2 RED + 2 SEVE outstanding. **Lean DECLINE pending interview.**

---

## 10. Sources

| Reference | URL / Citation |
|---|---|
| SEC EDGAR Form D | https://www.sec.gov/Archives/edgar/data/2035385/000203538524000001/primary_doc.xml |
| Reawaken Capital website | https://reawakencap.com/ |
| Dylan Peters LinkedIn | https://www.linkedin.com/in/dylan-peters-re/ |
| Recreate Commercial Real Estate | https://www.recreatecre.com/ |
| Crunchbase Reawaken Capital | https://www.crunchbase.com/organization/reawaken-capital |
| Fulton County deed search (GSCCCA) | https://search.gsccca.org/RealEstate/ (login required) |
| Nevada license lookup | https://red.nv.gov/Content/Online_Services/License_Lookup/ |
| Form D primary doc (raw) | https://www.sec.gov/Archives/edgar/data/2035385/000203538524000001/ |

---

## Appendix A — Pipeline Verification Against Public Records (CRITICAL)

A direct verification of pro-forma numbers (purchase price, ARV, sq ft, year built) against Fulton County assessor data and Zillow sale comps was **attempted but not possible**. The reason is the most significant disclosure gap in the data room.

### The pipeline column is labeled "Address (Zillow Link)" but contains no addresses and no links

Inspection of the raw xlsx (sharedStrings.xml, sheet1.xml, comments1.xml, vmlDrawing1.vml — all underlying parts):

| Item checked | Result |
|---|---|
| Header for column A | "Address (Zillow Link)" |
| Cell values in column A (1,075 rows) | **City + ZIP code only**. Examples: "Atlanta, GA 30314", "Atlanta, GA 30310", "East Point, GA". **No street numbers anywhere.** |
| Hyperlinks anywhere in workbook | **Zero** — total hyperlink count: 0 |
| HYPERLINK() formulas | None |
| Hidden columns | None |
| Comments / threaded notes | 4 comments, all about basement-sqft assumptions; **no addresses** |
| VML / drawing layers | Empty (no embedded text) |
| Street references in the entire shared-strings table | **Exactly one** — in a deal-note for a separate property, referencing comp **"2126 Beecher sold for 450k"** (not a Reawaken property, just a comp citation) |

**Consequence**: an investor cannot verify a single property in the pipeline against:
- Fulton County tax assessor (sq ft, year built, assessed value, owner of record)
- GSCCCA deed index (purchase date, purchase price, current owner LLC)
- Zillow / Redfin (asking price, days on market, Zestimate, prior sale history)
- Building permits (work scope, contractor name, certificate of occupancy)
- MLS comps for the ARV estimates

The Pro-forma numbers stated in the spreadsheet — Purchase Price, ARV, Construction Cost, Rent — are entirely **self-attested**, with no documentary or registry path for independent verification.

### How this should have been provided

A standard pipeline data room for an SFR fund typically includes:
- Full street addresses per row (NOT zip-only)
- Live Zillow / Redfin links per row (consistent with the column header)
- Closing statements (HUD-1 or Closing Disclosure) for "Won" properties
- Title commitment or owner's policy showing the deed-holder LLC
- Appraisal or BPO for ARV estimates ≥ $400K
- Construction budget detail with GC name + estimate dates

None of these are provided. The "Address (Zillow Link)" column header strongly suggests the source spreadsheet **did contain** full addresses and links, which were stripped before sharing. This is consistent with either deliberate redaction (to prevent independent diligence) or a careless export. Neither explanation is good.

### Severity

**RED_FLAG_NEGATIVE on the entire pipeline**. The pro forma is detailed and internally consistent on a per-row basis, but every per-row number is unverifiable. **This is the single biggest issue in the data room.**

### Critical pre-commit ask

Request: **CSV or xlsx of the same pipeline with full street addresses and Zillow links preserved**. If the GP declines or provides only "Won" property addresses, that itself is informative — institutional buyside DD requires per-property verifiability.

---

## Appendix B — PadSplit Dependence (operational risk)

The pipeline notes and pro-forma columns reveal a key operational fact NOT disclosed in the FAQ.

### What's in the spreadsheet

| Pro-forma column | Value | Meaning |
|---|---|---|
| "Platform Fee (12%)" | line item | This matches **PadSplit's standard host platform fee** |
| "Ensuite Units: 5" | unit count | Co-living conversion model |
| "Ensuite Weekly Rate: $975" | rent assumption | (column says "Weekly" but the math — 5 × $975 = $4,875 monthly gross — implies the number is monthly; column is mis-labeled. Either way the number is reasonable for PadSplit Atlanta market.) |
| Notes referencing "Harper" and "Baywood" as prior PadSplit conversions | qualitative | Suggests team has operated PadSplit properties before |
| "Existing padsplit conversions like Harper, or Baywood" (note in row ~150) | qualitative | Confirms reliance on PadSplit operator |

### What this means

**Reawaken's strategy is essentially a PadSplit operator capital aggregator.** Buy SFR → renovate as co-living → list on PadSplit → collect platform-fee-net rent. This is a legitimate strategy, but it has implications the FAQ doesn't acknowledge:

1. **"In-house portfolio management" claim is misleading.** The actual operator is PadSplit (third-party). Reawaken's "in-house" appears to be construction/value-add only, not tenant-side property management.
2. **Concentration risk on PadSplit as a single platform.** If PadSplit changes its fee structure, restricts new conversions, or has its own existential risk, every Reawaken property is impaired simultaneously.
3. **Recent PadSplit-specific risks**: PadSplit has been the subject of municipal/regulatory pushback in Atlanta and elsewhere (zoning, occupancy permits, neighborhood opposition). Worth monitoring.
4. **Properties cannot be operated as traditional SFR** with the same cash-flow profile. The pro-forma 33% cash-on-cash return requires PadSplit-style co-living rents. Conventional single-family rental at $1,800-2,200/mo in 30310/30314 zips would produce drastically lower cash flow.

### Sources

- PadSplit website: https://www.padsplit.com/
- Atlanta PadSplit investing guide (third party): https://www.jakenfinancegroup.com/atlanta-padsplit-investing-a-2026-guide-to-high-cash-flow

### Severity

**MODERATE_UNDERDELIVERY** on the "in-house portfolio management" claim — Reawaken depends on PadSplit as the operator. Not catastrophic (PadSplit is a legitimate operating partner), but the FAQ misrepresents the operational structure.

---

## Appendix C — Undisclosed Team Members

The Form D lists **only Christopher Dylan Peters** as a related person. But the pipeline notes reference active deal-team participants who are not on the Form D:

| Name in deal notes | Apparent role |
|---|---|
| "Josh" | Underwriter / acquisitions ("Josh says he'd take 240k", "Josh thinks it could fit as much as 10 BRs", "BOWSER HAS CONFLICT" suggests Josh is one of two team members and Bowser is another) |
| "Scott" | Property walker / inspector ("Scott walking it tomorrow") |
| "Bowser" | Team member with a conflict on a specific deal |

### Implications

- **Form D under-disclosure risk**: Reg D requires listing all "executive officers, directors, and promoters." If Josh, Scott, or Bowser are involved in management or solicitation, they should be on Form D and aren't.
- **Or, contractor/employee misrepresentation**: alternatively, they may be 1099 contractors not requiring Form D disclosure — but the FAQ's "team" language implies executive involvement.
- **Independent verification**: ask Peters to identify each of these people, their formal roles, and whether they're employees, contractors, or co-GPs.

### Severity

**MODERATE** — either a Form D under-disclosure or a team-misrepresentation in marketing material. Should be clarified pre-commit.

---

## Appendix D — Investigation of Prior 6-Year Vehicle

The website claim "historical ROI annualized from a separate investment vehicle managed by the same team over a 6-year period" was investigated. **No public record of any such vehicle was found.** Specifics:

### SEC EDGAR

Full-text search for "Christopher Dylan Peters" returns **exactly one filing**: Reawaken Capital, LLC Form D (2024-08-28). Full-text search for "Dylan Peters" returns **two filings**: Reawaken's Form D plus a 2021 Jaguar Health (JAGX) proxy filing where Peters appears as a Recreate CRE representation contact (NOT an investment vehicle).

**Conclusion: there is no SEC-registered fund predating Reawaken with Dylan Peters as a related person.**

### LinkedIn / Crunchbase

Reviewed via public-page fetch:
- **Education**: Diablo Valley College, 2003–2007 (East Bay community college)
- **Certifications**: CREIPS + National Commercial Real Estate Advisor (both NCREA short-course certifications, **not** real estate licenses)
- **Other certifications**: Project Management Diploma (Alison), Certified Sommelier (multiple wine bodies)
- **Personal**: 10th Planet Jiu Jitsu black belt; UFC coach; Society of Wine Educators
- **Prior employment listed publicly**:
  - Vice President, Recreate Commercial Real Estate — Jan 2021 to Jan 2022 (1 year)
  - Earlier roles in tech/startups (representations of 500 Startups, Take Two Interactive, Jaguar Health, Transmission Agency per his bio)
  - "Post Exit Founders Community (PEF)" — Member since Apr 2026 — implies a prior exit, but the exited business is not publicly identified

**No prior real-estate investment fund or property-holding LLC is publicly disclosed.**

### Possible explanations for the "6-year vehicle" claim

| Hypothesis | Verification status |
|---|---|
| Unregistered family / single-purpose LLC (4(a)(2) raise; sub-Form-D threshold) | Plausible but unverifiable. If real, GP must produce entity name + audited returns. |
| 506 raise under a different name (Peters as silent/passive partner) | Possible, but Peters does not appear as "related person" on any other EDGAR Form D. |
| Personal investing history reframed as a "vehicle" | Most likely; technical claim of "personal portfolio" annualized over 6 years. Not the same as a managed-fund track record. |
| Marketing fabrication | Cannot be ruled out without GP-provided documentation. |

### "Family heritage in architecture" — possible referent

Search of California-licensed architects whose portfolio includes Atlanta, Las Vegas, and California (the three cities Dylan Peters is associated with) surfaced **Douglas Peters, AIA** — a CA-licensed architect with documented project work in all three markets (e.g., Block 34 Mall Fremont Street in Las Vegas, Gwinnett Place Mall Renovation in Atlanta).

**This is a plausible match for the "family heritage" claim if Douglas Peters is a relative.** Has not been confirmed. If confirmed, it would substantiate the family-architecture narrative but not the fund track record.

### Recommended follow-up questions for the principal

1. **What is the legal entity name of the "separate investment vehicle managed by the same team over a 6-year period"?**
2. **Who else was on the "team"?** (Form D for Reawaken lists only Peters)
3. **What dollar IRR / DPI / TVPI did that vehicle deliver?**
4. **Is there an audit, tax return (K-1), or capital-account statement from that vehicle that LPs can review?**
5. **Is Douglas Peters AIA the "family heritage in architecture" reference?** If so, what is the operating relationship between him and Reawaken (e.g., design fee, equity, advisor, none)?
6. **What was the prior "exit" referenced in your PEF membership?** Was it a real estate vehicle or a non-RE startup?

Until items 1–4 are answered with **a named entity and audited numbers**, the "6-year track record" should be treated as **UNSUBSTANTIATED** for purposes of return underwriting. This is a **material** point: the website's own "Historical ROI" claim depends on this prior vehicle.

### Updated severity scoring

This investigation upgrades the prior-vehicle claim from UNVERIFIABLE → **SEVERE_UNDERDELIVERY** (the marketing explicitly cites it as a benchmark for fund expectations, but it cannot be documented). The composite for the report now sits at **1.62 — high-conviction SHORT-tier**.

---

## Appendix E — Document Inventory

| File | Type | Notes |
|---|---|---|
| FAQ - Reawaken Capital Deck.docx | Marketing | 5,316 chars; key claims source |
| _Reawaken Capital's Investment Thesis.docx | Marketing | 3,711 chars; macro narrative |
| Current Pipeline Snapshot (Shared).xlsx | Operational | 1,076 × 64; per-property pro forma |
| Blogs/ (13 .docx files) | Marketing | Generic real-estate fund content |
| Property Photos (Data Room)/ | Empty directory | ⚠️ no actual property photos provided |

The empty Property Photos directory is itself notable — visual evidence of the underlying assets is conspicuously absent for a fund pitching value-add residential.

---

*This report was generated under standard buyside-DD R/f/M discipline. All assertions are sourced from either the data room or independently verifiable public records (SEC EDGAR, web). Personal-data assertions about principals are based on public LinkedIn / website / Crunchbase pages and have not been verified directly with the individuals or through paid background-check services. Any final commitment decision should incorporate the recommended principal interview and counsel review.*
