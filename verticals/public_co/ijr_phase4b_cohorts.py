"""Phase 4b — run cohort-specific canonical-authority m-sources.

For each of (banks, pharma, devices, healthcare_services), layer the
cluster-canonical f(M) on top of the existing Phase 1 universal battery
results, recompute composite, and report.

DISPATCH (cluster-canonical f(M) by cohort)

  banks               → fdic_call_reports.query_bank_credit_history (name lookup)
  pharma              → openfda.query_approved_drugs (drug pipeline)
                      + openfda.query_inspection_history (drug recalls)
                      + orange_book.query_orange_book (LOE)
                      + clinical_trials.query_by_lead_sponsor (pipeline)
  devices             → openfda.query_inspection_history (device recalls)
  healthcare_services → openfda.query_inspection_history (drug + food)

Defense (n=8, 0 catastrophes) is skipped — no statistical power.

OUTPUT
  data/_ijr_manifest/phase4_cohort_scores.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Callable

from .m_sources import (
    composite_recompute,
    openfda,
    orange_book,
    clinical_trials,
    fdic_call_reports,
    usaspending,
    pentagon_jbook,
    cms_cost_reports,
    llm_10k_extract,
)
from .ijr_universe_runner import _to_rfm_tuple
from .ijr_phase2_runner import _clean_company_name

HERE = Path(__file__).parent
DATA = HERE / "data" / "_ijr_manifest"
COHORTS = DATA / "phase4_cohorts.json"
P1_SCORES = DATA / "phase1_scores.json"
OUT = DATA / "phase4_cohort_scores.json"


_BANK_HOLDING_SUFFIXES = (
    " Bancorp", " Bancshares", " Bankshares",
    " Financial Group", " Financial Corp", " Financial Corporation",
    " Financial", " Holdings", " Holding Company", " Holding",
    " National Corp", " National Corporation",
)


def _bank_name_variants(name: str) -> list[str]:
    """Generate candidate FDIC bank-name variants from an IJR holding-company name."""
    n = (name or "").strip()
    variants = [n]
    # Strip address/state suffixes like "/Los Angeles CA"
    if "/" in n:
        variants.append(n.split("/", 1)[0].strip())
    # Strip bank holding-company suffixes
    for cand in list(variants):
        for suf in _BANK_HOLDING_SUFFIXES:
            if cand.lower().endswith(suf.lower()):
                stripped = cand[: -len(suf)].strip().rstrip(",")
                if stripped and stripped not in variants:
                    variants.append(stripped)
    # First meaningful token (e.g., "Cathay" from "Cathay General Bancorp")
    tokens = [t for t in (variants[0] or "").split()
              if t.lower() not in ("the", "of", "&", "and")]
    if tokens:
        first = tokens[0]
        if first not in variants and len(first) >= 4:
            variants.append(first)
    # Dedupe preserving order
    seen, out = set(), []
    for v in variants:
        if v and v not in seen:
            seen.add(v); out.append(v)
    return out


def _wrap_fdic(name: str, cutoff: str) -> dict:
    """FDIC Call Report distress detector with multi-variant name resolution.

    Tries: cleaned name → name with bank holding suffixes stripped →
    first-token fallback. This resolves "Cathay General Bancorp" →
    "Cathay" → "Cathay Bank".
    """
    variants = _bank_name_variants(name)
    r = None
    matched_name = None
    last_err = None
    for variant in variants:
        try:
            r = fdic_call_reports.query_bank_credit_history(bank_name=variant, quarters=16)
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            continue
        if "error" not in r and r.get("quarters_pulled"):
            matched_name = variant
            break
        last_err = r.get("error") if isinstance(r, dict) else "no_data"
    if not matched_name:
        return {"signal": "UNVERIFIABLE", "severity": "UNVERIFIABLE",
                "direction": "neutral",
                "_note": f"No FDIC match for variants {variants[:3]}; err={last_err}"}

    quarters = r.get("quarters_pulled") or []
    if len(quarters) < 4:
        return {"signal": "FDIC_NOT_FOUND" if not quarters else "FDIC_SPARSE",
                "severity": "UNVERIFIABLE", "direction": "neutral",
                "_note": f"Only {len(quarters)} quarters of Call Report data"}

    # Filter to pre-cutoff and sort ascending by REPDTE
    from datetime import date as _date
    try:
        cd = _date.fromisoformat(cutoff[:10])
    except Exception:
        cd = None
    def _qdt(q):
        s = str(q.get("REPDTE",""))
        if len(s) == 8:
            return _date(int(s[:4]), int(s[4:6]), int(s[6:8]))
        return None
    quarters = [q for q in quarters if _qdt(q) and (cd is None or _qdt(q) <= cd)]
    quarters.sort(key=_qdt)
    if len(quarters) < 4:
        return {"signal": "FDIC_PRE_CUTOFF_SPARSE",
                "severity": "UNVERIFIABLE", "direction": "neutral",
                "_note": f"{len(quarters)} quarters pre-cutoff"}

    # Latest vs 4 quarters prior
    latest = quarters[-1]
    prior = quarters[-5] if len(quarters) >= 5 else quarters[0]

    def _safe_ratio(num, denom):
        try:
            n, d = float(num), float(denom)
            return n / d if d else None
        except (TypeError, ValueError):
            return None

    # Use NCLNLS (TOTAL nonaccrual loans, all loan categories) / ASSET
    # as a denominator-stable distressed-loan share. NCLNLS/LNCON would
    # be wrong because LNCON is consumer-only loans (subset).
    nplshare_now  = _safe_ratio(latest.get("NCLNLS"), latest.get("ASSET"))
    nplshare_prev = _safe_ratio(prior.get("NCLNLS"),  prior.get("ASSET"))
    roa_now  = latest.get("ROAQ")
    roa_prev = prior.get("ROAQ")
    deps_now  = latest.get("DEPDOM") or 0
    deps_prev = prior.get("DEPDOM") or 0

    flags = []
    severity = "PASS"
    direction = "positive"

    # Nonaccrual loans / assets rising > 50 bps YoY = distress
    if nplshare_now is not None and nplshare_prev is not None:
        delta_bps = (nplshare_now - nplshare_prev) * 10000
        if delta_bps >= 100:
            flags.append(f"NPL share +{delta_bps:.0f}bps YoY")
            severity = "SEVERE_UNDERDELIVERY"
            direction = "negative"
        elif delta_bps >= 50:
            flags.append(f"NPL share +{delta_bps:.0f}bps YoY")
            severity = "MODERATE_UNDERDELIVERY"
            direction = "negative"

    # ROA collapse YoY
    if roa_now is not None and roa_prev is not None:
        try:
            roa_delta = float(roa_now) - float(roa_prev)
            if roa_delta <= -0.5 and float(roa_now) < 0.5:
                flags.append(f"ROA {roa_prev:.2f}→{roa_now:.2f}")
                if severity == "PASS":
                    severity = "MODERATE_UNDERDELIVERY"
                direction = "negative"
            if float(roa_now) < 0:
                flags.append(f"ROA NEGATIVE ({roa_now:.2f})")
                severity = "SEVERE_UNDERDELIVERY"
                direction = "negative"
        except (TypeError, ValueError):
            pass

    # Deposit flight > 5% YoY = bank-run risk
    if deps_prev > 0:
        dep_yoy = (deps_now - deps_prev) / deps_prev
        if dep_yoy <= -0.10:
            flags.append(f"Deposits {dep_yoy*100:+.1f}% YoY")
            severity = "SEVERE_UNDERDELIVERY"
            direction = "negative"
        elif dep_yoy <= -0.05:
            flags.append(f"Deposits {dep_yoy*100:+.1f}% YoY")
            if severity == "PASS":
                severity = "MODERATE_UNDERDELIVERY"
            direction = "negative"

    if flags:
        return {"signal": "FDIC_DISTRESS", "severity": severity,
                "direction": direction, "_note": "; ".join(flags),
                "_metrics": {"nplshare_now_bps": nplshare_now*10000 if nplshare_now else None,
                             "roa_now": roa_now,
                             "dep_yoy_pct": (deps_now-deps_prev)/deps_prev*100 if deps_prev > 0 else None}}

    return {"signal": "FDIC_CLEAN", "severity": "PASS", "direction": "positive",
            "_note": (f"Stable: NPL-share {nplshare_now*10000:.0f}bps "
                      f"ROA {roa_now} dep YoY {(deps_now-deps_prev)/max(1,deps_prev)*100:+.1f}%"
                      if nplshare_now is not None else "Stable; partial fields")}


def _wrap_usaspending(name: str, cutoff: str) -> dict:
    """Federal contract / grant presence — verifies federal-revenue claims."""
    try:
        r = usaspending.query_federal_presence(name_variants=name,
                                                end_date=cutoff)
    except Exception as e:
        return {"signal": "ERROR", "_note": f"{type(e).__name__}: {e}"}
    sig = r.get("signal")
    if sig is None:
        return {"signal": "UNVERIFIABLE", "severity": "UNVERIFIABLE",
                "direction": "neutral", "_note": "no signal field"}
    severity_map = {
        "INFLATION_SUSPECT":      "SEVERE_UNDERDELIVERY",
        "SUB_MATERIAL_FEDERAL":   "UNVERIFIABLE",
        "RECURRING_FEDERAL":      "PASS",
        "NEW_FEDERAL_AWARDS":     "PASS",
        "NOT_FEDERAL":            "UNVERIFIABLE",
    }
    direction_map = {
        "RECURRING_FEDERAL":      "positive",
        "NEW_FEDERAL_AWARDS":     "positive",
        "INFLATION_SUSPECT":      "negative",
    }
    return {
        "signal": sig,
        "severity": severity_map.get(sig, "UNVERIFIABLE"),
        "direction": direction_map.get(sig, "neutral"),
        "_note": f"Federal presence={sig}, total={r.get('total_obligated_usd','?')}",
    }


def _wrap_jbook(name: str, cutoff: str) -> dict:
    """Pentagon J-Book contractor lookup — does the DoD actually fund this name?"""
    try:
        r = pentagon_jbook.query_program_funding(contractor_name=name,
                                                  cutoff_date=cutoff)
    except Exception as e:
        return {"signal": "ERROR", "_note": f"{type(e).__name__}: {e}"}
    sig = r.get("signal", "NOT_FOUND")
    severity_map = {
        "FOUND_PROGRAM":      "PASS",
        "GROWING_PROGRAM":    "PASS",
        "DECLINING_PROGRAM":  "MODERATE_UNDERDELIVERY",
        "TERMINATED_PROGRAM": "SEVERE_UNDERDELIVERY",
        "NOT_FOUND":          "UNVERIFIABLE",
    }
    direction_map = {
        "FOUND_PROGRAM":      "positive",
        "GROWING_PROGRAM":    "positive",
        "DECLINING_PROGRAM":  "negative",
        "TERMINATED_PROGRAM": "negative",
    }
    return {
        "signal": sig,
        "severity": severity_map.get(sig, "UNVERIFIABLE"),
        "direction": direction_map.get(sig, "neutral"),
        "_note": r.get("_note", "")[:200],
    }


def _wrap_cms_hsvc_llm(name: str, cik: str, cutoff: str) -> dict:
    """First try to extract CCNs from the 10-K via LLM. If CCNs found,
    query cms_cost_reports directly. Otherwise fall back to facility-name
    substring search.
    """
    if not cik:
        return _wrap_cms_hsvc_search(name, cutoff)
    try:
        ext = llm_10k_extract.extract(
            ticker="_hsvc_" + name.replace(" ", "_"),
            cik=cik, cluster="HEALTHCARE_SERVICES", cutoff_date=cutoff,
        )
    except Exception:
        return _wrap_cms_hsvc_search(name, cutoff)
    if "error" in ext:
        return _wrap_cms_hsvc_search(name, cutoff)
    payload = ext.get("payload", {}) or {}
    facilities = payload.get("facilities") or []
    # Collect CCNs by facility_type
    by_type: dict[str, list[str]] = {}
    for f in facilities:
        ccn = f.get("ccn")
        ft  = (f.get("facility_type") or "snf").lower()
        if ccn:
            by_type.setdefault(ft, []).append(str(ccn).zfill(6))
    if not by_type:
        # No CCNs in 10-K — fall back to facility-name search
        return _wrap_cms_hsvc_search(name, cutoff)
    # Try each facility_type in size order
    types_by_size = sorted(by_type, key=lambda k: -len(by_type[k]))
    for ft in types_by_size:
        ccns = list(set(by_type[ft]))[:50]
        try:
            res = cms_cost_reports.query_operator_margin(
                operator_name=name, ccns=ccns,
                cutoff_date=cutoff, facility_type=ft)
        except Exception:
            continue
        if res.get("signal") and res.get("severity"):
            return {
                "signal":   f"CMS_{ft.upper()}_{res['signal']}",
                "severity": res["severity"],
                "direction": res.get("direction", "neutral"),
                "_note":    (res.get("_note", "") + f" (LLM-extracted {len(ccns)} CCNs, {ft})")[:300],
            }
    return _wrap_cms_hsvc_search(name, cutoff)


def _wrap_cms_hsvc_search(name: str, cutoff: str) -> dict:
    """CMS HCRIS by facility-name substring (no curated CCN list).

    Searches Skilled Nursing Facility + Hospital cost reports by Facility
    Name containing the operator's name. Imperfect (operators run
    facilities under sub-LLC names) but better than nothing.
    """
    # Try SNF first, then hospital
    import httpx
    headers = {"User-Agent": "Signal OS Research backtest@signalos.local"}
    matched_ccns = []
    for ftype, uuid in cms_cost_reports.DATASETS.items():
        if ftype not in ("snf", "hospital", "home_health"):
            continue
        try:
            with httpx.Client(headers=headers, timeout=45) as c:
                r = c.get(f"https://data.cms.gov/data-api/v1/dataset/{uuid}/data",
                          params={"filter[Facility Name][condition][path]": "Facility Name",
                                  "filter[Facility Name][condition][operator]": "CONTAINS",
                                  "filter[Facility Name][condition][value]": name,
                                  "size": 100})
                if r.status_code != 200:
                    continue
                rows = r.json()
                for row in rows or []:
                    ccn = row.get("Provider CCN") or row.get("CCN")
                    if ccn:
                        matched_ccns.append((str(ccn), ftype, row))
        except Exception:
            continue
    if not matched_ccns:
        return {"signal": "NO_CMS_MATCH", "severity": "UNVERIFIABLE",
                "direction": "neutral",
                "_note": f"No CMS HCRIS facility names contain '{name}'."}

    # Get unique CCNs by facility type
    by_type: dict[str, list[str]] = {}
    for ccn, ftype, _ in matched_ccns:
        by_type.setdefault(ftype, []).append(ccn)
    # Try in order of largest match (most CCNs found for that facility type)
    types_by_size = sorted(by_type, key=lambda k: -len(by_type[k]))
    best = None
    for ftype in types_by_size:
        ccns_unique = list(set(by_type[ftype]))[:50]
        try:
            res = cms_cost_reports.query_operator_margin(
                operator_name=name, ccns=ccns_unique,
                cutoff_date=cutoff, facility_type=ftype)
            sig = res.get("signal")
            sev = res.get("severity")
            # Prefer first non-UNVERIFIABLE result
            if sig and sev and sev != "UNVERIFIABLE":
                return {"signal": f"CMS_{ftype.upper()}_{sig}",
                        "severity": sev, "direction": res.get("direction","neutral"),
                        "_note": res.get("_note", "")[:300]
                                  + f" ({len(ccns_unique)} CCNs, {ftype})"}
            if best is None:
                best = (ftype, res)
        except Exception:
            continue
    if best:
        ftype, res = best
        return {"signal": f"CMS_{ftype.upper()}_{res.get('signal','?')}",
                "severity": res.get("severity","UNVERIFIABLE"),
                "direction": res.get("direction","neutral"),
                "_note": (res.get("_note","")[:200]
                          + f" ({len(by_type[ftype])} {ftype} CCNs)")}
    return {"signal": "CMS_AGG_FAILED", "severity": "UNVERIFIABLE",
            "direction": "neutral",
            "_note": f"Found {len(matched_ccns)} matching CCNs but aggregation failed."}


def _wrap_openfda_approved(name: str, cutoff: str) -> dict:
    """Pipeline presence check."""
    try:
        r = openfda.query_approved_drugs(name)
    except Exception as e:
        return {"signal": "ERROR", "_note": str(e)}
    n = r.get("n_approved_applications", 0) or 0
    if n >= 5:
        return {"signal": "PIPELINE_BROAD", "severity": "PASS",
                "direction": "positive", "_note": f"{n} approved applications."}
    if n >= 1:
        return {"signal": "PIPELINE_NARROW", "severity": "MODERATE_UNDERDELIVERY",
                "direction": "negative", "_note": f"Only {n} approved drug(s) — concentration risk."}
    return {"signal": "NO_APPROVED_DRUGS", "severity": "UNVERIFIABLE",
            "direction": "neutral",
            "_note": "Likely dev-stage or biologic-only (Purple Book)."}


def _wrap_openfda_inspection(endpoints):
    def _w(name: str, cutoff: str) -> dict:
        return openfda.query_inspection_history(name, cutoff, endpoints=endpoints)
    return _w


def _wrap_orange_book(name: str, cutoff: str) -> dict:
    return orange_book.query_orange_book(name, cutoff)


def _wrap_clinical_trials(name: str, cutoff: str) -> dict:
    try:
        r = clinical_trials.query_by_lead_sponsor(name, cutoff_date=cutoff)
    except Exception as e:
        return {"signal": "ERROR", "_note": str(e)}
    n = r.get("n_studies_pre_cutoff", 0) or 0
    phases = r.get("phase_counts", {})
    phase3_plus = sum(v for k, v in phases.items() if "PHASE3" in k.upper() or "PHASE4" in k.upper())
    if n == 0:
        return {"signal": "NO_CLINICAL_PRESENCE", "severity": "UNVERIFIABLE",
                "direction": "neutral"}
    if phase3_plus >= 3:
        return {"signal": "MATURE_PIPELINE", "severity": "PASS",
                "direction": "positive",
                "_note": f"{phase3_plus} Phase 3/4 studies (of {n} total)."}
    if n >= 5:
        return {"signal": "EARLY_PIPELINE", "severity": "PASS",
                "direction": "neutral",
                "_note": f"{n} studies, mostly early phase."}
    return {"signal": "THIN_PIPELINE", "severity": "MODERATE_UNDERDELIVERY",
            "direction": "negative",
            "_note": f"Only {n} CT.gov studies."}


COHORT_DISPATCH: dict[str, list[tuple[str, Callable[[str, str], dict]]]] = {
    "banks": [
        ("fdic_call_reports", _wrap_fdic),
    ],
    "defense": [
        ("usaspending_federal_presence", _wrap_usaspending),
        ("pentagon_jbook",               _wrap_jbook),
    ],
    "pharma": [
        ("openfda_approved_drugs",   _wrap_openfda_approved),
        ("openfda_inspection_drug",  _wrap_openfda_inspection(("drug",))),
        ("orange_book_loe",          _wrap_orange_book),
        ("clinical_trials",          _wrap_clinical_trials),
    ],
    "devices": [
        ("openfda_inspection_device", _wrap_openfda_inspection(("device",))),
    ],
    "healthcare_services": [
        ("cms_hcris_facility_search", _wrap_cms_hsvc_search),
    ],
}


def run_one(name: str, cohort: str, cutoff: str, *, cik: str | None = None) -> list[dict]:
    modules = COHORT_DISPATCH.get(cohort, [])
    cleaned = _clean_company_name(name)
    out = []
    for m_name, fn in modules:
        try:
            # CMS HCRIS LLM-augmented wrapper needs CIK; all others take (name, cutoff)
            if m_name == "cms_hcris_facility_search" and cik:
                res = _wrap_cms_hsvc_llm(cleaned, cik, cutoff)
            else:
                res = fn(cleaned, cutoff)
        except Exception as e:
            res = {"signal": "ERROR", "_note": f"{type(e).__name__}: {e}"}
        out.append(_to_rfm_tuple(m_name, res))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff", required=True)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    cohorts = json.loads(COHORTS.read_text())
    p1 = json.loads(P1_SCORES.read_text())["scores"]

    out_scores: dict[str, dict] = {}
    lock = Lock()
    t_start = time.time()

    targets = []
    for cohort, items in cohorts.items():
        if cohort not in COHORT_DISPATCH:
            print(f"Skipping cohort {cohort} (no dispatch)", file=sys.stderr)
            continue
        for it in items:
            targets.append({"ticker": it["ticker"], "cik": it.get("cik"),
                             "name": it.get("name"), "cohort": cohort})
    print(f"Running Phase 4b on {len(targets)} cohort members "
          f"({args.workers} workers)...", file=sys.stderr)

    def _worker(t: dict):
        try:
            new_tuples = run_one(t["name"], t["cohort"], args.cutoff, cik=t.get("cik"))
        except Exception as e:
            return t["ticker"], {"error": str(e), "cohort": t["cohort"]}
        ticker = t["ticker"]
        p1_entry = p1.get(ticker, {})
        combined = (p1_entry.get("rfm_tuples") or []) + new_tuples
        pilot = {"ticker": ticker, "cutoff": args.cutoff, "rfm_tuples": combined}
        comp = composite_recompute.recompute(pilot)
        return ticker, {
            "cohort": t["cohort"],
            "cik": p1_entry.get("cik"),
            "name": t.get("name"),
            "p1_distress": p1_entry.get("distress_composite"),
            "p4_distress": comp.get("distress_composite"),
            "p4_recovery": comp.get("recovery_composite"),
            "p4_tier": comp.get("tier"),
            "p4_n_formal": comp.get("n_formal_tuples"),
            "p4_new_tuples": new_tuples,
        }

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(_worker, t): t for t in targets}
        done = 0
        for fut in as_completed(futures):
            tk, payload = fut.result()
            with lock:
                out_scores[tk] = payload
            done += 1
            if done % 25 == 0:
                print(f"  {done}/{len(targets)} done in {(time.time()-t_start)/60:.1f}m",
                      file=sys.stderr)

    OUT.write_text(json.dumps({
        "cutoff_date": args.cutoff,
        "n_scored": len(out_scores),
        "scores": out_scores,
    }, indent=2, default=str))
    print(f"\nDone. {len(out_scores)} scored in {(time.time()-t_start)/60:.1f}m → {OUT}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
