# PRE-on-Entity Validation Report — Detroit Citywide

**Date:** 2026-05-19
**Jurisdiction:** Detroit, MI (Wayne County)
**Data source:** Detroit Open Data `tentative_assessment_roll_2025` (ArcGIS FeatureServer, 388,535 parcels)
**Statutory basis:** MCL 211.7cc — Principal Residence Exemption (PRE) requires natural-person owner-occupancy
**Follow-up to:** `lasalle_v2/comparison.md` — held-out blinded re-run that surfaced PRE-on-LLC as a distinct category of delayed property tax payments

> **Note:** This document describes a pattern of property tax payments that are below what statute appears to require. It is not a legal finding of fraud or criminal wrongdoing. The cause for any specific parcel may be clerical error, inherited PRE status from a prior owner, gaps in administrative process, or knowing non-correction — distinguishing among those requires investigation beyond this dataset.

## Executive summary

Detroit's tentative 2025 assessment roll contains **23,211 parcels** owned by limited-liability entities (LLC, Inc, Corp, Ltd, LP) that claim 100% Principal Residence Exemption — a claim that under the Michigan State Tax Commission's interpretation of MCL 211.7cc cannot apply to entity owners (PRE requires natural-person owner-occupancy). These parcels collectively account for **$10.72M/year** in delayed property tax payments via the 67-vs-40 mill rate differential.

This pattern is independent of, and additive to, the previously-reported "missed uncap" finding (8,126 parcels, $11.9–26.2M/yr): PRE-on-entity is a millage-rate issue that requires no transfer event to detect, while missed-uncap is a taxable-value issue conditional on a recent transfer.

Both findings are now wired into the production engine (commit `214314f`); citywide scans will surface both patterns in one pass.

## Statutory basis

**MCL 211.7cc — Principal Residence Exemption.** A parcel is exempt from the 18-mill local-school operating tax (effectively reducing the rate from ~67 to ~40 mills) when the property is "owned and occupied as a principal residence" by the person claiming the exemption.

Limited-liability entities (LLC, Inc, Corp, Ltd, LP) cannot occupy a principal residence in the statutory sense. The State Tax Commission, the Michigan Tax Tribunal, and the Michigan Department of Treasury have consistently held that PRE is reserved for natural persons. Entity-owned PRE claims are either (a) clerical errors in the original PRE affidavit (Form 2368) that the assessor has not caught, (b) inherited PRE status from a pre-LLC owner that was never withdrawn after a transfer, or (c) deliberate exploitation of the assessor's limited capacity to audit.

The economic incentive is direct. On a $20,000-TV parcel:
- Correct non-homestead tax = $20,000 × 67 / 1000 = **$1,340/yr**
- PRE-claiming tax = $20,000 × 40 / 1000 = **$800/yr**
- Suppressed: **$540/yr** per parcel

The penalty for an improperly-claimed PRE that gets caught (under MCL 211.7cc(3)) is repayment plus interest, but the population of entity-owned PREs visible on the assessor roll has clearly not been audited at scale.

## Methodology

Queried the Detroit Open Data `tentative_assessment_roll_2025` layer directly via ArcGIS FeatureServer, applying:

1. **Entity filter** (strict): owner name contains any of `LLC`, `L.L.C.`, `INC`, `CORP`, `LTD`, `L.P.`
2. **PRE filter:** `pct_pre_claimed >= 100`
3. **Carve-out exclusion:** owner name does NOT contain `CO-OP`, `COOPERATIVE`, `LDHA`, `LIMITED DIVIDEND`, `SENIOR HOUSING`, `LIHTC` (these have legitimate PRE pathways via individual member occupancy under housing-cooperative or LIHTC statutes)

The carve-out exclusion removed only 23 of 23,234 candidates (~0.1%) — negligible contamination of the candidate set.

A separate negative-control test pulled natural-person 100%-PRE parcels and confirmed they are not flagged by the rule (no false positives on legitimate PREs).

## Findings

### Headline

