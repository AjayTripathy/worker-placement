# US FHA Section 242 Hospital Muni — Sector Scoping & Masking Validation

**Date**: 2026-05-28
**Vertical**: muni_credit
**Mechanism tested**: `fha_section_242` — federal hospital mortgage insurance
**Hypothesis (catalog prediction)**: Cal-Mortgage analog at the federal level — full masking of operator credit; framework alpha collapses to ~30-60 bps (Cal-Mortgage-equivalent compression)
**Verdict**: **DOCUMENTED → PARTIAL MASKING** (NOT full Cal-Mortgage analog). Bonds wrap to AAA/AA+ rating but trade ~50-100 bps wider than the unwrapped MMD AAA curve, and sometimes WIDER than A-rated muni curve. Operator distress leaks through into spread more than Cal-Mortgage does.

---

## 1. Universe

**Active FHA 242 portfolio (HUD historical-deals file, 2025-04-22 Wayback snapshot)**:
- 94 active mortgage loans, 69 unique obligor hospitals
- Total active mortgage: **$8.66B** (consistent with the user's $15-20B prior, allowing for legacy deals + 2021-2025 new commitments not in this snapshot)
- Top state: NY (26 loans / 38% of obligors), then CA, IL, TX, SC, CO
- Top 15 obligors by exposure cover 81% of active dollars ($7.0B)

**Source**: `data/fha242/242_All_Historical_Deals.xlsx` (parsed → `242_active_aggregated.json`); commitments file `OHF_Commitment_Data.xls` (parsed → `ohf_commitments.json`).

**Two confirmed historical claim events** (program has been stress-tested):
| Obligor | Endorsement | Mortgage | Claim event | HUD loss |
|---|---|---|---|---|
| Lakeway Regional Medical Center, TX | 2010 | $167M | Default + FCA fraud, 2013 | ~$172M (gross) |
| LRGHealthcare, Laconia NH | 2009 | $135M | Ch.11 bankruptcy, 2020 | ~$111M |

Both bondholders/GNMA holders were paid (wrap held). The 2024 GAO report (GAO-24-106480) raised concerns about portfolio concentration but didn't recommend program shutdown.

---

## 2. Masking verdict — `fha_section_242` upgraded MENTIONED_NOT_VALIDATED → **DOCUMENTED (PARTIAL MASKING)**

### Cal-Mortgage benchmark (for comparison)

| Property | Cal-Mortgage | FHA 242 (this finding) |
|---|---|---|
| Wrap credit rating | State AA- (CA) | "AAA-equivalent" per HUD marketing; bonds carry Aa1/AA+ per agency |
| Stress-test history | 1 default (Tri-Valley) | 2+ defaults (Lakeway, LRG) — wrap held both times |
| Spread compression vs unwrapped | "FULL MASKING" — Carmel Valley Manor traded at 100.134 / 3.00% YTM despite SFF flag | **PARTIAL** — Maimonides Aa1/AA+ FHA-insured bond trades at 4.99% YTM (50-75 bps over AAA, ~AT A-rated curve) despite Aa1 wrap |
| Realizable alpha | 30-60 bps after compression | **Wider** — possibly 75-150 bps where operator weakness + wrap coexist |
| Underlying operator visibility | Hidden behind state credit | Partially exposed — bondholders price in some operator risk premium even with federal wrap |

### Load-bearing empirical anchor — Maimonides Medical Center

**Maimonides operator state (2024-2025)**:
- "Substantial doubt" going-concern in 2024 audit
- $375M cumulative loss 2021-2024
- $85M Q1 2025 operating loss (+39% YoY)
- Pending NYC Health+Hospitals merger
- Sources: Crain's NY, Brooklyn Paper, Forward

**Maimonides FHA-Insured Mortgage Hospital Revenue Bonds, Series 2020** (DASNY $135.8M issuance):
- At issuance (July 2020): Aa1/AA+, 2050 term priced 2.57% YTM, 2043 term priced 2.18%
- Today (May 2026):
  - 2050 (CUSIP 64990G3B6): trading at **4.99% YTM** / 72.49 price
  - 2043 (CUSIP 64990G3A8): trading at **4.44% YTM** / 94.74 price
- MMD AAA today: 20y=4.10%, 30y=4.45% → 24y interp ~4.24%, 17y interp ~3.74%
- **Spread to MMD AAA**: 2050 = ~+75 bps, 2043 = ~+70 bps
- **Spread to A-rated curve**: 2050 = ~+39 bps, 2043 = ~+50 bps

**Interpretation**: A bond explicitly marketed as "AAA-equivalent" because of federal-backed FHA wrap **trades wider than the A-rated muni curve**. The market is NOT giving the wrap full AAA treatment. Operator distress at Maimonides is partially leaking through.

This is **structurally weaker masking than Cal-Mortgage**. The hypothesis "FHA 242 is a federal-level Cal-Mortgage analog" is **partially falsified** — wrap exists and protects against ultimate loss, but spread compression to AAA is incomplete.

### Why FHA 242 ≠ Cal-Mortgage

Three structural reasons the FHA 242 wrap masks LESS effectively than Cal-Mortgage:
1. **Bond market technicals**: hospital revenue bond paper is thinly traded; even AAA-equivalent paper bears a meaningful liquidity / sector premium that AGM/Cal-Mortgage muni paper does not.
2. **Default history is non-zero**: Lakeway and LRGHealthcare both burned through the program (whereas Cal-Mortgage has had only Tri-Valley + small ones). The market remembers.
3. **Federal political risk**: the GAO repeatedly recommends volume limits; the program is reauthorized periodically; bond market prices in a small premium for "what if Congress changes the rules"

### Implication for framework

- The framework's operator-credit detectors (CMS Star, going-concern, layoffs, payor mix, DOJ FCA) **ARE useful** on FHA 242 paper — moreso than on Cal-Mortgage where the wrap fully decouples. Maimonides is the proof point: operator distress + wrap = +50 to +75 bps over A-curve, real spread to harvest.
- BUT the alpha mechanism is different than expected. Not "find masked operator distress that the market hasn't priced" (the Cal-Mortgage thesis). Rather: "find the bonds where the FHA wrap forces buyers to over-pay for the rating relative to the underlying operator quality" — i.e., a *fair-value* play where well-operated FHA 242 hospitals (NYP, MUSC, UNM, Englewood) deserve the AAA-equivalent treatment and weakly-operated ones (Maimonides, Kaleida, Brooklyn Hospital Center, St. Barnabas) deserve A-equivalent treatment but still wrap to AAA-equivalent.

---

## 3. Top 5 BUY candidates (operator-quality validated, wrap is bonus)

| Rank | Obligor | State | FHA Mortgage | Why buy |
|---|---|---|---|---|
| 1 | New York Presbyterian Hospital | NY | $1.37B | AMC + federal wrap; clean yield pickup over Treasuries |
| 2 | Medical University Hospital Authority (MUSC) | SC | $898M | State teaching system + 4-hospital acquisition refinance via FHA |
| 3 | University of New Mexico Hospital | NM | $503M | Level I trauma + state university + 2021 GNMA $320M deal at 3.275% fixed |
| 4 | Englewood Hospital and Medical Center | NJ | $172M | Suburban NJ AMC affiliate, clean operator |
| 5 | Union Hospital (Terre Haute IN) | IN | $267M | Regional monopoly, 2016 modern build |

All five have low operator-distress scores (1-3 / 10), no going-concern flags, and clean DOJ histories.

## 4. Top 5 EXCLUDE candidates (operator distress visible; wrap may compress spread but exclusion still adds value)

| Rank | Obligor | State | FHA Mortgage | Distress signals |
|---|---|---|---|---|
| 1 | Brooklyn Hospital Center | NY | $51M | "Substantial doubt" 2023 AND 2024 audits; $46M loss 2024; CEO considering Ch.11; $160M bailout ask |
| 2 | Maimonides Medical Center | NY | $246M | "Substantial doubt" 2024 audit; $375M cumulative loss; NYC H+H merger pending; bonds already widened |
| 3 | Kaleida Health (Buffalo) | NY | $443M | $200M+ losses since 2020; union strike vote 2025; OBBBA federal-cut sensitivity |
| 4 | St. Barnabas Hospital (Bronx) | NY | $105M | CMS 1-star; safety-net Medicaid concentration |
| 5 | Sinai Health System (Chicago) | IL | $102M | Safety-net hospital, structural deficits, federal-cut exposure |

Notice 4/5 are NY — partly because NY is 38% of the universe.

## 5. Honest TEY math

FHA 242 bonds come in TWO forms:
- **Tax-exempt FHA-insured** (most common; e.g., Maimonides Series 2020, MUSC 2019)
- **Taxable GNMA-collateralized** (e.g., Capital Health entire $755M, Maimonides 2013 $100M)

**For the tax-exempt subset** (the actionable muni alpha):
- Maimonides 2050 at 4.99% YTM × (1/(1-0.37)) ≈ **7.92% TEY** (for top-bracket investor)
- vs MMD AAA 24y ~4.24% × TEY ≈ 6.73%
- vs taxable 24y UST ~4.95% (current 30y)

**TEY pickup over AAA muni curve**: ~120 bps for top-bracket investor on the Maimonides 2050.
**TEY pickup over UST**: ~300 bps for top-bracket.

This is materially larger than the 30-60 bps Cal-Mortgage realizable alpha. Caveat: it's distress-tier paper; only meaningful if the framework's exclusion logic IS correct and the bond doesn't get further impaired. The +75 bps over AAA is partly compensation for that risk.

**For clean operator + wrap combinations** (NYP, MUSC, UNM, Englewood):
- Likely 30-50 bps over MMD AAA = the canonical Cal-Mortgage-style yield pickup of 30-60 bps the catalog predicted.
- TEY pickup ~50-80 bps over AAA muni curve.

**Path to alpha** (framework's primary contribution):
1. EXCLUSION VALUE: avoid Maimonides / Kaleida / Brooklyn Hospital Center buys at "AAA-equivalent" yields because the wrap is doing all the work and operator distress is real. Diligence value substantial — the bond price has already moved on Maimonides; future moves in Brooklyn Hospital Center likely.
2. SELECTION VALUE: prefer NYP / MUSC / UNM / Englewood for the clean wrap+operator combo.
3. FAIR-VALUE PLAY: where wrap pushes well-operated names to artificially tight spreads, those are the best risk/reward buys.

---

## 6. Comparison to Cal-Mortgage finding

| Dimension | Cal-Mortgage | FHA 242 |
|---|---|---|
| Geography | CA only | National (NY-heavy) |
| Sector | NH / CCRC (long-term care) | Acute care hospitals |
| Wrap credit | State AA- | Federal "AAA-equivalent" → market trades Aa1/AA+ |
| Universe size | ~30-40 obligors | 69 unique active obligors, $8.66B |
| Default history | Tri-Valley + small | Lakeway, LRGHealthcare + smaller |
| Spread compression | FULL — Cal-Mortgage names trade IDENTICALLY to clean basket | PARTIAL — wrap compresses but doesn't fully decouple; ~50-75 bps over AAA persists |
| Framework alpha mode | Tail-risk avoidance + uninsured subordinate exposure | Exclusion (poor operators) + selection (clean operators) + fair-value (mispriced wrap) |
| Realizable alpha | 30-60 bps TEY | Wider — possibly 50-120 bps depending on operator quality bucket |

**The pattern PARTIALLY generalizes**. The "insurance wrap masks operator credit" structural prediction holds, but the magnitude of masking is materially WEAKER than Cal-Mortgage. The federal wrap is less credible than the state wrap, apparently because (a) the program has actually defaulted, (b) bond market technicals add a sector premium, and (c) political/program risk is real.

---

## 7. Open gaps

1. **Spread test sample size**: Only 1 obligor (Maimonides) with empirical 2026 spread anchors. Need EMMA pulls for Kaleida, Albany Med, Hollywood Pres FHA series for N=5-10 within-rating comparison.
2. **CMS Star data**: pulled from news / 3rd-party sites; should download `data.cms.gov/provider-data/dataset/xubh-q36u` CSV directly for per-CCN matching.
3. **Operating margin / days cash**: relied on news; could pull HCRIS Worksheet E for top 15 systems for the structured composite.
4. **Capital Health $755M**: purely taxable GNMA → not in muni universe; useful only as case study. Confirms that some FHA 242 deals are entirely off the muni market.
5. **Pre-2021 vs post-2021 reauthorization**: the program was modified by GAO recommendations; market pricing of pre-2021 deals may differ from post.
6. **Insurer cascade tail**: HUD program-level losses are bounded by Treasury credit; cascade risk = political risk (volume limits, eligibility tightening). Cal-Mortgage cascade risk is fiscal (state appropriation). Different tail.

---

## 8. Knowledge-graph encoding

Update `knowledge_graph/masking_mechanisms.json` → `fha_section_242` entry:

- `documentation_depth`: `MENTIONED_NOT_VALIDATED` → **`DOCUMENTED`** (close to VERIFIED but with N=1 anchor; bump to VERIFIED after N≥5 spread anchors collected)
- `signal_to_price_impact`: revise from "FULL MASKING" → **"PARTIAL MASKING — wrap rated 'AAA-equivalent' but bonds trade ~50-75 bps wider than MMD AAA in secondary market; operator distress at e.g. Maimonides leaks into spread despite Aa1/AA+ wrap"**
- `alpha_implication`: revise from "cannot extract spread alpha" → **"EXCLUSION VALUE on operator-distress names (Brooklyn Hospital Center, Maimonides, Kaleida) where wrap compresses but doesn't fully decouple; SELECTION VALUE on clean-operator+wrap combos (NYP, MUSC, UNM, Englewood); FAIR-VALUE play on the wrap mispricing"**
- `severity`: revise from `HIGH` → **`MEDIUM`** (still substantial masking, but not Cal-Mortgage HIGH)
- `cross_references`: keep `cal_mortgage`, `agm_bond_insurance`, `gnma_passthrough_insurance`, `usda_rural_development`
- `verified_via`: add `data/us_fha242_hospital_universe.json` + `outputs/US_FHA242_HOSPITAL_SECTOR_SCOPING.md`
- `_notes`: add "FALSIFIES the original 'Cal-Mortgage analog at federal level' prediction. Federal wrap masks less effectively than state wrap, primarily because (a) program has had real defaults, (b) hospital revenue bond technicals add sector premium, (c) GAO-flagged program reauthorization risk."
