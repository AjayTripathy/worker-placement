# Quality wishlist — mechanical candidate list for the cull (2026-08-14)

**What this is.** The mechanical half of the hybrid seeding the principal approved on 2026-08-13. Every name below cleared a five-part quality gate on ten years of audited XBRL. Nothing here has been researched, and nothing here can fire an alert yet.

**What to do with it.** Cross out the names you would not own at any price and keep roughly seventy-five. Save the survivors as a list of tickers to `verticals/generators/data/quality_wishlist_active.json` in the form `{"asof": "YYYY-MM-DD", "tickers": ["AAA", "BBB"]}`. The daily watch reads that file and only that file. Until it exists the wishlist is inactive by design — an unculled mechanical list firing its own output is the generator grading itself.

**What happens after the cull.** Each surviving name carries valuation bands measured against its own ten-year history, not against its peers. When a name reaches the middle of its own range it proposes a first tranche; when it reaches the cheapest fifth of its own range it proposes a starter; and if its valuation slid twenty-five percentile points in a year while earnings per share rose, it proposes on that alone — the case of a good business that got cheap by standing still. No name is courted until it actually gets cheap, and no proposal ever places an order.

---

## How the gate read the tape

- Universe screened: **917** names (S&P 500 constituents plus the broad US market-cap ladder); **148** dropped as already in the research ledger.
- Cleared the gate: **51**. Failed it: **338**.
- Set aside as **189 insufficient-history** names — fewer than eight usable years of filings. These were neither passed nor failed; they are listed at the bottom.
- Banks, insurers and other financials removed before the gate ran: **191** (they have their own trap catalog and their own screen).
- **51** candidates remain, of which **0** could not be given a valuation percentile for lack of price history.

The five columns are the gate itself: how many of the last ten years earned more than fifteen percent on invested capital; how many years revenue rose; the latest gross margin and its ten-year trend; net debt against EBITDA; and the change in diluted share count across the decade. Return on invested capital is an approximation from tagged filing data — operating profit after an effective tax rate, over book equity plus net debt — and leases are not capitalised, so lease-heavy retailers read high. The last column is where the name sits in its own ten-year valuation range today: 0 is the cheapest it has ever been, 100 the dearest.

---

## Candidates (cheapest against their own history first)

