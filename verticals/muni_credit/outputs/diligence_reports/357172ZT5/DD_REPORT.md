# Diligence Report — CUSIP 357172ZT5

**Fremont Union High School District (Santa Clara County, CA) — General Obligation Bonds, Series 2019A**
4.00% coupon · due 2038-08-01 · dated 2019-06-06 · tax-exempt
Cutoff: 2026-06-20 · Status: in buy book · Verdict: **BUY**

---

## a. Snapshot

| Field | Value | Source |
|---|---|---|
| Issuer | Fremont Union High School District (FUHSD), Santa Clara County | EMMA OS cover; EMMA Security/Details |
| Series | General Obligation Bonds, Series 2019A (Election of 2014 + Election of 2018 authorizations) | OS cover |
| CUSIP | 357172ZT5 | EMMA Security/Details |
| Coupon / Maturity / Dated | 4.00% / 2038-08-01 / 2019-06-06 | EMMA Security/Details + OS |
| This maturity's par | $6,035,000 (of $100,280,000 Series 2019A) | EMMA maturity scale |
| Pledge | Unlimited ad-valorem GO + SB-222 statutory lien (Govt Code §53515) + Resolution pledge | OS, "Security and Source of Payment" |
| Tax status | Tax-exempt (federal + CA personal income tax); not an AMT preference item | OS, Orrick opinion; EMMA |
| Ratings (at issue) | Moody's **Aaa** / S&P **AAA** | OS cover |
| Last trade (tape) | 2026-03-26 @ 98.822, YX 4.122% (customer buy) | EMMA RTRS trade tape |
| Computed YTM @ 98.822 | **4.124%** to maturity; mod. duration **9.35 yr** | compute_bond_analytics (validated vs EMMA YX ±0.002) |
| After-tax TEY | **~8.29%** (YTM × 2.01 CA top-bracket gross-up) | derived |
| Call | Callable at **par** on any date on/after 2027-08-01 (maturities ≥ 2028) | OS, "Optional Redemption" |

**One-line thesis:** A AAA/Aaa unlimited-ad-valorem GO of a *community-funded* (basic-aid) Silicon Valley high-school district sitting on a ~$75.8B (2018-19) / materially larger today assessed-value base, with direct GO debt at **0.54% of AV**, no taxpayer above 2.3% of the roll, and a SB-222 statutory lien. The "tech-wealth AV" framing is a strength here, not a risk, and Prop-13 stickiness makes the GO levy base structurally resilient to an AI/tech drawdown.

---

## b. Issuer + pledge verification (EMMA Official Statement)

**Claim:** Unlimited ad-valorem GO with an SB-222 statutory lien, tax-exempt.
**How verified:** Pulled the EMMA Security/Details page for 357172ZT5 (disclaimer-gated), bound the CUSIP to EMMA issue **EP379545** = "General Obligation Bonds, Series 2019A," and downloaded the Official Statement PDF (`raw/official_statement.pdf`, 4.3 MB).
**Authority:** Official Statement, "Security and Source of Payment for the Bonds" (p. 14).
**Finding — VERIFIED.**

- *Unlimited ad-valorem.* "The Board of Supervisors of the County is empowered and is obligated to levy ad valorem taxes upon all property subject to taxation by the District… **without limitation as to rate or amount**" — proceeds deposited in a County-maintained Interest and Sinking Fund "used solely for the payment of the bonds of the District."
- *SB-222 statutory lien.* Confirmed verbatim: Govt Code §53515 (effective 2016) creates an automatic statutory lien on all tax revenues levied/collected, "valid and binding from the time the bonds are executed and delivered," effective without recordation.
- *Additional Resolution pledge* of all property-tax revenues and Interest-and-Sinking-Fund balances, "in addition to any statutory lien."
- *Tax status.* Orrick opinion: interest excluded from federal gross income (§103), not an AMT preference item, exempt from CA personal income tax. EMMA "Tax Status" = Tax-Exempt. **Not a federally-taxable bond** (the taxable-gate signature — odd 3-decimal coupon near par — does not apply; this is a clean 4.000% tax-exempt). VERIFIED.
- *Not a County obligation:* "The Bonds… are not a debt or obligation of the County." Standard for CA school GOs — the County is the levy/collection agent, not the obligor.

This is the cleanest pledge type in the CA muni universe: a voter-approved unlimited-rate ad-valorem levy on a very large, diversified tax base, ring-fenced from operating funds, with a statutory lien.

---

## c. Assessed-value base + taxpayer concentration + the Silicon-Valley / Prop-13 nuance

**AV base (OS, 2018-19):** District total assessed value **$75.77B** ($71.29B local secured + $4.48B unsecured; utility $0). AV grew every year shown except a −0.6% blip in 2010-11 (post-GFC), with +6–9.5% prints through the 2010s. *Authority: OS, "Assessed Valuation of Secured and Unsecured Property."*

