# American Housing Corporation — Series A DD Report

*Generated 2026-05-13 | Pipeline run: ahc_20260513_093817 | Policy: DEEP*

## Materials analyzed

1. `ahc-pitch.pdf` — 28-page Series A pitch deck
2. `ahc-flux-spv.pdf` — 2-page Flux Capital co-invest summary memo
3. `AHC - Summary Financial Model.xlsx` — investment model (production, returns, capital history, per-city economics)

## Deal frame

| | |
|---|---|
| Issuer | The American Housing Corporation (AHC) |
| Business | Vertically-integrated modular housing manufacturer; "American Rowhome" product; OpCo/PropCo structure; claimed Austin TX factory |
| Round | Series A, $50M raise, $235M pre-money / $285M post-money |
| Lead | Contrary; co-investors Antler, Flux Capital |
| Flux co-invest pitch | $5M @ $235M pre = 1.75% ownership; probability-weighted 11.25x projected MOIC over 5yr |
| User's existing position | $2.5M cost basis ($500K Mar 2025 + $2M Dec 2025); currently marked at $17M |
| New ask | Add $5M to existing position |

## Executive summary

This deal **does not currently reconcile against publicly available evidence**. The framework surfaced four high-severity issues that compound:

1. **Form D dollar mismatches on both prior rounds** — Sydecar-administered SPV filings show $485K (Round 1) and $2M (Round 2) actually raised vs. deck-claimed $2M and $7M. 4x and 3.5x mismatches respectively, with no parent-entity Form D found at SEC under any name searched.
2. **No corroboration of the Austin TX factory** — zero building permits, zero OSHA records, and the only TX-tax-registered AHC entity is mailed to Dallas (zip 75201), not Austin.
3. **Internal capacity divergence in the materials** — pitch deck says Factory 1 capacity = 1,000 homes/yr; financial model says 1,750 (75% overstatement, ~43% impact on the implied valuation case).
4. **The user's $17M current mark depends on the Dec 2025 round having closed at $50M post-money.** The only Form D that matches that round's timing is a $2M Sydecar side-syndicate, not a priced round at AHC parent. The mark is not supported by SEC-filed evidence.

The Series A may still be a good investment — but the case has to come from sponsor disclosures, not from pitch claims that fail to reconcile.

---

## Findings by severity

### CRITICAL (deal-breaking unless resolved)

**C1. Form D mismatches on every prior round we could verify**

Pulled and parsed Form D primary_doc.xml directly from SEC EDGAR for the three "American Housing"-named filers:

| Sydecar SPV (CIK) | Filed | Form D `totalAmountSold` | Investors | Deck claim |
|---|---|---|---|---|
| American Housing Corp Jan 2025 a Series of CGF2021 LLC (0002059084) | 2025-03-05 | **$485,000** | 2 accredited | "Mar 2025: $2M raised, Antler led, $15M post" |
| American Housing November 2025 a Series of CGF2021 LLC (0002099529) | 2025-12-05 | **$2,000,000** | 1 accredited | "Dec 2025: $7M raised, Contrary led, $50M post" |
| American Housing Impact Fund I LLC (0001968587) | 2023-03-15 | $40,000 of $10M target, never updated; Indianapolis IN, signer "Justin Bogard" | n/a | Likely unrelated name collision |

Both 2025 SPVs are administered by **Sydecar LLC** (Carta-style fund admin), signed by Sydecar's General Manager Brett Sagan, parent vehicle "CGF2021 LLC". No AHC principals appear as related persons. No Antler, Contrary, or Flux Capital appears as related persons either (Form D doesn't require LP disclosure).

**C2. No Form D from any AHC parent entity**

Every priced Reg D 506(b)/(c) raise must file Form D within 15 days of first sale. We searched EDGAR exhaustively for "American Housing Corporation", "American Housing", "AHC" (entity names), and the founder names — **zero parent-entity Form D filings exist**.

