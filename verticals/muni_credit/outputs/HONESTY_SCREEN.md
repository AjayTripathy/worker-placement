# Hospital Muni — R/f/M Honesty Screen

Programmatic check of MD&A documents for the four Mode B framing patterns surfaced in the Ascension 2024A R/f/M divergence report. Each check is a deterministic regex/text-pattern test on the pdftotext-extracted MD&A text — no LLM. Any analyst can re-derive these flags by grepping the source PDF.

## Four checks
1. **Rating-action acknowledgment** — does MD&A discuss recent Moody's/S&P/Fitch actions?
2. **Operating-margin disclosure** — explicit operating margin % stated, or hidden behind revenue/expense narrative?
3. **Same-facility framing density** — heavy 'same-facility' framing can obscure consolidated GAAP decline through divestitures
4. **Investment-income masking** — using investment gains to frame operational 'improvement'?

Scoring: 0-100 per check (higher = more honest). Aggregate is unweighted average.

## Ranking

| Rank | Obligor | Aggregate | Red flags | Tier |
|---|---|---|---|---|
| 1 | allina | 100.0 | 0 | ✅ HONEST |
| 2 | uchealth | 100.0 | 0 | ✅ HONEST |
| 3 | corewell | 92.5 | 0 | ✅ HONEST |
| 4 | rwjbarnabas | 92.5 | 0 | ✅ HONEST |
| 5 | nyu_langone | 87.5 | 0 | ✅ HONEST |
| 6 | cleveland_clinic | 82.5 | 1 | 🟡 MIXED |
| 7 | trinity_health | 81.2 | 0 | ✅ HONEST |
| 8 | adventist_health | 80.0 | 0 | ✅ HONEST |
| 9 | advocate_health | 75.0 | 1 | 🟡 MIXED |
| 10 | atrium_health | 75.0 | 1 | 🟡 MIXED |
| 11 | commonspirit | 75.0 | 1 | 🟡 MIXED |
| 12 | iu_health | 75.0 | 1 | 🟡 MIXED |
| 13 | mass_general_brigham | 75.0 | 1 | 🟡 MIXED |
| 14 | mgb | 75.0 | 1 | 🟡 MIXED |
| 15 | nyp | 75.0 | 1 | 🟡 MIXED |
| 16 | providence | 75.0 | 1 | 🟡 MIXED |
| 17 | unc_health_test | 75.0 | 1 | 🟡 MIXED |
| 18 | upmc | 75.0 | 1 | 🟡 MIXED |
| 19 | yale_new_haven | 75.0 | 1 | 🟡 MIXED |
| 20 | sanford | 72.5 | 1 | 🟡 MIXED |
| 21 | duke_health | 70.0 | 1 | 🟡 MIXED |
| 22 | bjc | 67.5 | 1 | 🟡 MIXED |
| 23 | lehigh_valley | 67.5 | 1 | 🟡 MIXED |
| 24 | lifespan | 67.5 | 1 | 🟡 MIXED |
| 25 | multicare | 67.5 | 1 | 🟡 MIXED |
| 26 | wellstar | 67.5 | 1 | 🟡 MIXED |
| 27 | ssm_health | 65.0 | 1 | 🟡 MIXED |
| 28 | cedars_sinai | 63.8 | 0 | 🟡 MIXED |
| 29 | avera | 60.0 | 1 | 🟡 MIXED |
| 30 | baptist_health_florida | 60.0 | 1 | 🟡 MIXED |
| 31 | christianacare | 60.0 | 1 | 🟡 MIXED |
| 32 | memorial_sloan_kettering | 60.0 | 1 | 🟡 MIXED |
| 33 | msk | 60.0 | 1 | 🟡 MIXED |
| 34 | sutter | 60.0 | 1 | 🟡 MIXED |
| 35 | texas_childrens | 60.0 | 1 | 🟡 MIXED |
| 36 | banner_health | 57.5 | 1 | 🟡 MIXED |
| 37 | johns_hopkins | 57.5 | 1 | 🟡 MIXED |
| 38 | kaiser | 57.5 | 1 | 🟡 MIXED |
| 39 | hackensack_meridian | 56.2 | 1 | 🟡 MIXED |
| 40 | allegheny_health | 55.0 | 2 | 🟡 MIXED |
| 41 | bon_secours | 55.0 | 2 | 🟡 MIXED |
| 42 | boston_childrens | 55.0 | 2 | 🟡 MIXED |
| 43 | chop | 55.0 | 2 | 🟡 MIXED |
| 44 | henry_ford | 55.0 | 2 | 🟡 MIXED |
| 45 | intermountain_test | 55.0 | 2 | 🟡 MIXED |
| 46 | memorial_hermann | 55.0 | 2 | 🟡 MIXED |
| 47 | mount_sinai | 55.0 | 2 | 🟡 MIXED |
| 48 | northwell | 55.0 | 2 | 🟡 MIXED |
| 49 | penn_medicine | 55.0 | 2 | 🟡 MIXED |
| 50 | childrens_atlanta | 52.5 | 2 | 🟡 MIXED |
| 51 | geisinger | 52.5 | 2 | 🟡 MIXED |
| 52 | norton_healthcare | 52.5 | 2 | 🟡 MIXED |
| 53 | stanford_health | 52.5 | 2 | 🟡 MIXED |
| 54 | adventhealth | 50.0 | 1 | 🟡 MIXED |
| 55 | carilion | 50.0 | 2 | 🟡 MIXED |
| 56 | centura | 50.0 | 2 | 🟡 MIXED |
| 57 | chla | 50.0 | 2 | 🟡 MIXED |
| 58 | mayo_clinic | 50.0 | 1 | 🟡 MIXED |
| 59 | tower_health | 50.0 | 2 | 🟡 MIXED |
| 60 | loma_linda | 48.8 | 1 | 🔴 SUSPECT |
| 61 | bilh | 45.0 | 2 | 🔴 SUSPECT |
| 62 | houston_methodist | 45.0 | 2 | 🔴 SUSPECT |
| 63 | ascension | 35.0 | 2 | 🔴 SUSPECT |

## Per-check scores

