## Context

QNST's FY26 print (8-K 2026-08-06) and 10-K (2026-08-26) both landed **before** this court convened, and they cut against the cohort narrative: revenue accelerated *through* the AI-Overviews transition rather than decaying with the SEO funnel. Two defects in the evidence pack must be corrected first — the tape quote and the XBRL block are both wrong (detail below the table).

**PRINT PROXIMITY: 2026-11-05 — UNCONFIRMED (yfinance-derived; no company PR names it).** No BusinessWire "sets date" release exists yet; the prior-year analog is FQ1 FY26 reported Nov 6 2025, announced Oct 27 2025. That is ~45 trading days out, **not within 5 trading days**, so the print-decisive reconstruction is not triggered. The information events that mattered (8-K 8/6, 10-K 8/26) have already passed.

| ticker | class | refuting metric | current value/trend (cited) | next print date | note |
|---|---|---|---|---|---|
| QNST | **DAMAGE-ABSENT** | Quarterly revenue + adj-EBITDA margin through the AI-Overviews transition (the metric the funnel-shock narrative predicts must decay) | FQ4 FY26 rev **$373.9M, +43% YoY**; Financial Services **$232.3M +24%**, Home Services **$141.6M +88%**; adj EBITDA **$41.4M +87%**, margin **11.1% (+270bp)**; FY26 rev **$1.294B +18%**; FY27 guide **$1.45–1.55B (+16%)** / adj EBITDA **$150–160M (+38%)**. Mgmt: proprietary Google-campaign revenue **>100% YoY** *as AI Overviews reached ~50%+ of searches* ([8-K 2026-08-06, ex-99.1](https://www.sec.gov/Archives/edgar/data/0001117297/000119312526338042/qnst-ex99_1.htm); [10-K FY2026](https://www.sec.gov/Archives/edgar/data/0001117297/000119312526367160/qnst-20260630.htm)) | 2026-11-05 (unconfirmed) | Damage is testably absent, but see the two disqualifiers below — the *thesis's own upside leg* is not in these numbers, and the disintermediation attack has a specific 22–24%-of-revenue target |

### The OpenAI-channel leg: CONFIRMED as real, DISCONFIRMED as material

The court was told to verify actual channel evidence rather than our inference. It exists, from the CEO on the FQ4 call:

> "We are integrated with OpenAI in most of our verticals now, in our two biggest verticals, auto insurance and home services." — Doug Valenti

But the same call kills the near-term sizing case:

> "The platforms themselves, the ad platforms aren't where they need to be yet for us to get big scale out of them, but they will be… we can see a path for those platforms, the LLMs, to being very big new channels of high-quality, high-intent, well-qualified media for our marketplaces."

Corroborated across two independent transcript renderings ([investing.com](https://www.investing.com/news/transcripts/earnings-call-transcript-quinstreet-tops-q4-2026-views-shares-jump-26-93CH-4844642), [Motley Fool via Globe & Mail](https://www.theglobeandmail.com/investing/markets/markets-news/motley/3841076/quinstreet-qnst-q4-2026-earnings-call-transcript/)). **Conclusion: the channel contributes ~nothing to the FY27 guide. It is unpaid optionality, not a driver.** The reason to look at QNST is that the base business is compounding while the tape prices funnel-death; the OpenAI channel is a free call on top. Do not size the channel.

### The red attack that survives — and it is specific

Disintermediation is not abstract here, it has a named target: **one client = 24% of net revenue in FQ3 FY26 and 22% for the nine months** ([10-Q 2026-03-31](https://www.sec.gov/Archives/edgar/data/0001117297/000119312526213979/qnst-20260331.htm); FY25 was 23% + 12%). Client contracts are cancelable with little or no notice and carry no cancellation penalty. If that single carrier builds direct conversational-ad buying, roughly a quarter of revenue is the loss-given-event — and Valenti's own bull line ("Carriers are in an exceptionally good financial position… really hungry for demand") is a *cyclical* underwriting-cycle tailwind that reverses, layered on top of the structural question.

Two further unresolved items, flagged not papered over:
- **Organic vs acquired growth is unverified.** Home Services +88% substantially reflects HomeBuddy (closed 2026-01-02); FY27's +16% laps a partial year. I could not extract the organic split — SeekingAlpha 403'd.
- **FY26 GAAP EPS $1.40 is flattered by a tax benefit** (valuation-allowance release). Use EBITDA/OCF, not GAAP EPS.

Valuation on corrected inputs: $19.44 × 57.09M sh = **$1.11B** cap; +$77.7M debt −$128.3M cash ⇒ EV ≈ **$1.06B** ⇒ **~6.8× FY27 EV/EBITDA guide-mid**, ~8.1× FY26 EV/OCF.

### Two evidence-pack defects — correct before any price gate

1. **Tape is wrong.** Pack says `px 17.535, dd52 -0.213`. Actual last close is **$19.44, Aug 31 2026 4:00pm EDT** ([stockanalysis.com](https://stockanalysis.com/stocks/qnst/)) — the pack quote is **9.8% low**, consistent with a thin pre-market print at the 12:51Z build time. True dd52 is **−12.8%**, not −21.3%. Any band or tripwire set off 17.535 is mis-specified. I could not re-poll IBKR directly (`search_contracts` permission not granted).
2. **XBRL block is unusable.** The pack's revenue rows are 2012–2014 quarters, and `ocf 2024-09-30 = −$13,706,000` contradicts FY26 OCF of **+$131.3M**. The instruction to "use THESE for SBC/share/OCF math" would produce garbage. Mis-framed extraction.

Separately: the eight Form 144s in three weeks look alarming and are **not** a signal — CEO Valenti's 751,631 sh @ $20.00–20.91 (8/7, $15.4M) and 84,595 @ $22.02 (8/10) are reported as executed under a **10b5-1 adopted 2024-09-06** / tax-withholding on vesting; CFO Wong sold 11,704 @ $20.40–20.50 on 8/18. Programmatic, pre-scheduled. Recording the anti-masking finding as a positive. (Form 4 primaries not opened — sec.gov 403'd WebFetch throughout, the known fingerprint issue; all SEC-hosted figures above are relayed via search rather than directly read.)

**COURT-WORTHY (damage-absent, ranked):**
1. **QNST** — the only member, and it qualifies: revenue accelerated +43% through the exact transition the cohort narrative says should have broken the funnel, yet the tape holds it at 6.8× FY27 EV/EBITDA guide with insiders' 10b5-1 prints clustered $20–22 above the current $19.44.

**COURT-WORTHINESS QNST: 7/10** — sizing hinges entirely on one resolvable pre-print question (whether the 22–24% single client is building direct AI-channel buying) plus the unextracted organic-vs-HomeBuddy split, so a court materially moves the decision even though the OpenAI leg itself is confirmed immaterial to FY27.

Score ≥6 → auto-escalates to full red/blue court. Two things the court must inherit: **do not size the OpenAI channel** (management says it lacks scale), and **re-poll the tape** — the pack's 17.535 is a bad quote.

Sources: [8-K FY2026 ex-99.1](https://www.sec.gov/Archives/edgar/data/0001117297/000119312526338042/qnst-ex99_1.htm) · [10-K FY2026](https://www.sec.gov/Archives/edgar/data/0001117297/000119312526367160/qnst-20260630.htm) · [10-Q 2026-03-31](https://www.sec.gov/Archives/edgar/data/0001117297/000119312526213979/qnst-20260331.htm) · [FQ4 transcript (investing.com)](https://www.investing.com/news/transcripts/earnings-call-transcript-quinstreet-tops-q4-2026-views-shares-jump-26-93CH-4844642) · [FQ4 transcript (Globe & Mail)](https://www.theglobeandmail.com/investing/markets/markets-news/motley/3841076/quinstreet-qnst-q4-2026-earnings-call-transcript/) · [stockanalysis.com QNST](https://stockanalysis.com/stocks/qnst/) · [MarketBeat CEO Form 4](https://www.marketbeat.com/instant-alerts/insider-selling-quinstreet-nasdaqqnst-ceo-sells-751631-shares-of-stock-2026-08-11/) · [Investing.com CFO Form 4](https://www.investing.com/news/insider-trading-news/quinstreet-cfo-gregory-wong-sells-239229-in-stock-on-august-18-93CH-4866215)