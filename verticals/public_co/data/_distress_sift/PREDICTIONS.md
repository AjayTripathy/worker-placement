# Public-co Distress Predictions — Forward Test (v1)

_Generated 2026-05-16T18:42:52.249198Z — `verticals.public_co.distress_sift` + `distress_deepread`_

## What this is

Concrete forward bets on a cohort of US-listed public companies that concentrate multiple distress fingerprints in their SEC filings. Built by:

1. Sweeping the SEC EDGAR full-text search (EFTS) API for six distinct distress phrases in filings since 2026-01-01 (going-concern qualifier, reverse stock split, change in auditor, minimum-bid-price deficiency, at-the-market offering, stock-for-services payment).
2. Aggregating by CIK and filtering to companies with ≥3 distinct distress signals concentrated in a single 5-month window.
3. Pulling each company's most recent XBRL-tagged financial facts via the SEC's free `companyfacts` API to compute cash position, trailing-quarter operating burn, and implied runway in months.
4. Producing per-company forward predictions with explicit falsification criteria (date + observable outcome).

**The signal:** companies in the critical (<6 mo runway) tier have a materially higher base rate of bankruptcy / further reverse-split / delisting / large-dilution events over the following 12 months than the broader Russell 3000 distress cohort. Whether the framework's discrimination is real on this specific cohort is the testable claim.

## Topline

| Tier | Count |
|---|---:|
| 🔴 CRITICAL (<6 mo runway) | 21 |
| 🟠 WARN (6-12 mo runway) | 4 |
| 🟡 WATCH (12-24 mo runway — multi-signal but adequately funded) | 4 |
| 🟢 OK (24+ mo runway — sift false-positive) | 1 |
| ⚪ UNKNOWN (XBRL data unavailable) | 0 |

## CRITICAL tier — sub-6-month runway, multiple signals

Forward bets are highest-conviction here. Listed in order of recency of latest report.

### Tenon Medical, Inc.  (TNON, TNONW)  (CIK 0001560293) (CIK 1560293)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2026-03-31):** $4.6M
- **Trailing-quarter operating burn:** $2.96M (≈ $0.99M/mo)
- **Implied runway:** 4.7 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1560293

**Forward bet:** by **2027-03-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2026-03-31 is 4.7 months (cash $4.6M ÷ monthly burn $0.99M).  
**Falsification:** if by 2027-03-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### CYABRA, INC.  (CYAB)  (CIK 0002032341) (CIK 2032341)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2026-03-31):** $3.1M
- **Trailing-quarter operating burn:** $2.60M (≈ $0.87M/mo)
- **Implied runway:** 3.6 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=2032341

**Forward bet:** by **2027-03-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2026-03-31 is 3.6 months (cash $3.1M ÷ monthly burn $0.87M).  
**Falsification:** if by 2027-03-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### Canton Strategic Holdings, Inc.  (CNTN, THAR)  (CIK 0001861657) (CIK 1861657)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2026-03-31):** $7.6M
- **Trailing-quarter operating burn:** $7.64M (≈ $2.55M/mo)
- **Implied runway:** 3.0 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1861657

**Forward bet:** by **2027-03-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2026-03-31 is 3.0 months (cash $7.6M ÷ monthly burn $2.55M).  
**Falsification:** if by 2027-03-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### XCel Brands, Inc.  (XELB)  (CIK 0001083220) (CIK 1083220)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2026-03-31):** $0.2M
- **Trailing-quarter operating burn:** $0.88M (≈ $0.29M/mo)
- **Implied runway:** 0.6 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1083220

**Forward bet:** by **2027-03-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2026-03-31 is 0.6 months (cash $0.2M ÷ monthly burn $0.29M).  
**Falsification:** if by 2027-03-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### Sky Quarry Inc.  (SKYQ)  (CIK 0001812447) (CIK 1812447)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2026-03-31):** $0.8M
- **Trailing-quarter operating burn:** $0.59M (≈ $0.20M/mo)
- **Implied runway:** 4.3 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1812447

**Forward bet:** by **2027-03-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2026-03-31 is 4.3 months (cash $0.8M ÷ monthly burn $0.20M).  
**Falsification:** if by 2027-03-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### GeoVax Labs, Inc.  (GOVX)  (CIK 0000832489) (CIK 832489)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2026-03-31):** $1.3M
- **Trailing-quarter operating burn:** $3.54M (≈ $1.18M/mo)
- **Implied runway:** 1.1 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=832489

