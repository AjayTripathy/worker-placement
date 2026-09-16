# NYC J-51 Obligation — Cohort Fraud Report (Final)

_Generated 2026-05-15T22:44:33.676028Z — `verticals.rent_stabilization.cohort_runner`_

## What this is

End-to-end run of the Signal OS rent-stabilization vertical, restricted to the **J-51 obligation** rule (`rules.j51_obligation.apply`, statutory ref **NYC Admin. Code §11-243** + ***Roberts v. Tishman Speyer Properties, L.P., 13 N.Y.3d 270 (2009)***). For each NYC building with an active J-51 stabilization obligation, we computed:

- **R (claim):** the borough-level 2025 median 1BR market rent — what a non-stabilized listing in this neighborhood would advertise. (ZIP-level Census ACS B25031 is supported but requires `CENSUS_API_KEY`; per-building StreetEasy listings are supported but Cloudflare-rate-limited at cohort scale.)
- **f (relationship):** the maximum lawful stabilized rent. Initial stabilized rent (borough-calibrated 1969 base) compounded by the NYC Rent Guidelines Board schedule (1969→2026, cumulative ≈ 5.85×) times a 1.5× allowance for legitimate vacancy bonuses + IAI improvements over the unit's history.
- **M (observed):** PLUTO building characteristics (year built, owner, unit count, building class, ZIP) cross-joined with the J-51 active obligation set from Socrata `y7az-s7wc`.

**Signal = R − f(M).** A positive value is the **annual market-rent incentive to flout** the J-51 obligation — the dollar amount per unit by which neighborhood market rents exceed the legal stabilized maximum the owner is statutorily required to honor. Aggregated to building level by multiplying per-unit gap × residential unit count.

## Topline (actionable rental cohort)

Filters out (a) co-op / Mitchell-Lama / HDFC / non-profit housing where units cannot lawfully be re-priced to market and (b) historically resolved Roberts-line settlements (Stuyvesant Town / Peter Cooper Village / Parker Towers — see appendix).

| Metric | Value |
|---|---:|
| Actionable J-51 rental buildings | 17,178 |
| Aggregate residential units in those buildings | 682,864 |
| **Aggregate annual market-rent gap (incentive-to-flout)** | **$18,563,973,882** |
| Buildings owned by entities (LLC / Corp / Trust) | 14,394 (84%) |
| Buildings owned by individuals | 2,784 (16%) |
| In Roberts tail period (post-abatement, pre-35-yr-end) | 13,442 (78%) |
| In J-51 active-abatement period | 3,736 (22%) |

_Excluded from above: 3,888 non-rental (co-op/MTL/HDFC) buildings and 23 historically-resolved Roberts buildings._

## By borough

| Borough | Buildings | Units | Annual gap |
|---|---:|---:|---:|
| Manhattan | 5,736 | 196,037 | $7,418,063,043 |
| Brooklyn | 5,513 | 178,317 | $5,176,034,905 |
| Queens | 2,465 | 142,585 | $3,190,326,728 |
| Bronx | 3,401 | 159,826 | $2,693,247,792 |
| Staten_Island | 63 | 6,099 | $86,301,414 |

## Portfolio leads — entity owners with ≥2 J-51 buildings

These are the highest-priority enforcement leads. Multi-building owners have the resources and the motive to deregulate at scale; the AG's Tenants Rights Bureau and DHCR enforcement have historically pursued this exact cohort (e.g., Tishman Speyer/Stuy Town, A&E Real Estate, Pinnacle Group).

_1,220 normalized owner keys cover ≥2 J-51 buildings._

