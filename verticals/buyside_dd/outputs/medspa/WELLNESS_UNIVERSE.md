# Wellness / Healthspan Candidate Universe — "Book of Watches" Expansion

**As-of:** 2026-06-26 · **Investor:** US HNW, CA top-bracket, self-managed SMA (US listings easy; foreign with friction)
**Purpose:** Surface PUBLIC equities with a real structural wellness tailwind that are **NOT already fully discounted**, for deep-diligence as WATCH candidates. Book originated in medical aesthetics (GLP-1-face/body) and is broadening to general wellness/healthspan.

**Already in book — DO NOT re-pitch:** ESTA, GALD, EOLS, Hugel (145020.KQ), LFMD, INMD. Already analyzed in peptide thesis: LLY, NVO, STVN, PPGN.

**Method note (SignalOS conditioning).** Every US-listed name was passed through the no-edge **conditioning layer** (`verticals/buyside_dd/connectors/discovery_state.py`) and logged to `outputs/latency_log.jsonl`. The conditioning layer is **CONTROL, not alpha** — it tells us whether the market has already crowded into the name, not whether it will go up. Numbers below are **approximate / labeled**; do not treat as precise. The conditioning layer's known lags: positioning ~26d; Google Trends + GDELT frequently UNAVAILABLE on a cloud IP, so attention leans on StockTwits + Wikipedia + FINRA-SI + SEC-FTD.

**Big structural caveat baked into the screen — the cap-tier guard.** Any name with mcap > $5B that looks quiet on RETAIL channels is NOT called UNDISCOVERED; the layer downgrades it to DISCOVERED_CROWDED ("the street watches every $5B+ name; absence of retail noise ≠ absence of discovery"). This is why WST/DXCM/RMD/GRMN/CELH read CROWDED despite low retail attention. For a HNW watch-list, "DISCOVERED_CROWDED" does **not** mean un-investable — it means *no informational edge from being early*; you'd be buying the consensus structural story, not a divergence. We flag those as **QUALITY-COMPOUNDER watches** vs. the genuinely **UNDISCOVERED** divergences.

---

## A. RANKED SHORTLIST — 9 strongest deep-dive candidates
(best structural tailwind × least-priced × cleanest verifiability)

| # | Ticker | Exch | Sub-theme | ~Mcap | Discovery regime | Near-term catalyst |
|---|--------|------|-----------|-------|------------------|--------------------|
| 1 | **VERU** | Nasdaq | GLP-1 muscle-preservation | ~$0.25B | **UNDISCOVERED** (attn .16 / pos .03) | Ph2b PLATEAU interim Q1'27 |
| 2 | **HIMS** | NYSE | GLP-1 telehealth distribution | ~$7B | DISCOVERED_CROWDED (attn .82 / pos .71) | Eucalyptus close; branded-GLP-1 ramp |
| 3 | **PGNY** | Nasdaq | Fertility benefits | ~$1.5B | **UNDISCOVERED** (attn .09 / pos .15) | 2027 selling season; Progyny Select |
| 4 | **WST** | NYSE | GLP-1 picks-and-shovels (injectables) | ~$23B | DISCOVERED_CROWDED (low-attn, cap-tier) | Quarterly GLP-1 elastomer volume |
| 5 | **DXCM** | Nasdaq | CGM-for-wellness (metabolic) | ~$30B | DISCOVERED_CROWDED (low-attn, cap-tier) | Stelo OTC ramp; Oura integration |
| 6 | **INSP** | NYSE | Sleep apnea (neurostim) | ~$3B | **DISCOVERING** (attn .00 / pos .32) | Inspire V launch; SLEEP 2026 CV data |
| 7 | **PRCT** | Nasdaq | Men's health BPH robotics | ~$1.6B | (small/mid, likely UND/DISCOVERING) | HYDROS intl launch; 27-33% rev growth |
| 8 | **BRBR** | NYSE | GLP-1 nutrition / protein | ~$8B | DISCOVERED_CROWDED (attn .14 / pos .31) | Premier Protein soda launch |
| 9 | **RMD** | NYSE | Sleep apnea CPAP | ~$27B | DISCOVERED_CROWDED (cap-tier) | GLP-1 screening tailwind realization |

### Why each makes the cut

