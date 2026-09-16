Sources came back cleanly enough to classify. Two notes on provenance before the output: **sec.gov returned 403 to every direct fetch this session**, so the filing numbers below are read from StockTitan's rendering of the company release and StockAnalysis's rendering of the statements, not from the EDGAR document itself. And I could not read `knowledge_graph/cohorts.json` (permission denied on the signalos directory), so the cohort/narrative is inferred from the event context, not quoted.

---

FVRR printed Q2 **12 days ago** (6-K, 2026-07-29) and the AI narrative is confirmed on the *volume* axis — but every *unit-economics* metric moved the opposite way, and the market has priced the operating business at an enterprise value of ~$19M.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| FVRR | **DAMAGE-ARRIVING** | (1) annual spend per buyer; (2) >$1,000-project revenue growth by category; (3) GAAP operating income | Spend/buyer **$368, +15.6% y/y**; take rate **27.6%→28.0%**; high-value cohorts **Programming +34%, Graphics +25% y/y** — while buyers fell 21.9% and marketplace rev −15.5% to $63.1M ([company release, 2026-07-29](https://www.globenewswire.com/news-release/2026/07/29/3334963/0/en/Fiverr-Announces-Second-Quarter-2026-Results.html); [6-K Ex-99.1](https://www.sec.gov/Archives/edgar/data/0001762301/000117891326003624/exhibit_99-1.htm)). GAAP op income **+$4.38M vs −$1.99M** a year ago on 10% *less* revenue | **~2026-11-11** (TipRanks; pack said 11-04 via yfinance) — **UNCONFIRMED**, no company PR names it | Damage real on volume, absent on margin/pricing. Magnitude unresolved: CFO guided "**at least six quarters**" for the transformation to show |

**Why not STRUCTURAL:** the narrative predicts economic destruction, and the destruction metrics are moving the wrong way for the bear — gross margin flat at 81.7%, take rate *up*, SBC down 42% y/y ($14.06M → $8.22M), GAAP operating income positive and improving, FCF positive in all five trailing quarters. A model being disintermediated does not raise its take rate.

**Why not DAMAGE-ABSENT:** the guide cut is severe and real — Q3 $80–88M (**−26% to −18%** y/y), FY26 $356–372M (−17% to −14%), buyers −21.9%, Writing & Translation −24%. Management named the mechanism (Gemini-in-Google-search compressing organic click-through). That is deterioration, not noise.

**The dispersion the cohort sale ignored — EV, not price:**
- Market cap ~$325M (35.95M sh × $9.04); cash & investments **$308.5M**; total debt **$2.68M** — the $460M convert was **fully repaid in Q4-2025** (total debt $463.56M → $4.16M)
- ⇒ **EV ≈ $19M**, against TTM FCF **$85.6M**, TTM GAAP net income **$30.0M**, and FY26 guided adj. EBITDA **$52–62M**
- SBC-adjusted TTM FCF = $85.6M − $38.8M = **$46.8M** ⇒ EV / SBC-adjusted FCF ≈ **0.4x**
- OCF is *not* float-inflated: Q2 OCF $13.84M ≈ NI $4.47M + SBC $8.22M. User funds (asset) and user accounts (liability) sit roughly matched and outside the cash line, so a shrinking GMV does **not** trigger a large float unwind — the usual melting-ice-cube accelerant is absent here

**Residual I could not close from primary source:** the FY2025 20-F says cash equivalents include "amounts related to payment processing companies," so some fraction of the $308.5M could be commingled with buyer escrow. The FY25 line-item split (Cash $125.2M + STI $157.7M, separate from Other Current Assets $163.3M ≈ user funds) argues it is corporate, and the June-2025 $748.2M − $460M convert ≈ $288M reconciles cleanly to $308.5M today. But I could not open the balance sheet itself. **This is the single load-bearing number and a court must verify it against Ex-99.1 directly.**

**COURT-WORTHY (damage-absent, ranked):**
No member qualifies as strictly damage-absent — FVRR is damage-arriving on volume. Ranking it anyway on axis-split dispersion:

1. **FVRR** — the market is paying ~$19M for a business that earned $30M GAAP over the last twelve months while its worst-hit segment collapsed; the entire bear case now rests not on the business but on whether $308M of cash gets returned or burned, and that is a governance question public filings can adjudicate.

**COURT-WORTHINESS FVRR: 8/10** — bounded downside (net cash ≈ 94% of market cap), a decisive open question (cash encumbrance + capital allocation) that is resolvable from public filings, and a flat book, so the court moves sizing from zero.

**PRINT PROXIMITY: ~2026-11-11 — UNCONFIRMED (TipRanks aggregator; evidence pack's 2026-11-04 is yfinance-derived; no company PR names either). ~62 trading days out; Q2 already printed 2026-07-29, so we are POST-catalyst, not racing one.** No pre-print reconstruction required. Pre-print position guidance is therefore not the binding question — but for completeness: **STARTER**, sized to the governance tail rather than the business tail, because the Q3 guide is already known and ugly while the cash is not yet demonstrably returnable.

---

**Three things a court must break, in order:**
1. **Is the $308.5M unencumbered corporate cash?** Read Ex-99.1's balance sheet for `user funds` / `user accounts` / `restricted` lines. If a material slice is escrow, EV multiplies and the thesis weakens sharply.
2. **Are the >$1k cohort growth rates absolute dollars or share-of-mix?** +34%/+25% came to me via a transcript summary, not the shareholder letter. If they are mix-share, the revenue floor argument collapses.
3. **Does the cash get returned?** Buybacks went $22.5M → $10.0M → $8.0M → **$0** in Q2-26, and the CFO explicitly deprioritized returns in favor of "a strong balance sheet" and opportunistic M&A — with AutoDS, the prior acquisition, already named as underperforming. Trapped cash compounding into bad M&A is the realistic path to the discount being *correct*.

**Not done — flagging rather than silently skipping:** the standing rule to close every analysis with the dashboard update (ledger upsert + edge_classification + entry_plan + scanner re-run + `/api/everything` verify) could not be executed. This session has no Bash tool and read access to `/Users/ajay/exalted/signalos` was denied. The `COURT-WORTHINESS FVRR: 8/10` line above is ≥6 and should auto-escalate to a full red/blue court via the harness's parse, but the ledger write needs a session with filesystem access.

Sources: [Fiverr Q2 2026 release (GlobeNewswire)](https://www.globenewswire.com/news-release/2026/07/29/3334963/0/en/Fiverr-Announces-Second-Quarter-2026-Results.html) · [6-K Ex-99.1](https://www.sec.gov/Archives/edgar/data/0001762301/000117891326003624/exhibit_99-1.htm) · [Fiverr IR](https://www.fiverr.com/news/fiverr-q2-2026-earnings) · [StockTitan release detail](https://www.stocktitan.net/news/FVRR/fiverr-announces-second-quarter-2026-o0quisjjfetp.html) · [Q2 2026 call transcript](https://www.aol.com/articles/fiverr-fvrr-q2-2026-earnings-005842000.html) · [StockAnalysis financials](https://stockanalysis.com/stocks/fvrr/financials/balance-sheet/) · [FY2025 20-F](https://www.sec.gov/Archives/edgar/data/0001762301/000117891326000858/zk2634486.htm) · [TipRanks earnings calendar](https://www.tipranks.com/stocks/fvrr/earnings)