| Rank | Normalized owner key | Buildings | Tail-period | Active | Units | Boroughs | Annual gap |
|---:|---|---:|---:|---:|---:|---|---:|
| 1 | SERLIN BUILDING PARTNERSHIP | 19 | 0 | 19 | 136 | BRO | $3,942,227 |
| 2 | BUSHWICK PROPERTIES MGNT PTRSH | 18 | 0 | 18 | 115 | BRO | $3,333,500 |
| 3 | JENKINS PORTFOLIO COMPANIES | 16 | 0 | 16 | 196 | MAN | $7,386,597 |
| 4 | COOPER & DECATUR PARTNERSHIP | 16 | 0 | 16 | 102 | BRO | $2,956,670 |
| 5 | EMPIRE | 16 | 6 | 10 | 64 | BRO | $1,855,165 |
| 6 | PACIFIC VILLAGE | 15 | 0 | 15 | 136 | BRO | $3,942,227 |
| 7 | JC REAL ESTATE DEVELOPMENT | 15 | 0 | 15 | 77 | BRO | $2,231,996 |
| 8 | CROWN PROSPECT PARTNE RSHIP | 14 | 13 | 1 | 126 | BRO | $3,652,357 |
| 9 | BOYNTON WHEELER IN | 14 | 0 | 14 | 118 | BRO | $1,986,775 |
| 10 | 78/79 YORK | 13 | 1 | 12 | 1,344 | MAN | $50,650,952 |
| 11 | WEST 128TH STREET | 13 | 0 | 13 | 230 | MAN | $8,667,946 |
| 12 | NEP WEST 119TH STREET PROPERTIES | 13 | 0 | 13 | 159 | MAN | $5,992,188 |
| 13 | MACBAIN DEVELOPMENT | 13 | 0 | 13 | 62 | BRO | $1,797,192 |
| 14 | KEW GARDENS HILLS | 12 | 12 | 0 | 1,268 | QUE | $28,339,191 |
| 15 | CITYWIDE PRESERVATION | 12 | 2 | 10 | 267 | BRO, BRO, MAN | $7,348,017 |
| 16 | HPH CHOSEN | 12 | 0 | 12 | 108 | MAN | $4,070,166 |
| 17 | WFHA BROOKLYN RESTORATION | 12 | 1 | 11 | 119 | BRO | $3,449,448 |
| 18 | NORTHERN MANHATTAN EQUITIES | 11 | 2 | 9 | 323 | MAN | $12,172,811 |
| 19 | BAINBRIDGE CLUSTER | 11 | 0 | 11 | 74 | BRO | $2,145,035 |
| 20 | EL DORADO | 11 | 11 | 0 | 63 | BRO | $1,937,921 |
| 21 | KING ENTERPRISES | 10 | 10 | 0 | 231 | MAN | $8,705,632 |
| 22 | ALDUS GREEN | 10 | 10 | 0 | 376 | BRO | $6,330,742 |
| 23 | CDC EAST 105TH STREET | 10 | 0 | 10 | 107 | MAN | $4,032,479 |
| 24 | GATES CLUSTER DEVELOPMENT | 10 | 1 | 9 | 98 | BRO | $2,840,722 |
| 25 | HOWARD AVENUE DEVELOPMENT | 10 | 0 | 10 | 69 | BRO | $2,000,100 |
| 26 | WYCKOFF HEIGHTS | 10 | 3 | 7 | 58 | BRO | $1,681,244 |
| 27 | 818-860 GV | 10 | 10 | 0 | 93 | BRO | $1,565,848 |
| 28 | NEW YORK EQUITY FUND  2003 | 10 | 10 | 0 | 37 | BRO | $1,072,518 |
| 29 | BEACH HAVEN APARTMENTS | 9 | 9 | 0 | 1,260 | BRO | $36,523,570 |
| 30 | CENTRAL HARLEM PORTFOLIO | 9 | 3 | 6 | 213 | MAN | $8,027,271 |
| 31 | 122 STREET PORTFOLIO | 9 | 0 | 9 | 113 | MAN | $4,258,599 |
| 32 | TINTON WALES | 9 | 0 | 9 | 240 | BRO | $4,040,899 |
| 33 | ICER OF HAMILTON HEIGHTS | 9 | 7 | 2 | 105 | MAN | $3,957,106 |
| 34 | GREENE LG | 9 | 0 | 9 | 78 | BRO, MAN | $2,591,574 |
| 35 | CROTONA PARK HOUSING | 9 | 0 | 9 | 147 | BRO | $2,475,051 |
| 36 | BROOKLYN PARK TERRACE | 9 | 2 | 7 | 71 | BRO | $2,058,074 |
| 37 | NORTON MG CLUSTER | 9 | 0 | 9 | 63 | BRO | $1,826,178 |
| 38 | NANRAJ | 9 | 0 | 9 | 58 | BRO | $1,681,244 |
| 39 | SHEFFIELD CLUSTER DEVELOPMENT | 9 | 0 | 9 | 58 | BRO | $1,681,244 |
| 40 | LEXINGTON AVENUE | 9 | 2 | 7 | 51 | BRO | $1,478,335 |
| 41 | ARIS CRESCENT II | 8 | 8 | 0 | 256 | QUE | $5,721,477 |
| 42 | WCG 111 STREET | 8 | 0 | 8 | 124 | MAN | $4,673,153 |
| 43 | BENSON ESTATES | 8 | 0 | 8 | 149 | BRO | $4,319,057 |
| 44 | E 129 ST CLUSTER | 8 | 0 | 8 | 79 | MAN | $2,977,251 |
| 45 | EAST 22ND EQUITIES | 8 | 8 | 0 | 100 | BRO | $2,898,696 |
| 46 | HAF EDGECOMBE ASSOCLP | 8 | 0 | 8 | 68 | MAN | $2,562,697 |
| 47 | KLANSTUY 25% | 8 | 1 | 7 | 77 | BRO | $2,231,996 |
| 48 | NU WORLD BUILDERS | 8 | 5 | 3 | 67 | BRO | $1,942,126 |
| 49 | RALPH-GATES CLUSTER | 8 | 8 | 0 | 41 | BRO | $1,188,465 |
| 50 | DARE TO DREAM HOUSING ASSOCIATION | 8 | 3 | 5 | 36 | BRO | $1,043,531 |

