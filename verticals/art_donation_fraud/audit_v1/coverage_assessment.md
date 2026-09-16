# Coverage Assessment — art_donation_fraud M-sources

Per Layer 3 Rule 2: a "no signal" output cannot be read as "no fraud" until you know what the M-source actually covers. This document enumerates what kinds of donors / works / claims are reachable by the v1 pipeline and what's structurally invisible.

## What's wired (v1)

| Source | Role | Live? | Coverage |
|---|---|---|---|
| `met_bulk_csv.py` (Met openaccess CSV) | M (museum acquisition records) | yes | 480K Met objects total; 7.4K gifts since 2010 in high-value classifications |
| `moma_bulk_csv.py` (MoMA Artworks.csv) | M (museum acquisition records) | yes | 140K MoMA objects total; 8.6K gifts since 2010 in high-value classifications |
| Donor name normalization + cohort aggregation | M-side transform | yes | 1,295 distinct normalized donors after deduping titles, "Mr. and Mrs. X" patterns, etc. |

Two museums total. The R-side (Form 8283 claimed FMV) is **not directly observed**; the v1 infers patterns at the cohort level.

## Donor / claim / work coverage matrix

### Well-covered

- **Active living collectors who donate to Met or MoMA, 2010-present, in high-value classifications.** Modern/Contemporary Art, European Paintings, Drawings, Prints, Photographs, Sculpture. These show up with full credit-line metadata, year, work attribution, classification.
- **Single-museum donor portfolios with clear name patterns.** "Gift of [Name], [Year]" patterns parse cleanly. Aggregation by normalized name reliably groups multi-year donations from the same individual.
- **Bequest patterns.** "Bequest of [Name], [Year]" parses cleanly. The single-year-cluster heuristic correctly identifies estate-driven disbursements as a separate archetype from active-collector clusters.

### Partially covered

- **Joint donor gifts.** "Mr. and Mrs. X" usually normalizes to the named spouse (typically the husband, per historical convention). Joint gifts where both spouses are independently wealthy are aggregated to one name; their separate auction histories aren't distinguished. Minor false-negative source for couples filing jointly.
- **Foundation gifts.** "Gift of the Annenberg Foundation, 1999" parses as `THE ANNENBERG FOUNDATION`. Foundation gifts are usually NOT the fraud pattern (foundations have their own 990 reporting and don't claim individual FMV deductions). But individual donors *using* a private foundation as a passthrough do, and we can't currently distinguish.
- **Complex composite credit lines.** `HELENA BIENSTOCK CYNTHIA MACKAY KEEGAN AND FRANK E JOHNSON` is three or more co-donors; the normalizer treats it as one. Per-donor aggregation undercounts here.
- **Promised gifts that haven't been formally accessioned.** "Promised Gift of X" appears in credit lines but the work may not yet be on the museum's books; the donor may still be claiming an annual partial deduction. Pattern observable; magnitude not.

### Structurally invisible to current M

1. **Form 8283 itself.** The donor's claimed FMV. This is the R. Not public; obtainable only through whistleblower (§7623) or tax-court litigation discovery.
2. **The donor's basis in the work.** Required to compute the actual fraud magnitude (R − cost basis × inflation factor). Sometimes inferable from auction history if the donor bought publicly; otherwise opaque.
3. **The appraiser.** Form 8283 Section B names the appraiser. Some appraisers have established patterns (rejected by Art Advisory Panel repeatedly). Not currently reachable.
4. **Museum deaccessions.** The §170(e)(7) recapture-trigger event. Some museums publish in annual reports; most don't. Auction lots sometimes say "Property from [museum] to benefit acquisitions fund" but inconsistently.
5. **Other major US museums.** Whitney, Guggenheim, Art Institute Chicago, LACMA, Getty, Boston MFA, Philadelphia MFA, SFMOMA, Brooklyn Museum, Hirshhorn, National Gallery. Together these probably outweigh Met+MoMA by donor count if not dollar volume. Each requires a separate connector.
6. **Non-museum charitable donees.** Universities (Yale, Harvard, Princeton art museums), libraries (Morgan, Huntington), historical societies — all qualified §501(c)(3) recipients of art donations. Wholly outside current scope.
7. **Auction comparables for the same work.** The cleanest fraud signal — "this work sold at auction in 2022 for $X, donor claimed $Y" — requires a per-work auction lookup that the v1 does not have.
8. **Donor-side financial events.** Public-figure donors with known capital-gains events in the same year as a clustered gift (Form 144 stock sales, Form 4 insider sales, IPO unlock dates). SEC EDGAR has all of this; no current cross-join.
9. **IRS Art Advisory Panel reductions.** Annual reports give aggregate stats but no donor-level outcomes. Some tax-court decisions (Hostetter, Smith, etc.) are case-by-case wins for the IRS that aren't currently used as ground truth.
10. **Private operating foundation passthroughs.** A donor who routes art through a private operating foundation (PoF) gets full FMV deduction but the PoF then donates to a museum at a different point in time. Hard to trace without 990-PF connector.

## "We found nothing wrong" honesty check

The v1 produces a sorted list of 77 flagged donors out of 1,295. Donors NOT flagged could be:

- Truly low-fraud-risk (steady stream of modest gifts, or single-work bequests)
- High-risk but outside the volume/volatility/clustering thresholds (e.g., a single $20M painting donation by an active collector wouldn't fire — n_works=1 fails the ≥25 threshold)
- High-risk and donating to museums outside this v1's scope (Whitney, Guggenheim, etc.)
- Hiding behind a name normalization that splits one donor across multiple keys

The bottom 80% of the matched list (confidence 0.65-0.80) is also noisy — bequest cases that look like fraud-pattern clusters because the heuristic doesn't distinguish living-donor bunching from estate dispersal as cleanly as it should. The credit-line prefix ("Gift of" vs "Bequest of") would fix this — currently parsed but not used as a partition.

## Concrete sources the framework should add

Ranked roadmap is in `connectors_to_add.md`. Headline:

| Gap | Source | Bucket | Closes |
|---|---|---|---|
| Per-work auction comparable | Artnet / Artprice / MutualArt | Paid (human-doable) | The R-vs-market gap per donation |
| Cross-museum donor view | Whitney + Guggenheim + AIC + LACMA + Getty + Boston MFA + SFMOMA scrapers | Agent-doable | The institutional collectors who spread gifts |
| Capital-gains-event correlator | SEC EDGAR Form 4 / Form 144 cross-join | Agent-doable | Public-figure donors with concurrent wealth events |
| Aggregate sanity check | IRS 990 Schedule M bulk | Agent-doable | Does claimed museum non-cash income reconcile to observed gifts? |
| Base-rate calibration | IRS Art Advisory Panel PDFs | Agent-doable | What % of appraisals get reduced, by how much |
| Deaccession events | Per-museum FOIL / state nonprofit disclosure | Human-doable | Wires §170(e)(7) recapture rule |
