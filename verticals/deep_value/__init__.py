"""Deep-value vertical — a composite cheap-stock FINDER feeding the R/f(M) trap-filter.

Pipeline: universe (Nasdaq screener) -> fundamentals (SEC frames, TTM) -> composite
score -> shortlist -> R/f(M) recompute-from-latest-10-Q trap-filter.

Value is the finder (what's cheap); R/f(M) is the verifier (is the cheapness REAL).
The screen is intentionally loose; the judgment lives in the trap-filter. See
memory project_deep_value_vertical.
"""
