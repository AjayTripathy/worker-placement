"""underwrite_candidates.py — full multi-risk underwrite of scanner candidates before promotion.

Composes the framework's risk overlays on every promote-ready name. BASE (always):
  EARTHQUAKE — school_go_issuer_credit.analyze(): district resolution + USGS ASCE7-22 seismic_ss + fault_zone
  FIRE       — wildfire_overlay.district_fire(): FEMA NRI building-value-weighted fire_high_share
  AI         — channel_scoring insulation by pledge (school-GO/water = insulated from State-GF cap-gains)
  FISCAL     — AB-1200 interim certification (from the credit module)
EXTENDED (full=True; 2026-06-19):
  FLOOD      — flood_overlay: NRI riverine/coastal BV tail + SJV subsidence (REVIEW; NFIP/levee-backstopped)
  SGMA       — sgma_overlay: critically-overdrafted groundwater basin = slow ag-AV-erosion tail (REVIEW)
  AV-CONC    — av_concentration: single-taxpayer % of AV + direct/overlapping debt-to-AV (FLAG/REVIEW)
  FISCAL-DEEP— fiscal_health: enrollment trend + pension/OPEB burden (REVIEW; levy-insulated)
  STRUCTURE  — structure_screen: call risk / CABs / insurance (near-par-call = hard FLAG)
  WATER      — water_revenue_underwrite: DSCR / rate covenant / supply (for revenue, non-tax bonds)
  LITIGATION — issuer_litigation: SEC-muni / FCMAT-fraud / federal-docket on the issuer (FLAG/REVIEW)

HARD flags (exclude): fiscal cert NEG/QUAL, CC-uncovered, geo-unresolved, AI<floor, fire ≥30% tail,
near-par-call, CAB, taxpayer/debt concentration, issuer litigation, water DSCR breach.
SOFT flags (REVIEW): fire 15-30%, EQ-elevated, flood, sgma, enrollment/pension, call-soon.

Usage: python3 underwrite_candidates.py            # all promote-ready in the standing want-list (full)
       python3 underwrite_candidates.py CUSIP ...  # specific names (full)
       python3 underwrite_candidates.py --cheap ... # base screens only (fast bulk cron pass)
"""
import json, os, sys, datetime
_TODAY = datetime.date.today().isoformat()
import school_go_issuer_credit as SC
import wildfire_overlay as WF
import channel_scoring_v2 as C

# Extended underwriting screens (2026-06-19). Each is a self-contained module; a broken/absent one
# must NOT kill the underwrite — it degrades to an "<x>-UNVERIFIABLE" soft note (UNVERIFIABLE != clean).
def _opt(mod):
    try: return __import__(mod)
    except Exception as e: print(f"[warn] screen module {mod} unavailable: {e}", file=sys.stderr); return None
FLOOD = _opt("flood_overlay")          # riverine/coastal flood + SJV subsidence (AV-erosion channel)
SGMA  = _opt("sgma_overlay")           # critically-overdrafted groundwater basins (ag AV-erosion)
AVC   = _opt("av_concentration")       # taxpayer concentration + direct/overlapping debt-to-AV
FISC  = _opt("fiscal_health")          # enrollment trend + pension/OPEB burden (marketability/tail)
STRUCT= _opt("structure_screen")       # call risk / CAB / insurance (structural)
WATER = _opt("water_revenue_underwrite")  # DSCR / rate-covenant / supply for revenue (non-tax) bonds
LITIG = _opt("issuer_litigation")      # issuer-level SEC/FCMAT/federal litigation
SMALLBASE = _opt("small_base")         # small/volatile tax base (few movers swing AV)
REINVEST  = _opt("reinvestment")       # reinvestment risk (when principal comes back, at what rate)
CONSTRUCT = _opt("construction_risk")  # project/completion risk (N/A for GO; revenue/lease only)
INSURER   = _opt("insurer_strength")   # bond-insurance wrap quality (rating-conditional)

