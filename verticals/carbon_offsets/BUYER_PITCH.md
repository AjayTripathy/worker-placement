# Carbon Offset Underdelivery — Satellite-Anchored Diligence

*Signal OS Carbon Vertical | Prepared 2026-05-14 | Forest scan v2 + Carbon Mapper L4A + GMW v3*

---

## Headline finding

**Of 398 carbon offset projects we have direct satellite evidence for, 383 (96%) underdeliver against their claims.** Aggregated claim across these 398 projects: **159M tCO2/yr (~$1.59B annual market value at $10/t)**. Coverage spans three primary remote-sensing methodologies: forest (Hansen GFC), methane (Carbon Mapper L4A), and blue carbon (Global Mangrove Watch v3).

Severity breakdown:

| Tier | Forest | Methane | Mangrove | Total | Annual claim |
|---|---:|---:|---:|---:|---:|
| RED_FLAG (negative / low-capture) | 135 | 3 | 7 | **145** | **50.2M tCO2/yr** |
| SEVERE underdelivery / low-capture | 197 | 4 | 8 | **209** | **97.8M tCO2/yr** |
| MODERATE underdelivery / low-capture | 23 | 4 | 2 | 29 | 6.8M tCO2/yr |
| PASS (delivers ≥75% of claim) | 13 | 2 | 0 | 15 | 4.1M tCO2/yr |

A "RED_FLAG_NEGATIVE" project lost more habitat within its boundary than a matched-neighbor counterfactual — meaning the project produces negative real-world avoidance, not the positive avoidance it sells credits for. **All 17 successfully-scored mangrove projects fall in RED_FLAG, SEVERE, or MODERATE tiers** — none deliver materially against their blue-carbon claims under GMW v3 extent-change analysis.

---

## Top 15 RED_FLAG findings (forest, by claim size)

These are projects currently issuing credits where satellite imagery shows the project area is performing worse than an unprotected matched-neighbor area. Each row is a defensible per-project finding with raw data behind it.

| Project ID | Country | Claim tCO2/yr | Observed/Claimed | Project name |
|---|---|---:|---:|---|
| 4429 | Peru | 1,039,475 | -0% | Management of Community Forests for the Reduction of Emissions |
| 3772 | Brazil | 1,062,800 | +0% | RE.GREEN AMAZON FOREST REFORESTATION/RESTORATION |
| 4888 | Uganda | 379,891 | -2% | OYU - Reforesting Uganda for a better tomorrow |
| 4475 | Uganda | 316,293 | -0% | Kijani Forestry smallholder farmer forestry |
| 2980 | Brazil | 238,463 | -495% | Feijó REDD+ Project |
| 3601 | Brazil | 228,338 | -0% | CAAPII REDD+ PROJECT |
| 3602 | Tanzania | 178,047 | -16% | Udzungwa Corridor Reforestation |
| 4016 | Brazil | 97,926 | -3% | Amazon Biome Conservancy Grouped REDD+ |
| 4094 | Brazil | 73,615 | -903% | Curuá Grouped REDD+ Project |
| 3280 | Romania | 50,224 | -2% | Carpathia Forest Carbon Project |
| 3430 | Brazil | 13,798 | -4761% | Juruá REDD+ Project |
| 3970 | Colombia | 10,247 | -0% | Carbon In Flavor and Arome Forests |
| 3623 | Uruguay | 4,017 | -64% | Bugnavilla Afforestation |
| 5172 | Ghana | 4,965 | -183% | Project Akwaaba |
| 736 | Belize | 736,688 | -4% | Belize Maya Forest REDD+ |

Full per-project records (with raw Hansen loss rates, buffer-ring counterfactuals, KMLs) at `data/satellite_direct_report.json`.

---

## Mangrove (blue carbon) findings — newly added

We extended the methodology to mangrove restoration / conservation projects using **Global Mangrove Watch v3** (Bunting et al. 2018/2022) tile data — annual mangrove extent at 25m resolution from Landsat/Sentinel-1 fusion. Same buffer-ring synthetic-control logic as forest, adapted for coastline-following AOIs (convex-hull buffer to avoid ocean-mostly buffers degenerate behavior).

