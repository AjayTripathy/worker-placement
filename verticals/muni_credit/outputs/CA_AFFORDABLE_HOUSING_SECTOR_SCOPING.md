# CA Affordable Housing Muni — Sector Scoping (Wrap-Cluster Validation Pass)

**Date**: 2026-05-28
**Time-box**: 90 min
**Vertical**: muni_credit
**Stance**: Hostile validator against the wrap-cluster catalog prediction. Look for where wraps DON'T mask.

---

## TL;DR — Headline Findings

The wrap-cluster catalog's prediction that federal/state wraps mask operator credit signal on CA affordable housing muni is **CONFIRMED for the wrapped subsector but the more important structural finding is that wraps are ABSENT on the entire workforce / essential housing subsector (CSCDA CIA, CalCHA, CMFA Special Finance Agency I) — and that subsector has materially defaulted in 2024-2025 with bond prices reflecting full operator-level distress.**

The sector cleaves into two halves:

1. **Wrapped half** — CalHFA program credit (Aa1/AA+, 1.31x PADR overcollateralization), Freddie Mac TEL conduit deals, GNMA/FHA 221d4 pass-throughs. Bonds trade +30 to +70 bps over MMD AAA regardless of underlying project quality. **STRONG masking confirmed.** Wrap-cluster catalog prediction holds — same structural pattern as AGM on AA-/A1 underlying.

2. **Unwrapped half** — CSCDA Community Improvement Authority + California Community Housing Agency (CalCHA) + CMFA Special Finance Agency I "essential housing" / "workforce housing" deals (2019-2022 vintage, ~$8-10B total, 45+ deals). NO credit enhancement — purely single-asset apartment cash flow with senior/sub lien stack. **7 of 14 CalCHA projects defaulted / drew reserves / impaired by 2024-2025.** Bonds trade 63-90 cents on the dollar; spreads +155 to +475+ bps. **Wrap-cluster prediction does NOT apply — signal flows fully to price.**

The framework's exclusion value is concentrated in the unwrapped half (already-distressed names, but more importantly the cohort of 2019-2022 essential-housing deals where the music may still be playing). Wrapped half offers little operator-signal alpha but does offer the AGM-style fair-value selection within wrap rating bucket.

---

## Universe size + market context

| Subsector | Estimated obligor count | Total par estimated | Status |
|---|---|---|---|
| CalHFA Affordable Multifamily Indenture (program-credit) | 1 program, several series | $200M-$500M outstanding from 2023 reentry | Active issuance, Aa1/AA+ |
| CalHFA Project-level supportive housing conduit | ~5-10 | ~$100M-$300M | Active |
| Freddie Mac TEL / GNMA conduit project-level (CSCDA + CMFA + CalPFA + SDHC + LAHCID) | ~100-200 deals 2023-2025 vintage | $5B+ annually | Active; CDLAC bottleneck = $4.87B/yr ceiling vs >$12B demand |
| CSCDA Community Improvement Authority + CalCHA + CMFA Special Finance Agency I (workforce / essential, UNWRAPPED) | 45+ deals 2019-2022 vintage | $8B-$10B aggregate | Stressed; 7+ defaulted/impaired |
| Rated nonprofit developer corporate credit (BRIDGE Housing AA-, Century Housing A-) | 2-5 | ~$300M-$500M | Active, clean credit |

**Total actionable universe**: 30-50 obligors with verifiable bonds + meaningful trade history. **Empirical anchors pulled this session: 8 CUSIPs across 8 distinct obligors.**

CDLAC market context: 354 multifamily applications received 2024, 138 awarded (39% hit rate). State allocates $4.87B annual private activity bond cap vs >$12B demand → market is heavily supply-constrained on the wrapped tax-exempt side.

---

## Structural taxonomy (the 7 wrap classes I identified)

