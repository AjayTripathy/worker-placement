Bash and Write are both disabled here, so this is research-and-report only — I couldn't persist the doctrine memory or touch the queue file. Flagging that at the end.

---

**Context:** CMTG's Q2 print (7/29/26) cut BVPS to $8.58 and the stock now trades $1.555 = **0.18x book**; the 8/27 band gate and subsequent slide to new lows decompose to a *0.4pp* change in implied severity, while the only genuinely new input is macro (30y at a 19-year high), not company disclosure — there has been **zero company disclosure since the 8/10 Form 4**.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| CMTG | **DAMAGE-ARRIVING** | Realized resolution severity (cents-on-dollar on resolved UPB) vs. booked reserve — 16.9% blended / 32.0% specific on RR5 | Reserve $567.4M = **16.9% of UPB** (32.0% specific on RR5, 2.9% general); Q2 provision $208.8M ($1.45/sh); BVPS **$10.69 (YE25) → $10.33 (Q1) → $8.58 (Q2)**; four loans / $447M UPB newly downgraded to RR5 in Q2; 2026 YTD $1.0B UPB resolved — 43% full repayment, 31% sale below par, 10% foreclosure, 7% DPO; SF office loan sold at **63c**. Mgmt declines a book floor: "more asset resolutions are needed before the bottom becomes clear." ([10-Q](https://www.sec.gov/Archives/edgar/data/0001666291/000119312526323733/cmtg-20260630.htm), [8-K ex99.1](https://www.sec.gov/Archives/edgar/data/0001666291/000119312526323745/cmtg-ex99_1.htm)) | **2026-11-04 — UNCONFIRMED** (yfinance-derived; no company PR names it) | Damage is unambiguously *arriving*, magnitude unresolved — not absent, not purely structural (43% of resolutions still pay at par). Binding constraint is the **TNW covenant**, not the discount: floor = **$1.0B + 75% of post-1/30/26 equity proceeds** (≈$1.0B flat; no equity issued), vs. equity $1.21B common / $1.24B total → headroom **~$210–240M against $247M of Q2 book burn**. In compliance at 6/30/26. |

**COURT-WORTHY (damage-absent, ranked):** **NONE.** No member qualifies as DAMAGE-ABSENT. CMTG's predicted damage is present and measurable in the reported numbers (−$1.75/sh of book in one quarter, four fresh RR5 downgrades, $723.7M REO), so the dispersion-vs-cohort trade does not apply here.

### The arithmetic that answers the queue's question

Equity is a ~6% sliver of the asset base, so price percent is the wrong unit:

- Risk assets at carry = $2.8B loans + $723.7M REO = **$3.524B**; common equity = $8.58 × 141.08M = **$1.2105B**; market cap = **$220.1M**.
- Market-implied *further* loss = $1,210.5M − $220.1M = **$990.4M = 28.1%** on everything at current carry (≈38.2% cumulative off gross UPB+REO).
- At the 8/27 gate price of $1.655 the same math gives **27.7%**.
- **Gate → now = +0.4pp of implied severity.** The 6.0% price slide equals a **0.37% change in implied asset marks.**

### Branch adjudication

**(a) Forced/mechanical flow — DROPPED, no seller can be named.** Dividend was paused 12/16/2024, so the income-fund exit is 20 months stale. Russell deletion is annual (June recon, already past). NYSE tests both untripped: $1.555 vs the $1.00/30-day standard, $220M cap vs the $50M standard. MORT/REM weights are proportional, not a cliff. Tax-loss window hasn't opened. The Jan-2026 HPS refi pushed the corporate maturity to **January 2030**, removing the one real maturity wall. Per the hard rule, the claim fails.

**(b) NEW information — real but macro-only, and already 0.4pp-sized.** The long-end rout is genuine and dated: 30y hit 5.31–5.34% mid-August, highest since 2007, and entered September on its worst stretch since 2006. Mack gave the transmission channel on 7/29 — cap rates rise "if interest rates continue to go up." But the company has disclosed nothing since 8/10, and the price move corresponds to 0.4pp of severity. The rout is a live forcing variable for the *9/30 covenant test*, not an explanation of the bleed.

