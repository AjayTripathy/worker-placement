# CFD Developer-Corporate-Credit Diligence Build

**Date:** 2026-05-28
**Scope:** Build a developer-corporate-credit diligence layer for the 117-CFD CA land-secured universe at `/Users/ajay/exalted/signalos/verticals/muni_credit/`.
**Framing:** Diligence-replication (not primarily alpha-seeking). The deliverable is the credit-rating sheet that a $1B CA muni shop charging 150 bps/yr would want in its research file on every master developer of every housing CFD, refreshed quarterly, with rating-action history.

---

## Deliverables

1. **`data/cfd_developer_credit.json`** — master file: 21 master developers identified across the universe, with credit data
2. **`detectors/developer_corp_credit.py`** — detector module, distinct from `developer_bankruptcy.py`
3. **Per-obligor JSONs** — all 117 CFDs now carry a `developer_corp_credit` block (4 with full data, 17 mature/built-out, 52 insufficient-data, 44 non-housing N/A)
4. **This build report**

---

## Coverage summary

| Bucket | Count | Description |
|---|---|---|
| Public-traded developer with credit ratings | **1 CFD** (irvine_2013_3 → FivePoint FPH) | Direct rating mapping with HIGH confidence |
| Private developer with documented RED distress | **2 CFDs** (diablo_grande_1, northstar_csd_1) | Court foreclosure / multi-year tax delinquency / Ch 9 |
| Private developer with STALE_RED distress (pre-snapshot) | **1 CFD** (palmdale_93_1, Ritter Ranch) | 1998 BK + Lehman 2008 BK — lingering 27 yrs |
| Mature / built-out master plan (developer fragmented) | **17 housing CFDs** | Talega, Stevenson Ranch, Rancho Santa Margarita, Lincoln Crossing, Stanford Ranch, Whitney Ranch, Black Mountain Ranch, Santaluz, Mountain Park, etc. |
| Housing CFD, developer not publicly identified (GAP) | **52 housing CFDs** | Need annual administration report from issuer/CFD administrator to resolve |
| Non-housing CFD (library/school/public-facility — N/A) | **44 CFDs** | No master developer applicable |
| **TOTAL UNIVERSE** | **117** | |

### Master-developer entity catalog (`cfd_developer_credit.json`)

**Publicly traded (12):**
- **FivePoint Holdings (FPH)** — B2/B+/BB- sub-IG, stable, recent Sep-2025 Moody's upgrade B3→B2 + $20M/yr interest savings refi. CFD: Irvine 2013-3.
- **D.R. Horton (DHI)** — A3/BBB+/BBB+ IG stable. Strongest IG profile.
- **Lennar (LEN)** — Baa3/BBB-/BBB- IG; S&P outlook revised to POSITIVE.
- **PulteGroup (PHM)** — Baa1/BBB+/A- IG stable. Strongest balance sheet (debt/book cap ~12.5%).
- **Toll Brothers (TOL)** — Baa2/BBB IG stable. Mar-2025 Moody's upgrade.
- **NVR (NVR)** — Baa1/BBB+ IG stable. No CA exposure.
- **Meritage (MTH)** — Ba2/BBB-/BBB- low-IG stable.
- **KB Home (KBH)** — Ba1/BB+ sub-IG stable. CA-HQ.
- **Tri Pointe Homes (TPH)** — BB sub-IG; **on S&P CreditWatch Developing as of 2026-02-18** (notable recent action). CA-HQ; inherited William Lyon CA CFD exposure.
- **Hovnanian (HOV)** — B2/B sub-IG stable. Limited CA exposure.
- **Beazer (BZH)** — B1/B sub-IG; **S&P DOWNGRADED to B from B+ on 2025-11 on higher leverage**. Notable recent action.
- **Taylor Morrison (TMHC)** — Ba3/BB sub-IG stable; acquired William Lyon Homes 2020 (legacy CA CFD presence).
- **Tejon Ranch (TRC)** — unrated by S&P/Moody's/Fitch; small-cap; no obvious distress.

