"""Reusable harness for short-thesis backtests against SEC filings.

Per-ticker configuration lives in `backtest.configs.<ticker>` and declares:
    CIK              str    EDGAR CIK (zero-padded)
    TICKER           str    short identifier used for output dirs
    CUTOFF_DATE      str    YYYY-MM-DD; filings strictly before this date are admissible
    PRIORITY_FORMS   set    form types to download as raw text for self-text scoring
    CLAIMS           list   curated claim dicts (claim_id, claim_text, M_sources, ...)
    M_QUERIES        list   (key, callable, kwargs) — each runs once and is stashed under `key`
    SCORERS          dict   claim_id -> callable(evidence, claim) -> finding dict
"""
