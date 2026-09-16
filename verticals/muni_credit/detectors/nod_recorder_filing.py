"""Land-secured (CFD) Notice-of-Default recorder-filing detector.

FIRES when the top property owner / master developer of a housing-development
CFD has had one or more Notices of Default recorded with a California county
recorder against its construction loan(s) in the last 24 months.

Why predictive: under California Civil Code 2924, a private-lender NoD is the
first formal step in a non-judicial foreclosure on a deed of trust. For a
housing-development CFD where the bulk of special-tax revenue depends on a
single master developer (or a few large developer parcels), a NoD against the
developer's construction loan is a leading indicator that the developer is
likely to stop paying special taxes within ~90 days (CC 2924 + CC 2924f timeline:
NoD -> 90-day cure window -> Notice of Trustee's Sale -> sale ~21 days later).

This is DIFFERENT from CFD-issuer-initiated judicial foreclosure on delinquent
special taxes (Govt Code 53356.1): the latter follows the special-tax
delinquency rather than predicting it. NoD on the developer's construction
financing is upstream of the special-tax cycle and typically precedes
CFD-special-tax delinquency by 6-18 months.

Public data: California county recorder offices. Free name-indexed search at
Stanislaus, Placer, Riverside, San Bernardino, Sacramento, San Joaquin and
others; partial paywall at Imperial. PropertyShark/PropertyRadar aggregate
across counties but borrower names paywalled in the free tier.

CAVEAT — entity resolution: developers structure each project as a separate
LLC. Resolving the parent developer to the project LLC is required; the
detector accepts an evidence list of NoD events keyed to the parent developer.

CAVEAT — base rate: in the 117-CFD universe, only a small minority of housing
CFDs have a clearly identifiable parent developer for which NoD history can
be pulled. Expected fire rate ~5-10% on housing CFDs (severity HIGH/MEDIUM
combined), much lower than CDIAC-derived signals which cover the entire
universe.

Data shape:
  {
    "developer_name": "East West Partners (Northstar)",
    "nod_events": [
      {
        "nod_date": "2010-03-31",
        "county": "Placer",
        "recording_id": "UNVERIFIABLE_NEWS_REFERENCED",
        "loan_principal_usd": 157000000,
        "borrower_entity": "East West Resort Development XX, L.P.",
        "beneficiary": "Bank of America N.A. (lead lender)",
        "current_status": "TRUSTEE_SALE",
        "trustee_sale_date": "2010-06-27",
        "source_url": "https://www.sierrasun.com/news/bank-of-america-files-notice-of-default-on-ritz-carlton-highlands-lake-tahoe/"
      }
    ],
    "as_of_date": "2026-05-28",
    "lookback_window_days": 730,
    "confidence": "HIGH"
  }
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["land_secured_district"],
    "asset_classes": ["ca_mello_roos_cfd", "ca_cfd_muni", "ca_1915_act_assessment_bonds"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "Land-secured (CFD) Notice-of-Default recorder-filing detector.",
}

from datetime import datetime, timedelta

LOOKBACK_DAYS_DEFAULT = 730  # 24 months

# Status -> severity mapping. Recorded NoD is the first step under CC 2924;
# trustee-sale notice (NOTS) means the lender has crossed the 90-day cure
# window without resolution — strongest signal. Cured / withdrawn = signal OFF.
STATUS_HIGH = {"TRUSTEE_SALE", "NOTS_RECORDED", "FORECLOSURE_SALE_COMPLETED",
                "REO", "DEED_IN_LIEU"}
STATUS_MEDIUM = {"NOD_PENDING", "NOD_RECORDED", "FORBEARANCE_NEGOTIATING"}
STATUS_OFF = {"CURED", "WITHDRAWN", "RESCINDED", "REINSTATED", "PAID_OFF"}


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def evaluate(obligor_name: str, data: dict) -> dict:
    if not isinstance(data, dict):
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    developer_name = data.get("developer_name")
    events = data.get("nod_events") or []
    as_of_date = _parse_date(data.get("as_of_date")) or datetime.utcnow()
    lookback_days = data.get("lookback_window_days", LOOKBACK_DAYS_DEFAULT)

    # UNVERIFIABLE sentinel passes through as missing
    if isinstance(events, str):
        events = []
    if not isinstance(events, list):
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    if not developer_name and not events:
        return {"fires": False, "reason": "INSUFFICIENT_DATA", "evidence": {}}

    cutoff = as_of_date - timedelta(days=lookback_days)

    severity = None
    in_window_events = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        ev_date = _parse_date(ev.get("nod_date"))
        if ev_date is None:
            continue
        if ev_date < cutoff:
            continue
        status = (ev.get("current_status") or "").upper().strip()
        if status in STATUS_OFF:
            continue
        in_window_events.append(ev)
        if status in STATUS_HIGH:
            severity = "HIGH"
        elif status in STATUS_MEDIUM and severity != "HIGH":
            severity = "MEDIUM"

    if not in_window_events:
        # Either no events at all, or only historical / cured events
        if events:
            return {
                "fires": False,
                "reason": "NO_NOD_IN_LOOKBACK_OR_CURED",
                "evidence": {
                    "developer_name": developer_name,
                    "historical_nod_count": len(events),
                    "lookback_window_days": lookback_days,
                },
            }
        return {
            "fires": False,
            "reason": "NO_NOD_FOUND",
            "evidence": {
                "developer_name": developer_name,
            },
        }

    return {
        "fires": True,
        "reason": "DEVELOPER_NOD_RECORDED",
        "severity": severity or "MEDIUM",
        "evidence": {
            "developer_name": developer_name,
            "nod_events_in_window": in_window_events,
            "lookback_window_days": lookback_days,
            "as_of_date": as_of_date.strftime("%Y-%m-%d"),
        },
    }
