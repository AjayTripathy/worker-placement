# Detroit Property-Tax Uncap — Blinded V2 Analysis

**Date:** 2026-05-15
**Database:** `/Users/ajay/exalted/detroit_fraud/uncap_tracker.db` (snapshot 2026-05-09/10)
**Methodology:** Signal OS post-improvement (Layer 3 discipline rules applied)

---

## Case parcel: 1553 GLYNN CT, Detroit 48206

**Parcel ID:** `06002672`. Property class: `COMMERCIAL-IMPROVED / APT-WALK UP` — a small walk-up apartment building in the New Center / Boston-Edison adjacent strip. Picked from the small set (n=33) of Detroit overdue parcels carrying both `CONSIDERATION_MISMATCH` and a $0 quit claim flag, and not the canonical 13300 LASALLE BLVD. It scores 95/100 in the existing pipeline with `method_agreement = both`.

### R / f / M decomposition

**R (assessor's claim):**

| Field | Value |
|---|---|
| Owner of record | `GLYNN 1553 LLC` |
| Taxable Value (TV) | $21,843 |
| State Equalized Value (SEV) = Assessed Value | $222,700 |
| Estimated True Cash Value (ETCV) | $472,774 |
| Recorded transfer date | 2024-06-04 |
| Recorded sale price | $364,900 |
| PRE % | 0% |
| Tax status | TAXABLE |

So the assessor knows market is ~$472K, knows there was a $364,900 transfer 11 months ago, has the SEV at $222,700 — and yet TV is still $21,843, ~9.8% of SEV. The TV did not reset.

**f (the legal relationship):** MCL 211.27a(3) — on a transfer of ownership, "the property's taxable value for the calendar year following the year of the transfer of ownership is the property's state equalized valuation for the calendar year following the transfer." Translation: on the 2025 assessment cycle following a 2024-06-04 transfer, TV must equal SEV. Expected `f(M) = SEV ≈ $222,700`.

**M (independent record):**

Wayne County Parcelmaster deed history (verified against `deed_transfers` table):

| Date | Instrument | Terms | Price | Grantor → Grantee | Liber/Page |
|---|---|---|---|---|---|
| 2024-06-18 | QC | 21-NOT USED/OTHER | $0 | HOF I GRANTOR TRUST 5, FAY SE et al → HOF I REO 5 LLC | 2024271683 |
| 2024-06-04 | PTA | 03-ARM'S LENGTH | $364,900 | HOF 1 REO 5 LLC → LYNN 1553 LLC | (none) |
| 2023-03-23 | SD | 10-FORECLOSURE | $591,229 | ATA HOLDINGS LLC → HOF I GRANTOR TRUST 5 | 2023150419 |
| 2015-05-01 | MLC | 03-ARM'S LENGTH | $140,000 | JACKSON, WILLIAM A → ATA HOLDINGS LLC | 2015242603 |

Earliest plausible date for an arm's-length transfer triggering uncap = 2024-06-04. SEV-implied target TV = $222,700.

**Signal:** `Signal = R - f(M) = $21,843 - $222,700 = -$200,857` of TV that should be on the roll but isn't.

At Detroit's non-homestead millage (~67 mills): **$13,457/yr in suppressed property tax**. Method A (sale-price implied: $364,900 × 0.5 = $182,450) yields a smaller estimate, $10,761/yr — the SEV-method is the binding floor here because the assessor's own SEV is below half the sale price. Both methods agree: TV is unambiguously below where MCL 211.27a requires it.

### Evidence trail and what's odd

1. **The $0 QC twelve days after the arm's-length sale** is the canonical entity-cleanup move: the seller (a foreclosure-bought REO trust) reorganized into a single-asset LLC after closing. This QC is structurally irrelevant to the uncap — the uncap-triggering event is the arm's-length 2024-06-04 PTA. The flag is a noise channel here.

2. **The "missing PTA" inference is ambiguous.** Ironically, the 2024-06-04 deed instrument is literally tagged "PTA" in Wayne County's data — but in this dataset PTA is a deed-recording category, not the assessor's Property Transfer Affidavit form (Form L-4260). The two are different documents. The relevant question is whether the buyer (LYNN 1553 LLC) filed L-4260 with Detroit's assessor, which the dataset cannot directly observe. Inferring "PTA not filed" from "TV not reset" is circular.

3. **The owner-name pipeline is broken in three places at once on this parcel:**
   - Assessor lists `GLYNN 1553 LLC` (likely OCR-dropped "L" → "LYNN")
   - Wayne County PTA grantee: `LYNN 1553 LLC`
   - Wayne County QC grantor: `HOF 1 REO 5 LLC` vs grantee `HOF I REO 5 LLC` (digit-1 vs Roman-I)

   The pipeline's `CHAIN_OF_TITLE_GAP` flags fire 5 times on this parcel, but at least 2 of them are pure name-normalization noise. **Discipline-rule-2 instantiation:** flag-counting without an entity-resolution pass overstates evidence severity. Score 95/100 here is partially manufactured by these false-positive chain flags.

4. **The legitimate signal stands without the noise.** Even discounting all five chain-of-title flags and the $0 QC flag, the SEV-only divergence ($222,700 SEV vs $21,843 TV on a property that demonstrably transferred for $364,900 to an unrelated LLC eleven months ago) is a clean MCL 211.27a violation worth ~$13.5K/yr.

### Why this is a stronger case than the chain-of-title flag count suggests

- **Property class is COMMERCIAL-IMPROVED** — meaning this is a multi-unit apartment building. The benefit from suppressed tax accrues to a holding LLC, not an owner-occupant. None of the MCL 211.27a(7) family/spousal exemptions plausibly apply.
- **Sale price ($364,900) is consistent with SEV-implied market ($445,400 = 2 × SEV)** — this isn't a bulk-portfolio price or a $0 QC. The transaction was real and arm's-length per the recorded terms code 03.
- **The grantor was a foreclosure REO trust (HOF I) selling its inventory to an unrelated single-asset LLC (LYNN 1553).** No 50%-or-less ownership change exemption applies.

So: this is a textbook overdue uncap. The signal is real. But the auxiliary audit-priority-score bumps came from artifact flags, not material evidence. (The underlying database column is named `fraud_score` in v1's source code; this report uses "audit-priority score" to avoid implying a legal finding of fraud.)

---

## Cohort-level pattern (citywide)

Pulled from `uncap_analysis` directly (the framework's own scoring) to characterize the broader population:

| Bucket | n | Annual tax gap (best-method) |
|---|---|---|
| Overdue, both methods agree | 4,317 | $8,644,015 |
| Overdue, SEV-method only (legally definitive, no MLS sale) | 2,162 | $3,216,569 |
| Overdue, sale-method only | 1,647 | (small — most have suppressed sale price) |
| **Total overdue** | **8,126** | **~$11.9M/yr (SEV-floor) – $26.2M/yr (sale-implied)** |

Cohort splits worth flagging:

**Owner type:**
| Bucket | n | Gap ($/yr) |
|---|---|---|
| INDIVIDUAL | 5,015 | $6,788,857 |
| LLC | 2,773 | $4,391,410 |
| OTHER_ENTITY (Inc/Holdings/Properties/Realty) | 260 | $542,386 |
| TRUST | 70 | $139,589 |
| Gov / Land Bank | 8 | $1,298 |

LLC-and-other-entity ownership is 38% of overdue parcels but ~42% of the dollar gap — entity-owned parcels uncapping-fail at higher dollar values per parcel ($1,584/yr vs $1,354/yr for individuals).

**Property class:**
| Class | n | Gap ($/yr) |
|---|---|---|
| RESIDENTIAL-IMPROVED | 7,205 | $8.43M |
| COMMERCIAL-IMPROVED | 303 | $2.36M |
| INDUSTRIAL-IMPROVED | 47 | $0.47M |

Commercial parcels are 3.7% of overdue count but 20% of the dollar gap — average $7,795/yr per commercial parcel vs $1,170/yr per residential.

**Data quality on the overdue set:**
- 6,809 `consistent` (sale price within 30%-300% of SEV-implied market — clean signal)
- 1,105 `sale_inflated` (likely bulk portfolio sale prices applied per-parcel — sale method unreliable)
- 148 `sale_suppressed` (sale price <30% of market — possible consideration hiding)
- 64 `zero_consideration` (deed records $0)

The 1,105 `sale_inflated` cases are the bulk-purchase pattern — investor LLCs buying portfolios where the per-parcel attribution is the contract price divided by parcel count. The framework correctly downgrades sale-method weight here and falls back to SEV-method, which is robust.

---

## Bottom line

The case parcel is a clean MCL 211.27a violation worth ~$13.5K/yr. The framework's headline finding (overdue) is correct. The framework's score-95 assignment is partly inflated by entity-name-normalization false positives that an entity-resolution pass would deflate.

The citywide pattern: ~8,126 overdue parcels and ~$11.9-26.2M/yr in suppressed taxes, with the entity-owned and commercial subsets carrying disproportionate dollar weight. The residential-individual majority (5,015 parcels, $6.8M/yr) is the more politically and operationally interesting cohort because it is also the most plausibly innocent (people who simply didn't know to file Form L-4260 after buying their house) — separating the willful from the negligent here requires deeper records the framework doesn't currently read (see `methodology_audit.md`, rule 1).
