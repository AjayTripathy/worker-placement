# Diligence Report — CUSIP 697479CB7

**Palo Verde Community College District (Riverside & San Bernardino Counties, CA)**
Election of 2014 General Obligation Bonds, Series A — 4.00% due 08/01/2045

Prepared: 2026-06-18 (cutoff = today) | Status: BUY-eligible, our highest-yield top pick
Last price ~95.3 | Last trade yield-to-worst ~4.33% | After-tax taxable-equivalent yield ~8.71% | Buy limit 95.93

---

## (a) Verdict & thesis

**VERDICT: BUY — confirmed clean, highest-yield pick. The ~8.71% taxable-equivalent yield is real, not distress.**

The headline yield comes from three honest, verifiable sources, none of which is a credit problem:

1. **A discount dollar price (~95.3) on a low 4% coupon.** A 4% coupon bond with ~19 years left naturally trades below par in today's rate environment. The discount is a coupon/rate artifact, not a credit markdown — the bond was issued at a premium (103.856% / 3.55% yield in 2016) and has simply repriced with the broad move in long rates.
2. **Genuine double tax exemption.** Interest is exempt from both federal income tax and California personal income tax (confirmed by bond counsel opinion in the Official Statement). For a top-bracket California buyer that grosses a ~4.33% tax-free yield up to roughly an 8.7–9.4% taxable-equivalent — the high end of our top 5.
3. **A small, thinly-traded issue.** Thin trading (the thinnest of our five picks) adds a modest illiquidity premium to the yield. That is a yield *tailwind* for a buy-and-hold ladder, not a sign of stress.

**Why this is not a distressed bond:** unlimited ad-valorem general-obligation pledge with a statutory first lien on the tax levy; light debt burden (direct GO debt = 0.20% of assessed value); a stable ~$2.1 billion tax base; the Teeter Plan, under which the District is paid 100% of its levy regardless of taxpayer delinquencies; and bond insurance from Assured Guaranty Municipal Corp. The issuer (a community college) is currently accredited with no fiscal-distress flags.

**The one finding that matters — and it is fully disclosed, not hidden:** the tax base has a single-taxpayer concentration. One natural-gas power plant (Blythe Energy LLC) is **13.5% of the District's secured assessed value**. We verified that plant is still operating in 2025. This is a real risk to monitor, but it is offset by the unlimited-tax pledge (if assessed value falls, the tax *rate* rises to cover debt service), the insurance wrap, and a light debt load. We rate it a manageable, priced risk — see Section (g).

---

## CRITICAL IDENTITY CORRECTION (read first)

Our pre-screen labeled this bond **"Palo Verde Unified School District" (the K-12 district)**. **That label is wrong.** Primary-source verification (EMMA security page + the Official Statement) confirms the issuer is:

> **PALO VERDE COMMUNITY COLLEGE DISTRICT** — Election of 2014 General Obligation Bonds, Series A (Riverside and San Bernardino Counties, California)

This is the **community-college district**, *not* the K-12 Palo Verde Unified School District, and not Palo Alto. The two districts are genuinely separate legal entities: the Official Statement's own direct-and-overlapping-debt table lists "Palo Verde Unified School District" as a *separate overlapping agency* from our issuer. The OpenFIGI name in our raw screen file ("PALO VERDE CLG DT-A" = "College District") was actually correct; the human-readable "Unified" label in `screens_and_sources.json` was the error. **All credit conclusions below are bound to the College District.** The thesis is not impaired by the correction — a community-college GO carries the same unlimited-ad-valorem property-tax security as a K-12 GO. But the AB-1200 screen note must be reinterpreted (see Section b).

---

## (b) Security & pledge