| # | Ticker | Company | Sector | ROIC>15% yrs | Rev-up yrs | Gross margin | ND/EBITDA | Diluted shares | Own-history %ile | Band |
|---|--------|---------|--------|--------------|------------|--------------|-----------|----------------|------------------|------|
| 1 | CPRT | COPART, INC. | Retail-Auto Dealers & Gasoli | 10/10 | 10/10 | 87.5% (-10bp/yr) | net cash | -7.0% | 1 | CHEAP |
| 2 | CMG | CHIPOTLE MEXICAN GRILL, INC. | Retail-Eating  Places | 9/10 | 9/9 | n/a | net cash | -14.7% | 2 | CHEAP |
| 3 | DPZ | Domino’s Pizza, Inc. | Wholesale-Groceries & Relate | 10/10 | 9/10 | 40.0% (+89bp/yr) | net cash | -38.3% | 3 | CHEAP |
| 4 | ROL | ROLLINS, INC. | Services-To Dwellings & Othe | 10/10 | 9/9 | 51.5% (+8bp/yr) | 0.60x | -1.6% | 5 | CHEAP |
| 5 | NKE | NIKE, Inc. | Rubber & Plastics Footwear | 10/10 | 8/10 | 42.9% (-20bp/yr) | 0.08x | -15.0% | 5 | CHEAP |
| 6 | PYPL | PayPal Holdings, Inc. | Services-Business Services,  | 8/10 | 10/10 | n/a | net cash | -21.2% | 7 | CHEAP |
| 7 | FDS | FACTSET RESEARCH SYSTEMS INC. | Services-Computer Programmin | 10/10 | 10/10 | 52.7% (-42bp/yr) | 1.12x | -9.1% | 8 | CHEAP |
| 8 | JKHY | JACK HENRY & ASSOCIATES, INC. | Services-Computer Integrated | 10/10 | 10/10 | 42.7% (-14bp/yr) | net cash | -10.5% | 13 | CHEAP |
| 9 | IDXX | IDEXX LABORATORIES INC /DE | In Vitro & In Vivo Diagnosti | 10/10 | 10/10 | 61.8% (+70bp/yr) | 0.18x | -13.5% | 16 | CHEAP |
| 10 | CLX | CLOROX CO /DE/ | Specialty Cleaning, Polishin | 8/10 | 8/10 | 45.2% (-30bp/yr) | 1.67x | -6.4% | 19 | CHEAP |
| 11 | FIZZ | National Beverage Corp. | Bottled & Canned Soft Drinks | 10/10 | 8/10 | 37.0% (-15bp/yr) | net cash | +0.4% | 20 | FAIR |
| 13 | QLYS | Qualys, Inc. | Services-Prepackaged Softwar | 10/10 | 9/10 | 82.8% (+104bp/yr) | net cash | -4.8% | 24 | FAIR |
| 14 | TSCO | TRACTOR SUPPLY CO /DE/ | Retail-Building Materials, H | 10/10 | 10/10 | 36.4% (+23bp/yr) | 0.80x | -22.2% | 29 | FAIR |
| 15 | NVR | NVR, Inc. | Operative Builders | 10/10 | 8/10 | n/a | net cash | -27.9% | 29 | FAIR |
| 16 | MA | Mastercard Incorporated | Services-Business Services,  | 10/10 | 8/10 | n/a | 0.42x | -20.3% | 30 | FAIR |
| 17 | ULTA | ULTA BEAUTY, INC. | Retail-Retail Stores, NEC | 10/10 | 9/10 | 39.1% (+46bp/yr) | net cash | -30.0% | 31 | FAIR |
| 18 | COLM | COLUMBIA SPORTSWEAR COMPANY | Apparel & Other Finishd Prod | 9/10 | 8/10 | 50.5% (+41bp/yr) | net cash | -22.9% | 32 | FAIR |
| 20 | JNJ | Johnson & Johnson | Pharmaceutical Preparations | 10/10 | 9/10 | 67.9% (+5bp/yr) | 0.52x | -13.6% | 53 | — |
| 21 | GGG | GRACO INC. | Pumps & Pumping Equipment | 9/10 | 8/10 | 52.4% (-15bp/yr) | net cash | -4.4% | 54 | — |
| 22 | MTD | Mettler-Toledo International Inc. | Laboratory Analytical Instru | 10/10 | 9/10 | 59.4% (+30bp/yr) | 1.78x | -26.9% | 56 | — |
| 23 | EXP | EAGLE MATERIALS INC | Cement, Hydraulic | 8/10 | 9/10 | 28.3% (+76bp/yr) | 1.94x | -35.7% | 65 | — |
| 24 | MCO | MOODY'S CORPORATION | Services-Consumer Credit Rep | 10/10 | 9/10 | 74.4% (+23bp/yr) | 1.19x | -11.6% | 67 | — |
| 25 | ALLE | Allegion plc | Services-Detective, Guard &  | 10/10 | 9/10 | 45.2% (+5bp/yr) | 1.64x | -10.6% | 67 | — |
| 27 | FTNT | FORTINET, INC. | Computer Peripheral Equipmen | 10/10 | 10/10 | 80.5% (+73bp/yr) | net cash | -13.2% | 73 | — |
| 28 | DRI | DARDEN RESTAURANTS, INC. | Retail-Eating  Places | 9/10 | 8/10 | 20.3% (+23bp/yr) | 0.99x | -10.1% | 74 | — |
| 29 | VRSN | VERISIGN INC/CA | Services-Computer Programmin | 10/10 | 10/10 | 88.1% (+60bp/yr) | 1.05x | -29.5% | 74 | — |
| 30 | UPS | UNITED PARCEL SERVICE INC | Trucking & Courier Services  | 10/10 | 8/10 | n/a | 1.68x | -6.2% | 77 | — |
| 31 | LOGI | LOGITECH INTERNATIONAL S.A. | Computer Peripheral Equipmen | 10/10 | 8/10 | 43.2% (+86bp/yr) | net cash | -10.6% | 77 | — |
| 32 | CDNS | CADENCE DESIGN SYSTEMS, INC. | Services-Prepackaged Softwar | 10/10 | 10/10 | n/a | net cash | -12.5% | 78 | — |
| 33 | TJX | THE TJX COMPANIES, INC. | Retail-Family Clothing Store | 10/10 | 9/10 | 31.0% (+24bp/yr) | net cash | -17.5% | 83 | — |
| 34 | CTAS | Cintas Corporation | Men's & Boys' Furnishgs, Wor | 9/10 | 10/10 | 50.0% (+60bp/yr) | 0.76x | -12.7% | 88 | — |
| 35 | ORLY | O REILLY AUTOMOTIVE INC | Retail-Auto & Home Supply St | 10/10 | 10/10 | 51.6% (-15bp/yr) | 1.47x | -43.8% | 88 | — |
| 36 | TXRH | Texas Roadhouse, Inc. | Retail-Eating  Places | 9/10 | 9/10 | n/a | net cash | -6.0% | 88 | — |
| 37 | ROST | Ross Stores, Inc. | Retail-Family Clothing Store | 9/10 | 8/10 | 27.7% (-16bp/yr) | net cash | -20.2% | 90 | — |
| 38 | COR | CENCORA, INC. | Wholesale-Drugs, Proprietari | 9/9 | 10/10 | 3.6% (+9bp/yr) | 0.90x | -10.4% | 90 | — |
| 39 | FFIV | F5, INC. | Computer Communications Equi | 10/10 | 10/10 | 81.4% (-36bp/yr) | net cash | -19.1% | 93 | — |
| 40 | BKNG | Booking Holdings Inc. | Transportation Services | 9/10 | 9/10 | n/a | 0.16x | -36.7% | 94 | — |
| 41 | FIX | COMFORT SYSTEMS USA, INC. | Electrical Work | 8/10 | 10/10 | 24.1% (+9bp/yr) | net cash | -6.5% | 98 | — |
| 42 | EW | Edwards Lifesciences Corporation | Orthopedic, Prosthetic & Sur | 10/10 | 9/10 | 78.0% (+70bp/yr) | net cash | -11.4% | 98 | — |
| 43 | AMAT | APPLIED MATERIALS INC /DE | Semiconductors & Related Dev | 10/10 | 9/10 | 48.7% (+67bp/yr) | net cash | -34.1% | 99 | — |
| 44 | GWW | W.W. Grainger, Inc. | Wholesale-Durable Goods | 10/10 | 10/10 | 39.1% (-22bp/yr) | 0.67x | -27.0% | 99 | — |
| 45 | CL | COLGATE-PALMOLIVE COMPANY | Perfumes, Cosmetics & Other  | 10/10 | 9/10 | 60.1% (-1bp/yr) | 1.67x | -10.8% | 99 | — |
| 46 | EME | EMCOR Group, Inc. | Electrical Work | 8/10 | 9/10 | 19.3% (+47bp/yr) | net cash | -28.7% | 99 | — |
| 47 | LRCX | LAM RESEARCH CORPORATION | Special Industry Machinery,  | 10/10 | 8/10 | 50.5% (+42bp/yr) | net cash | -28.0% | 99 | — |
| 48 | APH | AMPHENOL CORPORATION | Electronic Connectors | 10/10 | 9/10 | 36.9% (+25bp/yr) | 0.60x | +0.9% | 100 | — |
| 49 | FAST | FASTENAL CO | Retail-Building Materials, H | 10/10 | 10/10 | 45.0% (-56bp/yr) | net cash | -1.5% | 100 | — |
| 50 | WSM | WILLIAMS-SONOMA, INC. | Retail-Home Furniture, Furni | 10/10 | 8/10 | 46.2% (+109bp/yr) | net cash | -33.1% | 100 | — |
| 51 | GRMN | GARMIN LTD | Search, Detection, Navigatio | 10/10 | 9/10 | 58.7% (+27bp/yr) | net cash | +1.3% | 100 | — |