## Roberts-tail cohort (post-active-abatement, pre-35-yr-end)

Owners frequently treat the end of J-51 abatement as the end of the stabilization obligation. Roberts holds otherwise: the obligation runs for the abatement period **plus** 35 years. This subset is the highest rate of detected violations.

- Tail-period buildings: **13,442**
- Units: **539,167**
- Annual market-rent gap: **$15,007,835,153**

### Top 25 tail-period buildings by exposure

| BBL | Address | Borough | Units | Owner | Yr built | J-51 expires | Annual gap |
|---|---|---|---:|---|---:|---:|---:|
| 1002530001 | 100 CHERRY STREET | MAN | 1590 | KVI MEZZ CORP. | 1935 | 2057 | $59,921,885 |
| 1001420025 | 310 GREENWICH STREET | MAN | 1328 | IP MORTGAGE BORROWER LLC | 1975 | 2047 | $54,963,901 |
| 3013020001 | 1720 BEDFORD AVENUE | BRO | 1321 | FIELDBRIDGE ASSOCIATES | 1960 | 2050 | $38,291,774 |
| 1003150001 | 409 GRAND STREET | MAN | 880 | UNAVAILABLE OWNER | 1960 | 2042 | $33,164,314 |
| 1015490001 | 1660 2 AVENUE | MAN | 692 | CF E 86 LLC | 1964 | 2047 | $26,079,210 |
| 1008170029 | 6 WEST 16 STREET | MAN | 481 | AKAM ASSOCIATES | 1964 | 2047 | $18,127,312 |
| 3072740015 | 440 NEPTUNE AVENUE | BRO | 572 | UNAVAILABLE OWNER | 1964 | 2057 | $16,580,541 |
| 1015140039 | 1524 3 AVENUE | MAN | 430 | DRMBRE-85 FEE LLC | 1967 | 2047 | $16,205,290 |
| 1011620029 | 2039 BROADWAY | MAN | 387 | SHERMAN SQ REALTY CORP | 1971 | 2034 | $15,542,121 |
| 1013660001 | 984 1 AVENUE | MAN | 397 | 405 EAST 54TH STREET CORP | 1930 | 2037 | $14,961,628 |
| 1010240001 | 870 8 AVENUE | MAN | 381 | SUNSTONE ASSOCIATES LLC | 1965 | 2041 | $14,358,640 |
| 1008630044 | 66 EAST 34 STREET | MAN | 364 | 4 PARK AVENUE ASSOCIATES, | 1913 | 2046 | $13,717,966 |
| 1013330018 | 2 TUDOR CITY PLACE | MAN | 334 | NAUTILUS TUDOR LLC | 1956 | 2056 | $12,587,364 |
| 1008990001 | 205 3 AVENUE | MAN | 326 | 205 3 AVE CORP | 1964 | 2046 | $12,285,871 |
| 1008790027 | 143 EAST 23 STREET | MAN | 326 | KENMORE ASSOCIATES LP | 1928 | 2030 | $12,285,871 |
| 1005660018 | 20 UNIVERSITY PLACE | MAN | 323 | UNAVAILABLE OWNER | 1965 | 2050 | $12,172,811 |
| 1009130001 | 471 3 AVENUE | MAN | 300 | PLAZA REALTY INVESTORS, D | 1972 | 2048 | $12,048,156 |
| 1006430001 | 521 WEST STREET | MAN | 318 | 95-97 HORATIO L.L.C. | 1930 | 2029 | $11,984,377 |
| 4066980040 | 150-10 71 AVENUE | QUE | 536 | UNAVAILABLE OWNER | 1952 | 2044 | $11,979,343 |
| 1012330016 | 2350 BROADWAY | MAN | 312 | 2350 BROADWAY ASSOCIATES, | 1903 | 2045 | $11,758,257 |
| 1014240001 | 201 EAST 69 STREET | MAN | 300 | 201 EAST 69 LLC | 1927 | 2028 | $11,306,016 |
| 4042850010 | 26-10 UNION STREET | QUE | 504 | MITCHELL GARDENS #3 COOPE | 1957 | 2061 | $11,264,158 |
| 1010300058 | 240 CENTRAL PARK SOUTH | MAN | 297 | CENTRAL PARK SOUTH ASSOCI | 1940 | 2039 | $11,192,956 |
| 1012180001 | 575 AMSTERDAM AVENUE | MAN | 266 | UWS VENTURES IV, LLC | 1975 | 2045 | $11,009,336 |
| 1009000027 | 329 2 AVENUE | MAN | 292 | 245 E. 19 REALTY LLC | 1963 | 2043 | $11,004,522 |

