# Diligence Report — CUSIP 010824MD9

**Alameda City Unified School District (Alameda County, CA) — Election of 2014 GO Bonds, Series C, 3.00% term due 2042-08-01**

Cutoff: 2026-06-20 · Prepared by SignalOS (muni_credit) · Status: in buy book

| | |
|---|---|
| CUSIP | 010824MD9 (base 010824, suffix MD9) |
| Issuer | Alameda City Unified School District (the City-of-Alameda K-12 district — an island in SF Bay) |
| Issue | $62,500,000 Election of 2014 General Obligation Bonds, Series C |
| This maturity | $18,355,000 3.000% **Term** Bond due 2042-08-01 |
| Security | Unlimited ad-valorem GO + Gov't Code §53515 statutory lien |
| Tax status | Tax-exempt (federal + CA personal income tax) |
| Ratings (at issuance) | Moody's Aa2 / S&P AA |
| Dated / delivered | 2019-08-29 |
| Originally offered | price 102.773, yield 2.610% |
| Last reported trade (tape) | 2026-05-19 bid 79.27 (4.86% YTW); last offer 81.41 (5/14) |

**One-line verdict: BUY (small, patient, limit ~81 or better) — clean unlimited-GO credit on a deeply diversified, low-leverage island tax base; risks are honestly geographic (Bay flood / Hayward seismic) and tax-technical (deep-discount = ordinary-income market discount), not credit-masking.**

---

## a. Security, pledge and issuer identity (VERIFIED — primary source)

**Claim:** Unlimited ad-valorem GO of Alameda Unified, tax-exempt, with an SB-222 statutory lien.
**How verified:** Read the actual Official Statement (saved to `raw/official_statement.pdf`, 196 pp; text in `raw/os.txt`). Confirmed the exact CUSIP on the inside cover.
**Authority:** OS cover + maturity schedule + "Statutory Lien" section.
**Finding: VERIFIED.**

- Inside cover, line 94: *"$18,355,000 — 3.000% Term Bonds due August 1, 2042 — Yield: 2.610% — Price: 102.773; CUSIP Suffix: MD9"* under Base CUSIP **010824**. This is the exact security.
- Pledge (cover): *"The Bonds are general obligations of the District payable solely from the proceeds of ad valorem property taxes. The Board of Supervisors of Alameda County is empowered and obligated to annually levy such ad valorem property taxes, **without limitation as to rate or amount** … upon all property within the District."* — true **unlimited-tax** GO.
- Statutory lien (OS "Statutory Lien"): *"Pursuant to **Government Code Section 53515**, the Bonds will be secured by a statutory lien on all revenues received pursuant to the levy and collection of ad valorem property taxes… The lien automatically attaches… and is valid and binding from the time the Bonds are executed and delivered."* §53515 is the lien created by **SB 222 (2015)** — claim confirmed under its proper statutory name.
- Tax status (OS bond-counsel opinion): interest (and OID) **excluded from federal gross income, not an AMT preference item, and exempt from California personal income tax.** Tax-exempt confirmed.
- Paying agent: U.S. Bank N.A.; book-entry via DTC.

**Identity disambiguation (the requested check):** This is **Alameda *City* Unified School District** — the K-12 district covering the City of Alameda (the island), legal name "Alameda City Unified School District (Alameda County, California)." It is **NOT Alameda County** and **NOT** the county Office of Education. The 1% county-wide levy and the County GO line are separate overlapping entities (see §b tax-rate table). Base CUSIP 010824 maps to this district (confirmed via OS cover and EMMA issuer record).

**One caveat to flag honestly:** the §53515 lien also secures *all other* District GO bonds issued after Jan-2016 on a **pari passu, unallocated** basis — *"The statutory lien provision does not specify the relative priority of obligations so secured or a method of allocation."* This is standard for CA school GO statutory liens and not a defect, but it means newer Measure B (2022) GO bonds share the same lien.