| Obligor | Rating ack. | Op margin disc. | Same-facility | Inv-income mask |
|---|---|---|---|---|
| allina | 100 | 100 | 100 | 100 |
| uchealth | 100 | 100 | 100 | 100 |
| corewell | 100 | 100 | 100 | 70 |
| rwjbarnabas | 100 | 100 | 100 | 70 |
| nyu_langone | 50 | 100 | 100 | 100 |
| cleveland_clinic | 100 | 100 | 100 | 30 |
| trinity_health | 25 | 100 | 100 | 100 |
| adventist_health | 50 | 100 | 100 | 70 |
| advocate_health | 0 | 100 | 100 | 100 |
| atrium_health | 0 | 100 | 100 | 100 |
| commonspirit | 0 | 100 | 100 | 100 |
| iu_health | 0 | 100 | 100 | 100 |
| mass_general_brigham | 0 | 100 | 100 | 100 |
| mgb | 0 | 100 | 100 | 100 |
| nyp | 0 | 100 | 100 | 100 |
| providence | 0 | 100 | 100 | 100 |
| unc_health_test | 0 | 100 | 100 | 100 |
| upmc | 0 | 100 | 100 | 100 |
| yale_new_haven | 0 | 100 | 100 | 100 |
| sanford | 0 | 90 | 100 | 100 |
| duke_health | 0 | 80 | 100 | 100 |
| bjc | 0 | 70 | 100 | 100 |
| lehigh_valley | 0 | 70 | 100 | 100 |
| lifespan | 0 | 100 | 100 | 70 |
| multicare | 0 | 100 | 100 | 70 |
| wellstar | 0 | 70 | 100 | 100 |
| ssm_health | 0 | 90 | 100 | 70 |
| cedars_sinai | 25 | 30 | 100 | 100 |
| avera | 0 | 40 | 100 | 100 |
| baptist_health_florida | 0 | 40 | 100 | 100 |
| christianacare | 0 | 40 | 100 | 100 |
| memorial_sloan_kettering | 0 | 40 | 100 | 100 |
| msk | 0 | 40 | 100 | 100 |
| sutter | 0 | 40 | 100 | 100 |
| texas_childrens | 0 | 70 | 100 | 70 |
| banner_health | 0 | 30 | 100 | 100 |
| johns_hopkins | 0 | 30 | 100 | 100 |
| kaiser | 0 | 30 | 100 | 100 |
| hackensack_meridian | 25 | 0 | 100 | 100 |
| allegheny_health | 0 | 20 | 100 | 100 |
| bon_secours | 0 | 90 | 100 | 30 |
| boston_childrens | 0 | 20 | 100 | 100 |
| chop | 0 | 20 | 100 | 100 |
| henry_ford | 0 | 20 | 100 | 100 |
| intermountain_test | 0 | 20 | 100 | 100 |
| memorial_hermann | 0 | 20 | 100 | 100 |
| mount_sinai | 0 | 20 | 100 | 100 |
| northwell | 0 | 20 | 100 | 100 |
| penn_medicine | 0 | 20 | 100 | 100 |
| childrens_atlanta | 0 | 10 | 100 | 100 |
| geisinger | 0 | 10 | 100 | 100 |
| norton_healthcare | 0 | 10 | 100 | 100 |
| stanford_health | 0 | 10 | 100 | 100 |
| adventhealth | 0 | 30 | 100 | 70 |
| carilion | 0 | 0 | 100 | 100 |
| centura | 0 | 0 | 100 | 100 |
| chla | 0 | 0 | 100 | 100 |
| mayo_clinic | 0 | 30 | 100 | 70 |
| tower_health | 0 | 0 | 100 | 100 |
| loma_linda | 25 | 0 | 100 | 70 |
| bilh | 0 | 10 | 100 | 70 |
| houston_methodist | 0 | 10 | 100 | 70 |
| ascension | 0 | 10 | 60 | 70 |

## Detailed findings per obligor

### ✅ allina — score 100.0, HONEST

- **rating_action_acknowledgment** (100/100): GREEN
  - 11 agency mentions, 251 action terms, 10 co-occurrences
  - Sample: `...Credit Ratings Participation In August 2023, Allina Health announced it ended its engagement with Moody’s Investor Services (Moody’s) for the rating of Allina Health bonds. The decision to end Moody’s...`
  - Sample: `...on In August 2023, Allina Health announced it ended its engagement with Moody’s Investor Services (Moody’s) for the rating of Allina Health bonds. The decision to end Moody’s engagement was based on A...`
  - Sample: `...with Moody’s Investor Services (Moody’s) for the rating of Allina Health bonds. The decision to end Moody’s engagement was based on Allina Health’s initiatives to reduce expenses and a determination t...`
- **operating_margin_disclosure** (100/100): GREEN
  - 4 explicit % disclosures, 9 op income/loss mentions
  - Sample: `...39 Management’s Discussion and Analysis of Results of Operations Operating Results Allina Health’s operating margin before restructuring expenses was -1.4% for the three months ended March 31, 2024, c...`
  - Sample: `...3.5% -2.6% -1.0% 1.8% Operating Margin -1.4% -8.1% -6.2% -3.4% Net Income Margin...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 18129 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### ✅ uchealth — score 100.0, HONEST

- **rating_action_acknowledgment** (100/100): GREEN
  - 13 agency mentions, 372 action terms, 13 co-occurrences
  - Sample: `...0 to the basic financial statements. In July 2024, UCHealth completed an annual ratings update with Moody’s, Standard & Poor’s, and Fitch Ratings to rate the member organizations. Moody’s maintained i...`
  - Sample: `...ratings update with Moody’s, Standard & Poor’s, and Fitch Ratings to rate the member organizations. Moody’s maintained its UCHA rating at Aa2 Stable. Standard & Poor’s maintained its rating at AA Stab...`
  - Sample: `...ents at June 30, 2024 and 2023. The ratings are presented as the lower of Standard & Poor’s or Moody’s rating using the S&P scale: 2024...`
- **operating_margin_disclosure** (100/100): GREEN
  - 0 explicit % disclosures, 10 op income/loss mentions
  - Sample: `...erating expenses 2,830,640 2,585,144 2,283,327 Operating Income 294,951 271,012 236,797 Nonoperating Revenue (Expense) Investment income (loss)...`
  - Sample: `.... Purchased services and other expenses of $735,019 increased over 2023 by $43,984, or 6.4 percent. Operating income was $294,951 during the fiscal year, which is an 8.8 percent increase from 2023 ope...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 27133 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### ✅ corewell — score 92.5, HONEST

- **rating_action_acknowledgment** (100/100): GREEN
  - 19 agency mentions, 223 action terms, 12 co-occurrences
  - Sample: `...ition, results of operations and cash flows. For benchmarking purposes, we utilize a 5-year average Moody’s median (Moody’s median) throughout the MD&A below, which are calculated medians for healthca...`
  - Sample: `...f operations and cash flows. For benchmarking purposes, we utilize a 5-year average Moody’s median (Moody’s median) throughout the MD&A below, which are calculated medians for healthcare systems with ...`
  - Sample: `...iod last year. Care Delivery continues to experience a higher government payer mix compared to the Moody’s median due to the population demographics in the State of Michigan. Additionally, the Moody’s...`
