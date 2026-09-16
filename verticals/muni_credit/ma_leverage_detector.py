"""M&A leverage event detector.

WHY THIS EXISTS

Covenant tripwire (covenant_tripwire.py) misses obligors that get downgraded
because of M&A leverage, not because of covenant pressure. From the classification
backtest, 2 of 4 false negatives were M&A-driven:

  - Adventist Health West (Fitch A→BBB+, May 2024) — Tenet hospital acquisition
  - Naples Comprehensive Health (Moody's + Fitch 1-notch, Oct 2024) — possibly M&A

The M&A leverage detector is a SECOND signal layer that fires on obligors with
a material M&A event in the recent past. Combined with the covenant tripwire,
it should improve recall on the FN set.

INPUT
  data/ma_leverage_events.json — per-obligor M&A events with deal value, debt
                                  added, completion date, source citations
  data/operating_metrics.json — annual revenue per obligor (for sizing the deal)

OUTPUT TIERS

  MA_RED      Deal value >= 15% of annual revenue OR explicit high leverage impact
  MA_YELLOW   Deal value 5-15% of annual revenue
  MA_GREEN    Deal value < 5% of annual revenue (rounding error)
  MA_NONE     No M&A events in window

COMBINED SIGNAL — used in classification analyzer

  combined_signal = covenant_tripwire OR ma_leverage_red
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

HERE = Path(__file__).parent
MA_FILE = HERE / "data" / "ma_leverage_events.json"
OP_FILE = HERE / "data" / "operating_metrics.json"


def severity_for_deal_pct(deal_pct_of_revenue: float, explicit_impact: Optional[str] = None) -> str:
    """Map deal-size-vs-revenue percent + explicit impact tag to severity tier."""
    if explicit_impact == "high":
        return "MA_RED"
    if deal_pct_of_revenue is None:
        # Unknown deal value: trust the explicit impact, else assume YELLOW (something happened)
        if explicit_impact == "medium":
            return "MA_YELLOW"
        if explicit_impact == "low":
            return "MA_GREEN"
        return "MA_YELLOW"  # default for unsized events
    if deal_pct_of_revenue >= 15:
        return "MA_RED"
    if deal_pct_of_revenue >= 5:
        return "MA_YELLOW"
    return "MA_GREEN"


def evaluate_obligor(obligor_name: str, ma_events: list[dict],
                      annual_revenue_usd: Optional[float],
                      window_start: str = "2023-01-01",
                      window_end: str = "2025-03-31") -> dict:
    """Compute worst M&A leverage tier for one obligor in a given window."""
    relevant = []
    for e in ma_events:
        date = e.get("date") or e.get("completion_date")
        if not date:
            continue
        try:
            d = datetime.fromisoformat(date[:10])
        except Exception:
            continue
        if d < datetime.fromisoformat(window_start) or d > datetime.fromisoformat(window_end):
            continue
        relevant.append(e)

    # Compute per-event severity, take max
    worst_severity = "MA_NONE"
    severity_rank = {"MA_NONE": 0, "MA_GREEN": 1, "MA_YELLOW": 2, "MA_RED": 3}
    per_event = []
    for e in relevant:
        deal_value = e.get("deal_value_usd")
        deal_pct = (deal_value / annual_revenue_usd * 100) if (deal_value and annual_revenue_usd) else None
        impact = e.get("leverage_impact")
        tier = severity_for_deal_pct(deal_pct, impact)
        per_event.append({
            "date": e.get("date"),
            "type": e.get("type"),
            "counterparty": e.get("counterparty"),
            "deal_value_usd": deal_value,
            "deal_pct_of_revenue": deal_pct,
            "explicit_impact": impact,
            "severity": tier,
            "source_url": e.get("source_url"),
            "citation_text": e.get("citation_text"),
        })
        if severity_rank.get(tier, 0) > severity_rank.get(worst_severity, 0):
            worst_severity = tier

    return {
        "obligor": obligor_name,
        "worst_severity": worst_severity,
        "n_events_in_window": len(relevant),
        "per_event": per_event,
        "annual_revenue_usd": annual_revenue_usd,
    }


def run_screen() -> dict:
    """Run M&A leverage detector across all obligors with M&A data."""
    if not MA_FILE.exists():
        return {"results": [], "_error": f"{MA_FILE} missing — agent has not delivered yet"}
    ma_data = json.loads(MA_FILE.read_text())
    op_data = json.loads(OP_FILE.read_text()) if OP_FILE.exists() else {"obligors": {}}

    results = []
    for obligor, entry in ma_data.get("obligors", {}).items():
        ma_events = entry.get("ma_events", [])
        # Get revenue from operating_metrics if available; else from ma_events entry
        rev = (op_data.get("obligors", {}).get(obligor, {}).get("total_operating_revenue_usd")
               or entry.get("annual_revenue_at_event_usd"))
        result = evaluate_obligor(obligor, ma_events, rev)
        results.append(result)

    severity_rank = {"MA_NONE": 0, "MA_GREEN": 1, "MA_YELLOW": 2, "MA_RED": 3}
    results.sort(key=lambda r: -severity_rank.get(r["worst_severity"], 0))

    from collections import Counter
    dist = Counter(r["worst_severity"] for r in results)
    return {
        "evaluated_at": "2026-05-27",
        "n_obligors": len(results),
        "tier_distribution": dict(dist),
        "results": results,
    }


def load_ma_red_signals() -> dict:
    """Return {obligor → does MA_RED fire}."""
    out = run_screen()
    return {r["obligor"]: r["worst_severity"] == "MA_RED" for r in out.get("results", [])}


def load_combined_signals(tripwire_signals: dict) -> dict:
    """Combine covenant tripwire OR MA_RED into a single fire/no-fire signal."""
    ma_signals = load_ma_red_signals()
    all_obligors = set(tripwire_signals.keys()) | set(ma_signals.keys())
    combined = {}
    for o in all_obligors:
        combined[o] = bool(tripwire_signals.get(o)) or bool(ma_signals.get(o))
    return combined


if __name__ == "__main__":
    import sys
    out = run_screen()
    print(json.dumps(out, indent=2))
