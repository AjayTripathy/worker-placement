# Rent Stabilization Audit v1 — Brief

This folder is a methodology audit of the `rent_stabilization` vertical using the post-improvement Signal OS Layer 3 operational-discipline rules (from top-level `signalos/ARCHITECTURE.md`).

It is **not** a blinded re-run against a prior analysis (unlike `verticals/property_tax/lasalle_v2/`, which compared against `/Users/ajay/exalted/detroit_fraud/reports/lasalle_summary.md`). The rent_stabilization vertical has framework code and connectors but no stored production output to A/B against. So the audit is structural: it asks "what would change about how this vertical operates if we applied the same rigor as the lasalle_v2 audit produced for property tax?"

## What the audit produces

- `analysis.md` — overall read; how the framework currently works, what the new methodology would change
- `coverage_assessment.md` — what M-sources cover what NYC actor / unit types; structural gaps
- `methodology_audit.md` — per-rule transfer assessment (all 6 Layer 3 rules), parallel structure to `property_tax/lasalle_v2/methodology_audit.md`
- `candidate_triples.md` — sibling R/f/M triples worth wiring as new fs against the same M (analogous to PRE-on-LLC for property tax)

## Why a methodology audit and not a blinded data run

A blinded data run requires a canonical case to test against (in lasalle_v2, it was 13300 La Salle Blvd → discovered Glynn Court independently → A/B). For rent_stab there's no canonical NYC building previously analyzed in this repo. We could pick one and run, but the comparison value is lower without a v1 to push against.

If a real NYC building / portfolio enters the picture (e.g., a specific landlord under HCR audit), spawn a parallel `audit_v2/` for the blinded data run.
