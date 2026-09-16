SEC direct fetch 403'd (no fingerprint header available to WebFetch — the known failure path), so I verified against the company's own primary IR release and flagged anything I could only reach via secondary. Two defects in the evidence pack surfaced along the way.

---

**Triage context:** The pack's XBRL block is stale by roughly three quarters and understates the case by ~2,500x (it shows `rev 2025-06-30=15,000` — fifteen thousand dollars — while Q2 2026 revenue was $38.6M); the cohort definition at `knowledge_graph/cohorts.json` is outside my readable path, so the narrative below is **reconstructed** from the tape and sector, not read from the cohort file. Joby printed Q2 on 2026-08-05, then on 2026-08-11 announced both a $500M defense acquisition and a $750M ATM — so the "sold indiscriminately, nobody looked" premise is weak here: this name has three fresh, well-covered disclosures.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| JOBY | **STRUCTURAL** | Non-Blade revenue (revenue NOT from the acquired helicopter-brokerage business) — the only line that can show eVTOL/defense commercialization | ~**$2.4M of $38.6M total Q2 2026 revenue (~6%)**. Company release states Blade alone generated "**$36.2 million in Q2 revenue**"; total Q2 revenue $38.6M and FY26 outlook raised to "**$115 million to $125 million**" — a raise management attributes to Blade seat sales +50% y/y, not to aircraft. [jobyaviation.com Q2 2026 release](https://www.jobyaviation.com/news/joby-reports-second-quarter-2026-financial-results) | **2026-11-04** (yfinance-derived, UNCONFIRMED by company PR) | The revenue that appears to refute "pre-revenue" is *purchased conventional aviation revenue*. It does not touch the narrative actually being priced. Financing leg is separately confirmed, not refuted: $750M ATM signed 2026-08-11 = **9.2% of market cap** of mechanical supply. |

**Why not DAMAGE-ABSENT.** I tested the three legs of the narrative separately, because they do not resolve together:

- **Cash-crunch leg → genuinely REFUTED.** "$2.3B in cash and short-term investments as of June 30, 2026" ([company release](https://www.jobyaviation.com/news/joby-reports-second-quarter-2026-financial-results)) against ~$197M/qtr adjusted EBITDA loss ≈ 11–12 quarters. Net of the ~$450M cash portion of Resonant, ~9 quarters. There is no runway emergency, and anyone shorting on insolvency is wrong.
- **Dilution leg → CONFIRMED.** $750M at-the-market program via Morgan Stanley/J.P. Morgan/Allen/BofA, up to 3.0% commission, struck when the last sale was $8.81 (424B5, accession 0001628280-26-055507, 2026-08-11). Per the desk's value-ladder flow gate, this is the disqualifier: the issuer is a standing seller into any rally, so a long here bids into its own predicted supply.
- **Commercialization leg → STRUCTURALLY TRUE.** "Strongest quarterly progress yet in fifth and final stage of FAA Type Certification" is progress language with **no dated milestone**, and 94% of revenue is Blade. At $7.88 the discount has not created value: ~$8.14B cap less ~$2.3B liquidity ≈ **~$5.8B EV on a $120M guide midpoint ≈ ~48x EV/sales**, essentially all of it brokered helicopter seats at a loss. A -60.6% drawdown made this less expensive, not cheap.

The one legitimately overlooked item — Resonant Sciences at >$100M TTM revenue, ~40% growth, high-teens adjusted EBITDA margins, into which the tape sold off ~4% — **fails the desk's anchor test**. Those target financials are seller/acquirer-sourced in Joby's own deal PR ([ir.jobyaviation.com](https://ir.jobyaviation.com/news-events/press-releases/detail/189/joby-aviation-to-scale-defense-business-through-acquisition), search-surfaced, not independently fetched); there is no external same-event anchor on a private target, and per *attestation ≠ audit* they must be discounted. It also does not close until 1H 2027 and requires national-security approval. That is an option on an unverified number, not a damage-absent finding.

**COURT-WORTHY (damage-absent, ranked):**
**NONE.** No member classifies DAMAGE-ABSENT. JOBY's only damage-absent leg (balance sheet) is not the leg the cohort is being sold on, and the leg it *is* being sold on is confirmed true by the company's own numbers.

**COURT-WORTHINESS JOBY: 3/10** — the discount is directionally correct and a court cannot move the sizing decision, because the $750M ATM independently gates entry regardless of how the eVTOL argument resolves.

**PRINT PROXIMITY: 2026-11-04 — yfinance-derived, UNCONFIRMED by any company PR; ~11 weeks out, far beyond the 5-trading-day window.** The decisive print (Q2) already landed 2026-08-05 with the 10-Q on 2026-08-06, so no pre-print reconstruction is owed and no PRE-PRINT POSITION line is triggered. Book is flat with no working orders and this triage recommends it stay flat.

---

Three things you should know about how this ran, since they affect other benches:

1. **The evidence pack's XBRL block is broken for JOBY** — its newest frame is 2025-06-30 and it reports revenue of $15,000 for a company that just guided to $115–125M. A bench that trusted it would have written "pre-revenue" and been wrong by three orders of magnitude. Worth checking whether the frame selector is silently falling back to stale periods for other tickers.
2. **I hit the 403 path the desk has now logged three times.** `WebFetch` cannot set the Sec-Ch-Ua/Sec-Fetch-*/User-Agent fingerprint, so every `sec.gov` and `data.sec.gov` call failed. I did *not* route to r.jina.ai, since that proxy's truncation is what manufactured the false MFIC finding. I used the company's own IR primary instead and labeled the rest. The bench templates still don't have a path to `desk/sec_fetch.py`.
3. **`knowledge_graph/cohorts.json` is unreadable from `court_tmp`** (permission scope stops at the working dir), so "COHORT: ?" and the narrative were reconstructed rather than read. If the cohort's actual narrative is something other than eVTOL-timeline/burn/dilution, the STRUCTURAL call should be re-run against it — that's the one input that could change the classification.