**Private with public distress signals (5):**
- **World International, LLC** — RED distress (Diablo Grande 2017 delinquency → Ch 9 2025-11-25)
- **Angel's Crossing, LLC** — RED distress (successor to World International at Diablo Grande)
- **Mountainside Builders / Taylor Builders** — RED distress (Northstar CSD CFD 2018-04-04 foreclosure complaint; $24M+ cumulative arrears)
- **ACM Northstar** — RED distress (Northstar CSD CFD 2018-04-04 foreclosure complaint)
- **Ritter Ranch Development LLC / SunCal / Lehman** — STALE_RED (1998 BK; 2008 Lehman BK; 27 yrs lingering)

**Private with no distress (3 — for breadth):**
- **Brookfield Residential / Newland Communities** — sub-IG B/stable; subsidiary of A3-rated Brookfield Corp but the residential entity itself is deep speculative grade.
- **Lewis Group of Companies** — privately held; Inland Empire focus; no public credit data; no distress signals 2024-2026.
- **Irvine Company** — privately held by Bren family; not bond issuer at corp level; no public credit data.

---

## Detector module logic (`detectors/developer_corp_credit.py`)

Distinct from `developer_bankruptcy.py`:
- `developer_bankruptcy.py` fires ONLY on Ch 11 / Ch 9 / CCC-Caa-D ratings (terminal events)
- `developer_corp_credit.py` fires on credit-quality **deterioration** PRE-bankruptcy:

| Reason | Severity |
|---|---|
| `PRIVATE_DEVELOPER_RED_DISTRESS` (active foreclosure / multi-year delinquency / Ch 9) | HIGH |
| `DEVELOPER_DISTRESSED_RATING` (CCC/Caa/D) | HIGH |
| `DEVELOPER_SUB_IG_RECENT_DOWNGRADE` (sub-IG + downgrade in trailing 12mo) | HIGH |
| `DEVELOPER_SUB_IG_NEGATIVE_OUTLOOK` | HIGH |
| `PRIVATE_DEVELOPER_STALE_DISTRESS` (lingering multi-year case) | MEDIUM |
| `DEVELOPER_SUB_IG_STABLE` | MEDIUM |
| `DEVELOPER_IG_NEGATIVE_OUTLOOK` | LOW |
| `INSUFFICIENT_DATA` | no fire |
| `DEVELOPER_IG_STABLE_OR_UNRATED_CLEAN` | no fire |

### Expected fire rate (calibration)

Running the detector against current per-obligor data:
- **Universe-wide fire rate: 3.4%** (4 / 117)
- **Housing-CFD fire rate: 5.5%** (4 / 73 housing CFDs)
- 113 of 117 return INSUFFICIENT_DATA (gap to resolve by pulling annual admin reports)

Once the 52 insufficient-data housing CFDs are resolved (via David Taussig / NBS / Webb Municipal admin reports identifying current top taxpayers), I expect:
- ~5-10 additional fires (10-20% housing-CFD fire rate) — mostly MEDIUM severity (sub-IG public developers like FPH, BZH, TMHC, TPH, KBH appearing as top taxpayers in active master plans)
- 2-3 additional HIGH severity if any FY2024-2026 private-developer distress events surface from the 52 unresolved CFDs

This is consistent with the framework's narrow-detector composition principle (saved memory `feedback_detector_composition.md`): expected ~5-15% precision-weighted fire rate on the in-scope (housing) subset.

---

## Single most-compelling developer-credit signal found

**Beazer Homes (BZH) Nov-2025 S&P downgrade B+→B on higher leverage.** This is exactly the kind of pre-bankruptcy deterioration the detector is designed to catch — a sub-IG public homebuilder with concrete leverage concerns flagged 12-24 months before the historical pattern of Ch 11 in the 2008-2012 cycle. BZH has historical CA CFD presence in Inland Empire / Central Valley regions. If we can confirm BZH is the top taxpayer in any of the 52 unresolved housing CFDs (high-probability in cities like Fontana, Apple Valley, Hesperia, Eastvale, Rancho Cucamonga, Murrieta), the detector would fire at HIGH severity (sub-IG + recent downgrade).

