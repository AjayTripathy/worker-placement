# art_donation_fraud — v1 analysis

## How the v1 pipeline operates

The vertical implements one R/f/M triple end-to-end (constrained by available M-sources):

- **R (claim):** the donor's claimed fair market value on Form 8283. Form 8283 is **not public**. The v1 infers at the cohort level — we observe museum acquisition records (which name the donor and the work) and apply a structural fraud-pattern rule against the donor's portfolio, not against per-work claimed value.
- **f (relationship):** IRC §170(e)(1)(A) + Treas. Reg. §1.170A-13(c). Claimed FMV must equal what a willing buyer would pay in the regular market; auction comparables are the regulatory benchmark.
- **M (observed):** Met + MoMA bulk collection CSVs (free, GitHub-hosted, ~390MB total). Records include accession year, credit line ("Gift of [donor], [year]"), title, artist, classification, department.

Stage 5 (gap detection) is collapsed into the cohort runner because the R-side is not per-work observable. Stage 6 (rule application) computes per-donor portfolio features (volume, classification mix, year-clustering, museum spread) and applies `AUCTION_TO_DONATION_MATCH` to flag high-risk archetypes.

The compiled `AUCTION_TO_DONATION_MATCH` rule fires when a donor's portfolio shows ≥2 of:
- ≥25 total works (high-volume)
- ≥50% in market-volatile departments (Modern/Contemporary Art, European Paintings, etc.)
- ≥60% of works donated in a single tax year with ≥10 works total (bunching pattern)
- ≥100 works (portfolio-scale)

The second rule, `EARLY_DEACCESSION_RECAPTURE` (IRC §170(e)(7)), is declared but `implementation=None` — requires a museum deaccession connector that this v1 does not have.

## What the v1 found

- 1,295 distinct normalized donors across Met + MoMA gifts since 2010
- 15,936 high-value-classification gift records in scope
- 77 donors flagged (5.9% of cohort) representing 9,548 works
- 4 donors fall in the "highest-risk archetype" (medium-volume + market-volatile + clustered)
- Top flagged-donor patterns:
  - Massive single-year bequests: Phyllis Massar (1,338 prints, all 2012), Herbert Mitchell (620 works, 78% in 2015), Charles Wrightsman (196 works, 90% in 2019)
  - High-volatility concentrated: Patricia Phelps de Cisneros (167 modern/contemp works, 58% in 2016)
  - Corporate gifts: AXA Equitable (29 modern/contemp works, 100% in 2016 — corporate deaccession pattern)
  - Foundation gifts: Souls Grown Deep Foundation, Roy Lichtenstein Foundation (estate-driven)

## Layer 3 transfer assessment

Brief read on each Layer 3 rule for this vertical (full per-rule write-up in `methodology_audit.md`).

- **Rule 1 (read the notes):** strong transfer. The "notes" here are the museum's credit-line metadata and the donation press releases. We currently parse credit lines; we don't yet parse museum press releases (which sometimes disclose value).
- **Rule 2 (coverage assessment):** strong transfer. Met + MoMA cover ~30% of the major-donor art philanthropy universe by dollar value. Whitney + Guggenheim + Art Institute + Boston MFA + LACMA + Getty + Philadelphia MFA would cover most of the rest. See `coverage_assessment.md`.
- **Rule 3 (divergence ≠ scope):** strong transfer. The one f we currently apply (auction-to-donation match) catches one shape. Sibling triples in `candidate_triples.md`.
- **Rule 4 (subagent firewall):** marginal transfer. No scored cohort with known outcomes exists yet (no tax-court case database wired). Becomes relevant if/when we want to backtest against known IRS Art Advisory Panel reductions or §170(e)(7) recapture filings.
- **Rule 5 (stock-for-services):** does not transfer directly. No equity-payable dynamic in personal charitable contributions.
- **Rule 6 (hindsight calibration):** moderate transfer. The threshold values in the rule (≥25 works, ≥50% high-vol, ≥60% cluster) are author-declared, not tuned. No held-out cohort with known outcomes to calibrate against.

## Single highest-leverage change

The auction-comparable connector (Artnet / Artprice / MutualArt) is the unambiguous next step. It converts every "donor X gave Y works in single year" pattern from a structural flag into a per-work overstatement measurement. Without it, the v1 produces sorted-by-risk donor lists but cannot confirm any individual fraud. With it, the same cohort runner produces per-work FMV-vs-comparable gap dollar values.

The next-cheapest leverage is broader museum coverage — Whitney, Guggenheim, Art Institute Chicago, etc. all publish collection metadata in some form; scraping them adds the cross-museum donor view that would catch the institutional collectors who spread their gifts across multiple destinations.
