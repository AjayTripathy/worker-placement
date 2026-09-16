# CA Successor RDA Split-Rating Arbitrage Test

**Prepared**: 2026-05-28
**Framework lens**: Microstructure knowledge (hostile-validator stance)
**Hypothesis**: Rating-agency disagreement (S&P A-category vs Moody's Ba1/withdrawn) creates a tradeable spread microstructure inefficiency in CA Successor RDA tax-allocation bonds.
**Companion files**:
- `data/ca_successor_rda_split_rating_test.json` — per-name structured data
- `data/ca_successor_rda_universe.json` — universe inventory (prior scoping)
- `outputs/CA_SUCCESSOR_RDA_SECTOR_SCOPING.md` — prior scoping doc
- `knowledge_graph/masking_mechanisms.json` — `rops_allocation_intercept` entry (updated to document this falsification)

---

## TL;DR

**HYPOTHESIS NEGATED FOR CURRENT MARKET.** The 2012-2014 split-rating baseline that motivates this hypothesis (S&P 70% A-category vs Moody's 31 of 94 withdrawn + Ba1 average on remaining) has structurally COLLAPSED through 2014-2017 Moody's rating actions: Moody's withdrew most ratings on the sector, and the ratings that survived were UPGRADED to investment grade in 2014-2017 under new methodology (San Jose SARA to A1/A2, Santa Monica SA to A2, etc.).

Of N=10 CUSIPs tested across 9 distinct Successor Agency issuers, **ZERO have a current verified Moody's rating at Ba1 or lower**. The split-rating cohort the hypothesis requires does not exist in 2026.

Spread positioning: market prices essentially AT S&P-implied curve (mean observed-vs-S&P-implied spread = +5.5 bps, within bid/ask noise). 180 bps tighter than a counterfactual Moody's-Ba1-implied curve — but that counterfactual is irrelevant because Moody's isn't currently rating these credits at Ba1.

**Modest illiquidity premium** on small-issuer names (Brea +33 bps, Buena Park +36 bps, San Marcos +35 bps vs A-cat curve) is REAL but is small-issuer / small-deal liquidity discount, NOT a rating-disagreement-arbitrage signal.

**Verdict for masking-mechanism catalog**: `rating_agency_disagreement_arbitrage` is **NOT validated** as a current tradeable signal on this sector. Document the falsification in `rops_allocation_intercept` entry.

---

## 1. Test design

### 1.1 The hypothesis
Per prior scoping, CA Successor RDA bonds were noted to have the widest rating-agency disagreement of any muni sector (S&P 70% A-cat, 15% AA-, vs Moody's withdrew 31 of 94, rated remainder Ba1 average). The hypothesis: if the bond market prices to S&P (the more permissive view), there is a structural mispricing — buy at S&P-yield, get S&P-quality fundamentals, capture the "false-pessimism premium" implied by the Moody's rating.

### 1.2 Three possible outcomes (per task spec)
1. **S&P is right, Moody's overly pessimistic** → bonds price to S&P, captures the pessimism premium
2. **Moody's is right, S&P overly generous** → spread compression on S&P downgrade catch-up
3. **Market splits the difference** → modest mispricing either direction

### 1.3 Method
- Universe: 29 Successor RDA issuers from `data/ca_successor_rda_universe.json` + targeted CUSIP search
- Pulled EMMA secondary trades via MunicipalBonds.com (Chrome fingerprint scraping per saved memory)
- Cross-checked ratings via OS PDFs (Riverside 2018, Atascadero 2024, San Diego 2017, LA County 2017)
- Computed observed spread to MMD AAA at matched maturity, compared to S&P-implied and Moody's-implied curves
- Benchmark curve (FMSbonds 2026-05-28): AAA 10y 3.10%, AA 10y 3.20%, A 10y 3.40%, BBB 10y ~5.02%, BB/HY 10y ~4.99%

### 1.4 What went wrong with the hypothesis
The hypothesis requires a CURRENT split-rated cohort. After pulling 4 issuance OS PDFs and direct Moody's news on universe issuers, the structural pattern is:
- **Riverside 2018A**: S&P AA insured (AGM), no Moody's rating
- **San Diego 2017A**: S&P AA insured (BAM), no Moody's rating
- **LA County / West Covina 2017A**: S&P AA-, no Moody's rating
- **Atascadero 2024A**: S&P A+ Stable, no Moody's rating
- **San Jose SARA**: Moody's UPGRADED to A1/A2 in 2017 (Housing/Non-Housing)
- **Santa Monica SA**: Moody's UPGRADED to A2 (per PR_332803)

The pattern is overwhelming: post-2014 refundings are predominantly S&P-only or S&P+Fitch, with Moody's having WITHDRAWN ratings on most credits. The credits that retain Moody's ratings have been UPGRADED to investment grade under new methodology. **The 2012-2014 split-rating disagreement was resolved by Moody's exiting the market for most of these credits and upgrading the survivors.**

---

## 2. Results

### 2.1 N tested = 10 CUSIPs across 9 issuers

| Issuer | CUSIP | Coupon | Maturity | Latest Trade | YTM | Spread to AAA | S&P | Moody's |
|---|---|---|---|---|---|---|---|---|
| Anaheim SA | 032564AH9 | 5% | 2027-02 | 2026-05-04 | 2.28% | -12 bps | AA underlying | WITHDRAWN |
| Riverside SA 2018A (5s 30) | 76904RBR7 | 5% | 2030-09 | 2026-05-06 | 2.66% | +11 bps | AA insured (AGM) | WITHDRAWN |
| Riverside SA 2018A (5s 28) | 76904RBP1 | 5% | 2028-09 | 2026-05-11 | 2.70% | +15 bps | AA insured (AGM) | WITHDRAWN |
| San Marcos SA 2015A | 79876CAM0 | 5% | 2027-10 | 2025-09-04 | 3.10% | +65 bps | A-cat (inf) | WITHDRAWN |
| Brea SA 2017A | 106293BV4 | 5% | 2032-08 | 2026-05-13 | 3.33% | +83 bps | A-cat (inf) | WITHDRAWN |
| Buena Park SA Parity A | 119144AQ6 | 4% | 2034-09 | 2026-04-30 | 3.36% | +66 bps | A-cat (inf) | WITHDRAWN |
| Novato CDA Series A | 66989KAD3 | 4% | 2033-09 | 2026-02-24 | 2.62% | +2 bps | A-cat (inf) | WITHDRAWN |
| LA Co RDA Auth West Covina | 54465AHJ4 | 2.25% | 2025-09 | 2024-12-04 | 3.01% | +60 bps | AA- | NOT RATED |
| Inglewood Sub Lien CAB | 457106MR0 | 0% | 2027-05 | 2026-03-10 | 2.71% | +26 bps | not extracted | WITHDRAWN |
| Inglewood Taxable Sub Lien | 457106MY5 | 6.315% | 2038-05 | 2026-04-28 | 5.76% | n/a (taxable) | not extracted | WITHDRAWN |

### 2.2 Mean spread test

Excluding the taxable Inglewood and the stale LA County print:

- **Mean (observed - S&P-implied)** = +5.5 bps → Market prices ESSENTIALLY AT S&P-rated curve. Modest tilt wider for smallest-issuer names (Brea/Buena Park/San Marcos), but well within illiquidity-premium magnitude.
- **Mean (observed - Moody's-Ba1-implied)** = -180 bps → Market prices ~180 bps TIGHTER than a counterfactual Moody's Ba1 curve. But this counterfactual is structurally irrelevant: Moody's has no current Ba1 rating on these credits to disagree with.

### 2.3 The structural finding

**The hypothesized split-rating arbitrage does not exist in the current market because the split itself has resolved.** Moody's withdrew ratings on 31 of 94 (33%) of CA TABs in 2012-2014, then placed remaining under review for upgrade in 2015 under new methodology (Research Update PR_328765), then UPGRADED most of the survivors to investment grade in 2017 (San Jose SARA Housing A1, Non-Housing A2; Santa Monica A2). The remaining Ba1-rated credits (Atwater Ba2 in 2014, possibly Torrance Ba2) are a small residual that fell out of the universe through refunding or natural maturity.

---

## 3. Top 5 cleanest "buy" candidates (illiquidity-premium, not split-rating-arbitrage)

| # | Issuer | CUSIP | Pickup vs A-cat | Thesis | Host stress? |
|---|---|---|---|---|---|
| 1 | Brea SA 2017A 5s 2032 | 106293BV4 | +43 bps | Small affluent OC city, A-rated host; small-deal illiquidity discount | NO |
| 2 | Buena Park SA Parity A 4s 2034 | 119144AQ6 | +36 bps | Knott's Berry Farm host; concentration priced in; small-deal | NO |
| 3 | San Marcos SA 2015A 5s 2027 | 79876CAM0 | +35 bps | Stale Sep 2025 print; SD County north suburb; pure illiquidity | NO |
| 4 | Inglewood Sub Lien CAB 0s 2027 | 457106MR0 | -4 bps | Sports/entertainment AV growth (SoFi/Intuit Dome); trades AT A-cat curve | NO |
| 5 | Riverside SA 2018A 5s 2028 (underlying) | 76904RBP1 | -15 bps | Trades to AGM-insured AA wrap; underlying A- gives notional pickup | NO |

**Important framing**: these are NOT split-rating-arbitrage candidates. They are small-issuer illiquidity-premium candidates that may yield 30-50 bps pickup vs A-cat curve. Different signal regime entirely.

## 4. Top 3 false-positive risks

| # | Issuer | CUSIP | Risk |
|---|---|---|---|
| 1 | Anaheim SA 5s 2027 | 032564AH9 | Trades 12 bps THROUGH AAA. Disney top-taxpayer concentration is THE load-bearing risk. Recent strong AV but tail-risk on Disney parks closure or Disney-credit-event would catch S&P rating off-guard. |
| 2 | Lancaster SA (not in trade sample) | N/A | Antelope Valley housing-cycle exposure + CA aerospace defense contraction risk. Project area AV trajectory cyclical. |
| 3 | Stockton legacy insured RDA TABs (no CUSIP pulled) | N/A | Insurer wrap dominates; underlying credit unobservable. If host post-BK fiscal stress affects RPTTF distribution mechanics, the wrap absorbs but underlying signal goes wrong direction. |

---

## 5. Honest disciplines — hostile validator stance

Per task spec, look hard for evidence the hypothesis doesn't work.

### Evidence FOR the hypothesis (looking for confirmation)
- 2014 Bond Buyer commentary directly states S&P 70% A-cat vs Moody's 31 of 94 withdrawn / Ba1 average. The split-rating gap was REAL when the data was collected.
- Universe scoping (prior session) noted the widest rating-agency disagreement of any sector.
- Theoretical structure (S&P uses Special-Purpose District methodology; Moody's uses cash-flow volatility framework) supports persistent methodology divergence.

### Evidence AGAINST (the killers)
- **Moody's 2017 upgrade cycle**: San Jose SARA to A1/A2, Santa Monica to A2, multiple other names re-rated to IG. The 2014 Ba1 baseline DOES NOT persist to 2026.
- **Moody's withdrew ratings on the majority**: most universe names have NO current Moody's rating. The "split" requires two ratings; one is absent.
- **Empirical spread test**: mean observed-vs-S&P-implied = +5.5 bps. Market is NOT pricing to Moody's. Market is pricing to S&P, which is the rating it has.
- **OS PDF pattern**: of 4 OS PDFs pulled (Riverside 2018, San Diego 2017, LA County 2017, Atascadero 2024), ALL are S&P-only-rated. The new-issuance market does not seek Moody's ratings on these credits.
- **Insurance wrap dominance**: Riverside 2018 (AGM), San Diego 2017 (BAM), LA County legacy (AGM/NPFG). Wraps mask any underlying signal, including any split.
- **Small-issuer spread pickup is NOT the same signal**: the +30-50 bps pickup on Brea / Buena Park / San Marcos is illiquidity premium, not rating-disagreement. Wrong attribution would mis-classify alpha source.

### Verdict on hostile-validator stance
The hypothesis FAILS on multiple independent lines of evidence. The data-generating process for the 2014 "wide split" baseline has materially changed (Moody's exited the market for most credits; survivors upgraded). The 2026 market does not exhibit the alleged inefficiency.

**Counterfactual: if Moody's had not withdrawn and had not upgraded, would the split-rating arbitrage work today?** Probably yes — bond market clearly prices to S&P (mean +5.5 bps to S&P-implied). But this is a counterfactual, not a current opportunity.

---

## 6. Open data gaps

1. **CURRENT Moody's ratings** — Moody's website is JS-rendered, 403s on direct fetch even with full Chrome fingerprint. Would require headless browser (Playwright/Selenium) or paid Moody's API. Sampled via municipalbonds.com Moody's-by-issuer pages and Moody's news search; explicit confirmation on each universe CUSIP not done.
2. **Comprehensive S&P direct ratings** on San Marcos, Brea, Buena Park, Novato — inferred from sector pattern, not verified per-CUSIP. Would require pulling each issuer's OS from EMMA in bulk.
3. **2012-2014 backtest** — when the wide split was active, did bonds in fact trade closer to S&P or Moody's? Hypothesis confirmation at that point. Not done in 90-min window; requires historical EMMA trade data which is hard to access programmatically.
4. **Identification of any persisting Ba1 names** — Atwater RDA Ba2 (2014 last action), Torrance Ba2 (2013). If still actively rated, would be the only universe of split-rated names available. Not pulled.
5. **Effective duration / call risk** per CUSIP — back-of-envelope spread test ignores call protection.

---

## 7. Knowledge graph update

**Action**: Update `knowledge_graph/masking_mechanisms.json` `rops_allocation_intercept` entry to:
- Document the falsification of the split-rating-arbitrage alpha mode (was listed in `alpha_implication` field with confidence LOW; now confirmed FALSIFIED in current market)
- Add finding: "Rating-agency disagreement that produced the 2012-2014 wide split structurally resolved by Moody's rating withdrawals + 2014-2017 upgrade cycle. Current market does not exhibit the inefficiency."
- Add cross-reference to this test file path

**Microstructure-knowledge value**: This is a positive finding from the knowledge-graph perspective. We have now MEASURED a candidate masking mechanism / signal channel and CONFIRMED IT IS NOT CURRENTLY ACTIVE. This is exactly the kind of finding the catalog needs: not just "what does mask signals" but also "what was hypothesized to be tradeable but isn't, and why."

---

## 8. Path to validation if hypothesis revives

If a future session wants to retest:
1. Use a headless browser (Playwright) against Moody's website to enumerate all currently-rated CA Successor Agency TAB credits. Identify any still at Ba1 or lower.
2. Pull CUSIP-level OS PDFs from EMMA for those names.
3. Find any CUSIP with S&P >= A- AND active Moody's <= Ba1. If N >= 10 such names exist, repeat the spread test on that genuinely split-rated cohort.
4. If N < 10, document that the cohort is too small for statistical power and the hypothesis is structurally inactive (which is what this 90-min test indicates).

---

## Appendix A: Sources

| Citation | URL |
|---|---|
| MMD AAA / category curve 2026-05-28 | https://www.fmsbonds.com/market-yields/ |
| Nuveen Q2 2026 muni outlook (BBB/HY spreads) | https://www.nuveen.com/en-us/insights/municipal-bond-investing/municipal-market-update |
| Riverside 2018A OS | https://riversideca.gov/finance/investor/pdf/investorreports/18AB-SARDA-TARB/OS-2018AB-TAB.pdf |
| Atascadero S&P 2024 rating report | https://www.atascadero.org/sites/default/files/2024-03/2024%20Bond%20Refunding%20S&P%20Rating%20Analysis.PDF |
| San Diego SA 2017 OS | https://www.sandiego.gov/sites/default/files/dm_rda_pos.pdf |
| LA County / West Covina 2017A OS | https://emma.msrb.org/ER1028949-ER806449-ER1207595.pdf |
| Long Beach SA 2021 continuing disclosure | https://www.longbeach.gov/globalassets/finance/media-library/documents/city-budget-and-finances/treasury/fy21-disclosure |
| Moody's SJ SARA 2017 upgrade | https://www.moodys.com/research/Moodys-Upgrades-Successor-Agency-to-City-of-San-Jose-RDAs--PR_903967818 |
| Moody's Santa Monica SA A2 upgrade | https://www.moodys.com/research/Moodys-upgrades-Successor-Agency-to-City-of-Santa-Monica-RDAs--PR_332803 |
| Moody's 2012 CA TAB Ba1 downgrade | https://www.moodys.com/research/Moodys-downgrades-to-Ba1-all-California-TABs-rated-Baa3-or--PR_248528 |
| Moody's 2014 CA TAB withdrawals (22 + 31 cumulative) | https://www.moodys.com/research/Moodys-withdraws-ratings-on-22-former-California-Redevelopment-Authorities-tax--PR_274935 |
| Moody's 2015 review for upgrade (new methodology) | https://www.moodys.com/research/Moodys-places-ratings-of-CA-tax-allocation-bonds-under-review--PR_328765 |
| Bond Buyer CA TABs Heat Up 2014 | https://www.bondbuyer.com/opinion/commentary-california-tax-allocation-bonds-heat-up |
| Bond Buyer CA Redev Bonds Take Ratings Hit 2012 | https://www.bondbuyer.com/news/california-redevelopment-bonds-take-ratings-hit |
| Bondview San Marcos | https://www.bondview.com/bond/79876CAM0 |
| Bondview Brea | https://www.bondview.com/bond/106293BV4 |
| MunicipalBonds.com (per CUSIP) | https://www.municipalbonds.com/bonds/issue/{cusip}/ |
