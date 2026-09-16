"""Deterministic two-composite recompute (distress + recovery).

Reads R/f/M tuples from a pilot JSON, computes:
  - distress_composite: sum of severity weights / count_formal_tuples
    where weights = {PASS:0, UNV:0, MOD:1, SEV:2, RED:3}
  - recovery_composite: count of PASS-positive formal tuples / count_formal_tuples

Candidate m-source tuples (M_source.startswith("candidate:")) are
EXCLUDED from the formal composite to keep the math reproducible
across pilots. They are logged separately via candidate_log.py.

Also computes the proposed tier:
  HIGH_CONV_LONG  : recovery >= 0.30 AND distress <= 0.50
  HIGH_CONV_SHORT : distress >= 1.00 AND recovery <= 0.10
  NEUTRAL         : everything else

Usage:
  python3 -m verticals.public_co.m_sources.composite_recompute <pilot.json>
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "helper",
    "summary": "Deterministic distress/recovery composite recompute over pilot tuples; scoring infra, never dispatched.",
}

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SEV_W = {"PASS": 0, "UNVERIFIABLE": 0, "MODERATE_UNDERDELIVERY": 1,
         "SEVERE_UNDERDELIVERY": 2, "RED_FLAG_NEGATIVE": 3}


def is_candidate_tuple(tup: dict) -> bool:
    ms = tup.get("M_source")
    if not isinstance(ms, str):
        return False
    return ms.startswith("candidate:")


def recompute(pilot: dict) -> dict[str, Any]:
    tuples = pilot.get("rfm_tuples") or []
    formal = [t for t in tuples if not is_candidate_tuple(t)]
    candidates = [t for t in tuples if is_candidate_tuple(t)]
    n_formal = len(formal)
    if n_formal == 0:
        return {
            "distress_composite": None,
            "recovery_composite": None,
            "tier": "UNSCOREABLE",
            "n_formal_tuples": 0,
            "n_candidate_tuples": len(candidates),
            "_note": "No formal m-source tuples; cannot compute composites.",
        }

    distress_sum = sum(SEV_W.get(t.get("severity", "PASS"), 0) for t in formal)
    distress = distress_sum / n_formal

    n_pass_positive = sum(
        1 for t in formal
        if t.get("severity", "PASS") in ("PASS", "UNVERIFIABLE")
        and (t.get("direction") or "neutral") == "positive"
    )
    recovery = n_pass_positive / n_formal

    if recovery >= 0.30 and distress <= 0.50:
        tier = "HIGH_CONV_LONG"
    elif distress >= 1.00 and recovery <= 0.10:
        tier = "HIGH_CONV_SHORT"
    elif distress >= 0.50:
        tier = "SHORT_TIER"
    elif recovery >= 0.20:
        tier = "LONG_TIER"
    else:
        tier = "NEUTRAL"

    # Per-direction breakdown
    direction_counts = {"positive": 0, "neutral": 0, "negative": 0, "missing": 0}
    for t in formal:
        d = t.get("direction") or "missing"
        direction_counts[d] = direction_counts.get(d, 0) + 1

    severity_counts = {k: 0 for k in SEV_W}
    for t in formal:
        s = t.get("severity") or "PASS"
        severity_counts[s] = severity_counts.get(s, 0) + 1

    return {
        "distress_composite": round(distress, 3),
        "recovery_composite": round(recovery, 3),
        "tier": tier,
        "n_formal_tuples": n_formal,
        "n_candidate_tuples": len(candidates),
        "severity_counts": severity_counts,
        "direction_counts": direction_counts,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pilot_path", help="Path to a pilot JSON file")
    args = ap.parse_args()

    p = Path(args.pilot_path)
    if not p.exists():
        print(f"Not found: {p}", file=sys.stderr)
        sys.exit(1)
    pilot = json.loads(p.read_text())
    r = recompute(pilot)
    print(f"Pilot: {p}")
    print(f"  ticker: {pilot.get('ticker')}")
    print(f"  cutoff: {pilot.get('cutoff')}")
    print(json.dumps(r, indent=2))


if __name__ == "__main__":
    main()