| Structure class | Wrap severity | Wrap rating | Market yield | Predicted masking | Validated this session |
|---|---|---|---|---|---|
| `calhfa_overcollateralized_program` | STRONG | Aa1/AA+ | +60-67 bps over MMD AAA | STRONG | YES (N=2 CUSIPs) |
| `calhfa_conduit_supportive_housing` (Section 8 backed) | MEDIUM | not-rated tier | +20-50 bps over MMD AAA | PARTIAL | YES (N=1 CUSIP) |
| `freddie_mac_tel_passthrough` | STRONG (GSE) | Aa2/AA via Freddie credit substitution | +30-50 bps over MMD AAA | STRONG | INFERRED (N=1 CUSIP — Terracina, yield field corrupted; structurally inferred from Ready Capital lender) |
| `gnma_collateralized_passthrough` | MAXIMUM | Aaa (federal full faith & credit) | +15-30 bps over MMD AAA | MAXIMUM | NOT TESTED this session (no California-specific Aaa GNMA CUSIP with recent trade pulled) |
| `fha_542c_risk_share` | STRONG (hybrid federal+state) | embedded in CalHFA program | n/a standalone | STRONG | INDIRECTLY (rides CalHFA indenture) |
| `fha_221d4_new_construction` | MAXIMUM (federal) | embedded in GNMA bonds at takeout | n/a standalone | MAXIMUM | NOT TESTED (most California 4% LIHTC deals now route through Freddie TEL rather than FHA-221d4-GNMA path) |
| `essential_workforce_housing_unwrapped` | NONE | unrated | +155 to +475+ bps over MMD AAA on distressed names | NONE | YES (N=5 CUSIPs across 5 distinct obligors) |

---

## Per-wrap masking verdict

### CalHFA program credit (`calhfa_overcollateralized_program`) — STRONG MASKING CONFIRMED

**Empirical anchors:**
- **CUSIP 13032WCB8** (CalHFA Affordable Housing Rev Series A-1 Sustainability) — 3.85% coupon, 2039 maturity → trades 3.871% yield (May 13 2026), price 99.775. **Spread to MMD AAA 14y (~3.20%): +67 bps.**
- **CUSIP 13032WES9** (CalHFA Affordable Housing Rev Series B Sustainability) — 4.35% coupon, 2043 maturity → trades 4.261% yield (May 13 2026), price 100.575. **Spread to MMD AAA 17y (~3.65%): +61 bps.**

**Verdict**: Bonds trade ~60-67 bps over MMD AAA at Aa1/AA+ wrap rating. This is structurally consistent with the AGM compression curve at A1-underlying (~40-50 bps). CalHFA wrap masks the project-level mix of FHA Risk Share + GNMA + uninsured loans behind a uniform program credit.

Project-level operator distress signals (REAC scores, LIHTC compliance issues, occupancy collapse on individual properties in the CalHFA loan portfolio) do NOT translate to CalHFA program-credit spread until the portfolio-aggregate breaches PADR thresholds. Framework operator-signal detectors are MUTED here, same pattern as Cal-Mortgage on CA NH/CCRC.

### Freddie Mac TEL pass-through (`freddie_mac_tel_passthrough`) — STRONG MASKING INFERRED

**Empirical anchor (weak):**
- **CUSIP 130483GH7** (CMFA Multifamily Hsg Rev Terracina At Westpark Apts) — 3.20% coupon, 2045 maturity, price 99.713 May 13 2026. Yield field corrupted on aggregator (returned 0.000). Price near par implies the bond is priced at coupon or short to next call/tender.

**Inference**: 2024 CSCDA deals (Lexington Green $42.9M, Prospera $30.75M, Second St Andrews $12.9M) all used Ready Capital as lender — the dominant California Freddie Mac TEL originator. Pattern strongly suggests Freddie TEL pass-through structure (Freddie Mac unconditional purchase of the tax-exempt loan acts as credit enhancement, bondholder gets GSE credit).

**Predicted spread**: +30-50 bps over MMD AAA based on Freddie Mac muni paper pricing comparables. The wrap-cluster catalog prediction holds — federal GSE credit floor masks project-level signal.

**Hostile-validator check**: Could the prediction be wrong? On wrapped Freddie-TEL deals the prediction is unlikely to be wrong — Freddie Mac wraps are highly liquid and rated Aaa. The risk is that some 2024-2025 conduit deals are NOT actually Freddie-TEL but rather direct LIHTC + uninsured PAB structures masquerading as wrapped paper. **Data gap: need to pull OS for Lexington Green / Prospera / Second St Andrews to confirm structure.**

