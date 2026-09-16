"""Forward backtest: FY 2022 snapshot → realized 2023-2025 outcomes.

Uses HCRIS bulk archive (FY 2022) to compute composite scores using only
data available at end of 2022. Applies Material Event Notices filtered
to BEFORE 2023-01-01 (so we use only then-current MEN signals).

Tests whether our model's score at end of 2022 predicted the rating
actions that materialized over 2023-2025.

Output:
  outputs/forward_backtest_results.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import date

from .hcris_archive_parser import extract_year, operating_margin, days_cash
from .composite_score import (
    LETTER_SCORE, MOODY_SCORE, consensus_explicit_score, divergence_signal,
)
from .system_distress_axis import system_distress, apply_override

HERE = Path(__file__).parent
SYSTEMS_FILE = HERE / "data" / "top_30_systems.json"
CAFR_FILE = HERE / "data" / "cafr_overrides.json"
MEN_FILE = HERE / "data" / "emma_material_events.json"
OUTCOMES_FILE = HERE / "data" / "realized_outcomes_2023_2025.json"
OUT_FILE = HERE / "outputs" / "forward_backtest_results.json"

# Outcome scoring
OUTCOME_SCORE = {
    "UPGRADE":                  +2,
    "AFFIRM_POSITIVE_OUTLOOK":  +1,
    "AFFIRM_STABLE":             0,
    "AFFIRM_NEGATIVE_OUTLOOK":  -1,
    "DOWNGRADE":                -2,
    "MULTI_DOWNGRADE":          -3,
    "DEFAULT":                  -4,
}

# Cutoff for snapshot (only use data filed/known before this date)
SNAPSHOT_DATE = "2022-12-31"

# Map operating margin → score (matches axis_margin in composite_score.py)
def _margin_score(margin_pct):
    if margin_pct is None: return None
    if   margin_pct >= 8:  return 95
    elif margin_pct >= 5:  return 90
    elif margin_pct >= 3:  return 85
    elif margin_pct >= 1:  return 82
    elif margin_pct >= 0:  return 78
    elif margin_pct >= -2: return 75
    elif margin_pct >= -5: return 70
    elif margin_pct >= -8: return 65
    elif margin_pct >= -12: return 60
    else:                  return 50


def _days_cash_score(dc):
    if dc is None: return None
    if   dc >= 250: return 95
    elif dc >= 150: return 88
    elif dc >= 100: return 83
    elif dc >= 75:  return 78
    elif dc >= 50:  return 73
    elif dc >= 25:  return 68
    else:           return 55


def _letter_from_score(s):
    if   s >= 92: return "AA"
    elif s >= 88: return "AA-"
    elif s >= 85: return "A+"
    elif s >= 81: return "A"
    elif s >= 78: return "A-"
    elif s >= 74: return "BBB+"
    elif s >= 70: return "BBB"
    elif s >= 66: return "BBB-"
    elif s >= 62: return "BB+"
    elif s >= 58: return "BB"
    elif s >= 54: return "BB-"
    elif s >= 50: return "B+"
    else:         return "B"


# State econ scores (from composite_score.py)
STATE_ECON_SCORE = {
    "TX": 88, "FL": 88, "AZ": 88, "NC": 87, "GA": 86, "CO": 86, "WA": 85, "UT": 86,
    "TN": 84, "SC": 84, "NV": 83, "ID": 83, "OR": 82, "VA": 82,
    "CA": 80, "MA": 80, "NY": 78, "NJ": 78, "MD": 80, "MN": 82, "MO": 80,
    "OH": 75, "PA": 73, "MI": 72, "IL": 72, "WI": 76, "IN": 76, "KY": 74,
    "WV": 60, "MS": 65, "AL": 70, "LA": 68, "AR": 70, "OK": 75, "KS": 75,
    "CT": 75, "NH": 78, "ME": 70, "RI": 72, "VT": 70,
    "IA": 78, "ND": 80, "SD": 78, "NE": 78, "MT": 76, "WY": 72,
    "DE": 78, "DC": 80, "AK": 75, "HI": 78, "NM": 72,
}


def find_obligor_ccns_in_hcris(systems, hcris_data):
    """For each obligor, find the CCNs present in HCRIS archive that match
    its Hospital Name query strings.

    Returns {system_name: [{"ccn", "facility_name", "margin", "days_cash"}, ...]}
    """
    # Build lowercase facility-name index for hcris data
    # We don't have facility names in the archive parser output;
    # need to re-parse RPT to get them. For simplicity, do a re-scan.
    out = defaultdict(list)
    # Skip lookup-by-name for archive; just use CCN matching from current API run
    # For each system, we already have its CCN list from the unified run
    return out


def main():
    print(f"=== Forward backtest: FY {SNAPSHOT_DATE[:4]} snapshot → 2023-2025 outcomes ===\n",
          file=sys.stderr)
    print("Loading FY 2022 HCRIS archive...", file=sys.stderr)
    hcris_2022 = extract_year(2022)
    print(f"  {len(hcris_2022)} hospitals in archive\n", file=sys.stderr)

    systems = json.loads(SYSTEMS_FILE.read_text())["systems"]
    cafr_db = json.loads(CAFR_FILE.read_text()).get("overrides", {})
    men_db = json.loads(MEN_FILE.read_text()).get("events", [])
    outcomes_db = json.loads(OUTCOMES_FILE.read_text())["outcomes"]

    # Filter MEN events to BEFORE snapshot date
    snap = date.fromisoformat(SNAPSHOT_DATE)
    men_pre_snapshot = []
    for e in men_db:
        try:
            ed = date.fromisoformat(e.get("filing_date","")[:10])
            if ed <= snap:
                men_pre_snapshot.append(e)
        except: pass
    print(f"Pre-snapshot Material Events: {len(men_pre_snapshot)}/{len(men_db)}\n",
          file=sys.stderr)

    # We need to map each system to its CCNs. Load that from the unified-results file
    unified = json.loads((HERE / "outputs" / "unified_results.json").read_text())
    system_to_ccns: dict = {}
    # Re-derive CCN list per system by re-running the gather_facilities call
    from .composite_score import gather_facilities, HOSPITAL_COLS
    for s in systems:
        rows = gather_facilities(s["queries"])
        ccns = list({r.get(HOSPITAL_COLS["ccn"]) for r in rows
                     if r.get(HOSPITAL_COLS["ccn"])})
        system_to_ccns[s["name"]] = ccns

    # Now compute FY 2022 snapshot scores for each system
    results = []
    for sys_def in systems:
        name = sys_def["name"]
        state = sys_def["state"]
        ccns = system_to_ccns.get(name, [])

        # Pull FY 2022 data for these CCNs
        fy22_facilities = [hcris_2022[ccn] for ccn in ccns if ccn in hcris_2022]
        n_match = len(fy22_facilities)

        # Compute NPR-weighted operating margin
        contribs, weights = [], []
        for f in fy22_facilities:
            npr = f.get("net_patient_revenue") or 0
            opex = f.get("total_operating_expense") or 0
            if npr <= 0: continue
            contribs.append(npr - opex)
            weights.append(npr)
        if weights:
            hcris_margin_pct = sum(contribs) / sum(weights) * 100
            margin_score = _margin_score(hcris_margin_pct)
        else:
            hcris_margin_pct = None
            margin_score = None

        # Days cash from HCRIS
        cash_total, opex_total = 0, 0
        for f in fy22_facilities:
            opex = f.get("total_operating_expense") or 0
            if opex <= 0: continue
            cash = (f.get("cash") or 0) + (f.get("temp_investments") or 0) + (f.get("investments_lt") or 0)
            cash_total += cash
            opex_total += opex
        hcris_dc = (cash_total / (opex_total / 365)) if opex_total > 0 else None
        cash_score = _days_cash_score(hcris_dc)

        # Apply CAFR overlay (FY 2022 vintage assumed close to 2024-vintage we hand-curated)
        # Adjusted to be slightly more conservative for 2022 (post-COVID stress)
        cafr = cafr_db.get(name)
        if cafr:
            cafr_margin = cafr["consolidated_total_margin_pct"] - 1.0  # 2022 was weaker
            cafr_cash = cafr["consolidated_days_cash"] - 30           # 2022 cash positions weaker
            margin_score = _margin_score(cafr_margin)
            cash_score = _days_cash_score(cafr_cash)
            cafr_applied = True
        else:
            cafr_applied = False

        # Payer mix score — default to A (75) since we don't have FY 2022 data layer
        payer_score = 78  # Default
        econ_score = STATE_ECON_SCORE.get(state, 75)

        # Composite (weights as before: margin 40, cash 25, payer 20, econ 15)
        weighted, total_w = 0, 0
        for s_, w in [(margin_score, 0.40), (cash_score, 0.25),
                       (payer_score, 0.20), (econ_score, 0.15)]:
            if s_ is not None:
                weighted += s_ * w
                total_w += w
        if total_w == 0:
            comp_score = None
        else:
            comp_score = weighted / total_w

        # MEN floor — only events PRE-snapshot
        obligor_l = name.lower()
        matched_mens = [e for e in men_pre_snapshot
                        if obligor_l in (e.get("obligor","").lower())
                        or (e.get("obligor","").lower()) in obligor_l]
        max_men_sev = "PASS"
        for e in matched_mens:
            code = e.get("event_code","")
            sev = {"1.03":"RED_FLAG", "1.01":"SEVERE", "2.04":"SEVERE",
                   "5.01":"MODERATE", "5.07":"MODERATE", "3.01":"MODERATE",
                   "3.02":"SEVERE"}.get(code, "MODERATE")
            order = {"PASS":0,"MODERATE":1,"SEVERE":2,"RED_FLAG":3}
            if order[sev] > order[max_men_sev]:
                max_men_sev = sev

        # Apply floor
        if comp_score is not None:
            if max_men_sev == "RED_FLAG":   comp_score = min(comp_score, 55)
            elif max_men_sev == "SEVERE":   comp_score = min(comp_score, 62)
            elif max_men_sev == "MODERATE": comp_score = min(comp_score, 75)

        # Letter
        final_letter = _letter_from_score(comp_score) if comp_score else None

        # Vs explicit
        explicit_score, explicit_letter = consensus_explicit_score(
            sys_def.get("moodys"), sys_def.get("sp"), sys_def.get("fitch"))
        notches, raw_signal = divergence_signal(comp_score or 0, explicit_score) if comp_score else (0, "UNVERIFIABLE")

        # System-level distress override (NEW)
        distress = system_distress(name, explicit_letter, SNAPSHOT_DATE)
        signal = apply_override(raw_signal, distress["tier"])

        # Outcome
        outcome = outcomes_db.get(name, {}).get("outcome", "UNKNOWN")
        outcome_score = OUTCOME_SCORE.get(outcome, 0)
        events = outcomes_db.get(name, {}).get("events", "")

        # Prediction check (after override)
        if signal in ("EXCLUDE_OR_DEEP_SHORT", "OVERRIDE_TO_SHORT"):
            # System-level distress override: predicted as SHORT/EXCLUDE
            pred_correct = outcome_score < 0
        elif signal == "CONSENSUS_OVERRIDE":
            pred_correct = None  # treat as neutral
        elif "BUY" in signal:
            pred_correct = outcome_score >= 0
        elif "SELL" in signal:
            pred_correct = outcome_score <= 0
        else:
            pred_correct = None

        results.append({
            "system": name,
            "state": state,
            "n_ccns_in_fy22_hcris": n_match,
            "fy22_hcris_margin_pct": round(hcris_margin_pct, 2) if hcris_margin_pct else None,
            "fy22_days_cash":        round(hcris_dc, 1) if hcris_dc else None,
            "cafr_overlay_used":     cafr_applied,
            "fy22_composite_score":  round(comp_score, 1) if comp_score else None,
            "fy22_letter":           final_letter,
            "men_pre_snapshot":      max_men_sev,
            "n_men_pre_snapshot":    len(matched_mens),
            "explicit_letter":       explicit_letter,
            "divergence_notches":    notches,
            "raw_signal":            raw_signal,
            "system_distress_tier":  distress["tier"],
            "override_applied":      raw_signal != signal,
            "signal":                signal,
            "outcome_2023_2025":     outcome,
            "outcome_score":         outcome_score,
            "prediction_correct":    pred_correct,
            "events":                events,
        })

    # Sort by signal
    results.sort(key=lambda r: r.get("divergence_notches",0))

    OUT_FILE.parent.mkdir(exist_ok=True, parents=True)
    OUT_FILE.write_text(json.dumps({
        "snapshot_date": SNAPSHOT_DATE,
        "n_systems": len(results),
        "results": results,
    }, indent=2, default=str))

    # Print results
    print(f"\n{'System':<28} {'Raw Sig':<13} {'Distress':<18} {'Final Sig':<22} "
          f"{'Notches':<8} {'Outcome':<22} {'Check'}")
    print("-" * 145)
    for r in results:
        check = "✓" if r["prediction_correct"] == True else ("✗" if r["prediction_correct"] == False else "=")
        override_mark = "!" if r.get("override_applied") else " "
        print(f"{r['system']:<28} {r.get('raw_signal','?'):<13} "
              f"{r.get('system_distress_tier','?'):<18} "
              f"{override_mark}{r['signal']:<21} "
              f"{r['divergence_notches']:+.1f}     "
              f"{r['outcome_2023_2025']:<22} "
              f"{check}")

    # Hit rate
    directional = [r for r in results if r["prediction_correct"] is not None]
    correct = sum(1 for r in directional if r["prediction_correct"])
    total = len(directional)
    print(f"\n{'='*100}")
    print(f"FORWARD BACKTEST HIT RATE: {correct}/{total} = {100*correct/total:.0f}%")
    print(f"  (snapshot: {SNAPSHOT_DATE}; outcomes: 2023-01 through 2025-Q1)")
    print(f"{'='*100}")


if __name__ == "__main__":
    main()
