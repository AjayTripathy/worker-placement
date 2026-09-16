# Carbon Offsets Vertical — Step 1 Findings

*Data accessibility verification + credit type profile + anchor project sanity check. 2026-05-11.*

---

## Step 1a: Verra registry data accessibility — VERIFIED

**Public API surface** (no auth, no rate limit observed for project pulls):

| Endpoint | Purpose | Method |
|---|---|---|
| `POST /uiapi/resource/resource/search` | Project search (full registry) | Body: `{"program":"VCS","resourceType":"PROJECT"}`, query: `$top`, `$skip`, `$count=true` |
| `GET /uiapi/resource/resourceSummary/{id}` | Project detail (docs, location, attrs) | None |
| `POST /uiapi/asset/asset/search` | Issuance/credit search | Body shape not yet pinned down — returns 400 on incomplete params; revisit |
| `GET /mymodule/ProjectDoc/Project_ViewFile.asp?FileID={n}&IDKEY={k}` | Document download (PDDs, KMLs, monitoring reports, ERR spreadsheets) | Static IDKEY in registry response — no auth challenge |

**Saved to disk:** `/Users/ajay/exalted/signalos/verticals/carbon_offsets/data/verra_projects.json` — full 4,962-project pull.

**Project detail returns:**
- `resourceName`, `description`, `location` (lat/lon centroid), `attributes` (state/province), `participationSummaries` (proponent, status, est annual reductions, project category, validator name, registration date, crediting period, project acreage)
- `documentGroups`: `VCS_PIPELINE_DOCUMENTS`, `VCS_REGISTRATION_DOCUMENTS`, `VCS_ISSUANCE_DOCUMENTS`, `VCS_OTHER_DOCUMENTS`, `CCB_*` for dual-certified
- Each document has `uri`, `documentType`, `documentName`, `uploadDate`

**Critical finding:** AFOLU projects publish **KML files** as project documents (e.g., Mai Ndombe REDD+ has `Mai_Ndombe_PAA.kml` — 2 MB, 1,601 polygons, 5,597 coordinate strings). This is the actual project area geometry, downloadable without auth.

Non-AFOLU projects (methane, energy, waste) typically have only a centroid lat/lon, not polygons — sufficient for satellite point queries with a buffer.

**Issuance API gap:** Per-vintage credit issuance data is gated behind a request body shape we haven't fully reverse-engineered (returns 400 on most variants). Workaround: parse "Issuance Representation" PDF documents per project — they're public and contain vintage + tonnage. Defer issuance API; not blocking.

---

## Step 1b: Credit type distribution

**Total: 4,962 VCS projects, 2,626 active (Registered or in active issuance)**

**Top 10 by total estimated annual emission reductions (MtCO2/yr):**

| Integrity bucket | Total projects | Active | Total volume | Active volume | M-source feasibility |
|---|---|---|---|---|---|
| Forest:REDD | 309 | 110 | 1,279 | 72 | **HIGH** (Hansen, Planet, GFW) |
| Soil:ALM | 627 | 45 | 315 | 35 | LOW (modeled) |
| Cookstoves/efficiency | 513 | 273 | 314 | 147 | **MEDIUM** (Berkeley/Gill-Wiehl methodology, household survey) |
| Renewable energy | 1,696 | 1,388 | 247 | 196 | LOW (additionality, economic) |
| Forest:ARR | 562 | 182 | 139 | 15 | **HIGH** (NDVI, Hansen) |
| Waste-to-energy | 366 | 240 | 49 | 32 | **MEDIUM-HIGH** (sat methane near plant) |
| **Methane:fugitive (O&G)** | 28 | 21 | 41 | 35 | **VERY HIGH** (MethaneSAT, Carbon Mapper) |
| Waste/landfill | 337 | 202 | 40 | 17 | **VERY HIGH** (sat methane, plume detection) |
| Forest:IFM | 158 | 25 | 29 | 4 | **HIGH** (Hansen + state forest data) |
| Methane:livestock | 56 | 22 | 19 | 3 | MEDIUM (sat methane) |

**Strategic implications:**

- **Strong external M coverage exists for ~1,927 projects (39% of registry)** — forest, methane, waste/landfill — these are where divergence scoring is technically clean.
- **Cookstoves is a hidden giant (147 MtCO2/yr active)** — Berkeley 2024 paper (Gill-Wiehl) found ~10× over-crediting on average; methodology validated, no productized scoring exists yet.
- **Methane fugitive is small N (28 projects) but huge per-project value (35 MtCO2/yr active)** — Uzbekistan/Bangladesh gas distribution leakage projects are exactly the type where MethaneSAT plume detection can directly verify or contradict claims.
- **Renewable energy is the largest by project count (1,696) but the weakest by external M** — covering it requires economic additionality modeling, not satellite. Defer to a later phase.

