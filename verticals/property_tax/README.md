# property_tax

Detects patterns of delayed property tax payments under MCL 211.27a (Michigan): when a property transfers, the buyer must file Form L-4260 within 45 days and the assessor must reset Taxable Value to State Equalized Value at the next assessment cycle. The penalty for non-filing is $200 max — economically negligible relative to ongoing tax under-payment.

> Findings here describe property tax payments below what statute appears to require. They are not legal findings of fraud or criminal wrongdoing against any specific owner. Causes for any individual parcel may include clerical error, inherited status from a prior owner, administrative gaps, or knowing non-filing — distinguishing among those requires investigation beyond this dataset.

## Production state

- **Detroit citywide scan complete** (382,123 parcels, 29 zip codes): **8,126 overdue parcels, $11.9M–$26.2M/yr in delayed tax payments**
- **38% of overdue parcels are entity-owned** (LLC/Inc/Trust); these account for 42% of dollar gap
- **Held-out blinded re-run** in [`lasalle_v2/`](lasalle_v2/) validated the headline + surfaced PRE-on-LLC as a separate ~23K-parcel pattern of delayed payments
- **PRE-on-Entity now wired** (`PRE_ENTITY_VIOLATION` rule, commit `214314f`): 23,211 parcels, **$10.7M/yr** delayed — validated 2026-05-18 against Detroit Open Data

## Reports

| Report | Covers |
|---|---|
| [`REPORT_DETROIT_DELAYED_TAX_PAYMENTS_2026_05_19.md`](REPORT_DETROIT_DELAYED_TAX_PAYMENTS_2026_05_19.md) | **Combined synthesis** — both delayed-payment patterns, overlap analysis (~2,562 intersection parcels), combined audit prioritization, implementation status |
| [`REPORT_UNCAP_LASALLE_2026_05.md`](REPORT_UNCAP_LASALLE_2026_05.md) | Canonical missed-uncap finding (MCL 211.27a). La Salle / Glynn Ct / Garden case studies, NEZ analysis, exemption cross-reference |
| [`lasalle_v2/PRE_ENTITY_VALIDATION_2026_05_19.md`](lasalle_v2/PRE_ENTITY_VALIDATION_2026_05_19.md) | PRE-on-Entity validation (MCL 211.7cc). Per-zip / top-owner / per-class breakdown, TV-vs-SEV reconciliation |
| [`lasalle_v2/comparison.md`](lasalle_v2/comparison.md), `analysis.md`, `coverage_assessment.md`, `methodology_audit.md` | Blinded re-run methodology + A/B against the original analyst's report |

## Layout

```
property_tax/
├── manifest.py            VerticalManifest declaration
├── models.py              Vertical-local types
├── cap_law.py             MCL 211.27a logic — when does TV reset?
├── gap.py                 GapFunction: TV-vs-SEV-implied-by-sale
├── scorer.py              Severity tiers, dollar impact computation
├── sources/               Cross-jurisdiction sources (Redfin, Zillow MLS connectors)
├── jurisdictions/
│   ├── michigan/          Statute model — used by Detroit
│   ├── detroit/           Detroit-specific sources, config, registry builder
│   ├── la_county/         LA County (initial wiring)
│   └── california/        California cap-law shared logic (Prop 13 family)
└── lasalle_v2/            Held-out blinded re-run; A/B against /Users/ajay/exalted/detroit_fraud/reports/lasalle_summary.md
                          (external-repo path; "detroit_fraud" is a historical directory name predating
                           the current "delayed tax payments" framing — not a legal characterization)
```

## Detroit jurisdiction

Source connectors:
- **Detroit Open Data assessor** — full parcel roll (TV, SEV, ETCV, owner, transfer_date, sale_price_record, homestead_pct, NEZ district)
- **Wayne County Parcelmaster** — deed records (instrument, terms, grantor/grantee, liber/page, consideration)
- **Redfin / Zillow** — MLS sale prices (note: per `lasalle_v2/coverage_assessment.md`, these connectors exist but are operationally dark in the snapshot — `mls_sales` is 99.9999% assessor-record-repackaged)

