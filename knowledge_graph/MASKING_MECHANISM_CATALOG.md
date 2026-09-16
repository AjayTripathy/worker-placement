# Masking-Mechanism Catalog — Cross-Asset

**Built**: 2026-05-28
**Companion JSON**: `data/_meta/masking_mechanisms.json` (queryable structured catalog)
**Purpose**: Structured surface of every masking mechanism documented across Signal OS verticals to date. A "masking mechanism" is any structural feature that decouples a public signal from market-price reflection. The framework's value proposition depends on whether a sector has one.

---

## Summary

- **21 mechanisms catalogued**
- **8 categories used**: insurance_wrap (4), intercept_structure (4), statutory_carveout (4), implicit_guarantee (3), sovereign_guarantee (2), rating_agency_lag (2), donor_base_support (1), sponsor_support (1)
- **9 VERIFIED** (observed in primary-source data with measured price/spread impact)
- **5 DOCUMENTED** (described in scoping/validation with structural detail; price impact inferred)
- **7 MENTIONED_NOT_VALIDATED** (named but not yet sector-tested)
- **2 of the 9 VERIFIED entries are STRUCTURALLY-NEGATIVE** (Teeter Plan Mello-Roos carve-out; CFD redundant public-channel topology — expected masking confirmed ABSENT)

---

## Validation-status legend

| Status | Meaning |
|---|---|
| **VERIFIED** | Mechanism observed in primary-source data with measured spread/price impact |
| **DOCUMENTED** | Mechanism described in scoping/validation docs with structural detail; price impact inferred |
| **MENTIONED_NOT_VALIDATED** | Mechanism named but structural details / asset-class impact not yet tested |
| **STRUCTURALLY_NEGATIVE** | Expected masking mechanism confirmed ABSENT — itself a finding |

Severity scale: HIGH = decouples signal from price almost entirely; MEDIUM = 2-3 notch effect; LOW = mild delay; NONE = no masking after review (negative finding).

---

## Catalog table (sorted by category)

| # | Mechanism | Category | Asset class(es) | Severity | Signal-to-price impact | Status |
|---|---|---|---|---|---|---|
| 1 | Cal-Mortgage Loan Insurance Program | insurance_wrap | CA NH / CCRC / minor hospital | HIGH | STRONG masking → insured curve, AA- | VERIFIED |
| 2 | AGM bond insurance (Assured Guaranty Municipal) | insurance_wrap | US muni cross-sector | HIGH | STRONG masking on insured tranches | DOCUMENTED |
| 3 | BAM bond insurance (Build America Mutual) | insurance_wrap | US muni cross-sector, minor CA charter | HIGH | STRONG masking on insured tranches | MENTIONED_NOT_VALIDATED |
| 4 | Cal-Mortgage insurer-cascade tail risk | insurance_wrap | CA NH / CCRC | MEDIUM (latent) | Currently latent; +5.4 pp COVID-stress observed | DOCUMENTED |
| 5 | FHA Section 242 hospital mortgage insurance | sovereign_guarantee | US hospital muni | HIGH | FULL masking → US sovereign curve | MENTIONED_NOT_VALIDATED |
| 6 | GNMA pass-through insurance (housing muni) | sovereign_guarantee | US housing muni, Section 8 | HIGH | FULL masking on insured tranches | MENTIONED_NOT_VALIDATED |
| 7 | CSFA Charter LCFF intercept (Ed Code §17199.4) | intercept_structure | CA charter (CSFA-issued) | MEDIUM | PARTIAL masking — 2-3 notch uplift; 150-300 bps compression | VERIFIED |
| 8 | PCSD facility-credit pool | intercept_structure | CA charter facility bonds | HIGH (single-name) | MASKS single-charter signal at CUSIP level | DOCUMENTED |
| 9 | CCSA-JPA pooled financing | intercept_structure | CA charter pooled | MEDIUM | Single-name masked at pool level | MENTIONED_NOT_VALIDATED |
| 10 | Implicit state pension intercept | intercept_structure | US state pension obligation bonds | HIGH | STRONG masking → state-credit curve | MENTIONED_NOT_VALIDATED |
| 11 | GO bond taxing-authority masking | implicit_guarantee | US muni GO, school district GO | HIGH | STRONG masking except in tax-base erosion | MENTIONED_NOT_VALIDATED |
| 12 | Teeter Plan (Mello-Roos statutory carve-out) | statutory_carveout | CA Mello-Roos CFD, 1915 Act | NONE (negative finding) | STRUCTURALLY-NEGATIVE for Mello-Roos | VERIFIED (negative) |
| 13 | Reserve fund cushion (CFD) | statutory_carveout | CA Mello-Roos CFD, 1915 Act | MEDIUM | Delays bondholder default 1-3 years | VERIFIED |
| 14 | Charter private-placement opacity | statutory_carveout | CA charter (private-placement debt) | HIGH (alpha scope) | TOTAL masking — debt unanalyzable at bond level | VERIFIED |
| 15 | CFD redundant public-channel topology | statutory_carveout | CA Mello-Roos CFD | NONE (anti-masking) | STRUCTURALLY-NEGATIVE — signals reach market in real time | VERIFIED (negative) |
| 16 | Stale-distress pricing | rating_agency_lag | CFD, US muni broadly | LOW (mitigated) | FALSE POSITIVE re-detection; mitigated via `STALE_DISTRESS_YEARS=5` | VERIFIED |
| 17 | Hospital muni rating-agency response lag | rating_agency_lag | US hospital / CCRC muni | MEDIUM | 12-36 month signal lead vs rating action | DOCUMENTED |
| 18 | Obligated-group consolidation | implicit_guarantee | CA CCRC, US hospital | HIGH (single-site) | STRONG masking on single-site signals | VERIFIED |
| 19 | Faith-based / donor-base operator support | donor_base_support | US CCRC, Catholic hospital, NH | LOW | WEAK masking; dominated by other layers | MENTIONED_NOT_VALIDATED |
| 20 | Charter authorizer relationship | implicit_guarantee | CA charter | LOW | Modest support layer | DOCUMENTED |
| 21 | Solvent master-developer implicit support | sponsor_support | CA Mello-Roos CFD | MEDIUM | Sponsor solvency backstops pre-buildout CFD cash flow | VERIFIED |