| Metric | Value |
|---|---:|
| Total Detroit parcels (2025 roll) | 388,535 |
| Parcels with any PRE claimed | 223,262 |
| Parcels with 100% PRE | 215,575 |
| **Strict-entity parcels @ 100% PRE (post-carve-out)** | **23,211** |
| Average taxable value (TV) | $17,116 |
| Average SEV | $31,349 |
| Sum TV | $396.9M |
| Annual suppressed taxes at current TV (27 mill × TV / 1000) | **$10.72M** |
| Maximum exposure if TV also uncapped to SEV | $19.65M |

### TV distribution

| TV bracket | Parcels | Sum TV | Annual gap |
|---|---:|---:|---:|
| $0 (vacant or fully exempt) | 548 | $0 | $0 |
| $1 – $5,000 | 2,621 | $3.4M | $0.09M |
| $5,000 – $10,000 | 3,776 | $30.1M | $0.81M |
| $10,000 – $20,000 | 9,922 | $143.5M | $3.87M |
| $20,000 – $50,000 | 5,753 | $162.7M | $4.39M |
| $50,000 – $100,000 | 414 | $27.1M | $0.73M |
| $100,000 – $500,000 | 155 | $27.9M | $0.75M |
| $500,000+ | 3 | $2.2M | $0.06M |

The bulk of the dollar exposure sits in the $10K–$50K TV band — roughly 16,000 parcels, ~67% of total. This is the median Detroit residential parcel band, suggesting the pattern is broad-based across the residential investor population rather than concentrated at the high end.

### Property class

| Class | Parcels | % |
|---|---:|---:|
| RESIDENTIAL-IMPROVED | 20,754 | 89.4% |
| RESIDENTIAL-VACANT | 1,960 | 8.4% |
| RESIDENTIAL CONDOMINIUMS | 295 | 1.3% |
| COMMERCIAL-IMPROVED | 92 | 0.4% |
| COMMERCIAL-VACANT | 69 | 0.3% |
| INDUSTRIAL (combined) | 40 | 0.2% |
| Other | 1 | 0.0% |

98.7% residential — consistent with PRE being a residential exemption. The ~200 commercial/industrial parcels claiming PRE are particularly indefensible (PRE cannot be claimed on commercial property at all, even by a natural person) and should be the first audit priority.

### Geographic concentration (top 15 zips)

| Zip | Parcels | Sum TV | Annual gap |
|---|---:|---:|---:|
| 48228 | 2,541 | $37.5M | $1.01M |
| 48224 | 2,414 | $44.9M | $1.21M |
| 48235 | 2,069 | $42.1M | $1.14M |
| 48219 | 2,055 | $38.5M | $1.04M |
| 48205 | 1,901 | $29.0M | $0.78M |
| 48227 | 1,866 | $34.4M | $0.93M |
| 48221 | 1,541 | $39.2M | $1.06M |
| 48234 | 1,360 | $16.4M | $0.44M |
| 48238 | 829 | $11.3M | $0.31M |
| 48204 | 767 | $10.8M | $0.29M |
| 48223 | 730 | $14.5M | $0.39M |
| 48214 | 683 | $9.6M | $0.26M |
| 48213 | 584 | $6.3M | $0.17M |
| 48206 | 536 | $10.8M | $0.29M |
| 48203 | 445 | $5.8M | $0.16M |

Three zips (48228, 48224, 48235) each carry over 2,000 LLC-on-PRE parcels and over $1M/yr in suppressed tax. These are dense east-side and west-side residential investor zips.

### Top owners by parcel count (top 20)

