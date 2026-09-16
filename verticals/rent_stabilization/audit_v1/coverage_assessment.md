# Coverage Assessment — NYC Rent Stabilization M-sources

**What this document does:** enumerates which M-sources the framework actually queries, which actor / unit / building types each covers, and where the structural gaps are. Per Layer 3 discipline rule 2, "no signal" lines must be paired with coverage statements before they can be read as "no divergence."

---

## What's actually wired up

Inspected `/Users/ajay/exalted/signalos/verticals/rent_stabilization/sources/` and registry at `jurisdictions/nyc/registry.py:26`.

| Source code | Role | Live? | Coverage notes |
|---|---|---|---|
| `nyc_pluto.py` (Socrata `64uk-42ks`) | M (building characteristics → stabilization inference) | yes | Building-level only. Filters to `unitsres ≥ 6`, `bldgclass ∈ C0..C9 ∪ D0..D9`, `taxclass ∈ {2, 2A, 2B, 2C}` (`nyc_pluto.py:81-84`). Authority Tier 1 (gov primary), but inference layer is a heuristic. |
| `nyc_pluto.py` J-51 cross-join (Socrata `y7az-s7wc`) | M (active stabilization obligation) | yes | Window: `init_year + ex_years + 35 > current_year`. Authority Tier 1. Upgrades status to `j51_confirmed`, confidence to 1.0. |
| `nyc_streeteasy.py` | R-source for listings (the claim) | yes (with Cloudflare-fragile HTTP + Playwright fallback) | Authority Tier 4 (public web aggregator). Captures advertised rent, bedrooms, listing date. |
| `nyc_census_rents.py` (ACS B25031) | M (ZIP-level rent benchmarks) | yes | Authority Tier 2 (gov derived/aggregate). Marked `data_quality = "area_median"`. Useful for incentive estimation, not per-unit gap. |

That's three live data feeds, two of which (PLUTO and J-51) are actually independent M-sources of stabilization status. The listing data is R-side. ACS is a degraded M alternative when listings are absent.

**Single most important coverage finding:** for stabilization status itself, the framework has exactly **two** M-signals — PLUTO-vintage inference and J-51 cross-join. There is no DHCR / HCR signal. The actual unit-by-unit registration record (the Annual Apartment Registration filed by the owner) is the closest thing to ground truth and is not wired. Result: the entire pipeline relies on a building-level heuristic when a unit-level authoritative record exists and is FOIA / OPRA-able.

---

## Actor / unit / building coverage matrix

### Well-covered
- **Pre-1974 C/D-class multifamily ≥ 6 units in residential tax class 2x.** This is the modal RSL building. PLUTO sees them; vintage rule fires; confidence lands at 0.7-0.85.
- **Buildings with active J-51 obligations** that filed in `y7az-s7wc`. Status becomes `j51_confirmed`, confidence 1.0.
- **Manhattan / Brooklyn 1BR units listed on StreetEasy.** Listings are dense, refresh every 3 days per `cache_ttl_days`, and most rentals route through StreetEasy first.

### Partially covered
- **Owner-classification.** `_is_entity` (`nyc_pluto.py:58`) is a string-match on `LLC|INC|CORP|LTD|LP|TRUST|AUTHORITY|ASSOC|PARTNERS|REALTY`. Misses misspellings, foreign-language names, sole proprietors transacting via DBA, and trustees registered without a suffix. Catches the common case but leaks both directions.
- **Borough base rent.** `BASE_RENT_1969` is one number per borough (`rgb_schedule.py:115`-121). Bedroom count, building location within borough, original luxury status — all collapsed. Median 1BR in 1969 Crown Heights (~$105) is the same as median 1BR in 1969 Brooklyn Heights, which is implausible.
- **Vacancy-bonus / IAI history.** The single multiplier `1.5` (`jurisdictions/nyc/config.py:13`) stands in for 5+ decades of vacancy turnovers, allowed IAI, MCI, longevity, and (pre-HSTPA) high-rent vacancy. For a unit that has had 0 turnovers since 1974, 1.5× is generous; for one with 6 turnovers and a $40K kitchen-and-bath IAI in 2017, 1.5× is too tight.

### Structurally invisible to current M

1. **DHCR / HCR Annual Apartment Registration database.** Unit-level legal regulated rent, registration history per year, registered services, registered tenant name (redacted version is public via FOIL request). This is the authoritative R-side AND M-side simultaneously: the owner's annual registration *is* the legal rent of record. The framework cannot query it. Closing this gap is the rent-stab analogue of the L-4260 PTA log addition for property tax.

2. **J-51 expiration cohort.** Buildings whose J-51 abatement *just* expired but whose stabilization tail is still running (35-year tail per Roberts v. Tishman Speyer). The current `_load_j51_bbls` (`nyc_pluto.py:141`) tests `init_year + ex_years + 35 > current_year`, so it does include the tail in principle — but the *signaling* downstream collapses everything into binary `j51_confirmed`. A J-51 unit in the tail period is a higher-fraud-risk cohort than one in the active abatement period (owners are often surprised by the residual obligation; informal deregulations are common).

3. **421-a buildings.** Models declare `"421a_confirmed"` as a status (`models.py:21`) and scorer rewards it (`scorer.py:35`), but no source connector populates it. Dead code path.

4. **Section 8 / HCV voucher tenancies.** A unit may be both stabilized AND voucher-subsidized; HUD HAP contract rent and the legal regulated rent are independent ceilings. Listing-side data won't capture voucher tenancies because they're matched off-platform.

