# Detroit Property Tax: Combined Findings on Delayed Tax Payments

*Citywide analysis of 388,535 parcels across 29 zip codes | May 2026*

---

> **Disclaimer:** This document presents algorithmic analysis of public records for investigative and public-interest purposes. It is not a legal determination, and **nothing in it constitutes an allegation of fraud or criminal wrongdoing against any named individual or entity**. The patterns described below are delayed or under-paid property tax payments visible in public records — outcomes that may result from clerical error, inheritance of stale status, gaps in administrative process, or knowing non-filing. Distinguishing among those causes for any specific parcel requires investigation beyond what these public records support. All conclusions about specific transactions are drawn from official government records — Wayne County Register of Deeds, Detroit Open Data assessor records, Wayne County Parcelmaster — and are subject to independent verification. Readers are encouraged to consult those primary sources directly. Analytical flags such as "audit-priority score" are screening heuristics, not legal findings.

---

## Executive summary

Two **independent and additive** categories of delayed property tax payments are visible on Detroit's 2025 tentative assessment roll:

| Pattern | Statute | Parcels | Annual delayed/suppressed tax |
|---|---|---:|---:|
| **Missed uncap** — TV not reset after arm's-length transfer | MCL 211.27a | 8,114 | **$13.0M/yr** (conservative floor) |
| **PRE-on-Entity** — LLC/Inc/Corp claims Principal Residence Exemption | MCL 211.7cc | 23,211 | **$10.7M/yr** |
| **Overlap** (parcels in both) | — | ~2,562 | (already included above; not double-counted) |
| **Union — unique parcels affected by at least one pattern** | — | **~28,763** | **~$23.7M/yr combined** |

The two patterns differ in structure but converge on the same outcome: **owners of Detroit residential property held through entities are paying 50–80% less in annual property tax than a comparable individual buyer would**, by either (a) the recorded sale price not triggering a Taxable Value reset (missed uncap), (b) a homestead exemption that statute does not appear to allow for an entity owner (PRE-on-Entity), or both.

Detection of both patterns is now wired into the production Signal OS engine (commit `214314f`, 2026-05-18). Citywide scans surface both patterns in one pass.

---

## The two mechanisms

### Pattern 1 — Missed Uncap (MCL 211.27a)

When a property changes ownership at arm's length, Michigan law requires the new owner's Taxable Value (TV) to "uncap" — reset from the prior owner's capped TV to the assessor's State Equalized Value (SEV) at the next annual assessment. The mechanism for triggering this is a Property Transfer Affidavit (PTA) the buyer must file within 45 days.

The administrative gap: the assessor relies on the buyer to self-report the transfer via PTA, rather than proactively cross-referencing recorded deeds against the assessor roll. An owner who acquires through a **$0 quit claim deed** and does not file a PTA leaves no signal the assessor's automated workflow can act on. The statutory penalty for non-filing is $5/day capped at **$200** — a rounding error relative to multiple years of taxes calculated against a stale base.

The canonical case (`13300 La Salle Blvd`) shows the pattern at full clarity: $151,500 MLS sale + $0 quit claim deed filed the same day + no PTA + TV remains capped at $34,100 = $2,791/yr in delayed tax payments indefinitely. Full case detail and 64 similar zero-consideration cases are in [`REPORT_UNCAP_LASALLE_2026_05.md`](REPORT_UNCAP_LASALLE_2026_05.md).

Detection signal: **TV < 92% of SEV after a recorded transfer in the past three years**.

### Pattern 2 — PRE-on-Entity (MCL 211.7cc)

The Principal Residence Exemption reduces the millage rate from ~67 to ~40 mills for properties that are "owned and occupied as a principal residence" by the person claiming the exemption. The Michigan State Tax Commission has consistently held that limited-liability entities (LLC, Inc, Corp, Ltd, LP) cannot occupy a principal residence in the statutory sense — PRE is reserved for natural persons.

23,211 Detroit parcels have an entity-class owner claiming 100% PRE. On a $20,000-TV parcel, this reduces the owner's annual tax by $540 ($1,340 non-homestead − $800 PRE). Across the population, $10.72M/yr.

These patterns plausibly arise from (a) clerical errors in the original PRE affidavit the assessor has not caught, (b) inherited PRE status from a pre-LLC owner that was never withdrawn after a transfer to the LLC, or (c) knowing non-correction of a status the assessor's limited audit capacity hasn't reached. **The detection signal is contained entirely in the assessor roll — no external data is required.**

