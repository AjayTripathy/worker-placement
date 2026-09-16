"""Calibration spike for federal-contract f(M).

Question: is USAspending a stronger f(M) than megacap_namecheck for
counterparty/agency-claim verification? Federal registry is
comprehensive (no materiality gating), so naively absence should be
more informative than for commercial counterparties.

But several failure modes can produce 0 hits for real federal
relationships:
  (1) Subcontractor invisibility — prime gets the award, small-cap
      sub doesn't appear at the top level
  (2) Subsidiary naming asymmetry — award goes to "BWXT Y-12 LLC"
      not "BWX Technologies Inc"
  (3) CRADAs / OTAs — national-lab partnerships that aren't formal
      awards
  (4) Classified work
  (5) SBIR/STTR inflation — small grants described as "DoD program"
  (6) Reporting lag (30-60 days)

Test panel — names from current cohorts with explicit federal claims,
plus controls and pure-fabrications.
"""
from __future__ import annotations

import json
from pathlib import Path

from verticals.public_co.m_sources.usaspending import (
    query_recipient_contracts,
    query_recipient_grants,
    query_dod_contracts,
)


HERE = Path(__file__).parent

# (label, recipient_name, expected_band, notes)
PANEL = [
    # KNOWN DoD/federal primes — should hit big
    ("KNOWN_LMT",         "Lockheed Martin",      "HIGH",
     "DoD prime"),
    ("KNOWN_NOC",         "Northrop Grumman",     "HIGH",
     "DoD prime"),
    ("KNOWN_RTX",         "RTX Corporation",      "HIGH",
     "DoD prime"),

    # Real defense small-caps with DoD claims
    ("AIRO_drone",        "AIRO",                 "?",
     "claimed industrial-drone DoD relationship"),
    ("AIRO_drone_v2",     "Airo Group",           "?",
     "alt name variant"),
    ("KSCP_robotics",     "Knightscope",          "?",
     "security-robotics, claimed federal pilot programs"),
    ("KTOS_defense",      "Kratos Defense",       "?",
     "defense electronics, real DoD"),
    ("ONDS_drones",       "Ondas Holdings",       "?",
     "drone networks, claimed federal"),
    ("RCAT_drones",       "Red Cat Holdings",     "?",
     "drone manufacturer, defense claims"),

    # Fresh-universe names with implicit federal claims
    ("PESI_DOE",          "Perma-Fix Environmental","?",
     "claims DOE West Valley nuclear waste contracts"),
    ("PESI_alt",          "Perma-Fix",            "?",
     "alt name variant"),
    ("KULR_NASA",         "KULR Technology",      "?",
     "claims NASA/JPL battery safety work"),
    ("ALMU_DARPA",        "Aeluma",               "?",
     "compound semis, claimed federal R&D"),

    # Controls — no federal claim, expect 0
    ("CTRL_LRHC",         "La Rosa Holdings",     "ZERO",
     "real-estate brokerage, no federal claim"),
    ("CTRL_HDSN",         "Hudson Technologies",  "ZERO",
     "refrigerants, no federal claim"),
    ("CTRL_CWCO",         "Consolidated Water",   "ZERO",
     "water utility, no federal claim"),
    ("CTRL_CDNA",         "CareDx",               "?",
     "biotech, possibly NIH-funded"),

    # Fabricated-context — Akazoo (music streaming, no federal claim)
    ("FAB_AKAZOO",        "Akazoo",               "ZERO",
     "fabricated Sony deals, no federal claim possible"),
]


def main():
    out = []
    print(f"{'label':22s} {'recipient':28s} {'contracts':>9s} {'$M':>10s} "
          f"{'grants':>7s} {'$M_g':>8s} {'top_agency':30s}")
    print("=" * 120)
    for label, name, expected, notes in PANEL:
        contracts = query_recipient_contracts(
            recipient_name=name,
            start_date="2018-01-01",
            end_date="2026-05-18",
        )
        grants = query_recipient_grants(
            recipient_name=name,
            start_date="2018-01-01",
            end_date="2026-05-18",
        )
        n_c   = contracts.get("n_awards", 0)
        amt_c = contracts.get("total_amount", 0) / 1e6
        n_g   = grants.get("n_awards", 0)
        amt_g = grants.get("total_amount", 0) / 1e6
        agencies = contracts.get("agencies", {})
        top_ag = max(agencies.items(), key=lambda x: x[1])[0] if agencies else "—"
        print(f"  {label:20s} {name:28s} {n_c:>9d} {amt_c:>10.1f} "
              f"{n_g:>7d} {amt_g:>8.1f} {top_ag:30s}")
        out.append({
            "label": label,
            "recipient": name,
            "expected": expected,
            "notes": notes,
            "contracts": {
                "n_awards": n_c,
                "total_amount_M": amt_c,
                "top_agencies": dict(list(agencies.items())[:5]),
                "top_awards": contracts.get("top_awards", [])[:3],
            },
            "grants": {
                "n_awards": n_g,
                "total_amount_M": amt_g,
                "top_agencies": dict(list(grants.get("agencies", {}).items())[:5]),
            },
        })

    (HERE / "spike_results.json").write_text(json.dumps(out, indent=2, default=str))
    print(f"\nWrote {HERE / 'spike_results.json'}")


if __name__ == "__main__":
    main()
