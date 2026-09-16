# Candidate Sibling R/f/M Triples — NYC Rent Stabilization

Per Layer 3 Rule 3 (divergence ≠ scope), the current vertical wires one f (RSL §26-510 overcharge) against one M-family (PLUTO + listings). The candidates below are sibling triples within the rent-stab vertical — same domain, different fraud predicate, different f, mostly different M. Analogous to PRE-on-LLC for property tax: each is a separate R-claim with a separate f relationship that the existing M-side either already covers or could cover with a small connector add.

Ranked by **build cost ascending** then **ROI descending**.

---

## 1. J-51 obligation while listing at market rate (Roberts v. Tishman Speyer)

- **R:** asking rent on a listing for a unit in a J-51-confirmed building.
- **f:** NYC Admin Code §11-243 + Roberts v. Tishman Speyer (2009): all units in a J-51 building must remain stabilized for the benefit period + 35 years; deregulation during this window is void. Therefore listed rent must be ≤ legal stabilized max.
- **M:** PLUTO + J-51 dataset (`y7az-s7wc`, already wired) + StreetEasy listings (already wired).
- **Population:** thousands of J-51 buildings citywide; tail-period cohort (post-active but pre-35-year-end) likely 5K-10K buildings, ~50K-100K units.
- **Dollar exposure:** if even 5% of tail-period units are listed above the stabilized max with $1K/mo gap → $30M-60M/yr aggregate tenant harm.
- **Build cost:** **lowest**. Implement a compiled `J51_OBLIGATION` rule (currently `implementation=None` in `rules/__init__.py:32`). Reuses existing PLUTO + J-51 + listing pipeline. ~50 lines of f-library code, no new connector. Distinguishes from RSL_OVERCHARGE in that confidence is 1.0 (not vintage-inferred) and the legal basis is statutory + case-law specific.

---

## 2. HSTPA-lock void deregulation (post-2019)

- **R:** asking rent on a listing for a unit that was registered with DHCR as stabilized as of June 14, 2019 but is now being marketed as unregulated.
- **f:** HSTPA / RSL §26-511 as amended by L. 2019 ch. 36: any post-2019 deregulation without a lawful basis (co-op conversion, owner occupancy with proper notice) is void ab initio. Therefore the unit remains stabilized and listed rent must be ≤ legal stabilized max.
- **M:** DHCR Annual Apartment Registration (NOT yet wired) cross-joined to current listings.
- **Population:** estimated 10K-50K units citywide that fell off DHCR registration after 2019 without recorded lawful basis.
- **Dollar exposure:** rough order $50M-200M/yr — these are typically Manhattan / brownstone Brooklyn units where the deregulation gap is largest.
- **Build cost:** **medium**. Requires DHCR Annual Apartment Registration connector (FOIL-able, partial bulk releases). Once that connector exists, the f is straightforward year-over-year continuity check on the registration table. Same connector unlocks several other triples in this list (so amortized cost is favorable).

---

## 3. Preferential rent snap-back

- **R:** registered legal regulated rent jumps materially between consecutive years on the same unit, where prior years carried a "preferential rent" rider.
- **f:** RSL §26-511(c)(14) post-HSTPA: preferential rent in effect at lease renewal must be carried forward; legal regulated rent cannot snap back to the higher number for the duration of tenancy.
- **M:** DHCR Annual Apartment Registration history per unit (NOT yet wired).
- **Population:** all units with preferential rent riders pre-2019 — likely 100K+ unit-years.
- **Dollar exposure:** $20M-100M/yr if 10K snap-backs averaging $200/mo.
- **Build cost:** **medium-low.** Same connector as #2; f is consecutive-year delta check. Once DHCR registration exists, this rule is ~30 lines.

---

## 4. IAI (Individual Apartment Improvement) inflation