---

## Detail entries

### 1. Cal-Mortgage Loan Insurance Program — VERIFIED, HIGH severity

**Category**: insurance_wrap
**Asset classes**: CA NH muni, CA CCRC muni, minor CA hospital muni

State of California acts as insurer of last resort via HCAI; insured bonds carry State of CA AA- credit. Validation: CA NH backtest showed Cal-Mortgage-insured names (Carmel Valley Manor, The Redwoods Mill Valley) traded IDENTICALLY to clean-basket names despite triggering 2-4 detector fires. Carmel Valley Manor at par (100.134, 3.00% YTM) despite SFF Candidate flag. **In-sample exclusion alpha ~115 bps TEY compressed to ~30-60 bps in current market because insurance wraps mask operator signal.**

Alpha modes that survive: (1) forward-looking insurer-cascade tail risk; (2) uninsured/subordinate tranches (LAJH Series 2019A at +230 bps); (3) long-term loss-of-insurance-access on refi.

Sources: `outputs/CA_NH_INVESTMENT_THESIS.md`, `data/ca_nh_clean_basket_bonds.json`, `data/ca_nh_exclude_basket_bonds.json`, `data/ca_ccrc_universe.json`.

---

### 2. Teeter Plan (Mello-Roos carve-out) — VERIFIED NEGATIVE finding, NONE severity for Mello-Roos

**Category**: statutory_carveout
**Asset classes**: CA Mello-Roos CFD, CA 1915 Act assessment bonds

**Originally hypothesized as the Cal-Mortgage analog for the CFD vertical. Validation pass found explicit statutory exclusion of Mello-Roos special taxes and 1915 Act assessments from Teeter participation in every county checked.** Placer County FAQ ID 665 is explicit: "Placer County 'Teeters' all secured ad valorem taxes as well as all direct charges (with the exception of 1915 Act Bond and Mello Roos charges)." LA County YFSR field shows `teeter_plan: false` for Palmdale 93-1. Stanislaus empirically confirmed (Diablo Grande defaults reach bondholders). Of 30-CFD sample reviewed, only ~2 (San Joaquin 2009-2, Fairfield 2007-1) showed Teeter-masking.

This is itself a framework-relevant finding — where you'd expect masking, there isn't any. Mello-Roos CFD signals propagate to bondholders unmasked.

Sources: `outputs/LANDSECURED_SECTOR_SCOPING.md`, `outputs/LANDSECURED_VALIDATION_PASS.md`, `detectors/delinquency_spike.py` (Teeter caveat in docstring).

---