- **operating_margin_disclosure** (100/100): GREEN
  - 1 explicit % disclosures, 5 op income/loss mentions
  - Sample: `...2024 S&P Moody's Profitability Ratios Operating margin 1.6% 1.3% 2.7% 2.0% Total margin...`
  - Sample: `...ng margin through December 31, 2025 was $34.9 million or 0.4%, which is higher than previous year’s operating loss of (0.7)%. Similar to other insurers, Priority Health’s medical costs were elevated d...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 21159 words = 0.0/1k
- **investment_income_masking** (70/100): YELLOW — some investment-income framing (could be legitimate)
  - 1 investment-income-as-improvement passages
  - Sample: `...tive investments include hedge funds, private capital, and real estate. Hedge funds seek to produce positive investment returns regardless of market direction. These investments utilize multi-strategy...`

### ✅ rwjbarnabas — score 92.5, HONEST

- **rating_action_acknowledgment** (100/100): GREEN
  - 10 agency mentions, 191 action terms, 8 co-occurrences
  - Sample: `...g for the short-term liquidity program, the highest rating that could be assigned. In August 2025, Moody’s affirmed its A1 credit rating with a stable outlook. The A1 affirmation reflects “the Corpora...`
  - Sample: `...ey’s only NCI-designated cancer center—key differentiators in competitive markets.” Simultaneously, Moody’s affirmed its P-1 short-term liquidity rating, the highest rating that could be assigned. Thi...`
  - Sample: `...(ALICE) neighborhoods through employment and training opportunities. Credit Ratings In July 2025, S&P affirmed its AA- long-term rating with a stable outlook. S&P notes that “the rating reflects the b...`
- **operating_margin_disclosure** (100/100): GREEN
  - 3 explicit % disclosures, 7 op income/loss mentions
  - Sample: `...rating income 708,886 290,665 92,296 Operating margin 6.4% 3.0% 2.3% Operating cash flow 1,213,...`
  - Sample: `...5.6x For the year ended December 31, 2025, the Corporation’s total operating income and operating margin were $708,886 and 6.4%, respectively, compared to the operating income and operating margin of ...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 15694 words = 0.0/1k
- **investment_income_masking** (70/100): YELLOW — some investment-income framing (could be legitimate)
  - 1 investment-income-as-improvement passages
  - Sample: `...vities for the years ended December 31 2025 and 2024 was $1,032,103 and $794,740, respectively. Net investment income of $597,623 had a positive impact on investments. Borrowing under the commercial p...`

### ✅ nyu_langone — score 87.5, HONEST

- **rating_action_acknowledgment** (50/100): YELLOW
  - 2 agency mentions, 236 action terms, 2 co-occurrences
  - Sample: `...ons regarding the merger and LICH’s outstanding indebtedness. Rating Affirmation In February 2025, Moody’s reaffirmed its A1 rating with a stable outlook for NYU Langone Hospitals’ outstanding long- t...`
  - Sample: `...g with a stable outlook for NYU Langone Hospitals’ outstanding long- term debt. In September 2024, S&P Global Ratings affirmed its A+ rating with a stable outlook for NYU Langone Hospitals’ out- stand...`
- **operating_margin_disclosure** (100/100): GREEN
  - 26 explicit % disclosures, 2 op income/loss mentions
  - Sample: `...120.0 147.8 (27.8) (18.8)% Operating margin 3.0% 4.0% (unaudit...`
  - Sample: `...482.8 431.4 51.4 11.9% Operating margin 3.1% 3.1% Rendering of the future Julia Koch Family Ambulatory...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 22159 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 cleveland_clinic — score 82.5, MIXED

- **rating_action_acknowledgment** (100/100): GREEN
  - 8 agency mentions, 419 action terms, 8 co-occurrences
  - Sample: `...anding bonds have been assigned ratings of Aa2 (stable outlook) and AA (stable outlook) by Moody’s and S&P, respectively. In March 2026, S&P affirmed its AA rating on the obligated group’s outsta...`
  - Sample: `...ital spending program and a highly competitive service areas throughout the System. In March 2026, Moody’s affirmed its Aa2 rating on the obligated group’s outstanding debt and maintained its stable o...`
  - Sample: `...ffirmed its Aa2 rating on the obligated group’s outstanding debt and maintained its stable outlook. Moody’s cited various factors to support this rating and outlook, including a national and internati...`
- **operating_margin_disclosure** (100/100): GREEN
  - 14 explicit % disclosures, 27 op income/loss mentions
  - Sample: `...year of 2025 was $913 million on total unrestricted revenues of $18.3 billion, resulting in a 5.0% operating margin, as compared to operating income of $276 million and a 1.7% operating margin in 2024...`
  - Sample: `...arter of 2025 was $399 million on total unrestricted revenues of $5.0 billion, resulting in an 8.0% operating margin, as compared to operating income of $137 million and a 3.3% operating margin in the...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 39530 words = 0.0/1k
- **investment_income_masking** (30/100): RED — 3 investment-income-as-improvement passages; pattern of operational masking
  - 3 investment-income-as-improvement passages
  - Sample: `...endowment assets held in perpetuity or for a specified term, as well as to provide additional real growth through new gifts and investment return. 3/30/2026...`
  - Sample: `...rest rate swap agreements, including net interest paid or received under the swap agreements. Other nonoperating gains and losses were unfavorable by $7.1 million in the fourth quarter of 2025 compare...`

### ✅ trinity_health — score 81.2, HONEST

- **rating_action_acknowledgment** (25/100): YELLOW
  - 1 agency mentions, 57 action terms, 1 co-occurrences
  - Sample: `...(unaudited) ASSETS Daily Liquidity Money Market Funds (Moody's rated Aaa) $ 742 Checking and Deposit Accoun...`
- **operating_margin_disclosure** (100/100): GREEN
  - 1 explicit % disclosures, 11 op income/loss mentions
  - Sample: `...211% 197% Profitability Ratios (For the year ended June 30) Operating Margin before Other Items 0.8% 0.3% Operating Cash Flow Margin before Other Items 5.3%...`
  - Sample: `...5.2 percent operating cash flow margin before other items for the year ended June 30, 2024. • Operating income before other items of $197 million, or 0.8 percent operating margin before other items; c...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 4355 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### ✅ adventist_health — score 80.0, HONEST

- **rating_action_acknowledgment** (50/100): YELLOW
  - 2 agency mentions, 150 action terms, 2 co-occurrences
  - Sample: `...aded its long‐term rating from A to BBB+ and revised the outlook from Negative to Stable, and S&P Global Ratings downgraded its long‐term rating from A‐ to BBB+ and revised the outlook from Stable...`
  - Sample: `...11.5% 3.5% revenue Ratings and Outlook Updates In May 2024, Fitch Ratings downgraded its long‐term rating from A to BBB+ and revised the outlook from Negative to...`
- **operating_margin_disclosure** (100/100): GREEN
  - 0 explicit % disclosures, 27 op income/loss mentions
  - Sample: `...ons (224) (108) Nonoperating income: Net realized and unrealized gains on investments 119 156 (Loss) gain on acquisitions and divestures...`
  - Sample: `...ons and divestures (6) 80 Other nonoperating loss (8) (12) Total nonoperating income 1...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 18634 words = 0.0/1k
