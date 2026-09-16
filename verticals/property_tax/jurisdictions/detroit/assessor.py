"""Detroit Open Data assessor source — returns Record(record_type="assessment")."""
from __future__ import annotations

import time
from datetime import datetime
from typing import Iterator

import httpx

from core.exceptions import SourceError
from core.models import Entity, Record

FEATURE_SERVER = (
    "https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services"
    "/tentative_assessment_roll_2025/FeatureServer/0/query"
)

SELECT_FIELDS = ",".join([
    "parcel_id", "address", "zip_code", "taxpayer_1",
    "amt_assessed_value", "amt_taxable_value",
    "amt_taxable_value_tentative", "amt_assessed_value_tentative",
    "amt_estimated_true_cash_value",
    "sale_date", "amt_sale_price", "pct_pre_claimed",
    "property_class_description", "use_code_description",
    "nez_district", "tax_status",
])

_NEZ_JUNK = frozenset({
    "None", "VACANT LAND", "BUILDING DEMO", "NO STRUCTURE", "VACANT LOT",
    "BUILDING DEMOLITION", "0", "1801", "2", "PO1", "  ", "",
})

source_id = "detroit_open_data"
record_type = "assessment"


def _parse(row: dict) -> dict | None:
    parcel_id = row.get("parcel_id")
    if not parcel_id:
        return None

    def f(v):
        try:
            return float(v) if v not in (None, "", "N/A") else None
        except (ValueError, TypeError):
            return None

    raw_nez = (row.get("nez_district") or "").strip()
    nez = (
        raw_nez
        if (raw_nez
            and raw_nez not in _NEZ_JUNK
            and not raw_nez.upper().startswith(("PARCEL ADDED", "NEEDS", "DOES NOT", "NEED VALUE")))
        else None
    )

    owner = (row.get("taxpayer_1") or "").strip()

    return {
        "parcel_id":         str(parcel_id).strip().rstrip("."),
        "address":           (row.get("address") or "").strip(),
        "zip_code":          (row.get("zip_code") or "").strip(),
        "owner":             owner,
        "owner_is_entity":   _is_entity(owner),
        "sev":               f(row.get("amt_assessed_value")),
        "taxable_value":     f(row.get("amt_taxable_value")),
        "transfer_date":     row.get("sale_date") or None,
        "sale_price_record": f(row.get("amt_sale_price")),
        "homestead_pct":     f(row.get("pct_pre_claimed")) or 0.0,
        "property_class":    row.get("property_class_description") or "",
        "use_code":          row.get("use_code_description") or "",
        "nez_district":      nez,
        "tax_status":        (row.get("tax_status") or "").strip(),
        "extra": {
            "etcv":         f(row.get("amt_estimated_true_cash_value")),
            "tv_tentative": f(row.get("amt_taxable_value_tentative")),
            "av_tentative": f(row.get("amt_assessed_value_tentative")),
        },
    }


_ENTITY_SUFFIXES = frozenset({
    "LLC", "L.L.C.", "INC", "CORP", "LTD", "LP", "L.P.",
    "TRUST", "LAND BANK", "AUTHORITY", "ASSOCIATION",
})


def _is_entity(owner: str) -> bool:
    upper = owner.upper()
    return any(suf in upper for suf in _ENTITY_SUFFIXES)


def _query(params: dict) -> list:
    base = {"f": "json", "outFields": SELECT_FIELDS, "returnGeometry": "false"}
    base.update(params)
    try:
        with httpx.Client(timeout=30) as client:
            resp = client.get(FEATURE_SERVER, params=base)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise SourceError(f"ArcGIS error: {data['error']}")
            return [f["attributes"] for f in data.get("features", [])]
    except httpx.HTTPError as e:
        raise SourceError(f"Detroit Open Data request failed: {e}") from e


class DetroitAssessorSource:
    source_id = "detroit_open_data"
    record_type = "assessment"
    cache_ttl_days = 7  # assessment roll updates annually; 7 days balances freshness vs API load

    def fetch(self, entity: Entity) -> list[Record]:
        return fetch(entity.id)


def fetch(entity_id: str) -> list[Record]:
    """Fetch a single parcel by parcel_id."""
    clean = entity_id.strip().rstrip(".")
    rows = _query({"where": f"parcel_id LIKE '{clean}%'", "resultRecordCount": 1})
    if not rows:
        return []
    data = _parse(rows[0])
    if data is None:
        return []
    return [Record(
        entity_id=data["parcel_id"],
        record_type=record_type,
        source=source_id,
        data=data,
        fetched_at=datetime.utcnow(),
    )]


def fetch_zip(zip_code: str, page_size: int = 1000, delay: float = 0.25) -> Iterator[Record]:
    """Yield Records for all parcels in a zip code."""
    offset = 0
    while True:
        rows = _query({
            "where": f"zip_code='{zip_code}'",
            "resultOffset": offset,
            "resultRecordCount": page_size,
        })
        for row in rows:
            data = _parse(row)
            if data:
                yield Record(
                    entity_id=data["parcel_id"],
                    record_type=record_type,
                    source=source_id,
                    data=data,
                    fetched_at=datetime.utcnow(),
                )
        if len(rows) < page_size:
            break
        offset += page_size
        time.sleep(delay)