import glob as _glob
def _os_text(cu):
    """Cached OS text for a CUSIP, if any: water-OS cache, top-N diligence raw, or the av-concentration
    OS-text cache. Returns '' if none (-> insurer/construction degrade to UNVERIFIABLE, never assumed)."""
    for p in ([os.path.join(HERE, "data", "_water_os", f"{cu}.layout.txt")]
              + _glob.glob(os.path.join(OUT, "diligence_reports", cu, "raw", "*.txt"))
              + [os.path.join(HERE, "data", "_os_text", f"{cu}.txt")]):
        try:
            if os.path.exists(p): return open(p, encoding="utf-8", errors="replace").read()
        except Exception: pass
    return ""

def gap_screens(rec, av_total=None, enrollment=None, top1_share=None, insured=None, underlying_rating=None):
    """The four 'prospect-framework gap' screens — all REVIEW-level. Consume already-computed inputs
    (no re-fetch): small tax base, reinvestment timing, construction/project, insurer-wrap quality."""
    F = {}; soft = []; os_text = _os_text(rec["cusip"])
    if SMALLBASE and rec.get("pledge") != "water":               # tax-base size = a GO concept
        sb, f = SMALLBASE.small_base(av_total, enrollment, top1_share); F.update(sb); soft += f
    if REINVEST:
        rv, f = REINVEST.reinvest_flag(rec); F.update(rv); soft += f
    if CONSTRUCT:
        cr, f = CONSTRUCT.construction_risk(rec.get("pledge"), rec.get("security"), os_text); F.update(cr); soft += f
    if INSURER:
        isr, f = INSURER.insurer_strength(insured, None, underlying_rating, rec.get("credit_score"), os_text)
        F.update(isr); soft += f
    return F, soft

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "outputs")
FIRE_HIGH = 0.30          # >=30% of district BV in High/Very-High wildfire tracts -> hard FLAG
FIRE_REVIEW = 0.15        # 15-30% -> REVIEW (meaningful tax-base exposure to insurer-withdrawal/AV-drag)
# FLOOD is NON-DISCRIMINATING on an absolute threshold within CA: NRI flood ratings are national
# percentiles, and developed/valley California broadly rates "Relatively High," so the whole muni
# universe sits high (median building-value share ~59%, p75 ~83% across 262 graded names — even our
# book's Central Valley names sit BELOW the universe median). An absolute cut at 15-30% flags 80-97%
# of names = noise. So flag only the EXTREME within-universe tail (top ~15%, >=p85); the SJV-specific
# subsidence flag carries the levee-corridor signal that actually discriminates. (Recalibrated 2026-06-19
# from the full-universe grade.)
FLOOD_REVIEW = 0.90       # top ~15% of the CA universe by elevated-flood building-value share
INSUL_FLOOR = 90.0        # AI insulation floor (school-GO/water should sit ~93-99)
PROFILE = {"school": "school_go_av", "water": "water_revenue"}   # AI channel-profile keys (not credit keys)

def insul_of(pk):
    p = C.PROFILES.get(pk)
    if not p: return None
    return round(100 * (1 - sum(C.CH_W[c] * p.get(c, 0) for c in C.CH_W)), 1)

