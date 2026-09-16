# buyside_dd — Tech Debt

## TD-1 — Satellite imagery: parcel-level tasking + commercial license [enhancement for the carbon_mapper connector]

**What ships now (2026-06-07).** `connectors/carbon_mapper.py` is live and wired into the
atlas as a **Tier-1 `environmental_status`** source (co-dispatches with EPA Envirofacts). It
queries the **public** Carbon Mapper plume catalog (Planet Tanager-1 `tan`, NASA EMIT `emi`,
GAO/AVIRIS aircraft) by lat/lon or geocoded address and returns instrument-measured
methane/CO2 super-emitter observations. Validated live: discriminates an active O&G basin
(97 super-emitters) from a clean control (0), lifts a weakly-sourced environmental finding
0.30 -> 1.00 via the comparator's corroboration, and refutes a marketed "no methane" claim at
confidence 1.00. **Free for non-commercial / research use.**

**Two gaps before productizing:**
1. **Coverage is opportunistic, not on-demand.** The free catalog only has plumes where a
   satellite/aircraft happened to observe AND a plume was present. Absence of a plume is NOT
   proof of no emissions (could be no overpass, or sub-detection-threshold). For *facility-level,
   point-in-time* verification ("is THIS parcel emitting THIS quarter?") you need **tasked**
   acquisition — Planet/Carbon Mapper **commercial Tanager tasking** (paid). The connector
   already accepts `radius_km~1` for parcel scope; it just can't guarantee a recent overpass on
   the free tier.
2. **Commercial-use license.** Carbon Mapper data is published for non-commercial use; selling a
   product on top of it (or Planet's broader PlanetScope/SkySat optical for buildout/facility
   verification) needs a **Planet / Carbon Mapper commercial license**. Same theme as the muni
   CUSIP-feed wall: free data -> framework + demo; production -> paid feed.

**Optical buildout — FREE tier SHIPPED (2026-06-07), paid tier stubbed.**
`connectors/sentinel2_buildout.py` now provides the **general** "is the parcel physically being
built / active?" sensor at **$0** using ESA Sentinel-2 L2A (10-20 m) via the public Element84
Earth Search STAC + open `sentinel-cogs` bucket (no auth). Signal = NDBI(built-up) + NDVI change,
baseline vs recent, over a parcel window. Live-validated: Teravalis AZ new MPC (NDBI +0.093 /
NDVI -0.175) and Hyundai Metaplant GA (NDBI +0.068 / NDVI -0.164) both fired BUILDOUT; established
Phoenix residential control stayed flat (NDBI -0.010). Registered Tier-2 `construction_activity`.
The PAID escalation is `connectors/planet_imagery.py` (PlanetScope ~3 m / SkySat ~50 cm), same
output contract, fails cleanly with AUTH until `PL_API_KEY` + a commercial license are wired.
Cost: ~$2-5k/diligence event (SkySat tasking, €4,500 min/order, 25 km² min AOI) or ~$10-50k/yr
(PlanetScope AOI subscription). Use the free 10 m tier for routine screening; escalate to paid
high-res only when a specific deal needs to resolve individual structures/equipment.
Limits of the free tier: 10 m can't resolve single buildings; needs a TRUE pre-construction
baseline (a parcel already built at baseline reads "stable" — several CA CFD points did); and
desert→concrete can be ambiguous on NDBI alone (NDVI-drop corroboration handles it). Highest-value
targets unchanged: muni land-secured/CFD buildout vs. the OS absorption schedule (feed
`cdiac_default_draw`), and buyside China/greenfield-facility verification (ramp-dump archetype).

**Owner:** unassigned. **Priority:** LOW for #1/#2 (the free methane connector is useful today for
emitting-asset DD + ESG-honesty); MEDIUM for the optical connector (unlocks the broad buildout
product story).

---
*Logged 2026-06-07. See: `connectors/carbon_mapper.py`, `validate_carbon_mapper.py`,
`source_atlas.py` (carbon_mapper MSource + ATTRIBUTE_ALIASES).*
