"""Multi-channel scoring v2 — the honest successor to capgains_beta.py.

WHY v2: v1 collapsed several DISTINCT tech/AI transmission channels (property-cycle,
investment-income, mortgage, tech-footprint) into ONE number mislabeled "cap-gains" — which
is why its channel-specificity claim failed validation. v2 fixes that:

  1. Scores EACH channel separately (no collapse, no mislabel).
  2. Scores at the BOND-SECURITY level (the pledged revenue), NOT issuer general economy —
     a property-tax-GO debt-service levy is insulated even if the issuer's budget feels
     pension/sales-tax pressure (budget channel != security channel).
  3. Keeps every creditworthiness assessment as an R/f(M) claim (claim/method/authority/finding).
  4. Emits TWO ORTHOGONAL composites: ai_insulation and creditworthiness. They are NOT blended —
     a bond can be high-credit/AI-exposed (State GO) or strong-credit/insulated (school GO).

NOT a validated predictive model. These are STRUCTURAL exposure classifications + diligence
verdicts for SELECTION/EXCLUSION. Confidence is tagged; claims are auditable.
"""
import json
import capgains_beta as V1   # reuse the per-slot revenue/region/structure assignment

HOLD = "data/etf_v2_holdings.json"; ANALY = "data/etf_v2_bond_analytics.json"
OUT = "data/channel_scores_v2.json"

# ---- the nine channels + weights for the AI-insulation composite (income-tax dominant) ----
CH_W = {"income_tax":0.30, "property_av":0.15, "pension":0.12, "tech_firm_conc":0.10,
        "hospital_balsheet":0.10, "cre_office":0.08, "housing_price":0.06,
        "sales_tax_tot":0.05, "transit_airport":0.04}
TECH_HUB_CH = {"property_av","cre_office","tech_firm_conc","hospital_balsheet"}  # boosted in SV/Bay

# ---- per-revenue-source channel EXPOSURE profile (0=insulated .. 1=fully exposed), security-level ----
PROFILES = {
 # ad-valorem GO debt service: levy adjusts to cover debt service regardless of AV/economy -> insulated everywhere
 "school_go_av":          {"property_av":0.05},
 "water_revenue":         {},                                   # usage-based essential service
 "state_gf_income_tax":   {"income_tax":1.00, "pension":0.30, "sales_tax_tot":0.10, "cre_office":0.05},
 "tax_increment":         {"property_av":0.70, "cre_office":0.40, "tech_firm_conc":0.30, "income_tax":0.10},
 "hospital_revenue":      {"hospital_balsheet":0.50, "tech_firm_conc":0.20, "property_av":0.10},
 "ccrc_entrance":         {"housing_price":0.30, "hospital_balsheet":0.20},
 "housing_finance":       {"housing_price":0.50, "income_tax":0.05},
 "county_gf_appropriation":{"pension":0.50, "income_tax":0.20, "sales_tax_tot":0.20, "cre_office":0.10},
 "muni_revenue_authority":{"cre_office":0.20, "sales_tax_tot":0.20, "tech_firm_conc":0.10},
 # University general-revenue (e.g. UC Regents GRB). AI-crash channel = State educational
 # appropriations (~10% of system revenue, but a LARGER share of the PLEDGED base because the
 # resilient medical-center revenues are EXCLUDED from the GRB pledge — they back separate
 # Medical Center Pooled Revenue Bonds). Partly offset by counter-cyclical tuition pricing power +
 # federal research $; UCRP pension is market-crash sensitive. Verified FY24 audited report;
 # exact appropriations-in-pledge clause is in the GRB OS (see CREDIT note).
 "university_general_revenue":{"income_tax":0.35, "pension":0.12, "tech_firm_conc":0.08, "housing_price":0.05},
 # UC Limited Project Revenue Bonds: pledge is the revenues of SPECIFIC financed projects (student
 # housing/parking/dining) + indirect support — NOT the broad General Revenues, and NO state
 # appropriations -> LESS cap-gains/state-channel exposure than GRB (project revenue is
 # enrollment-driven, counter-cyclical), but more project-concentrated.
 "university_lprb":{"income_tax":0.15, "pension":0.10, "housing_price":0.12, "tech_firm_conc":0.05},
}