# Only issuer litigation that reaches the SECURITY hard-excludes (SEC-muni enforcement, securities /
# disclosure fraud about the bonds, misuse of THIS bond's proceeds). Operating-level governance — FCMAT
# general-fund fraud, board corruption, operating embezzlement — is REVIEW: on an insured, §53515
# statutory-lien GO paid from a SEGREGATED county levy it does not reach debt service. This is the
# Stockton case: the 2023 FCMAT general-fund fraud is honestly disclosed and structurally ring-fenced,
# so the DD report correctly called it BUY/monitor — the screen must not hard-exclude it.
HARD_LITIG_CATS = {"sec_enforcement", "securities_fraud", "disclosure_violation", "bond_proceeds_misuse"}
def _litig_contribution(l):
    fields = {"issuer_litigation_flag": l.get("issuer_litigation_flag"),
              "issuer_litigation_cats": l.get("categories")}
    cats = set(l.get("categories") or [])
    hard = soft = None
    if cats & HARD_LITIG_CATS:
        fields["issuer_litig_hard"] = True
        hard = "issuer-litigation:" + ";".join(sorted(cats & HARD_LITIG_CATS))
    elif l.get("issuer_litigation_flag") in ("FLAG", "REVIEW") and cats:
        fields["issuer_litig_hard"] = False
        soft = "issuer-litig-review:" + ";".join(sorted(cats))
    return fields, hard, soft

ALL_SCREENS = {"flood", "sgma", "structure", "av_conc", "fiscal", "water", "litig"}
TIER1_SCREENS = {"flood", "sgma", "structure"}        # cheap-ish (local + one EMMA call); fast first pass
TIER2_SCREENS = {"av_conc", "fiscal", "water", "litig"}  # expensive (OS parse / CDE / RECAP-SEC) — survivors only

