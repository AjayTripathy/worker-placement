"""Union-of-detectors exclusion screen runner.

Composes all predictive detectors per the detector-composition framework:
the portfolio is the universe MINUS any obligor caught by ANY detector.

Per-detector configuration: each detector contributes equally to the union.
Future enhancement: weight detectors by historical precision/recall.

Input shape:
  detector_data: dict {
    obligor_name: {
      "auditor_change": {...},     # input data for auditor_change.evaluate
      "pension_funded_ratio": {...},
      "late_filing": {...},
      "payor_concentration": {...},
      "exec_turnover": {...},
      ...
    }
  }

Also takes:
  ma_leverage_fires: dict {obligor → bool}  # from existing ma_leverage_detector
  covenant_tripwire_fires: dict {obligor → bool}  # from existing covenant_tripwire
                                                   # (note: this is the LOW-precision signal
                                                   # we use as last-resort fallback, not primary)

Output:
  per_obligor: list of {
    obligor, fired_by: [detector names that fired], excluded: bool, evidence: {...}
  }
  summary: counts + fire rates per detector + combined exclusion rate
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter, defaultdict

from . import (auditor_change, pension_funded_ratio, pension_funded_ratio_trajectory,
               late_filing, payor_concentration,
               exec_turnover, going_concern, doj_fca, honesty_decomposed,
               cms_readmissions, hhs_oig_cia, hcai_seismic,
               ccrc_occupancy, ccrc_days_cash,
               nh_cms_star_rating, nh_special_focus_facility, nh_civil_monetary_penalty,
               # Land-secured / CFD detectors
               value_to_lien_collapse, delinquency_spike, reserve_fund_drawn,
               reserve_fund_burndown, foreclosure_active, issuer_administration_concern,
               buildout_stalled, top_taxpayer_concentration, coverage_ratio_thin,
               developer_bankruptcy,
               # CDIAC Default & Draw-on-Reserve recorded-event history (live puller:
               # cdiac_draws.py; the source reserve_fund_drawn always named)
               cdiac_default_draw,
               # Diligence-replication layer (reproduces institutional active-manager research)
               nod_recorder_filing, developer_corp_credit,
               # Covenant disclosure layer — scans audit / EMMA text for breach language
               covenant_breach,
               # CA K-12 USD GO specific — COE AB 1200 quarterly fiscal certification
               coe_fiscal_certification,
               # Real-time news-velocity layer (fastest signal; precedes EMMA / rating actions)
               news_sentiment_monitor,
               # CA state-mediated apportionment-intercept activity tracker
               # (SCO LCFF / CDE Interim / DOF RPTTF — see data/etf_sco_intercept_scoring.json).
               # Overlaps with coe_fiscal_certification on the CDE Interim channel but ADDS
               # the RPTTF DOF-review-letter channel (3 SA holdings) and the SCO LCFF channel
               # (CSFA charter conduits) under a single intercept-activity taxonomy. Per
               # detector-composition memory: union-of-narrow-detectors > one comprehensive
               # score, so we keep both detectors; double-fire on a single CDE Q event is
               # acceptable (the obligor is excluded once either way).
               state_controller_intercept,
               # HCAI Cal-Mortgage cascade monitor (second-order insurer-pool detector).
               # Fires only on wrapped names when HCAI Monthly Activity Report shows
               # recent bondholder claim payment activity that draws down HFCLIF reserves.
               # Inert on NOT_INSURED obligors (e.g., the 4 large-system CHFFA hospital
               # holdings in the ETF basket: El Camino, Stanford, Providence, Adventist).
               # See data/cal_mortgage_cascade_activity.json + data/chffa_insurance_status.json.
               cal_mortgage_cascade_monitor)

# Active detector registry. Each must fire on <15% of universe with high precision.
# REJECTED (do not include in registry):
#   - rating_action_omission: fired on 60% of universe; comprehensive-score-in-disguise
#   - operating_margin_obscured: similar
#   - same_facility_framing_heavy: not validated
DETECTORS = {
    "auditor_change": auditor_change,
    "pension_funded_ratio": pension_funded_ratio,
    # 5-year trajectory extension — declining slope is the leading indicator
    # (Stockton/Vallejo CalPERS pattern; Sacramento USD CalSTRS pattern).
    "pension_funded_ratio_trajectory": pension_funded_ratio_trajectory,
    "late_filing": late_filing,
    "payor_concentration": payor_concentration,
    "exec_turnover": exec_turnover,
    "going_concern": going_concern,
    "doj_fca": doj_fca,
    "cms_readmissions": cms_readmissions,
    "hhs_oig_cia": hhs_oig_cia,
    # CCRC-specific
    "ccrc_occupancy": ccrc_occupancy,
    "ccrc_days_cash": ccrc_days_cash,
    # Nursing home specific
    "nh_cms_star_rating": nh_cms_star_rating,
    "nh_special_focus_facility": nh_special_focus_facility,
    "nh_civil_monetary_penalty": nh_civil_monetary_penalty,
    # Land-secured / CFD specific (V1: HIGH-confidence YFSR-direct)
    "value_to_lien_collapse": value_to_lien_collapse,
    "delinquency_spike": delinquency_spike,
    # CDIAC recorded default/draw-on-reserve history (cross-CFD, 1991-2026; ~710
    # events statewide so a name match is rare + very high precision). Complements
    # reserve_fund_drawn (YFSR balance) with the official default/draw filing record.
    "cdiac_default_draw": cdiac_default_draw,
    "reserve_fund_drawn": reserve_fund_drawn,
    "reserve_fund_burndown": reserve_fund_burndown,
    "foreclosure_active": foreclosure_active,
    "issuer_administration_concern": issuer_administration_concern,
    # Land-secured V2: MEDIUM-confidence (CDA-pull-dependent)
    "buildout_stalled": buildout_stalled,
    "top_taxpayer_concentration": top_taxpayer_concentration,
    "coverage_ratio_thin": coverage_ratio_thin,
    "developer_bankruptcy": developer_bankruptcy,
    # Diligence-replication layer
    "nod_recorder_filing": nod_recorder_filing,
    "developer_corp_credit": developer_corp_credit,
    # Covenant disclosure layer (prototype catch: Alliance Charter FY25
    # waiver — see outputs/CA_CHARTER_INVESTMENT_THESIS_V2.md)
    "covenant_breach": covenant_breach,
    # CA K-12 USD GO specific (COE AB 1200 quarterly fiscal certification;
    # see data/etf_coe_fiscal_scoring.json — calibrated fire rate 1/6 = 16.7%
    # on the 6-name ETF basket, vs 3-6% universe baseline; River Delta the
    # single fire with HIGH severity / BACK_TO_BACK_QUALIFIED).
    "coe_fiscal_certification": coe_fiscal_certification,
    # Real-time news-velocity layer — Google News + Bond Buyer + local CA outlets,
    # sentiment-tagged per obligor over trailing 90d / 12mo. Fastest signal in the
    # framework; precedes EMMA material events and formal rating actions by weeks
    # to months. Initial calibration on CA muni ETF basket (2026-05-28, N=19):
    # 4/19 = 21% fire rate, sector-skewed toward CHFFA hospital (3/4 hospital
    # obligors fire — Stanford strike, Providence AG action, Adventist regulatory
    # cluster) plus 1/6 K-12 (Clovis Title IX litigation cluster). Above the
    # nominal 15% per-detector universe-fire-rate ceiling — by design for
    # initial-launch screening; should tighten on broader universe before being
    # promoted to a primary alpha screen. See data/etf_news_sentiment.json.
    "news_sentiment_monitor": news_sentiment_monitor,
    # CA state-mediated apportionment-intercept activity tracker. Unifies three
    # structurally-distinct intercept channels under one taxonomy:
    #   - SCO LCFF (Ed Code 17199.4) for CSFA charter conduits
    #   - DOF + County Auditor RPTTF (HSC 34183) for Successor Agency TABs
    #   - CDE Interim Q/N (AB 1200) for K-12 USD operating-side distress (note:
    #     K-12 USD GO debt service is NOT paid by SCO — SB 222 statutory lien
    #     flows tax direct from county tax collector to bond trustee; the CDE
    #     channel is the upstream IDR signal that compresses the 5-notch ceiling)
    # ETF basket calibration (2026-05-28, N=9: 6 K-12 USD + 3 Successor Agency):
    # 1/9 = 11.1% fire rate. Single fire = River Delta USD MEDIUM (back-to-back
    # CDE Q). All 3 SAs approved-in-full by DOF. See data/etf_sco_intercept_scoring.json.
    "state_controller_intercept": state_controller_intercept,
    # HCAI Cal-Mortgage cascade monitor. SECOND-ORDER detector — fires only on
    # Cal-Mortgage-insured names when the HCAI Monthly Activity Report shows
    # recent bondholder claim payment activity affecting insurer capacity.
    # Severity HIGH if claim trailing 6mo / MEDIUM 6-18mo / LOW >18mo. Inert
    # (no fire) on NOT_INSURED obligors. Universe-level cascade state as of
    # 2026-05-28: 1 claim in trailing 18mo (St. Rose Hospital ~$13.96M, May
    # 2025 first appearance in Anticipated Recoveries). HFCLIF still
    # well-capitalized ($127.8M cash vs $75M statutory minimum); the cascade
    # is real but not yet wrap-breaking. See data/cal_mortgage_cascade_activity.json.
    "cal_mortgage_cascade_monitor": cal_mortgage_cascade_monitor,
    # REJECTED:
    # - hcai_seismic: 2030 deadline → 3-7 year lead time exceeds backtest window;
    #   AND nearly every CA hospital has unfunded SPC-2 buildings (sector-wide
    #   exposure, not discriminating per-obligor signal). Engine retained in
    #   detectors/ for future use when (a) we have a 5+ year backtest window
    #   OR (b) we can compare obligors against CA-cohort baseline.
}


def run(detector_data: dict, ma_leverage_fires: dict | None = None,
        covenant_tripwire_fires: dict | None = None,
        include_tripwire: bool = False) -> dict:
    """Run all detectors and compose via union.

    include_tripwire defaults to FALSE — the covenant tripwire fired on 88% of
    obligors blind and is unusable as a primary screen. Use only for diagnostics.
    """
    ma_leverage_fires = ma_leverage_fires or {}
    covenant_tripwire_fires = covenant_tripwire_fires or {}

    per_obligor = []
    detector_fire_counts = defaultdict(int)
    detector_eval_counts = defaultdict(int)

    all_obligors = set(detector_data.keys()) | set(ma_leverage_fires.keys())
    if include_tripwire:
        all_obligors |= set(covenant_tripwire_fires.keys())

    for obligor in sorted(all_obligors):
        data = detector_data.get(obligor, {})
        fired_by = []
        per_detector_results = {}

        for det_name, det_module in DETECTORS.items():
            det_data = data.get(det_name, {})
            if det_data:
                detector_eval_counts[det_name] += 1
                result = det_module.evaluate(obligor, det_data)
                per_detector_results[det_name] = result
                if result.get("fires"):
                    fired_by.append(det_name)
                    detector_fire_counts[det_name] += 1

        # External detectors (already-computed signals)
        if ma_leverage_fires.get(obligor):
            fired_by.append("ma_leverage")
            detector_fire_counts["ma_leverage"] += 1
        detector_eval_counts["ma_leverage"] += 1 if obligor in ma_leverage_fires else 0

        if include_tripwire and covenant_tripwire_fires.get(obligor):
            fired_by.append("covenant_tripwire")
            detector_fire_counts["covenant_tripwire"] += 1

        per_obligor.append({
            "obligor": obligor,
            "fired_by": fired_by,
            "excluded": len(fired_by) > 0,
            "n_detectors_fired": len(fired_by),
            "per_detector": per_detector_results,
        })

    n_excluded = sum(1 for r in per_obligor if r["excluded"])
    n_total = len(per_obligor)
    clean_basket = [r["obligor"] for r in per_obligor if not r["excluded"]]
    excluded_basket = [r["obligor"] for r in per_obligor if r["excluded"]]

    return {
        "n_universe": n_total,
        "n_excluded": n_excluded,
        "n_clean": n_total - n_excluded,
        "exclusion_rate": n_excluded / max(1, n_total),
        "detector_fire_counts": dict(detector_fire_counts),
        "detector_eval_counts": dict(detector_eval_counts),
        "detector_fire_rates": {
            name: detector_fire_counts[name] / max(1, detector_eval_counts[name])
            for name in detector_fire_counts
        },
        "clean_basket": clean_basket,
        "excluded_basket": excluded_basket,
        "per_obligor": per_obligor,
    }


def measure_exclusion_alpha(union_result: dict, outcomes: dict, threshold: str = "loose") -> dict:
    """Measure: does the clean basket have a lower deterioration rate than the full universe?

    outcomes: dict {obligor_name → outcome_class}
    """
    deteriorated_strict = {"DOWNGRADE", "MULTI_DOWNGRADE", "DEFAULT"}
    deteriorated_loose = deteriorated_strict | {"AFFIRM_NEGATIVE_OUTLOOK"}
    deteriorated_set = deteriorated_strict if threshold == "strict" else deteriorated_loose

    def is_deterioration(outcome):
        return outcome in deteriorated_set

    clean = union_result["clean_basket"]
    excluded = union_result["excluded_basket"]
    full = clean + excluded

    def deterioration_rate(basket):
        evaluable = [o for o in basket if o in outcomes and outcomes[o] not in (None, "UNVERIFIABLE")]
        if not evaluable:
            return None, 0, 0
        n_det = sum(1 for o in evaluable if is_deterioration(outcomes[o]))
        return n_det / len(evaluable), n_det, len(evaluable)

    clean_rate, clean_n_det, clean_n = deterioration_rate(clean)
    excl_rate, excl_n_det, excl_n = deterioration_rate(excluded)
    full_rate, full_n_det, full_n = deterioration_rate(full)

    return {
        "threshold": threshold,
        "clean_basket_size": len(clean),
        "clean_evaluable": clean_n,
        "clean_n_deteriorated": clean_n_det,
        "clean_deterioration_rate": clean_rate,
        "excluded_basket_size": len(excluded),
        "excluded_evaluable": excl_n,
        "excluded_n_deteriorated": excl_n_det,
        "excluded_deterioration_rate": excl_rate,
        "full_universe_size": len(full),
        "full_evaluable": full_n,
        "full_n_deteriorated": full_n_det,
        "full_deterioration_rate": full_rate,
        "exclusion_alpha_pp": (full_rate - clean_rate) * 100 if clean_rate is not None and full_rate is not None else None,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m detectors.union_runner <data_file.json>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        data = json.load(f)
    result = run(data.get("detector_data", {}), data.get("ma_leverage_fires", {}))
    print(json.dumps(result, indent=2, default=str))
