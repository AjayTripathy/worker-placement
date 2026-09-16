# Connector Build Backlog

Ranked priority list for new M-source connectors. Derived from the
cross-cohort planner-proposal aggregation (`data/_backtest/2025_05_15/
proposals_backlog.json`) + post-build calibration findings.

## Priority 1 — Shipped (this session)

| Source | Status | Notes |
|---|---|---|
| `bls_qcew.query_county_naics` | ✅ CANONICAL | County+NAICS employment denominator for facility-scope plausibility |
| `nasa_ntrs.query_ntrs` | ✅ CANONICAL | NASA Technical Reports Server — collaboration corroboration |
| `ucc_proxy.query_ucc_exposure` | ✅ v0 (proxy) | SEC-filing-based lien-exposure detector. **Real state UCC remains priority 2** |

## Priority 2 — Known gap, future build

### Real state UCC connector (8/8 planner consensus)
**The proxy doesn't catch fraudulent omission.** A company that
files UCC-1s at the state level but fails to disclose them in
8-K/10-K filings looks LOW_LIEN_EXPOSURE to the proxy. This is a
documented fraud pattern:

- Microcap toxic-convertible financiers (Yorkville Advisors, GHS
  Investments, Geneva Roth, Magna Group, Iliad Research, Cornell
  Capital) routinely file UCC-1s against pink-sheet and small OTC
  issuers without corresponding 8-K disclosure
- SEC enforcement AAERs regularly cite this gap (see
  sec.gov/divisions/enforce/friactions.htm)
- Greensill-style off-balance-sheet receivables financing
- Subsidiary-level UCC filings that don't roll up to consolidated
  parent disclosure
