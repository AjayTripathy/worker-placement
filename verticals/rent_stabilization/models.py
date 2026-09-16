from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, field_validator


class StabilizedBuilding(BaseModel):
    bbl: str
    address: str
    borough: str                        # "manhattan", "brooklyn", "queens", "bronx", "staten_island"
    zip_code: str
    unitsres: int                       # total residential units
    year_built: int
    bldg_class: str                     # NYC building class code (C1-C9, D1-D9, etc.)
    tax_class: str                      # "2", "2A", "2B", "2C"
    owner: str
    owner_is_entity: bool
    # stabilization status
    stabilization_status: str           # "likely", "j51_confirmed", "421a_confirmed", "exempt"
    stabilization_confidence: float     # 0.0–1.0
    base_rent_estimate: Decimal | None  # estimated initial legal rent at base_year
    base_year: int | None               # year RGB compounding starts from
    # J-51 / 421-a enrichment
    exemption_type: str | None          # "j51", "421a", None
    exemption_init_year: int | None
    exemption_duration_years: int | None
    extra: dict = {}

    @field_validator("base_rent_estimate", mode="before")
    @classmethod
    def coerce_decimal(cls, v):
        if v is None or v == "":
            return None
        return Decimal(str(v))


class RentListing(BaseModel):
    bbl: str
    address: str
    unit: str | None = None
    listed_rent: Decimal
    bedrooms: int                       # 0=studio, 1=1BR, 2=2BR, etc.
    listing_date: date
    source: str                         # "streeteasy", "zillow", "craigslist"

    @field_validator("listed_rent", mode="before")
    @classmethod
    def coerce_decimal(cls, v):
        return Decimal(str(v))
