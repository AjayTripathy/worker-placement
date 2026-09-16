"""
LA County Assessor source — returns Record(record_type="assessment").

Data sources:
  Portal API  — https://portal.assessor.lacounty.gov/api/parceldetail?ain=<AIN>
                  Current roll AV, HOE, address, use type.
  Portal API  — https://portal.assessor.lacounty.gov/api/parcel_ownershiphistory?ain=<AIN>
                  Transfer history with recording date and sale price.
  PAIS ArcGIS — assessor.gis.lacounty.gov pais_sales_parcels layer
                  Recent sales by zip code (used for zip-batch enumeration).

Key Prop 13 fields mapped:
  AIN                       — 10-digit parcel ID
  CurrentRoll_LandValue +   — current assessed value (Prop 13 capped)
  CurrentRoll_ImpValue
  CurrentRoll_BaseYear      — year AV was last reset (qualifying transfer)
  Exemption                 — "Homeowner Exemption" or "None"
  OwnershipHistory          — transfer dates and DTT sale prices
"""
from __future__ import annotations

import time
from datetime import datetime
from typing import Iterator

import httpx

from core.exceptions import SourceError
from core.models import Entity, Record

_PORTAL_BASE  = "https://portal.assessor.lacounty.gov/api"
_PAIS_SALES   = (
    "https://assessor.gis.lacounty.gov/assessor/rest/services"
    "/PAIS/pais_sales_parcels/MapServer/0/query"
)

_HEADERS = {"Accept": "application/json", "User-Agent": "SignalOS/1.0"}

source_id   = "la_county_assessor"
record_type = "assessment"

# DocumentReasonCodes that are NOT arm's-length transfers (no reassessment expected)
_EXCLUDED_REASON_CODES = frozenset({
    "U",   # Non-reappraisable trust transfer (§62d)
    "G",   # Gift
    "I",   # Interspousal transfer
    "D",   # Inheritance / devise
    "J",   # Joint tenancy death (surviving tenant)
})


