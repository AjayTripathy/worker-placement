"""events — the CLOSED catalyst-event taxonomy (formalized 2026-07-05 from the stringly-typed
tags frozen 2026-07-04). Every frozen prediction carries exactly one EVENT_TYPE; the enum is
the contract between the calibration ledger (per-type Brier grading), the resolution packs,
the predictions calendar, and the prediction-market mapper (venue_coverage says which types
can ever receive a crowd market_p — the coverage map verified 2026-07-05).

Adding a type = a doctrine change: extend ONLY here, with grading + coverage notes, never by
free-typing a new string into a ledger row. The taxonomy was frozen PRE-resolution so the
per-type Brier buckets stay honest — renaming/merging types after calls resolve is forbidden.
"""
from __future__ import annotations

EVENT_TYPES: dict[str, dict] = {
    "earnings_print":      {"desc": "a company's own scheduled results/KPI release",
                            "venue_coverage": "none (mid-caps; Kalshi lists mega-caps only)",
                            "grading": "mechanical vs the pack's adjudication spec"},
    "peer_read":           {"desc": "another company's print consumed as evidence for our name",
                            "venue_coverage": "none",
                            "grading": "graded on OUR framed direction; feeds update-table deltas (a pre-warning CONSUMES its delta)"},
    "political_process":   {"desc": "votes, elections, legislative tracks, cabinet changes",
                            "venue_coverage": "strong (Polymarket/Kalshi core)",
                            "grading": "watch for event CHANGES (the CIB deferral class) — adjudicate at the boundary date on facts as they stand"},
    "regulatory_decision": {"desc": "agency rulings, sanctions, approvals, rate notices (CMS/FHFA/KNF/CFTC class)",
                            "venue_coverage": "partial (headline geopolitics yes; niche dockets no)",
                            "grading": "the resolving DOCUMENT named in the pack; deadline slips are data, not misses"},
    "deal_corporate":      {"desc": "mergers, exchange ratios, tenders, spin calendars, buybacks-as-events",
                            "venue_coverage": "partial (large deals only)",
                            "grading": "terms vs our frozen fairness line (e.g. ratio <= NAV parity)"},
    "production_ops":      {"desc": "physical output prints & operational milestones (tonnes, transits, train CODs)",
                            "venue_coverage": "partial (chokepoints/geopolitical physical states list; company ops don't)",
                            "grading": "beware the BASIS TRAP (anode+blister class) — normalize units before comparing"},
    "monthly_data":        {"desc": "recurring published series (comps, order counts, transit counts, MBA weeklies)",
                            "venue_coverage": "partial",
                            "grading": "the purest nowcast class — flat-line floors apply; grade the series not the headline"},
    "nat_cat_season":      {"desc": "hurricane/wildfire season outcomes over a window",
                            "venue_coverage": "partial w/ THRESHOLD-MISMATCH RISK (Cat-4 market cannot grade a Cat-3+ call)",
                            "grading": "season-end adjudication; interim forecast updates = refinements only"},
    "scenario":            {"desc": "self-grading calls on our OWN verdicts (fair-band checks, pass-grading, no-trade grading)",
                            "venue_coverage": "none by construction",
                            "grading": "grades our machinery, not the world; excluded from the market-beating Brier gate"},
    # --- 2026-07-27 deliberate extensions (the two types the anchor-and-adjust wiring enforces on;
    #     the wider drift set (earnings_stock_reaction naming etc.) still awaits user canonicalization) ---
    "stock_reaction":      {"desc": "price direction over a defined post-event window (the -STK legs)",
                            "venue_coverage": "options (implied-binary digital = the standing anchor, desk/implied_binary.py)",
                            "grading": "mechanical: close N sessions after the print vs the frozen anchor; NEVER regrades the ops call (HCA doctrine); freeze REQUIRES reaction_driver + anchor-and-adjust vs the implied stamp"},
    "earnings_operating":  {"desc": "the operating half of a split earnings call (beat/guide/segment bar) — pairs with a stock_reaction leg",
                            "venue_coverage": "none (mid-caps)",
                            "grading": "mechanical vs the pack's adjudication spec; the strong (connector-fed) class — partition ops_data"},
}


def validate_event_type(kind: str) -> bool:
    return kind in EVENT_TYPES


def coverage(kind: str) -> str:
    return EVENT_TYPES.get(kind, {}).get("venue_coverage", "unknown")
