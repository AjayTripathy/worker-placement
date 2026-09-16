"""latency_log — append-only divergence -> discovery-state log (the knowledge-graph payoff).

THE POINT (spec §The retrofit, item 2): every divergence, at the moment of detection, gets one row
stamped with the conditioning-layer discovery_state. Later a scoring job appends the realized
time-to-price. Over many rows this builds the empirical signal-to-price-latency table by
(divergence_type x regime) — the latency axis of the SignalOS goal. Phase 1 only scaffolds the
append; Phase 2 wires the market-researcher to call it and the realized-latency back-fill.

Format: JSON Lines at outputs/latency_log.jsonl. One object per detected divergence:
  {
    "logged_at", "ticker", "divergence_type", "source_connector", "detection_date",
    "attention_score", "positioning_score", "regime",
    "realized_time_to_price_days": null   # filled later by the scoring job
  }
"""

from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py) — added 2026-07-29 gap-close.
APPLIES_TO = {
    "kind": 'helper',
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ['corporate_ipo_dd'],
    "applies_universally": False,
    "summary": 'Append-only divergence->discovery log; knowledge-graph exhaust, not a source.',
}

import json
import os
from datetime import datetime, timezone
from typing import Any, Optional

_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "latency_log.jsonl")


def log_divergence(ticker: str,
                   divergence_type: str,
                   source_connector: str,
                   discovery: dict[str, Any],
                   detection_date: Optional[str] = None,
                   path: Optional[str] = None,
                   extra: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Append one divergence -> discovery-state row. `discovery` is a discovery_state() dict.

    Returns the row written. realized_time_to_price_days is left null for the later scoring job.
    """
    path = path or _LOG_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    row = {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "ticker": ticker,
        "divergence_type": divergence_type,
        "source_connector": source_connector,
        "detection_date": detection_date or (discovery.get("asof")),
        "attention_score": discovery.get("attention_score"),
        "positioning_score": discovery.get("positioning_score"),
        "regime": discovery.get("regime"),
        "confidence": discovery.get("confidence"),
        "realized_time_to_price_days": None,
    }
    if extra:
        row["extra"] = extra
    with open(path, "a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def read_log(path: Optional[str] = None) -> list[dict[str, Any]]:
    path = path or _LOG_PATH
    if not os.path.exists(path):
        return []
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


if __name__ == "__main__":
    # scaffold: write the header/first row from a fresh discovery_state so the file exists
    from .discovery_state import discovery_state
    ds = discovery_state("RCAT", asof="2026-06-24", company_name="Red Cat Holdings",
                         shares_outstanding=122_742_361)
    r = log_divergence("RCAT", divergence_type="example_short_thesis",
                       source_connector="conditioning_layer_scaffold", discovery=ds)
    print("wrote scaffold row:", json.dumps(r))
