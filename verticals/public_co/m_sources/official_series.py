"""official_series — official-statistics MARKET LAYER (a series REGISTRY, not a watch).

Primary data source: national/territorial statistical agencies, fetched from their
own endpoints — DICJ Macao (monthly gross gaming revenue, report_en.xml behind the
JS/XSLT monthly page) and DSEC Macao (TimeSeriesApi indicator tree + value POST) in
v1; Eurostat / FDIC / US Census / EU TED registered as migration candidates.

Mechanism: the market-wide official print is the DENOMINATOR a single issuer's
claimed demand trajectory has to sit inside. A concession-wide GGR month, territory
visitor arrivals and territory hotel occupancy jointly separate "demand fell" from
"we lost share" from "spend-per-visit compressed" — three different theses that the
issuer's own release will not distinguish for you. Free, primary, T+1-day fast for
GGR and impossible to fake.

Pattern (the reason this is ONE m_source and not one module per country): a series
is a REGISTRY ROW declaring agency / geo / explicit UNIT / cadence / release lag /
adapter + params / the issuer features it serves. Adapters are per AGENCY, so a new
series from a known agency costs three lines. Dispatch matches issuer features (and
a geo token gate — SIC alone must never hand Macau GGR to Chipotle) to registered
series, and render_series() injects the matched table into the planner and both
benches.

CONFOUNDER: market-wide != company-specific (share can fall into a rising market);
official series get REVISED (the registry records revisions rather than clobbering);
rates (occupancy) take percentage-POINT deltas and refuse quarter summing, levels
(GGR, arrivals) take percent change.

Sibling m_sources here (bls_qcew, bts_airline_metrics, cms_cost_reports) are each a
SINGLE official series wired as its own module. This one is the generalization of
that pattern: they can be folded in as registry rows behind an agency adapter.

This is a THIN SHIM: the registry, agency adapters, degraded-never-cached cache and
merge-by-period history live in desk/official_series.py so the standing refresh
watch (registry entry official_series_refresh) sits next to the desk's watch loop.
The shim exists so the knowledge graph's m_source walk and the atlas's module
resolution both see the channel through their normal pattern.

STATUS: LIVE — 3 registered series, all fetched from primary agency endpoints.
Cache: desk/data/official_series/<key>.json
"""
from __future__ import annotations

from desk.official_series import (   # noqa: F401  (re-exported registry surface)
    ADAPTERS,
    APPLIES_TO,
    SERIES,
    backfill,
    fetch,
    history,
    latest,
    nowcast_quarter,
    refresh_all,
    render_series,
    series_for,
    yoy,
)
