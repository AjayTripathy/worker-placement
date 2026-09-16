"""LIVE (forward-looking) catalyst cohort — H2 2026 readouts/decisions.

Unlike the sealed backtest in catalyst_spec.py, these catalysts have NOT yet
resolved, so there is no outcome and no _sealed_outcomes entry. This is the
framework run in LIVE PREDICTION mode: cutoff = today (2026-06-01), corpus =
every pre-cutoff marketing exhibit. The honesty screen emits an EXCLUDE / ELEVATED
/ CLEAN call on each name BEFORE the catalyst prints.

Kept in a separate module + dict (LIVE_CASES) so the sealed scoring path never
touches them. The corpus (EDGAR) and M-layer (CT.gov) stages need no API credits;
only extract_claims / evaluate / adjudicate do.

NCT bindings: filled where a source tied a specific registered trial to the
upcoming readout. Per [[catalyst-identity-binding]], a name with nct_ids=() must
have its catalyst trial bound (against company guidance) BEFORE evaluate is run —
corpus + claim extraction do not require it. catalyst_type 'pdufa' marks a
regulatory decision (weaker fit for the trial-topline masking channels).
"""
from __future__ import annotations

from .catalyst_spec import CatalystCase

LIVE_CUTOFF = "2026-06-01"
WINDOW_START = "2024-06-01"  # 24-month marketing window to bound corpus size

