"""connectors_officekit — the desk's registered custody connectors for the
officekit sync layer (the compounding-asset side of the interface ruling,
2026-09-02: a new institution is a new registered connector + a test).

These are DEPLOYMENT-side: they read the desk's own caches and never ship with
the OSS package. Importing this module registers them; desk.household runs
sync before every render so the office reflects live custody state with
per-sleeve provenance + freshness badges (degrade LOUD, never silent).
"""
from __future__ import annotations

import json
from pathlib import Path

from officekit.sync import connector

ROOT = Path(__file__).resolve().parents[1]


@connector(id="ibkr_positions_board", label="IBKR — desk positions board",
           kind="positions", max_age_days=2)
def ibkr_positions_board():
    """The SignalOS alpha sleeve marked from the desk's live positions board.
    Value = gross positions market value (includes the SGOV cash-management
    line; excludes free cash and short-option liabilities — the provenance
    string says so on the page)."""
    d = json.loads((ROOT / "desk/ui/static/positions_board.json").read_text())
    return {
        "as_of": d["generated_utc"][:10],
        "provenance": (f"gross positions MV, {d['counts']['positions']} positions, "
                       f"generated {d['generated_utc']} (positions_board.json; "
                       "excludes free cash + short-option liabilities)"),
        "updates": [{"match": {"category": "alpha_market_neutral"},
                     "value": d["totals"]["mv_usd"]}],
    }


@connector(id="parametric_scorecard_nav", label="Parametric — desk scorecard",
           kind="positions", max_age_days=7)
def parametric_scorecard_nav():
    """The Parametric direct-index sleeve marked from the desk's scorecard sync
    (parametric_sync ingests the newest MSCO bundle). Falls back loudly (ERROR
    row) if the scorecard lacks a NAV."""
    d = json.loads((ROOT / "desk/data/parametric_scorecard.json").read_text())
    nav = d.get("nav") or d.get("net") or (d.get("structure") or {}).get("net")
    asof = d.get("asof") or (d.get("realized_ytd") or {}).get("asof")
    if not nav or not asof:
        raise ValueError("parametric_scorecard.json has no nav/asof — run parametric_sync")
    return {
        "as_of": str(asof)[:10],
        "provenance": f"Parametric scorecard NAV (desk parametric_sync, as of {asof})",
        "updates": [{"match": {"category": "direct_index"}, "value": float(nav)}],
    }