### Caveats carried by individual names

- **CMG** — DEBT-PARTIAL(6 year(s) before the first reported debt treated as DEBT-FREE, of 13 years); GM-UNAVAILABLE-WAIVED(fewer than 5 reported gross-margin years)
- **DPZ** — ROIC_UNBOUNDED(negative invested capital in >=1yr — buyback-driven; court must re-check)
- **ROL** — EBIT-FROM-PRETAX(no OperatingIncomeLoss tag in >=1yr — EBIT approximated as pretax + interest expense, which leaves other non-operating income in; reads HIGH); DEBT-PARTIAL(6 year(s) before the first reported debt treated as DEBT-FREE, of 13 years)
- **NKE** — EBIT-FROM-PRETAX(no OperatingIncomeLoss tag in >=1yr — EBIT approximated as pretax + interest expense, which leaves other non-operating income in; reads HIGH)
- **PYPL** — DEBT-PARTIAL(3 year(s) before the first reported debt treated as DEBT-FREE, of 13 years); GM-UNAVAILABLE-WAIVED(fewer than 5 reported gross-margin years)
- **FDS** — DEBT-PARTIAL(1 year(s) before the first reported debt treated as DEBT-FREE, of 13 years)
- **CLX** — EBIT-FROM-PRETAX(no OperatingIncomeLoss tag in >=1yr — EBIT approximated as pretax + interest expense, which leaves other non-operating income in; reads HIGH)
- **FIZZ** — EBIT-FROM-PRETAX(no OperatingIncomeLoss tag in >=1yr — EBIT approximated as pretax + interest expense, which leaves other non-operating income in; reads HIGH); DEBT-PARTIAL(5 interior year(s) interpolated from adjacent reported years, of 13 years)
- **META** — DEBT-PARTIAL(4 interior year(s) interpolated from adjacent reported years, of 13 years)
- **QLYS** — NO-DEBT-TAG(no debt concept in the window — treated as debt-free); ROIC_UNBOUNDED(negative invested capital in >=1yr — buyback-driven; court must re-check)
- **TSCO** — DEBT-PARTIAL(2 year(s) before the first reported debt treated as DEBT-FREE, of 13 years)
- **NVR** — EBIT-FROM-PRETAX(no OperatingIncomeLoss tag in >=1yr — EBIT approximated as pretax + interest expense, which leaves other non-operating income in; reads HIGH); GM-UNAVAILABLE-WAIVED(fewer than 5 reported gross-margin years)
- **MA** — GM-UNAVAILABLE-WAIVED(fewer than 5 reported gross-margin years)
- **ULTA** — DEBT-PARTIAL(12 year(s) before the first reported debt treated as DEBT-FREE, of 13 years)
- **COLM** — DEBT-PARTIAL(2 year(s) before the first reported debt treated as DEBT-FREE, of 13 years)
- **JNJ** — EBIT-FROM-PRETAX(no OperatingIncomeLoss tag in >=1yr — EBIT approximated as pretax + interest expense, which leaves other non-operating income in; reads HIGH)
- **MTD** — EBIT-FROM-PRETAX(no OperatingIncomeLoss tag in >=1yr — EBIT approximated as pretax + interest expense, which leaves other non-operating income in; reads HIGH)
- **EXP** — EBIT-FROM-PRETAX(no OperatingIncomeLoss tag in >=1yr — EBIT approximated as pretax + interest expense, which leaves other non-operating income in; reads HIGH)
- **MCO** — ROIC_UNBOUNDED(negative invested capital in >=1yr — buyback-driven; court must re-check)
- **LLY** — EBIT-FROM-PRETAX(no OperatingIncomeLoss tag in >=1yr — EBIT approximated as pretax + interest expense, which leaves other non-operating income in; reads HIGH)
- **FTNT** — DEBT-PARTIAL(7 year(s) before the first reported debt treated as DEBT-FREE, of 13 years); ROIC_UNBOUNDED(negative invested capital in >=1yr — buyback-driven; court must re-check)
- **VRSN** — ROIC_UNBOUNDED(negative invested capital in >=1yr — buyback-driven; court must re-check)
- **UPS** — GM-UNAVAILABLE-WAIVED(fewer than 5 reported gross-margin years)
- **LOGI** — NO-DEBT-TAG(no debt concept in the window — treated as debt-free)
- **CDNS** — GM-UNAVAILABLE-WAIVED(fewer than 5 reported gross-margin years)
- **TJX** — EBIT-FROM-PRETAX(no OperatingIncomeLoss tag in >=1yr — EBIT approximated as pretax + interest expense, which leaves other non-operating income in; reads HIGH)
- **TXRH** — DEBT-PARTIAL(1 interior year(s) interpolated from adjacent reported years, of 13 years); GM-UNAVAILABLE-WAIVED(fewer than 5 reported gross-margin years)
- **ROST** — EBIT-FROM-PRETAX(no OperatingIncomeLoss tag in >=1yr — EBIT approximated as pretax + interest expense, which leaves other non-operating income in; reads HIGH)
- **FFIV** — DEBT-PARTIAL(6 year(s) before the first reported debt treated as DEBT-FREE, of 13 years)
- **BKNG** — ROIC_UNBOUNDED(negative invested capital in >=1yr — buyback-driven; court must re-check); GM-UNAVAILABLE-WAIVED(fewer than 5 reported gross-margin years)
- **EW** — EBIT-FROM-PRETAX(no OperatingIncomeLoss tag in >=1yr — EBIT approximated as pretax + interest expense, which leaves other non-operating income in; reads HIGH)
- **WSM** — DEBT-PARTIAL(2 interior year(s) interpolated from adjacent reported years, of 13 years)
- **GRMN** — NO-DEBT-TAG(no debt concept in the window — treated as debt-free)