**1. VERU (Veru Inc) — GLP-1 muscle-preservation — the ONLY clean UNDISCOVERED divergence in the set.**
The strongest structural-tailwind × least-priced combination here. GLP-1 weight loss destroys lean mass as well as fat; "quality of weight loss" (preserving muscle/bone/physical function) is the next leg of the obesity-drug story, and enobosarm (oral SARM) is a direct play on it with FDA regulatory clarity already obtained and a Ph2b PLATEAU semaglutide-combo trial enrolling (interim Q1'27, topline Q4'27). Conditioning layer reads **UNDISCOVERED** (attention .16, positioning .03 — essentially no retail crowd, no short-interest spike, no FTD spike). This is a binary clinical name (small ~$250M mcap, history of pivots and dilution — diligence the cap structure and cash runway hard), but it is the one place in this universe where being early actually carries informational edge. **Surface as actionable for the quant analyst.**

**2. HIMS (Hims & Hers) — GLP-1 telehealth distribution — best structural franchise, but already DISCOVERED_CROWDED.**
The category-defining consumer front-end for GLP-1 + the broadest cross-sell (hair, derm, mental health, sexual health, now international via Eucalyptus/ZAVA/LiveWell). FY26 revenue guide $2.8-3.0B (19-28% growth), trading ~2.3x sales. But the conditioning layer is unambiguous: **attention .82, positioning .71 = DISCOVERED_CROWDED.** This is the crowded-name warning the framework exists to give (cf. RCAT) — a real story everyone already owns and shorts. Worth diligence as a quality watch, but do NOT treat it as an early/divergence call; you are buying consensus with a compounding-vs-margin-pivot debate priced in.

**3. PGNY (Progyny) — fertility benefits — UNDISCOVERED + cheapest quality name in the book.**
Dominant managed-fertility-benefits platform selling into self-insured employers; record Q1'26 rev $328.5M, ~$1.29B TTM, but mcap only ~$1.46B → ~1.1x sales and ~10x forward P/E for a category leader with a structural family-building / women's-health tailwind and a new fully-insured product (Progyny Select). Conditioning layer reads **UNDISCOVERED** (attention .09, positioning .15). The cheapness reflects real concerns (client concentration, utilization, a de-rating from prior multiples) — that's the diligence — but the combination of structural tailwind, category leadership, low multiple AND low crowding is the second-best risk/reward here.

**4. WST (West Pharmaceutical) — GLP-1 picks-and-shovels — the cleanest verifiable physical tailwind.**
The elastomer/containment monopoly inside every GLP-1 auto-injector pen made by Lilly/Novo. GLP-1 demand is the rising tide; this is the most *verifiable* tailwind in the set (volume is a hard-to-fake physical quantity — auto-injector unit growth, Annex-1 component demand). ~$23B mcap, ~39x fwd P/E (quality premium, not cheap). Conditioning reads DISCOVERED_CROWDED via the **cap-tier guard** (retail attention is actually low — .11 — but the street watches every $20B+ medtech). A quality-compounder watch, not a divergence; diligence the GLP-1 mix and the recent re-rating after the 2024 drawdown.

**5. DXCM (Dexcom) — CGM-for-wellness — the metabolic-tracking optionality nobody is paying for yet.**
Core diabetes CGM is mature/priced, but the **Stelo OTC** launch into the non-diabetic wellness/metabolic-health market (now integrating with Oura) is a genuine new TAM that the ~$30B mcap doesn't obviously capitalize. CROWDED by cap-tier guard (retail attention .08). Watch the OTC wellness ramp as the catalyst; the divergence to test in diligence is whether Stelo/Lingo create a durable consumer-subscription layer or a low-margin commodity.

**6. INSP (Inspire Medical) — sleep apnea neurostim — GLP-1 fear may be mispricing the tailwind.**
Hypoglossal-nerve-stim for OSA in CPAP-intolerant patients. The bear case (GLP-1 weight loss shrinks the OSA pool) is exactly the kind of secondary-effect narrative the book should adjudicate — ResMed's own data argues GLP-1 *expands* diagnosed OSA by funneling weight-loss patients into apnea screening. Inspire V launch + SLEEP-2026 cardiovascular data are near-term catalysts. ~$3B mcap, growth decelerated (Q1 +1.6%), so it's a "tailwind-vs-deceleration" diligence call. Conditioning reads **DISCOVERING** (attention ~0, positioning .32) — retail isn't talking about it, but short interest is building, i.e. the bears are positioning ahead of the crowd. That's a watch-it-closely state: not yet crowded, but the GLP-1-bear short is already on. Pair-watch with RMD (the same thesis at large-cap).