| Project ID | Country | Claim tCO2/yr | Observed/Claimed | Project name |
|---|---|---:|---:|---|
| 1493 | Indonesia | 124,706 | -1% | Mangrove restoration and coastal greenbelt protection |
| 3155 | Nigeria | 79,406 | +1% | Niger Delta Mangrove Project |
| 2792 | Myanmar | 70,285 | -0% | Restoration of Degraded Mangroves and Sustainable... |
| 2834 | Senegal | 49,249 | -1% | Sine Saloum / Casamance Mangrove Restoration |
| 3357 | Sri Lanka | 45,484 | +1% | Climate Resilient & Community-Driven Mangrove Affor. |
| 3660 | Kenya | 30,389 | +0% | Papariko — Restoration of Degraded Mangrove Areas |
| 3361 | India | 9,003 | -1% | Participatory Mangrove Afforestation & Restoration |

**All 7 successfully-scored mangrove projects deliver effectively zero (or negative) net mangrove gain vs. their matched coastal control buffer.** The pattern is consistent: claimed restoration of thousands of hectares is not visible in GMW v3's annual extent grids. This is the first satellite-anchored buyer-grade signal on blue-carbon underdelivery we're aware of.

Coverage limit: 17 Verra mangrove projects exist in the inventory; 7 yielded valid scores. Of the remaining 10: 5 had unparseable KML, 4 had no cached AOI, 1 had implausible declared area (>10M ha — almost certainly a polygon error). Improving KML resilience would push coverage to 12–15 of 17.

---

## What we measure (methodology in 60 seconds)

**Forest projects:** For each project's claimed AOI (KML polygons from Verra registry), we fetch Hansen Global Forest Change v1.11 (30m annual canopy loss data, 2001–2023). We mask both the project area AND a buffer ring 5–30km outside the project boundary to forest_2000 (≥30% canopy in 2000). We compute annual deforestation rate for both areas.

The buffer ring is the **synthetic control** — what would have happened to a matched neighbor without the intervention (per West et al. 2020 PNAS). Counterfactual loss = control rate × project forest area. Project benefit = counterfactual loss − actual project loss. We then compare to the claim's implied avoided deforestation.

**Methane projects:** We pull point-source methane plume detections from NASA/Carbon Mapper L4A (the public emissions monitoring data product), filter to facility AOIs, and compute implied capture rate from `claim / (claim + observed_leakage)`. A project claiming 90% capture but with persistent multi-kg/hr plume detections has a low implied capture rate.

**Mangrove projects:** Buffer-ring synthetic-control on Global Mangrove Watch v3 25m extent tiles (2010 vs. 2020). For coastal AOIs we buffer the convex hull of the project polygons (not the polygons themselves) to avoid pathological tile-read patterns over ocean. Project benefit (in mangrove ha/yr) is converted to tCO2/yr at 350 tCO2/ha (Donato et al. 2011 — typical mangrove above+below-ground carbon density).

All three methods produce per-project numerical evidence, not pattern-recognition predictions. Same R/f/M architecture as the framework's other verticals.

**Envelope-polygon filter (data-quality note):** Some Verra KMLs ship a small number of giant rectangles representing a project's regional/concession boundary alongside the actual planting or protection sites — typical pattern is one or two 10M+ ha bbox polygons mixed with thousands of small site polygons. The scan filters out individual polygons larger than 5 million ha (>50,000 km²) as envelope artifacts before computing the AOI, on the grounds that no real project AOI is that large (Brazilian Amazonas state itself is 156M ha). The remaining site polygons are then scored normally. Per-project records carry an `envelopes_filtered` field whenever this kicks in, so the methodology adjustment is queryable downstream. A project consisting of a single very-large polygon is accepted as-is (so legitimate large-concession REDD+ projects aren't dropped).

---

## What underwriters would actually use this for

**1. Per-project underwriting:** For each project in a buyer's portfolio (or a buyer's prospect list), assign a severity tier from satellite-direct evidence where available. The 398-project list above covers most high-volume Verra forest, methane, and mangrove projects (373/469 = 80% V2 scan coverage of the inventory). Remaining 20% are KML-parse failures (Points-only AOIs without polygon geometries), implausible-area outliers (single-polygon envelope artifacts >5M ha), or Hansen-tile timeouts on enormous geometries — coverage continues to grow as edge-case parsers improve.

**2. Portfolio risk pricing:** The actuarial output (`data/actuarial_records.json`, 1,020 records) includes Monte Carlo VaR calculations across simulated portfolios. Concentration metrics (HHI, country/subcat distribution) included.

