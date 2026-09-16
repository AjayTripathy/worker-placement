# LA Salle v1 vs v2 — Comparison

**v1:** `/Users/ajay/exalted/detroit_fraud/reports/lasalle_summary.md` (original analysis, May 2026)
**v2:** this folder, blinded subagent re-run (2026-05-15) using post-improvement Signal OS methodology

The v2 subagent had access to the same database (`uncap_tracker.db`) and Wayne County / source connector code. It did NOT have access to v1's text or conclusions. Three deliverables: `analysis.md`, `coverage_assessment.md`, `methodology_audit.md`.

---

## What v2 confirms

| | v1 | v2 |
|---|---|---|
| Citywide overdue count | 8,114 (8,126 before exempt removal) | 8,126 verified directly from `uncap_analysis` |
| Tax-gap range | $11.9M–$15.3M/yr (conservative–upper bound) | $11.9M (SEV-floor) – $26.2M/yr (sale-implied) |
| Entity-owned share | 38.5% of count | 38% of count, ~42% of dollar gap |
| Commercial dollar density | (not separated in v1 zip-by-zip table; implicit in 48226/48216 outliers) | 3.7% of count, 20% of dollar gap; $7,795/yr/parcel vs $1,170/yr residential |
| Case-level signal direction | $0 QC + MLS sale = MCL 211.27a violation | Confirmed on Glynn Court: $13.5K/yr signal stands without auxiliary flags |
| Basic R/f/M decomposition | TV vs SEV vs MCL 211.27a — sound | Verified end-to-end; SEV-method is the binding floor when sale data is suppressed |

**Overlap on case selection:** v2 was instructed to pick a case "different than 13300 LASALLE BLVD." It picked 1553 GLYNN CT — which IS in v1 as the second worked example (Boston-Edison adjacent, audit-priority score 95 — v1 calls the column `fraud_score`). The blinding worked in one direction (no access to v1) but blinded selection independently landed on one of v1's headline cases. That's a positive signal that these really are the most salient examples in the cohort, not an artifact of v1's specific framing.

---

## What v2 found that v1 did not

### 1. PRE-on-LLC pattern — order-of-magnitude larger by parcel count

> "20,180 LLC-owned parcels claim 100% PRE citywide" — `coverage_assessment.md` §"Structurally invisible to current M" item 1

PRE (Principal Residence Exemption, MCL 211.7cc) reduces millage from ~67 to ~40 mills for owner-occupied primary residences. **Entities cannot claim PRE** — the statute requires natural-person occupancy. The v2 agent identified that the database already contains both `parcels.owner` and `parcels.homestead_pct`, and a simple cross-join surfaces this population.

**v1 treatment of PRE:** mentioned in the Exemption Cross-Reference table; modeled at 67 mills with a "$2.1M sensitivity" if all 4,766 PRE-claiming non-NEZ overdue parcels were credited at 40 mills. v1 treated PRE as a downward adjustment to the headline finding, not as its own pattern category.

**v2 reframes:** PRE-on-LLC is a separate `f` (eligibility-claim divergence vs occupancy-record), structurally distinct from the missed-uncap `f` (TV-reset-claim divergence vs deed-record). Citywide it's an order of magnitude larger by parcel count than the 8,126 missed-uncap finding. Within the overdue cohort itself, 1,775 LLC-owned parcels claim PRE ≥50% — already an entity-PRE subpopulation hidden inside the missed-uncap population.

**Caveat:** the agent didn't compute the dollar exposure. At ~27 mills differential (67-40) on 20,180 parcels at average SEV ~$30K, rough estimate: 20,180 × $30,000 × 0.027 ≈ $16M/yr — comparable to or exceeding the missed-uncap finding by dollars too, if the parcel count holds up to verification.

### 2. MLS data is operationally absent

> "285,489 of 285,490 `mls_sales` rows are `source='assessor_record'` — the assessor's own field repackaged. Only 1 row is from any other source." — `coverage_assessment.md` §"What's actually wired up"

This is a coverage-assessment finding the v1 report did not surface. v1's "method_agreement = both" framing implies cross-record corroboration (sale-price method vs SEV method, two independent paths). v2 identifies that both methods derive from the assessor's own data — they're two interpretations of one source, not coverage convergence. The signal is still legitimate (TV<<SEV is the assessor disagreeing with itself, which is tautologically meaningful) but the *framing* in v1 that two independent methods agree is mis-stated.

**Practical consequence:** v1's tax-gap range of $11.9M-$15.3M is computed from the assessor's own data top-to-bottom. The Redfin/Zillow/PropStream/ATTOM connector code exists but never populated the database. If those sources had run, the per-parcel sale prices might be different (potentially higher in some cases, surfacing additional under-capping), and the data_quality classification ('sale_inflated' vs 'consistent') would have actual external validation.

### 3. The audit-priority score (column name `fraud_score` in v1's code) is hindsight-calibrated