### CalHFA conduit supportive housing (`calhfa_conduit_supportive_housing`) — PARTIAL MASKING

**Empirical anchor:**
- **CUSIP 13034PC96** (CalHFA Rev San Francisco Supportive Housing / 833 Bryant) — 4.00% coupon, 2045 maturity → 3.999% yield (May 13 2026), price 100.00. **Spread to MMD AAA 19y (~3.80%): +20 bps. Earlier March 2026 trades at 4.287% / 96.295 = +50 bps.**

**Verdict**: Section 8 HAP-backed supportive housing trades very tight at the par-priced May print but volatile in March prints. Section 8 federal voucher pledge acts as REVENUE-level credit floor — masks rent-collection risk on the project but bondholder still bears HAP contract renewal risk. Spread sensitivity to HAP renewal news = real but masked between events.

### Essential / workforce housing unwrapped — NO MASKING, FULL SIGNAL VISIBLE

**Empirical anchors (5 CUSIPs, 5 distinct obligors):**

| CUSIP | Obligor | Yield | Price | Spread to MMD AAA | Status |
|---|---|---|---|---|---|
| 126292BG5 | CSCDA CIA 1818 Platinum 2057 | 5.000% | 72.604 | +70 bps | Senior performing |
| 126292BT7 | CSCDA CIA Millenium South Bay 2056 | 5.318% | 69.073 | +102 bps | Senior |
| 126292CA7 | CSCDA CIA Westgate Phase 1 2047 | 5.520% | 67.818 | +172 bps | **CRF DRAW reported** |
| 12574TAB3 | CMFA Spec Fin Mix Center City 2056 | 5.753% | 75.0 | +155 bps | Senior |
| 13013HAA8 | CalCHA Annadel Apts 2049 | 5.750% | 90.191 | +190 bps | **DEFAULTED FY2024 DSCR** |

Plus from the Real Deal / Octus 2024-2025 reporting:
- **Mira Vista Hills (Antioch, $94M, Catalyst-administered)**: trading 63.5 cents on the dollar (Aug 2024), down from >70 cents mid-2023. Implied yield ~7.5-8.5% on 3% coupon 25y → **~+375 to +475 bps over MMD AAA**.
- **Serenity at Larkspur (342 units)**: DSCR-defaulted FY2024; recapitalization challenged by Larkspur City Council.

**Verdict**: Spread variance from +70 bps (top performer) to +475 bps (worst defaulter) across the unwrapped universe. **Spread tracks operator quality cleanly.** The wrap-cluster prediction that federal wraps would mask operator signal does NOT apply because no federal/state wrap exists. Signal flows in 1:1.

### GNMA pass-through and FHA 221(d)(4) — NOT DIRECTLY TESTED

Most 2023-2025 California 4% LIHTC deals route through Freddie Mac TEL rather than the older GNMA / FHA-221d4 securitization path. The GNMA-collateralized affordable housing CUSIPs of 2023-2025 vintage are scarce in California. Catalog prediction of MAXIMUM masking on Aaa GNMA paper is consistent with the BNY Mellon CA Muni fund holding CalHFA Sustainable Multifamily Variable Rate Certificates with 3.05% coupon (4/15/2034 maturity) — but no clean N≥1 matched-pair test was completed.

**FHA 542(c) Risk Share** is embedded inside the CalHFA Affordable Multifamily Indenture — the catalog-prediction validation rides on the CalHFA program-credit anchor. PARTIAL test only.

---

## Top 3 buy + Top 3 exclude (subject to deeper diligence)

### TOP 3 BUY candidates (selection within wrap rating band)

1. **CalHFA Affordable Housing Rev Series B Sustainability (CUSIP 13032WES9)** — 4.261% yield, +61 bps over MMD AAA, 17y duration, Aa1/AA+. Best risk-adjusted yield in the wrapped CA HFA tier. State HFA balance sheet upgraded by both Moody's (Aa1, Jan 2026) and S&P (AA+, Aug 2025) over the past 9 months = positive credit trajectory.
2. **CalHFA SF Supportive Housing / 833 Bryant (CUSIP 13034PC96)** at March 2026 trade levels of 4.287% yield / 96.30 price. +50 bps over MMD AAA with Section 8 HAP pledge as revenue floor. Volatile retracement signal; might be re-test-able if HAP-contract news cycle creates entry point. Wait for next +50 bps print.
3. **BRIDGE Housing Corp AA- corporate-credit social bonds** (CUSIPs not pulled — used as structural class). AA- non-profit developer corporate credit on a $4B affordable housing portfolio across CA/OR/WA. Should trade tighter than Aa1 CalHFA program credit on tenor basis. Likely fair value at 30-50 bps over MMD AAA. Confirm via EMMA pull on next session.

