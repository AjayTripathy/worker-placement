from __future__ import annotations

from datetime import date

from verticals.property_tax.models import Deed, Parcel, Sale

# CPI multipliers published annually by Michigan State Tax Commission
# TV growth is capped at lesser of 5% or CPI multiplier
CPI_MULTIPLIERS: dict[int, float] = {
    2010: 1.017, 2011: 1.027, 2012: 1.016, 2013: 1.024, 2014: 1.016,
    2015: 1.003, 2016: 1.003, 2017: 1.021, 2018: 1.021, 2019: 1.024,
    2020: 1.014, 2021: 1.014, 2022: 1.033, 2023: 1.05,  2024: 1.05,
    2025: 1.05,  2026: 1.05,
}

NOT_ARMS_LENGTH_TERMS = frozenset({
    "NOT USED/OTHER",
    "NOT ARM'S LENGTH",
    "NOT ARMS LENGTH",
    "FAMILY TRANSFER",
    "GOVERNMENTAL TRANSFER",
})

NOT_ARMS_LENGTH_INSTRUMENTS = frozenset({"QC", "QUITCLAIM", "LC", "LAND CONTRACT"})


class MCL211a27CapLaw:
    """
    MCL 211.27a: Taxable Value uncaps to SEV in the tax year following
    an arm's-length transfer of ownership.

    This is the f in Signal = R - f(M) for Michigan property tax.
    """

    def is_arms_length(self, deed: Deed) -> bool:
        if deed.is_zero_consideration or deed.consideration == 0:
            return False
        if deed.is_quit_claim:
            return False
        if deed.instrument_type.upper() in NOT_ARMS_LENGTH_INSTRUMENTS:
            return False
        if deed.terms and deed.terms.upper() in NOT_ARMS_LENGTH_TERMS:
            return False
        return True

    def uncap_year(self, transfer_date: date | str) -> int:
        """TV resets in the tax year *following* the transfer."""
        if isinstance(transfer_date, str):
            year = int(transfer_date[:4])
        else:
            year = transfer_date.year
        return year + 1

    def expected_tv(self, parcel: Parcel, sale: Sale | Deed) -> float | None:
        """
        After an arm's-length transfer, TV should equal SEV in the uncap year.
        SEV is the assessor's 50%-of-market estimate — the legally required reset target.
        """
        if parcel.sev is None:
            return None
        return float(parcel.sev)

    def is_overdue(self, parcel: Parcel, transfer_year: int) -> bool:
        """Uncap is overdue if the reset year is on or before the current tax year."""
        current_tax_year = date.today().year
        return self.uncap_year_from_year(transfer_year) <= current_tax_year

    def uncap_year_from_year(self, transfer_year: int) -> int:
        return transfer_year + 1

    def cpi_cap(self, year: int) -> float:
        return min(CPI_MULTIPLIERS.get(year, 1.05), 1.05)