### 3. CSFA Charter LCFF Intercept (Ed Code §17199.4) — VERIFIED, MEDIUM severity

**Category**: intercept_structure
**Asset classes**: CA charter (CSFA-issued)

State Controller diverts charter LCFF apportionment to bond trustee on deficiency. Real credit enhancement at payment-mechanism level, but NOT a state guarantee (LISC confirms CA is NOT in state-debt-service-guarantee tier — only CO/UT/TX/AZ/ID). CSFA 2024 pricing book: BBB CSFA charters at 91-110 bps over MMD; BB+ at 143 bps; unrated CSFA at 230-260 bps; vs pre-intercept charter muni at 275-450 bps. **~150-300 bps spread compression attributable to intercept**.

Importantly, spread STILL correlates with operator metrics within the intercept-protected pool — masking is partial, not Cal-Mortgage-strength.

Sources: `outputs/CHARTER_SECTOR_SCOPING.md`, `outputs/CHARTER_VALIDATION_PASS.md`, `data/charter_universe.json`.

---

### 4. Reserve fund cushion (CFD) — VERIFIED, MEDIUM severity

**Category**: statutory_carveout
**Asset classes**: CA Mello-Roos CFD, 1915 Act

Bond indenture reserve fund (typically 10% of par or max annual debt service) absorbs special-tax delinquency before bondholders see missed debt service. **Northstar CSD CFD 1 had 65-75% delinquency from FY 2019-20 onward but no bondholder default through 2026 because reserve absorbed three draws ($3.68M Sep 2020, $965K Mar 2021, etc.).** Reserve depletion event itself is EMMA-distributed via CDIAC Default & Draw filings.

The `reserve_fund_burndown` detector (proposed, currently 0% fire rate due to t-1 reserve data gaps) is the intended LEADING indicator. Northstar is currently the only CFD case where signal-to-price gap may still exist via this mechanism.

Sources: `outputs/CFD_TIMING_ALPHA_TEST.md`, `outputs/LANDSECURED_VALIDATION_PASS.md`, `detectors/reserve_fund_burndown.py`, `detectors/reserve_fund_drawn.py`.

---

### 5. CFD redundant public-channel topology — VERIFIED NEGATIVE finding, NONE severity (anti-masking)

**Category**: statutory_carveout
**Asset classes**: CA Mello-Roos CFD

CFD distress signals are carried by 3-4 redundant public channels: CDIAC YFSR (annual), CDIAC Default & Draw on Reserve (event-driven), Govt Code 53356.1 court foreclosures (event-driven), Govt Code 53359.5 continuing disclosure (semi-annual). The CFD timing test concluded: **the framework's CFD signal channel is market-efficient — public-channel topology is too redundant to extract timing alpha from CDIAC alone.** Diablo Grande price led signal by 6-12 months because dealer markups absorbed the multi-channel public information faster than annual CDIAC filings.

This is the structural reason CFD timing alpha was falsified. Cross-asset principle: where multiple public channels carry the same signal at different cadences, market-efficiency arbitrage forces synchrony.

Sources: `outputs/CFD_TIMING_ALPHA_TEST.md`, `outputs/CFD_UPSTREAM_DATA_TEST.md`.

---

### 6. Obligated-group consolidation — VERIFIED, HIGH severity (for single-site signals)

**Category**: implicit_guarantee
**Asset classes**: CA CCRC, US hospital muni

Most CA CCRC muni debt is concentrated in 4 obligated groups (HumanGood CA, Front Porch, Sequoia Living, Eskaton/ECS) controlling 25+ communities. Debt is cross-guaranteed jointly and severally; single-site distress is invisible to bondholders when group credit remains stable. **Mt SA Gardens unrated single-site has YTM ~7%; HumanGood CalOG Fitch A multi-site obligated group has YTM ~5%** — single-site = higher idiosyncratic credit risk priced in; obligated-group = diversified credit, less individual signal.

Framework's single-site CMS / occupancy / seismic detectors do NOT translate to bond-level signal for obligated-group names.

Sources: `data/ca_ccrc_universe.json`, `outputs/CA_NH_INVESTMENT_THESIS.md`.

---

### 7. PCSD Facility-Credit Pool — DOCUMENTED, HIGH severity (single-name scope)

**Category**: intercept_structure
**Asset classes**: CA charter facility bonds (PCSD)