---

## Step 1c: Anchor project sanity check

Three anchor projects validated, one per integrity-scoring methodology family:

### Anchor A: Mai Ndombe REDD+ Project (ID 934, Congo DRC)
- **Type:** Forest:REDD
- **Status:** Registered
- **Annual reduction claim:** 5.67 MtCO2/yr
- **Project area:** Multi-polygon KML, 1,601 polygons (downloaded, parseable)
- **Documents:** 7 groups, 97 docs total — PDD, Issuance Reps (×7 vintages), CCB monitoring reports (×16), ERR Calculation Spreadsheet
- **Methodology:** Hansen Global Forest Change tile data over the KML AOI; compare actual annual deforestation to PDD baseline counterfactual
- **Significance:** This is one of the largest REDD+ projects globally; previously studied by CarbonPlan and Wildlife Works critics

### Anchor B: Hududgaz Gas Distribution Methane Reduction (ID 4531, Uzbekistan)
- **Type:** Methane:fugitive
- **Status:** Registered
- **Annual reduction claim:** 7.35 MtCO2/yr
- **Project area:** Centroid at (41.286, 69.233) — Tashkent metro; actual project area is the Hududgaz pipeline network across Uzbekistan
- **Documents:** 4 groups, 24 docs — PDD, Issuance Reps (×8), Communications Agreement, Partial Release docs
- **Methodology:** MethaneSAT and Carbon Mapper plume detection over Uzbekistan gas infrastructure; if reduction claims are real, plumes should disappear post-implementation; if claims are inflated, plumes persist
- **Significance:** This is a relatively new VCS project type using methodology VM0048/VM0050. The integrity literature is thin — this is alpha-rich territory

### Anchor C: ECOPARQUE PAULÍNIA Landfill (ID 3404, Brazil)
- **Type:** Waste/landfill
- **Status:** Registered
- **Annual reduction claim:** 1.82 MtCO2/yr
- **Project area:** Centroid at (-22.778, -47.206) — São Paulo state, single landfill site
- **Documents:** 4 groups, 8 docs — Registration only (no Issuance docs yet, project registered late 2024)
- **Methodology:** Methane satellite (MethaneSAT free public data) point query at landfill location; landfill methane plumes are some of the most directly verifiable carbon claims
- **Significance:** Single-point method validates the satellite-vs-claim approach without polygon complexity

---

## What's confirmed accessible (engine inputs)

| Input | Source | Format | Cost |
|---|---|---|---|
| Project metadata (full registry) | Verra UIAPI | JSON | Free |
| Project area geometry | Verra documents (KML) | XML | Free |
| Project narrative + baseline claims | Verra PDDs | PDF | Free (need PDF parser) |
| Per-vintage issuance | Verra Issuance Representation PDFs OR pinned API call (TBD) | PDF / JSON | Free |
| Annual deforestation | Hansen Global Forest Change (Google Earth Engine) | Raster | Free with GEE account |
| Methane plumes | MethaneSAT public data, Carbon Mapper portal | Vector + raster | Free (public datasets); Sentinel-5P TROPOMI free |
| Forest cover trends (alt) | ESA WorldCover, Planet (commercial) | Raster | Free / Commercial |

---

## Recommended Step 2 (decision needed before proceeding)

Three options for which anchor to fully build out first:

**Option A — Forest:REDD on Mai Ndombe.** Reproduces the Guardian/CarbonPlan methodology; validates pipeline against a known answer; output is a comparable replication of published critique. Requires KML parsing, Google Earth Engine setup, Hansen tile queries.

**Option B — Methane fugitive on Hududgaz Uzbekistan.** Highest alpha (no published scoring exists for this methodology family); requires MethaneSAT/Carbon Mapper API access; output is potentially novel finding. Higher technical risk because methane satellite data quality varies by location and time.

**Option C — Landfill on ECOPARQUE Brazil.** Cleanest single-point validation of satellite-vs-claim approach; lowest technical complexity; useful as "calibration" before scaling to harder cases. Lower per-project value.

**My recommendation: build the architecture against B and C in parallel, defer A.**

Reasoning: REDD+ is the most-studied bucket. Reproducing a known answer is good for validation but doesn't produce new commercial signal. The methane buckets (fugitive + landfill) have **the strongest external M signal in the registry** (literally measured plumes from satellites), the **smallest competitive coverage** in published research, and **non-trivial active issuance** (35 + 17 = 52 MtCO2/yr active across only 223 projects = much more concentrated value per investigation). Building B+C also forces the per-type architecture to handle satellite methane natively, which is required infrastructure for the broader methane portion of the market (livestock, fugitive, landfill, gas distribution).

REDD+ can be added later as a third connector once the methane infrastructure works.

**Awaiting decision before proceeding to Step 2.**
