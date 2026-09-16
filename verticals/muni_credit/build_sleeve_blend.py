"""build_sleeve_blend — re-optimize the blended sleeve (Option C) on AFTER-TAX TEY.

Replaces the original fixed 40/60-by-provenance blend with a constraint formulation that
encodes what the 40% anchor was actually FOR (liquidity):

  maximize   par-weighted de-minimis-aware after-tax TEY
  subject to ladder coverage (>=1 name per maturity year where inventory allows)
             max 1 name per CUSIP-6 issuer
             >= ANCHOR_MIN of par in fast names (spread <=0.30pt and >=24 trades/yr)
             N = 24

Selection universe = the EMMA-verified, liquidity-gated names in Option A execclean + Option B
(48, no overlap). If data/issuer_credit/issuer_credit_latest.json exists, per-issuer credit
scores (AB 1200 certification-adjusted) REPLACE the flat security-class 90 for school GOs and
the issuer/county/fault-zone/seismic columns are attached to each holding.

Re-run after every Option A/B rebuild. Output: muni_etf_sleeve_blended.json.
"""
import json, datetime, os, statistics as st

SETTLE = datetime.date(2026, 6, 10)
TARGET, LOT, N_TARGET, ANCHOR_MIN = 1_000_000, 5_000, 24, 0.40
ZONE_CAP = 0.25   # default max share of NAMES per named-fault zone (single-event concentration cap;
                  # SF-vs-LA: San Andreas N and S segments rupture independently — 1906 vs 1857 — so
                  # capping each zone separately IS the diversification, per UCERF3 scenario geometry).
                  # HAZARD-WEIGHTED 2026-06-17: a single event in a HIGH-Ss zone (Bay/LA/Inland Empire/
                  # San Diego) is far more damaging than one in the low-Ss Central Valley, so cap the
                  # high-hazard zones TIGHTER (0.20) and the low-hazard Central Valley LOOSER (0.40) —
                  # optimize the real single-event risk, not a flat name-count.
def zone_cap(z):
    z = (z or "").upper()
    if any(k in z for k in ("BAY", "LA BASIN", "INLAND EMPIRE", "SAN DIEGO")): return 0.20  # high Ss
    if "CENTRAL VALLEY" in z: return 0.40                                                    # low Ss
    return 0.30                                                                              # other/mid
FIRE_HIGH = 0.15  # a name counts as fire-exposed when >=15% of building value sits in FEMA-NRI
FIRE_CAP = 0.0    # Relatively-High/Very-High wildfire tracts (was 0.30 — too loose: it let names with
                  # 15-30% of the TAX BASE in high-fire tracts grade clean. Tightened 2026-06-17 after a
                  # regrade caught Lakeside 28% / Monterey 20% / Western Placer 16% sitting in the book.
                  # Channel: insurer withdrawal -> unmarketable property -> assessed-value drag on
                  # the levy base. Fires are NOT single-fault events (2017/2020 sieges were
                  # statewide), so this caps the aggregate, not per-zone.


def yrs(mat):
    y, m, d = [int(x) for x in mat.split("-")]
    return (datetime.date(y, m, d) - SETTLE).days / 365.25


def tey_at(b):
    if b.get("tey_ytw_aftertax"): return b["tey_ytw_aftertax"]
    px, cp, ytw = b["emma_px"], b["coupon"], b["ytw"]
    thr = 100 - 0.25 * yrs(b["maturity"]); curr = cp / px
    if px < thr: return round(curr * 2.01 + max(0.0, ytw - curr), 4)
    return round(ytw * 2.01, 4)


def is_fast(b):
    l = b.get("liq") or {}
    return (l.get("px_spread") or 9) <= 0.30 and (l.get("n365") or 0) >= 24


def load():
    univ = []
    for fn, tag in [("muni_etf_option_A_execclean.json", "A-liquid"),
                    ("muni_etf_option_B_highyield.json", "B-yield"),
                    ("muni_etf_scanner_cleared.json", "C-scanner")]:   # underwritten scanner finds
        if not os.path.exists(fn): continue
        for b in json.load(open(fn))["barbell"]:
            b["sleeve"] = tag; b["tey_ytw_aftertax"] = tey_at(b); univ.append(b)
    # per-issuer credit overlay (school GOs): certification-adjusted score replaces class-90
    p = "data/issuer_credit/issuer_credit_latest.json"
    if os.path.exists(p):
        ic = {r["cusip"]: r for r in json.load(open(p))}
        for b in univ:
            r = ic.get(b["cusip"])
            if r:
                b["credit"] = r["credit_score"]
                b.update(issuer=r.get("district") or r.get("issuer"), county=r.get("county"),
                         cert_status=r.get("cert_status"), fault_zone=r.get("fault_zone"),
                         seismic_ss=r.get("seismic_ss"), credit_notes=r.get("credit_notes"),
                         fire_score=r.get("fire_score"), fire_high_share=r.get("fire_high_share"),
                         fire_worst_tract=r.get("fire_worst_tract"))
    return univ


def is_high_fire(b):
    return (b.get("fire_high_share") or 0) > FIRE_HIGH


