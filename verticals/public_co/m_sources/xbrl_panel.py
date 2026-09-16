"""Shared XBRL companyfacts helper — builds quarterly time-series panels.

WHY THIS EXISTS

Several deterministic m-sources (working_capital_drift, runway_calculator,
share_count_drift, rpo_drift, sbc_quality_check) all need the same upstream
operation: pull SEC XBRL companyfacts for a CIK, extract a us-gaap tag's
quarterly time series, and align periods across tags. Building one shared
helper keeps tag-handling and period-alignment quirks in one place.

ENDPOINT
  https://data.sec.gov/api/xbrl/companyfacts/CIK{10-digit}.json

REQUIRES
  - User-Agent header identifying contact (SEC rule)
  - 10 req/sec rate limit (we don't hit it)

OUTPUT MODEL
  panel(cik, tags, cutoff_date) returns:
    {
      "cik": "0001234567",
      "entity_name": "Acme Corp",
      "cutoff_date": "2024-05-15",
      "tags": {
         "us-gaap:Inventory": [
            {"end": "2024-03-31", "val": 12345000, "fp": "Q1", "fy": 2024,
             "filed": "2024-05-08", "form": "10-Q"},
            ...
         ],
         ...
      },
      "missing_tags": ["us-gaap:DeferredRevenue", ...],
    }

TAG FALLBACKS

Different filers use different us-gaap tags for the same concept (e.g.,
"Inventory" vs "InventoryNet"). Callers pass alternates as a list; the
helper returns the first tag that has data.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "helper",
    "summary": "Shared XBRL companyfacts panel builder feeding the drift detectors; infra, never dispatched.",
}

from datetime import date
from typing import Any, Iterable, Optional

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

# Whitelist of accepted units per concept type. Many tags publish in both
# USD and shares; callers want to specify which.
DEFAULT_UNITS_PRIORITY = ["USD", "USD/shares", "shares", "pure"]


def _parse_date(s: str) -> Optional[date]:
    try:
        return date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        return None


def _fetch_companyfacts(cik: str) -> dict:
    cik_padded = str(cik).zfill(10) if not str(cik).startswith("CIK") else str(cik)[3:].zfill(10)
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"
    try:
        with httpx.Client(headers=HEADERS, timeout=60, follow_redirects=True) as c:
            r = c.get(url)
            if r.status_code != 200:
                return {"error": f"status_{r.status_code}", "cik": cik_padded}
            return r.json()
    except httpx.HTTPError as e:
        return {"error": f"http: {e}", "cik": cik_padded}


def _extract_tag_series(
    facts: dict,
    tag: str,
    cutoff: Optional[date],
    units_priority: list[str],
) -> list[dict]:
    """Pull observations for a single us-gaap tag, sorted by period end ascending.

    tag format: "us-gaap:Inventory" → looks up facts["us-gaap"]["Inventory"]["units"].
    """
    try:
        namespace, name = tag.split(":", 1)
    except ValueError:
        return []
    bag = (facts.get("facts") or {}).get(namespace, {}).get(name, {})
    units = bag.get("units") or {}
    if not units:
        return []

    chosen_unit = None
    for u in units_priority:
        if u in units:
            chosen_unit = u
            break
    if chosen_unit is None:
        chosen_unit = next(iter(units.keys()), None)
    if chosen_unit is None:
        return []

    out = []
    for obs in units[chosen_unit]:
        end = _parse_date(obs.get("end") or "")
        if end is None:
            continue
        if cutoff is not None and end > cutoff:
            continue
        filed = _parse_date(obs.get("filed") or "")
        if cutoff is not None and filed is not None and filed > cutoff:
            # No look-ahead: skip observations filed after the cutoff even
            # if the period ended before.
            continue
        out.append({
            "end":   str(end),
            "val":   obs.get("val"),
            "fp":    obs.get("fp"),
            "fy":    obs.get("fy"),
            "form":  obs.get("form"),
            "filed": str(filed) if filed else None,
            "unit":  chosen_unit,
            "accn":  obs.get("accn"),
        })
    out.sort(key=lambda o: o["end"])
    return out


def panel(
    cik: str,
    tags: list[str | tuple[str, ...]],
    cutoff_date: str,
    *,
    units_priority: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Pull a multi-tag time-series panel for the CIK.

    Args:
      cik: 10-digit padded CIK.
      tags: list of us-gaap tags. Each entry can be:
            - a single tag string ("us-gaap:Inventory")
            - a tuple of fallback alternates (("us-gaap:Inventory",
              "us-gaap:InventoryNet")) — first one with data wins.
      cutoff_date: ISO YYYY-MM-DD. Drops observations filed or period-ended
            after cutoff (no look-ahead).
      units_priority: ordered list of preferred unit codes; defaults to
            ["USD","USD/shares","shares","pure"].

    Returns:
      {
        "cik": "...",
        "entity_name": "...",
        "cutoff_date": "...",
        "tags": {requested_tag_or_first_alt: [obs, ...]},
        "missing_tags": [...],
        "_resolved_tag": {requested: actually_used_tag},
        "_note": "...",
      }
    """
    cutoff = _parse_date(cutoff_date)
    if cutoff is None:
        return {"error": f"bad cutoff_date={cutoff_date!r}"}

    facts = _fetch_companyfacts(cik)
    if "error" in facts:
        return facts

    units_priority = units_priority or DEFAULT_UNITS_PRIORITY

    out_tags: dict[str, list[dict]] = {}
    missing: list[str] = []
    resolved: dict[str, str] = {}

    for entry in tags:
        if isinstance(entry, str):
            alts = [entry]
            key = entry
        else:
            alts = list(entry)
            key = alts[0]

        series: list[dict] = []
        used = None
        for alt in alts:
            s = _extract_tag_series(facts, alt, cutoff, units_priority)
            if s:
                series = s
                used = alt
                break

        if series:
            out_tags[key] = series
            resolved[key] = used or key
        else:
            missing.append(key)

    return {
        "cik": str(cik).zfill(10),
        "entity_name": facts.get("entityName"),
        "cutoff_date": cutoff_date,
        "tags": out_tags,
        "missing_tags": missing,
        "_resolved_tag": resolved,
    }