**Current AV (cross-check):** Santa Clara County's countywide 2025-26 assessment roll closed at **$725.7B, +4.15%** — the slowest growth since 2012, but still positive (Santa Clara County Assessor, roll-close 2025-26). FUHSD's own AV today is materially above the 2018-19 $75.8B baseline; the District remains one of the wealthiest tax bases per pupil in California.

**Taxpayer concentration — the key test of the "tech-wealth AV" framing (OS, "Largest Taxpayers"):**

| Rank | Taxpayer | Use | 2018-19 AV | % of secured |
|---|---|---|---|---|
| 1 | Google Inc. | Office | $1.65B | **2.32%** |
| 2 | Apple Computer Inc. | Office | $1.18B | 1.66% |
| 3 | Campus Holdings Inc. | Office | $1.09B | 1.52% |
| 4 | Lockheed Missiles & Space | Industrial | $0.89B | 1.25% |
| 5 | Yahoo Holdings | Office | $0.66B | 0.92% |
| … | (6–20: Juniper, Applied Materials, Intuitive Surgical, Agilent, etc.) | | | |
| | **Top-20 combined** | | **$11.31B** | **15.86%** |

**Finding — concentration is LOW and the OS says so explicitly:** "**No single taxpayer owns more than 2.32%** of the local secured taxable property." Even the marquee tech names (Apple, Google) are each ≤2.3% of the base; the top 20 together are under 16%. The `top_taxpayer_concentration` detector does **not** fire — this is a granular, residential-heavy base in which Apple Park/Google campuses are *additive diversifiers*, not single points of failure.

**The second-order tech/AI-crash question (addressed honestly):**

The AI-insulation screen (99) is built on the *state* channel: CA's General Fund is ~⅔ personal income tax, heavily capital-gains-driven, so a tech/AI crash hits *state* revenue hard (dot-com precedent: −71% capital-gains revenue). School-GO debt service is levied locally on AV and is insulated from that state channel. The legitimate second-order worry the prompt raises is whether a deep tech drawdown could erode the *local AV base itself*, since this base is tech-wealth-driven. Three points, honestly weighed:

1. **Prop-13 stickiness is the dominant mechanism.** AV resets to market only on **change of ownership or new construction** (Article XIIIA). Absent a sale, AV rises at the lesser of CPI or 2%/yr regardless of market value. So a paper decline in Silicon Valley home/office *market* values does **not** mechanically lower the AV roll. The only downward path is a **Prop-8 (1978) temporary "decline-in-value" reduction**, which a property owner must *apply for*, which the assessor grants only when current market value falls **below the property's existing (often deeply-below-market) Prop-13 base**. For long-held tech campuses and homes carrying base years from the 1990s–2010s, market value would have to fall enormous distances to pierce the base — Prop-8 relief is a real but **shallow and self-reversing** ("recapture") channel, not a cliff. The OS documents both the Prop-8 mechanism and the *County of Orange* recapture ruling that lets the assessor restore value faster than 2%/yr once markets recover.

2. **GO debt service is not AV-level-sensitive in the way operating revenue would be — it is rate-elastic.** The levy is sized each year to cover scheduled debt service; if AV *fell*, the County would simply *raise the unlimited ad-valorem rate* to collect the same dollars (the OS spells this out: a destruction-of-value event "necessitates a corresponding increase in the annual tax rate"). With direct GO debt at **0.54% of AV**, there is enormous headroom — AV could fall by half and the required rate would still be trivial. Bondholder risk from an AV decline is therefore minimal absent mass *delinquency*, not mass *revaluation*.

3. **This is a *community-funded (basic-aid) district*** — the strongest insulation fact in the file. FUHSD has been basic-aid "for over 25 years"; in 2018-19 its local property-tax revenue **exceeded its LCFF entitlement by ~$35M**, so it receives essentially no state apportionment for operations. That means (a) the District's *operating* credit is also insulated from the state cap-gains channel (it lives on local property tax, not Sacramento), and (b) even in a state-budget crisis driven by an AI crash, FUHSD's revenue stream is structurally different from a typical LCFF-dependent district. The AI-insulation screen (99) is, if anything, *understated* for the operating side.

**Net:** The "tech-wealth AV" characteristic is correctly read as a **positive** for this credit. The honest residual risk is a Prop-8 wave in a severe, *sustained* Bay Area real-estate repricing (a 2008-style event concentrated on recently-transacted, high-base-year tech properties), which could shave the roll a few points and require a modestly higher levy rate — comfortably absorbed at 0.54% direct debt/AV. The commercial-real-estate softness already visible (county roll growth at a 13-year low of 4.15%) is the thing to monitor, not a thesis-breaker.

