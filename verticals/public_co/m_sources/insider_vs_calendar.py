"""
Insider-sale × federal-budget-calendar overlay.

WHY THIS EXISTS
The canonical YSS / IONQ short-thesis tell: insiders dump shares on or
within days of a federal budget action that quietly de-funds the
company's primary customer program. Both Wolfpack reports cite specific
dates: IONQ's ex-CEO Chapman sold $37.5M on March 11, 2025 — the day the
House passed FY25 appropriations confirming the AFRL earmark was gone.

usaspending and pentagon_jbook are M-source verifiers; this is the
TEMPORAL detector — it answers "did insiders sell within N days of a
budget event that materially changed the company's revenue outlook?"

DATA SOURCES
1. SEC EDGAR submissions API for Form 4 filings (free, no key)
2. Budget calendar JSON in data/_budget_calendar/events.json

A Form 4 sale is "proximate" if it falls within ±window_days of any
listed budget event. Transaction code distinguishes discretionary
sales (S, F) from automatic 10b5-1 sales (S with footnote indicator);
the connector flags non-10b5-1 sales separately.

SIGNAL ENUM
  NO_PROXIMATE_SALES               — no insider sales in window
  ROUTINE_10B5_1                   — sales within window but all 10b5-1 (pre-planned)
  PROXIMATE_DISCRETIONARY          — discretionary sales within window (1-2 owners)
  CLUSTERED_DISCRETIONARY          — multiple insiders selling discretionarily within
                                      window AND (a) issuer has named-program exposure
                                      in pentagon_jbook by_entity index AND (b) at
                                      least one matched event's summary references
                                      the issuer's contractor name or a program
                                      they're tagged on. This is the canonical
                                      IONQ-pattern signal — both validators must
                                      pass.
  CLUSTERED_DISCRETIONARY_UNCONFIRMED — multiple insiders selling discretionarily
                                      within window BUT validator 1 or 2 fails.
                                      Temporal coincidence likely; not the
                                      IONQ-pattern. Common case: services prime
                                      with sales near earnings or vesting cycle
                                      that happens to overlap a budget event.

VALIDATORS (added 2026-05-24 after TDG/CACI false-positive review)
  validator 1: program_exposure_required — pass contractor_name; we look up
               whether the issuer has named-program exposure in by_entity.json.
               No exposure → signal can't be the IONQ pattern by construction.
  validator 2: event_content_relevance — for each matched event, check whether
               the event summary mentions the issuer's contractor name or any
               program they're tagged on. No event mentions → temporal-
               coincidence; the budget event was not specifically about this
               issuer's programs.

If both validators pass for any matched event, the discretionary signal
escalates to CLUSTERED_DISCRETIONARY. If either fails, it degrades to
CLUSTERED_DISCRETIONARY_UNCONFIRMED. Backwards-compatible: callers that
don't pass contractor_name get the legacy CLUSTERED_DISCRETIONARY behavior.
"""

from __future__ import annotations

APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["government_customer_concentration_above_5pct", "mentions_dod_program"],
    "asset_classes": ["public_equity_forensics"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Overlays insider sales on the federal budget calendar; sales timed to quiet de-funding events (YSS/IONQ tell).",
}

import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import httpx

HERE = Path(__file__).parent.parent / "data" / "_budget_calendar"
DEFAULT_CALENDAR = HERE / "events.json"
HEADERS = {"User-Agent": "Signal OS Research backtest@signalos.local"}

_CACHE: Optional[dict] = None

# EDGAR fair-use guidance: ≤10 req/sec. We throttle to ~7 req/sec sustained
# and back off aggressively on 429s. Both numbers are conservative because
# bulk-detector runs can otherwise trip global rate limits silently.
_MIN_GAP_SEC = 0.15
_BACKOFF_INITIAL = 1.5
_BACKOFF_MAX = 30.0
_last_request_ts: float = 0.0


