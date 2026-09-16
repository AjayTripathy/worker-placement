from decimal import Decimal

# California property tax rate: 1% base (Prop 13) + local levies (bonds, etc.)
# Typical effective rate in LA County is 1.2–1.3%; use 12 mills as conservative estimate.
MILLAGE_STANDARD = 12.0       # 1.2% of AV (1.0% Prop 13 base + 0.2% average local levies)

# California assesses at 100% of full cash value — no SEV ratio haircut
AV_RATIO = Decimal("1.0")

# Gap detection thresholds
# CA property values are much higher than Detroit; use larger minimums to suppress noise
SALE_LOOKBACK_YEARS = 3       # same lookback window as Michigan
CAPPED_THRESHOLD    = 0.85    # flag if AV < 85% of expected post-transfer AV
MIN_AV_DELTA        = Decimal("10000")  # minimum $10K gap to report
