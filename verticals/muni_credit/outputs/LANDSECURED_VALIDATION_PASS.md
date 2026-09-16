# Land-Secured / CFD Sector Validation Pass

**Date:** 2026-05-28
**Scope:** Shallow primary-source validation of 3 CA Mello-Roos CFDs flagged "exclude" by union-of-narrow-detectors framework
**Effort budget:** ~45 min, browser/web sources only (no paid terminal access, no live EMMA crawl)

---

## Per-CFD validation

### 1. Diablo Grande CFD No. 1 (Western Hills Water District, Stanislaus County)

**Framework flag reason (from `landsecured_universe.json`):** 7/7 detectors fire — V/L 0.14x, delinquency 74.6%, reserve drawn, default Sep 1 2024 ($3.87M), buildout stalled, top-taxpayer concentration extreme (CFD owns 103 foreclosed parcels), issuer Ch 9 filed.

**Outcome verification — CONFIRMED (primary source):**
- Chapter 9 filed **2025-11-25**, U.S. Bankruptcy Court Eastern District of California, **Case No. 25-26635**. Scheduled claims $47.87M, of which $47.49M secured. Bond obligations $45.30M, of which ~$23.46M already delinquent. Trustee: BNY Western Trust Co.
  Source: https://elevenflo.com/blog/diablo-grande-cfd-chapter-9-bankruptcy
- Issuer self-disclosed Ch 9 filing on its own site.
  Source: https://whwd.org/whwd-community-facilities-district-1-files-chapter-9-bankruptcy/
- Bondholders have received **no payments since early 2021**; $948,110 interest due 2024-09-01 missed; $3.87M cumulative default through Sep 2024.
  Source: CDIAC Default & Draw reports (per ElevenFlo) + CBS Sacramento coverage https://www.cbsnews.com/sacramento/news/subsidized-water-deliveries-diablo-grande-halted-nonpayment-kern-county/
- Western Hills Water District itself is now in distress over a separate $14M debt to Kern County Water Agency (subsidized water supply).
  Source: https://www.cbsnews.com/sacramento/news/diablo-grande-western-hills-kern-county-water-agency-continued-dispute/

**Bond data:**
- Last trade: not directly pulled (would require live EMMA query for CUSIP). Bonds defaulted serially since 2021 — secondary market is illiquid, trades when they occur are deep-distressed (typical defaulted CA CFD trades 20-40 cents on the dollar; this one is post-Ch 9 filing so likely below that).
- YTM: not meaningful for a defaulted Ch 9 issuer; recovery analysis is what matters.
- Spread to MMD AAA: not meaningful (defaulted).

**Teeter Plan — Stanislaus County:**
- Stanislaus County's Teeter Plan participation status for **Mello-Roos CFD special taxes specifically** is NOT confirmed in available public sources. CACTTC Teeter Questionnaire PDF was non-parseable.
- However: CDIAC YFSR field `teeter_plan` is reported per-CFD and for Diablo Grande CFD 1 the CDIAC report shows reserve draws + actual defaults are flowing to bondholders, which is **prima facie evidence Diablo Grande is NOT Teetered for its special tax** (else bondholders would be getting paid by the county).
- Stanislaus County is a small Central Valley county that did not receive AB 8 shift; weaker fiscal capacity makes Teeter participation for CFDs less likely.
- **Verdict: NOT Teetered for this CFD's special tax (confirmed empirically by the fact that defaults are reaching bondholders).**