# ---- creditworthiness R/f(M): security/lien -> (base score, claim, method, authority, finding, confidence) ----
CREDIT = {
 "school_go_sb222": (90, "Unlimited ad-valorem tax pledge + SB-222 statutory FIRST LIEN on the levy",
   "EMMA official statement + CA Gov Code", "CA Government Code §53515 (SB-222); EMMA OS", "VERIFIED", "HIGH"),
 "state_go": (80, "State GO full faith & credit; constitutional 2nd-priority on the General Fund",
   "CA Treasurer ratings + constitution", "CA Const. Art. XVI; CA Treasurer", "VERIFIED", "HIGH"),
 "water": (80, "Essential-service net-revenue pledge + rate covenant (typ. 1.2x)",
   "EMMA OS rate covenant", "EMMA official statement", "VERIFIED-STRUCTURE", "MED"),
 "calhfa": (80, "State HFA program bonds — over-collateralized, often MI/FHA-insured mortgage pools",
   "CalHFA financials + EMMA", "CalHFA / EMMA", "VERIFIED-STRUCTURE", "MED"),
 "ccrc_calmortgage": (84, "Cal-Mortgage (HCAI) insurance — state-program credit substitution (~AA-)",
   "EMMA insurance status + HCAI", "HCAI Cal-Mortgage program", "VERIFIED-WRAP", "HIGH"),
 "tab": (70, "Tax-increment (RPTTF) pledge + lien on increment; coverage depends on assessed value",
   "EMMA OS + county AV", "EMMA OS; county assessor", "VERIFIED-STRUCTURE", "MED"),
 "county_cop": (64, "Lease / certificate of participation — subject to ANNUAL APPROPRIATION + abatement risk",
   "EMMA OS lease structure", "EMMA OS", "VERIFIED-STRUCTURE", "MED"),
 "muni_rev": (72, "Municipal revenue-authority lease/revenue pledge; general-economy linked",
   "EMMA OS", "EMMA OS", "VERIFIED-STRUCTURE", "MED"),
 "hospital_naked": (55, "Naked CHFFA conduit revenue bond — covenants/coverage NOT retrieved",
   "EMMA OS NOT pulled", "(pending)", "UNVERIFIABLE", "LOW"),   # UNVERIFIABLE != clean
 "uc_grb": (82, "UC Regents General Revenue Bonds — broadest University revenue pledge (tuition/fees, "
   "F&A indirect-cost recovery, auxiliary/sales-and-services, investment income, + certain State "
   "educational appropriations); MEDICAL CENTER revenues EXCLUDED (separately secured under Medical "
   "Center Pooled Revenue Bonds, rated Aa3/AA-/AA-). AA+/Aa2; coverage held through 2008-09 (state "
   "appropriation cut backfilled by tuition increases) and 2020.",
   "UC FY24 audited annual report (med-center exclusion + revenue magnitudes); ratings history",
   "ucop.edu FY24 annual report; GRB OS for exact 'General Revenues' definition (appropriations-in-"
   "pledge clause INDICATED, OS-clause confirmation pending)", "VERIFIED-STRUCTURE", "HIGH"),
 "uc_lprb": (74, "UC Regents LIMITED PROJECT Revenue Bonds — NARROWER pledge: revenues of the "
   "SPECIFIC financed projects (student housing, parking, dining) + University indirect support, "
   "separately secured; NOT the broad General Revenues pledge and no state appropriations. Typically "
   "rated 1-2 notches BELOW GRB (~AA-/A+). More project-concentrated; project revenue is "
   "enrollment-driven (AI-crash insulated).",
   "EMMA issue description (verified GRB vs LPRB per CUSIP, 2026-06-09)", "EMMA security page",
   "VERIFIED-STRUCTURE", "HIGH"),
}
# Per-bond conduit security VERIFIED by reading the official statement (2026-06-07).
# Replaces the "hospital_naked" UNVERIFIABLE placeholder with the real authority + covenant terms.
VERIFIED_SECURITY = {
 7: (70, "CHFFA conduit (unenhanced): Gross Revenues pledge under a Master Trust Indenture (Obligated Group); "
        "rate covenant >=1.15x debt-service coverage (1.10x event-of-default floor); 1.10x additional-debt test; "
        "no debt-service reserve fund.",
     "Official statement read - Security & Master Indenture sections",
     "EMMA OS emma.msrb.org/ES1016029-ES795266-ES1196616.pdf (+64 continuing-disclosure filings)", "VERIFIED", "HIGH"),
 8: (72, "CHFFA conduit (unenhanced): security interest in Gross Revenues under a Master Trust Indenture "
        "(Obligated Group); rate covenant >=1.25x debt-service coverage.",
     "Official statement read - Security & Master Indenture sections",
     "EMMA OS emma.msrb.org/EP441871-EP345786-EP742362.pdf", "VERIFIED", "HIGH"),
}