**Forward bet:** by **2027-03-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2026-03-31 is 1.1 months (cash $1.3M ÷ monthly burn $1.18M).  
**Falsification:** if by 2027-03-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### Fusemachines Inc.  (FUSE, FUSEW)  (CIK 0002033383) (CIK 2033383)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2026-03-31):** $1.8M
- **Trailing-quarter operating burn:** $2.22M (≈ $0.74M/mo)
- **Implied runway:** 2.4 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=2033383

**Forward bet:** by **2027-03-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2026-03-31 is 2.4 months (cash $1.8M ÷ monthly burn $0.74M).  
**Falsification:** if by 2027-03-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### HCW Biologics Inc.  (HCWB)  (CIK 0001828673) (CIK 1828673)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2026-03-31):** $1.2M
- **Trailing-quarter operating burn:** $1.58M (≈ $0.53M/mo)
- **Implied runway:** 2.3 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1828673

**Forward bet:** by **2027-03-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2026-03-31 is 2.3 months (cash $1.2M ÷ monthly burn $0.53M).  
**Falsification:** if by 2027-03-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### reAlpha Tech Corp.  (AIRE)  (CIK 0001859199) (CIK 1859199)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2026-03-31):** $4.7M
- **Trailing-quarter operating burn:** $3.12M (≈ $1.04M/mo)
- **Implied runway:** 4.5 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1859199

**Forward bet:** by **2027-03-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2026-03-31 is 4.5 months (cash $4.7M ÷ monthly burn $1.04M).  
**Falsification:** if by 2027-03-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### VOLITIONRX LTD  (VNRX)  (CIK 0000093314) (CIK 93314)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2026-03-31):** $1.1M
- **Trailing-quarter operating burn:** $5.28M (≈ $1.76M/mo)
- **Implied runway:** 0.6 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=93314

**Forward bet:** by **2027-03-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2026-03-31 is 0.6 months (cash $1.1M ÷ monthly burn $1.76M).  
**Falsification:** if by 2027-03-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### FEMASYS INC  (FEMY)  (CIK 0001339005) (CIK 1339005)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2026-03-31):** $5.4M
- **Trailing-quarter operating burn:** $4.14M (≈ $1.38M/mo)
- **Implied runway:** 3.9 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1339005

**Forward bet:** by **2027-03-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2026-03-31 is 3.9 months (cash $5.4M ÷ monthly burn $1.38M).  
**Falsification:** if by 2027-03-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### Tivic Health Systems, Inc.  (TIVC)  (CIK 0001787740) (CIK 1787740)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2026-03-31):** $7.2M
- **Trailing-quarter operating burn:** $5.01M (≈ $1.67M/mo)
- **Implied runway:** 4.3 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1787740

**Forward bet:** by **2027-03-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2026-03-31 is 4.3 months (cash $7.2M ÷ monthly burn $1.67M).  
**Falsification:** if by 2027-03-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### Trio Petroleum Corp  (TPET)  (CIK 0001898766) (CIK 1898766)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2026-01-31):** $0.3M
- **Trailing-quarter operating burn:** $0.53M (≈ $0.18M/mo)
- **Implied runway:** 2.0 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1898766

**Forward bet:** by **2027-01-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2026-01-31 is 2.0 months (cash $0.3M ÷ monthly burn $0.18M).  
**Falsification:** if by 2027-01-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### Alzamend Neuro, Inc.  (ALZN)  (CIK 0001677077) (CIK 1677077)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2026-01-31):** $2.7M
- **Trailing-quarter operating burn:** $5.27M (≈ $1.76M/mo)
- **Implied runway:** 1.5 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1677077

**Forward bet:** by **2027-01-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2026-01-31 is 1.5 months (cash $2.7M ÷ monthly burn $1.76M).  
**Falsification:** if by 2027-01-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### MOBIX LABS, INC  (MOBX, MOBXW)  (CIK 0001855467) (CIK 1855467)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2025-12-31):** $0.0M
- **Trailing-quarter operating burn:** $4.76M (≈ $1.59M/mo)
- **Implied runway:** 0.0 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1855467

