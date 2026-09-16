"""Conditioning-layer (discovery_state) batch over the WELLNESS/HEALTHSPAN candidate universe.

Book started in medical aesthetics; broadening to general wellness/healthspan. This screens the NEW
sub-theme candidates (GLP-1 adjacencies, longevity diagnostics, hormone, femtech, sleep, wearables,
nutrition, derm/hair, behavioral, medspa rollups) through the NO-EDGE control layer to tag each
UNDISCOVERED vs DISCOVERING vs DISCOVERED_CROWDED, and log every row to latency_log.jsonl.

Foreign-primary HARD GUARD (GXI lesson): no US FINRA-SI / SEC-FTD feed -> positioning is a
missing-data artifact, NOT low crowding. Never call foreign-primary UNDISCOVERED on positioning.
"""
import json, sys, traceback
sys.path.insert(0, "/Users/ajay/exalted/signalos")
from verticals.buyside_dd.connectors.discovery_state import discovery_state
from verticals.buyside_dd.connectors.latency_log import log_divergence

ASOF = "2026-06-26"

# (ticker, company, sub_theme, divergence_type, shares_out_or_None, market_cap_or_None, foreign_primary)
CANDS = [
    # 1. GLP-1 ecosystem adjacencies
    ("HIMS", "Hims & Hers Health", "glp1_telehealth_distribution", "glp1_telehealth_branded_pivot", 222_000_000, 7_000_000_000, False),
    ("TDOC", "Teladoc Health", "glp1_telehealth_chronic", "telehealth_weight_chroniccare", 174_000_000, 1_700_000_000, False),
    ("WST",  "West Pharmaceutical Services", "glp1_picks_shovels_injectable", "glp1_elastomer_autoinjector_supply", 72_000_000, 22_000_000_000, False),
    ("DXCM", "Dexcom", "cgm_metabolic_wellness", "cgm_otc_stelo_wellness", 390_000_000, 30_000_000_000, False),
    ("VERU", "Veru Inc", "glp1_muscle_preservation", "enobosarm_sarm_muscle_glp1", 150_000_000, 250_000_000, False),
    ("BRBR", "BellRing Brands", "glp1_nutrition_protein", "premier_protein_rtd_glp1_nutrition", 130_000_000, 8_000_000_000, False),
    # 2. Longevity / preventive diagnostics
    ("FN_HEALTH", "Function Health (private)", "longevity_diagnostics_private", "private_no_listing", None, None, False),
    # 3. Hormone health
    ("OGN",  "Organon", "womens_health_menopause_hrt", "menopause_hrt_takeout", 256_000_000, 3_500_000_000, False),
    # 4. Women's health & fertility
    ("PGNY", "Progyny", "fertility_benefits", "fertility_benefits_managed", 90_000_000, 1_460_000_000, False),
    # 5. Sleep & recovery
    ("RMD",  "ResMed", "sleep_apnea_cpap", "cpap_glp1_screening_tailwind", 145_000_000, 27_000_000_000, False),
    ("INSP", "Inspire Medical Systems", "sleep_apnea_hgns", "hypoglossal_nerve_stim", 30_000_000, 3_000_000_000, False),
    # 6. Fitness / wearables / metabolic tracking
    ("PLNT", "Planet Fitness", "fitness_gyms", "gym_value_membership", 84_000_000, 4_300_000_000, False),
    ("GRMN", "Garmin", "wearables_fitness", "wearable_recovery_band", 192_000_000, 40_000_000_000, False),
    # 7. Functional nutrition / supplements
    ("SMPL", "Simply Good Foods", "functional_nutrition_betterforyou", "protein_low_carb_atkins_quest", 100_000_000, 3_000_000_000, False),
    ("CELH", "Celsius Holdings", "functional_beverage_energy", "functional_energy_drink", 280_000_000, 10_000_000_000, False),
    # 8. Skin / derm / beauty & hair
    ("RVNC", "Revance Therapeutics", "aesthetic_neurotoxin_derm", "daxxify_rha_takeout", 113_000_000, 400_000_000, False),
    # 9. Mental & behavioral health
    ("TALK", "Talkspace", "behavioral_telehealth", "behavioral_health_ai", 270_000_000, 870_000_000, False),
    ("LFST", "LifeStance Health", "behavioral_health_clinics", "outpatient_mentalhealth_rollup", 382_000_000, 3_250_000_000, False),
    # Men's health device
    ("PRCT", "PROCEPT BioRobotics", "mens_health_bph_robotics", "aquablation_hydros_bph", 56_000_000, 1_570_000_000, False),
]

out = []
for tk, name, theme, dtype, so, mcap, foreign in CANDS:
    rec = {"ticker": tk, "company": name, "sub_theme": theme, "divergence_type": dtype,
           "market_cap": mcap, "foreign_primary": foreign}
    if tk in ("FN_HEALTH",):
        rec["regime"] = "PRIVATE_NO_LISTING"
        out.append(rec); print(json.dumps({k: rec.get(k) for k in ("ticker","regime")})); continue
    try:
        ds = discovery_state(tk, asof=ASOF, company_name=name, shares_outstanding=so,
                             market_cap=mcap, enable_options=False, enable_13f=False)
        regime = ds.get("regime")
        if foreign and regime == "UNDISCOVERED":
            regime = "UNDISCOVERED_POSITIONING_UNVERIFIABLE"
        rec.update({"attention_score": ds.get("attention_score"),
                    "positioning_score": ds.get("positioning_score"),
                    "regime_raw": ds.get("regime"), "regime": regime,
                    "confidence": ds.get("confidence")})
        comp = ds.get("components", {})
        rec["src"] = {}
        for k in ("stocktwits", "wikipedia", "short_interest", "ftd", "gdelt", "google_trends"):
            v = comp.get(k, {})
            if isinstance(v, dict):
                rec["src"][k] = v.get("status") or {kk: v.get(kk) for kk in
                    ("msgs_per_day","window_saturated_sub_day","si_pct","short_interest_pct",
                     "ftd_shares","max_daily_fails","recent_vs_baseline","subscore") if kk in v}
        log_divergence(tk, divergence_type=dtype, source_connector="wellness_universe_screen",
                       discovery=ds, detection_date=ASOF,
                       extra={"sub_theme": theme, "foreign_primary": foreign})
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
        rec["trace"] = traceback.format_exc()[-300:]
    out.append(rec)
    print(json.dumps({k: rec.get(k) for k in
        ("ticker","regime","attention_score","positioning_score","confidence","error")}))

with open("/Users/ajay/exalted/signalos/verticals/buyside_dd/outputs/medspa/wellness_discovery_results.json", "w") as f:
    json.dump(out, f, indent=2)
print("WROTE", len(out), "records")
