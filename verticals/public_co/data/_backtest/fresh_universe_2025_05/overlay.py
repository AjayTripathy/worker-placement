"""Overlay the new UEI-anchored usaspending + megacap_namecheck
connectors on top of the existing Phase-1/2/3 results for the
fresh-universe cohort. Compare emit buckets before/after.

This is a fast validation that skips the LLM re-planning step:
- Phase 1 (planner) already produced .plan.json with claims.
- Phase 2 (plan_executor) already produced .queries.json with results.
- Phase 3 (deterministic_scorer) already produced .scores.json.

We add NEW signals from the new connectors per ticker, score them
through the existing dispatcher, and recompute composite + emit
decision. If any ticker's bucket flips, that's a target for full
LLM re-plan.
"""
from __future__ import annotations

import json
from pathlib import Path

from verticals.public_co.m_sources.usaspending import query_federal_presence
from verticals.public_co.m_sources.megacap_namecheck import query_megacap_mentions
from verticals.public_co.deterministic_scorer import _score_single_result
from verticals.public_co.forward_bet_emission import (
    EMIT_DA_TIERS, is_truth_signal,
)
from verticals.public_co.discovery_advantage import compute_discovery_advantage


HERE = Path(__file__).parent
BACKTEST_DIR = HERE.parent / "2025_05_15"
CUTOFF = "2025-05-15"

# Per-ticker overlay config: name_variants for usaspending +
# megacap subset most likely to fire if the small-cap inflates.
OVERLAY_CONFIG = {
    "LRHC": {
        "name_variants": ["La Rosa Holdings", "La Rosa Realty"],
        "megacaps":      ["Amazon", "Microsoft", "Apple", "Walmart"],
        "federal_claim_in_filing": False,
        "commercial_megacap_claim_in_filing": False,
    },
    "KULR": {
        "name_variants": ["KULR Technology", "KULR Technology Group"],
        "megacaps":      ["Amazon", "Tesla", "Nvidia"],
        "federal_claim_in_filing": True,    # claims NASA/JPL/DOD
        "commercial_megacap_claim_in_filing": False,
    },
    "HDSN": {
        "name_variants": ["Hudson Technologies"],
        "megacaps":      ["Amazon", "Microsoft", "Walmart"],
        "federal_claim_in_filing": False,   # bear thesis is on counterparties (Lennox etc.)
        "commercial_megacap_claim_in_filing": False,
    },
    "PESI": {
        "name_variants": ["Perma-Fix Environmental", "Perma-Fix"],
        "megacaps":      ["Boeing", "LockheedMartin", "GeneralMotors"],
        "federal_claim_in_filing": True,    # explicit DOE nuclear-waste
        "commercial_megacap_claim_in_filing": False,
    },
    "CWCO": {
        "name_variants": ["Consolidated Water"],
        "megacaps":      ["Amazon", "Microsoft", "Walmart"],
        "federal_claim_in_filing": False,
        "commercial_megacap_claim_in_filing": False,
    },
    "CDNA": {
        "name_variants": ["CareDx"],
        "megacaps":      ["JNJ", "Pfizer"],
        "federal_claim_in_filing": True,    # VA work is part of their model
        "commercial_megacap_claim_in_filing": False,
    },
    "ALMU": {
        "name_variants": ["Aeluma"],
        "megacaps":      ["Nvidia", "Apple"],
        "federal_claim_in_filing": True,    # claims DARPA-funded R&D
        "commercial_megacap_claim_in_filing": False,
    },
    "KLIC": {
        "name_variants": ["Kulicke and Soffa", "Kulicke & Soffa"],
        "megacaps":      ["Apple", "Nvidia"],
        "federal_claim_in_filing": False,
        "commercial_megacap_claim_in_filing": False,
    },
}

SEV_W = {
    "SEVERE_UNDERDELIVERY":   2.0,
    "RED_FLAG_NEGATIVE":      3.0,
    "MODERATE_UNDERDELIVERY": 1.0,
    "PASS":                   0.0,
    "UNVERIFIABLE":           0.0,
}


