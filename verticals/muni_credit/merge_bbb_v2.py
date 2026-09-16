"""Merge BBB v2 covenant + operating metrics chunks into main data files."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"

covenants_data = json.loads((DATA / "covenant_terms.json").read_text())
operating_data = json.loads((DATA / "operating_metrics.json").read_text())
cafr_data = json.loads((DATA / "cafr_overrides.json").read_text())
bbb_list_path = DATA / "bbb_universe_obligor_list.json"
bbb_list = json.loads(bbb_list_path.read_text())["obligors"] if bbb_list_path.exists() else []

added = 0
for chunk in ["a", "b"]:
    path = DATA / f"bbb_v2_covenants_and_metrics_chunk_{chunk}.json"
    if not path.exists():
        print(f"SKIP: {path} missing")
        continue
    v2 = json.loads(path.read_text())
    for obligor, entry in v2.get("obligors", {}).items():
        bbb_list.append(obligor)
        # Covenants
        if "covenants" in entry:
            covenants_data["obligors"][obligor] = entry["covenants"]
            covenants_data["obligors"][obligor]["_universe"] = "BBB-tier-v2"
        # Operating metrics
        if "operating_metrics" in entry:
            operating_data["obligors"][obligor] = entry["operating_metrics"]
        # CAFR overrides
        om = entry.get("operating_metrics", {})
        dc = om.get("days_cash_on_hand")
        if dc is not None:
            cafr_data.setdefault("overrides", {})[obligor] = {
                "consolidated_days_cash": dc,
                "consolidated_total_margin_pct": om.get("operating_margin_pct"),
                "_source": "BBB v2 research, " + (om.get("source_url") or "unknown"),
                "_universe": "BBB-tier-v2",
            }
        added += 1

# Dedupe the BBB list
bbb_list = list(dict.fromkeys(bbb_list))  # preserves order

(DATA / "covenant_terms.json").write_text(json.dumps(covenants_data, indent=2))
(DATA / "operating_metrics.json").write_text(json.dumps(operating_data, indent=2))
(DATA / "cafr_overrides.json").write_text(json.dumps(cafr_data, indent=2))
(DATA / "bbb_universe_obligor_list.json").write_text(json.dumps({"obligors": bbb_list}, indent=2))

print(f"Merged {added} BBB v2 obligors")
print(f"  BBB universe list now: {len(bbb_list)} obligors")
print(f"  covenant_terms now has {len(covenants_data['obligors'])} obligors")
print(f"  operating_metrics now has {len(operating_data['obligors'])} obligors")
