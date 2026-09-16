### WIE.VIE (Wienerberger AG — bricks/roof tiles/piping; infra+renovation now >60% of revenue) — screen: RISK_PREMIUM band-hit, ~5.4x EV/EBITDA, 4.5% yield — **BORDERLINE (lean NO-ENTRY; band RETIRED, not re-based) — resolves on the 2026-08-12 print**

**KILL FACTS**
- **The band fired on a catalyst the screen never saw.** Ad-hoc profit warning **2026-07-21**, 22 days *after* the 6/29 screen: FY26 operating EBITDA cut **€810m → ~€700m**; shares −6%+, 52-wk low €19.92 on 7/24 ([primary PDF](https://www.wienerberger.com/content/dam/corp/corporate-website/downloads/press-releases/2021-2030/2026/20260721_PA_wienerberger_Trading-Update_Q2.pdf)). The band was hit *because* the thesis's own gate failed — textbook adverse selection, same shape as today's FNF stale-band fill.
- **The disclaimed-recovery gate moved the wrong way.** Verbatim: recovery "did not materialize"; "taking longer to materialize than initially anticipated"; "remain subdued over the coming quarters"; and *"we have not seen any material government support programs or stimulus measures"* across the footprint. Not neutral — worse.
- **Organic earnings are deteriorating behind the M&A screen.** Q2 revenue +13% to €1.41bn but EBITDA €230m vs €253m; scope (Italcer/NEWS) added **>€16m** → organic Q2 EBITDA ≈ €214m, **−15% yoy**, margin 16.3% vs 20.2%. H1 26 = €97m + €230m = **€327m** vs H1 25 €383m.
- **Leverage arithmetic is the unpriced risk.** Net debt ~**€2,037m** post-Italcer, YE26 target 2.2x — computed on €810m. On €700m that is **2.9x**; hitting even 2.5x needs a ~€290m net-debt cut in H2 while paying a ~€104m dividend. UNVERIFIED at 6/30 — it prints tomorrow.
- **Not an orphan — fair-carry exemption does not apply.** 9 analysts; Erste→Accumulate (PT €24.20), Citi→Neutral (€22), UBS Sell (€18), Berenberg Buy (€25).

**SCREEN DEFECT TO FILE — new family (6) "guidance-superseded basis":** the screen's forward denominator was *withdrawn by the issuer* after the screen date. Corrected: EV ≈ €4.37bn (109.2m × €21.30 + €2.04bn ND, **excl. Italcer NCI — EV understated**) → **6.2x EV/EBITDA on €700m, not ~5.4x**. None of the five known families covers this.

**LIVE FACTS**
- Business is cyclical, **not melting**: +7% organic revenue, piping €1.4bn, roofing €1.2bn, >60% infra/reno.
- €700m implies H2 ≈ €373m vs H2 25 €371m — flat, but only because ~6 months of Italcer/NEWS scope funds the **€60m residual** residential drag (€100m total, €40m in H1). Zero cushion; base business does none of the work.
- Liquidity/structure clean: ATX mid-cap, ample ADV for a starter, no PFIC. Austria WHT 27.5% → 15% treaty for US holders (reclaim for the excess) — 4.46% gross yield is ~3.8% net; carry case is thinner than screened.
- Tape web-sourced (**€21.30 last, −31.9% YTD, 20% below 200dma**); **IBKR was not authorized this session** — live quote, positions and resting orders are UNVERIFIED against the broker.

**RESOLVES ON:**
- **2026-08-12 (T-1, tomorrow, 12:00 CET):** final H1 — the three numbers that decide this are **net debt / leverage ratio**, H2 phasing of the €60m residual, and any quantified Fit for Growth savings.
- **2026-11 (Q3):** first read on whether US/CA/UK new-build has troughed (Citi: "the trough has yet to be reached").
- **Feb 2027 (FY/CMD):** dividend decision if leverage lands >2.5x.

**Disposition: WATCH + tripwire — do NOT advance to court today, and retire the band outright.** The band's levels were not supplied in the pack; they are void regardless, being derived from a June world with an €810m denominator the issuer has since withdrawn. Courting a state that is superseded in under 24 hours burns the court. **No order rests.** Re-court on 8/12 post-print, gated on leverage ≤2.5x and evidence the H2 bridge is scope-plus-price rather than hope; if leverage prints ≥2.8x, this converts to AVOID until the balance sheet is repaired.

Sources: [Trading Update Q2 2026 (primary)](https://www.wienerberger.com/content/dam/corp/corporate-website/downloads/press-releases/2021-2030/2026/20260721_PA_wienerberger_Trading-Update_Q2.pdf) · [Q1 2026](https://ca.investing.com/news/company-news/wienerberger-q1-2026-slides-weather-hits-volumes-margins-compress-93CH-4633068) · [profit warning](https://www.investing.com/news/earnings/wienerberger-shares-tumble-as-brickmaker-cuts-profit-guidance-4802124) · [downgrades](https://www.ad-hoc-news.de/boerse/news/unternehmensnachrichten/wienerberger-s-profit-warning-triggers-analyst-downgrades-as-housing/69896989) · [quote](https://stockanalysis.com/quote/vie/WIE/) · [IR](https://www.wienerberger.com/en/investors/latest-results.html)

---

Two things I could not complete, flagged rather than papered over:

1. **IBKR MCP is unauthorized in this non-interactive session** — `search_contracts`, `get_price_snapshot`, `get_account_positions` and `get_account_orders` were all denied. So "NO POSITION / NO ORDERS" comes from the evidence pack, not a live poll, which is exactly the check the standing rule requires before any held/order claim. Authorize the connector in claude.ai settings to close this.
2. **The band's numeric levels were not in the pack**, so I could not test how far the touch was from the pre-warning reference. It doesn't change the verdict — the band is void on the guidance-supersession alone — but a re-derived band post-print needs those inputs.

I also did **not** perform the dashboard closing step (ledger upsert, edge_classification, entry_plan, scanner re-run, `/api/everything` verify) — this ran as a court-tmp verification with no write instruction, and the disposition is "retire the band, no order rests." Say the word and I'll push the retirement plus the new defect-family (6) entry into the ledger and re-run the scanner.