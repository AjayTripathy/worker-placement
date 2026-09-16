"""MAUDE complaint-velocity engine — tests whether the public openFDA device
adverse-event stream LEADS Class I device recall announcements (MAUDE_VELOCITY_SPEC.md).

Two openFDA endpoints (no auth; 240 req/min, 1000/day unauth — keep N modest or set OPENFDA_KEY):
  - device/enforcement.json : recall ground truth (classification, recall_initiation_date,
                              recalling_firm, product_code, reason_for_recall)
  - device/event.json       : MAUDE MDRs (date_received [observability stamp], date_of_event,
                              device.device_report_product_code, device.manufacturer_d_name, event_type)

CORRECTNESS CONTRACT (§3/§5): the MAUDE time series is indexed by `date_received`, never
`date_of_event`. As-of date D, the observable trailing count is exactly the reports with
date_received <= D — point-in-time by construction (the analogue of gov-contract G-4 load-date
censoring). The leak-check re-runs on date_of_event to quantify the phantom-lead inflation.
"""
from __future__ import annotations

import os
import time
import urllib.parse
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Optional

import httpx

_BASE = "https://api.fda.gov"
HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}
_KEY = os.environ.get("OPENFDA_KEY", "").strip()


def _get(path: str, params: dict, *, retries: int = 4) -> Optional[dict]:
    """GET an openFDA endpoint; returns parsed JSON or None on 404/empty."""
    if _KEY:
        params = {**params, "api_key": _KEY}
    _SAFE = '+[]:"'
    url = f"{_BASE}/{path}?{urllib.parse.urlencode(params, safe=_SAFE)}"
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=40, headers=HEADERS) as c:
                r = c.get(url)
            if r.status_code == 404:
                return None  # openFDA returns 404 for zero results
            if r.status_code == 429:
                time.sleep(2 + attempt * 3)
                continue
            if r.status_code != 200:
                time.sleep(1 + attempt)
                continue
            return r.json()
        except Exception:
            time.sleep(1 + attempt)
    return None


def _pd(s: str) -> Optional[date]:
    """Parse an openFDA YYYYMMDD (or YYYY-MM-DD) date string."""
    if not s:
        return None
    s = s.replace("-", "")
    if len(s) < 8:
        return None
    try:
        return date(int(s[0:4]), int(s[4:6]), int(s[6:8]))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Phase 1 feasibility
# ---------------------------------------------------------------------------

def fetch_class1_recalls(start: str, end: str, *, limit_total: int = 600) -> list[dict]:
    """All Class I device recall RECORDS (one per Z-number) from device/enforcement.

    enforcement has classification + recall_initiation_date + recalling_firm + reason
    but NOT product_code — that is enriched from device/recall.json (see enrich_product_code).
    """
    dq = f"[{start.replace('-','')}+TO+{end.replace('-','')}]"
    search = f'classification:"Class+I"+AND+recall_initiation_date:{dq}'
    out: list[dict] = []
    skip = 0
    while skip < limit_total:
        data = _get("device/enforcement.json",
                    {"search": search, "limit": 100, "skip": skip})
        if not data or not data.get("results"):
            break
        for r in data["results"]:
            out.append({
                "recall_number": r.get("recall_number"),
                "recalling_firm": r.get("recalling_firm"),
                "recall_initiation_date": r.get("recall_initiation_date"),
                "report_date": r.get("report_date"),
                "classification": r.get("classification"),
                "product_description": (r.get("product_description") or "")[:300],
                "reason_for_recall": (r.get("reason_for_recall") or "")[:500],
            })
        total = data.get("meta", {}).get("results", {}).get("total", 0)
        skip += 100
        if skip >= total:
            break
        time.sleep(0.25)
    return out


def class1_total(start: str, end: str) -> int:
    dq = f"[{start.replace('-','')}+TO+{end.replace('-','')}]"
    data = _get("device/enforcement.json",
                {"search": f'classification:"Class+I"+AND+recall_initiation_date:{dq}',
                 "limit": 1})
    return (data or {}).get("meta", {}).get("results", {}).get("total", 0)