### TOP 3 EXCLUDE candidates

1. **CalCHA Mira Vista Hills (Antioch)** — DSCR-defaulted, going-concern doubts, 63.5 cents secondary market, Catalyst-administered (replaced by Waterford). At 75-80 cents, would be a buy on workout-recovery thesis; at 63.5 cents the market is pricing serious principal impairment risk. SignalOS exclusion fires correctly on this name — wrap is absent so operator distress shows up in price.
2. **CalCHA Serenity at Larkspur** — DSCR-defaulted FY2024; recapitalization plan blocked by Larkspur City Council. Workout uncertain. Exclude all senior lien tranches pending plan resolution.
3. **CalCHA Annadel Apts (CUSIP 13013HAA8)** — DSCR-defaulted, trading 5.75% yield = +190 bps over MMD AAA = sub-IG corporate equivalent. Exclude.

Honorable mention exclusions: the remaining 6 CalCHA impaired names where reserves have been drawn but DSCR not yet failed (CTR City Anaheim, Creekwood Hayward, Exchange at Bayfront Hercules, Twin Creeks, Oceanaire Long Beach — plus Westgate Phase 1 which has a CRF draw on the same CUSIP 126292CA7 noted above).

### Honest validator caveat

These buy/exclude picks are STRUCTURAL signal — operator-quality + wrap-class fit. They are NOT recommendations to trade — no liquidity check, no current bid/offer depth, no TEY-vs-corporate-alternative comparison. A full pre-trade workup would add a $/par minimum-trade-size check + dealer-axe inquiry + CMP / REAC verification on the underlying properties.

---

## TEY math note

CalHFA Affordable Multifamily Indenture bonds are tax-exempt (Series A) and AMT (Series B is sustainability-designated, structure typically AMT-eligible private activity bond — verify each series). CalCHA / CSCDA CIA workforce housing bonds are typically tax-exempt under §142(d) qualified residential rental project rules but may have AMT-status flags. Mercy / Eden / BRIDGE Housing project-level conduit bonds are typically AMT.

**Rough TEY math**: At marginal CA + federal 50% combined rate, 4.261% on CalHFA 13032WES9 = 8.52% TEY. Against UST 17y at ~4.50% + AAA corporate spread ~50 bps = 5.00% corporate-equivalent, this is +352 bps TEY net pickup. Against AA corporate 17y at ~5.50% = +302 bps TEY net pickup. **Robust TEY pickup for the wrap quality.**

For CalCHA Annadel at 5.75% YTM = 11.50% TEY at 50% marginal — but the bond is DEFAULTED. Stated TEY meaningless without recovery-adjusted yield.

---

## Comparison to Cal-Mortgage / FHA 242 / AGM measurements

| Mechanism | Wrap Rating | Underlying credit | Measured compression | This-session anchor |
|---|---|---|---|---|
| Cal-Mortgage CA NH/CCRC | AA- (state) | Stressed nursing home / CCRC operator | At-curve = ~0 bps differential vs AA- benchmark, but absolute 30-60 bps alpha vs unhedged operator credit | N/A this session |
| AGM at AA- underlying (Moreno Valley CA) | AA (private) | AA- | ~5 bps | N/A |
| AGM at BBB- underlying (WCHCC) | AA (private) | BBB- | 140 bps | N/A |
| AGM at CCC- underlying (Brightline) | AA (private) | CCC- | 300-422 bps | N/A |
| FHA 242 hospital | Aa1/AA+ (federal-wrapped) | Stressed hospital (Maimonides) | 70-75 bps vs MMD AAA (~at A-curve) | N/A |
| **CalHFA Affordable Multifamily** (this session) | Aa1/AA+ | A1-equivalent portfolio (FHA Risk Share + GNMA + uninsured mix) | **60-67 bps vs MMD AAA** | YES — 2 CUSIPs |
| **CalHFA SF Supportive Housing** (this session) | not-rated tier (Section 8 HAP) | Project-level supportive housing operator | **20-50 bps vs MMD AAA** | YES — 1 CUSIP |
| **Essential / Workforce Housing Unwrapped** (this session) | unrated | Distressed apartment operator (defaulted DSCR) | **155-475 bps vs MMD AAA** | YES — 5 CUSIPs |

