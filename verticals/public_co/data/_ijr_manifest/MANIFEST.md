# IJR Universe R/f/M Manifest

**Universe**: 608 IJR holdings as of 2024-06-30 (SEC N-PORT-P)
**Generated**: 2026-05-26 (follows HANDOFF.md)
**Purpose**: For each of 26 GICS-style clusters, enumerate archetypal R-claims (what companies claim in 10-K), f(M) verification sources, and existing-vs-gap m-source coverage. Drives the deterministic IJR exclusion test design.

## Notation

- **R-claim** — assertion typical of cluster's 10-K (Item 1, 1A, 7, or footnotes). Subscripted **C/R** marks catastrophe-detection (lie likely conceals impairment) vs recovery-signal (lie likely conceals false hope).
- **f(M)** — verification mechanism: external data source + the joinable key.
- **m-source** — code module. ✅ = exists, ⚠️ = partial/needs extension, ❌ = gap.
- **Scope** — fraction of cluster names the check covers.

## Coverage legend (cluster-level expected hit-rate, after manifest review)

- **High** = ≥70% of names get ≥3 deterministic m-source checks
- **Med** = 40-70%
- **Low** = <40% (LLM narrative-heavy)

---

## 1. FINANCIALS (n=106) — Coverage: **High** for banks (~60/106), **Low** for insurance (~17/106)

**Top SICs**: State Commercial Banks (28), National Commercial Banks (22), Fire/Marine Casualty (10), Investment Advice (8), Savings Institution (6), Brokers/Dealers (5), Surety (4), Life Insurance (3).
**Reps**: COOP, AGO, LNC, PIPR, HASI, WD.
**Misclass overrides**: MARA → ENERGY (bitcoin miner); MOG/A → INDUSTRIALS_MACHINERY (defense actuators); IBTX → FINANCIALS (was UNKNOWN); PFBC → FINANCIALS.

Bank-heavy cluster splits into sub-archetypes: commercial banks (deposit-funded), insurance carriers (reserve adequacy), broker-dealers (capital + reg standing), asset managers (AUM persistence), specialty finance (book quality).

| # | R-claim (archetypal) | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Deposits stable, no material run risk | C | FDIC Call Report — uninsured deposit %, brokered deposit reliance | `fdic_call_reports.py` ✅ | Banks (~60) |
| 2 | Loan portfolio sound, NPL/charge-offs in line with peers | C | FDIC Call Report — NPL ratio, ALLL, CRE concentration | `fdic_call_reports.py` ⚠️ peer-bench logic to add | Banks |
| 3 | CRE/multifamily exposure manageable | C | Call Report Schedule RC-C — CRE concentration ratios | `fdic_call_reports.py` ⚠️ | Banks (~30 acutely) |
| 4 | Insurance reserves adequate; no PYD risk | C | A.M. Best / state insurance commissioner statutory filings | ❌ GAP `insurance_statutory.py` (state DOI scrape + NAIC) | Insurance (~17) |
| 5 | Broker-dealer in good standing, no FINRA actions | C | FINRA BrokerCheck disclosures, AWC orders | `finra_brokercheck.py` ✅ | Brokers (~5) |
| 6 | AUM persistent; not Vanguard-bleeding | R | 13F-HR filer counts + ADV Part 1 AUM (one-quarter lag) | ⚠️ extend `sec_filings.py` for ADV Part 1 | Asset mgrs (~8) |
| 7 | No undisclosed self-dealing / related-party loans | C | Form 4 + 8-K Item 1.01 anomalies | `form4.py` + `insider_buy_timing.py` ✅ | Universal |
| 8 | Capital ratios meet regulatory minimums | C | Call Report — Tier1, total capital, leverage | `fdic_call_reports.py` ✅ | Banks |
| 9 | No undisclosed material weakness in ICFR | C | Item 9A history + auditor turnover | `mw_lifecycle.py` + `auditor_change_tracker.py` ✅ | Universal |
| 10 | Insurance line — no cat exposure undisclosed | C | NAIC SERFF rate filings, state cat models | ❌ GAP `naic_serff.py` | P&C insurance (~10) |
| 11 | Specialty-finance covenants intact | C | Credit agreement amendments, covenant waivers | `lender_concession.py` ✅ | Specialty (~12) |
| 12 | Asset manager — no key-person departure risk | R | Form 4 named-executive churn, 8-K 5.02 | `form4.py` ⚠️ + claim_evolution | Asset mgrs |

**Cluster gaps (priority)**: insurance reserves (`insurance_statutory.py`), NAIC SERFF (`naic_serff.py`), ADV Part 1 extension.

---

## 2. REAL_ESTATE (n=56) — Coverage: **Med**

**Top SICs**: REITs (47), Real Estate (7), Real Estate Agents/Managers (2).
**Reps**: EPRT, PECO, SLG, CTRE, MAC, APLE, IIPR, BXMT.

Splits: net-lease REITs (EPRT, IIPR), shopping center (PECO, MAC), office (SLG), healthcare (CTRE, MPW), hospitality (APLE), mortgage REIT (BXMT). Catastrophe risks differ sharply: office = tenant occupancy / WALT; mREIT = mark-to-market book value / repo-margin; cannabis/specialty = tenant credit (IIPR).

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Occupancy stable, no tenant cluster risk | C | Tenant disclosure in 10-K + property tax records cross-ref | ⚠️ extend `revenue_concentration.py` for tenant rollup | All REITs |
| 2 | WALT (weighted-avg lease term) consistent across filings | C | 10-K supplements YoY | `claim_evolution.py` ✅ | All REITs |
| 3 | Rent roll — no large tenant on watchlist (e.g., Steward, Walgreens, anchor) | C | Cross-ref tenant filings; Form 8-K material customer events; CoStar peer data | ❌ GAP `tenant_credit_watch.py` (10-K named-tenant extraction + 8-K mat-customer) | All REITs |
| 4 | mREIT book value not understated marks | C | 10-Q book value evolution + repo-counterparty haircut disclosures | `claim_evolution.py` ⚠️ for mREIT-specific | mREITs (~5) |
| 5 | Healthcare REIT tenant solvent (Steward-style risk) | C | Tenant 10-K + Medicare cost reports + state nursing-home filings | ❌ GAP `cms_cost_reports.py` (CMS HCRIS) | Healthcare REITs (~6) |
| 6 | Cannabis REIT — tenant licensure intact (IIPR risk) | C | State cannabis license registries (CO, FL, MI, MA, NJ, CA) | ❌ GAP `cannabis_licenses.py` | IIPR + similar (~2) |
| 7 | Cap rate / NAV justified vs comp transactions | R | Greentree / Real Capital Analytics + cap-rate disclosures | ❌ GAP `cap_rate_bench.py` (RCA-style proxy) | All REITs |
| 8 | Refinancing risk — debt maturity ladder digestible | C | 10-K debt schedule + interest-rate hedge disclosures | `claim_evolution.py` ⚠️ | All REITs |
| 9 | Covenant compliance on credit facility | C | Lender concession / waiver tracking | `lender_concession.py` ✅ | All REITs |
| 10 | Going concern absent | C | Item 7 + auditor language | `going_concern_detector.py` ✅ | Universal |
| 11 | Insider buying signals book-value support | R | Form 4 net purchases by C-suite/board | `insider_buy_timing.py` ✅ | All REITs |
| 12 | Same-store NOI growth as disclosed | R | Multi-period 10-K same-store metrics reconciliation | ⚠️ extend `claim_evolution.py` for SS-NOI | All REITs |

**Cluster gaps (priority)**: tenant_credit_watch (huge — Steward-style catches), CMS HCRIS, cannabis_licenses, cap_rate_bench.

---

## 3. INDUSTRIALS_MACHINERY (n=33) — Coverage: **Med**