---

## Near misses (89) — failed on exactly one of the five tests

The gate is deliberately strict, and it produced fewer candidates than the design sketch assumed. These are the names it turned away on a single count, with the count named, so the shortlist can be widened by JUDGEMENT rather than by quietly loosening a threshold. Nothing here has a valuation band computed — adding a name to the active list gives it one on the next run.


**Return on invested capital cleared 15% in too few years** (40)

- **A** AGILENT TECHNOLOGIES, INC. — ROIC>15% in only 6/10yrs (need 8)
- **ADSK** AUTODESK, INC. — ROIC>15% in only 7/10yrs (need 8)
- **AEIS** ADVANCED ENERGY INDUSTRIES, INC. — ROIC>15% in only 6/10yrs (need 8)
- **AIT** APPLIED INDUSTRIAL TECHNOLOGIES, INC. — ROIC>15% in only 6/10yrs (need 8)
- **AME** AMETEK, Inc. — ROIC>15% in only 0/10yrs (need 8)
- **CAH** Cardinal Health, Inc. — ROIC>15% in only 4/9yrs (need 8)
- **CBRE** CBRE GROUP, INC. — ROIC>15% in only 3/10yrs (need 8)
- **CHD** CHURCH & DWIGHT CO., INC. — ROIC>15% in only 4/10yrs (need 8)
- **DAL** DELTA AIR LINES, INC. — ROIC>15% in only 7/10yrs (need 8)
- **DHI** D.R. Horton, Inc. — ROIC>15% in only 5/10yrs (need 8)
- **DLTR** DOLLAR TREE, INC. — ROIC>15% in only 4/10yrs (need 8)
- **ETN** EATON CORPORATION plc — ROIC>15% in only 0/10yrs (need 8)
- **EXPE** EXPEDIA GROUP, INC. — ROIC>15% in only 4/10yrs (need 8)
- **FOX** Fox Corp — ROIC>15% in only 4/10yrs (need 8)
- **FOXA** Fox Corp — ROIC>15% in only 4/10yrs (need 8)
- **GD** GENERAL DYNAMICS CORPORATION — ROIC>15% in only 4/10yrs (need 8)
- **GNRC** GENERAC HOLDINGS INC. — ROIC>15% in only 5/10yrs (need 8)
- **HUBB** HUBBELL INC — ROIC>15% in only 5/10yrs (need 8)
- **HWKN** HAWKINS, INC. — ROIC>15% in only 1/10yrs (need 8)
- **IBP** Installed Building Products, Inc. — ROIC>15% in only 6/10yrs (need 8)
- **IESC** IES Holdings, Inc. — ROIC>15% in only 6/10yrs (need 8)
- **IEX** IDEX CORP — ROIC>15% in only 5/10yrs (need 8)
- **JBL** JABIL INC — ROIC>15% in only 5/10yrs (need 8)
- **KEYS** KEYSIGHT TECHNOLOGIES, INC. — ROIC>15% in only 6/10yrs (need 8)
- **LUV** SOUTHWEST AIRLINES CO. — ROIC>15% in only 5/10yrs (need 8)
- **MAR** MARRIOTT INTERNATIONAL INC /MD/ — ROIC>15% in only 7/10yrs (need 8)
- **MDT** Medtronic plc — ROIC>15% in only 0/10yrs (need 8)
- **MRK** Merck & Co., Inc. — ROIC>15% in only 6/10yrs (need 8)
- **NOC** NORTHROP GRUMMAN CORP /DE/ — ROIC>15% in only 6/10yrs (need 8)
- **PAG** Penske Automotive Group, Inc. — ROIC>15% in only 3/10yrs (need 8)
- **PG** PROCTER & GAMBLE CO — ROIC>15% in only 7/10yrs (need 8)
- **PHM** PULTEGROUP, INC. — ROIC>15% in only 7/10yrs (need 8)
- **PPC** PILGRIM’S PRIDE CORPORATION — ROIC>15% in only 6/10yrs (need 8)
- **RPM** RPM INTERNATIONAL INC. — ROIC>15% in only 1/10yrs (need 8)
- **SYK** STRYKER CORP — ROIC>15% in only 0/10yrs (need 8)
- **TT** TRANE TECHNOLOGIES PLC — ROIC>15% in only 6/10yrs (need 8)
- **UAL** United Airlines Holdings, Inc. — ROIC>15% in only 4/10yrs (need 8)
- **VMC** VULCAN MATERIALS COMPANY — ROIC>15% in only 0/10yrs (need 8)
- **WMT** WALMART INC. — ROIC>15% in only 4/10yrs (need 8)
- **WTS** WATTS WATER TECHNOLOGIES INC — ROIC>15% in only 5/10yrs (need 8)