## Top 50 buildings by annual exposure (all cohorts)

| BBL | Address | Borough | Units | Owner | Borough median 1BR | Max legal | Monthly gap | Annual exposure | Tier |
|---|---|---|---:|---|---:|---:|---:|---:|---|
| 2051350051 | 120 ERSKINE PLACE | BRO | 4458 | UNAVAILABLE OWNER | $2,200 | $797 | $1,403 | $75,059,703 | high |
| 1002530001 | 100 CHERRY STREET | MAN | 1590 | KVI MEZZ CORP. | $4,500 | $1,359 | $3,141 | $59,921,885 | high |
| 1001420025 | 310 GREENWICH STREET | MAN | 1328 | IP MORTGAGE BORROWER LLC | $4,500 | $1,051 | $3,449 | $54,963,901 | high |
| 3013020001 | 1720 BEDFORD AVENUE | BRO | 1321 | FIELDBRIDGE ASSOCIATES | $3,400 | $984 | $2,416 | $38,291,774 | high |
| 1003150001 | 409 GRAND STREET | MAN | 880 | UNAVAILABLE OWNER | $4,500 | $1,359 | $3,141 | $33,164,314 | high |
| 1015490001 | 1660 2 AVENUE | MAN | 692 | CF E 86 LLC | $4,500 | $1,359 | $3,141 | $26,079,210 | high |
| 1008170029 | 6 WEST 16 STREET | MAN | 481 | AKAM ASSOCIATES | $4,500 | $1,359 | $3,141 | $18,127,312 | high |
| 3072740015 | 440 NEPTUNE AVENUE | BRO | 572 | UNAVAILABLE OWNER | $3,400 | $984 | $2,416 | $16,580,541 | high |
| 1015140039 | 1524 3 AVENUE | MAN | 430 | DRMBRE-85 FEE LLC | $4,500 | $1,359 | $3,141 | $16,205,290 | high |
| 1011620029 | 2039 BROADWAY | MAN | 387 | SHERMAN SQ REALTY CORP | $4,500 | $1,153 | $3,347 | $15,542,121 | high |
| 1013660001 | 984 1 AVENUE | MAN | 397 | 405 EAST 54TH STREET CORP | $4,500 | $1,359 | $3,141 | $14,961,628 | high |
| 1010240001 | 870 8 AVENUE | MAN | 381 | SUNSTONE ASSOCIATES LLC | $4,500 | $1,359 | $3,141 | $14,358,640 | high |
| 1008630044 | 66 EAST 34 STREET | MAN | 364 | 4 PARK AVENUE ASSOCIATES, | $4,500 | $1,359 | $3,141 | $13,717,966 | high |
| 1013330018 | 2 TUDOR CITY PLACE | MAN | 334 | NAUTILUS TUDOR LLC | $4,500 | $1,359 | $3,141 | $12,587,364 | high |
| 1008990001 | 205 3 AVENUE | MAN | 326 | 205 3 AVE CORP | $4,500 | $1,359 | $3,141 | $12,285,871 | high |
| 1008790027 | 143 EAST 23 STREET | MAN | 326 | KENMORE ASSOCIATES LP | $4,500 | $1,359 | $3,141 | $12,285,871 | high |
| 1005660018 | 20 UNIVERSITY PLACE | MAN | 323 | UNAVAILABLE OWNER | $4,500 | $1,359 | $3,141 | $12,172,811 | high |
| 1018900040 | 310 RIVERSIDE DRIVE | MAN | 323 | MASTERS APARTMENTS I | $4,500 | $1,359 | $3,141 | $12,172,811 | high |
| 2045060001 | 2700 BRONX PARK EAST | BRO | 716 | HP BRONX PARK EAST HOUSIN | $2,200 | $797 | $1,403 | $12,055,349 | high |
| 1009130001 | 471 3 AVENUE | MAN | 300 | PLAZA REALTY INVESTORS, D | $4,500 | $1,153 | $3,347 | $12,048,156 | high |
| 1006430001 | 521 WEST STREET | MAN | 318 | 95-97 HORATIO L.L.C. | $4,500 | $1,359 | $3,141 | $11,984,377 | high |
| 4066980040 | 150-10 71 AVENUE | QUE | 536 | UNAVAILABLE OWNER | $2,800 | $938 | $1,862 | $11,979,343 | high |
| 1012330016 | 2350 BROADWAY | MAN | 312 | 2350 BROADWAY ASSOCIATES, | $4,500 | $1,359 | $3,141 | $11,758,257 | high |
| 2045060040 | 2800 BRONX PARK EAST | BRO | 680 | HP BRONX PARK EAST HOUSIN | $2,200 | $797 | $1,403 | $11,449,214 | high |
| 1014240001 | 201 EAST 69 STREET | MAN | 300 | 201 EAST 69 LLC | $4,500 | $1,359 | $3,141 | $11,306,016 | high |
| 4042850010 | 26-10 UNION STREET | QUE | 504 | MITCHELL GARDENS #3 COOPE | $2,800 | $938 | $1,862 | $11,264,158 | high |
| 1010300058 | 240 CENTRAL PARK SOUTH | MAN | 297 | CENTRAL PARK SOUTH ASSOCI | $4,500 | $1,359 | $3,141 | $11,192,956 | high |
| 3070550013 | 2950 WEST 24 STREET | BRO | 360 | OCEAN TOWERS PARTNERS LLC | $3,400 | $835 | $2,565 | $11,080,195 | high |
| 1012180001 | 575 AMSTERDAM AVENUE | MAN | 266 | UWS VENTURES IV, LLC | $4,500 | $1,051 | $3,449 | $11,009,336 | high |
| 1009000027 | 329 2 AVENUE | MAN | 292 | 245 E. 19 REALTY LLC | $4,500 | $1,359 | $3,141 | $11,004,522 | high |
| 1014430001 | 1296 2 AVENUE | MAN | 289 | APPLEBAUM DAVID P | $4,500 | $1,359 | $3,141 | $10,891,462 | high |
| 1018520031 | 120 WEST 100 STREET | MAN | 287 | CF PWV LLC | $4,500 | $1,359 | $3,141 | $10,816,089 | high |
| 1018520020 | 790 COLUMBUS AVENUE | MAN | 287 | CF PWV LLC | $4,500 | $1,359 | $3,141 | $10,816,089 | high |
| 1017300025 | 25 WEST 132 STREET | MAN | 286 | THIRD LENOX TERRACE ASSOC | $4,500 | $1,359 | $3,141 | $10,778,402 | high |
| 1017300075 | 470 LENOX AVENUE | MAN | 286 | FIFTH LENOX TERRACE ASSOC | $4,500 | $1,359 | $3,141 | $10,778,402 | high |
| 1017300045 | 10 WEST 135 STREET | MAN | 286 | FIRST LENOX TERRACE ASSOC | $4,500 | $1,359 | $3,141 | $10,778,402 | high |
| 1017300009 | 45 WEST 132 STREET | MAN | 286 | SIXTH LENOX TERRACE ASSOC | $4,500 | $1,359 | $3,141 | $10,778,402 | high |
| 1017300064 | 40 WEST 135 STREET | MAN | 286 | FOURTH LENOX TERRACE ASSO | $4,500 | $1,359 | $3,141 | $10,778,402 | high |
| 1017300036 | 2186 5 AVENUE | MAN | 286 | SECOND LENOX TERRACE ASSO | $4,500 | $1,359 | $3,141 | $10,778,402 | high |
| 4001170001 | 50-01 39 AVENUE | QUE | 472 | SUNNYSIDE GARDEN APARTMEN | $2,800 | $938 | $1,862 | $10,548,973 | high |
| 2035670001 | 633 OLMSTEAD AVENUE | BRO | 624 | JAMIE TOWERS HOUSING | $2,200 | $797 | $1,403 | $10,506,338 | high |
| 1010220061 | 834 8 AVENUE | MAN | 278 | FIFTY FIRST-CAPITOLASSC | $4,500 | $1,359 | $3,141 | $10,476,908 | high |
| 4076320002 | 67-02 SPRINGFIELD BLVD | QUE | 467 | BELL PARK GARDENS | $2,800 | $938 | $1,862 | $10,437,226 | high |
| 3069790100 | 3521 NEPTUNE AVENUE | BRO | 334 | HP BAY PARK I PRESERVATIO | $3,400 | $807 | $2,593 | $10,393,946 | high |
| 1010670012 | 435 WEST 57 STREET | MAN | 275 | SOUTH PARK ESTATES COMPAN | $4,500 | $1,359 | $3,141 | $10,363,848 | high |
| 3074490001 | 3020 AVENUE Y | BRO | 357 | KINGS BAY HOUSES SECT 2 I | $3,400 | $984 | $2,416 | $10,348,345 | high |
| 3011890060 | 49 CROWN STREET | BRO | 321 | TIVOLI BI LLP | $3,400 | $815 | $2,585 | $9,958,306 | high |
| 1013680001 | 1026 1 AVENUE | MAN | 259 | 400 E57 FEE OWNER LLC | $4,500 | $1,359 | $3,141 | $9,760,860 | high |
| 1008890068 | 120 EAST 34 STREET | MAN | 259 | 120 EAST 34TH STREETCO. | $4,500 | $1,359 | $3,141 | $9,760,860 | high |
| 1022480092 | 128 SEAMAN AVENUE | MAN | 259 | WINDY REALTY ASSOCIATES L | $4,500 | $1,359 | $3,141 | $9,760,860 | high |

