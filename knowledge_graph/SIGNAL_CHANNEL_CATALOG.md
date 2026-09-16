# Signal OS — Cross-Vertical Signal Channel Catalog

**Compiled**: 2026-05-28
**Source**: Synthesis pass extracting documented data feeds from `verticals/muni_credit/{detectors,outputs}`, `verticals/buyside_dd/{connectors,source_atlas.py}`, `verticals/public_co/m_sources`, and `~/.claude/projects/-Users-ajay-exalted-signalos/memory/*.md`.
**Companion**: `verticals/muni_credit/data/_meta/signal_channels.json` (structured JSON form).

## Purpose

Structured catalog of public/near-public data feeds that carry credit / risk / operating signals across the Signal OS vertical universe. Used to (1) reason about signal-to-price latency, (2) discover redundancy clusters (multiple channels carrying the same information at different lags), (3) drive the masking-mechanism + microstructure-knowledge layer per `feedback_signalos_true_goal_microstructure_knowledge.md`.

Per the microstructure-knowledge memory: this catalog IS a primary deliverable of the framework — even where alpha tests fail, mapping channel topology + cadence + market-watching depth is the encoded knowledge.

## Headline counts

- **73 channels** catalogued
- By cadence: 21 real-time, 11 monthly, 4 quarterly, 3 semi-annual, 16 annual-mandatory, 13 event-driven, 4 irregular, 1 UNVERIFIABLE
- By market-watching depth: 10 WATCHED_BROADLY, 36 WATCHED_BY_SOPHISTICATED, 27 WATCHED_BY_FEW, 0 NOT_WATCHED
- **7 redundancy clusters** identified (channels carrying the same underlying signal at different lags)
- **1 under-documented channel** flagged: `ca_hcai_cal_mortgage_monthly` — the dominant NH/CCRC masking-mechanism source but read by no current detector.

---

## Table (sorted by cadence, real-time → annual)

### Real-time / sub-weekly

| Channel | Asset classes | Lag (days) | Market-watching depth |
|---|---|---|---|
| `county_recorder_nod_cc2924` | ca_cfd_muni / ca_real_estate / buyside_dd_real_estate | ~1 | WATCHED_BY_FEW |
| `sec_edgar_submissions` (filings) | public_co_equity / muni_credit | ~60 (10-K) | WATCHED_BROADLY |
| `sec_edgar_fulltext_search` | public_co_equity / public_co_credit | ~1 | WATCHED_BY_SOPHISTICATED |
| `sec_form_4` | public_co_equity | ~2 | WATCHED_BROADLY |
| `sec_form_d` | buyside_dd_sponsor / pre-IPO | ~15 | WATCHED_BY_SOPHISTICATED |
| `uspto_odp_patents` | public_co / DD | ~540 to publication | WATCHED_BY_SOPHISTICATED |
| `clinicaltrials_gov_v2` | public_co_biotech / pharma | ~21 | WATCHED_BY_SOPHISTICATED |
| `nhtsa_vpic` | public_co_ev / auto | ~30 | WATCHED_BY_FEW |
| `fmcsa_safer` | public_co_logistics / trucking | ~30 | WATCHED_BY_FEW |
| `nasa_ntrs` | public_co_defense / space | ~90 | WATCHED_BY_FEW |
| `sam_entity` | public_co_govt_services | ~30 | WATCHED_BY_SOPHISTICATED |
| `finra_brokercheck` | public_co_finserv / DD | ~14 | WATCHED_BY_SOPHISTICATED |
| `iborrowdesk_ibkr` | public_co_equity | ~1 | WATCHED_BROADLY |
| `austin_permits` | DD real-estate | ~1 | WATCHED_BY_FEW |
| `abq_permits` | DD real-estate | ~7 | WATCHED_BY_FEW |
| `bozeman_permits` | DD real-estate | ~7 | WATCHED_BY_FEW |
| `wprdc_allegheny` | DD real-estate | ~14 | WATCHED_BY_FEW |
| `acris_nyc` | DD real-estate | ~5 | WATCHED_BY_SOPHISTICATED |
| `tx_comptroller_corp` | DD entity | ~30 | WATCHED_BY_FEW |
| `state_corp_registries` (50-state) | DD entity / CFD developers | ~7 | WATCHED_BY_SOPHISTICATED |
| `pacer_bankruptcy` | DD / muni / public_co | ~1 | WATCHED_BY_SOPHISTICATED |
| `courtlistener_pacer` | DD / muni / public_co | ~1 | WATCHED_BY_SOPHISTICATED |
| `emma_rtrs_trades` | muni_credit | ~1 (15-min RTRS) | WATCHED_BROADLY |
| `edsource_la_times_charter_coverage` | ca_charter_muni | ~1 | WATCHED_BY_FEW |
| `web_discovery_search` (Brave/DDG) | DD / public_co | ~7 | WATCHED_BROADLY |

