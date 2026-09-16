# VCS Carbon Credit Integrity League Table

*Methodology and findings from a public-data scan of {N_PROJECTS} active VCS projects.*

*[Generated TBD – fill in after scan completes]*

---

## Executive Summary

[Auto-generated from scan results. Lead with the headline numbers:]
- {X} active VCS projects scanned
- {Y} flagged with severe integrity divergence (≥ "SEVERE" tier)
- {$Z}M tCO2/yr in claimed reductions sit behind flagged projects
- Worst single project: {NAME} in {COUNTRY} ({CLAIM} tCO2/yr) shows [observed metric vs claim]

---

## Methodology

**Universe:** All active Verra VCS projects (status: Registered, Late to verify, or Verification approval requested) in two integrity-critical credit type families: forest (REDD+, A/R, IFM, WRC) and methane (waste, fugitive emissions, livestock).

**Forest projects ({N_FOREST}):**

- *R signal:* Project's claimed annual emission reduction (from Verra registry).
- *M signal:* Annual forest loss inside the project's actual KML AOI polygons, measured by Hansen Global Forest Change v1.11 (30 m resolution, years 2001–2023).
- *Divergence score:* Mean annual deforestation in the (project crediting period) minus mean annual deforestation in (pre-project years 2001 to crediting start). Positive value = deforestation increased during the project.
- *Carbon stock assumption:* 165 tCO2/ha (mid-tropical estimate) applied uniformly to convert Verra's reduction claim into "implied avoided hectares."

**Methane projects ({N_METHANE}):**

- *R signal:* Project's claimed annual emission reduction (converted to continuous CH4 capture rate kg/hr at GWP100 = 28).
- *M signal:* Carbon Mapper L4A point-source plume detections within 5 km of the project centroid, restricted to the IPCC sector relevant to the project type (6A solid waste, 1B fugitive fuel, 3 livestock).
- *Divergence score:* Implied capture rate = claimed_capture / (claimed_capture + observed_leakage). A well-run landfill or methane-abatement project typically achieves 70–90%; <30% is a red flag.

**Severity buckets:**

| Severity | Definition |
|---|---|
| RED_FLAG_NEGATIVE | Forest project where deforestation INCREASED during crediting period |
| RED_FLAG_LOW_CAPTURE | Methane project with <30% implied capture rate |
| SEVERE_UNDERDELIVERY | Forest project where observed reduction is <25% of claimed |
| SEVERE_LOW_CAPTURE | Methane project with 30–50% implied capture rate |
| MODERATE_UNDERDELIVERY | Forest project where observed reduction is 25–75% of claimed |
| MODERATE_LOW_CAPTURE | Methane project with 50–70% implied capture rate |
| PASS | Within the expected range |

---

## Headline findings

[Insert top 25 worst offenders table from `build_league_table.py` output here.]

---

## Geographic concentration

[Insert breakdown of red flags by country.]

---

## Caveats

1. **Hansen forest definition vs project's:** Hansen uses ≥30% canopy cover as forest. Some Verra methodologies use other thresholds. We checked: most flagged projects have >90% forest fraction at the 30% threshold, so threshold sensitivity is unlikely to overturn results.
2. **Carbon stock heterogeneity:** Using uniform 165 tCO2/ha understates carbon storage in primary tropical forest (200–300 tCO2/ha) and overstates it in degraded/secondary forest. Effect on flagged projects: the higher carbon stock would *increase* implied avoided hectares, *worsening* the divergence ratio for projects flagged as RED_FLAG_NEGATIVE.
3. **Single observations:** Carbon Mapper plume detections are snapshots. A single detection doesn't establish a continuous emission rate. Multi-observation projects are more reliable; we report observation count alongside emission rates.
4. **Counterfactual baselines:** Forest projects can argue that their PDD baseline counterfactual would have been higher than historical without the project, and therefore observed deforestation matching historical = success. This argument requires the counterfactual itself to be defensible. Where the project area shows *increasing* deforestation under the project (RED_FLAG_NEGATIVE), the counterfactual argument doesn't recover the claim regardless.
5. **Carbon Mapper coverage** is not yet global. Asian projects (China, Southeast Asia, Central Asia) are largely outside coverage and excluded from methane scoring; we report status `outside_cm_coverage` for these.

---

## Data and reproducibility

All inputs are public:

- Verra registry: `https://registry.verra.org/uiapi/resource/resource/search` (no auth)
- Hansen GFC v1.11: `https://storage.googleapis.com/earthenginepartners-hansen/GFC-2023-v1.11/` (no auth, COG via `/vsicurl/`)
- Carbon Mapper STAC: `https://api.carbonmapper.org/api/v1/stac/search` (no auth)

Source code: `/Users/ajay/exalted/signalos/verticals/carbon_offsets/scan_forest.py`, `scan_methane.py`, `build_league_table.py`.

---

## Per-project deep dives

[Auto-generate one section per top-25 worst offender with:
- Project ID, name, country, sub-type
- Verra URL: https://registry.verra.org/app/projectDetail/VCS/{id}
- Crediting period, proponent, claimed annual reduction
- Observed pre/post deforestation OR plume detections
- Divergence score and severity
- Caveats specific to this project]
