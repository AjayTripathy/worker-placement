"""openFDA APIs — drug approvals, recalls, inspection citations, Warning Letters.

Two endpoint families:

1. Drug approvals (Drugs@FDA)
   https://api.fda.gov/drug/drugsfda.json
   Field of art: openfda.manufacturer_name. Has issuer ever shipped a drug?

2. Inspection citations (Form FDA-483 / Warning Letters proxy via 'enforcement')
   https://api.fda.gov/drug/enforcement.json
   https://api.fda.gov/food/enforcement.json
   https://api.fda.gov/device/enforcement.json
   Field of art: recalling_firm.

   Note: openFDA does not expose a clean Warning-Letter endpoint; the
   Inspection Classification Database (ICD) requires HHS data.gov. For
   the IJR backtest we use 'enforcement' recall events as the catastrophe
   proxy — Class I recalls are the highest-signal events and correlate
   strongly with WL issuance ~6-12 months later.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": ["283", "384"],
    "issuer_features": ["marketed_drug_or_device"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "m_source",
    "summary": "openFDA approvals/recalls/enforcement; has the issuer ever shipped a drug, and is quality cracking?",
}

import urllib.parse
from typing import Any

import httpx

HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

_RECALL_SEVERITY = {
    "CLEAN":               "PASS",
    "ROUTINE_RECALLS":     "PASS",
    "CLASS_II_PATTERN":    "MODERATE_UNDERDELIVERY",
    "CLASS_I_RECENT":      "SEVERE_UNDERDELIVERY",
    "MULTIPLE_CLASS_I":    "RED_FLAG_NEGATIVE",
    "UNVERIFIABLE":        "UNVERIFIABLE",
}


def query_approved_drugs(manufacturer_name: str) -> dict:
    """List FDA-approved drug applications for a manufacturer."""
    q = f'openfda.manufacturer_name:"{manufacturer_name}"'
    url = f"https://api.fda.gov/drug/drugsfda.json?search={urllib.parse.quote(q)}&limit=50"
    try:
        with httpx.Client(timeout=30, headers=HEADERS) as c:
            r = c.get(url)
            if r.status_code == 404:
                return {
                    "manufacturer_searched": manufacturer_name,
                    "n_approved_applications": 0,
                    "applications": [],
                }
            if r.status_code != 200:
                return {"error": f"status_{r.status_code}"}
            data = r.json()
    except Exception as e:
        return {"error": str(e)}

    apps = []
    brand_names: set[str] = set()
    for r in data.get("results", []):
        app = {
            "application_number": r.get("application_number"),
            "sponsor_name": r.get("sponsor_name"),
            "products": [],
        }
        for p in r.get("products", []) or []:
            brand = p.get("brand_name")
            if brand:
                brand_names.add(brand)
            app["products"].append({
                "brand": brand,
                "active_ingredient": ", ".join(
                    a.get("name", "") for a in (p.get("active_ingredients") or [])
                ),
                "marketing_status": p.get("marketing_status"),
                "dosage_form": p.get("dosage_form"),
            })
        apps.append(app)

    return {
        "manufacturer_searched": manufacturer_name,
        "n_approved_applications": data.get("meta", {}).get("results", {}).get("total", 0),
        "n_unique_brands": len(brand_names),
        "brand_names": sorted(brand_names),
        "applications": apps[:10],
    }


def query_inspection_history(
    firm_name: str,
    cutoff_date: str,
    *,
    lookback_years: int = 5,
    endpoints: tuple[str, ...] = ("drug", "device", "food"),
) -> dict[str, Any]:
    """Recall events for a firm across drug/device/food enforcement endpoints.

    Catastrophe proxy: Class I recalls in the past 24 months = SEVERE.
    Multiple Class I = RED_FLAG_NEGATIVE. Class II only = MODERATE.

    Args:
      firm_name: recalling_firm value (case-insensitive substring).
      cutoff_date: ISO YYYY-MM-DD; ignore recall events recorded after.
      lookback_years: years of recall history to scan (default 5).
      endpoints: subset of ("drug","device","food").

    Returns: {signal, severity, direction, metrics, recalls}.
    """
    from datetime import date as _date, timedelta as _td

    try:
        cutoff = _date.fromisoformat(cutoff_date[:10])
    except (ValueError, TypeError):
        return {"signal": "UNVERIFIABLE", "severity": "UNVERIFIABLE",
                "direction": "neutral", "_note": f"bad cutoff {cutoff_date}"}

    start = cutoff - _td(days=lookback_years * 365)
    recent_24m_floor = cutoff - _td(days=730)

    fnq = firm_name.replace('"', "")
    date_q = f"[{start.strftime('%Y%m%d')}+TO+{cutoff.strftime('%Y%m%d')}]"

    all_recalls: list[dict] = []

    for ep in endpoints:
        q = (
            f'recalling_firm:"{fnq}"+AND+recall_initiation_date:{date_q}'
        )
        url = f"https://api.fda.gov/{ep}/enforcement.json?search={urllib.parse.quote(q, safe='+[]:')}&limit=100"
        try:
            with httpx.Client(timeout=30, headers=HEADERS) as c:
                r = c.get(url)
                if r.status_code == 404:
                    continue
                if r.status_code != 200:
                    continue
                data = r.json()
        except Exception:
            continue

        for rec in data.get("results", []) or []:
            init_str = rec.get("recall_initiation_date") or ""
            try:
                init = _date(int(init_str[0:4]), int(init_str[4:6]), int(init_str[6:8]))
            except (ValueError, IndexError):
                continue
            if init > cutoff:
                continue
            all_recalls.append({
                "endpoint":           ep,
                "recall_initiation":  init.isoformat(),
                "classification":     rec.get("classification"),
                "status":             rec.get("status"),
                "product_description": (rec.get("product_description") or "")[:200],
                "reason_for_recall":   (rec.get("reason_for_recall") or "")[:200],
                "recalling_firm":      rec.get("recalling_firm"),
            })

    n_total = len(all_recalls)
    class1 = [r for r in all_recalls if r["classification"] == "Class I"]
    class2 = [r for r in all_recalls if r["classification"] == "Class II"]
    class1_recent = [r for r in class1
                     if _date.fromisoformat(r["recall_initiation"]) >= recent_24m_floor]

    if not all_recalls:
        signal = "CLEAN"
    elif len(class1_recent) >= 2:
        signal = "MULTIPLE_CLASS_I"
    elif class1_recent:
        signal = "CLASS_I_RECENT"
    elif len(class2) >= 3:
        signal = "CLASS_II_PATTERN"
    else:
        signal = "ROUTINE_RECALLS"

    direction = (
        "positive" if signal == "CLEAN"
        else "neutral" if signal == "ROUTINE_RECALLS"
        else "negative"
    )

    return {
        "firm_searched":  firm_name,
        "cutoff_date":    cutoff_date,
        "signal":         signal,
        "severity":       _RECALL_SEVERITY[signal],
        "direction":      direction,
        "metrics": {
            "n_recalls_total":    n_total,
            "n_class_i":          len(class1),
            "n_class_i_24m":      len(class1_recent),
            "n_class_ii":         len(class2),
            "endpoints_scanned":  list(endpoints),
        },
        "recalls_sample": all_recalls[:5],
        "_note": (
            f"{n_total} recall event(s) in {lookback_years}y; "
            f"{len(class1)} Class I ({len(class1_recent)} within 24m of cutoff)."
        ),
    }