### Monthly

| Channel | Asset classes | Lag (days) | Market-watching depth |
|---|---|---|---|
| `cms_nh_care_compare_stars` | ca/us nh_muni | ~30 | WATCHED_BY_SOPHISTICATED |
| `cms_nh_special_focus_facility` | ca/us nh_muni | ~30 | WATCHED_BY_SOPHISTICATED |
| `cms_nh_civil_monetary_penalty` | ca/us nh_muni | ~60 | WATCHED_BY_SOPHISTICATED |
| `ca_hcai_cal_mortgage_monthly` | ca nh / ccrc / hospital muni | ~30 | WATCHED_BY_FEW |
| `epa_frs` | public_co_industrial / DD | ~30 | WATCHED_BY_SOPHISTICATED |
| `epa_envirofacts_state_deq` | DD real-estate | ~60 | WATCHED_BY_SOPHISTICATED |
| `usaspending_gov` | public_co_defense / govt_services | ~30 | WATCHED_BY_SOPHISTICATED |
| `openfda` | public_co_pharma / biotech / devices | ~30 | WATCHED_BY_SOPHISTICATED |
| `fda_orange_book` | public_co_pharma | ~14 | WATCHED_BY_SOPHISTICATED |
| `bts_airline_metrics` | public_co_airlines | ~45 | WATCHED_BY_SOPHISTICATED |
| `nrel_alt_fuel_stations` | public_co_hydrogen / EV-charging | ~30 | WATCHED_BY_FEW |

### Quarterly

| Channel | Asset classes | Lag (days) | Market-watching depth |
|---|---|---|---|
| `ca_hcai_seismic_list` | ca_hospital_muni | ~60 | WATCHED_BY_SOPHISTICATED |
| `fdic_call_reports` | public_co_fintech / banks | ~45 | WATCHED_BROADLY |
| `dol_h1b_lca` | public_co_tech / biotech / semi | ~45 | WATCHED_BY_FEW |
| `bls_qcew` | public_co / DD market | ~180 | WATCHED_BY_FEW |

### Semi-annual

| Channel | Asset classes | Lag (days) | Market-watching depth |
|---|---|---|---|
| `emma_continuing_disclosure_53359_5` | ca_cfd_muni | ~45 | WATCHED_BY_SOPHISTICATED |
| `ca_successor_rda_rops` | ca_rda_successor_muni | ~60 | WATCHED_BY_FEW |
| `fcc_form_477` | public_co_telecom | ~180 | WATCHED_BY_FEW |

### Annual (mandatory)

