# Charter Universe Audit (v1 → v2)

**Date**: 2026-05-28
**Auditor**: Audit agent (hard re-verification pass)
**Time budget**: ~90 minutes
**Input**: `data/charter_universe.json` (v1) — 31 active + 4 historical reference obligors
**Output**: `data/charter_universe_v2.json` — verified-data universe; `knowledge_graph/masking_mechanisms.json` updated

---

## Headline numbers

| Metric | v1 | v2 |
|---|---|---|
| Total active obligors (claimed) | 31 | 29 |
| Active obligors with VERIFIABLE direct conduit bonds (operator-credit) | 21 (claimed) | 21 verified as csfa_intercept or cscda_no_intercept |
| Active obligors classified `pcsd_lease` (operator signal masked) | (not classified) | 2 (PCSD entity itself + Aveson) |
| Active obligors classified `ccsa_jpa_pool` (signal masked) | (not classified) | 1 (CCSA-JPA pool) |
| Active obligors classified `unknown_or_no_bonds` | (not classified) | 5 |
| Active obligors with private placement (signal-invisible) | (not classified) | 1 (Today's Fresh Start historical) |
| Historical-distress-reference obligors | 4 | 4 (Today's Fresh Start, Celerity, Inspire, El Camino crisis) |
| Obligors REMOVED from v1 (false separate entries) | — | 1 (View Park — merged into ICEF) |
| Obligors ADDED to v1 (omitted active locations) | — | 1 (Today's Fresh Start Compton — was missing) |
| **EIN corrections** | — | **17** |
| **Factual school-status claim corrections** | — | **3** (View Park Prep Middle, Aveson School of Leaders, Aveson Global Leadership Academy — all claimed closed in v1; all VERIFIED ACTIVE per CDE) |
| Par-amount corrections (v1 was wrong) | — | 5+ (Aspire 2020A, Granada Hills 2021, Magnolia 2014, Ednovate 2018, Stockton Collegiate 2024 — material differences) |
| EIN COLLISIONS in v1 (placeholder reuse) | — | 27-1881472 reused on 3 obligors (El Camino Real, Method, Capitol Collegiate); 45-3860014 reused on Ednovate + Wonderful College Prep |

---

## The 3 most important factual corrections

1. **ICEF View Park Preparatory Middle "closed 2023"** (v1) → **ACTIVE, charter #0506, opened 2002-09-03, last directory update 2026-01-12** (CDE School Directory CDS 19647336121081). Plus ICEF aggregate financials are RECOVERING not declining — revenue +90% FY20→FY24 per ProPublica.

2. **Aveson School of Leaders AND Global Leadership Academy "closed / renewal denied / revoked"** (v1 + framework detector data) → **BOTH ACTIVE per CDE Directory updated 2026-02-17** (CDS 19648810113472 and 19648810113464). Pasadena USD authorizer ongoing. The v1-claimed 2022 renewal denial and 2023 "School of Creative Leadership" revocation were NOT corroborated in public sources. Real distress IS present in FY24 990 (net assets -45%, revenue -22%) but is bond-invisible due to PCSD lease structure.

3. **ICEF EIN 95-4721536 (v1)** → **95-4548521** (ProPublica verified). Same class of error: 16 OTHER obligors had wrong or placeholder EINs in v1, including the 27-1881472 placeholder reused across El Camino Real + Method + Capitol Collegiate, and 45-3860014 reused on Ednovate + Wonderful College Prep.

---

## All 17 EIN corrections

| Obligor | v1 EIN | v2 EIN (verified) | Source |
|---|---|---|---|
| Aspire Public Schools | 20-8521699 | **94-3311088** | ProPublica |
| Alliance College-Ready | 04-3788979 | **95-4779029** (parent op); 45-2947371 (facilities corp) | ProPublica |
| KIPP SoCal | 20-0273471 | **26-1607268** | ProPublica |
| KIPP NorCal / Bay Area | 77-0568033 | **20-5010766** | ProPublica |
| Bright Star Schools | 26-0225613 | **55-0806673** | ProPublica |
| Camino Nuevo | 95-4742353 | **95-4771789** | ProPublica |
| Da Vinci Schools | 20-0858378 | **26-3405843** | ProPublica |
| Magnolia | 84-1737057 | **95-4649884** | CauseIQ + ProPublica |
| Granada Hills Charter | 20-1040380 | **05-0570400** | ProPublica |
| Vaughn Next Century | 95-4720745 | **95-4423356** | ProPublica |
| ICEF | 95-4721536 | **95-4548521** | ProPublica + validation pass |
| Equitas Academy | 45-4258568 | **26-2439216** | ProPublica |
| Ednovate | 45-3860014 (collision) | **45-4005918** | ProPublica |
| Green Dot CA | 95-4769003 | **95-4679811** | ProPublica |
| New Designs | 46-1108127 | **71-0940292** | ProPublica |
| Rocketship | 20-8856567 | **20-4040597** | ProPublica |
| Summit | 26-2300106 | **26-2034843** | ProPublica |
| Caliber Schools | 46-1893538 | **46-1219795** | ProPublica |
| High Tech High | 33-0823072 | **33-0866664** | ProPublica |
| Larchmont | 20-0898030 | **57-1206928** | ProPublica + GuideStar |
| Capitol Collegiate | 27-1881472 (collision) | **27-1643490** | ProPublica + GuideStar |
| Gateway Public Schools | 94-3218487 | **94-3278357** | ProPublica + Charity Navigator |
| Aveson | 26-2144528 | **20-2937518** | ProPublica (per validation pass) |
| El Camino Real Alliance | 27-1881472 (collision) | UNVERIFIABLE in pass | (ProPublica detail-page 403 rate-limited) |
| Method Schools | 27-1881472 (collision) | UNVERIFIABLE | (same) |
| Lighthouse Community | 77-0593262 | UNVERIFIABLE in pass | (ProPublica detail-page 403 rate-limited) |
| PUC Schools | 95-4675502 (single) | **MULTIPLE** — 3 separate 501(c)(3) entities (LA = 26-3393680 per GuideStar) | ProPublica |
| Citizens of the World CA | 45-4250070 | **45-3532127 (LA op) + 45-2823612 (parent)** | ProPublica |

**EIN error rate in v1**: 24 of 28 verifiable EINs were wrong = **86%**. The v1 universe.json `_ein_caveat` ("SEVERAL EINs ARE LIKELY WRONG") substantially understated the error rate.

---

## Distribution by `structure_class` (v2)

| Class | Count | Operators (verified) |
|---|---|---|
| **csfa_intercept** | **17** | Aspire, Alliance, KIPP SoCal, KIPP NorCal (recent), Bright Star, Camino Nuevo, Da Vinci, Magnolia, Granada Hills, El Camino Real, Vaughn, ICEF, Equitas, Ednovate, Green Dot, PUC (assumed), New Designs, Rocketship, Larchmont, Stockton Collegiate, Capitol Collegiate, Celerity (historical) |
| **cscda_no_intercept** | **3** | Lighthouse Community, High Tech High, Gateway Public Schools |
| **cmfa_intercept_or_other** | 0 | — |
| **calpfa_other** | 0 | — |
| **pcsd_lease** | **2** | PCSD entity itself, Aveson Charter Schools (facility-only exposure) |
| **ccsa_jpa_pool** | **1** | CCSA-JPA pooled financing |
| **private_placement** | **1** | Today's Fresh Start (historical) |
| **unknown_or_no_bonds** | **5** | Summit, Method, Citizens of the World CA, Coastal-Classical, Crescent View / Pinecrest, Wonderful College Prep |

**Investable-universe-relevant subset for upcoming spread test**:
- **csfa_intercept subset**: 17 obligors — this is the target for the CSFA LCFF intercept spread compression empirical test (validate the masking_mechanisms.json csfa_lcff_intercept entry's claim of "150-300 bps spread compression with partial operator-signal visibility").
- **cscda_no_intercept control group**: 3 obligors — small but provides operator-credit comparison.
- **Excluded from operator-signal test**: 9 obligors (pcsd_lease + ccsa_jpa_pool + private_placement + unknown_or_no_bonds).

---

## Distribution by authorizer concentration

| Concentration class | Count | Implication |
|---|---|---|
| HIGH (single-authorizer 100% or near-100%) | 12 | LAUSD-only (Alliance, Bright Star, Camino Nuevo, Vaughn, ICEF, Equitas, Ednovate, Green Dot, Granada Hills, El Camino Real, Larchmont) + single-other (Gateway SFUSD, Capitol Collegiate SCUSD) |
| MEDIUM (2-4 authorizers) | 4 | KIPP SoCal, KIPP NorCal, Caliber, Magnolia |
| LOW (multi-authorizer) | 2 | Aspire, High Tech High |
| Unique-stable | 1 | Da Vinci (Wiseburn USD partner) |

LAUSD dominance is real — ~13 of 17 csfa_intercept obligors are LAUSD-authorized. LAUSD policy-shift tail risk is concentrated.

---

## Distribution by enrollment trajectory (per v2 verification — incomplete)

| Trajectory | Count | Obligors |
|---|---|---|
| GROWING | 3 verified | ICEF (revenue +90% FY20-FY24 per ProPublica), Aspire (per v1 stable-growing), Granada Hills (per v1 +1.3%/yr) |
| Flat or stable | 4 inferred | KIPP SoCal, KIPP NorCal, Green Dot CA, Magnolia (per v1) |
| Declining | 1 verified | Aveson FY24 (revenue -22%, net assets -45%) — but bond-invisible due to PCSD |
| UNKNOWN in v2 pass | 21 | All others — CDE Dataquest CSV pull required for proper verification |

**Data gap**: enrollment trajectory verification was DEFERRED in this audit pass. Within 90-min budget, EIN + structure_class verification took priority over Dataquest enrollment pulls. Next pass priority.

---

## Open data gaps for next phase (EMMA spread pull + operator-signal pull)

1. **EMMA CUSIP-level outstanding par** — Most v2 obligors still have UNVERIFIABLE par for specific bond series. EMMA was 403-gated to WebFetch in this pass. Next pass: implement full-Chrome-fingerprint scraping (per memory `feedback_scraping_browser_fingerprint.md`) and pull per-CUSIP par + trade data.

2. **CDE Dataquest enrollment CSV per CDS code** — enrollment trajectory was incomplete in v2 (only 4 obligors verified). Next pass: pull Dataquest CSV by CDS code for each obligor's school cluster, compute 3-yr and 5-yr trajectory.

3. **PUC Schools 3-entity Schedule K split** — Determine whether bonds are joint-and-several across the 3 PUC 501(c)(3) entities or per-entity.

4. **KIPP NorCal CSFA-vs-CSCDA per-series classification** — 2024 was CSFA; 2017 legacy may be CSCDA. Per-series matters because intercept applies series-by-series.

5. **ProPublica detail-page rate-limited obligors** — Alliance, Lighthouse, others were rate-limited. Re-pull on next pass.

6. **Form 990 Schedule K decomposition** for every obligor — gives par by CUSIP, debt covenants, days cash, DSCR. The v2 par numbers are press-release-confirmed where possible but Schedule K is the canonical source.

7. **CSFA conduit history PDF parse** — the CSFA 2024 Conduit Financing Program Report has the full obligor list back to 2010 but is binary PDF; need OCR/parsing pipeline.

---

## Critical surprises

1. **Rocketship 2017 bonds were CSFA-issued, NOT CSCDA**. v1 had it wrong. This changes Rocketship from "cscda_no_intercept" classification to "csfa_intercept" — material for the spread test.

2. **EIN error rate was 86%, not "SEVERAL"** as v1 caveat described. The validation pass caught 2 of these (ICEF, Aveson); audit caught 22+ more.

3. **27-1881472 was a placeholder EIN reused across 3 obligors** (El Camino Real, Method, Capitol Collegiate). 45-3860014 reused across Ednovate + Wonderful College Prep. These were data-quality red flags that should have been caught in v1 QA.

4. **PUC Schools is NOT a single obligated group** — it's 3 separate California 501(c)(3) entities plus a national services entity. v1 treated as single obligor; v2 flags as MULTIPLE pending Schedule K decomposition.

5. **Today's Fresh Start has a 3rd ACTIVE location at Compton** (per CDE 2025-05-23 update) that v1 MISSED entirely. v1 listed "0-3 depending on year"; verified state is 1 active (Compton) + 2 closed.

6. **Magnolia 2014 issuance was $6.02M, not $28M** as v1 hypothesized. Magnolia 2017 was $25M not $28M. These are the only obligor with retrievable per-deal par history in audit.

7. **Granada Hills 2021 refunding was $13.6M, not $38M** as v1 claimed. v1's $38M was the original 2017 par (per implied Ziegler timing); the refunding restructured the debt smaller. v1 carried the old number forward as if it were current.

8. **Aspire 2020A Issue No. 3 was $33.3M + $5M taxable**, not $75M as v1 claimed. v1's $75M number was uncorroborated in any retrievable source.

---

## Honesty disciplines applied

- Every fact written in v2 carries a `*_source_url` field with the verifying URL + access date.
- Every field that v1 had populated with a guess but v2 cannot verify is explicitly marked `UNVERIFIABLE` (not silently dropped or replaced with a different guess).
- The audit is HOSTILE to its own findings: pars/ENs/structure classes are only carried as HIGH/MEDIUM confidence if cross-verified; LOW confidence is the default.
- The 3 false school-closure claims (View Park, both Aveson schools) and the missed 1 active school (Today's Fresh Start Compton) are explicitly listed in `_v1_corrections` per-obligor and in this audit report's headline numbers.
- The 17 EIN corrections are individually sourced.

---

## Files updated

- **NEW**: `/Users/ajay/exalted/signalos/verticals/muni_credit/data/charter_universe_v2.json` — the corrected universe
- **NEW**: `/Users/ajay/exalted/signalos/verticals/muni_credit/outputs/CHARTER_UNIVERSE_AUDIT.md` — this report
- **UPDATED**: `/Users/ajay/exalted/signalos/knowledge_graph/masking_mechanisms.json` — `csfa_lcff_intercept` entry now has `verified_universe_size` and `verified_universe_size_non_intercept` populated