def run_extra_screens(r, pledge, grf=None, ftracts=None, screens=None):
    """Run the selected extended screens for one record; return (fields, hard_flags, soft_flags).
    `screens` = subset of ALL_SCREENS (default all). Each screen is wrapped so a failure surfaces as an
    UNVERIFIABLE soft note, never a silent pass. Water-pledge names take the revenue track."""
    if screens is None: screens = ALL_SCREENS
    cu = r["cusip"]; dist = r.get("district"); county = r.get("county")
    F = {}; hard = []; soft = []
    def safe(name, fn):
        try: return fn()
        except Exception as e:
            soft.append(f"{name}-UNVERIFIABLE"); return None

    # STRUCTURE — call risk / CAB applies to EVERY bond (the 926055 par-call lesson)
    if STRUCT and "structure" in screens:
        s = safe("structure", lambda: STRUCT.screen_structure(cu))
        if s:
            F.update(next_call_date=s.get("next_call_date"), years_to_call=s.get("years_to_call"),
                     call_price=s.get("call_price"), is_cab=s.get("is_cab"),
                     insured=s.get("insured"), call_risk=s.get("call_risk"))
            cr = s.get("call_risk")
            if cr == "HARD": hard.append(f"near-par-call:{s.get('next_call_date')}")
            elif cr == "SOFT": soft.append(f"call-soon:{s.get('next_call_date')}")
            elif cr == "UNVERIFIABLE" and (s.get("price") or 0) >= 100.5:
                # a PREMIUM bond whose call schedule EMMA didn't render is a possible par-call truncation
                # (the Atwater trap: bought at 100.9, par-callable in <1y -> yield collapses). Surface it.
                soft.append("premium-call-UNVERIFIABLE")
            if s.get("is_cab"): hard.append("CAB-structure")

    # WATER pledge -> revenue underwrite (DSCR/covenant/supply); skip the tax-base school screens
    if pledge == "water":
        if WATER and "water" in screens:
            w = safe("water", lambda: WATER.underwrite_water(cu))
            if w:
                F.update(system_type=w.get("system_type"), dscr=w.get("dscr"),
                         rate_covenant=w.get("rate_covenant"), customer_top_share=w.get("customer_top_share"),
                         supply_risk=w.get("supply_risk"))
                v = w.get("verdict")
                if v == "FLAG": hard.append("water:" + (";".join(w.get("flags", []) or ["FLAG"])))
                elif v == "REVIEW": soft.append("water-review")
                elif v == "UNVERIFIABLE": soft.append("water-UNVERIFIABLE")
        if LITIG and "litig" in screens and dist:          # issuer litigation still applies to water agencies
            l = safe("litig", lambda: LITIG.screen_issuer(dist, county))
            if l:
                fl, h, s = _litig_contribution(l); F.update(fl)
                if h: hard.append(h)
                if s: soft.append(s)
        return F, hard, soft

    # ---- school-GO tax-base screens ----
    # FLOOD (riverine/coastal building-value tail + SJV subsidence)
    if FLOOD and "flood" in screens and grf is not None and ftracts is not None and dist:
        f = safe("flood", lambda: FLOOD.district_flood(dist, grf, ftracts, county))
        if f and not f.get("no_flood_data"):
            F.update(flood_score=f.get("flood_score"), flood_high_share=f.get("flood_high_share"),
                     flood_worst_tract=f.get("flood_worst_tract"), subsidence_flag=f.get("subsidence_flag"))
            # FLOOD is a REVIEW signal, NOT a hard FLAG: unlike CA fire (private insurers actively
            # withdrawing -> AV drag), flood insurance has the federal NFIP backstop, the Central Valley
            # sits behind a federal levee/reservoir system, and Prop 13 keeps AV sticky. So even a high
            # riverine-flood BV tail is surfaced for review, not used to exclude the AI-insulated core.
            t = f.get("flood_high_share") or 0
            if t >= FLOOD_REVIEW: soft.append(f"flood:{t:.0%}tail")
            if f.get("subsidence_flag"): soft.append("subsidence")

    # SGMA (critically-overdrafted groundwater basin = slow AV-erosion tail -> REVIEW, not default)
    if SGMA and "sgma" in screens and (dist or county):
        g = safe("sgma", lambda: SGMA.sgma_exposure(dist, county))
        if g:
            F.update(sgma_basin=g.get("sgma_basin"), sgma_priority=g.get("sgma_priority"),
                     sgma_critical=g.get("sgma_critical"))
            if g.get("sgma_flag") == "hard": soft.append(f"sgma-overdraft:{g.get('sgma_basin')}")

    # AV / TAXPAYER CONCENTRATION + DEBT BURDEN (parse OS; cached)
    if AVC and "av_conc" in screens:
        a = safe("av_conc", lambda: (AVC.batch([cu]) or [None])[0])
        if a:
            F.update(av_top1_taxpayer=a.get("av_top1_taxpayer"), av_top1_share=a.get("av_top1_share"),
                     av_top10_share=a.get("av_top10_share"), debt_to_av=a.get("overlapping_debt_to_av"))
            d = a.get("designation")
            if d == "FLAG": hard.append("AV-conc:" + (";".join(a.get("conc_flags", []) or ["FLAG"])))
            elif d == "REVIEW": soft.append("av-conc-review:" + (";".join(a.get("conc_flags", []) or [])))
            elif a.get("confidence") == "UNVERIFIABLE": soft.append("av-conc-UNVERIFIABLE")

    # FISCAL HEALTH (enrollment + pension/OPEB) — GO is levy-insulated, so these are marketability/tail = soft
    if FISC and "fiscal" in screens and dist:
        h = safe("fiscal", lambda: FISC.fiscal_health(dist, county))
        if h:
            F.update(enrollment_cagr_5y=h.get("enrollment_cagr_5y"),
                     pension_opeb_to_genfund=h.get("pension_opeb_to_genfund"))
            # only an ACTUAL adverse reading flags (severity soft/hard); UNVERIFIABLE/info is a
            # data-coverage note, not a flag (else every name without a cached audit goes to REVIEW).
            # GO debt service is on the separate county ad-valorem levy, so cap fiscal at REVIEW (soft).
            for fl in (h.get("fiscal_flags") or []):
                if fl.get("severity") in ("soft", "hard") and fl.get("dimension") in ("enrollment", "pension_opeb"):
                    soft.append("fiscal:" + fl.get("dimension", "") + ":" + str(fl.get("reason", ""))[:48])

    # ISSUER LITIGATION / SEC / FCMAT — only security-reaching matters hard-exclude (see _litig_contribution)
    if LITIG and "litig" in screens and dist:
        l = safe("litig", lambda: LITIG.screen_issuer(dist, county))
        if l:
            fl, h, s = _litig_contribution(l); F.update(fl)
            if h: hard.append(h)
            if s: soft.append(s)

    return F, hard, soft