def _portal_get(path: str, params: dict) -> dict:
    try:
        with httpx.Client(headers=_HEADERS, timeout=30, follow_redirects=True) as client:
            resp = client.get(f"{_PORTAL_BASE}/{path}", params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as e:
        raise SourceError(f"LA County portal request failed: {e}") from e


def _pais_get(params: dict) -> dict:
    try:
        with httpx.Client(headers=_HEADERS, timeout=30, follow_redirects=True) as client:
            resp = client.get(_PAIS_SALES, params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as e:
        raise SourceError(f"LA County PAIS request failed: {e}") from e


def _parse_parceldetail(p: dict) -> dict | None:
    ain = (p.get("AIN") or "").strip()
    if not ain:
        return None

    land = p.get("CurrentRoll_LandValue") or 0
    imp  = p.get("CurrentRoll_ImpValue") or 0
    tv   = float(land + imp) if (land + imp) > 0 else None

    address = " ".join(filter(None, [
        (p.get("SitusStreet") or "").strip(),
        (p.get("SitusCity") or "").strip(),
    ]))
    zip_code = (p.get("SitusZipCode") or "")[:5]
    hoe = (p.get("Exemption") or "").strip().lower() == "homeowner exemption"

    return {
        "parcel_id":         ain,
        "address":           address,
        "zip_code":          zip_code,
        "owner":             "",
        "owner_is_entity":   False,
        "sev":               None,   # CA has no SEV; AV is at 100% of market
        "taxable_value":     tv,
        "homestead_pct":     None,   # CA uses flat $7K HOE, not a percentage
        "transfer_date":     None,   # filled from ownership history or PAIS
        "sale_price_record": None,   # filled from ownership history or PAIS
        "nez_district":      None,
        "tax_status":        (p.get("TaxStatus") or "").strip() or None,
        "extra": {
            "base_year":           p.get("CurrentRoll_BaseYear"),
            "homeowner_exemption": hoe,
            "land_value":          float(land) if land else None,
            "improvement_value":   float(imp) if imp else None,
        },
    }


def _best_arms_length_transfer(history: list[dict]) -> tuple[str | None, float | None]:
    """
    Scan ownership history (most-recent first) for the latest arm's-length
    reassessment event. Returns (transfer_date_iso, sale_price_or_none).
    """
    for entry in history:
        if not entry.get("IsReassessed"):
            continue
        reason = (entry.get("DocumentReasonCode") or "").strip()
        if reason in _EXCLUDED_REASON_CODES:
            continue

        date_str = (entry.get("RecordingDate") or "").strip()  # "MM/DD/YYYY"
        if not date_str:
            continue
        try:
            dt = datetime.strptime(date_str, "%m/%d/%Y")
        except ValueError:
            continue

        price_raw = (entry.get("DTTSalePrice") or "").strip()
        price = float(price_raw) if price_raw else None

        return dt.strftime("%Y-%m-%d"), price

    return None, None


def _ms_to_iso(ms: int | None) -> str | None:
    if ms is None:
        return None
    try:
        return datetime.utcfromtimestamp(ms / 1000).strftime("%Y-%m-%d")
    except (OSError, ValueError):
        return None


class LACountyAssessorSource:
    source_id      = source_id
    record_type    = record_type
    cache_ttl_days = 7

    def fetch(self, entity: Entity) -> list[Record]:
        return fetch(entity.id)


def fetch(ain: str) -> list[Record]:
    """Fetch a single parcel by AIN using the portal API."""
    clean = ain.strip().replace("-", "")

    detail_resp = _portal_get("parceldetail", {"ain": clean})
    parcel_raw = detail_resp.get("Parcel")
    if not parcel_raw:
        return []

    data = _parse_parceldetail(parcel_raw)
    if data is None:
        return []

    # Augment with most recent arm's-length transfer date and price
    try:
        history_resp = _portal_get("parcel_ownershiphistory", {"ain": clean})
        history = history_resp.get("Parcel_OwnershipHistory") or []
        td, price = _best_arms_length_transfer(history)
        data["transfer_date"]     = td
        data["sale_price_record"] = price
    except SourceError:
        pass  # degrade gracefully — AV data is still useful

    return [Record(
        entity_id=data["parcel_id"],
        record_type=record_type,
        source=source_id,
        data=data,
        fetched_at=datetime.utcnow(),
    )]


def fetch_zip(zip_code: str, page_size: int = 1000, delay: float = 0.25) -> Iterator[Record]:
    """
    Yield Records for all parcels in a zip code that had recent sales.

    Enumeration uses the PAIS pais_sales_parcels layer (LIKE filter on zip).
    Per-parcel AV is fetched from the portal parceldetail API.
    Sale date and price come from PAIS, which reflects the assessor's own
    transfer records (arm's-length sales that triggered Prop 13 reassessment).
    """
    offset = 0
    while True:
        resp = _pais_get({
            "where":          f"SAADDR2 LIKE '%{zip_code}'",
            "outFields":      "AIN,SAADDR,SAADDR2,SALEDATE,SALEPRICE",
            "returnGeometry":    "false",
            "resultRecordCount": page_size,
            "resultOffset":      offset,
            "f":                 "json",
        })

        features = resp.get("features") or []
        for feat in features:
            attrs = feat.get("attributes") or {}
            ain = (attrs.get("AIN") or "").strip()
            if not ain:
                continue

            # Portal fetch for current AV
            try:
                detail_resp = _portal_get("parceldetail", {"ain": ain})
            except SourceError:
                continue
            parcel_raw = detail_resp.get("Parcel")
            if not parcel_raw:
                continue
            data = _parse_parceldetail(parcel_raw)
            if data is None:
                continue

            # Overlay PAIS sale data (assessor's own transfer record)
            sale_date_ms = attrs.get("SALEDATE")
            sale_price   = attrs.get("SALEPRICE")
            data["transfer_date"]     = _ms_to_iso(sale_date_ms)
            data["sale_price_record"] = float(sale_price) if sale_price else None

            # Use PAIS address as fallback if portal returned empty
            if not data["address"]:
                data["address"] = (attrs.get("SAADDR") or "").strip()
            if not data["zip_code"]:
                data["zip_code"] = zip_code

            yield Record(
                entity_id=data["parcel_id"],
                record_type=record_type,
                source=source_id,
                data=data,
                fetched_at=datetime.utcnow(),
            )

            time.sleep(delay)

        if not resp.get("exceededTransferLimit"):
            break
        offset += page_size