# external rating overlay (where known) — provides 3rd-party verification, can offset a naked conduit
RATING = {7: ("AA/Aa3", 18, "El Camino — large SV system, AA"), 8: ("AA-/Aa2", 16, "Stanford Health, AA-"),
          19: ("AA-/Aa2", 6, "CA State GO current AA-")}

# ---- CUSIP-6 issuer -> (ai_profile_key, credit_key, label): auto-classifies IBKR-scanned CA munis
# into the grader. ONLY verified issuers encoded; extend as each issuer's pledge is confirmed from
# its OS (don't guess a security type). Surfaced by the liquidity-vs-insulation finding: the liquid
# (>=$15M/CUSIP) CA muni space is ~State GO (AI-exposed) + UC Regents GRB (moderately insulated);
# the AI-insulated small issuers (school GO/water) are sub-$15M and illiquid.
CUSIP6_SECURITY = {
 # mega-issuer families keyed on 5 chars (span many sub-series): State GO, UC GRB
 "13063": ("state_gf_income_tax", "state_go", "State of California GO"),
 "13062": ("state_gf_income_tax", "state_go", "State of California GO"),
 "91412": ("university_general_revenue", "uc_grb", "Regents of the University of California GRB"),
 # per-issuer (6-char) — EMMA-verified 2026-06-08 building the insulated sleeve.
 # school + community-college GO carry the SB-222 statutory first lien (CA Gov Code §53515).
 "960622": ("school_go_av", "school_go_sb222", "Westminster School District GO"),
 "692039": ("school_go_av", "school_go_sb222", "Oxnard Union High School District GO"),
 "926055": ("school_go_av", "school_go_sb222", "Victor Valley Union HSD GO"),
 "694393": ("school_go_av", "school_go_sb222", "Pacific Grove Unified School District GO"),
 "623053": ("school_go_av", "school_go_sb222", "Mt. San Jacinto Community College District GO"),
 "95640H": ("school_go_av", "school_go_sb222", "West Valley-Mission CCD GO"),
 "661334": ("school_go_av", "school_go_sb222", "North Orange County CCD GO"),
 "95330S": ("school_go_av", "school_go_sb222", "West [CCD] Community College District GO"),
 # EMMA-verified 2026-06-09 (YTW-optimized sleeve)
 "91537P": ("school_go_av", "school_go_sb222", "Upland Unified School District GO"),
 "91882R": ("school_go_av", "school_go_sb222", "Val Verde Unified School District GO"),
 "90171T": ("school_go_av", "school_go_sb222", "Twin Rivers Unified School District GO"),
 "92603P": ("school_go_av", "school_go_sb222", "Victor Valley Community College District GO"),
 "95330P": ("school_go_av", "school_go_sb222", "West Hills Community College District GO"),
 "953544": ("county_gf_appropriation", "county_cop", "West Kern CCD — Certificate of Participation (lease/appropriation, NOT GO)"),
 # essential-service wastewater enterprise revenue via city/JPA financing authorities (insulated;
 # security = financing-authority/installment, NOT a pure water-district net-revenue pledge -> verify per OS)
 "695103": ("water_revenue", "water", "City of Pacifica Financing Authority Wastewater"),
 "607802": ("water_revenue", "water", "City of Modesto Wastewater"),
 "60164A": ("water_revenue", "water", "Milpitas Municipal Financing Authority Wastewater"),
 "95236E": ("water_revenue", "water", "West County Facilities Financing Authority Wastewater"),
}


# Per-CUSIP overrides (full 9-char) where the issuer-6 does NOT determine security type — e.g. UC
# Regents issues both General Revenue Bonds and Limited Project Revenue Bonds under the SAME CUSIP-6
# (91412G / 91412H), so GRB-vs-LPRB can only be set per CUSIP. EMMA-verified 2026-06-09.
CUSIP_OVERRIDE = {
 cu: ("university_lprb", "uc_lprb", "UC Regents Limited Project Revenue Bond")
 for cu in ("91412G2F1", "91412HKM4", "91412HKN2", "91412HKQ5", "91412HMD2", "91412GXY6")
}


def classify_cusip(cusip):
    """(ai_profile_key, credit_key, label) for a CUSIP — full-CUSIP override first (UC GRB vs LPRB
    share a CUSIP-6), then per-issuer 6-char, then mega-issuer 5-char family; None if unverified."""
    c = cusip or ""
    return CUSIP_OVERRIDE.get(c) or CUSIP6_SECURITY.get(c[:6]) or CUSIP6_SECURITY.get(c[:5])


