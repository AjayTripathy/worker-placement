# Art Donation Fraud — Cohort Intelligence Report (v1)

_Generated 2026-05-16T00:36:01.031593Z — `verticals.art_donation_fraud.cohort_runner`_

## What this is

End-to-end run of the Signal OS `art_donation_fraud` vertical. Pulls every "Gift of" / "Bequest of" / "Promised Gift of" high-value-classification record from the Metropolitan Museum of Art and the Museum of Modern Art bulk open-data CSVs, aggregates by normalized donor name, computes per-donor portfolio features, and applies the `AUCTION_TO_DONATION_MATCH` rule (IRC §170(e)(1)(A) + Treas. Reg. §1.170A-13(c)).

**R (claim, not directly observed):** the donor's claimed fair-market-value deduction on Form 8283. Form 8283 is not public; we infer at the cohort level rather than per-work.

**f (relationship):** Treas. Reg. §1.170A-13(c) — claimed FMV must equal what a willing buyer would pay a willing seller in the regular market. Auction comparables for the same artist / period / medium are the regulatory benchmark.

**M (observed):** Met + MoMA acquisition records (open-data CSVs, free, agent-doable). Per-work auction comparables would close the loop — see *Debt and tradeoffs* below.

## Topline

| Metric | Value |
|---|---:|
| Distinct normalized donors (Met + MoMA, gifts 2010+) | 1,295 |
| Total high-value-classification gift records | 15,936 |
| Donors flagged by `AUCTION_TO_DONATION_MATCH` | 77 |
| Works in flagged-donor portfolios | 9,548 |
| Of those, bequest-pattern (single-year disbursement) | 47 |
| Of those, active living-collector pattern (≥50% market-volatile) | 2 |
| Of those, portfolio-scale donors (≥100 works) | 14 |

## Highest-risk archetype — medium-volume, market-volatile, clustered

Mid-sized (20-200 work) portfolios concentrated in Modern/Contemporary or European Paintings, with most works donated in a single tax year (consistent with a bunching strategy or single-year tax planning event). This is the archetype where the gap between cost basis and claimed FMV is most exploitable: high-volatility market = subjective appraisal values; concentrated timing = single appraiser engagement; mid-sized portfolio = below the IRS Art Advisory Panel mandatory threshold ($50K per item) for most individual works.

| Rank | Donor (normalized) | Works | Year range | Cluster yr | Cluster % | High-vol % | Top dept |
|---:|---|---:|---|---:|---:|---:|---|
| 1 | PATRICIA PHELPS DE CISNEROS THROUGH THE LATIN | 167 | 2010–2017 | 2016 | 58% | 54% | Painting & Sculpture |
| 2 | AXA EQUITABLE | 29 | 2012–2016 | 2016 | 97% | 100% | Modern and Contemporary A |
| 3 | JACQUELINE LOEWE FOWLER | 56 | 2017–2021 | 2021 | 95% | 41% | Drawings and Prints |
| 4 | KENNETH JAY LANE | 27 | 2014–2018 | 2017 | 44% | 78% | European Paintings |

## Bequest-pattern donors (estate disbursement, lower fraud risk)

Single-year, single-event disbursements consistent with estate gifts or foundation dissolution. Lower fraud risk because the donor (decedent) no longer benefits from any FMV inflation; the §170(e)(7) recapture still applies if the museum disposes of the work early, but the primary `AUCTION_TO_DONATION_MATCH` fraud shape doesn't fit.

_47 donors. Top 15 by volume:_

| Donor | Works | Cluster year | Top dept |
|---|---:|---:|---|
| PHYLLIS MASSAR | 1338 | 2012 | Drawings and Prints |
| THE ROY LICHTENSTEIN FOUNDATION | 652 | 2013 | Photography |
| THE GILBERT B AND LILA SILVERMAN INSTRUCTION DRAWI | 285 | 2018 | Drawings & Prints |
| SPERONE WESTWATER | 182 | 2012 | Drawings & Prints |
| JACOB AND YAEL SAMUEL | 182 | 2015 | Drawings & Prints |
| THE DALED COLLECTION AND PARTIAL PURCHASE THROUGH  | 172 | 2011 | Drawings & Prints |
| HELEN AND SAM ZELL | 110 | 2022 | Drawings & Prints |
| ILSE BING WOLFF | 95 | 2013 | Photography |
| STEVEN KASHER AND SUSAN SPUNGEN KASHER | 93 | 2011 | Photographs |
| MAURICE B SENDAK | 90 | 2013 | Photographs |
| AMY BAKER SANDBACK | 85 | 2014 | Drawings & Prints |
| CHRISTOPHER MCCALL | 82 | 2021 | Photography |
| NEIL SELKIRK | 70 | 2012 | Photographs |
| PAUL REIFERSON AND JULIE SPIVACK MD | 67 | 2020 | Photographs |
| DITTE WOLFF | 64 | 2015 | Drawings and Prints |