def _throttled_get(url: str, *, max_retries: int = 4) -> Optional["httpx.Response"]:
    """GET with global throttle + exponential backoff on 429.

    Returns None on persistent failure so callers can decide whether to
    surface the error or skip silently."""
    global _last_request_ts
    import time as _time
    backoff = _BACKOFF_INITIAL
    for attempt in range(max_retries + 1):
        gap = _time.time() - _last_request_ts
        if gap < _MIN_GAP_SEC:
            _time.sleep(_MIN_GAP_SEC - gap)
        try:
            r = httpx.get(url, headers=HEADERS, timeout=30,
                          follow_redirects=True)
            _last_request_ts = _time.time()
        except Exception:
            return None
        if r.status_code == 429:
            _time.sleep(min(backoff, _BACKOFF_MAX))
            backoff *= 2
            continue
        return r
    return None


def _load_calendar(json_path: Optional[Path] = None) -> list[dict]:
    """Load budget-calendar events from JSON. Cached after first load."""
    global _CACHE
    if _CACHE is not None:
        return _CACHE.get("events") or []
    p = Path(json_path) if json_path else DEFAULT_CALENDAR
    if not p.exists():
        _CACHE = {"events": []}
        return []
    _CACHE = json.loads(p.read_text())
    return _CACHE.get("events") or []


def _fetch_form4_filings(cik: str, start_date: str, end_date: str) -> list[dict]:
    """Pull Form 4 (insider transactions) filings for a CIK in a date window.
    Returns one entry per filing: {accession, filing_date, primary_doc, owner_name}."""
    cik_padded = str(cik).zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
    r = _throttled_get(url)
    if r is None or r.status_code != 200:
        return []
    try:
        j = r.json()
    except Exception:
        return []

    recent = j.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accs = recent.get("accessionNumber", [])
    pris = recent.get("primaryDocument", [])
    pri_descs = recent.get("primaryDocDescription", [])

    out = []
    for i, f in enumerate(forms):
        if f not in ("4", "4/A"):
            continue
        d = dates[i] if i < len(dates) else ""
        if not (start_date <= d <= end_date):
            continue
        out.append({
            "form":        f,
            "filing_date": d,
            "accession":   accs[i]  if i < len(accs)  else "",
            "primary_doc": pris[i]  if i < len(pris)  else "",
            "doc_desc":    pri_descs[i] if i < len(pri_descs) else "",
        })
    return out


# Form 4 XML transaction codes (per SEC):
#  P = Open-market purchase   S = Open-market sale (discretionary)
#  A = Grant/award            M = Exercise/conversion of derivative
#  F = Tax withholding (forced sale, sometimes flagged "discretionary")
#  G = Gift                   J = Other (often plan-related)
#  D = Disposition to issuer
_SALE_CODES = {"S", "F"}  # F is forced but often counts toward concentration
_DISCRETIONARY_CODES = {"S"}  # Strict discretionary sales


def _parse_form4_xml(cik_int: int, accession: str, primary_doc: str) -> list[dict]:
    """Parse a Form 4 XML document. Returns list of transaction dicts:
    {tx_date, code, shares, price_per_share, value_usd, is_10b5_1, owner_name}."""
    acc_no_dashes = accession.replace("-", "")
    # EDGAR's primary_doc for Form 4 typically points at an XSL-rendered
    # viewer like "xslF345X06/ownership.xml" — but that URL returns HTML,
    # not XML. Strip the XSL transform directory to get raw XML.
    raw_doc = re.sub(r"^xsl[A-Za-z0-9]+/", "", primary_doc)
    url = (f"https://www.sec.gov/Archives/edgar/data/{cik_int}/"
           f"{acc_no_dashes}/{raw_doc}")
    r = _throttled_get(url)
    if r is None or r.status_code != 200:
        return []
    text = r.text

    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []

    # Owner name
    owner_name = ""
    for el in root.iter("rptOwnerName"):
        owner_name = (el.text or "").strip()
        break

    # 10b5-1 indicator (footnote referenced by transactionFootnote — best-effort)
    full_lower = text.lower()
    likely_10b5_1 = (
        "rule 10b5-1" in full_lower
        or "10b5-1 plan" in full_lower
        or "10b5-1(c)" in full_lower
    )

    txns = []
    # Non-derivative transactions
    for txn in root.iter("nonDerivativeTransaction"):
        tx_date_el = txn.find(".//transactionDate/value")
        code_el = txn.find(".//transactionCoding/transactionCode")
        shares_el = txn.find(".//transactionAmounts/transactionShares/value")
        price_el = txn.find(".//transactionAmounts/transactionPricePerShare/value")
        a_or_d_el = txn.find(".//transactionAmounts/transactionAcquiredDisposedCode/value")
        if tx_date_el is None or code_el is None or shares_el is None:
            continue
        tx_date = (tx_date_el.text or "").strip()
        code = (code_el.text or "").strip().upper()
        try:
            shares = float(shares_el.text or 0)
        except ValueError:
            shares = 0
        try:
            price = float(price_el.text) if price_el is not None and price_el.text else None
        except ValueError:
            price = None
        a_or_d = (a_or_d_el.text or "").strip().upper() if a_or_d_el is not None else ""
        value = (shares * price) if (price is not None and a_or_d == "D") else None
        txns.append({
            "tx_date":         tx_date,
            "code":            code,
            "shares":          shares,
            "price_per_share": price,
            "value_usd":       value,
            "a_or_d":          a_or_d,
            "is_10b5_1":       likely_10b5_1,
            "owner_name":      owner_name,
        })
    return txns