---

## b. Tax base — AV, concentration, leverage (VERIFIED, with a freshness caveat)

**Authority:** OS "Tax Base for Payment of Bonds" tables (California Municipal Statistics, Inc.), FY2018-19 roll. *Freshness caveat below.*

**Assessed valuation (the security):**
- FY2018-19 total AV: **$13,543,528,162**, up from $9.36B in FY2009-10 — a 10-year CAGR of ~3.8% with **no down years except a trivial −0.79% in 2010-11**. Through the dot-com and 2008 stress the Alameda roll barely moved; Prop-13 acquisition-value assessment makes the base extremely sticky.
- This bond series at issuance was $62.5M against a $13.5B base. **AV/par for this single series ≈ 740×** — overwhelming coverage of the levy.

**Taxpayer concentration — excellent (granular residential base):**
- 21,273 parcels; **84% of AV is residential** (single-family 54%, condo/townhouse 12%, 2-4 unit 8%, 5+ unit/apartments 9%); only 16% non-residential.
- **Top taxpayer = 1.78%** (BRE Alameda I, an apartment owner). **Top 20 = 10.58%** combined. No single anchor employer or one-plant exposure; the largest names are apartment REITs and the Alameda Towne Centre shopping center. This is among the most diversified school-GO bases in the state.

**Leverage — conservative:**
- Direct debt-to-AV at issuance: **1.11%**; combined direct **1.15%**; total direct + overlapping (incl. tax-increment) **2.81%**. All well inside investment-grade school-GO norms (<3-4%).

**Freshness caveat (honest):** the AV, taxpayer, and leverage figures above are from the **2019 OS (FY2018-19 roll)**. For a 2026 cutoff this is stale. I attempted to pull the District's most recent annual continuing-disclosure (which carries the current AV) from EMMA — the document endpoint **rate-limited (HTTP 520/403)** today and I would not fabricate a current AV. Directional read from independent sources: the City-of-Alameda roll has continued to grow (Alameda County roll has set records each year since 2019; Alameda is a supply-constrained, high-demand Bay island), and the District issued **Measure B (2022, $298M authorization; Series A/B 2024-25, base CUSIP 010824)** which *adds* direct debt — so current direct-debt-to-AV is somewhat higher than the 1.11% above but, against a materially larger AV, almost certainly still in the low-single-digit-% range. **Treat current AV/leverage as CONSISTENT-but-not-re-verified**, not VERIFIED. Recommend a one-line refresh from the next annual report when EMMA's doc endpoint is not throttled.

---

## c. AB-1200 fiscal certification + enrollment (the operating layer)

**AB-1200 (Alameda County):** The screen flags **AB-1200 POSITIVE** for the Alameda County Office of Education's certification of the District. A "Positive" certification means the County Superintendent finds the District **will meet its financial obligations** for the current and two subsequent fiscal years — the strongest of the three AB-1200 tiers (Positive / Qualified / Negative). This is the correct, expected status for an Aa2/AA island district and I treat it as **CONSISTENT** (the certification is a county-issued operating-solvency opinion; I did not independently re-pull the latest interim certification letter, which lives in the County COE filings).

