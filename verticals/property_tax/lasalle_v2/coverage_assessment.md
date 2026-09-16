# Coverage Assessment — Detroit Property-Tax M-sources

**What this document does:** enumerates which M-sources the framework actually queries, which actor / transaction types each covers, and where the structural gaps are. Per Layer-3 discipline rule 2, "no signal" lines must be paired with coverage statements before they can be read as "no divergence."

---

## What's actually wired up

Inspected the source connectors at `/Users/ajay/exalted/detroit_fraud/sources/` and the actual contents of `mls_sales` and `deed_transfers` in the database.

| Source code | Live in DB? | Records | Notes |
|---|---|---|---|
| `detroit_opendata.py` (assessor ArcGIS) | yes | 382,123 parcels | This is R, not M. It's the assessor's own roll. |
| `wayne_county.py` (Parcelmaster) | yes | 2,478 deed rows over 567 parcels | Authority Tier 1 (county recorder). Pulled selectively — only for parcels first-pass-flagged as overdue or upcoming. |
| `redfin.py` (Redfin scraper) | **no** | 0 rows in `mls_sales` | Code exists but no actual Redfin rows in the snapshot. The single non-assessor row in `mls_sales` is `mls_manual` (the canonical 13300 LASALLE BLVD entry, hand-typed). |
| `zillow.py` (Zillow scraper) | **no** | 0 rows | Same. |
| `propstream.py` (PropStream) | **no** | 0 rows | Same. |
| `attom.py` (ATTOM API) | **no** | 0 rows | Same. |

So `mls_sales` table has 285,490 rows but **285,489 of them are `source = 'assessor_record'`** — i.e. the assessor's own `sale_date` / `sale_price` field re-shaped as a "sale" record. Only **1 row** is from any other "MLS" source.

**This is the single most important coverage finding.** The framework's nominal three-source M-side (assessor / Wayne County deeds / MLS scrapers) is operationally a one-source M-side: assessor records, with Wayne County deeds layered on for ~567 already-flagged parcels. Redfin/Zillow/PropStream/ATTOM are dark code paths.

That means:
- The "agreement between methods" check (Method A sale-price vs Method B SEV) is largely an internal consistency check on the assessor's own data, not a true cross-record divergence check.
- `data_quality = 'sale_inflated'` (1,105 overdue parcels) is the assessor's own field disagreeing with itself (sale_price_record vs SEV) — useful but it's R-vs-R, not R-vs-M.

---

## Actor / transaction coverage matrix

For the overdue cohort (8,126 parcels), what gets seen and what is structurally invisible:

### Well-covered
- **Standard recorded warranty deeds** between unrelated parties (1,073 WD rows, terms-code 03 ARM'S LENGTH = 1,147 rows). Wayne County records these reliably.
- **Residential single-family transfers with assessor sale_price populated** — the 6,809 `consistent` overdue parcels are exactly this slice.
- **Foreclosure sheriff's deeds** (88 SD rows, terms-code 10-FORECLOSURE = 100 rows). These show up in the deed table but the framework treats them like any other transfer; in practice MCL 211.27a treats the sheriff-to-bank step and the bank-to-buyer step as separate transfer events, with the second being the one that triggers reset. Code does not encode this distinction.

### Partially covered
- **Quit-claim deeds** (311 QC rows + 11 lowercase). The deed flagging logic catches them but cannot distinguish "true MCL 211.27a(7) exempt entity-restructuring transfer" (e.g. individual deeding to their own LLC) from "consideration-hiding" without external entity-ownership data. Right now they all get flagged as suspicious. Discipline-rule-3 instantiation: divergence detection ≠ exemption verification.
- **Land contracts** (50 LC rows, instrument code) — Michigan land contracts can trigger TV reset depending on terms. Not modeled.
- **Multi-parcel sales** (81 + 75 multi-parcel rows). The framework correctly downgrades these via `data_quality = 'sale_inflated'` (1,105 cases) but cannot allocate the contract price to individual parcels — it just falls back to SEV-method. That's correct behavior, but it leaves the actual per-parcel arm's-length price unobserved.

### Structurally invisible to current M
1. **PRE (Principal Residence Exemption) eligibility.** The assessor's `homestead_pct` is R (the claim), not M. The framework reads the percentage but never queries any M-source to check whether the claimant actually lives there. **Quantitative: 1,775 LLC-owned parcels in the overdue cohort claim PRE ≥ 50%; 1,709 claim full 100% PRE.** Citywide (overdue or not), **20,180 LLC-owned parcels claim 100% PRE**. PRE on entity-owned property is per se ineligible under MCL 211.7cc — only natural persons occupying the property as their principal residence can claim it. This is a separate pattern of delayed tax payments worth millions per year that the current framework does not score.

2. **Off-market entity-to-entity transfers.** Bulk portfolio sales between investor LLCs where no deed is recorded at the parcel level (instead, the LLC's own equity is transferred — change in beneficial ownership without a deed). Wayne County captures none of these. MCL 211.27a(6)(d) defines a >50% beneficial ownership change in the entity owner as a transfer-of-ownership for uncap purposes, but the framework cannot see it. M-source needed: Michigan SoS LARA filings + LLC operating-agreement amendments. LARA's portal is heavily restricted (per ARCHITECTURE.md known limits) so this is a real gap, not just unbuilt.

3. **Bank REO inventory transfers.** A foreclosure filling out as bank → REO trust → single-asset LLC → end buyer may have only the first and last legs recorded as priced transactions. Intermediate steps (like the 2024-06-18 $0 QC on the 1553 GLYNN CT case, HOF I GRANTOR TRUST → HOF I REO 5 LLC) flood the deed table with noise that current flagging misreads as suspicious.

4. **Land Bank → end-user pipeline.** 63,871 parcels owned by Detroit Land Bank Authority (DLBA). The Side Lot / Auction / Rehabbed program prices are typically nominal ($100-$1,000) but transfer-of-ownership rules under MCL 211.27a(7)(o) generally exempt these. Framework treats them as ordinary transfers and would flag them spuriously if it pulled the data. (Currently it doesn't pull deed records for them, so this is dormant rather than active.)

5. **Tax tribunal / Board of Review appeal outcomes.** When SEV is reduced via successful appeal, the resulting low SEV becomes the new floor for the uncap-on-transfer calculation. If the appeal was secured improperly (collusive, or based on falsified income statements for income-property assessments), the framework cannot detect it because it accepts SEV as authoritative. M-sources that would surface this: Michigan Tax Tribunal docket, City of Detroit BoR petition log. Not queried.

6. **NEZ Homestead district eligibility.** Entity-owned parcels in NEZ districts cannot claim NEZ Homestead benefit (16+ low-millage rate); the framework checks `nez_eligible` correctly but does not check whether individual claimants in NEZ zones actually live there, which is the same M-gap as the PRE issue.

7. **Commercial / income property valuation.** For COMMERCIAL-IMPROVED parcels (303 in overdue cohort), the assessor's SEV is supposed to be derived from rental income via the income approach to value (per Michigan State Tax Commission Guide). M-sources that would let an analyst test SEV: actual rent rolls (private), Section 8 HAP contracts (HUD), CoStar / RentCast comps, listed asking rents on Zillow Rentals. None are wired in. The framework's "TV << SEV" check is robust, but the deeper question "is SEV itself collusively low?" is structurally invisible.

---

## "We found nothing" honesty check

Lines from the framework's output that would mislead if read as "no divergence":
- **`status = no_sale`** (167,193 of 382,123 parcels). For most of these, no MLS-tier search ever ran — Redfin/Zillow/PropStream code paths are dark. So `no_sale` means "assessor didn't record a sale" not "no sale happened." Of these, 203,098 are `sev_only` no_sales, meaning even without a sale we *can* see TV-below-SEV via Method B, but the framework demotes them to no_sale status rather than flagging them. (The script's `status` field is gated on having a recent sale; a parcel can have TV way below SEV with no recent sale and never get flagged.)
- **`zero_consideration` overdue (n=64)**. Many of these are legitimate exempt entity-restructuring transfers under MCL 211.27a(7); without LARA / operating-agreement data, the framework can't sort the legitimate from the consideration-suppressed.
- **`audit-priority score = 0`** on overdue parcels (column literally named `fraud_score` in v1's source). About half the SEV-only overdues have low scores because no deed records were pulled for them (deed pull was selective). Low score ≠ low risk; it can mean low data.

---

## Concrete sources the framework should add

Analogous to how USPTO ODP closed a coverage gap in the public-co backtest:

| Gap | M-source to add | Authority tier | Access | Closes |
|---|---|---|---|---|
| PRE-on-LLC pattern | Cross-join `parcels.owner LIKE '%LLC%'` × `parcels.homestead_pct >= 50` | (already in DB; just needs scoring rule) | Free | 20,180-parcel population |
| Beneficial-ownership change | Michigan LARA / SoS LLC filings, owner change history | Tier 1 (gov primary) | LARA portal restricted; FOIA | Bulk portfolio entity-restructuring |
| Appeal-secured low SEV | Michigan Tax Tribunal docket; Detroit BoR petitions | Tier 1 | Tribunal: free web search; BoR: FOIA | Collusive low SEV |
| L-4260 PTA filing | Detroit assessor PTA log | Tier 1 | FOIA (no public DB) | True "PTA not filed" determination — currently inferred circularly |
| Income-property SEV check | CoStar / RentCast / HUD HAP / listed rents | Tier 3-4 | Paid (CoStar/RentCast); free (HUD, Zillow Rentals) | Commercial under-assessment |
| True MLS comps | Redfin / Zillow / PropStream | Tier 4 | Code already exists, scrapers must be re-run; CF-blocked sometimes | Independent confirmation of arm's-length sale prices |

Of these, the **PRE-on-LLC** join requires zero new data and would surface a pattern of delayed payments an order of magnitude larger than the missed-uncap pattern in pure parcel count. It is the highest-ROI delta from the current framework.