| Parcels | Sum TV | Owner |
|---:|---:|---|
| 138 | $0.07M | HANTZ WOODLANDS LLC |
| 71 | $1.29M | DETROIT RENAISSANCE FUND LLC |
| 64 | $0.04M | HANTZ FARMS LLC |
| 60 | $0.47M | INDUMICH REALTY LLC |
| 51 | $1.09M | DUNMERE OWNER I LLC |
| 48 | $0.63M | DETROIT RENTAL FUND 6 LLC |
| 48 | $0.65M | RT HOMES DETROIT LLC |
| 46 | $0.80M | FDR INVESTMENTS LLC |
| 41 | $0.83M | FFGGP INC |
| 41 | $0.01M | SHA REALTY CORPORATION |
| 40 | $0.67M | DETROIT RENAISSANCE FUND, LLC |
| 39 | $0.33M | MSA REALTY FUND LLC |
| 37 | $0.66M | COASTAL LINE HOMES LLC |
| 36 | $0.41M | Q CAPITAL LLC |
| 34 | $0.26M | HERITAGE WALK REALTY DETROIT LLC |
| 32 | $0.52M | INVEST DETROIT FUND LLC |
| 31 | $0.57M | OFF MARKET BROKER LLC |
| 30 | $0.05M | RECOVERYPARK FARMS INC |

Hantz Woodlands LLC (138 parcels) and Hantz Farms LLC (64 parcels) are part of John Hantz's well-known land-bank assemblage; total exposure is modest ($0.07M + $0.04M TV) because most of these are vacant residential lots, but the count is large.

Detroit Renaissance Fund LLC and its variants (71 + 40 = 111 parcels) and the cluster of "OWNER I LLC" entities (DUNMERE OWNER I, WABAN OWNER I, OVERTON OWNER I, etc.) appear to be institutional Detroit single-family-rental aggregators. These warrant scrutiny because their portfolios are improved residential (not vacant) and therefore generate real suppressed tax.

### Top single-parcel exposures

| TV | Annual gap | Owner | Address | Class |
|---:|---:|---|---|---|
| $961,400 | $25,958 | D INVEST LLC | 12130 SCHAEFER (48227) | COMMERCIAL-IMPROVED |
| $749,595 | $20,239 | WORLDWIDE PREMIER INVESTMENTS INC. | 999 WHITMORE RD (48203) | COMMERCIAL-IMPROVED |
| $523,200 | $14,126 | BANYAN INVESTMENTS LLC | 1111 SEMINOLE (48214) | RESIDENTIAL-IMPROVED |
| $480,414 | $12,971 | COUNTRY HOUSE DETROIT LLC | 24224 W SEVEN MILE (48219) | COMMERCIAL-IMPROVED |
| $449,993 | $12,150 | 26149190 ONTARIO INC | 1535 SIXTH 5 | RESIDENTIAL CONDO |
| $445,100 | $12,018 | 4766 COMMONWEALTH LLC | 4766 COMMONWEALTH (48208) | RESIDENTIAL-IMPROVED |
| $397,561 | $10,734 | ABI INVEST MI, LLC | 360 LODGE (48214) | RESIDENTIAL-IMPROVED |
| $385,800 | $10,417 | SOLID GROUND EJ LLC | 1818 IROQUOIS (48214) | RESIDENTIAL-IMPROVED |
| $374,700 | $10,117 | LANDY LAND LLC | 60 CHARLOTTE (48201) | RESIDENTIAL-IMPROVED |
| $363,840 | $9,824 | GREEN LEAF 2 LLC | 66 SAND BAR LANE 38 (48214) | RESIDENTIAL-IMPROVED |

Two of the top three single-parcel exposures are **commercial-improved properties** — PRE on a commercial parcel is doubly indefensible, since PRE cannot be claimed on any commercial property regardless of owner type. These are the cleanest audit cases.

The "26149190 ONTARIO INC" owner is a foreign (Ontario, Canada) numbered corporation — additionally suspect given that the entity is presumably not even resident in Michigan, let alone occupying the parcel as a principal residence.

## Reconciliation with the lasalle_v2 initial estimate

The lasalle_v2 brief estimated ~20,180 parcels and ~$16M/yr. The validated numbers:

| Metric | lasalle_v2 estimate | Actual | Notes |
|---|---:|---:|---|
| Parcel count | ~20,180 | 23,211 | +15% — close enough; the "LLC only" filter in lasalle_v2 missed some Inc/Corp/Ltd variants |
| Annual exposure | ~$16M | $10.72M | -33% — explained below |