def overlay_one(tk: str, cfg: dict) -> dict:
    """Run new connectors on tk; return delta vs existing scores."""
    # Load existing scores
    scores_path = BACKTEST_DIR / f"{tk}.scores.json"
    data = json.loads(scores_path.read_text())
    existing = data.get("scores", [])
    existing_counts = {}
    counted = [s for s in existing if s.get("severity") != "UNVERIFIABLE"]
    for s in existing:
        sev = s.get("severity", "UNVERIFIABLE")
        existing_counts[sev] = existing_counts.get(sev, 0) + 1
    existing_comp = (sum(SEV_W.get(s.get("severity"), 0) for s in counted)
                     / max(1, len(counted)))

    # New connector A: federal presence (only if claim makes federal flavor)
    fed_result = None
    fed_severity = None
    if cfg["federal_claim_in_filing"]:
        fed_result = query_federal_presence(cfg["name_variants"])
        claim = {"category": "government_contract",
                 "claim_text": f"federal/agency relationship claimed in {tk} 10-K",
                 "m_source_status": "MAPPED"}
        sev, _, mv, interp, esc = _score_single_result(
            claim,
            {"label": "usaspending.query_federal_presence", "result": fed_result},
            focal_cik=None,
        )
        fed_severity = {"severity": sev, "m_value": mv, "interpretation": interp,
                        "signal": fed_result.get("signal"),
                        "contracts_M": fed_result.get("contracts_amount_M"),
                        "n_ueis": fed_result.get("n_ueis_resolved")}

    # New connector B: megacap namecheck (only if commercial megacap claim)
    mc_result = None
    mc_severity = None
    if cfg["commercial_megacap_claim_in_filing"]:
        mc_result = query_megacap_mentions(
            small_cap_name=cfg["name_variants"][0],
            cutoff_date=CUTOFF,
            megacap_subset=cfg["megacaps"],
        )
        claim = {"category": "partnership",
                 "claim_text": f"commercial megacap partnership claimed in {tk} 10-K",
                 "m_source_status": "MAPPED"}
        sev, _, mv, interp, esc = _score_single_result(
            claim,
            {"label": "megacap_namecheck.query_megacap_mentions", "result": mc_result},
            focal_cik=None,
        )
        mc_severity = {"severity": sev, "m_value": mv, "interpretation": interp,
                       "signal": mc_result.get("signal")}

    # Build augmented scores list
    augmented = list(existing)
    for entry in (fed_severity, mc_severity):
        if entry and entry["severity"] != "UNVERIFIABLE":
            augmented.append({"severity": entry["severity"],
                              "_overlay": True,
                              "_m_value": entry["m_value"]})
        elif entry:  # UNVERIFIABLE — still add to counts as a defended-skip
            augmented.append({"severity": "UNVERIFIABLE", "_overlay": True})

    aug_counts = {}
    aug_counted = [s for s in augmented if s.get("severity") != "UNVERIFIABLE"]
    for s in augmented:
        sev = s.get("severity", "UNVERIFIABLE")
        aug_counts[sev] = aug_counts.get(sev, 0) + 1
    aug_comp = (sum(SEV_W.get(s.get("severity"), 0) for s in aug_counted)
                / max(1, len(aug_counted)))

    # Truth signal + emit on existing vs augmented
    before_ts = is_truth_signal({"composite_score": existing_comp,
                                 "severity_counts": existing_counts})
    after_ts  = is_truth_signal({"composite_score": aug_comp,
                                 "severity_counts": aug_counts})
    da = compute_discovery_advantage(tk)
    da_tier = da.get("tier")
    before_emit = before_ts and da_tier in EMIT_DA_TIERS
    after_emit  = after_ts  and da_tier in EMIT_DA_TIERS

    return {
        "ticker":         tk,
        "da_tier":        da_tier,
        "before": {
            "composite":     round(existing_comp, 3),
            "counts":        existing_counts,
            "truth_signal":  before_ts,
            "emit":          before_emit,
        },
        "after": {
            "composite":     round(aug_comp, 3),
            "counts":        aug_counts,
            "truth_signal":  after_ts,
            "emit":          after_emit,
        },
        "fed_overlay": fed_severity,
        "mc_overlay":  mc_severity,
        "bucket_flipped":  (before_emit != after_emit) or (before_ts != after_ts),
    }


def main():
    rows = []
    print(f"{'TK':5s} {'before_comp':>11s} {'before_ts':>9s} {'before_emit':>11s}  "
          f"{'after_comp':>10s} {'after_ts':>8s} {'after_emit':>10s}  flip?  fed       mc")
    print("=" * 130)
    for tk, cfg in OVERLAY_CONFIG.items():
        r = overlay_one(tk, cfg)
        b, a = r["before"], r["after"]
        fed = (r["fed_overlay"] or {}).get("severity") if r["fed_overlay"] else "—"
        mc  = (r["mc_overlay"]  or {}).get("severity") if r["mc_overlay"]  else "—"
        flip = "YES" if r["bucket_flipped"] else ""
        print(f"  {tk:5s} {b['composite']:>9.3f}   "
              f"{'Y' if b['truth_signal'] else 'n':>7s}  "
              f"{'EMIT' if b['emit'] else '   -':>9s}    "
              f"{a['composite']:>8.3f}  "
              f"{'Y' if a['truth_signal'] else 'n':>6s}  "
              f"{'EMIT' if a['emit'] else '   -':>8s}  {flip:>4s}  "
              f"{fed!s:18s}  {mc}")
        rows.append(r)

    (HERE / "overlay_results.json").write_text(json.dumps(rows, indent=2, default=str))
    print(f"\nWrote {HERE / 'overlay_results.json'}")

    # Summary
    flipped = [r for r in rows if r["bucket_flipped"]]
    print(f"\n{'='*50}\nFlipped: {len(flipped)} of {len(rows)} names")
    for r in flipped:
        print(f"  {r['ticker']}: emit {r['before']['emit']} → {r['after']['emit']}")


if __name__ == "__main__":
    main()