Full per-zip / top-owner / per-parcel-class breakdown in [`lasalle_v2/PRE_ENTITY_VALIDATION_2026_05_19.md`](lasalle_v2/PRE_ENTITY_VALIDATION_2026_05_19.md).

---

## Overlap analysis

A server-side proxy filter on the 2025 roll (TV < 92% of SEV + transfer in last 3 years + 100% PRE + strict-entity owner) returned **2,562 parcels** in the intersection of both patterns. These are the highest-priority audit candidates — an entity-owned parcel that both (a) had a transfer with no TV reset, AND (b) is claiming the homestead exemption that the State Tax Commission interpretation does not allow for entity owners.

On the 2,562 intersection parcels:
- Sum TV: $50.5M
- Sum SEV: $86.8M
- Combined annual delay: TV under-reporting × 67 mill (non-homestead, since LLC) PLUS the PRE-related millage differential on capped TV. Worst-case: TV uncap to SEV at 67 mills = ($86.8M − $50.5M) × 67/1000 = $2.43M/yr from uncap alone, plus $50.5M × 27/1000 = $1.36M from the PRE-related component = **~$3.8M/yr on the 2,562 highest-priority parcels**.

This is the population an audit team would address first.

The server-side proxy slightly over-counts vs the engine's 8,114 uncap headline, so 2,562 is best read as an upper bound on the true intersection size.

---

## Why the assessor's office doesn't currently catch either

Both patterns persist for the same structural reason: **the assessor's workflow is downstream of self-reported information that the property owner controls**.

For missed uncap, the burden is on the buyer to file a PTA. No PTA filed = no uncap workflow. The $200 cap on the non-filing penalty makes non-filing economically rational at any sale price above ~$5,000.

For PRE-on-Entity, the burden is on the assessor to verify the PRE affidavit (Form 2368) matches the actual owner type. The assessor receives the affidavit at the time of original claim, but does not routinely re-verify when ownership transfers to an LLC. A pre-existing PRE on a parcel that gets sold to an LLC persists silently unless someone audits it.

Both gaps are systemic, not individual. They are gaps in the administrative process — and an automated detector reading the same public data the assessor already has can surface every instance.

---

## Combined audit prioritization

Suggested rank order for assessor / treasury attention:

1. **Intersection parcels (~2,562 with both patterns)** — entity-owned, recent transfer without TV reset, claiming PRE. Highest leverage per audit.
2. **Commercial/industrial PRE claims (~200 parcels)** — PRE on non-residential property is impermissible regardless of owner type. Includes some of the largest single-parcel exposures (e.g., 12130 SCHAEFER, D INVEST LLC, $961K TV / $25,958/yr).
3. **Foreign-entity PRE claims** — Ontario-numbered corporations and similar non-Michigan-resident entities cannot plausibly occupy Michigan principal residences.
4. **Zero-consideration quit claim deeds with high MLS-vs-deed delta** — the 64 canonical La Salle-pattern cases. Best per-parcel dollar exposure.
5. **Concentrated portfolios** — entities appearing across 10+ parcels in either pattern. Portfolio-level audits scale better than parcel-by-parcel.
6. **The long tail** — ~16,000 parcels in the $10K–$50K TV band with PRE-on-Entity status. Per-parcel exposure is modest ($300–$1,350/yr), but the count is large; best handled via a batch PRE-rescission process.

---

## Implementation status (Signal OS engine)

Both detectors are first-class rules in the property_tax vertical's Michigan jurisdiction:

| Rule | Statute | Implementation | Status |
|---|---|---|---|
| Missed uncap (gap function) | MCL 211.27a | `gap.py` → `PropertyTaxGapFunction` | Production since initial Signal OS commit |
| `PRE_ENTITY_VIOLATION` | MCL 211.7cc | `jurisdictions/michigan/rules/pre_entity_violation.py` | Production as of commit `214314f`, 2026-05-18 |
| `PILOT` | MCL 125.1415A | `jurisdictions/michigan/rules/pilot.py` | Production (exempts PILOT/LIHTC parcels from both detection paths) |
| `PRE` (gap modifier) | MCL 211.7cc | `jurisdictions/michigan/rules/pre.py` | Production (legitimate PRE-millage reduction for natural-person owners) |
| `NEZ` (gap modifier) | MCL 207.771 | `jurisdictions/michigan/rules/nez.py` | Production (reduces millage for NEZ-eligible parcels) |
| `PA210`, `OPRA` | MCL 207.771 / 207.841 | None — LLM fallback | Detectable=False — flagged but requires Michigan Treasury data request |

