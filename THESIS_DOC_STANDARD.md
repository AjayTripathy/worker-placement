# THESIS_DOC_STANDARD (v1.7, 2026-08-22) — what every position's final doc must contain

A position is UNDOCUMENTED unless one final doc (desk/reports/*.html + artifact) carries ALL of:

## 1 · The four-idea frame (its own section, per name)
- **Market believes** — the priced-in story, stated fairly enough that its holder would sign it
- **We believe** — our claim, in numbers where possible
- **Why we might have edge** — the mechanism (neglect, latency, structure, verified divergence);
  "nobody is grossly mispricing" is an acceptable answer and mandatory honesty for RP_FAIR carry
- **Why it may be priced in / why we may be wrong** — the strongest version, not a strawman
- **Mechanism falsifier** — the dated, checkable thing that kills the claim
- **Edge type** — EDGE / RISK_PREMIUM / RP_TAINTED / NONE (sizing reads this label)


## 1b · What could go wrong (the pre-mortem — v1.7, principal-directed 2026-08-22)
Distinct from the frame's "why we may be wrong" (the epistemic counter-case) and from the kill list
(monitorable tripwires). This block is the map of failures that DON'T ring bells:
- **Top 3 failure narratives**, written as stories not bullets-of-adjectives — at least ONE must be a
  mode with NO monitorable tripwire (name the unknown-unknown class: e.g. undisclosed related-party,
  unpublished competitor data, regulatory mood shift, fraud beneath the audited layer)
- **The reflexive/structural leg** — how our OWN actions or situation hurt us: order size vs ADV,
  our predicted flow, household concentration, tax constraints forcing holds, doctrine interactions
  (a resting order that becomes wrong when a different rule fires)
- **The pre-mortem sentence**, verbatim format: "If this position loses money, the most likely
  reason will be ___." Written BEFORE entry; quoted, unedited, at every post-mortem. The sentence is
  the block's contract — everything else exists to make this one line honest.

## 2 · SignalOS validation (the verification table)
Every load-bearing claim independently traced by fresh eyes to a PRIMARY document and rendered in the doc:
claim → source (citation/accession) → VERIFIED / CORROBORATED / REFUTED / UNVERIFIABLE → actual number.
Courts and reds generate; verification audits. Discrepancies print in the doc, including favorable ones.
The sweep runs to the doc's date (the ad-hoc rule — a 6-day-old guide cut killed one court already).

## 3 · The Brier-book entry
The frozen calibration call named in the doc: `TICKER|cat_date`, the resolution bar verbatim, our_p,
the external anchor if one exists, and the detector/instrument that grades it. No frozen call = no final
doc = no envelope. Nowcasts and later evidence adjust SIZING only, never the frozen number.

## Enforcement
`desk/consistency_check.check_position_docs_complete` (hourly): every held or staged-awaiting-click name is
checked for (a) an EC record with structured verdict_state, (b) an OPEN or graded calibration call, (c) a
desk/reports doc naming the ticker that contains the frame markers and a verification table. Missing leg →
loud flag until fixed. Pre-v1.6 held names backfill flag-driven; new positions comply before the envelope. v1.7 pre-mortem block: docs dated on/after 2026-08-22 REQUIRE it; earlier docs backfill flag-driven (WARN not CRITICAL).