> "The 30-point bucket for `instr == 'QC' and zero and prior_arms_length` directly encodes the LASALLE shape. The 30-point TV-suppression-depth bucket sets the cutoff right where LASALLE sits. The 'consideration suppression' 15-point dimension is calibrated to the LASALLE deed-vs-MLS-price gap." — `methodology_audit.md` §Rule 6

v1 reports audit-priority-score thresholds (≥65 flagged for review, top cases at 95; the column is literally named `fraud_score` in v1's source) but doesn't note that the score weights were authored after the LASALLE case was known. Per the new methodology Rule 6, this is contaminated calibration: the score weights encode the canonical case shape, so cases sharing that shape get high scores partly because the score was built around them. The score is useful as a ranking aid but is NOT a falsifiable probability.

**Practical consequence:** v1's "64 confirmed cases" tier and the table of concentrated owners (SATORI 1, VFMT, DUNMERE, etc.) at the top of the citywide ranking are reasonable as a ranked output, but the implied calibration ("≥65 means high-confidence audit target") is unverified against any held-out validation set.

### 4. Glynn Court score-95 has noise components

> "5× CHAIN_OF_TITLE_GAP flags fire on this parcel, but at least 2 of them are pure name-normalization noise (GLYNN/LYNN OCR drop; HOF 1 vs HOF I Roman/digit-1)." — `analysis.md` §"Evidence trail and what's odd"

v1's writeup of Glynn Court emphasizes the 5-link entity chain (HOF I Trust → HOF I REO 5 → GLYNN 1553 LLC) as evidence of elaborate structuring. v2 confirms the underlying signal is real (~$13.5K/yr SEV-method) but identifies that the *score* is partly inflated by name-normalization issues that an entity-resolution pass would deflate. The case is still flagworthy; the magnitude framing is partly artifact.

### 5. PTA-not-filed is inferred circularly

v1: "the assessor relies on Property Transfer Affidavits (PTAs) rather than proactively cross-referencing deed records ... investors who understand this do not file PTAs."

v2 (`methodology_audit.md` §Rule 1): the framework has no direct evidence the buyer failed to file L-4260; it infers non-filing from "TV not reset." But TV not reset can have other causes (assessor backlog, in-progress reset, exemption claim under review). The actual L-4260 filing log is FOIA-able from Detroit's assessor office and would be direct evidence — currently the framework conflates the *consequence* (low TV) with the *violation* (no PTA filing).

---

## What v1 had that v2 didn't reproduce

- **Direct conversation with the city assessor's office** (v1 §"What the Assessor's Office Said") — qualitative confirmation that the gap is structural, not enforcement-failure. v2 had no access to this; it's primary research that doesn't replicate from the database alone.
- **Specific MLS sale prices** for La Salle Blvd, Glynn Court, etc. v1 quotes "$151,500" for La Salle and "$364,900" for Glynn Court — these are in `mls_sales` but only because they were hand-entered (`source='mls_manual'`). v2 surfaced this as a coverage gap.
- **30+ NEZ district breakdown** (v1 §"NEZ District Breakdown") — v2 verified the NEZ overall counts but didn't break out per-district.
- **Serial actors table** (v1 §"Serial Actors", 10 entities with parcel counts and zip spread) — v2 verified entity-owned share at the cohort level but didn't reproduce the per-actor enumeration.

---

## Net read

v2 confirms the v1 finding (~8,126 overdue, $11.9M-$26.2M/yr) and validates the case-level signal direction. v2 surfaces five things v1 didn't:

1. **A larger separate pattern of delayed payments** (PRE-on-LLC, ~20K parcels, possibly $16M+/yr — bigger than the original finding by both count and dollars if the rough estimate holds)
2. **A coverage gap** (MLS sources are dark — `method_agreement = both` is misleading)
3. **A calibration issue** (the audit-priority score's weights encode the LASALLE pattern; not held-out validated)
4. **A score-magnitude artifact** (Glynn Court score-95 partially inflated by entity-name-resolution noise)
5. **A circular-inference issue** (PTA-not-filed is inferred, not observed; FOIA-able L-4260 log would be direct evidence)

v2 does not reproduce v1's primary research (assessor conversation) or its serial-actors / NEZ-district enumeration. Those are additive on the v1 side.

**Recommendation for follow-up if v2's findings hold up:**
- Verify the PRE-on-LLC count (20,180 parcels) directly in the database — this is the highest-ROI extension if accurate
- FOIA Detroit Assessor for the L-4260 filing log to convert PTA-not-filed from inferred to observed
- Run an actual entity-resolution pass (Levenshtein + Roman/digit normalization) on owner-name records and re-score Glynn Court / similar cases without name-noise inflation
- Re-run Redfin/Zillow connectors to populate `mls_sales` with true MLS prices and re-test "method agreement"
- Hold back a neighborhood (e.g. one zip code) from the audit-priority-score calibration and re-measure precision/recall vs the v1 ranking on that holdout