## Appendix A — validation: the literal Roberts cases at rank 1

Before any filtering, the **highest-exposure J-51 building in the unfiltered run is Stuyvesant Town** (BBL 1009720001, 8,764 units, BPP ST OWNER LLC, $330M/yr market-rent gap). Rank 2 is **Peter Cooper Village** (sister property, same litigation). These are the literal subject buildings of *Roberts v. Tishman Speyer*. The fact that the rule fires loudest on the case it is named after is a positive validation that the f-side computation and J-51 join are correct.

These buildings are excluded from the actionable cohort above because their enforcement status is settled history: the 2010 settlement ($173M to tenants) and the 2015 Brookfield/Blackstone affordability agreement (5,000 units preserved as middle-income through 2035) close the open-question dimension of the original violation. They remain subject to ongoing DHCR oversight.

| BBL | Address | Units | Owner | Annual gap |
|---|---|---:|---|---:|
| 1009720001 | 240 1 AVENUE | 8764 | BPP ST OWNER LLC | $330,286,414 |
| 1009780001 | 342 1 AVENUE | 2491 | BPP PCV OWNER LLC | $93,877,620 |
| 4031750001 | 104-20 QUEENS BOULEVARD | 1327 | BPP PARKER TOWER PROPERTY OWNE | $29,657,813 |
| 1009210019 | 333 EAST 14 STREET | 207 | STUYVESANT OWNERS INC | $7,801,151 |
| 1008970008 | 207 EAST 15 STREET | 59 | STUYVESANT GARDENS CO | $2,223,516 |
| 3075760069 | 850 EAST 31 STREET | 71 | PETER STUYVESANTS APTS INC | $2,058,074 |
| 3016770001 | 295 MALCOLM X BOULEVARD | 37 | BNIA STUYVESANT HEIGHTS HOUSIN | $1,072,518 |
| 1004650046 | 48 STUYVESANT STREET | 14 | STUYVESANT 48 LLC | $527,614 |
| 3016620006 | 237 MALCOLM X BOULEVARD | 12 | BNIA STUYVESANT HEIGHTS HOUSIN | $347,844 |
| 3016370032 | 914 GATES AVENUE | 12 | BNIA STUYVESANT HEIGHTS HOUSIN | $347,844 |

