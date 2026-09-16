"""portfolio_model.py — explore the yield/risk frontier over the consolidated diligence master.

Build portfolios under different constraint sets and see what each costs in after-tax TEY: fire tail,
single-event earthquake zone concentration (hazard-weighted), AI insulation, credit, liquidity. The
point is to SEE THE TRADE — how much yield you give up to take fire/quake risk down.

  python3 portfolio_model.py            # scenario comparison + the earthquake-diversification frontier
  (or import: load(), select(constraints), profile(holdings))
"""
import json, os, statistics as st
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "outputs")
N = 24                                   # target names
DEFAULT_ZONE_CAP = {"HIGH": 0.20, "LOW": 0.40, "MID": 0.30, "UNZONED": 0.30}

def load():
    m = json.load(open(os.path.join(OUT, "DILIGENCE_MASTER.json")))
    # investable = priced + screened (CLEAR/REVIEW only) — exclude FLAG and not-yet-underwritten UNSCREENED
    return [r for r in m if r.get("tey_aftertax") and r.get("maturity")
            and r["uw_verdict"] in ("CLEAR", "REVIEW")]

def select(univ, n=N, fire_tail_cap=1.0, flood_tail_cap=1.0, zone_cap=None, ai_floor=0, credit_floor=0,
           clear_only=False, ss_cap=99.0, exclude_near_call=True, sgma_cap=1.0):
    """Greedy max-TEY portfolio with a maturity-ladder backbone + the given risk caps (count-based).
    exclude_near_call drops HARD near-par-call names (never a long-hold ladder anchor); sgma_cap bounds
    the share of names in critically-overdrafted groundwater basins (slow AV-erosion tail)."""
    zone_cap = zone_cap or DEFAULT_ZONE_CAP
    pool = [r for r in univ
            if (not clear_only or r["uw_verdict"] == "CLEAR")
            and (r.get("ai_insulation") or 100) >= ai_floor
            and (r.get("credit_score") or 100) >= credit_floor
            and (r.get("fire_tail") or 0) < fire_tail_cap
            and (r.get("flood_tail") or 0) < flood_tail_cap
            and not (exclude_near_call and r.get("call_risk") == "HARD")
            and (r.get("seismic_ss") or 0) < ss_cap]
    pool.sort(key=lambda r: -r["tey_aftertax"])
    basket, used6 = [], set(); zc = Counter(); yrs = set()
    def cap_ok(r):   # PER-ZONE cap (Bay vs LA are independent faults — cap each separately, level by hazard)
        z = r.get("fault_zone") or "UNZONED"
        cap = zone_cap.get(r.get("hazard_tier", "UNZONED"), 0.30)
        return zc[z] + 1 <= cap * n + 1e-9
    def add(r):
        basket.append(r); used6.add(r["cusip"][:6]); zc[r.get("fault_zone") or "UNZONED"] += 1
    for r in sorted(pool, key=lambda r: (r["maturity"][:4], -r["tey_aftertax"])):   # ladder backbone
        if len(basket) >= n: break
        yr = r["maturity"][:4]
        if yr in yrs or r["cusip"][:6] in used6 or not cap_ok(r): continue
        add(r); yrs.add(yr)
    for r in pool:                                                                   # fill by TEY
        if len(basket) >= n: break
        if r["cusip"][:6] in used6 or not cap_ok(r): continue
        add(r)
    return basket

