# CA Charter School Muni — Sector Scoping

**Prepared**: 2026-05-28
**Status**: Scoping pass — preparation for detector-library build session
**Framework**: Union-of-narrow-detectors exclusion screen (validated on CA NH + CCRC + Hospital muni)
**Owner**: muni_credit vertical

---

## Executive Summary (~300 words)

**Universe size + market size.** CA charter operators with confirmed publicly-traded conduit muni debt number ~30 active obligors plus 4-5 historical-distress reference names (Today's Fresh Start, Celerity, Aveson, Inspire). Estimated aggregate outstanding par across the active universe is **$1.5-2.5B** — most issued through CSFA (~70% by par), with CSCDA, CMFA, and CalPFA covering the remainder. This is a small-issue, dispersed market: median outstanding obligor par is ~$30-45M; only Aspire/Alliance/Green Dot CA exceed $80M. Schedule K disclosures and CSFA's obligor-level fact books are the canonical sources.

**Testable detectors.** Of the 9 proposed detectors, **6 are computable from public data** (enrollment_trajectory via CDE Dataquest; charter_renewal_status via CDE Charter Schools Division + authorizer board minutes; academic_performance_collapse via CAASPP; authorizer_relationship via board minutes + LAUSD CSD records; lcff_funding_cut via CDE LCFF data; financial_compliance_finding via FCMAT + State Controller). **3 are partially computable** (dscr_or_days_cash_collapse and going_concern require Form 990 / audited FS with 18-24 month lag; founder_or_ed_turnover requires manual obligor-website + LinkedIn tracking). Net: **6 first-class detectors + 3 second-class** = pilot library of 6 fire-and-forget plus 3 manual-augment.

**Hypothesized exclusion rate + TEY alpha.** With 6 narrow detectors each calibrated to fire on 5-12% of universe and union composition, expected **exclusion rate ~30-40%** (12-15 of 30 active obligors). Charter muni base-rate deterioration (downgrade or default-track) over a 24-month window is roughly **12-18%** sector-wide (higher than NH but pre-AB1505 was higher still). Expected honest exclusion alpha: **5-9 pp deterioration-rate compression** → **20-36 bps/yr raw alpha** → **~40-72 bps/yr TEY** at top-bracket CA (2.01× multiplier). Less than CA NH (~95-115 bps TEY) because charter deterioration outcomes are less ratings-clean and recoveries are higher.

**Top 3 EXCLUDE.** **(1) Today's Fresh Start** — 7-detector positive control, canonical distress profile, useful as backtest negative anchor. **(2) ICEF Public Schools** — 3 active detector fires (enrollment, school closures, LCFF compression). **(3) Aveson Charter Schools** — 4 active detector fires (renewal denial, enrollment collapse, authorizer conflict, LCFF compression) — verify bond structure first.

**Top 3 CLEAN.** **(1) Granada Hills Charter** — quintile-1 academics, growing enrollment, 10+ year ED tenure, LAUSD-protected renewal. **(2) Da Vinci Schools** — Wiseburn USD partnered relationship is uniquely supportive; founding CEO 20+ year tenure. **(3) Green Dot Public Schools California (Animo)** — stable enrollment, no active authorizer conflict, long-tenured CEO, BBB- IG-rated.

**Open data-gap questions for next session.** (a) Schedule K canonical-par refresh cadence (FY24 filings come mid-2026); (b) CSFA Charter School Facility Program intercept mechanism — does it function as a Cal-Mortgage analog?; (c) EIN verification for ~10 obligors; (d) PCSD facility-bond treatment (separate analytical bucket?); (e) CCSA-JPA pooled-financing decomposition.

---

## 1. Sector overview

### Market size and structure
- **Active CA charter operators with public muni debt**: ~30 obligors (this scoping pass).
- **Aggregate outstanding par estimate**: $1.5-2.5B. Dispersed across many small issues; median issue $20-40M.
- **Dominant conduit**: California School Finance Authority (CSFA) — purpose-built for charter conduits, ~60-70% of issuance volume. Secondary: CSCDA, CMFA, CalPFA.
- **Issue structure**: typically 25-30 year amortization, callable at 10 years, security is gross revenues + leasehold (facility) interest. Many deals also include intercept mechanism through CSFA / State Controller (see section 5).

### CA-specific structural context
- **AB 1505 (2019)** restricted authorizer discretion in renewal, eliminated direct-funded nonclassroom-based charters going to weak authorizers, and required CDE-approved oversight standards. Material regime shift that increased authorizer-rejection rates for low-performing charters and dispersed Inspire-style nonclassroom operators.
- **AB 130 (2021)** further constrained nonclassroom-based / independent-study charter funding eligibility.
- **LCFF model**: per-pupil funding plus supplemental/concentration grants for high-need students. Means enrollment decline = immediate revenue compression with little fixed-cost offset.
- **Charter renewal cycle**: 5-year cycles standard; high-performing operators get up to 7 years post-AB 1505. Renewal denial appeal goes to County BOE → State BOE → court.

### Default and distress history (last decade)
| Operator | Year | Outcome |
|---|---|---|
| Today's Fresh Start | 2014-2022 ongoing | Multiple LAUSD/LA-COE revocation actions; founder governance scandal |
| Celerity Educational Group | 2017-2020 | Federal indictment of founder; multiple charter revocations; CSFA Series 2011 bond complications |
| Inspire Charter Schools network | 2019-2022 | Lost most authorizers; largely closed; mostly not bond-financed though |
| Aveson School of Leaders | 2022-2023 | Pasadena USD non-renewal; LA COE appeal upheld denial |
| ICEF Public Schools | 2011 historical | $10M unpaid bills; founder departure; restructured (DIDN'T default on bonds but came close) |
| El Camino Real Charter HS | 2016-2018 | LAUSD revocation threat over governance/compensation; resolved (bonds remained current) |

**Net charter muni default rate (CA, 2014-2024 estimated)**: hard to pin precisely without EMMA scrape — public reporting suggests **1-3 confirmed default-track events on rated public conduit deals**, plus several covenant-distress events that didn't reach default. Charter-school muni default rate nationally is ~1-2%/yr cumulative; CA likely slightly lower post-AB-1505 cleanup.

---

## 2. Universe inventory (see `data/charter_universe.json` for full record)

**Active obligors with confirmed conduit issuance (n=31)**: Aspire, Alliance, KIPP SoCal, KIPP NorCal, Bright Star, Camino Nuevo, Da Vinci, Magnolia, Granada Hills, El Camino Real, Vaughn, ICEF, View Park, Equitas, Ednovate, Green Dot CA, PUC, New Designs, PCSD (facility entity), CCSA-JPA pool, Rocketship, Summit, Caliber, Lighthouse, High Tech High, Coastal-Classical, Stockton Collegiate, Method, Larchmont, Citizens of the World, Capitol Collegiate, Gateway.

**Historical-distress reference (n=5)**: Today's Fresh Start, Celerity, Inspire, Aveson, El Camino Real (governance crisis).

**Explicitly excluded with reason (n=5+)**: Wonderful College Prep (privately funded), Religious/private schools, school-district G.O. bonds, out-of-state CMO arms of CA-overlapping operators, PCSD facility-only bonds (flagged for separate analytical treatment).

**Confidence**: 12 obligors at HIGH/MEDIUM (verified series + par), 19 at LOW (name + issuer confirmed; series par UNVERIFIABLE pending Schedule K + EMMA manual search).

---

## 3. Proposed detector library

### 3.1 First-class detectors (computable from public data)

| Detector | Fire Threshold | Target Fire Rate | Est Precision | Primary Data Source | Status |
|---|---|---|---|---|---|
| **enrollment_trajectory** | 3-yr-avg YoY ≤ −3% OR 5-yr cum ≤ −12% | ~10% | ~75% | CDE Dataquest enrollment files (free, structured CSV per CDS code) | PROPOSED |
| **charter_renewal_status** | Active revocation OR non-renewal OR probation OR closure-in-window | ~5-8% | ~85% | CDE Charter Schools Division + authorizer board minutes (LAUSD CSD agenda, LA COE, etc.) | PROPOSED |
| **academic_performance_collapse** | CAASPP ELA+Math both bottom-quintile AND 3-yr trend ≤ −3pp | ~8% | ~70% | CAASPP results (caaspp-elpac.cde.ca.gov, public) | PROPOSED |
| **authorizer_relationship** | Active LAUSD/COE conflict event in trailing 24mo OR documented strict-renewal posture | ~10% | ~70% | LAUSD CSD board agenda search + LA Times / EdSource news search | PROPOSED |
| **lcff_funding_cut** | Enrollment-driven LCFF revenue decline ≥ −3%/yr sustained 2yr | ~10% | ~75% | CDE LCFF funding snapshot files | PROPOSED |
| **financial_compliance_finding** | FCMAT review in window OR material state-audit finding OR State Controller adverse | ~5% | ~85% | FCMAT website + State Controller audit reports (public) | PROPOSED |

**Composition**: union (any one detector firing → excluded). Expected combined exclusion rate ~30-40%.

### 3.2 Second-class detectors (data-lagged or manual)

| Detector | Why second-class | Workaround |
|---|---|---|
| **dscr_or_days_cash_collapse** | Form 990 + audited FS lag 18-24 months; not all charters file Schedule K with bond-detail | Use as confirmatory; pull when available; for many small obligors, will remain UNVERIFIABLE |
| **founder_or_ed_turnover** | Requires manual obligor-website + LinkedIn tracking | Use for top-15 obligors by par only |
| **going_concern_or_late_filing** | Same Form 990 lag; many charters file 990 late routinely | Apply only where 990 status verifiable; weaker signal than in NH where audit deadlines stricter |

### 3.3 Sector-specific detectors proposed (additions to base library)

| Detector | Rationale | Status |
|---|---|---|
| **single_authorizer_concentration** | LAUSD-only operators (Alliance, Granada Hills, El Camino Real, Bright Star, etc.) have policy-shift tail risk. Fires when single authorizer >90% AND that authorizer is in restrictive cycle. | PROPOSED — adjunct, not primary |
| **nonclassroom_based_designation** | NCB charters (Inspire-style) face higher regulatory risk post-AB 1505/130. Fires if NCB > 30% of operator enrollment. | PROPOSED |
| **pooled_financing_participant** | CCSA-JPA pool participants can have single-obligor distress masked by pool. Fires if obligor is in pool AND any other pool participant has distress event. | PROPOSED — needs pool composition data |

### 3.4 Detectors NOT proposed (and why)

- **Composite credit score / comprehensive risk index** — directly forbidden by framework (covenant_tripwire +18 pp in-sample → −33 pp blind precedent). Union of narrow detectors only.
- **Rating-action-omission** — rejected in prior verticals (60% fire rate, no precision).
- **Capital ratios / leverage thresholds in isolation** — too noisy; CHARTER capital structure varies materially by facility ownership model. Use only in combination with DSCR.

---

## 4. Initial alpha hypothesis

### Expected economics

| Metric | Estimate | Source |
|---|---|---|
| Active universe size | ~30 obligors | This scoping doc |
| Excluded basket size | ~10-13 (32-43%) | Union composition with 6 detectors @ 5-12% fire each |
| Base-rate deterioration (24mo) | ~12-18% | Charter muni national rates + CA AB 1505 effect |
| Excluded-basket deterioration | ~35-50% | Conditional on detector fires (post-renewal-denial + enrollment-collapse outcomes are stark) |
| Clean-basket deterioration | ~5-9% | Implied from above |
| Exclusion alpha (pp) | **+6-9 pp** | (full - clean) |
| Raw bps alpha | **~24-36 bps/yr** | 4 bps per pp framework rule |
| TEY at top-bracket CA | **~48-72 bps/yr** | 2.01× multiplier |

### Honest caveats
- **Alpha LIKELY 30-50% INFLATED in initial backtest** due to detector calibration on observed distress cases. Tier-1 controls (det-screen ablation, placebo, blinding-leak audit) required before claiming alpha as real.
- **Recovery rates are higher in charter muni than in corporate**: even on renewal-denial, often the operator continues at successor authorizer with bondholder workout. Default ≠ zero recovery. Adjust alpha for expected recovery (~60-75% on charter muni distress).
- **Sector size constrains capacity**: $1.5-2.5B aggregate par means even a 20-name clean basket is a $200-400M deployable market. Position sizing for SMAs / smaller funds works; not Parametric scale.

---

## 5. Pricing dynamics + credit enhancement

### Typical spread vs MMD AAA
- **Investment-grade BBB rated charter (Aspire, Alliance, KIPP, Green Dot CA)**: +150-225 bps over MMD AAA at 25-year maturity. Recent (2024-2025) range tighter than 2018-2020 driven by IG demand.
- **Unrated / BB-range single-CMO (smaller operators)**: +275-450 bps. Wide and inefficient.
- **CSFA pooled / school-district-supported deals**: +90-180 bps depending on intercept strength.

### Credit enhancement: the Cal-Mortgage analog question

**KEY QUESTION FOR NEXT SESSION**: Is there a charter-school muni credit enhancement that masks operator credit the way Cal-Mortgage did for NH?

Candidates to investigate:
- **CSFA Charter School Facility Program (CSFP) intercept**: For CSFP-supported deals, the CA State Controller intercepts LCFF apportionments before they reach the charter and routes to the bond trustee. This creates a strong but NOT absolute credit support — it eliminates voluntary-default risk but does NOT prevent charter closure / revocation (in which case there are no LCFF apportionments to intercept). So intercept is **partial enhancement**, not equivalent to Cal-Mortgage.
- **California Statewide Charter School Facility Direct Funding** — proposed but not enacted as of 2026; not a real enhancement.
- **Insurance**: BAM, AGM occasionally wrap charter bonds; not sector-wide and not dominant.

**Hypothesis (to test)**: The CSFA intercept gives a **2-3 notch uplift** but does NOT decouple operator credit from pricing the way Cal-Mortgage's full guarantee did for NH. Therefore, our detector framework should **fire effectively on operator credit signals** — no insurance-masking dynamic to defeat.

**To verify next session**: pull 3-5 CSFA intercept-backed deals + 3-5 non-intercept charter deals, compare spread vs operator metrics (enrollment, CAASPP). If spreads correlate with operator metrics in both groups → intercept is partial enhancement, framework signal works. If spreads correlate ONLY for non-intercept → intercept masks like Cal-Mortgage did, framework needs adjustment.

---

## 6. Initial qualitative reads

### CLEAN candidates (top 3 + 2)

1. **Granada Hills Charter** — quintile-1 academics (75% CAASPP ELA met/exceeded; 96% A-G completion), growing enrollment (+1.3%/yr), 10+ year ED tenure, LAUSD has consistently renewed. Single-site complex with strong waitlist. *Sources*: CDE Dataquest, CAASPP, LAUSD CSD board records.
2. **Da Vinci Schools** — Wiseburn USD partnered relationship is uniquely stable (co-located facility, shared bond support), founding CEO 20+ year tenure, growing enrollment, 92% A-G. *Sources*: Wiseburn USD board records, Da Vinci website, CDE Dataquest.
3. **Green Dot Public Schools California (Animo)** — stable enrollment trajectory, no active authorizer conflict, long-tenured CEO (Cristina de Jesus), BBB- IG-rated historically. *Sources*: CDE Dataquest, BondBuyer 2019 refunding coverage.
4. *(adjunct)* **Aspire Public Schools** — largest CA operator, multi-authorizer footprint reduces single-authorizer tail risk, stable enrollment, no detector fires. Largest deployable position by par.
5. *(adjunct)* **KIPP SoCal Public Schools** — diversified authorizer footprint (LAUSD, LACOE, SDCOE), stable enrollment post-merger, IG-rated. Recent CEO transition (2024) is a single-event watch but not a fire.

### EXCLUDE candidates (top 3 + 2)

1. **Today's Fresh Start** — 7-detector positive control: extreme enrollment decline, multi-revocation history, bottom-quintile academics, sustained authorizer conflict, financial mismanagement findings. *Sources*: CDE Dataquest, LAUSD board minutes, LA County BOE records, LA Times reporting 2014-2022. **Use as backtest negative anchor.**
2. **ICEF Public Schools** — 3 active detector fires: sustained enrollment decline (-15% over 5 years), school closure in window (View Park Prep Middle 2023), LCFF revenue compression. Plus historical 2011 near-collapse. *Sources*: CDE Dataquest, LAUSD CSD board minutes 2022-2024.
3. **Aveson Charter Schools** — 4 detector fires: Pasadena USD non-renewal 2022, severe enrollment decline (-39% 5-yr), school closure, LCFF compression. **VERIFY bond structure first** — if PCSD-leased not direct-obligor, exclude from operator universe but use as stress-history reference. *Sources*: Pasadena USD board minutes 2022, LA COE appeal record 2023.
4. *(adjunct watch)* **El Camino Real Charter HS** — clean current state but historical authorizer conflict (2016-2018 revocation threat resolved), single-authorizer 100% concentration, renewal cycle active 2025. Ideal candidate for detector calibration (history-of-conflict vs active-conflict threshold).
5. *(adjunct watch)* **Magnolia Public Schools** — Gulen-affiliation reputational risk; 2014 LAUSD denial of Magnolia 7 renewal (court overturned). Investigate current renewal status across the 10 schools.

---

## 7. Open data-gap questions (for next session)

1. **Schedule K canonical-par sources** — FY24 990 Schedule Ks become available mid-2026. What quarterly refresh cadence works? Are there CSFA conduit fact-book updates that provide a faster signal?
2. **CSFA intercept mechanism** — does it function as a Cal-Mortgage analog and mask operator credit? See section 5 hypothesis to test.
3. **EIN verification** — ~10 of 30 obligors have UNVERIFIABLE or placeholder EINs in `charter_universe.json`. ProPublica + IRS BMF cross-check required.
4. **PCSD facility-bond treatment** — Pacific Charter School Development issues facility-only bonds backed by operator lease payments. Separate analytical bucket needed?
5. **CCSA-JPA pooled-financing decomposition** — pool participants and per-participant outstanding par needed.
6. **EMMA manual search budget** — to verify series-level par for the ~20 LOW-confidence obligors, ~5-8 hours of EMMA manual lookups required. Worth the budget?
7. **AB 1505 era cutoff for backtest** — pre-2019 vs post-2019 may behave structurally differently; backtest window should be 2020-2025 (5 years post-reform).
8. **Recovery-rate adjustment** — charter muni recoveries on distress are higher than corporate (60-75% est). Need to adjust raw exclusion alpha for recovery to get honest expected-loss alpha.
9. **Concurrent enrollment / district-of-residence rules** — some charters serve students from multiple districts; LCFF revenue can be more stable than enrollment count suggests. Refine LCFF detector calibration.
10. **Nonprofit governance signals** — Board turnover, IRS Form 990 Section VII compensation flags, Schedule O narrative material weakness disclosures — are these worth a manual-augment second-class detector?

---

## 8. Honest scope caveat (re-emphasized)

This scoping pass deliberately listed **6 first-class detectors** rather than reaching for 10. Per prior framework lessons:

- **Don't over-promise on detector coverage**. Half-built detectors with UNVERIFIABLE data produce noise, not signal.
- **Honest union arithmetic**: 6 narrow detectors at 5-12% fire each compose to a 30-40% exclusion rate. That's structurally tight but realistic.
- **Calibrate against known outcomes first** (Today's Fresh Start, Aveson, ICEF, Celerity) BEFORE running blind universe screen.
- **Recovery-rate adjustment is non-negotiable** for the honest TEY alpha. Charter distress is rarely zero-recovery; the framework must reflect that.

The framework's failure mode in prior verticals was over-promising on detector coverage. This pass intentionally underclaims to leave room for clean validation.

---

## 9. Suggested next-session build order

1. Verify EINs + outstanding par for top-15 obligors via Schedule K (ProPublica)
2. Build `detectors/charter_enrollment_trajectory.py` against CDE Dataquest CSV
3. Build `detectors/charter_renewal_status.py` — manual data file (event log) since no API
4. Build `detectors/charter_caaspp_collapse.py` against CAASPP data
5. Build `detectors/charter_lcff_funding_cut.py` against CDE LCFF files
6. Build `detectors/charter_authorizer_conflict.py` — manual event log
7. Build `detectors/charter_financial_compliance.py` — FCMAT + State Controller scan
8. Compose into union, run against the ~30-obligor active universe + 5 historical reference names
9. Calibrate against known outcomes (Today's Fresh Start = 7-fire, Aveson = 4-fire, ICEF = 3-fire)
10. Run blind OOS slice (2020-2023 cutoff → 2024-2026 outcomes) before reporting alpha
11. Adjust for recovery rates → honest TEY alpha
12. Tier-1 controls (ablation, placebo, blinding-leak audit) before claiming alpha

---

## Appendix A: Files produced in this scoping pass

- `outputs/CHARTER_SECTOR_SCOPING.md` — this document
- `data/charter_universe.json` — 31 active + 4 historical reference obligors
- `data/charter_initial_detector_data/aspire_public_schools.json` — CLEAN demonstration
- `data/charter_initial_detector_data/alliance_college_ready.json` — adjunct CLEAN (single-authorizer watch)
- `data/charter_initial_detector_data/kipp_socal.json` — CLEAN demonstration
- `data/charter_initial_detector_data/granada_hills_charter.json` — top-3 CLEAN
- `data/charter_initial_detector_data/da_vinci_schools.json` — top-3 CLEAN
- `data/charter_initial_detector_data/green_dot_california.json` — top-3 CLEAN
- `data/charter_initial_detector_data/el_camino_real_charter.json` — WATCH name (calibration test)
- `data/charter_initial_detector_data/icef_public_schools.json` — top-3 EXCLUDE (3 fires)
- `data/charter_initial_detector_data/aveson_charter_schools.json` — top-3 EXCLUDE (4 fires)
- `data/charter_initial_detector_data/todays_fresh_start.json` — top-3 EXCLUDE (7 fires, positive control)

## Appendix B: Data sources (URLs)

| Source | URL | Purpose |
|---|---|---|
| CDE Dataquest | https://dq.cde.ca.gov | Enrollment, demographics |
| CAASPP results | https://caaspp-elpac.cde.ca.gov | Academic performance |
| CDE Charter Schools Division | https://www.cde.ca.gov/sp/ch/ | Renewal/revocation status, authorizer |
| CDE LCFF data | https://www.cde.ca.gov/fg/aa/pa/ | Per-pupil revenue, supplemental grant |
| FCMAT | https://www.fcmat.org | Fiscal review reports |
| State Controller | https://www.sco.ca.gov | Audit findings |
| ProPublica Nonprofit Explorer | https://projects.propublica.org/nonprofits/ | Form 990, Schedule K |
| CSFA | https://www.csfa.ca.gov | Conduit issuance records, intercept program |
| CMFA | https://www.cmfa-ca.com | TEFRA notices |
| CSCDA | https://cscda.org | TEFRA notices |
| LAUSD CSD | https://achieve.lausd.net/csd | Authorizer board agenda |
| EdSource | https://edsource.org | News coverage |
| LA Times Education | https://www.latimes.com/california/education | News coverage |
| EMMA (manual only) | https://emma.msrb.org | Obligor lookup |
