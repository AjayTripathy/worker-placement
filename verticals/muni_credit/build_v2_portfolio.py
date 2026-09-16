"""Build the portfolio from v2 dual-axis scores: gate on creditworthiness AND AI-insulation,
exclude UNVERIFIABLE credit (UNVERIFIABLE != clean), then report holdings + portfolio stats.
"""
import json, statistics as st

D = json.load(open("data/channel_scores_v2.json"))
B = D["bonds"]
INS_GATE, CRED_GATE = 90, 75   # AI-insulation >= 90, creditworthiness >= 75

def passes(b):
    f0 = b["rfm_diligence"][0]["finding"]
    return (b["ai_insulation"] >= INS_GATE and b["creditworthiness"] >= CRED_GATE
            and "UNVERIFIABLE" not in f0)

port = sorted([b for b in B if passes(b)], key=lambda b: (-b["creditworthiness"], -b["ai_insulation"]))
excl = [b for b in B if not passes(b)]

def f(xs): return [x for x in xs if x is not None]
ytw = st.mean(f(b["ytw_pct"] for b in port)); ytm = st.mean(f(b["ytm_pct"] for b in port))
dw = st.mean(f(b["dur_to_worst"] for b in port)); dm = st.mean(f(b["dur_to_maturity"] for b in port))
ins = st.mean(b["ai_insulation"] for b in port); cred = st.mean(b["creditworthiness"] for b in port)

print(f"=== V2 PORTFOLIO — gates: AI-insulation>={INS_GATE}, creditworthiness>={CRED_GATE}, credit not UNVERIFIABLE ===")
print(f"{'obligor':<36}{'sec':>16}{'AIins':>6}{'cred':>5}{'YTW':>6}{'durW':>6}")
for b in port:
    print(f"{b['obligor'][:35]:<36}{b['security'][:16]:>16}{b['ai_insulation']:>6.0f}"
          f"{b['creditworthiness']:>5.0f}{(b['ytw_pct'] or 0):>6.2f}{(b['dur_to_worst'] or 0):>6.1f}")
print(f"\nHOLDINGS: {len(port)} (equal-weight)")
print(f"  avg AI-insulation {ins:.0f}/100  |  avg creditworthiness {cred:.0f}/100")
print(f"  avg YTW {ytw:.2f}%  YTM {ytm:.2f}%  TEY(YTW x2.01) {ytw*2.01:.2f}%")
print(f"  duration to-worst {dw:.1f}yr / to-maturity {dm:.1f}yr")
from collections import Counter
sec = Counter(b["security"] for b in port)
print("  security mix: " + ", ".join(f"{k}:{v}" for k, v in sec.most_common()))
print(f"\nEXCLUDED ({len(excl)}/20) with reason:")
for b in excl:
    f0 = b["rfm_diligence"][0]["finding"]
    why = ("UNVERIFIABLE credit" if "UNVERIFIABLE" in f0 else
           f"insulation {b['ai_insulation']:.0f}<{INS_GATE}" if b["ai_insulation"] < INS_GATE else
           f"credit {b['creditworthiness']:.0f}<{CRED_GATE}")
    print(f"  {b['obligor'][:38]:<40} [{b['security']}] — {why}")

json.dump({"gates": {"ai_insulation": INS_GATE, "creditworthiness": CRED_GATE},
           "holdings": port, "excluded": [{"obligor": b["obligor"], "reason": b["security"]} for b in excl],
           "stats": {"n": len(port), "avg_ai_insulation": round(ins, 1), "avg_creditworthiness": round(cred, 1),
                     "avg_ytw_pct": round(ytw, 2), "tey_pct": round(ytw * 2.01, 2),
                     "dur_to_worst": round(dw, 1), "dur_to_maturity": round(dm, 1)}},
          open("data/v2_portfolio.json", "w"), indent=1)
print("\nsaved -> data/v2_portfolio.json")
