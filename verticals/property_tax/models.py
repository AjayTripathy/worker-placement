from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator


class Parcel(BaseModel):
    parcel_id: str
    address: str
    zip_code: str
    owner: str | None = None
    owner_is_entity: bool = False
    sev: Decimal | None = None              # State Equalized Value (assessor's 50%-of-market)
    taxable_value: Decimal | None = None    # current capped TV — the regulated record R
    homestead_pct: float | None = None      # PRE % — 100 = full homestead
    nez_district: str | None = None
    tax_status: str | None = None           # "TAXABLE", "EXEMPT"
    transfer_date: date | None = None
    sale_price_record: Decimal | None = None
    property_class: str | None = None
    use_code: str | None = None
    extra: dict = {}

    @field_validator("taxable_value", "sev", "sale_price_record", mode="before")
    @classmethod
    def coerce_decimal(cls, v):
        if v is None or v == "":
            return None
        return Decimal(str(v))


class Sale(BaseModel):
    parcel_id: str
    sale_date: date
    sale_price: Decimal | None = None
    source: str
    is_arms_length: bool | None = None     # None = unknown, requires classification

    @field_validator("sale_price", mode="before")
    @classmethod
    def coerce_decimal(cls, v):
        if v is None or v == "":
            return None
        return Decimal(str(v))


class Deed(BaseModel):
    parcel_id: str
    sale_date: date
    grantor: str
    grantee: str
    instrument_type: str                    # "WD", "QC", "LC", etc.
    consideration: Decimal
    liber_page: str = ""
    is_quit_claim: bool = False
    is_zero_consideration: bool = False
    terms: str | None = None               # "ARM'S LENGTH", "NOT ARM'S LENGTH", etc.

    @field_validator("consideration", mode="before")
    @classmethod
    def coerce_decimal(cls, v):
        if v is None or v == "":
            return Decimal(0)
        return Decimal(str(v))