Run:
```bash
signalos run --zip 48238 --deeds --llm
signalos report --zip 48238 --tier high --csv detroit_48238.csv
```

## Known triples

| R | f | M | Status |
|---|---|---|---|
| Assessor TV | Must reset to ~SEV after arm's-length transfer (MCL 211.27a) | Wayne County deeds + MLS | **Built** — uncap detection |
| Owner's PRE eligibility claim (homestead_pct) | PRE requires natural-person owner-occupancy (MCL 211.7cc) | Owner type on assessor roll | **Built** — `PRE_ENTITY_VIOLATION` rule (Michigan jurisdiction). Validated 2026-05-18: 23,211 strict-entity parcels claim 100% PRE → **$10.7M/yr** suppressed |

### About the PRE-on-LLC discovery

The PRE-on-LLC triple is the cleanest validation in the repo that the held-out blinded re-run methodology produces real findings the original analyst missed. The original LA Salle analysis (in `/Users/ajay/exalted/detroit_fraud/reports/lasalle_summary.md`) treated PRE only as a downward sensitivity adjustment to the missed-uncap headline ($2.1M off the $13M figure). The v2 re-run, applying the Layer 3 "divergence ≠ solvency" discipline rule (which forces the question "what other forms of tax under-payment does this framework miss BY DESIGN?"), surfaced PRE-on-LLC as a structurally distinct pattern of delayed tax payments.

#### Validation (2026-05-18 Detroit Open Data scan)

Direct query of `tentative_assessment_roll_2025` ArcGIS layer:

| Metric | Initial estimate | Validated |
|---|---:|---:|
| Strict-entity parcels (LLC/INC/CORP/LTD/LP) @ 100% PRE | ~20,180 | **23,211** |
| Average TV | ($30K SEV-like) | $17,116 (TV) |
| Average SEV | $30K | $31,349 |
| Annual delayed tax payments | ~$16M | **$10.72M** |
| Co-op / LDHA legit carve-outs | (not assessed) | 23 (~0.1%) — negligible |
| Property class | (assumed residential) | 98% residential-improved ✓ |

The initial $16M figure used SEV ($30K) as the taxable base; the actual taxable base is the capped TV ($17,116 avg), which is ~55% of SEV under Michigan's Headlee/Proposal A caps. At current capped TV, real annual delayed tax payments = 23,211 × $17,116 × 27 mills / 1000 = **$10.72M/yr**.

If TV had also been correctly uncapped to SEV under MCL 211.27a (a separate, independent pattern of delayed payments), the maximum-possible exposure rises to ~$19.6M/yr. The two paths (PRE-on-entity, TV-uncap-failure) are independent and should both be reported.

#### Wired into the engine (2026-05-18)

New rule `PRE_ENTITY_VIOLATION` in `jurisdictions/michigan/rules/pre_entity_violation.py`:
- Fires when `owner_is_entity AND homestead_pct > 0 AND not in co-op/LDHA carve-out`
- Annual impact = `TV × (67 - 40) × pct / 100 / 1000`
- Scorer pushes the parcel to **high tier** regardless of other components (MCL 211.7cc is a hard statutory contradiction, not a sensitivity adjustment)
- `PropertyTaxGapFunction` now synthesizes a `GapResult` for the no-TV-uncap-but-PRE-on-entity case so the rule chain can process the parcel
- Sanity-tested against 14 known parcels (BANYAN INVESTMENTS LLC, SOLID GROUND EJ LLC, D INVEST LLC, 4766 COMMONWEALTH LLC) — all matched correctly with accurate annual-dollar math
- Negative control: natural-person owners with 100% PRE are not flagged (no false positives)

Full A/B in [`lasalle_v2/comparison.md`](lasalle_v2/comparison.md).

## Related

- Original Detroit work lives in a separate repo at `/Users/ajay/exalted/detroit_fraud/` — pre-Signal-OS-refactor scripts + the canonical `reports/lasalle_summary.md`. The directory name is historical, predating the current "delayed tax payments" framing; it is not a legal characterization of any owner's conduct.
- `lasalle_v2/comparison.md` is the A/B between v1 and the post-improvement methodology