**Enrollment:** ~**10,771 (2024-25)** and ~**10,781 (2025-26)** per CDE/EdData — essentially flat the last two years. Statewide CA districts (and AUSD's own officials) cite **declining-enrollment** budget pressure post-COVID, and AUSD is not immune.

**Why this is a second-order risk for THIS bond (important):** enrollment drives the *operating* general fund via LCFF/ADA funding. It does **not** secure the GO bonds. The GO debt-service pledge is the **unlimited ad-valorem levy on the $13.5B+ property base**, which the County is obligated to set at whatever rate is needed to pay principal and interest — completely independent of how many students enroll. Declining enrollment would have to go so far as to trigger District insolvency/dissolution to threaten bondholders, and even then the statutory lien on the tax levy survives. So enrollment is a monitoring item for operating credit, not a debt-service risk. **Not a masking finding.**

---

## d. Call schedule (VERIFIED — primary source)

**Authority:** OS "Redemption" section.

- **Optional redemption:** maturities on/before 2027-08-01 are non-callable; maturities on/after 2028-08-01 are **callable at par (no premium) on 2027-08-01 or any date thereafter**, from any source of funds, in whole or part. This 2042 term bond is therefore **currently callable at 100 from 2027-08-01**.
- **Mandatory sinking fund:** the 2042 term bond amortizes 2040 ($5.62M) / 2041 ($6.11M) / 2042 maturity ($6.625M), at par, no premium.

**Practical effect:** the par call is deeply out-of-the-money at today's ~80 dollar price (a 3% coupon bond will not be refunded at par when it trades 19 points below par), so yield-to-worst is the **yield-to-maturity** (2042), and the deep discount means call risk is effectively nil. Confirmed by the math: YTC-to-2027 computes to ~17% (i.e., the call is irrelevant; YTW = YTM).

---

## e. Trade tape — liquidity and the REAL current level (VERIFIED — RTRS)

**Authority:** MSRB RTRS reported-trade tape for 010824MD9 (625 prints; saved to `raw/trade_tape.json`). Note: EMMA's reported "yield" (YX) is **MSRB yield-to-WORST**, not YTM — labeled accordingly.

**Material correction to the screen.** The stated "last px ~86.18 / TEY ~8.2%" is **stale** — that 86-handle was a **February 5, 2026** level. The tape has since sold off:

| Date | Type | Price | YTW | Par |
|---|---|---|---|---|
| 2026-05-19 | bid (purchase-from-cust) | **79.27** | 4.86% | $45k |
| 2026-05-15 | bid | 81.25 | 4.66% | $20k |
| 2026-05-14 | **offer (sale-to-cust)** | **81.41** | 4.64% | $20k |
| 2026-02-05 | offer | 88.33 | 3.97% | $25k |
| 2025-12-04 | bid | 82.09 | 4.54% | $25k |
| 2025-06-26 | offer | 77.20 | 5.00% | $50k |

**Honest current picture:** the realistic **acquirable level is ~81 (last customer offer 81.41, 5/14)**, with a dealer **bid ~79.3** — a wide **~2-point bid/ask**. The bond is *cheaper* than the 86.18 the screen carried, which improves yield (see §f) but the stale anchor must be corrected.

**Liquidity — thin (gate-relevant):** trailing-12-month tape = **7 distinct trade days, 8 customer-facing prints, only 1 two-sided day**, all in $10k-$50k lots. This **fails a tight liquidity gate**. Implication: this is a buy-and-hold-to-maturity (HTM) name; expect to pay ~1-2 points of spread on entry, do it in small clips with a limit, and do not assume you can exit at the bid in size. For an HTM ladder the one-time spread is a ~10-15 bps/yr drag over the 16-yr hold — tolerable, but size the position accordingly.

---

## f. RISK LEAD — Bay-island flood, Hayward seismic, and the deep-discount tax trap

These are the decisive items and are led here per the geography.

### f.1 Bay-island coastal / sea-level-rise flood (REVIEW — honest treatment)
- Alameda is a **low-lying reclaimed island** in San Francisco Bay; large portions (Bay Farm Island, the former Naval Air Station / Alameda Point, harbor-edge neighborhoods) sit at low elevation behind levees/seawalls and are in FEMA coastal-flood and projected sea-level-rise inundation zones. The screen's **flood tail 83%** is honest: real, but **below the 90% within-CA hard-tail** — it is a *review*, not an *exclude*.
- **The channel that matters for a GO bond is the tax base, not bondholder property damage.** Two transmission paths:
  1. **Insurer-withdrawal / AV channel:** if California's coastal/flood insurance availability deteriorates (as wildfire insurance already has statewide), financing and resale of low-lying parcels gets harder, which can soften assessed values and new-construction additions over a multi-decade horizon. Over a **16-year hold to 2042**, partial SLR/king-tide exposure is a genuine slow-burn drag on AV growth — though Prop-13's acquisition-value floor means existing AV is very sticky downward.
  2. **Catastrophe channel:** the OS itself names *"complete or partial destruction of taxable property caused by a natural or manmade disaster, such as earthquake, flood, fire…"* as an AV-reduction risk that would **raise the levy rate** (the unlimited pledge re-rates to cover debt service), not impair the pledge directly.
- **Mitigants:** Alameda's flood exposure is partial (the island core and much of the residential roll are not in the worst inundation cells); the City and regional agencies (e.g., adaptation planning at Alameda Point) are actively engaged; and the unlimited levy plus 740× AV/par coverage means even a meaningful AV haircut is absorbed by a higher rate. **Net: a legitimate REVIEW-grade, long-horizon AV-growth risk — surfaced honestly, not disqualifying for an unlimited-GO HTM hold. Monitor CA coastal-insurance availability and the next AV roll for the low-lying TRAs.**

### f.2 Hayward fault seismic (moderate)
- Screen **EQ Ss 1.77** (moderate-high spectral acceleration) reflects proximity to the **Hayward fault**, one of the Bay Area's highest-probability major-rupture faults. A large Hayward event could damage Alameda's older housing/soft-story and bayfront stock and temporarily depress AV (Prop-8 declines), again **re-rating the levy upward** rather than impairing the pledge.
- **Same structural mitigant as flood:** the security is the levy on the whole base, and Alameda County's roll is enormous relative to this single levy. Seismic is a real-property/AV-volatility risk, not a debt-service-priority risk. Moderate, not severe.

### f.3 Deep-discount de-minimis / market-discount tax (the most-actionable finding)
**This corrects an overstatement embedded in the "TEY ~8.2%" headline.**

- A muni bought in the secondary market below the **de-minimis threshold** = 0.25% × full years to maturity, in points below par, has its discount taxed as **ordinary income** (market-discount accrual under IRC §1276), **not** tax-exempt and **not** capital gain.
- Years to maturity from settlement ≈ 16 → de-minimis cutoff = 0.25 × 16 = **4.00 points → price floor 96.00.**
- At **86.18** the discount is **13.8 pts**; at the realistic **81.4** offer it is **18.6 pts** — *far* below the 96 floor. **The entire market discount is taxed as ordinary income on accretion/sale.**
- **Because this is a California bond, the market discount is also NOT exempt from CA tax** (CA exempts the *interest* on CA munis, not market-discount gain). So the discount is taxed at roughly the top combined fed+CA ordinary rate (~50%).

**What this does to the "TEY":**

| Level | YTM (to 2042) | Naive full-exempt TEY (×2.01) | **Honest TEY** | Mod. duration |
|---|---|---|---|---|
| 86.18 (stale) | 4.19% | 8.42% | **~8.0%** | 12.2 |
| **81.41 (current offer)** | **4.65%** | 9.35% | **~8.8%** | 12.0 |
| 79.27 (current bid) | 4.87% | 9.79% | ~9.2% | 11.9 |

- The **naive full-exempt gross-up overstates the tax-equivalent yield** because it treats the whole YTM as tax-exempt. Only the **3.00% coupon** is exempt (current yield ≈ 3.7% on an ~81 cost); the ~1 point/yr of discount accretion is **ordinary-taxable**. The "honest TEY" column grosses up only the exempt coupon and adds the discount at its pre-tax accretion value.
- **Net practical read:** the *credit* is fine and the bond is *cheaper* than the screen implied (good for entry), but a buyer should underwrite this to an **after-tax YTM of ~3.7%** (not a tax-free ~4.7%), and the "~8.2% TEY" tag should be read as the honest ~8.0-8.8%, **with the explicit understanding that a large slice of that return is ordinary-income-taxed market discount, not tax-exempt coupon.** Mod duration ~12 means ~12% price move per 100 bps — meaningful rate risk on a 16-yr hold.

---

## g. Honesty-alpha read (takeaway-vs-data)

- **No credit masking detected.** This is a genuinely clean, conservatively-leveraged, deeply-diversified unlimited-GO on a wealthy supply-constrained island, with an Aa2/AA profile and a statutory lien. The OS discloses its geographic risks (it explicitly names earthquake/flood as AV risks) — honest disclosure, not a polished story diverging from its data.
- **The only takeaway-vs-data divergences are in OUR screen, and they cut both ways:**
  1. **Stale price (negative for the headline, positive for entry):** the "86.18 / 8.2% TEY" was a February level; the bond is now ~81 offer / 79 bid. The screen anchored on a 4-month-old print.
  2. **Overstated TEY framing (negative):** the deep-discount de-minimis ordinary-income treatment means the tax-equivalent yield is lower than a naive full-exempt gross-up implies, and a chunk of the return is taxable. This is the honesty-correction.
- These are *our* framing items to correct, not issuer dishonesty. Grade: **CLEAN issuer; correct the screen's price anchor and TEY label.**

---

## h. Verdict and actions

**VERDICT: BUY** — small, patient, limit-driven (target ~81 or better; do not chase above ~82 given the wide spread), buy-and-hold-to-maturity.

Rationale: clean unlimited-ad-valorem GO with a §53515 statutory lien on a $13.5B+, 84%-residential, top-20-only-10.6% tax base levered at ~1.1% direct; Aa2/AA; AB-1200 Positive. The risks are honest and structural, not credit-masking: (i) Bay-island flood/SLR and (ii) Hayward seismic are **AV-volatility/levy-re-rating** risks the unlimited pledge is designed to absorb, not pledge-priority risks; (iii) the deep discount is a **tax-character** issue (ordinary-income market discount, ~50% taxed, lowering after-tax yield to ~3.7%) and a **rate-risk** issue (duration ~12), not a credit issue. The name is **thinly traded** — size small, use limits, expect to hold.

**Conditions / monitoring:**
1. Refresh **current AV + direct-debt-to-AV** from the District's latest annual continuing disclosure once EMMA's doc endpoint is not rate-limited (today's CONSISTENT-not-VERIFIED item).
2. Underwrite to **after-tax YTM ~3.7%**, not the headline tax-free TEY; the screen's "8.2% TEY" should display as honest ~8.0-8.8% with the ordinary-income market-discount caveat.
3. Monitor **CA coastal/flood-insurance availability** and the low-lying-TRA AV trend (Alameda Point / Bay Farm) as the multi-decade SLR-AV channel.
4. Correct the stored "last px 86.18" to the live tape (~79 bid / ~81 offer, 5/2026).

---

### Documents (all absolute paths)
- Official Statement (primary, $62.5M Series C, 2019): `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/010824MD9/raw/official_statement.pdf`
- OS extracted text: `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/010824MD9/raw/os.txt`
- RTRS trade tape (625 prints): `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/010824MD9/raw/trade_tape.json`
- This report: `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/diligence_reports/010824MD9/DD_REPORT.md`

### Source authorities
- Pledge / lien / call / tax status / AV tables / taxpayers / debt ratios: 2019 OS (EMMA, Stradling Yocca Carlson & Rauth bond counsel; tables by California Municipal Statistics, Inc.).
- Trade tape: MSRB RTRS via EMMA Security/Details/010824MD9 (YX = yield-to-worst).
- Enrollment: CDE / EdData (10,771 in 2024-25; 10,781 in 2025-26).
- Yield/duration/de-minimis math: `compute_bond_analytics.py` (validated to EMMA ±0.003 per reference).
