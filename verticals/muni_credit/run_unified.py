"""Unified runner: 4-axis HCRIS + CAFR overrides + Material Events + MMD spread.

Architecture:
  1. Pull CMS HCRIS facility-level cost reports → operational margin / payer mix
  2. Layer in CAFR consolidated days-cash + total margin (for academic centers)
  3. Apply MEN-based override (Material Event in 24m → severity floor)
  4. Compute implied spread vs explicit rating using MMD curve

Final output per obligor:
  - HCRIS-only score
  - CAFR-adjusted score  (replaces days-cash + total-margin axes)
  - MEN-adjusted final score
  - Divergence in notches + bps vs explicit rating
  - Combined signal
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy

from .composite_score import (
    gather_facilities, composite, consensus_explicit_score,
    divergence_signal, HOSPITAL_COLS,
)
from .emma_material_events import query_obligor_events
from .mmd_proxy import divergence_bps

HERE = Path(__file__).parent
SYSTEMS_FILE = HERE / "data" / "top_30_systems.json"
CAFR_FILE = HERE / "data" / "cafr_overrides.json"
RESULTS_FILE = HERE / "outputs" / "unified_results.json"

# Letter score map (S&P scale)
LETTER_SCORE = {
    "AAA": 100, "AA+": 95, "AA": 92, "AA-": 89,
    "A+": 85, "A": 82, "A-": 79,
    "BBB+": 75, "BBB": 72, "BBB-": 69,
    "BB+": 65, "BB": 62, "BB-": 59,
    "B+": 55, "B": 52, "B-": 49,
    "CCC+": 45, "CCC": 42, "CCC-": 39,
}


def _days_cash_score(days_cash: float) -> tuple[int, str]:
    """Map days-cash to score + letter."""
    if   days_cash >= 250: return 95, "AA"
    elif days_cash >= 150: return 88, "AA-"
    elif days_cash >= 100: return 83, "A+"
    elif days_cash >= 75:  return 78, "A"
    elif days_cash >= 50:  return 73, "BBB+"
    elif days_cash >= 25:  return 68, "BBB"
    else:                  return 55, "BB"


def _total_margin_score(total_margin_pct: float) -> tuple[int, str]:
    """Map consolidated total margin to score + letter (more generous than operating)."""
    if   total_margin_pct >= 8:  return 95, "AA"
    elif total_margin_pct >= 5:  return 90, "AA-"
    elif total_margin_pct >= 3:  return 85, "A+"
    elif total_margin_pct >= 1:  return 82, "A"
    elif total_margin_pct >= 0:  return 78, "A-"
    elif total_margin_pct >= -2: return 75, "BBB+"
    elif total_margin_pct >= -5: return 70, "BBB"
    elif total_margin_pct >= -8: return 65, "BB+"
    else:                       return 50, "B+"


def _letter_from_score(score: float) -> str:
    if   score >= 92: return "AA"
    elif score >= 88: return "AA-"
    elif score >= 85: return "A+"
    elif score >= 81: return "A"
    elif score >= 78: return "A-"
    elif score >= 74: return "BBB+"
    elif score >= 70: return "BBB"
    elif score >= 66: return "BBB-"
    elif score >= 62: return "BB+"
    elif score >= 58: return "BB"
    elif score >= 54: return "BB-"
    elif score >= 50: return "B+"
    else:             return "B"


def _apply_cafr_override(base_composite: dict, cafr: dict) -> dict:
    """Recompute composite replacing operating margin + days-cash with consolidated values.

    Weights stay the same: 40% margin (now consolidated total), 25% days-cash
    (now consolidated), 20% payer mix (HCRIS-derived), 15% local econ.
    """
    if not cafr or base_composite.get("composite_score") is None:
        return base_composite

    # Get original axes from HCRIS composite
    axes = base_composite.get("axes", {})
    payer_score = axes.get("payer_mix", {}).get("score")
    econ_score = axes.get("local_econ", {}).get("score")

    # Replace margin + days-cash with CAFR values
    cafr_margin_score, cafr_margin_letter = _total_margin_score(
        cafr["consolidated_total_margin_pct"])
    cafr_cash_score, cafr_cash_letter = _days_cash_score(
        cafr["consolidated_days_cash"])

    # Re-weight
    components = [
        (cafr_margin_score, 0.40),
        (cafr_cash_score,   0.25),
        (payer_score,       0.20),
        (econ_score,        0.15),
    ]
    weighted, total_w = 0, 0
    for s, w in components:
        if s is not None:
            weighted += s * w
            total_w += w
    if total_w == 0:
        return base_composite
    new_score = weighted / total_w

    return {
        "composite_score": round(new_score, 1),
        "letter": _letter_from_score(new_score),
        "total_weight_used": round(total_w, 2),
        "axes": {
            "margin":     {"score": cafr_margin_score, "letter": cafr_margin_letter,
                           "source": "CAFR_CONSOLIDATED",
                           "total_margin_pct": cafr["consolidated_total_margin_pct"]},
            "days_cash":  {"score": cafr_cash_score, "letter": cafr_cash_letter,
                           "source": "CAFR_CONSOLIDATED",
                           "days_cash": cafr["consolidated_days_cash"]},
            "payer_mix":  axes.get("payer_mix", {}),
            "local_econ": axes.get("local_econ", {}),
        },
        "cafr_diagnostic": {
            "investment_income_pct_of_margin": cafr.get("investment_income_pct"),
        },
    }


def _apply_men_floor(score: float, men_result: dict) -> tuple[float, str | None]:
    """Material Event Notice severity floor.

    A MEN at SEVERE+ in last 24m caps the score at BB+ (65); RED_FLAG caps at B+ (55).
    Returns (new_score, override_reason).
    """
    sev = men_result.get("severity") or "PASS"
    if sev == "RED_FLAG_NEGATIVE":
        return min(score, 55), "MEN_BANKRUPTCY_FLOOR"
    if sev == "SEVERE_UNDERDELIVERY":
        return min(score, 62), "MEN_SEVERE_FLOOR"
    if sev == "MODERATE_UNDERDELIVERY":
        return min(score, 75), "MEN_MODERATE_FLOOR"
    return score, None


def process_system(sys_def: dict, cafr_db: dict) -> dict:
    name = sys_def["name"]
    state = sys_def["state"]
    queries = sys_def["queries"]
    moodys = sys_def.get("moodys")
    sp = sys_def.get("sp")
    fitch = sys_def.get("fitch")

    print(f"  Processing {name}", file=sys.stderr)

    # Step 1: HCRIS-only composite
    rows = gather_facilities(queries)
    fys = sorted({(r.get(HOSPITAL_COLS["fy_end"]) or "")[:4] for r in rows
                  if r.get(HOSPITAL_COLS["fy_end"])})
    latest_fy = fys[-1] if fys else None
    hcris_only = composite(rows, state=state, fiscal_year=latest_fy)

    # Step 2: CAFR overlay
    cafr = cafr_db.get(name)
    cafr_adjusted = _apply_cafr_override(hcris_only, cafr) if cafr else hcris_only

    # Step 3: Material Events floor
    men = query_obligor_events(name, "2024-12-31", lookback_days=730)
    cafr_score = cafr_adjusted.get("composite_score") or 0
    final_score, override_reason = _apply_men_floor(cafr_score, men)

    final_letter = _letter_from_score(final_score)

    # Step 4: Divergence
    explicit_score, explicit_letter = consensus_explicit_score(moodys, sp, fitch)
    notches, signal = divergence_signal(final_score, explicit_score)
    bps_div = divergence_bps(final_letter, explicit_letter, "2024-12-31")

    return {
        "system": name,
        "state": state,
        "explicit": {
            "moodys": moodys, "sp": sp, "fitch": fitch,
            "consensus_score": explicit_score, "consensus_letter": explicit_letter,
        },
        "n_hcris_facilities": len({r.get(HOSPITAL_COLS["ccn"]) for r in rows
                                    if r.get(HOSPITAL_COLS["ccn"])}),
        "fiscal_years_in_hcris": fys,
        "hcris_only_score": {
            "composite": hcris_only.get("composite_score"),
            "letter":    hcris_only.get("letter"),
        },
        "cafr_overlay_used": cafr is not None,
        "cafr_adjusted_score": {
            "composite": cafr_adjusted.get("composite_score"),
            "letter":    cafr_adjusted.get("letter"),
        },
        "material_events": {
            "signal":   men.get("signal"),
            "severity": men.get("severity"),
            "n_events": men.get("n_events", 0),
            "events_by_code": men.get("events_by_code", {}),
        },
        "final_score": {
            "composite": round(final_score, 1),
            "letter":    final_letter,
            "men_override": override_reason,
        },
        "divergence": {
            "notches": notches,
            "signal":  signal,
            "bps":     bps_div.get("divergence_bps"),
            "our_implied_spread_bps":      bps_div.get("our_implied_spread_bps"),
            "explicit_implied_spread_bps": bps_div.get("explicit_implied_spread_bps"),
            "interpretation":              bps_div.get("interpretation"),
        },
    }


def main():
    t0 = time.time()
    systems = json.loads(SYSTEMS_FILE.read_text())["systems"]
    cafr_db = json.loads(CAFR_FILE.read_text()).get("overrides", {})
    print(f"Processing {len(systems)} systems × 4 layers (HCRIS + CAFR + MEN + MMD)...",
          file=sys.stderr)

    results = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(process_system, s, cafr_db): s["name"] for s in systems}
        for fut in as_completed(futures):
            results.append(fut.result())

    results.sort(key=lambda r: -r["divergence"]["notches"])

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_FILE.write_text(json.dumps({
        "run_date": "2026-05-27",
        "n_systems": len(results),
        "elapsed_seconds": round(time.time() - t0, 1),
        "results": results,
    }, indent=2, default=str))

    elapsed = time.time() - t0
    print(f"\nDONE in {elapsed:.1f}s\n", file=sys.stderr)

    print(f"{'System':<28} {'Explicit':<8} {'HCRIS':<8} {'CAFR':<8} {'Final':<8} "
          f"{'MEN':<10} {'Notches':<9} {'Bps':<9} {'Signal':<14}")
    print("-" * 130)
    for r in results:
        hcris_let = r["hcris_only_score"]["letter"] or "—"
        cafr_let = r["cafr_adjusted_score"]["letter"] or "—"
        final_let = r["final_score"]["letter"] or "—"
        men_sig = (r["material_events"]["signal"] or "—").replace("MEN_","")[:9]
        bps = r["divergence"]["bps"]
        bps_str = f"{bps:+d}bp" if bps is not None else "—"
        print(f"{r['system']:<28} {r['explicit']['consensus_letter']:<8} "
              f"{hcris_let:<8} {cafr_let:<8} {final_let:<8} "
              f"{men_sig:<10} {r['divergence']['notches']:+.1f}     {bps_str:<9} "
              f"{r['divergence']['signal']}")


if __name__ == "__main__":
    main()