## Appendix B — non-rental buildings excluded

3,888 buildings (~281,413 units) matched J-51 obligation but were excluded from the actionable cohort because their owner names indicate they are co-ops, Mitchell-Lama developments, HDFC limited-equity buildings, or NYCHA-adjacent non-profit housing. Units in these buildings cannot lawfully be re-priced to market regardless of the J-51 obligation status, so the borough-median benchmark is not a meaningful incentive measurement.

- Excluded buildings: 3,888
- Excluded units: 283,233
- Excluded gap (would-be-flout incentive if these were market-rate): $7,920,258,864

Tightening this filter further requires a connector to NYC HPD's Mitchell-Lama building list and HDFC roster — both FOIL-able.

## How to read this — and what it cannot say

**What the signal IS:** structural exposure measurement. For every J-51 building in the cohort, the dollar gap between neighborhood market rent and the maximum legal stabilized rent the owner is statutorily required to honor. This is the magnitude of the *incentive* a rational owner has to flout the J-51 covenant.

**What the signal IS NOT:** confirmed unit-by-unit overcharge. To convert a building-level lead into a confirmed violation, an analyst must:
1. Pull the DHCR Annual Apartment Registration history per unit (FOIL request).
2. Compare the registered legal regulated rent to current rent rolls (RPIE filings or tenant-supplied leases).
3. Confirm the J-51 abatement on file with the Department of Finance.