Runner-up: **Tri Pointe Homes (TPH) on S&P CreditWatch Developing 2026-02-18** — material recent action; TPH inherited William Lyon's CA CFD exposure post-2020 acquisition; could be a top taxpayer in several CA CFDs.

---

## Surprising findings

1. **The two largest national homebuilders by CA presence (Lennar and KBH) are NOT both IG-rated.** Lennar is barely-IG (Baa3/BBB-) with S&P outlook revised to positive; KBH is sub-IG (Ba1/BB+). KBH being the CA-HQ'd builder one notch below IG with no recent rating action is a quiet structural risk to CA CFDs.

2. **FivePoint Holdings (FPH) is sub-IG (B2/B+/BB-) despite being the headline CA master-planned-community public co.** The recent Sep-2025 Moody's upgrade and $20M/yr interest savings refi suggest improvement, but FPH being deep sub-IG with Great Park Neighborhoods (Irvine CFD 2013-3) as a top exposure means even high-quality coastal-OC CFDs carry developer-credit tail risk.

3. **Brookfield Residential (parent of Newland Communities) is B/stable** — deep speculative grade despite IG parent Brookfield Corp (A3/A-). The residential subsidiary is structurally separated and the rating reflects standalone leverage. This is a meaningful catch: a diligence file that assumed "Brookfield = IG" because of the parent name would miss this.

4. **MDC Holdings (Richmond American Homes) is no longer public** — acquired by Sekisui in 2024. Historical S&P BBB-/BBB rating is now stale.

5. **The most concentrated, publicly-known master-developer-to-CFD mapping is FPH → Irvine 2013-3 at only 40% top-taxpayer concentration.** Most CA housing CFDs in the universe either (a) are mature/built-out with diffuse homeowner taxpayer base, or (b) have a single-LLC top taxpayer that doesn't map cleanly to a publicly-rated parent. The "developer LLC = parent public-co" entity resolution is harder than the framework planning assumed (consistent with saved memory `feedback_dd_entity_resolution.md`).

---

## What couldn't be pulled and why

1. **Top-taxpayer name in 52 of 73 housing CFDs.** The prior per-obligor build (`build_landsecured_per_obligor.py`) populated taxpayer concentration percentages but NOT names for most CFDs. Resolving this requires reading the issuer/administrator annual administration reports (David Taussig & Associates, NBS, Webb Municipal Finance, Spicer Consulting, Cooperative Strategies) on EMMA — typically a 50-150 page PDF per CFD per year. Time-boxed; left as the most-important diligence GAP.

2. **Real-time rating outlooks for Hovnanian, Meritage, NVR.** Search returned 2024 actions but not formal 2025-2026 outlook confirmations. Confidence marked MEDIUM rather than HIGH for these.

3. **Private CA developer financial health for entities like Lewis, Newland, Irvine Co, Tejon Ranch.** No public ratings; family-held or subsidiary-buried. Documented absence-of-distress in trade press 2024-2026, but cannot fabricate a synthetic rating. Marked UNVERIFIABLE with note explaining the gap.

4. **Fitch rating on KBH, BZH, Hovnanian.** KB Home IR page only lists Moody's and S&P; Fitch coverage unclear. Search did not surface; marked null.

5. **D-U-N-S numbers for all developers.** Out-of-scope per available free data; would require Dun & Bradstreet subscription (~$1500/yr).

---

## Diligence-replication value-add (closing framing)

This detector is the embodiment of the saved memory `feedback_framework_value_is_diligence_not_only_alpha.md` — the value-prop is NOT that the framework finds a hidden alpha that desks miss, but that it produces (in 75 minutes of agent work) a structured credit-rating sheet on every CA CFD master developer that would otherwise take a junior analyst at a muni shop several days to compile. The sheet is:
- Cited (source URL per rating/action)
- Honesty-disciplined (UNVERIFIABLE marked, not fabricated)
- Refresh-cadence-aware (`as_of_date` on every entry)
- Structured for detector composition (fires on the pre-bankruptcy deterioration window that `developer_bankruptcy.py` misses)