def _load_entity_index(entity_index_path: Optional[Path] = None) -> dict:
    """Load by_entity.json — contractor → programs map. Empty dict on failure."""
    p = entity_index_path or (Path(__file__).parent.parent / "data" / "_jbook_data" / "by_entity.json")
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text())
        return data.get("entities", {})
    except (json.JSONDecodeError, OSError):
        return {}


def _resolve_contractor_programs(contractor_name: str, entities: dict) -> list[dict]:
    """Return programs the contractor is tagged on. Case-insensitive substring match."""
    if not contractor_name or not entities:
        return []
    needle = contractor_name.lower().strip()
    matches = []
    for key, value in entities.items():
        # match either dictionary key or any display_name
        if needle in key.lower():
            matches.extend(value.get("programs", []))
            continue
        for dn in value.get("display_names", []):
            if needle in dn.lower() or dn.lower() in needle:
                matches.extend(value.get("programs", []))
                break
    return matches


def _event_mentions_issuer(event: dict, contractor_name: Optional[str],
                            programs: list[dict]) -> Optional[str]:
    """Check whether the event summary mentions the issuer or any of their
    programs. Returns the matched token or None.

    Looks at:
      - contractor_name (case-insensitive substring)
      - each program's program_name (case-insensitive substring, min 5 chars)
      - each program's pe_number (exact substring)
    """
    summary = (event.get("summary") or "").lower()
    if not summary:
        return None
    if contractor_name and contractor_name.lower() in summary:
        return f"contractor:{contractor_name}"
    for prog in programs or []:
        pname = (prog.get("program_name") or "").lower()
        if len(pname) >= 5 and pname in summary:
            return f"program:{prog.get('program_name')}"
        pe = prog.get("pe_number")
        if pe and pe.lower() in summary:
            return f"pe:{pe}"
    return None


