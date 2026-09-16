MILLAGE_NON_HOMESTEAD = 67.0   # standard non-homestead rate
MILLAGE_HOMESTEAD     = 40.0   # PRE rate (MCL 211.7cc)
MILLAGE_NEZ           = 6.0    # NEZ Homestead rate

SEV_RATIO = 0.5                # SEV = 50% of True Cash Value per Michigan Constitution Art. IX §3

# Gap detection thresholds
SALE_LOOKBACK_YEARS = 3        # only sales within this window trigger overdue/upcoming
CAPPED_THRESHOLD    = 0.92     # TV must be < 92% of SEV to be flagged (filters noise)
MIN_TV_DELTA        = 500      # minimum $500 TV gap to report
