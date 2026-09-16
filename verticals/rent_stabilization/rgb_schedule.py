"""
NYC Rent Guidelines Board (RGB) annual 1-year lease renewal increases.

Source: NYC RGB Orders 1–57 (1969–2025).
Rates are the effective percentage increases for 1-year leases signed
between October 1 of the given year and September 30 of the following year.

Also includes borough-calibrated initial stabilized rent estimates (1969)
for use when the actual DHCR-registered base rent is not available.
The estimates are derived from DHCR published median stabilized rents
back-calculated using the cumulative RGB factor.
"""
from __future__ import annotations

from decimal import Decimal

# 1-year lease renewal rates by RGB order year (October effective date)
RGB_1YR: dict[int, float] = {
    1969: 0.150,   # Order 1
    1970: 0.025,   # Order 2
    1971: 0.000,   # Order 3
    1972: 0.025,   # Order 4
    1973: 0.010,   # Order 5
    1974: 0.060,   # Order 6
    1975: 0.080,   # Order 7
    1976: 0.060,   # Order 8
    1977: 0.040,   # Order 9
    1978: 0.055,   # Order 10
    1979: 0.085,   # Order 11
    1980: 0.090,   # Order 12
    1981: 0.100,   # Order 13
    1982: 0.070,   # Order 14
    1983: 0.040,   # Order 15
    1984: 0.040,   # Order 16
    1985: 0.040,   # Order 17
    1986: 0.035,   # Order 18
    1987: 0.030,   # Order 19
    1988: 0.025,   # Order 20
    1989: 0.025,   # Order 21
    1990: 0.025,   # Order 22
    1991: 0.025,   # Order 23
    1992: 0.000,   # Order 24
    1993: 0.000,   # Order 25
    1994: 0.000,   # Order 26
    1995: 0.020,   # Order 27
    1996: 0.025,   # Order 28
    1997: 0.025,   # Order 29
    1998: 0.020,   # Order 30
    1999: 0.020,   # Order 31
    2000: 0.040,   # Order 32
    2001: 0.040,   # Order 33
    2002: 0.020,   # Order 34
    2003: 0.045,   # Order 35
    2004: 0.030,   # Order 36
    2005: 0.035,   # Order 37
    2006: 0.035,   # Order 38
    2007: 0.030,   # Order 39
    2008: 0.045,   # Order 40
    2009: 0.030,   # Order 41
    2010: 0.0225,  # Order 42
    2011: 0.0375,  # Order 43
    2012: 0.020,   # Order 44
    2013: 0.040,   # Order 45
    2014: 0.010,   # Order 46
    2015: 0.000,   # Order 47
    2016: 0.000,   # Order 48
    2017: 0.0125,  # Order 49
    2018: 0.015,   # Order 50
    2019: 0.015,   # Order 51
    2020: 0.000,   # Order 52  (COVID relief)
    2021: 0.000,   # Order 53  (COVID — 0% first year of 2yr = 0%/1.5%)
    2022: 0.0325,  # Order 54
    2023: 0.030,   # Order 55
    2024: 0.0275,  # Order 56
    2025: 0.025,   # Order 57  (effective Oct 2025)
}

# Cumulative RGB factor from 1969 to current year (precomputed for speed)
def _cumulative_factor(from_year: int, to_year: int) -> Decimal:
    """Product of (1 + rate) for each year in [from_year, to_year)."""
    factor = Decimal("1")
    for yr in range(from_year, to_year):
        rate = RGB_1YR.get(yr, 0.0)
        factor *= Decimal(str(1 + rate))
    return factor


def max_legal_rent(
    base_rent: Decimal,
    base_year: int,
    current_year: int,
    vacancy_bonus_factor: Decimal = Decimal("1.5"),
) -> Decimal:
    """
    Estimate the maximum possible legal stabilized rent in current_year.

    base_rent: initial registered legal rent at base_year
    base_year: year RGB compounding starts (year the unit first became stabilized)
    current_year: year to compute max for
    vacancy_bonus_factor: multiplier accounting for vacancy bonuses and IAI
        increases over the unit's history. 1.5 = 50% over pure RGB (conservative
        upper bound that encompasses most legitimate increases).

    This is an ESTIMATE, not the authoritative DHCR legal regulated rent.
    The authoritative value requires the DHCR rent registration record.
    """
    rgb_factor = _cumulative_factor(base_year, current_year)
    return (base_rent * rgb_factor * vacancy_bonus_factor).quantize(Decimal("0.01"))


# Borough-calibrated base rent estimates for 1969 (year of RSL enactment).
# Derived by back-calculating from DHCR 2023 median stabilized rents using
# the cumulative RGB factor (~5.85×). Represents the median initial rent
# for a ~1BR unit in a pre-war building in that borough.
BASE_RENT_1969: dict[str, Decimal] = {
    "manhattan":    Decimal("145"),
    "brooklyn":     Decimal("105"),
    "queens":       Decimal("100"),
    "bronx":        Decimal("85"),
    "staten_island": Decimal("90"),
}

BOROUGH_CODES = {
    "1": "manhattan",
    "2": "bronx",
    "3": "brooklyn",
    "4": "queens",
    "5": "staten_island",
    "MN": "manhattan",
    "BX": "bronx",
    "BK": "brooklyn",
    "QN": "queens",
    "SI": "staten_island",
}

RSL_ENACTMENT_YEAR = 1969   # NYC Rent Stabilization Law effective year
HSTPA_YEAR = 2019           # Housing Stability & Tenant Protection Act — no new deregulations
HIGH_RENT_DEREGULATION_THRESHOLD = Decimal("2500")  # pre-HSTPA threshold (monthly)