**7. PRCT (PROCEPT BioRobotics) — men's health BPH robotics — under-followed device compounder.**
Aquablation (HYDROS, AI-enabled robotic BPH therapy) riding the men's-health / aging-male tailwind; 27-33% guided 2026 revenue growth, international (UK) launch underway, ~$1.6B mcap. Adjacent to the men's-health theme (TRT/sexual health) but with a hard-to-fake adoption metric (procedure volume — 12,200 US procedures in Q1). Diligence path/profitability. Live discovery read pending.

**8. BRBR (BellRing Brands) — GLP-1 nutrition / protein — structural protein tailwind, crowded.**
Premier Protein / Dymatize RTD shakes are a direct beneficiary of the "protein is table stakes / muscle-preservation-on-GLP-1" consumer shift; entering protein-soda. ~$8B mcap. Conditioning reads DISCOVERED_CROWDED (attn .14 / pos .31 — modest crowd, meaningful short interest → the GLP-1-disruption *bear* is also positioned). The interesting tension: protein is GLP-1-*helped* while snacks are GLP-1-*hurt* — diligence whether the market has correctly separated the two inside packaged food.

**9. RMD (ResMed) — sleep apnea CPAP — the GLP-1-fear reversal trade, but large and watched.**
The cleanest "secondary-effect mispricing" thesis: GLP-1 was supposed to kill CPAP demand; instead ResMed is running physician screening programs to funnel weight-loss patients into apnea diagnosis, and demand held. ~$27B mcap → DISCOVERED_CROWDED by cap-tier. A quality-compounder watch where the catalyst is the *realization* that the GLP-1 threat was overstated.

---

## B. FULL SCREEN — ~25 names (incl. rejects)

Regime key: **UND** = UNDISCOVERED (low attention + low positioning) · **CRWD** = DISCOVERED_CROWDED · **CRWD\*** = CROWDED via cap-tier guard (retail quiet but >$5B) · **FOREIGN** = positioning blind (no US FINRA-SI/FTD) · **PRIVATE** = no clean listing.

