"""Merge charter universe v2 + non-CSFA conduits + CSFA report + Schedule K → v3.

Applies structural corrections from Schedule K agent and incorporates 56 empirical
spread anchors from the CSFA 2010-2024 transaction inventory.

Output:
- data/charter_universe_v3.json — unified obligor inventory
- data/charter_v3_spread_anchors.json — empirical primary-market anchors (56)
- prints v3 summary stats
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"

v2 = json.loads((DATA / "charter_universe_v2.json").read_text())
csfa = json.loads((DATA / "csfa_transactions_inventory.json").read_text())
other = json.loads((DATA / "non_csfa_charter_conduits.json").read_text())
sk = json.loads((DATA / "charter_form990_schedule_k.json").read_text())
spreads_v2 = json.loads((DATA / "charter_bond_spreads.json").read_text())
ops = json.loads((DATA / "charter_operator_signals.json").read_text())

# Schedule K-driven structural corrections (from agent's `v2_correction` fields)
SCHEDULE_K_CORRECTIONS = {
    "Da Vinci Schools": {
        "structure_class_v3": "wiseburn_usd_lease",
        "structure_class_evidence": "Da Vinci leases from Wiseburn USD-issued GO bonds; no direct CSFA bonds. District credit, not csfa_intercept.",
        "tradeable": False,
        "_v2_correction": "v2 csfa_intercept → v3 wiseburn_usd_lease (NOT tradeable as charter intercept)",
    },
    "Bright Star Schools": {
        "structure_class_v3": "no_direct_bonds_facility_lease_only",
        "structure_class_evidence": "Only $2.5M note + facility leases; no public muni debt at obligor level.",
        "tradeable": False,
        "_v2_correction": "v2 csfa_intercept → v3 no_direct_bonds (NOT tradeable)",
    },
    "High Tech High": {
        "structure_class_v3": "csfa_intercept",
        "structure_class_evidence": "Audit confirms CSFA-issued with state apportionment intercept (corrects v2 cscda_no_intercept misclassification).",
        "tradeable": True,
        "_v2_correction": "v2 cscda_no_intercept → v3 csfa_intercept",
    },
    "Lighthouse Community Public Schools": {
        "structure_class_v3": "csfa_intercept",
        "structure_class_evidence": "CSFA 2022 $26.865M issuance per CSFA 2022 conduit report (corrects v2 cscda_no_intercept).",
        "tradeable": True,
        "_v2_correction": "v2 cscda_no_intercept → v3 csfa_intercept",
    },
    "Summit Public Schools": {
        "structure_class_v3": "csfa_intercept",
        "structure_class_evidence": "Per CSFA report inventory; v2 had 'unknown_or_no_bonds'. 4 closed schools is operator-distress signal.",
        "tradeable": True,
        "_v2_correction": "v2 unknown_or_no_bonds → v3 csfa_intercept (4 closures = HIGH distress signal)",
        "operator_distress_flag": "4_school_closures_2020_2025",
    },
    "Camino Nuevo Charter Academy": {
        "structure_class_v3": "csfa_intercept_via_related_party_llc",
        "structure_class_evidence": "Operator has no direct CSFA bonds; bonds at related-party LLC (GNLA) level. Plus $9M Prop 1D state loan.",
        "tradeable": True,
        "_v2_correction": "v2 csfa_intercept (operator-level) → v3 csfa_intercept_via_LLC (GNLA borrower)",
        "true_bond_issuer": "GNLA (related-party LLC)",
    },
    "Rocketship Public Schools": {
        "structure_class_v3": "cross_state_facility_lease_ldc",
        "structure_class_evidence": "Bonds via Launchpad Development Company OG across DC+TN+CA. CA portion structurally distinct from CA-only CSFA intercept.",
        "tradeable": True,
        "_v2_correction": "v2 csfa_intercept → v3 cross_state_LDC (different masking mechanism, not pure CA intercept)",
    },
    "Alliance College-Ready Public Schools": {
        "operator_distress_flag": "covenant_breach_FY25",
        "operator_distress_source": "FY25 audit discloses non-compliance with financial covenants; waiver obtained",
        "_v2_correction": "v2 buy candidate → v3 EXCLUDE (covenant breach)",
    },
    "Aspire Public Schools": {
        "series_count_correction": "v2 had 4 series, actual is 8+ series, $225M outstanding via College for Certain LLC + KLARE",
        "true_bond_issuers": ["College for Certain LLC", "KLARE"],
        "_v2_correction": "Series count materially understated (4 → 8+, par 33M → 225M outstanding)",
    },
}

# v2 obligors keyed by name
v2_obligors_raw = v2.get("obligors") if "obligors" in v2 else v2
v2_obs = {}
if isinstance(v2_obligors_raw, list):
    for o in v2_obligors_raw:
        if isinstance(o, dict):
            v2_obs[o.get("name") or o.get("obligor_name")] = o
elif isinstance(v2_obligors_raw, dict):
    v2_obs = v2_obligors_raw

# Build v3 obligor index — start from v2
v3 = {}
for name, ob in v2_obs.items():
    if not isinstance(ob, dict): continue
    v3[name] = dict(ob)
    v3[name]["_from"] = "v2"
    v3[name]["structure_class_v3"] = ob.get("structure_class")  # default; may be overridden

# Add new obligors from CSFA report
csfa_tx = csfa["transactions"]
csfa_obs = defaultdict(list)
for tx in csfa_tx:
    obligor = tx.get("obligor_name")
    if obligor:
        csfa_obs[obligor].append(tx)

for obligor, txs in csfa_obs.items():
    if obligor not in v3:
        # Aggregate par and series count
        total_par = sum(t.get("par_usd") or 0 for t in txs if isinstance(t.get("par_usd"), (int, float)))
        # Best rating across transactions
        ratings = [t.get("rating_at_issuance") for t in txs if t.get("rating_at_issuance")]
        # Identify structure (CSFA is intercept-eligible unless flagged otherwise)
        structures = set(t.get("structure", "") for t in txs)
        v3[obligor] = {
            "name": obligor,
            "_from": "csfa_report_2010_2024",
            "structure_class_v3": "csfa_intercept",
            "csfa_transaction_count": len(txs),
            "csfa_aggregate_par_usd": total_par,
            "csfa_ratings_seen": list(set(ratings)),
            "csfa_first_year": min((t.get("closing_date", "0000") or "0000")[:4] for t in txs),
            "csfa_last_year": max((t.get("closing_date", "0000") or "0000")[:4] for t in txs),
            "transactions": txs,
        }
    else:
        # Already in v3 (from v2) — add CSFA transaction history
        v3[obligor]["csfa_transactions"] = txs
        v3[obligor]["csfa_transaction_count"] = len(txs)
        v3[obligor]["csfa_aggregate_par_usd"] = sum(t.get("par_usd") or 0 for t in txs if isinstance(t.get("par_usd"), (int, float)))

# Add obligors from non-CSFA conduit pass
per_conduit = other.get("per_conduit", {})
for conduit_name, conduit_data in per_conduit.items():
    if not isinstance(conduit_data, dict): continue
    new_obs = conduit_data.get("new_obligors_discovered", [])
    if isinstance(new_obs, list):
        for o in new_obs:
            if isinstance(o, str):
                name = o
            elif isinstance(o, dict):
                name = o.get("name") or o.get("obligor_name")
            else: continue
            if name not in v3:
                v3[name] = {
                    "name": name,
                    "_from": f"non_csfa_conduit_{conduit_name}",
                    "structure_class_v3": f"{conduit_name}_other",
                    "tradeable": True,
                }

# Apply Schedule K corrections
for name, fix in SCHEDULE_K_CORRECTIONS.items():
    if name in v3:
        v3[name].update(fix)
        v3[name]["_schedule_k_corrected"] = True
    else:
        # Not in v3 yet — add it
        v3[name] = dict(fix)
        v3[name]["name"] = name
        v3[name]["_schedule_k_corrected"] = True

# Apply Schedule K detailed data
for name, sk_data in sk.get("per_obligor", {}).items():
    if name in v3:
        v3[name]["schedule_k_data"] = sk_data
    elif isinstance(sk_data, dict):
        v3[name] = {"name": name, "_from": "schedule_k_only", "schedule_k_data": sk_data}

# Add operator scores
for name, opdata in ops.get("per_obligor", {}).items():
    if name in v3:
        v3[name]["operator_signal_strength_score"] = opdata.get("operator_signal_strength_score")
        v3[name]["operator_signal_subscores"] = opdata.get("n_verifiable_subscores")

# Distribution stats
struct_counts = defaultdict(int)
sourced = defaultdict(int)
for name, ob in v3.items():
    struct_counts[ob.get("structure_class_v3") or "unknown"] += 1
    sourced[ob.get("_from") or "?"] += 1

# Persist
out = {
    "_meta": {
        "schema_version": "v3",
        "built_from": ["charter_universe_v2.json", "csfa_transactions_inventory.json",
                       "non_csfa_charter_conduits.json", "charter_form990_schedule_k.json",
                       "charter_bond_spreads.json", "charter_operator_signals.json"],
        "v2_corrections_applied": list(SCHEDULE_K_CORRECTIONS.keys()),
    },
    "obligor_count": len(v3),
    "obligors_by_source": dict(sourced),
    "structure_class_distribution_v3": dict(struct_counts),
    "obligors": v3,
}
(DATA / "charter_universe_v3.json").write_text(json.dumps(out, indent=2, default=str))

# Extract empirical spread anchors from CSFA data for the spread test
anchors = []
for tx in csfa_tx:
    if tx.get("mmd_spread_bps_at_issuance") is not None:
        anchors.append({
            "obligor": tx.get("obligor_name"),
            "series": tx.get("series"),
            "closing_date": tx.get("closing_date"),
            "par_usd": tx.get("par_usd"),
            "rating": tx.get("rating_at_issuance"),
            "structure": tx.get("structure"),
            "mmd_spread_bps": tx.get("mmd_spread_bps_at_issuance"),
            "primary_market_yield_pct": tx.get("primary_market_yield_pct"),
        })
(DATA / "charter_v3_spread_anchors.json").write_text(json.dumps({
    "verified_at": "2026-05-28",
    "anchor_count": len(anchors),
    "source": "CSFA 2010-2024 Conduit Financing Program Reports — parsed pdftotext via Wayback Machine archives",
    "anchors": anchors,
}, indent=2, default=str))

print(f"=== v3 universe built ===")
print(f"Total obligors: {len(v3)}")
print(f"\nBy source:")
for k, v in sorted(sourced.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")
print(f"\nBy structure class:")
for k, v in sorted(struct_counts.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")
print(f"\nEmpirical spread anchors extracted: {len(anchors)}")
print(f"\nFiles written:")
print(f"  data/charter_universe_v3.json")
print(f"  data/charter_v3_spread_anchors.json")
