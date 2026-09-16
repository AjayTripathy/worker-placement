"""CMS Medicare cost reports — HCRIS data for hospitals / SNFs / home health.

WHY THIS EXISTS

Healthcare operators (ENSG, NHC, SEM, ADUS, PRVA) and their REIT
landlords (CTRE, MPW, healthcare-tenants of IIPR) all live or die by
Medicare margins. CMS HCRIS publishes facility-level cost reports
annually — the Form 2552 (hospital), 2540 (SNF), and 1728 (home health)
data files contain revenue mix, Medicare days, operating expenses, and
net income per facility.

Aggregating across an operator's facility roster gives a deterministic
read on segment margin trends without trusting the 10-K narrative. A
multi-year decline in Medicare margin to <0% is the catastrophe pattern
that Steward Health Care exhibited 18 months before MPW disclosure.

DATA SOURCE

CMS Open Data Portal datasets (stable UUIDs as of 2026):
  Hospital  (Form 2552-10): c40fae1f-99a7-4d7f-b94e-fa9989b3c486
  SNF       (Form 2540-10): 56a8a4cb-2cc4-43b1-8eee-b2dfe2c92bda
  Home Hlth (Form 1728-94): cea7ec1e-6c4c-4866-934d-7a5d8b3e6c4a

The CMS Open Data API supports filter queries with up to 5000 rows per
page. We join by CCN (CMS Certification Number) — the canonical
6-digit Medicare provider ID. Issuers disclose their CCNs in 10-K
supplemental schedules or you can join via the Provider of Services
(POS) file by facility name + state.

PUBLIC NAME LOOKUP

For v1 this m-source accepts either:
  - a list of known CCNs (preferred)
  - a substring of provider_name to fuzzy-match against the POS file

OUTPUT

  signal: HEALTHY | STABLE | COMPRESSED | DETERIORATING | UNVERIFIABLE
  metrics: {n_ccns_searched, n_facilities_with_data, latest_fiscal_year,
            weighted_operating_margin_pct, yoy_delta_pp}

THRESHOLDS (NPR-weighted operating margin = Net Income from Service / Net Patient Revenue)

  >= +5%        → HEALTHY
  0 to +5%      → STABLE
  -5 to 0%      → COMPRESSED
  < -5%         → DETERIORATING

YoY delta < -3 pp also forces at least COMPRESSED.

We use operating margin rather than pure Medicare margin because CMS
Open Data exposes the rolled-up cost-report summaries, not the Worksheet-E
Medicare-cost split. The operating margin captures the same catastrophe
pattern — facilities going negative on operations.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["80", "806", "805"],
    "issuer_features": ["healthcare_operator", "healthcare_reit_landlord"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "CMS HCRIS cost reports; facility-level Medicare margins adjudicate operator/landlord narratives deterministically.",
}

from pathlib import Path
from typing import Any, Iterable, Optional

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

# Live UUIDs as of 2026-05-26 (verified via https://data.cms.gov/data.json).
# CMS reissues UUIDs occasionally; re-query data.json if these 404.
DATASETS = {
    "hospital":    "44060663-47d8-4ced-a115-b53b4c270acb",
    "snf":         "a69d3df7-3f66-4a0d-b5b8-0d66049bd565",
    "home_health": "4999da74-1d8d-4a6f-934e-2d7ea470cc63",
}

_SEVERITY_MAP = {
    "HEALTHY":        "PASS",
    "STABLE":         "PASS",
    "COMPRESSED":     "MODERATE_UNDERDELIVERY",
    "DETERIORATING":  "SEVERE_UNDERDELIVERY",
    "UNVERIFIABLE":   "UNVERIFIABLE",
}

CACHE_DIR = Path(__file__).parent.parent / "data" / "_cms_hcris"


def _api_url(dataset_uuid: str) -> str:
    return f"https://data.cms.gov/data-api/v1/dataset/{dataset_uuid}/data"


def _fetch_cost_reports(
    dataset_uuid: str,
    ccns: list[str],
    fiscal_year_end_max: Optional[str] = None,
    *,
    page_size: int = 1000,
) -> list[dict]:
    """Pull cost-report rows for the given CCNs from CMS Open Data.

    CMS Open Data column names are human-readable with spaces and Title
    Case (e.g., 'Provider CCN', 'Fiscal Year End Date', 'Net Income from
    service to patients'). httpx URL-encodes filter param keys correctly.
    """
    if not ccns:
        return []
    all_rows: list[dict] = []
    try:
        with httpx.Client(headers=HEADERS, timeout=60) as c:
            for ccn in ccns:
                params = {
                    "filter[Provider CCN]": str(ccn).zfill(6),
                    "size": page_size,
                }
                r = c.get(_api_url(dataset_uuid), params=params)
                if r.status_code != 200:
                    continue
                rows = r.json()
                if not isinstance(rows, list):
                    continue
                if fiscal_year_end_max:
                    rows = [
                        row for row in rows
                        if (row.get("Fiscal Year End Date") or "")[:10]
                        <= fiscal_year_end_max
                    ]
                all_rows.extend(rows)
    except httpx.HTTPError:
        return all_rows
    return all_rows


def _safe_float(v) -> Optional[float]:
    try:
        if v in (None, ""):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _operating_margin(row: dict) -> Optional[float]:
    """Operating margin = Net Income from service to patients / Net Patient Revenue.

    Preferred over total Net Income (which includes non-operating items like
    investment gains and grants). Returns None if either is missing or NPR≤0.
    """
    ni  = _safe_float(row.get("Net Income from service to patients"))
    npr = _safe_float(row.get("Net Patient Revenue"))
    if ni is None or npr is None or npr <= 0:
        return None
    return (ni / npr) * 100.0


def query_operator_margin(
    operator_name: str,
    ccns: list[str],
    cutoff_date: str,
    *,
    facility_type: str = "snf",
) -> dict[str, Any]:
    """Aggregate Medicare margin across an operator's facility CCNs.

    Args:
      operator_name: company name (for echo).
      ccns: list of CMS Certification Numbers (6-digit strings).
      cutoff_date: ISO YYYY-MM-DD; only fiscal years ending on/before this.
      facility_type: "hospital" | "snf" | "home_health".

    Returns: standard signal + metrics dict.
    """
    if facility_type not in DATASETS:
        return {"signal": "UNVERIFIABLE", "severity": "UNVERIFIABLE",
                "direction": "neutral",
                "_note": f"Unknown facility_type {facility_type!r}; "
                          f"choose from {list(DATASETS)}."}

    if not ccns:
        return {"signal": "UNVERIFIABLE", "severity": "UNVERIFIABLE",
                "direction": "neutral",
                "_note": "No CCNs provided; extract from issuer's 10-K "
                          "facility schedule or join via CMS Provider of Services file."}

    rows = _fetch_cost_reports(DATASETS[facility_type], ccns,
                               fiscal_year_end_max=cutoff_date)
    if not rows:
        return {"operator_name": operator_name,
                "facility_type": facility_type,
                "signal": "UNVERIFIABLE",
                "severity": "UNVERIFIABLE",
                "direction": "neutral",
                "n_ccns_searched": len(ccns),
                "_note": "No cost-report rows returned for these CCNs (dataset UUID may have changed, or CCNs invalid)."}

    # Group by fiscal_year_end → aggregate weighted margin
    by_year: dict[str, list[dict]] = {}
    for r in rows:
        fy = (r.get("Fiscal Year End Date") or "")[:10]
        if not fy:
            continue
        by_year.setdefault(fy[:4], []).append(r)

    if not by_year:
        return {"operator_name": operator_name, "signal": "UNVERIFIABLE",
                "severity": "UNVERIFIABLE", "direction": "neutral",
                "_note": "Cost reports returned but no Fiscal Year End Date values."}

    sorted_years = sorted(by_year.keys())
    latest_year = sorted_years[-1]
    prev_year = sorted_years[-2] if len(sorted_years) >= 2 else None

    def _weighted_margin(year_rows: list[dict]) -> Optional[float]:
        contribs = []
        weights = []
        for r in year_rows:
            m = _operating_margin(r)
            w = _safe_float(r.get("Net Patient Revenue"))
            if m is None or w is None or w <= 0:
                continue
            contribs.append(m * w)
            weights.append(w)
        if not weights:
            return None
        return sum(contribs) / sum(weights)

    margin_latest = _weighted_margin(by_year[latest_year])
    margin_prev   = _weighted_margin(by_year[prev_year]) if prev_year else None
    margin_delta  = (margin_latest - margin_prev) if (margin_latest is not None and margin_prev is not None) else None

    if margin_latest is None:
        signal = "UNVERIFIABLE"
    elif margin_delta is not None and margin_delta < -3:
        signal = "COMPRESSED" if margin_latest >= -5 else "DETERIORATING"
    elif margin_latest >= 5:
        signal = "HEALTHY"
    elif margin_latest >= 0:
        signal = "STABLE"
    elif margin_latest >= -5:
        signal = "COMPRESSED"
    else:
        signal = "DETERIORATING"

    direction = (
        "positive" if signal in ("HEALTHY", "STABLE")
        else "negative" if signal in ("COMPRESSED", "DETERIORATING")
        else "neutral"
    )

    return {
        "operator_name":  operator_name,
        "facility_type":  facility_type,
        "cutoff_date":    cutoff_date,
        "signal":         signal,
        "severity":       _SEVERITY_MAP[signal],
        "direction":      direction,
        "metrics": {
            "n_ccns_searched":              len(ccns),
            "n_facilities_with_data":       sum(len(v) for v in by_year.values()),
            "latest_fiscal_year":           latest_year,
            "prev_fiscal_year":             prev_year,
            "weighted_operating_margin_pct": round(margin_latest, 2) if margin_latest is not None else None,
            "yoy_delta_pp":                  round(margin_delta, 2) if margin_delta is not None else None,
        },
        "_note": (
            f"{facility_type.upper()} weighted operating margin (NPR-weighted) "
            f"{margin_latest:.1f}% (YoY {margin_delta:+.1f}pp); "
            f"latest FY {latest_year}, {sum(len(v) for v in by_year.values())} facility-years."
            if margin_latest is not None and margin_delta is not None
            else f"Latest FY {latest_year}; partial margin coverage."
        ),
    }


if __name__ == "__main__":
    import json
    import sys
    # Smoke test — example CCNs are illustrative only
    op = sys.argv[1] if len(sys.argv) > 1 else "Example Operator"
    ccns = sys.argv[2].split(",") if len(sys.argv) > 2 else ["555047", "555048"]
    cutoff = sys.argv[3] if len(sys.argv) > 3 else "2024-05-15"
    ft = sys.argv[4] if len(sys.argv) > 4 else "snf"
    print(json.dumps(query_operator_margin(op, ccns, cutoff, facility_type=ft),
                     indent=2, default=str))
