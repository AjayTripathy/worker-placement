"""Backtest case definitions and the BLINDING contract.

A CatalystCase is everything the evaluator is ALLOWED to know before predicting:
the company, its EDGAR CIK, the program, the trial NCT, the catalyst type, and
the cutoff date. The evaluator may read marketing filed on or before `cutoff`
and may query M-sources reconstructed as-of `cutoff` — nothing after.

The ground-truth OUTCOME of each catalyst is deliberately NOT in this file. It
lives in `_sealed_outcomes.json`, which the evaluator must never import. Only the
scoring step (after a prediction is committed to disk) is permitted to open it.
This makes the blind mechanically enforceable, not a matter of discipline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
SEALED_OUTCOMES = Path(__file__).parent / "_sealed_outcomes.json"


@dataclass(frozen=True)
class CatalystCase:
    case_id: str
    company: str
    ticker: str
    cik: str                       # 10-digit zero-padded EDGAR CIK
    program: str                   # drug / asset
    indication: str
    nct_ids: tuple[str, ...]       # registered trial(s) behind the catalyst
    catalyst_type: str             # 'phase3_topline' | 'pdufa' | ...
    cutoff: str                    # ISO date; read nothing filed/updated after this
    marketing_window_start: str    # earliest filing date to ingest (bound corpus size)
    notes: str = ""
    aliases: tuple[str, ...] = field(default_factory=tuple)  # sponsor-name variants for M lookups


# ── The matched pair (one MISS, one HIT) ─────────────────────────────────────
# Outcomes are SEALED (see _sealed_outcomes.json). Do not annotate them here.
CASES: dict[str, CatalystCase] = {
    "cassava_simufilam_p3": CatalystCase(
        case_id="cassava_simufilam_p3",
        company="Cassava Sciences, Inc.",
        ticker="SAVA",
        cik="0001069530",  # now Filana Therapeutics; formerly Cassava / Pain Therapeutics
        program="simufilam",
        indication="Alzheimer's disease (mild-to-moderate)",
        nct_ids=("NCT04994483", "NCT05026177"),  # RETHINK-ALZ, REFOCUS-ALZ
        catalyst_type="phase3_topline",
        cutoff="2024-11-24",  # day before RETHINK-ALZ topline announcement
        # Wide window: the catalyst-relevant EFFICACY promotion (Phase 2b 2020 /
        # open-label 2021-22 "simufilam improved cognition" claims) predates the
        # readout by years. The cutoff — not the window start — enforces the blind.
        marketing_window_start="2021-01-01",
        aliases=("Cassava Sciences", "Cassava Sciences, Inc.", "Cassava"),
        notes=("Single-asset Alzheimer's company. Carries a pre-cutoff honesty overlay "
               "(SEC negligence-based disclosure settlement re: 2020 Phase 2b results, "
               "disclosed 2024-09-26). Strong-signal first-validation case; a subtler "
               "non-fraud miss should be the second-round test."),
    ),
    "madrigal_resmetirom_p3": CatalystCase(
        case_id="madrigal_resmetirom_p3",
        company="Madrigal Pharmaceuticals, Inc.",
        ticker="MDGL",
        cik="0001157601",
        program="resmetirom",
        indication="MASH / NASH with fibrosis",
        nct_ids=("NCT03900429",),  # MAESTRO-NASH
        catalyst_type="phase3_topline",
        cutoff="2022-12-18",  # day before MAESTRO-NASH AA-endpoint topline
        marketing_window_start="2021-01-01",
        aliases=("Madrigal Pharmaceuticals", "Madrigal Pharmaceuticals, Inc.", "Madrigal"),
        notes=("Single-asset MASH company. Phase 3 biopsy co-primary readout (NASH "
               "resolution + fibrosis improvement at Week 52) for accelerated approval."),
    ),
    # ── Held-out OOS pair (no SEC/integrity overlay on either; CNS/psychiatry) ──
    "cortexyme_atuzaginstat_gain": CatalystCase(
        case_id="cortexyme_atuzaginstat_gain",
        company="Cortexyme, Inc.",
        ticker="CRTX",
        cik="0001662774",
        program="atuzaginstat (COR388)",
        indication="Alzheimer's disease (mild-to-moderate)",
        nct_ids=("NCT03823404",),  # GAIN (Phase 2/3)
        catalyst_type="phase2_3_topline",
        cutoff="2021-10-25",  # day before GAIN co-primary topline announcement
        marketing_window_start="2019-06-01",  # ~IPO; gingipain-thesis promotion runs early
        aliases=("Cortexyme", "Cortexyme, Inc."),
        notes=("Single-asset Alzheimer's company. Gingipain (P. gingivalis) hypothesis; "
               "GAIN trial co-primary ADAS-Cog11 / ADCS-ADL. No SEC/integrity overlay — "
               "a clean non-fraud miss test for the evidence/science channels."),
    ),
    "karuna_karxt_emergent2": CatalystCase(
        case_id="karuna_karxt_emergent2",
        company="Karuna Therapeutics, Inc.",
        ticker="KRTX",
        cik="0001771917",
        program="KarXT (xanomeline-trospium)",
        indication="Schizophrenia (acute psychosis)",
        nct_ids=("NCT04659161",),  # EMERGENT-2
        catalyst_type="phase3_topline",
        cutoff="2022-08-07",  # day before EMERGENT-2 PANSS topline announcement
        marketing_window_start="2021-01-01",
        aliases=("Karuna Therapeutics", "Karuna Therapeutics, Inc.", "Karuna"),
        notes=("Single-asset schizophrenia company. EMERGENT-2 primary = PANSS total "
               "change vs placebo. No SEC/integrity overlay — clean HIT contrast."),
    ),
    # ── Second held-out pair: validate the endpoint-construct gate fix ──────────
    "cytokinetics_aficamten_sequoia": CatalystCase(
        case_id="cytokinetics_aficamten_sequoia",
        company="Cytokinetics, Incorporated",
        ticker="CYTK",
        cik="0001061983",
        program="aficamten (CK-274)",
        indication="Obstructive hypertrophic cardiomyopathy (oHCM)",
        nct_ids=("NCT05186818",),  # SEQUOIA-HCM
        catalyst_type="phase3_topline",
        cutoff="2023-12-26",  # day before SEQUOIA-HCM topline announcement
        marketing_window_start="2022-06-01",
        aliases=("Cytokinetics", "Cytokinetics, Incorporated", "Cytokinetics Inc"),
        notes=("Cardiac myosin inhibitor. SEQUOIA-HCM primary = change in pVO2 (peak "
               "oxygen uptake) at Week 24. No SEC/integrity overlay — held-out HIT "
               "to test that the construct-gate fix does not false-exclude a clean hit."),
    ),
    "atea_at527_moonsong": CatalystCase(
        case_id="atea_at527_moonsong",
        company="Atea Pharmaceuticals, Inc.",
        ticker="AVIR",
        cik="0001593899",
        program="AT-527 (bemnifosbuvir)",
        indication="COVID-19 (outpatient, mild-to-moderate)",
        nct_ids=("NCT04709835",),  # MOONSONG (Phase 2) — the trial that read out 2021-10-19
        catalyst_type="phase2_topline",
        cutoff="2021-10-18",  # day before MOONSONG topline announcement
        marketing_window_start="2020-09-01",
        aliases=("Atea Pharmaceuticals", "Atea Pharmaceuticals, Inc.", "Atea"),
        notes=("Oral antiviral. MOONSONG (Phase 2) primary = change-from-baseline "
               "SARS-CoV-2 viral load (RT-PCR) in outpatients; this is the readout that "
               "missed on 2021-10-19 and dropped the stock ~70%. (The Phase 3 MORNINGSKY, "
               "NCT04889040, primary = time-to-symptom-alleviation, was Terminated AFTER "
               "this miss — do not confuse the two.) No SEC/integrity overlay — held-out "
               "MISS to confirm the construct-gate fix does not over-suppress real signals."),
    ),
}


# ── Outcome-blind survivorship-safe cohort (N=24) ───────────────────────────
# Drawn from a CT.gov enumeration (Ph2b/Ph3 drug/biologic toplines) filtered to
# small US-listed single-asset sponsors, then SEC-name-resolved and fixed-seed
# sampled. Every NCT/cutoff below was cross-checked against the actual
# price-moving press release (the catalyst-identity-binding protocol): a valid
# NCT that resolves is NOT proof it is the trial that moved the stock. Bindings
# that failed that check were dropped (PVLA private-until-2024; SLGL terminated
# patidegib; BIXT/PII/EDSA no clean readout; ASND safety-OLE; AGEN BLA-withdrawal;
# PROK withdrawn) and backfilled from the same universe.
COHORT24: dict[str, CatalystCase] = {
    "phathom_vonoprazan_phalcon_hp": CatalystCase(
        case_id="phathom_vonoprazan_phalcon_hp",
        company="Phathom Pharmaceuticals, Inc.",
        ticker="PHAT",
        cik="0001783183",
        program="vonoprazan (triple/dual therapy)",
        indication="H. pylori infection",
        nct_ids=("NCT04167670",),  # PHALCON-HP (H. pylori) — NOT the EE trial
        catalyst_type="phase3_topline",
        cutoff="2021-04-28",  # PR 2021-04-29
        marketing_window_start="2020-06-01",
        aliases=("Phathom Pharmaceuticals", "Phathom Pharmaceuticals, Inc.", "Phathom"),
        notes=("Bound to PHALCON-HP (H. pylori eradication), the trial behind NCT04167670 — "
               "the erosive-esophagitis PHALCON-EE catalyst is a different trial/date."),
    ),
    "tarsus_tp03_saturn1": CatalystCase(
        case_id="tarsus_tp03_saturn1",
        company="Tarsus Pharmaceuticals, Inc.",
        ticker="TARS",
        cik="0001819790",
        program="TP-03 (lotilaner 0.25%)",
        indication="Demodex blepharitis",
        nct_ids=("NCT04475432",),  # Saturn-1
        catalyst_type="phase2b_3_topline",
        cutoff="2021-06-18",  # PR Mon 2021-06-21
        marketing_window_start="2020-10-01",
        aliases=("Tarsus Pharmaceuticals", "Tarsus Pharmaceuticals, Inc.", "Tarsus"),
        notes="Saturn-1 (Demodex blepharitis), collarette-cure primary at Day 43.",
    ),
    "beyondspring_plinabulin_dublin3": CatalystCase(
        case_id="beyondspring_plinabulin_dublin3",
        company="BeyondSpring Inc.",
        ticker="BYSI",
        cik="0001677940",
        program="plinabulin + docetaxel",
        indication="2nd/3rd-line EGFR-WT NSCLC",
        nct_ids=("NCT02504489",),  # DUBLIN-3
        catalyst_type="phase3_topline",
        cutoff="2021-08-03",  # PR 2021-08-04
        marketing_window_start="2020-06-01",
        aliases=("BeyondSpring", "BeyondSpring Inc.", "BeyondSpring Pharmaceuticals"),
        notes=("DUBLIN-3 (NSCLC), overall-survival primary. Cayman FPI — may file 6-K "
               "rather than 8-K, so the 8-K marketing corpus can be thin."),
    ),
    "canfite_piclidenoson_comfort": CatalystCase(
        case_id="canfite_piclidenoson_comfort",
        company="Can-Fite BioPharma Ltd.",
        ticker="CANF",
        cik="0001536196",
        program="piclidenoson (CF101)",
        indication="moderate-to-severe plaque psoriasis",
        nct_ids=("NCT03168256",),  # COMFORT
        catalyst_type="phase3_topline",
        cutoff="2022-06-28",  # PR 2022-06-29
        marketing_window_start="2021-06-01",
        aliases=("Can-Fite BioPharma", "Can-Fite BioPharma Ltd.", "Can-Fite"),
        notes=("COMFORT (psoriasis), PASI-75 primary met vs placebo (p<0.04) but Otezla-"
               "inferior on secondaries. Israeli FPI — likely 6-K filer (thin 8-K corpus)."),
    ),
    "actinium_iomab_sierra": CatalystCase(
        case_id="actinium_iomab_sierra",
        company="Actinium Pharmaceuticals, Inc.",
        ticker="ATNM",
        cik="0001388320",
        program="Iomab-B (apamistamab-I131)",
        indication="relapsed/refractory AML (BMT conditioning)",
        nct_ids=("NCT02665065",),  # SIERRA
        catalyst_type="phase3_topline",
        cutoff="2022-10-28",  # PR Mon 2022-10-31
        marketing_window_start="2021-06-01",
        aliases=("Actinium Pharmaceuticals", "Actinium Pharmaceuticals, Inc.", "Actinium"),
        notes=("SIERRA (AML), durable-CR primary met (p<0.0001). OS key-secondary missed; "
               "market repriced that failure ~21 months later (2024-08-05 FDA). Topline = HIT."),
    ),
    "anika_cingal_1901": CatalystCase(
        case_id="anika_cingal_1901",
        company="Anika Therapeutics, Inc.",
        ticker="ANIK",
        cik="0000898437",
        program="Cingal (cross-linked HA + triamcinolone)",
        indication="knee osteoarthritis",
        nct_ids=("NCT04231318",),  # Cingal 19-01
        catalyst_type="phase3_topline",
        cutoff="2022-10-31",  # PR 2022-11-01
        marketing_window_start="2021-06-01",
        aliases=("Anika Therapeutics", "Anika Therapeutics, Inc.", "Anika"),
        notes="Cingal 19-01 (knee OA), WOMAC-Pain superiority vs steroid at 26 wks met.",
    ),
    "abeona_eb101_viital": CatalystCase(
        case_id="abeona_eb101_viital",
        company="Abeona Therapeutics Inc.",
        ticker="ABEO",
        cik="0000318306",
        program="EB-101 (gene-corrected cell therapy)",
        indication="recessive dystrophic epidermolysis bullosa (RDEB)",
        nct_ids=("NCT04227106",),  # VIITAL
        catalyst_type="phase3_topline",
        cutoff="2022-11-02",  # PR 2022-11-03
        marketing_window_start="2021-06-01",
        aliases=("Abeona Therapeutics", "Abeona Therapeutics Inc.", "Abeona"),
        notes="VIITAL (RDEB), both co-primaries (wound healing + pain) met.",
    ),
    "lianbio_mavacamten_explorer_cn": CatalystCase(
        case_id="lianbio_mavacamten_explorer_cn",
        company="LianBio",
        ticker="LIANY",
        cik="0001831283",
        program="mavacamten",
        indication="obstructive HCM (Chinese patients)",
        nct_ids=("NCT05174416",),  # EXPLORER-CN
        catalyst_type="phase3_topline",
        cutoff="2023-04-25",  # PR 2023-04-26
        marketing_window_start="2022-01-01",
        aliases=("LianBio", "LianBio LLC", "LianBio Development"),
        notes=("EXPLORER-CN (oHCM), Valsalva LVOT-gradient primary met (p<0.001). "
               "FPI — likely 6-K filer (thin 8-K corpus)."),
    ),
    "kalvista_sebetralstat_konfident": CatalystCase(
        case_id="kalvista_sebetralstat_konfident",
        company="KalVista Pharmaceuticals, Inc.",
        ticker="KALV",
        cik="0001348911",
        program="sebetralstat (oral)",
        indication="hereditary angioedema (on-demand)",
        nct_ids=("NCT05259917",),  # KONFIDENT
        catalyst_type="phase3_topline",
        cutoff="2024-02-12",  # PR 2024-02-13
        marketing_window_start="2023-01-01",
        aliases=("KalVista Pharmaceuticals", "KalVista Pharmaceuticals, Inc.", "KalVista"),
        notes="KONFIDENT (HAE), time-to-symptom-relief primary met at both doses (p<0.0001 / p=0.0013).",
    ),
    "palatin_pl9643_melody1": CatalystCase(
        case_id="palatin_pl9643_melody1",
        company="Palatin Technologies, Inc.",
        ticker="PTN",
        cik="0000911216",
        program="PL9643 (melanocortin agonist)",
        indication="dry eye disease",
        nct_ids=("NCT05201170",),  # MELODY-1
        catalyst_type="phase3_topline",
        cutoff="2024-02-27",  # PR 2024-02-28
        marketing_window_start="2023-01-01",
        aliases=("Palatin Technologies", "Palatin Technologies, Inc.", "Palatin"),
        notes=("MELODY-1 (DED), co-primary SPLIT — symptom/pain met (p<0.025), sign NOT "
               "significant. Strict co-primary rule = miss; market took it positively "
               "(~+15%). Labeled HIT under the price-direction tiebreak."),
    ),
    "atea_hcv_combo_p2": CatalystCase(
        case_id="atea_hcv_combo_p2",
        company="Atea Pharmaceuticals, Inc.",
        ticker="AVIR",
        cik="0001593899",
        program="bemnifosbuvir + ruzasvir (8-wk)",
        indication="chronic hepatitis C (treatment-naïve)",
        nct_ids=("NCT05904470",),  # Ph2 HCV combo (BEM+RZR, 275 pts, SVR12 primary, COMPLETED). NB: NCT05629962 is SUNRISE-3 (COVID Ph3) — a mis-binding caught by verify_finding 2026-06-01.
        catalyst_type="phase2_topline",
        cutoff="2024-12-03",  # PR 2024-12-04
        marketing_window_start="2024-01-01",
        aliases=("Atea Pharmaceuticals", "Atea Pharmaceuticals, Inc.", "Atea"),
        notes=("HCV combo Ph2 (SVR12 + safety primaries met, 98% PP). Distinct catalyst "
               "from the 2021 COVID MOONSONG miss (see atea_at527_moonsong)."),
    ),
    "candel_can2409_prostate_p3": CatalystCase(
        case_id="candel_can2409_prostate_p3",
        company="Candel Therapeutics, Inc.",
        ticker="CADL",
        cik="0001841387",
        program="CAN-2409 + valacyclovir + radiation",
        indication="localized prostate cancer (intermediate/high-risk)",
        nct_ids=("NCT01436968",),
        catalyst_type="phase3_topline",
        cutoff="2024-12-10",  # PR 2024-12-11
        marketing_window_start="2024-01-01",
        aliases=("Candel Therapeutics", "Candel Therapeutics, Inc.", "Candel"),
        notes="CAN-2409 Ph3 prostate, disease-free-survival primary met (p=0.0155).",
    ),
    "summit_ridinilazole_ricodify": CatalystCase(
        case_id="summit_ridinilazole_ricodify",
        company="Summit Therapeutics Inc.",
        ticker="SMMT",
        cik="0001599298",
        program="ridinilazole",
        indication="C. difficile infection",
        nct_ids=("NCT03595553", "NCT03595566"),  # twin Ri-CoDIFy Ph3 (ridinilazole vs vancomycin)
        catalyst_type="phase3_topline",
        cutoff="2021-12-17",  # PR Mon 2021-12-20
        marketing_window_start="2021-01-01",
        aliases=("Summit Therapeutics", "Summit Therapeutics Inc.", "Summit"),
        notes=("Twin Ri-CoDIFy Ph3 (CDI) — superiority in sustained clinical response NOT met. "
               "Dec-2021 topline reported both twins together. Prior NCT04781387 was a "
               "mis-binding (Crestone CRS3123), caught by deterministic verify_binding."),
    ),
    "kiniksa_mavrilimumab_ards": CatalystCase(
        case_id="kiniksa_mavrilimumab_ards",
        company="Kiniksa Pharmaceuticals International, plc",
        ticker="KNSA",
        cik="0001730430",
        program="mavrilimumab",
        indication="COVID-19-related ARDS",
        nct_ids=("NCT04447469",),  # KPL-301-C203 Ph3 portion
        catalyst_type="phase2_3_topline",
        cutoff="2021-12-27",  # PR 2021-12-28
        marketing_window_start="2021-01-01",
        aliases=("Kiniksa Pharmaceuticals", "Kiniksa Pharmaceuticals International, plc", "Kiniksa"),
        notes=("Ph3 portion of the Ph2/3 ARDS study — primary (alive & ventilation-free "
               "at Day 29) NOT met. The April-2021 Ph2 positive is a separate, earlier event."),
    ),
    "monopar_validive_voice": CatalystCase(
        case_id="monopar_validive_voice",
        company="Monopar Therapeutics Inc.",
        ticker="MNPR",
        cik="0001645469",
        program="Validive (clonidine buccal tablet)",
        indication="severe oral mucositis (chemoradiation)",
        nct_ids=("NCT04648020",),  # VOICE
        catalyst_type="phase2b_3_topline",
        cutoff="2023-03-24",  # PR Mon 2023-03-27
        marketing_window_start="2022-06-01",
        aliases=("Monopar Therapeutics", "Monopar Therapeutics Inc.", "Monopar"),
        notes="VOICE (SOM) — interim failed the prespecified efficacy threshold; trial halted for futility.",
    ),
    "annexon_anx007_archer": CatalystCase(
        case_id="annexon_anx007_archer",
        company="Annexon, Inc.",
        ticker="ANNX",
        cik="0001528115",
        program="ANX007 (anti-C1q)",
        indication="geographic atrophy / dry AMD",
        nct_ids=("NCT04656561",),  # ARCHER (Phase 2, GA) — anti-C1q ANX007
        catalyst_type="phase2_topline",
        cutoff="2023-05-23",  # PR 2023-05-24
        marketing_window_start="2022-06-01",
        aliases=("Annexon", "Annexon, Inc.", "Annexon Biosciences"),
        notes=("ARCHER Ph2 (GA) — anatomic primary (GA lesion-growth rate) NOT significant; "
               "BCVA vision-loss secondary hit. Market treated it as a failure (~-50%). "
               "Prior NCT04701164 was a mis-binding (ANX005 Guillain-Barre Ph3), caught "
               "by deterministic verify_binding."),
    ),
    "inovio_vgx3100_reveal2": CatalystCase(
        case_id="inovio_vgx3100_reveal2",
        company="Inovio Pharmaceuticals, Inc.",
        ticker="INO",
        cik="0001055726",
        program="VGX-3100 + electroporation",
        indication="cervical HSIL (HPV-16/18)",
        nct_ids=("NCT03721978",),  # REVEAL 2 (NOT REVEAL 1, which was the 2021 positive)
        catalyst_type="phase3_topline",
        cutoff="2023-08-08",  # disclosed in 2023-08-09 Q2 strategic update
        marketing_window_start="2022-06-01",
        aliases=("Inovio Pharmaceuticals", "Inovio Pharmaceuticals, Inc.", "Inovio"),
        notes=("REVEAL 2 (cervical HSIL) — biomarker-selected primary not significant; "
               "program discontinued. REVEAL 1 (NCT03185013) was the separate 2021 positive."),
    ),
    "neumora_navacaprant_koastal1": CatalystCase(
        case_id="neumora_navacaprant_koastal1",
        company="Neumora Therapeutics, Inc.",
        ticker="NMRA",
        cik="0001885522",
        program="navacaprant (KOR antagonist)",
        indication="major depressive disorder",
        nct_ids=("NCT06029426",),  # KOASTAL-1
        catalyst_type="phase3_topline",
        cutoff="2024-12-31",  # PR 2025-01-02 (01-01 holiday)
        marketing_window_start="2024-01-01",
        aliases=("Neumora Therapeutics", "Neumora Therapeutics, Inc.", "Neumora"),
        notes="KOASTAL-1 (MDD), MADRS Wk6 primary failed — complete placebo overlap.",
    ),
    "rigel_fostamatinib_forward": CatalystCase(
        case_id="rigel_fostamatinib_forward",
        company="Rigel Pharmaceuticals, Inc.",
        ticker="RIGL",
        cik="0001034842",
        program="fostamatinib",
        indication="warm autoimmune hemolytic anemia (wAIHA)",
        nct_ids=("NCT03764618",),  # FORWARD
        catalyst_type="phase3_topline",
        cutoff="2022-06-07",  # PR 2022-06-08
        marketing_window_start="2021-06-01",
        aliases=("Rigel Pharmaceuticals", "Rigel Pharmaceuticals, Inc.", "Rigel"),
        notes="FORWARD (wAIHA) — durable hemoglobin-response primary NOT met in overall population (p=0.398).",
    ),
    "praxis_prax114_aria": CatalystCase(
        case_id="praxis_prax114_aria",
        company="Praxis Precision Medicines, Inc.",
        ticker="PRAX",
        cik="0001689548",
        program="PRAX-114 (monotherapy)",
        indication="major depressive disorder",
        nct_ids=("NCT04832425",),  # Aria
        catalyst_type="phase2_3_topline",
        cutoff="2022-06-03",  # PR Mon 2022-06-06
        marketing_window_start="2021-06-01",
        aliases=("Praxis Precision Medicines", "Praxis Precision Medicines, Inc.", "Praxis"),
        notes="Aria (MDD) — HAM-D17 Day-15 primary and all secondaries failed.",
    ),
    "mirum_maralixibat_march": CatalystCase(
        case_id="mirum_maralixibat_march",
        company="Mirum Pharmaceuticals, Inc.",
        ticker="MIRM",
        cik="0001759425",
        program="maralixibat (LIVMARLI)",
        indication="progressive familial intrahepatic cholestasis (PFIC)",
        nct_ids=("NCT03905330",),  # MARCH
        catalyst_type="phase3_topline",
        cutoff="2022-10-21",  # PR Mon 2022-10-24
        marketing_window_start="2021-06-01",
        aliases=("Mirum Pharmaceuticals", "Mirum Pharmaceuticals, Inc.", "Mirum"),
        notes="MARCH (PFIC), pruritus-severity primary in PFIC2 met (p=0.0098).",
    ),
    "cingulate_ctx1301_adult": CatalystCase(
        case_id="cingulate_ctx1301_adult",
        company="Cingulate Inc.",
        ticker="CING",
        cik="0001862150",
        program="CTx-1301 (dexmethylphenidate)",
        indication="adult ADHD",
        nct_ids=("NCT05631626",),  # CTx-1301-022 adult ALC study
        catalyst_type="phase3_topline",
        cutoff="2023-07-10",  # PR 2023-07-11
        marketing_window_start="2022-06-01",
        aliases=("Cingulate", "Cingulate Inc.", "Cingulate Therapeutics"),
        notes=("CTx-1301-022 (adult ADHD) — PERMP primary NOT significant (p=0.089), study "
               "deliberately underpowered (effect-size estimation). Headlined 'positive'; "
               "stock fell ~8%. A honesty-channel test case (positive spin vs missed primary)."),
    ),
    "organogenesis_renu_oa_p3": CatalystCase(
        case_id="organogenesis_renu_oa_p3",
        company="Organogenesis Holdings Inc.",
        ticker="ORGO",
        cik="0001661181",
        program="ReNu (amniotic suspension allograft)",
        indication="knee osteoarthritis",
        nct_ids=("NCT04636229",),
        catalyst_type="phase3_topline",
        cutoff="2024-05-01",  # PR 2024-05-02 (NOT the 2023 data-lock / interim)
        marketing_window_start="2023-06-01",
        aliases=("Organogenesis", "Organogenesis Holdings Inc.", "Organogenesis Holdings"),
        notes=("ReNu Ph3 (knee OA), 6-month WOMAC-Pain primary met (p=0.0177). The catalyst "
               "PR is 2024-05-02, not the 2023 primary-completion / March-2023 interim."),
    ),
    "soleno_dccr_c602": CatalystCase(
        case_id="soleno_dccr_c602",
        company="Soleno Therapeutics, Inc.",
        ticker="SLNO",
        cik="0001484565",
        program="DCCR (diazoxide choline ER)",
        indication="Prader-Willi syndrome",
        nct_ids=("NCT03714373",),  # Study C602 randomized-withdrawal period
        catalyst_type="phase3_topline",
        cutoff="2023-09-25",  # PR 2023-09-26
        marketing_window_start="2022-09-01",
        aliases=("Soleno Therapeutics", "Soleno Therapeutics, Inc.", "Soleno"),
        notes=("C602 randomized-withdrawal HQ-CT primary met (p=0.0022). Distinct from the "
               "original DESTINY/C601 (NCT03440814) that missed in 2020."),
    ),
}

CASES.update(COHORT24)

# Case-id lists for convenient pipeline invocation.
VALIDATION6 = ["cassava_simufilam_p3", "madrigal_resmetirom_p3",
               "cortexyme_atuzaginstat_gain", "karuna_karxt_emergent2",
               "cytokinetics_aficamten_sequoia", "atea_at527_moonsong"]
COHORT24_IDS = list(COHORT24.keys())


def get_case(case_id: str) -> CatalystCase:
    return CASES[case_id]