**(c) Crowded-exit beta — rejected.** Peers aren't collapsing: 1-yr total return at 8/25/26 was BXMT −20.0%, LADR −5.0%, ARI **+9.5%**, against CMTG −61% off its 52w high. This is idiosyncratic drift, not cohort beta.

**Synthesis:** none of the three. The bleed is **absence of a marginal buyer** in a levered stub — dividend suspended with no timeline, no buyback authorized ("potential use," no commitment), no internalization (not discussed on the call), no new originations until "latter part of 2026 and early 2027," Street at Sell / $2.22 average target. The 8/10 verdict stands, but its stated reason ("no re-rate mechanism") should be replaced: there *is* now a dated mechanism, and it points **down** — the $1.0B TNW covenant, tested 9/30/2026, with under one quarter of Q2-magnitude loss in headroom.

**Decisive unverified variable (would flip the covenant conclusion):** whether the TNW definition adds back the CECL allowance or excludes unrealized marks, as many mREIT credit agreements do. If it does, headroom is far larger and the truncation risk mostly dissolves. I could not read the covenant definition itself — sec.gov returned HTTP 403 to every direct fetch, so the covenant text above came via the search index over `cmtg-20260630.htm` rather than my own read of the document. That is the one item worth resolving before Q3.

**COURT-WORTHINESS CMTG: 4/10** — book is NO POSITION / NO orders and the new covenant finding argues for staying flat, so a full court cannot change a sizing decision that is already zero.

**PRINT PROXIMITY: 2026-11-04 — UNCONFIRMED (yfinance-derived; no company PR or 8-K names the date; ~45 trading days out, well outside the 5-day window).** No print-decisive reconstruction required. Pre-print position: **FLAT** — the equity is a near-the-money option on resolution severity with a quarterly covenant knock-out, and you are not paid to own the truncated side of that before the 9/30 test is disclosed.

### Recommended queue actions (not executed — Bash/Write disabled)
1. **Retire the price band.** A percent band on a 0.18x-book stub with ~16x gearing to asset marks manufactures noise gates; this one cost a court cycle to answer "nothing changed."
2. **Replace with a covenant-headroom gate:** re-court if TNW < $1.10B (≈$210M → $100M headroom halved) or BVPS < $7.80, read at the Q3 filing.
3. **Resolve the TNW definition** (CECL add-back?) from the credit agreement exhibit — needs a fetcher with a real User-Agent, since WebFetch is 403'd on sec.gov.
4. Keep the standing "internalization/buyback → immediate re-court" trigger; neither has occurred.

I drafted a doctrine memory on levered-stub gate mis-specification (convert price moves to implied asset-mark deltas before treating them as information) but **could not save it** — the Write tool is disabled this session. Worth re-issuing when writes are available.

Sources: [Q2 2026 10-Q](https://www.sec.gov/Archives/edgar/data/0001666291/000119312526323733/cmtg-20260630.htm) · [Q2 2026 8-K ex99.1](https://www.sec.gov/Archives/edgar/data/0001666291/000119312526323745/cmtg-ex99_1.htm) · [Q2 slides coverage](https://www.investing.com/news/company-news/claros-mortgage-q2-2026-slides-show-255m-loss-portfolio-cleanup-93CH-4825601) · [Q2 call transcript](https://www.investing.com/news/transcripts/earnings-call-transcript-claros-mortgage-trust-posts-q2-2026-loss-shares-fall-93CH-4825272) · [Feb 2026 HPS term loan call](https://www.fool.com/earnings/call-transcripts/2026/02/19/claros-mortgage-cmtg-earnings-call-transcript/) · [30y yield 19-year high](https://www.cnbc.com/2026/08/18/treasury-yields-.html) · [30y worst stretch since 2006](https://www.bloomberg.com/news/articles/2026-09-01/us-30-year-bond-enters-september-on-its-worst-stretch-since-2006) · [CMTG quote/shares](https://stockanalysis.com/stocks/cmtg/) · [Dividend history](https://stockanalysis.com/stocks/cmtg/dividend/)