The scorer handles combined cases: when both a TV-uncap gap AND a PRE_ENTITY_VIOLATION fire on the same parcel, the uncap calculation uses the non-homestead millage (i.e., does not apply a PRE reduction the LLC owner cannot legitimately claim) and the PRE-related millage differential on current TV is summed in.

Both findings are surfaced by the standard CLI:

```bash
signalos run --zip 48238 --deeds --llm
signalos report --zip 48238 --tier high --csv detroit_48238.csv
```

Internally the rule continues to be named `PRE_ENTITY_VIOLATION` because that's the existing API contract; the term refers to the statutory non-compliance with MCL 211.7cc's natural-person-occupancy requirement, not a legal finding of wrongdoing.

---

## What's NOT in scope

This analysis does not address:

- **PA 210 (Commercial Rehabilitation Act)** TV freezes — these produce a TV-below-SEV pattern identical to a missed uncap but are legitimate. ~340 commercial parcels in the flagged set could be PA 210; verification requires a Michigan Treasury data request.
- **OPRA (Obsolete Property Rehabilitation)** — similar legitimate TV freeze for blighted commercial. Not in assessor roll; expected minimal residential overlap.
- **Trust-structured PREs** — Trust owners were excluded from the PRE-on-Entity detector because revocable living trusts can claim PRE under specific conditions (MCL 211.7cc(5)). A targeted review could identify the trust subset where grantor isn't owner-occupant.
- **PRE-on-Entity verification of actual occupancy** — the detector flags claims; it cannot verify whether an LLC ever occupied the property. Some flagged parcels may have been occupied by a natural-person tenant who was the LLC's beneficial owner. This is a legal question, not a data question.
- **Beneficial-ownership disclosure** — many entity owners are themselves shell LLCs. Identifying the ultimate human beneficial owner requires Michigan LARA corporate filings, not the assessor roll.
- **Intent and cause for any specific parcel.** The detector tells you a tax payment is below what statute appears to require. It cannot tell you whether the cause is clerical, inherited from a prior owner, an unresolved administrative gap, or knowing non-filing. Establishing intent for any individual parcel requires investigation outside this dataset.

---

## Related documents

| Document | What it covers |
|---|---|
| `REPORT_UNCAP_LASALLE_2026_05.md` | Canonical missed-uncap report. La Salle / Glynn Court / Garden case studies, NEZ analysis, exemption cross-reference, methodology. |
| `lasalle_v2/PRE_ENTITY_VALIDATION_2026_05_19.md` | PRE-on-Entity validation: count, dollar exposure, geographic and owner distribution, top exposures. |
| `lasalle_v2/comparison.md` | A/B between the original analyst's report and the blinded-re-run methodology. |
| `lasalle_v2/methodology_audit.md` | What the lasalle_v2 methodology gets right and wrong. |
| `lasalle_v2/coverage_assessment.md` | Detroit Open Data + Wayne County deeds coverage analysis. |
| `README.md` | property_tax vertical overview, layout, run instructions. |

---

## Recommended next steps

For Signal OS:
- **Run a combined detection pass on a single zip** (e.g., 48224, where both patterns are highest density) and produce a per-parcel CSV ranked by combined audit-priority score. This is the right artifact for an external audit pilot.
- **Build a `concentrated_owner` detector** that flags entities appearing across N or more parcels in either pattern. Portfolio-level audits are more efficient to litigate.
- **Wire Wayne County LARA** corporate-filings data to resolve beneficial owners of the top concentrated-owner entities. Outside the assessor-only data envelope but inside the public-record envelope.

For the public-interest audience:
- The combined $23.7M/yr figure is the headline. It exceeds the city's annual fire-department budget for capital equipment, several times over.
- The two patterns are correlated: an entity that under-reports a sale price (missed uncap) is more likely to also carry forward a PRE status that doesn't apply. The 2,562-parcel intersection is where the two patterns co-occur.
- The administrative gap is what enables both patterns. Michigan law is clear on MCL 211.27a (mandatory uncap on arm's-length transfer) and MCL 211.7cc (PRE is for natural persons). Closing the gap requires the assessor's office to add deed-record + owner-type audits to its workflow — not legislation.
