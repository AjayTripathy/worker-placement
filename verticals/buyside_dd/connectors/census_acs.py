"""Census ACS B25031 — median gross rent by bedroom count.

Used as a market-rent comparable to flag rents that diverge materially from
neighborhood median. ACS 5-year estimates lag ~2 years; treat as floor.

API: https://api.census.gov/data/{year}/acs/acs5
Auth: free key from https://api.census.gov/data/key_signup.html
      export CENSUS_API_KEY=<key>

Variables (B25031 — median gross rent by bedrooms):
  B25031_001E — median, all units
  B25031_002E — no bedroom (studio)
  B25031_003E — 1BR
  B25031_004E — 2BR
  B25031_005E — 3BR
  B25031_006E — 4BR
  B25031_007E — 5BR+
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'm_source',
    "sic_codes": [],
    "sic_prefixes": ['65'],
    "issuer_features": ['residential_rental_business'],
    "asset_classes": ['corporate_ipo_dd', 'real_assets'],
    "applies_universally": False,
    "summary": 'ACS median gross rent by bedroom: market-rent ground truth for residential landlords.',
}

import os

from .base import (
    BaseConnector,
    ConnectorRequest,
    ConnectorResult,
    ConnectorObservation,
    ErrorKind,
    safe_get,
)


VARIABLES = {
    0: "B25031_002E",
    1: "B25031_003E",
    2: "B25031_004E",
    3: "B25031_005E",
    4: "B25031_006E",
    5: "B25031_007E",
}


class CensusAcsConnector(BaseConnector):
    source_id = "census_acs_b25031"
    rate_limit_per_min = 30

    def query(self, request: ConnectorRequest) -> ConnectorResult:
        key = os.getenv("CENSUS_API_KEY")
        if not key:
            return self._fail(
                request, ErrorKind.AUTH,
                "CENSUS_API_KEY env var not set; free key at api.census.gov/data/key_signup.html",
            )

        year = request.year or 2022
        zip5 = self._zip_from_request(request)
        if not zip5:
            return self._fail(
                request, ErrorKind.UNSUPPORTED,
                "need 5-digit zip in geographic_area or address",
            )

        get_vars = ",".join([VARIABLES[0], VARIABLES[1], VARIABLES[2], VARIABLES[3], VARIABLES[4], VARIABLES[5]])
        url = (
            f"https://api.census.gov/data/{year}/acs/acs5"
            f"?get=NAME,{get_vars}&for=zip%20code%20tabulation%20area:{zip5}&key={key}"
        )
        self._throttle()
        sess = self._session()
        r, ek, ed = safe_get(sess, url)
        if r is None:
            return self._fail(request, ek, ed)
        try:
            arr = r.json()
        except ValueError as e:
            return self._fail(request, ErrorKind.PARSE_FAIL, f"json: {e}", raw=r.text)

        if not isinstance(arr, list) or len(arr) < 2:
            return self._fail(request, ErrorKind.NOT_FOUND, f"no data for zip {zip5}", raw=r.text)

        header = arr[0]
        row = arr[1]
        idx = {h: i for i, h in enumerate(header)}
        obs = []
        obs.append(ConnectorObservation(
            attribute="census_acs_zcta_name",
            value=row[idx["NAME"]],
            source_url=url,
        ))
        for br, var in VARIABLES.items():
            if var not in idx:
                continue
            raw_val = row[idx[var]]
            try:
                val = float(raw_val) if raw_val not in (None, "", "-666666666") else None
            except ValueError:
                val = None
            if val is not None:
                obs.append(ConnectorObservation(
                    attribute=f"acs_median_rent_{br}br",
                    value=val,
                    value_unit="USD/month",
                    source_url=url,
                    extra={"variable": var, "year": year},
                ))
        return self._ok(request, obs, raw=r.text)

    def _zip_from_request(self, req: ConnectorRequest) -> str | None:
        if req.geographic_area and req.geographic_area.isdigit() and len(req.geographic_area) == 5:
            return req.geographic_area
        if req.address:
            tail = req.address.strip().split()[-1]
            if tail.isdigit() and len(tail) == 5:
                return tail
            for tok in req.address.split():
                if tok.isdigit() and len(tok) == 5:
                    return tok
        if req.extra and "zip" in req.extra:
            return str(req.extra["zip"])
        return None


if __name__ == "__main__":
    c = CensusAcsConnector()
    req = ConnectorRequest(geographic_area="15210", year=2022)  # Pittsburgh
    result = c.query(req)
    print(f"success={result.success} error={result.error_kind}/{result.error_detail}")
    for o in result.observations:
        print(f"  {o.attribute} = {o.value} {o.value_unit or ''}")