def query_insider_sales_near_budget_events(
    cik: str,
    window_days: int = 14,
    lookback_days: int = 365,
    calendar_path: Optional[str] = None,
    cutoff_date: Optional[str] = None,
    contractor_name: Optional[str] = None,
    entity_index_path: Optional[str] = None,
) -> dict[str, Any]:
    """Overlay insider sales against federal budget events.

    Args:
      cik: 10-digit padded CIK of the focal company
      window_days: ± days around each budget event to count proximate sales
      lookback_days: how far back to scan Form 4 filings (default 365)
      calendar_path: override default events.json
      cutoff_date: ISO YYYY-MM-DD upper bound (for historical backtests)
      contractor_name: (optional) used by validators 1+2 to gate
                       CLUSTERED_DISCRETIONARY. If omitted, validators
                       don't run and the legacy threshold (3+ unique
                       discretionary owners) determines the signal.
      entity_index_path: (optional) override path to by_entity.json
                         used for program-exposure lookup.

    Returns:
      {
        "n_form4_filings":          int,
        "n_total_sales":            int,
        "n_total_sale_value_usd":   float (where computable),
        "n_proximate_sales":        sales within ±window_days of any event,
        "proximate_value_usd":      float,
        "n_discretionary_proximate": discretionary (code S, non-10b5-1) within window,
        "n_unique_owners_proximate":int,
        "matched_events":           [list of (event_date, event_type, n_sales_in_window)],
        "top_proximate_sales":      top-10 proximate sales by value,
        "signal":                   NO_PROXIMATE_SALES | ROUTINE_10B5_1 |
                                    PROXIMATE_DISCRETIONARY | CLUSTERED_DISCRETIONARY,
        "cutoff_date":              echo,
      }
    """
    events = _load_calendar(Path(calendar_path) if calendar_path else None)
    if not events:
        return {"error": "no budget-calendar events available",
                "signal": "NO_PROXIMATE_SALES"}

    if cutoff_date:
        cutoff = date.fromisoformat(str(cutoff_date)[:10])
    else:
        cutoff = date.today()

    start_d = cutoff - timedelta(days=lookback_days)
    start_s = start_d.isoformat()
    cutoff_s = cutoff.isoformat()

    filings = _fetch_form4_filings(cik, start_s, cutoff_s)
    if not filings:
        return {
            "n_form4_filings":           0,
            "n_total_sales":             0,
            "n_proximate_sales":         0,
            "n_discretionary_proximate": 0,
            "signal":                    "NO_PROXIMATE_SALES",
            "matched_events":            [],
            "_note":                     f"No Form 4 filings for CIK {cik} between {start_s} and {cutoff_s}.",
        }

    cik_int = int(str(cik).lstrip("0") or "0")
    all_txns: list[dict] = []
    # Hard cap to keep runtime bounded but high enough that a year's worth
    # of Form 4 filings for a typical issuer fits — 75 was Chapman's IONQ
    # case (~75 Form 4s in 540 days). EDGAR rate-limits to ~10 req/sec.
    for f in filings[:200]:
        all_txns.extend(_parse_form4_xml(cik_int, f["accession"], f["primary_doc"]))

    # Filter to sales within window
    event_dates = [(date.fromisoformat(e["date"]), e) for e in events
                    if start_s <= e["date"] <= cutoff_s]
    if not event_dates:
        return {
            "n_form4_filings":           len(filings),
            "n_total_sales":             sum(1 for t in all_txns if t["code"] in _SALE_CODES),
            "n_proximate_sales":         0,
            "n_discretionary_proximate": 0,
            "signal":                    "NO_PROXIMATE_SALES",
            "matched_events":            [],
            "_note":                     f"No budget-calendar events in window [{start_s}, {cutoff_s}].",
        }

    proximate: list[dict] = []
    matched_events: dict[str, dict] = {}
    for txn in all_txns:
        if txn["code"] not in _SALE_CODES:
            continue
        try:
            tx_d = date.fromisoformat(txn["tx_date"])
        except ValueError:
            continue
        for ev_d, ev in event_dates:
            delta = abs((tx_d - ev_d).days)
            if delta <= window_days:
                annotated = {**txn, "event_date": ev["date"],
                             "event_type": ev["event_type"], "days_from_event": (tx_d - ev_d).days}
                proximate.append(annotated)
                key = ev["date"]
                m = matched_events.setdefault(key, {
                    "event_date": ev["date"], "event_type": ev["event_type"],
                    "summary":    ev.get("summary", "")[:120],
                    "n_sales":    0, "n_discretionary": 0,
                    "value_usd":  0.0, "unique_owners": set(),
                })
                m["n_sales"] += 1
                if txn["code"] == "S" and not txn["is_10b5_1"]:
                    m["n_discretionary"] += 1
                if txn["value_usd"]:
                    m["value_usd"] += float(txn["value_usd"])
                if txn["owner_name"]:
                    m["unique_owners"].add(txn["owner_name"])
                break  # one event per txn

    # Serialize matched_events (set → list)
    matched_list = []
    for v in sorted(matched_events.values(), key=lambda x: x["event_date"]):
        matched_list.append({**v, "unique_owners": sorted(v["unique_owners"]),
                             "n_unique_owners": len(v["unique_owners"])})

    total_sales = sum(1 for t in all_txns if t["code"] in _SALE_CODES)
    total_sale_value = sum(t["value_usd"] or 0 for t in all_txns if t["code"] in _SALE_CODES)
    n_prox = len(proximate)
    n_disc_prox = sum(1 for t in proximate if t["code"] == "S" and not t["is_10b5_1"])
    prox_value = sum(t["value_usd"] or 0 for t in proximate)
    unique_owners = {t["owner_name"] for t in proximate if t["owner_name"]}

    # Baseline signal (legacy logic, before validators)
    if n_disc_prox == 0:
        baseline = "ROUTINE_10B5_1" if n_prox > 0 else "NO_PROXIMATE_SALES"
    elif len(unique_owners) >= 3:
        baseline = "CLUSTERED_DISCRETIONARY"
    else:
        baseline = "PROXIMATE_DISCRETIONARY"

    # Validators 1+2 — only if contractor_name provided (backwards-compatible)
    validator_meta: dict[str, Any] = {
        "contractor_name": contractor_name,
        "validators_run": bool(contractor_name),
    }
    signal = baseline
    if contractor_name:
        entities = _load_entity_index(Path(entity_index_path) if entity_index_path else None)
        issuer_programs = _resolve_contractor_programs(contractor_name, entities)
        v1_pass = len(issuer_programs) > 0  # validator 1: issuer has named-program exposure

        # validator 2: check each matched event's summary for issuer link
        event_links: list[dict] = []
        for ev in matched_list:
            matched_token = _event_mentions_issuer(ev, contractor_name, issuer_programs)
            if matched_token:
                event_links.append({
                    "event_date":    ev.get("event_date"),
                    "event_type":    ev.get("event_type"),
                    "matched_token": matched_token,
                })
        v2_pass = len(event_links) > 0

        validator_meta.update({
            "validator_1_program_exposure": v1_pass,
            "validator_2_event_content_relevance": v2_pass,
            "issuer_programs_found":         len(issuer_programs),
            "event_program_links":           event_links,
            "linked_event_count":            len(event_links),
        })

        # Downgrade discretionary signals if validators fail
        if baseline in ("CLUSTERED_DISCRETIONARY", "PROXIMATE_DISCRETIONARY"):
            if not (v1_pass and v2_pass):
                signal = "CLUSTERED_DISCRETIONARY_UNCONFIRMED" \
                    if baseline == "CLUSTERED_DISCRETIONARY" \
                    else "PROXIMATE_DISCRETIONARY_UNCONFIRMED"
                validator_meta["downgrade_reason"] = (
                    "no program exposure" if not v1_pass
                    else "no event-content link to issuer's programs"
                )

    top_prox = sorted(proximate, key=lambda t: -(t["value_usd"] or 0))[:10]
    return {
        "n_form4_filings":            len(filings),
        "n_total_sales":              total_sales,
        "n_total_sale_value_usd":     total_sale_value,
        "n_proximate_sales":          n_prox,
        "proximate_value_usd":        prox_value,
        "n_discretionary_proximate":  n_disc_prox,
        "n_unique_owners_proximate":  len(unique_owners),
        "matched_events":             matched_list,
        "top_proximate_sales":        top_prox,
        "signal":                     signal,
        "baseline_signal":            baseline,
        "validator_meta":             validator_meta,
        "window_days":                window_days,
        "lookback_start":             start_s,
        "cutoff_date":                cutoff_s,
    }


if __name__ == "__main__":
    import sys
    cik = sys.argv[1] if len(sys.argv) > 1 else "0001824920"  # IONQ
    cutoff = sys.argv[2] if len(sys.argv) > 2 else "2025-12-31"
    r = query_insider_sales_near_budget_events(cik, cutoff_date=cutoff)
    print(json.dumps(r, indent=2, default=str))
