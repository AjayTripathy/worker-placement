# Diligence Report — CUSIP 452641HM8

**Imperial Community College District (Imperial County, CA) — 2017 General Obligation Refunding Bonds**
4.000% coupon, term bond due 2040-08-01 · BAM-insured · Cutoff: 2026-06-20

---

## (a) Verdict & buy thesis

**VERDICT: CLEAR TO BUY** (high-quality unlimited-tax GO; community-college fiscal-distress proxy —
ACCJC accreditation — is *good standing / Accredited*; high seismic and a Colorado-River-dependent
ag tax base are real, but both are buffered by the unlimited-rate pledge, the Teeter Plan, a BAM
insurance wrap, and senior-most water rights).

This is a voter-approved **unlimited ad-valorem general obligation** bond of a California community
college district. **A CCD GO is the same security as a K-12 GO** — Imperial County is legally
obligated to levy property taxes **without limitation of rate or amount** to pay it, the levy is
backed by the **SB-222 statutory first lien** (added Gov. Code §53515 family / Education Code §15251),
and the County runs a **Teeter Plan** so the District receives 100% of the secured levy regardless of
taxpayer delinquency. The bond is **BAM-insured (S&P "AA" insured) over a strong S&P "A+" underlying**.
It is trading near par (~99.78) because the 4.0% coupon is close to today's market level — this is
*not* a distressed or deep-discount situation, and the tiny discount stays within the IRS de-minimis
threshold, so there is **no ordinary-income tax drag** (unlike a deep-discount name).

**The two things the matcher couldn't resolve, now resolved:**
1. **Accreditation (the CCD analog of AB-1200): RESOLVED to GOOD STANDING.** Imperial Valley College
   is **confirmed present in the authoritative ACCJC roster** and carries **"Accredited" / no
   sanction** (not Warning, Probation, or Show Cause), confidence VERIFIED, as of 2026-06-19. This
   converts the matcher's `CC-UNKNOWN` (a soft REVIEW, never auto-clean) into a confirmed clean read.
2. **Seismic (the missing Ss): RESOLVED to HIGH — Ss ≈ 1.98.** Imperial Valley is one of the most
   seismically active places in California (Imperial / Cerro Prieto / Brawley faults; 1979 M6.4
   Imperial Valley and 2010 M7.2 El Mayor–Cucapah ruptures). This is a genuine catastrophe-exposure
   flag. It does **not** sink the credit, for three structural reasons spelled out in §d/§g, but it is
   the single most important physical-risk caveat on the name and the buyer should hold to maturity.

The thesis: buy a near-AA (insured) / A+ (underlying), statutorily-lien-secured, AI-/wildfire-insulated,
near-par tax-exempt cash flow whose two real risks — high seismicity and a single-source
(Colorado-River) ag/geothermal tax base — are each materially buffered by the unlimited-rate pledge,
the Teeter advance, the BAM wrap, and IID's senior-most (1901-priority) water entitlement.

---

## (b) Accreditation — the CCD fiscal-distress signal (lead finding)

**Finding: Imperial Valley College = GOOD STANDING ("Accredited"), no sanction. VERIFIED against the
ACCJC authoritative roster as of 2026-06-19.**

- **Why this is the right signal.** California's AB-1200 interim certification (Positive / Qualified /
  Negative) — the fiscal-distress proxy we use for K-12 GO — governs **K-12 districts only**.
  Community college districts are not in it. The correct operating-stress proxy for a CCD is its
  **ACCJC accreditation status** (Accrediting Commission for Community and Junior Colleges), because
  loss of accreditation cuts a college off from Title IV federal aid and state apportionment — the
  CCD analog of an AB-1200 Negative. The escalating sanction ladder is:
  *good standing < On Warning < Probation < Show Cause (+ Restoration).*
- **The resolution.** SignalOS' ACCJC overlay (`accjc_overlay.py`) pulled the authoritative ACCJC
  roster (138 institutions, ACCJC REST directory, as_of 2026-06-19) and matched **Imperial Valley
  College**: status_raw **"Accredited"**, **no sanction**, normalized to **good_standing**,
  confidence **VERIFIED**, system "Imperial CCD". (Saved: `raw/accjc_status.json`.)
