"""
NYC Census ACS rental listing source — returns Record(record_type="listing").

Uses Census Bureau ACS 5-year estimates (table B25031) to return median gross
rent by bedroom count for a given ZIP code. This is not a per-building listing
but a ZIP-level market benchmark — the gap it produces represents the potential
incentive for a landlord to overcharge rather than confirming a specific overcharge.

ACS variable mapping (B25031):
  B25031_002E — median gross rent, no bedroom (studio)
  B25031_003E — median gross rent, 1 bedroom
  B25031_004E — median gross rent, 2 bedrooms
  B25031_005E — median gross rent, 3 bedrooms
  B25031_006E — median gross rent, 4+ bedrooms

Metadata note: records include data_quality="area_median" to distinguish from
building-specific scraped listings. Gap function respects this flag.
"""
from __future__ import annotations

from datetime import date, datetime

import httpx

from core.exceptions import SourceError
from core.models import Entity, Record

source_id   = "nyc_census_acs"
record_type = "listing"

_ACS_BASE    = "https://api.census.gov/data/2022/acs/acs5"
_ACS_VARS    = "B25031_002E,B25031_003E,B25031_004E,B25031_005E,B25031_006E"
_HEADERS     = {"User-Agent": "SignalOS/1.0 (academic/nonprofit research)"}

_BEDROOM_VARS = {
    0: "B25031_002E",
    1: "B25031_003E",
    2: "B25031_004E",
    3: "B25031_005E",
    4: "B25031_006E",
}


def _fetch_acs_rents(zip_code: str) -> dict[int, float] | None:
    """Return {bedrooms: median_rent} for the zip code, or None on failure."""
    try:
        with httpx.Client(headers=_HEADERS, timeout=20) as client:
            resp = client.get(_ACS_BASE, params={
                "get": _ACS_VARS + ",NAME",
                "for": f"zip code tabulation area:{zip_code}",
            })
            resp.raise_for_status()
            rows = resp.json()
    except httpx.HTTPError as e:
        raise SourceError(f"Census ACS fetch failed for {zip_code}: {e}") from e

    if len(rows) < 2:
        return None

    header = rows[0]
    values = rows[1]
    result: dict[int, float] = {}

    var_list = [_ACS_VARS.split(",")[i] for i in range(5)]
    for bedrooms, var in enumerate(var_list):
        if var in header:
            idx = header.index(var)
            try:
                val = float(values[idx])
                if val > 0:
                    result[bedrooms] = val
            except (ValueError, TypeError, IndexError):
                pass

    return result if result else None


class NYCCensusRentsSource:
    source_id      = source_id
    record_type    = record_type
    cache_ttl_days = 365    # ACS estimates change annually

    def fetch(self, entity: Entity) -> list[Record]:
        zip_code = entity.metadata.get("zip_code", "")
        bbl      = entity.id
        if not zip_code:
            return []
        return _make_records(zip_code, bbl)


def _make_records(zip_code: str, bbl: str) -> list[Record]:
    rents = _fetch_acs_rents(zip_code)
    if not rents:
        return []

    today = date.today()
    records = []
    for bedrooms, median_rent in rents.items():
        records.append(Record(
            entity_id=bbl,
            record_type=record_type,
            source=source_id,
            data={
                "bbl":          bbl,
                "address":      f"ZIP {zip_code} area median",
                "unit":         None,
                "listed_rent":  median_rent,
                "bedrooms":     bedrooms,
                "listing_date": str(today),
                "source":       source_id,
                "data_quality": "area_median",
                "zip_code":     zip_code,
            },
            fetched_at=datetime.utcnow(),
        ))
    return records


def fetch_zip_rents(zip_code: str) -> dict[int, float] | None:
    """Public helper — returns {bedrooms: median_rent} for the given zip."""
    return _fetch_acs_rents(zip_code)