def zone_label(ss):
    if ss is None: return "?"
    return "ELEVATED" if ss >= 2.0 else ("moderate" if ss >= 1.0 else "low")

def underwrite(cusips, meta, screens=None):
    """`screens` selects which extended screens run (subset of ALL_SCREENS; default all). Pass an empty
    set for base-only (fire/EQ/AI/cert) — the fast cron pass. TIER1_SCREENS / TIER2_SCREENS are presets."""
    if screens is None: screens = ALL_SCREENS
    recs = SC.analyze(cusips)                          # credit + EARTHQUAKE (seismic_ss, fault_zone)
    tracts = WF.load_tracts(); grf = WF.load_grf_ca()
    ftracts = FLOOD.load_tracts() if (FLOOD and "flood" in screens) else None
    for r in recs:
        cu = r["cusip"]
        # SC.analyze flags revenue/utility bonds (sewer/water/financing-authority) -> water track, overriding
        # any want-list "school GO" mislabel (the Tulare sewer-bond case).
        pledge = "water" if (r.get("is_revenue") or r.get("pledge") == "water") else meta.get(cu, {}).get("pledge", "school")
        # FIRE
        r["fire_high_share"] = None
        if r.get("district") and r.get("cert_status") != "UNRESOLVED":
            f = WF.district_fire(r["district"], grf, tracts)
            if f: r.update(f)
        # AI insulation by pledge type
        r["ai_insulation"] = insul_of(PROFILE.get(pledge, "school_go_av")) if PROFILE.get(pledge) else None
        r["tey"] = meta.get(cu, {}).get("tey")
        # ---- BASE flags (fire / EQ / AI / cert) — hard vs soft tracked explicitly ----
        hard, soft = [], []
        r["pledge"] = pledge
        cs = r.get("cert_status")
        # The cert / CC / geo-resolution / fire screens are SCHOOL-DISTRICT-specific. A water/wastewater
        # REVENUE bond has no school district, so the school resolver correctly returns UNRESOLVED — that's
        # N/A, not a flag. Water names are graded by the revenue track (DSCR/supply/customer) instead.
        if pledge == "water":
            if (cs or "").startswith("UNRESOLVED"): r["cert_status"] = "N/A-REVENUE"
        else:
            ch, cs_soft = SC.cert_contribution(cs)           # cert + CCD-accreditation severity (shared)
            hard += ch; soft += cs_soft
            tail = r.get("fire_high_share")
            if tail is None and r.get("district"): soft.append("fire-unmatched")
            elif (tail or 0) >= FIRE_HIGH: hard.append(f"FIRE-high:{tail:.0%}")
            elif (tail or 0) >= FIRE_REVIEW: soft.append(f"fire-review:{tail:.0%}tail")
        if (r.get("ai_insulation") or 100) < INSUL_FLOOR: hard.append(f"AI-insul<{INSUL_FLOOR:.0f}")
        if (r.get("seismic_ss") or 0) >= 2.0: soft.append(f"EQ-elevated:{r['seismic_ss']:.2f}")
        # ---- EXTENDED screens ----
        if screens:
            xf, xh, xs = run_extra_screens(r, pledge, grf, ftracts, screens)
            r.update(xf); hard += xh; soft += xs
        r["uw_flags"] = hard + soft
        r["uw_hard"], r["uw_soft"] = hard, soft
        r["uw_verdict"] = "FLAG" if hard else ("REVIEW" if soft else "CLEAR")
        r["screened_asof"] = _TODAY                               # any-tier resume stamp
        if "av_conc" in screens: r["deep_asof"] = _TODAY          # tier-2-specific stamp (OS-parse actually ran)
    return recs