def select(univ):
    AT = lambda b: -b["tey_ytw_aftertax"]
    basket, used6 = [], set()
    def take(b):
        basket.append(b); used6.add(b["cusip"][:6])
    byyr = {}
    for b in univ: byyr.setdefault(b["maturity"][:4], []).append(b)
    for y in sorted(byyr):                                   # ladder backbone, best after-tax per year
        for b in sorted(byyr[y], key=AT):
            if b["cusip"][:6] not in used6: take(b); break
    pool = sorted([b for b in univ if b["cusip"][:6] not in used6], key=AT)
    for b in pool:
        if len(basket) >= N_TARGET: break
        if b["cusip"][:6] not in used6: take(b)
    # liquidity-anchor repair: swap worst slow names for best unused fast names until >= ANCHOR_MIN
    def fast_share():
        return sum(1 for b in basket if is_fast(b)) / len(basket)
    spare_fast = sorted([b for b in univ if is_fast(b) and b["cusip"][:6] not in used6], key=AT)
    while fast_share() < ANCHOR_MIN and spare_fast:
        slow = sorted([b for b in basket if not is_fast(b)], key=AT)
        if not slow: break
        out = slow[-1]; inn = spare_fast.pop(0)
        basket.remove(out); used6.discard(out["cusip"][:6]); take(inn)
    # COMBINED single-event-zone + wildfire repair — run as ONE loop so a swap for one cap can't
    # re-violate the other (the old sequential repairs conflicted: the fire pass re-concentrated a
    # fault zone the zone pass had just diversified). Each replacement must satisfy BOTH caps.
    from collections import Counter
    def zone_counts(): return Counter(b.get("fault_zone") for b in basket if b.get("fault_zone"))
    def fits(b):   # a candidate that does not itself breach either cap if added
        z = b.get("fault_zone")
        if is_high_fire(b): return False
        if z and (zone_counts()[z] + 1) / len(basket) > zone_cap(z): return False
        return True
    for _ in range(4 * N_TARGET):
        zc = zone_counts()
        over_zone = [z for z, c in zc.items() if c / len(basket) > zone_cap(z)]
        hf = [b for b in basket if is_high_fire(b)]
        over_fire = len(hf) / len(basket) > FIRE_CAP
        if not over_zone and not over_fire: break
        # remove the worst-AT name in whichever cap is most violated
        if over_zone:
            z = max(over_zone, key=lambda z: zc[z])
            out = sorted([b for b in basket if b.get("fault_zone") == z], key=AT)[-1]
        else:
            out = sorted(hf, key=AT)[-1]
        repl = sorted([b for b in univ if b["cusip"][:6] not in used6 and fits(b)], key=AT)
        if not repl: break
        basket.remove(out); used6.discard(out["cusip"][:6]); take(repl[0])
    return basket


def size(basket):
    base = (TARGET // len(basket) // LOT) * LOT
    for b in basket: b["par"] = base
    for b in sorted(basket, key=lambda x: -x["tey_ytw_aftertax"])[:(TARGET - base * len(basket)) // LOT]:
        b["par"] += LOT


def main():
    univ = load(); basket = select(univ); size(basket)
    tot = sum(b["par"] for b in basket)
    def pw(k):
        n = sum(b["par"] * b[k] for b in basket if b.get(k) is not None)
        d = sum(b["par"] for b in basket if b.get(k) is not None)
        return n / d if d else None
    sp = [b["liq"]["px_spread"] for b in basket if (b.get("liq") or {}).get("px_spread") is not None]
    from collections import Counter
    fz = Counter()
    for b in basket:
        if b.get("fault_zone"): fz[b["fault_zone"]] += b["par"]
    summ = {"sleeve": "C-blended", "n": len(basket), "total_par": tot,
            "selection_metric": "after-tax TEY (de-minimis aware), liquidity-anchor constraint",
            "anchor_min_fast_share": ANCHOR_MIN,
            "fast_share": round(sum(1 for b in basket if is_fast(b)) / len(basket), 2),
            "par_weighted_ytw_pct": round(pw("ytw") * 100, 2),
            "par_weighted_tey_aftertax_pct": round(pw("tey_ytw_aftertax") * 100, 2),
            "par_weighted_insulation": round(pw("insul")), "par_weighted_credit": round(pw("credit")),
            "demin_breaches": sum(1 for b in basket if b.get("demin_breach")),
            "median_same_day_spread_pt": round(st.median(sp), 3) if sp else None,
            "ladder": f"{min(b['maturity'] for b in basket)}..{max(b['maturity'] for b in basket)}",
            "par_by_fault_zone": {k: v for k, v in fz.most_common()},
            "high_fire_names": sum(1 for b in basket if is_high_fire(b)),
            "high_fire_par": sum(b["par"] for b in basket if is_high_fire(b)),
            "fire_cap_names_share": FIRE_CAP, "fire_high_threshold": FIRE_HIGH,
            "phase1_deployable_now_par": sum(b["par"] for b in basket if is_fast(b)),
            "phase1_pct": round(100 * sum(b["par"] for b in basket if is_fast(b)) / tot),
            "phase2_accumulate_par": sum(b["par"] for b in basket if not is_fast(b)),
            "phase2_n_names": sum(1 for b in basket if not is_fast(b)),
            "asof": str(SETTLE)}
    json.dump({"basket_summary": summ, "barbell": basket},
              open("muni_etf_sleeve_blended.json", "w"), indent=1, default=str)
    print(f"SLEEVE C (after-tax optimized) — {len(basket)} names, ${tot:,}")
    print(f"  YTW {summ['par_weighted_ytw_pct']}% | TEY after-tax {summ['par_weighted_tey_aftertax_pct']}% | "
          f"insul {summ['par_weighted_insulation']} | credit {summ['par_weighted_credit']} | "
          f"fast-share {summ['fast_share']} | demin {summ['demin_breaches']}/{len(basket)}")
    for z, v in summ["par_by_fault_zone"].items():
        print(f"  zone {z}: ${v:,} ({100*v/tot:.0f}%)")


if __name__ == "__main__":
    main()