**Top SICs**: Oil/Gas Field Machinery (3), Refrigeration (3), Coating/Engraving (2), Aircraft Parts (2), Railroad Equip (2), Special Industry (2), Farm Machinery (2), Ordnance (2).
**Reps**: SPXC, AVAV, ACLS, ACA, WHD, GMS, JBT, VECO.
**Misclass include**: MOG/A (defense actuators), AVAV (drones).

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Order backlog converts to revenue on schedule | C | Backlog disclosures evolution across 10-Qs | `claim_evolution.py` ✅ | All |
| 2 | No customer concentration that mechanically breaks revenue | C | 10-K Item 1 + Schedule II + segment breakdown | `revenue_concentration.py` ✅ | All |
| 3 | DoD/aerospace contract awards real (AVAV, MOG/A) | C | USAspending + FPDS-NG + SAM.gov registration | `usaspending.py` + `sam_entity.py` ✅ | Defense subset (~5) |
| 4 | Aerospace OEM ramp consistent (Boeing/Airbus tier risk) | C | FAA production rate + customer 10-K rate disclosures | ❌ GAP `oem_rate_tracker.py` (Boeing 737/787, Airbus rate) | A&P (~4) |
| 5 | Capex maintained, plant utilization not falling | R | 10-K plant list cross-ref EPA FRS facility data | `epa_frs.py` ✅ | All with US plants |
| 6 | OSHA safety record not deteriorating | C | OSHA inspection records | `osha_establishments.py` ✅ | All US-mfg |
| 7 | Patents (innovation pipeline) real, not lapsed | R | USPTO continuations + maintenance fees + ODP | `google_patents.py` + `uspto_odp.py` ✅ | Tech-heavy (~10) |
| 8 | Supplier concentration (chips/rare-earth) manageable | C | Item 1A + claim evolution YoY | `claim_evolution.py` ⚠️ | All |
| 9 | Working capital — inventory not building disproportionately | R | 10-Q inventory delta vs revenue delta | ❌ GAP `working_capital_drift.py` | All |
| 10 | No material weakness or auditor change | C | Item 9A + auditor tracking | `mw_lifecycle.py` + `auditor_change_tracker.py` ✅ | Universal |
| 11 | Insider conviction at price levels | R | Form 4 purchases | `insider_buy_timing.py` ✅ | Universal |
| 12 | No undisclosed FCPA / export-control issues | C | OFAC, BIS, DDTC sanctions + DOJ FCPA case docket | ❌ GAP `export_control_check.py` (BIS, DDTC, OFAC) | Export-heavy (~8) |

**Cluster gaps (priority)**: working_capital_drift (universal!), oem_rate_tracker, export_control_check.

---

## 4. TECH_HARDWARE (n=31) — Coverage: **Med**

**Top SICs**: Semiconductors (14), PCBs (5), Electronic Components (3), Computer Comm Equip (3), Computer Periph (2).
**Reps**: FORM, AEIS, SANM, DIOD, PLXS, KLIC, UCTT, SITM.

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Customer concentration manageable; not single-fab dependent | C | 10-K named customers + customer 10-K cross-ref | `revenue_concentration.py` + `counterparty_reciprocity.py` ✅ | All semis |
| 2 | Cycle inventory not a hidden write-down | C | 10-Q inventory days, segment inventory by node | ❌ GAP `working_capital_drift.py` | All |
| 3 | Patents valid; no PAE litigation risk material | R | USPTO ODP + PACER/Lex Machina docket | `uspto_odp.py` + `google_patents.py` ⚠️ + ❌ GAP `patent_litigation.py` | All |
| 4 | Export-controlled tech compliant (US-China) | C | BIS entity list + denied parties + 10-K Item 1A | ❌ GAP `export_control_check.py` | Semis with China revenue (~14) |
| 5 | Foundry capacity allocations real (TSMC, Samsung) | C | Supplier 10-K cross-ref; capacity reservation disclosures | `counterparty_reciprocity.py` ⚠️ | Fabless |
| 6 | H1B / engineering headcount supports R&D claims | R | DoL LCA filings | `dol_h1b_lca.py` ✅ | All |
| 7 | Revenue forward — design-win pipeline real | R | Customer 8-K design-in disclosures, IDM roadmap | ❌ GAP `design_win_proxy.py` | Hard |
| 8 | No undisclosed RMA / quality recall | C | Customer 8-K, openFDA (if med-grade), self-text | `edgar_fts.py` ⚠️ for "recall" tokens | All |
| 9 | Insider conviction | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 10 | No material weakness | C | Item 9A | `mw_lifecycle.py` ✅ | Universal |
| 11 | M&A coherence — recent deals deliver | R | 10-K acquisition coherence | `acq_coherence.py` ✅ | Acquirers |
| 12 | No going concern | C | Item 7 + auditor | `going_concern_detector.py` ✅ | Universal |

**Cluster gaps (priority)**: working_capital_drift, export_control_check, patent_litigation, design_win_proxy.

---

## 5. BUSINESS_SERVICES (n=30) — Coverage: **Med**

**Top SICs**: Computer Processing/Data Prep (7), Help Supply Services (5), Business Services NEC (4), Services to Dwellings (3), Misc Business (2), Employment Agencies (2), Management Consulting (2), Equipment Rental (2).
**Reps**: RHI, KFY, DXC, ABM, FTDR, MPW (misclass — REIT, override to REAL_ESTATE), EVTC, CARG.
**Misclass override**: MPW → REAL_ESTATE.

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Staffing demand stable (BLS-corroborated for RHI, KFY) | R | BLS QCEW employment+wage data by NAICS | `bls_qcew.py` ✅ | Staffing (~7) |
| 2 | Permanent-placement vs temp-mix stable | R | 10-K segment + BLS labor flow | `bls_qcew.py` ⚠️ | Staffing |
| 3 | Customer concentration — no single-client cliff | C | 10-K named clients + segment | `revenue_concentration.py` ✅ | All |
| 4 | IT services contract pipeline (DXC) genuine | C | USAspending federal IT awards; SAM registration | `usaspending.py` + `sam_entity.py` ✅ | Fed IT (~5) |
| 5 | SaaS-adj. — gross revenue retention claim real | C | 10-K segment + cohort disclosures + claim evolution | `claim_evolution.py` ⚠️ | Software-adj (~8) |
| 6 | No undisclosed litigation drag (wage-hour class actions for staffing) | C | PACER docket + 10-K Item 3 | ❌ GAP `pacer_class_action.py` | Staffing/svcs |
| 7 | Auditor stability | C | Auditor change | `auditor_change_tracker.py` ✅ | Universal |
| 8 | Insider buying | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 9 | Acquisitions integrating | R | acq coherence | `acq_coherence.py` ✅ | Acquirers |
| 10 | Revenue forward — pipeline metrics claimed (CARG inventory listings, ALRM subscribers) | R | Marketplace listings scrape; sub count claim evolution | ❌ GAP `marketplace_health.py` | Marketplace subset |
| 11 | Working capital — DSO not bleeding (fed contracts, payment timing) | R | 10-Q DSO drift | ❌ GAP `working_capital_drift.py` | All |
| 12 | No going concern / material weakness | C | Item 7/9A | `going_concern_detector.py` + `mw_lifecycle.py` ✅ | Universal |

**Cluster gaps**: pacer_class_action, marketplace_health, working_capital_drift.

---

## 6. MATERIALS_CHEMICALS (n=30) — Coverage: **Med**

