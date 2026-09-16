"""IJR Phase 5 — honesty-only backtest.

Separates HONESTY signals (claim vs canonical-authority divergence) from
DISTRESS signals (financial-impairment factors). Backtests using only
honesty signals.

HONESTY MODULES (in our codebase)
  External canonical authorities that adjudicate company claims:
    fdic_call_reports          (banks: deposit/NPL/ROA claims)
    finra_brokercheck          (broker-dealers: regulatory standing)
    openfda_approved_drugs     (drug pipeline claims)
    openfda_inspection_*       (manufacturing-quality claims)
    orange_book_loe            (patent moat claims)
    clinical_trials            (trial pipeline claims)
    cms_cost_reports           (healthcare margin claims)
    cms_hcris_facility_search  (same — via facility-name search)
    usaspending_federal_presence (federal revenue claims)
    pentagon_jbook             (DoD program funding claims)
    epa_emissions, epa_frs     (environmental footprint claims)
    nhtsa_manufacturer         (auto-related claims)
    fmcsa                      (trucking safety claims)
    google_patents, uspto_odp  (IP moat claims)
    acq_coherence              (M&A narrative coherence)
    counterparty_reciprocity   (named counterparty cross-check)
    revenue_concentration      (customer-diversification claim)
    tenant_credit_watch        (REIT tenant-quality claim)
    bts_airline_metrics        (airline KPI claims)
    fcc_form_477               (cable subscriber claims)
    nasa_ntrs                  (aerospace research claims)
    sam_entity                 (federal contractor standing)
    megacap_namecheck          (megacap-customer claims)

  LLM-extract honesty-adjacent (extracts the CLAIM; the heuristic
  classifier flags concentration / KPI decline as catastrophe-relevant):
    llm_real_estate_extract
    llm_communications_extract
    llm_business_services_extract
    llm_tech_software_services_extract
    llm_healthcare_pharma_extract

DISTRESS MODULES (EXCLUDED from this backtest)
    filing_timeliness          (operational discipline)
    mw_lifecycle               (self-disclosed weakness)
    going_concern_detector     (auditor self-disclosure)
    auditor_change_tracker     (governance flag)
    lender_concession          (self-disclosed financial stress)
    insider_buy_timing         (behavior signal)
    insider_vs_calendar        (behavior signal)
    working_capital_drift      (Sloan accruals factor)
    runway_calculator          (Altman-Z-adjacent)
    share_count_drift          (Quality-Minus-Junk factor)
    rpo_drift                  (bookings quality)
    iborrow                    (market sentiment)
    osha_establishments        (worker-safety distress)
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict

HERE = Path(__file__).parent
DATA = HERE / "data" / "_ijr_manifest"

HONESTY_MODULES = {
    # Canonical-authority cross-checks
    "fdic_call_reports", "finra_brokercheck",
    "openfda_approved_drugs", "openfda_inspection_drug",
    "openfda_inspection_food", "openfda_inspection_device",
    "openfda_inspection_supp", "openfda_inspection_hsvc",
    "orange_book_loe",
    "clinical_trials",
    "cms_cost_reports", "cms_hcris_facility_search",
    "usaspending_federal_presence", "pentagon_jbook",
    "ic_contracting_proxy",
    "epa_emissions", "epa_frs",
    "nhtsa_manufacturer", "fmcsa",
    "google_patents", "uspto_odp",
    "acq_coherence", "counterparty_reciprocity",
    "revenue_concentration", "tenant_credit_watch",
    "bts_airline_metrics", "fcc_form_477",
    "nasa_ntrs", "sam_entity",
    "megacap_namecheck",
    "export_control_check",
    # LLM-extract (honesty-adjacent — extracts the claim itself)
    "llm_real_estate_extract", "llm_communications_extract",
    "llm_business_services_extract", "llm_tech_software_services_extract",
    "llm_healthcare_pharma_extract", "llm_healthcare_services_extract",
}

DISTRESS_MODULES = {
    "filing_timeliness", "mw_lifecycle", "going_concern_detector",
    "auditor_change_tracker", "lender_concession",
    "insider_buy_timing", "insider_vs_calendar",
    "working_capital_drift", "runway_calculator", "share_count_drift",
    "rpo_drift", "iborrow", "osha_establishments",
}

SEV_W = {"PASS": 0, "UNVERIFIABLE": 0, "MODERATE_UNDERDELIVERY": 1,
         "SEVERE_UNDERDELIVERY": 2, "RED_FLAG_NEGATIVE": 3}


def _load_all_tuples() -> dict:
    """Merge RFM tuples across Phase 1, 2, 2.5, 4 for each ticker."""
    out: dict[str, dict] = {}
    # Phase 1 — universal battery (mostly distress; only ~3 honesty if we include filing_timeliness etc.)
    p1 = json.loads((DATA / "phase1_scores.json").read_text())["scores"]
    for tk, s in p1.items():
        out[tk] = {
            "cik": s.get("cik"),
            "cluster": s.get("cluster"),
            "tuples": list(s.get("rfm_tuples") or []),
        }
    # Phase 2 — cohort-conditional (openfda, orange_book, epa, osha, nhtsa)
    try:
        p2 = json.loads((DATA / "phase2_scores.json").read_text())["scores"]
        for tk, s in p2.items():
            if s.get("skipped"): continue
            d = out.setdefault(tk, {"cik": s.get("cik"), "cluster": s.get("cluster"), "tuples": []})
            d["tuples"].extend(s.get("p2_tuples", []) or [])
    except FileNotFoundError:
        pass
    # Phase 2.5 — LLM extracts
    try:
        p25 = json.loads((DATA / "phase25_scores.json").read_text())["scores"]
        for tk, s in p25.items():
            if "error" in s: continue
            sig = s.get("llm_signal"); sev = s.get("llm_severity")
            if not sig or not sev: continue
            d = out.setdefault(tk, {"cik": s.get("cik"), "cluster": s.get("cluster"), "tuples": []})
            cluster_lower = (d.get("cluster") or "unknown").lower()
            d["tuples"].append({
                "M_source": f"llm_{cluster_lower}_extract",
                "severity": sev,
                "direction": "negative" if sev not in ("PASS", "UNVERIFIABLE") else "positive",
                "signal": sig,
            })
    except FileNotFoundError:
        pass
    # Phase 4 — cohort-canonical authorities (fdic, usaspending, jbook, cms)
    try:
        p4 = json.loads((DATA / "phase4_cohort_scores.json").read_text())["scores"]
        for tk, s in p4.items():
            d = out.setdefault(tk, {"cik": s.get("cik"), "cluster": s.get("cohort"), "tuples": []})
            d["tuples"].extend(s.get("p4_new_tuples", []) or [])
    except FileNotFoundError:
        pass
    return out


def _honesty_only_score(tuples: list[dict]) -> tuple[int, list[str]]:
    """Return (max severity weight from HONESTY modules only, list of fires)."""
    max_w = 0
    fires = []
    for t in tuples:
        ms = t.get("M_source")
        if ms not in HONESTY_MODULES:
            continue
        sev = t.get("severity") or "PASS"
        w = SEV_W.get(sev, 0)
        if w > 0:
            fires.append(f"{ms}={t.get('signal','?')}({sev})")
        if w > max_w:
            max_w = w
    return max_w, fires


def main():
    merged = _load_all_tuples()
    returns = json.loads((DATA / "forward_returns.json").read_text())
    holdings_raw = json.loads((DATA / "ijr_holdings_2024_06_30.json").read_text())
    if isinstance(holdings_raw, dict) and "holdings" in holdings_raw:
        holdings_raw = holdings_raw["holdings"]
    holdings = {h["ticker"]: h for h in holdings_raw if h.get("ticker")}
    r24 = returns.get("returns_24m", {})

    # Build per-ticker rows
    rows = []
    for tk, d in merged.items():
        ret = r24.get(tk)
        if ret is None: continue
        max_honesty, fires = _honesty_only_score(d["tuples"])
        n_honesty_modules_ran = sum(1 for t in d["tuples"] if t.get("M_source") in HONESTY_MODULES)
        rows.append({
            "ticker": tk, "ret_24m": ret, "is_cat": ret <= -0.30,
            "cluster": d.get("cluster"),
            "value_usd": holdings.get(tk, {}).get("value_usd"),
            "honesty_max": max_honesty,
            "honesty_fires": fires,
            "n_honesty_evaluated": n_honesty_modules_ran,
        })

    total = sum(1 for r in rows)
    n_cat = sum(1 for r in rows if r["is_cat"])
    n_with_honesty_eval = sum(1 for r in rows if r["n_honesty_evaluated"] > 0)
    n_with_honesty_fire = sum(1 for r in rows if r["honesty_max"] > 0)

    print("=" * 80)
    print("PHASE 5 — HONESTY-ONLY BACKTEST")
    print("=" * 80)
    print(f"Universe with returns: {total}")
    print(f"Actual catastrophes:    {n_cat} ({100*n_cat/total:.1f}%)")
    print(f"Names with ≥1 honesty module evaluated:  {n_with_honesty_eval}")
    print(f"Names with ≥1 honesty signal firing:     {n_with_honesty_fire}")

    # Catastrophe coverage by honesty
    n_cat_with_eval = sum(1 for r in rows if r["is_cat"] and r["n_honesty_evaluated"] > 0)
    print(f"\nOf {n_cat} catastrophes:")
    print(f"  {n_cat_with_eval} had at least one honesty module evaluated")
    print(f"  {n_cat - n_cat_with_eval} had NO honesty module run (uncovered)")

    # Precision / recall at various honesty severity thresholds
    print(f"\n{'thresh':>8} {'n_flagged':>10} {'n_caught':>10} {'precision':>10} {'recall':>10} {'cat covered':>14}")
    for thresh in (1, 2, 3):
        flagged = [r for r in rows if r["honesty_max"] >= thresh]
        caught = [r for r in flagged if r["is_cat"]]
        prec = len(caught)/len(flagged) if flagged else 0
        recall_overall = len(caught) / n_cat if n_cat else 0
        # Among catastrophes where honesty was evaluated:
        cat_evaluated = [r for r in rows if r["is_cat"] and r["n_honesty_evaluated"] > 0]
        recall_evaluated = len(caught) / len(cat_evaluated) if cat_evaluated else 0
        label = {1: "MODERATE+", 2: "SEVERE+", 3: "RED only"}[thresh]
        print(f"{label:>8} {len(flagged):>10} {len(caught):>10} "
              f"{prec*100:>9.1f}% {recall_overall*100:>9.1f}% "
              f"{recall_evaluated*100:>13.1f}% (of evaluated)")

    # Basket returns
    ijr_24m = returns.get("ijr_24m", 0)
    print(f"\nIJR benchmark 24m: {ijr_24m*100:+.2f}%")
    print(f"Universe-EW with returns: {sum(r['ret_24m'] for r in rows)/total*100:+.2f}%")

    print(f"\nExclusion alpha (drop names where any honesty signal fires ≥ thresh):")
    print(f"{'thresh':>10} {'n_kept':>8} {'kept_EW':>10} {'alpha_vs_IJR':>14} {'cat_caught':>12}")
    for thresh in (1, 2, 3):
        kept = [r for r in rows if r["honesty_max"] < thresh]
        flagged = [r for r in rows if r["honesty_max"] >= thresh]
        if not kept: continue
        kept_ret = sum(r["ret_24m"] for r in kept) / len(kept)
        cat_flagged = sum(1 for r in flagged if r["is_cat"])
        label = {1: "MODERATE+", 2: "SEVERE+", 3: "RED only"}[thresh]
        print(f"{label:>10} {len(kept):>8} {kept_ret*100:>+9.2f}% {(kept_ret-ijr_24m)*100:>+13.2f}pp "
              f"{cat_flagged:>11}")

    print(f"\nLong-only alpha (BUY names where honesty signal fires — 'we trust the catches'):")
    print(f"{'thresh':>10} {'n_long':>8} {'long_EW':>10} {'alpha_vs_IJR':>14} {'cat_in_basket':>14}")
    for thresh in (1, 2, 3):
        long_basket = [r for r in rows if r["honesty_max"] >= thresh]
        if not long_basket: continue
        long_ret = sum(r["ret_24m"] for r in long_basket) / len(long_basket)
        cat_in = sum(1 for r in long_basket if r["is_cat"])
        label = {1: "MODERATE+", 2: "SEVERE+", 3: "RED only"}[thresh]
        print(f"{label:>10} {len(long_basket):>8} {long_ret*100:>+9.2f}% {(long_ret-ijr_24m)*100:>+13.2f}pp "
              f"{cat_in:>13}")

    # Per-cluster honesty-only coverage
    print(f"\nPer-cluster honesty-evaluation coverage:")
    by_c = defaultdict(list)
    for r in rows:
        by_c[r["cluster"] or "UNKNOWN"].append(r)
    print(f"{'cluster':<28} {'n':>4} {'cat':>4} {'evaluated':>10} {'fired':>6}")
    for c in sorted(by_c, key=lambda x: -len(by_c[x])):
        members = by_c[c]
        eval_n = sum(1 for r in members if r["n_honesty_evaluated"] > 0)
        fire_n = sum(1 for r in members if r["honesty_max"] > 0)
        cat_n = sum(1 for r in members if r["is_cat"])
        print(f"{c:<28} {len(members):>4} {cat_n:>4} {eval_n:>10} {fire_n:>6}")


if __name__ == "__main__":
    main()