---

## d. Debt-to-AV + overlapping debt

*Authority: OS, "Direct and Overlapping Debt," ratios to 2018-19 AV.*

| Metric | Amount | % of 2018-19 AV |
|---|---|---|
| **District direct GO debt (5/1/19)** | $412,210,088 | **0.54%** |
| Total direct + overlapping tax & assessment debt | $1,414,731,182 | 1.87% |
| Gross combined total debt | $1,685,147,335 | 2.22% |
| Net combined total debt | $1,633,163,835 | 2.16% |

- **Direct GO leverage of 0.54% of AV is exceptionally conservative** — well inside the comfort zone for a CA school GO (many AAA peers run 1–2.5%). The District is 100%-applicable for its own $412M; the rest of the "overlapping" stack is community-college, county, and city debt shared across a much larger footprint.
- **Coincidental-number caution:** the screen's "EQ Ss 1.87" (seismic) and the OS's "1.87% total direct+overlapping debt/AV" are *unrelated* metrics that happen to share the digits — do not conflate.
- *Second-order link to (c):* because direct debt/AV is 0.54%, the levy rate needed to service the bonds is tiny, so even a Prop-8-driven AV decline translates into a negligible rate increase for taxpayers — low risk of a tax-revolt / delinquency feedback loop.

---

## e. AB-1200 certification + enrollment (Santa Clara COE)

**Claim:** AB-1200 POSITIVE.
**How verified:** OS certification-history statement + the District's current FY2025-26 Adoption Budget filed on EMMA (`raw/continuing_disclosure_latest.pdf`, dated 2025-06-17), under the jurisdiction of the **Santa Clara County Superintendent of Schools**.
**Finding — VERIFIED / CONSISTENT.**

- OS: "In the last five years, the District has **not** received a negative or qualified certification for an interim financial report." (AB-1200 assigns positive / qualified / negative; FUHSD has stayed positive.)
- The FY2025-26 budget passed the County's criteria-and-standards review; the District's combined ending fund balance is **~$59.2M** (general fund, unrestricted + restricted), with the unrestricted component ~$37.8M — healthy reserves for a ~$165M+ operating district.
- **Enrollment / ADA:** FY2025-26 funded ADA ~**9,250**, regular ADA ~8,933 (vs ~11,051 enrollment cited in the 2019 OS — a multi-year decline typical of expensive Bay Area districts as families age out / are priced out). *Honest flag:* the budget's fiscal-indicator screen acknowledges declining enrollment as a watch-item. **But for a community-funded district this is far less of a credit concern** than for an LCFF district, because revenue tracks *property tax*, not per-pupil ADA — enrollment decline does not cut the District's funding the way it would elsewhere. And it is fully irrelevant to GO debt service, which is levied on AV.

---

## f. Call schedule

*Authority: OS, "The Bonds — Redemption."*

- **Optional redemption:** Series 2019A maturities **on/after 2038… i.e. those maturing on or after 2028** are callable **at the option of the District, on any date on/after 2027-08-01, at 100% of par (no premium)**, plus accrued interest. Maturities on/before 2027-08-01 are non-callable.
- Our bond (2038-08-01) **is** subject to this par call from 2027-08-01.
- **Economic read:** at the current discount price (98.82), the par call is *out of the money* — it would never be optimal for the District to call at 100 a bond trading below 100. Yield-to-call (5.10%) > yield-to-maturity (4.124%), so **yield-to-worst = yield-to-maturity = 4.124%**. The call is benign at today's price; it would only matter if the bond moved to a premium (rates fall well below 4%), in which case YTW would shift to the 2027 call. EMMA's reported YX of 4.122% is, in this discount case, the yield-to-maturity (the worst case), consistent with our independent computation.
- *Sinking fund:* the OS describes mandatory sinking-fund redemption for a separate $29.85M **2046 term bond** — not our 2038 serial maturity.

---

## g. Trade tape + liquidity

*Authority: EMMA RTRS trade tape for 357172ZT5 (`raw/trade_tape_357172ZT5.json`, 283 reported trades, 2019-05-16 → 2026-03-26).*

