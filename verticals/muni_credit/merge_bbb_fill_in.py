"""Merge the BBB fill-in metrics into operating_metrics + cafr_overrides."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"

fill_in = json.loads((DATA / "bbb_metrics_fill_in.json").read_text())
operating = json.loads((DATA / "operating_metrics.json").read_text())
cafr = json.loads((DATA / "cafr_overrides.json").read_text())

added = 0
for obligor_name, entry in fill_in.get("obligors", {}).items():
    om = entry.get("operating_metrics", {})
    # Update operating_metrics
    operating["obligors"][obligor_name] = om
    # Update cafr_overrides for days cash
    dc = om.get("days_cash_on_hand")
    if dc is not None:
        cafr.setdefault("overrides", {})[obligor_name] = {
            "consolidated_days_cash": dc,
            "consolidated_total_margin_pct": om.get("operating_margin_pct"),
            "_source": "BBB fill-in research, " + (om.get("source_url") or "unknown"),
            "_universe": "BBB-tier",
        }
    added += 1

(DATA / "operating_metrics.json").write_text(json.dumps(operating, indent=2))
(DATA / "cafr_overrides.json").write_text(json.dumps(cafr, indent=2))

print(f"Merged {added} obligors into operating_metrics + cafr_overrides")
for name, entry in fill_in.get("obligors", {}).items():
    om = entry.get("operating_metrics", {})
    dc = om.get("days_cash_on_hand")
    print(f"  {name:<40} DCOH={dc} margin={om.get('operating_margin_pct')}%")
