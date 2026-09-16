# Signal OS — Connector Queue (compile-phase output)

_Generated 2026-05-17T08:58:56.486454Z from 5 plan.json files._

**Total unique proposed connectors:** 12


Connectors are ranked by **reference count × cohort breadth × buildability** (free + no-auth + structured-API connectors first). Top-of-queue connectors are the cheapest path to unlocking adjudication for the most claims.

## Priority queue

### 1. `finra_brokercheck.query_firm` — FINRA BrokerCheck firm registration lookup
- **Referenced by:** 1 claim(s) across 1 ticker(s): COF
- **Endpoint:** `https://api.brokercheck.finra.org/search/firm`
- **Access:** api  (no auth)
- **Cost:** free  |  **Completeness:** all FINRA-member broker-dealers
- **Referent / Attribute:** entity / registration_status
- **Sample invocation:** `GET https://api.brokercheck.finra.org/search/firm?query=Capital%20One%20Securities&hl=true&nrows=12&start=0&r=25&sort=score+desc`
- **Rationales (per claim):**
  - `COF` / `COF-4` (regulatory_milestone): FINRA BrokerCheck is the authoritative, free, public registry of all U.S.-registered broker-dealers. Three named subsidiaries should each return a CRD record with status 'Approved' and SEC# present.

### 2. `fdic_bankfind.query_institution` — FDIC BankFind Suite institution registry; resolves an institution name/cert/RSSDID and returns charter class, primary regulator, status, and headquarters.
- **Referenced by:** 1 claim(s) across 1 ticker(s): SOFI
- **Endpoint:** `https://banks.data.fdic.gov/api/institutions`
- **Access:** api  (no auth)
- **Cost:** free  |  **Completeness:** All FDIC-insured US depository institutions
- **Referent / Attribute:** entity / charter_class
- **Sample invocation:** `GET https://banks.data.fdic.gov/api/institutions?filters=NAME:%22SoFi%20Bank%22&fields=NAME,CERT,FED_RSSD,CHRTAGNT,REGAGNT,ACTIVE,STALP,CITY`
- **Rationales (per claim):**
  - `SOFI` / `SOFI-1` (regulatory_milestone): OCC national-bank charter status, primary federal regulator, and FDIC insurance status are authoritative registry attributes that the FDIC BankFind Suite resolves directly by institution name.

### 3. `sec_abs15g.query_securitizer_filings` — SEC EDGAR ABS-15G / ABS-EE filings registry. Returns asset-backed securitizer disclosures (repurchase activity, pool composition) per CIK with filing date and document URLs.
- **Referenced by:** 1 claim(s) across 1 ticker(s): SOFI
- **Endpoint:** `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=ABS-15G&dateb=&owner=include&count=40`
- **Access:** api  (no auth)
- **Cost:** free  |  **Completeness:** All SEC-registered ABS securitizers (federally registered offerings only; 144A private deals partially covered via Form D)
- **Referent / Attribute:** loan_portfolio / pool_balance
- **Sample invocation:** `GET https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001818874&type=ABS-15G&dateb=20260516&owner=include&count=40`
- **Rationales (per claim):**
  - `SOFI` / `SOFI-3` (production_volume): Loan-platform third-party origination volume should flow through whole-loan-sale or ABS issuance channels; ABS-15G filings disclose securitizer repurchase activity and pool composition at the asset-po

### 4. `fhfa_fhlb.query_member_advances` — FHFA Federal Home Loan Bank member-advance disclosures and call-report-derived advance balances per member institution.
- **Referenced by:** 1 claim(s) across 1 ticker(s): SOFI
- **Endpoint:** `https://www.fhfa.gov/data/dashboard/fhlb-member-data`
- **Access:** csv_download  (no auth)
- **Cost:** free  |  **Completeness:** All FHLB member banks (FDIC-insured depository institutions and certain insurance companies)
- **Referent / Attribute:** loan_portfolio / advance_balance
- **Sample invocation:** `GET https://www.fhfa.gov/sites/default/files/data-files/fhlb-members.csv  (filter on member_name=='SoFi Bank, National Association')`
- **Rationales (per claim):**
  - `SOFI` / `SOFI-8` (vendor_relationship): FHLB membership and advance balances are reported by FHFA at the member-institution level; this is the authoritative registry for the FHLB-borrowing-capacity claim that the catalog's fdic_call_reports