# (case_id, company, ticker, cik, program, indication, nct_ids, catalyst_type, notes)
_SPECS: list[tuple] = [
    # ── Clinical pivotal / registrational readouts (best framework fits) ──
    ("live_amlx_avexitide_lucidity", "Amylyx Pharmaceuticals, Inc.", "AMLX", "0001658551",
     "avexitide", "post-bariatric hypoglycemia", ("NCT06747468",), "phase3_topline", "LUCIDITY; Q3 2026 (HIGH)"),
    ("live_alms_envudeucitinib_lumus", "Alumis Inc.", "ALMS", "0001847367",
     "envudeucitinib (ESK-001, TYK2)", "systemic lupus erythematosus", ("NCT05966480",), "phase2b_topline", "LUMUS; Q3 2026 (HIGH)"),
    ("live_syre_spy072_skyway", "Spyre Therapeutics, Inc.", "SYRE", "0001636282",
     "SPY072 (anti-TL1A)", "rheumatoid arthritis / PsA / axSpA", ("NCT07148414",), "phase2_topline",
     "SKYWAY; RA Q3, PsA/axSpA Q4 2026 (HIGH)"),
    ("live_cytk_aficamten_acacia", "Cytokinetics, Incorporated", "CYTK", "0001061983",
     "aficamten (CK-3773274)", "symptomatic non-obstructive hypertrophic cardiomyopathy (nHCM)",
     ("NCT06081894",), "phase3_topline",
     "ACACIA-HCM Ph3 nHCM (aficamten vs placebo, NCT06081894). FORWARD-LEAKED: topline "
     "reported 2026-05-05 (POSITIVE, both dual primaries hit — KCCQ-CSS +3.0 p=0.021, "
     "pVO2 +0.67 p=0.003), 4 wk before cutoff; the readout 8-K is in the pre-cutoff corpus. "
     "Distinct from SEQUOIA-HCM/MAPLE-HCM (obstructive HCM)."),
    ("live_smmt_ivonescimab_harmoni3", "Summit Therapeutics Inc.", "SMMT", "0001599298",
     "ivonescimab", "1L squamous metastatic NSCLC", ("NCT05899608",), "phase3_topline",
     "HARMONi-3 SQ cohort; 2H 2026 PFS + interim OS (HIGH)"),
    ("live_olma_palazestrant_opera1", "Olema Pharmaceuticals, Inc.", "OLMA", "0001750284",
     "palazestrant (OP-1250)", "ER+/HER2- breast cancer (2L/3L)", ("NCT06016738",), "phase3_topline",
     "OPERA-01; Fall 2026 (HIGH)"),
    ("live_imcr_tebentafusp_tebeam", "Immunocore Holdings plc", "IMCR", "0001671927",
     "tebentafusp (KIMMTRAK)", "2L+ cutaneous melanoma", ("NCT05549297",), "phase3_topline", "TEBE-AM; 2H 2026 (HIGH)"),
    ("live_imvt_imvt1402_ra", "Immunovant, Inc.", "IMVT", "0001764013",
     "IMVT-1402 (anti-FcRn)", "difficult-to-treat rheumatoid arthritis", ("NCT06754462",), "phase2_topline",
     "RA Ph2 (sole IMVT-1402 RA trial); pcd 2027-09 (catalyst is an interim); 2H 2026 (HIGH)"),
    ("live_rare_gtx102_aspire", "Ultragenyx Pharmaceutical Inc.", "RARE", "0001515673",
     "GTX-102 (apazunersen)", "Angelman syndrome", ("NCT06617429",), "phase3_topline", "Aspire; 2H 2026 (HIGH)"),
    ("live_hrmy_pitolisant_tempo", "Harmony Biosciences Holdings, Inc.", "HRMY", "0001802665",
     "pitolisant", "Prader-Willi syndrome (EDS)", ("NCT06366464",), "phase3_topline",
     "TEMPO Ph3 PWS (pitolisant vs placebo, n=134, pcd 2026-07); 2H 2026 (HIGH). Was bogus NCT06478394."),
    ("live_bhvn_opakalim_epilepsy", "Biohaven Ltd.", "BHVN", "0001935979",
     "opakalim (BHV-7000)", "refractory focal epilepsy", ("NCT06132893", "NCT06309966"), "phase2_3_topline",
     "RISE 2/RISE 3 pivotal; 2H 2026 (HIGH)"),
    ("live_vtvt_cadisegliatin_catt1", "vTv Therapeutics Inc.", "VTVT", "0001641489",
     "cadisegliatin", "type 1 diabetes", ("NCT06334133",), "phase3_topline", "CATT1; 2H 2026 (HIGH)"),
    ("live_iva_lanifibranor_nativ3", "Inventiva S.A.", "IVA", "0001756594",
     "lanifibranor", "MASH (F2/F3 fibrosis)", ("NCT04849728",), "phase3_topline",
     "NATiV3 Ph3 NASH/MASH (IVA337 vs placebo, n=1000); 2H 2026 (HIGH; FR ADS)"),
    ("live_imux_vidofludimus_ensure", "Immunic, Inc.", "IMUX", "0001280776",
     "vidofludimus calcium (IMU-838)", "relapsing multiple sclerosis", ("NCT05134441", "NCT05201638"), "phase3_topline",
     "ENSURE-1/2; by EOY 2026 (HIGH)"),
    ("live_abvx_obefazimod_abtect", "Abivax SA", "ABVX", "0001956827",
     "obefazimod", "ulcerative colitis (maintenance)", ("NCT05535946",), "phase3_topline",
     "ABTECT-Maintenance Ph3 UC (ABX464/obefazimod, n=1116, pcd 2026-04); 2H 2026 (MED; FR ADS)"),
    ("live_annx_anx007_archer2", "Annexon, Inc.", "ANNX", "0001528115",
     "vonaprument (ANX007)", "geographic atrophy (dry AMD)", ("NCT06510816",), "phase3_topline",
     "ARCHER II; Q4 2026 (HIGH). NOTE: ANX007 ARCHER-I was a sealed-cohort MISS."),
    ("live_avir_bemnifosbuvir_cforward", "Atea Pharmaceuticals, Inc.", "AVIR", "0001593899",
     "bemnifosbuvir + ruzasvir", "hepatitis C (HCV)", ("NCT07037277",), "phase3_topline",
     "C-FORWARD; year-end 2026 (HIGH). Same combo as sealed atea_hcv_combo_p2 HIT."),
    ("live_pcvx_vax31_opus1", "Vaxcyte, Inc.", "PCVX", "0001649094",
     "VAX-31", "invasive pneumococcal disease (adults)", ("NCT07284654",), "phase3_topline", "VAX31-103/OPUS-1; Q4 2026 (HIGH)"),
    ("live_cldx_barzolvolimab_csu", "Celldex Therapeutics, Inc.", "CLDX", "0000744218",
     "barzolvolimab", "chronic spontaneous urticaria", ("NCT06455202",), "phase3_topline",
     "EMBARQ-CSU1/CSU2; Q4 2026 (HIGH)"),
    ("live_zbio_obexelimab_sunstone", "Zenas BioPharma, Inc.", "ZBIO", "0001953926",
     "obexelimab", "systemic lupus erythematosus", ("NCT06559163",), "phase2_topline", "SunStone; Q4 2026 (HIGH)"),
    ("live_adct_zynlonta_lotis5", "ADC Therapeutics SA", "ADCT", "0001771910",
     "ZYNLONTA (loncastuximab tesirine) + rituximab",
     "relapsed/refractory DLBCL (2L+, ASCT-ineligible)", ("NCT04384484",), "phase3_topline",
     "LOTIS-5 Ph3 confirmatory (lonca+rituximab vs R-GemOx, N=440, PFS ~262 events, pcd "
     "2026-03-31); topline 2Q 2026 (HIGH) — confirmatory trial for ZYNLONTA accelerated "
     "approval. Rebound from LOTIS-7 Ph1b after verify_finding caught a severe finding "
     "mis-bound across phase/endpoint/regimen axes. LOTIS-7 (NCT04970901, lonca+glofitamab) "
     "is a separate, later catalyst (full data EOY 2026)."),
    ("live_sls_gps_regal", "SELLAS Life Sciences Group, Inc.", "SLS", "0001390478",
     "galinpepimut-S (GPS, WT1 peptide immunotherapy)",
     "acute myeloid leukemia (2nd complete remission maintenance)", ("NCT04229979",), "phase3_topline",
     "REGAL Ph3 (GPS vs investigator's choice of best available therapy in AML CR2, n~125, "
     "primary=overall survival). Event-driven: final OS analysis triggers at 80 events. Per the "
     "2026-05-12 8-K, 78/80 events had occurred as of 2026-05-11 and SELLAS REMAINS BLINDED — the "
     "final OS topline is imminent and UNREAD. INTERIM-LEAK ACKNOWLEDGED (run allow_leak=True): the "
     "Mar/May-2025 8-Ks announce a POSITIVE INTERIM ANALYSIS outcome (IDMC futility/efficacy/safety "
     "review → continue without modification), which the leak pre-flight flags. That interim is NOT "
     "the binary catalyst — the trial continued to the 80-event final OS analysis, which has not "
     "read out and on which the stock has not repriced. Final analysis originally guided year-end "
     "2025, slipped to mid-2026. Distinct from SLS009 (tambiciclib) Ph2 NCT04588922, a separate "
     "earlier-stage AML catalyst reading out ~EOY 2026."),
    ("live_rare_gtx102_aspire", "Ultragenyx Pharmaceutical Inc.", "RARE", "0001515673",
     "GTX-102 (apazunersen, intrathecal antisense oligonucleotide vs UBE3A-AS)",
     "Angelman syndrome (full maternal UBE3A deletion, pediatric ages 4-17)",
     ("NCT06617429",), "phase3_topline",
     "Aspire Ph3 (NCT06617429): n=129, randomized, QUADRUPLE-masked (incl. outcomes assessor), "
     "sham-lumbar-puncture control during the double-blind period then crossover to GTX-102; "
     "primary = change in Bayley-4 Cognitive raw score WITHOUT caregiver input at Day 338. Fully "
     "enrolled / active-not-recruiting; topline 2H 2026 and UNREAD - the stock has not repriced on a "
     "controlled cognition result. The marketing corpus carries OPEN-LABEL Phase 1/2 (NCT04259281) "
     "efficacy claims: +6.7 Bayley-4 Cognition GSV at Week 48 (n=40 of 74) 'far exceeding natural "
     "history', with 3 treatment-related lower-extremity-weakness SAEs that paused dosing and forced "
     "a DOSE REDUCTION + slower titration. NO FORWARD LEAK: the Phase 1/2 open-label data is NOT the "
     "binary catalyst; Aspire's sham-controlled Day-338 readout is unread. Screen focus: "
     "open_label_extrapolation, naive natural-history benchmarking, safety_signal_framing, "
     "selective-cohort reporting, biomarker_to_clinical_leap."),
    ("live_iova_lifileucel_lun202", "Iovance Biotherapeutics, Inc.", "IOVA", "0001425205",
     "lifileucel (IOV-LUN-202)", "NSCLC", ("NCT04614103",), "phase2_topline", "IOV-LUN-202; 2H 2026 enroll, data later (LOW)"),
    ("live_acrs_ati052_ad", "Aclaris Therapeutics, Inc.", "ACRS", "0001557746",
     "ATI-052 (TSLP/IL-4Ra)", "atopic dermatitis (POC)", (), "phase2_topline",
     "POC; 2H 2026 / Q4 (MED). NCT UNRESOLVED — Ph1b not registered on CT.gov; bind before evaluate."),

    # ── Regulatory decisions (PDUFA / BLA / NDA) — weaker fit; included for completeness ──
    ("live_arvn_vepdegestrant_pdufa", "Arvinas, Inc.", "ARVN", "0001655759",
     "vepdegestrant", "ESR1-mut ER+ breast cancer", ("NCT05654623",), "pdufa", "VERITAC-2; PDUFA ~2026-06-05 (MED)"),
    ("live_spro_tebipenem_pdufa", "Spero Therapeutics, Inc.", "SPRO", "0001701108",
     "tebipenem HBr", "complicated UTI", ("NCT06059846",), "pdufa", "PIVOT-PO; PDUFA ~2026-06-18 (MED; GSK-partnered)"),
    ("live_achv_cytisinicline_pdufa", "Achieve Life Sciences, Inc.", "ACHV", "0000949858",
     "cytisinicline", "smoking cessation", ("NCT04576949", "NCT05206370"), "pdufa", "ORCA-2/ORCA-3; PDUFA ~2026-06-20 (HIGH)"),
    ("live_uncy_olc_pdufa", "Unicycive Therapeutics, Inc.", "UNCY", "0001766140",
     "oxylanthanum carbonate", "hyperphosphatemia (CKD)", ("NCT06218290",), "pdufa",
     "UNI-OLC-201; PDUFA ~2026-06-29 (MED); NCT MED—verify"),
    ("live_ions_olezarsen_pdufa", "Ionis Pharmaceuticals, Inc.", "IONS", "0000874015",
     "olezarsen", "severe hypertriglyceridemia", ("NCT05079919", "NCT05552326"), "pdufa",
     "CORE/CORE2; sNDA PDUFA ~2026-06-30 (MED)"),
    ("live_vrdn_veligrotug_pdufa", "Viridian Therapeutics, Inc.", "VRDN", "0001590750",
     "veligrotug", "thyroid eye disease", ("NCT05176639", "NCT06021054"), "pdufa", "THRIVE/THRIVE-2; BLA PDUFA ~2026-06-30 (HIGH)"),
    ("live_vera_atacicept_pdufa", "Vera Therapeutics, Inc.", "VERA", "0001831828",
     "atacicept", "IgA nephropathy", ("NCT04716231",), "pdufa", "ORIGIN; BLA PDUFA ~2026-07-07 (HIGH)"),
    ("live_cort_relacorilant_pdufa", "Corcept Therapeutics Incorporated", "CORT", "0001088856",
     "relacorilant + nab-paclitaxel", "ovarian cancer", ("NCT05257408",), "pdufa", "ROSELLA; NDA PDUFA ~2026-07-11 (MED)"),
    ("live_celc_gedatolisib_pdufa", "Celcuity Inc.", "CELC", "0001603454",
     "gedatolisib", "HR+/HER2- breast cancer", ("NCT05501886",), "pdufa", "VIKTORIA-1; NDA PDUFA ~2026-07-17 (MED)"),
    ("live_elvr_rivoceranib_pdufa", "Elevar Therapeutics", "ELVR", "0001739016",
     "rivoceranib + camrelizumab", "hepatocellular carcinoma", ("NCT03764293",), "pdufa",
     "CARES-310 Ph3 1L HCC (camrelizumab/SHR-1210 + rivoceranib/apatinib, n=543); NDA PDUFA ~2026-07-23 (MED)"),
    ("live_capr_deramiocel_pdufa", "Capricor Therapeutics, Inc.", "CAPR", "0001133869",
     "deramiocel", "DMD cardiomyopathy", ("NCT05126758",), "pdufa", "HOPE-3; BLA PDUFA ~2026-08-22 (HIGH)"),
    ("live_rare_dtx401_pdufa", "Ultragenyx Pharmaceutical Inc.", "RARE", "0001515673",
     "DTX401", "glycogen storage disease Ia", ("NCT05139316",), "pdufa", "GlucoGene; BLA PDUFA ~2026-08-23 (MED)"),
    ("live_nuvl_zidesamtinib_pdufa", "Nuvalent, Inc.", "NUVL", "0001861560",
     "zidesamtinib", "ROS1+ NSCLC (pretreated)", ("NCT05118789",), "pdufa", "ARROS-1; NDA PDUFA ~2026-09-18 (HIGH)"),
    ("live_rare_ux111_pdufa", "Ultragenyx Pharmaceutical Inc.", "RARE", "0001515673",
     "UX111", "Sanfilippo syndrome (MPS IIIA)", ("NCT02716246",), "pdufa", "Transpher A; BLA PDUFA ~2026-09-19 (MED)"),
    ("live_prax_relutrigine_pdufa", "Praxis Precision Medicines, Inc.", "PRAX", "0001689548",
     "relutrigine", "developmental epileptic encephalopathy", ("NCT05818553",), "pdufa",
     "EMBOLD; NDA PDUFA ~2026-09-27 (MED). Different asset than sealed prax114 (PRAX-114)."),
    ("live_srrk_apitegromab_pdufa", "Scholar Rock Holding Corporation", "SRRK", "0001727196",
     "apitegromab", "spinal muscular atrophy", ("NCT05156320",), "pdufa", "SAPPHIRE; BLA PDUFA ~2026-09-30 (HIGH)"),
    ("live_ptgx_rusfertide_pdufa", "Protagonist Therapeutics, Inc.", "PTGX", "0001377121",
     "rusfertide", "polycythemia vera", ("NCT05210790",), "pdufa", "VERIFY; NDA PDUFA Q3 2026 (HIGH)"),
    ("live_arqt_zoryve_pdufa", "Arcutis Biotherapeutics, Inc.", "ARQT", "0001787306",
     "Zoryve cream 0.3%", "dermatology", (), "pdufa",
     "sNDA PDUFA ~2026-06-29 (MED). NCT UNRESOLVED — MUSE PK/age-expansion study, no RCT; masking channels N/A."),
    ("live_lnth_mk6240_pdufa", "Lantheus Holdings, Inc.", "LNTH", "0001521036",
     "MK-6240 (tau PET)", "imaging", (), "pdufa",
     "SCREEN N/A — tau-PET imaging diagnostic; 'efficacy' = reader sensitivity/specificity vs autopsy, "
     "not a trial-topline; prior NCT05746312/NCT05450627 were bogus (Anxiety / pancreatic). No masking surface."),
    ("live_bfri_ameluz_pdufa", "Biofrontera Inc.", "BFRI", "0001858685",
     "Ameluz-PDT", "superficial basal cell carcinoma", ("NCT03573401",), "pdufa", "ALA-BCC-CT013; sNDA PDUFA ~2026-09-28 (MED)"),
    ("live_mnkd_furoscix_pdufa", "MannKind Corporation", "MNKD", "0000899460",
     "Furoscix ReadyFlow", "autoinjector (CHF)", (), "pdufa",
     "sNDA PDUFA ~2026-07-26 (MED). NCT UNRESOLVED — device sNDA, no efficacy trial; masking channels N/A."),

    # ── Large-cap / multi-asset (low framework value; included per 'pull them all') ──
    ("live_mrna_mrna1010_pdufa", "Moderna, Inc.", "MRNA", "0001682852",
     "mRNA-1010", "seasonal influenza", ("NCT06602024",), "pdufa",
     "P304/IGNITE-2; BLA PDUFA ~2026-08-05 (MED). NOT P303/NCT05827978."),
    ("live_gild_bic_len_pdufa", "Gilead Sciences, Inc.", "GILD", "0000882095",
     "bictegravir/lenacapavir", "HIV", ("NCT05502341",), "pdufa", "ARTISTRY-1; NDA PDUFA ~2026-08-27 (MED)"),
    ("live_jazz_ziihera_pdufa", "Jazz Pharmaceuticals plc", "JAZZ", "0001232524",
     "Ziihera (zanidatamab)", "1L biliary tract cancer", ("NCT05152147",), "pdufa",
     "HERIZON-BTC-302; sBLA PDUFA ~2026-08-25 (MED); NCT MED—verify"),
    ("live_mrk_keytruda_welireg_rcc", "Merck & Co., Inc.", "MRK", "0000310158",
     "Keytruda + Welireg", "adjuvant RCC", ("NCT05239728",), "pdufa", "LITESPARK-022; BLA PDUFA ~2026-06-19 (MED)"),
    ("live_tlx_pixclara_pdufa", "Telix Pharmaceuticals Limited", "TLX", "0002007191",
     "TLX101-Px (Pixclara)", "glioma imaging", (), "pdufa", "NDA PDUFA ~2026-09-11 (MED; AU-parent)"),
    ("live_phar_besremi_pdufa", "PharmaEssentia Corporation", "PHAR", "0001828316",
     "Besremi (ropeginterferon alfa-2b)", "essential thrombocythemia", ("NCT04285086",), "pdufa",
     "SURPASS-ET Ph3 (ropeginterferon vs anagrelide, n=174); sBLA PDUFA ~2026-08-30 (MED; TW-parent)"),
]

