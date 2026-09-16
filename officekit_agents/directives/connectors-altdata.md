# Alt-Data Connector Atlas — physical-truth verification sources

Distilled doctrine for the desk's alt-data/verification connector suite: primary sources that check a marketed claim against an instrument measurement, a government record, or an exhaust stream rather than another document. Organizing principle: target the number management can misstate, not the one the Street already nowcasts; satellite beats phone data only for hard-to-fake physical quantities with no phone substitute.

## carbon-mapper-methane

**Verifies that an asset is physically operating/emitting — or refutes a marketed "clean / within-limits" environmental claim — via instrument-measured methane/CO2 plumes.**
- Source: public, no-auth `GET https://api.carbonmapper.org/api/v1/catalog/plumes/annotated?bbox=minLon&bbox=minLat&bbox=maxLon&bbox=maxLat&plume_gas=CH4&emission_min=<kg/hr>&sort=emissions_desc&status=published`. Instruments: Planet Tanager-1 (`tan`), NASA EMIT (`emi`), GAO/AVIRIS aircraft.
- Quirk: the annotated list nulls latitude/longitude/datetime, but `plume_id` encodes instrument+timestamp (`tan20250815t183402…`) — parse it.
- Registered as a Tier-1 `environmental_status` source so it co-dispatches with EPA Envirofacts; corroboration raises detector confidence automatically (validated: a weak web-only finding rose 0.30 → 1.00 with satellite corroboration; a "no methane" claim vs a measured plume → REFUTED/SEVERE).
- Lags/limits: free coverage is opportunistic (overpass + plume present), so **absence ≠ no emissions**. Only emitting-asset classes (O&G, landfill, petrochem) show up; parcel-level point-in-time needs paid tasked acquisition. Free tier is non-commercial-use only — productizing requires a Planet/Carbon Mapper license.
- Reach for it: any environmental or operations claim on a methane-emitting asset class; strongest as a corroborator/refuter, not a standalone screen.
- Reference implementation: verticals/buyside_dd/connectors/carbon_mapper.py

## sentinel2-buildout

**Verifies "this parcel is physically being built / is active" — the ground truth behind buildout-on-schedule and facility-under-construction claims — at $0.**
- Source: ESA Sentinel-2 L2A (10-20 m), no auth, via the public Element84 Earth Search STAC (`POST https://earth-search.aws.element84.com/v1/search`, collection `sentinel-2-l2a`) + the open `sentinel-cogs` AWS bucket; read Red/NIR/SWIR16 COG windows with rasterio (hit STAC with plain requests).
- Signal, baseline vs recent date over the parcel: NDBI=(SWIR16−NIR)/(SWIR16+NIR) up ≥0.06 AND NDVI=(NIR−Red)/(NIR+Red) down ≥0.05 → buildout. Registered Tier-2 `construction_activity`.
- Gotchas: 10 m cannot resolve single buildings; requires a true pre-construction baseline (already-built sites read "stable"); desert→concrete is ambiguous on NDBI alone (use the NDVI drop); NDBI false-negatives on modern reflective roofs — NDVI collapse is the reliable channel there; STAC requires RFC3339 datetimes (bit-rot fixed once already).
- Paid escalation: PlanetScope ~3 m daily / SkySat ~50 cm tasked, same output contract — roughly $2-5k per diligence event (SkySat tasking, ~25 km² min AOI) or ~$10-50k/yr for continuous AOI monitoring (dated — re-verify before relying). Strategy: free 10 m + free methane for routine screening; pay only when a deal needs individual structures resolved.
- Reference implementation: verticals/buyside_dd/connectors/sentinel2_buildout.py (paid stub: connectors/planet_imagery.py)

## crop-yield-ndvi

