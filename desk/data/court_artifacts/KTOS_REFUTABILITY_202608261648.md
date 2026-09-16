## KTOS — Refutability Triage

Cause-check first: the cohort's implied "damage" narrative is **not** in KTOS's numbers — the company beat and *raised* on 2026-08-04 — but the -60.6% drawdown is a multiple round-trip from a Feb-2026 blow-off, and the pack's `excess_dd -0.367` is measured against the wrong anchor (Industrials median), not against the actual peer cohort where AVAV is down *more*.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| KTOS | **DAMAGE-ABSENT** (operating) / price gate open | FY26 organic revenue growth + book-to-bill + guide direction | Q2'26 rev **$458.8M, +30.5% y/y, +19.1% organic**; B2B **1.1x** Q / **1.3x LTM**; backlog **$2.084B**; FY26 guide **raised** to $1,750–1,810M (from ~$1.73B mid); Q3 guide $460–480M (+19–25% organic) — [company PR, 2026-08-04](https://www.kratosdefense.com/newsroom/kratos-reports-second-quarter-2026-financial-results) | 2026-11-03 (UNCONFIRMED) | No guide cut, no disclosure withdrawal, no metric deterioration. Damage is testably absent. |

**Cause-check verdict — this is beta-bleed, not dislocation.** Nearest peer AVAV: $417.86 → $146.99 = **-64.8% dd52**, a *deeper* drawdown than KTOS's -60.6%. RCAT, ONDS all de-rated on the same 2026 unwind of defense/drone growth multiples. KTOS is mid-pack in its real cohort; the -0.367 "excess" is an artifact of benchmarking a name that 3x'd into the melt-up against an Industrials median that never participated. Per the artifact taxonomy, there is no same-event external anchor showing dispersion the market ignored.

**The named objection (a price gate, not a kill).** Two facts the beat-and-raise headline hides:
- **Dilution wedge.** Diluted shares **157.4M → 190.1M**, +20.8% y/y (prior-year figure from the pack's own XBRL `dil_sh 2025-06-29`). Revenue *per diluted share* is **$2.23 → $2.41, +8.0%** — not +30.5%. Growth is substantially bought, not earned: the Feb-2026 raise sold **14,285,714 shares** off an $88.23 reference price ([424B5](https://www.sec.gov/Archives/edgar/data/1069258/000162828026012874/kratos-final424b5.htm)) — 67% above today's $52.75.
- **Negative FCF.** FY26 guided OCF $30–50M against capex $125–135M → **FCF of −$85M to −$105M**.

At $52.75: mcap $9.90B, net cash **$1,244M** ($1,438M cash vs $193.6M total debt) → **EV ≈ $8.66B = 4.9x FY26 sales, ~49.6x FY26 adj. EBITDA** ($173–176M). On 2027 (guide: +100bps margin, ~$2.1B rev → ~$227M EBITDA), today is ~38x. The drawdown moved this from absurd to merely expensive.

**COURT-WORTHY (damage-absent, ranked):**
1. **KTOS** — the only member, and it qualifies on the operating axis only: a beat-and-raise with 1.3x LTM book-to-bill, a $15.0B bid pipeline, and 12.6% of market cap in net cash with no net debt is genuinely divergent from a 60% drawdown. But the dispersion-vs-cohort test *fails* (AVAV fell further), discovery_state is **CROWDED** — this is among the most-retail-discussed defense names, with five Form 144s in the last 30 days plus insider Form 4 sales on 8/17–8/20 marking the informed side as a seller — and the residual objection is valuation, which by doctrine yields a price gate rather than a kill.

**Price gate (the actionable output):** FLAT above ~$46. Entry becomes attractive at **$42–46**, i.e. ~30–33x 2027E EBITDA, which sits on the $43.09 52-week low — only 18% below spot, so this is a live gate, not a theoretical one. Size at starter on a tag, funded by the fact that the balance sheet fully funds the capex build without another raise.

**PRINT PROXIMITY: 2026-11-03 — UNCONFIRMED (yfinance-derived; no Kratos PR names the date, and their Q3 releases have historically landed in early November). ~48 trading days out, well beyond the 5-day window, so the print-decisive reconstruction is not triggered.** Pre-print stance is therefore the standing gate above, not a catalyst race; the Q3 checkpoint is whether the $460–480M / 19–25% organic guide holds without further share issuance.

**COURT-WORTHINESS KTOS: 5/10 — operating damage is genuinely absent, but the peer tape kills the dislocation premise and the sole remaining objection is a valuation price gate that a court would not move.**

Two data-integrity notes for the pipeline: the evidence pack's XBRL quarterly block is unusable for current math — the `rev` series ends in **2013** and `ocf`/`sbc` end in 2025; only `dil_sh` was current enough to cite. And one secondary reported the 52-week low as $39.00; IBKR gw and stockanalysis agree at **$43.09**, which I used.

Sources: [Kratos Q2 2026 PR](https://www.kratosdefense.com/newsroom/kratos-reports-second-quarter-2026-financial-results) · [424B5 offering](https://www.sec.gov/Archives/edgar/data/1069258/000162828026012874/kratos-final424b5.htm) · [KTOS quote/balance sheet](https://stockanalysis.com/stocks/ktos/) · [AVAV quote](https://stockanalysis.com/stocks/avav/) · [drone-sector selloff](https://247wallst.com/investing/2026/08/18/drone-stocks-see-limited-losses-tuesday-during-nasdaq-sell-off-red-cat-ondas-flat-while-aerovironment-tumbles/) · [Aug-20 move](https://www.tradingkey.com/news/market-movers/262121897-market-movers-ktos-20260820)

*Caveat on inputs: `knowledge_graph/cohorts.json` was not readable from this session (path outside the granted directory), so COHORT and the named NARRATIVE arrived as literal `?`. I reconstructed the narrative from the tape as the 2026 defense-tech/drone multiple de-rating and stated it as a reconstruction; if the actual cohort definition names a different mechanism, the cause-check above should be re-run against it. Bash and the IBKR snapshot tool were both unavailable, so tape facts rest on the pack's ibkr_gw values plus an independent secondary that agrees.*