**Top SICs**: Industrial Organic Chem (3), Plastics NEC (3), Chemicals Allied (3), Medicinal Chem (2), Plastic Resins (2), Paper Mills (2), Perfumes/Cosmetics (2).
**Reps**: BCPC, AWI, FUL, SXT, IOSP, NPO, WDFC.
**Misclass override**: CMA → FINANCIALS (Comerica bank, mis-classified via stale pharma SIC).

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | EPA environmental compliance — no major NOV / consent decree | C | EPA ECHO + emissions inventory | `epa_emissions.py` + `epa_frs.py` ✅ | All US facilities |
| 2 | PFAS / Superfund liability bounded | C | EPA CERCLIS / Superfund + 10-K Item 3 contingencies | ⚠️ extend `epa_frs.py` for Superfund | ~30% of cluster |
| 3 | OSHA / chemical incident rate not deteriorating | C | OSHA + CSB investigations | `osha_establishments.py` ✅ | All |
| 4 | Customer concentration manageable | C | 10-K named customers | `revenue_concentration.py` ✅ | All |
| 5 | Raw-material pass-through real (margin claim) | R | Input cost indices (BLS PPI by chemical, NYMEX) + GM bridge | ❌ GAP `cogs_pass_through.py` | All |
| 6 | Capex maintenance vs growth split disclosed | R | 10-K capex breakout consistency | `claim_evolution.py` ⚠️ | All |
| 7 | No undisclosed product-liability litigation | C | PACER docket + state AG tort filings + Item 3 | ❌ GAP `pacer_class_action.py` | All |
| 8 | Working capital — inventory not stockpile-overhanging | R | DSI drift | ❌ GAP `working_capital_drift.py` | All |
| 9 | Insider conviction | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 10 | No material weakness | C | Item 9A | `mw_lifecycle.py` ✅ | Universal |
| 11 | Acquisition coherence (FUL, IOSP, NPO are serial acquirers) | R | acq coherence | `acq_coherence.py` ✅ | Acquirers |
| 12 | No going concern | C | Item 7 + auditor | `going_concern_detector.py` ✅ | Universal |

**Cluster gaps**: Superfund extension to epa_frs, cogs_pass_through, pacer_class_action.

---

## 7. CONSUMER_RETAIL (n=27) — Coverage: **Low-Med**

**Top SICs**: Auto Dealers (4), Family Clothing (4), Shoe Stores (3), Misc Shopping (3), Catalog/Mail-Order (2), Auto/Home Supply (2), Retail NEC (2).
**Reps**: ANF, NSIT, ABG, SIG, ASO, GPI, BOOT, AAP.

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Same-store sales / comp transactions as reported | C | Multi-period 10-Q same-store reconciliation | `claim_evolution.py` ⚠️ for comp drift | All |
| 2 | Foot-traffic / e-com mix not deteriorating beyond disclosed | C | Placer.ai / SafeGraph / app-store rank + Google Trends | ❌ GAP `consumer_traffic_proxy.py` | All physical retail |
| 3 | Inventory clean (no markdown overhang — AAP, GPS-style blowup) | C | 10-Q inventory/revenue ratio drift + Q-end vs FY-end | ❌ GAP `working_capital_drift.py` | All retail |
| 4 | Lease maturity ladder digestible (store closures real) | C | 10-K lease ladder + store-count reconciliation | `claim_evolution.py` ⚠️ | All physical retail |
| 5 | No undisclosed cyber breach (Item 1C SEC rule 2023+) | C | Item 1C cyber + 8-K Item 1.05 | ⚠️ extend `edgar_fts.py` for Item 1.05 hits | Universal |
| 6 | Wage-hour / ADA / class-action exposure bounded | C | PACER + state AG filings | ❌ GAP `pacer_class_action.py` | All |
| 7 | Auto dealers — F&I income & captive-finance reliance disclosed | C | 10-K + auto SAAR (FRED) + Manheim used-car index | ❌ GAP `auto_dealer_signals.py` | Auto dealers (~6) |
| 8 | Tariff / sourcing concentration (China, Vietnam) flagged | C | 10-K + customs ImportGenius/Panjiva | ❌ GAP `import_concentration.py` | Apparel/shoe (~10) |
| 9 | No going concern | C | Item 7 + auditor | `going_concern_detector.py` ✅ | Universal |
| 10 | Insider conviction at down-cycle prices | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 11 | Liquidity adequate post-debt amendment | C | Lender concession tracking | `lender_concession.py` ✅ | Distressed (~8) |
| 12 | E-com investment translates to revenue | R | Digital revenue claim YoY consistency | `claim_evolution.py` ⚠️ | All |

**Cluster gaps**: consumer_traffic_proxy (Placer.ai-style), auto_dealer_signals, import_concentration, working_capital_drift.

---

## 8. CONSUMER_DISCRETIONARY (n=26) — Coverage: **Med**

**Top SICs**: Motor Vehicle Parts (7), Hotels & Motels (4), Footwear (3), Men/Boys Apparel (3), Auto Repair (2).
**Reps**: FSS, VFC, KTB, BRC, SHOO, PENN, AIN, LCII.

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | OEM tier exposure — F-150/Bronco/Tesla rate decisions disclosed | C | OEM 10-K production rate + customer letters | ❌ GAP `oem_rate_tracker.py` | Auto parts (~7) |
| 2 | Hotel ADR/RevPAR/occupancy reconciled | C | STR-style proxy via 10-Q segment + Smith Travel quarterly | ❌ GAP `hotel_revpar_proxy.py` | Hotels (~4) |
| 3 | Casino — regional gaming revenue real (PENN) | C | State gaming commission monthly reports (PA, NJ, MI, IN, NV) | ❌ GAP `state_gaming_reports.py` | PENN, similar (~2) |
| 4 | Inventory clean (apparel rolloff risk) | C | DSI drift | ❌ GAP `working_capital_drift.py` | All apparel |
| 5 | Tariff / sourcing concentration | C | Customs data | ❌ GAP `import_concentration.py` | Apparel/footwear |
| 6 | NHTSA recall events bounded (auto parts) | C | NHTSA recalls database | `nhtsa.py` ✅ | Auto parts (~9) |
| 7 | OSHA / EPA compliance | C | OSHA + EPA | `osha_establishments.py` + `epa_frs.py` ✅ | All US mfg |
| 8 | Customer concentration | C | 10-K named | `revenue_concentration.py` ✅ | All |
| 9 | No material weakness | C | Item 9A | `mw_lifecycle.py` ✅ | Universal |
| 10 | Insider conviction | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 11 | Acquisition coherence | R | acq coherence | `acq_coherence.py` ✅ | Acquirers |
| 12 | Lender concession history | C | covenant amendments | `lender_concession.py` ✅ | Distressed (~6) |

**Cluster gaps**: oem_rate_tracker, hotel_revpar_proxy, state_gaming_reports, working_capital_drift, import_concentration.

---

## 9. HEALTHCARE_PHARMA (n=25) — Coverage: **High**

**Top SICs**: Pharma Preparations (21), Biological Products (4).
**Reps**: OGN, KRYS, ALKS, PBH, CORT, VCEL, PINC, CPRX.

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Trial enrollment / readout claims (timing & sample) real | C | ClinicalTrials.gov + enrollment milestones | `clinical_trials.py` ✅ | All clinical-stage |
| 2 | FDA AE / Form FDA-483 / warning letter status | C | openFDA AE + 483/WL inspection database | `openfda.py` ✅ | All |
| 3 | Pipeline NCT IDs match claimed assets | C | Cross-ref 10-K asset list to CT.gov sponsor field | `clinical_trials.py` ⚠️ + claim_evolution | All clinical |
| 4 | Patents valid (Orange Book ladder real) | R | Orange Book + USPTO ODP + IPR/PGR petitions | `uspto_odp.py` + ❌ GAP `orange_book.py` | All marketed Rx |
| 5 | Manufacturing inspection clean | C | FDA inspection database, EMA EudraGMDP | `openfda.py` ⚠️ + ❌ GAP `eu_gmp.py` | All |
| 6 | DEA / controlled-substance compliance | C | DEA registration + diversion control history | ❌ GAP `dea_registration.py` | Schedule II-V (~5) |
| 7 | Customer concentration — 340B / PBM / wholesaler | C | 10-K named (McKesson, CVS, Cardinal) | `revenue_concentration.py` ✅ | All commercial |
| 8 | Royalty / milestone receipts on schedule | R | Counterparty 10-K cross-ref + 10-K disclosures | `counterparty_reciprocity.py` ✅ | Royalty-recipients |
| 9 | No material weakness | C | Item 9A | `mw_lifecycle.py` ✅ | Universal |
| 10 | Insider conviction at trough | R | Form 4 + 10b5-1 plan adoption timing | `insider_buy_timing.py` + `insider_vs_calendar.py` ✅ | Universal |
| 11 | Going concern absent for development-stage | C | Item 7 + cash runway calc | `going_concern_detector.py` ✅ + ❌ GAP `runway_calculator.py` | Dev-stage (~6) |
| 12 | Reverse-stock-split / dilution telegraphed | C | S-3 ATM activity, share count drift | ❌ GAP `share_count_drift.py` | Dev-stage |