The most charitable interpretation: AHC's priced rounds were sized *above* the SPV side-syndicate amounts (e.g., Antler/Contrary invested directly into AHC parent at the claimed terms; the Sydecar SPVs were small angel-pool add-ons), but the parent files Form D under a different legal name we haven't identified. **The burden is on AHC to identify that parent filing.** Until they do, the only SEC-recorded fundraising for any "American Housing" entity sums to **$2.485M total**, not the $9M of priced rounds the deck claims.

The less charitable interpretations: (a) priced rounds didn't close at claimed terms, or (b) AHC didn't file Form D — a Reg D compliance violation that has its own regulatory exposure.

### SEVERE (material misrepresentation; affects valuation thesis directly)

**S1. Internal capacity divergence: 1,000 vs 1,750 homes/yr (75% overstatement)**

| Source | Claim |
|---|---|
| Pitch deck p.25 | "Factory 1 will have a production capacity of **1,000 homes/yr**" |
| Financial Model Block 1 | "Factory 1: **1,750 Townhomes**" |

This is the single most important production number in the deal. Compounding effect on the valuation case:
- Model assumes 1,750 units × $450k margin = **$787.5M Factory 1 GP**
- At pitch's 1,000 units × same margin = **$450M GP** (43% reduction)
- The 15x EBITDA case ($9.45B) becomes ~$5.4B — same direction as overstatement

Either number could be the right one. **Either way, the materials internally contradict.** A sophisticated investor needs reconciliation before underwriting.

**S2. AHC parent entity registered in Dallas (zip 75201), not Austin where the factory is claimed**

TX Comptroller franchise tax record:
```
AMERICAN HOUSING CORPORATION
Taxpayer ID: 17513726384
Mailing ZIP: 75201 (Dallas TX)
```

The pitch repeatedly emphasizes Austin TX as the factory location. Three reads, in order of charitability:
1. The Dallas address is the registered agent or HQ; factory operates from a separate Austin address (common for TX corps to use Dallas/Houston registered agents)
2. The factory is operated by a different LLC/subsidiary not yet disclosed (e.g., "AHC Manufacturing TX LLC", "Alamo Industries")
3. The factory location claim is overstated

This finding alone is not diagnostic — but combined with S3 and S4, the triangulation tightens.

**S3. Zero Austin building permits under any AHC name variant**

Queried Austin's open-data permit database (Socrata) for: "American Housing Corporation", "American Housing Corp", "American Rowhome", "Rowhome". All returned 0 permits.

"AHC" returned 25 permits, all of which on inspection are unrelated entities (Lennar Homes, Victory Plumbing, Hydrotech, Landmark Electric) where "AHC" is a coincidental substring match.

The pitch claims:
- A 250,000 sqft Factory 1 in Austin (Series A is to build it)
- An MVP factory built Q3 2025 (current 36-homes/yr capacity)
- A demo home assembled Q1 2026
- A 3-unit Austin rowhome project in active pipeline

Even an MVP factory at meaningful scale (≥10,000 sqft) and an assembled residential structure should generate at least one electrical/mechanical/building permit. Possible explanations: factory in leased space under landlord's prior permits, demo home outside city limits (county only), or operating under unlisted entity name.

**S4. Zero OSHA establishment records under any AHC name variant in TX**

OSHA establishment search across name variants returned 0 records. Less probative than S3 — OSHA may not have inspected a sub-2-year-old, sub-10-employee facility — but it's a third corroborating data point pointing the same direction as S2 and S3.

**S5. SPV side-syndicates ≠ priced rounds — but the deck conflates them**

Even granting that AHC's priced rounds happened separately at the parent (as door 1 of S2 above), the deck cites round amounts of $2M and $7M without disclosing whether those are full-round amounts or include the Sydecar SPV slices. The Sydecar Form D's are real evidence of $2.485M raised across both rounds; whatever else AHC raised at parent level is currently unverifiable from our position.

### MODERATE (worth flagging; not deal-breaking individually)

**M1. EBITDA = 80% of Gross Profit assumption is implausibly high**

