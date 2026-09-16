# Rent Stabilization Audit v1 — Analysis

Methodology audit of the `rent_stabilization` vertical against the post-improvement Layer 3 operational-discipline rules from `signalos/ARCHITECTURE.md`. Structural, not blinded data run (per `BRIEF.md`).

---

## How the framework currently operates

The vertical implements one R/f/M triple, end to end:

- **R (claim):** the asking rent on an active rental listing — the landlord's public assertion that this unit can lawfully be let at this price. Source = StreetEasy listing scrape (`sources/nyc_streeteasy.py`) or, in degraded mode, ZIP-level Census ACS B25031 medians (`sources/nyc_census_rents.py`).
- **f (relationship):** under NYC RSL §26-510, the legal maximum stabilized rent equals `base_rent × cumulative_RGB_factor × vacancy_bonus_factor`. Implemented in `rgb_schedule.py:88` (`max_legal_rent`).
- **M (observed):** building-level stabilization status, vintage, and unit count from PLUTO (`sources/nyc_pluto.py`), enriched with an active-J-51 cross-join from Socrata dataset `y7az-s7wc`.

Stage 5 lives in `gap.py:39` (`RentStabilizationGapFunction`). Inputs: a PLUTO-derived `StabilizedBuilding` plus listing records. Outputs: a `GapResult` whose `raw_gap = listed_rent − max_legal_rent`. Severity tiering happens in `scorer.py:21` and bakes in stabilization-confidence, gap magnitude, and an `owner_is_entity` flag.

Three SignalRules are declared in `rules/__init__.py`: `RSL_OVERCHARGE` (compiled, fires on positive gap), `J51_OBLIGATION` (LLM-only, no compiled implementation), `HSTPA_LOCK` (`detectable=False`). Of those, only `RSL_OVERCHARGE` is wired to compiled code at `rules/rsl_overcharge.py:8`.

The whole pipeline is one f against one M-source family (PLUTO + listings), with a hard-coded conservative `vacancy_bonus_factor = 1.5` (`jurisdictions/nyc/config.py:13`) and a $500 minimum monthly delta floor.

## Worked illustration — fabricated structural example

Consider a unit at fabricated BBL `3008470042` (Brooklyn, Crown Heights), a 24-unit pre-war C4-class building completed 1928. PLUTO query yields:
- `unitsres = 24`, `bldgclass = "C4"`, `taxclass = "2"`, `year_built = 1928`, `borough = "brooklyn"`
- Owner: "1234 EASTERN PKWY LLC" → `owner_is_entity = True`
- Stabilization confidence: 0.5 (base) + 0.2 (pre-1974) + 0.1 (C-class) + 0.1 (>=20 units) = 0.85, capped (`nyc_pluto.py:88`-95)
- Status: `"likely"` (no J-51 hit)
- Borough base rent estimate: `$105` (1969 Brooklyn baseline, `rgb_schedule.py:117`)

Cumulative RGB factor 1969→2026 ≈ 5.85. Apply `vacancy_bonus_factor = 1.5` → estimated max legal rent ≈ `$105 × 5.85 × 1.5 ≈ $921/mo` for the borough-median 1BR.

Asking rent on StreetEasy: $3,200/mo for a 1BR. Raw gap = $2,279/mo. Annual exposure per `scorer.py` = $27,348. Severity score from `scorer.py:21`: stabilization_confidence (0.85 → +25) + gap >100% (+30) + owner_is_entity (+10) = **65 → "high"**.

This is the framework working as designed: a building-level inference that hits the $500 floor, fires `RSL_OVERCHARGE`, and gets surfaced as a lead. Note what it cannot say:
- Whether *this specific unit* was ever stabilized (PLUTO is building-level, not unit-level).
- Whether the actual DHCR-registered base rent is closer to $300 (legal max ≈ $2,634, gap collapses) or $90 (gap widens).
- Whether the building has an active or expired J-51 abatement that obligates stabilization independently of vintage.
- Whether the listing is a "preferential rent" the owner intends to revert; an unlawful Class A→short-term-rental conversion; or a deregulated unit under a contested high-rent vacancy claim.

Real-shape signal, "lead for DHCR inquiry" tier, which the `gap.py:14-18` docstring honestly admits.

## Bottom line — which Layer 3 rules surface real changes

- **Rule 1 (read the notes):** strong transfer. The framework reads PLUTO + listings and stops. It never touches the actual DHCR Annual Apartment Registration record — the unit-level legal regulated rent, registration history, registered services. Adding HCR registration converts nearly every building-level *estimate* into a unit-level *measurement*. This is the rent-stab analogue of the public-co Note 15 finding.
- **Rule 2 (coverage assessment):** strong transfer. PLUTO covers ≥6 units, C/D class, taxclass 2x. Misses 4-5 unit buildings under hotel-class stabilization, J-51 buildings whose vintage doesn't trigger inclusion, condo-converted buildings carrying stabilized leftover units, SCRIE/DRIE participants, rent-controlled holdovers vs rent-stabilized; unit-level base-rent registration history at HCR. Many "no overcharge detected" outputs are hidden coverage gaps.
- **Rule 3 (divergence ≠ solvency/scope):** strongest transfer. The current f catches one shape — listed rent above legal max. It misses J-51-while-charging-market (Roberts v. Tishman Speyer territory, declared in `rules/__init__.py:21` but never implemented in compiled f), IAI inflation, preferential-rent rider misuse, unlawful deregulation-on-vacancy claims, Section 8 / SCRIE double-claiming, pied-à-terre and STR violations. Sibling triples in `candidate_triples.md`.
- **Rule 4 (subagent firewall):** marginal transfer. No scored cohort exists yet. Becomes relevant when a portfolio screen ranks N landlords and the analyst is already aware of which owners are under HCR enforcement.
- **Rule 5 (stock-for-services):** does not transfer. No equity-payable dynamic in residential rent.
- **Rule 6 (hindsight calibration):** strong transfer. The `vacancy_bonus_factor = 1.5` and `min_rent_delta = $500` are not tuned on observed outcomes — they are author-declared "conservative" defaults. Honest about being an estimate, but hides an uncalibrated precision-recall tradeoff that probably costs recall on Manhattan high-rent buildings and precision in outer-borough small-multifamily.

Single highest-leverage change: wire DHCR Annual Apartment Registration as a unit-level M-source. Simultaneously addresses Rule 1 (notes) and Rule 6 (calibration) by replacing borough-baseline estimates with measured base rents.
