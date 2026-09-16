"""
Revenue-concentration analyzer for federal services primes.

WHY THIS EXISTS
10-K concentration disclosures land MODERATE in the default scoring even
when they describe an industry-standard distribution. BAH C3 is the
canonical example: "85% of FY25 revenue from 2,596 IDIQ task orders;
top IDIQ vehicle = 18% of revenue; largest TO = 4%" was scored MODERATE
purely because the LLM didn't have an industry benchmark to compare
against. With 2,596 active TOs and a 4% single-TO ceiling, this is
operationally diversified — not a concentration risk.

This M-source adjudicates concentration metrics against:
  1. Industry-standard thresholds (per axis)
  2. Hand-curated peer benchmarks from public 10-Ks (BAH, SAIC, CACI,
     LDOS, KBR, VVX, PSN — extend in
     data/_peer_benchmarks/services_prime_concentration.json)

THE THREE AXES
  Top customer %:         dominated by DoD for defense primes (60-95%
                          typical); not a concentration risk in the
                          conventional sense — DoD is a stable
                          counterparty with statutory funding
  Top contract vehicle %: industry median ~15%; CONCENTRATED above ~30%
                          (federal primes commonly have 1-3 dominant
                          IDIQs like GSA OASIS+, NETCENTS, SeaPort-NxG)
  Top task order %:       industry median ~3-5%; CONCENTRATED above 10%
                          (a single TO >10% means loss-of-recompete is
                          material to the issuer)

SIGNAL ENUM
  DIVERSIFIED            — all metrics at or below industry median →
                            PASS (cleaner than TYPICAL)
  TYPICAL                — within industry norms but at the
                            higher-concentration end → PASS
  CONCENTRATED           — one or more metrics exceed CONCENTRATED
                            thresholds → MODERATE
  SEVERELY_CONCENTRATED  — one or more metrics exceed SEVERE thresholds
                            → SEVERE
  UNVERIFIABLE           — missing inputs

THRESHOLDS (defaults; can be tuned per cohort)
  top_vehicle_pct:    [< 12 DIVERSIFIED] [12-30 TYPICAL] [30-50 CONCENTRATED] [>50 SEVERE]
  top_task_order_pct: [< 4 DIVERSIFIED]  [4-10 TYPICAL]  [10-20 CONCENTRATED] [>20 SEVERE]
  n_idiq_vehicles:    informational; ≥1000 is operational diversification
                       even with high single-vehicle %

CUSTOMER concentration is NOT used as a primary axis because DoD/U.S.
Government concentration is the entire premise of defense services
primes; conflating it with vehicle/TO concentration is a category error.
The 10% SEC customer-disclosure rule already requires disclosure.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["873", "737"],
    "issuer_features": ["government_customer_concentration_above_5pct"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Benchmarks federal-prime concentration disclosures against industry-standard IDIQ/task-order distributions.",
}

import json
import statistics
from pathlib import Path
from typing import Any, Optional

PEER_DATA = Path(__file__).parent.parent / "data" / "_peer_benchmarks" / "services_prime_concentration.json"

# Thresholds: top-vehicle and top-TO concentration tiers
# (axis, low, mid, high) where:
#   < low → DIVERSIFIED, [low, mid) → TYPICAL,
#   [mid, high) → CONCENTRATED, ≥ high → SEVERE
_THRESHOLDS = {
    "top_vehicle_pct":    {"low": 12.0, "mid": 30.0, "high": 50.0},
    "top_task_order_pct": {"low": 4.0,  "mid": 10.0, "high": 20.0},
}


def _load_peers() -> list[dict]:
    if not PEER_DATA.exists():
        return []
    try:
        return json.loads(PEER_DATA.read_text()).get("peers", [])
    except (json.JSONDecodeError, OSError):
        return []


def _percentile_of(value: float, sample: list[float]) -> Optional[float]:
    """Percentile rank of value within sample. None if sample empty."""
    if not sample:
        return None
    sample = sorted(sample)
    below = sum(1 for s in sample if s < value)
    equal = sum(1 for s in sample if s == value)
    # Standard percentile rank: (below + 0.5*equal) / n
    return 100.0 * (below + 0.5 * equal) / len(sample)


def _classify_axis(value: float, axis: str) -> str:
    """Return tier for a single axis."""
    t = _THRESHOLDS[axis]
    if value < t["low"]:
        return "DIVERSIFIED"
    if value < t["mid"]:
        return "TYPICAL"
    if value < t["high"]:
        return "CONCENTRATED"
    return "SEVERELY_CONCENTRATED"


# Tier severity ranking — for aggregating across axes
_TIER_RANK = {
    "DIVERSIFIED":           0,
    "TYPICAL":               1,
    "CONCENTRATED":          2,
    "SEVERELY_CONCENTRATED": 3,
}


def query_revenue_concentration(
    recipient_name: str,
    top_vehicle_pct:    Optional[float] = None,
    top_task_order_pct: Optional[float] = None,
    n_idiq_vehicles:    Optional[int]   = None,
    top_customer_pct:   Optional[float] = None,
    fiscal_year:        Optional[int]   = None,
) -> dict[str, Any]:
    """Adjudicate revenue-concentration metrics against industry norms + peers.

    Args:
      recipient_name:     company name (for echo/output)
      top_vehicle_pct:    largest single IDIQ vehicle as % of revenue
      top_task_order_pct: largest single task order as % of revenue
      n_idiq_vehicles:    count of active IDIQ vehicles (operational
                          diversification proxy)
      top_customer_pct:   largest customer as % of revenue (informational
                          only — DoD concentration is not a primary risk axis)
      fiscal_year:        for echo

    Returns:
      {
        "by_axis":           dict with per-axis tier + peer percentile,
        "signal":            DIVERSIFIED | TYPICAL | CONCENTRATED |
                              SEVERELY_CONCENTRATED | UNVERIFIABLE,
        "peer_comparison":   {n_peers, peer_medians},
        "operational_diversification_note": str (if n_idiq_vehicles set),
        "fiscal_year":       int or None,
        "_inputs":           dict echo,
        "_note":             human explainer,
      }
    """
    inputs = {
        "recipient_name":     recipient_name,
        "top_vehicle_pct":    top_vehicle_pct,
        "top_task_order_pct": top_task_order_pct,
        "n_idiq_vehicles":    n_idiq_vehicles,
        "top_customer_pct":   top_customer_pct,
        "fiscal_year":        fiscal_year,
    }

    # Need at least one of top_vehicle_pct or top_task_order_pct
    if top_vehicle_pct is None and top_task_order_pct is None:
        return {
            "by_axis":         {},
            "signal":          "UNVERIFIABLE",
            "peer_comparison": {},
            "fiscal_year":     fiscal_year,
            "_inputs":         inputs,
            "_note": (
                "Need at least top_vehicle_pct or top_task_order_pct to "
                "adjudicate concentration. 10-Ks of federal services primes "
                "typically disclose both in the MD&A concentration section."
            ),
        }

    peers = _load_peers()

    # Per-axis classification + peer percentile
    by_axis: dict[str, dict] = {}
    tier_ranks_used = []
    for axis, value in [
        ("top_vehicle_pct",    top_vehicle_pct),
        ("top_task_order_pct", top_task_order_pct),
    ]:
        if value is None:
            continue
        tier = _classify_axis(value, axis)
        tier_ranks_used.append(_TIER_RANK[tier])

        peer_sample = [p.get(axis) for p in peers
                        if p.get("ticker") != recipient_name and p.get(axis) is not None]
        pct = _percentile_of(value, peer_sample)
        peer_median = statistics.median(peer_sample) if peer_sample else None

        by_axis[axis] = {
            "value":            value,
            "tier":             tier,
            "threshold_low":    _THRESHOLDS[axis]["low"],
            "threshold_mid":    _THRESHOLDS[axis]["mid"],
            "threshold_high":   _THRESHOLDS[axis]["high"],
            "peer_percentile":  pct,
            "peer_median":      peer_median,
            "n_peers":          len(peer_sample),
        }

    # Aggregate signal — worst tier across axes wins
    if not tier_ranks_used:
        signal = "UNVERIFIABLE"
    else:
        worst = max(tier_ranks_used)
        signal = next(t for t, r in _TIER_RANK.items() if r == worst)

    # Operational diversification override: if n_idiq_vehicles >= 1000
    # AND top_task_order_pct < 5, the issuer is operationally diversified
    # regardless of single-vehicle concentration. A 25% top vehicle that
    # spans 2,000+ TOs is a portfolio, not a concentration risk.
    op_diversification_note = ""
    if n_idiq_vehicles and n_idiq_vehicles >= 1000:
        if top_task_order_pct is not None and top_task_order_pct < 5:
            op_diversification_note = (
                f"Operational diversification: {n_idiq_vehicles:,} active "
                f"IDIQ TOs with single-TO ceiling {top_task_order_pct:.1f}% "
                f"of revenue. Single-vehicle % is a portfolio concentration "
                f"metric, not an operational risk — loss-of-recompete on "
                f"any single TO is bounded at <5% of revenue."
            )
            # If signal was CONCENTRATED purely due to single-vehicle %,
            # downgrade to TYPICAL given the operational diversification.
            if signal == "CONCENTRATED" and by_axis.get("top_vehicle_pct", {}).get("tier") == "CONCENTRATED":
                signal = "TYPICAL"

    # Peer comparison summary
    peer_comparison = {
        "n_peers": len(peers),
        "peer_medians": {
            "top_vehicle_pct": statistics.median([p["top_vehicle_pct"] for p in peers
                                                   if p.get("top_vehicle_pct") is not None]) if peers else None,
            "top_task_order_pct": statistics.median([p["top_task_order_pct"] for p in peers
                                                      if p.get("top_task_order_pct") is not None]) if peers else None,
            "top_customer_pct": statistics.median([p["top_customer_pct"] for p in peers
                                                    if p.get("top_customer_pct") is not None]) if peers else None,
        },
    }

    # Build human note
    parts = []
    for axis in ("top_vehicle_pct", "top_task_order_pct"):
        if axis not in by_axis:
            continue
        a = by_axis[axis]
        v = a["value"]
        pct = a["peer_percentile"]
        pm = a["peer_median"]
        pct_str = f"{pct:.0f}th percentile of {a['n_peers']} peers" if pct is not None else "no peer data"
        pm_str = f"peer median {pm:.1f}%" if pm is not None else "no peer median"
        parts.append(f"{axis}={v:.1f}% → {a['tier']} ({pct_str}, {pm_str})")
    if op_diversification_note:
        parts.append(op_diversification_note)

    return {
        "by_axis":          by_axis,
        "signal":           signal,
        "peer_comparison":  peer_comparison,
        "operational_diversification_note": op_diversification_note,
        "fiscal_year":      fiscal_year,
        "_inputs":          inputs,
        "_note":            ". ".join(parts),
    }
