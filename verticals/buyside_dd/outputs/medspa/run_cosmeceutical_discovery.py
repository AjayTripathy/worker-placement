"""Batch discovery_state over the COSMECEUTICAL sleeve candidates.

Cosmeceutical-specific demand thesis (NOT GLP-1): skinification / derm-recommendation moat /
active-ingredient arms race / pro-medical channel / DTC-with-owned-formulation.

US-listed names get the full retail+positioning read. Foreign-primary names (OR.PA, BEI.DE,
4911.JP, GIVN.SW, SY1.DE, DSFIR.AS, CRDA.L, HONASA.NS) have NO US FTD/FINRA-SI feed -> positioning
layer is BLIND. HARD GUARD (GXI lesson): foreign-primary -> never call UNDISCOVERED on positioning;
tag UNDISCOVERED_POSITIONING_UNVERIFIABLE.
"""
import json, sys, traceback
sys.path.insert(0, "/Users/ajay/exalted/signalos")
from verticals.buyside_dd.connectors.discovery_state import discovery_state
from verticals.buyside_dd.connectors.latency_log import log_divergence

ASOF = "2026-06-26"

# (ticker, company_name, divergence_type, note, shares_out_or_None, foreign_primary)
CANDS = [
    # ---- Sub-seg 1: prestige/mass beauty with derm credibility ----
    ("EL",    "Estee Lauder", "premium_skincare_science_turnaround", "La Mer/Re-Nutriv longevity science; turnaround", 360_000_000, False),
    ("LRLCY", "L'Oreal ADR", "dermatological_beauty_compounder", "Active Cosmetics: CeraVe/LRP/SkinCeuticals/Vichy", None, True),
    ("BEISY", "Beiersdorf ADR", "derma_eucerin_thiamidol_compounder", "Eucerin/Aquaphor Derma +8-12% organic", None, True),
    ("SSDOY", "Shiseido ADR", "drunk_elephant_impairment_value_trap", "DE underperforming, impairment risk", None, True),
    ("KVUE",  "Kenvue", "neutrogena_aveeno_takeout_pending", "being acquired by Kimberly-Clark 2H26", 1_900_000_000, False),
    ("COTY",  "Coty", "prestige_skincare_levered_turnaround", "Lancaster/philosophy skincare; $3.4B debt", 860_000_000, False),
    # ---- Sub-seg 2: DTC / tech cosmeceutical ----
    ("ODD",   "Oddity Tech", "biotech_actives_dtc_owned_formulation", "Oddity Labs molecule-discovery; Il Makiage/SpoiledChild", 57_000_000, False),
    ("ELF",   "e.l.f. Beauty", "skinification_mix_shift_skincare", "skincare 9->23% of consumption; Naturium/Rhode", 57_000_000, False),
    ("HONASA.NS","Honasa Consumer", "india_dtc_mamaearth_skincare", "India DTC; foreign+illiquid for US SMA", None, True),
    # ---- Sub-seg 3: ingredient picks-and-shovels ----
    ("CRDA.L","Croda International", "beauty_actives_picks_shovels", "Consumer Care Beauty Actives; UK-listed", None, True),
    ("GIVN.SW","Givaudan", "active_beauty_diluted_by_FF", "Active Beauty small vs F&F; CH-listed", None, True),
    ("SY1.DE","Symrise", "cosmetic_actives_microbiome", "Scent&Care cosmetic ingredients; DE-listed", None, True),
    ("DSFIR.AS","DSM-Firmenich", "personal_care_actives_clinical", "personal-care actives; NL-listed", None, True),
    ("ASH",   "Ashland", "biofunctional_skincare_actives_turnaround", "biofunctional actives but diluted/levered", 47_000_000, False),
    ("SXT",   "Sensient", "personal_care_color_minor_exposure", "cosmetic colors minor vs food", 42_000_000, False),
    ("CDXS",  "Codexis", "enzyme_biocatalysis_NOT_cosmetic", "pharma enzymes; NOT a cosmetic-actives play", 80_000_000, False),
    # ---- Sub-seg 4: professional / haircare cosmeceutical ----
    ("SKIN",  "Beauty Health (SkinHealth Systems)", "hydrafacial_pro_channel_microcap_turnaround", "HydraFacial pro device/consumable; microcap", 125_000_000, False),
    ("NUS",   "Nu Skin", "direct_selling_skincare_device_distressed", "Prysm iO device; structural DS decline", 50_000_000, False),
    ("OLPX",  "Olaplex", "bondbuilding_haircare_takeout_dead", "Henkel takeout $2.06 closing ~Jul-1", 660_000_000, False),
]

out = []
for tk, name, dtype, note, so, foreign in CANDS:
    rec = {"ticker": tk, "company": name, "divergence_type": dtype, "note": note, "foreign_primary": foreign}
    try:
        ds = discovery_state(tk, asof=ASOF, company_name=name,
                             shares_outstanding=so, enable_options=False, enable_13f=False)
        regime = ds.get("regime")
        if foreign and regime == "UNDISCOVERED":
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
                rec["src"][k] = v.get("status") or {
                    "sub": v.get("subscore"),
                    "extra": {kk: v.get(kk) for kk in ("msgs_per_day","has_article","si_pct","short_interest_pct","ftd_shares") if kk in v}
                }
        log_divergence(tk, divergence_type=dtype, source_connector="cosmeceutical_sleeve_screen",
                       discovery=ds, detection_date=ASOF, extra={"note": note, "foreign_primary": foreign})
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
        rec["trace"] = traceback.format_exc()[-300:]
    out.append(rec)
    print(json.dumps({k: rec.get(k) for k in ("ticker","regime","attention_score","positioning_score","confidence","error")}))

with open("/Users/ajay/exalted/signalos/verticals/buyside_dd/outputs/medspa/cosmeceutical_discovery_results.json", "w") as f:
    json.dump(out, f, indent=2)
print("WROTE", len(out), "records")
