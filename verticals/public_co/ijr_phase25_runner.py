"""Phase 2.5 — LLM-extracted inputs + cluster-specific m-source retry.

For the 21 misses in clusters with no Phase-2 dispatch:
  REAL_ESTATE       (5)  HPP, SVC, ABR, SITC, IIPR
  BUSINESS_SERVICES (8)  RGP, RHI, CARS, KELYA, TTEC, UPBD, DFIN, NEO
  TECH_SOFTWARE_SERVICES (5) NABL, SPSC, SLP, DV, CXM
  COMMUNICATIONS    (3)  CABO, TTGT, GOGO

Steps per ticker:
  1. Call llm_10k_extract.extract() with cluster-specific schema
  2. Convert extracted payload to a synthetic RFM tuple if it signals
     catastrophe risk (e.g., top tenant > 15%, KPI YoY < -5%, etc.)
  3. Combine with existing Phase 1 + Phase 2 tuples; recompute composite.

OUTPUT
  data/_ijr_manifest/phase25_scores.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Any

from .m_sources import composite_recompute, llm_10k_extract
from .ijr_universe_runner import _to_rfm_tuple

HERE = Path(__file__).parent
DATA = HERE / "data" / "_ijr_manifest"
MISSES = DATA / "phase2_misses.json"
P1_SCORES = DATA / "phase1_scores.json"
P2_SCORES = DATA / "phase2_scores.json"
OUT = DATA / "phase25_scores.json"

# Clusters where LLM extraction adds value
TARGET_CLUSTERS = {
    "REAL_ESTATE",
    "BUSINESS_SERVICES",
    "TECH_SOFTWARE_SERVICES",
    "COMMUNICATIONS",
    # bonus: also run on healthcare/pharma where we extract drug/CCN info
    "HEALTHCARE_SERVICES",
    "HEALTHCARE_PHARMA",
}


# ============================================================
# Payload → RFM tuple converters
# ============================================================

def _real_estate_signal(payload: dict) -> tuple[str, str, str, str]:
    """REIT tenant concentration. Returns (signal, severity, direction, note)."""
    tenants = payload.get("tenants") or []
    if not tenants:
        return ("NO_TENANT_TABLE", "UNVERIFIABLE", "neutral",
                "10-K had no extractable tenant table.")
    # Top tenant concentration
    top_pct = max((t.get("rent_pct") or 0) for t in tenants)
    top5_pct = sum(sorted([t.get("rent_pct") or 0 for t in tenants], reverse=True)[:5])
    # Heuristic catastrophe-risk classifier
    if top_pct >= 25:
        sig = "TENANT_HEAVY_CONCENTRATION"
        sev = "SEVERE_UNDERDELIVERY"
    elif top_pct >= 15:
        sig = "TENANT_NOTABLE_CONCENTRATION"
        sev = "MODERATE_UNDERDELIVERY"
    elif top5_pct >= 50:
        sig = "TOP5_HEAVY"
        sev = "MODERATE_UNDERDELIVERY"
    else:
        sig = "TENANTS_DIVERSIFIED"
        sev = "PASS"
    direction = "negative" if sev != "PASS" else "positive"
    return (sig, sev, direction,
            f"Top tenant {top_pct:.1f}%; top5 {top5_pct:.1f}%.")


def _business_services_signal(payload: dict) -> tuple[str, str, str, str]:
    customers = payload.get("named_customers") or []
    top1 = payload.get("top_1_customer_pct") or (max((c.get("revenue_pct") or 0) for c in customers) if customers else 0)
    top5 = payload.get("top_5_customer_pct") or (sum(sorted([c.get("revenue_pct") or 0 for c in customers], reverse=True)[:5]))

    if top1 >= 30:
        sig = "CUSTOMER_HEAVY"
        sev = "SEVERE_UNDERDELIVERY"
    elif top1 >= 15:
        sig = "CUSTOMER_NOTABLE"
        sev = "MODERATE_UNDERDELIVERY"
    elif top5 >= 50 and top5 > 0:
        sig = "TOP5_HEAVY"
        sev = "MODERATE_UNDERDELIVERY"
    elif not customers:
        return ("NO_CUSTOMER_DISCLOSURE", "PASS", "positive",
                "No 10% customer disclosure (per SEC rule, no single customer ≥ 10%).")
    else:
        sig = "CUSTOMERS_DIVERSIFIED"
        sev = "PASS"
    return (sig, sev, "negative" if sev != "PASS" else "positive",
            f"Top customer {top1:.1f}%; top5 {top5:.1f}%; n={len(customers)}.")


def _communications_signal(payload: dict) -> tuple[str, str, str, str]:
    """Cable/satellite/wifi: look at YoY KPI declines."""
    kpis = payload.get("kpis") or []
    if not kpis:
        return ("NO_KPI_TABLE", "UNVERIFIABLE", "neutral", "No KPI table extracted.")
    declines = []
    for k in kpis:
        yoy = k.get("yoy_change_pct")
        if yoy is None:
            v_now, v_prev = k.get("value_latest"), k.get("value_prior")
            if v_now and v_prev and v_prev != 0:
                yoy = 100.0 * (v_now - v_prev) / v_prev
        if yoy is not None:
            declines.append((yoy, k.get("metric", "?")))
    if not declines:
        return ("KPIS_NO_YOY", "UNVERIFIABLE", "neutral", "No YoY KPI deltas.")
    worst_yoy, worst_metric = min(declines)
    if worst_yoy <= -10:
        sig, sev = "KPI_SEVERE_DECLINE", "SEVERE_UNDERDELIVERY"
    elif worst_yoy <= -3:
        sig, sev = "KPI_DECLINING", "MODERATE_UNDERDELIVERY"
    elif worst_yoy >= 5:
        sig, sev = "KPI_GROWING", "PASS"
    else:
        sig, sev = "KPI_STABLE", "PASS"
    return (sig, sev, "negative" if sev != "PASS" else "positive",
            f"Worst KPI {worst_metric}: {worst_yoy:+.1f}% YoY.")


def _tech_software_signal(payload: dict) -> tuple[str, str, str, str]:
    # Look at NRR trajectory + customer concentration combined
    kpis = payload.get("kpis") or []
    nrr = None
    nrr_prev = None
    for k in kpis:
        m = (k.get("metric") or "").lower()
        if "revenue retention" in m or "nrr" in m:
            nrr = k.get("value_latest")
            nrr_prev = k.get("value_prior")
            break
    cust_sig, cust_sev, _, _ = _business_services_signal(payload)
    if nrr is not None and nrr_prev is not None:
        nrr_delta = nrr - nrr_prev
        if nrr < 100 and nrr_delta < -5:
            return ("NRR_INVERTED", "SEVERE_UNDERDELIVERY", "negative",
                    f"NRR {nrr:.0f} (was {nrr_prev:.0f}, Δ {nrr_delta:+.0f}pp).")
        if nrr_delta < -5:
            return ("NRR_DECELERATING", "MODERATE_UNDERDELIVERY", "negative",
                    f"NRR {nrr:.0f} (Δ {nrr_delta:+.0f}pp).")
    # Fall back to customer signal
    return (cust_sig, cust_sev,
            "negative" if cust_sev != "PASS" else "positive",
            f"NRR={nrr}, customer={cust_sig}.")


def _healthcare_signal(payload: dict) -> tuple[str, str, str, str]:
    # For now, just acknowledge facility coverage
    facilities = payload.get("facilities") or []
    if facilities:
        return ("FACILITIES_LISTED", "PASS", "neutral",
                f"{len(facilities)} facilities extracted (downstream CMS lookup needed).")
    return ("NO_FACILITY_LIST", "UNVERIFIABLE", "neutral", "")


def _pharma_signal(payload: dict) -> tuple[str, str, str, str]:
    drugs = payload.get("marketed_drugs") or []
    rev_conc = payload.get("revenue_concentration_pct")
    if rev_conc and rev_conc >= 80 and len(drugs) <= 2:
        return ("SINGLE_PRODUCT_DEPENDENT", "MODERATE_UNDERDELIVERY", "negative",
                f"{rev_conc:.0f}% revenue from {len(drugs)} marketed drug(s).")
    if drugs:
        return ("PORTFOLIO_DIVERSIFIED", "PASS", "positive",
                f"{len(drugs)} marketed drugs.")
    return ("NO_MARKETED_DRUGS", "UNVERIFIABLE", "neutral", "")


CLUSTER_SIGNALS = {
    "REAL_ESTATE":              _real_estate_signal,
    "BUSINESS_SERVICES":        _business_services_signal,
    "TECH_SOFTWARE_SERVICES":   _tech_software_signal,
    "COMMUNICATIONS":           _communications_signal,
    "HEALTHCARE_SERVICES":      _healthcare_signal,
    "HEALTHCARE_PHARMA":        _pharma_signal,
}


def _payload_to_rfm(cluster: str, payload: dict) -> dict:
    fn = CLUSTER_SIGNALS.get(cluster)
    if fn is None:
        return {"M_source": f"llm_{cluster.lower()}",
                "severity": "UNVERIFIABLE", "direction": "neutral",
                "signal": "NO_CONVERTER", "_raw": {}}
    sig, sev, direction, note = fn(payload)
    return {
        "M_source": f"llm_{cluster.lower()}_extract",
        "severity": sev,
        "direction": direction,
        "signal": sig,
        "_raw": {"_note": note},
    }


# ============================================================
# Main
# ============================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff", required=True)
    ap.add_argument("--workers", type=int, default=3,
                    help="Concurrent LLM calls (rate-limit safe)")
    ap.add_argument("--max", type=int, default=0)
    args = ap.parse_args()

    misses = json.loads(MISSES.read_text())
    targeted = [m for m in misses if m["cluster"] in TARGET_CLUSTERS]
    if args.max:
        targeted = targeted[: args.max]

    p1 = json.loads(P1_SCORES.read_text())["scores"]
    p2 = json.loads(P2_SCORES.read_text())["scores"]

    print(f"Running Phase 2.5 LLM extraction on {len(targeted)} misses "
          f"({args.workers} workers)...", file=sys.stderr)
    t_start = time.time()
    lock = Lock()
    out: dict[str, dict] = {}

    def _worker(m: dict) -> tuple[str, dict]:
        t = m["ticker"]
        try:
            ext = llm_10k_extract.extract(
                ticker=t, cik=m["cik"], cluster=m["cluster"],
                cutoff_date=args.cutoff,
            )
        except Exception as e:
            return t, {"error": f"extract failed: {type(e).__name__}: {e}",
                       "cluster": m["cluster"]}
        if "error" in ext:
            return t, {"error": ext["error"], "cluster": m["cluster"]}

        payload = ext.get("payload", {})
        new_tuple = _payload_to_rfm(m["cluster"], payload)
        p1_tuples = p1.get(t, {}).get("rfm_tuples", [])
        p2_entry = p2.get(t, {})
        p2_tuples = p2_entry.get("p2_tuples", []) if not p2_entry.get("skipped") else []
        combined = p1_tuples + p2_tuples + [new_tuple]

        pilot = {"ticker": t, "cutoff": args.cutoff, "rfm_tuples": combined}
        comp = composite_recompute.recompute(pilot)
        return t, {
            "cik": m["cik"],
            "cluster": m["cluster"],
            "ret_24m": m["ret24"],
            "p1_distress": p1.get(t, {}).get("distress_composite"),
            "p25_distress": comp.get("distress_composite"),
            "p25_recovery": comp.get("recovery_composite"),
            "p25_tier": comp.get("tier"),
            "p25_n_formal": comp.get("n_formal_tuples"),
            "llm_signal":  new_tuple["signal"],
            "llm_severity": new_tuple["severity"],
            "llm_note":    new_tuple.get("_raw", {}).get("_note", ""),
            "payload_summary": _summarize_payload(m["cluster"], payload),
        }

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(_worker, m): m for m in targeted}
        for fut in as_completed(futures):
            t, payload = fut.result()
            with lock:
                out[t] = payload
            print(f"  {t}: signal={payload.get('llm_signal')} "
                  f"sev={payload.get('llm_severity')} "
                  f"p25_dist={payload.get('p25_distress')}", file=sys.stderr)

    elapsed = time.time() - t_start
    OUT.write_text(json.dumps({
        "cutoff_date": args.cutoff,
        "n_misses_targeted": len(targeted),
        "n_scored": len(out),
        "scores": out,
    }, indent=2, default=str))
    print(f"\nDone. {len(out)} scored in {elapsed/60:.1f}m. Output: {OUT}", file=sys.stderr)

    catches = [t for t, s in out.items() if (s.get("p25_distress") or 0) >= 0.20]
    margins = [t for t, s in out.items()
               if 0 < (s.get("p25_distress") or 0) < 0.20]
    print(f"\nNewly caught at dist ≥ 0.20: {len(catches)} ({catches})")
    print(f"Marginal (0 < dist < 0.20): {len(margins)} ({margins})")


def _summarize_payload(cluster: str, payload: dict) -> str:
    if cluster == "REAL_ESTATE":
        tenants = payload.get("tenants", [])
        return f"{len(tenants)} tenants; top: " + ", ".join(
            f"{t.get('name','?')}({t.get('rent_pct','?')}%)" for t in tenants[:3])
    if cluster in ("BUSINESS_SERVICES", "TECH_SOFTWARE_SERVICES"):
        customers = payload.get("named_customers", [])
        return f"{len(customers)} customers; top: " + ", ".join(
            f"{c.get('name','?')}({c.get('revenue_pct','?')}%)" for c in customers[:3])
    if cluster == "COMMUNICATIONS":
        kpis = payload.get("kpis", [])
        return "; ".join(f"{k.get('metric')}: {k.get('value_latest')} (YoY {k.get('yoy_change_pct')}%)"
                         for k in kpis[:3])
    return f"{len(payload)} keys"


if __name__ == "__main__":
    main()