**Revenue fell in more years than the durability test allows** (27)

- **AAPL** Apple Inc. — revenue rose in only 7/10yrs (need 8)
- **AOS** A. O. Smith Corporation — revenue rose in only 7/10yrs (need 8)
- **BBY** BEST BUY CO., INC. — revenue rose in only 6/10yrs (need 8)
- **BF-A** Brown-Forman Corporation — revenue rose in only 6/10yrs (need 8)
- **BF-B** Brown-Forman Corporation — revenue rose in only 6/10yrs (need 8)
- **CMI** CUMMINS INC. — revenue rose in only 6/10yrs (need 8)
- **CSCO** CISCO SYSTEMS, INC. — revenue rose in only 7/10yrs (need 8)
- **EXPD** EXPEDITORS INTERNATIONAL OF WASHINGTON,  — revenue rose in only 7/10yrs (need 8)
- **GM** GENERAL MOTORS COMPANY — revenue rose in only 5/10yrs (need 8)
- **HON** Honeywell International Inc — revenue rose in only 7/10yrs (need 8)
- **HPQ** HP INC. — revenue rose in only 5/10yrs (need 8)
- **HRB** H&R Block, Inc. — revenue rose in only 6/9yrs (need 8)
- **ITW** ILLINOIS TOOL WORKS INC — revenue rose in only 7/10yrs (need 8)
- **LII** LENNOX INTERNATIONAL INC — revenue rose in only 7/10yrs (need 8)
- **LSTR** LANDSTAR SYSTEM, INC. — revenue rose in only 5/10yrs (need 8)
- **MAS** Masco Corporation — revenue rose in only 6/10yrs (need 8)
- **NTAP** NetApp, Inc. — revenue rose in only 7/10yrs (need 8)
- **ODFL** OLD DOMINION FREIGHT LINE, INC. — revenue rose in only 5/9yrs (need 8)
- **PCAR** PACCAR Inc — revenue rose in only 6/10yrs (need 8)
- **RL** Ralph Lauren Corporation — revenue rose in only 6/10yrs (need 8)
- **ROK** Rockwell Automation, Inc. — revenue rose in only 7/10yrs (need 8)
- **SNA** Snap-on Inc — revenue rose in only 6/10yrs (need 8)
- **TER** TERADYNE, INC. — revenue rose in only 7/10yrs (need 8)
- **TGT** TARGET CORPORATION — revenue rose in only 6/10yrs (need 8)
- **TPR** Tapestry, Inc. — revenue rose in only 7/10yrs (need 8)
- **VC** VISTEON CORP — revenue rose in only 3/10yrs (need 8)
- **WAT** Waters Corporation — revenue rose in only 7/10yrs (need 8)

