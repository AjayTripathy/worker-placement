"""
fda_slep_telemetry — FDA / ASPR Shelf Life Extension Program (SLEP) Telemetry Engine.

Administered jointly by the FDA Center for Drug Evaluation and Research (CDER) and ASPR/DOD,
the Shelf Life Extension Program (SLEP) conducts periodic chemical stability and potency testing
on federal strategic drug stockpiles.

Primary use: Modeling the aging and expiration cliff of government-held TPOXX / medical countermeasure
batches to forecast exact quarters when BARDA is mathematically forced to re-order replacement stock.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

# Baseline regulatory stability parameters for Oral Tecovirimat (TPOXX)
BASELINE_SHELF_LIFE_YEARS = 7.0
MAX_SLEP_EXTENSION_YEARS = 3.0  # Max stability extension typically granted by FDA CDER

# Historical Major BARDA Delivery Batches for SIGA (Contract 75A50118C00019)
HISTORICAL_STOCKPILE_TRANCHES = [
    {
        "tranche_id": "BARDA-2018-01",
        "delivery_date": "2018-12-15",
        "quantity_courses": 360_000,
        "format": "Oral Capsule 200mg",
        "baseline_expiry": "2025-12-15",
        "slep_status": "EXTENDED_TO_2027",
        "current_expiry": "2027-12-15",
        "replenishment_window_start": "2027-03-01",
        "replenishment_window_end": "2027-09-30"
    },
    {
        "tranche_id": "BARDA-2019-01",
        "delivery_date": "2019-11-20",
        "quantity_courses": 420_000,
        "format": "Oral Capsule 200mg",
        "baseline_expiry": "2026-11-20",
        "slep_status": "EXTENDED_TO_2028",
        "current_expiry": "2028-11-20",
        "replenishment_window_start": "2028-02-01",
        "replenishment_window_end": "2028-08-31"
    },
    {
        "tranche_id": "BARDA-2020-01",
        "delivery_date": "2020-10-10",
        "quantity_courses": 350_000,
        "format": "Oral Capsule 200mg",
        "baseline_expiry": "2027-10-10",
        "slep_status": "UNDER_INITIAL_BASELINE",
        "current_expiry": "2027-10-10",
        "replenishment_window_start": "2027-01-01",
        "replenishment_window_end": "2027-07-31"
    },
    {
        "tranche_id": "BARDA-2022-IV",
        "delivery_date": "2022-08-15",
        "quantity_courses": 50_000,
        "format": "Intravenous (IV) Vial",
        "baseline_expiry": "2029-08-15",
        "slep_status": "UNDER_INITIAL_BASELINE",
        "current_expiry": "2029-08-15",
        "replenishment_window_start": "2028-11-01",
        "replenishment_window_end": "2029-05-31"
    },
    {
        "tranche_id": "DOD-2024-01",
        "delivery_date": "2024-06-30",
        "quantity_courses": 23_030,
        "format": "Oral Capsule 200mg",
        "baseline_expiry": "2031-06-30",
        "slep_status": "UNDER_INITIAL_BASELINE",
        "current_expiry": "2031-06-30",
        "replenishment_window_start": "2030-10-01",
        "replenishment_window_end": "2031-03-31"
    }
]


def model_stockpile_aging(
    as_of_date: Optional[str] = None,
    lead_time_months: int = 9,
    tranches: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Model the aging and expiration cliff of medical countermeasure stockpile batches.
    Calculates when upcoming tranches reach replenishment deadline (lead time before expiration).
    """
    today_dt = datetime.date.fromisoformat(as_of_date) if as_of_date else datetime.date.today()
    tranche_list = tranches or HISTORICAL_STOCKPILE_TRANCHES
    
    analyzed_tranches = []
    total_courses = 0
    courses_expiring_within_12m = 0
    courses_expiring_within_24m = 0
    courses_in_active_reorder_window = 0
    next_reorder_deadline = None

    for t in tranche_list:
        courses = t["quantity_courses"]
        total_courses += courses
        exp_dt = datetime.date.fromisoformat(t["current_expiry"])
        days_to_exp = (exp_dt - today_dt).days
        months_to_exp = days_to_exp / 30.417

        # Re-order deadline is expiry minus lead time
        lead_time_days = int(lead_time_months * 30.417)
        reorder_dt = exp_dt - datetime.timedelta(days=lead_time_days)
        is_in_reorder_window = today_dt >= reorder_dt and today_dt <= exp_dt

        if not next_reorder_deadline or (reorder_dt > today_dt and reorder_dt < next_reorder_deadline):
            next_reorder_deadline = reorder_dt

        if months_to_exp <= 12.0:
            courses_expiring_within_12m += courses
        if months_to_exp <= 24.0:
            courses_expiring_within_24m += courses
        if is_in_reorder_window:
            courses_in_active_reorder_window += courses

        analyzed_tranches.append({
            "tranche_id": t["tranche_id"],
            "format": t["format"],
            "quantity_courses": courses,
            "current_expiry": t["current_expiry"],
            "slep_status": t["slep_status"],
            "months_to_expiry": round(months_to_exp, 1),
            "reorder_trigger_date": reorder_dt.isoformat(),
            "in_active_reorder_window": is_in_reorder_window
        })

    return {
        "as_of_date": today_dt.isoformat(),
        "total_stockpile_courses_tracked": total_courses,
        "courses_expiring_within_12m": courses_expiring_within_12m,
        "courses_expiring_within_24m": courses_expiring_within_24m,
        "courses_in_active_reorder_window": courses_in_active_reorder_window,
        "next_reorder_deadline": next_reorder_deadline.isoformat() if next_reorder_deadline else None,
        "lead_time_months_assumed": lead_time_months,
        "tranche_breakdown": analyzed_tranches,
        "telemetry_verdict": "REORDER_CYCLE_APPROACHING" if courses_expiring_within_24m > 0 else "STOCKPILE_HEALTHY"
    }
