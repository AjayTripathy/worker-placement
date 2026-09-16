"""GARP vertical — growth-at-a-reasonable-price FINDER feeding the R/f(M) growth-trap filter.

Pipeline: universe (Nasdaq, <$15B small/mid) -> multi-year fundamentals (SEC frames,
trailing 3-yr growth) -> composite GARP score (growth x quality x reasonable price) ->
shortlist -> R/f(M) verify the growth is real/organic/durable/cash-backed.

GARP's failure mode is the GROWTH TRAP (decelerating / inorganic / non-cash / estimate-
too-high), the mirror of the value trap. The screen is the finder; the trap-filter is the
judgment. Trailing growth only (no forward analyst estimates without a paid feed).
Reuses verticals.deep_value for the universe + frames helpers. See deep-value memory.
"""