- **Liquidity: adequate-to-good for a small school-GO maturity.** 98 distinct trade days over the bond's life; **16 distinct trade days in the trailing 12 months**; a **$6.01M block has printed**; two-sided (customer buy + customer sell + inter-dealer) prints recur. Passes the liquidity gate comfortably for an HTM ladder position.
- **Price/yield trajectory:** traded ~101 (≈3.3% YX) through Oct 2025, then repriced down to **98.82 / ~4.12%** by late Feb–Mar 2026 as the curve backed up — a rate move, not a credit move (consistent with AAA spread stability; no material event in the continuing-disclosure stream).
- **Staleness flag (honest):** the most recent print is **2026-03-26** — roughly 3 months before cutoff. The "last px ~98.82" is that March print, **not a live two-sided quote**. Per our standing note, the IBKR muni feed is close-only; treat 98.82 as indicative. Re-confirm an executable level before adding. At 98.82 the YTM is 4.124% / TEY ~8.29%, which is the basis for the screen's ~8.2% tag and is fairly rich for a AAA CA GO of this duration (≈9.4-yr mod duration) — attractive entry if the level holds.

---

## h. Risk register + verdict

**Overlay screens (re-grounded against primary sources):**

| Screen | Tag | Adjudication |
|---|---|---|
| AB-1200 | POSITIVE (Santa Clara) | **VERIFIED** — 5-yr clean certification history; healthy reserves. |
| AI insulation | 99 | **VERIFIED and arguably understated** — school-GO levy is off the state cap-gains channel, *and* the District is community-funded (operating revenue is local property tax too). |
| Tech-wealth AV second-order | (review) | **Addressed (c):** Prop-13 stickiness + 0.54% debt/AV + rate-elastic levy make this resilient; residual = a severe sustained Prop-8 wave. Monitor CRE softness (county roll growth at 13-yr low). |
| Fire | 4% tail | Low. Suburban Sunnyvale/Cupertino built-out footprint; not a wildland-interface AV base. No action. |
| Flood | 61% tail (REVIEW) | Acknowledged. For a GO secured by an unlimited ad-valorem levy on a $75.8B+ diversified base, localized flood exposure to a fraction of parcels is not a debt-service threat — the levy is rate-elastic and the base is enormous. Anti-masking note: no flood carve-out or special-district masking observed. Monitor, do not block. |
| Earthquake (Ss 1.87) | moderate — Bay / San Andreas N / Hayward | Real physical hazard (Hayward fault proximity). Credit channel is the OS "destruction by earthquake → AV reduction → higher levy rate" path; with 0.54% debt/AV the rate cushion is vast. Bondholder loss would require simultaneous mass destruction *and* mass delinquency — remote for a AAA base. Do not confuse the seismic "1.87" with the debt "1.87%." |
| Top-taxpayer concentration | — | **Does not fire.** Largest taxpayer 2.32%; top-20 = 15.86%. |
| Taxable-muni gate | — | **Clean.** Confirmed tax-exempt (Orrick); not a federally-taxable harvest artifact. |

**What would change the verdict (disconfirming watch-list):**
- A County roll *decline* (not just slowing growth) driven by a Bay-Area CRE/tech repricing + a measurable Prop-8 appeal wave concentrated in FUHSD TRAs.
- A slip from POSITIVE AB-1200 certification or a sharp reserve drawdown in future budgets (none in the current file).
- Accelerating enrollment decline *combined with* loss of community-funded status (would take an extreme AV collapse — ~$35M/yr cushion).

**Verdict: BUY (hold/add on confirmed level).** Highest-quality pledge type (unlimited ad-valorem GO + SB-222 lien), AAA/Aaa, community-funded Silicon Valley district, direct debt 0.54% of a ~$75.8B+ diversified base with no taxpayer >2.3%, AB-1200 positive, adequate liquidity. The marketed "tech-wealth AV" is a genuine strength, not a hidden risk — and the honest second-order AI-crash channel (local AV erosion) is structurally muted by Prop-13 stickiness and an enormous levy-rate cushion. The only caveats are operational, not directional: (1) the 98.82 print is ~3 months stale — re-confirm an executable level; (2) at ~8.3% TEY this is fairly rich, so it is an attractive add only if the level holds.

---

### Documents (all absolute paths)
- `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/357172ZT5/DD_REPORT.md` (this report)
- `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/357172ZT5/raw/official_statement.pdf` (EMMA OS, Series 2019A/B/C, issue EP379545)
- `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/357172ZT5/raw/official_statement.txt` (extracted text)
- `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/357172ZT5/raw/continuing_disclosure_latest.pdf` (FY2025-26 Adoption Budget, 2025-06-17 — AB-1200/reserves/ADA)
- `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/357172ZT5/raw/continuing_disclosure_latest.txt`
- `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/357172ZT5/raw/trade_tape_357172ZT5.json` (283 RTRS trades)
- `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/357172ZT5/raw/emma_security_details_357172ZT5.html` (EMMA Security/Details, ZT5)

*Primary sources: MSRB EMMA (Security/Details, Official Statement, RTRS trade tape, continuing disclosure); Santa Clara County Assessor (2024-25 / 2025-26 roll-close). Bond analytics validated against EMMA reported yield to ±0.002. Cutoff 2026-06-20.*
