"""build_diligence_master.py — consolidate ALL per-CUSIP diligence + underwriting into one durable record.

Joins the scattered outputs (scanner want-list, fire x EQ x AI underwriting, AB-1200 credit overlay,
the live book) into a single master keyed by CUSIP, carrying every screen result so nothing is lost and
the whole universe is queryable / model-able. Re-run any time to refresh (idempotent). The regraded,
banded verdict (post-2026-06-17 fire fix) is recomputed here so the master is always current.

Writes: outputs/DILIGENCE_MASTER.json  (+ .csv for spreadsheets, + a short .md summary)
"""
import json, os, csv, datetime
from collections import Counter
try:
    import underwrite_candidates as GAP        # gap_screens (small-base / reinvest / construction / insurer)
except Exception:
    GAP = None

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "outputs")
def load(p, d):
    try: return json.load(open(p))
    except Exception: return d

# hazard tier per named fault zone (single-event severity; drives the hazard-weighted zone cap)
def hazard_tier(z):
    z = (z or "").upper()
    if any(k in z for k in ("BAY", "LA BASIN", "INLAND EMPIRE", "SAN DIEGO")): return "HIGH"
    if "CENTRAL VALLEY" in z: return "LOW"
    if not z or z == "NONE": return "UNZONED"
    return "MID"

