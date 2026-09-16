# verticals

Each subfolder is one application of the Signal OS framework. All verticals share the same `core/` primitives but instantiate domain-specific Sources, GapFunctions, and SignalRules.

| Vertical | What it does | Production state |
|---|---|---|
| [`property_tax/`](property_tax/) | Detects overdue property tax uncaps (TV not reset after transfer) under MCL 211.27a. Detroit + LA jurisdictions; Michigan statute model shared. | **Production-validated** — citywide Detroit scan, ~8,126 overdue parcels, $11.9–$26.2M/yr suppressed taxes. Held-out blinded re-run in `lasalle_v2/` validated the headline + surfaced PRE-on-LLC as a separate fraud category. |
| [`rent_stabilization/`](rent_stabilization/) | Detects rent overcharges on NYC J-51 / Rent Stabilization Law (RSL) units — listed asking rent vs legal-max-rent under RGB cumulative factor. | **Built, NYC wired** — RSL overcharge rule + NYC RGB schedule + listing-source connectors. |
| [`carbon_offsets/`](carbon_offsets/) | Detects voluntary carbon market under-delivery via satellite — REDD+ avoided-deforestation, methane plume rates, mangrove cover. | **Production-validated** — V2 forest scan complete (398 satellite-direct projects, 96% underdelivering, $1.59B claim coverage). Methane + mangrove modules built. |
| [`buyside_dd/`](buyside_dd/) | General-purpose forensic DD on private deal data rooms — extracts claims from PDFs/decks, types referents, looks up f-rules and M-sources, runs cross-checks. | **Built, two real-deal validations** — FCRE2 ($30M Section 8 RE) and AHC ($50M venture). 14+ source connectors. |
| [`public_co/`](public_co/) | Public-co SEC-filing forensic divergence screen. Runs forward on any current ticker; runs as backtest against historical cohorts with known outcomes for validation. Subagent-firewalled blinding, USPTO ODP patent connector, calibration heuristics. | **Built, validated on eVTOL + 3D printing cohorts** — perfect monotonic ranking on eVTOL (N=6, 1 confirmed bankruptcy); ~50/50 on held-out 3D printing pre-improvements. See `public_co/ARCHITECTURE.md`. |
| [`nikola_backtest/`](nikola_backtest/) | Legacy folder — pipeline migrated to `public_co/`. Keeps published case study + pre-refactor evidence JSON for historical reference. | Frozen reference. |
| [`lordstown_backtest/`](lordstown_backtest/) | Same as Nikola — legacy folder, scripts migrated to `public_co/`. | Frozen reference. |

## Vertical pattern

A new vertical typically adds:

1. A `manifest.py` with a `VerticalManifest` (declares required source types)
2. A `gap.py` with a GapFunction
3. A `scorer.py` with a Scorer
4. `jurisdictions/<j>/` with jurisdiction-specific Sources, config, registry-builder
5. `sources/` with cross-jurisdiction source connectors (if applicable)
6. `rules/<rule>.py` with one SignalRule per legal carve-out / exemption / amplifier

The buyside_dd and public_co verticals are structurally different — they don't slot into the per-jurisdiction `signalos run` CLI because the unit of analysis is a document set, not an entity universe.

## Choosing what to build next

`vertical_ilr_scoring.md` (top-level) lists candidate verticals scored on I × L × accessibility(M). Don't build verticals where any one of those is zero.
