"""Filing-timeliness — operational/accounting discipline indicator.

Companies that file 10-Ks and 10-Qs on time through cyclical stress demonstrate
working internal controls and a credible finance organization. Streak breaks
(NT filings, large filing-date variance, 10-K/A amendments) indicate
operational/accounting friction.

OUTPUT FIELDS

  on_time_streak_periods: int
    Consecutive 10-K + 10-Q filings ending at cutoff that were filed within
    standard SEC deadlines.

  nt_count_5y: int
    Number of NT 10-K / NT 10-Q filings in the 5-year window ending at cutoff.

  amendment_count_5y: int
    Number of 10-K/A or 10-Q/A filings (often signal restatement / correction).

  median_days_to_file_10k: int
    Median days from period-end to filing-date for 10-Ks in the window.
    Useful for detecting drift even within deadline.

  signal: ON_TIME_STREAK | RECENT_NT_FILING | RECURRING_AMENDMENTS | DRIFTING_TIMING

LIMITATIONS

  - Standard SEC deadlines are filer-status-dependent (Large Accelerated:
    60 days for 10-K, 40 days for 10-Q; Accelerated: 75 / 40; Non-accel: 90
    / 45). This module uses generous 90/45 to avoid false alarms on smaller
    issuers; pair with filer-status detection for tighter precision.
  - NT filings don't always indicate distress (e.g., one-time M&A timing).
    Repeated NT filings or NT + late actual filing is the real signal.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "On-time 10-K/10-Q streak and NT/amendment history as an operational-discipline indicator.",
}

from datetime import date
from typing import Any, Optional

from .. import edgar


DEADLINE_10K_DAYS = 90  # non-accelerated; large-accel is 60
DEADLINE_10Q_DAYS = 45  # non-accelerated; large-accel is 40


def _parse_date(s: str) -> Optional[date]:
    try:
        return date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        return None


def query_filing_timeliness(
    cik: str,
    cutoff_date: str,
    lookback_years: int = 5,
) -> dict[str, Any]:
    """Compute filing-timeliness statistics for the CIK as of cutoff_date.

    Returns a dict with on-time streak, NT count, amendment count, median
    time-to-file, and a categorical signal.
    """
    cutoff = _parse_date(cutoff_date)
    if cutoff is None:
        return {"signal": "ERROR", "_note": f"Could not parse cutoff_date={cutoff_date!r}"}

    try:
        _, filings = edgar.list_filings(cik)
    except Exception as e:
        return {"signal": "ERROR", "_note": f"list_filings failed: {e}"}

    # Filter to pre-cutoff and within lookback window
    start_window = date(cutoff.year - lookback_years, cutoff.month, cutoff.day)
    relevant = []
    for f in filings:
        fd = _parse_date(f.get("filing_date") or "")
        if fd is None or fd > cutoff or fd < start_window:
            continue
        relevant.append({**f, "filing_date_parsed": fd})

    # Categorize
    annual_filings = [f for f in relevant if f.get("form") in ("10-K", "10-K/A")]
    quarterly_filings = [f for f in relevant if f.get("form") in ("10-Q", "10-Q/A")]
    nt_filings = [f for f in relevant if f.get("form", "").startswith("NT")]
    amendments = [f for f in relevant if f.get("form", "").endswith("/A")
                  and f.get("form", "") in ("10-K/A", "10-Q/A")]

    # Time-to-file: filing_date - report_date for 10-K / 10-Q
    days_to_file_10k = []
    days_to_file_10q = []
    on_time_periods = []  # for streak: list of (filing_date, was_on_time)

    # Sort 10-Ks + 10-Qs by filing_date ascending for streak computation
    period_filings = sorted(
        [f for f in relevant if f.get("form") in ("10-K", "10-Q")],
        key=lambda f: f["filing_date_parsed"],
    )

    for f in period_filings:
        rd = _parse_date(f.get("report_date") or "")
        fd = f["filing_date_parsed"]
        if rd is None:
            continue
        days = (fd - rd).days
        if f["form"] == "10-K":
            days_to_file_10k.append(days)
            on_time = days <= DEADLINE_10K_DAYS
        else:
            days_to_file_10q.append(days)
            on_time = days <= DEADLINE_10Q_DAYS
        on_time_periods.append((fd, on_time, f["form"], days))

    # Streak ending at cutoff: count consecutive on-time from the END
    streak = 0
    for fd, on_time, form, days in reversed(on_time_periods):
        if on_time:
            streak += 1
        else:
            break

    # Median days to file
    median_10k = sorted(days_to_file_10k)[len(days_to_file_10k) // 2] if days_to_file_10k else None
    median_10q = sorted(days_to_file_10q)[len(days_to_file_10q) // 2] if days_to_file_10q else None

    # Signal classification
    n_nt = len(nt_filings)
    n_amend = len(amendments)
    most_recent_nt = max((f["filing_date_parsed"] for f in nt_filings), default=None)
    days_since_nt = (cutoff - most_recent_nt).days if most_recent_nt else None

    if days_since_nt is not None and days_since_nt <= 365:
        signal = "RECENT_NT_FILING"
    elif n_amend >= 2:
        signal = "RECURRING_AMENDMENTS"
    elif streak >= 8:
        signal = "ON_TIME_STREAK"
    elif median_10k and median_10k > DEADLINE_10K_DAYS - 7:
        signal = "DRIFTING_TIMING"
    else:
        signal = "ON_TIME_STREAK"

    return {
        "cik": cik,
        "cutoff_date": cutoff_date,
        "on_time_streak_periods": streak,
        "nt_count_5y": n_nt,
        "amendment_count_5y": n_amend,
        "median_days_to_file_10k": median_10k,
        "median_days_to_file_10q": median_10q,
        "most_recent_nt_filing": str(most_recent_nt) if most_recent_nt else None,
        "days_since_most_recent_nt": days_since_nt,
        "n_annual_filings_5y": len(annual_filings),
        "n_quarterly_filings_5y": len(quarterly_filings),
        "signal": signal,
        "_nt_filings": [
            {"form": f["form"], "filing_date": str(f["filing_date_parsed"])}
            for f in nt_filings
        ],
        "_amendment_filings": [
            {"form": f["form"], "filing_date": str(f["filing_date_parsed"])}
            for f in amendments
        ],
    }


if __name__ == "__main__":
    # Quick sanity check
    import json
    # NSP — should show clean streak
    print("NSP (Insperity):")
    print(json.dumps(query_filing_timeliness("0001000753", "2026-05-26"), indent=2))