def regrade(rec):
    """Banded, current verdict from the consolidated screens (matches underwrite_candidates fix)."""
    pledge = rec.get("pledge") or ("water" if "water" in ((rec.get("security") or "")).lower() else "school")
    # WATER/wastewater REVENUE bonds: graded by the revenue track (DSCR/supply/customer) + structure +
    # litigation — NOT the school-district cert/fire/geo screens (which correctly return N/A for them).
    if pledge == "water":
        if rec.get("dscr") is None and rec.get("system_type") is None:
            return "UNSCREENED", ["water-not-underwritten"]
        wf = []
        dscr = rec.get("dscr")
        if dscr is not None and dscr < 1.10: wf.append(f"DSCR:{dscr:.2f}x")
        elif dscr is not None and dscr < 1.25: wf.append(f"dscr-review:{dscr:.2f}x")
        if rec.get("supply_risk") == "high": wf.append("water-supply-high")
        if rec.get("call_risk") == "HARD": wf.append(f"near-par-call:{rec.get('next_call_date') or ''}")
        elif rec.get("call_risk") == "SOFT": wf.append("call-soon")
        if rec.get("is_cab"): wf.append("CAB-structure")
        if rec.get("issuer_litig_hard"): wf.append("issuer-litigation")
        elif rec.get("issuer_litigation_flag") in ("FLAG", "REVIEW"): wf.append("issuer-litig-review")
        whard = [f for f in wf if f.startswith(("DSCR", "near-par-call", "CAB", "issuer-litigation"))]
        return ("FLAG" if whard else ("REVIEW" if wf else "CLEAR")), wf
    # NOT-YET-SCREENED names must NOT default to CLEAR — no fire/EQ/credit data = UNSCREENED, not investable
    if rec.get("fire_score") is None and rec.get("seismic_ss") is None and rec.get("credit_score") is None:
        return "UNSCREENED", ["not-yet-underwritten"]
    flags = []; cert = rec.get("cert_status"); tail = rec.get("fire_tail"); ss = rec.get("seismic_ss")
    ins = rec.get("ai_insulation")
    if cert in ("NEGATIVE", "QUALIFIED"): flags.append(f"fiscal:{cert}")
    elif cert in ("CC-PROBATION", "CC-SHOWCAUSE"): flags.append(f"CC-sanction:{cert[3:].lower()}")   # ACCJC sanction = hard
    elif cert in ("CC-WARNING", "CC-RESTORATION", "CC-UNKNOWN", "NOT-COVERED-CC"): flags.append(f"CC-review:{cert}")  # soft
    # CC-ACCREDITED (good standing) -> no flag, grades like a Positive cert
    if (cert or "").startswith("UNRESOLVED"): flags.append("unresolved-geo")  # incl AMBIG/COLLISION
    if ins is not None and ins < 90: flags.append("AI<90")
    if tail is None and rec.get("district"): flags.append("fire-unmatched")
    elif (tail or 0) >= 0.30: flags.append(f"FIRE-high:{tail*100:.0f}%")
    elif (tail or 0) >= 0.15: flags.append(f"fire-review:{tail*100:.0f}%")
    if (ss or 0) >= 2.0: flags.append(f"EQ-elev:{ss:.2f}")
    elif (ss or 0) >= 1.5: flags.append(f"EQ-veryhigh:{ss:.2f}")
    # --- extended screens (2026-06-19): flood / subsidence / sgma / structure / av-conc / debt / litigation / fiscal / water ---
    ft = rec.get("flood_tail")   # FLOOD = REVIEW only, and only the EXTREME within-CA tail (>=p85 ~0.90):
    if (ft or 0) >= 0.90: flags.append(f"flood:{ft*100:.0f}%")   # NRI rates ~all developed CA high (non-discriminating below this)
    if rec.get("subsidence_flag"): flags.append("subsidence")
    # SGMA is an AG-AV-erosion tail; it's immaterial for a large URBAN tax base. Gate the county-level flag
    # by AV size: a >$8B base is a city (Fresno's ag AV is ~0.02%), so don't flag it (DD-confirmed false
    # positives). Small/unknown-AV ag districts still flag.
    if rec.get("sgma_critical") and (rec.get("base_av") or 0) < 8e9:
        flags.append("sgma-overdraft")
    cr = rec.get("call_risk")
    if cr == "HARD": flags.append(f"near-par-call:{rec.get('next_call_date') or ''}")
    elif cr == "SOFT": flags.append("call-soon")
    elif cr == "UNVERIFIABLE" and (rec.get("px") or 0) >= 100.5: flags.append("premium-call-UNVERIFIABLE")  # Atwater trap
    if rec.get("is_cab"): flags.append("CAB-structure")
    av1 = rec.get("av_top1_share")                       # percent scale (e.g. 13.54)
    if av1 is not None and av1 > 20: flags.append(f"AV-conc:{av1:.0f}%")
    elif av1 is not None and av1 > 10: flags.append(f"av-conc-review:{av1:.0f}%")
    dav = rec.get("debt_to_av")                          # percent scale
    if dav is not None and dav > 12: flags.append(f"debt/AV:{dav:.0f}%")
    elif dav is not None and dav > 6: flags.append(f"debt-review:{dav:.0f}%")
    il = rec.get("issuer_litigation_flag")   # only security-reaching litigation hard-excludes (issuer_litig_hard)
    if rec.get("issuer_litig_hard"): flags.append("issuer-litigation")
    elif il in ("FLAG", "REVIEW"): flags.append("issuer-litig-review")
    ec = rec.get("enrollment_cagr_5y")                   # fraction (e.g. -0.016)
    if ec is not None and ec <= -0.04: flags.append(f"enroll-decline:{ec*100:.0f}%")
    elif ec is not None and ec <= -0.02: flags.append(f"enroll-soft:{ec*100:.0f}%")
    po = rec.get("pension_opeb_to_genfund")
    if po is not None and po >= 1.0: flags.append(f"pension:{po:.1f}x")
    elif po is not None and po >= 0.5: flags.append(f"pension-soft:{po:.1f}x")
    dscr = rec.get("dscr")
    if dscr is not None and dscr < 1.10: flags.append(f"DSCR:{dscr:.2f}x")
    elif dscr is not None and dscr < 1.25: flags.append(f"dscr-review:{dscr:.2f}x")
    if rec.get("supply_risk") == "high": flags.append("water-supply-high")
    flags += rec.get("gap_flags") or []   # small-base / reinvestment / construction / insurer-wrap — all REVIEW
    # fiscal cert (NEGATIVE/QUALIFIED), CC-uncovered, geo-unresolved, AI<floor, fire tail, near-par-call,
    # CAB, taxpayer/debt concentration, issuer litigation, water DSCR breach = hard (exclude).
    # flood / sgma / enrollment / pension = REVIEW only (levy-insulated or federally-backstopped).
    hard = [f for f in flags if f.startswith(("fiscal", "CC-sanction", "unresolved", "AI<", "FIRE-high",
            "near-par-call", "CAB", "AV-conc", "debt/AV", "issuer-litigation", "DSCR"))]
    soft = [f for f in flags if f not in hard]
    v = "FLAG" if hard else ("REVIEW" if soft else "CLEAR")
    return v, flags

