# carbon_offsets

Voluntary carbon market satellite-vs-claim divergence. Three product modules — REDD+ avoided-deforestation forest scans, methane plume rates, mangrove cover.

## Production state

- **V2 forest scan complete:** 398 satellite-direct projects scanned, **96% underdelivering**, **$1.59B claim coverage** ([`STEP3_LEAGUE_TABLE.md`](STEP3_LEAGUE_TABLE.md), [`league_table.csv`](data/league_table.csv))
- **Methane scan**: built ([`scan_methane.py`](scan_methane.py)) — uses Carbon Mapper L4A plume detections sector-filtered
- **Mangrove scan**: built ([`scan_mangrove.py`](scan_mangrove.py))
- **Buyer-pitch deck**: [`BUYER_PITCH.md`](BUYER_PITCH.md) — defensible-done state for outreach to insurers / fund-of-funds

## Methodology

Synthetic-control upgrade (matches West et al. 2020 PNAS approach):
- For each project, compute a buffer-ring control area (5–30km outside AOI)
- Mask both project + control to forest_2000 (canopy ≥30%)
- Compute annual deforestation rate (ha lost / ha forested) for both
- Counterfactual deforestation = control rate × project forest area
- Project benefit = counterfactual_loss − actual_project_loss
- Compare to the project's claimed avoided deforestation

Implementation lives in [`scan_forest_v2.py`](scan_forest_v2.py). v1 (`scan_forest.py`) used a simpler before/after delta; v2 added the buffer-ring counterfactual to handle confounding from baseline trends.

## Layout

```
carbon_offsets/
├── BUYER_PITCH.md             Buyer-facing deck; defensible-done state
├── REPORT_TEMPLATE.md         Per-project report template
├── STEP1_FINDINGS.md          Methodology validation findings
├── STEP2_FINDINGS.md          Cohort-level findings
├── STEP3_LEAGUE_TABLE.md      League table writeup (398 projects)
├── scan_forest.py             v1 forest scanner (before/after delta)
├── scan_forest_v2.py          v2 with synthetic-control buffer ring  ← current
├── scan_mangrove.py           Mangrove cover analyzer
├── scan_methane.py            Carbon Mapper plume-rate analyzer
├── score_mangrove.py
├── build_league_table.py      Cohort league table builder
├── build_satellite_direct_report.py
├── calibrate_probability.py   Severity → probability calibration
├── compare_buffer_methods.py  v1 vs v2 sensitivity comparison
├── insurance_output.py        Insurer-format output (per-project actuarial)
├── retry_failed_kmls.py       KML cache retry harness
├── validate_pipeline.py
├── diagnose_hang.py           macOS fork() + Cocoa workaround diagnostic
├── data/                      JSON outputs + KML cache + league_table.csv
└── rs_cache/                  Raster cache (Hansen GFC tiles)
```

## Run

The scanners are data-pipeline scripts, not CLI commands. Run directly:

```bash
# Forest scan (v2 — current)
python3 -m verticals.carbon_offsets.scan_forest_v2

# Methane scan
python3 -m verticals.carbon_offsets.scan_methane

# Build league table from completed scans
python3 -m verticals.carbon_offsets.build_league_table
```

## Notes

- macOS fork() + Cocoa requires `OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` (set automatically in v2). See [`diagnose_hang.py`](diagnose_hang.py) for the underlying rasterio/objc issue.
- Carbon Mapper plume coverage is geographically partial (longitudes east of ~57° currently uncovered). `accessibility(M)` varies geographically — check coverage for each project's centroid before scoring.
- The `scan_methane_BUGGED.json` artifact is from a known pre-fix run; the current `scan_methane.json` is the corrected output.