**Verifies ag/commodity/fertilizer/crop-insurance harvest claims against measured crop condition — "record yields" vs NDVI down YoY is a divergence flag.**
- Method: peak-season mean NDVI over a cropland AOI, current year vs prior years, on the free Sentinel-2 path (shared STAC+COG helper `connectors/_s2util.py`). Registered Tier-2 `crop_condition` (GEOGRAPHIC_AREA).
- Live-validated on Iowa/Illinois corn multi-year series with coherent YoY readings (dated — re-verify before relying).
- This is the genuinely viable free-tier satellite detector: no phone-data substitute exists for yield, and it works on 10 m.
- Reach for it: any thesis where a marketed harvest/yield/condition number is load-bearing and management has an incentive to shade it.
- Reference implementation: verticals/buyside_dd/connectors/crop_yield_ndvi.py (runner: validate_altdata.py)

## oil-storage-tank-shadow

**Would verify crude storage levels via floating-roof tank shadows — honest finding: it does NOT work on free 10 m imagery; this is the genuine paid-Planet case.**
- Mechanics: floating roofs sink as tanks drain → larger interior shadow = inverse fill proxy. Pipeline includes the mandatory sun-elevation normalization (×tan(elev)); without it the raw signal just reads season.
- Why free fails: at 10 m a tank is 5-10 px, so per-tank roof shadow is sub-pixel; the normalized residual sits within sensor noise. A usable barrel count needs PlanetScope/SkySat ~3 m (paid). Registered Tier-3 LOW.
- Value: the clean build/buy example of where the free tier fails and paid imagery is actually required. Productization also wants EIA weekly-stocks cross-validation.
- Reach for it: only with paid high-res imagery in hand; otherwise use EIA/official series.
- Reference implementation: verticals/buyside_dd/connectors/oil_storage.py

## forest-integrity-panel

**Verifies the QUANTITY half of a timberland/biological-asset balance-sheet mark: satellite clear-cut rate vs the stated sustainable-harvest rate.**
- Method: Sentinel-2 clear-cut proxy (baseline NDVI≥0.6 pixels dropping ≥0.25 YoY) over estate-region AOIs, compared against (a) a protected national park control — harvest is illegal there, so its reading (~0.95%/yr in the validation run) is the method's noise floor — and (b) a non-company peer region. Atlas: `forest_harvest_rate` Tier-2.
- Data-quality guards learned the hard way (a thin-haze scene produced a fake 84% clear-cut): bad-scene span-scaling, cloud-differential exclusion → UNVERIFIABLE not ELEVATED, partial-tile rejection, coverage-band widening (a fell can hide under cloud).
- Cadence: quarterly re-run; it grades the mark's plausibility, never times the stock. Price half of the mark is transaction-tested separately.
- Generalizes to any timberland/biological-asset holder (Rayonier/PotlatchDeltic/Weyerhaeuser class). First pass on a Nordic forest-products name read SUSTAINABLE vs the national harvest norm (dated — re-verify before relying).
- Reference implementation: verticals/buyside_dd/connectors/forest_integrity.py (+ run_forest_panel.py, forest_aoi.json)

## usaspending-federal-contracts

**Verifies any "X% government revenue" claim against the primary auditable federal-procurement record.**
- Source: `POST api.usaspending.gov/api/v2/search/spending_by_award/` with `recipient_search_text` + contract `award_type_codes`; public, no auth. Returns prime-contract totals, defense-vs-civil split by awarding agency, per-agency breakdown, top awards. Tier-1 `government_contracts`, with a recall-floor rule so a gov-revenue claim can never pass unverified.
- Lesson 1 — contracts hide in SUBSIDIARIES: search the corporate family, not the parent's full legal name. Strip the legal-form suffix to a core family name and match recipients by distinctive-token subset. Case law: Planet Labs — parent-name search found $19.6M; family search found $142.8M across three entities including the `Planet Labs Federal, Inc.` defense/IC vehicle. `<Co> Federal Inc` / `<Co> Government Solutions` is the standard pattern.
- Lesson 2 — USASpending materially UNDERSTATES gov revenue for IC/foreign-heavy issuers: prime-only (subcontracts invisible), multi-year obligation totals (not annual), classified IC and foreign-sovereign contracts absent. A low total ≠ small gov revenue; the gap itself is thesis texture (foreign-sovereign + classified = unauditable, adds geopolitical/FX risk).
- Reach for it: any government-revenue, defense-mix, or agency-concentration claim.
- Reference implementation: verticals/buyside_dd/connectors/usaspending.py