**Cluster gaps**: orange_book, dea_registration, eu_gmp, runway_calculator, share_count_drift.

---

## 10. TECH_SOFTWARE_SERVICES (n=23) — Coverage: **Low-Med**

**Top SICs**: Prepackaged Software (12), Computer Programming/Data Processing (7), Computer Integrated Systems (3), Computer Programming Services (1).
**Reps**: SPSC, ACIW, BOX, IAC, ALRM, DV, PRFT, BL.

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | NRR / GRR claims as reported (cohort math) | C | Multi-year cohort metric claim evolution | `claim_evolution.py` ⚠️ | All SaaS |
| 2 | RPO / cRPO consistent with revenue | C | 10-Q cRPO/revenue ratio drift | ❌ GAP `rpo_drift.py` | All SaaS |
| 3 | Customer concentration / public-sector mix | C | 10-K named + USAspending if fed | `revenue_concentration.py` + `usaspending.py` ✅ | All |
| 4 | Headcount supports growth claim | R | DOL LCA filings + LinkedIn-proxy | `dol_h1b_lca.py` ✅ + ❌ GAP `headcount_proxy.py` | All |
| 5 | Bookings backlog real, not stuffed | C | Bookings/billings claim evolution | `claim_evolution.py` ⚠️ | All |
| 6 | No undisclosed cyber breach | C | Item 1C + 8-K Item 1.05 | `edgar_fts.py` ⚠️ | Universal |
| 7 | Stock-based comp not gross-up-hidden | R | SBC/revenue ratio + non-GAAP reconciliation drift | ❌ GAP `sbc_quality_check.py` | All |
| 8 | Insider conviction at trough multiples | R | Form 4 + 10b5-1 timing | `insider_buy_timing.py` + `insider_vs_calendar.py` ✅ | Universal |
| 9 | No material weakness | C | Item 9A | `mw_lifecycle.py` ✅ | Universal |
| 10 | M&A integrating; no goodwill impairment looming | R | acq coherence + claim evolution on segment EBITDA | `acq_coherence.py` ✅ + ⚠️ extend | Acquirers (BOX, IAC) |
| 11 | No going concern | C | Item 7 + auditor | `going_concern_detector.py` ✅ | Universal |
| 12 | Patents (where claimed competitive moat) | R | USPTO + ODP | `google_patents.py` + `uspto_odp.py` ✅ | Patent-pitched (~5) |

**Cluster gaps**: rpo_drift, headcount_proxy, sbc_quality_check.

---

## 11. ENERGY (n=23) — Coverage: **Med**

**Top SICs**: Crude Petroleum/Natural Gas (8), Oil/Gas Field Services (6), Drilling (3), Bituminous Coal (2), Silver Ores (2), Refining (1).
**Reps**: SM, MGY, HP, CRC, NOG, AMR, PTEN, LBRT.
**Misclass include**: MARA (bitcoin miner) → ENERGY; ARCH (Arch Resources) → ENERGY.

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Proved reserves SEC-disclosed not overstated (5-year revisions) | C | 10-K SMOG + EIA / state O&G regulator production data | ❌ GAP `reserves_revision.py` (EIA + RRC + NDIC) | E&P (~10) |
| 2 | Hedging book covers near-term decline | R | 10-Q hedge schedule + forward curve | ❌ GAP `hedge_book_check.py` (NYMEX, ICE) | E&P |
| 3 | Rig count / frac fleet utilization disclosed | C | Baker Hughes rig count + Enverus | ❌ GAP `rig_utilization.py` | Drillers/services |
| 4 | Coal mine compliance — MSHA violations bounded | C | MSHA injury/violation database | ❌ GAP `msha_violations.py` | Coal (~3) |
| 5 | EPA Method 21 / emissions compliance | C | EPA GHGRP + emissions inventory | `epa_emissions.py` + `epa_frs.py` ✅ | All US ops |
| 6 | Decommissioning / ARO liability not understated | C | 10-K AROs + state bonding requirements | ⚠️ extend `claim_evolution.py` | E&P, services |
| 7 | Lender concession / borrowing-base redeterminations | C | Credit facility amendments | `lender_concession.py` ✅ | E&P highly levered |
| 8 | No going concern | C | Item 7 + auditor | `going_concern_detector.py` ✅ | Universal |
| 9 | Bitcoin miner — hash rate / energy cost claims (MARA) | C | On-chain hash share + state-PUC power agreements | ❌ GAP `btc_miner_signals.py` | MARA + IREN-like (~2) |
| 10 | Insider conviction at commodity-trough | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 11 | Acquisition coherence (NOG-style minerals roll-ups) | R | acq coherence | `acq_coherence.py` ✅ | Acquirers |
| 12 | Customer / midstream concentration | C | 10-K named (often gathering/pipeline) | `revenue_concentration.py` ✅ | All |

**Cluster gaps**: reserves_revision, hedge_book_check, rig_utilization, msha_violations, btc_miner_signals.

---

## 12. INDUSTRIALS_CONSTRUCTION (n=21) — Coverage: **Med**

**Top SICs**: Operative Builders (6), Household Furniture (2), Water/Sewer/Pipeline (2), Wood Household Furn (2), General Bldg Contractors (2).
**Reps**: MTH, DY, IBP, TPH, MHO, GVA, CVCO, CCS.

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Homebuilder community count / absorption consistent | C | Census new-home sales + state recorder permits | ❌ GAP `homebuilder_permits.py` (Census BPS + local) | Builders (~8) |
| 2 | Backlog/contract pipeline real (Dycom, Granite) | C | USAspending fed infra + state DOT awards + claim evolution | `usaspending.py` ✅ + ❌ GAP `state_dot_awards.py` | Contractors (~5) |
| 3 | Mortgage rate sensitivity disclosed candidly | C | 10-K rate-environment language drift | `claim_evolution.py` ⚠️ | Builders |
| 4 | Land position / cancellation rate trend | C | 10-K lots-owned/controlled + cancellation rate | `claim_evolution.py` ⚠️ | Builders |
| 5 | OSHA safety record | C | OSHA construction | `osha_establishments.py` ✅ | All US |
| 6 | EPA / wetland compliance for site dev | C | EPA + Army Corps 404 permits | `epa_frs.py` ✅ + ❌ GAP `usace_404.py` | Builders, Granite |
| 7 | Working capital — inventory build (spec-home risk) | R | DSI drift, spec vs sold mix | ❌ GAP `working_capital_drift.py` | Builders |
| 8 | Lender concession on rev-credit fac | C | Lender amendments | `lender_concession.py` ✅ | All |
| 9 | Insider conviction at cycle trough | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 10 | No material weakness | C | Item 9A | `mw_lifecycle.py` ✅ | Universal |
| 11 | No going concern | C | Item 7 + auditor | `going_concern_detector.py` ✅ | Universal |
| 12 | Telecom infra customer concentration (DY: AT&T, Lumen, Verizon) | C | 10-K named + customer 10-K cross-ref | `revenue_concentration.py` + `counterparty_reciprocity.py` ✅ | Telecom infra (~3) |

**Cluster gaps**: homebuilder_permits, state_dot_awards, usace_404, working_capital_drift.

---

## 13. INDUSTRIALS_TRANSPORT (n=19) — Coverage: **Med**