- **investment_income_masking** (70/100): YELLOW — some investment-income framing (could be legitimate)
  - 1 investment-income-as-improvement passages
  - Sample: `...ays cash on hand increased to 137.5 on December 31, 2024 from 131.7 at December 31, 2023, driven by investment returns due to strong market performance and proceeds from excess capacity payment relate...`

### 🟡 advocate_health — score 75.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 50 action terms, 0 co-occurrences
- **operating_margin_disclosure** (100/100): GREEN
  - 2 explicit % disclosures, 32 op income/loss mentions
  - Sample: `...2025 2024 Operating Performance Operating margin(1) 3.2% 1.4% Operating cash flow margin(2)...`
  - Sample: `...2025 2024 Operating Performance Operating margin(1) 3.2% 2.2% Operating cash flow margin(2)...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 9608 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 atrium_health — score 75.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 50 action terms, 0 co-occurrences
- **operating_margin_disclosure** (100/100): GREEN
  - 2 explicit % disclosures, 32 op income/loss mentions
  - Sample: `...2025 2024 Operating Performance Operating margin(1) 3.2% 1.4% Operating cash flow margin(2)...`
  - Sample: `...2025 2024 Operating Performance Operating margin(1) 3.2% 2.2% Operating cash flow margin(2)...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 9608 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 commonspirit — score 75.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 244 action terms, 0 co-occurrences