- Categorization fraud (calling a UCC-secured note a "private
  placement" without secured-debt language)

**Blocked on infrastructure:** state UCC portals are uniformly behind
bot protection (CA bizfileonline / FL Sunbiz / NY new ucc-efiling /
NC sosnc.gov all use Cloudflare/Incapsula). Realistic paths:

1. **Paid aggregator API** (~$1.5-5k/yr): CSC Global, Wolters Kluwer,
   Lien Solutions, OpenCorporates premium. Cleanest. Recommended
   if/when a customer needs this signal.
2. **Browser-automation cluster** (Playwright + per-state HTML
   parsers + CAPTCHA-solver like 2Captcha): months of build, ongoing
   maintenance, legal-review of state TOS, fragile to portal changes.
   Not recommended unless the data is core IP.
3. **Direct state bulk-data subscriptions** (per-state, fee-based,
   formal registration). Patchwork of states; not all participate.

When built, the connector should support **reconciliation**: fetch
UCC-1s by company name (parent + subsidiaries from 10-K Ex-21), fetch
the company's 10-K secured-debt schedule, compare. UCC filings
absent from SEC disclosure = fraud signal.

## Priority 3 — Multi-ticker planner consensus (all currently blocked)

Probed each Priority 3 endpoint 2026-05-18. **All are blocked behind
the same kinds of access barriers as state UCC**: paid APIs, JS-
rendered widgets, ToS restrictions, or bot protection. The free-
public-API era for diligence data is essentially over for these
domains. Decision: document each with its access blocker, paid
aggregator that covers it, and an SEC-proxy alternative if one
exists. No build until customer demand justifies one of the paths.

### USPTO Patent Assignment Database (PAS) — 4/8 tickers
**Block:** legacy assignment-api.uspto.gov returns HTTP:000;
S3 bulk-download buckets at s3.amazonaws.com/data.patentsview.org
return 403; new PatentsView ODP API requires paid key
**Paid coverage:** PatentsView premium (~$500-2k/yr); LexisNexis
PatentSight; Innography (paid)
**SEC-proxy:** SEC filings disclose patent licensing transactions
under Item 1.01 (Material Definitive Agreement) for significant
deals. Use `edgar_fts` with "patent assignment" / "patent license"
/ "exclusive license" terms scoped to focal CIK. Captures only
material licenses, not the full assignment chain.
**When to build:** when a customer needs full patent-transfer
history (M&A target valuation; IP-as-collateral analysis).

### DoD program-office press releases (MDA/SF/AFRL) — 3/8 tickers
**Block:** multi-site custom scraping needed across mda.mil,
spaceforce.mil, afmc.af.mil, defense.gov; each has its own HTML
structure; no aggregator API
**Paid coverage:** Govini (defense-specific market intelligence);
Bloomberg Government; Defense News Premium
**SEC-proxy:** USAspending (already canonical) captures DoD AWARDS;
SEC 8-K filings disclose program-selection wins under Item 7.01
(Regulation FD Disclosure). Use `edgar_fts` for "DoD program" /
specific program names ("Replicator", "Blue UAS", "SBIR Phase III")
to detect company-disclosed program wins.
**When to build:** when defense-cohort coverage exceeds 20-30
tickers; current cohort (~10 names) is manageable via SEC + usaspending.

### LinkedIn headcount snapshot — 3/8 tickers
**Block:** ToS explicitly prohibits scraping; hiQ v. LinkedIn
appeal continues but commercial use carries legal risk
**Paid coverage:** LinkedIn Sales Navigator API ($X/user); RocketReach
($59-249/mo); Hunter.io for emails only
**SEC-proxy:** `dol_h1b_lca` (already canonical) covers H-1B-dense
companies. `osha_establishments` covers traditional manufacturing.
SEC 10-K Item 1.D ("Human Capital") discloses total headcount but
not per-site breakdown.
**When to build:** never under free model. Use `dol_h1b_lca` + 10-K
Item 1.D as the workforce-verification stack.

### Foreign business registries — 3/8 tickers
**Block:** per-jurisdiction (Singapore ACRA, Cayman Companies
Registry, BVI Financial Services Commission, EU TED procurement,
Bahamas Companies Registry); each has its own access pattern; most
behind Cloudflare/Incapsula like US state UCC
**Paid coverage:** OpenCorporates premium (~$1.5-5k/yr — best
aggregator for international entity data); Moody's Orbis (enterprise);
Refinitiv (enterprise)
**SEC-proxy:** SEC 10-K Item 1 (Business) describes foreign
subsidiaries. SEC 10-K Exhibit 21 lists all consolidated subsidiaries
with state/country of incorporation. `edgar_fts` for specific country
names + entity activity.
**When to build:** when targeting cohorts heavy in offshore-domiciled
small-caps (Cayman-incorporated SPACs, Bermuda-domiciled insurers,
BVI-shell penny stocks). OpenCorporates premium is the cleanest path.

### NASA SBIR/STTR Award Database — 2/8 tickers
**Block:** sbir.gov API is hard-rate-limited (429 on all endpoints
as of 2026-05-18); data.gov returns 0 SBIR datasets
**Paid coverage:** SBIR alumni reporting tools; Govini
**SEC-proxy:** Already covered by `usaspending.query_federal_presence`
which includes NASA SBIR Phase I/II awards. The unique value of
sbir.gov over usaspending would be Phase I "topic abstracts" and
"transition to Phase III" status — neither tracked elsewhere.
**When to build:** when planner needs to verify a specific SBIR topic
ID claim. Currently usaspending covers ~95% of the signal.

### PCAOB audit-firm registry — 2/8 tickers
**Block:** PCAOB website uses HawkSearch (third-party JS-rendered
search widget); no documented API endpoint; firm list requires
client-side JS rendering to query
**Paid coverage:** Audit Analytics (~$3k+/yr — covers PCAOB
inspection findings, auditor changes, restatements); BVD's Sirius
**SEC-proxy:** SEC 8-K Item 4.01 (Changes in Registrant's Certifying
Accountant) and Item 4.02 (Non-Reliance on Previously Issued
Financial Statements) are mandatory disclosures for any auditor
change or financial restatement. `edgar_fts` + `sec_filings` already
cover these. ~80% of the signal the PCAOB registry would add.
**When to build:** when PCAOB inspection findings (audit quality
ratings) become relevant for a specific cohort. Audit Analytics is
the cleanest paid path.

### SEMI / industry trade-association rosters — 2/8 tickers
**Block:** member-only access; SEMI World Fab Forecast is paid
($30k+/yr); AHRI Certified Directory has free search but no API;
AUVSI member directory member-only
**Paid coverage:** SEMI World Fab Forecast; AHRI Certified Directory
(free per-search, no bulk); various industry-specific tools
**SEC-proxy:** SEC 10-K Item 1 (Business) often discusses trade
association memberships and industry standards bodies. Limited
coverage; mostly narrative not registry.
**When to build:** when targeting industry-specific cohorts where
trade-assoc membership is a meaningful signal (e.g., SEMI for chip-
equipment companies). One-off per industry.

## Summary of access patterns observed across Priority 2 + 3

| Pattern | Affected sources | Workaround |
|---|---|---|
| Bot protection (Cloudflare/Incapsula) | state UCC, CA bizfile, NY UCC, FL Sunbiz, foreign registries | Playwright cluster OR paid aggregator |
| Paid-API-only (no free tier) | OpenCorporates, PatentsView ODP, Sales Navigator, SEMI | Buy the API |
| JS-rendered widgets | PCAOB HawkSearch, many state portals | Playwright |
| Hard rate-limiting | SBIR.gov | Wait; or pay aggregator |
| ToS-restricted | LinkedIn | Don't scrape |
| Multi-site custom scraping | DoD MDA/SF/AFRL, foreign registries | Per-source maintenance burden |

**The general pattern:** primary-source data for diligence is
increasingly behind paid aggregators or bot protection. The cleanest
free signal-stack is what we've already built: SEC EDGAR + USAspending
+ SAM.gov + EPA + OSHA + DOL H-1B LCA + BLS QCEW + NASA NTRS +
USPTO ODP + Clinical Trials + openFDA + FINRA + FDIC. SEC-proxy
patterns (like ucc_proxy) extend that stack into otherwise-paid
domains at ~80% signal coverage.

Real coverage beyond what we have requires either paid aggregator
subscriptions (best for specific customer needs) or browser-
automation infrastructure (best when scale + maintenance budget
both available).

## Priority 4 — Per-ticker novel sources (logged but not built)

The full 188 unique sources from
`data/_backtest/2025_05_15/proposals_backlog.json` are domain-specific
and proposed by single tickers. Mostly:
- Foreign-jurisdiction registries (Cayman, BVI, Bahamas, Singapore,
  Israel, Suzhou)
- US niche regulatory registries (FAA Part 21, NRC license database,
  EPA Section 608 reclaimer list, USDA-FSIS, FCC, FDA Drug
  Establishment)
- County-level registries (assessor parcels, building permits)
- State environmental agency portals (ADEQ, TCEQ, CalEPA, CDPHE)
- Litigation/regulatory (PACER, district-court dockets, court
  records, state inspector-general audits)
- Visual sources (Sentinel-2 / Planet Labs satellite imagery)
- Cross-checks (megacap earnings-call transcripts, GAO reports)

These mostly need targeted build when a specific cohort hits the
domain. Not basket-level priorities.

## How proposals flow into this list

1. Planner subagent emits `creative_extensions` in a plan.json
2. `plan_executor` logs to `_proposed_sources/<TK>.creative_extensions.json`
3. `aggregate_proposals.py` semantically groups across all cohort
   runs into `proposals_backlog.json`
4. Multi-ticker frequency → this backlog gets updated
5. Highest-frequency proposals get promoted to the build queue

The promotion loop is mechanical. Run more cohorts → backlog
ranking updates → next-connector-to-build becomes evident from data.