LIVE_CASES: dict[str, CatalystCase] = {
    s[0]: CatalystCase(
        case_id=s[0], company=s[1], ticker=s[2], cik=s[3], program=s[4],
        indication=s[5], nct_ids=s[6], catalyst_type=s[7],
        cutoff=LIVE_CUTOFF, marketing_window_start=WINDOW_START, notes=s[8],
    )
    for s in _SPECS
}

LIVE_IDS: list[str] = list(LIVE_CASES.keys())

# Cases with NO efficacy-masking surface for the trial-topline honesty screen:
# imaging diagnostics (efficacy = reader accuracy vs autopsy), device/formulation
# sNDAs (no efficacy trial), and assets whose pivotal is not registered on CT.gov.
# They have no M to verify marketing against, so the screen is N/A — excluded from
# the runnable set rather than bound to an ill-fitting NCT.
SCREEN_NA_IDS: set[str] = {
    "live_lnth_mk6240_pdufa",   # tau-PET imaging diagnostic
    "live_tlx_pixclara_pdufa",  # 18F-FET glioma imaging diagnostic (Pixclara)
    "live_arqt_zoryve_pdufa",   # roflumilast PK/age-expansion sNDA, no RCT
    "live_mnkd_furoscix_pdufa", # Furoscix ReadyFlow device sNDA, no efficacy trial
    "live_acrs_ati052_ad",      # ATI-052 Ph1b not registered on CT.gov
}

