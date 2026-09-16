from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class DonatedArtwork(BaseModel):
    """A work currently in a museum's collection received as a gift."""
    museum: str                              # "met" | "moma" | etc.
    object_id: str                           # museum-internal ID
    accession_number: str | None
    accession_year: int | None
    credit_line: str                         # "Gift of [donor name], [year]"
    donor_name_raw: str                      # parsed from credit_line
    donor_name_normalized: str               # for matching/aggregation
    title: str
    artist: str
    classification: str | None               # "Paintings" | "Sculpture" | etc.
    department: str | None
    medium: str | None = None
    object_url: str | None = None
    primary_image: str | None = None


class AuctionLot(BaseModel):
    """A specific lot result from a public auction."""
    house: str                               # "sothebys" | "christies" | "phillips" | "heritage"
    sale_id: str
    sale_date: date | None
    lot_number: str | None
    title: str
    artist: str
    hammer_price: Decimal | None             # USD
    estimate_low: Decimal | None
    estimate_high: Decimal | None
    buyer: str | None                        # rarely public — usually anonymous
    sale_url: str | None = None
    image_url: str | None = None


class DonationGapInput(BaseModel):
    """Composite input passed to gap function."""
    artwork: DonatedArtwork
    matched_lot: Optional[AuctionLot] = None