## litigation-screen

**Verifies the litigation background of any named deal principal/operator/sponsor/GP — a default screen, not a "recommended next step."**
- Source: CourtListener / RECAP v4 search API (free scriptable PACER proxy; unauthenticated, rate-limited — retry with backoff) for federal dockets + opinions on names and aliases.
- Classification: MATERIAL (nature-of-suit securities-850 / fraud-370 / RICO-470 / stockholder-160 / franchise-196 / contract-190, or subject-as-debtor bankruptcy) fires; BASELINE (employment/ADA/wage-hour 710/442/445/446 — routine for any large operator) does not. Distinguishes subject-as-defendant/debtor (bad) from plaintiff/creditor (neutral); flags common-name collisions as `disambiguation_needed` → detector returns REVIEW, not CLEAR — human adjudicates.
- Auto-dispatch: a recall-floor rule fires the screen whenever a claim casts a person/entity in a founder/operator/sponsor/GP/CEO role. Tier-1 `litigation_history` for both PERSON and ENTITY.
- Coverage caveat — state it every time: FEDERAL/RECAP ONLY. State courts have no unified free API; full PACER party-search and UCC liens are paid/manual escalation (state-court gated portals → real-browser automation path, see: browser-automation-gated-portals). Clean here ≠ clean everywhere.
- Reference implementation: verticals/buyside_dd/connectors/litigation_screen.py (+ detectors/principal_litigation_flag.py)

## form-d-gp-reconciliation

**Verifies marketed private-fund sizes against SEC EDGAR Form D filings per vehicle — the fund-size lie-detector for any PE/RE/credit GP pitch.**
- Method: pull each fund's Form D (CIK for the main vehicle AND every feeder/SMA): `Total Amount Sold`, `Date of First Sale` (watch "Yet to Occur"), investor count. Marketed totals are often a family/SMA roll-up no single Form D substantiates, with feeders double-counted.
- Case law (real-estate GP, Jun-2026 diligence): "first close at over $450M" → Form D showed $0 sold / first sale yet to occur; "$267M" fund → largest single Form D $133M; "$440M raised" → main-fund Form D $378.7M with an overlapping feeder double-count.
- Lag caveat: Form D is due 15 days after first sale, so a genuine close can post-date a $0 filing — reconcile, don't assert fraud.
- Companion checks that ride along: the "endnote-quarantined disclaimer" mechanism (pitches go honest in 6-pt endnotes, promotional in headlines — grade takeaway-vs-data divergence; demand realized DPI + net IRR with realized/unrealized split and gross-to-net); and the deregistered/absent-RIA check (IAPD/Form ADV by CRD — no manager-specific ADV means AUM/custody/conflicts are UNVERIFIABLE, which ≠ clean; ask which entity is adviser of record).
- Reference implementation: verticals/buyside_dd/outputs/pearlmark_20260617/ (worked example)

## customer-id-whale-detector

