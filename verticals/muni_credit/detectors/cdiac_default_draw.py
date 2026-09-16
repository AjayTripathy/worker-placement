"""CDIAC Default & Draw-on-Reserve history detector.

FIRES when the obligor appears in California's CDIAC Default-and-Draw-on-Reserve
index (a recorded debt-service default or a draw on the bond reserve fund).

Why predictive / high-precision: a recorded default or reserve draw is the
hardest possible credit fact — the bond's self-protection was breached and the
issuer reported it to CDIAC (mandatory under Gov Code 53359 / 6599.1). Across the
ENTIRE CA index there are only ~710 events 1991-2026 (273 defaults, 414 draws),
so a name match is rare and very high precision. ~89% of events are land-secured
(Mello-Roos/CFD) + Marks-Roos public-financing-authority pools, so this detector
APPLIES_TO land_secured / successor_agency (reserve-backed local debt). GO,
school-GO, hospital, water, county-appropriation credits almost never appear
(their stress shows up as rating downgrades, which CDIAC does not track).

This is the live data-sourcing layer the existing `reserve_fund_drawn` detector
already names as a source ("CDIAC Default & Draw on Reserve database") but never
had a puller for — see `cdiac_draws.py` (DebtWatch API).

Data shape (built by cdiac_draws.build_detector_data):
  {
    "events": [{"date":"2009-09-01","type":"Default","amount_usd":3.4e6,
                "issuer":"...","issue_name":"...","county":"...","cdiac":"2005-1234"}],
    "n_defaults": 1, "n_draws": 2, "n_replenishments": 0,
    "match_confidence": "HIGH",            # HIGH = >=2 distinctive tokens / number-confirmed;
                                           # MEDIUM = place-token-only (review, don't hard-exclude)
    "matched_issuers": ["..."],
    "source": "CDIAC Default & Draw on Reserve (DebtWatch API)",
    "as_of": 2026
  }
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": ["land_secured_district", "successor_agency_obligor"],
    "asset_classes": ["ca_mello_roos_cfd", "ca_cfd_muni", "ca_1915_act_assessment_bonds", "ca_rda_successor_muni", "ca_tax_allocation_bonds_post_dissolution"],
    "applies_universally": False,
    "kind": "detector",
    "summary": "CDIAC Default & Draw-on-Reserve history detector.",
}

REF_YEAR = 2026          # as-of year of the index pull
RECENT_WINDOW = 10       # an event within this many years is "recent" (vs stale credit-history)


def evaluate(obligor_name: str, data: dict) -> dict:
    events = data.get("events") or []
    conf = (data.get("match_confidence") or "HIGH").upper()

    if not events:
        return {"fires": False, "reason": "NO_CDIAC_DEFAULT_DRAW_RECORD", "evidence": {}}

    n_def = data.get("n_defaults")
    n_draw = data.get("n_draws")
    if n_def is None:
        n_def = sum(1 for e in events if (e.get("type") or "").lower().startswith("default"))
    if n_draw is None:
        n_draw = sum(1 for e in events if "draw" in (e.get("type") or "").lower())

    years = [int((e.get("date") or "0")[:4]) for e in events if (e.get("date") or "")[:4].isdigit()]
    most_recent = max(years) if years else 0
    recent = most_recent >= REF_YEAR - RECENT_WINDOW
    base_ev = {
        "matched_issuers": data.get("matched_issuers"),
        "most_recent_event_year": most_recent or None,
        "n_defaults": n_def, "n_draws": n_draw,
        "source": data.get("source", "CDIAC Default & Draw on Reserve"),
    }

    # Place-token-only name match: surface for analyst review, do NOT hard-exclude
    # (matcher-precision discipline — a city-token collision is not a confirmed match).
    if conf == "MEDIUM":
        return {"fires": True, "reason": "CDIAC_RECORD_POSSIBLE_NAME_MATCH", "severity": "REVIEW",
                "evidence": {**base_ev, "note": "place-token-only name match; verify CDIAC number before excluding"}}

    if n_def > 0:
        return {"fires": True, "reason": "CDIAC_DEFAULT_ON_RECORD",
                "severity": "RED" if recent else "MEDIUM",
                "evidence": {**base_ev, "stale": not recent}}
    if n_draw > 0:
        return {"fires": True, "reason": "CDIAC_RESERVE_DRAWN_ON_RECORD",
                "severity": "HIGH" if recent else "MEDIUM",
                "evidence": {**base_ev, "stale": not recent}}

    # only replenishment events matched (a prior draw was repaid) — informational, not a fire
    return {"fires": False, "reason": "CDIAC_RESERVE_REPLENISHED_ONLY", "evidence": base_ev}
