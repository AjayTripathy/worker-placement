"""UEI-anchored spike — re-runs the same panel using exact UEI lookup
instead of name substring, and compares the two side-by-side.

Method per ticker:
  1. resolve_recipient_ueis(name) → list of UEI dicts (parent + subs)
  2. For each UEI, query_by_uei() → exact-match contract awards
  3. Aggregate across all UEIs under the same parent name
  4. Compare with the substring-match number from the previous spike

The hypothesis: UEI-anchored query removes substring noise (Hudson
Technologies 67k → ~$33M; AIRO 119 → real value under canonical name)
AND closes the variant gap (Airo Group 0 → finds awards under
subsidiary or aliased UEI).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from verticals.public_co.m_sources.usaspending import (
    resolve_recipient_ueis,
    query_by_uei,
)


HERE = Path(__file__).parent

# (label, candidate_search_names) — try multiple variants per ticker
PANEL = [
    # KNOWN federal primes — calibrators
    ("KNOWN_LMT",         ["Lockheed Martin"]),
    ("KNOWN_NOC",         ["Northrop Grumman"]),
    ("KNOWN_RTX",         ["RTX Corporation", "Raytheon Technologies"]),
    ("KNOWN_KTOS",        ["Kratos Defense", "Kratos"]),

    # Defense / federal small-caps with claimed relationships
    ("AIRO",              ["AIRO Group", "Airo", "AIRO Manufacturing"]),
    ("KSCP_robotics",     ["Knightscope"]),
    ("ONDS_drones",       ["Ondas Holdings", "Ondas Networks"]),
    ("RCAT_drones",       ["Red Cat Holdings", "Teal Drones"]),

    # Fresh-universe names with implicit federal claims
    ("PESI_DOE",          ["Perma-Fix Environmental", "Perma-Fix"]),
    ("KULR_NASA",         ["KULR Technology"]),
    ("ALMU_DARPA",        ["Aeluma"]),

    # Controls — no federal claim, expect zero
    ("CTRL_LRHC",         ["La Rosa Holdings"]),
    ("CTRL_HDSN",         ["Hudson Technologies"]),
    ("CTRL_CWCO",         ["Consolidated Water"]),
    ("CTRL_CDNA",         ["CareDx"]),
    ("CTRL_KLIC",         ["Kulicke & Soffa", "Kulicke and Soffa"]),

    # Fabricated context
    ("FAB_AKAZOO",        ["Akazoo"]),
]


def aggregate_for_ticker(label: str, candidates: list[str]) -> dict:
    """Resolve all candidate variants, dedupe by UEI, query each."""
    all_ueis: dict[str, dict] = {}
    for name in candidates:
        ueis = resolve_recipient_ueis(name, limit=10)
        for u in ueis:
            if u["uei"] not in all_ueis:
                all_ueis[u["uei"]] = u
        time.sleep(0.1)

    # For each UEI, query contracts
    per_uei = []
    total_contracts = 0
    total_amount = 0.0
    all_agencies: dict[str, int] = {}
    for uei, info in all_ueis.items():
        res = query_by_uei(uei, start_date="2018-01-01", end_date="2026-05-18")
        n = res.get("n_awards", 0)
        amt = res.get("total_amount", 0)
        per_uei.append({
            "uei": uei,
            "name": info["name"],
            "level": info.get("recipient_level"),
            "n_awards": n,
            "amount_M": amt / 1e6,
            "top_awards": res.get("top_awards", [])[:3],
        })
        total_contracts += n
        total_amount += amt
        for ag, count in res.get("agencies", {}).items():
            all_agencies[ag] = all_agencies.get(ag, 0) + count
        time.sleep(0.15)

    return {
        "label": label,
        "candidates": candidates,
        "ueis_resolved": len(all_ueis),
        "per_uei": per_uei,
        "total_contracts": total_contracts,
        "total_amount_M": total_amount / 1e6,
        "agencies": all_agencies,
    }


def main():
    out = []
    print(f"{'label':18s} {'ueis':>4s} {'contracts':>9s} {'$M':>10s} {'top_agency':40s}")
    print("=" * 100)
    for label, candidates in PANEL:
        agg = aggregate_for_ticker(label, candidates)
        top_ag = max(agg["agencies"].items(), key=lambda x: x[1])[0] if agg["agencies"] else "—"
        print(f"  {label:16s} {agg['ueis_resolved']:>4d} {agg['total_contracts']:>9d} "
              f"{agg['total_amount_M']:>10.1f} {top_ag:40s}")
        out.append(agg)

    (HERE / "uei_results.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {HERE / 'uei_results.json'}")


if __name__ == "__main__":
    main()