**Identifies a company's UNDISCLOSED top customer ("whale") via customs bill-of-lading alias triangulation + Bayesian evidence aggregation — the swing factor for any single-customer-dependent thesis.**
- Pipeline: (1) resolve shipping entities — companies ship on customs BOLs under the OPERATING/legal SUBSIDIARY, not the brand (case law: Stevanato ships as "Nuova Ompi SRL"; querying "Stevanato" returns nothing) — maintained alias registry, extended per name learned; (2) free US BOL aggregators for shipper→consignee (importinfo/importgenius public tiers worked; importyeti Cloudflare-403s (dated — re-verify before relying)); (3) Bayesian aggregation over six evidence channels (customs_bol, co_location, disclosed_agreements, product_format, revenue_geography, demand_trend_correlation) as likelihood-ratio vectors, with leave-one-out robustness.
- Two structural blind spots, both encoded: BOL aggregators are the CBP AMS vessel-manifest feed — OCEAN-ONLY, and foreign fill/foreign-market shipments bypass US customs entirely. So "customer absent from BOL" is weakly informative, never zero — down-weight (LR ~0.6), don't zero.
- Air-freight closure: `census_trade_flow(hs_code, country, mode)` — US Census international-trade API (free key, ~/.census_key) gives monthly imports by HS6 × country × transport mode, ~5-week lag, with a recent-vs-baseline surge flag. Validated: Korea→US botulinum imports are 100% air, empirically proving the ocean-BOL blindness.
- Regime-conditional (decisive): the edge pays only when the market DISCOUNTS an undisclosed concentration (fears the hidden whale is the weak one). It is dead when the market rewards concentration (assumes AI-strong), when the whale is consensus-named, or when the order book is lumpy capital equipment (a named customer doesn't de-risk cadence). Screen price/disclosure/stickiness legs FIRST; spend the scarce BOL query last.
- Validation: Stevanato posterior Lilly 93%/Novo 4%, robust ≥67% dropping the customs channel — converted an unresolvable customer mystery into a valuation question.
- Reference implementation: verticals/buyside_dd/connectors/customer_id.py

## origin-mix-tariff-exposure

**Triangulates a company's UNDISCLOSED sourcing/origin geography into a SIZED tariff EBIT-at-risk number — companies disclose the risk but hide the magnitude.**
- Method: (1) decompose reported GMV/revenue into buckets with different origin exposure (3P marketplace vs 1P own-inventory vs acquired/branded), each with low/base/high origin priors; (2) cross-check with customs BOL (reuses customer-id's shipping-entity resolution) + Census trade flow by HS × country; (3) apply tariff INCIDENCE to compute EBIT-at-risk under pass-through scenarios.
- The insight most tariff bears miss: **origin share is NOT the margin denominator.** On 3P/marketplace volume the tariff lands on the third-party importer-of-record — off the platform's P&L. Only own-inventory origin GMV hits COGS, so a high China-share name can have small margin exposure (the bear may still be right on demand/volume).
- BOL cross-check undercounts marketplaces: 3P goods land under the manufacturer's name, not the platform's — treat as directional.
- Validated on a marketplace furniture name: biggest China bucket was off-P&L; worst-case EBIT hit ~42% of pretax at 60% pass-through, ~$0 at demonstrated full pass-through (dated — re-verify before relying).
- Reference implementation: verticals/buyside_dd/connectors/origin_mix.py

## hiring-velocity-plant-ramp

**Verifies a new-plant/capacity ramp toward utilization — the free LEADING proxy for the margin-inflection print — via job-posting count, production-role mix, and posting velocity at the site.**
- Mechanism: a plant ramping to 24/7 hires in a WAVE (operators/technicians/QC/shift crews) then TAPERS at full staff. Accelerating operator postings = mid-ramp; postings drying up = nearing full utilization = inflection approaching, ahead of the margin print.
- Source: LinkedIn guest jobs endpoint (`/jobs-guest/jobs/api/seeMoreJobPostings/search`, no auth, posting dates in the payload). Caveats: LinkedIn skews white-collar — the production-operator wave is often Indeed-only; add a free Adzuna key (~/.adzuna_key) to capture it. A single ~300-person plant is small/lumpy — read the trend across snapshots, never one pull.
- The decisive negative that produced it (encode this): the satellite furnace-thermal route was CONTROL-REFUTED — a mature always-on furnace site read LOWER daytime Landsat surface-temp excess than both a ramping site and a no-furnace big-box control; insulated roofs + solar heterogeneity swamp any furnace signal. Free foot-traffic also failed (no Popular Times for low-consumer-traffic manufacturers). Hierarchy: hiring (free, works) > paid mobility (cost + small-N) >> free satellite thermal (refuted) / free phone (absent).
- Auto-fires (recall-floor) on capacity-ramp claims: "coming online", "operating leverage as the plant fills", "sold out into 20XX".
- Reference implementation: verticals/buyside_dd/connectors/hiring_velocity.py

## restaurant-ratings-operating-locations

**Verifies that each marketed brick-and-mortar operating unit (restaurant/retail/clinic/franchise) exists AND is operational, with its public rating/review count.**
- Providers: Google Places API (New) `places:searchText` — authoritative `businessStatus` (OPERATIONAL / CLOSED_PERMANENTLY / CLOSED_TEMPORARILY / NOT_FOUND) + rating + review count; key via env or ~/.google_places_key. No-key fallback: OSM Nominatim geocode — confirms address existence only (ratings inherently need a key on every provider).
- Auto-fires (recall-floor) on "N operating units at these addresses" rosters; deliberately does NOT fire on "units APPROVED" entitlement claims (separate rule) or person bios.
- Case law: a 24-unit franchise roster verified 24/24 operating — and the SAME pass caught two sister units excluded from the deal perimeter (scope/non-compete question) plus related-party ownership of the "owned" parcels via county assessor records with price anchors. Physical verification finds perimeter games, not just closures.
- Reach for it: any deal marketing a unit roster; pair with county assessor lookups on owned real estate.
- Reference implementation: verticals/buyside_dd/connectors/restaurant_ratings.py

## app-review-velocity

**Verifies consumer-app traction/deterioration for any issuer whose product is a consumer app — dated review velocity + exact cohort deltas, all keyless.**
- Sources: iTunes Search (entity resolution; UNRESOLVED on ambiguity), iTunes Lookup (lifetime count/rating → EXACT cohort delta from snapshots ≥3 days apart), iTunes RSS (~500 dated reviews → true trailing 7d/30d velocity on the first run; floors flagged when pagination exhausts), Play Store ld+json aggregate (undated; snapshot fodder). US storefront only — RSS is per-country. Play recent-review stream would need batchexecute (not built).
- Calibration 1 — POPULATION MISMATCH: RSS-visible cohorts are WRITTEN reviews, structurally angrier than the prompted-in-app population dominating lifetime means (every name reads ~1.8-3.9★ recent vs ~4.5★ lifetime). Never read visible-vs-lifetime as deterioration. Valid reads: velocity trend, cohort-vs-own-history, name-vs-name in-channel, exact snapshot delta.
- Calibration 2 — velocity measures PROMPTING as much as sentiment: spikes near a version release are artifact candidates; a velocity COLLAPSE has no prompt excuse and is the cleaner signal.
- Reach for it: consumer-app, DAU/MAU-marketed, or marketplace-KPI issuers; run as a standing daily snapshot on tracked names.
- Reference implementation: verticals/buyside_dd/connectors/app_review_velocity.py

## beauty-virality-radar

**Detects consumer products going viral and maps each to the investable PUBLIC beneficiary (brand-owner | ODM | distributor) — the trade is the LATENCY: virality leads the earnings print ~1-2 quarters, and most viral brands are private.**
- Architecture: durable brand→vehicle registries (beauty + ~40 viral-prone consumer brands across food/bev/apparel/tech/home; space-insensitive matching) + `resolve_odm_via_fda()` — the openFDA NDC/SPL route names the OTC/SPF contract manufacturer directly (OTC/SPF subset only; non-SPF ODM links stay UNVERIFIED until customs-BOL/SPL confirms).
- Detection paths, in order of quality: (1) authenticated TikTok Creative Center browser poll — industry-filtered trending-hashtag tables (rank/tag/posts/views) across five consumer categories in one session; auth = a Playwright storage_state harvested from a logged-in Chrome TikTok-for-Business session (the `_ads`-suffixed cookies are the business session; Chrome cookie store decrypts via the OS keychain path — reusable technique, see: browser-automation-gated-portals); cookie expires in ~weeks → poll returns NO_AUTH → re-harvest; (2) periodic WebSearch scan for the qualitative influencer/ODM layer; (3) paid trend APIs. Direct APIs are gated from plain egress: TikTok CC unauthed, Reddit/Sephora/Google-Trends 403, Amazon Movers JS-lazy (dated — re-verify before relying).
- Reads: ACCEL virality + clean vehicle + unpriced latency = long candidate; FADING virality on a public brand = short-side tell 1-2 quarters ahead; viral brand with NO public vehicle = IPO/M&A watch signal in itself.
- Discipline: confirmed-referents-only in any model (a spurious social-lift once entered via a double-count + an unverified brand link); the ODM-mapping hypothesis is under a pre-registered backtest with locked success criteria — treat ODM social-lift as unproven until it clears.
- Judgment: the trade plays over quarters, so daily-vs-weekly detection buys only days.
- Reference implementation: verticals/buyside_dd/connectors/beauty_virality.py, connectors/beauty_velocity_poll.py, outputs/medspa/run_virality_scan.py

## edinet-japan

**Provides audited Japanese fundamentals for the global value screen — full-universe scoring without an API key.**
- Transport trick: EDINET API v2 returns 401 without a subscription key, but the PUBLIC viewer serves identical CSV-facts ZIPs — Playwright drives the document-detail search date-by-date into the same cache (GeneXus postback gotchas encoded: hidden inputs behind styled labels, filter-grid re-render race, downloads in `href` not `onclick`). First crawl: 1,525 filings, 0 unparseable, 968 scored. A real API key can replace the crawl (drop in global/data/edinet_key.txt).
- Japan-specific extraction case law: consolidation outranks tag preference — an IFRS filer's parent-only JP-GAAP statements can silently poison a row (a ¥1.55B vs true ¥450B cash miss); prefer consolidated context regardless of taxonomy. Post-FYE stock splits fake yields (a 1:4 split after fiscal year-end produced a 164% fake FCF yield) — use the as-of-filing-date share count. JP-GAAP puts one-time gains below operating income, so the one-time-EBIT guard is structurally satisfied for JPPFS filers; IFRS filers need a flag.
- PFIC is structural and the test basis is decisive: for public names §1297 runs on FMV (denominator ≈ mktcap + liabilities), not book assets — cheapness shrinks the denominator, so the discount and the PFIC poison are the same phenomenon. FMV recompute roughly doubled the flagged share of the cheap top vs book basis (~52% vs ~25%) (dated — re-verify before relying). Taxable books gate PFIC names out; revive only via tax-advantaged wrapper, MTM override, or passive<50%.
- Prices: cached bulk yfinance `.T`; per-name fast_info rate-limits at ~40 names/4min — don't.
- Reference implementation: verticals/deep_value/global/ (edinet_fundamentals.py, edinet_browser_crawl.py, screen_japan.py)

## price-history-nasdaq

**Provides free keyless daily OHLC price history when the usual free sources are walled.**
- Working path: Nasdaq historical API — `https://api.nasdaq.com/api/quote/<TICKER>/historical?assetclass=stocks&fromdate=YYYY-MM-DD&todate=YYYY-MM-DD&limit=9999` — REQUIRES full browser headers including `Origin: https://www.nasdaq.com` + `Referer: https://www.nasdaq.com/`. Response rows in `data.tradesTable.rows` as `{date: "MM/DD/YYYY", close: "$X.XX"}`.
- Dead/degraded alternatives (dated — re-verify before relying): stooq bulk history is behind a captcha/API-key wall (the light latest-quote endpoint `https://stooq.com/q/l/?s=<t>.us&f=sd2t2ohlcv&e=csv` still works); Yahoo chart v8 returns 429 even with a browser UA.
- General scraping doctrine: on a 403, complete the browser fingerprint (Sec-Ch-Ua / Sec-Fetch-* / Referer) before assuming a hard gate.
- Reach for it: any public-co price-series need outside the broker rail.
- Reference implementation: verticals/public_co/pledge_margin_call.py::fetch_price_series

## ibkr-conid-local-gateway

**Resolves option contract IDs read-only through the local IB Gateway when the hosted chain endpoint is down — conIDs are not derivable, and hand-constructing one is the error mode.**
- Method: `ib_insync` → `IB().connect("::1", 4001, clientId=N, readonly=True)` → `qualifyContracts(Option(sym, "YYYYMMDD", strike, "P"/"C", "SMART", currency="USD", multiplier="100"))` → pass the returned conId to the staging connector. A lookup is not an order; the transmit discipline is untouched.
- Gotcha 1: the gateway listens on IPv6 ONLY — an IPv4 127.0.0.1 probe reports the port closed; `lsof -nP -iTCP -sTCP:LISTEN | grep java` finds it.
- Gotcha 2 (the proof step): always resolve a control contract you already hold in the same call — the new ID is proven real by the held position's conId matching, not guessed.
- Context: the hosted strike-level chain call is the least reliable in the rail (15+ failures over ~14h in one episode) while snapshots/positions/orders stayed healthy; strikes on one chain run non-sequential IDs.

## spcx-ipo-lockup-calendar

**Verifies IPO lockup-supply waterfalls from the primary prospectus — anticipation selling vs actual supply release are different events; the 424B4 is the only authority.**
- Method: pull the 424B4 by accession number, extract every tranche: event-driven releases (N trading days after an earnings release), date-certain drips, price-conditioned tranches (dead below the trigger), extended-holder and insider dates, waiver authority (the sole bank that can accelerate everything), and float-relative sizing (a release can be multiples of float).
- Case law (SPCX, corrected from the primary 2026-07-30): a −49% drawdown happened on ANTICIPATION with zero supply released — the first release was event-driven (Q2-earnings+2 trading days, ~143% of float), then date-certain drips each ~50% of float, a Q3+2d tranche at 203% of float, insider shares a year out; float only ~4.85% of shares outstanding. Every listed option expiry contained ≥2 tranches — no clean tenor existed for structure trades (dated — re-verify before relying).
- Also watch for negative-convexity issuance riders (VWAP-based deal consideration: falling price → more shares).
- Reach for it: any recent IPO where "the lockup expired/is expiring" is doing thesis work — build the tranche table from the filing before trusting any calendar service.
- Reference implementation: desk edge_classifications/SPCX.json (worked example)

## section-232-pharma-tariff

**Verifies pharma tariff exposure under Section 232 (Proclamation 11020, Apr-2 2026) — the relief tiers INVERT for a cash-pay small-cap already at a country cap.**
- The tier structure: default 100% / country-cap (Korea, EU, Japan) 15% / onshoring-agreement 20% / 0% only via an HHS most-favored-nation government drug-pricing deal. Covers patented Orange/Purple-Book articles + APIs; generics/biosimilars exempt.
- The trap: the big-pharma playbook ("announce US capex, get relief") does NOT generalize. For a company that is (a) already at the 15% country cap, (b) cash-pay (no government-payer pricing to concede → the 0% MFN door is structurally shut), and (c) a small-cap single-sourcing a biologic it doesn't manufacture (multi-year FDA site-change; the contract manufacturer builds at home), onshoring RAISES the rate 15%→20% and there is no door below the cap. "Onshoring drops the tariff" is FALSE for that profile — the tariff is a durable drag, and management's "mitigate or eliminate" framing should be discounted to "defer."
- Only genuine full off-ramp: a product-classification carveout, separate from onshoring and usually unverifiable. Two-sided risk: country caps can also be raised.
- Cross-check the stockpile-deferral story with the customs/Census air-import channel (see: customer-id-whale-detector) — stockpiling defers, never eliminates.
- Case law: EOLS/Jeuveau, 10-Q-confirmed 15%, quantified ~1-3 GM-pt durable drag (dated — re-verify before relying).

## diligence-master-shared-store-rules

**Not a source — the two store-integrity rules every connector's shared JSON store must obey, plus the consolidated per-security diligence-master pattern.**
- Rule 1 — UNSCREENED ≠ CLEAR: a name with no data from a screen must be marked UNSCREENED and excluded from the investable set, never defaulted to CLEAR (caught: 53 un-underwritten names showing falsely clean because no flags fired on absent data).
- Rule 2 — always MERGE shared stores, never overwrite: `json.dump(new_records, open(store,"w"))` on a partial run silently wipes every other record (a 2-name run once wiped 36 records and zeroed a screen). Load-merge-by-key in every shared-JSON writer; audit any new writer for this pattern.
- Pattern: one record per security joining EVERY screen with a banded verdict, rebuilt idempotently by the daily cron — so a verdict always reflects all screens or is explicitly UNSCREENED.
- Reference implementation: verticals/muni_credit/build_diligence_master.py, portfolio_model.py
