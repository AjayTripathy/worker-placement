## Context

JMIA is a **single-member cohort event** here, and one caveat up front: `knowledge_graph/cohorts.json` was permission-denied to this session, so the cohort's stated narrative is **inferred** from the event blob (Consumer Discretionary / Catalog-Specialty Distribution, dd52 −0.592, excess −0.39) as *"unprofitable frontier e-commerce, demand destruction + cash-out risk."* Also flagging: the IBKR `get_price_snapshot` call was permission-denied, so the tape below is the pack's Yahoo mark ($6.23), **not** a live IBKR pull — the standing live-price rule is unmet for this run. The sweep dated 2026-08-11 measured the drawdown **one day before** the 08-12 print + raise, which materially changes the read.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| JMIA | **DAMAGE-ARRIVING** | FY26 adj-EBITDA loss vs. the **held** $25–30M envelope (H1 already $19.4M) — and perimeter-adj GMV growth vs. the **cut** 20–30% FY guide | Adj EBITDA loss $8.7M in Q2, −36% YoY; H1 $19.4M, −34% YoY. GMV +20% (+23% adj) to $216.3M; QAC 2.6M +21%; orders 6.3M +26%. **FY GMV guide cut 27–32% → 20–30%; Q3 guided 15–25%** ([Q2 release, 2026-08-12](https://www.accessnewswire.com/newsroom/en/computers-technology-and-internet/jumia-reports-second-quarter-2026-results-and-announces-capital-r-1206388); prior guide reaffirmed at Q1: [Q1 release](https://www.accessnewswire.com/newsroom/en/computers-technology-and-internet/jumia-reports-first-quarter-2026-results-1164412)) | ~2026-11-11 — **UNCONFIRMED** (yfinance-derived; pattern-consistent with 05-07 and 08-12, no company PR names it) | Demand leg is damage-**absent** (customers/orders/GP all accelerating, GM 52.6%→59.0%); damage is isolated to high-value electronics on an exogenous memory/CPU shortage. Guide cut = the disqualifying fact for DAMAGE-ABSENT under R2.3. |

**Why not DAMAGE-ABSENT:** the prompt names guide cuts as a DAMAGE-ARRIVING marker, and Jumia cut FY GMV at the print. Profitability improving does not rescue the classification.

## The quantified crux a court would adjudicate

Management **cut the GMV guide but held the $25–30M FY adj-EBITDA loss guide**. Those two moves are in tension, and the arithmetic is checkable from public filings:

- 2025 quarterly adj-EBITDA loss: Q1 $15.7M, Q2 $13.6M, **Q3 $13.9M (derived)**, Q4 $7.3M → FY $50.5M ([FY2025 release](https://investor.jumia.com/news/news-details/2026/Jumia-Reports-Fourth-Quarter-and-Full-Year-2025-Results/default.aspx)). H2-2025 = $21.2M.
- 2026: Q1 $10.7M (derived), Q2 $8.7M → H1 $19.4M, **−34% YoY**.
- FY guide $25–30M ⇒ **H2-2026 = $5.6–10.6M**, i.e. **−50% to −73% YoY** — the improvement rate must roughly **double** versus the 34% H1 actually delivered, while the GMV that funds that operating leverage was just guided **down** and supply volatility "persists into early Q3."
- Sequential pace is $2.0M/qtr (Q1→Q2). Extrapolated: Q3 $6.7M, Q4 $4.7M — **not breakeven**. Q4 breakeven requires the 2025-style seasonal step (Q3→Q4 was −$6.6M last year on peak GMV) to repeat *and* opex to stay flat.

That is a real mechanism, not a fantasy — but it is a tight claim with one named failure mode, and the market marked the stock **+7.7% to $6.255** on the print ([MoneyCheck](https://moneycheck.com/jumia-jmia-stock-jumps-8-on-strong-q2-earnings-and-50m-ifc-investment)), reading "loss −36% + IFC anchor" without pricing the H2 requirement.

**The second decisive datum cuts against buying here:** the best-informed marginal buyer — the IFC, a World Bank affiliate with full diligence access and an ESG/policy covenant package — agreed to $5.52/ADS on 08-12 (6-K 0001756708-26-000025, evidence pack). The tape at $6.23 is **12.9% above** that clearing print, with the raise **not yet closed** (2H-August) and registration rights granted to certain Other Investors. Per the fairly-paid-risk bar, fairness is *verified* at $5.52 — not at $6.23.

## COURT-WORTHY (damage-absent, ranked)

**None.** JMIA does not qualify — it is DAMAGE-ARRIVING on a same-print guide cut. It is nonetheless *court-worthy* on the information-value test, for a different reason: the crux above is quantified, falsifiable from filings already public, and the two benches are evenly matched (balance sheet just de-risked to ~$96M pro-forma liquidity vs. a $25–30M FY loss envelope, growth exogenously impaired, informed-buyer price *below* the tape). A court most likely converts "not on the radar" into a **price-gated stance at/below the IFC clearing print**, which is a genuine sizing change from a zero baseline.

**PRINT PROXIMITY: NONE within 5 trading days — next print ~2026-11-11, yfinance-derived and UNCONFIRMED (no company PR names it; consistent with the 05-07 / 08-12 cadence). The print-decisive reconstruction is therefore not triggered.**

One dated event *does* land inside the window and I'm treating it as the analog: **the $50M raise closes in the second half of August 2026** — ~9.06M new ADSs (**~7.4% dilution**; share count from a low-confidence secondary, ~119–124M ADS, so treat the exact percentage as approximate) hit the register at $5.52 with registration rights attached. **PRE-EVENT POSITION: FLAT.** The stock trades 12.9% above the price the most-diligenced buyer paid one week ago, the closing adds supply into that gap, and the guide that would justify paying up is the one carrying the unresolved H2 arithmetic — there is no reason to pay $6.23 ahead of an event that mechanically pulls toward $5.52.

**COURT-WORTHINESS JMIA: 6/10 — held EBITDA guide requires an H2 improvement ~2× the H1 delivered while the growth guide was cut, and the tape sits 12.9% above a verified informed-buyer clearing price with the raise still open.**

---

**Pending closing step, not executed:** the standing rule is ledger upsert + edge_classification + entry_plan + scanner re-run + `/api/everything` verification. I could not complete it — `Grep`/`Glob` over `/Users/ajay/exalted/signalos` and the IBKR MCP calls were both permission-denied in this non-interactive session, so I have neither the ledger schema nor a live price to write. Grant read access to the repo (and the IBKR tool) and I'll do the upsert with a live IBKR mark rather than the Yahoo pack value.