The $16M vs $10.72M gap comes from the taxable base. lasalle_v2 used a $30K average — that's the SEV (State Equalized Value, 50% of market) average. The correct taxable base is the **capped Taxable Value (TV)**, which averages $17,116 — about 55% of SEV under Michigan's Headlee/Proposal A caps that have suppressed TV growth below SEV growth since 1995. Using TV gives the actually-suppressed tax: $10.72M.

If we instead assume the parcel SHOULD also have been uncapped to SEV under MCL 211.27a (a separate, independent pattern of delayed payments), the maximum-exposure figure rises to $19.65M. The two patterns are distinct and additive; both are detected by the production engine.

## Implementation status

Wired into the production engine (commit `214314f`, 2026-05-18):

- **`PRE_ENTITY_VIOLATION` rule** registered in `verticals/property_tax/jurisdictions/michigan/rules/`
- **`PropertyTaxGapFunction.compute()`** now synthesizes a `GapResult` even when no TV-uncap gap exists, so PRE-on-entity-only parcels reach the rule chain
- **`PropertyTaxScorer`** treats PRE_ENTITY_VIOLATION as a hard statutory contradiction — score forced to ≥75 (high tier) when the rule fires
- **Combined math**: when both PRE-on-entity AND uncap-gap fire on the same parcel, the uncap calculation uses the 67-mill non-homestead rate (i.e., does not apply a PRE reduction the LLC owner cannot legitimately claim) and the millage-differential gap on current TV is summed in

Citywide scans run via the existing CLI (`signalos run --zip <zip> --tier high`) will now report PRE-on-entity parcels alongside missed-uncap parcels in a single pass. The rule identifier `PRE_ENTITY_VIOLATION` is an internal code name for non-compliance with MCL 211.7cc's natural-person-occupancy requirement; it is not a legal finding of fraud.

## Audit prioritization

Suggested rank order for assessor / treasury attention:

1. **Commercial/industrial parcels claiming PRE** (~200 parcels). PRE on non-residential property is impermissible regardless of owner type. Largest single-parcel exposures fall here.
2. **Foreign-entity owners** (`ONTARIO INC`, `BVI`, etc.). Non-Michigan-resident entities cannot plausibly claim Michigan principal-residence status.
3. **Top owners by parcel count** (>30 parcels each). Institutional rental aggregators with claimed PREs are highest-leverage to correct via portfolio-level audit rather than parcel-by-parcel.
4. **Top single-parcel exposures** (TV > $300K). Individually significant; quick wins.
5. **The long tail** (TV $10K–$50K, ~16K parcels). Where most of the dollars sit but per-parcel exposure is small; best handled by a batch PRE-rescission process rather than case-by-case audit.

## Caveats

- The 23 co-op/LDHA exclusions are a conservative carve-out. Some of the excluded entities may not actually be eligible for PRE either (e.g., LDHAs without member-occupancy structure). A second pass could re-include them after individual review.
- The `owner_is_entity` classification is keyword-based on `taxpayer_1`. A name like `JOHNSON, MICHAEL INCORPORATED CONSULTANT` would false-positive on "INC" — but inspection of the top-100 names found no such cases; the production rule uses the same classifier and is consistent with the validation count.
- The 2025 tentative roll is a snapshot. The actual 2024-paid tax may differ if the property's PRE status changed mid-year. The dollar exposure should be read as "annual rate of suppression at current roll status," not "actual past-year underpayment."
- Some parcels with `TV = 0` (548 of them) appear in the dataset — these are likely fully tax-exempt parcels mistagged with a PRE claim, or vacant lots with no taxable improvement. They contribute zero to the dollar gap and should be silently filtered in any audit report.

## Related artifacts

- Production rule: `verticals/property_tax/jurisdictions/michigan/rules/pre_entity_violation.py`
- Validation script (ad hoc): inline in this report's repo history (commit `214314f`)
- Original discovery: `verticals/property_tax/lasalle_v2/BRIEF.md`
- Comparison vs original analyst: `verticals/property_tax/lasalle_v2/comparison.md`
- Uncap-detection finding (separate delayed-payment pattern): `verticals/property_tax/README.md`