def main():
    uw = {r["cusip"]: r for r in load(os.path.join(OUT, "underwriting_candidates.json"), [])}
    # water_revenue_underwrite persists to its own cache (data/water_revenue_cache.json) keyed by
    # CUSIP; overlay its revenue-underwrite fields (system_type/dscr/rate_covenant/supply_risk) onto
    # the uw record so the master picks them up (otherwise water names show 'water-not-underwritten').
    wuc = load("data/water_revenue_cache.json", {})
    for cu, wr in (wuc.items() if isinstance(wuc, dict) else []):
        if not isinstance(wr, dict):
            continue
        rec_u = uw.setdefault(cu, {"cusip": cu})
        for k in ("system_type", "dscr", "dscr_method", "rate_covenant", "supply_risk",
                  "supply_note", "supply_authority"):
            if wr.get(k) is not None:
                rec_u[k] = wr[k]
    wl = {r["cusip"]: r for r in load(os.path.join(OUT, "SCANNER_STANDING_WANTLIST.json"), [])}
    ic = {r["cusip"]: r for r in load("data/issuer_credit/issuer_credit_latest.json", [])}
    book = {x["cusip"]: x for x in load("muni_etf_sleeve_blended.json", {}).get("barbell", [])}
    avc = load("data/av_concentration_cache.json", {})   # dict keyed by cusip -> {av_total, ...} for small_base
    cusips = sorted(set(uw) | set(wl) | set(book) | set(ic))
    today = datetime.date.today().isoformat()

    master = []
    for cu in cusips:
        u = uw.get(cu, {}); w = wl.get(cu, {}); c = ic.get(cu, {}); b = book.get(cu, {})
        liq = w.get("liq") or b.get("liq") or {}
        rec = {
            "cusip": cu,
            "issuer": u.get("district") or c.get("district") or b.get("issuer") or w.get("security"),
            "county": u.get("county") or c.get("county") or b.get("county"),
            "coupon": w.get("coupon") or b.get("coupon"),
            "maturity": (w.get("maturity") or b.get("maturity") or "")[:10],
            "security": w.get("security") or b.get("security"),
            "px": w.get("px") or b.get("emma_px"),
            "ytw": w.get("ytw") or b.get("ytw"),
            "tey_aftertax": w.get("tey_aftertax") or b.get("tey_ytw_aftertax") or u.get("tey"),
            "demin_breach": w.get("demin") if w.get("demin") is not None else b.get("demin_breach"),
            # --- the three screens + credit ---
            "ai_insulation": u.get("ai_insulation") if u.get("ai_insulation") is not None else b.get("insul"),
            "fire_score": u.get("fire_score") if u.get("fire_score") is not None else b.get("fire_score"),
            "fire_tail": u.get("fire_high_share") if u.get("fire_high_share") is not None else b.get("fire_high_share"),
            "fire_worst_tract": u.get("fire_worst_tract") or b.get("fire_worst_tract"),
            "seismic_ss": (u.get("seismic_ss") if u.get("seismic_ss") is not None else c.get("seismic_ss")) if (u or c) else b.get("seismic_ss"),
            "fault_zone": u.get("fault_zone") or c.get("fault_zone") or b.get("fault_zone"),
            "credit_score": u.get("credit_score") or c.get("credit_score") or b.get("credit"),
            "cert_status": u.get("cert_status") or c.get("cert_status") or b.get("cert_status"),
            "n365": liq.get("n365"), "two_sided_days": liq.get("two_sided_days"),
            "px_spread": liq.get("px_spread"), "max_block": liq.get("max_block"),
            # --- extended screens (carried from the underwriting store) ---
            "flood_tail": u.get("flood_high_share"), "flood_worst_tract": u.get("flood_worst_tract"),
            "subsidence_flag": u.get("subsidence_flag"),
            "sgma_basin": u.get("sgma_basin"), "sgma_critical": u.get("sgma_critical"),
            "sgma_priority": u.get("sgma_priority"),
            "call_risk": u.get("call_risk"), "next_call_date": u.get("next_call_date"),
            "years_to_call": u.get("years_to_call"), "is_cab": u.get("is_cab"), "insured": u.get("insured"),
            "call_price": u.get("call_price"), "underlying_rating": u.get("underlying_rating"),
            "av_top1_taxpayer": u.get("av_top1_taxpayer"), "av_top1_share": u.get("av_top1_share"),
            "av_top10_share": u.get("av_top10_share"), "debt_to_av": u.get("debt_to_av"),
            "enrollment_cagr_5y": u.get("enrollment_cagr_5y"),
            "pension_opeb_to_genfund": u.get("pension_opeb_to_genfund"),
            "issuer_litigation_flag": u.get("issuer_litigation_flag"),
            "issuer_litig_hard": u.get("issuer_litig_hard"),
            "system_type": u.get("system_type"), "dscr": u.get("dscr"),
            "rate_covenant": u.get("rate_covenant"), "supply_risk": u.get("supply_risk"),
            "pledge": u.get("pledge") or ("water" if "water" in ((w.get("security") or b.get("security") or "")).lower() else "school"),
            "in_book": cu in book, "asof": today,
        }
        rec["hazard_tier"] = hazard_tier(rec["fault_zone"])
        # GAP screens (small-base / reinvestment / construction / insurer-wrap) — REVIEW-level, computed here
        # from the consolidated fields (the master build IS the universe pass for these).
        if GAP:
            try:
                gf, gflags = GAP.gap_screens(rec, av_total=(avc.get(cu) or {}).get("av_total"),
                                             top1_share=rec.get("av_top1_share"), insured=rec.get("insured"),
                                             underlying_rating=rec.get("underlying_rating"))
                rec.update(gf); rec["gap_flags"] = gflags
            except Exception as e:
                rec["gap_flags"] = []
        rec["uw_verdict"], rec["uw_flags"] = regrade(rec)
        master.append(rec)

    # Merge VERIFIED current-state (current-FY AV / coverage) from the continuing-disclosure refresh
    # (refresh_current_state.py). The OS-derived av_* fields above are issuance-vintage; these are current.
    # MERGE only (add fields) — never clobber the existing master record (the recurring overwrite bug).
    cs = {r["cusip"]: r for r in load(os.path.join(OUT, "CURRENT_STATE_REFRESH.json"), [])}
    n_cur = 0
    for rec in master:
        r = cs.get(rec["cusip"])
        if not r:
            continue
        if r.get("av_current"):
            rec["current_av"] = r["av_current"]; rec["current_av_fy"] = r.get("av_current_fy")
            rec["current_av_chg_pct"] = r.get("av_change_pct")
            rec["current_delinquency_pct"] = r.get("delinquency_pct"); n_cur += 1
        if r.get("dscr_current") is not None:
            rec["current_dscr"] = r["dscr_current"]; n_cur += 1
        rec["current_state_status"] = r.get("status"); rec["current_state_asof"] = r.get("refreshed")

    # Merge realized-tape LIQUIDITY + execution tier (liquidity_gate tape_metrics). Tells you which names
    # are click-to-trade self-directed (frequent two-sided + recent) vs need a desk/bid-wanted. MERGE only.
    # Merge refreshed CALL SCHEDULES (structure_screen live pull) — resolves call_risk/next_call_date.
    cal = load(os.path.join(OUT, "CALL_SCHEDULES.json"), {})
    for rec in master:
        c = cal.get(rec["cusip"])
        if c and c.get("call_price"):
            rec["call_price"] = c["call_price"]; rec["next_call_date"] = c.get("next_call_date")
            rec["call_risk"] = "callable@par"

    lt = load(os.path.join(OUT, "LIQUIDITY_TAPE.json"), {})   # {cusip: {n365, ..., execution_tier}}
    for rec in master:
        t = lt.get(rec["cusip"])
        if not t:
            continue
        rec["liq"] = {k: t.get(k) for k in ("n365", "two_sided_days", "days_since_trade", "max_block")}
        rec["execution_tier"] = t.get("execution_tier")
        rec["liq_floor_pass"] = t.get("floor_pass")
        rec["tape_asof"] = t.get("tape_asof")

    json.dump(master, open(os.path.join(OUT, "DILIGENCE_MASTER.json"), "w"), indent=1, default=str)
    # CSV for spreadsheets
    cols = ["cusip","issuer","county","coupon","maturity","px","ytw","tey_aftertax","demin_breach",
            "ai_insulation","fire_score","fire_tail","fire_worst_tract","seismic_ss","fault_zone",
            "hazard_tier","credit_score","cert_status","n365","two_sided_days","uw_verdict","in_book"]
    with open(os.path.join(OUT, "DILIGENCE_MASTER.csv"), "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); wr.writeheader()
        for r in master: wr.writerow(r)
    # summary
    v = Counter(r["uw_verdict"] for r in master)
    print(f"DILIGENCE_MASTER: {len(master)} CUSIPs consolidated | verdicts {dict(v)}")
    print(f"  with AI insul: {sum(1 for r in master if r['ai_insulation'] is not None)} | "
          f"fire: {sum(1 for r in master if r['fire_tail'] is not None)} | "
          f"EQ: {sum(1 for r in master if r['seismic_ss'] is not None)} | "
          f"credit: {sum(1 for r in master if r['credit_score'] is not None)}")
    print(f"  -> outputs/DILIGENCE_MASTER.{{json,csv}}")
    return master

if __name__ == "__main__":
    main()