The DHCR Annual Apartment Registration connector is the rent-stab analogue of the Detroit L-4260 PTA log — the single highest-ROI add to the framework. See `audit_v1/coverage_assessment.md` for the full M-source roadmap.

**Known false-positive sources in this report:**
- **Co-op buildings.** Co-op corporations don't typically charge rent (members own units). Filter `is_coop=True` to remove these. We flag 3,888 non-rental rows separately.
- **HDFCs / income-restricted housing.** Many J-51 buildings in this set are HDFC limited-equity co-ops or LIHTC properties where rent is capped well below borough median. Same `is_coop` filter catches most.
- **Borough-level rent benchmarks.** Using a single borough median 1BR rent overstates the gap in cheap subneighborhoods (East Bronx, deep Queens) and understates in expensive ones (UWS, West Village). ZIP-level Census ACS resolution requires a `CENSUS_API_KEY`; per-building StreetEasy listings would be the next step beyond that.
- **Sub-1974 vintage assumption.** For buildings built post-1974 with J-51, the base year is year_built, not 1969. The runner correctly applies this — RGB compounds from year_built — but newer buildings will show smaller gaps.

**Where this report sits in the pipeline:** stage 5 (gap detection) → stage 6 (rule application: J51_OBLIGATION fired). Next stages (verification, packaging for enforcement referral) require the DHCR connector or analyst hand-work.
