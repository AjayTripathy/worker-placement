"""
California Proposition 13 cap law (Article XIII A, California Constitution).

Key differences from Michigan MCL 211.27a:
  - AV assessed at 100% of full cash value (no 50% SEV haircut)
  - Annual growth capped at 2% (not lesser of 5%/CPI)
  - On arm's-length transfer: AV resets to full sale price (not SEV)
  - Several statutory exclusions from reassessment (Prop 19, R&T Code §62)
"""
from __future__ import annotations

from datetime import date

from verticals.property_tax.models import Deed, Parcel, Sale

# Document types excluded from reassessment (R&T Code §62 et seq.)
_EXCLUDED_INSTRUMENTS = frozenset({
    "II",    # Interspousal transfer
    "IT",    # Intrafamily transfer
    "TT",    # Trust transfer (revocable living trust)
    "GFT",   # Gift deed
    "INH",   # Inheritance / probate transfer
})

# Terms indicating non-arm's-length family/trust transfers
_EXCLUDED_TERMS = frozenset({
    "GIFT",
    "INTERSPOUSAL",
    "INTRAFAMILY",
    "INTRA-FAMILY",
    "TRUST TRANSFER",
    "REVOCABLE TRUST",
    "INHERITANCE",
    "ESTATE",
    "NO CONSIDERATION",
})


class Prop13CapLaw:
    """
    California Revenue & Taxation Code §§51-68 (Proposition 13, 1978).

    Assessed Value is frozen at the base year value (purchase price) and may
    increase by no more than 2% annually. Change of ownership triggers
    reassessment to current full cash value — the f in Signal = R - f(M).
    """

    ANNUAL_CAP = 0.02  # 2% maximum annual AV increase

    def is_arms_length(self, deed: Deed) -> bool:
        if deed.is_zero_consideration or deed.consideration == 0:
            return False
        if deed.is_quit_claim:
            return False
        instr = (deed.instrument_type or "").upper().strip()
        if instr in _EXCLUDED_INSTRUMENTS:
            return False
        terms = (deed.terms or "").upper()
        return not any(t in terms for t in _EXCLUDED_TERMS)

    def uncap_year(self, transfer_date: date | str) -> int:
        """
        Reassessment takes effect on the January 1 lien date of the tax year
        following the change of ownership.
        """
        year = transfer_date.year if hasattr(transfer_date, "year") else int(str(transfer_date)[:4])
        return year + 1

    def uncap_year_from_year(self, transfer_year: int) -> int:
        return transfer_year + 1

    def expected_tv(self, parcel: Parcel, sale: Sale | Deed) -> float | None:
        """
        After an arm's-length transfer, AV resets to full cash value (= sale price).
        California has no SEV haircut — assessed at 100% of market.
        """
        price = (
            getattr(sale, "consideration", None)
            or getattr(sale, "sale_price", None)
        )
        return float(price) if price and price > 0 else None

    def is_overdue(self, parcel: Parcel, transfer_year: int) -> bool:
        return self.uncap_year_from_year(transfer_year) <= date.today().year
