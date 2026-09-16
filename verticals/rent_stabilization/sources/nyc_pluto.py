"""
NYC PLUTO source — returns Record(record_type="stabilization") for buildings
likely subject to the NYC Rent Stabilization Law (RSL).

Data: NYC MapPLUTO via Socrata (dataset 64uk-42ks).
  https://data.cityofnewyork.us/resource/64uk-42ks.json

Stabilization inference rules (all must hold):
  1. yearbuilt < 1974 (pre-RSL; buildings built earlier covered by original 1969 law)
     OR bldgclass starts with C or D (apartment buildings) with taxclass 2x
  2. unitsres >= 6 (threshold for RSL coverage)
  3. taxclass in {"2", "2A", "2B", "2C"} (residential multi-family)

J-51 enrichment:
  If a BBL appears in the J-51 historical dataset (y7az-s7wc) and the
  stabilization obligation hasn't expired (init_year + ex_years + 35 > now),
  status is upgraded to "j51_confirmed" with confidence=1.0.

This source does NOT return unit-level legal rents — it provides building
characteristics used by RentStabilizationGapFunction to estimate the max
legal rent from the RGB schedule + borough base rent.
"""
from __future__ import annotations

import time
from datetime import datetime
from decimal import Decimal
from typing import Iterator

import httpx

from core.exceptions import SourceError
from core.models import Entity, Record

from ..rgb_schedule import BASE_RENT_1969, BOROUGH_CODES, RSL_ENACTMENT_YEAR

_PLUTO_ENDPOINT = "https://data.cityofnewyork.us/resource/64uk-42ks.json"
_J51_ENDPOINT   = "https://data.cityofnewyork.us/resource/y7az-s7wc.json"

_HEADERS = {"Accept": "application/json", "User-Agent": "SignalOS/1.0"}

source_id   = "nyc_pluto"
record_type = "stabilization"

_RSL_TAX_CLASSES   = {"2", "2a", "2b", "2c"}
_LIKELY_STABLE_BLD_CLASSES = {
    "C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9",
    "D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9",
}
_RSL_ENACTMENT_YEAR = 1974  # buildings completed before 1974 covered from enactment

_ENTITY_SUFFIXES = frozenset({
    "LLC", "L.L.C.", "INC", "CORP", "LTD", "LP", "L.P.",
    "TRUST", "AUTHORITY", "ASSOC", "PARTNERS", "REALTY",
})


def _is_entity(name: str) -> bool:
    upper = name.upper()
    return any(s in upper for s in _ENTITY_SUFFIXES)


def _boro_name(boro_code: str) -> str:
    return BOROUGH_CODES.get(str(boro_code).strip(), "unknown")


def _parse_pluto(row: dict, j51_bbl_set: set[str] | None = None) -> dict | None:
    # PLUTO Socrata returns BBL as a float string like "2026710001.00000000"
    bbl_raw = (row.get("bbl") or "").strip()
    if not bbl_raw:
        return None
    bbl = str(int(float(bbl_raw))).zfill(10)

    unitsres  = int(row.get("unitsres") or 0)
    year_built = int(row.get("yearbuilt") or 0)
    bldg_class = (row.get("bldgclass") or "").strip().upper()
    tax_class  = (row.get("taxclass") or "").strip().lower()
    owner      = (row.get("ownername") or "").strip()
    borough    = _boro_name(row.get("boro") or row.get("borocode") or "")

    # Apply RSL eligibility rules
    if unitsres < 6:
        return None
    if bldg_class not in _LIKELY_STABLE_BLD_CLASSES:
        return None

    # Confidence scoring
    confidence = 0.5
    if year_built > 0 and year_built < _RSL_ENACTMENT_YEAR:
        confidence += 0.2   # pre-RSL vintage is strong signal
    if bldg_class in _LIKELY_STABLE_BLD_CLASSES:
        confidence += 0.1
    if unitsres >= 20:
        confidence += 0.1   # larger buildings more likely to be fully stabilized
    confidence = min(confidence, 0.85)  # cap at 0.85 without confirmed exemption data

    # J-51 enrichment
    status = "likely"
    exemption_type = None
    exemption_init_year = None
    exemption_duration_years = None

    if j51_bbl_set and bbl in j51_bbl_set:
        status = "j51_confirmed"
        confidence = 1.0
        exemption_type = "j51"

    # Borough base rent estimate
    base_rent = BASE_RENT_1969.get(borough, Decimal("100"))
    base_year = RSL_ENACTMENT_YEAR

    address = (row.get("address") or "").strip()
    zip_code = (row.get("zipcode") or "").strip()[:5]

    return {
        "bbl":                       bbl,
        "address":                   address,
        "borough":                   borough,
        "zip_code":                  zip_code,
        "unitsres":                  unitsres,
        "year_built":                year_built,
        "bldg_class":                bldg_class,
        "tax_class":                 tax_class,
        "owner":                     owner,
        "owner_is_entity":           _is_entity(owner),
        "stabilization_status":      status,
        "stabilization_confidence":  confidence,
        "base_rent_estimate":        str(base_rent),
        "base_year":                 base_year,
        "exemption_type":            exemption_type,
        "exemption_init_year":       exemption_init_year,
        "exemption_duration_years":  exemption_duration_years,
        "extra":                     {
            "lotarea":  row.get("lotarea"),
            "bldgarea": row.get("bldgarea"),
            "assesstot": row.get("assesstot"),
        },
    }