**Top SICs**: Air Transport Scheduled (5), Trucking (4), Water Transport (3), Freight Arrangement (2), Air Nonscheduled (2), Transp Services (2).
**Reps**: ALK, VRRM, MATX, TDW, SKYW, RXO, HUBG, ARCB.

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Airline RASM/CASM/load-factor reconciled | C | BTS T-100 + DOT Form 41 monthly | ❌ GAP `bts_airline_metrics.py` | Airlines (~7) |
| 2 | OTP (on-time performance) not concealed deteriorating | C | BTS OTP monthly | ❌ GAP `bts_airline_metrics.py` | Airlines |
| 3 | FAA airworthiness / accident history (ALK MAX-9, etc.) | C | NTSB + FAA enforcement | ❌ GAP `faa_enforcement.py` | Airlines + non-sched |
| 4 | Trucking — FMCSA safety scores not deteriorating | C | FMCSA SMS BASIC scores | `fmcsa.py` ✅ | Trucking (~4) |
| 5 | Truck OOS (out-of-service) rate per-mile-driven | C | FMCSA roadside inspection data | `fmcsa.py` ✅ | Trucking |
| 6 | Marine — port congestion / contract rate reset | R | BTS / IMO + claim evolution | ⚠️ extend `claim_evolution.py` | Marine (~3) |
| 7 | Tidewater-style offshore — rig demand consistent | R | Baker Hughes rig + Bassoe/Westwood (proxy via 10-K) | ❌ GAP `rig_utilization.py` | TDW |
| 8 | Pension / OPEB liability not deteriorating | C | 10-K pension footnote evolution | `claim_evolution.py` ⚠️ | Legacy carriers |
| 9 | Lender concession / aircraft-financing | C | Lender amendments | `lender_concession.py` ✅ | Airlines |
| 10 | Insider conviction at fuel-cycle trough | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 11 | No material weakness | C | Item 9A | `mw_lifecycle.py` ✅ | Universal |
| 12 | Customer concentration (RXO, Hub Group brokered freight) | C | 10-K named | `revenue_concentration.py` ✅ | Brokers (~4) |

**Cluster gaps**: bts_airline_metrics, faa_enforcement.

---

## 14. MATERIALS_METALS (n=19) — Coverage: **Med**

**Top SICs**: Steel Works (8 split across two SIC codes), Nonmetallic Mining (3), Rolling Nonferrous (3), Gold/Silver (1).
**Reps**: ATI, MLI, CRS, WIRE, B, ROCK, WOR, KALU.
**Misclass override**: B → INDUSTRIALS_MACHINERY (Barnes Group is industrial, not gold ore).

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Steel/aluminum pricing pass-through (margin claim) | R | BLS PPI by NAICS + GM bridge evolution | ❌ GAP `cogs_pass_through.py` | All |
| 2 | Defense/aerospace ATI/CRS — DPA-funded backlog real | R | DPA Title III + USAspending DLA awards | `usaspending.py` ✅ + ⚠️ extend for DPA | Specialty steel/Ti (~3) |
| 3 | EPA emissions compliance — steel-mill NOx/Hg | C | EPA + emissions inventory | `epa_emissions.py` + `epa_frs.py` ✅ | All US |
| 4 | OSHA / MSHA — mining safety record | C | OSHA + MSHA mine database | `osha_establishments.py` ✅ + ❌ GAP `msha_violations.py` | Mining (~5) |
| 5 | Working capital — scrap/raw inventory not stockpiled | R | DSI drift | ❌ GAP `working_capital_drift.py` | All |
| 6 | Tariff exposure (Section 232, Section 301) | C | 10-K Item 1A + USTR exclusion process | ⚠️ extend `claim_evolution.py` | All |
| 7 | Customer concentration | C | 10-K named | `revenue_concentration.py` ✅ | All |
| 8 | Lender concession / cyclical-trough amendments | C | Lender amendments | `lender_concession.py` ✅ | Levered (~5) |
| 9 | Insider conviction at commodity-trough | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 10 | No material weakness | C | Item 9A | `mw_lifecycle.py` ✅ | Universal |
| 11 | Acquisition coherence (CRS, NPO-style portfolio churn) | R | acq coherence | `acq_coherence.py` ✅ | Acquirers |
| 12 | No going concern | C | Item 7 + auditor | `going_concern_detector.py` ✅ | Universal |

**Cluster gaps**: cogs_pass_through, msha_violations, working_capital_drift.

---

## 15. COMMUNICATIONS (n=17) — Coverage: **Low**

**Top SICs**: Comm Services NEC (5), Telephone Comm (5), Cable TV (3), Books Publishing (2), Telegraph (1).
**Reps**: CCOI, SATS, CALX, TDS, WLY, CABO, ADEA, DLX.

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Sub count not bleeding faster than disclosed (CABO, TDS) | C | FCC Form 477 broadband + state PUC | ❌ GAP `fcc_form_477.py` | Cable/wireless (~6) |
| 2 | ARPU stable across reporting periods | R | Multi-period claim evolution | `claim_evolution.py` ⚠️ | All cable/telco |
| 3 | Capex sustaining DOCSIS / fiber footprint claim | C | Capex/footprint reconciliation + state grant filings | ❌ GAP `bead_grant_tracker.py` (NTIA BEAD) | Cable/telco |
| 4 | FCC license renewal / spectrum holdings disclosed | C | FCC ULS Universal Licensing System | ❌ GAP `fcc_uls.py` | Spectrum holders |
| 5 | Echostar/satellite-orbital risk (SATS Boost/Dish) | C | FCC ITS filings + spectrum auction proceeds | ❌ GAP `fcc_uls.py` | SATS |
| 6 | Royalty / IP licensing pipeline (ADEA) | C | Customer 10-K patent license disclosures + ITC docket | ❌ GAP `patent_litigation.py` | ADEA, IP-licensors |
| 7 | Publishing — print/digital revenue mix (WLY) | R | Multi-period claim evolution | `claim_evolution.py` ⚠️ | WLY, DLX |
| 8 | Lender concession on heavy debt (cable, telecom) | C | Lender amendments | `lender_concession.py` ✅ | All levered |
| 9 | Insider conviction | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 10 | No material weakness | C | Item 9A | `mw_lifecycle.py` ✅ | Universal |
| 11 | Cyber breach not undisclosed (sub data) | C | Item 1C + 8-K 1.05 | `edgar_fts.py` ⚠️ | All carriers |
| 12 | No going concern | C | Item 7 + auditor | `going_concern_detector.py` ✅ | Universal |

**Cluster gaps**: fcc_form_477, fcc_uls, bead_grant_tracker, patent_litigation.

---

## 16. HEALTHCARE_DEVICES (n=16) — Coverage: **High**

**Top SICs**: Surgical/Medical Instruments (11), Electromedical (4), Orthopedic/Prosthetic (1).
**Reps**: GKOS, MMSI, ITGR, TNDM, NARI, ICUI, CNMD, IART.

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | 510(k) / PMA clearance status & MDR adverse events | C | FDA 510(k) + MAUDE adverse events | `openfda.py` ✅ | All |
| 2 | Manufacturing site Form FDA-483 / warning letter clean | C | FDA inspection database | `openfda.py` ⚠️ + ❌ GAP `fda_inspection.py` | All US mfg |
| 3 | Recalls — Class I/II not increasing | C | FDA recall database | `openfda.py` ✅ | All |
| 4 | Reimbursement / CMS coverage stable (IART, TNDM coverage risk) | C | CMS NCD/LCD + CPT coding decisions | ❌ GAP `cms_coverage.py` | All Rx/device |
| 5 | Hospital GPO contract concentration | C | 10-K named GPOs (Vizient, Premier, HPG) | `revenue_concentration.py` ✅ | All |
| 6 | Clinical evidence claim — trial results real | C | ClinicalTrials.gov | `clinical_trials.py` ✅ | Trial-pitching (~8) |
| 7 | Patent / IP — competitive moat | R | USPTO + ODP | `google_patents.py` + `uspto_odp.py` ✅ | All |
| 8 | International approvals real (CE-mark MDR, PMDA) | R | EU EUDAMED + Japan PMDA | ❌ GAP `eudamed.py` | All international |
| 9 | Insider conviction | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 10 | No material weakness | C | Item 9A | `mw_lifecycle.py` ✅ | Universal |
| 11 | Acquisition coherence | R | acq coherence | `acq_coherence.py` ✅ | Acquirers (ITGR, MMSI) |
| 12 | No going concern | C | Item 7 + auditor | `going_concern_detector.py` ✅ | Universal |