### 5. `fdic_call_reports.consumer_loan_originations` — FDIC Call Report consumer-loan origination volume per institution (RSSDID-keyed quarterly schedules RC-C / RI). Lets analysts see whether named UPST partner banks (Cross River Bank, FinWise Bank, Customers Bank, etc.) show unsecured personal-loan portfolio levels consistent with UPST's reported 83% origination concentration.
- **Referenced by:** 1 claim(s) across 1 ticker(s): UPST
- **Endpoint:** `https://banks.data.fdic.gov/api/financials`
- **Access:** api  (no auth)
- **Cost:** free  |  **Completeness:** FDIC-chartered banks only (Cross River, FinWise, Customers, etc. are covered; non-bank purchasers are not)
- **Referent / Attribute:** loan_portfolio / consumer_loan_origination_volume
- **Sample invocation:** `GET https://banks.data.fdic.gov/api/financials?filters=RSSDID:58978%20AND%20REPDTE:20251231&fields=NAMEFULL,LNCONOTH,LNCON,LNATRESR&sort_by=REPDTE&limit=4`
- **Rationales (per claim):**
  - `UPST` / `UPST-1` (customer_pipeline): UPST does not name its top lending partners in the 10-K, but bank-partner Call Reports are the registry analog: if UPST's claimed 83% origination concentration is accurate, the partner banks' consumer

### 6. `sec_edgar.absee_loan_disclosures` — SEC EDGAR Asset-Backed Securities issuer reports (ABS-EE / 10-D / 424B) including loan-tape XML/XBRL exhibits. UPST is a sponsor of multiple securitization shelves; pool-level outstanding-balance data is filed periodically.
- **Referenced by:** 1 claim(s) across 1 ticker(s): UPST
- **Endpoint:** `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001647639&type=ABS-EE&dateb=&owner=include&count=40`
- **Access:** api  (no auth)
- **Cost:** free  |  **Completeness:** SEC-registered ABS only; private-pool sales and whole-loan sales to lending partners are not covered
- **Referent / Attribute:** loan_portfolio / outstanding_principal_balance
- **Sample invocation:** `GET https://data.sec.gov/submissions/CIK0001647639.json then filter forms ABS-EE/10-D/424B5; sum pool_principal_balance across active trusts.`
- **Rationales (per claim):**
  - `UPST` / `UPST-2` (production_volume): UPST-serviced loans flowing through securitizations are visible in ABS-EE filings (per Regulation AB) — total outstanding balance across all UPST-sponsored trusts is the registry analog for the servic

### 7. `nv_sos.query_entity` — Nevada Secretary of State business entity search (SilverFlume) — returns entity status, formation date, entity type, and registered agent for a corporate name.
- **Referenced by:** 1 claim(s) across 1 ticker(s): AFRM
- **Endpoint:** `https://www.nvsilverflume.gov/businessSearch`
- **Access:** scrape  (no auth)
- **Cost:** free  |  **Completeness:** All Nevada-domiciled entities
- **Referent / Attribute:** entity / incorporation_status
- **Sample invocation:** `POST businessSearch with {entityName: 'Affirm Holdings, Inc.'} ; parse status, NV file number, formation/conversion date.`
- **Rationales (per claim):**
  - `AFRM` / `AFRM-5` (regulatory_milestone): Reincorporation is a state-registry event; the only authoritative adjudicator is the destination state's Secretary-of-State business registry. EDGAR shows the filing but not the actual state record th

### 8. `nfa_basic.query_swap_dealer_registration` — NFA BASIC registry: provisional and full CFTC swap-dealer registration lookup by firm name or NFA ID
- **Referenced by:** 1 claim(s) across 1 ticker(s): COF
- **Endpoint:** `https://www.nfa.futures.org/basicnet/basic-profile.aspx`
- **Access:** scrape  (no auth)
- **Cost:** free  |  **Completeness:** all CFTC-registered swap dealers and major swap participants
- **Referent / Attribute:** entity / registration_status
- **Sample invocation:** `GET https://www.nfa.futures.org/basicnet/basic-profile.aspx?nfaid=<NFAID>; parse 'Swap Dealer' registration block`
- **Rationales (per claim):**
  - `COF` / `COF-3` (regulatory_milestone): CFTC swap-dealer registration is an authoritative, publicly searchable registry maintained by the National Futures Association under CFTC delegation. Claim is binary (registered/not) and registry-adju