| Channel | Asset classes | Lag (days) | Market-watching depth |
|---|---|---|---|
| `cdiac_yfsr` | ca_cfd_muni | ~150 | WATCHED_BY_SOPHISTICATED |
| `county_tax_default_list` | ca_cfd_muni / real_estate | ~215 | WATCHED_BY_FEW |
| `cms_hospital_hrrp` | us_hospital_muni | ~60 | WATCHED_BY_SOPHISTICATED |
| `cms_cost_reports_hcris` | hospital / nh / public_co_healthcare | ~270 | WATCHED_BY_SOPHISTICATED |
| `ca_cde_dataquest` | ca_charter_muni | ~270 | WATCHED_BY_FEW |
| `ca_caaspp_results` | ca_charter_muni | ~240 | WATCHED_BY_FEW |
| `ca_cde_lcff_funding_data` | ca_charter_muni | ~180 | WATCHED_BY_FEW |
| `osha_establishments_form_300A` | public_co_industrial / DD | ~60 | WATCHED_BY_FEW |
| `pentagon_jbook_program_funding` | public_co_defense | ~60 | WATCHED_BY_SOPHISTICATED |
| `cybercom_budget` | public_co_cyber | ~60 | WATCHED_BY_FEW |
| `doe_budget_cbj` | public_co_quantum / clean_energy | ~30 | WATCHED_BY_SOPHISTICATED |
| `irs_form_990_schedule_k` | nonprofit muni | ~540 | WATCHED_BY_SOPHISTICATED |
| `propublica_nonprofit_explorer` | nonprofit muni | ~570 | WATCHED_BY_SOPHISTICATED |
| `form_5500_pension` | hospital / pension / industrial | ~365 | WATCHED_BY_SOPHISTICATED |
| `census_acs_b25031` | DD real-estate / market | ~730 (5-yr est) | WATCHED_BROADLY |
| `hud_fmr` | DD real-estate | ~90 | WATCHED_BY_SOPHISTICATED |

### Event-driven

| Channel | Asset classes | Lag (days) | Market-watching depth |
|---|---|---|---|
| `cdiac_default_and_draw_db` | ca_cfd_muni | ~10 | WATCHED_BY_SOPHISTICATED |
| `emma_material_events` | muni (all classes) | ~10 | WATCHED_BY_SOPHISTICATED |
| `govt_code_53356_1_court_foreclosure` | ca_cfd_muni | 0 | WATCHED_BY_SOPHISTICATED |
| `ca_cde_charter_schools_division` | ca_charter_muni | ~30 | WATCHED_BY_FEW |
| `hhs_oig_cia_list` | hospital / healthcare | ~14 | WATCHED_BY_SOPHISTICATED |
| `doj_fca_settlements` | hospital / healthcare | ~1 | WATCHED_BY_SOPHISTICATED |
| `moody_s_p_fitch_rating_actions` | muni / public_co_credit | ~1 | WATCHED_BROADLY |
| `export_control_csl` | semi / industrial / aerospace | ~1 | WATCHED_BROADLY |
| `ca_muni_conduit_tefra_os` | ca muni (all sectors) | ~30 | WATCHED_BY_SOPHISTICATED |

### Irregular / UNVERIFIABLE

| Channel | Asset classes | Notes |
|---|---|---|
| `ca_fcmat_reports` | ca_charter / school_district | Reviews initiated on demand |
| `ca_state_controller_audits` | ca local govt / charter | Adverse findings ~6mo post-fieldwork |
| `fema_nfhl` | DD real-estate | Maps re-issued years apart |
| `ic_contracting_proxy` | public_co_govt_services | Derived, not raw — cadence depends on inputs |
| `nrc_state_industrial_permits` | public_co_industrial | UNVERIFIABLE — placeholder, not catalogued in m_sources |

---

## Redundancy clusters

Per the microstructure-knowledge framework, **the more public channels that carry the same signal, the harder it is to extract timing alpha** — by the time the slowest channel publishes, the dealer market has already repriced based on the fastest. Each cluster below is a documented redundancy structure.

### Cluster 1 — CA CFD distress signaling (5+ channels)

