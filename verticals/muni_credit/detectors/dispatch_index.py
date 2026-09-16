"""Dispatch index + coverage validator — the muni "brain".

The union runner dispatches a detector only when its input data key happens to
be populated (presence-based dispatch). That cannot catch a detector that
*should* run but silently didn't, because the missing data is exactly what makes
it invisible. This module adds the missing half: each detector declares the
obligor SECTORS it APPLIES_TO, and a pre-flight validator compares, per obligor,
the set of detectors that SHOULD apply against the set that actually had data.
The difference is a coverage gap — surfaced loudly instead of swallowed.

This mirrors the dispatch-index pattern already used in the public_co / buyside
verticals (query the graph at dispatch time + an output-side coverage validator),
which the muni vertical never received.

Sector model
------------
A CCRC is a hybrid: it operates independent-living + assisted-living + a
skilled-nursing wing that carries its own CMS provider number. So an obligor's
EFFECTIVE sectors expand via SECTOR_IMPLIES — a `ccrc` obligor is also subject to
every `snf` detector (CMS star / SFF / civil monetary penalty), which is the
precise applicability the presence-based runner kept missing.
"""
from __future__ import annotations

# Knowledge-graph dispatch contract (see knowledge_graph/dispatch.py). Added 2026-07-29
# to close the atlas gap; muni sector mapping mirrors detectors/dispatch_index.py.
APPLIES_TO = {
    "sic_codes": [],
    "sic_prefixes": [],
    "issuer_features": [],
    "asset_classes": [],
    "applies_universally": False,
    "kind": "helper",
    "summary": "Dispatch index + coverage validator — the muni \"brain\".",
}

# Canonical obligor sectors.
SECTORS = frozenset({
    "ccrc", "snf", "hospital",
    "k12_usd", "charter", "successor_agency",
    "land_secured",
    "water_revenue", "electric_revenue",   # essential-service enterprise-revenue (utility sleeve)
})

# An obligor in the key sector is ALSO subject to the implied sectors' detectors.
# A CCRC contains a skilled-nursing facility -> snf detectors apply.
SECTOR_IMPLIES = {
    "ccrc": frozenset({"ccrc", "snf"}),
}

# Detectors that apply to every obligor regardless of sector (governance /
# disclosure / market-signal layers that are not sector-specific).
_UNIVERSAL = frozenset({"*"})

