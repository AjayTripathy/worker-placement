# AHC Factory — Hardened Verification

*Generated: 2026-05-14T11:33:35.651954*

## Purpose

The original AHC DD run flagged 'no Austin permits' for the claimed factory. That single negative was insufficient evidence — a real factory might not show in Austin city permits if it's in a surrounding city, owned by a separate LLC, or simply doesn't have recent build work.

This script tests the factory claim across the additional `f(M)` sources we should query before treating absence as meaningful.

## Sources queried

- **TCAD** (Travis County Appraisal District) — property ownership: 14 name variants tested
- **WCAD** (Williamson County) — property ownership: 14 name variants tested
- **HCAD** (Hays County) — property ownership: 14 name variants tested
- **TCEQ Central Registry** — industrial environmental permits: 11 name variants tested
- **TX Comptroller** — entity name + DBA variants: 11 name variants tested
- **USPTO TESS** — trademarks for AMERICAN ROWHOME / ROWHOME / AHC
- **Wayback Machine** — historical website addresses on AHC domains

## Findings

See `findings.json` for full per-source response data.