**Cluster gaps**: cms_coverage, fda_inspection, eudamed.

---

## 17. HEALTHCARE_SERVICES (n=14) — Coverage: **Med-High**

**Top SICs**: Medical Labs (3), Home Health (3), Hospitals (2), Health Services (2), Skilled Nursing (2), Nursing/Personal Care (1), Commercial Bio Research (1).
**Reps**: ENSG, SEM, RDNT, HI (misclass — INDUSTRIALS), FTRE, ADUS, PRVA, NHC.
**Misclass override**: HI → INDUSTRIALS_MACHINERY (Hillenbrand industrial mfg).

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Medicare cost report data corroborates segment EBITDA (ENSG, NHC, SEM) | C | CMS HCRIS cost reports | ❌ GAP `cms_cost_reports.py` | SNFs, hospitals (~5) |
| 2 | CMS survey deficiencies / civil money penalties | C | CMS Nursing Home Compare + CASPER | ❌ GAP `cms_nursing_home_compare.py` | SNFs (~3) |
| 3 | Hospital quality measures / readmission penalties | C | CMS Hospital Compare + IPPS data | ❌ GAP `cms_hospital_compare.py` | Hospitals (~2) |
| 4 | Reimbursement headwinds disclosed candidly | C | CMS proposed rule comments + 10-K claim evolution | `claim_evolution.py` ⚠️ | All |
| 5 | Home-health 80/20 / OASIS quality data | C | CMS HHCAHPS + survey data | ❌ GAP `cms_home_health.py` | Home health (~3) |
| 6 | CRO / lab clinical trial backlog (FTRE) | R | Customer 10-K cross-ref + ClinicalTrials.gov sponsor | `clinical_trials.py` + `counterparty_reciprocity.py` ✅ | FTRE, similar (~2) |
| 7 | FDA / CAP / CLIA accreditation intact (RDNT, labs) | C | CMS QCOR + FDA inspection | ❌ GAP `cms_qcor.py` | Labs/imaging |
| 8 | OSHA bloodborne pathogen / nursing-home safety | C | OSHA | `osha_establishments.py` ✅ | All US ops |
| 9 | Acquisition coherence (ENSG operator-roll-up) | R | acq coherence | `acq_coherence.py` ✅ | ENSG, ADUS |
| 10 | Lender concession / liquidity covenants | C | Lender amendments | `lender_concession.py` ✅ | Levered |
| 11 | Insider conviction | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 12 | No material weakness / going concern | C | Item 9A/7 | `mw_lifecycle.py` + `going_concern_detector.py` ✅ | Universal |

**Cluster gaps**: cms_cost_reports, cms_nursing_home_compare, cms_hospital_compare, cms_home_health, cms_qcor.

---

## 18. UTILITIES (n=13) — Coverage: **Med**

**Top SICs**: Water Supply (4), Electric (2), Electric/Other Combined (2), NatGas (3 split), Hazardous Waste (1).
**Reps**: OTTR, CWT, AROC, AVA, MGEE, AWR, CPK, CWEN.

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Rate case outcomes / authorized ROE consistent w/ disclosure | C | State PUC docket + 10-K rate-case schedule | ❌ GAP `state_puc_rate_cases.py` | All regulated (~10) |
| 2 | EPA Section 316(b) / cooling-water compliance | C | EPA permits + NPDES | `epa_emissions.py` + `epa_frs.py` ✅ | Thermal gen |
| 3 | Wildfire liability / inverse condemnation (CA) | C | State wildfire reports + claim evolution | ⚠️ extend `claim_evolution.py` | West-coast (~3) |
| 4 | Renewable PTC/ITC monetization real (CWEN, AROC) | R | Treasury tax-credit transfer registry + 10-K | ❌ GAP `irs_tax_credit_transfer.py` | Renewable IPP |
| 5 | Customer / volumetric throughput claims | R | EIA Form 861 / 826 / state filings | ❌ GAP `eia_utility_data.py` | All |
| 6 | Pension / OPEB liability candor | C | Multi-period footnote evolution | `claim_evolution.py` ⚠️ | All |
| 7 | Going concern absent | C | Item 7 + auditor | `going_concern_detector.py` ✅ | Universal |
| 8 | Lender concession / heavy bond maturity | C | Lender amendments | `lender_concession.py` ✅ | All |
| 9 | Insider conviction | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 10 | No material weakness | C | Item 9A | `mw_lifecycle.py` ✅ | Universal |
| 11 | Customer concentration (industrial loads, midstream cust for AROC) | C | 10-K named | `revenue_concentration.py` ✅ | All |
| 12 | M&A coherence (CPK serial acquirer) | R | acq coherence | `acq_coherence.py` ✅ | CPK |

**Cluster gaps**: state_puc_rate_cases, irs_tax_credit_transfer, eia_utility_data.

---

## 19. CONSUMER_STAPLES_DISTRIB (n=12) — Coverage: **Low-Med**

**Top SICs**: Wholesale Misc Nondurable (3), Wholesale Groceries (3), Wholesale Farm Products (2), Wholesale Drugs (1), Wholesale Beer/Wine (1), Wholesale Chemicals (1), Wholesale Petroleum (1).
**Reps**: CENTA, HWKN, VSTS, ANDE, WKC, CHEF, UVV, MGPI.

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Spread / arbitrage margin disclosed consistently | R | Commodity index (CBOT, NYMEX) + GM bridge | ❌ GAP `cogs_pass_through.py` | All distrib |
| 2 | Customer concentration (foodservice, retail chain) | C | 10-K named | `revenue_concentration.py` ✅ | All |
| 3 | Inventory days not building | R | DSI drift | ❌ GAP `working_capital_drift.py` | All |
| 4 | Pension / OPEB (legacy distrib) | C | Footnote evolution | `claim_evolution.py` ⚠️ | Legacy (UVV, etc.) |
| 5 | Crop year / harvest disclosures (ANDE, UVV) | R | USDA NASS + claim evolution | ❌ GAP `usda_nass.py` | Ag distrib (~2) |
| 6 | DEA controlled-sub compliance (drug wholesale) | C | DEA registration | ❌ GAP `dea_registration.py` | Pharma distrib (~1) |
| 7 | Lender concession | C | Lender amendments | `lender_concession.py` ✅ | All |
| 8 | Insider conviction | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 9 | No material weakness | C | Item 9A | `mw_lifecycle.py` ✅ | Universal |
| 10 | Acquisition coherence | R | acq coherence | `acq_coherence.py` ✅ | Acquirers |
| 11 | No going concern | C | Item 7 + auditor | `going_concern_detector.py` ✅ | Universal |
| 12 | OSHA — distribution-center safety | C | OSHA | `osha_establishments.py` ✅ | All US |

**Cluster gaps**: cogs_pass_through, working_capital_drift, usda_nass, dea_registration.

---

## 20. CONSUMER_RESTAURANTS (n=12) — Coverage: **Low-Med**

