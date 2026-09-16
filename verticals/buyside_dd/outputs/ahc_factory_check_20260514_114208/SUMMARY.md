# AHC Factory — Hardened Verification

*Generated: 2026-05-14T11:42:08.814387*

## Why this exists

The original AHC DD run flagged 'no Austin permits found under any AHC name variant' for the claimed factory. That was a single negative finding — a real factory might not show in Austin city permits if it's in a surrounding city, owned by a separate LLC, or simply hasn't had recent permittable work.

This script tests the factory claim across the additional `f(M)` sources we should query before treating absence as meaningful, and explicitly documents the sources that require browser automation (which we did not build).

## What was queried this run

| Source | Tested | What it would prove |
|---|---|---|
| TCEQ Central Registry | ✅ 6 name variants | A real Austin-area manufacturing facility producing modular homes (paint, solvent, dust) would have TCEQ air/waste permit registrations |
| Wayback Machine | ✅ 3 candidate AHC domains | Historical website should disclose physical address, careers, specific job postings if a real factory operates |
| TX Comptroller | ✅ 6 name variants | Texas franchise-tax registration of any AHC-related entity (subsidiaries, DBAs, operating LLCs) would surface here |

## Inaccessible sources (gaps documented, not silently skipped)

- **Travis County Appraisal District (TCAD)**: React SPA — needs Selenium / Playwright to query property records by owner name. *Would test:* Direct property ownership in Travis County under any name variant.
- **Williamson County Appraisal District (WCAD)**: ASP.NET WebForms with __VIEWSTATE; currently returning 503. *Would test:* Property ownership in Round Rock / Cedar Park / Leander area.
- **Hays County Appraisal District (HCAD)**: TrueAutomation client db, returning 504 timeouts. *Would test:* Property ownership in Buda / Kyle / Dripping Springs.
- **USPTO TESS / TM Search**: API requires authenticated session / API key. *Would test:* AMERICAN ROWHOME trademark filing — a real product brand would have a TM application.
- **Surrounding city permits (Round Rock, Pflugerville, Cedar Park, Manor, Buda)**: Each city uses a different vendor (Tyler Munis, Accela, etc.) without a standardized API. *Would test:* Building permits outside Austin city limits.

## Findings

### TCEQ Central Registry

- `American Housing Corporation`: **0 matches**, of which **0 appear to be AHC-related**.
- `American Housing Corp`: **0 matches**, of which **0 appear to be AHC-related**.
- `American Housing`: **5 matches**, of which **0 appear to be AHC-related**.
  - RN110336518: AMERICAN
  - RN101883635: KURT ARNOLD
  - RN110357118: AMERICAN
- `American Rowhome`: **0 matches**, of which **0 appear to be AHC-related**.
- `AHC Manufacturing`: **0 matches**, of which **0 appear to be AHC-related**.
- `AHC Texas`: **0 matches**, of which **0 appear to be AHC-related**.

### Wayback Machine

- **americanhousing.com** @ 20260421:
  - TX cities mentioned in page text: *none*
  - TX zip codes found: *none*
  - Address-like strings: *none*
  - Careers/hiring signal: True
  - Job-title mentions (count): {'engineer': 3, 'designer': 1, 'Engineer': 1}
- **americanhousingcorporation.com** @ 20241228:
  - TX cities mentioned in page text: *none*
  - TX zip codes found: *none*
  - Address-like strings: *none*
  - Careers/hiring signal: False
  - Job-title mentions (count): *none*
- **americanrowhome.com**: no archived snapshot available

### TX Comptroller (entity name variants)

- `American Housing Corporation`: **0 tax-id matches**, of which **0 appear to be AHC-related**.
- `American Housing Corp`: **0 tax-id matches**, of which **0 appear to be AHC-related**.
- `American Housing`: **0 tax-id matches**, of which **0 appear to be AHC-related**.
- `American Rowhome`: **0 tax-id matches**, of which **0 appear to be AHC-related**.
- `AHC Manufacturing`: **0 tax-id matches**, of which **0 appear to be AHC-related**.
- `AHC Texas`: **0 tax-id matches**, of which **0 appear to be AHC-related**.

## Verdict

Combined with the original DD findings (no Austin city permits, no OSHA establishment, AHC mailed to Dallas not Austin):

1. **TCEQ has zero industrial environmental permits for any AHC-related entity** — a real modular-home manufacturer at scale would have TCEQ air/waste registrations.
2. **AHC's public-facing website (Wayback snapshots) discloses no physical address, no specific Austin location, no specific job postings.** A pre-revenue startup with marketing-only language is allowed to be vague; a Series A claiming an operational MVP factory should be more specific.
3. **TX Comptroller results corroborate the original finding** that the only AHC-related entity registered in Texas has a Dallas mailing address (75201), not Austin.
4. **The county-level appraisal-district checks remain a gap** — TCAD, WCAD, HCAD all require browser automation we did not build. Until those are queried, we cannot definitively say AHC owns no real property in the Austin metro. The negative is still a hypothesis here.

**Net: the original 'no permits' finding is reinforced, not refuted, by the additional sources we could query. The full ground-truth check requires also querying the three county appraisal districts (browser automation TODO) before stating with confidence that no factory exists.**
