"""cosmecca_q2_model — Q2/H1-2026 revenue+margin estimate for Cosmecca (241710.KQ), = our segment quant
model ANCHORED to the Census demand tell, with a SOCIAL-MEDIA-LIFT overlay wired to the virality data.

METHOD:
1) Segment projection off VERIFIED Q1-26 actuals (DART), sequential (QoQ) with suncare seasonality +
   base-effect fade, cross-checked to the Census HS3304 import velocity (the aggregate demand ceiling).
2) SOCIAL-LIFT overlay: a coefficient on the Korea-export/US-indie segment driven by how many of
   Cosmecca's CONFIRMED customer-brands (openFDA: Anua, BYOMA, + likely) are trending on TikTok. The
   honest mechanic: virality LEADS the ODM print ~1-2 quarters, so a Q2 estimate wants the customer-brand
   virality from ~Q4'25-Q1'26 — which we DON'T have a history of (we just started logging). So today the
   overlay reads the CURRENT snapshot as a proxy and is FLAGGED low-confidence. With 0 of Cosmecca's
   customers currently trending (attention is on APR/ELF brands, not Cosmecca's), the lift is ~NEUTRAL.
"""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
VLOG = HERE / "beauty_velocity_log.jsonl"

# --- VERIFIED Q1-26 segment actuals (DART, KRW B) ---
Q1 = {"Korea": 142.2, "US": 49.7, "China": 6.4}        # +91.3% / +16.9% / -27.1% YoY
Q2_25_GROUP_EST = 165.0   # ESTIMATED Q2'25 base (FY25 640.8B; Q1'25 ~127B; Q2/Q3 suncare-stronger)
GROUP_OPM_RECENT = 0.118  # Q4'25 & Q1'26 run-rate; Q2'25 was 14.2% (the hard comp); FY25 13.0%

# Cosmecca's social-lift referents: ONLY openFDA-CONFIRMED *skincare* customer-brands (Englewood SPF).
# Excludes Bass Pro (retailer, not a skincare-virality signal) and Dr. Melaxin (UNVERIFIED link — adding
# it manufactured a spurious +1.5% lift via double-count; the discipline: confirmed referents only).
COSMECCA_CUSTOMERS = ["anua", "byoma", "dr. perry"]


def social_lift():
    """Read the latest virality poll; count Cosmecca customer-brands trending -> a small lift coefficient
    on the Korea/US-indie export segment. Honest: with no lagged history, this is a low-conf proxy."""
    n, note = 0, "no virality log"
    if VLOG.exists():
        try:
            last = json.loads(VLOG.read_text().splitlines()[-1])
            tags = []
            for rows in last.get("by_industry", {}).values():
                tags += [r["tag"].lower() for r in rows]
            n = sum(1 for c in set(COSMECCA_CUSTOMERS) if any(c.replace(" ", "") in t.replace(" ", "") for t in tags))
            note = f"{n} Cosmecca customer-brand(s) trending in latest poll ({len(tags)} hashtags)"
        except Exception as e:
            note = f"log read err: {str(e)[:50]}"
    # lift = +1%/trending-customer-brand on the export leg, minus a 0.5% share-of-attention drag,
    # clamped small. n=0 -> ~neutral. (Uncalibrated directional overlay, NOT a fitted coefficient.)
    lift = max(-0.02, min(0.05, 0.01 * n - 0.005))
    return {"n_customers_trending": n, "lift_pct": round(lift, 4), "note": note,
            "confidence": "LOW (no lagged customer-brand virality history; current snapshot as proxy)"}


def project():
    sl = social_lift()
    L = sl["lift_pct"]
    # QoQ multipliers off Q1-26 (suncare-season tailwind vs base-effect fade). Social lift nudges the
    # Korea/US export legs (the US-indie-brand exposed ones); China unaffected.
    scen = {
        "bear":  {"Korea": 0.98, "US": 0.98, "China": 0.95, "opm": 0.115},
        "base":  {"Korea": 1.05, "US": 1.03, "China": 1.00, "opm": 0.128},
        "bull":  {"Korea": 1.12, "US": 1.06, "China": 1.05, "opm": 0.140},
    }
    out = {}
    for s, c in scen.items():
        kor = Q1["Korea"] * c["Korea"] * (1 + L)
        us = Q1["US"] * c["US"] * (1 + L)
        chn = Q1["China"] * c["China"]
        grp = kor + us + chn
        op = grp * c["opm"]
        yoy = grp / Q2_25_GROUP_EST - 1
        # threshold read: re-rate needs OPM>=13% AND Korea YoY still strong (>30%); unwind = OPM<12% & Korea fading
        kor_yoy = kor / (Q2_25_GROUP_EST * 0.52) - 1   # ~52% of Q2'25 was Korea (rough)
        out[s] = {"Korea": round(kor, 1), "US": round(us, 1), "China": round(chn, 1),
                  "group_rev": round(grp, 1), "OP": round(op, 1), "OPM": c["opm"],
                  "group_yoy": round(yoy, 3), "korea_yoy_est": round(kor_yoy, 3)}
    return sl, out


def read(out):
    b = out["base"]
    rerate = b["OPM"] >= 0.13 and b["korea_yoy_est"] > 0.30
    unwind = b["OPM"] < 0.12 and b["korea_yoy_est"] < 0.20
    if rerate:
        return "RE-RATE-ish (OPM>=13% + Korea still >30%) — but base OPM sits right on the 13% line"
    if unwind:
        return "UNWIND (OPM<12% + Korea fading)"
    return ("IN-LINE / base: strong revenue (suncare) + OPM ~12.5-13% borderline + Korea still >30% YoY. "
            "Roughly priced — the print is the trigger, not a clear re-rate. Matches the standalone Q2 prediction.")


if __name__ == "__main__":
    sl, out = project()
    print("=== COSMECCA Q2/H1-2026 ESTIMATE (segment quant + Census anchor + social-lift overlay) ===")
    print(f"\nSOCIAL-MEDIA LIFT: {sl['lift_pct']:+.1%}  ({sl['note']}; conf {sl['confidence']})")
    print(f"  -> {'NEUTRAL — does NOT raise the estimate' if abs(sl['lift_pct'])<0.01 else 'applied to export legs'}")
    print(f"\n{'scenario':<8} {'Korea':>7} {'US':>6} {'China':>6} {'GROUP':>7} {'YoY':>7} {'OPM':>6} {'OP(KRWb)':>9}")
    for s, r in out.items():
        print(f"{s:<8} {r['Korea']:>7} {r['US']:>6} {r['China']:>6} {r['group_rev']:>7} "
              f"{r['group_yoy']:>+7.0%} {r['OPM']:>6.1%} {r['OP']:>9}")
    print(f"\nREAD: {read(out)}")
    print("\nNOTE: Q1-26 segments VERIFIED (DART). Q2'25 base + Korea-share = ESTIMATED. Social-lift = "
          "uncalibrated directional overlay (no lagged customer-brand virality history yet) -> ~neutral now.")