**Top SICs**: Retail Eating Places (12).
**Reps**: SHAK, EAT, FL (misclass — retail), CAKE, BLMN, PZZA, PLAY, JACK.
**Misclass override**: FL → CONSUMER_RETAIL (Foot Locker).

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Same-store sales / traffic / check growth real | C | Multi-period reconciliation + Placer.ai/SafeGraph foot traffic | `claim_evolution.py` ⚠️ + ❌ GAP `consumer_traffic_proxy.py` | All |
| 2 | Unit count / opening guidance met | C | 10-K unit count claim evolution | `claim_evolution.py` ⚠️ | All |
| 3 | Franchise vs company-operated mix | R | 10-K segment | `claim_evolution.py` ⚠️ | Franchisors |
| 4 | FDA Reportable Food Registry / outbreak risk | C | FDA RFR + CDC outbreak data | ❌ GAP `fda_rfr.py` | All |
| 5 | App downloads / digital-mix claims | R | App-store rank + claim evolution | ❌ GAP `app_store_rank.py` | Digital-pitched (~5) |
| 6 | Wage-hour class action exposure | C | PACER + state AG | ❌ GAP `pacer_class_action.py` | All |
| 7 | Lease maturity / store closure schedule | C | 10-K lease ladder | `claim_evolution.py` ⚠️ | All |
| 8 | Lender concession (BLMN, JACK levered) | C | Lender amendments | `lender_concession.py` ✅ | Levered (~5) |
| 9 | Insider conviction | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 10 | No material weakness | C | Item 9A | `mw_lifecycle.py` ✅ | Universal |
| 11 | No going concern | C | Item 7 + auditor | `going_concern_detector.py` ✅ | Universal |
| 12 | Inventory / commodity hedge (beef, dairy) | R | Hedge book + commodity reconciliation | ❌ GAP `hedge_book_check.py` | Casual dining (~6) |

**Cluster gaps**: consumer_traffic_proxy, fda_rfr, app_store_rank, pacer_class_action.

---

## 21. INDUSTRIALS_ELECTRICAL (n=11) — Coverage: **Med**

**Top SICs**: Misc Elec Mach (3), Household Audio/Video (2), Elec Industrial App (1), Radio/TV Broadcast Equip (1).
**Reps**: FN, FELE, ESE, RUN, ENR, SONO, THS (misclass — staples), KN.
**Misclass override**: THS → CONSUMER_STAPLES_FOOD (TreeHouse Foods).

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Optical/photonics customer concentration (FN: Cisco, Ciena) | C | 10-K + customer 10-K | `revenue_concentration.py` + `counterparty_reciprocity.py` ✅ | FN, similar |
| 2 | Solar — ITC monetization & residential install rate (RUN) | C | EIA + state PUC interconnection queues + claim evolution | ❌ GAP `solar_install_proxy.py` | RUN |
| 3 | Sunrun-style — net-customer-add candor | C | Cohort claim evolution | `claim_evolution.py` ⚠️ | RUN |
| 4 | DOL H1B — engineering headcount supports R&D | R | LCA data | `dol_h1b_lca.py` ✅ | All |
| 5 | Patents — Sonos audio IP | R | USPTO + ITC docket | `google_patents.py` + `uspto_odp.py` + ❌ GAP `patent_litigation.py` | SONO |
| 6 | Battery / cell supplier concentration | C | 10-K + counterparty | `revenue_concentration.py` ✅ | RUN, ENR |
| 7 | Customer warranty / RMA disclosure | C | Item 7 contingencies + claim evolution | `claim_evolution.py` ⚠️ | All |
| 8 | Lender concession | C | Lender amendments | `lender_concession.py` ✅ | Levered (RUN) |
| 9 | Insider conviction | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 10 | No material weakness | C | Item 9A | `mw_lifecycle.py` ✅ | Universal |
| 11 | No going concern | C | Item 7 + auditor | `going_concern_detector.py` ✅ | Universal |
| 12 | Acquisition coherence | R | acq coherence | `acq_coherence.py` ✅ | Acquirers |

**Cluster gaps**: solar_install_proxy, patent_litigation.

---

## 22. CONSUMER_SERVICES (n=10) — Coverage: **Low-Med**

**Top SICs**: Misc Amusement (3), Educational Services (3), Personal Services (2), Services NEC (1), Motion Picture Theaters (1).
**Reps**: MSGS, LRN, UNF, YELP, STRA, CNK, KAR, PRDO.

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | For-profit education — Title IV/IPEDS metrics (STRA, LRN, PRDO) | C | IPEDS + Title IV default rates | ❌ GAP `ipeds_title_iv.py` | For-profit edu (~3) |
| 2 | Accreditation status intact | C | DoE accreditation list + state authorization | ❌ GAP `accreditation_status.py` | For-profit edu |
| 3 | Enrollment claims reconcile to IPEDS submissions | C | IPEDS lag + claim evolution | ❌ GAP `ipeds_title_iv.py` | For-profit edu |
| 4 | Yelp reviews/click-through claims | R | Yelp public API + claim evolution | `claim_evolution.py` ⚠️ | YELP |
| 5 | Sports/entertainment — gate / sponsorship reconciled | R | League data + MSG-specific filings | ❌ GAP (LLM-narrative for MSGS) | MSGS |
| 6 | Cinema — box-office share consistent w/ disclosed | R | NATO/Comscore + 10-K | ❌ GAP `box_office_share.py` | CNK |
| 7 | Auction-flow / KAR-style vehicle volume (OPENLANE) | R | Manheim + claim evolution | ❌ GAP `auto_auction_volume.py` | KAR |
| 8 | OSHA / wage-hour | C | OSHA + PACER | `osha_establishments.py` ✅ + ❌ GAP `pacer_class_action.py` | All |
| 9 | Lender concession | C | Lender amendments | `lender_concession.py` ✅ | Levered |
| 10 | Insider conviction | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 11 | No material weakness / going concern | C | Item 9A/7 | `mw_lifecycle.py` + `going_concern_detector.py` ✅ | Universal |
| 12 | Customer concentration | C | 10-K named | `revenue_concentration.py` ✅ | All |

**Cluster gaps**: ipeds_title_iv, accreditation_status, box_office_share, auto_auction_volume, pacer_class_action.

---

## 23. UNKNOWN (n=10) — Coverage: **N/A — needs manual reclassification**

**Reps**: SEE (Sealed Air → MATERIALS_CHEMICALS), ARCH (Arch Resources → ENERGY), ATGE (Adtalem Education → CONSUMER_SERVICES), IBTX (Indep Bank → FINANCIALS), AXL (American Axle → CONSUMER_DISCRETIONARY), CWEN/A (dup of CWEN → UTILITIES), HAYN (Haynes International → MATERIALS_METALS), PFBC (Preferred Bank → FINANCIALS).

All have no CIK or SIC; the underlying enrichment failed. **Action**: Re-run CIK/SIC enrichment with name-resolution fallback, then assign to existing clusters via override table. No new R/f/M tuples — these inherit from target cluster manifest entries above.

---

## 24. CONSUMER_STAPLES_FOOD (n=9) — Coverage: **Med**

**Top SICs**: Food and Kindred (3), Sugar/Confectionery (2), Cigarettes (2), Soft Drinks (1), Cookies/Crackers (1).
**Reps**: AL (misclass — aircraft leasing), SMPL, JJSF, VGR, FIZZ, JBSS, BGS, HAIN, MGPI (dup with cluster 19).
**Misclass override**: AL → FINANCIALS or new TRANSPORT_FINANCE sub (aircraft leasing).

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | FDA inspection — food safety (SMPL, BGS, HAIN, JJSF, JBSS) | C | FDA inspection + FSMA records | `openfda.py` ⚠️ + ❌ GAP `fda_food_inspection.py` | All food |
| 2 | FDA Reportable Food Registry / recall events | C | FDA recall feed | `openfda.py` ✅ | All food |
| 3 | Customer concentration (Walmart, Costco) | C | 10-K named | `revenue_concentration.py` ✅ | All |
| 4 | Tobacco — FDA Deeming / PMTA status (VGR) | C | FDA PMTA database + claim evolution | ❌ GAP `fda_pmta.py` | VGR |
| 5 | Hain-style audit / quality issues | C | claim evolution + Item 9A | `claim_evolution.py` + `mw_lifecycle.py` ✅ | All |
| 6 | Commodity hedge (corn, soy, sugar, cocoa) | R | Hedge book + commodity index | ❌ GAP `hedge_book_check.py` | All food |
| 7 | OSHA — food-plant safety | C | OSHA | `osha_establishments.py` ✅ | All US ops |
| 8 | Lender concession (BGS, HAIN distressed) | C | Lender amendments | `lender_concession.py` ✅ | Distressed (~3) |
| 9 | Insider conviction | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 10 | No material weakness / going concern | C | Item 9A/7 | `mw_lifecycle.py` + `going_concern_detector.py` ✅ | Universal |
| 11 | EPA — water discharge from food plants | C | EPA FRS NPDES | `epa_frs.py` ✅ | All US |
| 12 | Acquisition coherence (HAIN-style portfolio prune) | R | acq coherence | `acq_coherence.py` ✅ | Acquirers |