| Attribute | Finding | How verified | Authority |
|---|---|---|---|
| Issuer | Palo Verde **Community College** District | OS cover page; EMMA issue header | `raw/official_statement.pdf` p.1; `raw/emma_security_details.html` |
| Series | Election of 2014 GO Bonds, Series A ($12,500,000 new money, part of a $15,970,000 combined sale) | OS cover | `raw/official_statement.pdf` |
| Pledge | **Unlimited ad-valorem general obligation.** Counties are "empowered and obligated to levy ad valorem taxes, without limitation as to rate or amount, upon all property within the District" for debt service | OS, Security & Sources of Payment | `raw/official_statement.pdf` |
| Statutory lien | **SB-222 statutory first lien** (Gov. Code §53515, Stats. 2015 Ch. 78). Lien attaches automatically to ad-valorem tax revenues, valid from delivery, enforceable against successors/creditors without filing | OS, "General" / SB 222 section | `raw/official_statement.pdf` |
| Tax status | **Tax-exempt** — excluded from federal gross income, not an AMT preference item, and exempt from California personal income tax (bond counsel: Stradling Yocca Carlson & Rauth) | OS cover legend; EMMA "Tax Status: Tax Exempt" | `raw/official_statement.pdf`; `raw/emma_security_details.html` |
| Bond insurance | **Assured Guaranty Municipal Corp. (AGM)** municipal bond insurance policy | OS cover + Bond Insurance section | `raw/official_statement.pdf` |
| Dated / Maturity / Coupon | 04/05/2016 / 08/01/2045 / 4.00% fixed | EMMA security details | `raw/emma_security_details.html` |
| Optional redemption | Callable at **par on/after 08/01/2026** (bonds maturing on/after 08/01/2027) | OS, Redemption section | `raw/official_statement.pdf` |

**Pledge finding: VERIFIED.** Unlimited ad-valorem GO with an SB-222 statutory first lien — the strongest standard CA muni security structure. The unlimited-tax feature is the key defense against the tax-base concentration in Section (c): if a large taxpayer's assessed value falls, the county *must* raise the tax rate on remaining property to make debt service whole.