- **Honesty discipline applied.** We assert *good standing* only because the college is **confirmed
  present in the roster AND carries no sanction** — not merely "absent from a sanction list." That is
  the difference between this VERIFIED read and the matcher's prior `CC-UNKNOWN` (which we treat as a
  soft REVIEW, never clean, precisely because unverifiable ≠ clean).
- **The one open item, flagged honestly.** IVC's next comprehensive review is the **2026 cycle**; the
  on-campus ACCJC visit occurred **Feb 23–24, 2026**. As of cutoff, the roster status field still
  reads **Accredited** and **no commission action (reaffirmation or sanction) has been posted** from
  that visit. The cumulative directory status is the binding signal and it is clean; the specific
  post-visit commission decision is a **monitoring item** (a sanction, if one were imposed, would be
  an operating-stress headline — *not* a default trigger on the GO; see §d).
- **Last prior action:** 2023 Midterm Report, ACCJC action letter dated 2023-06-15; first accredited
  1962. No history of probation/show-cause surfaced.

**Bottom line on the matcher's CC-UNKNOWN: it is now a confirmed CLEAN, not an unknown.**

---

## (c) Seismic & water context — the two real physical risks (lead finding)

### Seismic — HIGH (the "missing Ss" is now read)

**Finding: Ss ≈ 1.98 (very high). VERIFIED against USGS ASCE 7-22.** Imperial Valley is among the
most seismically active regions in the state.

- **The number.** USGS ASCE 7-22 building-code service at El Centro (32.792, −115.5631, Site Class D):
  **Ss = 1.98**, S1 = 0.72, SDS = 1.30, **Seismic Design Category D**. For calibration, the Chico USD
  GO we cleared earlier had Ss ≈ 0.93; **this is roughly 2× the short-period hazard.** The earlier
  screen's "Ss read missing" is now filled, and it confirms the brief's concern: this tax base sits on
  active faults (Imperial, Brawley, Cerro Prieto), the **1979 M6.4 Imperial Valley** quake (severely
  damaged the Imperial County Services Building in El Centro), and the **2010 M7.2 El Mayor–Cucapah**
  rupture (widespread liquefaction across the southern Imperial Valley, 0.3–0.6g near Calexico/El
  Centro). This is real, not theoretical.
- **Why it does not sink the credit (mechanism, not hand-waving):**
  1. **Unlimited-rate pledge.** The OS is explicit that a "**complete or partial destruction of
     taxable property caused by … earthquake … could cause a reduction in the assessed value … and
     necessitate a corresponding increase in the annual tax rate.**" The pledge is **without
     limitation of rate or amount** — so an AV hit is absorbed by *raising the levy rate on the
     surviving base*, not by impairing debt service. (The OS discloses this risk honestly — a
     positive: the marketed security and the disclosed risk are aligned, no divergence.)
  2. **Teeter Plan** insulates against the *collection* disruption (the County advances 100% of the
     secured levy).
  3. **BAM insurance wrap** sits in front of the bondholder for timely principal/interest if a
     catastrophe ever did stress the District's own resources.
- **Residual risk that remains:** a severe, widespread quake could damage so much of the base that the
  *rate increase required* becomes politically/practically hard, and could disrupt the College's
  physical plant/operations. This is a tail risk, mitigated but not eliminated. It is the single most
  important reason to treat this as a **hold-to-maturity** position, not a trading line.

### Water & the ag/geothermal tax base — concentrated source, senior-most right

**Finding: the tax base is Colorado-River-dependent agriculture + geothermal/solar power generation;
the water risk is real at the macro level but heavily buffered by IID's 1901-priority senior water
right. CONSISTENT.**

- Imperial Valley farms ~470,000 acres on **Colorado River water as its sole supply**, delivered by
  the Imperial Irrigation District (IID), generating >$3B/yr of economic activity (nation's winter
  vegetables). The water story is therefore the *economic* story of the tax base.
