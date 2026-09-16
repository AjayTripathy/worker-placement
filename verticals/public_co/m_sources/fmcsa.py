"""FMCSA SAFER motor carrier registry.

Two-step lookup: keyword search returns DOT numbers; carrier snapshot returns
fleet size (Power Units), driver count, and legal name.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["42"],
    "issuer_features": ["motor_carrier_operator"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "FMCSA SAFER registry; fleet size and driver counts verify claimed trucking scale.",
}

import re
import sys
import time
import urllib.parse

import httpx

UA = {"User-Agent": "Mozilla/5.0"}


def search_carrier(name_query: str) -> list[dict]:
    url = (
        f"https://safer.fmcsa.dot.gov/keywordx.asp?"
        f"searchstring=*{urllib.parse.quote(name_query)}*&SEARCHTYPE="
    )
    try:
        with httpx.Client(timeout=30, headers=UA) as c:
            r = c.get(url)
            if r.status_code != 200:
                return []
        carriers = []
        for m in re.finditer(
            r'query_string=(\d+)&original_query_string=([^"]+)"[^>]*>([^<]+)</a></B></th>\s*<td[^>]*>\s*<b>([^<]+)</b>',
            r.text,
        ):
            carriers.append({
                "dot_number": m.group(1),
                "name": m.group(3).strip(),
                "location": m.group(4).strip(),
            })
        return carriers
    except Exception as e:
        print(f"  fmcsa search error for {name_query}: {e}", file=sys.stderr)
        return []


def carrier_snapshot(dot_number: str) -> dict:
    url = (
        f"https://safer.fmcsa.dot.gov/query.asp?searchtype=ANY&"
        f"query_type=queryCarrierSnapshot&query_param=USDOT&query_string={dot_number}"
    )
    try:
        with httpx.Client(timeout=30, headers=UA) as c:
            r = c.get(url)
            if r.status_code != 200:
                return {"error": f"status_{r.status_code}"}
        txt = re.sub(r"<[^>]+>", " ", r.text)
        txt = re.sub(r"\s+", " ", txt)
        out: dict = {"dot_number": dot_number}
        m1 = re.search(r"Power Units:\s*(\d+)", txt)
        m2 = re.search(r"Drivers:\s*(\d+)", txt)
        m3 = re.search(r"MCS-150 Form Date:\s*(\d{2}/\d{2}/\d{4})", txt)
        m4 = re.search(r"Legal Name:\s*([^O]+?)(?=Operating Status|DBA|Physical)", txt)
        out["power_units"] = int(m1.group(1)) if m1 else None
        out["drivers"] = int(m2.group(1)) if m2 else None
        out["mcs150_form_date"] = m3.group(1) if m3 else None
        out["legal_name"] = m4.group(1).strip()[:80] if m4 else None
        return out
    except Exception as e:
        return {"error": str(e)}


def query_named_customers(customers: list[tuple[str, int | None]]) -> dict:
    """For each (name, claimed_truck_order) tuple, search SAFER, take exact name
    matches, fetch snapshot for each, and return per-customer fleet capacity."""
    out: dict = {}
    for name, claimed in customers:
        results = search_carrier(name)
        exact = [c for c in results if name.lower() in c["name"].lower()]
        chosen = exact[:3]
        snapshots = []
        for c in chosen:
            snap = carrier_snapshot(c["dot_number"])
            snap["name"] = c["name"]
            snap["location"] = c["location"]
            snapshots.append(snap)
            time.sleep(0.3)
        out[name] = {
            "claimed_truck_order": claimed,
            "search_term_results": len(results),
            "name_matches": len(exact),
            "carriers_inspected": snapshots,
        }
        time.sleep(0.5)
    return out
