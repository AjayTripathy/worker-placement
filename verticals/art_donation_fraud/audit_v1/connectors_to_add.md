# Connectors to add — art_donation_fraud v2 roadmap

Per the connector-discipline rule (`feedback_connector_discipline.md`): every audit ships a first-class table of connectors to add, triaged by who can build them. Don't bury this in `coverage_assessment.md`.

## What's already wired (v1)

| Connector | Source | Records produced | Status |
|---|---|---|---|
| `met_bulk_csv.py` | Met openaccess GitHub CSV (~318MB) | `museum_acquisition` for 480K Met objects, filtered to 7.4K gifts since 2010 in high-value cls | shipped |
| `moma_bulk_csv.py` | MoMA collection GitHub CSV (~73MB) | `museum_acquisition` for 140K MoMA objects, filtered to 8.6K gifts since 2010 | shipped |
| `met_collection.py` | Met REST API (per-object) | live single-object lookup (Incapsula-protected; needs real UA) | shipped, unused at cohort scale |

## What's missing (v2 roadmap, ranked)

### Agent-doable (build in next session; no external dependency)

| Rank | Connector | What it unlocks | Effort estimate |
|---:|---|---|---|
| 1 | **Other top US museum collection scrapers** — Whitney, Guggenheim, Art Institute Chicago, LACMA, Getty, Boston MFA, Philadelphia MFA, SFMOMA | Cross-museum donor pattern; right now we miss the donors who give to Whitney+Met+MoMA portfolio-wide | 1-2 hr / museum × 8 museums |
| 2 | **IRS Form 990 Schedule M bulk** — IRS publishes 990 XML in bulk at `s3://irs-form-990/`. Schedule M reports aggregate non-cash contributions by category per filer-year | Sanity-check: does Met's reported non-cash gift value match the sum of inferred values for works we observe? | 2-3 hr |
| 3 | **IRS Art Advisory Panel annual reports** (published PDFs) | Calibrates base rate of fraud — what % of appraisals get reduced, by how much, in what categories | 1 hr (PDF scrape) |
| 4 | **SEC EDGAR Form 4 / Form 144 cross-join** for public-figure donors | Identifies donors whose clustered gift year coincides with a known capital-gains event (stock sale, IPO, vesting) — strongest fraud-risk archetype | 2-4 hr (we already have edgar.py in public_co/) |
| 5 | **Phillips lot archive** (already partial — page renders 6.8MB HTML, parser not written) | Per-work auction comparable for contemporary art (Phillips is the smallest of the big 3, but most accessible) | 3 hr |
| 6 | **Heritage Auctions** (TLS 1.0 issue fixable with `ssl_context` workaround) | Per-work comparable for mid-market art | 2 hr |
| 7 | **Wikidata SPARQL** with chunked queries (avoid timeout) | Catalog-raisonné provenance + occasional auction price for famous works | 3 hr |

### Agent-adjacent (one-time user action: free API key signup)

| Rank | Connector | Key needed | Build effort once key obtained |
|---:|---|---|---|
| 1 | **Artsy public API** (`xapp_token`, free) | Sign up at `artsy.net/developers`, ~5 min | 2-3 hr — gives auction results + market data |
| 2 | **The Met has an open-data SPARQL endpoint** under `data.metmuseum.org` — may be more performant than per-object REST | None | 1 hr |

### Human-doable (FOIL, paid vendor, identity verification)

| Rank | Connector | Access path | What it unlocks |
|---:|---|---|---|
| 1 | **Artnet Price Database** ($480/yr individual, $2.5K/yr commercial) | Subscription | **The auction comparable.** Comprehensive, structured, the production answer for per-work FMV verification. Closes the binding constraint. |
| 2 | **Artprice.com** (~$300/yr) | Subscription | Alternative to Artnet; broader European coverage |
| 3 | **MutualArt** ($30/mo) | Subscription | Lower-tier but cheap-to-trial |
| 4 | **Museum deaccession records** | Per-museum FOIL or state non-profit disclosure law; some museums publish in annual reports | Wires the `EARLY_DEACCESSION_RECAPTURE` (§170(e)(7)) rule — the lawsuit-grade signal |
| 5 | **Form 8283 itself** (the actual R) | **IRS internal only.** Whistleblower program (IRC §7623) is the only way to attach a §6103 disclosure to a specific case. | Confirms the actual claimed FMV per case — closes the R-side gap |

## Order of attack for v2

1. **Cheapest agent-doable first** to maximize signal on the existing report:
   - Other US museum scrapers (especially Whitney + Guggenheim — same modernist donor circle as MoMA, would cross-validate the existing flagged-donor list)
   - 990 Schedule M (aggregate sanity check)
2. **Agent-adjacent next**: Artsy `xapp_token` signup — closes 80% of the auction-comp gap for contemporary art
3. **Human-doable in parallel**: hand user the artifact for Artnet trial subscription (one-month is enough to validate before committing to annual)