**Cluster gaps**: fda_food_inspection, fda_pmta, hedge_book_check.

---

## 25. INDUSTRIALS_INSTRUMENTS (n=8) — Coverage: **Med**

**Top SICs**: Ophthalmic Goods (2), Instruments Meas (2), Industrial Instr (1), Totalizing Meters (1), Lab Analytical (1), Watches/Clocks (1).
**Reps**: BMI, ITRI, STAA, COHU, EYE, CTKB, MLAB, MOV.

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Utility water-meter / smart-grid backlog (BMI, ITRI) | C | USAspending state/local + claim evolution | `usaspending.py` ✅ + ⚠️ extend for state/local | BMI, ITRI |
| 2 | FDA 510(k) (STAA, EYE ophthalmic) | C | FDA 510(k) | `openfda.py` ✅ | STAA, EYE, CTKB |
| 3 | Lab equipment customer concentration | C | 10-K named (pharma, biotech) | `revenue_concentration.py` ✅ | MLAB, CTKB |
| 4 | Patents / R&D (semicap test equipment — COHU) | R | USPTO + ODP | `google_patents.py` + `uspto_odp.py` ✅ | COHU |
| 5 | Working capital — DSI/DSO drift | R | DSI/DSO drift | ❌ GAP `working_capital_drift.py` | All |
| 6 | Vision-care reimbursement / Medicare LCD (EYE) | C | CMS LCD | ❌ GAP `cms_coverage.py` | EYE |
| 7 | OSHA / EPA compliance | C | OSHA + EPA | `osha_establishments.py` + `epa_frs.py` ✅ | All US |
| 8 | Lender concession | C | Lender amendments | `lender_concession.py` ✅ | Levered |
| 9 | Insider conviction | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 10 | No material weakness | C | Item 9A | `mw_lifecycle.py` ✅ | Universal |
| 11 | Acquisition coherence | R | acq coherence | `acq_coherence.py` ✅ | Acquirers |
| 12 | No going concern | C | Item 7 + auditor | `going_concern_detector.py` ✅ | Universal |

**Cluster gaps**: working_capital_drift, cms_coverage.

---

## 26. INDUSTRIALS_WHOLESALE (n=7) — Coverage: **Low-Med**

**Top SICs**: Wholesale Computers/Peripherals (3), Wholesale Industrial Mach (1), Wholesale Lumber (1), Wholesale Hardware (1), Wholesale Medical/Dental (1).
**Reps**: BCC, REZI, PLUS, PDCO, SCSC, CNXN, DXPE.

| # | R-claim | C/R | f(M) source | m-source | Scope |
|---|---|---|---|---|---|
| 1 | Channel-stuffing / DSO bleed (IT VARs) | C | DSO drift + working capital | ❌ GAP `working_capital_drift.py` | All VARs |
| 2 | Lumber pricing pass-through (BCC) | R | NYMEX lumber + GM bridge | ❌ GAP `cogs_pass_through.py` | BCC |
| 3 | Customer concentration (Resideo, Patterson dental chains) | C | 10-K named | `revenue_concentration.py` ✅ | All |
| 4 | Vendor / OEM concentration (Cisco, HP for VARs) | C | 10-K named vendors | `revenue_concentration.py` + `counterparty_reciprocity.py` ✅ | VARs |
| 5 | OSHA / DC safety | C | OSHA | `osha_establishments.py` ✅ | All US |
| 6 | Lender concession (PDCO distress history) | C | Lender amendments | `lender_concession.py` ✅ | Levered |
| 7 | Insider conviction | R | Form 4 | `insider_buy_timing.py` ✅ | Universal |
| 8 | No material weakness | C | Item 9A | `mw_lifecycle.py` ✅ | Universal |
| 9 | Acquisition coherence (DXPE, PLUS roll-ups) | R | acq coherence | `acq_coherence.py` ✅ | Acquirers |
| 10 | No going concern | C | Item 7 + auditor | `going_concern_detector.py` ✅ | Universal |
| 11 | FDA-controlled medical supply compliance (PDCO) | C | FDA inspection | `openfda.py` ⚠️ + ❌ GAP `fda_inspection.py` | PDCO |
| 12 | Cyber breach disclosure (IT VAR risk) | C | Item 1C + 8-K 1.05 | `edgar_fts.py` ⚠️ | VARs |

**Cluster gaps**: working_capital_drift, cogs_pass_through.

---

# Summary

## Coverage histogram (manifest-implied)

| Coverage tier | Clusters | Names |
|---|---|---|
| **High** (≥70% names get ≥3 deterministic checks) | HEALTHCARE_PHARMA, HEALTHCARE_DEVICES, FINANCIALS-banks subset | ~85 |
| **Med** (40-70%) | REAL_ESTATE, INDUSTRIALS_MACHINERY, TECH_HARDWARE, BUSINESS_SERVICES, MATERIALS_CHEMICALS, CONSUMER_DISCRETIONARY, ENERGY, INDUSTRIALS_CONSTRUCTION, INDUSTRIALS_TRANSPORT, MATERIALS_METALS, HEALTHCARE_SERVICES, UTILITIES, INDUSTRIALS_ELECTRICAL, INDUSTRIALS_INSTRUMENTS, CONSUMER_STAPLES_FOOD | ~290 |
| **Low-Med** (30-50%) | TECH_SOFTWARE_SERVICES, CONSUMER_RETAIL, CONSUMER_STAPLES_DISTRIB, CONSUMER_RESTAURANTS, CONSUMER_SERVICES, INDUSTRIALS_WHOLESALE | ~98 |
| **Low** (<30%) | COMMUNICATIONS, insurance-subset of FINANCIALS | ~50 |
| **UNKNOWN** (needs reclassify) | UNKNOWN | 10 |

**Implication**: With current m-source inventory (~25 modules), ~375/608 (62%) names get high/med coverage on the universal C-claim battery (filing_timeliness, mw_lifecycle, lender_concession, auditor_change, going_concern, form4, insider_buy_timing, revenue_concentration, edgar_fts) — but cluster-specific signal varies widely.

## Universal m-source battery (apply to ALL 608)

Always-on regardless of cluster: `filing_timeliness`, `mw_lifecycle`, `auditor_change_tracker`, `going_concern_detector`, `lender_concession`, `form4`, `insider_buy_timing`, `insider_vs_calendar`, `revenue_concentration`, `acq_coherence`, `iborrow`, `counterparty_reciprocity`, `claim_evolution`, `edgar_fts`, `megacap_namecheck`.

## Top 5 gap m-sources by inferred coverage × catastrophe-signal strength

(See GAPS.md for full prioritization.)

1. **`working_capital_drift.py`** — DSI/DSO/DPO inflection detector, universal across all goods clusters (~400 names)
2. **`tenant_credit_watch.py`** — REIT named-tenant 10-K/8-K monitor (Steward-style catches) (~56 REITs)
3. **`pacer_class_action.py`** — federal class-action docket (wage-hour, securities, product liability) (universal ~600)
4. **`consumer_traffic_proxy.py`** — Placer.ai-style foot-traffic + Google Trends + app rank (~50 retail/restaurant)
5. **`cms_cost_reports.py`** — Medicare HCRIS for SNF, hospital, home-health, healthcare REIT tenants (~15 direct + IIPR/CTRE/MPW indirect)
