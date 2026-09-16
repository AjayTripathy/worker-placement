# AHC Factory — Address-Resolved Check (4422 Supply Ct, Austin, TX 78744)

*Generated: 2026-05-14 | Updates the prior `ahc_factory_check_*` runs after the user supplied a specific factory address*

---

## Headline

**The original DD finding "no Austin permits under AHC name" was a false negative.** When queried by **address** (not by AHC entity name) at the user-supplied address `4422 Supply Ct, Austin, TX 78744`, **12 building permits surface** — exactly the false-negative path I flagged in the framework analysis: tenants don't file permits, GCs and property owners do.

The new question is not "does the factory exist?" but "is the factory consistent with the operational scale claimed?"

| | |
|---|---|
| Address | 4422 Supply Ct, Austin, TX 78744 (southeast Austin, real industrial corridor near Bergstrom) |
| Property owner | **IGX Burleson Park, LLC** (filed 2017 building permit) — TX entity 32056072567, mailed to Bandera TX 78003 |
| Originally built | 2016–2017 (shell office/warehouse, multiple GCs) |
| First tenant finish-out | 2017–2018 |
| Latest activity | **2025-09 to 2025-10: 600-amp electrical service upgrade** filed by CM Constructors |
| Prior tenant per multiple business directories | **Evolution Salt Co.** (Himalayan salt products) — still listed on Superpages, Cortera, Bizapedia, ChamberofCommerce |

---

## Permit timeline at 4422 Supply Ct (Austin Open Data, 12 records)

```
2016-05-16  → 2017-03-09   New Construction of Shell Office/Warehouse Building (5 permits, multiple GCs)
2017-08-29  → 2018-02-22   Tenant finish-out to create office/warehouse (5 permits)
                           — IGX Burleson Park, LLC listed as contractor on building permit
2025-09-08  → 2025-10-24   Upgrade existing service to 600 amp (Building + Electrical)
                           — CM Constructors *MAIN* (Mark McDonald, real Austin commercial GC)
```

**The 2025-09 600-amp service upgrade is consistent with AHC's claim that an "MVP factory was built Q3 2025."** A 600A 3-phase service is industrial-grade (residential is typically 200A). It supports significant equipment loads — CNC machines, welding rigs, painting equipment, conveyor systems.

CM Constructors is a real Austin commercial GC — their other 2024-2026 Austin permits include hospital remodels at Mueller Blvd (X-Ray, MRI, Fluoro room installs), office finish-outs at Mopac/Arboretum, and research-services remodels. They are not a fly-by-night entity.

---

## What this confirms

1. ✅ **The address is a real industrial property** — built 2016, in continuous tenant use since 2017
2. ✅ **A tenant build-out happened Q3-Q4 2025** that's timing-consistent with AHC's claimed MVP-factory completion
3. ✅ **The 600A electrical capacity is industrial-grade** and supports the kind of equipment claimed
4. ✅ **The original "no AHC name in Austin permits" finding was a false negative** — caused by querying by entity name when the permit applicant is always the GC or property owner. This is the textbook false-negative path I documented earlier.

## What remains uncertain (can't be confirmed from these sources alone)

1. ⚠️ **No 2025 permits show major construction, loading-dock work, fire-suppression upgrades, or spray-booth/finishing permits.** A real factory producing 36 modular homes/yr at scale would typically also need these. The single 600A electrical upgrade may be sufficient for an MVP-stage operation but is thin for a Series-A pitch claim of operational production capacity.
2. ⚠️ **Evolution Salt Co. is still listed as the address tenant in multiple business directories** (Superpages, Cortera, Bizapedia, ChamberofCommerce). Could be (a) stale directory data — directories update slowly, (b) Evolution Salt moved out and AHC took over, or (c) shared / co-tenant occupancy.
3. ⚠️ **The lease/ownership relationship between AHC and IGX Burleson Park is not in the permit data** — would need to see lease agreement or county clerk DBA filings.
4. ⚠️ **The actual square footage AHC occupies is unknown** without TCAD property lookup (still requires browser automation or PDF report download).
5. ⚠️ **TCEQ still has zero AHC-related industrial environmental permits.** A modular-home factory doing finishing work (paint, primer, solvents) usually needs TCEQ air permits. Two reads: (a) MVP-stage operations may be below permit thresholds, or (b) the finishing work isn't actually happening at this site.

---

## Updated DD verdict

The original DD report's claim that the **factory may not exist** was overstated; the address resolves to a real industrial property with timing-consistent build-out activity in Q3-Q4 2025. The factory **probably exists in some form**.

But the **scale and operational status remain unverified.** The single 600A electrical permit is much smaller than what a fully-operational 36-home/yr modular factory would typically generate in permit volume. Evolution Salt Co. remains the directory-listed tenant.

**For the partner email, the framing should change from:**
> "Zero permits found — factory may not exist"

**to:**
> "Address resolves to real industrial property at 4422 Supply Ct (owner IGX Burleson Park, LLC). A 600A electrical service upgrade was completed by CM Constructors in Oct 2025, timing-consistent with AHC's claimed MVP factory completion. However: (a) only one permit set for the build-out, with no loading-dock, fire-suppression, or finishing-work permits typical of a modular-home factory, (b) the property's prior tenant (Evolution Salt Co.) is still listed in business directories, (c) AHC has zero TCEQ industrial environmental permits. **Recommendation: ask AHC for a lease copy + Certificate of Occupancy + tour of the operational floor + production photos with verifiable timestamps before underwriting the production-capacity claim.**"

---

## Methodology lesson

The hardened-check framework needs an explicit `address-resolved` step. When an issuer provides a specific property address, queries should ALWAYS be:

1. **Address-keyed permit search** (not name-keyed). Permits are filed by GCs and property owners, not tenants — so name-based queries miss tenant operations entirely.
2. **Property ownership lookup** (via county appraisal district or county clerk records).
3. **Tenant verification** via business directory cross-reference (Yelp, Yellow Pages, Cortera, ChamberofCommerce) — not authoritative but signals previous occupancy.
4. **Web search for the address** (DuckDuckGo / Google) — surfaces commercial real estate listings, news, business directories.
5. **Satellite imagery** of the address at multiple time points to verify recent build-out activity visible from above (loading bays added, equipment outside, etc.).
6. **Utility connection records** if available — large commercial electric/gas hookups are often in city/county open data.

Without an address, our framework can only test entity-name presence in registries — which is necessary but not sufficient. With an address, we get ground-truth signal.

---

## Files updated

- `verticals/buyside_dd/outputs/ahc_factory_check_address_resolved.md` (this document)
- `verticals/buyside_dd/ahc_factory_hardened_check.py` (still useful for entity-name baseline; should add an `address` mode in next iteration)
