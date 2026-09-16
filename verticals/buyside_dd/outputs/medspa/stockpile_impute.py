"""stockpile_impute — IMPUTE Evolus's Jeuveau inventory BETWEEN 10-Q filings, to read the tariff
pre-buy before the Q2 (Jun-30) 10-Q files ~Aug 5.

LOGIC: inventory(t) = inventory(last reported) + cumulative[ imports_in(t) - sell_through_out(t) ].
- anchor = last reported InventoryNet ($24.8M @ Mar-31-2026, SEC XBRL).
- imports_in velocity = REAL US Census AIR imports of Korea->US botulinum toxin (HS 3002.49) — the
  air-freight channel that ocean bills-of-lading can't see (the data confirms it's 100% air). Pulled
  live via customer_id.census_trade_flow; updates monthly (~5wk lag). AGGREGATE caveat: captures all
  Korean toxin importers (Evolus/Jeuveau dominant + Hugel/Letybo), value-based not unit-based — so the
  SURGE FLAG (velocity materially elevated) is the robust signal; the imputed $ is indicative.
- sell_through_out = COGS run-rate (steady).
A pre-tariff STOCKPILE = air-import velocity >> sell-through => imputed inventory builds above the
~$32.9M prior peak ahead of the Sept-29 tariff.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))   # signalos repo root (medspa->outputs->buyside_dd->verticals->signalos)
from verticals.buyside_dd.connectors.customer_id import census_trade_flow

ANCHOR_INV_M = 24.8          # $M, 2026-03-31 (SEC XBRL InventoryNet, verified)
PRIOR_PEAK_M = 32.9          # $M, 2025-09-30 — the level a real stockpile must break
GROSS_MARGIN = 0.669
QTR_SALES_M = 82.0
QTR_COGS_M = QTR_SALES_M * (1 - GROSS_MARGIN)   # ~$27M/qtr product cost flowing OUT of inventory


def impute():
    tf = census_trade_flow("300249", "south korea", mode="air")
    if tf.get("status") != "OK":
        return {"status": tf.get("status"), "note": tf.get("note"),
                "anchor_M": ANCHOR_INV_M, "prior_peak_to_break_M": PRIOR_PEAK_M}
    vel = tf["velocity_vs_baseline"] or 1.0
    imports_in_M = QTR_COGS_M * vel
    imputed = ANCHOR_INV_M + imports_in_M - QTR_COGS_M
    surge = vel - 1.0
    import math
    p_build = round(1 / (1 + math.exp(-6 * (surge - 0.25))), 2)   # ~25% velocity surge = inflection
    return {
        "status": "IMPUTED",
        "source": "US Census air-imports HS3002.49 Korea->US (live)",
        "census_latest_month": tf["latest_month"],
        "import_velocity_vs_baseline": vel,
        "census_surge_flag": tf["surge"],
        "baseline_avg_M": tf["baseline_avg_M"], "recent_3mo_avg_M": tf["recent_3mo_avg_M"],
        "imputed_inventory_Jun30_M": round(imputed, 1),
        "breaks_prior_peak_$32.9M": imputed > PRIOR_PEAK_M,
        "p_material_stockpile_in_Q2_10Q": p_build,
        "read": "STOCKPILE LIKELY" if p_build >= 0.6 else
                ("INCONCLUSIVE" if p_build >= 0.35 else "NO STOCKPILE YET"),
        "caveat": "aggregate (Evolus+Hugel) value-based air-import proxy; surge flag is the robust "
                  "signal. Decisive pre-tariff months (May-Sep) post monthly ~5wk lag — recheck.",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(impute(), indent=2))
