# art_donation_fraud — audit_v1 brief

First-pass build of the Signal OS vertical for inflated FMV deductions on art donated to qualified museums under §170(e).

This audit_v1 documents both the **structural audit** (what would and would not be a sound fraud signal here) and the **e2e v1 run** (Met + MoMA cohort, ~16K gifts, 77 flagged donors). Unlike `rent_stabilization/audit_v1/`, this folder ships the cohort run alongside the methodology audit because the vertical was greenfield — no pre-existing implementation to push against.

## Why this vertical

- **I (incidence):** ~$3-5B/yr in non-cash art deductions claimed against U.S. federal income tax (IRS Statistics of Income, latest available). IRS Art Advisory Panel reviews appraisals >$50K and historically reduces ~30% of submitted valuations by ~30%, implying aggregate annual fraud ≈ **$1B+/yr**.
- **L (loss per case):** Very high. Single large donation can carry $10M+ claimed FMV; 30% inflation × 37% marginal rate = $1M+ Treasury cost per case. Whistleblower bounty (IRC §7623) is 15-30% of recovery.
- **accessibility(M):** **Mixed**. Museum acquisition records are very accessible (Met + MoMA publish bulk CSVs on GitHub). Auction comparables are paywalled (Artnet, Artprice) or behind anti-bot defenses (Christie's, Sotheby's). Form 8283 itself (the R) is not public.

## What this folder produces

- `BRIEF.md` (this file) — framing and scope
- `analysis.md` — overall read; what the v1 run reveals; what would change with each missing connector
- `coverage_assessment.md` — which donor / work / claim types the current M-sources reach
- `methodology_audit.md` — per-rule transfer assessment (Layer 3 rules from `ARCHITECTURE.md`)
- `candidate_triples.md` — sibling R/f/M triples within the vertical worth wiring
- `connectors_to_add.md` — first-class connector backlog with bucket triage (agent / agent-adjacent / human)
- `donor_findings.json` — raw 1,295-donor portfolio scores
- `fraud_report.md` — polished output of the v1 cohort run with a `Debt and tradeoffs` section

## What this v1 cannot say

The cleanest fraud shape — "donor X bought work W at auction for $A, then donated W to museum Y in year T+1 claiming $B FMV (B >> A)" — requires a per-work auction comparable that this v1 does not have. Today's signal is a **portfolio-pattern flag** (volume × market-volatility × year-clustering), not per-work overstatement confirmation. See `connectors_to_add.md` for the next-step roadmap.