Pacific Charter School Development owns facilities, leases them to charter operators, issues bonds backed by multi-charter lease cash flows. **Aveson FY24 financial deterioration (revenue -22% YoY, net assets -45%, net income flipped to -$1.85M loss) is real distress but invisible at the PCSD bond level** because PCSD has diversified lease payers.

Framework cannot extract investable signal at single-charter level for PCSD-leased operators. Universe.json tagging required to separate `direct_conduit_issuer` vs `pcsd_lease_pool` vs `pooled_jpa`.

Sources: `outputs/CHARTER_VALIDATION_PASS.md`, `data/charter_initial_detector_data/aveson_charter_schools.json`.

---

### 8. Charter private-placement opacity — VERIFIED, HIGH severity (alpha scope)

**Category**: statutory_carveout
**Asset classes**: CA charter (private-placement debt)

Private-placement debt has no SEC continuing-disclosure obligations, no EMMA material event filings, no observable trade data. **Today's Fresh Start has confirmed multi-revocation operator distress (LAUSD 2007, LACOE 2020 Inglewood, SBE 2020 renewal denial, charter closed 6/30/2015 + 6/30/2020), but no analyzable bond CUSIPs.** Framework hit is real; debt is unreachable.

Useful only as positive-control / training-set anchor. Framework needs `direct_conduit_issuer_public` vs `private_placement` tagging.

Sources: `outputs/CHARTER_VALIDATION_PASS.md`, `data/charter_initial_detector_data/todays_fresh_start.json`.

---

### 9. Solvent master-developer implicit support — VERIFIED, MEDIUM severity

**Category**: sponsor_support
**Asset classes**: CA Mello-Roos CFD (pre-buildout housing)

When pre-buildout CFD has >50% taxpayer concentration with solvent master developer, developer pays special tax across undeveloped parcels and backstops cash flow until buildout. **Irvine 2013-3 has 0.1% delinquency on $904M par with FivePoint master developer (B2/B+/BB- sub-IG but solvent). Beazer Nov 2025 S&P downgrade B+→B and Tri Pointe Feb 2026 CreditWatch Developing are the current sub-IG developer signals to watch.**

Detector composition: `top_taxpayer_concentration` should fire ONLY when concentration AND (delinquency >2% OR buildout stalled OR developer in distress). `developer_corp_credit.py` provides the developer-credit layer.

Sources: `outputs/CFD_DEVELOPER_CREDIT_BUILD.md`, `data/cfd_developer_credit.json`, `detectors/developer_corp_credit.py`, `detectors/top_taxpayer_concentration.py`.

---

### 10. Hospital muni rating-agency response lag — DOCUMENTED, MEDIUM severity

**Category**: rating_agency_lag
**Asset classes**: US hospital / CCRC / minor NH muni

Rating agencies update on multi-quarter to multi-year cycles. **HCAI seismic detector docstring specifies typically 12-36 months lead time vs rating action.** Framework signals (CMS Star, SFF, CMP, HCAI seismic non-compliance) appear in primary-source data 12-36 months before rating downgrades. Sophisticated dealer markup repricing may be faster; index-tracking flow is the slow-mover.

Sources: `detectors/hcai_seismic.py`, `feedback_signalos_true_goal_microstructure_knowledge.md`.

---

### 11. AGM bond insurance (Assured Guaranty Municipal) — DOCUMENTED, HIGH severity

**Category**: insurance_wrap

Same wrap-masking pattern as Cal-Mortgage but private-sector insurer (rated A1/AA). **Palomar Health $700M+ revenue bonds remained in workout via forbearance with AGM in Jan 2025 — AGM absorbed the credit deterioration signal rather than bondholders.** Same alpha modes apply: insurer-cascade tail risk, subordinate tranches, refi-time loss of insurance access.

Sources: `data/ca_per_obligor/palomar_health.json`, `data/ca_nh_exclude_basket_bonds.json`.

---

### 12. Cal-Mortgage insurer-cascade tail risk — DOCUMENTED, MEDIUM (latent) severity

**Category**: insurance_wrap

When multiple Cal-Mortgage-insured operators distress simultaneously, insurer reserves drawn → state appropriation pressured → potential insurer rating action → all wrapped names widen. **COVID-stress 2020-2022 backtest window saw +5.4 pp exclusion alpha vs in-sample +14.3 pp — partial cascade reduced wrap masking marginally.** HCAI Cal-Mortgage Monthly Activity Reports are the primary monitoring source.

Sources: `outputs/CA_NH_INVESTMENT_THESIS.md`, `data/ca_nh_exclude_basket_bonds.json`.

