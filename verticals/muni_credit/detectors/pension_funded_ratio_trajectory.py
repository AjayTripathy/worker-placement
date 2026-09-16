"""Pension funded-ratio TRAJECTORY detector.

Extension of pension_funded_ratio.py (which is snapshot-only) to capture the
5-year trajectory. Stockton, Vallejo, and Sacramento USD all share a pattern:
sequential CalPERS / CalSTRS funded-ratio decline for 3-5 years before the
fiscal-distress catalyst event. The TRAJECTORY (slope) is the leading
indicator; the snapshot (level) is the lagging confirm.

FIRES when 5-year trajectory shows funded-ratio decline > 5pp OR current
funded ratio < 60%.

Severity model:
  HIGH    -> declining trajectory (> 5pp drop over 5y) AND current < 60%
  MEDIUM  -> declining trajectory (> 5pp drop over 5y) AND current 60-75%
  LOW     -> stable trajectory but current < 75% (watch only — does NOT fire)
  None    -> does not fire

Why predictive: CalPERS and CalSTRS publish per-employer Annual Actuarial
Valuation Reports each FY with funded-ratio history. The slope flags
employers whose contribution costs are RISING faster than payroll growth,
eroding general-fund flexibility 24-60 months ahead of rating-agency action.
Stockton CalPERS funded-ratio sequence (Misc plan) declined approximately:
  FY2008: 89% -> FY2009: 75% -> FY2010: 73% -> FY2011: 68% -> FY2012: 63%
  -> Ch 9 filing June 2012.
Vallejo CalPERS Misc declined for 4 years before May 2008 Ch 9.
Sacramento City USD CalSTRS exposure 5-year decline preceded the April 2026
Fitch IDR cut to BB- (April 2026 Bond Buyer).

Data source:
  CalPERS Public Agency Actuarial Valuation Reports (one per employer-plan
    per year) — https://www.calpers.ca.gov/page/employers/actuarial-services/employer-contributions
  CalSTRS Defined Benefit Program valuation reports —
    https://www.calstrs.com/general-information/actuarial-valuations-and-reports
  GASB 68 disclosures embedded in employer audited financial statements
    (ACFR / CAFR).

Data shape (per obligor):
  {
    "pension_system": "CalPERS Misc" | "CalSTRS DB" | "CalPERS Safety" | etc,
    "funded_ratio_5yr_history": [
      {"fy": "2024-2025", "ratio": 75.2, "source_url": "...", "source_page": "p.12"},
      {"fy": "2023-2024", "ratio": 78.1, "source_url": "..."},
      {"fy": "2022-2023", "ratio": 80.3, "source_url": "..."},
      {"fy": "2021-2022", "ratio": 78.0, "source_url": "..."},
      {"fy": "2020-2021", "ratio": 76.0, "source_url": "..."}
    ],
    "as_of_date": "2026-05-28",
    "confidence": "HIGH" | "MEDIUM" | "LOW"
  }

Notes on multi-plan obligors:
  - Most CA cities have BOTH CalPERS Misc AND CalPERS Safety. If both are
    available, pass each plan as a separate record (obligor name suffixed
    " — Misc" / " — Safety"). This detector evaluates one plan at a time.
  - K-12 districts have CalSTRS DB exposure but the funded ratio is the
    SYSTEMWIDE CalSTRS ratio (no per-district disaggregation). The signal
    is therefore concentrated when the system itself is declining. Per-
    district variation is captured by the district's GASB 68 net pension
    liability as a multiple of governmental-fund revenue.
  - Pre-2018 (Stockton/Vallejo) funded ratios were reported on the older
    actuarial method; current reports use GASB 68 / Entry Age Normal. Trend
    interpretation is still valid as long as the series is internally
    consistent.
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["pension_dependent_gf"],
    "asset_classes": ["all_muni"],
    "applies_universally": True,
    "kind": "detector",
    "summary": "Pension funded-ratio TRAJECTORY detector.",
}

CRITICAL_LEVEL = 60.0           # current funded ratio % below this fires HIGH
WATCH_LEVEL = 75.0              # current funded ratio % below this is at-risk
TRAJECTORY_DECLINE_PP = 5.0     # 5-year drop (pp) that fires the trajectory


def _compute_trajectory(history: list[dict]) -> tuple[float | None, float | None, int]:
    """Returns (trajectory_pct_5yr, current_funded_ratio, n_points).

    trajectory_pct_5yr = oldest_ratio - newest_ratio (positive = declining;
      i.e. matches the spec's "trajectory_pct_5yr: -2.9" by negation: we
      report newest-minus-oldest as the signed change so a -2.9 means
      declined 2.9pp).
    """
    if not history:
        return None, None, 0
    # Order: callers may pass newest-first OR oldest-first; sort defensively
    # by fy lexicographically (works for "2020-2021", "2021-2022", ...).
    pts = [h for h in history if isinstance(h.get("ratio"), (int, float))]
    if not pts:
        return None, None, 0
    pts = sorted(pts, key=lambda h: h.get("fy", ""))
    oldest = pts[0]["ratio"]
    newest = pts[-1]["ratio"]
    delta_signed = newest - oldest  # negative = declining
    return delta_signed, newest, len(pts)


def evaluate(obligor_name: str, data: dict) -> dict:
    history = data.get("funded_ratio_5yr_history") or []
    pension_system = data.get("pension_system") or "UNKNOWN"

    delta_signed, current, n = _compute_trajectory(history)
    if current is None or n < 2:
        return {
            "fires": False,
            "reason": "INSUFFICIENT_DATA",
            "evidence": {"n_history_points": n, "pension_system": pension_system},
        }

    declining = (delta_signed is not None) and (delta_signed <= -TRAJECTORY_DECLINE_PP)
    critical_level = current < CRITICAL_LEVEL
    at_risk_level = current < WATCH_LEVEL

    evidence = {
        "pension_system": pension_system,
        "current_funded_ratio_pct": round(current, 2),
        "trajectory_change_pp_5yr": round(delta_signed, 2) if delta_signed is not None else None,
        "n_history_points": n,
        "history": history,
        "as_of_date": data.get("as_of_date"),
        "confidence": data.get("confidence"),
    }

    # FIRES cases per spec
    if declining and critical_level:
        return {
            "fires": True,
            "reason": "PENSION_TRAJECTORY_DECLINING_AND_CRITICAL",
            "severity": "HIGH",
            "evidence": evidence,
        }
    if declining and at_risk_level:
        return {
            "fires": True,
            "reason": "PENSION_TRAJECTORY_DECLINING_AT_RISK_LEVEL",
            "severity": "MEDIUM",
            "evidence": evidence,
        }
    if declining:
        # Declining but level still > 75% — fires LOW (Stockton in FY2008 looked
        # like this: 89% but already on the slope)
        return {
            "fires": True,
            "reason": "PENSION_TRAJECTORY_DECLINING_EARLY",
            "severity": "LOW",
            "evidence": evidence,
        }
    if critical_level:
        # Snapshot fallback — matches the original detector's CRITICAL gate.
        return {
            "fires": True,
            "reason": "PENSION_SNAPSHOT_CRITICAL",
            "severity": "HIGH",
            "evidence": evidence,
        }
    if at_risk_level:
        # Watch — do NOT fire (per detector-composition discipline: narrow filters).
        return {
            "fires": False,
            "reason": "PENSION_WATCH_STABLE",
            "severity": "LOW",
            "evidence": evidence,
        }
    return {
        "fires": False,
        "reason": "PENSION_ADEQUATE",
        "evidence": evidence,
    }


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m detectors.pension_funded_ratio_trajectory <data_file.json>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        payload = json.load(f)
    for obligor, rec in payload.get("obligors", {}).items():
        result = evaluate(obligor, rec)
        print(f"{obligor}: {result['reason']} fires={result['fires']} sev={result.get('severity')}")
