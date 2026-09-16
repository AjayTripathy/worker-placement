"""TIER-1 CONTROL 2 — channel ablation on the survivorship_2025_05 backtest.

The pilots' R/f/M tuples carry free-text M_source. Normalize into channel
families, then:

  DROP-ONE:  recompute the composite without family F -> re-tier -> LOOSE_LONG
             basket + NOT-SHORT exclusion basket (which channels carry alpha?)
  ONLY-ONE:  narrow detector framing — exclude any name where family F fires
             at SEVERE+ -> kept-basket alpha + catastrophe recall/precision
  NARROW-UNION: union of the highest-precision families vs the comprehensive
             composite (detector-composition doctrine test)

Writes: data/_backtest/tier1_controls/control2_ablation.json
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from tier1_step0_reproduce import load_rows, tier, SEV_W  # type: ignore

HERE = Path(__file__).parent
OUT = HERE / "data" / "_backtest" / "tier1_controls"
IJR = 0.2611

FAMILIES = [
    ("claim_evolution", ("claim_evolution", "cross-filing", "10-k vs", "vs q1", "claim evolution")),
    ("going_concern", ("going_concern",)),
    ("auditor", ("auditor", "attestation")),
    ("insider_form4", ("form4", "form 4", "insider")),
    ("external_mirror", ("edgar_fts", "mirror", "competitor", "usaspending", "openfda",
                         "supplier", "sector knowledge", "bls", "peer")),
    ("capital_action", ("dividend", "purchases of equity", "issuer purchases", "buyback",
                        "capital_action", "capital action", "repurchase")),
]


def family_of(t: dict) -> str:
    text = " ".join(str(t.get(k) or "") for k in ("M_source", "f")).lower()
    for fam, keys in FAMILIES:
        if any(k in text for k in keys):
            return fam
    return "filing_internal"


def composite(tuples):
    if not tuples:
        return None
    return sum(SEV_W.get(t.get("severity"), 0) for t in tuples) / len(tuples)


def basket_stats(rows, ijr=IJR):
    long_ = [r for r in rows if r["tier"] in ("STRICT_LONG", "LOOSE_LONG")]
    keep = [r for r in rows if r["tier"] != "SHORT"]
    cats = [r for r in rows if r["forward_return"] <= -0.40]
    cats_flagged = [r for r in cats if r["tier"] == "SHORT"]
    lm = statistics.mean(r["forward_return"] for r in long_) if long_ else None
    km = statistics.mean(r["forward_return"] for r in keep) if keep else None
    return {
        "n_universe": len(rows),
        "long_n": len(long_), "long_mean": lm,
        "long_alpha_ijr": (lm - ijr) if lm is not None else None,
        "keep_n": len(keep), "keep_mean": km,
        "keep_alpha_ijr": (km - ijr) if km is not None else None,
        "cat_recall": len(cats_flagged) / len(cats) if cats else None,
        "long_tickers": sorted(r["ticker"] for r in long_),
    }


def main():
    rows, _, _ = load_rows()
    rows = [r for r in rows if r["forward_return"] is not None]

    # tag tuples
    fam_counts: dict[str, int] = {}
    fam_fires: dict[str, int] = {}
    for r in rows:
        for t in r["tuples"]:
            f = family_of(t)
            t["_family"] = f
            fam_counts[f] = fam_counts.get(f, 0) + 1
            if SEV_W.get(t.get("severity"), 0) >= 2:
                fam_fires[f] = fam_fires.get(f, 0) + 1

    base = basket_stats(rows)
    results = {"family_tuple_counts": fam_counts, "family_severe_fires": fam_fires,
               "baseline": base, "drop_one": {}, "only_one_narrow": {}, }

    fams = [f for f, _ in FAMILIES] + ["filing_internal"]

    # DROP-ONE
    for fam in fams:
        ab = []
        dropped_names = []
        for r in rows:
            kept_tuples = [t for t in r["tuples"] if t["_family"] != fam]
            c = composite(kept_tuples)
            if c is None:
                dropped_names.append(r["ticker"])
                continue
            ab.append({**r, "composite": c, "tier": tier(c)})
        st = basket_stats(ab)
        st["names_left_unscoreable"] = dropped_names
        results["drop_one"][fam] = st

    # ONLY-ONE narrow exclusion: exclude if family fires SEVERE+
    for fam in fams:
        excluded = [r for r in rows if any(
            t["_family"] == fam and SEV_W.get(t.get("severity"), 0) >= 2 for t in r["tuples"])]
        kept = [r for r in rows if r not in excluded]
        cats = [r for r in rows if r["forward_return"] <= -0.40]
        cat_ex = [r for r in excluded if r["forward_return"] <= -0.40]
        km = statistics.mean(r["forward_return"] for r in kept) if kept else None
        results["only_one_narrow"][fam] = {
            "n_excluded": len(excluded),
            "excl_precision_cat": len(cat_ex) / len(excluded) if excluded else None,
            "cat_recall": len(cat_ex) / len(cats) if cats else None,
            "kept_n": len(kept), "kept_mean": km,
            "kept_alpha_ijr": (km - IJR) if km is not None else None,
        }

    # NARROW-UNION: pick the 2 families with highest exclusion precision (min 5 exclusions)
    cands = [(f, v) for f, v in results["only_one_narrow"].items()
             if v["n_excluded"] >= 5 and v["excl_precision_cat"] is not None]
    cands.sort(key=lambda kv: -kv[1]["excl_precision_cat"])
    union_f = [f for f, _ in cands[:2]]
    excluded = [r for r in rows if any(
        t["_family"] in union_f and SEV_W.get(t.get("severity"), 0) >= 2 for t in r["tuples"])]
    kept = [r for r in rows if r not in excluded]
    cats = [r for r in rows if r["forward_return"] <= -0.40]
    cat_ex = [r for r in excluded if r["forward_return"] <= -0.40]
    km = statistics.mean(r["forward_return"] for r in kept)
    results["narrow_union"] = {
        "families": union_f, "n_excluded": len(excluded),
        "excl_precision_cat": len(cat_ex) / len(excluded) if excluded else None,
        "cat_recall": len(cat_ex) / len(cats),
        "kept_n": len(kept), "kept_mean": km, "kept_alpha_ijr": km - IJR,
    }

    # RED-only anywhere (max-severity narrow rule)
    excluded = [r for r in rows if any(SEV_W.get(t.get("severity"), 0) >= 3 for t in r["tuples"])]
    kept = [r for r in rows if r not in excluded]
    cat_ex = [r for r in excluded if r["forward_return"] <= -0.40]
    km = statistics.mean(r["forward_return"] for r in kept)
    results["red_only_rule"] = {
        "n_excluded": len(excluded),
        "excl_precision_cat": len(cat_ex) / len(excluded) if excluded else None,
        "cat_recall": len(cat_ex) / len(cats),
        "kept_n": len(kept), "kept_mean": km, "kept_alpha_ijr": km - IJR,
    }

    (OUT / "control2_ablation.json").write_text(json.dumps(results, indent=2, default=str))

    print("family tuple counts:", fam_counts)
    print("family SEVERE+ fires:", fam_fires)
    b = base
    print(f"\nBASELINE  long n={b['long_n']} mean {b['long_mean']*100:+.1f}% alpha {b['long_alpha_ijr']*100:+.1f}pp | "
          f"keep n={b['keep_n']} mean {b['keep_mean']*100:+.1f}% alpha {b['keep_alpha_ijr']*100:+.1f}pp | recall {b['cat_recall']*100:.0f}%")
    print("\nDROP-ONE (comprehensive composite minus one family):")
    for fam in fams:
        s = results["drop_one"][fam]
        lm = s["long_mean"]; ka = s["keep_alpha_ijr"]
        print(f"  -{fam:16} long n={s['long_n']:3} mean {lm*100:+7.1f}% alpha {s['long_alpha_ijr']*100:+7.1f}pp | "
              f"keep alpha {ka*100:+7.1f}pp | recall {s['cat_recall']*100:3.0f}% | basket_now={s['long_tickers']}")
    print("\nONLY-ONE narrow exclusion (exclude on family SEVERE+):")
    for fam in fams:
        s = results["only_one_narrow"][fam]
        if s["kept_mean"] is None: continue
        pr = s["excl_precision_cat"]
        print(f"  {fam:16} excl={s['n_excluded']:3} prec={pr if pr is None else round(pr,2)} "
              f"recall={s['cat_recall']*100:3.0f}% kept_alpha={s['kept_alpha_ijr']*100:+.1f}pp (kept n={s['kept_n']})")
    nu = results["narrow_union"]
    print(f"\nNARROW-UNION {nu['families']}: excl={nu['n_excluded']} prec={nu['excl_precision_cat']:.2f} "
          f"recall={nu['cat_recall']*100:.0f}% kept_alpha={nu['kept_alpha_ijr']*100:+.1f}pp (kept n={nu['kept_n']})")
    ro = results["red_only_rule"]
    print(f"RED-ONLY rule: excl={ro['n_excluded']} prec={ro['excl_precision_cat']:.2f} "
          f"recall={ro['cat_recall']*100:.0f}% kept_alpha={ro['kept_alpha_ijr']*100:+.1f}pp (kept n={ro['kept_n']})")


if __name__ == "__main__":
    main()