# detector_name -> frozenset(sectors it applies to). "*" == all sectors.
DETECTOR_APPLIES_TO: dict[str, frozenset] = {
    # --- universal governance / disclosure / market-signal ---
    "auditor_change": _UNIVERSAL,
    "late_filing": _UNIVERSAL,
    "going_concern": _UNIVERSAL,
    "exec_turnover": _UNIVERSAL,
    "pension_funded_ratio": _UNIVERSAL,
    "pension_funded_ratio_trajectory": _UNIVERSAL,
    "covenant_breach": _UNIVERSAL,
    "news_sentiment_monitor": _UNIVERSAL,
    # --- healthcare / senior-living ---
    "payor_concentration": frozenset({"hospital", "snf", "ccrc"}),
    "doj_fca": frozenset({"hospital", "snf", "ccrc"}),
    "cms_readmissions": frozenset({"hospital", "snf"}),
    "hhs_oig_cia": frozenset({"hospital", "snf", "ccrc"}),
    "cal_mortgage_cascade_monitor": frozenset({"hospital", "snf", "ccrc"}),
    # --- CCRC-specific ---
    "ccrc_occupancy": frozenset({"ccrc"}),
    "ccrc_days_cash": frozenset({"ccrc"}),
    # --- skilled-nursing-specific (apply to CCRCs via SECTOR_IMPLIES) ---
    "nh_cms_star_rating": frozenset({"snf"}),
    "nh_special_focus_facility": frozenset({"snf"}),
    "nh_civil_monetary_penalty": frozenset({"snf"}),
    # --- land-secured / CFD / dirt bonds ---
    "value_to_lien_collapse": frozenset({"land_secured"}),
    "delinquency_spike": frozenset({"land_secured"}),
    "reserve_fund_drawn": frozenset({"land_secured"}),
    "reserve_fund_burndown": frozenset({"land_secured"}),
    "foreclosure_active": frozenset({"land_secured"}),
    "issuer_administration_concern": frozenset({"land_secured"}),
    "buildout_stalled": frozenset({"land_secured"}),
    "top_taxpayer_concentration": frozenset({"land_secured"}),
    "coverage_ratio_thin": frozenset({"land_secured"}),
    "developer_bankruptcy": frozenset({"land_secured"}),
    "nod_recorder_filing": frozenset({"land_secured"}),
    "developer_corp_credit": frozenset({"land_secured"}),
    # CDIAC Default & Draw-on-Reserve recorded-event history (the live puller the
    # YFSR-based reserve_fund_drawn detector always named as a source). Cross-sector
    # but empirically ~89% land-secured + Marks-Roos public-financing-authority pools;
    # successor-agency TABs also carry reserves and occasionally appear. See cdiac_draws.py.
    "cdiac_default_draw": frozenset({"land_secured", "successor_agency"}),
    # --- K-12 USD GO / charter / successor agency ---
    "coe_fiscal_certification": frozenset({"k12_usd"}),
    "state_controller_intercept": frozenset({"k12_usd", "charter", "successor_agency"}),
    # --- essential-service enterprise revenue (water / electric utility-revenue bonds) ---
    # For a REVENUE bond the load-bearing risk is the system's coverage + its PHYSICAL supply. The supply
    # must be verified first-principles against published authority (DWR SWP / MWD / USBR Colorado-River
    # contractors + DWR Bulletin 118 critical basins), not the issuer's own OS keywords. The pre-flight
    # validator now FLAGS any water-revenue obligor that wasn't run through the supply-source authority.
    # keyed by MODULE name so name-joins against the KG inventory hold (was "water_supply_source" — the
    # 2026-07-29 APPLIES_TO sweep caught the mismatch; no external references existed)
    "water_supply_authority": frozenset({"water_revenue"}),    # detectors/water_supply_authority.verify_supply
    # hcai_seismic was MISSING from this map entirely (2026-07-29 sweep finding) — CA-hospital scope
    "hcai_seismic": frozenset({"hospital"}),
    "dscr_coverage": frozenset({"water_revenue", "electric_revenue"}),
    "rate_covenant": frozenset({"water_revenue", "electric_revenue"}),
    "customer_concentration": frozenset({"water_revenue", "electric_revenue"}),
    "power_supply_source": frozenset({"electric_revenue"}),     # fuel mix / take-or-pay member credit
}


def effective_sectors(sector: str) -> frozenset:
    """Expand an obligor's declared sector to include implied sub-sectors."""
    return SECTOR_IMPLIES.get(sector, frozenset({sector}))


def expected_detectors(sector: str) -> set:
    """Detectors that SHOULD apply to an obligor in the given sector."""
    eff = effective_sectors(sector)
    out = set()
    for det, applies in DETECTOR_APPLIES_TO.items():
        if applies == _UNIVERSAL or (applies & eff):
            out.add(det)
    return out


def coverage_report(detector_data: dict, sector_by_obligor: dict | str) -> dict:
    """Compare expected vs actually-fed detectors per obligor.

    sector_by_obligor: either a single sector string (whole screen is one
    sector) or a dict {obligor_name -> sector}.

    Returns {
      "per_obligor": [{obligor, sector, expected, fed, missing}],
      "gap_by_detector": {detector -> n_obligors_missing_data},
      "n_obligors": int,
    }
    """
    per_obligor = []
    gap_by_detector: dict[str, int] = {}
    for obligor, data in detector_data.items():
        sector = sector_by_obligor if isinstance(sector_by_obligor, str) else sector_by_obligor.get(obligor, "")
        expected = expected_detectors(sector)
        fed = {k for k, v in (data or {}).items() if v}
        missing = sorted(expected - fed)
        for det in missing:
            gap_by_detector[det] = gap_by_detector.get(det, 0) + 1
        per_obligor.append({
            "obligor": obligor, "sector": sector,
            "expected": sorted(expected), "fed": sorted(fed), "missing": missing,
        })
    return {
        "per_obligor": per_obligor,
        "gap_by_detector": dict(sorted(gap_by_detector.items(), key=lambda kv: -kv[1])),
        "n_obligors": len(detector_data),
    }


def print_coverage_report(report: dict, title: str = "DISPATCH COVERAGE") -> None:
    n = report["n_obligors"]
    print(f"\n=== {title} (brain pre-flight) ===")
    gaps = report["gap_by_detector"]
    if not gaps:
        print("  No coverage gaps: every applicable detector had data for every obligor.")
        return
    print(f"  Applicable-but-unfed detectors (data sourcing gaps):")
    for det, cnt in gaps.items():
        print(f"    {det}: missing data on {cnt}/{n} obligors it applies to")