def main():
    args = sys.argv[1:]
    # --cheap = base only; --tier1 = +flood/sgma/structure; default = all extended screens
    screens = set() if "--cheap" in args else (TIER1_SCREENS if "--tier1" in args else ALL_SCREENS)
    args = [a for a in args if not a.startswith("--")]
    wl = json.load(open(os.path.join(OUT, "SCANNER_STANDING_WANTLIST.json")))
    by = {r["cusip"]: r for r in wl}
    cusips = args or [r["cusip"] for r in wl]
    meta = {cu: {"pledge": ("water" if "water" in (by.get(cu, {}).get("security", "").lower()) else "school"),
                 "tey": by.get(cu, {}).get("tey_aftertax")} for cu in cusips}
    recs = underwrite(cusips, meta, screens=screens)
    # MERGE into the stored underwriting (do NOT overwrite — a partial run must keep prior names).
    p = os.path.join(OUT, "underwriting_candidates.json")
    try: prior = {r["cusip"]: r for r in json.load(open(p))}
    except Exception: prior = {}
    for r in recs: prior[r["cusip"]] = r
    recs = list(prior.values())
    json.dump(recs, open(p, "w"), indent=1, default=str)

    recs.sort(key=lambda r: (0 if r["uw_verdict"] == "CLEAR" else 1, -(r.get("tey") or 0)))
    L = ["# Candidate Underwriting — multi-risk (hazard × structure × tax-base × governance)", "",
         "_Base: EARTHQUAKE (USGS ASCE7-22 Ss + fault zone), FIRE (FEMA NRI High/Very-High BV tail, hard ≥30%), "
         "AI insulation by pledge, AB-1200 fiscal cert. Extended: FLOOD (NRI riverine/coastal tail + subsidence, "
         "REVIEW), SGMA (critically-overdrafted basin, REVIEW), AV/taxpayer concentration + debt-to-AV, structure "
         "(near-par-call / CAB / insurance), fiscal-deep (enrollment + pension/OPEB), water-revenue DSCR/covenant/"
         "supply, and issuer litigation (SEC/FCMAT/federal). CLEAR = promotion-ready; UNVERIFIABLE ≠ clean._", "",
         "| CUSIP | District (County) | TEY | Credit/Cert | EQ Ss (zone) | Fire hi-BV% | AI insul | Verdict | Flags |",
         "|---|---|---|---|---|---|---|---|---|"]
    nclear = 0
    for r in recs:
        if r["uw_verdict"] == "CLEAR": nclear += 1
        fh = f"{100*r['fire_high_share']:.0f}%" if r.get("fire_high_share") is not None else "—"
        ss = f"{r['seismic_ss']:.2f} ({zone_label(r.get('seismic_ss'))})" if r.get("seismic_ss") is not None else "—"
        tey = f"{r['tey']*100:.2f}%" if r.get("tey") else "—"
        dist = f"{r.get('district') or '?'} ({r.get('county') or '?'})"
        L.append(f"| {r['cusip']} | {dist} | {tey} | {r.get('credit_score','?')}/{r.get('cert_status','?')} "
                 f"| {ss} | {fh} | {r.get('ai_insulation','—')} | {r['uw_verdict']} | {'; '.join(r['uw_flags']) or '—'} |")
    L.insert(5, f"\n**{nclear}/{len(recs)} CLEAR** (all three overlays + fiscal cert pass). Rest are FLAG/REVIEW — see flags.\n")
    open(os.path.join(OUT, "UNDERWRITING_CANDIDATES.md"), "w").write("\n".join(L))
    print("\n".join(L[:8]))
    print(f"\n... wrote outputs/UNDERWRITING_CANDIDATES.md ({nclear}/{len(recs)} CLEAR)")

if __name__ == "__main__":
    main()
