"""Phase 4c — cohort basket returns vs sector ETFs.

For each cohort:
  1. Baseline (cohort-EW): buy all IJR names in cohort equal-weight
  2. Distress exclusion: drop names with p4_distress >= 0.20
  3. Distress exclusion (strict): drop names with p4_distress >= 0.10
  4. Inversion (Phase 3d): buy distressed names, exclude runway_red

Compare each to the cohort's sector ETF benchmark and report:
  - n names in basket
  - basket EW return
  - alpha vs sector ETF
  - catastrophe precision/recall

Skip cohorts where N is too small (defense=8, 0 cat) or where signals
don't fire (banks=58, 0 cat).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

HERE = Path(__file__).parent
DATA = HERE / "data" / "_ijr_manifest"

ETF_BENCH = {
    "banks":              {"primary": "KRE",  "secondary": "KBE"},
    "defense":            {"primary": "XAR",  "secondary": "ITA"},
    "pharma":             {"primary": "XPH",  "secondary": "IBB"},
    "devices":            {"primary": "XHE",  "secondary": "PSCH"},
    "healthcare_services":{"primary": "XHS",  "secondary": "PSCH"},
}


def main():
    cohorts = json.loads((DATA / "phase4_cohorts.json").read_text())
    p4 = json.loads((DATA / "phase4_cohort_scores.json").read_text())["scores"]
    p1 = json.loads((DATA / "phase1_scores.json").read_text())["scores"]
    returns = json.loads((DATA / "forward_returns.json").read_text())
    etfs = json.loads((DATA / "phase4_etf_benchmarks.json").read_text())
    r24 = returns["returns_24m"]

    for cohort, items in cohorts.items():
        bench_pri = ETF_BENCH.get(cohort, {}).get("primary")
        bench_sec = ETF_BENCH.get(cohort, {}).get("secondary")
        bench_pri_ret = etfs.get(bench_pri, {}).get("ret_24m") if bench_pri else None
        bench_sec_ret = etfs.get(bench_sec, {}).get("ret_24m") if bench_sec else None
        ijr_ret = etfs.get("IJR", {}).get("ret_24m", 0)

        print("=" * 80)
        print(f"COHORT: {cohort.upper()}  n_holdings={len(items)}")
        if bench_pri_ret is not None:
            print(f"  Primary benchmark: {bench_pri} 24m={bench_pri_ret*100:+.2f}%")
        if bench_sec_ret is not None:
            print(f"  Secondary benchmark: {bench_sec} 24m={bench_sec_ret*100:+.2f}%")
        print(f"  IJR reference: {ijr_ret*100:+.2f}%")
        print("=" * 80)

        # Build per-ticker record
        rows = []
        for it in items:
            t = it["ticker"]
            ret = r24.get(t)
            if ret is None:
                continue
            # Prefer phase 4 distress (includes cohort-specific signals)
            p4_entry = p4.get(t, {})
            p1_entry = p1.get(t, {})
            dist = p4_entry.get("p4_distress")
            if dist is None:
                dist = p1_entry.get("distress_composite") or 0
            # Check for runway_red signal (in either tuples)
            has_runway_red = False
            all_tuples = list(p1_entry.get("rfm_tuples") or []) + list(p4_entry.get("p4_new_tuples") or [])
            for tup in all_tuples:
                if tup.get("M_source") == "runway_calculator" and tup.get("signal") == "RED":
                    has_runway_red = True
            # Check for any cluster-canonical signal firing at moderate+
            has_canonical_fire = False
            for tup in p4_entry.get("p4_new_tuples") or []:
                sev = tup.get("severity")
                if sev in ("MODERATE_UNDERDELIVERY", "SEVERE_UNDERDELIVERY", "RED_FLAG_NEGATIVE"):
                    has_canonical_fire = True
            rows.append({
                "ticker": t, "ret": ret, "dist": dist,
                "is_cat": ret <= -0.30,
                "has_runway_red": has_runway_red,
                "has_canonical_fire": has_canonical_fire,
            })

        if not rows:
            print("  No rows. Skipping.\n")
            continue

        n = len(rows)
        n_cat = sum(1 for r in rows if r["is_cat"])
        base_ew = sum(r["ret"] for r in rows) / n

        print(f"  Universe-EW: n={n}, catastrophes={n_cat} ({100*n_cat/n:.1f}%), "
              f"return={base_ew*100:+.2f}%, "
              f"alpha vs {bench_pri}={(base_ew - bench_pri_ret)*100:+.2f}pp")

        # Strategy 1: Drop dist >= 0.20
        for thresh in (0.20, 0.10):
            kept = [r for r in rows if r["dist"] < thresh]
            dropped = [r for r in rows if r["dist"] >= thresh]
            if not kept: continue
            ret_kept = sum(r["ret"] for r in kept) / len(kept)
            cat_dropped = sum(1 for r in dropped if r["is_cat"])
            cat_kept = sum(1 for r in kept if r["is_cat"])
            print(f"\n  STRATEGY: Drop dist >= {thresh:.2f}")
            print(f"    Kept: n={len(kept)}, return={ret_kept*100:+.2f}%, "
                  f"alpha vs {bench_pri}={(ret_kept - bench_pri_ret)*100:+.2f}pp")
            print(f"    Dropped: n={len(dropped)} ({cat_dropped}/{n_cat} catastrophes "
                  f"= {100*cat_dropped/max(1,n_cat):.0f}% recall, "
                  f"{100*cat_dropped/max(1,len(dropped)):.0f}% precision)")

        # Strategy 2: Inversion — buy any distressed name (any module fired), exclude runway_red
        distressed = [r for r in rows if r["dist"] >= 0.10 or r["has_canonical_fire"]]
        inversion_kept = [r for r in distressed if not r["has_runway_red"]]
        if inversion_kept:
            ret_inv = sum(r["ret"] for r in inversion_kept) / len(inversion_kept)
            inv_cat = sum(1 for r in inversion_kept if r["is_cat"])
            print(f"\n  STRATEGY: Inversion (buy distressed pool, exclude runway_red)")
            print(f"    Distressed pool: n={len(distressed)}")
            print(f"    Inversion-kept: n={len(inversion_kept)}, "
                  f"catastrophes={inv_cat} ({100*inv_cat/len(inversion_kept):.0f}%)")
            print(f"    Return={ret_inv*100:+.2f}%, "
                  f"alpha vs {bench_pri}={(ret_inv - bench_pri_ret)*100:+.2f}pp")

        print()


if __name__ == "__main__":
    main()
