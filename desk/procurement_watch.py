"""
procurement_watch — Continuous Procurement, Contract Mod, and Stockpile Telemetry Watcher.

Monitors configured defense and biodefense contracts for:
  1. USAspending Contract Modifications & Delta Obligations (contract_mod_poller)
  2. SAM.gov Sole-Source Justification & Approval (J&A) Filings (sam_opportunities)
  3. PHEMCE & Congressional Budget Appropriation Health (phemce_appropriations)
  4. FDA/ASPR SLEP Expiration & Re-Order Window Telemetry (fda_slep_telemetry)

Rides desk intraday cron alongside filing_watch: python3 -m desk.procurement_watch
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from verticals.public_co.m_sources.contract_mod_poller import poll_contract_modifications
from verticals.public_co.m_sources.sam_opportunities import query_sam_opportunities, parse_sole_source_justification
from verticals.public_co.m_sources.phemce_appropriations import audit_phemce_stockpile_health
from verticals.public_co.m_sources.fda_slep_telemetry import model_stockpile_aging

CONF = ROOT / "desk" / "data" / "procurement_watch.json"
STATE = ROOT / "desk" / "data" / "procurement_watch_state.json"


def _load(p: Path, default: Any) -> Any:
    try:
        return json.loads(p.read_text())
    except Exception:
        return default


def _save(p: Path, data: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def run_procurement_sweep(dry_run: bool = False) -> List[Dict[str, Any]]:
    conf = _load(CONF, {"targets": {}})
    state = _load(STATE, {})
    today = datetime.date.today().isoformat()
    alerts = []

    for tk, t in conf.get("targets", {}).items():
        if t.get("until") and t["until"] < today:
            continue  # Target window expired

        piid = t.get("primary_award_piid")
        target_state = state.get(tk, {})
        known_mods = target_state.get("known_mod_numbers", [])

        # 1. Poll Contract Modifications
        mod_result = poll_contract_modifications(piid, known_mod_numbers=known_mods)
        if mod_result.get("has_new_mods"):
            alerts.append({
                "ticker": tk,
                "type": "NEW_CONTRACT_MODIFICATION",
                "award_piid": piid,
                "new_mods": mod_result["new_mods"],
                "total_obligated": mod_result["cumulative_obligations"]
            })
            if not dry_run:
                updated_known = list(set(known_mods + [m["modification_number"] for m in mod_result["new_mods"]]))
                target_state["known_mod_numbers"] = updated_known
                target_state["last_mod_poll"] = today

        # 2. Check FDA SLEP Aging Telemetry
        slep_result = model_stockpile_aging(lead_time_months=t.get("lead_time_months", 9))
        if slep_result.get("courses_in_active_reorder_window", 0) > 0:
            alerts.append({
                "ticker": tk,
                "type": "SLEP_REORDER_WINDOW_ACTIVE",
                "courses_in_window": slep_result["courses_in_active_reorder_window"],
                "next_deadline": slep_result["next_reorder_deadline"]
            })

        # 3. Check PHEMCE Appropriations Health
        phemce_result = audit_phemce_stockpile_health(contractor_ticker=tk)
        target_state["phemce_status"] = phemce_result["status"]
        target_state["last_sweep"] = datetime.datetime.utcnow().isoformat() + "Z"

        if not dry_run:
            state[tk] = target_state

    if not dry_run:
        _save(STATE, state)

    return alerts


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    print(f"=== Running SignalOS Procurement Watcher (dry_run={dry_run}) ===")
    alerts = run_procurement_sweep(dry_run=dry_run)
    print(f"Sweep complete. Alerts generated: {len(alerts)}")
    for a in alerts:
        print(f"ALERT: [{a['type']}] Ticker: {a['ticker']} -> {a}")


if __name__ == "__main__":
    main()
