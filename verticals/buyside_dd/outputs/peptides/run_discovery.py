"""Batch discovery_state over GLP-1 secondary-effect candidates.

US-listed names get the full retail+positioning read. Foreign-primary names (Bachem, PolyPeptide,
Gerresheimer, Ypsomed) have NO US FTD/FINRA-SI feed; we run them on any US OTC/ADR ticker where one
exists, else flag the positioning layer UNVERIFIABLE and lean on attention only.
"""
import json, sys, traceback, os
sys.path.insert(0, "/Users/ajay/exalted/signalos")
from verticals.buyside_dd.connectors.discovery_state import discovery_state
from verticals.buyside_dd.connectors.latency_log import log_divergence

ASOF = "2026-06-25"

# (ticker_for_connector, company_name, divergence_type, note, shares_out_or_None)
CANDS = [
    # peptide CDMOs
    ("BANB.SW", "Bachem Holding", "peptide_cdmo_glp1_capacity", "primary CH-listed; US positioning UNVERIFIABLE", None),
    ("PPGN.SW", "PolyPeptide Group", "peptide_cdmo_glp1_capacity", "primary CH-listed", None),
    # device & containment
    ("GXI.DE",  "Gerresheimer", "primary_containment_vials_devices", "primary DE-listed", None),
    ("STVN",    "Stevanato Group", "primary_containment_glass_fillfinish", "US-listed (NYSE)", 264_000_000),
    ("WST",     "West Pharmaceutical Services", "elastomer_stoppers_devices", "US-listed (NYSE)", 72_000_000),
    ("YPSN.SW", "Ypsomed Holding", "autoinjector_pen_platform", "primary CH-listed", None),
    ("ATR",     "AptarGroup", "drug_delivery_dispensing", "US-listed (NYSE)", 66_000_000),
    # delivery / telehealth distribution
    ("HIMS",    "Hims & Hers Health", "glp1_telehealth_distribution", "US-listed (NYSE)", 222_000_000),
    # second-order picks-and-shovels surfaced
    ("AMPH",    "Amphastar Pharmaceuticals", "peptide_api_genericinjectable_glp1", "US-listed; sterile injectable + peptide API", 48_000_000),
    ("CTLT",    "Catalent", "cdmo_fillfinish_glp1", "may be private post-Novo-Holdings deal", None),
    ("MTD",     "Mettler-Toledo", "peptide_synthesis_lab_instruments", "US-listed; SPPS instruments/balances", 21_000_000),
    ("DHR",     "Danaher", "bioprocess_reagents_picksandshovels", "US-listed; bioprocess", 715_000_000),
    ("TMO",     "Thermo Fisher Scientific", "reagents_resins_cdmo_patheon", "US-listed; Patheon CDMO + reagents", 380_000_000),
    ("RGEN",    "Repligen", "bioprocessing_filtration_peptide", "US-listed; bioprocessing tools", 56_000_000),
    ("DSM",     "DSM-Firmenich", "amino_acid_specialty_inputs", "EU-listed", None),
    # demand-destruction shorts (packaged food / confection / restaurants)
    ("HSY",     "Hershey", "confection_demand_destruction_short", "US-listed", 152_000_000),
    ("MDLZ",    "Mondelez", "snack_demand_destruction_short", "US-listed", 1_300_000_000),
    ("KHC",     "Kraft Heinz", "packaged_food_demand_destruction_short", "US-listed", 1_200_000_000),
    ("CAG",     "Conagra Brands", "packaged_food_demand_destruction_short", "US-listed", 478_000_000),
    # demand-destruction: dialysis, sleep-apnea device, bariatric
    ("DVA",     "DaVita", "dialysis_demand_destruction_long_or_short", "US-listed; CKD slows -> ambiguous", 78_000_000),
    ("RMD",     "ResMed", "cpap_osa_glp1_two_sided", "US-listed; OSA approval = two-sided", 147_000_000),
    # demand-CREATION new indications
    ("VKTX",    "Viking Therapeutics", "glp1_pipeline_new_indication", "US-listed; clinical-stage GLP-1/GIP + MASH", 113_000_000),
    ("STVN2",   "PLACEHOLDER", "skip", "skip", None),
]

out = []
for tk, name, dtype, note, so in CANDS:
    if dtype == "skip":
        continue
    rec = {"ticker": tk, "company": name, "divergence_type": dtype, "note": note}
    try:
        ds = discovery_state(tk, asof=ASOF, company_name=name,
                             shares_outstanding=so, enable_options=False, enable_13f=False)
        rec.update({
            "attention_score": ds.get("attention_score"),
            "positioning_score": ds.get("positioning_score"),
            "regime": ds.get("regime"),
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
        # log every candidate to latency log
        log_divergence(tk, divergence_type=dtype, source_connector="glp1_secondary_effects_screen",
                       discovery=ds, detection_date=ASOF, extra={"note": note})
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
        rec["trace"] = traceback.format_exc()[-500:]
    out.append(rec)
    print(json.dumps({k: rec.get(k) for k in ("ticker","regime","attention_score","positioning_score","confidence","error")}))

with open("verticals/buyside_dd/outputs/peptides/discovery_results.json", "w") as f:
    json.dump(out, f, indent=2)
print("WROTE", len(out), "records")
