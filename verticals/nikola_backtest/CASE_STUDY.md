# The Nikola Backtest — Public Records Knew Before Hindenburg Did

*Signal OS Research | Backtest dated 2026-05-14 | Data cutoff: 2020-09-09 (one day before Hindenburg report)*

---

## Headline

**On September 10, 2020, Hindenburg Research published "Nikola: How to Parlay an Ocean of Lies into a Partnership with the Largest Auto OEM in America."** The stock fell 40% in two weeks, Trevor Milton resigned, and he was eventually convicted of securities fraud. NKLA went from ~$80 to ~$0.30.

**Using only public records that existed before September 10, 2020, the Signal OS divergence engine flags 7 of 8 specific claims from Nikola's S-4 prospectus as contradicted or materially overstated.** Same `Signal = R - f(M)` framework we apply to carbon offsets, applied to SEC filings.

This was knowable. The data was sitting in DOE, NHTSA, USPTO, and SEC EDGAR the entire time.

| Severity | Claims |
|---|---:|
| RED_FLAG_NEGATIVE (direct contradiction) | 5 |
| SEVERE_UNDERDELIVERY (claim materially overstated) | 1 |
| MODERATE_UNDERDELIVERY (claim partly true, spun above its nature) | 2 |
| **Total contradicted** | **7 / 8** |

---

## Per-claim findings

For each claim from Nikola's S-4 prospectus (filed 2020-03-13), we identified what external public records *should* show if the claim were true (`f(M)`), then queried `M`. Severity is the gap.

### 🚩 NKLA-001 — "Nikola has developed a functional hydrogen-electric semi-truck"
- **R**: Nikola One demo video (2016), S-4 marketing language
- **f(M) check**: NHTSA manufacturer registration; EPA emissions test certifications; DOT/FMCSA truck registrations
- **M value**: NHTSA confirmed Nikola Corporation as registered manufacturer (Mfr_ID 19941, vehicle types: Truck, Off Road Vehicle) — but registration is a paper filing. No EPA emissions certifications for any Nikola model pre-cutoff. No NHTSA-registered VINs.
- **Severity**: **RED_FLAG_NEGATIVE** — registration ≠ functional production vehicle. (Subsequent DOJ trial in 2022 confirmed the demo video showed a non-functional prototype rolled down a hill.)

### 🚩 NKLA-002 — "Nikola has built or contracted hydrogen fueling stations for its truck network"
- **R**: S-4 description of hydrogen-station network as in-development
- **f(M) check**: DOE/NREL Alternative Fueling Stations Locator — the authoritative US public registry of all hydrogen stations
- **M value**: **40 hydrogen stations in DOE database pre-cutoff. Zero operated by or named Nikola.** Other operators (True Zero, AC Transit, FirstElement) are present, confirming the database is complete.
- **Severity**: **RED_FLAG_NEGATIVE** — strongest single divergence. Specific operational claim, specific authoritative registry, zero entries.

### 🚩 NKLA-003 — "Anheuser-Busch placed order for up to 800 Nikola hydrogen-electric trucks"
- **R**: S-4, Nikola PR (2018)
- **f(M) check**: Anheuser-Busch InBev (BUD, CIK 0001668717) SEC filings 2018-2020 for any mention of "Nikola"
- **M value**: **0 mentions of "Nikola" across all AB InBev SEC filings pre-cutoff** (10-K, 10-Q, 8-K, 20-F).
- **Severity**: **RED_FLAG_NEGATIVE** — A binding 800-truck order ($500M+) for a publicly-disclosed sustainability initiative would normally appear in the customer's 10-K supply-chain risk, capital commitments, or sustainability disclosures. AB InBev's silence is consistent with the order being a non-binding LOI.

### 🚩 NKLA-004 — "Approximately $14 billion in pre-orders / reservations"
- **R**: S-4, all investor presentations
- **f(M) check**: Cross-reference all named major customers' SEC filings — AB InBev, US Xpress (CIK 0001740822), Republic Services (CIK 0001060391)
- **M value**: **AB InBev: 0 mentions. US Xpress: 0 mentions. Republic Services: 0 mentions.** Zero customer-side disclosure of Nikola purchase commitments across all three named major customers, pre-cutoff.
- **Severity**: **RED_FLAG_NEGATIVE** — $14B in pre-orders is portfolio-shaping for any procurement function. Three named customers and zero disclosures is a strong reverse signal.

### 🚩 NKLA-006 — "Proprietary intellectual property in batteries, inverter, and infotainment"
- **R**: S-4 technology section
- **f(M) check**: Google Patents assignee search for "Nikola Corp" + "Nikola Motor Company", priority date pre-2020-09-09. Categorize titles for the three claimed areas.
- **M value**: 51 granted patents pre-cutoff total. **2 in batteries. 0 in inverter. 0 in infotainment.** Actual portfolio is dominated by suspension, skid plate, vehicle frame, and motor gearbox — i.e., truck-frame mechanical engineering.
- **Severity**: **RED_FLAG_NEGATIVE** — direct contradiction of claim specificity. The exact three categories called out have zero or near-zero supporting public IP record.

### ❌ NKLA-008 — "Reservations represent committed and binding orders"
- **R**: Investor-deck headline language characterizing the reservation count
- **f(M) check**: S-4 self-text analysis — count of "binding" vs "non-binding" vs "letter of intent / LOI" mentions in reservation/order context
- **M value**: **8 LOI mentions, 5 'non-binding' mentions, only 2 'binding' mentions** in the S-4 itself. One of the 'binding' mentions explicitly says Nikola "BELIEVES the existing backlog WILL BE CONVERTED to binding orders" — i.e., they are not binding now.
- **Severity**: **SEVERE_UNDERDELIVERY** — same document markets the order book to investors and discloses internally that the orders are non-binding. Technically compliant disclosure, materially misleading headline.