Public homebuilder benchmarks (Lennar, DR Horton, KB Home): ~14% EBITDA margin on revenue against ~20-23% gross margin → EBITDA is ~60-70% of GP at scale. AHC at Factory 1 stage (pre-scale) claiming 80% is on the optimistic edge of plausible. At Factory 2 (1M sqft, 17,500 units) running at 80% while a 100x-larger Lennar runs lower is suspicious of model overstatement. Worth challenging the model's SG&A and operating cost assumptions.

**M2. Aspen unit-economics line item is overstated relative to logistics**

Per-city table: Austin AHC cost $180/sqft, Aspen local hard cost $1,200/sqft → $900/sqft AHC margin → $1.62M margin per unit in Aspen. The model assumes the same $180/sqft cost for Aspen as Austin. Logistics from Austin TX factory to Aspen CO (intermodal containers per the pitch) would add $20-50/sqft, not zero. Aspen specifically also has high entitlement and labor costs that won't be eliminated by factory-prefab. Probably the most aggressive line in the per-city table.

**M3. Bozeman pipeline unit-count internal inconsistency**

Pitch deck: "Bozeman, MT — 30+ rowhomes in new-urbanist community"; Financial Model: "Bozeman 40 units, $44.7M Project Gross Profit". Minor numeric mismatch (30 vs 40, 33% delta). Caught by the framework's cross-claim consistency check after scope-aware grouping.

**M4. Team includes alumni from failed modular housing companies**

Roster includes alumni from Cover (failed 2020), Katerra (BK 2021), Samara (closed), Aro Homes (active but under-scaled). This is a pattern signal — modular housing has a graveyard despite consistent technical optimism. AHC's response should articulate what these team members learned at their prior companies and how AHC structurally avoids the same traps (over-scaling factory before product-market fit, capital-intensive expansion before unit economics prove out).

**M5. Patent / IP claims unverified**

The pitch claims a "Building System" of 5 components and an "Alamo" software platform "already in production." No patent filings asserted in the deck itself. USPTO search blocked from this environment (rate-limited / needs API key). Worth a separate manual check given that the technical moat depends on IP defensibility.

### LOW (open questions; documented for the file)

**L1. Bozeman + Albuquerque pipeline projects unverified.** City portals (OpenGov for Bozeman, ABQ ArcGIS) don't expose queryable APIs from this environment. Manual lookup viable but not done.

**L2. Direct confirmation that Contrary leads this Series A and that the Dec 2025 round was Contrary-led at $50M post.** Both funds are real and SEC-registered (Contrary: 22 Contrary Capital / Breakout Fund entities found at EDGAR; Antler: 11 Antler funds found). But which specific fund is investing here, and at what terms, requires direct outreach.

