from __future__ import annotations

from typing import Protocol

from .models import Deed, Parcel, Sale


class CapLaw(Protocol):
    """
    State-specific property tax cap law.

    Implementors encode the statutory relationship between a transfer event
    and the taxable value reset — the f in Signal = R - f(M).
    """

    def is_arms_length(self, deed: Deed) -> bool:
        """
        Whether a deed transfer triggers an uncap.
        Quit-claims, zero-consideration deeds, and family transfers typically do not.
        """
        ...

    def uncap_year(self, transfer_date) -> int:
        """Tax year in which TV should reset after the transfer."""
        ...

    def expected_tv(self, parcel: Parcel, sale: Sale | Deed) -> float | None:
        """
        The TV that should appear on the roll after an arm's-length transfer.
        Returns None if insufficient data to estimate.
        """
        ...

    def is_overdue(self, parcel: Parcel, transfer_year: int) -> bool:
        """Whether the uncap should have occurred already (transfer_year <= current tax year)."""
        ...
