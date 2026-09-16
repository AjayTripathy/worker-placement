### FLEX (Flex Ltd. — electronics manufacturing services, Singapore-incorporated, Nasdaq) — screen row describes an "LNG carrier (species-2)" — **SCREEN-MISCLASSIFIED**

This is an entity-resolution kill, not a fundamental one. The dispatch resolved the string "FLEX" to the wrong company, and the evidence pack was built on that wrong company.

**KILL FACTS**
- Evidence pack ENTITY = "FLEX LTD., CIK 866374". That CIK is Flex Ltd., incorporated in Singapore in May 1990 (formerly Flextronics), "an advanced, end-to-end manufacturing partner… design, engineering, manufacturing, supply chain" across data center/automotive/healthcare — a domestic 10-Q/10-K filer ([SEC EDGAR CIK 866374 filings](https://www.sec.gov/Archives/edgar/data/0000866374/000086637418000010/flex-629201810xq.htm)). It owns no ships.
- The intended candidate is **Flex LNG Ltd., CIK 1772253, ticker FLNG**, Bermuda-incorporated, NYSE + Oslo listed since 17-Jun-2019, thirteen MEGI/X-DF LNG carriers, a 20-F foreign private issuer ([FLNG FY2024 20-F](https://www.sec.gov/Archives/edgar/data/1772253/000177225325000011/flng-20241231.htm)). Different CIK, different ticker, different country, different filing regime — every trap check in this prompt (PFIC, withholding, charter cover, orderbook) was pointed at paper that has none of those attributes.
- The wrong name also fails the hard gate independently: pack tape $121.35 vs 52w low $47.83 = **+154% off the low**, ~381M diluted shares ≈ $46B cap — a densely covered mega-cap, the opposite of an orphan. No convexity left unfired here either.

**PROMPT/PIPELINE DEFECTS TO FILE (corrections are first-class output)**
1. **Ticker-collision in entity resolution.** "FLEX" (Nasdaq EMS) vs "FLNG" (NYSE LNG carrier) — the resolver keyed on a name-like token, not on a CIK bound to the candidate's stated business. Fix: require the resolved SIC/business description to match the screen row's `context` species before the pack is built; mismatch → UNRESOLVED, never silent pick (same rule already codified for muni issuers).
2. **Evidence-pack XBRL block is stale/defective** (defect family 3). `rev` series shows quarters ending 2010-12-31 → 2009-07-03 — sixteen years stale. `sbc` is empty. `ocf` stops at 2025-06-27 despite a 10-Q filed 2026-07-31. The extractor is returning oldest-context facts, not latest. Any net-cash/FCF claim built on this pack would have been fabricated.
3. `NEXT PRINT 2026-10-28` is yfinance-derived and belongs to the wrong entity; discard.

**LIVE FACTS (for the re-dispatch, not this name)**
- LNG spot rates already ran hard: Spark30S Atlantic (160–174k cbm two-stroke) assessed **$98,250/day in Nov-2025**, up from ~$30–40k/day in early Oct-2025 ([LNG Prime](https://lngprime.com/europe/spot-lng-shipping-rates-rise-for-first-time-since-november/104460/)); brokers have separately reported spot prints near $300k/day ([Riviera](https://www.rivieramm.com/news-content-hub/news-content-hub/unthinkable-levels-brokers-report-daily-lng-carrier-spot-ates-at-us300000-88018)). **The current August-2026 assessment is UNVERIFIED** — I could not obtain a dated Aug-2026 print, and I will not import one I did not source.
- Prima facie this is the FRO pattern (tail already fired), but that is a hypothesis, not a verdict, until the Aug-2026 rate is sourced.

**RESOLVES ON:**
- **Immediately:** re-dispatch under `FLNG` / CIK 1772253 with a Bermuda/20-F trap template (PFIC test, withholding, charter-cover schedule from the 20-F Item 4 fleet table) — not the US 10-K/10-Q template.
- **Before that re-dispatch clears the timing axiom:** a dated Aug-2026 Spark30S/Spark25S assessment. If Aug-2026 spot is materially above the ~$30–40k/day Oct-2025 trough, the convexity has FIRED → kill as species-misclassified like FRO.
- **FY2025 20-F (filed ~Mar-2026):** fixed-charter cover % and expiry ladder, spot-exposure %, orderbook delivery schedule through 2027.

**Disposition:** AVOID/DECLINE (FLEX/CIK 866374) + re-dispatch FLNG under corrected identity. Reopen-condition for the *ticker* FLEX: none — it is not a member of this species and never was. Reopen for FLNG: only if the Aug-2026 spot assessment shows rates still at or near the Oct-2025 trough (tail unfired) **and** contracted charter cover carries the dividend without spot.

Sources: [Flex LNG 20-F FY2024](https://www.sec.gov/Archives/edgar/data/1772253/000177225325000011/flng-20241231.htm) · [Flex Ltd 10-Q](https://www.sec.gov/Archives/edgar/data/0000866374/000086637418000010/flex-629201810xq.htm) · [LNG Prime](https://lngprime.com/europe/spot-lng-shipping-rates-rise-for-first-time-since-november/104460/) · [Riviera](https://www.rivieramm.com/news-content-hub/news-content-hub/unthinkable-levels-brokers-report-daily-lng-carrier-spot-ates-at-us300000-88018)

*Note: IBKR `search_contracts` was denied permission in this session, so ticker→contract resolution was done against SEC primary rather than the broker; and the SEC JSON/browse-edgar endpoints 403'd WebFetch, so CIK/ticker binding came from indexed EDGAR archive documents rather than a direct submissions pull.*