---

### 13. Stale-distress pricing — VERIFIED, LOW severity (mitigation implemented)

**Category**: rating_agency_lag (broader interpretation)
**Asset classes**: CFD, US muni broadly

**Palmdale 93-1 reports `current_delinquency_pct: 100%` in CDIAC continuously since 1996/97 — 27 years stale.** Detector would falsely classify as fresh distress; bonds traded at deep distress / workout values for 25+ years. Honesty-alpha violation. Mitigation: `_distress_origination_date` field + `STALE_DISTRESS_YEARS = 5` cutoff in `run_landsecured_union_screen.py`.

Sources: `outputs/LANDSECURED_VALIDATION_PASS.md`, `outputs/LANDSECURED_UNIVERSE_EXPANSION.md`, `outputs/CFD_TIMING_ALPHA_TEST.md`.

---

### 14. BAM bond insurance — MENTIONED_NOT_VALIDATED, HIGH severity

**Category**: insurance_wrap

Same wrap-masking pattern as AGM. BAM rated AA at S&P; occasionally wraps charter muni but not sector-dominant. Mentioned as alternate insurer hypothesis for LAJH 2020 series.

Sources: `data/ca_nh_exclude_basket_bonds.json`, `outputs/CHARTER_SECTOR_SCOPING.md`.

---

### 15. CCSA-JPA pooled financing — MENTIONED_NOT_VALIDATED, MEDIUM severity

**Category**: intercept_structure

Pool of charter operators jointly issuing through CCSA-JPA. Single-charter signal masked at CUSIP level; framework needs pool-decomposition data to test. Proposed as a sector-specific detector in charter scoping; not yet validated.

Sources: `outputs/CHARTER_SECTOR_SCOPING.md`, `data/charter_universe.json`.

---

### 16. FHA Section 242 hospital mortgage insurance — MENTIONED_NOT_VALIDATED, HIGH severity

**Category**: sovereign_guarantee
**Asset classes**: US hospital muni

Federal full-faith-and-credit guarantee on hospital mortgages under Section 242 of the National Housing Act. Bonds trade to GNMA-equivalent / U.S. agency curve, not hospital credit. Listed as the cross-vertical analog to Cal-Mortgage but not yet quantitatively tested in any vertical.

Sources: `feedback_signalos_true_goal_microstructure_knowledge.md`.

---

### 17. GNMA pass-through insurance — MENTIONED_NOT_VALIDATED, HIGH severity

**Category**: sovereign_guarantee
**Asset classes**: US housing muni state HFA, Section 8 assisted housing

State HFA bonds backed by GNMA MBS carry full federal credit. Section 8 HAP provides federal payment for assisted housing. The buyside_dd Section 8 housing case found 41% premium claims over FMR were structurally infeasible — sovereign guarantee creates both a credit floor AND a revenue ceiling (HAP caps at FMR).

Sources: `feedback_signalos_true_goal_microstructure_knowledge.md`, `verticals/buyside_dd/outputs/20260512_212228/DIVERGENCE_REPORT.md`.

---

### 18. Implicit state pension intercept — MENTIONED_NOT_VALIDATED, HIGH severity

**Category**: intercept_structure
**Asset classes**: US state pension obligation bonds (POBs)

State POBs trade to state-credit curve, not pension-fund curve. `pension_funded_ratio.py` detector signals operator-level distress but does NOT translate to POB spreads. UC Medical Center pooled-pension (UCRP) is a related obligated-group / state-pool example.

Sources: `feedback_signalos_true_goal_microstructure_knowledge.md`, `detectors/pension_funded_ratio.py`, `data/ca_per_obligor/uc_medical_centers.json`.

---

### 19. GO bond taxing-authority masking — MENTIONED_NOT_VALIDATED, HIGH severity

**Category**: implicit_guarantee
**Asset classes**: US muni GO bonds, school district GO

GO bonds backed by unlimited (or limited) taxing power; operating-budget signals don't translate to spreads except in catastrophic tax-base erosion. Elk Grove USD CFD 1 (V/L 463x because backed by entire district AV) is a CFD-adjacent example. Not yet sector-tested as a standalone vertical; likely dominant masking for the largest segment of US muni market.

Sources: `feedback_signalos_true_goal_microstructure_knowledge.md`, `outputs/LANDSECURED_SECTOR_SCOPING.md`.

---

### 20. Faith-based / donor-base operator support — MENTIONED_NOT_VALIDATED, LOW severity

