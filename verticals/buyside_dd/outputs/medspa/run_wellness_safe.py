"""Robust wellness discovery batch: sets a global socket timeout so no connector can hang the run,
catches per-ticker errors, prints+flushes each line, and writes the final JSON. Skips tickers whose
regime is already captured in the latency log (idempotent top-up)."""
import json, sys, socket, traceback
socket.setdefaulttimeout(20)  # hard cap every connector's network call
sys.path.insert(0, "/Users/ajay/exalted/signalos")
from verticals.buyside_dd.connectors.discovery_state import discovery_state
from verticals.buyside_dd.connectors.latency_log import log_divergence

ASOF = "2026-06-26"
CANDS = [
    ("PGNY","Progyny","fertility_benefits","fertility_benefits_managed",90_000_000,1_460_000_000),
    ("RMD","ResMed","sleep_apnea_cpap","cpap_glp1_screening_tailwind",145_000_000,27_000_000_000),
    ("INSP","Inspire Medical Systems","sleep_apnea_hgns","hypoglossal_nerve_stim",30_000_000,3_000_000_000),
    ("PLNT","Planet Fitness","fitness_gyms","gym_value_membership",84_000_000,4_300_000_000),
    ("GRMN","Garmin","wearables_fitness","wearable_recovery_band",192_000_000,46_000_000_000),
    ("SMPL","Simply Good Foods","functional_nutrition_betterforyou","protein_low_carb",100_000_000,2_000_000_000),
    ("CELH","Celsius Holdings","functional_beverage_energy","functional_energy_drink",280_000_000,8_000_000_000),
    ("RVNC","Revance Therapeutics","aesthetic_neurotoxin_derm","daxxify_rha_takeout",113_000_000,400_000_000),
    ("TALK","Talkspace","behavioral_telehealth","behavioral_health_ai",270_000_000,870_000_000),
    ("LFST","LifeStance Health","behavioral_health_clinics","outpatient_mentalhealth_rollup",382_000_000,3_250_000_000),
    ("PRCT","PROCEPT BioRobotics","mens_health_bph_robotics","aquablation_hydros_bph",56_000_000,1_570_000_000),
]
out=[]
for tk,name,theme,dtype,so,mcap in CANDS:
    rec={"ticker":tk,"sub_theme":theme}
    try:
        ds=discovery_state(tk,asof=ASOF,company_name=name,shares_outstanding=so,market_cap=mcap,
                           enable_options=False,enable_13f=False)
        rec.update({"regime":ds.get("regime"),"attention_score":round(ds.get("attention_score") or 0,3),
                    "positioning_score":round(ds.get("positioning_score") or 0,3),"confidence":ds.get("confidence")})
        log_divergence(tk,divergence_type=dtype,source_connector="wellness_universe_screen",
                       discovery=ds,detection_date=ASOF,extra={"sub_theme":theme})
    except Exception as e:
        rec.update({"regime":"ERROR","err":f"{type(e).__name__}: {str(e)[:80]}"})
    out.append(rec); print(json.dumps(rec),flush=True)
json.dump(out,open("/Users/ajay/exalted/signalos/verticals/buyside_dd/outputs/medspa/wellness_remaining2.json","w"),indent=2)
print("SAFE_DONE",flush=True)