def enrich_product_code(recall_number: str) -> Optional[dict]:
    """Look up product_code + structured root_cause_description from device/recall.json
    via the shared Z-number (enforcement.recall_number == recall.product_res_number)."""
    data = _get("device/recall.json",
                {"search": f'product_res_number:"{recall_number}"', "limit": 1})
    if not data or not data.get("results"):
        return None
    r = data["results"][0]
    return {
        "product_code": r.get("product_code"),
        "root_cause_description": r.get("root_cause_description"),
        "event_date_initiated": r.get("event_date_initiated"),
        "event_date_posted": r.get("event_date_posted"),
        "device_name": (r.get("openfda", {}) or {}).get("device_name"),
    }


def measure_reporting_lag(product_codes: list[str], *, per_code: int = 100) -> dict:
    """§5 / Phase-1: distribution of (date_received - date_of_event) across MAUDE.

    The make-or-break feasibility number: if this lag >> defect burn time, channel is dead.
    """
    lags: list[int] = []
    for pc in product_codes:
        data = _get("device/event.json",
                    {"search": f'device.device_report_product_code:"{pc}"',
                     "limit": per_code, "sort": "date_received:desc"})
        if not data:
            continue
        for r in data.get("results", []):
            dr = _pd(r.get("date_received", ""))
            de = _pd(r.get("date_of_event", ""))
            if dr and de and dr >= de:
                d = (dr - de).days
                if 0 <= d <= 3650:  # drop obvious garbage dates
                    lags.append(d)
        time.sleep(0.3)
    lags.sort()
    if not lags:
        return {"n": 0}
    n = len(lags)
    return {
        "n": n,
        "median_days": lags[n // 2],
        "p25_days": lags[n // 4],
        "p75_days": lags[(3 * n) // 4],
        "p90_days": lags[int(0.9 * n)],
        "mean_days": round(sum(lags) / n, 1),
    }


# ---------------------------------------------------------------------------
# Phase 2 signal
# ---------------------------------------------------------------------------

def fetch_maude_series(firm_tokens: list[str], product_code: str,
                       before: date, *, lookback_days: int = 760,
                       date_field: str = "date_received") -> list[date]:
    """Daily MDR-receipt histogram for (manufacturer-token × product_code) in
    [before-lookback, before], via openFDA `count=` aggregation (one call).

    The manufacturer is filtered SERVER-SIDE on the single most-distinctive firm token
    (longest), so the count histogram is already firm-scoped — no per-record pagination.
    date_field: 'date_received' (point-in-time, default) or 'date_of_event' (leak-check only).
    Returns the list of dates expanded by count (one entry per MDR), all <= `before`.
    """
    start = before - timedelta(days=lookback_days)
    dq = f"[{start.strftime('%Y%m%d')}+TO+{before.strftime('%Y%m%d')}]"
    toks = sorted([t for t in firm_tokens if len(t) >= 3], key=len, reverse=True)
    mfr_clause = f'+AND+device.manufacturer_d_name:{toks[0].lower()}' if toks else ""
    search = (f'device.device_report_product_code:"{product_code}"'
              f'+AND+{date_field}:{dq}{mfr_clause}')
    data = _get("device/event.json", {"search": search, "count": date_field})
    dates: list[date] = []
    if not data:
        return dates
    for bucket in data.get("results", []):
        d = _pd(bucket.get("time", ""))
        if d and d <= before:
            dates.extend([d] * int(bucket.get("count", 0)))
    dates.sort()
    return dates


def _trailing_count(dates: list[date], asof: date, window: int) -> int:
    lo = asof - timedelta(days=window)
    return sum(1 for d in dates if lo < d <= asof)


def detect_spike(dates: list[date], announcement: date, *,
                 window: int = 30, baseline_days: int = 365,
                 baseline_gap: int = 90, mult: float = 3.0,
                 sigma: float = 3.0, min_baseline: float = 3.0) -> dict:
    """§3 spike detector. Returns {fired, spike_date, lead_days, baseline_rate, peak_count}.

    Baseline = mean trailing-`window` count over [ann-baseline_days-gap, ann-gap], i.e. the
    pre-spike regime ending >= baseline_gap days before announcement. Spike threshold =
    max(baseline*mult, baseline + sigma*sqrt(baseline)). First crossing in (ann-365, ann] wins.
    """
    if not dates:
        return {"fired": False, "reason": "no_maude_history"}
    # baseline window
    b_end = announcement - timedelta(days=baseline_gap)
    b_start = b_end - timedelta(days=baseline_days)
    b_dates = [d for d in dates if b_start < d <= b_end]
    # baseline mean 30d rate over the baseline window (sample at weekly steps)
    samples = []
    step = b_start
    while step <= b_end:
        samples.append(_trailing_count(dates, step, window))
        step += timedelta(days=7)
    baseline = (sum(samples) / len(samples)) if samples else 0.0
    baseline = max(baseline, 0.0)
    if baseline < min_baseline:
        return {"fired": False, "reason": "sparse_baseline",
                "baseline_rate": round(baseline, 2), "n_total": len(dates)}
    threshold = max(baseline * mult, baseline + sigma * (baseline ** 0.5))
    # scan forward day-by-day from (ann-365) to ann for first crossing
    scan = announcement - timedelta(days=365)
    first_spike = None
    peak = 0
    while scan <= announcement:
        c = _trailing_count(dates, scan, window)
        peak = max(peak, c)
        if first_spike is None and c >= threshold:
            first_spike = scan
        scan += timedelta(days=1)
    if first_spike is None:
        return {"fired": False, "reason": "no_crossing",
                "baseline_rate": round(baseline, 2), "threshold": round(threshold, 2),
                "peak_count": peak, "n_total": len(dates)}
    return {
        "fired": True,
        "spike_date": first_spike.isoformat(),
        "lead_days": (announcement - first_spike).days,
        "baseline_rate": round(baseline, 2),
        "threshold": round(threshold, 2),
        "peak_count": peak,
        "n_total": len(dates),
    }


# ---------------------------------------------------------------------------
# Root-cause classifier (§5 LOCKED keyword lists)
# ---------------------------------------------------------------------------

_SUDDEN = ["lot", "manufacturing defect", "contamination", "sterility", "specific lots",
           "particulate", "seal", "leak in", "single lot", "out of specification",
           "component from supplier", "assembly error"]
_SLOW = ["software", "firmware", "design", "wear", "degradation", "battery", "over time",
         "may fail", "cybersecurity", "false alarm", "under-delivery", "occlusion",
         "inaccurate", "algorithm", "chronic"]


def classify_root_cause(text: str) -> str:
    t = (text or "").lower()
    sudden = any(k in t for k in _SUDDEN)
    slow = any(k in t for k in _SLOW)
    if sudden and not slow:
        return "SUDDEN"
    if slow and not sudden:
        return "SLOW_BURN"
    return "AMBIGUOUS"


# Amendment M-1: map the STRUCTURED FDA root_cause_description field (cleaner than the
# free-text keyword lists in §5) to the slow-burn/sudden buckets. Original §5 lists kept
# as a fallback for records lacking the structured field.
_RC_SLOW = {
    "device design", "software design", "component design/selection", "software change control",
    "labeling design", "process design", "software in the use environment", "package design/selection",
    "design", "software", "use error",
}
_RC_SUDDEN = {
    "nonconforming material/component", "material/component contamination",
    "mixed-up of materials/components", "packaging", "employee error", "process control",
    "release of material/component prior to receiving test results", "storage",
    "equipment maintenance", "labeling mix-ups", "environmental control",
    "process change control", "manufacturing", "contamination", "component",
}


def classify_root_cause_structured(rc: str, reason_fallback: str = "") -> str:
    """SLOW_BURN / SUDDEN / AMBIGUOUS from the structured root_cause_description; falls back
    to the §5 free-text classifier on the reason string when the field is missing/unknown."""
    k = (rc or "").strip().lower()
    if k in _RC_SLOW:
        return "SLOW_BURN"
    if k in _RC_SUDDEN:
        return "SUDDEN"
    # 'Under Investigation by firm', 'Other', 'Unknown/Undetermined', '' -> fall back
    return classify_root_cause(reason_fallback)


def firm_tokens(firm: str) -> list[str]:
    """Distinctive tokens from a recalling_firm name for the fuzzy manufacturer gate."""
    stop = {"inc", "inc.", "llc", "corp", "corporation", "company", "co", "ltd", "the",
            "medical", "devices", "device", "systems", "international", "usa", "us",
            "technologies", "technology", "products", "manufacturing", "and", "of"}
    toks = []
    for w in (firm or "").replace(",", " ").replace(".", " ").split():
        wl = w.lower()
        if wl in stop or len(wl) < 3:
            continue
        toks.append(w)
    return toks[:3]
