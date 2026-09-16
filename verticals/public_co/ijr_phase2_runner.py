"""IJR Phase-2 runner — cluster-specific m-sources on missed catastrophes.

Targets the 56 names where Phase 1 distress_composite = 0.000 yet 24m
return ≤ -30%. For each, dispatches the cluster-appropriate additional
m-sources where inputs are auto-derivable from ticker/company name.

DISPATCH

  CONSUMER_STAPLES_FOOD       openfda.query_inspection_history (food + drug)
  HEALTHCARE_DEVICES          openfda.query_inspection_history (device + drug)
  HEALTHCARE_PHARMA           openfda.query_inspection_history (drug) +
                              orange_book.query_orange_book (applicant LOE)
  CONSUMER_STAPLES_DISTRIB    openfda.query_inspection_history (drug supplements)
  MATERIALS_CHEMICALS         epa_emissions.query_facility_emissions +
                              osha_establishments.query_establishments
  MATERIALS_METALS            osha_establishments + epa_frs.query_facilities
  INDUSTRIALS_CONSTRUCTION    osha_establishments
  INDUSTRIALS_MACHINERY       osha_establishments + nhtsa.query_manufacturer
  INDUSTRIALS_WHOLESALE       osha_establishments
  INDUSTRIALS_INSTRUMENTS     osha_establishments
  CONSUMER_DISCRETIONARY      nhtsa.query_manufacturer (if auto-parts)
  CONSUMER_RESTAURANTS        osha_establishments
  REAL_ESTATE                 (skip — needs curated tenant lists for tenant_credit_watch)

OUTPUT

  data/_ijr_manifest/phase2_scores.json — same shape as phase1_scores.json
  Combines Phase 1 + Phase 2 RFM tuples and recomputes composite.

Usage:
  python3 -m verticals.public_co.ijr_phase2_runner --cutoff 2024-05-15
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Optional

from .m_sources import (
    composite_recompute,
    openfda,
    orange_book,
    epa_emissions,
    osha_establishments,
    epa_frs,
    nhtsa,
)
from .ijr_universe_runner import _to_rfm_tuple

HERE = Path(__file__).parent
DATA = HERE / "data" / "_ijr_manifest"
P1_SCORES = DATA / "phase1_scores.json"
MISSES = DATA / "phase2_misses.json"
OUT = DATA / "phase2_scores.json"


# ============================================================
# Wrapper functions that adapt diverse signatures + emit standard
# severity/direction. Each wrapper takes (name, cutoff) → dict.
# ============================================================

def _wrap_openfda_inspection(endpoints):
    def _w(name: str, cutoff: str) -> dict:
        return openfda.query_inspection_history(name, cutoff, endpoints=endpoints)
    return _w


def _wrap_orange_book(name: str, cutoff: str) -> dict:
    return orange_book.query_orange_book(name, cutoff)


def _wrap_epa_emissions(name: str, cutoff: str) -> dict:
    """EPA emissions returns 'operational_scale_signal' rather than severity.
    Map to severity/direction here."""
    try:
        res = epa_emissions.query_facility_emissions(name)
    except Exception as e:
        return {"signal": "ERROR", "_note": str(e)}
    if "error" in res:
        return {"signal": "UNVERIFIABLE", "severity": "UNVERIFIABLE",
                "direction": "neutral", "_note": res.get("error", "")}
    sig = res.get("operational_scale_signal", "UNKNOWN")
    # No facilities found is a recovery signal for a chemicals firm (no Superfund liability)
    # Many facilities w/ violations = catastrophe-relevant
    n_loc = res.get("n_locations", 0) or 0
    n_violations = res.get("n_violations_5y", 0) or 0
    if sig == "FACILITIES_FOUND" and n_violations >= 5:
        return {"signal": "EPA_VIOLATIONS_HIGH",
                "severity": "MODERATE_UNDERDELIVERY", "direction": "negative",
                "_note": f"{n_violations} EPA violations across {n_loc} facilities."}
    if sig == "FACILITIES_FOUND":
        return {"signal": "EPA_PRESENT_CLEAN",
                "severity": "PASS", "direction": "positive",
                "_note": f"{n_loc} facilities, no major violations."}
    return {"signal": sig, "severity": "UNVERIFIABLE", "direction": "neutral"}


def _wrap_osha(name: str, cutoff: str) -> dict:
    try:
        res = osha_establishments.query_establishments(name)
    except Exception as e:
        return {"signal": "ERROR", "_note": str(e)}
    if "error" in res:
        return {"signal": "UNVERIFIABLE", "severity": "UNVERIFIABLE", "direction": "neutral"}
    n_estab = res.get("n_establishments", 0) or 0
    # Look at inspection results / violations
    dart_rate = res.get("avg_dart_rate")
    if dart_rate and dart_rate > 5:
        return {"signal": "OSHA_HIGH_INJURY", "severity": "MODERATE_UNDERDELIVERY",
                "direction": "negative",
                "_note": f"Avg DART rate {dart_rate:.1f} across {n_estab} establishments."}
    if n_estab > 0:
        return {"signal": "OSHA_PRESENT_CLEAN", "severity": "PASS",
                "direction": "positive", "_note": f"{n_estab} establishments, normal injury rates."}
    return {"signal": "OSHA_NO_RECORDS", "severity": "UNVERIFIABLE", "direction": "neutral"}


def _wrap_nhtsa(name: str, cutoff: str) -> dict:
    try:
        res = nhtsa.query_manufacturer(name)
    except Exception as e:
        return {"signal": "ERROR", "_note": str(e)}
    n = res.get("n_manufacturers", 0) or 0
    if n > 0:
        return {"signal": "NHTSA_REGISTERED", "severity": "PASS", "direction": "neutral"}
    return {"signal": "NHTSA_NOT_FOUND", "severity": "UNVERIFIABLE", "direction": "neutral"}


# ============================================================
# Cluster → list of (m_source_name, callable(name, cutoff)) tuples
# ============================================================

DISPATCH: dict[str, list[tuple[str, Callable[[str, str], dict]]]] = {
    "CONSUMER_STAPLES_FOOD":     [("openfda_inspection_food", _wrap_openfda_inspection(("food", "drug")))],
    "HEALTHCARE_DEVICES":        [("openfda_inspection_device", _wrap_openfda_inspection(("device", "drug")))],
    "HEALTHCARE_PHARMA":         [
        ("openfda_inspection_drug", _wrap_openfda_inspection(("drug",))),
        ("orange_book_loe",        _wrap_orange_book),
    ],
    "CONSUMER_STAPLES_DISTRIB":  [("openfda_inspection_supp", _wrap_openfda_inspection(("drug", "food")))],
    "MATERIALS_CHEMICALS":       [
        ("epa_emissions",          _wrap_epa_emissions),
        ("osha_establishments",    _wrap_osha),
    ],
    "MATERIALS_METALS":          [("osha_establishments", _wrap_osha)],
    "INDUSTRIALS_CONSTRUCTION":  [("osha_establishments", _wrap_osha)],
    "INDUSTRIALS_MACHINERY":     [
        ("osha_establishments",    _wrap_osha),
        ("nhtsa_manufacturer",     _wrap_nhtsa),
    ],
    "INDUSTRIALS_WHOLESALE":     [("osha_establishments", _wrap_osha)],
    "INDUSTRIALS_INSTRUMENTS":   [("osha_establishments", _wrap_osha)],
    "CONSUMER_DISCRETIONARY":    [("nhtsa_manufacturer", _wrap_nhtsa)],
    "CONSUMER_RESTAURANTS":      [("osha_establishments", _wrap_osha)],
}


_NAME_SUFFIXES = (
    "/The",
    " Inc",
    " Corp",
    " Corporation",
    " Co",
    " Ltd",
    " Holdings",
    " Holdings Inc",
    " Group",
    " Group Inc",
    " PLC",
    " LLC",
)


def _clean_company_name(name: str) -> str:
    """Strip trailing corporate suffixes and odd punctuation so substring
    matching in external feeds (openFDA, EPA, OSHA, NHTSA, Orange Book)
    has a clean brand-form to match against."""
    n = (name or "").replace("&amp;", "&").strip()
    if n.endswith("/The"):
        n = n[:-4].rstrip()
    # Iteratively strip known suffixes from the right
    changed = True
    while changed:
        changed = False
        for s in _NAME_SUFFIXES:
            if n.lower().endswith(s.lower()):
                n = n[: -len(s)].rstrip(" ,")
                changed = True
                break
    return n


def run_one(name: str, cluster: str, cutoff: str) -> list[dict]:
    """Run Phase 2 modules for a single name based on cluster."""
    modules = DISPATCH.get(cluster, [])
    cleaned = _clean_company_name(name)
    out = []
    for m_name, fn in modules:
        try:
            res = fn(cleaned, cutoff)
        except Exception as e:
            res = {"signal": "ERROR", "_note": f"{type(e).__name__}: {e}"}
        out.append(_to_rfm_tuple(m_name, res))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--max", type=int, default=0)
    args = ap.parse_args()

    misses = json.loads(MISSES.read_text())
    if args.max:
        misses = misses[: args.max]
    p1 = json.loads(P1_SCORES.read_text())
    p1_scores = p1["scores"]

    print(f"Running Phase 2 on {len(misses)} misses with {args.workers} workers...", file=sys.stderr)
    t_start = time.time()
    lock = Lock()
    out_scores: dict[str, dict] = {}

    def _worker(m: dict) -> Optional[tuple[str, dict]]:
        t = m["ticker"]
        cluster = m["cluster"]
        name = m["name"]
        if cluster not in DISPATCH:
            return t, {"skipped": True, "reason": f"no Phase 2 dispatch for cluster {cluster}"}
        t0 = time.time()
        p2_tuples = run_one(name, cluster, args.cutoff)
        elapsed = time.time() - t0

        # Combine with Phase 1 tuples
        p1_entry = p1_scores.get(t, {})
        p1_tuples = p1_entry.get("rfm_tuples", [])
        combined = p1_tuples + p2_tuples

        pilot = {"ticker": t, "cutoff": args.cutoff, "rfm_tuples": combined}
        comp = composite_recompute.recompute(pilot)

        return t, {
            "cik": p1_entry.get("cik"),
            "cluster": cluster,
            "company_name": name,
            "ret_24m": m["ret24"],
            "p1_distress": p1_entry.get("distress_composite"),
            "p2_distress": comp.get("distress_composite"),
            "p2_recovery": comp.get("recovery_composite"),
            "p2_tier": comp.get("tier"),
            "p2_n_formal": comp.get("n_formal_tuples"),
            "p2_tuples": p2_tuples,
            "_elapsed_s": round(elapsed, 1),
        }

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(_worker, m): m for m in misses}
        for fut in as_completed(futures):
            result = fut.result()
            if result is None:
                continue
            ticker, payload = result
            with lock:
                out_scores[ticker] = payload

    elapsed = time.time() - t_start
    OUT.write_text(json.dumps({
        "cutoff_date": args.cutoff,
        "n_misses": len(misses),
        "n_scored": len(out_scores),
        "scores": out_scores,
    }, indent=2, default=str))
    print(f"Done. {len(out_scores)} scored in {elapsed/60:.1f}m. Output: {OUT}", file=sys.stderr)

    # Summary: how many newly caught?
    newly_caught = [t for t, s in out_scores.items()
                    if s.get("p2_distress") and s.get("p2_distress") > 0]
    print(f"\nNewly caught at distress > 0: {len(newly_caught)}/{len(misses)}")
    print(f"Newly caught at distress >= 0.20: "
          f"{sum(1 for t, s in out_scores.items() if (s.get('p2_distress') or 0) >= 0.20)}/{len(misses)}")


if __name__ == "__main__":
    main()