**Ratings (at issuance, 2016):** insured **"AA" (S&P)** on the AGM policy; underlying **"A1" (Moody's) / "A" (S&P)**. The current live rating fields on the EMMA page are loaded dynamically and were not captured in the saved static HTML — **current ratings are UNVERIFIED in this pass** (flagged; the 2016 underlying single-A / insured double-A is the documented anchor).

**Call note:** the bond is currently callable at par. With the bond trading at a discount (~95.3), call risk is economically immaterial today — the District has no incentive to refinance a below-par 4% bond. No adjustment to thesis.

---

## (c) Issuer & tax base — a small agricultural/energy district (concentration flagged)

This is a small, rural district in the Palo Verde Valley around Blythe in far-eastern Riverside County (with a San Bernardino County portion), on the Colorado River at the Arizona line. The tax base is **agricultural and energy**, not suburban-residential.

**Total assessed value (FY 2015-16, per Official Statement): $2,136,502,590.** Five-year history is stable, no collapse:

| FY | Total AV |
|---|---|
| 2011-12 | $1,940,036,122 |
| 2012-13 | $2,001,080,911 |
| 2013-14 | $1,978,613,490 |
| 2014-15 | $2,268,176,098 |
| 2015-16 | $2,136,502,590 |

*Source: OS, "Assessed Valuations" table — `raw/official_statement.pdf`. Note: figures are 2015-16 vintage (issue era); a current-AV refresh from the District's latest continuing-disclosure annual report is recommended pre-trade but was not obtained in this pass (UNVERIFIED — see Section h).*

**Tax base by land use (FY 2015-16, local secured AV $2.03B):** Single-Family Residential 25.4%; Agricultural/Rural 17.8%; Commercial 14.7%; **Utility Roll / Power Plant 13.7%**; Mobile Home/Lots 11.8%; Vacant 9.2%; Industrial 1.4%. This is an ag/energy economy, not a bedroom community.

**SINGLE-TAXPAYER CONCENTRATION — the material finding:**

| Rank | Taxpayer | Use | AV | % of secured AV |
|---|---|---|---|---|
| 1 | **Blythe Energy LLC** | **Power Plant** | $275,462,000 | **13.54%** |
| 2 | Purple Verbena | Agricultural | $31,695,277 | 1.56% |
| 3 | Gila Farm Land | Agricultural | $24,428,662 | 1.20% |
| 4 | CO River Basin Farms | Agricultural | $23,120,406 | 1.14% |
| 5 | NextEra Blythe Solar Energy Center LLC | Solar Farm | $22,284,229 | 1.10% |
| — | **Top 20 total** | — | $530,266,775 | **26.07%** |

*Source: OS, "20 Largest Local Secured Taxpayers" — `raw/official_statement.pdf`.*

Roughly **one in seven dollars** of the secured tax base is a single gas-fired power plant, and the top 20 names are over a quarter of it. For a small district this is a genuine concentration. **We verified the asset is a going concern:** Blythe Energy (the ~520 MW natural-gas station) was still generating in 2025 (~46.2 GWh Feb–May 2025 per Global Energy Monitor / grid data). The valley is also a growing utility-scale solar hub (NextEra Blythe Solar, Blythe Mesa Solar 485 MW under NextEra, NRG's Blythe PV), which diversifies the energy tax base over time. *Source: web search — see Section h.*

**Why this concentration does not break the thesis:** (1) **Unlimited tax pledge** — if Blythe Energy's AV dropped, the county raises the levy rate on all remaining property to cover debt service. (2) **Light debt burden** — direct GO debt is only **0.20%** of AV; combined direct debt 1.56%; gross combined total (all overlapping) 5.32% — so the dollar amount needing coverage is small relative to even a reduced base. (3) **AGM insurance** backstops timely payment. (4) **Teeter Plan** (both counties) — the District receives 100% of its levy regardless of delinquencies.

---

## (d) Three risk screens

| Screen | Reading | Interpretation |
|---|---|---|
| **AI / tech-crash insulation** | **99.2 (fully insulated)** | Debt service is paid from **local property taxes**, not the State General Fund. The state cap-gains/AI-crash channel that hits State GO does not reach this pledge. Strongest possible insulation. |
| **Wildfire** | Score 70.5; **0% high-fire tail share**; worst tract "Relatively Moderate" | Desert valley, low vegetation fuel load. No high-fire census tracts in the district. The insurance-withdrawal/AV-drag channel is essentially absent. |
| **Earthquake** | **Ss 0.36 — the lowest seismic of our top 5** | 0.2-second spectral acceleration of 0.36 g is low for inland Southern California. The earthquake-driven AV-destruction channel is the smallest among our picks. (Note: the raw screen file's "hazard_tier: HIGH" label conflicts with the low 0.36 Ss number and the prompt's read of "lowest-seismic in the top 5"; the **numeric Ss 0.36 is the authority** and is genuinely low — the "HIGH" tier string appears to be a mislabel in the screen file.) |

All three physical/macro screens are favorable, with earthquake notably the best of the five.

---

## (e) Liquidity & execution — thinnest of the five; accumulate with patience

Verified against the EMMA trade tape (`raw/emma_trade_tape.json`, 460 lifetime trades; analysis script run this session):

- **50 trades in the trailing 365 days**, across **15 distinct trading days**, **14 of them two-sided** — genuinely two-sided, not one-way dealer offers.
- **Trade mix (last 365d):** 12 customer buys, 11 customer sells, 27 inter-dealer — a real (if thin) secondary market.
- **Most recent trade: 2026-03-19** at 95.34–95.68 (yield ~4.33–4.36%). ~3 months stale as of cutoff — thin but acceptably recent.
- **Price dispersion was wide:** 88.29–99.24 over the year on small lots. This is thin-market noise on odd-lot prints, **not** a credit deterioration trend (the within-band variance here is dominated by trade-timing/lot-size, not operator signal).

**Execution guidance:** this is the **thinnest** of our five picks. The ~95.93 limit is reasonable versus the latest ~95.3–95.7 prints. Expect to **work the order patiently in small clips** rather than fill at size in one day; there is roughly one two-sided day per ~26 calendar days. For a hold-to-maturity ladder, the wide bid/ask is a one-time buy-side cost of ~1–3 bps/yr amortized — acceptable. Do not chase; let the limit sit. IBKR returned **no tradable contract** for this CUSIP (consistent with a thin muni; source pricing/execution off the EMMA tape and dealer runs, not a live IBKR quote).

---

## (f) Tax & yield — the math behind ~8.71%

- **Last trade yield-to-worst ≈ 4.33%** (tax-free), at price ~95.3. (EMMA reports trade yield as yield-to-**worst**, here measured to the par call/maturity — the correct conservative metric.)
- **Double tax-exempt** for a California resident: federal *and* California income tax free. Top-bracket gross-up (fed 37% + 3.8% NIIT + CA 13.3% ≈ 54.1% combined marginal) implies a taxable-equivalent of up to ~9.4%. The screen's **~8.71%** is a more conservative gross-up (consistent with a slightly lower blended marginal rate and/or a haircut for the market-discount tax treatment below) — and is the **highest after-tax TEY in our top 5**.
- **De-minimis check (important and favorable):** with ~19.1 years to maturity, the de-minimis threshold price is ~95.22 (par minus 0.25 pt/yr). The bond at ~95.34 trades **just above** that line — market discount ~4.66 pts vs ~4.78 pts allowed. **The de-minimis rule is NOT breached.** Therefore the accreted market discount is taxed as a **capital gain** at sale/maturity (favorable), *not* recharacterized as ordinary income. This is a meaningful tax efficiency and supports the TEY claim.
  - *Caveat:* the de-minimis cushion is thin (~0.12 pt). If you buy materially below ~95.2, the bond crosses into de-minimis territory and the discount becomes ordinary-income-taxed, which would lower the realized after-tax TEY. **Keep the execution price at/above ~95.2** to preserve capital-gains treatment. The 95.93 limit is safely on the right side of this line.

**Finding: the 8.71% TEY is real and defensible** — discount-coupon + genuine double exemption + favorable (capital-gains) discount treatment, with a thin liquidity premium on top. None of it is credit distress.

---

## (g) Risks

1. **Single-taxpayer / power-plant concentration (PRIMARY).** Blythe Energy LLC = 13.5% of secured AV; top-20 = 26%. A retirement, derating, or successful assessment appeal by the power plant would dent the base. *Mitigants:* unlimited-tax pledge (rate floats up), only 0.20% direct debt-to-AV, AGM insurance, Teeter 100%-collection, and the asset is confirmed operating in 2025 with a growing solar tax base alongside it. **Monitor:** the District's annual continuing-disclosure AV report for any drop in the Blythe Energy line or large pending appeals.
2. **Small-district enrollment volatility.** For a community college, enrollment drives **state operating apportionment** — but **not** GO debt service, which is property-tax secured regardless. The accreditation status is current (ACCJC, no concerns; next comprehensive review fall 2026). Enrollment risk is an operating-budget issue, not a bondholder-payment issue here. Low direct relevance to this GO.
3. **Stale tax-base data.** AV figures are 2015-16 (issue vintage). A current-AV pull from the latest annual disclosure is recommended pre-trade (UNVERIFIED this pass).
4. **Current ratings UNVERIFIED.** Documented anchor is 2016 underlying A1/A, insured AA (AGM). Live ratings not captured (EMMA dynamic field). AGM remains an active, investment-grade-rated insurer; underlying single-A community-college GOs of this debt profile are typically stable, but confirm before sizing.
5. **Continuing-disclosure / material-event status UNVERIFIED.** The EMMA continuing-disclosure list is AJAX-loaded and the partial-view endpoint 404'd via CUSIP in this environment. No material-event notice was *observed*, but **absence of observation is not absence of events** — this must be confirmed on the live EMMA page before trade. **UNVERIFIABLE ≠ clean.**
6. **Liquidity / execution.** Thinnest of the five; ~3-month-stale last print; wide odd-lot dispersion. Accumulate patiently with a resting limit; treat wide spread as a small one-time HTM cost.
7. **Seismic label discrepancy (minor).** Screen file tags "HIGH" tier while Ss is 0.36 (low) — treat the numeric Ss as authority; genuinely the lowest-seismic of the five.

**Net:** one real, fully-disclosed concentration risk, well-mitigated by structure; two open verification items (current ratings, continuing-disclosure) to close before execution. None of these makes the bond distressed.

---

## (h) Sources & attached documents

**Documents in `raw/`:**
- `raw/official_statement.pdf` — **Official Statement** (Palo Verde Community College District, $15,970,000 GO Bonds, dated 2016; FOS 03/17/2016), fetched this session from EMMA (`https://emma.msrb.org/ES771666-ES606276-ES1002022.pdf`). Authority for issuer, pledge, SB-222 lien, tax status, AGM insurance, AV history, taxpayer concentration, debt ratios, ratings, redemption.
- `raw/os_text.txt` — extracted plain text of the OS (for grep/citation).
- `raw/emma_security_details.html` — EMMA security page snapshot. Authority for coupon/maturity/dated/tax-status/issue identity (issuer header "PALO VERDE COMMUNITY COLLEGE DISTRICT…Series A").
- `raw/emma_trade_tape.json` — 460-trade EMMA tape. Authority for liquidity, two-sidedness, last price/yield.
- `raw/screens_and_sources.json` — pre-run screens (AI/fire/EQ, AB-1200, execution). **Note: its `issuer` field "Palo Verde Unified" is corrected to "Palo Verde Community College District" by this report.**
- `raw/cd_partial.html` — attempted continuing-disclosure fetch (returned 404; CD status remains UNVERIFIED).

**External (web) sources:**
- Palo Verde College accreditation — ACCJC institution page (`https://accjc.org/institution/palo-verde-college/`) and District accreditation page (`https://www.paloverde.edu/accreditation/`): **Accredited, no current concerns; next comprehensive review fall 2026.**
- Blythe Energy power station operating status 2025 — Global Energy Monitor (`https://www.gem.wiki/Blythe_Energy_power_station`) / grid data (`https://www.gridinfo.com/plant/blythe-energy-inc/55295`): plant operating, ~46.2 GWh Feb–May 2025.

**Verification ledger (claim → method → authority → finding):**
| Claim | Method | Authority | Finding |
|---|---|---|---|
| Issuer is Palo Verde **Unified** (K-12) | Read OS cover + EMMA header | OS p.1; EMMA HTML | **REFUTED** — it is Palo Verde **Community College** District |
| Unlimited ad-valorem GO + SB-222 lien | Read Security/Sources + SB-222 section | OS | **VERIFIED** |
| Tax-exempt (fed + CA) | Bond counsel opinion legend | OS cover; EMMA tax status | **VERIFIED** |
| Bond insured | Cover + Bond Insurance section | OS | **VERIFIED — AGM** |
| AB-1200 "POSITIVE" fiscal cert | n/a | — | **N/A — AB-1200 applies to K-12 districts, not community colleges.** Operating-fiscal proxy = ACCJC accreditation (current/clean). Re-interpret screen accordingly. |
| Tax-base concentration | Read 20-largest-taxpayers + land-use tables | OS | **VERIFIED — Blythe Energy 13.5% of AV; top-20 26%** |
| Power plant still operating | Web search | GEM / grid data | **VERIFIED (2025 operating)** |
| ~50 trades/yr, two-sided, recent | Parse EMMA tape | `emma_trade_tape.json` | **VERIFIED — 50/365d, 14 two-sided days, last 2026-03-19** |
| 8.71% TEY real, not distress; not de-minimis | Recompute YTW gross-up + de-minimis threshold | OS price/coupon; tape | **VERIFIED — de-minimis NOT breached; capital-gains discount treatment** |
| Current ratings | EMMA live field | (dynamic, not captured) | **UNVERIFIABLE this pass** — close before trade |
| Continuing-disclosure / material events | CD partial fetch | (404) | **UNVERIFIABLE this pass** — close before trade |

*Reader note: this report uses plain-language claim → method → authority → finding discipline; no detector internal labels are printed.*