**Forward bet:** by **2026-12-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2025-12-31 is 0.0 months (cash $0.0M ÷ monthly burn $1.59M).  
**Falsification:** if by 2026-12-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### Catheter Precision, Inc.  (VTAK)  (CIK 0001716621) (CIK 1716621)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2025-12-31):** $0.1M
- **Trailing-quarter operating burn:** $6.78M (≈ $2.26M/mo)
- **Implied runway:** 0.0 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1716621

**Forward bet:** by **2026-12-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2025-12-31 is 0.0 months (cash $0.1M ÷ monthly burn $2.26M).  
**Falsification:** if by 2026-12-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### CDT Equity Inc.  (CDT, CDTTW)  (CIK 0001896212) (CIK 1896212)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2025-12-31):** $1.5M
- **Trailing-quarter operating burn:** $10.92M (≈ $3.64M/mo)
- **Implied runway:** 0.4 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1896212

**Forward bet:** by **2026-12-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2025-12-31 is 0.4 months (cash $1.5M ÷ monthly burn $3.64M).  
**Falsification:** if by 2026-12-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### Sow Good Inc.  (SOWG)  (CIK 0001490161) (CIK 1490161)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2025-12-31):** $1.5M
- **Trailing-quarter operating burn:** $3.34M (≈ $1.11M/mo)
- **Implied runway:** 1.3 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1490161

**Forward bet:** by **2026-12-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2025-12-31 is 1.3 months (cash $1.5M ÷ monthly burn $1.11M).  
**Falsification:** if by 2026-12-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### Modular Medical, Inc.  (MODD)  (CIK 0001074871) (CIK 1074871)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2025-12-31):** $2.9M
- **Trailing-quarter operating burn:** $17.94M (≈ $5.98M/mo)
- **Implied runway:** 0.5 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1074871

**Forward bet:** by **2026-12-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2025-12-31 is 0.5 months (cash $2.9M ÷ monthly burn $5.98M).  
**Falsification:** if by 2026-12-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### Interactive Strength, Inc.  (TRNR)  (CIK 0001785056) (CIK 1785056)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2025-12-31):** $0.5M
- **Trailing-quarter operating burn:** $8.16M (≈ $2.72M/mo)
- **Implied runway:** 0.2 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1785056

**Forward bet:** by **2026-12-31** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2025-12-31 is 0.2 months (cash $0.5M ÷ monthly burn $2.72M).  
**Falsification:** if by 2026-12-31 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

### SunPower Inc.  (SPWR, SPWRW)  (CIK 0001838987) (CIK 1838987)

- **Signals concentrated 2026-01-01 → present:** atm_offering, going_concern, reverse_split
- **Cash + equivalents (as of 2025-12-28):** $9.6M
- **Trailing-quarter operating burn:** $13.41M (≈ $4.47M/mo)
- **Implied runway:** 2.2 months
- **EDGAR filings:** https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1838987

**Forward bet:** by **2026-12-28** this company will have done at least one of: (a) filed Chapter 11 / Chapter 7 / receivership; (b) executed another reverse stock split; (c) raised another ≥10%-dilutive equity offering; (d) been delisted from its primary exchange. Implied runway as of 2025-12-28 is 2.2 months (cash $9.6M ÷ monthly burn $4.47M).  
**Falsification:** if by 2026-12-28 the company is still listed on the same exchange, has not split, has not raised ≥10% dilutive equity, and has not entered bankruptcy proceedings, this prediction is wrong.

## WARN tier — 6-12 month runway

Capital raise required within a year; bankruptcy possible but not imminent.

- **PAVmed Inc.  (PAVM)  (CIK 0001624326)** (CIK 1624326) — cash $6.5M, burn $0.87M/mo, runway 7.4 mo (as of 2026-03-31)
- **Functional Brands Inc.  (MEHA)  (CIK 0001837254)** (CIK 1837254) — cash $1.1M, burn $0.14M/mo, runway 7.6 mo (as of 2026-03-31)
- **iBio, Inc.  (IBIO)  (CIK 0001420720)** (CIK 1420720) — cash $47.6M, burn $5.66M/mo, runway 8.4 mo (as of 2026-03-31)
- **Caring Brands, Inc.  (CABR)  (CIK 0002020737)** (CIK 2020737) — cash $2.0M, burn $0.18M/mo, runway 11.1 mo (as of 2026-03-31)