def profile(hold):
    if not hold: return {}
    teys = [r["tey_aftertax"] for r in hold]; n = len(hold)
    zc = Counter(r.get("fault_zone") or "UNZONED" for r in hold)
    htc = Counter(r.get("hazard_tier", "UNZONED") for r in hold)
    max_zone = max(zc.values()) / n
    high_haz_share = htc.get("HIGH", 0) / n
    # the REAL single-event metric: largest share in any single HIGH-hazard (major-fault) zone
    hi_zones = Counter(r.get("fault_zone") for r in hold if r.get("hazard_tier") == "HIGH")
    max_hi_zone = (max(hi_zones.values()) / n) if hi_zones else 0
    fast = sum(1 for r in hold if (r.get("px_spread") or 9) <= 0.30 and (r.get("n365") or 0) >= 24) / n
    return {
        "n": n, "TEY": round(st.mean(teys) * 100, 2),
        "max_1evt%": round(max_hi_zone * 100, 0),     # worst single-event (largest single major-fault zone)
        "high_haz%": round(high_haz_share * 100, 0),
        "fire>=15%": sum(1 for r in hold if (r.get("fire_tail") or 0) >= 0.15),
        "max_fire_tail%": round(max((r.get("fire_tail") or 0) for r in hold) * 100, 0),
        "flood>=15%": sum(1 for r in hold if (r.get("flood_tail") or 0) >= 0.15),
        "sgma_crit": sum(1 for r in hold if r.get("sgma_critical")),
        "near_call": sum(1 for r in hold if r.get("call_risk") == "HARD"),
        "Ss>=2.0": sum(1 for r in hold if (r.get("seismic_ss") or 0) >= 2.0),
        "AI_insul": round(st.mean([r["ai_insulation"] for r in hold if r.get("ai_insulation")] or [0]), 0),
        "credit": round(st.mean([r["credit_score"] for r in hold if r.get("credit_score")] or [0]), 0),
        "fast%": round(fast * 100, 0), "demin": sum(1 for r in hold if r.get("demin_breach")),
    }

SCENARIOS = {
    "Max yield (no caps)":    dict(zone_cap={"HIGH":1.0,"LOW":1.0,"MID":1.0,"UNZONED":1.0}, fire_tail_cap=1.0),
    "Clean-verdict only":     dict(clear_only=True, zone_cap={"HIGH":1.0,"LOW":1.0,"MID":1.0,"UNZONED":1.0}),
    "Fire tail = 0":          dict(fire_tail_cap=0.0001, zone_cap={"HIGH":1.0,"LOW":1.0,"MID":1.0,"UNZONED":1.0}),
    "Quake-diversified":      dict(zone_cap={"HIGH":0.20,"LOW":0.40,"MID":0.30,"UNZONED":0.30}),
    "Balanced (all caps)":    dict(fire_tail_cap=0.15, zone_cap={"HIGH":0.20,"LOW":0.35,"MID":0.30,"UNZONED":0.25}, ss_cap=2.0),
    "Conservative (CLEAR+caps)": dict(clear_only=True, fire_tail_cap=0.0001, zone_cap={"HIGH":0.20,"LOW":0.35,"MID":0.30,"UNZONED":0.25}, ss_cap=2.0),
}

def main():
    univ = load()
    print(f"investable universe (CLEAR+REVIEW, priced): {len(univ)} names\n")
    cols = ["n","TEY","max_1evt%","high_haz%","fire>=15%","max_fire_tail%","Ss>=2.0","AI_insul","credit","fast%","demin"]
    print(f"{'scenario':28} " + " ".join(f"{c:>9}" for c in cols))
    base=None
    for name, cons in SCENARIOS.items():
        p = profile(select(univ, **cons))
        if base is None: base = p["TEY"]
        cost = f"({p['TEY']-base:+.2f})" if name!="Max yield (no caps)" else ""
        print(f"{name:28} " + " ".join(f"{str(p.get(c,'')):>9}" for c in cols) + f"  TEY {cost}")
    # earthquake-diversification frontier: tighten the HIGH-hazard zone cap, watch TEY
    print("\n=== Earthquake-diversification frontier (tighten high-hazard zone cap) ===")
    print(f"{'high-haz zone cap':18} {'TEY':>6} {'max-1evt%':>10} {'high-haz%':>10} {'Ss>=2.0':>8}")
    for cap in (1.00, 0.40, 0.30, 0.25, 0.20, 0.15):
        zc = {"HIGH": cap, "LOW": 0.40, "MID": 0.30, "UNZONED": 0.30}
        p = profile(select(univ, zone_cap=zc))
        print(f"{cap*100:>14.0f}%   {p['TEY']:>6.2f} {p['max_1evt%']:>10.0f} {p['high_haz%']:>10.0f} {p['Ss>=2.0']:>8}")

if __name__ == "__main__":
    main()