- **The key insulation point:** IID holds **2.6 million acre-feet of senior present-perfected rights
  with a 1901 priority date — the most senior single entitlement on the Colorado River.** In a
  shortage, junior users (much of Arizona, urban Southern California via MWD) are curtailed *first*;
  IID's senior right is curtailed *last*. Post-2026 Colorado River operations are under active
  Federal negotiation (framework not effective until WY2027, beginning Oct 1 2026), and IID is
  pursuing *compensated conservation* (up to ~100,000 af of 2026 savings under the QSA/SCIA), which
  trades water for cash rather than forced fallowing. Salton Sea exposure is the long-tail
  environmental overhang, not a near-term debt-service issue.
- **Net:** the water risk is a **slow-moving macro overhang on land values**, not a debt-service
  cliff. Even a meaningful fallowing program shows up as gradual AV pressure — which the unlimited-
  rate pledge absorbs — not as a sudden levy failure. This is a *credit*, not a *price/rate-regime*,
  statement.

---

## (d) Security & pledge — what legally compels payment

**Finding: UNLIMITED AD-VALOREM GENERAL OBLIGATION, BAM-insured. VERIFIED against the Official
Statement (`raw/official_statement.pdf`).**

- **Issuer/CUSIP binding — VERIFIED.** CUSIP base **452641** = "Imperial Community College District
  (Imperial County, California)." Suffix **HM8** binds, in the OS maturity scale, to the
  **$10,690,000 4.000% Term Bond due August 1, 2040** (yield at issue 3.480%, price 104.221C). The
  issue is the **2017 General Obligation Refunding Bonds**, dated 2017-12-13 (EMMA issue ER383454).
  Cross-checked: EMMA security detail (coupon 4.0 / maturity 08/01/2040 / dated 12/13/2017 / callable
  Yes / next call 08/01/2027 @ 100) and the OS scale. The tentative identification in the brief is
  **correct**.
- **The legal mechanism (quoted from the OS):** "The Board of Supervisors of Imperial County has the
  power and is obligated to **annually levy ad valorem taxes upon all property subject to taxation by
  the District without limitation of rate or amount** … for the payment of principal of and interest
  on the Refunding Bonds."
- **Statutory lien (SB-222):** "Pursuant to Senate Bill 222 effective January 1, 2016, voter approved
  general obligation bonds which are secured by ad valorem tax collections, including the Refunding
  Bonds, are secured by a **statutory lien on all revenues received pursuant to the levy and
  collection of the property tax** … Said lien **attaches automatically and is valid and binding from
  the time the bonds are executed and delivered**." This is the strongest muni security: a perfected
  first lien on the tax stream, ahead of general creditors. (Same security as a K-12 GO.)
- **Teeter Plan (credit positive):** Imperial County has adopted the Teeter Plan (Cal. Rev. & Tax.
  Code §4701 et seq.); the District "**receives 100% of secured property taxes levied** in exchange
  for foregoing … interest and penalties … on delinquent taxes." Taxpayer delinquency does not reduce
  debt-service cash flow.
- **Insurance wrap (BAM):** Insured by **Build America Mutual Assurance Company**; **insured rating
  S&P "AA," underlying rating S&P "A+"** at issuance. The wrap is a timely-payment backstop. *Wrap
  economics:* because the **underlying is already A+** (strong), the rating-conditional spread
  compression the wrap buys is modest (wraps compress most where the underlying is weak — e.g. BBB-/
  CCC-; at A+ the underlying carries the credit, the wrap trims a few bps). So treat this as an
  A+-underlying credit with a thin insurance cushion, not as a wrap-dependent name.
- **Tax status — Tax-exempt.** Jones Hall bond-counsel opinion: interest excluded from federal gross
  income, **not** an AMT preference item for individuals, and **exempt from California personal income
  tax**.

---

## (e) Issuer & tax base — AV, concentration, debt burden

**Finding: multi-billion-dollar, broadly diversified base with a visible ag + geothermal/solar
power-generation cluster; light direct debt; AV figures are FY2017-18 vintage (current AV is a
monitoring item).**