**Category**: donor_base_support
**Asset classes**: US CCRC, Catholic hospital, faith-based NH

Implicit donor / community / diocese support that historically materializes in distress events. Bethany Home Society and Carmel Valley Manor (Catholic) are dominated by Cal-Mortgage wrap, not donor signal. CHS Buffalo / Long Island / NJ safety-net distress suggests donor base insufficient in high-Medicaid regions.

Sources: `data/ca_nh_clean_basket_bonds.json`, `data/detector_data_filing_payor.json`.

---

### 21. Charter authorizer relationship — DOCUMENTED, LOW severity

**Category**: implicit_guarantee
**Asset classes**: CA charter

Strong authorizer relationships (Da Vinci-Wiseburn USD, Granada Hills-LAUSD) are an implicit support layer. Authorizer-conflict detector fires only on ACTIVE conflicts. Functionally less material than LCFF intercept.

Sources: `outputs/CHARTER_SECTOR_SCOPING.md`, `outputs/CHARTER_VALIDATION_PASS.md`.

---

## Cross-asset clusters

### Insurance-wrap cluster

`cal_mortgage`, `agm_bond_insurance`, `bam_bond_insurance`, `fha_section_242`, `gnma_passthrough_insurance`

**Common pattern**: Bond credit decoupled from underlying obligor via insurer / sovereign guarantee. Signal-to-spread translation muted unless insurer itself stressed. Framework adds value via forward-flag for insurer cascade tail risk and identification of uninsured subordinate tranches. **All 5 should be probed for similar effects — Cal-Mortgage is the only one with primary-source verified spread compression measurements in the current dataset.**

### Intercept-structure cluster

`csfa_lcff_intercept`, `pcsd_facility_credit`, `ccsa_jpa_pool`, `state_pension_intercept`, `go_bond_taxing_authority`

**Common pattern**: Pre-distribution payment diversion or pooled cash-flow structure provides 2-3 notch credit uplift while leaving operator-level signal partially visible. Framework can fire on operator credit but spreads tighter than pure operator credit would justify.

### Statutory-carveout cluster

`teeter_carveout_mello_roos`, `reserve_fund_cushion`, `charter_private_placement_opacity`, `cfd_redundant_signal_channels`

**Common pattern**: Statutory or structural rules that change which signals matter (or whether any market signal exists at all). Includes BOTH masking-present (reserve cushion delays bondholder default) and masking-absent (Teeter excludes Mello-Roos; CFD signal channels are redundant) findings.

### Implicit-support cluster

`obligated_group_consolidation`, `donor_base_support`, `charter_authorizer_relationship`, `solvent_master_developer_implicit_support`

**Common pattern**: Non-contractual support layers (sponsor solvency, donor base, authorizer relationship, joint-and-several group debt) that absorb single-name distress until aggregate-level pressure mounts.

### Rating-lag cluster

`rating_agency_lag_muni`, `stale_distress_pricing`

**Common pattern**: Temporal masking — rating action lags primary-source events; or stale-default reporting creates false-positive fresh-distress signals.

---

## Open mechanisms to catalog next

- **USDA Rural Development hospital / housing insurance** (sovereign analog to FHA 242)
- **California GO bond AB 8 fiscal-shift mechanism** (specifically for school district credit)
- **Tobacco settlement revenue bonds** (master settlement agreement implicit federal-state structure)
- **Hospital Provider Fee / Medicaid supplemental payment programs** (federal+state hybrid revenue stream that masks payor-mix signals)
- **Catholic diocese / religious-order joint-and-several debt structures** (extension of obligated-group concept)
- **Texas Permanent School Fund Bond Guarantee Program** (analog to CSFA LCFF intercept but at K-12 GO level)

---

## Discipline notes

- Every entry cites at least one source artifact (path included). The user can trace any catalog claim back to where the finding originated.
- Where a mechanism was named but structural details / asset-class impact have not been tested, `documentation_depth: MENTIONED_NOT_VALIDATED` is set explicitly. No fabricated properties.
- Negative findings (Teeter NOT applying to Mello-Roos; CFD signal channels being redundant rather than masking) are captured as their own entries — the ABSENCE of expected masking is a structural finding worth cataloging.
- Cross-references link mechanisms in the same cluster so similar effects can be probed jointly (e.g., all 5 insurance-wrap mechanisms can be tested for spread-compression and forward-flag insurer-cascade alpha using the Cal-Mortgage methodology).