## Portfolio-scale active donors

Donors with ≥100 works in the Met+MoMA collection from 2010+ who have been donating across multiple years (i.e., not pure bequest). These are the institutional-scale collectors. Many are legitimate, but the pattern of large-scale repeat donation is also where the most sophisticated tax-shelter structures appear (private operating foundations donating to museums, charitable lead annuity trusts, etc.).

| Donor | Works | Years span | Museums | High-vol % | Top depts |
|---|---:|---:|---|---:|---|
| PETER J COHEN | 1394 | 8 | met+moma | 0% | Photography(1339); Photographs(53) |
| HERBERT MITCHELL | 620 | 2 | met | 0% | Photographs(482); Drawings and Prints(138) |
| C R LINDLEY M D | 567 | 8 | met | 0% | Photographs(567) |
| CHARLES WRIGHTSMAN | 196 | 3 | met | 12% | Drawings and Prints(164); European Paintings(24) |
| SUSAN AND PETER MACGILL | 185 | 6 | met+moma | 0% | Photography(178); Photographs(7) |
| HELENA BIENSTOCK CYNTHIA MACKAY KEEGAN AND FR | 177 | 2 | met | 0% | Drawings and Prints(177) |
| ROBERT B MENSCHEL | 173 | 3 | moma | 0% | Photography(173) |
| PATRICIA PHELPS DE CISNEROS THROUGH THE LATIN | 167 | 8 | moma | 54% | Painting & Sculpture(91); Drawings & Prints(37) |
| MONICA AND MARKUS HOTTENROTT | 145 | 2 | met | 0% | Photographs(145) |
| DONATO ESPOSITO | 138 | 6 | met | 0% | Drawings and Prints(138) |
| JOYCE F MENSCHEL | 136 | 7 | met | 0% | Photographs(136) |
| THE IRVING PENN FOUNDATION | 131 | 5 | met | 0% | Photographs(131) |
| HELEN KORNBLUM | 116 | 6 | moma | 0% | Photography(116) |
| HEIDI AND RICHARD RIEGER | 108 | 6 | moma | 0% | Photography(108) |

---

## Debt and tradeoffs (built into this v1)

Per the connector-discipline rule, this section is honest about what is shippable today vs. what requires another connector or external action. None of the items below are shipped in this run.

### Binding constraint: per-work auction comparables

The `AUCTION_TO_DONATION_MATCH` rule fires today on **structural portfolio patterns** (volume, classification mix, year-clustering) rather than on per-work auction comps. The cleanest fraud signal — "donor X bought work W at Christie's NY in 2022 for $1.2M, then donated W to the Met in 2023 and claimed $5M FMV" — requires an auction-comp connector that this v1 does not have.

**Auction connector triage (per connector-discipline rule):**

| Source | Bucket | Probed today | Outcome |
|---|---|---|---|
| Christie's lot archive | agent-doable (in theory) | yes | `/api/v1/search` empty; 404 on guessed paths. Real API requires reverse-engineering their internal GraphQL. |
| Sotheby's lot archive | agent-doable (in theory) | yes | Results page returns 200 but no `__NEXT_DATA__` and no price strings — fully JS-rendered. Would need Playwright + bot-detection bypass. |
| Artsy public API | agent-adjacent (free key required) | yes | 401 without `xapp_token`. Free signup at artsy.net/developers. |
| Wikidata SPARQL (`P2284 price`) | agent-doable | yes | SPARQL endpoint timed out on the auction-price query; would need narrower query or alternate mirror. |
| Heritage Auctions | agent-doable | yes | TLS 1.0 alert from their server — needs a TLS-version fallback or direct HTML scrape. |
| Phillips lot archive | agent-doable | partial | 200 on past-auctions page (6.8MB HTML); parser not yet written. |
| Artnet / Artprice / MutualArt | **paid-vendor, human-doable** | n/a | Comprehensive auction comps; the right answer for production. Artnet Price Database: $480/yr individual, ~$2.5K/yr commercial. |