## WATCH tier — 12-24 month runway despite multi-signal

Sift surfaced these via the distress-phrase search but XBRL says they are adequately funded. Either the sift signal is forward-looking (reverse split to maintain listing, ATM filed but unused) OR the financial picture is deteriorating below what the most recent XBRL filing shows.

- **Jet.AI Inc.  (JTAI)  (CIK 0001861622)** (CIK 1861622) — cash $13.5M, burn $1.01M/mo, runway 13.3 mo
- **FOCUS UNIVERSAL INC.  (FCUV)  (CIK 0001590418)** (CIK 1590418) — cash $5.4M, burn $0.38M/mo, runway 14.0 mo
- **SPRUCE BIOSCIENCES, INC.  (SPRB)  (CIK 0001683553)** (CIK 1683553) — cash $54.1M, burn $2.91M/mo, runway 18.6 mo
- **LQR House Inc.  (YHC)  (CIK 0001843165)** (CIK 1843165) — cash $10.0M, burn $0.48M/mo, runway 20.8 mo

## OK tier — sift false-positives

Multi-signal hits but cash position > 24 months of burn. Acknowledged as sift false-positives. Useful for understanding the rule's noise floor.

- **Aprea Therapeutics, Inc.  (APRE)  (CIK 0001781983)** (CIK 1781983) — cash $46.5M; reasons for distress signals not solvency-driven

## How to read this — and debt/tradeoffs

**What this is:** a structural distress-pattern screen producing per-company concrete forward bets. The bets fall in three shapes: (a) bankruptcy / reverse split / large-dilution / delisting within 12 months of the latest 10-Q for CRITICAL tier; (b) capital raise required for WARN; (c) survival prediction for WATCH/OK.

**What this is NOT:** a fraud signal. None of the cohort is being accused of any wrongdoing. Going-concern qualifiers and ATM offerings are legal and disclosed. The prediction is about *outcome*, not *malfeasance*.

### Debt + tradeoffs in v1

- **Single-source XBRL.** Cash and burn come from the most recent XBRL-tagged 10-Q. Companies file XBRL inconsistently; some concepts (e.g., `CashAndCashEquivalentsAtCarryingValue` vs. `Cash` vs. composite concept) can mismatch. Cross-check with the actual 10-Q text before trading on the signal.
- **Operating burn is trailing-quarter only.** A company may have accelerated cost cuts after the latest quarter end that this signal misses. Some of the CRITICAL tier may have already raised since the report date (`Aprea Therapeutics` is the obvious OK example — they did raise post-quarter).
- **EDGAR full-text search caps at 1,000 hits per query.** The `reverse_split` query maxed out — there are >1,000 reverse-split mentions in 2026 YTD. The sift undercounts. Tighter date-window queries would catch more.
- **No insider-selling cross-join yet.** The `public_co` vertical has EDGAR Form 4 / Form 144 access; cross-referencing with concentrated insider selling in the same window would tighten the signal further.
- **No market-cap or volume filter.** Several names in the cohort are essentially shell companies with <$10M market cap; these survive on dilution indefinitely without ever filing bankruptcy. A market-cap floor of $25M would meaningfully tighten the actionable cohort.
- **Calibration is structural, not empirical.** The <6-month, 6-12, 12-24 thresholds are author-declared. A held-out cohort of prior distress cases would let us tune them to maximize precision on the 12-month bankruptcy outcome (the Layer 3 Rule 6 violation).

### What the right next step is

1. **Pre-register the predictions.** Hash this file's contents and commit the hash to git or a public timestamp service so the falsification criteria can't be moved later.
2. **Wire Form 4 / Form 144 cross-join.** The `public_co/edgar.py` already fetches XML; add a Form 4/144 parser to surface concentrated insider exits in the same date window.
3. **Add market-cap / float filter.** Pull from XBRL `EntityCommonStockSharesOutstanding` and current price (Yahoo / Polygon free tier). Filter cohort to >$25M cap.
4. **Compute Layer 3 Rule 5 (stock-for-services) per company.** Already in `SIGNAL_QUERIES`; surface the explicit equity-for-services dollar amount from each company's MD&A.