**L3. The 11.25x probability-weighted MOIC** depends on Bear/Base/Bull/Moonshot scenarios with FY31 revenue of $244M / $1.39B / $1.77B / $4.20B. None of these are stress-tested against capital-stack assumptions (PropCo's ability to fund construction at the implied throughput).

---

## What we verified

For completeness, the framework verified the following without flagging issues:

- **AHC entity exists in TX corporate registry** (taxpayer ID 17513726384, Dallas mailing) — though see S2 about the Austin/Dallas mismatch
- **Contrary and Antler are real SEC-filed VC fund families** (22 Contrary entities, 11 Antler entities) — though specific lead-fund attribution is unverified (L2)
- **At least 3 "American Housing"-named SEC filers exist** — though as analyzed in C1/C2, these are SPV side-syndicates, not the parent
- **Round 3 ($50M) Form D not yet filed** — could be expected if still actively fundraising

---

## What we couldn't verify (and why)

| Claim | Reason | Path to verify |
|---|---|---|
| AHC parent entity name | Multiple "American Housing" entities exist at SEC; none is clearly the operating parent | Direct disclosure from AHC |
| Austin factory existence | Zero Tier-1 records under any AHC variant | Direct disclosure of operating LLC name; on-site visit |
| Bozeman 30-40 unit project | OpenGov portal not API-accessible | Manual portal lookup; AHC can provide permit numbers |
| Albuquerque 50+ rowhomes | ABQ ArcGIS endpoint flaky | Same |
| Contrary leadership of this round | Lead-investor confirmation requires direct fund outreach | Reference call with Contrary partner |
| Founder patent claims | USPTO connector blocked | Manual patentsview.org search with API key |

---

## Recommendation

**Do not commit additional capital at $235M pre-money until AHC provides satisfactory answers to three pointed questions:**

1. **What's the legal name of the AHC parent entity that filed Form D for the Mar 2025 and Dec 2025 priced rounds?** If they cannot produce a parent Form D distinct from the Sydecar SPV's, that's:
   - A Reg D compliance violation (exposure to the company), AND
   - Means the only SEC-recorded fundraising history for any "American Housing" entity is **$2.485M** total, not the $9M the deck claims

2. **Reconcile Factory 1 capacity: 1,000 (pitch p.25) vs 1,750 (financial model).** The 43% valuation gap is too large to be a typo. Resolve with an updated model showing which capacity is the underwritable case, plus the engineering basis for that throughput.

3. **Disclose the operating entity name for the Austin TX factory.** The TX-registered AHC parent sits in Dallas; zero Austin permits or OSHA records exist under any AHC variant. Either the factory operates under a separate (undisclosed) entity, or the Austin claim needs substantial recalibration. Either way the investor needs to know which entity owns the IP, which entity owns the factory, and how the OpCo/PropCo capital stack maps to those entities.

**On the user's existing $17M current mark**: this valuation assumes the Dec 2025 round closed at $50M post-money. The only Dec 2025 Form D we can find is a $2M Sydecar SPV with 1 investor. **The mark is not supported by SEC-filed evidence.** Request from AHC: the Dec 2025 SAFE/Series Seed/preferred-stock issuance docs, the cap table that produces $50M post-money, and the cap table that produces the $17M mark on $2.5M cost basis.

**On the new $5M co-invest**: Without satisfactory answers above, this is currently a deal where the available public evidence does not support the pitched valuation thesis. The Series A could still be a good investment — strong product concept, plausible team backgrounds, real macro tailwind for missing-middle housing — but the case has to come from disclosure-driven DD, not from pitch claims that fail to reconcile against the public record.

**Estimated probability the deal is salvageable** with full disclosure: moderate. The structural concerns are about transparency and the gap between pitched and SEC-recorded numbers, not about the underlying business model being unworkable. Modular housing has a real opportunity; AHC's specific positioning (containerized components, Sydecar-style syndication of side rounds, OpCo/PropCo split) is internally coherent. But a sophisticated investor has to insist on the documents before underwriting.

---

## Appendix: methodology

**Framework**: Signal OS buyside DD pipeline, DEEP policy (max $5,000 / 1-week wall budget; FOIA-enabled; paid sources allowed; report-severity threshold = MINOR).

**Sources queried**:
- **Tier 1 (gov primary)**: SEC EDGAR (full-text + company-name browse + Form D primary_doc.xml parsing); TX Comptroller franchise tax; Austin Socrata permits; OSHA Establishment Search
- **Tier 1, blocked**: USPTO PatentsView (API key needed), USPTO Google Patents fallback (rate-limited from this IP)
- **Tier 5 (snippet)**: DuckDuckGo Lite for Crunchbase / Preqin pivot URLs
- **Internal**: Cross-claim consistency checker (groups by subject + predicate + scope; flags numeric divergence ≥ 5%)

**Total budget consumed**: $0.00 (all sources queried were free).

**Total Findings produced**: 13 across 16 typed claims dispatched.

**Key sources cited**:
- https://www.sec.gov/Archives/edgar/data/2059084/000205908425000001/primary_doc.xml (CIK 0002059084 Form D)
- https://www.sec.gov/Archives/edgar/data/2099529/000209952925000001/primary_doc.xml (CIK 0002099529 Form D)
- https://comptroller.texas.gov/data-search/franchise-tax?name=American%20Housing%20Corp (TX entity verification)
- https://data.austintexas.gov/resource/3syk-w9eu.json (Austin permits Socrata)
- https://www.osha.gov/pls/imis/establishment.search (OSHA TX)
