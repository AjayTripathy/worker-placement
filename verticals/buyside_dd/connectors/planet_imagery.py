"""Planet PlanetScope/SkySat optical connector — PAID ESCALATION TIER (stub).

Same BaseConnector interface and the SAME `construction_activity` / buildout output
contract as the free Sentinel2BuildoutConnector — but at Planet resolution
(PlanetScope ~3 m daily; SkySat/Pelican ~50 cm tasked) instead of Sentinel-2's
10-20 m. Use this when a specific deal justifies high-res confirmation (parcel-level
rooftops, individual structures, equipment on site) that 10 m can't resolve.

Cost model (see TECH_DEBT TD-1): SkySat tasking ~€4,500 min/order, 25 km² min AOI,
~$2-5k per diligence event; PlanetScope AOI subscription ~$10-50k/yr for continuous
monitoring. Requires a commercial license + PL_API_KEY. This stub fails cleanly with
AUTH until the key/license is wired, so the dispatch socket exists at zero cost today.
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": ['15', '16', '17', '65'],
    "issuer_features": ['construction_activity_claim', 'physical_plant_operations'],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Paid-tier optical escalation when Sentinel-2 resolution is insufficient. Same applicability as sentinel2_buildout.',
}

import os

from .base import BaseConnector, ConnectorRequest, ConnectorResult, ErrorKind


class PlanetImageryConnector(BaseConnector):
    source_id = "planet_imagery"
    rate_limit_per_min = 60

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        api_key = os.getenv("PL_API_KEY")
        if not api_key:
            return self._fail(
                request, ErrorKind.AUTH,
                "Planet commercial feed not licensed: set PL_API_KEY and a PlanetScope/SkySat "
                "subscription. Free fallback: use source_id='sentinel2_buildout' (10-20 m, $0).",
            )
        # Implementation deferred until a deal justifies the paid feed. The Quick Search +
        # Orders/Tasking API would slot here, returning the same construction_activity /
        # ndbi_delta / ndvi_delta observation contract at PlanetScope/SkySat resolution.
        return self._fail(request, ErrorKind.UNSUPPORTED, "planet_imagery query not yet implemented")