**Carries more than two turns of net debt** (11)

- **AZO** AUTOZONE INC — net debt/EBITDA 2.03x (max 2.0)
- **CDW** CDW CORP — net debt/EBITDA 2.58x (max 2.0)
- **FICO** FAIR ISAAC CORP — net debt/EBITDA 3.11x (max 2.0)
- **HD** HOME DEPOT, INC. — net debt/EBITDA 2.17x (max 2.0)
- **LOW** LOWE’S COMPANIES, INC. — net debt/EBITDA 3.31x (max 2.0)
- **MSCI** MSCI INC. — net debt/EBITDA 3.27x (max 2.0)
- **MSI** Motorola Solutions, Inc. — net debt/EBITDA 2.12x (max 2.0)
- **PEP** PepsiCo, Inc. — net debt/EBITDA 2.65x (max 2.0)
- **PM** Philip Morris International Inc. — net debt/EBITDA 2.59x (max 2.0)
- **SBUX** Starbucks Corporation — net debt/EBITDA 2.68x (max 2.0)
- **SHW** THE SHERWIN-WILLIAMS COMPANY — net debt/EBITDA 2.32x (max 2.0)

**Diluted share count grew across the decade** (8)

- **AMZN** AMAZON COM INC — diluted shares +13.5% over the window (max +2%)
- **ANET** Arista Networks, Inc. — diluted shares +11.7% over the window (max +2%)
- **MPWR** Monolithic Power Systems, Inc. — diluted shares +18.2% over the window (max +2%)
- **NVDA** NVIDIA CORP — diluted shares +7.7% over the window (max +2%)
- **RMD** ResMed Inc. — diluted shares +3.1% over the window (max +2%)
- **VEEV** Veeva Systems Inc. — diluted shares +15.2% over the window (max +2%)
- **VRTX** VERTEX PHARMACEUTICALS INC / MA — diluted shares +6.9% over the window (max +2%)
- **ZM** Zoom Communications, Inc. — diluted shares +293.4% over the window (max +2%)