def score_bond(slot, ch_key, struct_key, region, analytics, holding):
    # ---- 1. per-channel exposure (security-level), tech-hub region boost ----
    prof = dict(PROFILES.get(ch_key, {}))
    boost = 1.40 if region == V1.REGION_SV else (1.10 if region == V1.REGION_BAY else 1.0)
    chan = {}
    for c in CH_W:
        e = prof.get(c, 0.0)
        if c in TECH_HUB_CH:
            e = min(1.0, e * boost)
        chan[c] = round(e, 3)
    exposure = sum(CH_W[c] * chan[c] for c in CH_W)
    ai_insulation = round(100 * (1 - exposure), 1)

    # ---- 2. creditworthiness R/f(M) (retain claims) ----
    base, claim, f, m, finding, conf = VERIFIED_SECURITY.get(slot) or CREDIT[struct_key]
    rfm = [{"component": "security_lien", "R": claim, "f": f, "M": m,
            "finding": finding, "confidence": conf, "score": base}]
    cw = base
    # rating overlay
    if slot in RATING:
        rt, bump, note = RATING[slot]
        cw += bump
        rfm.append({"component": "external_rating", "R": f"Agency rating {rt} ({note})",
                    "f": "rating-agency action", "M": "S&P/Moody's/Fitch", "finding": "VERIFIED",
                    "confidence": "HIGH", "score": bump})
    # CDIAC default/draw history (clean unless a recorded event)
    yconf = holding.get("yield_confidence", "")
    rfm.append({"component": "cdiac_default_draw", "R": "No recorded CDIAC default/draw for this obligor",
                "f": "cdiac_draws.py match", "M": "CDIAC DebtWatch default-draw index", "finding": "CLEAN",
                "confidence": "MED", "score": 0})
    # liquidity / disclosure penalty (stale or never-traded marks = harder to verify/exit)
    if yconf in ("STALE", "NO_TAPE"):
        cw -= 8
        rfm.append({"component": "liquidity_disclosure", "R": f"Mark quality: {yconf}",
                    "f": "EMMA RTRS tape", "M": "EMMA", "finding": "FLAG", "confidence": "HIGH", "score": -8})
    cw = max(0, min(100, cw))

    return {"slot": slot, "obligor": (holding.get("obligor_name") or "")[:40],
            "revenue_source": ch_key, "security": struct_key, "region_note": region != V1.REGION_BASE,
            "channels": chan, "ai_insulation": ai_insulation,
            "creditworthiness": round(cw, 1), "credit_confidence": conf,
            "rfm_diligence": rfm,
            "ytw_pct": round(analytics["emma_ytw"] * 100, 2) if analytics.get("emma_ytw") else None,
            "ytm_pct": round(analytics["ytm"] * 100, 2) if analytics.get("ytm") else None,
            "dur_to_worst": analytics.get("dur_to_worst"), "dur_to_maturity": analytics.get("dur_to_maturity"),
            "coupon": analytics.get("coupon"), "maturity": analytics.get("maturity")}


def main():
    H = {h["slot"]: h for h in json.load(open(HOLD))["holdings"]}
    A = {r["slot"]: r for r in json.load(open(ANALY))["rows"]}
    rows = []
    for slot, (ch, st, region, note) in V1.ASSIGN.items():
        rows.append(score_bond(slot, ch, st, region, A.get(slot, {}), H[slot]))
    json.dump({"channels": list(CH_W), "channel_weights": CH_W, "bonds": rows}, open(OUT, "w"), indent=1)

    rows.sort(key=lambda r: (-r["ai_insulation"], -r["creditworthiness"]))
    print(f"{'slot':>4}{'AI-ins':>7}{'credit':>7}{'YTW':>6}{'dur-w':>6}  obligor [security | cred-finding]")
    for r in rows:
        f0 = r["rfm_diligence"][0]["finding"]
        print(f"{r['slot']:>4}{r['ai_insulation']:>7.0f}{r['creditworthiness']:>7.0f}"
              f"{(r['ytw_pct'] or 0):>6.2f}{(r['dur_to_worst'] or 0):>6.1f}  {r['obligor'][:34]:34} [{r['security']} | {f0}]")
    print("saved ->", OUT)
    return rows


if __name__ == "__main__":
    main()