# Cases whose catalyst already RESOLVED before the cutoff, so the outcome leaks
# into the pre-cutoff corpus — they cannot be a blind forward test. Excluded from
# the runnable set (run them only as labeled positive/negative controls, never as
# forward predictions).
FORWARD_LEAKED_IDS: set[str] = {
    # FDA approved VEPPANU (vepdegestrant) 2026-05-01, ahead of the 2026-06-05
    # PDUFA; the approval 8-K sits in the pre-cutoff corpus. Outcome is known.
    "live_arvn_vepdegestrant_pdufa",
    # ACACIA-HCM (aficamten nHCM) topline reported 2026-05-05 — POSITIVE on both
    # dual primaries — 4 weeks before the cutoff; the readout 8-K is in the
    # pre-cutoff corpus, so this is not a blind forward test. Outcome is known.
    "live_cytk_aficamten_acacia",
}

# Trial-topline readouts are the strongest fit for the honesty screen (the
# masking surface is the pivotal trial). PDUFA/regulatory decisions are excluded
# from the forward run: by decision day the efficacy data is already public, so
# there is little new honesty signal.
TRIAL_READOUT_TYPES: set[str] = {
    "phase1b_topline", "phase2_topline", "phase2b_topline",
    "phase2_3_topline", "phase3_topline",
}

# The cohort to actually run the honesty screen on: trial readouts with a bound
# NCT, minus screen-N/A and forward-leaked cases.
RUNNABLE_IDS: list[str] = [
    cid for cid, c in LIVE_CASES.items()
    if c.catalyst_type in TRIAL_READOUT_TYPES
    and cid not in SCREEN_NA_IDS
    and cid not in FORWARD_LEAKED_IDS
]