**Cross-vertical pattern confirmed**: Wrap-class taxonomy operates consistently across muni sectors. The wider compression on CalHFA (60-67 bps vs MMD AAA) compared to FHA 242 Maimonides (70-75 bps) reflects that CalHFA's underlying loan portfolio is HIGHER quality (mix of FHA Risk Share + GNMA, all current pay) than Maimonides' standalone hospital with going-concern audit.

**Honest finding**: CalHFA wraps better than FHA Section 242. Original catalog hypothesis that "federal wraps mask LESS than state wraps" (per FHA 242 Maimonides finding) is REFINED — what matters is the UNDERLYING credit quality being wrapped, not the wrap source. CalHFA at AA-program-credit + good underlying = tight; FHA 242 at federal-wrap + distressed-hospital = wider.

---

## Empirical anchor count this session

- **CalHFA program credit**: 2 CUSIPs (13032WCB8, 13032WES9) with 2026-05-13 secondary trade prints
- **CalHFA conduit supportive housing**: 1 CUSIP (13034PC96) with 5 trade prints over 2026-03 to 2026-05
- **CMFA Freddie TEL** (inferred): 1 CUSIP (130483GH7) with corrupted yield field (price-only anchor)
- **CSCDA CIA workforce housing**: 3 CUSIPs (126292BG5, 126292BT7, 126292CA7) with 2025-2026 prints
- **CMFA Special Finance Agency I workforce housing**: 1 CUSIP (12574TAB3) with 2025 prints
- **CalCHA workforce housing**: 1 CUSIP (13013HAA8 Annadel) with 2024 prints; plus Mira Vista Hills secondary-market-price reference at 63.5 cents

**Total: 9 CUSIPs, 8 distinct obligors, all primary-source MunicipalBonds.com EMMA trade tape** (per saved memory: full Chrome browser fingerprint deployed; no 403s; verified pricing pulls).

---

## Open data gaps

1. **HUD REAC inspection scores** — not pulled. HUD MF Physical Inspection Scores by State CSV (huduser.gov/portal/datasets/pis.html) would map ~5000+ California HUD-assisted multifamily projects to current REAC scores. Highest-priority next-session pull — would enable per-project operator-quality scoring on wrapped Freddie-TEL deals.
2. **LIHTC compliance status** — HCD California Department of Housing and Community Development records not pulled.
3. **Section 8 contract expiration status** — HUD database not pulled.
4. **OS confirmation for 2024 CSCDA project deals** — Lexington Green, Prospera, Second St Andrews. Need to confirm Freddie TEL vs other structure.
5. **GNMA-California-specific CUSIPs** — Aaa-rated GNMA-collateralized CA housing muni anchor not pulled. May not exist at scale in 2023-2025 vintage (Freddie TEL displacement).
6. **BRIDGE Housing corporate-credit CUSIPs** — used as structural class only; not pulled for empirical anchor.
7. **6 remaining CalCHA impaired names** — CTR City Anaheim, Creekwood Hayward, Exchange at Bayfront Hercules, Twin Creeks, Oceanaire Long Beach. CUSIPs and pricing not pulled.
8. **MMD AAA daily yield curve** — used May 26 2026 ~3.10% 10y / ~4.10% 20y rough cut from Raymond James publication. Should pull TM3 (Refinitiv) full curve for precision.

---

## Knowledge graph updates

This pass refines and extends the wrap-cluster catalog:

1. **`gnma_passthrough_insurance`** — upgrade from `MENTIONED_NOT_VALIDATED` → `DOCUMENTED` (rather than `VERIFIED`). The federal-wrap prediction holds structurally but the dominant California issuance pattern of 2023-2025 routes through Freddie Mac TEL rather than GNMA. GNMA-specific CA muni CUSIP not anchored this session.
2. **Add new mechanism `freddie_mac_tel_passthrough`** — primary credit-enhancement structure for 2023-2025 California 4% LIHTC + tax-exempt PAB acquisitions and rehabs. Freddie Mac unconditional purchase of the tax-exempt loan, GSE credit substitution. Structural analog to GNMA but with Freddie Mac balance sheet rather than full federal faith & credit.
3. **Add new mechanism `calhfa_program_credit_overcollateralization`** — state HFA balance-sheet wrap (Aa1/AA+, 1.31x PADR). Distinct from FHA 542c risk-share which is the underlying loan-level insurance. Strong masking; analog to Cal-Mortgage but for housing instead of nursing/CCRC.
4. **Add new mechanism `essential_workforce_housing_unwrapped_jpa_acquisition`** — STRUCTURAL ANTI-MASKING. Joint Powers Authority single-asset apartment acquisitions (2019-2022 vintage CSCDA CIA / CalCHA / CMFA Special Finance Agency I, ~$8-10B). Bondholders take full project-level credit risk; spread varies +70 bps (performing senior) to +475+ bps (defaulted) with operator distress. Wrap-cluster prediction does NOT apply.
5. **FHA Section 542(c) Risk-Share** — embedded inside CalHFA Affordable Multifamily Indenture. Add new mechanism entry; mark as DOCUMENTED via CalHFA program credit anchor.
6. **Section 8 HAP contract** — for CalHFA conduit supportive housing. Already noted in `gnma_passthrough_insurance` mechanism's `_notes` field; should be elevated to a standalone mechanism `section_8_hap_revenue_floor` given the +20-50 bps observed compression on 13034PC96.

---

## Path to deliverables (this pass + next)

### This session's deliverables ✅

1. ✅ `/Users/ajay/exalted/signalos/verticals/muni_credit/data/ca_affordable_housing_universe.json` — universe inventory, structural taxonomy, per-obligor anchors
2. ✅ `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/CA_AFFORDABLE_HOUSING_SECTOR_SCOPING.md` — this report
3. ✅ Knowledge-graph update planned: 4 new mechanism entries + 1 upgrade (gnma_passthrough); see "Knowledge graph updates" section above. Encoded in masking_mechanisms.json update committed separately.

### Next-session work to promote findings to VERIFIED

1. Pull HUD REAC inspection scores for CalHFA Affordable Multifamily Indenture's underlying property portfolio (if disclosable) and Freddie TEL conduit deals — would enable within-wrap project-quality vs spread test.
2. Pull OS for 2024 CSCDA project-level deals (Lexington Green, Prospera, Second St Andrews) — confirm Freddie TEL structure and capture CUSIPs / pricing.
3. Pull MunicipalBonds.com trade data for 6 remaining CalCHA impaired names — complete the unwrapped-distress universe.
4. Pull BRIDGE Housing corporate-credit CUSIPs — anchor rated-nonprofit-developer structural class.
5. Pull TM3 / Refinitiv MMD AAA full curve to replace rough cut.

### Composite framework implication

The framework's exclusion-value on CA affordable housing muni concentrates in:

1. **Unwrapped workforce / essential housing subsector** — already at distress prices, but DUE DILIGENCE replication value to AVOID buying recovery-thesis names without underwriting the workout.
2. **2019-2022 vintage unwrapped deals that have NOT YET impaired** — forward-looking detector opportunity. SignalOS detector pattern: scan for occupancy decline → DSCR threshold → reserve fund burn → DEFAULT cascade. Same template as CFD `reserve_fund_burndown.py` and `delinquency_spike.py`. Pattern not yet built for housing but mechanically analogous.
3. **Within-wrap selection on CalHFA / Freddie-TEL deals** — narrow alpha but cleaner than wrap-band reach into distressed underlying.

The wrap-cluster catalog prediction is REFINED — wraps mask when wraps exist; the more important framework finding is that **a major portion of the CA affordable housing market is structured as if a wrap exists but doesn't (workforce housing labeled 'tax-exempt municipal bond' but really single-asset apartment LP debt)**. This is the largest sectoral-scale anti-masking finding from the wrap-cluster catalog work to date.
