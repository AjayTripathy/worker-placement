"""Severity tiers + report rendering shared across backtests."""
from __future__ import annotations

import json
import sys
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    RED_FLAG_NEGATIVE = "RED_FLAG_NEGATIVE"
    SEVERE_UNDERDELIVERY = "SEVERE_UNDERDELIVERY"
    MODERATE_UNDERDELIVERY = "MODERATE_UNDERDELIVERY"
    UNVERIFIABLE = "UNVERIFIABLE"
    PASS = "PASS"


SEVERITY_ORDER = [
    Severity.RED_FLAG_NEGATIVE,
    Severity.SEVERE_UNDERDELIVERY,
    Severity.MODERATE_UNDERDELIVERY,
    Severity.UNVERIFIABLE,
    Severity.PASS,
]


def write_findings(findings: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(exist_ok=True, parents=True)
    out_path.write_text(json.dumps(findings, indent=2, default=str))
    print(f"Saved {len(findings)} findings to {out_path}", file=sys.stderr)


def print_summary(findings: list[dict], cutoff_date: str, ticker: str) -> None:
    counts: dict[str, int] = {}
    for f in findings:
        sev = str(f.get("severity"))
        counts[sev] = counts.get(sev, 0) + 1
    print(f"\n=== {ticker} backtest summary (pre-{cutoff_date} cutoff) ===", file=sys.stderr)
    for sev in SEVERITY_ORDER:
        if sev.value in counts:
            print(f"  {sev.value}: {counts[sev.value]}", file=sys.stderr)
    print(f"  Total claims tested: {len(findings)}", file=sys.stderr)
    contra = sum(1 for f in findings if f.get("M_supports_claim") is False)
    print(f"  Claims contradicted by public records: {contra}", file=sys.stderr)
