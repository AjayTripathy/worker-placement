"""
Rent stabilization gap function.

Signal = listed_rent - max_legal_stabilized_rent

R (regulated): estimated maximum legal stabilized rent, computed from:
    initial_base_rent × cumulative_RGB_factor × vacancy_bonus_allowance

M (market): rent advertised on StreetEasy or other listing sources.

When M > R the landlord may be charging above the legal ceiling — either
through illegal deregulation, IAI fraud, or outright overcharging.

Note on precision:
    Without the actual DHCR-registered base rent for each unit, max_legal_rent
    is an estimate. The estimate is conservative (generous vacancy_bonus_factor)
    to minimise false positives. Signals here are leads for DHCR inquiry, not
    definitive legal findings.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from core.models import Entity, GapResult, Record

from .models import RentListing, StabilizedBuilding
from .rgb_schedule import (
    BASE_RENT_1969,
    HSTPA_YEAR,
    RSL_ENACTMENT_YEAR,
    max_legal_rent,
)

_DEFAULT_MIN_RENT_DELTA = Decimal("500")   # minimum monthly gap to report
_DEFAULT_LOOKBACK_DAYS  = 90               # only consider listings this fresh


class RentStabilizationGapFunction:
    """
    Detects rent overcharges in buildings likely subject to the NYC RSL.

    Computes the estimated maximum legal stabilized rent from building
    vintage and RGB history, then compares to listed market rent.
    """

    def __init__(
        self,
        min_rent_delta: Decimal = _DEFAULT_MIN_RENT_DELTA,
        lookback_days: int = _DEFAULT_LOOKBACK_DAYS,
        vacancy_bonus_factor: Decimal = Decimal("1.5"),
    ):
        self.min_rent_delta = min_rent_delta
        self.lookback_days  = lookback_days
        self.vacancy_bonus_factor = vacancy_bonus_factor

    def compute(self, entity: Entity, records: list[Record]) -> GapResult | None:
        building = _extract_building(records)
        if building is None:
            return None

        if building.stabilization_confidence < 0.4:
            return None  # too uncertain to signal

        listings = _extract_listings(records, self.lookback_days)
        if not listings:
            return None  # no market data — nothing to compare

        current_year = date.today().year
        max_rent = _estimate_max_legal_rent(building, current_year, self.vacancy_bonus_factor)
        if max_rent is None:
            return None

        # Use the highest listed rent as the market signal (most suspicious)
        best_listing = max(listings, key=lambda l: l.listed_rent)
        listed = best_listing.listed_rent

        raw_gap = listed - max_rent
        if raw_gap < self.min_rent_delta:
            return None  # gap too small or negative

        data_quality = _assess_quality(building, best_listing)
        flags = []
        if building.stabilization_status == "likely":
            flags.append("inferred_stabilization")
        if building.owner_is_entity:
            flags.append("entity_owner")

        return GapResult(
            entity_id=entity.id,
            regulated_value=max_rent,
            market_value=listed,
            expected_regulated=max_rent,
            raw_gap=raw_gap,
            gap_pct=float(raw_gap / max_rent) if max_rent else 0.0,
            gap_direction="overcharge",
            data_quality_flags=flags,
            metadata={
                "stabilization_status":     building.stabilization_status,
                "stabilization_confidence": building.stabilization_confidence,
                "base_year":                building.base_year,
                "base_rent_estimate":       float(building.base_rent_estimate) if building.base_rent_estimate else None,
                "max_legal_rent":           float(max_rent),
                "listed_rent":              float(listed),
                "listing_unit":             best_listing.unit,
                "listing_source":           best_listing.source,
                "listing_date":             str(best_listing.listing_date),
                "num_listings":             len(listings),
                "bedrooms":                 best_listing.bedrooms,
                "owner":                    building.owner,
                "owner_is_entity":          building.owner_is_entity,
                "borough":                  building.borough,
                "year_built":               building.year_built,
                "unitsres":                 building.unitsres,
                "exemption_type":           building.exemption_type,
                "data_quality":             data_quality,
                "address":                  building.address,
                "zip_code":                 building.zip_code,
            },
        )


def _estimate_max_legal_rent(
    building: StabilizedBuilding,
    current_year: int,
    vacancy_bonus_factor: Decimal,
) -> Decimal | None:
    """
    Conservative upper bound on the maximum legal stabilized rent.

    Uses the building's known base_rent_estimate and base_year. Falls back
    to borough-calibrated 1969 base if neither is known.
    """
    base_rent = building.base_rent_estimate
    base_year = building.base_year

    if base_rent is None or base_year is None:
        # Infer from borough + RSL enactment
        base_rent = BASE_RENT_1969.get(building.borough, Decimal("100"))
        base_year = RSL_ENACTMENT_YEAR

    if base_year >= current_year:
        return None

    return max_legal_rent(base_rent, base_year, current_year, vacancy_bonus_factor)


def _assess_quality(building: StabilizedBuilding, listing: RentListing) -> str:
    if building.stabilization_status in ("j51_confirmed", "421a_confirmed"):
        return "confirmed_obligation"
    if building.stabilization_confidence >= 0.8:
        return "high_confidence_inferred"
    if building.stabilization_confidence >= 0.6:
        return "medium_confidence_inferred"
    return "low_confidence_inferred"


def _extract_building(records: list[Record]) -> StabilizedBuilding | None:
    for r in records:
        if r.record_type == "stabilization":
            try:
                return StabilizedBuilding(**r.data)
            except Exception:
                pass
    return None


def _extract_listings(records: list[Record], lookback_days: int) -> list[RentListing]:
    cutoff = date.today().toordinal() - lookback_days
    out = []
    for r in records:
        if r.record_type == "listing":
            try:
                listing = RentListing(**r.data)
                if listing.listing_date.toordinal() >= cutoff:
                    out.append(listing)
            except Exception:
                pass
    return out
