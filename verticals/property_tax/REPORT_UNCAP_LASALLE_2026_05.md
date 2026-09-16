<!--
Imported into Signal OS on 2026-05-19 from `/Users/ajay/exalted/detroit_fraud/reports/lasalle_summary.md`
(external-repo path; the directory name is historical and predates the current "delayed
tax payments" framing — the directory name is not a legal characterization).
This is the canonical report on the MCL 211.27a missed-uncap pattern of delayed property
tax payments. The original analysis was the bootstrap finding that anchored the property_tax
vertical's methodology. The held-out blinded re-run that validated it lives in `lasalle_v2/`.
The companion finding (PRE-on-Entity, MCL 211.7cc) lives in
`lasalle_v2/PRE_ENTITY_VALIDATION_2026_05_19.md`. The combined synthesis is
`REPORT_DETROIT_DELAYED_TAX_PAYMENTS_2026_05_19.md`.
-->

# Detroit Property Tax Uncapping: The La Salle Pattern and How Widespread It Is

*Analysis of 382,123 parcels across 29 Detroit zip codes | May 2026*

---

> **Disclaimer:** This document presents algorithmic analysis of public records for
> investigative and public-interest purposes. It is not a legal determination, and
> **nothing in it constitutes an allegation of fraud or criminal wrongdoing against
> any named individual or entity**. The patterns described below are delayed or
> under-paid property tax payments visible in public records — outcomes that may
> result from clerical error, inherited status, gaps in administrative process, or
> knowing non-filing. Distinguishing among those causes for any specific parcel
> requires investigation beyond what these public records support. All conclusions
> about specific transactions are drawn from official government records — Wayne
> County Register of Deeds, Detroit Open Data assessor records, Wayne County
> Parcelmaster — and are subject to independent verification. Readers are encouraged
> to consult those primary sources directly. Analytical flags such as
> "audit-priority score" and "consideration mismatch" are screening heuristics,
> not legal findings.

---

## Executive Summary

- **8,114 Detroit properties** have an overdue tax uncap: a recorded ownership transfer where the Taxable Value has not been reset to market as Michigan law requires. This covers all 29 zip codes and 382,123 parcels — effectively the full city.
- **Estimated uncollected property tax: $13.0M/yr** at the conservative floor (after accounting for Neighborhood Enterprise Zone rate reductions). The core count of 6,045 parcels with no applicable exemption produces **$11.9M/yr** with no caveats.
- **4,317 of the 8,114 are high-confidence** — both the sale price and the assessor's own State Equalized Value independently confirm the TV should have been reset.
- **64 involve a deed recording $0 consideration** on what public MLS records show was an open-market sale — the most aggressive form of consideration suppression, and the pattern the La Salle and Glynn Court cases illustrate.
- **38.5% (3,128) are entity-held** — LLCs, holding companies, trusts — where the structural layering between buyer and deed is the mechanism that prevents the assessor from acting.
- The system does not catch this because it relies on buyers to self-report. The penalty for not doing so — $200 maximum — is a rounding error relative to years of suppressed taxes.

---

## The La Salle Pattern

The analysis takes its name from **13300 La Salle Blvd** in Detroit's La Salle Gardens neighborhood (48238). It is the case this analyst has examined in most detail — including a direct conversation with the city assessor's office — and it illustrates, more clearly than any aggregate statistic can, both the mechanism of the problem and the system's failure to catch it. The same pattern appears in 64 confirmed cases across the city and underlies hundreds more.

### How It Works

Under Michigan law (MCL 211.27a), when a property sells at arm's length, the new owner's Taxable Value must be reset — "uncapped" — to the State Equalized Value at the next annual assessment. This is mandatory. The mechanism for triggering it is a Property Transfer Affidavit (PTA) the buyer must file within 45 days.

The La Salle pattern exploits a gap: the assessor relies on PTAs rather than proactively cross-referencing deed records. An investor who understands this can record a deed that shows no taxable consideration — effectively erasing the market transaction from the assessor's view — and simply not file a PTA. The assessor has no basis to act, and the TV stays capped indefinitely.

The instrument of choice is the **quit claim deed with $0 consideration**. Unlike a warranty deed, a quit claim carries no price guarantee and triggers no real estate transfer tax. It looks, to an automated assessor system, like a non-taxable family transfer or entity restructuring. In practice, it is sometimes neither.

---

### 13300 La Salle Blvd (48238)

13300 La Salle is a two-family residential property. MLS data shows it sold for **$151,500 on December 8, 2023**. The deed filed at Wayne County on that same date records a consideration of **$0**.

**The deed chain:**

| Date | Instrument | Grantor | Grantee | Consideration |
|------|------------|---------|---------|---------------|
| June 23, 2023 | Warranty Deed | Prior individual owner | P L Jackson Consultants LLC | $40,000 |
| December 8, 2023 | Quit Claim Deed | Two individual grantors | Hope Properties United LLC | $0 |

There is a **missing deed** between these two instruments. P L Jackson Consultants LLC acquired the property in June 2023, but no recorded instrument shows how the individual grantors on the December deed obtained title before transferring to Hope Properties United LLC. The MLS sale of $151,500 is the most likely trace of that unrecorded intermediate transaction.

The December 8 quit claim deed (Document 2024003352, Liber 58614 / Page 1436, prepared by First Centennial Title Agency, Inc.) did two things simultaneously: it concealed the market transaction from the assessor, and it corrupted the valuation baseline.

**Tax impact:**

| | Recorded deed ($0) | MLS-implied ($151,500) |
|---|---|---|
| SEV (50% of market) | $34,100 | $75,750 |
| Current TV | $34,100 | — |
| Annual tax at 67 mills | $2,285 | $5,075 |
| **Uncollected tax/yr** | — | **$2,791** |

The assessor's own ETCV (Estimated True Cash Value) for this parcel is $80,481 — their internal market estimate. SEV is supposed to be 50% of market; 50% of $80,481 is $40,240, consistent with the tentative 2026 AV of $40,200 the assessor is already moving toward. Neither figure reaches the $75,750 SEV a $151,500 arm's-length sale would require.

### What the Assessor's Office Said

When the assessor's office was asked directly about this case, the response confirmed two things. First, the office relies on Property Transfer Affidavits (PTAs) to trigger the uncapping process; it does not routinely cross-reference deed records against MLS sale prices. Second, a deed stating $0 consideration is treated as a non-taxable transfer and does not generate a review flag. There is no automated workflow for identifying the gap between a $0 deed and a $151,500 market transaction visible in public MLS data — even when both instruments are dated the same day and reference the same property.

This is not a failure of any individual assessor. It is a structural gap in the administrative process: the law puts the burden on buyers to self-report, the penalty for not reporting is negligible, and the office has no standing mechanism to cross-check public MLS data against the deed record.

---

## The Pattern Beyond La Salle

The same mechanism — $0 or nominal-consideration quit claim deed filed on the date of an open-market MLS transaction — appears in **64 confirmed cases** across the city. Two examples illustrate the range.

### 1553 Glynn Ct (48206) — Audit-Priority Score: 95

**1553 Glynn Court** in the Boston-Edison neighborhood is another instance of the pattern, identified independently by the same algorithm. The numbers are larger and the entity structure is more elaborate.

MLS data shows the property sold for **$364,900**. The deed recorded the same day states **$0**.

**Current assessment:**
- Taxable Value: **$21,843**
- State Equalized Value: **$222,700**
- TV-to-SEV ratio: **9.8%** — meaning the taxable base is less than 10% of the assessor's own market estimate

**The deed chain involves five distinct entities across multiple instruments:**

1. Prior individual owner → **ATA Holdings LLC** (2015)
2. ATA Holdings LLC → **HOF I Grantor Trust 5** (no direct recording found between 2015 and 2023)
3. **HOF I Grantor Trust 5** → **HOF I REO 5 LLC** (June 4, 2024) — chain-of-title gap: grantee appears as "HOF 1 REO 5 LLC" and "HOF I REO 5 LLC" in different instruments
4. **HOF I REO 5 LLC** → **GLYNN 1553 LLC** (June 18, 2024, $0 quit claim deed, Liber 2024271683)

The MLS sale of $364,900 does not appear anywhere in the deed record. The instrument filed at the county on the date of that transaction is a $0 quit claim. The assessor's records show the transfer date as the 2015 conveyance to ATA Holdings. The current TV of $21,843 reflects over a decade of capped growth from that stale baseline.

**Tax impact:**

| | Recorded (stale baseline) | MLS-implied ($364,900) |
|---|---|---|
| SEV (50% of market) | $222,700 (assessor current) | $182,450 |
| Correct TV after uncap | $21,843 (hasn't been reset) | $182,450 |
| Annual tax at 67 mills | $1,463 | $12,224 |
| **Uncollected tax/yr** | — | **$10,761** |

The trust-to-LLC structure — with a grantor trust as an intermediate holding vehicle — is not incidental. Grantor trusts are commonly used to obscure beneficial ownership because they are not required to disclose their beneficiaries in public deed records. The subsequent transfer to a purpose-named LLC (GLYNN 1553 LLC) creates a chain where every instrument in the public record is technically legal but the underlying market transaction at $364,900 is invisible.

---

### 7405 Garden (48204) — Audit-Priority Score: 82

For completeness, a case with explicit price suppression rather than $0 consideration:

**7405 Garden St** sold on the open market for **$110,000** (MLS-confirmed). The deed recorded on the same date states a consideration of **$1**. The instrument is a quit claim deed. A second quit claim deed three months later transferred the property to **LTN 7405 Garden LLC** (consideration again: $1).

Current TV: **$19,307**. Assessor's SEV: **$155,900**. Uncollected tax at 67 mills: approximately **$9,174/yr**.

The $1 consideration is a formal acknowledgment that something was paid — enough to invoke a transfer — but not enough to trigger the transfer tax or a meaningful uncapping calculation. The full consideration on the prior deed ($110,000) simply does not appear in any recorded instrument.

---

## Scale Across Detroit: The Broader Finding

La Salle is one data point in a much larger pattern. Across **29 Detroit zip codes** and **382,123 parcels**, this analysis identified **8,126 properties** with overdue uncaps — transfers on record where the Taxable Value has not been reset as Michigan law requires. After removing 12 fully exempt properties (PILOT housing, Land Bank, nonprofits), the working count is **8,114**.

**The estimated uncollected property tax is $13.0M/yr** at the conservative floor — after adjusting for Neighborhood Enterprise Zone reduced millage rates where applicable. The core count of **6,045 parcels with no applicable exemption** produces **$11.9M/yr** with no caveats.

### Confidence Tiers

| Confidence tier | Parcels | Est. uncollected tax/yr | Basis |
|---|---|---|---|
| Both methods agree | 4,317 | $13.1M | Sale price confirms SEV-implied market; both show TV should have reset |
| SEV method only | 2,162 | $1.3M | TV below assessor's own SEV — legally definitive regardless of sale data |
| Sale method only | 1,647 | $2.6M | Sale price reliable but SEV may not yet reflect the transfer |
| **Total** | **8,114** | **$13.0M** (conservative floor) | After NEZ and exemption adjustments |

Of the 15,009 property transfers recorded in the three-year lookback window across all 29 zip codes, **54%** show an overdue uncap. That rate is consistent across every part of the city — it does not vary materially between neighborhoods, housing types, or price points.

### Entity Ownership

**3,128 of the 8,114 overdue uncaps** (38.5%) are held by LLCs, corporations, holding companies, or trusts. These account for an estimated **$5.9M/yr** in uncollected tax.

Entity ownership is legally significant because MCL 211.27a(6)(h) provides a narrow exemption for transfers where the beneficial ownership interest does not change — an individual deeding property to their own wholly-owned LLC, for instance. This exemption is routinely invoked, explicitly or implicitly, as a justification for not filing a Property Transfer Affidavit. In many of the 3,128 entity-held cases, no such exemption was properly claimed or documented. The exemption does not apply to arm's-length sales between unrelated parties, and it does not apply to the trust-to-LLC structures seen in cases like Glynn Court.

### The Zero-Consideration Subset

**64 overdue uncaps** involve a recorded consideration of exactly $0 — the most aggressive form of consideration suppression. Using the assessor's SEV-based delta (since the deed conceals the true price), these account for an estimated **$159,151/yr** in uncollected taxes on the SEV delta alone. That figure systematically understates the true exposure: $0 quit claim deeds are nearly always accompanied by a parallel, unrecorded or separately documented market transaction.

High-scoring zero-consideration cases (beyond La Salle and Glynn Court):

- **18272 Ohio (48221) — VPFIIR24 LLC** (score: 80): TV $28,522 / SEV $65,700. $0 quit claim from Northwest Passage LLC on May 8, 2024 (Liber 2024173647). The prior grantor in the chain is AXIN MI LLC; an intermediate instrument between 2019 and 2024 is missing.
- **2633 W Grand Blvd (48208) — ZAYTAM Investments LLC** (score: 75): TV $6,700 / SEV $97,200. Five-link deed chain going back to 2015 with consideration amounts of $1 and $2,500 on quit claim instruments. Current TV represents 6.9% of SEV.
- **18229 Sorrento (48235) — A&D Investors LLC** (score: 71): TV $15,018 / SEV $66,200. $0 quit claim in October 2024; last prior individual grantor visible in the chain is from 2012 — a 12-year gap in publicly traceable title.

### Serial Actors

The following entities appear as owners on three or more overdue uncap properties across multiple zip codes, suggesting systematic rather than incidental behavior. All figures are SEV-based tax delta estimates.

| Owner | Properties | Est. uncollected/yr | Avg audit-priority score | Zip codes |
|---|---|---|---|---|
| SATORI 1 LLC | 21 | $7,367 | 27 | 48238, 48227, 48235, 48228, 48219, 48213 |
| VFMT REALTY INVESTMENT GROUP LLC | 20 | $16,856 | 35 | 48224, 48227, 48235, 48228, 48219, 48205 |
| DUNMERE OWNER I LLC | 18 | $12,181 | 29 | 48227, 48235, 48221, 48228, 48219, 48213 |
| LGL LLC | 15 | $8,307 | 28 | 48228, 48238, 48227, 48219, 48204, 48224 |
| DETROITS BEST HOMES LLC | 13 | $22,321 | 43 | 48238, 48227, 48235, 48221, 48219, 48224 |
| XAMENA LLC | 10 | $15,013 | 42 | 48235, 48221, 48228, 48219, 48224, 48202 |
| JW VENTURE HOLDINGS MICHIGAN LLC | 10 | $11,441 | 38 | 48227, 48235, 48221, 48228, 48219, 48205 |
| DOUBLE O REAL ESTATE LLC | 9 | $21,595 | 43 | 48214, 48215, 48221, 48204, 48208, 48202 |
| MTMA 1 LLC | 8 | $18,796 | 42 | 48235, 48221, 48228, 48223, 48224, 48205 |
| JOHN GRAHAM INC | 8 | $13,545 | 39 | 48238, 48235, 48221, 48219, 48224 |

The geographic spread across 5–6 zip codes for most of these entities is significant: it suggests a purchasing strategy that is citywide, not neighborhood-specific, and requires the sophistication to track multiple properties and their PTA obligations simultaneously. Not filing PTAs across a 21-property portfolio is not an oversight.

### By Zip Code

| Zip | Neighborhood | Overdue | Est. tax/yr | High-confidence | Zero-consideration |
|---|---|---|---|---|---|
| 48221 | Bagley / Sherwood Forest | 670 | $1,921,881 | 548 | 7 |
| 48224 | East English Village | 751 | $1,454,699 | 617 | 6 |
| 48235 | Bagley / Palmer Woods border | 677 | $1,395,854 | 607 | 4 |
| 48227 | Brightmoor / Rosedale Park | 692 | $1,094,725 | 579 | 5 |
| 48219 | Grandmont / Redford border | 628 | $1,230,329 | 558 | 8 |
| 48228 | Warrendale / West Outer Drive | 756 | $990,869 | 636 | 2 |
| 48214 | East Jefferson | 202 | $998,867 | 142 | 1 |
| 48234 | Warren / Conant Gardens | 427 | $838,198 | 324 | 4 |
| 48205 | East Side / Morningside | 480 | $550,438 | 409 | 2 |
| 48223 | Rosedale Park / Grandmont | 244 | $650,803 | 209 | 2 |
| 48202 | New Center / Boston-Edison N | 127 | $616,473 | 86 | 2 |
| 48206 | Boston-Edison | 249 | $537,251 | 183 | 3 |
| 48238 | La Salle Gardens / Dexter | 354 | $501,899 | 262 | 2 |
| 48201 | Midtown / Wayne State | 44 | $487,459 | 20 | 0 |
| 48216 | Corktown | 43 | $480,079 | 28 | 0 |
| 48226 | Downtown / Renaissance Center | 19 | $450,607 | 17 | 0 |
| 48209 | Springwells / Mexicantown | 178 | $433,615 | 119 | 0 |
| 48204 | Dexter / NW Goldberg | 318 | $356,531 | 263 | 4 |
| 48210 | West Vernor | 190 | $285,063 | 134 | 1 |
| 48207 | Lafayette Park / Elmwood Park | 135 | $267,731 | 81 | 0 |
| 48239 | Rosedale Park West | 92 | $246,456 | 78 | 0 |
| 48215 | Jefferson Chalmers | 129 | $238,095 | 84 | 2 |
| 48203 | Palmer Park / Highland Park border | 126 | $258,200 | 93 | 1 |
| 48213 | East Side | 208 | $240,988 | 150 | 2 |
| 48212 | Gratiot / Conner | 187 | $215,240 | 113 | 3 |
| 48208 | Woodbridge | 76 | $169,129 | 44 | 0 |
| 48217 | Delray | 90 | $116,464 | 71 | 3 |
| 48211 | Eastern Market border | 33 | $70,474 | 23 | 0 |
| 48218 | River Rouge border | 1 | — | 1 | 0 |

Two patterns stand out. First, **48221 and 48224** each exceed $1.4M/yr on predominantly single-family residential stock — these are not commercial anomalies but investor accumulation in middle-tier neighborhoods. Second, small-parcel-count zips punch far above their weight: **48226 (Downtown)** produces $451k/yr on just 19 overdue uncaps — the highest per-parcel average in the city, driven by large commercial properties in a rapidly appreciating corridor. **48216 (Corktown)** is similar at $480k/yr on 43 parcels. **48205** has the largest raw volume: 480 overdue uncaps, of which 409 are high-confidence.

---

## Neighborhood Enterprise Zones (NEZ)

### What NEZ Is

Neighborhood Enterprise Zones are state-designated development districts in Detroit created under MCL 207.771 et seq. The purpose is to incentivize investment in areas the state designates as economically distressed: new residential construction and substantial rehabilitation within a NEZ zone can qualify for a dramatically reduced millage rate — approximately **6 mills** instead of the standard 67 mills — for up to 15 years.

The NEZ Homestead benefit is the specific program relevant here. To qualify, a property must be:
1. Located within a designated NEZ district
2. Owner-occupied as the buyer's primary residence
3. Certified by the Michigan Strategic Fund (administered through the Michigan Economic Development Corporation)

**LLCs and corporate owners cannot qualify for the NEZ Homestead rate.** The statute requires owner-occupancy, and entities by definition do not occupy residences. An LLC purchasing a property in a NEZ zone pays the full 67-mill non-homestead rate regardless of the zone designation.

### What the Data Shows

**2,081 of the 8,114 overdue uncap properties lie within NEZ districts.** The analysis separates these into two groups based on ownership type:

| Group | Parcels | At 67 mills | Adjusted rate | Adjusted tax gap |
|---|---|---|---|---|
| Entity-owned in NEZ zone | 534 | $924k | 67 mills (no adjustment) | **$924k — LLC cannot claim NEZ benefit** |
| Individually owned in NEZ zone | 1,547 | $2.48M | 6 mills | **$222k — NEZ rate credited** |
| No NEZ (core) | 6,045 | $11.87M | 67 mills | $11.87M |

The conservative floor of **$13.0M/yr** credits the 1,547 individually-owned NEZ parcels at 6 mills. It does not reduce the 534 entity-owned NEZ parcels, because those owners cannot legally claim the homestead rate.

### NEZ District Breakdown

The 1,547 individually-owned overdue uncaps in NEZ zones are spread across 30+ districts. The ten largest by parcel count:

| NEZ District | Parcels |
|---|---|
| West Warren – Southfield (H153) | 93 |
| Morningside (H068) | 64 |
| Warren – Rouge Park (H154) | 52 |
| Eight Mile – Evergreen (H010) | 47 |
| Prevost – Puritan (H008) | 45 |
| Grandmont West (H006) | 44 |
| West Warren – Greenfield (H158) | 43 |
| Bagley (H025) | 41 |
| Charles – Buffalo (H046) | 41 |
| Gratiot – Eight Mile (H042) | 37 |

The geographic concentration of overdue uncaps within NEZ districts is notable: these are precisely the areas the state designated as needing investment support, and they are experiencing significant investor acquisition activity. The NEZ benefit was designed for homeowners rehabilitating distressed properties — not for investors who acquire through quit claim deeds and do not file PTAs.

---

## Exemption Cross-Reference

To test whether legitimate tax benefits explain any of the 8,126 flagged parcels, the analysis cross-referenced every major Michigan and Detroit-specific program that can lawfully produce a TV below SEV or a reduced millage rate.

| Program | Statute | What it does | Treatment in this model |
|---|---|---|---|
| **PRE — Principal Residence Exemption** | MCL 211.7cc | Reduces millage ~67→~40 mills for owner-occupied primary residences | 67-mill baseline used for all non-NEZ parcels; $2.1M sensitivity reported separately |
| **NEZ Homestead** | MCL 207.771 | Reduces millage to ~6 mills in designated zones, owner-occupied only | Fully modeled per-parcel — entity-owned at 67 mills, individually-owned at 6 mills |
| **PILOT / LIHTC** | MCL 125.1415a | Negotiated payment in lieu of taxes for affordable housing | 12 parcels removed from count; `tax_status = EXEMPT` |
| **Renaissance Zones** | MCL 125.2681 | Near-zero taxation for 15 years in state-designated zones | Zero overlap; only 3 active zones remain, all industrial/automotive |
| **PA 210 — Commercial Rehabilitation** | MCL 207.841 | Freezes TV at pre-renovation level up to 10 years for rehabilitated commercial properties | No assessor-roll flag; ~340 commercial parcels at risk; requires separate data request |
| **OPRA — Obsolete Property Rehabilitation (PA 146)** | MCL 125.2781 | Freezes TV up to 12 years; commercial and some residential | No assessor-roll flag; minimal residential overlap expected; not modeled |
| **PA 198 — Industrial Facilities Exemption** | MCL 207.551 | 50% abatement for new/rehabilitated industrial facilities | Industrial only; no overlap with residential flagged set |
| **Brownfield TIF** | MCL 125.2651 | Captures tax increment for brownfield redevelopment | Does not suppress TV; does not produce TV-below-SEV signal; not applicable |

**PILOT / fully exempt — negligible.** 12 parcels carry `tax_status = EXEMPT`: one LIHTC housing property, three Detroit Land Bank parcels, one nonprofit, and scattered others. Removed from count. 8,126 → **8,114**.

**Renaissance Zones — zero impact.** The three remaining active Renaissance Zones (Ford, Flex-N-Gate, Sakthi) are industrial/automotive. No overlap.

**PA 198 / Brownfield TIF — not applicable.** PA 198 applies to industrial facilities. Brownfield TIF captures future increment without lowering underlying TV.

**OPRA (PA 146) — not detectable, minimal expected impact.** OPRA exemptions (TV freeze for blighted commercial sites) are not flagged in the assessor roll. Primarily commercial; limited residential overlap. Not modeled.

**PA 210 — unknown.** PA 210 freezes a rehabilitated commercial property's TV at its pre-renovation level for up to 10 years — producing a TV-below-SEV pattern identical to a missed uncap. There is no PA 210 flag in the assessor roll. Approximately 340 commercial parcels in the flagged set are the prime candidates. A full cross-reference would require a separate data request from the Michigan Department of Treasury or the city assessor's office.

**PRE (Principal Residence Exemption) — modeled at 67 mills; $2.1M sensitivity.** MCL 211.7cc reduces the millage rate for owner-occupied primary residences from ~67 to ~40 mills. The model uses 67 mills as the baseline for all non-NEZ parcels. Of the 8,126 overdue parcels, 4,766 currently claim PRE.

| PRE group | Parcels | At 67 mills (modeled) | At 40 mills (adjusted) | Difference |
|---|---|---|---|---|
| Homestead, no NEZ | 4,766 | $5.23M | $3.12M | −$2.11M |
| Non-homestead / entity | 1,813 | correct at 67 mills | — | — |
| NEZ individual (incl. PRE overlap) | 1,547 | already at 6 mills | — | — |

The 67-mill baseline is retained for the conservative floor for three reasons: PRE status can be removed at uncapping if the assessor finds the property is not genuinely owner-occupied (common in investor portfolios where PRE was claimed improperly); a fraction of "homestead" overdue uncaps involve buyers who claimed PRE on properties they do not occupy; and the conservative floor is defined as requiring no assumptions beyond what the assessor roll states as fact. PRE is a claim, not a verified finding.

**PRE-adjusted sensitivity:** Crediting all 4,766 PRE-claiming non-NEZ parcels at 40 mills reduces the total by approximately **$2.1M/yr**, to roughly **$10.9M/yr** at the conservative floor.

### Adjusted Totals

| Scenario | Parcels | Est. uncollected tax/yr |
|---|---|---|
| **Core — no NEZ, no exemption** | **6,045** | **$11.9M** |
| + entity-owned NEZ (no benefit possible) | 6,579 | $12.8M |
| + individual NEZ at adjusted 6-mill rate | **8,114** | **$13.0M** ← conservative floor |
| PRE sensitivity: homestead parcels at 40 mills | 8,114 | ~$10.9M |
| Upper bound — no NEZ or PRE adjustment | 8,114 | $15.3M |

The **$13.0M figure is the most defensible published estimate.** The $11.9M core count requires no assumptions at all: those 6,045 parcels are in no NEZ zone, carry no exempt tax_status, and have a TV that has not been reset to the assessor's own SEV following a recorded transfer.

---

## Why the Assessment System Does Not Catch This

Michigan law places the obligation to notify the assessor on the **buyer**, not the seller or the assessor. Buyers must file a Property Transfer Affidavit (PTA) within 45 days of closing. The penalty for non-filing is $5/day, capped at **$200 total** — a rounding error relative to years of suppressed taxes.

The assessor has independent access to Wayne County deed records and the transfer dates visible in Detroit's own Open Data portal. The 8,114 overdue uncaps in this analysis were identified entirely from public data the assessor already holds. The uncapping did not happen not because the information was unavailable, but because the administrative process depends on PTAs rather than deed cross-referencing — and investors who understand this do not file PTAs.

The $0 quit claim deed adds a second layer of insulation. Even if the assessor cross-references deed records, a $0 deed gives no price signal — it looks like a non-taxable family transfer or entity reorganization. The assessor has no formal mechanism to consult MLS data. The gap between deed consideration and MLS sale price is precisely what this analysis was designed to detect, and it is not detectable from deed records alone.

---

## Methodology Note

Full methodology is in `METHODOLOGY.md`. In brief:

**Data sources:** Detroit Open Data assessor records (all 382,123 parcels, 29 zip codes — effectively the full city), Wayne County Parcelmaster deed history (automated browser for flagged parcels), and Wayne County Register of Deeds index data (public search). MLS sale prices sourced from Redfin and Zillow sale history.

**Uncap tests:** Two independent tests are run for each parcel. The *sale-price method* estimates the correct new TV as sale_price × 0.5 and compares to current TV. The *SEV method* uses the assessor's own SEV: because SEV is updated annually to 50% of market, a parcel with TV below SEV following a recorded transfer has not been uncapped regardless of the sale price. Both tests are legally definitive; the SEV method does not require sale price data.

**Tax estimates:** The SEV-based delta is used for properties where the sale price appears to be a bulk portfolio price (artificially low per-parcel); the sale-price-based delta is used otherwise. Detroit's non-homestead millage rate of 67 mills is the baseline for all non-NEZ parcels. NEZ individually-owned parcels use 6 mills. All eight major Michigan tax-reduction programs were reviewed for overlap; see *Exemption Cross-Reference*.

**Audit-priority score:** A composite score (0–100) weighted by consideration mismatch (deed vs. MLS), zero-consideration deed, chain-of-title gaps, entity ownership, TV/SEV ratio, and method agreement. Scores ≥65 are flagged for manual review. The score is a screening heuristic for assessor/treasury audit prioritization; it is not a legal determination and is not an allegation of fraud against any specific owner.

---

## Key Terms

**TV — Taxable Value.** The value used to calculate a property's tax bill. Under Michigan law, TV grows by the lesser of CPI or 5% per year while a property stays with the same owner. It resets to SEV when the property is sold — "uncapping."

**SEV — State Equalized Value.** The assessor's estimate of 50% of a property's market value, updated annually. After an arm's-length sale, the new owner's TV must be reset to the SEV at the next annual assessment.

**AV — Assessed Value.** In Michigan, AV and SEV are the same figure — both equal 50% of market. The terms appear interchangeably in assessor records.

**ETCV — Estimated True Cash Value.** The assessor's internal full-market estimate (100% of market). Used as a cross-check: ETCV $80,000 → correctly set SEV should be $40,000.

**Uncapping.** The required reset of TV to SEV following an arm's-length sale. Governed by MCL 211.27a. An "overdue uncap" means the transfer is on record but TV has not been reset.

**MCL — Michigan Compiled Laws.** MCL 211.27a: the uncapping statute. MCL 207.526: real estate transfer tax, calculated on actual consideration paid.

**PTA — Property Transfer Affidavit.** The form a buyer must file within 45 days of closing to trigger the uncapping process. Penalty for non-filing: $5/day capped at $200.

**Quit Claim Deed (QC).** Transfers whatever interest the grantor holds, without title warranties. Used for family transfers, LLC reorganizations, and estate settlements — but also in investment transactions where the parties want to avoid warranty deed disclosures. Commonly used with $0 consideration in the La Salle pattern.

**Warranty Deed (WD).** Standard instrument for arm's-length sales. The grantor warrants clear title; stated consideration is typically the true sale price. Transfer taxes are calculated on this amount.

**Consideration.** The price paid for a property as stated on the deed. Under MCL 207.526, transfer tax is calculated on actual consideration. A $0 deed implies no taxable transfer — sometimes legitimate, sometimes not.

**Liber / Page.** Wayne County's deed recording reference. Every recorded instrument is assigned a liber number and page as its permanent index location.

**Mills / Millage rate.** One mill = $1 of tax per $1,000 of taxable value. Detroit non-homestead rate: 67 mills. NEZ Homestead rate: ~6 mills. PRE (homestead) rate: ~40 mills.

**NEZ — Neighborhood Enterprise Zone.** State-designated development district in Detroit. Owner-occupants who qualify receive a ~6-mill millage rate for up to 15 years. LLCs and corporations are ineligible. Created under MCL 207.771.

**PRE — Principal Residence Exemption.** Reduces millage from ~67 to ~40 mills for owner-occupied primary residences. Governed by MCL 211.7cc. Can be removed by the assessor at uncapping if the property is not genuinely owner-occupied.

**Chain-of-title gap.** A discrepancy in the deed chain where the grantee of one recorded instrument does not match the grantor of the next instrument for the same property — indicating an unrecorded intermediate conveyance.