**The microstructure finding that falsified the land-secured timing-alpha hypothesis.** From `CFD_TIMING_ALPHA_TEST.md` + `CFD_UPSTREAM_DATA_TEST.md`: the same special-tax delinquency event is carried by 5+ public channels at varying lags.

| Channel | Cadence | Lag from event |
|---|---|---|
| `govt_code_53356_1_court_foreclosure` | event-driven | 0 days |
| `cdiac_default_and_draw_db` | event-driven | ~10 days |
| `emma_material_events` | event-driven | ~10 days |
| `emma_continuing_disclosure_53359_5` | semi-annual | ~30-60 days |
| `cdiac_yfsr` | annual-mandatory | ~150 days |
| `county_tax_default_list` | annual-mandatory | ~215 days |

**Implication**: 3 of 3 priority CFDs tested (Diablo Grande, Northstar, Palmdale 93-1) showed price-led-signal or co-incident behavior. Market repriced Diablo Grande to 65c before first detector fired (CDIAC YFSR + Default & Draw filings). Framework's contribution on these names = classification + diligence-replication, not entry-timing alpha.

### Cluster 2 — CA NH operator quality (3 CMS channels)

3 CMS channels triangulate NH operator quality with high correlation; the union (per detector-composition discipline) caught 2/2 deteriorating obligors with 100% precision in 2023-2025.

- `cms_nh_care_compare_stars` (monthly)
- `cms_nh_special_focus_facility` (monthly)
- `cms_nh_civil_monetary_penalty` (monthly)

**Implication**: Effective for classification but **MASKED** by Cal-Mortgage insurance wrap (bondholders price insurer credit, not operator) for ~half of the CA NH universe. Framework value here = hedge against insurer-cascade tail risk, not steady alpha. See `CA_NH_INVESTMENT_THESIS.md`.

### Cluster 3 — Healthcare fraud + enforcement (3 federal channels)

- `doj_fca_settlements` (event-driven, ~1d)
- `hhs_oig_cia_list` (event-driven, ~14d)
- `cms_hospital_hrrp` (annual)

CIA = 5-year structural overhead burden. HRRP fires only at max (3.00%) per detector-composition discipline.

### Cluster 4 — DoD revenue forward + rear-view triangulation

- `usaspending_gov` — rear-view obligations (monthly)
- `pentagon_jbook_program_funding` — forward funding (annual)
- `earmark_detector` — political fragility overlay (annual via J-Book)
- `sec_form_4` (insider_vs_calendar overlay) — temporal proximity to budget events
- `ic_contracting_proxy` — classified-revenue plausibility envelope

Canonical YSS/IONQ short-thesis vector: forward-funding zero + insider sale within window of budget action. Each channel insufficient alone; composition produces catastrophe signal.

### Cluster 5 — Developer credit chain (DD + muni)

- `sec_edgar_submissions` — public-co developers
- `state_corp_registries` — entity status, formation
- `county_recorder_nod_cc2924` — lender NoDs / trustee sales
- `moody_s_p_fitch_rating_actions` — agency ratings
- `emma_continuing_disclosure_53359_5` — CFD top-taxpayer disclosures
- `pacer_bankruptcy` — Ch 11 / Ch 9 filings

Detectors `developer_bankruptcy`, `developer_corp_credit`, `nod_recorder_filing` compose this into a chain-of-distress signal for CFD master developers.

### Cluster 6 — Workplace / facility scope plausibility

- `osha_establishments_form_300A` — ≥20 employee establishments (annual)
- `dol_h1b_lca` — quarterly H-1B sponsorships at worksite
- `bls_qcew` — county-NAICS denominator (quarterly, 180d lag)
- `epa_frs` — permitted facilities (monthly)
- `epa_envirofacts_state_deq` — environmental status
- `fmcsa_safer` — fleet size

Adjudicates "we have N-person factory at X" claims for public-co + DD. OSHA primary for ≥20-employee; H-1B catches sub-20 (tech/drone/biotech/semi).