- **Assessed valuation (OS, FY2017-18, issuance year):** total AV **$12,083,143,285**; local secured
  AV **$10,744,538,490**. The OS AV history is *rising* (FY2015-16 → FY2017-18: $11.55B → $12.08B).
  California Prop 13 (Art. XIIIA) caps annual AV growth at ~2% absent a change of ownership/new
  construction, so the base is directionally **higher** today than the 2017 vintage.
  *Caveat: a current-year (FY2024-25/25-26) AV was not retrievable from a primary source at cutoff —
  the Imperial County Assessor roll figure is a monitoring item (see §g).*
- **Debt burden — light.** OS Direct-and-Overlapping table (as of 2017-11-01): **direct debt = 0.57%
  of AV**; total direct + overlapping tax/assessment debt 2.72%; combined total debt 4.26% of AV. Low
  leverage on a $12B base.
- **Top-taxpayer concentration — moderate, with the brief's ag/geothermal signature.** Top-20 secured
  taxpayers = **9.57% of AV**. The top names confirm the Imperial-Valley economy exactly:
  - **#1 Alphabet Farms LLC (Agricultural) — 1.53%** of AV (largest single taxpayer)
  - **#2 MidAmerican Energy Holding Corp. (Power Generation) — 1.39%**
  - **#3 Hudson Ranch Power I LLC (geothermal) — 0.66%**, #4 Heber Field Company (geothermal) 0.55%,
    #11 Second Imperial Geothermal 0.40%, plus multiple solar (Campo Verde, Imperial Valley Solar 1,
    Centinela Solar) names.
  - Agricultural names (#6 MFC Imperial, #14 De Jong, #15 Imperial Valley Farms, #20 Meyer Imperial)
    and commercial (Walmart, Imperial Valley Mall, Gran Plaza) round it out.
  No single taxpayer exceeds ~1.5% of AV; the base is **diversified at the parcel level** but
  *thematically* concentrated in two correlated sectors — **Colorado-River-dependent ag** and
  **renewable/geothermal power** — both tied to the same regional water-and-energy story (§c). That
  thematic concentration is the honest nuance: the names are many, but the *drivers* are few.
- **Geothermal note:** the geothermal cluster (Hudson Ranch / Heber / Second Imperial — the
  Salton-Sea geothermal field, increasingly a lithium-extraction play) is a *growth* vector for the AV
  base, partially offsetting ag/water downside. Not modeled as credit-positive here, but worth noting.
- **Enrollment.** OS FTES history ~6,000–7,400 over FY2008–FY2017. Enrollment pressures *operating*
  (apportionment) revenue, **not** GO debt service, which is paid from the separate dedicated
  ad-valorem levy. The accreditation status (§b) is the cleaner operating-health read and it is good.

---

## (f) The risk screens (reconciled)

| Screen | Read | What it means here |
|---|---|---|
| **AI / tech-crash insulation** | **99 / 100 (fully insulated)** | This is a *local property-tax* credit; debt service comes from the Imperial County ad-valorem levy, **not** the CA General Fund. The State-GF capital-gains channel that cut *State* GO ~4–5 notches in the dot-com bust does **not** touch a CCD unlimited-tax GO. An AI/tech crash does not impair this property-tax stream. (Credit insulation, not a price/rate statement.) |
| **Wildfire** | **0% high-fire tail (low)** | Imperial Valley is **desert / irrigated cropland**, not wildland-urban interface. The insurer-withdrawal → AV-erosion channel is not materially present. Correct read. |
| **Flood tail** | **91% NRI (flagged REVIEW — reconciled DOWN)** | The high FEMA National Risk Index flood score is a **desert-hydrology artifact**, treated honestly: NRI flood expected-annual-loss runs hot in arid basins (flash-flood / canal / Salton-Sea-basin scoring) where exposure is concentrated and built value sparse. The Imperial Valley tax base is **irrigated farmland**, not floodplain housing stock; the OS itself names flood among AV risks but with no flood-specific covenant or history of flood-driven AV impairment. **Net: the 91% is not a load-bearing physical risk for this GO**; the unlimited-rate pledge would absorb any localized AV hit. Treat as REVIEW-noted, not a flag. |
| **Earthquake** | **Ss ≈ 1.98 (HIGH) — resolved** | The one genuinely high physical risk. See §c. Real catastrophe exposure, structurally buffered by unlimited-rate pledge + Teeter + BAM wrap; hold-to-maturity. |

The screens are *honest both ways*: wildfire and flood are de-rated where the geography doesn't
support the model, and seismic is escalated where it does.

---

## (g) Liquidity, execution, tax & yield

**Liquidity — orderly, genuinely two-sided, near our level. Source: `raw/emma_trade_tape.json`
(MSRB trade tape, the authoritative trade-level source; 810 prints since 2017).**

- **Activity:** **100 prints in the trailing 365 days across 37 distinct trade days** — regular, not
  episodic. Trade-type mix (365d): 25 sale-to-customer (customer buys), 20 purchase-from-customer
  (customer sells), 55 inter-dealer.
- **Two-sided near our level (fire-sale check):** in the last weeks the tape shows a customer **sale**
  at **99.62 / 4.035%** (2026-05-21) and a dealer print at **99.781 / 4.020%** (2026-05-29), bracketing
  our ~99.78 entry. This is live price discovery at/near par, not a forced liquidation.
- **Range (365d):** YTW min 3.442 / median **4.089** / max 4.653; price min 93.00 / median 99.08 /
  max 100.75. Our entry at ~99.78 sits at the **recent upper-price / lower-yield end** of the band —
  fair-to-slightly-rich vs the trailing median, consistent with the recent rally toward par.
- **Live-quote caveat (HONEST FLAG):** Per protocol a live IBKR quote was sought before pricing; the
  **IBKR muni feed does not carry this CUSIP** (consistent with its sparse/close-only muni coverage),
  so a live bid/ask is **UNVERIFIABLE via IBKR**. Execution is anchored on the EMMA/MSRB trade tape
  (last print 2026-05-29), which is the correct authority for muni levels. For an HTM ladder the
  bid/ask is a one-time ~1–3 bps/yr amortized buy-side cost — immaterial.

**Tax & yield — near par, de-minimis NOT breached → no ordinary-income drag.**

- **Coupon fully tax-exempt** (federal non-AMT + CA), per Bond Counsel (§d).
- **De-minimis check (the key tax point):** purchase ~**99.78** vs par; ~14.1 years to the 2040
  maturity → de-minimis threshold ≈ **96.47** (100 − 0.25 × 14.1). The purchase price is **above** the
  threshold, so the small ~0.2-point discount accretes as a **capital gain, NOT ordinary income**.
  There is **no ordinary-income tax drag** on this name (contrast the deep-discount Chico case where
  the discount was taxed as ordinary income).
- **Yield:** gross **yield-to-worst ≈ 4.02–4.04%** (EMMA YX = MSRB yield-to-worst, priced to the worse
  of the 2027 par call vs the 2040 maturity — labeled correctly as YTW, not YTM). The quoted
  **after-tax taxable-equivalent yield ≈ 8.1%** is a clean CA-top-bracket gross-up of the exempt
  coupon (~4.04% / (1 − ~0.50) ≈ 8.1%), with **no discount-tax netting needed** because de-minimis is
  not breached.
  - *Self-discipline note (house rule on TEY conflation): the ~8.1% is an **after-tax
    taxable-equivalent** figure; gross YTW is ~4.04%; these are not the same metric.*
- **Call (mild, in our favor):** callable at par 2027-08-01. With a 4.0% coupon trading near par in a
  ~4% market, the call is roughly at-the-money; YTW≈YTM is the realistic case. Not a windfall, not a
  trap.

---

## (h) Risks / what could go wrong

1. **Seismic catastrophe (the dominant physical risk).** Ss ≈ 1.98; active Imperial/Brawley/Cerro
   Prieto faults; 1979 M6.4 and 2010 M7.2 precedents. A severe widespread quake could damage the AV
   base and the College plant. **Buffered** by unlimited-rate pledge + Teeter + BAM wrap, but not
   eliminated → **hold-to-maturity**, don't size as a trading line.
2. **Colorado-River / water macro overhang (slow-moving).** Sole-source river supply for an ag base;
   post-2026 operations under Federal negotiation. **Buffered** by IID's 1901-priority senior-most
   right (curtailed last) and compensated-conservation (cash for water, not forced fallowing). Shows
   up as gradual AV pressure the unlimited-rate pledge absorbs, not a levy cliff. Salton Sea = long-
   tail environmental overhang.
3. **Thematic tax-base concentration.** Parcel-level diversified (top-1 = 1.53%, top-20 = 9.57%), but
   the *drivers* cluster in two correlated sectors (Colorado-River ag; geothermal/solar power) tied to
   the same water/energy story. A correlated shock to Valley water would hit both legs. Geothermal/
   lithium growth is a partial offset.
4. **Accreditation — Feb-2026 comprehensive-review decision pending (monitoring item).** Current ACCJC
   status is clean (Accredited / good standing), but the post-visit commission action from the 2026
   comprehensive review was not yet posted at cutoff. A sanction (if any) would be an operating-stress
   *headline*, **not** a default trigger on the GO (the lien rides the AV levy, county-collected).
   Re-check the next ACCJC commission-actions report.
5. **Stale AV / continuing disclosure (UNVERIFIABLE current AV — flagged honestly).** The AV, debt,
   and concentration figures are the **FY2017-18 OS vintage**. A current-year Imperial County Assessor
   roll AV and current GO debt-service coverage were **not retrievable from a primary source at
   cutoff** (EMMA continuing-disclosure fetch was rate-limited; the Assessor roll figure was not
   web-available). Prop 13 makes the base directionally *higher*, and the light 0.57% direct-debt/AV
   leaves wide headroom — but **current AV/coverage are a monitoring item, not a clean confirmation**.
6. **Interest-rate / price risk.** A ~14-year 4% bond near par; if rates rise the mark falls. This is
   price/regime risk, not credit impairment; HTM neutralizes it (statutory lien + unlimited levy →
   par at 2040, subject to the at-the-money 2027 call).
7. **No distress events affirmatively ruled out exhaustively.** No default/missed-payment/rating-
   withdrawal surfaced, but the EMMA material-events list could not be fully machine-parsed at cutoff
   (Terms-of-Use wall + rate limit). This is "no distress found," **not** "distress exhaustively
   ruled out."

---

## (i) Sources & attached documents

All files in `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/452641HM8/raw/`.

| File | What it is | Authoritative source |
|---|---|---|
| `official_statement.pdf` | **Official Statement**, $16,200,000 Imperial CCD 2017 GO Refunding Bonds (186 pp). Establishes unlimited-tax pledge, SB-222 statutory lien, Teeter Plan, BAM wrap (insured S&P AA / underlying A+), AV $12.08B (FY17-18), 0.57% direct debt/AV, top-20 = 9.57%, the HM8→4.0% 2040 term-bond binding, Jones Hall tax opinion, and the earthquake/flood AV-risk disclosure. | EMMA issue ER383454, doc `ER1108709-ER867124-ER1267816.pdf` |
| `emma_security_details.html` | EMMA Security/Details page (post-disclaimer): coupon 4.0%, maturity 08/01/2040, dated 12/13/2017, callable Yes, next call 08/01/2027 @ 100, embedded trade tape. | https://emma.msrb.org/Security/Details/452641HM8 |
| `emma_trade_tape.json` | MSRB trade tape, 810 prints 2017–2026; two-sided customer/dealer prints at ~99.6–99.8 in May 2026; YX = yield-to-worst. | EMMA / MSRB Real-Time Transaction Data |
| `accjc_status.json` | ACCJC overlay result: Imperial Valley College = "Accredited"/good_standing, no sanction, VERIFIED, roster as_of 2026-06-19. | ACCJC REST directory (`accjc_overlay.py`) |
| `screens_and_sources.json` | Consolidated SignalOS screens (accreditation, seismic Ss=1.98, water, AV/concentration, tape rollup, AI/fire/flood). | SignalOS muni_credit vertical |

**External primary sources cited (not file-attachable):**
- ACCJC — Imperial Valley College institution record: https://accjc.org/institution/imperial-valley-college/ ;
  IVC accreditation page: https://www.imperial.edu/about/accreditation/
- USGS ASCE 7-22 seismic design values, El Centro (32.792, −115.5631), Site Class D: Ss = 1.98 / S1 = 0.72 / SDS = 1.30 / SDC D.
- USGS — 1979 Imperial Valley & 2010 M7.2 El Mayor–Cucapah liquefaction (OFR 2011-1071): https://pubs.usgs.gov/of/2011/1071
- Imperial Irrigation District — Colorado River senior rights (2.6 MAF, 1901 priority), QSA/SCIA conservation, post-2026 operations: https://www.iid.com/

---

### Verification ledger (claim → method → authority → finding)

| Claim | Method | Authority | Finding |
|---|---|---|---|
| CUSIP 452641HM8 = Imperial CCD 2017 GO Refunding, 4.0% 2040 term | OS maturity scale + EMMA security detail | OS / EMMA | **VERIFIED** |
| Unlimited ad-valorem GO (not COP/CFD/lease) | Read OS security section | OS | **VERIFIED** |
| SB-222 statutory lien | Read OS statutory-lien paragraph | OS / Gov. Code §53515 family | **VERIFIED** |
| Teeter Plan (100% secured levy) | Read OS Teeter section | OS | **VERIFIED** |
| BAM insured S&P AA / underlying S&P A+ | Read OS cover + RATINGS | OS | **VERIFIED** |
| Tax-exempt (fed non-AMT + CA) | Read Bond Counsel opinion | OS (Jones Hall) | **VERIFIED** |
| **Imperial Valley College ACCJC = good standing / Accredited, no sanction** | ACCJC roster match + sanction check | ACCJC REST roster (as_of 2026-06-19) | **VERIFIED (CC-UNKNOWN resolved → CLEAN)** |
| **Seismic Ss ≈ 1.98 (HIGH)** | USGS ASCE 7-22 service @ El Centro | USGS | **VERIFIED (missing Ss now read)** |
| Colorado-River sole supply; IID 1901-priority senior right | Issuer/operator disclosure + reporting | IID / news | **CONSISTENT** |
| AV $12.08B / 0.57% direct debt / top-20 9.57% | Read OS tables | OS (Cal Muni Statistics) | **VERIFIED (FY2017-18 vintage)** |
| Two-sided non-fire-sale market ~99.7 | Parsed MSRB trade tape | EMMA/MSRB | **VERIFIED** |
| De-minimis NOT breached → no ordinary-income drag | Threshold calc vs ~99.78 price | IRC de-minimis rule | **VERIFIED** |
| Flood 91% NRI = desert-hydrology artifact, not load-bearing | NRI vs geography + OS flood mention | FEMA NRI / OS | **REVIEW (reconciled DOWN, honest)** |
| Post-2026 ACCJC comprehensive-review decision | Searched ACCJC actions | ACCJC | **PENDING (monitoring item)** |
| Current-year AV / coverage | Searched EMMA CDD + County Assessor | EMMA / County | **UNVERIFIABLE (stale FY2017-18; monitoring)** |
| Live bid/ask | IBKR contract search | IBKR | **UNVERIFIABLE (not carried)** |
| No distress / default events | EMMA scan (partial) | EMMA | **No distress found (not exhaustively ruled out)** |

<!-- current-state-refresh -->
### Current-State Verification (AV / coverage refresh — 2026-06-20)

Refreshed 2026-06-20 via a SERIAL, throttled EMMA continuing-disclosure pull (the original UNVERIFIABLE flag was an EMMA 403 rate-limit from concurrent scraping, not a real disclosure gap). Latest issuer annual report: _Annual Financial Disclosures Posted 03/14/2026  for the year ended 06/30/2025 (223 KB)_. **Current total assessed valuation (levy base): $17,652,863,517 for FY2025-26 (+8.0% YoY)**; secured-tax delinquency **1.84%**; audited FY2025 on file. — AV trend 2022-23 $14.64B → 2023-24 $15.57B → 2024-25 $16.35B → 2025-26 $17.65B For an unlimited ad-valorem GO the AV base + the delinquency cushion ARE the 'coverage' — there is no DSCR; the levy rate floats to hold debt service constant. **This resolves the prior 'current AV/coverage UNVERIFIABLE' caveat.**