- **R:** owner-claimed IAI on a DHCR registration justifying a base-rent increase.
- **f:** RSL §26-511(c)(13) and DHCR Operational Bulletin: IAI must be substantiated by permits, paid invoices, and physical work; allowable rent increase = (cost / 60) post-HSTPA for buildings with 35+ units, (cost / 40) for smaller. Therefore claimed IAI must trace to DOB permits and contractor records.
- **M:** DHCR registration (IAI claim) + NYC DOB permits (`Approved Permits` Socrata dataset, `ipu4-2q9a`) + DOB Job Application filings.
- **Population:** ~200K+ post-vacancy IAI claims since the 1990s; non-trivial fraction lack any DOB permit trace.
- **Dollar exposure:** very large — single-unit IAI fraud often inflates legal rent by $500-$2,000/mo permanently. Aggregate tenant harm probably 9-figures.
- **Build cost:** **medium-high.** Requires DHCR registration connector AND a DOB permit connector AND fuzzy address-matching across the two. The f itself is a "claimed cost vs permit-implied scope" comparison that needs adjudication rules (which permit categories count as IAI-substantiating).

---

## 5. Pied-à-terre / short-term-rental conversion of stabilized unit

- **R:** Airbnb / VRBO listing for a unit at a BBL whose corresponding apartment is registered as stabilized with DHCR.
- **f:** RSL + NYC Multiple Dwelling Law §4(8): Class A multiple dwellings (where stabilized units sit) cannot be rented for fewer than 30 days without owner present. STR rental of a stabilized unit also breaks the owner's stabilization registration accuracy (registered tenant ≠ STR guests).
- **M:** Airbnb scrape (Inside Airbnb publishes city-level data quarterly) joined to BBL via address geocoding; DHCR registration (NOT yet wired).
- **Population:** 5K-15K STR-listed units citywide (per Inside Airbnb), unknown overlap with stabilized cohort.
- **Dollar exposure:** moderate — single-unit STR yields $30K-60K/yr revenue which is mostly removed from rent-regulated tenant supply.
- **Build cost:** **medium.** Inside Airbnb data is free. Address-geocoding to BBL is straightforward (NYC GeoSearch API). Cross-join to DHCR is the gating step.

---

## 6. SCRIE / DRIE benefit fraud

- **R:** owner files for SCRIE/DRIE tax abatement credit naming a unit + tenant; owner is supposed to freeze that tenant's rent at anniversary.
- **f:** NYC Admin Code §26-509 et seq.: SCRIE/DRIE freezes legal regulated rent at participant's anniversary level for program duration; owner receives tax abatement equal to frozen amount.
- **M:** HPD SCRIE/DRIE participant register + DHCR registration cross-check + StreetEasy listing for the same unit.
- **Population:** ~70K SCRIE + ~10K DRIE participants citywide. Fraud subset likely small (single-digit %) but per-unit harm is the abatement amount itself.
- **Dollar exposure:** lower aggregate than #1-#4 but very clean shape (binary fraud per unit).
- **Build cost:** **medium-high.** SCRIE/DRIE roster requires FOIL request. Listing cross-check uses existing pipeline.

---

## Cost-vs-ROI summary

| Rank | Triple | Build cost | $ exposure (annual rough order) | Notes |
|---|---|---|---|---|
| 1 | J-51 obligation enforcement | **lowest** (no new connector) | $30-60M | Just compile the existing SignalRule |
| 2 | HSTPA void deregulation | medium | $50-200M | Anchor connector for triples 3 & 4 |
| 3 | Preferential rent snap-back | medium-low (after #2) | $20-100M | Reuses #2's connector |
| 4 | IAI inflation | medium-high | 9-figures | Needs DOB cross-join in addition to DHCR |
| 5 | Pied-à-terre / STR | medium | moderate | Cross-domain (Airbnb + DHCR) |
| 6 | SCRIE/DRIE benefit fraud | medium-high | lower | FOIL-gated roster |

**Highest-ROI single move:** compile the J-51 obligation rule (#1) and ship the DHCR Annual Apartment Registration connector (gates #2-4). Same shape as the property-tax recommendation: one connector add unlocks an order of magnitude of additional fraud population that the existing M-side infrastructure can immediately query.