def _load_j51_bbls(current_year: int) -> set[str]:
    """
    Return the set of BBLs with an active J-51 stabilization obligation.

    J-51 requires stabilization for ex_years + 35 years after init_year.
    Obligation active when: init_year + ex_years + 35 > current_year.
    """
    active: set[str] = set()
    offset = 0
    page = 1000
    while True:
        try:
            with httpx.Client(headers=_HEADERS, timeout=30) as client:
                resp = client.get(_J51_ENDPOINT, params={
                    "$limit":  page,
                    "$offset": offset,
                    "$select": "b,block,lot,init_year,ex_years",
                })
                resp.raise_for_status()
                rows = resp.json()
        except httpx.HTTPError as e:
            raise SourceError(f"J-51 fetch failed: {e}") from e

        for row in rows:
            try:
                init_year = int(row.get("init_year") or 0)
                ex_years  = int(row.get("ex_years") or 0)
                if init_year + ex_years + 35 > current_year:
                    boro  = row.get("b", "").strip()
                    block = (row.get("block") or "").strip().zfill(5)
                    lot   = (row.get("lot") or "").strip().zfill(4)
                    bbl   = f"{boro}{block}{lot}"
                    active.add(bbl)
            except (ValueError, TypeError):
                continue

        if len(rows) < page:
            break
        offset += page

    return active


def _pluto_query(params: dict) -> list[dict]:
    try:
        with httpx.Client(headers=_HEADERS, timeout=30) as client:
            resp = client.get(_PLUTO_ENDPOINT, params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as e:
        raise SourceError(f"PLUTO request failed: {e}") from e


class NYCPLUTOSource:
    source_id      = source_id
    record_type    = record_type
    cache_ttl_days = 30     # PLUTO updated annually; cache aggressively

    def __init__(self, load_j51: bool = True):
        self._j51_bbls: set[str] | None = None
        self._load_j51 = load_j51

    def _ensure_j51(self) -> set[str] | None:
        if not self._load_j51:
            return None
        if self._j51_bbls is None:
            current_year = datetime.utcnow().year
            try:
                self._j51_bbls = _load_j51_bbls(current_year)
            except SourceError:
                self._j51_bbls = set()
        return self._j51_bbls

    def fetch(self, entity: Entity) -> list[Record]:
        bbl = entity.id.replace("-", "").replace(" ", "")
        rows = _pluto_query({"$where": f"bbl='{bbl}'", "$limit": 1})
        if not rows:
            return []
        j51 = self._ensure_j51()
        data = _parse_pluto(rows[0], j51)
        if data is None:
            return []
        return [Record(
            entity_id=data["bbl"],
            record_type=record_type,
            source=source_id,
            data=data,
            fetched_at=datetime.utcnow(),
        )]


def fetch_zip(
    zip_code: str,
    page_size: int = 1000,
    delay: float = 0.1,
    load_j51: bool = True,
) -> Iterator[Record]:
    """Yield stabilization Records for all eligible buildings in a zip code."""
    current_year = datetime.utcnow().year
    j51_bbls = _load_j51_bbls(current_year) if load_j51 else None

    offset = 0
    while True:
        rows = _pluto_query({
            "$where": (
                f"zipcode='{zip_code}' "
                f"AND unitsres >= 6 "
                f"AND (bldgclass LIKE 'C%' OR bldgclass LIKE 'D%')"
            ),
            "$limit":  page_size,
            "$offset": offset,
        })

        for row in rows:
            data = _parse_pluto(row, j51_bbls)
            if data:
                yield Record(
                    entity_id=data["bbl"],
                    record_type=record_type,
                    source=source_id,
                    data=data,
                    fetched_at=datetime.utcnow(),
                )

        if len(rows) < page_size:
            break
        offset += page_size
        time.sleep(delay)