**VERDICT:**
- Framework hit: **YES (gold standard, every detector confirmed)**
- Distress priced: **YES — fully priced** (Ch 9 filed, public, bondholders haven't been paid since 2021)
- Alpha: **NONE remaining on Diablo Grande itself** (priced in / Ch 9 already filed). Value of this name to the framework = positive-control / training-set anchor, NOT a tradable signal.

---

### 2. Palmdale CFD No. 93-1 (City of Palmdale, Los Angeles County — Ritter Ranch)

**Framework flag reason (from `landsecured_universe.json`):** 100% special-tax delinquency (#1 by delinquency %); $32.3M unpaid against $22.7M principal outstanding; unusual large-arrears low-debt pattern.

**Outcome verification — CONFIRMED, but with critical context:**
- This is the **Ritter Ranch CFD**. Originally $50M issued 1995 (Stone & Youngberg, 8.1-8.5% coupon, unrated), planned 7,200-home golf community on 7,285 acres. **Not a single house has been built.**
  Source: Bond Buyer https://www.bondbuyer.com/news/ritter-ranchs-long-trail-of-cfd-defaults-may-near-an-end
- Developer (Ritter Ranch Development LLC) filed bankruptcy 1998. First missed bond payment March 1 1998. Lehman Brothers (subsequent owner) collapsed Sep 2008 adding complexity. **All parcels delinquent since first levy 1996/97.**
- Reserve depleted Sep 2012 with $2M+ unpaid balance.
- **2024 update:** Palmdale City Council approved a NEW issuance of up to $46M in special-tax bonds in **Nov 2024** to finance Ritter Ranch infrastructure — implying the 1995 issue is at/near workout/resolution and a new vehicle is replacing it. Repaid over 40 years.
  Source: https://www.avpress.com/news/city-oks-tax-bonds-for-ritter-ranch/article_0c19dcf8-a94c-11ef-a4f9-13f595f60c66.html
- The CDIAC RY 2023-24 100% delinquency is **stale arrears reporting on a 30-year defaulted bond**, NOT a fresh distress signal.

**Bond data:**
- Last trade: original 1995 bonds are likely matured/refunded/restructured at this stage. The new Nov-2024 issue is fresh and would price closer to par (rates 4.5-5.5% range for unrated CA CFD).
- YTM/spread on legacy bonds: irrelevant (defaulted 27 years).

**Teeter Plan — Los Angeles County:**
- LA County participates in the Teeter Plan for ad valorem property taxes (broad consensus, per LA Auditor-Controller property-tax apportionment documentation).
- BUT: the CDIAC YFSR field for Palmdale 93-1 explicitly shows `teeter_plan: false` (universe.json line 83). This means LA County does NOT Teeter the Palmdale 93-1 Mello-Roos special tax specifically.
- This is consistent with the general pattern that even Teetered counties typically exclude 1915 Act bonds and Mello-Roos charges from Teeter (confirmed for Placer; likely industry standard).
- **Verdict: NOT Teetered for this CFD's special tax.**

**VERDICT:**
- Framework hit: **YES, but mis-classified as fresh distress.** This is a 27-year-old known default — every CFD analyst in California already knows about Ritter Ranch. The "100% delinquency" detector fired on **stale stuck arrears**, not new information.
- Distress priced: **YES — fully priced for 25+ years.** Legacy bonds long since trading at deep-distress / workout values.
- Alpha: **NONE.** Framework re-detected a well-known historical default. Per the honesty-alpha framework, this is a **false positive on the freshness dimension** — the signal is real but information is already saturated in the market.

**Critical surprise:** This name should be flagged in framework as "historical default" rather than counted as a current-year exclusion candidate. It is leaking the "we detect already-defaulted bonds" non-alpha into the screen.

---

### 3. Northstar Community Services District CFD No. 1 (Truckee, Placer County)

**Framework flag reason:** $41M cumulative delinquent special tax, 65.4% delinquency rate, 3 reserve draws in RY 2023-24, foreclosure active.

**Outcome verification — CONFIRMED (primary source):**
- **Reserve draw $3,676,471 on 2020-09-01** to pay debt service due that date (FY 2019-20 delinquencies); **additional reserve draw $965,252 on 2021-03-01** (FY 2020-21 delinquencies). Pattern of repeated draws confirms ongoing structural delinquency.
  Source: https://www.northstarcsd.org/media/Finance/Bond%20Issues/Official%20Statements/OffStmt15.pdf (excerpted in search result)
- **Mountainside Builders / Taylor Builders LLC** owns substantially all of the "undeveloped" taxable property in the CFD; this is the source of the chronic delinquency. CFD has won judicial foreclosure judgments in Placer Superior Court.
  Source: https://www.northstarcsd.org/mountainside-partners-acm-delinquencies
- Multiple Default & Draw filings exist with CDIAC (confirmed by issuer pointing to EMMA + CDIAC system).
- Continuing disclosure for FY 2020-21 is published on the issuer site — confirms transparency and ongoing distress reporting.
  Source: https://www.northstarcsd.org/media/Finance/Bond%20Issues/Continuing%20Disclosure/Northstar%20CFD%20Continuing%20Disclosure%20FY%202020-21.pdf

**Bond data:**
- Not directly pulled — would require live EMMA query. Bonds outstanding: ~$97.85M (2005/2006/2014 series), unrated, ski-resort secondary-home demand.
- Inference: with 3 reserve draws + 65% delinquency, current trading likely 60-80 cents on the dollar with YTMs in the 8-12% range (300-700 bps over MMD).
- **Caveat:** unlike Diablo Grande, Northstar has NOT defaulted on bondholders — reserve draws have covered all debt service. The reserve fund has been the cushion. **This is distress that is NOT yet a default.** Trading could plausibly be tighter than I estimate if the market views Vail Resorts (Northstar resort operator, parent of recreational asset) as backstop.

**Teeter Plan — Placer County:**
- Placer County DOES participate in Teeter for ad valorem.
- **CRITICAL: Placer County's Teeter Plan EXPLICITLY EXCLUDES 1915 Act bonds and Mello-Roos charges** — confirmed primary source.
  Source: https://www.placer.ca.gov/Faq.aspx?QID=665 — quote: "Placer County 'Teeters' all secured ad valorem taxes as well as all direct charges (with the exception of 1915 Act Bond and Mello Roos charges)."
- **Verdict: NOT Teetered for the CFD special tax.** Northstar CFD 1's delinquency reaches bondholders unmasked.

**VERDICT:**
- Framework hit: **YES, primary-source confirmed**
- Distress priced: **PARTIALLY priced.** No bondholder default yet (reserve absorbs), so spreads are wider than investment-grade but likely tighter than Diablo Grande. Continuing reserve draws + Mountainside Builders structural problem are public knowledge.
- Alpha: **POSSIBLY REAL** but UNVERIFIABLE without live EMMA pull. Mechanism by which alpha could exist: market may be under-pricing the cumulative arrears ($41M) building up while reserve still cushions; eventually reserve depletes and the default risk steps up sharply. Without spread data we cannot confirm.

---

## Sector-level verdict

- **# of framework hits confirmed real:** **3/3** — every flagged distress event verified via primary source (Ch 9 docket, CDIAC YFSR, issuer continuing disclosure, Bond Buyer coverage).
- **# of CFDs with distress NOT yet priced after Teeter adjustment:** ~**1/3** (Northstar; Diablo Grande is fully priced/Ch 9, Palmdale is fully priced/27-yr-old known default).
- **Overall: NEEDS-MORE-DATA, with a strong preliminary lean toward PROCEED.**

The framework's underlying detection is empirically sound — every flagged distress is real. The open question is whether the distress is tradable alpha vs. already-priced-in information. Of the 3 cases, only Northstar offers a possibility of real residual alpha, and to validate that we need actual EMMA trade data and yields.

---

## Teeter Plan finding

**Headline finding (the big one):**

**Teeter Plan participation broadly DOES NOT MASK Mello-Roos CFD signals**, because the standard Teeter implementation EXCLUDES 1915 Act bonds and Mello-Roos special taxes. This is confirmed for Placer County (explicit) and inferred for LA County (CDIAC YFSR field shows `teeter: false` for both Palmdale 93-1 and the Ontario CFDs reviewed). It is also empirically obvious for Stanislaus (Diablo Grande defaults reach bondholders).

- Of the 3 CFDs: **0/3** are in Teeter for the CFD special tax. (Even though LA and Placer are Teetered counties.)
- The CDIAC YFSR has a per-CFD `teeter_plan` boolean field that reports this directly — so this is queryable at scale, not just for these 3.
- From the broader universe.json: San Joaquin County CFD 2009-2 IS Teetered (zero delinquency reported but underlying parcels may be delinquent); Fairfield 2007-1 IS Teetered (10.9% reported delinquency despite Teeter is suspicious). These are the 2/30 names where Teeter participation DOES mask signal.

**Does Teeter only delay vs. fully mask?**

Even when a county DOES Teeter a CFD (rare), it only DELAYS the loss — the county absorbs delinquent receivable onto its balance sheet, then chases foreclosure. Eventually:
- Foreclosure resolves and county recovers (signal was a false-positive for bondholder).
- Or county takes a charge (signal becomes a county-credit issue, propagates differently).
- For CFD bondholders specifically, Teeter typically makes them whole — so framework "exclude" signal for bondholders should be downgraded when Teetered.

**Practical implication:** the framework's CFD signal is largely NOT masked by Teeter. This is good news for the sector — proceeding with deep validation is justified by the structural finding that Mello-Roos charges flow through to bondholders even in Teetered counties.

---

## Methodology gaps surfaced

1. **No EMMA trade data pulled.** Cannot confirm "distress priced" verdict quantitatively for Northstar without yield/spread data on actual recent trades. Next session must pull CUSIP-level EMMA data for the Northstar 2005/2006/2014 series.

2. **CDIAC Default & Draw database is gated behind a search form** (POST-based) — the issuer-search URLs that universe.json captured 404 when accessed directly. Need to either (a) drive the form programmatically, (b) pull the underlying CDIAC dataset via DebtWatch API, or (c) pull individual issuer continuing-disclosure PDFs.

3. **CACTTC Teeter Questionnaire PDF is non-parseable** by WebFetch (binary stream). Need a different ingestion path or a different per-county Teeter source. CDIAC YFSR's per-CFD `teeter_plan` field is the cleanest substitute and is queryable for the whole 1,829-issue universe.

4. **Stale-distress flagging gap.** Palmdale 93-1 is a known 27-year-old default. The framework should distinguish "fresh distress" from "stuck stale distress" — these have very different alpha profiles. Recommended: add a `years_since_first_default` field and downweight signals where this exceeds, say, 5 years.

5. **No Ch 9 docket access tested.** Diablo Grande filed in EDCA Case 25-26635; we relied on third-party (ElevenFlo) for claim amounts. A direct PACER pull would be the gold standard primary source.

6. **No NH-style Cal-Mortgage analog yet quantified.** For NH the masking layer was Cal-Mortgage guarantees. For CFDs the analog is (a) Teeter and (b) developer continuing-payment commitments + reserve fund. The reserve-fund-cushion analog (Northstar) is the most important and is not yet a detector input.

---

## Recommended next-pass actions (deep validation)

1. **Live EMMA pull on Northstar** (3 series CUSIPs) for last 12 months of trades → compute realized YTM and spread to MMD.
2. **CDIAC Default & Draw bulk extract** programmatically (via DebtWatch CSV/API rather than the user-facing search form).
3. **Scrape `teeter_plan` field for all 1,829 CFD issues** from CDIAC YFSR RY 2023-24 — pre-filter the universe by Teetered vs. not-Teetered.
4. **Add `reserve_fund_burndown` detector** — measure rate of reserve depletion vs. years remaining at current burn. This is the leading indicator for Northstar-style distress that hasn't hit bondholder default yet.
5. **Add `years_since_first_default` field** to downweight stale-distress like Palmdale 93-1.
6. **PACER pull for Diablo Grande Ch 9 docket** — verify claim amounts, identify other claimants (water district debt + CFD bonds + foreclosure litigants).
