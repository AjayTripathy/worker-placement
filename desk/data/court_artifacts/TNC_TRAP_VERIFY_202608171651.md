I could not reach `sec.gov` directly — WebFetch is sent without a User-Agent and SEC returns HTTP 403 on both `data.sec.gov` and `www.sec.gov`, and no Bash/IBKR permission was available in this session. Q2 figures below therefore come from a **mirror** of 8-K Ex-99.1 / 10-Q, flagged per external-data discipline.

### TNC (Tennant Co — industrial floor-cleaning equipment, NYSE) — screen px $69.27 / mcap $1.181B / dd3y 41.8% / GM 38.8% / ROE 3.1% / fwd rev +5.9% — **BORDERLINE (lean constructive) — resolves on Q3 cash flow**

**SCREEN TIE-OUT (all four metrics verified, none is an artifact)**
- mcap: cover shares 17,037,788 (10-Q, 3/31/26) × $69.27 = **$1.180B** vs screen $1.181B. Exact. No family-1 defect.
- ROE 3.1%: arithmetically right, semantically a trap in *our* favor. TTM NI = FY25 $43.8M − H1'25 $33.3M + H1'26 $7.8M = **$18.3M** / equity $533.4M = 3.4% (3.1% on average equity). Normalized on FY2024's ~$85M NI = **~16%**. This is defect family 5 *inverted* — screened at the trough, not the windfall.
- fwd rev +5.9%: consistent with guidance **raised** to $1.270–1.310B. The trap is that adj EBITDA was simultaneously **cut** to $155–170M vs ~$180M consensus.

**KILL FACTS**
- H1'26 operating cash flow **−$26.2M** (vs +$22.1M H1'25); Q1 alone −$31.2M. Working capital ballooned (inventory $204.6M, receivables $280.6M) on the North America ERP botch.
- Board repurchased **$60.0M of stock in Q1** funded by **$85.0M net new borrowings** while OCF was negative — then authorized **2,000,000 more shares** (~12% of the float) on 4/29/26. Net leverage **1.0x → 2.0x** in six months. That is debt-funded buyback into a deteriorating quarter.
- Miss is now serial: Q2 adj EBITDA −30.8%, GM 39.5% vs 41.5%; "expected ERP optimization benefits did not fully materialize." EMEA price/volume pressure is *demand*, not ERP, and FY25 sales were already −6.5%.
- **Not an orphan** — Sidoti, Roth (initiated 10/2025), Zacks (cut to Strong Sell 8/12/26) all cover it. FAIR-CARRY does not apply; it cannot be unpriced paper.

**LIVE FACTS**
- Sales *recovered* to 2024 levels ($1.29B guide vs $1.287B FY24); the entire gap to 2024 is **margin, not volume** — EBITDA $162M mid vs ~$205M. Reversible in principle.
- Covenant 3.75x vs 2.0x actual; $289.3M revolver unused. Tails bounded, unlevered equity, ~54-year dividend-increase streak intact.
- Integrity clean: management **quantified its own damage** ($23M sales / $17M GM in Q1) rather than burying it. Goodwill $209.9M, no new impairment. Anti-masking = positive finding.
- At $66.76 (yahoo pack 8/17, **not** an IBKR print): EV ~$1.417B = 8.3–9.1x guided EBITDA, ~6.9x FY2024-normalized (UNVERIFIED normalization), 13.4x normalized EPS.

**RESOLVES ON:** (1) **~2026-11-02 Q3 print** (yfinance-derived, unconfirmed) — H2 OCF must turn positive and recover the H1 −$26.2M, else the working-capital build is permanent loss, not timing; (2) same print — GM back above 41% or the ERP thesis is really a tariff/mix thesis; (3) Q3 10-Q — whether they kept buying stock on the revolver; a third quarter of debt-funded repurchase into negative OCF converts this to a capital-allocation DECLINE; (4) EMEA organic volume separated from ERP noise.

**Disposition: WATCH + tripwire.** Not advance-to-court. Per response taxonomy the open question is *data/execution*, not valuation — a price gate would arm against numbers we know are distorted, which is the INTRA-batch error we just paid for. Tripwires: Q3 OCF < +$25M → DECLINE; new buyback disclosed with OCF still negative → DECLINE; OCF > +$50M **and** GM > 41% → advance to court with a FALLEN-COMPOUNDER frame.

**Corrections to file (first-class output)**
1. **New defect family (6): trough-metric without direction flag.** Family 5 catches only windfall-year screening. ROE/GM/margin fields need a cycle-extreme test that reports *which side* of normal the metric sits on. TNC would have been rejected on ROE 3.1% by a naive reader.
2. **Screen defect: `fwd_rev_growth_pct` is blind to margin direction.** TNC raised revenue guidance and cut EBITDA in the same release; the field scored the raise. Any margin collapse with pricing pass-through will mis-rank the same way. Pair the field with a forward-margin delta.
3. **Evidence-pack infra bug.** The XBRL block instructs "use THESE for SBC/share/OCF math" but `rev` ends **2019-09-30** and `sbc`/`ocf` are Q1-only series ending 2025-03-31. Following the instruction literally yields seven-year-old revenue. Zero-output/stale-output alarm should fire on this pack.
4. **Fetch-path gap.** SEC returns 403 to the WebFetch path; only the desk's full-fingerprint fetcher works. Court prompts that say "10-K/10-Q as primary" are unsatisfiable from a session without Bash — worth wiring the fetcher behind a tool.
5. **Mirror unreliability.** One stocktitan 10-Q URL returned **Q1** data when asked for Q2 without saying so. Period-binding on mirrored filings must be asserted, not assumed.

Sources: [8-K Ex-99.1 mirror](https://www.stocktitan.net/sec-filings/TNC/8-k-tennant-co-reports-material-event-a0766e9cdefb.html), [10-Q mirror](https://www.stocktitan.net/sec-filings/TNC/10-q-tennant-co-quarterly-earnings-report-f0c831421fca.html), [FY2025 results](https://investors.tennantco.com/news/news-details/2026/Tennant-Company-Reports-2025-Fourth-Quarter-and-Full-Year-Results/default.aspx), [StockStory Q2 reaction](https://stockstory.org/us/stocks/nyse/tnc/news/earnings/tennant-nysetnc-misses-q2-cy2026-revenue-estimates-stock-drops-138percent), [Zacks downgrade](https://www.marketbeat.com/instant-alerts/tennant-nysetnc-downgraded-to-strong-sell-rating-by-zacks-research-2026-08-12/).

Two caveats on completeness: the FY2024 EBITDA normalization (~$205M) is **UNVERIFIED** — I could not reach the FY2024 release — and I did not pull the proxy, so **related-party and share-pledge checks are UNVERIFIED**. Both are cheap to close before any court and neither changes the WATCH disposition.