### Cluster 7 — Pharma / biotech regulatory + clinical

- `clinicaltrials_gov_v2` (real-time)
- `openfda` (monthly)
- `fda_orange_book` (monthly)
- `uspto_odp_patents`

Cell/gene cohort relies on clinicaltrials + openFDA; marketed-Rx LOE pattern uses Orange Book + USPTO.

---

## Under-documented channel (single flagged item)

**`ca_hcai_cal_mortgage_monthly`** — HCAI Cal-Mortgage Loan Insurance Division Monthly Activity Report

This is the *single most important MASKING mechanism source* for CA NH/CCRC muni. The Cal-Mortgage insurance wrap decouples operator credit from bond pricing for ~half of the CA NH/CCRC universe (Aldersly, Bethany Home, O'Connor Woods, The Redwoods, Carmel Valley Manor all wrap-dependent). The Monthly Activity Report is the only primary source for confirming insurance status + portfolio claim activity.

**Currently**: cited only in obligor-bond JSON notes (`ca_nh_clean_basket_bonds.json`, `ca_nh_exclude_basket_bonds.json`). NO detector reads this channel.

**Recommended**: build a dedicated `cal_mortgage_cascade_monitor` detector that watches monthly activity (claim events, portfolio reserve burn, new commitments) as an insurer-cascade tail-risk early warning. This is the cross-vertical analog of the framework's macro-hedge thesis from `CA_NH_INVESTMENT_THESIS.md` ("If Cal-Mortgage faces a claim cascade from multiple stressed CCRCs/NHs simultaneously, the insurer credit itself resets and ALL wrapped names widen").

---

## Per-channel detail

Full per-channel records (publisher, url_pattern, lag explanation, market-watching depth justification, redundant channels, access gating, detectors that read this, source artifacts, _notes) are in:

`/Users/ajay/exalted/signalos/verticals/muni_credit/data/_meta/signal_channels.json`

The JSON is the canonical / queryable form. This markdown is a navigational surface.

## Source artifacts (cross-cutting)

The following artifacts were the primary source material for this catalog:

- **Memories** at `/Users/ajay/.claude/projects/-Users-ajay-exalted-signalos/memory/`
  - `feedback_signalos_true_goal_microstructure_knowledge.md`
  - `feedback_honesty_alpha_framework.md`
  - `feedback_detector_composition.md`
  - `feedback_dd_two_modes.md`
  - `feedback_dd_entity_resolution.md`
  - `feedback_scraping_browser_fingerprint.md`
- **Scoping + validation** at `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/`
  - `LANDSECURED_SECTOR_SCOPING.md`
  - `CFD_UPSTREAM_DATA_TEST.md`
  - `CFD_TIMING_ALPHA_TEST.md`
  - `CFD_RECORDER_DATA_BUILD.md`
  - `CFD_DEVELOPER_CREDIT_BUILD.md`
  - `CHARTER_SECTOR_SCOPING.md`
  - `CA_NH_INVESTMENT_THESIS.md`
  - `LANDSECURED_VALIDATION_PASS.md`
- **Detector docstrings** at `/Users/ajay/exalted/signalos/verticals/muni_credit/detectors/*.py`
- **Public-co m-sources** at `/Users/ajay/exalted/signalos/verticals/public_co/m_sources/*.py`
- **DD source atlas + connectors** at `/Users/ajay/exalted/signalos/verticals/buyside_dd/{source_atlas.py, connectors/*.py}`

## Maintenance

- **Refresh trigger**: when a new detector / m-source / DD connector is added, append a channel record to the JSON.
- **Cadence verification**: detector docstrings cite cadence and lag where known; UNVERIFIABLE remains the honest annotation when cadence isn't documented.
- **Redundancy-cluster discovery**: when 2+ channels are observed to carry the same underlying signal, document the cluster (this is the microstructure knowledge being encoded).