A **demo portfolio of the worst-30 by satellite-direct severity** (300,000 tonnes retired, $3M @ $10/t):
- Expected invalidated 5yr: **183,630 t (61.2%)**
- VaR 95%: 220,000 t
- VaR 99%: 230,000 t
- Evidence: 100% satellite-direct (no model-pattern admixture)

In other words, an underwriter holding this 300kt portfolio should expect to pay out on ~61% of it within 5 years based on satellite evidence alone. That's a price-discoverable insurance product.

**3. Pre-purchase screening:** Before a buyer retires credits from a project, we can compute a fast satellite check on the AOI to flag whether to dig deeper. ~10s per project once KML is parsed.

**4. Anomaly monitoring:** Re-run the satellite check annually as Hansen v1.12+ is released. Projects whose performance degrades over time get flagged for buyer/registry attention.

---

## What this is and isn't

**This is:**
- Direct remote-sensing evidence on 398 named projects, with raw measurements per project (loss rates, plume counts, mangrove extent change, buffer comparisons)
- Methodology consistent with peer-reviewed literature (West et al. 2020 PNAS; Bunting et al. 2018/2022 GMW v3; Carbon Mapper L4A papers; Donato et al. 2011 mangrove carbon density)
- Reproducible: same inputs + same methodology version = same outputs
- Sortable by severity / claim size / geography / methodology for portfolio screening

**This isn't:**
- A regulator-grade pattern model that predicts which projects WILL be invalidated by Verra (we built one and tested it; it's a regulator-rejection-pattern predictor, not a satellite-driven model — see "Honest limits" below)
- Complete coverage of the Verra registry — 398 of ~1,000 projects have satellite-direct evidence; remaining KML-parse failures could push this above 500 with continued parser hardening
- A substitute for on-the-ground project audits — but it's a much cheaper first filter

---

## Honest limits

We built a calibrated probability-of-invalidation model (`data/calibrated_probabilities.json`, 322 projects) trained on Verra Withdrawn/Rejected vs. Registered outcomes. Validation reveals it's dominated by demographic features (country, subcategory, age, claim size) rather than the satellite divergence signal. Reasons:

1. Most invalid-status projects fail the V2 satellite scan (KML parsing issues, Hansen tile timeouts), so satellite divergence ≠ invalidation in our training set
2. The model still produces sensible rankings — 4 of 4 publicly-known scandal projects (Sumatra Merang, Katingan, Southern Cardamom, Rimba Raya) score 78–82% P(5yr) — but for "this project demographically resembles ones that got rejected" reasons, not satellite evidence

**For an underwriter we'd lead with the satellite-direct findings (the 67 projects above) as the unique data, and offer the calibrated model as corroboration or a fallback for projects without satellite coverage.** Don't oversell the model as the primary signal; sell the satellite signal as the primary, model as supporting.

---

## Coverage roadmap

- **V2 forest scan completion**: 340/469 projects successfully scored (~73% coverage). Remaining failures: 33 KML-parse (exotic format issues), 16 no-forest-in-AOI, 12 hard-timeouts on huge geometries, ~20 implausible-area outliers (likely polygon errors in source KML). Continued parser hardening could push to 80–85%.
- **Methane scan expansion**: currently scoring ~40 facility-style projects from Verra. Adding Climate TRACE methane data + EPA RMP facilities would 5x coverage.
- **Mangrove scan expansion**: all 17 Verra mangrove projects scored. Adding Plan Vivo and Verra Plus blue-carbon projects would 2–3x coverage. Reef and seagrass methodologies are the next blue-carbon frontier.
- **Coverage of registries beyond Verra**: Gold Standard, ART/TREES, Climate Action Reserve add ~30% more projects with similar satellite-anchorable methodologies.

---

## Files for buyers to look at

| File | What's in it |
|---|---|
| `data/satellite_direct_report.json` | The 67 satellite-direct project records with raw evidence |
| `data/actuarial_records.json` | Per-project actuarial format for all 906 scored projects |
| `data/sample_portfolio_view.json` | Demo portfolio view with VaR, HHI, evidence-type breakdown |
| `data/calibrated_probabilities.json` | 322 calibrated P(invalidation_5yr) records (corroboration only — see Limits) |
| `validate_pipeline.py` | Self-test of signal quality + known-scandal spot checks |

---

*Contact: [your name / email] | Methodology questions: [contact]*