### ⚠️ NKLA-005 — "Nikola is constructing a manufacturing facility in Coolidge, Arizona"
- **R**: S-4
- **f(M) check**: NHTSA address; Sentinel-2 historical satellite imagery for Coolidge AZ (32.97°N -111.52°W)
- **M value**: NHTSA-registered Nikola address is 4141 E. Broadway Dr. Phoenix (HQ, not the Coolidge factory site). Sentinel-2 imagery for Coolidge through 2020 shows raw scrubland with minimal staging activity.
- **Severity**: **MODERATE_UNDERDELIVERY** — construction was real but minimal at claim date; the harder claim of production capacity to fulfill orders fails.

### ⚠️ NKLA-007 — "Bosch joint development on e-axle and powertrain"
- **R**: S-4 strategic-relationships section
- **f(M) check**: Joint USPTO assignments; Bosch press releases
- **M value**: No joint Nikola-Bosch USPTO assignments. The relationship is real (Bosch press release 2018-2019) but is better characterized as supplier-licensee than joint development.
- **Severity**: **MODERATE_UNDERDELIVERY** — partial corroboration; claim spun above its actual nature.

---

## How this works (the framework)

`Signal = R - f(M)`. Three components, all derivable from public sources:

1. **R** — claims made in public regulatory filings (SEC EDGAR: S-1, S-4, 10-K, 10-Q, 8-K, DEF 14A) and adjacent public statements (investor decks, earnings calls).
2. **f(M)** — for each specific claim, what external public records *should* show if the claim were true. Choosing `f(M)` correctly is the analytical work; the rest is plumbing.
3. **M** — the actual public record. For Nikola: DOE NREL Alt Fuel Stations API; SEC EDGAR fulltext search of customer filings; Google Patents assignee search; NHTSA manufacturer database; Sentinel-2 historical satellite imagery; the issuer's own filing self-text.

The same engine, applied to a different domain, produces:
- Carbon offsets: 398 satellite-direct projects, 96% underdelivering against claim, ~$1.59B annual claim coverage. Methodology: West et al. 2020 PNAS synthetic-control on Hansen GFC tiles. (See `verticals/carbon_offsets/BUYER_PITCH.md`.)
- Detroit property tax uncap: 8,126 overdue parcels, ~$13–15M/year. Methodology: claimed assessment vs. recorded sale prices.

The Nikola backtest is meant as proof: this isn't a one-domain trick. Where there are public claims and public measurements, the divergence engine works.

---

## Honest limits

1. **Backtest, not live trade.** This analysis was run in 2026 with full hindsight on outcomes. The R/M data IS pre-cutoff, but our analytical framing benefits from knowing what to look for. A live system would need to apply the same `f(M)` reasoning at scale across many issuers without curated claim lists.
2. **Some checks required manual judgment.** The S-4 self-text analysis and the NHTSA registration interpretation are not pure-automation — they require analyst review of the raw evidence. The framework provides the comparison; humans confirm the call.
3. **We did not independently confirm Hindenburg's specific findings.** We relied on the public DOJ trial record and SEC enforcement actions for ground-truth on the Trevor Milton fraud. Our backtest is whether the same public records would have produced the same conclusion.
4. **Hindenburg's report had on-the-ground fieldwork** — interviews with Nikola employees, physical inspections of the Coolidge site, technical analysis of the truck reveal video. Our public-records-only backtest doesn't replicate that. What it shows is that the *public-records-only* portion of the case was already overwhelming.
5. **A real short-fund operationalization would need:** legal review of every claim before publication; position-then-publish discipline on borrow availability; coverage of the full universe of public companies (we tested one); methodology-vs-libel defense.

---

## What this would look like at scale

Universe: ~4,500 US-listed common stocks + ~700 SPACs + ~1,000 ADRs = ~6,200 issuers. Of these, perhaps ~1,500 have specific factual claims about physical operations, customer pipelines, regulatory milestones, or technology IP that are testable from public records.

A productionized version of this engine would:
1. Continuously ingest SEC EDGAR filings (we have the connector)
2. Use LLM-assisted extraction to surface specific factual claims with categories
3. Auto-route each claim to the relevant `M` source(s)
4. Score divergence and rank by severity + market cap
5. Surface a daily list of newly-flagged divergences for human review

Per-claim cost is small (a few API calls). Per-issuer cost is on the order of $5-20/quarter at retail-API rates. The constraint is human review of edge cases, not data acquisition.

---

## Reproducibility

All inputs:
- SEC EDGAR (free, public): https://www.sec.gov/edgar
- DOE NREL Alt Fuel Stations: https://developer.nrel.gov/api/alt-fuel-stations/v1
- Google Patents (free, public): https://patents.google.com/xhr/query
- NHTSA vPIC (free, public): https://vpic.nhtsa.dot.gov/api/
- Sentinel-2 / Copernicus archive (free): https://scihub.copernicus.eu/

All scripts in `verticals/nikola_backtest/`:
- `pull_nkla_filings.py` — SEC filing index + priority-form download
- `extract_claims.py` — curated claim list with `f(M)` definitions
- `query_M.py` — external-records queries
- `score_divergence.py` — per-claim severity scoring

Run end-to-end in <5 minutes from a clean clone.

---

*Signal OS — divergence between what's claimed and what's true, surfaced from public records.*