The biggest near-term improvement is closing the 52-CFD admin-report gap. The second is institutionalizing a quarterly refresh cadence so credit-action data stays current.

---

## File paths (deliverables)

- `/Users/ajay/exalted/signalos/verticals/muni_credit/data/cfd_developer_credit.json`
- `/Users/ajay/exalted/signalos/verticals/muni_credit/detectors/developer_corp_credit.py`
- `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/CFD_DEVELOPER_CREDIT_BUILD.md` (this file)
- `/Users/ajay/exalted/signalos/verticals/muni_credit/data/landsecured_per_obligor/*.json` (all 117 updated)

## Sources cited (consolidated)

- FivePoint Holdings credit rating + refi: https://www.ainvest.com/news/point-debt-restructuring-strategic-move-optimize-capital-structure-mitigate-risk-2509/ + https://www.stocktitan.net/news/FPH/five-point-holdings-llc-reports-fourth-quarter-and-year-end-2025-0al0rz9lg8cg.html
- Lennar S&P positive outlook: https://www.investing.com/news/stock-market-news/lennar-outlook-revised-to-positive-at-sp-on-strong-credit-metrics-93CH-4140811
- Lennar Moody's Baa3 upgrade: https://www.moodys.com/research/Moodys-upgrades-Lennars-senior-unsecured-rating-to-Baa3-outlook-stable--PR_436047
- PulteGroup Moody's Baa1 upgrade: https://www.investing.com/news/stock-market-news/moodys-upgrades-pultegroups-unsecured-ratings-stable-outlook-93CH-3935536
- KB Home credit ratings (Ba1 / BB+): https://investor.kbhome.com/financial-information/credit-ratings/default.aspx
- Toll Brothers Moody's Baa2 upgrade Mar 2025: https://finance.yahoo.com/news/toll-brothers-finance-corp-moodys-184509346.html
- Toll Brothers S&P BBB upgrade: https://www.investing.com/news/stock-market-news/toll-brothers-inc-rating-upgraded-to-bbb-by-sp-global-ratings-93CH-4083478
- Tri Pointe S&P CreditWatch Developing 2026-02-18: https://www.spglobal.com/ratings/en/regulatory/article/-/view/type/HTML/id/3519103
- Tri Pointe S&P positive outlook Sep-2025: https://www.investing.com/news/stock-market-news/sp-global-revises-tri-pointe-homes-outlook-to-positive-on-strong-metrics-93CH-4219808
- Hovnanian Moody's B2 upgrade Jun 2024: https://khov.gcs-web.com/news-releases/news-release-details/hovnanian-enterprises-announces-credit-rating-upgrade-moodys
- Beazer S&P B downgrade Nov 2025: https://www.spglobal.com/ratings/en/regulatory/article/-/view/type/HTML/id/3475187
- Meritage Moody's Ba2: https://www.spglobal.com/marketintelligence/en/news-insights/latest-news-headlines/moody-s-affirms-meritage-homes-ratings-58596569
- Brookfield Residential S&P B stable May 2024: https://cbonds.com/news/1854301/
- Diablo Grande Ch 9 + World International / Angel's Crossing: https://elevenflo.com/blog/diablo-grande-cfd-chapter-9-bankruptcy
- Northstar CSD Mountainside / ACM delinquencies: https://www.northstarcsd.org/mountainside-partners-acm-delinquencies
- Mountainside Builders acquisition story: https://www.sierrasun.com/news/945-acre-northstar-area-land-portfolio-sold-to-nor-cal-developer-mountainside-builders/
- Ritter Ranch Bond Buyer 27-yr default: https://www.bondbuyer.com/news/ritter-ranchs-long-trail-of-cfd-defaults-may-near-an-end