### 9. `nmls.query_consumer_access` — NMLS Consumer Access — Nationwide Multistate Licensing System public registry for state-licensed mortgage companies and individual MLOs.
- **Referenced by:** 1 claim(s) across 1 ticker(s): OPEN
- **Endpoint:** `https://www.nmlsconsumeraccess.org/EntityDetails.aspx and https://www.nmlsconsumeraccess.org/Home.aspx/CompanySearch`
- **Access:** scrape  (no auth)
- **Cost:** free  |  **Completeness:** All state-licensed non-bank mortgage companies and individual MLOs (NMLS-participating states, which is all 50)
- **Referent / Attribute:** entity / license_status_by_state
- **Sample invocation:** `GET https://www.nmlsconsumeraccess.org/Home.aspx/CompanySearch with name='Opendoor' -> parse company-detail page for state licenses and license-status fields`
- **Rationales (per claim):**
  - `OPEN` / `OPEN-6` (regulatory_milestone): State mortgage-origination licensing has no SEC analog; NMLS is the authoritative public registry for non-bank mortgage lender licensing status across all 50 states.

### 10. `argentina_compras.query_public_tenders` — Argentine federal procurement portal COMPR.AR / Contrataciones del Estado tender registry. Returns public-sector tenders awarded by Banco de la Nación Argentina (a state-owned bank), including vendor name and contract value.
- **Referenced by:** 1 claim(s) across 1 ticker(s): SOFI
- **Endpoint:** `https://comprar.gob.ar/PublicacionOC.aspx`
- **Access:** scrape  (no auth)
- **Cost:** free  |  **Completeness:** Argentine federal public-sector procurement only; provincial coverage incomplete
- **Referent / Attribute:** entity / vendor_award_status
- **Sample invocation:** `GET https://comprar.gob.ar/PublicacionOC.aspx?qs=BUSCAR&entidad=Banco%20Naci%C3%B3n&proveedor=Technisys&desde=2024-01-01&hasta=2026-05-16`
- **Rationales (per claim):**
  - `SOFI` / `SOFI-5` (customer_pipeline): Banco Nación is a state-owned Argentine bank; vendor selections for core-banking modernization at state banks typically appear in the federal procurement registry. Provides authoritative independent c

### 11. `pacer.federal_court_docket` — PACER federal-court case docket lookup. Returns case caption, filing date, current status, certifying orders for a specific federal civil case number.
- **Referenced by:** 1 claim(s) across 1 ticker(s): UPST
- **Endpoint:** `https://pacer.uscourts.gov/ or https://www.courtlistener.com/api/rest/v3/dockets/ (RECAP mirror, free)`
- **Access:** api  (no auth)
- **Cost:** free (via CourtListener RECAP) or $0.10/page (direct PACER)  |  **Completeness:** all US federal civil dockets
- **Referent / Attribute:** event / case_status_and_certification_order
- **Sample invocation:** `GET https://www.courtlistener.com/api/rest/v3/dockets/?docket_number=2:22-cv-02935&court=ohsd`
- **Rationales (per claim):**
  - `UPST` / `UPST-4` (regulatory_milestone): The class-action existence, caption, court, and certification-order date are public PACER record; CourtListener's RECAP archive provides keyless free access. EDGAR full-text would only find UPST's own

### 12. `pacer.query_case_docket` — Federal court PACER docket retrieval for case-status and final-judgment verification on named civil cases.
- **Referenced by:** 1 claim(s) across 1 ticker(s): OPEN
- **Endpoint:** `https://pcl.uscourts.gov/pcl/index.jsf (PACER Case Locator) and per-court CM/ECF (e.g. https://ecf.azd.uscourts.gov)`
- **Access:** api  (auth required)
- **Cost:** $0.10/page on PACER; free via CourtListener RECAP  |  **Completeness:** All federal district / appellate court cases; bankruptcy and state cases excluded
- **Referent / Attribute:** event / final_judgment_status
- **Sample invocation:** `PACER Case Locator search court=azd, case_no=2:22-CV-01717-MTL -> CM/ECF docket pull -> filter for 'Final Judgment' entry; alternatively use CourtListener RECAP archive (https://www.courtlistener.com/api/rest/v3/dockets/?docket_number=2:22-`
- **Rationales (per claim):**
  - `OPEN` / `OPEN-5` (regulatory_milestone): Securities-class-action final disposition is an authoritative status only court dockets adjudicate; SEC filings are issuer-prepared and therefore self-referential. CourtListener / RECAP provides a fre