5. **SCRIE / DRIE participants.** Senior Citizen Rent Increase Exemption / Disability Rent Increase Exemption freezes the legal regulated rent at the participant's anniversary level for the duration of program eligibility. NYC HPD publishes participant-count data by community district; per-unit data is not public. An HPD SCRIE/DRIE roster cross-join would catch a fraud pattern: collecting program credit while charging a non-frozen successor tenant.

6. **Rent-controlled (not -stabilized) holdover units.** Pre-1947 buildings with a continuously-resident pre-1971 tenant are under Rent Control (different statute, different ceiling), not RSL. PLUTO vintage rule lumps them into the stabilization-likely cohort. False-positive risk at the elderly / long-tenured edge.

7. **Condo / co-op buildings with leftover stabilized units.** When a building converted under a non-eviction plan, holdover stabilized tenants remain stabilized while neighboring units are unregulated condos. `bldgclass` filtering catches some (R-class units excluded) but mid-conversion buildings carry mixed status, invisible at the building level.

8. **Off-platform listings.** Craigslist, broker-only walk-ins, by-owner deals, WhatsApp groups for diaspora communities. Particularly relevant for outer-borough immigrant-tenant markets where StreetEasy penetration is low. ZIP-level ACS partially compensates but cannot identify a specific unit's overcharge.

9. **Pre-stabilization private deals.** Cash discounts, key money, pet fees in lieu of rent — payments outside the listed-rent number. The listing M understates the true R; the framework computes a smaller overcharge than reality.

10. **Building-wide registration filings (DOB Real Property Income & Expense / RPIE).** DOF requires owners of income-producing properties (≥10 units) to file annual income/expense statements. RPIE-reported rent is a separate independent observation of effective rent and could anchor the calibration of `vacancy_bonus_factor` per-building rather than globally. Not wired.

---

## "We found nothing wrong" honesty check

Lines from current framework output that would mislead if read as "no overcharge":

- **Building filtered out in PLUTO.** A 5-unit pre-war Brooklyn building (sub-threshold for `unitsres >= 6`) returns no `stabilization` record. The gap function exits at `gap.py:60` (`if building is None`) with no signal. This is "no coverage of this unit type," not "no overcharge."
- **`stabilization_confidence < 0.4`** (`gap.py:63`). PLUTO sees a postwar building with `bldgclass = D7` and `unitsres = 8`; confidence stays at 0.5 base + 0.1 D-class = 0.6, but if vintage > 1974, the +0.2 vintage bump is not applied and you stay at 0.6. Edge cases drop below 0.4 silently. Output is `None`. This is "we don't know," not "compliant."
- **`raw_gap < min_rent_delta` (`gap.py:80`).** Gap of $400/mo on a $1,000/mo legal max (40% overcharge) is suppressed because it's under the absolute $500 floor. Honest negative? No — that's a real and proportionally large overcharge that the framework mutes.
- **No listings returned by StreetEasy.** Cloudflare blocked, address parse failed, building genuinely vacant, listings only on Craigslist — all four indistinguishable. Output is `None` from `gap.py:67`.
- **`status = "likely"` with confidence 0.5.** Almost every building Output that fires under this status carries the "inferred_stabilization" flag (`gap.py:86`) and is discounted by the scorer; this discount is correct epistemically but conflates "we're unsure about stabilization" with "we're sure about no-overcharge."

---

## Concrete sources the framework should add

Analogous to USPTO ODP closing a gap in public-co backtests; or L-4260 PTA log for property tax:

| Gap | M-source to add | Authority tier | Access | Closes |
|---|---|---|---|---|
| Unit-level legal regulated rent | DHCR / HCR Annual Apartment Registration (FOIL-able by building or by tenant request) | Tier 1 | FOIL; partial bulk via FOIL → CSV | Replaces borough estimate with registered base rent for every unit ever registered |
| J-51 tail-period cohort | Same J-51 dataset (`y7az-s7wc`) but with explicit "in tail" sub-flag | Tier 1 | Free (already wired) | Tags higher-fraud-risk J-51 cohort separately |
| 421-a obligation | DOF 421-a benefits dataset (Socrata) | Tier 1 | Free | Activates dead `421a_confirmed` code path |
| RPIE-reported actual rent | DOF Real Property Income & Expense filings | Tier 1 | FOIL (some bulk releases exist) | Per-building calibration of vacancy_bonus_factor |
| SCRIE / DRIE roster | HPD SCRIE/DRIE participant register | Tier 1 | FOIL | Catches benefit-fraud pattern |
| HPD building registration | HPD HPDONLINE building records | Tier 1 | Free Socrata | Cross-references owner identity, registers managing agent |
| Building-wide rent reduction orders | DHCR rent reduction order register (issued on tenant complaint) | Tier 1 | FOIL | Past adverse outcomes against the same owner — strong calibration prior |
| ACRIS deed history | NYC ACRIS recorder | Tier 1 | Free Socrata | Owner-identity entity resolution; flips on deed transfer (potential vacancy bonus moment under pre-HSTPA rules) |
| Off-platform listings | Craigslist NYC apartments scrape | Tier 4 | Free | Coverage of off-StreetEasy markets |

The DHCR Annual Apartment Registration is the highest-ROI add by far. It alone would convert the vertical from a heuristic-leads engine into a unit-level overcharge measurement engine, and would supply ground truth for calibrating the vacancy/IAI multiplier (Rule 6) at the same time.