**Recommended next step:** sign up for the free Artsy `xapp_token` (agent-adjacent, ~5 min), then build a Sotheby's HTML scraper using Playwright (~2 hr). The auction-comp coverage would convert this cohort-intelligence report into per-work fraud confirmations.

### Secondary connectors not yet wired

- **Other top US museums.** This v1 covers only Met + MoMA. The Whitney, Guggenheim, Art Institute Chicago, LACMA, Getty, Boston MFA, Philadelphia Museum of Art, and SFMOMA collectively account for the bulk of major-donor art philanthropy. None publish bulk CSVs as cleanly as Met/MoMA, but most have either web-scrapeable collection pages or downloadable acquisition lists. **Bucket: agent-doable.** Estimated effort: 1-2 hrs per museum scraper.
- **Museum deaccession records.** Required for the `EARLY_DEACCESSION_RECAPTURE` (§170(e)(7)) rule which is currently `implementation=None`. Deaccessions are published in piecemeal fashion (museum press releases, ARTnews / Art Newspaper coverage, auction lot consignor names). No central registry. **Bucket: human-doable** — best constructed by FOIL request to museums (museums are usually 501(c)(3) and subject to state non-profit disclosure) or via paid art-news archive subscription.
- **Form 990 Schedule M bulk.** IRS publishes 990 XML in bulk via the AWS S3 mirror `s3://irs-form-990/`. Schedule M reports total non-cash contributions by category per museum-year. Adds aggregate sanity check (does Met's reported non-cash gift value match the sum of inferred values of works we see?). **Bucket: agent-doable.** Estimated effort: 2-3 hrs.
- **IRS Art Advisory Panel annual reports.** Published PDFs with aggregate statistics on appraisal reviews (volume of submissions, % reduced, average reduction). Useful for calibrating the base rate of fraud. **Bucket: agent-doable.** Estimated effort: 1 hr (PDF scrape).
- **Donor wealth / capital-gains-event correlator.** Public-figure donors with known wealth events (IPO, large stock vest, real-estate sale) in the same year as a clustered gift make for the strongest fraud-risk signal. Requires SEC EDGAR Form 144 / Form 4 cross-join. **Bucket: agent-doable.** Estimated effort: 2-4 hrs.

### Methodological tradeoffs in this v1

- **Donor name normalization is regex-based.** Catches most patterns (`Mr. and Mrs. X` → `X`; honorific stripping) but misses long composite names (`HELENA BIENSTOCK CYNTHIA MACKAY KEEGAN AND FRANK E JOHNSON` is a joint gift that should be split into 3 distinct donors). Per-donor aggregation undercounts as a result.
- **Bequest vs. lifetime gift partitioning is heuristic.** I treat single-year ≥95% clustering as bequest. The actual cleanest signal is the credit-line prefix (`Bequest of` vs `Gift of` vs `Promised Gift of`); currently the parser captures this in `gift_year` but the runner does not yet use it as a partition key.
- **High-value classification filter is narrow.** Photographs and prints dominate the cohort (5,767 records of 15,936). Both have legitimate fraud cases but the highest dollar exposure per item is in paintings + sculpture (where the rule actually targets via `high_vol_share`). The filter could be tightened to exclude prints/photographs from the high-volume rule branch — keeping them only in the high-volatility branch.
- **No artist-market-volatility data.** The rule treats all of "Modern and Contemporary Art" as high-volatility, but within the dept a Wade Guyton donation and an unknown emerging artist donation are very different. An artist-level volatility score (auction price σ over time) would refine the signal.
- **Single-museum view of each donor.** The Met-cross-MoMA pattern (e.g., Patricia Phelps de Cisneros gives to BOTH) is detected because we union the two CSVs. But the broader cross-museum view (Whitney + Guggenheim + MoMA + Met) is not — and that's where the biggest patterns live (`Eli Broad`, `David Geffen`, `Henry Kravis` etc. spread their gifts).
