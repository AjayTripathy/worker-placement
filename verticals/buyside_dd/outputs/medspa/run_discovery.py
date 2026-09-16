"""Batch discovery_state over MEDSPA / aesthetics / GLP-1-telehealth candidates.

Demand-side ("upstream" consumer front-end) angle on the peptide/GLP-1 boom.
US-listed names get the full retail+positioning read. Foreign-primary names (Galderma GALD.SW)
have NO US FTD/FINRA-SI feed -> positioning layer is BLIND (positioning=0 is a missing-data
artifact, not low crowding). HARD GUARD per GXI lesson: foreign-primary -> never call UNDISCOVERED
on positioning; tag UNDISCOVERED_RETAIL_ONLY / positioning UNVERIFIABLE.
"""
import json, sys, traceback
sys.path.insert(0, "/Users/ajay/exalted/signalos")
from verticals.buyside_dd.connectors.discovery_state import discovery_state
from verticals.buyside_dd.connectors.latency_log import log_divergence

ASOF = "2026-06-25"

# (ticker, company_name, divergence_type, note, shares_out_or_None, foreign_primary)
CANDS = [
    # ---- Aesthetics injectables / devices (picks-and-shovels, GLP-1-independent demand) ----
    ("GALD.SW", "Galderma Group", "aesthetics_injectables_neurotox_filler", "primary CH-listed; Restylane/Sculptra/Daxxify; 2024 IPO", None, True),
    ("ABBV",    "AbbVie", "allergan_aesthetics_botox_juvederm", "US-listed; Allergan Aesthetics segment", 1_766_000_000, False),
    ("EOLS",    "Evolus", "neurotoxin_jeuveau_filler", "US-listed; Jeuveau + Evolysse fillers; aesthetics pure-play", 66_000_000, False),
    ("RVNC",    "Revance Therapeutics", "daxxify_neurotoxin_rha_filler", "US-listed; Daxxify + RHA; being acquired by Crown?", 113_000_000, False),
    ("INMD",    "InMode", "rf_energy_aesthetic_devices", "US/IL; RF body-contouring & aesthetic devices", 60_000_000, False),
    ("CUTR",    "Cutera", "aesthetic_lasers_distressed", "US-listed; distressed laser/energy devices", 20_000_000, False),
    ("ESTA",    "Establishment Labs", "breast_aesthetics_motiva", "US/CR; Motiva breast implants + femtech", 28_000_000, False),
    # ---- GLP-1 telehealth / consumer distribution ----
    ("HIMS",    "Hims & Hers Health", "glp1_telehealth_distribution", "US-listed; compounded-sema crackdown risk", 222_000_000, False),
    ("LFMD",    "LifeMD", "glp1_telehealth_weightmgmt", "US-listed; WeightRx/RexMD telehealth + GLP-1 programs", 47_000_000, False),
    ("TALK",    "Talkspace", "telehealth_behavioral_glp1_adjacent", "US-listed; behavioral telehealth, GLP-1 adjacency", 270_000_000, False),
    ("TDOC",    "Teladoc Health", "telehealth_chronic_weight_glp1", "US-listed; chronic-care/weight telehealth", 174_000_000, False),
    ("WW",      "WW International", "weightwatchers_glp1_telehealth_pivot", "US-listed; Sequence clinical/GLP-1 pivot (bankruptcy?)", 80_000_000, False),
    # ---- Compounding-pharmacy / supply exposure ----
    ("FFLWF",   "Fagron/other", "compounding_pharmacy_supply", "placeholder for compounder check", None, True),
]

out = []
for tk, name, dtype, note, so, foreign in CANDS:
    if dtype == "skip":
        continue
    rec = {"ticker": tk, "company": name, "divergence_type": dtype, "note": note, "foreign_primary": foreign}
    try:
        ds = discovery_state(tk, asof=ASOF, company_name=name,
                             shares_outstanding=so, enable_options=False, enable_13f=False)
        regime = ds.get("regime")
        # GXI HARD GUARD: foreign-primary -> positioning is a missing-data artifact
        if foreign and regime in ("UNDISCOVERED",):
            regime = "UNDISCOVERED_POSITIONING_UNVERIFIABLE"
        rec.update({
            "attention_score": ds.get("attention_score"),
            "positioning_score": ds.get("positioning_score"),
            "regime_raw": ds.get("regime"),
            "regime": regime,
            "confidence": ds.get("confidence"),
        })
        comp = ds.get("components", {})
        rec["src"] = {}
        for k in ("stocktwits", "wikipedia", "short_interest", "ftd", "gdelt", "google_trends"):
            v = comp.get(k, {})
            if isinstance(v, dict):
                rec["src"][k] = v.get("status", "OK") if v.get("status") else {
                    "sub": v.get("subscore"),
                    "extra": {kk: v.get(kk) for kk in ("msgs_per_day","window_saturated_sub_day","has_article","si_pct","short_interest_pct","ftd_shares") if kk in v}
                }
        log_divergence(tk, divergence_type=dtype, source_connector="medspa_demand_side_screen",
                       discovery=ds, detection_date=ASOF, extra={"note": note, "foreign_primary": foreign})
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
        rec["trace"] = traceback.format_exc()[-400:]
    out.append(rec)
    print(json.dumps({k: rec.get(k) for k in ("ticker","regime","attention_score","positioning_score","confidence","error")}))

with open("/Users/ajay/exalted/signalos/verticals/buyside_dd/outputs/medspa/discovery_results.json", "w") as f:
    json.dump(out, f, indent=2)
print("WROTE", len(out), "records")