def quarterly_series(observations: list[dict]) -> list[dict]:
    """Filter a tag's observations to quarter-end periods only.

    Companyfacts mixes quarterly (Q1/Q2/Q3) and FY annual periods. For
    panel analyses we usually want clean Q1/Q2/Q3/Q4 quarter-ends.
    Treats fp=="FY" or form=="10-K" as Q4 (period-end matches FY end).
    """
    seen_ends: set[str] = set()
    out = []
    for o in observations:
        end = o.get("end")
        if not end or end in seen_ends:
            continue
        fp = o.get("fp") or ""
        form = o.get("form") or ""
        if fp in ("Q1", "Q2", "Q3", "FY") or form == "10-K":
            out.append(o)
            seen_ends.add(end)
    out.sort(key=lambda o: o["end"])
    return out


def latest_n_quarters(observations: list[dict], n: int) -> list[dict]:
    q = quarterly_series(observations)
    return q[-n:] if len(q) >= n else q


if __name__ == "__main__":
    import json
    import sys
    cik = sys.argv[1] if len(sys.argv) > 1 else "0000320193"  # AAPL
    cutoff = sys.argv[2] if len(sys.argv) > 2 else "2024-05-15"
    p = panel(
        cik,
        tags=[
            ("us-gaap:Inventory", "us-gaap:InventoryNet"),
            "us-gaap:AccountsReceivableNetCurrent",
            "us-gaap:Revenues",
            "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        ],
        cutoff_date=cutoff,
    )
    # Just dump tag counts to keep output small
    print(json.dumps({
        "cik": p.get("cik"),
        "entity": p.get("entity_name"),
        "missing": p.get("missing_tags"),
        "counts": {k: len(v) for k, v in (p.get("tags") or {}).items()},
        "latest_inventory": (p.get("tags") or {}).get("us-gaap:Inventory", [])[-2:],
    }, indent=2, default=str))