- **operating_margin_disclosure** (100/100): GREEN
  - 0 explicit % disclosures, 13 op income/loss mentions
  - Sample: `...n a non-GAAP basis for EBITDA (earnings before interest, tax, depreciation and amortization, and nonoperating income). The non-GAAP financial measures are in addition to, not a substitute for, measure...`
  - Sample: `...perations among current, past and future periods. Financial Highlights and Summary CommonSpirit’s operating loss was $687 million during the year ended June 30, 2025, compared to an operating loss of ...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 22938 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 iu_health — score 75.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 133 action terms, 0 co-occurrences
- **operating_margin_disclosure** (100/100): GREEN
  - 0 explicit % disclosures, 13 op income/loss mentions
  - Sample: `...Total operating expenses 8,966,754 8,300,765 Operating income 256,597 343,121 Nonoperating income (loss): Investment income, net...`
  - Sample: `...ating income 256,597 343,121 Nonoperating income (loss): Investment income, net 900,653 931,205 (Losses) gains on interest rate swaps, net (5,13...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 16429 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 mass_general_brigham — score 75.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 3 agency mentions, 90 action terms, 0 co-occurrences
- **operating_margin_disclosure** (100/100): GREEN
  - 5 explicit % disclosures, 9 op income/loss mentions
  - Sample: `...and prior year activity, Mass General Brigham generated income from operations of $58 million (0.3% operating margin) in 2025 and a loss from operations of $72 million in 2024 (-0.4% operating margin)...`
  - Sample: `...arge and prior year activity, Mass General Brigham generated income from operations of $58 million (0.3% operating margin) in 2025 and a loss from operations of $72 million in 2024 (-0.4% operating ma...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 6013 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 mgb — score 75.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 3 agency mentions, 90 action terms, 0 co-occurrences
- **operating_margin_disclosure** (100/100): GREEN
  - 5 explicit % disclosures, 9 op income/loss mentions
  - Sample: `...and prior year activity, Mass General Brigham generated income from operations of $58 million (0.3% operating margin) in 2025 and a loss from operations of $72 million in 2024 (-0.4% operating margin)...`
  - Sample: `...arge and prior year activity, Mass General Brigham generated income from operations of $58 million (0.3% operating margin) in 2025 and a loss from operations of $72 million in 2024 (-0.4% operating ma...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 6013 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 nyp — score 75.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 336 action terms, 0 co-occurrences
- **operating_margin_disclosure** (100/100): GREEN
  - 1 explicit % disclosures, 11 op income/loss mentions
  - Sample: `...$96,881 $445,282 Total operating margin 3.6% 4.2% Source: Three Months Ended March 31, 2025 Unaudited Financial Stat...`
  - Sample: `...ses 2,615,823 2,508,054 Operating income 96,881 112,482 Investment return – net 14,09...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 28311 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 providence — score 75.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 275 action terms, 0 co-occurrences
- **operating_margin_disclosure** (100/100): GREEN
  - 0 explicit % disclosures, 15 op income/loss mentions
  - Sample: `...sale of its clinical engineering department to Trimedx. At closing, a net gain was reported within operating income, consistent with the treatment of similar disposals. In December 2025, Tegria Holdin...`
  - Sample: `...hree months ended December 31, 2024 Non-operating gains were $81 million, compared with non-operating losses of $28 million in 2024. The increase was driven by higher investment gains of $95 million, ...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 28761 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 unc_health_test — score 75.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 3 agency mentions, 90 action terms, 0 co-occurrences
- **operating_margin_disclosure** (100/100): GREEN
  - 5 explicit % disclosures, 9 op income/loss mentions
  - Sample: `...and prior year activity, Mass General Brigham generated income from operations of $58 million (0.3% operating margin) in 2025 and a loss from operations of $72 million in 2024 (-0.4% operating margin)...`
  - Sample: `...arge and prior year activity, Mass General Brigham generated income from operations of $58 million (0.3% operating margin) in 2025 and a loss from operations of $72 million in 2024 (-0.4% operating ma...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 6013 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 upmc — score 75.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 174 action terms, 0 co-occurrences
- **operating_margin_disclosure** (100/100): GREEN
  - 3 explicit % disclosures, 12 op income/loss mentions
  - Sample: `...$ 218 $ 68 $ - $ 286 Operating margin % 1.2% 0.4% - 0.9% Operating margin % (including income...`
  - Sample: `...$ 167 $ (506) $ - $ (339) Operating margin % 1.0% (3.2)% - (1.1)% Operating margin % (including income...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 21938 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 yale_new_haven — score 75.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 219 action terms, 0 co-occurrences
- **operating_margin_disclosure** (100/100): GREEN
  - 0 explicit % disclosures, 11 op income/loss mentions
  - Sample: `...7,419,245 6,950,993 Operating income before depreciation, amortization, interest, and restructuring expenses 160,3...`
  - Sample: `...831 56,646 (1,611,349) 7,419,245 (472,193) 6,947,052 Operating income (loss) before depreciation, amortization, interest, and restructuring expenses 42,162 1,422 141,258 (32,583)...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 22535 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 sanford — score 72.5, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 316 action terms, 0 co-occurrences
- **operating_margin_disclosure** (90/100): GREEN
  - 0 explicit % disclosures, 9 op income/loss mentions
  - Sample: `...l other investment return, including realized and unrealized gains and losses, are recorded as non- operating income (expense), unless restricted by donors. Investment return with donor restrictions i...`
  - Sample: `...lassified and reported as net assets released from restrictions within other operating revenue, non-operating income (expense), or releases for acquisitions of property and equipment. 2505-11958-CS...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 21395 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 duke_health — score 70.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 1 agency mentions, 160 action terms, 0 co-occurrences
- **operating_margin_disclosure** (80/100): GREEN
  - 0 explicit % disclosures, 8 op income/loss mentions
  - Sample: `...Total expenses 7,105,720 6,619,243 Operating income 178,969 202,689 Nonoperating income (loss): Net investment income...`
  - Sample: `...Operating income 178,969 202,689 Nonoperating income (loss): Net investment income 400,458 404,012 Nonoperating components of net periodic benefit cost 67,254...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 16580 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 bjc — score 67.5, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 145 action terms, 0 co-occurrences
- **operating_margin_disclosure** (70/100): YELLOW
  - 0 explicit % disclosures, 7 op income/loss mentions
  - Sample: `...38.5 Total expenses 5,267.5 4,838.8 Operating income 59.4 154.3 Investment earnings, net 54.7 4...`
  - Sample: `...roups of assets, which generally is at the hospital level. Impairment write-downs are recognized in operating income at the time the impairment is identified. Net Assets Net Assets Without Donor Restr...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 14617 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 lehigh_valley — score 67.5, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 123 action terms, 0 co-occurrences
- **operating_margin_disclosure** (70/100): YELLOW
  - 0 explicit % disclosures, 7 op income/loss mentions
  - Sample: `...2025 2024 Investment income included in operating income (losses): Interest and dividends $29,094 $43,911 Endowment payout 236,616...`
  - Sample: `...$270,625 $199,427 Investment income included in nonoperating income (losses): Net realized and unrealized gains (losses) 331,098 247,633 Interest and dividends 41,723...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 15689 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 lifespan — score 67.5, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 34 action terms, 0 co-occurrences
- **operating_margin_disclosure** (100/100): GREEN
  - 0 explicit % disclosures, 13 op income/loss mentions
  - Sample: `...Brown Health of $3,278.8 million. The operating margin for Rhode Island was $76.0 million while the operating loss for Massachusetts was ($53.3 million), resulting in an overall operating margin of $2...`
  - Sample: `...Brown Health of $1,125.8 million. The operating margin for Rhode Island was $28.4 million while the operating loss for Massachusetts was ($32.2 million), resulting in an overall operating loss of ($3....`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 6092 words = 0.0/1k
- **investment_income_masking** (70/100): YELLOW — some investment-income framing (could be legitimate)
  - 1 investment-income-as-improvement passages
  - Sample: `...2025, from $1,919.6 million at September 30, 2024. The increase reflects bond proceeds received and favorable investment returns for the nine months ended June 30, 2025, less funds requisitioned. Othe...`

### 🟡 multicare — score 67.5, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 516 action terms, 0 co-occurrences
- **operating_margin_disclosure** (100/100): GREEN
  - 0 explicit % disclosures, 16 op income/loss mentions
  - Sample: `...1,433,731 1,359,705 5,751,176 5,137,486 Operating loss (75,192) (19,398) (100,586) (188,471) Nonoperating income (loss): Invest...`
  - Sample: `...(75,192) (19,398) (100,586) (188,471) Nonoperating income (loss): Investment (loss) income 24,809 98,730 214,783 282,866 Inherent contribution*...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 45801 words = 0.0/1k
- **investment_income_masking** (70/100): YELLOW — some investment-income framing (could be legitimate)
  - 2 investment-income-as-improvement passages
  - Sample: `...e purchasing power of the endowment assets held in perpetuity, as well as to provide additional growth through new gifts and investment returns....`
  - Sample: `...e purchasing power of the endowment assets held in perpetuity, as well as to provide additional growth through new gifts and investment returns....`

### 🟡 wellstar — score 67.5, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 192 action terms, 0 co-occurrences
- **operating_margin_disclosure** (70/100): YELLOW
  - 0 explicit % disclosures, 7 op income/loss mentions
  - Sample: `...al expenses 6,220,366 4,647,889 Operating income, before FEMA funding for operating expenses and unrestricted contribution received i...`
  - Sample: `...ntribution received in business combination 163,125 — Operating income before impairment losses 495,138 212,630 Impairment of long-lived assets (4,495) (2,...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 19891 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 ssm_health — score 65.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 166 action terms, 0 co-occurrences
- **operating_margin_disclosure** (90/100): GREEN
  - 0 explicit % disclosures, 9 op income/loss mentions
  - Sample: `...OTHER ITEMS: Long-lived asset impairment - (33,096) OPERATING LOSS AFTER OTHER ITEMS (69,972) (59,491) NONOPERATING GAINS AND (LOSSES): Investment income 273,7...`
  - Sample: `...the financial reporting basis and the tax basis of their assets and liabilities along with net operating losses that meet the more likely than not recognition criteria. Changes in recognition or measu...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 16937 words = 0.0/1k
- **investment_income_masking** (70/100): YELLOW — some investment-income framing (could be legitimate)
  - 1 investment-income-as-improvement passages
  - Sample: `...urchasing power of the endowment assets held in perpetuity as well as to provide additional real growth through new gifts and investment return. 17. DERIVATIVE INSTRUMENTS SSMH utilizes various intere...`

### 🟡 cedars_sinai — score 63.8, MIXED

- **rating_action_acknowledgment** (25/100): YELLOW
  - 1 agency mentions, 323 action terms, 1 co-occurrences
  - Sample: `...five-year period is to produce a rate of return that equals or exceeds the appropriate bond index, Standard & Poor’s 500 Stock Index, or other appropriate international equity indices. As part of inve...`
- **operating_margin_disclosure** (30/100): YELLOW
  - 0 explicit % disclosures, 3 op income/loss mentions
  - Sample: `...17,651 Total expenses 7,134,461 6,693,157 Income from operations 143,148 259,201 Investment income (loss)...`
  - Sample: `...udited) Total revenues $ 6,952,358 $ 6,972,971 Income from operations 259,201 256,605 Excess (deficiency) of revenues ov...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 44626 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 avera — score 60.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 293 action terms, 0 co-occurrences
- **operating_margin_disclosure** (40/100): YELLOW
  - 0 explicit % disclosures, 4 op income/loss mentions
  - Sample: `...l expenses 3,044,587 2,857,477 Operating Income 182,752 45,513 Other Income (Expense) Investment income - realized...`
  - Sample: `...er. Distributions from investments in affiliated organizations recorded at cost are recorded as non-operating income....`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 27007 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 baptist_health_florida — score 60.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 217 action terms, 0 co-occurrences
- **operating_margin_disclosure** (40/100): YELLOW
  - 0 explicit % disclosures, 4 op income/loss mentions
  - Sample: `...assets, management considers all available positive and negative evidence primarily relating to net operating loss carryovers, deferred compensation accruals, and bad debt allowances. As of September ...`
  - Sample: `...change in the valuation allowance was $40,381. As of September 30, 2024, BHS had an available net operating loss carryforward of $603,660. Management believes that it is more likely than not that the ...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 17430 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 christianacare — score 60.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 199 action terms, 0 co-occurrences
- **operating_margin_disclosure** (40/100): YELLOW
  - 0 explicit % disclosures, 4 op income/loss mentions
  - Sample: `...ly amortized. Other components of net periodic pension cost, which are presented in other nonoperating losses, revenues, and gains on the consolidated statement of operations and changes in net assets...`
  - Sample: `...vely. Other components of net periodic postretirement benefit cost, which are presented in other nonoperating losses, revenues, and gains on the consolidated statement of operations and changes in net...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 18825 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 memorial_sloan_kettering — score 60.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 229 action terms, 0 co-occurrences
- **operating_margin_disclosure** (40/100): YELLOW
  - 0 explicit % disclosures, 4 op income/loss mentions
  - Sample: `...e (loss) from operations 134,277 (248,052) Nonoperating income and expenses – net Investment returns, net of expenses, allocations to operations and amounts recorded in net assets with donor restricti...`
  - Sample: `...ponents of net periodic benefit credits 37,497 69,136 Other nonoperating income and expenses – net 1,369 (10,361) Total nonoperating income and expenses – net 371,733 (873,31...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 23909 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 msk — score 60.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 229 action terms, 0 co-occurrences
- **operating_margin_disclosure** (40/100): YELLOW
  - 0 explicit % disclosures, 4 op income/loss mentions
  - Sample: `...e (loss) from operations 134,277 (248,052) Nonoperating income and expenses – net Investment returns, net of expenses, allocations to operations and amounts recorded in net assets with donor restricti...`
  - Sample: `...ponents of net periodic benefit credits 37,497 69,136 Other nonoperating income and expenses – net 1,369 (10,361) Total nonoperating income and expenses – net 371,733 (873,31...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 23909 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 sutter — score 60.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 117 action terms, 0 co-occurrences
- **operating_margin_disclosure** (40/100): YELLOW
  - 0 explicit % disclosures, 4 op income/loss mentions
  - Sample: `...18,065 Income from operations 509 142 Nonoperating income: Investment income, net 1,364 771 Other components of net periodic postretirement cost...`
  - Sample: `...116 Other (73) (21) Total nonoperating income, net 1,350 866 Net income 1,859 1,008 Less income attributable to noncontrolling interests...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 12899 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 texas_childrens — score 60.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 220 action terms, 0 co-occurrences
- **operating_margin_disclosure** (70/100): YELLOW
  - 0 explicit % disclosures, 7 op income/loss mentions
  - Sample: `...3 For the twelve months ended September 30, 2024, Texas Children’s operating loss was $467.9 million, a decrease of $582.3 million compared to prior year operating income of $114.4 million. T...`
  - Sample: `...s Children’s operating loss was $467.9 million, a decrease of $582.3 million compared to prior year operating income of $114.4 million. Texas Children’s operating cash flow, which is calculated by add...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 22385 words = 0.0/1k
- **investment_income_masking** (70/100): YELLOW — some investment-income framing (could be legitimate)
  - 1 investment-income-as-improvement passages
  - Sample: `...ment assets held in perpetuity or for a specific term, as well as to provide additional real growth through new gifts and investment return. From time to time, the fair value of assets associated with...`

### 🟡 banner_health — score 57.5, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 170 action terms, 0 co-occurrences
- **operating_margin_disclosure** (30/100): YELLOW
  - 0 explicit % disclosures, 3 op income/loss mentions
  - Sample: `...529,241 Total expenses 10,086,184 9,226,290 Operating income 310,927 200,358 Other income (loss): Investment income – realized 56,807...`
  - Sample: `...2020 and 2019, were $117,666,000 and $113,839,000, respectively, and primarily relate to BHN’s net operating loss carryforwards. Banner has established a valuation allowance equal to the deferred tax ...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 12321 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 johns_hopkins — score 57.5, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 317 action terms, 0 co-occurrences
- **operating_margin_disclosure** (30/100): YELLOW
  - 0 explicit % disclosures, 3 op income/loss mentions
  - Sample: `...ated accumulated depreciation are removed from the accounts and any gain or loss is included in operating income. 10 The Johns Hopkins Health System Corporat...`
  - Sample: `...experience develops or new information becomes known; such adjustments are included in current operating income. Deferred Revenue Deferred revenue includes JHHP’s capitated receipts received in advanc...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 28253 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 kaiser — score 57.5, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 157 action terms, 0 co-occurrences
- **operating_margin_disclosure** (30/100): YELLOW
  - 0 explicit % disclosures, 3 op income/loss mentions
  - Sample: `...al operating expenses 61,971 54,618 Operating income 1,960 1,843 Other income and expense: Investment income – net...`
  - Sample: `...operating expenses 31,082 28,151 Operating income 1,028 908 Other income and expense: Investment income – net...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 19449 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 hackensack_meridian — score 56.2, MIXED

- **rating_action_acknowledgment** (25/100): YELLOW
  - 1 agency mentions, 164 action terms, 1 co-occurrences
  - Sample: `...od and determined with an analysis of bonds available with an “AA-” or better rating rated by S&P. A hypothetical bond portfolio was constructed to match the expected monthly benefit payments...`
- **operating_margin_disclosure** (0/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 0 op income/loss mentions
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 15823 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 allegheny_health — score 55.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 320 action terms, 0 co-occurrences
- **operating_margin_disclosure** (20/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 2 op income/loss mentions
  - Sample: `...ting expenses 29,671,780 27,261,070 Operating loss (512,285) (160,874) Net investment income, including net realized gains on investments 597,463...`
  - Sample: `...2024 2023 Deferred tax assets Net operating loss carryforwards $ 156,081 $ 114,600 Other payables and accrued expenses 113,476...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 32090 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 bon_secours — score 55.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 183 action terms, 0 co-occurrences
- **operating_margin_disclosure** (90/100): GREEN
  - 0 explicit % disclosures, 9 op income/loss mentions
  - Sample: `...and the positive impacts of run-rate improvement efforts. In line with these results, the recurring operating income margin of improved to 2.8% for the first half of 2025, up from 1.0% in the prior ye...`
  - Sample: `...16,504 8,471 96,826 30,065 Recurring Operating Income 194,720 63,377 (21,177) (15,454) Nonrecurring Operating Losses, Net (22,526) (19,...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 20041 words = 0.0/1k
- **investment_income_masking** (30/100): RED — 4 investment-income-as-improvement passages; pattern of operational masking
  - 4 investment-income-as-improvement passages
  - Sample: `...$443.8 million. The favorable operating results for the first six months of 2025, combined with net investment gains, led to positive excess of revenue over expenses of $631.9 million for the six mont...`
  - Sample: `...investment portfolio driving net investment gains (realized and unrealized) of $443.8 million. The favorable operating results for the first six months of 2025, combined with net investment gains, led...`

### 🟡 boston_childrens — score 55.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 258 action terms, 0 co-occurrences
- **operating_margin_disclosure** (20/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 2 op income/loss mentions
  - Sample: `...4,984 Expenses 3,848,418 3,253,792 Operating loss (218,439) (28,808) Nonoperating gains (losses), net 401,481 (490,658) Exc...`
  - Sample: `...55 Total expenses 4,089,999 3,783,292 Loss from operations (104,473) (218,436) Non-operating gains (los...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 26986 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 chop — score 55.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 222 action terms, 0 co-occurrences
- **operating_margin_disclosure** (20/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 2 op income/loss mentions
  - Sample: `...s 4,737,475 4,456,258 Operating Income 231,195 87,188 Dividend and Interest income, net 41,590...`
  - Sample: `...3,992,710 811,377 1,620 (68,232) 4,737,475 Operating Income 138,826 104,132 (605) (11,158) 231,195 Dividend and interest income, net 25,762 15,828...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 29810 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 henry_ford — score 55.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 127 action terms, 0 co-occurrences
- **operating_margin_disclosure** (20/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 2 op income/loss mentions
  - Sample: `...ersus historical payment patterns; potential unknown high-cost cases; providers incurring increased operating income pressure and looking to increase their net revenue - 16 - within commercial populat...`
  - Sample: `...net periodic benefit cost are required to be presented separately from service costs and outside of operating income in the consolidated statements of operations. Only the service cost component of ne...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 15245 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 intermountain_test — score 55.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 118 action terms, 0 co-occurrences
- **operating_margin_disclosure** (20/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 2 op income/loss mentions
  - Sample: `...61 472 458 Net operating income 558 378 Nonoperating income (loss) Investment income 1,390...`
  - Sample: `...458 Net operating income 558 378 Nonoperating income (loss) Investment income 1,390 794 Gain from sale of affiliates 317 — Loss from nono...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 11742 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 memorial_hermann — score 55.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 169 action terms, 0 co-occurrences
- **operating_margin_disclosure** (20/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 2 op income/loss mentions
  - Sample: `...s 8,335,914 7,547,180 Operating income 308,281 323,102 Non-operating activities: Investment gains and other, net...`
  - Sample: `...that require recognition in the accompanying consolidated balance sheets. The Health System has net operating loss (NOL) tax carryforwards that generally will expire between 2024 and 2040, and certain...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 17837 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 mount_sinai — score 55.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 324 action terms, 0 co-occurrences
- **operating_margin_disclosure** (20/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 2 op income/loss mentions
  - Sample: `...Total operating expenses 12,119,682 Loss from operations (265,404) Other items: Net change in unrea...`
  - Sample: `...tal, and other items. The System differentiates its operating activities through the use of the loss from operations as an intermediate measure of operations. For the purposes of display, items which ...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 36711 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 northwell — score 55.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 151 action terms, 0 co-occurrences
- **operating_margin_disclosure** (20/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 2 op income/loss mentions
  - Sample: `...asset will not be realized. Significant components of Northwell’s deferred tax assets relate to net operating loss (NOL) carryforwards. Certain entities have NOL carryforwards aggregating approximatel...`
  - Sample: `...,266 In March 2026, Northwell negotiated an early release from an existing operating lease. A non- operating loss of approximately $58,000 resulted from the transaction and will be recognized in 2026....`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 21088 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 penn_medicine — score 55.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 200 action terms, 0 co-occurrences
- **operating_margin_disclosure** (20/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 2 op income/loss mentions
  - Sample: `...otal operating expenses 12,112,044 11,073,302 Operating income 219,923 272,608 Nonoperating activity, net 356,397 106,145...`
  - Sample: `...ue of the swaps. Gains/(losses) on the interest rate swap agreements are recorded as other non-operating income/(loss) in the Combined Statements of Operations. Two interest rate swap agreement mature...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 18292 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 childrens_atlanta — score 52.5, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 212 action terms, 0 co-occurrences
- **operating_margin_disclosure** (10/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 1 op income/loss mentions
  - Sample: `...2,571,811 - 2,571,811 2,249,918 - 2,249,918 OPERATING INCOME 308,975 26,565 335,540 398,248 20,150 418,398 INVESTMENT INCOME (Note 5) 945,627...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 10620 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 geisinger — score 52.5, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 93 action terms, 0 co-occurrences
- **operating_margin_disclosure** (10/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 1 op income/loss mentions
  - Sample: `...7,763,987 7,158,812 Operating loss (36,982) (238,970) Investing and financing activities Investment earnings, net...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 10441 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 norton_healthcare — score 52.5, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 173 action terms, 0 co-occurrences
- **operating_margin_disclosure** (10/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 1 op income/loss mentions
  - Sample: `...for that year are filed. In addition, for all tax years prior to 2025 generating or utilizing a net operating loss (NOL), tax authorities can adjust the amount of NOL carryforward to subsequent years....`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 17039 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 stanford_health — score 52.5, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 216 action terms, 0 co-occurrences
- **operating_margin_disclosure** (10/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 1 op income/loss mentions
  - Sample: `...ng expenses 8,408,665 7,456,840 Income from operations 543,759 414,866 Interest and inv...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 21888 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 adventhealth — score 50.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 139 action terms, 0 co-occurrences
- **operating_margin_disclosure** (30/100): YELLOW
  - 0 explicit % disclosures, 3 op income/loss mentions
  - Sample: `...ion from business combination 21,695 Total nonoperating losses, net (247,104) Excess of revenue and gains over expenses and losses 65...`
  - Sample: `...Total operating expenses 17,508,179 15,769,230 Income from Operations 2,302,128 1,024,426 Nonoperating Gains...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 12632 words = 0.0/1k
- **investment_income_masking** (70/100): YELLOW — some investment-income framing (could be legitimate)
  - 1 investment-income-as-improvement passages
  - Sample: `...vested in a portfolio designed to protect principal and obtain competitive investment returns and long-term investment growth, consistent with actuarial assumptions, with a reasonable and prudent leve...`

### 🟡 carilion — score 50.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 22 action terms, 0 co-occurrences
- **operating_margin_disclosure** (0/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 0 op income/loss mentions
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 1455 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 centura — score 50.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 1 action terms, 0 co-occurrences
- **operating_margin_disclosure** (0/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 0 op income/loss mentions
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 117 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 chla — score 50.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 337 action terms, 0 co-occurrences
- **operating_margin_disclosure** (0/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 0 op income/loss mentions
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 29004 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🟡 mayo_clinic — score 50.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 271 action terms, 0 co-occurrences
- **operating_margin_disclosure** (30/100): YELLOW
  - 0 explicit % disclosures, 3 op income/loss mentions
  - Sample: `...nefits — 1 Net operating loss 21 2 Other 5...`
  - Sample: `...$ 8 $ 4 The Clinic had federal net operating losses of $22 and $11 at December 31, 2024 and 2023, respectively. The Tax Cuts and Jobs Act (TCJA), enacted on December 22, 2017 repealed Net Operating Lo...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 50707 words = 0.0/1k
- **investment_income_masking** (70/100): YELLOW — some investment-income framing (could be legitimate)
  - 1 investment-income-as-improvement passages
  - Sample: `...e endowment assets held in perpetuity or for a specific term, as well as to provide additional real growth through new gifts and investment return. At December 31, 2024, the endowment net asset compos...`

### 🟡 tower_health — score 50.0, MIXED

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 216 action terms, 0 co-occurrences
- **operating_margin_disclosure** (0/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 0 op income/loss mentions
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 10566 words = 0.0/1k
- **investment_income_masking** (100/100): GREEN — no investment-income masking detected
  - 0 investment-income-as-improvement passages

### 🔴 loma_linda — score 48.8, SUSPECT — multiple Mode B framing concerns

- **rating_action_acknowledgment** (25/100): YELLOW
  - 1 agency mentions, 165 action terms, 1 co-occurrences
  - Sample: `...sted in a manner that is intended to produce results that exceed the price and yield results of the Standard & Poor’s 500 Index, while assuming a moderate level of investment risk. The University expe...`
- **operating_margin_disclosure** (0/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 0 op income/loss mentions
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 17666 words = 0.0/1k
- **investment_income_masking** (70/100): YELLOW — some investment-income framing (could be legitimate)
  - 1 investment-income-as-improvement passages
  - Sample: `...ustment to operating activities in the statement of cash flows. The gain on the sale is reported as investment income by the University for the value of the land, building and land improvements. The U...`

### 🔴 bilh — score 45.0, SUSPECT — multiple Mode B framing concerns

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 259 action terms, 0 co-occurrences
- **operating_margin_disclosure** (10/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 1 op income/loss mentions
  - Sample: `...Total operating expenses 9,156,135 7,825,374 Loss from operations (248,951) (131,216) Nonoperating gains (losses):...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 24817 words = 0.0/1k
- **investment_income_masking** (70/100): YELLOW — some investment-income framing (could be legitimate)
  - 1 investment-income-as-improvement passages
  - Sample: `...a predictable and stable source of revenue to the annual operating budget. Additional real growth will be provided through new gifts or excess investment return. (15) Concentrations of Credit Risk The...`

### 🔴 houston_methodist — score 45.0, SUSPECT — multiple Mode B framing concerns

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 127 action terms, 0 co-occurrences
- **operating_margin_disclosure** (10/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 1 op income/loss mentions
  - Sample: `...69,378 495,187 470,478 Operating income 637,080 496,440 Investment results and other, net 649,055 791,412...`
- **same_facility_framing** (100/100): GREEN — minimal same-facility framing
  - 0 mentions / 12291 words = 0.0/1k
- **investment_income_masking** (70/100): YELLOW — some investment-income framing (could be legitimate)
  - 1 investment-income-as-improvement passages
  - Sample: `...o time, the fair value of an endowment account may be less than the contribution amount(s) due to unfavorable investment returns. Endowment accounts with a fair value of $11.3 million and $23.8 millio...`

### 🔴 ascension — score 35.0, SUSPECT — multiple Mode B framing concerns

- **rating_action_acknowledgment** (0/100): RED — MD&A does not acknowledge agency actions
  - 0 agency mentions, 51 action terms, 0 co-occurrences
- **operating_margin_disclosure** (10/100): RED — MD&A discusses revenue/expense without disclosing operating margin %
  - 0 explicit % disclosures, 1 op income/loss mentions
  - Sample: `...es section. a Q4 FY25 recurring operating loss of $30 million, represent...`
- **same_facility_framing** (60/100): YELLOW — moderate same-facility framing
  - 17 mentions / 3454 words = 4.92/1k
  - Sample: `...e 30, 2025and2024 FortheyearendedJune30,2025,theSystemexperienced on a same facility basis which due to the organizational a 0.7% samefacilityincreaseinoverallvolume,measured...`
  - Sample: `...Facility Total after the incident, Ascension’s same facility volumes for...`
- **investment_income_masking** (70/100): YELLOW — some investment-income framing (could be legitimate)
  - 2 investment-income-as-improvement passages
  - Sample: `...ing a $816 plans have also contributed to a reduction of agency million improvement from Ascension’s comparable prior staffingrateswhilemanagingagencyutilizationtovolume year investment income of $1 b...`
  - Sample: `...r FY25, Ascension also recognized $93 basis, the System’s average length of stay has improved million of investment gains associated with the 0.9% over the prior year while acuity has increased1.6%. S...`

---

## Methodology notes

**Why deterministic, not LLM?** A signal we can audit and reproduce by hand is more credible than one that requires re-running an LLM. The four checks here are simple enough that any analyst can verify them with `grep` on the source PDF.

**Why these four?** They are the patterns surfaced by the manual Ascension R/f/M divergence report (Ω1, Ω2, R9, Ω5). The Ascension MD&A here scores 35.0 — lowest in the pilot — which validates the screener is picking up the same patterns the human analyst flagged.

**Limitations**:
- Text extraction quality matters. Ascension's MD&A is full of Unicode bidi marks (we strip them in `normalize()`).
- A high score is NECESSARY but not SUFFICIENT for honesty — these are 4 specific patterns. An obligor could pass all 4 and still be misleading in other ways.
- The investment-income-masking check is more pattern-sensitive than the others; expect 20-30% false positive rate on language like 'investment in technology that improved...'

## Next builds
- Cross-reference honesty score with realized rating outcomes — does LOW score correlate with subsequent negative rating action?
- Add more checks: covenant compliance disclosure, contingent liability disclosure (pension, litigation), forward-looking statement specificity
- Scale to remaining 60 obligors once MD&As are pulled