| Ticker / Exch | Sub-theme | 1-line structural thesis | ~Mcap / mult | Discovery regime | Catalyst | Verdict |
|---|---|---|---|---|---|---|
| **VERU** Nasdaq | GLP-1 muscle-preservation | Lean-mass preservation = next leg of obesity-drug story; enobosarm SARM + sema combo | ~$0.25B | **UND** (.16/.03) | Ph2b interim Q1'27 | **SHORTLIST #1 — actionable** |
| **PGNY** Nasdaq | Fertility benefits | Category-leader fertility benefits, ~10x P/E, structural family-building tailwind | ~$1.5B / ~1.1x sales | **UND** (.09/.15) | 2027 selling season | **SHORTLIST #3** |
| **HIMS** NYSE | GLP-1 telehealth | Defining consumer GLP-1 front-end + cross-sell + intl | ~$7B / ~2.3x sales | CRWD (.82/.71) | Eucalyptus close | **SHORTLIST #2 (crowded)** |
| **WST** NYSE | GLP-1 picks/shovels | Elastomer monopoly in every GLP-1 pen; verifiable volume | ~$23B / ~39x fwd | CRWD\* (.11) | GLP-1 vol prints | **SHORTLIST #4 (quality)** |
| **DXCM** Nasdaq | CGM-for-wellness | Stelo OTC metabolic-wellness TAM beyond diabetes | ~$30B | CRWD\* (.08) | Stelo OTC ramp | **SHORTLIST #5 (quality)** |
| **INSP** NYSE | Sleep apnea neurostim | GLP-1-fear may misprice OSA-screening tailwind | ~$3B | **DISCOVERING** (.00/.32) | Inspire V / SLEEP'26 | **SHORTLIST #6** |
| **PRCT** Nasdaq | Men's health BPH | Aquablation robotic BPH, 27-33% growth, under-followed | ~$1.6B | _pending (non-decisive)_ | HYDROS intl | **SHORTLIST #7** |
| **BRBR** NYSE | GLP-1 nutrition | Premier Protein RTD = protein/muscle-preservation tailwind | ~$8B | CRWD (.14/.31) | Protein soda | **SHORTLIST #8** |
| **RMD** NYSE | Sleep apnea CPAP | GLP-1-threat-overstated reversal; demand held | ~$27B | CRWD\* | screening programs | **SHORTLIST #9 (quality)** |
| **OGN** NYSE | Women's health / menopause HRT | 70+ women's-health products, FDA HRT box-warning removal tailwind | ~$3.5B | UND (.001/.19) on layer | — | **REJECT — under $14.00 Sun Pharma cash takeout (close early-2027); merger-arb, NOT a wellness watch. Conditioning reads "quiet" but upside is capped at deal price.** |
| **TDOC** NYSE | GLP-1/chronic telehealth | Chronic-care + weight telehealth at distressed multiple | ~$1.7B | CRWD (.17/.43) | turnaround | REJECT — structurally challenged, high short positioning, no clean wellness tailwind |
| **GRMN** NYSE | Wearables / fitness | Fitness wearable + new CIRQA recovery band vs WHOOP/Oura | ~$46B | **UND_RETAIL_ONLY** (.20/.06) | CIRQA launch | REJECT — retail quiet but cap-tier guard: $46B, street watches it; wearable mix small vs auto/marine; no edge |
| **CELH** Nasdaq | Functional beverage | Functional energy drink, better-for-you tailwind | ~$8B | **CRWD** (.83/.84) | distribution | REJECT — heavily crowded both sides (high attn + high positioning); GLP-1 angle thin |
| **SMPL** Nasdaq | Functional nutrition | Atkins/Quest low-carb-protein = GLP-1-aligned | ~$2B | **UND** (.11/.17) | OWYN/protein | WATCH-LITE — genuinely under-owned; protein-aligned but Atkins legacy drag; diligence brand mix |
| **PLNT** NYSE | Fitness gyms | Value gym; "GLP-1 makes people exercise" tailwind | ~$4.3B | **CRWD** (.08/.24) | guidance reset | REJECT — just cut guidance & cancelled price hikes (-30%); broken near-term, not a clean tailwind |
| **RVNC** Nasdaq | Aesthetic neurotoxin/derm | Daxxify + RHA fillers | ~$0.4B | _pending (non-decisive)_ | Crown takeout? | REJECT-ish — distressed; aesthetics already in book (GALD/EOLS); only interesting as M&A-arb |
| **TALK** Nasdaq | Behavioral telehealth | Virtual mental health + TALK-AI | ~$0.87B | _pending (non-decisive)_ | TALK-AI launch | WATCH-LITE — mental-health tailwind real; profitability/competition diligence |
| **LFST** Nasdaq | Behavioral health clinics | Largest outpatient mental-health rollup | ~$3.25B | _pending (non-decisive)_ | margin inflection | WATCH-LITE — structural demand, but rollup margins; CEO calls peers "dislocated" |
| **ABBV** NYSE | Aesthetics (Botox/Juvederm) | Allergan Aesthetics segment | mega-cap | CRWD\* | — | REJECT — aesthetics buried in pharma mega-cap; no pure exposure (and aesthetics in book) |
| **CUTR** Nasdaq | Aesthetic lasers | Distressed energy-device maker | micro | n/a | restructuring | REJECT — distressed/going-concern risk; aesthetics already covered |
| **IRTC** Nasdaq | Cardiac monitoring | Zio ambulatory ECG; preventive-cardiac tailwind | ~$3.5B | _not screened_ | guidance raise | WATCH-LITE (adjacent) — preventive-screening tailwind but recent cyber breach; diligence |
| **BFLY** NYSE | Handheld ultrasound | Ultrasound-on-chip democratizing imaging | small | _not screened_ | FDA clearances | WATCH-LITE (adjacent) — preventive-diagnostics tailwind; cash-burn diligence |
| **JYNT** Nasdaq | Chiro / wellness clinic | Cash-pay chiropractic franchise rollup | ~$0.13B / 41x P/E | _not screened_ | refranchising | REJECT — micro-cap, recovery/wellness-clinic but operationally troubled |
| **VERU dup / FN_HEALTH** | Longevity diagnostics | Function Health (Ezra/Getlabs) | PRIVATE | PRIVATE | — | NO LISTING — best longevity-diagnostics asset is private |

---

## C. Sub-themes that are structurally PRIVATE (the public-market gap)

These wellness sub-themes have **no clean public pure-play** — the category leaders are venture-funded private companies. Flagging so we know where the public market simply cannot express the theme:

1. **Longevity / preventive whole-body diagnostics — DEEPLY PRIVATE.** The leaders are **Function Health** (acquired **Ezra** whole-body MRI May'25 + **Getlabs** at-home draws Apr'26), **Prenuvo** (>100k scans, $120M Series B), **Superpower**, **Hone Health**, **Tally Health** (acquired by Infinite Epigenetics Apr'26). Biological-age/epigenetic testing likewise private. Public proxies are only indirect (imaging-hardware OEMs, lab-testing co's like LH/DGX which are NOT wellness-positioned). **No public pure-play exists.**
2. **Wearables / recovery — the two hottest names are PRIVATE.** **WHOOP** ($10.1B private, $575M Series G) and **Oura** (private) dominate the longevity-conscious wearable conversation. Only **Garmin** (GRMN) and **Apple** are public, and the recovery/wellness mix is a small slice of each — no clean public expression.
3. **Hormone-health telehealth (men's TRT, women's HRT) — PRIVATE front-ends.** The branded consumer franchises (TRT Nation, Hone, Maximus for men; Alloy, Winona, Midi for women's menopause/HRT) are private. Public exposure is only via diversified platforms (HIMS men's, LFMD/RexMD) or pharma supplying the molecules (OGN — now being acquired). The FDA's Nov'25 removal of HRT box warnings is a real tailwind with **no clean public pure-play.**
4. **IV-hydration / medspa / hyper-wellness clinic rollups — PRIVATE and fragile.** Restore Hyper Wellness (the would-be public rollup) **filed bankruptcy**; the category is fragmented private operators. **No investable public rollup.**
5. **Functional supplements / better-for-you brands — mostly PRIVATE or buried.** Vital Proteins (Nestlé), Optimum Nutrition (Glanbia), AG1/Athletic Greens (private), most DTC supplement brands private. Public exposure is indirect (BRBR, SMPL, Glanbia GLB.L foreign, Nestlé foreign).
6. **GLP-1 compounding / specialty pharmacy — PRIVATE / regulatorily impaired.** The compounding angle is largely private and now under FDA crackdown as branded GLP-1 supply normalizes; not a durable public thesis.

**Implication for the book:** the public market lets you express the *picks-and-shovels* (WST, DXCM, STVN already in book), the *distribution front-end* (HIMS, LFMD in book), and *specific device/benefit niches* (PGNY, INSP, PRCT, VERU). The *direct longevity-diagnostics, premium-wearable, and hormone-telehealth consumer franchises* — arguably the purest healthspan plays — are **private** and only reachable via late-stage venture, secondaries, or eventual IPOs to monitor (Function Health, Prenuvo, WHOOP, Oura, Superpower).

---

## D. Conditioning-layer notes & caveats

- **UNDISCOVERED reads (the un-crowded names):** VERU (.16/.03), PGNY (.09/.15), SMPL (.11/.17), OGN (.00/.19), and GRMN as UNDISCOVERED_RETAIL_ONLY (.20/.06 — cap-tier downgrade, institutional unverified).
- **Only VERU is surfaced as ACTIONABLE** (UNDISCOVERED divergence with a real, near-term, hard-to-fake catalyst — the muscle-preservation clinical readout). PGNY and SMPL read UNDISCOVERED but are *value/quality watches*, not event divergences (no specific near-term catalyst that the market is mispricing on a measurable quantity), so they're watch-list, not trade-now. **OGN's "quiet" reading is a trap — it is under a definitive all-cash takeout at $14.00, so the conditioning quiet reflects deal-certainty, not an un-found opportunity.** This is exactly why conditioning is CONTROL not alpha — a low score must be read with the M&A/context overlay.
- **INSP is DISCOVERING** (attention ~0 but positioning .32): the GLP-1-bear short is being put on *before* the retail crowd arrives — a "watch the short build" state, the inverse of a crowded long.
- **Cap-tier guard dominates the large names** (WST, DXCM, RMD, GRMN, CELH): these are flagged CROWDED even with low retail attention. Correct behavior — the street watches $5B+ names; we are NOT early on them.
- **Positioning lag ~26d**; Google Trends + GDELT were UNAVAILABLE on this IP (expected), so attention leans on StockTwits + Wikipedia + FINRA-SI + SEC-FTD. Confidence is MED across the board for that reason.
- **No foreign-listing positioning blind spots in the shortlist** — all 9 shortlist names are US-primary listings, clean for the SMA. (GALD, Hugel, Glanbia would be FOREIGN/positioning-unverifiable, but aesthetics is already in book and Glanbia is a reject.)
- Every screened name is logged with `(ticker, divergence_type, source_connector, detection_date, attention_score, positioning_score, regime)` to `outputs/latency_log.jsonl` per the latency-map mandate.