**Gross margin eroding** (3)

- **ALGN** ALIGN TECHNOLOGY, INC. — gross margin eroding: slope -78bps/yr and latest -527bps vs 10yr median
- **F** Ford Motor Co — gross margin eroding: slope -57bps/yr and latest -813bps vs 10yr median
- **MNST** Monster Beverage Corp — gross margin eroding: slope -104bps/yr and latest -338bps vs 10yr median

---

## Insufficient history (189) — neither passed nor failed

Recent listings, spin-offs, foreign private issuers and names whose tagged filings do not reach back eight years. They are excluded from the candidate list because the gate has no opinion on them, not because they failed it.

- **NO-XBRL** (83): AGI, ALC, AMX, ASML, AUGO, AZN, B, BABA, BEPC, BHP, BIDU, BLTE, BP, BTE, BTG, BTI, BUD, BZ, CAAP, CHT, CLBT, CMS-PB, CNI, CPA, DNN, DOX, E, EMBJ, EQNR, EQX, ERIC, ESLT, FMS, FMX, FSV, GDS, GDV, GFI, HTHT, ICL, ICLR, IHS, JD, JPC, KEP, KGC, MWH, NAD, NBIS, NGG, NTES, NVG, NVS, NXE, OGC, PBR, PBR-A, QH, RELX, RIO, RYAAY, SGHC, SIND, SKHY, SKM, SNN, SONY, TAL, TECK, TLK, TM, TME, TNK, TRP, TSM, TTAM, TTE, UGP, UL, VIPS, VOD, WSE, XE
- **INSUFFICIENT-HISTORY 0/8 usable years** (22): APA, ARCC, BELFA, BKR, COGT, CP, CQP, DKL, ENB, EPD, ERAS, ET, IMO, INFQ, INVH, LYB, MPLX, SUN, UHAL, UHAL-B, V, WMG
- **INSUFFICIENT-HISTORY 7/8 usable years** (20): ABNB, APPN, AUR, AVPT, BE, BEAM, CPNG, CRWD, DASH, DELL, DTM, HLIO, KMI, MRNA, P, PANW, PRVA, SCCO, SNOW, TWLO
- **INSUFFICIENT-HISTORY 3/8 usable years** (16): CGON, DTE, FIG, GDDY, HTFL, IOVA, LOAR, LUNR, NTSK, SDRL, SNDK, SUNB, TKO, VNOM, WSO, WSO-B
- **INSUFFICIENT-HISTORY 4/8 usable years** (14): BKV, CASY, CVNA, FERG, GEV, GOOG, INGM, RGTI, SHOP, SOLV, SRRK, SW, VLTO, XEL
- **INSUFFICIENT-HISTORY 6/8 usable years** (11): BTU, DKNG, LQDA, LYV, MDB, OSW, TDG, WBD, WFRD, XENE, ZLAB
- **INSUFFICIENT-HISTORY 5/8 usable years** (8): COKE, CR, GEHC, GRND, KGS, KVUE, NRIX, PHIN
- **INSUFFICIENT-HISTORY 7/8 revenue year-on-year comparisons** (6): AWK, CARR, CTVA, NEE, OTIS, SPHR
- **INSUFFICIENT-HISTORY 2/8 usable years** (3): ATAI, PSKY, VG
- **SIC-UNRESOLVED** (2): BF.B, BRK.B
- **INSUFFICIENT-HISTORY 1/8 usable years** (2): MDLN, VTRS
- **INSUFFICIENT-HISTORY 2/8 computable ROIC years** (1): W
- **INSUFFICIENT-HISTORY 6/8 computable ROIC years** (1): CHRN

---

*Generated by `verticals/generators/quality_wishlist.py --screen`. Sleeve cap for anything that eventually comes out of this list: 8% of the book in aggregate.*
