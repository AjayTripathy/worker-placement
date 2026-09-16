"""MSRB EMMA Material Event Notice (MEN) lookup.

WHY THIS EXISTS

Hospital muni obligors disclose material credit events via MSRB EMMA
continuing-disclosure filings — Rule 15c2-12 mandates 14 specific event
types including:
  1.03 — Bankruptcy/Receivership
  2.04 — Modifications to rights of bond holders / covenant violations
  3.02 — Adverse tax events
  5.01 — Rating change
  5.07 — Material event modifications
  6.01 — Tender offers
  Default-on-debt (multiple sub-codes)

A hospital like Tower Health is rated CCC- not because their facility-
level operating margins are bad (they're middling) but because they've
filed multiple MENs disclosing covenant violations and missed payments.
CMS HCRIS cannot see these; only EMMA can.

DATA ACCESS LIMITS

EMMA's REST endpoint at api.emma.msrb.org is NOT publicly documented.
The web interface (emma.msrb.org) is server-rendered .aspx pages that
require browser-style scraping.

For this MVP we use TWO paths:
  1. CSV bulk dataport from msrb.org/EMMA-Dataport (requires registration,
     ~$0 for non-commercial use)
  2. Hand-curated MEN log for known distressed obligors

In production, an MSRB subscription ($1K-5K/yr depending on tier) gives
clean structured access.

CURRENT IMPLEMENTATION

For this MVP, we load a hand-curated MEN database covering the 31 hospital
systems in our top-30 universe. This is enough to demonstrate the signal
mechanic; expand to live scraping once EMMA structured access is set up.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

HERE = Path(__file__).parent
DATA = HERE / "data" / "emma_material_events.json"

# Severity classifier for MEN codes
EVENT_CODE_SEVERITY = {
    "1.01": "MODERATE",  # principal/interest payment delinquency
    "1.02": "SEVERE",    # non-payment-related default
    "1.03": "RED_FLAG",  # bankruptcy / receivership
    "2.04": "SEVERE",    # modifications to rights of bond holders
    "3.01": "MODERATE",  # adverse tax events affecting tax-exemption
    "3.02": "SEVERE",    # IRS determinations of taxability
    "4.01": "MODERATE",  # release/substitution of collateral
    "5.01": "MODERATE",  # rating change (direction-dependent)
    "5.07": "MODERATE",  # material event modifications
    "6.01": "MODERATE",  # tender offers
    "8.01": "MODERATE",  # consummation of merger / acquisition
    "9.01": "MODERATE",  # appointment of trustee
}


def query_obligor_events(
    obligor_name: str,
    cutoff_date: str,
    lookback_days: int = 730,
) -> dict:
    """Look up Material Event Notices for an obligor.

    Args:
      obligor_name: e.g., "Tower Health"
      cutoff_date: ISO YYYY-MM-DD
      lookback_days: trailing window to scan
    """
    if not DATA.exists():
        return {
            "signal": "UNVERIFIABLE",
            "severity": "UNVERIFIABLE",
            "direction": "neutral",
            "_note": (
                f"EMMA MEN cache missing at {DATA}. Either (a) register at "
                "msrb.org/EMMA-Dataport and populate from bulk CSV download, "
                "or (b) hand-curate known events for now."
            ),
        }

    db = json.loads(DATA.read_text())
    from datetime import date as _date, timedelta as _td
    try:
        cd = _date.fromisoformat(cutoff_date[:10])
        floor = cd - _td(days=lookback_days)
    except Exception:
        return {"signal": "ERROR", "_note": f"bad cutoff {cutoff_date}"}

    # Match obligor — exact OR substring (case-insensitive)
    obligor_l = obligor_name.lower()
    matched_events = []
    for event in db.get("events", []):
        e_obligor = (event.get("obligor") or "").lower()
        if obligor_l in e_obligor or e_obligor in obligor_l:
            try:
                e_date = _date.fromisoformat(event.get("filing_date", "")[:10])
            except Exception:
                continue
            if floor <= e_date <= cd:
                matched_events.append(event)

    if not matched_events:
        return {
            "signal":     "NO_MEN_24M",
            "severity":   "PASS",
            "direction":  "positive",
            "n_events":   0,
            "_note":      f"No Material Event Notices in trailing {lookback_days/365:.1f} years.",
        }

    # Aggregate
    severity_rank = {"PASS": 0, "MODERATE": 1, "SEVERE": 2, "RED_FLAG": 3}
    max_sev = "PASS"
    by_code = {}
    for e in matched_events:
        code = e.get("event_code", "?")
        sev = EVENT_CODE_SEVERITY.get(code, "MODERATE")
        by_code[code] = by_code.get(code, 0) + 1
        if severity_rank[sev] > severity_rank[max_sev]:
            max_sev = sev

    sev_to_severity = {
        "PASS": ("MEN_CLEAN", "PASS"),
        "MODERATE": ("MEN_MODERATE_EVENTS", "MODERATE_UNDERDELIVERY"),
        "SEVERE": ("MEN_SEVERE_EVENTS", "SEVERE_UNDERDELIVERY"),
        "RED_FLAG": ("MEN_BANKRUPTCY", "RED_FLAG_NEGATIVE"),
    }
    signal_label, severity = sev_to_severity[max_sev]

    return {
        "signal":     signal_label,
        "severity":   severity,
        "direction":  "negative" if severity != "PASS" else "positive",
        "n_events":   len(matched_events),
        "events_by_code": by_code,
        "events":     matched_events[:10],
        "_note":      f"{len(matched_events)} MEN(s) in {lookback_days}d; codes={by_code}",
    }


if __name__ == "__main__":
    import sys
    obligor = sys.argv[1] if len(sys.argv) > 1 else "Tower Health"
    cutoff = sys.argv[2] if len(sys.argv) > 2 else "2024-12-31"
    print(json.dumps(query_obligor_events(obligor, cutoff), indent=2, default=str))
