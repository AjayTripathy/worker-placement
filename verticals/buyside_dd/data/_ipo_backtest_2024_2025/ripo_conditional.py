"""Does the framework's exclusion add anything ON TOP OF RIPO's picks?

Prior test (ripo_membership.py) showed RIPO's selection alone separates
catastrophes (in-RIPO cat-rate 0.20 vs 0.68 out). The sharper question: take
ONLY the names RIPO actually held, then apply the framework's exclusion selector
(foreign-issuer / archetype). Conditional on already passing RIPO's size/liquidity
screen, does the detector still exclude the losers — i.e. is there incremental
edge over just buying the passive product?

Run: python3 verticals/buyside_dd/data/_ipo_backtest_2024_2025/ripo_conditional.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE / "ripo_conditional.json"

OFFSHORE = {"E9", "D8", "D0"}
ASIA = {"F4", "K3", "U0", "F5", "N8"}
SUFFIXES = {"INC", "CORP", "CORPORATION", "LTD", "LIMITED", "LLC", "PLC", "CO",
            "GROUP", "HOLDINGS", "HOLDING", "SA", "AG", "NV", "PARENT",
            "TECHNOLOGIES", "INTERNATIONAL", "THE", "CLASS", "A", "COMPANY"}


def norm(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9 ]", " ", (name or "").upper())
    return " ".join(t for t in s.split() if t and t not in SUFFIXES)


def main():
    mem = json.loads((HERE / "ripo_membership.json").read_text())
    in_ripo_norm = {norm(n) for n in mem["in_ripo_names"]}

    feats = {f["cik"]: f for f in json.loads((HERE / "features.json").read_text())["features"]}
    outs = {o["cik"]: o for o in json.loads((HERE / "outcomes.json").read_text())["labels"]}
    cohort = json.loads((HERE / "cohort.json").read_text())["cohort"]

    rows = []
    for rec in cohort:
        keys = {norm(rec["company_name"]), norm(rec.get("name_official") or "")}
        if not (keys & in_ripo_norm):
            continue
        o = outs.get(rec["cik"], {})
        f = feats.get(rec["cik"], {})
        r = o.get("r_current")
        if r is None and o.get("delisted_no_price"):
            r = -1.0  # adverse delist only; merger cash-out stays None (excluded)
        offshore = int(f.get("incorp_code") in OFFSHORE)
        asia = int(f.get("biz_country_code") in ASIA)
        fpi = int(bool(f.get("foreign_private_issuer")))
        rows.append({
            "name": rec["company_name"], "r": r,
            "catastrophe": bool(o.get("catastrophe")),
            "foreign_issuer": fpi, "archetype": offshore + asia + fpi,
        })

    def stats(rs):
        rets = [x["r"] for x in rs if x["r"] is not None]
        cats = sum(x["catastrophe"] for x in rs)
        return {
            "n": len(rs),
            "catastrophe_rate": round(cats / len(rs), 3) if rs else None,
            "mean_return": round(sum(rets) / len(rets), 4) if rets else None,
            "median_return": round(sorted(rets)[len(rets) // 2], 4) if rets else None,
            "pct_positive": round(sum(1 for x in rets if x > 0) / len(rets), 3) if rets else None,
        }

    strategies = {
        "ripo_all": rows,
        "ripo_then_exclude_foreign_issuer": [r for r in rows if not r["foreign_issuer"]],
        "ripo_then_exclude_archetype_ge1": [r for r in rows if r["archetype"] < 1],
        "ripo_then_exclude_archetype_ge2": [r for r in rows if r["archetype"] < 2],
    }
    table = {k: stats(v) for k, v in strategies.items()}

    flagged = [r for r in rows if r["foreign_issuer"]]
    results = {
        "n_ripo_cohort": len(rows),
        "strategies": table,
        "names_excluded_by_foreign_issuer": [r["name"] for r in flagged],
        "excluded_were_catastrophes": {r["name"]: r["catastrophe"] for r in flagged},
    }
    OUT.write_text(json.dumps(results, indent=2))

    print(f"RIPO ∩ cohort names: {len(rows)}")
    print(f"\n{'strategy':<36}{'n':<5}{'cat_rate':<10}{'mean':<10}{'median':<10}{'%pos'}")
    for k, s in table.items():
        print(f"{k:<36}{s['n']:<5}{s['catastrophe_rate']:<10}{s['mean_return']:<10}{s['median_return']:<10}{s['pct_positive']}")
    print(f"\nNames the foreign-issuer screen would drop from RIPO's picks:")
    for r in flagged:
        rs = f"{r['r']:+.3f}" if r["r"] is not None else "merger/no-px (excluded)"
        print(f"  {r['name']:<40} r={rs:<24} catastrophe={r['catastrophe']}")
    print(f"\nWrote {OUT.name}")


if __name__ == "__main__":
    main()
