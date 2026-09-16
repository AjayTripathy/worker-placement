from decimal import Decimal

# Minimum monthly rent gap to surface as a signal
MIN_RENT_DELTA = Decimal("500")

# Listing freshness window — ignore listings older than this
LISTING_LOOKBACK_DAYS = 90

# Vacancy-bonus / IAI allowance multiplier applied on top of pure RGB compounding.
# 1.5 means we allow the legal rent to be up to 50% above the pure RGB calculation,
# accounting for vacancy bonuses (pre-2019) and individual apartment improvements.
# This is conservative — it reduces false positives at the cost of missing smaller gaps.
VACANCY_BONUS_FACTOR = Decimal("1.5")
