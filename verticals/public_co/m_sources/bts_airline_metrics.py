"""BTS airline operational metrics — T-100, Form 41, On-Time Performance.

WHY THIS EXISTS

Airlines telegraph distress through operational metrics months before
the financial impact appears in 10-Q earnings:
  - Load factor declining while ASMs grow → demand softening
  - On-time performance falling → operational discipline cracking
  - Stage length / fleet utilization shifts → strategy changes

The Bureau of Transportation Statistics (BTS) publishes monthly carrier
operational data through TranStats. Free, well-structured. The two
datasets most useful for catastrophe-detection:

  1. T-100 Segment (US Carriers) — monthly RPM, ASM, load factor,
     departures by carrier-origin-destination
  2. On-Time Performance (DOT BTS) — monthly arrival delays, cancellations

We use the carrier-month aggregate via the BTS API
(https://www.transtats.bts.gov/Data_Elements.aspx?Data=2) when
available, falling back to the per-airport CSV downloads.

IMPLEMENTATION

For the IJR backtest we need quarterly aggregated metrics by IATA code.
We don't ship a full BTS scraper here — we use the publicly accessible
TranStats DB1B summary feed via the simplest possible route: BTS's
'Air Carrier Statistics' Time Series endpoint, which returns monthly
totals by carrier in CSV.

INPUTS

  carrier_iata: 2-letter IATA code (AS=Alaska, DL=Delta, AA=American,
                UA=United, SKW=SkyWest, F9=Frontier, SAVE=Spirit etc.)
  cutoff_date: ISO YYYY-MM-DD; latest month for trailing-12m aggregation

OUTPUT

  signal: STRONG | STABLE | SOFTENING | DETERIORATING | UNVERIFIABLE
  metrics: {load_factor_ttm, load_factor_yoy_delta_pp,
            asm_yoy_pct, otp_arrival_pct_ttm, otp_yoy_delta_pp}

THRESHOLDS

  load_factor YoY delta (pp):
    >= +1     → STRONG
    -1 to +1  → STABLE
    -3 to -1  → SOFTENING
    < -3      → DETERIORATING

  OTP YoY delta (pp):
    >= +2     → STRONG
    -2 to +2  → STABLE
    -5 to -2  → SOFTENING
    < -5      → DETERIORATING

Worst tier wins.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["451"],
    "issuer_features": ["airline_operator"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "BTS T-100/Form-41/on-time data; load factor and ops metrics telegraph airline distress before the 10-Q.",
}

from datetime import date
from typing import Any, Optional

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

_SEVERITY_MAP = {
    "STRONG":         "PASS",
    "STABLE":         "PASS",
    "SOFTENING":      "MODERATE_UNDERDELIVERY",
    "DETERIORATING":  "SEVERE_UNDERDELIVERY",
    "UNVERIFIABLE":   "UNVERIFIABLE",
}

# BTS Time Series CSV downloads via the public API gateway.
# These endpoints accept POSTed form parameters; the easier route is the
# TranStats "T-100 Domestic Segment U.S. Carriers" prefab CSV with date
# range. The API surface is finicky in 2026 — we wrap calls to allow
# pre-cached CSVs at data/_bts/<carrier>.csv as the primary path.
from pathlib import Path
CACHE_DIR = Path(__file__).parent.parent / "data" / "_bts"


def _local_carrier_panel(carrier_iata: str) -> Optional[list[dict]]:
    """Read a pre-cached monthly panel from data/_bts/<carrier>.csv.

    Expected schema (header row):
      year,month,passengers,seats,asm,rpm,otp_arrival_pct
    """
    f = CACHE_DIR / f"{carrier_iata.upper()}.csv"
    if not f.exists():
        return None
    import csv
    rows = []
    with f.open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                rows.append({
                    "year":              int(r["year"]),
                    "month":             int(r["month"]),
                    "passengers":        float(r.get("passengers") or 0) or None,
                    "seats":             float(r.get("seats") or 0) or None,
                    "asm":               float(r.get("asm") or 0) or None,
                    "rpm":               float(r.get("rpm") or 0) or None,
                    "otp_arrival_pct":   float(r.get("otp_arrival_pct") or "nan"),
                })
            except (KeyError, ValueError):
                continue
    rows.sort(key=lambda r: (r["year"], r["month"]))
    return rows


def _filter_to_window(rows: list[dict], end: date, months: int) -> list[dict]:
    start_y = end.year - (months // 12)
    start_m = end.month
    while start_m <= 0:
        start_m += 12
        start_y -= 1
    cutoff_key = (end.year, end.month)
    start_key = (start_y, start_m)
    return [r for r in rows if start_key <= (r["year"], r["month"]) <= cutoff_key]


def _sum_or_none(rows: list[dict], field: str) -> Optional[float]:
    vals = [r.get(field) for r in rows if r.get(field) is not None]
    return sum(vals) if vals else None


def _mean_or_none(rows: list[dict], field: str) -> Optional[float]:
    vals = [r[field] for r in rows
            if r.get(field) is not None and r[field] == r[field]]  # NaN-safe
    return sum(vals) / len(vals) if vals else None


def query_airline_metrics(carrier_iata: str, cutoff_date: str) -> dict[str, Any]:
    """Compute load-factor + OTP YoY drift for a carrier.

    Currently reads local pre-cached BTS panels. Returns UNVERIFIABLE
    when no cache exists for the carrier.
    """
    try:
        cutoff = date.fromisoformat(cutoff_date[:10])
    except (ValueError, TypeError):
        return {"signal": "UNVERIFIABLE", "severity": "UNVERIFIABLE",
                "direction": "neutral", "_note": f"bad cutoff {cutoff_date}"}

    rows = _local_carrier_panel(carrier_iata)
    if not rows:
        return {
            "carrier_iata":  carrier_iata,
            "signal":        "UNVERIFIABLE",
            "severity":      _SEVERITY_MAP["UNVERIFIABLE"],
            "direction":     "neutral",
            "_note": (
                f"No local BTS panel at {CACHE_DIR}/{carrier_iata.upper()}.csv. "
                "Populate from TranStats (T-100 Segment + OTP Carrier Performance) "
                "with schema: year,month,passengers,seats,asm,rpm,otp_arrival_pct."
            ),
        }

    last_12m = _filter_to_window(rows, cutoff, 12)
    prev_12m = _filter_to_window(
        rows,
        date(cutoff.year - 1, cutoff.month, 1),
        12,
    )

    if not last_12m:
        return {"carrier_iata": carrier_iata, "signal": "UNVERIFIABLE",
                "severity": "UNVERIFIABLE", "direction": "neutral",
                "_note": "Cache present but no data in TTM window."}

    asm_now = _sum_or_none(last_12m, "asm")
    asm_prev = _sum_or_none(prev_12m, "asm")
    rpm_now = _sum_or_none(last_12m, "rpm")
    rpm_prev = _sum_or_none(prev_12m, "rpm")
    otp_now = _mean_or_none(last_12m, "otp_arrival_pct")
    otp_prev = _mean_or_none(prev_12m, "otp_arrival_pct")

    lf_now = (rpm_now / asm_now * 100.0) if (asm_now and rpm_now) else None
    lf_prev = (rpm_prev / asm_prev * 100.0) if (asm_prev and rpm_prev) else None
    lf_delta = (lf_now - lf_prev) if (lf_now is not None and lf_prev is not None) else None
    otp_delta = (otp_now - otp_prev) if (otp_now is not None and otp_prev is not None) else None
    asm_yoy = (100.0 * (asm_now - asm_prev) / asm_prev) if (asm_now and asm_prev) else None

    def _classify_lf(d):
        if d is None: return "UNVERIFIABLE"
        if d >= 1: return "STRONG"
        if d >= -1: return "STABLE"
        if d >= -3: return "SOFTENING"
        return "DETERIORATING"

    def _classify_otp(d):
        if d is None: return "UNVERIFIABLE"
        if d >= 2: return "STRONG"
        if d >= -2: return "STABLE"
        if d >= -5: return "SOFTENING"
        return "DETERIORATING"

    rank = {"STRONG": 0, "STABLE": 1, "SOFTENING": 2, "DETERIORATING": 3, "UNVERIFIABLE": -1}
    by_rank = {v: k for k, v in rank.items() if v >= 0}

    lf_tier = _classify_lf(lf_delta)
    otp_tier = _classify_otp(otp_delta)
    valid = [rank[t] for t in (lf_tier, otp_tier) if rank[t] >= 0]
    signal = by_rank[max(valid)] if valid else "UNVERIFIABLE"

    direction = (
        "positive" if signal in ("STRONG", "STABLE")
        else "negative" if signal in ("SOFTENING", "DETERIORATING")
        else "neutral"
    )

    return {
        "carrier_iata":  carrier_iata,
        "cutoff_date":   cutoff_date,
        "signal":        signal,
        "severity":      _SEVERITY_MAP[signal],
        "direction":     direction,
        "metrics": {
            "load_factor_ttm_pct":     round(lf_now, 2) if lf_now is not None else None,
            "load_factor_yoy_delta_pp": round(lf_delta, 2) if lf_delta is not None else None,
            "load_factor_tier":         lf_tier,
            "asm_yoy_pct":              round(asm_yoy, 2) if asm_yoy is not None else None,
            "otp_arrival_pct_ttm":      round(otp_now, 2) if otp_now is not None else None,
            "otp_yoy_delta_pp":         round(otp_delta, 2) if otp_delta is not None else None,
            "otp_tier":                 otp_tier,
        },
        "_note": (
            f"LF TTM {lf_now:.1f}% (YoY {lf_delta:+.1f}pp); "
            f"OTP {otp_now:.1f}% (YoY {otp_delta:+.1f}pp)."
            if all(v is not None for v in (lf_now, lf_delta, otp_now, otp_delta))
            else "Partial BTS metrics; some tiers UNVERIFIABLE."
        ),
    }


if __name__ == "__main__":
    import json
    import sys
    iata = sys.argv[1] if len(sys.argv) > 1 else "AS"
    cutoff = sys.argv[2] if len(sys.argv) > 2 else "2024-05-15"
    print(json.dumps(query_airline_metrics(iata, cutoff), indent=2, default=str))
