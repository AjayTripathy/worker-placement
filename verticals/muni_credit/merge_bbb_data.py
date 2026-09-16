"""Merge BBB covenant + operating metrics chunks into the main data files.

Reads:
  data/bbb_covenants_and_metrics_chunk_a.json
  data/bbb_covenants_and_metrics_chunk_b.json
Writes:
  data/covenant_terms.json     (appended)
  data/operating_metrics.json  (appended)
  data/cafr_overrides.json     (appended — uses days_cash from operating_metrics)
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"

# Load existing data
covenant_data = json.loads((DATA / "covenant_terms.json").read_text())
operating_data = json.loads((DATA / "operating_metrics.json").read_text())
cafr_data = json.loads((DATA / "cafr_overrides.json").read_text())

# Track which obligors are BBB-universe so the tripwire screen can filter
bbb_obligor_names = []

for chunk in ["a", "b"]:
    path = DATA / f"bbb_covenants_and_metrics_chunk_{chunk}.json"
    if not path.exists():
        print(f"SKIP: {path} missing")
        continue
    bbb = json.loads(path.read_text())
    for obligor_name, entry in bbb.get("obligors", {}).items():
        bbb_obligor_names.append(obligor_name)
        # Covenants
        if "covenants" in entry:
            covenant_data["obligors"][obligor_name] = entry["covenants"]
            covenant_data["obligors"][obligor_name]["_universe"] = "BBB-tier"
        # Operating metrics
        if "operating_metrics" in entry:
            operating_data["obligors"][obligor_name] = entry["operating_metrics"]
        # CAFR overrides — derive days cash from operating_metrics
        om = entry.get("operating_metrics", {})
        dc = om.get("days_cash_on_hand")
        if dc is not None:
            cafr_data.setdefault("overrides", {})[obligor_name] = {
                "consolidated_days_cash": dc,
                "consolidated_total_margin_pct": om.get("operating_margin_pct"),
                "_source": "BBB universe research, " + (om.get("source_url") or "unknown"),
                "_universe": "BBB-tier",
            }

# Write back
(DATA / "covenant_terms.json").write_text(json.dumps(covenant_data, indent=2))
(DATA / "operating_metrics.json").write_text(json.dumps(operating_data, indent=2))
(DATA / "cafr_overrides.json").write_text(json.dumps(cafr_data, indent=2))

# Save the BBB list for the screen runner
(DATA / "bbb_universe_obligor_list.json").write_text(
    json.dumps({"obligors": bbb_obligor_names}, indent=2)
)

print(f"Merged {len(bbb_obligor_names)} BBB obligors")
print(f"  covenant_terms now has {len(covenant_data['obligors'])} obligors")
print(f"  operating_metrics now has {len(operating_data['obligors'])} obligors")
print(f"  cafr_overrides now has {len(cafr_data['overrides'])} obligors")
for name in bbb_obligor_names:
    print(f"  - {name}")
